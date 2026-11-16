"""Warm bars producer (CURE3-1, A9 root cause).

The live runner's bars producer returned an EMPTY map while still
marking the `bars` key produced, so sleeves were FED on nothing (or,
for other inputs, UNFED forever) and no RTH session could ever fill.
This producer fetches real Alpaca SIP bars (1Day + 1Hour) for the
desk's symbol union through the paper credentials route, caches them
in state/warm_bars.json (fresh < 3600s), and returns them in the
snapshot shapes the adapters consume: {SYM: rows} plus {"SYM|1Day"}
and {"SYM|1Hour"} aliases.

Fail-closed honesty: on any fetch failure with no usable cache it
returns {} — the `bars` key is ABSENT, the registry does not mark it
produced (cycle marks only returned keys), and dependent sleeves are
UNFED by name instead of evaluating on an empty map.
"""
from __future__ import annotations
import json, math, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DATA_URL = "https://data.alpaca.markets"
CORE_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "SMH"]
ET = ZoneInfo("America/New_York")

# ------------------------------------------------------- bars integrity
# BARS-INTEGRITY-20261029 (DEEP-PASS 3.1 item 2, adopted as is from
# the new-head Trade Brain bars payload gate, Section 2.3 point 10):
# a daily history payload is validated AS A WHOLE at ingestion. Any
# failure rejects the payload as daily_history_invalid_or_incomplete
# (this producer then fails closed: no bars key, sleeves UNFED by
# name) instead of the old behaviour, which merged whatever arrived
# per symbol with no payload level check at all.
MAX_DAILY_BARS = 1000
# SIP daily bars lag ~15-18 min; the just-closed session counts as
# completed only from 16:30 ET so the gate never rejects a history
# whose final bar is still settling at the provider.
SESSION_SETTLE_ET = (16, 30)


class BarsIntegrityError(ValueError):
    """A daily bars payload failed the whole-payload integrity gate."""


def _ny_date(stamp):
    dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET).date().isoformat()


def validate_daily_payload(symbol, rows, start, expected_last=None):
    """None when the symbol's daily series passes the gate, else the
    named failure reason. Checks: at most MAX_DAILY_BARS bars, every
    OHLC finite and positive, no bar outside the requested window,
    New York dates strictly increasing (no duplicates), and, when
    expected_last is given, the series ends exactly on that session."""
    if len(rows) > MAX_DAILY_BARS:
        return f"too_many_bars:{len(rows)}"
    start_date = str(start)[:10]
    prev = None
    for r in rows:
        try:
            vals = [float(r[k]) for k in ("o", "h", "l", "c")]
            day = _ny_date(r["t"])
        except (KeyError, TypeError, ValueError):
            return "malformed_bar"
        if any(not math.isfinite(v) or v <= 0 for v in vals):
            return "non_finite_or_non_positive_ohlc"
        if day < start_date:
            return f"bar_outside_window:{day}"
        if prev is not None and day <= prev:
            return f"duplicate_or_non_increasing_date:{day}"
        prev = day
    if expected_last is not None:
        if prev is None:
            return "empty_history"
        if prev != expected_last:
            return f"history_ends_{prev}_expected_{expected_last}"
    return None


def expected_latest_completed_session(now):
    """The latest completed daily session at `now`, derived by
    walking the desk trading calendar (core.data.is_trading_day)
    backwards up to 8 days from the candidate date: today ET once
    the session has closed and settled (16:30 ET), else yesterday
    ET. Returns an ISO date, or None when no trading day is found
    inside the walk (the exact check then does not apply)."""
    from core.data import is_trading_day
    et_now = now.astimezone(ET)
    cand = et_now.date()
    if (et_now.hour, et_now.minute) < SESSION_SETTLE_ET:
        cand -= timedelta(days=1)
    for _ in range(9):
        if is_trading_day(cand):
            return cand.isoformat()
        cand -= timedelta(days=1)
    return None


