"""qr_r10_kernels: the R10 kernel rows -- CER, CQR, TCFT, CARM, AIRT, CRD -- each sleeve's decision layer on its
vendored kernel vs the archive's own kernel loaded from its pinned blob.

SOURCE: quant-research-backup@d170596b research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/<lane>/
(the blob shas below, read from R10_BLOBS and checked against their sha), with the lanes' own verification:
tcft/verification/TEST_CASES.json (the 304 recorded campaign cases: inputs and R10 outputs) replayed through the
vendored TCFT kernel, and crd/repair/test_repairs.py (the 19 owner tests, with before.py, the pinned history copies
and TEST_PLAN.json) executed against the vendored crd_r10.py.
PORT: desk/sleeves/quant_research/{cer,cqr,tcft,carm,airt,crd}.py over desk/vendor/quant_research/r10/.
Compared: byte-exact vendoring; per lane at least 1000 randomized cases of the sleeve's admission function against
the playbook's rule composed on the SOURCE module (admitted flag and reason code exactly, details to 1e-12); AIRT's
sizing, capacity and exit rules and CRD's exit rule as direct source-vs-vendored calls; CRD's plan (the gate, the
domain restriction, the SLSQP optimiser and the whole-share rounding) on randomized accounts."""
import contextlib
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import shutil
from datetime import datetime, timedelta, timezone

import numpy as np

from . import write_receipt
from .r10src import blob, source_tree

N = int(os.environ.get("R10_PARITY_CASES", 1000))
N_PLAN = int(os.environ.get("R10_PARITY_PLANS", 200))
LANE = "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/"
FILES = {   # vendored path (desk/vendor/quant_research/r10/...) -> (archive path under LANE, blob sha)
    "airt/code/coordinator.py": ("airt/code/coordinator.py", "f49a25951d07597b08681d07ecd4e51f8d08794d"),
    "airt/code/vendor/airt_r1.py": ("airt/code/vendor/airt_r1.py", "6fb518d1d6975351ccb5af4d652750af37a5108e"),
    "carm/code/reference_kernel.py": ("carm/code/reference_kernel.py", "3a482c62bc79d92aac0d24bff1017f33d75cb11e"),
    "cer/reference_kernel_r10.py": ("cer/reference_kernel_r10.py", "c418bd076c972f986a3571cae2b1ff2348e86d39"),
    "cqr/queue_delta_r10.py": ("cqr/queue_delta_r10.py", "d5bd3f351158be899b1e9c0c07c72da8c76df76a"),
    "crd/crd_r10.py": ("crd/repair/crd_r10.py", "4d5abbd02788d5370e597e6f93bf1375fd8085e5"),
    "tcft/code/execution.py": ("tcft/code/execution.py", "ef57f5e848be10ac2957a9ee3227fa54ad5b95b0"),
    "tcft/code/kernel.py": ("tcft/code/kernel.py", "df9b493887c0be116ab3b9c7fddb4dbff706d9e7"),
}
TCFT_CASES = "8e55ee6b98d1cab39c9595fa1bba4ad62e0b92f7"
CRD_TESTS = {"repair/test_repairs.py": "12913d95fb14b9c426e3a81442cb212aced7de8b",
             "repair/before.py": "4b0d570243d91b8865211b5d71137dbcbe484f84",
             "repair/history/pre_final_id_domain/crd_r10.py": "b4e76bdc0e3327645a3ac68a0019747ea80652df",
             "repair/history/pre_result_alias/crd_r10.py": "9112760c311003e2494e9323aea378ca821e4165",
             "TEST_PLAN.json": "6ac7a7150172601d732b94dd28927e5094d75bf7"}
CRD_RECORDED = "e9c5b7beec58580b1c531bcec6808ce9fc3c5fe1"
UTC = timezone.utc


def vendored_bytes(rel):
    from desk.vendor.quant_research import r10
    return open(os.path.join(os.path.dirname(r10.__file__), rel), "rb").read()


def same(a, b, tol=1e-12):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            return False
        return (math.isnan(a) and math.isnan(b)) or a == b or abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


class Tally:
    def __init__(self):
        self.parts = {}
        self.diffs = []
        self.outcomes = {}

    def add(self, part, ok, detail=None):
        p = self.parts.setdefault(part, {"cases": 0, "identical": 0})
        p["cases"] += 1
        p["identical"] += bool(ok)
        if detail and "source" in detail and isinstance(detail["source"], (list, tuple)):
            key = str(detail["source"][1] if len(detail["source"]) > 1 else detail["source"][0])
            key = key.split(":")[0][:40] if key.startswith(("ABSTAIN", "INVALID")) else key[:40]
            c = self.outcomes.setdefault(part, {})
            c[key] = c.get(key, 0) + 1
        if not ok and len(self.diffs) < 60:
            self.diffs.append(dict(part=part, **(detail or {})))


