"""lazarus_vmr: the ChartsLector producer as Lazarus ran it (Author-research shadow/paper_sleeve/chartslector/
cl_live_fires.py + cl_core.py, quant-research-critical @0be4c575, run from the SOURCE tree in its own process) vs
the port's feed (desk.sleeves.families.lazarus.run_cl: the vendored copy over the engine store the desk writes from
its QQQ daily bars), on the same market data.

Each case: a desk-calendar day axis of 440-560 sessions ending at a random session in 2023-2026; an engine store of
QQQ plus 0-3 other names (the source reads the whole store: its day axis = the sessions most names printed); four
Cboe histories (VIX, VIX3M, VVIX, SKEW) built from calm / fear regimes so the VIX Mood Ring composite crosses 35 in
episodes of 1-12 sessions (cooldown chains), with Cboe dates dropped (the producer's ffill(limit=3)) and Cboe ending
before / with / after the store (its fail-closed rule); `--today` 0-6 days after the last session (store > 4 days
stale -> no fires). The source reads the full store; the port writes QQQ's rows only.

Compared: every VMR / QM fire record (key, symbol, lane, fire bar, close, plan, tags ...) and the producer's stale
flag. Named divergence counted, not failed: in "gap" cases (QQQ misses a session most names printed, or prints one
most names missed — never seen on the real tape) the source's day axis differs from QQQ's own sessions; every such
case is classified and its diffs are reported under day_axis.

    CL_SRC=<Author-research/shadow/paper_sleeve/chartslector dir> python3 -m tools.parity.run lazarus_vmr"""
import hashlib
import json
import math
import os
import random
import shutil
import tempfile
from datetime import date, datetime, timedelta

from desk import calendar as cal
from desk.sleeves.families import lazarus as L
from desk.util import ET

from . import old_run, write_receipt

N_CASES = 1200
BATCH = 100
PINS = {"cl_live_fires.py": "dec0c0637680a23f1d23a058c35a5c9623c99e67",
        "cl_core.py": "d265d5609503b3d9ecf389b134050d9e77d94ae8"}
DEFAULT_SRC = "/home/user/quant-research-critical/Author-research/shadow/paper_sleeve/chartslector"

OLD = r'''
import contextlib, io, json, math
import cl_live_fires as M
out = []
for c in PAYLOAD["cases"]:
    with contextlib.redirect_stdout(io.StringIO()):
        M.main(["--eng", c["eng"], "--out", c["out"], "--cboe-dir", c["cboe"], "--no-net", "--no-sec",
                "--today", c["today"]])
    J = json.load(open(c["out"]))
    out.append({"fires": J["fires"], "stale": J["freshness"]["stale"], "last": J["freshness"]["engine_last_session"]})
print(json.dumps(out))
'''


def _src():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"          # never write __pycache__ into the source tree
    d = os.environ.get("CL_SRC") or DEFAULT_SRC
    for fn, want in PINS.items():
        b = open(os.path.join(d, fn), "rb").read()
        got = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
        if got != want:
            raise SystemExit(f"{fn} in {d} is blob {got[:12]}, not the pinned {want[:12]}")
    return d


def sessions(end, n):
    out, d = [], end
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def bar_epoch(d):
    return int(datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET).timestamp())


def walk(rnd, days, px):
    rows = []
    for d in days:
        o = px * (1 + rnd.gauss(0, 0.006))
        c = max(1.0, px * (1 + rnd.gauss(0.0004, 0.012)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.004)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, 0.004)))
        rows.append({"t": bar_epoch(d), "o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2),
                     "v": float(rnd.randrange(20_000_000, 90_000_000))})
        px = c
    return rows


def cboe_series(rnd, days, last_idx_bias):
    """per-day (VIX, VIX3M, VVIX, SKEW) from calm / fear regimes; fear episodes push the composite under 35."""
    n = len(days)
    fear = [False] * n
    for _ in range(rnd.randint(1, 5)):
        ln = rnd.randint(1, 12)
        st = rnd.randint(max(0, n - 14), n - 1) if rnd.random() < last_idx_bias else rnd.randint(0, n - 1)
        for i in range(st, min(n, st + ln)):
            fear[i] = True
    out = []
    for i in range(n):
        if fear[i]:
            vix = rnd.uniform(24, 48)
            r = rnd.uniform(0.9, 1.12)
            vvix = rnd.uniform(105, 170)
        else:
            vix = rnd.uniform(11, 24)
            r = rnd.uniform(0.78, 0.98)
            vvix = rnd.uniform(75, 120)
        skew = rnd.uniform(112, 160)
        out.append((round(vix, 2), round(vix / r, 2), round(vvix, 2), round(skew, 2)))
    return out


def write_cboe(d, days, vals, rnd):
    os.makedirs(d, exist_ok=True)
    keep = list(range(len(days)))
    if rnd.random() < 0.3:                                    # Cboe dates missing (1-4 in a row): ffill(limit=3)
        for _ in range(rnd.randint(1, 3)):
            i = rnd.randrange(len(days))
            for j in range(i, min(len(days), i + rnd.randint(1, 4))):
                if j in keep and j != len(days) - 1:
                    keep.remove(j)
    end = len(days)
    u = rnd.random()
    if u < 0.12:
        end = len(days) - rnd.randint(1, 2)                   # Cboe behind the store: fail closed
    extra = []
    if u > 0.9:                                                # Cboe one session ahead of the store
        nx = days[-1] + timedelta(days=1)
        while not cal.is_trading_day(nx):
            nx += timedelta(days=1)
        extra = [(nx, vals[-1])]
    rows = [(days[i], vals[i]) for i in keep if i < end] + extra
    files = {"VIX_History.csv": ("DATE,OPEN,HIGH,LOW,CLOSE", lambda v: "%s,%s,%s,%s" % (v[0], v[0], v[0], v[0])),
             "VIX3M_History.csv": ("DATE,OPEN,HIGH,LOW,CLOSE", lambda v: "%s,%s,%s,%s" % (v[1], v[1], v[1], v[1])),
             "VVIX_History.csv": ("DATE,VVIX", lambda v: "%s" % v[2]),
             "SKEW_History.csv": ("DATE,SKEW", lambda v: "%s" % v[3])}
    for fn, (hdr, fmt) in files.items():
        with open(os.path.join(d, fn), "w") as f:
            f.write(hdr + "\n" + "\n".join("%s,%s" % (x.strftime("%m/%d/%Y"), fmt(v)) for x, v in rows) + "\n")


