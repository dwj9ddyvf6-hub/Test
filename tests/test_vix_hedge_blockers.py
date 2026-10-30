"""Blockers: vix_hedge port (batch 8) — PORT-VIX-1.

Oracle: v2 proof/enhance/vix_hedge.json (A/B control/treatment + e2e
entry/exit intents, recorded 2026-10-23) and v2 proof/fixture (fail-
closed, no chain => no intents). Same fixture inputs must produce the
same intents in v3, byte-compared on the recorded fields.
Fail direction: on the pre-port tree adapters.vix_hedge does not exist.
"""
import json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CHAIN = [{"symbol": "VXX270115C00024000", "strike": 24, "expiration": "2027-01-15"}]
QUOTES = {"VXX261218C00020000": {"bid": 2.20, "ask": 2.30},
          "VXX270115C00024000": {"bid": 0.45, "ask": 0.50}}
IMP_POS = [{"symbol": "VXX261218C00020000", "qty": 8, "avg_price": 1.10}]


def bars(px, n=5):
    return [{"t": 1760000000.0 + k * 86400, "o": px, "h": px, "l": px, "c": px, "v": 1000} for k in range(n)]


def view(extra_positions=None, quotes=None, vix=15.0, chain=None):
    return {"bars": {"VXX": bars(20.0), "VIX": bars(vix, 30)},
            "options": {"chains": {"VXX": CHAIN if chain is None else chain},
                        "quotes": QUOTES if quotes is None else quotes},
            "positions": IMP_POS if extra_positions is None else extra_positions}


def ctx(**kw):
    c = {"sleeve_id": "vix_hedge", "session": "2026-10-23",
         "now": "2026-10-23T15:00:00", "equity": 10000.0, "state_dir": "/tmp"}
    c.update(kw)
    return c


class TestVixHedgePort(unittest.TestCase):
    def ev(self, v, c=None):
        from adapters.vix_hedge import evaluate
        return evaluate(v, c or ctx())

    def test_entry_matches_v2_enhance_oracle_control(self):
        # Switch OFF + no positions = v2 enhance "control" intent, byte-equal
        # on every recorded field (intent_id/kind/symbol/side/qty/reason/pi).
        out = self.ev(view(extra_positions=[]),
                      ctx(extra={"vix_hedge_improve": {"adopt_imported_position": False}}))
        self.assertEqual(out, [{
            "intent_id": "vix_hedge-20261023T150000-1", "kind": "entry",
            "symbol": "VXX270115C00024000", "side": "buy", "qty": 2,
            "order_type": "market", "limit_price": None, "stop_price": None,
            "reason": "vix_hedge long_call: occ=VXX270115C00024000 strike=24.00 expiry=2027-01-15 dte=84 ask=0.50 vix=15.00 pctl30=0.0 structure=long_call dte_window=60-110 strike_rule=nearest(1.20*spot) brake_exempt=tail_hedge",
            "time_in_force": "day", "position_intent": "buy_to_open",
            "price_hint": 20.0}])

    def test_treatment_adopts_import_profit_target_exit_oracle(self):
        # Default ON + held adopted OCC = v2 enhance "treatment" exit.
        out = self.ev(view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["symbol"], "VXX261218C00020000")
        self.assertEqual(out[0]["qty"], 8)
        self.assertEqual(out[0]["side"], "sell")
        self.assertEqual(out[0]["position_intent"], "sell_to_close")
        self.assertEqual(out[0]["reason"],
                         "vix_hedge exit: profit_target_100pct occ=VXX261218C00020000")

    def test_exit_vol_spike(self):
        v = view(); v["bars"]["VIX"] = bars(31.0, 30)
        v["options"]["quotes"] = dict(QUOTES, VXX261218C00020000={"bid": 1.0, "ask": 1.1})
        out = self.ev(v)
        self.assertEqual(len(out), 1)
        self.assertIn("vol_spike_take_profit", out[0]["reason"])

    def test_exit_dte_floor(self):
        # Adopted OCC expiry 2026-12-18; session 2026-11-30 => dte 18 <= 21.
        v = view(); v["options"]["quotes"] = dict(QUOTES, VXX261218C00020000={"bid": 1.0, "ask": 1.1})
        out = self.ev(v, ctx(session="2026-11-30", now="2026-11-30T15:00:00"))
        self.assertEqual(len(out), 1)
        self.assertIn("dte_floor_21", out[0]["reason"])

    def test_refusal_not_complacent(self):
        v = view(extra_positions=[]); v["bars"]["VIX"] = bars(25.0, 30)
        # vix 25, pctl: last equals all => 0% below? window all equal -> pctl 0 <25 complacent!
        # Use rising closes so pctl is high: last is max.
        v["bars"]["VIX"] = [{"t": 1760000000.0 + k * 86400, "o": 10 + k, "h": 10 + k,
                             "l": 10 + k, "c": 10.0 + k, "v": 1} for k in range(30)]
        self.assertEqual(self.ev(v), [])

    def test_refusal_no_vix_read_fail_closed(self):
        v = view(extra_positions=[]); v["bars"] = {"VXX": bars(20.0)}
        self.assertEqual(self.ev(v), [])

    def test_refusal_no_vehicle_no_chain(self):
        # v2 fixture oracle: complacent tape, no chain => no intents.
        v = view(extra_positions=[], chain=[])
        self.assertEqual(self.ev(v), [])

    def test_refusal_spread_gate(self):
        v = view(extra_positions=[])
        v["options"]["quotes"] = {"VXX270115C00024000": {"bid": 0.10, "ask": 0.50}}
        self.assertEqual(self.ev(v), [])

    def test_refusal_adopted_held_no_exit_blocks_second_entry(self):
        v = view(); v["options"]["quotes"] = dict(QUOTES, VXX261218C00020000={"bid": 1.00, "ask": 1.10})
        self.assertEqual(self.ev(v), [])  # max-1: held hedge, no exit due

    def test_config_row_and_registry_declaration(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = [s for s in cfg["sleeves"] if s["id"] == "vix_hedge"]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["cadence_s"], 300)
        self.assertEqual(r["slice"]["capital_usd"], 11000.0)  # R3-VIXHEDGE-20261025
        self.assertEqual(r["session"], "rth")
        self.assertEqual(set(r["inputs"]), {"bars", "options", "positions"})
        from adapters.vix_hedge import INPUTS, PRODUCERS
        self.assertEqual(tuple(r["inputs"]), INPUTS)
        self.assertTrue(PRODUCERS)


if __name__ == "__main__":
    unittest.main()
