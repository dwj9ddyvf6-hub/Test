"""The Ausar desk's store and strategy-book mechanics that the vendored TensorRuntime and TensorActions drive,
ported for the two state-repair books: backend/store.py (Store.connect / transaction / settings / event) and the
strategy-owned local-book path of backend/trading.py TradingDesk — claim_strategy_book, strategy_cash (versioned
settlement receipts), _raw_quote, _position, _risk_reducing, _account (split-unit marks, corporate-action totals),
_validate_capacity, _normalize_intent, submit_strategy_intent / _submit_normalized_intent, _terminal, _block,
_window, _service_ids, process (the local quote-based simulation) and _fill — with the source's arithmetic and
statement order: whole-share long-only intents, cash reserved at the quote x (1 + slippage) and capped by the
decision's frozen max debit, fills at the fresh observed quote x (1 +- slippage_bps) inside the order's session
window, integer-cent notional / fees / average cost / realized P&L, and sale proceeds held as a settlement claim
released at the first XNYS open on or after the T+1 maturity (the vendored settlement calendar through r19_ledger,
extended past 2026 by its own rule). providers.exchange_calendar is ported over the XNYS adapter.

Removed (operator / desk-wide controls, not the strategy's rules): the book halt, drawdown brake, symbol and
gross exposure caps (the per-book exposure walk keeps its fresh-quote reads) and the portfolio-wide capacity
check; broker books, protective / OCO orders and external-position locks (a strategy-owned local book has none).
No broker transport exists here: the book is the strategy's own local paper ledger; the desk replicates its
holdings (desk.sleeves.families.tensor_state). tools/parity/tensor_state.py compares it with the source."""
import hashlib
import json
import re
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .ts_source import ACTIVE, NY, DeskError, cents, checked_cents, symbol

