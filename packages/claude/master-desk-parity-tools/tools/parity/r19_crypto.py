"""R19 crypto execution parity: the SOURCE — the vendored backend/r19_crypto.py evaluate inside the vendored
backend/r19_core.py Ledger.process (r19_cli.bounded_snapshot, _housekeeping, _mark, _execute: one order per signal and
side, each fill min(remaining, displayed size net of what the book took from that depth snapshot), the 5-minute entry
window, owned exits sold in displayed-size slices, cash credited at once) on its sqlite ledger, cycling every 30 s as
its worker did — vs the DESK: R19Crypto (desk/sleeves/families/r19_crypto.py) through the real Engine on sim:binance.

A fake Binance serves both sides one capture per cycle, built by the wrapper's own capture(): contiguous native 4h
klines (a calm random tape, then a breakout bar or a bear-volume shock and its confirmation, then random bars), USD-M
funding settled every 8 h with random signs, the depth's top of book (spreads 1-150 bp, displayed sizes from a dollar
to $300k), native filters and a last trade 1-120 s old; the sim fills at that same top of book. Cases draw a random
book (3 symbols x 18 books: every family, exit policy and capacity). Cycles: passes inside each 4h window (entries,
structural triggers, owed-exit starts) — all ten in the entry's window; elsewhere the first, the pass at +300 s (where
the desk's 30 s passes, as the worker's next cycle, retire an expired entry window and free its slot: live passes
start 30 s apart, so one falls in every window's last 30 s) and random others —, every 30 s while the source book
holds units whose owned exit is due (the desk's owed-exit clock), and random passes elsewhere (where neither acts).

The source runs with the ledger's spread gate neutralised (its execution config max_spread_bps 1e9; the evaluator
still sees the books' 100 bp entry rule) — the gate desk.feedlib.r19_ledger removes runtime-wide; the desk fills it
would have refused are counted. Compared per cycle: every fill (side, quantity, price, fee); at the end: cash and
holdings (quantities to 1e-6, the desk book's float sums against the native 0.01 / 0.1 lots; money to 1e-9).

    python3 -m tools.parity.run r19_crypto      (R19_PARITY_JOBS worker processes, default 4; seed order kept)"""
import json
import os
import random
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from tools.parity import write_receipt

UTC = timezone.utc
STEP = 14400
N_CASES = int(os.environ.get("R19_CRYPTO_CASES", "300"))
T0 = 1_788_000_000 - 1_788_000_000 % STEP                   # a UTC 4h boundary (2026-08-29)
FILTERS = {"ADAUSDT": (0.5, "0.0001", "0.1", "0.1"), "ENJUSDT": (0.03, "0.00001", "0.1", "0.1"),
           "LINKUSDT": (12.0, "0.01", "0.01", "0.01")}      # price, tick, step, minimum quantity


def _iso(t):
    return datetime.fromtimestamp(t, tz=UTC).isoformat()


def _cfgs():
    from desk.sleeves.families import r19_crypto as F
    return [c for c in F.vc.register() if not c.get("collector_only")]


def tape(rnd, sym, n, event_at, family):
    """n bars from T0: a calm walk, the family's trigger at bar `event_at`, then a random walk."""
    p0, tick = FILTERS[sym][0], Decimal(FILTERS[sym][1])

    def r(x):
        return float((Decimal(repr(x)) / tick).to_integral_value() * tick)
    bars, c = [], p0
    for i in range(n):
        o = c
        if i == event_at and family in ("breakout_base", "negative_funding_squeeze"):
            hi = max(b["h"] for b in bars[-20:])
            c = hi * (1 + rnd.uniform(0.002, 0.03))
            v = 1e6 * rnd.uniform(1, 3)
        elif i == event_at - 1 and family.startswith("absorption"):
            c = o * (1 - rnd.uniform(0.02, 0.05))
            v = 1e6 * rnd.uniform(2.6, 5)                    # a bear volume shock below EMA50
        elif i == event_at and family.startswith("absorption"):
            prev = bars[-1]
            c = max(o * (1 + rnd.uniform(0.005, 0.03)), (prev["h"] + prev["l"]) / 2 * 1.002)
            v = 1e6 * rnd.uniform(0.8, 2)
        else:
            drift = rnd.gauss(0, 0.004) if i < event_at - 1 else rnd.gauss(-0.002, 0.012)
            c = max(o * (1 + drift), p0 * 0.2)
            v = 1e6 * rnd.uniform(0.6, 1.4)
        o, c = r(o), r(c)
        h, lo = r(max(o, c) * (1 + rnd.uniform(0, 0.003))), r(min(o, c) * (1 - rnd.uniform(0, 0.003)))
        bars.append({"t": float(T0 + i * STEP), "o": o, "h": max(h, o, c), "l": min(lo, o, c), "c": c, "v": round(v, 1)})
    return bars


