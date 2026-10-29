"""killed_leader1d_long / killed_leader1d_short: the study's own main() (vendored leader1d_long_fulluniverse_
2026-10-02.py, run unmodified on a synthetic breakout_universe_daily.jsonl) vs the sleeves stepped session by session.

Per case: a random universe (3-5 names + SPY, real trading days) with momentum bursts so the gated Leader-1d event
fires. Source side: main() with DATA / OUT pointed at the case files and the window opened over the case (its
WARMUP set to 251 - the genome job's 252-bar minimum - so both sides start on the same bar; the warm-up gap is the
sleeves' named divergence). Sleeve side: the genome job's per-session rows (leader.latest's frame row of each name's
bars through t) fed to the sleeve at the first pass of t+1; its kept events are scored with the source's own trade()
and summarised with the source's own summary. Compared exactly: n, mean, median, t, hit, min, max of the kept trades
(the long sleeve), and for the short sleeve the same kept set with net = -(long net) - 0.002 (5bp/side, short)."""
import contextlib
import io
import json
import math
import os
import random
import shutil
import sys
import tempfile
from datetime import date

import numpy as np

from desk import calendar as cal
from desk.contract import View
from desk.sleeves.killed import common as K
from desk.sleeves.killed import daily as DL

from . import write_receipt

N_CASES = 1000


def gen_universe(rnd, start, n_bars):
    days, d = [], date.fromisoformat(start)
    while len(days) < n_bars:
        if cal.is_trading_day(d):
            days.append(d.isoformat())
        d = date.fromordinal(d.toordinal() + 1)
    out = {}
    for sym in ["SPY"] + [f"N{k}" for k in range(rnd.randint(3, 5))]:
        px, rows = rnd.uniform(10, 200), []
        drift = 0.0
        for i, day in enumerate(days):
            if rnd.random() < 0.04:
                drift = rnd.choice([-0.01, 0.0, 0.004, 0.012, 0.025])
            r = rnd.gauss(drift, 0.022)
            o = px * (1 + rnd.gauss(0, 0.006))
            c = max(0.5, px * (1 + r))
            h = max(o, c) * (1 + abs(rnd.gauss(0, 0.008)))
            l = min(o, c) * (1 - abs(rnd.gauss(0, 0.008)))
            v = float(int(rnd.uniform(3e5, 2e6) * (2.5 if r > 0.02 else 1.0)))
            rows.append([day, round(o, 4), round(h, 4), round(l, 4), round(c, 4), v])
            px = c
        out[sym] = rows
    return days, out


def run_source(L1, raw, work):
    data = os.path.join(work, "daily.jsonl")
    with open(data, "w") as f:
        for s, bars in raw.items():
            f.write(json.dumps({"s": s, "bars": bars}) + "\n")
    out = os.path.join(work, "res.json")
    saved = (L1.DATA, L1.OUT, L1.WARMUP, L1.EVENT_START, L1.WINDOW_END)
    try:
        L1.DATA, L1.OUT, L1.WARMUP = data, out, 251
        L1.EVENT_START, L1.WINDOW_END = date(2000, 1, 1), date(2100, 1, 1)
        with contextlib.redirect_stdout(io.StringIO()):
            L1.main()
    finally:
        L1.DATA, L1.OUT, L1.WARMUP, L1.EVENT_START, L1.WINDOW_END = saved
    return json.load(open(out))


def sleeve_kept(sleeve, frames, days):
    """step the sleeve: at the first pass of each session t+1, the rows of session t (names with >= 252 bars)."""
    st, kept = {}, []
    for k in range(251, len(days) - 1):
        t, nxt = days[k], days[k + 1]
        rows = {}
        for s, df in frames.items():
            r = df.iloc[k]
            rows[s] = [t, int(r["score"]), bool(r["gate"])]
        v = View(now=_at(nxt), session=nxt, state=st,
                 extra={"killed_leader_last": rows, "pending_orders": [], "closed_trades": []})
        sleeve.signal(v)
        st = sleeve._st
        for tr in st.get("tranches", []):
            if tr["status"] == "planned" and tr["enter_day"] == nxt:
                kept.append((tr["sym"], days.index(tr["event"])))
                tr["status"], tr["units"], tr["entry_ref"] = "held", 1.0, 1.0      # the book took it
    return kept


