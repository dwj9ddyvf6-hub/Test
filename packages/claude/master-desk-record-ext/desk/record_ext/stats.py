"""Per-date Spearman IC and the plain t over dates, numpy / pandas only (the scorer's definitions, kept free of the
forecast package so this lane stands alone)."""
import math

import numpy as np

MIN_NAMES = 20


def panel(x, y, dates, names):
    """long arrays -> (dates, names, X, Y) matrices (dates ascending); a cell with a non-finite x or y is NaN in both"""
    import pandas as pd
    df = pd.DataFrame({"d": np.asarray(dates), "n": np.asarray(names), "x": np.asarray(x, float),
                       "y": np.asarray(y, float)})
    df = df.drop_duplicates(["d", "n"], keep="last")
    X = df.pivot(index="d", columns="n", values="x").sort_index()
    Y = df.pivot(index="d", columns="n", values="y").reindex(index=X.index, columns=X.columns)
    bad = ~(np.isfinite(X.to_numpy()) & np.isfinite(Y.to_numpy()))
    Xa, Ya = X.to_numpy().copy(), Y.to_numpy().copy()
    Xa[bad] = np.nan
    Ya[bad] = np.nan
    return X.index.to_numpy(), X.columns.to_numpy(), Xa, Ya


def _row_rank(A):
    import pandas as pd
    return pd.DataFrame(A).rank(axis=1).to_numpy()


def ic_rows(X, Y, min_names=MIN_NAMES):
    """per-row Spearman IC of two matrices (NaN where a row has fewer than min_names pairs)"""
    m = np.isfinite(X) & np.isfinite(Y)
    Xm, Ym = np.where(m, X, np.nan), np.where(m, Y, np.nan)
    rx, ry = _row_rank(Xm), _row_rank(Ym)
    n = m.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mx, my = np.nanmean(rx, axis=1), np.nanmean(ry, axis=1)
        dx, dy = rx - mx[:, None], ry - my[:, None]
        num = np.nansum(dx * dy, axis=1)
        den = np.sqrt(np.nansum(dx * dx, axis=1) * np.nansum(dy * dy, axis=1))
        ic = num / den
    ic[(n < min_names) | ~np.isfinite(ic)] = np.nan
    return ic


def t_plain(s):
    """{n, mean, sd, t} of a series (non-finite dropped); t is None under 3 values or with zero spread"""
    s = np.asarray(s, float)
    s = s[np.isfinite(s)]
    n = len(s)
    out = {"n": n, "mean": float(s.mean()) if n else None, "sd": None, "t": None}
    if n < 3:
        return out
    sd = float(s.std(ddof=1))
    out["sd"] = sd
    if sd > 0:
        out["t"] = float(s.mean() / (sd / math.sqrt(n)))
    return out


def no_data(why, **kw):
    return {"status": "no_data", "reason": why, **kw}