UTC = timezone.utc
TERMINAL = {"filled", "cancelled", "expired", "rejected"}
DEFAULTS = {"quote_max_age_seconds": 300, "heartbeat_seconds": 2, "cycle_interval_seconds": 60}
# backend/trading.py POLICY as tensor_cli set it (set_book stores numbers as floats: number())
POLICY = {"halted": False, "halt_reason": None, "allow_short": False,
          "gross_exposure_cap": None, "symbol_exposure_cap": None,
          "drawdown_alert_percent": None, "drawdown_brake_percent": None,
          "fees_per_order": 0.0, "slippage_bps": 10.0, "max_fill_quantity": None}
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS watchlist(symbol TEXT PRIMARY KEY,added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS quotes(symbol TEXT PRIMARY KEY,price TEXT NOT NULL,as_of TEXT NOT NULL,source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,actor TEXT NOT NULL,timestamp TEXT NOT NULL,message TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS p_books(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,broker TEXT NOT NULL,description TEXT,cash_cents INTEGER NOT NULL DEFAULT 0,realized_cents INTEGER NOT NULL DEFAULT 0,fees_cents INTEGER NOT NULL DEFAULT 0,peak_equity_cents INTEGER NOT NULL DEFAULT 0,policy TEXT NOT NULL,policy_version INTEGER NOT NULL,policy_hash TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS p_fundings(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,client_id TEXT NOT NULL,amount_cents INTEGER NOT NULL,timestamp TEXT NOT NULL,UNIQUE(book_id,client_id));
CREATE TABLE IF NOT EXISTS p_positions(book_id TEXT NOT NULL,symbol TEXT NOT NULL,quantity TEXT NOT NULL,cost_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL DEFAULT 0,sleeve TEXT,source TEXT NOT NULL,locked INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,PRIMARY KEY(book_id,symbol));
CREATE TABLE IF NOT EXISTS p_intents(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,client_id TEXT NOT NULL,payload_hash TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,order_type TEXT NOT NULL,time_in_force TEXT NOT NULL,limit_price TEXT,stop_price TEXT,not_before TEXT,expires_at TEXT,reason TEXT,sleeve TEXT,take_profit TEXT,stop_loss TEXT,max_fill_quantity TEXT,status TEXT NOT NULL,filled_quantity TEXT NOT NULL DEFAULT '0',filled_notional_cents INTEGER NOT NULL DEFAULT 0,fees_cents INTEGER NOT NULL DEFAULT 0,reserved_cents INTEGER NOT NULL DEFAULT 0,reserved_quantity TEXT NOT NULL DEFAULT '0',triggered INTEGER NOT NULL DEFAULT 0,parent_id TEXT,oco_group TEXT,broker_id TEXT,broker_client_id TEXT NOT NULL UNIQUE,broker_status TEXT,submitted_at TEXT,completed_at TEXT,session_date TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,error TEXT,source TEXT NOT NULL DEFAULT 'operator',policy_version INTEGER NOT NULL,session_open TEXT,session_close TEXT,UNIQUE(book_id,client_id));
CREATE TABLE IF NOT EXISTS p_fills(id TEXT PRIMARY KEY,intent_id TEXT NOT NULL,book_id TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,notional_cents INTEGER NOT NULL,fee_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL,fill_key TEXT NOT NULL UNIQUE,timestamp TEXT,observed_at TEXT NOT NULL,source TEXT NOT NULL,quote_as_of TEXT,quote_source TEXT,policy_version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS p_state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS a_strategy_ownership(book_id TEXT PRIMARY KEY REFERENCES p_books(id),installation_id TEXT NOT NULL UNIQUE,claimed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS a_strategy_settlements(fill_id TEXT PRIMARY KEY REFERENCES p_fills(id),book_id TEXT NOT NULL REFERENCES p_books(id),amount_cents INTEGER NOT NULL CHECK(amount_cents>0),release_at TEXT NOT NULL,created_at TEXT NOT NULL,released_at TEXT);
CREATE TABLE IF NOT EXISTS a_strategy_settlement_policy_receipts(fill_id TEXT PRIMARY KEY REFERENCES a_strategy_settlements(fill_id),policy_version TEXT NOT NULL,definition TEXT NOT NULL,definition_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS a_strategy_intent_limits(intent_id TEXT PRIMARY KEY REFERENCES p_intents(id),installation_id TEXT NOT NULL,max_debit_cents INTEGER NOT NULL CHECK(max_debit_cents>0),reference_price TEXT NOT NULL,quote_as_of TEXT NOT NULL,created_at TEXT NOT NULL);
"""


def now():
    return datetime.now(UTC).isoformat()


def identifier():
    return uuid.uuid4().hex


def number(value):
    return float(Decimal(str(value)))


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def decimal(value, name, positive=True, max_places=6):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise DeskError(f"{name} must be a finite number", 422) from None
    if not result.is_finite() or (positive and result <= 0) or abs(result) > Decimal("1000000000") or result.as_tuple().exponent < -max_places:
        raise DeskError(f"{name} must be finite, positive and at most {max_places} decimal places", 422)
    return result


def timestamp(value, name):
    if value is None:
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()
        return parsed.astimezone(UTC).isoformat()
    except (ValueError, TypeError):
        raise DeskError(f"{name} must be a timezone-aware ISO timestamp", 422) from None


def clock_time(clock):
    if clock is None:
        return datetime.now(UTC)
    return datetime.fromisoformat(timestamp(clock, "clock"))


def exchange_calendar(clock=None):
    """backend/providers.py exchange_calendar over the XNYS adapter (desk.feedlib.r19_source.DeskXNYS)."""
    from .r19_source import DeskXNYS
    from .ts_source import utc_clock
    clock = utc_clock(clock)
    cal = DeskXNYS()
    day = clock.astimezone(NY).date()
    valid = cal.is_session(day)
    previous = cal.previous_session(day) if valid else cal.date_to_session(day, direction="previous")
    following = cal.next_session(day) if valid else cal.date_to_session(day, direction="next")
    opened = cal.session_open(day).to_pydatetime() if valid else None
    closed = cal.session_close(day).to_pydatetime() if valid else None
    upcoming = day if valid and clock < opened else following
    upcoming_close = day if valid and clock < closed else following
    iso = lambda value: value.isoformat() if value is not None else None  # noqa: E731
    return {
        "exchange": "XNYS", "timezone": "America/New_York", "timestamp": clock.isoformat(),
        "date": str(day), "is_session": bool(valid), "is_open": bool(valid and opened <= clock < closed),
        "session_date": str(day) if valid else None, "open_at": iso(opened), "close_at": iso(closed),
        "previous_session": str(previous.date()), "next_session": str(following.date()),
        "previous_open_at": iso(cal.session_open(previous).to_pydatetime()),
        "previous_close_at": iso(cal.session_close(previous).to_pydatetime()),
        "next_open_at": iso(cal.session_open(upcoming).to_pydatetime()),
        "next_close_at": iso(cal.session_close(upcoming_close).to_pydatetime()),
        "early_close": bool(valid and closed.astimezone(NY).hour < 16),
        "source": "exchange_calendars XNYS",
    }


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, *exc):
        try:
            return super().__exit__(*exc)
        finally:
            self.close()


class Store:
    """backend/store.py's connection discipline: per-use connections, Row factory, BEGIN IMMEDIATE writers."""

    def __init__(self, path):
        from .ts_source import install_shims
        install_shims()
        from ..vendor.ausar_ts.backend.tensor_actions import initialize_action_tables
        self.path = path
        with self.connect() as con:
            con.executescript(SCHEMA)
            initialize_action_tables(con)
            for key, value in DEFAULTS.items():
                con.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (key, json.dumps(value)))

    def connect(self):
        con = sqlite3.connect(self.path, timeout=15, factory=_ClosingConnection, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA busy_timeout=15000")
        con.execute("PRAGMA journal_mode=WAL")
        return con

    @contextmanager
    def transaction(self):
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def settings(con):
        return {r["key"]: json.loads(r["value"]) for r in con.execute("SELECT * FROM settings")}

    @staticmethod
    def event(con, kind, actor, message, payload=None):
        con.execute("INSERT INTO events(event_type,actor,timestamp,message,payload) VALUES(?,?,?,?,?)",
                    (kind, actor, now(), message, json.dumps(payload or {}, default=str)))


class TradingBridge:
    """the strategy-owned local-book subset of backend/trading.py TradingDesk."""

    def __init__(self, store, calendar=exchange_calendar):
        self.store, self.calendar = store, calendar
        self._lock = threading.RLock()

    # -- books (tensor_cli install_all: create_book, set_book policy, fund_book 100,000) ---------------------
    def create_book(self, name, capital_cents, client_id=None):
        with self.store.transaction() as con:
            row = con.execute("SELECT id FROM p_books WHERE name=?", (name,)).fetchone()
            rid = row["id"] if row else identifier()
            if not row:
                serialized, ts = dump(POLICY), now()
                con.execute("INSERT INTO p_books(id,name,kind,broker,description,cash_cents,realized_cents,fees_cents,peak_equity_cents,policy,policy_version,policy_hash,created_at,updated_at) VALUES(?,?,?,?,?,0,0,0,0,?,?,?,?,?)",
                            (rid, name, "forward", "local", "R12 frozen independent strategy; virtual paper capital only",
                             serialized, 1, hashlib.sha256(serialized.encode()).hexdigest(), ts, ts))
            client = client_id or "r12-opening-capital-" + name
            if not con.execute("SELECT 1 FROM p_fundings WHERE book_id=? AND client_id=?", (rid, client)).fetchone():
                con.execute("INSERT INTO p_fundings VALUES(?,?,?,?,?)", (identifier(), rid, client, capital_cents, now()))
                con.execute("UPDATE p_books SET cash_cents=cash_cents+?,peak_equity_cents=MAX(peak_equity_cents,cash_cents+?),updated_at=? WHERE id=?",
                            (capital_cents, capital_cents, now(), rid))
            return rid

    @staticmethod
    def _book(con, book_id):
        book = con.execute("SELECT * FROM p_books WHERE id=?", (book_id,)).fetchone()
        if not book:
            raise DeskError("Independent paper book not found", 404)
        return book

    @staticmethod
    def _strategy_owner(con, book_id):
        return con.execute("SELECT * FROM a_strategy_ownership WHERE book_id=?", (book_id,)).fetchone()

    def claim_strategy_book(self, book_id, installation_id, con=None):
        if not isinstance(installation_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", installation_id):
            raise DeskError("A bounded strategy installation identity is required", 422)
        if con is None:
            with self.store.transaction() as writer:
                return self.claim_strategy_book(book_id, installation_id, con=writer)
        if not con.in_transaction:
            raise DeskError("Strategy ownership requires an existing writer transaction")
        book = self._book(con, book_id)
        if book["broker"] != "local":
            raise DeskError("Strategy ownership supports dedicated local paper books only")
        previous = self._strategy_owner(con, book_id)
        if previous:
            if previous["installation_id"] != installation_id:
                raise DeskError("This paper book is already owned by another strategy installation")
            return dict(previous)
        if con.execute("SELECT 1 FROM a_strategy_ownership WHERE installation_id=?", (installation_id,)).fetchone():
            raise DeskError("A strategy installation may own only one paper book")
        held = any(Decimal(row["quantity"]) != 0 for row in con.execute("SELECT quantity FROM p_positions WHERE book_id=?", (book_id,)))
        traded = con.execute("SELECT 1 FROM p_fills WHERE book_id=? LIMIT 1", (book_id,)).fetchone()
        pending = con.execute("SELECT 1 FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested') LIMIT 1", (book_id,)).fetchone()
        if held or traded or pending:
            raise DeskError("A strategy requires an empty book with no holdings, fills or active orders")
        ts = now()
        con.execute("INSERT INTO a_strategy_ownership VALUES(?,?,?)", (book_id, installation_id, ts))
        self.store.event(con, "strategy_book_claimed", "strategy", "Bound a dedicated local paper book to an installed strategy", {"book_id": book_id, "installation_id": installation_id})
        return {"book_id": book_id, "installation_id": installation_id, "claimed_at": ts}

    # -- settlement ----------------------------------------------------------------------------------------
    @staticmethod
    def _strategy_settlement_terms(clock):
        from .r19_ledger import settlement_terms
        try:
            return settlement_terms(clock)
        except Exception:
            raise DeskError("Covered regular-way settlement calendar unavailable; no local strategy fill committed") from None

    @staticmethod
    def _strategy_settlement_release_at(clock):
        return TradingBridge._strategy_settlement_terms(clock)["cash_release_at"]

    def _settlement_boundaries(self, con, row):
        """every sale here carries a versioned receipt (no pre-rollout legacy fills exist in these books)."""
        observed = clock_time(row["fill_observed_at"])
        terms = self._strategy_settlement_terms(observed)
        receipt = con.execute("SELECT * FROM a_strategy_settlement_policy_receipts WHERE fill_id=?", (row["fill_id"],)).fetchone()
        if not receipt or receipt["policy_version"] != terms["policy_version"] or hashlib.sha256(receipt["definition"].encode()).hexdigest() != receipt["definition_sha256"] or receipt["definition"] != dump(terms) or receipt["created_at"] != row["created_at"] or row["release_at"] != terms["cash_release_at"]:
            raise DeskError("Settlement policy receipt is unknown or differs from independent calendar replay")
        return terms["cash_release_at"], None

    def strategy_cash(self, con, book_id, clock=None, release=True):
        clock = clock_time(clock)
        book = self._book(con, book_id)
        owned = self._strategy_owner(con, book_id)
        unsettled, due = 0, []
        if owned:
            if release and not con.in_transaction:
                raise DeskError("Settlement release requires an existing writer transaction")
            rows = con.execute("SELECT s.*,f.observed_at AS fill_observed_at,f.rowid AS fill_append_rowid FROM a_strategy_settlements s JOIN p_fills f ON f.id=s.fill_id WHERE s.book_id=?", (book_id,)).fetchall()
            for row in rows:
                boundary, _ = self._settlement_boundaries(con, row)
                if clock < clock_time(boundary):
                    unsettled += row["amount_cents"]
                elif row["released_at"] is None:
                    due.append(row["fill_id"])
            if release:
                for fill_id in due:
                    con.execute("UPDATE a_strategy_settlements SET released_at=? WHERE fill_id=? AND released_at IS NULL", (clock.isoformat(), fill_id))
        reserved = con.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book_id,)).fetchone()[0]
        settled = checked_cents(book["cash_cents"] - unsettled, "Settled strategy cash")
        return {"cash_cents": book["cash_cents"], "unsettled_cents": unsettled, "settled_cents": settled, "reserved_cents": reserved, "available_cents": checked_cents(settled - reserved, "Available strategy cash")}

    # -- quotes, positions, account ------------------------------------------------------------------------
    def _raw_quote(self, con, sym, clock, require_fresh=True):
        quote = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
        if not quote:
            raise DeskError("A timestamped price is required for order validation")
        age = (clock - datetime.fromisoformat(quote["as_of"])).total_seconds()
        max_age = self.store.settings(con)["quote_max_age_seconds"]
        if require_fresh and not 0 <= age <= max_age:
            raise DeskError("A fresh timestamped intraday quote is required")
        if require_fresh and any(word in quote["source"].lower() for word in ("historical", "daily bar", "daily close")):
            raise DeskError("Historical daily bars cannot authorize intraday fills")
        return quote

    @staticmethod
    def _position(con, book_id, sym):
        return con.execute("SELECT * FROM p_positions WHERE book_id=? AND symbol=?", (book_id, sym)).fetchone()

    @staticmethod
    def _risk_reducing(qty, side, order_qty):
        return (qty > 0 and side == "sell" or qty < 0 and side == "buy") and order_qty <= abs(qty)

    def _account(self, con, book, clock):
        from ..vendor.ausar_ts.backend.tensor_actions import action_totals, split_mark_price
        value, pnl, missing, gross, stale = 0, 0, 0, 0, 0
        strategy_owned = self._strategy_owner(con, book["id"])
        positions = []
        for row in con.execute("SELECT * FROM p_positions WHERE book_id=? ORDER BY symbol", (book["id"],)):
            qty = Decimal(row["quantity"])
            if qty == 0:
                continue
            quote = con.execute("SELECT * FROM quotes WHERE symbol=?", (row["symbol"],)).fetchone()
            fresh = False
            if quote:
                price = split_mark_price(con, book["id"], row["symbol"], quote["price"], quote["as_of"]) if strategy_owned else Decimal(quote["price"])
                marked = cents(qty * price)
                delta = marked - row["cost_cents"]
                age = (clock - datetime.fromisoformat(quote["as_of"])).total_seconds()
                fresh = 0 <= age <= self.store.settings(con)["quote_max_age_seconds"]
            else:
                price, marked, delta = None, 0, 0
                missing += 1
            stale += int(not fresh)
            value += marked
            pnl += delta
            gross += abs(marked)
            positions.append({"book_id": book["id"], "symbol": row["symbol"], "quantity": number(qty), "cost_basis": row["cost_cents"] / 100,
                              "mark_price": number(price) if price is not None else None, "market_value": marked / 100,
                              "unrealized_pnl": delta / 100, "realized_pnl": row["realized_cents"] / 100, "quote_fresh": fresh})
        reserved = con.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book["id"],)).fetchone()[0]
        action_values = action_totals(con, book["id"], clock, self.store.settings(con)["quote_max_age_seconds"]) if strategy_owned else None
        if action_values:
            value += action_values["fractional_market_cents"]
            gross += abs(action_values["fractional_market_cents"])
            missing += action_values["missing_marks"]
            stale += action_values["stale_marks"]
        equity = book["cash_cents"] + value + (action_values["receivable_cents"] if action_values else 0)
        account = {"currency": "USD", "cash": book["cash_cents"] / 100, "equity": equity / 100, "market_value": value / 100,
                   "gross_exposure": gross / 100, "reserved_cash": reserved / 100, "available_cash": (book["cash_cents"] - reserved) / 100,
                   "realized_pnl": book["realized_cents"] / 100, "unrealized_pnl": pnl / 100, "fees": book["fees_cents"] / 100,
                   "missing_marks": missing, "stale_marks": stale}
        if strategy_owned:
            cash = self.strategy_cash(con, book["id"], clock, release=False)
            account.update(unsettled_cash=cash["unsettled_cents"] / 100, settled_cash=cash["settled_cents"] / 100,
                           available_cash=cash["available_cents"] / 100,
                           dividend_receivable=action_values["receivable_cents"] / 100,
                           fractional_claim_market_value=action_values["fractional_market_cents"] / 100,
                           corporate_action_coverage=action_values["coverage"],
                           exact_market_value_cents=value, exact_equity_cents=equity)
        return account, positions

    # -- orders ----------------------------------------------------------------------------------------------
    def _validate_capacity(self, con, book, data, price, exclude=None, clock=None):
        from ..vendor.ausar_ts.backend.tensor_actions import action_coverage
        clock = clock or datetime.now(UTC)
        pos = self._position(con, book["id"], data["symbol"])
        qty = Decimal(pos["quantity"]) if pos else Decimal(0)
        order_qty = Decimal(data["quantity"]) - Decimal(data.get("filled_quantity", "0"))
        reducing = self._risk_reducing(qty, data["side"], order_qty)
        account, positions = self._account(con, book, clock)
        remaining_signed = order_qty if data["side"] == "buy" else -order_qty
        projected = qty + remaining_signed
        owner = self._strategy_owner(con, book["id"])
        if owner:
            coverage = action_coverage(con, book["id"], clock, data["symbol"])
            if coverage["target_blocked"]:
                raise DeskError("Corporate action units or current action coverage are unverified for this symbol")
            if coverage["entry_blocked"] and not reducing:
                raise DeskError("Corporate action review or fractional cash-in-lieu prevents new strategy entries")
            changed = con.execute("SELECT MAX(effective_at) FROM a_strategy_actions WHERE book_id=? AND symbol=? AND kind='split' AND applied_at IS NOT NULL", (book["id"], data["symbol"])).fetchone()[0]
            source_quote = con.execute("SELECT as_of FROM quotes WHERE symbol=?", (data["symbol"],)).fetchone()
            if changed and (not source_quote or source_quote["as_of"] < changed):
                raise DeskError("The execution quote predates the observed share split")
        if owner and projected < 0:
            raise DeskError("Strategy-owned local paper books are long-only")
        active = list(con.execute("SELECT * FROM p_intents WHERE book_id=? AND id!=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book["id"], exclude or "")))
        shares = Decimal(0)
        for intent in active:
            if intent["symbol"] != data["symbol"] or intent["side"] != data["side"]:
                continue
            shares += Decimal(intent["reserved_quantity"])
        if data["side"] == "sell" and qty > 0 and min(order_qty, qty) + shares > qty:
            raise DeskError("Insufficient unreserved shares in this independent book")
        reservation_price = price
        if data["side"] == "buy":
            bound = data.get("limit_price") or data.get("stop_price")
            reservation_price = max(price, Decimal(bound)) if bound else price
        estimated = checked_cents(cents(order_qty * reservation_price), "Reserved order notional")
        fee = cents(Decimal(str(json.loads(book["policy"])["fees_per_order"]))) if Decimal(data.get("filled_quantity", "0")) == 0 else 0
        other_cash = sum(r["reserved_cents"] for r in active)
        spending_cash = self.strategy_cash(con, book["id"], clock)["settled_cents"] if owner else book["cash_cents"]
        if data["side"] == "buy" and not (reducing and qty < 0) and spending_cash - other_cash < estimated + fee:
            raise DeskError("Insufficient unreserved settled cash in this strategy book" if owner else "Insufficient unreserved cash in this independent book")
        if not reducing:
            # the source's per-book exposure walk (its caps are operator gates, removed); its marks must be fresh
            symbols = {p["symbol"] for p in positions} | {p["symbol"] for p in active if not p["parent_id"]} | {data["symbol"]}
            for sym in symbols:
                self._raw_quote(con, sym, clock)
        reserve_cash = estimated + fee if data["side"] == "buy" and not (reducing and qty < 0) else 0
        closing_direction = qty > 0 and data["side"] == "sell" or qty < 0 and data["side"] == "buy"
        reserve_qty = min(order_qty, abs(qty)) if closing_direction else Decimal(0)
        return reserve_cash, reserve_qty

    def _normalize_intent(self, payload):
        allowed = {"book_id", "symbol", "side", "quantity", "order_type", "time_in_force", "client_id", "limit_price", "stop_price", "not_before", "expires_at", "reason", "sleeve", "take_profit", "stop_loss", "max_fill_quantity"}
        if set(payload) - allowed:
            raise DeskError("Unknown intent fields", 422)
        data = {"book_id": payload.get("book_id", "main"), "symbol": symbol(str(payload.get("symbol", ""))), "side": payload.get("side"), "quantity": str(decimal(payload.get("quantity"), "quantity")), "order_type": payload.get("order_type", "market"), "time_in_force": payload.get("time_in_force", "day"), "client_id": payload.get("client_id")}
        if not isinstance(data["side"], str) or data["side"] not in {"buy", "sell"} or not isinstance(data["order_type"], str) or data["order_type"] not in {"market", "limit", "stop", "stop_limit"} or not isinstance(data["time_in_force"], str) or data["time_in_force"] not in {"day", "gtc", "opg", "cls"}:
            raise DeskError("Unsupported side, order type or time in force", 422)
        if not isinstance(data["client_id"], str) or not 1 <= len(data["client_id"].strip()) <= 100 or not isinstance(data["book_id"], str):
            raise DeskError("book_id and client_id must be bounded strings", 422)
        for key in ("limit_price", "stop_price", "take_profit", "stop_loss", "max_fill_quantity"):
            value = payload.get(key)
            if isinstance(value, dict):
                raise DeskError("Protective orders are not part of a strategy-owned local book", 422)
            data[key] = str(decimal(value, key)) if value is not None else None
        data["not_before"] = timestamp(payload.get("not_before"), "not_before")
        data["expires_at"] = timestamp(payload.get("expires_at"), "expires_at")
        for key, limit in (("reason", 2000), ("sleeve", 100)):
            value = payload.get(key)
            if value is not None and (not isinstance(value, str) or len(value) > limit):
                raise DeskError(key + " is too long", 422)
            data[key] = value
        if data["order_type"] in {"limit", "stop_limit"} and not data["limit_price"] or data["order_type"] in {"stop", "stop_limit"} and not data["stop_price"]:
            raise DeskError("Order type requires its explicit limit/stop price", 422)
        if data["order_type"] not in {"limit", "stop_limit"} and data["limit_price"] is not None or data["order_type"] not in {"stop", "stop_limit"} and data["stop_price"] is not None:
            raise DeskError("Limit/stop fields do not match this order type", 422)
        if data["time_in_force"] in {"opg", "cls"} and data["order_type"] not in {"market", "limit"}:
            raise DeskError("Auction orders support only market or limit mechanics", 422)
        if data["not_before"] and data["expires_at"] and data["not_before"] >= data["expires_at"]:
            raise DeskError("expires_at must follow not_before", 422)
        return data

    def submit_strategy_intent(self, payload, installation_id, transaction_guard=None, con=None, clock=None):
        if not isinstance(installation_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", installation_id):
            raise DeskError("A bounded strategy installation identity is required", 422)
        supplied = dict(payload)
        max_debit_cents = supplied.pop("max_debit_cents", None)
        if max_debit_cents is not None and (type(max_debit_cents) is not int or not 1 <= max_debit_cents <= 9_000_000_000_000_000_000):
            raise DeskError("Strategy max_debit_cents must be a positive bounded integer", 422)
        data = self._normalize_intent(supplied)
        if con is None:
            with self.store.transaction() as writer:
                return self._submit_normalized_intent(writer, data, installation_id, transaction_guard, clock, max_debit_cents)
        if not con.in_transaction:
            raise DeskError("Strategy submission requires an existing writer transaction")
        return self._submit_normalized_intent(con, data, installation_id, transaction_guard, clock, max_debit_cents)

    def _submit_normalized_intent(self, con, data, installation_id, transaction_guard=None, clock=None, max_debit_cents=None):
        if transaction_guard is not None:
            transaction_guard(con)
        clock = clock_time(clock)
        book = self._book(con, data["book_id"])
        owner = self._strategy_owner(con, book["id"])
        if not owner or owner["installation_id"] != installation_id or book["broker"] != "local":
            raise DeskError("Strategy installation does not own this local paper book")
        quantity = Decimal(data["quantity"])
        if quantity != quantity.to_integral_value():
            raise DeskError("Strategy-owned paper intents require whole shares", 422)
        fill_cap = data.get("max_fill_quantity") or json.loads(book["policy"])["max_fill_quantity"]
        if fill_cap is not None and Decimal(str(fill_cap)) != Decimal(str(fill_cap)).to_integral_value():
            raise DeskError("Strategy-owned partial fill limits require whole shares", 422)
        identity = {**data, "strategy_max_debit_cents": max_debit_cents} if max_debit_cents is not None else data
        digest = hashlib.sha256(dump(identity).encode()).hexdigest()
        existing = con.execute("SELECT * FROM p_intents WHERE book_id=? AND client_id=?", (book["id"], data["client_id"])).fetchone()
        if existing:
            if existing["payload_hash"] != digest or existing["source"] != "strategy":
                raise DeskError("client_id already identifies a different autonomous intent")
            return dict(existing)
        position = self._position(con, book["id"], data["symbol"])
        held = Decimal(position["quantity"]) if position else Decimal(0)
        if data["side"] == "sell" and not self._risk_reducing(held, "sell", quantity):
            raise DeskError("A strategy-owned book permits sales of existing unreserved long shares only")
        quote = self._raw_quote(con, data["symbol"], clock)
        reference = Decimal(data["limit_price"] or quote["price"])
        notional_cents = cents(quantity * reference)
        if not 1 <= notional_cents <= 9_000_000_000_000_000_000:
            raise DeskError("Intent notional must be at least one cent and fit the integer-cents ledger", 422)
        reservation_reference = reference
        if data["side"] == "buy":
            slip = Decimal(str(json.loads(book["policy"])["slippage_bps"])) / 10000
            reservation_reference = max(reference, Decimal(quote["price"]) * (1 + slip))
        reserve_cash, reserve_qty = self._validate_capacity(con, book, data, reservation_reference, clock=clock)
        if data["side"] == "buy":
            max_debit_cents = reserve_cash if max_debit_cents is None else max_debit_cents
            if reserve_cash > max_debit_cents:
                raise DeskError("Strategy quote debit exceeds the frozen entry budget")
        rid, ts = identifier(), clock.isoformat()
        columns = list(data) + ["id", "payload_hash", "status", "reserved_cents", "reserved_quantity", "broker_client_id", "created_at", "updated_at", "policy_version", "source"]
        values = list(data.values()) + [rid, digest, "queued", reserve_cash, str(reserve_qty), "aster_" + rid, ts, ts, book["policy_version"], "strategy"]
        con.execute(f"INSERT INTO p_intents({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", values)
        if data["side"] == "buy":
            con.execute("INSERT INTO a_strategy_intent_limits VALUES(?,?,?,?,?,?)", (rid, installation_id, max_debit_cents, str(reservation_reference), quote["as_of"], ts))
        con.execute("INSERT OR IGNORE INTO watchlist VALUES(?,?)", (data["symbol"], ts))
        provenance = {"intent_id": rid, "book_id": book["id"], "client_id": data["client_id"], "policy_version": book["policy_version"],
                      "execution": "installed strategy decision; automatic local paper order mechanics", "installation_id": installation_id}
        if data["side"] == "buy":
            provenance["max_debit_cents"] = max_debit_cents
        self.store.event(con, "strategy_intent_authorized", "strategy", f"Installed strategy authorized {data['side']} {data['quantity']} {data['symbol']} in {book['name']}", provenance)
        return dict(con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone())

    def _terminal(self, con, intent, status, reason, clock):
        con.execute("UPDATE p_intents SET status=?,error=?,reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=? WHERE id=?", (status, reason, clock.isoformat(), clock.isoformat(), intent["id"]))
        self.store.event(con, "autonomous_order_" + status, "execution_clerk", reason, {"intent_id": intent["id"], "book_id": intent["book_id"]})

    def _block(self, con, intent, reason, clock):
        state = intent["status"] if intent["status"] in {"submitting", "cancel_requested"} else "blocked"
        if intent["error"] != reason or intent["status"] != state:
            con.execute("UPDATE p_intents SET status=?,error=?,updated_at=? WHERE id=?", (state, reason, clock.isoformat(), intent["id"]))
            self.store.event(con, "autonomous_order_blocked", "risk_officer", reason, {"intent_id": intent["id"], "book_id": intent["book_id"]})

    def _window(self, con, intent, calendar, clock, initial_calendar=None):
        if intent["expires_at"] and clock >= datetime.fromisoformat(intent["expires_at"]):
            self._terminal(con, intent, "expired", "Explicit expiry reached", clock)
            return False
        if intent["not_before"] and clock < datetime.fromisoformat(intent["not_before"]):
            return False
        tif = intent["time_in_force"]
        if tif == "gtc":
            return bool(calendar.get("is_open"))
        target_open, target_close = intent["session_open"], intent["session_close"]
        if target_close is None:
            original_session = initial_calendar or calendar
            opened = timestamp(original_session.get("open_at") or original_session.get("next_open_at"), "calendar open")
            closed = timestamp(original_session.get("close_at") or original_session.get("next_close_at"), "calendar close")
            if not opened or not closed:
                raise DeskError("Exchange session boundaries are unavailable")
            target_open, target_close = opened, closed
            created = datetime.fromisoformat(intent["not_before"] or intent["created_at"])
            if created > datetime.fromisoformat(closed):
                target_open = timestamp(original_session.get("next_open_at"), "next session open")
                target_close = timestamp(original_session.get("next_close_at"), "next session close")
                if not target_open or not target_close:
                    raise DeskError("Next exchange session is unavailable")
            session_date = datetime.fromisoformat(target_open).date().isoformat()
            con.execute("UPDATE p_intents SET session_open=?,session_close=?,session_date=? WHERE id=?", (target_open, target_close, session_date, intent["id"]))
        session_open, session_close = datetime.fromisoformat(target_open), datetime.fromisoformat(target_close)
        if tif == "opg":
            end = session_open + timedelta(seconds=60)
            if clock > end:
                self._terminal(con, intent, "expired", "Opening auction window missed; no fallback or late replay", clock)
                return False
            return session_open <= clock <= end
        if clock > session_close:
            self._terminal(con, intent, "expired", "Session window closed; no late replay", clock)
            return False
        if tif == "cls":
            return session_close - timedelta(seconds=60) <= clock <= session_close
        return session_open <= clock <= session_close and bool(calendar.get("is_open"))

    def _service_ids(self):
        buckets = [[] for _ in range(4)]
        with self.store.transaction() as con:
            for row in con.execute("SELECT i.*,p.quantity AS held_quantity FROM p_intents i LEFT JOIN p_positions p ON p.book_id=i.book_id AND p.symbol=i.symbol WHERE i.status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested') ORDER BY i.created_at,i.id"):
                remaining = Decimal(row["quantity"]) - Decimal(row["filled_quantity"])
                held = Decimal(row["held_quantity"] or "0")
                bucket = 0 if row["status"] == "cancel_requested" else 1 if row["parent_id"] else 2 if self._risk_reducing(held, row["side"], remaining) else 3
                buckets[bucket].append(row["id"])
            for index, bucket in enumerate(buckets):
                prior = con.execute("SELECT value FROM p_state WHERE key=?", ("service_cursor:" + str(index),)).fetchone()
                if prior and prior[0] in bucket:
                    offset = bucket.index(prior[0]) + 1
                    buckets[index] = bucket[offset:] + bucket[:offset]
            selected = [[] for _ in buckets]
            for index, allowance in enumerate((50, 100, 25, 25)):
                selected[index] = buckets[index][:allowance]
                buckets[index] = buckets[index][allowance:]
            budget = 200 - sum(map(len, selected))
            for index, bucket in enumerate(buckets):
                extra = bucket[:budget]
                selected[index].extend(extra)
                budget -= len(extra)
            for index, bucket in enumerate(selected):
                if bucket:
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("service_cursor:" + str(index), bucket[-1]))
            return [rid for bucket in selected for rid in bucket]

    def process(self, clock=None):
        """backend/trading.py process(): the local quote-based simulation of each active strategy intent
        (clock None: the production per-intent clock and its pre-fill window / quote re-check)."""
        dynamic_clock = clock is None
        clock = clock_time(clock)
        result = {"processed": 0, "fills": 0, "submitted": 0, "errors": []}
        try:
            calendar = self.calendar(clock)
        except Exception:
            result["errors"].append("Exchange calendar unavailable; execution deferred")
            calendar = None
        for rid in self._service_ids():
            if dynamic_clock:
                clock = clock_time(None)
                try:
                    calendar = self.calendar(clock)
                except Exception:
                    calendar = None
            with self.store.transaction() as con:
                intent = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                if not intent or intent["status"] not in ACTIVE:
                    continue
                book = self._book(con, intent["book_id"])
                try:
                    if calendar is None:
                        raise DeskError("Exchange calendar unavailable; no new local fill authorized")
                    original_calendar = self.calendar(datetime.fromisoformat(intent["not_before"] or intent["created_at"])) if intent["session_close"] is None and intent["time_in_force"] != "gtc" else None
                    if not self._window(con, intent, calendar, clock, initial_calendar=original_calendar):
                        continue
                    quote = self._raw_quote(con, intent["symbol"], clock)
                    quote_time = datetime.fromisoformat(quote["as_of"])
                    if calendar.get("open_at") and quote_time < datetime.fromisoformat(timestamp(calendar["open_at"], "calendar open")):
                        raise DeskError("Quote predates the exchange session; no auction or daily-close replay")
                    if intent["time_in_force"] == "cls" and quote_time < datetime.fromisoformat(timestamp(calendar["close_at"], "calendar close")) - timedelta(seconds=60):
                        raise DeskError("Closing simulation needs a quote from its documented final-minute window")
                    policy = json.loads(book["policy"])
                    observed = Decimal(quote["price"])
                    if intent["order_type"] in {"stop", "stop_limit"}:
                        threshold = Decimal(intent["stop_price"])
                        triggered = intent["triggered"] or (observed >= threshold if intent["side"] == "buy" else observed <= threshold)
                        if not triggered:
                            continue
                        con.execute("UPDATE p_intents SET triggered=1 WHERE id=?", (rid,))
                    slip = Decimal(str(policy["slippage_bps"])) / 10000
                    price = observed * (1 + slip if intent["side"] == "buy" else 1 - slip)
                    if intent["order_type"] in {"limit", "stop_limit"}:
                        limit = Decimal(intent["limit_price"])
                        if intent["side"] == "buy" and price > limit or intent["side"] == "sell" and price < limit:
                            continue
                    remaining = Decimal(intent["quantity"]) - Decimal(intent["filled_quantity"])
                    self._validate_capacity(con, book, dict(intent), price, rid, clock)
                    max_fill = intent["max_fill_quantity"] or policy["max_fill_quantity"]
                    quantity = min(remaining, Decimal(str(max_fill))) if max_fill else remaining
                    fee = cents(Decimal(str(policy["fees_per_order"]))) if Decimal(intent["filled_quantity"]) == 0 else 0
                    notional = cents(quantity * price)
                    if notional < 1:
                        raise DeskError("Fill notional is below one cent")
                    fill_key = rid + ":local:" + str(Decimal(intent["filled_quantity"]) + quantity)
                    if dynamic_clock:
                        clock = clock_time(None)
                        calendar = self.calendar(clock)
                        if not self._window(con, intent, calendar, clock, initial_calendar=original_calendar):
                            continue
                        self._raw_quote(con, intent["symbol"], clock)
                    con.execute("SAVEPOINT local_fill")
                    try:
                        filled = self._fill(con, intent, quantity, notional, price, fee, clock, fill_key, "local quote-based simulation", quote=quote)
                    except BaseException:
                        con.execute("ROLLBACK TO local_fill")
                        raise
                    finally:
                        con.execute("RELEASE local_fill")
                    result["fills"] += int(filled)
                    result["processed"] += 1
                except DeskError as exc:
                    self._block(con, intent, exc.detail, clock)
                    result["errors"].append({"intent_id": rid, "detail": exc.detail})
        return result

    def _fill(self, con, intent, quantity, notional, price, fee, clock, fill_key, source, source_timestamp=None, quote=None):
        if con.execute("SELECT 1 FROM p_fills WHERE fill_key=?", (fill_key,)).fetchone():
            return False
        book = self._book(con, intent["book_id"])
        strategy_owner = self._strategy_owner(con, book["id"])
        if strategy_owner and (book["broker"] != "local" or quantity != quantity.to_integral_value()):
            raise DeskError("Strategy-owned paper fills require whole-share local execution")
        if strategy_owner and intent["side"] == "buy":
            limit = con.execute("SELECT * FROM a_strategy_intent_limits WHERE intent_id=?", (intent["id"],)).fetchone()
            if not limit or limit["installation_id"] != strategy_owner["installation_id"]:
                raise DeskError("Strategy entry has no matching durable debit budget; no fill committed")
            cumulative_debit = checked_cents(intent["filled_notional_cents"] + intent["fees_cents"] + notional + fee, "Cumulative strategy entry debit")
            if cumulative_debit > limit["max_debit_cents"]:
                raise DeskError("Actual quote fill would exceed the frozen cumulative strategy debit budget")
        pos = self._position(con, book["id"], intent["symbol"])
        old_qty = Decimal(pos["quantity"]) if pos else Decimal(0)
        old_cost, old_realized = (pos["cost_cents"], pos["realized_cents"]) if pos else (0, 0)
        delta = quantity if intent["side"] == "buy" else -quantity
        realized = 0
        if old_qty == 0 or old_qty * delta >= 0:
            new_cost = old_cost + (notional if delta > 0 else -notional)
        else:
            closing = min(abs(old_qty), quantity)
            basis_abs = abs(old_cost) if closing == abs(old_qty) else int((Decimal(abs(old_cost)) * closing / abs(old_qty)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            closing_notional = notional if closing == quantity else int((Decimal(notional) * closing / quantity).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            realized = closing_notional - basis_abs if old_qty > 0 else basis_abs - closing_notional
            signed_basis = basis_abs if old_qty > 0 else -basis_abs
            opening_notional = notional - closing_notional
            new_cost = old_cost - signed_basis + (opening_notional if delta > 0 else -opening_notional)
        new_qty = old_qty + delta
        if new_qty == 0:
            new_cost = 0
        sleeve = intent["sleeve"] if not pos or old_qty == 0 else pos["sleeve"] if pos["sleeve"] == intent["sleeve"] else None
        cash_delta = -notional if intent["side"] == "buy" else notional
        cash = checked_cents(book["cash_cents"] + cash_delta - fee, "Resulting cash")
        realized_total = checked_cents(book["realized_cents"] + realized, "Realized P&L")
        fees_total = checked_cents(book["fees_cents"] + fee, "Total fees")
        checked_cents(new_cost, "Position cost basis")
        checked_cents(old_realized + realized, "Position realized P&L")
        checked_cents(intent["filled_notional_cents"] + notional, "Cumulative fill notional")
        checked_cents(intent["fees_cents"] + fee, "Order fees")
        remaining = max(Decimal(intent["quantity"]) - Decimal(intent["filled_quantity"]) - quantity, Decimal(0))
        settlement_amount = max(notional - fee, 0) if strategy_owner and intent["side"] == "sell" else 0
        settlement_release = self._strategy_settlement_release_at(clock) if settlement_amount else None
        settlement_terms = self._strategy_settlement_terms(clock) if settlement_amount else None
        if settlement_terms and settlement_terms["cash_release_at"] != settlement_release:
            raise DeskError("Settlement release and policy terms disagree before fill commit")
        bound = intent["limit_price"] or intent["stop_price"]
        reservation_price = max(price, Decimal(bound)) if bound else price
        if intent["side"] == "buy":
            checked_cents(cents(remaining * reservation_price), "Remaining cash reservation")
        observed = con.execute("SELECT price FROM quotes WHERE symbol=?", (intent["symbol"],)).fetchone()
        mark = cents(new_qty * Decimal(observed[0])) if observed else 0
        market_value = sum((cents(Decimal(row["quantity"]) * Decimal(row["price"])) for row in con.execute("SELECT p.quantity,q.price FROM p_positions p JOIN quotes q ON p.symbol=q.symbol WHERE p.book_id=? AND p.symbol!=?", (book["id"], intent["symbol"]))), mark)
        checked_cents(market_value, "Resulting market value")
        checked_cents(cash + market_value, "Resulting equity")
        con.execute("UPDATE p_books SET cash_cents=?,realized_cents=?,fees_cents=?,updated_at=? WHERE id=?", (cash, realized_total, fees_total, clock.isoformat(), book["id"]))
        con.execute("INSERT OR REPLACE INTO p_positions VALUES(?,?,?,?,?,?,?,?,?)", (book["id"], intent["symbol"], str(new_qty), new_cost, old_realized + realized, sleeve, "local_simulation", 0, clock.isoformat()))
        fid = identifier()
        con.execute("INSERT INTO p_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (fid, intent["id"], book["id"], intent["symbol"], intent["side"], str(quantity), str(price), notional, fee, realized, fill_key, source_timestamp or clock.isoformat(), clock.isoformat(), source, quote["as_of"] if quote else None, quote["source"] if quote else None, book["policy_version"]))
        if settlement_amount:
            con.execute("INSERT INTO a_strategy_settlements VALUES(?,?,?,?,?,NULL)", (fid, book["id"], settlement_amount, settlement_release, clock.isoformat()))
            definition = dump(settlement_terms)
            con.execute("INSERT INTO a_strategy_settlement_policy_receipts VALUES(?,?,?,?,?)", (fid, settlement_terms["policy_version"], definition, hashlib.sha256(definition.encode()).hexdigest(), clock.isoformat()))
        filled = Decimal(intent["filled_quantity"]) + quantity
        remaining = Decimal(intent["quantity"]) - filled
        status = "filled" if remaining <= 0 else "partially_filled"
        remaining_is_short_cover = new_qty < 0 and self._risk_reducing(new_qty, intent["side"], remaining)
        reserve_cash = cents(remaining * reservation_price) if intent["side"] == "buy" and not remaining_is_short_cover else 0
        closing_direction = new_qty > 0 and intent["side"] == "sell" or new_qty < 0 and intent["side"] == "buy"
        reserve_qty = min(remaining, abs(new_qty)) if closing_direction else Decimal(0)
        completed = clock.isoformat() if status == "filled" else intent["completed_at"] if intent["status"] in TERMINAL else None
        con.execute("UPDATE p_intents SET filled_quantity=?,filled_notional_cents=filled_notional_cents+?,fees_cents=fees_cents+?,status=?,reserved_cents=?,reserved_quantity=?,completed_at=?,updated_at=?,error=NULL WHERE id=?", (str(filled), notional, fee, status, reserve_cash, str(reserve_qty), completed, clock.isoformat(), intent["id"]))
        self.store.event(con, "autonomous_paper_fill", "execution_clerk", f"{source}: {intent['side']} {quantity} {intent['symbol']}",
                         {"intent_id": intent["id"], "book_id": book["id"], "fill_id": fid, "quantity": number(quantity), "price": number(price),
                          "notional": notional / 100, "fee": fee / 100, "realized_pnl": realized / 100, "observed_at": clock.isoformat(),
                          "quote_as_of": quote["as_of"] if quote else None, "sale_cash_release_at": settlement_release, "settlement_terms": settlement_terms})
        return True

    # -- the desk's view ------------------------------------------------------------------------------------
    def holdings(self, book_id):
        with self.store.connect() as con:
            return {r["symbol"]: Decimal(r["quantity"]) for r in con.execute("SELECT symbol,quantity FROM p_positions WHERE book_id=?", (book_id,)) if Decimal(r["quantity"]) != 0}

    def summary(self, book_id, clock):
        clock = datetime.fromtimestamp(float(clock), UTC) if isinstance(clock, (int, float)) else clock_time(clock)
        with self.store.connect() as con:
            book = self._book(con, book_id)
            account, positions = self._account(con, book, clock)
            fills = con.execute("SELECT COUNT(*) FROM p_fills WHERE book_id=?", (book_id,)).fetchone()[0]
            active = con.execute("SELECT COUNT(*) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book_id,)).fetchone()[0]
        return {"equity": account["equity"], "cash": account["cash"], "settled_cash": account["settled_cash"],
                "positions": len(positions), "fills": fills, "active_intents": active,
                "missing_marks": account["missing_marks"], "stale_marks": account["stale_marks"]}
