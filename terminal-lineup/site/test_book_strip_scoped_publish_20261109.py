#!/usr/bin/env python3
"""Regression blocker: BOOK-STRIP-SCOPED-PUBLISH-20261109 and
SYNC-SCOPED-WAIT-20261109.

Failure class: the book strip watcher republishes one small data
file, but it drove sync_to_test.py's full-tree publish. A full
publish takes minutes and, since the SYNC-SINGLE-FLIGHT cure
(2026-11-08), exactly one sync may run at a time: a watcher cycle
that landed during the hourly sync's run stood down with publish
exit 5 and the watcher reported it as a publish FAILURE (live:
2026-11-09 08:13 ET and 15:13 ET, after the 2026-11-05/06 exit-3
409-race failures of the same collision class).

The cure has two halves, both proven here:
(1) sync_to_test.py gains a scoped mode (--only <rels>): it
    publishes only the named files through the same gates, and it
    WAITS for the single-flight lock (acquire_single_flight_wait)
    instead of standing down. A concurrent full sync therefore
    delays a scoped publish; it can no longer fail it. The full
    sync's own stand-down (exit 5) is unchanged.
(2) watch_book_strip.py's default publish command IS the scoped
    mode over the generator's full write set, so the watcher can
    no longer invoke a whole-tree publish at all.

The behavioral checks run against a real local git repo through a
stand-in ghapi whose tree and contents are the repo itself, so the
scoped publisher's census, gate, upload, index regeneration and
read-back all execute for real; only the network is replaced.

Fail-first: against the pre-cure sync_to_test.py the module has
no publish_scoped and no acquire_single_flight_wait, checks 1
and 4 fail on AttributeError, and the pre-cure watcher's default
command has no --only, so check 5 fails.

Run standalone: python3 test_book_strip_scoped_publish_20261109.py
(exit 0 = pass), or under pytest (test_* functions).
"""
import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

REPO = "/repos/dwj9ddyvf6-hub/Test"
GEN_SRC = '''
import json


def build_index(entries, head, gen_at, owner, repo):
    files = [e["path"] for e in entries if e["type"] == "blob"]
    return {"totals": {"files": len(files)}, "files": files,
            "head": head}


def render_markdown(index, navigation=None):
    return "# Index\\n\\nfiles: %d\\n" % index["totals"]["files"]
'''


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args),
                          capture_output=True, text=True, check=True)


class FakeGhapi:
    """ghapi stand-in backed by a real local git repository.

    Tree reads come from git ls-tree; contents PUTs write the blob
    into the repo and move HEAD with a real commit, so a second
    tree read observes the first publish exactly as the real API
    would present it."""

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
    (repo / "INDEX.json").write_text("{}\n", encoding="utf-8")
    (repo / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-q", "-m", "seed")
    return repo


def run_scoped(tmp: Path):
    """Point the sync module at a temp ROOT and fake repo; return
    (fake, log_path). The module's ROOT/PREFIX/SYNC_LOG and the
    ghapi transport are swapped and restored by the caller via
    the returned restore closure."""
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

    return fake, log, restore


def test_scoped_waits_for_lock_and_publishes():
    with tempfile.TemporaryDirectory() as td:
        fake, log, restore = run_scoped(Path(td))
        held = sync.acquire_single_flight()
        assert held is not None
        released = []

        def release_soon():
            time.sleep(1.0)
            held.close()
            sync._LOCK_FH = None
            released.append(True)

        import threading
        t = threading.Thread(target=release_soon)
        t.start()
        try:
            rc = sync.publish_scoped(["site/book-strip/data.json"])
        finally:
            t.join()
            restore()
        assert released, "lock was never released by the holder"
        assert rc == 0, f"scoped publish returned {rc}"
        assert "terminal-lineup/site/book-strip/data.json" in fake.puts
        assert "INDEX.json" in fake.puts
        assert "scoped publish" in log.read_text(encoding="utf-8")


def test_scoped_clean_when_unchanged():
    with tempfile.TemporaryDirectory() as td:
        fake, log, restore = run_scoped(Path(td))
        try:
            (sync.ROOT / "site" / "book-strip" / "data.json"
             ).write_text('{"v": 1}\n', encoding="utf-8")
            rc = sync.publish_scoped(["site/book-strip/data.json"])
        finally:
            restore()
        assert rc == 0, f"unchanged scoped publish returned {rc}"
        assert fake.puts.count(
            "terminal-lineup/site/book-strip/data.json") == 0


def test_scoped_zero_byte_refused():
    with tempfile.TemporaryDirectory() as td:
        fake, log, restore = run_scoped(Path(td))
        page = sync.ROOT / "site" / "index.html"
        page.write_bytes(b"")
        try:
            rc = sync.publish_scoped(["site/index.html"])
        finally:
            restore()
        assert rc == 4, f"zero-byte scoped publish returned {rc}"
        assert fake.puts == []


def test_lock_wait_timeout_fails_loud():
    held = sync.acquire_single_flight()
    assert held is not None
    try:
        t0 = time.time()
        got = sync.acquire_single_flight_wait(timeout=2)
        assert got is None
        assert time.time() - t0 >= 2
    finally:
        sync._LOCK_FH = None
        held.close()


def test_full_sync_still_stands_down():
    held = sync.acquire_single_flight()
    assert held is not None
    orig = sync.ghapi.api

    def forbidden(*a, **k):
        raise AssertionError("stood-down run touched the API")

    sync.ghapi.api = forbidden
    try:
        assert sync.main([]) == 5
    finally:
        sync.ghapi.api = orig
        sync._LOCK_FH = None
        held.close()


def load_watcher():
    spec = importlib.util.spec_from_file_location(
        "watch_book_strip_scopedtest", SITE / "watch_book_strip.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_watcher_default_command_is_scoped():
    if os.environ.get("BOOK_STRIP_SYNC_CMD"):
        return  # an override is in force; the default is not in play
    watch = load_watcher()
    assert "--only" in watch.SYNC_CMD, watch.SYNC_CMD
    for rel in watch.SCOPED_FILES:
        assert rel.startswith("site/"), rel
    assert "site/book-strip/data.json" in watch.SCOPED_FILES


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print("book strip scoped publish tests: PASS (%d checks)"
          % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
