"""rsi_meanrev: old rsi_meanrev_sleeve.py vs the vendored femto port (with the master-desk restorations).

The old entry/exit DECISIONS are traced from maybe_enter / manage_position in the old gate order using only
the old module's own functions (rsi_wilder, size_qty, _trading_days_between, constants); the desk-wide gates
(earnings, kill switch, drawdown brake, chart gate, desk cap) are out of scope by the cutover doctrine.
Corpus: 50 paths x every day (entries) + up to 15 entries per path walked to their first exit."""
import os
from datetime import datetime, timezone

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("rsi_meanrev")
N_SEEDS = 50

OLD = r'''
import pandas as pd
from datetime import date
from zoneinfo import ZoneInfo
import rsi_meanrev_sleeve as O
ET = ZoneInfo("America/New_York")
def frame(rows):
    idx = pd.DatetimeIndex([pd.Timestamp(r["d"] + " 00:00", tz=ET) for r in rows])
    return pd.DataFrame({"o": [r["o"] for r in rows], "h": [r["h"] for r in rows], "l": [r["l"] for r in rows],
                         "c": [r["c"] for r in rows], "v": [r["v"] for r in rows]}, index=idx)
def entry(bars, equity):
    if len(bars) < O.WARMUP_BARS:
        return None
    last_rsi = O.rsi_wilder(bars["c"]).iloc[-1]
    if pd.isna(last_rsi) or last_rsi >= O.RSI_OVERSOLD:
        return None
    if len(bars) < O.MA200_PERIOD:
        return None
    sma200 = float(bars["c"].rolling(O.MA200_PERIOD).mean().iloc[-1])
    last_close = float(bars["c"].iloc[-1])
    if last_close <= sma200:
        return None
    qty = O.size_qty(equity, last_close)
    return qty if qty > 0 else None
def exit_reason(bars, p, today):
    last_close = float(bars["c"].iloc[-1])
    rsi = O.rsi_wilder(bars["c"]).iloc[-1]
    entry_px = p["entry_px"]
    sma5 = (float(bars["c"].rolling(O.MA5_PERIOD).mean().iloc[-1]) if len(bars) >= O.MA5_PERIOD else None)
    if sma5 is not None and last_close > sma5:
        return "sma5_exit"
    if not pd.isna(rsi) and rsi > O.RSI_OVERBOUGHT:
        return "rsi_overbought"
    if last_close >= entry_px * (1.0 + O.PROFIT_TARGET):
        return "profit_target"
    if last_close <= entry_px * (1.0 - O.STOP_LOSS):
        return "stop_loss_market"
    if O._trading_days_between(bars, p.get("entry_date", ""), today) >= O.TIME_STOP_DAYS:
        return "time_stop"
    return None
out = []
for case in PAYLOAD["cases"]:
    rows = case["rows"]
    ents = []
    for i in range(30, len(rows)):
        ents.append(entry(frame(rows[max(0, i + 1 - 360):i + 1]), case["equity"]))
    exits = []
    for e in case["entries"]:
        p = {"entry_px": rows[e]["o"], "entry_date": rows[e]["d"]}
        got = None
        for d in range(e + 1, min(len(rows), e + 30)):
            r = exit_reason(frame(rows[max(0, d - 360):d]), p, date.fromisoformat(rows[d]["d"]))
            if r:
                got = [rows[d]["d"], r]
                break
        exits.append(got)
    out.append({"entries": ents, "exits": exits})
print(json.dumps(out))
'''


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
    return out[0].reason.split(":", 1)[1].split()[0]


def run():
    cases = []
    for seed in range(N_SEEDS):
        rows = walk(1000 + seed, 520, start_px=30 + seed, vol=0.018 + (seed % 4) * 0.007, drift=0.0009)
        cases.append({"rows": rows, "equity": 100_000.0, "entries": []})
    for c in cases:
        rows = c["rows"]
        es = []
        for i in range(30, len(rows) - 1):
            if _femto_entry(rows[max(0, i + 1 - 360):i + 1], rows[i + 1]["d"]):
                es.append(i + 1)
        c["entries"] = es[:15]
    old = old_run(OLD, {"cases": cases})
    n = same = 0
    diffs = []
    for seed, (c, o) in enumerate(zip(cases, old)):
        rows = c["rows"]
        for k, a in enumerate(o["entries"]):
            i = 30 + k
            b = _femto_entry(rows[max(0, i + 1 - 360):i + 1], rows[min(i + 1, len(rows) - 1)]["d"])
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "entry", "seed": seed, "day": rows[i]["d"], "old": a, "new": b})
        for e, a in zip(c["entries"], o["exits"]):
            pos = {"qty": 10, "entry_px": rows[e]["o"], "entry_date": rows[e]["d"]}
            b = None
            for d in range(e + 1, min(len(rows), e + 30)):
                r = _femto_exit(rows[max(0, d - 360):d], pos, rows[d]["d"])
                if r:
                    b = [rows[d]["d"], r]
                    break
            n += 1
            same += a == b
            if a != b:
                diffs.append({"kind": "exit", "seed": seed, "entry": rows[e]["d"], "old": a, "new": b})
    res = {"sleeve": "rsi_meanrev", "cases": n, "identical": same, "diffs": diffs[:40], "n_diffs": len(diffs)}
    write_receipt("rsi_meanrev" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
