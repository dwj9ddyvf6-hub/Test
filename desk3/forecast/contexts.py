"""Context registry (FACTORY.md §3 Context, phase P2): every dimension is known at the close of d, assigned point in
time, and the search's cells are "all", every single dimension value and every pair of dimensions (no triples: the
Factory lesson, 0 of 9,861 triples passed).

Dimensions
  fear     market   fear | calm. fear = SPY's close-to-close return <= -1% on d, or SPY's close under its 50-session
                    mean (the fear-day definition of adapters/features.market, so the survivors' cells are the same)
  spy200   market   above_rising | above_falling | below. above = SPY's close > its 200-session mean; rising = that
                    mean is above its value 20 sessions earlier. Undefined (no cell) before 220 SPY sessions
  vix      market   lo | mid | hi: the VIX close's tercile within the trailing VIX_WINDOW sessions ending at d
                    (d included; at least VIX_MIN sessions), so the cuts move with the data and never see d+1
  tier     name     q1 .. q5: the per-day quintile of the name's 20-session mean dollar volume (raw close x raw
                    volume, sessions d-19..d) across every name with a value that day; q1 the thinnest. A context,
                    never a filter (FACTORY.md §3.3)
  age      name     new | old: fewer than AGE_NEW (252) sessions since the name's first bar, or not. A name whose first
                    bar is the dataset's first session is left-censored: its listing date is unknown, so it is "old"
                    only from its 252nd session on and has no age cell before that
  state    name     UP | RESET from adapters/features.frame (the survivors' states); no cell when neither
  sector   name     MISSING: the desk has no point-in-time sector map (DEEP's universe.csv and assets.json carry
                    symbol, name, exchange and status only; the own_index map is not point in time). Marked missing,
                    never imputed; no sector cell is built

assign_market(spy_close, vix) and assign_names(...) return the per-date and per-row labels; cells(dims) the cell
list; mask(frame, ctx) a cell's row mask."""
from itertools import combinations

import numpy as np
import pandas as pd

from . import Context

VIX_WINDOW = 504
VIX_MIN = 252
AGE_NEW = 252
SPY_MA = 200
SPY_SLOPE = 20

DIMS = {
    "fear": ("fear", "calm"),
    "spy200": ("above_rising", "above_falling", "below"),
    "vix": ("lo", "mid", "hi"),
    "tier": ("q1", "q2", "q3", "q4", "q5"),
    "age": ("new", "old"),
    "state": ("UP", "RESET"),
}
MARKET_DIMS = ("fear", "spy200", "vix")
NAME_DIMS = ("tier", "age", "state")
MISSING = {"sector": "no point-in-time sector map in the desk data (DEEP universe.csv / assets.json carry no "
                     "sector; own_index is not point in time): marked missing, no cell"}


def _rolling_pct_of_last(x, window, min_n):
    """the share of the trailing window (ending at i, i included) at or below x[i]; NaN under min_n values"""
    x = np.asarray(x, float)
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(n):
        if not np.isfinite(x[i]):
            continue
        w = x[max(0, i - window + 1):i + 1]
        w = w[np.isfinite(w)]
        if len(w) >= min_n:
            out[i] = float((w < x[i]).sum() + 0.5 * ((w == x[i]).sum() - 1) + 0.5) / len(w)
    return out


def assign_market(spy_close, vix):
    """spy_close: Series of SPY closes indexed by ISO session; vix: {session: close} or Series.
    -> DataFrame indexed by session with columns fear, spy200, vix (labels, or None where undefined)"""
    s = pd.Series(spy_close, dtype=float).sort_index()
    s = s[np.isfinite(s.to_numpy())]
    r = s.pct_change()
    m50 = s.rolling(50).mean()
    fear = (r <= -0.01) | (s < m50)
    fear_l = np.where(m50.notna() | (r <= -0.01), np.where(fear, "fear", "calm"), None)
    m200 = s.rolling(SPY_MA).mean()
    rising = m200 > m200.shift(SPY_SLOPE)
    ok = m200.notna() & m200.shift(SPY_SLOPE).notna()
    lab = np.where(s > m200, np.where(rising, "above_rising", "above_falling"), "below")
    spy200 = np.where(ok, lab, None)
    v = pd.Series(vix, dtype=float) if not isinstance(vix, pd.Series) else vix.astype(float)
    v = v.sort_index()
    pv = pd.Series(_rolling_pct_of_last(v.to_numpy(), VIX_WINDOW, VIX_MIN), index=v.index)
    pv = pv.reindex(s.index)
    vl = np.where(pv.isna(), None, np.where(pv < 1 / 3, "lo", np.where(pv < 2 / 3, "mid", "hi")))
    return pd.DataFrame({"fear": fear_l, "spy200": spy200, "vix": vl}, index=s.index)


def tier_of(dv20, dates):
    """per-day dollar-volume quintile labels (q1 thinnest); None where dv20 is missing"""
    df = pd.DataFrame({"d": np.asarray(dates), "x": np.asarray(dv20, float)})
    df.loc[~np.isfinite(df.x) | (df.x <= 0), "x"] = np.nan
    p = df.groupby("d")["x"].rank(pct=True, method="average")
    q = np.ceil(p.to_numpy() * 5).clip(1, 5)
    return np.where(np.isfinite(q), np.char.add("q", np.nan_to_num(q).astype(int).astype(str)), None)


def age_of(pos, left_censored):
    """pos: the session index of each bar within its name (0 = first bar); left_censored: the name's first bar is the
    dataset's first session (bool per row). -> new | old | None"""
    pos = np.asarray(pos)
    lc = np.asarray(left_censored, bool)
    old = pos >= AGE_NEW
    return np.where(old, "old", np.where(lc, None, "new"))


def cells(dims=DIMS):
    """[Context]: all, every single dim value, every pair of dims (values crossed); never a triple"""
    out = [Context("all", {})]
    for k, vals in dims.items():
        out += [Context(f"{k}={v}", {k: v}) for v in vals]
    for a, b in combinations(list(dims), 2):
        for va in dims[a]:
            for vb in dims[b]:
                ctx = Context("", {a: va, b: vb})
                out.append(Context(ctx.key, ctx.dims))
    return out


def market_cells():
    return cells({k: DIMS[k] for k in MARKET_DIMS})


def mask(frame, ctx):
    """boolean row mask of a cell over a frame holding the dims as columns"""
    m = np.ones(len(frame), bool)
    for k, v in ctx.dims.items():
        m &= (frame[k].to_numpy() == v)
    return m
