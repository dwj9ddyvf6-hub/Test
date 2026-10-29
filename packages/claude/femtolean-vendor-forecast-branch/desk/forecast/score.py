"""The scorer (FACTORY.md §4 steps 1-4): per-date statistics, a Newey-West t over dates, discovery and holdout with
the embargo, and BH over a whole run.

  ic_by_date      s_t = the cross-sectional Spearman IC on date t (Pearson on average ranks, the novel.py rule);
                  a date needs min_names names to have an IC
  brier_by_date   s_t = mean(Brier_base - Brier_f) on date t, base = the discovery base rate
  r_by_date       s_t = mean R of the date's trades minus the mean of their random-same-name baselines
  nw_t            t = mean(s) / (sd(s) / sqrt(T_eff)), T_eff = T / (1 + 2 sum_{l=1..L} w_l rho_l), Bartlett weights
                  w_l = 1 - l / (L + 1), L = h - 1 for an h-session label (overlapping windows); T_eff is kept in
                  [1, T] (negative autocorrelation never inflates the evidence). p two-sided on Student's t with
                  T_eff - 1 degrees of freedom (desk/lab/stats.t_sf). L = 0 is the plain t over dates.
  block_t         the p that enters BH: gapped blocks for an h-session label: blocks of 2h - 1 dates, the first h
                  of each kept (the last h - 1 dropped, so under MA(h - 1) overlap the block means are independent);
                  t over the block means, Student's t with blocks - 1 df; h = 1 is the plain t over dates. Measured
                  (tests/test_forecast_score.py, 2026-10-27): with MA(19) per-date series and BH at q = 0.10 over
                  2,000 null cells, P(any false discovery) is 0.10 at T = 250 and 0.03 at T = 1500 with gapped blocks,
                  but 1.0 with the Newey-West t (Bartlett or unweighted) and 0.57 / 0.97 with contiguous 20-blocks:
                  the HAC variance's own noise fattens the extreme tail BH reads. NW t stays on every Score as
                  ic_t_clustered (FACTORY.md §4.3); the BH p is the block p (a deviation from §4.3, on this evidence)
  split           discovery = dates before the split (a date, or the first `frac` of dates); holdout = the rest;
                  the embargo drops discovery dates within EMBARGO_DAYS calendar days of the split (their labels run
                  into the holdout), picker/model.EMBARGO_DAYS
  score           one (forecaster, target, cell, split) -> Score; under MIN_DATES dates or MIN_OBS observations the
                  cell is `untested` (logged, never a null)
  bh_run          BH at q over every tested Score's p of a run at once (picker/model.bh; q values by
                  lab/stats.qvalues); deflation_trials = m on every Score"""
import math
from datetime import date, timedelta

import numpy as np

from ..lab import stats as LS
from ..picker import model as M
from . import Score

EMBARGO_DAYS = M.EMBARGO_DAYS
MIN_DATES = 30
MIN_OBS = 300
MIN_NAMES = 20
Q = M.Q


def _codes(dates):
    u, inv = np.unique(np.asarray(dates), return_inverse=True)
    return u, inv


def ic_by_date(x, y, dates, min_names=MIN_NAMES):
    """(dates, s_t, n_t): per-date Spearman IC of x with y over the rows where both are finite"""
    import pandas as pd
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    df = pd.DataFrame({"d": np.asarray(dates)[m], "x": x[m], "y": y[m]})
    if df.empty:
        return np.array([]), np.array([]), np.array([], int)
    g = df.groupby("d", sort=True)
    df["rx"] = g["x"].rank()
    df["ry"] = g["y"].rank()
    df["n"] = g["x"].transform("size")
    df = df[df["n"] >= min_names]
    if df.empty:
        return np.array([]), np.array([]), np.array([], int)
    g = df.groupby("d", sort=True)
    mx, my = g["rx"].transform("mean"), g["ry"].transform("mean")
    df["cxy"], df["cxx"], df["cyy"] = (df.rx - mx) * (df.ry - my), (df.rx - mx) ** 2, (df.ry - my) ** 2
    s = df.groupby("d", sort=True)[["cxy", "cxx", "cyy", "n"]].agg({"cxy": "sum", "cxx": "sum", "cyy": "sum",
                                                                    "n": "first"})
    with np.errstate(invalid="ignore", divide="ignore"):
        ic = (s.cxy / np.sqrt(s.cxx * s.cyy)).to_numpy()
    ok = np.isfinite(ic)
    return s.index.to_numpy()[ok], ic[ok], s.n.to_numpy()[ok].astype(int)


