"""Shared machinery of the six-strategy reconstruction's factor sleeves (AlphaMemo, QuantaAlpha) and its TopkDropout
book (also Kronos): the frozen 640-name panel roster, the reconstruction's feature processing (factor_common.py:
base_features, normalized, train_predict's eligibility mask) and shared/portfolio.py's dropout branch with
shared/dropout.py's selector (vendored byte-exact)."""
import contextlib
import io
import json
import os
import sys
import types

import numpy as np

from . import common as C

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "quant_research")
_U = json.load(open(os.path.join(VENDOR, "sixai", "data", "universe.json")))
SYMBOLS = tuple(e["symbol"] for e in _U)                       # the panel's 640 columns, in order
CANDIDATE = np.array([bool(e["equity_candidate"]) for e in _U])
N_ROWS = 320                                                   # >= 252 + 21 eligibility rows; factor windows <= 130


def sspm():
    from ...vendor.quant_research.alphamemo.sspm.core import math_utils, operators
    return operators, math_utils


def dropout_mod():
    from ...vendor.quant_research.sixai.shared import dropout
    return dropout


def install_joblib_shim():
    """joblib is not installed: QuantaAlpha's function_lib imports Parallel / delayed at module load (used only by its
    rolling beta / residual helpers, outside the frozen pool); a sequential stand-in keeps the module loadable."""
    if "joblib" in sys.modules:
        return
    m = types.ModuleType("joblib")

    class Parallel:
        def __init__(self, n_jobs=None, **kw):
            pass

        def __call__(self, it):
            return [f(*a, **k) for f, a, k in it]

    def delayed(f):
        return lambda *a, **k: (f, a, k)
    m.Parallel, m.delayed = Parallel, delayed
    sys.modules["joblib"] = m


