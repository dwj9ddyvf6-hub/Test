"""FREE_OPT_OWN_IV — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py evaluate(): buy the ATM straddle
(call AND put together) when a causal realized-volatility forecast
exceeds indicative IV by 2 points. One leg is never submitted alone.
The forecast itself was a package input on the old desk too: the
package arrives as context.extra["package"] with exactly 2 legs
(rights {call, put}) and must pass the source's package_skew check
(cross-leg source stamps within 30s). Exit: ten sessions or expiry
(ExitRule time_bars=10 on each leg intent; expiry is core Broker data).
One intent per leg; the core options path submits them as one package
(named misfit: Intent has no package grouping — legs share the reason
tag "package FREE_OPT_OWN_IV_V1").

EXIT EVALUATION (FREEOPT-COMPLETE, 2026-10-16): the designed exit —
ten sessions or expiry — is evaluated below in signal(), the desk's
exit-evaluation home, from the served position records plus the
producer's exit inputs (context.extra["quotes"]: snapshot quotes
for the held contracts; context.extra["session_dates"]: the SPY
session calendar). Entries are deduped per session, the source
execute() journal law (one package per book per session).

VIRTUAL BOOK MAPPING: Ledger account "free_options" (pool $100,000).
"""
import math
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, ExitRule, Intent, SleeveConfig

ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
SOURCE_MAX_SECONDS = 90
RECEIPT_MAX_SECONDS = 30
FUTURE_TOLERANCE_SECONDS = 2
SKEW_MAX_SECONDS = 30

# ENH-20261024 (IMPROVE-free_opt_own_iv): forecast/IV gate — refuse a
# package unless it carries forecast and IV values with
# forecast - IV >= 2.0 points (the strategy's own stated test); both
# values are stamped into the intent reason. Missing/unparseable values
# fail closed. Switched by extra["free_opt_own_iv_improve"]
# ["forecast_iv_gate"] (default ON; OFF restores pre-change rule).

FORECAST_IV_MIN_SPREAD = 2.0

