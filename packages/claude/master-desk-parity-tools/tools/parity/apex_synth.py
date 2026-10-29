"""Deterministic randomized markets for the APEX parity harnesses: every symbol the APEX sleeves read, from its
real first date, in the source's daily-record shape {"dates", "open", "high", "low", "close", "volume",
"adj_close"}. A regime-switching equity factor (calm / normal / stress volatility and drift, jumps) drives the
Nasdaq-100, semis and the sectors; the 10-year yield and the T-bill rate are mean-reverting with persistent shocks;
the stock-bond and stock-gold correlations drift through both signs; the volatility indices follow realised
volatility with a stress-inverted term structure; Bitcoin trades every calendar day. Built only to exercise the
decision branches (gates, switches, crashes, correlation flips) — not a model of any market."""
import math
from datetime import date, timedelta

import numpy as np

from desk import calendar as cal

START, END = date(1985, 10, 1), date(2026, 10, 9)
FIRST = {"^NDX": "1985-10-01", "QQQ": "1999-03-10", "^IRX": "1985-10-01", "^TNX": "1985-10-01",
         "^VIX": "1990-01-02", "^VIX3M": "2006-07-17", "^VIX9D": "2011-01-03", "^VIX6M": "2008-01-02",
         "^VXN": "2001-01-23", "IEF": "2002-07-30", "SMH": "2000-06-05", "^SOX": "1994-05-04", "GLD": "2004-11-18",
         "USO": "2006-04-10", "UUP": "2007-03-01", "BTC-USD": "2014-09-17", "GC=F": "2000-08-30",
         "DX-Y.NYB": "1985-10-01", "TQQQ": "2010-02-11", "BIL": "2007-05-30",
         **{s: "1998-12-22" for s in ("XLK", "XLF", "XLE", "XLV", "XLP", "XLI", "XLB", "XLU", "XLY")}}


def _ar1(rng, n, phi, sd, lo=None, hi=None):
    x = np.zeros(n)
    e = rng.standard_normal(n) * sd
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
        if lo is not None:
            x[i] = min(max(x[i], lo), hi)
    return x


def _rec(dates, close, adj=None, opn=None):
    close = np.asarray(close, dtype=float)
    adj = close if adj is None else np.asarray(adj, dtype=float)
    opn = close if opn is None else np.asarray(opn, dtype=float)
    hi = np.maximum(opn, close) * 1.004
    lo = np.minimum(opn, close) * 0.996
    f = lambda a: [float(v) for v in a]  # noqa: E731
    return {"dates": [d.isoformat() for d in dates], "open": f(opn), "high": f(hi), "low": f(lo), "close": f(close),
            "volume": [1.0e6] * len(dates), "adj_close": f(adj)}


