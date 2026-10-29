"""przm_fade_edges sleeve - PRZM-RECREATION-SPEC-2026-10-29 (FROZEN).

Recreation of PRZM ZERO's Fade Edges state. Provenance:
extracted = the regime test and the trading rule are in the public
record (Flight Manual V201: "In a pin, fade the edges to the magnet.
In a run, don't fight it"; fallback code: pin = spot > gammaFlip;
Fade Edges is the neutral-in-a-pin call state, not a direction).
recreated = the gamma computation, the session-edge definition, and
all entry/target/invalidation mechanics (the record names none).

Frozen mechanics:
  * Gamma (recreated): per chain pull, GEX per strike =
    OI x gamma x 100 x spot, + for calls / - for puts. Magnet =
    strike with largest |net GEX|. Flip = strike where cumulative
    net GEX summed from the lowest strike changes sign.
  * Regime (extracted test): pin when spot > flip; run otherwise.
    NO substitute regime test exists under this spec (F1/F4).
  * Edges (recreated): running session high/low of SPY 1-min bars,
    first fadeable at 10:00 ET.
  * Entry (recreated on the extracted rule): in a pin, SPY within
    0.05% of the session high with that high above the magnet ->
    short toward the magnet; mirror at the low. An edge already past
    the magnet is spent: no trade. Fixed $2,000 notional, one fade
    per edge per session, max two open fades.
  * Target (extracted destination): the magnet; exit on a 1-min
    close at/through it. Invalidation (recreated): 1-min close
    0.15% beyond the faded edge. Regime flip to run exits at once
    (extracted: "In a run, don't fight it"). Entries 09:45-15:15;
    all fades closed by 15:45.

WAITING STATE: the desk's options_chain producer serves delta-only
rows (feed=indicative carries no greeks and no open interest;
FEED-WIRE-20261025 in desk3/producers.py), so gamma levels cannot
be computed from any route that exists today. When the chain rows
fed to this sleeve lack gamma or OI, gamma_levels() returns None
and the sleeve reports WAITING_NO_GAMMA_LEVELS, ledgers the regime
as unknown, and trades nothing. The config row is parked=true with
that named reason. Paper only; $10,000 slice; no backtest claimed.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYMBOL = "SPY"
EDGE_TOL_FRAC = 0.0005
INVALID_FRAC = 0.0015
NOTIONAL_PER_FADE = 2000.0
MAX_OPEN_FADES = 2
EDGES_FROM = dtime(10, 0)
ENTRY_START = dtime(9, 45)
ENTRY_END = dtime(15, 15)
FLAT_TIME = dtime(15, 45)

CONFIG = SleeveConfig(
    sleeve_id="przm_fade_edges",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"przm_fade_state": "dict", "position": "dict|None"},
    risk_pct=0.20,
    parked=True,
)


def _num(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def gamma_levels(chain_rows, spot):
    """Recreated gamma computation. Returns {"magnet": strike,
    "flip": strike} or None when rows lack gamma/OI (the honest
    waiting condition) or no sign change exists."""
    if not chain_rows or not spot or spot <= 0:
        return None
    per_strike = {}
    usable = 0
    for r in chain_rows:
        if not isinstance(r, dict):
            continue
        strike = _num(r.get("strike"))
        gamma = _num(r.get("gamma"))
        oi = _num(r.get("open_interest", r.get("oi")))
        right = str(r.get("right") or r.get("type") or "").lower()
        if strike is None or gamma is None or oi is None or oi <= 0:
            continue
        if right not in ("call", "put", "c", "p"):
            continue
        sign = 1.0 if right in ("call", "c") else -1.0
        per_strike[strike] = per_strike.get(strike, 0.0) \
            + sign * oi * gamma * 100.0 * spot
        usable += 1
    if usable == 0 or not per_strike:
        return None
    magnet = max(per_strike, key=lambda k: abs(per_strike[k]))
    cum = 0.0
    flip = None
    prev_sign = 0
    for strike in sorted(per_strike):
        cum += per_strike[strike]
        s = 1 if cum > 0 else (-1 if cum < 0 else prev_sign)
        if prev_sign and s and s != prev_sign:
            flip = strike
            break
        if s:
            prev_sign = s
    if flip is None:
        return None
    return {"magnet": magnet, "flip": flip, "gex": per_strike}


def regime_for(spot, levels):
    """Extracted test: pin = spot > gamma flip."""
    if levels is None:
        return None
    return "pin" if spot > levels["flip"] else "run"


def _bars_today(raw, session):
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _num(row.get("t"))
        vals = [_num(row.get(k)) for k in ("o", "h", "l", "c")]
        if t is None or None in vals:
            continue
        ts = t / 1000.0 if t > 1.0e12 else t
        dt = datetime.fromtimestamp(ts, tz=ET)
        if dt.date().isoformat() != session:
            continue
        if dt.time() < dtime(9, 30) or dt.time() >= dtime(16, 0):
            continue
        out.append({"t": ts, "o": vals[0], "h": vals[1],
                    "l": vals[2], "c": vals[3]})
    out.sort(key=lambda b: b["t"])
    return out


class PrzmFadeEdgesSleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("przm_fade_state") or {})
        session = ctx.session
        if state.get("day") != session:
            state = {"day": session, "faded_edges": [], "plan": None,
                     "regime_log": []}
        state.setdefault("faded_edges", [])
        state.setdefault("plan", None)
        self.przm_fade_state = state
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": session, "state": "waiting"}
        today = _bars_today((bars or {}).get(SYMBOL) or [], session)
        if not today:
            self.last_evaluation["state"] = "no_bars_today"
            return []
        latest = today[-1]
        spot = latest["c"]
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        levels = gamma_levels(extra.get("przm_chain") or [], spot)
        regime = regime_for(spot, levels)
        qty_open = _num((slice_state or {}).get(SYMBOL)) or 0.0
        plan = state.get("plan")

        if levels is None:
            self.last_evaluation = {
                "sleeve": CONFIG.sleeve_id, "session": session,
                "state": "WAITING_NO_GAMMA_LEVELS", "regime": None}
            return []

        state.setdefault("regime_log", []).append(
            {"t": latest["t"], "regime": regime, "spot": spot,
             "magnet": levels["magnet"], "flip": levels["flip"]})
        self.last_evaluation = {
            "sleeve": CONFIG.sleeve_id, "session": session,
            "state": regime, "magnet": levels["magnet"],
            "flip": levels["flip"]}

        # ---- manage open fade -------------------------------------
        if plan and qty_open != 0:
            direction = int(plan["direction"])
            magnet = float(plan["magnet"])
            edge = float(plan["edge"])
            reason = None
            if regime == "run":
                reason = "przm_fade_edges regime flip to run: do not fight it"
            elif now_dt.time() >= FLAT_TIME:
                reason = "przm_fade_edges 15:45 time exit"
            elif direction == -1 and latest["c"] <= magnet:
                reason = "przm_fade_edges magnet reached"
            elif direction == 1 and latest["c"] >= magnet:
                reason = "przm_fade_edges magnet reached"
            elif direction == -1 and latest["c"] > edge * (1 + INVALID_FRAC):
                reason = "przm_fade_edges invalidation beyond edge"
            elif direction == 1 and latest["c"] < edge * (1 - INVALID_FRAC):
                reason = "przm_fade_edges invalidation beyond edge"
            if reason:
                state["plan"] = None
                self.last_evaluation["state"] = "exit"
                return [Intent(
                    "exit", SYMBOL, qty=abs(qty_open), price_hint=spot,
                    reason=reason,
                    side="buy" if qty_open < 0 else "sell",
                    position_intent="buy_to_close" if qty_open < 0
                    else "sell_to_close", signal_date=session)]
            self.last_evaluation["state"] = "fade_open"
            return []
        if plan and qty_open == 0:
            self.last_evaluation["state"] = "awaiting_fill"
            return []

        # ---- entries: pin only; a run stands aside ----------------
        if regime != "pin":
            self.last_evaluation["state"] = "stand_aside_run"
            return []
        if not (ENTRY_START <= now_dt.time() <= ENTRY_END):
            self.last_evaluation["state"] = "outside_entry_window"
            return []
        if now_dt.time() < EDGES_FROM:
            self.last_evaluation["state"] = "edges_not_printable_before_1000"
            return []
        equity = _num(ctx.equity) or 0.0
        if equity <= 0:
            self.last_evaluation["state"] = "blocked_equity_unavailable"
            return []
        hi = max(b["h"] for b in today)
        lo = min(b["l"] for b in today)
        magnet = levels["magnet"]
        faded = set(state.get("faded_edges") or [])
        direction = edge = None
        if spot >= hi * (1 - EDGE_TOL_FRAC) and hi > magnet \
                and "high" not in faded:
            direction, edge = -1, hi
        elif spot <= lo * (1 + EDGE_TOL_FRAC) and lo < magnet \
                and "low" not in faded:
            direction, edge = 1, lo
        if direction is None:
            self.last_evaluation["state"] = "pin_no_edge_touch"
            return []
        qty = max(1, int(NOTIONAL_PER_FADE // spot))
        stop = round(edge * (1 + INVALID_FRAC), 4) if direction == -1 \
            else round(edge * (1 - INVALID_FRAC), 4)
        state["faded_edges"] = sorted(faded | {"high" if direction == -1 else "low"})
        state["plan"] = {"direction": direction, "edge": edge,
                         "magnet": magnet, "flip": levels["flip"],
                         "entry": spot, "session": session}
        self.last_evaluation["state"] = "fade_entry"
        return [Intent(
            "enter", SYMBOL, qty=qty, price_hint=spot, stop=stop,
            target=magnet,
            exit_rules=(ExitRule("stop", stop), ExitRule("target", magnet)),
            reason=(f"przm_fade_edges {'short' if direction == -1 else 'long'} "
                    f"fade at edge={edge:.2f} to magnet={magnet:.2f}; "
                    f"flip={levels['flip']:.2f}; qty={qty}"),
            side="sell" if direction == -1 else "buy",
            position_intent="sell_to_open" if direction == -1 else "buy_to_open",
            signal_date=session)]


_INSTANCE = PrzmFadeEdgesSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.przm_fade_state = _INSTANCE.przm_fade_state
    return out
