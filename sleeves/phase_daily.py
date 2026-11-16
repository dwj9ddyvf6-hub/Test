"""Phase Daily — lean-desk port.

EXTRACTED from the old desk's phase_daily.py + phase_signals.py
(Milkman Daily Bilbo Boxes). phase_compression_daily and
detect_episodes are ported verbatim in behavior — pandas/numpy
re-expressed in pure Python (ewm adjust=False recursions, rolling
sample stdev ddof=1); plumbing is core-owned. See ports/phase_daily.md.

Strategy (phase_signals docstring):
  Box: high/low of the FIRST 5 compression (grey) days (fewer if the
  squeeze ends early). Knowable at the close of the 5th grey day, or at
  the close of the first non-grey day when compression ends early.
  K5: resting buy-stop at box high, working 20 trading days after the
  box locks, gated each day on prior close > daily EMA21. Box-low
  touch first -> no trade. Initial stop = box low.
  Trail: each day the stop ratchets up to yesterday's daily EMA50
  (never down). Exit when price falls through the trail.
Risk 0.25%/trade; per-position notional cap 25% of equity; max 10
positions (phase_daily.py constants, verbatim).

The NC intraday nowcast arm does NOT port as a signal here — named
misfit (ports/phase_daily.md): it needs 5-min provisional bars and
crosses episode state intraday; it belongs to a core intraday product.

The old desk's earnings flatten + re-entry arm (15:55 ET flatten
the session before earnings, re-entry after) was NOT ported at
first — named misfit M-PH2 (ports/phase_daily.md). An earlier
port record claimed the flatten was "a desk-wide core Risk/Gate
duty"; no such core duty ever existed on the lean desk and no
sleeve emitted the earnings_flatten ExitRule kind, so the kind
was removed from the contract (audit cure 9, 2026-10-18) rather
than left as a named exit route that would never fire.

ENH (IMPROVE-phase_daily, Edge program 2026-10-24, plan R-2
closeout): the arm is restored behind a switch. A held position
whose next earnings print falls on the coming session is
flattened at the 15:55 ET evaluation of the flatten session —
the earnings session itself when the source times the print
after-hours, otherwise the last served session before the
earnings date (a pre-market or untimed print is never ridden
into). After the print, the position re-enters on the first
session serving a post-print bar, at that session's close,
under its surviving box/trail state (the booked record below),
unless the close has fallen through the surviving trail — the
premise is then dead and the name stays flat. The earnings
calendar arrives via context.extra (below), produced at warm
time only by runtime/earnings_warm.py (Nasdaq calendar) into
the local cache and served by adapters/phase_daily.py; a stale
or unserved calendar fails the arm closed (no flatten on
invented data — the position rides through, as the control
does). Switch context.extra["phase_daily_enhance"]
["earnings_flatten_arm"], default ON; OFF restores the
pre-change ride-through rule exactly (the frozen control: no
flatten, no re-entry, trail/K5 unchanged). Every flatten /
re-entry decision point records a paired control/treatment
record in the phase_daily_enh_journal (adopted from
context.extra, filed on self.last_evaluation), and a flatten
also files its surviving record under last_evaluation
["earnings_flat"] for the caller to book into sleeve_state —
the same journal-rebuilt-state limit the other sleeves record
(journal positions carry only symbol/qty/avg_price).

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty",
                   "trail": float} | None, "episode_key": str|None,
                   "earnings_flat": {"qty","entry_px","entry_date",
                   "trail","stop_px","episode_key","earnings_date",
                   "flat_date"} | None}}
  "universe": optional override (default: bars keys; the old sleeve
              read desk/phase_universe.txt)
  "earnings": {SYM: "YYYY-MM-DD"|None} and "earnings_time":
              {SYM: "pre"|"after"|None}, "earnings_fresh": bool
              (served by adapters/phase_daily.py from the warm-time
              producer's cache, params first; absent or stale fails
              the arm closed)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
BOX_DAYS = 5
K5_WINDOW_BARS = 20
RISK_FRACTION = 0.0025

def _frac_qty(dollars, per_unit):
    """WS4-FRACTIONAL-20261114 (owner ruling 2026-11-14 17:08 ET:
    "It needs to buy stuff of any price"). Express a positive
    dollar budget as a fractional quantity, rounded DOWN to the
    door's 6dp precision, never up past the budget. Returns 0.0
    only when the budget itself is not positive or the unit
    price / per-share risk is not positive — the budget deciding,
    never the share price. Reconciliation with OBS-1 (2026-10-23,
    standing): the forced 1-share floor stays forbidden;
    whole-share rounding was the defect."""
    if dollars <= 0 or per_unit <= 0:
        return 0.0
    import math as _m
    return _m.floor((dollars / per_unit) * 1_000_000) / 1_000_000

MAX_POSITIONS = 10
NOTIONAL_CAP = 0.25
FLATTEN_ARM_HM = (15, 55)  # the old arm's 15:55 ET flatten time
EXP_ID = "ENH-PHASE-DAILY-20261024"

CONFIG = SleeveConfig(
    sleeve_id="phase_daily", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "episode_key": "str|None",
                  "earnings_flat": "dict|None"},
    risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def _ewm(values, alpha):
    out = []
    v = None
    for x in values:
        v = x if v is None else v + alpha * (x - v)
        out.append(v)
    return out


def ema(values, n):
    """pandas ewm(span=n, adjust=False)."""
    return _ewm(values, 2.0 / (n + 1.0))


def rma(values, n):
    """pandas ewm(alpha=1/n, adjust=False)."""
    return _ewm(values, 1.0 / n)


def atr_series(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(float(b["h"]) - float(b["l"]))
        else:
            pc = float(bars[i - 1]["c"])
            trs.append(max(float(b["h"]) - float(b["l"]),
                           abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    return rma(trs, n)


def _rolling_std(values, window=21):
    """pandas rolling(21, min_periods=1).std(ddof=1): NaN for <2 points."""
    out = []
    for i in range(len(values)):
        w = values[max(0, i - window + 1):i + 1]
        if len(w) < 2:
            out.append(float("nan"))
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
        out.append(math.sqrt(var))
    return out


def phase_compression_daily(bars):
    """Verbatim port of phase_signals.phase_compression_daily:
    grey (1) when the 21-period Bollinger band sits inside the 2xATR14
    Keltner band, except when the band gap is not shrinking and we are
    already inside the 1.854xATR expansion zone."""
    n = len(bars)
    if n == 0:
        return []
    price = [float(b["c"]) for b in bars]
    a14 = atr_series(bars, 14)
    pivot = ema(price, 21)
    sd = _rolling_std(price, 21)
    grey = [0] * n
    comp = []
    inexp = []
    for i in range(n):
        above = price[i] >= pivot[i]
        bb_up, bb_dn = pivot[i] + 2.0 * sd[i], pivot[i] - 2.0 * sd[i]
        kc_up, kc_dn = pivot[i] + 2.0 * a14[i], pivot[i] - 2.0 * a14[i]
        ex_up, ex_dn = pivot[i] + 1.854 * a14[i], pivot[i] - 1.854 * a14[i]
        comp.append((bb_up - kc_up) if above else (kc_dn - bb_dn))
        inexp.append((bb_up - ex_up) if above else (ex_dn - bb_dn))
    for i in range(1, n):
        widening = comp[i - 1] <= comp[i]
        if widening and inexp[i] > 0:
            grey[i] = 0
        elif comp[i] <= 0:
            grey[i] = 1
    return grey


def detect_episodes(bars):
    """Verbatim port of phase_signals.detect_episodes (dates from bars)."""
    grey = phase_compression_daily(bars)
    dates = _dates(bars)
    h = [float(b["h"]) for b in bars]
    lo = [float(b["l"]) for b in bars]
    n = len(bars)
    episodes = []
    i = 0
    while i < n:
        if grey[i] != 1:
            i += 1
            continue
        start = i
        ep_hi, ep_lo = h[i], lo[i]
        n_grey = 1
        box = None
        j = i + 1
        while j < n and grey[j] == 1:
            ep_hi = max(ep_hi, h[j])
            ep_lo = min(ep_lo, lo[j])
            n_grey += 1
            if n_grey == BOX_DAYS:
                box = (ep_hi, ep_lo, j)
            j += 1
        ended = j < n
        if box is None:
            box = (ep_hi, ep_lo, j if ended else None)
        episodes.append({
            "start_idx": start, "end_idx": j - 1, "ended": ended,
            "n_grey": n_grey, "ep_hi": float(ep_hi), "ep_lo": float(ep_lo),
            "box_hi": float(box[0]), "box_lo": float(box[1]),
            "box_locked_idx": box[2],
            "start_date": dates[start], "end_date": dates[j - 1]})
        i = j if j > start else start + 1
    return episodes


def size_qty(equity, entry_ref, stop_ref):
    """Verbatim old phase_daily.size_qty (post 2026-10-09 audit): risk
    0.25% on the box range, capped at 25% notional. NO 1-share floor —
    the old max(qty, 1) forced orders breaching both rails and was
    removed there; 0 flows to the caller's qty < 1 skip."""
    risk_dist = entry_ref - stop_ref
    if risk_dist <= 0:
        return 0
    qty = _frac_qty(equity * RISK_FRACTION, risk_dist)
    qty = min(qty, _frac_qty(equity * NOTIONAL_CAP, entry_ref))
    return qty


