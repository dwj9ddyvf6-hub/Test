#!/usr/bin/env python3
"""Regression blocker: SYNC-PUT-TRANSPORT-20261109.

On 2026-11-09 the 19:12 ET hourly sync to the public Test
repo died with exit 1: an SSLEOFError (a URLError) raised by
urllib inside ghapi.api during a put_file PUT. ghapi.api
converts HTTPError responses into ApiError but lets transport
errors (the connection or TLS layer died; no HTTP response
ever existed) propagate raw, and main() catches only
ApiError, so the run crashed mid-publish: files already
landed, no index regeneration, no sync-log line (the log
stayed at 442 lines; the mirror's own line became 443). The
mirror_master.py writes to the same repo through the same
ghapi helper succeeded minutes later, proving the route
itself was healthy: the failure was one dropped connection
in a run that performs hundreds of sequential PUTs.

put_file already retried the two response-bearing flakes
(401 once, SYNC-PUT-AUTH-20261108; sha conflicts by re-read,
SYNC-PUT-SHA-20261108) but had no branch for a transport
error, so one drop killed the whole run.

The cure retries the PUT once, unchanged in content and base
sha, after a transport error. The outcome of a dropped PUT
is unknown (it may have landed), and the retry is exact
either way: if the first PUT landed, the retry draws a 409
sha conflict and the existing sha-conflict branch re-reads
the current sha and re-PUTs the identical bytes; ghapi also
fetches a fresh credential surrogate per call, so the retry
rides a fresh connection. A second transport error raises,
unchanged, so a genuinely dead route still fails loud. A
403 still raises without any retry (the rate-stop rule).

Fail-first: on the pre-cure put_file the first SSLEOFError
propagates immediately instead of returning the retried sha.

Run standalone: python3 test_sync_put_transport_retry_20261109.py
(exit 0 = pass), or under pytest.
"""
import ssl
import sys
import urllib.error
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

ApiError = sync.ghapi.ApiError
PATH = "terminal-lineup/site/pattern-draw/data.json"
BODY_403 = ('{"message":"API rate limit exceeded",'
            '"documentation_url":"https://docs.github.com/rest",'
            '"status":"403"}')
BODY_409 = ('{"message":"is at newsha but expected base-sha",'
            '"documentation_url":"https://docs.github.com/rest",'
            '"status":"409"}')


def ssleof():
    return urllib.error.URLError(
        ssl.SSLEOFError(8, "EOF occurred in violation of "
                           "protocol (_ssl.c:2406)"))


class Script:
    """A scripted ghapi.api: outcomes per PUT (and one GET)."""

    def __init__(self, puts, get_cur=None):
        self.puts = list(puts)
        self.get_cur = get_cur
        self.calls = []

    def __call__(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "PUT":
            outcome = self.puts.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 201, {"content": {"sha": outcome}}
        if method == "GET":
            if self.get_cur is None:
                raise AssertionError("unexpected GET")
            return 200, {"sha": self.get_cur}
        raise AssertionError(f"unexpected method {method}")


def run_put(script):
    orig_api = sync.ghapi.api
    orig_sleep = sync.time.sleep
    sync.ghapi.api = script
    sync.time.sleep = lambda s: None
    try:
        return sync.put_file(PATH, b"{}", "msg", "base-sha")
    finally:
        sync.ghapi.api = orig_api
        sync.time.sleep = orig_sleep


def test_transport_error_retries_once_with_identical_payload():
    script = Script(puts=[ssleof(), "newsha"])
    got = run_put(script)
    assert got == "newsha"
    puts = [c for c in script.calls if c[0] == "PUT"]
    assert len(puts) == 2
    assert puts[0][2] == puts[1][2]
    assert puts[1][2]["sha"] == "base-sha"


def test_dropped_put_that_landed_heals_through_sha_branch():
    """First PUT drops at transport (but actually landed, so
    the repo moved): the retry draws 409, the sha branch
    re-reads the current sha and re-PUTs identical bytes."""
    script = Script(
        puts=[ssleof(),
              ApiError(409, "PUT", PATH, BODY_409),
              "landedsha"],
        get_cur="landedsha")
    got = run_put(script)
    assert got == "landedsha"
    puts = [c for c in script.calls if c[0] == "PUT"]
    assert len(puts) == 3
    assert puts[2][2]["sha"] == "landedsha"
    assert puts[2][2]["content"] == puts[0][2]["content"]


def test_second_transport_error_raises():
    script = Script(puts=[ssleof(), ssleof()])
    try:
        run_put(script)
    except urllib.error.URLError:
        assert len([c for c in script.calls if c[0] == "PUT"]) == 2
        return
    raise AssertionError("second transport error did not raise")


def test_403_raises_without_retry():
    script = Script(puts=[ApiError(403, "PUT", PATH, BODY_403)])
    try:
        run_put(script)
    except ApiError as e:
        assert e.status == 403
        assert len(script.calls) == 1
        return
    raise AssertionError("403 did not raise")


def test_clean_put_unchanged():
    script = Script(puts=["sha-ok"])
    assert run_put(script) == "sha-ok"
    assert len(script.calls) == 1


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
