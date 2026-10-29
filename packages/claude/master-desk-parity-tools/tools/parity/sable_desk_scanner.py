"""sable_desk_scanner: the legacy desk-native completed-bar support scanner and its two-pass tape (autopilot-desk
@48e8f90f: desk-core.mjs scoreDeskQuote / buildDeskScan / deskScanToBundle, quote-core.mjs quoteFromCompletedBars,
screen-core.mjs screenScore / pickDeep / quoteFromSparkMeta, features.mjs sessionFromQuote; the SOURCE modules run
unmodified under Node 22) vs the port (desk/sleeves/sable/desk_scanner.py) on the same inputs.

Cases:
  quotes     random desk quotes — price, support, VWAP, ATR, extension, RSI / MACD (number, null or absent),
             volume ratios, 52-week ranges (incl. null / inverted), 5-minute OHLC vs spark-screen sources, earnings,
             ETF / stock kinds, day previous closes, Tensor reads (buy / sell / states) and mandates (ETF-only,
             under-the-radar, caps) -> scoreDeskQuote, and per batch of 30 -> buildDeskScan + deskScanToBundle
  bars       random completed 5-minute tapes (1-90 bars, gaps in fields) -> quoteFromCompletedBars
  metas      random Yahoo spark metas (prices, day / 52-week ranges, 0-80 five-minute closes, ETF flags) ->
             quoteFromSparkMeta (all fields but the display name / sector) and screenScore; per batch -> pickDeep
             with positions, pins and the vanes.
Compared exactly (JSON null = undefined).

    AUTOPILOT_DESK=<autopilot-desk @48e8f90f> python3 -m tools.parity.run sable_desk_scanner"""
import random

from desk.sleeves.sable import desk_scanner as ds

from . import write_receipt
from .node_pinned import cleanup, run as node_run, same, stage

COMMIT = "48e8f90f5d9def28363eb4013dac4dd8d78f74bf"
FILES = {
    "src/lib/scanner/desk-core.mjs": "1b5f90418acae9d53d3bf25caa251f86843351b2",
    "src/lib/scanner/features.mjs": "843833d1f8fab0669912c6bf1cd3860a771f735e",
    "src/lib/market/quote-core.mjs": "7b2bac129c4c65410229e08dbd6fa2579926a696",
    "src/lib/desk/screen-core.mjs": "4a94dc93d6dd1cda5fc61b83a77c39fad1358073",
    "src/lib/desk/sectors.mjs": "e40ca396a132dd7469401135001c1a553c64afd2",
    "src/lib/desk/ledger-core.mjs": "6342ddc827978ceaecefa2c893bbc85e7d1361f8",
}
N_QUOTES = 3000
N_BARS = 1500
N_METAS = 1500
BATCH = 30
TICKERS = ["AAPL", "MSFT", "NVDA", "IRDM", "OSCR", "SMH", "QQQ", "SPY", "IWM", "AMD", "CRWD", "TSLA", "ONDS", "AMPX",
           "LLY", "BRK.B", "X", "abc", "1BAD", "META", "AVGO", "V", "MA", "JPM", "UNH", "GOOGL", "AMZN", "PLTR"]

DRIVER = r"""
import { readFileSync } from "node:fs";
import { scoreDeskQuote, buildDeskScan, deskScanToBundle } from "./src/lib/scanner/desk-core.mjs";
import { quoteFromCompletedBars } from "./src/lib/market/quote-core.mjs";
import { screenScore, pickDeep, quoteFromSparkMeta } from "./src/lib/desk/screen-core.mjs";
const P = JSON.parse(readFileSync(0, "utf8"));
const quotes = P.quotes.map((c) => scoreDeskQuote(c.quote, c.tensor, c.mandate));
const scans = P.scans.map((b) => { const s = buildDeskScan({ quotes: b.quotes, reads: b.reads, mandate: b.mandate,
  completedBarAt: b.completedBarAt, now: 0 }); delete s.generatedAt; return { scan: s, bundle: deskScanToBundle(s) }; });
const bars = P.bars.map((c) => quoteFromCompletedBars(c.meta, c.bars, c.source));
const metas = P.metas.map((c) => { const q = quoteFromSparkMeta(c.meta, c.ticker, c.seed); if (q) { delete q.name; delete q.sector; }
  return { q, s: screenScore(c.row) }; });
const deep = P.deep.map((c) => pickDeep(c.rows, c.opts));
console.log(JSON.stringify({ quotes, scans, bars, metas, deep }));
"""


