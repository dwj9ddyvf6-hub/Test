"""GATE-EVIDENCE-DESTRUCTION + GATE-CONCURRENCY blockers (2026-11-11).

Pre-cure, run_regression_blockers.sh used the FIXED scratch path
$PWD/.gate_tmp: it rm -rf'd that dir at start and again from the
EXIT/INT/TERM trap. Two defects followed:

1. GATE-CONCURRENCY: two concurrent gate runs shared one scratch
   dir (and one unittest.log), colliding and deleting each other's
   temp space mid-run.
2. GATE-EVIDENCE-DESTRUCTION: unittest.log lived inside the scratch
   dir, so the trap destroyed a failing gate's own evidence. This is
   exactly how the LAND-SHEN-20261110 first-run failure (Ran 1,859
   failures=2 errors=1) lost its log.

Cure pinned here: the scratch dir is per-run unique (mktemp -d), the
trap removes only that per-run scratch dir, and on EVERY run (pass
or fail) the script writes a durable receipt OUTSIDE the scratch
dir: the full unittest log plus a one-line JSON proof row appended
to state/gate_receipts/receipts.jsonl (run id, UTC timestamp, tree
hash, wall seconds, unittest's "Ran N tests in Xs" line, exit code).
The GATE-MASK-20261026 exit-code contract is preserved: rc is
captured from unittest, the tail is printed, exit "$rc".

Fail direction: against the pre-cure script (GATE_RECEIPTS_GATE
pointing at `git show HEAD:run_regression_blockers.sh`) the text
tests fail (fixed path present, no mktemp, no receipts) and the
behavioral tests fail (no receipts dir is ever created).
"""
import glob
import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.environ.get(
    "GATE_RECEIPTS_GATE",
    os.path.join(HERE, "run_regression_blockers.sh"))

FAILING = (
    "import unittest\n"
    "class T(unittest.TestCase):\n"
    "    def test_x(self):\n"
    "        self.fail('deliberate')\n"
)
PASSING = (
    "import unittest\n"
    "class T(unittest.TestCase):\n"
    "    def test_x(self):\n"
    "        self.assertTrue(True)\n"
)


def _script_text():
    with open(GATE) as fh:
        return fh.read()


def _make_tree(blocker_src):
    tmp = tempfile.mkdtemp(prefix="gate_receipts_")
    shutil.copy(GATE, os.path.join(tmp, "run_regression_blockers.sh"))
    os.mkdir(os.path.join(tmp, "tests"))
    with open(os.path.join(tmp, "tests", "test_dummy_blockers.py"), "w") as fh:
        fh.write(blocker_src)
    return tmp


