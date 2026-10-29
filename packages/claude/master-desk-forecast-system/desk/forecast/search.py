"""The gated search (FACTORY.md §4, phase P2): forecaster x target x context cell, discovery and holdout, walk-forward,
BH over the whole run, own-name costs and capacity.

Two lanes share one BH:
  cross-sectional  per-name forecasters on a panel (one row per name and session). s_t = the date's Spearman IC
                   between the forecaster and the target over the cell's names (average ranks; Pearson of the ranks,
                   score.ic_by_date's rule; at least MIN_NAMES names). Context cells with name dims (tier, age,
                   state) rank within that group; market dims (fear, spy200, vix) select dates.
  market           index forecasters (adapters/regime.py) on SPY's own series, one row per session.
                   s_t = z_t (y_t - ybar_disc), z_t = (x_t - mean_disc x) / sd_disc x: a predictive-regression
                   contribution whose mean is the discovery-standardised covariance; the discovery moments are frozen
                   and reused on the holdout.

Gates, in order (every number is a constant below):
  1 split      discovery = dates before SPLIT minus the embargo; holdout = dates from SPLIT. The embargo is
               max(EMBARGO_DAYS, the label's span in calendar days) so no discovery label reaches into the holdout.
  2 cell size  a cell needs MIN_DATES dates and MIN_OBS observations in discovery, or it is `untested` (logged,
               never a null, never counted in BH).
  3 t and p    score.block_t with h = the target horizon (P1's gapped blocks: the p that enters BH); the Newey-West t
               (L = h - 1) is kept beside it.
  4 BH         Benjamini-Hochberg at Q over every tested cell of the run at once (both lanes): m = trials.
  5 walk-fwd   expanding yearly folds inside discovery (the first year trains only); each fold's sign is learned on
               the dates before it minus h + 5 sessions; pass = the fold mean has the discovery sign in at least
               WF_AGREE of the folds (at least WF_MIN_FOLDS folds with WF_MIN_FOLD_DATES dates) and the pooled
               walk-forward series (learned sign x s_t over the fold dates) has block t >= WF_T.
  6 holdout    opened ONCE per run key (forecaster versions, targets, data identity, SEARCH_VERSION): HoldoutLedger
               refuses a second opening, and the opening is logged (time, key, discovery digest) in the report.
               Pass = the discovery sign, signed block t >= HOLD_T and signed effect >= HOLD_FRAC x discovery effect.
  7 costs      cross-sectional: the application set per date is the top quintile by sign x value (a long), or for a
               0/1 flag with sign -1 the flagged names (a veto, which trades nothing: its net is the excess it avoids).
               net_t = mean excess of the set - 2 x its mean per-side cost (costs.per_side); execution_net = the mean
               over holdout dates per opportunity (every name of the set counts, filled or not). Market return
               targets: sign(z) x return - 2 x INDEX_COST; volatility targets are not tradable as stock (options
               routes are forward-only, FACTORY §4.10): their net is None.
  8 capacity   capacity.cap on the application set (median per date, then median over holdout dates); `tiny` under
               capacity.TINY_USD.
Verdicts: untested | null-overall (fails 4) | wf-failed | holdout-failed | sign-flip (holdout significantly opposite)
| cost-failed | tiny | promoted-B. Grade A needs a second dataset passing (not in this run)."""
import hashlib
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import Score
from . import capacity as CP
from . import contexts as CX
from . import score as S

SEARCH_VERSION = "search-p2-1"
SPLIT = "2023-01-01"
EMBARGO_DAYS = 45
Q = 0.10
MIN_DATES, MIN_OBS, MIN_NAMES = 30, 300, 20
WF_AGREE, WF_T, WF_MIN_FOLDS, WF_MIN_FOLD_DATES = 0.70, 2.0, 3, 10
HOLD_T, HOLD_FRAC = 2.0, 0.5
INDEX_COST = 0.0003
CLIP = (-0.95, 3.0)          # the excess used for the money metrics only (ranks are unaffected): bad-print safety
TOP = 0.8


