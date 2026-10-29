"""killed_pead_price_surprise / killed_pead_spillover_scalp: the studies' own code run unmodified on synthetic
calendars and bars vs the desk's producer and sleeves.

PEAD (vendored pead/code/04_backtest.py): main() with pd.read_parquet answered by the case's frames and OUT in a
scratch dir; its locals are read at return (sys.setprofile) - evt (every kept event's surprise S and quarter
quintile) and tr_all (each event's 1/5/10/20-day returns). Compared exactly per event: S against
killed_data.surprise; the top-quintile membership against killed_data.q80 applied to the same quarter's S (the sleeve
uses the previous quarter's cut - the named divergence - but the cut is the same computation); and every hold's
return against the PeadPriceSurprise sleeve's tranches (entered at t+2, exited at the close of entry + n - 1)
priced on the same bars.

Spillover (vendored pead/v1_spillover_dev_2026-10-02.py, whose committed text has its module-level statements out
of order and cannot run as a script): its `__main__` block is executed unmodified with pd.read_parquet answered by
the case frames; the per-event `cohort` list it builds before the shuffled aggregate lines fail is read back and
compared exactly with the sleeve's rule (buy the event-day close when c_t / c_{t-1} - 1 - 0.0015 > 0.0001, sell the
next open) on the same bars."""
import contextlib
import io
import json
import os
import random
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from desk import calendar as cal
from desk.contract import View
from desk.feedlib import killed_data as KD
from desk.sleeves.killed import common as K
from desk.sleeves.killed import events as EV
from desk.util import ET

from . import write_receipt

N_CASES = 1000
VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desk", "vendor",
                      "midna_research")


def sessions(a, n):
    out, d = [], date.fromisoformat(a)
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def gen_case(rnd):
    start = (date(2024, 1, 2) + timedelta(days=rnd.randint(0, 500))).isoformat()
    days = sessions(start, rnd.randint(120, 170))
    syms = ["SPY"] + [f"E{k:02d}" for k in range(rnd.randint(14, 30))]
    bars = []
    for s in syms:
        px = rnd.uniform(5, 300)
        first = rnd.randint(0, 5) if s != "SPY" else 0
        for i, d in enumerate(days[first:]):
            o = px * (1 + rnd.gauss(0, 0.004))
            px = max(0.5, px * (1 + rnd.gauss(0.0003, 0.02 if s != "SPY" else 0.009)))
            bars.append({"symbol": s, "date": d, "o": round(o, 4), "c": round(px, 4)})
    events = []
    for s in syms[1:]:
        for _ in range(rnd.randint(1, 3)):
            d = rnd.choice(days[2:-25])
            if rnd.random() < 0.05:
                d = (date.fromisoformat(d) + timedelta(days=1)).isoformat()   # a calendar date that may not trade
            events.append({"event_date": d, "symbol": s, "time": rnd.choice(["time-after-hours", "time-pre-market",
                                                                             "time-not-supplied"]),
                           "market_cap": rnd.uniform(1e8, 5e10)})
    if rnd.random() < 0.3:
        events.append({"event_date": days[10], "symbol": "NOBARS", "time": "time-not-supplied", "market_cap": 1e9})
    # the study's quarters held thousands of events; a synthetic quarter with too few for pd.qcut's five bins is
    # dropped (the source's qcut would leave NaN quintiles there)
    per_q = {}
    for e in events:
        per_q.setdefault(KD.quarter_of(e["event_date"]), []).append(e)
    events = [e for q, es in per_q.items() if len(es) >= 12 for e in es]
    return days, pd.DataFrame(bars), pd.DataFrame(events).drop_duplicates(["event_date", "symbol"])


@contextlib.contextmanager
def parquet_answer(frames):
    real = pd.read_parquet
    pd.read_parquet = lambda path, *a, **k: frames[os.path.basename(str(path))].copy()
    try:
        yield
    finally:
        pd.read_parquet = real


def capture_locals(fn, code):
    """call fn() and return the locals of the frame running `code` at its return (or exception exit)."""
    got = {}

    def prof(frame, event, arg):
        if frame.f_code is code and event in ("return", "c_exception"):
            got.update(frame.f_locals)
    sys.setprofile(prof)
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - the spillover script fails after its loop by construction
        got["_error"] = f"{type(e).__name__}: {e}"
    finally:
        sys.setprofile(None)
    return got


