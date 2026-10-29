"""Midna's hourly watch (scripts/tensor-watch.mjs @ cursor/lector-desk-f184 fd0e0a07, blob c3777a91 — identical on the
paper-desk and entire refs), ported line for line; the replica engine runs in desk/feedlib/midna_watch_runner.mjs.

  fetch     Yahoo chart: 60m range 730d (a 422 retries with period1 = now - 729 days), 1d range 2y (QQQ, TZA), 1wk
            range 10y, includePrePost=false, events=div,splits; four attempts
  hourly    the swing basket's closed regular-session 1H bars (more than 400 needed); a fire is a consensus-buy bar
            with a monitor-buy bar at most 3 bars earlier (the setup), the first consensus of each setup; gap20 = more
            than 20 bars since the previous fire; bars before index 200 never fire; a gap20 fire of the last three
            hours not seen before goes to the inbox (key SYM:1h:swing:<setup ts>:confirmed, unit 1h-basket,
            maxBars 60) and is remembered
  qqq       QQQ / TZA closed daily replica bars: flip = slowState turns bearish; flip5 = a flip on one of the last
            five bars; slowBear; the TZA bar of QQQ's last session (open, close)
  moonshot  each basket name's closed weekly bars: a weekly buy-cyan bar (index >= 59) closing <= 14.94 with
            depth60 = (1 - low60 / high60) x 100 >= 70.35; only the latest, and only while it is <= 10 days old
  output    {generatedAt, qqq, moonshots, inbox (new fires), errors}; the seen map persists

Named divergences: the watch ran from the desk supervisor at 10:31, 11:01, ... the close + 1 minute (a 10-minute run
cap); here it is the family job `midna_watch` (desk/sleeves/families/midna_tensor.py JOBS) every 30 minutes over the
same window, writing cache/midna/watch.json (the inbox files, shadow-feed.json and watch-seen.json hand-offs);
inRegularSession reads the desk calendar (market-calendar.mjs carried the 2026 table only)."""
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

from urllib.parse import quote

from ..data.http import HttpError, get
from ..sleeves.midna import common as M
from ..util import ET, read_json, write_json_atomic
from .midna_panel import swing_universe

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "midna_watch_runner.mjs")
CHEAP_MAX = 14.94
DEPTH60_MIN = 70.35


def in_regular_session(epoch):
    t = datetime.fromtimestamp(float(epoch), tz=ET)
    ymd = t.date().isoformat()
    if not M.is_trading_day(ymd):
        return False
    m = t.hour * 60 + t.minute
    return 9 * 60 + 30 <= m < M.session_close_minutes(ymd)


def swing_age(flags, index):
    for cursor in range(index, max(0, index - 3) - 1, -1):
        if flags[cursor][1]:
            return index - cursor
    return None


def hourly_fires(sym, rows):
    """rows: closed 1H bars [ts, close, consensusBuy, monitorBuy]."""
    rows = [r for r in rows if in_regular_session(r[0])]
    if len(rows) <= 400:
        return []
    flags = [(bool(r[2]), bool(r[3])) for r in rows]
    fires, seen_setup, last = [], set(), -1_000_000
    for i in range(len(rows)):
        age = swing_age(flags, i)
        if not flags[i][0] or age is None:
            continue
        setup_ts = int(rows[i - age][0])
        if setup_ts in seen_setup:
            continue
        seen_setup.add(setup_ts)
        gap20 = i - last > 20
        last = i
        if i < 200:
            continue
        fires.append({"sym": sym, "setupTs": setup_ts, "fireTs": int(rows[i][0]), "close": float(rows[i][1]),
                      "gap20": gap20})
    return fires


def depth60(bars, index):
    frm = max(0, index - 59)
    hi, lo = float("-inf"), float("inf")
    for i in range(frm, index + 1):
        hi = max(hi, float(bars[i][2]))
        lo = min(lo, float(bars[i][3]))
    if not (hi > 0) or hi == float("inf") or index - frm < 59:
        return None
    return (1 - lo / hi) * 100


def iso_ms(ts):
    """new Date(ts * 1000).toISOString()"""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def weekly_moonshots(sym, bars, now):
    """bars: closed 1wk bars [ts, close, high, low, buyCyan]."""
    out, ts = [], []
    for i in range(59, len(bars)):
        if not bars[i][4]:
            continue
        close = float(bars[i][1])
        depth = depth60(bars, i)
        if close > CHEAP_MAX or depth is None or depth < DEPTH60_MIN:
            continue
        out.append({"key": f"{sym}:1w:cyan:{int(bars[i][0])}:moonshot", "sym": sym, "fireBar": iso_ms(bars[i][0]),
                    "close": close, "depth60": depth})
        ts.append(int(bars[i][0]))
    if not out:
        return []
    if now - ts[-1] > 10 * 86400:                      # Date.now()/1000 - Date.parse(fireBar)/1000
        return []
    return [out[-1]]


