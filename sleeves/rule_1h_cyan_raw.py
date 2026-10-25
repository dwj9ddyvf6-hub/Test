"""Rule 1H Cyan Raw — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1h_cyan_raw.py (rule
V3-1H-CYAN-RAW-H7-aab0a308). Fire detection is the external Node 1H scorer
(dcg_rule_1h.mjs) — fires arrive as a core Data product via context.extra
(a sleeve never shells out; ports/rule_1h_cyan_raw.md).

Rule (exact thresholds): 1H cyan fire AND signal-bar range >= 2.05 x
ATR14 (feature "rangeatr") AND WaveTrend spread (wt1-wt2, "wtgap") >=
6.88 AND SMH weekly uptrend ("smhUp" == 1). The old per-fire guards are
ported: non-dict fire rows, missing/non-numeric rangeatr/wtgap, and NaN
scores are SKIPPED per-fire (a NaN was truthy and False-comparing in the
pre-fix code — the BC14S-9 class).
Eligibility: $5+ and $1M 20-day dollar volume, point-in-time: dv20 from
the DAILY bars, ending at the latest daily bar <= the signal's ET session
date (the old 2026-10-06 fix — an exact-date match always missed intraday
and killed every signal; this sleeve had never traded on that bug).
Entry: next hourly bar after the signal bar. Hold: 7 hourly bars after
entry, counted with the old _bar_after law (a bare-date entry_time counts
only bars on a LATER ET date — pre-fill bars of the entry day never
count). Universe: the old 41-name 1H basket (bars keys here).

Inputs via context.extra:
  "rule_fires_1h": {SYM: [{"t": iso-ts, "rangeatr": .., "wtgap": ..,
                    "smhUp": 0|1}]}   (Data product, 1H scorer)
  "daily_bars": {SYM: [daily bar dicts]}  (for the dv20 desk filter)
  "sleeve_state": {SYM: {"position": {"entry_date"|"entry_time","qty"} | None}}
Bars (the `bars` argument): 1H dicts {"t","o","h","l","c","v"} ascending,
"t" epoch seconds of the bar open. Only the latest CLOSED bar can be the
signal bar: the core delivers closed bars only; a fire whose "t" is not
the last bar's timestamp is ignored (old law).

Sizing (A2-06 reconciliation, 2026-10-16): 1% of equity notional per
position (NOTIONAL_FRACTION, carried on the intent's qty_hint), max
10 positions. No risk-fraction sizing exists in the source: the old
framework sized centrally in sleeve_core.run_fill (equal weight over
a 30% sleeve cap, Decision #20), sleeves never computed a quantity,
and the 0.001 in the old Sleeve(...) constructor was its
cost_bps_side (10bp/side cost model) -- the "Risk 0.1%" this port
originally declared was that cost arg misread (EVIDENCE-FINAL2).
Stops: none in the source -- the old sleeve set no
disaster_stop_pct; the only exit is the time hold above.

ENH (IMPROVE-rule_1h_cyan_raw, Edge program 2026-10-24): the entry
intent additionally carries ExitRule("stop", <signal bar low>) +
stop= — the signal bar is bars[-1], already in hand at entry; the
level is the trade's own invalidation (the expansion that qualified
the trade is undone below it), no new parameter. Switched by
context.extra["rule_1h_cyan_raw_enhance"]["signal_low_stop"]
(default ON; OFF restores the pre-change rule exactly — time exit
only). Paired records ride the rule_1h_cyan_raw_enh_journal.
"""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

HOLD_BARS = 7
MIN_PX = 5.0
MIN_DV20 = 1_000_000
RANGE_ATR_MIN = 2.05
WTGAP_MIN = 6.88
NOTIONAL_FRACTION = 0.01  # A2-06: the executed sizing law
# (1% of equity notional per position) -- see docstring note
MAX_POSITIONS = 10

CONFIG = SleeveConfig(
    sleeve_id="rule_1h_cyan_raw", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)

# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-RULE-1H-CYAN-RAW-20261024"


