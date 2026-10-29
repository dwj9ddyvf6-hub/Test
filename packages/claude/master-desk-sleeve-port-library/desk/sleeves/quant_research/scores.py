"""The quant_research score producer (desk job `qr_scores`, after each close): the six-strategy reconstruction's daily
model scores for the latest completed session, written to cache/qr_scores.json for the TopkDropout sleeves.

  alphamemo    residual frozen pool (15 sspm formulas) + the 4 baseline features, per-date z-score, LightGBM model
  quantaalpha  rounds5 frozen pool (QuantaAlpha native parser / function library), per-date CSRankNorm, LightGBM

Both on the frozen 640-name panel roster: split-adjusted daily bars through the session (hub `equity_split`),
build_panel's causal eligibility, train_predict's masking. The document also carries each column's eligibility and
the 20-session mean dollar volume the book's participation cap uses.

Named divergence (window_start_float): the factor values are evaluated over the job's trailing 320-session window, the
native over the panel's whole 2016- history. pandas' online rolling sums / variances carry ~1e-13 accumulation
differences from where a series starts; on rare names that flips a LightGBM split or a cross-sectional rank tie (2 of
504 sampled QuantaAlpha scores; recomputed over the whole history they match to 4e-12). Counted in the parity
receipt (tools/parity/qr_factor_books.py)."""
import json
import os
import time

import numpy as np

from ... import calendar as cal
from . import common as C
from . import lgbm_text as L
from . import sixai as S

CACHE = "qr_scores.json"
MODELS = {}


def model(name):
    if name not in MODELS:
        if name == "alphamemo":
            pool = [f["formula"] for f in json.load(open(os.path.join(S.VENDOR, "alphamemo",
                                                                       "residual-frozen-pool.json")))["factors"]]
            m = L.Model.load(os.path.join(S.VENDOR, "alphamemo", "residual-model.txt"))
        else:
            pool = [f["expression"] for f in json.load(open(os.path.join(S.VENDOR, "quantaalpha",
                                                                         "rounds5-frozen-pool.json")))["pool"]]
            m = L.Model.load(os.path.join(S.VENDOR, "quantaalpha", "rounds5-model.txt"))
        MODELS[name] = (pool, m)
    return MODELS[name]


def compute(P, name):
    """the model score of the panel's last row: {symbol: score} over the eligible names."""
    pool, m = model(name)
    if name == "alphamemo":
        ops, _ = S.sspm()
        feats = S.base_features(P) + [ops.evaluate_formula(f, S.features(P)) for f in pool]
        mode = "zscore"
    else:
        feats = S.quantaalpha_values(P, pool)
        mode = "rank"
    n = P["close"].shape[0]
    pred = S.predict_rows(m, feats, P["eligible"], [n - 1], mode)[0]
    return {S.SYMBOLS[j]: float(pred[j]) for j in range(len(S.SYMBOLS)) if np.isfinite(pred[j])}


def last_completed(now):
    d = cal._as_date(now).isoformat()
    if C.is_session(d) and now >= cal.session_close(d) + 15 * 60:
        return d
    return C.prev_session(d)


def run(hub, root, now, names=("alphamemo", "quantaalpha")):
    d = last_completed(now)
    old = read(root)
    if old and old.get("asof") == d and all(n in old for n in names):
        return {"due": False, "asof": d}
    frames = C.daily(hub, "equity_split", S.SYMBOLS, S.N_ROWS + 60)
    have = [s for s, f in frames.items() if f.index.max().date().isoformat() >= d]
    if len(have) < 50:
        raise RuntimeError(f"bars through {d} for only {len(have)} names")
    P = S.panel_and_eligibility(frames, d)
    doc = {"asof": d, "computed_at": time.time(), "served": len(frames),
           "eligible": [S.SYMBOLS[j] for j in np.flatnonzero(P["eligible"][-1])],
           "adv20": {S.SYMBOLS[j]: float(v) for j, v in enumerate(S.adv20(P)) if np.isfinite(v)}}
    for name in names:
        t0 = time.time()
        doc[name] = compute(P, name)
        doc[name + "_seconds"] = round(time.time() - t0, 1)
    path = os.path.join(root, "cache", CACHE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(doc, f)
    os.replace(path + ".tmp", path)
    return {"asof": d, "served": len(frames), "eligible": len(doc["eligible"]),
            **{n: len(doc[n]) for n in names}}


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


def feed_scores(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    return read(root) if root else None