def qqq_flip(qqq, tza):
    """qqq / tza: closed 1d bars [ts, open, close, bearish]."""
    prev, flips = False, []
    for b in qqq:
        bear = bool(b[3])
        flips.append(bear and not prev)
        prev = bear
    if not qqq:
        return None
    last = qqq[-1]
    session = datetime.fromtimestamp(int(last[0]), tz=ET).date().isoformat()
    t = next((b for b in reversed(tza) if datetime.fromtimestamp(int(b[0]), tz=ET).date().isoformat() == session), None)
    if t is None:
        return None
    return {"session": session, "slowBear": bool(last[3]), "flip5": any(flips[-5:]), "tzaOpen": float(t[1]),
            "tzaClose": float(t[2])}


class YahooStatus(Exception):
    """a chart response that is not ok (the source's !response.ok): retried; any other failure propagates at once."""

    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.status = status


def desk_get(url, params):
    """one attempt through the desk's HTTP client (its pacing): a non-2xx status raises YahooStatus, a transport
    failure raises as is (the source's fetch rejection)."""
    try:
        r = get(url, params, tries=1)
    except HttpError as e:
        if e.status:
            raise YahooStatus(e.status) from e
        raise
    if r is None:
        raise YahooStatus(404)
    return r


def yahoo(sym, interval, rng, now, getter=None):
    """the watch's yahoo(): four attempts on a status that is not ok (sleeping 0.4 s x attempt between); a 60m range
    rejected with 422 is asked again at once as period1 = now - 729 days / period2 = now; the last status is raised."""
    getter = getter or desk_get
    ys = sym.replace(".", "-")
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(ys, safe="-_.!~*'()")
    params = {"interval": interval, "range": rng, "includePrePost": "false", "events": "div,splits"}
    last = "no response"
    for attempt in range(4):
        try:
            return getter(url, params)
        except YahooStatus as e:
            last = f"HTTP {e.status}"
            if e.status == 422 and interval == "60m":
                end = int(now)
                params = {"interval": "60m", "period1": end - 729 * 86400, "period2": end, "includePrePost": "false",
                          "events": "div,splits"}
                continue
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(last)


def run_engine(jobs, timeout=900):
    """the replica over a batch of jobs -> {key: rows | {"error"}}; a runner failure marks every job of the batch."""
    if not jobs:
        return {}
    try:
        p = subprocess.run(["node", "--max-old-space-size=1024", RUNNER], input=json.dumps({"jobs": jobs}),
                           capture_output=True, text=True, timeout=timeout,
                           env=dict(os.environ, UV_THREADPOOL_SIZE="1", MALLOC_ARENA_MAX="2"))
        if p.returncode != 0:
            raise RuntimeError("watch runner failed: " + p.stderr[-300:])
        return json.loads(p.stdout)["out"]
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as e:
        return {j["key"]: {"error": str(e)} for j in jobs}


def _pass(symbols, interval, yinterval, rng, now, getter, batch):
    """(sym, rows, error) in symbol order: the fetch, then the replica (batched through one runner per batch)."""
    for i in range(0, len(symbols), batch):
        got = []
        for sym in symbols[i:i + batch]:
            try:
                got.append((sym, yahoo(sym, yinterval, rng, now, getter), None))
            except Exception as e:                 # noqa: BLE001 — the source's per-symbol catch
                got.append((sym, None, str(e)))
        out = run_engine([{"key": sym, "interval": interval, "payload": payload, "now": now}
                          for sym, payload, err in got if err is None])
        for sym, payload, err in got:
            if err is not None:
                yield sym, None, err
                continue
            rows = out.get(sym)
            if isinstance(rows, dict):
                yield sym, None, str(rows.get("error"))
                continue
            yield sym, rows or [], None


