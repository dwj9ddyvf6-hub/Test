"""FREE_OPT_PAIR — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py evaluate(): both exposures of a
cross-underlying pair, only after a hedge ratio frozen from prior
closes (package["hedge_frozen"] true, package["hedge"] present).
A failed leg closes the filled leg (the desk's package path is
atomic — no leg ever fills alone, a stronger form of the rule).
Exit: ten sessions (ExitRule time_bars=10 per leg), evaluated in
signal() (FREEOPT-COMPLETE, 2026-10-16) from the served position
records plus the producer's exit inputs (context.extra["quotes"],
context.extra["session_dates"]); ten sessions or expiry closes
the package together, only with two-sided quotes for both legs
(the source manage_exits quotes_ok rule). Entries are deduped per
session, the source execute() journal law.

VIRTUAL BOOK MAPPING: Ledger account "free_options" (pool $100,000).
Inputs via context.extra: "quote" (freshness gate), "package":
{"legs": [2 legs with distinct "underlying"], "hedge": {...},
"hedge_frozen": bool}.
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
    sleeve_id="free_opt_pair", cadence_s=300, universe=(),
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


def pair_legs(package):
    """Verbatim entry condition: 2 legs, 2 underlyings, hedge frozen."""
    if not package:
        return None
    legs = package.get("legs") or []
    underlyings = {leg.get("underlying") for leg in legs}
    if len(legs) == 2 and len(underlyings) == 2 and package.get("hedge_frozen") \
            and package.get("hedge"):
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
    """Designed exit (contracts()): ten sessions; a failed leg
    closes the filled leg — the package exits together, and only
    with a two-sided quote for every leg (the source manage_exits
    quotes_ok rule: otherwise the position is retained). Expiry
    closes the package on the same rule as the family's other
    straddle book."""
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
            reason = ("free_opt_pair exit: %s entry=%s sessions=%d "
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


def _leg_price(leg):
    """A leg's tradable price (its ask): finite and > 0, else None.
    A zero/missing/unparseable ask is a dead quote for that leg —
    the package must not be emitted on it (cf. the ask=0 wedge)."""
    try:
        p = float(leg.get("ask") or leg.get("ap") or 0)
    except (TypeError, ValueError):
        return None
    return p if math.isfinite(p) and p > 0 else None


class FreeOptPair(BaseSleeve):
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
        legs = pair_legs(extra.get("package"))
        if not legs:
            return exits
        prices = [_leg_price(leg) for leg in legs]
        if any(not leg.get("symbol") or p is None
               for leg, p in zip(legs, prices)):
            return exits
        out = []
        for leg, price in zip(legs, prices):
            # XT-8 (2026-10-16): pass a package leg's declared
            # direction through to the intent. The ported leg shape
            # carries no direction (the source's _send_mleg carried an
            # explicit per-leg "side"); a package leg that DOES declare
            # one (side / position_intent in the producer's package)
            # must not be flattened to dispatch's default buy_to_open.
            # Undeclared legs keep the historical shape exactly.
            side = leg.get("side") if leg.get("side") in ("buy", "sell") \
                else None
            pi = leg.get("position_intent") if leg.get(
                "position_intent") in ("buy_to_open", "sell_to_open") \
                else None
            if side and pi and (side == "buy") != (pi == "buy_to_open"):
                return []  # contradictory declaration: fail closed
            out.append(Intent(
                "enter", str(leg["symbol"]), qty_hint=1,
                price_hint=round(price, 2),
                exit_rules=(ExitRule("time_bars", 10),),
                side=side, position_intent=pi,
                reason="free_opt_pair package FREE_OPT_PAIR_V1 leg underlying=%s "
                       "hedge frozen from prior closes (account=%s)"
                       % (leg.get("underlying"), ACCOUNT)))
        return exits + out


def signal(bars, slice_state, context):
    return FreeOptPair().signal(bars, slice_state, context)
