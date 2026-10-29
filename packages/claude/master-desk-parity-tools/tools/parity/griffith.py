"""griffith (Leaders Rest, Parallax): the SOURCE runtime's own run_three_strategies + drain_strategy_handoffs
(agentic-trading-desk main @4c8c179c, run unmodified in a scratch copy of its tree: GRIFFITH_SRC) vs the port
(desk/sleeves/families/griffith.py), on deterministic randomized cases.

Per case: a random slice of the frozen SCOPE universe (in manifest order, always with the sector-proxy ETFs the
universe holds) on regime-switching daily paths of 300-550 sessions (Alpaca-shaped ISO stamps), an account (equity,
buying power), held names, the strategy's open risk, the capture time; then a delivery pass with its own held names,
working entries and asks (some missing, some at or below a plan stop, some after a plan expired).
Source: AgenticDesk built with object.__new__ — the real ScopePlane, StrategyLedger, ThreeStrategyOrchestrator,
ExecutionOverlays, PortfolioAllocator — once per strategy (active_versions narrowed to that strategy, so the two
sleeves' books stay separate as on the desk); stubbed: the bar fetch (the case tape), the risk snapshot (the case's
open risk; admission allowed), the correlation multiplier (1.0), SEC sector classification (none), the record-only
replay / brokerage planes, the broker (captures payloads), the RiskGate and new-entry admission (allow), the desk
position cap / Tensor reservation / hands budget (unbounded), the desk-wide allocator terms (never binding) — exactly
the gates the port removes. Compared: every decision (id, status, score, engine, references, reasons), every
armed handoff (allocation id, plan, quantity, expiry), every handoff's state after delivery and every order payload
(client id, qty, type, limit, trigger, take-profit, stop-loss, tif) against the port's intents.

    GRIFFITH_SRC=/path/to/scratch/agentic_src python3 -m tools.parity.griffith [n_cases]"""
import copy
import json
import os
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from desk.contract import View
from desk.feedlib import griffith as tape
from desk.sleeves.families import griffith as G
from desk.util import parse_ts

from . import old_run, trading_dates, write_receipt

N_CASES = 1000
NAMES = 18
# every temp file a source run creates lives in the harness-owned dir PAYLOAD["tmp"] (removed by run_source)
TEMP_PRELUDE = r'''
import os as _os, tempfile as _tempfile
_tempfile.tempdir = PAYLOAD["tmp"]
_os.environ["TMPDIR"] = PAYLOAD["tmp"]
'''


def temp_root():
    """a disk-backed temp root: the default temp dir, never the RAM-backed /dev/shm."""
    d = os.path.realpath(tempfile.gettempdir())
    return "/tmp" if d == "/dev/shm" or d.startswith("/dev/shm/") else d


def run_source(script, payload, tree, timeout, prefix):
    """old_run with a harness-owned temp dir on disk that the source's temp files go into, removed however the run
    ends (result, failure, timeout)."""
    with tempfile.TemporaryDirectory(prefix=prefix, dir=temp_root()) as tmp:
        return old_run(TEMP_PRELUDE + script, dict(payload, tmp=tmp), tree=tree, timeout=timeout)

