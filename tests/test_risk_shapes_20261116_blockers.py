"""RISK-SHAPES-20261116 regression blockers (desk full audit
escalation 6, owner ruling 2026-11-16 09:22 ET).

Item B, SATY-DAY-STOP-20261116 (the cure these tests block):
saty_day's DAILY_STOP_USD was 10000.0 on a $10,000 slice
(config/sleeves.json saty_day slice capital_usd 10000.0;
desk3/port_batch6.py row agrees) — 100% of the slice, i.e. no
stop at all. The cure takes the Saty family's standard daily
stop fraction, sourced from the sibling Saty sleeves' code:
sleeves/saty_magnum.py SESSION_STOP_PCT = 0.01 (MAG-B3) and
sleeves/saty_sol_0dte.py DAILY_LOSS_FRACTION = 0.01, each
applied against session P&L as a fraction of slice equity in
the same _session_pnl idiom saty_day uses. saty_sol is NOT a
source (pinned, excluded by the task). The halt is journaled
on the evaluation stamp as daily_stop_fraction /
daily_stop_usd so the landed value is visible in the record.

Item A, PRZM-ZERO-RISKSHAPE-20261116 (BLOCKED disposition,
pinned here so the evidence cannot silently change): no
stop/target was landed for przm_zero, because (1) no
transferable family standard exists in the code — every
zero-DTE sibling read carries its kill/target as in-sleeve
underlying-level rules derived from a structure przm_zero
does not possess (Saty ladder anchor/ATR unit, em_1587 box
edge, przm_fade_edges gamma magnet/edge, shen_fade option
premium bracket) and the family's standard for the Intent
fields themselves is to NOT set them (saty_day, em_1587 and
shen_fade state this in their headers verbatim); and (2) the
required replay population is empty — przm_zero's live journal
holds zero recorded calls (147 of 147 rows unfed on
2026-11-16) and the only recorded tape, the real 2026-11-13
fixture replayed below, judges zero prints, so zero calls
exist to replay any shape against. The Item A tests pin those
facts: if a judged tape or a recorded call ever appears, the
census test fails loudly and the disposition must be revisited.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
SESSION = "2026-10-21"
SESSION_D = date(2026, 10, 21)


# ------------------------------------------------------------ saty_day drive
def _b(t_epoch, o, h, l, c, v=10000.0):
    return {"t": t_epoch, "o": o, "h": h, "l": l, "c": c, "v": v}


def _trading_days_before(n, end=SESSION_D):
    days, d = [], end - timedelta(days=1)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return sorted(days)


def _rth_closes():
    pts = []
    for i in range(78):
        if i <= 20:
            c = 500.0 + 4.0 * i / 20
        elif i <= 50:
            c = 504.0 - 8.0 * (i - 20) / 30
        else:
            c = 496.0 + 4.0 * (i - 50) / 27
        pts.append(round(c, 4))
    pts[-1] = 500.0
    return pts


def _hist_bars(days):
    """The port_batch6 proven warmup recipe: 66 extended + 78 RTH
    + 48 extended 5-minute bars per day at the closes pattern."""
    out = []
    prev_close = 500.0
    for d in days:
        t = datetime.combine(d, time(4, 0), tzinfo=ET)
        for _ in range(66):
            out.append(_b(t.timestamp(), prev_close, prev_close + 0.3,
                          prev_close - 0.3, prev_close))
            t += timedelta(minutes=5)
        prev = prev_close
        for c in _rth_closes():
            o = prev
            h = max(o, c) + (1.0 if c == 504.0 else 0.15)
            l = min(o, c) - (1.0 if c == 496.0 else 0.15)
            out.append(_b(t.timestamp(), o, h, l, c))
            prev = c
            t += timedelta(minutes=5)
        for _ in range(48):
            out.append(_b(t.timestamp(), prev, prev + 0.3,
                          prev - 0.3, prev))
            t += timedelta(minutes=5)
        prev_close = prev
    return out


_HIST = None


def _drive(pnl_fills, equity=10000.0):
    """One saty_day evaluation, flat today, no position, with the
    session's fills served. Returns (intents, stamp)."""
    global _HIST
    if _HIST is None:
        _HIST = _hist_bars(_trading_days_before(110))
    from core.sleeve import Context
    from sleeves.saty_day import SatyDay
    now = datetime.combine(SESSION_D, time(10, 6), tzinfo=ET)
    extra = {"bars_5m_long": {"SPY": list(_HIST), "QQQ": list(_HIST)},
             "bars_1m": {"SPY": [], "QQQ": []},
             "session_fills": pnl_fills,
             "sleeve_state": {}}
    ctx = Context(now=now.timestamp(), session=SESSION,
                  equity=equity, extra=extra)
    s = SatyDay()
    out = s.signal({}, {}, ctx)
    return out, s.last_evaluation


