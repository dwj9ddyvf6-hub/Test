"""Aster batch 3 — options recovery (RSI2 vertical, VWAP20 long) +
Tensor LEAPS sleeves (ASTER-BUILD-MAP batch 3; TSV rows 26-35).

FAITHFUL PORT of the staged archive source
`source/backend/r19_options.py` (books in
`source/strategies/r19/options_rules.json`), translated to the v3
snapshot form. Rules preserved from the archive:

- recovery_signal(rows, method): >=200 completed native sessions,
  chronological/complete/observed bars; close > SMA200; RSI2 < 10
  (the archive's own Wilder-seeded recursion, copied verbatim) or
  VWAP20: close <= 0.98 * VWAP20 of typical price (H+L+C)/3.
- Entries only 09:35 <= ET < 09:40, market open, signal session ==
  calendar previous session, universe [IWM, QQQ, SPY] in order,
  first passing symbol only, one package per book (no entry while
  any package is held).
- Contract selection (_select_contracts): DTE band + delta band
  (greeks <=10s old at selection), earliest expiry, then delta
  nearest band midpoint, then strike nearest spot. Vertical wing:
  same expiry/right, strike beyond long in the trade direction,
  nearest spot*1.02 (calls).
- Caps: vertical debit/width <= max_debit_width; long
  debit/(spot*100) <= max_premium_spot.
- Sizing: risk = min(slice_equity * risk_fraction, 5% of the $10k
  slice initial - outstanding max-loss, slice cash); qty =
  floor(risk / (debit_per_package + per-leg fees)), capped by
  displayed size on every leg; qty < 1 refuses.
- Exits (_exit_intents): european -> settle at expiry close
  (official_PM_expiry); planned session exit = hold_sessions-th
  session counting entry as session 1 (exit_session computed from
  the calendar's future_sessions exactly as _exit_session), due
  5 min before that session's close (and any time after);
  pre-expiry obligation exit at previous-session-before-expiry,
  15 min before close; verified assignment alert exit; touch
  books: fresh (<=5s, sip) underlying bid >= entry_spot * 1.02
  exits early. Compulsory exits are priced from current OPRA
  quotes; an unpriceable due exit emits nothing here and is named
  by the desk's obligation surfacing upstream (the archive raised
  blockers; v3 intent lists carry intents only).
- tensor_leaps: entry ONLY on a qualified native G4 event
  (Tensor product consumed at the sleeve layer — the Tensor ENGINE
  is untouched): qualified_native_G4 true, source_sha256 present,
  entry_session == calendar session, signal_end >= book
  installed_at, signal_end <= available_at < now, and a future
  original_G4_exit_at deadline. DTE 540-720, delta 0.6-0.8, long
  calls; exit session = first session >= entry + 365 calendar days
  (archive hold_calendar_days), superseded by the original G4
  saved deadline and by qualified G4 exit events for the held
  event id.

Slice convention (map §3): $10,000 slice; risk A = 2% = $200,
B = 0.5% = $50 — the source books' fractions applied to the slice.

Inputs are v3 producer keys ONLY (view["bars"], view["options_chain"],
view["options_quotes"], view["quotes"], view["positions"],
view["extra"]["tensor_G4_events"/"tensor_G4_exit_events"]). No v3
producer emits OPRA chains or G4 events yet, so in the live registry
these sleeves are UNFED by name — never fed invented data.
Fee schedule comes from the snapshot (explicit paper assumption);
absent it, the archive's 15 bps of per-package debit is used as the
fee amount per package leg-count share — see FIDELITY-LEDGER ASTER-B3:
fixtures always supply the explicit schedule; the fallback exists
only so a fee-less snapshot degrades to a named constant, and entry
sizing records the fee used in the intent metadata.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    ET = timezone(timedelta(hours=-4))

INPUTS = ("bars", "options_chain", "quotes", "positions")
PRODUCERS = (
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 3600},
    {"name": "options_chain", "outputs": ("options_chain", "options_quotes"),
     "freshness_sla_s": 900},
    {"name": "quotes", "outputs": ("quotes",), "freshness_sla_s": 60},
    {"name": "broker_readback", "outputs": ("positions",),
     "freshness_sla_s": 900},
    {"name": "tensor_bundle", "outputs": ("tensor",), "freshness_sla_s": 93600},
)

# book id -> archive options_rules.json book, verbatim fields.
_BOOKS = {
    "OPT_RSI2_VERTICAL_FIXED_A": dict(signal="RSI2", structure="vertical",
        exit_rule="fixed", risk_fraction=0.02, max_debit_width=0.6,
        max_premium_spot=0.025, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_RSI2_VERTICAL_FIXED_B": dict(signal="RSI2", structure="vertical",
        exit_rule="fixed", risk_fraction=0.005, max_debit_width=0.45,
        max_premium_spot=0.015, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_RSI2_VERTICAL_TOUCH_A": dict(signal="RSI2", structure="vertical",
        exit_rule="touch", risk_fraction=0.02, max_debit_width=0.6,
        max_premium_spot=0.025, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_RSI2_VERTICAL_TOUCH_B": dict(signal="RSI2", structure="vertical",
        exit_rule="touch", risk_fraction=0.005, max_debit_width=0.45,
        max_premium_spot=0.015, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_TENSOR_LEAPS_A": dict(signal=None, structure="long",
        exit_rule=None, risk_fraction=0.02, max_debit_width=None,
        max_premium_spot=0.5, dte=(540, 720), delta=(0.6, 0.8),
        hold_calendar_days=365),
    "OPT_TENSOR_LEAPS_B": dict(signal=None, structure="long",
        exit_rule=None, risk_fraction=0.005, max_debit_width=None,
        max_premium_spot=0.5, dte=(540, 720), delta=(0.6, 0.8),
        hold_calendar_days=365),
    "OPT_VWAP20_LONG_FIXED_A": dict(signal="VWAP20", structure="long",
        exit_rule="fixed", risk_fraction=0.02, max_debit_width=0.6,
        max_premium_spot=0.025, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_VWAP20_LONG_FIXED_B": dict(signal="VWAP20", structure="long",
        exit_rule="fixed", risk_fraction=0.005, max_debit_width=0.45,
        max_premium_spot=0.015, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_VWAP20_LONG_TOUCH_A": dict(signal="VWAP20", structure="long",
        exit_rule="touch", risk_fraction=0.02, max_debit_width=0.6,
        max_premium_spot=0.025, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
    "OPT_VWAP20_LONG_TOUCH_B": dict(signal="VWAP20", structure="long",
        exit_rule="touch", risk_fraction=0.005, max_debit_width=0.45,
        max_premium_spot=0.015, dte=(14, 21), delta=(0.5, 0.6),
        hold_sessions=5),
}

SPECS = {
    "aster_rec_rsi2_vertical_fixed_a": dict(
        book="OPT_RSI2_VERTICAL_FIXED_A", family="recovery",
        **_BOOKS["OPT_RSI2_VERTICAL_FIXED_A"]),
    "aster_rec_rsi2_vertical_fixed_b": dict(
        book="OPT_RSI2_VERTICAL_FIXED_B", family="recovery",
        **_BOOKS["OPT_RSI2_VERTICAL_FIXED_B"]),
    "aster_rec_rsi2_vertical_touch_a": dict(
        book="OPT_RSI2_VERTICAL_TOUCH_A", family="recovery",
        **_BOOKS["OPT_RSI2_VERTICAL_TOUCH_A"]),
    "aster_rec_rsi2_vertical_touch_b": dict(
        book="OPT_RSI2_VERTICAL_TOUCH_B", family="recovery",
        **_BOOKS["OPT_RSI2_VERTICAL_TOUCH_B"]),
    "aster_tensor_leaps_a": dict(
        book="OPT_TENSOR_LEAPS_A", family="tensor_leaps",
        **_BOOKS["OPT_TENSOR_LEAPS_A"]),
    "aster_tensor_leaps_b": dict(
        book="OPT_TENSOR_LEAPS_B", family="tensor_leaps",
        **_BOOKS["OPT_TENSOR_LEAPS_B"]),
    "aster_rec_vwap20_long_fixed_a": dict(
        book="OPT_VWAP20_LONG_FIXED_A", family="recovery",
        **_BOOKS["OPT_VWAP20_LONG_FIXED_A"]),
    "aster_rec_vwap20_long_fixed_b": dict(
        book="OPT_VWAP20_LONG_FIXED_B", family="recovery",
        **_BOOKS["OPT_VWAP20_LONG_FIXED_B"]),
    "aster_rec_vwap20_long_touch_a": dict(
        book="OPT_VWAP20_LONG_TOUCH_A", family="recovery",
        **_BOOKS["OPT_VWAP20_LONG_TOUCH_A"]),
    "aster_rec_vwap20_long_touch_b": dict(
        book="OPT_VWAP20_LONG_TOUCH_B", family="recovery",
        **_BOOKS["OPT_VWAP20_LONG_TOUCH_B"]),
}

UNIVERSE = ("IWM", "QQQ", "SPY")

EXP_ID_LEAPS_SPREAD = "ENH-B13-LEAPS-SPREAD-20261024"
LEAPS_MAX_SPREAD_FRAC = 0.30  # desk precedent: laz8_opt 30% spread gate
def _leaps_spread_enh_on(view, ctx, sid):
    """ENH (Edge batch 13): LEAPS spread gate. Default ON; OFF restores
    the pre-change ask-only pricing rule exactly."""
    extra = {}
    if isinstance(ctx, dict): extra.update(ctx.get("extra") or {})
    extra.update((view or {}).get("extra") or {})
    ov = extra.get("aster_leaps_enh")
    if isinstance(ov, dict):
        per = ov.get(sid) if isinstance(ov.get(sid), dict) else ov
        if isinstance(per, dict) and "spread_gate" in per:
            return bool(per["spread_gate"])
    return True

SLICE_USD = 10000.0

# --- ENH (Edge IMPROVE batch 10, 2026-10-24): mid-price limit execution.
# Binding leak: entries pay the full package ask and exits take the full
# package bid on 5-session recovery options (market orders) — the quoted
# spread is crossed twice on a short-horizon edge, even though this
# engine already fetches fresh OPRA bid/ask for every leg. Treatment:
# limit at the package mid. Switch: extra["enh_<sid>"] or
# extra["aster_b3_enh"] {"mid_limit": bool}, default ON; OFF restores
# the pre-change market order exactly. Shadow control = the ask/bid
# package price the pre-change rule would have crossed, recorded paired
# on the intent ("enhance_exp") and in extra["aster_enh_exp_journal"].
# Scoped to the recovery family (batch-10 sleeves); tensor_leaps keeps
# the pre-change execution (different horizon, separate program).
EXP_ID_B3 = "ENH-ASTERB3-MIDLIMIT-20261024"

def _enh_on(view, sid):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b3_enh")
    if isinstance(ov, dict) and "mid_limit" in ov:
        return bool(ov["mid_limit"])
    return True

def _paired(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)

def _mid_quotes(quotes):
    out = []
    for q in quotes:
        b = float(q.get("bid") or 0); a = float(q.get("ask") or 0)
        if not (a >= b > 0):
            return None
        out.append({"bid": (a + b) / 2, "ask": (a + b) / 2})
    return out


def _stamp(s):
    v = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if v.tzinfo is None:
        raise ValueError("timezone_required")
    return v


def _now(view, ctx):
    raw = (view or {}).get("now") or (ctx or {}).get("now")
    if raw is None:
        sess = (ctx or {}).get("session") or ""
        raw = f"{str(sess)[:10]}T09:37:00-04:00" if sess else None
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    return _stamp(raw)


def _bars(view, sym):
    m = view.get("bars") or {}
    for key in (sym, f"{sym}|1Day", f"{sym}|1d", f"{sym}|1D"):
        if m.get(key):
            return m[key]
    return []


def rsi2(closes):
    """Archive rsi2(), verbatim recursion."""
    if len(closes) < 3:
        raise ValueError("RSI2_warmup")
    changes = [float(b) - float(a) for a, b in zip(closes, closes[1:])]
    gain = sum(max(x, 0) for x in changes[:2]) / 2
    loss = sum(max(-x, 0) for x in changes[:2]) / 2
    for x in changes[2:]:
        gain = (gain + max(x, 0)) / 2
        loss = (loss + max(-x, 0)) / 2
    return 50.0 if gain == loss == 0 else 100.0 if loss == 0 else \
        100 - 100 / (1 + gain / loss)


def recovery_signal(rows, method, now):
    """Archive recovery_signal(): returns dict or raises ValueError."""
    if method not in ("RSI2", "VWAP20"):
        raise ValueError("unknown_recovery_signal_method")
    if len(rows) < 200:
        raise ValueError("200_completed_native_sessions_required")
    rows = rows[-200:] if len(rows) > 200 else rows
    # archive validates the full supplied window; v3 bars producers
    # supply the trailing window — validate the last 200 exactly as
    # the archive validates its (200-row) input.
    for x in rows:
        if _stamp(x["usable_after"]) > now or x.get("complete") is not True:
            raise ValueError("unobserved_or_incomplete_signal_bar")
    sessions = [x["session"] for x in rows]
    if len(set(sessions)) != len(rows) or sessions != sorted(sessions):
        raise ValueError("duplicate_or_nonchronological_sessions")
    for x in rows:
        low, high, close, volume = (float(x["l"]), float(x["h"]),
                                     float(x["c"]), float(x["v"]))
        if not 0 < low <= close <= high or volume < 0:
            raise ValueError("invalid_native_underlying_bar_OHLCV")
        if not all(math.isfinite(v) for v in (low, high, close, volume)):
            raise ValueError("nonfinite_native_underlying_bar")
    closes = [float(x["c"]) for x in rows]
    sma = sum(closes[-200:]) / 200
    if method == "RSI2":
        value = rsi2(closes)
        passed = closes[-1] > sma and value < 10
    else:
        last = rows[-20:]
        volume = sum(float(x["v"]) for x in last)
        if volume <= 0:
            raise ValueError("VWAP_zero_volume")
        value = sum((float(x["h"]) + float(x["l"]) + float(x["c"])) / 3
                    * float(x["v"]) for x in last) / volume
        passed = closes[-1] > sma and closes[-1] <= value * .98
    return {"pass": passed, "method": method, "value": value,
            "sma200": sma, "signal_session": rows[-1]["session"]}


def _fees(view, legs_count, debit):
    """Per-contract-per-fill fee total for a package (archive
    _entry_intent: fee schedule from the snapshot). Fallback: the
    books' fee_bps=15 applied to the package debit (named constant;
    see module docstring)."""
    fee = ((view.get("extra") or {}).get("option_fees")
           or (view.get("options") or {}).get("fees") or {})
    per = fee.get("per_contract_per_fill")
    if per is not None:
        return float(per) * legs_count, float(per)
    return debit * 0.0015, debit * 0.0015 / max(legs_count, 1)


def _quote(view, occ):
    q = (view.get("options_quotes") or {}).get(occ)
    if q is None:
        raise ValueError("missing_option_quote")
    return q


def _fresh(q, now, max_age_s, feed):
    if q.get("feed") != feed:
        raise ValueError(f"requires_{feed}")
    market, receipt = _stamp(q["market_at"]), _stamp(q["received_at"])
    if not market <= receipt <= now or (now - market).total_seconds() > max_age_s:
        raise ValueError("stale_quote")
    return q


def _spot(view, sym, now):
    uq = (view.get("quotes") or {}).get(sym)
    if uq is None:
        raise ValueError("missing_underlying_quote")
    _fresh(uq, now, 5, "sip")
    if uq.get("symbol") not in (None, sym):
        raise ValueError("underlying_identity_mismatch")
    return (float(uq["bid"]) + float(uq["ask"])) / 2


def _select_contracts(view, spec, sym, now):
    """Archive _select_contracts for calls. Returns (legs, spot)."""
    spot = _spot(view, sym, now)
    today = now.astimezone(ET).date()
    chain = (view.get("options_chain") or {}).get(sym) or []
    if not chain:
        raise ValueError("no_chain_for_symbol")
    cands = []
    for raw in chain:
        if raw.get("right") != "call":
            continue
        try:
            expiry = raw["expiry"]
            dte = (datetime.fromisoformat(expiry).date() - today).days
            delta = abs(float(raw["delta"]))
            if not (spec["dte"][0] <= dte <= spec["dte"][1]
                    and spec["delta"][0] <= delta <= spec["delta"][1]):
                continue
            gm, gr = _stamp(raw["greeks_market_at"]), _stamp(raw["greeks_received_at"])
            if not gm <= gr <= now or (now - gm).total_seconds() > 10:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        cands.append(raw)
    if not cands:
        raise ValueError("no_qualified_delta_DTE_contract")
    mid = sum(spec["delta"]) / 2
    long = min(cands, key=lambda x: (x["expiry"],
                                     abs(abs(float(x["delta"])) - mid),
                                     abs(float(x["strike"]) - spot),
                                     x["symbol"]))
    legs = [dict(long, ratio=1)]
    if spec["structure"] == "vertical":
        target = spot * 1.02
        wings = [x for x in chain
                 if x.get("right") == "call"
                 and x.get("expiry") == long["expiry"]
                 and float(x.get("strike") or 0) > float(long["strike"])]
        if not wings:
            raise ValueError("no_same_expiry_wing")
        wing = min(wings, key=lambda x: (abs(float(x["strike"]) - target),
                                         x["symbol"]))
        legs.append(dict(wing, ratio=-1))
    return legs, spot


def _package_price(legs, quotes, opening):
    """Archive _cash_price: open pays ask long / bid short; close
    receives bid long / pays ask short. Per package (x100)."""
    total = 0.0
    for leg, q in zip(legs, quotes):
        ratio = int(leg["ratio"])
        px = float(q["ask"] if (ratio > 0) == opening else q["bid"])
        total += ratio * px * 100
    return total


def _shape(legs):
    ratios = [int(x["ratio"]) for x in legs]
    if len(legs) == 1 and ratios == [1]:
        return "long", None
    if len(legs) == 2 and ratios == [1, -1]:
        width = abs(float(legs[0]["strike"]) - float(legs[1]["strike"])) * 100
        return "debit_vertical", width
    raise ValueError("unsupported_package_shape")


def _exit_session(view, spec, entry_session):
    """Archive _exit_session from the calendar's future_sessions."""
    cal = view.get("calendar") or {}
    sessions = cal.get("future_sessions") or []
    if sessions != sorted(set(sessions)) or not sessions \
            or sessions[0] != entry_session:
        raise ValueError("complete_future_exchange_sessions_required")
    if spec.get("hold_calendar_days"):
        threshold = (datetime.fromisoformat(entry_session).date()
                     + timedelta(days=spec["hold_calendar_days"])).isoformat()
        choices = [x for x in sessions if x >= threshold]
        if not choices:
            raise ValueError("calendar_checkpoint_sessions_required")
        return min(choices)
    n = spec.get("hold_sessions", 5)
    if len(sessions) < n:
        raise ValueError("complete_future_exchange_sessions_required")
    return sessions[n - 1]


