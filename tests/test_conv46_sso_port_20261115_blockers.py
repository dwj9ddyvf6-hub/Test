"""Regression blockers: SSO-PORT-CONV46-20261115 (2026-11-15).

Defect class: CONV-46 (the SSO Opus TIME_25-removal variation)
could not be rostered because no SSO parent existed on any live
surface: TIME_25 occurred only in the 2026-11-03 research engines
(research_notes/trendspider-sso-opus-test-20261103), so there was
no installed form to vary beside, and the register row's premise
that an installed form's forward record already runs did not
survive verification (CONVERSION-BLOCKED-20261115).

Cure (this landing): desk3/sso_opus.py, a line-faithful stdlib
port of the research baseline (harness run_sim, trail_from=
"close"), rostered as sso_opus; the TIME_25-removal variation
rostered beside it as sso_opus_notime25 under GUTTING AS
VARIATION (same engine, drop_time25=True, own id, own falsifier;
the parent is never edited into the variation). Fidelity was
proven BEFORE rostering by pass2/sso_fidelity_check.py: the
original harness reproduces its own ledgers exactly, and the
port reproduces both ledgers trade-for-trade (265/265 primary at
cost 0, 282/282 at cost 5bp, 0 divergences at 1e-9) plus the
harness's synthetic known-answer series (4/4). This blocker
carries the synthetic test and the rule pins inside the gate so
the form cannot silently drift afterward.

Modules covered by name: desk3/sso_opus.py,
adapters3/sso_opus.py, adapters3/sso_opus_notime25.py,
desk3/producers_g4.py (the bars:SSO:15Min registry key).

Fail direction: on the pre-change tree at a090950 the engine,
adapters, roster rows and registry entry do not exist, so these
tests fail or error there; the CONV-47 registry spot checks pass
on both trees by design (they pin what must not move).
"""
import json
import os
import unittest
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER_FALSIFIER = ("The variation's first 20 forward fires "
                      "graded against the installed form's same-day "
                      "fires (the uniform variation falsifier form).")
REGISTER_KILL = ("Paired delta not positive retires the "
                 "variation; the installed form is untouched "
                 "either way.")


def _synth_bars():
    """The research harness's synthetic construction, rebuilt in
    stdlib (harness synth_series): 26 RTH bars/day from Tue
    2024-01-02; opens equal the previous close; h/l are the
    construction's 0.1% pads. Returns (bars, expected) with the
    harness's own expected trades."""
    rows = []
    cur = [datetime(2024, 1, 2, 9, 30)]
    bar_in_day = [0]

    def next_stamp():
        t = cur[0]
        bar_in_day[0] += 1
        if bar_in_day[0] >= 26:
            bar_in_day[0] = 0
            nxt = (t + timedelta(days=1)).replace(hour=9, minute=30)
            while nxt.weekday() >= 5:
                nxt += timedelta(days=1)
            cur[0] = nxt
        else:
            cur[0] = t + timedelta(minutes=15)
        return t

    price = [100.0]

    def add(mult, vol):
        c = price[-1] * mult
        o = price[-1]
        t = next_stamp()
        rows.append({"t": t.strftime("%Y-%m-%dT%H:%M:%S-05:00"),
                     "date": t.strftime("%Y-%m-%d"),
                     "o": o, "h": max(o, c) * 1.001,
                     "l": min(o, c) * 0.999, "c": c, "v": vol})
        price.append(c)

    for _ in range(250):
        add(1.001, 1000)
    add(1.002, 3000)
    a_entry = price[-1]
    for _ in range(26):
        add(0.999, 1000)
    a_exit = price[-1]
    for _ in range(30):
        add(1.001, 1000)
    add(1.002, 3000)
    b_entry = price[-1]
    add(1.16, 1000)
    b_exit = price[-1]
    add(1.0, 1000)
    for _ in range(30):
        add(1.001, 1000)
    add(1.002, 3000)
    c_entry = price[-1]
    add(1.05, 1000)
    add(1.05, 1000)
    add(0.92, 1000)
    c_exit = price[-1]
    add(1.0, 1000)
    for _ in range(30):
        add(1.001, 1000)
    add(1.002, 3000)
    d_entry = price[-1]
    add(0.96, 1000)
    d_exit = price[-1]
    add(1.0, 1000)
    for _ in range(30):
        add(1.001, 1000)
    expected = [
        {"setup": "A", "exit_reason": "TIME_25",
         "return": (0.999 ** 26) - 1.0,
         "entry_price": a_entry, "exit_price": a_exit},
        {"setup": "A", "exit_reason": "TAKE_PROFIT",
         "return": b_exit / b_entry - 1.0,
         "entry_price": b_entry, "exit_price": b_exit},
        {"setup": "A", "exit_reason": "TRAILING_STOP",
         "return": c_exit / c_entry - 1.0,
         "entry_price": c_entry, "exit_price": c_exit},
        {"setup": "A", "exit_reason": "STOP_LOSS",
         "return": d_exit / d_entry - 1.0,
         "entry_price": d_entry, "exit_price": d_exit},
    ]
    return rows, expected


