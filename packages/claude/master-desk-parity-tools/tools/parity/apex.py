"""apex (the 24 APEX / Aurelia (Cursor2) allocation sleeves): the SOURCE's own research code (cursor2 main
@ca8ac1f650670e1d, run in its own tree: CURSOR2_SRC, default /home/user/cursor2, no bytecode written there) vs the
port, three ways, on every market below.

  A. series   every date's decision. desk/feedlib/apex_rules.py (the readings: the source desk's planned_position
              on each strategy's own simulator run, the unshifted lag choices, the multi-asset loops re-run) runs on
              cursor2's own modules in the source tree and on the vendored modules in the desk, same data: every
              value of every date must be identical (NaN = NaN).
  B. backtest the same readings against the source backtest's own next-session values, read straight off the
              research functions' outputs in the source tree (position.shift(-1); the lag-shifted semis share,
              boost, holding, bond and diversifier choices .shift(-2); PRISM's held weights .shift(-2); Sector
              Kings' _lagged_book read with one-hot returns; E7 on the market's own calendar): the live readings
              ARE the backtest's decisions, on every date where both exist. One exception, counted as explained:
              E7 on the index's third-last date when the index stops inside a month (the backtest's turn-of-month
              window then marks the index's last date as the month's last session; the reading, like the live
              decision, uses the exchange calendar).
  C. live     the port's live path (desk/feedlib/apex.compute: the records cut at a sampled decision date, the
              sessions after it) vs the source computing the same readings on the same cut records.
Markets: the source's own Yahoo cache (cursor2 data/cache/yahoo, tracked at ca8ac1f, through 2026-10-09: the data
its research ran on; APEX_SOURCE_DATA = its JSON dump, `python3 -m tools.parity.apex --dump <out.json>` with pyarrow
importable) and APEX_SYNTH deterministic randomized markets (tools/parity/apex_synth.py, seeds 1..N).

    python3 -m tools.parity.run apex           (APEX_SOURCE_DATA, CURSOR2_SRC, APEX_SYNTH, APEX_LIVE_SAMPLES)"""
import json
import os
import random
import sys
import tempfile
from datetime import date

from desk.feedlib import apex as AF

from . import old_run, write_receipt
from .apex_synth import market

SRC_TREE = os.environ.get("CURSOR2_SRC", "/home/user/cursor2")
N_SYNTH = int(os.environ.get("APEX_SYNTH", "4"))
LIVE_SAMPLES = int(os.environ.get("APEX_LIVE_SAMPLES", "6"))
RULES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desk",
                     "feedlib", "apex_rules.py")

