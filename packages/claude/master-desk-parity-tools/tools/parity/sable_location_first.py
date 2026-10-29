"""sable_location_first: the Location-first Repair v2.1.0 screen and its desk scan (autopilot-desk @48e8f90f, the
SOURCE .mjs modules run unmodified under Node 22) vs the port (desk/sleeves/sable/location_first.py) on the same
inputs.

Each case: a daily OHLCV series (50-280 bars) drawn from six regimes — random walk, trend-then-wash-then-base, drift-
wash-quiet-repair (the setup the screen looks for), steady trend, flat tape, crash — in the sources' field spellings (time/open/... or
t/o/...), sometimes close-only (high = low = close), without volume, with a missing open, duplicated or shuffled
rows; a live session price or none; event / structural / liquidity context flags; external supports.

Compared, exactly (doubles bit for bit; JSON null = JavaScript undefined):
  evaluate()          the whole result: status, setup, priority, score, reason codes, public reason, metrics, plan
  deskActionOf()      action / tier / reason / floor for a random kind and ETF-only mandate
  evaluateLeaders()   the funnel's leaders read (status, action, score, reason, metrics) with random SPY momentum,
                      event and regime flags
  buildLocationFirstScan()  per batch of 25 results with random quotes (kinds, bar stamps, prices) and mandates
                      (maxPositions 2 / 4 / 6 / 7 / 13 / none, radarCap): candidates, pressure, hands, caps, counts
  hydrateQuotesFromLocationFirst()  price, atr, ema21, ema50, support, locationFirstAt, kind (the fields the paper
                      pass reads)

    AUTOPILOT_DESK=<autopilot-desk @48e8f90f> python3 -m tools.parity.run sable_location_first"""
import random

from desk.sleeves.sable import location_first as lf
from desk.sleeves.families.sable import ETF_TICKERS, TICKERS, ms

from . import write_receipt
from .node_pinned import cleanup, run as node_run, same, stage

COMMIT = "48e8f90f5d9def28363eb4013dac4dd8d78f74bf"
FILES = {
    "src/lib/scanner/location-first-repair.mjs": "5377c97f7c0d48b1045fdc9f754b9b3555ae638c",
    "src/lib/scanner/location-first-desk.mjs": "0b1c5417322c2ddc51f369d2b2b54473dec9efee",
    "src/lib/scanner/leaders-rest-core.mjs": "5df6186e61ce2a79a0a21850144d1f3e24336637",
    "src/lib/scanner/desk-core.mjs": "1b5f90418acae9d53d3bf25caa251f86843351b2",
    "src/lib/scanner/features.mjs": "843833d1f8fab0669912c6bf1cd3860a771f735e",
    "src/lib/desk/catalog.mjs": "39da6b5c7f5296544b54fd0e94de34fbbdc36ffd",
}
N_CASES = 6000
BATCH = 25

DRIVER = r"""
import { readFileSync } from "node:fs";
import { evaluate, deskActionOf } from "./src/lib/scanner/location-first-repair.mjs";
import { evaluateLeaders } from "./src/lib/scanner/leaders-rest-core.mjs";
import { buildLocationFirstScan, hydrateQuotesFromLocationFirst } from "./src/lib/scanner/location-first-desk.mjs";
const P = JSON.parse(readFileSync(0, "utf8"));
const cases = P.cases.map((c) => {
  const r = evaluate(c.input);
  return { r, a: deskActionOf(r, c.action), l: evaluateLeaders(c.leaders) };
});
const scans = P.batches.map((b) => {
  const results = b.idx.map((i) => cases[i].r);
  const scan = buildLocationFirstScan({ results, quotes: b.quotes, mandate: b.mandate, now: 0, completedBarAt: null });
  delete scan.generatedAt;
  const q = JSON.parse(JSON.stringify(b.quotes));
  hydrateQuotesFromLocationFirst(q, results, b.closesBy);
  const h = {};
  for (const [t, v] of Object.entries(q)) h[t] = { price: v.price, atr: v.atr, ema21: v.ema21, ema50: v.ema50,
    support: v.support, locationFirstAt: v.locationFirstAt, kind: v.kind };
  return { scan, h };
});
console.log(JSON.stringify({ cases, scans }));
"""


