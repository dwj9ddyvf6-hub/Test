"""ausar_spot_recipes parity: the SOURCE runtime — the vendored backend/public_recipe_runtime.py PublicRecipeDesk over
the real BinancePublicSpotFeed acquisition, its reducer (strategies/public_recipes/public_source_sleeves.py), sqlite
journal and replay verification intact; only HTTP (an in-memory opener serving exchangeInfo / klines / trades /
bookTicker) and the wall clock stubbed — against the port's capture feed + process() on the same tapes.

Each case: one of the three books (TOMAZETTI_RSI2 ADAUSDT 1h, IU_BODY ENJUSDT 5m, AI_VOLUME LINKUSDT 4h), 299 seed
bars + 24-48 live bars with planted setups (RSI2 washouts in an uptrend, giant bodies, volume spikes up and down),
0-4 captures after each completion (some late, some skipped), quotes with drops through the IU_BODY trailing stop,
displayed sizes from zero to deep, repeated identical bodies, crossed / off-tick bodies, acquisition failures
(metadata, klines, trades, book ticker), stale trades, a non-trading status and venue minimum / maximum stress.
Compared per capture: every fill (side, qty, price) and every cancel, plus the reducer's final cash and position.
3,000 cases (seed % 3 picks the book): 1,000 per recipe, each recipe being its own decision rules in the reducer.
Run one source process at a time (150 sequential batches of 20 cases); PARITY_CKPT=<dir> resumes a stopped run.

    python3 -m tools.parity.run ausar_spot_recipes"""
import json
import os
import random
import sys
from decimal import Decimal

from tools.parity import ROOT, write_receipt

TREE = os.path.join(ROOT, "desk", "vendor", "ausar_ctx")
N_CASES = int(os.environ.get("RECIPE_CASES", "3000"))
MKT = {"tomazetti_rsi2": ("ADAUSDT", 3600, "0.00010000", "0.10000000", (0.3, 1.2)),
       "iu_body": ("ENJUSDT", 300, "0.00010000", "0.10000000", (0.04, 0.6)),
       "ai_volume": ("LINKUSDT", 14400, "0.00100000", "0.01000000", (6.0, 30.0))}


def _grid(x, tick):
    return (Decimal(str(x)) / tick).to_integral_value() * tick


def _s(x, q="0.00000001"):
    return str(Decimal(str(x)).quantize(Decimal(q)))


