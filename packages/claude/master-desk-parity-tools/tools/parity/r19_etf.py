"""R19 ETF execution parity: the SOURCE — the vendored backend/r19_etf.py evaluate (its receipt-bound etf block built
by the vendored r19_etf_data.prepare_common / enrich_snapshot over the source's own collector cache, on the XNYS / NSCC
calendar) inside the vendored backend/r19_core.py Ledger.process (bounded_snapshot, _housekeeping, _mark, _execute:
displayed size, settled cash, the margin credit, gross capacity, sale claims released at the first XNYS open after
their T+1 maturity) on its sqlite ledger, cycling every 30 s through the 09:35-09:40 window as its worker did — vs the
DESK: R19Etf (desk/sleeves/families/r19_etf.py) through the real Engine (paper mode, the venue filling at the quote),
its feed r19_etf_quotes reading the same fake Alpaca client through the vendored r19_data.Collector.refresh_quotes.

Cases draw a random book (the 26: every policy, gross and frequency), a daily tape for the 15 funds (a drift each,
one fund's November run), and each cycle's IEX top of book per fund (spreads 1-30 bp: some wider than the books'
20 bp; displayed sizes 1-5,000 shares; quote ages 0.3-4 s: some stale). Sessions: the installation week from
Monday 2026-10-19 (the fixed books' initial allocation), the November and December origins' five sessions (monthly
selection, rebalances, rotations whose buys wait for the T+1 release, retries of unfunded targets), each with
its window's ten 30 s cycles, and two cycles in each of two other sessions.

Neutralised on the source: the ledger's 20 bp mid-spread execution gate, a runtime-wide removal desk.feedlib.r19_ledger
names (its execution config max_spread_bps 1e9; the evaluator keeps its own 20 bp ask-basis rule; desk fills the
gate would have refused are counted), and margin interest, a named divergence of the wrapper (the ledger accrued on
its debt continuously, the desk charges a negative balance daily: both off, the cases with debt counted). Quote ages
avoid (1.999, 2] s, where a held name's quote turning 2 s old between the snapshot and the acknowledgement withholds
the ledger's NAV from every buy (the NAV-withheld coupling desk.feedlib.r19_ledger removes). Compared per cycle: every
fill (symbol, side, quantity, price, fee); at the end: cash net of debt with the unsettled claims, the claims,
holdings and the pending target.

    python3 -m tools.parity.run r19_etf      (R19_PARITY_JOBS worker processes, default 4; seed order kept)"""
import hashlib
import json
import math
import os
import random
import sqlite3
import sys
import types
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from tools.parity import write_receipt

UTC = timezone.utc
N_CASES = int(os.environ.get("R19_ETF_CASES", "200"))
FUNDS = ["QLD", "QQQ", "SMH", "SPY", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
LEVEL = {"QLD": 100, "QQQ": 500, "SMH": 250, "SPY": 600, "XLB": 90, "XLC": 100, "XLE": 90, "XLF": 50, "XLI": 140,
         "XLK": 230, "XLP": 80, "XLRE": 42, "XLU": 80, "XLV": 140, "XLY": 220}
START, INSTALL, END = date(2025, 6, 2), date(2026, 10, 19), date(2026, 12, 8)
WINDOWS = [date(2026, 10, d) for d in (19, 20, 21, 22, 23)] + [date(2026, 11, d) for d in (2, 3, 4, 5, 6)] + \
          [date(2026, 12, d) for d in (1, 2, 3, 4, 7)]
OTHER = [date(2026, 10, 27), date(2026, 11, 16)]


def _iso(t):
    return datetime.fromtimestamp(t, tz=UTC).isoformat()


def _norm(x, places=6):
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places)).normalize())


