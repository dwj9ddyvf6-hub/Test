"""rule_1h_cyan_raw: the old mode_rank (hourly scan) vs the restored rank, on the same RTH-grid 1H basket tapes,
SMH daily rows and genome daily bars; the vendored dcg_rule_1h.mjs scores both (byte-identical), its fires
given to the old scan through its own score_1h.

Per case: 30-41 basket names with 120-400 RTH 1H bars (some signal bars nudged across the rule's range/ATR,
WaveTrend-gap and SMH-trend conditions), a scan clock at :26 (the latest bar closed), books holding names
with a precise entry time (the old law counts bars strictly after it — the port counts from the fill),
surviving pending buys. Compared: the staged pending (buys, sells, exit dates)."""
import json
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.feedlib import dcg
from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, trading_dates, write_receipt
from .dcg_frame import _walk

F = femto_module("rule_1h_cyan_raw")
ET = ZoneInfo("America/New_York")
N_CASES = 24

OLD = r'''
from datetime import datetime as _DT, timezone
import sleeve_core as core
import rule_1h_cyan_raw as O


class FakeDT(_DT):
    NOW = None

    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz is not None else cls.NOW


O.datetime = FakeDT
out = []
for c in PAYLOAD["cases"]:
    FakeDT.NOW = _DT.fromisoformat(c["now"])
    core.et_now = lambda c=c: _DT.fromisoformat(c["now"])
    h1 = c["h1"]
    O.load_1h_cache = lambda h1=h1: {s: [dict(b) for b in bl] for s, bl in h1.items()}
    O.smh_daily_bars = lambda: []
    O.score_1h = lambda symbols_data, smh_daily, dry_run=False, c=c: c["fires"]
    daily = c["daily"]
    core.load_cache = lambda path, daily=daily: {"bars": daily}
    STATE = {"book": c["book"], "pending": c["pending"], "stats": {}}
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    O.mode_rank(c["now"], dry_run=False, no_fetch=True)
    out.append({k: STATE["pending"].get(k) for k in ("buys", "sells", "exit_dates")})
print(json.dumps(out))
'''


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tape(rnd, sessions, px):
    out = []
    for d in sessions:
        for h in range(9, 16):
            t = datetime.fromisoformat(d).replace(hour=h, tzinfo=ET).astimezone(timezone.utc).timestamp()
            o = px * (1 + rnd.gauss(0, 0.002))
            c = max(0.5, px * (1 + rnd.gauss(0.0003, 0.008)))
            out.append({"t": t, "o": round(o, 4), "h": round(max(o, c) * (1 + abs(rnd.gauss(0, 0.004))), 4),
                        "l": round(min(o, c) * (1 - abs(rnd.gauss(0, 0.004))), 4), "c": round(c, 4),
                        "v": float(int(rnd.uniform(2e4, 3e5)))})
            px = c
    return out


def run():
    rnd = random.Random(19)
    cases, news = [], []
    for k in range(N_CASES):
        days = trading_dates("2026-03-02", 120)
        today = days[-1]
        scan_h = rnd.randint(10, 15)
        now = datetime.fromisoformat(today).replace(hour=scan_h, minute=26, tzinfo=ET)
        basket = ["B%02d" % j for j in range(rnd.randint(30, 41))]
        h1, daily = {}, {}
        for s in basket:
            bl = _tape(rnd, days[-rnd.randint(18, 58):], rnd.uniform(3, 150))
            h1[s] = [b for b in bl if b["t"] + 3600 <= now.timestamp()]
            daily[s] = _walk(rnd, days, h1[s][-1]["c"], 0.0, 0.02)
        smh = _walk(rnd, trading_dates("2024-12-02", 450), 250.0, 0.0006, 0.015)
        smh = [r for r in smh if r[0] <= today]
        fires = dcg.score_1h(h1, smh)
        for s, fl in fires.items():                        # nudge some latest-bar fires across the rule
            bl = h1[s]
            last = _iso(bl[-1]["t"])
            if rnd.random() < 0.5 and not any(f["t"] == last for f in fl):
                fl.append({"t": last, "rangeatr": None, "wtgap": None, "smhUp": None})
            for f in fl:
                if f["t"] == last and rnd.random() < 0.8:
                    f.update(rangeatr=round(rnd.uniform(1.5, 3.5), 4), wtgap=round(rnd.uniform(3, 12), 4),
                             smhUp=rnd.choice((1, 1, 0, None)))
        book = {}
        for s in rnd.sample(basket, rnd.randint(0, 8)):
            bl = h1[s]
            et = bl[-rnd.randint(2, 30)]["t"] + rnd.choice((0, 240, 1800))
            book[s] = {"qty": 10.0, "entry_px": 20.0, "entry_date": datetime.fromtimestamp(et, tz=ET).date().isoformat(),
                       "entry_time": _iso(et), "exit_due_date": "2099-01-01"}
        pend = {"buys": rnd.sample(basket, rnd.randint(0, 3)), "sells": [], "exit_dates": {}}
        old_daily = {s: [list(r) for r in rows] for s, rows in daily.items()}
        cases.append({"now": now.isoformat(), "h1": {s: [dict(b, t=_iso(b["t"])) for b in bl] for s, bl in h1.items()},
                      "fires": fires, "daily": old_daily, "book": book, "pending": pend})
        news.append((h1, daily))
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"staged_buys": 0, "staged_sells": 0, "new_buys": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, (h1, daily), o) in enumerate(zip(cases, news, old)):
        ebars = {s: [{"t": datetime.fromisoformat(r[0]).replace(hour=4, tzinfo=timezone.utc).timestamp(), "o": r[1],
                      "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in rows] for s, rows in daily.items()}
        state = {s: {"position": dict(p, opened_at=datetime.fromisoformat(p["entry_time"].replace("Z", "+00:00"))
                                      .timestamp())} for s, p in c["book"].items()}
        ctx = fc.Context(now=datetime.fromisoformat(c["now"]).timestamp(), session=c["now"][:10], equity=100_000.0,
                         extra={"sleeve_state": state, "meta": {"pending": c["pending"]}, "bars_1h": h1,
                                "fires_1h": c["fires"]})
        meta = F.next_meta(ebars, {}, ctx, [])
        p = meta.get("pending") or {}
        cmp("pending", ci, o, {k: p.get(k) for k in ("buys", "sells", "exit_dates")})
        counts["staged_buys"] += len(o.get("buys") or [])
        counts["staged_sells"] += len(o.get("sells") or [])
        counts["new_buys"] += len(set(o.get("buys") or []) - set(c["pending"]["buys"]))
    res = {"sleeve": "rule_1h_cyan_raw", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("rule_1h_cyan_raw", res)
    return res
