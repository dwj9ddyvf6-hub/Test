"""GATE-MASK-20261026 blocker: the regression gate must propagate
unittest's exit code.

Before the cure, run_regression_blockers.sh piped unittest through
`| tail -5` under POSIX sh (no pipefail), so the script's exit status
was tail's -- always 0 -- and the gate could not return failure no
matter how many blockers failed. This test runs the REAL gate script
against a temp mini-tree: a failing dummy blocker must make the
script exit nonzero, and a passing one must make it exit 0.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(HERE, "run_regression_blockers.sh")

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


def _run_gate(blocker_src):
    tmp = tempfile.mkdtemp(prefix="gate_mask_")
    try:
        shutil.copy(GATE, os.path.join(tmp, "run_regression_blockers.sh"))
        os.mkdir(os.path.join(tmp, "tests"))
        with open(os.path.join(tmp, "tests", "test_dummy_blockers.py"), "w") as fh:
            fh.write(blocker_src)
        proc = subprocess.run(
            ["sh", os.path.join(tmp, "run_regression_blockers.sh")],
            capture_output=True, text=True, timeout=120)
        return proc.returncode, proc.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class TestGateExitCodePropagation(unittest.TestCase):
    def test_failing_blocker_makes_gate_exit_nonzero(self):
        rc, out = _run_gate(FAILING)
        self.assertNotEqual(rc, 0,
                            "gate masked a failing blocker (rc=0); tail output: %r" % out)
        self.assertIn("FAILED", out)

    def test_passing_blocker_makes_gate_exit_zero(self):
        rc, out = _run_gate(PASSING)
        self.assertEqual(rc, 0, "gate failed a passing tree; tail output: %r" % out)
        self.assertIn("OK", out)


if __name__ == "__main__":
    unittest.main()