def pead_case(P, days, bars, events, work):
    P.OUT = os.path.join(work, "results_dev.md")
    with parquet_answer({"earnings_events.parquet": events, "daily_bars_2016_2021.parquet": bars}), \
            contextlib.redirect_stdout(io.StringIO()):
        loc = capture_locals(P.main, P.main.__code__)
    return loc


def desk_bars(df, sym):
    g = df[df["symbol"] == sym].sort_values("date")
    return [{"t": datetime.fromisoformat(d).replace(hour=9, minute=30, tzinfo=ET).timestamp(), "o": o, "c": c,
             "h": max(o, c), "l": min(o, c), "v": 1e6} for d, o, c in zip(g["date"], g["o"], g["c"])]


def run_pead(n, rnd):
    from desk.vendor.midna_research import pead_backtest_dev as P
    work = tempfile.mkdtemp(prefix="killed_pead_")
    diffs, stats = [], {"events": 0, "cohort": 0, "hold_returns": 0}
    try:
        for case in range(n):
            days, bars, events = gen_case(rnd)
            while len(events) < 12:                       # a case needs a quarter with enough events for qcut
                days, bars, events = gen_case(rnd)
            loc = pead_case(P, days, bars, events, work)
            if "evt" not in loc or "tr_all" not in loc:
                diffs.append({"case": case, "bad": f"source failed: {loc.get('_error')}"})
                continue
            evt, tr_all = loc["evt"], loc["tr_all"]
            spy = desk_bars(bars, "SPY")
            cache = {}
            bad = []
            for row in evt.itertuples():
                t = str(pd.Timestamp(row.event_date).date())
                b = cache.setdefault(row.symbol, desk_bars(bars, row.symbol))
                s = KD.surprise(b, spy, t)
                if s != row.surprise:
                    bad.append(f"S {row.symbol} {t}: source {row.surprise} desk {s}")
            # dropped events: the producer returns None for exactly the events the source dropped
            kept = {(r.symbol, str(pd.Timestamp(r.event_date).date())) for r in evt.itertuples()}
            for r in events.itertuples():
                key = (r.symbol, r.event_date)
                b = cache.setdefault(r.symbol, desk_bars(bars, r.symbol))
                if (KD.surprise(b, spy, r.event_date) is not None) != (key in kept):
                    bad.append(f"kept-set {key}")
            # the cut: q80 of the quarter's S <-> quintile 5
            for q, g in evt.groupby("quarter"):
                cut = KD.q80(list(g["surprise"]))
                if cut is None:
                    continue
                mine = set(g.loc[g["surprise"] > cut, "symbol"] + "|" + g.loc[g["surprise"] > cut, "event_date"].astype(str))
                src = set(g.loc[g["quintile"] == 5, "symbol"] + "|" + g.loc[g["quintile"] == 5, "event_date"].astype(str))
                if mine != src:
                    bad.append(f"cohort {q}")
            # the sleeve's tranches on the cohort, priced on the same bars
            sl = EV.PeadPriceSurprise()
            for r in tr_all[tr_all["quintile"] == 5].itertuples():
                t = str(pd.Timestamp(r.event_date).date())
                entry = K.add_sessions(t, 2)
                f = {"t": t, "ready": True, "cut": -1.0, "from_quarter": "x", "cohort": {r.symbol: r.surprise},
                     "n_events": 1}
                sl.signal(View(now=datetime.fromisoformat(entry).replace(hour=8, tzinfo=ET).timestamp(), session=entry,
                               extra={"killed_pead": f, "pending_orders": [], "closed_trades": []}))
                b = {K.bar_day(x): x for x in cache[r.symbol]}
                for tr in sl._st["tranches"]:
                    h = int(tr["arm"].split(":")[1])
                    if tr["exit_day"] not in b or entry not in b:
                        bad.append(f"no bar {r.symbol} {tr['exit_day']}")
                        continue
                    mine = b[tr["exit_day"]]["c"] / b[entry]["o"] - 1.0 - P.COST
                    if mine != getattr(r, f"ret_{h}"):
                        bad.append(f"ret_{h} {r.symbol} {t}: source {getattr(r, f'ret_{h}')} sleeve {mine}")
                    stats["hold_returns"] += 1
                sl._st = None
            stats["events"] += len(evt)
            stats["cohort"] += int((tr_all["quintile"] == 5).sum())
            if bad:
                diffs.append({"case": case, "bad": bad[:6]})
            if (case + 1) % 100 == 0:
                print(f"pead {case + 1}/{n} diffs={len(diffs)}", file=sys.stderr, flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return diffs, stats


SPILL_SRC = os.path.join(VENDOR, "pead_v1_spillover_dev.py")


def spill_case(code, bars, events):
    g = {"__name__": "__main__", "__builtins__": __builtins__}
    pre, _, main = open(SPILL_SRC).read().partition('if __name__ == "__main__":\n')
    imports = "\n".join(l for l in pre.splitlines() if l.startswith("import ") or l.startswith("from "))
    consts = "\n".join(l for l in pre.splitlines() if l.split("=")[0].strip() in ("COST", "FILT", "NCTL", "SEED"))
    state = "by = {}\ncohort = []\ncontrol = []\nn_events = 0; n_skip = 0\n"
    body = "\n".join(l[4:] if l.startswith("    ") else l for l in main.splitlines())
    with parquet_answer({"earnings_events.parquet": events, "daily_bars_2016_2021.parquet": bars}):
        try:
            exec(compile(imports + "\n" + consts + "\n" + state + body, SPILL_SRC, "exec"), g)
        except NameError as e:
            g["_error"] = str(e)                     # the committed file's shuffled aggregate lines (t_rel ...)
    return g


def run_spill(n, rnd):
    diffs, stats = [], {"events": 0, "trades": 0}
    for case in range(n):
        days, bars, events = gen_case(rnd)
        while len(events) < 12:
            days, bars, events = gen_case(rnd)
        events = events[events["symbol"] != "NOBARS"]
        g = spill_case(None, bars, events)
        if "t_rel" not in str(g.get("_error")):
            diffs.append({"case": case, "bad": f"the source block stopped early: {g.get('_error')}"})
        src = [float(x) for x in g["cohort"]] if "cohort" in g else []
        mine = []
        for r in events.sort_index().itertuples():
            b = [x for x in bars[bars["symbol"] == r.symbol].sort_values("date").itertuples()]
            ds = [x.date for x in b]
            if r.event_date not in ds:
                continue
            i = ds.index(r.event_date)
            if i == 0 or not (b[i].c > 0 and b[i - 1].c > 0):
                continue
            rp = b[i].c / b[i - 1].c - 1 - EV.SPILL_COST
            if not rp > EV.SPILL_FILT or i + 1 >= len(b) or not b[i + 1].o > 0:
                continue
            sl = EV.PeadSpilloverScalp()
            now = cal.session_close(r.event_date) - 25 * 60
            f = {"t": r.event_date, "events": {r.symbol: {"prev_close": b[i - 1].c, "last": b[i].c}}}
            sl.signal(View(now=now, session=r.event_date, extra={"killed_spillover": f, "pending_orders": [],
                                                               "closed_trades": []}))
            (tr,) = sl._st["tranches"]
            if tr["exit_day"] != b[i + 1].date or tr["enter_at"] != "close" or tr["exit_at"] != "open":
                diffs.append({"case": case, "bad": f"tranche {tr}"})
            mine.append(b[i + 1].o / b[i].c - 1 - EV.SPILL_COST)
        if mine != src:
            diffs.append({"case": case, "bad": f"cohort source {src[:4]} sleeve {mine[:4]}"})
        stats["events"] += len(events)
        stats["trades"] += len(src)
    return diffs, stats


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    d1, s1 = run_pead(n, rnd)
    d2, s2 = run_spill(n, rnd)
    res = {"cases": 2 * n, "identical": 2 * n - len(d1) - len(d2), "n_diffs": len(d1) + len(d2),
           "diffs": (d1 + d2)[:8], "stats": {"pead": s1, "spillover": s2},
           "sleeves": ["killed_pead_price_surprise", "killed_pead_spillover_scalp"],
           "method": "PEAD: vendored 04_backtest.py main() unmodified on synthetic calendars/bars (pd.read_parquet "
                     "answered, locals read at return) vs killed_data.surprise / q80 and the sleeve's hold tranches - "
                     "S, kept set, in-quarter cohort and every hold return exact; spillover: the vendored script's "
                     "__main__ block executed unmodified (its shuffled aggregate lines fail after the loop) - the "
                     "per-event cohort returns vs the sleeve's rule and tranche days exact"}
    write_receipt("killed_pead", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
