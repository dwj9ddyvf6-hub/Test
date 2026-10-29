"""griffith_factor (R4 parallel lab x5, tournament daily candidates x2): the SOURCE's own materializers
(agentic-trading-desk main @4c8c179c, run unmodified in a scratch copy of its tree: GRIFFITH_SRC) vs the port
(desk/sleeves/families/griffith_factor.py) on deterministic randomized panels.

Source: the panel is stored as SCOPE evidence (the real ScopePlane.store_evidence, raw Alpaca-shaped bars), then
r4_parallel_materializer.ParallelMaterializer.run() decides every SPY month end for the five monthly candidates and
r4_candidate_evidence.R4CandidateEvidence.run_bounded() observes every name at every completed bar for the two daily
candidates. Port: for each month the cutoff the port derives on the first session after it (month_end_cutoff) and
its selection (monthly_selection); for each name and bar the port's observation on that prefix (the same
evaluate_daily_candidate through the port's epoch -> ISO tape conversion). Compared: every monthly decision's cutoff
and selected list (order included), every daily observation's state.

    GRIFFITH_SRC=/path/to/scratch/agentic_src python3 -m tools.parity.griffith_factor [n_panels]"""
import json
import os
import random
import sys
from datetime import date, timedelta

from desk import calendar as cal
from desk.feedlib import griffith as tape
from desk.sleeves.families import griffith_factor as F
from desk.util import parse_ts

from . import write_receipt
from .griffith import path, run_source

N_PANELS = 200
SRC = r'''
import sys, json, tempfile, pathlib, sqlite3, shutil
sys.dont_write_bytecode = True
from scope_runtime import ScopePlane
from r4_parallel_materializer import ParallelMaterializer
from r4_candidate_evidence import R4CandidateEvidence
out = []
for case in PAYLOAD["cases"]:
    tdir = tempfile.mkdtemp(prefix="case_")                        # inside PAYLOAD["tmp"]
    tmp = pathlib.Path(tdir) / "desk.db"
    scope = ScopePlane(tmp, sorted(case["bars"]))
    for s, bl in case["bars"].items():
        scope.store_evidence(s, "1Day", bl)
    ParallelMaterializer(tmp).run()
    ev = R4CandidateEvidence(tmp)
    for _ in range(100):
        r = ev.run_bounded(source_limit=24)
        if r.get("unchangedSuppressed") or not r.get("pendingSources"):
            break
    db = sqlite3.connect(tmp)
    monthly = [[v, at, json.loads(sel), st] for v, at, sel, st in db.execute(
        "SELECT version_id,decision_at,selected_json,state FROM r4_parallel_decisions ORDER BY version_id,decision_at")]
    daily = [[v, s, c, st] for v, s, c, st in db.execute(
        "SELECT version_id,symbol,bar_cutoff,state FROM r4_candidate_observations ORDER BY version_id,symbol,bar_cutoff")]
    out.append({"monthly": monthly, "daily": daily})
    db.close()
    shutil.rmtree(tdir, ignore_errors=True)
print(json.dumps(out))
'''


