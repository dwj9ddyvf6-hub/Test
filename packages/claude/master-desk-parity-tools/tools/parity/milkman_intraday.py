"""milkman_intraday: the study's own SPY intraday scripts vs the port's detection and exit engines, trade by trade.

SOURCE side: quant-research-critical@0be4c575 milkman-study/v2/code: 21_intraday.py (9ea632d0), 22_intraday2.py
(410af17e), ilib.py (47753cf8) and mlib.py (0e488ae7), blob-checked and copied to a temporary directory. The scripts
run unmodified except for one declared substitution, "R_ = 30;" -> "R_ = 1;": their random-baseline draw count. That
count feeds only the baseline columns (rmean, draws), never the trade list. Each runs in its own process with
pandas.read_parquet answering the vault paths (spy_1m / 3m / 10m / 1h / 4h) from a synthetic Data Vault tape, and
writes nothing (to_parquet and the /workspace makedirs are inert). numba's @njit runs as plain Python via
tools/parity/stubs/numba.py.
PORT side: desk/sleeves/milkman/intraday.py on the same tape: Panel (built from the 1m bars as epoch bar dicts, with
no daily or hour feed, so the daily table is the panel's own days, as in the study); then detect21 / detect10 /
detect_cdc with run_exit, lema_trades / lema_exit, mdl_trades, esmon_window, pmath_trades, opx4_rows and gupn_trade.
Compared exactly:
  21: every trade of every setup and cell (strat, cell, side, entry bar, entry px, target, stop, stop mode, last bar)
      and its exit (exit px, hold), against the study's T frame after ilib.eng;
  22: every recorded row (strat, cell, side, date, return %, hold) of LEMA, MDL, ESMON, PMATH, OPX4 and GUPN, against
      the study's OUTROWS.
A case is one panel day of one tape: all of its trades across all setups and cells.
Tapes: 30-45 weekday sessions in 2012 (inside the study's LEMA train split), all hours 04:00-19:59 with sparse pre/post
markets, cent prices, trend days, calm stretches, overnight gaps, a forced gap-up continuation, a half day and a
broken day (both dropped by the panel's >= 300-bar rule), and missing minutes.
LIVE check: for sampled sessions, the port's live path is replayed minute by minute. Each pass gets a Panel of the bars
up to that minute, with that session forming, over a 4-day window (the live feed serves 7). For every lane of every
setup, each trade of the complete session must appear at the pass after its deciding bar with identical parameters,
and its exit at the pass after its exit bar. A day-end exit is the market-on-close (named divergence 2).
Counted, not diffs:
  * same_bar: lane trades whose exit is decided inside their deciding bar (named divergence 1: not taken live);
  * after_moc_entry: lane trades deciding at/after the close-12 pass (named divergence 2: not entered live);
  * moc_cut: lane trades whose stop / target exit falls after the close-12 pass; live exits them at the close
    (named divergence 2);
  * opx4_data_end: the study clipped a hold whose H-th session lies beyond the data to the last session; the
    port computes the same (the live sleeve holds the full H sessions)."""
import inspect
import json
import os
import random
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np

from . import old_run, write_receipt

TREE = "/home/user/quant-research-critical/milkman-study/v2/code"
FILES = {"21_intraday.py": "9ea632d0b65cebcd7f4bbd4adcf4537c1b5c2a3c",
         "22_intraday2.py": "410af17efea5b359fb4197ae3bad5903bc152ae5",
         "ilib.py": "47753cf83727a98bbe76e0951d21b4085e4ad3f5",
         "mlib.py": "0e488ae7ad34c37197b7141afb3ba5d1483892f6"}
N_TAPES = int(os.environ.get("MILKMAN_INTRADAY_TAPES", 48))
N_LIVE = int(os.environ.get("MILKMAN_INTRADAY_LIVE_TAPES", 12))
COST = 0.015


