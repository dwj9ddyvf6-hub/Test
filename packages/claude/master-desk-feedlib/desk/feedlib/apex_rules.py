"""The APEX decisions: each sleeve's source strategy, called as its research runner called it, read the way the
source desk's live runtime read APEX (desk/agents/risk.py: the target on the finished session t, the simulator's
position held after t, planned_position -> the exposure held from the close of the next session).

Pure: no package imports. The source modules arrive as `Mods` — in the desk, the vendored ones (desk/vendor/apex,
their `yahoo` bound by desk/feedlib/apex.py); in the parity harness, cursor2's own modules in their own tree (it
runs this same file there). Every reading is a function of the data through t:

  plan .......... planned_position(target[t], position[t], band) on the strategy's own simulator run (its last
                  simulate call; the core variants: each run in the dict's own order) — the backtest's
                  position[t + 1] (lag 1), the source desk's "plan for the next close";
  lagged choices  the unshifted series the source shifts by lag + 1 (E5's flag / 3, E6's trend >= 0.5, N2's
                  hold, C4's choice, E3 / v1.1's bond trend): their value on t governs the session after next,
                  i.e. the capital from the close of the next session;
  multi-asset ... the source's own multi-asset loop (simulate_multi, _lagged_book) re-run on its captured targets
                  with two empty rows appended: its position after the next session (Sector Kings' read out of
                  _lagged_book with one-hot returns, no rate and no cost);
  E7 ............ the turn-of-month flag two sessions ahead from the market extended by the calendar's next
                  sessions (zero returns), the signals not recomputed.
Scalar mode reads the date t; series mode returns every date's reading (pandas Series on the Nasdaq-100 index)."""
import math
import sys
from contextlib import contextmanager

TIERS = ("APEX-20", "APEX-25", "APEX-30", "APEX-40", "APEX-50F", "APEX-K")
BASELINES = ("QQQ", "BH2", "BH3", "SMA200-1x", "SMA200-3x", "TREND-1x", "TREND-3x", "VOL-3x")


class Mods:
    """the source modules: S strategies, N inventions, C round3, SER data.series, F features, E backtest.engine,
    AG the live runtime's planned_position / alpaca_weights."""

    def __init__(self, S, N, C, SER, F, E, AG):
        self.S, self.N, self.C, self.SER, self.F, self.E, self.AG = S, N, C, SER, F, E, AG


def call_with_locals(fn, *a, **kw):
    """fn(*a, **kw) and its local variables at return (the source's own intermediate series, observed)."""
    code, got = fn.__code__, {}
    old = sys.getprofile()

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is code:
            got.clear()
            got.update(frame.f_locals)

    sys.setprofile(prof)
    try:
        res = fn(*a, **kw)
    finally:
        sys.setprofile(old)
    return res, got


@contextmanager
def spy(mods, name):
    """record every call of global `name` of each module (args, kwargs, result); the real function still runs."""
    calls, saved = [], []
    for mod in mods:
        real = getattr(mod, name)
        saved.append((mod, real))

        def wrapper(*a, _real=real, **kw):
            res = _real(*a, **kw)
            calls.append((a, kw, res))
            return res

        setattr(mod, name, wrapper)
    try:
        yield calls, saved[0][1]
    finally:
        for mod, real in saved:
            setattr(mod, name, real)