def _session_exit_due(view, now, session, minutes_before_close):
    """Archive _session_exit_due."""
    today = now.astimezone(ET).date().isoformat()
    if today > session:
        return True
    if today < session:
        return False
    cal = view.get("calendar") or {}
    close = (cal.get("option_close_by_date") or {}).get(session)
    if not close and cal.get("session") == session:
        close = cal.get("close")
    if not close:
        raise ValueError("owned_exit_session_close_calendar_required")
    return now >= _stamp(close) - timedelta(minutes=minutes_before_close)


def _positions(view):
    out = []
    for p in view.get("positions") or []:
        if not isinstance(p, dict) or not p.get("symbol"):
            continue
        meta = p.get("metadata") or {}
        if "legs" in meta or "legs" in p:
            out.append(p)
    return out


def _meta(p):
    return p.get("metadata") or {}


def _held_legs(p):
    return _meta(p).get("legs") or p.get("legs")


def _exit_intents(sleeve_id, spec, view, ctx, now, session):
    cal = view.get("calendar") or {}
    out = []
    seq = 0
    for p in _positions(view):
        meta = _meta(p)
        legs = _held_legs(p)
        if not legs:
            continue
        qty = int(float(p.get("qty") or 0))
        if qty <= 0:
            continue
        expiry = legs[0].get("expiry") or legs[0].get("expiration_date")
        due, reason, action = False, None, "close"
        if legs[0].get("exercise_style") == "european":
            close = (cal.get("option_close_by_date") or {}).get(expiry)
            if cal.get("session", session) >= expiry and close \
                    and now >= _stamp(close):
                due, reason, action = True, "official_PM_expiry", "settle"
        else:
            try:
                due = _session_exit_due(view, now,
                                        meta.get("exit_session", expiry), 5)
            except (ValueError, KeyError, TypeError):
                due = False
            reason = "planned_session_exit"
            guard = (cal.get("previous_session_by_date") or {}).get(expiry) \
                or meta.get("expiry_exit_session")
            if guard:
                try:
                    if _session_exit_due(view, now, guard, 15):
                        due, reason = True, "pre_expiry_obligation_exit"
                except (ValueError, KeyError, TypeError):
                    pass
            check = ((view.get("extra") or {}).get("exercise_checks")
                     or (view.get("extra") or {}).get("assignment_alerts")
                     or {}).get(legs[0].get("underlying"), {})
            if check.get("assignment_alert") and check.get("verified") is True \
                    and check.get("source_sha256") \
                    and _stamp(check["received_at"]) <= now:
                due, reason = True, "assignment_risk_exit_or_lifecycle_obligation"
            if spec["family"] == "tensor_leaps":
                if meta.get("original_G4_exit_at") \
                        and now >= _stamp(meta["original_G4_exit_at"]):
                    due, reason = True, "original_G4_saved_deadline_exit"
                if not due:
                    events = (view.get("extra") or {}).get(
                        "tensor_G4_exit_events") or []
                    if any(x.get("event_id") == meta.get("G4_event_id")
                           and x.get("qualified_native_G4")
                           and x.get("exit_due") and x.get("source_sha256")
                           and _stamp(x["available_at"]) <= now
                           for x in events):
                        due, reason = True, "original_G4_state_or_time_exit"
            if not due and spec.get("exit_rule") == "touch" \
                    and (view.get("extra") or {}).get("market_open", True):
                try:
                    uq = (view.get("quotes") or {})[legs[0]["underlying"]]
                    _fresh(uq, now, 5, "sip")
                    if float(uq["bid"]) >= float(meta["entry_spot"]) * 1.02:
                        due, reason = True, \
                            "simultaneously_observed_two_percent_recovery"
                except (ValueError, KeyError, TypeError):
                    pass
        if not due:
            continue
        price = None
        if action != "settle":
            try:
                quotes = []
                for leg in legs:
                    q = _quote(view, leg["symbol"])
                    _fresh(q, now, 10, "opra")
                    if abs(int(q["bid_size"] if int(leg["ratio"]) > 0
                               else q["ask_size"])) < qty:
                        raise ValueError("exit_depth_insufficient")
                    quotes.append(q)
                times = [_stamp(q["market_at"]) for q in quotes]
                if (max(times) - min(times)).total_seconds() > 2:
                    raise ValueError("asynchronous_package_legs")
                price = _package_price(legs, quotes, opening=False)
            except (ValueError, KeyError, TypeError):
                continue  # unpriceable due exit: no fake fill price
        seq += 1
        stamp_s = now.strftime("%Y%m%dT%H%M%S")
        xit = {
            "intent_id": f"{sleeve_id}-{stamp_s}-x{seq}",
            "kind": "exit", "symbol": p["symbol"], "side": "sell",
            "qty": qty, "order_type": "market", "limit_price": None,
            "stop_price": None,
            "reason": f"aster exit: {reason} {sleeve_id} book={spec['book']}",
            "time_in_force": "day", "position_intent": "sell_to_close",
            "price_hint": (round(price, 4) if price is not None else None),
            "legs": legs, "metadata": dict(meta),
            "exit_action": action}
        if action != "settle" and price is not None \
                and spec.get("family") == "recovery" \
                and _enh_on(view, sleeve_id):
            try:
                qs = [_quote(view, leg["symbol"]) for leg in legs]
                mq = _mid_quotes(qs)
                if mq is not None:
                    mid_price = _package_price(legs, mq, opening=False)
                    if mid_price > 0:
                        rec = {"exp_id": EXP_ID_B3, "sleeve": sleeve_id,
                               "kind": "exit", "switch_on": True,
                               "control_price": round(price, 4),
                               "treatment_limit_ps": round(mid_price / 100, 4),
                               "spread_saved": round(mid_price - price, 4)}
                        xit["order_type"] = "limit"
                        xit["limit_price"] = round(mid_price / 100, 2)
                        xit["enhance_exp"] = rec
                        _paired(view, rec)
            except (ValueError, KeyError, TypeError):
                pass
        out.append(xit)
    return out


