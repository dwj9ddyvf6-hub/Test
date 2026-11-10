"""Regression blocker for CHAIN-SPOT-RETRY-20261109.

The 2026-11-09 15:57 ET chain snapshot run stored SPY and then
refused QQQ and IWM: the spot quote fetch returned a Yahoo
regularMarketTime of 2026-11-09T20:56:17Z / 20:56:18Z, and by
the time those symbols were reached (after the preceding
symbol's Alpaca content leg) the quote's age had crossed the
90-second freshness gate. The collector fetched the spot
exactly once per symbol and refused on that single stale
verdict, with no re-fetch, even though the quote source is a
live endpoint whose timestamp advances between fetches.

The cure: fetch_spot_fresh re-fetches the quote inside a
bounded, spaced attempt budget when the verdict is not fresh
and a fresh quote is required, returning the first fresh
result; a quote that stays stale through the whole budget is
returned as stale so the caller's fail-closed refusal still
fires on the LAST quote seen. The 90-second gate itself is
unchanged. Fixture fetches only: no network, no keys.
"""

import importlib.util
import os

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")
_spec = importlib.util.spec_from_file_location(
    "collect_chains", os.path.join(SITE, "collect_chains.py"))
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


def _seq(results):
    calls = []

    def fake_fetch(symbol):
        calls.append(symbol)
        return results[min(len(calls) - 1, len(results) - 1)]

    return fake_fetch, calls


STALE = (680.0, "src", "2026-11-09T20:56:17+00:00", "stale")
FRESH = (681.65, "src", "2026-11-09T20:58:54+00:00", "fresh")


def test_stale_then_fresh_is_stored_on_the_fresh_quote():
    fetch, calls = _seq([STALE, FRESH])
    sleeps = []
    out = cc.fetch_spot_fresh("QQQ", fetch=fetch,
                              sleep=sleeps.append)
    assert out == FRESH
    assert calls == ["QQQ", "QQQ"]
    assert sleeps, "a stale verdict must wait before re-fetching"


def test_persistent_stale_returns_last_stale_for_refusal():
    fetch, calls = _seq([STALE])
    out = cc.fetch_spot_fresh("IWM", fetch=fetch,
                              sleep=lambda s: None)
    assert out[3] == "stale"
    assert out[2] == STALE[2]
    assert len(calls) == cc.SPOT_ATTEMPTS


def test_fresh_first_fetch_is_not_refetched():
    fetch, calls = _seq([FRESH])
    sleeps = []
    out = cc.fetch_spot_fresh("SPY", fetch=fetch,
                              sleep=sleeps.append)
    assert out == FRESH
    assert calls == ["SPY"]
    assert sleeps == []


def test_no_retry_when_freshness_not_required():
    # Outside the market window (the --force seed path) a stale
    # quote is stored as the dated record it is; the retry must
    # not stall that path re-fetching a closed market's quote.
    fetch, calls = _seq([STALE, FRESH])
    out = cc.fetch_spot_fresh("QQQ", fetch=fetch,
                              sleep=lambda s: None,
                              require_fresh=False)
    assert out == STALE
    assert calls == ["QQQ"]
