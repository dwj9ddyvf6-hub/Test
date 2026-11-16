"""CONFIG-TRUTH-20261116 blockers (Mon 2026-11-16 total audit,
Phase E LOGICAL + OPEN row 11).

Defects:
(a) przm_fade_edges: the live module of record is
    adapters3.przm_fade_edges (config/sleeves.json "module"), and its
    docstring claimed "PARKED: the options_chain producer serves
    delta-only rows (no greeks, no open interest)". The config of
    record contradicts it: the row is parked=false, unparked
    2026-11-14 (FEED80-PRZM-20261114) because chain rows now carry
    gamma+OI. Cure: the docstring states the live truth.
(b) mk_zerodte_spx: sleeves/milkman_0dte.py defines
    CAPITAL = 1_000_000.0 once and never consumes it (sizing in that
    module is PREMIUM_PER_TRADE in whole contracts; live orders are
    governed by the dispatcher's per-slice buying-power check
    against the $10,000 config slice), and its config row carried a
    stale install-era inert_reason ("SPX 0DTE chain not available:
    PARKED + UNFED at install 2026-10-27 ... no delta/greeks").
    Cure: CAPITAL is annotated INERT with what actually governs,
    and the config row drops inert_reason and states the true state
    in entry_blocked_reason: ARMED-PROVEN, entry blocked only by
    the milkman_0dte port gap (the Milkman intraday study was never
    ported). The port itself is a separate lane and is NOT attempted
    here; no sizing, value, or strategy logic changes.

Fail direction: the truthfulness assertions fail on the pre-cure
tree and pass on the cured tree. The config-row, AST-inertness, and
value pins pass both ways by design (they prove the annotations are
true and that nothing else moved).
"""
import ast
import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
CFG = os.path.join(ROOT, "config", "sleeves.json")
PRZM_ADAPTER3 = os.path.join(ROOT, "adapters3", "przm_fade_edges.py")
MILKMAN = os.path.join(ROOT, "sleeves", "milkman_0dte.py")


def _row(sid):
    with open(CFG) as fh:
        doc = json.load(fh)
    (r,) = [s for s in doc["sleeves"] if s["id"] == sid]
    return r


def _docstring(path):
    with open(path) as fh:
        tree = ast.parse(fh.read())
    return ast.get_docstring(tree) or ""


class TestPrzmFadeDocstringTruth(unittest.TestCase):
    def test_config_row_is_live_module_of_record(self):
        # Pin (passes both ways): the config of record the docstring
        # must be truthful to.
        r = _row("przm_fade_edges")
        self.assertEqual(r["module"], "adapters3.przm_fade_edges")
        self.assertFalse(r["parked"])
        self.assertIn("UNPARKED 2026-11-14", r["params"]["parked_reason"])
        self.assertIn("gamma+OI", r["params"]["parked_reason"])

    def test_docstring_does_not_claim_parked_or_delta_only(self):
        doc = _docstring(PRZM_ADAPTER3)
        self.assertIsNone(re.search(r"\bPARKED\b\s*:", doc), doc)
        self.assertNotIn("delta-only", doc)
        self.assertNotIn("no greeks, no open interest", doc)

    def test_docstring_states_live_truth(self):
        doc = _docstring(PRZM_ADAPTER3)
        self.assertIn("parked=false", doc)
        self.assertIn("2026-11-14", doc)
        self.assertIn("gamma+OI", doc)


class TestMilkmanCapitalTruth(unittest.TestCase):
    def _capital_block(self):
        with open(MILKMAN) as fh:
            lines = fh.read().splitlines()
        (idx,) = [i for i, ln in enumerate(lines)
                  if ln.startswith("CAPITAL =")]
        return lines, idx

    def test_capital_annotated_inert_and_what_governs(self):
        lines, idx = self._capital_block()
        # The contiguous comment block directly above the assignment.
        block = []
        j = idx - 1
        while j >= 0 and lines[j].lstrip().startswith("#"):
            block.append(lines[j])
            j -= 1
        annotation = "\n".join(reversed(block))
        self.assertIn("INERT", annotation)
        self.assertIn("dispatcher", annotation)
        self.assertIn("buying-power", annotation)
        self.assertIn("PREMIUM_PER_TRADE", annotation)

    def test_capital_never_consumed_in_module(self):
        # Truth pin (passes both ways): the INERT annotation is a
        # fact, not a hope -- exactly one assignment, zero loads of
        # the name anywhere in sleeves/milkman_0dte.py.
        with open(MILKMAN) as fh:
            tree = ast.parse(fh.read())
        assigns = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "CAPITAL"
                           for t in n.targets)]
        loads = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Name) and n.id == "CAPITAL"
                 and isinstance(n.ctx, ast.Load)]
        self.assertEqual(len(assigns), 1)
        self.assertEqual(loads, [])

    def test_capital_value_unchanged(self):
        # Pin (passes both ways): annotation only, no sizing change.
        with open(MILKMAN) as fh:
            tree = ast.parse(fh.read())
        (assign,) = [n for n in ast.walk(tree)
                     if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "CAPITAL"
                             for t in n.targets)]
        self.assertEqual(ast.literal_eval(assign.value), 1_000_000.0)


class TestMkZerodteConfigTruth(unittest.TestCase):
    def test_no_stale_inert_reason(self):
        r = _row("mk_zerodte_spx")
        self.assertNotIn("inert_reason", r["params"])

    def test_stale_install_claims_absent_from_params(self):
        r = _row("mk_zerodte_spx")
        blob = json.dumps(r["params"])
        self.assertNotIn("PARKED + UNFED at install", blob)
        self.assertNotIn("no delta/greeks on this account tier", blob)

    def test_config_states_armed_proven_entry_blocked_by_port_gap(self):
        # MILKMAN-0DTE-PORT-20261116 supersedes the port-gap half of
        # this pin: the intraday study is now ported, so the config
        # of record must state the closure, not the old block. The
        # ARMED-PROVEN half of the original pin stands unchanged.
        r = _row("mk_zerodte_spx")
        self.assertFalse(r["parked"])
        reason = r["params"].get("entry_blocked_reason", "")
        self.assertIn("ARMED-PROVEN", reason)
        self.assertIn("MILKMAN-0DTE-PORT-20261116", reason)
        self.assertIn("intraday", reason)
        self.assertNotIn("was never ported", reason)
        self.assertNotIn("lane_signals stay empty", reason)


if __name__ == "__main__":
    unittest.main()
