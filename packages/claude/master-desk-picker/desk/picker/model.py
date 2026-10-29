"""Weights earned by measured lift (PICKER.md steps 4-6 and the go-live gate).

  lift       per feature, within a family: the hit rate (T1 before the stop) and mean R of the top third against the
             bottom third, a two-proportion z-test, Benjamini-Hochberg across features (q = 0.10)
  logistic   L2-regularized logistic regression (Newton steps), standardized on the training slice only
  isotonic   pool-adjacent-violators on a held-back calibration slice (the last fifth of the training period by time)
  walk       expanding walk-forward by test period, an embargo of EMBARGO sessions between train and test so no
             training case's outcome overlaps a test case; out-of-sample decile calibration, realized mean R by decile,
             the random-entry baseline under the same exits, and the go-live gate

Expected R of a case = p x reward - (1 - p) x risk, reward = T1 distance / stop distance (its plan's R:R), risk 1."""
import math
from datetime import date, timedelta

import numpy as np

EMBARGO_DAYS = 45              # calendar days (about 30 sessions: the 20-session time stop plus margin)
L2 = 1.0
Q = 0.10


def bh(pvals, q=Q):
    """Benjamini-Hochberg: a boolean list, True where the p-value is a discovery at FDR q"""
    p = np.asarray(pvals, float)
    n = len(p)
    if n == 0:
        return []
    order = np.argsort(p)
    thr = q * (np.arange(1, n + 1)) / n
    ok = p[order] <= thr
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    res = np.zeros(n, bool)
    res[order[:k]] = True
    return res.tolist()


def _norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def lift(X, y, r, names):
    """per feature: top-third vs bottom-third hit rate and mean R, the z-test p-value and the BH verdict"""
    rows = []
    for j, nm in enumerate(names):
        x = X[:, j]
        m = np.isfinite(x)
        if m.sum() < 60 or np.nanstd(x[m]) == 0:
            rows.append({"feature": nm, "n": int(m.sum()), "p": 1.0})
            continue
        lo, hi = np.nanquantile(x[m], [1 / 3, 2 / 3])
        top, bot = m & (x >= hi), m & (x <= lo)
        n1, n0 = int(top.sum()), int(bot.sum())
        if n1 < 20 or n0 < 20:
            rows.append({"feature": nm, "n": int(m.sum()), "p": 1.0})
            continue
        p1, p0 = y[top].mean(), y[bot].mean()
        pp = (y[top].sum() + y[bot].sum()) / (n1 + n0)
        se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n0)) or 1e-9
        z = (p1 - p0) / se
        rows.append({"feature": nm, "n": int(m.sum()), "top_rate": round(100 * p1, 1), "bottom_rate": round(100 * p0, 1),
                     "lift_pts": round(100 * (p1 - p0), 1), "top_r": round(float(np.nanmean(r[top])), 3),
                     "bottom_r": round(float(np.nanmean(r[bot])), 3), "z": round(z, 2), "p": 2 * _norm_sf(abs(z))})
    keep = bh([x["p"] for x in rows])
    for x, k in zip(rows, keep):
        x["discovery"] = bool(k)
        x["p"] = float(f"{x['p']:.3g}")
    return rows


class Logistic:
    def __init__(self, l2=L2, iters=25):
        self.l2, self.iters = l2, iters

    def fit(self, X, y):
        self.mu = np.nanmean(X, axis=0)
        self.sd = np.nanstd(X, axis=0)
        self.sd[~np.isfinite(self.sd) | (self.sd == 0)] = 1.0
        self.mu[~np.isfinite(self.mu)] = 0.0
        Z = self._z(X)
        n, k = Z.shape
        A = np.hstack([np.ones((n, 1)), Z])
        w = np.zeros(k + 1)
        reg = np.full(k + 1, self.l2)
        reg[0] = 0.0
        for _ in range(self.iters):
            p = 1 / (1 + np.exp(-np.clip(A @ w, -30, 30)))
            g = A.T @ (p - y) + reg * w
            H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(reg) + 1e-9 * np.eye(k + 1)
            step = np.linalg.solve(H, g)
            w -= step
            if np.abs(step).max() < 1e-7:
                break
        self.w = w
        return self

    def _z(self, X):
        Z = (X - self.mu) / self.sd
        return np.clip(np.nan_to_num(Z, nan=0.0), -6, 6)

    def predict(self, X):
        Z = self._z(X)
        return 1 / (1 + np.exp(-np.clip(self.w[0] + Z @ self.w[1:], -30, 30)))


