"""momentum: old momentum_sleeve.py (mode_rank at 16:05 + mode_fill at 10:05) vs the restored femto port.

The old DECISIONS are traced with the old module's own compute_rank / new_buy_gates / cost_bps / constants in
the old order: rank -> review due? -> target/sells/buys; fill -> rank sells (fresh quote) -> 40% breaker ->
gated buys (30% budget minus book + pending notional, split over the target, all-in mid x (1 + cost), 1-share
minimum, book cap 10). Desk gates (risk_gate, drawdown brake, chart gate, desk cap) out of scope.
Corpus: 400 random books/universes/times/VIX states."""
import os
import random
from datetime import date, datetime, timedelta, timezone

from zoneinfo import ZoneInfo

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("momentum")
ET = ZoneInfo("America/New_York")
N_CASES = 400

OLD = r'''
import math
from datetime import datetime
from zoneinfo import ZoneInfo
import momentum_sleeve as O
ET = ZoneInfo("America/New_York")
out = []
for case in PAYLOAD["cases"]:
    bars = {s: [dict(b) for b in rows] for s, rows in case["bars"].items()}
    now = datetime.fromisoformat(case["now"]).astimezone(ET)
    # rank at 16:05 of the previous session == the same completed bars
    today = case["today"]
    rank = O.compute_rank(bars, today, now)
    spy = rank["spy_sessions"]
    book = case["book"]
    pend_entry = case["pending"]
    plan = None
    from datetime import date, timedelta
    prev = date.fromisoformat(today) - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    if spy and spy[-1] >= prev.isoformat():
        last_rev = case["meta"].get("last_review_spy_date")
        is_first = not book and not case["meta"].get("ranked")
        if last_rev and spy:
            due = sum(1 for d in spy if d > last_rev) >= O.REVIEW_EVERY
        else:
            due = False
        due = is_first or last_rev is None or due
        target = rank["top"] if due else sorted(book)
        sells = [s for s in book if s not in target]
        buys = [s for s in target if s not in book and s not in pend_entry]
        plan = {"review": due, "target": target, "sells": sells, "buys": buys}
    mids = case["mids"]
    exits = []
    done = []
    for s in (plan or {}).get("sells", []):
        if mids.get(s) is None:
            continue
        exits.append([s, "rank"]); done.append(s)
    for s, p in book.items():
        if s in done:
            continue
        m = mids.get(s)
        if m is None:
            continue
        if m <= (1 - O.BREAKER_DROP) * p["entry_px"]:
            exits.append([s, "breaker"]); done.append(s)
    buys_out = []
    if plan and plan["buys"]:
        blocks = O.new_buy_gates(now, case["vix"] or (None, None, None, "unavailable"), bars.get("SPY") or [], today)
        if not blocks:
            book_not = sum(p["qty"] * p["entry_px"] for p in book.values())
            pend_not = sum(p["qty"] * p["ref_px"] for p in pend_entry.values())
            budget = max(0.0, O.SLEEVE_CAP * case["equity"] - book_not - pend_not)
            n_target = max(1, len(plan["target"] or plan["buys"]))
            n_open = len(book) + len(pend_entry)
            if budget > 0:
                for s in plan["buys"]:
                    if n_open - len(done) >= O.MAX_POSITIONS:
                        continue
                    m = mids.get(s)
                    if m is None:
                        continue
                    all_in = m * (1.0 + O.cost_bps(m))
                    qty = max(1, math.floor((budget / n_target) / all_in)) if all_in > 0 else 1
                    buys_out.append([s, qty]); n_open += 1
    out.append({"plan": None if plan is None else {k: plan[k] for k in ("review", "sells", "buys")},
                "exits": exits, "buys": buys_out})
print(json.dumps(out))
'''


