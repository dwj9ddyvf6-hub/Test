"""Wave-3 crypto door (2026-10-15): donchian_crypto's bars come from
the CRYPTO door — Kraken public OHLC at 15 minutes — never from the
Alpaca stock-bars route (which 404s/serves nothing for crypto pairs
on this subscription; the pre-wave live provider handed the sleeve
Alpaca DAILY STOCK bars for "SOLUSD", the wrong feed on both axes).

Source of record: the old desk's desk/kraken_bars.py (fix-all
2026-10-13, track F3), itself following donchian_crypto_sleeve's
fetch_15m_bars precedent — Kraken public OHLC REST, no keys:
  * pair SOLUSD -> SOLUSD (BTCUSD -> XBTUSD, DOGEUSD -> XDGUSD are
    the only desk overrides; only SOLUSD is consumed here),
  * the result key is NOT the request pair: parse the single
    non-"last" result entry,
  * candles are [time, o, h, l, c, vwap, volume, count] with string
    prices; volume is element 6 (element 5 is VWAP),
  * the last candle is still forming. The sleeve's spec is CLOSED
    15m bars only (sleeves/donchian_crypto.py docstring), so this
    producer drops the forming candle — the old donchian code did
    the same on its side; the lean port consumes bars[-1] as the
    last closed bar, so the drop belongs to the door.
Bar shape matches the lean convention: {"t": epoch float, "o","h",
"l","c","v"} ascending.

Fail-closed: any transport error, Kraken error payload, or malformed
result -> no bars -> the sleeve evaluates to nothing, as ported.
"""
import json
import urllib.request

KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
_PAIR_OVERRIDES = {"BTCUSD": "XBTUSD", "DOGEUSD": "XDGUSD"}
CRYPTO_SLEEVES = ("donchian_crypto",)


def kraken_pair(symbol):
    sym = str(symbol or "").upper().strip()
    if not sym.endswith("USD"):
        return None
    return _PAIR_OVERRIDES.get(sym, sym)


def parse_ohlc_payload(payload):
    """Kraken OHLC payload -> lean bar dicts (old kraken_bars
    parse_ohlc_payload, verbatim in substance; "t" as epoch float
    per the lean bar convention). [] on any malformed shape."""
    if not isinstance(payload, dict) or payload.get("error"):
        return []
    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    candles = None
    for key, val in result.items():
        if key == "last":
            continue
        candles = val
        break
    if not isinstance(candles, list):
        return []
    bars = []
    for c in candles:
        try:
            bars.append({"t": float(c[0]), "o": float(c[1]),
                         "h": float(c[2]), "l": float(c[3]),
                         "c": float(c[4]), "v": float(c[6])})
        except (ValueError, IndexError, TypeError):
            continue
    bars.sort(key=lambda b: b["t"])
    return bars


def closed_bars(bars):
    """Drop the still-forming last candle: the consumer's contract
    is closed bars only."""
    return list(bars or [])[:-1]


