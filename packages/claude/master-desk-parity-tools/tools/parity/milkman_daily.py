"""milkman_daily: the study's own daily strategy functions vs the port's bar programs, rule by rule.

SOURCE side: quant-research-critical@0be4c575 milkman-study/v2/code (dstrats.py c1845e96, dlib.py 026fbc64, mlib.py
0e488ae7, blob-checked, copied to a temporary directory) imported in its own process from that directory (numba's @njit compiler decorator stood
in by tools/parity/stubs/numba.py when numba is absent). Each case calls the strategy function (double7, buyday,
weekday, bilbo_daily, gg_trade, ema21rev, po_signal, ribbon, comp_expansion, bigday, ftd) on a synthetic daily series
and keeps its closed trades, as 12_run_daily.py does (xi >= 0, finite ep / xp, ep > 0).
PORT side: desk/sleeves/milkman/rules.py replayed bar by bar (open, touch over the bar, close, end) on the same
series, with the study's indicators (vendored _cache / htf_levels).
Compared exactly, trade by trade: (entry bar, exit bar, entry price, exit price); comp_expansion's entry bar is its
signal bar, as the study records it.
Series: 600-900 business days, mixing calm stretches (compression episodes), trends, gaps and multi-day selloffs
(corrections, big down days). Kinds etf / fut / stock; stock volume and price sometimes fail the liquidity gate.
Cells: each lane's designated cell plus neighbouring grid cells from 12_run_daily.py; both sides.
Counted, not diffs:
  * gg_last_bar_entry: a Golden Gate entry on the period's last bar with no exit on that bar is a port trade closed
    at that bar's close (named divergence 7). The study's engine leaves it open and drops it;
  * ftd_data_end: the study closes a follow-through trade at the data's last bar when its 120-bar cap lies beyond
    the data. That is a data-end artifact; the port keeps it open;
  * nonoverlap_data_end: nonoverlap drops a trade whose exit lies beyond the data, so it no longer blocks later
    entries, and the study keeps trades that overlap it. The port's trade is still open and blocks them. These are
    counted only after the port's first trade that is still open at the data end."""
import inspect
import json
import os
import random
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import old_run, write_receipt

TREE = "/home/user/quant-research-critical/milkman-study/v2/code"
N_PER_RULE = int(os.environ.get("MILKMAN_CASES_PER_RULE", 1000))
CELLS = {
    "D7": [dict(N=7, ma=200), dict(N=5, ma=100), dict(N=10, ma=200)],
    "LBD": [dict(k=3, exact=True), dict(k=2, exact=False), dict(k=4, exact=True)],
    "DOW": [dict(dow=0), dict(dow=3)],
    "DBB": [dict(boxlen=5, exitm="ema50"), dict(boxlen=3, exitm="ema50"), dict(boxlen=8, exitm="ema50")],
    "GG": [dict(freq="M", entry_lvl=0.618, ema_gate="with", stop="pivot"),
           dict(freq="W", entry_lvl=0.382, tgt_lvl=0.618, stop="pivot", ema_gate="off", po_filter=True, min_left=1),
           dict(freq="M", entry_lvl=0.5, ema_gate="off", stop="trigger"),
           dict(freq="W", entry_lvl=0.382, tgt_lvl=1.0, stop="trigger", ema_gate="off", po_filter=False, min_left=1)],
    "E21": [dict(k=2.0, H=10), dict(k=4.0, H=10), dict(k=4.0, H=20), dict(k=3.5, H=28)],
    "PO": [dict(kind="accum", H=20), dict(kind="extreme", H=20), dict(kind="accum", H=10)],
    "RIB": [dict(exitm="opposite"), dict(exitm="h20"), dict(exitm="fast")],
    "CEX": [dict(minbars=10, H=5), dict(minbars=3, H=10), dict(minbars=5, H=20)],
    "BIG": [dict(thr=-2.0, H=10), dict(thr=-1.5, H=3)],
    "FTD": [dict(corr=10.0, gain=1.25), dict(corr=5.0, gain=1.0)],
}
FN = {"D7": "double7", "LBD": "buyday", "DOW": "weekday", "DBB": "bilbo_daily", "GG": "gg_trade", "E21": "ema21rev",
      "PO": "po_signal", "RIB": "ribbon", "CEX": "comp_expansion", "BIG": "bigday", "FTD": "ftd"}
INDEX_ONLY = {"DOW", "BIG", "FTD"}


