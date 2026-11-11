#!/usr/bin/env python3
"""Regression blocker: SYNC-PUT-OVERSIZE-20261110.

On 2026-11-10 the 19:12 ET hourly sync exited 3:
PUT /repos/dwj9ddyvf6-hub/Test/contents/terminal-lineup/site/
chain-explorer/data.json -> HTTP 422 "file too large". The
local file is 46,715,772 bytes; the remote already held a
41,298,704-byte version uploaded earlier through the same
Contents PUT, so the PUT route works to at least ~41 MB and
fails at 46.7 MB. DATA_JSON_CAP (50 MB) is an inclusion cap,
not an API limit, so a file the sync is willing to publish
had no route to the repo at all.

The cure keeps the Contents PUT exactly as it was for the
normal case, and only when that PUT raises ApiError 422
whose body says the file/content is too large (and it is
NOT the sha-conflict 422, which keeps its existing branch)
falls back to a Git Data single-file commit in the shape of
morgue/daily_cycle.py push_feed(): create the blob, verify
its sha equals blob_sha(data), then an 8-attempt loop of
tree-on-current-head + commit (Repository Maintainer
identity) + PATCH ref with force=False, retrying on
non-fast-forward. The fallback returns the blob sha, so the
caller's returned-sha check and the run's final read-back
proof pass unchanged.

Fail-first: on the pre-cure put_file the too-large 422
raises ApiError instead of returning the blob sha, and no
git-data call is ever made.

Run standalone: python3 test_sync_put_oversize_fallback_20261110.py
(exit 0 = pass), or under pytest.
"""
import base64
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

ApiError = sync.ghapi.ApiError
PATH = "terminal-lineup/site/chain-explorer/data.json"
DATA = b'{"oversize": true, "rows": [1, 2, 3]}'
BODY_TOO_LARGE = ('{"message": "content is too large", '
                  '"documentation_url": '
                  '"https://docs.github.com/rest/repos/contents"}')
BODY_FILE_TOO_LARGE = ('{"message": "file too large", '
                       '"documentation_url": '
                       '"https://docs.github.com/rest/repos/contents"}')
BODY_422_SHA = ('{"message": "Invalid request. \\"sha\\" wasn\'t '
                'supplied.", "documentation_url": "https://docs.'
                'github.com/rest/repos/contents"}')
BODY_422_OTHER = ('{"message": "Validation Failed: bad request", '
                  '"documentation_url": '
                  '"https://docs.github.com/rest/repos/contents"}')
BODY_403 = ('{"message": "API rate limit exceeded", '
            '"documentation_url": "https://docs.github.com/rest", '
            '"status": "403"}')
IDENTITY = {
    "name": "Repository Maintainer",
    "email": "316344525+dwj9ddyvf6-hub@users.noreply.github.com",
}


