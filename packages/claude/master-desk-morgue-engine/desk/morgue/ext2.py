"""Morgue extensions, package vendor-forecast (2026-10-27): the rows the rea-flow package skipped (A69 A87 A63 A28 A55 CX-eg-1
CX-if-3 B175 A86 CX-mq-1 MG1) plus the rows LIC-02 reopened (V-vol-4, V-qc-3) and the bot rule sets of the paid crypto tooling
(C145-C151). Pure functions of their arguments: no I/O, no clock, no network. Each states its source row and what it
leaves to the caller.

  A69   price_american / greeks_american / rate_bucket   Bjerksund-Stensland (2002) with bumped greeks and the r buckets
  A87   svi_fit / svi_total_variance / wing_richness     raw SVI per expiry by least squares; a context only
  A63   flow_conv_div                                    net-premium slope vs price slope per bucket
  A28   gex_tape_signed                                  GEX with the dealer sign read from the day's signed prints
  A55   parent_orders                                    fragments of one order merged: BLOCK / SPLIT / SWEEP
  CX-eg-1 discover                                       every study outcome ranked by its Wilson bound, n >= 30
  CX-if-3 tape_trend, expiry_distribution                the two-week premium trend and the DTE shape
  B175  flip_verdict                                     the gamma flip with a 1% chain-mass floor and a no_flip verdict
  A86   snapshot_quality, iv_smoothness, smoothness_gate FlashAlpha's quality score and a spike gate
  CX-mq-1 walls_by_expiry                                Call Resistance / Put Support, all expiries and 0DTE, with HVL
  MG1   tape_scope                                       the Tape's scope over core, board and held names under one budget
  V-vol-4 vega_volga_profile                             vendor-convention MM vega and volga in $mm per vol point
  V-qc-3  em_straddle                                    expected move = 1.25 x the ATM straddle
  C145-C151 grid_bot, dca_bot, pair_bot                  the WunderTrading bots' rules as deterministic simulators
  CX-tr-1 min_variance_weights, max_sharpe_weights, eigen_portfolios   Eiten's portfolio constructors"""
import math

import numpy as np

from . import bs

# ---------------------------------------------------------------- A69 Bjerksund-Stensland 2002
_BV = {}


def _bvn(x, y, rho):
    """P(X <= x, Y <= y) for a standard bivariate normal with correlation rho"""
    from scipy.stats import multivariate_normal
    key = round(rho, 12)
    if key not in _BV:
        _BV[key] = multivariate_normal(mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]], allow_singular=False)
    if x == -math.inf or y == -math.inf:
        return 0.0
    if x == math.inf:
        return bs.ncdf(y)
    if y == math.inf:
        return bs.ncdf(x)
    return float(_BV[key].cdf([x, y]))


def _phi(S, T, gam, H, I, r, b, v):
    lam = (-r + gam * b + 0.5 * gam * (gam - 1.0) * v * v) * T
    sq = v * math.sqrt(T)
    d = -(math.log(S / H) + (b + (gam - 0.5) * v * v) * T) / sq
    kap = 2.0 * b / (v * v) + (2.0 * gam - 1.0)
    return math.exp(lam) * S ** gam * (bs.ncdf(d) - (I / S) ** kap * bs.ncdf(d - 2.0 * math.log(I / S) / sq))


def _psi(S, T, gam, H, I2, I1, t1, r, b, v):
    sq1, sq = v * math.sqrt(t1), v * math.sqrt(T)
    e1 = (math.log(S / I1) + (b + (gam - 0.5) * v * v) * t1) / sq1
    e2 = (math.log(I2 * I2 / (S * I1)) + (b + (gam - 0.5) * v * v) * t1) / sq1
    e3 = (math.log(S / I1) - (b + (gam - 0.5) * v * v) * t1) / sq1
    e4 = (math.log(I2 * I2 / (S * I1)) - (b + (gam - 0.5) * v * v) * t1) / sq1
    mu = (b + (gam - 0.5) * v * v) * T
    f1 = (math.log(S / H) + mu) / sq
    f2 = (math.log(I2 * I2 / (S * H)) + mu) / sq
    f3 = (math.log(I1 * I1 / (S * H)) + mu) / sq
    f4 = (math.log(S * I1 * I1 / (H * I2 * I2)) + mu) / sq
    rho = math.sqrt(t1 / T)
    lam = -r + gam * b + 0.5 * gam * (gam - 1.0) * v * v
    kap = 2.0 * b / (v * v) + (2.0 * gam - 1.0)
    return math.exp(lam * T) * S ** gam * (_bvn(-e1, -f1, rho) - (I2 / S) ** kap * _bvn(-e2, -f2, rho)
                                           - (I1 / S) ** kap * _bvn(-e3, -f3, -rho)
                                           + (I1 / I2) ** kap * _bvn(-e4, -f4, -rho))


