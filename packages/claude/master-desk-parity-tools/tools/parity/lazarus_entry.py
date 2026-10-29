"""lazarus_entry: Lazarus' entry decision (lazarus-desk @a3319569, desk.decide() and run_pass's fire-close fill-in,
data.dv20 / data.bars on engine-store CSVs, desk.oldest_fire_day — the SOURCE package in its own process) vs the
port (desk.sleeves.families.lazarus: decide, close_on, dv20, oldest_fire_day) on the same fire, clock, quotes,
book and bars.

The removed gates are not compared — the source runs its own ungated path instead:
  * fear_day lanes (1d / 1w kinds) run with entry policy "next_open" (Lazarus' gate-free policy: trigger from the
    research entry bar for max_delay_minutes). A weekly fire is handed to the source with its fire bar moved to
    its week's last session, the bar whose entry_bar("1d") is the 1W research entry bar entry_bar("1w") — the
    entry window the port opens (next_open always read entry_bar("1d"); Lazarus never ran it for weekly lanes);
  * the qqq_red_1h lane keeps its policy with QQQ and the stock quoted red, so its gate passes and the entry
    window, limit and sizing are the source's;
  * held = the lane's own symbols (the cross-lane held_by_account set removed); avail = an unbounded pool (the
    account cash pool removed).
Each case: a random lane of the 75, a fire (daily 09:30 / hourly RTH bar / Monday-labelled, week-last-session or
weekday weekly bars; close given or filled from the bars; plan; size class incl. 1dc's core_small / core_micro /
test / log_only; shadow; ref_price), a clock before / inside / at the edges of / after the entry window or on a
closed day, a live price (missing in some cases), the stock's 12-30 daily engine bars (some below 20: dv20 None;
volumes around the liquidity floors), the lane's used budget and held symbols.

Compared: the decision (result; for an intent its quantity and limit price), the filled fire close, dv20 and the
5-session oldest fire day. Counted, not failed: a missing live price the source turned into an order with limit
"None" (its run_pass assert valid_order then raised) is the port's "wait".

    LAZARUS_SRC=<lazarus-desk @a3319569> python3 -m tools.parity.run lazarus_entry"""
import json
import os
import shutil
import tempfile
import copy
from datetime import date, timedelta

import pandas as pd

from desk import calendar as cal
from desk.sleeves.families import lazarus as L

from . import old_run, write_receipt
from .lazarus_common import (COMMIT, daily_bars, fire_bar, pick_row, plan, rand_session, seed_rng,
                             source_tree, write_bars)

N_CASES = 3000
BATCH = 500

OLD = r'''
import json, math
import pandas as pd
from lazarus import desk as D, data, cal
out = []
for c in PAYLOAD["cases"]:
    data._B.clear()
    C = {"paths": {"engine_bars": PAYLOAD["eng"]}, "mode": "shadow"}
    s, f = c["row"], dict(c["fire"])
    now = cal.ts(c["now"])
    if s["kind"] == "1w":
        t = cal.day0(f["fire_bar"]); last = t - pd.Timedelta(days=t.weekday()) + pd.Timedelta(days=4)
        while not cal.is_td(last): last -= pd.Timedelta(days=1)
        f["fire_bar"] = str(last.date())
    if f["close"] is None:
        b = data.bars(C, f["sym"]); r = b[b.d == cal.day0(f["D"])] if b is not None else None
        f["close"] = float(r.close.iloc[-1]) if r is not None and len(r) else None
    day = str(cal.day0(now).date()); td = cal.is_td(now)
    q = {f["sym"]: (c["px"], c["prior"]), "QQQ": (c["qqq_px"], c["qqq_prior"])}
    quotes = lambda sym, acct=None: q.get(sym, (None, None))
    rec = {"close": f["close"], "dv20": data.dv20(C, f["sym"], now), "oldest": D.oldest_fire_day(now, 5)}
    try:
        dec = D.decide(C, s, f, now, day, td, None, None, c["qqq_px"], c["qqq_prior"], None, None, quotes,
                       set(c["held"]), {"MAIN": 1e18, "TEST_MWJW": 1e18}, {s["id"]: c["used"]})
        o = dec.get("order")
        rec.update(result=dec["result"], qty=int(o["qty"]) if o else None, limit=o["limit_price"] if o else None)
    except Exception as e:
        rec.update(result="error", error=type(e).__name__ + ": " + str(e)[:120])
    out.append(rec)
print(json.dumps(out))
'''


