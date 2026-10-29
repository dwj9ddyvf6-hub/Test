"""Deterministic INPUT generator for the Aurelia crypto parity harnesses (tools/parity/free_kraken.py,
fwd_alpaca.py, fwd_coinbase_sma200.py). It decides nothing: from a seed it builds the public payloads both sides
read — the source desk (run in its own tree, where this stubs directory is on sys.path) through its stubbed HTTP
calls, the port through the desk's data shapes — and the seeded paper-ledger history of each Kraken book."""
import random
from datetime import datetime, timedelta, timezone

H4 = 4 * 3600
UTC = timezone.utc
BASE = datetime(2026, 1, 5, tzinfo=UTC)
SYMBOLS = (("ADA", "PF_ADAUSD", "ADAUSD", 0.45), ("LINK", "PF_LINKUSD", "LINKUSD", 14.0))
TICKERS = "https://futures.kraken.com/derivatives/api/v3/tickers"
INSTRUMENTS = "https://futures.kraken.com/derivatives/api/v3/instruments"
CHART = "https://futures.kraken.com/api/charts/v1/trade/%s/4h"
FUNDING = "https://futures.kraken.com/derivatives/api/v3/historical-funding-rates?symbol=%s"
OHLC = "https://api.kraken.com/0/public/OHLC?pair=%s&interval=240"
DEPTH = "https://api.kraken.com/0/public/Depth?pair=ENJUSD&count=5"


def _iso(dt):
    return dt.astimezone(UTC).isoformat()


def _z(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _px(x):
    return float("%.6g" % x)


# -- Kraken ----------------------------------------------------------------------------------------------------
def _candles(rnd, n, start_px, fire, plants):
    """n 4h bars [o, h, l, c, v] (index 0 oldest, n - 1 forming); the bars in `plants` close below the lowest low of
    the 20 bars before them; `fire` (index or None) likewise; a few near misses close exactly at that low."""
    rows, px = [], start_px
    for _ in range(n):
        o = px * (1 + rnd.gauss(0, 0.004))
        c = o * (1 + rnd.gauss(0.0004, 0.012))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.005)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.005)))
        rows.append([o, h, lo, c, float(int(rnd.uniform(1e4, 5e6)))])
        px = c
    for k in sorted(set(plants) | ({fire} if fire is not None else set())):
        if k < 20 or k >= n:
            continue
        low = min(r[2] for r in rows[k - 20:k])
        if k == fire and k not in plants and rnd.random() < 0.06:
            c = low                                                      # equal is not below: no breakdown
        else:
            c = low * (1 - rnd.uniform(0.0005, 0.03))
        o = rows[k][0]
        rows[k] = [o, max(o, c) * 1.002, min(o, c) * 0.997, c, rows[k][4]]
    return [[_px(x) for x in r[:4]] + [r[4]] for r in rows]


def _sell(sid, perp, t, price):
    return {"status": "filled", "paper_only": True, "writer": "experiment_executor", "sleeve": sid, "symbol": perp,
            "side": "sell", "quantity": 1.0, "price": price, "client_order_id": "%s-%s" % (sid, t.date().isoformat()),
            "filled_at": _iso(t), "affects_aurelia": False, "quote_exchange_time": None, "model_entry_open_used": False}


def _cover(sid, perp, t, exit_due, price):
    return {"status": "filled", "paper_only": True, "writer": "experiment_executor", "sleeve": sid, "symbol": perp,
            "side": "buy", "quantity": 1.0, "price": price, "client_order_id": "%s-exit-%s" % (sid, exit_due.date()),
            "filled_at": _iso(t), "affects_aurelia": False, "quote_exchange_time": None, "model_entry_open_used": False}