def _bs02_call(S, X, T, r, b, v):
    if b >= r:                                   # an American call is never exercised early: Black-Scholes-Merton
        return _gbsm(S, X, T, r, b, v, True)
    beta = (0.5 - b / (v * v)) + math.sqrt((b / (v * v) - 0.5) ** 2 + 2.0 * r / (v * v))
    b_inf = beta / (beta - 1.0) * X
    b0 = max(X, r / (r - b) * X)
    t1 = 0.5 * (math.sqrt(5.0) - 1.0) * T

    def h(t):
        return -(b * t + 2.0 * v * math.sqrt(t)) * X * X / ((b_inf - b0) * b0)
    i1 = b0 + (b_inf - b0) * (1.0 - math.exp(h(t1)))
    i2 = b0 + (b_inf - b0) * (1.0 - math.exp(h(T)))
    if S >= i2:
        return S - X
    a1 = (i1 - X) * i1 ** -beta
    a2 = (i2 - X) * i2 ** -beta
    return (a2 * S ** beta - a2 * _phi(S, t1, beta, i2, i2, r, b, v) + _phi(S, t1, 1.0, i2, i2, r, b, v)
            - _phi(S, t1, 1.0, i1, i2, r, b, v) - X * _phi(S, t1, 0.0, i2, i2, r, b, v)
            + X * _phi(S, t1, 0.0, i1, i2, r, b, v) + a1 * _phi(S, t1, beta, i1, i2, r, b, v)
            - a1 * _psi(S, T, beta, i1, i2, i1, t1, r, b, v) + _psi(S, T, 1.0, i1, i2, i1, t1, r, b, v)
            - _psi(S, T, 1.0, X, i2, i1, t1, r, b, v) - X * _psi(S, T, 0.0, i1, i2, i1, t1, r, b, v)
            + X * _psi(S, T, 0.0, X, i2, i1, t1, r, b, v))


def _gbsm(S, X, T, r, b, v, is_call):
    d1 = (math.log(S / X) + (b + 0.5 * v * v) * T) / (v * math.sqrt(T))
    d2 = d1 - v * math.sqrt(T)
    if is_call:
        return S * math.exp((b - r) * T) * bs.ncdf(d1) - X * math.exp(-r * T) * bs.ncdf(d2)
    return X * math.exp(-r * T) * bs.ncdf(-d2) - S * math.exp((b - r) * T) * bs.ncdf(-d1)


def price_american(spot, strike, t_years, sigma, is_call, rate=bs.RATE, div=0.0):
    """Bjerksund-Stensland (2002) American option value, cost of carry b = rate - div. The put is the call on the mirrored
    problem: P(S, X, T, r, b, v) = C(X, S, T, r - b, -b, v). None for a non-positive input. Bounded below by intrinsic."""
    if not (spot > 0 and strike > 0 and t_years > 0 and sigma > 0):
        return None
    b = rate - div
    if is_call:
        v = _bs02_call(spot, strike, t_years, rate, b, sigma)
    else:
        v = _bs02_call(strike, spot, t_years, rate - b, -b, sigma)
    intrinsic = max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    return max(v, intrinsic)


def rate_bucket(t_years, curve):
    """the r of the shortest bucket (1m 3m 6m 1y 2y: {label: rate}) that covers t_years, else the longest"""
    order = (("1m", 1 / 12), ("3m", 0.25), ("6m", 0.5), ("1y", 1.0), ("2y", 2.0))
    have = [(lb, yrs) for lb, yrs in order if lb in curve and curve[lb] is not None]
    if not have:
        return None
    for lb, yrs in have:
        if t_years <= yrs:
            return curve[lb]
    return curve[have[-1][0]]


