"""griffith_intraday: the SOURCE's own agents (agentic-trading-desk main @4c8c179c, run unmodified in a scratch copy of
its tree: GRIFFITH_SRC) vs the port's line-for-line functions (desk/sleeves/families/griffith_intraday.py).

  trend     app.TrendAgent.proposals over sequences of SPY 5-minute tapes (new / repeated newest bar, short tapes,
            held / flat, a working order) — side, quantity, price, and the remembered newest bar;
  scan      AgenticDesk.broad_scan + market_regime over random IEX snapshot sets (missing lanes, stale lanes, spreads
            and prices at the filters' edges) — every candidate field, the order, the regime;
  research  ResearchEngine.analyze over random headline sets — scores and kept headlines;
  setups    SetupAgents.decide over random 1-minute tapes (breakouts, VWAP hugs, gaps, extensions) and regimes —
            setup, decision, thesis, every technical;
  funnel    ScopePlane.funnel + watch_population (sqlite, persisted across a run sequence) over random decision sets —
            radar / armed / hands and the watch population.

    GRIFFITH_SRC=/path/to/scratch/agentic_src python3 -m tools.parity.griffith_intraday [n_cases]"""
import json
import math
import os
import random
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from desk.sleeves.families import griffith_intraday as P

from . import write_receipt
from .griffith import run_source

N = 1000
WORDS = sorted(P.POSITIVE | P.NEGATIVE | P.CATALYST | {"the", "shares", "company", "reports", "quarter", "stock",
                                                         "rally", "falls", "update", "market", "Beat", "UPGRADE"})
SRC = r'''
import sys, json, tempfile, pathlib, types
sys.dont_write_bytecode = True
import agentic_runtime as A
from app import TrendAgent, load_config
from scope_runtime import ScopePlane
from strategy_system import StrategyDecision
cfg = load_config()
store = types.SimpleNamespace(event=lambda *a, **k: None)
desk = object.__new__(A.AgenticDesk)
desk.agent_config = cfg["agentic"]
out = {"trend": [], "scan": [], "research": [], "setups": [], "funnel": []}
for seq in PAYLOAD["trend"]:
    agent = TrendAgent(cfg, store)
    res = []
    for step in seq:
        props = agent.proposals({"SPY": step["bars"]}, step["positions"], step["orders"])
        res.append({"props": [[p.symbol, p.side, p.qty, p.reference_price] for p in props],
                    "last": agent.last_bar.get("SPY")})
    out["trend"].append(res)
for case in PAYLOAD["scan"]:
    cands = desk.broad_scan(case["snaps"])
    out["scan"].append({"cands": [A.asdict(c) for c in cands], "regime": desk.market_regime(case["snaps"])})
for case in PAYLOAD["research"]:
    r = A.ResearchEngine().analyze(case["news"], case["symbols"])
    out["research"].append({k: [v[0], v[1]] for k, v in r.items()})
for case in PAYLOAD["setups"]:
    c = A.Candidate(**case["cand"])
    d = A.SetupAgents().decide(c, case["bars"], case["regime"])
    out["setups"].append(A.asdict(d))
import shutil
for seq in PAYLOAD["funnel"]:
    tmp = tempfile.mkdtemp(prefix="case_")                         # inside PAYLOAD["tmp"]
    plane = ScopePlane(pathlib.Path(tmp) / "s.db", seq["universe"])
    res = []
    for run in seq["runs"]:
        ds = [StrategyDecision(decisionId=d["id"], strategyId=d["strategy"], scannerVersion=d["version"], symbol=d["symbol"],
                               asOf="x", evidenceHash="h", status=d["status"], score=d["score"]) for d in run]
        f = plane.funnel(ds, radar_max=seq["radar"], armed_max=seq["armed"], hands_max=seq["hands"])
        res.append({"funnel": f, "watch": plane.watch_population(seq["watch"])})
    out["funnel"].append(res)
    shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps(out))
'''