def features(P):
    """load_panel()['features']: open_ close high low volume vwap and ret = close / close[-1] - 1."""
    f = {"open_": P["open"], "close": P["close"], "high": P["high"], "low": P["low"], "volume": P["volume"],
         "vwap": P["vwap"]}
    ret = np.full_like(P["close"], np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        ret[1:] = P["close"][1:] / P["close"][:-1] - 1
    f["ret"] = ret
    return f


def base_features(P):
    """factor_common.base_features: intraday, relative volume 20, range, ret1 (sspm TsMean / Delay)."""
    ops, _ = sspm()
    f = features(P)
    c, o, v = f["close"], f["open_"], f["volume"]
    with np.errstate(invalid="ignore", divide="ignore"):
        return [(c - o) / o, v / ops.TsMean(v, 20), (f["high"] - f["low"]) / ops.Delay(c, 1), c / ops.Delay(c, 1) - 1]


def normalized(x, mode):
    """factor_common.normalized: per-date z-score (population std, floor 1e-12) or Qlib CSRankNorm, NaN / inf -> 0."""
    _, mu = sspm()
    if mode == "rank":
        return np.nan_to_num((mu.rank_rows(x) - .5) * 3.46, nan=0., posinf=0., neginf=0.).astype(np.float32)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mean = np.nanmean(x, axis=1, keepdims=True)
            sd = np.nanstd(x, axis=1, keepdims=True)
            return np.nan_to_num((x - mean) / np.maximum(sd, 1e-12), nan=0., posinf=0., neginf=0.).astype(np.float32)


def predict_rows(model, feats, eligible, rows, mode):
    """train_predict's prediction on panel rows `rows`: each feature masked to the eligible cells, normalised by date,
    the model's raw prediction; ineligible -> NaN."""
    X = np.empty((len(rows), feats[0].shape[1], len(feats)), dtype=np.float32)
    for i, values in enumerate(feats):
        masked = np.where(eligible[rows], values[rows], np.nan)
        X[..., i] = normalized(masked, mode)
    pred = model.predict(X.reshape(-1, X.shape[-1])).reshape(X.shape[:2])
    pred[~eligible[rows]] = np.nan
    return pred


def panel_and_eligibility(frames, upto, n_rows=N_ROWS):
    P = C.panel(frames, SYMBOLS, upto, n_rows)
    P["eligible"] = C.eligibility(P["close"], P["volume"], P["valid"]) & CANDIDATE[None, :]
    return P


def quantaalpha_values(P, expressions):
    """reconstruct.OriginalCompiler over the panel rows: the native parser's compiled expression evaluated with the
    native function library on MultiIndex (datetime, instrument) series of every roster column."""
    import pandas as pd
    install_joblib_shim()
    from ...vendor.quant_research.quantaalpha import expr_parser as parser
    from ...vendor.quant_research.quantaalpha import function_lib as functions
    dates, symbols = P["dates"], list(SYMBOLS)
    index = pd.MultiIndex.from_product([pd.to_datetime(dates), symbols], names=["datetime", "instrument"])
    scope = {name: getattr(functions, name) for name in dir(functions)
             if callable(getattr(functions, name)) and not name.startswith("_")}
    for name in ["open", "close", "high", "low", "volume", "vwap"]:
        scope[name] = pd.Series(P[name].reshape(-1), index=index)
    scope.update({"np": np, "pd": pd})
    out = []
    for expr in expressions:
        with contextlib.redirect_stdout(io.StringIO()):
            compiled = parser.parse_expression(parser.parse_symbol(expr, ["$open", "$close", "$high", "$low",
                                                                          "$volume", "$vwap"]))
        series = eval(compiled, {"__builtins__": {}}, scope)
        out.append(series.reindex(scope["close"].index).to_numpy().reshape(len(dates), len(symbols)))
    return out


# --------------------------------------------------------------------------------------------- the dropout book
def adv20(P):
    """shared/portfolio.backtest's participation base: 20-session mean split close x volume through the prior row."""
    dv = P["close"] * P["volume"]
    out = np.full(dv.shape[1], np.nan)
    tail = dv[-20:]
    ok = np.isfinite(tail).all(axis=0)
    out[ok] = tail[:, ok].mean(axis=0)
    return out


def dropout_plan(symbols, score, eligible_prev, held_qty, held_sessions, bid, ask, cash, adv, topk, n_drop, min_hold,
                 risk_degree, buy_bps, sell_bps, participation=0.01):
    """shared/portfolio.backtest's dropout branch for one session: the native TopkDropout selection, sales capped at
    1% of ADV, the risk-degree buy budget split over the planned buys, the participation cap on every trade and the
    long-only affordability scale. Prices: bid for sales, ask for buys (the backtest used the session's open).
    Returns (desired shares per column, selection)."""
    D = dropout_mod()
    N = len(score)
    executable = np.isfinite(ask) & (ask > 0) & np.isfinite(bid) & (bid > 0)
    held = np.flatnonzero(held_qty > 1e-12).tolist()
    sel = D.select_topk_dropout(score, np.array(symbols), held, eligible_prev & np.isfinite(score),
                                executable, held_sessions, topk, n_drop, min_hold)
    q = held_qty.astype(float)
    desired = q.copy()
    p_sell, p_buy = np.where(executable, bid, np.nan), np.where(executable, ask, np.nan)
    sale = 0.0
    for j in sel["actual_sell"]:
        planned = q[j] * p_sell[j]
        filled = planned if participation is None else min(planned, max(0.0, float(np.nan_to_num(adv[j], nan=0)))
                                                            * participation)
        desired[j] = q[j] - filled / p_sell[j]
        sale += filled
    available = D.dropout_buy_budget(cash, sale, sell_bps, buy_bps, risk_degree)
    if sel["actual_buy"]:
        budget = available / len(sel["planned_buy"])
        for j in sel["actual_buy"]:
            desired[j] = budget / p_buy[j]
    delta = desired - q
    delta[~executable] = 0
    mark = np.where(delta > 0, p_buy, p_sell)
    mark = np.nan_to_num(mark, nan=0)
    if participation is not None:
        limit = np.maximum(0, np.nan_to_num(adv, nan=0)) * participation
        dollars = delta * mark
        scale = np.minimum(1, np.divide(limit, np.abs(dollars), out=np.ones(N), where=np.abs(dollars) > 0))
        delta *= scale
    dollars = delta * mark
    proceeds = float(np.maximum(-dollars, 0).sum())
    buys = float(np.maximum(dollars, 0).sum())
    budget = max(0., cash + proceeds * (1 - sell_bps / 10000))
    needed = buys * (1 + buy_bps / 10000)
    if needed > budget and needed > 0:
        delta[delta > 0] *= budget / needed
    return q + delta, sel