SRC = r'''
import json, sys, types
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
import desk.data.series as SER
from desk import features as F, inventions as N, round3 as C, strategies as S
from desk.backtest import engine as E
from desk.agents.portfolio import alpaca_weights
from desk.agents.risk import planned_position
ns = {"__name__": "apex_rules"}
exec(compile(open(PAYLOAD["rules"]).read(), PAYLOAD["rules"], "exec"), ns)
R = types.SimpleNamespace(**ns)
mods = R.Mods(S=S, N=N, C=C, SER=SER, F=F, E=E, AG=types.SimpleNamespace(planned_position=planned_position,
                                                                       alpaca_weights=alpaca_weights))
sessions = [pd.Timestamp(d) for d in PAYLOAD["sessions"]]
def enc(v):
    if isinstance(v, pd.Series):
        return [None if x is None or (isinstance(x, float) and x != x) else (x if isinstance(x, str) else float(x))
                for x in v.tolist()]
    if isinstance(v, float) and v != v:
        return None
    return v
def flat(d):
    out = {}
    for k, v in (d.get("plan") or {}).items():
        out["plan." + k] = v
    for i, b in enumerate(d.get("books") or []):
        for k, v in b[1].items():
            out["books.%d.%s" % (i, k)] = v
    for k in ("idle", "boost"):
        if k in d:
            out[k] = d[k]
    for k, v in (d.get("obs") or {}).items():
        out["obs." + k] = v
    return out
if PAYLOAD.get("t"):                                   # C: the readings on the cut records' last date
    dec = R.decide_all(mods, pd.Timestamp(PAYLOAD["t"]), sessions)
    out = {sid: ({"error": d["error"]} if "error" in d else {k: enc(v) for k, v in flat(d).items()})
           for sid, d in dec.items() if sid != "_signals"}
    json.dump({"dec": out}, open(PAYLOAD["out"], "w"))
    print(json.dumps({"ok": True}))
    raise SystemExit(0)
dec = R.decide_all(mods, sessions=sessions, series=True)
m = SER.ndx_market()
idx = m.index
sig = S.compute_signals(m)
# B: the backtest's own next-session values, read off the research functions' outputs
nx1 = lambda s: s.reindex(idx).shift(-1)
nx2 = lambda s: s.reindex(idx).shift(-2)
pos = lambda df: nx1(df["position"])
def locals_of(fn, *a, **kw):
    return R.call_with_locals(fn, *a, **kw)
bt = {}
res = S.core_variants(m, sig)
bt["apex_trend_har_tiers"] = {"plan.NDX": pos(res["APEX-50F"])}
bt["apex_benchmarks"] = {"plan.NDX": pos(res["QQQ"])}
bond_r = SER.treasury_7_10y_returns(idx)
onmap = lambda s: s.map(lambda x: {1.0: "TSY", 0.0: "CASH"}.get(x) if x == x else None)
df, loc = locals_of(S.apex_v11, m, sig, bond_r)
_, loc3 = locals_of(S.e3_defensive_bonds, m, sig, bond_r, S.APEX_V11)
bt["apex_v11_defensive_bond"] = {"plan.NDX": pos(df), "idle": onmap(nx2(loc3["on_held"]))}
vix, vix3m = SER.aligned_close("^VIX", idx), SER.aligned_close("^VIX3M", idx)
bt["apex_e1_vix_term_gate"] = {"plan.NDX": pos(S.e1_vix_term_structure(m, sig, vix, vix3m))}
bt["apex_e2_double7_dip"] = {"plan.NDX": pos(S.e2_dip_overlay(m, sig))}
df, loc = locals_of(S.e3_defensive_bonds, m, sig, bond_r)
bt["apex_e3_defensive_treasuries"] = {"plan.NDX": pos(df), "idle": onmap(nx2(loc["on_held"]))}
df = S.e5_semis_tilt(m, sig, Y.get_daily("SMH")["adj_close"].pct_change())
L, sh = pos(df), nx2(df["semis_share"])
bt["apex_e5_semis_rs_tilt"] = {"plan.NDX": (1.0 - sh) * L, "plan.SMH": sh * L}
df = S.e6_overnight_boost(m, sig, SER.adjusted_open_close("QQQ"))
bt["apex_e6_overnight_boost"] = {"plan.NDX": pos(df), "boost": nx2(df["boost"])}
bt["apex_e7_turn_of_month"] = {"plan.NDX": pos(S.e7_turn_of_month(m, sig))}
tnx = Y.get_daily("^TNX")["close"]
sleeves = N.sleeve_returns(idx, m.r)
n1 = N.n1_duration_shield(m, sig, tnx)
bt["apex_n1_duration_shield"] = {"plan.NDX": pos(n1)}
bt["apex_n7_omni"] = {"plan.NDX": pos(n1)}
df = N.n2_silicon_switch(m, sleeves["SOX"])
L, h = pos(df), nx2(df["holding_sox"])
bt["apex_n2_silicon_switch"] = {"plan.NDX": L * (1.0 - h), "plan.SOX": L * h}
for sid, names in (("apex_n3_prism_classic", ["NDX", "TSY", "GOLD", "OIL", "USD"]),
                   ("apex_n4_prism_paradigm", ["NDX", "SOX", "GOLD", "BTC"])):
    p = N.prism({k: sleeves[k] for k in names}, m)
    bt[sid] = {"plan." + k: nx2(p["w_" + k]) for k in names}
n5, L5 = N.n5_gestalt(m, sig, sleeves["SOX"])
bt["apex_n5_gestalt"] = {"plan.NDX": pos(n5)}
n6 = N.n6_ensemble(m, sig, L5)
bt["apex_n6_gestalt_apex"] = {"plan.NDX": pos(n6)}
gold = N.aligned_returns("GC=F", idx, field="close")
er = N.aligned_returns("QQQ", idx, field="adj_close").dropna()
p = C.c1_aurelia(er, gold.reindex(er.index), SER.risk_free_daily(er.index))
bt["apex_c1_aurelia_pair"] = {"plan.NDX": nx2(p["w_NDX"]), "plan.GOLD": nx2(p["w_GOLD"])}
with R.spy((C,), "_lagged_book") as (calls, real):
    C.c2_sector_kings(idx, m.rf)
d2 = calls[-1][0][0]
plan = {}
for j, s_ in enumerate(C.SECTORS):
    probe = np.zeros(d2.shape); probe[:, j] = 1.0
    plan["plan." + s_] = nx2(pd.Series(real(d2, probe, np.zeros(d2.shape[0]), bps=0.0, fin_spread=0.0), index=idx))
bt["apex_c2_sector_kings"] = plan
bt["apex_c3_follow_through"] = {"plan.NDX": pos(C.c3_follow_through(m, sig))}
dxy = N.aligned_returns("DX-Y.NYB", idx, field="close")
df, loc = locals_of(C.c4_broken_hedge, m, sig, sleeves["TSY"].reindex(idx), gold.reindex(idx), dxy.reindex(idx),
                    gate=0.20, switch_bps=3.0)
bt["apex_c4_broken_hedge"] = {"plan.NDX": pos(df), "idle": nx2(loc["chosen"])}
bt["apex_c5_reflex"] = {"plan.NDX": pos(C.c5_reflex(m, sig, sleeves["SOX"])[0])}
bt["apex_c6_slingshot"] = {"plan.NDX": pos(C.c6_slingshot(m, sig, tnx))}
with R.spy((C,), "simulate") as (calls, _):
    C.gold_sleeve(idx, m.rf, gold)
g = pos(calls[-1][2])
bt["apex_c7_council"] = {"books.0.NDX": pos(n6), "books.1.GOLD": g}
_, loc = locals_of(N.prism_targets, {"BTC": sleeves["BTC"]}, idx)
b = pos(E.simulate(loc["unit"]["BTC"], sleeves["BTC"].reindex(idx).fillna(0.0), m.rf,
                   costs=E.FUTURES_COSTS.with_(trade_bps=N.PRISM_BPS["BTC"]), lag=1, band=0.20))
bt["apex_council_btc"] = {"books.0.NDX": pos(n6), "books.1.GOLD": g, "books.2.BTC": b}
series = {sid: {k: enc(v) for k, v in flat(d).items()} for sid, d in dec.items() if sid != "_signals"}
back = {sid: {k: enc(v) for k, v in d.items()} for sid, d in bt.items()}
json.dump({"index": [str(d.date()) for d in idx], "series": series, "backtest": back}, open(PAYLOAD["out"], "w"))
print(json.dumps({"ok": True, "n": len(idx)}))
'''


