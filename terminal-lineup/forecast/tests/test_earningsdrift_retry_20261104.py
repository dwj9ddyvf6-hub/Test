"""Regression blocker for EARNINGS-DRIFT-RETRY-20261104.

Earnings Drift re-reads report dates from EDGAR on every run.
On 2026-11-03 the lane failed outright when EDGAR truncated
one chunked response mid-transfer (http.client.IncompleteRead,
0 bytes): a transient transport event the same refresher
walked past on its next run. The fetch now retries transport
failures a bounded number of times (three attempts total) and
then raises, so the caller still fails by name. A response
that arrives but is not JSON is not retried: it is not a
transport failure.

Fail direction on the pre-cure code: _get_json has no retry
(the attempts/_urlopen/_sleep seams do not exist), so the
recover-after-two-failures test raises IncompleteRead on the
first attempt and fails.
"""
import http.client
import importlib.util
import io
import json
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_earningsdrift",
    os.path.join(SITE, "refresh_earningsdrift.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _opener_failing_then_ok(failures):
    calls = {"n": 0}

    def opener(req, timeout=None):
        calls["n"] += 1
        if calls["n"] <= failures:
            raise http.client.IncompleteRead(b"", 1234)
        return _Resp(json.dumps({"ok": True}).encode())

    return opener, calls


def test_recovers_after_transient_truncations():
    opener, calls = _opener_failing_then_ok(2)
    out = mod._get_json("https://data.sec.gov/submissions/x.json",
                        _urlopen=opener, _sleep=lambda s: None)
    assert out == {"ok": True}
    assert calls["n"] == 3


def test_bounded_then_raises_by_name():
    import pytest
    opener, calls = _opener_failing_then_ok(99)
    with pytest.raises(http.client.IncompleteRead):
        mod._get_json("https://data.sec.gov/submissions/x.json",
                      _urlopen=opener, _sleep=lambda s: None)
    assert calls["n"] == 3  # bounded means bounded


def test_non_transport_failure_is_not_retried():
    import pytest
    calls = {"n": 0}

    def opener(req, timeout=None):
        calls["n"] += 1
        return _Resp(b"this is not json")

    with pytest.raises(json.JSONDecodeError):
        mod._get_json("https://data.sec.gov/submissions/x.json",
                      _urlopen=opener, _sleep=lambda s: None)
    assert calls["n"] == 1
