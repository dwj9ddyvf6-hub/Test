"""absorption parity: the SOURCE runtime — the vendored backend/absorption_runtime.py AbsorptionDesk over the real
AbsorptionPublicFeed(BinancePublicSpotFeed) acquisition, its sqlite journal and verification intact; only HTTP
(an in-memory opener serving exchangeInfo / klines / trades / bookTicker) and the wall clock stubbed — against the
port's capture feed + step() on the same tapes, one capture per pass, the desk book modelled as the engine's sim
venue fills it (the decided quantity at the observed ask / bid, 10 bps, binary cash).

Each case: 299 seed bars + 18-34 live native 4h bars of ENJUSDT or LINKUSDT (planted bear shocks and reclaim
confirmations), 0-4 captures after each completion (0-620 s, some skipped = outages), randomized quotes (sizes
from zero to deep, repeated identical bodies, off-tick and crossed bodies), metadata / klines / trades / bookTicker
failures (incl. the one-retry fallback quote), stale last trades, a non-trading status, venue minimum / maximum
stress and occasional vendor corrections of a seen bar. Compared per capture: every fill (side, qty, price) and
every signal admission / skip.

Two port runs: `same_pass` (an entry may follow an exit in the same pass, as in the source) must match the source
exactly; the deployed run (an exit and an entry never share a pass) differs only where that named divergence
fires — counted and listed.

    python3 -m tools.parity.run absorption"""
import json
import os
import random
import sys
from decimal import Decimal

from tools.parity import ROOT, write_receipt

TREE = os.path.join(ROOT, "desk", "vendor", "ausar_ctx")
STEP = 14400
N_CASES = int(os.environ.get("ABSORPTION_CASES", "1000"))
SPECS = {"ENJUSDT": {"tick": "0.00010000", "step": "0.10000000", "px": (0.04, 0.6)},
         "LINKUSDT": {"tick": "0.00100000", "step": "0.01000000", "px": (6.0, 30.0)}}


def _fmt(x, q):
    return str(Decimal(str(x)).quantize(Decimal(q)))


def _grid(x, tick):
    return (Decimal(str(x)) / tick).to_integral_value() * tick


