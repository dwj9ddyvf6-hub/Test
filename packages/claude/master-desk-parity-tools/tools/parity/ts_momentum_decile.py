"""ts_momentum_decile: old mode_rank + mode_fill (the monthly rebalance) vs the restored port's rank + fill pass.

Synthetic genomes on first trading days: random walks of 450 completed sessions with momentum leaders, a SEMI
cluster that crowds the decile (sector cap), names under the $1M median dollar volume, short histories and
the bankruptcy-artifact signature (a +600% month after 3 flat months). The OLD rank gets what its top-up
produced at 10:00 — the last 400 bars including today's partial session — with the earnings blackout and
the Decision #86 park off (cutover doctrine); its fill runs with the desk gates proceeding (drawdown brake,
Decision #75, context gate, 150% cap) and prices buys at the partial session's close. The port ranks the
completed bars at 10:00 and fills on the next pass at a quote whose mid is that same price. Compared: the
staged buys / sells / sector-capped decile, the sells submitted (symbol, qty) and the buys (symbol, qty)."""
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.families.femto_specs import _holiday_list
from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, trading_dates, write_receipt

F = femto_module("ts_momentum_decile")
ET = ZoneInfo("America/New_York")
TODAYS = ("2026-03-02", "2026-06-01", "2026-09-01", "2026-12-01", "2026-04-01", "2026-07-01")
N_CASES = 24

OLD = r'''
import sys, types
import desk as _pkg
import sleeve_core as core
import ts_momentum_decile as O
O.NEW_ENTRIES_PAUSED = False


def mod(name, top=False, **fns):
    m = types.ModuleType(name if top else "desk." + name)
    for k, v in fns.items():
        setattr(m, k, v)
    if top:
        sys.modules[name] = m
    else:
        sys.modules["desk." + name] = m
        setattr(_pkg, name, m)


mod("earnings", top=True, is_blackout=lambda s, d: False)
mod("desk_exposure", top=True, check_cap=lambda equity, add, data=None: (True, 0.0, 0.0),
    clamp_exit_qty=lambda sym, q, sleeve=None: (q, ""))
mod("drawdown_brake", check_drawdown=lambda: ("ok", ""), log_activation=lambda *a, **k: None)
mod("decision75", pre_buy=lambda *a, **k: "proceed", sweep_releases=lambda *a, **k: [])
mod("context_gate", check_and_log=lambda sym, sleeve: (True, ""))
mod("red_day_gate", check=lambda sym, now: (True, ""))
from datetime import datetime
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")
out = []
for c in PAYLOAD["cases"]:
    bars = {s: [list(r) for r in rows] for s, rows in c["bars"].items()}
    now = datetime.fromisoformat(c["today"]).replace(hour=10, minute=0, tzinfo=ET)
    core.et_now = lambda now=now: now
    O.load_universe = lambda bars=bars: sorted(bars)
    O.fetch_bars = lambda symbols, today, no_fetch=False, dry_run=False, bars=bars: \
        {s: [b for b in bl if b[0] <= today] for s, bl in bars.items() if s in set(symbols)}
    core.load_cache = lambda path, bars=bars: {"bars": bars}
    STATE = {"book": c["book"], "pending": {}, "stats": {}}
    SUB = []
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    O.SL.reconcile_pending = lambda st, today: ([], [])
    O.SL.get_account = lambda c=c: {"equity": c["equity"]}

    def _sub(args, timeout=120, SUB=SUB):
        a = dict(zip(args[0::2], args[1::2]))
        SUB.append([a["--side"], a["--symbol"], float(a["--qty"])])
        return {"id": "o%d" % len(SUB), "status": "accepted"}
    O.SL.submit = _sub
    r = O.mode_rank(c["today"], dry_run=False, no_fetch=True)
    pend = dict(STATE["pending"])
    O.mode_fill(c["today"], dry_run=False)
    out.append({"pending": {k: pend.get(k) for k in ("buys", "sells", "decile", "eligible")},
                "sells": [[s, q] for side, s, q in SUB if side == "sell"],
                "buys": [[s, q] for side, s, q in SUB if side == "buy"]})
print(json.dumps(out))
'''

SEMI = ["NVDA", "AMD", "INTC", "MU", "AVGO", "QCOM", "TXN", "ADI", "AMAT", "LRCX", "KLAC", "ASML", "MCHP", "ON",
        "NXPI", "MPWR", "SWKS", "QRVO", "MRVL", "MXL"]


