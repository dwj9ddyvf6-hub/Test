"""apex_options (the 15 APEX option sleeves) and the Variance Value legs of N7 / C7 / the Council: the SOURCE's own
code (cursor2 main @ca8ac1f650670e1d in its own tree: CURSOR2_SRC) vs the port, four ways, on every market below.

  I. inputs   build_inputs (x: S, r, rf, total return, trend, HAR vol, APEX-50F target, drawdown, VXN, its 80th
              percentile, prior 10-day high, level, APEX-50F return, month starts) and the surface's IVs, source vs
              vendored, every date, exact.
  R. replay   every decision the source made: each strategy (research/run_options_study.py / _v2 / _v3 calls) runs
              in the source tree with its Book recorded (the state handed to decide() each day — core, nav_prev,
              legs, O12's closure state — and the open / close / adjust it made); the port re-runs the vendored
              strategy with desk/feedlib/apex_book.LiveBook replaying those states (no listing: the source's
              continuous strikes and units): every day's trades must be identical.
  E. E4       tail_hedge_overlay's loop traced line by line in the source (the held puts, the exposure, the spot, the
              NAV at each month start, and what it bought) vs apex_options.tail_rule, every month start.
  L. live     desk/feedlib/apex.option_context on sampled dates (the records through the day before, today's QQQ
              close and index levels as the live values) vs the source: its build_inputs on the finished data
              (the signals) and on the data through today (today's row), its surface at today, the cores' plans by
              its planned_position.
Markets: the source's own Yahoo cache (APEX_SOURCE_DATA, as tools/parity/apex.py) and APEX_SYNTH synthetic markets.

    python3 -m tools.parity.run apex_options"""
import json
import os
import random
import tempfile
from datetime import date

from desk.feedlib import apex as AF

from . import old_run, write_receipt
from .apex import N_SYNTH, SRC_TREE, records_of
from .apex_synth import market

LIVE_SAMPLES = int(os.environ.get("APEX_LIVE_SAMPLES", "6"))
START = "2002-01-25"
TAGS = ["call", "leap", "put", "phx", "chop", "fear", "vv", "rr", "base"]
OPS = ["open", "close", "adjust"]
FIELDS = ("S", "r", "rf_daily", "tr", "trend", "vol", "L", "dd252", "vol30", "vol30_p80", "hi10_prior", "level",
          "apex_ret", "month_start")
# (sleeve, the strategy call as its runner made it) — mirrors desk/sleeves/families/apex_options.ROWS_O
CALLS = {
    "apex_o1_convex": "O.o1_convex(x, m, surf, costs, start)",
    "apex_o1b_convex_incremental": "O.o1b_convex(x, m, surf, costs, start)",
    "apex_o2_leaps_apex": "O.o2_leaps(x, surf, costs, start)",
    "apex_o2b_leaps_incremental": "O.o2b_leaps(x, surf, costs, start)",
    "apex_o10_leaps_vv": "O.o2b_leaps(x, surf, costs, start, with_variance_value=True)",
    "apex_o3_regime_putwrite": "O.o3_putwrite(x, surf, costs, start)",
    "apex_o4_phoenix": "O.overlay(x, surf, costs, start, ('phoenix',))",
    "apex_o5_chop_harvest": "O.overlay(x, surf, costs, start, ('chop',))",
    "apex_o8_fear_put_spread": "O.overlay(x, surf, costs, start, ('fear',))",
    "apex_o9_omega": "O.overlay(x, surf, costs, start, ('phoenix', 'chop', 'fear'))",
    "apex_o11_apex_vv": "O.overlay(x, surf, costs, start, ('vv',))",
    "apex_o6_variance_value": "O.o6_variance_value(x, surf, costs, start)",
    "apex_o7_skew_risk_reversal": "O.o7_skew_rr(x, surf, costs, start)",
    "apex_o12_hybrid_leaps": "O.o12_hybrid(x, surf, costs, start)",
    "apex_c7_council": "C.variance_value_cash(m, price, '^VXN', 0.0055)",
}

