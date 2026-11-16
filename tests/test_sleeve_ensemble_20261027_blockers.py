"""SLEEVE-ENSEMBLE-20261027 blockers: Claude's sleeve ensemble tool
(Femto-lean desk/forecast/ensemble.py + tools/sleeve_ensemble.py,
factory-p3) ported into desk3/forecast/ (ensemble.py, evidence.py,
sleeve_ensemble.py) as an ADVISORY report generator (EXECUTE-SCOPE-
2026-10-27 item 6; provenance in desk3/forecast/PROVENANCE.md).

Adapted from the source tests (tests/test_sleeve_ensemble.py in the
source repo, sha256 d4a5bc46... in the program MANIFEST) to this repo's
unittest gate. Two source tests change form, by name:
  - the Ledoit-Wolf sklearn reference test: sklearn is not installed in
    this repo's environment, so the blocker checks the shrinkage's
    defining properties instead (unit diagonal, delta in [0, 1],
    off-diagonals shrunk toward 0, exact identity case);
  - the no-import guard: muse-desk-v3 has no desk/ai operator tools, so
    the guard is absolute here: NO production module outside
    desk3/forecast imports the ensemble or the sleeve_ensemble tool.

Fail directions (each proven at landing by temporary breakage):
  - twin detection weakened (single linkage / lower twin_rho) -> red
  - identical-fill hashing losing its scale normalisation -> red
  - the tool accepting a corrupt ledger segment -> red
  - the v3 probe counting a pre-epoch or timestamp-less fill -> red
  - any production path importing the ensemble (wiring it into a
    sleeve, the dispatcher, or a book) -> red
"""
import ast
import gzip
import hashlib
import json
import math
import os
import sys
import tempfile
import unittest
import warnings
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from core import data as cal  # noqa: E402
from desk3.forecast import ensemble as EN  # noqa: E402
from desk3.forecast import evidence as EV  # noqa: E402
from desk3.forecast import sleeve_ensemble as TOOL  # noqa: E402

ET = ZoneInfo("America/New_York")


def _sessions(n, start=date(2027, 1, 4)):
    out, d = [], start
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _next_trading_day(d):
    d += timedelta(days=1)
    while not cal.is_trading_day(d):
        d += timedelta(days=1)
    return d


def _ts(d, hour=16, minute=30):
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=ET).timestamp()


def _book(rets, days, cap=100_000.0, inst="EQ:SPY"):
    eq, curve = cap, [[_ts(days[0]), cap]]
    for d, r in zip(days[1:], rets):
        eq *= 1 + r
        curve.append([_ts(d), eq])
    return {"capital": cap, "curve": curve, "n_fills": 2,
            "positions": {inst: {"qty": 1.0, "avg": 1.0}}, "trades": [], "cash": cap}


def _fills(sid, days, inst="EQ:SPY", scale=1.0):
    return [{"sleeve": sid, "inst": inst, "side": "buy" if i % 2 == 0 else "sell",
             "qty": scale * (10 + i), "at": _ts(d, 10)} for i, d in enumerate(days[:6])]


