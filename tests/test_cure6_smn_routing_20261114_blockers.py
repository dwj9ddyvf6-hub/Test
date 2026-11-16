"""CURE-6 ROUTING blockers (Lane C, 2026-11-14).

The four s_mn Tensor fire consumers (desk3/lazarus_midna.py SPECS:
s_mn_d_green_band, s_mn_w_cyan_breadth, s_mn_w_cyan_vix,
s_mn_w_green_smh) route on {sleeve_id, family, timeframe, date,
price}; the served bundle fires carried none of family/timeframe, so
every fire died at routing. Cure at the desk-side producer layer
(desk3/tensor_native.apply_native_to_fire — the pinned engine and
its pins untouched): a fire whose symbol has a native analysis
record gains family/timeframe derived ONLY from its own variant
identity — the weekly engine's primaryMarkers (buy-cyan -> cyan,
buy-green -> green) and the weekly timeframe of that analysis
(1W). sleeve_id is deliberately NOT stamped: the consumers treat an
absent sleeve_id as broadcast (considered by every sleeve, then
gated by family/timeframe), and the (family, timeframe) variant
maps to a SET of sleeves (cyan/1W = breadth + vix sleeves), so any
single stamped sleeve_id would starve its sibling — addressed
delivery stays the upstream Midna product's property, named in
BUGLOG_2026-11-14 CURE-6.
"""
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FIRE = {"symbol": "NBIS", "decision": "TRADE", "confidence": 8,
        "phenotype": "TRANSITION", "regime": "bullish",
        "bar_date": "2026-11-13", "t": 1794601800,
        "entry": 50.0, "stop": 49.0, "target": 60.0,
        "price": 50.0, "date": "2026-11-13"}


def _record(markers):
    return {"features": {}, "signal_end": "2026-11-13",
            "rep_g": {"last": {"primaryMarkers": list(markers)}}}


def _bars(sym, closes):
    return {f"{sym}|1Day": [{"t": f"2026-11-{d:02d}T05:00:00Z",
                             "o": c, "h": c, "l": c, "c": c, "v": 1000}
                            for d, c in enumerate(closes, start=1)]}


class TestRoutingStamps(unittest.TestCase):
    def test_cyan_marker_stamps_cyan_1w(self):
        from desk3.tensor_native import apply_native_to_fire
        out = apply_native_to_fire(dict(FIRE), _record(["buy-cyan"]))
        self.assertEqual(out["family"], "cyan")
        self.assertEqual(out["timeframe"], "1W")
        self.assertNotIn("sleeve_id", out)

    def test_green_marker_stamps_green_1w(self):
        from desk3.tensor_native import apply_native_to_fire
        out = apply_native_to_fire(dict(FIRE), _record(["buy-green"]))
        self.assertEqual(out["family"], "green")
        self.assertEqual(out["timeframe"], "1W")

    def test_sell_marker_and_missing_record_stamp_nothing(self):
        from desk3.tensor_native import apply_native_to_fire
        out = apply_native_to_fire(dict(FIRE), _record(["sell-red"]))
        self.assertNotIn("family", out)
        self.assertNotIn("timeframe", out)
        bare = apply_native_to_fire(dict(FIRE), None)
        self.assertNotIn("family", bare)


class TestEndToEndRouting(unittest.TestCase):
    def _view(self, fire):
        bars = {}
        bars.update(_bars("NBIS", [50.0] * 25))
        bars.update(_bars("SMH", [300.0] * 25))
        return {"tensor": {"fires": [fire]}, "bars": bars,
                "positions": [],
                "extra": {"breadth_pct": 0.60, "vix": 18.0}}

    def _ctx(self):
        return {"session": "2026-11-13",
                "now": datetime(2026, 11, 13, 15, 0,
                                tzinfo=timezone.utc)}

    def test_unstamped_fire_routes_nowhere(self):
        from desk3 import lazarus_midna
        view = self._view(dict(FIRE))
        for sid in lazarus_midna.SPECS:
            # GOING-LIVE-VARIATIONS-20261115: s_mn_hourly_1w_varn1 is
            # the CONV-37 night-1 variation of s_mn_hourly_1w and
            # inherits the parent's routing form, so it carries the
            # parent's exemption here exactly as the parent does.
            if sid in ("s_mn_hourly_1w", "s_mn_hourly_1w_varn1"):
                continue
            self.assertEqual(
                lazarus_midna.evaluate(sid, view, self._ctx()), [],
                f"{sid} must not route an unstamped fire")

    def test_cyan_1w_fire_enters_breadth_and_vix_sleeves(self):
        from desk3 import lazarus_midna
        from desk3.tensor_native import apply_native_to_fire
        fire = apply_native_to_fire(dict(FIRE), _record(["buy-cyan"]))
        view = self._view(fire)
        for sid in ("s_mn_w_cyan_breadth", "s_mn_w_cyan_vix"):
            out = lazarus_midna.evaluate(sid, view, self._ctx())
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["kind"], "entry")
            self.assertEqual(out[0]["symbol"], "NBIS")
        # family mismatch: the green sleeves refuse a cyan fire
        self.assertEqual(lazarus_midna.evaluate(
            "s_mn_w_green_smh", view, self._ctx()), [])

    def test_green_1w_fire_enters_smh_sleeve(self):
        from desk3 import lazarus_midna
        from desk3.tensor_native import apply_native_to_fire
        fire = apply_native_to_fire(dict(FIRE), _record(["buy-green"]))
        view = self._view(fire)
        out = lazarus_midna.evaluate("s_mn_w_green_smh", view, self._ctx())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        # timeframe mismatch: the 1D green sleeve refuses a 1W fire
        self.assertEqual(lazarus_midna.evaluate(
            "s_mn_d_green_band", view, self._ctx()), [])


if __name__ == "__main__":
    unittest.main()
