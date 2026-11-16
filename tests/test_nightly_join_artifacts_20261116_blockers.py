"""Regression blockers: NIGHTLY-JOIN-ARTIFACTS-20261116 (2026-11-16).

Defect class: CONV-86 (LS7) was BLOCKED-ON-WIRING because the
nightly forecast-ledger plus bars join produced no artifact the
desk can read (the only record was the historical 6-row
computation in LEAD-STACKING.md); CONV-87's LS8 conditioner arm
rides the same join and had no accrual surface; CONV-104 was
BLOCKED-ON-WIRING because the night-study panel was not a
desk-readable source and the AA119 residue set was enumerated
in no desk-readable file.

Cure (this landing):
- desk3/nightly_join.py: the ONE join (historical reproduction
  and forward accrual share every definition), writing
  state/nightly_join/latest.json nightly.
- config/conversion_shadow_20261115.json + desk3/
  conversion_shadow.py: CONV-86/87 registered as FORECAST_JOIN
  arms grading the join artifact, falsifiers and kill rules
  byte-identical to their Conversion Register rows.
- midna-book/tools/night_panel_publish.py: the night study
  publishes its panel (universe, date, membership) to
  state/night_panel/latest.json, residue enumerable from it.

Fail direction: on the pre-cure tree desk3/nightly_join.py does
not exist, the registry carries no CONV-86/87 arms and the
publisher does not exist, so the import, registry and publisher
tests fail or error there; the saty_sol pin passes on both
trees by design (it pins what must not move).
"""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REGISTER = Path(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/"
    "CONVERSION-REGISTER-2026-11-15.jsonl").expanduser()
PUBLISHER = Path(
    "~/workspace/midna-book/tools/night_panel_publish.py"
).expanduser()
SATY_SOL_SHA256 = ("36e306c6294c385a5e9e96a89f8f4cd2753067597"
                   "c95efb1fea416cc08962bdc")


def _register_row(conv):
    for line in open(REGISTER):
        r = json.loads(line)
        if r["id"] == conv:
            return r
    raise AssertionError(f"{conv} not in the Conversion Register")


