"""midna_faber / midna_lc_prior_month_reversal / midna_distance_pair_shares: the original quantpedia.ts (paper-desk
68315288) under Node vs desk/sleeves/midna/quantpedia.py, and the producer's main() vs the in-pass assembly.

Books: the source runs its real applyQuantpedia(state, now, quotes, signals) on three accounts (green.ts
buyBlockReason stubbed to "no block" — the removed desk gate; state.halted false); the port runs the same step on the
same accounts. Compared: every book's open positions (symbol, shares, pair key) and cash after the pass.
Producers: the vendored quantpedia-signals.py main() and board-signals.py main() (their fetch stubbed with the
case's rows, their clock set to the case's; file writes to a scratch path) vs desk/feedlib/midna_signals.py
qp_signals / board_signals over the same rows."""
import atexit
import json
import os
import random
import shutil
import tempfile

from desk.feedlib import midna_signals as S
from desk.sleeves.midna import common as M
from desk.sleeves.midna import quantpedia as P
from desk.vendor.midna import board_signals as B
from desk.vendor.midna import quantpedia_signals as Q

from . import write_receipt
from .midna_common import build, run_js, same, sessions_ending

N_CASES = 1500
N_PRODUCER = 300
FILES = ["src/lib/equity/quantpedia.ts", "src/lib/equity/kronos.ts", "src/lib/equity/rules.ts",
         "src/lib/equity/green.ts", "src/lib/equity/types.ts"]
SIDES = ("faber", "reversal", "pairs")

JS = r'''
const qp = require('./src/lib/equity/quantpedia.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const out = []
for (const c of PAYLOAD.cases) {
  const books = qp.blankQuantpedia(c.born)
  for (const side of ['faber', 'reversal', 'pairs']) {
    const a = books[side]
    a.cash = c.books[side].cash
    c.books[side].positions.forEach((p, k) => {
      a.positions[side + ':' + p.sym + ':2026-01-0' + (k % 9 + 1) + ':' + k] = { sym: p.sym, pairKey: p.pairKey || undefined,
        qty: p.qty, entryAvg: p.entryAvg, entryDay: '2026-01-02', openedAt: '2026-01-02T15:00:00.000Z', mark: p.mark,
        markAt: '2026-01-02T15:00:00.000Z', status: 'open' }
    })
  }
  const state = { halted: false, shadow: { quantpedia: books } }
  qp.applyQuantpedia(state, new Date(c.now * 1000), c.quotes, c.signals)
  const res = {}
  for (const side of ['faber', 'reversal', 'pairs']) {
    const a = books[side]
    res[side] = { cash: a.cash, open: Object.values(a.positions).filter((p) => p.status === 'open')
      .map((p) => [p.sym, p.qty, p.pairKey || null]) }
  }
  out.push(res)
}
console.log(JSON.stringify(out))
'''


def _signals(rnd, as_of):
    faber = [{"sym": s, "above": rnd.random() < 0.5} for s in Q.FABER if rnd.random() < 0.95]
    names = [s for s in Q.LARGE if rnd.random() < 0.9]
    reversal = sorted([{"sym": s, "ret": round(rnd.gauss(0.0, 0.08), 6)} for s in names], key=lambda r: r["ret"])
    pairs = []
    for _ in range(rnd.randint(0, 20)):
        a, b = rnd.sample(Q.LARGE, 2)
        z = rnd.choice([rnd.uniform(-4, 4), rnd.uniform(-0.6, 0.6), rnd.uniform(1.8, 2.2) * rnd.choice((-1, 1))])
        long = (a if rnd.random() < 0.5 else b) if abs(z) >= 2 else None
        pairs.append({"a": a, "b": b, "z": z, "long": long})
    return {"asOf": as_of, "faber": faber, "reversal": reversal, "pairs": pairs}


