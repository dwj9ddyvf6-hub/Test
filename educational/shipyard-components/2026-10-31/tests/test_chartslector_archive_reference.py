from pathlib import Path
import importlib.util
import sys
import types
import unittest

# A test-only no-op decorator keeps the shared indicator's algorithm callable when
# Numba is absent. It is not exported as a runtime fallback and does not test JIT.
NUMBA_STUBBED = importlib.util.find_spec("numba") is None
if NUMBA_STUBBED:
    sys.modules["numba"] = types.SimpleNamespace(njit=lambda **kwargs: (lambda fn: fn))

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHARTSLECTOR = ROOT / "research" / "chartslector"
sys.path.insert(0, str(CHARTSLECTOR / "archive_reference" / "ship" / "sleeve_cl" / "chartslector"))
sys.path.insert(0, str(CHARTSLECTOR / "archive_reference" / "systems"))
sys.path.insert(0, str(CHARTSLECTOR / "archive_reference" / "tests"))
import cl_core
import ranker_feats
import screens
import pine_ref


class ArchiveReferenceTests(unittest.TestCase):
    def test_cl_core_indicator_and_composite_known_answers(self):
        a = np.array([[1, 2, 3, 4]], dtype=np.float32)
        np.testing.assert_allclose(cl_core.sma(a, 2), [[np.nan, 1.5, 2.5, 3.5]], equal_nan=True)
        np.testing.assert_allclose(cl_core.rma(a, 2), [[np.nan, 1.5, 2.25, 3.125]], equal_nan=True)
        self.assertAlmostEqual(float(cl_core.vmr_composite([15.53], [15.53 / 0.863], [85.46], [143.04])[0]), 75.4, delta=0.6)

    def test_pine_reference_rolling_and_lod_examples(self):
        np.testing.assert_allclose(pine_ref.ta_sma([1, 2, 3], 2), [np.nan, 1.5, 2.5], equal_nan=True)
        self.assertEqual(pine_ref.lod_entry(10.5, 10, 2, pct=0.65, frac=0.1), (True, 9.8))
        ups, downs = pine_ref.gaps_counts([2, 2, 3, 2], [1, 2, 2.5, 1.5], [1.5, 2.5, 2.8, 1.6])
        self.assertEqual(len(ups), 4); self.assertEqual(len(downs), 4)

    def test_ranker_feature_constructor_and_explicit_coefficient_contract(self):
        t = 64; symbols = 20
        base = np.arange(t, dtype=np.float32)[None, :] + 20 + np.arange(symbols, dtype=np.float32)[:, None] / 10
        o, c, h, lo, v = base - .1, base, base + .5, base - .5, np.full_like(base, 1_000_000)
        f = ranker_feats.raw(o, h, lo, c, v, need=["ret5", "atrp"])
        self.assertIn("e50ATR", f); self.assertIn("ret5", f)
        coefs = {"Breakout": {"const": 10, "terms": {}}, "Expansion": {"const": 20, "terms": {}}, "Risk": {"const": 30, "terms": {}}}
        scored = ranker_feats.score(f, coefs)
        self.assertAlmostEqual(float(scored["S10"][0, -1]), 18.0, places=5)
        self.assertAlmostEqual(float(scored["Opp"][0, -1]), 18.5, places=5)
        # Strictly-below universe percentile: ties have zero names strictly below.
        self.assertTrue((ranker_feats.upct(np.ones((20, 1), np.float32), np.ones((20, 1), bool)) == 0).all())

    def test_screen_contract_on_synthetic_panel(self):
        t, n = 210, 20
        c = np.tile(np.linspace(10, 20, t, dtype=np.float32), (n, 1)) * (1 + np.arange(n, dtype=np.float32)[:, None] * .01)
        o, h, lo, v = c - .1, c * 1.03, c * .97, np.full_like(c, 800_000)
        class Panel: pass
        p=Panel(); p.O,p.H,p.L,p.C,p.V=o,h,lo,c,v; p.dates=np.arange(t)
        import ind
        p.atrp=ind.atr(h,lo,c)/c
        masks=screens.build(p, np.full_like(c, 1_000_000))
        self.assertIn("breadth_screener", masks)
        self.assertEqual(masks["qullamaggie_nofloat"].shape, c.shape)
        self.assertEqual(masks["base_screen"].dtype, np.dtype(bool))

    def test_research_harnesses_are_inert_text_with_no_machine_paths(self):
        for p in (CHARTSLECTOR / "archive_reference").rglob("*.reference.txt"):
            text=p.read_text()
            self.assertNotIn("/workspace/", text)
            self.assertNotIn("/home/" + "box/", text)
        self.assertTrue((CHARTSLECTOR / "archive_reference" / "index.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
