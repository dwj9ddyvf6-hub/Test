"""One session's cross-section -> its screen rows, by the frozen spec and the reference scorer's functions.

OW is a same-session rank, so P depends on the whole cross-section: every name's eligibility, tier and lrv22 come
first, then OW within each tier, then P, the veto, the HAR forecast and momentum's percentile.
  eligible   the scorer's rule on d (raw close >= $1, dv20 >= $100,000, >= 60 bars in the segment, raw volume > 0,
             ATR > 0); its tier by the scorer's rule (liquid first: raw close >= $5 and dv20 >= $20M)
  OW         the scorer's same-session rank (average rank of ties / the tier's count of eligible names > 0.9); a tier
             holding fewer than 50 eligible names takes the spec's frozen cutoffs and the row says so
             (ow_fallback); ow_frozen, the frozen-cutoff version, is on every scored row beside ow_rank
  P, veto    SEC-V's logistic on the standardized features; veto = P >= the tier's threshold, veto_applied only in
             small, micro and nano (a liquid name's P and flag are recorded, never applied)
  HAR        yhat (the forecast of log RV20), sigma_mean = exp(yhat + s2/2): the per-day volatility forecast for the
             next 20 sessions (the lognormal mean of RV20, a daily standard deviation of log returns), and var_mean
             = exp(2 yhat + 2 s2)
  momentum   mom6 = ln(c[d-21] / c[d-126]) and mom6_pct, its share at or below within session x tier
A name that is not scored keeps what is known of it and its reason. Pure: no file, clock or network."""
from . import engine_score_ref as ref
from .bars import ineligible

TIERS = ref.TIERS
OW_MIN_NAMES = 50          # features.OW.fallback: "a tier holding fewer than 50 screened names on d"
FEATURES = ("close", "volume", "dv20", "bars", "first", "lrv1", "lrv5", "lrv22", "rv22", "atr_pct", "log_atr_pct",
            "mom6")
SCORES = ("tier", "tier_n", "ow", "ow_rank", "ow_pct", "ow_frozen", "ow_fallback", "p", "threshold", "veto",
          "veto_applied", "yhat", "sigma_mean", "var_mean", "mom6_pct")
FIELDS = {
    "sym": "the symbol (Alpaca's notation)",
    "session": "the screen date d: bars through its close only",
    "scored": "eligible on d and scored",
    "reason": "why not scored (the listing filter, the bars, or the eligibility rule)",
    "close": "raw close on d (as traded)",
    "volume": "raw volume on d",
    "dv20": "median of raw close x raw volume over the 20 bars ending at d",
    "bars": "bars in the current segment read (the window holds at most job.N_BARS)",
    "first": "the session of the window's first bar",
    "lrv1": "log max(|r_d|, 0.0005), r on adjusted closes",
    "lrv5": "0.5 log max(var5, 1e-8), one-pass sample variance of the last 5 daily log returns",
    "lrv22": "0.5 log max(var22, 1e-8), the last 22 returns",
    "rv22": "exp(lrv22): the 22-session realized volatility, a daily standard deviation",
    "atr_pct": "the 14-session simple mean true range over the adjusted close",
    "log_atr_pct": "log(atr_pct)",
    "mom6": "ln(c_adj[d-21] / c_adj[d-126]); None below 127 bars",
    "tier": "liquid / small / micro / nano by the spec's rule; None when not eligible",
    "tier_n": "the tier's count of eligible names on d",
    "ow": "the OW that entered P (0 / 1): ow_rank, or ow_frozen when the tier holds fewer than 50 names",
    "ow_rank": "same-session OW: the percentile rank of lrv22 within the tier above 0.9",
    "ow_pct": "that percentile rank: the average rank of ties / tier_n",
    "ow_frozen": "OW by the spec's frozen cutoff: lrv22 above the tier's frozen lrv22",
    "ow_fallback": "true when ow is ow_frozen (the tier held fewer than 50 eligible names)",
    "p": "SEC-V's P(lose5)",
    "threshold": "the tier's frozen veto threshold",
    "veto": "P >= threshold (recorded for every tier)",
    "veto_applied": "the veto in force: small, micro and nano only (liquid names are recorded, never vetoed)",
    "yhat": "HAR's forecast of lrv20, the log of the next 20 sessions' daily volatility",
    "sigma_mean": "the per-day volatility forecast for the next 20 sessions: exp(yhat + s2/2), the lognormal mean of "
                  "RV20 (a daily standard deviation of log returns)",
    "var_mean": "exp(2 yhat + 2 s2): the lognormal mean of RV20^2 (sqrt(var_mean) is not sigma_mean)",
    "mom6_pct": "momentum's share at or below within session x tier, (0, 1] (a tie-breaker only)",
    "spec_version": "the frozen spec's version",
    "spec_sha256": "the frozen spec file's sha256",
}


