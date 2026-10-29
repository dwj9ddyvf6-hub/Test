"""FREE_OPT_WHEEL — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py contracts()/evaluate(): sell ONE
cash-secured put only when cash covers assignment (cash >= strike*100).
Later lifecycle steps (assignment, shares, covered call) are later
states, not this sleeve's entry — on the lean desk they are core
Ledger/Broker state transitions (named misfit: the Intent contract has
no sell-to-open side; the entry intent carries position_intent in its
reason for the core options path). Freshness: source assess(), as in
free_opt_tail.

EXIT EVALUATION (FREEOPT-COMPLETE, 2026-10-16): the designed exit is
expiry (assignment itself is the broker's settlement, not an order).
On the expiry session the sold put is closed buy_to_close — the
desk's settlement idiom (spx_premium settlement_close) — evaluated
in signal() from the served position record plus the producer's
snapshot quote for the held contract (context.extra["quotes"]),
only with a two-sided quote (the source manage_exits quotes_ok
rule) — except at/past expiry, where the AUDIT3-C bypass applies
(see _exit_intents). Entries are deduped per session, the source
execute() journal law.

ASSIGNMENT LIFECYCLE (AUDIT3 Batch 4, 2026-10-16 — port misfit
M2): assignment, the shares, and the called-away close are Ledger
position state transitions owned by the core derivation
(core/slice_sync.py): an assigned put becomes a wheel shares
record (sleeve_state[UNDERLYING]["position"] with wheel="assigned",
its cost basis strike minus the premium kept). This sleeve's
covered-call side manages those shares from the served state: one
sell_to_open call per 100 reserved shares against a fresh served
call quote (context.extra["call_quote"]) while no covering call
is open — the source's own law, "a call is not sold without
reserved shares". While a shares record is open the cycle is in
its shares leg and no new put is sold: the source design is a
single-position sequential cycle (put -> assignment -> shares ->
covered call -> called away -> restart).

VIRTUAL BOOK MAPPING: Ledger account "free_options" (pool budget
$100,000); the wheel's cash reservation is its slice's Risk budget —
cash arrives as context.extra["cash"] (the old evaluate() argument).
Inputs via context.extra: "quote" (with "strike"), "cash",
"call_quote" (with "strike").
"""
import math
import re as _re
from datetime import datetime, timedelta, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
SOURCE_MAX_SECONDS = 90
RECEIPT_MAX_SECONDS = 30
FUTURE_TOLERANCE_SECONDS = 2