def _r(rnd, p, lo, hi, nd=3):
    """a number, null or absent (returned as a sentinel to omit)."""
    x = rnd.random()
    if x < p:
        return "__absent__"
    if x < p * 1.6:
        return None
    return round(rnd.uniform(lo, hi), nd)


def _put(d, k, v):
    if v != "__absent__":
        d[k] = v


def make_quote(rnd):
    px = round(rnd.uniform(0.5, 600), 2) if rnd.random() > 0.02 else rnd.choice([0, -1, None])
    q = {"ticker": rnd.choice(TICKERS)}
    _put(q, "price", px)
    base = px if isinstance(px, (int, float)) and px > 0 else 50
    _put(q, "support", _r(rnd, 0.1, base * 0.85, base * 1.02, 2))
    _put(q, "vwap", _r(rnd, 0.15, base * 0.97, base * 1.03, 2))
    _put(q, "atr", _r(rnd, 0.1, 0, base * 0.03, 3))
    _put(q, "extensionAtr", _r(rnd, 0.3, -0.5, 3.0, 3))
    _put(q, "rsi", _r(rnd, 0.2, 20, 85, 2))
    _put(q, "macdHist", _r(rnd, 0.2, -0.4, 0.4, 3))
    _put(q, "volume", _r(rnd, 0.1, 0, 5e6, 0))
    _put(q, "avgVolume", _r(rnd, 0.1, 0, 5e6, 0))
    lo = round(base * rnd.uniform(0.4, 1.0), 2)
    _put(q, "low52", rnd.choice([lo, lo, None, "__absent__", 0]))
    _put(q, "high52", rnd.choice([round(base * rnd.uniform(1.0, 2.5), 2), round(lo * 0.9, 2), None, "__absent__"]))
    src = rnd.choice(["live-read", "live-read", "live-read-quote", "demo", "other", "__absent__"])
    _put(q, "source", src)
    if rnd.random() < 0.3:
        q["screen"] = rnd.random() < 0.7
    if rnd.random() < 0.6:
        q["completedBarAt"] = rnd.choice([1.79e12, 0, None])
    if rnd.random() < 0.3:
        q["sparkBars"] = rnd.choice([0, 12, None])
    if rnd.random() < 0.06:
        q["earningsImminent"] = rnd.choice([True, 1])
    _put(q, "kind", rnd.choice(["stock", "etf", "ETF", "__absent__", None]))
    _put(q, "dayPrevClose", _r(rnd, 0.4, base * 0.95, base * 1.05, 2))
    _put(q, "prevClose", _r(rnd, 0.3, base * 0.95, base * 1.05, 2))
    tensor = None
    if rnd.random() < 0.3:
        tensor = {}
        _put(tensor, "paperSell", rnd.choice([True, False, "__absent__"]))
        _put(tensor, "paperBuy", rnd.choice([True, False, 1, "__absent__"]))
        _put(tensor, "state", rnd.choice(["VECTOR_BUY", "REVERSAL_WINDOW", "NEUTRAL", None, "__absent__"]))
    mandate = None
    if rnd.random() < 0.5:
        mandate = {}
        _put(mandate, "assetClass", rnd.choice(["etfs", "both", "__absent__"]))
        _put(mandate, "allowStocks", rnd.choice([True, False, "__absent__"]))
        _put(mandate, "maxPositions", rnd.choice([2, 4, 6, 7, 13, "__absent__"]))
        _put(mandate, "radarCap", rnd.choice([5, 36, 60, "__absent__"]))
        _put(mandate, "discoveryPreference", rnd.choice(["under_the_radar", "none", "__absent__"]))
    return {"quote": q, "tensor": tensor, "mandate": mandate}


