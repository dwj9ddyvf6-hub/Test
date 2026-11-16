"""G21 jump-aware pricer miniature — CONV59-G21-PRICER-20261116.

Built to the CONV-59 register row's exact specification, no more
and no less (CONVERSION-REGISTER-2026-11-15, CONV-59; source
Lane E / DATA-HUNT-4-CHAINDEPTH.md):

- A fitted jump-aware pricing miniature over the held chain
  surfaces. It PRICES; it does not signal. It is a component for
  the book's vol expressions (the CONV-15 / CONV-16 class), never
  a standalone strategy, and carries no sizing.
- Fit on the held index rows (the morgue modelled-IV ledger:
  SPY / QQQ / IWM rows in iv_ledger_modelled.jsonl shape).
- Adoption test (the row's Kill rule): the fit must beat the
  desk's existing Black-Scholes inversion on the held next-day
  pairs, scored as next-day mid error in vol points (the G21
  candidate's own scoring), bucketed by delta. The desk's
  existing inversion carried forward IS the baseline: tomorrow's
  contract priced at today's modelled IV. If the miniature's
  out-of-sample MAE is not below the baseline's, it is NOT
  adopted (the module reports adopted=False; nothing consumes it
  as a pricing aid in that state).
- Focus form: the miniature reads the Focus chain panel in the
  format that exists (the dry-capture store's
  iv_ledger_modelled.jsonl, identical layout and basis to the
  morgue store) and fits it cross-sectionally. USE CONDITION
  (the row's falsifier-shaped rule): no strategy sizes from its
  Focus output until a second dated Focus panel exists, because
  a one-session cross-section cannot carry a temporal claim.
  focus_use_allowed() enforces the count of dated panels.

Price basis, printed wherever the output is used (the row's own
requirement): indicative mids inverted through the desk's own
Black-Scholes assumptions (the ledger rows carry that basis in
their "model" field: r = 0.045 flat; dividend yield SPY 0.013,
QQQ 0.005, IWM 0.014, else 0.0; European). Scoring against the
next day's modelled IV is therefore partly circular, exactly as
DH4 states; the adoption test is a comparison of two pricers on
the same basis, which is what the Kill rule asks for.

The model (miniature, in the strict sense DH4 uses): per
underlying and fit date, an IV surface

    iv(m, T) = a0 + a1*m + a2*m^2 + a3*log(T) + a4/sqrt(T)

with m = log(K / F), F = spot * exp((r - q) * T). The 1/sqrt(T)
term is the jump component's signature in a miniature: jump risk
elevates short-dated IV with a term that decays as T grows,
without inventing a jump-intensity parameter the held sample
(11 sessions) cannot identify. T is the miniature's own named
convention: (expiry - date).days + 1, in years /365, counting
the expiry day so same-day expiries carry a positive tenor; the
convention is used identically in fit, prediction and delta
bucketing, and the baseline comparison shares it.

Estimator: iteratively reweighted least squares with Huber
weights (tuning constant 1.345 x the MAD scale, the standard
Huber choice). The input basis is indicative quotes, and the
ledger carries inversion blow-ups (individual rows err by
hundreds of vol points against any surface); plain least
squares is not a faithful fit on this basis — its in-sample MAE
on SPY 2026-11-12 is 8.70 vol points against the robust fit's
surface. No row is excluded by the robust fit; weights are a
property of the estimator, not a data rule.

Pair definition for the adoption test (named, because DH4's
printed 103,675 does not reproduce under it): contracts keyed by
OCC, deduplicated keep-last per (date, occ) — the estate's own
ledger dedupe rule — present with an IV on both days of a
consecutive stored date pair. On the DH4-era dates (<=
2026-11-13) that definition yields 107,196 pairs; DH4's 103,675
was counted on the daily snapshots and does not reproduce under
either the ledger definition or a snapshot-IV recount attempted
at build time. The quantities that DO reproduce exactly, and
that the blocker pins, are: Focus panel 27,405 quote-carrying
modelled-IV rows over 31 underlyings in 1 session (2026-11-14),
and the index ledger's DH4-era total of 134,857 rows (SPY
57,855, QQQ 54,186, IWM 22,816).
"""
from __future__ import annotations

