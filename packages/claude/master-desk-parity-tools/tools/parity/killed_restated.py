"""killed_golden_cross_spy, killed_naive_20d_breakout and the daily / opening arms of killed_short_candidates (C4,
C5a, C5b): these studies never had committed code (golden cross is a characterization; the naive-breakout and
short-candidate runners stayed in /tmp), so there is no source to run. This harness checks what can still be checked:
the sleeve, stepped forward on the engine's own tranche ledger (KilledSleeve.signal: plan() then TrancheBook.step),
against a batch restatement of the pre-registered rule over the same series. It catches what forward stepping gets
wrong (a session off, a missed or duplicated signal, de-overlap timing, an exit on the wrong pass), not a misreading
of the pre-registration both sides share.

Per case, real trading days (the desk calendar, early closes included) and random daily bars with regime drifts.
Passes per session: 09:31 (quotes at the open), 09:45 (a random price inside the first half hour), 10:00 (the first
30-minute close) and the close - 20 min (the close, inside the market-on-close window); the daily bars of completed
sessions only. Compared exactly, per tranche: symbol, arm, entry session and price, exit session and price (open
tranches: entry only).

  golden cross    the SMA50 / SMA200 state of close t (ties keep the position), long from open t+1 while +1, flat at
                  the first pass of t+1 when -1; birth holds the state (sleeve divergence)
  naive breakout  close t > max(close t-20 .. t-1) -> long open t+1, out at close t+20; a signal while a hold is open
                  (t before its exit session) is skipped
  C4              closes of t-1 and t both in the top 20% of their day's range -> short open t+1, cover close t+2
                  (every streak day; overlapping tranches)
  C5              open_t / close_{t-1} - 1 >= 2% and open_t >= 0.98 x the trailing-252-session high -> short open t;
                  (a) out at the first price at or below close_{t-1} before 10:00, else the first-30-minute close;
                  (b) out at the first-30-minute close"""
import json
import random
import sys
from datetime import date, datetime

from desk import calendar as cal
from desk.contract import View
from desk.sleeves.killed import common as K
from desk.sleeves.killed import daily as DL
from desk.sleeves.killed import intraday as IN
from desk.util import ET

from . import write_receipt

N_CASES = 1000


def days_from(rnd, n):
    d = date(2024, 1, 2).toordinal() + rnd.randint(0, 400)
    out = []
    while len(out) < n:
        x = date.fromordinal(d)
        if cal.is_trading_day(x):
            out.append(x.isoformat())
        d += 1
    return out


def series(rnd, days, gap_p=0.0):
    px, out, drift = rnd.uniform(15, 300), [], 0.0
    for day in days:
        if rnd.random() < 0.03:
            drift = rnd.choice([-0.006, -0.002, 0.0, 0.002, 0.006])
        g = rnd.choice([0.0, 0.0, 0.025, 0.04]) if rnd.random() < gap_p else rnd.gauss(0, 0.004)
        o = px * (1 + g)
        c = max(0.5, o * (1 + rnd.gauss(drift, 0.018)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.006)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.006)))
        if rnd.random() < 0.25:                                   # strong closes (top of the range) for C4
            c = h - (h - lo) * rnd.uniform(0, 0.15)
        p45 = o * (1 + rnd.gauss(-0.01, 0.012))                   # inside the first half hour
        p30 = o * (1 + rnd.gauss(0, 0.01))                        # the first 30-minute close
        out.append({"day": day, "t": datetime(*map(int, day.split("-")), 9, 30, tzinfo=ET).timestamp(),
                    "o": round(o, 4), "h": round(max(h, o, c, p45, p30), 4), "l": round(min(lo, o, c, p45, p30), 4),
                    "c": round(c, 4), "v": 1e6, "p45": round(p45, 4), "p30": round(p30, 4)})
        px = c
    return out


def passes(day):
    o, c = cal.session_open(day), cal.session_close(day)
    return [("open", o + 60), ("p45", o + 15 * 60), ("p30", o + 30 * 60), ("close", c - 20 * 60)]


def step(sleeve, data, days, first):
    """the sleeve through sessions days[first:], every pass; -> its tranches (all ever seen, by id)."""
    st, seen = {}, {}
    pre = {s: [{kk: b[kk] for kk in ("t", "o", "h", "l", "c", "v")} for b in rows] for s, rows in data.items()}
    for k in range(first, len(days)):
        d = days[k]
        bars = {s: rows[:k] for s, rows in pre.items()}
        for what, now in passes(d):
            px = {s: rows[k][{"open": "o", "p45": "p45", "p30": "p30", "close": "c"}[what]] for s, rows in data.items()}
            quotes = {s: {"last": p, "t": now, "day_open": data[s][k]["o"]} for s, p in px.items()}
            v = View(now=now, session=d, state=st, bars={"1d": bars}, quotes=quotes, equity=100_000.0,
                     extra={"pending_orders": [], "closed_trades": []})
            sleeve.signal(v)
            st = sleeve._st
            for t in st.get("tranches", []):
                seen[t["id"]] = dict(t)
    return seen


def summarize(trs):
    out = []
    for t in trs.values():
        if t["status"] == "void":
            out.append([t["sym"], t["arm"], "void", t["enter_day"]])
        elif t["status"] == "planned":
            out.append([t["sym"], t["arm"], "planned", t["enter_day"]])
        else:
            row = [t["sym"], t["arm"], t["enter_day"], round(t["entry_ref"], 4)]
            if t["status"] == "closed":
                row += [K.et_day(t["exited_at"]), round(t["exit_ref"], 4)]
            out.append(row)
    return sorted(out, key=json.dumps)


