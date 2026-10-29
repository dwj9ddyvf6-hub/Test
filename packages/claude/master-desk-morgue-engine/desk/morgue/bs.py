"""Black-Scholes price, greeks and implied volatility (textbook math, explicit rate and dividend yield, no hidden
constants). The Map needs gamma under a spot shift for the zero-gamma grid; the rest serves the tape and tests.

gamma here equals desk/terminal/strip.bs_gamma at a zero dividend yield and the same rate (tests/test_morgue_map.py
pins the parity), so the strip and the Morgue Map are one gamma."""
import math

RATE = 0.045
_SQRT2 = math.sqrt(2.0)


def phi(x):
    """standard normal density"""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def d1(spot, strike, t_years, sigma, rate=RATE, div=0.0):
    return (math.log(spot / strike) + (rate - div + 0.5 * sigma * sigma) * t_years) / (sigma * math.sqrt(t_years))


def _ok(spot, strike, t_years, sigma):
    return spot > 0 and strike > 0 and sigma > 0 and t_years > 0


def gamma(spot, strike, t_years, sigma, rate=RATE, div=0.0):
    """gamma, the same for a call and a put; 0.0 for an input that is no contract"""
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    return math.exp(-div * t_years) * phi(d1(spot, strike, t_years, sigma, rate, div)) / (
        spot * sigma * math.sqrt(t_years))


def delta(spot, strike, t_years, sigma, is_call, rate=RATE, div=0.0):
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    n = ncdf(d1(spot, strike, t_years, sigma, rate, div))
    q = math.exp(-div * t_years)
    return q * n if is_call else q * (n - 1.0)


def vega(spot, strike, t_years, sigma, rate=RATE, div=0.0):
    """price change per 1.00 (100 points) of volatility; divide by 100 for per point"""
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    return spot * math.exp(-div * t_years) * phi(d1(spot, strike, t_years, sigma, rate, div)) * math.sqrt(t_years)


def price(spot, strike, t_years, sigma, is_call, rate=RATE, div=0.0):
    if t_years <= 0 or sigma <= 0:
        return max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    a = d1(spot, strike, t_years, sigma, rate, div)
    b = a - sigma * math.sqrt(t_years)
    q, df = math.exp(-div * t_years), math.exp(-rate * t_years)
    if is_call:
        return spot * q * ncdf(a) - strike * df * ncdf(b)
    return strike * df * ncdf(-b) - spot * q * ncdf(-a)


def theta(spot, strike, t_years, sigma, is_call, rate=RATE, div=0.0):
    """price change per year of calendar time (divide by 365 for per day)"""
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    a = d1(spot, strike, t_years, sigma, rate, div)
    b = a - sigma * math.sqrt(t_years)
    q, df = math.exp(-div * t_years), math.exp(-rate * t_years)
    first = -spot * q * phi(a) * sigma / (2.0 * math.sqrt(t_years))
    if is_call:
        return first - rate * strike * df * ncdf(b) + div * spot * q * ncdf(a)
    return first + rate * strike * df * ncdf(-b) - div * spot * q * ncdf(-a)


def implied_vol(target, spot, strike, t_years, is_call, rate=RATE, div=0.0, lo=1e-4, hi=5.0):
    """the volatility whose price equals `target`, by bisection; None when the price lies outside what any volatility
    in [lo, hi] can give (below intrinsic, above the bound): never a clipped guess"""
    if not _ok(spot, strike, t_years, 1.0) or target is None or target <= 0:
        return None
    f_lo, f_hi = price(spot, strike, t_years, lo, is_call, rate, div), price(spot, strike, t_years, hi, is_call, rate,
                                                                              div)
    if not f_lo - 1e-9 <= target <= f_hi + 1e-9:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if price(spot, strike, t_years, mid, is_call, rate, div) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def vanna(spot, strike, t_years, sigma, rate=RATE, div=0.0):
    """d delta / d sigma (per 1.00 of volatility), the same for a call and a put: -exp(-qT) phi(d1) d2 / sigma
    (Bullflow's VEX uses it; divide by 100 for a point of volatility)"""
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    a = d1(spot, strike, t_years, sigma, rate, div)
    b = a - sigma * math.sqrt(t_years)
    return -math.exp(-div * t_years) * phi(a) * b / sigma


def charm(spot, strike, t_years, sigma, is_call, rate=RATE, div=0.0):
    """delta decay: -d delta / d T, the change in delta per YEAR of time passing (divide by 365 for a day)"""
    if not _ok(spot, strike, t_years, sigma):
        return 0.0
    a = d1(spot, strike, t_years, sigma, rate, div)
    b = a - sigma * math.sqrt(t_years)
    q = math.exp(-div * t_years)
    root = sigma * math.sqrt(t_years)
    tail = q * phi(a) * (2.0 * (rate - div) * t_years - b * root) / (2.0 * t_years * root)
    return (div * q * ncdf(a) - tail) if is_call else (-div * q * ncdf(-a) - tail)
