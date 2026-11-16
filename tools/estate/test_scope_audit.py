#!/usr/bin/env python3
"""Tests for scope_audit.py. Builds throwaway git repos in temp dirs."""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope_audit  # noqa: E402


def run(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, *args], check=True,
                   capture_output=True, text=True)


class ScopeAuditTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        run(self.repo, "init", "-q")
        run(self.repo, "config", "user.email", "test@example.com")
        run(self.repo, "config", "user.name", "Test")
        self.write("auth/login.py", "def login(user):\n    return user\n")
        self.write("auth/session.py", "def session():\n    return 1\n")
        self.write("billing/invoice.py", "def invoice():\n    return 2\n")
        self.write("requirements.txt", "requests==2.31.0\n")
        run(self.repo, "add", "-A")
        run(self.repo, "commit", "-qm", "base")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, rel: str, content: str) -> None:
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def commit(self) -> None:
        run(self.repo, "add", "-A")
        run(self.repo, "commit", "-qm", "change")

    def audit(self, intent: str, **kw) -> dict:
        return scope_audit.audit(self.repo, "HEAD~1", "HEAD", intent,
                                 kw.get("allowed", []),
                                 kw.get("max_hunk", 300),
                                 kw.get("max_areas", 4))

    def categories(self, report: dict) -> set[str]:
        return {f["category"] for f in report["findings"]}


class TestCleanDiff(ScopeAuditTestCase):
    def test_clean_diff_passes(self) -> None:
        self.write("auth/login.py", "def login(user):\n    return user.strip()\n")
        self.commit()
        report = self.audit("Improve auth login handling")
        self.assertTrue(report["clean"], report["findings"])
        self.assertEqual(report["keep"], ["auth/login.py"])

    def test_cli_exit_zero_on_clean(self) -> None:
        self.write("auth/login.py", "def login(user):\n    return user.strip()\n")
        self.commit()
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "scope_audit.py"),
             self.repo, "HEAD~1", "HEAD", "--intent",
             "Improve auth login handling"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CLEAN", proc.stdout)


class TestUnrelatedPath(ScopeAuditTestCase):
    def test_unrelated_path_flagged(self) -> None:
        self.write("auth/login.py", "def login(user):\n    return user.strip()\n")
        self.write("billing/invoice.py", "def invoice():\n    return 99\n")
        self.commit()
        report = self.audit("Improve auth login handling")
        self.assertFalse(report["clean"])
        self.assertIn("unrelated-path", self.categories(report))
        flagged = {f["path"] for f in report["findings"]
                   if f["category"] == "unrelated-path"}
        self.assertEqual(flagged, {"billing/invoice.py"})

    def test_allowed_list_covers_path(self) -> None:
        self.write("billing/invoice.py", "def invoice():\n    return 99\n")
        self.commit()
        report = self.audit("Improve auth login handling",
                            allowed=["billing"])
        self.assertNotIn("unrelated-path", self.categories(report))


class TestDependency(ScopeAuditTestCase):
    def test_dependency_addition_flagged(self) -> None:
        self.write("requirements.txt",
                   "requests==2.31.0\nflask==3.0.0\n")
        self.commit()
        report = self.audit("Add flask to requirements for the web layer")
        self.assertIn("new-dependency", self.categories(report))
        detail = " ".join(f["detail"] for f in report["findings"]
                          if f["category"] == "new-dependency")
        self.assertIn("flask", detail)

    def test_lockfile_change_flagged(self) -> None:
        self.write("auth/login.py", "def login(user):\n    return user.strip()\n")
        self.write("go.sum", "example.com/mod v1.0.0 h1:abc=\n")
        self.commit()
        report = self.audit("Improve auth login handling")
        self.assertIn("new-dependency", self.categories(report))


class TestFormattingOnly(ScopeAuditTestCase):
    def test_formatting_only_flagged(self) -> None:
        # Reindent only: same tokens, different leading whitespace.
        self.write("auth/session.py", "def session():\n        return 1\n")
        self.commit()
        report = self.audit("Tidy auth session module")
        self.assertIn("formatting-only", self.categories(report))


class TestOtherFlags(ScopeAuditTestCase):
    def test_config_edit_flagged(self) -> None:
        self.write(".github/workflows/ci.yml", "name: ci\non: [push]\n")
        self.commit()
        report = self.audit("Improve auth login handling",
                            allowed=[".github"])
        self.assertIn("config-or-ci", self.categories(report))

    def test_public_api_rename_flagged(self) -> None:
        self.write("auth/login.py", "def sign_in(user):\n    return user\n")
        self.commit()
        report = self.audit("Rename auth login entry point")
        self.assertIn("public-api-rename", self.categories(report))

    def test_usage_error_exit_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "scope_audit.py"),
             self.repo, "no-such-ref", "HEAD", "--intent", "anything"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
