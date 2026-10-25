"""Tensor Swing (flagship) — lean-desk port.

The Tensor engine (v698 pin, Decision #108) runs ONLY inside core
Data's vendored canonical door. This sleeve NEVER imports the engine:
it receives engine output as data via context.extra and performs the
desk's candidate staging/selection on it. See ports/tensor_swing.md.

Selection law carried from the old desk (owner ruling, 2026-10-08, Decisions
#74/#75 + selection doctrine):
  * The engine's swing signals arrive ranked by the desk runner
    (phenotype, confidence, votes); the sleeve stages candidates in
    that order — it does not re-rank by confidence alone.
  * A signal is valid only in its measured context: the two valid jobs
    are (1) buy-the-dip/pullback in an uptrend on broadly red fear
    days, (2) reversal after a major downtrend / deep reset. Bearish
    stock regime is the FAVORABLE habitat (owner ruling, 2026-10-13 correction)
    — never a veto.
  * Extension/euphoria invalidates: candidates flagged extended by the
    engine/extension data are not staged.
  * Gold Diamond is ANNOTATION ONLY (Decision #109): when the core
    supplies a stamp per symbol it is copied onto the intent reason;
    it never blocks, vetoes, delays, or re-ranks.
  * The chart gate (Decision #75) and the red-day rule are core Gate's;
    risk/sizing are core Risk's. This sleeve only stages.

Inputs via context.extra:
  "tensor_signals": [{"symbol","decision","confidence","phenotype",
                      "regime","extended": bool, "bar_date",
                      "entry","stop","target"}]
                    — engine output via core Data ONLY; entry/stop/
                    target are the staged decision's own prices (the
                    producer's detect_signals-mirror mapping: entry =
                    the canonical bar close at the swing's timestamp,
                    stop = the swing's invalidation, target = the
                    swing's target)
  "gold_diamond": {SYM: {"stamp": "qualified|rejected|warming", ...}}
  "sleeve_state": {SYM: {"position": {...} | None}}
  "max_new": optional cap on staged candidates this pass
  "tensor_exit": {SYM: {"bearish_exit": bool, "bearish_reason": str|None,
                        "last_close": float, "bar_ts": [epoch, ...]}}
                    — the producer's exit view (core/tensor_feeds):
                    the old runner's manage_positions inputs over the
                    same canonical series

Exits (M-TS1 cure, 2026-10-15 — ports/tensor_swing.md): the old
runner exited held Tensor positions three ways, all restored here:
the bearish engine trigger and the 20-closed-bar time stop
(manage_positions, evaluated in that order) become exit intents
over the core's position records, and the bracket's take-profit
level — persisted on the record as target_px at the fill — is
evaluated close-based (the lean idiom for sleeve rules). The
bracket's stop leg was never an evaluated rule: it is the resting
GTC broker stop core places from the intent's stop at the fill.
A held symbol with no tensor_exit row is not evaluated this pass
(fail closed, as the old runner skipped bar-less symbols).
Bars: canonical 1H-derived context is the engine's; the bars arg is
accepted for contract shape. Pricing comes from the staged decision,
never from the bars arg (the old desk priced off the decision too).
"""
import math

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

MIN_CONF = 7  # desk swing-watch floor used across Tensor consumers
EXIT_TIME_STOP_BARS = 20  # old desk EXIT_TIME_STOP_BARS: the study's
                          # edge horizon — exit longs held past 20
                          # closed bars since the entry bar

