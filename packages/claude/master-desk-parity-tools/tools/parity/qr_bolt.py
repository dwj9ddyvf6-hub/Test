"""qr_bolt: BOLT's R10 kernel as the source runs it vs desk/sleeves/quant_research/bolt.py's calls through the
vendored copies (desk/vendor/quant_research/r10/bolt/).

SOURCE: quant-research-backup@d170596b research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt:
code/transport_kernel.py (blob 6f38ffc3), code/admission.py (1b5a233d) and verification/TEST_CASES.json (2e6a20f6),
loaded from their blobs in a temporary directory (tools/parity/r10src.py).
  (A) the source's own recorded verification cases (finite dual witnesses, native clock / contract gates, physical
      net decisions): the vendored functions reproduce every recorded R10 output.
  (B) randomized kernel problems: two forward-normalised expiries of a lognormal martingale (random volatilities,
      strike ladders, spreads, quote noise; some boxes inconsistent on purpose), the crossing payoff at theta 0.5% /
      1% / 2% -> the source's quote_bounds vs the vendored one: bounds equal to 1e-12 or the same refusal.
  (C) randomized snapshots through the sleeve: SPXW chain rows around an event -> bolt.snapshot() (bracket, the
      put-call-parity forward, quotes_for, the vendored kernel) vs the same quotes bounded by the source kernel.
  (D) randomized physical admissions (support counts, net scenario increments, the paired LCB, gate statuses and bad
      domains) and native-gate rows: source vs vendored, identical statuses."""
import json
import math
import os
from datetime import date, datetime, time as dtime, timedelta

import numpy as np

from . import write_receipt
from .r10src import COMMIT, REPO, blob, source_tree

PATH = "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt/"
FILES = {"transport_kernel.py": "6f38ffc3e51d9dd30a5f11cb4d50831e0b74db7d",
         "admission.py": "1b5a233ddc5bb3ba5b64d5d7f37cb092be3f06a7"}
CASES_SHA = "2e6a20f64fb413a07ff4bfecd765c6d0a9addbb5"
N_KERNEL = int(os.environ.get("BOLT_PARITY_KERNEL", 1000))
N_SNAP = int(os.environ.get("BOLT_PARITY_SNAPSHOTS", 100))
N_ADMIT = int(os.environ.get("BOLT_PARITY_ADMISSIONS", 1000))


def _bounds(TK, x, y, qb, qa, th, mean=1.0):
    try:
        b = TK.quote_bounds(np.asarray(x), np.asarray(y), qb, qa, TK.crossing_payoff(np.asarray(x), np.asarray(y), th),
                            mean=mean)
        return ("ok", float(b.lower), float(b.upper))
    except Exception as e:                                      # the refusal is part of the decision
        return ("refused", type(e).__name__, str(e)[:160])


def _same(a, b, tol=1e-12):
    if a[0] != b[0]:
        return False
    if a[0] == "refused":
        return a[1:] == b[1:]
    return abs(a[1] - b[1]) <= tol and abs(a[2] - b[2]) <= tol


def _call(f, k, s):
    n = lambda v: 0.5 * (1 + math.erf(v / math.sqrt(2)))      # noqa: E731
    d1 = (math.log(f / k) + s * s / 2) / s
    return f * n(d1) - k * n(d1 - s)


def kernel_case(rng):
    """the sleeve's domain: strikes within +-10% of the forward, >= 0.5% apart (quotes_for's grid, <= 41)."""
    s1 = rng.uniform(0.01, 0.05)
    s2 = s1 * rng.uniform(1.05, 2.0) if rng.random() > 0.1 else s1 * rng.uniform(0.5, 1.0)   # sometimes not convex
    step = 0.01 if rng.random() < 0.7 else 0.005
    ks = np.arange(0.9, 1.1 + 1e-9, step)
    qs = []
    for s in (s1, s2):
        q = []
        for k in ks:
            c = _call(1.0, float(k), s)
            if c < 2e-4:
                continue
            half = c * rng.uniform(0.02, 0.10)
            noise = c * rng.normal(0, 0.01) if rng.random() < 0.2 else 0.0
            q.append((float(k), max(1e-6, c + noise - half), c + noise + half))
        qs.append(q)
    x = sorted({0.5, 2.0} | {k for k, _, _ in qs[0]})
    y = sorted({0.5, 2.0} | {k for k, _, _ in qs[1]})
    return x, y, qs[0], qs[1], float(rng.choice([0.005, 0.01, 0.02]))