def _ts(base, minutes):
    return (base + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def trend_seq(rnd):
    base = datetime(2026, 3, 2, 14, 30, tzinfo=timezone.utc) + timedelta(days=rnd.randint(0, 200))
    px, bars, steps = rnd.uniform(400, 600), [], []
    held, pending = None, False
    for k in range(rnd.randint(55, 90)):
        drift = rnd.choice([0.0015, -0.0015, 0.0, 0.0004])
        px *= 1 + rnd.gauss(drift, 0.002)
        bars.append({"t": _ts(base, 5 * k), "o": px, "h": px * 1.001, "l": px * 0.999, "c": round(px, 2),
                     "v": rnd.randint(1000, 90000)})
        if k < 30 and rnd.random() < 0.7:
            continue
        u = rnd.random()
        if u < 0.1:
            held = None
        elif u < 0.2:
            held = round(rnd.uniform(0.1, 0.3), 6)
        pending = rnd.random() < 0.1
        window = bars[-rnd.choice([50, 50, 50, 49, 50]):]
        steps.append({"bars": window, "positions": ([{"symbol": "SPY", "qty": str(held)}] if held else []),
                      "orders": ([{"symbol": "SPY"}] if pending else []), "qty": held, "pending": pending})
        if rnd.random() < 0.15:
            steps.append(dict(steps[-1]))               # the same newest bar again
    return steps


def snap(rnd, base):
    def stamp():
        return _ts(base, -rnd.randint(0, 600)) if rnd.random() < 0.95 else rnd.choice([None, "bad", ""])
    edge = rnd.random() < 0.15
    px = rnd.choice([4.99, 5.0, 1000.0, 1000.01, rnd.uniform(1, 2000)]) if edge else rnd.uniform(6, 600)
    s = {}
    if rnd.random() < 0.95:
        s["dailyBar"] = {"o": px * rnd.uniform(0.95, 1.05), "c": px * rnd.uniform(0.98, 1.02),
                         "v": rnd.choice([0, rnd.randint(1000, 50_000_000), rnd.randint(1000, 50_000_000)]),
                         "t": stamp()}
    if rnd.random() < 0.95:
        s["prevDailyBar"] = {"c": rnd.choice([0, px * rnd.uniform(0.9, 1.1), px * rnd.uniform(0.9, 1.1)]),
                             "v": rnd.choice([0, rnd.randint(1000, 50_000_000)])}
    if rnd.random() < 0.7:
        s["minuteBar"] = {"c": px * rnd.uniform(0.99, 1.01), "t": stamp()}
    if rnd.random() < 0.9:
        bid = px * rnd.uniform(0.99, 1.0)
        ask = bid * (rnd.uniform(1.0, 1.007) if rnd.random() < 0.8 else rnd.choice([0, 0.99, 1.02]))
        s["latestQuote"] = {"bp": rnd.choice([bid, bid, bid, 0]), "ap": ask, "t": stamp()}
    if rnd.random() < 0.7:
        s["latestTrade"] = {"p": px * rnd.uniform(0.995, 1.005), "t": stamp()}
    return s


def scan_case(rnd):
    base = datetime(2026, 5, 4, 15, 0, tzinfo=timezone.utc)
    names = ["SPY", "QQQ", "IWM"] + [f"S{i}" for i in range(rnd.randint(3, 25))]
    return {"snaps": {n: snap(rnd, base) for n in names if rnd.random() < 0.95}}


def research_case(rnd):
    syms = [f"S{i}" for i in range(rnd.randint(1, 8))]
    news = []
    for _ in range(rnd.randint(0, 30)):
        words = [rnd.choice(WORDS) for _ in range(rnd.randint(2, 9))]
        news.append({"headline": " ".join(w if rnd.random() < 0.8 else w + "-x" for w in words),
                     "symbols": rnd.sample(syms + ["OTHER"], rnd.randint(1, min(3, len(syms) + 1)))})
    return {"news": news, "symbols": syms}


def setup_case(rnd):
    px = rnd.uniform(5, 500)
    n = rnd.randint(30, 200)
    mode = rnd.choice(["breakout", "vwap", "gap", "extended", "random"])
    bars = []
    for k in range(n):
        late = k >= n - 12
        drift = {"breakout": 0.0009 if late else 0.0, "vwap": 0.0002 if late else 0.0, "gap": 0.0002,
                 "extended": 0.004, "random": rnd.gauss(0, 0.001)}[mode]
        px *= 1 + rnd.gauss(drift, 0.0006 if mode in ("breakout", "vwap") else 0.0015)
        h, lo = px * (1 + abs(rnd.gauss(0, 0.0007))), px * (1 - abs(rnd.gauss(0, 0.0007)))
        b = {"t": k, "o": px, "h": h, "l": lo, "c": px, "v": rnd.randint(100, 50000)}
        if rnd.random() < 0.9:
            b["vw"] = (h + lo + px) / 3
        bars.append(b)
    last = bars[-1]["c"]
    price = max(b["h"] for b in bars[-20:]) * 1.0002 if mode == "breakout" else last * rnd.choice([1.0, 1.0, 1.001,
                                                                                                    0.999, 1.02])
    cand = {"symbol": "S", "price": price, "score": rnd.uniform(0, 8), "gap_percent": rnd.choice([0.5, 2.0, 3.5, -1.0]),
            "intraday_percent": rnd.uniform(-2, 2), "relative_volume": rnd.choice([0.8, 1.5, 2.5, 1.49]),
            "spread_percent": 0.1, "dollar_volume": 1e6, "catalyst_score": rnd.choice([0.0, 0.5, 1.5, -1.0])}
    return {"cand": cand, "bars": bars, "regime": rnd.choice(["risk_on", "neutral", "neutral", "risk_off"])}


def funnel_seq(rnd):
    uni = [f"N{i:03d}" for i in range(40)]
    strategies = [("PARALLAX", ["PX_1_3_0_EXACT", "PX_1_3_0_CHALLENGER"]),
                  ("LEADERS_REST", ["LR_1_0_0_EXACT", "LR_1_1_0_CORRECTED"]),
                  ("foliotend-location-first-swing", ["LF_2_0_0_EXACT", "LF_2_1_0_CORRECTED"])]
    runs = []
    for r in range(rnd.randint(1, 4)):
        ds = []
        for s in rnd.sample(uni, rnd.randint(5, 40)):
            for strat, versions in strategies:
                for v in versions:
                    if rnd.random() < 0.7:
                        ds.append({"id": f"{strat}:{s}:{r}:{v}", "strategy": strat, "version": v, "symbol": s,
                                   "status": rnd.choice(["BUY", "SETUP", "WATCH", "WAIT", "AVOID", "UNAVAILABLE"]),
                                   "score": rnd.choice([None, round(rnd.uniform(0, 100)), 100, 0, 48])})
        runs.append(ds)
    radar = rnd.randint(1, 30)
    armed = rnd.randint(1, 30)
    hands = rnd.randint(1, 30)
    return {"universe": uni, "runs": runs, "radar": radar, "armed": armed, "hands": hands,
            "watch": rnd.randint(1, 60)}


def port_funnel(seq):
    states, res = {}, []

    class D:
        def __init__(self, d):
            self.symbol, self.strategyId, self.scannerVersion = d["symbol"], d["strategy"], d["version"]
            self.status, self.score = d["status"], d["score"]
    for run in seq["runs"]:
        f = P.funnel([D(d) for d in run], states, seq["radar"], seq["armed"], seq["hands"])
        res.append({"funnel": f, "watch": P.watch_population(states, seq["watch"])})
    return res


def same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main(argv):
    tree = os.environ.get("GRIFFITH_SRC")
    if not tree or not os.path.isdir(tree):
        raise SystemExit("set GRIFFITH_SRC to a scratch copy of agentic-trading-desk@4c8c179")
    n = int(argv[0]) if argv else N
    rnd = random.Random(424242)
    payload = {"trend": [trend_seq(rnd) for _ in range(max(1, n // 4))], "scan": [scan_case(rnd) for _ in range(n)],
               "research": [research_case(rnd) for _ in range(n)], "setups": [setup_case(rnd) for _ in range(n)],
               "funnel": [funnel_seq(rnd) for _ in range(max(1, n // 4))]}
    src = run_source(SRC, payload, tree, 7200, "griffith_intraday_parity_")
    diffs, counts = [], {}
    # trend
    k = 0
    for seq, res in zip(payload["trend"], src["trend"]):
        last = None
        for step, want in zip(seq, res):
            k += 1
            prop, last = P.trend_proposal(step["bars"], last, step["qty"], step["pending"])
            got = [["SPY", prop[0], prop[1], prop[2]]] if prop else []
            if not same(got, want["props"]) or last != want["last"]:
                diffs.append({"what": "trend", "port": [got, last], "source": [want["props"], want["last"]]})
    counts["trend_steps"] = k
    counts["trend_orders"] = sum(len(s["props"]) for r in src["trend"] for s in r)
    for case, want in zip(payload["scan"], src["scan"]):
        got = [asdict(c) for c in P.broad_scan(case["snaps"])]
        if not same(got, want["cands"]) or P.market_regime(case["snaps"]) != want["regime"]:
            diffs.append({"what": "scan", "port": got[:3], "source": want["cands"][:3]})
    counts["scan_candidates"] = sum(len(w["cands"]) for w in src["scan"])
    for case, want in zip(payload["research"], src["research"]):
        got = {k: [v[0], v[1]] for k, v in P.analyze(case["news"], case["symbols"]).items()}
        if not same(got, want):
            diffs.append({"what": "research", "port": got, "source": want})
    for case, want in zip(payload["setups"], src["setups"]):
        got = asdict(P.decide(P.Candidate(**case["cand"]), case["bars"], case["regime"]))
        if not same(got, want):
            diffs.append({"what": "setup", "port": got, "source": want})
    counts["setups"] = {s: sum(1 for w in src["setups"] if w["setup"] == s and w["decision"] == "BUY")
                        for s in ("momentum_breakout", "vwap_pullback", "gap_continuation")}
    for seq, want in zip(payload["funnel"], src["funnel"]):
        got = port_funnel(seq)
        if not same(got, want):
            diffs.append({"what": "funnel", "port": got, "source": want})
    cases = sum(len(payload[k]) for k in ("scan", "research", "setups")) + k + sum(
        len(s["runs"]) for s in payload["funnel"])
    path_ = write_receipt("griffith_intraday", {
        "family": "griffith_intraday", "sleeves": ["griffith_auditable_20_50_trend"] + list(P.LEGACY),
        "cases": cases, "identical": cases - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:30],
        "coverage": counts, "source": {"repo": "agentic-trading-desk", "commit": P.SOURCE["commit"],
                                       "run": "app.TrendAgent, AgenticDesk.broad_scan/market_regime, ResearchEngine, "
                                              "SetupAgents, ScopePlane.funnel/watch_population"}})
    print(json.dumps({"cases": cases, "diffs": len(diffs), "coverage": counts, "receipt": path_}))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
