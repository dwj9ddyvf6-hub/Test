"""qr_factor_books: the six-strategy reconstruction's AlphaMemo / QuantaAlpha model scores and its TopkDropout book vs
desk/sleeves/quant_research (scores.py, sixai.py, dropout_book.py).

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/source.zip.parts, extracted
(SIXAI_X; members sha256-pinned in the receipt).
  (A) scores: the reconstruction's frozen native daily signals (alphamemo/results/residual-signals.csv.gz,
      quantaalpha/results/rounds5-signals.csv.gz: factor_common.train_predict's LightGBM predictions, every eligible
      name and session 2021-01-04..2026-10-07) on its real panel (data/panel.npz). PORT: on sampled sessions, the
      production path -- the trailing 320-session window of the panel's split-adjusted open / close / high / low /
      volume / vwap and validity, common.eligibility x the roster's equity-candidate flags, scores.compute() (the
      vendored sspm operators / QuantaAlpha parser and function library, the reconstruction's normalisation, the
      LightGBM text models). Compared per name (|port - native| <= 1e-9 relative; the CSV keeps 12 digits) and the
      scored sets exactly. A session with a differing name is recomputed over the panel's whole history (the native
      evaluation's span): identical there -> counted as the named divergence `window_start_float` (pandas' online
      rolling sums / variances carry ~1e-13 accumulation differences from where the series starts, enough to flip a
      LightGBM split or a cross-sectional rank tie); a session still differing is replayed under the source's own
      runtime (SOURCE_RUNTIME_PYTHON: an interpreter with the reconstruction's pandas 2.2 / numpy 2.3.5, which
      requirements-replay.txt pins; the desk runs pandas 3 / numpy 2.5): the production window's scores identical
      there -> counted as the named divergence `runtime_numerics` (the two runtimes' rolling second moments differ in
      the last bits, enough to move a cross-sectional rank by a position); anything else stays an unexplained diff.
  (B) the book: shared/portfolio.py backtest(mode='dropout') (with shared/dropout.py), run with `python3 -I` in its
      own process over synthetic panels and score streams (top-k / n_drop / min-hold / cost pairs of the registered
      runs, a participation cap that binds) -> its per-session trades. PORT: sixai.dropout_plan replayed session by
      session from the same holdings, cash, prices (bid = ask = the session's open), 20-session dollar volume and
      eligibility; every name's trade compared (|diff| <= 1e-9 x max(1, shares))."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from . import write_receipt

SIXAI_X = os.environ.get("SIXAI_X", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/"
                                    "sixai/x")
MEMBERS = ["data/panel.npz", "alphamemo/results/residual-signals.csv.gz", "quantaalpha/results/rounds5-signals.csv.gz",
           "shared/portfolio.py", "shared/dropout.py"]
N_AM = int(os.environ.get("FACTOR_PARITY_AM_DATES", 40))
N_QA = int(os.environ.get("FACTOR_PARITY_QA_DATES", 12))
N_BOOK = int(os.environ.get("FACTOR_PARITY_BOOK_SEEDS", 10))


def sha(rel):
    return hashlib.sha256(open(os.path.join(SIXAI_X, rel), "rb").read()).hexdigest()


SOURCE_RUNTIME = os.environ.get("SOURCE_RUNTIME_PYTHON")
RUNTIME_SRC = r"""
import json, sys
import numpy as np, pandas as pd
ROOT, X, name, i, n_rows = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, ROOT)
from desk.sleeves.quant_research import common as C, scores as SC, sixai as S
z = np.load(X + "/data/panel.npz", allow_pickle=False, mmap_mode="r")
lo = i - n_rows + 1
P = {k: np.array(z[k][lo:i + 1], dtype=float) for k in ("open", "close", "high", "low", "volume", "vwap")}
P["valid"] = np.array(z["valid"][lo:i + 1])
P["dates"] = np.array(z["dates"])[lo:i + 1]
P["eligible"] = C.eligibility(P["close"], P["volume"], P["valid"]) & S.CANDIDATE[None, :]
print(json.dumps({"runtime": {"pandas": pd.__version__, "numpy": np.__version__}, "scores": SC.compute(P, name)}))
"""


def source_runtime_scores(name, i):
    """the production window's scores computed by this port under the source's runtime (None when not configured)."""
    if not SOURCE_RUNTIME:
        return None
    from desk.sleeves.quant_research import sixai as S
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([SOURCE_RUNTIME, "-I", "-W", "ignore", "-c", RUNTIME_SRC, root, SIXAI_X, name, str(i),
                        str(S.N_ROWS)], capture_output=True, text=True, timeout=3600, env=env)
    if r.returncode:
        raise RuntimeError("source-runtime replay failed: " + r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------------------------------------- (A) model scores
def part_a():
    from desk.sleeves.quant_research import common as C
    from desk.sleeves.quant_research import scores as SC
    from desk.sleeves.quant_research import sixai as S
    z = np.load(os.path.join(SIXAI_X, "data/panel.npz"), allow_pickle=False, mmap_mode="r")
    dates = np.array(z["dates"])
    assert list(z["symbols"]) == list(S.SYMBOLS)
    out = {}
    rng = np.random.default_rng(20261016)
    for name, path, n in (("alphamemo", "alphamemo/results/residual-signals.csv.gz", N_AM),
                          ("quantaalpha", "quantaalpha/results/rounds5-signals.csv.gz", N_QA)):
        sig = pd.read_csv(os.path.join(SIXAI_X, path), float_precision="round_trip")
        picks = sorted(rng.choice(sorted(sig.date.unique()), n, replace=False))
        st = {"dates": 0, "scores": 0, "bad": 0, "set_bad": 0, "eligibility_bad": 0, "max_rel": 0.0, "diffs": [],
              "counted": {"window_start_float": 0, "runtime_numerics": 0}}
        by = {d: g.set_index("symbol").score for d, g in sig[sig.date.isin(picks)].groupby("date")}
        for d in picks:
            i = int(np.flatnonzero(dates == d)[0])
            rows = slice(i - S.N_ROWS + 1, i + 1)
            P = {k: np.array(z[k][rows], dtype=float) for k in ("open", "close", "high", "low", "volume", "vwap")}
            P["valid"] = np.array(z["valid"][rows])
            P["dates"] = dates[rows]
            P["eligible"] = C.eligibility(P["close"], P["volume"], P["valid"]) & S.CANDIDATE[None, :]
            st["eligibility_bad"] += int((P["eligible"][-1] != np.array(z["eligible"][i])).sum())
            got = pd.Series(SC.compute(P, name))
            want = by[d]
            common = want.index.intersection(got.index)
            rel = np.abs(got[common].values - want[common].values) / np.maximum(1e-12, np.abs(want[common].values))
            st["dates"] += 1
            st["scores"] += len(want)
            nb = int((rel > 1e-9).sum())
            sd = len(want.index.symmetric_difference(got.index))
            if nb or sd:                                      # recompute over the native evaluation's whole span
                Q = {k: np.array(z[k][:i + 1], dtype=float) for k in ("open", "close", "high", "low", "volume", "vwap")}
                Q["valid"] = np.array(z["valid"][:i + 1])
                Q["dates"] = dates[:i + 1]
                Q["eligible"] = C.eligibility(Q["close"], Q["volume"], Q["valid"]) & S.CANDIDATE[None, :]
                full = pd.Series(SC.compute(Q, name))
                fc = want.index.intersection(full.index)
                frel = np.abs(full[fc].values - want[fc].values) / np.maximum(1e-12, np.abs(want[fc].values))
                if int((frel > 1e-9).sum()) == 0 and not len(want.index.symmetric_difference(full.index)):
                    st["counted"]["window_start_float"] += nb + sd
                    st["diffs"].append({"date": d, "window_names": nb, "set_diff": sd, "full_history": "identical"})
                    nb = sd = 0
                    rel = frel
                else:
                    rt = source_runtime_scores(name, i)
                    if rt is not None:
                        g2 = pd.Series(rt["scores"])
                        c2 = want.index.intersection(g2.index)
                        r2 = np.abs(g2[c2].values - want[c2].values) / np.maximum(1e-12, np.abs(want[c2].values))
                        if int((r2 > 1e-9).sum()) == 0 and not len(want.index.symmetric_difference(g2.index)):
                            st["counted"]["runtime_numerics"] += nb + sd
                            st["runtime"] = rt["runtime"]
                            st["diffs"].append({"date": d, "window_names": nb, "set_diff": sd,
                                                "source_runtime": "identical", "max_rel_source_runtime": float(
                                                    r2.max()) if len(r2) else 0.0})
                            nb = sd = 0
                            rel = r2
            st["bad"] += nb
            st["set_bad"] += sd
            st["max_rel"] = max(st["max_rel"], float(rel.max()) if len(rel) else 0.0)
            if nb or sd:
                st["diffs"].append({"date": d, "bad": nb, "set_diff": sd})
        out[name] = st
    return out


# ------------------------------------------------------------------------------------------- (B) the book
SRC = r'''
import json, sys
TREE = sys.argv[1]
sys.path.insert(0, TREE)
import numpy as np, pandas as pd
from portfolio import backtest
out = []
for c in json.load(sys.stdin)["cases"]:
    prices = {k: np.array(v, dtype=float) for k, v in c["prices"].items() if k not in ("dates", "symbols", "eligible")}
    prices["dates"] = np.array(c["prices"]["dates"]); prices["symbols"] = np.array(c["prices"]["symbols"])
    prices["eligible"] = np.array(c["prices"]["eligible"], dtype=bool)
    frame = pd.DataFrame(c["signals"], columns=["date", "symbol", "score"])
    ledger, trades, metrics = backtest(prices, frame, start=c["start"], mode="dropout", topk=c["topk"],
                                       n_drop=c["n_drop"], min_hold=c["min_hold"], risk_degree=c["risk"],
                                       buy_bps=c["buy"], sell_bps=c["sell"])
    out.append({"trades": trades[["date", "symbol", "quantity_delta"]].values.tolist() if len(trades) else [],
                "cash": ledger[["date", "cash"]].values.tolist()})
print(json.dumps(out))
'''


def book_case(rng):
    n, m = 140, int(rng.integers(12, 30))
    syms = [f"S{j:02d}" for j in range(m)]
    days = [str(d.date()) for d in pd.bdate_range("2024-01-02", periods=n)]
    r = rng.normal(0.0004, rng.uniform(0.01, 0.03, m), (n, m))
    close = rng.uniform(5, 200, m) * np.exp(np.cumsum(r, axis=0))
    opn = np.r_[close[:1], close[:-1]] * np.exp(rng.normal(0, 0.004, (n, m)))
    vol = np.exp(rng.normal(np.log(rng.uniform(2e4, 3e6, m)), 0.5, (n, m)))
    gaps = rng.random((n, m)) < 0.01                                     # a missing open now and then
    opn[gaps] = np.nan
    elig = rng.random((n, m)) > 0.08
    sc = rng.normal(0, 1, (n, m)) + np.cumsum(rng.normal(0, 0.3, (n, m)), axis=0) * 0.2
    sig = [[days[i], syms[j], float(sc[i, j])] for i in range(n) for j in range(m) if elig[i, j]]
    topk, n_drop = int(rng.integers(3, 8)), int(rng.integers(1, 3))
    min_hold = int(rng.choice([1, 5]))
    buy, sell = [(0.0, 5.0), (5.0, 15.0), (15.0, 15.0), (10.0, 10.0)][int(rng.integers(0, 4))]
    prices = {"dates": days, "symbols": syms, "open": opn.tolist(), "close": close.tolist(), "volume": vol.tolist(),
              "all_open": opn.tolist(), "all_close": close.tolist(), "eligible": elig.tolist()}
    prices = json.loads(json.dumps(prices).replace("NaN", "null"))
    return {"prices": prices, "signals": sig, "start": days[25], "topk": topk, "n_drop": n_drop,
            "min_hold": min_hold, "risk": 0.95, "buy": buy, "sell": sell}


def replay(case, src):
    from desk.sleeves.quant_research import sixai as S
    P = case["prices"]
    dates = P["dates"]
    syms = P["symbols"]
    N = len(syms)
    opn = np.array([[np.nan if x is None else x for x in row] for row in P["all_open"]], dtype=float)
    close = np.array(P["close"], dtype=float)
    vol = np.array(P["volume"], dtype=float)
    elig = np.array(P["eligible"], dtype=bool)
    score = {}
    for d, s, v in case["signals"]:
        score.setdefault(d, {})[s] = v
    trades = {}
    for d, s, q in src["trades"]:
        trades.setdefault(d, {})[s] = float(q)
    cash_after = {d: float(c) for d, c in src["cash"]}
    i0 = dates.index(case["start"])
    q = np.zeros(N)
    entered = np.full(N, -10 ** 9)
    cash = 100000.0
    n, bad, diffs = 0, 0, []
    for i in range(i0, len(dates)):
        d_prev = dates[i - 1]
        vec = np.full(N, np.nan)
        for s, v in (score.get(d_prev) or {}).items():
            vec[syms.index(s)] = v
        p = opn[i]
        dv = close * vol
        win = dv[i - 20:i]
        adv = np.where(np.isfinite(win).all(axis=0), win.mean(axis=0), np.nan) if i >= 20 else np.full(N, np.nan)
        desired, sel = S.dropout_plan(syms, vec, elig[i - 1], q, i - entered, p, p, cash, adv, case["topk"],
                                      case["n_drop"], case["min_hold"], case["risk"], case["buy"], case["sell"])
        delta = desired - q
        want = np.zeros(N)
        for s, x in (trades.get(dates[i]) or {}).items():
            want[syms.index(s)] = x
        n += 1
        tol = 1e-9 * np.maximum(1.0, np.abs(want))
        if (np.abs(delta - want) > tol).any():
            bad += 1
            if len(diffs) < 3:
                j = int(np.argmax(np.abs(delta - want)))
                diffs.append({"date": dates[i], "symbol": syms[j], "port": float(delta[j]), "source": float(want[j])})
        # advance the state with the source's own trades (so one difference does not cascade)
        for j in np.flatnonzero(np.abs(want) > 1e-12):
            if abs(q[j]) < 1e-12 and abs(q[j] + want[j]) > 1e-12:
                entered[j] = i
        q = q + want
        cash = cash_after.get(dates[i], cash)
    return n, bad, diffs


def part_b():
    tree = tempfile.mkdtemp(prefix="qr_book_src_")
    try:
        for rel in ("shared/portfolio.py", "shared/dropout.py"):
            shutil.copyfile(os.path.join(SIXAI_X, rel), os.path.join(tree, os.path.basename(rel)))
        rng = np.random.default_rng(7)
        cases = [book_case(rng) for _ in range(N_BOOK)]
        r = subprocess.run([sys.executable, "-I", "-c", SRC, tree], input=json.dumps({"cases": cases}),
                           capture_output=True, text=True, timeout=7200, cwd=tree)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        src = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    n = bad = trades = 0
    diffs = []
    for c, s in zip(cases, src):
        a, b, d = replay(c, s)
        n += a
        bad += b
        trades += len(s["trades"])
        diffs += d
    return {"sessions": n, "bad": bad, "source_trades": trades, "diffs": diffs[:5]}


def run():
    pins = {k: sha(k) for k in MEMBERS}
    a = part_a()
    b = part_b()
    cases = sum(v["scores"] for v in a.values()) + b["sessions"]
    nbad = sum(v["bad"] + v["set_bad"] for v in a.values()) + b["bad"]
    out = {"family": "quant_research", "sleeves": ["qr_alphamemosourcepreservingfactorrecon",
                                                   "qr_quantaalphadeterministicproposalreco",
                                                   "qr_kronosbasezeroshotustransfer"],
           "cases": cases, "identical": cases - nbad, "n_diffs": nbad, "scores": a, "book": b,
           "source": {"archive": "quant-research-critical@0be4c57569e363d052bd23564cf0664697439927 research/"
                                 "2026-10-08-six-strategy-reconstruction/source.zip.parts", "members_sha256": pins},
           "method": "(A) the frozen native signals on the real panel vs the port's production scoring of the "
                     "trailing window; (B) shared/portfolio.backtest(dropout) (own process, -I) vs dropout_plan "
                     "replayed session by session",
           "not_in_this_comparison": ["execution timing and live quotes (named divergences)",
                                      "Kronos forecasts (tools/parity/qr_kronos.py)"]}
    write_receipt("qr_factor_books", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}))
    print(json.dumps(r["scores"])[:1500])
    print(json.dumps(r["book"])[:1500])
