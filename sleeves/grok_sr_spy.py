"""grok_sr_spy sleeve - GROK-SR-SPY-SPEC-2026-10-28 (FROZEN).

Provenance: X post by @thiccteddy, algo by Grok, installed by owner
order 2026-10-28. Edge status: UNPROVEN; the live paper record is the
test and no backtest is claimed.

SPY 1-minute horizontal support/resistance, exactly per the frozen
spec:

  * Zone map built from the prior 10 completed RTH sessions only
    (current session excluded), static for the session, no repaint:
    fractal swing pivots (5 bars each side, causally confirmed) plus
    volume-at-price nodes (0.10 bins at/above the 90th percentile of
    bin volume), single-linkage clustered with max gap 0.40 pt into
    0.40-0.80 pt bands, scored by pivot touches + node volume share,
    top 6 bands kept.
  * Fade: price enters a band from outside and the bar prints a
    rejection (wick beyond the band's far edge >= 50% of the bar's
    range, close back inside the band or beyond its near edge) on
    volume > 1.5x the trailing 20-bar average.
  * Breakout: a bar closes beyond the band's far edge by >= 0.10 pt
    with body >= 60% of its range, volume greater than the prior
    bar's and >= 1.2x the trailing 20-bar average.
  * Invalidation: a close back through the band within 3 bars after
    the entry fill exits at the next bar open (the intent emitted on
    the reclaim bar's close fills next open, per desk convention).
    After 3 bars the reclaim rule lapses; stop/target/hard-flat govern.
  * Stop beyond the zone (+/- 0.10 past the far edge, mirrored by
    setup/direction per spec); target is the nearest band edge in the
    trade direction or 2R from entry, whichever is closer (2R if no
    band lies in the trade direction).
  * Entries 09:30-11:30 ET only; hard flat 13:00 ET (the sleeve's own
    rule - config flat_by_close stays false so no second flatten path
    exists); one open position at a time; max 3 entries per session;
    a band that produced an exit is dead for the rest of the session.

Sizing (spec names stop/target math but NO sizing formula; the choice
is stated here and in GROK-SR-SPY-BUILD.md + the install proof):
unit risk 0.25% of slice equity per trade with a 25% notional cap,
the trullas_divergence install norm.

Data law: 1-minute bars are Alpaca SIP (enforced by the desk warm /
adapter path; volume signals on 1-min bars use SIP only).

State (open-trade plan, day counters, dead bands) is carried in
ctx.extra["grok_state"] and round-tripped by the adapter, which
persists it beside the sleeve journal. The strategy itself is pure:
clock only via Context.now, no files, no broker. Zones need no
persisted state: they are recomputed deterministically each cycle
from completed prior sessions only.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SYMBOL = "SPY"
PIVOT_K = 5
LOOKBACK_SESSIONS = 10
BIN_SIZE = 0.10
NODE_PERCENTILE = 0.90
CLUSTER_GAP = 0.40
BAND_MIN_WIDTH = 0.40
BAND_MAX_WIDTH = 0.80
MAX_BANDS = 6
FADE_VOL_MULT = 1.5
BREAKOUT_VOL_MULT = 1.2
BREAKOUT_MIN_CLOSE_BEYOND = 0.10
BREAKOUT_MIN_BODY_FRAC = 0.60
FADE_MIN_WICK_FRAC = 0.50
TRAILING_VOL_BARS = 20
STOP_BEYOND = 0.10
TARGET_R_MULT = 2.0
RECLAIM_WINDOW_BARS = 3
ENTRY_START = dtime(9, 30)
ENTRY_END = dtime(11, 30)
FLAT_TIME = dtime(13, 0)
MAX_ENTRIES_PER_DAY = 3
UNIT_RISK_PCT = 0.0025
NOTIONAL_CAP_PCT = 0.25

CONFIG = SleeveConfig(
    sleeve_id="grok_sr_spy",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"grok_state": "dict", "position": "dict|None"},
    risk_pct=UNIT_RISK_PCT,
    parked=False,
)


# ------------------------------------------------------------------ utils
def _number(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _epoch(v):
    n = _number(v)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if not isinstance(v, str):
        return None
    try:
        p = datetime.fromisoformat(v.replace("Z", "+00:00"))
        from datetime import timezone
        if p.tzinfo is None:
            p = p.replace(tzinfo=timezone.utc)
        return p.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _rth_bars(raw):
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _epoch(row.get("t"))
        o, h, l, c = (_number(row.get(k)) for k in ("o", "h", "l", "c"))
        v = _number(row.get("v")) or 0.0
        if None in (t, o, h, l, c) or min(o, h, l, c) <= 0 or h < l:
            continue
        dt = datetime.fromtimestamp(t, tz=ET)
        if dt.time() < dtime(9, 30) or dt.time() >= dtime(16, 0):
            continue
        if v <= 0:
            continue
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    deduped = []
    for b in out:
        if deduped and b["t"] == deduped[-1]["t"]:
            deduped[-1] = b
        else:
            deduped.append(b)
    return deduped


def _session_of(bar):
    return datetime.fromtimestamp(bar["t"], tz=ET).date().isoformat()


def _by_session(bars):
    groups = {}
    for b in bars:
        groups.setdefault(_session_of(b), []).append(b)
    return groups


# ------------------------------------------------------------------ zones
def _fractal_pivots(session_bars, k=PIVOT_K):
    """Pivot prices in ONE session. A pivot at index i needs k bars on
    each side inside the same session, so it is causally confirmed by
    construction and never straddles a session boundary."""
    prices = []
    n = len(session_bars)
    for i in range(k, n - k):
        window_h = [session_bars[j]["h"] for j in range(i - k, i + k + 1)]
        if session_bars[i]["h"] == max(window_h) and window_h.count(session_bars[i]["h"]) == 1:
            prices.append(session_bars[i]["h"])
        window_l = [session_bars[j]["l"] for j in range(i - k, i + k + 1)]
        if session_bars[i]["l"] == min(window_l) and window_l.count(session_bars[i]["l"]) == 1:
            prices.append(session_bars[i]["l"])
    return prices


def _volume_nodes(prior_bars):
    """Volume-at-price in 0.10 bins (bar volume assigned to the bin of
    its close). Returns [(node_price, volume_share)] for bins at or
    above the 90th percentile of bin volumes."""
    bins = {}
    total = 0.0
    for b in prior_bars:
        idx = math.floor(b["c"] / BIN_SIZE + 1e-9)
        bins[idx] = bins.get(idx, 0.0) + b["v"]
        total += b["v"]
    if not bins or total <= 0:
        return []
    vols = sorted(bins.values())
    threshold = vols[math.ceil(NODE_PERCENTILE * len(vols)) - 1]
    out = []
    for idx, vol in bins.items():
        if vol >= threshold:
            out.append((idx * BIN_SIZE + BIN_SIZE / 2.0, vol / total))
    return out


def _bands_from_items(items):
    """items: [(price, touches, vol_share)] sorted by price.
    Single-linkage clusters (max gap CLUSTER_GAP); a cluster wider
    than BAND_MAX_WIDTH splits at its largest internal gap and
    re-applies; a band narrower than BAND_MIN_WIDTH expands
    symmetrically to BAND_MIN_WIDTH."""
    if not items:
        return []
    clusters = [[items[0]]]
    for item in items[1:]:
        if item[0] - clusters[-1][-1][0] <= CLUSTER_GAP + 1e-9:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    bands = []
    for cluster in clusters:
        lo, hi = cluster[0][0], cluster[-1][0]
        if hi - lo > BAND_MAX_WIDTH + 1e-9 and len(cluster) > 1:
            gaps = [(cluster[j + 1][0] - cluster[j][0], j)
                    for j in range(len(cluster) - 1)]
            _, split_at = max(gaps)
            bands.extend(_bands_from_items(cluster[:split_at + 1]))
            bands.extend(_bands_from_items(cluster[split_at + 1:]))
            continue
        if hi - lo < BAND_MIN_WIDTH - 1e-9:
            mid = (lo + hi) / 2.0
            lo, hi = mid - BAND_MIN_WIDTH / 2.0, mid + BAND_MIN_WIDTH / 2.0
        bands.append({
            "low": round(lo, 4), "high": round(hi, 4),
            "score": sum(t for _, t, _ in cluster) + sum(s for _, _, s in cluster),
            "touches": int(sum(t for _, t, _ in cluster)),
        })
    return bands


def build_zones(prior_bars):
    """Zone bands from COMPLETED prior-session bars only. The caller
    excludes the current session; this function is a pure function of
    what it is given, so zones are identical with or without today's
    bars in the raw input when the caller filters by session (see
    zones_for)."""
    groups = _by_session(prior_bars)
    items = []
    for session in sorted(groups):
        for price in _fractal_pivots(groups[session]):
            items.append((price, 1, 0.0))
    for price, share in _volume_nodes(prior_bars):
        items.append((price, 0, share))
    items.sort(key=lambda x: x[0])
    bands = _bands_from_items(items)
    bands.sort(key=lambda b: (-b["score"], b["low"]))
    bands = bands[:MAX_BANDS]
    bands.sort(key=lambda b: b["low"])
    return bands


def zones_for(bars, session):
    """Bands for `session`: the last LOOKBACK_SESSIONS completed RTH
    sessions strictly before it."""
    groups = _by_session(bars)
    prior_dates = sorted(d for d in groups if d < session)[-LOOKBACK_SESSIONS:]
    prior = [b for d in prior_dates for b in groups[d]]
    return build_zones(prior)


def _band_key(band):
    return f"{band['low']:.2f}-{band['high']:.2f}"


def _stop_target(setup, direction, band, entry, bands):
    """Frozen stop/target math. Stop beyond the zone; target the
    nearest band edge in the trade direction or 2R, whichever closer."""
    if setup == "fade":
        stop = band["high"] + STOP_BEYOND if direction == -1 else band["low"] - STOP_BEYOND
    else:  # breakout
        stop = band["low"] - STOP_BEYOND if direction == 1 else band["high"] + STOP_BEYOND
    stop = round(stop, 4)
    risk = abs(entry - stop)
    if risk <= 0:
        return stop, None
    if direction == 1:
        two_r = entry + TARGET_R_MULT * risk
        edges = [b["low"] for b in bands if b["low"] > entry]
        target = min([two_r] + edges) if edges else two_r
    else:
        two_r = entry - TARGET_R_MULT * risk
        edges = [b["high"] for b in bands if b["high"] < entry]
        target = max([two_r] + edges) if edges else two_r
    return stop, round(target, 4)


# ------------------------------------------------------------------ sleeve
class GrokSrSpySleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("grok_state") or {})
        session = ctx.session
        if state.get("day") != session:
            state = {"day": session, "entries_today": 0, "plan": None,
                     "dead_bands": []}
        state.setdefault("entries_today", 0)
        state.setdefault("plan", None)
        state.setdefault("dead_bands", [])
        self.grok_state = state
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": session, "state": "scanning"}
        raw = (bars or {}).get(SYMBOL) or []
        all_bars = _rth_bars(raw)
        groups = _by_session(all_bars)
        today = groups.get(session) or []
        qty_open = _number((slice_state or {}).get(SYMBOL)) or 0.0
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        plan = state.get("plan")

        # ---- an exit the desk already executed: band dies ------------
        if plan and qty_open == 0 and plan.get("seen_open"):
            key = plan.get("band_key")
            if key and key not in state["dead_bands"]:
                state["dead_bands"].append(key)
            state["plan"] = None
            plan = None
            self.last_evaluation["state"] = "exit_observed_band_dead"

        # ---- manage an open position ---------------------------------
        if plan and qty_open != 0:
            plan["seen_open"] = True
            return self._manage(today, state, plan, qty_open, now_dt)
        if plan and qty_open == 0:
            # Entry emitted, fill not yet visible in slice_state: wait.
            self.last_evaluation["state"] = "awaiting_fill"
            return []
        if qty_open != 0:
            # Position open with no plan (state rebuilt): hard flat only.
            if now_dt.time() >= FLAT_TIME:
                self.last_evaluation["state"] = "flat_1300_no_plan"
                latest = today[-1] if today else None
                return [self._exit(latest, abs(qty_open), qty_open,
                                   "grok_sr_spy flat 13:00 ET (plan unavailable)")]
            self.last_evaluation["state"] = "position_open_no_plan"
            return []

        # ---- entry gates ----------------------------------------------
        if not today:
            self.last_evaluation["state"] = "no_bars_today"
            return []
        latest = today[-1]
        latest_dt = datetime.fromtimestamp(latest["t"], tz=ET)
        if not (ENTRY_START <= latest_dt.time() < ENTRY_END):
            self.last_evaluation["state"] = "outside_entry_window"
            return []
        if int(state.get("entries_today") or 0) >= MAX_ENTRIES_PER_DAY:
            self.last_evaluation["state"] = "blocked_max_entries_3"
            return []
        equity = _number(ctx.equity) or 0.0
        if equity <= 0:
            self.last_evaluation["state"] = "blocked_equity_unavailable"
            return []
        if len(today) < TRAILING_VOL_BARS + 1:
            self.last_evaluation["state"] = "insufficient_intraday_history"
            return []
        prev = today[-2]
        trailing = today[-TRAILING_VOL_BARS - 1:-1]
        avg_vol = sum(b["v"] for b in trailing) / TRAILING_VOL_BARS

        bands = zones_for(all_bars, session)
        self.last_evaluation["bands"] = bands
        dead = set(state.get("dead_bands") or [])
        live_bands = [b for b in bands if _band_key(b) not in dead]
        hit = self._scan(latest, prev, avg_vol, live_bands)
        if not hit:
            self.last_evaluation["state"] = "no_setup"
            return []
        setup, direction, band = hit
        entry = latest["c"]
        stop, target = _stop_target(setup, direction, band, entry, bands)
        if target is None:
            self.last_evaluation["state"] = "blocked_zero_risk"
            return []
        risk = abs(entry - stop)
        qty = int(math.floor(min(UNIT_RISK_PCT * equity / risk,
                                 NOTIONAL_CAP_PCT * equity / entry)))
        if qty <= 0:
            self.last_evaluation["state"] = "blocked_size_zero"
            return []
        state["entries_today"] = int(state.get("entries_today") or 0) + 1
        state["plan"] = {
            "setup": setup, "direction": direction,
            "band_low": band["low"], "band_high": band["high"],
            "band_key": _band_key(band), "entry": entry, "stop": stop,
            "target": target, "entry_index": len(today) - 1,
            "session": session, "seen_open": False}
        self.last_evaluation["state"] = "entry_intent"
        side = "buy" if direction == 1 else "sell"
        reason = (
            f"grok_sr_spy {setup} {'long' if direction == 1 else 'short'}: "
            f"band={band['low']:.2f}-{band['high']:.2f}; entry={entry:.4f}; "
            f"stop={stop:.4f}; target={target:.4f}; qty={qty}")
        return [Intent(
            "enter", SYMBOL, qty=qty, price_hint=entry,
            stop=stop, target=target,
            exit_rules=(ExitRule("stop", stop), ExitRule("target", target)),
            reason=reason, side=side,
            position_intent="buy_to_open" if direction == 1 else "sell_to_open",
            signal_date=session)]

    # ------------------------------------------------------------- scan
    def _scan(self, bar, prev, avg_vol, bands):
        rng = bar["h"] - bar["l"]
        if rng <= 0 or avg_vol <= 0:
            return None
        body = abs(bar["c"] - bar["o"])
        # Fades first, across all bands: a bar that closes back inside
        # a band it rejected at is a fade, even though that same close
        # also sits beyond some lower band's far edge.
        for band in bands:
            lo, hi = band["low"], band["high"]
            # Fade resistance -> short: approached from below, wick
            # beyond the far (top) edge, close back inside or below
            # the near edge (close <= band top covers both readings).
            if (prev["c"] < lo and bar["h"] > hi
                    and (bar["h"] - max(bar["o"], bar["c"])) >= FADE_MIN_WICK_FRAC * rng
                    and bar["c"] <= hi
                    and bar["v"] > FADE_VOL_MULT * avg_vol):
                return ("fade", -1, band)
            # Fade support -> long: mirrored.
            if (prev["c"] > hi and bar["l"] < lo
                    and (min(bar["o"], bar["c"]) - bar["l"]) >= FADE_MIN_WICK_FRAC * rng
                    and bar["c"] >= lo
                    and bar["v"] > FADE_VOL_MULT * avg_vol):
                return ("fade", 1, band)
        for band in bands:
            lo, hi = band["low"], band["high"]
            # Breakout long: decisive close above the far edge. The
            # prior close must be at or below the far edge - this bar
            # is the crossing, not a bar merely sitting beyond a
            # distant band.
            if (prev["c"] <= hi
                    and bar["c"] > hi + BREAKOUT_MIN_CLOSE_BEYOND
                    and bar["c"] > bar["o"]
                    and body >= BREAKOUT_MIN_BODY_FRAC * rng
                    and bar["v"] > prev["v"]
                    and bar["v"] >= BREAKOUT_VOL_MULT * avg_vol):
                return ("breakout", 1, band)
            # Breakout short: decisive close below the far edge,
            # prior close at or above it (the crossing bar).
            if (prev["c"] >= lo
                    and bar["c"] < lo - BREAKOUT_MIN_CLOSE_BEYOND
                    and bar["c"] < bar["o"]
                    and body >= BREAKOUT_MIN_BODY_FRAC * rng
                    and bar["v"] > prev["v"]
                    and bar["v"] >= BREAKOUT_VOL_MULT * avg_vol):
                return ("breakout", -1, band)
        return None

    # ------------------------------------------------------------ exits
    def _exit(self, bar, qty, signed_qty, reason):
        return Intent("exit", SYMBOL, qty=float(qty),
                      price_hint=bar["c"] if bar else None, reason=reason,
                      side="buy" if signed_qty < 0 else "sell",
                      position_intent="buy_to_close" if signed_qty < 0
                      else "sell_to_close")

    def _manage(self, today, state, plan, qty_open, now_dt):
        signed = qty_open
        latest = today[-1] if today else None
        # Hard flat first: 13:00 ET exits everything.
        if now_dt.time() >= FLAT_TIME:
            key = plan.get("band_key")
            if key and key not in state["dead_bands"]:
                state["dead_bands"].append(key)
            state["plan"] = None
            self.last_evaluation["state"] = "flat_1300"
            return [self._exit(latest, abs(signed), signed,
                               "grok_sr_spy flat 13:00 ET")]
        if latest is None:
            self.last_evaluation["state"] = "position_open"
            return []
        # Reclaim invalidation: within 3 bars after the entry fill
        # (fill bar = entry_index + 1, so the window is entry_index+1
        # .. entry_index+3 in today's bar indices).
        idx = len(today) - 1
        ei = int(plan.get("entry_index") or 0)
        if ei + 1 <= idx <= ei + RECLAIM_WINDOW_BARS:
            lo, hi = float(plan["band_low"]), float(plan["band_high"])
            c = latest["c"]
            if plan["setup"] == "fade":
                reclaimed = c > hi if int(plan["direction"]) == -1 else c < lo
            else:  # breakout: a close back inside the band reclaims it
                reclaimed = c <= hi if int(plan["direction"]) == 1 else c >= lo
            if reclaimed:
                key = plan.get("band_key")
                if key and key not in state["dead_bands"]:
                    state["dead_bands"].append(key)
                state["plan"] = None
                self.last_evaluation["state"] = "reclaim_exit"
                return [self._exit(latest, abs(signed), signed,
                                   "grok_sr_spy reclaim within 3 bars: exit next open")]
        self.last_evaluation["state"] = "position_open"
        return []


_INSTANCE = GrokSrSpySleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.grok_state = _INSTANCE.grok_state
    return out