def _series(rnd, n, style):
    px = rnd.choice([rnd.uniform(1.5, 5), rnd.uniform(5, 60), rnd.uniform(60, 600)])
    out = []
    if style == "wash":
        up = max(20, n - rnd.randint(15, 45))
        wash = rnd.randint(5, 25)
        for i in range(n):
            if i < up:
                mu, vol = rnd.uniform(-0.002, 0.004), 0.015
            elif i < up + wash:
                mu, vol = -rnd.uniform(0.004, 0.02), 0.02
            else:
                mu, vol = rnd.uniform(-0.002, 0.006), 0.012
            out.append((mu, vol))
    elif style == "repair":                       # drift, a wash under the 50-day, a quiet base lifting off it
        b = rnd.randint(8, 25)
        c = rnd.randint(3, 12)
        a = max(10, n - b - c)
        out = [(rnd.uniform(-0.0005, 0.002), rnd.uniform(0.008, 0.016))] * a + \
              [(-rnd.uniform(0.005, 0.013), rnd.uniform(0.008, 0.02))] * b + \
              [(rnd.uniform(0.001, 0.008), rnd.uniform(0.004, 0.012))] * c
        out = out[:n]
    elif style == "trend":
        mu = rnd.uniform(-0.004, 0.004)
        out = [(mu, rnd.uniform(0.008, 0.03))] * n
    elif style == "flat":
        out = [(0.0, rnd.uniform(0.002, 0.01))] * n
    elif style == "crash":
        k = rnd.randint(int(n * 0.6), n - 1)
        out = [(0.001, 0.015)] * k + [(-0.04, 0.04)] * (n - k)
    else:
        out = [(rnd.uniform(-0.001, 0.001), rnd.uniform(0.01, 0.04))] * n
    bars, t = [], 1.70e9 + rnd.randint(0, 400) * 86400
    for mu, vol in out:
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.05, px * (1 + rnd.gauss(mu, vol)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = float(int(rnd.uniform(2e5, 2e7)))
        bars.append({"t": t, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4), "v": v})
        px = c
        t += 86400
    return bars


def make_case(i):
    rnd = random.Random(f"sable-lf-{i}")
    n = rnd.choice([rnd.randint(50, 75), rnd.randint(70, 140), rnd.randint(140, 280)])
    style = rnd.choice(["walk", "wash", "wash", "repair", "repair", "repair", "repair", "trend", "flat", "crash"])
    raw = _series(rnd, n, style)
    close_only = rnd.random() < 0.10
    no_vol = rnd.random() < 0.06
    long_names = rnd.random() < 0.5
    bars = []
    for b in raw:
        if close_only:
            b = dict(b, o=b["c"], h=b["c"], l=b["c"])
        if no_vol:
            b = dict(b, v=0)
        row = {"time": b["t"], "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"], "volume": b["v"]} \
            if long_names else dict(b)
        if rnd.random() < 0.02:
            row.pop("open" if long_names else "o", None)
        bars.append(row)
    if rnd.random() < 0.03 and len(bars) > 3:
        bars.insert(rnd.randint(1, len(bars) - 1), dict(bars[rnd.randint(0, len(bars) - 1)]))
    if rnd.random() < 0.03:
        rnd.shuffle(bars)
    last = raw[-1]["c"]
    inp = {"symbol": rnd.choice(TICKERS).lower() if rnd.random() < 0.3 else rnd.choice(TICKERS), "bars": bars}
    if rnd.random() < 0.6:
        inp["regularSessionPrice"] = round(last * (1 + rnd.gauss(0, 0.015)), 4)
    ctx = {}
    if rnd.random() < 0.05:
        ctx["eventBlocked"] = True
    if rnd.random() < 0.03:
        ctx["structuralBreakdown"] = True
    if rnd.random() < 0.03:
        ctx["liquidityOk"] = rnd.choice([True, False])
    if ctx or rnd.random() < 0.5:
        inp["marketContext"] = ctx
    if rnd.random() < 0.05:
        inp["externalSupports"] = [{"price": round(last * rnd.uniform(0.95, 1.0), 4), "weight": rnd.choice([0, 2, 5])}
                                   for _ in range(rnd.randint(1, 2))]
    norm = lf.normalize_bars(bars)
    lead = {"symbol": inp["symbol"], "bars": norm}
    if rnd.random() < 0.5:
        lead["regularSessionPrice"] = inp.get("regularSessionPrice", last)
    if rnd.random() < 0.5:
        lead["spyMomentum"] = round(rnd.uniform(-0.2, 0.4), 4)
    if rnd.random() < 0.05:
        lead["eventBlocked"] = True
    if rnd.random() < 0.05:
        lead["regimeDead"] = True
    action = {"kind": rnd.choice(["stock", "etf", "ETF"]), "etfOnly": rnd.random() < 0.2}
    return {"input": inp, "action": action, "leaders": lead, "style": style}