def k5_trigger(bars, ep):
    """K5 evaluation after the box locks: returns (bar_idx, stop_px) of
    the first bar within K5_WINDOW_BARS after lock whose high reaches
    box_hi, gated on the PRIOR close > EMA21, provided no earlier bar
    touched box_lo first. None = no live trigger on the last bar."""
    lock = ep["box_locked_idx"]
    if lock is None:
        return None
    closes = [float(b["c"]) for b in bars]
    e21 = ema(closes, 21)
    last = len(bars) - 1
    # Old boxlow_touched / boxhi-breach scan start: for a full 5-grey-day
    # box the lock bar IS the 5th grey day (its low is part of the box),
    # so the scan starts after it. For an early-end box the lock bar is
    # the first non-grey RESOLUTION bar, whose low is NOT part of the
    # box — a box-low touch or a box-high breach on that very bar kills
    # the trade (the box was not knowable until its close, so a breach
    # on it printed without a possible fill).
    start = lock if ep.get("n_grey", BOX_DAYS) < BOX_DAYS else lock + 1
    for i in range(start, min(last + 1, lock + 1 + K5_WINDOW_BARS)):
        if float(bars[i]["l"]) <= ep["box_lo"]:
            return None  # box-low touch first -> no trade
        if i == lock:
            if float(bars[i]["h"]) >= ep["box_hi"]:
                return None  # resolution-bar breach: dead, not a trigger
            continue
        if float(bars[i]["h"]) >= ep["box_hi"] and closes[i - 1] > e21[i - 1]:
            return (i, ep["box_lo"]) if i == last else None
    return None


