"""Galath Anna PhD location-overridden printer grid — one monitor over the source script itself
(galath-desk-backup@3e93f984, branch gospel-2026-08-13, scripts/anna-phd-replay.mjs: "replay anna-replica against
her labeled daily buys/sells. Ports math + indicators + printer"), vendored byte-exact under desk/vendor/galath_gospel
and executed under Node by desk/feedlib/node/galath_phd.mjs; never reimplemented.

What runs: the replay's own buildAnnaReplica(bars) — default options, as replayMain calls it: the seven votes, the
UT / EMA / WaveTrend / Stoch triggers, regime, DCB, and the location printer that overrides them (launch pad,
reclaim, extended, failed euphoria, fight; pad-sequence, support-bounce and warn-confirm cyans; held sells) — on the
daily tape of every name Anna's labeled census holds (.data/anna-census/research/scored-events.json, vendored: the
events with a price and a buy / sell side, mapped by the script's yahooSymbol — 115 names). The family job
galath_phd runs it after each close; the monitor records each name's newest print (CYAN / GREEN buy, RED / MAGENTA
sell) with its location class.

Named divergences:
  * the script replayed her labeled days once (a census); here it runs daily over the same names, the job's cache
    feeding the monitor;
  * tapes: the desk's Yahoo daily bars (Nasdaq / Cboe while Yahoo refuses this host) over the script's 2y range, in
    fetchDaily's shape (a missing volume as 0), completed sessions only (fetchDaily kept the forming bar);
  * the script's import-time mkdirSync(<workspace>/.data/yahoo-daily) lands in the desk's cache
    (desk/feedlib/node/workspace_fs_sync.mjs serves node:fs to that script only).
Removed gates: none (a replay: nothing is traded)."""
import json
import os
from datetime import datetime

from ... import calendar as cal
from ...feedlib import node_source as NS
from ...util import ET, read_json
from . import reads as R
from .base import MonitorSpec, Obs

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "galath_gospel")
EVENTS = os.path.join(VENDOR, "data", "anna-census", "research", "scored-events.json")
PREFIX = "galath_gospel/"
ALIAS = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SPX": "^GSPC", "VIX": "^VIX"}
NEEDS = [{"source": "yahoo", "interval": "1d", "n": 760}]
CACHE = "galath_phd"
MAX_AGE = 30 * 3600


def two_year_start(now):
    """the Galath desk's 2y range start (now minus two years; Feb 29 -> Feb 28)."""
    d = datetime.fromtimestamp(now, tz=ET)
    try:
        start = d.replace(year=d.year - 2)
    except ValueError:                                  # Feb 29
        start = d.replace(year=d.year - 2, day=28)
    return start.timestamp()


def yahoo_symbol(t):
    """anna-phd-replay.mjs yahooSymbol."""
    if t in ALIAS:
        return ALIAS[t]
    if not t or len(t) > 5:
        return None
    return t


def census_names():
    """replayMain's names: events with a price, a buy / sell side and a ticker, in first-seen order."""
    doc = json.load(open(EVENTS))
    out = []
    for e in doc.get("events") or []:
        if e.get("px") is None or e.get("primary") not in ("buy", "sell") or not e.get("tickerUsed"):
            continue
        s = yahoo_symbol(e["tickerUsed"])
        if s and s not in out:
            out.append(s)
    return tuple(out)


UNIVERSE = census_names()


def fetch_daily_shape(rows, now):
    """fetchDaily's bars: {t ms, o, h, l, c, v (null -> 0), session "regular"} over the 2y range."""
    t0 = two_year_start(now)
    out = []
    for b in rows or []:
        if any(b.get(k) is None for k in ("o", "h", "l", "c")) or float(b["t"]) < t0:
            continue
        out.append({"t": int(round(float(b["t"]) * 1000)), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                    "v": b.get("v") or 0, "session": "regular"})
    return out


def workspace(root):
    return os.path.join(root, "cache", "monitor", "galath_workspace")


def replay(root, daily, now, symbols=None, chunk=40):
    NS.verify(PREFIX, 2)
    reqs = [{"symbol": s, "bars": fetch_daily_shape(daily.get(s), now)} for s in symbols or UNIVERSE if daily.get(s)]
    out = {}
    for i in range(0, len(reqs), chunk):
        res = NS.run("galath_phd.mjs", {"workspace": workspace(root), "requests": reqs[i:i + chunk], "look": 260})
        for r in res["results"]:
            if r.get("ok") and r.get("n"):
                out[r["symbol"]] = r
    return out


def run_job(engine):
    """after each close (retried every 30 minutes until written): the replay over the census names."""
    now = engine.clock()
    prev = read_json(R.path(engine.root, CACHE), None) or {}
    d = cal._as_date(now)
    if prev.get("at") and cal.is_trading_day(d) and float(prev["at"]) >= cal.session_close(d):
        return {"skipped": "replayed this session", "at": prev["at"]}
    bars = R.hub_bars(engine, NEEDS, UNIVERSE).get("1d") or {}
    res = replay(engine.root, bars, now)
    R.write(engine.root, CACHE, now, res)
    return {"names": len(UNIVERSE), "replayed": len(res), "prints": sum(1 for r in res.values() if r.get("print"))}


def evaluate(view, mon):
    reads = R.read(getattr(mon.engine, "root", None), CACHE, view.now, MAX_AGE)
    out = {}
    for sym in mon.CONFIG.universe:
        r = reads.get(sym)
        if r is None:
            continue
        p = r.get("print")
        if not p:
            out[sym] = None
            continue
        out[sym] = Obs("%s:%s" % (p["marker"], p.get("location")),
                       "PhD replica %s at %s (%s, %s regime)" % (p["marker"], p.get("c"), p.get("location"),
                                                                p.get("regime")),
                       p["t"] / 1000.0, {"print": p, "last": r.get("last"), "bars": r.get("n")}, p.get("c"))
    return out


SPECS = [MonitorSpec(
    sleeve_id="mon_galath_annaphdlocationoverriddenprintergrid", title="Anna PhD location-overridden printer grid",
    source={"repo": "galath-desk-backup", "ref": "gospel-2026-08-13", "commit": "3e93f984e08268f1ff1bb1fa85798cb8f3827b34",
            "path": "scripts/anna-phd-replay.mjs", "blob_sha": "3816c9d59591ced9ec2d9a900cc66fe7694f27b8",
            "line_start": 1, "line_end": 1078},
    evaluate=evaluate, universe=UNIVERSE, needs={}, schedule="after_close+30:after_close+420", cadence_s=900,
    mode="event", params={"census": "scored-events.json", "names": len(UNIVERSE), "executed": "galath_gospel"})]

JOBS = {"mon_galath_phd": ("after_close+20:after_close+360", 1800, run_job)}
