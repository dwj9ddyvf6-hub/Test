"""The portfolio by breadth (FACTORY.md §7, BSF-09): many weak, unrelated edges, never one edge counted twice.

IR ~ IC x sqrt(BR_eff). Breadth is earned by independent bets, so a name is one bet however many promoted cells flag it
(the router keeps the cell with the best bound and lists the rest as supporting) and bets that move together are one
bet in the count. Nothing here places an order: it proposes risk budgets for the owner to approve.

  effective_bets(C)        participation ratio of the correlation matrix's eigenvalues, (sum l)^2 / sum l^2: N for N
                           independent bets, 1 for N identical ones
  shrink_corr(X)           Ledoit-Wolf shrinkage of the sample correlation of the series X (T x N) toward the identity
  risk_parity(cov, b)      weights w >= 0 (sum 1) whose risk contributions w_i (cov w)_i are the budget shares b_i
                           (equal budgets: risk parity), by cyclical coordinate descent
  allocate(proposals)      -> Allocation: for the BUY proposals, one bet per name; quality q_i = the cell's utility lower
                           bound over its volatility (times the grade factor); independence w = C^-1 q clipped at 0;
                           risk_i = R_UNIT x BR_eff x w_i, so three identical bets carry one bet's risk and N
                           independent ones carry N; capped per name, per sector and in total (desk/ai/gates CEILINGS,
                           which a limits file can only tighten); the portfolio's utility gain over the best single
                           bet at equal risk, with a block-bootstrap lower bound
AVOID / SELL / TRIM proposals take no risk: they are listed as vetoes."""
import math

import numpy as np

from . import cards as CD
from . import search as SR

GRADE_Q = {"A": 1.0, "B": 0.7, "P": 0.3}
BOOT = 2000
SEED = 1587
LB_Q = 0.05
SHRINK_MIN = 1e-6
EPS = 1e-9                      # a gain below a billionth of a unit is float noise, not a gain


def ceilings():
    from desk.ai import gates as AG
    return AG.limits()


def shrink_corr(X):
    """Ledoit-Wolf (2004) shrinkage of the sample covariance of the standardized series toward mI, returned as a
    correlation matrix; X is T x N with no missing values"""
    X = np.asarray(X, float)
    T, N = X.shape
    if N == 1:
        return np.ones((1, 1)), 0.0
    Z = (X - X.mean(0)) / np.where(X.std(0, ddof=0) > 0, X.std(0, ddof=0), 1.0)
    S = Z.T @ Z / T
    m = np.trace(S) / N
    d2 = float(((S - m * np.eye(N)) ** 2).sum() / N)
    b2 = 0.0
    for t in range(T):
        x = Z[t][:, None]
        b2 += float(((x @ x.T - S) ** 2).sum() / N)
    b2 = min(b2 / T ** 2, d2)
    delta = 0.0 if d2 <= 0 else b2 / d2
    C = delta * m * np.eye(N) + (1 - delta) * S
    d = np.sqrt(np.diag(C))
    return C / np.outer(d, d), float(delta)


def pairwise_corr(series, min_overlap=SR.MIN_DATES):
    """{key: (dates, values)} -> (keys, C, overlaps). Each pair is correlated on the dates both are active; a pair that
    shares fewer than min_overlap dates is never active together and is taken as uncorrelated (0). Each correlation is
    pulled toward 0 by T/(T+N) (a prior of N dates), and the matrix is repaired to positive semi-definite."""
    keys = list(series)
    N = len(keys)
    pos = {k: {d: i for i, d in enumerate(series[k][0])} for k in keys}
    C, O = np.eye(N), np.zeros((N, N), int)
    for i in range(N):
        for j in range(i + 1, N):
            com = sorted(set(pos[keys[i]]) & set(pos[keys[j]]))
            O[i, j] = O[j, i] = len(com)
            if len(com) < min_overlap:
                continue
            a = np.array([series[keys[i]][1][pos[keys[i]][d]] for d in com], float)
            b = np.array([series[keys[j]][1][pos[keys[j]][d]] for d in com], float)
            if a.std() > 0 and b.std() > 0:
                C[i, j] = C[j, i] = float(np.corrcoef(a, b)[0, 1]) * len(com) / (len(com) + N)
    lam, V = np.linalg.eigh(C)
    C = (V * np.clip(lam, 1e-6, None)) @ V.T
    d = np.sqrt(np.diag(C))
    return keys, C / np.outer(d, d), O


def effective_bets(C):
    lam = np.clip(np.linalg.eigvalsh(np.asarray(C, float)), 0, None)
    s2 = float((lam ** 2).sum())
    return 0.0 if s2 <= 0 else float(lam.sum() ** 2 / s2)