def gen_vault(seed):
    """a deterministic synthetic Data Vault SPY tape: the all-hours 1m frame (naive ET timestamps)."""
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    n_days = int(rng.integers(30, 46))
    start = pd.Timestamp("2012-04-02") + pd.Timedelta(days=int(rng.integers(0, 150)))
    days = pd.bdate_range(start, periods=n_days)
    special = rng.choice(np.arange(4, n_days - 2), 4, replace=False)
    half = int(special[0]) if rng.random() < 0.6 else -1
    broken = int(special[1]) if rng.random() < 0.5 else -1
    gu_day = int(special[2])                             # a forced gap-up continuation morning (GUPN's X grid)
    ath_day = int(special[3])                            # a forced premarket all-time high (PMATH)
    p_pre, p_post = float(rng.uniform(0.45, 1.0)), float(rng.uniform(0.25, 0.9))
    px = float(rng.uniform(90, 160))
    mu_prev = 0.0
    T, O, H, L, C, V = [], [], [], [], [], []
    minutes = np.arange(240, 1200)                       # 04:00 .. 19:59
    rth = (minutes >= 570) & (minutes < 960)
    melt = {}                                            # melt-ups into an OpEx Friday, then a dip (4h PO rollovers)
    fridays = [x for x in pd.date_range(days[0], days[-1], freq="WOM-3FRI")]
    pos = {x: i for i, x in enumerate(days)}
    for x in fridays:
        if x in pos and rng.random() < 0.85:
            f = pos[x] + int(rng.integers(-2, 3))
            for i in range(f - int(rng.integers(3, 6)), f):
                melt[i] = (float(rng.uniform(0.00003, 0.00006)), 0.6)
            for i in range(f, f + int(rng.integers(1, 3))):
                melt[i] = (-float(rng.uniform(0.00002, 0.00005)), 1.0)
    if True:
        f = int(rng.integers(8, n_days - 2))
        for i in range(f - 4, f):
            melt.setdefault(i, (float(rng.uniform(0.00003, 0.00006)), 0.6))
        melt.setdefault(f, (-float(rng.uniform(0.00002, 0.00005)), 1.0))
    run_hi = 0.0
    for k, d in enumerate(days):
        regime = rng.random()
        mu = 0.55 * mu_prev + rng.normal(0, 0.000012)
        if regime < 0.16:
            mu += rng.choice((-1, 1)) * rng.uniform(0.00003, 0.00007)      # trend days
        mu_prev = mu
        sig = float(rng.uniform(0.00018, 0.0009))
        if k in melt:
            mu, sig = melt[k][0], sig * melt[k][1]
        gap = rng.normal(0, 0.0025) + (rng.choice((-1, 1)) * rng.uniform(0.005, 0.016) if rng.random() < 0.15 else 0.0)
        s = np.full(len(minutes), sig)
        s[~rth] *= 0.45
        s[rth] *= 1 + 1.2 * np.exp(-np.arange(390) / 25.0) + 0.6 * np.exp(-(389 - np.arange(390)) / 20.0)
        for _ in range(int(rng.integers(0, 4))):                          # calm stretches (compression)
            a = int(rng.integers(0, len(minutes) - 60))
            s[a:a + int(rng.integers(30, 130))] *= rng.uniform(0.08, 0.3)
        m = np.zeros(len(minutes))
        m[rth] = mu
        if k == ath_day and run_hi > 0:
            gap = max(gap, float(np.log(run_hi * 1.006 / px)))
        if k == gu_day:                                                    # a gap-up continuation morning
            gap = abs(gap) + 0.005
            m[(minutes >= 570) & (minutes < 690)] = 0.00016
        r = rng.normal(m, s)
        r[0] += gap
        path = px * np.exp(np.cumsum(r))
        prev = np.r_[px, path[:-1]]
        hi = np.maximum(prev, path) * np.exp(np.abs(rng.normal(0, s / 2)))
        lo = np.minimum(prev, path) * np.exp(-np.abs(rng.normal(0, s / 2)))
        px = float(path[-1])
        keep = np.where(rth, rng.random(len(minutes)) > 0.003,
                        rng.random(len(minutes)) < np.where(minutes < 570, p_pre, p_post))
        if k == half:                                                      # an early close: RTH ends 13:00
            keep &= ~((minutes >= 780) & (minutes < 960)) | (rng.random(len(minutes)) < 0.25)
        if k == broken:                                                    # a broken day: 250 RTH bars
            keep &= ~((minutes >= 820) & (minutes < 960))
        idx = np.flatnonzero(keep)
        run_hi = max(run_hi, float(np.round(hi[idx], 2).max()) if len(idx) else 0.0)
        base = d.value // 60_000_000_000
        T.append(base + minutes[idx])
        O.append(np.round(prev[idx], 2))
        C.append(np.round(path[idx], 2))
        H.append(np.round(hi[idx], 2))
        L.append(np.round(lo[idx], 2))
        V.append(np.where(rth[idx], rng.integers(20_000, 400_000, len(idx)), rng.integers(100, 20_000, len(idx))))
    o, c = np.concatenate(O), np.concatenate(C)
    h = np.maximum(np.concatenate(H), np.maximum(o, c))
    lo = np.minimum(np.concatenate(L), np.minimum(o, c))
    ts = pd.to_datetime(np.concatenate(T) * 60_000_000_000)
    return pd.DataFrame({"timestamp": ts, "open": o, "high": h, "low": lo, "close": c,
                         "volume": np.concatenate(V).astype(float)})


