"""Edge batch 18 blockers — ENH2-18 (2026-10-24), second Edge look.

Binding leaks (measured pre-change in the batch work log; every
sleeve below entered on the stale/wide fixture pre-change):
- 9 sleeves (red_day_reversal, rsi_meanrev, rule_1d_cyan_smallcap,
  rule_1d_green_tom, rule_1h_cyan_raw, rule_1w_cyan_mom_adx,
  rule_1w_swing_beta_wt, s_1dg, s_1dgp5): entries sized/priced off
  the newest bar with NO comparison of that bar's timestamp to the
  decision clock — a dead bars feed still enters days later at the
  stale close. Cure: desk3/enhance18 stale_bar_gate at the adapter
  layer (default ON; OFF = pre-change exactly), exits unfiltered.
- rsi_meanrev_options: short leg's spread ungated (debit priced off
  its bid, exit off its ask). Cure: short_leg_spread_gate > 0.50
  of mid refused.
Fail-first: with the adapter wiring stashed, the stale/wide tests
fail (entries emitted); fresh/tight fixtures pass both ways.
"""
import importlib, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import test_port_batch6_blockers as b6
import test_lazarus_batch1_blockers as lz1
import test_lazarus_batch2_blockers as lz2
from desk3 import enhance18

ET = b6.ET


def entries(out):
    return [i for i in out if i["kind"] == "entry"]


def stale_now(iso_date, days=10):
    d = date.fromisoformat(iso_date) + timedelta(days=days)
    return f"{d.isoformat()}T10:00:00-04:00"


