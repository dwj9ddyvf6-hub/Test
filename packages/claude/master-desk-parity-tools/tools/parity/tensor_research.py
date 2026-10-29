"""tensor_research: every ported decision function vs its source, on deterministic randomized cases.

  features   agentic-trading-desk @4c8c179c, run unmodified in a scratch copy of its tree (TENSOR_SRC; the one module
             that hashes a canonical manifest at import, tensor_market_scan, is loaded with that constant stubbed):
             tensor_htf_event_ledger.feature_tape (full and only_latest), tensor_htf_advanced_features.technical_tape,
             tensor_htf_conditional_discovery.labels, tensor_htf_weekly_color_discovery.atoms,
             tensor_htf_weekly_cyan_study.context + HYPOTHESES, tensor_htf_weekly_cyan_discovery.purge (vs the
             PurgedBook's admission), tensor_market_scan.tail_features + evaluate_specs on the frozen v4 registry,
             tensor_higher_timeframe.admit_completed, tensor_counterfactual_policy_lab.atr,
             tensor_experimental_strategy.decision_from_prediction (+ the evaluate loop's authorized-unqualified
             replace) vs desk/feedlib/tensor_features.py and the family's ExperimentBook path.
  sable      autopilot-desk @48e8f90f (AUTOPILOT_SRC): quote-core.mjs quoteFromCompletedBars, ledger-core.mjs
             swingSizeShares and canEnterUnderMandate (defaultMandate), unattended-core.mjs applyStopsAndTargets vs the
             family's sable_quote / swing_size_shares / can_enter / swing_bracket_check.
  calendar   the research studies' bar arithmetic (entry = open of bar i+1, exit = close of bar i+h on the bar
             sequence: sessions, ISO weeks, canonical RTH hours) vs desk/feedlib/tensor_research.py entry_open /
             exit_close.
  asof       the runner on a series cut at bar j (what the forward job sees) vs bar j of the full-series replay (what
             the research studies scored): primary markers, enrichment ids, sidecar genomes / phenotypes, the v615
             Swing (confirmed, event key) on 1d / 1wk / 1h.

    TENSOR_SRC=/scratch/agentic_src AUTOPILOT_SRC=/home/user/autopilot-desk python3 -m tools.parity.tensor_research [n]"""
import hashlib
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from desk import calendar as cal
from desk.feedlib import tensor_features as tf
from desk.feedlib import tensor_research as P
from desk.sleeves.families import tensor_research as F

from . import write_receipt
from .griffith import run_source

N_CASES = 1000
REGISTRY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desk",
                        "vendor", "griffith", "tensor_phenotype_registry.json")

