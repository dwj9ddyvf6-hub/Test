"""milkman_Author: the Author studies' own decision code vs desk/sleeves/milkman/Author.py.

SOURCE side (quant-research-critical@0be4c575 Author-research/... and milkman-study/v2/code; the same blobs sit in
quant-research-backup@d170596b):
each file is blob-checked; its functions are taken by exact source (ast) and its statements by verified exact text,
then executed on synthetic inputs in a fresh namespace (they are pure pandas / numpy; the scripts' module-level data
loading is not run):
  (A) bigwinners/code/build_frame.py: the desk avoid / meta decile / boost / calib / score / ALL_NAV / CAL_NAV
      statements on a synthetic fire frame -> Author.bw_stream per fire (META, f_resp_hit, RET-QUIET and WG08 missing,
      as on the desk; ep_own episodes);
  (B) bigwinners/code/s1_sleeve.py sim() (sweep, $1,000, $50,000) and s1b_paced.py sim() (token bucket) on synthetic
      CAL_NAV fire histories over real sessions -> the BigWinners / BigWinnersPaced sleeves' entries() replayed session
      by session over a book that fills at the study's entry price and releases each position after its W52 exit;
  (C) TENSOR_CREATIVE/code/c04b_book.py: the timing-book threshold and signal statements on synthetic weekly breadth
      series -> BreadthTiming.decide at every week;
  (D) c03_ratio.py's ratio-bar statements + c_eng.payload's stamping on synthetic stock / SPY daily bars ->
      Author.ratio_bars;
  (E) c_eng.tierA_proxy on synthetic close panels -> Author.tier_a_proxy on Author.daily_features;
  (F) milkman-study 40_addons.py flags_for (with the vendored dstrats) at sampled fire dates -> Author.milkman_flags
      (RIB_CROSS10, LBD3, PO_DIST, CEX_UP5).
Not measured here: the engine itself (vendored byte-exact, run unchanged) and the scans' data plumbing."""
import ast
import hashlib
import json
import os
import random
import tempfile
import zlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import write_receipt

QRB = "/home/user/quant-research-critical/Author-research"
QRC = "/home/user/quant-research-critical/milkman-study/v2/code"
FILES = {
    "build_frame": (f"{QRB}/bigwinners/code/build_frame.py", "5f89bc9fb93d8ddc197c1a9d56bbd4f85954fc2e"),
    "s1": (f"{QRB}/bigwinners/code/s1_sleeve.py", "70cfa858462c58a4f08a441613862d8bbae9f1b5"),
    "s1b": (f"{QRB}/bigwinners/code/s1b_paced.py", "41baeca890e6d3d19bea536f256483f62c4c564a"),
    "common": (f"{QRB}/bigwinners/code/common.py", "867eeaa772fce926592c9e5dab42d0d84fd27a61"),
    "c04b": (f"{QRB}/TENSOR_CREATIVE/code/c04b_book.py", "9c1139051946686fc35c2d3b09374f415023bae1"),
    "c_eng": (f"{QRB}/TENSOR_CREATIVE/code/c_eng.py", "fe69cfcef763fd21d67b7421621d71b4df8d02ae"),
    "c03": (f"{QRB}/TENSOR_CREATIVE/code/c03_ratio.py", "83c8e7ac2883249885da3e75c5d666aa5bbbde45"),
    "addons": (f"{QRC}/40_addons.py", "dc25c9b969196ed475d05c6c3323ee624d5bda89"),
}
N = int(os.environ.get("Author_PARITY_N", 1000))


def src(name):
    path, blob = FILES[name]
    b = open(path, "rb").read()
    assert hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == blob, f"{path} differs from the pinned blob"
    return b.decode()


def func(name, fn, g):
    """exec the exact source of function `fn` from file `name` into namespace g."""
    text = src(name)
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn:
            exec(compile(ast.get_source_segment(text, node), f"{name}:{fn}", "exec"), g)
            return g[fn]
    raise KeyError(fn)


def lines(name, first, last):
    """the exact source lines from the line starting with `first` through the line starting with `last`, dedented."""
    import textwrap
    L = src(name).splitlines()
    a = next(i for i, x in enumerate(L) if x.strip().startswith(first))
    b = next(i for i in range(a, len(L)) if L[i].strip().startswith(last))
    return textwrap.dedent("\n".join(L[a:b + 1]))


