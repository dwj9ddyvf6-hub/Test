"""Rule 1W Cyan Mom/ADX — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1w_cyan_mom_adx.py + rule_sleeve_base.py
(rule V2-1W-CYAN-RAW-H126-f10092bc, tier A). Fire detection is the external
Node GBM rule scorer's — fires arrive as a core Data product via
context.extra (a sleeve never shells out; ports/rule_1w_cyan_mom_adx.md).

Rule: 1W cyan fire AND log dv20 (feature "dv") <= 7.350284290313721 AND
126-session return ("mom") >= 0.44456708133220685 AND ADX >=
25.795216751098632. Eligibility: $5+ and $1M dv20 (desk filter, computed
from bars — distinct from the rule's log-dv feature). Entry: next session
close. Hold: 126 sessions; exit staged at sessions_since >= HOLD-1 (old
stage-one-early fix). Risk 0.1%.

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timezone

from . import dcg_core
from .compat import BaseSleeve, Intent, SleeveConfig

HOLD_BARS = 126
LANE = "1W"
SIGNAL_KIND = "cyan"
MIN_PX = 5.0
MIN_DV20 = 1_000_000
RISK_FRACTION = 0.001
MAX_POSITIONS = 10

CONDITIONS = (
    {"feature": "dv", "op": "<=", "value": 7.350284290313721},
    {"feature": "mom", "op": ">=", "value": 0.44456708133220685},
    {"feature": "adx", "op": ">=", "value": 25.795216751098632},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1w_cyan_mom_adx", cadence_s=300, universe=(),
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
    if len(bars) < 20:
        return 0.0
    return sum(float(b["c"]) * float(b["v"]) for b in bars[-20:]) / 20.0


def sessions_since(bars, entry_date):
    ds = _dates(bars)
    try:
        return len(ds) - 1 - ds.index(entry_date)
    except ValueError:
        return None


RANK_HM, FILL_HM = (16, 38), (10, 38)       # old crons rank 16:38, fill 10:38 ET
COST_BPS_SIDE = 0.001


def signals(scores, context=None):
    """old mode_rank: the rule on the signal bar (the name's last bar) + the desk filter, scorer order."""
    facts = scores.get("facts") or {}
    out = []
    for s, f in ((scores.get("rules") or {}).get("1W:cyan") or {}).items():
        fa = facts.get(s) or {}
        if f.get("date") != fa.get("date"):
            continue
        feats = dict(f.get("features") or {})
        if not rule_pass(feats, CONDITIONS):
            continue
        px = fa.get("px")
        if px is None or not (px >= MIN_PX):
            continue
        if (fa.get("dv20") or 0) < MIN_DV20:
            continue
        out.append((s, f["date"]))
    return out


class Rule1wCyanMomAdx(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old runtime (dcg_core) — the rank stages after the close (next_meta), the next
        session's fill pass executes the old sleeve_core fill law, market-on-close."""
        if dcg_core.phase(context, RANK_HM, FILL_HM) != "fill":
            return []
        meta = (context.extra or {}).get("meta") or {}
        return dcg_core.fill(Intent, context, meta, COST_BPS_SIDE, "rule_1w_cyan_mom_adx", disaster_stop=None)


def next_meta(bars, slice_state, context, intents=()):
    return dcg_core.next_meta(context, (context.extra or {}).get("meta") or {}, signals, HOLD_BARS, bars,
                              COST_BPS_SIDE, "rule_1w_cyan_mom_adx", RANK_HM, FILL_HM)


def signal(bars, slice_state, context):
    return Rule1wCyanMomAdx().signal(bars, slice_state, context)