# -- the case generator (exec'd identically in this process and in the source process) -------------------------------
GEN = r'''
import random as _r
from datetime import datetime as _dt, timedelta as _td, timezone as _tz
VOCAB = ["buy-green", "buy-cyan", "sell-red", "sell-magenta", "dcb-buy", "consensus-buy", "consensus-sell",
         "participation-footprint", "extension-warning", "state-p", "buy-gold", "warning-amber"]
ENRICH = ["participation-footprint", "extension-warning", "state-p", "squeeze-release", "trend-repair"]
def walk(rnd, n, px):
    out, left, drift, vol = [], 0, 0.0, rnd.uniform(0.01, 0.05)
    for _ in range(n):
        if left <= 0:
            left = rnd.randint(5, 40); drift = rnd.choice([0.012, 0.006, 0.002, 0.0, -0.003, -0.008])
            vol = max(0.005, min(0.12, vol * rnd.uniform(0.6, 1.6)))
        left -= 1
        r = rnd.gauss(drift, vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.05, 0.2) if rnd.random() < 0.03 else 0.0)
        o = px * (1 + rnd.gauss(0, vol / 3)); c = max(0.5, px * (1 + r))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2))); l = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = 0.0 if rnd.random() < 0.01 else float(int(rnd.uniform(1e5, 6e6)))
        out.append((round(o, 4), round(h, 4), round(l, 4), round(c, 4), v)); px = c
    return out
def stamps(frame, n, end):
    out, d = [], end
    while len(out) < n:
        if frame == "1d" and d.weekday() < 5:
            out.append(d)
        elif frame == "1wk" and d.weekday() == 0:
            out.append(d)
        d -= _td(days=1)
    return [int(_dt(x.year, x.month, x.day, 13, 30, tzinfo=_tz.utc).timestamp()) for x in out[::-1]]
def build_case(seed):
    rnd = _r.Random(seed)
    frame = rnd.choice(["1d", "1d", "1wk"])
    n = rnd.randint(205, 460)
    end = _dt(2026, 1, 2) + _td(days=rnd.randint(0, 280))
    times = stamps(frame, n, end.date())
    bars = [{"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}
            for t, (o, h, l, c, v) in zip(times, walk(rnd, n, rnd.uniform(5, 400)))]
    spy = [{"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}
           for t, (o, h, l, c, v) in zip(times, walk(rnd, n, rnd.uniform(300, 600)))]
    if rnd.random() < 0.1:
        spy = spy[: rnd.randint(150, n)]
    def marks(p):
        return sorted({m for m in VOCAB[:7] if rnd.random() < p})
    tail = []
    for k in range(min(64, n)):
        row = {"time": times[n - min(64, n) + k], "primaryMarkers": marks(0.08),
               "dcbMarker": "buy" if rnd.random() < 0.05 else None,
               "warningMarker": "amber" if rnd.random() < 0.05 else None,
               "enrichment": {"signals": [{"id": e} for e in ENRICH if rnd.random() < 0.1]},
               "rvol": round(rnd.uniform(0.3, 3.0), 3), "fastState": rnd.choice(["bullish", "bearish", "neutral"]),
               "slowState": rnd.choice(["bullish", "bearish", "neutral"]),
               "candleRegime": rnd.choice(["bullish", "bearish", "neutral"]),
               "bullishVotes": rnd.randint(0, 9), "bearishVotes": rnd.randint(0, 9),
               "tensorContext": {"cycle": {"state": rnd.choice(["BULL_STRONG", "BULL_WEAK", "BEAR_WEAK", None]),
                                           "momentum": rnd.choice(["aligned", "diverging", None])}}}
        tail.append(row)
    if rnd.random() < 0.3:                                   # fresh primary markers on the newest bar
        tail[-1]["primaryMarkers"] = sorted(set(tail[-1]["primaryMarkers"]) | {rnd.choice(["buy-green", "buy-cyan"])})
    active = set(rnd.sample(VOCAB, rnd.randint(0, 6)))
    fresh = {s for s in sorted(active) if rnd.random() < 0.6} | (
        {rnd.choice(["buy-green", "buy-cyan", "sell-red", "dcb-buy"])} if rnd.random() < 0.7 else set())
    active |= fresh
    ages = {s: rnd.randint(0, 40) for s in VOCAB if rnd.random() < 0.4}
    extra = {"bullishVotes": rnd.randint(0, 9), "bearishVotes": rnd.randint(0, 9),
             "fastState": rnd.choice(["bullish", "bearish"]), "slowState": rnd.choice(["bullish", "bearish"]),
             "activeCall": rnd.choice(["bullish", "bearish", None]), "callLifecycle": rnd.choice(["reversed", "new", None]),
             "candleRegime": rnd.choice(["bullish", "bearish"]), "rvol": round(rnd.uniform(0.3, 3.0), 3),
             "tensorContext": {"cycle": {"state": rnd.choice(["BULL_STRONG", "BULL_WEAK", "BEAR_WEAK"]),
                                         "momentum": rnd.choice(["aligned", "diverging"]),
                                         "momentumAgreement": rnd.random() < 0.5, "ageBars": rnd.randint(0, 30),
                                         "slowK": round(rnd.uniform(0, 100), 2)}},
             "signalAges": ages, "freshSignals": sorted(fresh)}
    k = rnd.randint(1, 6)
    cutoff = times[-k] if rnd.random() < 0.9 else times[-1] + 3600
    pred = {"prediction_id": "tfpred:%08x" % rnd.getrandbits(32), "observation_hash": "%016x" % rnd.getrandbits(64),
            "specification_id": rnd.choice(["spec-a", "spec-b"]), "symbol": "SYM%d" % seed, "timeframe": frame,
            "event_cutoff": cutoff}
    state = rnd.choice(["QUALIFIED", "AUTHORIZED_PAPER_EXPERIMENT", "AUTHORIZED_PAPER_EXPERIMENT", "NOT_EVALUATED"])
    raw = [{"t": _dt.fromtimestamp(b["time"], _tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": b["open"], "h": b["high"],
            "l": b["low"], "c": b["close"], "v": b["volume"]} for b in bars]
    if rnd.random() < 0.2:
        raw[rnd.randrange(len(raw))]["h"] = -1.0             # malformed
    if rnd.random() < 0.2:
        raw.append(dict(raw[-1]))                            # duplicate
    clock = _dt.fromtimestamp(times[-1], _tz.utc) + _td(hours=rnd.choice([1, 3, 6, 30, 200]))
    syms = ["AAA", "BBB", "CCC"]
    purge = sorted({(rnd.choice(syms), (_dt(2024, 1, 1) + _td(days=rnd.randint(0, 700))).date().isoformat())
                    for _ in range(rnd.randint(5, 40))}, key=lambda x: (x[1], x[0]))
    idx = sorted(rnd.sample(range(1, n), min(8, n - 1)))
    return {"seed": seed, "frame": frame, "bars": bars, "spy": spy, "tail": tail, "active": sorted(active),
            "fresh": sorted(fresh), "extra": extra, "pred": pred, "state": state, "raw": raw,
            "clock": clock.isoformat(), "purge": purge, "atr_idx": idx}
'''