# ------------------------------------------------------------------------------------------------------------- CER
def cer_records(rng, prior, cutoff, required):
    recs = []
    span = (cutoff - prior).total_seconds() / 3600
    for k in required:
        kind = rng.choice(["old", "new", "none"], p=[0.45, 0.5, 0.05])
        for j in range(int(rng.integers(1, 3)) + int(rng.random() < 0.2)):
            if kind == "old" or j > 0:
                pub = prior - timedelta(hours=float(rng.uniform(12, 72))) if kind == "old" else \
                    prior + timedelta(hours=float(rng.uniform(-72, span)))
            elif kind == "new":
                pub = prior + timedelta(hours=float(rng.uniform(0.01, span - 11.5)))
            else:
                pub = cutoff + timedelta(hours=float(rng.uniform(1, 48)))
            rec = pub + timedelta(minutes=float(rng.uniform(0, 600)) if j else float(rng.uniform(0, 300)))
            ext = rec + timedelta(minutes=float(rng.uniform(0, 60)))
            ver = ext + timedelta(minutes=float(rng.uniform(0, 60)))
            eff = pub - timedelta(days=float(rng.uniform(0, 3))) if rng.random() < 0.9 else cutoff + timedelta(days=1)
            until = None if rng.random() < 0.8 else eff + timedelta(days=float(rng.uniform(0.5, 20)))
            recs.append({"project_id": "P1" if rng.random() < 0.95 else "P2", "predicate_id": k,
                         "origin_family": str(rng.choice(["registry", "utility", "press"])), "body_sha256": "b" * 64,
                         "state": "TRUE" if j == 0 or rng.random() < 0.85 else str(rng.choice(["FALSE", "UNKNOWN"])),
                         "published": pub.isoformat(), "received": rec.isoformat(), "extracted": ext.isoformat(),
                         "verified": ver.isoformat(), "effective_from": eff.isoformat(),
                         "effective_until": until.isoformat() if until else None})
    return recs


def history(rng, scale):
    n = int(rng.integers(0, int(scale * 1.5) + 1))
    return [{"issuer": f"I{int(rng.integers(0, 60))}", "group": f"G{int(rng.integers(0, 16))}",
             "exit_session": f"20{int(rng.integers(20, 26))}-{int(rng.integers(1, 13)):02d}-15", "label": 0.0}
            for _ in range(n)]


def cer_source(Ks, project, recs, prior, cutoff, hist):
    from desk.sleeves.quant_research import r10 as R
    try:
        proofs = tuple(Ks.Proof(p["project_id"], p["predicate_id"], p["origin_family"], p["body_sha256"],
                                Ks.State(p["state"]), *(datetime.fromisoformat(p[k]) for k in
                                                        ("published", "received", "extracted", "verified",
                                                         "effective_from")),
                                datetime.fromisoformat(p["effective_until"]) if p.get("effective_until") else None)
                       for p in recs)
        g = Ks.Graph(project["project_id"], tuple(project["required"]), datetime.fromisoformat(project["frozen_at"]),
                     project["contract_sha256"])
        if not Ks.closure(g, proofs, prior, cutoff):
            return False, "NO_CLOSURE"
        after = Ks.Interval(*project["after"]) if project.get("after") else None
        before = Ks.Interval(*project["before"]) if project.get("before") else None
        screen = Ks.robust_conversion_screen(after, before, project["equity_value"])
    except (ValueError, KeyError, TypeError):
        return False, "INVALID_INPUT"
    if screen is None or screen <= 0:
        return False, "UNSUPPORTED_OR_NONPOSITIVE_ECONOMICS"
    sup = R.support(hist)
    if sup["episodes"] < 100 or sup["issuers"] < 40 or sup["groups"] < 10 or sup["months"] < 36:
        return False, "INSUFFICIENT_SUPPORT"
    f = project.get("forecast_net")
    if f is None or f <= 0.005:
        return False, "FORECAST_BELOW_BUFFER"
    return True, "ADMITTED"


def lane_cer(Ks, T, rng):
    from desk.sleeves.quant_research import cer
    base = datetime(2027, 1, 4, 21, 15, tzinfo=UTC)
    for i in range(N):
        prior = base + timedelta(days=int(rng.integers(0, 30)))
        cutoff = prior + timedelta(days=int(rng.integers(1, 6)))
        prior = prior.replace(hour=21, minute=15)
        req = [f"p{k}" for k in range(int(rng.integers(1, 4)))]
        recs = cer_records(rng, prior, cutoff, req)
        lo = float(rng.uniform(-5e6, 5e7))
        project = {"project_id": "P1", "required": req, "contract_sha256": "c" * 64,
                   "frozen_at": (prior - timedelta(days=float(rng.uniform(-0.5, 10)))).isoformat(),
                   "after": [lo, lo + float(rng.uniform(0, 2e7))] if rng.random() < 0.9 else None,
                   "before": [0.0, float(rng.uniform(0, 2e7))] if rng.random() < 0.9 else None,
                   "equity_value": float(rng.uniform(1e8, 5e9)), "forecast_net": float(rng.uniform(-0.01, 0.03))}
        hist = history(rng, float(rng.choice([60, 150])))
        try:
            proofs = cer.proofs_of({"proofs": recs})
            ok, why, _ = cer.evaluate(project, proofs, prior, cutoff, hist)
        except (ValueError, KeyError, TypeError):
            ok, why = False, "INVALID_INPUT"
        want = cer_source(Ks, project, recs, prior, cutoff, hist)
        T.add("cer", (ok, why) == want, {"case": i, "port": [ok, why], "source": list(want)})


