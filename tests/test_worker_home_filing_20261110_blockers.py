"""WORKER-HOME-FILING-20261110 blockers (desk side).

Root cause: desk pool workers run with HOME set to the desk state
root by design (desk3/pool.py spawn env), so any module-level path
built with os.path.expanduser("~") resolves into the state tree,
not the real workspace. adapters3/em_1587.py built its permanent
filing log path that way, so every expected-move filing from
2026-11-02 onward landed in a shadow ledger at
state/workspace/femto-lean/state/ledger.jsonl while the permanent
ledger the Expected Move Map refresh reads stayed frozen at
session 2026-11-04. The sleeve journal reported "filed" the whole
time, because the write itself succeeded, into the wrong file.

Cure pinned here: the filing path is anchored to the module's own
tree (two levels up from adapters3/, then femto-lean/state), with
no dependence on the process HOME.

On the pre-cure tree: test 1 fails (the default FILING_LOG_PATH
differs from the permanent ledger), test 2 fails (importing the
module under a worker-style HOME yields a state-root path).
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PERMANENT = os.path.join(os.path.dirname(ROOT),
                         "femto-lean", "state", "ledger.jsonl")


class WorkerHomeFiling(unittest.TestCase):
    def test_filing_path_is_the_permanent_ledger(self):
        sys.path.insert(0, ROOT)
        import adapters3.em_1587 as mod
        self.assertEqual(os.path.abspath(mod.FILING_LOG_PATH),
                         os.path.abspath(PERMANENT))

    def test_filing_path_ignores_process_home(self):
        env = dict(os.environ)
        env["HOME"] = os.path.join(ROOT, "state")
        env["PYTHONPATH"] = ROOT
        out = subprocess.run(
            [sys.executable, "-c",
             "from adapters3.em_1587 import FILING_LOG_PATH;"
             "print(FILING_LOG_PATH)"],
            env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-500:])
        self.assertEqual(os.path.abspath(out.stdout.strip()),
                         os.path.abspath(PERMANENT))

    def test_source_has_no_home_relative_filing_path(self):
        src = open(os.path.join(ROOT, "adapters3", "em_1587.py"),
                   encoding="utf-8").read()
        self.assertNotIn('expanduser(\n    "~/workspace/femto-lean', src)
        self.assertNotIn('expanduser("~/workspace/femto-lean', src)


if __name__ == "__main__":
    unittest.main()