def _fills_for_pnl(pnl):
    """A closed round trip realizing exactly `pnl` (options x100):
    buy 1 contract at (150 - pnl)/100... constructed directly:
    buy_to_open at price B, sell_to_close at price B + pnl/100,
    qty 1, so cash = -100*B + 100*(B + pnl/100) = pnl."""
    b = 3.0
    return [{"qty": 1, "price": b, "position_intent": "buy_to_open"},
            {"qty": 1, "price": b + pnl / 100.0,
             "position_intent": "sell_to_close"}]


class TestSatyDayStopSource(unittest.TestCase):
    def test_fraction_constant_matches_both_sibling_sources(self):
        from sleeves import saty_day, saty_magnum, saty_sol_0dte
        self.assertEqual(saty_magnum.SESSION_STOP_PCT, 0.01)
        self.assertEqual(saty_sol_0dte.DAILY_LOSS_FRACTION, 0.01)
        self.assertEqual(saty_day.DAILY_STOP_FRACTION, 0.01)
        self.assertEqual(saty_day.DAILY_STOP_FRACTION,
                         saty_magnum.SESSION_STOP_PCT)
        self.assertEqual(saty_day.DAILY_STOP_FRACTION,
                         saty_sol_0dte.DAILY_LOSS_FRACTION)

    def test_absolute_slice_sized_stop_is_gone(self):
        from sleeves import saty_day
        self.assertFalse(hasattr(saty_day, "DAILY_STOP_USD"),
                         "the 100%-of-slice absolute stop must not "
                         "survive in any form")


class TestSatyDayStopBehavior(unittest.TestCase):
    def test_halts_at_family_threshold_on_the_slice(self):
        # session P&L -150.00 = -1.5% of the $10,000 slice: past
        # the family 1% stop ($100.00), far above the old $10,000.
        out, stamp = _drive(_fills_for_pnl(-150.0), equity=10000.0)
        self.assertEqual(out, [])
        self.assertEqual(stamp["session_pnl"], -150.0)
        self.assertTrue(stamp.get("daily_stop_halt"))
        self.assertEqual(stamp.get("stood_down"), "daily_stop")
        # the landed value is journaled as the sourced constant
        self.assertEqual(stamp.get("daily_stop_fraction"), 0.01)
        self.assertEqual(stamp.get("daily_stop_usd"), 100.0)

    def test_no_halt_above_threshold(self):
        # -50.00 = -0.5% of the slice: inside the family stop.
        _out, stamp = _drive(_fills_for_pnl(-50.0), equity=10000.0)
        self.assertEqual(stamp["session_pnl"], -50.0)
        self.assertNotEqual(stamp.get("stood_down"), "daily_stop")
        self.assertFalse(stamp.get("daily_stop_halt"))

    def test_threshold_scales_with_slice_equity(self):
        # The family form is a fraction of equity, not a hard-coded
        # $100: on a $100,000 slice the same -150.00 does not halt,
        # and -1,500.00 (=-1.5%) halts at a journaled $1,000.00.
        _out, stamp = _drive(_fills_for_pnl(-150.0), equity=100000.0)
        self.assertFalse(stamp.get("daily_stop_halt"))
        out, stamp = _drive(_fills_for_pnl(-1500.0), equity=100000.0)
        self.assertEqual(out, [])
        self.assertTrue(stamp.get("daily_stop_halt"))
        self.assertEqual(stamp.get("daily_stop_usd"), 1000.0)


class TestSatyDayV2DivergenceConfinement(unittest.TestCase):
    """The port_batch6 byte-identity pin carries a named
    SATY-DAY-STOP-20261116 exemption for saty_day (the raschke_rre
    form). This test confines that exemption: every v2->v3 change
    group in sleeves/saty_day.py must be a daily-stop hunk, and
    the cured assignment must be among them. Any other divergence
    from v2 fails here loudly."""

    V2_FILE = "/home/hatch/workspace/muse-desk-v2/sleeves/saty_day.py"

    @unittest.skipUnless(os.path.exists(V2_FILE), "v2 tree absent")
    def test_divergence_confined_to_daily_stop_hunks(self):
        import difflib
        old = open(self.V2_FILE).read().splitlines()
        new = open(os.path.join(ROOT, "sleeves", "saty_day.py")
                   ).read().splitlines()
        markers = ("DAILY_STOP", "daily stop", "daily_stop",
                   "$10,000", "$10K", "SATY-DAY-STOP")
        groups = list(difflib.SequenceMatcher(
            None, old, new).get_grouped_opcodes(0))
        self.assertTrue(groups, "saty_day must diverge from v2 "
                                "by the landed cure, not silently "
                                "return to the v2 stop")
        saw_assignment = False
        for group in groups:
            text = []
            for tag, i1, i2, j1, j2 in group:
                text += old[i1:i2] + new[j1:j2]
            joined = "\n".join(text)
            self.assertTrue(any(m in joined for m in markers),
                            "non-daily-stop divergence from v2: "
                            + joined[:200])
            if "DAILY_STOP_FRACTION = 0.01" in joined:
                saw_assignment = True
        self.assertTrue(saw_assignment)