def _at(day):
    from datetime import datetime
    from desk.util import ET
    y, m, d = map(int, day.split("-"))
    return datetime(y, m, d, 9, 31, tzinfo=ET).timestamp()


def summ(L1, v):
    v = np.asarray(v, float)
    out = {"n": len(v)}
    if len(v):
        out.update({"mean": float(np.mean(v)), "median": float(np.median(v)), "t": float(L1.tstat(v)),
                    "hit": float(np.mean(v > 0)), "min": float(np.min(v)), "max": float(np.max(v))})
    return out


def run(n=N_CASES, seed=20261016):
    from desk.feedlib import leader
    L1 = leader.l1()                                       # the vendored study module (hyphenated file name)
    rnd = random.Random(seed)
    work = tempfile.mkdtemp(prefix="killed_leader_")
    diffs, stats = [], {"kept_long": 0, "events_raw": 0, "cases_with_trades": 0}
    try:
        for case in range(n):
            days, raw = gen_universe(rnd, "2023-01-03", rnd.randint(300, 380))
            src = run_source(L1, raw, work)
            frames = {s: L1.frame(raw[s]) for s in raw if s != "SPY"}
            long_s, short_s = DL.Leader1dLong(), DL.Leader1dShort()
            long_s.UNIVERSE = short_s.UNIVERSE = tuple(sorted(frames))
            mine = []
            for side, sl in ((1, long_s), (-1, short_s)):
                kept = sorted(sleeve_kept(sl, frames, days))
                nets = []
                for s, i in kept:
                    if i + L1.HOLD >= len(frames[s]):
                        continue                                  # the source's right-censoring
                    net, _ = L1.trade(frames[s], i, L1.HOLD)      # long open_{t+1} -> close_{t+20}, 5bp/side
                    if net is not None:
                        nets.append(net if side > 0 else -net - 0.002)
                mine.append(nets)
            lo = summ(L1, mine[0])
            sh = summ(L1, mine[1])
            exp_short = summ(L1, [-x - 0.002 for x in mine[0]])
            bad = []
            for k in ("n", "mean", "median", "t", "hit", "min", "max"):
                a, b = src["leader"].get(k), lo.get(k)
                if not (a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b))):
                    bad.append(f"long {k}: source {a} sleeve {b}")
            if sh["n"] != src["leader"]["n"] or any(
                    not (sh.get(k) == exp_short.get(k) or (isinstance(sh.get(k), float) and math.isnan(sh[k])))
                    for k in ("mean", "median", "min", "max")):
                bad.append(f"short: {sh} vs {exp_short}")
            stats["kept_long"] += lo["n"]
            stats["events_raw"] += src["n_events_raw"]
            stats["cases_with_trades"] += lo["n"] > 0
            if bad:
                diffs.append({"case": case, "bad": bad})
            if (case + 1) % 50 == 0:
                print(f"case {case + 1}/{n} diffs={len(diffs)}", file=sys.stderr, flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["killed_leader1d_long", "killed_leader1d_short"],
           "method": "leader1d_long_fulluniverse_2026-10-02.py main() run unmodified on a synthetic daily file "
                     "(DATA/OUT redirected, window opened, WARMUP 251 = the genome job's 252-bar floor) vs the "
                     "sleeves stepped session by session on the frame rows; kept trades scored by the source's "
                     "trade(); n/mean/median/t/hit/min/max exact (short: same kept set, net = -long - 0.002)"}
    write_receipt("killed_leader", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
