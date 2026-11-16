"""TENSOR NATIVE FEATURES blockers (TENSOR-SERVE-SHAPE cure,
2026-11-12; TENSOR-FIRE-PATH.md CURE-3 feature half).

Diagnosis: the CURE-3 envelope layer (2026-11-11) served each fire's
own values under the names the variant families read, but the
FEATURE fields (markers, native_close, depth60, ret60, vol20, dv20,
atr_ratio) were deliberately not derived: they need a feature
producer with a verified canonical mapping, never guessed fields.
Cure pinned here (desk3/tensor_native.py, wired into
desk3/tensor_warm.build_bundle): weekly bars by the archive's
whole-week exact-membership rule, features() ported verbatim from
source/backend/r19_tensor.py, markers/votes from the pinned v698
engine's own state via desk3/tensor_state_runner.mjs, a prepared
analysis record whose analysis_sha256 binds its contents, an
enrollment census that assesses every universe symbol (ready /
verified_ineligible / blocked, never silent), and fires stamped
with their symbol's native fields. A symbol with no buildable
record keeps the envelope values only — the feature gates fail
closed downstream, exactly as before the cure.
"""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3 import tensor_native  # noqa: E402
import core.data  # noqa: E402

VOTE_NAMES = tensor_native.VOTE_NAMES


def daily_series():
    """Two full years of deterministic daily bars on real sessions."""
    cal = tensor_native.desk_calendar(date(2024, 1, 2), date(2025, 12, 31))
    rows = []
    prev = None
    for i, s in enumerate(cal):
        c = 9.0 + 1.5 * math.sin(i / 7.0) + i * 0.01
        o = prev if prev is not None else c
        rows.append({"t": f"{s['session']}T05:00:00Z", "o": o,
                     "h": max(o, c) * 1.01, "l": min(o, c) * 0.99,
                     "c": c, "v": 2_500_000})
        prev = c
    return rows


def expected_features(weekly, daily):
    """The canonical formulas, written independently from the
    archive spec (r19_tensor.features) for cross-checking."""
    import statistics
    c = [x["c"] for x in weekly]
    rets = [math.log(c[i] / c[i - 1]) for i in range(len(c) - 20, len(c))]
    trs = []
    for i, x in enumerate(weekly):
        pc = weekly[i - 1]["c"] if i else x["c"]
        trs.append(max(x["h"] - x["l"], abs(x["h"] - pc), abs(x["l"] - pc)))

    def rma(n):
        v = trs[0]
        for x in trs[1:]:
            v = v + (x - v) / n
        return v

    return {"native_close": c[-1],
            "depth60": (1 - min(x["l"] for x in weekly[-60:])
                        / max(x["h"] for x in weekly[-60:])) * 100,
            "ret60": (daily[-1]["c"] / daily[-61]["c"] - 1) * 100,
            "vol20": statistics.stdev(rets),
            "dv20": sum(x["c"] * x["v"] for x in daily[-21:-1]) / 20,
            "atr_ratio": rma(20) / rma(60)}


class TestWeeklyAndFeatures(unittest.TestCase):
    def test_weekly_whole_weeks_exact_membership(self):
        cal = tensor_native.desk_calendar(date(2025, 1, 1),
                                          date(2025, 3, 31))
        daily = [{"t": f"{s['session']}T05:00:00Z", "o": 10.0, "h": 11.0,
                  "l": 9.0, "c": 10.5, "v": 1000} for s in cal]
        # Remove one session in the week of 2025-01-13: that whole
        # week must drop out (exact membership), neighbours stay.
        victim = "2025-01-14"
        daily = [b for b in daily if not b["t"].startswith(victim)]
        weekly = tensor_native.weekly_from_daily(daily, cal)
        mondays = [w["t"][:10] for w in weekly]
        self.assertNotIn("2025-01-13", mondays)
        self.assertIn("2025-01-06", mondays)
        self.assertIn("2025-01-20", mondays)
        # The final calendar week (Mon 2025-03-31) can never be a
        # whole week in a calendar ending 2025-03-31.
        self.assertNotIn("2025-03-31", mondays)
        w = weekly[0]
        self.assertEqual(w["c"], 10.5)
        self.assertEqual(w["h"], 11.0)
        self.assertEqual(w["l"], 9.0)
        self.assertTrue(w["end"].startswith("2025-01-03"))

    def test_features_match_canonical_formulas(self):
        daily = daily_series()
        cal = tensor_native.desk_calendar(date(2024, 1, 1),
                                          date(2026, 1, 14))
        weekly = tensor_native.weekly_from_daily(daily, cal)
        self.assertGreaterEqual(len(weekly), 60)
        got = tensor_native.features(weekly, daily)
        exp = expected_features(weekly, daily)
        for k, v in exp.items():
            self.assertAlmostEqual(got[k], v, places=9, msg=k)

    def test_features_warmup_raises(self):
        with self.assertRaises(ValueError):
            tensor_native.features([], daily_series())


SIGNAL = {"symbol": "AAA", "decision": "TRADE", "confidence": 0.9,
          "phenotype": "p", "regime": "r", "bar_date": "2025-12-30",
          "t": 1767225600, "bull_votes": 5, "bear_votes": 2,
          "entry": 12.5, "stop": 12.0, "target": 14.0,
          "latest_diag": {}, "extended": {}}

REPAIR = [[-1, -1, -1, -1, 1, -1, -1], [-1, -1, 1, -1, 1, -1, -1],
          [1, -1, 1, -1, 1, -1, -1], [1, 1, 1, -1, 1, -1, -1]]


