"""Sleeve ensemble (FACTORY.md §9, track P1-S): portfolio-level reading of the sleeves' forward record. Read-only and
advisory: it reads books (daily equity curves) and the ledger's book_fill rows that already exist, never runs a
sleeve, never backtests, and never changes a decision, size or order. Its output is a set of proposals for the owner.

Pipeline (pure functions over plain data):
  daily_returns   per-sleeve session returns on one NYSE-session calendar (a 24/7 book's weekend move folds into the
                  next session), NaN while the sleeve is not alive; sessions-alive counts
  fill_hash       sha256 of each sleeve's (session, inst, side, qty / max qty) fill sequence -> identical-fill groups
  pairwise_corr   Pearson rho on each pair's overlapping alive sessions (NaN below min_overlap)
  clusters        union of identical-fill groups and rho >= 0.95 twins (single linkage); each cluster is one bet
  lw_corr         Ledoit-Wolf (2004) shrinkage of the correlation matrix toward the identity
  loo             equal-risk portfolio Sharpe and max drawdown with vs without each sleeve, bootstrap CI over days
  evidence        PSR / DSR from desk.learn.evidence; empirical-Bayes shrunk Sharpe (its formula)
  effective_bets  cluster count; participation ratio (sum lambda)^2 / sum lambda^2 of the shrunk cluster correlation;
                  BR = (sum q)^2 / q'Cq (FACTORY §7)
  allocate        w proportional to C^-1 q over clusters, clipped >= 0, with a bootstrap band
"""
import hashlib
import math
from datetime import date, datetime

import numpy as np

from .. import calendar as cal
from ..learn import evidence as EV
from ..util import ET

PERIODS = 252                 # session calendar
MIN_RECORD = EV.MIN_RETURNS   # FACTORY §9: T_s >= 20 forward days before a label is more than provisional
MIN_OVERLAP = 5               # exploratory pairwise overlap (FACTORY's confident gate is MIN_RECORD)
TWIN_RHO = 0.95
REDUNDANT_RHO = 0.8
DIVERSIFIER_RHO = 0.5
LINKAGE_RHO = 0.6
SIGMA_FLOOR = 1e-4            # 1 bp/day: a near-flat book is not levered to unit risk


# ---------------------------------------------------------------- daily P&L on a common calendar
def _last_by_date(curve):
    out = {}
    for ts, eq in curve or ():
        out[datetime.fromtimestamp(float(ts), tz=ET).date()] = float(eq)
    return out


def daily_returns(books, sessions=None):
    """books: {sid: book document}. -> dict(dates, sids, R (T x N returns, NaN when not alive), P ($ P&L),
    alive (sessions alive per sleeve), capital). A session return is E(d_i)/E(d_{i-1}) - 1 where E(d) is the last
    mark on or before date d; a sleeve is alive from its first mark through its last mark."""
    marks = {sid: _last_by_date(b.get("curve")) for sid, b in books.items()}
    marks = {sid: m for sid, m in marks.items() if m}
    if sessions is None:
        alld = sorted({d for m in marks.values() for d in m})
        sessions = [d for d in _date_range(alld[0], alld[-1]) if cal.is_trading_day(d)] if alld else []
    sessions = [d if isinstance(d, date) else date.fromisoformat(d) for d in sessions]
    sids = sorted(marks)
    T, N = max(len(sessions) - 1, 0), len(sids)
    E = np.full((len(sessions), N), np.nan)
    for j, sid in enumerate(sids):
        m = marks[sid]
        ds = sorted(m)
        first, last = ds[0], ds[-1]
        k, cur = 0, None
        for i, d in enumerate(sessions):
            while k < len(ds) and ds[k] <= d:
                cur = m[ds[k]]
                k += 1
            if d >= first and (d <= last or (i > 0 and sessions[i - 1] < last)):
                E[i, j] = cur
    with np.errstate(invalid="ignore", divide="ignore"):
        P = E[1:] - E[:-1] if T else np.zeros((0, N))
        R = np.where(E[:-1] > 0, P / E[:-1], np.nan) if T else np.zeros((0, N))
    alive = (~np.isnan(R)).sum(axis=0)
    cap = np.array([float(books[s].get("capital") or 100_000.0) for s in sids])
    return {"dates": [d.isoformat() for d in sessions[1:]], "sids": sids, "R": R, "P": P, "alive": alive,
            "capital": cap}


