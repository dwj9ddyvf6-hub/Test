"""F4-CRYPTO-BARKEY-20261114 blockers.

Lane D's fixture drives (FIXTURE-DRIVES-2-2026-11-14, family F4)
found 39 armed Aster crypto sleeves resolving 0 bars: their engines
request archive keys (ADAUSDT|4Hour, LINKUSDT|4Hour, ADAUSDT|1Hour)
while the desk's warm layer serves the same underlyings only as
Alpaca spot keys (LINK/USD|4Hour, ADA/USD|1Hour). The cure is
engine-side key normalization (desk3/crypto_bars.py): exact archive
keys keep precedence, then the served BASE/USD spot form, then for
4Hour a deterministic resample of the served BASE/USD 1Hour tape.
ENJ has no served spot equivalent and must stay unresolved.
[Amended CLEAR-THE-BOARD-20261114: the ENJ premise was superseded
by the owner's fix-the-blocked order — the KrakenProducer now
serves the real Kraken spot tape as ENJ/USD|4Hour. The ENJ
assertions below pin the surviving invariant on a premise-filtered
view: absent a served spot series, ENJ resolves nothing.]
"""
import glob
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _snapshot_view():
    snaps = sorted(glob.glob(os.path.join(ROOT, "state", "snapshots",
                                          "*.json")))
    assert snaps, "no retained snapshot"
    doc = None
    for path in snaps:  # newest by the snapshot's own asof, not name
        with open(path) as fh:
            cand = json.load(fh)
        if doc is None or str(cand.get("asof")) > str(doc.get("asof")):
            doc = cand
    data = doc["data"]
    keep = {k: v for k, v in (data.get("bars") or {}).items()
            if any(s in k for s in ("ADA", "LINK", "ENJ", "PF_"))}
    return {"now": data.get("now") or data.get("now_iso"),
            "bars": keep, "positions": [],
            "funding": data.get("funding") or {},
            "slice": {"cash_usd": 10000.0}}


class TestF4ResolutionOnLiveSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.view = _snapshot_view()
        cls.bars = cls.view["bars"]

    def test_snapshot_premise(self):
        # The mismatch itself: no USDT bar key is served, the /USD
        # spot forms are.
        self.assertFalse(any("USDT" in k for k in self.bars))
        self.assertGreaterEqual(len(self.bars["LINK/USD|4Hour"]), 500)
        self.assertGreaterEqual(len(self.bars["ADA/USD|1Hour"]), 700)

    def test_common_ada_4hour_and_1hour(self):
        from aster_sleeves import _common
        b4 = _common._bars(self.view, "4Hour")
        self.assertGreaterEqual(len(b4), 100)
        self.assertEqual(len(_common._bars(self.view, "1Hour")),
                         len(self.bars["ADA/USD|1Hour"]))

    def test_b11_b12_link(self):
        from desk3 import aster_b11_crypto, aster_b12_crypto
        n = len(self.bars["LINK/USD|4Hour"])
        self.assertEqual(len(aster_b11_crypto._bars(self.view,
                                                    "LINKUSDT")), n)
        self.assertEqual(len(aster_b12_crypto._bars(self.view,
                                                    "LINKUSDT")), n)

    def _enj_premise_view(self):
        # AMENDED CLEAR-THE-BOARD-20261114 (pin moved by a ruled
        # change, FEED80-GATE-PINS precedent): the F4 ENJ assertions
        # tested the premise "no ENJ spot series is served". The
        # owner's fix-the-blocked order superseded that premise —
        # the KrakenProducer now serves the real Kraken spot tape as
        # ENJ/USD|4Hour (tests/test_clear_the_board_20261114_
        # blockers.py pins the new behavior). What must hold at the
        # same strength in BOTH worlds, and what these assertions now
        # pin: with no ENJ/USD spot series in the view, ENJ resolves
        # nothing — resolution never fabricates and never falls back
        # to a perp series.
        bars = {k: v for k, v in self.bars.items()
                if not k.startswith("ENJ/USD")}
        return {**self.view, "bars": bars}

    def test_aster_crypto_ada_and_enj(self):
        from desk3 import aster_crypto
        self.assertGreaterEqual(
            len(aster_crypto._bars(self.view, "ADAUSDT")), 100)
        # ENJ on the no-spot-series premise: stays bar-blind by name.
        self.assertEqual(
            aster_crypto._bars(self._enj_premise_view(), "ENJUSDT"), [])

    def test_batch13_link(self):
        from desk3 import aster_batch13
        self.assertEqual(len(aster_batch13._bars(
            self.view, "LINKUSDT")), len(self.bars["LINK/USD|4Hour"]))

    def test_batch1_link_and_enj(self):
        from desk3 import aster_batch1
        self.assertEqual(len(aster_batch1._bars(
            self.view, "LINKUSDT", ("4Hour", "4H"))),
            len(self.bars["LINK/USD|4Hour"]))
        self.assertEqual(aster_batch1._bars(
            self._enj_premise_view(), "ENJUSDT", ("4Hour", "4H")), [])

    def test_b4_spot_link_and_enj(self):
        from desk3 import aster_b4
        self.assertEqual(len(aster_b4._spot_bars(
            self.view, "LINKUSDT")), len(self.bars["LINK/USD|4Hour"]))
        self.assertEqual(
            aster_b4._spot_bars(self._enj_premise_view(), "ENJUSDT"), [])


