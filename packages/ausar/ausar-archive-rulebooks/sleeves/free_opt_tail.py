"""FREE_OPT_TAIL — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py contracts()/evaluate(): buy ONE
put when the underlying day return is at or below -3%. Exit: five
sessions or a 50% premium loss (the 5-session hold is ExitRule data)
— evaluated in signal() (FREEOPT-COMPLETE, 2026-10-16), the desk's
exit-evaluation home: the held record's entry premium against the
producer-supplied snapshot quote for the held contract
(context.extra["quotes"]) and the SPY session calendar
(context.extra["session_dates"]); expiry closes the position on
the same rule. An exit fires only with a two-sided quote for the
held contract (the source manage_exits quotes_ok rule). Entries
are deduped per session, the source execute() journal law.
Indicative quotes are not OPRA: freshness is the source's assess()
(90s source / 30s receipt / 2s future tolerance), ported below.

VIRTUAL BOOK MAPPING: Ledger account "free_options" (the FREE_OPTIONS
package pool, BUDGET_USD = 100,000 budget config in aurelia_common);
this sleeve's slice of the pool is its own ledger slice under sleeve
id free_opt_tail. Inputs via context.extra: "quote" (indicative quote
dict for one option symbol), "underlying_return", "market_open".
"""
import math
from datetime import datetime, timedelta, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
SOURCE_MAX_SECONDS = 90
RECEIPT_MAX_SECONDS = 30
FUTURE_TOLERANCE_SECONDS = 2

CONFIG = SleeveConfig(
    sleeve_id="free_opt_tail", cadence_s=300, universe=(),
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
    """Verbatim _fresh_quote from aurelia_free_options."""
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
    """Designed exit (contracts()): five sessions or a 50% premium
    loss; expiry closes the position on the same rule. Fires only
    with a two-sided quote for the held contract (the source
    manage_exits quotes_ok rule: otherwise it is retained)."""
    held = _held(extra)
    if not held:
        return []
    quotes = extra.get("quotes") or {}
    dates = extra.get("session_dates") or []
    out = []
    for sym, pos in sorted(held.items()):
        q = quotes.get(sym)
        # AUDIT3-C (2026-10-16): at/past expiry the two-sided
        # gate must not strand the close (quotes die exactly
        # then); the expiry branch below still fires and the
        # price falls back per side.
        if not _two_sided(q) and not (
                _occ_expiry(sym) is not None
                and session >= _occ_expiry(sym)):
            continue
        entry_date = str(pos.get("entry_date") or "")[:10]
        held_sessions = _sessions_since(dates, entry_date)
        try:
            entry_px = float(pos.get("entry_px"))
        except (TypeError, ValueError):
            entry_px = None
        premium_loss = entry_px is not None and entry_px > 0 \
            and q is not None and q.get("bid") is not None \
            and float(q["bid"]) <= 0.5 * entry_px
        expiry = _occ_expiry(sym)
        if held_sessions >= 5:
            why = "five_sessions"
        elif premium_loss:
            why = "premium_loss_50pct"
        elif expiry is not None and session >= expiry:
            why = "expiry"
        else:
            continue
        qty = float(pos.get("qty") or 0)
        reason = ("free_opt_tail exit: %s entry=%s sessions=%d "
                  "(account=%s)" % (why, entry_date, held_sessions,
                                    ACCOUNT))
        if qty > 0:
            out.append(Intent(
                "exit", sym, qty_hint=int(qty),
                price_hint=(round(float(q["bid"]), 2)
                              if q and q.get("bid") else None),
                side="sell", position_intent="sell_to_close",
                reason=reason))
        elif qty < 0:
            out.append(Intent(
                "exit", sym, qty_hint=int(-qty),
                price_hint=(round(float(q["ask"]), 2)
                              if q and q.get("ask") else None),
                side="buy", position_intent="buy_to_close",
                reason=reason))
    return out


class FreeOptTail(BaseSleeve):
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
        ret = extra.get("underlying_return")
        if ret is None:
            return exits
        try:
            ret_f = float(ret)
        except (TypeError, ValueError):
            return exits
        # Source semantics: fire only when ret <= -0.03. (The port's
        # inverted bail test, `float(ret) > -0.03`, lets NaN through —
        # NaN is not > -0.03 — and emitted an intent on a NaN return.)
        if not math.isfinite(ret_f) or not ret_f <= -0.03:
            return exits
        if "P" not in str(quote.get("symbol") or ""):
            return exits
        try:
            ap = float(quote["ap"])
        except (TypeError, ValueError):
            return exits
        if not math.isfinite(ap) or ap <= 0:
            return exits
        return exits + [Intent(
            "enter", str(quote["symbol"]), qty_hint=1,
            price_hint=round(ap, 2),
            exit_rules=(ExitRule("time_bars", 5),),
            reason="free_opt_tail buy_to_open 1 put: underlying day return "
                   "%.4f <= -3%% (account=%s pool budget=%d)"
                   % (ret_f, ACCOUNT, BUDGET_USD))]


def signal(bars, slice_state, context):
    return FreeOptTail().signal(bars, slice_state, context)
