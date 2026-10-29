"""lazarus_exit: Lazarus' hold and exit arithmetic (lazarus-desk @a3319569 — desk.queue_pos's planned time exit from
the research entry bar, book.apply's entry fill with book.hold_exit (hold from the fill), book.exits: the time exit
at time_exit_at - 20 min (35 on a half-day close), the plan's own stop, session-only DAY sell limit at last x 0.99;
the SOURCE package in its own process, mode shadow, no broker) vs the port (desk.sleeves.families.lazarus:
time_exit_at, hold_exit, exit_decision) on the same lane, fire, fill and clock.

Each case: a random lane of the 75 (hold units 1h / 1d / 1w, holding from the plan or the fill), a fire bar of its
kind, a plan (max_bars 1-260 / 1-80 / 1-120 or none; no stop or a 4-30% stop), the entry fill on the entry bar's
session or 1-5 sessions later or on a closed day, an entry price, and a clock across the hold — biased to the exit
boundary minute, half-day closes, closed days and after-hours — with a live price above / below the stop or none.

Compared: the stored time exit (string), whether an exit is sent, its quantity, limit price and reason (time /
stop).

    LAZARUS_SRC=<lazarus-desk @a3319569> python3 -m tools.parity.run lazarus_exit"""
from datetime import date, timedelta

import pandas as pd

from desk import calendar as cal
from desk.sleeves.families import lazarus as L

from . import old_run, write_receipt
from .lazarus_common import COMMIT, HALF_DAYS, et, fire_bar, pick_row, plan, rand_session, seed_rng, source_tree

N_CASES = 3000
BATCH = 750

OLD = r'''
import json
from lazarus import desk as D, book as B, cal
SC = json.load(open("config/sleeves.json"))
C = {"mode": "shadow", "exit_limit": {"buffer_pct": 1.0}}
out = []
for c in PAYLOAD["cases"]:
    s = next(x for x in SC["sleeves"] if x["id"] == c["lane"])
    f, acct = c["fire"], s["broker_account"]
    S = {"book": {acct: {}}, "orders": {}, "seen": {}}
    p = D.queue_pos(S, SC, s, f, acct, {"qty": str(c["qty"]), "limit_price": "1.0"}, cal.ts(c["queued"]))
    te0 = p["time_exit_at"]
    p["status"] = "entry_pending"
    o = S["orders"]["x"] = {"cid": "x", "account": acct, "pos_id": p["id"], "side": "buy", "qty": c["qty"],
                            "limit": 1.0, "status": "new_local"}
    B.apply(S, SC, acct, o, {"status": "filled", "id": "b1", "filled_qty": str(c["qty"]),
                             "filled_avg_price": str(c["avg"]), "filled_at": c["fill_at"]}, [], cal.ts(c["fill_at"]))
    intents = []
    B.exits(S, SC, C, {}, lambda sym, acct=None: (c["px"], None), [], cal.ts(c["now"]), intents)
    x = intents[0] if intents else None
    out.append({"te0": te0, "te": p["time_exit_at"], "qty": int(x["order"]["qty"]) if x else None,
                "limit": x["order"]["limit_price"] if x else None, "why": x["why"] if x else None})
print(json.dumps(out))
'''


