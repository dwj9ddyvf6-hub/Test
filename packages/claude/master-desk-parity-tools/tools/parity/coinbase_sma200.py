"""coinbase_sma200: the SOURCE runtime (agentic-trading-desk aurelia-paper-desk @1720157f, desk-source/backend/
prospective_native.py: NativeProspectiveDesk.install + run_once on its own SQLite journal, the capture built and
validated by its own CoinbasePublicFeed.capture / independently_valid_markets) vs the port
(desk/sleeves/families/coinbase_sma200.py over engine-shaped Views), both books, on deterministic random UTC-day
sequences: opening-window passes (00:00-00:05 UTC), passes just after it and midday passes, days whose window is
missed, gates flipping across the SMA200, and data faults (a stale last trade, the latest candle not yet published,
a product halted).

Stubbed in the source (I/O only): CoinbasePublicFeed._get_json (the GET: serves the case's raw product / candle /
ticker / L1 book bodies with a receipt built exactly like the original, server Date = the receipt second) and the
module clock (the case's decision time). The source keeps its whole journal, verify_ledger replay, fill and cycle
logic. Fills in the port are applied by the harness at the same received bid / ask with the source's own fee
rounding (FEE 0.2% rounded up to $1e-8), so each side's book evolves from its own decisions.

Compared per pass and book: the fills (side, symbol, quantity, price), then cash and holdings. Displayed L1 sizes
are large in every case (C1: the desk's quote carries no size, so the source's depth cap is outside the port)."""
import json
import os
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_UP

from desk.contract import View
from desk.sleeves.families import coinbase_sma200 as C

from . import old_run, write_receipt

SRC = os.environ.get("AUSAR_SRC", "/home/user/br/agentic-trading-desk@aurelia-paper-desk/ausar-archive/ausar-receiver/"
                     "original-payload/desk-source")
N_SEQ = int(os.environ.get("COINBASE_SEQS", "120"))
DAYS = int(os.environ.get("COINBASE_DAYS", "28"))
BATCH = int(os.environ.get("COINBASE_BATCH", "10"))
UTC = timezone.utc
BASE = {"BTC-USD": 60000.0, "ETH-USD": 3000.0}

SOURCE_SCRIPT = r'''
import hashlib, json, os, sqlite3, tempfile
from datetime import datetime, timezone
from email.utils import format_datetime
import backend.prospective_native as PN
UTC = timezone.utc
NOW = [None]
_clock = PN.clock
def clock(value=None):
    return NOW[0] if value is None else _clock(value)
PN.clock = clock
MARKET = {}
def _get_json(self, tail):
    started = clock()
    path = tail.split('?')[0]
    sym = path.split('/')[1]
    kind = path.split('/')[-1] if path.count('/') > 1 else 'product'
    body = MARKET[kind].get(sym)
    if body is None:
        raise ValueError('Coinbase public GET HTTP 503')
    raw = json.dumps(body).encode()
    received = clock()
    receipt = {'url': self.BASE + tail, 'request_started_at': started.isoformat(), 'received_at': received.isoformat(),
               'http_status': 200, 'server_date': format_datetime(received.replace(microsecond=0), usegmt=True),
               'transport': 'absolute_deadline_bounded_http', 'raw_sha256': hashlib.sha256(raw).hexdigest(),
               'raw_bytes': len(raw), 'raw_body_utf8': raw.decode('utf-8')}
    return json.loads(raw), receipt
PN.CoinbasePublicFeed._get_json = _get_json
out = []
for seq in PAYLOAD['seqs']:
    d = tempfile.mkdtemp()
    path = os.path.join(d, 'native-prospective.sqlite')
    desk = PN.NativeProspectiveDesk(path)
    NOW[0] = datetime.fromtimestamp(seq['install'], tz=UTC)
    desk.install(True, now=NOW[0])
    steps = []
    for st in seq['steps']:
        NOW[0] = datetime.fromtimestamp(st['now'], tz=UTC)
        MARKET.clear()
        MARKET.update(st['market'])
        try:
            cap = PN.CoinbasePublicFeed().capture(NOW[0])
            res = desk.run_once(capture=cap, now=NOW[0])
        except Exception as e:
            res = {'status': 'error', 'error': type(e).__name__ + ': ' + str(e)}
        con = sqlite3.connect(path)
        at = NOW[0].isoformat()
        fills = sorted([r[0], r[1], r[2], r[3], r[4]] for r in con.execute(
            'SELECT book, symbol, side, quantity, price FROM native_fills WHERE at=?', (at,)))
        books = {}
        for book, cash in con.execute('SELECT book, cash FROM native_books'):
            books[book] = {'cash': cash, 'positions': {s: q for s, q in con.execute(
                'SELECT symbol, quantity FROM native_positions WHERE book=?', (book,)) if Decimal(q) > 0}}
        con.close()
        steps.append({'status': res.get('status'), 'error': res.get('error'), 'fills': fills, 'books': books})
    out.append(steps)
print(json.dumps(out))
'''.replace("import backend.prospective_native as PN", "from decimal import Decimal\nimport backend.prospective_native as PN")


