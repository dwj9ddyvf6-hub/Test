"""Author_book: the Author scanner book's decision code — the Signal Prism scan, the buy desk's distill, the curl /
select / washout reads, the bottom screen with its sector tape and fund overlay, the session-tape rebase, the book
assembly and the roster — vs their sources at Author-desk @652db7af under Node 22 (unmodified: the TypeScript with
types erased by the TypeScript compiler; desk-autopilot.mjs's keepNearBuy / orderBook / filterBookForCurl read
verbatim out of the pinned script; the source's clock — Date.now() / new Date() — set per case, the only stub).

  prism    prism/scan.ts scanPrismSymbol(symbol, bars, bench) on random daily tapes, with and without the SPY bench
           — vs desk/sleeves/Author/prism.py
  select   select.ts readSelect, curl.ts readCurl / curlNote / keepAfterCurl on random tapes and lasts on and off
           their marked levels — vs desk/sleeves/Author/book.py
  bottom   bottom-screen.ts scoreBottom / scoreBottomNamed with the sector tape (sector-tape.ts readSectorTape over
           SPY and the sector ETFs) and fund evidence (fund-overlay.ts applyFundOverlay / mergeSec); a share of the
           tapes searched until the port reads a BUY (the branch random walks rarely reach)
  distill  buy-desk.ts distillBuys over a random universe (mapped / unmapped names, SPY, the sector and regime
           ETFs; rows from the prism scan above), then the scan worker's keepAfterCurl cut and the autopilot's
           orderBook -> filterBookForCurl -> keepNearBuy book assembly
  session  after-hours.ts sessionTape / tapeNote / applySessionTape (decide + rebasePlan) / liveStop /
           aggressiveTarget / liveAccuratePlan on random 5-minute tapes around the clock
  roster   roster.ts curateRoster sequences (adds, keeps, demotions, NO_PROGRESS / TTL / REL_WEAK / STOP / TARGET
           drops, cluster cuts, the 24-name cap) with stampTensorBuy / stampTensorSell between them
Cases are deterministic and seeded. Compared exactly (JSON null = undefined).

    Author_DESK=<Author-desk @652db7af> PARITY_BLOBS=<dir with the voice/machine JSON blobs>
        python3 -m tools.parity.run Author_book"""
import math
import random

from desk.sleeves.Author import book as B
from desk.sleeves.Author import levels as L
from desk.sleeves.Author import prism as PR

from . import write_receipt
from .Author_src import BOOK_DATA, BOOK_TS, COMMIT, DAY_MS, daily_bars
from .node_pinned import cleanup, run as node_run, same, stage, transpile_ts

N_PRISM = 1200
N_SELECT = 1500
N_BOTTOM = 1200
N_DISTILL = 300
N_SESSION = 1500
N_ROSTER = 400
BATCH = 50

EXTRA_TS = {
    "src/lib/workdesk/roster.ts": "cfb60b83f8fa7872a57e722d1cba6a9ad377b7e8",
    "src/lib/workdesk/cluster.ts": "c0677336bd094fcddde96e0fd189c99f9a0ab051",
}
SCRIPTS = {"scripts/desk-autopilot.mjs": "470a6cd72511d9ea981d58c729f63506b64fb499"}

CLOCK = r"""
const RealDate = Date;
let NOW = 0;
class FakeDate extends RealDate {
  constructor(...a) { if (a.length === 0) super(NOW); else super(...a); }
  static now() { return NOW; }
}
globalThis.Date = FakeDate;
const setNow = (t) => { NOW = t; };
const { readFileSync } = require("node:fs");
const P = JSON.parse(readFileSync(0, "utf8"));
"""

DRIVER_PRISM = CLOCK + r"""
const S = require("./src/lib/prism/scan.js");
const out = P.cases.map((c) => { setNow(c.now); return S.scanPrismSymbol(c.symbol, c.bars, c.bench || undefined); });
console.log(JSON.stringify(out));
"""

DRIVER_SELECT = CLOCK + r"""
const SE = require("./src/lib/workdesk/select.js");
const CU = require("./src/lib/workdesk/curl.js");
const out = P.cases.map((c) => {
  setNow(c.now);
  const curl = CU.readCurl(c.bars || undefined);
  return { sel: SE.readSelect(c.bars || undefined, c.last), curl, note: CU.curlNote(curl, c.seed),
           keep: CU.keepAfterCurl(c.setup, c.bars || undefined) };
});
console.log(JSON.stringify(out));
"""