def make_case(seed, root):
    rnd = random.Random(seed)
    end = date(2023, 1, 3) + timedelta(days=rnd.randrange(0, 1380))
    while not cal.is_trading_day(end):
        end -= timedelta(days=1)
    days = sessions(end, rnd.randint(440, 560))
    k = rnd.choice((0, 1, 1, 2, 3))
    kind = "full"
    qqq_days, other_days = list(days), list(days)
    if k >= 1 and rnd.random() < 0.1:
        kind = "gap"
        i = rnd.randrange(len(days) - 30, len(days))
        if rnd.random() < 0.5:
            qqq_days = days[:i] + days[i + 1:]                     # QQQ misses a session the others printed
        elif k >= 2:
            other_days = days[:i] + days[i + 1:]                   # QQQ prints a session most names missed
    eng = os.path.join(root, "eng")
    qqq = walk(rnd, qqq_days, rnd.uniform(250, 650))
    L.write_store(eng, "QQQ", qqq)
    for j in range(k):
        L.write_store(eng, "N%03d" % j, walk(rnd, other_days, rnd.uniform(5, 300)))
    write_cboe(os.path.join(root, "cboe"), days, cboe_series(rnd, days, 0.6), rnd)
    today = days[-1] + timedelta(days=rnd.choice((0, 0, 1, 1, 2, 3, 5, 6)))
    return {"eng": eng, "cboe": os.path.join(root, "cboe"), "out": os.path.join(root, "src_out.json"),
            "today": today.isoformat(), "qqq": qqq, "kind": kind, "work": os.path.join(root, "port")}


def _same(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def run(n=N_CASES):
    src = _src()
    stats = {"cases": 0, "fires_src": 0, "fires_port": 0, "vmr_fires": 0, "stale_cases": 0, "gap_cases": 0,
             "gap_cases_differing": 0, "cases_with_fire": 0}
    diffs, day_axis = [], []
    identical = 0
    tmp = tempfile.mkdtemp(prefix="lz_vmr_")
    try:
        for b0 in range(0, n, BATCH):
            cases = []
            for i in range(b0, min(n, b0 + BATCH)):
                root = os.path.join(tmp, "c%05d" % i)
                cases.append(dict(make_case(7000 + i, root), i=i))
            res = old_run(OLD, {"cases": [{k: c[k] for k in ("eng", "cboe", "out", "today")} for c in cases]},
                          tree=src)
            for c, r in zip(cases, res):
                J = L.run_cl(c["work"], c["qqq"], c["cboe"], c["today"])
                port = {"fires": J["fires"], "stale": J["freshness"]["stale"]}
                stats["cases"] += 1
                stats["fires_src"] += len(r["fires"])
                stats["fires_port"] += len(port["fires"])
                stats["vmr_fires"] += sum(1 for f in r["fires"] if f["lane"] == "s_cl_vmr_qqq")
                stats["stale_cases"] += 1 if r["stale"] else 0
                stats["cases_with_fire"] += 1 if r["fires"] else 0
                ok = _same(r["fires"], port["fires"]) and r["stale"] == port["stale"]
                if c["kind"] == "gap":
                    stats["gap_cases"] += 1
                    if not ok:                         # named divergence: the day axis (explained, not failed)
                        stats["gap_cases_differing"] += 1
                        day_axis.append({"case": c["i"], "src": {"fires": [f["key"] for f in r["fires"]],
                                                                 "stale": r["stale"], "last": r["last"]},
                                         "port": {"fires": [f["key"] for f in port["fires"]],
                                                  "stale": port["stale"],
                                                  "last": J["freshness"]["engine_last_session"]}})
                        continue
                if ok:
                    identical += 1
                else:
                    diffs.append({"case": c["i"], "today": c["today"], "src": r, "port": port})
            shutil.rmtree(tmp)
            os.makedirs(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    payload = {"cases": stats["cases"], "identical": identical, "diffs": diffs[:50], "n_diffs": len(diffs),
               "explained": {"day_axis": stats["gap_cases_differing"]},
               "stats": stats, "named_divergence_day_axis": {"cases": stats["gap_cases"],
                                                              "differing": stats["gap_cases_differing"],
                                                              "examples": day_axis[:10]},
               "sleeves": ["lz_cl_vmr_qqq", "lz_cl_qm_small"], "family": "chartslector",
               "method": "source cl_live_fires.main (CL_SRC tree, own process; --no-net --no-sec) on the full engine "
                         "store vs the port's run_cl (vendored copy, QQQ-only store written from desk bars); "
                         "same Cboe CSVs and --today", "source": dict(L.CL_SOURCE, src_dir=src)}
    write_receipt("lazarus_vmr", payload)
    return dict(payload, sleeve="lazarus_vmr")
