"""desk/picker/replay.py's setup definitions A0..C0 as forecasters (imports only; the definitions are not copied).

  compute(a, mkt)   pick.<def> at every bar i: 1.0 when the definition fires at the close of i (replay.define on
                    replay.prepare of the usable bars, the market context of replay.market), 0.0 when it does not, NaN
                    before bar 260 (define's own warmup) and on unusable bars (data.guard)
  cases(...)        replay.cases unchanged: every case of every definition with its forward path, plus the seeded
                    random entries; the replay reproduction (tools/forecast_search.py --replay) reads these
The target is the path label (path_t1_stop_20: +T1 before the stop line, odds.simulate's rules, R in the plan's own
risk), scored against the random-same-name baseline (adapters/odds.py)."""
import numpy as np

from ...picker import replay as R
from .. import Forecaster, Laws
from .. import data as D

WARMUP = 260
LAWS = Laws(bounded=(0.0, 1.0), warmup=WARMUP, abstains=False, costed="odds.simulate exits, plan-risk R")

FORECASTERS = tuple(
    Forecaster(id=f"pick.{d}", version="replay-2026-10-27", kind="rule", owner_module="desk.picker.replay",
               family="pick." + R.FAMILY[d], targets=("path_t1_stop_20",), laws=LAWS,
               inputs=("daily bars", "SPY", "VIX"), evidence=("docs/research/picker-replay-2026-10-27.md",))
    for d in R.DEFS)


def market(mkt):
    """replay.market's per-session context and SPY's closes from the raw market inputs"""
    spy_bars = D.to_bars(mkt["spy"], np.where(D.guard(mkt["spy"]))[0])
    return R.market(spy_bars, mkt.get("vix") or {}, mkt.get("breadth") or {})


def compute(a, mkt, ctx=None):
    n = len(a["c"])
    out = {f.id: np.full(n, np.nan) for f in FORECASTERS}
    ok = D.guard(a)
    idx = np.where(ok)[0]
    if len(idx) <= WARMUP:
        return out
    ctx_by_d, spy_close = ctx if ctx is not None else market(mkt)
    A = R.prepare(D.to_bars(a, idx))
    spy_c = np.array([spy_close.get(d, np.nan) for d in A["d"]])
    for j in range(WARMUP, len(idx)):
        c = dict(ctx_by_d.get(A["d"][j]) or {})
        c["spy_c"] = spy_c
        fired, _ = R.define(A, j, c)
        i = idx[j]
        for d in R.DEFS:
            out["pick." + d][i] = 1.0 if d in fired else 0.0
    return out


def cases(sym, bars, mkt_ctx, spy_close, seed=0):
    """replay.cases, unchanged, with the per-case fields the replay table does not read dropped (memory)"""
    rows = R.cases(sym, bars, mkt_ctx, spy_close, seed)
    for r in rows:
        if r["def"] != "R":
            r["spy_ret1"] = r["feats"][R.FEATURES.index("spy_ret1")]
        r.pop("feats", None)
        r.pop("conds", None)
    return rows