def desk_symbols(root):
    """Symbol union: config universes (bounded lists) + core indices."""
    syms = set(CORE_SYMBOLS)
    # FEED80-HEDGE-20261114: TZA is s_mn_hedge's instrument; without
    # it in the warm universe the sleeve could never price its own
    # hedge leg even when hedge_signal is served.
    syms.add("TZA")
    # CLEAR-THE-BOARD-20261114 (CR-1): QLD is the target instrument
    # of four aster_etf sleeves (qld_buy_hold, qld_monthly, and the
    # QQQ/QLD halves of qqq_qld_buy_hold / qqq_qld_monthly). It was
    # in no warm list, so the snapshot carried no QLD bars at all
    # and those sleeves refused their whole rebalance on a missing
    # target price — the feed half of the CR-1 class, hidden behind
    # the weight-lag half the 2026-11-11 cure landed. QLD is a real
    # Alpaca-listed ETF (producers.py already names it in its own
    # symbol set); serve it like every other sleeve instrument.
    syms.add("QLD")
    # GOING-LIVE-BASKETS-20261115: the live overnight basket
    # sleeves (desk3/overnight_baskets.py) trade the Focus 29
    # complex and its sub-baskets at the close and the open on
    # daily bars. Seven of those names (SOXX, TSM, AMAT, FLNC,
    # EOSE, CEG, XLE) were in no warm list, so the snapshot
    # carried no bars for them at all: the energy8 basket could
    # resolve only 4 of its 8 names, below its registered
    # 6-name floor, and could never fire. They are real
    # Alpaca-listed names; serve them like every other sleeve
    # instrument. SIVE is deliberately not added: it is
    # unmeasurable on book routes and is excluded from the
    # Focus 29 set by the register itself.
    syms.update(("SOXX", "TSM", "AMAT", "FLNC", "EOSE", "CEG",
                 "XLE"))
    try:
        uni = json.load(open(os.path.join(root, "config", "universes.json")))
        for key in ("basket_41", "momentum_114", "phase_48"):
            for s in uni.get(key, []) or []:
                if isinstance(s, str) and "/" not in s:
                    syms.add(s)
    except (OSError, ValueError):
        pass
    return sorted(syms)


def _fetch(symbols, timeframe, start, env, limit=10000, expected_last=None,
           session_drops=None):
    """Paginated fetch (CURE3-1 fix-in-pass): a 100-symbol chunk over a
    500-day window far exceeds one 10000-bar page — follow
    next_page_token until exhausted or Alpaca truncates silently.
    The loop only exits when no token remains, so the merged series
    is complete by construction; BARS-INTEGRITY-20261029 adds the
    payload gate on top: a returned symbol the caller did not
    request fails any timeframe's payload, and a 1Day payload must
    additionally pass validate_daily_payload per symbol, with the
    exact expected latest completed session when the caller
    supplies one (fetch_all does, from the desk calendar)."""
    out = {}
    headers = {"APCA-API-KEY-ID": env.get("ALPACA_KEY_ID", ""),
               "APCA-API-SECRET-KEY": env.get("ALPACA_SECRET_KEY", "")}
    for i in range(0, len(symbols), 50):
        chunk = symbols[i:i + 50]
        wanted = set(chunk)
        token = None
        while True:
            params = {"symbols": ",".join(chunk), "timeframe": timeframe,
                      "start": start, "feed": "sip", "limit": limit,
                      "adjustment": "raw", "sort": "asc"}
            if token:
                params["page_token"] = token
            q = urllib.parse.urlencode(params)
            # EGRESS-1: netfetch (http.client), not urllib — see
            # desk3/netfetch.py.
            from .netfetch import fetch_json
            doc = fetch_json(f"{DATA_URL}/v2/stocks/bars?{q}",
                             headers=headers, timeout=60)
            for sym, rows in (doc.get("bars") or {}).items():
                if sym not in wanted:
                    raise BarsIntegrityError(
                        f"daily_history_invalid_or_incomplete:"
                        f"symbol_mismatch:{sym}_not_requested")
                out.setdefault(sym, []).extend(
                    {"t": r["t"], "o": r["o"], "h": r["h"], "l": r["l"],
                     "c": r["c"], "v": r["v"]} for r in rows or [])
            token = doc.get("next_page_token")
            if not token:
                break
    if timeframe == "1Day":
        for sym in list(out):
            if expected_last is not None:
                # WARM-DAILY-PARTIAL-BAR-20261102: during the session
                # the provider appends today's IN-PROGRESS daily bar,
                # so every series ends on the current session instead
                # of the latest completed one and the exact-end gate
                # below dropped every equity symbol (the intraday
                # warm product carried no equity |1Day series at all;
                # desk gate failure named 2026-11-02). A bar dated
                # after the latest completed session is by definition
                # not a completed bar (adapters' closed_bars drop it
                # too), so trailing bars past expected_last are
                # trimmed BEFORE validation. A series that is stale
                # even after trimming still drops by name below.
                rows = out[sym]
                cut = len(rows)
                while cut > 0:
                    try:
                        day = _ny_date(rows[cut - 1]["t"])
                    except (KeyError, TypeError, ValueError):
                        break
                    if day > expected_last:
                        cut -= 1
                    else:
                        break
                if cut < len(rows):
                    out[sym] = rows[:cut]
            reason = validate_daily_payload(sym, out[sym], start,
                                            expected_last=expected_last)
            if reason is None:
                continue
            if reason.startswith(("history_ends_", "empty_history")):
                # Session currency is per symbol: one halted or
                # delisted name ending early drops THAT symbol (and
                # is named in session_drops), never the whole union.
                # If every symbol drops, fetch_all returns an empty
                # map and the producer fails closed as usual.
                del out[sym]
                if session_drops is not None:
                    session_drops.append({"symbol": sym, "reason": reason})
                continue
            raise BarsIntegrityError(
                f"daily_history_invalid_or_incomplete:{sym}:{reason}")
    return out