def kraken_case(seed):
    """one pass of the source's kraken_paper.run(): `now`, each perpetual's chart / spot OHLC / funding / ticker /
    instrument row, the ENJ book, and per book (BREAKDOWN, CROWDED) a seeded ledger history:
      flat              nothing held
      open_due          a short from an earlier breakdown event e (filled inside its window), its 16h exit due
      open_not_due      the same, its exit not yet due (e = F-2 is the current event itself)
      covered_same_day  a short entered at 00:00-08:00 and covered 16h later, both today; now 20:00-24:00 (BREAKDOWN)
      collision         a short covered at 00:00-04:00 today (exit due 00:00) and the next short entered at 04:00-08:00
                        today (exit due 20:00 today: the same exit-due date); now 20:00-24:00 (BREAKDOWN)
    Bar indices: the chart's bar i opens at f_open - (F - i) x 4h, F = the forming bar; an event e is entry-due at
    open(e + 2) and exit-due at open(e + 6). "state" is the port's position for each book."""
    rnd = random.Random(seed)
    day = BASE + timedelta(days=rnd.randrange(0, 240))
    late = rnd.random() < 0.22
    hour = rnd.randrange(20, 24) if late else rnd.randrange(0, 24)
    now = day + timedelta(hours=hour, seconds=rnd.choice((0, 1, rnd.randrange(0, 3600))))
    f_open = now - timedelta(seconds=(now - BASE).total_seconds() % H4)
    case = {"seed": seed, "now": _iso(now), "books": {}, "ledger": [], "scenario": {}, "state": {}}
    ins = []
    for name, perp, spot_pair, px0 in SYMBOLS:
        n = rnd.choice((rnd.randrange(8, 24), rnd.randrange(40, 120), rnd.randrange(180, 330), rnd.randrange(181, 330)))
        if rnd.random() < 0.02:
            px0 *= 60000.0                                               # a price level past the sleeve's cap
        F = n - 1

        def open_of(i):
            return f_open - timedelta(seconds=(F - i) * H4)

        fire = F - 2 if rnd.random() < 0.55 else None
        plants, led, scen, state = [], [], {}, {}
        for book in ("BREAKDOWN", "CROWDED"):
            sid = "FREE_KRAKEN_%s_%s_V1" % (name, book)
            u = rnd.random()
            if n < 40:
                kind = "flat"
            elif book == "BREAKDOWN" and late:
                kind = ("covered_same_day", "collision", "flat", "open_due")[int(u * 4)]
            else:
                kind = "flat" if u < 0.45 else ("open_due" if u < 0.75 else "open_not_due")
            scen[book] = kind
            state[book] = None
            if kind == "flat":
                continue
            if kind == "open_due":
                e = F - 6 - rnd.randrange(0, 4)
            elif kind == "open_not_due":
                e = F - rnd.randrange(2, 6)
            elif kind == "covered_same_day":
                e = F - rnd.choice((6, 7))                               # entry due 04:00 / 00:00 today
                if rnd.random() < 0.85:
                    fire = F - 2                                         # a new breakdown event at 20:00 today
            else:
                e = F - 6                                                # the open short: entry due 04:00 today
                e1 = F - 11                                              # the covered one: entry due 08:00 yesterday
                plants.append(e1)
                due1 = open_of(e1 + 2)
                t1 = due1 + timedelta(seconds=rnd.randrange(0, H4 - 1))
                tc1 = open_of(e1 + 6) + timedelta(seconds=rnd.randrange(0, H4 - 1))
                led += [_sell(sid, perp, t1, None), _cover(sid, perp, tc1, open_of(e1 + 6), None)]
            plants.append(e)
            due = open_of(e + 2)
            t0 = min(now, due + timedelta(seconds=rnd.randrange(0, H4 - 1)))
            led.append(_sell(sid, perp, t0, None))
            if kind == "covered_same_day":
                exit_due = open_of(e + 6)
                tc = exit_due + timedelta(seconds=rnd.randrange(0, max(1, int((now - exit_due).total_seconds()))))
                led.append(_cover(sid, perp, tc, exit_due, None))
            else:
                state[book] = {"qty": -1, "entry_due_at": _iso(due)}
        if rnd.random() < 0.03:
            fire = None
        candles = _candles(rnd, n, px0, fire, plants)
        for row in led:
            row["price"] = candles[-1][0]
        times = [open_of(i) for i in range(n)]
        if not led and n > 25 and rnd.random() < 0.06:                    # an exchange gap in the perpetual tape
            drop = rnd.randrange(1, n - 3)
            del candles[drop]
            del times[drop]
        chart = [{"time": int(t.timestamp() * 1000), "open": repr(c[0]), "high": repr(c[1]), "low": repr(c[2]),
                  "close": repr(c[3]), "volume": repr(c[4])} for t, c in zip(times, candles)]
        # spot: the same 4h grid, the basis around a small mean (sometimes a spike on the last completed bar), the
        # window starting later than the perpetual's (unpaired perpetual bars), now and then a missing / bad row
        n_spot = min(len(chart), rnd.choice((0, rnd.randrange(5, 60), rnd.randrange(150, 260), 400)))
        mu, sd = rnd.uniform(-0.0005, 0.001), rnd.uniform(0.0001, 0.0008)
        spike = rnd.random() < 0.35
        spot = []
        for k, cd in enumerate(chart[len(chart) - n_spot:]):
            b = mu + sd * (rnd.uniform(3.5, 8) if (spike and k == n_spot - 2) else rnd.gauss(0, 1))
            sc, so = _px(float(cd["close"]) / (1 + b)), _px(float(cd["open"]) / (1 + b))
            spot.append([int(cd["time"] / 1000), repr(so), repr(_px(max(so, sc) * 1.001)), repr(_px(min(so, sc) * 0.999)),
                         repr(sc), repr(sc), repr(float(int(rnd.uniform(1e3, 1e6)))), rnd.randrange(10, 900)])
        if spot and rnd.random() < 0.12:
            del spot[rnd.randrange(0, len(spot))]
        if spot and rnd.random() < 0.03:
            j = rnd.randrange(0, len(spot))
            spot[j] = spot[j][:4] + ["0.0"] + spot[j][5:]
        meta = _instrument(rnd, name, perp)
        if meta is not None:
            ins.append(meta)
        case["books"][name] = {"perp": perp, "spot_pair": spot_pair, "chart": chart, "spot": spot,
                               "rates": _rates(rnd, now), "ticker": _ticker(rnd, candles[-1][3])}
        case["scenario"][name] = scen
        case["state"][name] = state
        case["ledger"] += led
    if rnd.random() < 0.3:
        ins.append({"symbol": "PF_ENJUSD" if rnd.random() < 0.5 else "FI_ENJUSD_261225", "type": "flexible_futures",
                    "base": "ENJ", "quote": "USD", "pair": "ENJ:USD", "contractSize": 1})
    ins.append({"symbol": "PF_XBTUSD", "type": "flexible_futures", "base": "XBT", "quote": "USD", "pair": "XBT:USD",
                "contractSize": 1, "tradeable": True, "fundingRateCoefficient": 8})
    rnd.shuffle(ins)
    case["instruments"] = {"result": "success", "instruments": ins}
    case["enj"] = _depth(rnd)
    return case


