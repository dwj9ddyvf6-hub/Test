"""FREE_KRAKEN_LINK_BREAKDOWN — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_kraken_paper.py breakdown() + aurelia_common's
kraken clock (verbatim semantics): on completed 4h bars, the signal bar
is the latest whose entry is due (entry = signal open + 8h, i.e.
open(i+2)); entry fires when the signal close is below the prior 20
bars' low. The candle open is NOT the fill — entry is a short at a live
quote after open(i+2). Exit: cover 16h after the entry due time.
Quantity 1 contract, budget $100,000, max exposure 10% (the old
executor's caps — Risk budget config for this book).

VIRTUAL BOOK MAPPING: Ledger account "free_kraken" (BUDGET_USD =
100,000 for the whole Kraken test family; per-test max exposure 10%).
The old isolated paper ledger (exp_submit) does not come over; the
core Broker serves fills on the live paper transport (LC-7,
2026-10-18; DRY is a test/shadow stub only). Short state arrives as
context.extra["sleeve_state"]["PF_LINKUSD"] = {"qty": -1,
"entry_due_at": iso} (negative = short). Bars: 4h dicts
{"t","o","h","l","c","v"} (t = bar open, epoch s). Quote via
context.extra["quote"] = {"bid","ask"}.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "free_kraken"
BUDGET_USD = 100_000.0
MAX_EXPOSURE = 0.10
INSTRUMENT = "PF_LINKUSD"
BAR_SECONDS = 4 * 3600
ENTRY_SHIFT = timedelta(hours=8)
HOLD = timedelta(hours=16)

# ENH-20261024 (IMPROVE-free_kraken_link_breakdown): entry-validity gate - when entry_ready,
# refuse the short if the live bid >= decision["prior_20_low"] (breakdown
# already failed by the sleeve's own definition). Switched by
# extra["free_kraken_link_breakdown_improve"]["breakdown_validity_gate"] (default ON; OFF
# restores the pre-change rule exactly). Paired control/treatment record
# appended to extra["enhance_paired"] on every entry_ready decision.

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_link_breakdown", cadence_s=3600,
    universe=(INSTRUMENT,), state_schema={"position": "dict|None"},
    risk_pct=None)


def breakdown_validity_gate_enabled(extra):
    ov = (extra or {}).get("free_kraken_link_breakdown_improve")
    if isinstance(ov, dict) and "breakdown_validity_gate" in ov:
        return bool(ov["breakdown_validity_gate"])
    return True


def _iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize(bars):
    rows = []
    for b in bars or []:
        try:
            t = float(b["t"])
            row = {"open_at": _iso(t), "close_at": _iso(t + BAR_SECONDS),
                   "open": float(b["o"]), "high": float(b["h"]),
                   "low": float(b["l"]), "close": float(b["c"]),
                   "volume": float(b.get("v") or 0)}
        except (KeyError, TypeError, ValueError):
            continue  # malformed bar: fail closed, never raise (P3 2026-10-15)
        rows.append(row)
    return rows


def completed_bars(rows, now):
    return sorted([r for r in rows if _parse(r["close_at"]) <= now],
                  key=lambda r: r["open_at"])


def entry_due_at(signal_open):
    return signal_open.astimezone(timezone.utc) + ENTRY_SHIFT


def exit_due_at(entry_due):
    return entry_due.astimezone(timezone.utc) + HOLD


def select_signal(rows, now):
    chosen = None
    for bar in completed_bars(rows, now):
        if entry_due_at(_parse(bar["open_at"])) <= now:
            chosen = bar
    return chosen


def event_id(instrument, signal):
    payload = json.dumps({"instrument": instrument, "signal_open": signal["open_at"],
                          "signal_close": signal["close_at"], "close": signal["close"]},
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def breakdown_decision(rows, now, *, instrument=""):
    """Verbatim port of kraken_breakdown_decision."""
    done = completed_bars(rows, now)
    if len(done) < 22:
        return {"status": "WARMING_UP",
                "reason": f"{len(done)} completed 4h bars; 22 required.",
                "entry_due_at": None}
    signal_bar = select_signal(done, now)
    if signal_bar is None:
        return {"status": "WARMING_UP", "reason": "No bar has reached open(i+2).",
                "entry_due_at": None}
    prior = [bar for bar in done if bar["open_at"] < signal_bar["open_at"]]
    if len(prior) < 20:
        return {"status": "WARMING_UP", "reason": "Fewer than 20 bars before the signal.",
                "entry_due_at": None}
    window = [bar["low"] for bar in prior[-20:]]
    fired = float(signal_bar["close"]) < min(window)
    due = entry_due_at(_parse(signal_bar["open_at"]))
    base = {"signal_open_at": signal_bar["open_at"],
            "signal_close_at": signal_bar["close_at"],
            "signal_close": signal_bar["close"],
            "known_at": signal_bar["close_at"],
            "entry_due_at": due.isoformat(),
            "signal_event_id": event_id(instrument, signal_bar),
            "prior_20_low": min(window),
            "decision_at": now.isoformat()}
    if not fired:
        return {**base, "status": "QUALIFIED/AWAITING SIGNAL",
                "reason": "Close is not below the prior 20 lows."}
    if now < due:
        return {**base, "status": "QUALIFIED/OUTSIDE WINDOW",
                "reason": "Breakdown is true. open(i+2) has not arrived."}
    return {**base, "status": "entry_ready", "side": "sell",
            "reason": "Short the perpetual at a live quote after open(i+2). "
                      "The candle open is not the fill."}


class FreeKrakenLinkBreakdown(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        now = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        state = extra.get("sleeve_state") or {}
        pos = state.get(INSTRUMENT) or {}
        qty = float(pos.get("qty") or 0) if isinstance(pos, dict) else 0.0
        quote = extra.get("quote") or {}
        bid, ask = quote.get("bid"), quote.get("ask")
        try:
            quote_ok = bool(bid and ask and float(bid) > 0
                            and float(bid) <= float(ask))
        except (TypeError, ValueError):
            quote_ok = False  # malformed quote: fail closed (P3 2026-10-15)
        if qty < 0:
            # open short: cover once the 16h exit is due (old _cover_due)
            due_raw = pos.get("entry_due_at")
            if due_raw:
                due = exit_due_at(_parse(due_raw))
                if now >= due and quote_ok:
                    return [Intent(
                        "exit", INSTRUMENT, qty_hint=int(abs(qty)),
                        price_hint=round(float(ask), 4),
                        reason="free_kraken_link_breakdown cover short at live ask; "
                               "exit due %s (account=%s)" % (due.isoformat(), ACCOUNT))]
            return []
        rows = normalize(bars.get(INSTRUMENT) or [])
        decision = breakdown_decision(rows, now, instrument=INSTRUMENT)
        if decision.get("status") != "entry_ready":
            return []
        if not quote_ok:
            return []
        # ENH gate: control would enter; treatment refuses when the
        # live bid has recovered to/above the breakdown level.
        gate_on = breakdown_validity_gate_enabled(extra)
        refused = bool(gate_on and float(bid) >= float(decision["prior_20_low"]))
        try:
            (extra.setdefault("enhance_paired", [])).append(
                {"sleeve": "free_kraken_link_breakdown", "gate": "breakdown_validity_gate",
                 "gate_on": gate_on, "bid": float(bid),
                 "prior_20_low": float(decision["prior_20_low"]),
                 "control_decision": "enter",
                 "treatment_decision": "refuse" if refused else "enter"})
        except Exception:
            pass
        if refused:
            return []
        return [Intent(
            "enter", INSTRUMENT, qty_hint=1, price_hint=round(float(bid), 4),
            reason="free_kraken_link_breakdown SHORT at live bid after open(i+2); "
                   "event=%s entry_due=%s (account=%s max_exposure=%.2f)"
                   % (decision["signal_event_id"], decision["entry_due_at"],
                      ACCOUNT, MAX_EXPOSURE))]


def signal(bars, slice_state, context):
    return FreeKrakenLinkBreakdown().signal(bars, slice_state, context)