def vault_frames(m):
    """the vault's candle files from the 1m tape: 3m / 10m / 1h / 4h bins from midnight."""
    out = {"spy_1m": m}
    for name, rule in (("spy_3m", "3min"), ("spy_10m", "10min"), ("spy_1h", "1h"), ("spy_4h", "4h")):
        x = m.set_index("timestamp").resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                                         "close": "last", "volume": "sum"})
        out[name] = x.dropna(subset=["open"]).reset_index()
    return out


OLD = r'''
import json, os, sys
import numpy as np
import pandas as pd
GEN
VF
FR = {}
def _rp(path, *a, **k):
    return FR[os.path.basename(str(path))[:-len(".parquet")]].copy()
pd.read_parquet = _rp
pd.DataFrame.to_parquet = lambda self, *a, **k: None
_mk = os.makedirs
os.makedirs = lambda p, *a, **k: None if str(p).startswith("/workspace") else _mk(p, *a, **k)
SRC = {n: open(n).read() for n in ("21_intraday.py", "22_intraday2.py")}
for n in SRC:
    assert SRC[n].count("R_ = 30;") == 1
out = []
def one(case):
    FR.clear()
    FR.update(vault_frames(gen_vault(case["seed"])))
    g = {"__name__": "__main__", "__file__": os.path.join(os.getcwd(), "21_intraday.py")}
    exec(compile(SRC["21_intraday.py"].replace("R_ = 30;", "R_ = 1;"), "21_intraday.py", "exec"), g)
    T = g["T"]
    t21 = T[["strat", "cell", "side", "ent", "ep", "tgt", "stp", "smode", "last", "xp", "hold"]].values.tolist()
    g2 = {"__name__": "__main__", "__file__": os.path.join(os.getcwd(), "22_intraday2.py")}
    exec(compile(SRC["22_intraday2.py"].replace("R_ = 30;", "R_ = 1;"), "22_intraday2.py", "exec"), g2)
    t22 = []
    for st, frames in g2["OUTROWS"].items():
        for f in frames:
            for r in f[["strat", "cell", "side", "date", "ret", "hold"]].itertuples(index=False):
                t22.append([r.strat, r.cell, int(r.side), str(pd.Timestamp(r.date).date()), float(r.ret), float(r.hold)])
    return {"t21": [[str(a), str(b), int(c), int(d), float(e), float(f), float(g_), int(h), int(i), float(j), float(k)]
                    for a, b, c, d, e, f, g_, h, i, j, k in t21], "t22": t22}
for case in PAYLOAD["cases"]:
    try:
        out.append(one(case))
    except Exception as e:
        import traceback
        out.append({"error": f"{type(e).__name__}: {e}", "where": traceback.format_exc()[-600:]})
print(json.dumps(out))
'''.replace("GEN", inspect.getsource(gen_vault)).replace("VF", inspect.getsource(vault_frames))


