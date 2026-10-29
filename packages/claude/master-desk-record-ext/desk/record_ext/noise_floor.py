"""C197 - the permutation (shuffled-ghost) noise floor.

Re-run the candidate against a control in which the signal is shuffled and require the real t to beat what shuffling
produces. The shuffle keeps each name's own signal values and their serial structure at the label horizon: a name's
date-ordered signal is cut into blocks of `h` sessions (h = the target horizon) and the blocks are permuted across that
name's dates. The cross-section on a date then pairs a signal with the wrong date's outcome, while overlapping-label
persistence inside a block survives. For each permutation the per-date Spearman IC and its t over dates are recomputed;
the noise floor is the `q` quantile (0.95) of |t| over the permutations. The real |t| above the floor is a signal
that shuffling does not reproduce; below it, it is not distinguishable from the shuffled ghost.

Under MIN_DATES dates or MIN_OBS observations the answer is no_data, never a floor."""
import numpy as np

from .stats import MIN_NAMES, ic_rows, no_data, panel, t_plain

MIN_DATES = 30
MIN_OBS = 300
N_PERM = 100
Q = 0.95


def _block_shuffle(col, h, rng):
    n = len(col)
    starts = list(range(0, n, h))
    order = rng.permutation(len(starts))
    idx = np.concatenate([np.arange(starts[k], min(starts[k] + h, n)) for k in order])
    return col[idx]


def permutation_null(x, y, dates, names, h=1, n_perm=N_PERM, seed=1587, q=Q, min_names=MIN_NAMES):
    """-> {status, t, floor, exceeds, n_dates, n_obs, n_perm, h, null_median}; t is the observed plain t of the per-date
    IC, floor the q-quantile of |t| under block-shuffled signals"""
    _, _, X, Y = panel(x, y, dates, names)
    n_obs = int(np.isfinite(X).sum())
    obs = ic_rows(X, Y, min_names)
    obs_t = t_plain(obs)
    if obs_t["n"] < MIN_DATES or n_obs < MIN_OBS:
        return no_data(f"{obs_t['n']} dates and {n_obs} observations; need {MIN_DATES} and {MIN_OBS}",
                       n_dates=obs_t["n"], n_obs=n_obs)
    if obs_t["t"] is None:
        return no_data("the per-date IC has no spread", n_dates=obs_t["n"], n_obs=n_obs)
    h = max(1, int(h))
    rng = np.random.default_rng(seed)
    nulls = []
    for _ in range(int(n_perm)):
        Xp = np.empty_like(X)
        for j in range(X.shape[1]):
            Xp[:, j] = _block_shuffle(X[:, j], h, rng)
        tt = t_plain(ic_rows(np.where(np.isfinite(Y), Xp, np.nan), Y, min_names))["t"]
        if tt is not None:
            nulls.append(abs(tt))
    if len(nulls) < 20:
        return no_data(f"only {len(nulls)} usable permutations", n_dates=obs_t["n"], n_obs=n_obs)
    floor = float(np.quantile(nulls, q))
    return {"status": "ok", "t": round(obs_t["t"], 3), "floor": round(floor, 3),
            "exceeds": bool(abs(obs_t["t"]) > floor), "n_dates": obs_t["n"], "n_obs": n_obs, "n_perm": len(nulls),
            "h": h, "null_median": round(float(np.median(nulls)), 3)}


null_floor = permutation_null
