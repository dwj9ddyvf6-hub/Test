"""FIX-F1-Q07 blockers (2026-11-15, SLEEVE FIX PROGRAM lane F1).

Defects (root cause: the producers DO stamp alt-data; three Q07
consumers could not read the serving form, so their filters failed
closed on every real fire):

1. desk3/q07_engine.py refused every real composer fire before any
   filter ran: specs carry band "ml" while desk-fires-composer-v1
   stamps cap_band "midlarge", and _filters_pass read only flat fire
   fields, blind to fire["tags"] where the composer stamps wiki_low
   (wlow's primary evidence). Cure: band-vocabulary normalization +
   flat-then-tags evidence reads (fail-closed unchanged).

2. desk3/lazarus_q07.py SPECS carried parked=True for four swing-ML
   lanes the roster unparked on 2026-11-14 (UNPARK-REGISTRY-20261114,
   owner's all-sleeves-firing order); the engine flag overrode the
   roster. Cure: parked=False for exactly those four lanes.

3. laz_sleeves/_common.py q07_evaluate indexed tensor_fires as a
   {SYM: fire} dict while the Tensor bundle producer serves a list
   (bundle["fires"], built solely from tensor_swing signals), read
   alt filters only from alt_data (whose producer serves mcap_band
   only, pinned), and computed deep70 at 0.30 * trailing high where
   every other estate reading is 0.70. Cure: list normalization,
   composer-tags fallback for fields the alt row lacks, deep70 0.70.

Fail direction: every entry test below returns [] (or raises, for
the list-shape case) on the pre-cure tree and emits exactly one
entry on the cured tree; the two fail-closed guards return [] on
both. Proven on a preserved pre-cure copy in /tmp (see
research_notes/alpha-hunt-chaos-20261115/pass2/FIX-F1-Q07.md).
"""
import os
import sys
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TODAY = date(2026, 10, 23)


def daily_series(n, close, high=None, last_down=False):
    rows = []
    d = TODAY - timedelta(days=n - 1)
    for i in range(n):
        c = close
        rows.append({"t": (d + timedelta(days=i)).isoformat(),
                     "o": c, "h": high if high is not None else c,
                     "l": c, "c": c, "v": 1000})
    if last_down:
        rows[-1]["c"] = close - 10.0
    return rows


# ------------------------------------------------------------ q07_engine
class TestQ07EngineServingForm(unittest.TestCase):
    SID = "s_q07w_g52_ml_ins2_wlow"  # filters ins2 + wlow, band ml

    def _view(self, fire):
        from importlib import import_module
        mod = import_module(f"adapters3.{self.SID}")
        bars = {"QQQ|1day": daily_series(300, 500.0, last_down=True),
                "ABC|1day": daily_series(300, 40.0)}
        view = {"now": "2026-10-23T15:55:00+00:00", "bars": bars,
                "positions": [], "extra": {"sleeve_fires": [fire]}}
        return mod.evaluate(view, {})

    def _fire(self, **kw):
        f = {"sleeve": self.SID, "symbol": "ABC",
             "signal_date": "2026-10-21", "insider_buys": 3,
             "wiki_views_30d": 100}
        f.update(kw)
        return f

    def test_composer_long_band_vocabulary_enters(self):
        # The real composer's serving form: band "midlarge".
        out = self._view(self._fire(cap_band="midlarge",
                                    band="midlarge"))
        self.assertEqual(len([i for i in out if i.kind == "enter"]), 1)

    def test_wlow_evidence_under_tags_enters(self):
        # wiki evidence ONLY under tags (the composer's form): no
        # flat wiki_views_30d, no flat wiki_low.
        f = self._fire(cap_band="ml")
        del f["wiki_views_30d"]
        f["tags"] = {"wiki_low": True, "insider_buys": 3}
        out = self._view(f)
        self.assertEqual(len([i for i in out if i.kind == "enter"]), 1)

    def test_fail_closed_preserved_without_evidence(self):
        f = self._fire(cap_band="midlarge", insider_buys=0)
        f["tags"] = {"insider_buys": 0, "wiki_low": False}
        self.assertEqual(self._view(f), [])


