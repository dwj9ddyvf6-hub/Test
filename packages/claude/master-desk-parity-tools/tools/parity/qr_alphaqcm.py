"""qr_alphaqcm: the AlphaQCM reconstruction's native outputs and native torch operators vs
desk/sleeves/quant_research/alphaqcm.py (+ alphagen_np.py).

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/source.zip.parts, extracted
(SIXAI_X; members sha256-pinned below):
  (A) the reconstruction's own frozen native outputs on its real panel: alphaqcm/runs/corrected-seed2/signals.csv.gz
      (train_native's causal daily ensemble score, every eligible roster name and date 2017-01-03..2026-10-07),
      data/panel.npz (its eligibility mask) and alphaqcm/outputs/alphaqcm-selected-targets.csv.gz (export_portfolios'
      top-20% targets). PORT: alphaqcm's eligibility (common.eligibility) on the panel's close / volume / valid,
      alphagen_np.ensemble over the whole panel, and on each native target date the sleeve's own decision path
      (is_decision cadence, scores() on the trailing 300-row panel, top_weights()).
  (B) the native operators themselves (alphaqcm/vendor/alphagen, torch; run with TORCH_PYTHON -I in its own process)
      on randomized expressions from the native grammar (alphagen.config OPERATORS, DELTA_TIMES, CONSTANTS) over
      synthetic panels with gaps and ineligible stretches: CachedCalculator's mask + normalize_by_day per
      expression vs alphagen_np -- both in float64 (the operators' semantics, free of float32 summation-order noise;
      (A) covers the float32 production path). Rows on which an expression is constant across stocks normalise to
      rounding noise on both sides and are counted, not compared.
Tolerance: (A) float32 -- |port - native| <= 1e-5 * max(1, |native|) per value, selections exact; (B) float64 --
<= 1e-9 * max(1, |native|).
Part (B) is skipped (and recorded) when TORCH_PYTHON is not set."""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

from . import write_receipt

SIXAI_X = os.environ.get("SIXAI_X", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/"
                                    "sixai/x")
TORCH_PYTHON = os.environ.get("TORCH_PYTHON")
PINS = {"data/panel.npz": None,
        "alphaqcm/runs/corrected-seed2/signals.csv.gz": None,
        "alphaqcm/outputs/alphaqcm-selected-targets.csv.gz": None,
        "alphaqcm/vendor/alphagen/data/expression.py": None,
        "alphaqcm/vendor/alphagen/utils/pytorch_utils.py": None,
        "alphaqcm/vendor/alphagen_qlib/stock_data.py": None,
        "alphaqcm/vendor/alphagen/config.py": None}
N_EXPR = int(os.environ.get("ALPHAQCM_PARITY_EXPRS", 1200))
TOL = 1e-5
TOL_B = 1e-9