def gen_series(seed, index_only):
    """a deterministic daily OHLCV series: (dates, o, h, l, c, v, kind)."""
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    n = int(rng.integers(600, 900))
    calm = rng.random(n // 20 + 1) < 0.45
    base = np.repeat(np.where(calm, rng.uniform(0.002, 0.006, len(calm)), rng.uniform(0.012, 0.03, len(calm))), 20)[:n]
    drift = np.repeat(rng.normal(0, 0.0025, n // 40 + 1), 40)[:n]
    r = rng.normal(drift, base)
    for k in rng.choice(n, int(rng.integers(3, 9)), replace=False):     # selloffs: corrections / big down days
        r[k:k + int(rng.integers(2, 12))] -= rng.uniform(0.008, 0.04)
    for k in rng.choice(n, int(rng.integers(2, 8)), replace=False):     # gaps
        r[k] += rng.choice((-1, 1)) * rng.uniform(0.02, 0.07)
    c = float(rng.uniform(2.0, 300.0)) * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]] * np.exp(rng.normal(0, base / 2))
    h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, base / 1.4)))
    l = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, base / 1.4)))
    if index_only:
        kind = "fut" if seed % 5 == 0 else "etf"
    else:
        kind = ("etf", "fut", "stock", "stock")[seed % 4]
    dv = 10 ** rng.uniform(5.8, 7.6)                                   # stock liquidity sometimes below $5M / day
    v = dv / c * np.exp(rng.normal(0, 0.5, n))
    dates = [str(x.date()) for x in pd.bdate_range("2014-01-02", periods=n)]
    return dates, o.tolist(), h.tolist(), l.tolist(), c.tolist(), v.tolist(), kind


OLD = r'''
import numpy as np
import dstrats as D
GEN
out = []
for case in PAYLOAD["cases"]:
    dates, o, h, l, c, v, kind = gen_series(case["seed"], case["index_only"])
    d = dict(date=np.array(dates, dtype="datetime64[ns]"), o=np.array(o), h=np.array(h), l=np.array(l),
             c=np.array(c), v=np.array(v), kind=kind)
    t = getattr(D, case["fn"])(d, side=case["side"], **case["cell"])
    ok = (t["xi"] >= 0) & np.isfinite(t["xp"]) & np.isfinite(t["ep"]) & (t["ep"] > 0)
    out.append([[int(a), int(b), float(p), float(q)] for a, b, p, q in zip(t["ent"][ok], t["xi"][ok], t["ep"][ok], t["xp"][ok])])
print(__import__("json").dumps(out))
'''.replace("GEN", inspect.getsource(gen_series))