@dataclass(frozen=True)
class Spec:
    fid: str
    target: str
    h: int
    binary: bool = False
    declared_sign: int = 1
    lane: str = "xs"           # xs | market


def is_vol(target):
    return target.startswith(("realized_vol", "spy_rv"))


class HoldoutAlreadyOpened(RuntimeError):
    pass


class HoldoutLedger:
    """one opening per run key, logged; root holds <key>.json"""

    def __init__(self, root):
        self.root = root

    def path(self, key):
        return os.path.join(self.root, f"{key}.json")

    def is_open(self, key):
        return os.path.exists(self.path(key))

    def open(self, key, digest, note=""):
        os.makedirs(self.root, exist_ok=True)
        p = self.path(key)
        entry = {"key": key, "opened_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "discovery_digest": digest,
                 "search_version": SEARCH_VERSION, "note": note}
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            with open(p) as f:
                prev = json.load(f)
            raise HoldoutAlreadyOpened(f"holdout {key} was opened at {prev.get('opened_at')}")
        with os.fdopen(fd, "w") as f:
            json.dump(entry, f, sort_keys=True)
        return entry


def run_key(specs, data_id, split=SPLIT, wf_unit="year"):
    body = {"v": SEARCH_VERSION, "specs": sorted(f"{s.fid}|{s.target}|{s.h}" for s in specs),
            "data": data_id, "split": split}
    if wf_unit != "year":                       # the default key (the first run's) is unchanged
        body["wf_unit"] = wf_unit
    raw = json.dumps(body, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def embargo_days(h):
    return max(EMBARGO_DAYS, int(math.ceil(h * 7 / 5)) + 4)


def split_masks(dates, h, split=SPLIT):
    cut = (date.fromisoformat(split) - timedelta(days=embargo_days(h))).isoformat()
    if isinstance(getattr(dates, "dtype", None), pd.CategoricalDtype):          # the DEEP panel: compare categories
        cats = np.asarray(dates.cat.categories).astype(str)
        codes = dates.cat.codes.to_numpy()
        return (cats < cut)[codes], (cats >= split)[codes]
    d = np.asarray(dates).astype(str)
    return d < cut, d >= split


def _date_codes(d):
    """(sorted unique ISO dates, int64 code per row) for a plain or categorical date column"""
    if isinstance(getattr(d, "dtype", None), pd.CategoricalDtype):
        used, codes = np.unique(d.cat.codes.to_numpy(), return_inverse=True)
        return np.asarray(d.cat.categories).astype(str)[used], codes.astype(np.int64)
    ud, dc = np.unique(np.asarray(d).astype(str), return_inverse=True)
    return ud, dc.astype(np.int64)


# ------------------------------------------------------------------ the per-(date, group) tables, cross-sectional
NAME_GROUPINGS = ((),) + tuple((k,) for k in CX.NAME_DIMS) + tuple(
    (a, b) for i, a in enumerate(CX.NAME_DIMS) for b in CX.NAME_DIMS[i + 1:])


def _gcodes(panel, grouping):
    if not grouping:
        return np.zeros(len(panel), np.int64), [()]
    lab = panel[list(grouping)].astype(object)
    ok = lab.notna().all(axis=1).to_numpy()
    tup = pd.MultiIndex.from_frame(lab.where(lab.notna(), "")).to_flat_index()
    codes, uniq = pd.factorize(tup)
    codes = np.where(ok, codes, -1).astype(np.int64)
    return codes, list(uniq)


def tables(panel, fcol, tcol, binary, dcodes, ndates, groupings=NAME_GROUPINGS, cache=None):
    """{grouping: DataFrame[date_code, gval, s, n, top_g, top_c, top_cap, bot_g, bot_c, bot_cap, fl_g, fl_c, fl_cap,
    fl_n]} over the panel rows (a split's rows)"""
    x = panel[fcol].to_numpy(np.float64)
    y = panel[tcol].to_numpy(np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    out = {}
    for g in groupings:
        gc, gv = cache[g] if cache is not None and g in cache else _gcodes(panel, g)
        m = ok & (gc >= 0)
        if not m.any():
            out[g] = pd.DataFrame()
            continue
        G = len(gv)
        key = dcodes[m] * G + gc[m]
        df = pd.DataFrame({"k": key, "x": x[m], "y": y[m]})
        grp = df.groupby("k", sort=False)
        rx = grp["x"].rank().to_numpy()
        ry = grp["y"].rank().to_numpy()
        uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        n = cnt[inv].astype(float)
        mu = (n + 1) / 2
        cxy = np.bincount(inv, (rx - mu) * (ry - mu))
        cxx = np.bincount(inv, (rx - mu) ** 2)
        cyy = np.bincount(inv, (ry - mu) ** 2)
        with np.errstate(invalid="ignore", divide="ignore"):
            ic = cxy / np.sqrt(cxx * cyy)
        yc = np.clip(y[m], *CLIP)
        cost = panel["cost"].to_numpy(np.float64)[m]
        cap = CP.cap(panel["dv20"].to_numpy(np.float64)[m], 1.0)
        ym = np.bincount(inv, yc) / cnt
        pct = rx / n
        pos = (yc > ym[inv]).astype(float)                      # beats the group's mean that date (cards: base rate, lift)
        res = {"k": uk, "s": ic, "n": cnt, "base_p": np.bincount(inv, pos) / cnt}
        sets = {"top": pct > TOP, "bot": pct <= 1 - TOP}
        if binary:
            sets["fl"] = x[m] > 0.5
        for nm, sel in sets.items():
            ns = np.bincount(inv, sel.astype(float), minlength=len(uk))
            with np.errstate(invalid="ignore", divide="ignore"):
                res[nm + "_g"] = np.bincount(inv, np.where(sel, yc, 0.0), minlength=len(uk)) / ns - ym
                res[nm + "_c"] = np.bincount(inv, np.where(sel, cost, 0.0), minlength=len(uk)) / ns
                res[nm + "_cap"] = np.exp(np.bincount(inv, np.where(sel & (cap > 0), np.log(np.where(cap > 0, cap, 1)),
                                                                    0.0), minlength=len(uk)) / ns)
            res[nm + "_n"] = ns
            with np.errstate(invalid="ignore", divide="ignore"):
                res[nm + "_p"] = np.bincount(inv, np.where(sel, pos, 0.0), minlength=len(uk)) / ns
        t = pd.DataFrame(res)
        t = t[(t.n >= MIN_NAMES) & np.isfinite(t.s)]
        t["date"] = (t.k // G).astype(np.int64)
        t["g"] = (t.k % G).astype(np.int64)
        t["gval"] = [gv[i] for i in t.g]
        out[g] = t.drop(columns=["k", "g"]).sort_values("date").reset_index(drop=True)
    return out


def _cell_series(tabs, ctx, mlab, date_index):
    """(dates codes, table rows) of one cell from the grouping tables and the market labels per date code"""
    nd = tuple(k for k in CX.NAME_DIMS if k in ctx.dims)
    t = tabs.get(nd)
    if t is None or t.empty:
        return None
    if nd:
        want = tuple(ctx.dims[k] for k in nd)
        t = t[[gv == want for gv in t.gval]]
    for k in CX.MARKET_DIMS:
        if k in ctx.dims:
            t = t[mlab[k][t.date.to_numpy()] == ctx.dims[k]]
    return t


# ------------------------------------------------------------------ walk-forward
def _fold_labels(dates_iso, unit):
    if unit == "quarter":
        return np.array([f"{d[:4]}Q{(int(d[5:7]) - 1) // 3}" for d in dates_iso])
    return np.array([d[:4] for d in dates_iso])


def walk_forward(dates_iso, s, h, disc_sign, unit="year"):
    """{folds, agree, agree_share, t, pass} over expanding yearly (or, for a short second dataset, quarterly) folds of
    a discovery series (date order)"""
    s = np.asarray(s, float)
    yrs = _fold_labels(dates_iso, unit)
    uy = sorted(set(yrs))
    agree, pooled, folds = 0, [], 0
    gap = h + 5
    for y in uy[1:]:
        te = np.flatnonzero(yrs == y)
        tr = np.flatnonzero(yrs < y)
        tr = tr[:max(0, len(tr) - gap)]
        if len(te) < WF_MIN_FOLD_DATES or len(tr) < WF_MIN_FOLD_DATES:
            continue
        folds += 1
        learned = 1.0 if s[tr].mean() >= 0 else -1.0
        agree += int(np.sign(s[te].mean()) == disc_sign)
        pooled.append(learned * s[te])
    if folds < WF_MIN_FOLDS:
        return {"folds": folds, "agree": agree, "agree_share": None, "t": None, "pass": False}
    bt = S.block_t(np.concatenate(pooled), h)["t"]
    share = agree / folds
    return {"folds": folds, "agree": agree, "agree_share": round(share, 3), "t": None if bt is None else round(bt, 3),
            "pass": bool(share >= WF_AGREE and bt is not None and bt >= WF_T)}


# ------------------------------------------------------------------ the run
def _stats(s, h):
    s = np.asarray(s, float)
    b = S.block_t(s, h)
    nw = S.nw_t(s, h - 1)
    return {"mean": float(s.mean()) if len(s) else None, "t_block": b["t"], "p": b["p"], "t_nw": nw["t"]}


def _net_series(t, sign, binary):
    if binary and sign < 0:
        return -t.fl_g.to_numpy(), t.fl_n.to_numpy(), t.fl_cap.to_numpy()
    if binary:
        return (t.fl_g - 2 * t.fl_c).to_numpy(), t.fl_n.to_numpy(), t.fl_cap.to_numpy()
    if sign > 0:
        return (t.top_g - 2 * t.top_c).to_numpy(), t.top_n.to_numpy(), t.top_cap.to_numpy()
    return (t.bot_g - 2 * t.bot_c).to_numpy(), t.bot_n.to_numpy(), t.bot_cap.to_numpy()


_RUN = None


def _call(arg):
    name, i, it = arg
    return i, getattr(_RUN, name)(it)


class Run:
    """one search run: discovery for every spec x cell, BH, walk-forward, one holdout opening, costs, verdicts"""

    def __init__(self, panel=None, specs=(), market=None, market_specs=(), ledger=None, data_id="", note="",
                 cells=None, market_cells=None, groupings=NAME_GROUPINGS, log=print, workers=1, split=SPLIT,
                 wf_unit="year"):
        self.split, self.wf_unit = split, wf_unit
        self.panel, self.market = panel, market
        self.specs, self.mspecs = list(specs), list(market_specs)
        self.ledger, self.data_id, self.note, self.log = ledger, data_id, note, log
        self.cells = cells or CX.cells()
        self.mcells = market_cells or CX.market_cells()
        self.groupings = groupings
        self.rows = []
        self.holdout = None
        self.workers = workers

    # ---- cross-sectional helpers
    def _prep(self, frame):
        ud, dc = _date_codes(frame["d"])
        mlab = {}
        for k in CX.MARKET_DIMS:
            if k in frame.columns:
                col = frame[k].astype(object)
                mlab[k] = col.groupby(dc).first().reindex(range(len(ud))).to_numpy(object)
        cache = {g: _gcodes(frame, g) for g in self.groupings}
        return ud, dc, mlab, cache

    def _xs_split(self, frame, spec, prep):
        ud, dc, mlab, cache = prep
        tabs = tables(frame, spec.fid, spec.target, spec.binary, dc, len(ud), self.groupings, cache)
        out = {}
        for ctx in self.cells:
            t = _cell_series(tabs, ctx, mlab, ud)
            out[ctx.key] = (t, ud)
        return out

    def _market_split(self, frame, spec, moments):
        x = frame[spec.fid].to_numpy(float)
        y = frame[spec.target].to_numpy(float)
        ok = np.isfinite(x) & np.isfinite(y)
        if moments is None:
            if ok.sum() < 3:
                return {}, None
            moments = (float(x[ok].mean()), float(x[ok].std(ddof=1)) or 1.0, float(y[ok].mean()))
        z = (x - moments[0]) / moments[1]
        s = z * (y - moments[2])
        d = frame["d"].astype(str).to_numpy()
        out = {}
        for ctx in self.mcells:
            m = ok.copy()
            for k, v in ctx.dims.items():
                m &= frame[k].to_numpy(object) == v
            out[ctx.key] = (pd.DataFrame({"date_iso": d[m], "s": s[m], "n": np.ones(m.sum(), int),
                                          "z": z[m], "y": y[m]}), None)
        return out, moments

    def _masks(self, h):
        if not hasattr(self, "_mk"):
            self._mk = {}
        if h not in self._mk:
            self._mk[h] = split_masks(self.panel["d"], h, self.split)
        return self._mk[h]

    def _cols(self, spec):
        """the numeric columns a worker reads (the dates and dims live in the parent's caches, so a forked worker
        never touches a per-row Python object and copy-on-write never duplicates the panel)"""
        return [spec.fid, spec.target, "cost", "dv20"]

    def _frame(self, spec, mask):
        """a small frame of the spec's numeric columns from the parent's numpy views (no pandas block is touched
        in a worker, so nothing is consolidated or copied there)"""
        return pd.DataFrame({c: self.arr[c][mask] for c in self._cols(spec)})

    def _disc_spec(self, spec):
        disc, _ = self._masks(spec.h)
        fr = self._frame(spec, disc)
        key = ("xs", spec.h)
        if key not in self.cache:
            self.cache[key] = self._prep(fr)
        series = self._xs_split(fr, spec, self.cache[key])
        return [self._disc_row(spec, ck, t, ud) for ck, (t, ud) in series.items()]

    def _map(self, fn, items):
        if self.workers <= 1 or len(items) <= 1:
            out = []
            for it in items:
                out.append(fn(it))
                self.log(f"{fn.__name__} {it[0].fid if isinstance(it, tuple) else it.fid}")
            return out
        import multiprocessing as mp
        global _RUN
        _RUN = self
        # no maxtasksperchild: a recycled worker is forked from the pool's handler thread and can inherit a held
        # queue lock (observed: a deadlocked DEEP run, 2026-10-27)
        with mp.get_context("fork").Pool(self.workers) as pool:
            res = [None] * len(items)
            for k, (i, r) in enumerate(pool.imap_unordered(_call, [(fn.__name__, i, it) for i, it in
                                                                   enumerate(items)])):
                res[i] = r
                self.log(f"{fn.__name__} {k + 1}/{len(items)}")
            out = res
        return out

    def discovery(self):
        Mk = self.market
        self.cache = {}
        if self.specs:
            need = {c for sp in self.specs for c in self._cols(sp)}
            self.arr = {c: np.asarray(self.panel[c].to_numpy()) for c in sorted(need)}
            for h in sorted({sp.h for sp in self.specs}):          # warm the shared caches before any fork
                disc, hold = self._masks(h)
                base = ["d"] + [k for k in CX.MARKET_DIMS + CX.NAME_DIMS if k in self.panel.columns]
                self.cache[("xs", h)] = self._prep(self.panel.loc[disc, base].reset_index(drop=True))
                self.cache[("xs-hold", h)] = self._prep(self.panel.loc[hold, base].reset_index(drop=True))
        for rows in self._map(self._disc_spec, self.specs):
            self.rows.extend(rows)
        self.moments = {}
        for spec in self.mspecs:
            disc, _ = split_masks(Mk["d"], spec.h, self.split)
            series, mom = self._market_split(Mk.loc[disc].reset_index(drop=True), spec, None)
            self.moments[(spec.fid, spec.target)] = mom
            for ck, (t, _) in series.items():
                self.rows.append(self._disc_row(spec, ck, t, None))

    def _disc_row(self, spec, ck, t, ud):
        if t is None or len(t) == 0:
            n_dates, n_obs, s, diso = 0, 0, np.array([]), []
        else:
            s = t.s.to_numpy(float)
            n_dates, n_obs = len(t), int(t.n.sum())
            diso = list(ud[t.date.to_numpy()]) if ud is not None else list(t.date_iso)
        row = {"forecaster": spec.fid, "target": spec.target, "h": spec.h, "lane": spec.lane, "cell": ck,
               "binary": spec.binary, "declared_sign": spec.declared_sign, "disc_dates": n_dates, "disc_obs": n_obs,
               "first_date": diso[0] if diso else None, "last_date": diso[-1] if diso else None}
        sc = Score(forecaster=spec.fid, target=spec.target, cell=ck, split="disc", n_obs=n_obs, n_dates=n_dates,
                   first_date=row["first_date"], last_date=row["last_date"], n_opportunities=n_obs)
        if n_dates < MIN_DATES or n_obs < MIN_OBS:
            sc.status = "untested"
        else:
            st = _stats(s, spec.h)
            sc.ic, sc.t_block, sc.ic_t_clustered, sc.p = st["mean"], st["t_block"], st["t_nw"], st["p"]
            if sc.p is None:
                sc.status = "untested"
            row.update(disc_mean=st["mean"], disc_t=st["t_block"], disc_t_nw=st["t_nw"], disc_p=st["p"])
            sgn = 1.0 if st["mean"] >= 0 else -1.0
            row["sign"] = int(sgn)
            row["wf"] = walk_forward(diso, s, spec.h, sgn, self.wf_unit)
        row["status"] = sc.status
        row["_score"] = sc
        return row

    def bh(self):
        found = S.bh_run([r["_score"] for r in self.rows], Q)
        ids = {id(s) for s in found}
        self.m = sum(1 for r in self.rows if r["_score"].status == "tested" and r["_score"].p is not None)
        for r in self.rows:
            sc = r["_score"]
            r["q"] = sc.q_bh
            r["bh"] = id(sc) in ids
            r["trials"] = sc.trials
        return self.m

    def digest(self):
        raw = json.dumps([[r["forecaster"], r["target"], r["cell"], r.get("disc_mean"), r.get("bh")]
                          for r in self.rows], default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def open_holdout(self):
        key = run_key(self.specs + self.mspecs, self.data_id, self.split, self.wf_unit)
        self.holdout = self.ledger.open(key, self.digest(), self.note)
        self.log(f"holdout opened {key}")
        Mk = self.market
        byspec = {}
        for r in self.rows:
            byspec.setdefault((r["forecaster"], r["target"]), []).append(r)
        items = [(spec, byspec[(spec.fid, spec.target)]) for spec in self.specs]
        done = self._map(self._hold_spec, items)
        for (spec, rows), new in zip(items, done):
            for r, n in zip(rows, new):
                r.update(n)
        for spec in self.mspecs:
            _, hold = split_masks(Mk["d"], spec.h, self.split)
            mom = self.moments.get((spec.fid, spec.target))
            series, _ = self._market_split(Mk.loc[hold].reset_index(drop=True), spec, mom) if mom else ({}, None)
            for r in byspec[(spec.fid, spec.target)]:
                t, _ = series.get(r["cell"], (None, None))
                self._hold_row(spec, r, t, None)
        return self.holdout

    def _hold_spec(self, item):
        spec, rows = item
        _, hold = self._masks(spec.h)
        fr = self._frame(spec, hold)
        k = ("xs-hold", spec.h)
        if k not in self.cache:
            self.cache[k] = self._prep(fr)
        series = self._xs_split(fr, spec, self.cache[k])
        out = []
        for r in rows:
            r = {k2: v for k2, v in r.items() if k2 != "_score"}
            t, ud = series.get(r["cell"], (None, None))
            self._hold_row(spec, r, t, ud)
            out.append(r)
        return out

    def _hold_row(self, spec, r, t, ud):
        if r["status"] != "tested":
            r["verdict"] = "untested"
            return
        if t is None or len(t) < MIN_DATES or int(t.n.sum()) < MIN_OBS:
            r["hold_dates"] = 0 if t is None else len(t)
            r["verdict"] = "holdout-insufficient" if r["bh"] and r["wf"]["pass"] else self._pre_verdict(r)
            return
        s = t.s.to_numpy(float)
        st = _stats(s, spec.h)
        sg = r["sign"]
        r.update(hold_dates=len(t), hold_obs=int(t.n.sum()), hold_mean=st["mean"], hold_t=st["t_block"],
                 hold_t_nw=st["t_nw"])
        r["hold_signed"] = sg * st["mean"]
        r["hold_t_signed"] = None if st["t_block"] is None else sg * st["t_block"]
        if spec.lane == "xs" and is_vol(spec.target):
            r["execution_net"] = None
            r["capacity_note"] = "volatility target: sizing and options routes, not a stock direction trade"
        elif spec.lane == "xs":
            net, nopp, cap = _net_series(t, sg, spec.binary)
            ok = np.isfinite(net)
            r["execution_net"] = float(np.mean(net[ok])) if ok.any() else None
            r["net_t"] = S.block_t(net[ok], spec.h)["t"] if ok.sum() > 3 else None
            r["n_opportunities"] = int(np.nansum(nopp))
            capd = cap[np.isfinite(cap)] * spec.h
            r["capacity_usd"] = float(np.median(capd)) if len(capd) else None
            r["capacity_note"] = CP.note(r["capacity_usd"])
        elif spec.target.startswith("spy_ret"):
            pos = np.sign(t.z.to_numpy()) * sg
            r["execution_net"] = float(np.mean(pos * t.y.to_numpy()) - 2 * INDEX_COST)
            r["capacity_note"] = "SPY: capacity not binding"
        else:
            r["execution_net"] = None
            r["capacity_note"] = "volatility target: options routes, forward-only (FACTORY §4.10)"
        r["verdict"] = self._verdict(r)

    def _pre_verdict(self, r):
        if not r["bh"]:
            return "null-overall"
        if not r["wf"]["pass"]:
            return "wf-failed"
        return "holdout-insufficient"

    def _verdict(self, r):
        hs, ht = r.get("hold_signed"), r.get("hold_t_signed")
        if ht is not None and ht <= -HOLD_T:
            return "sign-flip"
        if not r["bh"]:
            return "null-overall"
        if not r["wf"]["pass"]:
            return "wf-failed"
        dm = abs(r["disc_mean"])
        if not (ht is not None and ht >= HOLD_T and hs >= HOLD_FRAC * dm):
            return "holdout-failed"
        net = r.get("execution_net")
        if (r["lane"] == "xs" and not is_vol(r["target"])) or r["target"].startswith("spy_ret"):
            if net is None or net <= 0:
                return "cost-failed"
        if r.get("capacity_usd") is not None and r["capacity_usd"] < CP.TINY_USD:
            return "tiny"
        return "promoted-B"

    def execute(self):
        self.discovery()
        self.bh()
        self.open_holdout()
        return self.report()

    def report(self):
        rows = []
        for r in self.rows:
            d = {k: v for k, v in r.items() if k != "_score"}
            rows.append(d)
        counts = {}
        for r in rows:
            counts[r.get("verdict", "untested")] = counts.get(r.get("verdict", "untested"), 0) + 1
        return {"search_version": SEARCH_VERSION, "split": self.split, "wf_unit": self.wf_unit, "embargo_days_min": EMBARGO_DAYS, "q": Q,
                "min_dates": MIN_DATES, "min_obs": MIN_OBS, "cells_total": len(rows),
                "cells_tested": self.m, "cells_untested": sum(1 for r in rows if r["status"] == "untested"),
                "bh_pass": sum(1 for r in rows if r.get("bh")), "verdicts": counts, "holdout": self.holdout,
                "rows": rows}