# -- the evaluation (exec'd in both processes over a library L with the same function names) --------------------------
EVAL = r'''
import hashlib as _h, json as _j
from datetime import datetime as _dt2, timezone as _tz2
def _canon(v):
    if isinstance(v, (set, frozenset)):
        return sorted(_canon(x) for x in v)
    if isinstance(v, dict):
        return {str(k): _canon(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    if isinstance(v, float) and v != v:
        return "NaN"
    return v
def _dig(v):
    return _h.sha256(_j.dumps(_canon(v), sort_keys=True, default=repr).encode()).hexdigest()
def evaluate(L, c, detail=False):
    out, info = {}, {}
    bars, spy, frame = c["bars"], c["spy"], c["frame"]
    active, fresh = set(c["active"]), set(c["fresh"])
    full = L.feature_tape(bars)
    out["feature_tape"] = full
    latest = L.feature_tape(bars, only_latest=True)[-1]
    out["feature_latest"] = latest
    spy_by_date = {_dt2.fromtimestamp(int(b["time"]), _tz2.utc).date().isoformat(): float(b["close"]) for b in spy}
    tech = L.technical_tape(bars, spy_by_date)
    out["technical_tape"] = tech
    tlatest = L.technical_tape(bars, spy_by_date, only_latest=True)[-1]
    out["technical_latest"] = tlatest
    features = dict(latest, **c["extra"])
    lab = L.labels(active, fresh, features)
    out["labels"] = lab
    adv = dict(features, **tlatest)
    adv["spyRegime"] = L.feature_tape(spy)[-1]["regime"] if spy else None
    at = L.atoms(adv, active, {})
    out["atoms"] = at
    ctx = L.cyan_context(features, active)
    out["cyan"] = [ctx, sorted(h for h, fn in L.hypotheses() if fn(ctx))]
    tensor = {"researchTail": c["tail"]}
    tail = L.tail_features(bars, tensor, spy, frame)
    out["tail"] = tail
    context = {"symbol": "X", "frames": {frame: {"barCutoff": int(bars[-1]["time"]), "featureVersion": L.FEATURE_VERSION,
                                                 "features": tail}}}
    specs = L.specs()
    out["specs"] = L.evaluate_specs(context, specs)
    # the frozen registry on contexts built to satisfy (or narrowly miss) each spec's rules
    import random as _rr
    rnd = _rr.Random(c["seed"] * 7 + 1)
    synth = []
    for spec in specs:
        ctx = {}
        rules = list(spec.get("required") or []) + list(spec.get("optional") or [])
        miss = rnd.randrange(len(rules)) if rules and rnd.random() < 0.4 else None
        for k, rule in enumerate(rules):
            if rule in (spec.get("optional") or []) and rnd.random() < 0.5:
                continue
            op, val = rule["op"], rule.get("value")
            if op == "eq":
                v = val if k != miss else ("other" if isinstance(val, str) else None)
            elif op in ("gt", "gte"):
                v = (float(val) + rnd.choice([0.0, 0.5, 10.0]) + (1e-9 if op == "gt" else 0.0)) if k != miss else float(val) - 1
            elif op in ("lt", "lte"):
                v = (float(val) - rnd.choice([0.0, 0.5, 10.0]) - (1e-9 if op == "lt" else 0.0)) if k != miss else float(val) + 1
            elif op == "contains":
                v = [val, "buy-green"] if k != miss else ["sell-red"]
            elif op == "in":
                v = val[0] if (k != miss and val) else "zz"
            else:
                v = val
            cur = ctx
            parts = str(rule["path"]).split(".")
            for part in parts[:-1]:
                cur = cur.setdefault(part, {})
            cur[parts[-1]] = v
        synth.append(L.evaluate_specs(ctx, specs))
    out["specs_synthetic"] = synth
    clock = _dt2.fromisoformat(c["clock"])
    try:
        completed, meta = L.admit_completed(c["raw"], frame, clock)
        out["admit"] = [completed, meta]
    except Exception as e:
        completed = None
        out["admit"] = ["ERROR", type(e).__name__]
    rows = [{"high": b["high"], "low": b["low"], "close": b["close"]} for b in bars]
    out["atr"] = [L.atr(rows, i) for i in c["atr_idx"]]
    try:                                                     # the decision admits the raw bars itself (wall clock)
        dec = L.decision(c["pred"], c["raw"], c["state"])
    except Exception as e:
        dec = "ERROR:" + type(e).__name__
    out["decision"] = dec
    out["purge"] = L.purge([tuple(x) for x in c["purge"]])
    info = {"labels": len(lab), "atoms": len(at), "hyp": len(out["cyan"][1]), "specs": len(out["specs"]),
            "admitted": isinstance(out["admit"][0], list), "decision": isinstance(dec, dict),
            "purge_kept": len(out["purge"]), "purge_items": len(c["purge"]),
            "g1": tail["dailyGreenG1"]["state"], "phenotype": tail["phenotype"]["state"],
            "spec_matches_synthetic": sum(len(x) for x in synth)}
    if detail:
        return {k: _canon(v) for k, v in out.items()}, info
    return {k: _dig(v) for k, v in out.items()}, info
'''