class Ctx:
    def __init__(self, mods, t=None, sessions=(), series=False):
        self.M, self.t, self.sessions, self.series = mods, t, list(sessions), series
        self.memo = {}

    def get(self, key, fn):
        if key not in self.memo:
            self.memo[key] = fn()
        return self.memo[key]

    # -- data -----------------------------------------------------------------------------------------------------
    @property
    def m(self):
        return self.get("m", self.M.SER.ndx_market)

    @property
    def sig(self):
        return self.get("sig", lambda: self.M.S.compute_signals(self.m))

    def daily(self, sym):
        return self.M.SER.yahoo.get_daily(sym)

    @property
    def tnx(self):
        return self.get("tnx", lambda: self.daily("^TNX")["close"])

    @property
    def sleeves(self):
        return self.get("sleeves", lambda: self.M.N.sleeve_returns(self.m.index, self.m.r))

    @property
    def sox(self):
        return self.sleeves["SOX"]

    @property
    def gold_gc(self):
        return self.get("gold_gc", lambda: self.M.N.aligned_returns("GC=F", self.m.index, field="close"))

    @property
    def bond_r(self):
        return self.get("bond_r", lambda: self.M.SER.treasury_7_10y_returns(self.m.index))

    def ext_index(self, n=None):
        """the sessions after the data's last date: the first n, or through the end of the second one's month."""
        import pandas as pd
        s = [pd.Timestamp(x) for x in self.sessions]
        if n is not None:
            s = s[:n]
        if len(s) < (n or 2):
            raise RuntimeError("the calendar's next sessions are needed")
        return pd.DatetimeIndex(s, name=self.m.index.name)

    # -- readings -------------------------------------------------------------------------------------------------
    def read(self, s):
        """s on the decision date (scalar) / on every date (series)."""
        if self.series:
            return s.reindex(self.m.index)
        v = s.loc[self.t]
        if isinstance(v, str):
            return v
        return None if v != v else float(v)

    def read_ahead(self, s, k):
        """the value s holds k rows after the decision date (multi-asset re-runs: k = 2, the held column)."""
        return self.read(s.shift(-k))

    def plan(self, target, out, band, lag):
        """the exposure held from the close of the session after t: planned_position(target[t], position[t])."""
        import pandas as pd
        pos = out["position"]
        d = target.reindex(pos.index)
        pp = self.M.AG.planned_position
        if lag != 1:                                   # a buy-and-hold variant: lag 0, band 0, constant
            return self.read(d)
        if self.series:
            v = [pp(float(x), float(p), band) for x, p in zip(d.to_numpy(dtype=float), pos.to_numpy(dtype=float))]
            return pd.Series(v, index=pos.index).reindex(self.m.index)
        return pp(float(d.loc[self.t]), float(pos.loc[self.t]), band)

    def runs(self, call):
        """call() and every simulator run it made, in order (strategies / inventions / round3 call simulate through
        their own module global; buy_and_hold through the engine's)."""
        with spy((self.M.S, self.M.N, self.M.C, self.M.E), "simulate") as (calls, _):
            res = call()
        return res, calls

    def plan_run(self, a, kw):
        """the plan of one captured simulator run, on its positions of every row (the same run untrimmed), defined
        from the session before the source's first kept row: simulate(trim=True) keeps the rows from its first
        valid target + lag + 1, and the plan for that row is made the session before it."""
        import pandas as pd
        out = self.M.E.simulate(*a, **dict(kw, trim=False))
        p = self.plan(a[0], out, kw.get("band", 0.20), kw.get("lag", 1))
        first = a[0].first_valid_index() if kw.get("trim", True) else None
        if first is None:
            return p
        idx = out.index
        start = idx[max(min(int(idx.searchsorted(first)) + kw.get("lag", 1) + 1, len(idx) - 1) - 1, 0)]
        if self.series:
            return p.where(pd.Series(self.m.index >= start, index=self.m.index))
        return p if self.t >= start else float("nan")

    def book(self, call):
        """(the plan of the strategy's own run = its last simulator call, the strategy's result)."""
        res, calls = self.runs(call)
        a, kw, _ = calls[-1]
        return self.plan_run(a, kw), res

    def book_locals(self, fn, *a, **kw):
        with spy((self.M.S, self.M.N, self.M.C, self.M.E), "simulate") as (calls, _):
            res, loc = call_with_locals(fn, *a, **kw)
        ca, ckw, _ = calls[-1]
        return self.plan_run(ca, ckw), res, loc

    def choose(self, v, mapping):
        if self.series:
            return v.map(lambda x: mapping.get(x) if x == x else None)
        return mapping.get(v)


# -- the sleeves ------------------------------------------------------------------------------------------------------
def _variants(c):
    def run():
        return c.M.S.core_variants(c.m, c.sig)          # research/run_study.py main()
    res, calls = c.get("cv", lambda: c.runs(run))
    plans = {}
    for name, (a, kw, _) in zip(res.keys(), calls):    # the dict's own evaluation order: one run per variant
        plans[name] = c.get("cv:" + name, lambda a=a, kw=kw: c.plan_run(a, kw))
    return plans


def _tiers(c):
    p = _variants(c)
    return {"plan": {"NDX": p["APEX-50F"]}, "obs": {k: p[k] for k in TIERS}}