# --------------------------------------------------------------------------------------------- (A) the stream
def fire_frame(rng, n):
    sect = np.array(["XLK", "XLF", "XLB", "XLRE", "XLU", "SMH", "XLE", "XLV", "", "XLI"])
    px = np.round(np.exp(rng.uniform(np.log(0.5), np.log(220), n)), 2)
    X = pd.DataFrame(dict(
        signal=rng.choice(["cyan", "green"], n), dist52=rng.uniform(-70, 0, n), src="delisted",
        f_ep_ord=np.nan, ep_own=rng.integers(1, 4, n), sector=sect[rng.integers(0, len(sect), n)], px=px,
        meta_bot20=np.nan, retquiet=np.nan, f_resp_hit=np.nan, meta=np.nan, held=rng.random(n) < 0.3,
        depth60=rng.uniform(0, 95, n), rvol20=rng.uniform(0.01, 0.2, n), d_ret60=rng.uniform(-60, 150, n),
        dv20=10 ** rng.uniform(5, 8, n), wg08=np.nan))
    X["sector"] = X.sector.replace("", np.nan)
    X["liquid"] = X.dv20 >= 1e6
    X.loc[: 19, "meta"] = rng.uniform(0, 1, 20)               # a few META rows keep the decile cut defined
    X.loc[: 19, "held"] = False
    return X


def case_stream(seed):
    from desk.sleeves.milkman import Author as G
    rng = np.random.default_rng(seed)
    X = fire_frame(rng, 120)
    g = {"X": X, "np": np, "pd": pd}
    code = lines("build_frame", "cy, gr = X.signal.values", 'X["ALL_NAV"] = X.liquid & ~X.avoid')
    exec(compile(code, "build_frame:stream", "exec"), g)
    X = g["X"]
    bad = []
    for i in range(20, len(X)):
        r = X.iloc[i]
        f = {"close": r.px, "dv20": r.dv20, "lane": r.signal, "sector": r.sector if isinstance(r.sector, str) else None,
             "d_dist52": r.dist52, "ep": int(r.ep_own), "depth60": r.depth60, "rvol20": r.rvol20, "d_ret60": r.d_ret60}
        ok, score = G.bw_stream(f)
        if ok != bool(r.CAL_NAV) or abs(score - float(r.score)) > 1e-12:
            bad.append({"i": i, "port": [ok, score], "study": [bool(r.CAL_NAV), float(r.score)]})
    return {"n": len(X) - 20, "bad": bad[:3], "nbad": len(bad), "in_stream": int(X.CAL_NAV.iloc[20:].sum())}


# --------------------------------------------------------------------------------------------- (B) the sleeves' sims
def sessions(a="2019-01-02", b="2023-12-29"):
    from desk import calendar as cal
    d, out = date.fromisoformat(a), []
    while d <= date.fromisoformat(b):
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


SESS = None