SRC_LIB = r'''
import sys, types, os, json, dataclasses
sys.dont_write_bytecode = True
import tensor_htf_event_ledger as EL, tensor_htf_advanced_features as AF, tensor_htf_conditional_discovery as CD
import tensor_htf_weekly_color_discovery as WC, tensor_htf_weekly_cyan_study as CS, tensor_htf_weekly_cyan_discovery as CDISC
import tensor_higher_timeframe as HT, tensor_counterfactual_policy_lab as PL, tensor_experimental_strategy as XS
src = open("tensor_market_scan.py").read().replace(
    "CANONICAL_TENSOR_SOURCE_HASH = canonical_tensor_source_hash()", "CANONICAL_TENSOR_SOURCE_HASH = 'parity-stub'")
MS = types.ModuleType("tensor_market_scan"); MS.__file__ = os.path.abspath("tensor_market_scan.py")
sys.modules["tensor_market_scan"] = MS
exec(compile(src, MS.__file__, "exec"), MS.__dict__)
REG = PAYLOAD["registry"]
class L:
    FEATURE_VERSION = MS.FEATURE_VERSION
    feature_tape = staticmethod(EL.feature_tape)
    technical_tape = staticmethod(AF.technical_tape)
    labels = staticmethod(CD.labels)
    atoms = staticmethod(WC.atoms)
    cyan_context = staticmethod(CS.context)
    @staticmethod
    def hypotheses():
        return [(h.id, h.predicate) for h in CS.HYPOTHESES]
    tail_features = staticmethod(MS.tail_features)
    evaluate_specs = staticmethod(MS.evaluate_specs)
    @staticmethod
    def specs():
        return [s for s in REG["phenotypes"] if s.get("enabled")]
    @staticmethod
    def admit_completed(raw, frame, now):
        return HT.admit_completed(raw, frame, now)
    atr = staticmethod(PL.atr)
    @staticmethod
    def decision(row, raw, state):
        item = XS.decision_from_prediction(row, raw, state)
        if item is not None and state != "QUALIFIED":            # evaluate()'s authorized-unqualified replace
            item = dataclasses.replace(item, metrics={**item.metrics, "paperExperimentAuthorized": True},
                                       reasonCodes=("AUTHORIZED_UNQUALIFIED_PAPER", *item.reasonCodes))
        return dataclasses.asdict(item) if item is not None else None
    @staticmethod
    def purge(items):
        return [list(x[:2]) for x in CDISC.purge([(s, d, 0.0, None) for s, d in items])]
'''


class PortLib:
    FEATURE_VERSION = tf.FEATURE_VERSION
    feature_tape = staticmethod(tf.feature_tape)
    technical_tape = staticmethod(tf.technical_tape)
    labels = staticmethod(tf.labels)
    atoms = staticmethod(tf.atoms)
    cyan_context = staticmethod(tf.cyan_context)
    tail_features = staticmethod(tf.tail_features)
    evaluate_specs = staticmethod(tf.evaluate_specs)
    admit_completed = staticmethod(tf.admit_completed)
    atr = staticmethod(tf.atr)
    _specs = None

    @staticmethod
    def hypotheses():
        return list(tf.CYAN_HYPOTHESES)

    @classmethod
    def specs(cls):
        if cls._specs is None:
            cls._specs = [s for s in json.load(open(REGISTRY))["phenotypes"] if s.get("enabled")]
        return cls._specs

    @staticmethod
    def decision(row, raw, state):
        """the ExperimentBook path: admit_completed on the prediction's bars (the source admits inside
        decision_from_prediction, on the wall clock), decision_from_prediction, the authorized-unqualified replace."""
        if state not in {"QUALIFIED", "AUTHORIZED_PAPER_EXPERIMENT"}:
            return tf.decision_from_prediction(row, [], state)
        completed, _ = tf.admit_completed(raw, str(row["timeframe"]), datetime.now(timezone.utc))
        fields = tf.decision_from_prediction(row, completed, state)
        if fields is None:
            return None
        if state != "QUALIFIED":
            fields["metrics"] = dict(fields["metrics"], paperExperimentAuthorized=True)
            fields["reasonCodes"] = ("AUTHORIZED_UNQUALIFIED_PAPER", *fields["reasonCodes"])
        from dataclasses import asdict
        return asdict(F._decision(fields))

    @staticmethod
    def purge(items):
        """the PurgedBook's admission over the events in arrival order (one tag: the source's per-hypothesis list)."""
        book = F.PurgedBook("griffith_weekly_cyan_confirmation", intervals=("1wk",), slots=1, cost_bps=50.0)
        st, kept = {}, []
        for sym, day in items:
            t = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
            ev = {"key": f"k|{sym}|{day}", "symbol": sym, "t": t, "tags": ["CY"], "purge_days": 84}
            if book.admit(ev, st, 0):
                kept.append([sym, day])
        return sorted(kept)


def _gen_ns():
    ns = {}
    exec(GEN, ns)
    exec(EVAL, ns)
    return ns


def source_batch(tree, seeds, detail=False):
    script = GEN + EVAL + SRC_LIB + r'''
res = []
for seed in PAYLOAD["seeds"]:
    c = build_case(seed)
    d, info = evaluate(L, c, detail=PAYLOAD["detail"])
    res.append({"seed": seed, "out": d, "info": info})
print(json.dumps(res, default=repr))
'''
    reg = json.load(open(REGISTRY))
    return run_source(script, {"seeds": seeds, "registry": reg, "detail": detail}, tree, 3600,
                      "tensor_research_parity_")