CONFIG = SleeveConfig(
    sleeve_id="free_opt_wheel", cadence_s=300, universe=(),
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


def _occ_expiry(symbol):
    s = str(symbol or "")
    if len(s) < 15 or not s[-15:-9].isdigit():
        return None
    d = s[-15:-9]
    return "20%s-%s-%s" % (d[:2], d[2:4], d[4:6])


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
    """Source execute() entered at most once per book per session
    (its journal client id is per book per session); the served
    state carries both facts — entry_date on a held record,
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
    """Designed exit (contracts()): expiry or call assignment.
    Assignment is the broker's settlement; the order-side exit is
    the expiry-session close (the desk's settlement idiom). This
    exit only ever fires at/past expiry, so the AUDIT3-C bypass
    applies unconditionally here (below)."""
    held = _held(extra)
    if not held:
        return []
    quotes = extra.get("quotes") or {}
    out = []
    for sym, pos in sorted(held.items()):
        expiry = _occ_expiry(sym)
        if expiry is None or session < expiry:
            continue
        # AUDIT3-C (2026-10-16, applied to wheel 2026-10-18):
        # at/past expiry the two-sided gate must not apply —
        # expiring contracts' quotes go one-sided or vanish
        # exactly when the close is most time-critical, and the
        # pre-cure gate wedged the exit permanently (the record
        # then outlived the position). The close still fires;
        # prices fall back per leg.
        q = quotes.get(sym) or {}
        qty = float(pos.get("qty") or 0)
        reason = ("free_opt_wheel exit: expiry settlement expiry=%s "
                  "(account=%s)" % (expiry, ACCOUNT))
        if qty < 0:
            out.append(Intent(
                "exit", sym, qty_hint=int(-qty),
                price_hint=(round(float(q["ask"]), 2)
                              if q.get("ask") else None),
                side="buy", position_intent="buy_to_close",
                reason=reason))
        elif qty > 0:
            out.append(Intent(
                "exit", sym, qty_hint=int(qty),
                price_hint=(round(float(q["bid"]), 2)
                              if q.get("bid") else None),
                side="sell", position_intent="sell_to_close",
                reason=reason))
    return out


def _occ_root(symbol):
    s = str(symbol or "")
    if len(s) < 15 or not s[-15:-9].isdigit():
        return None
    return s[:-15]


def _occ_cp(symbol):
    m = _re.match(r"^[A-Z]{1,6}\d{6}([CP])\d{8}$", str(symbol or ""))
    return m.group(1) if m else None


def _wheel_shares(extra):
    """(underlying, position) of the core-written wheel shares
    record (an assigned put's shares), or (None, None)."""
    state = extra.get("sleeve_state") or {}
    for sym, entry in state.items():
        if not isinstance(entry, dict):
            continue
        pos = entry.get("position")
        if not isinstance(pos, dict) or pos.get("wheel") != "assigned":
            continue
        try:
            if float(pos.get("qty") or 0) > 0:
                return sym, pos
        except (TypeError, ValueError):
            continue
    return None, None


def _open_call_for(extra, underlying):
    """The OCC of an open short call record covering `underlying`,
    or None — the sleeve reads coverage from the served records
    themselves, so a call closed by its own exit frees the shares
    without any extra bookkeeping."""
    state = extra.get("sleeve_state") or {}
    for sym, entry in state.items():
        if _occ_cp(sym) != "C" or _occ_root(sym) != underlying:
            continue
        if not isinstance(entry, dict):
            continue
        pos = entry.get("position")
        if not isinstance(pos, dict):
            continue
        try:
            if float(pos.get("qty") or 0) < 0:
                return sym
        except (TypeError, ValueError):
            continue
    return None


def _covered_call_intent(extra, moment):
    """The wheel's covered-call step (source contracts(): "Later
    steps are assignment, shares, and a covered call... A call is
    not sold without reserved shares"): shares held, no covering
    call open, and a fresh served call quote on the shares' own
    underlying -> sell_to_open one call per 100 reserved shares,
    in the entry intent's own reason idiom."""
    sym, pos = _wheel_shares(extra)
    if sym is None:
        return None
    if _open_call_for(extra, sym) is not None:
        return None
    quote = extra.get("call_quote")
    fresh, _reason = fresh_quote(moment, quote)
    if not fresh:
        return None
    occ = str(quote.get("symbol") or "")
    if _occ_cp(occ) != "C" or _occ_root(occ) != sym:
        return None
    try:
        strike = float(quote.get("strike"))
        bp = float(quote["bp"])
        shares = float(pos.get("qty") or 0)
    except (TypeError, ValueError, KeyError):
        return None
    contracts = int(shares // 100)
    if contracts < 1 or not math.isfinite(strike) or strike <= 0 \
            or not math.isfinite(bp) or bp <= 0:
        return None
    return Intent(
        "enter", occ, qty_hint=contracts,
        price_hint=round(bp, 2),
        reason="free_opt_wheel sell_to_open %d covered call strike=%s "
               "covered_for=%s reserved_shares=%d (account=%s)"
               % (contracts, strike, sym, int(shares), ACCOUNT))


class FreeOptWheel(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        exits = _exit_intents(extra, context.session)
        if _entered_this_session(extra, context.session):
            return exits
        moment = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        cc = _covered_call_intent(extra, moment)
        if cc is not None:
            return exits + [cc]
        if _wheel_shares(extra)[0] is not None:
            # The cycle is in its shares leg (a covering call is
            # open, or none is quotable yet): no new put is sold
            # while the shares record is open.
            return exits
        quote = extra.get("quote")
        fresh, _reason = fresh_quote(moment, quote)
        if not fresh:
            return exits
        strike = quote.get("strike")
        try:
            cash = float(extra.get("cash") or 0)
            strike_f = float(strike) if strike else 0.0
            bp = float(quote["bp"])
        except (TypeError, ValueError):
            return exits
        if not strike or not math.isfinite(strike_f) or strike_f <= 0 \
                or not math.isfinite(cash) or cash < strike_f * 100 \
                or not math.isfinite(bp) or bp <= 0:
            return exits
        # AUDIT3-C (2026-10-16): the pre-cure test searched the
        # whole OCC symbol for the letter "P" — every SPY contract
        # (calls included) contains P in the underlying, so the
        # wheel would sell a "cash-secured put" on a CALL. Parse
        # the OCC type character at its fixed position instead.
        _sym = str(quote.get("symbol") or "")
        _m = _re.match(r"^[A-Z]{1,6}\d{6}([CP])\d{8}$", _sym)
        if _m is None or _m.group(1) != "P":
            return exits
        return exits + [Intent(
            "enter", str(quote["symbol"]), qty_hint=1,
            price_hint=round(bp, 2),
            reason="free_opt_wheel sell_to_open 1 cash-secured put strike=%s "
                   "cash=%.2f covers assignment (account=%s)"
                   % (strike_f, cash, ACCOUNT))]


def signal(bars, slice_state, context):
    return FreeOptWheel().signal(bars, slice_state, context)
