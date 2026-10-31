#!/usr/bin/env python3
"""Independent-oracle crosscheck: our morgue pricing vs Codex's option stack.

Adopted 2026-10-28 (evaluation 05 section 2 item 1 / section 7 item 3).
Runs OUR ~/workspace/morgue/bs.py + payoff.py and HIS European
Black-Scholes / American CRR / payoff / sensitivity-grid functions
(extracted verbatim from the read-only reference copy
oracle/codex_app.js, executed under node) on:

  1. the Hull textbook case (call 10.450576 / put 5.573518),
  2. put-call parity cases (incl. a dividend case),
  3. an American put early-exercise case (CRR premium +0.513 reference),
  4. the Payoff Sketch's eight fixture positions (the set recorded in
     terminal-lineup/BUILD-PROGRESS.md, Tool 6 verify phase: five
     fixture cases plus the verifier's three extra cases, legs exactly
     as in that harness),
  5. a gamma known-answer case at an off-ATM strike (S100/K80/30d/20%):
     our morgue map gamma (bs.gamma, the map_gex path) against his
     European model's gamma. This is the independent-oracle blocker
     his own GEX fixture lacked (05 section 7 item 1 pattern applied
     to our GEX): his static-GEX blackScholesGamma is NOT used, it is
     the defective function (03 section 2.6).

Tolerance: 1e-4 relative. Any disagreement beyond it is printed and
listed under DISAGREEMENTS, never smoothed. Near-zero quantities also
show their absolute error so a relative blow-up on a ~0 value can be
judged on its face.

Usage: python3 crosscheck_payoff.py [--json PATH]
Exit code 0 when every check is within tolerance, 1 otherwise.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))
import bs  # noqa: E402  (our morgue Black-Scholes)
import payoff  # noqa: E402  (our morgue expiration payoff)

TOL = 1e-4
APP_JS = os.path.join(HERE, "codex_app.js")

JS_FUNCS = ["optionStrategyPnlAt", "optionStrategyStats",
            "standardNormalCdf", "blackScholesEuropean",
            "crrAmericanOption", "americanCrrGreeks",
            "optionScenarioModel", "buildOptionStrategyModel",
            "buildOptionStrategySensitivity"]

# The Payoff Sketch's eight fixture positions (BUILD-PROGRESS Tool 6
# verify harness): page-side leg spelling (buy/sell, qty).
FIXTURES = [
    ("long call", [{"type": "call", "side": "buy", "strike": 100,
                    "premium": 3, "qty": 1}]),
    ("long put x2", [{"type": "put", "side": "buy", "strike": 100,
                      "premium": 2.5, "qty": 2}]),
    ("bull call spread (sample)",
     [{"type": "call", "side": "buy", "strike": 100, "premium": 3, "qty": 1},
      {"type": "call", "side": "sell", "strike": 110, "premium": 1, "qty": 1}]),
    ("short straddle",
     [{"type": "call", "side": "sell", "strike": 100, "premium": 4, "qty": 1},
      {"type": "put", "side": "sell", "strike": 100, "premium": 3.5, "qty": 1}]),
    ("iron condor 4-leg",
     [{"type": "put", "side": "buy", "strike": 90, "premium": 0.5, "qty": 1},
      {"type": "put", "side": "sell", "strike": 95, "premium": 1.2, "qty": 1},
      {"type": "call", "side": "sell", "strike": 105, "premium": 1.1, "qty": 1},
      {"type": "call", "side": "buy", "strike": 110, "premium": 0.4, "qty": 1}]),
    ("own short put", [{"type": "put", "side": "sell", "strike": 80,
                        "premium": 1.75, "qty": 3}]),
    ("own long straddle",
     [{"type": "call", "side": "buy", "strike": 95, "premium": 4.2, "qty": 1},
      {"type": "put", "side": "buy", "strike": 95, "premium": 3.8, "qty": 1}]),
    ("own bear put spread",
     [{"type": "put", "side": "buy", "strike": 105, "premium": 5, "qty": 2},
      {"type": "put", "side": "sell", "strike": 90, "premium": 1.5, "qty": 2}]),
]
PRICES = [0, 25, 50, 80, 90, 92.5, 95, 100, 102, 105, 107.5, 110, 120, 150, 200]
# spot, days, vol% at the morgue/Payoff Sketch rate convention (4.5%, no div)
GREEK_SETTINGS = [(100, 30, 25), (85, 60, 40), (120, 7, 15)]
RATE_PCT = 4.5

PARITY_CASES = [  # S, K, days, iv%, rate%, div%
    (100, 100, 365, 20, 5, 0),
    (100, 100, 180, 35, 4.5, 2),
    (120, 90, 90, 30, 3, 1),
    (80, 110, 30, 45, 5, 0),
]


def extract_js(path):
    src = open(path, encoding="utf-8").read()
    out = []
    for name in JS_FUNCS:
        i = src.index(f"function {name}(")
        j = src.index("{", i)
        depth, k = 0, j
        while True:
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out.append(src[i:k + 1])
    return "\n".join(out)


def his_legs(legs):
    return [{"type": l["type"],
             "side": "long" if l["side"] == "buy" else "short",
             "strike": l["strike"], "premium": l["premium"],
             "contracts": l["qty"], "multiplier": 100,
             "ivPct": None} for l in legs]


def our_legs(legs):
    return [{"type": l["type"],
             "side": "long" if l["side"] == "buy" else "short",
             "strike": float(l["strike"]), "premium": float(l["premium"]),
             "contracts": float(l["qty"]), "multiplier": 100.0}
            for l in legs]


def run_his():
    jobs = {"hull": {}, "parity": [], "american": {}, "fixtures": [],
            "gamma": {}, "sensitivity": {}}
    jobs["hull"] = {"call": ["blackScholesEuropean", 100, 100, 365, 20, 5, 0, "call"],
                    "put": ["blackScholesEuropean", 100, 100, 365, 20, 5, 0, "put"]}
    jobs["parity"] = [[S, K, d, iv, r, q] for (S, K, d, iv, r, q) in PARITY_CASES]
    jobs["gamma"] = {"args": [100, 80, 30, 20, RATE_PCT, 0, "call"]}
    jobs["gamma_r0"] = {"args": [100, 80, 30, 20, 0, 0, "call"]}
    js = extract_js(APP_JS) + r"""
