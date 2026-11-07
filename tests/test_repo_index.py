"""Offline inventory contracts; all Git mutations occur in temporary fixtures."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_repo_index", ROOT / "tools/build_repo_index.py")
indexer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(indexer)


def blob(path="file.txt", content=b"fixture\n", mode="100644"):
    return {"path": path, "type": "blob", "mode": mode,
            "sha": hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest(), "size": len(content)}


class InventoryValidationTests(unittest.TestCase):
    def test_exact_self_exclusions_and_deterministic_order(self):
        tree = [blob("tools/build_repo_index.py"), blob("a.txt")]
        first = indexer.build_index(tree, "a" * 40, "2026-11-07T00:00:00Z", "example", "library")
        self.assertEqual(first, indexer.build_index(list(reversed(tree)), "a" * 40, "2026-11-07T00:00:00Z", "example", "library"))
        self.assertEqual({x["path"] for x in first["files"] if x.get("self")}, {"INDEX.md", "INDEX.json"})
        self.assertTrue(next(x for x in first["files"] if x["path"] == "tools/build_repo_index.py")["sha"])
        self.assertEqual(first["totals"]["bytes"], 16)

    def test_rejects_incomplete_unsafe_or_ambiguous_inventory(self):
        invalid = [[blob(), blob()], [blob("../escape")], [blob("/absolute")], [blob("a\\b")],
                   [blob("a//b")], [blob("a"), blob("a/b")], [blob(".git/config")],
                   [dict(blob(), sha=None)], [dict(blob(), size=-1)], [dict(blob(), size=True)],
                   [dict(blob(), type="commit", mode="160000")], [dict(blob(), mode="100664")]]
        for entries in invalid:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                indexer.build_entries(entries)

    def test_rejects_unattributed_or_undated_snapshot(self):
        for commit, stamp in [(None, "2026-11-07T00:00:00Z"), ("HEAD", "2026-11-07T00:00:00Z"), ("a"*40, "2026-11-07"), ("a"*40, None)]:
            with self.subTest(commit=commit, stamp=stamp), self.assertRaises(ValueError):
                indexer.build_index([], commit, stamp, "x", "y")

    def test_dynamic_collections_and_manifest_entrypoints(self):
        entries = [blob("docs/research/new-study/SYNTHESIS.md"), blob("docs/research/new-study/evidence.json"), blob("future-area/README.md")]
        index = indexer.build_index(entries, "a"*40, "2026-11-07T00:00:00Z", "x", "y")
        navigation = {"schema_version": 1, "areas": {"future-area": {"summary": "New evidence collection.", "entrypoints": ["future-area/README.md"]}}, "routes": [{"reading_order": [{"path": "docs/research/new-study/SYNTHESIS.md"}]}]}
        rendered = indexer.render_markdown(index, navigation)
        self.assertIn("docs/research/new-study/", rendered)
        self.assertIn("— 2 files", rendered)
        self.assertIn("New evidence collection.", rendered)
        navigation["areas"]["future-area"]["entrypoints"] = ["absent.md"]
        with self.assertRaises(ValueError): indexer.render_markdown(index, navigation)

    def test_truncated_saved_snapshot_never_writes_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "snapshot.json").write_text(json.dumps({"truncated": True, "tree": [blob()]}))
            with contextlib.redirect_stderr(io.StringIO()):
                code = indexer.main(["--tree-json", str(root / "snapshot.json"), "--out-dir", str(root / "output")])
            self.assertEqual(code, 2)
            self.assertFalse((root / "output").exists())


class GitSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        for path, text in {"alpha/file.txt": "nested\n", "alpha.txt": "flat\n", "zeta.txt": "z\n", "café.txt": "unicode\n", "tools/build_repo_index.py": "source\n"}.items():
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        (self.root / "symbolic").symlink_to("alpha.txt")
        self.git("add", "."); self.git("commit", "-qm", "fixture")
        self.output = self.root / "generated"

    def tearDown(self): self.directory.cleanup()
    def git(self, *args): return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode().strip()
    def run_main(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return indexer.main(["--local-repo", str(self.root), "--out-dir", str(self.output), *extra])
    def bytes_tree(self): return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def test_committed_snapshot_matches_independent_git_tree(self):
        snap = indexer.local_snapshot(self.root)
        self.assertEqual(indexer.tree_hash(snap["tree"]), self.git("rev-parse", "HEAD^{tree}"))
        self.assertEqual(snap["head"], self.git("rev-parse", "HEAD"))
        self.assertEqual(next(e for e in snap["tree"] if e["path"] == "symbolic")["mode"], "120000")

    def test_staged_snapshot_is_read_only_and_excludes_unstaged_bytes(self):
        (self.root / "alpha.txt").write_text("staged\n"); self.git("add", "alpha.txt")
        (self.root / "alpha.txt").write_text("unstaged\n")
        before = self.bytes_tree()
        snap = indexer.local_snapshot(self.root, staged=True)
        self.assertEqual(before, self.bytes_tree())
        self.assertIsNone(snap["head"])
        self.assertEqual(snap["source"]["tree_sha"], self.git("write-tree"))
        self.assertEqual(next(e for e in snap["tree"] if e["path"] == "alpha.txt")["sha"], blob(content=b"staged\n")["sha"])

    def test_map_is_read_from_selected_source_not_worktree(self):
        target = self.root / "docs/REPOSITORY-MAP.json"; target.parent.mkdir()
        target.write_text(json.dumps({"schema_version": 1, "areas": {}})); self.git("add", "."); self.git("commit", "-qm", "map")
        target.write_text("invalid worktree JSON")
        self.assertEqual(indexer.local_snapshot(self.root)["navigation_map"], {"schema_version": 1, "areas": {}})

    def test_check_allows_index_only_successor_and_rejects_source_drift(self):
        self.assertEqual(self.run_main(), 0)
        for name in indexer.SELF_PATHS:
            (self.root / name).write_bytes((self.output / name).read_bytes())
        self.git("add", *indexer.SELF_PATHS); self.git("commit", "-qm", "index only")
        self.assertEqual(self.run_main("--check"), 0)
        before = self.bytes_tree()
        self.assertEqual(self.run_main("--check"), 0)
        self.assertEqual(before, self.bytes_tree())
        (self.root / "zeta.txt").write_text("changed source\n"); self.git("add", "zeta.txt"); self.git("commit", "-qm", "source moved")
        self.assertEqual(self.run_main("--check"), 1)

    def test_check_rejects_prose_and_provenance_tampering(self):
        self.assertEqual(self.run_main(), 0)
        markdown = self.output / "INDEX.md"; original = markdown.read_text(); markdown.write_text(original + "drift\n")
        self.assertEqual(self.run_main("--check"), 1)
        markdown.write_text(original)
        saved_file = self.output / "INDEX.json"; saved = json.loads(saved_file.read_text())
        saved["source"]["tree_sha"] = "f" * 40
        saved_file.write_text(json.dumps(saved)); markdown.write_text(indexer.render_markdown(saved))
        self.assertEqual(self.run_main("--check"), 1)


class FixedGuideBlockTests(unittest.TestCase):
    def test_exact_block_and_missing_target_are_detected(self):
        spec = importlib.util.spec_from_file_location("guide_checker", ROOT / "agentic-trade-desk/skeleton/tools/check_root_readme_links.py")
        checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "docs").mkdir()
            source = (ROOT / "docs/README_FIXED_SECTION.md").read_text()
            (root / "docs/README_FIXED_SECTION.md").write_text(source)
            block = checker.extract_block(source)
            (root / "README.md").write_text(block)
            for name in checker.TARGETS:
                target=root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text("fixture")
            self.assertEqual(checker.check(root / "README.md"), [])
            (root / "README.md").write_text(block.replace("judgment", "changed"))
            self.assertTrue(checker.check(root / "README.md"))
            (root / "README.md").write_text(block); (root / checker.TARGETS[1]).unlink()
            self.assertTrue(checker.check(root / "README.md"))
