"""The Tensor research plane: the research sleeves' detectors run over the desk's pinned production Tensor engine (v698,
desk/vendor/old_desk_research/tensor_exact, hash-checked before every batch) for the 1,838-name canonical research
roster, in background jobs; the sleeves read the events cache-only.

Inputs — the FolioTend production chart inputs (the engine's own INTERVALS request contract):
  1h   the canonical Yahoo 60m regular-session series, range 1y (desk/feedlib/canonical.py, shared with tensor_swing)
  1d   the Yahoo chart API 1d, range 2y      parsed by the production parseYahooReplicaHistory (forming bar dropped)
  1wk  the Yahoo chart API 1wk, range 10y    likewise
  With Alpaca keys, 1d and 1wk come from batched SIP 1Day / 1Week bars over the same ranges (alpaca_history: about
  190 requests for the roster where Yahoo needs one per name; 1,834 of the 1,838 failed on 2026-10-16 while Yahoo
  refused this host): split-adjusted as Yahoo's OHLC are, completed sessions and weeks only, stamped as Yahoo stamps
  them, through the production parse's bar filter. Yahoo serves the names Alpaca does not. Named divergences, measured
  against Yahoo's own bars: SPY's 120 daily sessions to 2026-10-15 agree in OHLC to Yahoo's float32 rounding
  (<= 0.003%), with SIP volume 0.17% higher at the median; six names' weekly bars agree likewise, except a re-listed
  ticker whose Alpaca history carries its predecessor's prints (CORZ, week of 2024-01-22).
Each job batch runs desk/feedlib/tensor_research.mjs (one node process per CHUNK symbols, WORKERS in parallel): the
replica (display window = the production chart window), the v619 research sidecar, the v615 Swing + its notification
key, the v698 Swing / Swing Transition on the replica decorated by the production native structural engine. Views name
their input window ("fd" = the production window; "ag" = the agentic market scan's 420 daily / 260 weekly bars).

  job_1h(engine)   each completed RTH hour: the roster's 1h frames -> events_1h.json
  job_1d(engine)   after each close: the roster's 1d frames (and on a week's last session the 1wk frames) ->
                   events_1d.json / events_1wk.json, plus the daily context the hourly sleeves read
Detectors live in desk/sleeves/families/tensor_research.py (DETECTORS); this module only moves data. A symbol whose
input is unavailable yields no frame (fail closed) and is listed in the cache's errors."""
import hashlib
import json
import os
import re
import subprocess
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic
from . import tensor as T

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "tensor_research.mjs")
VENDOR = os.path.join(os.path.dirname(HERE), "vendor")
CHUNK = 30
WORKERS = max(1, min(8, (os.cpu_count() or 2) - 1))     # node processes; one core left for the desk
ORIGINS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
REQUEST = {"1d": {"range": "2y", "interval": "1d"}, "1wk": {"range": "10y", "interval": "1wk"}}
AG_WINDOW = {"1d": 420, "1wk": 260}         # tensor_market_scan DAILY_INPUT_BARS / WEEKLY_INPUT_BARS
# the research sources executed by the runner besides the pinned engine (sha256 of the vendored bytes)
RESEARCH_PINS = {
    "foliotend_research/v619/app/lib/foliotend-research-sidecar.ts":
        "ffbc3af7110af150a3a8a66b165d6f6e35ddbf3e0b5ed146af20d4707301b3b5",
    "foliotend_research/v615/lib/tensor-swing-signals.mjs":
        "3b6b64bdd45dfdea47b510aef7740765ef9e1818c680d531fb8f929261f7e4a2",
    "foliotend_research/v615/lib/tensor-swing-notification.mjs":
        "1779203e6828fbf3f973fdbc1503276b347fb5887f1e30f7c2aad1ddda759ba6",
}
_PIN_OK = {}


class ResearchEngineError(RuntimeError):
    pass


def verify():
    T.verify()
    for rel, want in RESEARCH_PINS.items():
        p = os.path.join(VENDOR, rel)
        st = os.stat(p)
        if _PIN_OK.get(rel) == (st.st_mtime_ns, st.st_size):
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got != want:
            raise ResearchEngineError(f"research source drifted: {rel}")
        _PIN_OK[rel] = (st.st_mtime_ns, st.st_size)


