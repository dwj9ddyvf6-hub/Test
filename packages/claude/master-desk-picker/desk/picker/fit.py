"""Fit the Fear-Day Buy List's thresholds on discovery data, freeze them, test them once on the holdout (UNI-04).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module; tools-free CLI `python -m desk.picker.fit` (reads the price panels, writes the frozen fit file
            config/picker/fearday_fit.json and the numbers the report docs/research/picker-fit-2026-10-27.md quotes).
  Constraints  point in time: every candidate row is fearday.frame_df's row i (bars 0..i only), the market state is the
            picker's own rule, the tiers are the day's cross-section, the vetoes are the scalar functions' vectorised
            twins (tests/test_picker_fit.py proves parity); entry at the next open, exit by the plan (time exit at the
            close of the session `hold` after the decision day, or a disaster stop at `stop_atr` x ATR under the close,
            filled at the stop or at the open on a gap through); net of the picker's own cost model (Corwin-Schultz
            spread + 2 x impact); discovery = decisions whose label ends 45 calendar days before 2023-01-01, holdout =
            decisions from 2023-01-01. The holdout is read once, after the parameters are frozen from discovery.
            Sleeves are never touched.
  Outcome   per parameter group (weights, hold, stop, risk) a fitted value or a pooled one, with the discovery numbers,
            the holdout comparison against the provisional value, and a status the holdout decides.
  Proof     tests/test_picker_fit.py (vector/scalar parity, known-answer stop and time exits, the embargo rule, the
            freeze hash); the report quotes the run.
  Edges     reverse splits are not available in the panels (that veto reads no_data, as live without a split source);
            names that stop trading before the horizon exit at their last close (counted); the VIX is not passed to the
            market state (SPY only); the veto thresholds, the fear rule and the state definitions are not refitted
            (their discovery studies are cited and they stay provisional)."""
import hashlib
import json
import math
import os

import numpy as np
import pandas as pd

from . import fearday as F
from . import model as M

HOLDS = (10, 20, 30, 40, 60, 75, 90, 120)
STOPS = (None, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0)        # ATR multiples under the close; None = no stop
START = "2017-01-03"                    # the first decision day: a year of history for every rolling window
SPLIT = "2023-01-01"                    # holdout start
EMBARGO_DAYS = M.EMBARGO_DAYS           # 45 calendar days between a discovery label's end and the holdout start
FEATS = ("F3", "N1", "N7", "MOM126", "F7", "F6", "N5")
STATE_CODE = {"UP": 1, "RESET": 2}
SIGNS = {"UP": {"F3": 1, "N1": 1, "N7": 1, "MOM126": 1}, "RESET": {"F7": -1, "F6": 1, "N5": -1}}
TIER_GROUPS = {"thin": (1, 2), "mid": (3,), "liquid": (4, 5)}
N_FLOOR_DATES = 60                      # the Factory bar's forward dates (forward_tests/README): a group needs this many
N_FLOOR_PICKS = 300                     # fear dates and this many picks before it may carry its own value
T_ADOPT = 2.0                           # a fitted value must beat the provisional one by this clustered t on discovery
GROUPS_TESTED = 5                       # buy, watch, thin, mid, liquid: a group's own value needs the Bonferroni t
T_GROUP = 2.5758293035489004            # two-sided 0.05 / GROUPS_TESTED, the normal quantile (math: statistics.NormalDist)
LANE_ORDER = ("buy", "watch", "small")


