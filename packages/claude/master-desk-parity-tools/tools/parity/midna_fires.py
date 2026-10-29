"""midna_hourly_1d / midna_hourly_1w fires: the vendored sleeve_midna.hourly_fires (quant-research-backup ce5ccbcd,
blob 49c0524b, unmodified; its SHADOW_DIR pointed at the case's scratch research root) vs
desk/feedlib/midna_fires.hourly_fires on the same synthetic tracker files.

Per case: a latest_fires_v3.json with 1h / 1d / 1w rows (random tradeable flags, active units, bar sources, entry
refs, priorities, stops, max bars) and a ledger.jsonl holding fire records for some keys (tradeable / bar_source
overrides, cal_plans per unit, meta decile / score, sometimes non-numeric), other record types and malformed lines.
The source's 1D / 1W fires (its 1h lane is midna_hourly_playbook's) are compared with the port's in order, on every
field the port emits (the alt-data tag columns, all None for Midna fires, are the port's named omission).

Then the box's own tracker state once (real_snapshot): shadow/live/latest_fires_v3.json and shadow/log/ledger.jsonl as
committed to quant-research-backup main ce5ccbcd (Author-research/), read by exact blob sha from the blob directory
(MIDNA_FIRES_BLOBS, default /home/user/blobs, which holds the repository's blobs by sha), each blob re-hashed and the
ledger's three split parts joined and checked against the whole-file sha256 of the backup's parts manifest; the same
comparison. The box's last run (2026-10-14) left no tradeable 1D / 1W fire, so the tracker's earlier full runs are
replayed too: each run's rows of shadow/live/fires_log_v3.csv (the tracker's append-only log of every run's
latest_fires rows, same commit, by blob sha) typed back into a latest_fires_v3.json, against the same ledger - every
run with a tradeable 1D / 1W row.

midna_w_cyan_breadth (forward_part): the vendored sleeve_midna.forward_fires on a state.json whose forward accounts
stage random rows (missing / empty symbols and signal days, flags, scores, signal days on both sides of the DST
changes; the other five accounts stage rows too) vs midna_fires.forward_fires on the same w-cyan-breadth rows (the
desk's account midna_w_cyan_quiet_tape stages them). The source's FEEDS / LIVE point at the case's scratch dir (no
halt file; holdSessions 126, the account's spec) and its tracker engine dir is absent, so the fire close is its
"signal file" branch - the port's (the lane fills the close from the desk's bars, a named divergence). Compared
exactly: the lane's fires in order, every field the port emits; the plan is the source's with exactly the removed
gate taken out (stop 40 -> 99 and the scheme's " / 40% adverse circuit")."""
from datetime import date, timedelta
import csv
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
from pathlib import Path

from desk.feedlib import midna_fires as F

from . import write_receipt

N_CASES = 1500
BLOBS = os.environ.get("MIDNA_FIRES_BLOBS", "/home/user/blobs")
SNAPSHOT = {"repo": "quant-research-backup", "commit": "ce5ccbcd3634f79358eb096b6e43271989bb27d0",
            "latest": ("Author-research/shadow/live/latest_fires_v3.json", "fd111d43693d1c13c091fa797e78b7ccd2ba795c"),
            "ledger_parts": [("Author-research/shadow/log/ledger.jsonl.part000", "5d08ec60bc49f41fde35077f4d445d563f5ae392"),
                             ("Author-research/shadow/log/ledger.jsonl.part001", "c37c2b693b4d022bc1b985d3bafeb702378cf2a8"),
                             ("Author-research/shadow/log/ledger.jsonl.part002", "db3b45be42244273716e2fd0f29282ff815c3cbe")],
            "ledger_sha256": "71e476883099979771e7d95c86f2c13c21f4aa2de5c623c4f45399e2a6558bfa",
            "fires_log": ("Author-research/shadow/live/fires_log_v3.csv", "2382b9aab631550b76ac99a59b84939064a7f524")}


def _num(v):
    """a CSV number back as the JSON number it was written from (60 -> int, 60.0 -> float, empty -> None)."""
    if v in ("", None):
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def log_runs(path):
    """fires_log_v3.csv -> {run (detected_at_et): [latest_fires_v3 rows]}."""
    runs = {}
    with open(path, newline="") as f:
        for x in csv.DictReader(f):
            runs.setdefault(x["detected_at_et"], []).append(
                {"symbol": x["symbol"], "time_et": x["time_et"], "lane": x["lane"], "bar_source": x["bar_source"] or None,
                 "key": x["key"], "tradeable": {"True": True, "False": False}.get(x["tradeable"]),
                 "priority": _num(x["priority"]), "active_units": x["active_units"], "entry_ref": _num(x["entry_ref"]),
                 "stop_pct": _num(x["stop_pct"]), "max_hold_bars": _num(x["max_hold_bars"])})
    return runs