def brier_by_date(p, y, dates, base):
    """(dates, s_t, n_t): s_t = mean over the date of (base - y)^2 - (p - y)^2"""
    p, y = np.asarray(p, float), np.asarray(y, float)
    m = np.isfinite(p) & np.isfinite(y)
    u, inv = _codes(np.asarray(dates)[m])
    d = (base - y[m]) ** 2 - (p[m] - y[m]) ** 2
    n = np.bincount(inv, minlength=len(u))
    return u, np.bincount(inv, weights=d, minlength=len(u)) / n, n


def r_by_date(r, base, dates):
    """(dates, s_t, n_t): s_t = mean R of the date's cases minus the mean of their baselines (finite pairs only)"""
    r, base = np.asarray(r, float), np.asarray(base, float)
    m = np.isfinite(r) & np.isfinite(base)
    u, inv = _codes(np.asarray(dates)[m])
    n = np.bincount(inv, minlength=len(u))
    return u, (np.bincount(inv, weights=r[m], minlength=len(u)) - np.bincount(inv, weights=base[m],
                                                                              minlength=len(u))) / n, n


def nw_t(s, lags=0):
    """{mean, sd, T, T_eff, t, p} of a per-date series s (date order)"""
    s = np.asarray(s, float)
    s = s[np.isfinite(s)]
    T = len(s)
    out = {"mean": float(s.mean()) if T else None, "sd": None, "T": T, "T_eff": None, "t": None, "p": None}
    if T < 3:
        return out
    sd = float(s.std(ddof=1))
    u = s - s.mean()
    var0 = float((u * u).mean())
    acc = 0.0
    L = max(0, min(int(lags), T - 2))
    if var0 > 0:
        for l in range(1, L + 1):
            rho = float((u[l:] * u[:-l]).mean()) / var0
            acc += (1 - l / (L + 1)) * rho
    T_eff = min(float(T), max(1.0, T / (1 + 2 * acc)))
    out.update(sd=sd, T_eff=T_eff)
    if sd <= 0:
        return out
    t = out["mean"] / (sd / math.sqrt(T_eff))
    df = max(1.0, T_eff - 1)
    out.update(t=t, p=min(1.0, 2 * LS.t_sf(abs(t), df)))
    return out


def nw_t_many(Sm, lags=0):
    """nw_t over the rows of a (cells, T) matrix of complete per-date series at once -> (mean, t, T_eff, p) arrays;
    the same formula as nw_t (tests/test_forecast_score.py holds them equal), p from scipy's Student t"""
    from scipy.stats import t as student
    Sm = np.asarray(Sm, float)
    k, T = Sm.shape
    mu = Sm.mean(axis=1)
    sd = Sm.std(axis=1, ddof=1)
    U = Sm - mu[:, None]
    var0 = (U * U).mean(axis=1)
    acc = np.zeros(k)
    L = max(0, min(int(lags), T - 2))
    for l in range(1, L + 1):
        acc += (1 - l / (L + 1)) * np.where(var0 > 0, (U[:, l:] * U[:, :-l]).mean(axis=1) / np.where(var0 > 0, var0, 1),
                                            0.0)
    T_eff = np.minimum(float(T), np.maximum(1.0, T / (1 + 2 * acc)))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = mu / (sd / np.sqrt(T_eff))
    p = np.minimum(1.0, 2 * student.sf(np.abs(t), np.maximum(1.0, T_eff - 1)))
    return mu, t, T_eff, p