CONFIG = SleeveConfig(
    sleeve_id="free_opt_own_iv", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def forecast_iv_gate_enabled(extra):
    ov = (extra or {}).get("free_opt_own_iv_improve")
    if isinstance(ov, dict) and "forecast_iv_gate" in ov:
        return bool(ov["forecast_iv_gate"])
    return True


def _forecast_iv(package):
    """(forecast, iv) as floats or (None, None). Primary fields
    forecast/iv; aliases forecast_vol/implied_iv accepted."""
    if not isinstance(package, dict):
        return None, None
    def _num(*keys):
        for k in keys:
            if package.get(k) is not None:
                try:
                    v = float(package[k])
                except (TypeError, ValueError):
                    return None
                return v if math.isfinite(v) else None
        return None
    return _num("forecast", "forecast_vol"), _num("iv", "implied_iv")


def parse_time(value):
    text = str(value).replace("Z", "+00:00")
    if "." in text:
        head, rest = text.split(".", 1)
        digits = []
        index = 0
        while index < len(rest) and rest[index].isdigit():
            digits.append(rest[index]); index += 1
        text = f"{head}.{''.join(digits)[:6]}{rest[index:]}" if digits else f"{head}{rest[index:]}"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def quote_block(moment, source_at, received_at):
    if not source_at or not received_at:
        return "source time or receipt time is missing"
    source = parse_time(source_at)
    received = parse_time(received_at)
    if source > moment + timedelta(seconds=FUTURE_TOLERANCE_SECONDS):
        return "source timestamp is beyond the 2-second clock tolerance"
    if received > moment + timedelta(seconds=FUTURE_TOLERANCE_SECONDS):
        return "receipt timestamp is beyond the 2-second clock tolerance"
    if (moment - source).total_seconds() > SOURCE_MAX_SECONDS:
        return f"source age exceeds {SOURCE_MAX_SECONDS:g} seconds"
    if (moment - received).total_seconds() > RECEIPT_MAX_SECONDS:
        return f"receipt age exceeds {RECEIPT_MAX_SECONDS:g} seconds"
    if received < source:
        return "receipt is earlier than the source timestamp"
    return None


def fresh_quote(moment, quote):
    if not quote:
        return False, "Indicative quote has not been observed."
    try:
        block = quote_block(moment, quote.get("t") or quote.get("source_at"),
                            quote.get("received_at"))
        if block:
            return False, block
        if not quote.get("ap") or not quote.get("bp") \
                or float(quote["ap"]) < float(quote["bp"]) \
                or float(quote["bp"]) <= 0:
            return False, "Indicative quote is missing or crossed."
    except (TypeError, ValueError, OverflowError):
        return False, "Indicative quote is malformed."
    return True, None


def package_skew(legs):
    """Verbatim package_skew: consecutive leg source stamps > 30s apart block."""
    stamps = [leg.get("source_at") for leg in legs if leg.get("source_at")]
    if len(stamps) < 2:
        return "cross-leg source time is missing" if len(legs) > 1 else None
    try:
        parsed = [parse_time(s) for s in stamps]
    except (TypeError, ValueError):
        return "cross-leg source time is malformed"
    for left, right in zip(parsed, parsed[1:]):
        if abs((left - right).total_seconds()) > SKEW_MAX_SECONDS:
            return "cross-leg timestamp skew exceeds 30 seconds"
    return None


def _leg_price(leg):
    """A leg's tradable price (its ask): finite and > 0, else None.
    A zero/missing/unparseable ask is a dead quote for that leg —
    the package must not be emitted on it (cf. the ask=0 wedge)."""
    try:
        p = float(leg.get("ask") or leg.get("ap") or 0)
    except (TypeError, ValueError):
        return None
    return p if math.isfinite(p) and p > 0 else None


def _leg_fresh(moment, leg):
    """The leg's own source stamp must be fresh under the sleeve's
    own windows (90s source max / 2s future tolerance), not merely
    within 30s of the other leg: two stamps 10 days old are mutually
    in-skew but are not a fresh quote."""
    try:
        src = parse_time(leg.get("source_at"))
    except (TypeError, ValueError):
        return False
    age = (moment - src).total_seconds()
    return -FUTURE_TOLERANCE_SECONDS <= age <= SOURCE_MAX_SECONDS


def straddle_legs(package):
    legs = (package or {}).get("legs") or []
    if len(legs) == 2 and {leg.get("right") for leg in legs} == {"call", "put"} \
            and package_skew(legs) is None:
        return legs
    return None


def _occ_expiry(symbol):
    s = str(symbol or "")
    if len(s) < 15 or not s[-15:-9].isdigit():
        return None
    d = s[-15:-9]
    return "20%s-%s-%s" % (d[:2], d[2:4], d[4:6])


def _sessions_since(dates, entry_date):
    """Sessions elapsed since entry (the desk's counting law):
    delivered session dates strictly after the entry date."""
    if not entry_date:
        return 0
    entry = str(entry_date)[:10]
    return sum(1 for d in dates or () if str(d)[:10] > entry)


def _two_sided(q):
    if not isinstance(q, dict):
        return False
    try:
        return float(q.get("ask")) > 0 \
            and float(q.get("bid")) >= 0 \
            and float(q.get("ask")) >= float(q.get("bid"))
    except (TypeError, ValueError):
        return False


def _held(extra):
    state = extra.get("sleeve_state") or {}
    out = {}
    for sym, entry in state.items():
        if not isinstance(entry, dict) \
                or not isinstance(entry.get("position"), dict):
            continue
        pos = entry["position"]
        try:
            if float(pos.get("qty") or 0) != 0:
                out[sym] = pos
        except (TypeError, ValueError):
            continue
    return out


def _entered_this_session(extra, session):
    """Source execute() entered at most one package per book per
    session (its journal client id is per book per session); the
    served state carries both facts — entry_date on a held record,
    last_exit_date on the entry after a close."""
    state = extra.get("sleeve_state") or {}
    for entry in state.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("last_exit_date") == session:
            return True
        pos = entry.get("position")
        if isinstance(pos, dict) \
                and str(pos.get("entry_date") or "")[:10] == session:
            return True
    return False


def _exit_intents(extra, session):
    """Designed exit (contracts()): ten sessions or expiry; one leg
    is not left open — the package exits together, and only with a
    two-sided quote for every leg (the source manage_exits
    quotes_ok rule: otherwise the position is retained) — except
    at/past expiry, where the AUDIT3-C bypass applies (below)."""
    held = _held(extra)
    if not held:
        return []
    quotes = extra.get("quotes") or {}
    dates = extra.get("session_dates") or []
    groups = {}
    for sym, pos in held.items():
        groups.setdefault(str(pos.get("entry_date") or "")[:10],
                          []).append((sym, pos))
    out = []
    for entry_date, legs in sorted(groups.items()):
        held_sessions = _sessions_since(dates, entry_date)
        expiries = [e for e in (_occ_expiry(s) for s, _p in legs) if e]
        at_expiry = bool(expiries) and session >= min(expiries)
        if held_sessions < 10 and not at_expiry:
            continue
        # AUDIT3-C (2026-10-16): at/past expiry the two-sided
        # gate must not apply — expiring contracts' quotes go
        # one-sided or vanish exactly when the close is most
        # time-critical, and the pre-cure gate wedged the exit
        # permanently (the record then outlived the position).
        # The close still fires; prices fall back per leg.
        if not at_expiry and any(
                not _two_sided(quotes.get(sym)) for sym, _p in legs):
            continue
        why = "ten_sessions" if held_sessions >= 10 else "expiry"
        for sym, pos in legs:
            qty = float(pos.get("qty") or 0)
            q = quotes.get(sym) or {}
            reason = ("free_opt_own_iv exit: %s entry=%s sessions=%d "
                      "(account=%s)"
                      % (why, entry_date, held_sessions, ACCOUNT))
            if qty > 0:
                out.append(Intent(
                    "exit", sym, qty_hint=int(qty),
                    price_hint=(round(float(q["bid"]), 2)
                                  if q.get("bid") else None),
                    side="sell", position_intent="sell_to_close",
                    reason=reason))
            elif qty < 0:
                out.append(Intent(
                    "exit", sym, qty_hint=int(-qty),
                    price_hint=(round(float(q["ask"]), 2)
                                  if q.get("ask") else None),
                    side="buy", position_intent="buy_to_close",
                    reason=reason))
    return out


class FreeOptOwnIv(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        exits = _exit_intents(extra, context.session)
        if _entered_this_session(extra, context.session):
            return exits
        quote = extra.get("quote")
        moment = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        fresh, _reason = fresh_quote(moment, quote)
        if not fresh:
            return exits
        legs = straddle_legs(extra.get("package"))
        if not legs:
            return exits
        # ENH gate: control buys any fresh complete package; treatment
        # refuses unless forecast - IV >= 2.0 is carried and shown.
        gate_on = forecast_iv_gate_enabled(extra)
        forecast, iv = _forecast_iv(extra.get("package"))
        spread = (forecast - iv) if (forecast is not None and iv is not None) else None
        try:
            (extra.setdefault("enhance_paired", [])).append(
                {"sleeve": "free_opt_own_iv", "gate": "forecast_iv_gate",
                 "gate_on": gate_on, "forecast": forecast, "iv": iv, "spread": spread,
                 "control_decision": "enter",
                 "treatment_decision": "enter" if (not gate_on or (spread is not None and spread >= FORECAST_IV_MIN_SPREAD)) else "refuse"})
        except Exception:
            pass
        if gate_on and (spread is None or spread < FORECAST_IV_MIN_SPREAD):
            return exits
        prices = [_leg_price(leg) for leg in legs]
        if any(not leg.get("symbol") or p is None or not _leg_fresh(moment, leg)
               for leg, p in zip(legs, prices)):
            return exits
        return exits + [Intent(
            "enter", str(leg["symbol"]), qty_hint=1,
            price_hint=round(price, 2),
            exit_rules=(ExitRule("time_bars", 10),),
            reason="free_opt_own_iv package FREE_OPT_OWN_IV_V1 leg=%s "
                   "buy_to_open straddle forecast=%s iv=%s spread=%s (account=%s)"
                   % (leg.get("right"),
                      ("%.2f" % forecast) if forecast is not None else "none",
                      ("%.2f" % iv) if iv is not None else "none",
                      ("%.2f" % spread) if spread is not None else "none",
                      ACCOUNT))
            for leg, price in zip(legs, prices)]


def signal(bars, slice_state, context):
    return FreeOptOwnIv().signal(bars, slice_state, context)