def make_case(i):
    rnd = seed_rng("exit", i)
    row = pick_row(rnd)
    kind = L.entry_kind(row)
    d = rand_session(rnd)
    fb = fire_bar(rnd, kind, d)
    p = plan(rnd, L.hold_kind(row) if L.hold_kind(row) in ("1h", "1d", "1w") else "1d")
    sym = "X%05d" % i
    f = {"key": f"{sym}:{row['id']}:x:{fb[:10]}", "sym": sym, "lane": row["id"], "fire_bar": fb, "D": fb[:10],
         "close": 10.0, "plan": p, "strategy": "s", "shadow": False, "source": "x"}
    eb, _ = L.entry_window(row, fb)
    u = rnd.random()
    fd = eb.date()
    if u < 0.2:                                        # a later fill session (hold from the fill)
        for _ in range(rnd.randint(1, 5)):
            fd += timedelta(days=1)
            while not cal.is_trading_day(fd):
                fd += timedelta(days=1)
    elif u < 0.23:
        fd = fd + timedelta(days=(5 - fd.weekday()) % 7 or 6)      # a weekend fill stamp
    fill = pd.Timestamp(et(fd, 9, 30)) + pd.Timedelta(minutes=rnd.randint(0, 389))
    if fill < eb:
        fill = eb
    avg = round(rnd.uniform(1, 400), 2)
    qty = rnd.randint(1, 60)
    te0 = L.time_exit_at(row, fb, p)
    te = L.hold_exit(row, p, te0, fill) if te0 is not None else None
    v = rnd.random()
    if te is not None and v < 0.45:                    # around the exit boundary
        lead = 35 if L.cal.close_minutes(te) != 960 and te == L.cal.s_close(te) else 20
        now = te - pd.Timedelta(minutes=lead) + pd.Timedelta(minutes=rnd.choice((-61, -1, 0, 0, 1, 2, 10, 25, 60, 1440)))
    elif te is not None and v < 0.6:
        now = te + pd.Timedelta(days=rnd.randint(0, 9), minutes=rnd.randint(-600, 600))
    elif v < 0.7:
        hd = rnd.choice(HALF_DAYS)
        now = pd.Timestamp(et(hd, 12, rnd.randint(0, 59)))
    else:
        now = fill + pd.Timedelta(minutes=rnd.randint(0, 60 * 24 * 400))
    now = now.tz_convert("UTC").floor("s").tz_convert(L.cal.TZ)     # floor in UTC: DST fall-back hours are ambiguous
    px = round(avg * rnd.uniform(0.6, 1.4), 2) if rnd.random() < 0.95 else None
    if px is not None and p["stop_pct"] < 99 and rnd.random() < 0.5:     # on / around the plan's stop
        px = round(avg * (1 - p["stop_pct"] / 100) * rnd.choice((0.97, 0.999, 1.0, 1.001, 1.03)), 2)
    if px is not None and px < 1 and rnd.random() < 0.5:
        px = round(px, 4)
    return {"lane": row["id"], "row": row, "fire": f, "queued": str(eb), "fill_at": str(fill), "avg": avg, "qty": qty,
            "now": str(now), "now_ts": now, "fill_ts": fill, "px": px}


def port(c):
    row, f = c["row"], c["fire"]
    te0 = L.time_exit_at(row, f["fire_bar"], f["plan"])
    te = L.hold_exit(row, f["plan"], te0, c["fill_ts"]) if te0 is not None else None
    ex = L.exit_decision(te, f["plan"], c["avg"], c["now_ts"], c["px"])
    return {"te0": str(te0) if te0 is not None else None, "te": str(te) if te is not None else None,
            "exit": ex}


def compare(s, p):
    if s["te0"] != p["te0"] or s["te"] != p["te"]:
        return False
    ex = p["exit"]
    if s["limit"] is None:
        return ex is None or ex["limit"] is None
    if ex is None or ex["limit"] is None:
        return False
    kind_s = "stop" if s["why"].startswith("stop") else "time"
    kind_p = "stop" if ex["why"].startswith("stop") else "time"
    return float(s["limit"]) == float(ex["limit"]) and kind_s == kind_p and s["why"] == ex["why"]


def run(n=N_CASES):
    src = source_tree()
    stats = {"exits": 0, "time": 0, "stop": 0, "holds": 0, "hold_kinds": {}, "hold_from": {}}
    diffs, identical = [], 0
    for b0 in range(0, n, BATCH):
        cases = [make_case(i) for i in range(b0, min(n, b0 + BATCH))]
        payload = {"cases": [{k: c[k] for k in ("lane", "fire", "queued", "fill_at", "avg", "qty", "now", "px")}
                             for c in cases]}
        res = old_run(OLD, payload, tree=src)
        for i, (c, s) in enumerate(zip(cases, res)):
            p = port(c)
            hk = L.hold_kind(c["row"])
            stats["hold_kinds"][hk] = stats["hold_kinds"].get(hk, 0) + 1
            hf = c["row"]["exit"]["hold_from"]
            stats["hold_from"][hf] = stats["hold_from"].get(hf, 0) + 1
            if s["limit"] is not None:
                stats["exits"] += 1
                stats["stop" if s["why"].startswith("stop") else "time"] += 1
            else:
                stats["holds"] += 1
            if compare(s, p) and (s["qty"] is None or s["qty"] == c["qty"]):
                identical += 1
            else:
                diffs.append({"case": b0 + i, "lane": c["lane"], "fire_bar": c["fire"]["fire_bar"],
                              "plan": c["fire"]["plan"], "fill": c["fill_at"], "now": c["now"], "px": c["px"],
                              "src": s, "port": {"te0": p["te0"], "te": p["te"], "exit": p["exit"]}})
    payload = {"cases": n, "identical": identical, "diffs": diffs[:50], "n_diffs": len(diffs), "stats": stats,
               "sleeves": [L.sleeve_id(r["id"]) for r in L.rows()],
               "method": "source desk.queue_pos -> book.apply (filled, hold_exit) -> book.exits (shadow mode, no "
                         "broker) in its own process vs the port's time_exit_at / hold_exit / exit_decision",
               "source": {"repo": "lazarus-desk", "commit": COMMIT, "src_dir": src}}
    write_receipt("lazarus_exit", payload)
    return dict(payload, sleeve="lazarus_exit")