def _rates(rnd, now):
    """Kraken historical funding prints (hourly), oldest first; sparse / short histories, a few printed after now,
    and a latest print that is sometimes a crowded spike."""
    span_h = rnd.choice((rnd.randrange(10, 60), rnd.randrange(400, 800), rnd.randrange(2100, 2600)))
    step = rnd.choice((1, 1, 1, 7, 30))
    out = []
    t = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=span_h)
    level = rnd.uniform(-2e-6, 4e-6)
    end = now + timedelta(hours=rnd.choice((0, 0, 0, 2)))
    while t <= end:
        fr = rnd.gauss(level, 3e-6)
        out.append({"timestamp": _z(t), "fundingRate": fr, "relativeFundingRate": fr / rnd.uniform(0.1, 30)})
        t += timedelta(hours=step)
    known = [r for r in out if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) <= now]
    if known and rnd.random() < 0.5:
        r = known[-1]
        r["fundingRate"] = abs(level) + rnd.uniform(5e-6, 3e-5)
        r["relativeFundingRate"] = r["fundingRate"] * rnd.choice((1, 1, 1, -1)) / 10
    if rnd.random() < 0.04:
        rnd.shuffle(out)                                                 # the API's order is what "latest" reads
    if rnd.random() < 0.04:
        out = []
    return out


