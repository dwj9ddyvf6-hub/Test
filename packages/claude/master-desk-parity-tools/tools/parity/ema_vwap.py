"""ema_vwap: old ema_vwap_sleeve.py vs the vendored femto port (with the master-desk restorations).

Old decisions traced from maybe_enter / manage_position with the old module's own functions (add_indicators,
deviation_below, reverted_to_vwap, size_qty) in the old order; desk-wide gates out of scope (cutover doctrine).
Corpus: 50 paths (some with zero-volume days) x every day + up to 15 entries per path walked to exit."""
import os
from datetime import datetime, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("ema_vwap")
N_SEEDS = 50
WINDOW = 120

OLD = r'''
import pandas as pd
from datetime import date, timedelta
import ema_vwap_sleeve as O
def frame(rows):
    df = pd.DataFrame([(pd.Timestamp(r["d"]), r["o"], r["h"], r["l"], r["c"], r["v"]) for r in rows],
                      columns=["date", "o", "h", "l", "c", "v"]).set_index("date")
    return O.add_indicators(df)
def entry(df, equity):
    if len(df) < O.WARMUP_BARS + 1 or not O.deviation_below(df):
        return None
    qty = O.size_qty(equity, float(df["c"].iloc[-1]))
    if qty <= 0 or qty * float(df["c"].iloc[-1]) > O.SLEEVE_NOTIONAL_CAP * equity:
        return None
    return qty
def exit_reason(df, p, today_iso):
    close = float(df["c"].iloc[-1])
    entry_px = float(p["entry_px"])
    pnl = close / entry_px - 1.0
    if pnl <= -O.STOP_LOSS:
        return "stop_loss"
    if pnl >= O.PROFIT_TARGET:
        return "profit_target"
    if O.reverted_to_vwap(df):
        return "vwap_reversion"
    d0, d1 = date.fromisoformat(p["entry_date"]), date.fromisoformat(today_iso)
    held = sum(1 for i in range((d1 - d0).days) if (d0 + timedelta(days=i + 1)).weekday() < 5)
    return "time_stop" if held >= O.TIME_STOP_DAYS else None
out = []
W = PAYLOAD["window"]
for case in PAYLOAD["cases"]:
    rows = case["rows"]
    ents = [entry(frame(rows[max(0, i + 1 - W):i + 1]), case["equity"]) for i in range(31, len(rows))]
    exits = []
    for e in case["entries"]:
        p = {"entry_px": rows[e]["o"], "entry_date": rows[e]["d"]}
        got = None
        for d in range(e + 1, min(len(rows), e + 30)):
            df = frame(rows[max(0, d - W):d])
            if len(df) < O.WARMUP_BARS + 1:
                continue
            r = exit_reason(df, p, rows[d]["d"])
            if r:
                got = [rows[d]["d"], r]
                break
        exits.append(got)
    out.append({"entries": ents, "exits": exits})
print(json.dumps(out))
'''

EXIT_MAP = (("stop=True", "stop_loss"), ("target=True", "profit_target"), ("reverted=True", "vwap_reversion"))


def _ctx(session, pos=None):
    st = {"SYM": {"position": pos}} if pos else {}
    return fc.Context(now=datetime.fromisoformat(session).replace(hour=15, minute=3, tzinfo=timezone.utc).timestamp(),
                      session=session, equity=100_000.0, extra={"sleeve_state": st, "universe": ["SYM"]})


def _femto_entry(window, session):
    out = [i for i in F.signal({"SYM": as_epoch(window)}, {}, _ctx(session)) if i.kind == "enter"]
    return out[0].qty_hint if out else None


def _femto_exit(window, pos, session):
    out = [i for i in F.signal({"SYM": as_epoch(window)}, {"SYM": pos["qty"]}, _ctx(session, pos)) if i.kind == "exit"]
    if not out:
        return None
    r = out[0].reason
    for key, name in EXIT_MAP:          # old precedence: stop -> target -> reversion -> time
        if key in r:
            return name
    return "time_stop"


def run():
    cases = []
    for seed in range(N_SEEDS):
        rows = walk(2000 + seed, 400, start_px=15 + 3 * seed, vol=0.02 + (seed % 5) * 0.006)
        cases.append({"rows": rows, "equity": 100_000.0, "entries": []})
    for c in cases:
        rows = c["rows"]
        es = [i + 1 for i in range(31, len(rows) - 1)
              if _femto_entry(rows[max(0, i + 1 - WINDOW):i + 1], rows[i + 1]["d"])]
        c["entries"] = es[:15]
    old = old_run(OLD, {"cases": cases, "window": WINDOW})
    n = same = 0
    diffs = []
    for seed, (c, o) in enumerate(zip(cases, old)):
        rows = c["rows"]
        for k, a in enumerate(o["entries"]):
            i = 31 + k
            b = _femto_entry(rows[max(0, i + 1 - WINDOW):i + 1], rows[min(i + 1, len(rows) - 1)]["d"])
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "entry", "seed": seed, "day": rows[i]["d"], "old": a, "new": b})
        for e, a in zip(c["entries"], o["exits"]):
            pos = {"qty": 10, "entry_px": rows[e]["o"], "entry_date": rows[e]["d"]}
            b = None
            for d in range(e + 1, min(len(rows), e + 30)):
                r = _femto_exit(rows[max(0, d - WINDOW):d], pos, rows[d]["d"])
                if r:
                    b = [rows[d]["d"], r]
                    break
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "exit", "seed": seed, "entry": rows[e]["d"], "old": a, "new": b})
    res = {"sleeve": "ema_vwap", "cases": n, "identical": same, "diffs": diffs[:40], "n_diffs": len(diffs)}
    write_receipt("ema_vwap" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