def port_batch(seeds, detail=False):
    ns = _gen_ns()
    out = []
    for seed in seeds:
        c = ns["build_case"](seed)
        d, info = ns["evaluate"](PortLib, c, detail=detail)
        out.append({"seed": seed, "out": json.loads(json.dumps(d, default=repr)), "info": info})
    return out


def first_diff(a, b, path=""):
    if type(a) is not type(b):
        return path, a, b
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}.{k}", a.get(k, "<missing>"), b.get(k, "<missing>")
            r = first_diff(a[k], b[k], f"{path}.{k}")
            if r:
                return r
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}[len]", len(a), len(b)
        for i, (x, y) in enumerate(zip(a, b)):
            r = first_diff(x, y, f"{path}[{i}]")
            if r:
                return r
        return None
    return None if a == b else (path, a, b)


def run_features(tree, n):
    from concurrent.futures import ThreadPoolExecutor
    seeds = list(range(n))
    batches = [seeds[i:i + 50] for i in range(0, n, 50)]
    diffs, cov, done = [], {}, 0

    def one(batch):
        return batch, source_batch(tree, batch), port_batch(batch)
    with ThreadPoolExecutor(max_workers=2) as ex:
        for batch, src, port in ex.map(one, batches):
            for s, p in zip(src, port):
                done += 1
                for k, v in s["info"].items():
                    key = f"{k}={v}" if isinstance(v, (bool, str)) else k
                    cov[key] = cov.get(key, 0) + (v if isinstance(v, int) and not isinstance(v, bool) else 1)
                bad = sorted(k for k in s["out"] if s["out"][k] != p["out"].get(k))
                if bad:
                    diffs.append({"seed": s["seed"], "components": bad})
            print(f"features {done}/{n}, diffs {len(diffs)}", flush=True)
    for d in diffs[:5]:                                     # the first differing value of each bad component
        s = source_batch(tree, [d["seed"]], detail=True)[0]["out"]
        p = port_batch([d["seed"]], detail=True)[0]["out"]
        d["first"] = {k: [str(x)[:200] for x in (first_diff(s[k], p[k]) or ())] for k in d["components"]}
    return {"cases": n, "diffs": diffs, "coverage": cov,
            "components": ["feature_tape", "feature_latest", "technical_tape", "technical_latest", "labels", "atoms",
                           "cyan", "tail", "specs", "specs_synthetic", "admit", "atr", "decision", "purge"]}


# -- Sable desk rules vs the autopilot-desk modules (node) ------------------------------------------------------------
SABLE_JS = r'''
const SRC = process.argv[process.argv.length - 1];
const { quoteFromCompletedBars } = await import(SRC + "/src/lib/market/quote-core.mjs");
const { swingSizeShares, canEnterUnderMandate } = await import(SRC + "/src/lib/desk/ledger-core.mjs");
const { applyStopsAndTargets } = await import(SRC + "/src/lib/desk/unattended-core.mjs");
const chunks = [];
for await (const c of process.stdin) chunks.push(c);
const cases = JSON.parse(Buffer.concat(chunks).toString("utf8"));
const mandate = { allowEtfs: true, allowStocks: true, excludeMegaCaps: false, allowOvernight: true,
  allowExtendedHours: false, allowStressBuys: false, allowEarningsWindow: false };
const out = [];
for (const c of cases) {
  const bars = c.bars.map((b) => ({ time: b.t, open: b.o, high: b.h, low: b.l, close: b.c, volume: b.v }));
  const q = quoteFromCompletedBars({ ticker: c.ticker, name: c.ticker, sector: "x", kind: c.kind }, bars);
  const size = swingSizeShares({ equity: c.equity, cash: c.cash, price: c.price, atr: c.atr, sizeDown: c.sizeDown });
  const gate = q ? canEnterUnderMandate(mandate, { ...q, regime: "supportive" }, "regular") : null;
  const state = { positions: [{ id: "p1", ticker: "T", qty: 10, avgPrice: c.avg, stop: c.stop, target: c.target }],
    quotes: { T: { price: c.mark, atr: c.qatr } }, events: [], orders: [], broker: { mode: "paper" }, cash: 0,
    mandate: {} };
  const pos = state.positions[0];
  applyStopsAndTargets(state);
  const exited = state.events.length > 0;
  out.push({ quote: q && { price: q.price, prevClose: q.prevClose, high: q.high, low: q.low, volume: q.volume,
      avgVolume: q.avgVolume, support: q.support, resistance: q.resistance, rsi: q.rsi, macdHist: q.macdHist,
      atr: q.atr, extensionAtr: q.extensionAtr, completedBarAt: q.completedBarAt, kind: q.kind },
    size, gate, bracket: { stop: pos.stop ?? null, target: pos.target ?? null,
      exited, body: exited ? state.events[0].body : null } });
}
process.stdout.write(JSON.stringify(out) + "\n");
'''


