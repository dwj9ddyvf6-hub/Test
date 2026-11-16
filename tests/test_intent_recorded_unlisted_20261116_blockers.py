"""INTENT-RECORDED-UNLISTED-20261116 blocker.

Live defect, Sunday 2026-11-15: 71 distinct entry intents from
intent-graded sleeves were submitted to the broker and rejected
HTTP 422 code 42210000 asset-not-found (142 broker rows):
free_kraken_enj_spot ENJ/USD 51, free_kraken_ada_breakdown
PF_ADAUSD 10, aster_abs_enj_4h ENJ/USD 10. ENJ/USD is not listed
at Alpaca and PF_ADAUSD is a Kraken perpetual-futures key, not an
Alpaca instrument; all three sleeves are registered intent-graded
(their roster rows state they evaluate and forward-grade from the
dispatcher record, execution failing closed at the broker seam),
and CONV-27's grader already reads their entry intents as shadow
entries. The broker submission was pure waste motion.

Cure: at the live door, a non-exit entry in a proven-unlisted
symbol (ENJ/USD or a PF_ key) is journaled as an intent_recorded
row and consumed with status "recorded"; submit_order is never
called. The conversion grader's load_intent_entries accepts the
recorded rows beside the historical broker_rejected_terminal
rows, so the graded population is unchanged. Test doubles keep
the old behavior (the kraken e2e contracts dispatch these symbols
through a FakeBroker by design).

Fail direction: on the pre-cure tree the ENJ and PF entries reach
submit_order (submit_count grows) and return queued/rejected from
the broker error path, and load_intent_entries sees no recorded
rows.

ENJ-PAPER-20261116 amendment (dated estate form, same day): the
ENJ leg of this cure is superseded by the escalation-2 landing.
ENJ-class entries no longer stop at recorded — they fill in the
free_kraken paper form at the door (never submitted, exactly as
this cure required) — and ENJ-class exits fill against the
sleeve's own paper position instead of reaching the wire. The
PF_ leg of this file stands verbatim: PF entries are still
recorded, never submitted, and the grader loader still unions
recorded rows. The two tests below were amended in place to the
new ENJ form; their PF and listed-symbol assertions are
unchanged.
"""
import json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402

SLICES = {"free_kraken_enj_spot": {"capital_usd": 10000, "cash_usd": 10000},
          "free_kraken_ada_breakdown": {"capital_usd": 10000,
                                        "cash_usd": 10000},
          "plain": {"capital_usd": 10000, "cash_usd": 10000}}


class LiveBookFake(FakeBroker):
    """A FakeBroker standing at the live door (PaperDoor's class
    flag), so the dispatcher's live-book paths engage."""
    live_book = True


def _entry(iid, symbol, side="buy", qty=2):
    return {"intent_id": iid, "kind": "entry", "symbol": symbol,
            "side": side, "qty": qty, "order_type": "market",
            "time_in_force": "gtc", "price_hint": 100.0}


def _disp(tmp, broker):
    return Dispatcher(tmp, broker, slices=dict(SLICES),
                      price_lookup=lambda s: 100.0)


