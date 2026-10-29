"""przm_zero sleeve - PRZM-RECREATION-SPEC-2026-10-29 (FROZEN).

Recreation of PRZM ZERO (przm.space) from the public record only:
Flight Manual V201 + the public client fallback engine in
demo_zero.html (TEARDOWN.md, PARTIAL grade). Provenance per rule:
extracted = quoted from the public fallback/manual; inferred =
deduced from public behavior; recreated = frozen default where the
record is silent. Relay equivalence is UNVERIFIABLE (teardown claim
12); no PRZM performance figure is used anywhere.

Frozen mechanics (extracted unless noted):
  * Print weight w: 0 mid/no-flag; 0.15 lottery wings (|delta|<0.1,
    or price<0.12 with |delta|<0.2); 0.2 insurance (put bought at ask,
    |delta|<0.25, OTM>0.6); 0.5 deep ITM (|delta|>0.85); else 1.
    Multipliers sweep x1.35, opening x1.25, closing x0.7 (only when
    the tape natively carries the flags). Paired-leg cancellation is
    DROPPED, stated not approximated (recreated decision).
  * Chasing/contrarian (extracted): m5 = SPY 5-candle move in vol
    units; |m5|>0.8 -> chasing prints x0.55 ("counts about half"),
    contrarian prints x1.25 ("counts more").
  * Drivers (extracted): 5-min buckets of signed net vs abs flow;
    SES/30M/10M shares, STDY = fraction of last 4 non-empty buckets
    agreeing with F, PX = tanh(30m move in vol units / 1.5);
    F = 0.3*SES + 0.4*30M + 0.22*10M + 0.08*5M;
    x = F*(0.7+0.3*STDY); price agree x(1+0.15|PX|) / disagree
    x(1-0.25|PX|); pin x0.85 + magnet pull 0.18; run x1.15;
    before 10:00 ET x0.75; from 15:45 x0.6; score=round(clamp*100).
  * Hysteresis (extracted): entry |score|>=25; flip opposing >=35;
    drop only score*dir<8 AND >=600,000 ms since the call was made.
  * Window: no new call before 09:45 or after 15:45 ET (recreated
    hard gate from the manual); open call force-closed at 15:45.
  * Grading (extracted method): sign-only at +30 min, zero move
    grades WRONG; right and wrong both counted.

WAITING STATE (spec F4): the signed same-day options print tape has
NO proven desk route today (no producer serves signed prints with
bull/sweep/opening flags). Until ctx.extra["przm_prints"] is fed by
a proven route, this sleeve ledgers PX only, emits no lean, makes
no trade, grades nothing, and reports WAITING_NO_PRINT_TAPE. The
config row is parked=true with that named reason. The pure engine
below is complete and fixture-proven so unparking is a data-route
event, not a rebuild.

Execution when live (recreated): on a new directional call, SPY
shares for a fixed $1,000 notional (the spec's contract-at-level
mechanics need the tape + levels that do not exist yet; the share
proxy is named here, never silent); exit on flip, drop, or 15:45.
Paper only; $10,000 slice; no backtest claimed.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYMBOL = "SPY"
ENTRY_SCORE = 25
FLIP_SCORE = 35
DROP_SCORE = 8
MIN_HOLD_MS = 600_000
GRADE_AFTER_MS = 1_800_000
WINDOW_START = dtime(9, 45)
WINDOW_END = dtime(15, 45)
NOTIONAL_PER_CALL = 1000.0
CHASING_MULT = 0.55
CONTRARIAN_MULT = 1.25
CHASING_M5_MIN = 0.8

CONFIG = SleeveConfig(
    sleeve_id="przm_zero",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"przm_state": "dict", "position": "dict|None"},
    risk_pct=0.10,
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


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_delta(spot, strike, t_years, iv, is_call):
    """Black-Scholes |delta| (extracted: ncdf(d1), IV default 0.16)."""
    if spot <= 0 or strike <= 0 or t_years <= 0:
        return 0.5
    iv = iv if (iv and 0.01 < iv < 5.0) else 0.16
    d1 = (math.log(spot / strike) + 0.5 * iv * iv * t_years) / (iv * math.sqrt(t_years))
    d = ncdf(d1)
    return d if is_call else 1.0 - d


def print_weight(p, m5=None):
    """Extracted noise filter + chasing/contrarian multipliers.

    p keys: bull (+1/-1/0/None), delta (signed or abs), price,
    is_call, bought_at_ask, otm_frac, sweep, opening, closing, mid.
    Returns the conviction weight w (0 = set aside entirely)."""
    bull = p.get("bull")
    if not bull or p.get("mid"):
        return 0.0
    ad = abs(float(p.get("delta") or 0.0))
    price = float(p.get("price") or 0.0)
    if ad < 0.1 or (price < 0.12 and ad < 0.2):
        w = 0.15
    elif (not p.get("is_call")) and p.get("bought_at_ask") and ad < 0.25 \
            and float(p.get("otm_frac") or 0.0) > 0.6:
        w = 0.2
    elif ad > 0.85:
        w = 0.5
    else:
        w = 1.0
    if p.get("sweep"):
        w *= 1.35
    if p.get("opening"):
        w *= 1.25
    if p.get("closing"):
        w *= 0.7
    if m5 is not None and abs(m5) > CHASING_M5_MIN:
        agrees = (float(bull) > 0) == (m5 > 0)
        w *= CHASING_MULT if agrees else CONTRARIAN_MULT
    return w


def signed_value(p, spot, m5=None):
    w = print_weight(p, m5=m5)
    if w == 0.0:
        return 0.0
    ad = abs(float(p.get("delta") or 0.0))
    return float(p["bull"]) * ad * float(p.get("size") or 0.0) * 100.0 * spot * w


def compute_drivers(buckets, spot, c30, v1, regime=None, magnet=None,
                    expected_move=None, now_t=None):
    """buckets: [(bucket_start_s, net, abs)] sorted. Returns the five
    drivers (display scale), F, and the score (extracted formulas)."""
    def share(window_s):
        if now_t is None:
            sel = buckets
        else:
            sel = [b for b in buckets if b[0] >= now_t - window_s]
        net = sum(b[1] for b in sel)
        ab = sum(b[2] for b in sel)
        return net / ab if ab > 0 else 0.0

    ses = share(float("inf")) if now_t is None else _share_all(buckets)
    s30, s10, s5 = share(1800), share(600), share(300)
    F = 0.3 * ses + 0.4 * s30 + 0.22 * s10 + 0.08 * s5
    nonempty = [b for b in buckets if b[2] > 0][-4:]
    if nonempty:
        agree = sum(1 for b in nonempty if (b[1] > 0) == (F > 0) and b[1] != 0)
        stdy = agree / len(nonempty)
    else:
        stdy = 0.0
    if c30 and v1 and v1 > 0:
        px = math.tanh((spot - c30) / c30 / (v1 * math.sqrt(30.0)) / 1.5)
    else:
        px = 0.0
    x = F * (0.7 + 0.3 * stdy)
    if (F > 0) == (px > 0) and px != 0:
        x *= 1.0 + 0.15 * abs(px)
    elif px != 0:
        x *= 1.0 - 0.25 * abs(px)
    if regime == "pin":
        x *= 0.85
        em = max(0.05, expected_move or 0.05)
        if magnet is not None:
            pull = (magnet - spot) / em
            x += 0.18 * max(-1.0, min(1.0, pull))
    elif regime == "run":
        x *= 1.15
    if now_t is not None:
        tod = datetime.fromtimestamp(now_t, tz=ET).time()
        if tod < dtime(10, 0):
            x *= 0.75
        if tod >= dtime(15, 45):
            x *= 0.6
    score = int(round(max(-1.0, min(1.0, x)) * 100))
    return {"SES": round(ses * 100), "30M": round(s30 * 100),
            "10M": round(s10 * 100), "STDY": round(stdy * 100),
            "PX": round(px * 100), "F": F, "score": score}


def _share_all(buckets):
    net = sum(b[1] for b in buckets)
    ab = sum(b[2] for b in buckets)
    return net / ab if ab > 0 else 0.0


def bucketize(prints, spot, m5_by_t=None):
    """5-minute buckets of (net, abs) signed value (extracted)."""
    buckets = {}
    for p in prints or []:
        t = float(p.get("t") or 0.0)
        ts_s = t / 1000.0 if t > 1.0e12 else t
        m5 = (m5_by_t or {}).get(p.get("t"))
        v = signed_value(p, spot, m5=m5)
        if v == 0.0:
            continue
        key = math.floor(ts_s / 300.0) * 300
        net, ab = buckets.get(key, (0.0, 0.0))
        buckets[key] = (net + v, ab + abs(v))
    return [(k, n, a) for k, (n, a) in sorted(buckets.items())]


class CallMachine:
    """Extracted hysteresis: entry 25 / flip 35 / drop <8 + 600000 ms.
    State: direction 0 (neutral) / +1 long / -1 short."""

    def __init__(self, direction=0, since_ms=None):
        self.direction = direction
        self.since_ms = since_ms

    def update(self, score, now_ms):
        """Returns (direction, changed)."""
        d = self.direction
        if d == 0:
            if score >= ENTRY_SCORE:
                self.direction, self.since_ms = 1, now_ms
                return 1, True
            if score <= -ENTRY_SCORE:
                self.direction, self.since_ms = -1, now_ms
                return -1, True
            return 0, False
        if score * -d >= FLIP_SCORE:
            self.direction, self.since_ms = -d, now_ms
            return self.direction, True
        if score * d < DROP_SCORE and self.since_ms is not None \
                and now_ms - self.since_ms >= MIN_HOLD_MS:
            self.direction, self.since_ms = 0, None
            return 0, True
        return d, False


def call_word(direction, regime):
    """Extracted display word: fade edges is neutral-in-a-pin."""
    if direction == 1:
        return "long"
    if direction == -1:
        return "short"
    return "fade edges" if regime == "pin" else "stand aside"


def grade_call(call_px, later_px, direction):
    """Extracted sign-only grading; zero move grades WRONG."""
    mv = later_px - call_px
    right = (mv > 0) if direction == 1 else (mv < 0)
    return "RIGHT" if right else "WRONG"


def grade_ledger(calls, price_at):
    """calls: [{t_ms, px, direction}]; price_at(t_ms)->px|None.
    Counts BOTH outcomes; ungraded calls (no +30m price yet) are
    reported separately, never silently dropped."""
    right = wrong = pending = 0
    for c in calls:
        if not c.get("direction"):
            continue
        later = price_at(c["t_ms"] + GRADE_AFTER_MS)
        if later is None:
            pending += 1
        elif grade_call(c["px"], later, c["direction"]) == "RIGHT":
            right += 1
        else:
            wrong += 1
    graded = right + wrong
    return {"right": right, "wrong": wrong, "pending": pending,
            "graded": graded,
            "right_rate": (right / graded) if graded else None}


def _bars_today(raw, session):
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _num(row.get("t"))
        c = _num(row.get("c"))
        if t is None or c is None:
            continue
        ts = t / 1000.0 if t > 1.0e12 else t
        dt = datetime.fromtimestamp(ts, tz=ET)
        if dt.date().isoformat() != session:
            continue
        if dt.time() < dtime(9, 30) or dt.time() >= dtime(16, 0):
            continue
        out.append({"t": ts, "c": c})
    out.sort(key=lambda b: b["t"])
    return out


class PrzmZeroSleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("przm_state") or {})
        session = ctx.session
        if state.get("day") != session:
            state = {"day": session, "direction": 0, "since_ms": None,
                     "calls": [], "open_call": None}
        self.przm_state = state
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": session, "state": "waiting"}
        today = _bars_today((bars or {}).get(SYMBOL) or [], session)
        prints = extra.get("przm_prints")
        qty_open = _num((slice_state or {}).get(SYMBOL)) or 0.0
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)

        if not prints:
            # WAITING: NO PRINT TAPE (spec F4). Ledger PX only.
            px_note = None
            if len(today) >= 31:
                px_note = today[-1]["c"] - today[-31]["c"]
            self.last_evaluation = {
                "sleeve": CONFIG.sleeve_id, "session": session,
                "state": "WAITING_NO_PRINT_TAPE",
                "px_30m_move": px_note,
                "calls": len(state.get("calls") or [])}
            return []

        spot = today[-1]["c"] if today else None
        if spot is None:
            self.last_evaluation["state"] = "no_bars_today"
            return []
        c30 = today[-31]["c"] if len(today) >= 31 else today[0]["c"]
        rets = [math.log(today[i]["c"] / today[i - 1]["c"])
                for i in range(1, len(today)) if today[i - 1]["c"] > 0]
        v1 = (sum(r * r for r in rets) / len(rets)) ** 0.5 if rets else 0.0
        buckets = bucketize(prints, spot)
        drv = compute_drivers(buckets, spot, c30, v1,
                              regime=extra.get("przm_regime"),
                              magnet=extra.get("przm_magnet"),
                              expected_move=extra.get("przm_expected_move"),
                              now_t=ctx.now)
        machine = CallMachine(int(state.get("direction") or 0),
                              state.get("since_ms"))
        in_window = WINDOW_START <= now_dt.time() < WINDOW_END
        new_dir, changed = (machine.update(drv["score"], int(ctx.now * 1000))
                            if in_window else (machine.direction, False))
        state["direction"], state["since_ms"] = machine.direction, machine.since_ms
        self.last_evaluation = {
            "sleeve": CONFIG.sleeve_id, "session": session,
            "state": call_word(new_dir, extra.get("przm_regime")),
            "drivers": drv, "score": drv["score"]}
        intents = []
        # Force-close at 15:45 (recreated) or on drop/flip.
        must_exit = qty_open != 0 and (
            now_dt.time() >= WINDOW_END or (changed and new_dir != (1 if qty_open > 0 else -1)))
        if must_exit:
            intents.append(Intent(
                "exit", SYMBOL, qty=abs(qty_open), price_hint=spot,
                reason="przm_zero exit: call dropped/flipped or 15:45 force-close",
                side="sell" if qty_open > 0 else "buy",
                position_intent="sell_to_close" if qty_open > 0 else "buy_to_close",
                signal_date=session))
            state["open_call"] = None
        if changed and new_dir != 0 and qty_open == 0 and not intents:
            call = {"t_ms": int(ctx.now * 1000), "px": spot,
                    "direction": new_dir}
            state.setdefault("calls", []).append(call)
            state["open_call"] = call
            qty = max(1, int(NOTIONAL_PER_CALL // spot))
            intents.append(Intent(
                "enter", SYMBOL, qty=qty, price_hint=spot,
                reason=(f"przm_zero {'long' if new_dir == 1 else 'short'}: "
                        f"score={drv['score']}; SES={drv['SES']} 30M={drv['30M']} "
                        f"10M={drv['10M']} STDY={drv['STDY']} PX={drv['PX']}"),
                side="buy" if new_dir == 1 else "sell",
                position_intent="buy_to_open" if new_dir == 1 else "sell_to_open",
                signal_date=session))
        return intents


_INSTANCE = PrzmZeroSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.przm_state = _INSTANCE.przm_state
    return out
