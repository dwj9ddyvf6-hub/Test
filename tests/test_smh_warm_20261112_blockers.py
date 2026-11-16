"""SMH warm-universe blockers (2026-11-12, Firing Line follow-up).

Defect: rule_1h_cyan_raw's fire_passes requires smhUp == 1, and the
1H scorer computes smhUp from an SMH daily series. No SMH series
existed anywhere in the estate: SMH sat only in the genome_1838
universe list, which desk3/warm.py desk_symbols() never reads, so
every rule_fires_1h fire carried smhUp=null and the sleeve failed
closed forever.

Cure: SMH joins CORE_SYMBOLS in desk3/warm.py (a market-context
index like SPY/QQQ/IWM/DIA, its semantic home), and the research
build wires daily["SMH"] into the scorer as smhDaily. The rejected
route, adding SMH to config/universes.json basket_41, is pinned
shut below: basket_41 is a trading universe read by the Tensor
universe, seven adapters and options warming; putting a context
index there would widen the blast radius desk-wide.

Named behavior consequence: desk3/lazarus_midna.py's smh_calm gate
reads SMH bars and previously always skipped for want of them; with
the series served, the gate evaluates as the sleeve code designs.
No sleeve logic changed.

Fail direction: pre-cure, SMH is absent from CORE_SYMBOLS and from
desk_symbols() output.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3 import warm  # noqa: E402


class TestSmhWarmUniverse(unittest.TestCase):

    def test_smh_in_core_symbols(self):
        self.assertIn("SMH", warm.CORE_SYMBOLS)

    def test_desk_symbols_serves_smh(self):
        self.assertIn("SMH", warm.desk_symbols(ROOT))

    def test_rejected_route_stays_rejected(self):
        with open(os.path.join(ROOT, "config",
                               "universes.json")) as fh:
            universes = json.load(fh)
        for key in ("basket_41", "momentum_114", "phase_48"):
            self.assertNotIn("SMH", universes.get(key) or [],
                             f"SMH must not enter trading universe "
                             f"{key}; CORE_SYMBOLS is its home")


if __name__ == "__main__":
    unittest.main()