# ------------------------------------------------------------------------------------------------------------- CQR
def cqr_orders(rng, n, r):
    return [{"name": f"o{k}", "quantity": float(rng.integers(1, 100)), "contribution_usd_per_unit":
             float(rng.uniform(-5, 20)), "resource_per_unit": [float(rng.uniform(0, 3)) for _ in range(r)],
             "mandatory": m, "shortfall_penalty_usd_per_unit": (float(rng.uniform(0, 30)) if m else None)
             if rng.random() > 0.03 else float(rng.uniform(0, 30))}
            for k, m in ((k, bool(rng.random() < 0.2)) for k in range(n))]


def cqr_source(Ks, packet, hist):
    from desk.sleeves.quant_research import r10 as R

    def orders(rows):
        return [Ks.Order(r["name"], r["quantity"], r["contribution_usd_per_unit"], tuple(r["resource_per_unit"]),
                         bool(r["mandatory"]), r.get("shortfall_penalty_usd_per_unit")) for r in rows]
    try:
        d = Ks.paired_delta(orders(packet["before"]), orders(packet["after"]), packet["capacity"],
                            packet.get("settlement_usd", 0.0))
    except (ValueError, RuntimeError, KeyError, TypeError):
        return False, "UNSUPPORTED_QUEUE", None
    rel = d["delta_usd"] / float(packet["market_value"])
    if not rel > 0:
        return False, "NONPOSITIVE_REVALUATION", d["delta_usd"]
    sup = R.support(hist)
    if sup["episodes"] < 100 or sup["issuers"] < 20 or sup["months"] < 24 or packet["oof_calibration_clusters"] < 30:
        return False, "INSUFFICIENT_SUPPORT", None
    f = packet.get("forecast_excess")
    if f is None or f <= 2 * max(0.0015, packet["side_cost"]) + 0.005:
        return False, "BELOW_COST_BUFFER", None
    return True, "ADMITTED", d["delta_usd"]


def lane_cqr(Ks, T, rng):
    from desk.sleeves.quant_research import cqr
    for i in range(N):
        r = int(rng.integers(1, 3))
        before = cqr_orders(rng, int(rng.integers(1, 4)), r)
        after = before + [dict(o, name="award") for o in cqr_orders(rng, 1, r)]
        packet = {"before": before, "after": after, "capacity": [float(rng.uniform(10, 200)) for _ in range(r)],
                  "settlement_usd": float(rng.uniform(-50, 200)), "market_value": float(rng.uniform(1e3, 1e5)),
                  "oof_calibration_clusters": int(rng.integers(20, 40)), "side_cost": float(rng.uniform(0, 0.003)),
                  "forecast_excess": float(rng.uniform(-0.01, 0.03))}
        hist = history(rng, float(rng.choice([60, 150])))
        ok, why, det = cqr.evaluate(packet, hist)
        want = cqr_source(Ks, packet, hist)
        good = (ok, why) == want[:2] and (want[2] is None or same(det.get("delta_usd"), want[2]))
        T.add("cqr", good, {"case": i, "port": [ok, why], "source": list(want[:2])})


# ------------------------------------------------------------------------------------------------------------ TCFT
NOW = "2026-10-09T18:00:00Z"
TARGET = {"first_received": "2026-10-09T16:00:00Z", "ingested": "2026-10-09T16:00:01Z", "ready": "2026-10-09T16:00:02Z",
          "kind": "ORIGINAL_INDEX_TARGET", "owner_id": "FUND", "security_id": "PERM", "revision_id": "v1",
          "source_sha256": "a" * 64, "allowances_complete": True, "announcement_time": "2026-10-09T15:59:00Z",
          "implementation_close": "2026-12-11T21:00:00Z", "effective_open": "2026-12-14T14:30:00Z"}
TARGET_CHANGES = [{}, {}, {}, {}, {}, {}, {"first_received": "2026-10-10T00:00:00Z"},
                  {"ready": "2026-10-10T00:00:00Z"}, {"kind": "CURRENT_HOLDINGS"}, {"allowances_complete": False},
                  {"allowances_complete": "True"}]


def tcft_lots(rng):
    out = []
    for kind in ("SUPPLY", "DEMAND"):
        for j in range(int(rng.integers(1, 4))):
            out.append({"lot_id": f"{kind}{j}", "owner_id": str(int(rng.integers(0, 4))), "security_id": "SEC",
                        "kind": kind, "shares": float(rng.integers(1, 51) * rng.choice([1, 1000])),
                        "slot": int(rng.integers(0, 10)), "available_at": "2026-10-09T17:00:00Z",
                        "measurement": "MODEL_ADJUSTMENT", "source_sha256": "a" * 64})
    return out