def _path(rnd, dates, kind):
    px = rnd.uniform(3, 400)
    dv = 10 ** rnd.uniform(5.3, 8.5)
    drift = {"leader": rnd.uniform(0.002, 0.004), "semi": rnd.uniform(0.0015, 0.0035),
             "plain": rnd.uniform(-0.0012, 0.0016)}.get(kind, 0.0)
    rows = []
    flat_from = len(dates) - rnd.randint(120, 300) if kind == "artifact" else None
    for i, d in enumerate(dates):
        if flat_from is not None and flat_from <= i < flat_from + 66:
            r = rnd.gauss(0, 0.001)                         # three flat months
        elif flat_from is not None and flat_from + 66 <= i < flat_from + 86:
            r = 0.105                                       # then a > +500% month
        else:
            r = rnd.gauss(drift, 0.02)
        o = px * (1 + rnd.gauss(0, 0.005))
        c = max(0.05, px * (1 + r))
        rows.append([d, round(o, 4), round(max(o, c) * 1.01, 4), round(min(o, c) * 0.99, 4), round(c, 4),
                     float(int(dv / c * rnd.uniform(0.5, 1.5)))])
        px = c
    return rows


def run():
    rnd = random.Random(86)
    cases = []
    for k in range(N_CASES):
        today = TODAYS[k % len(TODAYS)]
        hol = set(_holiday_list(today))
        hist = [d for d in trading_dates("2024-03-01", 800) if d < today and d not in hol][-450:]
        names = {}
        for j in range(rnd.randint(120, 260)):
            kind = rnd.choices(("plain", "leader", "artifact", "short"), (80, 12, 3, 5))[0]
            names["N%03d" % j] = kind
        for s in rnd.sample(SEMI, rnd.randint(4, len(SEMI))):
            names[s] = "semi"
        bars = {}
        for s, kind in names.items():
            rows = _path(rnd, hist, kind)
            if kind == "short":
                rows = rows[-rnd.randint(150, 300):]
            last = rows[-1][4]
            part = round(last * (1 + rnd.gauss(0, 0.01)), 4)
            rows.append([today, last, max(last, part), min(last, part), part, float(int(rows[-1][5] * 0.2))])
            bars[s] = rows
        held = rnd.sample(sorted(bars), rnd.randint(0, 40))
        book = {s: {"qty": float(rnd.choice((1, 7, 33, 120, 2.5))), "entry_px": 10.0, "entry_date": hist[-30]}
                for s in held}
        cases.append({"today": today, "bars": bars, "book": book,
                      "equity": rnd.choice((100_000.0, 250_000.0, 1_000_000.0))})
    old_cases = [dict(c, bars={s: rows[-400:] for s, rows in c["bars"].items()}) for c in cases]
    old = old_run(OLD, {"cases": old_cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"decile": 0, "staged_buys": 0, "staged_sells": 0, "sector_trims": 0, "artifact_excluded": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        today = c["today"]
        ebars = {}
        for s, rows in c["bars"].items():
            ebars[s] = [{"t": datetime.fromisoformat(r[0]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
                         "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in rows[:-1]]
        state = {s: {"position": dict(p)} for s, p in c["book"].items()}
        hol = _holiday_list(today)
        t_rank = datetime.fromisoformat(today).replace(hour=10, minute=0, tzinfo=ET).timestamp()
        ctx = fc.Context(now=t_rank, session=today, equity=c["equity"],
                         extra={"sleeve_state": state, "meta": {}, "nyse_holidays": hol})
        meta = F.next_meta(ebars, {}, ctx, [])
        p = meta.get("pending") or {}
        cmp("pending", ci, o["pending"], {k: p.get(k) for k in ("buys", "sells", "decile", "eligible")})
        quotes = {s: {"bid": rows[-1][4], "ask": rows[-1][4], "t": t_rank + 290} for s, rows in c["bars"].items()}
        ctx2 = fc.Context(now=t_rank + 300, session=today, equity=c["equity"],
                          extra={"sleeve_state": state, "meta": meta, "nyse_holidays": hol, "quotes": quotes})
        out = F.signal(ebars, {}, ctx2)
        cmp("sells", ci, o["sells"], [[i.symbol, i.qty] for i in out if i.kind == "exit"])
        cmp("buys", ci, o["buys"], [[i.symbol, i.qty] for i in out if i.kind == "enter"])
        meta2 = F.next_meta(ebars, {}, ctx2, out)
        cmp("filled", ci, True, meta2.get("filled_month") == today[:7] and not meta2.get("pending"))
        counts["decile"] += len(o["pending"]["decile"] or [])
        counts["staged_buys"] += len(o["pending"]["buys"] or [])
        counts["staged_sells"] += len(o["pending"]["sells"] or [])
        counts["sector_trims"] += len(p.get("trims") or [])
        counts["artifact_excluded"] += len(p.get("excluded_artifact") or [])
    res = {"sleeve": "ts_momentum_decile", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("ts_momentum_decile" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
