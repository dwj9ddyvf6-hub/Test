"""Daily Cyan GBM — lean-desk port.

EXTRACTED from the old desk's daily_cyan_gbm_sleeve.py. The GBM score
itself is produced by an external Node scorer (dcg_scorer/dcg_score.mjs
+ a frozen model file) over a market-feature frame — in the lean desk
that score arrives as a core Data product via context.extra (named
misfit, ports/daily_cyan_gbm.md); a sleeve never shells out. The
selection law is ported verbatim: score >= SCORE_CUT (0.00208, the
2026-10-05 recalibration: 90th percentile of scores), price >= $5,
exit at the close of the 21st session after entry (HOLD_BARS).
dv20 (mean 20d dollar volume) ported as a pure helper. Old sleeve
risk fraction 0.1% (sleeve_core Sleeve cost/risk arg 0.001).

The old build_market VIX-staleness law is a core Data duty here: if
the core's score feed is stale it must not deliver scores at all
(fail closed: no scores in extra = no entries).

Inputs via context.extra:
  "dcg_scores": {SYM: score} — the Data product for context.session
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
from datetime import datetime, timezone

from . import dcg_core
from .compat import BaseSleeve, Intent, SleeveConfig

HOLD_BARS = 21
SCORE_CUT = 0.00208
MIN_PX = 5.0
RISK_FRACTION = 0.001

CONFIG = SleeveConfig(
    sleeve_id="daily_cyan_gbm", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


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
    ds = _dates(bars)
    try:
        return len(ds) - 1 - ds.index(entry_date)
    except ValueError:
        return None


RANK_HM, FILL_HM = (16, 32), (10, 32)       # old crons daily-cyan-gbm rank 16:32, fill 10:32 ET
COST_BPS_SIDE = 0.001
DISASTER_STOP = 0.25
MIN_DV20 = 1_000_000


def signals(scores, context=None):
    """old mode_rank: score >= SCORE_CUT on the signal bar (the name's last bar), $5+, $1M dv20; by score."""
    facts = scores.get("facts") or {}
    out = []
    for s, f in (scores.get("gbm") or {}).items():
        fa = facts.get(s) or {}
        if f.get("score") is None or f["score"] < SCORE_CUT or f.get("date") != fa.get("date"):
            continue
        if fa.get("px") is None or fa["px"] < MIN_PX or (fa.get("dv20") or 0) < MIN_DV20:
            continue
        out.append((s, f["score"]))
    out.sort(key=lambda t: -t[1])
    return out


class DailyCyanGbm(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old runtime (dcg_core) — the rank stages after the close (next_meta), the next
        session's fill pass executes the old sleeve_core fill law, market-on-close."""
        if dcg_core.phase(context, RANK_HM, FILL_HM) != "fill":
            return []
        meta = (context.extra or {}).get("meta") or {}
        return dcg_core.fill(Intent, context, meta, COST_BPS_SIDE, "daily_cyan_gbm", disaster_stop=DISASTER_STOP)


def next_meta(bars, slice_state, context, intents=()):
    return dcg_core.next_meta(context, (context.extra or {}).get("meta") or {}, signals, HOLD_BARS, bars,
                              COST_BPS_SIDE, "daily_cyan_gbm", RANK_HM, FILL_HM)


def signal(bars, slice_state, context):
    return DailyCyanGbm().signal(bars, slice_state, context)