def _quote(rnd, now, base):
    last = round(base * rnd.uniform(0.97, 1.03), 2)
    q = {"last": last, "previousClose": round(base, 2), "timeMs": (now - rnd.choice([0, 20, 300, 2000])) * 1000}
    r = rnd.random()
    if r < 0.5:
        s = rnd.uniform(0.0002, 0.01)
        q["bid"], q["ask"] = round(last * (1 - s), 2), round(last * (1 + s), 2)
    elif r < 0.55:
        q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
    elif r < 0.6:
        q["ask"] = round(last * 1.002, 2)
    elif r < 0.65:
        q["bid"] = round(last * 0.998, 2)
    return q


def gen_case(rnd):
    as_of = rnd.choice(sessions_ending("2026-12-15", 230))
    roll = rnd.random()
    day = M.next_trading_day(as_of) if roll < 0.8 else (as_of if roll < 0.9 else M.next_trading_day(M.next_trading_day(as_of)))
    mins = rnd.choice([rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(570, 599),
                       rnd.randint(960, 1100)])
    now = M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))
    born = rnd.choice([as_of, M.add_days(as_of, -30), M.next_trading_day(as_of), "2026-01-01"])
    sig = _signals(rnd, as_of)
    pool = list(Q.FABER) + list(Q.LARGE)
    base = {s: rnd.choice([rnd.uniform(3, 20), rnd.uniform(20, 400)]) for s in pool}
    quotes = {s: _quote(rnd, now, base[s]) for s in pool if rnd.random() < 0.93}
    books = {}
    for side in SIDES:
        uni = list(Q.FABER) if side == "faber" else list(Q.LARGE)
        held = rnd.sample(uni, rnd.randint(0, min(5, len(uni))))
        pos = []
        for s in held:
            pk = None
            if side == "pairs":
                rows = [r for r in sig["pairs"] if s in (r["a"], r["b"])]
                pk = P.pair_key(rows[0]["a"], rows[0]["b"]) if rows and rnd.random() < 0.8 else \
                    (P.pair_key(s, rnd.choice(Q.LARGE)) if rnd.random() < 0.7 else None)
            mark = round(base[s] * rnd.uniform(0.9, 1.1), 2)
            pos.append({"sym": s, "qty": rnd.randint(1, 400), "entryAvg": round(base[s] * rnd.uniform(0.8, 1.2), 2),
                        "mark": mark, "pairKey": pk})
        books[side] = {"cash": round(rnd.choice([rnd.uniform(0, 3000), rnd.uniform(0, 100000), 100000.0]), 2),
                       "positions": pos}
    return {"now": now, "born": born, "signals": sig, "quotes": quotes, "books": books}


def port(c):
    out = {}
    quotes = {s: q for s, q in c["quotes"].items() if q and q.get("last", 0) > 0}
    for side in SIDES:
        b = c["books"][side]
        acc = P.Account(b["cash"], [dict(p, mark=(quotes[p["sym"]]["last"] if p["sym"] in quotes else p["mark"]))
                                    for p in b["positions"]])
        if c["signals"].get("asOf") and P.can_act(c["now"], c["signals"]["asOf"], c["born"]):
            P.STEPS[side](acc, quotes, c["signals"])
        out[side] = {"cash": acc.cash, "open": [[p["sym"], p["qty"], p.get("pairKey")] for p in acc.positions]}
    return out