DRIVER_BOTTOM = CLOCK + r"""
const BS = require("./src/lib/workdesk/bottom-screen.js");
const ST = require("./src/lib/workdesk/sector-tape.js");
const FO = require("./src/lib/workdesk/fund-overlay.js");
const out = P.cases.map((c) => {
  setNow(c.now);
  const map = new Map(Object.entries(c.barsBy));
  const tape = c.withTape ? ST.readSectorTape(map) : undefined;
  const ctx = { spy: c.ctx.spy || undefined, sectors: c.ctx.sectors, spyUnder200: c.ctx.spyUnder200,
                spyNewLow20: c.ctx.spyNewLow20, tape, funds: new Map(Object.entries(c.funds)) };
  return { tape: tape ?? null, score: BS.scoreBottom(c.bars || undefined, c.last, ctx),
           named: BS.scoreBottomNamed(c.symbol, c.bars || undefined, c.last, ctx),
           sec: FO.mergeSec(c.ev, c.sec), overlay: FO.applyFundOverlay(c.hit, c.ev2) };
});
console.log(JSON.stringify(out));
"""

AUTOPILOT = r"""
const SRC = readFileSync("./scripts/desk-autopilot.mjs", "utf8");
function extract(name) {
  const i = SRC.indexOf("function " + name + "(");
  if (i < 0) throw new Error("no " + name);
  let j = SRC.indexOf("{", SRC.indexOf(")", i));
  let depth = 0, k = j;
  for (; k < SRC.length; k++) {
    if (SRC[k] === "{") depth++;
    else if (SRC[k] === "}") { depth--; if (depth === 0) break; }
  }
  return SRC.slice(i, k + 1);
}
const CP = require("./src/lib/workdesk/copy.js");
const CU2 = require("./src/lib/workdesk/curl.js");
const quiet = { error: () => {}, log: () => {} };
const AP = new Function("buyCall", "callRank", "keepAfterCurl", "curlNote", "console",
  [extract("keepNearBuy"), extract("orderBook"), extract("filterBookForCurl")].join("\n") +
  "\nreturn { keepNearBuy, orderBook, filterBookForCurl };")(CP.buyCall, CP.callRank, CU2.keepAfterCurl, CU2.curlNote, quiet);
"""

DRIVER_DISTILL = CLOCK + AUTOPILOT + r"""
const BD = require("./src/lib/workdesk/buy-desk.js");
const CU = require("./src/lib/workdesk/curl.js");
const ST = require("./src/lib/workdesk/sector-tape.js");
const out = P.cases.map((c) => {
  setNow(c.now);
  const map = new Map(Object.entries(c.barsBy));
  const funds = new Map(Object.entries(c.funds));
  const d = BD.distillBuys(c.rows, c.noBars ? undefined : map, funds);
  const kept = [];
  for (const s of d.buys) { const k = CU.keepAfterCurl(s, map.get(s.symbol)); if (k.keep) kept.push(s); }
  let book = AP.filterBookForCurl(AP.orderBook(kept), map);
  const stamped = book.map((s, i) => (c.lasts[i] == null ? s : { ...s, afterHours: { last: c.lasts[i] } }));
  return { d, kept, book, near: AP.keepNearBuy(stamped), tape: ST.readSectorTape(map) };
});
console.log(JSON.stringify(out));
"""

DRIVER_SESSION = CLOCK + r"""
const AH = require("./src/lib/workdesk/after-hours.js");
const out = P.cases.map((c) => {
  setNow(c.now);
  const tape = AH.sessionTape(c.bars || undefined, c.now);
  return { tape, note: AH.tapeNote(tape, c.now), applied: AH.applySessionTape(c.setup, tape, c.now, c.daily || undefined),
           stop: AH.liveStop(c.buy, c.daily || undefined), agg: AH.aggressiveTarget(c.daily || undefined, c.buy, c.risk),
           live: AH.liveAccuratePlan(c.setup, c.last, c.daily || undefined) };
});
console.log(JSON.stringify(out));
"""