def greeks_american(spot, strike, t_years, sigma, is_call, rate=bs.RATE, div=0.0, ds=0.01, dv=0.01, dt=1 / 365):
    """finite-difference greeks of price_american: delta and gamma by a +-ds relative spot bump, vega per 1.00 of sigma by a
    +-dv bump, theta per year as the one-day roll (negative when time costs). A70's bump recipe"""
    def p(s=spot, v=sigma, t=t_years):
        return price_american(s, strike, t, v, is_call, rate, div)
    up, dn, mid = p(spot * (1 + ds)), p(spot * (1 - ds)), p()
    if None in (up, dn, mid):
        return None
    h = spot * ds
    vega = (p(v=sigma + dv) - p(v=max(sigma - dv, 1e-4))) / (sigma + dv - max(sigma - dv, 1e-4))
    th = (p(t=t_years - dt) - mid) / dt if t_years > dt else None
    return {"price": mid, "delta": (up - dn) / (2 * h), "gamma": (up - 2 * mid + dn) / (h * h), "vega": vega, "theta": th}


# ---------------------------------------------------------------- A87 raw SVI
def svi_total_variance(k, a, b, rho, m, sig):
    k = np.asarray(k, float)
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sig * sig))


def svi_fit(k, w, starts=None):
    """raw SVI (a, b, rho, m, sigma) of one expiry's total variance w = iv^2 t over log-moneyness k, by bounded least
    squares from several starts. Returns {"params", "rmse", "n"} or None under 5 points. b >= 0, |rho| < 1, sigma > 0"""
    from scipy.optimize import least_squares
    k, w = np.asarray(k, float), np.asarray(w, float)
    ok = np.isfinite(k) & np.isfinite(w) & (w > 0)
    k, w = k[ok], w[ok]
    if len(k) < 5:
        return None
    span = max(float(k.max() - k.min()), 1e-3)
    lo = [-abs(w).max(), 0.0, -0.999, k.min() - span, 1e-4]
    hi = [abs(w).max() * 2, 10.0, 0.999, k.max() + span, 5.0]
    best = None
    ss = starts or [(w.min() * 0.5, 0.1, -0.5, 0.0, 0.1), (w.min() * 0.8, 0.3, 0.0, float(k.mean()), 0.3),
                    (w.min() * 0.2, 0.05, 0.5, float(np.median(k)), 0.05), (w.mean() * 0.5, 0.5, -0.8, 0.0, 0.5)]
    for x0 in ss:
        x0 = np.clip(x0, np.array(lo) + 1e-9, np.array(hi) - 1e-9)
        r = least_squares(lambda p: svi_total_variance(k, *p) - w, x0, bounds=(lo, hi), xtol=1e-14, ftol=1e-14, gtol=1e-14,
                          max_nfev=4000)
        if best is None or r.cost < best.cost:
            best = r
    return {"params": tuple(float(x) for x in best.x), "rmse": float(math.sqrt(2 * best.cost / len(k))), "n": int(len(k))}


def wing_richness(params, wing=0.2):
    """mean total variance at k = +-wing over the at-the-money one (k = 0): above 1 the wings are rich. The wing distance
    is the desk's choice (the vendor withholds its constants); a context, never a trade signal"""
    atm = float(svi_total_variance([0.0], *params)[0])
    w = svi_total_variance([-wing, wing], *params)
    return float(w.mean() / atm) if atm > 0 else None


# ---------------------------------------------------------------- A63 flow momentum / convergence
def flow_conv_div(drift, bars, lookback=3):
    """per bucket (flow.net_drift rows with "t" and "net_premium_usd") against the price bars {"t","c"} on the same bucket
    starts: slope of the last `lookback` net premiums vs slope of the last `lookback` closes. +1 convergence (both rising or
    both falling), -1 divergence (opposite), 0 when either is flat or short. Returns [{"t","flow_slope","price_slope","state"}]"""
    px = {b["t"]: b["c"] for b in bars}
    rows, ts = [], []
    for d in drift:
        if d["t"] in px:
            ts.append((d["t"], d["net_premium_usd"], px[d["t"]]))
    out = []
    for i, (t, _, _) in enumerate(ts):
        if i + 1 < lookback:
            continue
        w = ts[i + 1 - lookback:i + 1]
        fs = (w[-1][1] - w[0][1]) / (lookback - 1)
        ps = (w[-1][2] - w[0][2]) / (lookback - 1)
        st = 0 if fs == 0 or ps == 0 else (1 if (fs > 0) == (ps > 0) else -1)
        out.append({"t": t, "flow_slope": fs, "price_slope": ps, "state": st})
    return out