class TestF4ResampleIntegrity(unittest.TestCase):
    def test_resample_is_exact_aggregation_of_served_1hour(self):
        from desk3.crypto_bars import resample_1h_to_4h
        view = _snapshot_view()
        hourly = sorted(view["bars"]["ADA/USD|1Hour"],
                        key=lambda r: str(r["t"]))
        out = resample_1h_to_4h(hourly)
        # Hourly bars from a 00:00Z start: one output per complete
        # 4h bucket; the trailing partial bucket is dropped.
        self.assertEqual(len(out), len(hourly) // 4)
        first = out[0]
        src = hourly[:4]
        self.assertEqual(first["o"], src[0]["o"])
        self.assertEqual(first["c"], src[-1]["c"])
        self.assertEqual(first["h"], max(r["h"] for r in src))
        self.assertEqual(first["l"], min(r["l"] for r in src))
        self.assertAlmostEqual(first["v"],
                               sum(r["v"] for r in src), places=6)
        # Prices track the desk's Kraken-perp 4h series on the same
        # stamps to within a normal spot/perp basis (sanity, not a
        # source: the resample is built only from the spot tape).
        pf = {str(r["t"])[:13]: r for r in view["bars"]["PF_ADAUSD|4Hour"]}
        checked = 0
        for r in out:
            p = pf.get(str(r["t"])[:13])
            if p:
                self.assertLess(abs(r["c"] - p["c"]) / p["c"], 0.02)
                checked += 1
        self.assertGreater(checked, 150)


class TestF4ExactKeyPrecedence(unittest.TestCase):
    def test_archive_key_still_wins_when_present(self):
        from desk3 import aster_b11_crypto
        marker = [{"t": "2026-01-01T00:00:00Z", "o": 1, "h": 1,
                   "l": 1, "c": 1, "v": 1}]
        view = {"bars": {"LINKUSDT|4Hour": marker,
                         "LINK/USD|4Hour": [{"t": "x", "o": 2, "h": 2,
                                             "l": 2, "c": 2, "v": 2}]}}
        self.assertEqual(aster_b11_crypto._bars(view, "LINKUSDT"),
                         marker)

    def test_non_usdt_symbols_untouched(self):
        from desk3 import aster_batch1
        rows = [{"t": "2026-01-01", "o": 1, "h": 1, "l": 1, "c": 1,
                 "v": 1}]
        view = {"bars": {"SPY|1Day": rows}}
        self.assertEqual(aster_batch1._bars(view, "SPY", ("1Day",)),
                         rows)


if __name__ == "__main__":
    unittest.main()
