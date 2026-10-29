"""Statistical evidence for a forward record among ~550 sleeves tried at once: is a sleeve's Sharpe skill, or the luck
of the best of many? Evidence only — the graduation bar (scorecard.py) and its verdicts are the owner's and stay as
they are; this tells the person reading a PROPOSE whether luck has been excluded.

Per sleeve, on its daily returns (per-period Sharpe SR, T returns, skew g3, raw kurtosis g4):
  psr        PSR(0) = Phi((SR - 0) sqrt(T - 1) / sqrt(1 - g3 SR + (g4 - 1)/4 SR^2))  (Bailey & Lopez de Prado)
  dsr        PSR(SR0), SR0 = sqrt(V[SR_n]) ((1 - e) Phi^-1(1 - 1/N) + e Phi^-1(1 - 1/(N exp(1)))), e = 0.5772...:
             the Sharpe the best of N skill-less sleeves would show (N = sleeves with a record; V = their SR variance)
  min_trl    1 + (1 - g3 SR + (g4 - 1)/4 SR^2) (z_0.95 / SR)^2 returns: how long a record must be before SR > 0 is
             95% certain (None when SR <= 0)
  p          1 - PSR(0); bh: Benjamini-Hochberg at q = 0.10 across every sleeve with a record
  shrunk     empirical-Bayes Sharpe: m + w (SR - m), w = tau^2 / (tau^2 + se^2), se^2 = (1 - g3 SR + (g4-1)/4 SR^2)/T,
             tau^2 = max(0, Var(SR) - mean(se^2)), m = the cross-sectional mean (annualised by the book's own
             periods: x sqrt(252) for a US-session book, x sqrt(365) for one that trades every day)
  luck_excluded  T >= min_trl and dsr >= 0.95 and bh"""
import math
from statistics import NormalDist

EULER = 0.5772156649015329
Z95 = NormalDist().inv_cdf(0.95)
MIN_RETURNS = 20
Q_FDR = 0.10


def _phi(x):
    return NormalDist().cdf(x)


def _q(sr, g3, g4):
    return 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr * sr


def psr(sr, t, g3=0.0, g4=3.0, sr_star=0.0):
    q = _q(sr, g3, g4)
    if t < 2 or q <= 0:
        return None
    return _phi((sr - sr_star) * math.sqrt(t - 1) / math.sqrt(q))


def min_trl(sr, g3=0.0, g4=3.0, sr_star=0.0, z=Z95):
    if sr <= sr_star:
        return None
    return 1.0 + _q(sr, g3, g4) * (z / (sr - sr_star)) ** 2


def expected_max_sr(var_sr, n):
    if n < 2 or var_sr <= 0:
        return 0.0
    inv = NormalDist().inv_cdf
    return math.sqrt(var_sr) * ((1 - EULER) * inv(1 - 1.0 / n) + EULER * inv(1 - 1.0 / (n * math.e)))


def bh(pvals, q=Q_FDR):
    """{key: p} -> {key: rejected?} (Benjamini-Hochberg step-up)."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, k = len(items), 0
    for i, (_, p) in enumerate(items, 1):
        if p <= i * q / m:
            k = i
    return {key: i < k for i, (key, _) in enumerate(items)}


def assess(stats_by_sleeve):
    """stats_by_sleeve: {sid: attribution.sleeve_stats(...)} -> {sid: evidence} for every sleeve with a record of at
    least MIN_RETURNS daily returns and a non-zero deviation."""
    rec = {}
    for sid, s in stats_by_sleeve.items():
        if (s.get("ret_n") or 0) >= MIN_RETURNS and s.get("ret_sd"):
            rec[sid] = (s["ret_mean"] / s["ret_sd"], int(s["ret_n"]), float(s.get("ret_skew") or 0.0),
                        float(s.get("ret_kurt") or 3.0))
    periods = {sid: (252 if (stats_by_sleeve[sid].get("market") or "us") == "us" else 365) for sid in rec}
    if not rec:
        return {}
    srs = [v[0] for v in rec.values()]
    n = len(srs)
    mean_sr = sum(srs) / n
    var_sr = sum((x - mean_sr) ** 2 for x in srs) / (n - 1) if n > 1 else 0.0
    sr0 = expected_max_sr(var_sr, n)
    se2 = {sid: max(_q(sr, g3, g4), 1e-12) / t for sid, (sr, t, g3, g4) in rec.items()}
    tau2 = max(0.0, var_sr - sum(se2.values()) / n)
    pv = {sid: 1.0 - (psr(sr, t, g3, g4) or 0.0) for sid, (sr, t, g3, g4) in rec.items()}
    sig = bh(pv)
    out = {}
    for sid, (sr, t, g3, g4) in rec.items():
        w = tau2 / (tau2 + se2[sid]) if tau2 + se2[sid] > 0 else 0.0
        trl = min_trl(sr, g3, g4)
        d = psr(sr, t, g3, g4, sr_star=sr0)
        out[sid] = {"sharpe_daily": round(sr, 6), "returns": t, "psr": _r(psr(sr, t, g3, g4)), "dsr": _r(d),
                    "sr0_daily": round(sr0, 6), "trials": n, "min_trl_days": None if trl is None else round(trl, 1),
                    "p": round(pv[sid], 6), "bh": bool(sig.get(sid)),
                    "shrunk_sharpe_ann": round((mean_sr + w * (sr - mean_sr)) * math.sqrt(periods[sid]), 4),
                    "luck_excluded": bool(trl is not None and t >= trl and d is not None and d >= 0.95
                                          and sig.get(sid))}
    return out


def _r(x):
    return None if x is None else round(x, 6)