# -- batch restatements ------------------------------------------------------------------------------------------
def batch_golden(rows, days, first):
    out, pos, entry = [], False, None
    closes = [r["c"] for r in rows]
    for k in range(first - 1, len(days) - 1):                     # close k decides at the first pass of k+1
        if k < 200:
            continue
        f, s = sum(closes[k - 49:k + 1]) / 50, sum(closes[k - 199:k + 1]) / 200
        state = 1 if f > s else (-1 if f < s else 0)
        want = state if state != 0 else (1 if pos else -1)
        if want > 0 and not pos:
            pos, entry = True, [days[k + 1], rows[k + 1]["o"]]
        elif want < 0 and pos:
            out.append(["SPY", "gc", entry[0], round(entry[1], 4), days[k + 1], round(rows[k + 1]["o"], 4)])
            pos = False
    if pos:
        out.append(["SPY", "gc", entry[0], round(entry[1], 4)])
    return out


def batch_breakout(data, days, first):
    out = []
    for sym, rows in data.items():
        until = None
        closes = [r["c"] for r in rows]
        for k in range(first - 1, len(days) - 1):
            if k < 20 or not closes[k] > max(closes[k - 20:k]):
                continue
            if until is not None and days[k] < until:
                continue
            until = K.add_sessions(days[k], 20)
            row = [sym, "nb20", days[k + 1], round(rows[k + 1]["o"], 4)]
            if until in days:
                row += [until, round(rows[days.index(until)]["c"], 4)]
            out.append(row)
    return out


def strong(r):
    return r["h"] > r["l"] and (r["c"] - r["l"]) / (r["h"] - r["l"]) >= 0.8


def batch_short(data, days, first):
    out = []
    for sym, rows in data.items():
        for k in range(first, len(days)):                         # the open of session k
            t = k - 1
            if t < 1:
                continue
            if strong(rows[t - 1]) and strong(rows[t]):
                row = [sym, "C4", days[k], round(rows[k]["o"], 4)]
                if k + 1 < len(days):
                    row += [days[k + 1], round(rows[k + 1]["c"], 4)]
                out.append(row)
            o, pc = rows[k]["o"], rows[t]["c"]
            hi = max(r["h"] for r in rows[max(0, t - 251):t + 1])
            if pc > 0 and (o - pc) / pc >= 0.02 and o >= 0.98 * hi:
                a = rows[k]["p45"] if rows[k]["p45"] <= pc else rows[k]["p30"]
                out.append([sym, "C5a", days[k], round(o, 4), days[k], round(a, 4)])
                out.append([sym, "C5b", days[k], round(o, 4), days[k], round(rows[k]["p30"], 4)])
    return out


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    diffs, stats = [], {"golden": 0, "breakout": 0, "C4": 0, "C5": 0, "cases": {"golden": 0, "breakout": 0, "short": 0}}
    for case in range(n):
        kind = ("golden", "breakout", "short")[case % 3]
        if kind == "golden":
            days = days_from(rnd, rnd.randint(230, 420))
            data = {"SPY": series(rnd, days)}
            sl = DL.GoldenCrossSpy()
            first = 201                                           # the first session with 201 closed bars behind it
            mine = summarize(step(sl, data, days, first))
            want = sorted(batch_golden(data["SPY"], days, first), key=json.dumps)
        elif kind == "breakout":
            days = days_from(rnd, rnd.randint(60, 160))
            data = {f"N{i}": series(rnd, days) for i in range(rnd.randint(2, 5))}
            sl = DL.Naive20dBreakout()
            sl.UNIVERSE = tuple(data)
            first = 1
            mine = summarize(step(sl, data, days, first))
            want = sorted(batch_breakout(data, days, first), key=json.dumps)
        else:
            days = days_from(rnd, rnd.randint(40, 120))
            data = {f"S{i}": series(rnd, days, gap_p=0.15) for i in range(rnd.randint(2, 4))}
            sl = IN.ShortCandidates()
            sl.UNIVERSE = tuple(data)
            first = 1
            mine = summarize(step(sl, data, days, first))
            want = sorted(batch_short(data, days, first), key=json.dumps)
        stats["cases"][kind] += 1
        for r in want:
            arm = r[1]
            stats[{"gc": "golden", "nb20": "breakout"}.get(arm, arm[:2])] += 1
        if mine != want:
            diffs.append({"case": case, "kind": kind, "only_sleeve": [r for r in mine if r not in want][:4],
                          "only_batch": [r for r in want if r not in mine][:4]})
        if (case + 1) % 100 == 0:
            print(f"case {case + 1}/{n} diffs={len(diffs)}", file=sys.stderr, flush=True)
    res = {"cases": n, "identical": n - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:8], "stats": stats,
           "sleeves": ["killed_golden_cross_spy", "killed_naive_20d_breakout", "killed_short_candidates (C4, C5)"],
           "method": "no committed source exists for these studies; the sleeve stepped forward on its tranche ledger "
                     "(four passes per session) vs a batch restatement of the pre-registered rule on the same random "
                     "series; every tranche's symbol, arm, entry session / price and exit session / price exact"}
    write_receipt("killed_restated", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
