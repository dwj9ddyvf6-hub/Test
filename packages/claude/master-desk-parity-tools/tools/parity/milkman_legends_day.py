"""milkman_legends_day: his Legend's Buy Day package (02_buyday_backtest.py, LEG 2, the day leg) vs the port's LBDD
bar program (desk/sleeves/milkman/rules.py), trade by trade.

SOURCE side: quant-research-critical@0be4c575 milkman-study/v2/packages/legends-buy-day-package/02_buyday_backtest.py
(blob 8c8a41f1, read with git and blob-checked, written to a temporary directory) run unmodified in its own process
(python3 -I) on a synthetic 1-minute CSV with --cost 0 --slip 0; the rows of its buyday-trades.csv with leg == "day"
are its trades.
PORT side: the LBDD rule replayed bar by bar (open, touch over the bar, close, end) on the daily bars of the same
minutes, with his ES tick (0.25) in the cell; the desk's lane runs it on SPY with a 0.01 tick.
Series: regular-hours minutes only (09:30-15:59 ET, weekdays), on the 0.25 grid, so his full session is the regular
session and his ATR (the mean of the prior 20 full-session ranges), stop (one tick under the prior full-session low)
and overnight move (the 09:30 open against the prior 15:59 close) read what the port reads. Sessions drift in regimes
with multi-day selloffs (lower-low streaks) and open with gaps on both sides of the 0.15 ATR gate.
Compared exactly: (entry date, entry px, exit px, exit kind: stop | close), from the 26th session on: his frame drops
its first 20 sessions for the ATR, and his streak reads the dropped frame, so it needs five more.

    python3 -m tools.parity.milkman_legends_day"""
import csv
import hashlib
import os
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta

from . import write_receipt

REPO = "/home/user/quant-research-critical"
COMMIT = "0be4c57569e363d052bd23564cf0664697439927"
PATH = "milkman-study/v2/packages/legends-buy-day-package/02_buyday_backtest.py"
BLOB = "8c8a41f122e2a1c98411e61e7256afcb9662be6f"
CASES = int(os.environ.get("LEGENDS_DAY_CASES", 300))
SESSIONS = 320
FIRST = 26
CELL = {"k": 4, "gate": 0.15, "atrn": 20, "tick": 0.25}


def his_script():
    raw = subprocess.run(["git", "-C", REPO, "show", f"{COMMIT}:{PATH}"], capture_output=True, check=True).stdout
    sha = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
    if sha != BLOB:
        raise SystemExit(f"blob mismatch: {sha} != {BLOB}")
    return raw


def q(x):
    return round(x * 4) / 4.0


