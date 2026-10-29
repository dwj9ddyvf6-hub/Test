"""qr_kronosbasezeroshotustransfer -- the six-strategy reconstruction's genuine Kronos-base zero-shot US transfer
(kronos/run_financial.py, results/portfolios/kronos-primary): the released Kronos-base checkpoint and tokenizer
(shiyu-coder/Kronos@67b630e6 model code and the reconstruction's FP32 KV-cache predictor, vendored byte-exact under
desk/vendor/quant_research/kronos/; weights pinned by its weights-lock.json) forecast the frozen 24-name universe
(the 24 most liquid eligible equities on 2024-06-28, registration.json) every ten sessions from 2024-07-01: 90-session
contexts, ten sessions ahead, ten sampled paths at temperature 0.6 / top-p 0.9, seeds 100 + session index x 1000 +
batch ordinal; score = mean forecast close over the ten sessions / last close - 1. The scores are traded as
registered: TopkDropout top 4, drop 1, minimum hold 5 sessions, risk degree 0.95 (dropout_book.py), on each forecast
date's following session; holdings drift in between.

The forecasts come from the job `qr_kronos` (after the close of a forecast date), which runs kronos_runner.py with
the interpreter that carries torch (env QR_KRONOS_PYTHON, else this interpreter) and caches cache/qr_kronos.json.

Named divergences:
  1. data: the desk's Alpaca split-adjusted daily bars (the reconstruction's provider and adjustment); amount =
     volume x the bar's vwap as the reconstruction derived it;
  2. execution: as dropout_book.py (market orders from the first pass of the next session, sells first, sized on the
     live quote; the reconstruction filled at the open); budget costs: the registration's 15 / 15 bp;
  3. runtime: torch and the Hugging Face weights are not part of the desk's own interpreter -- the job uses a
     configured interpreter and downloads the locked weights once (verified by sha256);
  4. the ten forecast dates are the desk calendar's next ten sessions (the reconstruction read them from its panel)."""
import json
import os
import subprocess
import sys
import tempfile
from datetime import timedelta

import numpy as np

from ... import calendar as cal
from . import common as C
from . import sixai as S
from .dropout_book import DropoutBook

SID = "qr_kronosbasezeroshotustransfer"
VENDOR = os.path.join(S.VENDOR, "kronos")
REG = json.load(open(os.path.join(VENDOR, "registration.json")))
UNIVERSE = tuple(REG["symbols"])
PANEL_START = "2016-01-04"
GRID_START = "2024-07-01"
RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kronos_runner.py")
CACHE = "qr_kronos.json"
WEIGHTS = os.path.join("cache", "qr_kronos_weights")


def session_index(d):
    """the reconstruction panel's session index (2016-01-04 = 0)."""
    return len(C.sessions_between(PANEL_START, d)) - 1


GRID0 = None


def is_forecast_date(d):
    global GRID0
    if GRID0 is None:
        GRID0 = session_index(GRID_START)
    if d < GRID_START or not C.is_session(d):
        return False
    return (session_index(d) - GRID0) % 10 == 0


def next_sessions(d, n=10):
    out, x = [], cal._as_date(d)
    while len(out) < n:
        x += timedelta(days=1)
        if C.is_session(x):
            out.append(x.isoformat())
    return out


def job_input(frames, d):
    """run_financial's per-date inputs from the desk's bars through session d."""
    P = C.panel(frames, UNIVERSE, d, 300)
    elig = C.eligibility(P["close"], P["volume"], P["valid"])
    js = [j for j in range(len(UNIVERSE)) if elig[-1, j] and P["valid"][-90:, j].all()]
    contexts = {}
    for j in js:
        c = {k: P[k][-90:, j].astype(float) for k in ("open", "high", "low", "close", "volume")}
        c["amount"] = c["volume"] * P["vwap"][-90:, j]
        if not all(np.isfinite(v).all() for v in c.values()):
            continue
        contexts[UNIVERSE[j]] = {k: [float(x) for x in v] for k, v in c.items()}
    syms = [s for s in UNIVERSE if s in contexts]
    adv = S.adv20(P)
    return {"t": session_index(d), "decision_date": d, "symbols": syms, "contexts": contexts,
            "x_dates": [str(x) for x in P["dates"][-90:]], "y_dates": next_sessions(d), "batch": 4, "threads": 2}, \
        {"eligible": [UNIVERSE[j] for j in np.flatnonzero(elig[-1])],
         "adv20": {UNIVERSE[j]: float(v) for j, v in enumerate(adv) if np.isfinite(v)}}


def python_for(engine=None):
    return os.environ.get("QR_KRONOS_PYTHON") or sys.executable


def run(hub, root, now, python=None, timeout=4 * 3600):
    from .scores import last_completed
    d = last_completed(now)
    if not is_forecast_date(d):
        return {"due": False, "last_completed": d}
    path = os.path.join(root, "cache", CACHE)
    try:
        if json.load(open(path)).get("asof") == d:
            return {"due": False, "asof": d}
    except (OSError, ValueError):
        pass
    frames = C.daily(hub, "equity_split", UNIVERSE, 360)
    job, extra = job_input(frames, d)
    tmp = tempfile.mkdtemp(prefix="qr_kronos_")
    inp, out = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
    json.dump(job, open(inp, "w"))
    p = subprocess.run([python or python_for(), RUNNER, inp, out, os.path.join(root, WEIGHTS)], capture_output=True,
                       text=True, timeout=timeout)
    if p.returncode or not os.path.exists(out):
        raise RuntimeError(f"kronos runner failed: {p.stderr[-600:]}")
    res = json.load(open(out))
    doc = {"asof": d, "kronos": res["scores"], "forecast_mean_close": res["forecast_mean_close"],
           "seeds": res["seeds"], **extra}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(doc, f)
    os.replace(path + ".tmp", path)
    return {"due": True, "asof": d, "scores": len(res["scores"])}


_CACHE = {}


def read(root):
    p = os.path.join(root, "cache", CACHE)
    try:
        key = (p, os.stat(p).st_mtime_ns)
    except OSError:
        return None
    if _CACHE.get("key") != key:
        try:
            _CACHE.update(key=key, doc=json.load(open(p)))
        except (OSError, ValueError):
            return None
    return _CACHE["doc"]


def feed_kronos(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    return read(root) if root else None


class KronosBook(DropoutBook):
    SID = SID
    NAME = "kronos"
    FEED = "qr_kronos"
    STUDY = "kronos-primary: Kronos-base 10-session forecasts, TopkDropout 4 / 1, min hold 5"
    TOPK, NDROP, MIN_HOLD, RISK = 4, 1, 5, 0.95
    BUY_BPS, SELL_BPS = 15.0, 15.0
    SYMBOLS = UNIVERSE
    SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT, "path": C.SIXAI + "kronos/run_financial.py",
              "upstream": "shiyu-coder/Kronos@67b630e67f6a18c9e9be918d9b4337c960db1e9a; NeoQuasar/Kronos-base@2b554741",
              "registration": "results/portfolios/kronos-primary/registration.json"}

    def doc(self, root):
        return read(root)

    def is_signal_date(self, d):
        return is_forecast_date(d)


def sleeves():
    return [KronosBook()]