def _rank_pct(lrv22, tiers):
    """{name: average rank of its ties / its tier's count}: the percentile ref.ow_same_session compares with 0.9"""
    by = {}
    for k, v in lrv22.items():
        if v is not None:
            by.setdefault(tiers[k], []).append((v, k))
    out = {}
    for items in by.values():
        items.sort()
        n, i = len(items), 0
        while i < n:
            j = i
            while j + 1 < n and items[j + 1][0] == items[i][0]:
                j += 1
            for q in range(i, j + 1):
                out[items[q][1]] = (i + 1 + j + 1) / 2.0 / n
            i = j + 1
    return out


def screen(entries, session, spec, spec_sha):
    """entries [(symbol, features or None, reason or None)] of one session -> its rows, sorted by symbol"""
    rows, elig = {}, {}
    for sym, f, why in entries:
        row = {"sym": sym, "session": session, "scored": False, "reason": why}
        row.update({k: (f or {}).get(k) for k in FEATURES})
        row.update({k: None for k in SCORES})
        row.update(spec_version=spec.get("version"), spec_sha256=spec_sha)
        if f is not None and why is None:
            row["reason"] = ineligible(f)
            tier = ref.tier_of(f["close"], f["dv20"]) if row["reason"] is None else None
            if row["reason"] is None and tier is None:
                row["reason"] = "dv20_below_min"
            if tier is not None:
                elig[sym] = (f, tier)
        rows[sym] = row
    lrv22 = {s: f["lrv22"] for s, (f, _) in elig.items()}
    tiers = {s: t for s, (_, t) in elig.items()}
    rank, pct = ref.ow_same_session(lrv22, tiers), _rank_pct(lrv22, tiers)
    n_tier = {t: sum(1 for x in tiers.values() if x == t) for t in TIERS}
    mom = {}
    for t in TIERS:
        mom.update(ref.share_at_or_below({s: f["mom6"] for s, (f, x) in elig.items() if x == t}))
    v = spec["veto"]
    for s, (f, t) in elig.items():
        fallback = n_tier[t] < OW_MIN_NAMES
        frozen = ref.ow_frozen(f["lrv22"], t, spec)
        ow = frozen if fallback else rank[s]
        p = ref.veto_probability(ow, f["lrv1"], f["lrv5"], f["lrv22"], t, spec)
        flag, applied = ref.veto(p, t, spec)
        har = ref.har_forecast(f["lrv1"], f["lrv5"], f["lrv22"], f["log_atr_pct"], t, spec)
        rows[s].update(scored=True, reason=None, tier=t, tier_n=n_tier[t], ow=ow, ow_rank=rank[s], ow_pct=pct[s],
                       ow_frozen=frozen, ow_fallback=fallback, p=p, threshold=v["thresholds"][t], veto=flag,
                       veto_applied=applied, yhat=har["yhat"], sigma_mean=har["sigma_mean"],
                       var_mean=har["var_mean"], mom6_pct=mom.get(s))
    return [rows[s] for s in sorted(rows)]


def counts(rows):
    """per tier: n, the veto flag's and the applied veto's counts and shares, OW and the fallback; coverage"""
    tiers = {}
    for t in TIERS:
        rs = [r for r in rows if r["scored"] and r["tier"] == t]
        n = len(rs)
        tiers[t] = {"n": n, "veto": sum(1 for r in rs if r["veto"]),
                    "veto_applied": sum(1 for r in rs if r["veto_applied"]),
                    "veto_share": round(sum(1 for r in rs if r["veto"]) / n, 6) if n else None,
                    "veto_applied_share": round(sum(1 for r in rs if r["veto_applied"]) / n, 6) if n else None,
                    "ow": sum(1 for r in rs if r["ow"]), "ow_fallback": bool(rs and rs[0]["ow_fallback"])}
    why = {}
    for r in rows:
        if not r["scored"]:
            why[r["reason"]] = why.get(r["reason"], 0) + 1
    scored = sum(1 for r in rows if r["scored"])
    return {"tiers": tiers, "coverage": {"names": len(rows), "scored": scored, "not_scored": len(rows) - scored,
                                         "reasons": dict(sorted(why.items()))}}
