"""Per-name costs from the name's own daily bars (FACTORY.md §4 step 8, phase P2).

  spread_cs     Corwin & Schultz (2012) high-low spread estimator on the bar pair (t-1, t), point in time:
                  beta  = ln(H_{t-1}/L_{t-1})^2 + ln(H_t/L_t)^2
                  gamma = ln(max(H_{t-1}, H_t) / min(L_{t-1}, L_t))^2
                  alpha = (sqrt(2 beta) - sqrt(beta)) / (3 - 2 sqrt 2) - sqrt(gamma / (3 - 2 sqrt 2))
                  S     = 2 (e^alpha - 1) / (1 + e^alpha), negative estimates set to 0 (the paper's convention),
                averaged over the last CS_WINDOW pairs (t included)
  impact        square-root impact (Almgren et al. 2005; Toth et al. 2011): Y * sigma_d * sqrt(Q / ADV$), Y = 1,
                sigma_d the 20-session daily close-to-close volatility, Q the reference order (REF_ORDER_USD)
  per_side      CROSS x S / 2 + AUCTION + impact, capped at CAP: the half-spread is crossed (the desk's 2.3x
                simulated-vs-touch rule, X3), an auction fee of 2 bp (EQ-01), and the impact of the reference order.
                A round trip costs 2 x per_side.
Every input is known at the close of t."""
import numpy as np
import pandas as pd

CS_WINDOW = 20
CROSS = 2.3
AUCTION = 0.0002
REF_ORDER_USD = 10_000.0
Y = 1.0
CAP = 0.25
K = 3 - 2 * np.sqrt(2)


def spread_cs(h, l, window=CS_WINDOW):
    h, l = np.asarray(h, float), np.asarray(l, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        hl = np.log(h / l) ** 2
        beta = hl + np.r_[np.nan, hl[:-1]]
        hh = np.maximum(h, np.r_[np.nan, h[:-1]])
        ll = np.minimum(l, np.r_[np.nan, l[:-1]])
        gamma = np.log(hh / ll) ** 2
        alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / K - np.sqrt(gamma / K)
        s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    return pd.Series(s).rolling(window, min_periods=max(5, window // 2)).mean().to_numpy()


def impact(sigma_d, adv_usd, q=REF_ORDER_USD):
    sigma_d, adv_usd = np.asarray(sigma_d, float), np.asarray(adv_usd, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(adv_usd > 0, Y * sigma_d * np.sqrt(q / adv_usd), np.nan)


def per_side(h, l, c, dollar_volume):
    """-> (per-side cost fraction, dv20, sigma20) arrays for one name's bars"""
    c = np.asarray(c, float)
    s = spread_cs(h, l)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.r_[np.nan, c[1:] / c[:-1] - 1]
    sig = pd.Series(r).rolling(20, min_periods=10).std().to_numpy()
    dv20 = pd.Series(np.asarray(dollar_volume, float)).rolling(20, min_periods=10).mean().to_numpy()
    cost = CROSS * s / 2 + AUCTION + impact(sig, dv20)
    return np.minimum(cost, CAP), dv20, sig