def _entry_intent(sleeve_id, spec, view, ctx, now, session, sym,
                  signal_id, extra_meta=None):
    legs, spot = _select_contracts(view, spec, sym, now)
    quotes = []
    for leg in legs:
        q = _quote(view, leg["symbol"])
        _fresh(q, now, 10, "opra")
        quotes.append(q)
    times = [_stamp(q["market_at"]) for q in quotes]
    if (max(times) - min(times)).total_seconds() > 2:
        raise ValueError("asynchronous_package_legs")
    # ENH batch 13 (binding leak: unpriced spread on 540-720 DTE LEAPS):
    # entry paid the ask with NO bid/ask spread check; a wide spread is
    # an immediate, certain loss of the warehoused premium. Refuse when
    # (ask-bid)/mid exceeds the desk's 30% options spread gate. The
    # ask-only decision is the shadow control, recorded on the intent.
    if spec["family"] == "tensor_leaps" and _leaps_spread_enh_on(view, ctx, sleeve_id):
        for leg, q in zip(legs, quotes):
            if int(leg["ratio"]) > 0:
                bid, ask = float(q["bid"]), float(q["ask"])
                mid = (bid + ask) / 2
                if mid > 0 and (ask - bid) / mid > LEAPS_MAX_SPREAD_FRAC:
                    raise ValueError("leaps_spread_gate")
    shape, width = _shape(legs)
    debit = _package_price(legs, quotes, opening=True)
    if shape == "debit_vertical" \
            and debit / width > float(spec["max_debit_width"]):
        raise ValueError("spread_debit_budget_exceeded")
    if shape == "long" \
            and debit / (spot * 100) > float(spec["max_premium_spot"]):
        raise ValueError("uncapped_premium_budget_exceeded")
    fees, per_leg_fee = _fees(view, len(legs), debit)
    per = debit + fees
    sl = view.get("slice") or {}
    equity = float(sl.get("capital_usd") or SLICE_USD)
    cash = float(sl.get("cash_usd") or equity)
    outstanding = 0.0
    for p in _positions(view):
        m = _meta(p)
        if m.get("max_loss_per_package") is not None:
            outstanding += max(0.0, float(m["max_loss_per_package"])) \
                * int(float(p.get("qty") or 0))
    risk = min(equity * float(spec["risk_fraction"]),
               equity * 0.05 - outstanding, cash)
    qty = int(risk // per) if per > 0 else 0
    if qty < 1:
        raise ValueError("whole_contract_unaffordable_or_premium_reserve_exhausted")
    for leg, q in zip(legs, quotes):
        avail = int(q["ask_size"] if int(leg["ratio"]) > 0 else q["bid_size"])
        qty = min(qty, avail)
    if qty < 1:
        raise ValueError("zero_displayed_package_size")
    exit_session = _exit_session(view, spec, session)
    cal = view.get("calendar") or {}
    meta = {"rule_id": spec["book"], "risk_budget": round(risk, 4),
            "entry_spot": spot, "entry_session": session,
            "exit_session": exit_session,
            "expiry_exit_session": (cal.get("previous_session_by_date")
                                    or {}).get(legs[0]["expiry"]),
            "held_sessions": spec.get("hold_sessions"),
            "exit_rule": spec.get("exit_rule", "fixed"),
            "signal_id": signal_id, "legs": legs,
            "per_leg_fee": per_leg_fee,
            "max_loss_per_package": round(per, 4)}
    if extra_meta:
        meta.update(extra_meta)
    pkg = "PKG:" + hashlib.sha256(json.dumps(
        [spec["book"], signal_id, [x["symbol"] for x in legs]],
        sort_keys=True).encode()).hexdigest()[:24]
    stamp_s = now.strftime("%Y%m%dT%H%M%S")
    it = {"intent_id": f"{sleeve_id}-{stamp_s}-1", "kind": "entry",
            "symbol": pkg, "side": "buy", "qty": qty,
            "order_type": "market", "limit_price": None,
            "stop_price": None,
            "reason": f"aster entry: {spec['family']}_qualified_entry "
                      f"{sleeve_id} book={spec['book']} sym={sym} "
                      f"signal={signal_id}",
            "time_in_force": "day", "position_intent": "buy_to_open",
            "price_hint": round(debit, 4), "legs": legs, "metadata": meta}
    if spec.get("family") == "recovery" and _enh_on(view, sleeve_id):
        mq = _mid_quotes(quotes)
        if mq is not None:
            mid_debit = _package_price(legs, mq, opening=True)
            if mid_debit > 0:
                rec = {"exp_id": EXP_ID_B3, "sleeve": sleeve_id,
                       "kind": "entry", "switch_on": True,
                       "control_price": round(debit, 4),
                       "treatment_limit_ps": round(mid_debit / 100, 4),
                       "spread_saved": round(debit - mid_debit, 4)}
                it["order_type"] = "limit"
                it["limit_price"] = round(mid_debit / 100, 2)
                it["enhance_exp"] = rec
                _paired(view, rec)
    return it


def evaluate(sleeve_id, view, ctx=None):
    spec = SPECS[sleeve_id]
    view = view or {}
    ctx = ctx or {}
    now = _now(view, ctx)
    if now is None:
        return []
    session = str(ctx.get("session") or (view.get("calendar") or {})
                  .get("session") or now.astimezone(ET).date().isoformat())[:10]
    out = _exit_intents(sleeve_id, spec, view, ctx, now, session)
    if out:
        return out
    extra = view.get("extra") or {}
    # Archive: entries are evaluated only when no package is held.
    if _positions(view):
        return []
    if extra.get("market_open", True) is not True:
        return []
    et = now.astimezone(ET)
    if not (9, 35) <= (et.hour, et.minute) < (9, 40):
        return []
    cal = view.get("calendar") or {}
    if spec["family"] == "recovery":
        prev = cal.get("previous_session")
        for sym in UNIVERSE:
            try:
                rows = _bars(view, sym)
                signal = recovery_signal(rows, spec["signal"], now)
                if prev is not None and signal["signal_session"] != prev:
                    continue
                if not signal["pass"]:
                    continue
                sid = f"{spec['book']}:{sym}:{signal['signal_session']}"
                return [_entry_intent(sleeve_id, spec, view, ctx, now,
                                      session, sym, sid)]
            except (ValueError, KeyError, TypeError):
                continue
        return []
    if spec["family"] == "tensor_leaps":
        events = extra.get("tensor_G4_events") or []
        installed = extra.get("installed_at") or ctx.get("installed_at")
        for event in events:
            try:
                if not event.get("signal_end") or not installed:
                    continue
                if _stamp(event["signal_end"]) < _stamp(installed):
                    continue  # pre-install: not a forward entry
                if event.get("qualified_native_G4") is not True \
                        or not event.get("source_sha256") \
                        or event.get("entry_session") != session:
                    continue
                if not _stamp(event["signal_end"]) \
                        <= _stamp(event["available_at"]) < now:
                    continue
                if not event.get("original_G4_exit_at") \
                        or _stamp(event["original_G4_exit_at"]) <= now:
                    continue
                sid = f"{spec['book']}:{event['event_id']}"
                return [_entry_intent(
                    sleeve_id, spec, view, ctx, now, session,
                    event["symbol"], sid,
                    {"G4_source_sha256": event["source_sha256"],
                     "G4_event_id": event["event_id"],
                     "G4_signal_end": event["signal_end"],
                     "original_G4_exit_at": event["original_G4_exit_at"],
                     "original_G4_exit_session":
                         event.get("original_G4_exit_session")})]
            except (ValueError, KeyError, TypeError):
                continue
        return []
    return []


def register(registry):
    for p in PRODUCERS:
        if p["name"] not in registry.producers:
            registry.register_producer(p["name"], p["outputs"],
                                       p["freshness_sla_s"])
    for sid in SPECS:
        registry.register_sleeve(sid, INPUTS)
    return registry


def config_rows():
    rows = []
    for sid in SPECS:
        rows.append({
            "id": sid, "module": f"adapters3.{sid}", "cadence_s": 300,
            "session": "rth",
            "slice": {"capital_usd": SLICE_USD, "cash_usd": SLICE_USD},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None, "params": {}, "inputs": list(INPUTS),
            "parked": False})
    return rows