def tcft_source(Ks, Xs, ev, cutoff):
    g = Xs.target_gate(ev.get("target") or {}, cutoff)
    if g != "INPUT_SCHEMA_VALID_NOT_TRADE_AUTHORIZATION":
        return False, g
    try:
        scen = tuple(Ks.Scenario(sc["scenario_id"], tuple(
            Ks.Lot(l["lot_id"], l["owner_id"], l["security_id"], l["kind"], l["shares"], int(l["slot"]),
                   l["available_at"], l["measurement"], l["source_sha256"]) for l in sc["lots"]),
            sc["model_allowances_complete"]) for sc in ev["scenarios"])
        env = Ks.finite_envelope(scen, cutoff, int(ev.get("max_carry_slots", 5)))
    except (ValueError, ArithmeticError, KeyError, TypeError):
        return False, "INVALID_GRAPH"
    if env["status"] != "MODEL_ENVELOPE_COMPUTED":
        return False, env["status"]
    sec = (env["securities"] or {}).get(ev["security_id"])
    if not sec or not sec["structural_candidate"]:
        return False, "NO_STRUCTURAL_GAP"
    lo, hi = sec["time_cut_gap_lower_shares"], sec["time_cut_gap_upper_shares"]
    if float(ev["price"]) * lo / float(ev["adv60_dollars"]) < 0.1 or (hi - lo) / hi > 0.5:
        return False, "GAP_TOO_SMALL_OR_WIDE"
    sup = ev["support"]
    if sup["clusters"] < 300 or sup["securities"] < 60 or sup["family_calibration"] < 30 or sup["years"] < 5:
        return False, "INSUFFICIENT_SUPPORT"
    if float(ev["net_lcb_bp"]) < 20 or float(ev["paired_base_lcb"]) <= 0:
        return False, "NET_OR_PAIRED_BOUND"
    return True, "ADMITTED"


def lane_tcft(Ks, Xs, T, rng):
    from desk.sleeves.quant_research import tcft
    for i in range(N):
        ev = {"target": dict(TARGET, **TARGET_CHANGES[int(rng.integers(len(TARGET_CHANGES)))]),
              "scenarios": [{"scenario_id": f"s{k}", "lots": tcft_lots(rng),
                             "model_allowances_complete": bool(rng.random() < 0.95)}
                            for k in range(int(rng.integers(1, 3)))],
              "security_id": "SEC", "max_carry_slots": int(rng.choice([0, 1, 3, 5])),
              "price": float(rng.uniform(10, 200)), "adv60_dollars": float(10 ** rng.uniform(2, 6)),
              "support": {"clusters": float(rng.choice([250, 400, 400, 400])),
                          "securities": float(rng.choice([50, 80, 80, 80])),
                          "family_calibration": float(rng.choice([20, 40, 40, 40])),
                          "years": float(rng.choice([4, 6, 6, 6]))},
              "net_lcb_bp": float(rng.uniform(0, 40)), "paired_base_lcb": float(rng.uniform(-0.01, 0.02))}
        ok, why, _ = tcft.evaluate(ev, NOW)
        want = tcft_source(Ks, Xs, ev, NOW)
        T.add("tcft", (ok, why) == want, {"case": i, "port": [ok, why], "source": list(want)})


def tcft_recorded(K, X, T):
    """the archive's recorded campaign (TEST_CASES.json) replayed through the vendored kernel."""
    rows = json.loads(blob(TCFT_CASES))
    sha = "a" * 64

    def lot(i, owner, kind, shares, slot):
        return K.Lot(i, owner, "SEC", kind, shares, slot, "2026-10-09T17:00:00Z", "MODEL_ADJUSTMENT", sha)
    rng = random.Random(20261009)                  # the campaign's own generator (carry is drawn, not recorded)
    mincut = []
    for case in range(120):
        lots = tuple(lot(f"{kind}{j}", str(rng.randrange(4)), kind,
                         rng.randrange(1, 51) * rng.choice([1e-15, .001, 1, 1e15]), rng.randrange(10))
                     for kind in ["SUPPLY", "DEMAND"] for j in range(3))
        mincut.append((lots, rng.choice([0, 1, 3, 5])))
    flags = {"False": False, "True": True, "'False'": "False", "'True'": "True", "0": 0, "1": 1, "None": None,
             "[]": []}
    scale_i = 0
    k_mincut = 0
    for r in rows:
        fam, d = r["family"], r["detail"]
        if fam == "BOOLEAN_AND_SCALE" and "flag" in d:
            try:
                got = K.cancellation((lot("d", "A", "DEMAND", 100, 1), lot("s", "B", "SUPPLY", 100, 4)), NOW,
                                     relax_time=flags[d["flag"]])["SEC"]["cancelled_shares"]
            except ValueError:
                got = "REJECTED"
            T.add("tcft_recorded", same(got, d["r10"]), {"family": fam, "name": r["name"]})
        elif fam == "BOOLEAN_AND_SCALE":
            s, dd = d["supply"], d["demand"]
            got = K.cancellation((lot("d", "A", "DEMAND", dd, 2), lot("s", "B", "SUPPLY", s, 1)), NOW)["SEC"]
            T.add("tcft_recorded", same(got, d["r10"]), {"family": fam, "name": r["name"]})
            scale_i += 1
        elif fam == "RANDOM_EXACT_MINCUT":
            lots, carry = mincut[k_mincut]
            k_mincut += 1
            ok = [l.__dict__ for l in lots] == d["lots"]
            for relaxed in (False, True):
                got = K.cancellation(lots, NOW, carry, relaxed)["SEC"]
                ok = ok and same(got, d[str(relaxed)]["actual"])
            T.add("tcft_recorded", ok, {"family": fam, "name": r["name"]})
        elif fam == "FUNDED_SWAP":
            x = d["input"]
            q, settle = x["qqq_prices"], x["settlement"]
            got = X.completed_swap(40000, x["fee"], x["fill"], q, 100, 105, settle, 6, settle, 6 + settle)
            T.add("tcft_recorded", json.loads(json.dumps(got, default=str)) == d["account"],
                  {"family": fam, "name": r["name"]})
        elif fam == "TARGET_GATE":
            T.add("tcft_recorded", X.target_gate(d["row"], NOW) == d["result"], {"family": fam, "name": r["name"]})
        elif fam == "RISK_EXIT":
            T.add("tcft_recorded", X.risk_exit(*d["input"]) == d["result"], {"family": fam, "name": r["name"]})
        else:
            T.add("tcft_recorded", False, {"family": fam, "name": r["name"], "why": "unknown family"})


