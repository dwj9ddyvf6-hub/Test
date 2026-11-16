"""ADA-WINDOW-20261116 blockers (desk full audit 2026-11-16, Phase E1).

ENH-ABS-WINDOW-20261024 cured five ADA sleeves in aster_sleeves._common
by extending the archive 300s entry window to one full 3600s cadence
(WINDOW_SIDS). Six sibling ADA sleeves at the same 3600s cadence were
never added, so their designed signals stayed executable only ~8% of
the time (fixture-proven in Phase E1: entry at lag 120s, NO entry at
lag 1800s/3500s on identical bars). This blocker pins the mirror cure:
the same five crypto sleeves through evaluate_crypto via WINDOW_SIDS,
and aster_pub_rsi2_ada through its own evaluate_rsi2 window, same
principle (window = one cadence, switch entry_window_cadence default
ON, OFF = exact archive 300s rule, paired shadow record on late
entries). No signal, threshold, sizing or stop changes.
"""
import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
UTC = timezone.utc

SIX = ("aster_abs_nonneg_ada_vol1pct", "aster_breakout_ada_fullcash",
       "aster_breakout_ada_vol1pct", "aster_squeeze_ada_fullcash",
       "aster_abs_neg_ada_vol1pct_varsg", "aster_pub_rsi2_ada")
FIVE_CURED = ("aster_abs_base_ada_fullcash", "aster_abs_base_ada_vol1pct",
              "aster_abs_neg_ada_fullcash", "aster_abs_neg_ada_vol1pct",
              "aster_abs_nonneg_ada_fullcash")


def iso(d):
    return d.isoformat().replace("+00:00", "Z")


def _abs_bars(n=310):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(n):
        bars.append({"t": iso(start + timedelta(hours=4 * i)),
                     "o": 1.0, "h": 1.01, "l": 0.99, "c": 1.0,
                     "v": 1000.0})
    bars[n - 3].update({"o": 1.0, "h": 1.0, "l": 0.90, "c": 0.92,
                        "v": 100000.0})
    bars[n - 2].update({"o": 0.93, "h": 0.99, "l": 0.92, "c": 0.98,
                        "v": 5000.0})
    return bars


def _breakout_bars(n=60):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(n):
        bars.append({"t": iso(start + timedelta(hours=4 * i)),
                     "o": 1.0, "h": 1.01, "l": 0.99, "c": 1.0,
                     "v": 1000.0})
    bars[n - 2].update({"o": 1.0, "h": 1.06, "l": 0.99, "c": 1.05,
                        "v": 5000.0})
    bars[n - 1].update({"o": 1.05, "h": 1.07, "l": 1.04, "c": 1.06,
                        "v": 5000.0})
    return bars


def _view4(bars, lag_s, funding=None):
    entry_close = datetime.fromisoformat(
        bars[-1]["t"].replace("Z", "+00:00")) + timedelta(hours=4)
    view = {"now": iso(entry_close + timedelta(seconds=lag_s)),
            "bars": {"ADAUSDT|4Hour": bars}, "positions": [],
            "slice": {"cash_usd": 10000.0}}
    if funding is not None:
        view["funding"] = {"ADAUSDT": {"rate": funding}}
    return view


def _crypto(sid, lag_s, ctx=None):
    import importlib
    mod = importlib.import_module(f"aster_sleeves.{sid}")
    if sid in ("aster_abs_nonneg_ada_vol1pct",
               "aster_abs_neg_ada_vol1pct_varsg"):
        # varsg carries POSITIVE funding on purpose: its registered
        # SIGN_GATE_DROP form must still fire (parent sign leg intact
        # elsewhere is pinned by the batch-1 / gatecure suites).
        return mod.evaluate(_view4(_abs_bars(), lag_s, 0.001), ctx or {})
    if sid == "aster_squeeze_ada_fullcash":
        return mod.evaluate(_view4(_breakout_bars(), lag_s, -0.001),
                            ctx or {})
    return mod.evaluate(_view4(_breakout_bars(), lag_s), ctx or {})