def _date_range(a, b):
    out, d = [], a
    while d <= b:
        out.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return out


# ---------------------------------------------------------------- identical fills
def fill_hashes(fills, normalise=True):
    """fills: iterable of ledger book_fill rows {sleeve, inst, side, qty, at}. -> {sid: (sha256, n_fills)}. Fills are
    summed per (ET session date, inst, side), quantities divided by the sleeve's largest such sum (so a 2x copy of a
    sleeve hashes the same; normalise=False keeps raw quantities: exact copies only) and rounded to 6 significant
    figures."""
    agg = {}
    for r in fills:
        sid = r.get("sleeve")
        if not sid:
            continue
        d = datetime.fromtimestamp(float(r["at"]), tz=ET).date().isoformat()
        k = (d, str(r["inst"]), str(r["side"]))
        a = agg.setdefault(sid, {})
        n, q = a.get(k, (0, 0.0))
        a[k] = (n + 1, q + abs(float(r["qty"])))
    out = {}
    for sid, a in agg.items():
        mx = (max(q for _, q in a.values()) or 1.0) if normalise else 1.0
        seq = sorted((d, i, s, float(f"{q / mx:.6g}")) for (d, i, s), (_, q) in a.items())
        h = hashlib.sha256(repr(seq).encode()).hexdigest()
        out[sid] = (h, sum(n for n, _ in a.values()))
    return out


def identical_fill_groups(hashes):
    """{sid: (hash, n)} -> sorted list of groups (lists of sids) of size >= 2 sharing one fill sequence."""
    by = {}
    for sid, (h, _) in hashes.items():
        by.setdefault(h, []).append(sid)
    return sorted((sorted(g) for g in by.values() if len(g) > 1), key=lambda g: (-len(g), g[0]))


# ---------------------------------------------------------------- correlation
def pairwise_corr(R, min_overlap=MIN_OVERLAP):
    """-> (rho N x N with NaN where the overlap < min_overlap or a side is flat on it, overlap counts). The overlap of
    a pair counts the sessions both are alive and at least one moved: two sleeves flat on the same days share no
    evidence, and counting those days would let two active sessions decide a "twin"."""
    M = (~np.isnan(R)).astype(float)
    X = np.nan_to_num(R)
    nz = (X != 0).astype(float)
    n = M.T @ M
    active = n - ((M * (1 - nz)).T @ (M * (1 - nz)))
    sx = X.T @ M                      # sum of x_i over days where j alive
    sxx = (X * X).T @ M
    sxy = X.T @ X
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sxy / n - (sx / n) * (sx.T / n)
        vi = sxx / n - (sx / n) ** 2
        rho = cov / np.sqrt(vi * vi.T)
    bad = (active < min_overlap) | ~(vi > 1e-18) | ~(vi.T > 1e-18)
    rho[bad] = np.nan
    np.fill_diagonal(rho, 1.0)
    return np.clip(rho, -1.0, 1.0), active.astype(int)


def standardize(R):
    """z-score each column on its alive days, zero elsewhere, scaled so that diag(X'X/T) = 1."""
    T = R.shape[0]
    Z = np.zeros_like(R, dtype=float)
    for j in range(R.shape[1]):
        a = ~np.isnan(R[:, j])
        x = R[a, j]
        if len(x) >= 2 and x.std() > 0:
            Z[a, j] = (x - x.mean()) / x.std() * math.sqrt(T / len(x))
    return Z


def lw_corr(Z):
    """Ledoit-Wolf shrinkage of S = Z'Z/T toward the identity (Z standardized). -> (C, delta)."""
    T, N = Z.shape
    if T == 0 or N == 0:
        return np.eye(N), 1.0
    S = Z.T @ Z / T
    mu = np.trace(S) / N
    F = mu * np.eye(N)
    d2 = ((S - F) ** 2).sum()
    b2bar = (((Z * Z).sum(axis=1) ** 2).sum() / T - (S ** 2).sum()) / T     # (1/T^2) sum_t ||z z' - S||^2
    b2 = min(max(b2bar, 0.0), d2)
    delta = b2 / d2 if d2 > 0 else 1.0
    C = delta * F + (1 - delta) * S
    s = np.sqrt(np.diag(C))
    s[s == 0] = 1.0
    return C / np.outer(s, s), float(delta)


