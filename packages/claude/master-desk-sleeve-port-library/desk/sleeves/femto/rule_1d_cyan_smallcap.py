"""Rule 1D Cyan Small-Cap — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1d_cyan_smallcap.py + rule_sleeve_base.py
(rule V4-1D-CYAN-RAW-H21-COV-bb707043, tier A). The fire detection itself is
done by the external Node GBM rule scorer (dcg_rule_score.mjs + the frozen
tensor_gbm_v4_1D_cyan_full model) — in the lean desk those fires arrive as a
core Data product via context.extra, exactly as Daily Cyan GBM's scores do;
a sleeve never shells out (named misfit, ports/rule_1d_cyan_smallcap.md).
The selection law is ported verbatim: rule conditions (exact thresholds),
the $5 <= px < $10 band, the $1M dv20 desk filter, and the EDGAR log-mcap
test (fail closed: missing mcap => skipped). The mcap VALUE also arrives
via extra (the EDGAR public-float computation is a Data product).

Rule: 1D cyan fire AND pxn == 2 AND di between -10.590971183776855 and
12.556758308410648 AND log10 mcap <= 9.377766990661621.
Entry: next session close after the signal bar (core executes).
Hold: 21 sessions; exit staged at sessions_since >= HOLD-1 so the core's
next-session fill lands on the 21st close (the old sleeve's 2026-10-07
stage-one-early fix, verbatim in effect).
Risk: 0.1% (old Sleeve cost/risk arg 0.001); desk MAX_POSITIONS=10 is
core Risk's; the sleeve-local capacity check mirrors the old rank pass.

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}  (Data product)
  "log_mcap":   {SYM: float | None}  (EDGAR public float, fail closed)
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timezone

from . import dcg_core
from .compat import BaseSleeve, Intent, SleeveConfig

HOLD_BARS = 21
LANE = "1D"
SIGNAL_KIND = "cyan"
MIN_DV20 = 1_000_000
MCAP_THRESHOLD = 9.377766990661621
RISK_FRACTION = 0.001
MAX_POSITIONS = 10  # sleeve_core.MAX_POSITIONS (desk-wide cap is core Risk's)

CONDITIONS = (
    {"feature": "pxn", "op": "==", "value": 2},
    {"feature": "di", "op": "between", "lo": -10.590971183776855,
     "hi": 12.556758308410648},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1d_cyan_smallcap", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def cond_pass(feats, cond):
    """Verbatim port of rule_sleeve_base.cond_pass (None feature fails)."""
    v = (feats or {}).get(cond["feature"])
    if v is None:
        return False
    try:
        v = float(v)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(v):
        return False
    op = cond["op"]
    if op == "<=":
        return v <= cond["value"]
    if op == ">=":
        return v >= cond["value"]
    if op == "==":
        return v == cond["value"]
    if op == "between":
        return cond["lo"] <= v <= cond["hi"]
    raise ValueError("unknown op %s" % op)


def rule_pass(feats, conditions=CONDITIONS):
    return all(cond_pass(feats, c) for c in conditions)


def dv20(bars):
    """Mean 20-session dollar volume ending at the last bar (old dv20)."""
    if len(bars) < 20:
        return 0.0
    return sum(float(b["c"]) * float(b["v"]) for b in bars[-20:]) / 20.0


def sessions_since(bars, entry_date):
    ds = _dates(bars)
    try:
        return len(ds) - 1 - ds.index(entry_date)
    except ValueError:
        return None


RANK_HM, FILL_HM = (16, 34), (10, 34)       # old crons rank 16:34, fill 10:34 ET
COST_BPS_SIDE = 0.001


def signals(scores, context=None):
    """old mode_rank: the rule on the signal bar (the name's last bar) + the desk filter, scorer order."""
    facts = scores.get("facts") or {}
    out = []
    for s, f in ((scores.get("rules") or {}).get("1D:cyan") or {}).items():
        fa = facts.get(s) or {}
        if f.get("date") != fa.get("date"):
            continue
        feats = dict(f.get("features") or {})
        if not rule_pass(feats, CONDITIONS):
            continue
        px = fa.get("px")
        if px is None or not (5.0 <= px < 10.0):
            continue
        if (fa.get("dv20") or 0) < MIN_DV20:
            continue
        lm = fa.get("log_mcap")                         # EDGAR public float (fail closed)
        if lm is None or lm > MCAP_THRESHOLD:
            continue
        out.append((s, f["date"]))
    return out


class Rule1dCyanSmallcap(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old runtime (dcg_core) — the rank stages after the close (next_meta), the next
        session's fill pass executes the old sleeve_core fill law, market-on-close."""
        if dcg_core.phase(context, RANK_HM, FILL_HM) != "fill":
            return []
        meta = (context.extra or {}).get("meta") or {}
        return dcg_core.fill(Intent, context, meta, COST_BPS_SIDE, "rule_1d_cyan_smallcap", disaster_stop=None)


def next_meta(bars, slice_state, context, intents=()):
    return dcg_core.next_meta(context, (context.extra or {}).get("meta") or {}, signals, HOLD_BARS, bars,
                              COST_BPS_SIDE, "rule_1d_cyan_smallcap", RANK_HM, FILL_HM)


def signal(bars, slice_state, context):
    return Rule1dCyanSmallcap().signal(bars, slice_state, context)