def sha(rel):
    return hashlib.sha256(open(os.path.join(SIXAI_X, rel), "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------- (A) native outputs
def part_a():
    from desk.sleeves.quant_research import alphagen_np as A
    from desk.sleeves.quant_research import alphaqcm as Q
    from desk.sleeves.quant_research import common as C
    z = np.load(os.path.join(SIXAI_X, "data/panel.npz"), allow_pickle=False)
    dates = z["dates"]
    pos = np.array([int(np.flatnonzero(z["symbols"] == s)[0]) for s in Q.ROSTER])
    arr = {k: z[k][:, pos].astype(float) for k in ("open", "close", "high", "low", "volume", "vwap")}
    valid = z["valid"][:, pos]
    elig_native = z["eligible"][:, pos]
    elig = C.eligibility(arr["close"], arr["volume"], valid)
    elig_bad = int((elig != elig_native).sum())
    a = int(np.searchsorted(dates, "2016-06-01"))
    data = np.stack([arr[k] for k in A.FEATURES], axis=1)
    data[~np.isfinite(data)] = np.nan
    data = data[a - 100:].astype(np.float32)
    score = A.ensemble(Q.NODES, Q.POOL["weights"], data, elig[a - 100:], 100, data.shape[0])
    sig = pd.read_csv(os.path.join(SIXAI_X, "alphaqcm/runs/corrected-seed2/signals.csv.gz"),
                      float_precision="round_trip")
    di = {d: i for i, d in enumerate(dates[a:])}
    sj = {s: j for j, s in enumerate(Q.ROSTER)}
    mine = np.array([score[di[r.date], sj[r.symbol]] for r in sig.itertuples()])
    native = sig.score.values
    diff = np.abs(mine - native)
    score_bad = int((~(diff <= TOL * np.maximum(1.0, np.abs(native)))).sum())
    have = set(zip(sig.date, sig.symbol))
    port_set = {(dates[a + i], Q.ROSTER[j]) for i, j in zip(*np.nonzero(~np.isnan(score)))}
    set_bad = len(have ^ port_set)
    # the sleeve's own decision path on each native target date
    tg = pd.read_csv(os.path.join(SIXAI_X, "alphaqcm/outputs/alphaqcm-selected-targets.csv.gz"))
    native_dates = sorted(tg.date.unique())
    port_dates = [d for d in dates if Q.is_decision(d)]
    cadence_bad = len(set(native_dates) ^ set(port_dates))
    sel_bad, sel = [], 0
    for d in native_dates:
        i = int(np.flatnonzero(dates == d)[0])
        P = {k: v[i - Q.N_ROWS + 1:i + 1] for k, v in arr.items()}
        P["valid"] = valid[i - Q.N_ROWS + 1:i + 1]
        w = Q.top_weights(Q.scores(P))
        want = tg[tg.date == d].set_index("symbol").weight.to_dict()
        sel += 1
        if w is None or set(w) != set(want) or any(abs(w[s] - want[s]) > 1e-15 for s in want):
            sel_bad.append({"date": d, "port_only": sorted(set(w or {}) - set(want)),
                            "native_only": sorted(set(want) - set(w or {}))})
    return {"scores": len(native), "score_bad": score_bad, "max_abs_diff": float(np.nanmax(diff)),
            "eligibility_cells": int(elig.size), "eligibility_bad": elig_bad, "scored_set_bad": set_bad,
            "decision_dates": len(native_dates), "cadence_bad": cadence_bad, "selections": sel,
            "selection_bad": len(sel_bad), "selection_diffs": sel_bad[:3]}


# ------------------------------------------------------------------------------------------- (B) native operators
TORCH_SCRIPT = r'''
import json, sys
VENDOR = sys.argv[1]
sys.path.insert(0, VENDOR)
import numpy as np, torch
from alphagen_qlib.stock_data import StockData
from alphagen.data.expression import *
from alphagen.config import OPERATORS
from alphagen.utils.pytorch_utils import normalize_by_day
import ast

def parse_native_expression(text):
    scope = {x.__name__: x for x in OPERATORS}
    scope['Constant'] = Constant
    for feature in FeatureType:
        scope[feature.name.lower()] = Feature(feature)
    rewritten = text.replace('$', '')
    tree = ast.parse(rewritten, mode='eval')
    return eval(compile(tree, '<native-alphaqcm-expression>', 'eval'), {'__builtins__': {}}, scope)

class Panel(StockData):
    def __init__(self, arr):
        self.arr = arr
        super().__init__('synthetic', '', '', 100, 0, device=torch.device('cpu'))
    @classmethod
    def _init_qlib(cls):
        return
    def _get_data(self):
        return torch.tensor(self.arr, dtype=torch.float64), None, None

out = []
for case in json.load(sys.stdin)["cases"]:
    arr = np.array(case["data"], dtype=np.float64)
    arr[~np.isfinite(arr)] = np.nan
    data = Panel(arr)
    elig = torch.tensor(np.array(case["elig"], dtype=bool)[100:])
    res = []
    for text in case["exprs"]:
        try:
            v = parse_native_expression(text).evaluate(data).clone()
        except Exception as e:
            res.append({"error": type(e).__name__}); continue
        v[~elig] = torch.nan
        v[~torch.isfinite(v)] = torch.nan
        res.append({"v": normalize_by_day(v).numpy().astype(float).tolist()})
    out.append(res)
print(json.dumps(out))
'''

OPS_UNARY = ["Abs", "Log"]
OPS_BINARY = ["Add", "Sub", "Mul", "Div", "Greater", "Less"]
OPS_ROLL = ["Ref", "Mean", "Sum", "Std", "Var", "Max", "Min", "Med", "Mad", "Delta", "WMA", "EMA"]
OPS_PAIR = ["Cov", "Corr"]
DTS = [10, 20, 30, 40, 50]
CONSTS = [-30., -10., -5., -2., -1., -0.5, -0.01, 0.01, 0.5, 1., 2., 5., 10., 30.]
FEATS = ["$open", "$close", "$high", "$low", "$volume", "$vwap"]


def rand_expr(rng, depth=0, budget=None):
    budget = budget if budget is not None else [0]
    r = rng.random()
    if depth >= 2 or r < 0.25:
        return str(rng.choice(FEATS))
    kind = rng.choice(["u", "b", "r", "p"], p=[0.2, 0.35, 0.35, 0.1])
    if kind == "u":
        return f"{rng.choice(OPS_UNARY)}({rand_expr(rng, depth + 1, budget)})"
    if kind == "b":
        lhs = rand_expr(rng, depth + 1, budget)
        rhs = f"Constant({rng.choice(CONSTS)})" if rng.random() < 0.4 else rand_expr(rng, depth + 1, budget)
        return f"{rng.choice(OPS_BINARY)}({lhs},{rhs})" if rng.random() < 0.5 else \
            f"{rng.choice(OPS_BINARY)}({rhs},{lhs})"
    dt = int(rng.choice(DTS)) if budget[0] < 50 else 10
    budget[0] += dt
    if kind == "r":
        return f"{rng.choice(OPS_ROLL)}({rand_expr(rng, depth + 1, budget)},{dt})"
    return f"{rng.choice(OPS_PAIR)}({rand_expr(rng, depth + 1, budget)},{rand_expr(rng, depth + 1, budget)},{dt})"


def synth_panel(rng, n=260, m=40):
    r = rng.normal(0.0003, rng.uniform(0.01, 0.04, m), (n, m))
    c = rng.uniform(5, 300, m) * np.exp(np.cumsum(r, axis=0))
    o = c * np.exp(rng.normal(0, 0.005, (n, m)))
    h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, 0.01, (n, m))))
    l = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, 0.01, (n, m))))
    v = np.exp(rng.normal(14, 1.2, (n, m)))
    vw = (h + l + c) / 3
    arr = np.stack([o, c, h, l, v, vw], axis=1)
    for j in rng.choice(m, 6, replace=False):                      # gaps (unobserved sessions)
        a = int(rng.integers(0, n - 20))
        arr[a:a + int(rng.integers(1, 15)), :, j] = np.nan
    elig = rng.random((n, m)) > 0.1
    for j in rng.choice(m, 4, replace=False):                      # ineligible stretches
        a = int(rng.integers(0, n - 60))
        elig[a:a + int(rng.integers(20, 60)), j] = False
    return arr, elig


