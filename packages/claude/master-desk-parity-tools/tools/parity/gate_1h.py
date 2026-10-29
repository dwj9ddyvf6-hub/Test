"""gate_1h: old gate_1h_sleeve.py mode_scan vs the restored port (scan) on the same daily + RTH 1H tape.

The OLD scan computes its daily gated events itself (the vendored research frame on bars before today) and
walks its own 1H cache; the port reads the genome job's last-close rows (here: the same frame through the
leader feed) and the adapter's RTH-grid 1H bars. Compared: the staged pending (buys, sells, exit dates,
entry bars), last_event and last_entry_bar, across random books (entry bars 5-40 bars back), prior
entry bars (the 20-bar de-overlap) and prior events."""
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.feedlib import leader
from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt
from .leader_d import _path

F = femto_module("gate_1h")
ET = ZoneInfo("America/New_York")
N_CASES = 30

OLD = r'''
from datetime import datetime
from zoneinfo import ZoneInfo
import sleeve_core as core
import gate_1h_sleeve as O
ET = ZoneInfo("America/New_York")
out = []
for c in PAYLOAD["cases"]:
    dbars = {s: [list(r) for r in rows] for s, rows in c["daily"].items()}
    h1 = {s: [dict(b) for b in bl] for s, bl in c["h1"].items()}
    now = datetime.fromisoformat(c["now"])
    core.et_now = lambda now=now: now
    O.core.et_now = core.et_now
    core.load_cache = lambda path, dbars=dbars, h1=h1: {"bars": h1} if "1h" in path.lower() else {"bars": dbars}
    O.core.load_cache = core.load_cache
    O.basket_syms = lambda c=c: list(c["basket"])
    STATE = {"book": c["book"], "pending": c["pending"], "last_event": c["last_event"],
             "last_entry_bar": c["last_entry_bar"], "stats": {}}
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    O.mode_scan(c["today"], dry_run=False, no_fetch=True)
    out.append({"pending": STATE["pending"], "last_event": STATE["last_event"],
                "last_entry_bar": STATE["last_entry_bar"]})
print(json.dumps(out))
'''


def _h1_from_daily(rnd, rows, days_back=60):
    """RTH clock-hour bars (09..15 ET starts) per session shaped around each daily bar."""
    out = []
    for r in rows[-days_back:]:
        d = date.fromisoformat(r[0])
        px = r[1]
        for h in range(9, 16):
            t = datetime(d.year, d.month, d.day, h, 0, tzinfo=ET)
            c = r[4] if h == 15 else px * (1 + rnd.gauss(0, 0.006))
            hi, lo = max(px, c) * 1.002, min(px, c) * 0.998
            out.append({"t": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": round(px, 4),
                        "h": round(hi, 4), "l": round(lo, 4), "c": round(c, 4), "v": 1000.0})
            px = c
    return out


def run():
    rnd = random.Random(53)
    cases = []
    for k in range(N_CASES):
        n = rnd.randint(380, 600)
        dates = trading_dates("2024-01-02", n + 1)
        today = dates[-1]
        hist = dates[:-1]
        basket = ["B%02d" % j for j in range(rnd.randint(20, 41))]
        daily = {s: _path(rnd, hist, rnd.uniform(5, 300), rnd.uniform(-0.001, 0.0015)) for s in basket}
        h1 = {}
        for s in basket:
            bl = _h1_from_daily(rnd, daily[s])
            hh = rnd.choice((10, 11, 13, 15))      # today's completed bars up to the scan time
            t0 = datetime.fromisoformat(today).replace(hour=9, tzinfo=ET)
            for h in range(9, hh):
                t = t0.replace(hour=h)
                px = bl[-1]["c"]
                bl.append({"t": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": px, "h": px * 1.003,
                           "l": px * 0.997, "c": px * (1 + rnd.gauss(0, 0.004)), "v": 1000.0})
            h1[s] = bl
        scan_h = rnd.choice((10, 11, 12, 14, 15))
        now = datetime.fromisoformat(today).replace(hour=scan_h, minute=16, tzinfo=ET)
        # completed bars only (the port's hub view): start + 65 min <= now (old fetch rule) ~ start <= now - 1h
        h1 = {s: [b for b in bl if datetime.fromisoformat(b["t"].replace("Z", "+00:00")).timestamp() + 3900
                  <= now.timestamp()] for s, bl in h1.items()}
        book = {}
        for s in rnd.sample(basket, rnd.randint(0, 5)):
            bl = h1[s]
            if len(bl) > 45:
                book[s] = {"qty": 10.0, "entry_px": 50.0, "entry_date": hist[-3], "exit_due_date": "2099-01-01",
                           "entry_bar_t": bl[-rnd.randint(5, 40)]["t"]}
        last_event = {s: hist[-1] for s in rnd.sample(basket, rnd.randint(0, 3))}
        last_entry_bar = {}
        for s in rnd.sample(basket, rnd.randint(0, 6)):
            bl = h1[s]
            if len(bl) > 30:
                last_entry_bar[s] = bl[-rnd.randint(1, 30)]["t"]
        pending = {"buys": rnd.sample(basket, rnd.randint(0, 2)), "sells": [], "exit_dates": {}, "entry_bars": {}}
        cases.append({"daily": daily, "h1": h1, "today": today, "now": now.isoformat(), "basket": basket,
                      "book": book, "last_event": last_event, "last_entry_bar": last_entry_bar, "pending": pending})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"staged_buys": 0, "staged_sells": 0, "signals": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    def ep(t):
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()

    def iso(t):
        return datetime.fromtimestamp(float(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for ci, (c, o) in enumerate(zip(cases, old)):
        rows = {}
        for s, bl in c["daily"].items():
            r = leader.latest(as_epoch([dict(d=x[0], o=x[1], h=x[2], l=x[3], c=x[4], v=x[5]) for x in bl]))
            if r:
                rows[s] = r
        h1 = {s: [dict(b, t=ep(b["t"])) for b in bl] for s, bl in c["h1"].items()}
        state = {s: {"position": dict(p, entry_bar_t=ep(p["entry_bar_t"]))} for s, p in c["book"].items()}
        meta = {"pending": c["pending"], "last_event": c["last_event"],
                "last_entry_bar": {s: ep(t) for s, t in c["last_entry_bar"].items()}}
        ctx = fc.Context(now=datetime.fromisoformat(c["now"]).timestamp(), session=c["today"], equity=100_000.0,
                         extra={"sleeve_state": state, "bars_1h": h1})
        pending, last_ev, last_eb, signals = F.scan(ctx, meta, rows, c["basket"])
        pend_new = dict(pending, entry_bars={s: iso(t) for s, t in pending["entry_bars"].items()})
        cmp("pending", ci, o["pending"], pend_new)
        cmp("last_event", ci, o["last_event"], last_ev)
        cmp("last_entry_bar", ci, o["last_entry_bar"], {s: iso(t) for s, t in last_eb.items()})
        counts["staged_buys"] += len(o["pending"].get("buys") or [])
        counts["staged_sells"] += len(o["pending"].get("sells") or [])
        counts["signals"] += len(signals)
    res = {"sleeve": "gate_1h", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("gate_1h", res)
    return res
