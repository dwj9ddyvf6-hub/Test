"""The odds engine as the random baseline of every path target (desk/terminal/odds.py: simulate, wilson; the picker
replay's random-same-name draws).

  table(cs, rnd)   the picker replay's definition table from replay.cases rows: each case simulated under its own
                   plan by odds.simulate (R in the plan's risk; a next open at or under the stop is void), and each
                   case's random-entry baselines under the case's own exits: a seeded random entry of the same name
                   (any day), of the same name in the same regime, in an uptrend, and on a session of the same fear
                   state. The selection and the summary are tools/picker_replay.py's (summarize is imported; the pick
                   loop mirrors its main() line for line and tests/test_forecast_replay.py proves the two agree on the
                   same input). Each row also carries the factory's date-clustered statistic: s_t = mean R minus the
                   mean same-name-and-regime baseline of the date's cases, with its Newey-West t (L = TS - 1).
  compute(a, mkt)  odds.random: the uninformative forecast (0.0 at every usable bar): the baseline as a forecaster, so a
                   path target's score always has its random row beside it."""
import zlib

import numpy as np

from ...picker import replay as R
from ...terminal import odds as O
from .. import Forecaster, Laws
from .. import data as D
from .. import score as S

FORECASTERS = (Forecaster(id="odds.random", version=O.VERSION, kind="rule", owner_module="desk.terminal.odds",
                          family="baseline", targets=("path_t1_stop_20",),
                          laws=Laws(bounded=(0.0, 0.0), warmup=0, costed="odds.simulate exits, plan-risk R"),
                          inputs=("daily bars",), grade="NEW", note="random same-name entries under the same exits"),)


def compute(a, mkt):
    ok = D.guard(a)
    return {"odds.random": np.where(ok, 0.0, np.nan)}


def _summarize():
    from tools.picker_replay import summarize
    return summarize


def simulate_cases(cs):
    P = np.stack([r["P"] for r in cs])
    out_d = np.array([r["out"] for r in cs])
    t1_d = np.array([r["t1"] for r in cs])
    t2_d = np.array([r["t2"] for r in cs])
    risk = np.array([r["risk"] for r in cs])
    valid = (out_d > 0) & (t1_d > 0)
    sim = O.simulate(P, np.where(valid, out_d, 1.0), np.where(valid, t1_d, 1.0),
                     np.where(np.isfinite(t2_d), t2_d, 99.0), R.TS, risk)
    sim["resolved"] &= valid
    return sim, valid, out_d, t1_d, risk


def bases(cs, rnd, valid, out_d, t1_d, risk, spy1):
    RP = np.stack([r["P"] for r in rnd]) if rnd else np.zeros((0, O.T, 4), np.float32)
    keys = {"any": (lambda r: r["sym"], lambda c: c["sym"]),
            "regime": (lambda r: (r["sym"], r["regime"]), lambda c: (c["sym"], c["regime"])),
            "uptrend": (lambda r: (r["sym"], True) if r["up"] else None, lambda c: (c["sym"], True)),
            "fear": (lambda r: (r["sym"], r["fear"]), None)}
    out = {}
    for name, (kr, kc) in keys.items():
        pool = {}
        for j, r in enumerate(rnd):
            k = kr(r)
            if k is not None:
                pool.setdefault(k, []).append(j)
        pick = np.full(len(cs), -1)
        for n, c in enumerate(cs):
            k = kc(c) if kc else (c["sym"], bool(spy1[n] <= R.FEAR_SPY))
            js = pool.get(k)
            if js:
                pick[n] = js[zlib.crc32(f"{name}{c['sym']}{c['date']}{c['def']}".encode()) % len(js)]
        base = np.full(len(cs), np.nan)
        has = pick >= 0
        if has.any():
            bs = O.simulate(RP[pick[has]], np.where(valid, out_d, 1.0)[has], np.where(valid, t1_d, 1.0)[has], None,
                            R.TS, risk[has])
            base[has] = np.where(bs["resolved"], bs["r"], np.nan)
        out[name] = base
    return out


def table(cs, rnd):
    """{def: {"all": the replay's summary row (n, mean_r, base_r, edge_r, edge_lo, edge_hi, ...), "fear"/"calm",
    "clustered": the factory's per-date statistic}} plus "_n" counts"""
    summarize = _summarize()
    sim, valid, out_d, t1_d, risk = simulate_cases(cs)
    spy1 = np.array([r["spy_ret1"] for r in cs])
    bs = bases(cs, rnd, valid, out_d, t1_d, risk, spy1)
    base = bs["regime"]
    defs = np.array([r["def"] for r in cs])
    dates = np.array([r["date"] for r in cs])
    rep = {"_n": {"cases": len(cs), "random_entries": len(rnd)}}
    for d in R.DEFS:
        idx = np.where(defs == d)[0]
        row = {"all": summarize(sim, idx, base)}
        row["all"]["bases"] = {k: summarize(sim, idx, v).get("base_r") for k, v in bs.items()}
        for nm, m in (("fear_spy_down1", spy1 <= R.FEAR_SPY), ("calm", spy1 > R.FEAR_SPY)):
            row[nm] = summarize(sim, np.where((defs == d) & m)[0], bs["fear"])
        res = idx[sim["resolved"][idx]]
        u, s, n_t = S.r_by_date(sim["r"][res], base[res], dates[res])
        sc = S.score(f"pick.{d}", "path_t1_stop_20", "all", "all", u, s, n_t, lags=R.TS - 1, kind="r")
        row["clustered"] = {"n_dates": sc.n_dates, "n_obs": sc.n_obs, "mean_s": sc.mean_excess_net,
                            "t_nw": sc.ic_t_clustered, "t_block": sc.t_block, "t_eff": sc.t_eff, "p": sc.p, "status": sc.status}
        rep[d] = row
    return rep
