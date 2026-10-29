"""Author Tensor watch desk — the producer of the Tensor 2 replica book (Author-desk@652db7af src/lib/tensor), executed
under Node from the vendored files (desk/feedlib/Author_tensor.py; never reimplemented).

What runs: once per completed canonical hour, for each name of the watch desk's default list (src/lib/desk-store.ts
DEFAULT_WATCH, vendored and parsed: SATL SKYQ RDW INDI SPY QQQ NVDA MU AAPL AMD TSLA WULF POET),
analyzeSymbol(symbol, "1h") on the canonical 1H series (desk/feedlib/canonical.py, tensor_swing's: the source's own
1h request, Yahoo 60m, range 1y, regular session) and its 1d horizon frame (range 2y), and on the analysis' own
admitted 1h signal tape the Tensor 2 replica (engine.ts buildTensorReplica). Its one row,
mon_Author_tensor2washoutreclaimtransition, trades the replica's persisted signal as a funded paper book (the
owner's ruling D32, 2026-10-26; desk/sleeves/monitor/printer_books.py). The watch desk's other reads (context,
native vector, forecast, causal events, location printer, inferred weights) and its 5m-only rows (the Green / Cyan
engine, its gold overlay, Tensor 0, the GREEN study) were removed from the desk with their rows (the owner,
2026-10-26: "anything that is not an actual trading sleeve/strategy can just be removed altogether. And any tensor
strategy that requires 1m or 5m bars"); the job still runs the source's whole 1h analysis, whose loaders the
replica's tape comes from.

Named divergences:
  * frame: 1h (the owner's decision), where the watch desk's default was 5m;
  * cadence: the source analysed on page view / the desk's sweep (24 names a request); here the family job
    mon_Author_tensor runs the stack once per completed canonical hour, 2-11 minutes after it closes (the 15:30 stub
    at 16:32) — a separate process, one node run for the whole list — and the book reads its cache (reads older
    than 90 minutes are not used);
  * tapes: the canonical 1H series (completed hours only; with no fresh fetch its cached series, else no bars) and
    the hub's Yahoo daily bars (a null volume print arrives as 0; while Yahoo refuses this host the hub's Nasdaq
    fallback), shaped as the chart API result and cut at the source's range start (now - 1 year / 2 years); no
    forming candle is served.
Removed gates: none (no desk-wide gate exists in this stack)."""
import os
import re

from ...feedlib import Author_tensor as GT
from . import reads as R
from .base import MonitorSpec, Obs

STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                     "Author_mon", "src", "lib", "desk-store.ts")
REPO = {"repo": "Author-desk", "ref": "main", "commit": "652db7afcc4312b6bd44d41547ca0f73981fe3ff"}
NEEDS = {"bars": [{"source": "yahoo", "interval": "1d", "n": 760}]}     # the hours: the canonical 1H series
FRAME = "1h"
# the canonical hours complete at :30 (the 15:30 stub at 16:30): one run 2-11 minutes after each
JOB_SCHEDULE, JOB_CADENCE = "ext&et:10:30-16:45&minute:32-41", 1200
SCHEDULE, CADENCE = "ext&et:10:30-17:30", 600                          # the monitors: each run's cache within 10 min


def default_watch():
    src = open(STORE, encoding="utf-8").read()
    body = re.search(r"const DEFAULT_WATCH: WatchItem\[\] = \[(.*?)\]\.map", src, re.S).group(1)
    return tuple(re.findall(r'"([^"]+)"', body))


UNIVERSE = default_watch()
CACHE = "Author_tensor"
MAX_AGE = 90 * 60                        # one hourly run to the next, with slack


def run_job(engine):
    """the job (once per completed canonical hour, a separate process): the stack over the watch list on the
    canonical 1H series and the hub's daily tape, one node run, cached for the Tensor 2 book."""
    from ...feedlib.canonical import Canonical
    now = engine.clock()
    b1 = R.hub_bars(engine, NEEDS["bars"], UNIVERSE).get("1d") or {}
    can = Canonical(os.path.dirname(engine.hub.cache.root))
    hours = {s: can.bars(s, now) for s in UNIVERSE}
    reqs = [{"symbol": s, "charts": GT.charts(s, hours[s], b1.get(s) or [], now, interval=FRAME)} for s in UNIVERSE
            if hours[s]]
    out, errors = {}, {}
    for r in GT.analyze(reqs, now, interval=FRAME):
        if r.get("ok") and r.get("status") not in (None, "UNAVAILABLE"):
            out[r["symbol"]] = r
        elif not r.get("ok"):
            errors[r.get("symbol")] = r.get("error")
    R.write(engine.root, CACHE, now, out, errors=errors, frame=FRAME, canonical=dict(can.status))
    return {"analyzed": len(out), "requested": len(reqs), "errors": len(errors)}


def _sec(ms):
    return ms / 1000.0 if ms is not None else None


def _tensor2(r):
    m = (r.get("tensor2") or {}).get("marker")
    if not m:
        return None
    return Obs(m["marker"], "Tensor 2 %s (%s, %s)" % (m["marker"], m.get("location"), m.get("regime")),
               _sec(m["t"]), {"marker": m}, m.get("c"))


def _evaluate(pick):
    def ev(view, mon):
        res = R.read(getattr(mon.engine, "root", None), CACHE, view.now, MAX_AGE)
        return {sym: pick(r) for sym, r in res.items() if sym in mon.CONFIG.universe}
    return ev


ROWS = (
    ("mon_Author_tensor2washoutreclaimtransition", "Tensor2 washout/reclaim transition", "src/lib/tensor/engine.ts",
     "ce8bda0ea712fd7e336200bc15dc2769e0973ada", 288, _tensor2, "event"),
)

SPECS = [MonitorSpec(sleeve_id=sid, title=title, source=dict(REPO, path=path, blob_sha=sha, line_start=1, line_end=end),
                     evaluate=_evaluate(pick), universe=UNIVERSE, needs={}, schedule=SCHEDULE, cadence_s=CADENCE,
                     mode=mode, params={"frame": FRAME, "watch": "DEFAULT_WATCH", "executed": "Author_mon"})
         for sid, title, path, sha, end, pick, mode in ROWS]
JOBS = {"mon_Author_tensor": (JOB_SCHEDULE, JOB_CADENCE, run_job)}
