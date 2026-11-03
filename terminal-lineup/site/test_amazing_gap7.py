#!/usr/bin/env python3
"""Regression blocker: GAP-7 (2026-11-02 night, Phase Gap7).

Two of the three unbuilt GrokBot attractions had an honest series in
the desk's own data and are built in publish_desk.build_attractions:

1. Desk vs small caps: IWM daily closes are in the same board price
   panel that already carries SPY and QQQ, so the small-cap line is
   computed by the same rule over the same capital window.
2. Closed trades log: the desk dispatcher's journal (both
   generations, dispatcher.jsonl.1 then dispatcher.jsonl) carries
   fill events with sleeve, symbol, side, qty, price and timestamp.
   A closed trade is listed only when its opening fills are also in
   the journal record (FIFO pairing); the count of closing fills
   whose openings are not on record is carried, never hidden.

The third attraction, an Opportunity Ranker desk surface, stays
unbuilt: the feed carries no ranked list (its setups source is
disabled by the owner's 2026-10-25 ruling) and no strategy row
carries a rank or score. This test pins that absence so a future
ranked series, if one ever lands in the feed, is a deliberate add.

Every figure is recomputed here from the source files, not copied
from the build output. Run: python3 test_amazing_gap7.py
Exit 0 = pass.
"""
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE.parents[1] / "morgue" / "data_cache" / "board_bt_bars.json"
JOURNALS = (HERE.parents[1] / "muse-desk-v3" / "state" / "dispatcher.jsonl.1",
            HERE.parents[1] / "muse-desk-v3" / "state" / "dispatcher.jsonl")
ATTR = HERE / "desk" / "attractions.json"
PAGE = HERE / "desk" / "index.html"
SRC = (HERE / "publish_desk.py").read_text(encoding="utf-8")

misses = []


def check(cond, msg):
    if not cond:
        misses.append(msg)


feed = json.loads((HERE / "desk" / "terminal_feed.json").read_text(
    encoding="utf-8"))
start_date = str((feed.get("evidence_packet") or {}).get("period", {})
                 .get("start") or "")[:10]
attr = json.loads(ATTR.read_text(encoding="utf-8"))
page = PAGE.read_text(encoding="utf-8")
panel = json.loads(PANEL.read_text(encoding="utf-8"))

# --- 1. small caps (IWM) recomputed from the panel -----------------
rows = [r for r in panel.get("IWM") or [] if str(r[0]) >= start_date]
check(bool(rows), "panel carries no IWM rows in the capital window")
if rows:
    base = rows[0][4]
    want_last = round((rows[-1][4] / base - 1) * 100, 3)
    got = (attr.get("small_caps_pct") or {}).get("IWM") or []
    check(bool(got), "attractions.json has no small_caps_pct IWM series")
    if got:
        check(got[-1]["pct"] == want_last,
              f"IWM last pct {got[-1]['pct']} != recomputed {want_last}")
        check(len(got) == len(rows),
              f"IWM series length {len(got)} != panel rows {len(rows)}")
check("Desk vs small caps" in page,
      "desk page lacks the Desk vs small caps card")

# --- no regression on the GAP-1 benchmarks -------------------------
for sym in ("SPY", "QQQ"):
    srows = [r for r in panel.get(sym) or [] if str(r[0]) >= start_date]
    want = round((srows[-1][4] / srows[0][4] - 1) * 100, 3)
    got = (attr.get("benchmarks_pct") or {}).get(sym) or []
    check(got and got[-1]["pct"] == want,
          f"GAP-1 regression: {sym} last pct != recomputed {want}")

# --- 2. closed trades recomputed from the journal ------------------
fills = []
for path in JOURNALS:
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("event") == "fill":
            fills.append(rec)
fills.sort(key=lambda r: r["ts"])
lots = defaultdict(deque)
closed = {}
orphan = 0
for idx, f in enumerate(fills):
    key = (f.get("sleeve"), f["symbol"])
    qty, px = float(f["qty"]), float(f["price"])
    direction = 1 if f["side"] == "buy" else -1
    intent = f.get("position_intent") or ""
    is_close = intent.endswith("_to_close") or (
        not intent and lots[key] and lots[key][0][0] != direction)
    if not is_close:
        lots[key].append([direction, qty, px, f["ts"]])
        continue
    remaining, paired = qty, 0.0
    while remaining > 1e-9 and lots[key] and lots[key][0][0] != direction:
        lot = lots[key][0]
        take = min(remaining, lot[1])
        pnl = (px - lot[2]) * take if lot[0] == 1 else (lot[2] - px) * take
        agg = closed.setdefault(idx, {
            "sleeve": key[0], "symbol": key[1], "qty": 0.0,
            "entry_cost": 0.0, "pnl": 0.0, "exit_px": px,
            "exit_date": str(f["ts"])[:10],
            "side": "long" if lot[0] == 1 else "short"})
        agg["qty"] += take
        agg["entry_cost"] += lot[2] * take
        agg["pnl"] += pnl
        lot[1] -= take
        remaining -= take
        paired += take
        if lot[1] <= 1e-9:
            lots[key].popleft()
    if paired < qty - 1e-9:
        orphan += 1
want_trades = [{"sleeve": a["sleeve"], "symbol": a["symbol"],
                "side": a["side"], "qty": a["qty"],
                "entry_avg": round(a["entry_cost"] / a["qty"], 4),
                "exit_px": a["exit_px"], "exit_date": a["exit_date"],
                "pnl": round(a["pnl"], 2)}
               for a in closed.values()]
got_trades = attr.get("closed_trades") or []
check(len(got_trades) == len(want_trades),
      f"closed_trades count {len(got_trades)} != recomputed "
      f"{len(want_trades)}")
for want in want_trades:
    match = [g for g in got_trades
             if g.get("symbol") == want["symbol"]
             and g.get("exit_date") == want["exit_date"]]
    check(bool(match), f"closed trade missing from attractions: {want}")
    if match:
        g = match[0]
        for k in ("qty", "entry_avg", "exit_px", "pnl", "side", "sleeve"):
            check(g.get(k) == want[k],
                  f"closed trade {want['symbol']} field {k}: "
                  f"{g.get(k)} != recomputed {want[k]}")
meta = attr.get("closed_trades_meta") or {}
check(meta.get("unpaired_close_fills") == orphan,
      f"unpaired_close_fills {meta.get('unpaired_close_fills')} != "
      f"recomputed {orphan}")
check("Closed trades" in page, "desk page lacks the Closed trades card")

# --- producer source carries both series at the source -------------
check("dispatcher.jsonl" in SRC, "publish_desk.py does not read the journal")
check('"IWM"' in SRC, "publish_desk.py does not build the IWM series")

# --- 3. Opportunity Ranker stays honestly absent -------------------
check(not feed.get("setups"),
      "feed setups unexpectedly non-empty; ranker input appeared, "
      "revisit GAP-7 row 2 deliberately")
check("Opportunity Ranker" not in page,
      "desk page claims an Opportunity Ranker with no ranked series "
      "in the feed")

if misses:
    print("FAIL test_amazing_gap7:")
    for m in misses:
        print(" -", m)
    sys.exit(1)
print("PASS test_amazing_gap7")