def _ticker(rnd, px):
    u = rnd.random()
    bid, ask = _px(px * (1 - 0.0004)), _px(px * (1 + 0.0004))
    if u < 0.06:
        return None                                                      # symbol absent from the ticker list
    if u < 0.10:
        return {"bid": None, "ask": ask}
    if u < 0.14:
        return {"bid": ask, "ask": bid}                                  # crossed
    if u < 0.16:
        return {"bid": 0.0, "ask": ask}
    if u < 0.18:
        return {"bid": bid, "ask": bid}                                  # locked: bid == ask is not crossed
    return {"bid": bid, "ask": ask, "last": px}


def _instrument(rnd, name, perp):
    u = rnd.random()
    row = {"symbol": perp, "type": "flexible_futures", "base": name, "quote": "USD", "pair": "%s:USD" % name,
           "contractSize": 1, "tradeable": True, "fundingRateCoefficient": 8}
    if u < 0.04:
        return None                                                      # not listed
    if u < 0.06:
        row["type"] = "futures_inverse"
    elif u < 0.08:
        row["contractSize"] = 10
    elif u < 0.09:
        row["pair"] = "%s:USDT" % name
    return row


def _depth(rnd):
    u = rnd.random()
    bid, ask = _px(rnd.uniform(0.02, 0.05)), None
    ask = _px(bid * (1 + rnd.uniform(0.0002, 0.01)))
    book = {"asks": [[repr(ask), "100.0", 1792145074]], "bids": [[repr(bid), "120.0", 1792145070]]}
    if u < 0.08:
        book["bids"] = []
    elif u < 0.12:
        book["asks"] = []
    elif u < 0.17:
        book["bids"][0][0], book["asks"][0][0] = book["asks"][0][0], book["bids"][0][0]
    elif u < 0.19:
        book["bids"][0][0] = "0"
    elif u < 0.21:
        return {}                                                        # the pair unknown: no book in the result
    return {"ENJUSD": book}


def routes(case):
    """url -> payload, as the source's _get calls name them."""
    out = {TICKERS: {"result": "success", "tickers": []}, INSTRUMENTS: case["instruments"],
           DEPTH: {"error": [], "result": case["enj"]}}
    for name, b in case["books"].items():
        if b["ticker"] is not None:
            out[TICKERS]["tickers"].append(dict(b["ticker"], symbol=b["perp"]))
        out[CHART % b["perp"]] = {"candles": b["chart"], "more_candles": False}
        out[FUNDING % b["perp"]] = {"result": "success", "rates": b["rates"]}
        out[OHLC % b["spot_pair"]] = {"error": [], "result": {b["spot_pair"]: b["spot"], "last": 0}}
    return out


# -- Alpaca USD forwards ---------------------------------------------------------------------------------------
FWD_IDS = {"ADA/USD": "FWD_ALPACA_ADA_RSI2_V1", "LINK/USD": "FWD_ALPACA_LINK_AI_VOLUME_V1"}


def _ms(dt):
    return dt.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _walk(rnd, n, px, drift, vol):
    out = []
    for _ in range(n):
        o = px
        c = o * (1 + rnd.gauss(drift, vol))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        out.append([o, h, lo, c])
        px = c
    return out


