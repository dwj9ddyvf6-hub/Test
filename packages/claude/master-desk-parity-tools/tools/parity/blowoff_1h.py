"""blowoff_1h: old blowoff_1h_sleeve.py mode_scan (TRADING_ENABLED = True: the forward test) vs the port's scan.

A synthetic basket of 1H tapes on the clock grid (some names with ETH bars, some with a still-forming bar
from the scan hour) — random walks with volume-backed rally bursts mid-tape and into the last bars so the
R4 blowoff rising edges fire. The OLD scan filters its cache through rth_1h_bars and _drop_forming_1h (its
clock patched to the scan time); the port reads the adapter's RTH-grid trim and its own 65-minute rule.
Compared per case: the staged pending (buys after the capacity rule merged with surviving buys, sells
at >= 20 RTH bars after the entry bar, the +4-day exit backstop, signal bars), last_signal_bar (the
20-bar de-overlap anchor and the recorded-signal exclusion) and the signals, across random books, entry
bars, prior signal bars (real edges, arbitrary bars, off-tape times) and surviving pending."""
import os
import random
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from desk.feedlib import blowoff
from desk.sleeves.families.femto import _trim
from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, trading_dates, write_receipt

F = femto_module("blowoff_1h")
ET = ZoneInfo("America/New_York")
N_CASES = 40

OLD = r'''
from datetime import datetime as _DT, timezone
import sleeve_core as core
import blowoff_1h_sleeve as O
O.TRADING_ENABLED = True


class FakeDT(_DT):
    NOW = None

    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz is not None else cls.NOW.replace(tzinfo=None)


O.datetime = FakeDT
out = []
for c in PAYLOAD["cases"]:
    h1 = {s: [dict(b) for b in bl] for s, bl in c["h1"].items()}
    now = _DT.fromisoformat(c["now"])
    FakeDT.NOW = now
    core.et_now = lambda now=now: now
    core.load_cache = lambda path, h1=h1: {"bars": h1}
    O.basket_syms = lambda c=c: list(c["basket"])
    STATE = {"book": c["book"], "pending": c["pending"], "last_signal_bar": c["last_signal_bar"], "stats": {}}
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    res = O.mode_scan(c["today"], dry_run=False, no_fetch=True)
    out.append({"pending": STATE["pending"], "last_signal_bar": STATE["last_signal_bar"],
                "signals": res["signals"]})
print(json.dumps(out))
'''