CONFIG = SleeveConfig(
    sleeve_id="tensor_swing", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def stage_candidates(signals, held, gold_diamond=None, max_new=None):
    """Pure staging: preserve engine order; drop held symbols,
    sub-floor confidence, and extended candidates; annotate (never
    gate on) Gold Diamond. Returns intent-ready dicts."""
    out = []
    gd = gold_diamond or {}
    seen = set()
    for s in signals or []:
        if not isinstance(s, dict):
            continue
        sym = s.get("symbol")
        if not sym or sym in held or sym in seen:
            continue  # one candidate per symbol per pass (repair
            # 2026-10-15: duplicates staged twice -> double entry,
            # since dispatch does not dedupe same-tick intents)
        seen.add(sym)
        try:
            conf = int(s.get("confidence"))
        except (TypeError, ValueError):
            continue
        if conf < MIN_CONF:
            continue
        if s.get("extended"):
            continue  # extension/euphoria invalidates (selection doctrine)
        row = dict(s)
        stamp = (gd.get(sym) or {}).get("stamp")
        row["gold_diamond"] = stamp  # annotation only, Decision #109
        out.append(row)
        if max_new is not None and len(out) >= max_new:
            break
    return out


def improve_enabled(extra):
    """ENH (IMPROVE-tensor_swing): the reward>=risk staging floor
    switch — context.extra["tensor_swing_improve"]["reward_risk_floor"],
    default ON; OFF restores the pre-change staging exactly. Sleeve
    layer only; the Tensor engine is untouched."""
    ov = (extra or {}).get("tensor_swing_improve")
    if isinstance(ov, dict) and "reward_risk_floor" in ov:
        return bool(ov["reward_risk_floor"])
    return True


def _fmt_stamp(t):
    """Entry-bar stamp for reason strings: whole epochs print as ints."""
    f = float(t)
    return str(int(f)) if f.is_integer() else str(f)


def time_stop_due(entry_bar_t, bar_ts):
    """The old runner's _time_stop_due (scan_and_trade.py), ported to
    epoch stamps. Returns (due, bars_held_or_None, note).

    Count semantics are the old arithmetic ones (bars_since_entry,
    MF-003): closed bars elapsed since the entry bar = bar stamps
    strictly after the entry stamp. The count is grid-agnostic, so
    the lean position record's fill-tick entry_bar_t counts the
    same bars the old record's swing-event stamp did at hourly
    granularity. An entry stamp older than the whole supplied
    window is necessarily past the horizon -> due, bars_held None,
    note says so (the old window-age fallback). A missing entry
    stamp, an empty window, or a stamp after the newest bar proves
    nothing -> not due. Never raises.
    """
    try:
        if entry_bar_t is None or not bar_ts:
            return False, None, None
        entry = float(entry_bar_t)
        stamps = [float(t) for t in bar_ts]
        if entry < stamps[0]:
            return (True, None,
                    "entry bar %s older than %d-bar window"
                    % (_fmt_stamp(entry), len(stamps)))
        if entry > stamps[-1]:
            return False, None, None
        n = sum(1 for t in stamps if t > entry)
        return n > EXIT_TIME_STOP_BARS, n, None
    except (TypeError, ValueError):
        return False, None, None


def evaluate_exit(pos, view):
    """One held position against the old runner's exit rules, in
    the old evaluation order (manage_positions: bearish trigger,
    then time stop). The bracket's take-profit leg — a resting
    limit on the old desk — is evaluated last, close-based: on a
    tick where several rules are true the exit is identical and
    only the recorded reason differs. Returns the rule's reason
    string (old formats), or None. Pure; never raises."""
    if not isinstance(view, dict):
        return None  # no exit product for this symbol: fail closed
    if view.get("bearish_exit"):
        return view.get("bearish_reason") or "bearish exit trigger"
    due, n_bars, note = time_stop_due(pos.get("entry_bar_t"),
                                      view.get("bar_ts"))
    if due:
        if n_bars is not None:
            return ("time stop: %d closed bars since entry "
                    "(edge horizon %d)" % (n_bars, EXIT_TIME_STOP_BARS))
        return ("time stop: %s (edge horizon %d bars)"
                % (note, EXIT_TIME_STOP_BARS))
    target = pos.get("target_px")
    last = view.get("last_close")
    if target is not None and last is not None:
        try:
            if float(last) >= float(target):
                return ("target reached: close %.2f >= target %.2f"
                        % (float(last), float(target)))
        except (TypeError, ValueError):
            pass
    return None


class TensorSwing(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        held = {s for s, st in state.items() if (st or {}).get("position")}
        gate_on = improve_enabled(extra)
        paired = []
        self.last_evaluation = {"improve_switch": gate_on, "paired_records": paired}
        staged = stage_candidates(extra.get("tensor_signals"), held,
                                  extra.get("gold_diamond"),
                                  extra.get("max_new"))
        intents = []
        for row in staged:
            sym = row["symbol"]
            # The intent carries the staged decision's own entry /
            # stop / target, exactly as the old desk's decide()
            # consumed detect_signals' output. A decision the engine
            # left unpriced (any of the three missing) or whose
            # per-share risk is not positive was SKIPPED by the old
            # desk ("engine omitted entry/stop/target" /
            # SKIP_INVALID_RISK) — never traded. Mirror that here:
            # an unpriceable staged row emits NO intent. (Defect
            # 2026-10-15: this loop emitted bare intents — price
            # derived from an unrelated bars arg or None, stop never
            # set — and dispatch rejected 168 of them with
            # price=0.0/stop=0.0; the flagship could not enter.)
            entry, stop, target = (row.get("entry"), row.get("stop"),
                                   row.get("target"))
            if entry is None or stop is None or target is None:
                continue
            try:
                entry, stop, target = (float(entry), float(stop),
                                       float(target))
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(entry) and math.isfinite(stop)
                    and math.isfinite(target)):
                continue
            if entry <= 0 or stop <= 0 or stop >= entry:
                continue  # per-share risk must be positive (old decide())
            # ENH: refuse a row whose own target-entry < entry-stop.
            paired.append({"symbol": sym, "entry": entry, "stop": stop,
                           "target": target,
                           "reward_risk": round((target - entry) / (entry - stop), 4),
                           "control": "stage", "treatment": (
                               "refuse_lopsided" if (gate_on and (target - entry) < (entry - stop))
                               else "stage")})
            if gate_on and (target - entry) < (entry - stop):
                continue
            reason = ("tensor_swing staged: phenotype=%s conf=%s regime=%s"
                      " entry=%.2f stop=%.2f target=%.2f"
                      % (row.get("phenotype"), row.get("confidence"),
                         row.get("regime"), entry, stop, target))
            if row.get("bar_date"):
                # SA-17 (2026-10-16): the swing's confirmation date is
                # the staged decision's own bar date — carried on the
                # intent so the ledger record can date the evidence.
                reason += " swing_bar_date=%s" % row["bar_date"]
            if row.get("gold_diamond"):
                reason += " gold_diamond=%s (annotation only)" % row["gold_diamond"]
            intents.append(Intent(
                "enter", sym, price_hint=entry, stop=stop, target=target,
                signal_date=row.get("bar_date"),
                # The position's exit rules as data (ports/tensor_
                # swing.md M-TS1: "exit rules must be expressed as
                # ExitRule data"): the stop core places as the GTC
                # broker stop at the fill, the staged target, and
                # the 20-bar time stop. Evaluated exits live below.
                exit_rules=(ExitRule("stop", stop),
                            ExitRule("target", target),
                            ExitRule("time_bars",
                                       float(EXIT_TIME_STOP_BARS))),
                reason=reason))
        # -- Exits (M-TS1 cure): the old runner's manage_positions
        # over the core's position records, fed by the producer's
        # tensor_exit view. Dispatch clamps the quantity to this
        # sleeve's own slice, exactly as the old desk clamped its
        # exits to the Tensor book (co-holders are never sold).
        view_all = extra.get("tensor_exit") or {}
        for sym, st in state.items():
            pos = (st or {}).get("position")
            if not pos:
                continue
            try:
                qty = int(float(pos.get("qty") or 0))
            except (TypeError, ValueError):
                continue
            if qty <= 0:
                continue  # Tensor stages longs only; a non-long
                # record is not this sleeve's position to close
            view = view_all.get(sym)
            why = evaluate_exit(pos, view)
            if why is None:
                continue
            last = view.get("last_close")
            intents.append(Intent(
                "exit", sym, qty_hint=qty,
                price_hint=(round(float(last), 2)
                            if last is not None else None),
                reason="tensor_swing exit: %s" % why))
        return intents


def signal(bars, slice_state, context):
    return TensorSwing().signal(bars, slice_state, context)