def _flat(dec):
    out = {}
    for k, v in (dec.get("plan") or {}).items():
        out["plan." + k] = v
    for i, b in enumerate(dec.get("books") or []):
        for k, v in b[1].items():
            out["books.%d.%s" % (i, k)] = v
    for k in ("idle", "boost"):
        if k in dec:
            out[k] = dec[k]
    for k, v in (dec.get("obs") or {}).items():
        out["obs." + k] = v
    return out


def _val(v):
    if v is None:
        return None
    if isinstance(v, str):
        return v
    v = float(v)
    return None if v != v else v


def _eq(a, b):
    a, b = _val(a), _val(b)
    if a is None or b is None:
        return a is None and b is None
    return a == b


def records_of(path):
    raw = json.load(open(path))
    return {s: raw[s] for s in AF.SYMBOLS if s in raw}


def _source(recs, sessions, t=None):
    with tempfile.TemporaryDirectory() as tmp:
        dpath, opath = os.path.join(tmp, "data.json"), os.path.join(tmp, "out.json")
        json.dump(recs, open(dpath, "w"))
        old_run(SRC, {"data": dpath, "out": opath, "rules": RULES, "t": t,
                      "sessions": [d.isoformat() for d in sessions]}, timeout=7200, tree=SRC_TREE)
        return json.load(open(opath))