CRYPTO_URL = "https://data.alpaca.markets/v1beta3/crypto/us"
# HARDEN-B4: the symbol/timeframe slices the batch-4 sleeves declare
# (bars:<sym>:<tf> registry keys). Windows are the desk's data
# contract for those lanes: weekly for the leader_sc rotation,
# 15Min for legends_ema's QQQ lane, 5Min/1Min for saty_day's SPY/QQQ
# books, and the Alpaca crypto pairs the fwd_* sleeves declare.
EXTRA_TF_FETCHES = (("1Week", 1000),)
INTRADAY_FETCHES = (("QQQ", "15Min", 30),
                    # CR6-V03-WARMUP-20261114: SPY 5Min widened
                    # 60 -> 300 days. saty_gpt_v03's 1H frame is
                    # session-aligned by design and is resampled
                    # from its 10m frame (itself built from this
                    # 5Min series); its pinned warmup is 1000 1H
                    # bars = ~167 sessions. The rolling 60-day
                    # window capped the resample at ~258 bars, so
                    # the sleeve could never warm up no matter how
                    # long it ran. 300 days holds ~210 sessions
                    # (~1260 resampled 1H bars).
                    ("SPY", "5Min", 300),
                    ("QQQ", "5Min", 60), ("SPY", "1Min", 18),
                    ("QQQ", "1Min", 10),
                    # investandbefree_dmac install 2026-10-29: SPY/QQQ
                    # 1Hour at 200 calendar days (~140 RTH sessions)
                    # for the sleeve's 4H aggregation; the base 30-day
                    # hourly product held only ~51 sessions and the
                    # 500-day weekly product only ~72 weekly bars
                    # (weekly window above widened 500 -> 1000 days,
                    # ~143 bars, for the same install).
                    ("SPY", "1Hour", 200), ("QQQ", "1Hour", 200),
                    # bta_onebar family install 2026-10-30: 30-minute
                    # bars for the one-bar Donchian sleeves (50-bar
                    # channel needs at least 51 bars; 30 calendar
                    # days holds several hundred per symbol).
                    ("QQQ", "30Min", 30), ("SPY", "30Min", 30),
                    ("MDY", "30Min", 30), ("DIA", "30Min", 30),
                    # FEED80-WARM-20261114: 30Min for the full
                    # aster_batch15.UNIVERSE42 — the r19 overnight
                    # timing sleeves read 30Min bars for all 42
                    # symbols and only the 4 index names above were
                    # ever fetched, so their timeframe was unservable
                    # (FEED-GRANULARITY-SPEC mechanism 2). The blocker
                    # test_feed80_warm_20261114 pins this list against
                    # UNIVERSE42 so universe drift fails loudly.
                    ("AAOI", "30Min", 200), ("AEHR", "30Min", 200),
                    ("AG", "30Min", 200), ("ALAB", "30Min", 200),
                    ("ANF", "30Min", 200), ("ARM", "30Min", 200),
                    ("ARQQ", "30Min", 200), ("ASPI", "30Min", 200),
                    ("AXTI", "30Min", 200), ("CLS", "30Min", 200),
                    ("CORZ", "30Min", 200), ("CRDO", "30Min", 200),
                    ("CRML", "30Min", 200), ("CVNA", "30Min", 200),
                    ("FCEL", "30Min", 200), ("FFIV", "30Min", 200),
                    ("HIVE", "30Min", 200), ("HUT", "30Min", 200),
                    ("IREN", "30Min", 200), ("KEEL", "30Min", 200),
                    ("LASR", "30Min", 200), ("LITE", "30Min", 200),
                    ("MU", "30Min", 200), ("NBIS", "30Min", 200),
                    ("OKLO", "30Min", 200), ("OUST", "30Min", 200),
                    ("POET", "30Min", 200), ("SATL", "30Min", 200),
                    ("SHAZ", "30Min", 200), ("SIVEF", "30Min", 200),
                    ("SKYQ", "30Min", 200), ("SNDK", "30Min", 200),
                    ("SOXL", "30Min", 200), ("TE", "30Min", 200),
                    ("TEM", "30Min", 200), ("TSEM", "30Min", 200),
                    ("TTMI", "30Min", 200), ("USAR", "30Min", 200),
                    ("VELO", "30Min", 200), ("VRT", "30Min", 200),
                    ("WDC", "30Min", 200), ("WYFI", "30Min", 200),
                    # soxl_pm_breakout cure 2026-11-04: the sleeve
                    # declares bars:SOXL:15Min by design; the slice
                    # was never wired, leaving it UNFED by name and
                    # the roster contract red. 30 days matches the
                    # QQQ 15Min lane.
                    ("SOXL", "15Min", 30),
                    # SSO-PORT-CONV46-20261115: sso_opus and
                    # sso_opus_notime25 declare bars:SSO:15Min;
                    # 30 days x 26 RTH bars = ~780 bars, above the
                    # strategy's 200-bar warmup, the SOXL lane's
                    # shape.
                    ("SSO", "15Min", 30))