def _sessions():
    from desk.feedlib.r19_source import is_session
    d, out = START, []
    while d <= END:
        if is_session(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _midnight(d):
    from desk.util import ET
    return datetime(d.year, d.month, d.day, tzinfo=ET).timestamp()


def case(seed):
    from desk.sleeves.families import r19_etf as R
    rnd = random.Random(seed)
    cfg = rnd.choice(R.RULES["sleeves"])
    run = rnd.choice(FUNDS)
    closes, yahoo = {}, {}
    sessions = _sessions()
    for s in FUNDS:
        mu, px = rnd.gauss(0.0003, 0.0006), LEVEL[s] * rnd.uniform(0.8, 1.2)
        closes[s], yahoo[s] = {}, {}
        for d in sessions:
            m = mu + (0.012 if s == run and (d.year, d.month) == (2026, 11) else 0.0)
            px = max(5.0, round(px * math.exp(rnd.gauss(m, 0.01)), 2))
            closes[s][d] = px
            yahoo[s][d] = round(px * (1 + rnd.gauss(0, 0.0005)), 4)
    return {"seed": seed, "cfg": cfg, "closes": closes, "yahoo": yahoo, "sessions": sessions,
            "ids": {s: hashlib.sha1(f"asset:{s}".encode()).hexdigest()[:8] + "-0000-4000-8000-" +
                    hashlib.sha1(f"id:{s}".encode()).hexdigest()[:12] for s in FUNDS},
            "rnd_state": rnd.getstate()}


def draw_top(rnd, last):
    """each fund's IEX top of book: (bid, ask, bid size, ask size, quote age)"""
    top = {}
    for s in FUNDS:
        mid = last[s] * (1 + rnd.gauss(0, 0.002))
        bps = rnd.choice((1, 2, 3, 5, 10, 15, 19)) if rnd.random() < 0.9 else rnd.choice((22, 30))
        bid = math.floor(mid * (1 - bps / 2e4) * 100) / 100
        ask = max(math.ceil(mid * (1 + bps / 2e4) * 100) / 100, round(bid + 0.01, 2))
        sizes = (1, 3, 10, 50, 100, 200, 500, 1000, 5000)
        age = rnd.choice((0.3, 1.0, 1.7)) if rnd.random() < 0.9 else rnd.choice((2.5, 4.0))
        top[s] = (round(bid, 2), round(ask, 2), rnd.choice(sizes), rnd.choice(sizes), age)
    return top


class Client:
    """the fake Alpaca client: paper /v2/assets (the census) and data /v2/stocks/quotes/latest (the IEX top)"""
    host = "https://paper-api.alpaca.markets"

    def __init__(self, ids, clock):
        self.ids, self.clock, self.top = ids, clock, {}

    def _get(self, path, params=None, host=None):
        p = dict(params or {})
        if path == "/v2/assets":
            return [] if p.get("status") == "inactive" else [
                {"id": self.ids[s], "class": "us_equity", "exchange": "ARCA", "symbol": s, "name": s,
                 "status": "active", "tradable": True, "marginable": True, "shortable": True,
                 "easy_to_borrow": True, "fractionable": True} for s in FUNDS]
        if path == "/v2/stocks/quotes/latest":
            now = self.clock()
            return {"quotes": {s: {"bp": b, "ap": a, "bs": bs, "as": as_, "t": _iso(now - age), "bx": "V", "ax": "V",
                                   "c": ["R"], "z": "C"}
                               for s, (b, a, bs, as_, age) in self.top.items() if s in p["symbols"].split(",")}}
        raise AssertionError(path)


def _tables(c):
    """per case, once: each session's close clock and the rows both sides read (native closes, the adjusted bars
    the source's provider history is cut from, the desk's daily bars of either provider)."""
    if "_tab" not in c:
        from desk.feedlib.r19_source import DeskXNYS
        cal = DeskXNYS()
        ss = c["sessions"]
        mids = [_midnight(d) for d in ss]
        c["_tab"] = {
            "close": [cal.session_close(d).timestamp() for d in ss],
            "hist": {s: [{"session": d.isoformat(), "c": c["closes"][s][d]} for d in ss] for s in FUNDS},
            "adj": {s: [{"t": _iso(x), "c": c["closes"][s][d]} for d, x in zip(ss, mids)] for s in FUNDS},
            "bars": {(k, s): [{"t": x, "o": v[s][d], "h": v[s][d], "l": v[s][d], "c": v[s][d], "v": 1e6, "ac": v[s][d]}
                              for d, x in zip(ss, mids)]
                     for k, v in (("equity", c["closes"]), ("yahoo", c["yahoo"])) for s in FUNDS}}
    return c["_tab"]


def _done(c, now):
    """the number of sessions closed by now"""
    import bisect
    return bisect.bisect_right(_tables(c)["close"], now)


def _source_snapshot(c, col, led, now, session):
    """the R19 cycle's snapshot for its ETF books: calendar, census, raw native closes, the etf contexts
    (prepare_common over the source collector's cache), then the IEX quote refresh."""
    from desk.feedlib import r19_source as RS
    from desk.feedlib.r19_source import DeskXNYS
    import importlib
    etf_data = importlib.import_module(RS.PKG + ".r19_etf_data")
    cal = DeskXNYS()
    tab, k = _tables(c), _done(c, now)
    last = c["sessions"][k - 1]
    opened, closed = cal.session_open(session).timestamp(), cal.session_close(session).timestamp()
    census = col._assets(datetime.fromtimestamp(now, tz=UTC))
    snap = {"asof": _iso(now), "now": _iso(now), "environment": "paper", "quotes": {}, "provider_receipts": {},
            "calendar": {"session": session.isoformat(), "open": _iso(opened), "close": _iso(closed), "is_open": True,
                         "verified": True, "exchange": "XNYS", "settlement_calendar": "NSCC"},
            "assets": census["value"], "corporate_actions": [],
            "corporate_action_coverage": {"verified": True, "verified_symbols": FUNDS, "symbols": FUNDS},
            "histories": {s: tab["hist"][s][max(0, k - 300):k] for s in FUNDS}}
    received = _iso(tab["close"][k - 1] + 3600)
    adjusted = {s: {"value": {"bars": tab["adj"][s][max(0, k - 300):k]},
                    "source_sha256": hashlib.sha256(f"{s}:{last}".encode()).hexdigest(), "observed_at": received}
                for s in FUNDS}
    actions = {"value": {"verified_symbols": FUNDS}, "observed_at": received}
    snap = etf_data.prepare_common(col, snap, [], led.books(), adjusted, census, actions, last.isoformat(), cal)
    col.refresh_quotes(snap, FUNDS)
    snap["asof"] = snap["now"] = _iso(now)
    return snap


def _yahoo_cache(c, col):
    """the independent Yahoo histories the INTERVAL books read, as the source cached them after each signal close"""
    from desk.feedlib.r19_source import DeskXNYS
    cal = DeskXNYS()
    for signal in (date(2026, 9, 30), date(2026, 10, 16), date(2026, 10, 30), date(2026, 11, 30)):
        expected = [d for d in c["sessions"] if d <= signal][-252:]
        received = _iso(cal.session_close(signal).timestamp() + 3600)
        for s in FUNDS:
            value = {"history": [{"session": d.isoformat(), "close": c["yahoo"][s][d]} for d in expected],
                     "received_at": received, "source_sha256": hashlib.sha256(f"y:{s}:{signal}".encode()).hexdigest()}
            col.save("r19:etf:YAHOO:" + signal.isoformat() + ":" + s, value, received, value["source_sha256"])


def run_case(c, d):
    """both sides in lockstep over one case -> (source fills, desk fills, source end, desk end, stats); the
    desk's R19 source directory and the vendored modules' clock are restored however the case ends"""
    from desk.feedlib import r19_source as RS
    prior = os.environ.get("DESK_R19_SOURCE_DIR")
    try:
        return _run_case(c, d)
    finally:
        RS.bind_clock(None)
        if prior is None:
            os.environ.pop("DESK_R19_SOURCE_DIR", None)
        else:
            os.environ["DESK_R19_SOURCE_DIR"] = prior


def _run_case(c, d):
    import dataclasses
    from desk.engine import Engine
    from desk.feedlib import r19_ledger as L
    from desk.feedlib import r19_source as RS
    from desk.feedlib.r19_source import DeskXNYS
    from desk.feeds import Feeds
    from desk.sleeves.families import r19_etf as R
    from desk.util import ET
    from tests.fakes import FakeAlpaca
    m = RS.vendored()
    core, cli = m["r19_core"], m["r19_cli"]
    import importlib
    ve = importlib.import_module(RS.PKG + ".r19_etf")
    cal = DeskXNYS()
    cfg = c["cfg"]
    registered = next(x for x in ve.register() if x["id"] == cfg["id"])
    rnd = random.Random()
    rnd.setstate(c["rnd_state"])
    t = [cal.session_open(INSTALL).timestamp() - 1800]
    client = Client(c["ids"], lambda: t[0])
    RS.bind_clock(lambda: t[0])
    # source: its ledger (the clock advances a microsecond per read, as the worker's wall clock did), its collector
    tick = [t[0], 0]

    def clk():
        tick[1] += 1
        return datetime.fromtimestamp(tick[0] + tick[1] * 1e-6, tz=UTC)
    led = core.Ledger(os.path.join(d, "r19.sqlite"), clock=clk)
    led.install([dict(registered, max_spread_bps=1e9, margin=dict(registered["margin"], annual_interest=0))],
                enabled=True, at=_iso(t[0]))
    col = m["r19_data"].Collector(os.path.join(d, "source"), getter=RS.alpaca_getter(client, lambda: t[0]))
    _yahoo_cache(c, col)

    def evaluate(snapshot, book):                      # the evaluator sees the registered config
        return ve.evaluate(snapshot, dict(book, config=registered))
    # desk: the real engine, the feed on its own collector directory, the venue filling at the same top of book
    os.environ["DESK_R19_SOURCE_DIR"] = os.path.join(d, "desk_r19")
    top = {}

    class Hub:
        alpaca = types.SimpleNamespace(c=client)
        health = {}

        def equity_source(self):
            return "alpaca"

        def resolve(self, source):
            return source

        def bars(self, source, interval, symbols, n=300, cache_only=False):
            k, rows = _done(c, t[0]), _tables(c)["bars"]
            key = "yahoo" if source == "yahoo" else "equity"
            return {s: [dict(b) for b in rows[(key, s)][max(0, k - n):k]] for s in symbols if (key, s) in rows}

        def quotes(self, source, symbols, max_age=20):
            return {s: {"bid": top[s][0], "ask": top[s][1], "last": top[s][1], "t": t[0] - 1} for s in symbols if s in top}

    class Broker(FakeAlpaca):
        def account(self):
            return {"equity": "100000"}

        def asset(self, sym):
            return {"fractionable": True, "shortable": True, "easy_to_borrow": True}
    hub, broker = Hub(), Broker()
    feeds = Feeds(hub, None, lambda: t[0])
    for name, fn in R.FEEDS.items():
        feeds.register(name, fn)
    sl = next(s for s in R.sleeves() if s.rule["id"] == cfg["id"])
    sl.CONFIG = dataclasses.replace(sl.CONFIG, params=dict(sl.CONFIG.params, margin_rate=0))   # carry: off
    sid = sl.CONFIG.sleeve_id
    eng = Engine({"mode": "paper", "replica_utilization": 1.0}, [sl], os.path.join(d, "desk"), broker=broker, hub=hub,
                 clock=lambda: t[0], feeds=feeds, sleep=lambda s: None)
    ledger_path = os.path.join(d, "desk", "state", "ledger.jsonl")
    cycles = []
    for day in WINDOWS:
        cycles += [cal.session_open(day).timestamp() + 300 + 30 * k for k in range(10)]
    for day in OTHER:
        cycles += [cal.session_open(day).timestamp() + 300 + 30 * k for k in sorted(rnd.sample(range(10), 2))]
    cycles.sort()
    src, desk, seen_src, seen_desk = [], [], 0, 0
    stats = {"gate_would": 0, "blocked_cycles": 0, "debt_cycles": 0, "t1_waits": 0}
    for i, now in enumerate(cycles):
        session = datetime.fromtimestamp(now, tz=ET).date()
        last = {s: c["closes"][s][c["sessions"][_done(c, now) - 1]] for s in FUNDS}
        top.clear()
        top.update(draw_top(rnd, last))
        client.top = top
        broker.quotes = {s: {"bid": v[0], "ask": v[1]} for s, v in top.items()}
        t[0] = now
        # source: one worker cycle for this book
        snap = _source_snapshot(c, col, led, now, session)
        book = cli._current_book(led, cfg["id"])
        tick[0], tick[1] = now + 0.001, 0
        try:
            res = led.process(cfg["id"], cli.bounded_snapshot(snap, book), evaluate)
            if res.get("blockers"):
                stats["blocked_cycles"] += 1
        except Exception as e:                          # a failed cycle changes nothing (r19_cli book_error)
            src.append([i, "error", type(e).__name__, str(e)[:120]])
        con = sqlite3.connect(os.path.join(d, "r19.sqlite"))
        for seq, kind, payload in con.execute("SELECT seq,kind,payload_json FROM r19_events WHERE book_id=? AND seq>? "
                                              "ORDER BY seq", (cfg["id"], seen_src)).fetchall():
            seen_src = seq
            if kind == "fill":
                p = json.loads(payload)
                src.append([i, p["symbol"], p["side"], _norm(p["quantity"]), _norm(p["price"]), _norm(p["fee"])])
        con.close()
        after = next(x for x in led.books() if x["id"] == cfg["id"])
        if Decimal(after["debt"]) > 0:
            stats["debt_cycles"] += 1
        pend = (after["state"].get("pending_target") or {}).get("payload", {}).get("target_units") or {}
        if after["receivables"] and any(int(Decimal(after["positions"].get(s, {}).get("quantity", 0))) < int(q)
                                        for s, q in pend.items()):
            stats["t1_waits"] += 1
        # desk: the engine's pass at now
        eng.run_pass()
        with open(ledger_path) as f:
            rows = f.readlines()
        for line in rows[seen_desk:]:
            r = json.loads(line)
            if r.get("kind") == "book_fill" and r.get("sleeve") == sid:
                sym = r["inst"].split(":", 1)[1]
                desk.append([i, sym, r["side"], _norm(r["qty"]), _norm(r["price"]), _norm(r["fee"])])
                b, a = Decimal(str(top[sym][0])), Decimal(str(top[sym][1]))
                if (a - b) / ((a + b) / 2) * 10000 > Decimal(str(cfg["maximum_spread_bps"])):
                    stats["gate_would"] += 1
        seen_desk = len(rows)
    book = next(x for x in led.books() if x["id"] == cfg["id"])
    claims = sum((Decimal(x["amount"]) for x in book["receivables"]), Decimal(0))
    pend = (book["state"].get("pending_target") or {}).get("payload", {}).get("target_units")
    end_src = {"cash": _norm(Decimal(book["cash"]) - Decimal(book["debt"]) + claims), "unsettled": _norm(claims),
               "positions": {s: _norm(p["quantity"]) for s, p in sorted(book["positions"].items())},
               "pending": {s: int(q) for s, q in sorted(pend.items())} if pend else None}
    dbook = eng.books.get(sid)
    st = eng.store.sleeve_get(sid) or {}
    dp = (st.get("pending") or {}).get("target")
    end_desk = {"cash": _norm(dbook.cash), "unsettled": _norm(L.unsettled(st.get("ledger") or L.fresh())),
                "positions": {i_.split(":", 1)[1]: _norm(p["qty"]) for i_, p in sorted(dbook.positions.items())},
                "pending": {s: int(q) for s, q in sorted(dp.items())} if dp else None}
    return src, desk, end_src, end_desk, dict(stats, cycles=len(cycles))


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
    diffs = []
    stats = {"cycles": 0, "fills_buy": 0, "fills_sell": 0, "multi_fill_orders": 0, "rotations": 0, "t1_wait_cycles": 0,
             "source_errors": 0, "source_blocked_cycles": 0, "spread_gate_would_refuse": 0, "cases_with_debt": 0,
             "by_policy": {}, "by_gross": {}}
    jobs = max(1, int(os.environ.get("R19_PARITY_JOBS", "4")))          # cases are independent: seed order kept
    with ProcessPoolExecutor(jobs) as ex:
        results = list(ex.map(_one, range(1, N_CASES + 1), chunksize=2))
    for seed, cfg, src, desk, end_src, end_desk, st in results:
        c = {"cfg": cfg}
        fills = [e for e in src if e[2] in ("buy", "sell")]
        stats["cycles"] += st["cycles"]
        stats["spread_gate_would_refuse"] += st["gate_would"]
        stats["source_blocked_cycles"] += st["blocked_cycles"]
        stats["t1_wait_cycles"] += st["t1_waits"]
        stats["cases_with_debt"] += 1 if st["debt_cycles"] else 0
        stats["source_errors"] += sum(1 for e in src if e[1] == "error")
        for e in fills:
            stats["fills_" + e[2]] += 1
        per = {}
        for e in fills:
            per[(e[1], e[2], e[0] // 10)] = per.get((e[1], e[2], e[0] // 10), 0) + 1
        stats["multi_fill_orders"] += sum(1 for v in per.values() if v > 1)
        sold = {e[1] for e in fills if e[2] == "sell"}
        stats["rotations"] += 1 if any(e[2] == "buy" and e[1] not in sold for e in fills if sold) else 0
        pol = c["cfg"]["policy"]
        stats["by_policy"][pol] = stats["by_policy"].get(pol, 0) + 1
        g = str(c["cfg"]["gross_target"])
        stats["by_gross"][g] = stats["by_gross"].get(g, 0) + 1
        if fills != desk or end_src != end_desk:
            diffs.append({"seed": seed, "cfg": c["cfg"]["id"], "source": fills[:12], "desk": desk[:12],
                          "source_end": end_src, "desk_end": end_desk})
    from desk.sleeves.families import r19_etf as R
    res = {"cases": N_CASES, "identical": N_CASES - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:20],
           "stats": stats,
           "source": {"evaluator": "desk/vendor/ausar_r19/r19_etf.py (blob eeaf26d3) + r19_etf_data.py prepare_common",
                      "ledger": "desk/vendor/ausar_r19/r19_core.py Ledger.process / _execute (blob e12a2bf6)",
                      "cycle": "desk/vendor/ausar_r19/r19_cli.py bounded_snapshot; r19_data.Collector.refresh_quotes"},
           "port": "desk/sleeves/families/r19_etf.py R19Etf through desk.engine.Engine (paper, venue at the quote) + "
                   "desk/feedlib/r19_ledger.py settlement claims",
           "named_divergences": {"spread_gate_removed_fills": stats["spread_gate_would_refuse"],
                                 "margin_interest_neutralised_cases": stats["cases_with_debt"],
                                 "nav_withheld_coupling": "not exercised (quote ages avoid (1.999, 2] s)"},
           "sleeves": sorted(x["id"].lower() for x in R.RULES["sleeves"])}
    write_receipt("r19_etf", res)
    return dict(res, sleeve="r19_etf")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "stats")}))
    sys.exit(1 if r["diffs"] else 0)
