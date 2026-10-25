"""FREE_KRAKEN_ADA_CROWDED — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_kraken_paper.py crowded(): the ADA breakdown
(port in free_kraken_ada_breakdown) PLUS a crowded-long funding gate:
Kraken HOURLY funding prints (not an 8h Binance settlement) — at least
30 prints in 90 days, and the latest print must be > 0 AND above the
90-day 75th percentile. Short 1 contract at a live quote; cover due
16h after entry due, same clock as the breakdown sleeve.

VIRTUAL BOOK MAPPING: Ledger account "free_kraken" (family budget
$100,000, per-test max exposure 10%). Funding prints arrive as
context.extra["funding_rates"] = [{"timestamp","fundingRate"}]; short
state as context.extra["sleeve_state"]["PF_ADAUSD"].
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "free_kraken"
BUDGET_USD = 100_000.0
MAX_EXPOSURE = 0.10
INSTRUMENT = "PF_ADAUSD"
BAR_SECONDS = 4 * 3600
ENTRY_SHIFT = timedelta(hours=8)
HOLD = timedelta(hours=16)

# ENH-20261024 (IMPROVE-free_kraken_ada_crowded): funding-freshness gate - refuse the
# entry when the latest funding print is more than 2 hours old at the
# decision time (prints are hourly by design; two intervals tolerates
# one missed print). Switched by
# extra["free_kraken_ada_crowded_improve"]["funding_freshness_gate"] (default ON; OFF
# restores the pre-change rule exactly). Paired record appended to
# extra["enhance_paired"].

FUNDING_MAX_AGE = timedelta(hours=2)

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_ada_crowded", cadence_s=3600,
    universe=(INSTRUMENT,), state_schema={"position": "dict|None"},
    risk_pct=None)


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


def funding_freshness_gate_enabled(extra):
    ov = (extra or {}).get("free_kraken_ada_crowded_improve")
    if isinstance(ov, dict) and "funding_freshness_gate" in ov:
        return bool(ov["funding_freshness_gate"])
    return True


def crowded_decision(rows, rates, now, *, instrument="", freshness_gate=True):
    """Verbatim port of crowded(): breakdown first, then the funding gate."""
    base = breakdown_decision(rows, now, instrument=instrument)
    if base["status"] != "entry_ready":
        return base
    dated = []
    for rate in rates or []:
        try:
            stamp = _parse(rate["timestamp"])
            value = float(rate["fundingRate"])
        except (KeyError, TypeError, ValueError):
            continue  # malformed print: fail closed, never raise (P3)
        if stamp <= now:
            dated.append((stamp, value))
    dated.sort(key=lambda x: x[0])
    window = [value for stamp, value in dated if now - stamp <= timedelta(days=90)]
    if len(window) < 30:
        return {"status": "WARMING_UP",
                "reason": f"{len(window)} funding prints in 90 days; 30 required."}
    latest = dated[-1][1]
    latest_at = dated[-1][0]
    if freshness_gate and now - latest_at > FUNDING_MAX_AGE:
        return {"status": "REFUSED_STALE_FUNDING",
                "reason": "Latest funding print is more than 2 hours old "
                          "(age %.2fh); crowding is not certified current."
                          % ((now - latest_at).total_seconds() / 3600.0),
                "latest_print_at": latest_at.isoformat(),
                "latest_age_hours": (now - latest_at).total_seconds() / 3600.0,
                "entry_due_at": base.get("entry_due_at"),
                "signal_event_id": base.get("signal_event_id")}
    ranked = sorted(window)
    percentile = ranked[int(0.75 * (len(ranked) - 1))]
    if latest <= 0 or latest <= percentile:
        return {"status": "QUALIFIED/AWAITING SIGNAL",
                "reason": "Funding is not above zero and the 90-day 75th percentile."}
    return {**base, "status": "entry_ready", "side": "sell",
            "reason": "Crowded-long failure on Kraken hourly funding, "
                      "not a Binance settlement."}


class FreeKrakenAdaCrowded(BaseSleeve):
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
            due_raw = pos.get("entry_due_at")
            if due_raw:
                due = exit_due_at(_parse(due_raw))
                if now >= due and quote_ok:
                    return [Intent(
                        "exit", INSTRUMENT, qty_hint=int(abs(qty)),
                        price_hint=round(float(ask), 4),
                        reason="free_kraken_ada_crowded cover short at live ask; "
                               "exit due %s (account=%s)" % (due.isoformat(), ACCOUNT))]
            return []
        rows = normalize(bars.get(INSTRUMENT) or [])
        gate_on = funding_freshness_gate_enabled(extra)
        decision = crowded_decision(rows, extra.get("funding_rates"), now,
                                    instrument=INSTRUMENT, freshness_gate=gate_on)
        try:
            _ctl = crowded_decision(rows, extra.get("funding_rates"), now, instrument=INSTRUMENT, freshness_gate=False)
            (extra.setdefault("enhance_paired", [])).append(
                {"sleeve": "free_kraken_ada_crowded", "gate": "funding_freshness_gate",
                 "gate_on": gate_on, "decision_status": decision.get("status"),
                 "control_decision": "enter" if _ctl.get("status") == "entry_ready" else "no_entry",
                 "treatment_decision": "enter" if decision.get("status") == "entry_ready" else "refuse_or_no_entry"})
        except Exception:
            pass
        if decision.get("status") != "entry_ready" or not quote_ok:
            return []
        return [Intent(
            "enter", INSTRUMENT, qty_hint=1, price_hint=round(float(bid), 4),
            reason="free_kraken_ada_crowded SHORT crowded-long failure at live "
                   "bid; event=%s entry_due=%s (account=%s max_exposure=%.2f)"
                   % (decision.get("signal_event_id"),
                      decision.get("entry_due_at"), ACCOUNT, MAX_EXPOSURE))]


def signal(bars, slice_state, context):
    return FreeKrakenAdaCrowded().signal(bars, slice_state, context)
