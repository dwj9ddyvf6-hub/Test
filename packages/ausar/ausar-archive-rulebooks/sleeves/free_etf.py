"""FREE_ETF — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from the old desk's aurelia_free_etf.py (decide/targets_for/
schedule/window) + aurelia_common quote-freshness (assess/quote_block).
Signal: prior completed SIP daily bars, adjustment=all (the receipt).
Execution quote: a separate IEX quote. Entry clock 09:35-09:40 ET only;
exits are NOT limited to the entry window. Session notional cap $25,000
on a $100,000 book; per-book slice = min(budget / n_books, $10,000).

VIRTUAL BOOK MAPPING: Ledger account "free_etf", budget config
BUDGET_USD = 100,000 (aurelia_common.BUDGETS["FREE_ETF"]), day cap
$25,000 as sleeve config. QQQ is never ordered: existing broker QQQ
shares are ATTRIBUTED to this book — in core terms a Risk.Slices
attribution (grant = min(desired, broker_qty - others_attributed)),
emitted as an enter intent whose reason marks it slice-only (named
misfit in the port report). TQQQ/GLD are refused (Aurelia owns them).

Inputs via context.extra:
  "etf_books": [book dicts {id, fixed_weights?|symbols, policy}] (the old
     desk's rulebook file is absent on Femto too — no books, no intents)
  "etf_receipt": {"histories": {sym: [{session, close}...]},
     "source_receipts_verified": bool, "feed": "sip", "adjustment": "all",
     "signal_session": "YYYY-MM-DD"}
  "quotes": {sym: {"t","received_at","bp","ap"}} (IEX)
  "held_rows": {row_id: qty}  (per-book holdings, producer-supplied
     from the dispatch records — AUDIT-20261018-CURE13: there is NO
     slice_state fallback; the aggregate per-symbol qty must never be
     read as one book's ownership. When held_rows is absent entirely,
     a nonzero aggregate for a symbol is UNATTRIBUTED and that symbol
     fails closed for every book; an aggregate of zero is owned zero.)
  "spent_usd": session buys so far (day-cap accounting)
  "broker_qqq_qty": float, "attributed_others": float (QQQ grant math)
Bars argument is unused: the SIP receipt carries the signal history,
exactly as the old decide() read histories from the receipt.
"""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
BUDGET_USD = 100_000.0
DAY_CAP_USD = 25_000.0
ACCOUNT = "free_etf"
AURELIA_EQUITY = {"QQQ", "TQQQ", "GLD"}
ETF_SOURCE_MAX_SECONDS = 2
RECEIPT_MAX_SECONDS = 30
FUTURE_TOLERANCE_SECONDS = 2