def fire_history(seed):
    """synthetic CAL_NAV fire histories over real sessions: weekly fires on a 60-name pool, the study's entry
    (next session after the fire week) and W52 exit sessions, prices, scores."""
    from desk.sleeves.milkman import Author as G
    global SESS
    if SESS is None:
        SESS = sessions()
    pos = {d: i for i, d in enumerate(SESS)}
    rng = np.random.default_rng(seed)
    syms = [f"S{k:02d}" for k in range(60)]
    rows = []
    fri = date(2019, 1, 4)
    last = date.fromisoformat(SESS[-1]) - timedelta(days=380)
    lam = rng.uniform(0.5, 4)
    while fri <= last:
        k = min(60, int(rng.poisson(lam)))
        for j in rng.choice(60, k, replace=False):
            ls = G._week_last_session(fri).isoformat()
            ent = G.session_after(ls, 1)
            ex = G.week_plus(fri.isoformat(), 52)
            if ent not in pos or ex not in pos:
                continue
            E = float(np.round(np.exp(rng.uniform(np.log(1.5), np.log(300))), 2))
            rows.append(dict(sym=syms[int(j)], t=int(pd.Timestamp(fri).value // 10 ** 9),
                             friday=fri.isoformat(), last_session=ls, de=pos[ent], dx52=pos[ex], E=E,
                             px=float(np.round(E * np.exp(rng.normal(0, 0.03)), 2)),
                             exitpx=float(np.round(E * np.exp(rng.normal(0.05, 0.6)), 2)),
                             score=float(rng.choice([5.5, 6.0, 6.25, 6.5])), dv20=float(10 ** rng.uniform(6, 8))))
        fri += timedelta(days=7)
    X = pd.DataFrame(rows).sort_values(["sym", "t"]).reset_index(drop=True)
    X["dsj"] = X.sym.map({s: i for i, s in enumerate(syms)}).astype(int)
    X["avoid"] = False
    return X


def study_sims(X):
    nD = len(SESS)
    C = np.ones((nD, 60)) * 10.0
    calv = np.array([pd.Timestamp(d + " 09:31").tz_localize("America/New_York").timestamp() for d in SESS])
    g = {"X": X, "C": C, "nD": nD, "cal": calv, "np": np, "pd": pd}
    func("common", "desk_cost", g)
    g1 = dict(g)
    sim1 = func("s1", "sim", g1)
    E1, _, _ = sim1(np.ones(len(X), bool), 1000, 50000, mode="sweep")
    g2 = dict(g)
    sim2 = func("s1b", "sim", g2)
    E2, _, _ = sim2(np.ones(len(X), bool), 1000, 50000)
    return E1, E2, calv


def port_replay(X, paced, calv):
    """the sleeve's entries() on each entry session, over a book that fills at the study's entry price (the live quote
    there) and closes each position at its W52 session's close (the book's closed trades feed the realised P&L)."""
    from desk.contract import View
    from desk.sleeves.milkman import Author as G
    sl = (G.BigWinnersPaced if paced else G.BigWinners)()
    score = {f"bw|{r.sym}|{r.t}": r.score for r in X.itertuples()}
    real_stream = G.bw_stream
    G.bw_stream = lambda f: (True, score[f"bw|{f['sym']}|{f['t']}"])
    try:
        by_entry, info = {}, {}
        for r in X.itertuples():
            f = {"sym": r.sym, "t": int(r.t), "friday": r.friday, "last_session": r.last_session, "lane": "cyan",
                 "close": float(r.px), "dv20": float(r.dv20)}
            by_entry.setdefault(int(r.de), []).append((f, r))
            info[f"bw|{r.sym}|{r.t}"] = r
        st = {"ledger": {}, "seen": {}, "log": [], "extra": {}}
        closed, entered = [], {}
        for di in sorted(by_entry):
            session = SESS[di]
            for key, x in list(st["ledger"].items()):
                if x["exit_on"] < session:                       # sold at its exit session's close
                    st["ledger"].pop(key)
                    closed.append({"inst": "EQ:" + x["sym"], "qty": x["qty"], "entry": x["ref"],
                                   "exit": float(info[key].exitpx), "closed_at": x["exit_on"]})
            quotes = {f["sym"]: {"ask": float(r.E), "bid": float(r.E)} for f, r in by_entry[di]}
            view = View(now=float(calv[di]), session=session,
                        extra={"Author_quotes": quotes, "closed_trades": closed[-300:]})
            G_ = {"weekly": {"fires": [f for f, r in by_entry[di]]}}
            for it in sl.entries(view, st, G_, session, float(calv[di])):
                entered[it.signal_key] = int(it.qty)
        return entered
    finally:
        G.bw_stream = real_stream


def case_sims(seed):
    X = fire_history(seed)
    if not len(X):
        return {"n": 0, "nbad": 0, "bad": []}
    E1, E2, calv = study_sims(X)
    out = {"n": len(X), "nbad": 0, "bad": [], "entered": [len(E1), len(E2)]}
    for paced, E in ((False, E1), (True, E2)):
        want = {f"bw|{X.sym[i]}|{X.t[i]}": int(q) for i, q in E.qty.items()}
        got = port_replay(X, paced, calv)
        if want != got:
            out["nbad"] += 1
            out["bad"].append({"paced": paced, "study_only": sorted(set(want) - set(got))[:3],
                               "port_only": sorted(set(got) - set(want))[:3], "n_study": len(want),
                               "n_port": len(got)})
    return out


# --------------------------------------------------------------------------------------------- (C) breadth timing
def case_breadth(seed):
    from desk.sleeves.milkman import Author as G
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2016-10-03", "2026-10-05", freq="W-MON")
    n = rng.integers(450, 1900, len(weeks))
    share = np.clip(0.3 + np.cumsum(rng.normal(0, 0.03, len(weeks))) * 0.3 + rng.normal(0, 0.05, len(weeks)), 0.02, 0.98)
    cnt = np.round(share * n).astype(int)
    fridays = [str((w + pd.Timedelta(days=4)).date()) for w in weeks]
    breadth = {f: [int(nn), 0, int(c), 0, 0, 0] for f, nn, c in zip(fridays, n, cnt)}
    B = pd.DataFrame({"bv5": cnt / n, "n": n}, index=weeks)
    B = B[B.n >= 500].sort_index()
    wkend = B.index + pd.Timedelta(days=4)
    g = {"B": B, "m": "bv5", "wkend": wkend, "TRAIN_END": pd.Timestamp("2023-09-29"), "q": 0.5, "np": np, "pd": pd}
    exec(compile(lines("c04b", "x = pd.Series(B[m].values, index=wkend)", "x = pd.Series(B[m].values, index=wkend)"),
                 "c04b:x", "exec"), g)
    exec(compile("tr = x.index <= TRAIN_END", "c04b:tr", "exec"), g)
    assert "x = pd.Series(B[m].values, index=wkend); tr = x.index <= TRAIN_END" in src("c04b")
    exec(compile(lines("c04b", "th = np.nanquantile(x[tr], q)", "th = np.nanquantile(x[tr], q)"), "c04b:th", "exec"), g)
    assert "sig = (x <= th).astype(float).where(x.notna())" in src("c04b")
    exec(compile("sig = (x <= th).astype(float).where(x.notna())", "c04b:sig", "exec"), g)
    sig = g["sig"]
    sl = G.BreadthTiming()
    bad, cmp_ = [], 0
    for wk, s in sig.items():
        f = str(wk.date())
        if f <= "2023-09-29":
            continue
        d = sl.decide(breadth, f)
        cmp_ += 1
        if d is None or d["week"] != f or d["on"] != bool(s) or abs(d["thr"] - g["th"]) > 1e-12:
            bad.append({"week": f, "study": bool(s), "port": d})
    return {"n": cmp_, "nbad": len(bad), "bad": bad[:3]}


# --------------------------------------------------------------------------------------------- (D) ratio bars
def daily_pair(rng, start="2023-01-02", n=400):
    from desk import calendar as cal
    d, days = date.fromisoformat(start), []
    while len(days) < n:
        if cal.is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    from desk.sleeves.milkman.Author import _week_last_session
    fri = days[-1] + timedelta(days=(4 - days[-1].weekday()) % 7)
    while days[-1] < _week_last_session(fri):                   # end on the week's last session (a closed week)
        if cal.is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)

    def path(p0, vol):
        r = rng.normal(0.0003, vol, len(days))
        c = p0 * np.exp(np.cumsum(r))
        o = c * np.exp(rng.normal(0, vol / 3, len(days)))
        h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, vol / 2, len(days))))
        l = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, vol / 2, len(days))))
        ac = c * np.exp(-np.linspace(0.02, 0, len(days)) * rng.uniform(0, 1))
        return pd.DataFrame(dict(o=o, h=h, l=l, c=c, v=rng.integers(1e5, 1e7, len(days)).astype(float), ac=ac),
                            index=pd.DatetimeIndex([pd.Timestamp(x) for x in days]))
    s, b = path(rng.uniform(5, 200), rng.uniform(0.01, 0.04)), path(400, 0.01)
    drop = rng.random(len(days)) < 0.02                         # the benchmark misses a few sessions
    b = b[~drop]
    return s, b