def bars_of(m):
    """the tape as the desk's bar dicts (epoch seconds)."""
    import pandas as pd
    t = m.timestamp.dt.tz_localize("America/New_York").astype("int64") // 10 ** 9
    if int(t.iloc[0]) > 10 ** 12:                         # (a coarser resolution than ns)
        t = (pd.Series(m.timestamp.dt.tz_localize("America/New_York").values.astype("datetime64[s]").astype("int64")))
    return [{"t": float(a), "o": float(b), "h": float(c), "l": float(d), "c": float(e), "v": float(f)}
            for a, b, c, d, e, f in zip(t.values, m.open.values, m.high.values, m.low.values, m.close.values,
                                        m.volume.values)]


def port_tape(seed):
    """the port's 21 trades and 22 rows on one tape, plus the per-day lane counters."""
    import pandas as pd
    from desk.sleeves.milkman import intraday as I
    m = gen_vault(seed)
    # the clock hours before the 1m window come from the hourly feed, as live (yahoo_clock): here the tape's own
    # hours, so the tape's first (partial) hour is a bar as in the vault's 1h / 4h candles
    P = I.Panel(bars_of(m), h1=bars_of(vault_frames(m)["spy_1h"]))
    t21, t22 = [], []
    for di in range(len(P.days)):
        e = int(P.E0[di])
        for t in I.detect21(P, di) + I.detect10(P, di) + [x for x in I.detect_cdc(P) if x["di"] == di]:
            xi, xp = I.run_exit(P, t, e)
            t21.append([t["strat"], t["cell"], t["side"], t["ent"], t["ep"], t["tgt"], t["stp"], t["smode"], t["last"],
                        xp, float(xi - t["ent"])])
    day = lambda d: str(pd.Timestamp(P.DT[d]).date())
    for EN in (10, 20, 30):
        for q in (0.7, 0.8, 0.9):
            thr = I.lema_threshold(P, q)
            for t in I.lema_trades(P, EN, thr, q):
                xj, xp = I.lema_exit(P, t, int(P.E0[t["d"]]))
                t22.append(["LEMA", t["cell"], t["side"], day(t["d"]),
                            t["side"] * (xp / t["ep"] - 1) * 100 - 2 * COST, float(xj - t["ent"])])
    for side in (1, -1):
        for erc in (0.25, 0.35, 0.5, 1.01):
            for k in (0.75, 1.0, 1.25):
                for t in I.mdl_trades(P, erc, k, side):
                    if t["f"] is not None:
                        t22.append(["MDL", t["cell"], side, day(t["d"]), t["ret"] * 100 - 2 * COST,
                                    float(t["xb"] - t["f"])])
    for d in range(len(P.days)):
        dt = pd.Timestamp(P.DT[d])
        if dt < pd.Timestamp("2010-01-01"):
            continue
        for eh in (4, 6, 8, 9.5):
            for xh in (12, 16):
                a, b = I.esmon_window(P, dt, eh, xh)
                if type(a) is not float or type(b) is not float:
                    continue
                rr = (b / a - 1) * 100 - 2 * COST
                for sd in (1, -1):
                    t22.append(["ESMON", f"dow={dt.dayofweek};entry={eh};exit={xh}", sd, day(d), sd * rr,
                                float(int((xh - eh) * 60))])
        for cell, t in I.pmath_trades(P, d):
            xi, xp = I.run_exit(P, t, int(P.E0[d]))
            t22.append(["PMATH", cell, -1, day(d), -(xp / t["ep"] - 1) * 100 - 2 * COST, float(t["xm"])])
        for X in (0.5, 1.0, 1.5):
            t = I.gupn_trade(P, d, X)
            if t is not None:
                e = int(P.E0[d])
                t22.append(["GUPN", f"X={X}", 1, day(d), (P.c[e] / P.o[t["ent"]] - 1) * 100 - 2 * COST,
                            float(e - t["ent"])])
    counted = {"opx4_data_end": 0}
    DATES = P.dates()
    dc = P.daily.c.values
    nd = len(DATES)
    for window, grid in ((True, [(thr, H) for thr in (-99, 0.618, 1.0) for H in (3, 5, 10)]),
                         (False, [("noOpEx_all", H) for H in (5, 10)])):
        rows = I.opx4_rows(P, window=window)
        for thr, H in grid:
            for r in rows:
                if window and not r["ext"] >= thr:
                    continue
                x = min(r["d"] + H, nd - 1)
                if r["d"] + H > nd - 1:
                    counted["opx4_data_end"] += 1
                t22.append(["OPX4", f"ext={thr};H={H}", -1, str(pd.Timestamp(DATES[r["d"]]).date()),
                            -(dc[x] / r["px"] - 1) * 100 - 2 * COST, float(H)])
    days = {i: day(i) for i in range(len(P.days))}
    ent_day = {j: days[di] for di in range(len(P.days)) for j in range(int(P.S0[di]), int(P.E0[di]) + 1)}
    lanes = lane_counters(P)
    return {"t21": t21, "t22": t22, "days": days, "ent_day": ent_day, "counted": counted, "lanes": lanes}