# ------------------------------------------------------------------------------------------------------------ CARM
def lane_carm(Ks, T, rng):
    from desk.sleeves.quant_research import carm
    for i in range(N):
        def side():
            a = float(rng.integers(0, 50)) if rng.random() < 0.95 else 0.0
            return {"added": a, "executed": float(rng.integers(0, 30)), "cancelled": float(rng.integers(0, 30)),
                    "mature_live": float(rng.integers(0, 30))}
        ep = {"support": {"train_episodes": float(rng.choice([400, 600, 600, 600, 600])),
                          "train_dates": float(rng.choice([90, 120, 120, 120, 120])),
                          "calibration_dates": float(rng.choice([50, 70, 70, 70, 70]))},
              "summary": {"B": side(), "A": side()},
              "estimates": {"gross_lower_bp": float(rng.uniform(0, 120)), "qqq_upper_bp": float(rng.uniform(0, 30)),
                            "incremental_lower_bp": float(rng.uniform(0, 12)),
                            "cost_upper_bp": float(rng.uniform(5, 30)), "overhead_bp": float(rng.uniform(-1, 10)),
                            "cpdw_bp": float(rng.uniform(0, 10))}}
        mid = float(rng.uniform(20, 500))
        half = mid * float(rng.uniform(0, 2.4e-4))
        quote = {"bid": mid - half, "ask": mid + half}
        got = carm.evaluate(ep, quote)
        sup = ep["support"]
        if sup["train_episodes"] < 500 or sup["train_dates"] < 100 or sup["calibration_dates"] < 60:
            want = (False, "INSUFFICIENT_SUPPORT")
        else:
            e = ep["estimates"]
            try:
                ok = Ks.admit(gross_lower_bp=e["gross_lower_bp"], qqq_upper_bp=e["qqq_upper_bp"],
                              incremental_lower_bp=e["incremental_lower_bp"], cost_upper_bp=max(15.0, e["cost_upper_bp"]),
                              overhead_bp=e["overhead_bp"])
                err = None
            except ValueError as exc:
                ok, err = False, str(exc)
            mb = [(s["executed"] - s["cancelled"] + s["mature_live"]) / s["added"] if s["added"] else None
                  for s in (ep["summary"]["B"], ep["summary"]["A"])]
            m = mb[0] - mb[1] if None not in mb else None
            if err is not None:
                want = (False, "INVALID_INPUT: " + err[:80])
            elif m is None:
                want = (False, "UNSUPPORTED_MEMORY")
            elif not ok or e["cpdw_bp"] <= 5:
                want = (False, "NET_EDGE")
            elif (quote["ask"] - quote["bid"]) / ((quote["ask"] + quote["bid"]) / 2) * 1e4 > 4:
                want = (False, "SPREAD")
            else:
                want = (True, "ADMITTED")
        T.add("carm", tuple(got) == want, {"case": i, "port": list(got), "source": list(want)})