# ---------------------------------------------------------------- clusters
class _UF:
    def __init__(self, items):
        self.p = {i: i for i in items}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def twin_groups(rho, twin_rho=TWIN_RHO):
    """complete linkage on rho (missing = 0): groups whose every pair has rho >= twin_rho. Single linkage would chain
    unrelated sleeves through short, noisy overlaps. -> list of index lists (size >= 2)."""
    n = rho.shape[0]
    if n < 2:
        return []
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    r = np.nan_to_num(rho, nan=0.0)
    D = np.clip(1.0 - (r + r.T) / 2, 0.0, 2.0)
    np.fill_diagonal(D, 0.0)
    lab = fcluster(linkage(squareform(D, checks=False), method="complete"), t=1.0 - twin_rho + 1e-12,
                   criterion="distance")
    g = {}
    for i, k in enumerate(lab):
        g.setdefault(k, []).append(i)
    return [v for v in g.values() if len(v) > 1]


def clusters(sids, rho, fill_groups, twin_rho=TWIN_RHO):
    """-> list of clusters (each {members, why}), every sid in exactly one; why in {"fills", "rho", "fills+rho",
    "single"}, and the identical-fill pairs whose P&L disagrees (rho < REDUNDANT_RHO), which are not merged.
    Identical-fill groups and complete-linkage rho twins are merged (union): each cluster is one bet."""
    uf = _UF(sids)
    idx = {s: i for i, s in enumerate(sids)}
    why = {}
    conflicts = []
    for g in fill_groups:
        g = [s for s in g if s in idx]
        for a in range(len(g)):
            for b in range(a + 1, len(g)):
                r = rho[idx[g[a]], idx[g[b]]]
                if not np.isnan(r) and r < REDUNDANT_RHO:      # same fills, different P&L: a record question
                    conflicts.append((g[a], g[b], round(float(r), 4)))
                    continue
                uf.union(g[a], g[b])
                why.setdefault(g[a], set()).add("fills")
                why.setdefault(g[b], set()).add("fills")
    for g in twin_groups(rho, twin_rho):
        for i in g[1:]:
            uf.union(sids[g[0]], sids[i])
        for i in g:
            why.setdefault(sids[i], set()).add("rho")
    groups = {}
    for s in sids:
        groups.setdefault(uf.find(s), []).append(s)
    out = []
    for g in groups.values():
        w = set().union(*(why.get(s, set()) for s in g)) if len(g) > 1 else set()
        out.append({"members": sorted(g), "why": "+".join(sorted(w)) if w else "single"})
    return sorted(out, key=lambda c: (-len(c["members"]), c["members"][0])), conflicts


def exposure_twins(books, sids, rho, inst="EQ:QQQ", thr=TWIN_RHO):
    """sleeves whose daily P&L has rho >= thr with a reference book that only ever held `inst` (long-QQQ twins)."""
    refs = [i for i, s in enumerate(sids)
            if set(books[s].get("positions") or {}) | {t.get("inst") for t in books[s].get("trades") or ()} == {inst}]
    hit = set(refs)
    for i in refs:
        hit |= set(np.where(np.nan_to_num(rho[i], nan=0.0) >= thr)[0].tolist())
    return {"inst": inst, "references": sorted(sids[i] for i in refs), "twins": sorted(sids[i] for i in hit)}


def linkage_count(rho, cut_rho=LINKAGE_RHO):
    """FACTORY §9: average-linkage hierarchical clusters, distance sqrt(2(1 - rho)), missing rho = 0, cut at rho."""
    n = rho.shape[0]
    if n < 2:
        return n
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    r = np.nan_to_num(rho, nan=0.0)
    D = np.sqrt(np.clip(2.0 * (1.0 - r), 0.0, None))
    np.fill_diagonal(D, 0.0)
    Z = linkage(squareform((D + D.T) / 2, checks=False), method="average")
    return int(fcluster(Z, t=math.sqrt(2.0 * (1.0 - cut_rho)), criterion="distance").max())