# ------------------------------------------------------------------------------------------------ market state, by date
def spy_days(spy_close, params=None):
    """per-session market state from SPY's closes (a Series indexed by ISO date), the vectorised twin of
    fearday.market_state: DataFrame(fear, bull, spy_ok, ret) indexed like the input"""
    p = params or F.CONFIG
    fp, bp = p["fear"], p["bull"]
    s = spy_close.astype(float)
    r = s.pct_change()
    ma = s.rolling(fp["below_ma"]).mean()
    vol = r.rolling(fp["vol_window"]).std()
    med = vol.rolling(fp["vol_median_window"], min_periods=fp["vol_median_window"] // 2).median()
    fear = (r <= fp["spy_drop"]) | ((s < ma) & ma.notna()) | ((vol > fp["vol_spike_mult"] * med) & med.notna())
    m200 = s.rolling(bp["ma"]).mean()
    then = m200.shift(bp["rising_lookback"])
    bull = ((s > m200) & (m200 > then)).where(then.notna())
    vm = s.rolling(p["vetoes"]["off_below_spy_ma"]).mean()
    ok = ~((vm.notna()) & (s < vm))
    return pd.DataFrame({"fear": fear.fillna(False).astype(bool), "bull": bull, "spy_ok": ok, "ret": r})


# ------------------------------------------------------------------------------------------------ vectorised vetoes
def veto_columns(fr, params=None):
    """the avoid study's signals as whole-history columns of the name's frame (fearday.frame_df): a DataFrame of
    float (1 fired, 0 not, NaN no data) for the signals that do not need the tier, plus the two nano conditions
    (pump_raw, mfi_raw) the caller ANDs with tier 1, plus bad (the bad-print guard)"""
    p = params or F.CONFIG
    vp = p["vetoes"]
    n = len(fr)
    idx = np.arange(n)
    c, v, r = fr["c"], fr["v"], fr["r"]
    out = pd.DataFrame(index=fr.index)
    out["new_listing"] = ((idx + 1) < vp["new_listing"]["sessions"]).astype(float)
    sp = vp["spike_day"]
    out["spike_day"] = (r >= sp["day"]).astype(float).rolling(sp["window"], min_periods=1).max()
    dc = vp["dead_cat"]
    hi = c.rolling(dc["high_window"], min_periods=dc["high_window"]).max()
    r5 = c / c.shift(dc["bounce_days"]) - 1
    out["dead_cat"] = ((c <= dc["of_high"] * hi) & (r5 >= dc["bounce"])).astype(float).where(idx >= dc["high_window"])
    out["far_above_50d"] = (c >= vp["far_above_50d"]["mult"] * fr["m50"]).astype(float).where(fr["m50"].notna())
    out["stretched"] = ((c / fr["m50"] - 1) >= vp["stretched"]["above_50d"]).astype(float).where(fr["m50"].notna())
    ip = vp["idio_decline"]
    out["idio_decline"] = ((fr["r5"] <= ip["r5"]) & (fr["F4"] >= ip["share"])).astype(float).where(
        fr["F4"].notna() & fr["r5"].notna())
    sg = vp["surge"]
    vmed = v.shift(1).rolling(sg["vol_median"], min_periods=10).median()
    hit = ((r.abs() >= sg["move"]) & (v >= sg["vol_mult"] * vmed)).astype(float)
    out["surge"] = (hit.rolling(sg["window"], min_periods=1).sum() >= sg["days"]).astype(float)
    pn = vp["pump_nano"]
    m = v.shift(1).rolling(pn["vol_median"], min_periods=10).median()
    out["pump_raw"] = ((fr["r5"] >= pn["r5"]) & (m > 0) & (v >= pn["vol_mult"] * m)).astype(float)
    out["mfi_raw"] = (F.mfi(fr, vp["mfi_nano"]["n"]) >= vp["mfi_nano"]["mfi"]).astype(float)
    bp = p["bad_print"]
    jump = c / c.shift(1)
    vm20 = v.shift(1).rolling(bp["vol_median"], min_periods=1).median()
    bad = (((jump > bp["up"]) | (jump < bp["down"])) & ~(v > bp["vol_mult"] * vm20)).astype(float)
    out["bad"] = bad.rolling(bp["window"], min_periods=1).max()
    return out


# ------------------------------------------------------------------------------------------------ outcomes of a plan
def simulate(o, l, c, i, atr, stops, holds, ended):
    """gross open-to-exit returns of buying the next open after decision rows `i` (positions in the name's arrays o, l,
    c): array (len(i), len(stops), len(holds)) of returns and of exit offsets (sessions after the entry session; -1 for
    not closed). stop level = close[i] - s x atr[i] (s None: no stop); a session whose low is at or under it sells at the
    stop, or at its open when it opened at or under it; otherwise the exit is the close of position i + hold. `ended`: the
    name stopped trading before the data did: an exit beyond its last bar uses the last close; else it is not closed."""
    i = np.asarray(i)
    nc, n = len(i), len(c)
    H = max(holds)
    ret = np.full((nc, len(stops), len(holds)), np.nan, dtype=np.float32)
    off = np.full((nc, len(stops), len(holds)), -1, dtype=np.int16)
    e = i + 1
    ok = e < n
    if not ok.any():
        return ret, off
    pad = H + 2
    nanp = np.full(pad, np.nan)
    lo = np.concatenate([l, nanp])
    op = np.concatenate([o, nanp])
    cl = np.concatenate([c, np.full(pad, c[-1] if ended else np.nan)])
    ee = np.where(ok, e, 0)
    win = np.lib.stride_tricks.sliding_window_view
    wl, wo = win(lo, H)[ee], win(op, H)[ee]
    entry = o[ee]
    ar = np.arange(nc)
    for si, s in enumerate(stops):
        if s is None:
            first = np.full(nc, 10 ** 6)
            stop_px = np.zeros(nc)
        else:
            stop_px = c[i] - s * atr
            hit = wl <= stop_px[:, None]
            first = np.where(hit.any(axis=1), hit.argmax(axis=1), 10 ** 6)
        sx = np.minimum(wo[ar, np.minimum(first, H - 1)], stop_px) if s is not None else np.zeros(nc)
        for hi_, h in enumerate(holds):
            tpos = i + h                                  # the time exit's position in the name's bars
            tj = h - 1                                    # ... as an offset from the entry session
            px_t = cl[np.minimum(tpos, n + pad - 1)]
            stopped = first <= tj
            px = np.where(stopped, sx, px_t)
            r_ = px / entry - 1
            good = ok & np.isfinite(r_) & (entry > 0)
            ret[good, si, hi_] = r_[good]
            off[good, si, hi_] = np.where(stopped, first, tj)[good]
    return ret, off


# ------------------------------------------------------------------------------------------------ the per-name table
def name_rows(g, spy_close, days, p, didx, last_di, n_days):
    """candidate rows of one name over its whole history: DataFrame, plus its dollar-volume column over the master
    calendar (for the day's tiers) and the simulated outcomes. g: the name's DataFrame (d, o, h, l, c, v)"""
    fr = F.frame_df(g, spy_close, p)
    vc = veto_columns(fr, p)
    di = g["d"].map(didx).to_numpy(dtype="float64")                  # master calendar index, NaN when off-calendar
    dv_full = np.full(n_days, np.nan, dtype=np.float32)
    okd = np.isfinite(di)
    badp = (vc["bad"].to_numpy() > 0)
    dvv = fr["dv20"].to_numpy()
    dv_full[di[okd & ~badp].astype(int)] = dvv[okd & ~badp]
    fear = np.zeros(len(g), bool)
    fear[okd] = days["fear"].to_numpy()[di[okd].astype(int)]
    st = fr["state"].map({"UP": 1, "RESET": 2}).fillna(0).to_numpy()
    pos = np.where(okd & fear & (st > 0) & ~badp & (g["d"].to_numpy() >= START))[0]
    if not len(pos):
        return None, dv_full
    sub = fr.iloc[pos]
    ended = last_di < n_days - 6
    ret, off = simulate(g["o"].to_numpy(), g["l"].to_numpy(), g["c"].to_numpy(), pos, sub["atr"].to_numpy(), STOPS, HOLDS,
                        ended)
    t = pd.DataFrame({"di": di[pos].astype(np.int16), "st": st[pos].astype(np.int8),
                      "nwarn": vc[["new_listing", "spike_day", "dead_cat", "far_above_50d"]].iloc[pos].fillna(0).sum(axis=1)
                      .to_numpy(), "npen": vc[["stretched", "idio_decline", "surge"]].iloc[pos].fillna(0).sum(axis=1)
                      .to_numpy(), "pump_raw": vc["pump_raw"].iloc[pos].to_numpy(), "mfi_raw": vc["mfi_raw"].iloc[pos]
                      .to_numpy(), "close": sub["c"].to_numpy(), "atr": sub["atr"].to_numpy(), "vol20": sub["vol20"]
                      .to_numpy(), "dv20": sub["dv20"].to_numpy(), "cs": sub["cs"].to_numpy(),
                      "edi": np.where(pos + 1 < len(g), di[np.minimum(pos + 1, len(g) - 1)], np.nan)})
    for k in FEATS:
        t[k] = sub[k].to_numpy()
    return (t, ret, off), dv_full


def build(bars, spy_close, params=None, log=print):
    """-> (T, RET, OFF, tiers, days): the candidate table over every name. bars: DataFrame(sid, d, o, h, l, c, v) with d
    an ISO string; spy_close: Series indexed by the ISO date"""
    p = params or F.CONFIG
    days = spy_days(spy_close, p)
    dates = list(days.index)
    didx = {d: k for k, d in enumerate(dates)}
    n_days = len(dates)
    DV = np.full((n_days, bars["sid"].nunique()), np.nan, dtype=np.float32)
    parts, rets, offs = [], [], []
    bars = bars.sort_values(["sid", "d"], kind="stable")
    sids = bars["sid"].to_numpy()
    cut = np.flatnonzero(np.r_[True, sids[1:] != sids[:-1], True])
    for k in range(len(cut) - 1):
        g = bars.iloc[cut[k]:cut[k + 1]].drop_duplicates("d", keep="last").reset_index(drop=True)
        if len(g) < 260:
            continue
        last_di = didx.get(g["d"].iloc[-1], n_days - 1)
        got, dv = name_rows(g, spy_close, days, p, didx, last_di, n_days)
        DV[:, k] = dv
        if got is not None:
            t, ret, off = got
            t["nm"] = np.int32(k)
            parts.append(t)
            rets.append(ret)
            offs.append(off)
        if k % 500 == 0:
            log(f"  names {k}/{len(cut) - 1}, candidate rows {sum(len(x) for x in parts):,}")
    T = pd.concat(parts, ignore_index=True)
    rank = pd.DataFrame(DV).rank(axis=1, pct=True)
    q = p["tiers"]["quintiles"]
    tier = np.ceil(rank.to_numpy() * q).clip(max=q)
    T["tier"] = tier[T["di"].to_numpy().astype(int), T["nm"].to_numpy()]
    return T, np.concatenate(rets), np.concatenate(offs), days


# ------------------------------------------------------------------------------------------------ the list, vectorised
def prepare(T, days, p=None):
    """add what the veto and the ranks need: the tier-dependent vetoes, the drop, the penalty count and the within-state
    percentile ranks of each signed feature -> the kept rows (index into T) as a DataFrame"""
    p = p or F.CONFIG
    vp = p["vetoes"]
    spy_ok = days["spy_ok"].to_numpy()[T["di"].to_numpy().astype(int)]
    nano = np.isin(T["tier"].to_numpy(), vp["nano_tiers"])
    nw = T["nwarn"].to_numpy() + (nano & (T["pump_raw"].to_numpy() > 0)) + (nano & (T["mfi_raw"].to_numpy() > 0))
    npn = T["npen"].to_numpy()
    fired = np.where(spy_ok, nw + npn, 0)
    pen = np.where(spy_ok, nw * vp["warning_penalty"] + npn * vp["penalty"], 0.0)
    drop = fired >= vp["drop_at"]
    K = T.loc[~drop].copy()
    K["pen"] = np.where(drop, 0.0, pen)[~drop]
    K["row"] = np.flatnonzero(~drop)
    K["g"] = K["di"].astype(np.int64) * 10 + K["st"].astype(np.int64)
    for st_name, signs in SIGNS.items():
        m = K["st"].to_numpy() == STATE_CODE[st_name]
        for k, sg in signs.items():
            K.loc[m, "rk_" + k] = (sg * K.loc[m, k]).groupby(K.loc[m, "g"]).rank(pct=True)
    return K


def lane_groups(K, p=None):
    """lane id per kept row: 1 buy (UP, not thin), 2 watch (RESET, not thin), 3 small (thin tiers, both states); the
    group id (a date and a lane) the top N are taken in"""
    p = p or F.CONFIG
    thin = np.isin(K["tier"].to_numpy(), p["tiers"]["small_lane"])
    lane = np.where(thin, 3, np.where(K["st"].to_numpy() == 1, 1, 2))
    return lane, K["di"].to_numpy().astype(np.int64) * 10 + lane


def scores(K, weights, pen_scale=1.0, tier_w=None):
    """score = |w|-weighted mean of the available ranks - pen_scale x penalty. weights {"UP": {feat: w}, "RESET": {...}}
    (magnitudes); tier_w {state: {group: {feat: w}}} overrides it for the rows whose tier is in the group"""
    sc = np.full(len(K), np.nan)
    tier = K["tier"].to_numpy()
    for st_name, signs in SIGNS.items():
        m0 = K["st"].to_numpy() == STATE_CODE[st_name]
        variants = [(m0, weights[st_name])]
        if tier_w and st_name in tier_w:
            variants = []
            for gname, ts in TIER_GROUPS.items():
                m = m0 & np.isin(tier, ts)
                variants.append((m, (tier_w[st_name].get(gname) or weights[st_name])))
        for m, w in variants:
            if not m.any():
                continue
            R = np.column_stack([K["rk_" + k].to_numpy()[m] for k in signs])
            a = np.array([abs(w.get(k, 0.0)) for k in signs])
            av = np.isfinite(R)
            num = np.where(av, R, 0.0) @ a
            den = av @ a
            with np.errstate(invalid="ignore", divide="ignore"):
                sc[m] = np.where(den > 0, num / den, np.nan)
    return sc - pen_scale * K["pen"].to_numpy()


def top_n(K, sc, n, gid):
    """boolean array over K: the row is in the top n of its group by (-score, -dv20, name); NaN scores are not cards"""
    ok = np.isfinite(sc)
    idx = np.flatnonzero(ok)
    order = np.lexsort((K["nm"].to_numpy()[idx], -K["dv20"].to_numpy()[idx], -sc[idx], gid[idx]))
    idx = idx[order]
    g = gid[idx]
    start = np.r_[True, g[1:] != g[:-1]]
    first = np.maximum.accumulate(np.where(start, np.arange(len(g)), 0))
    keep = (np.arange(len(g)) - first) < n
    out = np.zeros(len(K), bool)
    out[idx[keep]] = True
    return out


# ------------------------------------------------------------------------------------------------ net returns
def net_returns(K, T_ret, T_off, spy_o, spy_c, plan, risk_pct=None, book=None, stop=None, hold=None, p=None):
    """-> DataFrame(net, spy, cost, w) per kept row for the plan {hold, stop_atr} at risk_pct: net = gross - cost
    (the picker's cost: spread + 2 x impact_k x vol x sqrt(size / dv)); spy = SPY's open-to-close over the same days"""
    p = p or F.CONFIG
    pp = p["plan"]
    risk_pct = pp["risk_pct"] if risk_pct is None else risk_pct
    hold = plan["hold"] if hold is None else hold
    stop = plan["stop_atr"] if stop is None else stop
    si, hi = STOPS.index(stop), HOLDS.index(hold)
    rows = K["row"].to_numpy()
    gross = np.clip(T_ret[rows, si, hi].astype(float), -1.0, 5.0)         # the study's clip: one print is not a result
    off = T_off[rows, si, hi].astype(int)
    vol = K["vol20"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        w = np.minimum(risk_pct / (vol * math.sqrt(hold)), pp["max_weight_pct"])
        size = w / 100.0 * (pp["book_usd"] if book is None else book)
        impact = pp["impact_k"] * vol * np.sqrt(size / K["dv20"].to_numpy())
    cs = np.nan_to_num(K["cs"].to_numpy())
    cost = cs + 2 * impact
    e = K["edi"].to_numpy()
    x = np.where(np.isfinite(e) & (off >= 0), np.minimum(e + off, len(spy_c) - 1), np.nan)    # a name that stopped trading: SPY to the data's end
    with np.errstate(invalid="ignore"):
        s_ret = spy_c[np.nan_to_num(x, nan=0).astype(int)] / spy_o[np.nan_to_num(e, nan=0).astype(int)] - 1
    s_ret = np.where(np.isfinite(x), s_ret, np.nan)
    return pd.DataFrame({"net": gross - cost, "gross": gross, "spy": s_ret, "cost": cost, "w": w, "off": off},
                        index=K.index)


# ------------------------------------------------------------------------------------------------ split and statistics
def label_end_ok(di, off_sessions, dates, split=SPLIT, embargo=EMBARGO_DAYS):
    """a discovery row's label must end (calendar) at least `embargo` days before the split: boolean per row. di: the
    decision day's index in dates; off_sessions: sessions to the exit from the entry (approximate end = dates[di + 1 +
    off])"""
    cut = (pd.Timestamp(split) - pd.Timedelta(days=embargo)).strftime("%Y-%m-%d")
    dts = np.array(dates)
    end = np.minimum(np.asarray(di, dtype=int) + 1 + np.asarray(off_sessions, dtype=int), len(dts) - 1)
    return dts[end] <= cut


def clustered(values, clusters):
    """(mean, t, n_clusters): the event-weighted mean of `values` and its t with the standard error clustered by date, the
    composite study's ct(): se = sqrt(sum over clusters of (sum of (e - mean))^2) / N"""
    e = np.asarray(values, float)
    cl = np.asarray(clusters)
    m = np.isfinite(e)
    e, cl = e[m], cl[m]
    n = len(e)
    if n < 2:
        return float("nan"), float("nan"), 0
    mu = e.mean()
    sums = pd.Series(e - mu).groupby(cl).sum()
    se = math.sqrt(float((sums ** 2).sum())) / n
    return float(mu), float(mu / se) if se > 0 else float("nan"), int(len(sums))


def freeze_hash(obj):
    """the content hash of a JSON-able object: sha256 of its canonical text (sorted keys, no spaces)"""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


FIT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "picker",
                        "fearday_fit.json")


# ------------------------------------------------------------------------------------------------ the fitting context
class Ctx:
    """the candidate table with everything the fit reads: K (kept rows), the lane of each, outcomes and SPY"""

    def __init__(self, T, RET, OFF, days, spy_o, spy_c, p=None):
        self.p = p or F.CONFIG
        self.dates = np.array(list(days.index))
        self.days = days
        self.T, self.RET, self.OFF = T, RET, OFF
        self.K = prepare(T, days, self.p)
        self.lane, self.gid = lane_groups(self.K, self.p)
        self.spy_o, self.spy_c = np.asarray(spy_o, float), np.asarray(spy_c, float)
        self.di = self.K["di"].to_numpy().astype(int)
        self.date = self.dates[self.di]
        self.cut = (pd.Timestamp(SPLIT) - pd.Timedelta(days=EMBARGO_DAYS)).strftime("%Y-%m-%d")
        self._net = {}

    def net(self, hold, stop, risk=None):
        key = (hold, stop, risk)
        if key not in self._net:
            n = net_returns(self.K, self.RET, self.OFF, self.spy_o, self.spy_c, {"hold": hold, "stop_atr": stop},
                            risk_pct=risk, p=self.p)
            n["excess_spy"] = n["net"] - n["spy"]
            ok = np.isfinite(n["net"].to_numpy()) & np.isfinite(n["spy"].to_numpy())
            end_ok = label_end_ok(self.di, np.maximum(n["off"].to_numpy(), 0), list(self.dates))
            n["disc"] = ok & end_ok & (self.date < SPLIT)
            n["hold_"] = ok & (self.date >= SPLIT)
            self._net = {key: n}                    # one plan at a time: the arrays are large
        return self._net[key]

    def net_choice(self, choice, risk=None):
        """net() for a choice {"hold", "stop_atr", "hold_by": {"lane:buy" | "tier:liquid": hold}}: each row gets its own
        group's hold (the lane's before the tier's), the rest the pooled one. The columns are those of net()"""
        stop = choice["stop_atr"]
        hold = np.full(len(self.K), choice["hold"])
        tier = self.K["tier"].to_numpy()
        for key, h in (choice.get("hold_by") or {}).items():
            kind, name = key.split(":")
            m = (self.lane == {v: k for k, v in GROUP_LANES.items()}[name]) if kind == "lane" else np.isin(tier, TIER_GROUPS[name])
            hold = np.where(m, h, hold)
        out = None
        for h in sorted(set(hold.tolist())):
            n = self.net(int(h), stop, risk).copy()
            if out is None:
                out = n
            else:
                m = hold == h
                out.loc[m] = n.loc[m]
        return out

    def picks(self, weights, n=20, pen_scale=1.0, tier_w=None):
        sc = scores(self.K, weights, pen_scale, tier_w)
        return top_n(self.K, sc, n, self.gid), sc


def pick_table(ctx, picks, net, period):
    """per pick of the period: lane, date index, net, excess over the lane-day pool's mean, excess over SPY"""
    ok = net[period].to_numpy() if isinstance(period, str) else np.asarray(period)
    ok = ok & np.isfinite(net["net"].to_numpy())
    pool = pd.Series(net["net"].to_numpy()[ok]).groupby(ctx.gid[ok]).mean()
    sel = picks & ok
    t = pd.DataFrame({"lane": ctx.lane[sel], "di": ctx.di[sel], "tier": ctx.K["tier"].to_numpy()[sel],
                      "st": ctx.K["st"].to_numpy()[sel], "net": net["net"].to_numpy()[sel],
                      "ex_spy": net["excess_spy"].to_numpy()[sel], "cost": net["cost"].to_numpy()[sel],
                      "gross": net["gross"].to_numpy()[sel]})
    t["ex_pool"] = t["net"] - pool.reindex(ctx.gid[sel]).to_numpy()
    return t


def summarise(t, col, by=None):
    """mean (in %), date-clustered t, picks and dates of column `col`; by: a list of columns to group on"""
    def one(x):
        m, tt, nd = clustered(x[col].to_numpy(), x["di"].to_numpy())
        return {"n": int(len(x)), "dates": nd, "mean_pct": round(100 * m, 3) if m == m else None,
                "t": round(tt, 2) if tt == tt else None, "net_pct": round(100 * float(x["net"].mean()), 3)}
    if by is None:
        return one(t) if len(t) else {"n": 0, "dates": 0, "mean_pct": None, "t": None, "net_pct": None}
    return {str(k): one(g) for k, g in t.groupby(by)}


# ------------------------------------------------------------------------------------------------ weights
def learn_weights(ctx, state, train, lam, y_net):
    """non-negative ridge weights of the state's signed ranks on the within-day net return (demeaned inside the
    state-day group), over the rows `train` (boolean over K). y_net: net return per K row. -> {feature: weight}, summing
    to the number of features (only ratios matter)"""
    from scipy.optimize import nnls
    feats = list(SIGNS[state])
    m = train & (ctx.K["st"].to_numpy() == STATE_CODE[state]) & np.isfinite(y_net)
    g = ctx.K["g"].to_numpy()[m]
    y = pd.Series(np.clip(y_net[m], -1, 5))
    y = (y - y.groupby(g).transform("mean")).to_numpy()
    lo, hi = np.percentile(y, [0.5, 99.5])
    y = np.clip(y, lo, hi)
    cols = []
    for k in feats:
        r = pd.Series(ctx.K["rk_" + k].to_numpy()[m])
        cols.append((r - r.groupby(g).transform("mean")).fillna(0.0).to_numpy())
    A = np.column_stack(cols)
    A2 = np.vstack([A, np.sqrt(lam * len(y)) * np.eye(len(feats))])
    b2 = np.concatenate([y, np.zeros(len(feats))])
    w, _ = nnls(A2, b2)
    if w.sum() <= 0:
        return {k: 1.0 for k in feats}
    w = w / w.sum() * len(feats)
    return {k: float(x) for k, x in zip(feats, w)}


def lane_excess(ctx, weights, lane, n=20, period="disc", hold=60, stop=3.0, mask=None, tier_w=None):
    """the pick-minus-pool table of one lane for the weights and plan, over the period's rows"""
    pk, _ = ctx.picks(weights, n, tier_w=tier_w)
    net = ctx.net(hold, stop)
    t = pick_table(ctx, pk & (ctx.lane == lane) if mask is None else pk & (ctx.lane == lane) & mask, net,
                   {"disc": "disc", "hold": "hold_"}[period])
    return t


def walk_forward_weights(ctx, state, lams, years, hold=60, stop=3.0, shrink=(0.0, 0.5, 1.0), log=print):
    """expanding walk-forward inside discovery: for each test year the weights are learned on rows whose label ends 45
    days before the year, then the year's top-20 are scored. -> {(lam, shrink): table of the test years' picks,
    'equal': table}. shrink s blends learned weights with equal ones: w = (1 - s) x equal + s x learned"""
    lane = 1 if state == "UP" else 2
    net = ctx.net(hold, stop)
    y_net = net["net"].to_numpy()
    di_date = ctx.date
    end_ok = label_end_ok(ctx.di, np.maximum(net["off"].to_numpy(), 0), list(ctx.dates), split="%d-01-01" % years[0])
    out = {}
    base = {s: {k: 1.0 for k in v} for s, v in SIGNS.items()}
    eq_tabs = []
    res = {(lam, sh): [] for lam in lams for sh in shrink}
    for y in years:
        cut = f"{y}-01-01"
        cutb = (pd.Timestamp(cut) - pd.Timedelta(days=EMBARGO_DAYS)).strftime("%Y-%m-%d")
        ends = np.array(ctx.dates)[np.minimum(ctx.di + 1 + np.maximum(net["off"].to_numpy(), 0), len(ctx.dates) - 1)]
        train = (ends <= cutb) & (di_date >= X_START_TRAIN)
        test = (di_date >= cut) & (di_date < f"{y + 1}-01-01")
        tn = net["disc"].to_numpy()
        for lam in lams:
            lw = learn_weights(ctx, state, train & tn, lam, y_net)
            for sh in shrink:
                w = {k: (1 - sh) * 1.0 + sh * lw[k] for k in lw}
                W = dict(base, **{state: w})
                t = lane_excess(ctx, W, lane, 20, "disc", hold, stop, mask=test)
                res[(lam, sh)].append(t.assign(year=y))
        t = lane_excess(ctx, base, lane, 20, "disc", hold, stop, mask=test)
        eq_tabs.append(t.assign(year=y))
    out = {k: pd.concat(v) for k, v in res.items()}
    out["equal"] = pd.concat(eq_tabs)
    return out


X_START_TRAIN = START


def paired(a, b, col):
    """(difference in %, t, dates): the event-weighted mean of `col` in table a minus table b, with the standard error
    clustered by date over both tables' events (the two sets share dates, not picks)"""
    ea, eb = a[col].to_numpy(float), b[col].to_numpy(float)
    ma, mb = np.isfinite(ea), np.isfinite(eb)
    if ma.sum() < 2 or mb.sum() < 2:
        return float("nan"), float("nan"), 0
    ea, eb = ea[ma], eb[mb]
    da, db = a["di"].to_numpy()[ma], b["di"].to_numpy()[mb]
    mua, mub = ea.mean(), eb.mean()
    ca = pd.Series((ea - mua) / len(ea)).groupby(da).sum()
    cb = pd.Series((eb - mub) / len(eb)).groupby(db).sum()
    c = ca.sub(cb, fill_value=0.0)
    se = math.sqrt(float((c ** 2).sum()))
    d = mua - mub
    return float(100 * d), float(d / se) if se > 0 else float("nan"), int(len(c))


# ------------------------------------------------------------------------------------------------ hold and stop
PROVISIONAL = {"hold": 60, "stop_atr": 3.0, "risk_pct": 1.0}


def plan_tables(ctx, picks, lanes=(1, 2, 3), holds=HOLDS, stops=STOPS):
    """{(hold, stop): pick table} over the common discovery sample (rows whose label ends before the embargo for every
    hold in the grid, so the choices are compared on the same picks)"""
    common = np.ones(len(ctx.K), bool)
    for h in holds:
        common &= ctx.net(h, None)["disc"].to_numpy()
    sel = picks & np.isin(ctx.lane, lanes)
    out = {}
    for h in holds:
        for s in stops:
            out[(h, s)] = pick_table(ctx, sel, ctx.net(h, s), common)
    return out, int(common.sum())


def best_hold(tabs, holds=HOLDS, col="ex_spy", provisional=PROVISIONAL, where=None):
    """-> {"best", "chosen", "t_vs_provisional", "grid"}: the hold with the highest date-clustered t of `col` at no stop;
    it replaces the provisional hold only when it beats it by a paired t of T_ADOPT (else the provisional value stays)"""
    def sub(t):
        return t if where is None else t[where(t)]
    grid = {h: summarise(sub(tabs[(h, None)]), col) for h in holds}
    best = max(holds, key=lambda h: grid[h]["t"] if grid[h]["t"] is not None else -9)
    d, t, _ = paired(sub(tabs[(best, None)]), sub(tabs[(provisional["hold"], None)]), col)
    chosen = best if (best != provisional["hold"] and t == t and t >= T_ADOPT and d > 0) else provisional["hold"]
    return {"best": best, "chosen": chosen, "diff_pp": None if d != d else round(d, 3),
            "t_vs_provisional": None if t != t else round(t, 2), "grid": grid}


def best_stop(tabs, hold, stops=STOPS, col="ex_spy", where=None):
    """-> the tightest finite stop whose discovery cost against no stop is not significant (paired t of none minus stop
    below T_ADOPT); None when every finite stop in the grid costs significantly more (a plan that wants no stop at all).
    {"chosen", "grid": {stop: {mean, t, vs_none_t}}}"""
    def sub(t):
        return t if where is None else t[where(t)]
    none = sub(tabs[(hold, None)])
    grid, chosen = {}, None
    for s in sorted(x for x in stops if x is not None):
        tb = sub(tabs[(hold, s)])
        d, t, _ = paired(none, tb, col)
        grid[s] = dict(summarise(tb, col), cost_vs_none_pp=None if d != d else round(d, 3),
                       t_cost=None if t != t else round(t, 2))
        if chosen is None and t == t and t < T_ADOPT:
            chosen = s
    grid["none"] = summarise(none, col)
    return {"chosen": chosen, "grid": grid}


# ------------------------------------------------------------------------------------------------ the groups
LANE_NAME = {1: "buy", 2: "watch", 3: "small"}
GROUP_LANES = {1: "buy", 2: "watch"}                            # the small lane is the thin tier group's rows
TIER_WHERE = {g: (lambda ts: (lambda t: np.isin(t["tier"].to_numpy(), ts)))(ts) for g, ts in TIER_GROUPS.items()}
LANE_WHERE = {n: (lambda ln: (lambda t: t["lane"].to_numpy() == ln))(ln) for ln, n in GROUP_LANES.items()}


def group_support(tabs_one, where):
    """(dates, picks) a group has on the discovery sample: the n floor a group needs before it may carry its own value"""
    t = tabs_one[where(tabs_one)]
    return int(t["di"].nunique()), int(len(t))


def discover(ctx, log=print):
    """every choice, made on the discovery sample only -> a dict (JSON-able) with the chosen values and the numbers behind
    them. Nothing here reads a holdout row (Ctx.net's `hold_` column is never used in this function)"""
    equal = {s: {k: 1.0 for k in v} for s, v in SIGNS.items()}
    res = {"weights": {}, "plan": {}, "risk": {}, "penalty": {}}
    # weights: learned (non-negative ridge, walk-forward by year) against equal weights
    for state in ("UP", "RESET"):
        wf = walk_forward_weights(ctx, state, lams=(0.01, 0.1), years=(2019, 2020, 2021, 2022), shrink=(1.0,))
        rows = {}
        for k, v in wf.items():
            if k == "equal":
                continue
            d, t, nd = paired(v, wf["equal"], "ex_pool")
            rows[f"lam={k[0]}"] = {"learned": summarise(v, "ex_pool"), "minus_equal_pp": round(d, 3), "t": round(t, 2),
                                   "dates": nd}
        adopt = [k for k, r in rows.items() if r["t"] >= T_ADOPT and r["minus_equal_pp"] > 0]
        lane = 1 if state == "UP" else 2
        w_all = learn_weights(ctx, state, ctx.net(60, 3.0)["disc"].to_numpy(), 0.01, ctx.net(60, 3.0)["net"].to_numpy())
        res["weights"][state] = {"equal": summarise(wf["equal"], "ex_pool"), "learned_vs_equal": rows,
                                 "learned_on_all_discovery_lam0.01": {k: round(x, 3) for k, x in w_all.items()},
                                 "chosen": "equal" if not adopt else adopt[0], "lane": LANE_NAME[lane]}
        log(f"  weights {state}: {res['weights'][state]['chosen']}")
    W = {s: {k: 1.0 for k in v} for s, v in SIGNS.items()}
    # the penalty scale (every fired signal costs 0.1 of the score)
    for lane, state in ((1, "UP"), (2, "RESET")):
        tabs = {}
        for ps in (0.0, 1.0, 3.0, 10.0):
            pk, _ = ctx.picks(W, 20, pen_scale=ps)
            tabs[ps] = pick_table(ctx, pk & (ctx.lane == lane), ctx.net(60, None), "disc")
        res["penalty"][state] = {str(ps): dict(summarise(tb, "ex_pool"), vs_1_pp=round(paired(tb, tabs[1.0], "ex_pool")[0], 3),
                                               vs_1_t=round(paired(tb, tabs[1.0], "ex_pool")[1], 2))
                                 for ps, tb in tabs.items()}
    # hold and stop: pooled, then each lane and each tier group against the pooled value
    pk, _ = ctx.picks(W, 20)
    tabs, ncom = plan_tables(ctx, pk)
    res["plan"]["common_rows"] = ncom
    h = best_hold(tabs)
    stop = best_stop(tabs, h["chosen"])
    edge = max(s for s in STOPS if s is not None)
    chosen_stop = None if stop["chosen"] is None or stop["chosen"] >= edge else stop["chosen"]
    res["plan"]["hold"] = {"chosen": h["chosen"], "best": h["best"], "t_vs_provisional": h["t_vs_provisional"],
                           "grid": {str(k): v for k, v in h["grid"].items()}}
    res["plan"]["stop_atr"] = {"chosen": chosen_stop, "rule_chosen": stop["chosen"],
                               "grid": {str(k): v for k, v in stop["grid"].items()}}
    log(f"  hold {h['chosen']} (best {h['best']}), stop {chosen_stop}")
    groups = {}
    for name, where in list(LANE_WHERE.items()) + list(TIER_WHERE.items()):
        nd, npk = group_support(tabs[(60, None)], where)
        hh = best_hold(tabs, where=where)
        ss = best_stop(tabs, h["chosen"], where=where)
        # the group's own hold against the pooled one on the group's picks
        d, t, _ = paired(tabs[(hh["best"], None)][where(tabs[(hh["best"], None)])],
                         tabs[(h["chosen"], None)][where(tabs[(h["chosen"], None)])], "ex_spy")
        enough = nd >= N_FLOOR_DATES and npk >= N_FLOOR_PICKS
        own = bool(enough and hh["best"] != h["chosen"] and t == t and t >= T_GROUP and d > 0)
        groups[name] = {"dates": nd, "picks": npk, "floor_met": enough, "best_hold": hh["best"],
                        "best_vs_pooled_pp": None if d != d else round(d, 3), "t": None if t != t else round(t, 2),
                        "own_hold": hh["best"] if own else None, "grid_t": {str(k): v["t"] for k, v in hh["grid"].items()},
                        "stop_rule": ss["chosen"]}
    res["plan"]["groups"] = groups
    # risk: the growth of a book that sizes each pick at risk_pct / (vol x sqrt(hold)), capped, over the discovery picks
    sizes = {}
    pp = ctx.p["plan"]
    pk, _ = ctx.picks(W, 20)
    for r in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 8.0):
        net = ctx.net(h["chosen"], chosen_stop, r)
        sel = pk & net["disc"].to_numpy() & np.isfinite(net["net"].to_numpy())
        w, R = net["w"].to_numpy()[sel] / 100.0, net["net"].to_numpy()[sel]
        sizes[str(r)] = {"growth_per_pick": round(float(np.log1p(np.maximum(w * R, -0.999)).mean()), 6),
                         "mean_weight_pct": round(float(100 * w.mean()), 2),
                         "share_at_cap": round(float((net["w"].to_numpy()[sel] >= pp["max_weight_pct"] - 1e-9).mean()), 3)}
    g = [v["growth_per_pick"] for v in sizes.values()]
    res["risk"] = {"grid": sizes, "interior_optimum": bool(max(g) > g[-1] and max(g) > g[0] and g.index(max(g)) not in (0, len(g) - 1)),
                   "identified": False}
    res["risk"]["identified"] = res["risk"]["interior_optimum"]
    own_h = {n: g["own_hold"] for n, g in groups.items() if g["own_hold"]}
    res["choice"] = {"hold": h["chosen"], "stop_atr": chosen_stop, "risk_pct": PROVISIONAL["risk_pct"],
                     "weights": "equal", "hold_by": {("lane:" if n in LANE_WHERE else "tier:") + n: v
                                                     for n, v in own_h.items()}}
    nfit = ctx.net_choice(res["choice"])
    t_fit = pick_table(ctx, ctx.picks(W, 20)[0], nfit, "disc")
    yr = np.array([x[:4] for x in ctx.dates])[t_fit["di"].to_numpy()]
    res["by_year"] = {y: {"vs_pool": summarise(g, "ex_pool"), "vs_spy": summarise(g, "ex_spy")}
                      for y, g in t_fit.groupby(yr)}
    res["fitted_discovery"] = {"vs_pool": summarise(t_fit, "ex_pool"), "vs_spy": summarise(t_fit, "ex_spy"),
                               "by_lane_vs_pool": {LANE_NAME[int(k)]: v for k, v in summarise(t_fit, "ex_pool", by="lane").items()},
                               "mean_cost_pct_by_tier": {str(int(k)): round(100 * float(g["cost"].mean()), 3)
                                                         for k, g in t_fit.groupby("tier")}}
    return res