def _run_gate(tree):
    proc = subprocess.run(
        ["sh", os.path.join(tree, "run_regression_blockers.sh")],
        capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout


def _receipt_rows(tree):
    ledger = os.path.join(tree, "state", "gate_receipts", "receipts.jsonl")
    if not os.path.exists(ledger):
        return []
    with open(ledger) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _receipt_logs(tree):
    return sorted(glob.glob(
        os.path.join(tree, "state", "gate_receipts", "unittest-*.log")))


class TestGateScriptText(unittest.TestCase):
    def test_per_run_temp_is_not_the_fixed_path(self):
        text = _script_text()
        self.assertNotIn('GATE_TMP="$PWD/.gate_tmp"', text,
                         "gate still uses the fixed .gate_tmp scratch path")
        self.assertIn("mktemp -d", text,
                      "gate does not create a per-run temp dir with mktemp -d")
        self.assertIn("GATE_TMP=", text)
        gate_tmp_line = [ln for ln in text.splitlines()
                         if ln.startswith("GATE_TMP=")][0]
        self.assertIn("mktemp", gate_tmp_line,
                      "GATE_TMP is not the mktemp per-run dir: %r" % gate_tmp_line)

    def test_receipt_target_exists_and_is_outside_scratch(self):
        text = _script_text()
        self.assertIn("state/gate_receipts", text,
                      "no durable receipts dir named in the gate script")
        self.assertIn("receipts.jsonl", text,
                      "no receipts ledger named in the gate script")
        for line in text.splitlines():
            if line.startswith(("RECEIPTS_DIR=", "RECEIPT_LOG=",
                                "RECEIPTS_LEDGER=")):
                self.assertNotIn("GATE_TMP", line,
                                 "receipt target is inside the scratch "
                                 "temp: %r" % line)
                self.assertTrue(
                    "gate_receipts" in line or "RECEIPTS_DIR" in line,
                    "receipt target does not point at the receipts "
                    "dir: %r" % line)
        # The full unittest log is copied to the receipt log.
        self.assertIn('cp "$GATE_LOG" "$RECEIPT_LOG"', text,
                      "gate never copies the unittest log to a receipt")

    def test_trap_removes_scratch_never_receipt(self):
        text = _script_text()
        trap_lines = [ln.strip() for ln in text.splitlines()
                      if ln.strip().startswith("trap ")]
        self.assertTrue(trap_lines, "gate script has no trap")
        joined = " ".join(trap_lines)
        self.assertIn("GATE_TMP", joined,
                      "trap no longer cleans the scratch temp: %r" % joined)
        self.assertNotIn("RECEIPT", joined,
                         "trap removes the receipt target: %r" % joined)
        self.assertNotIn("gate_receipts", joined,
                         "trap removes the receipts dir: %r" % joined)

    def test_gate_mask_exit_contract_preserved(self):
        text = _script_text()
        self.assertIn('|| rc=$?', text,
                      "unittest exit code is no longer captured into rc")
        self.assertIn('tail -5 "$GATE_LOG"', text,
                      "human tail print was dropped")
        self.assertIn('exit "$rc"', text,
                      "script no longer re-raises unittest's exit code")


class TestGateReceiptsBehavior(unittest.TestCase):
    def test_passing_run_writes_receipt(self):
        tree = _make_tree(PASSING)
        try:
            rc, out = _run_gate(tree)
            self.assertEqual(rc, 0, "gate failed a passing tree: %r" % out)
            rows = _receipt_rows(tree)
            self.assertEqual(len(rows), 1,
                             "passing run wrote no receipt row: %r" % rows)
            row = rows[0]
            for field in ("run_id", "timestamp_utc", "tree_hash",
                          "wall_seconds", "ran_line", "exit_code", "log"):
                self.assertIn(field, row, "receipt row missing %s" % field)
            self.assertEqual(row["exit_code"], 0)
            self.assertIsInstance(row["wall_seconds"], int)
            self.assertGreaterEqual(row["wall_seconds"], 0)
            self.assertTrue(row["ran_line"].startswith("Ran "),
                            "ran_line is not unittest's summary: %r"
                            % row["ran_line"])
            logs = _receipt_logs(tree)
            self.assertEqual(len(logs), 1,
                             "passing run preserved no receipt log")
            with open(logs[0]) as fh:
                body = fh.read()
            self.assertIn("Ran ", body)
            self.assertIn("OK", body)
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    def test_failing_run_preserves_its_evidence(self):
        tree = _make_tree(FAILING)
        try:
            rc, out = _run_gate(tree)
            self.assertNotEqual(rc, 0,
                                "gate masked a failing blocker: %r" % out)
            rows = _receipt_rows(tree)
            self.assertEqual(len(rows), 1,
                             "failing run wrote no receipt row (its "
                             "evidence was destroyed): %r" % rows)
            self.assertNotEqual(rows[0]["exit_code"], 0)
            logs = _receipt_logs(tree)
            self.assertEqual(len(logs), 1,
                             "failing run's unittest log did not survive "
                             "the trap")
            with open(logs[0]) as fh:
                body = fh.read()
            self.assertIn("FAILED", body)
            self.assertIn("deliberate", body)
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    def test_two_runs_get_distinct_receipts_and_scratch_is_cleaned(self):
        tree = _make_tree(PASSING)
        try:
            rc1, _ = _run_gate(tree)
            rc2, _ = _run_gate(tree)
            self.assertEqual((rc1, rc2), (0, 0))
            rows = _receipt_rows(tree)
            self.assertEqual(len(rows), 2,
                             "second run did not append its own receipt")
            self.assertNotEqual(rows[0]["run_id"], rows[1]["run_id"],
                                "concurrent-capable run ids collide")
            self.assertEqual(len(_receipt_logs(tree)), 2,
                             "per-run receipt logs collide/overwrite")
            leftovers = glob.glob(os.path.join(tree, ".gate_tmp", "run.*"))
            self.assertEqual(leftovers, [],
                             "per-run scratch dirs were not cleaned: %r"
                             % leftovers)
        finally:
            shutil.rmtree(tree, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