def cal_close(ts):
    from desk import calendar as cal
    return cal.session_close(pd.Timestamp(ts).date())


def case_ratio(seed):
    from desk.sleeves.milkman import Author as G
    rng = np.random.default_rng(seed)
    s, b = daily_pair(rng)
    adj = lambda x: pd.DataFrame({k: x[k] * (x.ac / x.c) for k in "ohlc"} | {"v": x.v}, index=x.index)
    g = {"d": adj(s), "BM": {"SPY": adj(b)}, "b": "SPY", "pd": pd, "np": np, "json": json}
    code = lines("c03", 'd = d.dropna(subset=["c"]); B = BM[b].reindex(d.index)', "st = r.index.to_series()")
    assert code.count("\n") == 3, code
    exec(compile(code, "c03:ratio", "exec"), g)
    payload = func("c_eng", "payload", {"pd": pd, "np": np, "json": json})
    tmp = tempfile.mkdtemp(prefix="Author_parity_")
    try:
        payload("X", g["a"], tmp, "1wk")
        js = json.load(open(os.path.join(tmp, "X.json")))["chart"]["result"][0]
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    q = js["indicators"]["quote"][0]
    study = list(zip(js["timestamp"], q["open"], q["high"], q["low"], q["close"], q["volume"]))
    asof = cal_close(s.index[-1]) + 3600     # the scan runs after the last week's close
    bars, bend = G.ratio_bars(s, b, asof)    # raw bars with Yahoo's adjclose, adjusted inside as yl() does
    port = [(x["t"], x["o"], x["h"], x["l"], x["c"], x["v"]) for x in bars]
    study_bend = {int(pd.Timestamp(k).tz_localize("America/New_York").timestamp()) + 9 * 3600 + 1800:
                  str(pd.Timestamp(v).date()) for k, v in zip(g["st"].values, g["en"].values)}
    bad = []
    if len(study) != len(port):
        bad.append({"len": [len(study), len(port)]})
    else:
        for u, v in zip(study, port):
            if u[0] != v[0] or any(abs(a - c) > 1e-9 * max(1.0, abs(a)) for a, c in zip(u[1:], v[1:])):
                bad.append({"study": u, "port": v})
                break
        if {k: study_bend[k] for k in bend} != bend:
            bad.append({"bend": "differs"})
    return {"n": len(study), "nbad": len(bad), "bad": bad[:2]}