def alpaca_case(seed):
    """one forward_cycle.run_cycle() pass over both listed books: `now` near a bar close (inside or outside the 300 s
    decision window), each book's raw Alpaca bars from 45 days back to now (the forming bar included), its latest
    quote (fresh, stale, future, wide, crossed, one-sided or unreachable), the seeded holding (ledger fill + the
    forward state's entry bar close) and already-sent client ids."""
    rnd = random.Random(seed)
    day = BASE + timedelta(days=rnd.randrange(60, 280))
    u = rnd.random()
    if u < 0.55:
        anchor = day + timedelta(hours=4 * rnd.randrange(0, 6))          # a 4h close: both windows can open
        age = rnd.choice((0, 1, rnd.randrange(0, 301), rnd.randrange(0, 301), 300, 301))
    elif u < 0.85:
        anchor = day + timedelta(hours=rnd.choice([h for h in range(24) if h % 4]))   # an hourly close only
        age = rnd.randrange(0, 301)
    else:
        anchor = day + timedelta(hours=rnd.randrange(0, 24))
        age = rnd.randrange(301, 3500)
    now = anchor + timedelta(seconds=age)
    case = {"seed": seed, "now": _iso(now), "books": {}}
    for sym, step, px, n_h in (("ADA/USD", 3600, rnd.uniform(0.2, 1.2), 45 * 24 + 6),
                               ("LINK/USD", 14400, rnd.uniform(6, 30), 45 * 6 + 2)):
        opened = now - timedelta(seconds=(now - BASE).total_seconds() % step)        # the forming bar's open
        n = n_h if rnd.random() > 0.04 else rnd.randrange(20, 240 if step == 3600 else 70)   # a short history
        plant = rnd.random() < 0.5
        if step == 3600:
            rows = _walk(rnd, n, px, rnd.uniform(0.0002, 0.0015) if plant else rnd.uniform(-0.001, 0.001), 0.006)
            if plant:                                                    # a sharp dip on the last completed bars
                k = rnd.choice((2, 3, 4))
                for j in range(max(1, n - 1 - k), n - 1):
                    o = rows[j - 1][3]
                    c = o * (1 - rnd.uniform(0.006, 0.03))
                    rows[j] = [o, o * 1.001, c * 0.998, c]
        else:
            rows = _walk(rnd, n, px, rnd.uniform(0.0, 0.004) if plant else rnd.uniform(-0.003, 0.003), 0.015)
        vols = [float(int(rnd.uniform(1e3, 1e5))) for _ in range(n)]
        if step == 14400 and plant and n > 2:                            # a volume spike on an up bar
            j = n - 2
            o = rows[j - 1][3]
            c = o * (1 + rnd.uniform(0.002, 0.04))
            rows[j] = [o, c * 1.002, o * 0.998, c]
            vols[j] = vols[j] * rnd.uniform(2.5, 9)
        raw = []
        for i, (r, v) in enumerate(zip(rows, vols)):
            t = opened - timedelta(seconds=(n - 1 - i) * step)
            raw.append({"t": t.isoformat().replace("+00:00", "Z"), "o": _px(r[0]), "h": _px(r[1]), "l": _px(r[2]),
                        "c": _px(r[3]), "v": v, "n": rnd.randrange(0, 50), "vw": _px(r[3])})
        last_c = raw[-2]["c"] if len(raw) > 1 else px
        q = rnd.random()
        bid, ask = _px(last_c * (1 - rnd.uniform(0.0001, 0.002))), _px(last_c * (1 + rnd.uniform(0.0001, 0.002)))
        stamp = now - timedelta(milliseconds=rnd.randrange(0, 9000))
        quote = {"bid": bid, "ask": ask, "exchange_at": _ms(stamp)}
        if q < 0.06:
            quote["exchange_at"] = _ms(now - timedelta(milliseconds=rnd.randrange(10001, 60000)))   # stale
        elif q < 0.11:
            quote["exchange_at"] = _ms(now + timedelta(milliseconds=rnd.randrange(1, 3000)))       # future
        elif q < 0.17:
            quote["bid"] = _px(ask * (1 - rnd.uniform(0.0102, 0.05)))                                # > 100 bps wide
        elif q < 0.20:
            quote["bid"], quote["ask"] = ask, bid                                                    # crossed
        elif q < 0.22:
            quote["bid"] = None
        elif q < 0.24:
            quote["bid"] = 0.0
        elif q < 0.27:
            quote = None                                                                             # unreachable
        held, entry = 0.0, None
        if rnd.random() < 0.42 and n > 8:
            held = round(10000.0 / last_c * rnd.choice((rnd.uniform(0.6, 0.999), rnd.uniform(0.9, 1.1))), 8)
            k = rnd.randrange(1, 8)
            entry = (opened - timedelta(seconds=k * step)).isoformat()   # the close of the bar k bars back
        sent = []
        if rnd.random() < 0.1:                                           # this bar's orders already sent
            stamp_c = opened.isoformat().replace("-", "").replace(":", "").replace("+00:00", "Z")   # as _client()
            sent = [("%s-%s-%s" % (FWD_IDS[sym], stamp_c, side))[:48] for side in ("buy", "sell")]
        case["books"][sym] = {"raw": raw, "quote": quote, "held": held, "entry": entry, "sent": sent}
    return case