def case(seed):
    rnd = random.Random(seed)
    sym = rnd.choice(sorted(SPECS))
    sp = SPECS[sym]
    tick = Decimal(sp["tick"])
    n_live = rnd.randint(18, 34)
    n = 299 + n_live
    t0 = 1_700_006_400 + rnd.randint(0, 400) * STEP          # a UTC 4h boundary
    px = rnd.uniform(*sp["px"])
    vol0 = rnd.uniform(2e5, 4e6) if sym == "ENJUSDT" else rnd.uniform(2e4, 3e5)
    rows, shock_next = [], False
    plant = rnd.uniform(0.12, 0.35)
    for i in range(n):
        o = px
        if shock_next:                                          # a reclaim after a planted shock (often)
            c = o * (1 + rnd.uniform(0.01, 0.10)) if rnd.random() < 0.8 else o * (1 - rnd.uniform(0, 0.03))
            v = vol0 * rnd.uniform(0.5, 2.0)
            shock_next = False
        elif rnd.random() < plant:                              # a bear volume shock
            c = o * (1 - rnd.uniform(0.01, 0.06))
            v = vol0 * rnd.uniform(1.6, 9.0)
            shock_next = True
        else:
            c = o * (1 + rnd.gauss(0, 0.018))
            v = vol0 * rnd.uniform(0.3, 1.6)
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.008)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, 0.008)))
        q8 = "0.00000001"
        oo, hh, ll, cc = (_fmt(_grid(x, tick), q8) for x in (o, h, l, c))
        hh = max(hh, oo, cc, key=Decimal)
        ll = min(ll, oo, cc, key=Decimal)
        if Decimal(ll) <= 0:
            ll = _fmt(tick, q8)
        vv = _fmt(round(v, 1 if sym == "ENJUSDT" else 2), q8)
        rows.append([t0 + i * STEP, oo, hh, ll, cc, vv])
        px = float(cc)
    install = t0 + 299 * STEP + rnd.randint(30, STEP - 700)    # inside the forming 300th bar
    caps = [install]
    for i in range(299, n):
        close = t0 + (i + 1) * STEP
        if close > t0 + n * STEP - 1 or rnd.random() < 0.12:
            continue                                            # an outage over this completion
        k = rnd.choice((1, 1, 2, 2, 3, 4))
        offs = sorted(rnd.sample(range(1, 420), k))
        if rnd.random() < 0.08:
            offs = [rnd.randint(301, 900)]                     # first seen too late
        caps += [close + o for o in offs]
    caps = sorted(set(c for c in caps if c < t0 + n * STEP))
    obs = []
    last_body = None
    for j, t in enumerate(caps):
        bar_i = (t - t0) // STEP                               # the forming bar
        ref = Decimal(rows[min(bar_i, n - 1)][1])
        spread = tick * rnd.choice((1, 1, 1, 2, 3))
        bid = max(tick, _grid(ref * Decimal(str(1 + rnd.gauss(0, 0.004))), tick))
        ask = bid + spread
        r = rnd.random()
        size = (lambda: _fmt(rnd.choice((0, rnd.uniform(1, 50), rnd.uniform(50, 5e3), rnd.uniform(5e3, 5e5),
                                         rnd.uniform(5e3, 5e5), rnd.uniform(5e5, 5e7), rnd.uniform(5e5, 5e7))),
                                  sp["step"]))
        body = {"symbol": sym, "bidPrice": _fmt(bid, "0.00000001"), "bidQty": size(),
                "askPrice": _fmt(ask, "0.00000001"), "askQty": size()}
        if r < 0.08 and last_body:
            body = dict(last_body)                              # the identical book-ticker body again
        elif r < 0.10:
            body["bidPrice"] = _fmt(Decimal(body["bidPrice"]) + tick / 2, "0.00000001")   # off the tick
        elif r < 0.11:
            body["bidPrice"], body["askPrice"] = body["askPrice"], body["bidPrice"]       # crossed
        last_body = body
        o = {"t": t, "quote": body,
             "trade_age": rnd.choice([rnd.randint(0, 59)] * 9 + [rnd.randint(62, 200)]),
             "fail": {k: rnd.random() < p for k, p in (("meta", .04), ("klines", .03), ("trades", .03),
                                                         ("bt_once", .03), ("bt_twice", .01))},
             "status": "BREAK" if rnd.random() < 0.02 else "TRADING", "correct": None}
        if rnd.random() < 0.0015 and j > 0:
            o["correct"] = rnd.randint(1, 250)                  # a vendor correction of a seen bar, k bars back
        obs.append(o)
    lim = {"min_notional": rnd.choice(("5.00000000", "5.00000000", "10.00000000", "250000.00000000")),
           "max_qty": rnd.choice(("92141578.00000000",) * 6 + ("1000.00000000",)),
           "mkt_max": rnd.choice(("0.00000000", "0.00000000", "5000000.00000000"))}
    return {"seed": seed, "symbol": sym, "spec": sp, "rows": rows, "install": install, "obs": obs, "lim": lim}


def klines_at(c, o):
    """the raw klines a capture at o['t'] sees: the last 300 rows up to and including the forming one."""
    t = o["t"]
    rows = [list(r) for r in c["rows"] if r[0] <= t]
    if o.get("correct"):
        done = [r for r in rows if r[0] + STEP <= t]
        if len(done) > o["correct"]:
            r = done[-o["correct"]]
            r[2] = str((Decimal(r[2]) + Decimal(c["spec"]["tick"])).quantize(Decimal("0.00000001")))
    return rows[-300:]


def exchange_info(c, o):
    sp, lim = c["spec"], c["lim"]
    return {"symbols": [{"symbol": c["symbol"], "status": o["status"], "isSpotTradingAllowed": True, "quoteAsset": "USDT",
                         "baseAsset": c["symbol"][:-4],
                         "filters": [{"filterType": "PRICE_FILTER", "minPrice": sp["tick"], "maxPrice": "1000.00000000",
                                      "tickSize": sp["tick"]},
                                     {"filterType": "LOT_SIZE", "minQty": sp["step"], "maxQty": lim["max_qty"],
                                      "stepSize": sp["step"]},
                                     {"filterType": "MARKET_LOT_SIZE", "minQty": "0.00000000", "maxQty": lim["mkt_max"],
                                      "stepSize": "0.00000000"},
                                     {"filterType": "NOTIONAL", "minNotional": lim["min_notional"],
                                      "applyMinToMarket": True, "maxNotional": "9000000.00000000"}]}]}