# ------------------------------------------------------------------------------------------------------------ AIRT
def airt_episode(rng, Ks):
    route = rng.choice(["continuation", "recovery", "random"], p=[0.35, 0.35, 0.3])
    scale = float(rng.uniform(10, 40)) if route != "random" else float(rng.uniform(5, 40))
    D = max(20.0, 1.5 * scale) * float(rng.uniform(1.0, 2.5))
    ep = {"v0": float(rng.uniform(2, 5)), "a0": float(rng.uniform(1.25, 2)), "scale": scale,
          "spread0": float(rng.uniform(4, 15)), "midpoint": 100.0, "sigma1m": float(rng.uniform(1, 30)),
          "expected_round_trip_bp": float(rng.uniform(1, 20)), "policy_sha": "pol"}
    ep["spread2"] = min(8.0, 0.7 * ep["spread0"]) * float(rng.uniform(0.5, 1.05))
    if route == "continuation":
        x0 = D
        ep.update(x0=x0, x1=x0 * float(rng.uniform(0.78, 1.2)), x2=x0 * float(rng.uniform(0.78, 1.2)),
                  q1=float(rng.uniform(0.08, 0.5)), q2=float(rng.uniform(0.08, 0.5)),
                  eta1=float(rng.uniform(0.04, 0.3)) * D, vwap1=float(rng.uniform(99, 100.02)),
                  vwap2=float(rng.uniform(99, 100.02)))
        ep["eta2"] = ep["eta1"] * float(rng.uniform(0.45, 1.5))
    elif route == "recovery":
        x0 = -D
        ep.update(x0=x0, x1=x0 * float(rng.uniform(0.6, 1.2)), x2=-abs(x0) * float(rng.uniform(-0.05, 1.0)),
                  q1=-float(rng.uniform(0.08, 0.5)), q2=float(rng.uniform(-0.06, 0.4)),
                  eta1=-float(rng.uniform(0, 0.06)) * D, eta2=float(rng.uniform(0.18, 1.0)) * D,
                  vwap1=float(rng.uniform(99, 100.02)), vwap2=float(rng.uniform(99, 101)))
    else:
        sign = 1 if rng.random() < 0.5 else -1
        x0 = sign * float(rng.uniform(10, 150))
        ep.update(x0=x0, x1=x0 * float(rng.uniform(0.6, 1.2)), x2=x0 * float(rng.uniform(0.5, 1.2)),
                  v0=float(rng.uniform(1, 5)), a0=float(rng.uniform(1, 2)), spread2=float(rng.uniform(1, 10)),
                  q1=float(rng.uniform(-0.5, 0.5)), q2=float(rng.uniform(-0.5, 0.5)),
                  eta1=float(rng.uniform(-10, 40)), eta2=float(rng.uniform(-10, 60)),
                  vwap1=float(rng.uniform(99, 101)), vwap2=float(rng.uniform(99, 101)))
    return ep


def airt_records(rng, cell, now, n, days, mean):
    recs = []
    for k in range(n):
        day = f"2026-{1 + k % days // 28:02d}-{1 + k % days % 28:02d}"
        t0 = now - float(rng.uniform(5e5, 5e7))
        recs.append({"technical_eligible": True, "mature": True, "policy_sha": "pol", "cell": list(cell),
                     "permanent_id": f"P{k}", "day": day, "event_at": t0, "outcome_at": t0 + 100,
                     "available_at": t0 + 200, "net": float(rng.normal(mean, 30)), "execution_cost": 5.0,
                     "reserved": 10000.0})
    return recs


def lane_airt(Ks, T, rng):
    from desk.sleeves.quant_research import airt
    Kv = airt.kernel()
    now = 1.8e9
    keys = airt.ROUTE_KEYS
    for i in range(N):
        ep = airt_episode(rng, Ks)
        try:
            name = Ks.route(**{k: ep[k] for k in keys})
            if name is None:
                want = (None, "NO_ROUTE")
            else:
                D = abs(ep["x0"])
                c = Ks.cell(name, ep["v0"], D, ep["scale"])
                ep["records"] = airt_records(rng, c if rng.random() < 0.95 else ("other", 0, 0), now,
                                             int(rng.choice([150, 250, 300, 300])), int(rng.choice([50, 70, 80, 80])),
                                             float(rng.uniform(0, 60)))
                mean, se = Ks.calibration(ep["records"], now, "pol", c)
                if not Ks.expectancy_admitted(mean, se, ep["expected_round_trip_bp"]):
                    want = (None, "EXPECTANCY")
                else:
                    want = (name, c, Ks.stop_distance(D, ep["sigma1m"]))
        except Ks.EvidenceUnavailable as e:
            want = (None, "ABSTAIN: " + str(e)[:80])
        got = airt.evaluate(ep, now)
        if want[0] is None:
            ok = got[0] is None and got[1] == want[1]
        else:
            ok = got[0] == want[0] and tuple(got[1]) == tuple(want[1]) and same(got[2]["d"], want[2])
        T.add("airt_admission", ok, {"case": i, "port": [got[0], str(got[1])], "source": [want[0], str(want[1])]})
        # sizing and capacity, the exit rule: direct source-vs-vendored calls
        args = dict(equity=float(rng.uniform(1e5, 2e6)), d=float(rng.uniform(1e-3, 2e-2)),
                    adv20=float(rng.uniform(1e4, 1e8)), observed_last60_dollars=float(rng.uniform(0, 1e7)),
                    entry_price=float(rng.uniform(5, 500)))
        cap = dict(equity=args["equity"], available_cash=float(rng.uniform(0, args["equity"])),
                   gross_with_reservations=float(rng.uniform(0, 0.5 * args["equity"])),
                   sector_with_reservations={"S": float(rng.uniform(0, 0.3 * args["equity"]))},
                   occupied_names=int(rng.integers(0, 5)), sector="S", proposed_shares=int(rng.integers(0, 5000)),
                   price_cap=args["entry_price"] * 1.0002, session_return=float(rng.uniform(-0.01, 0.01)),
                   peak_drawdown=float(rng.uniform(0, 0.07)))
        T.add("airt_size", Ks.size_shares(**args) == Kv.size_shares(**args) and
              Ks.portfolio_capacity(**cap) == Kv.portfolio_capacity(**cap), {"case": i})
        ex = dict(bid=float(rng.uniform(95, 105)), average_fill=100.0, d=float(rng.uniform(1e-3, 0.03)),
                  now=now + float(rng.uniform(0, 3000)), first_fill=now, route_name=str(rng.choice(
                      ["continuation", "recovery"])), x=float(rng.uniform(-20, 20)),
                  flatten_at=now + float(rng.uniform(0, 4000)) if rng.random() < 0.5 else None)
        T.add("airt_exit", Ks.exit_reason(**ex) == Kv.exit_reason(**ex), {"case": i})