# ------------------------------------------------------------------------------------------------ the holdout
CONFIRM_T = 2.0       # the holdout confirms a fitted group when its objective is positive at this clustered t and it does
                      # not lose to the provisional value (paired difference >= 0); written before the holdout was read


def _confirm(obj, diff_pp):
    ok = obj["t"] is not None and obj["mean_pct"] is not None and obj["mean_pct"] > 0 and obj["t"] >= CONFIRM_T
    ok_diff = diff_pp is None or diff_pp >= 0
    return bool(ok and ok_diff)


def holdout(ctx, choice, log=print):
    """the one read of the holdout: the frozen choice against the provisional plan, on decisions from SPLIT. -> dict"""
    W = {s_: {k: 1.0 for k in v} for s_, v in SIGNS.items()}     # the frozen weights (equal: the learner did not beat them)
    out = {"split": SPLIT}
    stop = choice["stop_atr"]
    per = "hold_"
    pk, _ = ctx.picks(W, 20)
    pk5, _ = ctx.picks(W, 5)
    nf = ctx.net_choice(choice)
    fit_t = pick_table(ctx, pk, nf, per)
    lane_name = lambda d_: {LANE_NAME[int(k)]: v for k, v in d_.items()}            # noqa: E731
    out["fitted"] = {"all_lanes_vs_spy": summarise(fit_t, "ex_spy"), "all_lanes_vs_pool": summarise(fit_t, "ex_pool"),
                     "by_lane_vs_pool": lane_name(summarise(fit_t, "ex_pool", by="lane")),
                     "by_lane_vs_spy": lane_name(summarise(fit_t, "ex_spy", by="lane")),
                     "by_tier_vs_pool": summarise(fit_t, "ex_pool", by="tier")}
    t5 = pick_table(ctx, pk5, nf, per)
    out["fitted_top5"] = {"vs_pool": summarise(t5, "ex_pool"), "vs_spy": summarise(t5, "ex_spy"),
                          "by_lane_vs_pool": lane_name(summarise(t5, "ex_pool", by="lane"))}
    prov_t = pick_table(ctx, pk, ctx.net(PROVISIONAL["hold"], PROVISIONAL["stop_atr"]), per)
    out["provisional"] = {"all_lanes_vs_spy": summarise(prov_t, "ex_spy"), "all_lanes_vs_pool": summarise(prov_t, "ex_pool"),
                          "by_lane_vs_pool": lane_name(summarise(prov_t, "ex_pool", by="lane"))}
    d, t, nd = paired(fit_t, prov_t, "ex_spy")
    out["fitted_minus_provisional"] = {"pp": round(d, 3), "t": round(t, 2) if t == t else None, "dates": nd}
    # one factor at a time: the fitted holds with the provisional stop, the fitted stop with the provisional hold
    only_stop = pick_table(ctx, pk, ctx.net_choice({"hold": PROVISIONAL["hold"], "stop_atr": stop}), per)
    only_hold = pick_table(ctx, pk, ctx.net_choice(dict(choice, stop_atr=PROVISIONAL["stop_atr"])), per)
    d_s, t_s, _ = paired(only_stop, prov_t, "ex_spy")
    d_h, t_h, _ = paired(only_hold, prov_t, "ex_spy")
    out["stop_vs_provisional"] = {"pp": round(d_s, 3), "t": round(t_s, 2) if t_s == t_s else None}
    out["hold_vs_provisional"] = {"pp": round(d_h, 3), "t": round(t_h, 2) if t_h == t_h else None}
    # each group's own hold against the pooled one, on that group's picks
    out["group_hold"] = {}
    for key, h in (choice.get("hold_by") or {}).items():
        kind, name = key.split(":")
        where = LANE_WHERE[name] if kind == "lane" else TIER_WHERE[name]
        own = fit_t[where(fit_t)]
        pooled = only_stop[where(only_stop)]
        d_, t_, _ = paired(own, pooled, "ex_spy")
        out["group_hold"][key] = {"hold": h, "own": summarise(own, "ex_spy"), "pooled_hold": summarise(pooled, "ex_spy"),
                                  "pp": round(d_, 3), "t": round(t_, 2) if t_ == t_ else None}
    # the holdout's own grids, for the record only (nothing is chosen from them)
    out["holdout_hold_grid_no_stop"] = {str(h): summarise(pick_table(ctx, pk, ctx.net(h, None), per), "ex_spy") for h in HOLDS}
    out["holdout_stop_grid"] = {str(s_): summarise(pick_table(ctx, pk, ctx.net(choice["hold"], s_), per), "ex_spy")
                                for s_ in STOPS}
    wl = out["fitted"]["by_lane_vs_pool"]
    out["penalty"] = {}
    for lane, state in ((1, "UP"), (2, "RESET")):
        tb = {}
        for ps in (0.0, 1.0):
            pkp, _ = ctx.picks(W, 20, pen_scale=ps)
            tb[ps] = pick_table(ctx, pkp & (ctx.lane == lane), nf, per)
        d_, t_, _ = paired(tb[1.0], tb[0.0], "ex_pool")
        out["penalty"][state] = {"one": summarise(tb[1.0], "ex_pool"), "zero": summarise(tb[0.0], "ex_pool"),
                                 "one_minus_zero_pp": round(d_, 3), "t": round(t_, 2) if t_ == t_ else None}
    none = {"t": None, "mean_pct": None}
    st = {"plan.hold": _confirm(out["fitted"]["all_lanes_vs_spy"], out["hold_vs_provisional"]["pp"]),
          "plan.stop_atr": _confirm(out["fitted"]["all_lanes_vs_spy"], out["stop_vs_provisional"]["pp"]),
          "weights.UP": _confirm(wl.get("buy", none), None), "weights.RESET": _confirm(wl.get("watch", none), None),
          "vetoes.penalty": bool(out["penalty"]["UP"]["one_minus_zero_pp"] >= 0 and _confirm(wl.get("buy", none), None)),
          "plan.risk_pct": False}                    # not identified on discovery: no holdout can confirm a value the fit did not choose
    for key, g in out["group_hold"].items():
        st["plan_by." + key] = _confirm(g["own"], g["pp"])
    out["confirmed"] = st
    return out