def lane_counters(P):
    """the designated cells' trades on complete days: same-bar exits, entries at/after the close-12 pass, and
    stop / target exits after it (named divergences 1-2)."""
    from desk.sleeves.milkman import intraday as I
    out = {"same_bar": 0, "after_moc_entry": 0, "moc_cut": 0, "lane_trades": 0}
    for d in range(len(P.days)):
        e = int(P.E0[d])
        for setup, (sid, picks) in I.SETUPS.items():
            if setup in ("ESMON", "OPX4"):
                continue
            for side, cell in picks:
                for t in I.lane_trades(setup, P, d, cell, side):
                    out["lane_trades"] += 1
                    ex = t.get("exit")
                    if P.mod[min(t["decide"], e)] >= 378:
                        out["after_moc_entry"] += 1
                    elif ex is not None and ex[0] <= t["decide"]:
                        out["same_bar"] += 1
                    elif ex is not None and ex[0] < e and P.mod[ex[0]] >= 378:
                        out["moc_cut"] += 1
    return out


def _f(x):
    return float("nan") if x is None else float(x)


def _close(a, b):
    a, b = _f(a), _f(b)
    if np.isnan(a) or np.isnan(b):
        return np.isnan(a) and np.isnan(b)
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def compare(old, port):
    """per panel day: diffs of the 21 trades and the 22 rows."""
    by_day = {d: {"old": [], "port": []} for d in port["days"].values()}
    for side, rows in (("old", old["t21"]), ("port", port["t21"])):
        for r in rows:
            d = port["ent_day"].get(int(r[3]))
            by_day.setdefault(d, {"old": [], "port": []})[side].append(("21",) + tuple(r))
    for side, rows in (("old", old["t22"]), ("port", port["t22"])):
        for r in rows:
            by_day.setdefault(r[3], {"old": [], "port": []})[side].append(("22",) + tuple(r))
    diffs, identical, n_trades = [], 0, 0
    for d, g in sorted(by_day.items(), key=lambda kv: str(kv[0])):
        n_trades += len(g["old"])
        bad = _diff(g["old"], g["port"])
        if bad:
            diffs.append({"day": d, "diff": bad})
        else:
            identical += 1
    return diffs, identical, len(by_day), n_trades