def _walk(rng, n, base):
    px, out = base * rng.uniform(0.8, 1.2), []
    vol = rng.uniform(0.015, 0.035)
    regime = rng.choice((0.002, -0.002, 0.0))
    for i in range(n):
        if rng.random() < 0.04:
            regime = rng.choice((0.004, -0.004, 0.0, 0.002, -0.002))
        r = rng.gauss(regime, vol)
        o = px
        c = max(1.0, px * (1 + r))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 3)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 3)))
        out.append([round(lo, 2), round(h, 2), round(o, 2), round(c, 2), round(rng.uniform(1e3, 5e4), 8)])
        px = c
    for row in out:
        row[0] = min(row[0], row[2], row[3])
        row[1] = max(row[1], row[2], row[3])
    return out


def _product(sym, halted=False):
    return {"id": sym, "base_currency": sym.split("-")[0], "quote_currency": "USD", "quote_increment": "0.01",
            "base_increment": "0.00000001", "display_name": sym.replace("-", "/"), "min_market_funds": "1",
            "margin_enabled": False, "post_only": False, "limit_only": False, "cancel_only": False,
            "status": "delisted" if halted else "online", "status_message": "", "trading_disabled": False,
            "fx_stablecoin": False, "max_slippage_percentage": "0.02000000", "auction_mode": False,
            "high_bid_limit_percentage": ""}


def make_sequence(seed):
    rng = random.Random(seed)
    first = datetime(2025, 1, 6, tzinfo=UTC) + timedelta(days=rng.randint(0, 500))
    hist = 215
    start = first - timedelta(days=hist)
    total = hist + DAYS + 1
    candles = {s: _walk(rng, total, b) for s, b in BASE.items()}
    steps = []
    for k in range(DAYS):
        day = first + timedelta(days=k)
        t0 = day.timestamp()
        times = []
        if rng.random() < 0.88:                                  # the opening window (missed on some days)
            times += [t0 + rng.uniform(0.5, 25), t0 + rng.uniform(30, 120)]
            if rng.random() < 0.3:
                times.append(t0 + rng.uniform(250, 299))
        if rng.random() < 0.5:
            times.append(t0 + rng.uniform(300, 900))
        if rng.random() < 0.6:
            times.append(t0 + rng.uniform(3600, 80000))
        for now in sorted(times):
            nowdt = datetime.fromtimestamp(now, tz=UTC)
            idx = hist + k                                       # candles completed before this day's opening
            fault = rng.random()
            market = {"product": {}, "candles": {}, "ticker": {}, "book": {}}
            port_bars, port_quotes, prods = {}, {}, {}
            for s in BASE:
                rows = []
                for i in range(idx + 1):                         # incl. today's forming candle (start = opening)
                    lo, hi, o, c, v = candles[s][i]
                    rows.append([int((start + timedelta(days=i)).timestamp()), lo, hi, o, c, v])
                if fault < 0.04 and s == "ETH-USD" and now - t0 < 120:
                    rows = rows[:-2] + rows[-1:]                 # yesterday's candle not yet published
                halted = fault > 0.985 and s == "BTC-USD"
                market["product"][s] = _product(s, halted)
                market["candles"][s] = list(reversed(rows))       # Coinbase serves newest first
                last = rows[-1][4]
                mid = round(last * (1 + rng.gauss(0, 0.002)), 2)
                bid, ask = round(mid - 0.01, 2), round(mid + 0.01, 2)
                trade_at = now - (rng.uniform(31, 90) if (0.04 <= fault < 0.08 and s == "BTC-USD") else rng.uniform(0, 5))
                market["ticker"][s] = {"trade_id": int(now), "price": str(mid), "size": "0.01",
                                       "time": datetime.fromtimestamp(trade_at, tz=UTC).isoformat().replace("+00:00", "Z"),
                                       "bid": str(bid), "ask": str(ask), "volume": "1000"}
                market["book"][s] = {"bids": [[str(bid), "500.0", 3]], "asks": [[str(ask), "500.0", 4]],
                                     "sequence": int(now * 1000) % (10 ** 12) + 1, "auction_mode": False,
                                     "auction": None, "time": nowdt.isoformat().replace("+00:00", "Z")}
                port_bars[s] = [{"t": float(r[0]), "o": r[3], "h": r[2], "l": r[1], "c": r[4], "v": r[5]}
                                for r in rows if r[0] + 86400 <= now]
                port_quotes[s] = {"bid": bid, "ask": ask, "last": mid, "t": trade_at, "_at": now}
                prods[s] = market["product"][s]
            steps.append({"now": now, "market": market, "port": {"bars": port_bars, "quotes": port_quotes,
                                                                  "products": prods}})
    return {"seed": seed, "install": (first - timedelta(days=1)).timestamp(), "steps": steps}


def _fee(notional):
    return (notional * C.FEE).quantize(C.PN.MONEY_QUANTUM, rounding=ROUND_UP)


