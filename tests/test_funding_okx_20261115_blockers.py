"""FUNDING-OKX-20261115 blockers: the funding-gated Aster family was
registry-FED but form-starved, and no OKX funding producer existed.

The defect, proven at unit level pre-cure: the registered funding
producer (CoinalyzeFunding) served view["funding"] as {SYM: float}
with no settlement stamps. aster_sleeves/_common.known_funding_rate
iterates funding RECORDS and raises TypeError on a float, so the
five _common sleeves (aster_abs_neg_ada x2, aster_abs_nonneg_ada
x2, aster_squeeze_ada_fullcash) could never read a rate on a live
snapshot; and the record form every other funding engine unwraps
({SYM: {"rate": x}}) was returned RAW by the two outlier readers
desk3/aster_batch13._funding and desk3/aster_batch8._funding, whose
callers float() it. Vein 2 (pass2/VEIN2-DIG.md) proved the class
UNFED, not gated: with OKX funding-rate-history served in record
form, all 28 funding sleeves fire on their own engines.

Pins:
- OkxFunding serves {SYM: {"rate", "settled_at", "received_at"}}
  from OKX public funding-rate-history (ADA/ENJ/LINK USDT swaps),
  persists the fetched history to state/okx_funding_history.json,
  and stamps funding_source "okx";
- fail-closed: fetch failure with no cache or a stale cache (>3h)
  serves {}; a fresh cache serves; a symbol whose latest print is
  >24h old is omitted; a missing symbol never zeroes the others;
- EVERY engine funding reader reads the served form (the _common
  known_funding_rate, b11, aster_crypto, batch7, batch13, batch8,
  gate_distance);
- register_all wires the funding output to the OKX producer;
- the two Vein 2 MISPRICED sign-gate forms are registered as
  _varsg variations in config/f4_variations_20261115.json with
  their replay counts and the uniform falsifier, parents and the
  339 roster untouched.
  AMENDED 2026-11-15 (VARIATION-ROSTERING-20261115): the 19 F4
  variations are now rostered as first-class sleeves (roster
  339 -> 358); the roster pin below moves to 358 and the _varsg
  absence assertion becomes a presence assertion. The funding
  cure's own assertions are unchanged.

Fail direction: on the preserved pre-cure tree
(/tmp/funding_okx_precure) the OkxFunding import fails, the wiring
test finds the Coinalyze scalar producer, batch13/batch8 return
the record dict raw, and the variation rows are absent.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 11, 15, 20, 0, tzinfo=timezone.utc)
RATES = {"ADAUSDT": -0.0001293, "ENJUSDT": 0.00003959,
         "LINKUSDT": -0.00000381}


def _history(rate, latest=None, n=12):
    latest = latest or (NOW - timedelta(hours=1))
    rows = []
    for i in range(n):
        ts = latest - timedelta(hours=8 * (n - 1 - i))
        rows.append((int(ts.timestamp() * 1000), rate))
    return rows


def _fetcher_ok(symbols):
    return {sym: _history(RATES[sym]) for sym in symbols}


def _fetcher_boom(symbols):
    raise RuntimeError("HTTP 503 for okx funding-rate-history")


def _mkroot():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _served(root=None):
    from desk3.producers import OkxFunding
    prod = OkxFunding(root or _mkroot(), fetcher=_fetcher_ok)
    return prod({"now": NOW})


class TestOkxProducerForm(unittest.TestCase):
    def test_serves_record_form_all_symbols(self):
        out = _served()
        self.assertEqual(out["funding_source"], "okx")
        self.assertEqual(set(out["funding"]), set(RATES))
        for sym, rate in RATES.items():
            rec = out["funding"][sym]
            self.assertIsInstance(rec, dict)
            self.assertAlmostEqual(rec["rate"], rate)

    def test_settled_and_received_stamps(self):
        out = _served()
        latest = NOW - timedelta(hours=1)
        for sym in RATES:
            rec = out["funding"][sym]
            self.assertEqual(rec["settled_at"], latest.isoformat())
            self.assertEqual(rec["received_at"], NOW.isoformat())

    def test_history_persisted_to_state(self):
        root = _mkroot()
        _served(root)
        path = os.path.join(root, "state", "okx_funding_history.json")
        doc = json.load(open(path))
        self.assertEqual(doc["source"], "okx")
        rows = doc["history"]["ADAUSDT"]
        self.assertEqual(len(rows), 12)
        self.assertAlmostEqual(rows[-1]["rate"], RATES["ADAUSDT"])

    def test_parse_okx_payload(self):
        from desk3.producers import parse_okx_funding_history
        payload = [
            {"fundingTime": "2000", "fundingRate": "0.0002"},
            {"fundingTime": "1000", "fundingRate": "0.0001"},
            {"fundingTime": "2000", "fundingRate": "0.0003"},
            {"fundingTime": "bad", "fundingRate": "0.1"},
            {"fundingRate": "0.1"},
        ]
        rows = parse_okx_funding_history(payload)
        self.assertEqual(rows, [(1000, 0.0001), (2000, 0.0003)])


class TestOkxFailClosed(unittest.TestCase):
    def test_fetch_failure_no_cache_serves_empty(self):
        from desk3.producers import OkxFunding
        prod = OkxFunding(_mkroot(), fetcher=_fetcher_boom)
        self.assertEqual(prod({"now": NOW}), {})
        self.assertTrue(prod.last_error)

    def test_stale_cache_not_served(self):
        from desk3.producers import OkxFunding
        root = _mkroot()
        doc = {"fetched_at": (NOW - timedelta(hours=4)).isoformat(),
               "source": "okx",
               "history": {s: [{"ts_ms": int((NOW - timedelta(
                   hours=5)).timestamp() * 1000), "rate": r}]
                   for s, r in RATES.items()}}
        with open(os.path.join(root, "state",
                               "okx_funding_history.json"), "w") as fh:
            json.dump(doc, fh)
        prod = OkxFunding(root, fetcher=_fetcher_boom)
        self.assertEqual(prod({"now": NOW}), {})

    def test_fresh_cache_served_on_fetch_failure(self):
        from desk3.producers import OkxFunding
        root = _mkroot()
        doc = {"fetched_at": (NOW - timedelta(minutes=30)).isoformat(),
               "source": "okx",
               "history": {s: [{"ts_ms": int((NOW - timedelta(
                   hours=1)).timestamp() * 1000), "rate": r}]
                   for s, r in RATES.items()}}
        with open(os.path.join(root, "state",
                               "okx_funding_history.json"), "w") as fh:
            json.dump(doc, fh)
        prod = OkxFunding(root, fetcher=_fetcher_boom)
        out = prod({"now": NOW})
        self.assertEqual(set(out["funding"]), set(RATES))
        self.assertAlmostEqual(out["funding"]["ADAUSDT"]["rate"],
                               RATES["ADAUSDT"])

    def test_stale_print_symbol_omitted(self):
        from desk3.producers import OkxFunding

        def fetch(symbols):
            out = {s: _history(RATES[s]) for s in symbols}
            out["LINKUSDT"] = _history(
                RATES["LINKUSDT"], latest=NOW - timedelta(hours=30))
            return out
        prod = OkxFunding(_mkroot(), fetcher=fetch)
        out = prod({"now": NOW})
        self.assertIn("ADAUSDT", out["funding"])
        self.assertNotIn("LINKUSDT", out["funding"])

    def test_partial_fetch_isolation(self):
        from desk3.producers import OkxFunding

        def fetch(symbols):
            return {s: _history(RATES[s])
                    for s in ("ADAUSDT", "LINKUSDT")}
        prod = OkxFunding(_mkroot(), fetcher=fetch)
        out = prod({"now": NOW})
        self.assertEqual(set(out["funding"]), {"ADAUSDT", "LINKUSDT"})


class TestEveryEngineReadsServedForm(unittest.TestCase):
    def setUp(self):
        self.view = {"funding": _served()["funding"]}

    def test_common_known_funding_rate(self):
        import aster_sleeves._common as C
        got = C.known_funding_rate(self.view, NOW, NOW)
        self.assertAlmostEqual(got, RATES["ADAUSDT"])

    def test_b11_funding(self):
        from desk3.aster_b11_crypto import _funding
        self.assertAlmostEqual(_funding(self.view, "LINKUSDT"),
                               RATES["LINKUSDT"])

    def test_aster_crypto_funding(self):
        from desk3.aster_crypto import _funding
        self.assertAlmostEqual(_funding(self.view, "ADAUSDT"),
                               RATES["ADAUSDT"])

    def test_batch7_funding(self):
        from desk3.aster_batch7 import _funding
        self.assertAlmostEqual(_funding(self.view, "ENJUSDT"),
                               RATES["ENJUSDT"])

    def test_batch13_funding_unwraps_record(self):
        from desk3.aster_batch13 import _funding
        got = _funding(self.view, "LINKUSDT")
        self.assertAlmostEqual(got, RATES["LINKUSDT"])

    def test_batch8_funding_unwraps_record(self):
        from desk3.aster_batch8 import _funding
        got = _funding(self.view)
        self.assertAlmostEqual(got, RATES["ENJUSDT"])

    def test_gate_distance_latest_rate(self):
        from desk3.gate_distance import _latest_rate
        self.assertAlmostEqual(_latest_rate(self.view, "ADAUSDT"),
                               RATES["ADAUSDT"])

    def test_scalar_still_read_by_unwrapped_readers(self):
        # The record cure must not break the scalar form the other
        # readers have always accepted (fixture compatibility).
        view = {"funding": {"LINKUSDT": -0.001}}
        from desk3.aster_batch13 import _funding as f13
        from desk3.aster_b11_crypto import _funding as f11
        self.assertAlmostEqual(f13(view, "LINKUSDT"), -0.001)
        self.assertAlmostEqual(f11(view, "LINKUSDT"), -0.001)


class TestWiring(unittest.TestCase):
    def test_register_all_wires_okx_funding(self):
        import desk3.producers as P

        class FakeDesk:
            def __init__(self):
                self.prods = {}

            def add_producer(self, name, fn, outputs, sla):
                self.prods[name] = (fn, list(outputs))
        desk = FakeDesk()
        P.register_all(desk, _mkroot(), env={})
        fund = [(n, fn) for n, (fn, outs) in desk.prods.items()
                if "funding" in outs]
        self.assertEqual(len(fund), 1)
        name, fn = fund[0]
        self.assertEqual(name, "okx_funding")
        fn.fetcher = _fetcher_ok
        out = fn({"now": NOW})
        self.assertIsInstance(out["funding"]["ADAUSDT"], dict)


class TestVariationsRegistered(unittest.TestCase):
    def setUp(self):
        path = os.path.join(ROOT, "config",
                            "f4_variations_20261115.json")
        self.doc = json.load(open(path))
        self.by_id = {v["id"]: v for v in self.doc["variations"]}

    def test_three_varsg_entries_beside_the_sixteen(self):
        self.assertEqual(len(self.doc["variations"]), 19)
        self.assertIn("_varsg", self.doc["suffix_scheme"])
        for vid in (
                "aster_r19_linkusdt_absorption_negative_funding_"
                "fixed16_fullcash_varsg",
                "aster_r19_linkusdt_absorption_negative_funding_"
                "fixed16_volume1pct_varsg",
                "aster_abs_neg_ada_vol1pct_varsg"):
            self.assertIn(vid, self.by_id)
            self.assertEqual(self.by_id[vid]["operator"],
                             "SIGN_GATE_DROP")

    def test_link_replay_counts(self):
        v = self.by_id["aster_r19_linkusdt_absorption_negative_"
                       "funding_fixed16_fullcash_varsg"]
        self.assertEqual(v["parent"], "aster_r19_linkusdt_absorption"
                                      "_negative_funding_fixed16_fullcash")
        self.assertEqual(v["replay"]["variation_entries_revealed"], 10)
        self.assertEqual(v["replay"]["parent_entries"], 2)
        self.assertAlmostEqual(
            v["replay"]["grades_bp"]["fwd5_excess_vs_qqq"], 351.6)

    def test_ada_replay_counts(self):
        v = self.by_id["aster_abs_neg_ada_vol1pct_varsg"]
        self.assertEqual(v["parent"], "aster_abs_neg_ada_vol1pct")
        self.assertEqual(v["replay"]["variation_entries_revealed"], 3)
        self.assertAlmostEqual(
            v["replay"]["grades_bp"]["fwd3_excess_vs_qqq"], 588.9)

    def test_uniform_falsifier_and_parents_untouched(self):
        for vid, v in self.by_id.items():
            if vid.endswith("_varsg"):
                self.assertTrue(v["falsifier"].startswith(
                    "Retire if, over its first 20 resolved forward "
                    "fires"))
        cfg = json.load(open(os.path.join(ROOT, "config",
                                          "sleeves.json")))
        rows = cfg["sleeves"] if isinstance(cfg, dict) else cfg
        if isinstance(rows, dict):
            rows = list(rows.values())
        ids = {r["id"] for r in rows}
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # (2026-11-15): 339 + the 19 F4 variations rostered as
        # first-class sleeves (BUGLOG_2026-11-15.md).
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(ids), 400)
        for vid in self.by_id:
            if vid.endswith("_varsg"):
                # VARIATION-ROSTERING-20261115: rostered now; the
                # pre-rostering absence assertion is superseded.
                self.assertIn(vid, ids)


if __name__ == "__main__":
    unittest.main()
