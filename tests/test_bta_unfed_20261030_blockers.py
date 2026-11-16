"""BTA-ONEBAR-UNFED-20261030 contract blockers.

Root cause (RESEARCH-R2, deep-dive-repair-20261030): the three
bta_onebar adapters3 modules and their config/sleeves.json rows
declared a bare input key bars_30min that NO registered producer
emits (BarsProjection tf map covers only bars_1day, bars_1hour,
bars_5min, bars_1min; the literal bars:SYM:30Min keys are the real
feed contract and were already produced live). desk3/registry.py
fed_states marks any sleeve with an unproduced declared input
UNFED, so no runner restart could ever feed them.

Cure: the redundant bars_30min declaration was removed from all
three adapters3 modules AND all three config rows. No bars_30min
producer was added (that would be a second source of truth).

These tests pin the general contract the install tests missed:
every roster sleeve declared input must be a registered producer
output, or sit on the dated, shrink-only legacy ledger below
(pre-existing unproduced keys owned by other lanes, enumerated
2026-10-30 from a live build_desk registry read; bars_30min is
deliberately NOT on it). A new unproduced declared input anywhere
on the roster fails this test by name.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

BTA_IDS = ("bta_onebar_qqq", "bta_onebar_basket", "bta_onebar_rth")

# Dated 2026-10-30, shrink-only. Keys declared by roster sleeves
# but emitted by no registered producer, pre-existing this cure
# and owned by their own lanes. Removing a key from production
# declarations must also remove it here; adding a key here to
# silence a new failure is forbidden (write the producer or drop
# the declaration instead).
LEGACY_UNPRODUCED_KEYS = {
    # TENSOR-SERVE-SHAPE-20261112 shrink: "extra" is produced now
    # (desk3.producers.TensorG4Events serves view["extra"] with the
    # tensor_G4_events bridge from the bundle's native product);
    # the aster_tensor_leaps pair are its consumers.
    # FEED80-20261114 shrink: "hedge_signal" and "midna_signals"
    # are produced now (desk3.producers3.MidnaSignalsProducer over
    # the desk's own swing-timing product, commit 1134e7f) and
    # "opening_events" is produced now
    # (desk3.producers3.OpeningEventsProducer over the recovered-R5
    # assembler drop, commit 5f61508); their consumers are the
    # s_mn_* sleeves and the aster_open_gamma pair. The three
    # entries leave the ledger below; the shrink direction is the
    # ledger working as designed.
    # IV-PRODUCER-20261114 shrink (landed by Lane C, 3ca0c78; the
    # shrink itself applied by Lane A with its gate run): "iv" is
    # produced now (desk3.producers.IVProducer over the desk's
    # AlpacaOptions route); iron_condor is its consumer.
    # CURE-6-RECONCILIATION-20261114 shrink (parent board): the
    # "midna_fires" entry added the same day by UNPARK-REGISTRY
    # leaves again because its only declarations were reverted by
    # the reconciliation — desk3/lazarus_midna declares INPUTS=
    # (tensor,bars,positions), so the four s_mn fire consumers
    # declare tensor, and no roster sleeve declares midna_fires.
    # A ledger key no sleeve declares is stale by this test's own
    # rule; the shrink direction is the ledger working as designed.
    # CLEAR-THE-BOARD-20261114 shrink: "milkman_0dte_chain" is
    # produced now (desk3.producers3.MilkmanChainProducer over
    # desk3/milkman_chain.py); mk_zerodte_spx is its consumer.
    # The entry leaves the ledger; the shrink direction is the
    # ledger working as designed.
    # SLEEVE-FIRING-20261111 shrink: "journal", "latest_quotes",
    # "options.chain" and "options:chains" declarations were cured
    # to the keys the sleeves' code actually reads (the sleeves' own
    # state-dir journal; view["quotes"]; view["options"]) in config
    # and module INPUTS; no roster sleeve declares them any more.
    # ALT-DATA-20261112 shrink: "alt_data" is produced now
    # (desk3.producers3.AltDataProducer over the EDGAR band drop);
    # s_cl_qm_small is its consumer.
}


def _producer_outputs():
    from desk3.run_live import build_desk
    desk, _rows = build_desk(ROOT, dispatch=False, env={})
    outs = set()
    for spec in desk.registry.producers.values():
        outs.update(spec["outputs"])
    return desk, outs


class TestBtaUnfedCure(unittest.TestCase):
    def test_bars_30min_declared_nowhere(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        for row in cfg["sleeves"]:
            self.assertNotIn("bars_30min", row.get("inputs", []), row["id"])
        for sid in BTA_IDS:
            mod = importlib.import_module(f"adapters3.{sid}")
            self.assertNotIn("bars_30min", mod.INPUTS, sid)

    def test_bta_inputs_all_produced_and_config_matches(self):
        desk, outs = _producer_outputs()
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        for sid in BTA_IDS:
            mod = importlib.import_module(f"adapters3.{sid}")
            row = [r for r in cfg["sleeves"] if r["id"] == sid][0]
            self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]), sid)
            for key in mod.INPUTS:
                self.assertIn(key, outs, f"{sid} declares unproduced {key}")

    def test_roster_contract_no_new_unproduced_inputs(self):
        desk, outs = _producer_outputs()
        offenders = {}
        for sid, spec in desk.registry.sleeves.items():
            bad = [k for k in spec["inputs"]
                   if k not in outs and k not in LEGACY_UNPRODUCED_KEYS]
            if bad:
                offenders[sid] = bad
        self.assertEqual(offenders, {})

    def test_legacy_ledger_is_real_and_shrink_only(self):
        desk, outs = _producer_outputs()
        declared = set()
        for spec in desk.registry.sleeves.values():
            declared.update(spec["inputs"])
        for key in LEGACY_UNPRODUCED_KEYS:
            self.assertIn(key, declared, f"stale ledger entry {key}")
            self.assertNotIn(key, outs, f"ledger entry now produced {key}")
        self.assertNotIn("bars_30min", LEGACY_UNPRODUCED_KEYS)


if __name__ == "__main__":
    unittest.main()
