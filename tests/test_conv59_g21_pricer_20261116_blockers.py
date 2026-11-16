"""CONV59-G21-PRICER-20261116 regression blockers.

The G21 jump-aware pricer miniature (CONV-59) is built to its
register row's exact specification: a pricing component (never a
strategy, no sizing), fit on the held index rows, adoption-tested
against the desk's Black-Scholes inversion on the held next-day
pairs, reading the Focus chain panel in the format that exists
(iv_ledger_modelled.jsonl). These tests pin:

- the panel-format reader and the estate's keep-last dedupe;
- Black-Scholes known answers (put-call parity, ATM value);
- the surface fit's recovery of a known surface and the
  adoption test's machinery (a spot-shifted surface is priced
  better by the fit than by the carried-forward baseline);
- the Focus use condition (no sizing use until a second dated
  panel exists);
- the held-store fixture proof: the Focus panel census
  reproduces DH4's published quantities exactly (27,405
  quote-carrying modelled-IV rows, 31 underlyings, 1 session
  2026-11-14) and the index ledger's DH4-era total reproduces
  exactly (134,857 rows; SPY 57,855, QQQ 54,186, IWM 22,816);
- the adoption verdict on the held DH4-era pairs under the
  module's named pair definition (107,196 pairs; DH4's printed
  103,675 was snapshot-counted and does not reproduce — named in
  desk3/g21_pricer.py): the miniature does NOT beat the desk's
  inversion (MAE 6.82 vs 3.58 vol points), so under the row's
  Kill rule it is NOT adopted. This test pins that verdict so a
  silent change to either number is a named event.

Fail direction: on the pre-cure tree desk3/g21_pricer.py does
not exist, so every test errors on import.
"""
import json
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

INDEX_LEDGER = os.path.expanduser(
    "~/workspace/morgue/state/morgue/chains/"
    "iv_ledger_modelled.jsonl")
FOCUS_LEDGER = os.path.expanduser(
    "~/workspace/research_notes/decisions-api-leverage-20261114/"
    "keepgoing2/wave4/dry_capture/store/iv_ledger_modelled.jsonl")


def _row(date="2026-11-12", expiry="2026-12-12", occ="X1",
         underlying="SPY", side="call", spot=100.0, strike=100.0,
         iv=0.20, mid=5.0):
    return {"date": date, "expiry": expiry, "occ": occ,
            "underlying": underlying, "side": side, "spot": spot,
            "strike": strike, "iv": iv, "quote_mid": mid,
            "quote_bid": mid - 0.05, "quote_ask": mid + 0.05,
            "captured_at_utc": date + "T14:57:00Z",
            "iv_basis": "MODELLED", "model": "MODELLED"}


