"""red_day_reversal: old red_day_reversal_sleeve.py vs the vendored femto port (master-desk restorations).

  entry   old maybe_enter order (detect_washout -> size_shares -> in_rth) == femto entry intent
          (qty, limit price = the last close); earnings gate held clear on both sides
  exits   old exit_due(pos{target_px, stop_px, entry_ts from the fill}, now, mark) == femto exit_due(...)
          over a grid of marks and elapsed times
Corpus: 50 paths x every day (entries at a 10:05 ET pass); 40k exit probes."""
import os
import random
from datetime import datetime, timedelta, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("red_day_reversal")
N_SEEDS = 50

OLD = r'''
from datetime import datetime, timezone
import red_day_reversal_sleeve as O
def bars(rows):
    return [{"t": r["d"], "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]
out = {"entries": [], "exits": []}
for case in PAYLOAD["cases"]:
    rows, eq = case["rows"], case["equity"]
    ents = []
    for i in range(205, len(rows)):
        b = bars(rows[max(0, i + 1 - 220):i + 1])
        now = datetime.fromtimestamp(case["now"][i - 205], tz=timezone.utc)
        sig, day_pct, rsi, above = O.detect_washout(b)
        if not sig:
            ents.append(None); continue
        qty = O.size_shares(eq, float(b[-1]["c"]))
        if qty <= 0 or not O.in_rth(now):
            ents.append(None); continue
        ents.append([qty, round(float(b[-1]["c"]), 2)])
    out["entries"].append(ents)
for p in PAYLOAD["probes"]:
    fill, opened, now, mark = p
    pos = {"target_px": round(fill * (1 + O.PROFIT_TARGET_PCT), 2), "stop_px": round(fill * (1 - O.STOP_PCT), 2),
           "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat()}
    r = O.exit_due(pos, datetime.fromtimestamp(now, tz=timezone.utc), mark)
    out["exits"].append(list(r))
print(json.dumps(out))
'''


def _femto_entry(window, now, session):
    ctx = fc.Context(now=now, session=session, equity=100_000.0, extra={"sleeve_state": {}, "universe": ["SYM"]})
    out = [i for i in F.signal({"SYM": as_epoch(window)}, {}, ctx) if i.kind == "enter"]
    return [out[0].qty_hint, out[0].order["limit_price"]] if out else None


def run():
    rnd = random.Random(7)
    cases = []
    for seed in range(N_SEEDS):
        rows = walk(3000 + seed, 420, start_px=40 + seed, vol=0.03 + (seed % 3) * 0.01, drift=0.0012, jumps=0.05)
        nows = []
        for i in range(205, len(rows)):
            d = datetime.fromisoformat(rows[min(i + 1, len(rows) - 1)]["d"])
            hh = rnd.choice((13, 14, 15, 19, 20, 21))          # mix of in-RTH and after-hours passes (UTC)
            nows.append(d.replace(hour=hh, minute=5, tzinfo=timezone.utc).timestamp())
        cases.append({"rows": rows, "equity": 100_000.0, "now": nows})
    probes = []
    base = datetime(2026, 3, 2, 15, tzinfo=timezone.utc).timestamp()
    for _ in range(40_000):
        fill = round(rnd.uniform(5, 500), 4)
        opened = base + rnd.randint(0, 200) * 3600
        now = opened + rnd.randint(0, 120) * 3600 + rnd.randint(0, 3599)
        mark = None if rnd.random() < 0.15 else round(fill * rnd.uniform(0.95, 1.06), 4)
        probes.append([fill, opened, now, mark])
    old = old_run(OLD, {"cases": cases, "probes": probes})
    n = same = 0
    diffs = []
    for seed, (c, oe) in enumerate(zip(cases, old["entries"])):
        rows = c["rows"]
        for k, a in enumerate(oe):
            i = 205 + k
            b = _femto_entry(rows[max(0, i + 1 - 220):i + 1], c["now"][k], rows[min(i + 1, len(rows) - 1)]["d"])
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "entry", "seed": seed, "day": rows[i]["d"], "old": a, "new": b})
    for p, a in zip(probes, old["exits"]):
        fill, opened, now, mark = p
        b = list(F.exit_due({"entry_px": fill, "opened_at": opened}, now, mark))
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": "exit", "probe": p, "old": a, "new": b})
    res = {"sleeve": "red_day_reversal", "cases": n, "identical": same, "diffs": diffs[:40], "n_diffs": len(diffs)}
    write_receipt("red_day_reversal" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