import json
import math
from datetime import date

R_FLAT = 0.045  # the ledger's own model basis (rows' "model")
DIV_YIELD = {"SPY": 0.013, "QQQ": 0.005, "IWM": 0.014}
BASIS_NOTE = ("indicative mids inverted through the desk's own "
              "Black-Scholes assumptions (r=0.045 flat; dividend "
              "yield SPY 0.013, QQQ 0.005, IWM 0.014, else 0.0; "
              "European)")
HUBER_K = 1.345        # standard Huber tuning constant
IRLS_ITERS = 8         # estimator iterations, fixed


# ------------------------------------------------------------- IO
def read_ledger(path):
    """Read an iv_ledger_modelled.jsonl store (the panel format
    that exists; both the morgue index store and the Focus dry-
    capture store share it). Rows are returned as stored."""
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dedupe_rows(rows):
    """One row per (date, occ), keep-last (the estate's ledger
    dedupe rule for the collector's duplicate captures)."""
    by = {}
    for r in rows:
        by[(r["date"], r["occ"])] = r
    return by


def census(rows):
    """The panel census in DH4's terms."""
    dates = sorted({r["date"] for r in rows})
    underlyings = sorted({r["underlying"] for r in rows})
    quote_rows = sum(1 for r in rows
                     if r.get("quote_mid") is not None
                     and r.get("iv") is not None)
    return {"rows": len(rows), "quote_iv_rows": quote_rows,
            "underlyings": underlyings,
            "n_underlyings": len(underlyings), "dates": dates,
            "n_dates": len(dates)}


def focus_use_allowed(rows):
    """The CONV-59 use condition: Focus output may inform sizing
    only once a second dated Focus panel exists."""
    return len({r["date"] for r in rows}) >= 2


# ------------------------------------------------- Black-Scholes
def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def tenor_years(date_str, expiry_str):
    d = (date.fromisoformat(str(expiry_str)[:10])
         - date.fromisoformat(str(date_str)[:10])).days + 1
    return max(d, 1) / 365.0


def bs_delta(spot, strike, t_years, iv, side, underlying):
    if spot <= 0 or strike <= 0 or t_years <= 0 or iv <= 0:
        return None
    q = DIV_YIELD.get(underlying, 0.0)
    d1 = (math.log(spot / strike)
          + (R_FLAT - q + 0.5 * iv * iv) * t_years) \
        / (iv * math.sqrt(t_years))
    if side == "call":
        return math.exp(-q * t_years) * _ncdf(d1)
    return -math.exp(-q * t_years) * _ncdf(-d1)


def bs_price(spot, strike, t_years, iv, side, underlying):
    if spot <= 0 or strike <= 0 or t_years <= 0 or iv <= 0:
        return None
    q = DIV_YIELD.get(underlying, 0.0)
    sq = iv * math.sqrt(t_years)
    d1 = (math.log(spot / strike)
          + (R_FLAT - q + 0.5 * iv * iv) * t_years) / sq
    d2 = d1 - sq
    df_r = math.exp(-R_FLAT * t_years)
    df_q = math.exp(-q * t_years)
    if side == "call":
        return spot * df_q * _ncdf(d1) - strike * df_r * _ncdf(d2)
    return strike * df_r * _ncdf(-d2) - spot * df_q * _ncdf(-d1)


# -------------------------------------------------------- surface
def _features(spot, strike, t_years, underlying):
    q = DIV_YIELD.get(underlying, 0.0)
    fwd = spot * math.exp((R_FLAT - q) * t_years)
    m = math.log(strike / fwd)
    return [1.0, m, m * m, math.log(t_years),
            1.0 / math.sqrt(t_years)]