class TestRulePins(unittest.TestCase):
    def test_constants_match_the_research_harness(self):
        from desk3 import sso_opus as m
        self.assertEqual(m.STOP_LOSS_PNL, -0.035)
        self.assertEqual(m.TRAIL_FRACTION, 0.93)
        self.assertEqual(m.TAKE_PROFIT_PNL, 0.15)
        self.assertEqual(m.TIME_25_HELD, 25)
        self.assertEqual(m.TIME_60_HELD, 60)
        self.assertEqual(m.TIME_60_PNL, 0.01)
        self.assertEqual(m.ADX_MIN, 20.0)
        self.assertEqual(m.WARMUP_BARS, 200)
        self.assertEqual(m.SETUP_A_VOL_MULT, 2.0)
        self.assertEqual(m.SETUP_B_VOL_MULT, 1.5)
        self.assertEqual(m.SETUP_B_RSI_MIN, 50.0)

    def test_variation_is_the_only_difference(self):
        from desk3 import sso_opus as m
        self.assertFalse(m.SPECS["sso_opus"]["drop_time25"])
        self.assertTrue(m.SPECS["sso_opus_notime25"]["drop_time25"])
        self.assertEqual(set(m.SPECS),
                         {"sso_opus", "sso_opus_notime25"})


class TestSyntheticKnownAnswer(unittest.TestCase):
    def test_port_reproduces_the_constructed_trades(self):
        from desk3 import sso_opus as m
        bars, expected = _synth_bars()
        trades = m.simulate(bars, drop_time25=False, cost_bp=0.0)
        self.assertEqual(len(trades), len(expected))
        for exp, act in zip(expected, trades):
            self.assertEqual(act["setup"], exp["setup"])
            self.assertEqual(act["exit_reason"], exp["exit_reason"])
            self.assertAlmostEqual(
                act["return"], exp["return"],
                delta=1e-9 * max(1.0, abs(exp["return"])))
            self.assertAlmostEqual(
                act["entry_price"], exp["entry_price"],
                delta=1e-6 * max(1.0, abs(exp["entry_price"])))
            self.assertAlmostEqual(
                act["exit_price"], exp["exit_price"],
                delta=1e-6 * max(1.0, abs(exp["exit_price"])))

    def test_variation_removes_exactly_the_time25_class(self):
        from desk3 import sso_opus as m
        bars, _expected = _synth_bars()
        base = m.simulate(bars, drop_time25=False, cost_bp=0.0)
        var = m.simulate(bars, drop_time25=True, cost_bp=0.0)
        self.assertEqual(
            sum(1 for t in base if t["exit_reason"] == "TIME_25"), 1)
        self.assertFalse(
            any(t["exit_reason"].startswith("TIME_25") for t in var))
        # Downstream of the removed exit, both runs are flat from
        # the same bar, so the constructed TRAILING_STOP and
        # STOP_LOSS trades are identical in the two forms; the
        # held-over first position exits under a surviving class.
        for reason in ("TRAILING_STOP", "STOP_LOSS"):
            b2 = [t for t in base if t["exit_reason"] == reason]
            v2 = [t for t in var if t["exit_reason"] == reason]
            self.assertEqual(len(b2), 1, reason)
            self.assertEqual(len(v2), 1, reason)
            self.assertAlmostEqual(b2[0]["return"], v2[0]["return"],
                                   delta=1e-12)


class TestRosterAndRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            cls.rows = json.load(fh)["sleeves"]
        cls.by_id = {r["id"]: r for r in cls.rows}

    def test_roster_387_with_both_rows_exactly_once(self):
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # (the five overnight basket sleeves rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(self.rows), 400)
        for sid in ("sso_opus", "sso_opus_notime25"):
            hits = [r for r in self.rows if r["id"] == sid]
            self.assertEqual(len(hits), 1, sid)
            self.assertEqual(hits[0]["module"], f"adapters3.{sid}")
            self.assertEqual(hits[0]["inputs"],
                             ["bars", "bars:SSO:15Min", "positions"])
            self.assertFalse(hits[0]["parked"])

    def test_config_rows_match_the_engine(self):
        from desk3 import sso_opus as m
        for row in m.config_rows():
            self.assertEqual(self.by_id[row["id"]], row)

    def test_warm_serves_the_declared_tape(self):
        from desk3 import warm
        hits = [f for f in warm.INTRADAY_FETCHES
                if f[0] == "SSO" and f[1] == "15Min"]
        self.assertEqual(len(hits), 1)
        self.assertGreaterEqual(hits[0][2], 30)

    def test_registry_declares_the_granular_key(self):
        # The fed registry marks a granular bars input produced
        # only when the bars_timeframes producer declares it
        # (desk3/producers_g4.py _BARS_TF_KEYS); without this the
        # pair read UNFED by name even with the tape served.
        from desk3.producers_g4 import _BARS_TF_KEYS
        self.assertIn("bars:SSO:15Min", _BARS_TF_KEYS)

    def test_registry_entry_carries_the_register_texts(self):
        reg = json.loads(open(os.path.join(
            ROOT, "config", "conversion_variations_20261115.json"))
            .read())
        hits = [v for v in reg["variations"] if v["conv"] == "CONV-46"]
        self.assertEqual(len(hits), 1)
        v = hits[0]
        self.assertEqual(v["id"], "sso_opus_notime25")
        self.assertEqual(v["parent"], "sso_opus")
        self.assertEqual(v["falsifier"], REGISTER_FALSIFIER)
        self.assertEqual(v["kill_rule"], REGISTER_KILL)
        self.assertIn("Fidelity basis", v["replay_counts"])

    def test_conv47_entry_untouched(self):
        reg = json.loads(open(os.path.join(
            ROOT, "config", "conversion_variations_20261115.json"))
            .read())
        (v,) = [x for x in reg["variations"] if x["conv"] == "CONV-47"]
        self.assertEqual(v["id"], "aster_trader_turtle2010")
        self.assertEqual(v["parent"], "aster_trader_donchian55")


def _rth_stamps(n, start=datetime(2026, 11, 16, 14, 30)):
    """n RTH 15-minute bar stamps (UTC ISO) from Mon 2026-11-16
    09:30 ET, 26 bars per day, weekdays only."""
    out = []
    t = start
    while len(out) < n:
        if t.weekday() < 5:
            for _ in range(26):
                out.append(t)
                t += timedelta(minutes=15)
                if len(out) >= n:
                    break
        t = t.replace(hour=14, minute=30) + timedelta(days=1)
    return [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in out]


class TestLiveEvaluate(unittest.TestCase):
    def _view(self, bars, positions):
        return {"bars": {"SSO|15Min": bars}, "positions": positions,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}

    def test_entry_signal_fires_through_evaluate(self):
        from adapters3 import sso_opus as ad
        stamps = _rth_stamps(260)
        bars = []
        px = 50.0
        for i, s in enumerate(stamps):
            prev = px
            px *= 1.01 if i == len(stamps) - 1 else 1.001
            bars.append({"t": s, "o": prev, "h": px * 1.001,
                         "l": prev * 0.999, "c": px,
                         "v": 3000.0 if i == len(stamps) - 1
                         else 1000.0})
        out = ad.evaluate(self._view(bars, []))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "enter")
        self.assertEqual(out[0].symbol, "SSO")
        self.assertEqual(out[0].side, "buy")

    def test_time25_exit_in_baseline_absent_in_variation(self):
        from adapters3 import sso_opus as base_ad
        from adapters3 import sso_opus_notime25 as var_ad
        stamps = _rth_stamps(40)
        bars = []
        px = 50.0
        for i, s in enumerate(stamps):
            if i >= 10:
                px *= 0.999  # gentle decline: pnl<0, no stop/trail
            bars.append({"t": s, "o": px, "h": px * 1.001,
                         "l": px * 0.999, "c": px, "v": 1000.0})
        pos = [{"symbol": "SSO", "qty": 100.0,
                "avg_price": bars[10]["o"],
                "opened_at": stamps[10]}]
        out_b = base_ad.evaluate(self._view(bars, pos))
        self.assertEqual(len(out_b), 1)
        self.assertEqual(out_b[0].kind, "exit")
        self.assertIn("TIME_25", out_b[0].reason)
        out_v = var_ad.evaluate(self._view(bars, pos))
        self.assertEqual(out_v, [])


if __name__ == "__main__":
    unittest.main()