def _benchmarks(c):
    p = _variants(c)
    return {"plan": {"NDX": p["QQQ"]}, "obs": {k: p[k] for k in BASELINES}}


def _bond_idle(c):
    on = c.read(c.M.S.bond_trend(c.bond_r, c.m.index))   # on_held = bond_trend.shift(lag + 1)
    return c.choose(on, {1.0: "TSY", 0.0: "CASH"})


def _v11(c):
    p, _ = c.book(lambda: c.M.S.apex_v11(c.m, c.sig, c.bond_r))
    return {"plan": {"NDX": p}, "idle": _bond_idle(c)}


def _e1(c):
    vix, vix3m = c.M.SER.aligned_close("^VIX", c.m.index), c.M.SER.aligned_close("^VIX3M", c.m.index)
    p, _ = c.book(lambda: c.M.S.e1_vix_term_structure(c.m, c.sig, vix, vix3m))
    return {"plan": {"NDX": p}, "obs": {"vix_vix3m": c.read(vix / vix3m)}}


def _e2(c):
    p, _ = c.book(lambda: c.M.S.e2_dip_overlay(c.m, c.sig))
    return {"plan": {"NDX": p}, "obs": {"double7": c.read(c.M.F.double7_state(c.sig.level, c.sig.trend >= 0.5))}}


def _e3(c):
    p, _ = c.book(lambda: c.M.S.e3_defensive_bonds(c.m, c.sig, c.bond_r))
    return {"plan": {"NDX": p}, "idle": _bond_idle(c)}


def _e5(c):
    smh_r = c.daily("SMH")["adj_close"].pct_change()                  # research/run_study.py
    L, _, loc = c.book_locals(c.M.S.e5_semis_tilt, c.m, c.sig, smh_r)
    share = c.read(loc["flag"] / 3.0)                                  # share = (flag / 3).shift(lag + 1)
    return {"plan": {"NDX": (1.0 - share) * L, "SMH": share * L}, "obs": {"semis_share": share, "exposure": L}}


def _e6(c):
    """boost = (trend.shift(lag + 1) >= 0.5), kept where QQQ has the next session's close and the open after it
    (sessions past the data's end count as present: the boost is bought and sold in them)."""
    oc = c.M.SER.adjusted_open_close("QQQ")
    p, _ = c.book(lambda: c.M.S.e6_overnight_boost(c.m, c.sig, oc))
    o2 = oc["open"].reindex(c.m.index).shift(-2)
    c1 = oc["close"].reindex(c.m.index).shift(-1)
    o2.iloc[-2:] = o2.iloc[-2:].fillna(1.0)
    c1.iloc[-1:] = c1.iloc[-1:].fillna(1.0)
    on = (c.sig.trend >= 0.5).astype(float).where(o2.notna() & c1.notna(), 0.0)
    return {"plan": {"NDX": p}, "boost": c.read(on)}


def _e7(c):
    S, SER = c.M.S, c.M.SER
    idx = c.m.index.append(c.ext_index())                              # the calendar ahead: tom.shift(-(lag + 1))
    m2 = SER.Market(r=c.m.r.reindex(idx).fillna(0.0), rf=c.m.rf.reindex(idx).ffill(), name=c.m.name)
    g = c.sig
    sig2 = S.Signals(level=g.level.reindex(idx), trend=g.trend.reindex(idx), vol=g.vol.reindex(idx),
                     sma200=g.sma200.reindex(idx))
    p, _ = c.book(lambda: S.e7_turn_of_month(m2, sig2))
    return {"plan": {"NDX": p}}


def _n1(c):
    p, _ = c.get("n1", lambda: c.book(lambda: c.M.N.n1_duration_shield(c.m, c.sig, c.tnx)))
    return {"plan": {"NDX": p}, "obs": {"duration_gate": c.read(c.M.N.duration_gate(c.tnx, c.m.index))}}


def _n2(c):
    L, _, loc = c.book_locals(c.M.N.n2_silicon_switch, c.m, c.sox)
    h = c.read(loc["hold"].astype(float))                              # held_asset = hold.shift(lag + 1)
    return {"plan": {"NDX": L * (1.0 - h), "SOX": L * h}, "obs": {"holding_sox": h}}