# ------------------------------------------------------------ lazarus_q07
class TestLazarusQ07Unparked(unittest.TestCase):
    FOUR = ("s_q07w_s52_ml_deep70_wlow", "s_q07w_s52_ml_deep70_vix20_wlow",
            "s_q07w_s78_ml_deep70_wcov", "s_q07w_s78_ml_deep70_mom6_wlow")

    def test_specs_match_roster_unpark(self):
        from desk3.lazarus_q07 import SPECS
        for sid in self.FOUR:
            self.assertFalse(SPECS[sid]["parked"], sid)

    def test_unparked_lane_enters_on_qualifying_fire(self):
        from desk3.lazarus_q07 import evaluate_sleeve
        sid = "s_q07w_s52_ml_deep70_wlow"
        days = [TODAY - timedelta(days=i) for i in range(29, -1, -1)]
        bars = [{"date": d.isoformat(), "c": 10.0} for d in days]
        fire = {"symbol": "TEST", "family": "swing", "band": "midlarge",
                "signal_date": "2026-10-23", "price": 10.0,
                "tags": {"deep70": True, "wiki_low": True}}
        v = {"bars": {"QQQ": [{"date": "2026-10-22", "c": 101.0},
                             {"date": "2026-10-23", "c": 100.0}],
                      "TEST": bars},
             "positions": [], "fires": [fire],
             "extra": {"q07_exp_journal": {"records": []}}}
        out = evaluate_sleeve(sid, v, {"session": "2026-10-23",
                                       "now": "2026-10-23"})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


# ------------------------------------------------------------ laz _common
def _common_view(tensor_fires, alt, fires=None, closes=None):
    closes = closes if closes is not None else \
        [50.0 + i * 0.2 for i in range(140)]  # rising: mom6 > 0
    bars = [{"t": (TODAY - timedelta(days=len(closes) - 1 - i)).isoformat(),
             "o": c, "h": c, "l": c, "c": c, "v": 1000}
            for i, c in enumerate(closes)]
    qqq = [{"t": "2026-10-22", "o": 500.0, "h": 500.0, "l": 500.0,
            "c": 500.0, "v": 1},
           {"t": "2026-10-23", "o": 490.0, "h": 490.0, "l": 490.0,
            "c": 490.0, "v": 1}]
    return {"now": "2026-10-23T15:55:00+00:00",
            "bars": {"ACME|1Day": bars, "QQQ|1Day": qqq},
            "positions": [], "tensor_fires": tensor_fires,
            "alt_data": alt, "fires": fires or [], "vix": 25.0}


class TestCommonServingForm(unittest.TestCase):
    SID = "s_q07w_s52_ml_ins2_mom6_wlow"  # filters ins2 + mom6 + wlow

    def _ev(self, view):
        import importlib
        mod = importlib.import_module(f"laz_sleeves.{self.SID}")
        return mod.evaluate(view, {"sleeve_id": self.SID})

    def test_list_tensor_fires_and_composer_tag_fallback_enters(self):
        # Producer shapes: tensor_fires is a LIST with no family
        # field; alt_data carries mcap_band only; the insider/wiki
        # evidence rides the composer fires tags.
        view = _common_view(
            tensor_fires=[{"symbol": "ACME", "date": "2026-10-22",
                           "confidence": 5}],
            alt={"ACME": {"mcap_band": "midlarge"}},
            fires=[{"symbol": "ACME",
                    "tags": {"insider_buys": 3, "wiki_low": True}}])
        out = self._ev(view)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_fail_closed_preserved_without_any_alt_evidence(self):
        view = _common_view(
            tensor_fires=[{"symbol": "ACME", "date": "2026-10-22",
                           "confidence": 5}],
            alt={"ACME": {"mcap_band": "midlarge"}}, fires=[])
        self.assertEqual(self._ev(view), [])

    def test_deep70_is_70pct_of_high_not_30pct(self):
        import importlib
        sid = "s_q07w_s78_ml_deep70_glow_ins2"
        mod = importlib.import_module(f"laz_sleeves.{sid}")
        closes = [100.0] * 130 + [50.0]  # 50% of high: deep70, not 0.30-deep
        view = _common_view(
            tensor_fires={"ACME": {"family": "swing",
                                   "date": "2026-10-22"}},
            alt={"ACME": {"mcap_band": "midlarge", "insider_buys": 3,
                          "gamma_low": True}},
            closes=closes)
        out = mod.evaluate(view, {"sleeve_id": sid})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


if __name__ == "__main__":
    unittest.main()