# --------------------------------------------------------------------------------------------- (E) tier-A proxy
def case_tier(seed):
    from desk.sleeves.milkman import Author as G
    rng = np.random.default_rng(seed)
    nd, ns = 420, 12
    C = (np.exp(np.cumsum(rng.normal(0, rng.uniform(0.01, 0.06, ns), (nd, ns)), axis=0)) * rng.uniform(0.5, 60, ns)).T
    sect = ["SMH", "XLF", "XLK", "XLU", "XLRE", "XLB", "XLE", None, "SMH", "XLV", "XLI", "XLK"]
    FM = pd.DataFrame(dict(i=np.repeat(np.arange(ns), 8), d=rng.integers(260, nd, ns * 8)))
    FM["sym"] = [f"S{i}" for i in FM.i]
    g = {"np": np, "pd": pd}
    tA = func("c_eng", "tierA_proxy", g)
    out = tA(FM.copy(), {"C": C}, {f"S{i}": sect[i] for i in range(ns)})
    days = pd.bdate_range("2020-01-01", periods=nd)
    bad = []
    for r in out.itertuples():
        d = pd.DataFrame(dict(o=C[r.i], h=C[r.i], l=C[r.i], c=C[r.i], v=1e6, ac=C[r.i]), index=days)
        f = G.daily_features(d, days[r.d])
        got = G.tier_a_proxy(f["close"], f["d_ret60"], f["dd252"], sect[r.i])
        if got != bool(r.tierA_proxy):
            bad.append({"i": int(r.i), "d": int(r.d), "study": bool(r.tierA_proxy), "port": got})
    return {"n": len(out), "nbad": len(bad), "bad": bad[:3]}


