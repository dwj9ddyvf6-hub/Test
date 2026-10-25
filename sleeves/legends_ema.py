"""Legend's EMA — lean-desk port.

EXTRACTED from the old desk's legends_ema.py (QQQ-only). The setup
evaluation (evaluate_setup) and exit_geometry are ported verbatim in
behavior — 15-minute RTH bars arrive via context.extra from core Data
(the old file fetched 1-min bars and built 15m bars itself; the
aggregation is a Data duty now). The geometry is emitted as Intent
stop/target data and recorded on the position. See
ports/legends_ema.md.

M-LE1 SUBSTITUTION (ruled 2026-10-18, AUDIT-20261018-CURE10): the
port assigned the OCO lifecycle (place/refresh with a $0.20
deadband, 600s unprotected-timeout flatten, 1800s stale-refresh
escalation) to core Broker — it was never built there, and
core/protection.py deliberately skips this sleeve. The ruled
protection is the in-signal one landed by AUDIT3-A1-04
(2026-10-16): the recorded stop/target are evaluated against the
last CLOSE on every tick, and any open position flattens at
15:59 ET. A wick through the stop that recovers before the tick
produces no exit — the deliberate difference from the old resting
OCO, and the desk-wide close-based exit idiom. No broker OCO is
placed for this sleeve.

Strategy (old module): from the prior RTH session's 15m bars with the
EMA(20) warmed over the prior 5 sessions: trend = |close-open| / range
of the session; trend_day when trend >= TREND_Q80 (0.7686); no_touch
when NO 15m bar of the session touches its EMA value. Armed = trend_day
AND no_touch. Entry side is REVERSION toward the EMA (old rule
verbatim: sell when the entry print is above the EMA, buy when below).
Entry at the next session's open window (09:30-09:45 ET
cutoff in the old runner — a core execution detail). Exit geometry:
TP at the EMA target, stop = 0.5 x ATR14 (mean RTH high-low of the
prior 14 sessions) normalized — never a fixed-point stop. Qty =
(equity x 0.25%) // (0.5 x ATR14). Flat by 15:59 ET.

ENTRY GEOMETRY GATE (the owner's ruling 2026-10-23, IMPROVE-legends_ema):
entries are refused when the remaining distance to the EMA target
cannot pay for the coded stop — the predicate is
forecast_payoff_gate(ref, ema_last, atr14) =
abs(ref - ema_last) >= STOP_ATR_MULT * atr14 (0.5 x ATR14, unrounded;
equality is TAKEN). The gate sits in the entry branch after the
tp/sl geometry and before sizing, and is switched by
context.extra["legends_ema_improve"]["entry_geometry_gate"]
(default ON; switch OFF restores the pre-change rule exactly).
Every armed setup that reaches the gate point is recorded in the
legends_ema_exp/1 experiment journal (served back via
context.extra["legends_ema_exp_journal"], filed on
self.last_evaluation): the pre-change rule runs as the shadow
control on the same closes, opening a virtual position that the
in-signal shadow update evaluates with the sleeve's own close-based
stop/target/flat logic, so refused setups still produce a paired
outcome record. TREND_Q80, M-LE1 exits, sizing unchanged.

Inputs via context.extra:
  "bars_15m_by_session": [[bar,...], ...] — 15m RTH bars grouped by
      session, oldest first; the LAST group is the setup session,
      earlier groups warm the EMA (old: 5 warmup sessions + setup day)
  "daily_ranges": [h-l, ...] prior sessions for ATR14 (needs exactly
      the last 14; fewer => setup fails closed, as the old code did)
  "sleeve_state": {"QQQ": {"position": {...} | None}}
Bars (arg): daily QQQ bars, price hints only.
"""
import hashlib
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYMBOL = "QQQ"
RISK_FRACTION = 0.0025
EMA_SPAN = 20
WARMUP_SESSIONS = 5
ATR_SESSIONS = 14
STOP_ATR_MULT = 0.5
TREND_Q80 = 0.7686
FLAT_HM = (15, 59)
ENTRY_OPEN_HM = (9, 30)
ENTRY_CUTOFF_HM = (9, 45)

CONFIG = SleeveConfig(
    sleeve_id="legends_ema", cadence_s=300, universe=(SYMBOL,),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)