def run_port(seq):
    sleeves = {book: next(s for s in C.sleeves() if s.book == book) for book in ("ETH_SMA200", "BTC_ETH_SMA200")}
    books = {b: {"cash": Decimal("100000"), "pos": {s: Decimal(0) for s in C.SYMBOLS}, "state": {}} for b in sleeves}
    out = []
    for st in seq["steps"]:
        fills = []
        for book, sl in sleeves.items():
            bk = books[book]
            positions = {f"SPOT:COINBASE:{s}": {"qty": float(q), "avg": 0.0, "meta": {}, "mark": None}
                         for s, q in bk["pos"].items() if q > 0}
            view = View(now=st["now"], session="", bars={"1d": st["port"]["bars"]}, quotes=st["port"]["quotes"],
                        positions=positions, equity=float(bk["cash"]), cash=float(bk["cash"]),
                        state=json.loads(json.dumps(bk["state"])),
                        extra={"coinbase_products": st["port"]["products"], "pending_orders": []})
            try:
                intents = sl.signal(view)
                bk["state"] = sl.update_state(view, intents) or bk["state"]
            except Exception:                                     # the source's run_once fails the whole pass too
                intents = []
            for it in sorted(intents, key=lambda i: 0 if i.kind == "exit" else 1):
                q = Decimal(repr(it.qty))
                quote = st["port"]["quotes"][it.symbol]
                if it.kind == "exit":
                    px = Decimal(str(quote["bid"]))
                    bk["cash"] += q * px - _fee(q * px)
                    bk["pos"][it.symbol] -= q
                    fills.append([book, it.symbol, "sell", str(q), str(px)])
                else:
                    px = Decimal(str(quote["ask"]))
                    bk["cash"] -= q * px + _fee(q * px)
                    bk["pos"][it.symbol] += q
                    fills.append([book, it.symbol, "buy", str(q), str(px)])
        out.append({"fills": sorted(fills),
                    "books": {b: {"cash": bk["cash"], "positions": {s: q for s, q in bk["pos"].items() if q > 0}}
                              for b, bk in books.items()}})
    return out


def _same_fills(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(sorted(a), sorted(b)):
        if x[:3] != y[:3] or Decimal(x[3]) != Decimal(y[3]) or Decimal(x[4]) != Decimal(y[4]):
            return False
    return True


def _batches():
    """sequences in batches of BATCH (generated, replayed on both sides and compared one batch at a time)."""
    for b0 in range(0, N_SEQ, BATCH):
        seqs = [make_sequence(4400 + i) for i in range(b0, min(N_SEQ, b0 + BATCH))]
        ports = [run_port(s) for s in seqs]
        batch = [{"install": s["install"], "steps": [{"now": st["now"], "market": st["market"]} for st in s["steps"]]}
                 for s in seqs]
        old = old_run(SOURCE_SCRIPT, {"seqs": batch}, timeout=7200, tree=SRC)
        del batch
        for seq, src, port in zip(seqs, old, ports):
            yield seq, src, port


def run():
    diffs, cases = [], 0
    stats = {"sequences": N_SEQ, "passes": 0, "fills": {"buy": 0, "sell": 0}, "status": {}, "errors": 0}
    for seq, src, port in _batches():
        for i, (a, b) in enumerate(zip(src, port)):
            stats["passes"] += 1
            stats["status"][a["status"]] = stats["status"].get(a["status"], 0) + 1
            stats["errors"] += 1 if a.get("error") else 0
            for f in a["fills"]:
                stats["fills"][f[2]] += 1
            for book in ("ETH_SMA200", "BTC_ETH_SMA200"):
                cases += 1
                fa = [f for f in a["fills"] if f[0] == book]
                fb = [f for f in b["fills"] if f[0] == book]
                sa, sb = a["books"][book], b["books"][book]
                bad = []
                if not _same_fills(fa, fb):
                    bad.append("fills")
                if abs(Decimal(sa["cash"]) - sb["cash"]) > Decimal("1e-8"):
                    bad.append("cash")
                if {s: Decimal(q) for s, q in sa["positions"].items()} != sb["positions"]:
                    bad.append("positions")
                if bad:
                    diffs.append({"seed": seq["seed"], "step": i, "book": book, "what": bad,
                                  "at": datetime.fromtimestamp(seq["steps"][i]["now"], tz=UTC).isoformat(),
                                  "source": {"fills": fa, "cash": sa["cash"], "positions": sa["positions"],
                                             "status": a["status"], "error": a.get("error")},
                                  "port": {"fills": fb, "cash": str(sb["cash"]),
                                           "positions": {s: str(q) for s, q in sb["positions"].items()}}})
    res = {"sleeve": "coinbase_sma200", "cases": cases, "identical": cases - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats, "source_tree": SRC,
           "source_commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
           "named_divergences_in_cases": {"C1": "L1 sizes large in every case (no depth cap reached)",
                                          "C2": "harness fills sells then buys at the decision quote on both sides",
                                          "C3": "harness charges the source's rounded-up fee on both sides",
                                          "C4": "completion observed on the next pass: no fill impact"},
           "method": "per pass and book: fills, cash, holdings; both books on the same market, each side carrying "
                     "its own journal / book"}
    write_receipt("coinbase_sma200", res)
    return res