# ------------------------------------------------------------------------------------------------ the frozen file
FIT_STATUS_KEYS = ("plan.hold", "plan.stop_atr", "plan.risk_pct", "weights.UP", "weights.RESET", "vetoes.penalty")


def fit_params(choice):
    """the parameters the fit sets, as the overlay on fearday_params.json"""
    params = {"plan": {"hold": int(choice["hold"]), "stop_atr": choice["stop_atr"], "risk_pct": float(choice["risk_pct"])},
              "top_n": 20,
              "weights": {s: {k: float(SIGNS[s][k]) for k in SIGNS[s]} for s in SIGNS}}
    by = {k: {"hold": int(v)} for k, v in (choice.get("hold_by") or {}).items()}
    if by:
        params["plan_by"] = by
    return params


def fit_doc(choice, disc, holdout_res=None, fitted_on="2026-10-27"):
    """the frozen fit file. Stage A (holdout_res None): the discovery choice, every group `fitted`. Stage B: the holdout's
    verdict per group (`confirmed`, or `fitted` when the holdout did not confirm it; the risk stays `not_identified`).
    params_sha256 covers the parameters alone (stage A and B share it); content_sha256 covers params and status"""
    params = fit_params(choice)
    status = {k: "fitted" for k in FIT_STATUS_KEYS}
    status["plan.risk_pct"] = "not_identified"
    for key in params.get("plan_by", {}):
        status["plan_by." + key] = "fitted"
    if holdout_res:
        for k, ok in holdout_res["confirmed"].items():
            if k in status and status[k] == "fitted" and ok:
                status[k] = "confirmed"
    body = {"params": params, "status": status}
    doc = {"version": 1, "fitted_on": fitted_on, "split": SPLIT, "embargo_days": EMBARGO_DAYS,
           "params": params, "params_sha256": freeze_hash(params), "status": status,
           "content_sha256": freeze_hash(body)}
    doc["discovery"] = {"choice": choice, "plan": {k: disc["plan"][k] for k in ("hold", "stop_atr", "common_rows")},
                        "fitted": disc["fitted_discovery"], "by_year": disc["by_year"]}
    if holdout_res:
        doc["holdout"] = {k: v for k, v in holdout_res.items()}
    return doc


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=str)
        f.write("\n")
    os.replace(tmp, path)