def make_bars(rnd):
    n = rnd.randint(1, 90)
    px, out, t = rnd.uniform(5, 300), [], 1_790_000_000
    for _ in range(n):
        o = px * (1 + rnd.gauss(0, 0.002))
        c = px * (1 + rnd.gauss(0, 0.004))
        b = {"time": t, "open": round(o, 3), "high": round(max(o, c) * 1.002, 3), "low": round(min(o, c) * 0.998, 3),
             "close": round(c, 3), "volume": float(rnd.randint(0, 50000))}
        for k in list(b):
            if rnd.random() < 0.01:
                if rnd.random() < 0.5:
                    b.pop(k)
                else:
                    b[k] = None
        out.append(b)
        px = c
        t += 300
    meta = {"ticker": rnd.choice(TICKERS), "kind": rnd.choice(["stock", "etf"])}
    return {"meta": meta, "bars": out, "source": rnd.choice(["live-read", "demo"])}


def make_meta(rnd):
    px = round(rnd.uniform(1, 500), 2)
    m = {"symbol": rnd.choice(TICKERS + [""])}
    _put(m, "regularMarketPrice", rnd.choice([px, px, None, "__absent__", 0]))
    _put(m, "previousClose", _r(rnd, 0.3, px * 0.95, px * 1.05, 2))
    _put(m, "chartPreviousClose", _r(rnd, 0.3, px * 0.95, px * 1.05, 2))
    _put(m, "regularMarketDayHigh", _r(rnd, 0.2, px, px * 1.04, 2))
    _put(m, "regularMarketDayLow", _r(rnd, 0.2, px * 0.96, px, 2))
    _put(m, "fiftyTwoWeekLow", _r(rnd, 0.2, px * 0.4, px, 2))
    _put(m, "fiftyTwoWeekHigh", _r(rnd, 0.2, px, px * 2, 2))
    _put(m, "regularMarketVolume", _r(rnd, 0.2, 0, 1e7, 0))
    _put(m, "instrumentType", rnd.choice(["EQUITY", "ETF", "etf", "__absent__", None]))
    k = rnd.randint(0, 80)
    if rnd.random() < 0.8:
        m["sparkCloses"] = [rnd.choice([round(px * (1 + rnd.gauss(0, 0.004)), 3)] * 9 + [None]) for _ in range(k)]
        m["sparkTimes"] = [1_790_000_000 + 300 * i for i in range(k)]
    seed = rnd.choice([None, {"kind": "etf", "avgVolume": 2e6}, {"kind": "stock"}, {"avgVolume": 0}])
    row = make_quote(rnd)["quote"]
    if rnd.random() < 0.5:
        row["low"] = row.pop("support", None)
    if rnd.random() < 0.3:
        row["dayLow"] = round(rnd.uniform(1, 500), 2)
    return {"meta": m, "ticker": rnd.choice([m["symbol"], rnd.choice(TICKERS), ""]), "seed": seed, "row": row}


def _strip_sentinels(o):
    if isinstance(o, dict):
        return {k: _strip_sentinels(v) for k, v in o.items() if v != "__absent__"}
    if isinstance(o, list):
        return [_strip_sentinels(v) for v in o]
    return o