SOURCE_SCRIPT = r'''
import json, sys, tempfile, os, sqlite3
from datetime import datetime, timezone
sys.path.insert(0, PAYLOAD["tree"])
import backend.public_recipe_runtime as prr
import backend.absorption_runtime as ar
STEP = 14400
CLOCK = [0.0]
def utcnow():
    CLOCK[0] += 0.001
    return datetime.fromtimestamp(CLOCK[0], timezone.utc)
prr.utcnow = utcnow
ar.utcnow = utcnow
class Resp:
    def __init__(self, status, body): self.status, self.body, self.headers = status, body, {}
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self, n=-1): return self.body
def run(c):
    out = []
    obs = c["obs"]
    cur = {"i": -1, "bt": 0}
    def opener(req, timeout=8):
        o = obs[cur["i"]]
        url = req.full_url.split("/api/v3/", 1)[1]
        fail = o["fail"]
        if url.startswith("exchangeInfo"):
            return Resp(500, b"{}") if fail["meta"] else Resp(200, json.dumps(c["info"][cur["i"]]).encode())
        if url.startswith("klines"):
            return Resp(500, b"[]") if fail["klines"] else Resp(200, json.dumps(
                [[r[0] * 1000, r[1], r[2], r[3], r[4], r[5], (r[0] + STEP) * 1000 - 1, "0", 1, "0", "0", "0"]
                 for r in c["klines"][cur["i"]]]).encode())
        if url.startswith("trades"):
            tt = int((o["t"] - o["trade_age"]) * 1000)
            return Resp(500, b"[]") if fail["trades"] else Resp(200, json.dumps(
                [{"id": 1, "price": "1", "qty": "1", "quoteQty": "1", "time": tt, "isBuyerMaker": True}]).encode())
        if url.startswith("ticker/bookTicker"):
            cur["bt"] += 1
            if fail["bt_twice"] or (fail["bt_once"] and cur["bt"] == 1):
                return Resp(500, b"{}")
            return Resp(200, json.dumps(o["quote"]).encode())
        raise AssertionError(url)
    d = tempfile.mkdtemp()
    CLOCK[0] = float(c["install"]) - 1.0
    desk = ar.AbsorptionDesk(os.path.join(d, "absorption.sqlite"),
                             feed=ar.AbsorptionPublicFeed(source=prr.BinancePublicSpotFeed(opener=opener)), clock=utcnow)
    desk.install(enable=True)
    book = "ABSORPTION_" + c["symbol"] + "_4H"
    seen = 0
    seeded = False
    for i, o in enumerate(obs):
        cur["i"], cur["bt"] = i, 0
        CLOCK[0] = float(o["t"])
        try:
            fc = desk.feed.capture(c["symbol"], "4h", STEP * 1000)
            desk.process_capture(book, fc)
            err = None
        except Exception as e:
            err = type(e).__name__ + ": " + str(e)[:120]
        db = sqlite3.connect(os.path.join(d, "absorption.sqlite"))
        rows = db.execute("SELECT rowid, payload FROM events WHERE book_id=? AND rowid>? ORDER BY rowid", (book, seen)).fetchall()
        db.close()
        seed_pass = not seeded and any(json.loads(p)["type"] == "BAR" for _, p in rows)
        seeded = seeded or seed_pass
        for rowid, payload in rows:
            seen = rowid
            ev = json.loads(payload)
            if ev["type"] == "FILL":
                out.append([i, "fill", ev["side"], ev["qty"], ev["price"]])
            elif ev["type"] == "BAR" and ev["feature"]["confirmed_absorption"] and not seed_pass:
                out.append([i, "signal", ev["bar"]["close_at"]])
            elif ev["type"] == "SKIP_ENTRY":
                out.append([i, "skip", ev["id"], ev["reason"]])
            elif ev["type"] == "CANCEL" and ev["id"].split(":", 1)[0] in ("zero-depth", "depth-veto", "ack-veto",
                                                                           "partial-remainder"):
                out.append([i, "drop" if ev.get("clear_target") else "retry", ev["reason"]])
            elif ev["type"] == "QUARANTINE":
                out.append([i, "quarantine"])
        if err:
            out.append([i, "error", err])
    st = json.loads(sqlite3.connect(os.path.join(d, "absorption.sqlite")).execute(
        "SELECT state FROM books WHERE id=?", (book,)).fetchone()[0])
    desk.close()
    return {"seed": c["seed"], "events": out, "admissions": st["signal_count"], "cash": st["cash"]}
import shutil
tempfile.tempdir = BATCH_TMP = tempfile.mkdtemp(prefix="parity-absorption-")
try:
    res = [run(c) for c in PAYLOAD["cases"]]
finally:
    tempfile.tempdir = None
    shutil.rmtree(BATCH_TMP, ignore_errors=True)
print(json.dumps(res))
'''


