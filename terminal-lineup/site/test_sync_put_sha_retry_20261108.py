#!/usr/bin/env python3
"""Regression blocker: SYNC-PUT-SHA-20261108.

sync_to_test.py snapshots every file's base blob sha once, at
run start, then uploads for minutes. Any writer that lands on
the repo mid-run (on 2026-11-08 the Test history-rewrite
publish moved every blob while the hourly sync was uploading)
invalidates the base sha of the files it touched, and GitHub
answers the stale-base PUT with 409. put_file's retry handled
only the 422 form, so the 409 killed the run mid-publish as a
HARD API ERROR (exit 3): dozens of files already landed, no
index regeneration, no sync-log line.

The cure retries a sha conflict (409, or 422 naming sha) once
with the file's CURRENT sha re-read from the contents endpoint;
the bytes written are still the run's candidate bytes, and the
caller's returned-sha check plus the final read-back proof
still verify the outcome. A second conflict, and any non-sha
error, still raise.

Fail-first: on the pre-cure put_file the 409 case raises
ApiError instead of returning the new sha.

Run standalone: python3 test_sync_put_sha_retry_20261108.py
(exit 0 = pass), or under pytest.
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

ApiError = sync.ghapi.ApiError
PATH = "terminal-lineup/site/decay-watch/data.json"
# The real 409 body names the two blob hashes but never the
# word "sha"; the fixture mirrors that exactly.
BODY_409 = ('{"message": "terminal-lineup/site/decay-watch/'
            'data.json is at 3d6cf968b78ee43ae108b169560e840b'
            'bd0ba6f5 but expected 17d6d4b8836b7a8795e818b1b1'
            'ec8cf751927b5d", "documentation_url": "https://'
            'docs.github.com/rest/repos/contents"}')
BODY_422 = ('{"message": "Invalid request. \\"sha\\" wasn\'t '
            'supplied.", "documentation_url": "https://docs.'
            'github.com/rest/repos/contents"}')


class Script:
    """A scripted ghapi.api: a list of outcomes per method."""

    def __init__(self, puts, get=None):
        self.puts = list(puts)
        self.get = get
        self.calls = []

    def __call__(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "PUT":
            outcome = self.puts.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 201, {"content": {"sha": outcome}}
        if method == "GET":
            if isinstance(self.get, Exception):
                raise self.get
            return 200, self.get
        raise AssertionError(f"unexpected method {method}")


def run_put(script):
    orig = sync.ghapi.api
    sync.ghapi.api = script
    try:
        return sync.put_file(PATH, b"{}", "msg", "stalebase")
    finally:
        sync.ghapi.api = orig


def test_409_retries_with_fresh_sha():
    script = Script(
        puts=[ApiError(409, "PUT", PATH, BODY_409), "newsha"],
        get={"sha": "freshbase"})
    got = run_put(script)
    assert got == "newsha"
    puts = [c for c in script.calls if c[0] == "PUT"]
    assert len(puts) == 2
    assert puts[1][2]["sha"] == "freshbase"


def test_422_sha_still_retries():
    script = Script(
        puts=[ApiError(422, "PUT", PATH, BODY_422), "newsha"],
        get={"sha": "freshbase"})
    assert run_put(script) == "newsha"


def test_second_409_raises():
    script = Script(
        puts=[ApiError(409, "PUT", PATH, BODY_409),
              ApiError(409, "PUT", PATH, BODY_409)],
        get={"sha": "freshbase"})
    try:
        run_put(script)
    except ApiError:
        return
    raise AssertionError("second 409 did not raise")


def test_403_raises_without_retry():
    script = Script(
        puts=[ApiError(403, "PUT", PATH, "rate limited")],
        get={"sha": "freshbase"})
    try:
        run_put(script)
    except ApiError:
        assert [c for c in script.calls if c[0] == "GET"] == []
        return
    raise AssertionError("403 did not raise")


def test_single_flight_second_acquire_refused():
    first = sync.acquire_single_flight()
    assert first is not None
    try:
        assert sync.acquire_single_flight() is None
    finally:
        sync._LOCK_FH = None
        first.close()
    third = sync.acquire_single_flight()
    assert third is not None
    sync._LOCK_FH = None
    third.close()


def test_main_stands_down_while_locked(capsys=None):
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


def test_lock_file_never_published():
    assert "site/.sync_to_test.lock" not in sync.included_files()


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
