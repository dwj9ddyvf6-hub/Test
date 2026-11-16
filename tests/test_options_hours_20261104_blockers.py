"""Blockers: OPTIONS-HOURS door refusal (cure 2026-11-04).

Live failure, 2026-11-03 evening: five sleeves re-emitted exits for
the same 6 SPY261204P00752000 puts every cycle after the close; each
submit drew the broker's deterministic HTTP 422 "options market
orders are only allowed during market hours" — 220 broker rows
(44 per sleeve) for a verdict that cannot change until the open.
Alpaca options trade only in the regular session (Mon-Fri
09:30-16:00 ET); equity market orders are queued by the broker
after hours and options LIMIT orders rest, so the refusal is
scoped to options (OCC shape) MARKET orders only.

Cure: PaperDoor refuses that exact shape locally while the ET
clock is outside the regular session, raising the broker-shaped
FetchError(422). Sleeve re-emission behaviour, dispatcher
journaling and terminal classification are unchanged; the wire
call is the only thing removed. The broker remains the backstop
on holidays and early closes (a wrong-open clock still gets the
broker's own answer; a wrong-closed clock can only delay an exit
that re-emits every cycle).

Fail direction: pre-cure the after-hours options market submit
reaches the (monkeypatched) wire and no FetchError is raised.
"""
import os, sys, unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import broker, netfetch  # noqa: E402
from desk3.netfetch import FetchError  # noqa: E402

ET = ZoneInfo("America/New_York")
OCC = "SPY261204P00752000"
WED_1000 = datetime(2026, 11, 4, 10, 0, tzinfo=ET)
WED_2000 = datetime(2026, 11, 4, 20, 0, tzinfo=ET)
SAT_1100 = datetime(2026, 11, 7, 11, 0, tzinfo=ET)


class OptionsHoursTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self._fetch = netfetch.fetch_json
        self.addCleanup(setattr, netfetch, "fetch_json", self._fetch)
        netfetch.fetch_json = lambda *a, **k: self.calls.append((a, k)) or {}

    def door(self, now):
        return broker.PaperDoor(
            env={"ALPACA_KEY_ID": "paper-key",
                 "ALPACA_SECRET_KEY": "paper-secret"},
            now_fn=lambda: now)

    def test_options_market_after_hours_refused_locally(self):
        with self.assertRaises(FetchError) as cm:
            self.door(WED_2000).submit_order("c1", OCC, "sell", 6, "market")
        self.assertEqual(cm.exception.status, 422)
        self.assertIn("market hours", str(cm.exception.body))
        self.assertEqual(self.calls, [])

    def test_options_market_on_weekend_refused_locally(self):
        with self.assertRaises(FetchError):
            self.door(SAT_1100).submit_order("c2", OCC, "sell", 6, "market")
        self.assertEqual(self.calls, [])

    def test_options_market_in_session_reaches_wire(self):
        self.door(WED_1000).submit_order("c3", OCC, "sell", 6, "market")
        self.assertEqual(len(self.calls), 1)

    def test_options_limit_after_hours_reaches_wire(self):
        self.door(WED_2000).submit_order("c4", OCC, "sell", 6, "limit",
                                         limit_price=10.0,
                                         time_in_force="gtc")
        self.assertEqual(len(self.calls), 1)

    def test_equity_market_after_hours_reaches_wire(self):
        self.door(WED_2000).submit_order("c5", "SPY", "sell", 6, "market")
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