def risk_parity(cov, budgets=None, iters=500, tol=1e-12):
    cov = np.asarray(cov, float)
    n = cov.shape[0]
    b = np.full(n, 1.0 / n) if budgets is None else np.asarray(budgets, float) / np.sum(budgets)
    x = 1.0 / np.sqrt(np.diag(cov))
    for _ in range(iters):
        old = x.copy()
        for i in range(n):
            s_ii = cov[i, i]
            rest = float(cov[i] @ x - s_ii * x[i])
            x[i] = (-rest + math.sqrt(rest * rest + 4 * s_ii * b[i])) / (2 * s_ii)
        if np.max(np.abs(x - old)) < tol:
            break
    return x / x.sum()


def block_bootstrap_lb(d, block, q=LB_Q, B=BOOT, seed=SEED):
    """lower q-quantile of the mean of d under a moving-block bootstrap with blocks of `block` dates"""
    d = np.asarray(d, float)
    T = len(d)
    if T < 3:
        return None, None
    block = max(1, min(int(block), T))
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(T / block))
    starts = rng.integers(0, T - block + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :T]
    means = d[idx].mean(axis=1)
    return float(np.quantile(means, q)), means


def _aligned(series):
    """{key: (dates, values)} -> (common dates, matrix T x N) on the dates all of them hold"""
    common = None
    for dates, _ in series.values():
        common = set(dates) if common is None else common & set(dates)
    common = sorted(common or [])
    cols = []
    for dates, v in series.values():
        pos = {d: i for i, d in enumerate(dates)}
        cols.append([v[pos[d]] for d in common])
    return common, (np.array(cols, float).T if cols else np.zeros((0, 0)))