def _rerun_multi(c, mod, call):
    """the source's simulate_multi re-run on its captured inputs with two empty rows: held two rows on = the
    position after the next session."""
    with spy((mod,), "simulate_multi") as (calls, real):
        call()
    a, kw, _ = calls[-1]
    tg, R, rf = a[0], a[1], a[2]
    idx = tg.index.append(c.ext_index(2))
    return real(tg.reindex(idx), R.reindex(idx), rf.reindex(idx).ffill(), *a[3:], **kw)


def _prism(names):
    def run(c):
        out = _rerun_multi(c, c.M.N, lambda: c.M.N.prism({k: c.sleeves[k] for k in names}, c.m))
        return {"plan": {k: c.read_ahead(out["w_" + k], 2) for k in names}}
    return run


def _c1(c):
    N, C = c.M.N, c.M.C
    er = N.aligned_returns("QQQ", c.m.index, field="adj_close").dropna()   # research/run_round3.py
    erf = c.M.SER.risk_free_daily(er.index)
    out = _rerun_multi(c, N, lambda: C.c1_aurelia(er, c.gold_gc.reindex(er.index), erf))
    return {"plan": {"NDX": c.read_ahead(out["w_NDX"], 2), "GOLD": c.read_ahead(out["w_GOLD"], 2)}}


def _c2(c):
    import numpy as np
    import pandas as pd
    C = c.M.C
    with spy((C,), "_lagged_book") as (calls, real):
        C.c2_sector_kings(c.m.index, c.m.rf)
    dec = calls[-1][0][0]
    n, k = dec.shape
    dec = np.vstack([dec, np.full((2, k), np.nan)])
    idx = c.m.index.append(c.ext_index(2))
    plan = {}
    for j, sym in enumerate(C.SECTORS):                                   # one-hot returns, no rate, no cost:
        probe = np.zeros((n + 2, k))                                      # the returned "ret" is the held weight
        probe[:, j] = 1.0
        held = real(dec, probe, np.zeros(n + 2), bps=0.0, fin_spread=0.0)
        plan[sym] = c.read_ahead(pd.Series(held, index=idx), 2)
    return {"plan": plan}


def _c3(c):
    p, _ = c.book(lambda: c.M.C.c3_follow_through(c.m, c.sig))
    return {"plan": {"NDX": p}}


def _c4(c):
    N, C = c.M.N, c.M.C
    idx = c.m.index
    dxy = N.aligned_returns("DX-Y.NYB", idx, field="close")
    p, df, loc = c.book_locals(C.c4_broken_hedge, c.m, c.sig, c.sleeves["TSY"].reindex(idx), c.gold_gc.reindex(idx),
                               dxy.reindex(idx), gate=0.20, switch_bps=3.0)
    return {"plan": {"NDX": p}, "idle": c.read(loc["choice"]),            # chosen = choice.shift(2)
            "obs": {"cut": c.read(df["hedge_off"].astype(float))}}


def _c5(c):
    p, (_, L) = c.book(lambda: c.M.C.c5_reflex(c.m, c.sig, c.sox))
    return {"plan": {"NDX": p}, "obs": {"reflex_L": c.read(L)}}


def _c6(c):
    p, _ = c.book(lambda: c.M.C.c6_slingshot(c.m, c.sig, c.tnx))
    return {"plan": {"NDX": p}}


def _gestalt(c):
    return c.get("n5", lambda: c.book(lambda: c.M.N.n5_gestalt(c.m, c.sig, c.sox)))


def _n5(c):
    p, (_, L) = _gestalt(c)
    return {"plan": {"NDX": p}, "obs": {"gestalt_L": c.read(L)}}


def _n6_plan(c):
    return c.get("n6", lambda: c.book(lambda: c.M.N.n6_ensemble(c.m, c.sig, _gestalt(c)[1][1]))[0])


def _n6(c):
    return {"plan": {"NDX": _n6_plan(c)}}


def _gold(c):
    return c.get("gold", lambda: c.book(lambda: c.M.C.gold_sleeve(c.m.index, c.m.rf, c.gold_gc))[0])


