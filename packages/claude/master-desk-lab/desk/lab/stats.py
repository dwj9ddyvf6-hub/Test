"""Paired statistics for few sessions and many signals.

  paired(obs)   obs [(session, x)]: the signal-weighted mean of x, its day-clustered standard error (CR1:
                sqrt(G / (G - 1) * sum_g (sum_{i in g} (x_i - mean))^2) / n, G sessions: signals of one session share
                its market, so they are not independent) and a two-sided p on Student's t with G - 1 degrees of freedom
                (with few clusters the normal would overstate the evidence)
  qvalues(p)    Benjamini-Hochberg adjusted p-values: q <= 0.10 is exactly desk/learn/evidence.bh's rejection at 0.10
  shrink(est)   empirical Bayes toward the cross-sectional mean, as desk/learn/evidence.py: w = tau^2 / (tau^2 + se^2),
                tau^2 = max(0, Var(means) - mean(se^2))
  mde(se)       the minimum detectable effect at two-sided alpha 0.10 and power 0.8: (z_0.95 + z_0.80) x SE"""
import math
from statistics import NormalDist

_Z = NormalDist().inv_cdf(0.95) + NormalDist().inv_cdf(0.80)


def _cf(a, b, x):
    """the continued fraction of the incomplete beta function (modified Lentz)"""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)), -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def betainc(a, b, x):
    """the regularized incomplete beta function I_x(a, b)"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(ln) * _cf(a, b, x) / a
    return 1.0 - math.exp(ln) * _cf(b, a, 1.0 - x) / b


def t_sf(t, df):
    """P(T > t) for Student's t with df degrees of freedom"""
    p = 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))
    return p if t >= 0 else 1.0 - p


def paired(obs):
    """{n, sessions, mean, se, t, p} of obs [(session, x)]; se, t and p need two sessions"""
    xs = [x for _, x in obs]
    n = len(xs)
    days = {}
    for d, x in obs:
        days.setdefault(d, []).append(x)
    out = {"n": n, "sessions": len(days), "mean": round(sum(xs) / n, 4) if n else None, "se": None, "t": None,
           "p": None}
    g = len(days)
    if n < 2 or g < 2:
        return out
    mean = sum(xs) / n
    se = math.sqrt(g / (g - 1.0) * sum(sum(x - mean for x in v) ** 2 for v in days.values())) / n
    if se <= 1e-12:
        p, t = (1.0, None) if abs(mean) <= 1e-12 else (0.0, None)
    else:
        t = mean / se
        p = min(1.0, 2.0 * t_sf(abs(t), g - 1.0))
    out.update(se=round(se, 4), t=None if t is None else round(t, 3), p=round(p, 6))
    return out


def qvalues(pvals):
    """{key: p} -> {key: BH-adjusted q} (keys whose p is None are left out)"""
    items = sorted(((k, p) for k, p in pvals.items() if p is not None), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 1.0
    for i in range(m, 0, -1):
        k, p = items[i - 1]
        run = min(run, p * m / i)
        out[k] = round(run, 6)
    return out


def shrink(est):
    """{key: (mean, se^2)} -> ({key: shrunk mean}, tau^2, the cross-sectional mean)"""
    if not est:
        return {}, None, None
    ms = [m for m, _ in est.values()]
    m = sum(ms) / len(ms)
    var = sum((x - m) ** 2 for x in ms) / (len(ms) - 1) if len(ms) > 1 else 0.0
    tau2 = max(0.0, var - sum(s for _, s in est.values()) / len(est))
    out = {}
    for k, (mu, s2) in est.items():
        w = tau2 / (tau2 + s2) if tau2 + s2 > 0 else 0.0
        out[k] = round(m + w * (mu - m), 4)
    return out, round(tau2, 6), round(m, 4)


def mde(se):
    return None if se is None else round(_Z * se, 4)


def quantile(xs, q):
    """the q-quantile of xs (nearest rank, the smallest value with at least q of xs at or below it)"""
    s = sorted(xs)
    if not s:
        return None
    return s[min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))]


def median(xs):
    s = sorted(xs)
    if not s:
        return None
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0