SRC = r'''
import json, sys
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
RAW = json.load(open(PAYLOAD["data"]))
def frame(rec):
    idx = pd.DatetimeIndex(pd.to_datetime(rec["dates"]), name="date")
    cols = {c: [float("nan") if v is None else v for v in (rec.get(c) or rec["close"])]
            for c in ("open", "high", "low", "close", "volume", "adj_close")}
    return pd.DataFrame(cols, index=idx).astype("float64")
FR = {}
import desk.data.yahoo as Y
def get_daily(symbol, max_age_hours=12.0, refresh=False):
    if symbol not in FR:
        if symbol not in RAW:
            raise RuntimeError("no daily history for " + symbol)
        FR[symbol] = frame(RAW[symbol])
    return FR[symbol]
Y.get_daily = get_daily
from desk import features as F, round3 as C, strategies as S
from desk.backtest import options as BO
from desk.data.series import aligned_close, ndx_market
from desk.options import sim as VS, strategies as O
from desk.options.surface import Surface, SurfaceParams
from desk.agents.risk import planned_position
TAGS, OPS = PAYLOAD["tags"], PAYLOAD["ops"]
if PAYLOAD.get("live"):                                  # L: the finished data / the data through today
    out = {}
    for which in ("finished", "today"):
        FR.clear()
        cut = pd.Timestamp(PAYLOAD["live"][which])
        keep = {s_: frame(rec) for s_, rec in RAW.items()}
        FR.update({s_: f_[f_.index <= cut] for s_, f_ in keep.items() if len(f_[f_.index <= cut])})
        m = ndx_market()
        surf = Surface(m.index, "^VXN", SurfaceParams.load())
        calls = []
        _sim = S.simulate
        def sim(*a, **kw):
            r_ = _sim(*a, **kw); calls.append((a, kw, r_)); return r_
        S.simulate = sim
        x = O.build_inputs(m, Y.get_daily("QQQ")["close"], surf, 0.0055)
        sig = S.compute_signals(m)
        S.run(S.apex_target(sig), m)
        S.simulate = _sim
        t = m.index[-1]
        def plan(c):
            a, kw, o = c
            return planned_position(float(a[0].reindex(o.index).loc[t]), float(o["position"].loc[t]), kw.get("band", 0.2))
        rec = {f: [None if (isinstance(v, float) and v != v) else (bool(v) if f == "month_start" else float(v))
                   for v in np.asarray(getattr(x, f)).tolist()] for f in PAYLOAD["fields"]}
        rec["dates"] = [str(d.date()) for d in x.dates]
        rec["plans"] = {"apex50f": plan(calls[0]), "apex30": plan(calls[1])}
        T = np.array([0.05, 0.1, 0.25, 0.5, 1.0]); Fw = np.array([1.0] * 5) * float(x.S[-1])
        rec["iv"] = [float(v) for K in (0.8, 1.0, 1.2) for v in surf.iv(len(x.dates) - 1, Fw * K, Fw, T)]
        out[which] = rec
    json.dump(out, open(PAYLOAD["out"], "w"))
    print(json.dumps({"ok": True}))
    raise SystemExit(0)
m = ndx_market()
price = Y.get_daily("QQQ")["close"]
surf = Surface(m.index, "^VXN", SurfaceParams.load())
x = O.build_inputs(m, price, surf, 0.0055)
start = int(m.index.searchsorted(pd.Timestamp(PAYLOAD["start"])))
costs = VS.OptionCosts()
arrays = {"x_" + f: np.asarray(getattr(x, f), dtype=float) for f in PAYLOAD["fields"]}
T = np.array([0.02, 0.08, 0.25, 0.6, 1.2])
ivs = []
for t in range(0, len(m.index), 97):
    Fw = np.full(5, float(x.S[t])) if x.S[t] == x.S[t] else np.full(5, 100.0)
    ivs.append(np.concatenate([surf.iv(t, Fw * K, Fw, T) for K in (0.75, 0.9, 1.0, 1.1, 1.3)]))
arrays["iv"] = np.array(ivs)
REC = {}
def closure_state(decide):
    for cell in (decide.__closure__ or ()):
        try:
            v = cell.cell_contents
        except ValueError:
            continue
        if isinstance(v, dict) and set(v) == {"fut", "wait_month"}:
            return v
    return None
class RecBook(VS.Book):
    def run(self, decide, start):
        st = closure_state(decide)
        def rec(b, t):
            R_["days"].append(t); R_["core"].append(b.core); R_["nav_prev"].append(b.nav_prev)
            R_["fut"].append(st["fut"] if st else 0.0); R_["wait"].append(1.0 if st and st["wait_month"] else 0.0)
            for l in b.legs:                                 # + whether K / units / px are numpy scalars
                R_["legs"].append([len(R_["days"]) - 1, float(l.is_call), l.K, l.exp_i, l.units, l.px, TAGS.index(l.tag),
                                   float(type(l.K) is not float), float(type(l.units) is not float),
                                   float(type(l.px) is not float)])
            R_["np_core"].append(float(type(b.core) is not float))
            decide(b, t)
        return VS.Book.run(self, rec, start)
    def open(self, t, is_call, K, exp_i, units, tag):
        leg = VS.Book.open(self, t, is_call, K, exp_i, units, tag)
        if leg is not None:
            R_["ops"].append([len(R_["days"]) - 1, 0, float(is_call), K, exp_i, units, TAGS.index(tag)])
        return leg
    def close(self, t, leg):
        R_["ops"].append([len(R_["days"]) - 1, 1, float(leg.is_call), leg.K, leg.exp_i, leg.units, TAGS.index(leg.tag)])
        VS.Book.close(self, t, leg)
    def adjust(self, t, leg, delta_units):
        if delta_units != 0 and np.isfinite(delta_units):
            R_["ops"].append([len(R_["days"]) - 1, 2, float(leg.is_call), leg.K, leg.exp_i, delta_units,
                              TAGS.index(leg.tag)])
        return VS.Book.adjust(self, t, leg, delta_units)
O.Book = RecBook
C.Book = RecBook
for sid, call in PAYLOAD["calls"].items():
    R_ = {"days": [], "core": [], "nav_prev": [], "fut": [], "wait": [], "legs": [], "ops": [], "np_core": []}
    eval(call)
    for k in ("days", "core", "nav_prev", "fut", "wait", "np_core"):
        arrays[sid + "|" + k] = np.asarray(R_[k], dtype=float)
    arrays[sid + "|legs"] = np.asarray(R_["legs"], dtype=float).reshape(-1, 10)
    arrays[sid + "|ops"] = np.asarray(R_["ops"], dtype=float).reshape(-1, 7)
# E: E4's monthly decisions, traced in tail_hedge_overlay's own loop
sig = S.compute_signals(m)
vxn, vix = aligned_close("^VXN", m.index), aligned_close("^VIX", m.index)
rv21 = F.realized_vol(m.r, 21)
iv = (vxn / 100).copy()
iv[vxn.isna()] = (vix / 100 * 1.15)[vxn.isna()]
iv[iv.isna()] = (rv21 * 1.2)[iv.isna()]
code = BO.tail_hedge_overlay.__code__
first = code.co_firstlineno
E4 = []
cur = {}
def tracer(frame, event, arg):
    if frame.f_code is not code:
        return None
    if event == "line":
        ln = frame.f_lineno - first
        L_ = frame.f_locals
        if ln == 44 and L_["new_month"][L_["t"]]:            # `if new_month[t]:` (source line 72)
            cur.update(t=L_["t"], held=float(L_["qty"]), ex=float(L_["ex"][L_["t"]]), S=float(L_["S"][L_["t"]]))
        elif ln == 49 and cur:                               # `if ex[t] > trigger:` (line 77): the NAV after closing
            cur["nav"] = float(L_["core"])
        elif ln == 58 and cur:                               # `nav = core + qty * put_px` (line 86): the outcome
            E4.append([cur["t"], cur["held"], cur["ex"], cur["S"], cur.get("nav", float("nan")), float(L_["qty"]),
                       float(L_["K"]), float(L_["expiry"] - L_["t"])])
            cur.clear()
    return tracer
sys.settrace(tracer)
S.e4_tail_hedge(m, sig, iv)
sys.settrace(None)
arrays["e4"] = np.asarray(E4, dtype=float).reshape(-1, 8)
np.savez(PAYLOAD["out"], **arrays)
print(json.dumps({"ok": True, "n": len(m.index)}))
'''