def _prep(c):
    """materialise the per-capture HTTP bodies both sides read."""
    c = dict(c)
    c["klines"] = [klines_at(c, o) for o in c["obs"]]
    c["info"] = [exchange_info(c, o) for o in c["obs"]]
    return c


def source_batch(cases):
    from tools.parity import old_run
    from tools.parity.batch_tmp import batch_tmp
    with batch_tmp("parity-absorption-"):     # removed here even when the child fails, times out or is killed
        return old_run(SOURCE_SCRIPT, {"tree": TREE, "cases": cases}, timeout=7200, tree=TREE)


class _Hub:
    def __init__(self, c):
        self.c, self.i, self.bt, self.health = c, 0, 0, {}
        hub = self

        class _B:
            def last_trade(self_, symbol):
                o = hub.c["obs"][hub.i]
                if o["fail"]["trades"]:
                    raise RuntimeError("HTTP 500")
                return float(int((o["t"] - o["trade_age"]) * 1000)) / 1000.0
        self.binance = _B()

    def bars(self, source, interval, symbols, n=300):
        o = self.c["obs"][self.i]
        if o["fail"]["klines"]:
            raise RuntimeError("HTTP 500")
        rows = self.c["klines"][self.i]
        bl = [{"t": float(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4]),
               "v": float(r[5])} for r in rows]
        return {symbols[0]: [b for b in bl if b["t"] + STEP <= o["t"]][-n:]}

    def quotes(self, source, symbols, max_age=20):
        o = self.c["obs"][self.i]
        self.bt += 1
        f = o["fail"]
        if f["bt_twice"] or (f["bt_once"] and self.bt == 1):
            return {}
        b = o["quote"]
        return {symbols[0]: {"bid": float(b["bidPrice"]), "ask": float(b["askPrice"]), "bid_size": float(b["bidQty"]),
                             "ask_size": float(b["askQty"]), "last": None, "t": float(o["t"])}}


def port_run(c, same_pass):
    from desk.sleeves.families import absorption as A

    class _Feeds:
        pass
    hub = _Hub(c)
    feeds = _Feeds()
    feeds.hub = hub
    orig = A.raw_exchange_info

    def info(symbol):
        if c["obs"][hub.i]["fail"]["meta"]:
            raise RuntimeError("HTTP 500")
        return c["info"][hub.i]
    A.raw_exchange_info = info
    try:
        st, cash, pos, out, deferred = None, 100000.0, None, [], 0
        for i, o in enumerate(c["obs"]):
            hub.i, hub.bt = i, 0
            cap = A.capture(feeds, None, float(o["t"]), c["symbol"])
            obsd = {"now": float(o["t"]), "bars": cap["bars"], "quote": cap["quote"], "contract": cap["contract"],
                    "last_trade_at": cap["last_trade_at"], "errors": cap["errors"], "cash": cash,
                    "position": pos, "working": None}
            st, actions, notes = A.step(st, obsd, c["symbol"], defer_entry_after_exit=not same_pass)
            for n in notes:
                if isinstance(n, tuple) and n[0] == "signal":
                    out.append([i, "signal", n[1].split(":", 2)[2]])
                elif isinstance(n, tuple) and n[0] == "skip":
                    out.append([i, "skip", "skip:" + n[1], n[2]])
                elif isinstance(n, tuple) and n[0] in ("drop", "retry"):
                    out.append([i, n[0], n[2]])
                elif isinstance(n, str) and n.startswith("prefix_quarantined:"):
                    out.append([i, "quarantine"])
                elif n == "entry_deferred_after_exit":
                    deferred += 1
            for side, qty, px, m in actions:
                q, p = float(A.oms_qty(qty)), float(px)
                fee = abs(q * p) * 10.0 / 1e4
                if side == "buy":
                    cash -= q * p + fee
                    pos = {"qty": q, "meta": {"position_meta": {"entry_id": m["entry_id"], "exit_due_at": m["exit_due_at"],
                                                                "origin": m["origin"], "contract": m["contract"]}}}
                else:
                    cash += q * p - fee
                    left = float(pos["qty"]) - q
                    pos = None if abs(left) < 1e-9 else dict(pos, qty=left)
                out.append([i, "fill", side, str(qty), str(px)])
        return {"events": out, "deferred": deferred, "cash": cash}
    finally:
        A.raw_exchange_info = orig