def sable_cases(n, seed=7):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        m = rnd.randint(2, 120)
        px = rnd.uniform(5, 500)
        bars = []
        for k in range(m):
            o = px * (1 + rnd.gauss(0, 0.003))
            c = max(0.5, px * (1 + rnd.gauss(rnd.choice([0.002, 0.0, -0.002]), 0.004)))
            h = max(o, c) * (1 + abs(rnd.gauss(0, 0.002)))
            lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.002)))
            bars.append({"t": 1_790_000_000 + 300 * k, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4),
                         "c": round(c, 4), "v": float(rnd.randint(0, 50_000))})
            px = c
        avg = rnd.uniform(5, 500)
        qatr = rnd.choice([None, 0.0, rnd.uniform(0.001, 0.05) * avg])
        stop = rnd.choice([None, round(avg * rnd.uniform(0.85, 1.0), 2)])
        target = rnd.choice([None, round(avg * rnd.uniform(1.0, 1.2), 2)])
        out.append({"ticker": rnd.choice(["AAPL", "SPY", "XOM", "SMH"]), "kind": rnd.choice(["stock", "etf"]),
                    "bars": bars, "equity": rnd.choice([0.0, rnd.uniform(1e3, 2e5)]), "cash": rnd.uniform(-10, 2e5),
                    "price": rnd.uniform(1, 600), "atr": rnd.choice([None, rnd.uniform(0.01, 20)]),
                    "sizeDown": rnd.random() < 0.3, "avg": avg, "qatr": qatr, "stop": stop, "target": target,
                    "mark": avg * rnd.uniform(0.85, 1.2)})
    return out


def port_sable(c):
    bars = c["bars"]
    q = F.sable_quote(c["ticker"], bars)
    size = F.swing_size_shares(c["equity"], c["cash"], c["price"], c["atr"], c["sizeDown"])
    gate = None
    if q:
        q = dict(q, kind=c["kind"])
        lb = {"run": "running", "edge": {}, "parked": [], "pos": {}, "working": {}, "cash": 1e9, "equity": 1e9}
        gate = F.can_enter(lb, c["ticker"], q, cal.session_open(datetime(2026, 10, 20).date()) + 3600)
    pos = {"avg": c["avg"], "stop": c["stop"], "target": c["target"]}
    hit = F.swing_bracket_check(pos, {"price": c["mark"], "atr": c["qatr"]})
    keys = ("price", "prevClose", "high", "low", "volume", "avgVolume", "support", "resistance", "rsi", "macdHist",
            "atr", "extensionAtr", "completedBarAt", "kind")
    return {"quote": q and {k: q.get(k) for k in keys}, "size": size, "gate": gate,
            "bracket": {"stop": pos["stop"], "target": pos["target"], "exited": hit is not None, "body": hit}}


