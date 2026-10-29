"""Independent paper books and durable authorized order mechanics.

Local fills simulate an observed quote, never an exchange. Connected books mirror
Alpaca PAPER truth and cumulative fills; they never borrow local simulation state.
Installed strategies may own dedicated local books through the guarded internal
submission boundary. Models, lab studies and inbox messages have no such write
interface. Unowned books retain their operator-controlled behavior.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .store import DeskError, Store, cents, checked_cents, identifier, now, number, symbol
from .tensor_actions import initialize_action_tables, action_totals, action_coverage, split_mark_price, apply_replayed_split, owned_quantity_at


UTC = timezone.utc
ACTIVE = {"queued", "open", "partially_filled", "blocked", "submitting", "cancel_requested"}
TERMINAL = {"filled", "cancelled", "expired", "rejected"}
POLICY = {"halted": False, "halt_reason": None, "allow_short": False,
          "gross_exposure_cap": None, "symbol_exposure_cap": None,
          "drawdown_alert_percent": None, "drawdown_brake_percent": None,
          "fees_per_order": 0, "slippage_bps": 0, "max_fill_quantity": None}
PORTFOLIO_POLICY = {"gross_exposure_cap": None, "symbol_exposure_cap": None}


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


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class TradingDesk:
    def __init__(self, store: Store):
        self.store = store
        with store.transaction() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS p_books(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,broker TEXT NOT NULL,description TEXT,cash_cents INTEGER NOT NULL DEFAULT 0,realized_cents INTEGER NOT NULL DEFAULT 0,fees_cents INTEGER NOT NULL DEFAULT 0,peak_equity_cents INTEGER NOT NULL DEFAULT 0,policy TEXT NOT NULL,policy_version INTEGER NOT NULL,policy_hash TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS p_policy_history(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,version INTEGER NOT NULL,hash TEXT NOT NULL,policy TEXT NOT NULL,actor TEXT NOT NULL,timestamp TEXT NOT NULL,UNIQUE(book_id,version));
                CREATE TABLE IF NOT EXISTS p_portfolio_policy_history(id TEXT PRIMARY KEY,version INTEGER NOT NULL UNIQUE,hash TEXT NOT NULL,policy TEXT NOT NULL,actor TEXT NOT NULL,timestamp TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS p_fundings(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,client_id TEXT NOT NULL,amount_cents INTEGER NOT NULL,timestamp TEXT NOT NULL,UNIQUE(book_id,client_id));
                CREATE TABLE IF NOT EXISTS p_positions(book_id TEXT NOT NULL,symbol TEXT NOT NULL,quantity TEXT NOT NULL,cost_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL DEFAULT 0,sleeve TEXT,source TEXT NOT NULL,locked INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,PRIMARY KEY(book_id,symbol));
                CREATE TABLE IF NOT EXISTS p_intents(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,client_id TEXT NOT NULL,payload_hash TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,order_type TEXT NOT NULL,time_in_force TEXT NOT NULL,limit_price TEXT,stop_price TEXT,not_before TEXT,expires_at TEXT,reason TEXT,sleeve TEXT,take_profit TEXT,stop_loss TEXT,max_fill_quantity TEXT,status TEXT NOT NULL,filled_quantity TEXT NOT NULL DEFAULT '0',filled_notional_cents INTEGER NOT NULL DEFAULT 0,fees_cents INTEGER NOT NULL DEFAULT 0,reserved_cents INTEGER NOT NULL DEFAULT 0,reserved_quantity TEXT NOT NULL DEFAULT '0',triggered INTEGER NOT NULL DEFAULT 0,parent_id TEXT,oco_group TEXT,broker_id TEXT,broker_client_id TEXT NOT NULL UNIQUE,broker_status TEXT,submitted_at TEXT,completed_at TEXT,session_date TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,error TEXT,source TEXT NOT NULL DEFAULT 'operator',policy_version INTEGER NOT NULL,UNIQUE(book_id,client_id));
                CREATE TABLE IF NOT EXISTS p_fills(id TEXT PRIMARY KEY,intent_id TEXT NOT NULL,book_id TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,notional_cents INTEGER NOT NULL,fee_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL,fill_key TEXT NOT NULL UNIQUE,timestamp TEXT,observed_at TEXT NOT NULL,source TEXT NOT NULL,quote_as_of TEXT,quote_source TEXT,policy_version INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS p_equity(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,timestamp TEXT NOT NULL,cash_cents INTEGER NOT NULL,equity_cents INTEGER NOT NULL,market_value_cents INTEGER NOT NULL,missing_marks INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS p_reconciliations(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,timestamp TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS p_broker_truth(book_id TEXT PRIMARY KEY,account TEXT NOT NULL,positions TEXT NOT NULL,orders TEXT NOT NULL,observed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS p_state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_strategy_ownership(book_id TEXT PRIMARY KEY REFERENCES p_books(id),installation_id TEXT NOT NULL UNIQUE,claimed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_strategy_settlements(fill_id TEXT PRIMARY KEY REFERENCES p_fills(id),book_id TEXT NOT NULL REFERENCES p_books(id),amount_cents INTEGER NOT NULL CHECK(amount_cents>0),release_at TEXT NOT NULL,created_at TEXT NOT NULL,released_at TEXT);
                CREATE INDEX IF NOT EXISTS a_strategy_settlements_due ON a_strategy_settlements(book_id,release_at) WHERE released_at IS NULL;
                CREATE TABLE IF NOT EXISTS a_strategy_settlement_policy_receipts(fill_id TEXT PRIMARY KEY REFERENCES a_strategy_settlements(fill_id),policy_version TEXT NOT NULL,definition TEXT NOT NULL,definition_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_strategy_settlement_legacy_reviews(fill_id TEXT PRIMARY KEY REFERENCES a_strategy_settlements(fill_id),definition TEXT NOT NULL,definition_sha256 TEXT NOT NULL,reviewed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_strategy_settlement_rollout(id INTEGER PRIMARY KEY CHECK(id=1),definition TEXT NOT NULL,definition_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_strategy_intent_limits(intent_id TEXT PRIMARY KEY REFERENCES p_intents(id),installation_id TEXT NOT NULL,max_debit_cents INTEGER NOT NULL CHECK(max_debit_cents>0),reference_price TEXT NOT NULL,quote_as_of TEXT NOT NULL,created_at TEXT NOT NULL);
            """)
            initialize_action_tables(con)
            if not con.execute("SELECT 1 FROM a_strategy_settlement_rollout WHERE id=1").fetchone():
                from .settlement_calendar import POLICY_VERSION, LEGACY_POLICY_VERSION
                legacy_bound = con.execute("SELECT COALESCE(MAX(rowid),0) FROM p_fills").fetchone()[0]
                definition = dump({"legacy_fill_rowid_upper_bound": legacy_bound, "current_policy_version": POLICY_VERSION, "legacy_policy_version": LEGACY_POLICY_VERSION})
                con.execute("INSERT INTO a_strategy_settlement_rollout VALUES(1,?,?,?)", (definition, hashlib.sha256(definition.encode()).hexdigest(), now()))
                self.store.event(con, "strategy_settlement_policy_rollout", "execution_clerk", "Recorded the immutable legacy fill boundary; all later owned sales require versioned settlement receipts", json.loads(definition))
            if not con.execute("SELECT 1 FROM p_books").fetchone():
                self._create_book(con, "main", "Main paper book", "main", "local", "Empty operator-controlled paper workspace")
            book_columns = {r[1] for r in con.execute("PRAGMA table_info(p_books)")}
            if "connection_id" not in book_columns:
                con.execute("ALTER TABLE p_books ADD COLUMN connection_id TEXT NOT NULL DEFAULT 'default'")
            con.execute("DROP INDEX IF EXISTS p_one_alpaca")
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS p_one_alpaca_connection ON p_books(broker,connection_id) WHERE broker='alpaca'")
            intent_columns = {r[1] for r in con.execute("PRAGMA table_info(p_intents)")}
            for column in ("session_open", "session_close"):
                if column not in intent_columns:
                    con.execute(f"ALTER TABLE p_intents ADD COLUMN {column} TEXT")
            if "broker_cumulative_notional" not in intent_columns:
                con.execute("ALTER TABLE p_intents ADD COLUMN broker_cumulative_notional TEXT")
            if "stale_marks" not in {r[1] for r in con.execute("PRAGMA table_info(p_equity)")}:
                con.execute("ALTER TABLE p_equity ADD COLUMN stale_marks INTEGER")
            if not con.execute("SELECT 1 FROM p_state WHERE key='portfolio_policy'").fetchone():
                serialized, ts = dump(PORTFOLIO_POLICY), now()
                digest = hashlib.sha256(serialized.encode()).hexdigest()
                current = {**PORTFOLIO_POLICY, "version": 1, "hash": digest, "actor": "operator", "updated_at": ts}
                con.execute("INSERT INTO p_state VALUES('portfolio_policy',?)", (dump(current),))
                con.execute("INSERT INTO p_portfolio_policy_history VALUES(?,?,?,?,?,?)", (identifier(), 1, digest, serialized, "operator", ts))

    def _create_book(self, con, rid, name, kind, broker, description, connection_id="default"):
        policy = dump(POLICY)
        digest, ts = hashlib.sha256(policy.encode()).hexdigest(), now()
        if "connection_id" in {r[1] for r in con.execute("PRAGMA table_info(p_books)")}:
            con.execute("INSERT INTO p_books(id,name,kind,broker,description,policy,policy_version,policy_hash,created_at,updated_at,connection_id) VALUES(?,?,?,?,?,?,1,?,?,?,?)", (rid, name, kind, broker, description, policy, digest, ts, ts, connection_id))
        else:
            con.execute("INSERT INTO p_books(id,name,kind,broker,description,policy,policy_version,policy_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,1,?,?,?)", (rid, name, kind, broker, description, policy, digest, ts, ts))
        con.execute("INSERT INTO p_policy_history VALUES(?,?,?,?,?,?,?)", (identifier(), rid, 1, digest, policy, "operator", ts))
        return rid

    @staticmethod
    def _book(con, book_id):
        book = con.execute("SELECT * FROM p_books WHERE id=?", (book_id,)).fetchone()
        if not book:
            raise DeskError("Independent paper book not found", 404)
        return book

    def create_book(self, payload):
        allowed = {"name", "kind", "broker", "description", "connection_id"}
        if set(payload) - allowed:
            raise DeskError("Unknown book fields", 422)
        name = str(payload.get("name", "")).strip()
        kind, broker = payload.get("kind", "main"), payload.get("broker", "local")
        description = payload.get("description")
        connection_id = payload.get("connection_id", "default")
        if not isinstance(connection_id, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", connection_id):
            raise DeskError("connection_id must be a named configured paper connection", 422)
        if not 1 <= len(name) <= 100 or not isinstance(kind, str) or kind not in {"main", "context", "forward", "shadow"} or not isinstance(broker, str) or broker not in {"local", "alpaca"} or (description is not None and (not isinstance(description, str) or len(description) > 2000)):
            raise DeskError("Invalid independent book name, kind, broker or description", 422)
        with self.store.transaction() as con:
            if con.execute("SELECT 1 FROM p_books WHERE name=?", (name,)).fetchone():
                raise DeskError("A book with this name already exists")
            if broker == "alpaca" and con.execute("SELECT 1 FROM p_books WHERE broker='alpaca' AND connection_id=?", (connection_id,)).fetchone():
                raise DeskError("Only one book may bind each Alpaca paper account connection")
            rid = self._create_book(con, identifier(), name, kind, broker, description, connection_id)
            self.store.event(con, "book_created", "operator", f"Created independent {broker} paper book: {name}", {"book_id": rid, "kind": kind})
        return next(b for b in self.snapshot()["books"] if b["id"] == rid)

    def fund_book(self, book_id, amount, client_id):
        amount = decimal(amount, "amount")
        amount_cents = cents(amount)
        if amount != Decimal(amount_cents) / 100 or not isinstance(client_id, str) or not 1 <= len(client_id.strip()) <= 100:
            raise DeskError("Funding requires positive whole cents and a client_id", 422)
        with self.store.transaction() as con:
            book = self._book(con, book_id)
            if book["broker"] != "local":
                raise DeskError("Connected paper cash is read from the broker; local funding is unavailable")
            row = con.execute("SELECT * FROM p_fundings WHERE book_id=? AND client_id=?", (book_id, client_id)).fetchone()
            if row:
                if row["amount_cents"] != amount_cents:
                    raise DeskError("client_id already identifies a different funding amount")
                return {"id": row["id"], "book_id": book_id, "client_id": client_id, "amount": amount_cents / 100, "timestamp": row["timestamp"]}
            rid = identifier()
            cash = checked_cents(book["cash_cents"] + amount_cents, "Funded cash")
            self._equity_snapshot(con, book_id, datetime.now(UTC))
            peak = checked_cents(self._book(con, book_id)["peak_equity_cents"] + amount_cents, "Funded equity peak")
            checked_cents(sum(row[0] for row in con.execute("SELECT amount_cents FROM p_fundings WHERE book_id=?", (book_id,))) + amount_cents, "Total contributed capital")
            ts = now()
            con.execute("INSERT INTO p_fundings VALUES(?,?,?,?,?)", (rid, book_id, client_id, amount_cents, ts))
            con.execute("UPDATE p_books SET cash_cents=?,peak_equity_cents=?,updated_at=? WHERE id=?", (cash, peak, ts, book_id))
            self.store.event(con, "independent_book_funding", "operator", f"Added ${amount_cents / 100:,.2f} in paper capital to {book['name']}", {"book_id": book_id, "funding_id": rid})
            self._equity_snapshot(con, book_id, datetime.now(UTC))
            return {"id": rid, "book_id": book_id, "client_id": client_id, "amount": amount_cents / 100, "timestamp": ts}

    @staticmethod
    def _strategy_owner(con, book_id):
        return con.execute("SELECT * FROM a_strategy_ownership WHERE book_id=?", (book_id,)).fetchone()

    def claim_strategy_book(self, book_id, installation_id, con=None):
        """Bind one empty local trading book to one trusted installation.

        Virtual funding is allowed before or after claiming. A supplied
        connection must already be inside the manager's writer transaction.
        This internal method is not exposed to models, inboxes or HTTP callers.
        """
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

    @staticmethod
    def _strategy_settlement_release_at(clock):
        """Versioned regular-way maturity, then explicit local-paper opening cash."""
        return TradingDesk._strategy_settlement_terms(clock)["cash_release_at"]

    @staticmethod
    def _strategy_settlement_terms(clock):
        from .settlement_calendar import settlement_terms
        try:
            return settlement_terms(clock)
        except Exception:
            raise DeskError("Covered regular-way settlement calendar unavailable; no local strategy fill committed") from None

    @staticmethod
    def _legacy_strategy_settlement_release_at(clock):
        from .settlement_calendar import legacy_release_at
        try:
            return legacy_release_at(clock)
        except Exception:
            raise DeskError("Legacy settlement replay calendar unavailable") from None

    def _settlement_boundaries(self, con, row):
        """Validate stored policy before deriving any release or cash mutation."""
        from .settlement_calendar import POLICY_VERSION, LEGACY_POLICY_VERSION
        observed = clock_time(row["fill_observed_at"])
        terms = self._strategy_settlement_terms(observed)
        receipt = con.execute("SELECT * FROM a_strategy_settlement_policy_receipts WHERE fill_id=?", (row["fill_id"],)).fetchone()
        if receipt:
            if receipt["policy_version"] != POLICY_VERSION or hashlib.sha256(receipt["definition"].encode()).hexdigest() != receipt["definition_sha256"] or receipt["definition"] != dump(terms) or receipt["created_at"] != row["created_at"] or row["release_at"] != terms["cash_release_at"]:
                raise DeskError("Settlement policy receipt is unknown or differs from independent calendar replay")
            return terms["cash_release_at"], None
        rollout = con.execute("SELECT * FROM a_strategy_settlement_rollout WHERE id=1").fetchone()
        if not rollout or hashlib.sha256(rollout["definition"].encode()).hexdigest() != rollout["definition_sha256"]:
            raise DeskError("Settlement policy rollout boundary is missing or corrupt")
        boundary = json.loads(rollout["definition"])
        if boundary.get("current_policy_version") != POLICY_VERSION or boundary.get("legacy_policy_version") != LEGACY_POLICY_VERSION or type(boundary.get("legacy_fill_rowid_upper_bound")) is not int or boundary["legacy_fill_rowid_upper_bound"] < 0:
            raise DeskError("Settlement policy rollout boundary is unsupported")
        if row["fill_append_rowid"] > boundary["legacy_fill_rowid_upper_bound"]:
            raise DeskError("Post-rollout sale is missing its required settlement policy receipt")
        expected_legacy = self._legacy_strategy_settlement_release_at(observed)
        if row["release_at"] != expected_legacy:
            raise DeskError("Unversioned legacy settlement differs from its preserved prior policy")
        # Preserve the original ledger and released timestamp. A legacy marker
        # that released too early cannot make those proceeds spendable before
        # the newly evidenced regular-way boundary. This is an explicit hold,
        # not a retroactive rewrite of the old settlement assertion.
        effective = max(clock_time(expected_legacy), clock_time(terms["cash_release_at"])).isoformat()
        review = {"original_policy_version": LEGACY_POLICY_VERSION,
                  "original_release_at": row["release_at"], "original_released_at_at_review": row["released_at"],
                  "corrected_terms": terms, "cash_release_not_before": effective,
                  "legacy_ledger_timestamps_rewritten": False}
        existing = con.execute("SELECT * FROM a_strategy_settlement_legacy_reviews WHERE fill_id=?", (row["fill_id"],)).fetchone()
        if existing:
            if hashlib.sha256(existing["definition"].encode()).hexdigest() != existing["definition_sha256"]:
                raise DeskError("Legacy settlement hold review hash mismatch")
            accepted = json.loads(existing["definition"])
            if accepted.get("original_policy_version") != LEGACY_POLICY_VERSION or accepted.get("original_release_at") != row["release_at"] or accepted.get("corrected_terms") != terms or accepted.get("cash_release_not_before") != effective or accepted.get("legacy_ledger_timestamps_rewritten") is not False:
                raise DeskError("Legacy settlement hold differs from its accepted review")
            review = None
        return effective, review

    def strategy_cash(self, con, book_id, clock=None, release=True):
        """Return exact cash cents after unsettled sales and active reservations.

        Release records are bookkeeping only: sale cash is already in p_books.
        Reads can request release=False; admission and processing release due
        records inside their existing writer transaction before validating cash.
        """
        clock = clock_time(clock)
        book = self._book(con, book_id)
        owned = self._strategy_owner(con, book_id)
        unsettled, due, reviews = 0, [], []
        if owned:
            if release and not con.in_transaction:
                raise DeskError("Settlement release requires an existing writer transaction")
            rows = con.execute("SELECT s.*,f.observed_at AS fill_observed_at,f.rowid AS fill_append_rowid FROM a_strategy_settlements s JOIN p_fills f ON f.id=s.fill_id WHERE s.book_id=?", (book_id,)).fetchall()
            for row in rows:
                boundary, review = self._settlement_boundaries(con, row)
                if clock < clock_time(boundary):
                    unsettled += row["amount_cents"]
                elif row["released_at"] is None:
                    due.append(row["fill_id"])
                if review:
                    reviews.append((row["fill_id"], review))
            # Every row's policy has been validated before any update. Invalid
            # or unknown policy never partially releases earlier rows.
            if release:
                for fill_id, review in reviews:
                    definition = dump(review)
                    con.execute("INSERT INTO a_strategy_settlement_legacy_reviews VALUES(?,?,?,?)", (fill_id, definition, hashlib.sha256(definition.encode()).hexdigest(), clock.isoformat()))
                    self.store.event(con, "strategy_settlement_legacy_review", "execution_clerk", "Preserved prior settlement assertion and applied an explicit regular-way cash boundary", {"fill_id": fill_id, "book_id": book_id, **review})
                for fill_id in due:
                    con.execute("UPDATE a_strategy_settlements SET released_at=? WHERE fill_id=? AND released_at IS NULL", (clock.isoformat(), fill_id))
        reserved = con.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book_id,)).fetchone()[0]
        settled = checked_cents(book["cash_cents"] - unsettled, "Settled strategy cash")
        return {"cash_cents": book["cash_cents"], "unsettled_cents": unsettled, "settled_cents": settled, "reserved_cents": reserved, "available_cents": checked_cents(settled - reserved, "Available strategy cash")}

    def set_book(self, book_id, payload, expected_hash=None, actor="operator", transaction_guard=None):
        # All policy writes come from this operator route, never from workers/models.
        changes = payload.get("policy", payload)
        if not isinstance(changes, dict):
            raise DeskError("policy must be an object", 422)
        acknowledgements = changes.get("acknowledge_external_symbols", [])
        unknown = set(changes) - set(POLICY) - {"acknowledge_external_symbols"}
        if unknown:
            raise DeskError("Unknown book policy fields: " + ", ".join(sorted(unknown)), 422)
        if not isinstance(acknowledgements, list) or len(acknowledgements) > 100 or any(not isinstance(item, str) for item in acknowledgements):
            raise DeskError("acknowledge_external_symbols must be a bounded list", 422)
        acknowledged = [symbol(s) for s in acknowledgements]
        with self.store.transaction() as con:
            if transaction_guard is not None:
                transaction_guard(con)
            book = self._book(con, book_id)
            if expected_hash is not None and book["policy_hash"] != expected_hash:
                raise DeskError("Book policy changed since approval; compare-and-swap refused the stale update")
            policy = json.loads(book["policy"])
            for key, value in changes.items():
                if key == "acknowledge_external_symbols":
                    continue
                if key in {"allow_short", "halted"}:
                    if not isinstance(value, bool):
                        raise DeskError(key + " must be true or false", 422)
                elif key == "halt_reason":
                    if value is not None and (not isinstance(value, str) or len(value) > 500):
                        raise DeskError("halt_reason is too long", 422)
                elif value is not None:
                    val = decimal(value, key, positive=key not in {"fees_per_order", "slippage_bps"})
                    if val < 0 or (key.startswith("drawdown_") and val > 100) or (key == "slippage_bps" and val > 1000) or (key == "fees_per_order" and val != Decimal(cents(val)) / 100):
                        raise DeskError("Invalid operator policy value for " + key, 422)
                    value = number(val)
                elif key in {"fees_per_order", "slippage_bps"}:
                    raise DeskError(key + " cannot be null", 422)
                policy[key] = value
            serialized, ts = dump(policy), now()
            digest, version = hashlib.sha256(serialized.encode()).hexdigest(), book["policy_version"] + 1
            con.execute("UPDATE p_books SET policy=?,policy_version=?,policy_hash=?,updated_at=? WHERE id=?", (serialized, version, digest, ts, book_id))
            con.execute("INSERT INTO p_policy_history VALUES(?,?,?,?,?,?,?)", (identifier(), book_id, version, digest, serialized, actor, ts))
            for sym in acknowledged:
                con.execute("UPDATE p_positions SET locked=0,source='broker_operator_acknowledged',updated_at=? WHERE book_id=? AND symbol=?", (ts, book_id, sym))
            self.store.event(con, "book_policy_updated", actor, "Updated an authorized versioned paper-book policy", {"book_id": book_id, "version": version, "hash": digest, "policy": policy, "acknowledged_external_symbols": acknowledged})
        return next(b for b in self.snapshot()["books"] if b["id"] == book_id)

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
                # Accept the broker-native protective object shape without inventing prices.
                expected = "limit_price" if key == "take_profit" else "stop_price"
                if key not in {"take_profit", "stop_loss"} or set(value) != {expected}:
                    raise DeskError("Protective orders require a single explicit price", 422)
                value = value[expected]
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
        if data["take_profit"] and data["stop_loss"]:
            tp, sl = Decimal(data["take_profit"]), Decimal(data["stop_loss"])
            if (data["side"] == "buy" and tp <= sl) or (data["side"] == "sell" and tp >= sl):
                raise DeskError("Protective target and stop have inconsistent directions", 422)
        return data

    @staticmethod
    def _portfolio_policy(con):
        return json.loads(con.execute("SELECT value FROM p_state WHERE key='portfolio_policy'").fetchone()[0])

    def set_portfolio_policy(self, payload):
        if set(payload) - set(PORTFOLIO_POLICY) - {"expected_hash"}:
            raise DeskError("Unknown portfolio policy fields", 422)
        expected = payload.get("expected_hash")
        if expected is not None and not isinstance(expected, str):
            raise DeskError("expected_hash must be a policy hash", 422)
        changes = {}
        for key in PORTFOLIO_POLICY:
            if key not in payload:
                continue
            value = payload[key]
            if value is not None:
                val = decimal(value, key)
                if val != Decimal(cents(val)) / 100:
                    raise DeskError("Portfolio caps must be positive whole USD cents or null", 422)
                value = number(val)
            changes[key] = value
        if not changes:
            raise DeskError("Supply at least one portfolio policy field", 422)
        with self.store.transaction() as con:
            previous = self._portfolio_policy(con)
            if expected is not None and previous["hash"] != expected:
                raise DeskError("Portfolio policy changed; compare-and-swap refused the stale update")
            policy = {key: changes.get(key, previous[key]) for key in PORTFOLIO_POLICY}
            serialized, ts = dump(policy), now()
            digest, version = hashlib.sha256(serialized.encode()).hexdigest(), previous["version"] + 1
            current = {**policy, "version": version, "hash": digest, "updated_at": ts, "actor": "operator"}
            con.execute("UPDATE p_state SET value=? WHERE key='portfolio_policy'", (dump(current),))
            con.execute("INSERT INTO p_portfolio_policy_history VALUES(?,?,?,?,?,?)", (identifier(), version, digest, serialized, "operator", ts))
            self.store.event(con, "portfolio_policy_updated", "operator", "Updated versioned risk limits across independent autonomous books", current)
            return current

    def _global_exposure(self, con, clock, candidate=None, exclude=None):
        books = list(con.execute("SELECT * FROM p_books ORDER BY created_at"))
        positions = {(row["book_id"], row["symbol"]): Decimal(row["quantity"]) for row in con.execute("SELECT * FROM p_positions WHERE quantity!='0'") if Decimal(row["quantity"])}
        bounds, price_bounds, mismatched_protection = {}, {}, set()
        brokers = {book["id"]: book["broker"] for book in books}
        pending = [dict(row) for row in con.execute("SELECT * FROM p_intents WHERE id!=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (exclude or "",))]
        if candidate is not None:
            pending.append(dict(candidate))
        for row in pending:
            key = (row["book_id"], row["symbol"])
            held = positions.get(key, Decimal(0))
            quantity = Decimal(row["quantity"]) - Decimal(row.get("filled_quantity", "0"))
            if row.get("parent_id"):
                if brokers.get(row["book_id"]) == "alpaca" and quantity > 0 and not self._risk_reducing(held, row["side"], quantity):
                    mismatched_protection.add(row["book_id"])
                continue
            if quantity <= 0 or self._risk_reducing(held, row["side"], quantity):
                continue
            bounds.setdefault(key, [Decimal(0), Decimal(0)])[0 if row["side"] == "buy" else 1] += quantity
            for field in ("limit_price", "stop_price"):
                if row.get(field):
                    price_bounds[key] = max(price_bounds.get(key, Decimal(0)), Decimal(row[field]))
        reasons, marks, quotes, unknown_books = [], [], {}, set()
        for book_id in sorted(mismatched_protection):
            reasons.append("Broker protection no longer matches held exposure for book " + book_id)
            unknown_books.add(book_id)
        max_age = self.store.settings(con)["quote_max_age_seconds"]
        for book in books:
            if book["broker"] != "alpaca":
                continue
            health = con.execute("SELECT value FROM p_state WHERE key=?", ("reconcile:" + book["id"],)).fetchone()
            truth = con.execute("SELECT observed_at FROM p_broker_truth WHERE book_id=?", (book["id"],)).fetchone()
            if not truth or not health or json.loads(health[0]).get("status") != "ok":
                reasons.append("Broker state is unknown for book " + book["id"])
                unknown_books.add(book["id"])
            elif not -5 <= (clock - datetime.fromisoformat(truth[0])).total_seconds() <= max_age:
                reasons.append("Broker state is stale for book " + book["id"])
                unknown_books.add(book["id"])
            external = con.execute("SELECT value FROM p_state WHERE key=?", ("external_locks:" + book["id"],)).fetchone()
            if external and json.loads(external[0]):
                reasons.append("Unattributed broker orders make pending exposure unknown for book " + book["id"])
                unknown_books.add(book["id"])
        for sym in sorted({key[1] for key in positions} | {key[1] for key in bounds}):
            try:
                quote = self._raw_quote(con, sym, clock)
                quotes[sym] = Decimal(quote["price"])
                marks.append({"symbol": sym, "price": number(quote["price"]), "as_of": quote["as_of"], "source": quote["source"]})
            except DeskError as exc:
                reasons.append(sym + ": " + exc.detail)
        missing_symbols = {key[1] for key in positions.keys() | bounds.keys()} - quotes.keys()
        for book_id, sym in positions.keys() | bounds.keys():
            if sym in missing_symbols:
                unknown_books.add(book_id)
        symbol_values = {sym: [0, 0] for sym in {key[1] for key in positions.keys() | bounds.keys()}}
        book_values = {book["id"]: [0, 0] for book in books}
        for key in positions.keys() | bounds.keys():
            book_id, sym = key
            if sym not in quotes:
                continue
            held = positions.get(key, Decimal(0))
            buys, sells = bounds.get(key, [Decimal(0), Decimal(0)])
            observed = abs(cents(held * quotes[sym]))
            reserved_price = max(quotes[sym], price_bounds.get(key, Decimal(0)))
            projected = max(abs(cents((held + buys) * reserved_price)), abs(cents((held - sells) * reserved_price)), observed)
            symbol_values.setdefault(sym, [0, 0])
            for index, value in enumerate((observed, projected)):
                symbol_values[sym][index] += value
                book_values[book_id][index] += value
        complete = not reasons
        gross, projected = sum(row[0] for row in book_values.values()), sum(row[1] for row in book_values.values())
        mark_times = [datetime.fromisoformat(mark["as_of"]) for mark in marks]
        return {"valuation_status": "complete" if complete else "incomplete", "incomplete_reasons": reasons,
                "calculated_at": clock.isoformat(), "gross_exposure": gross / 100 if complete else None,
                "projected_gross_exposure": projected / 100 if complete else None,
                "symbols": [{"symbol": sym, "gross_exposure": values[0] / 100 if complete else None, "projected_gross_exposure": values[1] / 100 if complete else None} for sym, values in sorted(symbol_values.items())],
                "books": [{"book_id": rid, "valuation_status": "incomplete" if rid in unknown_books else "complete", "gross_exposure": values[0] / 100 if rid not in unknown_books else None, "projected_gross_exposure": values[1] / 100 if rid not in unknown_books else None} for rid, values in book_values.items()],
                "marks": marks, "mark_span_seconds": (max(mark_times) - min(mark_times)).total_seconds() if mark_times else 0,
                "scope": "autonomous_books_only", "max_mark_age_seconds": max_age,
                "method": "Sum per-book absolute exposure with pending entry quantity and explicit price bounds; independent books never net"}

    def _validate_global_capacity(self, con, data, exclude=None, clock=None):
        policy = self._portfolio_policy(con)
        if all(policy[key] is None for key in PORTFOLIO_POLICY):
            return
        exposure = self._global_exposure(con, clock or datetime.now(UTC), data, exclude)
        if exposure["valuation_status"] != "complete":
            raise DeskError("Portfolio entry gate requires coherent fresh marks and known broker state: " + "; ".join(exposure["incomplete_reasons"]))
        gross = Decimal(str(exposure["projected_gross_exposure"]))
        if policy["gross_exposure_cap"] is not None and gross > Decimal(str(policy["gross_exposure_cap"])):
            raise DeskError("Operator portfolio gross exposure cap would be exceeded")
        if policy["symbol_exposure_cap"] is not None:
            cap = Decimal(str(policy["symbol_exposure_cap"]))
            if any(Decimal(str(row["projected_gross_exposure"])) > cap for row in exposure["symbols"]):
                raise DeskError("Operator portfolio symbol exposure cap would be exceeded")

    def _raw_quote(self, con, sym, clock, require_fresh=True):
        quote = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
        if not quote:
            raise DeskError("A timestamped price is required for order validation")
        age = (clock - datetime.fromisoformat(quote["as_of"])).total_seconds()
        max_age = self.store.settings(con)["quote_max_age_seconds"]
        if require_fresh and not -5 <= age <= max_age:
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

    @staticmethod
    def _realized_coverage(broker):
        if broker == "local":
            return {"status": "known", "method": "Exact signed average-cost accounting in durable fill append order"}
        return {"status": "withheld", "reason": "Cumulative broker order receipts do not establish a complete ordered execution tape; reconstructed realized cents are internal estimates, not verified realized P&L", "required_evidence": "Complete ordered broker execution activities and verified source cost basis"}

    def _fill_public(self, con, row):
        broker = self._book(con, row["book_id"])["broker"]
        coverage = self._realized_coverage(broker)
        return {**dict(row), "quantity": number(row["quantity"]), "price": number(row["price"]), "notional": row["notional_cents"] / 100, "fee": row["fee_cents"] / 100,
                "realized_cents": row["realized_cents"] if broker == "local" else None,
                "realized_pnl": row["realized_cents"] / 100 if broker == "local" else None, "realized_pnl_coverage": coverage}

    def _account(self, con, book, clock):
        realized_coverage = self._realized_coverage(book["broker"])
        truth = con.execute("SELECT positions,account,observed_at FROM p_broker_truth WHERE book_id=?", (book["id"],)).fetchone() if book["broker"] == "alpaca" else None
        basis_cursor_row = con.execute("SELECT value FROM p_state WHERE key=?", ("basis_receipt_cursor:" + book["id"],)).fetchone() if truth else None
        basis_cursor = int(json.loads(basis_cursor_row[0])) if basis_cursor_row else None
        actual_positions = {row["symbol"]: row for row in json.loads(truth["positions"])} if truth else {}
        latest_book_fill = con.execute("SELECT COALESCE(MAX(rowid),0) FROM p_fills WHERE book_id=?", (book["id"],)).fetchone()[0]
        basis_complete = book["broker"] == "local" or bool(truth and (basis_cursor is None or latest_book_fill <= basis_cursor))
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
                fresh = -5 <= age <= self.store.settings(con)["quote_max_age_seconds"]
            else:
                price, marked, delta = None, 0, 0
                missing += 1
            stale += int(not fresh)
            value += marked
            pnl += delta
            gross += abs(marked)
            basis = {"status": "known", "method": "Exact local signed average-cost ledger"}
            average_cost = Decimal(row["cost_cents"]) / 100 / qty
            if book["broker"] == "alpaca":
                actual = actual_positions.get(row["symbol"])
                actual_qty = Decimal(str(actual["qty"])) if actual else Decimal(0)
                if actual and actual.get("side") == "short" and actual_qty > 0:
                    actual_qty = -actual_qty
                actual_cost = Decimal(str(actual["avg_entry_price"])) if actual else None
                latest_fill = con.execute("SELECT COALESCE(MAX(rowid),0) FROM p_fills WHERE book_id=? AND symbol=?", (book["id"], row["symbol"])).fetchone()[0]
                no_later_receipt = latest_fill <= basis_cursor if basis_cursor is not None else bool(truth and datetime.fromisoformat(row["updated_at"]) <= datetime.fromisoformat(truth["observed_at"]))
                known = bool(actual and actual_qty == qty and cents(actual_qty * actual_cost) == row["cost_cents"] and no_later_receipt)
                basis = {"status": "known", "source": "Complete broker position snapshot", "observed_at": truth["observed_at"], "method": "Broker average entry price and rounded signed USD-cent basis"} if known else {"status": "withheld", "reason": "Current position cost basis is not verified by a matching complete broker position snapshot"}
                average_cost = actual_cost if known else None
                basis_complete = basis_complete and known
            known_basis = basis["status"] == "known"
            positions.append({"book_id": book["id"], "symbol": row["symbol"], "quantity": number(qty), "average_cost": number(average_cost) if average_cost is not None else None, "cost_basis": row["cost_cents"] / 100 if known_basis else None, "cost_basis_coverage": basis, "mark_price": number(price) if price is not None else None, "market_value": marked / 100, "unrealized_pnl": delta / 100 if known_basis and (quote is not None or book["broker"] == "local") else None, "realized_pnl": row["realized_cents"] / 100 if book["broker"] == "local" else None, "realized_pnl_coverage": realized_coverage, "quote_fresh": fresh, "sleeve": row["sleeve"], "source": row["source"], "locked": bool(row["locked"]), "updated_at": row["updated_at"]})
        reserved = con.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book["id"],)).fetchone()[0]
        action_values = action_totals(con, book["id"], clock, self.store.settings(con)["quote_max_age_seconds"]) if strategy_owned else None
        if action_values:
            value += action_values["fractional_market_cents"]
            gross += abs(action_values["fractional_market_cents"])
            missing += action_values["missing_marks"]
            stale += action_values["stale_marks"]
        equity = book["cash_cents"] + value + (action_values["receivable_cents"] if action_values else 0)
        peak = max(book["peak_equity_cents"], equity)
        drawdown = number(Decimal(str(max(peak - equity, 0))) * 100 / Decimal(str(peak))) if peak > 0 else 0
        account = {"currency": "USD", "cash": book["cash_cents"] / 100, "equity": equity / 100, "market_value": value / 100, "gross_exposure": gross / 100, "reserved_cash": reserved / 100, "available_cash": (book["cash_cents"] - reserved) / 100, "realized_pnl": book["realized_cents"] / 100 if book["broker"] == "local" else None, "realized_pnl_coverage": realized_coverage, "unrealized_pnl": pnl / 100, "fees": book["fees_cents"] / 100, "missing_marks": missing, "stale_marks": stale, "drawdown_percent": drawdown}
        if strategy_owned:
            cash = self.strategy_cash(con, book["id"], clock, release=False)
            account.update(unsettled_cash=cash["unsettled_cents"] / 100,
                           settled_cash=cash["settled_cents"] / 100,
                           available_cash=cash["available_cents"] / 100,
                           settlement="Versioned US equity T+2/T+1 maturity calendar; local-paper cash at the first XNYS open on/after maturity, with explicit preserved-legacy hold reviews")
            account.update(dividend_receivable=action_values["receivable_cents"] / 100,
                           fractional_claim_market_value=action_values["fractional_market_cents"] / 100,
                           corporate_action_coverage=action_values["coverage"],
                           exact_market_value_cents=value,
                           exact_equity_cents=equity,
                           dividend_cash_release="Independent dated payment evidence required; configured Alpaca dates simulate local paper payment at the later payable/process date's 09:30 New York, without asserting actual broker receipt",
                           return_scope="Local price P&L plus gross accrued dividend receivables; independent payment evidence required; fractional claims are provisional marks")
        if book["broker"] == "alpaca":
            account["unrealized_pnl"] = pnl / 100 if basis_complete and not missing else None
            account["unrealized_pnl_coverage"] = {"status": "known", "method": "Timestamped marks against matching complete broker position basis"} if basis_complete and not missing else {"status": "withheld", "reason": "Matching complete broker position basis and all position marks are required"}
            if truth:
                remote = json.loads(truth["account"])
                account["broker_reported_equity"] = number(remote.get("equity", 0))
                account["broker_observed_at"] = truth["observed_at"]
        return account, positions

    def _validate_capacity(self, con, book, data, price, exclude=None, clock=None):
        clock = clock or datetime.now(UTC)
        policy = json.loads(book["policy"])
        foreign_locks = con.execute("SELECT value FROM p_state WHERE key=?", ("external_locks:" + book["id"],)).fetchone()
        if foreign_locks and data["symbol"] in json.loads(foreign_locks[0]):
            raise DeskError("Unattributed external broker orders lock this symbol until they are resolved")
        pos = self._position(con, book["id"], data["symbol"])
        qty = Decimal(pos["quantity"]) if pos else Decimal(0)
        order_qty = Decimal(data["quantity"]) - Decimal(data.get("filled_quantity", "0"))
        if pos and pos["locked"]:
            raise DeskError("This external broker position is locked pending explicit operator acknowledgement")
        reducing = self._risk_reducing(qty, data["side"], order_qty)
        if policy["halted"] and not reducing:
            raise DeskError("This book is halted for entries; risk-reducing exits remain available")
        account, positions = self._account(con, book, clock)
        if policy["drawdown_brake_percent"] is not None and account["drawdown_percent"] >= policy["drawdown_brake_percent"] and not reducing:
            raise DeskError("Operator drawdown brake blocks additional entry exposure")
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
        if projected < 0 and not policy["allow_short"] and not reducing:
            raise DeskError("Short entries require the operator's allow_short policy")
        active = list(con.execute("SELECT * FROM p_intents WHERE book_id=? AND id!=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (book["id"], exclude or "")))
        # Protective OCO siblings represent one liability, not duplicate share claims.
        shares, seen_groups = Decimal(0), set()
        for intent in active:
            if intent["symbol"] != data["symbol"] or intent["side"] != data["side"]:
                continue
            if intent["oco_group"]:
                if intent["oco_group"] in seen_groups or intent["oco_group"] == data.get("oco_group"):
                    continue
                seen_groups.add(intent["oco_group"])
            shares += Decimal(intent["reserved_quantity"])
        if data["side"] == "sell" and qty > 0 and min(order_qty, qty) + shares > qty:
            raise DeskError("Insufficient unreserved shares in this independent book")
        if data["side"] == "buy" and qty < 0 and min(order_qty, -qty) + shares > -qty:
            raise DeskError("Insufficient unreserved short shares to cover")
        reservation_price = price
        if data["side"] == "buy":
            # A triggered market buy can execute above today's quote. Preserve
            # the explicitly known trigger/limit liability before transport.
            bound = data.get("limit_price") or data.get("stop_price")
            reservation_price = max(price, Decimal(bound)) if bound else price
        estimated = checked_cents(cents(order_qty * reservation_price), "Reserved order notional")
        fee = cents(Decimal(str(policy["fees_per_order"]))) if Decimal(data.get("filled_quantity", "0")) == 0 else 0
        other_cash = sum(r["reserved_cents"] for r in active)
        # Existing short liabilities may be closed even when cash has deteriorated.
        spending_cash = self.strategy_cash(con, book["id"], clock)["settled_cents"] if owner else book["cash_cents"]
        if data["side"] == "buy" and not (reducing and qty < 0) and spending_cash - other_cash < estimated + fee:
            raise DeskError("Insufficient unreserved settled cash in this strategy book" if owner else "Insufficient unreserved cash in this independent book")
        if not reducing:
            self._validate_global_capacity(con, data, exclude, clock)
            # Reserve exposure as well as cash: separate pending short entries
            # must not evade operator caps merely because they generate proceeds.
            pending_by_symbol = {}
            pending_prices = {}
            for pending in active:
                if pending["parent_id"]:
                    continue
                p = self._position(con, book["id"], pending["symbol"])
                held = Decimal(p["quantity"]) if p else Decimal(0)
                remaining = Decimal(pending["quantity"]) - Decimal(pending["filled_quantity"])
                if self._risk_reducing(held, pending["side"], remaining):
                    continue
                pending_by_symbol.setdefault(pending["symbol"], [Decimal(0), Decimal(0)])
                pending_by_symbol[pending["symbol"]][0 if pending["side"] == "buy" else 1] += remaining
                for field in ("limit_price", "stop_price"):
                    if pending[field]:
                        pending_prices[pending["symbol"]] = max(pending_prices.get(pending["symbol"], Decimal(0)), Decimal(pending[field]))
            pending_by_symbol.setdefault(data["symbol"], [Decimal(0), Decimal(0)])[0 if data["side"] == "buy" else 1] += order_qty
            pending_prices[data["symbol"]] = max([price, pending_prices.get(data["symbol"], Decimal(0))] + [Decimal(data[field]) for field in ("limit_price", "stop_price") if data.get(field)])
            gross = 0
            all_symbols = {p["symbol"] for p in positions} | set(pending_by_symbol)
            for sym in all_symbols:
                held_pos = self._position(con, book["id"], sym)
                held_qty = Decimal(held_pos["quantity"]) if held_pos else Decimal(0)
                observed = max(Decimal(self._raw_quote(con, sym, clock)["price"]), pending_prices.get(sym, Decimal(0)))
                positive, negative = pending_by_symbol.get(sym, [Decimal(0), Decimal(0)])
                projected_value = max(abs(cents((held_qty + positive) * observed)), abs(cents((held_qty - negative) * observed)))
                if policy["symbol_exposure_cap"] is not None and projected_value > cents(Decimal(str(policy["symbol_exposure_cap"]))):
                    raise DeskError("Operator symbol exposure cap would be exceeded")
                gross += projected_value
            if policy["gross_exposure_cap"] is not None and gross > cents(Decimal(str(policy["gross_exposure_cap"]))):
                raise DeskError("Operator gross exposure cap would be exceeded")
        reserve_cash = estimated + fee if data["side"] == "buy" and not (reducing and qty < 0) else 0
        closing_direction = qty > 0 and data["side"] == "sell" or qty < 0 and data["side"] == "buy"
        reserve_qty = min(order_qty, abs(qty)) if closing_direction else Decimal(0)
        return reserve_cash, reserve_qty

    def submit_intent(self, payload):
        """Operator boundary; dedicated strategy books permit reducing sells only."""
        data = self._normalize_intent(payload)
        with self.store.transaction() as con:
            return self._submit_normalized_intent(con, data)

    def submit_strategy_intent(self, payload, installation_id, transaction_guard=None, con=None, clock=None):
        """Trusted installed-strategy boundary, sharing the manager transaction.

        The manager may persist its decision/outbox in the same BEGIN IMMEDIATE
        transaction. Exceptions must escape that outer transaction to roll back
        the entire decision and order together. HTTP and model routes cannot
        select this source or supply an installation identity.
        """
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

    def _submit_normalized_intent(self, con, data, installation_id=None, transaction_guard=None, clock=None, max_debit_cents=None):
        if transaction_guard is not None:
            transaction_guard(con)
        clock = clock_time(clock)
        book = self._book(con, data["book_id"])
        owner = self._strategy_owner(con, book["id"])
        strategy = installation_id is not None
        if strategy:
            if not owner or owner["installation_id"] != installation_id or book["broker"] != "local":
                raise DeskError("Strategy installation does not own this local paper book")
        elif owner and data["side"] != "sell":
            raise DeskError("Operator entries are prohibited in a strategy-owned book; reducing sells remain available")
        if owner:
            quantity = Decimal(data["quantity"])
            if quantity != quantity.to_integral_value():
                raise DeskError("Strategy-owned paper intents require whole shares", 422)
            fill_cap = data.get("max_fill_quantity") or json.loads(book["policy"])["max_fill_quantity"]
            if fill_cap is not None and Decimal(str(fill_cap)) != Decimal(str(fill_cap)).to_integral_value():
                raise DeskError("Strategy-owned partial fill limits require whole shares", 422)
        identity = {**data, "strategy_max_debit_cents": max_debit_cents} if strategy and max_debit_cents is not None else data
        digest = hashlib.sha256(dump(identity).encode()).hexdigest()
        existing = con.execute("SELECT * FROM p_intents WHERE book_id=? AND client_id=?", (book["id"], data["client_id"])).fetchone()
        source = "strategy" if strategy else "operator"
        if existing:
            if existing["payload_hash"] != digest or existing["source"] != source:
                raise DeskError("client_id already identifies a different autonomous intent")
            return self._intent_public(existing)
        position = self._position(con, book["id"], data["symbol"])
        held = Decimal(position["quantity"]) if position else Decimal(0)
        quantity = Decimal(data["quantity"])
        if owner and data["side"] == "sell" and not self._risk_reducing(held, "sell", quantity):
            raise DeskError("A strategy-owned book permits sales of existing unreserved long shares only")
        quote = self._raw_quote(con, data["symbol"], clock)
        signed = quantity * (1 if data["side"] == "buy" else -1)
        if book["broker"] == "alpaca" and held * signed < 0 and (data["take_profit"] or data["stop_loss"]):
            raise DeskError("Broker-native protection cannot cover or flip an existing opposite position; close it separately before a protected new entry", 422)
        reference = Decimal(data["limit_price"] or quote["price"])
        notional_cents = cents(quantity * reference)
        if not 1 <= notional_cents <= 9_000_000_000_000_000_000:
            raise DeskError("Intent notional must be at least one cent and fit the integer-cents ledger", 422)
        if data["take_profit"]:
            target = Decimal(data["take_profit"])
            if data["side"] == "buy" and target <= reference or data["side"] == "sell" and target >= reference:
                raise DeskError("Take-profit must be beyond the entry reference in the trade direction", 422)
        if data["stop_loss"]:
            stop = Decimal(data["stop_loss"])
            if data["side"] == "buy" and stop >= reference or data["side"] == "sell" and stop <= reference:
                raise DeskError("Stop-loss must be on the protective side of the entry reference", 422)
        reservation_reference = reference
        if strategy and data["side"] == "buy":
            # Match the actual local buy's slippage and cent rounding so a
            # strategy cannot promise cash that its queued simulation needs.
            slip = Decimal(str(json.loads(book["policy"])["slippage_bps"])) / 10000
            reservation_reference = max(reference, Decimal(quote["price"]) * (1 + slip))
        reserve_cash, reserve_qty = self._validate_capacity(con, book, data, reservation_reference, clock=clock)
        if strategy and data["side"] == "buy":
            max_debit_cents = reserve_cash if max_debit_cents is None else max_debit_cents
            if reserve_cash > max_debit_cents:
                raise DeskError("Strategy quote debit exceeds the frozen entry budget")
        rid, ts = identifier(), clock.isoformat()
        columns = list(data) + ["id", "payload_hash", "status", "reserved_cents", "reserved_quantity", "broker_client_id", "created_at", "updated_at", "policy_version", "source"]
        values = list(data.values()) + [rid, digest, "queued", reserve_cash, str(reserve_qty), "aster_" + rid, ts, ts, book["policy_version"], source]
        con.execute(f"INSERT INTO p_intents({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", values)
        if strategy and data["side"] == "buy":
            con.execute("INSERT INTO a_strategy_intent_limits VALUES(?,?,?,?,?,?)", (rid, installation_id, max_debit_cents, str(reservation_reference), quote["as_of"], ts))
        con.execute("INSERT OR IGNORE INTO watchlist VALUES(?,?)", (data["symbol"], ts))
        provenance = {"intent_id": rid, "book_id": book["id"], "client_id": data["client_id"], "policy_version": book["policy_version"], "execution": "installed strategy decision; automatic local paper order mechanics" if strategy else "automatic order mechanics; no strategy decision"}
        if strategy:
            provenance["installation_id"] = installation_id
            if data["side"] == "buy":
                provenance["max_debit_cents"] = max_debit_cents
        self.store.event(con, "strategy_intent_authorized" if strategy else "autonomous_intent_authorized", source,
                         f"{'Installed strategy' if strategy else 'Operator'} authorized {data['side']} {data['quantity']} {data['symbol']} in {book['name']}", provenance)
        return self._intent_public(con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone())

    @staticmethod
    def _intent_public(row):
        data = dict(row)
        for key in ("quantity", "filled_quantity", "reserved_quantity", "limit_price", "stop_price", "take_profit", "stop_loss", "max_fill_quantity"):
            data[key] = number(data[key]) if data[key] is not None else None
        for key in ("filled_notional_cents", "fees_cents", "reserved_cents"):
            data[key.replace("_cents", "")] = data.pop(key) / 100
        data["triggered"] = bool(data["triggered"])
        return data

    def cancel_intent(self, rid):
        with self.store.transaction() as con:
            row = con.execute("SELECT i.*,b.broker FROM p_intents i JOIN p_books b ON b.id=i.book_id WHERE i.id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Autonomous intent not found", 404)
            if row["status"] == "filled":
                raise DeskError("A filled intent cannot be cancelled")
            if row["status"] not in TERMINAL:
                status = "cancel_requested" if row["broker"] == "alpaca" and row["broker_id"] or row["status"] == "submitting" else "cancelled"
                con.execute("UPDATE p_intents SET status=?,reserved_cents=CASE WHEN ?='cancelled' THEN 0 ELSE reserved_cents END,reserved_quantity=CASE WHEN ?='cancelled' THEN '0' ELSE reserved_quantity END,completed_at=CASE WHEN ?='cancelled' THEN ? ELSE completed_at END,updated_at=? WHERE id=?", (status, status, status, status, now(), now(), rid))
                self.store.event(con, "autonomous_cancel_requested", "operator", "Operator requested cancellation of an autonomous intent", {"intent_id": rid, "status": status})
            return self._intent_public(con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone())

    def _equity_snapshot(self, con, book_id, clock):
        book = self._book(con, book_id)
        account, positions = self._account(con, book, clock)
        # No float round-trip in persisted cash, marks or equity.
        value = account.get("exact_market_value_cents", sum((cents(Decimal(row["quantity"]) * Decimal(row["price"])) for row in con.execute("SELECT p.quantity,q.price FROM p_positions p JOIN quotes q ON p.symbol=q.symbol WHERE p.book_id=?", (book_id,))), 0))
        equity = account.get("exact_equity_cents", book["cash_cents"] + value)
        con.execute("INSERT INTO p_equity(id,book_id,timestamp,cash_cents,equity_cents,market_value_cents,missing_marks,stale_marks) VALUES(?,?,?,?,?,?,?,?)", (identifier(), book_id, clock.isoformat(), book["cash_cents"], equity, value, account["missing_marks"], account["stale_marks"]))
        con.execute("UPDATE p_books SET peak_equity_cents=MAX(peak_equity_cents,?) WHERE id=?", (equity, book_id))

    def snapshot(self):
        with self.store.connect() as con:
            con.execute("BEGIN")
            books, all_positions = [], []
            ownership = [dict(r) for r in con.execute("SELECT * FROM a_strategy_ownership ORDER BY claimed_at,book_id")]
            owner_ids = {row["book_id"]: row["installation_id"] for row in ownership}
            for book in con.execute("SELECT * FROM p_books ORDER BY created_at"):
                account, positions = self._account(con, book, datetime.now(UTC))
                all_positions.extend(positions)
                health = con.execute("SELECT value FROM p_state WHERE key=?", ("reconcile:" + book["id"],)).fetchone()
                books.append({"id": book["id"], "name": book["name"], "kind": book["kind"], "broker": book["broker"], "connection_id": book["connection_id"], "description": book["description"], "account": account, "policy": json.loads(book["policy"]), "policy_version": book["policy_version"], "policy_hash": book["policy_hash"], "created_at": book["created_at"], "updated_at": book["updated_at"], "strategy_installation_id": owner_ids.get(book["id"]), "reconciliation_health": json.loads(health[0]) if health else {"status": "not_checked"}})
            return {"books": books, "intents": [self._intent_public(r) for r in con.execute("SELECT * FROM p_intents ORDER BY created_at DESC LIMIT 1000")], "positions": all_positions,
                    "fills": [self._fill_public(con, r) for r in con.execute("SELECT * FROM p_fills ORDER BY observed_at DESC LIMIT 1000")],
                    "equity_history": [{"book_id": r["book_id"], "timestamp": r["timestamp"], "equity": r["equity_cents"] / 100, "cash": r["cash_cents"] / 100, "missing_marks": r["missing_marks"], "stale_marks": r["stale_marks"]} for r in con.execute("SELECT * FROM (SELECT * FROM p_equity ORDER BY timestamp DESC LIMIT 2000) ORDER BY timestamp")],
                    "reconciliations": [{**dict(r), "payload": json.loads(r["payload"])} for r in con.execute("SELECT * FROM p_reconciliations ORDER BY timestamp DESC LIMIT 100")],
                    "policy_history": [{**dict(r), "policy": json.loads(r["policy"])} for r in con.execute("SELECT * FROM p_policy_history ORDER BY timestamp DESC LIMIT 200")],
                    "broker_truth": [{"book_id": r["book_id"], "account": json.loads(r["account"]), "positions": json.loads(r["positions"]), "orders": json.loads(r["orders"]), "observed_at": r["observed_at"]} for r in con.execute("SELECT * FROM p_broker_truth")], "strategy_count": len(ownership),
                    "strategy_extension": {"enabled": bool(ownership), "registry": ownership, "authorization": "Explicitly installed strategies own separate local paper books; research, model and inbox output have no order authority"},
                    "strategy_settlements": [dict(r) for r in con.execute("SELECT * FROM a_strategy_settlements ORDER BY created_at DESC,fill_id LIMIT 1000")],
                    "strategy_settlement_policy_receipts": [dict(r) for r in con.execute("SELECT * FROM a_strategy_settlement_policy_receipts ORDER BY created_at DESC,fill_id LIMIT 1000")],
                    "strategy_settlement_legacy_reviews": [dict(r) for r in con.execute("SELECT * FROM a_strategy_settlement_legacy_reviews ORDER BY reviewed_at DESC,fill_id LIMIT 1000")],
                    "strategy_settlement_rollout": [dict(r) for r in con.execute("SELECT * FROM a_strategy_settlement_rollout")],
                    "strategy_intent_limits": [dict(r) for r in con.execute("SELECT * FROM a_strategy_intent_limits ORDER BY created_at DESC,intent_id LIMIT 1000")],
                    "corporate_actions": [{**dict(r), "definition": json.loads(r["definition"]), "payload": json.loads(r["payload"])} for r in con.execute("SELECT * FROM a_strategy_actions ORDER BY observed_at DESC,id LIMIT 1000")],
                    "dividend_receivables": [dict(r) for r in con.execute("SELECT * FROM a_strategy_receivables ORDER BY created_at DESC,action_id LIMIT 1000")],
                    "fractional_claims": [dict(r) for r in con.execute("SELECT * FROM a_strategy_fractional_claims ORDER BY created_at DESC,action_id LIMIT 1000")],
                    "verified_action_payments": [dict(r) for r in con.execute("SELECT * FROM a_strategy_action_payments ORDER BY observed_at DESC,action_id LIMIT 1000")],
                    "broker_accounting_coverage": self._realized_coverage("alpaca"),
                    "protection_capability": {"local": "Persistent operator-priced OCO exits, resized after measured partial fills and restricted to newly opened exposure", "broker": "Operator-priced native brackets with parent/leg polling and owned-order adoption", "automatic_broker_repair": False, "limitation": "Missing or mismatched broker protection is not automatically cancelled or replaced; a verified broker protection repair workflow is not installed"},
                    "performance": self._performance(con, books), "global_policy": self._portfolio_policy(con),
                    "global_exposure": self._global_exposure(con, datetime.now(UTC)),
                    "global_policy_history": [{**dict(row), "policy": json.loads(row["policy"])} for row in con.execute("SELECT * FROM p_portfolio_policy_history ORDER BY version DESC LIMIT 100")]}

    def _performance(self, con, books):
        result = []
        for book in books:
            funded = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM p_fundings WHERE book_id=?", (book["id"],)).fetchone()[0]
            equity_cents = cents(Decimal(str(book["account"]["equity"])))
            comparable = book["broker"] == "local" and not book["account"]["missing_marks"] and not book["account"]["stale_marks"]
            result.append({"book_id": book["id"], "net_external_cashflows": funded / 100 if book["broker"] == "local" else None,
                           "net_profit": (equity_cents - funded) / 100 if comparable else None,
                           "simple_return_percent": number(Decimal(equity_cents - funded) * 100 / funded) if comparable and funded else None,
                           "return_method": "Cashflow-adjusted dollar P&L and simple contributed-capital return; not a time-weighted return",
                           "benchmarks": [{"symbol": "QQQ", "return_percent": None, "status": "Awaiting timestamp-aligned benchmark history"}, {"symbol": "SPY", "represents": "S&P 500 ETF proxy", "return_percent": None, "status": "Awaiting timestamp-aligned benchmark history"}],
                           "alpha_claim": None, "limitations": "Missing/stale marks and unobserved broker cashflows invalidate performance comparisons"})
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
        # Processing catches DeskError inside its transaction. Every possible
        # valuation-range failure must precede accounting effects, not leave a
        # measured fill half committed when the order is subsequently blocked.
        observed = con.execute("SELECT price FROM quotes WHERE symbol=?", (intent["symbol"],)).fetchone()
        mark = cents(new_qty * Decimal(observed[0])) if observed else 0
        market_value = sum((cents(Decimal(row["quantity"]) * Decimal(row["price"])) for row in con.execute("SELECT p.quantity,q.price FROM p_positions p JOIN quotes q ON p.symbol=q.symbol WHERE p.book_id=? AND p.symbol!=?", (book["id"], intent["symbol"]))), mark)
        checked_cents(market_value, "Resulting market value")
        checked_cents(cash + market_value, "Resulting equity")
        con.execute("UPDATE p_books SET cash_cents=?,realized_cents=?,fees_cents=?,updated_at=? WHERE id=?", (cash, realized_total, fees_total, clock.isoformat(), book["id"]))
        con.execute("INSERT OR REPLACE INTO p_positions VALUES(?,?,?,?,?,?,?,?,?)", (book["id"], intent["symbol"], str(new_qty), new_cost, old_realized + realized, sleeve, "local_simulation" if book["broker"] == "local" else "broker_owned", 0, clock.isoformat()))
        fid = identifier()
        con.execute("INSERT INTO p_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (fid, intent["id"], book["id"], intent["symbol"], intent["side"], str(quantity), str(price), notional, fee, realized, fill_key, source_timestamp or (clock.isoformat() if book["broker"] == "local" else None), clock.isoformat(), source, quote["as_of"] if quote else None, quote["source"] if quote else None, book["policy_version"]))
        if settlement_amount:
            con.execute("INSERT INTO a_strategy_settlements VALUES(?,?,?,?,?,NULL)", (fid, book["id"], settlement_amount, settlement_release, clock.isoformat()))
            definition = dump(settlement_terms)
            con.execute("INSERT INTO a_strategy_settlement_policy_receipts VALUES(?,?,?,?,?)", (fid, settlement_terms["policy_version"], definition, hashlib.sha256(definition.encode()).hexdigest(), clock.isoformat()))
        filled = Decimal(intent["filled_quantity"]) + quantity
        remaining = Decimal(intent["quantity"]) - filled
        status = "filled" if remaining <= 0 else "partially_filled"
        bound = intent["limit_price"] or intent["stop_price"]
        reservation_price = max(price, Decimal(bound)) if bound else price
        remaining_is_short_cover = new_qty < 0 and self._risk_reducing(new_qty, intent["side"], remaining)
        reserve_cash = cents(remaining * reservation_price) if intent["side"] == "buy" and not remaining_is_short_cover else 0
        closing_direction = new_qty > 0 and intent["side"] == "sell" or new_qty < 0 and intent["side"] == "buy"
        reserve_qty = min(remaining, abs(new_qty)) if closing_direction else Decimal(0)
        completed = clock.isoformat() if status == "filled" else intent["completed_at"] if intent["status"] in TERMINAL else None
        con.execute("UPDATE p_intents SET filled_quantity=?,filled_notional_cents=filled_notional_cents+?,fees_cents=fees_cents+?,status=?,reserved_cents=?,reserved_quantity=?,completed_at=?,updated_at=?,error=NULL WHERE id=?", (str(filled), notional, fee, status, reserve_cash, str(reserve_qty), completed, clock.isoformat(), intent["id"]))
        self.store.event(con, "autonomous_paper_fill", "execution_clerk", f"{source}: {intent['side']} {quantity} {intent['symbol']}", {"intent_id": intent["id"], "book_id": book["id"], "fill_id": fid, "quantity": number(quantity), "price": number(price), "notional": notional / 100, "fee": fee / 100, "realized_pnl": realized / 100 if book["broker"] == "local" else None, "realized_pnl_coverage": self._realized_coverage(book["broker"]), "source_timestamp": source_timestamp, "observed_at": clock.isoformat(), "quote_as_of": quote["as_of"] if quote else None, **({"strategy_installation_id": strategy_owner["installation_id"], "sale_cash_release_at": settlement_release, "settlement_terms": settlement_terms} if strategy_owner else {})})
        if book["broker"] == "local":
            if intent["parent_id"]:
                self._oco_after_fill(con, intent, remaining, clock)
            elif intent["take_profit"] or intent["stop_loss"]:
                opened_qty = quantity - min(abs(old_qty), quantity) if old_qty * delta < 0 else quantity
                if opened_qty > 0:
                    self._create_protection(con, intent, opened_qty, fid, book, clock)
        self._equity_snapshot(con, book["id"], clock)
        return True

    def _create_protection(self, con, parent, qty, fill_id, book, clock):
        group = parent["id"] + ":" + fill_id
        side = "sell" if parent["side"] == "buy" else "buy"
        for kind, key in (("limit", "take_profit"), ("stop", "stop_loss")):
            if not parent[key]:
                continue
            rid, ts = identifier(), clock.isoformat()
            data = {"id": rid, "book_id": book["id"], "client_id": "protect_" + rid, "payload_hash": hashlib.sha256(group.encode()).hexdigest(), "symbol": parent["symbol"], "side": side, "quantity": str(qty), "order_type": kind, "time_in_force": "gtc", "limit_price": parent[key] if kind == "limit" else None, "stop_price": parent[key] if kind == "stop" else None, "status": "open", "reserved_quantity": str(qty), "parent_id": parent["id"], "oco_group": group, "broker_client_id": "aster_" + rid, "created_at": ts, "updated_at": ts, "policy_version": book["policy_version"], "sleeve": parent["sleeve"], "reason": "Explicit operator-defined protective " + key, "source": "operator_protection"}
            columns = list(data)
            con.execute(f"INSERT INTO p_intents({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", list(data.values()))
            self.store.event(con, "protective_order_created", "execution_clerk", "Created persistent protection using the operator's explicit price", {"intent_id": rid, "parent_id": parent["id"], "oco_group": group, "price": number(parent[key]), "quantity": number(qty), "order_type": kind})

    def _oco_after_fill(self, con, intent, remaining, clock):
        for sibling in con.execute("SELECT * FROM p_intents WHERE oco_group=? AND id!=? AND status IN ('queued','open','partially_filled','blocked')", (intent["oco_group"], intent["id"])).fetchall():
            if remaining <= 0:
                con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error='OCO sibling filled' WHERE id=?", (clock.isoformat(), clock.isoformat(), sibling["id"]))
            else:
                con.execute("UPDATE p_intents SET quantity=?,reserved_quantity=?,updated_at=? WHERE id=?", (str(Decimal(sibling["filled_quantity"]) + remaining), str(remaining), clock.isoformat(), sibling["id"]))
            self.store.event(con, "oco_protection_updated", "execution_clerk", "Updated the sibling protection after a measured protective fill", {"intent_id": sibling["id"], "remaining_quantity": number(max(remaining, Decimal(0)))})
        parent = con.execute("SELECT * FROM p_intents WHERE id=?", (intent["parent_id"],)).fetchone()
        if parent and parent["status"] in ACTIVE:
            con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,error='Protective exit triggered; unfilled parent remainder cancelled' WHERE id=?", (clock.isoformat(), parent["id"]))
            self.store.event(con, "protected_parent_remainder_cancelled", "execution_clerk", "Cancelled the unfilled entry remainder when its operator-defined protection executed", {"intent_id": parent["id"]})

    def _terminal(self, con, intent, status, reason, clock):
        con.execute("UPDATE p_intents SET status=?,error=?,reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=? WHERE id=?", (status, reason, clock.isoformat(), clock.isoformat(), intent["id"]))
        self.store.event(con, "autonomous_order_" + status, "execution_clerk", reason, {"intent_id": intent["id"], "book_id": intent["book_id"]})

    def _block(self, con, intent, reason, clock):
        state = intent["status"] if intent["status"] in {"submitting", "cancel_requested"} else "blocked"
        if intent["error"] != reason or intent["status"] != state:
            con.execute("UPDATE p_intents SET status=?,error=?,updated_at=? WHERE id=?", (state, reason, clock.isoformat(), intent["id"]))
            self.store.event(con, "autonomous_order_blocked", "risk_officer", reason, {"intent_id": intent["id"], "book_id": intent["book_id"]})

    def _window(self, con, intent, calendar, clock, broker=False, initial_calendar=None):
        if intent["expires_at"] and clock >= datetime.fromisoformat(intent["expires_at"]):
            self._terminal(con, intent, "expired", "Explicit expiry reached", clock)
            return False
        if intent["not_before"] and clock < datetime.fromisoformat(intent["not_before"]):
            return False
        tif = intent["time_in_force"]
        if tif == "gtc":
            return bool(calendar.get("is_open")) or broker
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
            return clock <= end if broker else session_open <= clock <= end
        if clock > session_close:
            self._terminal(con, intent, "expired", "Session window closed; no late replay", clock)
            return False
        if tif == "cls":
            return clock <= session_close if broker else session_close - timedelta(seconds=60) <= clock <= session_close
        return session_open <= clock <= session_close and bool(calendar.get("is_open")) or broker and clock <= session_close

    def _service_ids(self):
        # A bounded pass must never repeatedly serve only the oldest waiting
        # entries. Give cancellations/protection dedicated capacity and persist
        # a rotating cursor in each class so restart preserves fair service.
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

    def process(self, providers, clock=None):
        dynamic_clock = clock is None
        clock = clock_time(clock)
        result = {"processed": 0, "fills": 0, "submitted": 0, "errors": []}
        try:
            calendar = providers.calendar(clock)
        except Exception:
            result["errors"].append("Exchange calendar unavailable; execution deferred")
            calendar = None
        ids = self._service_ids()
        for rid in ids:
            if dynamic_clock:
                clock = clock_time(None)
                try:
                    calendar = providers.calendar(clock)
                except Exception:
                    calendar = None
            with self.store.transaction() as con:
                execution_fence = getattr(providers, "execution_fence", None)
                if callable(execution_fence):
                    execution_fence(con)
                intent = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                if not intent or intent["status"] not in ACTIVE:
                    continue
                book = self._book(con, intent["book_id"])
                reconciliation = con.execute("SELECT value FROM p_state WHERE key=?", ("reconcile:" + book["id"],)).fetchone()
                can_verify_lifecycle = book["broker"] == "alpaca" and (intent["broker_id"] or intent["status"] in {"cancel_requested", "submitting"})
                if reconciliation and json.loads(reconciliation[0])["status"] == "failed" and not can_verify_lifecycle:
                    self._block(con, intent, "This book's reconciliation failed; other books remain independent", clock)
                    result["errors"].append({"book_id": book["id"], "detail": "Book reconciliation failed"})
                    continue
                if book["broker"] == "alpaca":
                    remote = True
                else:
                    remote = False
                    try:
                        if calendar is None:
                            raise DeskError("Exchange calendar unavailable; no new local fill authorized")
                        original_calendar = providers.calendar(datetime.fromisoformat(intent["not_before"] or intent["created_at"])) if intent["session_close"] is None and intent["time_in_force"] != "gtc" else None
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
                        triggered = intent["triggered"]
                        if intent["order_type"] in {"stop", "stop_limit"}:
                            threshold = Decimal(intent["stop_price"])
                            triggered = triggered or (observed >= threshold if intent["side"] == "buy" else observed <= threshold)
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
                        capacity_data = dict(intent)
                        self._validate_capacity(con, book, capacity_data, price, rid, clock)
                        max_fill = intent["max_fill_quantity"] or policy["max_fill_quantity"]
                        quantity = min(remaining, Decimal(str(max_fill))) if max_fill else remaining
                        fee = cents(Decimal(str(policy["fees_per_order"]))) if Decimal(intent["filled_quantity"]) == 0 else 0
                        notional = cents(quantity * price)
                        if notional < 1:
                            raise DeskError("Fill notional is below one cent")
                        fill_key = rid + ":local:" + str(Decimal(intent["filled_quantity"]) + quantity)
                        if dynamic_clock:
                            clock = clock_time(None)
                            calendar = providers.calendar(clock)
                            if not self._window(con, intent, calendar, clock, initial_calendar=original_calendar):
                                continue
                            self._raw_quote(con, intent["symbol"], clock)
                        result["fills"] += int(self._fill(con, intent, quantity, notional, price, fee, clock, fill_key, "local quote-based simulation", quote=quote))
                        result["processed"] += 1
                    except DeskError as exc:
                        self._block(con, intent, exc.detail, clock)
                        result["errors"].append({"intent_id": rid, "detail": exc.detail})
            if remote:
                self._process_broker(providers, rid, calendar, clock, result, dynamic_clock)
        return result

    def _accepted_cancel_reason(self, con, intent, book, clock):
        if intent["expires_at"] and clock >= datetime.fromisoformat(intent["expires_at"]):
            return "Explicit operator expiry reached; broker cancellation must be verified"
        if intent["session_close"] and intent["time_in_force"] in {"day", "cls"} and clock > datetime.fromisoformat(intent["session_close"]):
            return "Authorized exchange session ended; broker cancellation must be verified"
        if intent["session_open"] and intent["time_in_force"] == "opg" and clock > datetime.fromisoformat(intent["session_open"]) + timedelta(seconds=60):
            return "Opening window ended; no fallback; broker cancellation must be verified"
        position = self._position(con, book["id"], intent["symbol"])
        held = Decimal(position["quantity"]) if position else Decimal(0)
        remaining = Decimal(intent["quantity"]) - Decimal(intent["filled_quantity"])
        reducing = self._risk_reducing(held, intent["side"], remaining)
        policy = json.loads(book["policy"])
        if not reducing:
            if policy["halted"]:
                return "Operator halt cancels outstanding entry exposure; existing exits remain active"
            projected = held + (remaining if intent["side"] == "buy" else -remaining)
            if projected < 0 and not policy["allow_short"]:
                return "Operator short-entry permission was withdrawn"
            try:
                self._validate_global_capacity(con, dict(intent), intent["id"], clock)
            except DeskError as exc:
                return "Outstanding entry cannot satisfy the current portfolio policy: " + exc.detail
            quote = con.execute("SELECT * FROM quotes WHERE symbol=?", (intent["symbol"],)).fetchone()
            if quote:
                try:
                    self._validate_capacity(con, book, dict(intent), Decimal(intent["limit_price"] or quote["price"]), intent["id"], clock)
                except DeskError as exc:
                    return "Outstanding entry violates the current operator policy: " + exc.detail
        return None

    def _process_broker(self, providers, rid, calendar, clock, result, dynamic_clock=False):
        if dynamic_clock:
            clock = clock_time(None)
            try:
                calendar = providers.calendar(clock)
            except Exception:
                calendar = None
        with self.store.connect() as reader:
            connection = reader.execute("SELECT b.connection_id FROM p_books b JOIN p_intents i ON i.book_id=b.id WHERE i.id=?", (rid,)).fetchone()
        broker = self._broker_for(providers, connection[0]) if connection else None
        if broker is None:
            with self.store.transaction() as con:
                intent = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                if intent["status"] == "cancel_requested":
                    con.execute("UPDATE p_intents SET error=?,updated_at=? WHERE id=?", ("Cancellation retained while Alpaca PAPER adapter is unavailable", clock.isoformat(), rid))
                else:
                    self._block(con, intent, "Alpaca PAPER adapter is not configured", clock)
            return
        with self.store.connect() as reader:
            unresolved = reader.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
        resolved_missing = False
        if unresolved and unresolved["status"] in {"submitting", "cancel_requested"} and not unresolved["broker_id"]:
            # Resolve an uncertain prior transport before applying a new time/risk
            # gate. Its receipt may already represent an executed broker trade.
            try:
                recovered = broker.get_order(client_id=unresolved["broker_client_id"])
                if recovered:
                    if dynamic_clock:
                        clock = clock_time(None)
                    with self.store.transaction() as con:
                        current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                        self._apply_remote_order(con, current, recovered, clock)
                        self.store.event(con, "paper_broker_identity_recovered", "execution_clerk", "Recovered the actual broker receipt before reconsidering time or risk gates", {"intent_id": rid, "broker_id": recovered.get("id")})
                    return
                resolved_missing = True
            except Exception:
                result["errors"].append({"intent_id": rid, "detail": "Prior transport remains unverified; no expiry or resend was assumed"})
                return
        with self.store.transaction() as con:
            intent = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
            book = self._book(con, intent["book_id"])
            if intent["status"] in TERMINAL:
                return
            cancelling = intent["status"] == "cancel_requested"
            if not cancelling and intent["broker_id"]:
                reason = self._accepted_cancel_reason(con, intent, book, clock)
                if not reason:
                    return  # Account/order poll supplies measured status and fills.
                con.execute("UPDATE p_intents SET status='cancel_requested',error=?,updated_at=? WHERE id=?", (reason, clock.isoformat(), rid))
                self.store.event(con, "authorized_broker_cancel_required", "risk_officer", reason, {"intent_id": rid, "book_id": book["id"]})
                cancelling = True
            try:
                reconciliation = con.execute("SELECT value FROM p_state WHERE key=?", ("reconcile:" + book["id"],)).fetchone()
                if not cancelling and reconciliation and json.loads(reconciliation[0])["status"] == "failed":
                    raise DeskError("This book's reconciliation failed; identity recovery is allowed but new transport is deferred")
                if not cancelling and calendar is None:
                    raise DeskError("Exchange calendar unavailable; new broker transport is deferred")
                truth = con.execute("SELECT observed_at FROM p_broker_truth WHERE book_id=?", (book["id"],)).fetchone()
                if not cancelling and (not truth or (clock - datetime.fromisoformat(truth[0])).total_seconds() > self.store.settings(con)["quote_max_age_seconds"]):
                    raise DeskError("A recent successful complete broker reconciliation is required before transport")
                original_calendar = providers.calendar(datetime.fromisoformat(intent["not_before"] or intent["created_at"])) if not cancelling and intent["session_close"] is None and intent["time_in_force"] != "gtc" else None
                if not cancelling and not self._window(con, intent, calendar, clock, broker=True, initial_calendar=original_calendar):
                    return
                if not cancelling:
                    quote = self._raw_quote(con, intent["symbol"], clock)
                    self._validate_capacity(con, book, dict(intent), Decimal(intent["limit_price"] or quote["price"]), rid, clock)
            except DeskError as exc:
                self._block(con, intent, exc.detail, clock)
                return
            data = dict(intent)
            # Persist submission identity before any request can leave this process.
            if not cancelling:
                con.execute("UPDATE p_intents SET status='submitting',submitted_at=COALESCE(submitted_at,?),updated_at=? WHERE id=?", (clock.isoformat(), clock.isoformat(), rid))
        try:
            # Lookup occurs before every first send/retry. Failure never authorizes resend.
            existing = None if resolved_missing else broker.get_order(client_id=data["broker_client_id"])
            if dynamic_clock:
                clock = clock_time(None)
                try:
                    calendar = providers.calendar(clock)
                except Exception:
                    calendar = None
            if cancelling:
                if existing:
                    with self.store.transaction() as con:
                        current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                        self._apply_remote_order(con, current, existing, clock)
                        if con.execute("SELECT status FROM p_intents WHERE id=?", (rid,)).fetchone()[0] in TERMINAL:
                            return
                    broker.cancel(existing["id"])
                    with self.store.transaction() as con:
                        con.execute("UPDATE p_intents SET broker_id=?,broker_status='pending_cancel',updated_at=? WHERE id=?", (existing["id"], clock.isoformat(), rid))
                else:
                    with self.store.transaction() as con:
                        current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                        self._terminal(con, current, "cancelled", "Broker confirmed client identity was not submitted", clock)
                return
            remote = existing
            if remote is None:
                with self.store.transaction() as con:
                    execution_fence = getattr(providers, "execution_fence", None)
                    if callable(execution_fence):
                        execution_fence(con)
                    current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                    if current["status"] == "cancel_requested":
                        self._terminal(con, current, "cancelled", "Operator cancelled before paper-broker transport", clock)
                        return
                    if current["status"] in TERMINAL:
                        return
                    if calendar is None:
                        raise DeskError("Exchange calendar unavailable; new broker transport is deferred")
                    live_book = self._book(con, current["book_id"])
                    original_calendar = providers.calendar(datetime.fromisoformat(current["not_before"] or current["created_at"])) if current["session_close"] is None and current["time_in_force"] != "gtc" else None
                    if not self._window(con, current, calendar, clock, broker=True, initial_calendar=original_calendar):
                        return
                    quote = self._raw_quote(con, current["symbol"], clock)
                    self._validate_capacity(con, live_book, dict(current), Decimal(current["limit_price"] or quote["price"]), rid, clock)
                    data = dict(current)
                submission = {**data, "client_id": data["broker_client_id"], "quantity": number(data["quantity"])}
                remote = broker.submit(submission)
                result["submitted"] += 1
                if dynamic_clock:
                    clock = clock_time(None)
            with self.store.transaction() as con:
                current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                self._apply_remote_order(con, current, remote, clock)
                self.store.event(con, "paper_broker_submission_receipt", "execution_clerk", "Recorded Alpaca PAPER order receipt; accepted status alone is not a fill", {"intent_id": rid, "broker_id": remote.get("id"), "client_id": data["broker_client_id"], "broker_status": remote.get("status"), "recovered_by_client_id": existing is not None})
        except DeskError as exc:
            if getattr(exc, "paused", False):
                raise
            with self.store.transaction() as con:
                current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                if current["status"] != "cancel_requested":
                    self._block(con, current, exc.detail, clock)
            result["errors"].append({"intent_id": rid, "detail": exc.detail})
        except Exception:
            with self.store.transaction() as con:
                current = con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()
                reason = "Paper broker result is ambiguous or unavailable; saved identity will be looked up before any resend"
                if current["error"] != reason:
                    con.execute("UPDATE p_intents SET error=?,updated_at=? WHERE id=?", (reason, clock.isoformat(), rid))
                    self.store.event(con, "paper_broker_submission_uncertain", "execution_clerk", reason, {"intent_id": rid, "broker_client_id": data["broker_client_id"]})
            result["errors"].append({"intent_id": rid, "detail": reason})

    def _apply_remote_order(self, con, intent, remote, clock):
        remote_id = str(remote.get("id") or "")
        client_id = str(remote.get("client_order_id") or "")
        if (not remote_id or (intent["broker_id"] and intent["broker_id"] != remote_id)
                or client_id != intent["broker_client_id"]
                or symbol(str(remote.get("symbol", ""))) != intent["symbol"]
                or remote.get("side") != intent["side"]):
            raise DeskError("Broker order identity does not match the authorized intent; saved ledger preserved")
        if remote.get("type") != intent["order_type"] or remote.get("time_in_force") != intent["time_in_force"]:
            raise DeskError("Broker order mechanics do not match the authorized intent; saved ledger preserved")
        for field in ("limit_price", "stop_price"):
            observed_price, authorized_price = remote.get(field), intent[field]
            if (observed_price is None) != (authorized_price is None) or (observed_price is not None and Decimal(str(observed_price)) != Decimal(authorized_price)):
                raise DeskError("Broker order price does not match the authorized intent; saved ledger preserved")
        remote_quantity = decimal(remote.get("qty"), "broker order quantity", max_places=9)
        if remote_quantity != Decimal(intent["quantity"]) and not (intent["parent_id"] and remote_quantity < Decimal(intent["quantity"])):
            raise DeskError("Broker order quantity does not match the authorized intent; saved ledger preserved")
        qty = Decimal(str(remote.get("filled_qty") or "0"))
        previous = Decimal(intent["filled_quantity"])
        if not qty.is_finite() or qty < previous or qty > remote_quantity or previous > remote_quantity:
            raise DeskError("Broker cumulative fill quantity is inconsistent; saved ledger preserved")
        if remote.get("status") == "filled" and qty != remote_quantity:
            raise DeskError("Broker filled status has incomplete cumulative quantity; saved ledger preserved")
        if remote_quantity != Decimal(intent["quantity"]):
            intent = {**dict(intent), "quantity": str(remote_quantity)}
        exact_notional = None
        if qty:
            avg = Decimal(str(remote.get("filled_avg_price") or "0"))
            if not avg.is_finite() or avg <= 0:
                raise DeskError("Broker fill has no valid cumulative execution price")
            exact_notional = qty * avg
            if qty == previous and cents(exact_notional) != intent["filled_notional_cents"]:
                raise DeskError("Broker revised execution notional without additional quantity; saved ledger preserved")
        if qty > previous:
            cumulative_notional = checked_cents(cents(exact_notional), "Broker cumulative notional")
            delta_notional = cumulative_notional - intent["filled_notional_cents"]
            prior_exact = intent["broker_cumulative_notional"]
            if prior_exact is None:
                # Existing deployments retain their measured cent ledger; new
                # receipts additionally preserve exact broker cumulative value.
                prior_exact = sum((Decimal(row["quantity"]) * Decimal(row["price"]) for row in con.execute("SELECT quantity,price FROM p_fills WHERE intent_id=?", (intent["id"],))), Decimal(0))
            else:
                prior_exact = Decimal(prior_exact)
            exact_delta = exact_notional - prior_exact
            if delta_notional < 0 or exact_delta <= 0:
                raise DeskError("Broker cumulative notional is inconsistent")
            delta_qty = qty - previous
            actual_delta_price = exact_delta / delta_qty
            observed_timestamp = remote.get("filled_at") or remote.get("updated_at")
            observed_timestamp = timestamp(observed_timestamp, "broker fill timestamp") if observed_timestamp else None
            self._fill(con, intent, delta_qty, delta_notional, actual_delta_price, 0, clock, intent["id"] + ":broker:" + str(qty.normalize()), "Alpaca PAPER cumulative fill delta", source_timestamp=observed_timestamp)
        if exact_notional is not None:
            con.execute("UPDATE p_intents SET broker_cumulative_notional=? WHERE id=?", (str(exact_notional), intent["id"]))
        remote_status = str(remote.get("status", "unknown"))
        status = {"filled": "filled", "partially_filled": "partially_filled", "canceled": "cancelled", "cancelled": "cancelled", "expired": "expired", "rejected": "rejected", "pending_cancel": "cancel_requested"}.get(remote_status, "partially_filled" if qty else "open")
        if intent["status"] in TERMINAL and status not in TERMINAL:
            # A lagging order-list response cannot undo a conclusive lifecycle
            # receipt. Newly observed cumulative fills remain accounted above.
            status = "filled" if qty == remote_quantity else intent["status"]
        if intent["status"] == "filled":
            status = "filled"
        if intent["status"] == "cancel_requested" and status not in TERMINAL:
            status = "cancel_requested"
        if status in ACTIVE and intent["parent_id"]:
            position = self._position(con, intent["book_id"], intent["symbol"])
            held = Decimal(position["quantity"]) if position else Decimal(0)
            remaining = Decimal(intent["quantity"]) - qty
            matches_direction = held > 0 and intent["side"] == "sell" or held < 0 and intent["side"] == "buy"
            reserve_qty = min(remaining, abs(held)) if matches_direction else Decimal(0)
            con.execute("UPDATE p_intents SET reserved_quantity=? WHERE id=?", (str(reserve_qty), intent["id"]))
        con.execute("UPDATE p_intents SET quantity=?,broker_id=?,broker_status=?,status=?,updated_at=?,completed_at=CASE WHEN ? THEN COALESCE(completed_at,?) ELSE completed_at END,reserved_cents=CASE WHEN ? THEN 0 ELSE reserved_cents END,reserved_quantity=CASE WHEN ? THEN '0' ELSE reserved_quantity END,error=NULL WHERE id=?", (str(remote_quantity), remote_id, remote_status, status, clock.isoformat(), status in TERMINAL, clock.isoformat(), status in TERMINAL, status in TERMINAL, intent["id"]))

    def _adopt_order(self, con, book, remote, clock, parent=None):
        client = str(remote.get("client_order_id") or "")
        rid = identifier()
        qty = decimal(remote.get("qty"), "broker order quantity", max_places=9)
        side = remote.get("side")
        if side not in {"buy", "sell"}:
            raise DeskError("Broker order side is invalid")
        data = {"id": rid, "book_id": book["id"], "client_id": "adopted_" + str(remote["id"]), "payload_hash": hashlib.sha256(dump(remote).encode()).hexdigest(), "symbol": symbol(remote["symbol"]), "side": side, "quantity": str(qty), "order_type": remote.get("type", "market"), "time_in_force": remote.get("time_in_force", "day"), "limit_price": str(remote["limit_price"]) if remote.get("limit_price") is not None else None, "stop_price": str(remote["stop_price"]) if remote.get("stop_price") is not None else None, "status": "open", "broker_id": str(remote["id"]), "broker_client_id": client or "adopted_" + str(remote["id"]), "created_at": timestamp(remote.get("submitted_at"), "broker submitted_at") or clock.isoformat(), "updated_at": clock.isoformat(), "submitted_at": timestamp(remote.get("submitted_at"), "broker submitted_at"), "policy_version": book["policy_version"], "reason": "Adopted an existing Aster-prefixed broker order; originating local receipt is unavailable", "source": "broker_orphan" if parent is None else "broker_protection", "parent_id": parent["id"] if parent else None, "oco_group": parent["id"] if parent else None}
        columns = list(data)
        con.execute(f"INSERT INTO p_intents({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", list(data.values()))
        self.store.event(con, "paper_broker_orphan_adopted", "accountant", "Adopted an owned broker order using its source identity; no invented sleeve", {"intent_id": rid, "broker_id": remote["id"], "book_id": book["id"], "source": data["source"]})
        return con.execute("SELECT * FROM p_intents WHERE id=?", (rid,)).fetchone()

    def reconcile(self, providers, clock=None):
        dynamic_clock = clock is None
        clock = clock_time(clock)
        result = {"books": 0, "adopted": 0, "fills": 0, "errors": []}
        self._reconcile_local(clock, result)
        with self.store.connect() as con:
            connected = [dict(r) for r in con.execute("SELECT * FROM p_books WHERE broker='alpaca'")]
        for book in connected:
            broker = self._broker_for(providers, book["connection_id"])
            if broker is None:
                result["errors"].append("Alpaca PAPER adapter is not configured")
                with self.store.transaction() as con:
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("reconcile:" + book["id"], dump({"status": "failed", "observed_at": clock.isoformat(), "reason": "Paper adapter is not configured"})))
                continue
            try:
                # Commit only after all account, position and order reads succeed.
                account, positions, orders = broker.account(), broker.positions(), broker.orders()
                if not isinstance(account, dict) or not isinstance(positions, list) or not isinstance(orders, list):
                    raise ValueError("Incomplete broker snapshot")
                cash_cents = checked_cents(cents(Decimal(str(account["cash"]))), "Broker cash")
                present_ids = {str(remote.get("id")) for remote in orders}
                for remote in orders:
                    present_ids.update(str(leg.get("id")) for leg in remote.get("legs") or [])
                with self.store.connect() as reader:
                    missing = [dict(row) for row in reader.execute("SELECT * FROM p_intents WHERE book_id=? AND (broker_id IS NOT NULL OR status IN ('submitting','cancel_requested')) AND status IN ('open','partially_filled','submitting','cancel_requested')", (book["id"],)) if row["broker_id"] is None or row["broker_id"] not in present_ids]
                    protective_parents = {r["broker_client_id"] for r in reader.execute("SELECT * FROM p_intents WHERE book_id=? AND (take_profit IS NOT NULL OR stop_loss IS NOT NULL)", (book["id"],))}
                # Network reads finish before the write transaction; broker status
                # persistence cannot deadlock with a held account-write lock.
                for pending in missing:
                    actual = broker.get_order(client_id=pending["broker_client_id"])
                    if actual:
                        orders.append(actual)
                for index, remote in enumerate(orders):
                    if not remote.get("legs") and (remote.get("order_class") in {"bracket", "oto"} or remote.get("client_order_id") in protective_parents):
                        actual = broker.get_order(client_id=remote.get("client_order_id"))
                        if actual:
                            orders[index] = actual
                if dynamic_clock:
                    clock = clock_time(None)
                adopted = 0
                with self.store.transaction() as con:
                    account_identity = str(account.get("id") or account.get("account_number") or "")
                    if account_identity:
                        for bound in con.execute("SELECT * FROM p_broker_truth"):
                            existing_account = json.loads(bound["account"])
                            existing_identity = str(existing_account.get("id") or existing_account.get("account_number") or "")
                            if bound["book_id"] == book["id"] and existing_identity and existing_identity != account_identity:
                                raise DeskError("The broker account identity changed; saved book binding was preserved")
                            if bound["book_id"] != book["id"] and existing_identity == account_identity:
                                raise DeskError("The same actual paper account cannot be attributed to multiple books")
                    before = con.execute("SELECT COUNT(*) FROM p_fills WHERE book_id=?", (book["id"],)).fetchone()[0]
                    owned_symbols = set()
                    flattened = []
                    observations = []
                    for remote in orders:
                        flattened.append((remote, None))
                        for leg in remote.get("legs") or []:
                            flattened.append((leg, remote.get("id")))
                    for remote, parent_broker_id in flattened:
                        current = con.execute("SELECT * FROM p_intents WHERE book_id=? AND (broker_id=? OR broker_client_id=?)", (book["id"], str(remote.get("id", "")), str(remote.get("client_order_id", "")))).fetchone()
                        parent = con.execute("SELECT * FROM p_intents WHERE book_id=? AND broker_id=?", (book["id"], str(parent_broker_id or ""))).fetchone() if parent_broker_id else None
                        if not current and (str(remote.get("client_order_id", "")).startswith("aster_") or parent is not None):
                            current = self._adopt_order(con, book, remote, clock, parent)
                            adopted += 1
                        if current:
                            owned_symbols.add(current["symbol"])
                            observations.append((current["id"], remote))
                    # Descending broker lists cannot define average-cost history.
                    # Establish parent/leg identities first, then replay observed
                    # cumulative deltas in their source chronology.
                    observations.sort(key=lambda item: datetime.fromisoformat(timestamp(item[1].get("filled_at") or item[1].get("updated_at") or item[1].get("submitted_at") or clock, "broker observation timestamp")))
                    for current_id, remote in observations:
                        current = con.execute("SELECT * FROM p_intents WHERE id=?", (current_id,)).fetchone()
                        self._apply_remote_order(con, current, remote, clock)
                    old_positions = {r["symbol"]: dict(r) for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (book["id"],))}
                    remote_symbols = set()
                    owned_broker_ids = {r[0] for r in con.execute("SELECT broker_id FROM p_intents WHERE book_id=? AND broker_id IS NOT NULL", (book["id"],))}
                    external_order_symbols = {symbol(r["symbol"]) for r, parent_id in flattened if str(r.get("id")) not in owned_broker_ids and not str(r.get("client_order_id", "")).startswith("aster_") and r.get("status") not in {"filled", "canceled", "cancelled", "expired", "rejected"}}
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("external_locks:" + book["id"], dump(sorted(external_order_symbols))))
                    for remote in positions:
                        sym = symbol(remote["symbol"])
                        qty = Decimal(str(remote["qty"]))
                        if remote.get("side") == "short" and qty > 0:
                            qty = -qty
                        price = Decimal(str(remote["avg_entry_price"]))
                        if not qty.is_finite() or not price.is_finite() or price <= 0:
                            raise ValueError("Invalid broker position")
                        remote_symbols.add(sym)
                        prior = old_positions.get(sym)
                        acknowledged = prior and prior["source"] == "broker_operator_acknowledged"
                        expected_qty = Decimal(prior["quantity"]) if prior else Decimal(0)
                        expected_cost = prior["cost_cents"] if prior else 0
                        matches_owned_ledger = expected_qty == qty and expected_cost == cents(qty * price)
                        owned = acknowledged or bool((sym in owned_symbols or prior and prior["source"] == "broker_owned") and matches_owned_ledger)
                        locked = not owned or sym in external_order_symbols
                        source = "broker_operator_acknowledged" if acknowledged else "broker_owned" if owned else "broker_external_unknown"
                        con.execute("INSERT OR REPLACE INTO p_positions VALUES(?,?,?,?,?,?,?,?,?)", (book["id"], sym, str(qty), cents(qty * price), prior["realized_cents"] if prior else 0, prior["sleeve"] if prior and owned else None, source, int(locked), clock.isoformat()))
                        con.execute("INSERT OR IGNORE INTO watchlist VALUES(?,?)", (sym, clock.isoformat()))
                    for sym, old in old_positions.items():
                        if sym not in remote_symbols:
                            con.execute("UPDATE p_positions SET quantity='0',cost_cents=0,updated_at=? WHERE book_id=? AND symbol=?", (clock.isoformat(), book["id"], sym))
                    # Broker legs can precede the parent's fill timestamp in a
                    # nested snapshot. Reserve against the final complete broker
                    # position, not the transient history replay order.
                    for protective in con.execute("SELECT * FROM p_intents WHERE book_id=? AND parent_id IS NOT NULL AND status IN ('open','partially_filled','cancel_requested')", (book["id"],)).fetchall():
                        position = self._position(con, book["id"], protective["symbol"])
                        held = Decimal(position["quantity"]) if position else Decimal(0)
                        remaining = Decimal(protective["quantity"]) - Decimal(protective["filled_quantity"])
                        matching = held > 0 and protective["side"] == "sell" or held < 0 and protective["side"] == "buy"
                        reserved = min(abs(held), remaining) if matching else Decimal(0)
                        con.execute("UPDATE p_intents SET reserved_quantity=? WHERE id=?", (str(reserved), protective["id"]))
                    con.execute("UPDATE p_books SET cash_cents=?,updated_at=? WHERE id=?", (cash_cents, clock.isoformat(), book["id"]))
                    con.execute("INSERT OR REPLACE INTO p_broker_truth VALUES(?,?,?,?,?)", (book["id"], dump(account), dump(positions), dump(orders), clock.isoformat()))
                    basis_cursor = con.execute("SELECT COALESCE(MAX(rowid),0) FROM p_fills WHERE book_id=?", (book["id"],)).fetchone()[0]
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("basis_receipt_cursor:" + book["id"], dump(basis_cursor)))
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("reconcile:" + book["id"], dump({"status": "ok", "observed_at": clock.isoformat()})))
                    after = con.execute("SELECT COUNT(*) FROM p_fills WHERE book_id=?", (book["id"],)).fetchone()[0]
                    payload = {"position_count": len(positions), "order_count": len(orders), "new_fill_deltas": after - before, "external_symbols_locked": sorted(sym for sym in remote_symbols if sym not in owned_symbols and not (old_positions.get(sym, {}).get("source") == "broker_operator_acknowledged"))}
                    con.execute("INSERT INTO p_reconciliations VALUES(?,?,?,?,?,?)", (identifier(), book["id"], clock.isoformat(), "completed", "Reconciled actual Alpaca PAPER account, positions and orders", dump(payload)))
                    self.store.event(con, "paper_broker_reconciled", "accountant", "Committed a complete broker snapshot and measured cumulative fill deltas", {"book_id": book["id"], **payload})
                    self._equity_snapshot(con, book["id"], clock)
                result["fills"] += after - before
                result["books"] += 1
                result["adopted"] += adopted
            except Exception:
                detail = "Broker reconciliation failed; previously observed account, positions and orders were preserved"
                with self.store.transaction() as con:
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("reconcile:" + book["id"], dump({"status": "failed", "observed_at": clock.isoformat(), "reason": detail})))
                    con.execute("INSERT INTO p_reconciliations VALUES(?,?,?,?,?,?)", (identifier(), book["id"], clock.isoformat(), "failed", detail, "{}"))
                    self.store.event(con, "paper_broker_reconcile_failed", "accountant", detail, {"book_id": book["id"]})
                result["errors"].append(detail)
        return result

    @staticmethod
    def _broker_for(providers, connection_id):
        resolver = getattr(providers, "broker_for", None)
        if callable(resolver):
            return resolver(connection_id)
        return getattr(providers, "broker", None) if connection_id == "default" else None

    def _reconcile_local(self, clock, result):
        with self.store.connect() as reader:
            books = [dict(r) for r in reader.execute("SELECT * FROM p_books WHERE broker='local'")]
        for book in books:
            try:
                with self.store.transaction() as con:
                    saved_book = self._book(con, book["id"])
                    for field in ("cash_cents", "realized_cents", "fees_cents", "peak_equity_cents"):
                        checked_cents(saved_book[field], "Saved " + field)
                    cash = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM p_fundings WHERE book_id=?", (book["id"],)).fetchone()[0]
                    rebuilt, realized, fees = {}, 0, 0
                    strategy_owned = self._strategy_owner(con, book["id"])
                    expected_settlements = {}
                    splits = [dict(row) for row in con.execute("SELECT * FROM a_strategy_actions WHERE book_id=? AND kind='split' AND applied_at IS NOT NULL", (book["id"],))] if strategy_owned else []
                    splits.sort(key=lambda row: (json.loads(row["payload"])["after_fill_rowid"], row["effective_at"], row["id"]))
                    next_split, expected_fractions = 0, {}
                    def replay_splits(before_rowid=None):
                        nonlocal next_split
                        while next_split < len(splits):
                            action = splits[next_split]
                            if before_rowid is not None and json.loads(action["payload"])["after_fill_rowid"] >= before_rowid:
                                break
                            fraction, basis = apply_replayed_split(rebuilt, action)
                            if fraction:
                                expected_fractions[action["id"]] = (action["symbol"], str(fraction), basis)
                            next_split += 1
                    # Cost-basis mutations follow durable append order. Wall
                    # clocks can move backwards without reversing accounting.
                    for fill in con.execute("SELECT rowid AS append_rowid,* FROM p_fills WHERE book_id=? ORDER BY rowid", (book["id"],)):
                        replay_splits(fill["append_rowid"])
                        for field in ("notional_cents", "fee_cents", "realized_cents"):
                            checked_cents(fill[field], "Saved fill " + field)
                        qty = Decimal(fill["quantity"])
                        delta = qty if fill["side"] == "buy" else -qty
                        old_qty, old_cost, prior_realized = rebuilt.setdefault(fill["symbol"], [Decimal(0), 0, 0])
                        notional = fill["notional_cents"]
                        gain = 0
                        if old_qty == 0 or old_qty * delta >= 0:
                            cost = old_cost + (notional if delta > 0 else -notional)
                        else:
                            closing = min(abs(old_qty), qty)
                            basis = abs(old_cost) if closing == abs(old_qty) else int((Decimal(abs(old_cost)) * closing / abs(old_qty)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                            closing_notional = notional if closing == qty else int((Decimal(notional) * closing / qty).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                            gain = closing_notional - basis if old_qty > 0 else basis - closing_notional
                            cost = old_cost - (basis if old_qty > 0 else -basis) + (notional - closing_notional) * (1 if delta > 0 else -1)
                        held = old_qty + delta
                        rebuilt[fill["symbol"]] = [held, 0 if held == 0 else cost, prior_realized + gain]
                        cash += (-notional if delta > 0 else notional) - fill["fee_cents"]
                        realized += gain
                        fees += fill["fee_cents"]
                        if strategy_owned and fill["side"] == "sell" and fill["notional_cents"] > fill["fee_cents"]:
                            saved_policy = con.execute("SELECT * FROM a_strategy_settlement_policy_receipts WHERE fill_id=?", (fill["id"],)).fetchone()
                            observed_sale = clock_time(fill["observed_at"])
                            expected_release = self._strategy_settlement_release_at(observed_sale) if saved_policy else self._legacy_strategy_settlement_release_at(observed_sale)
                            expected_settlements[fill["id"]] = (book["id"], fill["notional_cents"] - fill["fee_cents"], expected_release, fill["observed_at"])
                        if gain != fill["realized_cents"] or notional != cents(qty * Decimal(fill["price"])):
                            raise DeskError("Local fill arithmetic failed independent reconciliation")
                    replay_splits()
                    if strategy_owned:
                        for action in con.execute("SELECT * FROM a_strategy_actions WHERE book_id=?", (book["id"],)):
                            if hashlib.sha256(action["definition"].encode()).hexdigest() != action["definition_sha256"]:
                                raise DeskError("Corporate action definition no longer matches its accepted hash")
                        fractions = list(con.execute("SELECT * FROM a_strategy_fractional_claims WHERE book_id=?", (book["id"],)))
                        if {row["action_id"]: (row["symbol"], row["quantity"], row["basis_cents"]) for row in fractions} != expected_fractions:
                            raise DeskError("Corporate split fractional claims do not match independent basis replay")
                        fraction_map = {row["action_id"]: row for row in fractions}
                        dividends = [dict(row) for row in con.execute("SELECT * FROM a_strategy_actions WHERE book_id=? AND kind='dividend' AND applied_at IS NOT NULL", (book["id"],))]
                        expected_dividends = {}
                        for action in dividends:
                            quantity = owned_quantity_at(con, book["id"], action["symbol"], action["effective_at"])
                            amount = cents(quantity * Decimal(json.loads(action["definition"])["amount"]))
                            expected_dividends[action["id"]] = (action["symbol"], str(quantity), amount)
                        receivables = list(con.execute("SELECT * FROM a_strategy_receivables WHERE book_id=?", (book["id"],)))
                        if {row["action_id"]: (row["symbol"], row["entitled_quantity"], row["amount_cents"]) for row in receivables} != expected_dividends:
                            raise DeskError("Dividend receivables differ from independently reconstructed overnight holdings")
                        paid_action_ids = {row["action_id"] for row in con.execute("SELECT action_id FROM a_strategy_action_payments WHERE book_id=?", (book["id"],))}
                        for row in fractions + receivables:
                            pending_status = "awaiting_cash_in_lieu" if "basis_cents" in row.keys() else "receivable"
                            if row["status"] not in {"paid", pending_status} or (row["status"] == "paid") != (row["action_id"] in paid_action_ids):
                                raise DeskError("Corporate claim settlement status does not match independent payment receipts")
                        for payment in con.execute("SELECT p.*,a.kind,a.symbol,a.effective_at FROM a_strategy_action_payments p JOIN a_strategy_actions a ON a.id=p.action_id WHERE p.book_id=?", (book["id"],)):
                            if clock_time(payment["payment_at"]) < clock_time(payment["effective_at"]):
                                raise DeskError("Corporate payment predates its action")
                            cash += payment["amount_cents"]
                            if payment["kind"] == "split":
                                claim = fraction_map.get(payment["action_id"])
                                if not claim or claim["status"] != "paid":
                                    raise DeskError("Cash-in-lieu payment lacks its settled fractional claim")
                                gain = payment["amount_cents"] - claim["basis_cents"]
                                realized += gain
                                rebuilt[payment["symbol"]][2] += gain
                            else:
                                dividend = con.execute("SELECT * FROM a_strategy_receivables WHERE action_id=?", (payment["action_id"],)).fetchone()
                                if not dividend or dividend["status"] != "paid" or dividend["amount_cents"] != payment["amount_cents"]:
                                    raise DeskError("Dividend payment lacks its exact receivable")
                    actual = {r["symbol"]: [Decimal(r["quantity"]), r["cost_cents"], r["realized_cents"]] for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (book["id"],))}
                    if strategy_owned:
                        settlements = list(con.execute("SELECT s.*,f.observed_at AS fill_observed_at,f.rowid AS fill_append_rowid FROM a_strategy_settlements s JOIN p_fills f ON f.id=s.fill_id WHERE s.book_id=?", (book["id"],)))
                        actual_settlements = {row["fill_id"]: (row["book_id"], row["amount_cents"], row["release_at"], row["created_at"]) for row in settlements}
                        if actual_settlements != expected_settlements or any(row["released_at"] and clock_time(row["released_at"]) < clock_time(row["release_at"]) for row in settlements):
                            raise DeskError("Versioned strategy settlement records do not match local sale fills")
                        for row in settlements:
                            self._settlement_boundaries(con, row)
                    fresh_book = self._book(con, book["id"])
                    if actual != rebuilt or (cash, realized, fees) != (fresh_book["cash_cents"], fresh_book["realized_cents"], fresh_book["fees_cents"]):
                        raise DeskError("Local funding/fills and signed cost basis do not match the saved paper book")
                    payload = {"cash": cash / 100, "realized_pnl": realized / 100, "fees": fees / 100, "symbols": len(rebuilt)}
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("reconcile:" + book["id"], dump({"status": "ok", "observed_at": clock.isoformat()})))
                    con.execute("INSERT INTO p_reconciliations VALUES(?,?,?,?,?,?)", (identifier(), book["id"], clock.isoformat(), "completed", "Independently reconstructed local funding, signed holdings and fill ledger", dump(payload)))
                    self._equity_snapshot(con, book["id"], clock)
                result["books"] += 1
            except Exception:
                reason = "Local paper ledger reconciliation failed; new execution must be investigated"
                with self.store.transaction() as con:
                    con.execute("INSERT OR REPLACE INTO p_state VALUES(?,?)", ("reconcile:" + book["id"], dump({"status": "failed", "observed_at": clock.isoformat(), "reason": reason})))
                    con.execute("INSERT INTO p_reconciliations VALUES(?,?,?,?,?,?)", (identifier(), book["id"], clock.isoformat(), "failed", reason, "{}"))
                    self.store.event(con, "local_paper_reconcile_failed", "accountant", reason, {"book_id": book["id"]})
                result["errors"].append(reason)