# ------------------------------------------------------------ przm_zero pins
class TestPrzmZeroReplayPopulation(unittest.TestCase):
    def test_recorded_tape_replay_yields_zero_calls(self):
        """The only recorded przm tape (real Alpaca v1beta1 SPY
        0DTE prints, 2026-11-13 14:00-14:20Z) built through the
        desk's own bridge: every print is unjudged (quotes for the
        expired contracts are not served), every spec weight is 0,
        no bucket forms, the score is 0 and no call can be made.
        Any future judged tape changes this census and fails this
        test — by design, so the BLOCKED disposition is revisited
        on evidence, not on memory."""
        from desk3 import przm_tape
        from desk3.producers import _bs_call_price
        from sleeves.przm_zero import (bs_delta, bucketize,
                                       compute_drivers, print_weight)

        def bs_price(S, K, T, sigma, is_call):
            c = _bs_call_price(S, K, T, 0.0, sigma)
            return c if is_call else c - S + K

        fx = json.load(open(os.path.join(
            ROOT, "tests", "fixtures", "przm_tape_20261113.json")))
        quotes = {k: tuple(v) for k, v in fx["quotes"].items()}
        prints = przm_tape.build_prints(fx["trades"], quotes,
                                        fx["spot"], bs_price, bs_delta)
        self.assertEqual(len(prints), 3035)
        self.assertTrue(all(p.get("bull") is None for p in prints))
        self.assertTrue(all(print_weight(p) == 0.0 for p in prints))
        buckets = bucketize(prints, fx["spot"])
        self.assertEqual(buckets, [])
        drv = compute_drivers(buckets, fx["spot"], fx["spot"], 0.001)
        self.assertEqual(drv["score"], 0)

    def test_entry_intent_carries_no_stop_or_target_today(self):
        """Pins the named-open state (audit escalation 6): a driven
        entry intent carries stop=None / target=None. Landing a
        shape must deliberately change this pin, with the replay
        evidence the BUGLOG disposition names."""
        from core.sleeve import Context
        from sleeves.przm_zero import PrzmZeroSleeve
        bars = []
        t0 = datetime(2026, 10, 29, 9, 30, tzinfo=ET).timestamp()
        for i in range(40):
            bars.append({"t": t0 + i * 60, "o": 100.0, "h": 100.2,
                         "l": 99.8, "c": 100.0, "v": 1000})
        t_ms = int(bars[39]["t"] * 1000)
        prints = [{"t": t_ms, "bull": 1, "delta": 0.5, "price": 3.0,
                   "size": 100, "is_call": True}]
        ctx = Context(now=bars[39]["t"] + 60, session="2026-10-29",
                      equity=10000.0, extra={"przm_prints": prints})
        out = PrzmZeroSleeve().signal({"SPY": bars}, {}, ctx)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "enter")
        self.assertIsNone(out[0].stop)
        self.assertIsNone(out[0].target)


class TestPrzmZeroSiblingShapeCensus(unittest.TestCase):
    def test_sibling_shapes_are_structure_bound_not_transferable(self):
        """Source pins for the BLOCKED evidence: each sibling's
        kill/target derives from its own structure, and przm_zero
        possesses none of those structures (no ladder fractions,
        no gamma levels, no box edge in its module)."""
        from sleeves import przm_zero, saty_day, saty_sol_0dte
        # Saty ladder shape: kill at the 0.236 trigger level,
        # target at the 0.618 level — of an anchor/ATR ladder.
        self.assertEqual(saty_day.F_TRIGGER, 0.236)
        self.assertEqual(saty_day.F_TARGET, 0.618)
        self.assertEqual(saty_sol_0dte.F_TRIGGER, 0.236)
        self.assertEqual(saty_sol_0dte.F_TARGET, 0.618)
        # przm_zero has no ladder, no gamma magnet, no box edge.
        for name in ("F_TRIGGER", "F_TARGET", "F_GATE",
                     "gamma_levels", "INVALID_FRAC"):
            self.assertFalse(hasattr(przm_zero, name), name)
        # its own exits are the frozen spec's: drop / flip / 15:45.
        self.assertEqual(przm_zero.DROP_SCORE, 8)
        self.assertEqual(przm_zero.FLIP_SCORE, 35)


if __name__ == "__main__":
    unittest.main()