def signal_low_stop_enabled(extra):
    """ctx.extra['rule_1h_cyan_raw_enhance']['signal_low_stop'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("rule_1h_cyan_raw_enhance")
    if isinstance(ov, dict) and "signal_low_stop" in ov:
        return bool(ov["signal_low_stop"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("rule_1h_cyan_raw_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}


def _iso_t(epoch):
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat()


def _et_date_of_ts(epoch):
    return datetime.fromtimestamp(float(epoch), tz=ET).date().isoformat()


def bar_after(entry_t, bar_epoch):
    """Old _bar_after law, epoch form: True when the bar is strictly
    after the entry. A bare YYYY-MM-DD entry counts only bars whose ET
    date is LATER than the entry date (never same-day pre-fill bars)."""
    et = str(entry_t)
    if len(et) == 10:
        return _et_date_of_ts(bar_epoch) > et
    try:
        entry_epoch = datetime.fromisoformat(
            et.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return _iso_t(bar_epoch) > et
    return float(bar_epoch) > entry_epoch


def fire_passes(f):
    """(ok, rangeatr, wtgap): the rule conditions + per-fire NaN/type
    guards, verbatim in effect from the old rank loop."""
    if not isinstance(f, dict):
        return False, None, None
    try:
        ra = float(f.get("rangeatr"))
        wg = float(f.get("wtgap"))
    except (TypeError, ValueError):
        return False, None, None
    if not (math.isfinite(ra) and math.isfinite(wg)):
        return False, None, None
    if ra < RANGE_ATR_MIN or wg < WTGAP_MIN:
        return False, ra, wg
    if f.get("smhUp") != 1:
        return False, ra, wg
    return True, ra, wg


def dv20_daily(daily_bars, signal_date):
    """20d dollar volume ending at the latest daily bar <= signal_date
    (point-in-time; old 2026-10-06 fix). 0 when insufficient history."""
    if not daily_bars:
        return 0.0
    dates = [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                    tz=timezone.utc).date().isoformat()
             for b in daily_bars]
    idx = None
    for i, d in enumerate(dates):
        if d <= signal_date:
            idx = i
        else:
            break
    if idx is None or idx < 19:
        return 0.0
    return sum(float(b["c"]) * float(b["v"])
               for b in daily_bars[idx - 19:idx + 1]) / 20.0


class Rule1hCyanRaw(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        fires = extra.get("rule_fires_1h") or {}
        daily = extra.get("daily_bars") or {}
        equity = float(context.equity or 0.0)
        enh_on = signal_low_stop_enabled(extra)
        journal = _enh_journal(extra)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            bl = bars.get(sym) or []
            entry_t = p.get("entry_time") or p.get("entry_date")
            if not entry_t or not bl:
                continue
            n = sum(1 for b in bl if bar_after(entry_t, b["t"]))
            if n >= HOLD_BARS:
                qty = int(float(p.get("qty") or 0))
                if qty > 0:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2),
                        exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                        reason="rule_1h_cyan_raw: %d hourly bars after entry "
                               ">= hold %d" % (n, HOLD_BARS)))
        if equity <= 0 or not fires:
            self.last_evaluation = {
                "rule_1h_cyan_raw_enh_journal": journal}
            return intents
        open_n = len(book)
        for sym in sorted(fires):
            if sym in book or open_n >= MAX_POSITIONS:
                continue
            bl = bars.get(sym) or []
            if len(bl) < 100:  # old rank required >= 100 1H bars to score
                continue
            last_t = _iso_t(bl[-1]["t"])
            px = float(bl[-1]["c"])
            hit = None
            for f in fires.get(sym) or []:
                ok, ra, wg = fire_passes(f)
                if not ok:
                    continue
                ft = str(f.get("t") or "")
                match = (ft == last_t)
                if not match:
                    try:  # epoch comparison tolerates Z / offset spellings
                        match = abs(datetime.fromisoformat(
                            ft.replace("Z", "+00:00")).timestamp()
                            - float(bl[-1]["t"])) < 1.0
                    except ValueError:
                        match = False
                if match:
                    hit = (ra, wg)
                    break
            if hit is None:
                continue
            sig_date = _et_date_of_ts(bl[-1]["t"])
            if px < MIN_PX:
                continue
            if dv20_daily(daily.get(sym) or [], sig_date) < MIN_DV20:
                continue
            qty = int((equity * NOTIONAL_FRACTION) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            stop_px = round(float(bl[-1]["l"]), 2)
            journal["records"].append({
                "symbol": sym, "session": context.session,
                "control": {"exit_rules": ["time_bars"]},
                "treatment": {"exit_rules": ["stop", "time_bars"],
                              "stop": stop_px},
                "enhance_switch": enh_on})
            if enh_on:
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                    stop=stop_px,
                    exit_rules=(ExitRule("stop", stop_px),
                                ExitRule("time_bars", float(HOLD_BARS))),
                    reason="rule_1h_cyan_raw: cyan fire %s rangeatr=%.2f "
                           "wtgap=%.2f smhUp=1 px=%.2f"
                           % (last_t, hit[0], hit[1], px)))
            else:
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                    exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                    reason="rule_1h_cyan_raw: cyan fire %s rangeatr=%.2f "
                           "wtgap=%.2f smhUp=1 px=%.2f"
                           % (last_t, hit[0], hit[1], px)))
            open_n += 1
        self.last_evaluation = {"rule_1h_cyan_raw_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return Rule1hCyanRaw().signal(bars, slice_state, context)
