"""CSP-PREFLIGHT-20261104 blockers.

Live failure, 2026-11-03: qqq_put_ladder re-presented a
cash-secured put needing ~$1,040,231 of strike collateral against
an options buying power that fell from $1,025,054 toward
~$880,750, drawing 57 broker 403 rows: the desk burned wire calls
on a verdict the account state already determined.

Cure: the dispatcher refuses a sell_to_open OCC entry locally
when its strike collateral (strike x 100 x contracts, minus the
premium received) exceeds the broker-reported options buying
power, fetched once per Dispatcher and cached. When the broker
cannot report the field, no gate applies (preservation: a broker
that cannot answer must not become a new failure mode).

Fail direction: pre-cure there is no options_buying_power on
either door's get_account and no dispatcher gate, so the
low-buying-power case submits to the broker instead of rejecting
locally.
"""
import os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402

SYM = "QQQ261204P00500000"  # strike 500.000


def _disp(obp_marker):
    broker = FakeBroker(prices={SYM: 3.0})
    if obp_marker is not None:
        broker.options_buying_power = obp_marker
    root = tempfile.mkdtemp(prefix="csp-test-")
    return Dispatcher(root, broker,
                      slices={"qqq_put_ladder": {"capital_usd": 100000.0,
                                                 "cash_usd": 100000.0}}), broker


def _intent(iid, position_intent="sell_to_open", qty=1):
    return {"intent_id": iid, "kind": "entry", "symbol": SYM,
            "side": "sell" if position_intent == "sell_to_open" else "buy",
            "qty": qty, "position_intent": position_intent,
            "price_hint": 3.0}


class CspPreflightTests(unittest.TestCase):
    def test_unaffordable_csp_rejected_locally(self):
        disp, broker = _disp(10_000.0)
        # required 50,000 strike collateral - 300 premium = 49,700
        r = disp.process_intent(_intent("csp-1"), "qqq_put_ladder")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "insufficient_options_bp_csp")
        self.assertEqual(broker.submit_count, 0)

    def test_affordable_csp_passes(self):
        disp, broker = _disp(1_000_000.0)
        r = disp.process_intent(_intent("csp-2"), "qqq_put_ladder")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)

    def test_buy_to_open_unaffected_by_low_options_bp(self):
        disp, broker = _disp(10_000.0)
        r = disp.process_intent(_intent("csp-3", "buy_to_open"),
                                "qqq_put_ladder")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)

    def test_unreported_options_bp_means_no_gate(self):
        disp, broker = _disp(None)
        r = disp.process_intent(_intent("csp-4"), "qqq_put_ladder")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)


if __name__ == "__main__":
    unittest.main()
