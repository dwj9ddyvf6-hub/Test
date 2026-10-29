"""killed_smcap_beta_52w: the study's main() (vendored weekly-phenotypes/code/run_smcap_beta_52w.py, unmodified; its
BASE / HOLD folders pointed at a scratch dir holding synthetic weekly_bars_dev.json, weekly_2022plus.json and
qualifiers_dev.jsonl) vs killed_data.smcap_features on the same merged weekly series.

Per case: 6-30 names + SPY with ~120 weekly bars (the dev file holds the first part, the 2022plus file the rest, as
the study merged them), one or two signal Fridays with M2 qualifiers (a few marked m23_inadm, plus admitted
non-qualifier rows for the control pool). Names follow a market factor with betas 0.3-3.0 and some crash into the
BEAT region. main()'s per-qualifier list (feats) is read at its return; compared exactly per qualifier: beat,
beat_lo52, beat_run13, dvol52, beta, hibeta, small, and the primary flag (beat and small and hibeta)."""
import contextlib
import io
import json
import math
import os
import random
import shutil
import sys
import tempfile

from desk.feedlib import killed_data as KD

from . import write_receipt
from .killed_pead import capture_locals

N_CASES = 1000


def gen_case(rnd):
    t0 = 1_500_000_000 - (1_500_000_000 % 604800) + 4 * 86400          # a Monday 00:00 UTC grid
    nb = rnd.randint(118, 130)
    spy, px = [], 250.0
    mkt = []
    for i in range(nb):
        r = rnd.gauss(0.002, 0.022)
        mkt.append(r)
        px *= math.exp(r)
        spy.append({"t": t0 + 604800 * i, "o": px, "h": px, "l": px, "c": round(px, 6), "v": 5e8})
    bars = {"SPY": spy}
    for k in range(rnd.randint(6, 30)):
        beta = rnd.uniform(0.3, 3.0)
        px, s = rnd.uniform(5, 200), []
        crash = rnd.random() < 0.35
        idio = rnd.choice([0.001, 0.002, 0.01, 0.03, 0.06])
        quiet = rnd.random() < 0.2                     # low variance, slow bleed, thin: the triple's own shape
        if quiet:
            beta, idio, crash = rnd.uniform(0.3, 0.6), 0.0005, False
        for i in range(nb):
            r = beta * mkt[i] + rnd.gauss(0, idio)
            if crash and 55 <= i <= 64:
                r -= 0.05
            if quiet and 20 <= i <= 66:
                r -= 0.006
            px = max(0.2, px * math.exp(r))
            v = rnd.uniform(1e3, 1e4) if quiet else rnd.uniform(1e4, 2e6)
            s.append({"t": t0 + 604800 * i, "o": px, "h": px, "l": px, "c": round(px, 6), "v": round(v, 2)})
        bars[f"W{k:02d}"] = s
    cut = rnd.randint(60, 90)
    dev = {s: bl[:cut] for s, bl in bars.items()}
    plus = {s: bl[cut - 5:] for s, bl in bars.items()}             # overlapping weeks: the merge dedupes by t
    rows = []
    for _ in range(rnd.randint(1, 2)):
        i = rnd.randint(53, min(cut - 1, nb - 54))
        friday = f"2020-01-{10 + i % 18:02d}"
        names = [s for s in bars if s != "SPY"]
        rnd.shuffle(names)
        nq = rnd.randint(2, len(names))
        for j, s in enumerate(names):
            m2 = j < nq
            rows.append({"friday": friday + f"#{i}", "symbol": s, "idx": i, "m2": ["GREEN"] if m2 else [],
                         "m23_inadm": (rnd.random() < 0.1) if m2 else (rnd.random() < 0.2)})
    return bars, dev, plus, rows


def run(n=N_CASES, seed=20261016):
    from desk.vendor.midna_research import run_smcap_beta_52w as S
    rnd = random.Random(seed)
    work = tempfile.mkdtemp(prefix="killed_smcap_") + "/"
    diffs, stats = [], {"qualifiers": 0, "beat": 0, "small": 0, "hibeta": 0, "primary": 0}
    saved = (S.BASE, S.HOLD)
    try:
        S.BASE = S.HOLD = work
        for case in range(n):
            bars, dev, plus, rows = gen_case(rnd)
            json.dump(dev, open(work + "weekly_bars_dev.json", "w"))
            json.dump(plus, open(work + "weekly_2022plus.json", "w"))
            with open(work + "qualifiers_dev.jsonl", "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            with contextlib.redirect_stdout(io.StringIO()):
                loc = capture_locals(S.main, S.main.__code__)
            if "feats" not in loc:
                diffs.append({"case": case, "bad": f"source failed: {loc.get('_error')}"})
                continue
            src = loc["feats"]
            merged, _ = S.load_merged_bars()
            quals = [{"friday": r["friday"], "symbol": r["symbol"], "idx": r["idx"]} for r in rows
                     if r["m2"] and not r["m23_inadm"]]
            spy_t2c = {b["t"]: b["c"] for b in merged["SPY"]}
            mine = KD.smcap_features(quals, merged, spy_t2c)
            keys = ("friday", "symbol", "i", "beat", "beat_lo52", "beat_run13", "dvol52", "beta", "hibeta", "small")
            a = sorted(({k: f[k] for k in keys} for f in src), key=lambda f: (f["friday"], f["symbol"]))
            b = sorted(({k: f[k] for k in keys} for f in mine), key=lambda f: (f["friday"], f["symbol"]))
            if a != b:
                bad = [(x, y) for x, y in zip(a, b) if x != y][:3] or [("count", len(a), len(b))]
                diffs.append({"case": case, "bad": bad})
            for f in mine:
                if f["primary"] != (f["beat"] and f["small"] and f["hibeta"]):
                    diffs.append({"case": case, "bad": "primary flag"})
            stats["qualifiers"] += len(src)
            for k in ("beat", "small", "hibeta"):
                stats[k] += sum(1 for f in src if f[k])
            stats["primary"] += sum(1 for f in mine if f["primary"])
            if (case + 1) % 100 == 0:
                print(f"case {case + 1}/{n} diffs={len(diffs)}", file=sys.stderr, flush=True)
    finally:
        S.BASE, S.HOLD = saved
        shutil.rmtree(work, ignore_errors=True)
    res = {"cases": n, "identical": n - len({d["case"] for d in diffs}), "diffs": diffs[:6], "n_diffs": len(diffs),
           "stats": stats, "sleeves": ["killed_smcap_beta_52w"],
           "method": "vendored run_smcap_beta_52w.main() unmodified on synthetic dev / 2022plus weekly files and "
                     "qualifier rows (BASE/HOLD redirected, feats read at return) vs killed_data.smcap_features on "
                     "the same merged series; every qualifier's beat / lo52 / run13 / dvol52 / beta / hibeta / small "
                     "exact"}
    write_receipt("killed_smcap", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