def run_sable(src, n):
    cases = sable_cases(n)
    p = subprocess.run(["node", "--no-warnings", "--input-type=module", "-e", SABLE_JS, "--", src],
                       input=json.dumps(cases), capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        raise RuntimeError("sable source harness failed: " + p.stderr[-2000:])
    js = json.loads(p.stdout.strip().splitlines()[-1])
    diffs, cov = [], {}
    for i, (c, s) in enumerate(zip(cases, js)):
        mine = port_sable(c)
        if s["quote"] is not None:
            s["quote"]["kind"] = c["kind"]
        for k in ("quote", "size", "gate", "bracket"):
            a, b = json.loads(json.dumps(s[k])), json.loads(json.dumps(mine[k]))
            if a != b:
                diffs.append({"case": i, "what": k, "first": [str(x)[:160] for x in (first_diff(a, b) or ())]})
        cov["quote"] = cov.get("quote", 0) + (s["quote"] is not None)
        cov["gate_blocked"] = cov.get("gate_blocked", 0) + bool(s["gate"])
        cov["size_positive"] = cov.get("size_positive", 0) + (s["size"] > 0)
        cov["bracket_exit"] = cov.get("bracket_exit", 0) + bool(s["bracket"]["exited"])
    return {"cases": n, "diffs": diffs, "coverage": cov}


# -- the research studies' bar arithmetic --------------------------------------------------------------------------
def run_calendar(n, seed=11):
    rnd = random.Random(seed)
    start, end = datetime(2025, 1, 2).date(), datetime(2027, 6, 30).date()
    sessions, d = [], start
    while d <= end:
        if cal.is_trading_day(d):
            sessions.append(d)
        d += timedelta(days=1)
    hours = [o for s in sessions for o in P.hour_opens(s)]
    weeks = []
    for s in sessions:
        m = s - timedelta(days=s.weekday())
        if not weeks or weeks[-1][0] != m:
            weeks.append((m, []))
        weeks[-1][1].append(s)
    diffs, done = [], 0
    for _ in range(n):
        iv = rnd.choice(["1h", "1d", "1wk"])
        h = rnd.choice([1, 4, 10, 12, 13, 15, 20, 26, 30])
        if iv == "1d":
            i = rnd.randrange(len(sessions) - h - 1)
            t = int(cal.session_open(sessions[i])) + rnd.choice([0, 0, 3600 * 4])
            want = (cal.session_open(sessions[i + 1]), cal.session_close(sessions[i + h]), True)
        elif iv == "1wk":
            i = rnd.randrange(len(weeks) - h - 1)
            m = weeks[i][0]
            t = int(datetime(m.year, m.month, m.day, 9, 30, tzinfo=P.ET).timestamp())
            want = (cal.session_open(weeks[i + 1][1][0]), cal.session_close(weeks[i + h][1][-1]), True)
        else:
            i = rnd.randrange(len(hours) - h - 1)
            t = hours[i]
            e = P.hour_end(hours[i + h])
            want = (hours[i + 1], e, e == cal.session_close(cal._as_date(hours[i + h])))
        got = (P.entry_open(iv, t), *P.exit_close(iv, t, h))
        done += 1
        if tuple(float(x) if not isinstance(x, bool) else x for x in got) != \
                tuple(float(x) if not isinstance(x, bool) else x for x in want):
            diffs.append({"interval": iv, "t": t, "h": h, "port": list(got), "bars": list(want)})
    return {"cases": done, "diffs": diffs}


# -- as-of vs full replay -----------------------------------------------------------------------------------------------
def run_asof(n_symbols=34, points=30, seed=5):
    """per symbol: one full-series replay (its last `points` bars) and `points` as-of runs cut at each of those bars;
    the bar's markers, enrichment ids, sidecar and v615 Swing must agree."""
    from tests import tensor_research_fixtures as fx
    rnd = random.Random(seed)
    day = datetime(2026, 10, 16).date()
    specs = []
    for k in range(n_symbols):
        iv = ("1d", "1wk", "1h")[k % 3]
        n = {"1d": 504, "1wk": 520, "1h": 1750}[iv]
        times = {"1d": lambda: fx.daily_times(day, n), "1wk": lambda: fx.weekly_times(day, n),
                 "1h": lambda: fx.hourly_times(P.hour_opens(day)[-1], n)}[iv]()
        ohlcv = fx.path(random.Random(rnd.randrange(10 ** 9)), n)
        bars = [{"t": t, "o": o, "h": h, "l": l, "c": c, "v": v} for t, (o, h, l, c, v) in zip(times, ohlcv)]
        specs.append((f"S{k:02d}", iv, bars))
    view = {"name": "v", "sidecar": True, "swing615": True, "decorate": "never"}
    jobs, meta = [], []
    for sym, iv, bars in specs:
        jobs.append({"symbol": sym, "interval": iv, "bars": bars, "views": [dict(view, tail=points)]})
        meta.append((sym, iv, "full", len(bars)))
        for j in range(len(bars) - points, len(bars)):
            jobs.append({"symbol": sym, "interval": iv, "bars": bars[:j + 1], "views": [dict(view, tail=1)]})
            meta.append((sym, iv, "asof", j))
    results = {}

    def chunk_run(chunk):                    # the runner answers in job order (one symbol repeats within a chunk)
        res = P.run_batch(chunk)["results"]
        return [((j["symbol"], len(j["bars"]), j["views"][0]["tail"]), r) for j, r in zip(chunk, res)]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=P.WORKERS) as ex:
        for got in ex.map(chunk_run, [jobs[i:i + 10] for i in range(0, len(jobs), 10)]):
            results.update(got)
    keys = ("timestamp", "primaryMarkers", "dcbMarker", "warningMarker", "enrichmentIds", "sidecar")
    diffs, done, cov = [], 0, {"markers": 0, "genomes": 0, "phenotypes": 0, "swing_confirmed": 0}
    for sym, iv, bars in specs:
        full = results[(sym, len(bars), points)]
        rows = (full.get("views") or {}).get("v", {}).get("bars") or []
        for k, j in enumerate(range(len(bars) - points, len(bars))):
            one = results[(sym, j + 1, 1)]
            mine = ((one.get("views") or {}).get("v", {}).get("bars") or [None])[-1]
            ref = rows[k] if k < len(rows) else None
            done += 1
            if not mine or not ref:
                diffs.append({"symbol": sym, "interval": iv, "bar": j, "error": "missing row"})
                continue
            a = {x: ref.get(x) for x in keys}
            b = {x: mine.get(x) for x in keys}
            a["swing"] = {x: (ref.get("swing615") or {}).get(x) for x in ("confirmed", "eventKey", "setupBarTimestamp")}
            b["swing"] = {x: (mine.get("swing615") or {}).get(x) for x in ("confirmed", "eventKey", "setupBarTimestamp")}
            if a != b:
                diffs.append({"symbol": sym, "interval": iv, "bar": j,
                              "first": [str(x)[:160] for x in (first_diff(a, b) or ())]})
            cov["markers"] += bool(a["primaryMarkers"])
            cov["genomes"] += bool((a["sidecar"] or {}).get("genomes"))
            cov["phenotypes"] += bool((a["sidecar"] or {}).get("phenotypes"))
            cov["swing_confirmed"] += bool(a["swing"]["confirmed"])
    return {"cases": done, "diffs": diffs, "coverage": cov}