def snapshot_rows(rng, event_day):
    """SPXW calls and puts for the expiries around `event_day` from one lognormal law per expiry."""
    spot = float(rng.uniform(3000, 7000))
    rows = []
    d = date.fromisoformat(event_day)
    exps = [d - timedelta(days=k) for k in (1, 2, 3)] + [d + timedelta(days=k) for k in (1, 2, 3)]
    for j, e in enumerate(sorted(exps)):
        if e.weekday() >= 5:
            continue
        s = rng.uniform(0.01, 0.03) * (1 + 0.15 * j)
        fwd = spot * (1 + rng.normal(0, 0.0005))
        step = float(rng.choice([5.0, 10.0, 25.0]))
        for k in np.arange(round(spot * 0.88 / step) * step, spot * 1.12, step):
            c = _call(fwd, float(k), s)
            p = c - fwd + float(k)
            for typ, px in (("call", c), ("put", p)):
                if px < 0.05:
                    continue
                half = max(0.05, px * rng.uniform(0.002, 0.05))
                rows.append({"root": "SPXW", "expiration": e.isoformat(), "type": typ, "strike": float(k),
                             "bid": round(px - half, 2), "ask": round(px + half, 2)})
    return rows, spot


def run():
    from desk.sleeves.quant_research import bolt as B
    from desk.vendor.quant_research.r10.bolt import admission as AD_port
    from desk.vendor.quant_research.r10.bolt import transport_kernel as TK_port
    vendored = {f: open(os.path.join(os.path.dirname(TK_port.__file__), f), "rb").read() for f in FILES}
    byte_exact = {f: vendored[f] == blob(sha) for f, sha in FILES.items()}
    out = {"family": "quant_research", "sleeves": [B.SID], "byte_exact_vendoring": byte_exact,
           "source": {"repo": REPO, "commit": COMMIT, "path": PATH, "files": FILES,
                      "test_cases": {"path": PATH + "verification/TEST_CASES.json", "blob_sha": CASES_SHA}}}
    diffs = []
    with source_tree({"code/" + f: s for f, s in FILES.items()}, prefix="qr_bolt_src_") as (tmp, load):
        import sys
        sys.path.insert(0, os.path.join(tmp, "code"))
        try:
            TK = load("code/transport_kernel.py", "bolt_src_transport_kernel")
            AD = load("code/admission.py", "bolt_src_admission")
        finally:
            sys.path.remove(os.path.join(tmp, "code"))
        # (A) the recorded verification cases
        rec = json.loads(blob(CASES_SHA))
        a = {"cases": 0, "identical": 0}
        for r in rec:
            fam, det = r["family"], r["detail"]
            if fam == "FINITE_DUAL_WITNESS":
                x, y = np.array(det["states"][0]), np.array(det["states"][1])
                qb = [tuple(q) for q in det["quotes"][0]]
                qa = [tuple(q) for q in det["quotes"][1]]
                scale = float(r["name"].split("/")[0])
                b = TK_port.quote_bounds(x, y, qb, qa, np.array(det["payoff"]), scale)
                ok = abs(b.lower - det["r10_bounds"][0]) <= 1e-9 and abs(b.upper - det["r10_bounds"][1]) <= 1e-9
            elif fam == "NATIVE_CLOCK_CONTRACT_GATE":
                ok = AD_port.native_gate(det["row"], "2026-10-09T19:45:00Z") == det["result"]
            elif fam == "PHYSICAL_NET_DECISION":
                st = "INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED"
                ok = (AD_port.physical_admission(det["net_portfolio_scenarios"], .001, 80, 40, 24, st) == det["decision"]
                      and AD_port.physical_admission(det["net_portfolio_scenarios"], .001, 0, 40, 24, st)
                      == det["no_physical_training"]
                      and AD_port.physical_admission(det["net_portfolio_scenarios"], .001, 80, 40, 24,
                                                     "NO_TRADE_NATIVE_CONTRACT") == det["missing_native"])
            else:
                continue                                        # harness-fault injections / anchor diagnostics
            a["cases"] += 1
            a["identical"] += bool(ok)
            if not ok:
                diffs.append({"part": "A", "family": fam, "name": r["name"]})
        out["recorded_cases"] = a
        # (B) randomized kernel problems
        rng = np.random.default_rng(20261016)
        b_st = {"cases": 0, "identical": 0, "refused": 0}
        for i in range(N_KERNEL):
            x, y, qb, qa, th = kernel_case(rng)
            s, p = _bounds(TK, x, y, qb, qa, th), _bounds(TK_port, x, y, qb, qa, th)
            b_st["cases"] += 1
            b_st["refused"] += s[0] == "refused"
            if _same(s, p):
                b_st["identical"] += 1
            else:
                diffs.append({"part": "B", "case": i, "source": s, "port": p})
        out["kernel"] = b_st
        # (C) snapshots through the sleeve
        c_st = {"cases": 0, "identical": 0, "indexes_with_bounds": 0, "no_bracket": 0}
        days = [d for d in (date(2027, 1, 4) + timedelta(days=k) for k in range(400)) if d.weekday() in (1, 2, 3)]
        for i in range(N_SNAP):
            ev_day = days[int(rng.integers(len(days)))].isoformat()
            rows, spot = snapshot_rows(rng, ev_day)
            ev = datetime.combine(date.fromisoformat(ev_day), dtime(14, 0), B.ET)
            snap_dt = ev - timedelta(days=7)
            got = B.snapshot({"SPX": rows}, {"SPX": spot}, ev, snap_dt)["SPX"]
            br = B.bracket(rows, "SPXW", ev, snap_dt)
            want = None
            if br:
                fb, fa = B.forward(rows, "SPXW", br[0]), B.forward(rows, "SPXW", br[1])
                qb, qa = B.quotes_for(rows, "SPXW", br[0], fb), B.quotes_for(rows, "SPXW", br[1], fa)
                if len(qb) >= 9 and len(qa) >= 9:                  # the sleeve's grid (divergence 3)
                    x, y = (list(g) for g in B.states(B.quoted(rows, "SPXW", br[0], fb),
                                                      B.quoted(rows, "SPXW", br[1], fa), fb, fa))
                    res = [_bounds(TK, x, y, qb, qa, th) for th in B.THETAS]
                    want = ({"blocked": True} if any(r[0] == "refused" for r in res)
                            else {th: (r[1], r[2]) for th, r in zip(B.THETAS, res)})
            c_st["cases"] += 1
            if want is None:
                c_st["no_bracket"] += 1
                ok = got is None
            elif want.get("blocked"):
                ok = isinstance(got, dict) and "blocked" in got
            else:
                c_st["indexes_with_bounds"] += 1
                ok = isinstance(got, dict) and all(abs(got[B._th(th)][0] - want[th][0]) <= 1e-12 and
                                                   abs(got[B._th(th)][1] - want[th][1]) <= 1e-12 for th in B.THETAS)
            c_st["identical"] += bool(ok)
            if not ok:
                diffs.append({"part": "C", "case": i, "event": ev_day})
        out["snapshots"] = c_st
        # (D) admissions and native gates
        d_st = {"cases": 0, "identical": 0}
        statuses = ["INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED", "NO_TRADE_NATIVE_CONTRACT", "NO_TRADE_STALE"]
        for i in range(N_ADMIT):
            n = int(rng.integers(0, 4))
            vals = [float(v) for v in rng.normal(0.006, 0.006, n)]
            if rng.random() < 0.05:
                vals.append(float("nan"))
            counts = [int(rng.integers(0, 160)) for _ in range(3)]
            if rng.random() < 0.05:
                counts[int(rng.integers(3))] = -1
            lcb = float(rng.normal(0.002, 0.004))
            st = statuses[int(rng.integers(len(statuses)))]
            margin = .005 if rng.random() > 0.05 else float(rng.choice([.004, .01, float("inf")]))
            s = AD.physical_admission(vals, lcb, *counts, st, margin=margin)
            p = AD_port.physical_admission(vals, lcb, *counts, st, margin=margin)
            d_st["cases"] += 1
            d_st["identical"] += s == p
            if s != p:
                diffs.append({"part": "D", "case": i, "source": s, "port": p})
        for r in rec:
            if r["family"] == "NATIVE_CLOCK_CONTRACT_GATE":
                row = dict(r["detail"]["row"])
                for _ in range(10):
                    k = list(row)[int(rng.integers(len(row)))]
                    mut = dict(row)
                    v = mut[k]
                    mut[k] = (v * float(rng.uniform(-1, 2)) if isinstance(v, (int, float)) and not isinstance(v, bool)
                              else (not v) if isinstance(v, bool) else str(v)[:-1] + "Z")
                    s = AD.native_gate(mut, "2026-10-09T19:45:00Z")
                    p = AD_port.native_gate(mut, "2026-10-09T19:45:00Z")
                    d_st["cases"] += 1
                    d_st["identical"] += s == p
                    if s != p:
                        diffs.append({"part": "D", "gate": k})
        out["admissions"] = d_st
    cases = sum(out[k]["cases"] for k in ("recorded_cases", "kernel", "snapshots", "admissions"))
    ident = sum(out[k]["identical"] for k in ("recorded_cases", "kernel", "snapshots", "admissions"))
    out.update(cases=cases, identical=ident, n_diffs=len(diffs), diffs=diffs[:50],
               method="the source's recorded R10 verification cases replayed through the vendored kernel; randomized "
                      "kernel problems, chain snapshots through bolt.snapshot() and admissions / gates: source vs port",
               not_in_this_comparison=["options feed (divergence 1)", "calendars (2)", "grid choice (3: the port's "
                                       "own; no source grid)", "event history (4)", "execution (5)"])
    write_receipt("qr_bolt", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}),
          json.dumps({k: r[k] for k in ("recorded_cases", "kernel", "snapshots", "admissions", "byte_exact_vendoring")}))