def _solve(a, b):
    """Gaussian elimination for the small normal equations."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [x / pv for x in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0.0:
                f = m[r][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def _wls(xs, ys, ws):
    k = len(xs[0])
    ata = [[0.0] * k for _ in range(k)]
    atb = [0.0] * k
    for x, y, w in zip(xs, ys, ws):
        for i in range(k):
            atb[i] += w * x[i] * y
            for j in range(k):
                ata[i][j] += w * x[i] * x[j]
    return _solve(ata, atb)


def fit_surface(rows):
    """Robust (Huber IRLS) jump-aware surface over one
    underlying's rows for one date. Returns the fit or None when
    the sample cannot carry it (fewer rows than a stable fit
    needs, or a singular system)."""
    rows = [r for r in rows if r.get("iv") is not None
            and r.get("spot") and r.get("strike")]
    if len(rows) < 8:
        return None
    und = rows[0]["underlying"]
    xs, ys = [], []
    for r in rows:
        t = tenor_years(r["date"], r["expiry"])
        xs.append(_features(float(r["spot"]), float(r["strike"]),
                            t, und))
        ys.append(float(r["iv"]))
    ws = [1.0] * len(rows)
    coef = None
    for _ in range(IRLS_ITERS):
        coef = _wls(xs, ys, ws)
        if coef is None:
            return None
        res = [abs(sum(c * v for c, v in zip(coef, x)) - y)
               for x, y in zip(xs, ys)]
        srt = sorted(res)
        mad = srt[len(srt) // 2] or 1e-6
        delta = HUBER_K * 1.4826 * mad
        ws = [1.0 if r <= delta else delta / r for r in res]
    return {"underlying": und, "coef": coef, "n": len(rows)}


def predict_iv(fit, spot, strike, date_str, expiry_str):
    if fit is None or spot <= 0 or strike <= 0:
        return None
    t = tenor_years(date_str, expiry_str)
    x = _features(float(spot), float(strike), t,
                  fit["underlying"])
    return sum(c * v for c, v in zip(fit["coef"], x))


# --------------------------------------------------- adoption test
def next_day_pairs(by_date_occ):
    """(row_a, row_b) pairs: same OCC on consecutive stored
    dates, IV present on both. by_date_occ is dedupe_rows()."""
    dates = sorted({d for d, _ in by_date_occ})
    occs_by_date = {}
    for (d, o) in by_date_occ:
        occs_by_date.setdefault(d, set()).add(o)
    pairs = []
    for a, b in zip(dates, dates[1:]):
        for occ in sorted(occs_by_date[a] & occs_by_date[b]):
            ra = by_date_occ[(a, occ)]
            rb = by_date_occ[(b, occ)]
            if ra.get("iv") is not None and rb.get("iv") is not None:
                pairs.append((ra, rb))
    return pairs


def _delta_bucket(d):
    if d is None:
        return "unknown"
    a = abs(d)
    if a < 0.25:
        return "|d|<0.25"
    if a <= 0.50:
        return "0.25<=|d|<=0.50"
    return "|d|>0.50"


def adoption_test(rows, max_date=None):
    """The CONV-59 adoption test (the row's Kill rule), scored
    strictly out of sample: for each consecutive date pair, fit
    the surface on day a's index rows and predict day b's IVs for
    the paired contracts at day b's own spot and tenor; the
    baseline is the desk's Black-Scholes inversion carried
    forward (day a's modelled IV). Errors in vol points.
    max_date restricts the sample (the DH4-era bound is
    '2026-11-13')."""
    if max_date:
        rows = [r for r in rows if r["date"] <= max_date]
    by = dedupe_rows(rows)
    pairs = next_day_pairs(by)
    by_day = {}
    for (d, _), r in by.items():
        by_day.setdefault((d, r["underlying"]), []).append(r)
    fits = {}
    errs_mini, errs_base = [], []
    buckets = {}
    for ra, rb in pairs:
        key = (ra["date"], ra["underlying"])
        if key not in fits:
            fits[key] = fit_surface(by_day.get(key, []))
        fit = fits[key]
        pred = predict_iv(fit, float(rb["spot"]),
                          float(rb["strike"]), rb["date"],
                          rb["expiry"]) if fit else None
        actual = float(rb["iv"])
        e_base = abs(float(ra["iv"]) - actual) * 100.0
        errs_base.append(e_base)
        b = _delta_bucket(bs_delta(
            float(ra["spot"]), float(ra["strike"]),
            tenor_years(ra["date"], ra["expiry"]), float(ra["iv"]),
            ra["side"], ra["underlying"]))
        slot = buckets.setdefault(
            b, {"n": 0, "mini": 0.0, "base": 0.0, "scored": 0})
        slot["n"] += 1
        slot["base"] += e_base
        if pred is not None:
            e_mini = abs(pred - actual) * 100.0
            errs_mini.append(e_mini)
            slot["mini"] += e_mini
            slot["scored"] += 1

    def mae(xs):
        return sum(xs) / len(xs) if xs else None

    out_buckets = {}
    for b, s in sorted(buckets.items()):
        out_buckets[b] = {
            "n": s["n"], "scored": s["scored"],
            "mae_miniature_volpts":
                (s["mini"] / s["scored"]) if s["scored"] else None,
            "mae_baseline_volpts": s["base"] / s["n"]}
    mae_mini, mae_base = mae(errs_mini), mae(errs_base)
    return {
        "pairs": len(pairs), "scored": len(errs_mini),
        "mae_miniature_volpts": mae_mini,
        "mae_baseline_volpts": mae_base,
        "adopted": bool(mae_mini is not None
                        and mae_base is not None
                        and mae_mini < mae_base),
        "buckets": out_buckets,
        "basis": BASIS_NOTE,
        "pair_definition": ("OCC present with IV on both days of "
                            "a consecutive stored date pair, "
                            "dedupe keep-last per (date, occ)")}


def fit_focus_cross_section(rows):
    """The Focus form: per-underlying in-sample surface fit on
    the single held session. Carries no temporal claim; the use
    condition is focus_use_allowed()."""
    by_und = {}
    for r in rows:
        by_und.setdefault(r["underlying"], []).append(r)
    fits = {}
    for und, urs in sorted(by_und.items()):
        fit = fit_surface(urs)
        if fit is None:
            fits[und] = {"fitted": False, "n": len(urs)}
            continue
        errs = []
        for r in urs:
            pred = predict_iv(fit, float(r["spot"]),
                              float(r["strike"]), r["date"],
                              r["expiry"])
            if pred is not None:
                errs.append(abs(pred - float(r["iv"])) * 100.0)
        fits[und] = {"fitted": True, "n": len(urs),
                     "in_sample_mae_volpts":
                         (sum(errs) / len(errs)) if errs else None}
    return {"fits": fits,
            "use_allowed": focus_use_allowed(rows),
            "basis": BASIS_NOTE}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        prog="g21_pricer",
        description="G21 jump-aware pricer miniature (CONV-59)")
    ap.add_argument("--index-ledger", required=True)
    ap.add_argument("--focus-ledger")
    ap.add_argument("--max-date")
    args = ap.parse_args(argv)
    index_rows = read_ledger(args.index_ledger)
    out = {"index_census": census(index_rows),
           "adoption_test": adoption_test(
               index_rows, max_date=args.max_date)}
    if args.focus_ledger:
        focus_rows = read_ledger(args.focus_ledger)
        out["focus_census"] = census(focus_rows)
        out["focus_cross_section"] = fit_focus_cross_section(
            focus_rows)
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