class Market:
    """the fake Binance of one case: klines, funding, depth / filters / last trade, and the sim's quote."""

    def __init__(self, sym, bars, funding, clock):
        self.sym, self.all, self.funding, self.clock = sym, bars, funding, clock
        self.health, self.alpaca, self.cache = {}, None, None
        self.top = None                                      # (bid, ask, bid_size, ask_size, trade_age, update_id)
        m = self

        class Spot:
            def depth(self_, symbol, limit=5):
                b, a, bs, as_, _, uid = m.top
                return {"bids": [[b, bs]], "asks": [[a, as_]], "lastUpdateId": uid}

            def exchange_info(self_, symbol):
                _, tick, step, minimum = FILTERS[symbol]
                return {"qty_step": step, "price_tick": tick, "minimum_qty": minimum, "maximum_qty": "9000000",
                        "minimum_notional": "5"}

            def last_trade(self_, symbol):
                return m.clock() - m.top[4]

        class Futures:
            def funding_history(self_, symbol, limit=60):
                return [{"t": t, "rate": r} for t, r in m.funding if t <= m.clock()][-limit:]

        self.binance, self.binance_futures = Spot(), Futures()

    def equity_source(self):
        return "yahoo"

    def resolve(self, source):
        return source

    def bars(self, source, interval, symbols, n=300, cache_only=False):
        return {self.sym: [b for b in self.all if b["t"] + STEP <= self.clock()][-n:]}

    def quotes(self, source, symbols, max_age=20):
        b, a = self.top[0], self.top[1]
        return {self.sym: {"bid": float(b), "ask": float(a), "t": self.clock()}}


def draw_top(rnd, sym, mid, uid):
    _, tick, step, _ = FILTERS[sym]
    tick, step = Decimal(tick), Decimal(step)
    bps = Decimal(str(rnd.choice((1, 2, 3, 5, 10, 30, 80, 150) if rnd.random() < 0.15 else (1, 2, 3, 5, 10))))
    m = Decimal(repr(mid))
    bid = (m * (1 - bps / 20000) / tick).to_integral_value(rounding=ROUND_FLOOR) * tick
    ask = max((m * (1 + bps / 20000) / tick).to_integral_value(rounding=ROUND_CEILING) * tick, bid + tick)

    def size():
        usd = Decimal(str(rnd.choice((1, 4, 20, 150, 2000, 30000, 300000))))
        return max(step, (usd / m / step).to_integral_value(rounding=ROUND_FLOOR) * step)
    age = rnd.choice((1, 3, 5, 20, 59)) if rnd.random() < 0.9 else rnd.choice((61, 120))
    return (str(bid), str(ask), str(size()), str(size()), age, uid)


def case(seed):
    rnd = random.Random(seed)
    cfg = rnd.choice(_cfgs())
    act = 345 + rnd.randint(0, 3)                          # the books' activation bar: 340 served bars, >= 300 seeded
    event = act + rnd.randint(1, 3)
    n = act + 40
    bars = tape(rnd, cfg["symbol"], n, event, cfg["family"])
    funding = [(float(t), rnd.choice((-0.0002, -0.00003, 0.00001, 0.0001))) for t in
               range(T0 - T0 % 28800, T0 + n * STEP, 28800)]
    close = T0 + (event + 1) * STEP                       # the signal bar's close: its latest settlement, 3 times in
    want = {"negative_funding_squeeze": -0.0002, "absorption_negative_funding": -0.00003,     # 4 of the family's sign
            "absorption_nonnegative_funding": 0.00001}.get(cfg["family"])
    if want is not None and rnd.random() < 0.75:
        last = max(k for k, (ts, _) in enumerate(funding) if ts <= close)
        funding[last] = (funding[last][0], want)
    return {"seed": seed, "cfg": cfg, "bars": bars, "funding": funding, "act": act, "event": event, "n": n,
            "rnd_state": rnd.getstate()}


def _owed(book, now):
    """the source book holds units whose owned exit is due (its deadline or scheduled structural exit)."""
    for p in book["positions"].values():
        meta = p.get("metadata") or {}
        if not meta.get("exit_due_at"):
            continue
        from desk.sleeves.families import r19_crypto as F
        due = F.vc.stamp(meta["exit_due_at"])
        tr = (book.get("state") or {}).get("exit_trigger")
        if tr and tr.get("signal_id") == meta.get("signal_id"):
            due = min(due, F.vc.stamp(tr["execute_at"]))
        if now >= due.timestamp():
            return True
    return False