def _after(recs, n=40):
    """the calendar after the market's last session (synthetic markets live on the desk calendar)."""
    last = date.fromisoformat(recs["QQQ"]["dates"][-1])
    return AF.future_sessions(last)


def _tom_cut_short(idx, after):
    """the source backtest's turn_of_month_window flags its index's last date as its month's last trading day
    (pos == size) while the exchange calendar continues that month: the index cut the month short."""
    import pandas as pd
    from desk.vendor.aurelia import features as F
    a = pd.DatetimeIndex([pd.Timestamp(x) for x in idx])
    b = a.append(pd.DatetimeIndex([pd.Timestamp(x) for x in after]))
    return F.turn_of_month_window(a).iloc[-1] == 1.0 and F.turn_of_month_window(b).loc[a[-1]] == 0.0


def series_parity(name, recs, stats, diffs, explained):
    """A + B on one market."""
    sessions = _after(recs)
    src = _source(recs, sessions)
    idx = src["index"]
    frames = AF.frames_for(recs, date(2100, 1, 1))
    port = AF.decide_all(frames, sessions=sessions, series=True)
    cut_short = _tom_cut_short(idx, sessions)
    for sid, ser in src["series"].items():
        mine = _flat(port[sid])
        st = stats.setdefault(sid, {"dates": 0, "identical": 0, "backtest_dates": 0, "backtest_identical": 0,
                                    "backtest_explained": 0, "live": 0, "live_identical": 0})
        keys = sorted(set(ser) | set(mine))
        dkeys = [k for k in keys if k.startswith(("plan.", "books."))]
        for i, d in enumerate(idx):
            vals = [(k, ser[k][i] if k in ser else None, mine[k].iloc[i] if k in mine else None) for k in keys]
            if all(_val(a) is None and _val(b) is None for k, a, b in vals if k in dkeys):
                continue                                        # no decision defined on this date
            st["dates"] += 1
            bad = [(k, _val(a), _val(b)) for k, a, b in vals if not _eq(a, b)]
            if bad:
                if len(diffs) < 40:
                    diffs.append({"part": "A", "market": name, "sleeve": sid, "date": d, "diff": bad[:4]})
            else:
                st["identical"] += 1
        bt = src["backtest"].get(sid) or {}
        for i, d in enumerate(idx[:-2]):                        # the backtest's next-session values exist through
            vals = [(k, ser[k][i], bt[k][i]) for k in bt]       # the third-last date
            if all(_val(b) is None for _, _, b in vals):
                continue
            st["backtest_dates"] += 1
            bad = [(k, _val(a), _val(b)) for k, a, b in vals if not _eq(a, b)]
            if bad and sid == "apex_e7_turn_of_month" and i == len(idx) - 3 and cut_short:
                # E7 boosts on the turn-of-month flag two sessions ahead: from idx[-3] that is the index's last
                # date, which the backtest's window marks as a month end because its index stops there; the
                # reading uses the exchange calendar, as the live decision must (counted, never identical)
                st["backtest_explained"] += 1
                explained.append({"part": "B", "market": name, "sleeve": sid, "date": d, "diff": bad[:4],
                                  "why": "the source backtest's turn_of_month_window marks its index's last date "
                                         "(%s) as the month's last session; the exchange calendar continues the "
                                         "month (next session %s)" % (idx[-1], sessions[0].isoformat())})
            elif bad:
                if len(diffs) < 40:
                    diffs.append({"part": "B", "market": name, "sleeve": sid, "date": d, "diff": bad[:4]})
            else:
                st["backtest_identical"] += 1
    return src


def _cut(rec, t):
    if not rec:
        return rec
    n = sum(1 for d in rec["dates"] if d <= t.isoformat())
    return {k: (v[:n] if isinstance(v, list) else v) for k, v in rec.items()}