# ---------------------------------------------------------------- A28 tape-signed GEX
def gex_tape_signed(rows, spot, prints):
    """GEX with the dealer sign read from the tape. rows: opt_ext.rows_of rows (gamma, oi, strike, is_call, symbol); prints:
    flow.signed_print dicts ("contract", "raw_side" +1 ask / -1 bid, "size"). A contract's customer flow is the sum of
    raw_side x size; dealers took the other side, so the dealer sign is -sign(customer flow). A contract with no signed print
    keeps the convention (calls +, puts -). Returns the tape-signed and convention by-strike dollar gamma per 1% move, their
    totals, and the disagreement: strikes whose sign differs, and the share of absolute gamma they carry."""
    flow = {}
    for p in prints:
        flow[p["contract"]] = flow.get(p["contract"], 0.0) + p["raw_side"] * p["size"]
    tape_by, conv_by, tape_n, mass, dis_mass = {}, {}, 0, 0.0, 0.0
    for r in rows:
        mag = abs(r["gamma"]) * r["oi"] * 100.0 * spot * spot * 0.01
        conv = mag if r["is_call"] else -mag
        f = flow.get(r["symbol"], 0.0)
        sgn = -1.0 if f > 0 else (1.0 if f < 0 else None)
        tape = conv if sgn is None else sgn * mag
        tape_n += sgn is not None
        k = r["strike"]
        tape_by[k] = tape_by.get(k, 0.0) + tape
        conv_by[k] = conv_by.get(k, 0.0) + conv
        mass += mag
        if (tape > 0) != (conv > 0) and mag > 0:
            dis_mass += mag
    differ = [k for k in conv_by if (tape_by[k] > 0) != (conv_by[k] > 0)]
    return {"tape_by_strike": tape_by, "convention_by_strike": conv_by, "tape_net": sum(tape_by.values()),
            "convention_net": sum(conv_by.values()), "contracts_tape_signed": tape_n, "contracts": len(rows),
            "strikes_disagree": sorted(differ), "disagree_mass_share": (dis_mass / mass) if mass else None}


# ---------------------------------------------------------------- A55 consolidation grammar
def parent_orders(prints, gap_s=1.0, block_min=500):
    """merge the fragments of one order: the same contract, the same exchange (the print's "x", "" when absent) and each fragment
    within `gap_s` seconds of the last. A parent carries total size and premium, the fragment count, the first and last time and
    a label: BLOCK a single print of at least `block_min` contracts, SPLIT several fragments on one exchange, SWEEP fragments
    that walked more than one exchange (merged across exchanges inside the same window). The window and the block size are the
    desk's (the vendor seals them). Input ascending by "t"; prints are never mutated."""
    out, open_ = [], {}
    for p in sorted(prints, key=lambda q: q["t"]):
        c = p["contract"]
        cur = open_.get(c)
        if cur is not None and p["t"] - cur["t1"] <= gap_s:
            cur["size"] += p["size"]
            cur["premium"] += p["premium"]
            cur["n"] += 1
            cur["t1"] = p["t"]
            cur["x"].add(p.get("x", ""))
            continue
        cur = {"contract": c, "t0": p["t"], "t1": p["t"], "size": p["size"], "premium": p["premium"], "n": 1,
               "x": {p.get("x", "")}, "side": p.get("side")}
        open_[c] = cur
        out.append(cur)
    for o in out:
        o["exchanges"] = len(o.pop("x"))
        o["label"] = ("SWEEP" if o["exchanges"] > 1 else "SPLIT" if o["n"] > 1 else
                      "BLOCK" if o["size"] >= block_min else "SINGLE")
    return out


# ---------------------------------------------------------------- CX-eg-1 discovery scan
def wilson_lower(hits, n, z=1.96):
    if n <= 0:
        return None
    p = hits / n
    den = 1 + z * z / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den