# SEGMENT-CONSTRUCTION-20261116 (CONV-88 / CONV-108 / CONV-80):
# 1Min for the full Focus 29 set. Until this landing warm served
# 1Min only for SPY and QQQ (the INTRADAY_FETCHES lanes above), so
# no Focus name carried a served bars:<SYM>:1Min slice on the
# live-assembled view (0 of 29, GOING-LIVE-2026-11-15 section 6)
# and the KG-4 intraday segment construction (open drive
# 09:30-10:30, midday 10:30-15:00, close hour 15:00-16:00 ET)
# could not resolve for the sleeves that trade it
# (desk3/intraday_segments.py). The window mirrors the QQQ 1Min
# lane's 10 days: the segment sleeves consume only the current
# session, and the historical 1Min ground stays the ONE offline
# cache the weekend program widened (cache/bars/<SYM>/1Min.jsonl,
# DH3, 29 of 30 Focus names over 53 sessions) — this fetch does
# not create a second historical source, it serves the live view.
# The symbol list is pinned against
# desk3/overnight_baskets.FOCUS29 by the segment blocker tests
# (the FEED80-WARM-20261114 mechanism), so drift fails loudly.
FOCUS29_1MIN_SYMBOLS = ("SMH", "SOXX", "NVDA", "AVGO", "AMD",
                        "MRVL", "ARM", "TSM", "AMAT", "MU",
                        "SNDK", "WDC", "AAOI", "COHR", "LITE",
                        "CRDO", "ALAB", "AXTI", "CRWV", "PLTR",
                        "RKLB", "FLNC", "EOSE", "FCEL", "BE",
                        "OKLO", "VST", "CEG", "XLE")
FOCUS29_1MIN_DAYS = 10
INTRADAY_FETCHES = INTRADAY_FETCHES + tuple(
    (sym, "1Min", FOCUS29_1MIN_DAYS) for sym in FOCUS29_1MIN_SYMBOLS)