def _source(recs, extra):
    with tempfile.TemporaryDirectory() as tmp:
        dpath = os.path.join(tmp, "data.json")
        json.dump(recs, open(dpath, "w"))
        out = os.path.join(tmp, "out.npz" if not extra.get("live") else "out.json")
        old_run(SRC, dict(extra, data=dpath, out=out, tags=TAGS, ops=OPS, fields=list(FIELDS), start=START,
                          calls=CALLS), timeout=7200, tree=SRC_TREE)
        if extra.get("live"):
            return json.load(open(out))
        import numpy as np
        with np.load(out) as z:
            return {k: z[k] for k in z.files}


def _same(a, b):
    import numpy as np
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return a.shape == b.shape and bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))


def replay(name, recs, stats, diffs):
    """I + R + E on one market."""
    import numpy as np
    import pandas as pd
    from desk.feedlib.apex_book import make_live_book
    from desk.sleeves.families import apex_options as AO
    from desk.vendor.apex import opt_strategies as O, round3 as C, series as SER, sim as VS, surface as SURF
    src = _source(recs, {})
    frames = AF.frames_for(recs, date(2100, 1, 1))
    with AF.bound(frames):
        m = SER.ndx_market()
        price = frames["QQQ"]["close"]
        surf = SURF.Surface(m.index, "^VXN", SURF.SurfaceParams.load())
        x = O.build_inputs(m, price, surf, AF.DIV)
        st = stats.setdefault("_inputs", {"fields": 0, "identical": 0, "iv_points": 0, "iv_identical": 0})
        for f in FIELDS:
            st["fields"] += 1
            if _same(src["x_" + f], np.asarray(getattr(x, f), dtype=float)):
                st["identical"] += 1
            else:
                diffs.append({"part": "I", "market": name, "field": f})
        T = np.array([0.02, 0.08, 0.25, 0.6, 1.2])
        mine = []
        for t in range(0, len(m.index), 97):
            Fw = np.full(5, float(x.S[t])) if x.S[t] == x.S[t] else np.full(5, 100.0)
            mine.append(np.concatenate([surf.iv(t, Fw * K, Fw, T) for K in (0.75, 0.9, 1.0, 1.1, 1.3)]))
        st["iv_points"] += int(np.asarray(mine).size)
        if _same(src["iv"], np.asarray(mine)):
            st["iv_identical"] += int(np.asarray(mine).size)
        else:
            diffs.append({"part": "I", "market": name, "field": "surface iv"})
        start = int(m.index.searchsorted(pd.Timestamp(START)))
        costs = VS.OptionCosts()
        LB = make_live_book(VS)
        for sid, call in CALLS.items():
            days = src[sid + "|days"].astype(int)
            legs, ops = src[sid + "|legs"], src[sid + "|ops"]
            steps = []
            by_day = {}

            def num(v, is_np):                                  # the source's own scalar type: sum() of exact
                return np.float64(v) if is_np else float(v)     # floats is compensated, of numpy scalars is not
            for row in legs:
                by_day.setdefault(int(row[0]), []).append((bool(row[1]), num(row[2], row[7]), int(row[3]),
                                                            num(row[4], row[8]), num(row[5], row[9]),
                                                            TAGS[int(row[6])]))
            for i, t in enumerate(days):
                steps.append({"t": int(t), "core": num(src[sid + "|core"][i], src[sid + "|np_core"][i]),
                              "nav_prev": float(src[sid + "|nav_prev"][i]), "legs": by_day.get(i, []),
                              "o12": {"fut": float(src[sid + "|fut"][i]), "wait_month": bool(src[sid + "|wait"][i])}
                              if "o12" in call else None})
            want = {}
            for row in ops:
                want.setdefault(int(row[0]), []).append((OPS[int(row[1])], bool(row[2]), float(row[3]), int(row[4]),
                                                          float(row[5]), TAGS[int(row[6])]))
            cls = type("ReplayBook", (LB,), {"STATE": {"steps": steps}, "INSTANCES": []})
            saved = O.Book, C.Book
            O.Book = C.Book = cls
            try:
                eval(call, {"O": O, "C": C, "x": x, "m": m, "surf": surf, "costs": costs, "start": start,
                            "price": price})
            finally:
                O.Book, C.Book = saved
            got = cls.INSTANCES[-1].steps_out
            s = stats.setdefault(sid, {"days": 0, "identical": 0, "trades": 0})
            for i, t in enumerate(days):
                mine_ops = [(o["op"], o["is_call"], o["K"], o["exp_i"], o["units"] if o["op"] != "adjust" else o["delta"],
                             o["tag"]) for o in got[i]]
                s["days"] += 1
                s["trades"] += len(mine_ops)
                if mine_ops == want.get(i, []):
                    s["identical"] += 1
                elif len(diffs) < 40:
                    diffs.append({"part": "R", "market": name, "sleeve": sid, "t": int(t), "source": want.get(i, []),
                                  "port": mine_ops})
    s = stats.setdefault("apex_e4_rolling_tail_puts", {"days": 0, "identical": 0, "trades": 0})
    for t, held, ex, S, nav, qty, K, tenor in src["e4"]:
        d = AO.tail_rule(True, held, ex, S, nav)
        s["days"] += 1
        got = (d["close"], None if d["open"] is None else (d["open"]["K"], d["open"]["tenor"], d["open"]["units"]))
        exp = (held > 0, None if not ex > AO.TRIGGER else (K, int(tenor), qty))
        s["trades"] += int(d["open"] is not None) + int(d["close"])
        if got == exp:
            s["identical"] += 1
        elif len(diffs) < 40:
            diffs.append({"part": "E", "market": name, "t": int(t), "source": exp, "port": got})
    return len(m.index)