# ---------------------------------------------------------------- leave-one-out
def _sr(p):
    p = np.asarray(p, float)
    if p.shape[0] < 2:
        return np.nan
    sd = p.std(axis=0, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(sd > 0, p.mean(axis=0) / sd, np.nan)


def _mdd(p):
    """max drawdown of the additive cumulative return path (columns), from a start of 0."""
    c = np.cumsum(np.asarray(p, float), axis=0)
    c = np.concatenate([np.zeros((1,) + c.shape[1:]), c], axis=0)
    return (np.maximum.accumulate(c, axis=0) - c).max(axis=0)


def risk_units(R, sigma_floor=SIGMA_FLOOR):
    """each sleeve scaled to 1% daily risk on its alive days: x = r / max(sd, floor) * 0.01, 0 when not alive."""
    sd = np.array([np.nanstd(R[:, j], ddof=1) if (~np.isnan(R[:, j])).sum() >= 2 else np.nan
                   for j in range(R.shape[1])])
    sd = np.where(np.isnan(sd), sigma_floor, np.maximum(sd, sigma_floor))
    return np.nan_to_num(R) / sd * 0.01


def loo(X, n_boot=1000, seed=7):
    """X: T x N risk-unit returns. Equal-risk portfolio p = mean over sleeves; without s: (N p - x_s)/(N - 1).
    -> dict(sr, mdd, mc_sr[N] = SR(with) - SR(without) (per session), mc_dd[N] = MDD(with) - MDD(without)
    (> 0: s deepens the drawdown), mc_lo/mc_hi bootstrap 95% over days, rho_desk[N] = corr(x_s, desk without s))."""
    T, N = X.shape
    p = X.mean(axis=1)
    W = (N * p[:, None] - X) / (N - 1)
    sr_all, mdd_all = float(_sr(p)), float(_mdd(p))
    mc = sr_all - _sr(W)
    mcdd = mdd_all - _mdd(W)
    with np.errstate(invalid="ignore", divide="ignore"):
        xc, wc = X - X.mean(axis=0), W - W.mean(axis=0)
        rho_desk = (xc * wc).sum(axis=0) / np.sqrt((xc ** 2).sum(axis=0) * (wc ** 2).sum(axis=0))
    rng = np.random.default_rng(seed)
    bs = np.empty((n_boot, N))
    for b in range(n_boot):
        i = rng.integers(0, T, T)
        bs[b] = _sr(p[i]) - _sr(W[i])
    with np.errstate(invalid="ignore"):
        lo, hi = np.nanpercentile(bs, 2.5, axis=0), np.nanpercentile(bs, 97.5, axis=0)
    return {"sr": sr_all, "mdd": mdd_all, "mc_sr": mc, "mc_dd": mcdd, "mc_lo": lo, "mc_hi": hi, "rho_desk": rho_desk}


# ---------------------------------------------------------------- evidence
def sleeve_evidence(R):
    """per sleeve on its alive days: daily SR, T, skew, raw kurtosis, PSR(0), DSR (SR0 from the cross-section via
    learn.evidence.expected_max_sr), and the empirical-Bayes shrunk SR (learn.evidence's formula)."""
    rows = []
    for j in range(R.shape[1]):
        x = R[~np.isnan(R[:, j]), j]
        t = len(x)
        sd = x.std() if t else 0.0
        if t >= 2 and sd > 0:
            mu = x.mean()
            rows.append((mu / sd, t, float(((x - mu) ** 3).mean() / sd ** 3), float(((x - mu) ** 4).mean() / sd ** 4)))
        else:
            rows.append(None)
    ok = [r for r in rows if r]
    n = len(ok)
    srs = [r[0] for r in ok]
    m = sum(srs) / n if n else 0.0
    var = sum((s - m) ** 2 for s in srs) / (n - 1) if n > 1 else 0.0
    sr0 = EV.expected_max_sr(var, n)
    se2 = [max(EV._q(*r[:1], r[2], r[3]), 1e-12) / r[1] for r in ok]
    tau2 = max(0.0, var - (sum(se2) / n if n else 0.0))
    out = []
    for r in rows:
        if not r:
            out.append({"sr": None, "t": 0, "psr": None, "dsr": None, "shrunk": None})
            continue
        sr, t, g3, g4 = r
        s2 = max(EV._q(sr, g3, g4), 1e-12) / t
        w = tau2 / (tau2 + s2) if tau2 + s2 > 0 else 0.0
        out.append({"sr": sr, "t": t, "psr": EV.psr(sr, t, g3, g4), "dsr": EV.psr(sr, t, g3, g4, sr_star=sr0),
                    "shrunk": m + w * (sr - m)})
    return out, {"n": n, "mean_sr": m, "var_sr": var, "sr0": sr0, "tau2": tau2}


# ---------------------------------------------------------------- bets and allocation
def participation_ratio(C):
    lam = np.clip(np.linalg.eigvalsh(C), 0.0, None)
    return float(lam.sum() ** 2 / (lam ** 2).sum()) if lam.sum() > 0 else 0.0


def cluster_series(Z, members_idx):
    """mean of the members' standardized series, re-standardized (one column per cluster)."""
    S = np.column_stack([Z[:, ix].mean(axis=1) for ix in members_idx]) if members_idx else np.zeros((Z.shape[0], 0))
    T = S.shape[0]
    for j in range(S.shape[1]):
        v = math.sqrt((S[:, j] ** 2).sum() / T) if T else 0.0
        if v > 0:
            S[:, j] /= v
    return S


def independence_weights(C, q):
    """w proportional to C^-1 q, clipped >= 0, normalised to sum 1 (all zero when nothing is positive)."""
    w = np.linalg.solve(C, q) if len(q) else np.zeros(0)
    w = np.clip(w, 0.0, None)
    return w / w.sum() if w.sum() > 0 else w


def effective_bets(C, q=None):
    out = {"clusters": int(C.shape[0]), "participation_ratio": participation_ratio(C)}
    if q is not None and len(q):
        qp = np.clip(np.asarray(q, float), 0.0, None)
        den = float(qp @ C @ qp)
        out["breadth_q"] = float(qp.sum() ** 2 / den) if den > 0 else 0.0
    return out


# ---------------------------------------------------------------- the whole report
def build(books, fills, min_overlap=MIN_OVERLAP, n_boot=1000, seed=7):
    """books: {sid: book}; fills: iterable of ledger book_fill rows. -> the report dict (JSON-ready)."""
    fills = list(fills)
    dr = daily_returns(books)
    R_all, sids_all = dr["R"], dr["sids"]
    nf = {sid: int(books[sid].get("n_fills") or 0) for sid in sids_all}
    hashes = fill_hashes(fills)
    keep = [j for j, s in enumerate(sids_all)
            if dr["alive"][j] >= 2 and (nf[s] > 0 or s in hashes) and np.nanstd(R_all[:, j]) > 0]
    sids = [sids_all[j] for j in keep]
    R = R_all[:, keep]
    rho, ov = pairwise_corr(R, min_overlap)
    fgroups = identical_fill_groups(hashes)
    exact = identical_fill_groups(fill_hashes(fills, normalise=False))
    fgroups_rec = [[s for s in g if s in set(sids)] for g in fgroups]
    qqq = exposure_twins(books, sids, rho)
    cl, conflicts = clusters(sids, rho, [g for g in fgroups_rec if len(g) > 1])
    idx = {s: i for i, s in enumerate(sids)}
    Z = standardize(R)
    C_s, delta_s = lw_corr(Z)
    ev, evs = sleeve_evidence(R)
    q = np.array([e["shrunk"] for e in ev], float)
    X = risk_units(R)
    lo = loo(X, n_boot=n_boot, seed=seed)

    mem_idx = [[idx[s] for s in c["members"]] for c in cl]
    S = cluster_series(Z, mem_idx)
    C_c, delta_c = lw_corr(S)
    qc = np.array([float(np.mean(q[ix])) for ix in mem_idx])
    w = independence_weights(C_c, qc)
    rng = np.random.default_rng(seed + 1)
    T = R.shape[0]
    wb = []
    for _ in range(max(n_boot // 5, 50)):
        i = rng.integers(0, T, T)
        evb, _ = sleeve_evidence(R[i])
        qb = np.array([e["shrunk"] if e["shrunk"] is not None else 0.0 for e in evb])
        Cb, _ = lw_corr(cluster_series(standardize(R[i]), mem_idx))
        wb.append(independence_weights(Cb, np.array([qb[ix].mean() for ix in mem_idx])))
    wb = np.array(wb)
    bets = effective_bets(C_c, qc)
    bets["sleeves"] = len(sids)
    bets["participation_ratio_sleeves_no_dedup"] = participation_ratio(C_s)
    bets["linkage_clusters_rho_0_6"] = linkage_count(rho)
    bets["record_bound"] = max(T - 1, 0)

    cl_of = {}
    for k, c in enumerate(cl):
        for s in c["members"]:
            cl_of[s] = k
    absr = np.abs(np.nan_to_num(rho, nan=0.0))
    np.fill_diagonal(absr, 0.0)
    rows = []
    for i, s in enumerate(sids):
        e = ev[i]
        better = [j for j in range(len(sids)) if j != i and np.nan_to_num(rho[i, j], nan=0) >= REDUNDANT_RHO
                  and (q[j] > q[i] or (q[j] == q[i] and sids[j] < s))]
        mc, mlo, mhi = float(lo["mc_sr"][i]), float(lo["mc_lo"][i]), float(lo["mc_hi"][i])
        rd = float(lo["rho_desk"][i]) if not np.isnan(lo["rho_desk"][i]) else 1.0
        if mc < 0 and mhi < 0:
            prov = "drag"
        elif mc > 0 and mlo > 0 and (e["dsr"] or 0) >= 0.95:
            prov = "core"
        elif better:
            prov = "redundant"
        elif mc > 0 and rd < DIVERSIFIER_RHO:
            prov = "diversifier"
        else:
            prov = "neutral"
        k = cl_of[s]
        rows.append({"sleeve": s, "sessions_alive": int(dr["alive"][sids_all.index(s)]), "fills": nf[s],
                     "pnl_usd": round(float(np.nansum(dr["P"][:, sids_all.index(s)])), 2),
                     "sr_daily": _rd(e["sr"]), "psr": _rd(e["psr"]), "dsr": _rd(e["dsr"]), "q_shrunk": _rd(e["shrunk"]),
                     "mc_sr": _rd(mc), "mc_sr_ci": [_rd(mlo), _rd(mhi)], "mc_dd": _rd(float(lo["mc_dd"][i])),
                     "max_abs_rho": _rd(float(absr[i].max())), "rho_desk": _rd(float(lo["rho_desk"][i])), "cluster": k, "cluster_size": len(cl[k]["members"]),
                     "provisional_label": prov,
                     "label": prov if e["t"] >= MIN_RECORD else "unproven",
                     "low_confidence": bool(e["t"] < MIN_RECORD)})
    clus = []
    for k, c in enumerate(cl):
        ix = mem_idx[k]
        rep = max(c["members"], key=lambda s: (q[idx[s]], s))
        sub = rho[np.ix_(ix, ix)]
        clus.append({"id": k, "members": c["members"], "size": len(ix), "why": c["why"], "representative": rep,
                     "min_rho": _rd(float(np.nanmin(sub))) if len(ix) > 1 else None, "q": _rd(float(qc[k])),
                     "weight": _rd(float(w[k])), "weight_band": [_rd(float(np.percentile(wb[:, k], 5))),
                                                                 _rd(float(np.percentile(wb[:, k], 95)))]})
    return {"version": "ensemble-1", "calendar": {"first": dr["dates"][0] if dr["dates"] else None,
                                                  "last": dr["dates"][-1] if dr["dates"] else None,
                                                  "sessions": len(dr["dates"])},
            "params": {"min_overlap": min_overlap, "min_record": MIN_RECORD, "twin_rho": TWIN_RHO,
                       "redundant_rho": REDUNDANT_RHO, "diversifier_rho": DIVERSIFIER_RHO, "sigma_floor": SIGMA_FLOOR,
                       "n_boot": n_boot, "seed": seed},
            "counts": {"books": len(books), "with_curve": len(sids_all), "with_record": len(sids),
                       "sleeves_with_fills_in_ledger": len(hashes),
                       "identical_fill_groups": len(fgroups), "identical_fill_sleeves": sum(len(g) for g in fgroups),
                       "exact_fill_groups": len(exact), "exact_fill_sleeves": sum(len(g) for g in exact),
                       "clusters": len(cl), "multi_member_clusters": sum(1 for c in cl if len(c["members"]) > 1),
                       "pairs_with_overlap": int(((ov >= min_overlap).sum() - len(sids)) // 2)},
            "portfolio": {"sr_daily": _rd(lo["sr"]), "sr_ann": _rd(lo["sr"] * math.sqrt(PERIODS)),
                          "mdd_pct": _rd(100 * lo["mdd"])},
            "shrinkage": {"lw_delta_sleeves": _rd(delta_s), "lw_delta_clusters": _rd(delta_c)},
            "evidence_cross_section": {k: _rd(v) for k, v in evs.items()},
            "bets": {k: (_rd(v) if isinstance(v, float) else v) for k, v in bets.items()},
            "identical_fill_groups": fgroups, "exact_fill_groups": exact,
            "fill_pnl_conflicts": conflicts, "qqq_twins": qqq, "clusters": clus, "sleeves": rows}


def _rd(x, n=6):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) or math.isinf(x) else round(x, n)
