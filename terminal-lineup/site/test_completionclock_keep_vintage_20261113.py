#!/usr/bin/env python3
"""Regression blocker for COMPLETIONCLOCK-KEEP-VINTAGE-20261113.

Defect (session 2026-11-12 refresh, every resume): the Completion
Clock leg failed with "the deep-reset history does not reproduce
the registered pool day 2026-10-16 (pool 153, matching 31) under
the exact composite: got pool 154, matching 31". The composite's
320-bar universe keep was counted on the panel's FULL current
series (len(closes) inside reset_features), so a panel advance
that carried any name across 320 bars rewrote registered history.
The extra member was FLY: first bar 2025-08-07, 319 bars through
2026-11-11, its 320th bar dated 2026-11-12 itself. At the
register's vintage (written 2026-10-31, panel freshest
2026-10-30) FLY held 311 bars and stood outside the keep.

Cure: the history replay counts the keep at the registered
vintage (HISTORY_KEEP_END = 2026-10-30, bars with a session on or
before that day); per-day features are unchanged and the live leg
still counts the keep on the full current series.

Fail direction: against the pre-cure module the synthetic test
errors (reset_features took no bars_on_record argument) and the
panel test fails on 2026-10-16 (pool 154 against the registered
153). Both pass on the cured code.
"""
import bisect
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh_completionclock as cc


def _washed_out_series(n_bars, eval_idx):
    """A synthetic name that passes every per-day feature at
    eval_idx: flat at 100, a spike high early in the 252 window,
    a fall to 16 for the last 40 sessions on heavy volume."""
    closes, highs, lows, vols = [], [], [], []
    for j in range(n_bars):
        if j < eval_idx - 39:
            c = 100.0
        else:
            c = 16.0
        closes.append(c)
        highs.append(100.0 if j == eval_idx - 200 else c * 1.01)
        lows.append(c * 0.99)
        vols.append(5_000_000.0)
    return closes, highs, lows, vols


class KeepVintageTests(unittest.TestCase):
    def test_keep_counted_at_vintage_not_full_series(self):
        # 325 bars in total today, but only 311 of them on or
        # before the registered vintage: outside the keep for the
        # history replay, inside it for the live form.
        closes, highs, lows, vols = _washed_out_series(325, 300)
        feat_live = cc.reset_features(closes, highs, lows, vols,
                                      300, 0.0)
        self.assertIsNotNone(feat_live)
        feat_hist = cc.reset_features(closes, highs, lows, vols,
                                      300, 0.0, bars_on_record=311)
        self.assertIsNone(feat_hist)
        feat_hist_in = cc.reset_features(closes, highs, lows, vols,
                                         300, 0.0, bars_on_record=320)
        self.assertIsNotNone(feat_hist_in)


@unittest.skipUnless(os.path.exists(cc.PANEL_PATH),
                     "shipped panel not on this disk")
class RegisteredPoolTests(unittest.TestCase):
    REGISTERED = {"2026-06-05": (123, 25), "2026-06-10": (127, 26),
                  "2026-07-29": (61, 12), "2026-10-16": (153, 31)}

    def test_registered_days_reproduce(self):
        panel_raw = json.load(open(cc.PANEL_PATH))
        panel = {s: [(r[0], float(r[1]), float(r[2]), float(r[3]),
                      float(r[4]), float(r[5])) for r in rows]
                 for s, rows in panel_raw.items()}
        closes = {s: [r[4] for r in rows] for s, rows in panel.items()}
        highs = {s: [r[2] for r in rows] for s, rows in panel.items()}
        lows = {s: [r[3] for r in rows] for s, rows in panel.items()}
        vols = {s: [r[5] for r in rows] for s, rows in panel.items()}
        spy_dates = [r[0] for r in panel["SPY"]]
        spy_r10 = {spy_dates[i]: closes["SPY"][i]
                   / closes["SPY"][i - 10] - 1.0
                   for i in range(10, len(spy_dates))}
        keep = {s: bisect.bisect_right([r[0] for r in rows],
                                       cc.HISTORY_KEEP_END)
                for s, rows in panel.items()}
        fearday = json.load(open(cc.FEARDAY_PATH))
        fear_days = [e["date"] for e in
                     fearday["fear_days_in_record"]["days"]]
        got = {}
        for day in fear_days:
            if day not in self.REGISTERED:
                continue
            scored = []
            for sym in panel:
                if sym == "SPY":
                    continue
                idx = next((k for k, r in enumerate(panel[sym])
                            if r[0] == day), None)
                if idx is None:
                    continue
                feat = cc.reset_features(
                    closes[sym], highs[sym], lows[sym], vols[sym],
                    idx, spy_r10.get(day), bars_on_record=keep[sym])
                if feat:
                    scored.append((sym, feat["f7"], feat["f6"]))
            top = cc.composite_top_fifth(scored)
            got[day] = (len(scored), len(top))
        self.assertEqual(got, self.REGISTERED)


if __name__ == "__main__":
    unittest.main()