def case(seed):
    rnd = random.Random(seed)
    strategy = ["tomazetti_rsi2", "iu_body", "ai_volume"][seed % 3]
    sym, step, tick_s, step_s, (lo, hi) = MKT[strategy]
    tick = Decimal(tick_s)
    n_live = rnd.randint(24, 48)
    n = 299 + n_live
    t0 = 1_700_006_400 + rnd.randint(0, 2000) * 14400
    px = rnd.uniform(lo, hi)
    vol0 = rnd.uniform(1e5, 3e6)
    rows, k_dip, after = [], 0, 0
    for i in range(n):
        o = px
        v = vol0 * rnd.uniform(0.5, 1.5)
        if strategy == "tomazetti_rsi2":
            if k_dip:
                c = o * (1 - rnd.uniform(0.004, 0.02))
                k_dip -= 1
            elif rnd.random() < 0.10:
                c = o * (1 - rnd.uniform(0.004, 0.015))
                k_dip = rnd.randint(2, 4)
            else:
                c = o * (1 + rnd.gauss(0.0045, 0.004))
        elif strategy == "iu_body":
            r = rnd.random()
            if r < 0.06:
                c = o * (1 + rnd.uniform(0.02, 0.06))            # a giant bullish body
            elif r < 0.09:
                c = o * (1 - rnd.uniform(0.02, 0.06))            # a giant bearish body
            else:
                c = o * (1 + rnd.gauss(0, 0.002))
        else:
            r = rnd.random()
            if r < 0.10:
                c = o * (1 + rnd.uniform(0.01, 0.06))
                v = vol0 * rnd.uniform(2.5, 8)                   # a bullish volume spike
            elif r < 0.15:
                c = o * (1 - rnd.uniform(0.01, 0.06))
                v = vol0 * rnd.uniform(2.5, 8)                   # a bearish volume spike
            else:
                c = o * (1 + rnd.gauss(0.002, 0.012))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.002)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, 0.002)))
        oo, hh, ll, cc = (_grid(x, tick) for x in (o, h, l, c))
        hh, ll = max(hh, oo, cc), min(ll, oo, cc)
        ll = max(ll, tick)
        rows.append([t0 + i * step, _s(oo), _s(hh), _s(ll), _s(cc), _s(round(v, 1))])
        px = float(cc)
    install = t0 + 299 * step + rnd.randint(1, step - 1)
    caps = [install]
    for i in range(299, n):
        close = t0 + (i + 1) * step
        if rnd.random() < 0.10:
            continue
        span = min(step - 1, 420)
        k = rnd.choice((1, 1, 2, 2, 3, 4))
        offs = sorted(rnd.sample(range(1, span), min(k, span - 1)))
        if rnd.random() < 0.07:
            offs = [rnd.randint(301, max(302, step - 1))] if step > 302 else []
        caps += [close + o for o in offs]
    caps = sorted(set(c for c in caps if c < t0 + n * step))
    obs, last = [], None
    for j, t in enumerate(caps):
        bar_i = min((t - t0) // step, n - 1)
        ref = Decimal(rows[max(0, bar_i - 1)][4])
        shock = 1 + (rnd.uniform(-0.06, -0.01) if rnd.random() < 0.12 else rnd.gauss(0, 0.003))
        bid = max(tick, _grid(ref * Decimal(str(shock)), tick))
        ask = bid + tick * rnd.choice((1, 1, 2, 3))
        size = (lambda: _s(rnd.choice((0, rnd.uniform(1, 40), rnd.uniform(40, 4e3), rnd.uniform(4e3, 4e5),
                                       rnd.uniform(4e5, 4e7), rnd.uniform(4e5, 4e7))), step_s))
        body = {"symbol": sym, "bidPrice": _s(bid), "bidQty": size(), "askPrice": _s(ask), "askQty": size()}
        r = rnd.random()
        if r < 0.07 and last:
            body = dict(last)
        elif r < 0.085:
            body["bidPrice"] = _s(Decimal(body["bidPrice"]) + tick / 2)
        elif r < 0.095:
            body["bidPrice"], body["askPrice"] = body["askPrice"], body["bidPrice"]
        last = body
        obs.append({"t": t, "quote": body, "trade_age": rnd.choice([rnd.randint(0, 59)] * 9 + [rnd.randint(62, 200)]),
                    "fail": {k: rnd.random() < p for k, p in (("meta", .03), ("klines", .03), ("trades", .03),
                                                                ("bt", .02))},
                    "status": "BREAK" if rnd.random() < 0.015 else "TRADING",
                    "correct": rnd.randint(1, 250) if (rnd.random() < 0.002 and j) else None})
    lim = {"min_notional": rnd.choice(("5.00000000",) * 3 + ("1.00000000", "60000.00000000")),
           "max_qty": rnd.choice(("90000000.00000000",) * 6 + ("2000.00000000",)),
           "mkt_max": rnd.choice(("0.00000000", "0.00000000", "3000000.00000000"))}
    return {"seed": seed, "strategy": strategy, "symbol": sym, "step": step, "tick": tick_s, "lot": step_s,
            "rows": rows, "install": install, "obs": obs, "lim": lim}


def klines_at(c, o):
    t, step = o["t"], c["step"]
    rows = [list(r) for r in c["rows"] if r[0] <= t]
    if o.get("correct"):
        done = [r for r in rows if r[0] + step <= t]
        if len(done) > o["correct"]:
            r = done[-o["correct"]]
            r[2] = _s(Decimal(r[2]) + Decimal(c["tick"]))
    return rows[-300:]


def exchange_info(c, o):
    lim = c["lim"]
    return {"symbols": [{"symbol": c["symbol"], "status": o["status"], "isSpotTradingAllowed": True, "quoteAsset": "USDT",
                         "baseAsset": c["symbol"][:-4],
                         "filters": [{"filterType": "PRICE_FILTER", "minPrice": c["tick"], "maxPrice": "1000.00000000",
                                      "tickSize": c["tick"]},
                                     {"filterType": "LOT_SIZE", "minQty": c["lot"], "maxQty": lim["max_qty"],
                                      "stepSize": c["lot"]},
                                     {"filterType": "MARKET_LOT_SIZE", "minQty": "0.00000000", "maxQty": lim["mkt_max"],
                                      "stepSize": "0.00000000"},
                                     {"filterType": "NOTIONAL", "minNotional": lim["min_notional"],
                                      "applyMinToMarket": True, "maxNotional": "9000000.00000000"}]}]}


def _prep(c):
    c = dict(c)
    c["klines"] = [klines_at(c, o) for o in c["obs"]]
    c["info"] = [exchange_info(c, o) for o in c["obs"]]
    return c


SOURCE_SCRIPT = r'''
import json, sys, tempfile, os, sqlite3
from datetime import datetime, timezone
sys.path.insert(0, PAYLOAD["tree"])
import backend.public_recipe_runtime as prr
CLOCK = [0.0]
def utcnow():
    CLOCK[0] += 0.001
    return datetime.fromtimestamp(CLOCK[0], timezone.utc)
prr.utcnow = utcnow
class Resp:
    def __init__(self, status, body): self.status, self.body, self.headers = status, body, {}
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self, n=-1): return self.body
def run(c):
    out = []
    obs = c["obs"]
    cur = {"i": -1}
    step = c["step"]
    def opener(req, timeout=8):
        o = obs[cur["i"]]
        url = req.full_url.split("/api/v3/", 1)[1]
        f = o["fail"]
        if url.startswith("exchangeInfo"):
            return Resp(500, b"{}") if f["meta"] else Resp(200, json.dumps(c["info"][cur["i"]]).encode())
        if url.startswith("klines"):
            return Resp(500, b"[]") if f["klines"] else Resp(200, json.dumps(
                [[r[0] * 1000, r[1], r[2], r[3], r[4], r[5], (r[0] + step) * 1000 - 1, "0", 1, "0", "0", "0"]
                 for r in c["klines"][cur["i"]]]).encode())
        if url.startswith("trades"):
            tt = int((o["t"] - o["trade_age"]) * 1000)
            return Resp(500, b"[]") if f["trades"] else Resp(200, json.dumps(
                [{"id": 1, "price": "1", "qty": "1", "quoteQty": "1", "time": tt, "isBuyerMaker": True}]).encode())
        if url.startswith("ticker/bookTicker"):
            return Resp(500, b"{}") if f["bt"] else Resp(200, json.dumps(o["quote"]).encode())
        raise AssertionError(url)
    d = tempfile.mkdtemp()
    CLOCK[0] = float(c["install"]) - 1.0
    desk = prr.PublicRecipeDesk(os.path.join(d, "recipes.sqlite"), feed=prr.BinancePublicSpotFeed(opener=opener),
                                clock=utcnow)
    desk.install(True)
    book = "PUBLIC_" + c["strategy"].upper() + "_SPOT100"
    seen = 0
    for i, o in enumerate(obs):
        cur["i"] = i
        CLOCK[0] = float(o["t"])
        try:
            cap = desk.feed.capture(c["symbol"], prr.MARKETS[c["strategy"]][1], step * 1000)
            desk.process_capture(book, cap)
            err = None
        except Exception as e:
            err = type(e).__name__ + ": " + str(e)[:160]
        db = sqlite3.connect(os.path.join(d, "recipes.sqlite"))
        rows = db.execute("SELECT rowid, payload FROM events WHERE book_id=? AND rowid>? ORDER BY rowid", (book, seen)).fetchall()
        db.close()
        for rowid, payload in rows:
            seen = rowid
            ev = json.loads(payload)
            if ev["type"] == "FILL":
                out.append([i, "fill", ev["liquidity_side"], repr(ev["qty"]), repr(ev["price"]), ev["order_id"]])
            elif ev["type"] == "CANCEL":
                out.append([i, "cancel", ev["order_id"], ev["id"].split(":", 1)[0]])
        if err:
            out.append([i, "error", err])
    st = json.loads(sqlite3.connect(os.path.join(d, "recipes.sqlite")).execute("SELECT state FROM books WHERE id=?", (book,)).fetchone()[0])
    desk.close()
    pos = st["position"]
    return {"seed": c["seed"], "events": out, "cash": repr(st["book"]["cash"]),
            "position": None if not pos else [repr(pos["qty"]), repr(pos["avg_price"]), pos.get("stop")]}
import shutil
tempfile.tempdir = BATCH_TMP = tempfile.mkdtemp(prefix="parity-recipes-")
try:
    res = [run(c) for c in PAYLOAD["cases"]]
finally:
    tempfile.tempdir = None
    shutil.rmtree(BATCH_TMP, ignore_errors=True)
print(json.dumps(res))
'''


def source_batch(cases):
    from tools.parity import old_run
    from tools.parity.batch_tmp import batch_tmp
    with batch_tmp("parity-recipes-"):        # removed here even when the child fails, times out or is killed
        return old_run(SOURCE_SCRIPT, {"tree": TREE, "cases": cases}, timeout=7200, tree=TREE)


class _Hub:
    def __init__(self, c):
        self.c, self.i, self.health = c, 0, {}
        hub = self

        class _B:
            def last_trade(self_, symbol):
                o = hub.c["obs"][hub.i]
                if o["fail"]["trades"]:
                    raise RuntimeError("HTTP 500")
                return int((o["t"] - o["trade_age"]) * 1000) / 1000.0
        self.binance = _B()

    def bars(self, source, interval, symbols, n=300):
        o = self.c["obs"][self.i]
        if o["fail"]["klines"]:
            raise RuntimeError("HTTP 500")
        step = self.c["step"]
        bl = [{"t": float(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4]),
               "v": float(r[5])} for r in self.c["klines"][self.i]]
        return {symbols[0]: [b for b in bl if b["t"] + step <= o["t"]][-n:]}

    def quotes(self, source, symbols, max_age=20):
        o = self.c["obs"][self.i]
        if o["fail"]["bt"]:
            return {}
        b = o["quote"]
        return {symbols[0]: {"bid": float(b["bidPrice"]), "ask": float(b["askPrice"]), "bid_size": float(b["bidQty"]),
                             "ask_size": float(b["askQty"]), "last": None, "t": float(o["t"])}}