def _femto(case):
    st = {}
    for s, p in case["book"].items():
        st[s] = {"position": {"qty": p["qty"], "entry_px": p["entry_px"], "entry_date": "2025-01-02"}}
    for s, p in case["pending"].items():
        st.setdefault(s, {})["pending_entry"] = {"qty": p["qty"], "ref_px": p["ref_px"]}
    now = datetime.fromisoformat(case["now"]).timestamp()
    quotes = {s: {"bid": m - 0.01, "ask": m + 0.01} for s, m in case["mids"].items() if m is not None}
    ctx = fc.Context(now=now, session=case["today"], equity=case["equity"],
                     extra={"sleeve_state": st, "meta": case["meta"], "quotes": quotes, "vix": case["vix"]})
    bars = {s: as_epoch([dict(d=b["date"], **{k: b[k] for k in "ohlcv"}) for b in rows]) for s, rows in case["bars"].items()}
    plan = F.review_plan(bars, st, case["meta"], case["today"])
    out = F.signal(bars, {}, ctx)
    exits = []
    for i in out:
        if i.kind == "exit":
            exits.append([i.symbol, "breaker" if "breaker" in i.reason else "rank"])
    return {"plan": None if plan is None else {"review": plan["review"], "sells": plan["sells"], "buys": plan["buys"]},
            "exits": exits, "buys": [[i.symbol, i.qty_hint] for i in out if i.kind == "enter"]}


def run():
    rnd = random.Random(23)
    cases = []
    for k in range(N_CASES):
        n = rnd.randint(12, 45)
        syms = [f"M{j:02d}" for j in range(n)] + ["SPY"]
        bars = {}
        days = 300
        for j, s in enumerate(syms):
            rows = walk(50_000 + k * 100 + j, days, start_px=rnd.uniform(3, 400), vol=rnd.uniform(0.01, 0.05),
                        drift=rnd.uniform(-0.002, 0.004))
            if rnd.random() < 0.1:
                rows = rows[-rnd.randint(60, 200):]
            bars[s] = [{"date": r["d"], "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"],
                        "v": r["v"] * rnd.choice((0.01, 1, 5))} for r in rows]
        last_day = date.fromisoformat(bars["SPY"][-1]["date"])
        today = last_day + timedelta(days=1)
        while today.weekday() >= 5:
            today += timedelta(days=1)
        hh, mm = rnd.choice(((10, 5), (10, 30), (9, 50), (14, 30)))
        if rnd.random() < 0.15:
            today = today + timedelta(days=rnd.choice((0, 3)))      # occasionally a stale-SPY case
        now = datetime(today.year, today.month, today.day, hh, mm, tzinfo=ET)
        held = rnd.sample(syms[:-1], rnd.randint(0, min(10, n)))
        book = {s: {"qty": rnd.randint(1, 200), "entry_px": round(bars[s][-1]["c"] * rnd.uniform(0.5, 1.6), 4)}
                for s in held}
        rest = [s for s in syms[:-1] if s not in held]
        pend = {s: {"qty": rnd.randint(1, 50), "ref_px": round(bars[s][-1]["c"], 2)}
                for s in rnd.sample(rest, min(len(rest), rnd.randint(0, 2)))}
        spy_dates = [b["date"] for b in bars["SPY"]]
        meta = rnd.choice(({}, {"ranked": True}, {"ranked": True, "last_review_spy_date": spy_dates[-rnd.randint(1, min(120, len(spy_dates)))]}))
        mids = {s: (None if rnd.random() < 0.05 else round(bars[s][-1]["c"] * rnd.uniform(0.55, 1.1), 4)) for s in syms}
        vix = rnd.choice((None, (18.0, 17.0, today.isoformat(), "yahoo"), (35.0, 30.0, today.isoformat(), "yahoo"),
                          (21.0, 16.0, today.isoformat(), "yahoo"), (19.0, 18.0, "2020-01-01", "yahoo")))
        cases.append({"bars": bars, "today": today.isoformat(), "now": now.isoformat(), "book": book, "pending": pend,
                      "meta": meta, "mids": mids, "vix": vix, "equity": rnd.choice((50_000.0, 100_000.0, 400_000.0))})
    old = old_run(OLD, {"cases": cases})
    n = same = 0
    diffs = []
    for k, (c, a) in enumerate(zip(cases, old)):
        t_et = datetime.fromisoformat(c["now"]).astimezone(ET)
        if (t_et.hour, t_et.minute) < (10, 0):
            a = {"plan": a["plan"], "exits": [], "buys": []}          # old fill: nothing before 10:00 ET
        b = _femto(c)
        n += 1
        same += a == b
        if a != b:
            diffs.append({"case": k, "old": a, "new": b})
    res = {"sleeve": "momentum", "cases": n, "identical": same, "diffs": diffs[:20], "n_diffs": len(diffs)}
    write_receipt("momentum" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