def discover(studies, min_n=30):
    """every measured yes/no outcome of the studies card ({"gap_fill": gap_fill_study, "orb": orb_ib_study, "earnings":
    earnings_stats}) as {"name","n","hits","rate","wilson_lower"}, best Wilson bound first, those under `min_n` apart
    (counted, never ranked)."""
    rows = []
    g = studies.get("gap_fill") or {}
    if g.get("state") == "graded":
        rows.append(("gap fill (all)", g["n"], g["fills"]))
        for part, label in (("by_band", "gap fill "), ("by_weekday", "gap fill ")):
            for k, c in (g.get("partitions", {}).get(part) or {}).items():
                rows.append((label + k, c["n"], c["fills"]))
    for w, o in (studies.get("orb") or {}).items():
        if o.get("state") == "graded":
            rows.append((f"opening range {w}m breaks one side", o["n"], o["break_one_side"]))
            rows.append((f"opening range {w}m holds (no break)", o["n"], o["no_break"]))
    e = studies.get("earnings") or {}
    if e.get("state") == "graded":
        rows.append(("earnings move positive", e["n"], round(e["share_positive"] * e["n"])))
    ranked, under = [], 0
    for name, n, hits in rows:
        if n < min_n:
            under += 1
            continue
        ranked.append({"name": name, "n": n, "hits": hits, "rate": hits / n, "wilson_lower": wilson_lower(hits, n)})
    ranked.sort(key=lambda r: -r["wilson_lower"])
    return {"ranked": ranked, "under_floor": under, "min_n": min_n}


# ---------------------------------------------------------------- CX-if-3 two-week trend
DTE_EDGES = (("0d", 0, 0), ("1-7d", 1, 7), ("8-35d", 8, 35), ("36-98d", 36, 98), (">98d", 99, 10 ** 6))


def expiry_distribution(prints, today):
    """premium share by days to expiry (the Heat Score's own DTE tiers): flow.signed_print dicts with "expiry" and "premium"
    against `today` (a date). Returns {bucket: share} or {} with no premium"""
    from datetime import date
    tot, by = 0.0, {b[0]: 0.0 for b in DTE_EDGES}
    for p in prints:
        d = (date.fromisoformat(p["expiry"]) - today).days
        for name, lo, hi in DTE_EDGES:
            if lo <= d <= hi:
                by[name] += p["premium"]
                tot += p["premium"]
                break
    return {k: v / tot for k, v in by.items()} if tot > 0 else {}


def tape_trend(rows, symbol, sessions=10):
    """the last `sessions` stored tape cards of `symbol` ({"session","symbol","total_premium_usd","net_premium_usd"}) ascending,
    with the ordinary least squares slope per session of each series and the latest over the mean of the earlier ones.
    None with fewer than 3 sessions."""
    mine = sorted((r for r in rows if r.get("symbol") == symbol and r.get("total_premium_usd") is not None),
                  key=lambda r: r["session"])[-sessions:]
    if len(mine) < 3:
        return None

    def slope(y):
        x = np.arange(len(y), dtype=float)
        x -= x.mean()
        return float((x * (np.asarray(y, float) - np.mean(y))).sum() / (x * x).sum())
    tot = [r["total_premium_usd"] for r in mine]
    net = [r["net_premium_usd"] for r in mine]
    base = float(np.mean(tot[:-1]))
    return {"symbol": symbol, "sessions": [r["session"] for r in mine], "total": tot, "net": net,
            "total_slope": slope(tot), "net_slope": slope(net), "latest_vs_prior_mean": (tot[-1] / base) if base else None}


# ---------------------------------------------------------------- B175 gamma flip with a mass floor
def flip_verdict(by_strike, floor=0.01):
    """OptionScout's flip: the price where the cumulative gamma over ascending strikes crosses zero, linearly interpolated
    between strikes, and shown only if at least `floor` (1%) of the chain's absolute gamma lies on each side of it (gex-tools.txt:1
    via optionscout.md:45). Otherwise the verdict is no_flip with the reason. {"verdict": "flip"|"no_flip", "flip", "reason"}"""
    ks = sorted(by_strike)
    tot = sum(abs(by_strike[k]) for k in ks)
    if len(ks) < 2 or tot <= 0:
        return {"verdict": "no_flip", "flip": None, "reason": "no chain mass"}
    cum, prev = 0.0, None
    cross = None
    for k in ks:
        cum_prev = cum
        cum += by_strike[k]
        if prev is not None and cum_prev != 0 and (cum_prev < 0) != (cum < 0):
            cross = prev + (k - prev) * abs(cum_prev) / (abs(cum_prev) + abs(cum))
            break
        if cum == 0 and prev is not None:
            cross = k
            break
        prev = k
    if cross is None:
        return {"verdict": "no_flip", "flip": None, "reason": "cumulative gamma never changes sign"}
    below = sum(abs(by_strike[k]) for k in ks if k < cross)
    above = sum(abs(by_strike[k]) for k in ks if k > cross)
    if below < floor * tot or above < floor * tot:
        return {"verdict": "no_flip", "flip": None, "reason": f"under {floor:.0%} of the chain mass on one side"}
    return {"verdict": "flip", "flip": cross, "reason": ""}


