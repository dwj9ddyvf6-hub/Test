"""dcg frame: the old daily_cyan_gbm_sleeve / rule_sleeve_base scoring frame (prepare_bars trim, build_market from
the CBOE CSV, the dcg_xsect cache aligned by date, fomc_indices from macro_events.json) vs desk/feedlib/dcg.frame,
and the vendored Node scorers on both payloads.

A synthetic genome (150 names incl. the ten market ETFs, histories from 30 to 450 sessions, a VIX series with
gaps) per case. The OLD frame is built in its own process: the VIX CSV and the xsect cache are written the way
the old desk had them (the cache = dcg_xsect.compute_xsect over every cached name and day). The port runs
with the calendar extension off and the old FOMC list — then the payloads must be identical and so must
every name's signal-bar GBM score and rule features. Reported, not compared: how many signal-bar GBM scores
the named calendar divergence (turn-of-month / pre-FOMC at the signal bar) moves."""
import json
import os
import random
import tempfile

from desk.feedlib import dcg

from . import old_run, trading_dates, write_receipt

N_CASES = 6

OLD = r'''
import os, sys, tempfile, importlib.util
sys.argv = ["x"]
import daily_cyan_gbm_sleeve as D
import rule_sleeve_base as B
spec = importlib.util.spec_from_file_location("x_dcg", os.path.join(os.getcwd(), "dcg_scorer", "dcg_xsect.py"))
X = importlib.util.module_from_spec(spec)
spec.loader.exec_module(X)
out = []
for c in PAYLOAD["cases"]:
    tmp = tempfile.mkdtemp()
    csv = os.path.join(tmp, "vix.csv")
    with open(csv, "w") as fh:
        fh.write("date,close\n" + "".join("%s,%s\n" % (d, v) for d, v in sorted(c["vix"].items())))
    D.VIX_CSV = B.VIX_CSV = csv
    bars = {s: [list(r) for r in rows] for s, rows in c["bars"].items()}
    today = c["today"]
    days_all = sorted({b[0] for bl in bars.values() for b in bl})
    xc = os.path.join(tmp, "xsect.json")
    with open(xc, "w") as fh:
        json.dump({"days": days_all, "xsect": X.nan_to_null(X.compute_xsect(bars, days_all))}, fh)
    D.XSECT_CACHE = B.XSECT_CACHE = xc
    os.makedirs(os.path.join(tmp, "desk"), exist_ok=True)       # the old desk's desk/macro_events.json (in git;
    with open(os.path.join(tmp, "desk", "macro_events.json"), "w") as fh:   # absent from the partial checkout)
        fh.write(PAYLOAD["macro_events"])
    B.HERE = tmp
    b2 = {s: [b for b in bl if b[0] <= today] for s, bl in bars.items()}
    b2 = {s: bl for s, bl in b2.items() if len(bl) >= 60}
    days = sorted({b[0] for bl in b2.values() for b in bl})
    days = [d for d in days if d <= today]
    market = D.build_market(days, b2)
    xs = B.prepare_xsect(days)["xsect"]
    fomc = B.fomc_indices(days)
    out.append({"days": days, "market": market, "xsect": xs, "fomc": fomc})
print(json.dumps(out))
'''


def _walk(rnd, days, px, drift, vol):
    out = []
    for d in days:
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + rnd.gauss(drift, vol)))
        out.append([d, round(o, 4), round(max(o, c) * 1.01, 4), round(min(o, c) * 0.99, 4), round(c, 4),
                    float(int(rnd.uniform(1e5, 5e6)))])
        px = c
    return out


def _case(rnd, k):
    days = trading_dates("2024-11-04", 450)
    today = days[-1 - rnd.randint(0, 3)]
    bars = {e: _walk(rnd, days, rnd.uniform(20, 500), 0.0004, 0.012) for e in dcg.MARKET_ETFS}
    for j in range(140):
        n = rnd.choice((450, 450, 450, 300, 120, 59, 50, 30))
        bars["G%03d" % j] = _walk(rnd, days[-n:], rnd.uniform(3, 300), rnd.uniform(-0.002, 0.003), rnd.uniform(0.01, 0.05))
    vix = {d: round(rnd.uniform(12, 35), 2) for d in days if rnd.random() > 0.03 and d <= today}
    return {"bars": bars, "today": today, "vix": vix}


def run():
    rnd = random.Random(21)
    cases = [_case(rnd, k) for k in range(N_CASES)]
    macro = open(os.path.join(dcg.VENDOR, "macro_events.json")).read()
    old = old_run(OLD, {"cases": cases, "macro_events": macro}, timeout=3000)
    old_fomc = [e["date"] for e in json.load(open(os.path.join(dcg.VENDOR, "macro_events.json")))["events"]
                if "FOMC" in e.get("name", "").upper()]
    n = same = 0
    diffs = []
    counts = {"scored_names": 0, "gbm_last_bar_fires": 0, "rule_last_bar_fires": 0, "calendar_moved_scores": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": str(a)[:300], "new": str(b)[:300]})

    for ci, (c, o) in enumerate(zip(cases, old)):
        base, syms, bars = dcg.frame(c["bars"], c["vix"], c["today"], ahead_n=0, fomc=old_fomc)
        cmp("days", ci, o["days"], base["days"])
        cmp("market", ci, json.loads(json.dumps(o["market"])), json.loads(json.dumps(base["market"])))
        cmp("xsect", ci, json.loads(json.dumps(o["xsect"])), json.loads(json.dumps(base["xsect"])))
        cmp("fomc", ci, o["fomc"], base["fomcIdx"])
        obase = {"modelPath": dcg.MODEL, "days": o["days"], "market": o["market"], "xsect": o["xsect"],
                 "fomcIdx": o["fomc"]}
        g_old, _ = dcg.score(dcg.SCORER, obase, syms)
        g_new, _ = dcg.score(dcg.SCORER, base, syms)
        lo, ln = dcg.last_bar_fires(g_old, bars), dcg.last_bar_fires(g_new, bars)
        cmp("gbm_signal_bar", ci, lo, ln)
        r_old, _ = dcg.score(dcg.RULE_SCORER, dict(obase, lane="1D", signal="cyan"), syms)
        r_new, _ = dcg.score(dcg.RULE_SCORER, dict(base, lane="1D", signal="cyan"), syms)
        cmp("rule_signal_bar", ci, dcg.last_bar_fires(r_old, bars), dcg.last_bar_fires(r_new, bars))
        counts["scored_names"] += len(syms)
        counts["gbm_last_bar_fires"] += len(lo)
        counts["rule_last_bar_fires"] += len(dcg.last_bar_fires(r_old, bars))
        ext, syms2, _ = dcg.frame(c["bars"], c["vix"], c["today"])
        g_ext, _ = dcg.score(dcg.SCORER, ext, syms2)
        le = dcg.last_bar_fires(g_ext, bars)
        counts["calendar_moved_scores"] += sum(1 for s in le if s in lo and le[s]["score"] != lo[s]["score"])
    res = {"sleeve": "dcg_frame", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("dcg_frame", res)
    return res
