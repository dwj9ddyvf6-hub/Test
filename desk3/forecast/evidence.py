"""PORT-ADAPT (2026-10-27, ensemble port): local equivalent of Femto-lean
`desk/learn/evidence.py`, which has no muse-desk-v3 counterpart. Only the
three surfaces `desk3.forecast.ensemble` uses are provided, implementing
the published Bailey & Lopez de Prado formulas the source names:

  psr(sr, t, g3, g4, sr_star=0): Probabilistic Sharpe Ratio,
      PSR = Phi( (SR - SR*) * sqrt(T - 1) / sqrt(_q(SR, g3, g4)) )
      with _q = 1 - g3*SR + ((g4 - 1) / 4) * SR**2 the variance kernel
      (g3 = skewness, g4 = raw, non-excess, kurtosis).
  expected_max_sr(var, n): the expected maximum Sharpe over n trials,
      E[max] ~= sqrt(var) * ((1 - em) * Phi^-1(1 - 1/n)
                              + em * Phi^-1(1 - 1/(n*e))),
      em = Euler-Mascheroni constant (the DSR benchmark SR0).
  MIN_RETURNS = 20: FACTORY section 9's bar, the same value the source
  package states ("T_s >= 20 forward days before a label is more than
  provisional"; the source audit records the 7-session record's labels
  capped provisional against this bar).

Advisory only, like the rest of desk3/forecast: nothing in dispatch, any
sleeve, sizing, or order path imports this module (guarded by
tests/test_sleeve_ensemble_20261027_blockers.py).
"""
import math

from scipy.stats import norm

MIN_RETURNS = 20
_EULER_MASCHERONI = 0.5772156649015329


def _q(sr, g3, g4):
    """Variance kernel of the Sharpe estimator (Bailey & Lopez de Prado)."""
    return 1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * sr * sr


def psr(sr, t, g3, g4, sr_star=0.0):
    """Probabilistic Sharpe Ratio: P(true SR > sr_star) under the
    estimated SR's sampling distribution. None when undefined."""
    if sr is None or t is None or t < 2:
        return None
    q = _q(sr, g3, g4)
    if q <= 0:
        return None
    z = (sr - sr_star) * math.sqrt(t - 1) / math.sqrt(q)
    return float(norm.cdf(z))


def expected_max_sr(var, n):
    """Expected maximum Sharpe across n independent trials with
    cross-sectional Sharpe variance var (the DSR benchmark)."""
    if not n or n <= 1 or var is None or var <= 0:
        return 0.0
    sd = math.sqrt(var)
    z1 = float(norm.ppf(1.0 - 1.0 / n))
    z2 = float(norm.ppf(1.0 - 1.0 / (n * math.e)))
    return sd * ((1.0 - _EULER_MASCHERONI) * z1 + _EULER_MASCHERONI * z2)