def grid_no_flip(grid, k=0.01):
    """FINDINGS_NEW #8: no_flip when |net gamma| < k x the total absolute gamma at every grid point. grid: [(spot, net,
    total_abs)]"""
    return all(abs(net) < k * tot for _, net, tot in grid if tot > 0)


# ---------------------------------------------------------------- A86 snapshot quality
def snapshot_quality(rows, age_s):
    """FlashAlpha's quality = 0.4 x valid-IV share + 0.4 x valid delta/gamma share + 0.2 x freshness (linear to 0 over 300 s),
    0..1. rows: dicts with "iv", "gamma" (and optional "delta"). Valid: finite and positive iv; finite gamma"""
    n = len(rows)
    if not n:
        return None
    iv = sum(1 for r in rows if r.get("iv") and math.isfinite(r["iv"]) and r["iv"] > 0) / n
    gd = sum(1 for r in rows if r.get("gamma") is not None and math.isfinite(r["gamma"])
             and (r.get("delta") is None or math.isfinite(r["delta"]))) / n
    fresh = max(0.0, 1.0 - age_s / 300.0)
    return 0.4 * iv + 0.4 * gd + 0.2 * fresh


def iv_smoothness(strike_iv):
    """100 x exp(-mean adjacent-strike IV jump / 0.02) over the ascending strikes ({strike: iv}); 100 is a flat smile"""
    ks = sorted(strike_iv)
    if len(ks) < 2:
        return None
    jumps = [abs(strike_iv[b] - strike_iv[a]) for a, b in zip(ks, ks[1:])]
    return 100.0 * math.exp(-(sum(jumps) / len(jumps)) / 0.02)


def smoothness_gate(strike_gamma, k=6.0):
    """the A86 gate: stale when an adjacent-strike gamma jump exceeds k median absolute deviations of all the jumps.
    Returns {"status": "ok"|"stale", "strikes": [the strikes after a spike]}"""
    ks = sorted(strike_gamma)
    j = np.array([strike_gamma[b] - strike_gamma[a] for a, b in zip(ks, ks[1:])], float)
    if len(j) < 4:
        return {"status": "ok", "strikes": []}
    med = np.median(j)
    mad = np.median(np.abs(j - med))
    if mad == 0:
        mad = np.mean(np.abs(j - med))
    bad = [ks[i + 1] for i in range(len(j)) if mad > 0 and abs(j[i] - med) > k * mad]
    return {"status": "stale" if bad else "ok", "strikes": bad}


# ---------------------------------------------------------------- CX-mq-1 walls by expiry
def walls_by_expiry(rows, today, max_days=0):
    """MenthorQ's levels. Call Resistance = the strike with the highest net call gamma across expiries (sum of call
    gamma x OI dollar gamma), Put Support = the same for puts; the 0DTE set is the expiries within `max_days` of `today`
    (0 = the day's own, 1 = within 24 hours). rows: opt_ext rows (gamma, oi, strike, is_call, expiry, spot via "spot"
    argument-free: dollar gamma uses gamma x oi x 100 per 1.00 of spot, ranking only). Returns both sets side by side."""
    from datetime import date

    def levels(rs):
        call, put = {}, {}
        for r in rs:
            v = abs(r["gamma"]) * r["oi"] * 100.0
            tgt = call if r["is_call"] else put
            tgt[r["strike"]] = tgt.get(r["strike"], 0.0) + v
        return {"call_resistance": max(call, key=call.get) if call else None,
                "put_support": max(put, key=put.get) if put else None, "contracts": len(rs)}
    near = [r for r in rows if (date.fromisoformat(r["expiry"]) - today).days <= max_days]
    return {"all_expiries": levels(rows), "zero_dte": levels(near), "max_days": max_days}


