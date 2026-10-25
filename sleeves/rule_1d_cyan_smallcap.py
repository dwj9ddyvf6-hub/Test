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
desk MAX_POSITIONS=10 is
core Risk's; the sleeve-local capacity check mirrors the old rank pass.

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}  (Data product)
  "log_mcap":   {SYM: float | None}  (EDGAR public float, fail closed)
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
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

ENH (IMPROVE-rule_1d_cyan_smallcap, Edge program 2026-10-24): the
cyan family's own -25% disaster stop, carried on the entry intent as
ExitRule("stop", 0.75 x entry) + stop=, exactly as daily_cyan_gbm
carries its restored disaster stop (DISASTER_STOP = 0.25). Switched
by context.extra["rule_1d_cyan_smallcap_enhance"]["disaster_stop"]
(default ON; OFF restores the pre-change rule exactly — time exit
only). Paired control/treatment records ride the
rule_1d_cyan_smallcap_enh_journal (adopted from context.extra, filed
on self.last_evaluation); the control never emits intents.
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 21
LANE = "1D"
SIGNAL_KIND = "cyan"
MIN_DV20 = 1_000_000
MCAP_THRESHOLD = 9.377766990661621
NOTIONAL_FRACTION = 0.01  # A2-06: the executed sizing law
# (1% of equity notional per position) -- see docstring note
MAX_POSITIONS = 10  # sleeve_core.MAX_POSITIONS (desk-wide cap is core Risk's)

CONDITIONS = (
    {"feature": "pxn", "op": "==", "value": 2},
    {"feature": "di", "op": "between", "lo": -10.590971183776855,
     "hi": 12.556758308410648},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1d_cyan_smallcap", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)

# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-RULE-1D-CYAN-SMALLCAP-20261024"
DISASTER_STOP = 0.25  # the cyan family's own (daily_cyan_gbm source line 44)


def disaster_stop_enabled(extra):
    """ctx.extra['rule_1d_cyan_smallcap_enhance']['disaster_stop'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("rule_1d_cyan_smallcap_enhance")
    if isinstance(ov, dict) and "disaster_stop" in ov:
        return bool(ov["disaster_stop"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("rule_1d_cyan_smallcap_enh_journal")
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
    """Mean 20-session dollar volume ending at the last bar (old dv20)."""
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


class Rule1dCyanSmallcap(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        fires = extra.get("rule_fires") or {}
        log_mcap = extra.get("log_mcap") or {}
        equity = float(context.equity or 0.0)
        enh_on = disaster_stop_enabled(extra)
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
                        reason="rule_1d_cyan_smallcap: %d sessions >= hold %d (staged early)"
                               % (n, HOLD_BARS)))
        if equity <= 0 or not fires:
            self.last_evaluation = {
                "rule_1d_cyan_smallcap_enh_journal": journal}
            return intents
        open_n = len(book)
        for sym in sorted(fires):
            if sym in book or open_n >= MAX_POSITIONS:
                continue
            bl = bars.get(sym) or []
            if not bl:
                continue
            dates = _dates(bl)
            last_date = dates[-1]
            px = float(bl[-1]["c"])
            hit = None
            for f in fires.get(sym) or []:
                if isinstance(f, dict) and f.get("date") == last_date \
                        and rule_pass(f.get("features")):
                    hit = f
                    break
            if hit is None:
                continue
            if not (5.0 <= px < 10.0):
                continue
            if dv20(bl) < MIN_DV20:
                continue
            lm = log_mcap.get(sym)
            try:
                lm = float(lm) if lm is not None else None
            except (TypeError, ValueError):
                lm = None  # non-numeric mcap fails closed, never raises
            if lm is None or not math.isfinite(lm) \
                    or lm > MCAP_THRESHOLD:
                continue  # fail closed on missing mcap (old law)
            qty = int((equity * NOTIONAL_FRACTION) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            stop_px = round(px * (1 - DISASTER_STOP), 2)
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
                    reason="rule_1d_cyan_smallcap: cyan fire %s pxn/di pass, "
                           "px=%.2f dv20=%.0f log_mcap=%.4f <= %.4f"
                           % (last_date, px, dv20(bl), float(lm),
                              MCAP_THRESHOLD)))
            else:
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                    exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                    reason="rule_1d_cyan_smallcap: cyan fire %s pxn/di pass, "
                           "px=%.2f dv20=%.0f log_mcap=%.4f <= %.4f"
                           % (last_date, px, dv20(bl), float(lm),
                              MCAP_THRESHOLD)))
            open_n += 1
        self.last_evaluation = {
            "rule_1d_cyan_smallcap_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return Rule1dCyanSmallcap().signal(bars, slice_state, context)
