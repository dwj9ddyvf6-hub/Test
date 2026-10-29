"""The P2 search on DEEP (tools/forecast_search.py --search): build the panel from DEEP's bars.parquet through a local
config of paths (never committed: deep, vix, vix3m, skew, dix, holdout_root), check the laws of every forecaster it
searches, run search.Run, and write docs/research/forecast-search-<date>.{md,json} (no data path is written).

Panel (one row per name and session, every name, no price or volume floor; the bad-print guard masks bars):
  forecasters   adapters features, avoid (P1) and survivors, vendors (P2) per name; xs.* derived per date
  targets       up_excess_h (h = 5, 20, 60): close[d+h] / open[d+1] - 1 (the excess over the cell's same-date mean
                is what the IC ranks and what the money metrics subtract); realized_vol_20 (targets.realized_vol)
  cost, dv20    costs.per_side on the name's bars with raw close x raw volume
  dims          contexts: fear, spy200, vix (by session), tier (dv20 quintile of the day), age, state (UP/RESET as
                adapters/features.frame); sector missing
Market lane: adapters/regime on SPY's bars (etf_all.parquet) with Cboe VIX/VIX3M/SKEW and SqueezeMetrics DIX.csv (a
validation fixture, revised history: non-PIT); targets spy_rv_5, spy_rv_20 (log realized vol), spy_rvx_20 (the
forward log RV minus the trailing 20-session log RV: the part persistence does not give), spy_ret_20, spy_ret_60."""
import gc
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd

from . import contexts as CX
from . import costs as CO
from . import data as D
from . import registry as RG
from . import search as SR
from . import targets as TG
from . import xs as XS
from .adapters import _common as CM
from .adapters import avoid as AV
from .adapters import features as FT
from .adapters import regime as RE
from .adapters import survivors as SU
from .adapters import vendors as VE
from .adapters import vendors2 as VE2
from .adapters import vendors3 as VE3

XS_GROUPS = ("features", "avoid", "survivors", "vendors", "vendors2", "vendors3")
HS = (5, 20, 60)
_G = {}