CONFIG = SleeveConfig(
    sleeve_id="free_etf", cadence_s=60, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


# --- aurelia_common quote freshness, verbatim semantics ------------------
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


def quote_block(moment, source_at, received_at, *, source_max=ETF_SOURCE_MAX_SECONDS,
                receipt_max=RECEIPT_MAX_SECONDS):
    from datetime import timedelta
    if not source_at or not received_at:
        return "source time or receipt time is missing"
    source = parse_time(source_at)
    received = parse_time(received_at)
    if source > moment + timedelta(seconds=FUTURE_TOLERANCE_SECONDS):
        return "source timestamp is beyond the 2-second clock tolerance"
    if received > moment + timedelta(seconds=FUTURE_TOLERANCE_SECONDS):
        return "receipt timestamp is beyond the 2-second clock tolerance"
    if (moment - source).total_seconds() > source_max:
        return f"source age exceeds {source_max:g} seconds"
    if (moment - received).total_seconds() > receipt_max:
        return f"receipt age exceeds {receipt_max:g} seconds"
    if received < source:
        return "receipt is earlier than the source timestamp"
    return None


def assess(moment, source_at, received_at, *, source_max=ETF_SOURCE_MAX_SECONDS):
    return {"source_at": source_at, "received_at": received_at,
            "decision_at": moment.isoformat(),
            "block": quote_block(moment, source_at, received_at, source_max=source_max)}


def etf_window(moment):
    """Verbatim: 09:35-09:40 America/New_York."""
    local = moment.astimezone(ET)
    start = local.replace(hour=9, minute=35, second=0, microsecond=0)
    end = local.replace(hour=9, minute=40, second=0, microsecond=0)
    if local < start:
        return "before"
    if local >= end:
        return "after"
    return "open"


# --- aurelia_free_etf pure logic, verbatim in substance ------------------
def score_map(histories, symbols):
    scores = {}
    for symbol in symbols:
        rows = histories.get(symbol) or []
        if len(rows) < 252:
            return None, f"{symbol} has {len(rows)} SIP sessions; 252 are required"
        closes = [float(row["close"]) for row in rows[-252:]]
        if any(close <= 0 for close in closes):
            return None, f"{symbol} has a nonpositive SIP close"
        scores[symbol] = math.log(closes[-1] / closes[-127])
    return scores, None


def _select_backend(policy, own, other=None, incumbent=None):
    """Verbatim backend.r19_etf.select (Ausar archive, recovered
    2026-10-15 from Agentic-Trading-Desk@aurelia-paper-desk,
    ausar-archive/.../backend/r19_etf.py): deterministic original
    126-session selection and strict provider intervals."""
    if policy == 'EXSMH1':
        own = {s: v for s, v in own.items() if s != 'SMH'}
    if not own:
        raise ValueError('NO_ELIGIBLE_SCORE')
    if not policy.startswith('INTERVAL'):
        return min(own, key=lambda s: (-own[s], s)), {'ambiguous': False, 'scores': own}
    if other is None or set(other) != set(own) or 'QQQ' not in own:
        raise ValueError('PROVIDER_ELIGIBILITY_DISAGREEMENT')
    bounds = {s: [min(own[s], other[s]), max(own[s], other[s])] for s in sorted(own)}
    highest_low = max(v[0] for v in bounds.values())
    possible = [s for s, v in bounds.items() if v[1] >= highest_low]
    robust = [s for s, v in bounds.items() if all(v[0] > w[1] for t, w in bounds.items() if s != t)]
    choice = robust[0] if len(robust) == 1 else incumbent if incumbent in possible else 'QQQ'
    return choice, {'ambiguous': len(robust) != 1, 'bounds': bounds, 'possible_leaders': possible, 'robust_leader': robust[0] if len(robust) == 1 else None}


def targets_for(book, histories, other_scores=None):
    """Fixed-weight books resolve here. Selection books use the
    recovered r19_etf.select backend verbatim (EA2a, 2026-10-15):
    the rulebook (config/aurelia_free_etf_rules.json, the source's
    strategies/r19/etf_rules.json) is the books' selection source.
    Books with a secondary_provider need the YAHOO secondary scores
    (extra["etf_secondary_scores"]); absent them they fail closed,
    exactly as the source did when its YAHOO cache was missing."""
    if book.get("fixed_weights"):
        return {"weights": {s: float(w) for s, w in book["fixed_weights"].items()},
                "signal_present": True, "selected": None}
    symbols = list(book.get("symbols") or [])
    if book.get("policy") == "EXSMH1":
        symbols = [s for s in symbols if s != "SMH"]
    scores, problem = score_map(histories, symbols)
    if problem:
        return {"weights": {}, "signal_present": False, "selected": None}
    other = None
    if book.get("secondary_provider"):
        if not other_scores:
            return {"weights": {}, "signal_present": False, "selected": None}
        other = {s: float(other_scores[s]) for s in symbols if s in other_scores}
    try:
        selected, _detail = _select_backend(book["policy"], scores, other)
    except (ValueError, KeyError, TypeError) as exc:
        return {"weights": {}, "signal_present": False, "selected": None,
                "reason": str(exc)}
    if book["policy"].endswith("CORE25"):
        weights = {selected: 0.25}
        weights["QQQ"] = weights.get("QQQ", 0.0) + 0.75
        return {"weights": weights, "signal_present": True, "selected": selected}
    return {"weights": {selected: 1.0}, "signal_present": True, "selected": selected}


def initial_sessions(origin):
    from datetime import timedelta
    days = []
    cursor = origin
    while len(days) < 5:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def month_sessions(first):
    from datetime import timedelta
    days = []
    cursor = first
    while len(days) < 5:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


INITIAL_ORIGIN = None  # set below (date(2026,10,13) — first initial day)


def schedule_open_for(book, session, signal_session):
    from datetime import date as _date
    if book.get("fixed_weights"):
        return session in initial_sessions(INITIAL_ORIGIN)
    if not signal_session:
        return False
    signal = _date.fromisoformat(signal_session)
    nxt = _date(signal.year + (signal.month == 12),
                1 if signal.month == 12 else signal.month + 1, 1)
    return session in month_sessions(nxt)


from datetime import date as _d
INITIAL_ORIGIN = _d(2026, 10, 13)


def qqq_grant(desired, broker_qty, others_attributed):
    """virtual_attribute grant math, verbatim: room = broker - others."""
    desired = max(0.0, float(desired))
    room = max(0.0, float(broker_qty) - max(0.0, float(others_attributed)))
    return int(min(desired, room))


class FreeEtf(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        books = list(extra.get("etf_books") or [])
        receipt = extra.get("etf_receipt") or {}
        histories = receipt.get("histories") or {}
        verified = bool(receipt.get("source_receipts_verified")
                        and receipt.get("feed") == "sip"
                        and receipt.get("adjustment") == "all")
        signal_session = receipt.get("signal_session")
        moment = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        phase = etf_window(moment)
        session = moment.astimezone(ET).date()
        quotes = extra.get("quotes") or {}
        # CURE13: held_rows is per-book truth when the key is present
        # (an absent row held nothing). When the key is absent the
        # producer could not supply it — ownership is then known only
        # where the aggregate slice_state is zero.
        held_supplied = "held_rows" in extra
        held_rows = extra.get("held_rows") or {}
        used = float(extra.get("spent_usd") or 0.0)
        slice_usd = min(BUDGET_USD / max(len(books), 1), 10_000.0)
        intents = []

        def _owned(book_id, symbol):
            """One book's owned qty for one symbol, or None when it
            cannot be attributed (CURE13): held_rows is authoritative
            when supplied; without it, only an aggregate of zero is
            attributable (to every book, as zero) — a nonzero
            aggregate belongs to SOME book(s), never to EACH book."""
            row_id = f"FREE_ETF_{book_id}_{symbol}"
            if held_supplied:
                try:
                    return float(held_rows.get(row_id, 0) or 0)
                except (TypeError, ValueError):
                    return 0.0
            if row_id in held_rows:
                try:
                    return float(held_rows.get(row_id, 0) or 0)
                except (TypeError, ValueError):
                    return 0.0
            try:
                aggregate = float((slice_state or {}).get(symbol, 0) or 0)
            except (TypeError, ValueError):
                aggregate = 0.0
            return 0.0 if aggregate == 0 else None

        def _exit_candidates(book_id, enrolled):
            """Held rows for one book: ONLY the held_rows entries
            minted for it (CURE13 — the old slice_state fallback
            synthesized a candidate for every enrolled symbol at the
            full sleeve-aggregate qty, so every book holding the
            symbol was told it held the whole position)."""
            prefix = f"FREE_ETF_{book_id}_"
            found = {}
            for row_id, qty in held_rows.items():
                if isinstance(row_id, str) and row_id.startswith(prefix):
                    symbol = row_id[len(prefix):]
                    if symbol:
                        try:
                            found[symbol] = (float(qty or 0), row_id)
                        except (TypeError, ValueError):
                            continue
            return found

        def _deselected_exits(candidates, in_plan):
            """Trim-to-zero exits for held symbols absent from the plan.

            AUDIT-20261018-CURE12 (rotation/deselection orphans): a held
            symbol the current plan no longer weights has no other exit
            route — no ExitRule, no resting order. Exits are
            window-exempt in this sleeve (the after-window path below),
            so these fire in the open and after phases, never before
            the window, and only on a fresh quote with a positive bid,
            exactly as the after-window exit requires. Symbols in
            AURELIA_EQUITY are never ordered here: QQQ is virtual
            attribution only and TQQQ/GLD are Aurelia's (refused)."""
            out = []
            if phase == "before":
                return out
            for symbol, (owned, row_id) in sorted(candidates.items()):
                if symbol in in_plan or symbol in AURELIA_EQUITY:
                    continue
                if owned <= 0:
                    continue
                quote = quotes.get(symbol) or {}
                try:
                    checked = assess(moment, quote.get("t"),
                                     quote.get("received_at"))
                except (TypeError, ValueError):
                    checked = {"block": "unparseable quote timestamps"}
                bid, ask = quote.get("bp"), quote.get("ap")
                if checked["block"] or not bid or not ask:
                    continue
                try:
                    bid_f, ask_f = float(bid), float(ask)
                except (TypeError, ValueError):
                    continue
                if bid_f <= 0 or ask_f <= 0:
                    continue
                out.append(Intent(
                    "exit", symbol, qty_hint=int(owned),
                    price_hint=round(bid_f, 2),
                    reason="free_etf exit (deselected: not in current plan; "
                           "trim-to-zero) row=%s account=%s DAY limit at bid"
                           % (row_id, ACCOUNT)))
            return out

        if not books:
            # No plan at all: every held row is deselected.
            generic = {}
            for row_id, qty in held_rows.items():
                if (isinstance(row_id, str)
                        and row_id.startswith("FREE_ETF_")
                        and "_" in row_id[len("FREE_ETF_"):]):
                    try:
                        generic[row_id.rsplit("_", 1)[-1]] = (
                            float(qty or 0), row_id)
                    except (TypeError, ValueError):
                        continue
            return _deselected_exits(generic, set())
        for book in books:
            plan = targets_for(book, histories,
                               other_scores=extra.get("etf_secondary_scores"))
            enrolled = list(book.get("fixed_weights") or book.get("symbols") or [])
            qualified = verified and all(
                s in histories and len(histories[s]) >= 252 for s in enrolled)
            if not plan["weights"] or not qualified:
                # Held rows are evaluated BEFORE the plan gates: an
                # empty/failed or unqualified plan deselects everything
                # the book holds (CURE12) — it must not orphan them.
                intents.extend(_deselected_exits(
                    _exit_candidates(book["id"], enrolled), set()))
                continue
            intents.extend(_deselected_exits(
                _exit_candidates(book["id"], enrolled),
                set(plan["weights"])))
            sched = schedule_open_for(book, session, signal_session)
            for symbol, weight in plan["weights"].items():
                row_id = f"FREE_ETF_{book['id']}_{symbol}"
                quote = quotes.get(symbol) or {}
                if symbol in AURELIA_EQUITY and symbol != "QQQ":
                    continue  # refused: Aurelia owns it (old desk: BLOCKED_INPUT)
                # Quote freshness (assess/quote_block) applies to EVERY
                # quote this sleeve consumes, QQQ attribution included:
                # the grant is sized on the ask, so a stale/crossed or
                # unparseable quote must fail closed here exactly as it
                # does on the order path below (audit 2026-10-15 P3:
                # pre-fix a 2h-old QQQ quote still granted shares).
                try:
                    checked = assess(moment, quote.get("t"),
                                     quote.get("received_at"))
                except (TypeError, ValueError):
                    checked = {"block": "unparseable quote timestamps"}
                if symbol == "QQQ":
                    try:
                        bid_q = float(quote.get("bp") or 0)
                        ask = float(quote.get("ap") or 0)
                    except (TypeError, ValueError):
                        bid_q, ask = 0.0, 0.0
                    desired = int(slice_usd * weight / ask) if ask > 0 and weight else 0
                    grant = qqq_grant(desired, float(extra.get("broker_qqq_qty") or 0),
                                      float(extra.get("attributed_others") or 0))
                    if checked["block"] or bid_q <= 0 or bid_q > ask:
                        grant = 0
                    if phase == "open" and sched and grant > 0:
                        intents.append(Intent(
                            "enter", "QQQ", qty_hint=grant,
                            price_hint=round(ask, 2) if ask else None,
                            reason="free_etf VIRTUAL_ATTRIBUTION slice-only "
                                   "(account=%s row=%s desired=%d; no broker order)"
                                   % (ACCOUNT, row_id, desired)))
                    continue
                bid, ask = quote.get("bp"), quote.get("ap")
                owned = _owned(book["id"], symbol)
                if owned is None:
                    # Unattributed aggregate: this book's ownership of
                    # the symbol is unknown — fail closed for it
                    # (no entry sized on a guess, no exit of shares
                    # that may be another book's). CURE13.
                    continue
                if phase == "after" and owned > 0:
                    # exits are not limited to the entry window
                    if bid and ask and float(bid) > 0 and not checked["block"]:
                        target = int(slice_usd * weight / float(ask)) if float(ask) > 0 else 0
                        if owned > target:
                            intents.append(Intent(
                                "exit", symbol, qty_hint=int(owned - target),
                                price_hint=round(float(bid), 2),
                                reason="free_etf exit (window-exempt) row=%s "
                                       "account=%s DAY limit at bid" % (row_id, ACCOUNT)))
                    continue
                if phase != "open" or not sched:
                    continue
                if not bid or not ask or float(ask) <= 0 or float(bid) > float(ask):
                    continue
                if checked["block"]:
                    continue
                spread = (float(ask) - float(bid)) / float(ask) * 10000
                if spread > 20:
                    continue
                qty = int(slice_usd * weight / float(ask))
                if owned < qty:
                    if qty - owned < 1 or used + (qty - owned) * float(ask) > DAY_CAP_USD:
                        continue
                    used += (qty - owned) * float(ask)
                    intents.append(Intent(
                        "enter", symbol, qty_hint=int(qty - owned),
                        price_hint=round(float(ask), 2),
                        reason="free_etf entry row=%s account=%s DAY limit at ask "
                               "spread_bps=%.1f" % (row_id, ACCOUNT, spread)))
                elif owned > qty:
                    intents.append(Intent(
                        "exit", symbol, qty_hint=int(owned - qty),
                        price_hint=round(float(bid), 2),
                        reason="free_etf exit row=%s account=%s DAY limit at bid"
                               % (row_id, ACCOUNT)))
        return intents


def signal(bars, slice_state, context):
    return FreeEtf().signal(bars, slice_state, context)