def _producer_case(rnd, k):
    """rows for the producers: the quantpedia (day, price) rows and the board (day, h, l, c, v) rows of one clock."""
    as_of = rnd.choice(sessions_ending("2026-12-15", 200))
    now = M.et_to_epoch(M.next_trading_day(as_of), rnd.choice([3, 9, 12, 16, 20]), rnd.randint(0, 59))
    days = sessions_ending(as_of, rnd.randint(150, 520))
    qp_series = {}
    for s in list(Q.FABER) + list(Q.LARGE):
        if rnd.random() < 0.05:
            continue
        px = rnd.uniform(10, 300)
        rows = []
        start = rnd.randint(0, len(days) // 3) if rnd.random() < 0.2 else 0
        for d in days[start:]:
            px *= 1 + rnd.gauss(0.0004, 0.02)
            if rnd.random() < 0.01:
                continue
            rows.append((d, round(px, 4)))
        qp_series[s] = rows
    board = {}
    for s in rnd.sample(S.swing_universe(), k):
        px, rows = rnd.uniform(3, 200), []
        for d in days[-rnd.randint(50, min(len(days), 260)):] + ([M.et_ymd(now)] if rnd.random() < 0.3 else []):
            o = px
            px *= 1 + rnd.gauss(0.0005, 0.03)
            h, l = max(o, px) * (1 + abs(rnd.gauss(0, 0.01))), min(o, px) * (1 - abs(rnd.gauss(0, 0.01)))
            rows.append((d, round(h, 4), round(l, 4), round(px, 4), float(int(rnd.uniform(0, 5e6)))))
        board[s] = rows
    return now, qp_series, board


def producer_parity(n, rnd):
    diffs = []
    tmp = tempfile.mkdtemp(prefix="midna_qp_")
    atexit.register(shutil.rmtree, tmp, True)
    for i in range(n):
        now, qp_series, board = _producer_case(rnd, rnd.randint(5, 40))
        # quantpedia-signals.py main(): fetch stubbed, OUT redirected
        q_out = os.path.join(tmp, "qp.json")
        saved = (Q.fetch, Q.OUT)
        Q.fetch, Q.OUT = (lambda sym: list(qp_series.get(sym, []))), q_out
        try:
            with S.board_clock(now):
                Q.main.__globals__["datetime"] = S._Clock
                Q.main()
        finally:
            Q.fetch, Q.OUT = saved
            Q.main.__globals__["datetime"] = S.datetime
        src = json.load(open(q_out))
        src.pop("builtAt", None)
        mine = S.qp_signals({s: r for s, r in qp_series.items() if r})
        # board-signals.py main(): fetch stubbed, BASKET / OUT redirected, clock = now
        b_out, b_basket = os.path.join(tmp, "b.json"), os.path.join(tmp, "basket.json")
        json.dump({"symbols": list(board)}, open(b_basket, "w"))
        saved = (B.fetch, B.OUT, B.BASKET)
        B.fetch, B.OUT, B.BASKET = (lambda sym: {"rows": list(board[sym])}), b_out, b_basket
        try:
            with S.board_clock(now):
                B.main()
        finally:
            B.fetch, B.OUT, B.BASKET = saved
        bsrc = json.load(open(b_out))
        bsrc.pop("builtAt", None)
        bmine = S.board_signals(board, now)
        if not same(src, mine) or not same(bsrc, bmine):
            diffs.append({"case": i, "qp": same(src, mine), "board": same(bsrc, bmine)})
    return diffs


def run(n=N_CASES, n_prod=N_PRODUCER, seed=20261017):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    diffs, stats = [], {"orders": 0, "cases_with_orders": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(200, n - done))]
        old = run_js(work, JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            changed = sum(1 for side in SIDES if not same(p[side], {"cash": c["books"][side]["cash"],
                          "open": [[x["sym"], x["qty"], x.get("pairKey")] for x in c["books"][side]["positions"]]}))
            stats["cases_with_orders"] += changed > 0
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    pdiffs = producer_parity(n_prod, rnd)
    res = {"cases": n + n_prod, "identical": n + n_prod - len(diffs) - len(pdiffs), "diffs": (diffs + pdiffs)[:20],
           "n_diffs": len(diffs) + len(pdiffs), "stats": dict(stats, book_cases=n, producer_cases=n_prod),
           "sleeves": ["midna_faber", "midna_lc_prior_month_reversal", "midna_distance_pair_shares"],
           "method": "quantpedia.ts applyQuantpedia under Node (buyBlockReason stubbed) vs quantpedia.py steps; "
                     "vendored quantpedia-signals.py / board-signals.py main() (fetch stubbed) vs midna_signals"}
    write_receipt("midna_quantpedia", res)
    return dict(res, sleeve="midna_quantpedia")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