class TestEnsembleMath(unittest.TestCase):
    def test_identical_fill_sequences_grouped_and_scaled_copies(self):
        days = _sessions(10)
        fills = (_fills("a", days) + _fills("b", days) + _fills("c", days, scale=2.0)
                 + _fills("d", days[1:]) + _fills("e", days, inst="EQ:QQQ"))
        self.assertEqual(EN.identical_fill_groups(EN.fill_hashes(fills)), [["a", "b", "c"]])
        self.assertEqual(EN.identical_fill_groups(EN.fill_hashes(fills, normalise=False)),
                         [["a", "b"]])
        split = [dict(r, qty=r["qty"] / 2) for r in _fills("f", days) for _ in (0, 1)]
        self.assertEqual(EN.fill_hashes(split, normalise=False)["f"][0],
                         EN.fill_hashes(_fills("a", days), normalise=False)["a"][0])

    def test_three_identical_sleeves_count_as_one_bet(self):
        rng = np.random.default_rng(1)
        days = _sessions(401)
        base = rng.normal(0, 0.01, 400)
        books = {f"dup{i}": _book(base, days) for i in range(3)}
        books["ind1"] = _book(rng.normal(0, 0.01, 400), days)
        books["ind2"] = _book(rng.normal(0, 0.01, 400), days)
        rep = EN.build(books, [], n_boot=50)
        self.assertEqual(rep["counts"]["clusters"], 3)
        big = rep["clusters"][0]
        self.assertEqual(big["members"], ["dup0", "dup1", "dup2"])
        self.assertEqual(big["why"], "rho")
        self.assertTrue(2.7 < rep["bets"]["participation_ratio"] <= 3.0 + 1e-9)
        self.assertLess(rep["bets"]["participation_ratio_sleeves_no_dedup"], 2.6)

    def test_identical_fills_merge_unless_pnl_disagrees(self):
        rng = np.random.default_rng(2)
        days = _sessions(61)
        a = rng.normal(0, 0.01, 60)
        b = a + rng.normal(0, 0.004, 60)          # rho ~ 0.93: not a twin
        books = {"a": _book(a, days), "b": _book(b, days),
                 "c": _book(rng.normal(0, 0.01, 60), days),
                 "d": _book(rng.normal(0, 0.01, 60), days), "e": _book(a, days)}
        fills = _fills("c", days) + _fills("d", days) + _fills("a", days[2:]) + _fills("e", days[2:])
        rep = EN.build(books, fills, n_boot=50)
        groups = {tuple(c["members"]): c["why"] for c in rep["clusters"]}
        self.assertEqual(groups[("a", "e")], "fills+rho")
        self.assertIn(("b",), groups)
        self.assertIn(("c",), groups)
        self.assertIn(("d",), groups)
        self.assertEqual([x[:2] for x in rep["fill_pnl_conflicts"]], [("c", "d")])

    def test_twin_groups_use_complete_linkage(self):
        rho = np.array([[1, .96, .5], [.96, 1, .96], [.5, .96, 1.]])
        got = sorted(map(sorted, EN.twin_groups(rho)))
        self.assertIn(got, ([[0, 1]], [[1, 2]]))

    def test_leave_one_out_matches_hand_calculation(self):
        X = np.array([[0.01, -0.02, 0.005], [0.02, 0.01, -0.01],
                      [-0.01, 0.03, 0.0], [0.005, -0.01, 0.02]])
        out = EN.loo(X, n_boot=20)

        def sr(p):
            m = sum(p) / len(p)
            return m / math.sqrt(sum((x - m) ** 2 for x in p) / (len(p) - 1))

        def mdd(p):
            c, peak, dd = 0.0, 0.0, 0.0
            for x in p:
                c += x
                peak = max(peak, c)
                dd = max(dd, peak - c)
            return dd

        full = [row.mean() for row in X]
        self.assertAlmostEqual(out["sr"], sr(full))
        self.assertAlmostEqual(out["mdd"], mdd(full))
        for s in range(3):
            wo = [np.delete(row, s).mean() for row in X]
            self.assertAlmostEqual(out["mc_sr"][s], sr(full) - sr(wo))
            self.assertAlmostEqual(out["mc_dd"][s], mdd(full) - mdd(wo))
            self.assertLessEqual(out["mc_lo"][s], out["mc_hi"][s])

    def test_ledoit_wolf_shrinkage_properties(self):
        rng = np.random.default_rng(3)
        R = rng.normal(0, 1, (30, 8)) @ rng.normal(0, 1, (8, 8))
        Z = EN.standardize(R)
        C, delta = EN.lw_corr(Z)
        self.assertTrue(0.0 <= delta <= 1.0)
        self.assertTrue(np.allclose(np.diag(C), 1.0))
        S = Z.T @ Z / Z.shape[0]
        s = np.sqrt(np.diag(S))
        sample_corr = S / np.outer(s, s)
        off = ~np.eye(8, dtype=bool)
        self.assertTrue(np.all(np.abs(C[off]) <= np.abs(sample_corr[off]) + 1e-9))
        C1, d1 = EN.lw_corr(np.eye(5))            # already identity: nothing to shrink
        self.assertTrue(np.allclose(C1, np.eye(5)))

    def test_pairwise_corr_needs_active_overlap(self):
        R = np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0],
                      [0.01, 0.02], [-0.01, -0.01], [np.nan, 0.01]])
        rho, n = EN.pairwise_corr(R, min_overlap=3)
        self.assertEqual(n[0, 1], 2)
        self.assertTrue(np.isnan(rho[0, 1]))
        rho, _ = EN.pairwise_corr(R, min_overlap=2)
        self.assertAlmostEqual(rho[0, 1], np.corrcoef(R[:5, 0], R[:5, 1])[0, 1])

    def test_daily_returns_common_calendar_and_sessions_alive(self):
        days = _sessions(5)
        sat = days[-1] + timedelta(days=1)
        mon = _next_trading_day(days[-1])
        crypto = {"capital": 100.0, "curve": [[_ts(d), 100.0 + i] for i, d in enumerate(days)]
                  + [[_ts(sat), 110.0], [_ts(mon), 111.0]]}
        late = {"capital": 100.0, "curve": [[_ts(days[2]), 100.0], [_ts(days[3]), 101.0]]}
        dr = EN.daily_returns({"c": crypto, "l": late})
        self.assertEqual(dr["dates"][-1], mon.isoformat())
        self.assertEqual(len(dr["dates"]), 5)
        j = dr["sids"].index("c")
        self.assertAlmostEqual(dr["R"][-1, j], 111.0 / 104.0 - 1)
        k = dr["sids"].index("l")
        self.assertEqual(int(dr["alive"][k]), 1)
        self.assertEqual(int(dr["alive"][j]), 5)
        self.assertTrue(np.isnan(dr["R"][0, k]) and np.isnan(dr["R"][-1, k]))

    def test_short_records_are_low_confidence_and_unproven(self):
        rng = np.random.default_rng(4)
        days = _sessions(8)
        books = {f"s{i}": _book(rng.normal(0, 0.01, 7), days) for i in range(6)}
        rep = EN.build(books, [], n_boot=50)
        self.assertTrue(all(r["low_confidence"] and r["label"] == "unproven"
                            for r in rep["sleeves"]))
        self.assertEqual(rep["counts"]["with_record"], 6)

    def test_evidence_psr_dsr_formulas(self):
        self.assertEqual(EV.MIN_RETURNS, 20)
        self.assertEqual(EN.MIN_RECORD, 20)
        self.assertAlmostEqual(EV.psr(0.0, 100, 0.0, 3.0), 0.5)
        self.assertGreater(EV.psr(0.1, 100, 0.0, 3.0), EV.psr(0.0, 100, 0.0, 3.0))
        self.assertIsNone(EV.psr(0.1, 1, 0.0, 3.0))
        self.assertEqual(EV.expected_max_sr(0.01, 1), 0.0)
        self.assertLess(EV.expected_max_sr(0.01, 5), EV.expected_max_sr(0.01, 50))
        self.assertAlmostEqual(EV._q(0.0, 0.0, 3.0), 1.0)


