"""Timestamp-preserving public data and a strictly paper-only broker adapter.

Provider configuration never implies connectivity. Reads establish connectivity;
historical bars never become current quotes. Credentials remain in memory only.
"""
import json
import hashlib
import base64
import builtins
import csv
import io
import math
import os
import re
import sqlite3
import threading
import datetime as datetime_types
import httpx
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

import exchange_calendars as exchange
import pandas as pd

from .store import DeskError, symbol
from .http_transport import bounded_http


UTC = timezone.utc
NY = ZoneInfo("America/New_York")
PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
BAR_DAYS = {"1d": 1, "5d": 5, "1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "2y": 732, "5y": 1830, "max": None}
BAR_INTERVALS = {"1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"}


def utc_clock(clock=None):
    value = clock or datetime.now(UTC)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise DeskError("Clock must have a timezone", 422)
    return value.astimezone(UTC)


class ProviderError(RuntimeError):
    def __init__(self, message, status=None):
        self.status = status
        super().__init__(message)


def _request(method, url, payload=None, headers=None):
    """Bounded transport; never expose response bodies, URLs or authentication."""
    request_headers = {"User-Agent": "Mozilla/5.0 AsterDesk/1.0", "Accept": "application/json", **(headers or {})}
    body = None if payload is None else json.dumps(payload).encode()
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    try:
        status, body = bounded_http(method, url, body, request_headers, timeout_seconds=8, maximum_bytes=8_000_000, follow_redirects=not url.startswith((PAPER_URL, DATA_URL)))
        if not 200 <= status < 300:
            raise ProviderError(f"Provider HTTP request failed ({status})", status)
        return json.loads(body) if body else None
    except (httpx.HTTPError, TimeoutError, OSError, ValueError):
        raise ProviderError("Provider request failed or returned invalid data") from None


def _csv_request(url):
    try:
        status, body = bounded_http("GET", url, None, {"User-Agent": "Mozilla/5.0 AsterDesk/1.0", "Accept": "text/csv"}, timeout_seconds=8, maximum_bytes=8_000_000, follow_redirects=True)
        if not 200 <= status < 300:
            raise ProviderError("Historical CSV provider is unavailable", status)
        return body.decode("utf-8-sig")
    except (httpx.HTTPError, TimeoutError, OSError, ValueError, UnicodeError):
        raise ProviderError("Historical CSV provider is unavailable") from None


def _unconfigured_csv(url):
    raise ProviderError("No CSV transport was supplied to the injected provider adapter")


@lru_cache(maxsize=1)
def _nyse():
    return exchange.get_calendar("XNYS", start="2000-01-01", end="2040-12-31")


def exchange_calendar(clock=None):
    clock = utc_clock(clock)
    cal = _nyse()
    day = pd.Timestamp(clock.astimezone(NY).date())
    valid = cal.is_session(day)
    previous = cal.previous_session(day) if valid else cal.date_to_session(day, direction="previous")
    following = cal.next_session(day) if valid else cal.date_to_session(day, direction="next")
    opened = cal.session_open(day).to_pydatetime() if valid else None
    closed = cal.session_close(day).to_pydatetime() if valid else None
    upcoming = day if valid and clock < opened else following
    upcoming_close = day if valid and clock < closed else following
    iso = lambda value: value.isoformat() if value is not None else None
    return {
        "exchange": "XNYS", "timezone": "America/New_York", "timestamp": clock.isoformat(),
        "date": str(day.date()), "is_session": bool(valid), "is_open": bool(valid and opened <= clock < closed),
        "session_date": str(day.date()) if valid else None, "open_at": iso(opened), "close_at": iso(closed),
        "previous_session": str(previous.date()), "next_session": str(following.date()),
        "previous_open_at": iso(cal.session_open(previous).to_pydatetime()),
        "previous_close_at": iso(cal.session_close(previous).to_pydatetime()),
        "next_open_at": iso(cal.session_open(upcoming).to_pydatetime()),
        "next_close_at": iso(cal.session_close(upcoming_close).to_pydatetime()),
        "early_close": bool(valid and closed.astimezone(NY).hour < 16),
        "source": "exchange_calendars XNYS",
    }


class AlpacaPaper:
    """No configurable broker URL and no live endpoint code path."""
    def __init__(self, key, secret, record=None, transport=None):
        self._headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        self._transport = transport or _request
        self._record = record or (lambda *args: None)
        self._validated = False
        self._account = None

    def _call(self, method, path, payload=None, *, data=False):
        try:
            result = self._transport(method, (DATA_URL if data else PAPER_URL) + path, payload, self._headers)
            self._record("broker" if not data else "market_data", True, None)
            return result
        except ProviderError as exc:
            self._record("broker" if not data else "market_data", False, str(exc))
            raise
        except Exception:
            self._record("broker" if not data else "market_data", False, "Paper provider request failed")
            raise ProviderError("Paper provider request failed") from None

    def account(self):
        account = self._call("GET", "/v2/account")
        if not isinstance(account, dict) or account.get("status") != "ACTIVE" or not str(account.get("account_number", "")).startswith("PA"):
            self._record("broker", False, "An active paper account is required")
            raise ProviderError("An active paper account is required")
        self._validated = True
        self._account = account
        return account

    def positions(self):
        return self._call("GET", "/v2/positions")

    def orders(self):
        # A newest-500 historical window is not an open-order census: an old
        # foreign order can remain live after hundreds of later fills. Read the
        # full bounded open set independently before merging recent history.
        params = {"nested": "true", "limit": 500, "direction": "desc"}
        opened = self._call("GET", "/v2/orders?" + urlencode({"status": "open", **params}))
        if not isinstance(opened, list) or len(opened) >= 500:
            raise ProviderError("Paper open-order census is incomplete or exceeded its safe bound")
        recent = self._call("GET", "/v2/orders?" + urlencode({"status": "all", **params}))
        if not isinstance(recent, list):
            raise ProviderError("Paper order history is invalid")
        merged = {}
        for order in [*opened, *recent]:
            if not isinstance(order, dict) or not isinstance(order.get("id"), str) or not order["id"]:
                raise ProviderError("Paper order census contains an invalid identity")
            merged[order["id"]] = order
        return list(merged.values())

    def get_order(self, client_id=None, **kwargs):
        client_id = client_id or kwargs.get("client_order_id")
        if not client_id:
            raise DeskError("Broker lookup requires a client ID", 422)
        try:
            return self._call("GET", "/v2/orders:by_client_order_id?" + urlencode({"client_order_id": client_id}))
        except ProviderError as exc:
            if exc.status == 404:
                # A valid not-found read is distinct from an unavailable provider.
                self._record("broker", True, None)
                return None
            raise

    def submit(self, intent):
        if not self._validated:
            self.account()
        if self._account.get("trading_blocked") or self._account.get("account_blocked"):
            raise ProviderError("Paper account is blocked from trading")
        client_id = intent.get("client_order_id") or intent.get("client_id")
        if not isinstance(client_id, str) or not client_id or len(client_id) > 48:
            raise DeskError("A stable broker client ID of at most 48 characters is required", 422)
        order = {"symbol": symbol(intent["symbol"]), "side": intent["side"], "qty": str(intent.get("quantity", intent.get("qty"))),
                 "type": intent.get("order_type", intent.get("type", "market")), "time_in_force": intent.get("time_in_force", "day"),
                 "client_order_id": client_id}
        for field in ("limit_price", "stop_price"):
            if intent.get(field) is not None:
                order[field] = str(intent[field])
        for field, price_field in (("take_profit", "limit_price"), ("stop_loss", "stop_price")):
            value = intent.get(field)
            if value is not None:
                order[field] = {k: str(v) for k, v in value.items() if k in {"limit_price", "stop_price"}} if isinstance(value, dict) else {price_field: str(value)}
        if "take_profit" in order or "stop_loss" in order:
            order["order_class"] = "bracket" if "take_profit" in order and "stop_loss" in order else "oto"
        # POST is attempted once. TradingDesk resolves ambiguous delivery by ID.
        return self._call("POST", "/v2/orders", order)

    def cancel(self, order_id):
        if not order_id:
            raise DeskError("Broker cancellation requires an order ID", 422)
        return self._call("DELETE", "/v2/orders/" + quote(str(order_id), safe=""))

    def latest_trade(self, sym):
        data = self._call("GET", "/v2/stocks/" + quote(sym, safe="") + "/trades/latest?feed=iex", data=True)
        trade = data.get("trade") or {}
        if not trade.get("t") or not trade.get("p"):
            raise ProviderError("Paper data provider returned no timestamped trade")
        return Decimal(str(trade["p"])), utc_clock(trade["t"]), "Alpaca IEX last trade (provider timestamp)"


class Providers:
    MAX_SYMBOLS = 16
    MAX_BARS = 50000
    MAX_VENDOR_PAGES = 3

    def __init__(self, store, transport=None, csv_transport=None):
        self.store = store
        self.kind = os.environ.get("ASTER_MARKET_DATA", "yahoo").strip().lower()
        if self.kind not in {"manual", "yahoo", "alpaca"}:
            raise DeskError("ASTER_MARKET_DATA must be manual, yahoo or alpaca", 422)
        self._transport = transport or _request
        # An injected test adapter cannot unexpectedly fall through to a network.
        self._csv_transport = csv_transport or (_csv_request if transport is None else _unconfigured_csv)
        fallback = os.environ.get("ASTER_BAR_FALLBACK", "stooq").strip().lower()
        if fallback not in {"none", "stooq"}:
            raise DeskError("ASTER_BAR_FALLBACK must be none or stooq", 422)
        self.bar_fallbacks = [] if fallback == "none" else [fallback]
        self._mutex = threading.RLock()
        self._pending_state = {}
        with store.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS a_provider_state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_bar_cache(symbol TEXT,range TEXT,interval TEXT,provider TEXT,fetched_at TEXT,data TEXT,
                    PRIMARY KEY(symbol,range,interval,provider));
                CREATE TABLE IF NOT EXISTS a_quote_history(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,provider TEXT NOT NULL,
                    provider_asof TEXT NOT NULL,observed_at TEXT NOT NULL,price TEXT NOT NULL,source TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL UNIQUE,accepted INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS a_quote_history_asof ON a_quote_history(symbol,observed_at,provider_asof);
                CREATE TABLE IF NOT EXISTS a_bar_revisions(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,range TEXT NOT NULL,
                    interval TEXT NOT NULL,provider TEXT NOT NULL,provider_asof TEXT,observed_at TEXT NOT NULL,fetched_at TEXT NOT NULL,
                    source TEXT NOT NULL,adjustment TEXT NOT NULL,content_sha256 TEXT NOT NULL UNIQUE,data TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS a_bar_revisions_asof ON a_bar_revisions(symbol,observed_at,provider_asof);
            """)
        aliases = [name.strip() for name in os.environ.get("ASTER_ALPACA_ACCOUNTS", "").split(",") if name.strip()]
        if len(aliases) > 8 or len(set(aliases)) != len(aliases) or any(not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", name) or name == "default" for name in aliases):
            raise DeskError("ASTER_ALPACA_ACCOUNTS supports up to 8 unique named account aliases; default is reserved", 422)
        self.account_aliases = ["default", *aliases]
        self.brokers = {}
        for alias in self.account_aliases:
            prefix = "ASTER_ALPACA" if alias == "default" else "ASTER_ALPACA_" + alias.upper()
            key, secret = os.environ.get(prefix + "_KEY", ""), os.environ.get(prefix + "_SECRET", "")
            if key and secret:
                def record(component, success, error, connection=alias):
                    self._record("broker" if connection == "default" and component == "broker" else "broker:" + connection if component == "broker" else component, success, error)
                self.brokers[alias] = AlpacaPaper(key, secret, record, self._transport)
        self.broker = self.brokers.get("default")
        self.historical_adapters = {
            "yahoo": {"fetch": self._yahoo_bars, "intervals": BAR_INTERVALS, "historical_only": False},
            "alpaca": {"fetch": self._alpaca_bars, "intervals": BAR_INTERVALS, "historical_only": False},
            "stooq": {"fetch": self._stooq_bars, "intervals": {"1d"}, "historical_only": True},
        }

    def register_historical_adapter(self, name, fetch, intervals):
        """Trusted-code extension point, never a model/API mutation tool."""
        intervals = set(intervals)
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", name) or not callable(fetch) or not intervals or not intervals <= BAR_INTERVALS:
            raise ValueError("A named historical adapter with known intervals is required")
        self.historical_adapters[name] = {"fetch": fetch, "intervals": intervals, "historical_only": True}

    def broker_for(self, connection_id="default"):
        # Missing aliases cannot silently send to the default account.
        return self.brokers.get(connection_id)

    def _record(self, component, success, error):
        # Broker lookup may be called while TradingDesk owns a SQLite write
        # transaction. Status telemetry must never deadlock the order journal.
        with self._mutex:
            state = dict(self._pending_state.get(component, {}))
            if not state:
                with self.store.connect() as con:
                    row = con.execute("SELECT value FROM a_provider_state WHERE key=?", (component,)).fetchone()
                    state = json.loads(row[0]) if row else {}
            state.update({"connected": bool(success), "last_attempt_at": datetime.now(UTC).isoformat(), "last_error": error})
            if success:
                state["last_success_at"] = state["last_attempt_at"]
            self._pending_state[component] = state
            self._flush_state()

    def _flush_state(self):
        with self._mutex:
            if not self._pending_state:
                return
            con = self.store.connect()
            try:
                con.execute("PRAGMA busy_timeout=0")
                con.execute("BEGIN IMMEDIATE")
                for component, state in self._pending_state.items():
                    con.execute("INSERT OR REPLACE INTO a_provider_state VALUES(?,?)", (component, json.dumps(state)))
                con.commit()
                self._pending_state.clear()
            except sqlite3.OperationalError:
                con.rollback()
            finally:
                con.close()

    def status(self):
        self._flush_state()
        with self.store.connect() as con:
            states = {r["key"]: json.loads(r["value"]) for r in con.execute("SELECT * FROM a_provider_state")}
        with self._mutex:
            states.update(self._pending_state)
        result = {}
        for key, kind, configured in (("market_data", self.kind, self.kind != "alpaca" or self.broker is not None), ("broker", "alpaca-paper", self.broker is not None)):
            item = states.get(key, {})
            success = item.get("last_success_at")
            recent = bool(success and (datetime.now(UTC) - utc_clock(success)).total_seconds() < 300)
            result[key] = {**item, "kind": kind, "configured": configured, "connected": bool(configured and item.get("connected") and recent)}
        result["market_data"]["delayed"] = self.kind == "yahoo"
        result["market_data"]["description"] = {"manual": "Operator-supplied observations", "yahoo": "Yahoo Finance public data; may be delayed", "alpaca": "Alpaca IEX timestamped data"}[self.kind]
        result["broker"]["paper_only"] = True
        accounts = []
        for alias in self.account_aliases:
            item = states.get("broker" if alias == "default" else "broker:" + alias, {})
            success = item.get("last_success_at")
            recent = bool(success and (datetime.now(UTC) - utc_clock(success)).total_seconds() < 300)
            accounts.append({**item, "connection_id": alias, "configured": alias in self.brokers, "connected": bool(alias in self.brokers and item.get("connected") and recent), "paper_only": True})
        result["broker"]["accounts"] = accounts
        result["broker"]["connection_ids"] = list(self.brokers)
        historical = []
        for name, adapter in self.historical_adapters.items():
            item = states.get("bars:" + name, {})
            success = item.get("last_success_at")
            recent = bool(success and (datetime.now(UTC) - utc_clock(success)).total_seconds() < 300)
            historical.append({**item, "provider": name, "configured": name != "alpaca" or self.broker is not None, "enabled": name == self.kind or self.kind == "yahoo" and name in self.bar_fallbacks, "connected": bool(item.get("connected") and recent), "intervals": sorted(adapter["intervals"]), "historical_only": adapter["historical_only"]})
        result["historical_data"] = {"primary": self.kind, "fallbacks": self.bar_fallbacks if self.kind == "yahoo" else [], "adapters": historical, "daily_bars_are_executable_quotes": False}
        return result

    def calendar(self, clock=None):
        return exchange_calendar(clock)

    @staticmethod
    def quote_observation(con, sym, price, timestamp, source, provider, accepted=True):
        """Append content identity once; observation time is never backdated."""
        payload = {"symbol": sym, "provider": provider, "provider_asof": utc_clock(timestamp).isoformat(), "price": str(Decimal(str(price))), "source": source}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        con.execute("INSERT OR IGNORE INTO a_quote_history VALUES(?,?,?,?,?,?,?,?,?)", (digest, sym, provider, payload["provider_asof"], datetime.now(UTC).isoformat(), payload["price"], source, digest, int(accepted)))
        return digest

    def capture_quotes(self):
        """Record current operator marks when no ingestion hook is installed."""
        with self.store.transaction() as con:
            for row in con.execute("SELECT * FROM quotes").fetchall():
                source = row["source"]
                if not con.execute("SELECT 1 FROM a_quote_history WHERE symbol=? AND provider_asof=? AND price=? AND source=?", (row["symbol"], row["as_of"], row["price"], source)).fetchone():
                    self.quote_observation(con, row["symbol"], row["price"], row["as_of"], source, "stored quote")

    def observations(self, sym, as_of=None, limit=100):
        """A knowledge-time view; old bars are not evidence of past availability."""
        sym, cutoff = symbol(sym), utc_clock(as_of).isoformat()
        limit = max(1, min(int(limit), 500))
        with self.store.connect() as con:
            quotes = [dict(r) for r in con.execute("SELECT * FROM a_quote_history WHERE symbol=? AND observed_at<=? AND provider_asof<=? ORDER BY observed_at DESC LIMIT ?", (sym, cutoff, cutoff, limit))]
            revisions = [dict(r) for r in con.execute("SELECT * FROM a_bar_revisions WHERE symbol=? AND observed_at<=? AND (provider_asof IS NULL OR provider_asof<=?) ORDER BY observed_at DESC LIMIT ?", (sym, cutoff, cutoff, min(limit, 50)))]
        for row in quotes:
            row["accepted"] = bool(row["accepted"])
        for row in revisions:
            row["data"] = self._revision(row["id"])[1]
        return {"symbol": sym, "knowledge_as_of": cutoff, "quotes": quotes, "bar_revisions": revisions, "scope": "Only data observed by this desk by the cutoff; vendor revisions are retained. No historical availability is inferred."}

    def _yahoo(self, sym, range, interval, *, start_at=None):
        url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(sym.replace(".", "-"), safe="")
        # Yahoo's range=max can silently coarsen daily requests to monthly.
        # Explicit epoch boundaries retain the requested bar interval.
        params = {"interval": interval, "includePrePost": "false"}
        if start_at is not None:
            params.update({"period1": int(utc_clock(start_at).timestamp()),
                           "period2": int(datetime.now(UTC).timestamp())})
        elif range == "max":
            params.update({"period1": -2208988800, "period2": int(datetime.now(UTC).timestamp())})
        elif interval == "1wk":
            # Named ranges start midweek and Yahoo labels the clipped first
            # aggregate as a whole week. Request from New York Monday midnight
            # so every completed supplied week has its full exchange sessions.
            now = datetime.now(UTC)
            first_day = now.astimezone(NY).date() - timedelta(days=BAR_DAYS[range])
            monday = first_day - timedelta(days=first_day.weekday())
            params.update({"period1": int(datetime.combine(monday, datetime.min.time(), NY).timestamp()),
                           "period2": int(now.timestamp())})
        else:
            params["range"] = range
        result = self._transport("GET", url + "?" + urlencode(params), None, None)
        if not isinstance(result, dict) or not isinstance(result.get("chart"), dict):
            raise ProviderError("Public market provider returned invalid chart data")
        chart = result["chart"]
        rows = chart.get("result") or []
        if chart.get("error") or not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise ProviderError("Public market provider returned no data for this symbol")
        if start_at is not None:
            return {**rows[0], "_desk_request_window": {"start": datetime.fromtimestamp(params["period1"], UTC).isoformat(),
                     "end": datetime.fromtimestamp(params["period2"], UTC).isoformat(),
                     "anchor": "Opening of last verified completed native bar; overlap retained, no gap repair"}}
        if interval == "1wk" and range != "max":
            return {**rows[0], "_desk_request_window": {"start": datetime.fromtimestamp(params["period1"], UTC).isoformat(),
                     "end": datetime.fromtimestamp(params["period2"], UTC).isoformat(),
                     "anchor": "Monday 00:00 America/New_York; complete native-week query boundary"}}
        return rows[0]

    def refresh(self, symbols):
        symbols = sorted({symbol(s) for s in symbols})
        if len(symbols) > self.MAX_SYMBOLS:
            raise DeskError(f"Refresh is limited to {self.MAX_SYMBOLS} symbols per pass", 422)
        if self.kind == "manual":
            return {"provider": "manual", "quotes": [], "errors": [], "refreshed": 0, "description": "No external fetch configured"}
        quotes, errors = [], []
        for sym in symbols:
            try:
                if self.kind == "alpaca":
                    if self.broker is None:
                        raise ProviderError("Alpaca data credentials are not configured")
                    price, timestamp, source = self.broker.latest_trade(sym)
                else:
                    chart = self._yahoo(sym, "1d", "1m")
                    meta = chart.get("meta") or {}
                    if not meta.get("regularMarketTime") or not meta.get("regularMarketPrice"):
                        raise ProviderError("Public provider returned no timestamped quote")
                    price = Decimal(str(meta["regularMarketPrice"]))
                    timestamp = datetime.fromtimestamp(meta["regularMarketTime"], UTC)
                    source = "Yahoo Finance quote (provider timestamp; may be delayed)"
                accepted = False
                try:
                    quotes.append(self.store.ingest_quote(sym, price, timestamp, source, provider=self.kind))
                    accepted = True
                finally:
                    if price.is_finite() and price > 0 and (timestamp - datetime.now(UTC)).total_seconds() <= 5:
                        with self.store.transaction() as con:
                            self.quote_observation(con, sym, price, timestamp, source, self.kind, accepted)
                self._record("market_data", True, None)
            except (ProviderError, DeskError, ValueError, TypeError, KeyError, AttributeError, ArithmeticError, OSError):
                # Preserve prior quote truth and do not leak transport details.
                error = "Provider quote could not be fetched or accepted; saved quote retained"
                errors.append({"symbol": sym, "error": error})
                self._record("market_data", False, error)
        return {"provider": self.kind, "quotes": quotes, "errors": errors, "refreshed": len(quotes)}

    def _yahoo_bars(self, sym, range, interval, *, start_at=None):
        chart = self._yahoo(sym, range, interval, start_at=start_at) if start_at is not None else self._yahoo(sym, range, interval)
        vendor_meta = chart.get("meta") or {}
        vendor_interval = vendor_meta.get("dataGranularity")
        if vendor_interval is not None and vendor_interval != interval and {vendor_interval, interval} != {"1h", "60m"}:
            raise ProviderError("Historical provider changed the requested bar interval")
        q = (chart.get("indicators", {}).get("quote") or [{}])[0]
        adjusted = (chart.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose", [])
        bars, omitted_bar_rows = [], []
        timestamps = chart.get("timestamp") or []
        for i, timestamp in enumerate(timestamps):
            values = {field: q.get(field, [])[i] if i < len(q.get(field, [])) else None for field in ("open", "high", "low", "close", "volume")}
            valid_prices = all(values[f] is not None and math.isfinite(float(values[f])) and float(values[f]) > 0 for f in ("open", "high", "low", "close"))
            consistent_prices = valid_prices and float(values["low"]) <= min(float(values["open"]), float(values["close"])) and float(values["high"]) >= max(float(values["open"]), float(values["close"])) and float(values["low"]) <= float(values["high"])
            if consistent_prices:
                if i < len(adjusted) and adjusted[i] is not None and math.isfinite(float(adjusted[i])):
                    values["adjusted_close"] = adjusted[i]
                bars.append({"timestamp": datetime.fromtimestamp(timestamp, UTC).isoformat(), **values})
            else:
                # Keep the precise unavailable/inconsistent source row. Consumers may only
                # excuse an omission after proving that its native candle had
                # not completed at the actual fetch and decision clocks.
                omitted_bar_rows.append({"row_index": i,
                    "timestamp": datetime.fromtimestamp(timestamp, UTC).isoformat(), **values})
        result = {"provider": "yahoo", "source": "Yahoo Finance historical bars", "adjustment": "Yahoo adjusted_close as supplied; vendor OHLC retained without desk adjustments", "bars": bars, "truncated": len(bars) > self.MAX_BARS, "omitted_rows": len(timestamps) - len(bars), "vendor_interval": vendor_interval, "timestamp_semantics": "Vendor bar timestamp, not publication time"}
        if omitted_bar_rows:
            result["omitted_bar_rows"] = omitted_bar_rows
            result["source_row_count"] = len(timestamps)
        if chart.get("_desk_request_window"):
            result["request_window"] = chart["_desk_request_window"]
        regular_time = vendor_meta.get("regularMarketTime")
        if type(regular_time) is int and 0 < regular_time < 4_102_444_800:
            # The weekly endpoint can append a daily aggregate at this exact
            # quote clock. Retain both the untouched row and explicit vendor
            # marker; native consumers can quarantine that supplemental row.
            result["vendor_regular_market_timestamp"] = datetime.fromtimestamp(regular_time, UTC).isoformat()
        return result

    def _stooq_bars(self, sym, range, interval):
        if interval != "1d":
            raise ProviderError("Stooq fallback supports daily historical bars only")
        end = datetime.now(UTC).date()
        start = end - timedelta(days=BAR_DAYS[range]) if BAR_DAYS[range] is not None else datetime(1900, 1, 1).date()
        params = {"s": sym.lower().replace(".", "-") + ".us", "i": "d", "d1": start.strftime("%Y%m%d"), "d2": end.strftime("%Y%m%d")}
        text = self._csv_transport("https://stooq.com/q/d/l/?" + urlencode(params))
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or not {"Date", "Open", "High", "Low", "Close"} <= set(reader.fieldnames):
            raise ProviderError("Stooq returned no usable historical CSV")
        bars, omitted = [], 0
        for row in reader:
            date = datetime.strptime(row["Date"], "%Y-%m-%d").date()
            if not start <= date <= end:
                omitted += 1
                continue
            values = {field.lower(): float(row[field]) for field in ("Open", "High", "Low", "Close")}
            if not all(math.isfinite(v) and v > 0 for v in values.values()):
                omitted += 1
                continue
            volume = float(row["Volume"]) if row.get("Volume") else None
            if volume is not None and (not math.isfinite(volume) or volume < 0):
                omitted += 1
                continue
            bars.append({"timestamp": datetime.combine(date, datetime.min.time(), UTC).isoformat(), **values, "volume": volume})
        if not bars:
            raise ProviderError("Stooq returned no bars for the requested window")
        return {"provider": "stooq", "source": "Stooq daily historical CSV (US equity symbol)", "adjustment": "Stooq vendor adjustment policy unspecified; no desk adjustments", "return_scope": "close-price return; Stooq dividend and split adjustment policy unspecified", "bars": sorted(bars, key=lambda b: b["timestamp"]), "truncated": len(bars) > self.MAX_BARS, "omitted_rows": omitted, "vendor_interval": "1d", "timestamp_semantics": "Provider session date labelled 00:00 UTC; not a trade or publication timestamp", "fallback_from": "yahoo"}

    def _alpaca_bars(self, sym, range, interval, *, params=None, prefix=None):
        if self.broker is None:
            raise ProviderError("Alpaca data credentials are not configured")
        timeframe = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "30m": "30Min", "60m": "1Hour", "1d": "1Day", "1wk": "1Week", "1mo": "1Month"}[interval]
        days = BAR_DAYS[range]
        start = (datetime.now(UTC) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0) if days is not None else datetime(2000, 1, 1, tzinfo=UTC)
        params = dict(params or {"timeframe": timeframe, "start": start.isoformat(), "feed": "iex", "limit": 1000, "adjustment": "raw"})
        bars, token = list(prefix or []), params.get("page_token")
        seen = {token} if token else set()
        for _ in builtins.range(self.MAX_VENDOR_PAGES):
            raw = self.broker._call("GET", "/v2/stocks/" + sym + "/bars?" + urlencode(params), data=True)
            bars.extend({"timestamp": utc_clock(b["t"]).isoformat(), "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"], "volume": b["v"]} for b in raw.get("bars", []))
            token = raw.get("next_page_token")
            if not token or len(bars) >= self.MAX_BARS:
                break
            if token in seen or not isinstance(token, str) or len(token) > 4096:
                raise ProviderError("Historical pagination token is inconsistent")
            seen.add(token)
            params["page_token"] = token
        continuation = {**params, "page_token": token} if token and len(bars) < self.MAX_BARS else None
        return {"provider": "alpaca", "source": "Alpaca IEX bars", "adjustment": "raw Alpaca IEX OHLC", "bars": bars, "truncated": bool(token) or len(bars) > self.MAX_BARS, "vendor_continuation": continuation, "omitted_rows": 0, "vendor_interval": interval, "timestamp_semantics": "Vendor bar timestamp, not publication time"}

    def _save_bars(self, sym, range, interval, content):
        supplied = content["bars"]
        if not isinstance(supplied, list) or not supplied:
            raise ProviderError("Historical data returned no usable bars")
        bars = [{**b, "timestamp": utc_clock(b["timestamp"]).isoformat()} for b in supplied[:self.MAX_BARS]]
        content = {**content, "truncated": bool(content.get("truncated") or len(supplied) > self.MAX_BARS)}
        if any(utc_clock(b["timestamp"]) > datetime.now(UTC) + timedelta(seconds=5) for b in bars):
            raise ProviderError("Historical data contains a future timestamp")
        if any(not all(math.isfinite(float(b[f])) and float(b[f]) > 0 for f in ("open", "high", "low", "close")) for b in bars):
            raise ProviderError("Historical data contains invalid prices")
        if any(float(b["low"]) > min(float(b["open"]), float(b["close"])) or float(b["high"]) < max(float(b["open"]), float(b["close"])) or float(b["low"]) > float(b["high"]) for b in bars):
            raise ProviderError("Historical data contains inconsistent OHLC prices")
        if any(b.get("volume") is not None and (not math.isfinite(float(b["volume"])) or float(b["volume"]) < 0) for b in bars):
            raise ProviderError("Historical data contains invalid volume")
        if any(b.get("adjusted_close") is not None and (not math.isfinite(float(b["adjusted_close"])) or float(b["adjusted_close"]) <= 0) for b in bars):
            raise ProviderError("Historical data contains an invalid adjusted price")
        if len({b["timestamp"] for b in bars}) != len(bars):
            raise ProviderError("Historical data contains duplicate bar timestamps")
        bars = sorted(bars, key=lambda b: b["timestamp"])
        content = {**content, "symbol": sym, "range": range, "interval": interval, "bars": bars, "finality": "provisional_vendor_observation", "completeness": {"status": "bounded_partial" if content.get("truncated") or content.get("omitted_rows") else "complete_vendor_response", "exchange_coverage": "not independently certified", "omitted_rows": content.get("omitted_rows", 0), "vendor_continuation_available": bool(content.get("vendor_continuation")), "maximum_bars_per_revision": self.MAX_BARS}}
        fetched = datetime.now(UTC).isoformat()
        digest = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        provider_asof = bars[-1]["timestamp"] if bars else None
        result = {**content, "fetched_at": fetched, "provider_asof": provider_asof, "observed_at": fetched, "revision_id": digest, "content_sha256": digest, "cached": False, "stale_cache": False}
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO a_bar_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (digest, sym, range, interval, content["provider"], provider_asof, fetched, fetched, content["source"], content["adjustment"], digest, json.dumps(content)))
            stored = con.execute("SELECT * FROM a_bar_revisions WHERE id=?", (digest,)).fetchone()
            self._validated_revision(stored, digest)
            result["observed_at"] = stored["observed_at"]
            con.execute("INSERT OR REPLACE INTO a_bar_cache VALUES(?,?,?,?,?,?)", (sym, range, interval, self.kind, fetched, json.dumps(result)))
        return result

    def _cached_bars(self, row, sym, range, interval):
        """The cache stores recency; verified immutable content supplies truth."""
        cached = json.loads(row["data"])
        receipt, content = self._revision(cached.get("revision_id"))
        if (receipt["symbol"], receipt["range"], receipt["interval"]) != (sym, range, interval):
            raise ProviderError("Historical cache identity is inconsistent")
        fetched = utc_clock(row["fetched_at"])
        if fetched > datetime.now(UTC) + timedelta(seconds=5):
            raise ProviderError("Historical cache recency is invalid")
        return {**content, "fetched_at": fetched.isoformat(), "provider_asof": receipt["provider_asof"], "observed_at": receipt["observed_at"], "revision_id": receipt["id"], "content_sha256": receipt["content_sha256"], "cached": True, "stale_cache": False}

    def bars(self, sym, range="1mo", interval="1d"):
        sym = symbol(sym)
        if range not in BAR_DAYS or interval not in BAR_INTERVALS:
            raise DeskError("Unsupported bar range or interval", 422)
        with self.store.connect() as con:
            cached = con.execute("SELECT * FROM a_bar_cache WHERE symbol=? AND range=? AND interval=? AND provider=?", (sym, range, interval, self.kind)).fetchone()
        saved = None
        if cached:
            try:
                saved = self._cached_bars(cached, sym, range, interval)
            except (DeskError, ProviderError, ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                # Corrupt/unverifiable data cannot be used as a stale fallback.
                self._record("bars:" + self.kind, False, "Historical cache integrity could not be verified")
        if saved and (datetime.now(UTC) - utc_clock(saved["fetched_at"])).total_seconds() < 60:
            return saved
        candidates = [self.kind] + (self.bar_fallbacks if self.kind == "yahoo" else [])
        for name in candidates:
            adapter = self.historical_adapters.get(name)
            if adapter is None or interval not in adapter["intervals"]:
                continue
            try:
                content = adapter["fetch"](sym, range, interval)
                if content.get("provider") != name:
                    raise ProviderError("Historical adapter returned inconsistent source identity")
                result = self._save_bars(sym, range, interval, content)
                self._record("bars:" + name, True, None)
                if name == self.kind:
                    self._record("market_data", True, None)
                return result
            except (ProviderError, DeskError, KeyError, ValueError, TypeError, IndexError, AttributeError, ArithmeticError, OSError):
                self._record("bars:" + name, False, "Historical data read failed")
                if name == self.kind:
                    self._record("market_data", False, "Primary historical data read failed")
        if saved:
            return {**saved, "stale_cache": True, "error": "Historical data read failed; showing saved bars"}
        raise ProviderError("Historical data is unavailable; no fabricated bars") from None

    def native_bars_since(self, sym, start_at, interval="60m"):
        """Fetch the verified-prefix overlap and all subsequent vendor rows.

        Only the existing Yahoo hourly source is supported. Genuine completed
        omissions remain in the revision and are rejected by native validation.
        A stale or foreign-source cache never authorizes native decisions.
        """
        sym = symbol(sym)
        if not isinstance(start_at, (datetime_types.datetime, str)):
            raise DeskError("Explicit aware native query anchor required", 422)
        anchor, now = utc_clock(start_at), datetime.now(UTC)
        if self.kind != "yahoo" or interval != "60m":
            raise DeskError("Incremental native reads require Yahoo hourly bars", 422)
        if not now - timedelta(days=732) <= anchor <= now:
            raise DeskError("Native query anchor is outside the supported past window", 422)
        cache_range = "since:" + str(int(anchor.timestamp()))
        def validate_identity(content):
            window = content.get("request_window") or {}
            if content.get("provider") != "yahoo" or content.get("vendor_interval") not in {"60m", "1h"} or not window.get("start") or utc_clock(window["start"]) != anchor:
                raise ProviderError("Native source or request-window identity differs from its verified anchor")
            return content
        with self.store.connect() as con:
            cached = con.execute("SELECT * FROM a_bar_cache WHERE symbol=? AND range=? AND interval=? AND provider=?",
                                 (sym, cache_range, interval, self.kind)).fetchone()
        if cached:
            try:
                saved = validate_identity(self._cached_bars(cached, sym, cache_range, interval))
                if (now - utc_clock(saved["fetched_at"])).total_seconds() < 60:
                    return saved
            except (DeskError, ProviderError, ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                self._record("bars:yahoo", False, "Native cache integrity could not be verified")
        try:
            content = validate_identity(self._yahoo_bars(sym, cache_range, interval, start_at=anchor))
            result = self._save_bars(sym, cache_range, interval, content)
            self._record("bars:yahoo", True, None)
            self._record("market_data", True, None)
            return result
        except (ProviderError, DeskError, KeyError, ValueError, TypeError, IndexError, AttributeError, ArithmeticError, OSError):
            self._record("bars:yahoo", False, "Incremental native data read failed")
            raise ProviderError("Incremental native data is unavailable; no stale or fabricated bars") from None

    def _revision(self, revision_id):
        if not isinstance(revision_id, str) or not re.fullmatch(r"[a-f0-9]{64}", revision_id):
            raise DeskError("A valid immutable bar revision ID is required", 422)
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM a_bar_revisions WHERE id=?", (revision_id,)).fetchone()
        if row is None:
            raise DeskError("Bar revision not found", 404)
        return dict(row), self._validated_revision(row, revision_id)

    @staticmethod
    def _validated_revision(row, revision_id):
        try:
            content = json.loads(row["data"])
            if not isinstance(content, dict):
                raise ValueError("Invalid revision content")
            digest = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        except (ValueError, TypeError):
            raise DeskError("Bar revision integrity check failed; data is unavailable", 503) from None
        if digest != row["content_sha256"] or digest != revision_id:
            raise DeskError("Bar revision integrity check failed; data is unavailable", 503)
        if any(content.get(field) != row[field] for field in ("symbol", "range", "interval", "provider", "source", "adjustment")) or row["provider_asof"] != (content["bars"][-1]["timestamp"] if content.get("bars") else None):
            raise DeskError("Bar revision identity check failed; data is unavailable", 503)
        return content

    def bar_manifest(self, revision_id):
        receipt, content = self._revision(revision_id)
        bars = content.get("bars", [])
        return {"revision_id": revision_id, **{k: receipt[k] for k in ("symbol", "range", "interval", "provider", "source", "provider_asof", "observed_at", "fetched_at", "adjustment", "content_sha256")}, "bar_count": len(bars), "from_at": bars[0]["timestamp"] if bars else None, "through_at": bars[-1]["timestamp"] if bars else None, "finality": content.get("finality", "provisional_vendor_observation"), "vendor_interval": content.get("vendor_interval"), "timestamp_semantics": content.get("timestamp_semantics", "Vendor bar label; not publication time"), "completeness": content.get("completeness", {"status": "bounded_partial" if content.get("truncated") else "complete_vendor_response", "exchange_coverage": "not independently certified"}), "vendor_continuation_available": bool(content.get("vendor_continuation")), "immutable": True, "scope": "Snapshot of data observed by this desk; vendor revisions and incomplete exchange coverage remain possible"}

    def bar_page(self, revision_id, cursor=None, limit=500):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise DeskError("Bar page limit must be 1 to 1000", 422)
        receipt, content = self._revision(revision_id)
        offset = 0
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or len(cursor) > 512:
                    raise ValueError()
                decoded = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                offset = decoded["offset"]
                if decoded["revision_id"] != revision_id or isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= len(content["bars"]):
                    raise ValueError()
            except (ValueError, TypeError, KeyError, UnicodeError):
                raise DeskError("Bar cursor does not belong to this immutable revision", 422) from None
        end = min(offset + limit, len(content["bars"]))
        next_cursor = base64.urlsafe_b64encode(json.dumps({"revision_id": revision_id, "offset": end}, separators=(",", ":")).encode()).decode().rstrip("=") if end < len(content["bars"]) else None
        return {"revision_id": revision_id, "content_sha256": receipt["content_sha256"], "symbol": receipt["symbol"], "provider": receipt["provider"], "source": receipt["source"], "offset": offset, "limit": limit, "total_bars": len(content["bars"]), "bars": content["bars"][offset:end], "next_cursor": next_cursor, "finality": content.get("finality", "provisional_vendor_observation"), "immutable": True}

    def continue_bars(self, revision_id):
        receipt, content = self._revision(revision_id)
        continuation = content.get("vendor_continuation")
        if not continuation:
            return {"manifest": self.bar_manifest(revision_id), "continued": False}
        if content["provider"] != "alpaca" or self.kind != "alpaca" or self.broker is None:
            raise DeskError("The revision's configured historical provider is unavailable")
        try:
            extended = self._alpaca_bars(receipt["symbol"], receipt["range"], receipt["interval"], params=continuation, prefix=content["bars"])
            result = self._save_bars(receipt["symbol"], receipt["range"], receipt["interval"], extended)
        except (ProviderError, DeskError, KeyError, ValueError, TypeError, IndexError, AttributeError, ArithmeticError, OSError):
            self._record("bars:alpaca", False, "Historical continuation failed; immutable revision preserved")
            raise ProviderError("Historical continuation failed; immutable revision preserved") from None
        self._record("bars:alpaca", True, None)
        return {"manifest": self.bar_manifest(result["revision_id"]), "previous_revision_id": revision_id, "continued": True}