class Isotonic:
    """pool-adjacent-violators: a non-decreasing map from score to rate"""

    def fit(self, s, y):
        o = np.argsort(s)
        xs, ys = np.asarray(s, float)[o], np.asarray(y, float)[o]
        blocks = [[ys[0], 1.0, xs[0], xs[0]]]
        for xv, yv in zip(xs[1:], ys[1:]):
            blocks.append([yv, 1.0, xv, xv])
            while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
                b = blocks.pop()
                blocks[-1][0] += b[0]
                blocks[-1][1] += b[1]
                blocks[-1][3] = b[3]
        self.x = np.array([(b[2] + b[3]) / 2 for b in blocks])
        self.y = np.array([b[0] / b[1] for b in blocks])
        return self

    def predict(self, s):
        if len(self.x) == 1:
            return np.full(len(s), self.y[0])
        return np.interp(s, self.x, self.y)


def expected_r(p, rr):
    return p * rr - (1 - p)


def _d(s):
    return date.fromisoformat(s)


def walk_forward(dates, X, y, r, rr, splits, base_r=None):
    """splits: list of (test_start, test_end) ISO dates; train = every case dated before test_start minus the
    embargo. -> out-of-sample predictions (p, er) for the test cases, and per-split notes"""
    d = np.array([_d(x) for x in dates])
    P = np.full(len(y), np.nan)
    notes = []
    for a, b in splits:
        a_, b_ = _d(a), _d(b)
        tr = d < a_ - timedelta(days=EMBARGO_DAYS)
        te = (d >= a_) & (d < b_)
        if tr.sum() < 200 or te.sum() == 0:
            notes.append({"test": [a, b], "train_n": int(tr.sum()), "test_n": int(te.sum()), "skipped": True})
            continue
        idx = np.where(tr)[0]
        idx = idx[np.argsort(d[idx])]
        cut = int(len(idx) * 0.8)
        fit_i, cal_i = idx[:cut], idx[cut:]
        m = Logistic().fit(X[fit_i], y[fit_i])
        iso = Isotonic().fit(m.predict(X[cal_i]), y[cal_i])
        P[te] = iso.predict(m.predict(X[te]))
        notes.append({"test": [a, b], "train_n": int(tr.sum()), "test_n": int(te.sum())})
    er = expected_r(P, rr)
    return P, er, notes


def deciles(P, er, y, r, base_r=None, rr=None):
    """out-of-sample deciles of expected R: predicted rate, realized rate, realized mean R (with SE), the random
    baseline's mean R for the same cases (base_r: per-case random-entry R under the same exits)"""
    m = np.isfinite(P)
    if m.sum() < 50:
        return []
    q = np.quantile(er[m], np.linspace(0, 1, 11))
    out = []
    for k in range(10):
        s = m & (er >= q[k]) & ((er <= q[k + 1]) if k == 9 else (er < q[k + 1]))
        n = int(s.sum())
        if not n:
            continue
        rv = r[s][np.isfinite(r[s])]
        row = {"decile": k + 1, "n": n, "pred": round(100 * float(P[s].mean()), 1),
               "real": round(100 * float(y[s].mean()), 1), "exp_r": round(float(er[s].mean()), 3),
               "mean_r": round(float(rv.mean()), 3) if len(rv) else None,
               "se_r": round(float(rv.std() / math.sqrt(len(rv))), 3) if len(rv) > 1 else None}
        if base_r is not None:
            br = base_r[s][np.isfinite(base_r[s])]
            row["base_r"] = round(float(br.mean()), 3) if len(br) else None
            dlt = rv.mean() - br.mean() if len(br) and len(rv) else None
            se = math.sqrt(rv.var() / max(1, len(rv)) + br.var() / max(1, len(br))) if dlt is not None else None
            row["edge_r"] = round(float(dlt), 3) if dlt is not None else None
            row["edge_lo"] = round(float(dlt - 1.96 * se), 3) if se else None
        out.append(row)
    return out