# ---------------------------------------------------------------- MG1 tape scope
def tape_scope(core, board, held, max_names):
    """the Tape's names under one page budget: the three funds first, then held names, then the board in rank order, each once,
    at most `max_names`. Returns {"names": [...], "dropped": [...]} so the cut is counted, never hidden. Wiring this into
    tape_card's cycle is the caller's change (tape_card.py and cycle.py belong to the terminal stream)"""
    seen, names, dropped = set(), [], []
    for n in list(core) + list(held) + list(board):
        if n in seen:
            continue
        seen.add(n)
        (names if len(names) < max_names else dropped).append(n)
    return {"names": names, "dropped": dropped}


# ---------------------------------------------------------------- V-vol-4 vega and volga
def vega_volga_profile(rows, spot, call_sign=1.0):
    """market-maker vega and volga in $mm per vol point from the chain: per contract vega = bs.vega (per 1.00 of sigma) and volga
    = vega x d1 x d2 / sigma, times OI x 100 x 0.01 / 1e6. The sign is the Map's convention (dealers long calls `call_sign`,
    short puts -call_sign); the vendor's category signing needs the paid Cboe Open-Close file. rows: iv, t, strike, is_call, oi, div"""
    vega = volga = 0.0
    used = 0
    for r in rows:
        iv, t = r.get("iv"), r.get("t")
        if not iv or iv <= 0 or not t or t <= 0:
            continue
        d1 = bs.d1(spot, r["strike"], t, iv, bs.RATE, r.get("div", 0.0))
        d2 = d1 - iv * math.sqrt(t)
        v = bs.vega(spot, r["strike"], t, iv, bs.RATE, r.get("div", 0.0))
        sg = call_sign if r["is_call"] else -call_sign
        vega += sg * v * r["oi"] * 100.0 * 0.01 / 1e6
        volga += sg * v * d1 * d2 / iv * r["oi"] * 100.0 * 0.01 / 1e6
        used += 1
    return {"vega_mm_per_volpt": vega, "volga_mm_per_volpt": volga, "contracts_used": used}


# ---------------------------------------------------------------- V-qc-3 expected move from the straddle
def em_straddle(rows, spot, factor=1.25):
    """QANTRADING's expected move = 1.25 x the at-the-money straddle of the nearest expiry with an IV: (Black-Scholes call +
    put at the strike nearest the spot) x factor, as dollars and as a share of the spot. None without an IV"""
    live = [r for r in rows if r.get("iv") and r["iv"] > 0 and r.get("t") and r["t"] > 0]
    if not live:
        return None
    t = min(r["t"] for r in live)
    near = [r for r in live if r["t"] == t]
    k = min({r["strike"] for r in near}, key=lambda s: abs(s - spot))
    ivs = [r["iv"] for r in near if r["strike"] == k]
    iv = sum(ivs) / len(ivs)
    div = near[0].get("div", 0.0)
    st = bs.price(spot, k, t, iv, True, bs.RATE, div) + bs.price(spot, k, t, iv, False, bs.RATE, div)
    return {"straddle": st, "em_usd": factor * st, "em_pct": factor * st / spot * 100.0, "strike": k, "t_years": t}


# ---------------------------------------------------------------- C145-C151: the bot rule sets as simulators
def grid_bot(closes, lower, upper, n_grids, invest, fee=0.0):
    """WunderTrading's grid bot on a close series: n_grids equal levels between lower and upper; hold one lot per level below the
    price, buy a lot when the price falls through a level, sell it one level higher when the price rises through it. Returns
    {"profit", "trades", "open_lots", "equity"} marked to the last close. The lot is invest / n_grids in quote currency."""
    levels = np.linspace(lower, upper, n_grids + 1)
    lot = invest / n_grids
    cash, qty_by, trades = 0.0, {}, 0
    prev = closes[0]
    for c in closes[1:]:
        for i, lv in enumerate(levels[:-1]):
            if prev > lv >= c and i not in qty_by:                               # fell through level i: buy a lot
                qty_by[i] = lot / lv
                cash -= lot * (1 + fee)
                trades += 1
        for i in sorted(list(qty_by)):
            up = levels[i + 1]
            if prev < up <= c:                                                   # rose through the next level: sell
                cash += qty_by.pop(i) * up * (1 - fee)
                trades += 1
        prev = c
    mark = sum(q * closes[-1] for q in qty_by.values())
    return {"profit": cash, "trades": trades, "open_lots": len(qty_by), "equity": cash + mark}