def live(name, recs, n, rnd, stats, diffs):
    """L: option_context on sampled dates vs the source's build_inputs / surface / plans on the same data."""
    q = recs["QQQ"]["dates"]
    pool = list(range(len(q) - 400, len(q)))
    for i in sorted(set([len(q) - 1] + rnd.sample(pool, max(0, n - 1)))):
        today = date.fromisoformat(q[i])
        through = date.fromisoformat(q[i - 1])
        src = _source(recs, {"live": {"finished": through.isoformat(), "today": today.isoformat()}})
        S = recs["QQQ"]["close"][i]
        levels = {}
        for sym in AF.VOL_INDEXES:
            r = recs.get(sym)
            if r and today.isoformat() in r["dates"]:
                levels[sym] = r["close"][r["dates"].index(today.isoformat())]
        cut = {s: _cut(r, today) for s, r in recs.items()}
        ctx = AF.option_context(cut, through, today, S, levels, [])
        x = ctx["x"]
        s = stats.setdefault("_live", {"dates": 0, "identical": 0})
        s["dates"] += 1
        fin, tod = src["finished"], src["today"]
        bad = []
        for f in FIELDS:
            if f == "tr":                                             # today's total return: core accounting only
                continue
            mine = [float(v) if f != "month_start" else bool(v) for v in getattr(x, f)]
            if f in AF.SIGNAL_FIELDS:                                 # read at t - 1: the finished data's signals
                mine, ref = mine[:-1], fin[f]
            else:                                                     # today's row: price, rate, month start
                ref = tod[f]
            ok = len(mine) == len(ref) and all((a == b) or (a != a and b is None) for a, b in zip(mine, ref))
            if not ok:
                bad.append(f)
        if [str(d.date()) for d in x.dates] != tod["dates"]:
            bad.append("dates")
        if {k: float(v) for k, v in ctx["plans"].items()} != fin["plans"]:
            bad.append("plans")
        import numpy as np
        T = np.array([0.05, 0.1, 0.25, 0.5, 1.0])
        Fw = np.ones(5) * float(x.S[-1])
        ivs = [float(v) for K in (0.8, 1.0, 1.2) for v in ctx["surface"].iv(len(x.dates) - 1, Fw * K, Fw, T)]
        if ivs != tod["iv"]:
            bad.append("surface")
        if bad:
            diffs.append({"part": "L", "market": name, "date": today.isoformat(), "fields": bad})
        else:
            s["identical"] += 1


