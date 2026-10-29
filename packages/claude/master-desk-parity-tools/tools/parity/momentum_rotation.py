"""momentum_rotation: old momentum_rotation_sleeve.py vs the vendored femto port (master-desk restorations).

The old rebalance DECISION (maybe_rebalance with the old module's compute_ranks / rebalance_due / constants,
in the old order: exits rank > 10, unranked held, then top-5 entries with the 5-slot capacity and the 20%
weight) on random 41-name universes, random holdings (some unrankable), random equity; desk gates out of scope.
Compared: rebalance due?, the exit set, the ordered entry list with quantities."""
import os
import random
from datetime import datetime, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("momentum_rotation")
N_CASES = 600

OLD = r'''
import pandas as pd
import momentum_rotation_sleeve as O
def frame(rows):
    df = pd.DataFrame([(pd.Timestamp(r["d"]), r["o"], r["h"], r["l"], r["c"], r["v"]) for r in rows],
                      columns=["date", "o", "h", "l", "c", "v"]).set_index("date")
    return df
out = []
for case in PAYLOAD["cases"]:
    state = {}
    if case["last_rebalance"]:
        state["last_rebalance"] = case["last_rebalance"]
    due = O.rebalance_due(state, case["today"])
    if not due:
        out.append({"due": False}); continue
    bars_map = {}
    for sym, rows in case["bars"].items():
        df = frame(rows).tail(O.BARS_LIMIT)
        if len(df) < O.WARMUP_BARS + 1:
            continue
        bars_map[sym] = df
    ranks = O.compute_ranks(bars_map)
    held = case["held"]
    exits = []
    for sym in case["order"]:
        if sym not in held:
            continue
        r = ranks.get(sym)
        if r is None:
            continue
        if r[0] > O.SELL_RANK_CUTOFF:
            exits.append(sym)
    top = sorted(ranks.items(), key=lambda kv: kv[1][0])[:O.TOP_HOLD]
    committed = len(held) + len(case["pending"])
    entries = []
    for sym, (rank, mom) in top:
        if sym in held or sym in exits:
            continue
        if committed >= O.TOP_HOLD:
            break
        if sym in case["pending"]:
            continue
        df = bars_map.get(sym)
        ref_px = float(df["c"].iloc[-1])
        qty = int((case["equity"] * O.TARGET_WEIGHT) / ref_px) if ref_px > 0 else 0
        if qty <= 0:
            continue
        entries.append([sym, qty])
        committed += 1
    out.append({"due": True, "ranked": bool(ranks), "exits": sorted(exits), "entries": entries})
print(json.dumps(out))
'''


def _femto(case):
    st = {}
    for s in case["held"]:
        st[s] = {"position": {"qty": 10, "entry_px": 10.0, "entry_date": "2025-01-02"}}
    for s in case["pending"]:
        st.setdefault(s, {})["pending_entry"] = {"qty": 5}
    ctx = fc.Context(now=datetime.fromisoformat(case["today"]).replace(hour=13, minute=35, tzinfo=timezone.utc).timestamp(),
                     session=case["today"], equity=case["equity"],
                     extra={"sleeve_state": st, "last_rebalance": case["last_rebalance"], "universe": case["order"]})
    bars = {s: as_epoch(rows[-100:]) for s, rows in case["bars"].items()}
    if not F.rebalance_due(case["last_rebalance"], case["today"]):
        return {"due": False}
    out = F.signal(bars, {}, ctx)
    b = {s: bl for s, bl in bars.items() if bl and len(bl) >= F.WARMUP_BARS + 1}
    return {"due": True, "ranked": bool(F.compute_ranks(b)),
            "exits": sorted(i.symbol for i in out if i.kind == "exit"),
            "entries": [[i.symbol, i.qty_hint] for i in out if i.kind == "enter"]}


def run():
    rnd = random.Random(11)
    cases = []
    for k in range(N_CASES):
        n = rnd.randint(8, 41)
        syms = [f"S{j:02d}" for j in range(n)]
        bars = {}
        for j, s in enumerate(syms):
            length = rnd.choice((40, 60, 66, 70, 100, 140))
            rows = walk(k * 100 + j, 140, start_px=rnd.uniform(5, 300), vol=rnd.uniform(0.01, 0.05),
                        drift=rnd.uniform(-0.003, 0.004))
            bars[s] = rows[-length:]
        held = rnd.sample(syms, rnd.randint(0, min(7, n)))
        rest = [s for s in syms if s not in held]
        pending = rnd.sample(rest, min(len(rest), rnd.randint(0, 2)))
        today = bars[syms[0]][-1]["d"]
        last = rnd.choice((None, "2025-01-01", today))
        cases.append({"bars": bars, "order": syms, "held": held, "pending": pending, "today": today,
                      "last_rebalance": last, "equity": rnd.choice((25_000.0, 100_000.0, 250_000.0))})
    old = old_run(OLD, {"cases": cases})
    n = same = 0
    diffs = []
    for k, (c, a) in enumerate(zip(cases, old)):
        b = _femto(c)
        n += 1
        same += a == b
        if a != b:
            diffs.append({"case": k, "old": a, "new": b})
    res = {"sleeve": "momentum_rotation", "cases": n, "identical": same, "diffs": diffs[:30], "n_diffs": len(diffs)}
    write_receipt("momentum_rotation" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
