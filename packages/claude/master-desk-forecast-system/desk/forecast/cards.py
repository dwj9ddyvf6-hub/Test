"""Cell cards (FACTORY.md §3, §6): for each promoted cell, the evidence the router quotes and tests, computed on a
window of a panel the search already used. A card is descriptive: it selects nothing and opens no holdout.

  Cell(fid, target, cell, sign, binary)    one forecaster x target x context cell
  build(panel, cells, window, h)           -> [card]; card keys:
      n_obs, n_dates     observations and dates of the cell in the window
      base_rate          share of the cell's names that beat their group's mean over the horizon
      rate               the same share inside the cell's application set (a flagged name; the top or bottom quintile)
      lift               rate - base_rate (an avoid cell's lift is negative when the flag works)
      cost_side          mean per-side cost of the application set (costs.per_side, the names' own bars)
      dates, gross       per-date utility of the action before costs: the application set's excess (a long) or the
                         excess it avoids (an avoid flag: minus the set's excess), one value per date
  utility(card, own_cost_side, sides)      gross - sides x own_cost_side, per date
A cell with no dates in the window is a card with status no_data and the reason, never a zero."""
from dataclasses import dataclass

import numpy as np

from . import Context
from . import search as SR


@dataclass(frozen=True)
class Cell:
    fid: str
    target: str
    cell: str
    sign: int
    binary: bool


def context_of(key):
    if key == "all":
        return Context("all", {})
    dims = dict(p.split("=", 1) for p in key.split("|"))
    ctx = Context("", dims)
    return Context(ctx.key, dims)


def _w(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    return float((x[m] * w[m]).sum() / w[m].sum()) if m.any() else None


def build(panel, cells, window, h, workers=1):
    """cards for `cells` over panel rows with window[0] <= date < window[1]"""
    d = panel["d"]
    dd = np.asarray(d.astype(str)) if hasattr(d, "astype") else np.asarray(d).astype(str)
    sel = (dd >= window[0]) & (dd < window[1])
    out = []
    by = {}
    for c in cells:
        by.setdefault((c.fid, c.target, c.binary), []).append(c)
    base = panel.loc[sel].reset_index(drop=True)
    for (fid, tcol, binary), cs in by.items():
        run = SR.Run(base, [], cells=[context_of(c.cell) for c in cs], log=lambda *a: None)
        fr = base[[fid, tcol, "cost", "dv20"]].copy()
        prep = run._prep(base[["d"] + [k for k in ("fear", "spy200", "vix", "tier", "age", "state") if k in base]])
        spec = SR.Spec(fid, tcol, h, binary=binary)
        series = run._xs_split(fr, spec, prep)
        ud = prep[0]
        for c in cs:
            t = series.get(c.cell, (None, None))[0]
            if t is None or len(t) < SR.MIN_DATES or int(t.n.sum()) < SR.MIN_OBS:
                out.append({"fid": fid, "target": tcol, "cell": c.cell, "sign": c.sign, "status": "no_data",
                            "reason": f"under the cell minimum in the window ({0 if t is None else len(t)} dates, "
                                      f"{SR.MIN_DATES} needed)"})
                continue
            if binary:
                setn, setg, setc, setp = t.fl_n, t.fl_g, t.fl_c, t.fl_p
            elif c.sign > 0:
                setn, setg, setc, setp = t.top_n, t.top_g, t.top_c, t.top_p
            else:
                setn, setg, setc, setp = t.bot_n, t.bot_g, t.bot_c, t.bot_p
            gross = (-setg if (binary and c.sign < 0) else setg).to_numpy(float)
            rate, base_rate = _w(setp, setn), _w(t.base_p, t.n)
            out.append({"fid": fid, "target": tcol, "cell": c.cell, "sign": c.sign, "binary": bool(binary), "h": h,
                        "status": "ok", "n_obs": int(t.n.sum()), "n_dates": int(len(t)),
                        "n_set": int(np.nansum(setn)), "base_rate": base_rate, "rate": rate,
                        "lift": None if rate is None or base_rate is None else rate - base_rate,
                        "cost_side": _w(setc, setn), "window": list(window),
                        "dates": [str(ud[i]) for i in t.date.to_numpy()],
                        "gross": [float(x) for x in gross]})
    return out


def utility(card, own_cost_side=None, sides=2):
    """per-date utility of acting on the card with this name's own per-side cost (the card's own when None); an
    avoid flag trades nothing (sides = 0)"""
    g = np.asarray(card["gross"], float)
    c = card.get("cost_side") if own_cost_side is None else own_cost_side
    return g - sides * (c or 0.0)