def _key(r):
    if r[0] == "21":                 # strat cell side ent smode last
        return r[:5] + (r[8], r[9])
    return r[:5]                     # strat cell side date


def _vals(r):
    if r[0] == "21":
        return (r[5], r[6], r[7], r[10], r[11])     # ep tgt stp xp hold
    return (r[5], r[6])                              # ret hold


def _diff(old, port):
    go, gp = {}, {}
    for r in old:
        go.setdefault(_key(r), []).append(_vals(r))
    for r in port:
        gp.setdefault(_key(r), []).append(_vals(r))
    bad = []
    for k in sorted(set(go) | set(gp), key=str):
        a = sorted(go.get(k, []), key=lambda v: [_f(x) if not np.isnan(_f(x)) else -1e300 for x in v])
        b = sorted(gp.get(k, []), key=lambda v: [_f(x) if not np.isnan(_f(x)) else -1e300 for x in v])
        if len(a) != len(b) or not all(all(_close(x, y) for x, y in zip(u, v)) for u, v in zip(a, b)):
            bad.append({"key": [str(x) for x in k], "old": a[:4], "port": b[:4]})
            if len(bad) >= 5:
                break
    return bad


def port_case(seed):
    return port_tape(seed)


# --------------------------------------------------------------------------------------------- the live replay
def live_tape(seed, n_days=2):
    """replay the live path minute by minute on sampled sessions of one tape."""
    import pandas as pd
    from desk.sleeves.milkman import intraday as I
    m = gen_vault(seed)
    bars = bars_of(m)
    ts = np.array([b["t"] for b in bars])
    P0 = I.Panel(bars)
    rnd = random.Random(seed)
    cands = [d for d in range(8, len(P0.days)) if np.isfinite(P0.ATR.get(d, np.nan))]
    picks = sorted(rnd.sample(cands, min(n_days, len(cands))))
    stats = {"sessions": 0, "passes": 0, "lane_trades": 0, "entries_matched": 0, "exits_matched": 0,
             "moc_exits": 0, "mismatches": []}
    # the Legend's EMA threshold is a train-period quantile: the tape's own (as in the main comparison), not a 7-day
    # window's (the live sleeve reads it from the long daily history)
    thr = {q: I.lema_threshold(P0, q) for q in (0.7, 0.8, 0.9)}

    def seeded(X):
        for q, v in thr.items():
            X.cache[("lema_thr", q)] = v
        return X
    for d in picks:
        day = pd.Timestamp(P0.DT[d])
        iso = str(day.date())
        lo = (day - pd.Timedelta(days=4)).tz_localize("America/New_York").timestamp()
        end_day = (day + pd.Timedelta(hours=20)).tz_localize("America/New_York").timestamp()
        win = [b for b, t in zip(bars, ts) if lo <= t < end_day]
        wts = np.array([b["t"] for b in win])
        R = seeded(I.Panel(win))                             # the complete session, the same window
        rd = R.days.index[pd.DatetimeIndex(R.DT) == day][0]
        ref = {}
        for setup, (sid, picks_) in I.SETUPS.items():
            if setup in ("ESMON", "OPX4"):
                continue
            for side, cell in picks_:
                for t in I.lane_trades(setup, R, rd, cell, side):
                    ref[(setup, side, t["key"])] = t
        rs, re_ = int(R.S0[rd]), int(R.E0[rd])
        seen, exited = {}, {}
        stats["sessions"] += 1
        for j in range(rs, re_ + 1):
            cut = (day + pd.Timedelta(minutes=570 + int(R.mod[j]) + 1)).tz_localize("America/New_York").timestamp()
            L = seeded(I.Panel(win[:int(np.searchsorted(wts, cut))], today=iso))
            if L.live_di is None:
                continue
            ld = L.live_di
            jl = int(L.E0[ld])
            stats["passes"] += 1
            for setup, (sid, picks_) in I.SETUPS.items():
                if setup in ("ESMON", "OPX4"):
                    continue
                for side, cell in picks_:
                    for t in I.lane_trades(setup, L, ld, cell, side):
                        k = (setup, side, t["key"])
                        rel = jl - int(L.S0[ld])
                        if k not in seen:
                            seen[k] = rel
                            r = ref.get(k)
                            if r is None:
                                stats["mismatches"].append({"day": iso, "trade": [setup, side, t["key"]],
                                                            "why": "live-only trade"})
                                continue
                            if r["decide"] - rs != rel or t["decide"] - int(L.S0[ld]) != rel:
                                stats["mismatches"].append({"day": iso, "trade": [setup, side, t["key"]],
                                                            "why": f"first seen at bar {rel}, decides at "
                                                                   f"{r['decide'] - rs}"})
                            elif not _same(t, r, L, R):
                                stats["mismatches"].append({"day": iso, "trade": [setup, side, t["key"]],
                                                            "why": "parameters differ"})
                            else:
                                stats["entries_matched"] += 1
                        ex = t.get("exit")
                        if ex is not None and k not in exited:
                            exited[k] = (ex[0] - int(L.S0[ld]), ex[1])
        for k, r in ref.items():
            stats["lane_trades"] += 1
            if k not in seen:
                stats["mismatches"].append({"day": iso, "trade": [k[0], k[1], k[2]], "why": "never seen live"})
                continue
            rx = r.get("exit")
            lx = exited.get(k)
            if rx is not None and lx is not None and rx[0] - rs == lx[0] and _close(rx[1], lx[1]):
                stats["exits_matched"] += 1
            elif rx is not None and lx is None and rx[0] == re_:
                stats["moc_exits"] += 1                      # the session's last bar: the market-on-close exit
            elif rx is None and lx is None:
                stats["moc_exits"] += 1
            else:
                stats["mismatches"].append({"day": iso, "trade": [k[0], k[1], k[2]],
                                            "why": f"exit ref {rx} live {lx}"})
    return stats