DRIVER_ROSTER = CLOCK + r"""
const R = require("./src/lib/workdesk/roster.js");
const out = P.cases.map((c) => {
  let st = c.start;
  const steps = [];
  for (const s of c.steps) {
    setNow(s.now);
    if (s.kind === "curate") st = R.curateRoster(st, s.book, new Map(Object.entries(s.quotes)), s.dateEt, new Date(s.now), []);
    else if (s.kind === "buy") st = R.stampTensorBuy(st, s.symbol, s.at);
    else st = R.stampTensorSell(st, s.symbol, s.at);
    steps.push(JSON.parse(JSON.stringify(st)));
  }
  return steps;
});
console.log(JSON.stringify(out));
"""


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    return x


def _start(rnd):
    return 1_700_000_000_000 - (1_700_000_000_000 % DAY_MS) + rnd.randint(0, 500) * DAY_MS


# -- prism -------------------------------------------------------------------------------------------------------------
def prism_case(rnd, k):
    n = rnd.choice([0, 1, 30, 54, 55, 56, 60, 80, 120, 160, 200, 260, 320, 400])
    stamp = rnd.choice([4 * 3600_000, 13 * 3600_000 + 30 * 60_000])
    start = _start(rnd)
    bars = daily_bars(rnd, n, start_ms=start, stamp=stamp, regime=rnd.choice([None, None, None, "drop", "coil", "rip"]))
    bench = None
    x = rnd.random()
    if x < 0.6:
        bench = daily_bars(rnd, n + rnd.choice([0, 0, 5, -3]) if n > 5 else n, start_ms=start, stamp=stamp,
                           px=rnd.uniform(300, 600), regime=rnd.choice([None, "trend", "chop"]))
    elif x < 0.7:
        bench = daily_bars(rnd, rnd.choice([5, 15, 40]), start_ms=start, stamp=stamp)
    now = (bars[-1]["t"] if bars else 1_790_000_000_000) + 20 * 3600_000
    return {"symbol": rnd.choice(["NVDA", "AAPL", "SPY", "brk.b", "X"]) + str(k % 5), "bars": bars, "bench": bench,
            "now": now}


def port_prism(c):
    return PR.scan_prism_symbol(c["symbol"], c["bars"], c["bench"])


# -- select ------------------------------------------------------------------------------------------------------------
def _pick_last(rnd, bars, now):
    lastc = bars[-1]["c"] if bars else rnd.uniform(5, 50)
    x = rnd.random()
    if x < 0.04:
        return rnd.choice([0, None, -1])
    if x < 0.3 and bars:
        lv = B.marked_levels(bars, lastc)
        lv = [l for l in lv if math.isfinite(l["px"]) and l["px"] > 0]
        if lv:
            return round(rnd.choice(lv)["px"] * rnd.uniform(0.99, 1.01), 2)
    if x < 0.45 and len(bars) >= 50:
        fibs = L.fib_levels(bars, now)
        if fibs:
            return round(rnd.choice(fibs)["px"] * rnd.uniform(0.985, 1.015), 2)
    return rnd.choice([lastc, round(lastc * rnd.uniform(0.94, 1.06), 2)])


def select_case(rnd, k):
    n = rnd.choice([0, 10, 19, 20, 25, 39, 40, 50, 60, 80, 120, 160, 200, 260])
    bars = daily_bars(rnd, n, regime=rnd.choice([None, None, "drop", "coil", "chop"]))
    now = (bars[-1]["t"] if bars else 1_790_000_000_000) + rnd.choice([0, 3600_000, 20 * 3600_000, 3 * DAY_MS])
    return {"bars": bars or None, "last": _pick_last(rnd, bars, now), "now": now,
            "seed": rnd.choice(["", "NVDA", "x", "AB:1"]),
            "setup": {"curlOk": rnd.choice([True, False, None]), "atSupport": rnd.choice([True, False, None]),
                      "extensionR": rnd.uniform(-1, 2)}}


def port_select(c):
    bars, now = c["bars"], c["now"]
    curl = B.read_curl(bars)
    return {"sel": B.read_select(bars, c["last"], now), "curl": curl, "note": B.curl_note(curl, c["seed"]),
            "keep": B.keep_after_curl({k: v for k, v in c["setup"].items() if v is not None}, bars)}


# -- bottom ------------------------------------------------------------------------------------------------------------
MAPPED = ["NVDA", "AMD", "XOM", "AAPL", "LLY", "NKE", "FCX", "NEM", "O", "MOS", "TSLA"]
UNMAPPED = ["PLTR", "IONQ", "ZZZ", "ASTS"]
ETFS = ["SPY", "IWM", "XLK", "SMH", "SOXX", "XLE", "XOP", "XLF", "IYF", "XBI", "IBB", "GDX", "COPX", "USO", "SLV",
        "GLD", "XLY", "XHB", "XLP", "XLU"]