# ------------------------------------------------------------------------------------------------------------- CRD
EVIDENCE = ("rank", "rank_then", "residual_sum", "release", "calibrated", "rank_only", "se", "incremental_se",
            "effective_origins", "calibration_dates", "round_trip_cost")


def crd_evidence(rng):
    return {"rank": float(rng.uniform(0.5, 1.0)), "rank_then": float(rng.uniform(0.3, 0.9)),
            "residual_sum": float(rng.normal(0.01, 0.02)), "release": bool(rng.random() < 0.8),
            "calibrated": float(rng.uniform(0, 0.05)), "rank_only": float(rng.uniform(0, 0.03)),
            "se": float(rng.uniform(0, 0.01)), "incremental_se": float(rng.uniform(0, 0.01)),
            "effective_origins": float(rng.choice([25.0, 35.0, 60.0])), "calibration_dates": int(rng.choice([90, 120])),
            "round_trip_cost": float(rng.uniform(0, 0.004))}


def crd_doc(rng, n, Ks):
    a = rng.normal(0, 1, (n, n))
    cov = (a @ a.T / n + np.eye(n)) * float(rng.uniform(1e-4, 6e-4))
    corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
    m = int(rng.integers(150, 250))
    gross = 1.0 + float(rng.uniform(0, 0.04)) + rng.multivariate_normal(np.zeros(n), cov, m)
    names = [f"N{k}" for k in range(n)]
    return {"names": names, "sectors": [f"S{int(rng.integers(0, 3))}" for _ in range(n)],
            "clusters": [list(map(int, g)) for g in Ks.connected_clusters((corr + corr.T) / 2, 0.7)],
            "covariance20": cov.tolist(), "lower_mean_gross": np.maximum(gross, 0.01).tolist(),
            "cash_gross": [1.0001] * m, "candidates": {s: crd_evidence(rng) for s in names}}


def crd_plan_source(Ks, doc, held, marks, cash):
    names = list(doc["names"])
    if any(q > 0 and s not in names for s, q in held.items()):
        return None
    keep = []
    for i, s in enumerate(names):
        ev = doc["candidates"].get(s)
        try:
            ok = ev is not None and Ks.entry_allowed(*(ev[k] for k in EVIDENCE))
        except (KeyError, TypeError, ValueError):
            ok = False
        if ok or held.get(s, 0) > 0:
            keep.append(i)
    if not keep:
        return {}
    pos = {i: j for j, i in enumerate(keep)}
    gross = np.asarray(doc["lower_mean_gross"])[:, keep]
    cov = np.asarray(doc["covariance20"])[np.ix_(keep, keep)]
    sectors = [doc["sectors"][i] for i in keep]
    clusters = [g for g in ([pos[i] for i in grp if i in pos] for grp in doc["clusters"]) if g]
    px = np.array([marks[names[i]] for i in keep])
    shares = np.array([float(held.get(names[i], 0)) for i in keep])
    equity = float(shares @ px + cash)
    try:
        res = Ks.optimize_target(shares * px / equity, gross, np.asarray(doc["cash_gross"]), cov, sectors, clusters)
        if not res["trade"]:
            return {names[i]: int(q) for i, q in zip(keep, shares)}
        r = Ks.round_target(shares, res["plan"]["stocks"], px, cash, sectors=sectors, clusters=clusters,
                            covariance20=cov)
    except (Ks.DataGap, ValueError):
        return None
    return {names[i]: int(q) for i, q in zip(keep, r["shares"])}


def lane_crd(Ks, T, rng):
    from desk.sleeves.quant_research import crd
    Kv = crd.kernel()
    for i in range(N):
        ev = crd_evidence(rng)
        ok, why = crd.admitted(ev)
        want = Ks.entry_allowed(*(ev[k] for k in EVIDENCE))
        T.add("crd_entry", ok == want and why == ("ADMITTED" if want else "ENTRY_GATE"), {"case": i})
        x = dict(rank=float(rng.uniform(0, 1)), conservative_forecast=float(rng.normal(0.005, 0.01)),
                 fundamental_eligible=bool(rng.random() < 0.9), hard_cap_breach=bool(rng.random() < 0.1),
                 entry_drawdown=float(rng.uniform(0, 0.12)), account_drawdown=float(rng.uniform(0, 0.25)))
        T.add("crd_exit", Ks.exit_decision(**x) == Kv.exit_decision(**x), {"case": i})
    for i in range(N_PLAN):
        n = int(rng.integers(2, 6))
        doc = crd_doc(rng, n, Ks)
        marks = {s: float(rng.uniform(20, 300)) for s in doc["names"]}
        held = {}
        cash = 1_000_000.0
        if rng.random() < 0.5:                                    # a held book of 1-2 names at about 3-5%
            for s in doc["names"][:int(rng.integers(1, 3))]:
                held[s] = int(float(rng.uniform(0.03, 0.05)) * 1e6 / marks[s])
                cash -= held[s] * marks[s]
        got, det = crd.plan(doc, held, marks, cash)
        want = crd_plan_source(Ks, doc, held, marks, cash)
        T.add("crd_plan", (got is None and want is None) or got == want,
              {"case": i, "port": got if got is None or isinstance(got, dict) else str(got), "source": want,
               "detail": det if isinstance(det, str) else {k: v for k, v in det.items() if k != "gate"}})