def _blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def compare(src, mine):
    """the source's 1D / 1W fires vs the port's: the keys in order, then every field the port emits."""
    if [x["key"] for x in src] != [x["key"] for x in mine]:
        return [{"keys_source": [x["key"] for x in src], "keys_port": [x["key"] for x in mine]}]
    bad = []
    for a, b in zip(src, mine):
        for k, v in b.items():
            if a.get(k) != v:
                bad.append({"key": b["key"], "field": k, "source": a.get(k), "port": v})
    return bad


FWD_IDS = ["gbm-1d-cyan", "w-cyan-breadth", "w-cyan-vix", "d-green-band", "w-green-smh", "w-cyan-adx"]


def forward_case(rnd):
    accounts = {}
    for mid in FWD_IDS:
        staged = []
        for _ in range(rnd.randint(0, 7)):
            day = (date(2025, 1, 1) + timedelta(days=rnd.randint(0, 700))).isoformat()
            row = {"sym": rnd.choice(SYMS + ["", None]), "signalDay": rnd.choice([day, day, day, "", None]),
                   "flag": rnd.choice([None, "cyan", "buy-cyan"]), "score": rnd.choice([None, 0.5, 3, -1.25])}
            if rnd.random() < 0.1:
                row.pop("sym")
            if rnd.random() < 0.1:
                row.pop("signalDay")
            staged.append(row)
        accounts[mid] = {"holdSessions": 126 if mid == "w-cyan-breadth" else rnd.choice([0, 21, 26, 52]),
                         "staged": staged}
    return {"forward": {"accounts": accounts}}


def forward_part(n, rnd):
    """midna_w_cyan_breadth's fires: the vendored forward_fires vs the port's (see the module docstring)."""
    import desk.vendor.midna.sleeve_midna as SM
    root = tempfile.mkdtemp(prefix="midna_fwd_fires_")
    saved = (SM.FEEDS, SM.LIVE, SM.ENGINE_1D)
    diffs, stats = [], {"fires": 0, "staged_rows": 0}
    try:
        SM.FEEDS, SM.LIVE, SM.ENGINE_1D = Path(root) / "feeds", Path(root) / "live", Path(root) / "engine" / "1d"
        os.makedirs(SM.FEEDS)
        for case in range(n):
            doc = forward_case(rnd)
            with open(SM.FEEDS / "state.json", "w") as f:
                json.dump(doc, f)
            src = [x for x in SM.forward_fires() if x["lane"] == "s_mn_w_cyan_breadth"]
            for x in src:
                pl = x["cal_plans"][x["cal_units"][0]]
                assert pl["stop_pct"] == SM.FORWARD_RUIN_PCT and pl["scheme"].endswith(" / 40% adverse circuit")
                pl["stop_pct"], pl["scheme"] = 99.0, pl["scheme"][:-len(" / 40% adverse circuit")]   # the removed gate
            staged = doc["forward"]["accounts"]["w-cyan-breadth"]["staged"]
            mine = F.forward_fires(lambda sid: {"staged": staged} if sid == "midna_w_cyan_quiet_tape" else None)
            bad = compare(src, mine)
            stats["fires"] += len(src)
            stats["staged_rows"] += len(staged)
            if bad:
                diffs.append({"case": case, "bad": bad[:4]})
    finally:
        SM.FEEDS, SM.LIVE, SM.ENGINE_1D = saved
        shutil.rmtree(root, ignore_errors=True)
    return diffs, stats