const jobs = JSON.parse(process.argv[2]);
const out = {};
const eu = (a) => blackScholesEuropean(...a.slice(1));
out.hull = { call: eu(jobs.hull.call), put: eu(jobs.hull.put) };
out.parity = jobs.parity.map(([S,K,d,iv,r,q]) => ({
  call: blackScholesEuropean(S,K,d,iv,r,q,'call').theoreticalPrice,
  put: blackScholesEuropean(S,K,d,iv,r,q,'put').theoreticalPrice }));
out.american = {
  put200: crrAmericanOption(100,100,365,20,5,0,'put',200),
  put300: crrAmericanOption(100,100,365,20,5,0,'put',300),
  call200: crrAmericanOption(100,100,365,20,5,0,'call',200),
  call300: crrAmericanOption(100,100,365,20,5,0,'call',300),
  euPut: blackScholesEuropean(100,100,365,20,5,0,'put').theoreticalPrice,
  euCall: blackScholesEuropean(100,100,365,20,5,0,'call').theoreticalPrice };
out.gamma = blackScholesEuropean(...jobs.gamma.args);
out.gamma_r0 = blackScholesEuropean(...jobs.gamma_r0.args);
out.fixtures = jobs.fixtures.map(f => ({
  pnls: f.prices.map(p => optionStrategyPnlAt(f.legs, p)),
  stats: optionStrategyStats(f.legs),
  models: f.settings.map(s => buildOptionStrategyModel(f.legs, s)) }));
