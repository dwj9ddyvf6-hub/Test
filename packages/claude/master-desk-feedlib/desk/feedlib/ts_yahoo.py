"""The Ausar desk's Yahoo native-bar and quote provider for the Tensor state-repair books — a port of the source's
backend/providers.py Providers._yahoo / _yahoo_bars / _save_bars / _cached_bars / bars / native_bars_since /
refresh (kind "yahoo"; the Stooq fallback serves daily bars only and never these 60m / 1wk frames). The payload
each read returns is the source's: the vendor rows with their raw indices, the omitted-row evidence, the
native identity, the vendor regular-session metadata and regular-market clock, then the immutable revision
(content_sha256 == revision_id over the canonical content, first observation time, fetch time) that
tensor_runtime.canonical_native_bars validates. Quotes are the chart's regularMarketPrice at regularMarketTime,
stored under the source store's ingest rules (no older quote replaces a newer one).

Named divergences:
  * transport: the source's providers._request sent each GET unpaced (one attempt, 8-second deadline) from the
    runtime's 32 concurrent readers; here each GET goes through the desk's shared HTTP client (desk.data.http: the
    per-host rate ledger every desk process shares, the job's bulk lane that yields Yahoo to the trading loop, the
    circuit breaker that pauses a refusing host) with one attempt and the same 8-second deadline - a refused or
    paused read is the source's ProviderError, which the runtime records and retries;
  * the provider's wall clock is the desk clock (the same instant live; tests inject one);
  * revisions and the 60-second read cache live in the state books' own sqlite store (the source's
    bar_revision_codec compression of stored revisions is not used - the stored content and its hash are the same
    JSON);
  * vendor placeholders: a row whose open, high, low and close are all missing in a native period that had completed
    when it was fetched is Yahoo's placeholder for a period it holds no prints for, not a bar and not an omission:
    it is left out of the payload (its stamps kept as evidence, desk_vendor_placeholders) and the rows that remain
    are indexed as the response. The source took its two-year prefix from a reconstructed research seed and asked
    Yahoo only for the bars after it; Yahoo's own two-year hourly history carries such rows at 12:30 ET on every early
    close, through a ten-hour hole on 2026-01-30 / 02-02 for ~1,786 names, and in thin names' empty hours, and the
    source's rule refuses any omission in a completed period: 1,793 of H1STATE's 1,820 names failed its census
    (2026-10-16). A row with any price present is unchanged: an inconsistent one still fails closed, and a
    placeholder in a period still running is the source's unfinished omission. Likewise an hourly row stamped at a
    session's close before the newest row (Yahoo's close point: 13:00 on every early close, flat or carrying the last
    half hour) is off the source's 09:30 grid, which admits a close point only as the proven newest row; the source
    never relabels a row, so it is left out the same way (desk_vendor_placeholders);
  * weekly window: a weekly read of range max asks Yahoo from the New York Monday ten years back (the research seed's
    span) instead of 1900: asked from 1900, Yahoo labels some listings' weeks on Tuesdays (ABBV since 2013), which
    the source's weekly rule refuses ("Unsupported weekly source label"); from a Monday it labels every week Monday;
  * retention: a (symbol, range, interval, provider) keeps only the revision its cache row names; a superseded one
    is deleted in the transaction that stores its successor. Each revision is a whole chart (~475 KB), so keeping
    every one grew the store by a revision per name per hourly census (about 0.9 GB an hour, 6 GB a session; on
    2026-10-17 it reached 3.7 GB in two hours of census, its last write the minute the loop stopped). The runtime's coverage, receipts and observed periods keep their
    own copy of what each decision used, by revision id, and nothing reads a superseded revision."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import quote, urlencode

from .ts_source import NY, DeskError, symbol, utc_clock, vendored

UTC = timezone.utc
BAR_DAYS = {"1d": 1, "5d": 5, "1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "2y": 732, "5y": 1830, "max": None}
BAR_INTERVALS = {"1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"}
FRAME_OF = {"60m": "1h", "1d": "1d", "1wk": "1wk"}   # the runtime's native frame of a vendor interval
SEED_DAYS = 3660                                    # the research seed's span: ten years of daily / weekly bars
SCHEMA = """
CREATE TABLE IF NOT EXISTS a_bar_cache(symbol TEXT,range TEXT,interval TEXT,provider TEXT,fetched_at TEXT,data TEXT,
    PRIMARY KEY(symbol,range,interval,provider));