def weekdays(n, start=date(2015, 1, 5)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def gen(seed):
    """sessions of 390 one-minute bars: [(date, [(hh:mm, o, h, l, c), ...]), ...]"""
    rng = random.Random(seed)
    px, sessions, sell, ranges = 4000.0, [], 0, []
    for d in weekdays(SESSIONS):
        if sell == 0 and rng.random() < 0.12:
            sell = rng.randint(3, 6)                               # a multi-day selloff
        drift = -0.0045 if sell else rng.gauss(0.0004, 0.002)
        sell = max(0, sell - 1)
        if len(ranges) >= 20 and rng.random() < 0.3:               # an open at the gate's edge
            o = q(px + sum(ranges[-20:]) / 20 * rng.uniform(0.13, 0.17))
        else:
            gap = rng.gauss(0.0, 0.002) if rng.random() < 0.8 else rng.gauss(0.0, 0.006)
            o = q(px * (1 + gap))
        vol = px * rng.uniform(0.0004, 0.0009)
        step = px * drift / 390
        bars, c = [], o
        for m in range(390):
            hh, mm = divmod(9 * 60 + 30 + m, 60)
            bo = c
            c = q(bo + step + rng.gauss(0, vol))
            hi = q(max(bo, c) + abs(rng.gauss(0, vol / 2)))
            lo = q(min(bo, c) - abs(rng.gauss(0, vol / 2)))
            bars.append((f"{hh:02d}:{mm:02d}", bo, hi, lo, c))
        sessions.append((d, bars))
        ranges.append(max(b[2] for b in bars) - min(b[3] for b in bars))
        px = c
    return sessions


def theirs(script, sessions, work):
    data = os.path.join(work, "es.csv")
    with open(data, "w", newline="") as f:
        w = csv.writer(f)
        for d, bars in sessions:
            for t, o, h, l, c in bars:
                w.writerow([f"{d} {t}:00", f"{o:.2f}", f"{h:.2f}", f"{l:.2f}", f"{c:.2f}", 100])
    src = os.path.join(work, "buyday.py")
    with open(src, "wb") as f:
        f.write(script)
    out = os.path.join(work, "out")
    subprocess.run([sys.executable, "-I", src, data, "--cost", "0", "--slip", "0", "--out", out], capture_output=True,
                   cwd=work, timeout=600)
    rows = list(csv.DictReader(open(os.path.join(out, "buyday-trades.csv"))))
    return sorted((r["date"], round(float(r["entry_px"]), 4), round(float(r["exit_px"]), 4),
                   "stop" if r["reason"] == "stop" else "close") for r in rows if r["leg"] == "day")


def ours(sessions):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from desk.sleeves.milkman import rules as R
    dates = [d for d, _ in sessions]
    o = [bars[0][1] for _, bars in sessions]
    h = [max(b[2] for b in bars) for _, bars in sessions]
    l = [min(b[3] for b in bars) for _, bars in sessions]
    c = [bars[-1][4] for _, bars in sessions]
    X = R.Ctx(dates, o, h, l, c, [1e6] * len(dates), "fut")
    evs, _ = R.replay("LBDD", X, 1, CELL)
    ent = {e["tid"]: e for e in evs if e["kind"] == "enter"}
    return sorted((ent[e["tid"]]["date"], round(ent[e["tid"]]["px"], 4), round(e["px"], 4),
                   "stop" if e["at"] == "touch" else "close") for e in evs if e["kind"] == "exit" and e["tid"] in ent)


def one(seed):
    script = his_script()
    sessions = gen(seed)
    first = sessions[FIRST][0]
    with tempfile.TemporaryDirectory() as work:
        a = [x for x in theirs(script, sessions, work) if x[0] >= first]
    b = [x for x in ours(sessions) if x[0] >= first]
    return {"seed": seed, "identical": a == b, "theirs": a, "ours": b,
            "stops": sum(1 for x in a if x[3] == "stop")}


def run():
    seeds = [20261019 + i for i in range(CASES)]
    with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as ex:
        res = list(ex.map(one, seeds))
    diffs = [{"seed": r["seed"], "theirs": r["theirs"], "ours": r["ours"]} for r in res if not r["identical"]]
    trades = sum(len(r["theirs"]) for r in res)
    out = {"sleeves": ["mk_legendsbuydaydayleg"], "cases": len(res),
           "identical": sum(1 for r in res if r["identical"]), "n_diffs": len(diffs), "diffs": diffs[:20],
           "stats": {"trades": trades, "stop_exits": sum(r["stops"] for r in res), "sessions_per_case": SESSIONS,
                     "compared_from_session": FIRST},
           "source": {"repo": "quant-research-critical", "commit": COMMIT, "path": PATH, "blob": BLOB},
           "method": "his package's day leg run unmodified in its own process on synthetic regular-hours ES minutes "
                     "(--cost 0 --slip 0) vs rules.py LBDD replayed bar by bar on their daily bars; day-leg trades "
                     "compared exactly (entry date, entry px, exit px, stop | close)"}
    write_receipt("milkman_legends_day", out)
    return out


if __name__ == "__main__":
    r = run()
    print({k: r[k] for k in ("cases", "identical", "n_diffs")}, r["stats"])
    for d in r["diffs"][:3]:
        print(d)