# -- Coinbase daily ----------------------------------------------------------------------------------------------
def coinbase_case(seed):
    """a sequence of forward_cycle passes for FWD_COINBASE_SMA200_V1 sharing one decision state: the first pass
    of a UTC day (inside or just outside 00:00-00:05), a second pass the same day, the next day's first pass.
    Each pass: Coinbase's daily candles (enough / too few / a gap), the ticker (bid, ask) and its receipt time
    relative to the decision clock (before it: 0-90 s; after it: the source's live order of operations)."""
    rnd = random.Random(seed)
    day0 = BASE + timedelta(days=rnd.randrange(210, 300))
    n = rnd.choice((300, 300, 300, 250, rnd.randrange(150, 205)))
    start = day0 - timedelta(days=n)
    closes = []
    px = rnd.uniform(20000, 120000)
    for _ in range(n + 3):
        px *= 1 + rnd.gauss(0.001, 0.03)
        closes.append(_px(px))
    gap = rnd.randrange(0, n) if rnd.random() < 0.12 else None
    steps = []
    for k, day in enumerate((day0, day0, day0 + timedelta(days=1))):
        u = rnd.random()
        if k == 1:                                                       # a later pass the same UTC day
            moment = min(day + timedelta(seconds=86399), moment + timedelta(seconds=rnd.choice((30, 60, 299, 4000))))
        elif u < 0.8:
            moment = day + timedelta(seconds=rnd.choice((0, 1, rnd.randrange(0, 300), 299)))
        else:
            moment = day + timedelta(seconds=rnd.choice((300, rnd.randrange(300, 7200), 86399)))
        hist = []
        for i in range(n + 3):
            d = start + timedelta(days=i)
            if d + timedelta(days=1) > moment:
                break
            if gap is not None and i == gap:
                continue
            hist.append({"t": int(d.timestamp()), "c": closes[i]})
        ref = closes[min(len(closes) - 1, n + k)]
        bid = _px(ref * (1 - rnd.uniform(0, 0.0003)))
        ask = _px(bid * (1 + rnd.uniform(0.00001, 0.0003)))
        q = rnd.random()
        quote = {"bid": bid, "ask": ask}
        if q < 0.05:
            quote["bid"], quote["ask"] = ask, bid                        # crossed
        elif q < 0.08:
            quote["ask"] = 0.0
        elif q < 0.10:
            quote["bid"], quote["ask"] = _px(bid * 200), _px(ask * 200)  # 0.01 x ask above the $10,000 cap
        elif q < 0.13:
            quote = None                                                 # no ticker
        r = rnd.random()
        lag = rnd.uniform(0.05, 2.0) if r < 0.45 else (-rnd.uniform(0, 29.9) if r < 0.85 else -rnd.uniform(30.01, 90))
        steps.append({"moment": _iso(moment), "history": hist, "quote": quote,
                      "received_at": _iso(moment + timedelta(seconds=lag)) if quote else None})
    return {"seed": seed, "steps": steps}
