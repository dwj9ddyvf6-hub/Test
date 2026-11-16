"""VIRTUAL-BOOK CANARY CONFIG pin (OPERATION FIRING LINE,
2026-11-11).

The canary advance is a config landing: config/virtual_book.json
flips the staged virtual book from dual-read log mode to canary
enforcement for exactly the eleven S4 exit-storm sleeves
(DIAGNOSIS.md S4). This pin keeps the landing honest: the config
must parse, the mode must be canary (a silent revert to log/off
fails here, not in a census weeks later), the canary set must be
exactly the S4 eleven, and every canary name must be a live
roster sleeve (a renamed sleeve must not silently unenforce).
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")

S4_CANARIES = {"grok_sr_spy", "teddy_orb_spy", "trullas_v03",
               "trullas_v06", "trullas_v07", "trullas_v08",
               "saty_magnum", "legends_ema", "phase_daily",
               "raschke_pf3", "leaps_momentum"}


class TestVirtualBookCanaryConfig(unittest.TestCase):
    def test_canary_config_is_the_landed_state(self):
        with open(os.path.join(ROOT, "config", "virtual_book.json")) \
                as f:
            cfg = json.load(f)
        self.assertEqual(cfg.get("mode"), "canary")
        self.assertEqual(set(cfg.get("canary_sleeves") or ()),
                         S4_CANARIES)

    def test_every_canary_is_a_roster_sleeve(self):
        with open(os.path.join(ROOT, "config", "sleeves.json")) as f:
            roster = json.load(f)
        names = set()
        rows = roster if isinstance(roster, list) \
            else roster.get("sleeves") or roster
        if isinstance(rows, dict):
            names = set(rows.keys())
        else:
            for r in rows:
                names.add(r.get("id") or r.get("sleeve_id")
                          or r.get("name"))
        missing = S4_CANARIES - names
        self.assertEqual(missing, set(),
                         f"canary sleeves not on the roster: {missing}")


if __name__ == "__main__":
    unittest.main()
