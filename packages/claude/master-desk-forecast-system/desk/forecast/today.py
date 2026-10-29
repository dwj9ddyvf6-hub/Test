"""A ticker's context today (FACTORY.md §6): the router's input, built from one name's closed daily bars and the market
inputs, with the same functions the search used on its panel, so a cell means the same thing in the search and today.

  Market(mkt)            the market inputs and the SPY/VIX-derived day labels, built once per run
  snapshot(...)          -> the router's `today`: {sym, as_of, bar_closed, owned, context {fear, spy200, vix, tier, age,
                         state}, values {fid: {x, pct}}, cost_side, dv20, n_bars}
Point in time: bars after as_of are dropped before anything is computed. A dimension that cannot be known is None
(an unknown dim never matches a cell): tier needs today's cross-section (tier_cuts, the four quintile edges of the
day's dollar volume, from the host job), age needs the bars to start at a listing (left_censored says they do not),
and a score's percentile needs the day's sorted cross-section (pct[fid]); a flag needs neither."""
import numpy as np
import pandas as pd

from . import contexts as CX
from . import costs as CO
from . import data as D
from . import freeze as FZ
from .adapters import _common as CM
from .adapters import avoid as AV
from .adapters import features as FT
from .adapters import survivors as SU
from .adapters import vendors as VE
from .adapters import vendors2 as VE2


class Market:
    def __init__(self, mkt, thr=None):
        self.mkt = mkt
        self.fm = FT.market(mkt)
        self.cm = CM.market(mkt)
        self.spyr = AV.spy_returns({"spy": self.fm["s"]})
        self.thr = thr if thr is not None else FZ.load("avoid-deep-1")
        self.days = CX.assign_market(pd.Series(self.fm["s"]), pd.Series(mkt["vix"]))


def percentile(x, cross_section):
    """mid-rank fraction of x within a sorted 1-d array of the day's values (ties count half); None when empty"""
    cs = np.asarray(cross_section, float)
    cs = cs[np.isfinite(cs)]
    if not len(cs) or not np.isfinite(x):
        return None
    return float((np.searchsorted(cs, x, "left") + np.searchsorted(cs, x, "right")) / 2.0 / len(cs))


def tier_label(dv20, tier_cuts):
    if tier_cuts is None or dv20 is None or not np.isfinite(dv20) or dv20 <= 0:
        return None
    return "q" + str(1 + int(np.searchsorted(np.asarray(tier_cuts, float), dv20, "right")))


def _state(c, h, l):
    from .search_deep import _state as st
    code = int(st(c, h, l)[-1])
    return {1: "UP", 2: "RESET"}.get(code)


def compute_all(a, M):
    out = {}
    for fn in (lambda: FT.compute(a, None, m=M.fm), lambda: AV.compute(a, None, spyr=M.spyr, thr=M.thr),
               lambda: SU.compute(a, None, m=M.cm), lambda: VE.compute(a, None, m=M.cm),
               lambda: VE2.compute(a, None, m=M.cm)):
        for k, x in fn().items():
            out[k] = np.asarray(x, float)
    return out


def snapshot(sym, a, M, as_of, owned=None, closed=True, want=None, tier_cuts=None, pct=None, left_censored=False,
             dollar_volume=None, plan=None):
    """a: {d (ISO sessions), o, h, l, c, v}; bars dated after as_of are ignored"""
    keep = np.asarray(a["d"]).astype(str) <= as_of
    b = {k: np.asarray(v)[keep] for k, v in a.items()}
    n = len(b["c"])
    last_is_asof = n > 0 and str(b["d"][-1]) == as_of
    out = {"sym": sym, "as_of": as_of, "bar_closed": bool(closed and last_is_asof), "owned": owned,
           "context": {k: None for k in ("fear", "spy200", "vix", "tier", "age", "state")}, "values": {},
           "cost_side": None, "dv20": None, "n_bars": int(n), "plan": plan}
    if n < 2 or not last_is_asof:
        return out
    day = M.days.loc[as_of] if as_of in M.days.index else None
    if day is not None:
        for k in CX.MARKET_DIMS:
            v = day[k]
            out["context"][k] = None if v is None or (isinstance(v, float) and np.isnan(v)) else v
    dv = np.asarray(dollar_volume if dollar_volume is not None else b["c"] * b["v"], float)
    if len(dv) != n:
        dv = dv[keep] if len(dv) == len(keep) else b["c"] * b["v"]
    cost, dv20, _ = CO.per_side(b["h"], b["l"], b["c"], dv)
    out["cost_side"] = float(cost[-1]) if np.isfinite(cost[-1]) else None
    out["dv20"] = float(dv20[-1]) if np.isfinite(dv20[-1]) else None
    out["context"]["tier"] = tier_label(out["dv20"], tier_cuts)
    out["context"]["age"] = "old" if n - 1 >= CX.AGE_NEW else (None if left_censored else "new")
    ok = D.guard(b)
    idx = np.flatnonzero(ok)
    if len(idx) > 2 and idx[-1] == n - 1:
        out["context"]["state"] = _state(b["c"][idx], b["h"][idx], b["l"][idx])
    vals = compute_all(b, M)
    for fid, arr in vals.items():
        if want is not None and fid not in want:
            continue
        x = float(arr[-1]) if len(arr) and np.isfinite(arr[-1]) else None
        p = None
        if x is not None and pct is not None and fid in pct:
            p = percentile(x, pct[fid])
        out["values"][fid] = {"x": x, "pct": p}
    return out