# ------------------------------------------------------------ experiment
# IMPROVE-legends_ema entry geometry gate + shadow harness (§2/§3 of
# the improve-three spec). The journal rides the desk's existing
# stamp round-trip: adopted from context.extra, mutated in place
# during signal(), filed on self.last_evaluation.
EXP_ID = "IMP3-LEGENDS-20261023"
EXP_JOURNAL_VERSION = "legends_ema_exp/1"
EXP_FINGERPRINT = hashlib.sha256(
    f"{EXP_ID}|{EXP_JOURNAL_VERSION}|entry_geometry_gate|"
    f"STOP_ATR_MULT=0.5".encode()).hexdigest()[:28]
_EXP_COUNTS = ("armed", "gate_refused", "gate_passed", "control_trades",
               "treatment_trades", "closed")


def forecast_payoff_gate(ref, ema_last, atr14):
    """True when the remaining distance to the EMA target can pay for
    the coded stop: abs(ref - ema_last) >= STOP_ATR_MULT * atr14."""
    return abs(ref - ema_last) >= STOP_ATR_MULT * atr14


def entry_geometry_gate_enabled(extra):
    """ctx.extra['legends_ema_improve']['entry_geometry_gate'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("legends_ema_improve")
    if isinstance(ov, dict) and "entry_geometry_gate" in ov:
        return bool(ov["entry_geometry_gate"])
    return True


def _fresh_exp_open():
    return {"record": None, "position": None,
            "live_position_seen": False}


def _fresh_exp_journal():
    return {"exp_id": EXP_ID, "version": EXP_JOURNAL_VERSION,
            "fingerprint": EXP_FINGERPRINT, "records_tail": [],
            "counts": {k: 0 for k in _EXP_COUNTS},
            "open": _fresh_exp_open(), "last_session": None}


def _exp_journal(extra):
    """Adopt extra['legends_ema_exp_journal'] ONLY when exp_id,
    version and fingerprint all match (known keys merged onto a
    fresh journal); any mismatch returns a fresh journal and the
    caller stamps the rejection. A mismatched journal is never
    migrated and never affects live decisions."""
    raw = (extra or {}).get("legends_ema_exp_journal")
    if isinstance(raw, dict) \
            and raw.get("exp_id") == EXP_ID \
            and raw.get("version") == EXP_JOURNAL_VERSION \
            and raw.get("fingerprint") == EXP_FINGERPRINT:
        j = _fresh_exp_journal()
        j.update({k: raw[k] for k in j if k in raw})
        if isinstance(raw.get("counts"), dict):
            counts = {k: 0 for k in _EXP_COUNTS}
            counts.update({k: raw["counts"][k]
                           for k in counts if k in raw["counts"]})
            j["counts"] = counts
        if isinstance(raw.get("open"), dict):
            open_state = _fresh_exp_open()
            open_state.update({k: raw["open"][k]
                               for k in open_state if k in raw["open"]})
            j["open"] = open_state
        if not isinstance(j.get("records_tail"), list):
            j["records_tail"] = []
        return j
    return _fresh_exp_journal()


def ema(values, span):
    """Verbatim old ema: seeded at the first value."""
    k = 2.0 / (span + 1.0)
    out = []
    v = values[0]
    for x in values:
        v = x * k + v * (1 - k) if out else x
        out.append(v)
    return out


def evaluate_setup(sessions_bars, daily_ranges):
    """Verbatim port of _evaluate_setup_inner's math on pre-aggregated
    15m sessions. Returns the setup dict or None (fail closed)."""
    if not sessions_bars:
        return None
    setup_bars = sessions_bars[-1]
    all_bars = [b for sess in sessions_bars for b in sess]
    if len(setup_bars) < 10 or len(all_bars) < EMA_SPAN + 2:
        return None
    emas = ema([float(b["c"]) for b in all_bars], EMA_SPAN)
    setup_emas = emas[len(all_bars) - len(setup_bars):]
    sess_o = float(setup_bars[0]["o"])
    sess_c = float(setup_bars[-1]["c"])
    sess_h = max(float(b["h"]) for b in setup_bars)
    sess_l = min(float(b["l"]) for b in setup_bars)
    rng = sess_h - sess_l
    trend = (abs(sess_c - sess_o) / rng) if rng > 0 else 0.0
    no_touch = not any(float(b["l"]) <= e <= float(b["h"])
                       for b, e in zip(setup_bars, setup_emas))
    # Fail closed on unreadable ranges, exactly as the old
    # evaluate_setup's try/except -> None did: a non-numeric or
    # non-finite range must not reach the qty math (int(NaN) raised).
    try:
        ranges = [float(r) for r in (daily_ranges or [])][-ATR_SESSIONS:]
    except (TypeError, ValueError):
        return None
    atr14 = sum(ranges) / len(ranges) \
        if len(ranges) == ATR_SESSIONS \
        and all(math.isfinite(r) for r in ranges) else None
    if atr14 is None:
        return None
    return {"trend": trend, "trend_day": trend >= TREND_Q80,
            "no_touch": no_touch, "ema_last": setup_emas[-1],
            "atr14": atr14, "n_bars": len(setup_bars),
            "warmup_bars": len(all_bars),
            # Side is REVERSION, toward the EMA — the old entry rule
            # verbatim: side = "sell" if ref_px > ema_ref else "buy",
            # with ref_px the entry print vs the setup EMA. Under
            # no_touch the setup close sits strictly on one side of
            # its EMA, so close-vs-EMA here is that same side. (The
            # pre-assessment port used close-vs-open — trend
            # CONTINUATION — which inverts the strategy: a no-touch
            # up day leaves price ABOVE the EMA, and the old sleeve
            # shorts it; a no-touch down day is bought.)
            "direction": "sell" if sess_c > setup_emas[-1] else "buy"}


def exit_geometry(side, ref, ema_ref, atr14):
    """Verbatim: TP at the EMA target; stop normalized 0.5 x ATR14."""
    stop_dist = STOP_ATR_MULT * atr14
    tp = round(ema_ref, 2)
    sl = round(ref - stop_dist if side == "buy" else ref + stop_dist, 2)
    return tp, sl


class LegendsEma(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------ shadow harness
    def _close_shadow(self, journal, record, position, reason, px,
                      session):
        """Complete the paired record from the shadow position's own
        exit evaluation and move it to records_tail (capped at the
        last 64 completed records; counts are never trimmed)."""
        record["exit"] = {"reason": reason, "px": px,
                          "session": session}
        entry_ref = float(position["entry_ref"])
        per_share = (px - entry_ref) if position["side"] == "buy" \
            else (entry_ref - px)
        record["pnl_gross_per_share"] = per_share
        record["pnl_gross"] = per_share * position["qty"]
        journal["counts"]["closed"] = \
            int(journal["counts"].get("closed") or 0) + 1
        tail = journal.setdefault("records_tail", [])
        tail.append(record)
        del tail[:-64]
        journal["open"] = _fresh_exp_open()

    def _update_shadow(self, journal, bars, context, now_et, pos):
        """Shadow update — runs FIRST in signal(), before the
        position branch and all entry guards, and never emits
        intents. Evaluates an open shadow position against the last
        QQQ close with the live exit branch's own side-aware close
        logic (stop, then target), then the 15:59 flatten — the
        same precedence as the live branch. A position still open
        at the first pass of a later session force-closes at that
        pass's first QQQ close as 'unclosed_at_session_end'."""
        open_state = journal.get("open")
        if not isinstance(open_state, dict):
            return
        position = open_state.get("position")
        record = open_state.get("record")
        if not position or not record:
            return
        # External-close detection, pinned to the sleeve_state
        # position transition: a live position seen on an earlier
        # pass that is now absent marks the treatment leg; nothing
        # more is inferred.
        if open_state.get("live_position_seen") and pos is None:
            treatment = record.get("treatment")
            if isinstance(treatment, dict):
                treatment["live_position_closed_externally"] = True
        if pos is not None:
            open_state["live_position_seen"] = True
        bl = bars.get(SYMBOL) or []
        if not bl:
            return
        last = float(bl[-1]["c"])
        if record.get("session") != context.session:
            self._close_shadow(journal, record, position,
                                "unclosed_at_session_end", last,
                                context.session)
            return
        stop = float(position["stop"])
        target = float(position["target"])
        reason = None
        if position["side"] == "buy":
            if last <= stop:
                reason = "stop"
            elif last >= target:
                reason = "target"
        else:
            if last >= stop:
                reason = "stop"
            elif last <= target:
                reason = "target"
        if reason is None \
                and (now_et.hour, now_et.minute) >= FLAT_HM:
            reason = "flat_1559"
        if reason is not None:
            self._close_shadow(journal, record, position, reason,
                               last, context.session)

    def _record_opportunity(self, journal, context, setup, ref,
                            ref_source, side, tp, sl, qty_model,
                            gate_on, gate_ok):
        """Create this session's paired record at the gate point
        and open the shadow position when the control (pre-change)
        rule enters. Returns the new record, or None when this
        session's opportunity is already recorded or open (dedupe:
        the first gate-point evaluation of the session IS the
        opportunity)."""
        opp_id = "legends_ema:%s" % context.session
        open_state = journal.get("open")
        if isinstance(open_state, dict):
            open_rec = open_state.get("record")
            if open_rec and open_rec.get("opp_id") == opp_id:
                return None
        for rec in journal.get("records_tail") or []:
            if rec.get("opp_id") == opp_id:
                return None
        dist = abs(ref - setup["ema_last"])
        stop_dist = STOP_ATR_MULT * setup["atr14"]
        control_decision = "enter" if qty_model >= 1 \
            else "qty_below_1"
        if gate_on and not gate_ok:
            gate_decision = "refused"
            treatment_decision = "gate_refused"
        elif qty_model >= 1:
            gate_decision = "passed" if gate_on else "off"
            treatment_decision = "enter"
        else:
            gate_decision = "passed" if gate_on else "off"
            treatment_decision = "qty_below_1"
        record = {
            "opp_id": opp_id, "session": context.session,
            "side": side, "ref": ref, "ref_source": ref_source,
            "ema_last": setup["ema_last"], "atr14": setup["atr14"],
            "dist_to_ema": dist, "stop_dist": stop_dist,
            "rr": (dist / stop_dist) if stop_dist else None,
            "gate_enabled": gate_on, "gate_decision": gate_decision,
            "control": {"decision": control_decision,
                        "qty": qty_model},
            "treatment": {"decision": treatment_decision,
                          "qty": qty_model
                          if treatment_decision == "enter" else 0,
                          "live_intent_emitted": False},
            "exit": None, "pnl_gross_per_share": None,
            "pnl_gross": None, "improve_switch": gate_on}
        if treatment_decision == "gate_refused":
            record["treatment"]["pnl_gross"] = 0.0
            record["treatment"]["note"] = "refused_no_position"
        counts = journal["counts"]
        counts["armed"] = int(counts.get("armed") or 0) + 1
        if gate_decision == "refused":
            counts["gate_refused"] = \
                int(counts.get("gate_refused") or 0) + 1
        elif gate_decision == "passed":
            counts["gate_passed"] = \
                int(counts.get("gate_passed") or 0) + 1
        if control_decision == "enter":
            counts["control_trades"] = \
                int(counts.get("control_trades") or 0) + 1
        if treatment_decision == "enter":
            counts["treatment_trades"] = \
                int(counts.get("treatment_trades") or 0) + 1
        if control_decision == "enter":
            arms = ["control"]
            if treatment_decision == "enter":
                arms.append("treatment")
            journal["open"] = {
                "record": record,
                "position": {"side": side, "entry_ref": ref,
                             "stop": sl, "target": tp,
                             "qty": qty_model, "arms": arms,
                             "session": context.session,
                             "opp_id": opp_id},
                "live_position_seen": False}
        else:
            tail = journal.setdefault("records_tail", [])
            tail.append(record)
            del tail[:-64]
        return record

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYMBOL) or {}).get("position")
        now_et = datetime.fromtimestamp(float(context.now), tz=ET)
        intents = []
        # Experiment journal (§2): adopted at signal() entry, filed
        # on the stamp, and mutated through the pass so the filed
        # stamp always carries the post-pass state.
        journal = _exp_journal(extra)
        served_raw = extra.get("legends_ema_exp_journal")
        stamp = {"sleeve": "legends_ema", "session": context.session,
                 "legends_ema_exp_journal": journal,
                 "exp_journal_served": isinstance(served_raw, dict)}
        if isinstance(served_raw, dict) and not (
                served_raw.get("exp_id") == EXP_ID
                and served_raw.get("version") == EXP_JOURNAL_VERSION
                and served_raw.get("fingerprint") == EXP_FINGERPRINT):
            stamp["exp_journal_rejected"] = "fingerprint_mismatch"
        self.last_evaluation = stamp
        journal["last_session"] = context.session
        # Shadow update runs FIRST, before the position branch and
        # before all entry guards; it never emits intents.
        self._update_shadow(journal, bars, context, now_et, pos)
        if pos:
            qty = int(float(pos.get("qty") or 0))
            # AUDIT3-A1-04 (2026-10-16): the entry's stop/target
            # were emitted as ExitRule data nobody executed — the
            # sleeve never evaluated them in-signal, and protection
            # skips this sleeve precisely because its stop is "an
            # in-signal ATR construct, evaluated by the sleeve".
            # The only exit that existed was the 15:59 flatten.
            # Evaluate the record's own stop/target against the
            # last close, side-aware, before the flatten rule.
            if qty != 0:
                bl = bars.get(SYMBOL) or []
                last = float(bl[-1]["c"]) if bl else None
                stop = target = None
                for r in pos.get("exit_rules") or ():
                    if isinstance(r, dict):
                        if r.get("kind") == "stop":
                            stop = float(r["value"])
                        elif r.get("kind") == "target":
                            target = float(r["value"])
                if stop is None and pos.get("stop_px") is not None:
                    stop = float(pos["stop_px"])
                if last is not None:
                    hit = None
                    if qty > 0:
                        if stop is not None and last <= stop:
                            hit = "stop"
                        elif target is not None and last >= target:
                            hit = "target"
                    else:
                        if stop is not None and last >= stop:
                            hit = "stop"
                        elif target is not None and last <= target:
                            hit = "target"
                    if hit:
                        intents.append(Intent(
                            "exit", SYMBOL, qty_hint=abs(qty),
                            price_hint=round(last, 2),
                            reason="legends_ema: %s hit (close %.2f, "
                                   "stop %s, target %s)"
                                   % (hit, last, stop, target)))
                        return intents
            # XT-3 (2026-10-16): core's position record carries a
            # SIGNED qty (a short's record is negative); the old
            # sleeve's own bookkeeping stored an unsigned count, so
            # the ported qty > 0 gate made a short position invisible
            # to the flat-by-15:59 rule — the position could never
            # exit in-signal. The rule is side-agnostic: flatten
            # either side, sized by the position's magnitude.
            if qty != 0 and (now_et.hour, now_et.minute) >= FLAT_HM:
                intents.append(Intent(
                    "exit", SYMBOL, qty_hint=abs(qty),
                    reason="legends_ema: flat by 15:59 ET"))
            return intents
        # Weekday guard (CURE2, 2026-10-19): the entry window check
        # below is time-of-day only — a weekend tick at 09:35 ET with
        # an armed setup would enter on a non-trading day. Mirror the
        # siblings (morning_dip.in_window, bilbo time_gate_ok):
        # entries are Mon-Fri only. Entry-only: the exit path above
        # (stop/target + 15:59 flatten) is deliberately unguarded.
        if now_et.weekday() >= 5:
            return intents
        if not (ENTRY_OPEN_HM <= (now_et.hour, now_et.minute) < ENTRY_CUTOFF_HM):
            return intents
        setup = evaluate_setup(extra.get("bars_15m_by_session"),
                               extra.get("daily_ranges"))
        if not setup:
            return intents
        if not (setup["trend_day"] and setup["no_touch"]):
            return intents  # armed = trend_day AND no_touch (verbatim)
        equity = float(context.equity or 0.0)
        if equity <= 0 or not setup["atr14"]:
            return intents
        bl = bars.get(SYMBOL) or []
        ref = float(bl[-1]["c"]) if bl else setup["ema_last"]
        ref_source = "bar_close" if bl else "ema_fallback"
        side = setup["direction"]
        tp, sl = exit_geometry(side, ref, setup["ema_last"], setup["atr14"])
        # ENTRY GEOMETRY GATE (IMP3-LEGENDS-20261023): after the
        # tp/sl geometry, before sizing. The coded qty formula is
        # evaluated once here as the shadow model's qty — the live
        # qty below is that same value — so a setup the gate refuses
        # is recorded gate-refused even when it would also fail
        # qty < 1 (population order = code order).
        qty = int((equity * RISK_FRACTION) // (STOP_ATR_MULT * setup["atr14"]))
        gate_on = entry_geometry_gate_enabled(extra)
        gate_ok = forecast_payoff_gate(ref, setup["ema_last"],
                                       setup["atr14"])
        record = self._record_opportunity(
            journal, context, setup, ref, ref_source, side, tp, sl,
            qty, gate_on, gate_ok)
        if gate_on and not gate_ok:
            return intents
        if qty < 1:
            return intents
        if record is not None:
            record["treatment"]["live_intent_emitted"] = True
        intents.append(Intent(
            "enter", SYMBOL, qty_hint=qty, price_hint=round(ref, 2),
            stop=sl, target=tp,
            # The old sleeve TRADES the side (submit_oco took it).
            # Without the structured fields the dispatcher's entry
            # planner defaults an undeclared intent to a LONG buy —
            # a short setup would enter long with its stop above price.
            side=side,
            position_intent="buy_to_open" if side == "buy" else "sell_to_open",
            exit_rules=(ExitRule("stop", sl), ExitRule("target", tp)),
            reason="legends_ema armed: trend=%.4f >= %.4f, no_touch=%s, "
                   "atr14=%.2f, side=%s"
                   % (setup["trend"], TREND_Q80, setup["no_touch"],
                      setup["atr14"], side)))
        return intents


def signal(bars, slice_state, context):
    return LegendsEma().signal(bars, slice_state, context)