def live_parity(name, recs, idx, n, rnd, stats, diffs):
    """C: the port's live compute() vs the source's readings, both on the records cut at sampled dates."""
    pool = list(range(len(idx) - 400, len(idx) - 3))
    picks = sorted(set([len(idx) - 1] + rnd.sample(pool, max(0, n - 1))))
    for i in picks:
        t = date.fromisoformat(idx[i])
        sessions = AF.future_sessions(t)
        cut = {s: _cut(r, t) for s, r in recs.items()}
        mine = AF.compute(cut, t, sessions=sessions)
        src = _source(cut, sessions, t=t.isoformat())["dec"]
        for sid, s in src.items():
            st = stats[sid]
            st["live"] += 1
            d = mine["sleeves"].get(sid) or {}
            if "error" in s or "error" in d:
                diffs.append({"part": "C", "market": name, "sleeve": sid, "date": idx[i], "source": s.get("error"),
                              "port": d.get("error")})
                continue
            m = _flat(d)
            keys = sorted(set(s) | set(m))
            bad = [(k, _val(s.get(k)), _val(m.get(k))) for k in keys if not _eq(s.get(k), m.get(k))]
            if bad:
                diffs.append({"part": "C", "market": name, "sleeve": sid, "date": idx[i], "diff": bad[:4]})
            else:
                st["live_identical"] += 1
    return len(picks)


def run():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    stats, diffs, markets, explained = {}, [], [], []
    rnd = random.Random(20261016)
    sources = []
    if os.environ.get("APEX_SOURCE_DATA"):
        sources.append(("source_cache_ca8ac1f", records_of(os.environ["APEX_SOURCE_DATA"])))
    for seed in range(1, N_SYNTH + 1):
        sources.append(("synthetic_%d" % seed, {s: r for s, r in market(seed).items() if s in AF.SYMBOLS}))
    for name, recs in sources:
        src = series_parity(name, recs, stats, diffs, explained)
        n_live = live_parity(name, recs, src["index"], LIVE_SAMPLES, rnd, stats, diffs)
        markets.append({"market": name, "dates": len(src["index"]), "first": src["index"][0],
                        "last": src["index"][-1], "live_samples": n_live})
    sleeves = sorted(stats)
    cases = sum(stats[s]["dates"] + stats[s]["backtest_dates"] + stats[s]["live"] for s in sleeves)
    same = sum(stats[s]["identical"] + stats[s]["backtest_identical"] + stats[s]["live_identical"] for s in sleeves)
    res = {"sleeve": "apex", "family": "apex", "sleeves": sleeves, "cases": cases, "identical": same,
           "n_diffs": len(diffs), "diffs": diffs[:10], "explained": len(explained),
           "explained_cases": explained[:20], "markets": markets, "per_sleeve": stats,
           "method": "desk/feedlib/apex_rules on cursor2 @ca8ac1f's own modules in their tree vs on the vendored "
                     "modules [A: every date]; those readings vs the source backtest's own next-session values [B]; "
                     "the port's live compute() vs the source on records cut at sampled dates [C]; exact equality. "
                     "Explained (counted, not identical): E7 on the third-last date when the index cuts its last "
                     "month short (the backtest's turn-of-month window treats the index's end as a month end)."}
    write_receipt("apex", res)
    return res


def dump(out):
    """the source's own Yahoo cache (cursor2 data/cache/yahoo/*.parquet at ca8ac1f) -> one JSON records file."""
    import glob
    import pandas as pd
    res = {}
    for f in sorted(glob.glob(os.path.join(SRC_TREE, "data", "cache", "yahoo", "*.parquet"))):
        s = os.path.basename(f)[:-8]
        s = ("^" + s[4:]) if s.startswith("IDX_") else s
        s = (s[:-2] + "=F") if s.endswith("_F") else s
        df = pd.read_parquet(f)
        rec = {"dates": [d.date().isoformat() for d in df.index]}
        for c in ("open", "high", "low", "close", "volume", "adj_close"):
            rec[c] = [None if v != v else float(v) for v in df[c].tolist()]
        res[s] = rec
    json.dump(res, open(out, "w"))
    return len(res)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--dump":
        print(dump(sys.argv[2]))
    else:
        print(json.dumps({k: v for k, v in run().items() if k != "per_sleeve"}, indent=1)[:3000])