def _cut(rec, t):
    n = sum(1 for d in rec["dates"] if d <= t.isoformat())
    return {k: (v[:n] if isinstance(v, list) else v) for k, v in rec.items()}


def run():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    stats, diffs, markets = {}, [], []
    rnd = random.Random(20261017)
    sources = []
    if os.environ.get("APEX_SOURCE_DATA"):
        sources.append(("source_cache_ca8ac1f", records_of(os.environ["APEX_SOURCE_DATA"])))
    for seed in range(1, N_SYNTH + 1):
        sources.append(("synthetic_%d" % seed, {s: r for s, r in market(seed).items() if s in AF.SYMBOLS}))
    for name, recs in sources:
        n = replay(name, recs, stats, diffs)
        live(name, recs, LIVE_SAMPLES, rnd, stats, diffs)
        markets.append({"market": name, "dates": n})
    sleeves = sorted(k for k in stats if not k.startswith("_"))
    inp, lv = stats.get("_inputs", {}), stats.get("_live", {})
    cases = sum(stats[s]["days"] for s in sleeves) + inp.get("fields", 0) + inp.get("iv_points", 0) + lv.get("dates", 0)
    same = sum(stats[s]["identical"] for s in sleeves) + inp.get("identical", 0) + inp.get("iv_identical", 0) + \
        lv.get("identical", 0)
    covered = sorted(set(sleeves) | {"apex_n7_omni", "apex_council_btc"})
    res = {"sleeve": "apex_options", "family": "apex_options", "sleeves": covered, "cases": cases, "identical": same,
           "n_diffs": len(diffs), "diffs": diffs[:10], "markets": markets, "per_sleeve": stats,
           "method": "source Book.run recorded in the cursor2 tree (state handed to decide + its trades, every day) vs "
                     "the vendored strategy re-run on desk/feedlib/apex_book.LiveBook replaying those states; "
                     "build_inputs and the surface source vs vendored; tail_hedge_overlay traced vs tail_rule; "
                     "option_context vs the source on sampled dates; exact equality. The Variance Value rule is "
                     "shared by O6 / O10 / O11 / N7 (overlay) / C7 / the Council (variance_value_cash)."}
    write_receipt("apex_options", res)
    return res


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in run().items() if k != "per_sleeve"}, indent=1)[:3000])
