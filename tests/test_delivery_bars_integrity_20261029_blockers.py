"""DELIVERY-BARS-INTEGRITY-20261029 blockers: DEEP-PASS 3.1 items 1
and 2, adopted as is from the new-head Trade Brain hardening
(Sections 2.3 points 9 and 10).

Item 1, delivery time revalidation: a cached decision card is
rechecked against the live clock at delivery. Session closed since
computation rewrites the card to market_closed with setups stripped.
An underlying quote aged past 90 seconds (or future dated beyond 5
seconds) makes the delivery stale and DELETES the cache entry. An
option setup whose own quote died is dropped individually, with the
options block downgraded to stale and the scan status recomputed.
The same age rule revalidates the desk snapshot's quote maps at the
producer to snapshot delivery seam in Desk.run_cycle: a quote a
cache backed producer received more than 90 seconds before delivery
never reaches sleeves.

Item 2, bars payload integrity gate: a daily history payload is
validated as a whole before use. A symbol the caller did not
request, a non finite or non positive OHLC value, a bar outside the
requested window, a duplicate or non increasing New York date, or
more than 1000 bars each fail the payload as
daily_history_invalid_or_incomplete. The expected latest completed
session is derived by walking the desk trading calendar backwards
(up to 8 days), never accepted on a tolerance window; a history
that does not end on that session fails as well.

Fail direction: desk3/delivery.py does not exist on the pre-cure
tree and warm._fetch performs no payload validation, so every test
below fails pre-cure (import error or a missing rejection) and
passes post-cure.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 28, 14, 0, 0, tzinfo=timezone.utc)  # Wed 10:00 ET


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _card(underlying_age_s=10, option_age_s=10, equity=True):
    card = {"status": "ok",
            "quote": {"market_at": _iso(NOW - timedelta(seconds=underlying_age_s))},
            "setups": ([{"symbol": "SPY", "side": "long"}] if equity else []),
            "options": {"status": "ok",
                        "setup": {"symbol": "SPY261030C00700000",
                                  "quote_at": _iso(NOW - timedelta(seconds=option_age_s))}}}
    return card


class DeliveryCardTests(unittest.TestCase):
    def test_fresh_card_delivered_unchanged(self):
        from desk3.delivery import revalidate_card
        card = _card()
        delivered, verdict = revalidate_card(card, NOW, session_open=True)
        self.assertEqual(verdict, "fresh")
        self.assertEqual(delivered, card)

    def test_session_closed_rewrites_market_closed_and_strips(self):
        from desk3.delivery import revalidate_card
        delivered, verdict = revalidate_card(_card(), NOW, session_open=False)
        self.assertEqual(verdict, "market_closed")
        self.assertEqual(delivered["status"], "market_closed")
        self.assertEqual(delivered["setups"], [])
        self.assertIsNone(delivered["options"]["setup"])
        self.assertEqual(delivered["options"]["status"], "market_closed")

    def test_stale_underlying_is_stale_and_cache_entry_deleted(self):
        from desk3.delivery import revalidate_card
        cache = {"SPY": _card(underlying_age_s=120)}
        delivered, verdict = revalidate_card(
            cache["SPY"], NOW, session_open=True, cache=cache, cache_key="SPY")
        self.assertEqual(verdict, "stale")
        self.assertEqual(delivered["status"], "stale")
        self.assertEqual(delivered["setups"], [])
        self.assertNotIn("SPY", cache)  # deleted, forcing recomputation

    def test_future_dated_underlying_is_stale(self):
        from desk3.delivery import revalidate_card
        delivered, verdict = revalidate_card(
            _card(underlying_age_s=-30), NOW, session_open=True)
        self.assertEqual(verdict, "stale")
        self.assertEqual(delivered["status"], "stale")

    def test_boundary_exactly_90_seconds_is_fresh(self):
        from desk3.delivery import revalidate_card
        _d, verdict = revalidate_card(
            _card(underlying_age_s=90), NOW, session_open=True)
        self.assertEqual(verdict, "fresh")

    def test_missing_underlying_stamp_fails_closed_stale(self):
        from desk3.delivery import revalidate_card
        card = _card()
        del card["quote"]
        delivered, verdict = revalidate_card(card, NOW, session_open=True)
        self.assertEqual(verdict, "stale")
        self.assertEqual(delivered["setups"], [])

    def test_dead_option_setup_dropped_individually(self):
        from desk3.delivery import revalidate_card
        delivered, verdict = revalidate_card(
            _card(option_age_s=300), NOW, session_open=True)
        self.assertEqual(verdict, "option_setup_dropped")
        self.assertEqual(len(delivered["setups"]), 1)  # equity survives
        self.assertIsNone(delivered["options"]["setup"])
        self.assertEqual(delivered["options"]["status"], "stale")
        self.assertEqual(delivered["status"], "ok")  # equity still stands

    def test_dead_option_setup_with_no_equity_recomputes_status(self):
        from desk3.delivery import revalidate_card
        delivered, verdict = revalidate_card(
            _card(option_age_s=300, equity=False), NOW, session_open=True)
        self.assertEqual(verdict, "option_setup_dropped")
        self.assertEqual(delivered["status"], "stale")


class QuoteMapSeamTests(unittest.TestCase):
    def test_stale_and_unstamped_quotes_dropped_fresh_kept(self):
        from desk3.delivery import revalidate_quote_map
        data = {"quotes": {
            "SPY": {"received_at": _iso(NOW - timedelta(seconds=30))},
            "QQQ": {"received_at": _iso(NOW - timedelta(seconds=600))},
            "IWM": {"bid": 1.0}}}
        out, report = revalidate_quote_map(data, NOW)
        self.assertIn("SPY", out["quotes"])
        self.assertNotIn("QQQ", out["quotes"])
        self.assertNotIn("IWM", out["quotes"])
        self.assertEqual(report["quotes"]["QQQ"], "stale")
        self.assertIn("stamp", report["quotes"]["IWM"])

    def test_cycle_seam_drops_stale_quote_and_names_it(self):
        from desk3.cycle import Desk
        root = tempfile.mkdtemp(dir=ROOT)
        desk = Desk(root)

        def producer(pctx):
            return {"quotes": {
                "SPY": {"symbol": "SPY", "bid": 1.0, "ask": 1.1,
                        "received_at": _iso(NOW - timedelta(seconds=30))},
                "QQQ": {"symbol": "QQQ", "bid": 2.0, "ask": 2.1,
                        "received_at": _iso(NOW - timedelta(seconds=900))}}}

        desk.add_producer("quotes", producer, ["quotes"], 60)
        roll = desk.run_cycle(now=NOW)
        self.assertIn("SPY", desk._last_data["quotes"])
        self.assertNotIn("QQQ", desk._last_data["quotes"])
        self.assertEqual(
            roll["delivery_revalidation"]["quotes"]["QQQ"], "stale")


def _daily_doc(rows_by_sym, token=None):
    doc = {"bars": rows_by_sym}
    if token:
        doc["next_page_token"] = token
    return doc


def _row(day, o=100.0, h=101.0, l=99.0, c=100.5):
    return {"t": f"{day}T04:00:00Z", "o": o, "h": h, "l": l, "c": c, "v": 1000}


class WarmBarsGateTests(unittest.TestCase):
    """_fetch is driven through the netfetch seam with canned docs."""

    def _run_fetch(self, docs, timeframe="1Day", start="2026-10-01T00:00:00Z",
                   symbols=("SPY",), expected_last=None, session_drops=None):
        import desk3.netfetch as NF
        import desk3.warm as W
        queue = list(docs)
        orig = NF.fetch_json
        NF.fetch_json = lambda url, headers=None, timeout=30: queue.pop(0)
        try:
            return W._fetch(list(symbols), timeframe, start, {},
                            expected_last=expected_last,
                            session_drops=session_drops)
        finally:
            NF.fetch_json = orig

    def test_valid_daily_payload_passes(self):
        rows = [_row("2026-10-26"), _row("2026-10-27")]
        out = self._run_fetch([_daily_doc({"SPY": rows})],
                              expected_last="2026-10-27")
        self.assertEqual(len(out["SPY"]), 2)

    def test_pagination_is_followed_to_completion(self):
        docs = [_daily_doc({"SPY": [_row("2026-10-26")]}, token="tok"),
                _daily_doc({"SPY": [_row("2026-10-27")]})]
        out = self._run_fetch(docs, expected_last="2026-10-27")
        self.assertEqual(len(out["SPY"]), 2)

    def test_symbol_mismatch_fails_whole_payload(self):
        import desk3.warm as W
        with self.assertRaises(W.BarsIntegrityError) as cm:
            self._run_fetch([_daily_doc({"MSFT": [_row("2026-10-27")]})])
        self.assertIn("daily_history_invalid_or_incomplete", str(cm.exception))

    def test_duplicate_date_fails(self):
        import desk3.warm as W
        rows = [_row("2026-10-27"), _row("2026-10-27")]
        with self.assertRaises(W.BarsIntegrityError):
            self._run_fetch([_daily_doc({"SPY": rows})])

    def test_non_positive_ohlc_fails(self):
        import desk3.warm as W
        with self.assertRaises(W.BarsIntegrityError):
            self._run_fetch([_daily_doc({"SPY": [_row("2026-10-27", c=0.0)]})])

    def test_out_of_window_bar_fails(self):
        import desk3.warm as W
        with self.assertRaises(W.BarsIntegrityError):
            self._run_fetch([_daily_doc({"SPY": [_row("2026-09-15")]})])

    def test_history_not_ending_on_expected_session_drops_symbol(self):
        # Session currency is per symbol on a multi symbol union:
        # the stale symbol is dropped and named, never served, and
        # the surviving symbols still land. Corruption (the tests
        # above) fails the whole payload instead.
        rows = [_row("2026-10-26"), _row("2026-10-27")]
        drops = []
        out = self._run_fetch(
            [_daily_doc({"SPY": rows, "QQQ": [_row("2026-10-28")]})],
            symbols=("SPY", "QQQ"), expected_last="2026-10-28",
            session_drops=drops)
        self.assertNotIn("SPY", out)
        self.assertIn("QQQ", out)
        self.assertEqual(drops[0]["symbol"], "SPY")
        self.assertIn("expected_2026-10-28", drops[0]["reason"])

    def test_expected_session_walks_calendar_backwards(self):
        import desk3.warm as W
        # Wed 2026-10-28 10:00 ET: latest completed session is Tue 27th.
        self.assertEqual(W.expected_latest_completed_session(NOW),
                         "2026-10-27")
        # Sat 2026-10-31 12:00 ET: latest completed is Fri 30th.
        sat = datetime(2026, 10, 31, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(W.expected_latest_completed_session(sat),
                         "2026-10-30")
        # Mon 2026-11-02 10:00 ET: still Fri 30th.
        mon = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(W.expected_latest_completed_session(mon),
                         "2026-10-30")
        # Wed 2026-10-28 17:00 ET (after the 16:30 settlement
        # allowance): today is the completed session.
        late = datetime(2026, 10, 28, 21, 0, tzinfo=timezone.utc)
        self.assertEqual(W.expected_latest_completed_session(late),
                         "2026-10-28")


if __name__ == "__main__":
    unittest.main()
