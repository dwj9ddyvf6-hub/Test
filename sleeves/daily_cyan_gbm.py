"""Daily Cyan GBM — lean-desk port.

EXTRACTED from the old desk's daily_cyan_gbm_sleeve.py. The GBM score
itself is produced by an external Node scorer (dcg_scorer/dcg_score.mjs
+ a frozen model file) over a market-feature frame — in the lean desk
that score arrives as a core Data product via context.extra (named
misfit, ports/daily_cyan_gbm.md); a sleeve never shells out. The
selection law is ported verbatim: score >= SCORE_CUT (0.00208, the
2026-10-05 recalibration: 90th percentile of scores), price >= $5,
$1M dv20 on the signal day (old MIN_DV20 desk filter), capacity
before append against MAX_POSITIONS=10 counting the book (old
sleeve_core.MAX_POSITIONS), non-finite/non-numeric scores skipped
(old BC14A-12 guard), exit at the close of the 21st session after
entry (HOLD_BARS) staged one session early (old 2026-10-07 law:
sells staged at sessions_since >= HOLD_BARS - 1 so the next-session
fill lands on the 21st close). dv20 (mean 20d dollar volume) ported
as a pure helper. Old sleeve cost model 10bp/side (the Sleeve(...) constructor's
third arg, 0.001 -- a cost_bps_side the original port misread as
a "risk fraction"; the old framework sized centrally in
sleeve_core.run_fill, never by risk). Sizing here, unchanged:
1% of equity notional per position (NOTIONAL_FRACTION), max 10
positions; risk_pct is None -- no risk claim (A2-06
reconciliation, 2026-10-16, EVIDENCE-FINAL2). Disaster stop:
the old source set SL.disaster_stop_pct = 0.25
(daily_cyan_gbm_sleeve.py:44; 2026-10-10 audit, Decision #18
family) and the original port dropped it -- restored
2026-10-16: entries carry the -25% stop and core/protection
QUALIFYING arms it at the broker, as for gate_1h / leader_d /
leader_sc. [P3 audit 2026-10-15: the dv20 filter, the
capacity cap, the staged-early exit and the score guard were dropped
in the original port — restored here from the old source.]

The old build_market VIX-staleness law is a core Data duty here: if
the core's score feed is stale it must not deliver scores at all
(fail closed: no scores in extra = no entries).

Inputs via context.extra:
  "dcg_scores": {SYM: score} — the Data product for context.session
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 21
SCORE_CUT = 0.00208  # pre-change absolute cut (the experiment control)


# --- ENH 2026-10-24 (Edge IMPROVE-daily_cyan_gbm, Group B LEAP) -------
# Replace the frozen absolute cut with the session's own 90th
# percentile of delivered scores (the sleeve's stated "top tenth" law).
# Switch: extra["daily_cyan_gbm_improve"] {"percentile90": bool},
# default ON; OFF restores the SCORE_CUT comparison exactly. Paired
# records go to extra["daily_cyan_gbm_exp_journal"]["records"].
EXP_ID_DCG = "ENH-DCG-20261024"


def _dcg_enh_enabled(extra):
    ov = (extra or {}).get("daily_cyan_gbm_improve")
    if isinstance(ov, dict) and "percentile90" in ov:
        return bool(ov["percentile90"])
    return True


def percentile90(values):
    """90th percentile, linear interpolation (numpy default method)."""
    vals = sorted(float(v) for v in values)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    rank = 0.90 * (len(vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (rank - lo)
MIN_PX = 5.0
MIN_DV20 = 1_000_000  # old MIN_DV20 desk filter on the signal day
MAX_POSITIONS = 10  # sleeve_core.MAX_POSITIONS (old capacity law)
NOTIONAL_FRACTION = 0.01  # A2-06: executed sizing law (see above)
DISASTER_STOP = 0.25  # old SL.disaster_stop_pct (source line 44)

CONFIG = SleeveConfig(
    sleeve_id="daily_cyan_gbm", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def dv20(bars):
    """Mean 20-session dollar volume (old dv20 over the bar list)."""
    if len(bars) < 20:
        return None
    vals = [float(b["c"]) * float(b["v"]) for b in bars[-20:]]
    return sum(vals) / 20.0


def sessions_since(bars, entry_date):
    """Sessions elapsed since entry — the old counting law: bars dated
    strictly after the entry date (identical to the index count when
    the entry bar is in the list, and still correct when it has aged
    out of the delivered window)."""
    entry = str(entry_date)[:10]
    return sum(1 for d in _dates(bars) if d > entry)


class DailyCyanGbm(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        scores = extra.get("dcg_scores") or {}
        equity = float(context.equity or 0.0)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            bl = bars.get(sym) or []
            n = sessions_since(bl, p.get("entry_date")) if p.get("entry_date") else None
            if n is not None and n >= HOLD_BARS - 1:
                qty = int(float(p.get("qty") or 0))
                if qty > 0 and bl:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2),
                        reason="daily_cyan_gbm: %d sessions held >= %d (staged early)"
                               % (n, HOLD_BARS)))
        if equity <= 0 or not scores:
            return intents

        _enh_on = _dcg_enh_enabled(extra)
        _finite = [float(sc) for sc in scores.values()
                   if isinstance(sc, (int, float))
                   and not isinstance(sc, bool)
                   and math.isfinite(float(sc))]
        _p90 = percentile90(_finite) if _finite else None
        _bar = _p90 if (_enh_on and _p90 is not None) else SCORE_CUT
        _jr = (extra.get("daily_cyan_gbm_exp_journal") or {})
        if isinstance(_jr, dict) and isinstance(_jr.get("records"), list):
            _jr["records"].append({
                "exp_id": EXP_ID_DCG, "session": context.session,
                "p90": _p90, "score_cut": SCORE_CUT,
                "control_eligible": sorted(
                    s for s, sc in scores.items()
                    if isinstance(sc, (int, float))
                    and not isinstance(sc, bool)
                    and math.isfinite(float(sc)) and sc >= SCORE_CUT),
                "treatment_eligible": sorted(
                    s for s, sc in scores.items()
                    if isinstance(sc, (int, float))
                    and not isinstance(sc, bool)
                    and math.isfinite(float(sc)) and _p90 is not None
                    and sc >= _p90)})

        def _ok_score(sc):
            # Old BC14A-12 guard: non-numeric / bool / NaN / inf scores
            # are skipped, never compared or sorted on.
            return (isinstance(sc, (int, float))
                    and not isinstance(sc, bool)
                    and math.isfinite(float(sc)) and sc >= _bar)

        ranked = sorted(((s, float(sc)) for s, sc in scores.items()
                         if _ok_score(sc)),
                        key=lambda t: -t[1])
        open_n = len(book)
        for sym, sc in ranked:
            if sym in book or open_n >= MAX_POSITIONS:
                continue  # capacity tested BEFORE append (old law)
            bl = bars.get(sym) or []
            if not bl:
                continue
            px = float(bl[-1]["c"])
            if px < MIN_PX:
                continue
            dv = dv20(bl)
            if dv is None or dv < MIN_DV20:
                continue  # $1M dv20 desk filter (old MIN_DV20)
            qty = int((equity * NOTIONAL_FRACTION) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            stop_px = round(px * (1 - DISASTER_STOP), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("time_bars", float(HOLD_BARS))),
                reason="daily_cyan_gbm: score=%.5f >= cut %.5f dv20=%s"
                       % (sc, _bar, round(dv, 0))))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return DailyCyanGbm().signal(bars, slice_state, context)