def _norm(x, places=9):
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places)).normalize())


def run_case(c, d):
    """both sides in lockstep over one case -> (source, desk, stats)."""
    from desk.engine import Engine
    from desk.feedlib import r19_source as RS
    from desk.feeds import Feeds
    from desk.sleeves.families import r19_crypto as F
    m = RS.vendored()
    core, cli = m["r19_core"], m["r19_cli"]
    cfg, sym = c["cfg"], c["cfg"]["symbol"]
    rnd = random.Random()
    rnd.setstate(c["rnd_state"])
    t = [float(T0 + c["act"] * STEP + 30)]
    mk = Market(sym, c["bars"], c["funding"], lambda: t[0])
    clock = [t[0]]
    led = core.Ledger(os.path.join(d, "r19.sqlite"), clock=lambda: datetime.fromtimestamp(clock[0], tz=UTC))
    led.install([dict(cfg, max_spread_bps=1e9)], enabled=True, at=_iso(t[0]))     # the ledger's spread gate: off
    bid = cfg["id"]

    def evaluate(snapshot, book):                       # the evaluator keeps the books' own 100 bp entry rule
        return F.vc.evaluate(snapshot, dict(book, config=dict(book["config"], max_spread_bps=100)))
    feeds = Feeds(mk, None, lambda: t[0])
    for name, fn in F.FEEDS.items():
        feeds.register(name, fn)
    sid = cfg["id"].lower()
    eng = Engine({"mode": "sim"}, [s for s in F.sleeves() if s.CONFIG.sleeve_id == sid], os.path.join(d, "desk"),
                 hub=mk, clock=lambda: t[0], feeds=feeds, sleep=lambda s: None)
    ledger_path = os.path.join(d, "desk", "state", "ledger.jsonl")
    seen_src, seen_desk, uid = 0, 0, 0
    src, desk, gate_would = [], [], 0
    cycles = []
    entry_window = T0 + (c["event"] + 2) * STEP             # the signal bar's close + 4 h: the entry's 300 s
    for k in range(1, c["n"] - c["act"] - 1):              # the windows after activation
        b = T0 + (c["act"] + k) * STEP
        js = range(1, 11) if b == entry_window else sorted({1, 10} | set(rnd.sample(range(2, 10), rnd.randint(0, 3))))
        cycles += [b + 30 * j for j in js]
        if rnd.random() < 0.3:
            cycles.append(b + rnd.randint(700, STEP - 700))
    cycles = [t[0]] + cycles
    i, done = 0, -1e18
    while i < len(cycles):
        now = float(cycles[i])
        if now - done < 30:                                 # the worker's and the desk's 30 s cycle
            i += 1
            continue
        done = now
        last = c["bars"][max(0, int((now - T0) // STEP) - 1)]["c"]
        uid += 1
        mk.top = draw_top(rnd, sym, last * (1 + rnd.gauss(0, 0.001)), uid)
        t[0] = clock[0] = now
        # source: one worker cycle — the same capture, bounded per book, Ledger.process at now + 1 ms
        cap = F.capture(feeds, None, now, sym)
        snap = {"asof": _iso(now), "now": _iso(now), "quotes": {sym: cap["quote"]} if cap.get("quote") else {},
                "crypto": {sym: cap}}
        book = next(x for x in led.books() if x["id"] == bid)
        clock[0] = now + 0.001
        try:
            led.process(bid, cli.bounded_snapshot(snap, book), evaluate)
        except Exception as e:                              # a failed cycle changes nothing (r19_cli book_error)
            src.append([i, "error", type(e).__name__])
        con = sqlite3.connect(os.path.join(d, "r19.sqlite"))
        for seq, kind, payload in con.execute("SELECT seq,kind,payload_json FROM r19_events WHERE book_id=? AND seq>? "
                                              "ORDER BY seq", (bid, seen_src)).fetchall():
            seen_src = seq
            if kind == "fill":
                p = json.loads(payload)
                src.append([i, p["side"], _norm(p["quantity"], 6), _norm(p["price"]), _norm(p["fee"])])
        con.close()
        # desk: the engine's pass at now (the sleeve acts when its clock is open)
        t[0] = now
        eng.run_pass()
        with open(ledger_path) as f:
            rows = f.readlines()
        for line in rows[seen_desk:]:
            r = json.loads(line)
            if r.get("kind") == "book_fill" and r.get("sleeve") == sid:
                desk.append([i, r["side"], _norm(r["qty"], 6), _norm(r["price"]), _norm(r["fee"])])
                bb, aa = Decimal(mk.top[0]), Decimal(mk.top[1])
                if (aa - bb) / ((aa + bb) / 2) * 10000 > 100:
                    gate_would += 1
        seen_desk = len(rows)
        # the source worker cycles every 30 s: while an owned exit is due, the next cycle comes 30 s later (within the
        # tape: a remainder the native filters refuse — below the minimum quantity or notional — stays owed on both)
        book = next(x for x in led.books() if x["id"] == bid)
        nxt = cycles[i + 1] if i + 1 < len(cycles) else None
        if _owed(book, now) and (nxt is None or nxt > now + 30) and now + 30 < T0 + (c["n"] - 1) * STEP:
            cycles.insert(i + 1, now + 30)
        i += 1
    book = next(x for x in led.books() if x["id"] == bid)
    dbook = eng.books.get(sid)
    inst = f"SPOT:BINANCE:{sym}"
    end_src = [_norm(book["cash"]), {s: _norm(p["quantity"], 6) for s, p in book["positions"].items()}]
    end_desk = [_norm(dbook.cash), {sym: _norm(p["qty"], 6) for i_, p in dbook.positions.items() if i_ == inst}]
    return src, desk, end_src, end_desk, {"cycles": len(cycles), "gate_would": gate_would,
                                          "owed_at_end": int(bool(book["positions"]) and _owed(book, t[0]))}


def _one(seed):
    """one case, in a worker process: (seed, config, source fills, desk fills, source end, desk end, stats)"""
    from desk.feedlib import r19_source as RS
    from tools.parity.batch_tmp import case_tmp
    RS.install_shims()
    c = case(seed)
    with case_tmp() as d:
        src, desk, end_src, end_desk, st = run_case(c, d)
    return seed, c["cfg"], src, desk, end_src, end_desk, st


def run():
    from concurrent.futures import ProcessPoolExecutor
    diffs, stats = [], {"cycles": 0, "fills_buy": 0, "fills_sell": 0, "partial_entries": 0, "sliced_exits": 0,
                        "source_errors": 0, "spread_gate_would_refuse": 0, "owed_remainder_at_tape_end": 0,
                        "by_family": {}, "by_policy": {}}
    jobs = max(1, int(os.environ.get("R19_PARITY_JOBS", "4")))          # cases are independent: seed order kept
    with ProcessPoolExecutor(jobs) as ex:
        results = list(ex.map(_one, range(1, N_CASES + 1), chunksize=2))
    for seed, cfg, src, desk, end_src, end_desk, st in results:
        c = {"cfg": cfg}
        stats["cycles"] += st["cycles"]
        stats["spread_gate_would_refuse"] += st["gate_would"]
        stats["owed_remainder_at_tape_end"] += st["owed_at_end"]
        stats["source_errors"] += sum(1 for e in src if e[1] == "error")
        fills = [e for e in src if e[1] in ("buy", "sell")]
        for e in fills:
            stats["fills_" + e[1]] += 1
        buys = [e for e in fills if e[1] == "buy"]
        sells = [e for e in fills if e[1] == "sell"]
        stats["partial_entries"] += 1 if len(buys) > 1 else 0
        stats["sliced_exits"] += 1 if len(sells) > 1 else 0
        stats["by_family"][c["cfg"]["family"]] = stats["by_family"].get(c["cfg"]["family"], 0) + 1
        stats["by_policy"][c["cfg"]["exit_policy"]] = stats["by_policy"].get(c["cfg"]["exit_policy"], 0) + 1
        if fills != desk or end_src != end_desk:
            diffs.append({"seed": seed, "cfg": c["cfg"]["id"], "source": fills[:12], "desk": desk[:12],
                          "source_end": end_src, "desk_end": end_desk})
    res = {"cases": N_CASES, "identical": N_CASES - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:20],
           "stats": stats,
           "source": {"evaluator": "desk/vendor/ausar_r19/r19_crypto.py (blob b38e9d61)",
                      "ledger": "desk/vendor/ausar_r19/r19_core.py Ledger.process / _execute (blob e12a2bf6)",
                      "cycle": "desk/vendor/ausar_r19/r19_cli.py bounded_snapshot"},
           "port": "desk/sleeves/families/r19_crypto.py R19Crypto through desk.engine.Engine (sim:binance) + "
                   "desk/feedlib/r19_ledger.py",
           "named_divergences": {"spread_gate_removed_fills": stats["spread_gate_would_refuse"]},
           "sleeves": sorted(c["id"].lower() for c in _cfgs())}
    write_receipt("r19_crypto", res)
    return dict(res, sleeve="r19_crypto")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "stats")}))
    sys.exit(1 if r["diffs"] else 0)
