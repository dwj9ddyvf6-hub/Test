"""Exercise real Git snapshots and adversarial source boundaries, offline."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import repo_navigator as nav


class NavigationContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture Maintainer")
        self.git("config", "user.email", "fixture@example.invalid")
        for name, content in {
            "README.md": "# Fixture\nA committed research library.\n",
            "docs/source.md": "# Source\nfirst observation\nsecond observation\nfinal observation\n",
            "docs/other.md": "# Other\nneedle appears only in body\n",
            "docs/large.txt": "x" * 300,
        }.items():
            self.write(name, content)
        self.manifest = {"schema_version": 1, "repository_role": "Research fixture",
            "areas": {"(root)": {"summary": "Entry", "entrypoints": ["README.md"], "evidence_status": "guide"},
                      "docs": {"summary": "Records", "entrypoints": ["docs/source.md"], "evidence_status": "research"}},
            "routes": [{"id": "trace-research", "title": "Trace research evidence",
                        "aliases": ["research evidence"], "purpose": "Inspect original observations",
                        "reading_order": [{"path": "docs/source.md", "role": "Primary source"},
                                          {"path": "docs/other.md", "role": "Independent companion"}],
                        "checks": [{"command": "python offline_check.py", "scope": "example only", "side_effects": "none; not executed by navigator"}],
                        "next_queries": ["observation"], "evidence_boundary": "Historical source, not current runtime",
                        "related_routes": []}]}
        self.write("docs/REPOSITORY-MAP.json", json.dumps(self.manifest))
        self.git("add", ".")
        self.git("commit", "-qm", "Create fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode()

    def write(self, name, value):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value)

    def test_pinned_source_ignores_later_worktree_and_untracked_material(self):
        self.write("docs/source.md", "uncommitted replacement\n")
        self.write("private-untracked.md", "not in this corpus\n")
        pinned = nav.Snapshot(self.root, self.commit)
        working = nav.Snapshot(self.root, worktree=True)
        self.assertIn("first observation", pinned.text("docs/source.md")[0])
        self.assertEqual(working.text("docs/source.md")[0], "uncommitted replacement\n")
        self.assertNotIn("private-untracked.md", pinned.entries)
        self.assertNotIn("private-untracked.md", working.entries)
        self.assertNotEqual(pinned.excerpt("docs/source.md")["git_blob"], working.excerpt("docs/source.md")["git_blob"])

    def test_line_provenance_and_full_source_digest_survive_excerpt(self):
        source = nav.Snapshot(self.root)
        part = source.excerpt("docs/source.md", 2, 2)
        self.assertEqual(part["content"], "first observation\nsecond observation\n")
        self.assertEqual((part["start_line"], part["end_line"], part["next_line"]), (2, 3, 4))
        self.assertFalse(part["complete_file"])
        self.assertEqual(part["git_blob"], self.git("rev-parse", "HEAD:docs/source.md").strip())

    def test_packet_has_hard_content_budget_and_honest_omissions(self):
        result = nav.packet(nav.Snapshot(self.root), "trace-research", 30)
        self.assertLessEqual(result["content_characters"], 30)
        self.assertEqual(result["content_characters"], sum(len(x["content"]) for x in result["readings"]))
        self.assertFalse(result["complete_route_contents"])
        self.assertTrue(result["omissions"])
        self.assertFalse(result["runtime_or_profitability_proven"])
        full = nav.packet(nav.Snapshot(self.root), "trace-research", 1000)
        self.assertTrue(full["complete_route_contents"])
        self.assertEqual(len(full["readings"]), 2)

    def test_search_distinguishes_path_coverage_from_bounded_content(self):
        source = nav.Snapshot(self.root)
        paths = nav.search(source, "needle")
        self.assertEqual(paths["matches_total"], 0)
        content = nav.search(source, "needle", content=True, max_bytes=100)
        self.assertEqual(content["results"][0]["path"], "docs/other.md")
        self.assertEqual(content["results"][0]["content_hits"][0]["line"], 2)
        self.assertIn("docs/large.txt", [x["path"] for x in content["content_files_skipped"]])

    def test_broken_route_and_area_coverage_fail_without_changing_files(self):
        self.manifest["routes"][0]["reading_order"][0]["path"] = "docs/missing.md"
        self.manifest["areas"].pop("docs")
        self.write("docs/REPOSITORY-MAP.json", json.dumps(self.manifest))
        before = self.git("status", "--porcelain")
        result = nav.check_manifest(nav.Snapshot(self.root, worktree=True))
        self.assertFalse(result["passed"])
        self.assertEqual({e["kind"] for e in result["errors"]}, {"area_coverage", "invalid_source_pointer"})
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_traversal_absolute_paths_and_symlink_reads_are_refused(self):
        source = nav.Snapshot(self.root)
        for path in ["../outside.txt", "/etc/passwd", "docs/../README.md", "docs\\source.md"]:
            with self.assertRaises(ValueError):
                source.text(path)
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("not repository evidence")
        (self.root / "linked.txt").symlink_to(outside)
        self.git("add", "linked.txt")
        with self.assertRaises(ValueError):
            nav.Snapshot(self.root, worktree=True).text("linked.txt")
        # Even a previously regular tracked path cannot be swapped for a symlink.
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            nav.Snapshot(self.root, worktree=True).text("README.md")

    def test_duplicate_routes_and_unknown_relationship_are_reported(self):
        self.manifest["routes"].append(dict(self.manifest["routes"][0]))
        self.manifest["routes"][0]["related_routes"] = ["missing"]
        self.write("docs/REPOSITORY-MAP.json", json.dumps(self.manifest))
        result = nav.check_manifest(nav.Snapshot(self.root, worktree=True))
        self.assertFalse(result["passed"])
        self.assertIn("invalid_or_duplicate_route_id", [x["kind"] for x in result["errors"]])
        self.assertIn("missing_related_route", [x["kind"] for x in result["errors"]])

    def test_exact_route_wins_and_unmatched_query_is_not_fabricated(self):
        result = nav.route_matches(self.manifest, "trace-research")
        self.assertEqual(result[0]["route"]["id"], "trace-research")
        self.assertTrue(result[0]["exact_route_id"])
        self.assertEqual(nav.route_matches(self.manifest, "unrelated astrophysics"), [])

    def test_unborn_or_unknown_revision_fails_explicitly(self):
        with self.assertRaises(ValueError):
            nav.Snapshot(self.root, "does-not-exist")

    def test_manifest_missing_routes_is_rejected_instead_of_passing(self):
        self.manifest.pop("routes")
        self.write("docs/REPOSITORY-MAP.json", json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "routes"):
            nav.check_manifest(nav.Snapshot(self.root, worktree=True))

    def test_worktree_check_detects_missing_or_redirected_source(self):
        source = self.root / "docs/source.md"
        source.unlink()
        self.assertFalse(nav.check_manifest(nav.Snapshot(self.root, worktree=True))["passed"])
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("outside")
        source.symlink_to(outside)
        self.assertFalse(nav.check_manifest(nav.Snapshot(self.root, worktree=True))["passed"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixture requires POSIX")
    def test_fifo_swap_is_rejected_before_reading(self):
        source = self.root / "docs/source.md"
        source.unlink()
        os.mkfifo(source)
        result = subprocess.run([sys.executable, str(TOOLS / "repo_navigator.py"),
            "--repo", str(self.root), "--worktree", "read", "docs/source.md"],
            capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn("non-regular", result.stderr)

    def test_past_end_read_never_creates_nonprogressing_next_line(self):
        with self.assertRaisesRegex(ValueError, "beyond end"):
            nav.Snapshot(self.root).excerpt("docs/source.md", 999, 10)

    def test_content_hit_cap_reports_exact_omitted_matches(self):
        self.write("docs/other.md", "needle\n" * 100)
        result = nav.search(nav.Snapshot(self.root, worktree=True), "needle", content=True)
        row = next(x for x in result["results"] if x["path"] == "docs/other.md")
        self.assertEqual(row["content_hits_total"], 100)
        self.assertEqual(row["content_hits_omitted"], 97)
        self.assertEqual(len(row["content_hits"]), 3)

    def test_sha256_repository_uses_actual_git_object_identity(self):
        other = Path(self.tmp.name) / "sha256"
        result = subprocess.run(["git", "init", "-q", "--object-format=sha256", str(other)], capture_output=True)
        if result.returncode:
            self.skipTest("Installed Git does not support SHA256 repositories")
        for key, value in [("user.name", "Fixture Maintainer"), ("user.email", "fixture@example.invalid")]:
            subprocess.run(["git", "-C", str(other), "config", key, value], check=True)
        (other / "source.txt").write_text("source\n")
        subprocess.run(["git", "-C", str(other), "add", "source.txt"], check=True)
        subprocess.run(["git", "-C", str(other), "commit", "-qm", "Fixture"], check=True)
        expected = subprocess.check_output(["git", "-C", str(other), "rev-parse", "HEAD:source.txt"]).decode().strip()
        actual = nav.Snapshot(other).excerpt("source.txt")["git_blob"]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 64)

    def test_content_search_uses_one_closed_git_process_for_many_blobs(self):
        for number in range(80):
            self.write(f"docs/batch-{number:03d}.md", f"batchneedle observation {number}\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Batch sources")
        source = nav.Snapshot(self.root)
        processes = []
        real_popen = subprocess.Popen

        def launch(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            return process

        with patch.object(nav.subprocess, "Popen", side_effect=launch):
            result = nav.search(source, "batchneedle", limit=3, content=True)
        self.assertEqual(len(processes), 1)
        self.assertEqual(processes[0].args[-2:], ["cat-file", "--batch"])
        self.assertEqual(processes[0].returncode, 0)
        self.assertTrue(processes[0].stdin.closed)
        self.assertTrue(processes[0].stdout.closed)
        self.assertIsNone(source._batch_reader)
        self.assertEqual(result["matches_total"], 80)
        self.assertEqual(result["results_omitted"], 77)
        self.assertEqual(len(result["results"]), 3)
        first = result["results"][0]
        self.assertEqual(first["git_blob"], self.git("rev-parse", "HEAD:" + first["path"]).strip())

    def test_skipped_details_are_bounded_with_exact_counts(self):
        for number in range(200):
            self.write(f"docs/oversized-{number:03d}.md", "x" * 1000)
        for number in range(5):
            self.write(f"docs/image-{number}.png", "synthetic format fixture")
        (self.root / "docs/binary.txt").write_bytes(b"\0binary")
        (self.root / "docs/invalid.txt").write_bytes(b"\xff\xfe")
        self.git("add", ".")
        self.git("commit", "-qm", "Skipped sources")
        result = nav.search(nav.Snapshot(self.root), "absentfixturetoken", limit=1,
                            content=True, max_bytes=128)
        self.assertEqual(result["content_skipped_reason_counts"], {
            "size_limit": 202, "format_specific_reader": 5,
            "binary_content": 1, "invalid_utf8": 1,
        })
        self.assertEqual(result["content_files_skipped_total"], 209)
        self.assertEqual(len(result["content_files_skipped"]), nav.SKIPPED_DETAIL_LIMIT)
        self.assertEqual(result["content_skipped_details_omitted"], 209 - nav.SKIPPED_DETAIL_LIMIT)
        self.assertEqual(sum(result["content_skipped_reason_counts"].values()), 209)
        self.assertLess(len(json.dumps(result).encode()), 12000)
        self.assertEqual(result["matches_total"], 0)

    def test_batch_error_closes_process_and_next_search_can_recover(self):
        source = nav.Snapshot(self.root)
        with source.batch_reads():
            reader = source._batch_reader
            with self.assertRaises(nav.GitObjectReadError):
                reader.read("0" * 40, 0, 100)
            process = reader.process
            self.assertIsNotNone(process.poll())
            self.assertTrue(process.stdin.closed)
            self.assertTrue(process.stdout.closed)
            with self.assertRaises(nav.GitObjectReadError):
                reader.read(source.entries["README.md"]["index_blob"], 0, 100)
        self.assertIsNone(source._batch_reader)
        recovered = nav.search(source, "needle", content=True)
        self.assertEqual(recovered["results"][0]["path"], "docs/other.md")

    def test_batch_cleanup_on_unexpected_search_failure(self):
        source = nav.Snapshot(self.root)
        original_text = source.text
        captured = []

        def fail_after_read(path, bound):
            value = original_text(path, bound)
            captured.append(source._batch_reader.process)
            raise RuntimeError("synthetic caller failure")

        with patch.object(source, "text", side_effect=fail_after_read):
            with self.assertRaisesRegex(RuntimeError, "synthetic caller failure"):
                nav.search(source, "needle", content=True)
        self.assertEqual(len(captured), 1)
        self.assertIsNotNone(captured[0].poll())
        self.assertTrue(captured[0].stdin.closed)
        self.assertTrue(captured[0].stdout.closed)
        self.assertIsNone(source._batch_reader)

    def test_batch_is_lazy_and_never_used_for_worktree_or_path_only_search(self):
        committed = nav.Snapshot(self.root)
        worktree = nav.Snapshot(self.root, worktree=True)
        with patch.object(nav.subprocess, "Popen", side_effect=AssertionError("Unexpected Git process")):
            nav.search(committed, "needle")
            nav.search(worktree, "needle", content=True)
            # Every candidate exceeds this content bound, so no object is requested.
            result = nav.search(committed, "needle", content=True, max_bytes=1)
        self.assertEqual(result["content_files_inspected"], 0)
        self.assertEqual(result["content_files_skipped_total"], len(committed.entries))

    def test_batch_rejects_oversized_object_before_spawning_git(self):
        reader = nav.GitBlobBatch(self.root)
        with reader, patch.object(nav.subprocess, "Popen", side_effect=AssertionError("Unexpected Git process")):
            with self.assertRaisesRegex(nav.GitObjectReadError, "read bound"):
                reader.read("0" * 40, 101, 100)
        self.assertIsNone(reader.process)


if __name__ == "__main__":
    unittest.main()
