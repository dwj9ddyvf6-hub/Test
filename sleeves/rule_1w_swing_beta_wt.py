"""Rule 1W Swing Beta/WaveTrend — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1w_swing_beta_wt.py + rule_sleeve_base.py
(rule V2-1W-SWING-RAW-H126-727ea853, tier A). Fire detection is the external
Node GBM rule scorer's — fires arrive as a core Data product via
context.extra (a sleeve never shells out; ports/rule_1w_swing_beta_wt.md).

Rule: 1W swing fire AND beta to SPY >= 1.3545490503311157 AND WaveTrend
level (wt1) >= 25.92674789428711 AND EMA ribbon slope >=
0.009481946006417274. Eligibility: $5+ and $1M dv20. Entry: next session
close. Hold: 126 sessions; exit staged at sessions_since >= HOLD-1 (old
stage-one-early fix).

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.

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

ENH (IMPROVE-rule_1w_swing_beta_wt, Edge program 2026-10-24): size
each position by the passing fire's own beta — qty =
(equity x 1% / price) / beta_fire — so every slot carries equal
SPY-equivalent exposure (the flat 1% the current law pretends to
allocate). The beta >= 1.3545 entry condition bounds the divisor
below, so quantities only ever shrink versus the control; a scaled
quantity flooring to zero takes no position (OBS-1 preserved).
Switched by context.extra["rule_1w_swing_beta_wt_enhance"]
["beta_sizing"] (default ON; OFF restores the pre-change rule
exactly). Paired records ride the rule_1w_swing_beta_wt_enh_journal.
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 126
LANE = "1W"
SIGNAL_KIND = "swing"
MIN_PX = 5.0
MIN_DV20 = 1_000_000
NOTIONAL_FRACTION = 0.01  # A2-06: the executed sizing law
# (1% of equity notional per position) -- see docstring note
MAX_POSITIONS = 10

CONDITIONS = (
    {"feature": "beta", "op": ">=", "value": 1.3545490503311157},
    {"feature": "wt1", "op": ">=", "value": 25.92674789428711},
    {"feature": "ribbons", "op": ">=", "value": 0.009481946006417274},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1w_swing_beta_wt", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)

# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-RULE-1W-SWING-BETA-WT-20261024"


def beta_sizing_enabled(extra):
    """ctx.extra['rule_1w_swing_beta_wt_enhance']['beta_sizing'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("rule_1w_swing_beta_wt_enhance")
    if isinstance(ov, dict) and "beta_sizing" in ov:
        return bool(ov["beta_sizing"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("rule_1w_swing_beta_wt_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}


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
    """Sessions elapsed since entry — the old counting law (old sells
    loop: bars dated strictly after the entry date). Identical to the
    index count when the entry bar is in the list, and still correct
    when it has aged out of the delivered window (P3 audit 2026-10-15:
    the index form returned None then, so the sleeve exit never fired)."""
    entry = str(entry_date)[:10]
    return sum(1 for d in _dates(bars) if d > entry)


class Rule1wSwingBetaWt(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        fires = extra.get("rule_fires") or {}
        equity = float(context.equity or 0.0)
        enh_on = beta_sizing_enabled(extra)
        journal = _enh_journal(extra)
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
                        exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                        reason="rule_1w_swing_beta_wt: %d sessions >= hold %d (staged early)"
                               % (n, HOLD_BARS)))
        if equity <= 0 or not fires:
            self.last_evaluation = {
                "rule_1w_swing_beta_wt_enh_journal": journal}
            return intents
        open_n = len(book)
        for sym in sorted(fires):
            if sym in book or open_n >= MAX_POSITIONS:
                continue
            bl = bars.get(sym) or []
            if not bl:
                continue
            last_date = _dates(bl)[-1]
            px = float(bl[-1]["c"])
            hit_fire = None
            for f in fires.get(sym) or []:
                if isinstance(f, dict) and f.get("date") == last_date \
                        and rule_pass(f.get("features")):
                    hit_fire = f
                    break
            if hit_fire is None or px < MIN_PX or dv20(bl) < MIN_DV20:
                continue
            beta = float((hit_fire.get("features") or {})["beta"])
            qty_control = int((equity * NOTIONAL_FRACTION) // px)
            qty_treat = int((equity * NOTIONAL_FRACTION / beta) // px)
            journal["records"].append({
                "symbol": sym, "session": context.session, "beta": beta,
                "control": {"qty": qty_control},
                "treatment": {"qty": qty_treat},
                "enhance_switch": enh_on})
            qty = qty_treat if enh_on else qty_control
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                reason="rule_1w_swing_beta_wt: swing fire %s beta/wt1/ribbons "
                       "pass, px=%.2f dv20=%.0f" % (last_date, px, dv20(bl))))
            open_n += 1
        self.last_evaluation = {
            "rule_1w_swing_beta_wt_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return Rule1wSwingBetaWt().signal(bars, slice_state, context)
