"""Blockers: SATY-DAY-CHAIN-DIALECT cure (2026-11-04).

Root cause, the BTA-ONEBAR-UNFED-20261030 shape exactly: saty_day
was UNFED for all 78 cycles on 2026-11-03 and rsi_meanrev_options
shares the defect. Both declare the v2-dialect key "options_chains"
(port_batch6 carried v2's producer-registry names into the port).
No v3 producer emits that key; the chain both sleeves actually
consume rides the produced key "options_chain" (desk3/bridge.py
ViewContext.options_chain reads view["options_chain"]; port.bridge
serve_options is the fallback path). Neither sleeve reads
view["options_chains"] anywhere — the declaration names a key in a
dialect this desk does not speak, so the registry's fed check could
never pass.

Cure, per the BTA precedent: fix the DECLARATION at every place it
lives (desk_sleeves module INPUTS, config/sleeves.json rows,
port_batch6 _ROWS) from "options_chains" to the produced key
"options_chain" the accessors read, and shrink the legacy ledger
in test_bta_unfed_20261030_blockers.py by removing "options_chains"
(its own law: removing a key from declarations must remove it
there). No alias producer key was added: that would be a second
source of truth for the same chain.

Fail direction: pre-cure, all three declaration assertions fail
and the produced-inputs check names options_chains unproduced.
"""
import importlib, json, os, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

IDS = ("saty_day", "rsi_meanrev_options")


class SatyChainDialectTests(unittest.TestCase):
    def test_declarations_name_the_produced_key(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            mod = importlib.import_module(f"desk_sleeves.{sid}")
            self.assertNotIn("options_chains", mod.INPUTS, sid)
            self.assertIn("options_chain", mod.INPUTS, sid)
            self.assertNotIn("options_chains",
                             rows[sid].get("inputs", []), sid)
            self.assertIn("options_chain",
                          rows[sid].get("inputs", []), sid)
            self.assertEqual(tuple(mod.INPUTS),
                             tuple(rows[sid]["inputs"]), sid)

    def test_declared_inputs_are_produced(self):
        from desk3.run_live import build_desk
        desk, _rows = build_desk(ROOT, dispatch=False, env={})
        outs = set()
        for spec in desk.registry.producers.values():
            outs.update(spec["outputs"])
        for sid in IDS:
            for key in desk.registry.sleeves[sid]["inputs"]:
                self.assertIn(key, outs, f"{sid} declares unproduced {key}")


if __name__ == "__main__":
    unittest.main()