class TestStaleDailyGate(unittest.TestCase):
    def test_red_day_stale_refused_fresh_enters(self):
        closes = [50.0 + 50.0 * i / 208 for i in range(209)] + [96.5]
        last = b6.last_date(date(2025, 1, 1), len(closes))
        bars = {"SPY|1Day": b6.daily(closes)}
        self.assertEqual(entries(b6.evaluate(
            "red_day_reversal", b6.view_for(stale_now(last), bars))), [])
        self.assertEqual(len(entries(b6.evaluate(
            "red_day_reversal",
            b6.view_for(f"{last}T10:00:00-04:00", bars)))), 1)

    def test_red_day_switch_off_restores_stale_entry(self):
        closes = [50.0 + 50.0 * i / 208 for i in range(209)] + [96.5]
        last = b6.last_date(date(2025, 1, 1), len(closes))
        v = b6.view_for(stale_now(last), {"SPY|1Day": b6.daily(closes)},
                        extra={"red_day_reversal_enh2": {"stale_bar_gate": False}})
        self.assertEqual(len(entries(b6.evaluate("red_day_reversal", v))), 1)

    def test_red_day_exit_never_filtered_when_stale(self):
        closes = [90.0] * 209 + [104.5]
        last = b6.last_date(date(2025, 1, 1), len(closes))
        out = b6.evaluate("red_day_reversal", b6.view_for(
            stale_now(last), {"SPY|1Day": b6.daily(closes)},
            positions=b6.seeded("SPY", 50, 100.0, "2025-07-26T14:00:00Z")))
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1)

    def test_rsi_stale_refused(self):
        last = b6.last_date(date(2025, 1, 1), len(b6.RSI_ENTRY_CLOSES))
        extra = {"earnings": {"SPY": None}, "earnings_fresh": True}
        out = b6.evaluate("rsi_meanrev", b6.view_for(
            stale_now(last), {"SPY|1Day": b6.daily(b6.RSI_ENTRY_CLOSES)},
            extra=extra))
        self.assertEqual(entries(out), [])

    def test_rule_sleeves_stale_refused(self):
        cases = [
            ("rule_1d_cyan_smallcap", {"pxn": 2, "di": 0.0}, 7.0,
             {"log_mcap": {"MU": 9.0}}),
            ("rule_1w_cyan_mom_adx", {"dv": 7.0, "mom": 0.5, "adx": 30.0},
             20.0, {}),
            ("rule_1w_swing_beta_wt", {"beta": 1.5, "wt1": 30.0,
                                       "ribbons": 0.02}, 20.0, {}),
        ]
        for sid, feats, px, kw in cases:
            bars, session, extra, sym = b6._rule_entry(sid, feats, px=px)
            extra.update(kw)
            out = b6.evaluate(sid, b6.view_for(
                stale_now(session), {"MU|1Day": bars}, extra=extra))
            self.assertEqual(entries(out), [], sid)
            fresh = b6.evaluate(sid, b6.view_for(
                f"{session}T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
            self.assertEqual(len(entries(fresh)), 1, sid)

    def test_green_tom_stale_refused(self):
        days = []
        d = date(2025, 8, 1)
        while d <= date(2025, 9, 2):
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)
        bars = b6.daily([20.0] * 25, start=date(2025, 8, 9), vol=100000.0)
        extra = {"rule_fires": {"MU": [{"date": "2025-09-02", "features":
                                        {"mom121": 0.7, "disp": 0.025,
                                         "tom": 0}}]},
                 "trading_days": days}
        out = b6.evaluate("rule_1d_green_tom", b6.view_for(
            "2025-09-12T10:00:00-04:00", {"MU|1Day": bars}, extra=extra))
        self.assertEqual(entries(out), [])

    def test_rule_1h_stale_refused_fresh_enters(self):
        hb = b6._hourly(120)
        last_iso = datetime.fromisoformat(
            hb[-1]["t"].replace("Z", "+00:00")).isoformat()
        sig_date = datetime.fromisoformat(
            hb[-1]["t"].replace("Z", "+00:00")).astimezone(ET).date()
        dbars = b6.daily([10.0] * 25, start=sig_date - timedelta(days=24),
                         vol=200000.0)
        extra = {"rule_fires_1h": {"MU": [{"t": last_iso, "rangeatr": 3.0,
                                           "wtgap": 7.0, "smhUp": 1}]}}
        view_bars = {"MU|1Hour": hb, "MU|1Day": dbars}
        out = b6.evaluate("rule_1h_cyan_raw", b6.view_for(
            "2026-11-02T12:30:00-05:00", view_bars, extra=extra))
        self.assertEqual(entries(out), [])
        out = b6.evaluate("rule_1h_cyan_raw", b6.view_for(
            "2026-10-21T12:30:00-04:00", view_bars, extra=extra))
        self.assertEqual(len(entries(out)), 1)


class TestLazarusStaleGate(unittest.TestCase):
    def test_s_1dg_stale_bar_refused_fresh_enters(self):
        base = lz1.NOW - timedelta(days=20)
        bars = {"AAA|1Day": [{"t": (base + timedelta(days=i)).isoformat(),
                              "o": 10, "h": 10, "l": 10, "c": 10,
                              "v": 1000} for i in range(3)]}
        out = lz1.mod("s_1dg").evaluate(
            lz1.view([lz1.fire("s_1dg")], extra_bars=bars), lz1.ctx())
        self.assertEqual(entries(out), [])
        fresh = {"AAA|1Day": [{"t": f"2026-10-{20 + i:02d}T14:00:00Z",
                               "o": 10, "h": 10, "l": 10, "c": 10,
                               "v": 1000} for i in range(3)]}
        out = lz1.mod("s_1dg").evaluate(
            lz1.view([lz1.fire("s_1dg")], extra_bars=fresh), lz1.ctx())
        self.assertEqual(len(entries(out)), 1)

    def test_s_1dgp5_stale_bar_refused_fresh_enters(self):
        base = datetime.fromisoformat("2026-10-01T14:00:00-04:00")
        bars = {"ACME|1Day": [{"t": (base + timedelta(days=i)).isoformat(),
                               "o": 2, "h": 2, "l": 2, "c": 2,
                               "v": 1000} for i in range(3)]}
        v = lz2.lview([lz2.lfire("s_1dgp5", family="green")],
                      extra_bars=bars)
        self.assertEqual(entries(lz2.lev("s_1dgp5", v)), [])
        fresh = {"ACME|1Day": [{"t": f"2026-10-{22 + i:02d}T14:00:00Z",
                                "o": 2, "h": 2, "l": 2, "c": 2,
                                "v": 1000.0} for i in range(2)]}
        v = lz2.lview([lz2.lfire("s_1dgp5", family="green")],
                      extra_bars=fresh)
        out = lz2.lev("s_1dgp5", v)
        self.assertEqual(len(entries(out)), 1)
        self.assertEqual(out[0]["qty"], 500)  # ENH-LAZ-REPRICE is ENGINE-WIDE by design (batch-1 addendum: batch 19's bound guard + batch 21's moonshot rest on it): sizing runs off the freshest bar close ($2), so $1,000/2 = 500 — not the $3 fire print's 333. The stale-gate behavior above is unaffected.


class TestShortLegSpreadGate(unittest.TestCase):
    def _run(self, short_ask, extra_kw=None):
        session_d = date(2025, 1, 1) + timedelta(
            days=len(b6.RSI_ENTRY_CLOSES) - 1)
        extra = b6._opt_extra(session_d)
        for occ, q in extra["quotes"].items():
            if occ.endswith("C00121000"):
                q.update({"bid": 0.10, "ask": short_ask})
        if extra_kw:
            extra.update(extra_kw)
        return b6.evaluate("rsi_meanrev_options", b6.view_for(
            f"{session_d.isoformat()}T10:00:00-04:00",
            {"SPY|1Day": b6.daily(b6.RSI_ENTRY_CLOSES)}, extra=extra))

    def test_wide_short_leg_refused(self):
        self.assertEqual(entries(self._run(0.60)), [])  # frac 1.43

    def test_tight_short_leg_enters(self):
        self.assertEqual(len(entries(self._run(0.11))), 1)

    def test_switch_off_restores_wide_entry(self):
        out = self._run(0.60, {"rsi_meanrev_options_enh2":
                               {"short_leg_spread_gate": False}})
        self.assertEqual(len(entries(out)), 1)

    def test_paired_record_written(self):
        enhance18.LAST_PAIRED.clear()
        self._run(0.60)
        recs = [r for r in enhance18.LAST_PAIRED
                if r["sleeve"] == "rsi_meanrev_options"]
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["treatment_decision"], "refuse")
        self.assertGreater(recs[0]["short_spread_frac"], 0.50)


if __name__ == "__main__":
    unittest.main()