def read_cboe(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    d = pd.to_datetime(df["DATE"], format="%m/%d/%Y", errors="coerce")
    col = "CLOSE" if "CLOSE" in df.columns else df.columns[-1]          # SKEW_History.csv: DATE,SKEW
    s = pd.Series(df[col].astype(float).to_numpy(), index=d.dt.strftime("%Y-%m-%d"))
    return s[d.notna().to_numpy() & np.isfinite(s.to_numpy())].sort_index()


def read_dix(path):
    df = pd.read_csv(path)
    idx = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return (pd.Series(df["dix"].astype(float).to_numpy(), index=idx).sort_index(),
            pd.Series(df["gex"].astype(float).to_numpy(), index=idx).sort_index())


def file_id(path):
    st = os.stat(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return {"bytes": st.st_size, "sha256": h.hexdigest()}


def _state(c, h, l):
    c, h, l = (pd.Series(x) for x in (c, h, l))
    m50, m200 = c.rolling(50).mean(), c.rolling(200).mean()
    up = (c > m200) & (m50 > m200) & (m50 > m50.shift(10))
    reset = (c <= h.rolling(252).max() * 0.65) & (c <= l.rolling(252).min() * 1.10)
    return np.where(up, 1, np.where(reset, 2, 0)).astype(np.int8)


def _name(i):
    s, e = _G["off"][i]
    B = _G["B"]
    a = {k: B[k][s:e].astype(float) for k in ("o", "h", "l", "c", "v")}
    a["d"] = B["d"][s:e]
    n = e - s
    out = {}
    for grp, fn in (("features", lambda: FT.compute(a, None, m=_G["fm"])),
                    ("avoid", lambda: AV.compute(a, None, spyr=_G["spyr"], thr=_G["thr"])),
                    ("survivors", lambda: SU.compute(a, None, m=_G["cm"])),
                    ("vendors", lambda: VE.compute(a, None, m=_G["cm"])),
                    ("vendors2", lambda: VE2.compute(a, None, m=_G["cm"])),
                    ("vendors3", lambda: VE3.compute(a, None, m=_G["cm"]))):
        for k, x in fn().items():
            if k in _G["want"]:
                out[k] = np.asarray(x, np.float32)
    ok = D.guard(a)
    g = {k: np.where(ok, a[k], np.nan) for k in ("o", "h", "l", "c")}
    for hh in HS:
        out[f"up_excess_{hh}"] = TG.fwd_return(g, hh).astype(np.float32)
    out["realized_vol_20"] = TG.realized_vol(g, 20).astype(np.float32)
    dvol = B["c_raw"][s:e].astype(float) * B["v_raw"][s:e].astype(float)
    cost, dv20, _ = CO.per_side(g["h"], g["l"], g["c"], np.where(ok, dvol, np.nan))
    out["cost"], out["dv20"] = cost.astype(np.float32), dv20.astype(np.float32)
    st = np.zeros(n, np.int8)
    idx = np.flatnonzero(ok)
    if len(idx) > 2:
        st[idx] = _state(a["c"][idx], a["h"][idx], a["l"][idx])
    out["state"] = st
    out["pos"] = np.arange(n, dtype=np.int32)
    keep = np.isfinite(out["up_excess_5"]) | np.isfinite(out["up_excess_20"]) | np.isfinite(out["up_excess_60"])
    keep &= np.isfinite(out["dv20"])
    out = {k: v[keep] for k, v in out.items()}
    out["row"] = (s + np.flatnonzero(keep)).astype(np.int64)
    return out


# ---- the second dataset: the 2023+ split-adjusted daily cache (grade A rerun, docs/research/forecast-search-rerun-*)
CACHE_ETFS = frozenset(
    "ARKK BIL BOTZ BUG CIBR CLOU COPL COPX DBA DIA EEM EFA EWJ EWY EWZ FXI GDX GDXJ GLD GRID HACK HYG HYGU IBB IBIT "
    "ICLN IEF IGV IJH IJR ITA ITB IWD IWF IWM IWN IWO IYF IYT JETS KBE KRE KWEB LIT LQD MCHI MDY NLR PALL PDBC PFF "
    "PICK PPA PPLT QTUM REMX RSP SCHD SGOV SHY SIL SILJ SKYY SLV SMH SMHD SOXL SOXX SPY TAN TLT TQQQ URA URNM USO UUP "
    "VGT VOO VTI VXX WGMI XBI XHB XLB XLC XLE XLF XLI XLK XLP XLPD XLPU XLRE XLU XLV XLY XME XOP XRT ROBO ETHV".split())
COHORT_MIN = 100


def cache_common(syms, deep_roots=(), universe=()):
    """the cache names kept as common stock: not in the explicit ETF set, and not a symbol DEEP's universe lists but
    DEEP's own ETF/fund filter dropped (universe minus DEEP's bar roots)"""
    dropped = (set(universe) - set(deep_roots)) | CACHE_ETFS
    return sorted(s for s in syms if s not in dropped)


def coverage_starts(first_dates, cohort_min=COHORT_MIN):
    """first-bar dates shared by at least cohort_min names are coverage starts of the cache (not listings): a name
    starting there is left-censored, so its age is unknown rather than new"""
    s = pd.Series(list(first_dates)).value_counts()
    return set(s[s >= cohort_min].index)


def load_cache_source(cfg):
    """(bars frame like DEEP's, market dict with SPY from the cache, the left-censoring start dates)"""
    path = cfg["cache_parquet"] if cfg.get("cache_parquet") else None
    if path:
        c = pd.read_parquet(path)
    else:
        rows = []
        for sym, bars in D.iter_cache(cfg["cache"]):
            a = D.arrays(bars)
            if len(a["c"]):
                rows.append(pd.DataFrame({"sid": sym, **{k: a[k] for k in ("d", "o", "h", "l", "c", "v")}}))
        c = pd.concat(rows)
    c["sid"] = c["sid"].astype(str)
    spy = c[c.sid == "SPY"].sort_values("d")
    spy_a = {k: spy[k].to_numpy(float) for k in ("o", "h", "l", "c", "v")}
    spy_a["d"] = spy["d"].astype(str).to_numpy()
    deep_roots, universe = (), ()
    if cfg.get("deep"):
        deep_roots = {x.split("#")[0] for x in pd.read_parquet(os.path.join(cfg["deep"], "bars.parquet"),
                                                               columns=["sid"]).sid.cat.categories}
        universe = pd.read_csv(os.path.join(cfg["deep"], "universe.csv")).symbol
    keep = set(cache_common(c.sid.unique(), deep_roots, universe))
    c = c[c.sid.isin(keep)].copy()
    c["d"] = pd.to_datetime(c["d"])
    c["c_raw"], c["v_raw"] = c["c"], c["v"]
    c = c.sort_values(["sid", "d"], kind="stable").reset_index(drop=True)
    first = c.groupby("sid")["d"].min().dt.strftime("%Y-%m-%d")
    return c, spy_a, coverage_starts(first)


def load(cfg, limit_names=0):
    if cfg.get("cache") or cfg.get("cache_parquet"):
        b, spy_a, left_dates = load_cache_source(cfg)
        if limit_names:
            b = b[b.sid.isin(b.sid.drop_duplicates().iloc[:limit_names])].reset_index(drop=True)
        mkt = {"spy": spy_a, "vix": read_cboe(cfg["vix"]).to_dict()}
        for k in ("vix3m", "skew"):
            if cfg.get(k):
                mkt[k] = read_cboe(cfg[k]).to_dict()
        if cfg.get("dix"):
            dix, gex = read_dix(cfg["dix"])
            mkt["dix"], mkt["gex"] = dix.to_dict(), gex.to_dict()
        mkt["_left_dates"] = sorted(left_dates)
        return b, mkt
    deep = cfg["deep"]
    b = pd.read_parquet(os.path.join(deep, "bars.parquet"), columns=["sid", "d", "o", "h", "l", "c", "v", "c_raw",
                                                                     "v_raw"])
    b = b.sort_values(["sid", "d"], kind="stable").reset_index(drop=True)
    if limit_names:
        keep = b.sid.drop_duplicates().iloc[:limit_names]
        b = b[b.sid.isin(keep)].reset_index(drop=True)
    e = pd.read_parquet(os.path.join(deep, "etf_all.parquet"))
    spy = e[e.s == "SPY"].sort_values("d")
    spy_a = {k: spy[k].to_numpy(float) for k in ("o", "h", "l", "c", "v")}
    spy_a["d"] = pd.to_datetime(spy.d).dt.strftime("%Y-%m-%d").to_numpy()
    mkt = {"spy": spy_a, "vix": read_cboe(cfg["vix"]).to_dict()}
    if cfg.get("vix3m"):
        mkt["vix3m"] = read_cboe(cfg["vix3m"]).to_dict()
    if cfg.get("skew"):
        mkt["skew"] = read_cboe(cfg["skew"]).to_dict()
    if cfg.get("dix"):
        dix, gex = read_dix(cfg["dix"])
        mkt["dix"], mkt["gex"] = dix.to_dict(), gex.to_dict()
    return b, mkt


def build_panel(b, mkt, workers, want):
    d_iso = pd.to_datetime(b.d).dt.strftime("%Y-%m-%d").to_numpy()
    B = {k: b[k].to_numpy() for k in ("o", "h", "l", "c", "v", "c_raw", "v_raw")}
    B["d"] = d_iso
    sid = b.sid.to_numpy()
    start = np.flatnonzero(np.r_[True, sid[1:] != sid[:-1]])
    off = list(zip(start, np.r_[start[1:], len(sid)]))
    left_dates = mkt.pop("_left_dates", None)
    fm = FT.market(mkt)
    _G.update(B=B, off=off, fm=fm, spyr=AV.spy_returns({"spy": fm["s"]}), thr=__import__(
        "desk.forecast.freeze", fromlist=["load"]).load("avoid-deep-1"), cm=VE3.market3(mkt), want=set(want))
    import multiprocessing as mp
    parts = []
    with mp.get_context("fork").Pool(workers) as pool:
        for k, r in enumerate(pool.imap(_name, range(len(off)), chunksize=16)):
            parts.append(r)
            if k % 1000 == 0:
                print(f"names {k}/{len(off)}", flush=True)
    _G.clear()                                   # the bar arrays are not needed past the per-name pass
    cols = list(parts[0])
    P = {c: np.concatenate([p[c] for p in parts]) for c in cols}
    del parts
    gc.collect()
    first = d_iso.min()
    rows = P.pop("row")
    P["d"] = d_iso[rows]
    P["sid"] = sid[rows]
    lc = np.maximum.accumulate(np.where(np.r_[True, sid[1:] != sid[:-1]], np.arange(len(sid)), 0))
    left = (d_iso[lc] == first)[rows] if left_dates is None else np.isin(d_iso[lc], list(left_dates))[rows]
    dcat = pd.Categorical(P.pop("d"))
    P = pd.DataFrame(P)
    P["d"] = dcat
    P["sid"] = P["sid"].astype("category")
    P["age"] = pd.Categorical(CX.age_of(P.pop("pos").to_numpy(), left), categories=list(CX.DIMS["age"]))
    st = P.pop("state").to_numpy()
    P["state"] = pd.Categorical.from_codes(np.where(st == 1, 0, np.where(st == 2, 1, -1)), categories=["UP", "RESET"])
    P["tier"] = pd.Categorical(CX.tier_of(P["dv20"].to_numpy(), P["d"].cat.codes.to_numpy()),
                               categories=list(CX.DIMS["tier"]))
    md = CX.assign_market(pd.Series(fm["s"]), pd.Series(mkt["vix"]))
    cats = np.asarray(dcat.categories).astype(str)
    codes = dcat.codes
    for k in CX.MARKET_DIMS:
        lab = pd.Series(cats).map(md[k]).to_numpy(object)
        P[k] = pd.Categorical(lab[codes], categories=list(CX.DIMS[k]))
    _trim()
    for f in XS.FORECASTERS:
        if all(i in P.columns for i in f.inputs):
            P[f.id] = XS.derive(f.id, P, P["d"].cat.codes.to_numpy()).astype(np.float32)
    _trim()
    return P, md


def _trim():
    """return freed heap to the OS before the search forks its workers"""
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except OSError:
        pass


def market_panel(mkt, md):
    spy = mkt["spy"]
    ok = D.guard(spy)
    a = {k: np.where(ok, spy[k], np.nan) if k != "d" else spy[k] for k in spy}
    vals = RE.compute(spy, mkt)
    M = pd.DataFrame({"d": spy["d"], **{k: v for k, v in vals.items()}})
    M["spy_rv_5"] = TG.realized_vol(a, 5)
    M["spy_rv_20"] = TG.realized_vol(a, 20)
    lr = np.r_[np.nan, np.diff(np.log(a["c"]))]
    past = 0.5 * np.log(np.maximum(pd.Series(lr).rolling(20).var().to_numpy(), 1e-8))
    M["spy_rvx_20"] = M["spy_rv_20"] - past
    M["spy_ret_20"] = TG.fwd_return(a, 20)
    M["spy_ret_60"] = TG.fwd_return(a, 60)
    for k in CX.MARKET_DIMS:
        M[k] = M["d"].map(md[k]).to_numpy(object)
    return M


def specs_for(reg, P, M):
    xs, ms = [], []
    for fid in reg.ids():
        f = reg[fid]
        if f.family == "index":
            for t in f.targets:
                if fid in M.columns and t in M.columns and M[fid].notna().sum() > 300:
                    ms.append(SR.Spec(fid, t, int(t.rsplit("_", 1)[1]), lane="market", declared_sign=f.sign))
            continue
        if fid not in P.columns:
            continue
        binary = f.laws.bounded == (0.0, 1.0) and f.kind == "rule"
        for t in f.targets:
            if t in P.columns:
                ms_h = int(t.rsplit("_", 1)[1])
                xs.append(SR.Spec(fid, t, ms_h, binary=binary, declared_sign=f.sign))
    return xs, ms


def search(cfg, workers=3, limit_names=0):
    t0 = time.time()
    reg = RG.build(histories=int(cfg.get("law_histories", 200)), groups=XS_GROUPS + ("regime",))
    law_s = round(time.time() - t0, 1)
    b, mkt = load(cfg, limit_names)
    src = cfg["cache"] if cfg.get("cache") else os.path.join(cfg["deep"], "bars.parquet")
    data_id = {("cache" if cfg.get("cache") else "bars.parquet"): file_id(src), "names": int(b.sid.nunique()),
               "bars": int(len(b)), "window": [str(b.d.min())[:10], str(b.d.max())[:10]],
               "inputs": sorted(k for k in mkt if k != "spy" and not k.startswith("_"))}
    want = [f for f in reg.ids() if reg[f].family != "index"]
    P, md = build_panel(b, mkt, workers, want)
    del b
    gc.collect()
    t1 = time.time()
    M = market_panel(mkt, md)
    xs, ms = specs_for(reg, P, M)
    print(f"panel {len(P)} rows, {P.sid.nunique()} names; specs xs {len(xs)} market {len(ms)}", flush=True)
    run = SR.Run(P, xs, market=M, market_specs=ms, ledger=SR.HoldoutLedger(cfg.get("holdout_root",
                                                                                 "state/forecast/holdout")),
                 data_id=json.dumps(data_id, sort_keys=True), note=cfg.get("note", "DEEP P2 search"), workers=workers,
                 split=cfg.get("split", SR.SPLIT), wf_unit=cfg.get("wf_unit", "year"),
                 log=lambda m: print(m, flush=True))
    rep = run.execute()
    rep["data"] = data_id
    rep["panel"] = {"rows": int(len(P)), "names": int(P.sid.nunique()), "xs_specs": len(xs), "market_specs": len(ms),
                    "tier_rows": {k: int(v) for k, v in P["tier"].value_counts().items()},
                    "state_rows": {k: int(v) for k, v in P["state"].value_counts().items()}}
    rep["registry"] = {"law_histories": int(cfg.get("law_histories", 200)), "law_check_s": law_s,
                       "searched": sorted({s.fid for s in xs + ms})}
    rep["contexts"] = {"dims": {k: list(v) for k, v in CX.DIMS.items()}, "missing": CX.MISSING,
                       "cells_xs": len(run.cells), "cells_market": len(run.mcells)}
    rep["trials_by_forecaster"] = {}
    for r in rep["rows"]:
        if r["status"] == "tested":
            rep["trials_by_forecaster"][r["forecaster"]] = rep["trials_by_forecaster"].get(r["forecaster"], 0) + 1
    rep["runtime_s"] = {"law_check": law_s, "panel": round(t1 - t0 - law_s, 1), "search": round(time.time() - t1, 1)}
    rep["generated"] = time.strftime("%Y-%m-%d %H:%M")
    return rep


def _f(x, nd=4):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:+.{nd}f}" if isinstance(
        x, float) else str(x))