def part_b():
    from desk.sleeves.quant_research import alphagen_np as A
    if not TORCH_PYTHON:
        return {"skipped": "TORCH_PYTHON not set"}
    rng = np.random.default_rng(20261016)
    per = 100
    cases, panels = [], []
    for k in range(max(1, N_EXPR // per)):
        arr, elig = synth_panel(rng)
        exprs = []
        while len(exprs) < per:
            e = rand_expr(rng)
            node = A.parse(e)
            if node.backtrack() > 100 or "$" not in e:
                continue
            exprs.append(e)
        panels.append((arr, elig, exprs))
        cases.append({"data": np.where(np.isfinite(arr), arr, None).tolist(), "elig": elig.tolist(), "exprs": exprs})
    vendor = os.path.join(SIXAI_X, "alphaqcm", "vendor")
    r = subprocess.run([TORCH_PYTHON, "-I", "-c", TORCH_SCRIPT, vendor], input=json.dumps({"cases": cases}),
                       capture_output=True, text=True, timeout=7200)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    native = json.loads(r.stdout.strip().splitlines()[-1])
    n, bad, errors, maxd, diffs, degenerate = 0, 0, 0, 0.0, [], 0
    A.F32 = np.float64                                   # (B) compares the operators' semantics in float64
    for (arr, elig, exprs), res in zip(panels, native):
        data = arr.astype(np.float64)
        for e, got in zip(exprs, res):
            n += 1
            node = A.parse(e)
            try:
                v = A.evaluate(node, data, 100, data.shape[0]).astype(np.float64, copy=True)
            except Exception as ex:
                if "error" in got:
                    errors += 1
                    continue
                bad += 1
                diffs.append({"expr": e, "port_error": type(ex).__name__})
                continue
            if "error" in got:
                bad += 1
                diffs.append({"expr": e, "native_error": got["error"]})
                continue
            v[~elig[100:]] = np.nan
            v[~np.isfinite(v)] = np.nan
            mine = A.normalize_by_day(v)
            want = np.array(got["v"], dtype=np.float64)
            with np.errstate(all="ignore"):
                span = np.nanmax(v, axis=1) - np.nanmin(v, axis=1)
                const = ~(span > 1e-12 * np.maximum(1.0, np.nanmax(np.abs(v), axis=1)))
            degenerate += int(const.sum())
            d = np.abs(mine.astype(np.float64) - want)
            d[const] = 0
            maxd = max(maxd, float(d.max()))
            if (d > TOL_B * np.maximum(1.0, np.abs(want))).any():
                bad += 1
                i, j = np.unravel_index(int(np.argmax(d)), d.shape)
                diffs.append({"expr": e, "row": int(i), "col": int(j), "port": float(mine[i, j]),
                              "native": float(want[i, j])})
    A.F32 = np.float32
    return {"expressions": n, "bad": bad, "both_error": errors, "max_abs_diff": maxd, "diffs": diffs[:5],
            "constant_rows_counted": degenerate, "torch_python": TORCH_PYTHON, "dtype": "float64"}


def run():
    pins = {k: sha(k) for k in PINS}
    a = part_a()
    b = part_b()
    cases = a["scores"] + a["selections"] + a["eligibility_cells"] + b.get("expressions", 0)
    nbad = a["score_bad"] + a["selection_bad"] + a["eligibility_bad"] + a["scored_set_bad"] + a["cadence_bad"] + \
        b.get("bad", 0)
    out = {"family": "quant_research", "sleeves": ["qr_alphaqcmiqcmfactorpolicyreconstructi"], "cases": cases,
           "identical": cases - nbad, "n_diffs": nbad, "native_outputs": a, "native_operators": b,
           "tolerance": f"(A) float32: |port - native| <= {TOL} x max(1, |native|), selections exact; (B) float64: "
                        f"<= {TOL_B} x max(1, |native|)",
           "source": {"archive": "quant-research-critical@0be4c57569e363d052bd23564cf0664697439927 research/"
                                 "2026-10-08-six-strategy-reconstruction/source.zip.parts", "members_sha256": pins},
           "method": "(A) the reconstruction's frozen native scores / eligibility / targets on its real panel vs the "
                     "port; (B) native torch operators (alphagen) vs alphagen_np on randomized grammar expressions",
           "not_in_this_comparison": ["execution (divergence 3)", "the live data provider (divergence 2)"]}
    write_receipt("qr_alphaqcm", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}))
    print(json.dumps(r["native_outputs"])[:1500])
    print(json.dumps(r["native_operators"])[:1500])