def _bottom_tape(rnd, start, stamp):
    """a long drop off a high, then a base (an undercut / spring or a tightening range), dollar volume >= $15M."""
    px = rnd.uniform(15, 200)
    a = daily_bars(rnd, rnd.randint(120, 200), start_ms=start, stamp=stamp, px=px, regime="trend")
    b = daily_bars(rnd, rnd.randint(30, 70), start_ms=a[-1]["t"] + DAY_MS, stamp=stamp, px=a[-1]["c"], regime="drop")
    c = daily_bars(rnd, rnd.randint(25, 45), start_ms=b[-1]["t"] + DAY_MS, stamp=stamp, px=b[-1]["c"],
                   regime=rnd.choice(["coil", "chop"]))
    out = a + b + c
    vol = rnd.uniform(4e5, 3e6)
    for x in out:
        x["v"] = float(int(vol * rnd.uniform(0.5, 1.5) * (rnd.uniform(2, 4) if rnd.random() < 0.05 else 1)))
    return out


def _etf_bars(rnd, n, start, stamp):
    return daily_bars(rnd, n, start_ms=start, stamp=stamp, px=rnd.uniform(30, 500),
                      regime=rnd.choice([None, "trend", "drop", "chop"]))


def _fund(rnd, sym):
    return {"symbol": sym, "status": rnd.choice(["ok", "unknown", "bad"]),
            "sources": {"yahoo": rnd.choice(["ok", "fail", "skip"]), "sec": rnd.choice(["ok", "fail", "skip"])},
            "quality": rnd.choice([0, 1]), "flow": rnd.choice([0, 1]), "bad": rnd.random() < 0.3,
            "line": rnd.choice(["", "Filings still show cash on the balance sheet."]),
            "lines": rnd.choice([[], ["Operations still throw off cash.", "x"]]), "at": "2026-10-16T12:00:00.000Z"}


def bottom_case(rnd, k):
    start, stamp = _start(rnd), rnd.choice([4 * 3600_000, 13 * 3600_000 + 30 * 60_000])
    n_etf = rnd.choice([0, 59, 60, 79, 80, 200, 300])
    bars_by = {}
    for e in rnd.sample(ETFS, rnd.randint(0, len(ETFS))):
        bars_by[e] = _etf_bars(rnd, n_etf if e != "SPY" else rnd.choice([n_etf, 0, 120, 300]), start, stamp)
    sym = rnd.choice(MAPPED + UNMAPPED + ["SPY", "BTC-USD"])
    want = rnd.random() < 0.35
    bars = None
    for _ in range(60 if want else 1):
        bars = _bottom_tape(rnd, start, stamp) if rnd.random() < 0.7 else \
            daily_bars(rnd, rnd.choice([0, 30, 59, 60, 80, 126, 200, 260]), start_ms=start, stamp=stamp)
        if not want or not bars:
            break
        if B.score_bottom(bars, bars[-1]["c"])["tag"] == "BUY":
            break
    lastc = bars[-1]["c"] if bars else 10.0
    last = rnd.choice([lastc, lastc, round(lastc * rnd.uniform(0.97, 1.03), 2), 0, 5.0])
    spy = bars_by.get("SPY")
    funds = {s: _fund(rnd, s) for s in rnd.sample([sym] + MAPPED, rnd.randint(0, 3))}
    hit = {"tag": "BUY", "quality": rnd.randint(0, 3), "total": rnd.randint(0, 12),
           "size": rnd.choice(["Full size", "Half size"]), "live": True}
    sec = rnd.choice([None, {"cash": rnd.choice([None, 0, 1e9]), "debt": rnd.choice([None, 1e8, 2e10]),
                             "shares": rnd.choice([None, 1e8, 1.3e8]), "sharesYearAgo": rnd.choice([None, 0, 1e8]),
                             "netIncome": rnd.choice([None, -5e7, 5e7]), "form4Buys90d": rnd.choice([0, 2, 3]),
                             "form4Sells90d": rnd.choice([0, 1, 5])}])
    return {"symbol": sym, "bars": bars or None, "last": last, "barsBy": bars_by, "withTape": rnd.random() < 0.8,
            "ctx": {"spy": spy, "sectors": {e: b for e, b in bars_by.items() if e in B.SECTOR_ETFS and b},
                    "spyUnder200": rnd.random() < 0.3, "spyNewLow20": rnd.random() < 0.3},
            "funds": funds, "now": (bars[-1]["t"] if bars else 1_790_000_000_000) + 20 * 3600_000,
            "ev": _fund(rnd, sym), "sec": sec, "hit": hit, "ev2": rnd.choice([None, _fund(rnd, sym)])}


