"""CONSTANTS-PROVENANCE-20261116 verification (annotation-only lane).

Asserts every constant this lane marked carries a resolvable provenance
pointer: the CONSTANTS-PROVENANCE-20261116 id in the same file, plus the
named source token for that mark. Pure annotation: no value is asserted
changed — the marked values themselves are pinned here at their
pre-lane values, so a future value change fails this test loudly.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARK = "CONSTANTS-PROVENANCE-20261116"

# (file, marker token that must appear, value token that must be unchanged)
CASES = [
    ("desk3/aster_b2.py", "FIDELITY-LEDGER", "FEE_PER_CONTRACT = 0.65"),
    ("desk3/aster_batch3.py", "options_rules.json", "hold_sessions=5"),
    ("desk3/aster_crypto.py", "r19_crypto.py", "hold_h=96"),
    ("desk3/aster_batch7.py", "r19_crypto.py", "hold_h=96"),
    ("desk3/aster_b12_crypto.py", "r19_crypto.py", "hold_h=96"),
    ("desk3/aster_batch13.py", "r19_crypto.py", "deadline_h=96"),
    ("sleeves/milkman_0dte.py", "PROVENANCE.md", "TARGET_DELTA = 0.40"),
    ("sleeves/przm_fade_edges.py", "PRZM-RECREATION-SPEC-2026-10-29", "EDGE_TOL_FRAC = 0.0005"),
    ("sleeves/przm_zero.py", "PRZM-RECREATION-BUILD.md", "ENTRY_SCORE = 25"),
    ("sleeves/qullamaggie.py", "qullamaggie_sleeve.py", "RISK_FRACTION = 0.0035"),
    ("sleeves/qullamaggie_paper.py", "aurelia_common.BUDGETS", "BUDGET_USD = 100_000.0"),
    ("desk3/lazarus_midna.py", "catalog 15% stop", "stop=0.15"),
]

# PORT-PINNED files (TOTAL-AUDIT-PIN-REBASE-20261116 (6)): these
# eight files carry port byte-fidelity pins (test_port_batch1/2/3
# and test_port_b7 blockers) guaranteeing byte identity with their
# v2 sources. The tranche marks annotated them and broke those
# pins on the final merged gate; the marks were removed and the
# pins restored byte-exact. Their provenance lives in
# constants-ledger-20261116.md (each file is named there with its
# full row); the checks below pin the value in the file, the
# mark's ABSENCE from the file, and the file's presence in the
# ledger.
PINNED_CASES = [
    ("sleeves/bb_rsi_divergence.py", "BAR_MAX_AGE_S = 10.0 * 60.0"),
    ("sleeves/beatendown.py", "CUT_LAM = 0.17647058823529413"),
    ("sleeves/confluence.py", "SELECT_MIN_COUNT = 2"),
    ("sleeves/tensor_red_dip.py", "FEAR_QQQ_PCT = -1.5"),
    ("sleeves/saty_magnum.py", "SNAP_M10 = -100.0"),
    ("sleeves/free_etf.py", "weights = {selected: 0.25}"),
    ("sleeves/free_kraken_ada_crowded.py", "int(0.75 * (len(ranked) - 1))"),
    ("desk3/strategies/free_kraken_link_crowded.py", "int(0.75 * (len(ranked) - 1))"),
]


DERIV_MARK = "CONSTANTS-DERIVATIONS-20261116"

# Route-4 derivation marks (CONSTANTS-DERIVATIONS-20261116 lane):
# (file, derivation token that must appear, value token unchanged)
DERIV_CASES = [
    ("desk3/dispatcher.py", "bp_buffer_frac = 0.02", 's.get("bp_buffer_frac", 0.02)'),
    ("desk3/dispatcher.py", "signal-to-fill price", '"bp_buffer_frac": 0.02'),
    ("desk3/aster_b2.py", "DELIBERATE CONSERVATIVE COST MODEL", "FEE_PER_CONTRACT = 0.65"),
    ("desk3/aster_b2.py", "$0.0403/contract/side", "FEE_PER_CONTRACT = 0.65"),
    ("desk3/lazarus_midna.py", "band 10.0/20.0 DERIVED", "(10.0<=price<=20.0)"),
    ("desk3/lazarus_midna.py", "breadth_min 0.50 DERIVED", "float(b)<0.50"),
    ("desk3/lazarus_midna.py", "vix 12.0/25.0 DERIVED", "(12.0<=float(v)<=25.0)"),
    ("desk3/lazarus_midna.py", "smh_calm_window 21 DERIVED", "len(smh)>=21"),
    ("desk3/lazarus_midna.py", "smh_calm_max_move 0.05 DERIVED", "abs(r)>0.05"),
    ("desk3/lazarus_midna.py", "fire_age_days 10 DERIVED", "age_d>10"),
    ("sleeves/s_mn_kronos.py", "one calendar week of freshness", "MAX_FIRE_AGE_DAYS = 7"),
    ("sleeves/s_mn_moonshot.py", "one calendar week of freshness", "MAX_FIRE_AGE_DAYS = 7"),
    ("sleeves/laz8_opt.py", "unrepresentative of executable cost", "MAX_SPREAD_FRAC = 0.30"),
]

# Files whose fire-age marks must name the 7-vs-10 inconsistency.
FIRE_AGE_FILES = [
    "desk3/lazarus_midna.py",
    "sleeves/s_mn_kronos.py",
    "sleeves/s_mn_moonshot.py",
]


class TestConstantsProvenance20261116(unittest.TestCase):
    def test_every_mark_carries_id_pointer_and_unchanged_value(self):
        for rel, token, value in CASES:
            text = (ROOT / rel).read_text()
            self.assertIn(MARK, text, f"{rel} lost the provenance id")
            self.assertIn(token, text, f"{rel} lost its source pointer {token!r}")
            self.assertIn(value, text, f"{rel} value changed: {value!r}")

    def test_port_pinned_files_carry_provenance_in_the_ledger(self):
        ledger = (ROOT / "constants-ledger-20261116.md").read_text()
        for rel, value in PINNED_CASES:
            text = (ROOT / rel).read_text()
            self.assertIn(value, text, f"{rel} value changed: {value!r}")
            self.assertNotIn(MARK, text,
                             f"{rel} is port byte-pinned; its "
                             f"provenance mark belongs in the ledger")
            self.assertIn(rel, ledger,
                          f"{rel} lost its ledger provenance row")

    def test_every_derivation_mark_carries_id_basis_and_unchanged_value(self):
        for rel, token, value in DERIV_CASES:
            text = (ROOT / rel).read_text()
            self.assertIn(DERIV_MARK, text, f"{rel} lost the derivations id")
            self.assertIn(token, text, f"{rel} lost its derivation token {token!r}")
            self.assertIn(value, text, f"{rel} value changed: {value!r}")

    def test_bp_buffer_mark_carries_origin_and_falsifier(self):
        text = (ROOT / "desk3/dispatcher.py").read_text()
        self.assertIn("638b70c", text)
        self.assertIn("no source derivation", text)
        self.assertIn("intent-to-fill cost", text)
        self.assertIn("re-derived from that measurement", text)

    def test_fire_age_inconsistency_named_on_both_sides(self):
        for rel in FIRE_AGE_FILES:
            text = (ROOT / rel).read_text()
            self.assertIn("INCONSISTENCY NAMED", text,
                          f"{rel} fire-age mark does not name the 7-vs-10 inconsistency")
            self.assertIn("NOT harmonized", text,
                          f"{rel} fire-age mark does not state values were not harmonized")

    def test_saty_sol_pin_unchanged_and_unmarked_by_this_lane(self):
        import hashlib
        digest = hashlib.sha256((ROOT / "sleeves/saty_sol.py").read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc",
        )


if __name__ == "__main__":
    unittest.main()
