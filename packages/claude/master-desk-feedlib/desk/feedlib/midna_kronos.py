"""The Kronos forecast producer of midna_kronos_topk: the desk's kickKronos (src/lib/equity/desk.ts @ paper-desk
68315288) as the family job `midna_kronos`, running desk/feedlib/midna_kronos_runner.py (the kronos-forecast.py port)
in its own process with the interpreter that carries torch (cfg midna_kronos_python, else env MIDNA_KRONOS_PYTHON,
else this interpreter).

  due       kronosForecastDue: no ready forecast, a forecast from before the book was born, or one a full ten-session
            horizon old (tradingDaysAfter(signalDay, last completed session) >= 10); an error forecast is retried
            once it is 30 minutes old; one runner at a time (a pid lock)
  output    cache/midna/kronos-forecast.json ({status, signalDay, model, revision, scores [{sym, score, lastClose,
            forecastClose}], error, note}); the weights cache cache/midna/kronos-weights

Named divergences: the desk spawned the script detached from its pass and read the file at the next passes; here the
job's process runs it (the loop launches jobs beside its passes). The script fetched Yahoo's chart (1d, range 2y) for
each name itself; here the job reads the names' daily bars through the desk's data hub (its yahoo source: the same
chart OHLCV, split-adjusted, under the shared per-host rate budget, with the hub's Nasdaq fallback - the same
split-adjusted OHLCV - while Yahoo refuses) and hands them to the runner as cache/midna/kronos-input.json."""
import json
import os
import subprocess
import sys
import time

from ..sleeves.midna import common as M
from ..util import read_json, write_json_atomic

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "midna_kronos_runner.py")
HORIZON = 10
OUT = os.path.join("cache", "midna", "kronos-forecast.json")
WEIGHTS = os.path.join("cache", "midna", "kronos-weights")
INPUT = os.path.join("cache", "midna", "kronos-input.json")
SLEEVE = "midna_kronos_topk"


def forecast_due(forecast, born_day, as_of):
    """kronos.ts kronosForecastDue."""
    if not forecast or forecast.get("status") != "ready" or not forecast.get("signalDay"):
        return True
    if born_day and forecast["signalDay"] < born_day:
        return True
    return M.trading_days_after(forecast["signalDay"], as_of) >= HORIZON


# the model loads only in this job's own subprocess (never in the pass loop), on one thread, and exits with the job
LEAN_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_MAX_THREADS": "1",
            "MALLOC_ARENA_MAX": "2", "TOKENIZERS_PARALLELISM": "false"}


def bar_rows(bars, last_day):
    """the runner's rows from the hub's daily bars, with kronos-forecast.py parseBars's filter: a row needs open / high /
    low / close / volume, close > 0 and volume >= 0, and its session is at most the last completed one."""
    rows = []
    for b in bars or []:
        vals = [b.get(k) for k in ("o", "h", "l", "c", "v")]
        if any(v is None for v in vals) or float(b["c"]) <= 0 or float(b["v"]) < 0:
            continue
        day = M.et_ymd(b["t"])
        if last_day is not None and day > last_day:
            continue
        rows.append({"day": day, "open": float(b["o"]), "high": float(b["h"]), "low": float(b["l"]),
                     "close": float(b["c"]), "volume": float(b["v"])})
    return rows


def served_rows(hub, last_day):
    """the 24 names' daily rows through the desk's data hub (its yahoo source: the script's own chart OHLCV, with the
    hub's Nasdaq fallback while Yahoo refuses; the family's other feeds read yahoo too, keys or not), for the runner; a
    name the hub could not serve is absent and the runner reports it as the script reported a failed fetch."""
    from .midna_kronos_runner import CONTEXT, UNIVERSE
    try:
        got = hub.bars("yahoo", "1d", list(UNIVERSE), n=CONTEXT + 30) or {}
    except Exception:                                   # noqa: BLE001 — the runner reports every name as unserved
        got = {}
    rows = {sym: bar_rows(got.get(sym), last_day) for sym in UNIVERSE}
    return {"asOf": last_day, "source": "yahoo", "rows": {s: r for s, r in rows.items() if r}}


def python_for(engine):
    return (getattr(engine, "cfg", {}) or {}).get("midna_kronos_python") or os.environ.get("MIDNA_KRONOS_PYTHON") \
        or sys.executable


def job(engine, timeout=4 * 3600):
    now = engine.clock()
    out = os.path.join(engine.root, OUT)
    forecast = read_json(out, None)
    born = ((engine.store.sleeve_get(SLEEVE) or {}) if engine.store is not None else {}).get("bornDay")
    as_of = M.last_completed_session(now)
    if not forecast_due(forecast, born, as_of):
        return {"due": False, "signalDay": (forecast or {}).get("signalDay")}
    if (forecast or {}).get("status") == "error" and os.path.exists(out) and time.time() - os.path.getmtime(out) < 1800:
        return {"due": True, "skipped": "error forecast younger than 30 minutes"}
    inp = os.path.join(engine.root, INPUT)
    write_json_atomic(inp, served_rows(engine.hub, as_of))
    p = subprocess.run([python_for(engine), RUNNER, out, os.path.join(engine.root, WEIGHTS), as_of, inp],
                       cwd=engine.root, capture_output=True, text=True, timeout=timeout, env=dict(os.environ, **LEAN_ENV))
    doc = read_json(out, {}) or {}
    return {"due": True, "rc": p.returncode, "status": doc.get("status"), "signalDay": doc.get("signalDay"),
            "scores": len(doc.get("scores") or []), "error": (doc.get("error") or p.stderr[-300:] or None)}


def feed_forecast(feeds, sleeve, now, arg=None):
    eng = getattr(sleeve, "engine", None)
    root = eng.root if eng is not None else os.path.dirname(os.path.dirname(feeds.hub.cache.root))
    doc = read_json(os.path.join(root, OUT), None)
    if not doc or not isinstance(doc.get("scores"), list):
        return None
    return doc


def scores_json(doc):
    return json.dumps(doc, sort_keys=True)