def fetch_kraken_ohlc(symbol, interval=15, transport=None):
    """One Kraken public OHLC request -> parsed bars ([] on any
    failure, never raises). transport: callable(url) -> payload
    (tests); default is the live public REST GET."""
    pair = kraken_pair(symbol)
    if pair is None:
        return []
    url = "%s?pair=%s&interval=%d" % (KRAKEN_OHLC_URL, pair, int(interval))
    try:
        if transport is not None:
            payload = transport(url)
        else:
            req = urllib.request.Request(
                url, headers={"User-Agent": "femto-lean-desk/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
    except Exception:
        return []
    return parse_ohlc_payload(payload)


# -- Wave-4 (2026-10-15): Kraken perpetuals + fwd research sleeves -------
# The four free_kraken_{ada,link}_{breakdown,crowded} sleeves trade
# Kraken FUTURES perpetuals (PF_ADAUSD / PF_LINKUSD), not Kraken spot:
# their bars/quote/funding come from the futures doors the old desk
# used verbatim (desk/aurelia_kraken_paper.py):
#   bars    GET futures.kraken.com/api/charts/v1/trade/{SYM}/4h
#           (candles: time in ms, string OHLCV; the sleeve itself
#           drops uncompleted bars — its completed_bars law)
#   quote   GET futures.kraken.com/derivatives/api/v3/tickers
#           (row for the symbol: bid/ask)
#   funding GET futures.kraken.com/derivatives/api/v3/historical-
#           funding-rates?symbol={SYM} (rates: [{timestamp,
#           fundingRate}] — Kraken HOURLY prints, verbatim shape)
#
# The fwd_alpaca_* sleeves consume Alpaca crypto (v1beta3/crypto/us):
# bars at their SPEC timeframe (1Hour / 4Hour) and the latest quote
# ({bid, ask, exchange_at}). Their recipe "features" WERE fenced
# (recipe engine only in the excluded Ausar archive, BUGLOG
# AURELIA-4) until EA2b (2026-10-15, User's 10:44 order): the engine
# was recovered from that archive on GitHub and ported verbatim in
# core/recipe_features.py — FwdProducer now supplies "features"
# computed by the source's own source_features over completed bars,
# exactly as the old desk's _features did. The sleeves' trade
# authority is unchanged: their ported decide() still gates on the
# decision window, quote freshness and the budget cap.
#
# fwd_coinbase_sma200 consumes Coinbase Exchange public products:
# BTC-USD daily candles (granularity=86400 -> history rows) and the
# BTC-USD ticker ({as_of, bid, ask}). Its dedup state ("decisions")
# is persisted state the old coinbase_decide wrote itself; the lean
# sleeve is pure, so the producer supplies the persisted decisions
# and declares a post-evaluation stamp_state recording today's
# decision id (dispatch writes it AFTER evaluation — the sleeve
# never reads its own stamp in the same tick). That closes the
# dedup persistence gap: a decision id, once evaluated, never
# re-fires on a later tick of the same UTC day.
#
# Fail-closed everywhere: any fetch failure/malformed payload ->
# the key/bars are ABSENT and the sleeve evaluates to nothing.

KRAKEN_PERP_SLEEVES = ("free_kraken_ada_breakdown", "free_kraken_ada_crowded",
                       "free_kraken_link_breakdown", "free_kraken_link_crowded")
CROWDED_SLEEVES = ("free_kraken_ada_crowded", "free_kraken_link_crowded")
FWD_ALPACA_SPECS = {  # sleeve_id -> (symbol, timeframe)
    "fwd_alpaca_ada_rsi2": ("ADA/USD", "1Hour"),
    "fwd_alpaca_link_ai_volume": ("LINK/USD", "4Hour"),
}
COINBASE_SLEEVE = "fwd_coinbase_sma200"


def parse_kraken_charts(payload):
    """Kraken futures charts payload -> lean bars (t epoch s).
    [] on any malformed shape; uncompleted candles are KEPT (the
    consuming sleeves filter completed bars themselves, as ported)."""
    if not isinstance(payload, dict) or payload.get("error"):
        return []
    bars = []
    for c in payload.get("candles") or []:
        try:
            bars.append({"t": float(c["time"]) / 1000.0,
                         "o": float(c["open"]), "h": float(c["high"]),
                         "l": float(c["low"]), "c": float(c["close"]),
                         "v": float(c.get("volume") or 0)})
        except (KeyError, TypeError, ValueError):
            continue
    bars.sort(key=lambda b: b["t"])
    return bars


def parse_kraken_ticker(payload, symbol):
    """Kraken futures tickers payload -> {"bid","ask"} for `symbol`,
    or None (missing/crossed/non-positive -> fail closed)."""
    if not isinstance(payload, dict):
        return None
    for row in payload.get("tickers") or []:
        if isinstance(row, dict) and row.get("symbol") == symbol:
            try:
                bid, ask = float(row["bid"]), float(row["ask"])
            except (KeyError, TypeError, ValueError):
                return None
            if bid > 0 and bid <= ask:
                return {"bid": bid, "ask": ask}
            return None
    return None


def parse_kraken_funding(payload):
    """Kraken historical funding payload -> the verbatim rates list
    [{timestamp, fundingRate}] the crowded sleeves consume."""
    if not isinstance(payload, dict):
        return []
    out = []
    for r in payload.get("rates") or []:
        if isinstance(r, dict) and r.get("timestamp") is not None \
                and r.get("fundingRate") is not None:
            out.append({"timestamp": r["timestamp"],
                        "fundingRate": r["fundingRate"]})
    return out


def coinbase_history(candles, today_iso):
    """Coinbase daily candles [[t, low, high, open, close, vol],
    newest first] -> history rows [{date, close, complete,
    forming}]: today's candle is forming/incomplete, every earlier
    candle is complete (the sleeve's prepare() contract)."""
    out = []
    from datetime import datetime, timezone
    for c in candles or []:
        try:
            day = datetime.fromtimestamp(float(c[0]), tz=timezone.utc) \
                .date().isoformat()
            close = float(c[4])
        except (TypeError, ValueError, IndexError):
            continue
        forming = day >= str(today_iso)
        out.append({"date": day, "close": close,
                    "complete": not forming, "forming": forming})
    out.sort(key=lambda r: r["date"])
    return out


class KrakenPerpProducer:
    """fetch_4h(symbol)->[bars], fetch_quote(symbol)->{bid,ask}|None,
    fetch_funding(symbol)->[rates]. bars_for claims ONLY the four
    perpetual sleeves; extra_for supplies quote (+ funding_rates
    for the crowded pair)."""

    def __init__(self, fetch_4h=None, fetch_quote=None, fetch_funding=None):
        self.fetch_4h = fetch_4h
        self.fetch_quote = fetch_quote
        self.fetch_funding = fetch_funding
        self._cache = {}  # (session, bucket) -> {symbol: bars/rates}

    def bars_for(self, sleeve, symbols, ctx):
        if sleeve.CONFIG.sleeve_id not in KRAKEN_PERP_SLEEVES:
            return None
        if self.fetch_4h is None:
            return {}
        bucket = (ctx.session, int(float(ctx.now) // 3600))
        cache = self._cache.setdefault(bucket, {})
        out = {}
        for sym in symbols or []:
            key = ("bars", sym)
            if key not in cache:
                try:
                    cache[key] = self.fetch_4h(sym) or []
                except Exception:
                    cache[key] = []
            if cache[key]:
                out[sym] = cache[key]
        return out

    def extra_for(self, sleeve_id, ctx):
        if sleeve_id not in KRAKEN_PERP_SLEEVES:
            return {}
        out = {}
        symbol = {"free_kraken_ada_breakdown": "PF_ADAUSD",
                  "free_kraken_ada_crowded": "PF_ADAUSD",
                  "free_kraken_link_breakdown": "PF_LINKUSD",
                  "free_kraken_link_crowded": "PF_LINKUSD"}[sleeve_id]
        if self.fetch_quote is not None:
            try:
                q = self.fetch_quote(symbol)
            except Exception:
                q = None
            if q:
                out["quote"] = q
        if sleeve_id in CROWDED_SLEEVES and self.fetch_funding is not None:
            bucket = (ctx.session, int(float(ctx.now) // 3600))
            cache = self._cache.setdefault(bucket, {})
            key = ("funding", symbol)
            if key not in cache:
                try:
                    cache[key] = self.fetch_funding(symbol) or []
                except Exception:
                    cache[key] = []
            if cache[key]:
                out["funding_rates"] = cache[key]
        return out


class FwdProducer:
    """fetch_crypto_bars(symbol, timeframe)->[bars],
    fetch_crypto_quote(symbol)->{bid,ask,exchange_at}|None,
    fetch_coinbase_history()->[rows], fetch_coinbase_quote()->
    {as_of,bid,ask}|None. state_store supplies held_qty /
    entry_close_at (fwd_alpaca, from the persisted position record)
    and decisions (coinbase dedup state).

    EA2b: "features" IS supplied for the two fwd_alpaca books, from
    core.recipe_features.source_features (the recovered source
    engine, verbatim) over the completed bars — the old desk's
    _features call, restored. Any engine error -> no features key
    (the sleeves then report BLOCKED, the old fenced behavior)."""

    def __init__(self, fetch_crypto_bars=None, fetch_crypto_quote=None,
                 fetch_coinbase_history=None, fetch_coinbase_quote=None,
                 state_store=None):
        self.fetch_crypto_bars = fetch_crypto_bars
        self.fetch_crypto_quote = fetch_crypto_quote
        self.fetch_coinbase_history = fetch_coinbase_history
        self.fetch_coinbase_quote = fetch_coinbase_quote
        self.state_store = state_store
        self._cache = {}

    def bars_for(self, sleeve, symbols, ctx):
        sleeve_id = sleeve.CONFIG.sleeve_id
        if sleeve_id not in FWD_ALPACA_SPECS:
            return None
        if self.fetch_crypto_bars is None:
            return {}
        symbol, timeframe = FWD_ALPACA_SPECS[sleeve_id]
        cache = self._cache.setdefault(ctx.session, {})
        key = ("bars", sleeve_id)
        if key not in cache:
            try:
                cache[key] = self.fetch_crypto_bars(symbol, timeframe) or []
            except Exception:
                cache[key] = []
        return {symbol: cache[key]} if cache[key] else {}

    def _position(self, sleeve_id, symbol):
        if self.state_store is None:
            return {}
        try:
            ss = self.state_store.get(sleeve_id).get("sleeve_state") or {}
            entry = ss.get(symbol) or {}
            pos = entry.get("position") if isinstance(entry, dict) else None
            return pos if isinstance(pos, dict) else {}
        except Exception:
            return {}

    def _decisions(self, sleeve_id):
        if self.state_store is None:
            return {}
        try:
            d = self.state_store.get(sleeve_id).get("decisions")
        except Exception:
            return {}
        return d if isinstance(d, dict) else {}

    def _features(self, sleeve_id, ctx):
        """Recovered recipe features for one fwd_alpaca book: the
        source engine's source_features over the COMPLETED bars (the
        sleeves' own completed_bars law, re-applied here because the
        engine consumes the source bar shape), with the book's
        declared params (core.recipe_features.BOOK_PARAMS). None on
        any failure — fail closed to the sleeves' BLOCKED path."""
        from datetime import datetime, timedelta, timezone
        from core import recipe_features as rf
        symbol, timeframe = FWD_ALPACA_SPECS[sleeve_id]
        step = {"1Hour": 3600, "4Hour": 14400}[timeframe]
        cache = self._cache.setdefault(ctx.session, {})
        key = ("bars", sleeve_id)
        if key not in cache:
            if self.fetch_crypto_bars is None:
                return None
            try:
                cache[key] = self.fetch_crypto_bars(symbol, timeframe) or []
            except Exception:
                cache[key] = []
        now = datetime.fromtimestamp(float(ctx.now), tz=timezone.utc)
        rows = []
        for bar in cache[key] or []:
            try:
                opened = datetime.fromtimestamp(float(bar["t"]),
                                                tz=timezone.utc)
                closed = opened + timedelta(seconds=step)
                if closed > now:
                    continue
                rows.append({"open_at": opened.isoformat(),
                             "close_at": closed.isoformat(),
                             "open": float(bar["o"]), "high": float(bar["h"]),
                             "low": float(bar["l"]), "close": float(bar["c"]),
                             "volume": float(bar["v"])})
            except (TypeError, ValueError, KeyError):
                continue
        if not rows:
            return None
        strategy, spec_params = rf.BOOK_PARAMS[sleeve_id]
        try:
            return rf.source_features(
                strategy, rows, rf.make_params(strategy, spec_params))
        except Exception:
            return None

    def extra_for(self, sleeve_id, ctx):
        if sleeve_id in FWD_ALPACA_SPECS:
            symbol, _tf = FWD_ALPACA_SPECS[sleeve_id]
            out = {}
            if self.fetch_crypto_quote is not None:
                try:
                    q = self.fetch_crypto_quote(symbol)
                except Exception:
                    q = None
                if q:
                    out["quote"] = q
            pos = self._position(sleeve_id, symbol)
            out["held_qty"] = float(pos.get("qty") or 0)
            out["entry_close_at"] = pos.get("entry_close_at")
            if not out["entry_close_at"]:
                # AUDIT3-B-07 (2026-10-16): the fwd sleeves' only
                # working exit is the 5-bar timed exit anchored on
                # entry_close_at (the ai_volume feature dict never
                # carries long_close_signal — that branch is dead
                # in the source engine too). A record written
                # without the bar_close label (adopted/repaired
                # records) left the anchor None and the position
                # held forever. Fall back to the record's entry
                # instant: it falls inside the entry bar, so the
                # bar-counting anchor is equivalent.
                _et = pos.get("entry_bar_t") or pos.get("entry_t")
                if _et:
                    from datetime import datetime as _dt, timezone as _tz
                    try:
                        out["entry_close_at"] = _dt.fromtimestamp(
                            float(_et), tz=_tz.utc).isoformat()
                    except (TypeError, ValueError, OSError):
                        pass
            feats = self._features(sleeve_id, ctx)
            if feats:
                out["features"] = feats
            return out
        if sleeve_id == COINBASE_SLEEVE:
            out = {}
            cache = self._cache.setdefault(ctx.session, {})
            if "cb_history" not in cache:
                try:
                    cache["cb_history"] = self.fetch_coinbase_history() \
                        if self.fetch_coinbase_history else []
                except Exception:
                    cache["cb_history"] = []
            if cache["cb_history"]:
                out["history"] = cache["cb_history"]
            if self.fetch_coinbase_quote is not None:
                try:
                    q = self.fetch_coinbase_quote()
                except Exception:
                    q = None
                if q:
                    out["quote"] = q
            decisions = self._decisions(sleeve_id)
            out["decisions"] = decisions
            # Dedup persistence (post-evaluation stamp): record
            # today's (UTC) decision id so it never re-fires.
            from datetime import datetime, timezone
            from sleeves.fwd_coinbase_sma200 import decision_id
            day = datetime.fromtimestamp(float(ctx.now), tz=timezone.utc) \
                .date().isoformat()
            did = decision_id(day)
            if did not in decisions:
                merged = dict(decisions)
                merged[did] = {"id": did, "day": day}
                out["stamp_state"] = {"decisions": merged}
            return out
        return {}


class CryptoProducer:
    """fetch_15m(symbol) -> [bars] through the crypto door (the
    production callable lives in tools/run_live.py and wraps
    fetch_kraken_ohlc at interval=15). bars_for serves ONLY
    donchian_crypto; every other sleeve returns None so the caller
    falls through to the stock-bars door."""

    def __init__(self, fetch_15m=None):
        self.fetch_15m = fetch_15m
        self._cache = {}  # session -> {symbol: closed bars}

    def bars_for(self, sleeve, symbols, ctx):
        sleeve_id = sleeve.CONFIG.sleeve_id
        if sleeve_id not in CRYPTO_SLEEVES:
            return None
        if self.fetch_15m is None:
            return {}
        # 15m bars go stale within a session (unlike the daily-bar
        # producers' session cache): bucket the cache by the sleeve's
        # own 900s cadence so each tick can see newly closed bars.
        bucket = (ctx.session, int(float(ctx.now) // 900))
        cache = self._cache.setdefault(bucket, {})
        out = {}
        for sym in symbols or []:
            if sym not in cache:
                try:
                    cache[sym] = closed_bars(self.fetch_15m(sym) or [])
                except Exception:
                    cache[sym] = []
            if cache[sym]:
                out[sym] = cache[sym]
        return out