# GAMMA-WINDOW-20261116 (desk full audit Lane E, defect 1b): 1Min
# for the rest of UNIVERSE15 (desk3/aster_batch1.UNIVERSE15), the
# universe the opening-events assembler builds its first-5-minute
# state from. SPY/QQQ are served by the base INTRADAY_FETCHES
# lanes above and SMH/SOXX/XLE by the Focus 29 block; the ten
# names below complete the universe. Until this landing the
# assembler's candidate state could only ever assemble for
# {SPY, QQQ} (plus XLE via Focus 29), so a carrier day in XLF or
# XLU wrote a necessarily empty drop that no field distinguished
# from a true no-break day. The window mirrors the QQQ / Focus 29
# 1Min lanes' 10 days: the assembler consumes only the current
# session's first five minutes. The blocker
# test_gamma_window_20261116 pins the effective 1Min coverage of
# INTRADAY_FETCHES against UNIVERSE15 so drift fails loudly.
UNIVERSE15_1MIN_ADDITIONS = ("IWM", "DIA", "XLK", "XLF", "XLV",
                             "XLI", "XLP", "XLU", "XLB", "XLY")
UNIVERSE15_1MIN_DAYS = 10
INTRADAY_FETCHES = INTRADAY_FETCHES + tuple(
    (sym, "1Min", UNIVERSE15_1MIN_DAYS)
    for sym in UNIVERSE15_1MIN_ADDITIONS)
CRYPTO_FETCHES = (("ADA/USD", "1Hour", 30), ("ENJ/USD", "1Min", 7),
                  ("LINK/USD", "4Hour", 90), ("BTC/USD", "1Day", 500),
                  # FEED80-WARM-20261114: ETH/USD daily (the
                  # aster_native SMA200 sleeves' missing leg; 500
                  # days mirrors the BTC fetch and holds the 200
                  # completed sessions the gate needs) and SOL/USD
                  # 15Min (donchian_crypto's validated tape; 30 days
                  # mirrors the other 15Min lanes).
                  ("ETH/USD", "1Day", 500), ("SOL/USD", "15Min", 30),
                  # F4-CRYPTO-BARKEY-20261114: serve ADA's native
                  # 4Hour spot frame too (90 days ~= 540 bars, the
                  # LINK fetch's shape); until a snapshot carries
                  # it, the Aster ADA engines resample the 1Hour
                  # tape above (desk3/crypto_bars.py).
                  ("ADA/USD", "4Hour", 90),
                  # PF-PAIRED-RV-20261116 (MAKE-IT-WORK Decision C,
                  # 2026-11-16): serve BTC/USD's native 4Hour spot
                  # frame too (90 days ~= 540 bars, the LINK/ADA
                  # 4Hour shape) -- the paired relative-value
                  # anchor leg of the four short-side PF spot
                  # variations reads BTC/USD|4Hour from the same
                  # served tape route; no second tape source.
                  ("BTC/USD", "4Hour", 90))

# ENJ-FEED-CONV27-20261115: ENJ/USD is the one crypto pair no
# Alpaca product serves (the asset is unlisted; broker 42210000
# asset-not-found, proven 2026-10-30/31), so the Alpaca route
# above returns nothing for it and the warm cache carried no ENJ
# series at all: the F4 resolver's persisted step-2 tape
# (ENJ/USD|4Hour) existed only inside live cycle snapshots, and
# the conversion grader (desk3/conversion_shadow.py SeriesBook)
# had no ENJ tape to price on. The desk's stamped ENJ source is
# Kraken public spot (desk3/producers3.py KrakenProducer serves
# the same tape live into cycle snapshots); this fetch persists
# that same tape into the warm cache in the family's record form
# ({t,o,h,l,c,v} rows, ISO stamps), 90 days at 4Hour ~= 540 bars,
# the LINK fetch's shape. Fail-closed like every fetch family
# here: any failure leaves the key unproduced, never a fabricated
# or substituted series.
KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
KRAKEN_SPOT_FETCHES = (("ENJ/USD", "ENJUSD", "4Hour", 240, 90),)


