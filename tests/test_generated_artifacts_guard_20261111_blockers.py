"""EC-B11 (desk half) / NG-1 blockers (2026-11-11, FIX-ALL WAVE).

NG-1's generated-artifact guard (canon tools/validate_repo.py:
generated_artifact_errors) was adopted into the doctrine repo but
never into the desk gate. This test adopts it into the desk gate by
the gate's own discovery pattern (test_*_blockers.py): the gate now
fails the day a generated artifact (__pycache__/ or a .pyc/.pyo/.pyd
path) becomes tracked in the desk tree. The estate state was verified
clean at adoption (0 tracked generated artifacts).

The clean-export directory-keyed guard tightening (the other half of
EC-B11) lives on the export path's own surface and is NOT cured here;
it stays open under its owner in the wave record.

Fail direction: the predicate tests below fail against a predicate
that lets a generated path through; the live test fails the gate if
a generated artifact is ever committed.
"""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GENERATED_SUFFIXES = (".pyc", ".pyo", ".pyd")


def generated_artifact_paths(paths):
    """Mirror of canon's generated_artifact_errors, path form."""
    bad = []
    for path in paths:
        parts = path.replace(os.sep, "/").split("/")
        if "__pycache__" in parts or path.endswith(GENERATED_SUFFIXES):
            bad.append(path)
    return bad


class TestGeneratedArtifactPredicate(unittest.TestCase):
    def test_generated_paths_are_flagged(self):
        bad = generated_artifact_paths(
            [
                "desk3/__pycache__/cycle.cpython-312.pyc",
                "tools/leftover.pyc",
                "deep/mod.pyo",
                "deep/mod.pyd",
                "desk3/cycle.py",
                "tests/test_gate_mask_20261026_blockers.py",
            ]
        )
        self.assertEqual(
            bad,
            [
                "desk3/__pycache__/cycle.cpython-312.pyc",
                "tools/leftover.pyc",
                "deep/mod.pyo",
                "deep/mod.pyd",
            ],
        )

    def test_clean_paths_pass(self):
        self.assertEqual(
            generated_artifact_paths(["a/b.py", "c/d.jsonl", "e/__init__.py"]),
            [],
        )


class TestDeskTreeHasNoTrackedGeneratedArtifacts(unittest.TestCase):
    def test_live_tree_is_clean(self):
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=HERE,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked = [line for line in out.stdout.splitlines() if line.strip()]
        self.assertEqual(generated_artifact_paths(tracked), [])


if __name__ == "__main__":
    unittest.main()