def port_run(c):
    from desk.sleeves.families import ausar_spot_recipes as R

    class _Feeds:
        pass
    hub = _Hub(c)
    feeds = _Feeds()
    feeds.hub = hub
    orig = R.raw_exchange_info

    def info(symbol):
        if c["obs"][hub.i]["fail"]["meta"]:
            raise RuntimeError("HTTP 500")
        return c["info"][hub.i]
    R.raw_exchange_info = info
    try:
        row, out = R.fresh_row(c["strategy"]), []
        for i, o in enumerate(c["obs"]):
            hub.i = i
            cap = R.capture(feeds, None, float(o["t"]), c["strategy"])
            if not cap.get("quote"):
                continue
            try:
                new, fills, notes = R.process(row, cap, float(o["t"]))
            except (ValueError, KeyError, TypeError, ArithmeticError):
                continue
            row = new
            for side, qty, px, oid, action in fills:
                out.append([i, "fill", side, repr(qty), repr(px), oid])
            for n in notes:
                if isinstance(n, tuple) and n[0] == "cancel":
                    out.append([i, "cancel", n[1], {"filter-veto": "filter-veto", "depth-filter-veto": "depth-filter-veto",
                                                     "actual-fill-veto": "actual-fill-veto",
                                                     "partial-remainder": "partial-remainder-cancel",
                                                     "source_cancel": "cancel"}.get(n[2], "opening-guard-cancel")])
        pos = row["state"]["position"]
        return {"events": out, "cash": repr(row["state"]["book"]["cash"]),
                "position": None if not pos else [repr(pos["qty"]), repr(pos["avg_price"]), pos.get("stop")]}
    finally:
        R.raw_exchange_info = orig