def gate(dec):
    """PICKER.md go-live gate on out-of-sample deciles: the top decile's mean R > 0 and above the random baseline with
    the 95% interval excluding zero, and every decile's realized rate within 5 points of its predicted rate"""
    if not dec:
        return {"pass": False, "why": "no out-of-sample deciles"}
    top = dec[-1]
    cal = max(abs(x["pred"] - x["real"]) for x in dec)
    why = []
    if not (top.get("mean_r") is not None and top["mean_r"] > 0):
        why.append("top decile mean R not above 0")
    if not (top.get("edge_lo") is not None and top["edge_lo"] > 0):
        why.append("top decile not above the random baseline with the interval excluding 0")
    if cal > 5:
        why.append(f"calibration off by {cal:.1f} points in a decile (limit 5)")
    return {"pass": not why, "why": why, "worst_calibration_pts": round(cal, 1)}


WINSOR = 5.0                   # R clipped to ±WINSOR for the regression (a few data-break tails must not set weights)


class Ridge:
    """L2 linear regression of R on standardized features (the ranking target is mean R itself)"""

    def __init__(self, l2=50.0):
        self.l2 = l2

    def fit(self, X, r):
        self.mu = np.nanmean(X, axis=0)
        self.sd = np.nanstd(X, axis=0)
        self.sd[~np.isfinite(self.sd) | (self.sd == 0)] = 1.0
        self.mu[~np.isfinite(self.mu)] = 0.0
        Z = np.clip(np.nan_to_num((X - self.mu) / self.sd), -6, 6)
        y = np.clip(np.nan_to_num(r), -WINSOR, WINSOR)
        A = np.hstack([np.ones((len(Z), 1)), Z])
        reg = np.full(A.shape[1], self.l2)
        reg[0] = 0.0
        self.w = np.linalg.solve(A.T @ A + np.diag(reg), A.T @ y)
        return self

    def predict(self, X):
        Z = np.clip(np.nan_to_num((X - self.mu) / self.sd), -6, 6)
        return self.w[0] + Z @ self.w[1:]


def walk_forward_r(dates, X, r, splits):
    """out-of-sample predicted mean R by the same expanding, embargoed splits"""
    d = np.array([_d(x) for x in dates])
    out = np.full(len(r), np.nan)
    for a, b in splits:
        a_, b_ = _d(a), _d(b)
        tr = d < a_ - timedelta(days=EMBARGO_DAYS)
        te = (d >= a_) & (d < b_)
        if tr.sum() < 200 or te.sum() == 0:
            continue
        out[te] = Ridge().fit(X[tr], r[tr]).predict(X[te])
    return out


def deciles_r(pred, r, base_r):
    """out-of-sample deciles of predicted mean R: predicted, realized mean R ± SE, random baseline, edge and its low"""
    m = np.isfinite(pred) & np.isfinite(r)
    if m.sum() < 50:
        return []
    q = np.quantile(pred[m], np.linspace(0, 1, 11))
    out = []
    for k in range(10):
        s = m & (pred >= q[k]) & ((pred <= q[k + 1]) if k == 9 else (pred < q[k + 1]))
        rv = np.clip(r[s], -WINSOR, WINSOR)
        br = np.clip(base_r[s][np.isfinite(base_r[s])], -WINSOR, WINSOR)
        row = {"decile": k + 1, "n": int(s.sum()), "pred_r": round(float(pred[s].mean()), 3),
               "mean_r": round(float(rv.mean()), 3), "se_r": round(float(rv.std() / math.sqrt(len(rv))), 3),
               "base_r": round(float(br.mean()), 3) if len(br) else None}
        if len(br) > 1:
            dlt = rv.mean() - br.mean()
            se = math.sqrt(rv.var() / len(rv) + br.var() / len(br))
            row["edge_r"], row["edge_lo"] = round(float(dlt), 3), round(float(dlt - 1.96 * se), 3)
        out.append(row)
    return out