def _imports(path):
    mods = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(open(path).read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                parts = os.path.relpath(path, HERE).replace(os.sep, "/")[:-3].split("/")[:-n.level]
                base = ".".join(parts + ([base] if base else []))
            mods.add(base)
            mods |= {f"{base}.{a.name}" for a in n.names}
    return mods


class TestAdvisoryGuard(unittest.TestCase):
    def test_no_production_module_imports_the_ensemble(self):
        hits = []
        for root, _dirs, files in os.walk(HERE):
            rel = os.path.relpath(root, HERE)
            if rel.startswith(os.path.join("desk3", "forecast")) or "__pycache__" in rel \
                    or rel.startswith(".git") or rel.startswith("tests") \
                    or rel.startswith(".gate_tmp"):
                continue
            for fn in files:
                if fn.endswith(".py"):
                    txt = open(os.path.join(root, fn), errors="ignore").read()
                    if "forecast.ensemble" in txt or "forecast import ensemble" in txt \
                            or "sleeve_ensemble" in txt:
                        hits.append(os.path.join(rel, fn))
        self.assertEqual(hits, [], f"ensemble wired into production: {hits}")

    def test_ensemble_reads_no_sleeve_engine_or_broker_path(self):
        banned = ("sleeves", "desk3.dispatcher", "desk3.broker", "desk3.cycle",
                  "desk3.registry", "desk3.producers", "adapters", "adapters3")
        for rel in ("desk3/forecast/ensemble.py", "desk3/forecast/evidence.py",
                    "desk3/forecast/sleeve_ensemble.py"):
            mods = _imports(os.path.join(HERE, rel))
            bad = [m for m in mods if any(m == b or m.startswith(b + ".") for b in banned)]
            self.assertEqual(bad, [], (rel, mods))


def _femto_state(root, books, fills, corrupt=False):
    led = os.path.join(root, "state", "ledger")
    os.makedirs(led)
    with open(os.path.join(root, "state", "books.json"), "w") as f:
        json.dump(books, f)
    raw = "".join(json.dumps(dict(f, kind="book_fill")) + "\n" for f in fills).encode()
    with open(os.path.join(led, "seg-000000.jsonl.gz"), "wb") as f:
        f.write(gzip.compress(raw))
    with open(os.path.join(led, "open.jsonl"), "wb") as f:
        f.write(b"")
    sha = hashlib.sha256(raw).hexdigest() if not corrupt else "0" * 64
    with open(os.path.join(led, "manifest.json"), "w") as f:
        json.dump({"segments": [{"name": "seg-000000.jsonl.gz", "sha256": sha}],
                   "open": {"name": "open.jsonl"}}, f)


class TestTool(unittest.TestCase):
    def test_tool_writes_only_its_report_and_fails_closed_on_bad_segment(self):
        rng = np.random.default_rng(5)
        days = _sessions(12)
        base = rng.normal(0, 0.01, 11)
        books = {"a": _book(base, days), "b": _book(base, days),
                 "c": _book(rng.normal(0, 0.01, 11), days)}
        fills = _fills("a", days) + _fills("b", days)
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "rec")
            _femto_state(src, books, fills)
            before = sorted(os.path.relpath(os.path.join(r, f), src)
                            for r, _d, fs in os.walk(src) for f in fs)
            out = os.path.join(td, "out", "rep")
            self.assertEqual(TOOL.main(["--root", src, "--out", out, "--boot", "50"]), 0)
            after = sorted(os.path.relpath(os.path.join(r, f), src)
                           for r, _d, fs in os.walk(src) for f in fs)
            self.assertEqual(before, after)
            self.assertEqual(sorted(os.listdir(os.path.join(td, "out"))), ["rep.json", "rep.md"])
            rep = json.loads(open(out + ".json").read())
            self.assertEqual(rep["counts"]["identical_fill_groups"], 1)
            self.assertEqual(rep["counts"]["clusters"], 2)
            md = open(out + ".md").read()
            self.assertIn("Proposal", md)
            bad = os.path.join(td, "bad")
            _femto_state(bad, books, fills, corrupt=True)
            with self.assertRaises(SystemExit):
                TOOL.main(["--root", bad, "--out", os.path.join(td, "x", "rep")])

    def test_v3_probe_epoch_scoping_and_honest_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "capital_epoch.json"), "w") as f:
                json.dump({"account": "TESTACCT", "epoch_start_utc": "2026-10-26T20:14:30+00:00"}, f)
            rows = [
                {"event": "fill", "sleeve": "s1", "ts": "2026-10-27T13:00:00+00:00"},   # in epoch
                {"event": "fill", "sleeve": "s2", "ts": "2026-10-27T14:00:00+00:00"},   # in epoch
                {"event": "fill", "sleeve": "s1", "ts": "2026-10-25T13:00:00+00:00"},   # pre-epoch
                {"event": "fill", "sleeve": "s3"},                                       # no ts
                {"event": "intent", "sleeve": "s9", "ts": "2026-10-27T15:00:00+00:00"},  # not a fill
            ]
            with open(os.path.join(td, "dispatcher.jsonl"), "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            probe = TOOL.probe_v3_state(td)
            self.assertEqual(probe["verdict"], "CANNOT_FEED_HONESTLY")
            self.assertEqual(probe["fills_in_epoch"], 2)
            self.assertEqual(probe["fills_pre_epoch_excluded"], 1)
            self.assertEqual(probe["fills_no_ts_excluded"], 1)
            self.assertEqual(probe["sessions_counted"], 1)
            self.assertEqual(probe["sessions_with_fills"], ["2026-10-27"])
            self.assertEqual(probe["sleeves_counted"], 2)
            self.assertFalse(probe["books_json_present"])
            self.assertTrue(any("equity curves" in m for m in probe["missing_inputs"]))


if __name__ == "__main__":
    unittest.main()