def run_batch(jobs, timeout=1800):
    verify()
    try:
        p = subprocess.run(["node", "--no-warnings", RUNNER], input=json.dumps({"jobs": jobs}), capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise ResearchEngineError("node is not available") from e
    try:
        res = json.loads((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError) as e:
        raise ResearchEngineError(f"runner produced no JSON (exit {p.returncode}): {(p.stderr or '')[:300]}") from e
    return res


def frames(jobs, on_result, workers=WORKERS, chunk=CHUNK):
    """run jobs (any iterable: a generator lets fetching overlap the engine) in chunks on parallel node processes;
    on_result(job, result) is called per symbol in submission order as chunks finish. A failed chunk reports each
    of its symbols as {"ok": False, "error": ...}."""
    def one(c):
        try:
            res = run_batch(c)
            by = {(r["symbol"], r["interval"]): r for r in res.get("results") or []}
            return [(j, by.get((j["symbol"].upper(), j["interval"]), {"ok": False, "error": "no result"})) for j in c]
        except Exception as e:
            return [(j, {"ok": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}) for j in c]

    pending = deque()

    def drain(block):
        while pending and (block or pending[0].done()):
            for j, r in pending.popleft().result():
                on_result(j, r)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        buf = []
        for j in jobs:
            buf.append(j)
            if len(buf) >= chunk:
                pending.append(ex.submit(one, buf))
                buf = []
            drain(False)
        if buf:
            pending.append(ex.submit(one, buf))
        drain(True)


def yahoo_payload(symbol, interval, getter=None):
    """the production chart request (`?range=..&interval=..&includePrePost=false&events=div,splits`), query1 then
    query2; the raw JSON (parsed by the runner with the production parser) or None."""
    params = dict(REQUEST[interval], includePrePost="false", events="div,splits")
    if getter is not None:
        return getter(symbol, interval, params)
    from ..data.http import get
    return _two_origins(lambda origin: get(f"{origin}/v8/finance/chart/{symbol}", params), symbol)


def _two_origins(call, symbol):
    """query1 / query2, the first chosen by the symbol so the roster's requests spread over both hosts' pacing."""
    first = int(hashlib.sha1(symbol.encode()).hexdigest(), 16) % 2
    last = None
    for origin in (ORIGINS[first], ORIGINS[1 - first]):
        try:
            return call(origin)
        except Exception as e:                     # next origin
            last = e
    raise ResearchEngineError(f"both Yahoo origins failed for {symbol}: {last!r}")


def canonical_getter(symbol):
    """the canonical 1H request (desk/feedlib/canonical.py PARAMS / HEADERS) spread over both Yahoo hosts."""
    from ..data.http import get
    from .canonical import HEADERS, PARAMS
    return _two_origins(lambda origin: get(f"{origin}/v8/finance/chart/{symbol}", dict(PARAMS), headers=HEADERS),
                        symbol)


def fetch_stream(symbols, load, errors, workers=2):
    """yield (symbol, data) in roster order as load(symbol) returns it; a symbol whose load fails or returns nothing
    is recorded in errors (never substituted)."""
    def one(s):
        try:
            return s, load(s), None
        except Exception as e:
            return s, None, f"{type(e).__name__}: {str(e)[:120]}"

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for s, data, err in ex.map(one, symbols):
            if data and not isinstance(data, Exception):
                yield s, data
            else:
                errors[s] = err or "no data"


# -- daily and weekly history from Alpaca -----------------------------------------------------------------------------
ALPACA_TF = {"1d": "1Day", "1wk": "1Week"}
ALPACA_YEARS = {"1d": 2, "1wk": 10}         # REQUEST's ranges
ALPACA_CHUNK = 200                          # names per multi-symbol request
SIP_DELAY_S = 16 * 60                       # the free plan serves SIP data older than 15 minutes
INVALID = re.compile(r"invalid symbol: ([^\"'\s,}]+)")


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _years_before(t, years):
    d = datetime.fromtimestamp(t, tz=timezone.utc)
    try:
        return d.replace(year=d.year - years).timestamp()
    except ValueError:                          # 29 February
        return d.replace(year=d.year - years, day=28).timestamp()


def valid_bar(b):
    """the production parse's bar filter (parseYahooReplicaHistory): positive prices that the high and low bound."""
    return min(b["o"], b["h"], b["l"], b["c"]) > 0 and b["h"] >= max(b["o"], b["c"]) and b["l"] <= min(b["o"], b["c"])


def alpaca_history(client, symbols, interval, day, now):
    """{symbol: bars} over the Yahoo request's range (2y daily, 10y weekly) through the completed session `day`: SIP
    bars, split-adjusted as Yahoo's OHLC are. A daily bar is stamped at its session open, as Yahoo stamps it (Alpaca
    stamps 00:00 ET); a weekly bar keeps its Monday 00:00 ET stamp (both providers', holiday Mondays included) and is
    kept once its week's last session is `day` or earlier. A name Alpaca calls invalid is dropped from the request
    (one such name fails the whole request with HTTP 400), a name the response omits is asked singly, and names
    Alpaca does not serve are absent."""
    from ..util import parse_ts
    start = _years_before(now, ALPACA_YEARS[interval])
    names = list(symbols)
    for _ in range(len(names) + 1):
        if not names:
            return {}
        try:
            got = client.stock_bars(names, ALPACA_TF[interval], start=_iso(start - 7 * 86400),
                                    end=_iso(now - SIP_DELAY_S), feed="sip", adjustment="split")
            break
        except Exception as e:
            bad = INVALID.search(str(e))
            if not bad or bad.group(1) not in names:
                raise
            names.remove(bad.group(1))
    got = dict(got or {})
    for s in [s for s in names if not got.get(s)] if len(names) > 1 else []:
        # a multi-symbol response can omit a name Alpaca serves alone (DOW's weekly bars, 2026-10-16): asked singly
        try:
            got.update(client.stock_bars([s], ALPACA_TF[interval], start=_iso(start - 7 * 86400),
                                         end=_iso(now - SIP_DELAY_S), feed="sip", adjustment="split") or {})
        except Exception:
            pass
    out = {}
    for s, rows in got.items():
        bars = {}
        for r in rows:
            t = parse_ts(r["t"])
            if interval == "1d":
                d = session_of(t)
                if d > day or not cal.is_trading_day(d):
                    continue
                t = cal.session_open(d)
            elif cal.week_last_session(week_monday(t)) > day:
                continue
            b = {"t": int(t), "o": float(r["o"]), "h": float(r["h"]), "l": float(r["l"]), "c": float(r["c"]),
                 "v": float(r.get("v") or 0)}
            if t >= start and valid_bar(b):
                bars[b["t"]] = b
        if bars:
            out[s] = [bars[k] for k in sorted(bars)]
    return out


def history_stream(symbols, interval, day, now, errors, getter=None, client=None, counts=None):
    """yield (symbol, key, data) in roster order: ("bars", Alpaca's bars) chunk by chunk when a client is given, then
    ("payload", Yahoo's chart) for every name Alpaca did not serve. counts gathers the names each source served."""
    counts = counts if counts is not None else {}
    rest = list(symbols)
    if client is not None:
        rest = []
        for i in range(0, len(symbols), ALPACA_CHUNK):
            chunk = symbols[i:i + ALPACA_CHUNK]
            try:
                got = alpaca_history(client, chunk, interval, day, now)
            except Exception as e:                  # the chunk's names go to Yahoo
                got = {}
                counts["alpaca_error"] = f"{type(e).__name__}: {str(e)[:120]}"
            for s in chunk:
                if got.get(s):
                    counts["alpaca"] = counts.get("alpaca", 0) + 1
                    yield s, "bars", got[s]
                else:
                    rest.append(s)
    for s, p in fetch_stream(rest, lambda s: yahoo_payload(s, interval, getter), errors):
        counts["yahoo"] = counts.get("yahoo", 0) + 1
        yield s, "payload", p


# -- bar calendar ---------------------------------------------------------------------------------------------------
def hour_opens(day):
    from .canonical import session_opens
    return session_opens(day)


def hour_end(t):
    """the end of the canonical hourly bar opened at t (the close for the session's last bar / the 13:00 stub)."""
    day = cal._as_date(t)
    opens = hour_opens(day)
    close = cal.session_close(day)
    if opens and int(t) == opens[-1]:
        return close
    return min(int(t) + 3600, close)


def hour_shift(t, k):
    """the open of the canonical hourly bar k bars after the bar opened at t (k >= 1)."""
    day = cal._as_date(t)
    seq = [o for o in hour_opens(day) if o > int(t)]
    while len(seq) < k:
        day = cal.next_trading_day(day)
        seq += hour_opens(day)
    return seq[k - 1]


def session_of(t):
    """the trading day a daily bar (stamped at any time of its session date, ET) belongs to."""
    return datetime.fromtimestamp(float(t), tz=ET).date()


def week_monday(t):
    d = datetime.fromtimestamp(float(t) + 12 * 3600, tz=timezone.utc).date()
    return d - timedelta(days=d.weekday())


def entry_open(interval, t):
    """the open of the bar after the event bar (bar i+1)."""
    if interval == "1h":
        return hour_shift(t, 1)
    if interval == "1d":
        return cal.session_open(cal.next_trading_day(session_of(t)))
    monday = week_monday(t) + timedelta(days=7)
    d = monday
    while not cal.is_trading_day(d):
        d += timedelta(days=1)
    return cal.session_open(d)


def exit_close(interval, t, h):
    """(close epoch, is_session_close) of the bar h bars after the event bar (the close of bar i+h)."""
    if interval == "1h":
        o = hour_shift(t, h)
        end = hour_end(o)
        return end, end >= cal.session_close(cal._as_date(o))
    if interval == "1d":
        d = cal.next_trading_day(session_of(t), h)
        return cal.session_close(d), True
    last = cal.week_last_session(week_monday(t) + timedelta(days=7 * h))
    return cal.session_close(last), True


def bar_end(interval, t):
    if interval == "1h":
        return hour_end(t)
    if interval == "1d":
        return cal.session_close(session_of(t))
    return cal.session_close(cal.week_last_session(week_monday(t)))


# -- caches ---------------------------------------------------------------------------------------------------------
def cache_dir(root):
    return os.path.join(root, "cache", "tensor_research")


def events_path(root, interval):
    return os.path.join(cache_dir(root), f"events_{interval}.json")


def load_events(root, interval):
    return read_json(events_path(root, interval), None)


def roster():
    from ..sleeves.families.femto_specs import GENOME
    return list(GENOME)


# -- asset classification (tensor_htf_asset_classification, on public listing metadata) ------------------------------
SYMDIR = {"nasdaq": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
          "other": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"}
EXCHANGES = {"A": "AMEX", "N": "NYSE", "P": "ARCA", "Z": "BATS", "V": "IEX"}
FUND_PATTERN = re.compile(r"\b(ETF|ETN|FUND|PORTFOLIO|INDEX|ISHARES|PROSHARES|DIREXION|SPDR|"
                          r"VANECK|WISDOMTREE|GLOBAL X|EXCHANGE[- ]TRADED|2X|3X)\b", re.IGNORECASE)
ASSETS_MAX_AGE_S = 7 * 86400


def classify(name, exchange):
    """the source rule (tensor_htf_asset_classification.classify) on a listing's name and exchange."""
    if str(exchange or "") in {"ARCA", "NYSEARCA", "BATS"} or FUND_PATTERN.search(str(name or "")):
        return "FUND_OR_ETP_EXCLUDED_FROM_STOCK_CROSS_SECTION"
    return "OPERATING_COMPANY_CANDIDATE_CURRENT_METADATA"


def parse_symdir(text, kind):
    """{SYMBOL: {name, exchange}} from a Nasdaq Trader symbol-directory file (test issues and the footer dropped)."""
    out = {}
    lines = [l for l in (text or "").splitlines() if l.strip()]
    if not lines:
        return out
    head = lines[0].split("|")
    for line in lines[1:]:
        if line.startswith("File Creation Time"):
            continue
        row = dict(zip(head, line.split("|")))
        if row.get("Test Issue") == "Y":
            continue
        sym = (row.get("Symbol") if kind == "nasdaq" else row.get("ACT Symbol")) or ""
        exch = "NASDAQ" if kind == "nasdaq" else EXCHANGES.get(row.get("Exchange") or "", row.get("Exchange") or "")
        if sym:
            out[sym.upper()] = {"name": row.get("Security Name"), "exchange": exch}
    return out


def assets_path(root):
    return os.path.join(cache_dir(root), "assets.json")


def refresh_assets(root, now, getter=None, symbols=None):
    """the roster's classification from the Nasdaq Trader symbol directory (refreshed weekly)."""
    doc = read_json(assets_path(root), None) or {}
    if doc.get("asof") and now - float(doc["asof"]) < ASSETS_MAX_AGE_S and doc.get("rows"):
        return doc
    listing = {}
    for kind, url in SYMDIR.items():
        if getter is not None:
            text = getter(url)
        else:
            from ..data.http import get
            text = get(url, as_text=True)
        listing.update(parse_symdir(text, kind))
    rows = {}
    for s in symbols or roster():
        item = listing.get(s) or listing.get(s.replace("-", ".")) or listing.get(s.replace(".", "-"))
        rows[s] = {"state": "READY" if item else "UNAVAILABLE",
                   "classification": classify(item["name"], item["exchange"]) if item else "UNAVAILABLE",
                   "name": item["name"] if item else None, "exchange": item["exchange"] if item else None}
    doc = {"asof": now, "source": "nasdaqtrader symbol directory", "rows": rows}
    write_json_atomic(assets_path(root), doc)
    return doc


def load_assets(root):
    return (read_json(assets_path(root), None) or {}).get("rows") or {}


# -- jobs -----------------------------------------------------------------------------------------------------------
def _publish(root, interval, now, session, built, errors, info):
    doc = {"asof": now, "session": session, "interval": interval, "events": built["events"],
           "context": built.get("context") or {}, "errors": errors, "info": info}
    write_json_atomic(events_path(root, interval), doc)
    return doc


MIN_COVERAGE = 0.5          # a run publishes only when at least half the roster's frames reached the target bar
PREFETCH_BUDGET_S = 900     # one hourly run's time for cold Alpaca years (~20 requests a name); the rest resumes next run
WARM_BUDGET_S = 3000        # one canonical_warm run's time for the cold years, off the session


class IncompleteRun(RuntimeError):
    """the provider has not yet served the target bar for most of the roster: the job fails and is retried."""


def job_1d(engine, now=None, symbols=None, getter=None, weekly=None, asset_getter=None):
    """after each close: the roster's 1d frames, and on a week's last session the 1wk frames. Idempotent per session
    (a published session is not recomputed); a run that finds the target bar missing for most names raises."""
    from ..sleeves.families import tensor_research as F
    now = now or engine.clock()
    day = cal._as_date(now)
    if not cal.is_trading_day(day) or now < cal.session_close(day) + 15 * 60:
        day = cal.prev_trading_day(day)
    syms = list(symbols or roster())
    if "SPY" in syms:
        syms = ["SPY"] + [s for s in syms if s != "SPY"]
    info = {"session": day.isoformat(), "symbols": len(syms)}
    try:
        refresh_assets(engine.root, now, asset_getter, syms)
    except Exception as e:                              # the classification is weekly; a stale copy stays usable
        info["assets_error"] = f"{type(e).__name__}: {str(e)[:120]}"
    intervals = ["1d"]
    if weekly if weekly is not None else cal.week_last_session(day) == day:
        intervals.append("1wk")
    alpaca = getattr(getattr(engine, "hub", None), "alpaca", None)
    client = alpaca.c if (alpaca is not None and getter is None) else None
    for interval in intervals:
        done = load_events(engine.root, interval) or {}
        if done.get("session") == day.isoformat():
            info[interval] = {"skipped": "already published"}
            continue
        t0 = time.time()
        errors = {}
        ctx = {}
        if interval == "1d":                            # the relay's weekly permission: the last completed weeks
            ctx = {"episodes": ((load_events(engine.root, "1wk") or {}).get("context") or {}).get("episodes") or {}}
        else:                                           # the weekly Deep Reset groups read this session's daily flags
            d1 = load_events(engine.root, "1d") or {}
            if d1.get("session") == day.isoformat():
                ctx = {"ext": (d1.get("context") or {}).get("ext") or {}}
        built = F.Collector(interval, now, context=ctx, root=engine.root, day=day)
        parse_now = now
        if interval == "1wk":                           # a holiday-shortened week is complete at its last session
            friday = day + timedelta(days=4 - day.weekday())
            parse_now = max(now, datetime(friday.year, friday.month, friday.day, 16, 30, tzinfo=ET).timestamp())
        views_ = F.views(interval)
        sources = {}
        jobs = ({"symbol": s, "interval": interval, key: data, "now": parse_now, "views": views_}
                for s, key, data in history_stream(syms, interval, day, now, errors, getter, client, sources))
        frames(jobs, built.add)
        built.finish()
        errors.update(built.errors)
        if syms and built.n_fresh < MIN_COVERAGE * len(syms):
            raise IncompleteRun(f"{interval}: only {built.n_fresh} of {len(syms)} frames reached {day} "
                                f"({len(errors)} errors, sources {sources})")
        _publish(engine.root, interval, now, day.isoformat(), built.result(), errors,
                 {"frames": built.n_frames, "fresh": built.n_fresh, "events": built.n_events, "sources": sources,
                  "seconds": round(time.time() - t0, 1)})
        info[interval] = {"frames": built.n_frames, "fresh": built.n_fresh, "events": built.n_events,
                          "errors": len(errors), "sources": sources}
    return info


def warm_canonical(engine, now=None, running=(), symbols=None):
    """off the session: the roster's cold canonical years (about 20 Alpaca requests a name) that the hourly runs'
    900 s budget deferred (355 of 1,838 names on 2026-10-16), loaded so the next session's first hourly run covers
    the roster. Resumes where it stopped (the index is written per batch); never beside the hourly job, which writes
    the same index."""
    from .canonical_alpaca import AlpacaCanonical
    alpaca = getattr(getattr(engine, "hub", None), "alpaca", None)
    if alpaca is None:
        return {"skipped": "no Alpaca keys"}
    if "tensor_research_1h" in running:
        return {"skipped": "the hourly job is running"}
    now = now or engine.clock()
    can = AlpacaCanonical(os.path.dirname(engine.hub.cache.root), alpaca.c)
    syms = list(symbols or roster())
    idx = can.index()
    cold = [s for s in syms if s.upper() not in idx]
    if not cold:
        return {"skipped": "warm", "symbols": len(syms)}
    t0 = time.time()
    batches = can.prefetch(syms, now, budget_s=WARM_BUDGET_S)
    return {"cold": len(cold), "batches": batches, "deferred": can.deferred, "seconds": round(time.time() - t0, 1)}


def job_1h(engine, now=None, symbols=None, getter=None):
    """each completed RTH hour: the roster's canonical 1h frames (idempotent per completed bar)."""
    from ..sleeves.families import tensor_research as F
    from .canonical import Canonical, latest_completed_open
    now = now or engine.clock()
    root = os.path.dirname(engine.hub.cache.root) if getattr(engine, "hub", None) is not None else engine.root
    syms = list(symbols or roster())
    alpaca = getattr(getattr(engine, "hub", None), "alpaca", None)
    if alpaca is not None and getter is None:
        # with Alpaca keys: the roster's hours from batched SIP half hours (desk/feedlib/canonical_alpaca.py), about
        # ten requests an hour instead of one Yahoo request per name
        from .canonical_alpaca import AlpacaCanonical, latest_available_open
        can = AlpacaCanonical(root, alpaca.c)
        can.prefetch(syms, now, budget_s=PREFETCH_BUDGET_S)
        newest = latest_available_open(now)
    else:
        can = Canonical(root, getter=getter or canonical_getter)
        newest = latest_completed_open(now)
    done = load_events(engine.root, "1h") or {}
    if newest is not None and (done.get("info") or {}).get("newest_open") == newest:
        return {"skipped": "already published", "newest_open": newest, "deferred": getattr(can, "deferred", 0)}
    t0 = time.time()
    errors = {}

    def load(s):
        bl = can.bars(s, now)
        if not bl:
            raise ResearchEngineError(can.status.get(s) or "no bars")
        if newest is not None and int(bl[-1]["t"]) < newest:
            raise ResearchEngineError("stale: newest canonical bar %s" % int(bl[-1]["t"]))
        return bl

    daily = load_events(engine.root, "1d") or {}
    built = F.Collector("1h", now, context=daily.get("context") or {}, root=engine.root)
    jobs = ({"symbol": s, "interval": "1h", "bars": bl, "views": F.views("1h", s)}
            for s, bl in fetch_stream(syms, load, errors))
    frames(jobs, built.add)
    built.finish()
    errors.update(built.errors)
    if syms and built.n_fresh < MIN_COVERAGE * len(syms):
        raise IncompleteRun(f"1h: only {built.n_fresh} of {len(syms)} frames reached the bar opened {newest}")
    doc = _publish(engine.root, "1h", now, cal._as_date(now).isoformat(), built.result(), errors,
                   {"frames": built.n_frames, "events": built.n_events, "newest_open": newest,
                    "seconds": round(time.time() - t0, 1)})
    return {"frames": built.n_frames, "events": built.n_events, "errors": len(doc["errors"]),
            "deferred": getattr(can, "deferred", 0)}
