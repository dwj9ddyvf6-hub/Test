"""GOING-LIVE-GRADER-ARMS-20261115 blockers: the grader arm kinds
built for Conversion Lane C (SPLIT_GRADE, PHASE_GRADE, MEMBER_GRADE,
TWO_POOL, both-sides FWD_GRADE, partial-target EXIT_PAIR profiles)
and the arms they register (CONV-34, 61, 62, 74, 75, 76, 77, 93, 94,
99, 101, 113, 131, 143, 150, 152, 156, 161). CONV-80 stays BLOCKED
by construction and must never appear in the registry.

Synthetic-stream tests pin each kind's arithmetic; registry tests
pin the arms' forms and their byte-identical falsifier and kill
rule texts against the Conversion Register rows.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from desk3 import conversion_shadow as cs  # noqa: E402

REGISTER = (Path.home() / "workspace" / "research_notes"
            / "alpha-hunt-chaos-20261115" / "pass2"
            / "CONVERSION-REGISTER-2026-11-15.jsonl")

DATES = ["2026-11-%02d" % d for d in range(16, 31)] + \
        ["2026-12-%02d" % d for d in range(1, 16)]


def _series(closes):
    return (list(DATES), {d: c for d, c in zip(DATES, closes)})


class FakeBook:
    def __init__(self, series_map, root="/nonexistent-root"):
        self._map = series_map
        self.root = root

    def daily(self, symbol):
        return self._map.get(symbol)


def _bench(flat=200.0):
    return (list(DATES), {d: flat for d in DATES})


def _entry(sleeve, symbol, ts, price=100.0, dir_=1, iid="i1"):
    return {"sleeve": sleeve, "symbol": symbol, "price": price,
            "qty": 1.0, "ts": ts, "intent_id": iid,
            "date_et": ts[:10], "date_utc": ts[:10], "dir": dir_}


class TestSplitGrade(unittest.TestCase):
    def setUp(self):
        rising = [100.0 + 2 * k for k in range(30)]
        self.book = FakeBook({"AAA": _series(rising),
                              "QQQ": _series([200.0] * 30)})
        self.bench = _bench()

    def test_tod_ampm_split_separates_sides(self):
        arm = {"conv": "T", "kind": "SPLIT_GRADE",
               "split_key": "tod_ampm", "parents": ["p1"],
               "horizons": [5], "decisive_horizons": [5],
               "grade_n": 2, "grade_mode": "per_side",
               "spread_sides": ["AM", "PM"],
               "positive_rule": "a_positive_and_above_b",
               "calendar": "et"}
        entries = []
        for k in range(3):
            entries.append(_entry(
                "p1", "AAA", "2026-11-16T09:30:00-05:00",
                iid="am%d" % k))
            entries.append(_entry(
                "p1", "AAA", "2026-11-16T15:00:00-05:00",
                iid="pm%d" % k))
        res = cs.grade_split(self.book, self.bench, arm, entries,
                             split_ctx=cs.SplitContext("/nonexistent"))
        self.assertEqual(res["sides"]["AM"]["5"]["excess"]["n"], 3)
        self.assertEqual(res["sides"]["PM"]["5"]["excess"]["n"], 3)
        # identical entries at both hours on one series: equal means,
        # so the AM-above-PM rule grades negative, never positive.
        self.assertEqual(res["state"], "GRADED_NEGATIVE")

    def test_funding_sign_split_from_okx_record(self):
        from datetime import datetime, timezone

        def _ms(ts):
            return int(datetime.fromisoformat(
                ts.replace("Z", "+00:00")).timestamp() * 1000)

        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "state"))
            hist = {"history": {"ENJUSDT": [
                {"rate": -0.001, "ts_ms": _ms("2025-11-13T00:00:00Z")},
                {"rate": 0.002, "ts_ms": _ms("2025-11-15T00:00:00Z")}]}}
            with open(os.path.join(
                    td, "state", "okx_funding_history.json"),
                    "w") as fh:
                json.dump(hist, fh)
            ctx = cs.SplitContext(td)
            neg = _entry("p", "ENJUSDT", "2025-11-13T12:00:00Z")
            pos = _entry("p", "ENJUSDT", "2025-11-15T12:00:00Z")
            self.assertEqual(ctx.funding_sign(neg), "NEG")
            self.assertEqual(ctx.funding_sign(pos), "NONNEG")
            early = _entry("p", "ENJUSDT", "2025-11-01T12:00:00Z")
            self.assertIsNone(ctx.funding_sign(early))

    def test_warmup_state_split_groups(self):
        arm = {"conv": "T", "kind": "SPLIT_GRADE",
               "split_key": "warmup_state", "parents": ["a", "b"],
               "split_groups": {"PRESENT": ["a"], "ABSENT": ["b"]},
               "horizons": [5], "decisive_horizons": [5],
               "grade_n": 1, "grade_mode": "per_side",
               "spread_sides": ["PRESENT", "ABSENT"],
               "positive_rule": "a_above_b", "calendar": "et"}
        entries = [_entry("a", "AAA", "2026-11-16T10:00:00-05:00",
                          iid="a1"),
                   _entry("b", "AAA", "2026-11-16T10:00:00-05:00",
                          iid="b1")]
        res = cs.grade_split(self.book, self.bench, arm, entries,
                             split_ctx=cs.SplitContext("/nonexistent"))
        self.assertEqual(set(res["sides"]), {"PRESENT", "ABSENT"})


class TestPhaseGrade(unittest.TestCase):
    def test_phase_decomposition_arithmetic(self):
        closes = [100.0] * 30
        closes[1] = 110.0   # N1 span: 100 -> 110 = +10%
        closes[3] = 99.0    # N2-3 span: 110 -> 99 = -10%
        closes[5] = 118.8   # N4-5 span: 99 -> 118.8 = +20%
        book = FakeBook({"AAA": _series(closes),
                         "QQQ": _series([200.0] * 30)})
        arm = {"conv": "T", "kind": "PHASE_GRADE", "parents": ["p1"],
               "horizons": [5], "decisive_horizons": [5],
               "grade_n": 1, "grade_unit": "resolved entries",
               "phase_buckets": [
                   {"name": "N1", "from": 1, "to": 1},
                   {"name": "N2-3", "from": 2, "to": 3},
                   {"name": "N4-5", "from": 4, "to": 5},
                   {"name": "N4+", "from": 4, "to": None}],
               "phase_positive": "n23_positive_and_above_n1",
               "calendar": "et"}
        e = _entry("p1", "AAA", "2026-11-16T10:00:00-05:00")
        res = cs.grade_phase(book, _bench(), arm, [e])
        self.assertAlmostEqual(res["phases"]["N1"]["mean_bp"],
                               1000.0, places=1)
        self.assertAlmostEqual(res["phases"]["N2-3"]["mean_bp"],
                               -1000.0, places=1)
        self.assertAlmostEqual(res["phases"]["N4-5"]["mean_bp"],
                               2000.0, places=1)
        # N2-3 not positive: the shape grades negative at count.
        self.assertEqual(res["state"], "GRADED_NEGATIVE")


class TestBothSides(unittest.TestCase):
    def test_inverted_side_is_the_negated_stream(self):
        falling = [100.0 - 2 * k for k in range(30)]
        book = FakeBook({"AAA": _series(falling),
                         "QQQ": _series([200.0] * 30)},
                        root="/nonexistent-root")
        arm = {"conv": "T", "kind": "FWD_GRADE", "parents": ["p1"],
               "horizons": [5], "decisive_horizons": [5],
               "grade_n": 2, "grade_unit": "resolved entries",
               "both_sides": True, "calendar": "et",
               "print_distinct_dates": True}
        entries = [_entry("p1", "AAA",
                          "2026-11-16T10:00:00-05:00", iid="a"),
                   _entry("p1", "AAA",
                          "2026-11-17T10:00:00-05:00", iid="b")]
        res = cs.grade_fwd(book, _bench(), arm, entries)
        base = res["horizons"]["5"]["excess"]["mean_bp"]
        inv = res["inverted_horizons"]["5"]["excess"]["mean_bp"]
        self.assertLess(base, 0)
        self.assertAlmostEqual(inv, -base, places=1)
        self.assertEqual(res["state"], "GRADED_POSITIVE")
        self.assertEqual(res["distinct_decisive_dates"], 2)
        self.assertIn("accruing", res["borrow"])


class TestMemberAndTwoPool(unittest.TestCase):
    def setUp(self):
        rising = [100.0 + 2 * k for k in range(30)]
        falling = [100.0 - 2 * k for k in range(30)]
        self.book = FakeBook({"AAA": _series(rising),
                              "BBB": _series(falling),
                              "QQQ": _series([200.0] * 30)})
        self.bench = _bench()

    def test_per_member_count_blocks_grade_until_all_reach(self):
        arm = {"conv": "T", "kind": "MEMBER_GRADE",
               "parents": ["m1", "m2"], "horizons": [5],
               "decisive_horizons": [5], "grade_n": 2,
               "grade_unit": "graded fills per member",
               "calendar": "et"}
        entries = [_entry("m1", "AAA", "2026-11-16T10:00:00-05:00",
                          iid="a"),
                   _entry("m1", "AAA", "2026-11-17T10:00:00-05:00",
                          iid="b"),
                   _entry("m2", "AAA", "2026-11-16T10:00:00-05:00",
                          iid="c")]
        res = cs.grade_member(self.book, self.bench, arm, entries,
                              roster_ids=["m1", "m2", "x1"])
        self.assertEqual(res["per_member_decisive_n"],
                         {"m1": 2, "m2": 1})
        self.assertEqual(res["state"], "ACCRUING")

    def test_two_pool_identical_fills_incl_excl(self):
        arm = {"conv": "T", "kind": "TWO_POOL",
               "parents": ["f1", "fx"], "excluded": ["fx"],
               "horizons": [5], "decisive_horizons": [5],
               "grade_n": 1, "grade_unit": "forward fills per variant",
               "calendar": "et"}
        entries = [_entry("f1", "AAA", "2026-11-16T10:00:00-05:00",
                          iid="a"),
                   _entry("fx", "BBB", "2026-11-16T10:00:00-05:00",
                          iid="b")]
        res = cs.grade_two_pool(self.book, self.bench, arm, entries)
        self.assertGreater(res["family_incl_decisive"]["n"], 0)
        self.assertGreater(res["family_excl_decisive"]["mean_bp"],
                           res["family_incl_decisive"]["mean_bp"])
        self.assertLess(res["variant_decisive"]["mean_bp"], 0)
        self.assertEqual(res["state"], "GRADED_NEGATIVE")


class TestPartialTargetPath(unittest.TestCase):
    def test_partial_target_weighted_return(self):
        closes = [100.0] * 30
        closes[1] = 121.0   # target +20% touched at bar 1
        closes[5] = 100.0   # remainder exits flat at horizon 5
        series = _series(closes)
        out = cs.path_ret(series, _bench(), 0, 100.0, 1, 0.15, 0.20,
                          5, partial_pct=0.30)
        expect = 0.30 * (0.20 - cs.EXIT_COST) \
            + 0.70 * (0.0 - cs.EXIT_COST)
        self.assertAlmostEqual(out["ret"], expect, places=9)
        self.assertEqual(out["kind"], "partial_target_then_horizon")
        plain = cs.path_ret(series, _bench(), 0, 100.0, 1, 0.15,
                            0.20, 5)
        self.assertAlmostEqual(plain["ret"], 0.20 - cs.EXIT_COST,
                               places=9)


class TestAtsTercileKey(unittest.TestCase):
    def test_ats_z_recomputed_and_terciled(self):
        weeks = []
        base = 1000.0
        for j in range(12):
            weeks.append({"week_start": "2026-08-%02d" % (3 + 7 * j)
                          if 3 + 7 * j <= 31 else "2026-09-07",
                          "ats_share_qty": base + 100 * j})
        # simpler: explicit Mondays
        mondays = ["2026-08-03", "2026-08-10", "2026-08-17",
                   "2026-08-24", "2026-08-31", "2026-09-07",
                   "2026-09-14", "2026-09-21", "2026-09-28",
                   "2026-10-05", "2026-10-12", "2026-10-19"]
        weeks = [{"week_start": m, "ats_share_qty": 1000.0 + 500 * j}
                 for j, m in enumerate(mondays)]
        doc = {"per_symbol_series": {"AAA": {"weeks": weeks}}}
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "ats.json")
            with open(path, "w") as fh:
                json.dump(doc, fh)
            ctx = cs.SplitContext(td)
            arm = {"split_key": "ats_z_tercile", "series_path": path}
            e = _entry("p", "AAA", "2026-10-19T10:00:00-04:00")
            side = ctx.key(arm, e, "2026-10-19")
            self.assertIn(side, ("T1_LOW", "T2_MID", "T3_HIGH"))


def _register_rows():
    rows = {}
    with open(REGISTER) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


class TestRegistryArms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(
            (ROOT / "config/conversion_shadow_20261115.json")
            .read_text())
        cls.arms = cls.reg["arms"]
        cls.by_conv = {}
        for a in cls.arms:
            cls.by_conv.setdefault(a["conv"], []).append(a)
        cls.rows = _register_rows()

    def test_census_53_arms(self):
        # Renamed in substance by NIGHTLY-JOIN-ARTIFACTS-20261116:
        # CONV-86/87 FORECAST_JOIN arms joined the census
        # deliberately (53 to 55); their own blocker file is
        # tests/test_nightly_join_artifacts_20261116_blockers.py.
        # Renamed in substance again by SEGMENT-CONSTRUCTION-
        # 20261116 (55 to 56, CONV-80 SEGMENT_GRADE) and by
        # CONV21-INVERT-20261116 (56 to 57, CONV-21 FWD_GRADE);
        # the segment raise is carried here by
        # TOTAL-AUDIT-PIN-REBASE-20261116 (4).
        self.assertEqual(len(self.arms), 57)

    def test_new_arm_kinds(self):
        expect = {"CONV-61": "SPLIT_GRADE", "CONV-62": "PHASE_GRADE",
                  "CONV-74": "SPLIT_GRADE", "CONV-75": "PHASE_GRADE",
                  "CONV-76": "MEMBER_GRADE", "CONV-77": "ACTUAL_PAIR",
                  "CONV-93": "MEMBER_GRADE", "CONV-94": "FWD_GRADE",
                  "CONV-99": "FWD_GRADE", "CONV-101": "SPLIT_GRADE",
                  "CONV-113": "SPLIT_GRADE", "CONV-131": "SPLIT_GRADE",
                  "CONV-143": "FWD_GRADE", "CONV-150": "EXIT_PAIR",
                  "CONV-152": "FWD_GRADE", "CONV-156": "TWO_POOL",
                  "CONV-161": "EXIT_PAIR", "CONV-34": "EXIT_PAIR"}
        for conv, kind in expect.items():
            self.assertIn(conv, self.by_conv, conv)
            for a in self.by_conv[conv]:
                self.assertEqual(a["kind"], kind, conv)

    def test_multi_arm_rows(self):
        self.assertEqual(len(self.by_conv["CONV-152"]), 2)
        self.assertEqual(len(self.by_conv["CONV-161"]), 4)
        self.assertEqual(len(self.by_conv["CONV-34"]), 4)
        hosts161 = {a["parents"][0] for a in self.by_conv["CONV-161"]}
        self.assertEqual(hosts161, {"1w", "1wa", "s_1wlab", "1d"})
        hosts34 = {a["parents"][0] for a in self.by_conv["CONV-34"]}
        self.assertEqual(hosts34,
                         {"1w", "1wa", "s_1wlab", "s_rules_1w"})

    def test_falsifiers_byte_identical_to_register(self):
        # Scoped to this landing's 18 rows: every arm registered
        # tonight carries its register row's falsifier and kill
        # rule byte-identical. (Pre-existing arms carry the texts
        # their own landings pinned; two Pass 2 arms' config texts
        # differ from the jsonl register's expanded falsifier
        # wording, a pre-existing state this landing does not
        # rewrite.)
        new_convs = {"CONV-34", "CONV-61", "CONV-62", "CONV-74",
                     "CONV-75", "CONV-76", "CONV-77", "CONV-93",
                     "CONV-94", "CONV-99", "CONV-101", "CONV-113",
                     "CONV-131", "CONV-143", "CONV-150", "CONV-152",
                     "CONV-156", "CONV-161"}
        for conv in new_convs:
            for a in self.by_conv[conv]:
                self.assertEqual(a["falsifier"],
                                 self.rows[conv]["falsifier"], conv)
                self.assertEqual(a["kill_rule"],
                                 self.rows[conv]["kill_rule"], conv)

    def test_conv80_stays_blocked_unarmed(self):
        # Renamed in substance by SEGMENT-CONSTRUCTION-20261116
        # (carried here by TOTAL-AUDIT-PIN-REBASE-20261116 (4)):
        # CONV-80 is armed deliberately as the SEGMENT_GRADE arm;
        # its own blocker file is
        # tests/test_segment_construction_20261116_blockers.py.
        self.assertIn("CONV-80", self.by_conv)
        for a in self.by_conv["CONV-80"]:
            self.assertEqual(a["kind"], "SEGMENT_GRADE")

    def test_lazarus_bases_match_live_specs(self):
        for conv in ("CONV-161", "CONV-34"):
            for a in self.by_conv[conv]:
                self.assertEqual(cs.base_profile(a), a["base"], conv)
                self.assertFalse(cs.spec_drift(a), conv)

    def test_conv150_partial_target_profile(self):
        a = self.by_conv["CONV-150"][0]
        self.assertEqual(a["parents"], ["1d"])
        self.assertEqual(a["base"]["stop_pct"], 0.15)
        self.assertEqual(a["base"]["target_pct"], 0.20)
        self.assertEqual(a["base"]["partial_pct"], 0.30)
        self.assertEqual(a["base"]["horizon"], 40)
        names = {x["name"]: x for x in a["arms"]}
        self.assertIsNone(names["DROP_STOP"]["stop_pct"])
        self.assertEqual(names["WIDEN_stop"]["stop_pct"], 0.30)

    def test_conv34_counterfactual_profiles(self):
        arms = {a["parents"][0]: a for a in self.by_conv["CONV-34"]}
        self.assertEqual(arms["1w"]["base"]["stop_pct"], 0.30)
        self.assertEqual(arms["1w"]["arms"][0]["stop_pct"], 0.15)
        self.assertIsNone(arms["1wa"]["base"]["stop_pct"])
        self.assertEqual(arms["1wa"]["arms"][0]["stop_pct"], 0.15)
        self.assertIsNone(arms["s_1wlab"]["base"]["stop_pct"])
        self.assertEqual(arms["s_1wlab"]["arms"][0]["stop_pct"], 0.15)
        self.assertEqual(arms["s_rules_1w"]["base"]["horizon"], 54)
        self.assertEqual(arms["s_rules_1w"]["arms"][0]["horizon"], 27)

    def test_conv77_fleet_population_excludes_options(self):
        a = self.by_conv["CONV-77"][0]
        self.assertGreater(len(a["parents"]), 300)
        for bad in ("bilbo_options", "capitulation_options",
                    "investandbefree_dmac"):
            self.assertNotIn(bad, a["parents"])
        self.assertIn("CONV-77-PHASE-RERUN", a["note"])


if __name__ == "__main__":
    unittest.main()