def make_panel(i):
    rnd = random.Random(9100 + i)
    uni = tape.tape_symbols()
    etfs = [s for s in ("SPY", "QQQ", "IWM", "DIA", "GLD", "TLT", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV")
            if s in uni]
    names = sorted(set(rnd.sample(uni, rnd.randint(8, 24))) | set(rnd.sample(etfs, rnd.randint(4, len(etfs))))
                   | {"SPY"})
    n = rnd.randint(260, 420)
    start = (date(2023, 1, 2) + timedelta(days=rnd.randint(0, 400))).isoformat()
    bars = {}
    for k, s in enumerate(names):
        r = random.Random(i * 1000 + k)
        bl = path(r, n, start, leader=r.random() < 0.3)
        if r.random() < 0.15:                     # late listing / gaps: short or ragged histories
            bl = bl[r.randint(50, 200):]
        if r.random() < 0.05:
            bl = bl[:-r.randint(1, 3)]            # a name whose evidence stops early
        if r.random() < 0.05:
            bl[r.randint(0, len(bl) - 1)]["v"] = 0.0
        bars[s] = bl
    return {"bars": bars}


def port_monthly(case):
    """the port's decision for every month the panel's SPY tape completes (cutoff, selected)."""
    ebars = {s: [dict(b, t=parse_ts(b["t"])) for b in bl] for s, bl in case["bars"].items()}
    rows = {s: tape.raw_rows(bl) for s, bl in ebars.items()}
    spy_months = sorted({r["t"][:7] for r in rows["SPY"]})
    out = {}
    for m in spy_months:
        y, mo = int(m[:4]), int(m[5:7])
        nxt = date(y + (mo == 12), mo % 12 + 1, 1)
        while not cal.is_trading_day(nxt):
            nxt += timedelta(days=1)
        cutoff = F.month_end_cutoff(rows["SPY"], nxt.isoformat())
        for sid, version in F.MONTHLY.items():
            sel, status = F.monthly_selection(version, rows, cutoff)
            out[(version, cutoff)] = (sel, status)
    return out


def port_daily(case):
    ebars = {s: [dict(b, t=parse_ts(b["t"])) for b in bl] for s, bl in case["bars"].items()}
    out = {}
    for sid, version in F.DAILY.items():
        sl = F.R4DailyCandidate(sid, version)
        V = F.vendored()
        for s, bl in ebars.items():
            rows = tape.raw_rows(bl)
            for idx in range(252, len(rows)):
                r = V.strategy_tournament.evaluate_daily_candidate(version, rows[:idx + 1])
                out[(version, s, rows[idx]["t"])] = r["status"]
        # the sleeve's own per-session observation equals the source state on the last bar
        last = sl.observe(ebars)
        for s in last:
            out[("SETUP_SET", version, s)] = True
    return out


def main(argv):
    tree = os.environ.get("GRIFFITH_SRC")
    if not tree or not os.path.isdir(tree):
        raise SystemExit("set GRIFFITH_SRC to a scratch copy of agentic-trading-desk@4c8c179")
    n = int(argv[0]) if argv else N_PANELS
    diffs, monthly_n, daily_n, setups = [], 0, 0, {"monthly_selected": 0, "daily_setup": 0}
    for lo in range(0, n, 20):
        cases = [make_panel(i) for i in range(lo, min(n, lo + 20))]
        res = run_source(SRC, {"cases": cases}, tree, 7200, "griffith_factor_parity_")
        for i, (case, r) in enumerate(zip(cases, res)):
            pm = port_monthly(case)
            for version, at, sel, state in r["monthly"]:
                monthly_n += 1
                setups["monthly_selected"] += bool(sel)
                got = pm.get((version, at))
                if got is None or got[0] != sel:
                    diffs.append({"case": lo + i, "what": "monthly", "version": version, "cutoff": at,
                                  "source": sel, "port": got and got[0]})
            src_cut = {(v, at) for v, at, _, _ in r["monthly"]}
            for k in set(pm) - src_cut:
                if k[1] is not None and pm[k][0]:
                    diffs.append({"case": lo + i, "what": "monthly port-only", "key": list(k)})
            pdl = port_daily(case)
            last_src = {}
            for version, s, cutoff, state in r["daily"]:
                daily_n += 1
                setups["daily_setup"] += state == "SETUP"
                if pdl.get((version, s, cutoff)) != state:
                    diffs.append({"case": lo + i, "what": "daily", "version": version, "symbol": s,
                                  "cutoff": cutoff, "source": state, "port": pdl.get((version, s, cutoff))})
                if cutoff >= last_src.get((version, s), ("", ""))[0]:
                    last_src[(version, s)] = (cutoff, state)
            for (version, s), (cutoff, state) in last_src.items():
                if (state == "SETUP") != bool(pdl.get(("SETUP_SET", version, s))):
                    diffs.append({"case": lo + i, "what": "daily sleeve observation", "version": version,
                                  "symbol": s, "source": state})
        print(f"{min(n, lo + 20)}/{n} panels, monthly {monthly_n}, daily {daily_n}, diffs {len(diffs)}", flush=True)
    path_ = write_receipt("griffith_factor", {
        "family": "griffith_factor", "sleeves": list(F.MONTHLY) + list(F.DAILY), "cases": monthly_n + daily_n,
        "panels": n, "monthly_decisions": monthly_n, "daily_observations": daily_n,
        "identical": monthly_n + daily_n - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:50], "coverage": setups,
        "source": {"repo": "agentic-trading-desk", "commit": F.SOURCE["commit"],
                   "run": "ParallelMaterializer.run + R4CandidateEvidence.run_bounded"}})
    print(json.dumps({"panels": n, "monthly": monthly_n, "daily": daily_n, "diffs": len(diffs), "receipt": path_}))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
