"""Tensor Red Dip — lean-desk port.

EXTRACTED from the old desk's tensor_red_dip_sleeve.py. The signal
parse (read_fresh_signals semantics) and all decision constants are
ported verbatim; the journal/broker plumbing is core-owned — engine
signals arrive via context.extra from core Data (Decision #108 single
door). See ports/tensor_red_dip.md.

Strategy (old module): on a FEAR day (QQQ day-so-far <= -1.5%), buy
Tensor swing signals with confidence >= 7 whose own symbol is also
red on the day. Exits: +3% sell-into-strength, -8% stop, or the 3rd
trading day after entry (trading days = weekdays minus NYSE holidays,
the 2026-10-11 fix — the holiday set arrives via context.extra from
core Data's calendar). Risk 0.25%/trade on the 8% stop; max 5
positions.

Inputs via context.extra:
  "tensor_signals": [{"symbol","decision","confidence","phenotype"}]
                    (already conf-filtered shape of read_fresh_signals)
  "qqq_day_return": float (fraction) | None — None = fail closed
  "day_returns": {SYM: float} — symbol day-so-far returns
  "nyse_holidays": ["YYYY-MM-DD", ...] (core Data calendar product)
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
"""
import math
from datetime import date, timedelta

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

FEAR_QQQ_PCT = -1.5
MIN_CONF = 7
RISK_FRACTION = 0.0025
STOP_LOSS_PCT = 0.08
STRENGTH_TARGET_PCT = 0.03
HOLD_DAYS = 3
MAX_POSITIONS = 5