def real_snapshot():
    """the box's last tracker state through both sides (None when the blobs are not on this host)."""
    import desk.vendor.midna.sleeve_midna as SM
    want = [SNAPSHOT["latest"]] + SNAPSHOT["ledger_parts"]
    paths = [os.path.join(BLOBS, sha) for _, sha in want]
    if not all(os.path.exists(p) for p in paths):
        return None
    root = tempfile.mkdtemp(prefix="midna_fires_real_")
    saved = SM.SHADOW_DIR
    try:
        shadow = os.path.join(root, "shadow")
        os.makedirs(os.path.join(shadow, "live"))
        os.makedirs(os.path.join(shadow, "log"))
        latest = open(paths[0], "rb").read()
        if _blob_sha(latest) != SNAPSHOT["latest"][1]:
            raise SystemExit("latest_fires_v3.json blob mismatch")
        with open(os.path.join(shadow, "live", "latest_fires_v3.json"), "wb") as f:
            f.write(latest)
        h = hashlib.sha256()
        with open(os.path.join(shadow, "log", "ledger.jsonl"), "wb") as out:
            for (rel, sha), p in zip(SNAPSHOT["ledger_parts"], paths[1:]):
                b = open(p, "rb").read()
                if _blob_sha(b) != sha:
                    raise SystemExit(f"{rel} blob mismatch")
                h.update(b)
                out.write(b)
                del b
        if h.hexdigest() != SNAPSHOT["ledger_sha256"]:
            raise SystemExit("ledger.jsonl sha256 mismatch")
        SM.SHADOW_DIR = Path(shadow)
        src = [x for x in SM.hourly_fires() if x.get("midna_tf") in ("1d", "1w")]
        mine = F.hourly_fires(shadow)
        bad = compare(src, mine)
        rows = json.loads(latest).get("fires") or []
        days = sorted(str(r.get("time_et"))[:10] for r in rows if r.get("lane") in ("1d", "1w"))
        out = {"repo": SNAPSHOT["repo"], "commit": SNAPSHOT["commit"], "latest_blob": SNAPSHOT["latest"][1],
               "ledger_sha256": SNAPSHOT["ledger_sha256"],
               "rows": {ln: sum(1 for r in rows if r.get("lane") == ln) for ln in ("1h", "1d", "1w")},
               "fires": {ln: sum(1 for x in src if x["midna_tf"] == ln) for ln in ("1d", "1w")},
               "fire_days": [days[0], days[-1]] if days else None,
               "identical": not bad, "diffs": bad[:4]}
        lp = os.path.join(BLOBS, SNAPSHOT["fires_log"][1])
        if os.path.exists(lp):
            if _blob_sha(open(lp, "rb").read()) != SNAPSHOT["fires_log"][1]:
                raise SystemExit("fires_log_v3.csv blob mismatch")
            runs = log_runs(lp)
            pick = sorted(k for k, v in runs.items()
                          if any(r["lane"] in ("1d", "1w") and r["tradeable"] is True for r in v))
            rep = {"fires_log_blob": SNAPSHOT["fires_log"][1], "runs_logged": len(runs), "runs": [],
                   "fires": {"1d": 0, "1w": 0}, "identical": 0, "diffs": []}
            for k in pick:
                with open(os.path.join(shadow, "live", "latest_fires_v3.json"), "w") as f:
                    json.dump({"fires": runs[k]}, f)
                src = [x for x in SM.hourly_fires() if x.get("midna_tf") in ("1d", "1w")]
                mine = F.hourly_fires(shadow)
                bad = compare(src, mine)
                n = {ln: sum(1 for x in src if x["midna_tf"] == ln) for ln in ("1d", "1w")}
                rep["runs"].append({"run": k, "rows": len(runs[k]), "fires": n, "identical": not bad})
                for ln in n:
                    rep["fires"][ln] += n[ln]
                rep["identical"] += not bad
                if bad:
                    rep["diffs"].append({"run": k, "bad": bad[:4]})
            out["replay"] = rep
            out["identical"] = out["identical"] and not rep["diffs"]
            out["diffs"] = (out["diffs"] + rep["diffs"])[:4]
        return out
    finally:
        SM.SHADOW_DIR = saved
        shutil.rmtree(root, ignore_errors=True)
SYMS = ["AAPL", "MU", "ARM", "TEM", "ZS", "ABCL", "DKNG", "FCX", "SMCI", "PYPL", "CRWD", "OKLO"]