# -- the HTF universe classification (tensor_htf_asset_classification.classify) -----------------------------------
CLASSIFY_SRC = r"""
import sys
sys.dont_write_bytecode = True
from tensor_htf_asset_classification import classify
print(json.dumps([classify({"name": n, "exchange": e}) for n, e in PAYLOAD["rows"]]))
"""
WORDS = ["Apple", "Inc.", "Common Stock", "iShares", "Core", "S&P", "500", "ETF", "Trust", "ProShares", "UltraPro",
         "QQQ", "Direxion", "Daily", "Bull", "3x", "2X", "Shares", "Fund", "Fundamental", "Index", "Indexed", "SPDR",
         "VanEck", "Vectors", "WisdomTree", "Global X", "Global", "X", "Exchange-Traded", "Exchange Traded", "ETN",
         "Portfolio", "Portfolios", "Holdings", "Corp", "Class A", "Ordinary Shares", "Units", "Warrant"]
EXCH = ["NASDAQ", "NYSE", "ARCA", "BATS", "AMEX", "NYSEARCA", "IEX", "", "OTC"]


def run_classify(tree, n, seed=13):
    rnd = random.Random(seed)
    rows = []
    for _ in range(n):
        name = " ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 6)))
        rows.append((name.swapcase() if rnd.random() < 0.2 else name, rnd.choice(EXCH)))
    src = run_source(CLASSIFY_SRC, {"rows": rows}, tree, 900, "tensor_research_parity_")
    diffs = [{"name": r[0], "exchange": r[1], "source": a, "port": P.classify(*r)}
             for r, a in zip(rows, src) if P.classify(*r) != a]
    return {"cases": n, "diffs": diffs,
            "coverage": {"fund": sum(1 for a in src if a.startswith("FUND")),
                         "operating": sum(1 for a in src if a.startswith("OPER"))}}


PARTS = ("features", "sable", "calendar", "asof", "classify")


def main(argv):
    n = int(argv[0]) if argv else N_CASES
    parts = (argv[1].split(",") if len(argv) > 1 else list(PARTS))
    tree = os.environ.get("TENSOR_SRC")
    apsrc = os.environ.get("AUTOPILOT_SRC")
    receipt = {"family": "tensor_research", "sleeves": [s.CONFIG.sleeve_id for s in F.sleeves()]}
    prior = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs",
                         "receipts", "parity", "tensor_research.json")
    if os.environ.get("PARITY_MERGE") and os.path.exists(prior):     # add parts to the standing receipt
        old = json.load(open(prior))
        receipt.update({k: old[k] for k in PARTS if k in old and k not in parts})
    if "classify" in parts:
        if not tree or not os.path.isdir(tree):
            raise SystemExit("set TENSOR_SRC to a scratch copy of agentic-trading-desk@4c8c179")
        receipt["classify"] = run_classify(tree, max(n, 2000))
        print("classify done", len(receipt["classify"]["diffs"]), flush=True)
    if "features" in parts:
        if not tree or not os.path.isdir(tree):
            raise SystemExit("set TENSOR_SRC to a scratch copy of agentic-trading-desk@4c8c179")
        receipt["features"] = run_features(tree, n)
        print("features done", len(receipt["features"]["diffs"]), flush=True)
    if "sable" in parts:
        if not apsrc or not os.path.isdir(apsrc):
            raise SystemExit("set AUTOPILOT_SRC to autopilot-desk@48e8f90f")
        receipt["sable"] = run_sable(apsrc, n)
        print("sable done", len(receipt["sable"]["diffs"]), flush=True)
    if "calendar" in parts:
        receipt["calendar"] = run_calendar(max(n, 3000))
        print("calendar done", len(receipt["calendar"]["diffs"]), flush=True)
    if "asof" in parts:
        receipt["asof"] = run_asof(n_symbols=int(os.environ.get("PARITY_ASOF_SYMBOLS", "34")))
        print("asof done", len(receipt["asof"]["diffs"]), flush=True)
    total = sum(receipt[k]["cases"] for k in PARTS if k in receipt)
    bad = sum(len(receipt[k]["diffs"]) for k in PARTS if k in receipt)
    receipt.update(cases=total, n_diffs=bad, identical=total - bad,
                   source={"agentic": {"repo": "agentic-trading-desk", "commit": "4c8c179c5988d6e603c1f3c5f28f93e2344ca225"},
                           "autopilot": {"repo": "autopilot-desk", "commit": "48e8f90f5d9def28363eb4013dac4dd8d78f74bf"}},
                   not_comparable="the event books' lot accounting, MID21's make_plan on the engine, TRACE's daily-scale "
                                  "pipeline and the Sable sub-books have no runnable source on these inputs "
                                  "(tests/test_tensor_research.py checks each rule); the pinned v698 engine, the v619 "
                                  "sidecar, the v615 Swing, scout-hands.mjs and trace_r10.py run as vendored source")
    path = write_receipt("tensor_research", receipt)
    print(json.dumps({"cases": total, "diffs": bad, "receipt": path}))


if __name__ == "__main__":
    main(sys.argv[1:])