def cases_for(rule):
    rnd = random.Random(hash(rule) % 1000 + 17)
    out = []
    cells = CELLS[rule]
    for k in range(N_PER_RULE):
        seed = 10_000 * (sorted(CELLS).index(rule) + 1) + k // 2
        out.append({"rule": rule, "fn": FN[rule], "seed": seed, "side": 1 if k % 2 == 0 else -1,
                    "cell": cells[(k // 2) % len(cells)], "index_only": rule in INDEX_ONLY})
    return out


def port_case(case):
    from desk.sleeves.milkman import rules as R
    from desk.sleeves.milkman import vendored as V
    dates, o, h, l, c, v, kind = gen_series(case["seed"], case["index_only"])
    X = R.Ctx(dates, o, h, l, c, v, kind)
    gg_last = V.dstrats().htf_levels(X.d, case["cell"]["freq"])[2] if case["rule"] == "GG" else None
    evs, S = R.replay(case["rule"], X, case["side"], case["cell"], gg_last)
    tr = []
    for a, b, p, q, tid, sig in R.trades(evs):
        tr.append([X.idx[sig or a], X.idx[b], p, q, X.idx[a], int(gg_last[X.idx[a]]) if gg_last is not None else None])
    still_open = sorted(X.idx[x.get("signal") or x["i"]] for x in S["open"])
    return {"trades": tr, "n": X.n, "open": still_open, "nonoverlap": R.RULES[case["rule"]].nonoverlap}


def _ports(batch):
    return [port_case(c) for c in batch]


def compare(case, old, port):
    """(diffs, counted) for one case."""
    counted = {"gg_last_bar_entry": 0, "ftd_data_end": 0, "nonoverlap_data_end": 0}
    n = port["n"]
    o = [tuple(x) for x in old]
    port_closed = {tuple(x[:4]) for x in port["trades"]}
    if case["rule"] == "FTD":
        keep = []
        for x in o:
            if x[1] == n - 1 and x[1] - x[0] < 120 and x not in port_closed and x[0] in port["open"]:
                counted["ftd_data_end"] += 1                  # the study's close at the data end; the port holds it
            else:
                keep.append(x)
        o = keep
    if port["nonoverlap"] and port["open"]:
        first_open = min(port["open"])                    # the study dropped this unclosed trade, so it never blocked
        keep = []                                         # the entries after it; the port's open trade does
        for x in o:
            if x[0] > first_open and x not in port_closed:
                counted["nonoverlap_data_end"] += 1
            else:
                keep.append(x)
        o = keep
    p = []
    for a, b, ep, xp, ent_bar, last in port["trades"]:
        if case["rule"] == "GG" and ent_bar == last and b == ent_bar and (a, b, ep, xp) not in set(o):
            counted["gg_last_bar_entry"] += 1
            continue
        p.append((a, b, ep, xp))
    so, sp = sorted(o), sorted(p)
    if so == sp:
        return [], counted, len(so)
    return [{"old_only": sorted(set(so) - set(sp))[:5], "port_only": sorted(set(sp) - set(so))[:5]}], counted, len(so)


def run():
    import hashlib
    tree = tempfile.mkdtemp(prefix="milkman_src_")          # a copy: nothing is written into the source repo
    for name, blob in (("dstrats.py", "c1845e96afc6e5b3c53244055f3a8497bf752d6c"),
                       ("dlib.py", "026fbc64f43f6e8dd7546fad107f6ffdf5430b53"),
                       ("mlib.py", "0e488ae7ad34c37197b7141afb3ba5d1483892f6")):
        b = open(os.path.join(TREE, name), "rb").read()
        assert hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == blob, f"{name} differs from the pinned blob"
        open(os.path.join(tree, name), "wb").write(b)
    diffs, stats = [], {}
    try:
        _run(tree, diffs, stats)
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    total = sum(s["cases"] for s in stats.values())
    identical = sum(s["identical"] for s in stats.values())
    return _finish(total, identical, diffs, stats)


def _run(tree, diffs, stats):
    with ProcessPoolExecutor(4) as ex:
        for rule in sorted(CELLS):
            cases = cases_for(rule)
            old = []
            for i in range(0, len(cases), 250):
                old += old_run(OLD, {"cases": cases[i:i + 250]}, timeout=7200, tree=tree)
            parts = list(ex.map(_ports, [cases[i::4] for i in range(4)]))
            port = [None] * len(cases)
            for i in range(4):
                for k, r in zip(range(i, len(cases), 4), parts[i]):
                    port[k] = r
            s = stats.setdefault(rule, {"cases": 0, "identical": 0, "trades": 0, "gg_last_bar_entry": 0,
                                        "ftd_data_end": 0, "nonoverlap_data_end": 0})
            for c, o, p in zip(cases, old, port):
                d, cnt, ntr = compare(c, o, p)
                s["cases"] += 1
                s["trades"] += ntr
                for k, v in cnt.items():
                    s[k] += v
                if d:
                    diffs.append({"rule": rule, "seed": c["seed"], "side": c["side"], "cell": c["cell"], "diff": d})
                else:
                    s["identical"] += 1


def _finish(total, identical, diffs, stats):
    from desk.sleeves.milkman.daily import sleeve_id
    ids = sorted({sleeve_id(r) for r in ("D7", "LBD", "DOW", "DBB", "SGG", "MDGG", "E21", "PO", "RIB", "CEX", "BIG",
                                         "FTD")})
    res = {"sleeve": "milkman_daily", "family": "milkman", "sleeves": ids, "cases": total, "identical": identical,
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "source": {"repo": "quant-research-critical", "commit": "0be4c57569e363d052bd23564cf0664697439927",
                      "tree": TREE, "files": {"dstrats.py": "c1845e96afc6e5b3c53244055f3a8497bf752d6c",
                                              "dlib.py": "026fbc64f43f6e8dd7546fad107f6ffdf5430b53",
                                              "mlib.py": "0e488ae7ad34c37197b7141afb3ba5d1483892f6"}},
           "method": "the study's strategy functions (own process, own directory) vs rules.py replayed bar by bar; "
                     "closed trades compared exactly (entry bar, exit bar, entry px, exit px)",
           "divergences": {"counted_not_diffs": ["gg_last_bar_entry (named divergence 7)",
                                                 "ftd_data_end (the study's data-end close of a trade the port holds)",
                                                 "nonoverlap_data_end (entries the study kept after dropping an "
                                                 "unclosed trade at the data end; the port's open trade blocks them)"],
                           "not_in_this_comparison": ["live execution prices and timing (daily.py divergences 1-3)",
                                                      "sizing (4)", "univ data source (5)", "futures venue (6)",
                                                      "downtime (8)"]}}
    write_receipt("milkman_daily", res)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["stats"])[:3000])
    for d in r["diffs"][:3]:
        print(json.dumps(d, default=str)[:2000])