MUST = ("SPY", "QQQ", "IWM", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV")
STRATS = {"LEADERS_REST": ("griffith_leaders_rest", ["LR_1_0_0_EXACT", "LR_1_1_0_CORRECTED"]),
          "PARALLAX": ("griffith_parallax", ["PX_1_3_0_EXACT", "PX_1_3_0_CHALLENGER"])}

SRC = r'''
import sys, json, tempfile, threading, pathlib, types, copy, shutil
sys.dont_write_bytecode = True
from datetime import datetime, timezone
import agentic_runtime as A
from strategy_orchestrator import ThreeStrategyOrchestrator
from strategy_execution import ExecutionOverlays, PortfolioAllocator
from strategy_ledger import StrategyLedger
from scope_runtime import ScopePlane
from portfolio_risk import PortfolioRiskPlane
import sqlite3
A.deterministic_order_intents = lambda *a, **k: []
BASE = A.load_config()
NEUTRAL = 1e12
FIX = {}
class FixedDT(datetime):
    @classmethod
    def now(cls, tz=None):
        t = FIX["now"]
        return t.astimezone(tz) if tz else t.replace(tzinfo=None)
A.datetime = FixedDT
class Risk:
    allocation_inputs = staticmethod(PortfolioRiskPlane.allocation_inputs)
    reserve = staticmethod(PortfolioRiskPlane.reserve)
    def classifications(self, symbols): return {}, {}
    def correlation_multiplier(self, symbol, snapshot, daily): return 1.0, {}
    def calculate(self, *a, **k): return {}
out = []
for case in PAYLOAD["cases"]:
    res = {}
    for strategy, versions in PAYLOAD["strategies"].items():
        cfg = copy.deepcopy(BASE)
        cfg["risk"]["max_order_notional"] = 1e18
        cfg["risk"]["paper_aggressive_profile"].update(total_risk_fraction=NEUTRAL, symbol_risk_fraction=NEUTRAL,
                                                       sector_risk_fraction=NEUTRAL, gross_notional_fraction=NEUTRAL)
        cfg["m5_deterministic_replay"]["enabled"] = False
        cfg["agentic"]["max_positions"] = 10 ** 9
        three = cfg["three_strategy"]
        three["active_versions"] = versions
        three["scope"]["symbols_per_shard"] = len(case["universe"])
        three["scope"]["positions_max"] = 10 ** 9
        three["hands_max"] = 10 ** 6
        three["tensor_reserved_positions"] = 0
        d = object.__new__(A.AgenticDesk)
        d.config, d.three_strategy_config = cfg, three
        d.agent_config = cfg["agentic"]
        d.paper_aggressive_config = dict(three.get("paper_aggressive_execution") or {})
        d.universe = list(case["universe"])
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="case_"))      # inside PAYLOAD["tmp"]
        d.scope = ScopePlane(tmp / "scope.db", d.universe)
        d.strategies = ThreeStrategyOrchestrator()
        d.tensor_experimental = types.SimpleNamespace(evaluate=lambda: [])
        d.strategy_ledger = StrategyLedger(tmp / "ledger.db")
        d.portfolio_risk = Risk()
        d.overlays = ExecutionOverlays()
        d.allocator = PortfolioAllocator(cfg["risk"]["paper_aggressive_profile"])
        d.replay = types.SimpleNamespace(health=lambda: {})
        d.brokerage_policy = types.SimpleNamespace(stress_intents=lambda *a: {}, capacity_intents=lambda *a: {})
        d.brokerage_reality = None
        d.store = types.SimpleNamespace(event=lambda *a, **k: None)
        d.lock = threading.Lock()
        d.last_strategy_cycle = 0.0
        bars = case["bars"]
        def bounded(symbols, timeframe, limit, days=None, max_calls=12, bars=bars):
            if timeframe != "1Day":
                return {}, {}
            return {s: bars[s][-limit:] for s in symbols if s in bars}, {}
        d.bounded_bars = bounded
        acct = {"equity": case["equity"], "buying_power": case["buying_power"]}
        d.state = {"session": "premarket", "account": acct,
                   "positions": [{"symbol": s, "qty": "1"} for s in case["held"]], "open_orders": [],
                   "portfolio_risk": {"byStrategy": {strategy: case["risk"][strategy]}, "admissionAllowed": True,
                                      "openRisk": 0.0, "bySymbol": {}, "bySector": {}, "grossNotional": 0.0,
                                      "pendingNotional": 0.0}}
        A.utc_now = lambda: case["captured_at"]
        FIX["now"] = datetime.fromisoformat(case["captured_at"])
        d.run_three_strategies({})
        db = sqlite3.connect(tmp / "ledger.db")
        decisions = [json.loads(p) for (p,) in db.execute("SELECT payload FROM strategy_decisions ORDER BY decision_id")]
        armed = [{"allocation_id": a, "symbol": s, "state": st, "expires_at": e, "created_at": c,
                  "plan": json.loads(p)["plan"], "allocation": json.loads(p)["allocation"]}
                 for a, s, st, e, c, p in db.execute(
                     "SELECT allocation_id,symbol,state,expires_at,created_at,payload FROM execution_handoffs "
                     "ORDER BY created_at,allocation_id")]
        # delivery
        FIX["now"] = datetime.fromisoformat(case["claim_at"])
        d.state.update(session="regular", positions=[{"symbol": s, "qty": "1"} for s in case["claim_held"]],
                       open_orders=[{"symbol": s, "side": "buy"} for s in case["claim_pending"]])
        d.new_entry_admission = lambda: {"allowed": True, "reasons": []}
        d.risk = types.SimpleNamespace(evaluate=lambda *a, **k: [])
        sent = []
        def submit(payload, sent=sent):
            sent.append(payload)
            return {"id": "b%d" % len(sent), "status": "accepted"}
        d.alpaca = types.SimpleNamespace(submit_paper_order=submit)
        snaps = {s: {"latestQuote": {"ap": a}} for s, a in case["asks"].items()}
        d.drain_strategy_handoffs(snaps)
        states = {a: [st, r] for a, st, r in db.execute("SELECT allocation_id,state,last_reason FROM execution_handoffs")}
        res[strategy] = {"decisions": decisions, "armed": armed, "states": states, "sent": sent}
        db.close()
        shutil.rmtree(tmp, ignore_errors=True)
    out.append(res)
print(json.dumps(out))
'''


def path(rnd, n, start, leader=False):
    """regime-switching daily path (trend legs, pullbacks, shocks) with Alpaca-shaped stamps; a leader trends up and
    rests (a 3-12% pullback or a tight range) over its last sessions."""
    dates = trading_dates(start, n)
    px, vol = rnd.uniform(4, 400), rnd.uniform(0.008, 0.04)
    base_v = rnd.uniform(5e4, 3e6)
    rows, left, drift = [], 0, 0.0
    rest = rnd.randint(6, 16)
    for k, d in enumerate(dates):
        if leader:
            drift = rnd.choice([-0.004, -0.002, 0.0]) if k >= n - rest else 0.0025
            vol = 0.012
        elif left <= 0:
            left = rnd.randint(8, 60)
            drift = rnd.choice([0.004, 0.002, 0.0008, 0.0, -0.001, -0.003])
            vol = max(0.004, vol * rnd.uniform(0.6, 1.5))
        left -= 1
        r = rnd.gauss(drift, vol)
        if rnd.random() < 0.015:
            r += rnd.choice((-1, 1)) * rnd.uniform(0.05, 0.15)
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + r))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = float(int(base_v * rnd.uniform(0.4, 2.2) * (2.5 if abs(r) > 2 * vol else 1)))
        stamp = datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
        hour = 4 if 3 <= stamp.month <= 10 else 5           # 00:00 ET in UTC, as Alpaca stamps daily bars
        rows.append({"t": stamp.replace(hour=hour).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": round(o, 4),
                     "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4), "v": v})
        px = c
    return rows


def make_case(i):
    rnd = random.Random(7000 + i)
    uni = tape.tape_symbols()
    pick = set(rnd.sample(uni, NAMES)) | {s for s in MUST if s in uni}
    names = [s for s in uni if s in pick]
    n = rnd.randint(300, 550)
    start = (datetime(2023, 1, 2) + timedelta(days=rnd.randint(0, 300))).date().isoformat()
    leaders = set(rnd.sample(names, len(names) // 3)) | {"SPY"}
    bars = {s: path(random.Random(i * 1000 + k), n, start, leader=s in leaders) for k, s in enumerate(names)}
    last = datetime.fromisoformat(bars["SPY"][-1]["t"].replace("Z", "+00:00"))
    captured = (last + timedelta(days=1)).replace(hour=10, minute=rnd.randint(0, 59), second=rnd.randint(0, 59))
    claim = captured + timedelta(hours=rnd.choice([4, 4, 4, 30, 54, 100, 130, 170]))
    equity = rnd.choice([25_000.0, 100_000.0, 250_000.0]) * rnd.uniform(0.8, 1.2)
    held = sorted(rnd.sample(names, rnd.randint(0, 3)))
    risk = {k: equity * rnd.choice([0.0, 0.0, 0.005, 0.02, 0.029, 0.031]) for k in STRATS}
    asks = {}
    for s in names:
        c = bars[s][-1]["c"]
        u = rnd.random()
        if u < 0.08:
            continue                                   # no fresh price
        asks[s] = round(c * (rnd.uniform(0.7, 0.92) if u < 0.18 else rnd.uniform(0.97, 1.04)), 2)
    return {"universe": names, "bars": bars, "captured_at": captured.isoformat(), "claim_at": claim.isoformat(),
            "equity": equity, "buying_power": equity * rnd.choice([0.05, 0.5, 1.0, 2.0]), "held": held, "risk": risk,
            "claim_held": sorted(set(held) | set(rnd.sample(names, rnd.randint(0, 2)))),
            "claim_pending": sorted(rnd.sample(names, rnd.randint(0, 2))), "asks": asks}


def port_decisions(case):
    ebars = {k: [{"t": parse_ts(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                 for b in v] for k, v in case["bars"].items()}
    return G.ThreeStrategySleeve.decisions(ebars)


def port(case, strategy, decisions):
    sid, _ = STRATS[strategy]
    s = G.ThreeStrategySleeve(sid, strategy)
    cap = parse_ts(case["captured_at"])
    triples = s.plan_run(decisions, case["equity"], case["buying_power"], case["risk"][strategy], set(case["held"]),
                         cap)
    handoffs = s.arm(triples, {}, cap)
    armed = copy.deepcopy(handoffs)
    claim = parse_ts(case["claim_at"])
    view = View(now=claim, session=datetime.fromtimestamp(claim, tz=timezone.utc).date().isoformat(),
                quotes={k: {"ask": a} for k, a in case["asks"].items()},
                extra={"pending_orders": [{"inst": "EQ:" + k, "side": "buy", "action": "enter", "vqty": 1.0,
                                           "filled_v": 0.0, "signal_key": "x-" + k} for k in case["claim_pending"]]})
    intents = s.deliver(view, handoffs, {}, set(case["claim_held"]), claim)
    return decisions, armed, handoffs, intents


def compare(case, src, strategy, decisions):
    diffs = []
    decisions, armed, after, intents = port(case, strategy, decisions)
    from dataclasses import asdict
    pd = {d.decisionId: asdict(d) for d in decisions}
    sd = {d["decisionId"]: d for d in src["decisions"]}
    if set(pd) != set(sd):
        diffs.append({"what": "decision ids", "port_only": sorted(set(pd) - set(sd))[:5],
                      "source_only": sorted(set(sd) - set(pd))[:5]})
    for k in set(pd) & set(sd):
        a, b = pd[k], sd[k]
        for f in ("status", "score", "engine", "setupClass", "entryReference", "invalidationReference",
                  "horizonSessions", "evidenceHash"):
            if a.get(f) != b.get(f):
                diffs.append({"what": "decision " + f, "id": k, "port": a.get(f), "source": b.get(f)})
        if list(a.get("reasonCodes") or []) != list(b.get("reasonCodes") or []):
            diffs.append({"what": "decision reasons", "id": k, "port": a.get("reasonCodes"),
                          "source": b.get("reasonCodes")})
    sa = {h["allocation_id"]: h for h in src["armed"]}
    if set(armed) != set(sa):
        diffs.append({"what": "armed handoffs", "port_only": sorted(set(armed) - set(sa)),
                      "source_only": sorted(set(sa) - set(armed))})
    for aid in set(armed) & set(sa):
        p, s = json.loads(json.dumps(armed[aid])), sa[aid]
        if p["plan"] != s["plan"]:
            diffs.append({"what": "plan", "id": aid, "port": p["plan"], "source": s["plan"]})
        if p["allocation"] != s["allocation"]:
            diffs.append({"what": "allocation", "id": aid, "port": p["allocation"], "source": s["allocation"]})
        if abs(p["expires_at"] - parse_ts(s["expires_at"])) > 1e-6 or p["created_at"] != s["created_at"]:
            diffs.append({"what": "handoff times", "id": aid})
    for aid, (state, reason) in src["states"].items():
        h = after.get(aid)
        if h is None or h["state"] != state or (state != "ARMED" and h["reason"] != reason):
            diffs.append({"what": "handoff state", "id": aid, "port": h and [h["state"], h["reason"]],
                          "source": [state, reason]})
    sent = {o["client_order_id"]: o for o in src["sent"]}
    mine = {i.signal_key: i for i in intents}
    if set(sent) != set(mine):
        diffs.append({"what": "orders", "port_only": sorted(set(mine) - set(sent)),
                      "source_only": sorted(set(sent) - set(mine))})
    for cid in set(sent) & set(mine):
        o, i = sent[cid], mine[cid]
        rules = {r.kind: r.value for r in i.exit_rules}
        got = {"symbol": i.symbol, "qty": float(i.qty), "type": "stop_limit" if i.order.stop_price else "limit",
               "limit": i.order.limit_price, "trigger": i.order.stop_price, "tif": i.order.tif,
               "tp": rules.get("target"), "sl": rules.get("stop")}
        want = {"symbol": o["symbol"], "qty": float(o["qty"]), "type": o["type"], "limit": float(o["limit_price"]),
                "trigger": float(o["stop_price"]) if o.get("stop_price") else None, "tif": o["time_in_force"],
                "tp": float(o["take_profit"]["limit_price"]) if o.get("take_profit") else None,
                "sl": float(o["stop_loss"]["stop_price"]) if o.get("stop_loss") else None}
        if got != want or o.get("order_class") != "bracket" or o.get("side") != "buy":
            diffs.append({"what": "order", "id": cid, "port": got, "source": want})
    return diffs


def main(argv):
    tree = os.environ.get("GRIFFITH_SRC")
    if not tree or not os.path.isdir(tree):
        raise SystemExit("set GRIFFITH_SRC to a scratch copy of agentic-trading-desk@4c8c179 (with config.json)")
    n = int(argv[0]) if argv else N_CASES
    stats = {k: {"armed": 0, "orders": 0, "superseded": 0, "expired": 0, "deferred": 0, "decisions": 0}
             for k in STRATS}
    diffs, done = [], 0
    from concurrent.futures import ThreadPoolExecutor
    batches = [list(range(lo, min(n, lo + 10))) for lo in range(0, n, 10)]
    # PARITY_PROGRESS=<file>: each finished batch's stats and diffs are appended there, and a rerun skips them
    progress = os.environ.get("PARITY_PROGRESS")
    finished = {}
    if progress and os.path.exists(progress):
        for line in open(progress):
            if line.strip():
                row = json.loads(line)
                finished[row["lo"]] = row
    for row in finished.values():
        diffs += row["diffs"]
        done += row["n"]
        for strategy, st in row["stats"].items():
            for k, v in st.items():
                stats[strategy][k] += v
    batches = [b for b in batches if b[0] not in finished]

    def source(batch):
        cases = [make_case(i) for i in batch]
        return batch, cases, run_source(SRC, {"cases": cases, "strategies": {k: v[1] for k, v in STRATS.items()}},
                                        tree, 3600, "griffith_parity_")

    with ThreadPoolExecutor(max_workers=3) as ex:
        for batch, cases, res in ex.map(source, batches):
            lo = batch[0]
            bstats = {k: dict.fromkeys(stats[k], 0) for k in STRATS}
            bdiffs = []
            for i, (case, r) in enumerate(zip(cases, res)):
                pdec = port_decisions(case)
                for strategy in STRATS:
                    src = r[strategy]
                    st = bstats[strategy]
                    st["decisions"] += len(src["decisions"])
                    st["armed"] += len(src["armed"])
                    st["orders"] += len(src["sent"])
                    for state, _ in src["states"].values():
                        k = {"SUPERSEDED": "superseded", "EXPIRED": "expired", "ARMED": "deferred"}.get(state)
                        if k:
                            st[k] += 1
                    for dd in compare(case, src, strategy, pdec):
                        bdiffs.append(dict(dd, case=lo + i, strategy=strategy))
            for strategy, st in bstats.items():
                for k, v in st.items():
                    stats[strategy][k] += v
            diffs += bdiffs
            if progress:
                with open(progress, "a") as f:
                    f.write(json.dumps({"lo": lo, "n": len(cases), "stats": bstats, "diffs": bdiffs}) + "\n")
            done += len(cases)
            print(f"{done}/{n} cases, diffs {len(diffs)}", flush=True)
    path_ = write_receipt("griffith", {
        "family": "griffith", "sleeves": [v[0] for v in STRATS.values()], "cases": n,
        "identical": n - len({d["case"] for d in diffs}), "n_diffs": len(diffs), "diffs": diffs[:50],
        "coverage": stats, "source": {"repo": "agentic-trading-desk", "commit": G.SOURCE["commit"],
                                      "run": "AgenticDesk.run_three_strategies + drain_strategy_handoffs"},
        "removed_in_both": ["RiskGate", "new_entry_admission", "desk allocator terms (total/symbol/sector/gross)",
                            "correlation multiplier", "position cap + Tensor reservation", "hands budget"]})
    print(json.dumps({"cases": n, "diffs": len(diffs), "coverage": stats, "receipt": path_}))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
