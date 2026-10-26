#!/usr/bin/env python3
"""Step 5: dev-fold backtest (2016-2021) — distance primary, Engle-Granger
secondary, random-pair control (Decision #37). RESEARCH ONLY.

Per pre-registration:
- 12m formation / 6m trading, 6-month roll, 10 folds (explicit schedule below).
- Distance: top-20 pairs by sum of squared deviations of normalized prices.
- EG secondary: ADF(1) Engle-Granger filter on top-200 distance candidates,
  top-20 by most negative ADF t-stat.
- Entry |z|>2.0 (formation-window sigma), exit |z|<0.5, stop at |z|>4.0
  adverse, force-close at window end. $1/$1 self-financing. Pairs may reopen.
- Costs: 10bp round-trip per pair trade on $2 committed capital; borrow drag
  35 bps/yr (Saffi & Sigurdsson 2011, value-weighted US avg) applied daily
  as a fraction of the $1 short leg.
- Control: 20 random pairs from the same formed-on universe, identical rules
  (seed 42 documented; seeds 43-47 as robustness).
- Verdict leg: paired t-stat of fold-level NET returns (strategy - control).
- Output: data/dev_results.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.expanduser(
    "~<workspace>/alpaca-swing-desk/desk/research/pair-trading"
)
DATA = os.path.join(BASE, "data")

# Explicit pre-registered fold schedule: 12m formation, 6m trading, 6m roll.
FOLDS = [
    ("2016-01-01", "2016-12-31", "2017-01-01", "2017-06-30"),
    ("2016-07-01", "2017-06-30", "2017-07-01", "2017-12-31"),
    ("2017-01-01", "2017-12-31", "2018-01-01", "2018-06-30"),
    ("2017-07-01", "2018-06-30", "2018-07-01", "2018-12-31"),
    ("2018-01-01", "2018-12-31", "2019-01-01", "2019-06-30"),
    ("2018-07-01", "2019-06-30", "2019-07-01", "2019-12-31"),
    ("2019-01-01", "2019-12-31", "2020-01-01", "2020-06-30"),
    ("2019-07-01", "2020-06-30", "2020-07-01", "2020-12-31"),
    ("2020-01-01", "2020-12-31", "2021-01-01", "2021-06-30"),
    ("2020-07-01", "2021-06-30", "2021-07-01", "2021-12-31"),
]

COST_RT = 0.0010        # 10bp round-trip per pair trade, on $2 committed
BORROW_YR = 0.0035      # 35 bps/yr on the $1 short leg (Saffi & Sigurdsson 2011)
N_PAIRS = 20
CTRL_SEED = 42


def adf1_tstat(y, x):
    """Engle-Granger two-step, ADF(1) with constant on residuals.

    y,x: normalized formation price vectors. Returns t-stat of gamma in
    de_t = c + gamma*e_{t-1} + delta*de_{t-1}.
    """
    n = len(y)
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    de = np.diff(e)
    e_lag = e[:-1]
    de_lag = np.empty_like(de)
    de_lag[0] = 0.0
    de_lag[1:] = de[:-1]
    Z = np.column_stack([np.ones(len(de)), e_lag, de_lag])
    b, res, *_ = np.linalg.lstsq(Z, de, rcond=None)
    dof = len(de) - 3
    s2 = float(res[0]) / dof if res.size else np.nan
    try:
        cov = s2 * np.linalg.inv(Z.T @ Z)
        se = np.sqrt(cov[1, 1])
    except np.linalg.LinAlgError:
        return np.nan
    return float(b[1] / se) if se > 0 else np.nan


def trade_pair(na, nb, mu, sigma, tdates=None, emit=False):
    """Simulate one pair over the trading window.

    na, nb: normalized (formation-base) price vectors incl. ffill; mu/sigma:
    formation spread stats.
    Returns dict with gross/net pnl (fraction of $2 committed), n_trades,
    n_stop, borrow_drag, daily pnl series.

    T3-18 addition (additive, default off): with emit=True and tdates given,
    also returns a "trades" list of per-round-trip dicts (fold/pair attached
    by the caller): direction, entry_date, exit_date, entry_z, exit_z,
    outcome in {converge, adverse_stop, force_close}, gross, net,
    days_active. Core loop logic is untouched; aggregates are identical
    whether emit is on or off.

    Stop-sign fix (2026-10-02, spec deviation repaired): the stop is the
    ADVERSE 4-sigma stop per the pre-reg ("z > 4.0 stop" on the z>2 entry
    leg) and this module's own docstring ("stop at |z|>4.0 adverse"). The
    previous code had the signs flipped -- it exited on favorable-side
    overshoot and rode adverse divergence to window end.
    """
    zero = {
        "gross": 0.0, "net": 0.0, "n_trades": 0, "n_stop": 0,
        "borrow_drag": 0.0, "cost_rt": 0.0, "days_active": 0,
    }
    # Degenerate-input guard (2026-10-02): a z-score is undefined when the
    # formation spread sigma is 0/non-finite, or when a leg has no
    # trading-window data (all-NaN survives ffill/bfill -> 0*NaN poison).
    # No defined signal -> no trade (conservative; formation/selection
    # untouched).
    if not (np.isfinite(sigma) and sigma > 0):
        return zero
    if not (np.all(np.isfinite(na)) and np.all(np.isfinite(nb))):
        return zero
    spread = na - nb
    z = (spread - mu) / sigma
    ra = np.diff(na) / na[:-1]
    rb = np.diff(nb) / nb[:-1]
    # position held during day t decided by signals through close t-1
    pos = np.zeros(len(z), dtype=int)
    state = 0  # +1 long-spread (long A short B), -1 short-spread
    n_trades = 0
    n_stop = 0
    t_entry = None
    z_entry = None
    direction = 0
    trade_log = []
    for t in range(len(z) - 1):
        if state == 0:
            if z[t] > 2.0:
                state = -1
                t_entry, z_entry, direction = t, float(z[t]), -1
            elif z[t] < -2.0:
                state = 1
                t_entry, z_entry, direction = t, float(z[t]), 1
        elif state == 1:  # long A, short B; adverse = spread keeps falling
            if abs(z[t]) < 0.5 or z[t] < -4.0:
                n_trades += 1
                stopped = z[t] < -4.0
                n_stop += 1 if stopped else 0
                if emit:
                    trade_log.append((t_entry, t, direction, z_entry,
                                      float(z[t]),
                                      "adverse_stop" if stopped else "converge"))
                state = 0
        else:  # state == -1: short A, long B; adverse = spread keeps rising
            if abs(z[t]) < 0.5 or z[t] > 4.0:
                n_trades += 1
                stopped = z[t] > 4.0
                n_stop += 1 if stopped else 0
                if emit:
                    trade_log.append((t_entry, t, direction, z_entry,
                                      float(z[t]),
                                      "adverse_stop" if stopped else "converge"))
                state = 0
        pos[t + 1] = state
    if state != 0:  # force close at window end
        n_trades += 1
        if emit:
            trade_log.append((t_entry, len(z) - 1, direction, z_entry,
                              float(z[len(z) - 1]), "force_close"))
    spr = ra - rb  # per-day spread return on $1/$1
    daily = pos[1:] * spr / 2.0  # fraction of $2 committed
    active = (pos[1:] != 0).astype(float)
    borrow = float(np.sum(active)) * (BORROW_YR / 252.0) * 0.5
    gross = float(np.sum(daily))
    net = gross - n_trades * COST_RT - borrow
    result = {
        "gross": gross, "net": net, "n_trades": n_trades, "n_stop": n_stop,
        "borrow_drag": borrow, "cost_rt": n_trades * COST_RT,
        "days_active": int(np.sum(active)),
    }
    if emit:
        trades = []
        for te, tx, dirc, ze, zx, kind in trade_log:
            g = float(np.sum(daily[te:tx]))
            b = (tx - te) * (BORROW_YR / 252.0) * 0.5
            trades.append({
                "direction": dirc,
                "entry_date": str(tdates[te]),
                "exit_date": str(tdates[tx]),
                "entry_z": ze, "exit_z": zx, "outcome": kind,
                "gross": g, "net": g - COST_RT - b,
                "days_active": int(tx - te),
            })
        result["trades"] = trades
    return result


def run_fold(fold_id, fs, fe, ts, te, adj, filt, emit_trades=False):
    expected = filt["expected_days"]
    names = [s for s in filt["symbols"] if s in adj.columns]
    # price filter: median adjusted close over formation >= $5
    fmask = (adj.index >= fs) & (adj.index <= fe)
    medpx = adj.loc[fmask, names].median()
    names = [s for s in names if medpx[s] >= 5.0]
    # formed-on set: complete formation window (every expected trading day)
    fdates = sorted(adj.index[fmask].unique())
    nobs = adj.loc[fmask, names].notna().sum()
    formed = [s for s in names if nobs[s] == expected]
    fsub = adj.loc[fmask, formed]
    X = fsub.values  # days x N
    base = X[0]
    Xn = X / base  # normalized prices
    n_days, n = Xn.shape

    # --- distance matrix (Gram trick) ---
    G = Xn.T @ Xn
    d2 = np.diag(G)
    SSD = d2[:, None] + d2[None, :] - 2.0 * G
    np.fill_diagonal(SSD, np.inf)
    iu = np.triu_indices(n, k=1)
    order = np.argsort(SSD[iu], kind="stable")
    top200 = [(int(iu[0][k]), int(iu[1][k])) for k in order[:200]]
    top20 = [(int(iu[0][k]), int(iu[1][k])) for k in order[:N_PAIRS]]

    # --- EG secondary on top-200 ---
    adf = []
    for i, j in top200:
        t = adf1_tstat(Xn[:, i], Xn[:, j])
        adf.append((t, i, j))
    adf.sort(key=lambda r: (np.inf if np.isnan(r[0]) else r[0]))
    eg20 = [(i, j) for _, i, j in adf[:N_PAIRS]]

    # --- trading window series (formation-base normalization, ffill) ---
    tmask = (adj.index >= ts) & (adj.index <= te)
    tdates = sorted(adj.index[tmask].unique())
    T = adj.loc[tmask, formed].ffill().bfill().values
    Tn = T / base  # formation-base normalized
    mu = Xn.mean(axis=0)
    # spread stats per pair computed on the fly
    def pair_series(i, j):
        na, nb = Tn[:, i], Tn[:, j]
        s = Xn[:, i] - Xn[:, j]
        m, sd = s.mean(), s.std()
        return na, nb, m, sd

    dist_res = [trade_pair(*pair_series(i, j), tdates=tdates,
                             emit=emit_trades)
                for i, j in top20]
    eg_res = [trade_pair(*pair_series(i, j))
              for i, j in eg20]

    # --- random-pair control (seed 42 primary) ---
    rng = np.random.default_rng(CTRL_SEED)
    idx = rng.choice(n, size=2 * N_PAIRS, replace=False)
    ctrl_pairs = [(int(idx[2 * k]), int(idx[2 * k + 1])) for k in range(N_PAIRS)]
    ctrl_res = [trade_pair(*pair_series(i, j))
                for i, j in ctrl_pairs]

    # --- robustness: seeds 43-47 mean ---
    ctrl_means = []
    for seed in range(43, 48):
        r2 = np.random.default_rng(seed)
        idx2 = r2.choice(n, size=2 * N_PAIRS, replace=False)
        pr = [(int(idx2[2 * k]), int(idx2[2 * k + 1])) for k in range(N_PAIRS)]
        rr = [trade_pair(*pair_series(i, j))
              for i, j in pr]
        ctrl_means.append(np.mean([x["net"] for x in rr]))
    ctrl_robust = float(np.mean(ctrl_means))

    # --- universe baseline: EW buy-and-hold over trading window ---
    first = adj.loc[tmask, formed].apply(lambda c: c.dropna().iloc[0] if c.notna().any() else np.nan)
    last = adj.loc[tmask, formed].apply(lambda c: c.dropna().iloc[-1] if c.notna().any() else np.nan)
    bh = (last / first - 1).dropna()
    baseline = float(bh.mean())

    def agg(res):
        return {
            "gross": float(np.mean([r["gross"] for r in res])),
            "net": float(np.mean([r["net"] for r in res])),
            "n_trades": int(np.sum([r["n_trades"] for r in res])),
            "n_stop": int(np.sum([r["n_stop"] for r in res])),
            "borrow_drag": float(np.sum([r["borrow_drag"] for r in res])),
            "cost_rt": float(np.sum([r["cost_rt"] for r in res])),
            "days_active": int(np.sum([r["days_active"] for r in res])),
        }

    fold_out = {
        "fold": fold_id,
        "formation": [fs, fe], "trading": [ts, te],
        "n_universe": len(names), "n_formed": n,
        "n_formation_days": n_days, "n_trading_days": len(tdates),
        "distance": agg(dist_res),
        "cointegration": agg(eg_res),
        "control": agg(ctrl_res),
        "control_robust_mean_net": ctrl_robust,
        "universe_baseline": baseline,
        "top20_pairs": [[formed[i], formed[j]] for i, j in top20],
        "eg20_pairs": [[formed[i], formed[j]] for i, j in eg20],
        "ctrl20_pairs": [[formed[i], formed[j]] for i, j in ctrl_pairs],
    }
    if emit_trades:
        log = []
        for (i, j), r in zip(top20, dist_res):
            for tr in r.get("trades", []):
                tr = dict(tr)
                tr["fold"] = fold_id
                tr["leg_a"] = formed[i]
                tr["leg_b"] = formed[j]
                log.append(tr)
        fold_out["trade_log"] = log
    return fold_out


def main():
    # Cleaned adjusted bars (04_clean_adj.py): bad-tick bars (extreme
    # single-day adjusted return on negligible volume, e.g. corporate-action
    # transition garbage prints) set to NaN; ffill in run_fold bridges them.
    adj = pd.read_parquet(os.path.join(DATA, "bars_adj_clean.parquet"))
    adj = adj.pivot(index="date", columns="symbol", values="c_adj").sort_index()
    adj.index = adj.index.astype(str)
    with open(os.path.join(DATA, "filter_pass.json")) as f:
        filt = json.load(f)

    folds_out = []
    for k, (fs, fe, ts, te) in enumerate(FOLDS, 1):
        r = run_fold(k, fs, fe, ts, te, adj, filt[f"fold{k}"])
        folds_out.append(r)
        print(f"fold{k}: N={r['n_formed']} dist_net={r['distance']['net']:.4f} "
              f"ctrl_net={r['control']['net']:.4f} "
              f"base={r['universe_baseline']:.4f}", file=sys.stderr)

    d = np.array([f["distance"]["net"] - f["control"]["net"] for f in folds_out])
    t_fold = float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))))
    d_eg = np.array([f["cointegration"]["net"] - f["control"]["net"] for f in folds_out])
    t_eg = float(d_eg.mean() / (d_eg.std(ddof=1) / np.sqrt(len(d_eg))))

    out = {
        "folds": folds_out,
        "aggregate": {
            "n_folds": len(folds_out),
            "distance_net_mean": float(np.mean([f["distance"]["net"] for f in folds_out])),
            "distance_gross_mean": float(np.mean([f["distance"]["gross"] for f in folds_out])),
            "control_net_mean": float(np.mean([f["control"]["net"] for f in folds_out])),
            "control_gross_mean": float(np.mean([f["control"]["gross"] for f in folds_out])),
            "eg_net_mean": float(np.mean([f["cointegration"]["net"] for f in folds_out])),
            "baseline_mean": float(np.mean([f["universe_baseline"] for f in folds_out])),
            "diff_net_mean": float(d.mean()),
            "t_stat_paired_fold_net": t_fold,
            "t_stat_paired_fold_net_eg": t_eg,
            "total_round_trips_dist": int(np.sum([f["distance"]["n_trades"] for f in folds_out])),
            "total_round_trips_ctrl": int(np.sum([f["control"]["n_trades"] for f in folds_out])),
            "total_borrow_drag_dist": float(np.sum([f["distance"]["borrow_drag"] for f in folds_out])),
            "total_rt_cost_dist": float(np.sum([f["distance"]["cost_rt"] for f in folds_out])),
            "cost_model": "10bp round-trip per pair trade on $2 committed; "
                          "borrow 35bps/yr (Saffi & Sigurdsson 2011) daily on $1 short leg",
        },
    }
    with open(os.path.join(DATA, "dev_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out["aggregate"], indent=2))


if __name__ == "__main__":
    main()
