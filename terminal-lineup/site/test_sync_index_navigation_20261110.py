#!/usr/bin/env python3
"""Regression blocker: SYNC-INDEX-NAVIGATION-20261110.

Failure class: the hourly sync regenerated INDEX.md by calling
the repo generator's render_markdown(index) with NO navigation
map, while the Repository integrity workflow checks the saved
INDEX.md against a rendering built WITH the navigation map at
the indexed commit (docs/REPOSITORY-MAP.json). The map changes
area summaries, entrypoints and collection routes, so every
sync-published INDEX.md differed from the deterministic
rendering and step 8 of the integrity workflow failed on every
hourly run, flooding the owner's inbox with failure mail (live:
GitHub run 42840525482 and at least ten more on 2026-11-10,
all step 8, "INDEX.md differs from the deterministic
rendering"; the saved INDEX.md reproduced locally as exactly
the no-navigation render).

Cure: sync_to_test.fetch_navigation(entries) reads the map blob
named by the same post-upload tree the index describes, and
both regeneration paths (full sync and scoped publish) render
with it.

Fail-first: on the pre-cure sync_to_test.py fetch_navigation
does not exist (check 1 fails) and the scoped publish's
INDEX.md carries no navigation marker (check 2 fails).

Run standalone: python3 test_sync_index_navigation_20261110.py
(exit 0 = pass), or under pytest (test_* functions).
"""
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

REPO = "/repos/dwj9ddyvf6-hub/Test"
MAP = {"schema_version": 1,
       "areas": {"terminal-lineup": {"summary": "NAV-MARKER-SUMMARY",
                                     "entrypoints": []}}}
GEN_SRC = '''
import json


def build_index(entries, head, gen_at, owner, repo):
    files = [e["path"] for e in entries if e["type"] == "blob"]
    return {"totals": {"files": len(files)}, "files": files,
            "head": head}


def render_markdown(index, navigation=None):
    out = "# Index\\n\\nfiles: %d\\n" % index["totals"]["files"]
    if navigation:
        out += "nav-summary: %s\\n" % (
            navigation["areas"]["terminal-lineup"]["summary"])
    return out
'''


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args),
                          capture_output=True, text=True, check=True)


class FakeGhapi:
    """ghapi stand-in backed by a real local git repository,
    extended with the git blob route fetch_navigation uses."""

    ApiError = sync.ghapi.ApiError

    def __init__(self, repo):
        self.repo = Path(repo)
        self.puts = []

    def _head(self):
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def _tree(self):
        out = git(self.repo, "ls-tree", "-r", "HEAD").stdout
        entries = []
        for line in out.splitlines():
            meta, path = line.split("\t", 1)
            _mode, typ, sha = meta.split()
            size = len(git(self.repo, "cat-file", "-p",
                           sha).stdout.encode())
            entries.append({"path": path, "type": typ, "sha": sha,
                            "size": size})
        return entries

    def api(self, method, path, payload=None):
        if method == "GET" and path == REPO:
            return 200, {"default_branch": "main"}
        if method == "GET" and path == f"{REPO}/commits/main":
            date = git(self.repo, "log", "-1", "--format=%cI",
                       ).stdout.strip()
            return 200, {"sha": self._head(),
                         "commit": {"committer": {"date": date}}}
        if method == "GET" and path.startswith(f"{REPO}/git/trees/"):
            return 200, {"tree": self._tree(), "truncated": False}
        if method == "GET" and path.startswith(f"{REPO}/git/blobs/"):
            sha = path.rsplit("/", 1)[-1]
            data = git(self.repo, "cat-file", "-p", sha).stdout.encode()
            return 200, {"content": base64.b64encode(data).decode(),
                         "encoding": "base64"}
        if method == "GET" and "/contents/tools/" in path:
            return 200, {"content": base64.b64encode(
                GEN_SRC.encode()).decode()}
        if method == "GET" and path.startswith(f"{REPO}/contents/"):
            rel = path[len(REPO) + len("/contents/"):]
            target = self.repo / rel
            if not target.exists():
                raise FakeGhapi.ApiError(404, "GET", path, "not found")
            data = target.read_bytes()
            return 200, {"sha": sync.blob_sha(data)}
        if method == "PUT" and path.startswith(f"{REPO}/contents/"):
            rel = path[len(REPO) + len("/contents/"):]
            data = base64.b64decode(payload["content"])
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            git(self.repo, "add", "--", rel)
            git(self.repo, "-c", "user.email=t@t", "-c",
                "user.name=t", "commit", "-q", "-m",
                payload["message"])
            self.puts.append(rel)
            return 201, {"content": {"sha": sync.blob_sha(data)}}
        raise AssertionError(f"unexpected api call {method} {path}")


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    strip = repo / "terminal-lineup" / "site" / "book-strip"
    strip.mkdir(parents=True)
    (strip / "data.json").write_text('{"v": 1}\n', encoding="utf-8")
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "REPOSITORY-MAP.json").write_text(
        json.dumps(MAP), encoding="utf-8")
    (repo / "INDEX.json").write_text("{}\n", encoding="utf-8")
    (repo / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-q", "-m", "seed")
    return repo


def run_scoped(tmp: Path):
    root = tmp / "lineup"
    strip = root / "site" / "book-strip"
    strip.mkdir(parents=True)
    (strip / "data.json").write_text('{"v": 2}\n', encoding="utf-8")
    repo = make_repo(tmp)
    fake = FakeGhapi(repo)
    log = tmp / "SYNC-LOG.md"
    saved = (sync.ROOT, sync.SYNC_LOG, sync.ghapi.api)
    sync.ROOT = root
    sync.SYNC_LOG = log
    sync.ghapi.api = fake.api

    def restore():
        sync.ROOT, sync.SYNC_LOG, sync.ghapi.api = saved
        sync._LOCK_FH = None

    return repo, fake, restore


def test_fetch_navigation_reads_map_blob():
    with tempfile.TemporaryDirectory() as td:
        repo, fake, restore = run_scoped(Path(td))
        try:
            _head, _gen, entries, _blobs = sync.fetch_head_and_tree()
            nav = sync.fetch_navigation(entries)
            assert nav == MAP, nav
            absent = sync.fetch_navigation(
                [e for e in entries
                 if e["path"] != "docs/REPOSITORY-MAP.json"])
            assert absent is None, absent
        finally:
            restore()


def test_scoped_publish_renders_index_with_navigation():
    with tempfile.TemporaryDirectory() as td:
        repo, fake, restore = run_scoped(Path(td))
        try:
            rc = sync.publish_scoped(["site/book-strip/data.json"])
        finally:
            restore()
        assert rc == 0, f"scoped publish returned {rc}"
        assert "INDEX.md" in fake.puts, fake.puts
        published = (repo / "INDEX.md").read_text(encoding="utf-8")
        assert "NAV-MARKER-SUMMARY" in published, published


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print("sync index navigation tests: PASS (%d checks)" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