CRYPTO_FIVE = SIX[:5]
OFF = {"enhance": {"entry_window_cadence": False}}


class AdaWindowCrypto(unittest.TestCase):
    def test_enter_late_within_one_cadence(self):
        for sid in CRYPTO_FIVE:
            for lag in (1800, 3500):
                with self.subTest(sid=sid, lag=lag):
                    out = _crypto(sid, lag)
                    self.assertEqual(len(out), 1)
                    rec = out[0]["enhance_exp"]["records"][0]
                    self.assertEqual(rec["exp_id"],
                                     "ENH-ABS-WINDOW-20261024")
                    self.assertEqual(
                        rec["control"], "no_entry_outside_300s_window")
                    self.assertEqual(rec["lag_s"], float(lag))

    def test_beyond_one_cadence_still_refused(self):
        for sid in CRYPTO_FIVE:
            with self.subTest(sid=sid):
                self.assertEqual(_crypto(sid, 3700), [])

    def test_off_restores_300s_window_exactly(self):
        for sid in CRYPTO_FIVE:
            with self.subTest(sid=sid):
                self.assertEqual(_crypto(sid, 1800, ctx=OFF), [])
                self.assertEqual(len(_crypto(sid, 120, ctx=OFF)), 1)

    def test_in_window_entry_has_no_shadow_record(self):
        for sid in CRYPTO_FIVE:
            with self.subTest(sid=sid):
                out = _crypto(sid, 120)
                self.assertEqual(len(out), 1)
                self.assertNotIn("enhance_exp", out[0])


def _rsi2_bars(n=300):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    closes, px = [], 1.0
    for _ in range(n - 5):
        px *= 1.003
        closes.append(px)
    for _ in range(5):
        px *= 0.97
        closes.append(px)
    bars, prev = [], 1.0
    for i, c in enumerate(closes):
        bars.append({"t": iso(start + timedelta(hours=i)), "o": prev,
                     "h": max(prev, c) * 1.001,
                     "l": min(prev, c) * 0.999, "c": c, "v": 1000.0})
        prev = c
    return bars


def _rsi2(lag_s, ctx=None):
    from aster_sleeves.aster_pub_rsi2_ada import evaluate
    bars = _rsi2_bars()
    last_close = datetime.fromisoformat(
        bars[-1]["t"].replace("Z", "+00:00")) + timedelta(hours=1)
    view = {"now": iso(last_close + timedelta(seconds=lag_s)),
            "bars": {"ADAUSDT|1Hour": bars}, "positions": [],
            "slice": {"cash_usd": 10000.0}}
    return evaluate(view, ctx or {})


class AdaWindowRsi2(unittest.TestCase):
    def test_enter_late_within_one_cadence(self):
        for lag in (1800, 3500):
            with self.subTest(lag=lag):
                out = _rsi2(lag)
                self.assertEqual(len(out), 1)
                rec = out[0]["enhance_exp"]["records"][0]
                self.assertEqual(rec["exp_id"], "ENH-ABS-WINDOW-20261024")
                self.assertEqual(rec["control"],
                                 "no_entry_outside_300s_window")
                self.assertEqual(rec["lag_s"], float(lag))

    def test_beyond_one_cadence_still_refused(self):
        self.assertEqual(_rsi2(3700), [])

    def test_off_restores_300s_window_exactly(self):
        self.assertEqual(_rsi2(1800, ctx=OFF), [])
        self.assertEqual(len(_rsi2(120, ctx=OFF)), 1)

    def test_in_window_entry_has_no_shadow_record(self):
        out = _rsi2(120)
        self.assertEqual(len(out), 1)
        self.assertNotIn("enhance_exp", out[0])


class AdaWindowRoster(unittest.TestCase):
    def test_window_roster_is_exactly_the_eleven(self):
        from aster_sleeves._common import WINDOW_SIDS
        self.assertEqual(set(WINDOW_SIDS), set(FIVE_CURED) | set(SIX))


if __name__ == "__main__":
    unittest.main()