def _c7(c):
    """55% N6, 25% the gold trend sleeve, 20% Variance Value on a T-bill core (its options decide live)."""
    n6, g = _n6_plan(c), _gold(c)
    return {"books": [[0.55, {"NDX": n6}], [0.25, {"GOLD": g}], [0.20, {}]], "vv_share": 0.20,
            "obs": {"n6": n6, "gold": g}}


def _btc(c):
    """N4's PRISM Bitcoin sleeve on its own: trend x min(1, 20% / HAR vol) (sigma_sleeve 0.20, PRISM_CAPS BTC 1),
    held by the source simulator (one-day lag, 0.20 band, Bitcoin's 10 bp)."""
    N, E = c.M.N, c.M.E
    btc = c.sleeves["BTC"]
    _, loc = call_with_locals(N.prism_targets, {"BTC": btc}, c.m.index)
    unit = loc["unit"]["BTC"]
    return c.plan_run((unit, btc.reindex(c.m.index).fillna(0.0), c.m.rf),
                      {"costs": E.FUTURES_COSTS.with_(trade_bps=N.PRISM_BPS["BTC"]), "lag": 1, "band": 0.20})


def _council_btc(c):
    """INVENTIONS_REPORT section 5's Council: the N6 signal for the Nasdaq sleeve, trend-levered gold, Bitcoin
    capped at 10% of risk, the Variance Value sleeve — C7's implemented components in C7's proportions on 90%."""
    n6, g, b = _n6_plan(c), _gold(c), _btc(c)
    return {"books": [[0.495, {"NDX": n6}], [0.225, {"GOLD": g}], [0.10, {"BTC": b}], [0.18, {}]], "vv_share": 0.18,
            "obs": {"n6": n6, "gold": g, "btc": b}}


def _n7(c):
    """the N1 Duration Shield core; the Variance Value overlay decides live on the whole book."""
    p, _ = c.get("n1", lambda: c.book(lambda: c.M.N.n1_duration_shield(c.m, c.sig, c.tnx)))
    return {"plan": {"NDX": p}, "vv_share": 1.0}


DECIDE = {
    "apex_trend_har_tiers": _tiers, "apex_benchmarks": _benchmarks, "apex_v11_defensive_bond": _v11,
    "apex_e1_vix_term_gate": _e1, "apex_e2_double7_dip": _e2, "apex_e3_defensive_treasuries": _e3,
    "apex_e5_semis_rs_tilt": _e5, "apex_e6_overnight_boost": _e6, "apex_e7_turn_of_month": _e7,
    "apex_n1_duration_shield": _n1, "apex_n2_silicon_switch": _n2,
    "apex_n3_prism_classic": _prism(("NDX", "TSY", "GOLD", "OIL", "USD")),
    "apex_n4_prism_paradigm": _prism(("NDX", "SOX", "GOLD", "BTC")), "apex_n5_gestalt": _n5,
    "apex_n6_gestalt_apex": _n6, "apex_n7_omni": _n7, "apex_c1_aurelia_pair": _c1, "apex_c2_sector_kings": _c2,
    "apex_c3_follow_through": _c3, "apex_c4_broken_hedge": _c4, "apex_c5_reflex": _c5, "apex_c6_slingshot": _c6,
    "apex_c7_council": _c7, "apex_council_btc": _council_btc,
}


def check(d):
    for k, v in (d.get("plan") or {}).items():
        if v is None or not math.isfinite(v):
            raise RuntimeError(f"no finite exposure for {k} ({v})")
    for b in d.get("books") or []:
        for k, v in b[1].items():
            if v is None or not math.isfinite(v):
                raise RuntimeError(f"no finite exposure for {k} ({v})")


def decide_all(mods, t=None, sessions=(), only=None, series=False):
    """every sleeve's decision on the finished session t (scalar; errors per sleeve) or on every date (series)."""
    import pandas as pd
    c = Ctx(mods, None if t is None else pd.Timestamp(t), sessions, series)
    out = {}
    for sid, fn in DECIDE.items():
        if only and sid not in only:
            continue
        if series:
            out[sid] = fn(c)
            continue
        try:
            d = fn(c)
            check(d)
            out[sid] = d
        except Exception as e:
            out[sid] = {"error": "%s: %s" % (type(e).__name__, str(e)[:200])}
    out["_signals"] = {"trend": c.read(c.sig.trend), "vol": c.read(c.sig.vol)}
    return out