CREATE TABLE IF NOT EXISTS a_bar_revisions(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,range TEXT NOT NULL,
    interval TEXT NOT NULL,provider TEXT NOT NULL,provider_asof TEXT,observed_at TEXT NOT NULL,fetched_at TEXT NOT NULL,
    source TEXT NOT NULL,adjustment TEXT NOT NULL,content_sha256 TEXT NOT NULL UNIQUE,data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS a_bar_revisions_key ON a_bar_revisions(symbol,range,interval,provider);
CREATE TABLE IF NOT EXISTS quotes(symbol TEXT PRIMARY KEY,price TEXT NOT NULL,as_of TEXT NOT NULL,source TEXT NOT NULL);
"""


class ProviderError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def source_request(method, url, payload=None, headers=None):
    """backend/providers._request for a public GET (one attempt, 8-second deadline, never exposing the body or
    URL), sent through the desk's shared HTTP client: its per-host rate ledger, lane and circuit breaker."""
    from ..data.http import HttpError, get
    if method != "GET" or payload is not None:
        raise ProviderError("Only public GET reads are configured")
    try:
        value = get(url, tries=1, timeout=8, headers=headers)
    except HttpError as exc:
        raise ProviderError(f"Provider HTTP request failed ({exc.status})" if exc.status else
                            "Provider request failed or returned invalid data", exc.status) from None
    if value is None:
        raise ProviderError("Provider HTTP request failed (404)", 404)
    return value


class YahooNative:
    kind = "yahoo"
    MAX_SYMBOLS = 16
    MAX_BARS = 50000

    def __init__(self, store, clock, transport=None):
        self.store, self.clock = store, clock
        self._transport = transport or source_request
        with store.connect() as con:
            con.executescript(SCHEMA)

    def _now(self):
        return datetime.fromtimestamp(float(self.clock()), UTC)

    def _yahoo(self, sym, range, interval, *, start_at=None):
        url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(sym.replace(".", "-"), safe="")
        params = {"interval": interval, "includePrePost": "false"}
        if start_at is not None:
            params.update({"period1": int(utc_clock(start_at).timestamp()), "period2": int(self._now().timestamp())})
        elif range == "max" and interval != "1wk":
            params.update({"period1": -2208988800, "period2": int(self._now().timestamp())})
        elif interval == "1wk":                    # max: the seed's span (module docstring, weekly window)
            now = self._now()
            first_day = now.astimezone(NY).date() - timedelta(days=BAR_DAYS[range] or SEED_DAYS)
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
        if interval == "1wk":
            return {**rows[0], "_desk_request_window": {"start": datetime.fromtimestamp(params["period1"], UTC).isoformat(),
                    "end": datetime.fromtimestamp(params["period2"], UTC).isoformat(),
                    "anchor": "Monday 00:00 America/New_York; complete native-week query boundary"}}
        return rows[0]

    def _yahoo_bars(self, sym, range, interval, *, start_at=None):
        chart = self._yahoo(sym, range, interval, start_at=start_at) if start_at is not None else self._yahoo(sym, range, interval)
        vendor_meta = chart.get("meta") or {}
        if (not isinstance(vendor_meta, dict) or vendor_meta.get('symbol') != sym.replace('.', '-')
                or vendor_meta.get('currency') != 'USD' or vendor_meta.get('instrumentType') not in ('EQUITY', 'ETF')):
            raise ProviderError('Historical native symbol, USD currency or equity/fund identity is unverified')
        vendor_interval = vendor_meta.get("dataGranularity")
        if vendor_interval is not None and vendor_interval != interval and {vendor_interval, interval} != {"1h", "60m"}:
            raise ProviderError("Historical provider changed the requested bar interval")
        q = (chart.get("indicators", {}).get("quote") or [{}])[0]
        adjusted = (chart.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose", [])
        bars, omitted_bar_rows = [], []
        raw = chart.get("timestamp") or []
        keep, placeholders = self._placeholders(raw, q, interval)
        timestamps = [raw[i] for i in keep]
        for i, (r, timestamp) in enumerate(zip(keep, timestamps)):
            values = {field: q.get(field, [])[r] if r < len(q.get(field, [])) else None for field in ("open", "high", "low", "close", "volume")}
            if any(isinstance(value, bool) for value in values.values()) or (r < len(adjusted) and isinstance(adjusted[r], bool)):
                raise ProviderError("Historical source contains Boolean OHLCV or adjusted prices")
            valid_prices = all(values[f] is not None and math.isfinite(float(values[f])) and float(values[f]) > 0 for f in ("open", "high", "low", "close"))
            consistent_prices = valid_prices and float(values["low"]) <= min(float(values["open"]), float(values["close"])) and float(values["high"]) >= max(float(values["open"]), float(values["close"])) and float(values["low"]) <= float(values["high"])
            if consistent_prices:
                if r < len(adjusted) and adjusted[r] is not None and math.isfinite(float(adjusted[r])):
                    values["adjusted_close"] = adjusted[r]
                bar = {"timestamp": datetime.fromtimestamp(timestamp, UTC).isoformat(), **values}
                if interval == "60m":
                    bar["source_row_index"] = i
                bars.append(bar)
            else:
                omitted_bar_rows.append({"row_index": i,
                                         "timestamp": datetime.fromtimestamp(timestamp, UTC).isoformat(), **values})
        result = {"provider": "yahoo", "source": "Yahoo Finance historical bars", "adjustment": "Yahoo adjusted_close as supplied; vendor OHLC retained without desk adjustments", "bars": bars, "truncated": len(bars) > self.MAX_BARS, "omitted_rows": len(timestamps) - len(bars), "vendor_interval": vendor_interval, "timestamp_semantics": "Vendor bar timestamp, not publication time"}
        result['native_identity'] = {'symbol': sym, 'provider_symbol': vendor_meta['symbol'],
                                     'currency': vendor_meta['currency'], 'instrument_type': vendor_meta['instrumentType']}
        if placeholders:
            result["desk_vendor_placeholders"] = placeholders
        if omitted_bar_rows:
            result["omitted_bar_rows"] = omitted_bar_rows
            result["source_row_count"] = len(timestamps)
        if chart.get("_desk_request_window"):
            result["request_window"] = chart["_desk_request_window"]
        if interval == "60m":
            result["source_row_count"] = len(timestamps)
            regular = (vendor_meta.get("currentTradingPeriod") or {}).get("regular")
            if isinstance(regular, dict):
                result["vendor_regular_session"] = {
                    "start": regular.get("start"), "end": regular.get("end"),
                    "timezone": regular.get("timezone"), "gmtoffset": regular.get("gmtoffset"),
                    "exchange_timezone": vendor_meta.get("exchangeTimezoneName"),
                    "source": "Yahoo chart meta.currentTradingPeriod.regular",
                }
        regular_time = vendor_meta.get("regularMarketTime")
        if type(regular_time) is int and 0 < regular_time < 4_102_444_800:
            result["vendor_regular_market_timestamp"] = datetime.fromtimestamp(regular_time, UTC).isoformat()
        return result

    def _placeholders(self, raw, q, interval):
        """the response's rows split into the ones the payload carries and Yahoo's rows that are no native bar (module
        docstring, vendor placeholders): open, high, low and close all missing in a native period complete at the fetch,
        and an hourly row stamped at a session's close before the newest row (Yahoo's close point, off the 09:30 grid;
        the newest is the runtime's to judge) -> (the indices kept, the others' ISO stamps). A period the runtime cannot
        place is kept, for its own rules to judge."""
        frame = FRAME_OF.get(interval)
        if frame is None:
            return list(range(len(raw))), []
        rt = vendored()["tensor_runtime"]
        now_ms = self._now().timestamp() * 1000
        keep, out = [], []
        for i, t in enumerate(raw):
            ms = int(t) * 1000
            if all((q.get(f) or [])[i:i + 1] in ([], [None]) for f in ("open", "high", "low", "close")):
                try:
                    done = rt._native_period(ms, frame)[1] <= now_ms
                except Exception:
                    done = False
                if done:
                    out.append(datetime.fromtimestamp(t, UTC).isoformat())
                    continue
            if frame == "1h" and i < len(raw) - 1:          # an hourly row at a session's close, not the newest row
                bounds = rt._session(datetime.fromtimestamp(t, UTC).astimezone(NY).date().isoformat())
                if bounds and ms == bounds[1]:
                    out.append(datetime.fromtimestamp(t, UTC).isoformat())
                    continue
            keep.append(i)
        return keep, out

    def _save_bars(self, sym, range, interval, content):
        supplied = content["bars"]
        if not isinstance(supplied, list) or not supplied:
            raise ProviderError("Historical data returned no usable bars")
        bars = [{**b, "timestamp": utc_clock(b["timestamp"]).isoformat()} for b in supplied[:self.MAX_BARS]]
        content = {**content, "truncated": bool(content.get("truncated") or len(supplied) > self.MAX_BARS)}
        if any(isinstance(b.get(field), bool) for b in bars for field in ("open", "high", "low", "close", "volume", "adjusted_close")):
            raise ProviderError("Historical data contains Boolean OHLCV or adjusted prices")
        if any(utc_clock(b["timestamp"]) > self._now() + timedelta(seconds=5) for b in bars):
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
        fetched = self._now().isoformat()
        digest = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        provider_asof = bars[-1]["timestamp"] if bars else None
        result = {**content, "fetched_at": fetched, "provider_asof": provider_asof, "observed_at": fetched, "revision_id": digest, "content_sha256": digest, "cached": False, "stale_cache": False}
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO a_bar_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (digest, sym, range, interval, content["provider"], provider_asof, fetched, fetched, content["source"], content["adjustment"], digest, json.dumps(content)))
            stored = con.execute("SELECT * FROM a_bar_revisions WHERE id=?", (digest,)).fetchone()
            result["observed_at"] = stored["observed_at"]
            con.execute("INSERT OR REPLACE INTO a_bar_cache VALUES(?,?,?,?,?,?)", (sym, range, interval, self.kind, fetched, json.dumps(result)))
            con.execute("DELETE FROM a_bar_revisions WHERE symbol=? AND range=? AND interval=? AND provider=? AND id<>?",
                        (sym, range, interval, content["provider"], digest))     # retention: the cached revision only
        return result

    def _cached_bars(self, row, sym, range, interval):
        cached = json.loads(row["data"])
        with self.store.connect() as con:
            receipt = con.execute("SELECT * FROM a_bar_revisions WHERE id=?", (cached.get("revision_id"),)).fetchone()
        if receipt is None:
            raise ProviderError("Historical cache revision is missing")
        content = json.loads(receipt["data"])
        if hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest() != receipt["content_sha256"]:
            raise ProviderError("Historical cache revision differs from its content hash")
        if (receipt["symbol"], receipt["range"], receipt["interval"]) != (sym, range, interval):
            raise ProviderError("Historical cache identity is inconsistent")
        native = content.get('native_identity') or {}
        if (not isinstance(native, dict) or native.get('symbol') != sym or native.get('provider_symbol') != sym.replace('.', '-')
                or native.get('currency') != 'USD' or native.get('instrument_type') not in ('EQUITY', 'ETF')):
            raise ProviderError('Historical cache requires a fresh native-identity qualified observation')
        fetched = utc_clock(row["fetched_at"])
        if fetched > self._now() + timedelta(seconds=5):
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
                saved = None
        if saved and (self._now() - utc_clock(saved["fetched_at"])).total_seconds() < 60:
            return saved
        try:
            return self._save_bars(sym, range, interval, self._yahoo_bars(sym, range, interval))
        except (ProviderError, DeskError, KeyError, ValueError, TypeError, IndexError, AttributeError, ArithmeticError, OSError):
            pass
        if saved:
            return {**saved, "stale_cache": True, "error": "Historical data read failed; showing saved bars"}
        raise ProviderError("Historical data is unavailable; no fabricated bars") from None

    def native_bars_since(self, sym, start_at, interval="60m"):
        sym = symbol(sym)
        if not isinstance(start_at, (datetime, str)):
            raise DeskError("Explicit aware native query anchor required", 422)
        anchor, now = utc_clock(start_at), self._now()
        if interval != "60m":
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
                saved = validate_identity(self._cached_bars_since(cached, sym, cache_range, interval))
                if (now - utc_clock(saved["fetched_at"])).total_seconds() < 60:
                    return saved
            except (DeskError, ProviderError, ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                pass
        try:
            content = validate_identity(self._yahoo_bars(sym, cache_range, interval, start_at=anchor))
            return self._save_bars(sym, cache_range, interval, content)
        except (ProviderError, DeskError, KeyError, ValueError, TypeError, IndexError, AttributeError, ArithmeticError, OSError):
            raise ProviderError("Incremental native data is unavailable; no stale or fabricated bars") from None

    def _cached_bars_since(self, row, sym, cache_range, interval):
        return self._cached_bars(row, sym, cache_range, interval)

    def refresh(self, symbols):
        symbols = sorted({symbol(s) for s in symbols})
        if len(symbols) > self.MAX_SYMBOLS:
            raise DeskError(f"Refresh is limited to {self.MAX_SYMBOLS} symbols per pass", 422)
        quotes, errors = [], []
        for sym in symbols:
            try:
                chart = self._yahoo(sym, "1d", "1m")
                meta = chart.get("meta") or {}
                if (not isinstance(meta, dict) or meta.get('symbol') != sym.replace('.', '-')
                        or meta.get('currency') != 'USD' or meta.get('instrumentType') not in ('EQUITY', 'ETF')):
                    raise ProviderError('Public quote native symbol, USD currency or equity/fund identity is unverified')
                if not meta.get("regularMarketTime") or not meta.get("regularMarketPrice"):
                    raise ProviderError("Public provider returned no timestamped quote")
                price = Decimal(str(meta["regularMarketPrice"]))
                timestamp = datetime.fromtimestamp(meta["regularMarketTime"], UTC)
                source = "Yahoo Finance quote (provider timestamp; may be delayed)"
                quotes.append(self.ingest_quote(sym, price, timestamp, source))
            except (ProviderError, DeskError, ValueError, TypeError, KeyError, AttributeError, ArithmeticError, OSError):
                errors.append({"symbol": sym, "error": "Provider quote could not be fetched or accepted; saved quote retained"})
        return {"provider": self.kind, "quotes": quotes, "errors": errors, "refreshed": len(quotes)}

    def ingest_quote(self, sym, price, as_of, source):
        """the source store's quote rule: timezone-aware, not future, positive; never replaced by an older one."""
        sym = symbol(sym)
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise DeskError("Quote timestamp must include a timezone", 422)
        as_of = as_of.astimezone(UTC)
        if (as_of - self._now()).total_seconds() > 5:
            raise DeskError("Quote timestamp cannot be in the future", 422)
        if not price.is_finite() or price <= 0 or not source.strip():
            raise DeskError("Quote needs a positive finite price and explicit source", 422)
        timestamp = as_of.isoformat()
        with self.store.transaction() as con:
            current = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
            if current:
                old = datetime.fromisoformat(current["as_of"])
                if as_of < old:
                    raise DeskError("An older quote cannot replace a newer quote")
                if as_of == old:
                    if Decimal(current["price"]) != price or current["source"] != source:
                        raise DeskError("This quote timestamp already has different price or provenance")
                    return self._quote(con, sym)
            con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", (sym, str(price), timestamp, source))
            return self._quote(con, sym)

    def _quote(self, con, sym):
        """backend/store.py Store.quote: the stored row, fresh within -5 s .. quote_max_age_seconds, price a number."""
        row = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
        if not row:
            return None
        data = dict(row)
        age = (self._now() - datetime.fromisoformat(row["as_of"])).total_seconds()
        max_age = json.loads(con.execute("SELECT value FROM settings WHERE key='quote_max_age_seconds'").fetchone()[0])
        data["fresh"] = -5 <= age <= max_age
        data["price"] = float(Decimal(str(row["price"])))
        return data
