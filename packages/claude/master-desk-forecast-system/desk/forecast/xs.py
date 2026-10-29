"""Cross-sectional derived forecasters: a same-date rank transform of registered per-name forecasters. A derived
value on date d reads only date d's cross-section of its (law-checked) inputs, so it inherits their point-in-time
law; check() proves it on a random panel (a later date's inputs changed: no earlier value moves; two runs
bit-identical; values inside the declared bounds).

  xs.momdip     pct_rank(mom.r126) - pct_rank(mom.r5): strong 126d momentum, weak last week (xcheck/composite C4,
                the "momentum dip": p_mom126 >= 0.7 and p_r5 <= 0.3 as a rule, its ranked score here)
  xs.n9_up      the N9 composite in UP (new10.py: members' discovery fear-day signs; P1 sign convention): the mean
                same-date pct rank of feat.F3, feat.N1, feat.N7 (all members required)
  xs.n9_reset   N9 in RESET: the mean pct rank of feat.F7neg, feat.F6, feat.N5neg (EVIDENCE S6)"""
import numpy as np
import pandas as pd

from . import Forecaster, Laws, Ledger

DERIVED = {
    "xs.momdip": ({"mom.r126": 1, "mom.r5": -1}, ("up_excess_20", "up_excess_60"), ("xcheck/composite C4",)),
    "xs.n9_up": ({"feat.F3": 1, "feat.N1": 1, "feat.N7": 1}, ("up_excess_20", "up_excess_60"), ("EVIDENCE S7",)),
    "xs.n9_reset": ({"feat.F7neg": 1, "feat.F6": 1, "feat.N5neg": 1}, ("up_excess_20", "up_excess_60"),
                    ("EVIDENCE S6",)),
}
BOUNDS = {"xs.momdip": (-1.0, 1.0), "xs.n9_up": (0.0, 1.0), "xs.n9_reset": (0.0, 1.0)}

FORECASTERS = tuple(
    Forecaster(id=k, version="p2-1", kind="score", owner_module="desk.forecast.xs", family="xs", targets=t,
               laws=Laws(bounded=BOUNDS[k], abstains=True, costed="own_name_cs_impact"), inputs=tuple(mem),
               grade="B" if k != "xs.n9_up" else "C", evidence=ev,
               ledger=Ledger(access_pit="same-date cross-section of closed-bar inputs"))
    for k, (mem, t, ev) in DERIVED.items())


def derive(fid, frame, dates):
    """frame: DataFrame with the member columns; dates: the row dates -> the derived values"""
    mem = DERIVED[fid][0]
    d = pd.Series(np.asarray(dates))
    parts = []
    for col, sg in mem.items():
        x = pd.Series(np.asarray(frame[col], float))
        parts.append(sg * x.groupby(d.values).rank(pct=True))
    if fid == "xs.momdip":                      # rank(mom126) - rank(r5): a difference, not a mean
        return sum(parts).to_numpy(float)
    return (sum(parts) / len(parts)).to_numpy(float)


def check(fid, seeds=20):
    """[failure strings] for one derived forecaster on random panels"""
    fails = []
    lo, hi = BOUNDS[fid]
    for s in range(seeds):
        rng = np.random.default_rng(40_000 + s)
        nd, nn = 30, 25
        dates = np.repeat(np.arange(nd), nn)
        fr = pd.DataFrame({c: rng.normal(size=nd * nn) for c in DERIVED[fid][0]})
        fr.iloc[rng.integers(0, nd * nn, 5), 0] = np.nan
        x1, x2 = derive(fid, fr, dates), derive(fid, fr.copy(), dates)
        if not np.array_equal(x1.view(np.uint64), x2.view(np.uint64)):
            fails.append(f"seed {s}: not deterministic")
        t = int(rng.integers(0, nd - 1))
        fr2 = fr.copy()
        later = dates > t
        fr2.loc[later] = rng.normal(size=(int(later.sum()), fr.shape[1]))
        x3 = derive(fid, fr2, dates)
        if not np.array_equal(x1[~later].view(np.uint64), x3[~later].view(np.uint64)):
            fails.append(f"seed {s}: look-ahead")
        f = np.isfinite(x1)
        if (x1[f] < lo).any() or (x1[f] > hi).any():
            fails.append(f"seed {s}: out of bounds")
    return fails
