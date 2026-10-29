"""snapback: old snapback_sleeve.py (compute_flags + mode_rank staging) vs the restored femto port.

A synthetic genome (bands of weekly dollar volume, beaten-down / wide-spread names, near-low and far-from-low
closes) of 300 daily bars per name; weekly bars are the Monday-bucketed daily bars for BOTH codes (what the
old Alpaca 1Week bars carried). Compared: the flagged list (symbol, close, spread, ret13, near_low, wkvol),
and the old mode_rank's staged pending (buys after the held / 91-day de-overlap / capacity rules merged
with surviving buys, sells due by the rank day, exit dates fill-Monday + 91) given random books, last
exits and previously staged buys. The fill itself is the shared sleeve_core law (its own receipt)."""
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt

F = femto_module("snapback")
N_CASES = 40

OLD = r'''
import types
from datetime import date, timedelta
import sleeve_core as core
import snapback_sleeve as O
out = []
for c in PAYLOAD["cases"]:
    weekly = {s: [[w["t"] + 8 * 3600, 0, 0, 0, w["c"], w["v"]] for w in wl] for s, wl in c["weekly"].items()}
    daily = {s: [[r["d"], r["o"], r["h"], r["l"], r["c"], r["v"]] for r in rows] for s, rows in c["daily"].items()}
    friday = date.fromisoformat(c["today"])
    while friday.weekday() != 4:
        friday -= timedelta(days=1)
    flagged = O.compute_flags(weekly, daily, friday)
    STATE = {"book": c["book"], "pending": c["pending"], "last_exit": c["last_exit"], "stats": {}}
    O.SL.load_state = lambda dry_run=False: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    core.load_cache = lambda path: {"bars": weekly} if "weekly" in path.lower() else {"bars": daily}
    O.core.load_cache = core.load_cache
    res = O.mode_rank(c["today"], dry_run=False, no_fetch=True)
    out.append({"flagged": flagged, "pending": STATE["pending"]})
print(json.dumps(out))
'''


def _genome(rnd, n_names, n_days, start):
    dates = trading_dates(start, n_days)
    daily = {}
    for k in range(n_names):
        s = "G%03d" % k
        px = rnd.uniform(1.5, 60)
        vol = rnd.uniform(0.01, 0.09)
        dv = 10 ** rnd.uniform(4.0, 8.0)                  # daily dollar volume band
        crash = rnd.random() < 0.35
        rows = []
        for i, d in enumerate(dates):
            drift = -0.012 if crash and n_days - 70 < i < n_days - 5 else rnd.uniform(-0.001, 0.0015)
            o = px * (1 + rnd.gauss(0, vol / 3))
            c = max(0.2, px * (1 + rnd.gauss(drift, vol)))
            h = max(o, c) * (1 + abs(rnd.gauss(0, vol)))
            lo = min(o, c) * (1 - abs(rnd.gauss(0, vol)))
            v = 0.0 if rnd.random() < 0.01 else float(int(dv / c * rnd.uniform(0.5, 1.5)))
            rows.append({"d": d, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4), "v": v})
            px = c
        daily[s] = rows
    return dates, daily


def run():
    rnd = random.Random(29)
    cases = []
    for k in range(N_CASES):
        dates, daily = _genome(rnd, rnd.randint(90, 160), 300, "2025-01-06")
        fridays = [d for d in dates[-15:] if date.fromisoformat(d).weekday() == 4]
        today = rnd.choice(fridays)
        daily = {s: [r for r in rows if r["d"] <= today] for s, rows in daily.items()}
        weekly = F.weekly_from_daily({s: as_epoch(rows) for s, rows in daily.items()})
        names = sorted(daily)
        book = {}
        for s in rnd.sample(names, rnd.randint(0, 9)):
            due = (date.fromisoformat(today) + timedelta(days=rnd.randint(-6, 80))).isoformat()
            book[s] = {"qty": float(rnd.randint(1, 300)), "entry_px": round(rnd.uniform(1, 50), 2),
                       "entry_date": today, "exit_due_date": due}
        last_exit = {s: (date.fromisoformat(today) - timedelta(days=rnd.randint(1, 140))).isoformat()
                     for s in rnd.sample(names, rnd.randint(0, 25))}
        pending = {"buys": rnd.sample(names, rnd.randint(0, 3)), "sells": rnd.sample(names, rnd.randint(0, 2)),
                   "exit_dates": {}}
        cases.append({"today": today, "daily": daily, "weekly": weekly, "book": book, "last_exit": last_exit,
                      "pending": pending})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"flagged": 0, "staged_buys": 0, "staged_sells": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        bars = {s: as_epoch(rows) for s, rows in c["daily"].items()}
        friday = date.fromisoformat(c["today"])
        flagged = F.compute_flags(c["weekly"], bars, friday)
        cmp("flagged", ci, o["flagged"], flagged)
        counts["flagged"] += len(o["flagged"])
        state = {s: {"position": dict(p)} for s, p in c["book"].items()}
        for s, d in c["last_exit"].items():
            state.setdefault(s, {"position": None})["last_exit_date"] = d
        now = datetime.fromisoformat(c["today"]).replace(hour=21, minute=0, tzinfo=timezone.utc).timestamp()
        ctx = fc.Context(now=now, session=c["today"], equity=100_000.0,
                         extra={"sleeve_state": state, "meta": {"pending": c["pending"]}})
        pend = F.rank(bars, ctx, {"pending": c["pending"]})
        new = {"buys": pend["buys"], "sells": pend["sells"], "exit_dates": pend["exit_dates"]}
        a = {k: o["pending"].get(k) for k in ("buys", "sells", "exit_dates")}
        cmp("pending", ci, a, new)
        counts["staged_buys"] += len(a["buys"] or [])
        counts["staged_sells"] += len(a["sells"] or [])
    res = {"sleeve": "snapback", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("snapback" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