CONFIG = SleeveConfig(
    sleeve_id="tensor_red_dip", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def filter_signals(signals):
    """read_fresh_signals' filter+dedupe, verbatim in behavior:
    confidence >= MIN_CONF only; de-dupe by symbol, first wins."""
    seen, out = set(), []
    for s in signals or []:
        if not isinstance(s, dict):
            continue
        sym = str(s.get("symbol") or "").upper()
        if not sym:
            continue
        try:
            conf = int(s.get("confidence"))
        except (TypeError, ValueError):
            continue
        if conf < MIN_CONF:
            continue
        if sym in seen:
            continue
        seen.add(sym)
        out.append({"symbol": sym, "decision": s.get("decision"),
                    "confidence": conf,
                    "phenotype": (str(s.get("phenotype") or "").upper() or None)})
    return out


def improve_enabled(extra):
    """ENH (IMPROVE-tensor_red_dip): the fear-magnitude gate switch —
    context.extra["tensor_red_dip_improve"]["fear_magnitude_gate"],
    default ON; OFF restores the pre-change rule exactly (any red
    print admitted)."""
    ov = (extra or {}).get("tensor_red_dip_improve")
    if isinstance(ov, dict) and "fear_magnitude_gate" in ov:
        return bool(ov["fear_magnitude_gate"])
    return True


def size_qty(equity, price):
    """Verbatim old size_qty: floor(risk$ / (price x 8%)); 0 when the
    inputs are unusable (caller skips), else at least 1."""
    if not equity or not price or price <= 0:
        return 0
    qty = math.floor((equity * RISK_FRACTION) / (price * STOP_LOSS_PCT))
    return max(1, qty) if qty >= 1 else 0


def trading_days_held(entry_date_iso, today_iso, holidays=()):
    """Verbatim old _trading_days_held with the holiday set injected
    (weekdays minus NYSE holidays; entry day = 0)."""
    try:
        d0 = date.fromisoformat(str(entry_date_iso)[:10])
        d1 = date.fromisoformat(str(today_iso)[:10])
    except (ValueError, TypeError):
        return 0
    if d1 <= d0:
        return 0
    hols = set(holidays or ())
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in hols:
            n += 1
    return n


def exit_reason(pos, last_px, today_iso, holidays=()):
    """Verbatim old exit precedence: strength target, then stop, then
    the 3-trading-day time stop. None = hold."""
    entry_px = float(pos.get("entry_px") or 0)
    if not entry_px or not last_px:
        return None
    if last_px >= entry_px * (1.0 + STRENGTH_TARGET_PCT):
        return "strength_target"
    if last_px <= entry_px * (1.0 - STOP_LOSS_PCT):
        return "stop_loss"
    if trading_days_held(pos.get("entry_date"), today_iso, holidays) >= HOLD_DAYS:
        return "time_stop"
    return None


class TensorRedDip(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        holidays = extra.get("nyse_holidays") or ()
        today = context.session
        equity = float(context.equity or 0.0)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            bl = bars.get(sym) or []
            if not bl:
                continue
            last_px = float(bl[-1]["c"])
            why = exit_reason(p, last_px, today, holidays)
            qty = int(float(p.get("qty") or 0))
            if why and qty > 0:
                intents.append(Intent(
                    "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                    reason="tensor_red_dip exit: %s" % why))
        # Telemetry stamp (2026-10-19 cure): every evaluation records
        # the inputs its silence turns on — QQQ return vs the fear
        # gate, Tensor signals seen/qualified, and the reason no
        # entry was emitted — so a silent session is provable DESIGN
        # vs defect from the tick record (dispatch merges
        # last_evaluation into the evaluation row). Telemetry only:
        # no decision below reads the stamp.
        raw_signals = extra.get("tensor_signals") or []
        qualified = filter_signals(raw_signals)
        qret = extra.get("qqq_day_return")
        stamp = {
            "session": today,
            "qqq_day_return": (None if qret is None else float(qret)),
            "qqq_day_pct": (None if qret is None
                            else round(float(qret) * 100.0, 4)),
            "fear_threshold_pct": FEAR_QQQ_PCT,
            "fear_day": bool(qret is not None
                             and float(qret) * 100.0 <= FEAR_QQQ_PCT),
            "tensor_signals_seen": len(raw_signals),
            "tensor_signals_qualified": len(qualified),
            "positions_held": len(book),
            "entries": 0,
            "exits": sum(1 for i in intents if i.kind == "exit"),
            "reason_for_no_intent": None,
            "skip_counts": {},
        }
        self.last_evaluation = stamp
        # entries: fear day required (fail closed on unknown QQQ return)
        if qret is None:
            stamp["reason_for_no_intent"] = "qqq_return_unknown"
            return intents
        if float(qret) * 100.0 > FEAR_QQQ_PCT:
            stamp["reason_for_no_intent"] = "not_fear_day"
            return intents
        if equity <= 0:
            stamp["reason_for_no_intent"] = "no_equity"
            return intents
        if not raw_signals:
            stamp["reason_for_no_intent"] = "no_tensor_signals"
            return intents
        if not qualified:
            stamp["reason_for_no_intent"] = "no_qualified_signals"
            return intents
        gate_on = improve_enabled(extra)
        stamp["improve_switch"] = gate_on
        stamp["paired_records"] = []
        day_rets = extra.get("day_returns") or {}
        room = MAX_POSITIONS - len(book)
        if room <= 0:
            stamp["reason_for_no_intent"] = "book_full"
            return intents
        skips = stamp["skip_counts"]
        for s in qualified:
            if room <= 0:
                break
            sym = s["symbol"]
            if sym in book:
                skips["in_book"] = skips.get("in_book", 0) + 1
                continue
            r = day_rets.get(sym)
            if r is None or float(r) >= 0:
                skips["not_red"] = skips.get("not_red", 0) + 1
                continue  # the symbol itself must be red on the day
            # ENH: control (pre-change) admits any red print; treatment
            # requires the sleeve's own fear magnitude (FEAR_QQQ_PCT)
            # on the symbol itself. Paired record per candidate.
            shallow = float(r) * 100.0 > FEAR_QQQ_PCT
            stamp["paired_records"].append({
                "symbol": sym, "day_return_pct": round(float(r) * 100.0, 4),
                "control": "admit", "treatment": (
                    "refuse_shallow_dip" if (gate_on and shallow) else "admit")})
            if gate_on and shallow:
                skips["dip_too_shallow"] = skips.get("dip_too_shallow", 0) + 1
                continue
            bl = bars.get(sym) or []
            if not bl:
                skips["no_bars"] = skips.get("no_bars", 0) + 1
                continue
            px = float(bl[-1]["c"])
            qty = size_qty(equity, px)
            if qty < 1:
                skips["sized_zero"] = skips.get("sized_zero", 0) + 1
                continue
            stop_px = round(px * (1 - STOP_LOSS_PCT), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("target", round(px * (1 + STRENGTH_TARGET_PCT), 2)),
                            ExitRule("time_bars", float(HOLD_DAYS))),
                reason="tensor_red_dip: fear day QQQ %.2f%%, conf=%d pheno=%s, sym red %.2f%%"
                       % (float(qret) * 100.0, s["confidence"], s["phenotype"],
                          float(r) * 100.0)))
            room -= 1
        stamp["entries"] = sum(1 for i in intents if i.kind == "enter")
        if not stamp["entries"]:
            if len(skips) == 1:
                stamp["reason_for_no_intent"] = (
                    "candidate_dip_too_shallow" if "dip_too_shallow" in skips else
                    "candidate_not_red" if "not_red" in skips else
                    "candidate_in_book" if "in_book" in skips else
                    "candidate_no_bars" if "no_bars" in skips else
                    "candidate_sized_zero")
            elif skips:
                stamp["reason_for_no_intent"] = "candidates_skipped_mixed"
            else:
                stamp["reason_for_no_intent"] = "book_full"
        return intents


def signal(bars, slice_state, context):
    return TensorRedDip().signal(bars, slice_state, context)
