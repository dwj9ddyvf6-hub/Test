"""C198 - the rolling-start gate and the factor-disguise check.

Rolling start: the score is rerun from `n_starts` different discovery start dates (the first start is the panel's
first date, the others at 10, 20, 30, 40 percent of the discovery span). For each start the discovery mean IC (start to
the split, less the embargo) is compared with the holdout mean IC (after the split); the gate wants the same non-zero
sign in `need` of the `n_starts` runs. The split is a date or the first `frac` of the dates; discovery drops the
sessions within EMBARGO_DAYS calendar days of the split (their labels run into the holdout), the picker's rule.

Factor disguise: a signal that is a known factor in another coat. Each date's cross-section of the signal is regressed
(OLS with an intercept) on the registered factors, the residual is scored against the outcome, and the partial IC is
compared with the raw one. Disguised = the partial IC t under 2, or less than half the raw IC kept, or the sign flipped.
Both answer no_data under MIN_DATES usable dates."""
from datetime import date

import numpy as np

from .stats import MIN_NAMES, ic_rows, no_data, panel, t_plain

EMBARGO_DAYS = 45                        # desk/picker/model.EMBARGO_DAYS
MIN_DATES = 30
N_STARTS = 5
NEED = 4
START_FRACS = (0.0, 0.1, 0.2, 0.3, 0.4)
REGISTERED = ("mom.r126", "mom.volscaled", "chk.px_dema200")
KEEP_MIN = 0.5
T_MIN = 2.0


def _d(v):
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def _sign(v):
    return 0 if v is None or v == 0 else (1 if v > 0 else -1)


def rolling_start_gate(x, y, dates, names, split=None, frac=0.6, embargo_days=EMBARGO_DAYS, n_starts=N_STARTS,
                       need=NEED, min_names=MIN_NAMES):
    """-> {status, pass, n_same, need, starts: [{start, discovery_n, discovery_mean, holdout_n, holdout_mean,
    same_sign}], split}"""
    ds, _, X, Y = panel(x, y, dates, names)
    ic = ic_rows(X, Y, min_names)
    ok = np.isfinite(ic)
    ds, ic = np.asarray([_d(v) for v in ds])[ok], ic[ok]
    if len(ds) < 2 * MIN_DATES:
        return no_data(f"{len(ds)} usable dates; need {2 * MIN_DATES}", n_dates=int(len(ds)))
    sp = _d(split) if split is not None else ds[min(len(ds) - 1, max(0, int(len(ds) * frac)))]
    hold = ic[np.asarray([d >= sp for d in ds])]
    cut = date.fromordinal(sp.toordinal() - int(embargo_days))
    disc_mask = np.asarray([d < cut for d in ds])
    disc_d, disc_ic = ds[disc_mask], ic[disc_mask]
    if len(hold) < MIN_DATES or len(disc_ic) < MIN_DATES:
        return no_data(f"{len(disc_ic)} discovery and {len(hold)} holdout dates; need {MIN_DATES} each",
                       n_dates=int(len(ds)))
    fr = START_FRACS if n_starts == N_STARTS else tuple(0.4 * k / max(1, n_starts - 1) for k in range(n_starts))
    hmean = float(hold.mean())
    starts, same = [], 0
    for f in fr:
        k = int(len(disc_ic) * f)
        seg = disc_ic[k:]
        if len(seg) < MIN_DATES:
            starts.append({"start": disc_d[k].isoformat(), "discovery_n": int(len(seg)), "discovery_mean": None,
                           "holdout_n": int(len(hold)), "holdout_mean": round(hmean, 4), "same_sign": False})
            continue
        dm = float(seg.mean())
        ss = _sign(dm) != 0 and _sign(dm) == _sign(hmean)
        same += int(ss)
        starts.append({"start": disc_d[k].isoformat(), "discovery_n": int(len(seg)), "discovery_mean": round(dm, 4),
                       "holdout_n": int(len(hold)), "holdout_mean": round(hmean, 4), "same_sign": bool(ss)})
    return {"status": "ok", "pass": bool(same >= need), "n_same": same, "need": need, "n_starts": len(starts),
            "starts": starts, "split": sp.isoformat()}


def factor_disguise(x, y, dates, names, factors, min_names=MIN_NAMES):
    """factors: {factor name: array aligned to x}. -> {status, disguised, raw_mean, partial_mean, partial_t, keep,
    factors_used, factors_missing}"""
    used = {k: v for k, v in (factors or {}).items() if v is not None}
    missing = [k for k in REGISTERED if k not in used]
    if not used:
        return no_data("no factor series supplied", factors_missing=missing)
    import pandas as pd
    df = pd.DataFrame({"d": np.asarray(dates), "n": np.asarray(names), "x": np.asarray(x, float),
                       "y": np.asarray(y, float), **{f"f_{k}": np.asarray(v, float) for k, v in used.items()}})
    df = df.dropna()
    fcols = [f"f_{k}" for k in used]
    raw, par, dd = [], [], []
    for d, g in df.groupby("d", sort=True):
        if len(g) < max(min_names, len(fcols) + 5):
            continue
        A = np.column_stack([np.ones(len(g)), g[fcols].to_numpy()])
        coef, *_ = np.linalg.lstsq(A, g["x"].to_numpy(), rcond=None)
        res = g["x"].to_numpy() - A @ coef
        r1 = ic_rows(g[["x"]].T.to_numpy(), g[["y"]].T.to_numpy(), min_names)[0]
        r2 = ic_rows(res[None, :], g[["y"]].T.to_numpy(), min_names)[0]
        if np.isfinite(r1) and np.isfinite(r2):
            raw.append(r1)
            par.append(r2)
            dd.append(d)
    if len(raw) < MIN_DATES:
        return no_data(f"{len(raw)} usable dates; need {MIN_DATES}", factors_missing=missing)
    tr, tp = t_plain(raw), t_plain(par)
    keep = (tp["mean"] / tr["mean"]) if tr["mean"] else None
    disguised = bool(tp["t"] is None or abs(tp["t"]) < T_MIN or keep is None or keep < KEEP_MIN)
    return {"status": "ok", "disguised": disguised, "raw_mean": round(tr["mean"], 4),
            "partial_mean": round(tp["mean"], 4), "partial_t": None if tp["t"] is None else round(tp["t"], 3),
            "keep": None if keep is None else round(keep, 3), "n_dates": len(raw), "factors_used": sorted(used),
            "factors_missing": missing}
