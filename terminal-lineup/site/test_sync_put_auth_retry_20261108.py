#!/usr/bin/env python3
"""Regression blocker: SYNC-PUT-AUTH-20261108.

On 2026-11-08 the hourly sync to the public Test repo died
twice in a row mid-publish on a single HTTP 401 "Bad
credentials" each time, on different files (the 22:12 ET run
on terminal-lineup/site/ai-chart-read/data.json, the proof
re-run on terminal-lineup/site/pattern-draw/data.json after
about 213 seconds of successful uploads). The credential was
not dead: a read-only authenticated probe of the repo
returned 200 with push permission minutes after the first
failure, and mirror_master.py wrote to the same repo through
the same ghapi credential helper in the same hour. The
estate transport diagnosis (2026-10-28) already classed
transient HTTP 401s on this egress path as a sporadic
edge/credential flake, retried by design in the older pusher.
put_file retried sha conflicts (409/422) but not 401, so one
flake killed the whole run: files already landed, no index
regeneration, no sync-log line.

The cure retries a 401 PUT once with the identical payload;
ghapi fetches a fresh credential surrogate per call, so the
retry carries a freshly fetched credential. A second 401
still raises as a hard API error, so a genuinely dead
credential fails loud instead of being retried forever. A
403 still raises without any retry (the rate-stop rule).

Fail-first: on the pre-cure put_file the first 401 raises
ApiError instead of returning the retried sha.

Run standalone: python3 test_sync_put_auth_retry_20261108.py
(exit 0 = pass), or under pytest.
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import sync_to_test as sync  # noqa: E402

ApiError = sync.ghapi.ApiError
PATH = "terminal-lineup/site/pattern-draw/data.json"
BODY_401 = ('{"message":"Bad credentials","documentation_url":'
            '"https://docs.github.com/rest","status":"401"}')
BODY_403 = ('{"message":"API rate limit exceeded",'
            '"documentation_url":"https://docs.github.com/rest",'
            '"status":"403"}')


class Script:
    """A scripted ghapi.api: a list of outcomes per PUT."""

    def __init__(self, puts):
        self.puts = list(puts)
        self.calls = []

    def __call__(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "PUT":
            outcome = self.puts.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 201, {"content": {"sha": outcome}}
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


def test_401_retries_once_with_identical_payload():
    script = Script(
        puts=[ApiError(401, "PUT", PATH, BODY_401), "newsha"])
    got = run_put(script)
    assert got == "newsha"
    puts = [c for c in script.calls if c[0] == "PUT"]
    assert len(puts) == 2
    assert puts[0][2] == puts[1][2]
    assert puts[1][2]["sha"] == "base-sha"
    assert [c for c in script.calls if c[0] == "GET"] == []


def test_second_401_raises():
    script = Script(
        puts=[ApiError(401, "PUT", PATH, BODY_401),
              ApiError(401, "PUT", PATH, BODY_401)])
    try:
        run_put(script)
    except ApiError as e:
        assert e.status == 401
        assert len([c for c in script.calls if c[0] == "PUT"]) == 2
        return
    raise AssertionError("second 401 did not raise")


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