def _norm(events):
    rank = {"cancel": 0, "fill": 1}
    return sorted([e for e in events if e[1] != "error"], key=lambda e: (e[0], json.dumps(e[1:])))


def _chunk(seeds):
    cases = [_prep(case(s)) for s in seeds]
    src = source_batch(cases)
    rows = []
    for c, s in zip(cases, src):
        p = port_run(c)
        rows.append({"seed": c["seed"], "strategy": c["strategy"], "source": _norm(s["events"]), "port": _norm(p["events"]),
                     "source_end": [s["cash"], s["position"]], "port_end": [p["cash"], p["position"]],
                     "errors": sum(1 for e in s["events"] if e[1] == "error")})
    return rows


def _chunked(name, fn, chunks):
    """run chunks one at a time (one source process alive at a time); PARITY_CKPT=<dir> keeps each finished
    chunk's rows so an interrupted run resumes where it stopped."""
    import json as _json
    ckpt = os.environ.get("PARITY_CKPT")
    if ckpt:
        os.makedirs(os.path.join(ckpt, name), exist_ok=True)
    rows = []
    for i, chunk in enumerate(chunks):
        path = os.path.join(ckpt, name, "%03d-%d.json" % (i, len(chunks))) if ckpt else None
        if path and os.path.exists(path):
            rows += _json.load(open(path))
            continue
        part = fn(chunk)
        if path:
            with open(path + ".tmp", "w") as f:
                _json.dump(part, f)
            os.replace(path + ".tmp", path)
        rows += part
    return rows


