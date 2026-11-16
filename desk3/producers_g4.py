"""G4 producer wiring, batch 4 (HARDEN cure batch 4, 2026-10-24).

Families cured here (HARDEN-AUDIT G4): xsp_state, bars_secondary,
bars_1day + vix, bars:<symbol>:<timeframe> keys, saty_setups, and the
file-served misc families qulla + buyback_scan. Every producer fails
closed: an unavailable/stale source returns {} and its dependents stay
UNFED by name (CURE3-1) — never FED on fabricated data.

Sources, per family:
  bars_daily / bars_hourly / bars_intraday / bars_timeframes
      Projections of the ONE warm bars product (desk3/warm.py). The
      projection producers read the warm producer's own cache file
      (state/warm_bars.json, same 3600s freshness rule WarmBars
      itself applies) and return MARKER values — {derived_from,
      timeframe, symbols, bar_counts, asof} — not copies of the bars.
      The sleeves' data path is view["bars"] (port4/port_b5/laz
      contexts all read it); these keys are the registry declarations
      of slices of that product, and duplicating ~6MB of bars per key
      per snapshot would be pure waste (state/snapshots is already
      >1GB). A timeframe key is returned ONLY when the warm product
      actually contains that (symbol, timeframe) slice.
  vix   Yahoo ^VIX daily chart, PRICE ONLY (the desk's sanctioned
        Yahoo route: hourly Yahoo volume is corrupt desk-wide, daily
        closes are price data). -> {"vix": float(last close),
        "bars:VIX:1Day": [daily rows]}. Cached state/vix_daily.json.
  bars_secondary
        Yahoo daily bars (price only) for the Aster R19 ETF interval
        universe — the archive design's secondary provider, paired
        against the Alpaca SIP primary in desk3/aster_etf_b9.py.
        Cached state/bars_secondary.json.
  calendar
        The desk's own trading calendar (core.data.is_trading_day +
        core.early_close), computed, never fetched: session,
        previous_session, first_session_of_week, weekly_pm_expiry,
        open. Consumers: aster_b4 (XSP), aster_batch1/3 gates.
  xsp_index_regime
        xsp_state = {weekly_bars, prior_digitals, adjacent_put_symbols}
        weekly_bars: ^XSP daily (Yahoo, price only) aggregated to
        weeks. adjacent pair + current digital: the live XSP put
        chain via desk3.producers.build_options_payload (the batch-2
        options source — ONE chain truth). prior_digitals: the
        producer's own ledger (state/xsp_digitals.json); one
        observation finalizes per weekly expiry, so the sleeve's
        >=26-observation gate refuses entries until real history
        accrues — the producer never backfills invented digitals.
  saty_setup_families
        Translates the desk's OWN published Best Setups doc
        (state/setups_latest.json, golden inputs as fallback — the
        same docs cycle._load_setups_docs serves) into SPY candidate
        rows {symbol, direction, entry, invalidation, targets,
        family, context, age_min} for aster_saty_research's ranker.
        The archive's 10 Saty families are absent (G1/G4 source
        ruling); this producer feeds the shell from the only setup
        source that exists on this desk, and says so.
  qulla / buyback_scan
        Serving producers over the desk cache layout the v2 warmer
        route used (cache/qulla/proposals.json written by
        desk3/qulla_scan.py running the upstream Qullamaggie engine;
        cache/scan/buyback.json written by desk3/buyback_scan.py, the
        EDGAR scanner). qulla is served ONLY when the persisted
        session equals today's ET session (a stale file never
        trades — the adapter re-checks the same rule). buyback_scan
        is served only inside the sleeve's own SCAN_MAX_AGE_DAYS=8
        freshness gate, with scan_age_days computed here.

opening_events is deliberately NOT produced here: its consumers
require causal received_at stamps <=5s after a 09:35 ET break, which
a 60s-cycle producer cannot emit without fabricating timestamps.
It stays UNFED by name (see BUGLOG HARDEN-B4-OPENING).

Fetchers are injectable so blockers prove behavior without network.
"""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from datetime import date, datetime, time as _time, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
_YAHOO_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) muse-desk-v3"}
WARM_CACHE_MAX_AGE_S = 3600
FILE_CACHE_MAX_AGE_S = 3600
BUYBACK_MAX_AGE_DAYS = 8.0  # sleeves/earnings_buyback SCAN_MAX_AGE_DAYS


def _get_json(url, headers=None, timeout=30):
    # EGRESS-1: netfetch (http.client), not urllib — see desk3/netfetch.py.
    from .netfetch import fetch_json
    return fetch_json(url, headers=headers or {}, timeout=timeout)