def port_bottom(c):
    bars_by = c["barsBy"]
    tape = B.read_sector_tape(bars_by, c["now"]) if c["withTape"] else None
    ctx = {"spy": c["ctx"]["spy"], "sectors": c["ctx"]["sectors"], "spyUnder200": c["ctx"]["spyUnder200"],
           "spyNewLow20": c["ctx"]["spyNewLow20"], "tape": tape, "funds": c["funds"]}
    return {"tape": tape, "score": B.score_bottom(c["bars"], c["last"], ctx),
            "named": B.score_bottom_named(c["symbol"], c["bars"], c["last"], ctx),
            "sec": B.merge_sec(c["ev"], c["sec"]), "overlay": B.apply_fund_overlay(c["hit"], c["ev2"])}


# -- distill -----------------------------------------------------------------------------------------------------------
def _turn_etf(rnd, n, start, stamp):
    """a sector ETF that lagged SPY for months and has led it for the last four weeks (sector-tape "turn")."""
    a = daily_bars(rnd, n - 20, start_ms=start, stamp=stamp, px=rnd.uniform(30, 300), regime="drop")
    b = daily_bars(rnd, 20, start_ms=a[-1]["t"] + DAY_MS, stamp=stamp, px=a[-1]["c"], regime="trend")
    return a + b


UNIVERSE = MAPPED + UNMAPPED + ["MU", "INTC", "CVX", "AMZN", "META", "GOLD", "SBUX", "PFE", "AVGO", "QCOM", "MRVL",
                                "ORCL", "ADBE", "EOG", "SLB", "ABBV", "MRK", "HD", "LOW", "SCCO", "AEM", "KGC", "DE"]


def _ceiling_case(rnd, start, stamp):
    """one bottom-screen BUY tape under 26-34 names, no sector ETFs (every name's policy is buy): more admitted names
    than the 20-name book ceiling."""
    tape = None
    for _ in range(400):
        tape = _bottom_tape(rnd, start, stamp)
        last = tape[-1]["c"]
        if B.score_bottom(tape, last)["tag"] == "BUY" and \
                L.admit_ticker("X", tape, last, tape[-1]["t"] + 20 * 3600_000)["live"]:
            break
    bars_by = {"SPY": _etf_bars(rnd, 300, start, stamp)}
    for s in rnd.sample(UNIVERSE, rnd.randint(26, 34)):
        bars_by[s] = [dict(b) for b in tape]
    return bars_by


def distill_case(rnd, k):
    start, stamp = _start(rnd), rnd.choice([4 * 3600_000, 13 * 3600_000 + 30 * 60_000])
    n_etf = rnd.choice([80, 200, 300])
    mode = rnd.choice(["noetf", "turn", "turn", "random"])
    if k % 25 == 0:
        bars_by = _ceiling_case(rnd, start, stamp)
        now = max(b[-1]["t"] for b in bars_by.values() if b) + 20 * 3600_000
        rows = [PR.scan_prism_symbol(s, bars_by[s], bars_by["SPY"]) for s in sorted(bars_by)]
        return {"rows": rows, "barsBy": bars_by, "funds": {}, "now": now, "noBars": False,
                "lasts": [None] * 40}
    bars_by = {}
    for e in ETFS:
        if mode == "noetf" and e != "SPY":
            continue
        if rnd.random() < 0.85 or e == "SPY":
            bars_by[e] = _turn_etf(rnd, n_etf, start, stamp) if (mode == "turn" and e != "SPY" and rnd.random() < 0.7) \
                else _etf_bars(rnd, n_etf, start, stamp)
    names = rnd.sample(UNIVERSE, rnd.choice([6, 12, 20, 30, 38]))
    for s in names:
        r = rnd.random()
        if r < 0.3:
            bars_by[s] = _bottom_tape(rnd, start, stamp)
        else:
            bars_by[s] = daily_bars(rnd, rnd.choice([30, 60, 120, 200, 300]), start_ms=start, stamp=stamp,
                                    regime=rnd.choice([None, None, "drop", "coil", "rip", "trend"]))
    now = max(b[-1]["t"] for b in bars_by.values() if b) + 20 * 3600_000
    bench = bars_by.get("SPY")
    rows = [PR.scan_prism_symbol(s, bars_by[s], bench) for s in sorted(bars_by)]
    rnd.shuffle(rows)
    funds = {s: _fund(rnd, s) for s in rnd.sample(names, min(len(names), rnd.randint(0, 4)))}
    lasts = [rnd.choice([None, None, rnd.uniform(5, 300)]) for _ in range(40)]
    return {"rows": rows, "barsBy": bars_by, "funds": funds, "now": now, "noBars": rnd.random() < 0.05,
            "lasts": lasts}