def run():
    seeds = list(range(1, N_CASES + 1))
    n_chunks = int(os.environ.get("PARITY_CHUNKS", "150"))               # 20 cases per source process
    rows = _chunked("ausar_spot_recipes", _chunk, [seeds[i::n_chunks] for i in range(n_chunks)])
    rows.sort(key=lambda r: r["seed"])
    diffs = []
    stats = {s: {"cases": 0, "buys": 0, "sells": 0, "cancels": 0, "source_cycle_errors": 0, "open_at_end": 0}
             for s in MKT}
    for r in rows:
        st = stats[r["strategy"]]
        st["cases"] += 1
        st["source_cycle_errors"] += r["errors"]
        st["open_at_end"] += 1 if r["source_end"][1] else 0
        for e in r["source"]:
            if e[1] == "fill":
                st["buys" if e[2] == "buy" else "sells"] += 1
            elif e[1] == "cancel":
                st["cancels"] += 1
        if r["source"] != r["port"] or r["source_end"] != r["port_end"]:
            diffs.append({"seed": r["seed"], "strategy": r["strategy"], "source": r["source"][:10],
                          "port": r["port"][:10], "source_end": r["source_end"], "port_end": r["port_end"]})
    res = {"cases": len(rows), "identical": len(rows) - len(diffs), "diffs": diffs[:20], "stats": stats,
           "source": {"runtime": "desk/vendor/ausar_ctx/backend/public_recipe_runtime.py (blob 5c5f529b), HTTP stubbed",
                      "reducer": "strategies/public_recipes/public_source_sleeves.py (blob 834a60ab)"},
           "named_divergences": {}}
    res["sleeves"] = ["ausar_public_tomazetti_rsi2_spot100", "ausar_public_iu_body_spot100",
                      "ausar_public_ai_volume_spot100"]
    write_receipt("ausar_spot_recipes", res)
    return dict(res, sleeve="ausar_spot_recipes")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "stats")}))
    sys.exit(1 if r["diffs"] else 0)