def allocate(proposals, book=None, as_of=None, boot=BOOT, seed=SEED):
    """proposals: router outputs. A BUY with a cell (and `book`, to read the cell's series) is a bet; every other
    label with a cell is a veto or an exit and takes no risk."""
    lim = ceilings()
    r_unit, cap_total = lim["risk_pct"], lim["max_open_risk_pct"]
    entries = {e["id"]: e for e in (book or {}).get("entries", [])}
    out = {"as_of": as_of, "items": [], "vetoes": [], "excluded": [], "caps_hit": [], "breadth_eff": 0.0,
           "n_bets": 0, "total_risk_pct": 0.0, "delta_u": None, "ir": None, "status": "ok", "reason": "",
           "propose_only": True, "ceilings": {"risk_pct": r_unit, "max_open_risk_pct": cap_total,
                                              "max_sector_names": lim["max_sector_names"]}}
    best = {}
    for p in proposals:
        lab, cell = p.get("label"), p.get("cell")
        if cell is None or lab in ("ABSTAIN", "WAIT", "HOLD"):
            continue
        if lab != "BUY":
            out["vetoes"].append({"sym": p["sym"], "label": lab, "cell": cell["id"], "lb": (p.get("du") or {}).get("lb")})
            continue
        e = entries.get(cell["id"])
        if e is None or not e["windows"]:
            out["excluded"].append({"sym": p["sym"], "why": "the cell's series is not in the book"})
            continue
        lb = (p.get("du") or {}).get("lb")
        if p["sym"] not in best or lb > best[p["sym"]][0]:                 # one bet per name, never a sum
            best[p["sym"]] = (lb, p, e)
    bets = []
    for sym, (lb, p, e) in sorted(best.items()):
        u = CD.utility(e["windows"][0], (p.get("cost") or {}).get("own_side"), 2)
        bets.append({"sym": sym, "p": p, "e": e, "lb": lb, "dates": e["windows"][0]["dates"], "u": u})
    # sector cap: at most max_sector_names per sector, best bounds first
    keep, seen = [], {}
    for b in sorted(bets, key=lambda b: -b["lb"]):
        sec = b["p"].get("sector")
        if sec is not None:
            seen[sec] = seen.get(sec, 0) + 1
            if seen[sec] > lim["max_sector_names"]:
                out["excluded"].append({"sym": b["sym"], "why": f"sector {sec}: already {lim['max_sector_names']} names"})
                out["caps_hit"].append("sector")
                continue
        keep.append(b)
    thin = [b for b in keep if len(b["dates"]) < SR.MIN_DATES]
    for b in thin:
        out["excluded"].append({"sym": b["sym"], "why": f"its cell has {len(b['dates'])} dates, {SR.MIN_DATES} needed"})
    bets = sorted((b for b in keep if len(b["dates"]) >= SR.MIN_DATES), key=lambda b: b["sym"])
    out["n_bets"] = len(bets)
    if not bets:
        out["reason"] = "no BUY proposal carries a bet"
        if thin:
            out.update(status="no_data", reason=f"the cell series hold fewer than {SR.MIN_DATES} dates")
        return out
    ser = {b["sym"]: (b["dates"], b["u"]) for b in bets}
    common, M = _aligned(ser)
    if len(common) >= SR.MIN_DATES:
        C, delta = shrink_corr(M)
        corr_how = "Ledoit-Wolf on the dates all bets share"
    else:
        _, C, ov = pairwise_corr(ser)
        delta, corr_how = None, "pairwise on the dates each pair shares (a pair that never co-occurs is uncorrelated)"
        # the portfolio's own series needs a common calendar: the union, a bet that is not active a day contributes 0
        dates = sorted({d for v in ser.values() for d in v[0]})
        pos = {d: i for i, d in enumerate(dates)}
        M = np.zeros((len(dates), len(bets)))
        for k, b in enumerate(bets):
            for d, x in zip(b["dates"], b["u"]):
                M[pos[d], k] = x
        common = dates
    sd = M.std(0, ddof=1)
    sd = np.where(sd > 0, sd, np.nan)
    q = np.array([max(b["lb"], 0.0) for b in bets]) / np.where(np.isfinite(sd), sd, np.inf)
    q = q * np.array([GRADE_Q.get(b["e"]["grade"], 0.0) for b in bets])
    br = effective_bets(C)
    try:
        w = np.linalg.solve(C + SHRINK_MIN * np.eye(len(bets)), q)
    except np.linalg.LinAlgError:
        w = q.copy()
    w = np.clip(w, 0, None)
    w = w / w.sum() if w.sum() > 0 else np.full(len(bets), 1.0 / len(bets))
    risk = r_unit * br * w
    capped = np.minimum(risk, r_unit)
    if (capped < risk - 1e-12).any():
        out["caps_hit"].append("per_name")
    if capped.sum() > cap_total + 1e-12:
        out["caps_hit"].append("total")
        capped = capped * cap_total / capped.sum()
    rp = risk_parity(C, w if w.sum() > 0 else None) if len(bets) > 1 else np.ones(1)
    for i, b in enumerate(bets):
        out["items"].append({"sym": b["sym"], "cell": b["p"]["cell"]["id"], "label": "BUY", "grade": b["e"]["grade"],
                             "n": b["p"]["cell"].get("n"), "base_rate": b["p"]["cell"].get("base_rate"),
                             "lift": b["p"]["cell"].get("lift"), "cost_side": (b["p"].get("cost") or {}).get("own_side"),
                             "lb": b["lb"], "q": float(q[i]), "independence": float(w[i]),
                             "risk_share": float(rp[i]), "risk_budget_pct": float(capped[i])})
    out.update(breadth_eff=float(br), total_risk_pct=float(capped.sum()), shrink=None if delta is None else float(delta),
               corr_method=corr_how, corr_dates=len(common), corr=[[round(float(x), 4) for x in r] for r in C])
    # the gain over the best single bet at the same volatility, with a block-bootstrap lower bound
    wp = capped / capped.sum() if capped.sum() > 0 else np.full(len(bets), 1.0 / len(bets))
    U = M @ wp
    j = int(np.nanargmax(np.where(np.isfinite(sd), M.mean(0) / sd, -np.inf)))
    s_p = float(U.std(ddof=1))
    alt = M[:, j] * (s_p / sd[j]) if np.isfinite(sd[j]) and sd[j] > 0 else np.zeros_like(U)
    d = U - alt
    h = max(b["e"]["h"] for b in bets)
    lbm, means = block_bootstrap_lb(d, h, B=boot, seed=seed)
    out["delta_u"] = {"mean": float(d.mean()), "lb": lbm, "q": LB_Q, "alt": f"best single bet ({bets[j]['sym']}) at equal risk",
                      "n_dates": len(common), "block": h, "boot": boot, "seed": seed, "positive": lbm is not None and lbm > EPS}
    per = 252.0 / h
    ir = float(U.mean() / s_p * math.sqrt(per)) if s_p > 0 else None
    _, irs = block_bootstrap_lb(U, h, B=boot, seed=seed)
    sdb = float(U.std(ddof=1))
    boots = None
    if irs is not None and sdb > 0:
        boots = np.quantile(irs / sdb * math.sqrt(per), [0.05, 0.95])
    out["ir"] = {"expected": ir, "lo": None if boots is None else float(boots[0]),
                 "hi": None if boots is None else float(boots[1]), "per_year": per}
    return out