def port_distill(c):
    bars_by = c["barsBy"]
    d = B.distill_buys(c["rows"], None if c["noBars"] else bars_by, c["funds"], c["now"])
    kept = [s for s in d["buys"] if B.keep_after_curl(s, bars_by.get(s["symbol"]))["keep"]]
    book = B.filter_book_for_curl(B.order_book(kept), bars_by)
    stamped = [s if (i >= len(c["lasts"]) or c["lasts"][i] is None) else dict(s, afterHours={"last": c["lasts"][i]})
               for i, s in enumerate(book)]
    return {"d": d, "kept": kept, "book": book, "near": B.keep_near_buy(stamped),
            "tape": B.read_sector_tape(bars_by, c["now"])}


# -- session -----------------------------------------------------------------------------------------------------------
def _five_min(rnd, now, px):
    """5-minute bars (pre / regular / post) over the four calendar days up to `now`."""
    out = []
    t0 = (now // 300_000) * 300_000 - 4 * DAY_MS
    t = t0
    while t <= now - 300_000:
        p = B.T.et_parts(t)
        hm = p["hour"] * 60 + p["minute"]
        if 1 <= p["dow"] <= 5 and 4 * 60 <= hm < 20 * 60 and rnd.random() < 0.97:
            o = px
            c = max(0.05, o * (1 + rnd.gauss(0, 0.003)))
            out.append({"t": t, "o": round(o, 2), "h": round(max(o, c) * (1 + abs(rnd.gauss(0, 0.001))), 2),
                        "l": round(min(o, c) * (1 - abs(rnd.gauss(0, 0.001))), 2), "c": round(c, 2),
                        "v": float(rnd.randint(100, 50000))})
            px = c
        t += 300_000
    return out


def session_case(rnd, k):
    daily = daily_bars(rnd, rnd.choice([0, 10, 16, 30, 90, 200]), regime=rnd.choice([None, "drop", "coil"]))
    base = (daily[-1]["t"] if daily else 1_790_000_000_000) + DAY_MS
    now = base - (base % DAY_MS) + rnd.choice([11, 12, 13, 14, 15, 18, 20, 22, 23]) * 3600_000 + \
        rnd.randint(0, 59) * 60_000 + rnd.choice([0, DAY_MS, 2 * DAY_MS])
    px = daily[-1]["c"] if daily else rnd.uniform(5, 200)
    bars = _five_min(rnd, now, px * rnd.uniform(0.95, 1.05)) if rnd.random() < 0.9 else []
    buy = round(px * rnd.uniform(0.94, 1.02), 2)
    stop = round(buy * rnd.uniform(0.9, 1.01), 2)
    target = round(buy * rnd.uniform(0.98, 1.3), 2)
    setup = {"symbol": "S%d" % (k % 7), "plan": {"buy": buy, "stop": stop, "target": target, "rr": 2.0},
             "close": round(px, 2), "antiChase": rnd.choice([True, False]), "tier": "A", "size": "Half size"}
    if rnd.random() < 0.3:
        setup["afterHours"] = {"last": round(px * rnd.uniform(0.97, 1.03), 2), "note": rnd.choice(["", "x"])}
    return {"bars": bars or None, "now": now, "setup": setup, "daily": daily or None, "buy": buy,
            "risk": rnd.choice([0, round(buy * 0.03, 4), -1]), "last": rnd.choice([None, round(px, 2)])}


def port_session(c):
    tape = B.session_tape(c["bars"], c["now"])
    return {"tape": tape, "note": B.tape_note(tape, c["now"]),
            "applied": B.apply_session_tape(c["setup"], tape, c["now"], c["daily"]),
            "stop": B.live_stop(c["buy"], c["daily"]), "agg": B.aggressive_target(c["daily"], c["buy"], c["risk"]),
            "live": B.live_accurate_plan(c["setup"], c["last"], c["now"], c["daily"])}


# -- roster ------------------------------------------------------------------------------------------------------------
POOL = ["NVDA", "AMD", "AVGO", "MU", "TSM", "PLTR", "CRM", "TSLA", "RIVN", "XOM", "CVX", "LLY", "AAPL", "META", "GOOGL",
        "ASTS", "RKLB", "ADM", "DE", "SPY", "IONQ", "SOFI", "HOOD", "COIN", "SHOP", "NET", "DDOG", "SNOW", "U", "PATH"]


def _iso(ms):
    return B._iso(ms)


def roster_case(rnd, k):
    now = 1_790_000_000_000 + rnd.randint(0, 200) * DAY_MS + rnd.randint(0, 23) * 3600_000
    px = {s: rnd.uniform(5, 300) for s in POOL}
    start = {"dateEt": B.T.et_parts(now - DAY_MS)["ymd"], "members": [], "addedToday": [], "kept": [],
             "droppedToday": []}
    if rnd.random() < 0.3:
        for s in rnd.sample(POOL, rnd.randint(1, 8)):
            m = {"symbol": s, "buy": round(px[s], 2), "stop": round(px[s] * 0.95, 2), "target": round(px[s] * 1.15, 2),
                 "rr": 3.0, "status": rnd.choice(["LIVE", "LIVE", "DROPPED"])}
            if rnd.random() < 0.5:
                m["addedAt"] = _iso(now - rnd.randint(1, 9) * DAY_MS)
            if rnd.random() < 0.3:
                m["held"] = True
            if rnd.random() < 0.3:
                m["sessionMarks"] = [B.T.et_parts(now - j * DAY_MS)["ymd"] for j in range(rnd.randint(1, 5), 0, -1)]
            start["members"].append(m)
    steps = []
    for _ in range(rnd.randint(2, 8)):
        now += rnd.choice([10 * 60_000, 3600_000, DAY_MS, 3 * DAY_MS])
        for s in POOL:
            px[s] *= 1 + rnd.gauss(0, 0.03)
        x = rnd.random()
        if x < 0.75:
            book = []
            for s in rnd.sample(POOL, rnd.choice([0, 2, 5, 8, 26])):
                b = round(px[s] * rnd.uniform(0.97, 1.0), 2)
                book.append({"symbol": s, "buy": b, "stop": round(b * rnd.uniform(0.93, 0.98), 2),
                             "target": round(b * rnd.uniform(1.05, 1.3), 2), "rr": round(rnd.uniform(1, 5), 1),
                             "close": round(px[s], 2), "call": rnd.choice(["BUY", "HALF", "PAPER"]),
                             "scanner": rnd.choice(["Vector", "Zenith", ""]), "held": rnd.random() < 0.1})
            quotes = {s: round(px[s], 2) for s in rnd.sample(POOL, rnd.randint(0, len(POOL)))}
            steps.append({"kind": "curate", "book": book, "quotes": quotes, "dateEt": B.T.et_parts(now)["ymd"],
                          "now": now})
        else:
            steps.append({"kind": "buy" if x < 0.9 else "sell", "symbol": rnd.choice(POOL), "at": _iso(now),
                          "now": now})
    return {"start": start, "steps": steps}


def port_roster(c):
    st = c["start"]
    out = []
    for s in c["steps"]:
        if s["kind"] == "curate":
            st = B.curate_roster(st, s["book"], s["quotes"], s["dateEt"], s["now"])
        elif s["kind"] == "buy":
            st = B.stamp_tensor_buy(st, s["symbol"], s["at"], s["now"])
        else:
            st = B.stamp_tensor_sell(st, s["symbol"], s["at"], s["now"])
        out.append(st)
    return out


# -- runner ------------------------------------------------------------------------------------------------------------
def _run_part(tree, driver, cases, port, diffs, label):
    ident = 0
    for i in range(0, len(cases), BATCH):
        chunk = cases[i:i + BATCH]
        theirs = node_run(tree, driver, {"cases": chunk}, name="__driver.cjs")
        for j, (c, t) in enumerate(zip(chunk, theirs)):
            d = same(_clean(port(c)), t)
            if d:
                diffs.append({"part": label, "case": i + j, "diff": [list(map(str, x)) for x in d[:5]]})
            else:
                ident += 1
    return ident


PARTS = [("prism", prism_case, port_prism, DRIVER_PRISM, "N_PRISM"),
         ("select", select_case, port_select, DRIVER_SELECT, "N_SELECT"),
         ("bottom", bottom_case, port_bottom, DRIVER_BOTTOM, "N_BOTTOM"),
         ("distill", distill_case, port_distill, DRIVER_DISTILL, "N_DISTILL"),
         ("session", session_case, port_session, DRIVER_SESSION, "N_SESSION"),
         ("roster", roster_case, port_roster, DRIVER_ROSTER, "N_ROSTER")]


def _stats(label, cases, stats):
    if label == "prism":
        for c in cases:
            r = port_prism(c)
            for e in r["episodes"]:
                key = "%s:%s" % (e["grade"], e["phase"])
                stats.setdefault("prism_grades", {}).setdefault(key, 0)
                stats["prism_grades"][key] += 1
    elif label == "select":
        for c in cases:
            v = B.read_select(c["bars"], c["last"], c["now"])["verdict"]
            stats.setdefault("select_verdicts", {}).setdefault(v, 0)
            stats["select_verdicts"][v] += 1
    elif label == "bottom":
        for c in cases:
            t = port_bottom(c)["named"]["tag"]
            stats.setdefault("bottom_named_tags", {}).setdefault(t, 0)
            stats["bottom_named_tags"][t] += 1
    elif label == "distill":
        for c in cases:
            p = port_distill(c)
            stats["distill_buys"] = stats.get("distill_buys", 0) + len(p["d"]["buys"])
            stats["distill_bottom_buys"] = stats.get("distill_bottom_buys", 0) + \
                len([s for s in p["d"]["buys"] if s["primaryScanner"] == "Bottom"])
            stats["book_after_curl"] = stats.get("book_after_curl", 0) + len(p["book"])
            for r in p["d"]["rejected"]:
                stats.setdefault("distill_rejected", {}).setdefault(r["status"], 0)
                stats["distill_rejected"][r["status"]] += 1
    elif label == "session":
        for c in cases:
            a = port_session(c)["applied"]
            key = "kept" if a["keep"] else "dropped"
            stats.setdefault("session_applied", {}).setdefault(key, 0)
            stats["session_applied"][key] += 1
    elif label == "roster":
        for c in cases:
            for st in port_roster(c):
                for d in st["droppedToday"]:
                    stats.setdefault("roster_drops", {}).setdefault(d["reason"], 0)
                    stats["roster_drops"][d["reason"]] += 1


def run():
    rnd = random.Random(20261017)
    built = []
    for label, make, port, driver, nkey in PARTS:
        built.append((label, [make(rnd, k) for k in range(globals()[nkey])], port, driver))
    diffs, stats, counts = [], {}, {}
    tree = None
    try:
        tree = stage("Author_DESK", "/home/user/Author-desk", dict(BOOK_TS, **BOOK_DATA, **EXTRA_TS, **SCRIPTS))
        transpile_ts(tree, list(BOOK_TS) + list(EXTRA_TS))
        for label, cases, port, driver in built:
            counts[label] = (len(cases), _run_part(tree, driver, cases, port, diffs, label))
    finally:
        if tree:
            cleanup(tree)
    for label, cases, port, driver in built:
        _stats(label, cases, stats)
    n = sum(v[0] for v in counts.values())
    res = {"sleeve": "Author_book", "cases": n, "identical": sum(v[1] for v in counts.values()), "diffs": diffs[:40],
           "n_diffs": len(diffs),
           "stats": dict(stats, **{f"{k}_cases": v[0] for k, v in counts.items()},
                         **{f"{k}_identical": v[1] for k, v in counts.items()}),
           "source": {"repo": "Author-desk", "commit": COMMIT,
                      "files": dict(BOOK_TS, **BOOK_DATA, **EXTRA_TS, **SCRIPTS)},
           "method": "source TypeScript (and desk-autopilot.mjs's book functions, read verbatim) under Node 22 vs "
                     "desk/sleeves/Author/{prism,book}.py, exact JSON equality (Date set to each case's clock)",
           "sleeves": ["Author_scanner_book_swing", "Author_sector_first_bottom"]}
    write_receipt("Author_book", res)
    return res