class TestMachinery(unittest.TestCase):
    def test_dedupe_keep_last(self):
        from desk3.g21_pricer import dedupe_rows
        rows = [_row(iv=0.20), _row(iv=0.25)]
        by = dedupe_rows(rows)
        self.assertEqual(len(by), 1)
        self.assertEqual(
            by[("2026-11-12", "X1")]["iv"], 0.25)

    def test_bs_put_call_parity(self):
        from desk3.g21_pricer import bs_price, tenor_years
        t = tenor_years("2026-11-12", "2026-12-12")
        c = bs_price(100.0, 100.0, t, 0.20, "call", "SPY")
        p = bs_price(100.0, 100.0, t, 0.20, "put", "SPY")
        fwd_cash = 100.0 * math.exp(-0.013 * t) \
            - 100.0 * math.exp(-0.045 * t)
        self.assertAlmostEqual(c - p, fwd_cash, places=8)

    def test_fit_recovers_known_surface(self):
        from desk3.g21_pricer import fit_surface, predict_iv, \
            _features
        coef = [0.22, -0.35, 0.9, 0.02, 0.015]
        rows = []
        for i, k in enumerate(range(80, 121, 4)):
            for exp in ("2026-11-19", "2026-12-17",
                        "2027-02-19"):
                from desk3.g21_pricer import tenor_years
                t = tenor_years("2026-11-12", exp)
                x = _features(100.0, float(k), t, "SPY")
                iv = sum(c * v for c, v in zip(coef, x))
                rows.append(_row(expiry=exp, occ=f"S{i}{exp}",
                                 strike=float(k), iv=iv))
        fit = fit_surface(rows)
        self.assertIsNotNone(fit)
        pred = predict_iv(fit, 100.0, 100.0, "2026-11-12",
                          "2026-12-17")
        from desk3.g21_pricer import tenor_years
        x = _features(100.0, 100.0,
                      tenor_years("2026-11-12", "2026-12-17"),
                      "SPY")
        want = sum(c * v for c, v in zip(coef, x))
        self.assertAlmostEqual(pred, want, places=3)

    def test_adoption_machinery_rewards_surface_on_spot_shift(
            self):
        from desk3.g21_pricer import adoption_test, _features, \
            tenor_years
        coef = [0.22, -0.35, 0.9, 0.02, 0.015]

        def surf(spot, strike, d, exp):
            x = _features(spot, strike, tenor_years(d, exp), "SPY")
            return sum(c * v for c, v in zip(coef, x))

        rows = []
        for day, spot in (("2026-11-12", 100.0),
                          ("2026-11-13", 110.0)):
            for k in range(85, 116, 3):
                for exp in ("2026-12-17", "2027-01-15",
                            "2027-03-19"):
                    rows.append(_row(
                        date=day, expiry=exp, occ=f"K{k}E{exp}",
                        spot=spot, strike=float(k),
                        iv=surf(spot, float(k), day, exp)))
        res = adoption_test(rows)
        self.assertEqual(res["pairs"], 33)
        self.assertLess(res["mae_miniature_volpts"],
                        res["mae_baseline_volpts"])
        self.assertTrue(res["adopted"])

    def test_focus_use_condition(self):
        from desk3.g21_pricer import focus_use_allowed
        self.assertFalse(focus_use_allowed([_row()]))
        self.assertTrue(focus_use_allowed(
            [_row(), _row(date="2026-11-15", occ="X2")]))


@unittest.skipUnless(os.path.exists(FOCUS_LEDGER),
                     "Focus panel store not on this box")
class TestHeldFocusPanel(unittest.TestCase):
    def test_focus_census_reproduces_dh4(self):
        from desk3.g21_pricer import read_ledger, census, \
            focus_use_allowed
        rows = read_ledger(FOCUS_LEDGER)
        c = census(rows)
        self.assertEqual(c["rows"], 27405)
        self.assertEqual(c["quote_iv_rows"], 27405)
        self.assertEqual(c["n_underlyings"], 31)
        self.assertEqual(c["dates"], ["2026-11-14"])
        self.assertFalse(focus_use_allowed(rows))

    def test_focus_cross_section_fits_all_underlyings(self):
        from desk3.g21_pricer import read_ledger, \
            fit_focus_cross_section
        out = fit_focus_cross_section(read_ledger(FOCUS_LEDGER))
        self.assertEqual(len(out["fits"]), 31)
        self.assertTrue(all(f["fitted"]
                            for f in out["fits"].values()))
        self.assertFalse(out["use_allowed"])


@unittest.skipUnless(os.path.exists(INDEX_LEDGER),
                     "index ledger not on this box")
class TestHeldIndexLedger(unittest.TestCase):
    def test_index_era_census_reproduces_dh4(self):
        from desk3.g21_pricer import read_ledger
        rows = read_ledger(INDEX_LEDGER)
        era = [r for r in rows if r["date"] <= "2026-11-13"]
        self.assertEqual(len(era), 134857)
        per = {}
        for r in era:
            per[r["underlying"]] = per.get(r["underlying"], 0) + 1
        self.assertEqual(per, {"SPY": 57855, "QQQ": 54186,
                               "IWM": 22816})

    def test_adoption_verdict_on_held_era_pairs(self):
        from desk3.g21_pricer import read_ledger, adoption_test
        rows = read_ledger(INDEX_LEDGER)
        res = adoption_test(rows, max_date="2026-11-13")
        self.assertEqual(res["pairs"], 107196)
        self.assertEqual(res["scored"], 107196)
        # The Kill rule applied to the held sample: the miniature
        # does not beat the desk's carried-forward inversion, so
        # it is not adopted. Pinned as a verdict, not a target.
        self.assertGreater(res["mae_miniature_volpts"],
                           res["mae_baseline_volpts"])
        self.assertFalse(res["adopted"])
        self.assertAlmostEqual(res["mae_baseline_volpts"], 3.5782,
                               places=2)
        self.assertAlmostEqual(res["mae_miniature_volpts"], 6.8185,
                               places=2)


if __name__ == "__main__":
    unittest.main()