def dca_bot(closes, base, safety, n_safety, step_pct, scale, tp_pct, fee=0.0):
    """the DCA bot with safety orders (the martingale family the desk bans for real money; a simulator for the paper record): a
    base order at the first close; safety order j (1..n_safety) of size safety x scale^(j-1) when the price is j x step_pct below
    the average entry; the whole position sold at tp_pct over the average entry; then the cycle restarts. Returns cycles, the
    realised P&L, the worst equity drawdown on the marked position and the capital at risk at the deepest point."""
    cash, qty, cost, so, cycles = 0.0, 0.0, 0.0, 0, 0
    worst, deepest = 0.0, 0.0
    for c in closes:
        if qty == 0:
            qty, cost, so = base / c, base * (1 + fee), 0
            continue
        avg = cost / qty
        if c >= avg * (1 + tp_pct / 100.0):
            cash += qty * c * (1 - fee) - cost
            cycles += 1
            qty, cost, so = 0.0, 0.0, 0
            continue
        if so < n_safety and c <= avg * (1 - step_pct * (so + 1) / 100.0):
            size = safety * scale ** so
            qty += size / c
            cost += size * (1 + fee)
            so += 1
        worst = min(worst, cash + qty * c - cost)
        deepest = max(deepest, cost)
    return {"cycles": cycles, "realised": cash, "worst_drawdown": worst, "max_capital": deepest,
            "open_cost": cost, "open_qty": qty}


def pair_bot(a, b, window=20, entry_z=2.0, exit_z=0.5, fee=0.0):
    """the market-neutral pairs bot: z of the log ratio of two series against its trailing window; short the ratio (short a,
    long b) above +entry_z, long below -entry_z, flat inside exit_z. Returns the trade count and the summed log-ratio P&L."""
    r = np.log(np.asarray(a, float)) - np.log(np.asarray(b, float))
    pos, pnl, trades = 0, 0.0, 0
    for t in range(window, len(r)):
        w = r[t - window:t]
        sd = w.std()
        z = (r[t] - w.mean()) / sd if sd > 0 else 0.0
        if pos != 0:
            pnl += pos * (r[t] - r[t - 1])
        if pos == 0 and abs(z) >= entry_z:
            pos = -1 if z > 0 else 1
            trades += 1
            pnl -= fee
        elif pos != 0 and abs(z) <= exit_z:
            pos = 0
            pnl -= fee
    return {"trades": trades, "pnl": pnl}


# ---------------------------------------------------------------- CX-tr-1 Eiten portfolio constructors (GPL-3.0 repo, reopened by LIC-01/02)
def min_variance_weights(cov):
    """the global minimum-variance weights w = S^-1 1 / (1' S^-1 1) (sum 1, shorts allowed): the Eiten 'minimum variance' form
    before its long-only clip. None for a singular covariance"""
    S = np.asarray(cov, float)
    try:
        x = np.linalg.solve(S, np.ones(len(S)))
    except np.linalg.LinAlgError:
        return None
    return x / x.sum()


def max_sharpe_weights(mu, cov, rf=0.0):
    """the tangency weights w = S^-1 (mu - rf) / sum(S^-1 (mu - rf)); None for a singular covariance or a zero sum"""
    S = np.asarray(cov, float)
    try:
        x = np.linalg.solve(S, np.asarray(mu, float) - rf)
    except np.linalg.LinAlgError:
        return None
    return x / x.sum() if abs(x.sum()) > 1e-15 else None


def eigen_portfolios(returns, k=3):
    """the top-k eigen-portfolios of the return covariance (returns: T x N): weights = eigenvector / sum(eigenvector) (Eiten's
    normalisation), with each portfolio's share of the variance. Sign of an eigenvector is made positive-sum so a result never
    flips between runs. The genetic-algorithm portfolio is not built: a stochastic optimiser is parameter fishing"""
    R = np.asarray(returns, float)
    S = np.cov(R, rowvar=False)
    vals, vecs = np.linalg.eigh(S)
    order = np.argsort(vals)[::-1][:k]
    out = []
    for i in order:
        v = vecs[:, i]
        if v.sum() < 0:
            v = -v
        s = v.sum()
        out.append({"weights": (v / s) if abs(s) > 1e-12 else v, "variance_share": float(vals[i] / vals.sum())})
    return out