def _iso(t):
    return datetime.fromtimestamp(float(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ep(t):
    return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()


def _tape(rnd, slots, n_rth, px):
    """1H bars over (session, hour) slots; RTH slot index k counts 09..15 ET bar starts."""
    bursts = set()
    for _ in range(rnd.randint(1, 4)):
        k = rnd.randint(150, max(151, n_rth - 12))
        bursts.update(range(k - rnd.randint(2, 7), k + 1))
    if rnd.random() < 0.65:                      # a rally into the last closed bars: the scan's fresh edge
        end = n_rth - rnd.randint(0, 3)
        bursts.update(range(end - rnd.randint(2, 8), end))
    out, k = [], 0
    for d, h in slots:
        rth = 9 <= h <= 15
        b = rth and k in bursts
        drift = rnd.uniform(0.004, 0.012) if b else rnd.uniform(-0.0018, 0.0012)
        sd = 0.006 if b else 0.004
        o = px * (1 + rnd.gauss(0, sd / 4))
        c = max(0.5, px * (1 + rnd.gauss(drift, sd)))
        v = rnd.uniform(2e4, 2e5) * (rnd.uniform(2.5, 6) if b else 1) * (1 if rth else 0.15)
        if rnd.random() < 0.01:
            v = 0.0
        t = datetime.fromisoformat(d).replace(hour=h, tzinfo=ET).astimezone(timezone.utc)
        out.append({"t": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "o": round(o, 4), "h": round(max(o, c) * 1.002, 4),
                    "l": round(min(o, c) * 0.998, 4), "c": round(c, 4), "v": float(int(v))})
        px = c
        k += rth
    return out


def run():
    rnd = random.Random(61)
    cases = []
    for ci in range(N_CASES):
        days = trading_dates(rnd.choice(("2025-01-06", "2025-06-02", "2025-10-20", "2026-02-02")), 52)
        today, hist = days[-1], days[:-1]
        scan_h = rnd.randint(10, 15)
        now = datetime.fromisoformat(today).replace(hour=scan_h, minute=rnd.randint(10, 15), tzinfo=ET)
        basket = ["H%02d" % j for j in range(rnd.randint(20, 42))]
        h1 = {}
        for s in basket:
            eth = rnd.random() < 0.3
            hours = (list(range(4, 9)) if eth else []) + list(range(9, 16)) + (list(range(16, 20)) if eth else [])
            slots = [(d, h) for d in hist[-rnd.randint(25, 51):] for h in hours]
            slots += [(today, h) for h in range(4 if eth else 9, scan_h)]
            if rnd.random() < 0.2:                # a still-forming scan-hour bar (hand-loaded cache)
                slots.append((today, scan_h))
            n_rth = sum(1 for d, h in slots if 9 <= h <= 15 and not (d == today and h == scan_h))
            h1[s] = _tape(rnd, slots, n_rth, rnd.uniform(4, 300))
        nts = now.timestamp()
        grid = {s: _trim([dict(b, t=_ep(b["t"])) for b in bl], nts, rth_grid=True) for s, bl in h1.items()}
        closed = {s: [b for b in bl if b["t"] + 3900 <= nts] for s, bl in grid.items()}
        book = {}
        for s in rnd.sample(basket, rnd.randint(0, 6)):
            bl = closed[s]
            if len(bl) < 45:
                continue
            k = rnd.choice((rnd.randint(5, 40), 20, 21, 22))
            et = bl[-k]["t"] + (1800 if rnd.random() < 0.2 else 0)   # off-grid stamps exercise the >= rule
            book[s] = {"qty": 10.0, "entry_px": 50.0, "entry_date": hist[-3], "exit_due_date": "2099-01-01",
                       "entry_bar_t": _iso(et) if rnd.random() < 0.92 else None}
        last_sb = {}
        for s in rnd.sample(basket, rnd.randint(0, 12)):
            bl = closed[s]
            if len(bl) < 160:
                continue
            edges = blowoff.rising_edges([b["c"] for b in bl], [b["v"] for b in bl])
            r = rnd.random()
            if edges and r < 0.45:                     # a real earlier (or the latest) edge as the anchor
                last_sb[s] = _iso(bl[rnd.choice(edges[-3:])]["t"])
            elif r < 0.8:
                last_sb[s] = _iso(bl[-rnd.randint(1, 30)]["t"])
            else:
                last_sb[s] = _iso(bl[0]["t"] - 86400 * 30)   # off the tape: no anchor index
        pend_buys = rnd.sample(basket, rnd.randint(0, 4))
        pending = {"buys": pend_buys, "sells": rnd.sample(basket, rnd.randint(0, 2)),
                   "exit_dates": {s: "2099-01-0%d" % rnd.randint(1, 9) for s in pend_buys[:rnd.randint(0, 2)]},
                   "signal_bars": {s: _iso(closed[s][-rnd.randint(1, 9)]["t"]) for s in pend_buys[:1] if closed[s]}}
        cases.append({"h1": h1, "today": today, "now": now.isoformat(), "basket": basket, "book": book,
                      "last_signal_bar": last_sb, "pending": pending})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"signals": 0, "staged_buys": 0, "staged_sells": 0, "capacity_cases": 0, "forming_names": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        nts = datetime.fromisoformat(c["now"]).timestamp()
        h1 = {s: _trim([dict(b, t=_ep(b["t"])) for b in bl], nts, rth_grid=True) for s, bl in c["h1"].items()}
        counts["forming_names"] += sum(1 for bl in h1.values() if bl and bl[-1]["t"] + 3900 > nts)
        state = {s: {"position": dict(p, entry_bar_t=_ep(p["entry_bar_t"]) if p["entry_bar_t"] else None)}
                 for s, p in c["book"].items()}
        p0 = c["pending"]
        meta = {"pending": dict(p0, signal_bars={s: _ep(t) for s, t in p0["signal_bars"].items()}),
                "last_signal_bar": {s: _ep(t) for s, t in c["last_signal_bar"].items()}}
        ctx = fc.Context(now=nts, session=c["today"], equity=100_000.0, extra={"sleeve_state": state, "bars_1h": h1})
        pending, last_sb, signals = F.scan(ctx, meta, c["basket"])
        cmp("pending", ci, o["pending"], dict(pending, signal_bars={s: _iso(t) for s, t in pending["signal_bars"].items()}))
        cmp("last_signal_bar", ci, o["last_signal_bar"], {s: _iso(t) for s, t in last_sb.items()})
        cmp("signals", ci, o["signals"], [s for s, _t in signals])
        counts["signals"] += len(o["signals"])
        counts["staged_buys"] += len(o["pending"].get("buys") or [])
        counts["staged_sells"] += len(o["pending"].get("sells") or [])
        fresh = [s for s in o["signals"] if s not in c["book"]]
        counts["capacity_cases"] += len(fresh) > len(set(o["pending"]["buys"]) - set(p0["buys"]))
    res = {"sleeve": "blowoff_1h", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("blowoff_1h", res)
    return res
