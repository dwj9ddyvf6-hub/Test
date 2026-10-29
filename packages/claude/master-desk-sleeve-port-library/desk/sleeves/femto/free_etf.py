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
  "held_rows": {row_id: qty}  (fallback: slice_state per symbol)
  "spent_usd": session buys so far (day-cap accounting)
  "broker_qqq_qty": float, "attributed_others": float (QQQ grant math)
Bars argument is unused: the SIP receipt carries the signal history,
exactly as the old decide() read histories from the receipt.
"""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig

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


def targets_for(book, histories):
    """Fixed-weight books resolve here. Selection books hit the same
    fence the old desk had: the selection backend lives in the excluded
    Ausar archive (Decision #119) — no weights, no intent."""
    if book.get("fixed_weights"):
        return {"weights": {s: float(w) for s, w in book["fixed_weights"].items()},
                "signal_present": True, "selected": None}
    symbols = list(book.get("symbols") or [])
    if book.get("policy") == "EXSMH1":
        symbols = [s for s in symbols if s != "SMH"]
    scores, problem = score_map(histories, symbols)
    if problem:
        return {"weights": {}, "signal_present": False, "selected": None}
    if book.get("secondary_provider"):
        return {"weights": {}, "signal_present": False, "selected": None}
    return {"weights": {}, "signal_present": False, "selected": None}


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
        if not books:
            return []
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
        held_rows = extra.get("held_rows") or {}
        used = float(extra.get("spent_usd") or 0.0)
        slice_usd = min(BUDGET_USD / max(len(books), 1), 10_000.0)
        intents = []
        for book in books:
            plan = targets_for(book, histories)
            if not plan["weights"]:
                continue
            enrolled = list(book.get("fixed_weights") or book.get("symbols") or [])
            qualified = verified and all(
                s in histories and len(histories[s]) >= 252 for s in enrolled)
            if not qualified:
                continue
            sched = schedule_open_for(book, session, signal_session)
            for symbol, weight in plan["weights"].items():
                row_id = f"FREE_ETF_{book['id']}_{symbol}"
                quote = quotes.get(symbol) or {}
                if symbol in AURELIA_EQUITY and symbol != "QQQ":
                    continue  # refused: Aurelia owns it (old desk: BLOCKED_INPUT)
                if symbol == "QQQ":
                    ask = float(quote.get("ap") or 0)
                    desired = int(slice_usd * weight / ask) if ask > 0 and weight else 0
                    grant = qqq_grant(desired, float(extra.get("broker_qqq_qty") or 0),
                                      float(extra.get("attributed_others") or 0))
                    if phase == "open" and sched and grant > 0:
                        intents.append(Intent(
                            "enter", "QQQ", qty_hint=grant,
                            price_hint=round(ask, 2) if ask else None,
                            reason="free_etf VIRTUAL_ATTRIBUTION slice-only "
                                   "(account=%s row=%s desired=%d; no broker order)"
                                   % (ACCOUNT, row_id, desired)))
                    continue
                checked = assess(moment, quote.get("t"), quote.get("received_at"))
                bid, ask = quote.get("bp"), quote.get("ap")
                owned = float(held_rows.get(row_id, (slice_state or {}).get(symbol, 0)) or 0)
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
