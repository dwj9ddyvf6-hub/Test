"""Blockers: PF_ foreign-contract door refusal (cure 2026-11-04).

Live failure, 2026-11-03: free_kraken_ada_breakdown emitted 6 intents
for PF_ADAUSD (a Kraken futures contract key, the sleeve's native
instrument), all rejected by the broker HTTP 422 code 42210000
"asset PF_ADAUSD not found" — 30 dispatcher rows burned on the wire
for a deterministic verdict. Alpaca lists no PF_ contracts; the
answer can never change for this symbol shape.

Cure: PaperDoor refuses PF_-prefixed symbols locally, raising the
same FetchError(422, body={code 42210000, message asset-not-found})
the broker itself returns, so dispatcher journaling, terminal-422
classification and pending behaviour are byte-identical, minus the
wire call. The dispatcher door contract is untouched: the kraken
e2e (test_harden_cure_batch3_blockers) dispatches PF_ADAUSD through
a FakeBroker and still fills, by design — these sleeves were built
for a Kraken door; whether they are parked or redesigned for spot
ADA is the owner's ruling, named in BUGLOG_2026-11-04.md.

Fail direction: pre-cure, submit_order posts to the wire (the
monkeypatched fetch records a call) and no FetchError is raised.
"""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import broker, netfetch  # noqa: E402
from desk3.netfetch import FetchError  # noqa: E402


class PfDoorTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self._fetch = netfetch.fetch_json
        self.addCleanup(setattr, netfetch, "fetch_json", self._fetch)
        netfetch.fetch_json = lambda *a, **k: self.calls.append((a, k)) or {}

    def door(self):
        return broker.PaperDoor(env={"ALPACA_KEY_ID": "paper-key",
                                     "ALPACA_SECRET_KEY": "paper-secret"})

    def test_pf_symbol_refused_locally_with_broker_shaped_422(self):
        with self.assertRaises(FetchError) as cm:
            self.door().submit_order("coid-1", "PF_ADAUSD", "sell", 1,
                                     "market")
        self.assertEqual(cm.exception.status, 422)
        self.assertIn("42210000", str(cm.exception.body))
        self.assertIn("PF_ADAUSD", str(cm.exception.body))
        self.assertEqual(self.calls, [])

    def test_listed_symbol_still_reaches_the_wire(self):
        self.door().submit_order("coid-2", "ADA/USD", "buy", 1, "market")
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