def make_batch(rnd, idx, cases, results):
    quotes, closes_by = {}, {}
    for i in idx:
        t = str(results[i]["symbol"])
        if not t or rnd.random() < 0.15:
            continue
        q = {"ticker": t}
        if rnd.random() < 0.7:
            q["kind"] = rnd.choice(["stock", "etf"])
        if rnd.random() < 0.6:
            q["locationFirstAt"] = 1.7e12 + rnd.randint(0, 10**6)
        if rnd.random() < 0.3:
            q["completedBarAt"] = 1.7e12 + rnd.randint(0, 10**6)
        if rnd.random() < 0.7:
            q["price"] = round(rnd.uniform(1, 300), 2)
        if rnd.random() < 0.3:
            q["atr"] = round(rnd.uniform(0.1, 5), 3)
        quotes[t] = q
        if rnd.random() < 0.5:
            bars = lf.normalize_bars(cases[i]["input"]["bars"])
            closes_by[t] = {"price": round(rnd.uniform(1, 300), 2), "times": [b["time"] for b in bars][-5:],
                            "closes": [b["close"] for b in bars][-5:]}
    mandate = {}
    mp = rnd.choice([2, 4, 6, 7, 13, None, "6"])
    if mp is not None:
        mandate["maxPositions"] = mp
    if rnd.random() < 0.3:
        mandate["radarCap"] = rnd.choice([5, 20, 36, 60])
    if rnd.random() < 0.1:
        mandate["assetClass"] = "etfs"
    return {"idx": idx, "quotes": quotes, "mandate": mandate, "closesBy": closes_by}


def port_hydrate(quotes, results, closes_by):
    out = {t: dict(q) for t, q in quotes.items()}
    for res in results:
        t = str(res.get("symbol") or "").upper()
        if not t:
            continue
        series = closes_by.get(t)
        ex = out.get(t) or {}
        h = lf.hydrate_quote(ex, res, series)
        at = ms(ex.get("locationFirstAt"))
        if at is None:
            times = (series or {}).get("times") or []
            at = ms(times[-1]) if times else None
        h["locationFirstAt"] = at
        h["kind"] = "etf" if lf.is_etf_ticker(t, ex.get("kind"), ETF_TICKERS) else "stock"
        out[t] = h
    return {t: {k: v.get(k) for k in ("price", "atr", "ema21", "ema50", "support", "locationFirstAt", "kind")}
            for t, v in out.items()}


def run():
    cases = [make_case(i) for i in range(N_CASES)]
    ours = []
    for c in cases:
        r = lf.evaluate(c["input"])
        ours.append({"r": r, "a": lf.desk_action_of(r, c["action"]["kind"], c["action"]["etfOnly"]),
                     "l": lf.evaluate_leaders(c["leaders"])})
    rnd = random.Random("sable-lf-batches")
    batches = [make_batch(rnd, list(range(k, min(k + BATCH, N_CASES))), cases, [o["r"] for o in ours])
               for k in range(0, N_CASES, BATCH)]
    tree = stage("AUTOPILOT_DESK", "/home/user/autopilot-desk", FILES)
    try:
        theirs = node_run(tree, DRIVER, {"cases": [{k: c[k] for k in ("input", "action", "leaders")} for c in cases],
                                         "batches": batches})
    finally:
        cleanup(tree)
    diffs, identical = [], 0
    stats = {"status": {}, "setup": {}, "leaders": {}, "styles": {}}
    for i, (c, o, t) in enumerate(zip(cases, ours, theirs["cases"])):
        d = same(o, t)
        if d:
            diffs.append({"case": i, "diff": d[:5]})
        else:
            identical += 1
        stats["status"][o["r"]["status"]] = stats["status"].get(o["r"]["status"], 0) + 1
        k = str(o["r"]["setup"])
        stats["setup"][k] = stats["setup"].get(k, 0) + 1
        stats["leaders"][o["l"]["status"]] = stats["leaders"].get(o["l"]["status"], 0) + 1
        stats["styles"][c["style"]] = stats["styles"].get(c["style"], 0) + 1
    scan_identical, hands = 0, 0
    for j, (b, t) in enumerate(zip(batches, theirs["scans"])):
        results = [ours[i]["r"] for i in b["idx"]]
        scan = lf.build_location_first_scan(results, b["quotes"], b["mandate"], ETF_TICKERS, completed_bar_at=None)
        mine = {"scan": scan, "h": port_hydrate(b["quotes"], results, b["closesBy"])}
        d = same(mine, t)
        if d:
            diffs.append({"batch": j, "diff": d[:5]})
        else:
            scan_identical += 1
        hands += len(scan["hands"])
    stats["scan_batches"] = len(batches)
    stats["scan_identical"] = scan_identical
    stats["hands_total"] = hands
    res = {"sleeve": "sable_location_first", "cases": N_CASES + len(batches), "identical": identical + scan_identical,
           "diffs": diffs[:50], "n_diffs": len(diffs), "stats": stats,
           "method": "the source .mjs modules (location-first-repair / location-first-desk / leaders-rest-core / "
                     "desk-core, autopilot-desk @48e8f90f, blob-verified) under Node 22 vs the Python port, same inputs",
           "source": {"repo": "autopilot-desk", "commit": COMMIT, "files": FILES},
           "sleeves": ["sable_location_first_repair_v210"]}
    write_receipt("sable_location_first", res)
    return res