out.sensitivityBase = (() => {
  const f = jobs.fixtures[2]; const s = f.settings[0];
  const grid = buildOptionStrategySensitivity(f.legs, s);
  const model = buildOptionStrategyModel(f.legs, s);
  return { gridBasePnl: grid.rows[1].cells[2].modeledPnlVsEntry,
           modelPnl: model.modeledPnlVsEntry };
})();
console.log(JSON.stringify(out));
"""
    job_payload = {
        "hull": jobs["hull"], "parity": jobs["parity"],
        "gamma": jobs["gamma"], "gamma_r0": jobs["gamma_r0"],
        "fixtures": [{
            "legs": his_legs(legs), "prices": PRICES,
            "settings": [{"spot": S, "daysToExpiration": d,
                          "volatilityPct": v, "riskFreeRatePct": RATE_PCT,
                          "dividendYieldPct": 0,
                          "exerciseStyle": "european", "treeSteps": 200}
                         for (S, d, v) in GREEK_SETTINGS],
        } for _, legs in FIXTURES],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(js)
        path = fh.name
    try:
        r = subprocess.run(["node", path, json.dumps(job_payload)],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError(f"node failed: {r.stderr[:2000]}")
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def rel(a, b):
    """Relative error of a against reference b."""
    if b == 0:
        return 0.0 if a == 0 else float("inf")
    return abs(a - b) / abs(b)


def main():
    his = run_his()
    rows, bad = [], []

    def check(name, ours, his_v, ref=None):
        r = rel(ours, his_v) if ref is None else rel(his_v, ref)
        ok = r <= TOL
        rows.append((name, ours, his_v, r, ok))
        if not ok:
            bad.append((name, ours, his_v, r))
        return r

    # 1. Hull textbook case: both engines against the textbook answers.
    mc = bs.price(100, 100, 1.0, 0.20, True, rate=0.05)
    mp = bs.price(100, 100, 1.0, 0.20, False, rate=0.05)
    check("Hull call vs textbook 10.450576 (ours)", mc, 10.450576)
    check("Hull call vs textbook 10.450576 (his)", his["hull"]["call"]["theoreticalPrice"], 10.450576)
    check("Hull put vs textbook 5.573518 (ours)", mp, 5.573518)
    check("Hull put vs textbook 5.573518 (his)", his["hull"]["put"]["theoreticalPrice"], 5.573518)
    check("Hull call ours-vs-his", mc, his["hull"]["call"]["theoreticalPrice"])
    check("Hull put ours-vs-his", mp, his["hull"]["put"]["theoreticalPrice"])
    for g in ("delta", "gamma", "vegaPerPctPoint"):
        pass  # fixture-position greeks below cover greeks systematically

    # 2. Put-call parity: residual C-P-(S e^-qT - K e^-rT) for both engines.
    for i, (S, K, d, iv, r, q) in enumerate(PARITY_CASES):
        T, sig = d / 365.0, iv / 100.0
        expect = S * math.exp(-q / 100 * T) - K * math.exp(-r / 100 * T)
        oc = bs.price(S, K, T, sig, True, rate=r / 100, div=q / 100)
        op = bs.price(S, K, T, sig, False, rate=r / 100, div=q / 100)
        check(f"parity[{i}] ours residual (S{S} K{K} {d}d iv{iv} r{r} q{q})",
              oc - op, expect)
        check(f"parity[{i}] his residual (S{S} K{K} {d}d iv{iv} r{r} q{q})",
              his["parity"][i]["call"] - his["parity"][i]["put"], expect)

    # 3. American early exercise: his CRR put premium vs +0.513 reference;
    #    no-dividend call must carry (almost) no premium.
    prem200 = his["american"]["put200"] - his["american"]["euPut"]
    prem300 = his["american"]["put300"] - his["american"]["euPut"]
    check("American put CRR200 vs ref 6.086383", his["american"]["put200"], 6.086383)
    check("American put premium (200 steps) vs +0.513", prem200, 0.513)
    rows.append(("American put premium (300 steps, informational)",
                 prem300, prem200, rel(prem300, prem200), prem300 > 0))
    call_prem = his["american"]["call300"] - his["american"]["euCall"]
    rows.append(("American no-div call premium (300 steps, must be ~<=0)",
                 call_prem, 0.0, abs(call_prem), call_prem <= 0.001))
    if call_prem > 0.001:
        bad.append(("American no-div call premium", call_prem, 0.0, call_prem))

    # 4. Eight fixture positions: expiry payoff, stats, model greeks.
    for (name, legs), hf in zip(FIXTURES, his["fixtures"]):
        L = our_legs(legs)
        worst = 0.0
        for p, hv in zip(PRICES, hf["pnls"]):
            worst = max(worst, rel(payoff.pnl_at(L, p), hv) if hv else
                        abs(payoff.pnl_at(L, p) - hv))
        rows.append((f"fixture {name}: payoff max rel err over {len(PRICES)} prices",
                     worst, 0.0, worst, worst <= TOL))
        if worst > TOL:
            bad.append((f"fixture {name} payoff", worst, 0.0, worst))
        st, hs = payoff.stats(L), hf["stats"]
        stat_pairs = [("netDebit", st["net_debit"], hs["netDebit"])]
        if not st["unbounded_profit"]:
            stat_pairs.append(("maxPnl", st["max_pnl"], hs["maxPnl"]))
        if not st["unbounded_loss"]:
            stat_pairs.append(("minPnl", st["min_pnl"], hs["minPnl"]))
        flags_ok = (st["unbounded_profit"] == hs["unboundedProfit"]
                    and st["unbounded_loss"] == hs["unboundedLoss"])
        be_ok = (len(st["breakevens"]) == len(hs["breakEvens"]) and all(
            rel(a, b) <= TOL for a, b in zip(st["breakevens"], hs["breakEvens"])))
        s_ok = flags_ok and be_ok and all(rel(a, b) <= TOL for _, a, b in stat_pairs)
        detail = "; ".join(f"{k} ours={a} his={b}" for k, a, b in stat_pairs)
        rows.append((f"fixture {name}: stats ({detail}; breakevens "
                     f"ours={st['breakevens']} his={hs['breakEvens']}; "
                     f"unbounded flags match={flags_ok})",
                     0.0 if s_ok else 1.0, 0.0, 0.0 if s_ok else 1.0, s_ok))
        if not s_ok:
            bad.append((f"fixture {name} stats", detail,
                        f"his breakevens={hs['breakEvens']}", float("nan")))
        # Model value + greeks at the three settings (European, r=4.5%).
        for si, (S, d, v) in enumerate(GREEK_SETTINGS):
            T, sig = d / 365.0, v / 100.0
            val = delta = gamma = theta = vega = 0.0
            for l in legs:
                w = (1 if l["side"] == "buy" else -1) * l["qty"] * 100
                ic = l["type"] == "call"
                val += w * bs.price(S, l["strike"], T, sig, ic)
                delta += w * bs.delta(S, l["strike"], T, sig, ic)
                gamma += w * bs.gamma(S, l["strike"], T, sig)
                theta += w * bs.theta(S, l["strike"], T, sig, ic) / 365.0
                vega += w * bs.vega(S, l["strike"], T, sig) / 100.0
            hm = hf["models"][si]
            pairs = [("value", val, hm["netTheoreticalValue"]),
                     ("delta", delta, hm["netDelta"]),
                     ("gamma", gamma, hm["netGamma"]),
                     ("theta/day", theta, hm["netThetaPerDay"]),
                     ("vega/pct", vega, hm["netVegaPerPctPoint"])]
            worst_g, worst_k = 0.0, ""
            for k, a, b in pairs:
                rr = rel(a, b) if abs(b) > 1e-9 else abs(a - b)
                if rr > worst_g:
                    worst_g, worst_k = rr, k
            ok = worst_g <= TOL
            rows.append((f"fixture {name}: model greeks setting {si+1} "
                         f"(S{S} {d}d vol{v}%), worst={worst_k}",
                         worst_g, 0.0, worst_g, ok))
            if not ok:
                bad.append((f"fixture {name} greeks setting {si+1} ({worst_k})",
                            str(pairs), "", worst_g))

    # Sensitivity grid base-cell identity (his grid vs his own model).
    sb = his["sensitivityBase"]
    check("sensitivity base cell == model P/L (his, bull spread setting 1)",
          sb["gridBasePnl"], sb["modelPnl"])

    # 5. Gamma known-answer blocker case, off-ATM: ours vs his European.
    g_ours = bs.gamma(100.0, 80.0, 30 / 365.0, 0.20, rate=0.045, div=0.0)
    g_his = his["gamma"]["gamma"]
    g_err = rel(g_ours, g_his)
    rows.append(("GAMMA BLOCKER S100/K80/30d/20% r4.5: morgue bs.gamma "
                 f"(ours={g_ours:.10g}) vs his European gamma "
                 f"(his={g_his:.10g}); our relative error",
                 g_ours, g_his, g_err, g_err <= TOL))
    if g_err > TOL:
        bad.append(("gamma blocker S100/K80/30d/20%", g_ours, g_his, g_err))
    # Same case at r=0 anchors both engines to the review's independent
    # correct value for this strike (03 section 2.6 table: 3.1993e-5).
    g0_ours = bs.gamma(100.0, 80.0, 30 / 365.0, 0.20, rate=0.0, div=0.0)
    check("GAMMA ANCHOR r0: ours vs 03 independent value 3.1993e-5",
          g0_ours, 3.1993e-5)
    check("GAMMA ANCHOR r0: his vs 03 independent value 3.1993e-5",
          his["gamma_r0"]["gamma"], 3.1993e-5)
    check("GAMMA ANCHOR r0: ours-vs-his", g0_ours, his["gamma_r0"]["gamma"])

    print(f"{'check':<72} {'rel err':>12}  verdict")
    for name, a, b, r, ok in rows:
        print(f"{name[:72]:<72} {r:>12.3e}  {'PASS' if ok else 'FAIL'}")
    print(f"\n{sum(1 for *_, ok in rows if ok)}/{len(rows)} checks within "
          f"{TOL:g} relative tolerance")
    if bad:
        print("\nDISAGREEMENTS beyond tolerance (named, not smoothed):")
        for name, a, b, r in bad:
            print(f"- {name}: ours={a} his={b} rel={r}")
    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        with open(p, "w") as fh:
            json.dump({"tolerance": TOL,
                       "rows": [{"check": n, "ours": a, "his": b,
                                 "rel_err": r, "ok": ok}
                                for n, a, b, r, ok in rows],
                       "disagreements": [str(x) for x in bad]}, fh, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
