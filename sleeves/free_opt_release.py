"""FREE_OPT_RELEASE — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py evaluate(): buy the straddle
(call AND put) only when a VERIFIED public event timestamp is loaded
for today's session. Exit: the session after the event, or expiry —
evaluated in signal() (FREEOPT-COMPLETE, 2026-10-16): entry fires
only on a verified-event session, so the held record's entry_date
IS the event session and the exit is due one session later (or at
expiry), from the served position records plus the producer's exit
inputs (context.extra["quotes"], context.extra["session_dates"]),
only with two-sided quotes for both legs (the source manage_exits
quotes_ok rule). Entries are deduped per session, the source
execute() journal law. Package rules as in free_opt_own_iv:
exactly 2 legs, rights {call, put}.

VIRTUAL BOOK MAPPING: Ledger account "free_options" (pool $100,000).
Inputs via context.extra: "quote" (freshness gate), "package",
"events": [{session: "YYYY-MM-DD", verified: bool}].

ENH (IMPROVE-free_opt_release, Edge program 2026-10-24): one added
refusal at the entry — refuse the package when its two legs fail the
family's own package-integrity tests (cross-leg source-stamp skew
> 30s, or either leg's source stamp > 90s old / > 2s in the future),
exactly as coded in the sibling free_opt_own_iv (package_skew /
_leg_fresh, copied verbatim below). Switched by
context.extra["free_opt_release_enhance"]["enabled"], default ON;
OFF restores the pre-change rule exactly. The pre-change rule runs
as the shadow control on every package reaching the change point
and is recorded paired on self.last_evaluation["paired"]; it never
emits intents.
"""
import math
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
SOURCE_MAX_SECONDS = 90
RECEIPT_MAX_SECONDS = 30
FUTURE_TOLERANCE_SECONDS = 2
SKEW_MAX_SECONDS = 30


def enhance_enabled(extra):
    """ENH free_opt_release switch: ctx.extra['free_opt_release_enhance']
    ['enabled'], default ON; OFF restores the pre-change rule exactly."""
    ov = (extra or {}).get("free_opt_release_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True

CONFIG = SleeveConfig(
    sleeve_id="free_opt_release", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


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


def _leg_price(leg):
    """A leg's tradable price (its ask): finite and > 0, else None.
    A zero/missing/unparseable ask is a dead quote for that leg —
    the package must not be emitted on it (cf. the ask=0 wedge)."""
    try:
        p = float(leg.get("ask") or leg.get("ap") or 0)
    except (TypeError, ValueError):
        return None
    return p if math.isfinite(p) and p > 0 else None


def package_skew(legs):
    """Verbatim from free_opt_own_iv: consecutive leg source stamps
    > 30s apart block."""
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


def _leg_fresh(moment, leg):
    """Verbatim from free_opt_own_iv: the leg's own source stamp must
    be fresh under the family's windows (90s source max / 2s future
    tolerance)."""
    try:
        src = parse_time(leg.get("source_at"))
    except (TypeError, ValueError):
        return False
    age = (moment - src).total_seconds()
    return -FUTURE_TOLERANCE_SECONDS <= age <= SOURCE_MAX_SECONDS


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
    """Designed exit (contracts()): the session after the event, or
    expiry. Entry required a verified event on the entry session,
    so one session past entry_date is the session after the event.
    The package exits together, only with two-sided quotes for
    every leg (the source manage_exits quotes_ok rule)."""
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
        if held_sessions < 1 and not at_expiry:
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
        why = "session_after_event" if held_sessions >= 1 else "expiry"
        for sym, pos in legs:
            qty = float(pos.get("qty") or 0)
            q = quotes.get(sym) or {}
            reason = ("free_opt_release exit: %s entry=%s sessions=%d "
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


class FreeOptRelease(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        self._paired = []
        self.last_evaluation = {
            "sleeve": "free_opt_release",
            "enhance_switch": enhance_enabled(extra),
            "paired": self._paired}
        exits = _exit_intents(extra, context.session)
        if _entered_this_session(extra, context.session):
            return exits
        quote = extra.get("quote")
        moment = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        fresh, _reason = fresh_quote(moment, quote)
        if not fresh:
            return exits
        events = extra.get("events") or []
        dated = any(e.get("session") == context.session and e.get("verified")
                    for e in events)
        legs = (extra.get("package") or {}).get("legs") or []
        if not dated or len(legs) != 2 \
                or {leg.get("right") for leg in legs} != {"call", "put"}:
            return exits
        prices = [_leg_price(leg) for leg in legs]
        if any(not leg.get("symbol") or p is None
               for leg, p in zip(legs, prices)):
            return exits
        # ENH change point: the family's package-integrity tests.
        # Control (pre-change rule) recorded paired; it never emits.
        enh_on = enhance_enabled(extra)
        block = package_skew(legs)
        if block is None and not all(
                _leg_fresh(moment, leg) for leg in legs):
            block = "leg source stamp stale, future, or missing"
        self._paired.append({
            "symbols": [str(leg.get("symbol")) for leg in legs],
            "source_at": [leg.get("source_at") for leg in legs],
            "control": "enter",
            "treatment": "refuse_integrity"
                         if (enh_on and block) else "enter",
            "switch_on": enh_on, "block": block})
        if enh_on and block:
            return exits
        return exits + [Intent(
            "enter", str(leg["symbol"]), qty_hint=1,
            price_hint=round(price, 2),
            reason="free_opt_release package FREE_OPT_RELEASE_V1 leg=%s "
                   "buy_to_open straddle on verified event %s (account=%s)"
                   % (leg.get("right"), context.session, ACCOUNT))
            for leg, price in zip(legs, prices)]


def signal(bars, slice_state, context):
    return FreeOptRelease().signal(bars, slice_state, context)