def watch(now, seen, symbols=None, getter=None, batch=12):
    """one watch run -> ({generatedAt, qqq, moonshots, inbox, errors, stamp}, seen)."""
    symbols = list(symbols or swing_universe())
    errors, fresh, moons = [], [], []
    recent_cut = now - 3 * 3600
    hourly_errors = 0
    for sym, rows, err in _pass(symbols, "1h", "60m", "730d", now, getter, batch):
        if err is not None:
            hourly_errors += 1
            errors.append(f"{sym} 1h: {err}")
            continue
        for fire in hourly_fires(sym, rows):
            if not fire["gap20"] or fire["fireTs"] < recent_cut:
                continue
            key = f"{sym}:1h:swing:{fire['setupTs']}:confirmed"
            if seen.get(key):
                continue
            fresh.append({"key": key, "sym": sym, "lane": "1h", "unit": "1h-basket",
                          "fireBar": iso_ms(fire["fireTs"]), "fireClose": fire["close"],
                          "detectedAt": iso_ms(now), "tradeable": True, "gap20": True, "firstOfSetup": True,
                          "barSource": "yahoo:canonical", "tags": ["in:1h-basket"], "maxBars": 60})
            seen[key] = iso_ms(now)
    qqq = None
    try:
        # Promise.all([yahoo("QQQ"), yahoo("TZA")]): both requests are made even when QQQ's fails; the first
        # failure (QQQ's when both fail - the order is deterministic here) is the block's error
        got, fails = {}, []
        for key in ("QQQ", "TZA"):
            try:
                got[key] = yahoo(key, "1d", "2y", now, getter)
            except Exception as e:                 # noqa: BLE001
                fails.append(e)
        if fails:
            raise fails[0]
        jobs = [{"key": "QQQ", "interval": "1d", "payload": got["QQQ"], "now": now},
                {"key": "TZA", "interval": "1d", "payload": got["TZA"], "now": now}]
        out = run_engine(jobs)
        for key in ("QQQ", "TZA"):
            if isinstance(out.get(key), dict):
                raise RuntimeError(out[key].get("error"))
        qqq = qqq_flip(out.get("QQQ") or [], out.get("TZA") or [])
    except Exception as e:                         # noqa: BLE001
        errors.append(f"QQQ: {e}")
    for sym, rows, err in _pass(symbols, "1wk", "1wk", "10y", now, getter, batch):
        if err is not None:
            errors.append(f"{sym} 1w: {err}")
            continue
        for shot in weekly_moonshots(sym, rows, now):
            if not seen.get(shot["key"]):
                moons.append(shot)
    ok = len(symbols) > 0 and hourly_errors < len(symbols)
    return {"generatedAt": iso_ms(now), "qqq": qqq, "moonshots": moons, "inbox": fresh, "errors": errors[:8],
            "stamp": ok}, seen


def path_of(root):
    return os.path.join(root, "cache", "midna", "watch.json")


def cadence(rec, now):
    """the family job's clock (desk/jobs.cadences): the source supervisor ran the watch at 10:31, 11:01, ... the close
    + 1 minute, so a run is due at the first :01 / :31 ET minute after the last run's start. A fixed 30 minutes from
    each start drifted with every late run, until the session's last run fell past the window and its close was
    never read (2026-10-16: 15:08 and 15:47 ET, then nothing)."""
    last = float((rec or {}).get("started") or 0)
    if last <= 0:
        return 0.0
    t = datetime.fromtimestamp(last, tz=ET).replace(second=0, microsecond=0)
    slot = t.replace(minute=1) if t.minute < 1 else t.replace(minute=31) if t.minute < 31 else \
        (t + timedelta(hours=1)).replace(minute=1)
    return max(0.0, slot.timestamp() - last)


def job(engine):
    """the family job: one watch run; the inbox accumulates (fires are consumed by the hourly books by key)."""
    now = engine.clock()
    path = path_of(engine.root)
    doc = read_json(path, {}) or {}
    res, seen = watch(now, dict(doc.get("seen") or {}))
    inbox = {f["key"]: f for f in doc.get("inbox") or []}
    for f in res["inbox"]:
        inbox[f["key"]] = f
    keep = sorted(inbox.values(), key=lambda f: f["fireBar"])[-400:]
    out = dict(res, inbox=keep, new_inbox=[f["key"] for f in res["inbox"]], seen=seen)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, out)
    return {"fires": len(res["inbox"]), "moonshots": len(res["moonshots"]),
            "qqq": None if not res["qqq"] else {"session": res["qqq"]["session"], "flip5": res["qqq"]["flip5"]},
            "errors": len(res["errors"])}


def feed_watch(feeds, sleeve, now, arg=None):
    eng = getattr(sleeve, "engine", None)
    root = eng.root if eng is not None else os.path.dirname(os.path.dirname(feeds.hub.cache.root))
    return read_json(path_of(root), None)