RANK = {"signal": 0, "quarantine": 1, "skip": 2, "fill:sell": 3, "fill:buy": 4, "retry": 5, "drop": 6}


def _norm(events):
    """one capture's events in the source's order of obligations (bars, process skips, exit, entry), canonical."""
    return sorted(_norm1(events), key=lambda e: (e[0], RANK[e[1] + (":" + e[2] if e[1] == "fill" else "")],
                                                 json.dumps(e[2:])))


def _norm1(events):
    out = []
    for e in events:
        if e[1] == "fill":
            out.append([e[0], "fill", e[2], str(Decimal(e[3]).normalize()), str(Decimal(e[4]).normalize())])
        elif e[1] == "error":
            continue
        else:
            out.append(list(e))
    return out


def _chunk(seeds):
    cases = [_prep(case(s)) for s in seeds]
    src = source_batch(cases)
    rows = []
    for c, s in zip(cases, src):
        a = _norm(s["events"])
        b = port_run(c, same_pass=True)
        d = port_run(c, same_pass=False)
        rows.append({"seed": c["seed"], "symbol": c["symbol"], "source": a, "port": _norm(b["events"]),
                     "deployed": _norm(d["events"]), "deferred": d["deferred"],
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
    n_chunks = int(os.environ.get("PARITY_CHUNKS", "40"))                # 25 cases per source process
    rows = _chunked("absorption", _chunk, [seeds[i::n_chunks] for i in range(n_chunks)])
    rows.sort(key=lambda r: r["seed"])
    diffs, dev, stats = [], [], {"fills_buy": 0, "fills_sell": 0, "signals": 0, "skips": 0, "quarantines": 0,
                                 "source_cycle_errors": 0, "deferred_entries": 0, "deployed_cases_differing": 0}
    reasons = {}
    stats["multi_fill_exits"] = 0
    for r in rows:
        stats["source_cycle_errors"] += r["errors"]
        sells = 0
        for e in r["source"]:
            if e[1] == "fill":
                stats["fills_" + e[2]] += 1
                if e[2] == "buy":
                    stats["multi_fill_exits"] += 1 if sells > 1 else 0
                    sells = 0
                else:
                    sells += 1
            elif e[1] in ("signal", "skip"):
                stats[e[1] + "s"] += 1
            elif e[1] == "quarantine":
                stats["quarantines"] += 1
            if e[1] in ("skip", "drop", "retry"):
                k = e[1] + ":" + str(e[-1]).split(":")[0 if e[1] != "skip" else 0]
                reasons[k] = reasons.get(k, 0) + 1
        stats["multi_fill_exits"] += 1 if sells > 1 else 0
        if r["source"] != r["port"]:
            diffs.append({"seed": r["seed"], "source": r["source"][:12], "port": r["port"][:12]})
        stats["deferred_entries"] += r["deferred"]
        if r["deployed"] != r["port"]:
            stats["deployed_cases_differing"] += 1
            if r["deferred"] == 0:
                dev.append({"seed": r["seed"], "why": "deployed differs without a deferral"})
    stats["skip_drop_retry_reasons"] = reasons
    res = {"cases": len(rows), "identical": len(rows) - len(diffs), "diffs": diffs[:20] + dev[:20],
           "unexplained_deployed": len(dev), "stats": stats,
           "source": {"runtime": "desk/vendor/ausar_ctx/backend/absorption_runtime.py (blob 6d05c2cd)",
                      "feed": "backend/public_recipe_runtime.py BinancePublicSpotFeed (blob 5c5f529b), HTTP stubbed",
                      "signals": "strategies/absorption/signals.py (blob 6b9feadb)"},
           "named_divergences": {"entry_deferred_after_exit": stats["deferred_entries"]}}
    if dev:
        res["diffs"] = res["diffs"]
    res["sleeves"] = ["ausar_absorption_enjusdt_4h", "ausar_absorption_linkusdt_4h"]
    write_receipt("absorption", res)
    return dict(res, sleeve="absorption")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "stats")}))
    sys.exit(1 if r["diffs"] else 0)