def gen_case(rnd):
    rows, ledger = [], []
    for k in range(rnd.randint(0, 14)):
        lane = rnd.choice(["1h", "1d", "1w"])
        sym = rnd.choice(SYMS)
        day = f"2026-10-{rnd.randint(1, 15):02d}"
        key = f"{sym}:{lane}:{rnd.choice(['swing', 'green', 'cyan'])}:{rnd.randint(10**9, 2 * 10**9)}:confirmed"
        units = rnd.choice(["", "u-a", "u-b,u-c", " u-d , u-e", "1h-basket"])
        rows.append({"symbol": sym, "time_et": f"{day} 09:30:00-04:00", "lane": lane,
                     "bar_source": rnd.choice(["yahoo:canonical", "yahoo", "alpaca:sip", "", None]),
                     "key": key, "tradeable": rnd.choice([True, True, False, None]),
                     "priority": rnd.choice([None, 0, 1, 2, 3]), "active_units": units,
                     "entry_ref": round(rnd.uniform(5, 300), 4), "stop_pct": rnd.choice([None, 12.0, 15.0, 99.0]),
                     "max_hold_bars": rnd.choice([None, 0, 20, 40, 52])})
        if rnd.random() < 0.7:
            u = units.split(",")[0].strip()
            rec = {"type": "fire", "key": key}
            if rnd.random() < 0.4:
                rec["tradeable"] = rnd.choice([True, False])
            if rnd.random() < 0.3:
                rec["bar_source"] = rnd.choice(["yahoo:canonical", "alpaca:sip"])
            if rnd.random() < 0.6 and u:
                rec["cal_plans"] = {u: {k2: v for k2, v in (("stop_pct", rnd.choice([10.0, 15.0, 99.0, None])),
                                                            ("max_bars", rnd.choice([30, 40, 52, None])))
                                        if rnd.random() < 0.8}}
            if rnd.random() < 0.7:
                rec["meta"] = {"decile": rnd.choice([1, 5, 9, 10, 7.5, "x", None]),
                               "score": rnd.choice([0.1, 2.5, -1.0, 7, "n/a", None])}
            ledger.append(json.dumps(rec, separators=(",", ":") if rnd.random() < 0.5 else (", ", ": ")))
        if rnd.random() < 0.2:
            ledger.append(json.dumps({"type": "outcome", "key": key, "ret": 0.01}))
    if rnd.random() < 0.2:
        ledger.append('{"type":"fire", broken')
    rnd.shuffle(ledger)
    return {"fires": rows}, ledger


def run(n=N_CASES, seed=20261016, n_forward=1000):
    import desk.vendor.midna.sleeve_midna as SM
    rnd = random.Random(seed)
    root = tempfile.mkdtemp(prefix="midna_fires_")
    diffs, stats = [], {"source_fires": 0, "lanes": {"1d": 0, "1w": 0}, "ledger_used": 0}
    saved = SM.SHADOW_DIR
    try:
        for case in range(n):
            shadow = os.path.join(root, f"c{case}", "shadow")      # a fresh root per case (the port memoises the ledger by file state)
            os.makedirs(os.path.join(shadow, "live"), exist_ok=True)
            os.makedirs(os.path.join(shadow, "log"), exist_ok=True)
            doc, ledger = gen_case(rnd)
            with open(os.path.join(shadow, "live", "latest_fires_v3.json"), "w") as f:
                json.dump(doc, f)
            with open(os.path.join(shadow, "log", "ledger.jsonl"), "w") as f:
                f.write("\n".join(ledger) + ("\n" if ledger else ""))
            SM.SHADOW_DIR = Path(shadow)
            src = [x for x in SM.hourly_fires() if x.get("midna_tf") in ("1d", "1w")]
            mine = F.hourly_fires(shadow)
            bad = compare(src, mine)
            stats["source_fires"] += len(src)
            for x in src:
                stats["lanes"][x["midna_tf"]] += 1
            stats["ledger_used"] += sum(1 for line in ledger if '"fire"' in line)
            if bad:
                diffs.append({"case": case, "bad": bad[:4]})
            shutil.rmtree(os.path.join(root, f"c{case}"), ignore_errors=True)
    finally:
        SM.SHADOW_DIR = saved
        shutil.rmtree(root, ignore_errors=True)
    real = real_snapshot()
    if real is not None and not real["identical"]:
        diffs.append({"case": "real_snapshot", "bad": real["diffs"]})
    fdiffs, fstats = forward_part(n_forward, rnd)
    for d in fdiffs:
        diffs.append(dict(d, part="forward"))
    res = {"cases": n + n_forward,
           "identical": n + n_forward - len([d for d in diffs if d["case"] != "real_snapshot"]), "diffs": diffs[:8],
           "n_diffs": len(diffs), "stats": dict(stats, forward=dict(fstats, cases=n_forward)), "real_snapshot": real,
           "sleeves": ["midna_hourly_1d", "midna_hourly_1w", "midna_w_cyan_breadth"],
           "method": "vendored sleeve_midna.hourly_fires (SHADOW_DIR -> the case's scratch research root) vs "
                     "midna_fires.hourly_fires on synthetic latest_fires_v3.json + ledger.jsonl; the 1D/1W fires in "
                     "order, every field the port emits exact; then once on the box's committed tracker state "
                     "(real_snapshot); and the vendored forward_fires vs the port on random forward states "
                     "(midna_w_cyan_breadth; the plan compared with exactly the removed 40% circuit taken out)"}
    write_receipt("midna_fires", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