def _same(t, r, L, R):
    for f in ("strat", "cell", "side", "smode", "tgt", "stp"):
        if f in t or f in r:
            a, b = t.get(f), r.get(f)
            if isinstance(a, float) or isinstance(b, float):
                if not _close(a, b):
                    return False
            elif a != b:
                return False
    if (t.get("ent") is not None) and (t["ent"] - int(L.S0[L.live_di]) != r["ent"] - int(R.S0[_rday(R, L)])):
        return False
    ep = t.get("ep")
    if ep is not None and np.isfinite(ep) and not _close(ep, r.get("ep")):
        return False
    return True


def _rday(R, L):
    import pandas as pd
    return int(R.days.index[pd.DatetimeIndex(R.DT) == pd.Timestamp(L.DT[L.live_di])][0])


# --------------------------------------------------------------------------------------------- run
def _old_batch(seeds, tree):
    return old_run(OLD, {"cases": [{"seed": s} for s in seeds]}, timeout=7200, tree=tree)


def _ports(seeds):
    return [port_case(s) for s in seeds]


def _lives(seeds):
    return [live_tape(s) for s in seeds]


def run():
    import hashlib
    tree = tempfile.mkdtemp(prefix="milkman_intraday_src_")    # a copy: nothing is written into the source repo
    for name, blob in FILES.items():
        b = open(os.path.join(TREE, name), "rb").read()
        assert hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == blob, f"{name} differs from the pinned blob"
        open(os.path.join(tree, name), "wb").write(b)
    seeds = [7_000 + k for k in range(N_TAPES)]
    W = max(1, int(os.environ.get("PARITY_WORKERS", 1)))      # one heavy process at a time unless asked otherwise
    try:
        if W == 1:
            olds = [_old_batch(seeds, tree)]
        else:
            with ThreadPoolExecutor(W) as tx:
                olds = list(tx.map(lambda ch: _old_batch(ch, tree), [seeds[i::W] for i in range(W)]))
        old = {}
        for i in range(len(olds)):
            for s, r in zip(seeds[i::len(olds)], olds[i]):
                old[s] = r
        if W == 1:
            parts, lives = [_ports(seeds)], [_lives(seeds[:N_LIVE])]
        else:
            with ProcessPoolExecutor(W) as ex:
                parts = list(ex.map(_ports, [seeds[i::W] for i in range(W)]))
                lives = list(ex.map(_lives, [seeds[:N_LIVE][i::W] for i in range(W)]))
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    port = {}
    for i in range(len(parts)):
        for s, r in zip(seeds[i::len(parts)], parts[i]):
            port[s] = r
    diffs, cases, identical, n_old = [], 0, 0, 0
    counted = {"opx4_data_end": 0, "same_bar": 0, "after_moc_entry": 0, "moc_cut": 0}
    by_strat = {}
    lane_trades = 0
    failed = [{"seed": s, "error": old[s]["error"]} for s in seeds if "error" in old[s]]
    for s in seeds:
        if "error" in old[s]:
            continue
        d, ide, n, nt = compare(old[s], port[s])
        cases += n
        identical += ide
        n_old += nt
        diffs += [dict(x, seed=s) for x in d]
        counted["opx4_data_end"] += port[s]["counted"]["opx4_data_end"]
        for k in ("same_bar", "after_moc_entry", "moc_cut"):
            counted[k] += port[s]["lanes"][k]
        lane_trades += port[s]["lanes"]["lane_trades"]
        for r in old[s]["t21"] + old[s]["t22"]:
            by_strat[r[0]] = by_strat.get(r[0], 0) + 1
    live = {"sessions": 0, "passes": 0, "lane_trades": 0, "entries_matched": 0, "exits_matched": 0, "moc_exits": 0,
            "mismatches": 0}
    live_bad = []
    for part in lives:
        for st in part:
            for k in live:
                if k != "mismatches":
                    live[k] += st[k]
            live["mismatches"] += len(st["mismatches"])
            live_bad += st["mismatches"][:5]
    from desk.sleeves.milkman.intraday import SETUPS
    res = {"sleeve": "milkman_intraday", "family": "milkman", "sleeves": sorted(v[0] for v in SETUPS.values()),
           "cases": cases, "identical": identical, "diffs": diffs[:10], "n_diffs": len(diffs) + live["mismatches"],
           "trades_compared": n_old, "trades_by_strat": by_strat, "tapes": len(seeds) - len(failed), "source_failed": failed, "counted": counted,
           "lane_trades": lane_trades, "live_replay": live, "live_mismatches": live_bad[:10],
           "source": {"repo": "quant-research-critical", "commit": "0be4c57569e363d052bd23564cf0664697439927",
                      "tree": TREE, "files": FILES, "substitution": "R_ = 30; -> R_ = 1; (random-baseline draws)"},
           "method": "the study's 21_intraday.py / 22_intraday2.py run on synthetic vault files vs the port's detection "
                     "and exits on the same tape; every trade / row compared exactly per panel day; plus a "
                     "minute-by-minute live replay of sampled sessions",
           "divergences": {"counted_not_diffs": ["same_bar (named divergence 1)", "after_moc_entry (2)", "moc_cut (2)",
                                                 "opx4_data_end (the study's data-end clip)"],
                           "not_in_this_comparison": ["fill prices and timing (1)", "daily history source (3)",
                                                      "history depth (4)", "extended-hours legs (5)",
                                                      "ATH reference (6)", "LEMA threshold source (7)",
                                                      "downtime (8)"]}}
    write_receipt("milkman_intraday", res)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "trades_compared", "counted", "live_replay")}))
    for d in r["diffs"][:3]:
        print(json.dumps(d, default=str)[:3000])
    for d in r["live_mismatches"][:5]:
        print(json.dumps(d, default=str)[:1000])