def _read_json_file(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write_json_file(path, doc):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(doc, fh)
        os.replace(tmp, path)
    except OSError:
        pass


# ------------------------------------------------------------------ yahoo
def fetch_yahoo_daily(symbol, range_="2y"):
    """Yahoo daily chart (price only) -> [{t,o,h,l,c,v}] ascending.

    t follows the desk daily-bar convention: midnight ET as 04:00Z.
    """
    q = urllib.parse.urlencode({"range": range_, "interval": "1d"})
    doc = _get_json(f"{YAHOO_URL}{urllib.parse.quote(symbol)}?{q}",
                    headers=_YAHOO_UA)
    result = ((doc.get("chart") or {}).get("result") or [None])[0]
    if not result:
        return []
    stamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    opens, highs = quote.get("open") or [], quote.get("high") or []
    lows, closes = quote.get("low") or [], quote.get("close") or []
    vols = quote.get("volume") or []
    rows = []
    for i, ts in enumerate(stamps):
        try:
            c = closes[i]
            if c is None:
                continue
            d = datetime.fromtimestamp(ts, timezone.utc).astimezone(ET).date()
            rows.append({"t": f"{d.isoformat()}T04:00:00Z",
                         "o": float(opens[i] if opens[i] is not None else c),
                         "h": float(highs[i] if highs[i] is not None else c),
                         "l": float(lows[i] if lows[i] is not None else c),
                         "c": float(c),
                         "v": float(vols[i] or 0) if i < len(vols) else 0.0})
        except (TypeError, ValueError, IndexError):
            continue
    return rows


class YahooDailyCached:
    """One Yahoo daily symbol, cached under state/ (fresh < 3600s)."""

    def __init__(self, root, symbol, cache_name, fetcher=None):
        self.root = root
        self.symbol = symbol
        self.fetcher = fetcher or fetch_yahoo_daily
        self.cache_path = os.path.join(root, "state", cache_name)
        self.last_error = None

    def rows(self, now):
        doc = _read_json_file(self.cache_path)
        if isinstance(doc, dict) and doc.get("rows"):
            try:
                fetched = datetime.fromisoformat(doc["fetched_at"])
                if (now - fetched).total_seconds() <= FILE_CACHE_MAX_AGE_S:
                    return doc["rows"]
            except (ValueError, KeyError, TypeError):
                pass
        try:
            rows = self.fetcher(self.symbol)
        except Exception as e:  # fail closed
            self.last_error = f"{type(e).__name__}:{e}"
            return doc.get("rows") if isinstance(doc, dict) and doc.get("rows") else []
        if rows:
            _write_json_file(self.cache_path,
                             {"fetched_at": now.isoformat(), "rows": rows})
            return rows
        self.last_error = "empty_fetch"
        return doc.get("rows") if isinstance(doc, dict) and doc.get("rows") else []


# ------------------------------------------------------------- bars slices
_TF_NORM = {"1day": "1Day", "1hour": "1Hour", "1week": "1Week",
            "15min": "15Min", "5min": "5Min", "1min": "1Min",
            "4hour": "4Hour"}


def warm_bars_map(root, now):
    """The warm bars product from its cache file, or None if the
    cache is missing/stale by WarmBars' own freshness rule."""
    doc = _read_json_file(os.path.join(root, "state", "warm_bars.json"))
    if not isinstance(doc, dict) or not isinstance(doc.get("bars"), dict):
        return None
    try:
        fetched = datetime.fromisoformat(doc["fetched_at"])
    except (ValueError, KeyError, TypeError):
        return None
    if (now - fetched).total_seconds() > WARM_CACHE_MAX_AGE_S:
        return None
    return doc["bars"]


def _tf_index(bars):
    """{"1Day": {SYM: n_rows}, ...} from a warm bars map."""
    idx = {}
    for key, rows in (bars or {}).items():
        if "|" not in key or not isinstance(rows, list):
            continue
        sym, tf = key.rsplit("|", 1)
        tf = _TF_NORM.get(tf.lower(), tf)
        idx.setdefault(tf, {})[sym] = len(rows)
    return idx


def _marker(tf, sym_counts, asof):
    return {"derived_from": "bars", "timeframe": tf,
            "symbols": sorted(sym_counts),
            "bar_counts": {s: sym_counts[s] for s in sorted(sym_counts)},
            "asof": asof}


class BarsProjection:
    """Outputs marker keys for slices of the warm bars product.

    mode="tf":   one output key per timeframe ("bars_1day" style) —
                 returned only when that timeframe exists in the map.
    mode="keys": the literal "bars:<sym>:<tf>" / "bars:*:<tf>" registry
                 keys — each returned only when the map contains that
                 slice ("*" = any symbol has the timeframe).
    """

    def __init__(self, root, outputs, mode="tf"):
        self.root = root
        self.outputs = tuple(outputs)
        self.mode = mode
        self.last_error = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        bars = warm_bars_map(self.root, now)
        if bars is None:
            self.last_error = "warm_bars_absent_or_stale"
            return {}
        idx = _tf_index(bars)
        asof = now.isoformat()
        out = {}
        for key in self.outputs:
            if self.mode == "tf":
                tf = {"bars_1day": "1Day", "bars_1hour": "1Hour",
                      "bars_5min": "5Min", "bars_1min": "1Min"}.get(key)
                if tf and idx.get(tf):
                    out[key] = _marker(tf, idx[tf], asof)
            else:  # literal bars:<sym>:<tf>
                parts = key.split(":")
                if len(parts) != 3:
                    continue
                _, sym, tf = parts
                tf = _TF_NORM.get(tf.lower(), tf)
                counts = idx.get(tf) or {}
                if sym == "*":
                    if counts:
                        out[key] = _marker(tf, counts, asof)
                elif sym in counts:
                    out[key] = _marker(tf, {sym: counts[sym]}, asof)
        return out


# --------------------------------------------------------------------- vix
class VixProducer:
    """^VIX daily close (scalar, the laz/q07 consumer shape) + the
    literal bars:VIX:1Day slice (real rows; single symbol, cheap)."""

    def __init__(self, root, fetcher=None):
        self.daily = YahooDailyCached(root, "^VIX", "vix_daily.json",
                                      fetcher=fetcher)
        self.last_error = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        rows = self.daily.rows(now)
        if not rows:
            self.last_error = self.daily.last_error or "no_vix_rows"
            return {}
        return {"vix": float(rows[-1]["c"]), "bars:VIX:1Day": rows}


# ------------------------------------------------------------ bars_secondary
class SecondaryBars:
    """Yahoo daily histories for the R19 ETF interval universe."""

    UNIVERSE = ("QQQ", "SPY", "SMH", "XLB", "XLC", "XLE", "XLF", "XLI",
                "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")

    def __init__(self, root, fetcher=None):
        self.root = root
        self.fetcher = fetcher or fetch_yahoo_daily
        self.cache_path = os.path.join(root, "state", "bars_secondary.json")
        self.last_error = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        doc = _read_json_file(self.cache_path)
        if isinstance(doc, dict) and doc.get("bars"):
            try:
                fetched = datetime.fromisoformat(doc["fetched_at"])
                if (now - fetched).total_seconds() <= FILE_CACHE_MAX_AGE_S:
                    return {"bars_secondary": doc["bars"]}
            except (ValueError, KeyError, TypeError):
                pass
        bars = {}
        for sym in self.UNIVERSE:
            try:
                rows = self.fetcher(sym)
            except Exception as e:
                self.last_error = f"{type(e).__name__}:{e}"
                rows = []
            if rows:
                bars[sym] = rows
        if not bars:
            if isinstance(doc, dict) and doc.get("bars"):
                return {"bars_secondary": doc["bars"]}
            self.last_error = self.last_error or "empty_fetch"
            return {}
        _write_json_file(self.cache_path,
                         {"fetched_at": now.isoformat(), "bars": bars})
        return {"bars_secondary": bars}


# ----------------------------------------------------------------- calendar
def build_calendar(today):
    """Desk trading-calendar facts for ET date `today` (a date).

    weekly_pm_expiry: the Friday of today's ISO week (the XSP weekly
    PM expiry convention); when Friday is not a trading day the last
    trading day on/before it is used.
    """
    from core.data import is_trading_day
    prev = today - timedelta(days=1)
    while not is_trading_day(prev):
        prev -= timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    first = not any(is_trading_day(monday + timedelta(days=i))
                    for i in range(today.weekday()))
    friday = monday + timedelta(days=4)
    expiry = friday
    while not is_trading_day(expiry) and expiry > monday:
        expiry -= timedelta(days=1)
    open_et = datetime.combine(today, _time(9, 30), tzinfo=ET)
    return {"session": today.isoformat(),
            "previous_session": prev.isoformat(),
            "first_session_of_week": bool(first and is_trading_day(today)),
            "weekly_pm_expiry": expiry.isoformat(),
            "open": open_et.isoformat()}


class CalendarProducer:
    def __init__(self, date_fn=None):
        self.date_fn = date_fn  # injectable for fixtures

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        today = self.date_fn() if self.date_fn else now.astimezone(ET).date()
        try:
            return {"calendar": build_calendar(today)}
        except Exception:
            return {}


# ---------------------------------------------------------------- xsp_state
def aggregate_weekly(daily_rows):
    """Daily rows -> weekly bars [{week_end,o,h,l,c,complete}]."""
    weeks = {}
    for r in daily_rows or []:
        d = date.fromisoformat(str(r["t"])[:10])
        monday = d - timedelta(days=d.weekday())
        w = weeks.setdefault(monday, [])
        w.append((d, r))
    out = []
    for monday in sorted(weeks):
        rows = sorted(weeks[monday], key=lambda x: x[0])
        out.append({"week_end": rows[-1][0].isoformat(),
                    "o": float(rows[0][1]["o"]),
                    "h": max(float(x[1]["h"]) for x in rows),
                    "l": min(float(x[1]["l"]) for x in rows),
                    "c": float(rows[-1][1]["c"]),
                    "complete": True})
    return out


def _xsp_chain_rows(env, now):
    """Live XSP chain rows via the batch-2 options source."""
    from desk3.producers import build_options_payload
    payload = build_options_payload(["XSP"], env, now) or {}
    rows = []
    for payload_v in (payload.get("options") or {}).values():
        if isinstance(payload_v, dict):
            for chain_rows in (payload_v.get("chains") or {}).values():
                if isinstance(chain_rows, list):
                    rows.extend(r for r in chain_rows if isinstance(r, dict))
    return rows


class XspStateProducer:
    """xsp_state for the Aster XSP put-credit books (desk3/aster_b4).

    Ledger (state/xsp_digitals.json): {expiry_iso: {"value": float,
    "pair": [lo_sym, hi_sym]}} — the current week's observation is
    (re)computed from the live chain each cycle; an observation is
    served in prior_digitals only once its expiry is in the past,
    so history accrues one real observation per week.
    """

    def __init__(self, root, env=None, env_resolver=None, daily_fetcher=None,
                 chain_fetcher=None):
        self.root = root
        self.env = env
        self.env_resolver = env_resolver
        self.daily = YahooDailyCached(root, "^XSP", "xsp_daily.json",
                                      fetcher=daily_fetcher)
        self.chain_fetcher = chain_fetcher  # (env, now) -> rows
        self.ledger_path = os.path.join(root, "state", "xsp_digitals.json")
        self.last_error = None

    def _env(self):
        if self.env is not None:
            return self.env
        if self.env_resolver is not None:
            return self.env_resolver() or {}
        return {}

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        today = now.astimezone(ET).date()
        daily = self.daily.rows(now)
        if not daily:
            self.last_error = self.daily.last_error or "no_xsp_daily"
            return {}
        weekly = aggregate_weekly(daily)
        spot = float(daily[-1]["c"])
        cal = build_calendar(today)
        expiry = cal["weekly_pm_expiry"]
        ledger = _read_json_file(self.ledger_path)
        if not isinstance(ledger, dict):
            ledger = {}
        pair = []
        # Current-week adjacent pair + digital from the live chain.
        try:
            rows = (self.chain_fetcher(self._env(), now)
                    if self.chain_fetcher else _xsp_chain_rows(self._env(), now))
        except Exception as e:
            self.last_error = f"chain:{type(e).__name__}:{e}"
            rows = []
        puts = [r for r in rows or []
                if r.get("underlying") == "XSP" and r.get("right") == "put"
                and str(r.get("expiry"))[:10] == expiry]
        strikes = sorted({float(r["strike"]) for r in puts
                          if r.get("strike") is not None})
        by_strike = {}
        for r in puts:
            by_strike.setdefault(float(r["strike"]), r)
        lo = max((s for s in strikes if s < spot), default=None)
        hi = min((s for s in strikes if s > spot), default=None)
        if lo is not None and hi is not None:
            adjacent = [s for s in strikes if lo <= s <= hi]
            if len(adjacent) == 2 and hi > lo:
                r_lo, r_hi = by_strike[lo], by_strike[hi]
                try:
                    mid_lo = (float(r_lo["bid"]) + float(r_lo["ask"])) / 2
                    mid_hi = (float(r_hi["bid"]) + float(r_hi["ask"])) / 2
                    value = (mid_hi - mid_lo) / (hi - lo)
                    if 0 < value < 1:
                        ledger[expiry] = {"value": value,
                                          "pair": [r_lo["symbol"], r_hi["symbol"]]}
                        _write_json_file(self.ledger_path, ledger)
                        pair = [r_lo["symbol"], r_hi["symbol"]]
                except (TypeError, ValueError, KeyError):
                    pair = []
        if not pair and expiry in ledger:
            pair = list(ledger[expiry].get("pair") or [])
        prior = [{"week_end": k, "value": float(v["value"])}
                 for k, v in sorted(ledger.items())
                 if k < today.isoformat()
                 and isinstance(v, dict) and v.get("value") is not None]
        return {"xsp_state": {"weekly_bars": weekly,
                              "prior_digitals": prior,
                              "adjacent_put_symbols": pair}}


# --------------------------------------------------------------- saty_setups
class SatySetupsProducer:
    """Best Setups published doc -> SPY candidate rows for the
    aster_saty_research ranker shell (see module docstring)."""

    def __init__(self, root):
        self.root = root
        self.last_error = None

    def _doc(self):
        state = os.path.join(self.root, "state")
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for path in (os.path.join(state, "setups_latest.json"),
                     os.path.join(repo, "best_setups", "golden", "inputs",
                                  "setups_latest.json")):
            doc = _read_json_file(path)
            if isinstance(doc, dict) and isinstance(doc.get("setups"), list):
                return doc
        return None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        doc = self._doc()
        if doc is None:
            self.last_error = "no_setups_doc"
            return {}
        stamp = doc.get("generated_at") or doc.get("as_of") or doc.get("scored_at")
        age_min = None
        try:
            when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            age_min = max(0.0, (now - when).total_seconds() / 60.0)
        except (ValueError, TypeError):
            pass
        out = []
        for row in doc["setups"]:
            if not isinstance(row, dict) or row.get("symbol") != "SPY":
                continue
            try:
                entry = float(row["entry"])
                inval = float(row["stop"])
                target = float(row["target"])
            except (KeyError, TypeError, ValueError):
                continue
            families = row.get("families") or []
            out.append({"symbol": "SPY",
                        "direction": str(row.get("side") or "long"),
                        "entry": entry, "invalidation": inval,
                        "targets": [target],
                        "family": str(families[0]) if families else "best_setups",
                        "context": float(row.get("score") or 0),
                        "age_min": age_min if age_min is not None else 0.0})
        return {"saty_setups": out}


def _expected_qulla_session(today):
    """QULLA-SESSION-RULE-20261108: the session a fresh qulla file
    carries for ET date `today`: today itself on a trading day,
    else the most recent trading day before it. This is the scan's
    own rule (desk3.qulla_scan.default_session: the session names
    the DECISION date and the engine's features are fenced to
    completed sessions before it). The file producer and the
    warmer used to demand session == today's CALENDAR date, a
    rule the scan can never satisfy on a weekend or holiday: the
    producer named stale_qulla_session every cycle, the sleeve
    stayed UNFED, and the warmer relaunched the full engine scan
    every retry window all weekend for a file that was already
    current. One session rule, shared by all three."""
    from core.data import is_trading_day
    d = today
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d.isoformat()


# ------------------------------------------------------------ file-served
class QullaFileProducer:
    """Serves cache/qulla/proposals.json (written by desk3/qulla_scan)
    only when its session is the current decision session (today's
    ET session on a trading day, else the most recent trading
    day's: QULLA-SESSION-RULE-20261108)."""

    def __init__(self, root):
        self.path = os.path.join(root, "cache", "qulla", "proposals.json")
        self.last_error = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        doc = _read_json_file(self.path)
        if not isinstance(doc, dict) or not isinstance(doc.get("proposals"), list):
            self.last_error = "no_qulla_file"
            return {}
        if doc.get("session") != _expected_qulla_session(
                now.astimezone(ET).date()):
            self.last_error = "stale_qulla_session"
            return {}
        # QULLA-EVIDENCE-ERROR (NO-PARTIALS DRIVE 2026-11-11): a
        # scan that FAILED inside the engine still writes a file
        # with the right session and an empty proposals list, and
        # the old shape served it: the sleeves read FED on an
        # engine-failed empty scan and nothing named it (live
        # artifact 2026-11-11: evidence.error "RuntimeError: qulla
        # frames incomplete", intraday_rows 0, proposals []).
        # Fail closed by name, the posture of every other producer:
        # the sleeves go UNFED with the cause on the roll.
        _ev = doc.get("evidence")
        if isinstance(_ev, dict) and _ev.get("error"):
            self.last_error = f"qulla_scan_evidence_error:{_ev.get('error')}"
            return {}
        self.last_error = None
        return {"qulla": doc}


class QullaScanWarmer:
    """QULLA-WIRE-20261104: the missing invocation of desk3/qulla_scan.

    Built-not-wired defect: qulla_scan.py has existed with no caller
    anywhere (cycle, scheduler, cron), so proposals.json sat at
    session 2026-11-02 while QullaFileProducer named
    stale_qulla_session every cycle and qullamaggie_paper stayed
    UNFED. Producer-shaped warmer, TensorWarmer's posture: serves no
    keys; when the file's session is not today's ET session it
    launches the scan DETACHED (its own subprocess, up to its 1800 s
    timeout — a cycle never blocks on it) and drops a per-session
    attempt marker bounding relaunches to one per retry window.
    The file producer keeps naming staleness until a scan lands.
    """

    def __init__(self, root, launcher=None, retry_s=3600):
        self.root = root
        self.launcher = launcher or self._launch_detached
        self.retry_s = retry_s
        self.last_error = None
        qdir = os.path.join(root, "cache", "qulla")
        self._file = os.path.join(qdir, "proposals.json")
        self._marker = os.path.join(qdir, "scan_attempt.json")

    def _launch_detached(self, root):
        import subprocess, sys
        qdir = os.path.join(root, "cache", "qulla")
        os.makedirs(qdir, exist_ok=True)
        log = open(os.path.join(qdir, "scan.log"), "ab")
        proc = subprocess.Popen([sys.executable, "-m", "desk3.qulla_scan"],
                                cwd=root, stdout=log, stderr=log,
                                start_new_session=True)
        # QULLA-DEAD-LAUNCH-20261112: return the child pid so the
        # attempt marker can name the launch it bounds (see __call__).
        return proc.pid

    @staticmethod
    def _pid_alive(pid):
        """True only when /proc shows a live (non-zombie) process.

        A detached scan child that died is either gone from /proc or
        a zombie (Z/X) awaiting reap; both count as dead. Falls back
        to kill(pid, 0) where /proc is unreadable."""
        try:
            with open(f"/proc/{int(pid)}/stat", "rb") as fh:
                stat = fh.read().decode(errors="replace")
            state = stat.rsplit(")", 1)[-1].split()[0]
            return state not in ("Z", "X", "x")
        except FileNotFoundError:
            return False
        except (OSError, IndexError, ValueError):
            try:
                os.kill(int(pid), 0)
                return True
            except PermissionError:
                return True
            except OSError:
                return False

    def _launch_proven_dead(self, attempt):
        """QULLA-DEAD-LAUNCH-20261112: the recorded launch is proven
        dead — its marker carries a pid, that pid is not alive, and
        proposals.json has not been rewritten since the marker (the
        scan's terminal output never landed). Markers without a pid
        (pre-cure shape, injected test launchers) never qualify:
        their suppression semantics are unchanged."""
        pid = attempt.get("pid")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return False
        if self._pid_alive(pid):
            return False
        try:
            marker_mtime = os.path.getmtime(self._marker)
        except OSError:
            return False
        try:
            produced_mtime = os.path.getmtime(self._file)
        except OSError:
            produced_mtime = 0.0
        return produced_mtime <= marker_mtime

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        today = now.astimezone(ET).date().isoformat()
        doc = _read_json_file(self._file)
        # QULLA-SESSION-RULE-20261108: the warmer's freshness test
        # is the same shared session rule as the file producer's;
        # a most-recent-trading-day file on a weekend is current
        # and launches nothing.
        # SLEEVE-FIRING-20261111: a doc whose evidence carries an
        # engine error is NOT a completed scan. The 2026-11-11
        # session's first attempt launched pre-market, the engine
        # failed on zero intraday frames, and the errored doc's
        # session stamp suppressed every retry for the whole day
        # while QullaFileProducer fail-closed on the same error.
        # An errored doc falls through to the attempt marker below
        # (one relaunch per retry window) so the scan retries once
        # intraday frames exist.
        _ev = doc.get("evidence") if isinstance(doc, dict) else None
        _errored = isinstance(_ev, dict) and bool(_ev.get("error"))
        if isinstance(doc, dict) and not _errored and \
                doc.get("session") == \
                _expected_qulla_session(now.astimezone(ET).date()):
            self.last_error = None
            return {}
        # QULLA-PREOPEN-DEFERRAL-20261113: before 09:47 ET on a
        # trading day, a scan for today's session cannot succeed
        # (the engine's intraday frame is built from today's RTH
        # 1Min bars only; see desk3.qulla_scan.scan_deferred).
        # Launching anyway writes the errored file the producer
        # fail-closes on AND stamps the attempt marker, which then
        # suppresses the first post-open retry for the full retry
        # window. In the deferral window: no launch, no marker, no
        # error — the first post-09:47 call launches into a session
        # whose bars exist.
        from desk3.qulla_scan import scan_deferred
        if scan_deferred(
                _expected_qulla_session(now.astimezone(ET).date()),
                now.astimezone(ET)):
            self.last_error = None
            return {}
        attempt = _read_json_file(self._marker)
        if isinstance(attempt, dict) and attempt.get("session") == today:
            try:
                age = (now - datetime.fromisoformat(
                    str(attempt.get("ts")))).total_seconds()
            except (TypeError, ValueError):
                age = None
            # QULLA-DEAD-LAUNCH-20261112: the marker bounds relaunches
            # while a scan may be RUNNING; it must not shield a launch
            # that provably died with zero output. Live artifact
            # 2026-11-12: the runner's first post-boot pass stamped
            # the marker at 15:38:27Z and launched, the child produced
            # nothing at all (no bar file touched, no scan.log append,
            # no proposals rewrite, no process alive at the next
            # checks, no OOM in the boot journal) and its death left
            # no trace anywhere — the marker then suppressed every
            # retry for the full window while the file producer named
            # the stale pre-open error and the sleeve sat UNFED well
            # after the open. A proven-dead launch falls through and
            # relaunches in this same call; the fresh marker (live
            # pid) re-arms the bound.
            if age is not None and age < self.retry_s and \
                    not self._launch_proven_dead(attempt):
                return {}
        try:
            # Launch FIRST, stamp the marker after: pre-cure the
            # marker was written before the launch, so a launcher
            # exception still left a marker suppressing retries for
            # the whole window. A failed launch now leaves no marker
            # and is retried on the next call, named each time.
            pid = self.launcher(self.root)
            os.makedirs(os.path.dirname(self._marker), exist_ok=True)
            marker = {"session": today, "ts": now.isoformat()}
            if isinstance(pid, int) and not isinstance(pid, bool) \
                    and pid > 0:
                marker["pid"] = pid
            with open(self._marker, "w") as fh:
                json.dump(marker, fh)
        except Exception as e:  # launch failure is named, never raised
            self.last_error = f"qulla_scan_launch:{type(e).__name__}:{e}"
            return {}
        self.last_error = None
        return {}


class OpeningGammaWarmer:
    """GAMMA-WINDOW-20261116: the missing in-window consumer for
    aster_open_gamma_a/b, QullaScanWarmer's shape exactly.

    The pair's strategy consumes an opening-event row only while
    its break is <=5s old and only inside 09:35-09:45 ET, but the
    fleet cycle that feeds them runs 691-1671s + 60s at an
    unanchored phase, so no main-cycle evaluation could ever land
    in the window fresh (Lane E, desk full audit 2026-11-16).
    Producer-shaped warmer: serves no keys; on the first cycle
    touching 09:30-09:35 ET on a weekday it launches the
    dedicated scan loop (desk3/opening_gamma_scan.py) DETACHED —
    its own subprocess polling at <=5s through 09:45 ET for the
    WINDOW_SIDS pair only, so the main cycle never blocks — and
    drops a per-session attempt marker bounding relaunches to
    one per session. Switch: a gamma_window_scan=False in the
    producer context restores the pre-cure behaviour (no launch).
    """

    def __init__(self, root, launcher=None):
        self.root = root
        self.launcher = launcher or self._launch_detached
        self.last_error = None
        odir = os.path.join(root, "state", "opening_gamma_window")
        self._marker = os.path.join(odir, "scan_attempt.json")

    def _launch_detached(self, root):
        import subprocess, sys
        odir = os.path.join(root, "state", "opening_gamma_window")
        os.makedirs(odir, exist_ok=True)
        log = open(os.path.join(odir, "scan.log"), "ab")
        proc = subprocess.Popen(
            [sys.executable, "-m", "desk3.opening_gamma_scan", root],
            cwd=root, stdout=log, stderr=log, start_new_session=True)
        return proc.pid

    def __call__(self, pctx):
        from desk3.opening_gamma_scan import (LAUNCH_START,
                                              WINDOW_START,
                                              window_scan_on)
        pctx = pctx or {}
        now = pctx.get("now") or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now_et = now.astimezone(ET)
        if not window_scan_on(pctx):
            self.last_error = None
            return {}
        if now_et.weekday() >= 5 or not (
                LAUNCH_START <= now_et.time() < WINDOW_START):
            self.last_error = None
            return {}
        today = now_et.date().isoformat()
        attempt = _read_json_file(self._marker)
        if isinstance(attempt, dict) and \
                attempt.get("session") == today:
            self.last_error = None
            return {}
        try:
            # Launch FIRST, stamp the marker after (the
            # QullaScanWarmer post-cure order): a failed launch
            # leaves no marker and is retried on the next cycle,
            # named each time.
            pid = self.launcher(self.root)
            os.makedirs(os.path.dirname(self._marker), exist_ok=True)
            marker = {"session": today, "ts": now.isoformat()}
            if isinstance(pid, int) and not isinstance(pid, bool) \
                    and pid > 0:
                marker["pid"] = pid
            with open(self._marker, "w") as fh:
                json.dump(marker, fh)
        except Exception as e:  # launch failure is named, never raised
            self.last_error = \
                f"opening_gamma_launch:{type(e).__name__}:{e}"
            return {}
        self.last_error = None
        return {}


BUYBACK_REFRESH_AGE_DAYS = 1.0


def _buyback_scan_age_days(doc, now):
    """Age in days of a buyback scan doc's scanned_at stamp, or
    None when the doc/stamp is unusable. Shared by the file
    producer's gate and the warmer's refresh test so the two can
    never disagree about what stale means."""
    if not isinstance(doc, dict) or not isinstance(doc.get("scan_signals"), list):
        return None
    try:
        when = datetime.fromisoformat(str(doc.get("scanned_at")).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (now - when).total_seconds() / 86400.0


class BuybackScanWarmer:
    """BUYBACK-WIRE-20261110: the missing invocation of desk3/buyback_scan.

    Built-not-wired defect, the qulla class exactly: buyback_scan.py
    existed with no caller anywhere (cycle, scheduler, cron), so
    cache/scan/buyback.json sat at the manual CURE1 refresh of
    2026-11-02T05:35Z, BuybackFileProducer named buyback_scan_stale
    once the sleeve's 8-day gate expired 2026-11-10T05:35Z, and the
    gate's cure1 freshness blocker went red (age 8.38d at the
    2026-11-10 morning gate). Producer-shaped warmer, QullaScanWarmer's
    posture: serves no keys; when the file's age passes
    BUYBACK_REFRESH_AGE_DAYS (1 day, far inside the 8-day gate) it
    launches the scan DETACHED (EDGAR pacing over the desk universe
    takes minutes; a cycle never blocks on it) and drops an attempt
    marker bounding relaunches to one per retry window. The scan
    itself stays fail-loud: a total EDGAR failure writes nothing, so
    a dead network never masquerades as a fresh empty scan. The file
    producer keeps naming staleness until a scan lands.
    """

    def __init__(self, root, launcher=None, retry_s=3600):
        self.root = root
        self.launcher = launcher or self._launch_detached
        self.retry_s = retry_s
        self.last_error = None
        sdir = os.path.join(root, "cache", "scan")
        self._file = os.path.join(sdir, "buyback.json")
        self._marker = os.path.join(sdir, "buyback_attempt.json")

    def _launch_detached(self, root):
        import subprocess, sys
        sdir = os.path.join(root, "cache", "scan")
        os.makedirs(sdir, exist_ok=True)
        log = open(os.path.join(sdir, "buyback_scan.log"), "ab")
        subprocess.Popen([sys.executable, "-m", "desk3.buyback_scan"],
                         cwd=root, stdout=log, stderr=log,
                         start_new_session=True)

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        age = _buyback_scan_age_days(_read_json_file(self._file), now)
        if age is not None and 0 <= age <= BUYBACK_REFRESH_AGE_DAYS:
            self.last_error = None
            return {}
        attempt = _read_json_file(self._marker)
        if isinstance(attempt, dict):
            try:
                age_s = (now - datetime.fromisoformat(
                    str(attempt.get("ts")))).total_seconds()
            except (TypeError, ValueError):
                age_s = None
            if age_s is not None and 0 <= age_s < self.retry_s:
                return {}
        try:
            os.makedirs(os.path.dirname(self._marker), exist_ok=True)
            with open(self._marker, "w") as fh:
                json.dump({"ts": now.isoformat()}, fh)
            self.launcher(self.root)
        except Exception as e:  # launch failure is named, never raised
            self.last_error = f"buyback_scan_launch:{type(e).__name__}:{e}"
            return {}
        self.last_error = None
        return {}


class BuybackFileProducer:
    """Serves cache/scan/buyback.json (written by desk3/buyback_scan)
    inside the sleeve's 8-day freshness gate, age computed here."""

    def __init__(self, root):
        self.path = os.path.join(root, "cache", "scan", "buyback.json")
        self.last_error = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        doc = _read_json_file(self.path)
        if not isinstance(doc, dict) or not isinstance(doc.get("scan_signals"), list):
            self.last_error = "no_buyback_file"
            return {}
        stamp = doc.get("scanned_at")
        try:
            when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            age_days = (now - when).total_seconds() / 86400.0
        except (ValueError, TypeError):
            self.last_error = "buyback_no_scan_stamp"
            return {}
        if age_days < 0 or age_days > BUYBACK_MAX_AGE_DAYS:
            self.last_error = "buyback_scan_stale"
            return {}
        return {"buyback_scan": {"scan_signals": doc["scan_signals"],
                                 "scan_age_days": age_days}}


class JournalSelfProducer:
    """journal:self / journal:momentum — a sleeve's own journal is a
    desk product, not an external feed: the Desk creates every
    sleeve's state dir and appends its journal every cycle (eval and
    unfed events alike). journal:self is therefore produced by
    construction; journal:momentum (leaps_momentum reads the momentum
    sleeve's journal) is produced only when that journal file exists.
    The port4 context reads the journal from the sleeve's state dir
    directly — these keys are the registry declarations of that
    desk-guaranteed state."""

    def __init__(self, root):
        self.root = root

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        out = {"journal:self": {"source": "per-sleeve state dirs",
                                "asof": now.isoformat()}}
        mom = os.path.join(self.root, "state", "momentum", "journal.jsonl")
        if os.path.exists(mom):
            out["journal:momentum"] = {"source": "state/momentum/journal.jsonl",
                                       "asof": now.isoformat()}
        return out


# ------------------------------------------------------------------ wiring
_BARS_TF_KEYS = ("bars:*:1Day", "bars:*:1Hour", "bars:*:1Week",
                 "bars:QQQ:1Day", "bars:QQQ:15Min", "bars:QQQ:1Min", "bars:QQQ:5Min",
                 "bars:SPY:5Min",
                 "bars:SPY:1Min",
                 "bars:QQQ:30Min", "bars:SPY:30Min",
                 "bars:MDY:30Min", "bars:DIA:30Min",
                 "bars:SOXL:15Min",
                 # SSO-PORT-CONV46-20261115: sso_opus and
                 # sso_opus_notime25 declare bars:SSO:15Min; the
                 # warm layer serves the slice (SSO 15Min fetch)
                 # but the registry key was never declared here,
                 # so the pair read UNFED by name.
                 "bars:SSO:15Min",
                 "bars:BTC-USD:1Day",
                 "bars:ADA/USD:1Hour", "bars:ENJ/USD:1Min",
                 "bars:LINK/USD:4Hour")


def bars_tf_keys():
    """The full bars:<sym>:<tf> registry key set: _BARS_TF_KEYS
    plus, SEGMENT-CONSTRUCTION-20261116 (CONV-88/CONV-108), one
    bars:<SYM>:1Min key per Focus 29 name. The warm layer serves
    those slices (desk3/warm.py FOCUS29_1MIN_SYMBOLS, pinned to
    this same FOCUS29 list); without the registry keys declared
    here the segment sleeves read UNFED by name even though the
    warm product carries their bars (the SSO 15Min cure's shape
    above)."""
    from .overnight_baskets import FOCUS29
    return list(_BARS_TF_KEYS) + [f"bars:{s}:1Min" for s in FOCUS29]


def register_all_g4(desk, root, env=None, env_resolver=None):
    """Wire every batch-4 producer into a Desk. Names mirror the
    engines' own PRODUCERS declarations where they exist."""
    desk.add_producer("bars_daily", BarsProjection(root, ["bars_1day"]),
                      ["bars_1day"], 93600)
    desk.add_producer("bars_hourly", BarsProjection(root, ["bars_1hour"]),
                      ["bars_1hour"], 93600)
    desk.add_producer("bars_intraday",
                      BarsProjection(root, ["bars_5min", "bars_1min"]),
                      ["bars_5min", "bars_1min"], 3600)
    desk.add_producer("bars_timeframes",
                      BarsProjection(root, bars_tf_keys(), mode="keys"),
                      bars_tf_keys(), 3600)
    desk.add_producer("vix", VixProducer(root), ["vix", "bars:VIX:1Day"], 3600)
    desk.add_producer("bars_secondary", SecondaryBars(root),
                      ["bars_secondary"], 3600)
    desk.add_producer("calendar", CalendarProducer(), ["calendar"], 3600)
    desk.add_producer("xsp_index_regime",
                      XspStateProducer(root, env, env_resolver=env_resolver),
                      ["xsp_state"], 900)
    desk.add_producer("saty_setup_families", SatySetupsProducer(root),
                      ["saty_setups"], 60)
    desk.add_producer("journal_self", JournalSelfProducer(root),
                      ["journal:self", "journal:momentum"], 3600)
    desk.add_producer("qulla_warmer", QullaScanWarmer(root), [], 3600)
    # GAMMA-WINDOW-20261116: detached in-window scan launcher for
    # the aster_open_gamma pair (serves no keys, like qulla_warmer).
    desk.add_producer("opening_gamma_warmer",
                      OpeningGammaWarmer(root), [], 3600)
    desk.add_producer("qulla", QullaFileProducer(root), ["qulla"], 3600)
    desk.add_producer("buyback_warmer", BuybackScanWarmer(root), [], 3600)
    desk.add_producer("buyback_scan", BuybackFileProducer(root),
                      ["buyback_scan"], 86400)
