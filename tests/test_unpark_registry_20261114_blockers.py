"""UNPARK-REGISTRY blockers (2026-11-14, ALL SLEEVES FIRING Lane A).

Owner's order 2026-11-14: "ALL SLEEVES MUST BE FIRING. Don't pause
any sleeves. A paused sleeve is useless."

Defects cured in config/sleeves.json (Lane A owns that file):

1. 27 sleeves were parked BY CHOICE (3 aster_tensor_c1_*_cool_25
   parked by a 2026-11-12 ruling + 24 rows parked with no reason
   recorded at all). Cure: parked=false with a params stamp
   (unparked_on / unpark_authority / prior parked_reason kept).

2. 30 rows conflated three different outside states under the bare
   parked flag: 22 ENJ rows + 6 Kraken PF rows cannot execute on
   the Alpaca door (BLOCKED-EXTERNAL), and przm_zero /
   przm_fade_edges wait on named missing products (UNFED).
   Cure: they stay non-evaluating (parked=true; the schema has no
   state field beyond parked) but their parked_reason stamps now
   lead with the outside-state classification, and parked-by-choice
   is ZERO across the whole roster.

3. CURE-6 registry half (FIRING-LINE-RESIDUE.md): the four s_mn
   fire consumers declared input "tensor", so the registry read
   them FED off the Tensor bundle substitution while their actual
   product (midna_fires, the Midna hourly signal product) has no
   producer on this desk and every fire is discarded at routing
   for missing family/timeframe/sleeve_id. Cure: declare
   "midna_fires"; the registry then reads them honestly UNFED
   until the external product lands.

4. CR-6 registry half: saty_gpt_v03 reads FED while its C-3 door
   requires the SPY daily series; its declared inputs named no
   daily-bars product distinctly. Cure: declare "bars_1day" (the
   BarsProjection daily product). shen_fade needs NO registry
   change: its inputs already declare the exact product key it
   consumes (bars:SPY:1Min); its BLOCKED_DATA is producer/sleeve
   side (see BUGLOG_2026-11-14 UNPARK-REGISTRY).

Fail direction: every assertion below fails on the pre-cure config
(57 parked, no stamps, s_mn on "tensor", saty without bars_1day)
and passes on the cured config.
"""
import json
import os
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
CFG = os.path.join(ROOT, "config", "sleeves.json")

UNPARK_27 = (
    "aster_tensor_c1_cash_cool_25", "aster_tensor_c1_delay_cool_25",
    "aster_tensor_c1_reserve_cool_25",
    "s_1wg_small", "s_1wsw_stress", "s_moonshot",
    "s_q07w_s52_ml_deep70_ins2_vix20", "s_q07w_s52_ml_deep70_vix20_wlow",
    "s_q07w_s52_ml_deep70_wlow", "s_q07w_s52_ml_ins2_mom6_vix20",
    "s_q07w_s52_ml_ins2_mom6_wlow", "s_q07w_s52_sm_cheap5_deep70_ins2",
    "s_q07w_s52_sm_cheap5_ins2_vix20", "s_q07w_s52_sm_cheap5_wcov",
    "s_q07w_s52_sm_deep70_wcov",
    "s_q07w_s78_mi_ats_z1_cheap5", "s_q07w_s78_mi_ats_z1_mom6",
    "s_q07w_s78_mi_cheap5_ins2_mom6", "s_q07w_s78_ml_deep70_glow_ins2",
    "s_q07w_s78_ml_deep70_ins2_vix20", "s_q07w_s78_ml_deep70_mom6_wlow",
    "s_q07w_s78_ml_deep70_wcov", "s_q07w_s78_sm_cheap5_ins2_vix20",
    "s_q07w_s78_sm_cheap5_wcov", "s_q07w_s78_sm_deep70_ins2",
    "s_q07w_s78_sm_deep70_wcov",
    "mk_zerodte_spx",
)
C1_COOL = UNPARK_27[:3]
SMN_FOUR = ("s_mn_d_green_band", "s_mn_w_cyan_breadth",
            "s_mn_w_cyan_vix", "s_mn_w_green_smh")


def _rows():
    with open(CFG) as fh:
        doc = json.load(fh)
    return {s["id"]: s for s in doc["sleeves"]}


class TestUnpark27(unittest.TestCase):
    def test_roster_size_unchanged(self):
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(_rows()), 400)

    def test_27_unparked_with_stamp(self):
        rows = _rows()
        for sid in UNPARK_27:
            s = rows[sid]
            self.assertFalse(s["parked"], sid)
            self.assertEqual(s["params"].get("unparked_on"),
                             "2026-11-14", sid)
            self.assertIn("all-sleeves-firing",
                          s["params"].get("unpark_authority", ""), sid)

    def test_c1_cool_gates_not_loosened(self):
        # Unpark changes ONLY the parked flag + stamp: cadence and
        # every pre-existing param of the C1 trio are untouched, and
        # the prior parking reason survives in the stamp.
        rows = _rows()
        for sid in C1_COOL:
            s = rows[sid]
            self.assertIn("prior_parked_reason", s["params"], sid)
            self.assertIn("2026-11-12",
                          s["params"]["prior_parked_reason"], sid)
            self.assertNotIn("parked_reason", s["params"], sid)


