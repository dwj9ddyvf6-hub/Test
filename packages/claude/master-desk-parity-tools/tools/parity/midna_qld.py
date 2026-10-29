"""midna_qld_weekly_timing: the original pullback.ts runQld / completedWeeks and pine.ts ema (entire 43f08f96) and
felipe/live.ts fetchDaily's parsing under Node vs desk/sleeves/midna/qld.py and desk/feedlib/midna_qld.py.

Cases: QQQ / QLD daily series of 300..1600 sessions (gaps, zero / missing opens, highs and lows, duplicated dates, a
holiday Friday, a series cut mid-week), with random from / to windows and costs. Compared exactly: runQld's curve
(date, equity) and trips (entry, exit, return) and open flag vs qld.run_qld; for every week of the backtest, the
source's decision (EMA12 > EMA26 on the QQQ weeks before it, runQld's index i - 1) vs qld.trend_for_week on the
days before that week's Monday (the live sleeve's decision); and, on random Yahoo chart bodies, fetchDaily's rows
vs midna_qld.parse_daily (fetch stubbed)."""
import json
import random
from datetime import date, datetime, timedelta, timezone

from desk.feedlib import midna_qld as F
from desk.sleeves.midna import common as M
from desk.sleeves.midna import qld as Q

from . import write_receipt
from .midna_common import build, run_js, same

N_CASES = 1200
FILES = ["src/lib/felipe/pullback.ts", "src/lib/lector/pine.ts", "src/lib/felipe/live.ts", "src/lib/felipe/verdict.ts"]

JS = r'''
const P = require('./src/lib/felipe/pullback.js')
const pine = require('./src/lib/lector/pine.js')
const live = require('./src/lib/felipe/live.js')
;(async () => {
  const out = []
  for (const c of PAYLOAD.cases) {
    const book = P.runQld(c.qqq, c.qld, c.opts)
    const weeks = P.completedWeeks(c.qqq)
    const fast = pine.ema(weeks.map((w) => w.close), 12)
    const slow = pine.ema(weeks.map((w) => w.close), 26)
    const on = []
    for (let i = 1; i < weeks.length; i += 1) {
      on.push([weeks[i].date, fast[i - 1] != null && slow[i - 1] != null && fast[i - 1] > slow[i - 1]])
    }
    out.push({ book, on })
  }
  const parsed = []
  for (const body of PAYLOAD.bodies) {
    globalThis.fetch = async () => ({ ok: true, json: async () => body })
    // fetchDaily is module-private: loadSeries -> fetchDaily over every symbol; read it back from its cache file
    parsed.push(await live.__fetchDailyForParity(body))
  }
  console.log(JSON.stringify({ out, parsed }))
})()
'''


def gen_days(rnd, n, start="2019-01-02"):
    d = date.fromisoformat(start)
    out, px = [], rnd.uniform(20, 300)
    while len(out) < n:
        d += timedelta(days=1)
        ymd = d.isoformat()
        if not M.is_trading_day(ymd) or rnd.random() < 0.01:
            continue
        px = max(1.0, px * (1 + rnd.gauss(0.0006, 0.018)))
        o = px * (1 + rnd.gauss(0, 0.006))
        h = max(o, px) * (1 + abs(rnd.gauss(0, 0.006)))
        lo = min(o, px) * (1 - abs(rnd.gauss(0, 0.006)))
        row = {"date": ymd, "open": round(o, 4), "high": round(h, 4), "low": round(lo, 4), "close": round(px, 4)}
        r = rnd.random()
        if r < 0.01:
            row["open"] = 0
        elif r < 0.02:
            row["low"] = 0
        elif r < 0.025:
            row["high"] = 0
        elif r < 0.03:
            row["close"] = 0
        out.append(row)
        if rnd.random() < 0.003:
            out.append(dict(row, close=round(px * 1.01, 4)))
    return out