def _load_publisher():
    spec = importlib.util.spec_from_file_location(
        "night_panel_publish", PUBLISHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestHistoricalReproduction(unittest.TestCase):
    """The join reproduces the historical 6-row computation on
    its original inputs before it is trusted forward."""

    @classmethod
    def setUpClass(cls):
        from desk3 import nightly_join as nj
        cls.nj = nj
        cls.check = nj.historical_check()

    def test_join_yield_42_of_201(self):
        self.assertEqual(self.check["corpus_calls"], 201)
        self.assertEqual(self.check["joined"], 42)
        self.assertEqual(self.check["unjoined"], 159)

    def test_ls7_six_rows_exact(self):
        self.assertEqual(self.check["ls7_x7"],
                         {"n": 6, "mean_bp": 156.25,
                          "median_bp": 152.11, "win": 0.833,
                          "t": 2.08})
        rows = {(r["symbol"], r["call_date"], r["next_on_bp"])
                for r in self.check["qualifying_rows"]}
        self.assertEqual(rows, {
            ("OKLO", "2026-11-06", 80.68),
            ("ALAB", "2026-11-06", 436.79),
            ("NVDA", "2026-11-12", 223.54),
            ("SOXX", "2026-11-12", -107.75)})
        # 6 rows counting the corpus's own duplicate calls
        self.assertEqual(len(self.check["qualifying_rows"]), 6)

    def test_ls8_split_exact(self):
        ls8 = self.check["ls8"]
        self.assertEqual(ls8["macro"]["n"], 14)
        self.assertEqual(ls8["macro"]["mean_bp"], 34.01)
        self.assertEqual(ls8["macro"]["t"], 2.34)
        self.assertEqual(ls8["quiet"]["n"], 28)
        self.assertEqual(ls8["quiet"]["mean_bp"], -60.40)
        self.assertEqual(ls8["quiet"]["t"], -0.89)
        self.assertEqual(ls8["split_bp"], 94.41)

    def test_definitions_union_semantics(self):
        nj = self.nj
        self.assertEqual(nj.stack_cell("mixed_below", "bear_below"),
                         "joint_below")
        self.assertEqual(nj.stack_cell("mixed_above", "bull_above"),
                         "joint_bull")
        self.assertEqual(nj.stack_cell("mixed_below", "mixed_above"),
                         "mixed")
        self.assertIsNone(nj.stack_cell(None, "bear_below"))
        self.assertEqual(nj.window_state("macro_named"), "macro")
        self.assertEqual(nj.window_state("none_mentioned"), "quiet")
        self.assertIsNone(nj.window_state("earnings_named"))


class TestForwardJoin(unittest.TestCase):
    LEDGER = (
        "## 2026-11-16 20:30 ET · night study\n"
        "- Name calls: NVDA tests 200 by Fri, confidence low. "
        "ZZZZ fades, confidence low.\n"
        "- Tags NVDA: A02=bearish A03=oversold_lt30 A04=bear "
        "A05=mixed_below A06=bear_below A12=below_flip "
        "A15=mixed_or_neutral A21=qualitative_only "
        "A22=macro_named A23=ns A34=down_small A35=ns "
        "ORIGIN=book-study\n"
        "- Tags ZZZZ: A02=bearish A03=oversold_lt30 A04=bear "
        "A05=mixed_below A06=bear_below A12=ns A15=ns "
        "A21=ns A22=none_mentioned A23=ns A34=ns A35=ns "
        "ORIGIN=book-study\n"
        "- Tags index: A02=neutral_range A03=neutral_45_55 "
        "A04=mixed A05=bull_above A06=bull_above A12=ns "
        "A15=ns A21=numeric_band A22=macro_named A23=ns "
        "A34=ns A35=ns ORIGIN=book-study\n")

    def _root(self, tmp):
        root = Path(tmp)
        bars = root / "cache" / "bars" / "NVDA"
        bars.mkdir(parents=True)
        rows = [{"t": "2026-11-16", "o": 100.0, "c": 100.0},
                {"t": "2026-11-17", "o": 102.0, "c": 103.0},
                {"t": "2026-11-18", "o": 103.0, "c": 104.0}]
        with open(bars / "1Day.jsonl", "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        log = root / "FORECAST-LOG.md"
        log.write_text(self.LEDGER)
        return root, log

    def test_forward_join_qualifying_and_pending(self):
        from desk3 import nightly_join as nj
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self._root(tmp)
            res = nj.forward_join(str(root), str(log))
            self.assertEqual(res["calls_tagged"], 2)
            self.assertEqual(res["calls_no_bars"], 1)
            self.assertEqual(res["no_bars_symbols"], ["ZZZZ"])
            self.assertEqual(len(res["qualifying"]), 1)
            q = res["qualifying"][0]
            self.assertEqual(q["symbol"], "NVDA")
            self.assertEqual(q["window"], "macro")
            self.assertEqual(q["state"], "RESOLVED")
            self.assertEqual(q["next_date"], "2026-11-17")
            self.assertEqual(q["next_on_bp"], 200.0)
            self.assertEqual(res["ls7_resolved"]["n"], 1)
            self.assertEqual(res["ls8_resolved"]["macro"]["n"], 1)

    def test_run_writes_wellformed_artifact(self):
        from desk3 import nightly_join as nj
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self._root(tmp)
            _text, doc = nj.run(str(root), log_path=str(log))
            art = json.loads(
                (root / "state" / "nightly_join"
                 / "latest.json").read_text())
            self.assertEqual(art["qualifying_ls7_count"], 1)
            self.assertEqual(art["qualifying"][0]["symbol"], "NVDA")
            self.assertEqual(doc["ls8"]["macro"]["n"], 1)
            ledger = (root / "state" / "nightly_join"
                      / "ledger.jsonl").read_text().strip()
            self.assertEqual(json.loads(ledger)
                             ["qualifying_ls7_count"], 1)


class TestGraderArms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(
            (ROOT / "config/conversion_shadow_20261115.json")
            .read_text())
        cls.arms = {a["conv"]: a for a in cls.reg["arms"]
                    if a["conv"] in ("CONV-86", "CONV-87")}

    def test_arms_registered(self):
        self.assertEqual(set(self.arms), {"CONV-86", "CONV-87"})
        self.assertEqual(self.arms["CONV-86"]["kind"],
                         "FORECAST_JOIN")
        self.assertEqual(self.arms["CONV-87"]["kind"],
                         "FORECAST_JOIN")
        self.assertEqual(self.arms["CONV-86"]["grade_n"], 20)
        self.assertEqual(self.arms["CONV-87"]["grade_n"], 40)
        # SEGMENT-CONSTRUCTION-20261116 (amendment, dated estate
        # form): CONV-80's SEGMENT_GRADE arm landed later the same
        # day, census 55 -> 56; this pin follows the census.
        # 55 at this landing; 56 after SEGMENT-CONSTRUCTION-
        # 20261116 added CONV-80; 57 after CONV21-INVERT-20261116
        # added CONV-21 (carried by TOTAL-AUDIT-PIN-REBASE-
        # 20261116 (5)).
        self.assertEqual(len(self.reg["arms"]), 57)

    def test_falsifiers_byte_identical_to_register(self):
        for conv in ("CONV-86", "CONV-87"):
            row = _register_row(conv)
            self.assertEqual(self.arms[conv]["falsifier"],
                             row["falsifier"])
            self.assertEqual(self.arms[conv]["kill_rule"],
                             row["kill_rule"])

    def _grade(self, tmp, rows):
        from desk3 import conversion_shadow as cs
        root = Path(tmp)
        (root / "state" / "nightly_join").mkdir(parents=True)
        (root / "state" / "nightly_join" / "latest.json").write_text(
            json.dumps({"rows": rows,
                        "qualifying": [r for r in rows
                                       if r.get("qualifying_ls7")]}))
        book = cs.SeriesBook(str(root))
        out = {}
        for conv in ("CONV-86", "CONV-87"):
            out[conv] = cs.grade_forecast_join(
                book, None, self.arms[conv], [])
        return out

    def test_grader_accrues_then_grades(self):
        q = {"symbol": "NVDA", "state": "RESOLVED",
             "qualifying_ls7": True, "window": "macro",
             "next_on": 0.02}
        m = {"symbol": "AMD", "state": "RESOLVED",
             "qualifying_ls7": False, "window": "macro",
             "next_on": 0.01}
        qt = {"symbol": "MU", "state": "RESOLVED",
              "qualifying_ls7": False, "window": "quiet",
              "next_on": -0.01}
        with tempfile.TemporaryDirectory() as tmp:
            out = self._grade(tmp, [q, m, qt])
            self.assertEqual(out["CONV-86"]["state"], "ACCRUING")
            self.assertEqual(out["CONV-86"]["resolved_decisive"], 1)
            self.assertEqual(out["CONV-87"]["state"], "ACCRUING")
            self.assertEqual(out["CONV-87"]["split_bp"], 250.0)
        with tempfile.TemporaryDirectory() as tmp:
            rows = [dict(q) for _ in range(20)] + \
                   [dict(m) for _ in range(10)] + \
                   [dict(qt) for _ in range(20)]
            out = self._grade(tmp, rows)
            self.assertEqual(out["CONV-86"]["state"],
                             "GRADED_POSITIVE")
            self.assertEqual(out["CONV-86"]["mean_net_bp"], 195.0)
            self.assertEqual(out["CONV-87"]["state"],
                             "GRADED_POSITIVE")

    def test_grader_missing_artifact_accrues_named(self):
        from desk3 import conversion_shadow as cs
        with tempfile.TemporaryDirectory() as tmp:
            book = cs.SeriesBook(tmp)
            res = cs.grade_forecast_join(
                book, None, self.arms["CONV-86"], [])
            self.assertEqual(res["state"], "ACCRUING")
            self.assertIn("absent", res["detail"])


class TestPanelArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pub = _load_publisher()
        cls.doc = cls.pub.build_panel(date="2026-11-16")

    def test_panel_shape(self):
        from desk3.overnight_baskets import FOCUS29
        doc = self.doc
        self.assertEqual(doc["date"], "2026-11-16")
        self.assertEqual(doc["universe_n"], 100)
        self.assertEqual(doc["focus29"], list(FOCUS29))
        self.assertEqual(doc["residue"],
                         [s for s in doc["universe"]
                          if s not in FOCUS29])
        self.assertFalse(set(doc["residue"]) & set(FOCUS29))

    def test_aa119_residue_set_enumerable(self):
        doc = self.doc
        aa = [r["symbol"] for r in doc["aa119_least_watched_12"]]
        self.assertEqual(aa, ["EZPW", "DGII", "TTEK", "BKH", "NWE",
                              "TECH", "MO", "EXPD", "FIS", "ELF",
                              "CTVA", "ENS"])
        for s in aa:
            self.assertIn(s, doc["residue"])


class TestPinsUntouched(unittest.TestCase):
    def test_saty_sol_pin_unchanged(self):
        h = hashlib.sha256(
            (ROOT / "sleeves" / "saty_sol.py").read_bytes()
        ).hexdigest()
        self.assertEqual(h, SATY_SOL_SHA256)


if __name__ == "__main__":
    unittest.main()