def crd_owner_tests(T):
    """crd/repair/test_repairs.py (19 owner tests) executed against the vendored crd_r10.py."""
    tmp = tempfile.mkdtemp(prefix="qr_crd_owner_")
    try:
        os.makedirs(os.path.join(tmp, "crd", "repair", "history", "pre_final_id_domain"))
        os.makedirs(os.path.join(tmp, "crd", "repair", "history", "pre_result_alias"))
        for rel, sha in CRD_TESTS.items():
            with open(os.path.join(tmp, "crd", rel), "wb") as f:
                f.write(blob(sha))
        with open(os.path.join(tmp, "crd", "repair", "crd_r10.py"), "wb") as f:
            f.write(vendored_bytes("crd/crd_r10.py"))
        r = subprocess.run([sys.executable, "-I", os.path.join(tmp, "crd", "repair", "test_repairs.py")], cwd=tmp,
                           capture_output=True, text=True, timeout=1800,
                           env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"))
        out = json.loads(r.stdout[r.stdout.index("{"):])
        rec = {t["id"]: t["pass"] for t in json.loads(blob(CRD_RECORDED))["tests"]}
        for t in out["tests"]:
            T.add("crd_owner_tests", t["pass"] and rec.get(t["id"]) is True, {"id": t["id"],
                                                                              "error": t.get("error")})
        return {"passed": out["passed"], "failed": out["failed"], "recorded_passed": sum(rec.values())}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    T = Tally()
    byte = {rel: vendored_bytes(rel) == blob(sha) for rel, (_, sha) in FILES.items()}
    files = {rel: sha for rel, (_, sha) in FILES.items()}
    rng = np.random.default_rng(20261016)
    with source_tree(files, prefix="qr_r10k_src_") as (tmp, load):
        Ks_cer = load("cer/reference_kernel_r10.py", "r10src_cer")
        Ks_cqr = load("cqr/queue_delta_r10.py", "r10src_cqr")
        Ks_carm = load("carm/code/reference_kernel.py", "r10src_carm")
        Ks_airt = load("airt/code/vendor/airt_r1.py", "r10src_airt")
        Ks_crd = load("crd/crd_r10.py", "r10src_crd")
        sys.path.insert(0, os.path.join(tmp, "tcft", "code"))
        try:
            Ks_tcft = load("tcft/code/kernel.py", "r10src_tcft_kernel")
            Xs_tcft = load("tcft/code/execution.py", "r10src_tcft_execution")
        finally:
            sys.path.remove(os.path.join(tmp, "tcft", "code"))
        lane_cer(Ks_cer, T, rng)
        lane_cqr(Ks_cqr, T, rng)
        lane_tcft(Ks_tcft, Xs_tcft, T, rng)
        lane_carm(Ks_carm, T, rng)
        lane_airt(Ks_airt, T, rng)
        lane_crd(Ks_crd, T, rng)
    from desk.sleeves.quant_research import tcft
    K, X = tcft.kernels()
    tcft_recorded(K, X, T)
    owner = crd_owner_tests(T)
    from desk.sleeves.quant_research import airt, carm, cer, cqr, crd
    out = {"family": "quant_research",
           "sleeves": [cer.SID, cqr.SID, tcft.SID, carm.SID, airt.SID, crd.SID],
           "byte_exact_vendoring": byte, "parts": T.parts, "source_outcomes": T.outcomes, "crd_owner_tests": owner,
           "cases": sum(p["cases"] for p in T.parts.values()),
           "identical": sum(p["identical"] for p in T.parts.values()), "n_diffs": len(T.diffs), "diffs": T.diffs,
           "source": {"repo": "quant-research-backup", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
                      "lane": LANE, "files": {rel: {"path": p, "blob_sha": s} for rel, (p, s) in FILES.items()},
                      "tcft_test_cases": TCFT_CASES, "crd_tests": CRD_TESTS},
           "method": "per lane: the sleeve's admission function on its vendored kernel vs the playbook rule composed "
                     "on the archive's kernel loaded from its blob (randomized); direct source-vs-vendored calls for "
                     "AIRT sizing / capacity / exits and CRD exits; CRD plans (gate, restriction, SLSQP, whole-share "
                     "rounding); TCFT's recorded campaign and CRD's owner tests against the vendored kernels",
           "not_in_this_comparison": ["the registered research inputs (each lane's divergence 1: no free source)",
                                      "desk execution (quotes, windows, fills)"]}
    write_receipt("qr_r10_kernels", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["parts"]),
          json.dumps(r["byte_exact_vendoring"]), json.dumps(r["crd_owner_tests"]))