def load_ctx(data_dir, p=None):
    T = pd.read_parquet(os.path.join(data_dir, "T.parquet"))
    R, O = np.load(os.path.join(data_dir, "RET.npy")), np.load(os.path.join(data_dir, "OFF.npy"))
    days = pd.read_parquet(os.path.join(data_dir, "days.parquet"))
    sp = pd.read_parquet(os.path.join(data_dir, "spy.parquet"))
    return Ctx(T, R, O, days, sp["o"].to_numpy(), sp["c"].to_numpy(), p)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stage", choices=("build", "discover", "freeze", "holdout"))
    ap.add_argument("--panels", help="the price panels directory (bars.parquet, etf_all.parquet)")
    ap.add_argument("--work", required=True, help="a directory for the candidate table and the stage outputs")
    ap.add_argument("--fit", default=FIT_PATH, help="the fit file to write (freeze, holdout)")
    a = ap.parse_args(argv)
    os.makedirs(a.work, exist_ok=True)
    if a.stage == "build":
        b = pd.read_parquet(os.path.join(a.panels, "bars.parquet"), columns=["sid", "d", "o", "h", "l", "c", "v"])
        b["sid"], b["d"] = b["sid"].astype(str), b["d"].dt.strftime("%Y-%m-%d")
        e = pd.read_parquet(os.path.join(a.panels, "etf_all.parquet"))
        sp = e[e.s == "SPY"].set_index("d").sort_index()
        T, R, O, days = build(b, sp["c"].astype(float))
        T.to_parquet(os.path.join(a.work, "T.parquet"))
        np.save(os.path.join(a.work, "RET.npy"), R)
        np.save(os.path.join(a.work, "OFF.npy"), O)
        days.to_parquet(os.path.join(a.work, "days.parquet"))
        sp[["o", "c"]].astype(float).to_parquet(os.path.join(a.work, "spy.parquet"))
    elif a.stage == "discover":
        write_json(os.path.join(a.work, "discovery.json"), discover(load_ctx(a.work)))
    elif a.stage == "freeze":
        d = json.load(open(os.path.join(a.work, "discovery.json")))
        write_json(a.fit, fit_doc(d["choice"], d))
    else:
        # the holdout reads the parameters from the frozen file, never from the discovery output
        doc = json.load(open(a.fit))
        if doc["params_sha256"] != freeze_hash(doc["params"]):
            raise SystemExit("the fit file's parameters do not match their hash")
        d = json.load(open(os.path.join(a.work, "discovery.json")))
        choice = dict(d["choice"])
        assert fit_params(choice) == doc["params"], "the frozen parameters differ from the discovery choice"
        h = holdout(load_ctx(a.work), choice)
        write_json(os.path.join(a.work, "holdout.json"), h)
        write_json(a.fit, fit_doc(choice, d, h))


if __name__ == "__main__":
    main()