def _trail_for(bl, pos):
    """The position's EMA50-ratchet trail, recomputed purely from
    the bars since the entry bar (each day's candidate is the
    PRIOR bar's EMA50), floored at the stored trail and the
    recorded initial stop; legacy records without a locatable
    entry bar keep the previous read. (The old ratchet is
    PERSISTENT state — new_stop = max(p.stop, yesterday's EMA50),
    never down — but no core writer updates this sleeve's stored
    trail, so reading only max(stored, e50[-2]) lets the trail
    FALL when EMA50 declines.)"""
    closes = [float(b["c"]) for b in bl]
    e50 = ema(closes, 50)
    floor = float(pos.get("trail") or 0.0)
    if pos.get("stop_px"):
        floor = max(floor, float(pos["stop_px"]))
    dates = _dates(bl)
    entry_idx = None
    if pos.get("entry_date"):
        try:
            entry_idx = dates.index(str(pos["entry_date"])[:10])
        except ValueError:
            entry_idx = None
    if entry_idx is not None and len(e50) >= 2:
        cand = e50[entry_idx:len(e50) - 1]
        trail = max([floor] + cand) if cand else floor
    else:
        trail = max(floor, e50[-2]) if len(e50) >= 2 else floor
    return trail


# ------------------------------------------------------------ ENH arm
def earnings_flatten_enabled(extra):
    """ENH-phase_daily: context.extra["phase_daily_enhance"]
    ["earnings_flatten_arm"], default ON; OFF restores the
    pre-change ride-through rule exactly."""
    ov = (extra or {}).get("phase_daily_enhance")
    if isinstance(ov, dict) and "earnings_flatten_arm" in ov:
        return bool(ov["earnings_flatten_arm"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("phase_daily_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == EXP_ID \
            and isinstance(raw.get("records"), list):
        return {"exp_id": EXP_ID, "records": list(raw["records"])}
    return {"exp_id": EXP_ID, "records": []}


def flatten_session_for(earnings_iso, time_hint, bar_dates):
    """The session whose 15:55 ET evaluation flattens the position:
    the earnings session itself for an after-hours print (the print
    lands after that session's close), otherwise the last served
    session strictly before the earnings date (a pre-market or
    untimed print is never ridden into). None when no prior served
    session exists to name."""
    try:
        ed = date.fromisoformat(str(earnings_iso)[:10])
    except (TypeError, ValueError):
        return None
    if time_hint == "after":
        return ed.isoformat()
    prior = [d for d in bar_dates if d < ed.isoformat()]
    return prior[-1] if prior else None


def _flatten_decision(sym, session, earnings, earnings_time, fresh,
                      bar_dates):
    """(flatten_session, earnings_iso, hint) when the arm has a
    decision point today, else None. Fail closed: a stale/unserved
    calendar, an unknown symbol, or a confirmed no-earnings record
    (None date) has no decision point — nothing is invented."""
    if not fresh or sym not in earnings:
        return None
    ed = earnings.get(sym)
    if ed is None:
        return None
    hint = (earnings_time or {}).get(sym)
    fsess = flatten_session_for(ed, hint, bar_dates)
    if fsess is None or fsess != session:
        return None
    return fsess, str(ed)[:10], hint


def _after_flatten_arm(now_epoch):
    """True once the evaluation clock reaches 15:55 ET."""
    hm = datetime.fromtimestamp(float(now_epoch), tz=timezone.utc) \
        .astimezone(ET)
    return (hm.hour, hm.minute) >= FLATTEN_ARM_HM


class PhaseDaily(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        earnings = extra.get("earnings") or {}
        earnings_time = extra.get("earnings_time") or {}
        earnings_fresh = bool(extra.get("earnings_fresh"))
        arm_on = earnings_flatten_enabled(extra)
        journal = _enh_journal(extra)
        records = []
        flat_records = {}
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < 60:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            closes = [float(b["c"]) for b in bl]
            if pos:
                qty = float(pos.get("qty") or 0)  # WS4: actual held qty
                if qty <= 0:
                    continue
                trail = _trail_for(bl, pos)
                if closes[-1] < trail:
                    intents.append(Intent(
                        "exit", sym, qty=qty,
                        price_hint=round(closes[-1], 2),
                        reason="phase trail breach: close %.2f < trail %.2f "
                               "(EMA50 ratchet)" % (closes[-1], trail)))
                    continue
                # ENH earnings flatten: on the flatten session the
                # arm (treatment) exits the whole position at the
                # 15:55 ET evaluation; the control (switch OFF, the
                # frozen pre-change rule) rides through. A trail
                # breach above takes precedence — a dead premise
                # exits as a trail exit and never re-enters.
                dec = _flatten_decision(sym, context.session, earnings,
                                        earnings_time, earnings_fresh,
                                        _dates(bl))
                if dec is not None:
                    fsess, ed, hint = dec
                    armed = _after_flatten_arm(context.now)
                    records.append({
                        "symbol": sym, "session": context.session,
                        "kind": "flatten_decision",
                        "earnings_date": ed, "earnings_time": hint,
                        "flatten_session": fsess,
                        "close": closes[-1], "trail": trail,
                        "control": "ride_through",
                        "treatment": "flatten" if armed
                                     else "flatten_pending_1555",
                        "switch_on": arm_on})
                    if arm_on and armed:
                        flat_records[sym] = {
                            "qty": qty,
                            "entry_px": pos.get("entry_px"),
                            "entry_date": pos.get("entry_date"),
                            "trail": trail,
                            "stop_px": pos.get("stop_px"),
                            "episode_key": st.get("episode_key"),
                            "earnings_date": ed,
                            "flat_date": context.session}
                        intents.append(Intent(
                            "exit", sym, qty=qty,
                            price_hint=round(closes[-1], 2),
                            reason="phase earnings_flatten: close %.2f "
                                   "ahead of earnings %s (%s); re-entry "
                                   "after the print under trail %.2f"
                                   % (closes[-1], ed, hint or "untimed",
                                      trail)))
                continue
            # ENH re-entry: a booked earnings_flat record whose print
            # has passed (a post-print bar is served) resumes the
            # position at the session's close under its surviving
            # trail — unless the close has fallen through that
            # trail, in which case the premise is dead, the record
            # is consumed, and the symbol falls through to the
            # ordinary K5 flow below.
            flat = st.get("earnings_flat") if arm_on else None
            if flat and flat.get("earnings_date") \
                    and str(flat["earnings_date"])[:10] < context.session:
                dates = _dates(bl)
                if dates and dates[-1] > str(flat["earnings_date"])[:10]:
                    trail = _trail_for(bl, flat)
                    fqty = float(flat.get("qty") or 0)  # WS4: actual flattened qty
                    rec = {"symbol": sym, "session": context.session,
                           "kind": "reentry_decision",
                           "earnings_date": str(flat["earnings_date"])[:10],
                           "flat_date": flat.get("flat_date"),
                           "close": closes[-1], "trail": trail,
                           "control": "stay_flat", "switch_on": arm_on}
                    if closes[-1] < trail:
                        rec["treatment"] = "stay_flat_trail_breached"
                        records.append(rec)
                    elif fqty > 0 and open_n < MAX_POSITIONS:
                        stop_px = float(flat.get("stop_px") or trail)
                        rec["treatment"] = "reenter"
                        records.append(rec)
                        intents.append(Intent(
                            "enter", sym, qty=fqty,
                            price_hint=round(closes[-1], 2),
                            stop=round(stop_px, 2),
                            exit_rules=(ExitRule("stop", round(stop_px, 2)),),
                            reason="phase earnings re-entry: flattened %s "
                                   "before earnings %s; resumed at close "
                                   "%.2f under surviving trail %.2f"
                                   % (flat.get("flat_date"),
                                      str(flat["earnings_date"])[:10],
                                      closes[-1], trail)))
                        open_n += 1
                        continue
                    else:
                        rec["treatment"] = "reenter_blocked"
                        records.append(rec)
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            eps = detect_episodes(bl)
            if not eps:
                continue
            ep = eps[-1]
            key = "%s:%s" % (ep["start_date"], ep["end_date"])
            if st.get("episode_key") == key:
                continue
            trig = k5_trigger(bl, ep)
            if not trig:
                continue
            _idx, stop_px = trig
            px = ep["box_hi"]
            qty = size_qty(equity, px, stop_px)
            if qty <= 0:
                continue  # old k5_skip_size: rails size to 0 -> no trade
            intents.append(Intent(
                "enter", sym, qty=qty, price_hint=round(px, 2),
                stop=round(stop_px, 2),
                exit_rules=(ExitRule("stop", round(stop_px, 2)),),
                reason="phase K5: box %.2f/%.2f locked %s, trigger at box high"
                       % (ep["box_hi"], ep["box_lo"], ep["end_date"])))
            open_n += 1
        if records:
            journal["records"].extend(records)
            self.last_evaluation = {
                "phase_daily_enh_journal": journal,
                "earnings_flat": flat_records}
        return intents


def signal(bars, slice_state, context):
    return PhaseDaily().signal(bars, slice_state, context)