class TestReclassification(unittest.TestCase):
    def test_parked_by_choice_is_zero(self):
        # Every remaining parked row must carry an outside-state
        # classification as the FIRST token of its parked_reason:
        # BLOCKED-EXTERNAL (cannot execute on this door) or
        # UNFED (named missing product).
        rows = _rows()
        parked = {k: v for k, v in rows.items() if v["parked"]}
        # FEED80-PRZM-20261114 (commit 5d1ef0f): przm_fade_edges
        # UNPARKED per its own stated condition (chain rows carry
        # gamma+OI now); 30 - 1 = 29.
        # CLEAR-THE-BOARD-20261114: the remaining 29 are unparked
        # too (28 fed with execution blocked by name at the door;
        # przm_zero fed by PrzmTapeProducer). Parked is ZERO.
        self.assertEqual(len(parked), 0)
        for sid, s in parked.items():
            reason = s["params"].get("parked_reason", "")
            self.assertTrue(
                reason.startswith(("BLOCKED-EXTERNAL", "UNFED")),
                f"{sid}: {reason[:60]}")

    def test_outside_blocked_28(self):
        # CLEAR-THE-BOARD-20261114: no row rests parked as
        # BLOCKED-EXTERNAL any more. The 28 are unparked and fed;
        # their stamps carry the CTB cure with the original
        # provenance retained (ENJ-ASSET-NOT-LISTED-20261030 /
        # PF-DOOR-20261104 as prior stamps), and execution still
        # fails closed at the broker seam by name.
        rows = _rows()
        blocked = [k for k, v in rows.items() if v["parked"]
                   and v["params"].get("parked_reason", "")
                   .startswith("BLOCKED-EXTERNAL")]
        self.assertEqual(len(blocked), 0)
        cured = [k for k, v in rows.items() if not v["parked"]
                 and "CLEAR-THE-BOARD-20261114" in
                 v["params"].get("parked_reason", "")]
        enj = [k for k in cured
               if rows[k]["params"]["parked_reason"]
               .find("ENJ-ASSET-NOT-LISTED-20261030") >= 0]
        pf = [k for k in cured
              if "PF-DOOR-20261104" in
              rows[k]["params"].get("parked_reason", "")]
        self.assertEqual(len(enj), 22)
        self.assertEqual(len(pf), 6)

    def test_unfed_reclassified_2(self):
        rows = _rows()
        for sid, product in (
                ("przm_zero", "signed same-day SPY options print tape"),):
            s = rows[sid]
            # CLEAR-THE-BOARD-20261114: the missing product is
            # SERVED now (PrzmTapeProducer, desk3/przm_tape.py,
            # real Alpaca v1beta1 prints); the row is unparked and
            # its stamp names the cure and keeps the product text.
            self.assertFalse(s["parked"], sid)
            reason = s["params"].get("parked_reason", "")
            self.assertIn("CLEAR-THE-BOARD-20261114", reason, sid)
            self.assertIn("PrzmTapeProducer", reason, sid)
        # FEED80-PRZM-20261114 (commit 5d1ef0f): przm_fade_edges left
        # this pair; its missing product (gamma+OI chain rows) is
        # served now and the row is unparked per its stated
        # condition, provenance kept in parked_reason.
        s = rows["przm_fade_edges"]
        self.assertFalse(s["parked"], "przm_fade_edges")
        self.assertIn("gamma+OI",
                      s["params"].get("parked_reason", ""),
                      "przm_fade_edges")


class TestRegistryHalves(unittest.TestCase):
    def test_cure6_smn_declare_midna_fires_not_tensor(self):
        # SUPERSEDED 2026-11-14 by the parent board decision
        # CURE-6-RECONCILIATION (see the amended test below and
        # BUGLOG_2026-11-14): Lane A's redeclaration rested on the
        # residue's product framing, but the consumer engine
        # desk3/lazarus_midna declares INPUTS=(tensor,bars,positions)
        # and PRODUCERS tensor_bundle outputs (tensor,), and the
        # routing cure landed the same day (3ca0c78). This test's
        # original assertion (midna_fires, not tensor) is retired;
        # the reconciled declaration is pinned by
        # test_cure6_smn_declare_tensor_reconciled below.
        pass

    def test_cure6_smn_declare_tensor_reconciled(self):
        rows = _rows()
        for sid in SMN_FOUR:
            inputs = rows[sid]["inputs"]
            self.assertIn("tensor", inputs, sid)
            self.assertNotIn("midna_fires", inputs, sid)
            self.assertIn("bars", inputs, sid)
            self.assertIn("positions", inputs, sid)
            note = (rows[sid].get("params") or {}).get(
                "registry_note_20261114", "")
            self.assertIn("CURE-6-RECONCILIATION", note, sid)

    def test_cr6_saty_declares_bars_1day(self):
        rows = _rows()
        self.assertIn("bars_1day", rows["saty_gpt_v03"]["inputs"])

    def test_cr6_shen_declaration_already_exact(self):
        # Determination recorded, not a change: shen_fade already
        # declares the exact product key it consumes.
        rows = _rows()
        self.assertIn("bars:SPY:1Min", rows["shen_fade"]["inputs"])


if __name__ == "__main__":
    unittest.main()