def run():
    rnd = random.Random("sable-ds")
    quotes = [_strip_sentinels(make_quote(rnd)) for _ in range(N_QUOTES)]
    scans = []
    for k in range(0, N_QUOTES, BATCH):
        b = {"quotes": {}, "reads": [], "mandate": quotes[k]["mandate"], "completedBarAt": rnd.choice([None, 1.79e12])}
        for c in quotes[k:k + BATCH]:
            b["quotes"][str(c["quote"].get("ticker"))] = c["quote"]
            if c["tensor"] is not None and rnd.random() < 0.7:
                b["reads"].append(dict(c["tensor"], ticker=c["quote"].get("ticker")))
        scans.append(b)
    bars = [make_bars(rnd) for _ in range(N_BARS)]
    metas = [_strip_sentinels(make_meta(rnd)) for _ in range(N_METAS)]
    deep = []
    for k in range(0, N_METAS, BATCH):
        rows = [m["row"] for m in metas[k:k + BATCH]]
        opts = {"positions": rnd.sample(TICKERS, rnd.randint(0, 3)), "pins": rnd.sample(TICKERS, rnd.randint(0, 5)),
                "cap": rnd.choice([5, 10, 36])}
        deep.append({"rows": rows, "opts": opts})
    payload = {"quotes": quotes, "scans": scans, "bars": bars, "metas": metas, "deep": deep}
    tree = stage("AUTOPILOT_DESK", "/home/user/autopilot-desk", FILES)
    try:
        theirs = node_run(tree, DRIVER, payload)
    finally:
        cleanup(tree)
    diffs, identical, stats = [], 0, {"actions": {}, "hands": 0}

    def chk(kind, i, mine, js):
        nonlocal identical
        d = same(mine, js)
        if d:
            diffs.append({kind: i, "diff": d[:4]})
        else:
            identical += 1

    for i, (c, t) in enumerate(zip(quotes, theirs["quotes"])):
        r = ds.score_desk_quote(c["quote"], c["tensor"], c["mandate"])
        chk("quote", i, r, t)
        a = (r or {}).get("action")
        stats["actions"][str(a)] = stats["actions"].get(str(a), 0) + 1
    for i, (b, t) in enumerate(zip(scans, theirs["scans"])):
        s = ds.build_desk_scan(b["quotes"], b["reads"], b["mandate"], b["completedBarAt"])
        mb = {k: v for k, v in ds.desk_scan_to_bundle(s).items()
              if k in ("status", "candidates", "pressure", "missing", "scanned", "fillCap", "radarCap")}
        chk("scan", i, {"scan": s, "bundle": mb},
            dict(t, bundle={k: v for k, v in t["bundle"].items() if k in ("status", "candidates", "pressure", "missing",
                                                                          "scanned", "fillCap", "radarCap")}))
        stats["hands"] += len(s["hands"])
    for i, (c, t) in enumerate(zip(bars, theirs["bars"])):
        q = ds.quote_from_completed_bars(c["meta"], c["bars"], c["source"])
        if q is not None and t is not None:
            t = {k: v for k, v in t.items() if k not in ("name", "sector")}
        chk("bars", i, q, t)
    for i, (c, t) in enumerate(zip(metas, theirs["metas"])):
        chk("meta", i, {"q": ds.quote_from_spark_meta(c["meta"], c["ticker"], c["seed"]),
                        "s": ds.screen_score(c["row"])}, t)
    for i, (c, t) in enumerate(zip(deep, theirs["deep"])):
        o = c["opts"]
        chk("deep", i, ds.pick_deep(c["rows"], o["positions"], o["pins"], cap=o["cap"]), t)
    n = len(quotes) + len(scans) + len(bars) + len(metas) + len(deep)
    res = {"sleeve": "sable_desk_scanner", "cases": n, "identical": identical, "diffs": diffs[:50],
           "n_diffs": len(diffs), "stats": stats,
           "method": "desk-core / quote-core / screen-core / features .mjs (autopilot-desk @48e8f90f, blob-verified) "
                     "under Node 22 vs the Python port, same inputs (bundle compared on the scan fields)",
           "source": {"repo": "autopilot-desk", "commit": COMMIT, "files": FILES}, "sleeves": ["sable_support_scanner"]}
    write_receipt("sable_desk_scanner", res)
    return res