def block_t(s, h=1):
    """{t, p, blocks} of a per-date series (date order) for an h-session label (gapped blocks, above)"""
    s = np.asarray(s, float)
    s = s[np.isfinite(s)]
    B = 2 * max(1, int(h)) - 1
    nb = len(s) // B
    out = {"t": None, "p": None, "blocks": nb}
    if nb < 3:
        return out
    X = s[len(s) - nb * B:].reshape(nb, B)[:, :max(1, int(h))].mean(axis=1)
    sd = float(X.std(ddof=1))
    if sd <= 0:
        return out
    t = float(X.mean() / (sd / math.sqrt(nb)))
    out.update(t=t, p=min(1.0, 2 * LS.t_sf(abs(t), nb - 1.0)))
    return out


def block_t_many(Sm, h=1):
    """block_t over the rows of a (cells, T) matrix -> (t, p) arrays"""
    from scipy.stats import t as student
    Sm = np.asarray(Sm, float)
    k, T = Sm.shape
    B = 2 * max(1, int(h)) - 1
    nb = T // B
    if nb < 3:
        return np.full(k, np.nan), np.ones(k)
    X = Sm[:, T - nb * B:].reshape(k, nb, B)[:, :, :max(1, int(h))].mean(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = X.mean(axis=1) / (X.std(axis=1, ddof=1) / math.sqrt(nb))
    return t, np.minimum(1.0, 2 * student.sf(np.abs(t), nb - 1))


def split_dates(dates, split=None, frac=0.6, embargo_days=EMBARGO_DAYS):
    """(disc mask, hold mask, the split date) over an array of ISO dates (or datetimes)"""
    ds = np.asarray([str(x)[:10] for x in np.asarray(dates)])
    if split is None:
        u = np.unique(ds)
        split = u[min(len(u) - 1, int(math.floor(frac * len(u))))] if len(u) else "9999-12-31"
    cut = (date.fromisoformat(split) - timedelta(days=embargo_days)).isoformat()
    disc = ds < cut
    hold = ds >= split
    return disc, hold, split


def score(forecaster, target, cell, split, s_dates, s, n_t, lags=0, kind="ic", min_dates=MIN_DATES,
          min_obs=MIN_OBS, **extra):
    """a Score from a per-date series (s_dates, s, n_t)"""
    n_obs, n_dates = int(np.sum(n_t)), int(len(s))
    sc = Score(forecaster=forecaster, target=target, cell=cell, split=split, n_obs=n_obs, n_dates=n_dates,
               first_date=str(s_dates[0])[:10] if n_dates else None,
               last_date=str(s_dates[-1])[:10] if n_dates else None, **extra)
    if n_dates < min_dates or n_obs < min_obs:
        sc.status = "untested"
        return sc
    r = nw_t(s, lags)
    b = block_t(s, lags + 1)
    sc.t_eff = None if r["T_eff"] is None else round(r["T_eff"], 2)
    sc.ic_t_clustered = None if r["t"] is None else round(r["t"], 4)
    sc.t_block = None if b["t"] is None else round(b["t"], 4)
    sc.p = b["p"]
    if kind == "ic":
        sc.ic = round(r["mean"], 6)
    else:
        sc.mean_excess_net = round(r["mean"], 6)
    return sc


def brier_skill(p, y, base):
    """1 - Brier(p) / Brier(base) over the finite pairs (base a scalar rate or an array)"""
    p, y = np.asarray(p, float), np.asarray(y, float)
    b = np.broadcast_to(np.asarray(base, float), p.shape)
    m = np.isfinite(p) & np.isfinite(y) & np.isfinite(b)
    bf, bb = np.mean((p[m] - y[m]) ** 2), np.mean((b[m] - y[m]) ** 2)
    return float(1 - bf / bb) if bb > 0 else None


def bh_run(scores, q=Q):
    """BH over every tested Score of a run at once: sets q_bh and deflation_trials; returns the discoveries"""
    tested = [s for s in scores if s.status == "tested" and s.p is not None]
    m = len(tested)
    keep = M.bh([s.p for s in tested], q)
    qs = LS.qvalues({i: s.p for i, s in enumerate(tested)})
    found = []
    for i, (s, k) in enumerate(zip(tested, keep)):
        s.q_bh, s.deflation_trials, s.trials = qs[i], m, m
        if k:
            found.append(s)
    return found