def parse_kraken_ohlc(payload):
    """Kraken public OHLC payload -> family record rows (ISO
    stamps), or [] on any defect. Field mapping mirrors
    desk3/producers3.py parse_ohlc_payload exactly (volume is
    candle index 6); only the stamp form differs (ISO here, the
    warm cache's form; epoch there, the snapshot's form)."""
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
    rows = []
    for cd in candles:
        try:
            rows.append({
                "t": datetime.fromtimestamp(
                    int(cd[0]), timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"),
                "o": float(cd[1]), "h": float(cd[2]),
                "l": float(cd[3]), "c": float(cd[4]),
                "v": float(cd[6])})
        except (ValueError, IndexError, TypeError):
            continue
    rows.sort(key=lambda r: r["t"])
    return rows


def _fetch_kraken_spot(pair, interval_min, days, now=None):
    now = now or datetime.now(timezone.utc)
    since = int((now - timedelta(days=days)).timestamp())
    q = urllib.parse.urlencode({"pair": pair,
                                "interval": interval_min,
                                "since": since})
    # EGRESS-1: netfetch (http.client), not urllib — see
    # desk3/netfetch.py.
    from .netfetch import fetch_json
    doc = fetch_json(f"{KRAKEN_OHLC_URL}?{q}",
                     headers={"User-Agent": "midna-desk/1.0"},
                     timeout=60)
    return parse_kraken_ohlc(doc)


def _fetch_crypto(symbol, timeframe, start, env, limit=10000):
    headers = {"APCA-API-KEY-ID": env.get("ALPACA_KEY_ID", ""),
               "APCA-API-SECRET-KEY": env.get("ALPACA_SECRET_KEY", "")}
    out, token = [], None
    while True:
        params = {"symbols": symbol, "timeframe": timeframe,
                  "start": start, "limit": limit, "sort": "asc"}
        if token:
            params["page_token"] = token
        q = urllib.parse.urlencode(params)
        # EGRESS-1: netfetch (http.client), not urllib — see
        # desk3/netfetch.py.
        from .netfetch import fetch_json
        doc = fetch_json(f"{CRYPTO_URL}/bars?{q}", headers=headers,
                         timeout=60)
        for r in (doc.get("bars") or {}).get(symbol) or []:
            out.append({"t": r["t"], "o": r["o"], "h": r["h"],
                        "l": r["l"], "c": r["c"], "v": r["v"]})
        token = doc.get("next_page_token")
        if not token:
            break
    return out


def fetch_all(symbols, env, now=None):
    now = now or datetime.now(timezone.utc)
    fetch_all.last_session_drops = []
    daily_start = (now - timedelta(days=500)).strftime("%Y-%m-%dT00:00:00Z")
    try:
        daily = _fetch(symbols, "1Day", daily_start, env,
                       expected_last=expected_latest_completed_session(now),
                       session_drops=fetch_all.last_session_drops)
    except TypeError as e:
        if "unexpected keyword" not in str(e):
            raise
        # An injected fetch double with the pre-gate signature (the
        # harden batch-4 seam): the integrity gate lives inside the
        # real _fetch, so a double bypasses it by construction;
        # fixture payloads are not market payloads.
        daily = _fetch(symbols, "1Day", daily_start, env)
    hourly = _fetch(symbols, "1Hour",
                    (now - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z"),
                    env)
    bars = {}
    for sym in symbols:
        d = daily.get(sym) or []
        h = hourly.get(sym) or []
        if d:
            bars[sym] = d
            bars[f"{sym}|1Day"] = d
        if h:
            bars[f"{sym}|1Hour"] = h
            bars.setdefault(sym, d or h)
    # HARDEN-B4 extra slices: each family is isolated — a failed
    # timeframe leaves only its own declared keys unproduced.
    for tf, days in EXTRA_TF_FETCHES:
        try:
            extra = _fetch(symbols, tf,
                           (now - timedelta(days=days)).strftime(
                               "%Y-%m-%dT00:00:00Z"), env)
            for sym, rows in extra.items():
                if rows:
                    bars[f"{sym}|{tf}"] = rows
        except Exception:
            pass
    for sym, tf, days in INTRADAY_FETCHES:
        try:
            rows = _fetch([sym], tf,
                          (now - timedelta(days=days)).strftime(
                              "%Y-%m-%dT00:00:00Z"), env).get(sym) or []
            if rows:
                bars[f"{sym}|{tf}"] = rows
        except Exception:
            pass
    for sym, tf, days in CRYPTO_FETCHES:
        try:
            rows = _fetch_crypto(sym, tf,
                                 (now - timedelta(days=days)).strftime(
                                     "%Y-%m-%dT00:00:00Z"), env)
            if rows:
                bars[f"{sym}|{tf}"] = rows
                if sym == "BTC/USD" and tf == "1Day":
                    # fwd_coinbase_sma200 declares the Coinbase-style
                    # pair name; same Alpaca crypto daily product.
                    bars["BTC-USD|1Day"] = rows
                    bars.setdefault("BTC-USD", rows)
                if sym == "ETH/USD" and tf == "1Day":
                    # FEED80-WARM-20261114: the aster_native SMA200
                    # engines read the same Coinbase-style pair name
                    # (ETH-USD|1Day); same alias treatment as BTC.
                    bars["ETH-USD|1Day"] = rows
                    bars.setdefault("ETH-USD", rows)
                if sym == "SOL/USD" and tf == "15Min":
                    # FEED80-WARM-20261114: donchian_crypto declares
                    # the bare pair name (SOLUSD|15Min); same Alpaca
                    # crypto product.
                    bars["SOLUSD|15Min"] = rows
        except Exception:
            pass
    # ENJ-FEED-CONV27-20261115: the Kraken-sourced spot tapes
    # (KRAKEN_SPOT_FETCHES): the pairs Alpaca does not list, served
    # from the desk's stamped Kraken source in the same record
    # form. Isolated per entry like every family above: a Kraken
    # failure leaves only its own key unproduced.
    for sym, pair, tf, interval_min, days in KRAKEN_SPOT_FETCHES:
        try:
            rows = _fetch_kraken_spot(pair, interval_min, days, now)
            if rows:
                bars[f"{sym}|{tf}"] = rows
        except Exception:
            pass
    return bars


class WarmBars:
    """Callable producer: (pctx) -> {"bars": {...}} or {} on failure."""

    def __init__(self, root, env=None, fetcher=None, max_age_s=3600,
                 env_resolver=None):
        self.root = root
        self.env = env
        self.env_resolver = env_resolver  # callable -> env dict, lazy
        self.fetcher = fetcher or fetch_all
        self.max_age_s = max_age_s
        self.cache_path = os.path.join(root, "state", "warm_bars.json")
        self.last_error = None
        self.last_session_drops = []
        self._parsed = None  # R6: (mtime_ns, size, fetched, bars)

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        cached = self._read_cache(now)
        if cached is not None:
            return {"bars": cached}
        try:
            env = self.env
            if env is None and self.env_resolver is not None:
                env = self.env_resolver()
            bars = self.fetcher(desk_symbols(self.root), env or {}, now)
        except Exception as e:  # fail closed: no bars key, sleeves UNFED
            self.last_error = f"{type(e).__name__}:{e}"
            return {}
        # BARS-INTEGRITY-20261029: per symbol session drops from the
        # daily gate, named on the producer for the cycle roll's
        # producer error surface and for forensics.
        self.last_session_drops = list(
            getattr(self.fetcher, "last_session_drops", None) or [])
        if not bars:
            self.last_error = "empty_fetch"
            return {}
        try:
            tmp = self.cache_path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump({"fetched_at": now.isoformat(), "bars": bars}, fh)
            os.replace(tmp, self.cache_path)
        except OSError:
            pass  # cache is an optimization; the live bars still serve
        return {"bars": bars}

    def _read_cache(self, now):
        # R6 (2026-10-25): the 18MB cache file was re-parsed from disk
        # on EVERY cycle (measured 1.32s). The parsed bars are memoized
        # on the file's (mtime_ns, size): the producer replaces the
        # file atomically, so an unchanged key means unchanged content
        # and the identical dict is served; any rewrite re-parses.
        # Freshness semantics are unchanged (fetched_at vs max_age_s).
        try:
            st = os.stat(self.cache_path)
            key = (st.st_mtime_ns, st.st_size)
            if self._parsed is None or self._parsed[0] != key:
                doc = json.load(open(self.cache_path))
                fetched = datetime.fromisoformat(doc["fetched_at"])
                self._parsed = (key, fetched, doc["bars"])
            _, fetched, bars = self._parsed
            if (now - fetched).total_seconds() <= self.max_age_s:
                return bars
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return None