def make_case(i, eng):
    rnd = seed_rng("entry", i)
    row = pick_row(rnd)
    kind = L.entry_kind(row)
    d = rand_session(rnd)
    fb = fire_bar(rnd, kind, d)
    sym = "Z%05d" % i
    px0 = rnd.choice((rnd.uniform(0.6, 4.9), rnd.uniform(5, 60), rnd.uniform(60, 900)))
    p = plan(rnd, kind)
    if p["max_bars"] is None and rnd.random() < 0.5:
        p["max_bars"] = 5
    sc = None
    if row["sizing"].get("position_usd_by_class"):
        sc = rnd.choice(("core_small", "core_micro", "test", "log_only", "mid", None))
    elif rnd.random() < 0.5:
        sc = rnd.choice(("test", "log_only"))
    f = {"key": f"{sym}:{row['id']}:x:{fb[:10]}", "sym": sym, "lane": row["id"], "fire_bar": fb, "D": fb[:10],
         "close": round(px0, 2) if rnd.random() < 0.75 else None, "plan": p, "strategy": "s", "shadow": rnd.random() < 0.03,
         "source": "x", "size_class": sc}
    if rnd.random() < 0.1:
        f["ref_price"] = round(px0 * rnd.uniform(0.95, 1.05), 2)
    eb, dl = L.entry_window(row, fb)
    u = rnd.random()
    if u < 0.15:
        now = eb - pd.Timedelta(minutes=rnd.randint(1, 3000))
    elif u < 0.25:
        now = eb
    elif u < 0.35:
        now = dl
    elif u < 0.75:
        now = eb + (dl - eb) * rnd.random()
    elif u < 0.9:
        now = dl + pd.Timedelta(minutes=rnd.randint(1, 6000))
    else:
        now = eb + pd.Timedelta(days=rnd.randint(1, 4), minutes=rnd.randint(-120, 120))
    now = now.tz_convert("UTC").floor("s").tz_convert(L.cal.TZ)     # floor in UTC: DST fall-back hours are ambiguous
    px = round(px0 * rnd.uniform(0.9, 1.12), 2 if px0 >= 1 else 4)
    if kind != "1h" and rnd.random() < 0.08:
        px = None
    prior = max(round((px or px0) * rnd.uniform(1.0, 1.04), 4), px or 0.0)   # 1h: the stock quoted red (gate passes)
    qqq_prior = round(rnd.uniform(300, 600), 2)
    qqq_px = round(qqq_prior * (rnd.uniform(0.97, 0.999) if kind == "1h" else rnd.uniform(0.97, 1.03)), 2)
    z = row["sizing"]
    held = ["H%d" % k for k in range(rnd.randint(0, 3))] + ([sym] if rnd.random() < 0.05 else [])
    used = round(rnd.uniform(0, 1.2) * float(z["budget_usd"] or 1000), 2) if rnd.random() < 0.6 else 0.0
    upto = max(now.date(), date.fromisoformat(fb[:10]) + timedelta(days=1))
    rows = daily_bars(rnd, upto, rnd.choice((12, 19, 20, 24, 30)), px0, rnd.random() < 0.2)
    write_bars(eng, sym, rows)
    src_row = copy.deepcopy(row)
    if src_row["entry"]["policy"] == "fear_day":       # the source's own gate-free policy
        src_row["entry"]["policy"] = "next_open"
    return {"row": row, "src_row": src_row, "fire": f, "now": str(now), "now_epoch": now.timestamp(), "px": px, "prior": prior,
            "qqq_px": qqq_px, "qqq_prior": qqq_prior, "held": held, "used": used, "bars": rows, "kind": kind}


def port(c):
    f = dict(c["fire"])
    now = L.ts(c["now_epoch"])
    if f["close"] is None:
        f["close"] = L.close_on(c["bars"], f["D"])
    dv = L.dv20(c["bars"], now)
    dec = L.decide(c["row"], f, now, c["px"], set(c["held"]), c["used"], dv)
    return {"close": f["close"], "dv20": dv, "oldest": L.oldest_fire_day(now, 5), "result": dec["result"],
            "qty": dec.get("qty"), "limit": dec.get("limit")}


def compare(src, prt):
    """-> (same, explained)"""
    res = "held" if src.get("result") == "held_by_account" else src.get("result")
    base = src["close"] == prt["close"] and src["dv20"] == prt["dv20"] and src["oldest"] == prt["oldest"]
    if res == "intent" and src["limit"] == "None":
        return base and prt["result"] == "wait", True
    if res == "error" and "NoneType" in src.get("error", ""):    # float(None): no reference price at all
        return base and prt["result"] == "wait", True
    if res != prt["result"]:
        return False, False
    if res == "intent":
        return base and src["qty"] == prt["qty"] and float(src["limit"]) == float(prt["limit"]), False
    return base, False


def run(n=N_CASES):
    src = source_tree()
    stats = {"results": {}, "explained_source_raised": 0, "intents": 0, "kinds": {}}
    diffs, identical, compared = [], 0, 0
    tmp = tempfile.mkdtemp(prefix="lz_entry_")
    try:
        for b0 in range(0, n, BATCH):
            eng = os.path.join(tmp, "eng%d" % b0)
            cases = [make_case(i, eng) for i in range(b0, min(n, b0 + BATCH))]
            payload = {"eng": eng, "cases": [dict({k: c[k] for k in ("fire", "now", "px", "prior", "qqq_px",
                                                                       "qqq_prior", "held", "used")}, row=c["src_row"])
                                              for c in cases]}
            res = old_run(OLD, payload, tree=src)
            for i, (c, s) in enumerate(zip(cases, res)):
                p = port(c)
                same, expl = compare(s, p)
                compared += 1
                stats["results"][p["result"]] = stats["results"].get(p["result"], 0) + 1
                stats["kinds"][c["kind"]] = stats["kinds"].get(c["kind"], 0) + 1
                stats["intents"] += 1 if p["result"] == "intent" else 0
                if same:
                    identical += 1
                    stats["explained_source_raised"] += 1 if expl else 0
                else:
                    diffs.append({"case": b0 + i, "lane": c["row"]["id"], "fire": c["fire"], "now": c["now"],
                                  "px": c["px"], "src": s, "port": p})
            shutil.rmtree(eng, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    payload = {"cases": compared, "identical": identical, "diffs": diffs[:50], "n_diffs": len(diffs), "stats": stats,
               "sleeves": [L.sleeve_id(r["id"]) for r in L.rows()],
               "method": "source desk.decide (next_open for fear_day lanes, weekly fire bar -> its week's last "
                         "session; qqq_red_1h with red quotes) + run_pass close fill-in + data.dv20 on engine CSVs + "
                         "desk.oldest_fire_day, in its own process, vs the port's decide / close_on / dv20 / "
                         "oldest_fire_day",
               "source": {"repo": "lazarus-desk", "commit": COMMIT, "src_dir": src}}
    write_receipt("lazarus_entry", payload)
    return dict(payload, sleeve="lazarus_entry")