def stub_runner(jobs):
    out = {}
    for j in jobs:
        n = len(j["bars"])
        if j["interval"] == "1wk":
            last = {"index": n - 1, "timestamp": 0,
                    "barFinality": "closed", "close": j["bars"][-1]["c"],
                    "volume": j["bars"][-1]["v"], "rvol": 1.5,
                    "primaryMarkers": ["buy-cyan"],
                    "primaryMarker": "buy-cyan", "bullishVotes": 5,
                    "bearishVotes": 2, "totalVotes": 7,
                    "votes": {name: 1 for name in VOTE_NAMES},
                    "obv": 1000.0, "enrichmentIds": ["consensus-buy"]}
            out[j["key"]] = {"ok": True, "barsIn": n, "barsOut": n,
                             "lastClosedIndex": n - 1, "rows": [last],
                             "last": last}
        else:
            rows = []
            for i in range(max(0, n - 64), n):
                rows.append({
                    "index": i, "timestamp": 0, "barFinality": "closed",
                    "close": 50.0, "volume": 100000, "rvol": 1.0,
                    "primaryMarkers": [], "primaryMarker": None,
                    "bullishVotes": 0, "bearishVotes": 7, "totalVotes": 7,
                    "votes": {name: -1 for name in VOTE_NAMES},
                    "obv": float(i * 1000)})
            for row, pat in zip(rows[-4:], REPAIR):
                row["votes"] = dict(zip(VOTE_NAMES, pat))
            out[j["key"]] = {"ok": True, "barsIn": n, "barsOut": n,
                             "lastClosedIndex": n - 1, "rows": rows,
                             "last": rows[-1]}
    return out, "stub-engine"


def fake_1h(symbol):
    base = 1760000000
    return [{"t": base + 3600 * i, "o": 50.0, "h": 50.6, "l": 49.4,
             "c": 50.0, "v": 100000} for i in range(300)]


class FakeProducer:
    def extra_for(self, sleeve_id, ctx):
        memo = {"session": ctx.session, "rows": {"AAA": {"row": SIGNAL}}}
        path = os.path.join(self._root, "state",
                            "tensor_signals_memo.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(memo, fh)
        if sleeve_id == "tensor_swing":
            return {"tensor_signals": [dict(SIGNAL)], "tensor_exit": {}}
        return {"tensor_signals": [], "qqq_day_return": 0.0,
                "day_returns": {}, "nyse_holidays": []}


class TestBundleNativePass(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_fires_stamped_from_analysis_record(self):
        from desk3.tensor_warm import build_bundle
        tmp = self._root()
        fp = FakeProducer()
        fp._root = tmp
        daily = daily_series()
        with mock.patch.object(tensor_native, "run_state_jobs",
                               stub_runner), \
                mock.patch.object(core.data, "tensor_bars", fake_1h):
            payload = build_bundle(
                tmp, session="2026-11-12", producer=fp,
                fetch_daily=lambda syms: {"AAA": daily})
        rec = payload["tensor_analysis"]["AAA"]
        # The record's hash binds its contents (archive discipline).
        body = {k: v for k, v in rec.items() if k != "analysis_sha256"}
        self.assertEqual(rec["analysis_sha256"],
                         tensor_native.digest(body))
        self.assertEqual(payload["tensor_census"]["AAA"]["status"],
                         "ready")
        # Receipt timing discipline: native products are stamped at
        # the bundle's generated_at (its decision time), so the
        # serve-side census assessment can open in the build cycle.
        self.assertEqual(rec["prepared_at"], payload["generated_at"])
        self.assertEqual(payload["tensor_census"]["AAA"]["received_at"],
                         payload["generated_at"])
        fire = payload["fires"][0]
        self.assertEqual(fire["markers"], ["buy-cyan"])
        self.assertEqual(fire["primaryMarkers"], ["buy-cyan"])
        self.assertEqual(fire["signal"], "buy-cyan")
        for k in ("native_close", "depth60", "ret60", "vol20", "dv20",
                  "atr_ratio", "adv_usd"):
            self.assertEqual(fire[k], rec["features"][
                "dv20" if k == "adv_usd" else k], k)
        # The native signal_end replaces the envelope's bar_date one:
        # the variant books key delay/reserve timing on the weekly
        # signal, not on the swing bar.
        self.assertEqual(fire["signal_end"], rec["signal_end"])
        self.assertEqual(fire["date"], rec["signal_end"][:10])
        # Envelope facts survive untouched.
        self.assertEqual(fire["price"], fire["entry"])
        self.assertIn("fired_at", fire)
        # Panels ride the bundle under the symbol key (CURE-4 shape).
        panel = payload["AAA"]
        self.assertEqual(panel["frame"], "1h")
        self.assertGreaterEqual(len(panel["features"]), 4)
        self.assertEqual(panel["features"][-1]["bar_index"], 299)

    def test_no_data_keeps_envelope_only(self):
        from desk3.tensor_warm import build_bundle
        tmp = self._root()
        fp = FakeProducer()
        fp._root = tmp
        payload = build_bundle(tmp, session="2026-11-12", producer=fp)
        fire = payload["fires"][0]
        self.assertEqual(fire["price"], fire["entry"])  # envelope
        self.assertNotIn("markers", fire)               # nothing faked
        self.assertNotIn("tensor_analysis", payload)
        # The skip is named, never silent.
        self.assertEqual(
            payload["tensor_census"]["AAA"]["reason"], "no_daily_bars")


if __name__ == "__main__":
    unittest.main()