def markdown(rep, top=15):
    rows = rep["rows"]
    L = [f"# Forecast Factory P2 search on DEEP ({rep['generated']})", "",
         f"Data: {'DEEP bars.parquet' if 'bars.parquet' in rep['data'] else 'the 2023+ daily cache'} sha256 "
         f"`{(rep['data'].get('bars.parquet') or rep['data'].get('cache'))['sha256'][:16]}…`, {rep['data']['names']} "
         f"names, {rep['data']['bars']:,} bars, {rep['data']['window'][0]} to {rep['data']['window'][1]}; market "
         f"inputs {', '.join(rep['data']['inputs'])} (DIX/GEX: SqueezeMetrics DIX.csv, revised history, a validation "
         f"fixture, non-PIT). Panel {rep['panel']['rows']:,} rows. Split {rep['split']}, embargo ≥ "
         f"{rep['embargo_days_min']} calendar days (longer for 60-session labels), BH q {rep['q']}, cell minimum "
         f"{rep['min_dates']} dates and {rep['min_obs']} observations.", "",
         f"Holdout opened once: key `{rep['holdout']['key']}` at {rep['holdout']['opened_at']} (discovery digest "
         f"`{rep['holdout']['discovery_digest'][:16]}…`).", "",
         "## Headline", "",
         f"- Cells: {rep['cells_total']:,} total; **{rep['cells_tested']:,} tested** (m for BH); "
         f"{rep['cells_untested']:,} untested (under the minimum).",
         f"- **Passing BH:** {rep['bh_pass']:,}.",
         "- Verdicts: " + ", ".join(f"{k} {v:,}" for k, v in sorted(rep["verdicts"].items(), key=lambda kv: -kv[1]))
         + ".", ""]
    for title, pick in (("direction targets (up_excess, spy_ret)", lambda r: not SR.is_vol(r["target"])),
                        ("volatility targets (realized_vol, spy_rv)", lambda r: SR.is_vol(r["target"]))):
        bh = [r for r in rows if r.get("bh") and r.get("hold_signed") is not None and pick(r)]
        bh.sort(key=lambda r: -(r["hold_t_signed"] or -99))
        L += [f"## Top {top} BH-passing cells by holdout effect, {title}", "",
              "Ranked by the holdout's signed block t; s̄ = the mean per-date statistic (IC for the cross-sectional "
              "lane), signed by the discovery sign.", "",
              "| # | forecaster | target | cell | sign | disc s̄ (t) | q | WF agree, t | hold s̄ (t) | net/opp | "
              "capacity | verdict |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(bh[:top], 1):
            w = r["wf"]
            cap = "—" if r.get("capacity_usd") is None else f"${r['capacity_usd']:,.0f}"
            L.append(f"| {i} | {r['forecaster']} | {r['target']} | {r['cell']} | {r['sign']:+d} | "
                     f"{_f(r['disc_mean'])} ({_f(r['disc_t'], 1)}) | {r['q']:.2g} | {w['agree_share']}, "
                     f"{_f(w['t'], 1)} | {_f(r['hold_signed'])} ({_f(r['hold_t_signed'], 1)}) | "
                     f"{_f(r.get('execution_net'))} | {cap} | {r['verdict']} |")
        L.append("")
    prom = [r for r in rows if r.get("verdict") == "promoted-B"]
    L += ["", f"## Promoted (grade B; A needs a second dataset): {len(prom)}", ""]
    byf = {}
    for r in prom:
        byf.setdefault((r["forecaster"], r["target"]), []).append(r["cell"])
    for (f, t), cs in sorted(byf.items(), key=lambda kv: -len(kv[1])):
        L.append(f"- {f} → {t}: {len(cs)} cells ({', '.join(cs[:6])}{' …' if len(cs) > 6 else ''})")
    flips = [r for r in rows if r.get("verdict") == "sign-flip"]
    L += ["", f"## Sign flips in the holdout (X): {len(flips)}", ""]
    for r in sorted(flips, key=lambda r: r["hold_t_signed"])[:15]:
        L.append(f"- {r['forecaster']} → {r['target']} in {r['cell']}: disc {_f(r['disc_mean'])} "
                 f"(t {_f(r['disc_t'], 1)}), hold signed t {_f(r['hold_t_signed'], 1)}")
    L += ["", "## Pooled cell (all) per forecaster and target", "",
          "| forecaster | target | disc s̄ (t) | q | WF | hold s̄ signed (t) | net/opp | verdict |",
          "|---|---|---|---|---|---|---|---|"]
    for r in sorted((r for r in rows if r["cell"] == "all" and r["status"] == "tested"),
                    key=lambda r: (r["forecaster"], r["target"])):
        L.append(f"| {r['forecaster']} | {r['target']} | {_f(r['disc_mean'])} ({_f(r['disc_t'], 1)}) | "
                 f"{r['q']:.2g} | {r['wf']['agree_share']}, {_f(r['wf']['t'], 1)} | {_f(r.get('hold_signed'))} "
                 f"({_f(r.get('hold_t_signed'), 1)}) | {_f(r.get('execution_net'))} | {r.get('verdict')} |")
    L += ["", "## Contexts", "", f"- Dims: {json.dumps(rep['contexts']['dims'])}.",
          f"- Missing: sector ({rep['contexts']['missing']['sector']}).",
          f"- Cells per forecaster x target: {rep['contexts']['cells_xs']} cross-sectional, "
          f"{rep['contexts']['cells_market']} market.", "",
          f"Runtime: {rep['runtime_s']}.", ""]
    return "\n".join(L)


def write(rep, stem):
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    slim = dict(rep)
    cols = ("forecaster", "target", "cell", "status", "verdict", "disc_dates", "disc_obs", "disc_mean", "disc_t",
            "disc_t_nw", "disc_p", "q", "bh", "sign", "wf_folds", "wf_agree", "wf_t", "hold_dates", "hold_obs",
            "hold_signed", "hold_t_signed", "execution_net", "net_t", "n_opportunities", "capacity_usd")

    def rnd(v):
        if isinstance(v, (bool, np.bool_)):
            return bool(v)
        if isinstance(v, (float, np.floating)):
            return round(float(v), 5) if np.isfinite(v) else None
        if isinstance(v, (np.integer,)):
            return int(v)
        return v
    data = []
    for r in rep["rows"]:
        w = r.get("wf") or {}
        r2 = dict(r, wf_folds=w.get("folds"), wf_agree=w.get("agree_share"), wf_t=w.get("t"))
        data.append([rnd(r2.get(k)) for k in cols])
    slim["rows"] = {"columns": list(cols), "data": data,
                    "note": "one row per forecaster x target x cell; untested rows are logged, never nulls"}
    with open(stem + ".json", "w") as f:
        json.dump(slim, f, separators=(",", ":"), default=lambda x: x.item() if hasattr(x, "item") else str(x))
    with open(stem + ".md", "w") as f:
        f.write(markdown(rep))
