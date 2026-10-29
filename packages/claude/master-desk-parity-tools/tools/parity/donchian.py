"""donchian: old donchian_sleeve.py vs the vendored femto port (with the master-desk restorations).

Corpus: 60 deterministic daily paths x every evaluation day.
  entry   old detect_breakout(bars[-100:])            == femto entry_signal(bars[-100:])
  size    old size_qty(equity, px)                    == femto size_qty(equity, px)
  exits   old daily passes (update_trail -> check_exit, persisted trail, 100-bar windows) vs the femto
          sleeve's signal() on the same window and position: same first exit day and same reason."""
import os
from datetime import datetime, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("donchian")

WINDOW = 100          # the old pass's bar window (fetch_daily_bars limit)
FEMTO_BARS = 160      # the adapter hands the port 160 bars so trail_level can rebuild every past 100-bar window
N_SEEDS = 60

OLD = r'''
import donchian_sleeve as O
def iso(rows):
    return [{"t": r["d"], "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]
W = PAYLOAD["window"]
out = []
for case in PAYLOAD["cases"]:
    rows = case["rows"]
    ent = [bool(O.detect_breakout(iso(rows[max(0, i + 1 - W):i + 1]))) for i in range(30, len(rows))]
    size = [O.size_qty(eq, px) for eq, px in case["sizes"]]
    exits = []
    for e in case["entries"]:
        fill, entry_date = rows[e]["o"], rows[e]["d"]
        pos = {"qty": 10, "entry_px": round(fill, 2), "entry_date": entry_date, "bars_held": 0,
               "trail": round(fill * 0.96, 2)}
        got = None
        for d in range(e + 1, min(len(rows), e + 40)):
            w = iso(rows[max(0, d - W):d])
            pos["bars_held"] = sum(1 for b in w if str(b["t"]) > entry_date)
            O.update_trail(pos, w)
            r = O.check_exit(pos, w)
            if r:
                got = [rows[d]["d"], r]
                break
        exits.append(got)
    out.append({"entry": ent, "size": size, "exits": exits})
print(json.dumps(out))
'''


def _femto_exit(window_rows, pos, session):
    ctx = fc.Context(now=datetime.fromisoformat(session).replace(hour=14, minute=32, tzinfo=timezone.utc).timestamp(),
                     session=session, equity=100_000.0,
                     extra={"sleeve_state": {"SYM": {"position": pos}}, "universe": ["SYM"]})
    out = [i for i in F.signal({"SYM": as_epoch(window_rows)}, {"SYM": pos["qty"]}, ctx) if i.kind == "exit"]
    if not out:
        return None
    r = out[0].reason
    for key, name in (("channel=True", "donchian_exit"), ("trail_hit=True", "atr_trail"), ("time_due=True", "time_stop")):
        if key in r:
            return name
    return "unknown"


def _femto_entry_qty(eq, px):
    """the qty the femto sleeve's own signal() emits for a fresh breakout at close px with equity eq."""
    rows = [{"d": f"2025-01-{k + 2:02d}" if k < 29 else f"2025-02-{k - 26:02d}", "o": px * 0.9, "h": px * 0.9,
             "l": px * 0.88, "c": px * 0.9, "v": 1e6} for k in range(30)]
    rows[-1] = dict(rows[-1], c=px, h=px, o=px * 0.95)
    ctx = fc.Context(now=1.8e9, session="2025-03-10", equity=float(eq), extra={"sleeve_state": {}, "universe": ["SYM"]})
    out = [i for i in F.signal({"SYM": as_epoch(rows)}, {}, ctx) if i.kind == "enter"]
    return out[0].qty_hint if out else 0


def run():
    cases = []
    for seed in range(N_SEEDS):
        rows = walk(seed, 420, start_px=20 + seed, vol=0.02 + (seed % 5) * 0.006)
        sizes = [[50_000 + 1000 * seed, rows[i]["c"]] for i in range(30, len(rows), 7)]
        cases.append({"rows": rows, "sizes": sizes, "entries": []})
    # entries: the session after each old-detected breakout (computed by the femto side; both sides then walk
    # the same entry list — entry detection itself is compared separately)
    for c in cases:
        rows = c["rows"]
        c["entries"] = [i + 1 for i in range(30, len(rows) - 1)
                        if F.entry_signal(as_epoch(rows[max(0, i + 1 - WINDOW):i + 1]))][:12]
    old = old_run(OLD, {"window": WINDOW, "cases": cases})
    n = same = 0
    diffs = []
    for seed, (c, o) in enumerate(zip(cases, old)):
        rows = c["rows"]
        new_ent = [bool(F.entry_signal(as_epoch(rows[max(0, i + 1 - WINDOW):i + 1]))) for i in range(30, len(rows))]
        for k, (a, b) in enumerate(zip(o["entry"], new_ent)):
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "entry", "seed": seed, "day": rows[30 + k]["d"], "old": a, "new": b})
        for (eq, px), a in zip(c["sizes"], o["size"]):
            b = _femto_entry_qty(eq, px)
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "size", "seed": seed, "eq": eq, "px": px, "old": a, "new": b})
        for e, a in zip(c["entries"], o["exits"]):
            fill, entry_date = rows[e]["o"], rows[e]["d"]
            b = None
            for d in range(e + 1, min(len(rows), e + 40)):
                # the adapter hands the sleeve entry_px = the book's (unrounded) average fill, as the old
                # reconcile_fills initialised the trail from the unrounded fill_px
                r = _femto_exit(rows[max(0, d - FEMTO_BARS):d], {"qty": 10, "entry_px": fill,
                                                             "entry_date": entry_date}, rows[d]["d"])
                if r:
                    b = [rows[d]["d"], r]
                    break
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "exit", "seed": seed, "entry": entry_date, "old": a, "new": b})
    res = {"sleeve": "donchian", "cases": n, "identical": same, "diffs": diffs[:40], "n_diffs": len(diffs)}
    write_receipt("donchian" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