class TestIntentRecorded(unittest.TestCase):
    def test_enj_and_pf_entries_recorded_without_submit(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 100.0,
                                      "PF_ADAUSD": 100.0})
        d = _disp(tmp, broker)
        # ENJ-PAPER-20261116: the ENJ entry fills in the paper
        # form (status filled, venue kraken_paper) instead of
        # stopping at recorded; it still never reaches the seam.
        r = d.process_intent(_entry("enj-1", "ENJ/USD"),
                             "free_kraken_enj_spot")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["venue"], "kraken_paper")
        r = d.process_intent(_entry("pf-1", "PF_ADAUSD", side="sell"),
                             "free_kraken_ada_breakdown")
        self.assertEqual(r["status"], "recorded")
        self.assertEqual(broker.submit_count, 0,
                         "no unlisted entry may reach the broker seam")
        rows = [json.loads(l) for l in
                open(os.path.join(tmp, "state", "dispatcher.jsonl"))]
        rec = [x for x in rows if x.get("event") == "intent_recorded"]
        self.assertEqual(len(rec), 1)
        self.assertEqual({x["intent_id"] for x in rec}, {"pf-1"})
        fills = [x for x in rows if x.get("event") == "fill"]
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["intent_id"], "enj-1")
        self.assertEqual(fills[0]["venue"], "kraken_paper")
        # A rebuilt dispatcher treats the filled intent as spent.
        d2 = _disp(tmp, broker)
        r = d2.process_intent(_entry("enj-1", "ENJ/USD"),
                              "free_kraken_enj_spot")
        self.assertEqual(r["status"], "duplicate")
        self.assertEqual(broker.submit_count, 0)

    def test_listed_symbol_still_submits_and_exit_passes(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"SPY": 100.0, "ENJ/USD": 100.0})
        broker.positions["ENJ/USD"] = 10.0
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("spy-1", "SPY"), "plain")
        self.assertEqual(r["status"], "filled", r)
        # ENJ-PAPER-20261116: an ENJ-class exit no longer reaches
        # the wire at all — the paper book is its book of record,
        # and this sleeve holds no paper position, so the exit
        # fails closed by its paper name and submits nothing. The
        # pre-amendment assertion (the exit reaches the door
        # against the broker position) is superseded: submitting
        # ENJ to Alpaca is the one outcome both cures forbid.
        r = d.process_intent(
            {"intent_id": "enj-exit", "kind": "exit", "symbol": "ENJ/USD",
             "side": "sell", "qty": 2, "order_type": "market",
             "time_in_force": "gtc", "price_hint": 100.0,
             "position_intent": "sell_to_close"},
            "free_kraken_enj_spot")
        self.assertNotEqual(r.get("reason"),
                            "intent_recorded_unlisted_symbol")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected",
                          "exit_satisfied_no_paper_position"))
        self.assertEqual(broker.submit_count, 1,
                         "only the listed entry reaches the door; "
                         "the ENJ exit never does")

    def test_test_double_keeps_fake_door_behavior(self):
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"ENJ/USD": 100.0})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("enj-fake", "ENJ/USD"),
                             "free_kraken_enj_spot")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)


class TestGraderSeesRecordedIntents(unittest.TestCase):
    def test_loader_unions_recorded_and_terminal_rows(self):
        from desk3.conversion_shadow import load_intent_entries
        tmp = tempfile.mkdtemp()
        state = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state, "s_enj"))
        rows = [
            {"event": "intent_recorded", "intent_id": "r1",
             "sleeve": "s_enj", "symbol": "ENJ/USD", "side": "buy",
             "qty": 3, "kind": "entry"},
            {"event": "broker_rejected_terminal", "intent_id": "t1",
             "sleeve": "s_enj", "symbol": "ENJ/USD", "side": "sell",
             "qty": 1, "kind": "entry"},
            {"event": "intent_recorded", "intent_id": "x1",
             "sleeve": "s_enj", "symbol": "ENJ/USD", "side": "buy",
             "qty": 1, "kind": "exit"},
        ]
        with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        with open(os.path.join(state, "s_enj", "journal.jsonl"),
                  "w") as fh:
            for iid in ("r1", "t1", "x1"):
                fh.write(json.dumps(
                    {"event": "intent", "intent_id": iid,
                     "ts": "2026-11-16T15:00:00+00:00"}) + "\n")
        entries = load_intent_entries(tmp, "2026-11-16", {"s_enj"})
        self.assertEqual({e["intent_id"] for e in entries},
                         {"r1", "t1"})
        by_id = {e["intent_id"]: e for e in entries}
        self.assertEqual(by_id["r1"]["dir"], 1)
        self.assertEqual(by_id["t1"]["dir"], -1)


if __name__ == "__main__":
    unittest.main()