class FakeGhapi:
    """A scripted ghapi.api covering the Contents PUT plus the
    Git Data routes the fallback uses."""

    def __init__(self, puts, patch_failures=0, blob_error=None):
        self.puts = list(puts)
        self.patch_failures = patch_failures
        self.blob_error = blob_error
        self.calls = []
        self.heads = ["head-1", "head-2", "head-3", "head-4",
                      "head-5", "head-6", "head-7", "head-8",
                      "head-9"]

    def __call__(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "PUT":
            outcome = self.puts.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 201, {"content": {"sha": outcome}}
        if method == "GET" and path == sync.REPO_API:
            return 200, {"default_branch": "main"}
        if method == "GET" and "/contents/" in path:
            return 200, {"sha": "freshbase"}
        if method == "POST" and path.endswith("/git/blobs"):
            if self.blob_error is not None:
                raise self.blob_error
            if payload.get("encoding") == "utf-8":
                raw = payload["content"].encode("utf-8")
            else:
                raw = base64.b64decode(payload["content"])
            assert payload["encoding"] == "base64"
            return 201, {"sha": sync.blob_sha(raw)}
        if method == "GET" and "/git/ref" in path:
            return 200, {"object": {"sha": self.heads.pop(0)}}
        if method == "GET" and "/git/commits/" in path:
            head = path.rsplit("/", 1)[-1]
            return 200, {"tree": {"sha": f"tree-of-{head}"}}
        if method == "POST" and path.endswith("/git/trees"):
            return 201, {"sha": "new-tree-sha"}
        if method == "POST" and path.endswith("/git/commits"):
            return 201, {"sha": "new-commit-sha"}
        if method == "PATCH" and "/git/ref" in path:
            if self.patch_failures > 0:
                self.patch_failures -= 1
                raise ApiError(422, "PATCH", path,
                               '{"message": "Update is not a '
                               'fast forward"}')
            return 200, {"object": {"sha": payload["sha"]}}
        raise AssertionError(f"unexpected api call {method} {path}")

    def git_data_calls(self):
        return [c for c in self.calls
                if "/git/blobs" in c[1] or "/git/trees" in c[1]
                or "/git/commits" in c[1] or "/git/ref" in c[1]]


def run_put(fake, data=DATA):
    orig_api = sync.ghapi.api
    orig_sleep = sync.time.sleep
    sync.ghapi.api = fake
    sync.time.sleep = lambda s: None
    try:
        return sync.put_file(PATH, data, "msg", "base-sha")
    finally:
        sync.ghapi.api = orig_api
        sync.time.sleep = orig_sleep


def test_too_large_falls_back_to_git_data():
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_TOO_LARGE)])
    got = run_put(fake)
    assert got == sync.blob_sha(DATA), got
    puts = [c for c in fake.calls if c[0] == "PUT"]
    assert len(puts) == 1
    blobs = [c for c in fake.calls
             if c[0] == "POST" and c[1].endswith("/git/blobs")]
    assert len(blobs) == 1
    assert base64.b64decode(blobs[0][2]["content"]) == DATA
    trees = [c for c in fake.calls
             if c[0] == "POST" and c[1].endswith("/git/trees")]
    assert len(trees) == 1
    entry = trees[0][2]["tree"][0]
    assert entry == {"path": PATH, "mode": "100644",
                     "type": "blob", "sha": sync.blob_sha(DATA)}
    assert trees[0][2]["base_tree"] == "tree-of-head-1"
    commits = [c for c in fake.calls
               if c[0] == "POST" and c[1].endswith("/git/commits")]
    assert len(commits) == 1
    cpayload = commits[0][2]
    assert cpayload["message"] == "msg"
    assert cpayload["tree"] == "new-tree-sha"
    assert cpayload["parents"] == ["head-1"]
    assert cpayload["author"] == IDENTITY
    assert cpayload["committer"] == IDENTITY
    patches = [c for c in fake.calls if c[0] == "PATCH"]
    assert len(patches) == 1
    assert patches[0][2] == {"sha": "new-commit-sha", "force": False}


def test_file_too_large_wording_also_falls_back():
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_FILE_TOO_LARGE)])
    assert run_put(fake) == sync.blob_sha(DATA)
    assert fake.git_data_calls(), "no git-data fallback happened"


def test_non_fast_forward_retries_on_fresh_head():
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_TOO_LARGE)],
        patch_failures=1)
    assert run_put(fake) == sync.blob_sha(DATA)
    patches = [c for c in fake.calls if c[0] == "PATCH"]
    assert len(patches) == 2
    commits = [c for c in fake.calls
               if c[0] == "POST" and c[1].endswith("/git/commits")]
    assert len(commits) == 2
    assert commits[1][2]["parents"] == ["head-2"]


def test_blob_create_refusal_fails_loud():
    # Live boundary (2026-11-10): GitHub's create-blob step
    # itself refused the 46.7 MB candidate with 422 "your
    # input was too large" in both encodings. That refusal
    # must propagate unchanged (no tree/commit/ref calls,
    # no split, no silent pass), so the run fails loud.
    blob_422 = ApiError(
        422, "POST", "/git/blobs",
        '{"message": "Sorry, your input was too large to '
        'process.", "status": "422"}')
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_TOO_LARGE)],
        blob_error=blob_422)
    try:
        run_put(fake)
    except ApiError as e:
        assert e.status == 422
        rest = [c for c in fake.git_data_calls()
                if not c[1].endswith("/git/blobs")]
        assert rest == [], rest
        return
    raise AssertionError("blob-create 422 did not raise")


def test_small_file_never_touches_git_data():
    fake = FakeGhapi(puts=["sha-ok"])
    assert run_put(fake) == "sha-ok"
    assert len(fake.calls) == 1
    assert fake.git_data_calls() == []


def test_422_sha_conflict_does_not_use_git_data():
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_422_SHA), "newsha"])
    assert run_put(fake) == "newsha"
    puts = [c for c in fake.calls if c[0] == "PUT"]
    assert len(puts) == 2
    assert puts[1][2]["sha"] == "freshbase"
    assert fake.git_data_calls() == []


def test_422_other_raises_without_git_data():
    fake = FakeGhapi(
        puts=[ApiError(422, "PUT", PATH, BODY_422_OTHER)])
    try:
        run_put(fake)
    except ApiError as e:
        assert e.status == 422
        assert fake.git_data_calls() == []
        return
    raise AssertionError("non-too-large 422 did not raise")


def test_403_raises_without_git_data():
    fake = FakeGhapi(puts=[ApiError(403, "PUT", PATH, BODY_403)])
    try:
        run_put(fake)
    except ApiError as e:
        assert e.status == 403
        assert fake.git_data_calls() == []
        return
    raise AssertionError("403 did not raise")


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
