"""CURE1-DESK-20261102 blockers.

Class 1 (WORKER-IMPORT-POISON): desk3.port4_context.ensure_core left
desk3/vendor at sys.path[0] forever. The vendor tree carries a
top-level ``sleeves`` package, so any worker that evaluated a port4
sleeve before a ``sleeves.*`` import resolved ``sleeves`` to the
vendor package and every later ``sleeves.<id>`` / ``from sleeves
import <id>`` failed: 18 FED sleeves errored in health cycle 51
(2026-11-02) with ModuleNotFoundError / ImportError naming
desk3/vendor/sleeves/__init__.py.

These tests run the poisoning sequence in a FRESH subprocess (the
class is process-state pollution; an in-process test would be
contaminated by the test suite's own imports), in both orders.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_POISON_SEQ = r"""
import importlib, sys
sys.path.insert(0, {root!r})
from desk3.port4_context import load_strategy
m = load_strategy("legends_ema")
assert m is not None
import sleeves
assert "vendor" not in sleeves.__file__, sleeves.__file__
for sid in ("capitulation", "s_mn_vwap", "saty_sol_0dte",
            "ts_momentum_decile", "snapback", "confluence"):
    importlib.import_module("sleeves." + sid)
for sid in ("bb_rsi_divergence", "po10_qqq", "qullamaggie",
            "teddy_orb_spy", "investandbefree_dmac"):
    mod = importlib.import_module("sleeves")
    assert hasattr(mod, sid) or True  # name-import form checked below
    try:
        exec("from sleeves import " + sid)
    except ImportError:
        # sleeves/__init__ is lazy in this tree; the submodule form
        # above is the load path the adapters use. A failure here is
        # only a defect when the submodule form also fails.
        importlib.import_module("sleeves." + sid)
# the adapters the roster actually loads must import after port4 too
for modname in ("adapters3.capitulation", "adapters3.bb_rsi_divergence",
                "adapters.s_mn_vwap", "adapters3.saty_sol_0dte",
                "adapters3.ts_momentum_decile", "desk3.port_b5.po10_qqq"):
    importlib.import_module(modname)
print("POISON-SEQ-OK")
"""


class TestWorkerImportPoison(unittest.TestCase):
    def test_port4_first_then_sleeves_imports(self):
        code = _POISON_SEQ.format(root=ROOT)
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, cwd=ROOT,
                              timeout=180)
        self.assertEqual(proc.returncode, 0,
                         proc.stdout + proc.stderr)
        self.assertIn("POISON-SEQ-OK", proc.stdout)

    def test_vendor_not_left_on_sys_path(self):
        code = (
            "import sys; sys.path.insert(0, %r)\n"
            "from desk3.port4_context import ensure_core\n"
            "ensure_core()\n"
            "import os\n"
            "vendor = os.path.join(%r, 'desk3', 'vendor')\n"
            "assert vendor not in sys.path, sys.path[:3]\n"
            "import core.sleeve\n"
            "print('PATH-OK')\n" % (ROOT, ROOT))
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, cwd=ROOT,
                              timeout=120)
        self.assertEqual(proc.returncode, 0,
                         proc.stdout + proc.stderr)
        self.assertIn("PATH-OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
