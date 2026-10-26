"""Vectorized Black-Scholes-Merton pricing, greeks and implied-vol inversion (continuous dividend yield)."""

from __future__ import annotations

import numpy as np
from scipy.special import ndtr

SQRT_2PI = np.sqrt(2.0 * np.pi)


def _d1d2(S, K, T, r, q, sig):
    T = np.maximum(T, 1e-8)
    sig = np.maximum(sig, 1e-6)
    srt = sig * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig * sig) * T) / srt
    return d1, d1 - srt


def price(S, K, T, r, q, sig, is_call):
    S, K, T, r, q, sig = map(np.asarray, (S, K, T, r, q, sig))
    is_call = np.asarray(is_call, dtype=bool)
    d1, d2 = _d1d2(S, K, T, r, q, sig)
    dq, dr = np.exp(-q * T), np.exp(-r * T)
    call = S * dq * ndtr(d1) - K * dr * ndtr(d2)
    put = K * dr * ndtr(-d2) - S * dq * ndtr(-d1)
    out = np.where(is_call, call, put)
    expired = T <= 1e-8
    intrinsic = np.where(is_call, np.maximum(S - K, 0.0), np.maximum(K - S, 0.0))
    return np.where(expired, intrinsic, out)


def delta(S, K, T, r, q, sig, is_call):
    S, K, T, r, q, sig = map(np.asarray, (S, K, T, r, q, sig))
    d1, _ = _d1d2(S, K, T, r, q, sig)
    dq = np.exp(-q * np.maximum(T, 0))
    return np.where(np.asarray(is_call, dtype=bool), dq * ndtr(d1), dq * (ndtr(d1) - 1.0))


def vega(S, K, T, r, q, sig):
    S, K, T, r, q, sig = map(np.asarray, (S, K, T, r, q, sig))
    d1, _ = _d1d2(S, K, T, r, q, sig)
    return S * np.exp(-q * np.maximum(T, 0)) * np.exp(-0.5 * d1 * d1) / SQRT_2PI * np.sqrt(np.maximum(T, 1e-8))


def implied_vol(px, S, K, T, r, q, is_call, lo=0.01, hi=4.0, iters=60):
    """Bisection on the full arrays (robust; prices outside no-arbitrage bounds give NaN)."""
    px, S, K, T, r, q = map(lambda a: np.asarray(a, dtype=float), (px, S, K, T, r, q))
    is_call = np.asarray(is_call, dtype=bool)
    a = np.full(px.shape, lo)
    b = np.full(px.shape, hi)
    pa = price(S, K, T, r, q, a, is_call) - px
    pb = price(S, K, T, r, q, b, is_call) - px
    ok = (pa < 0) & (pb > 0)
    for _ in range(iters):
        m = 0.5 * (a + b)
        pm = price(S, K, T, r, q, m, is_call) - px
        left = pm > 0
        b = np.where(left, m, b)
        a = np.where(left, a, m)
    out = 0.5 * (a + b)
    return np.where(ok, out, np.nan)


def strike_for_delta(target_delta, S, T, r, q, sig, is_call):
    """Strike whose BS delta equals target_delta under volatility `sig` (scalar inputs)."""
    from scipy.stats import norm

    dq = np.exp(-q * T)
    if is_call:
        d1 = norm.ppf(np.clip(target_delta / dq, 1e-6, 1 - 1e-6))
    else:
        d1 = norm.ppf(np.clip(target_delta / dq + 1.0, 1e-6, 1 - 1e-6))
    return float(S * np.exp(-(d1 * sig * np.sqrt(T)) + (r - q + 0.5 * sig * sig) * T))