def gen_case(rnd):
    n = rnd.randint(300, 1600)
    qqq = gen_days(rnd, n)
    qld = gen_days(rnd, n - rnd.randint(0, 120), start=rnd.choice(["2019-01-02", "2019-03-01"]))
    if rnd.random() < 0.3:                                 # cut mid-week (an unfinished last week)
        qqq = qqq[:-rnd.randint(1, 3)]
    opts = {}
    if rnd.random() < 0.6:
        opts["from"] = qqq[rnd.randint(0, len(qqq) // 2)]["date"]
    if rnd.random() < 0.4:
        opts["to"] = qqq[rnd.randint(len(qqq) // 2, len(qqq) - 1)]["date"]
    opts["cost"] = rnd.choice([0.001, 0.001, 0.0, 0.0025])
    return {"qqq": qqq, "qld": qld, "opts": opts}


def gen_body(rnd):
    n = rnd.randint(5, 60)
    t0 = int(datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc).timestamp())
    stamps, o, h, l, c, a = [], [], [], [], [], []
    for i in range(n):
        stamps.append(t0 + i * 86400 + rnd.choice([0, 0, 0, 3600 * 5]))
        px = rnd.uniform(10, 50)
        f = rnd.uniform(0.9, 1.0)
        o.append(None if rnd.random() < 0.05 else round(px * 1.01, 4))
        h.append(None if rnd.random() < 0.05 else round(px * 1.03, 4))
        l.append(None if rnd.random() < 0.05 else round(px * 0.97, 4))
        c.append(None if rnd.random() < 0.05 else (0 if rnd.random() < 0.02 else round(px, 4)))
        a.append(None if rnd.random() < 0.05 else round(px * f, 6))
    return {"chart": {"result": [{"timestamp": stamps, "indicators": {"quote": [{"open": o, "high": h, "low": l,
                                                                                "close": c}],
                                                                       "adjclose": [{"adjclose": a}]}}]}}


def port_case(c):
    book = Q.run_qld(c["qqq"], c["qld"], c["opts"].get("from"), c["opts"].get("to"), c["opts"]["cost"])
    weeks = Q.completed_weeks(c["qqq"])
    on = []
    for i in range(1, len(weeks)):
        tr = Q.trend_for_week(c["qqq"], Q.week_start(weeks[i]["date"]))
        on.append([weeks[i]["date"], bool(tr and tr[0])])
    return {"book": book, "on": on}


def patch_live(work):
    """expose live.ts's module-private fetchDaily to the harness (the file is copied, not edited in place: one
    export line appended to the compiled module, the function body untouched)."""
    import os
    p = os.path.join(work, "out", "src", "lib", "felipe", "live.js")
    src = open(p).read()
    if "__fetchDailyForParity" not in src:
        src += "\nexports.__fetchDailyForParity = async (body) => fetchDaily('QQQ');\n"
        open(p, "w").write(src)


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("entire", FILES)
    patch_live(work)
    diffs, stats = [], {"trips": 0, "weeks": 0, "on_weeks": 0, "rows": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(150, n - done))]
        bodies = [gen_body(rnd) for _ in range(len(cases))]
        old = run_js(work, JS, {"cases": cases, "bodies": bodies})
        for k, (c, o) in enumerate(zip(cases, old["out"])):
            p = port_case(c)
            stats["trips"] += len(o["book"]["trips"])
            stats["weeks"] += len(o["on"])
            stats["on_weeks"] += sum(1 for w in o["on"] if w[1])
            bad = []
            if not same(p["book"], o["book"]):
                bad.append("book")
            if p["on"] != o["on"]:
                bad.append("decisions")
            body = bodies[k]
            pr = F.parse_daily(body)
            stats["rows"] += len(pr)
            if not same(pr, old["parsed"][k]):
                bad.append("fetchDaily")
            if bad:
                diffs.append({"case": done, "bad": bad})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_qld_weekly_timing"],
           "method": "pullback.ts runQld + completedWeeks + pine.ts ema and live.ts fetchDaily (fetch stubbed) under "
                     "Node vs qld.run_qld / qld.trend_for_week / midna_qld.parse_daily; exact"}
    write_receipt("midna_qld", res)
    return dict(res, sleeve="midna_qld")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
