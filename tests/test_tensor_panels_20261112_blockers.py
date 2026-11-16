"""TENSOR PANELS blockers (TENSOR-SERVE-SHAPE cure, 2026-11-12;
TENSOR-FIRE-PATH.md CURE-4).

Diagnosis: the batch1 recovery books (aster_tensor_h1_recovery,
aster_tensor_w1_recovery) read per-symbol native state panels from
view["tensor"]; the served bundle carried only session /
generated_at / sleeves / fires, none of which parse as panels, so
both books evaluated over an empty panel map every cycle.
Cure pinned here: desk3/tensor_native builds 1h native state
panels (the pinned engine's own seven vote channels per bar, plus
ATR14 / OBV-slope / dollar-volume producer math over the canonical
1h series) and desk3/tensor_warm serves them in the bundle under
symbol keys as {SYM: {"frame": "1h", "features": [rows]}} — the
shape aster_batch1._tensor_panels reads. Frame discipline is the
consumer's own: the 1h panels are accepted by the hourly book and
refused by the weekly book. (The weekly book's own frame cannot
ride the same bundle — the consumer reads ONE symbol-keyed panel
map from view["tensor"], one frame per symbol — and its entry
gate additionally requires bar_index + 1 >= 234 weekly bars
against ~69 weeks of history on this box; both walls are named in
BUGLOG_2026-11-12, TENSOR-SERVE-SHAPE-20261112.)
End-to-end pin: a repair pattern in the served panel shape forms
a real entry intent through the hourly book's own evaluate.
"""
import importlib
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desk3 import tensor_native  # noqa: E402
import core.data  # noqa: E402
import test_tensor_native_features_20261112_blockers as tnf  # noqa: E402


def ev(sid, view, state_dir):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, {"sleeve_id": sid, "state_dir": state_dir,
               "cycle_id": "fx"})


class TestPanels(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def _products(self, tmp):
        daily = tnf.daily_series()
        with mock.patch.object(core.data, "tensor_bars", tnf.fake_1h):
            return tensor_native.build_native_products(
                tmp, ["AAA"], {"AAA": daily},
                datetime(2026, 11, 12, tzinfo=timezone.utc),
                state_runner=tnf.stub_runner)

    def test_panel_shape_and_frame_discipline(self):
        from desk3 import aster_batch1
        tmp = self._root()
        products = self._products(tmp)
        rows = products["panels"]["AAA"]
        self.assertGreaterEqual(len(rows), 4)
        last = rows[-1]
        self.assertEqual(last["frame"], "1h")
        self.assertEqual(last["bar_index"], 299)
        self.assertEqual(last["total_votes"], 7)
        self.assertEqual(set(last["votes"]), set(tensor_native.VOTE_NAMES))
        view = {"tensor": {"AAA": {"frame": "1h", "features": rows}}}
        panels_1h = aster_batch1._tensor_panels(view, "1h")
        self.assertIn("AAA", panels_1h)
        self.assertEqual(aster_batch1._tensor_panels(view, "1wk"), {})

    def test_recovery_entry_end_to_end(self):
        tmp = self._root()
        products = self._products(tmp)
        view = {"now": "2026-11-12T14:00:00+00:00",
                "tensor": {"AAA": {"frame": "1h",
                                   "features": products["panels"]["AAA"]}},
                "bars": {}, "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        out = ev("aster_tensor_h1_recovery", view, self._root())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "AAA")
        # budget min(0.10*10000, 0.01*5.0e6, 10000) = 1000
        # -> floor(1000 / (50 * 1.001)) = 19 shares
        self.assertEqual(out[0]["qty"], 19)
        # The weekly book refuses the hourly frame (its own gate).
        self.assertEqual(ev("aster_tensor_w1_recovery", view,
                            self._root()), [])


if __name__ == "__main__":
    unittest.main()