def market(seed):
    rng = np.random.default_rng(seed)
    days = []
    d = START
    while d <= END:
        if cal.is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    n = len(days)
    P = np.array([[0.996, 0.003, 0.001], [0.005, 0.989, 0.006], [0.003, 0.027, 0.970]])
    vol, mu = np.array([0.11, 0.19, 0.45]), np.array([0.17, 0.08, -0.35])
    reg = np.zeros(n, dtype=int)
    reg[0] = 1
    u = rng.random(n)
    for i in range(1, n):
        reg[i] = int(np.searchsorted(np.cumsum(P[reg[i - 1]]), u[i]))
        reg[i] = min(reg[i], 2)
    z = rng.standard_normal(n)
    jump = np.where(rng.random(n) < 0.002, rng.choice([-1.0, 1.0], n) * rng.uniform(0.04, 0.10, n), 0.0)
    f = mu[reg] / 252 + vol[reg] / math.sqrt(252) * z + jump
    rho_b = _ar1(rng, n, 0.998, 0.03, -0.6, 0.6)                    # the stock-bond correlation drifts
    rho_g = _ar1(rng, n, 0.998, 0.03, -0.6, 0.6)                    # the stock-gold correlation drifts
    # rates (percent)
    shock = _ar1(rng, n, 0.996, 0.004)
    y = np.zeros(n)
    y[0] = 9.5
    ey = rng.standard_normal(n)
    for i in range(1, n):
        y[i] = y[i - 1] + 0.0008 * (5.0 - y[i - 1]) + 0.055 * ey[i] - 0.04 * rho_b[i] * z[i] + shock[i]
        y[i] = min(max(y[i], 0.4), 16.0)
    irx = np.clip(y - 1.4 + _ar1(rng, n, 0.995, 0.03), 0.02, 14.0)
    # equities
    r_ndx = np.clip(1.2 * f + 0.06 / math.sqrt(252) * rng.standard_normal(n), -0.3, 0.3)
    semis_drift = _ar1(rng, n, 0.999, 0.0004)
    r_sox = np.clip(1.6 * f + 0.12 / math.sqrt(252) * rng.standard_normal(n) + semis_drift, -0.35, 0.35)
    out = {}

    def from_(sym):
        a = date.fromisoformat(FIRST[sym])
        i0 = next(i for i, dd in enumerate(days) if dd >= a)
        return i0

    def path(r, i0, p0):
        return p0 * np.cumprod(1.0 + r[i0:])

    def etf(sym, r, p0, div=0.0, on=None):
        i0 = from_(sym)
        adj = path(r, i0, p0)
        k = np.arange(n - i0)
        close = adj * (1.0 + div / 252) ** (k[-1] - k)               # dividends: the adjusted close sits below
        opn = None
        if on is not None:
            opn = np.concatenate([[close[0]], close[:-1] * (1.0 + on[i0 + 1:])])
        out[sym] = _rec(days[i0:], close, adj, opn)
        return adj

    ndx_px = path(r_ndx, 0, 400.0)
    out["^NDX"] = _rec(days, ndx_px)
    on = 0.4 * r_ndx + 0.002 * rng.standard_normal(n)
    etf("QQQ", r_ndx + 0.003 / 252 + 0.0004 * rng.standard_normal(n), ndx_px[from_("QQQ")] / 40.0, 0.006, on)
    i0 = from_("^SOX")
    out["^SOX"] = _rec(days[i0:], path(r_sox, i0, 250.0))
    etf("SMH", r_sox + 0.004 / 252 + 0.0005 * rng.standard_normal(n), 90.0, 0.006)
    for j, s in enumerate(("XLK", "XLF", "XLE", "XLV", "XLP", "XLI", "XLB", "XLU", "XLY")):
        beta = 0.55 + 0.1 * j
        r = np.clip(beta * f + 0.12 / math.sqrt(252) * rng.standard_normal(n) + _ar1(rng, n, 0.999, 0.0003), -0.3, 0.3)
        etf(s, r, 25.0 + 3 * j, 0.015)
    out["^TNX"] = _rec(days, y)
    out["^IRX"] = _rec(days, irx)
    dy = np.diff(np.concatenate([[y[0]], y]))
    r_ief = np.concatenate([[0.0], y[:-1]]) / 100 / 252 - 7.5 * dy / 100 + 0.0002 * rng.standard_normal(n)
    etf("IEF", r_ief, 80.0, 0.03)
    # volatility indices
    rv = np.sqrt(np.convolve(f ** 2, np.ones(21) / 21, mode="full")[:n] * 252)
    stress = np.clip((rv * 100 - 20.0) / 30.0, 0.0, 1.0)
    vix = np.clip(100 * (0.75 * rv + 0.25 * vol[reg] + 0.02) * np.exp(0.08 * rng.standard_normal(n)), 9.0, 90.0)
    for sym, mult in (("^VIX", lambda: 1.0), ("^VXN", lambda: 1.2 * np.exp(0.05 * rng.standard_normal(n))),
                      ("^VIX9D", lambda: np.exp(-0.06 + 0.2 * stress + 0.05 * rng.standard_normal(n))),
                      ("^VIX3M", lambda: np.exp(0.09 - 0.30 * stress + 0.04 * rng.standard_normal(n))),
                      ("^VIX6M", lambda: np.exp(0.14 - 0.40 * stress + 0.04 * rng.standard_normal(n)))):
        i0 = from_(sym)
        out[sym] = _rec(days[i0:], (vix * mult())[i0:])
    # gold, dollar, oil, bitcoin
    r_g = 0.16 / math.sqrt(252) * rng.standard_normal(n) + 0.012 * rho_g * z / math.sqrt(252) * 10 + \
        _ar1(rng, n, 0.999, 0.0003)
    i0 = from_("GC=F")
    out["GC=F"] = _rec(days[i0:], path(r_g, i0, 270.0))
    etf("GLD", r_g + 0.0004 * rng.standard_normal(n), 44.0)
    r_d = 0.08 / math.sqrt(252) * rng.standard_normal(n) + _ar1(rng, n, 0.999, 0.0002)
    out["DX-Y.NYB"] = _rec(days, path(r_d, 0, 120.0))
    etf("UUP", r_d + 0.0003 * rng.standard_normal(n), 23.0)
    etf("USO", 0.35 / math.sqrt(252) * rng.standard_normal(n) + 0.3 * f + _ar1(rng, n, 0.999, 0.0006), 70.0)
    etf("TQQQ", 3.0 * r_ndx - 0.0095 / 252, 0.5)
    etf("BIL", irx / 100 / 252, 91.5)
    bdays = []
    d = date.fromisoformat(FIRST["BTC-USD"])
    while d <= END:
        bdays.append(d)
        d += timedelta(days=1)
    rb = np.clip(0.75 / math.sqrt(365) * rng.standard_normal(len(bdays)) + _ar1(rng, len(bdays), 0.999, 0.0008), -0.4, 0.4)
    out["BTC-USD"] = _rec(bdays, 450.0 * np.cumprod(1.0 + rb))
    return out