# --------------------------------------------------------------------------------------------- (F) the add-on flags
def case_flags(seed):
    from desk.sleeves.milkman import Author as G
    from desk.sleeves.milkman import vendored as V
    rng = np.random.default_rng(seed)
    n = int(rng.integers(320, 600))
    r = rng.normal(0.0004, rng.uniform(0.01, 0.04), n)
    for k in rng.choice(n, 6, replace=False):
        r[k:k + int(rng.integers(3, 15))] *= rng.uniform(0.05, 0.3)          # calm stretches
    c = rng.uniform(5, 150) * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]] * np.exp(rng.normal(0, 0.005, n))
    h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, 0.01, n)))
    l = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, 0.01, n)))
    v = 10 ** rng.uniform(5.5, 7.5) / c * np.exp(rng.normal(0, 0.4, n))
    days = pd.bdate_range("2018-01-02", periods=n)
    D = V.dstrats()
    g = dict(vars(D))
    func("addons", "within", g)
    flags_for = func("addons", "flags_for", g)
    d = dict(date=days.values.astype("datetime64[ns]"), o=o, h=h, l=l, c=c, v=v, kind="stock")
    F = flags_for(("S", d))
    frame = pd.DataFrame(dict(o=o, h=h, l=l, c=c, v=v, ac=c), index=days)
    bad, cmp_, pos = [], 0, {}
    for t in rng.choice(np.arange(300, n), 10, replace=False):
        got = G.milkman_flags(frame, days[t])
        cmp_ += 1
        for k in ("RIB_CROSS10", "LBD3", "PO_DIST", "CEX_UP5"):
            pos[k] = pos.get(k, 0) + int(bool(F[k].iloc[t]))
            if got.get(k) != bool(F[k].iloc[t]):
                bad.append({"t": int(t), "flag": k, "study": bool(F[k].iloc[t]), "port": got.get(k)})
    return {"n": cmp_, "nbad": len(bad), "bad": bad[:3], "pos": pos}


# --------------------------------------------------------------------------------------------- run
PARTS = {"stream": (case_stream, N // 50), "sims": (case_sims, max(20, N // 25)), "breadth": (case_breadth, N // 50),
         "ratio": (case_ratio, N // 4), "tier": (case_tier, N // 50), "flags": (case_flags, N // 10)}


def _run_part(args):
    name, seeds = args
    fn = PARTS[name][0]
    return [fn(s) for s in seeds]


def run():
    from concurrent.futures import ProcessPoolExecutor
    for k in FILES:
        src(k)
    stats, diffs = {}, []
    jobs = []
    W = max(1, int(os.environ.get("PARITY_WORKERS", 1)))      # one heavy process at a time unless asked otherwise
    for name, (fn, n) in PARTS.items():
        seeds = [zlib.crc32(name.encode()) % 997 * 1000 + i for i in range(n)]
        for i in range(W):
            jobs.append((name, seeds[i::W]))
    if W == 1:
        results = [_run_part(j) for j in jobs]
    else:
        with ProcessPoolExecutor(W) as ex:
            results = list(ex.map(_run_part, jobs))
    for (name, seeds), res in zip(jobs, results):
        s = stats.setdefault(name, {"runs": 0, "compared": 0, "bad": 0})
        for seed, r in zip(seeds, res):
            s["runs"] += 1
            s["compared"] += int(r["n"])
            s["bad"] += int(r["nbad"])
            for k, v in (r.get("pos") or {}).items():
                s.setdefault("flag_true", {})[k] = s.get("flag_true", {}).get(k, 0) + v
            if "entered" in r:
                s["entered_s1"] = s.get("entered_s1", 0) + r["entered"][0]
                s["entered_s1b"] = s.get("entered_s1b", 0) + r["entered"][1]
            if "in_stream" in r:
                s["in_stream"] = s.get("in_stream", 0) + r["in_stream"]
            if r["nbad"]:
                diffs.append({"part": name, "seed": seed, "bad": r["bad"]})
    cases = sum(s["compared"] for s in stats.values())
    nbad = sum(s["bad"] for s in stats.values())
    from desk.sleeves.milkman.Author import sleeves
    res = {"sleeve": "milkman_Author", "family": "milkman", "sleeves": sorted(s.CONFIG.sleeve_id for s in sleeves()),
           "cases": cases, "identical": cases - nbad, "n_diffs": nbad, "diffs": diffs[:10], "stats": stats,
           "source": {k: {"path": v[0], "blob": v[1]} for k, v in FILES.items()},
           "method": "the studies' own functions / statements (ast / exact text, blob-checked) on synthetic inputs vs "
                     "Author.py; (B) replays the sleeves' entries() session by session",
           "not_in_this_comparison": ["the Tensor engine (vendored byte-exact, run unchanged)", "the scans' data "
                                      "fetch and the jobs' schedule", "option contract choice (divergence 5)"]}
    write_receipt("milkman_Author", res)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["stats"]))
    for d in r["diffs"][:5]:
        print(json.dumps(d, default=str)[:1500])
