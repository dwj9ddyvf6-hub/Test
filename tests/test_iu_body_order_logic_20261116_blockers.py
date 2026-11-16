"""IU-BODY-ORDER-LOGIC-20261116 blockers (Mon 2026-11-16 total audit).

Defect: fwd_alpaca_enj_iu_body could never fire. Its byte-pinned
vendored strategy (desk3/vendor/sleeves/fwd_alpaca_enj_iu_body.py,
sha256 171f5f79..., pinned by tests/test_port_batch4_blockers.py)
returns [] from signal() by source design — the v2 source it
preserves (PUBLIC_IU_BODY_SPOT100) carried no order logic — so the
sleeve sat in the dispatcher's ENJ paper class with no intent ever
existing for the class to fill.

Cure (this landing): desk3/iu_body.py, a faithful desk-side
implementation of the order logic the escalations lane found in
the estate archive — strategies/public_recipes/
public_source_sleeves.py ::source_features + ::step for 'iu_body'
(sha256 e64c995d..., the value backend/public_recipe_runtime.py::
load_core pins), under that runtime's overlay (ENJUSDT 5m bars,
book PUBLIC_IU_BODY_SPOT100 spot equity_percent 100, spot
long-only, entry TTL 300s, bar max decision lag 300s, quote max
age 10s) — wired to the desk per the coordinator's decisions:
kraken_paper venue (the sleeve was already registered in
ENJ_PAPER_SLEEVES by 8096eed), the served Kraken ENJ 1-minute tape
resampled to the source's 5-minute bars, the standard $10,000
slice (the source book's 100%-of-its-own-book maps to the slice).
The roster row keeps its id, points at
adapters3.fwd_alpaca_enj_iu_body, and moves rth -> 24h. The
vendored file is untouched.

The logic pinned here, from the source and nowhere else:
- bodies |close-open|; baseline = sum of last 21 bodies / 20
  (needs >= 21 bars); strong = last body > 4.0 * baseline;
  long/short signals by close vs open; ATR14 Wilder RMA.
- flat + long_signal -> entry (source_body_impulse); flat +
  short_signal -> NO entry (spot long-only overlay, named).
- held long: trailing stop = max(prior, close - 2*ATR14),
  initialized at avg entry - 2*ATR14, never loosens.
- exit ONLY on the observed quote trigger (bid <= stop, quote
  strictly after the stop became active, quote age <= 10s).
  NO opposite-body exit and NO bar-low exit — the desk sibling
  desk3/aster_b4.py::evaluate_enj_iu_body has both; they are its
  divergences and are pinned ABSENT here.

Fidelity to the archive reducer itself is proven separately by
desk3/iu_body_fidelity_check.py -> desk3/iu_body_fidelity_result.json
(457 steps compared, 0 divergences, incl. the recorded Kraken
tape); the archive-dependent test below re-runs that drive when
the archive is present on this box and skips by name when it is
not — the published result file is the standing evidence.

Fail direction: on the pre-cure tree the roster module is the
port-batch4 adapter delegating to the vendored [] strategy, the
engine/adapter/fidelity files do not exist, and every evaluate
test returns [] — the entry, exit and wiring tests fail there.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
UTC = timezone.utc
BASE = datetime(2026, 11, 16, 0, 0, tzinfo=UTC)
SID = "fwd_alpaca_enj_iu_body"
ARCHIVE = os.path.expanduser(
    "~/workspace/.scratch-ausar-archive/handoff-20261024/source/"
    "strategies/public_recipes/public_source_sleeves.py")


def _iso(ep):
    return datetime.fromtimestamp(ep, UTC).isoformat()


def expand_1min(bars5):
    """Each (o,h,l,c) 5-minute bar -> five 1-minute desk rows whose
    desk resample is exactly that bar."""
    rows = []
    for i, (o, h, l, c) in enumerate(bars5):
        start = BASE.timestamp() + 300 * i
        mins = [(o, h, l, o), (o, o, o, o), (o, o, o, o),
                (o, o, o, o), (c, c, c, c)]
        for j, (mo, mh, ml, mc) in enumerate(mins):
            rows.append({"t": _iso(start + 60 * j), "o": mo, "h": mh,
                         "l": ml, "c": mc, "v": 200.0})
    return rows


def quiet(n, o=100.0, c=100.1):
    return [(o, max(o, c) + 0.3, min(o, c) - 0.4, c)] * n


def view(bars5, bid=None, ask=None, quote_age_s=1.0, lag_s=3.0,
         positions=None, cash=10000.0):
    last_close = BASE.timestamp() + 300 * len(bars5)
    gen = last_close + lag_s
    v = {"bars": {"ENJ/USD|1Min": expand_1min(bars5)},
         "positions": positions or [],
         "slice": {"cash_usd": cash},
         "kraken": {"generated_at": _iso(gen)}}
    if bid is not None:
        qa = gen - quote_age_s
        v["kraken.book"] = {"bids": [[str(bid), "1000000", qa]],
                            "asks": [[str(ask), "1000000", qa]]}
    return v


def entry_bars():
    return quiet(26) + [(100.0, 103.2, 99.9, 103.0)]


def held_view(extra_bars, bid, quote_age_s=1.0):
    bars = entry_bars() + extra_bars
    fill_ep = BASE.timestamp() + 300 * 27 + 3
    pos = [{"symbol": "ENJUSDT", "qty": 96, "avg_price": 103.1,
            "opened_at": _iso(fill_ep), "sleeve_id": SID}]
    return view(bars, bid=bid, ask=bid + 0.2, quote_age_s=quote_age_s,
                positions=pos)


HELD = [(103.1, 104.4, 102.7, 104.0), (104.0, 106.4, 103.6, 106.0),
        (106.0, 106.4, 104.6, 105.0), (105.0, 105.4, 104.1, 104.5)]


def archive_stop():
    """The trailing stop after HELD, from the archive reducer's own
    arithmetic via the engine's reconstruction (proven identical to
    the archive in the fidelity drive)."""
    from desk3.iu_body import resample_1min_to_5min, reconstruct_stop
    bars = resample_1min_to_5min(expand_1min(entry_bars() + HELD))
    fill_ep = BASE.timestamp() + 300 * 27 + 3
    stop, _af = reconstruct_stop(bars, 103.1, fill_ep, "long")
    return stop


class TestRosterAndPins(unittest.TestCase):
    def test_vendored_file_byte_identical(self):
        p = os.path.join(ROOT, "desk3", "vendor", "sleeves",
                         "fwd_alpaca_enj_iu_body.py")
        self.assertEqual(
            hashlib.sha256(open(p, "rb").read()).hexdigest(),
            "171f5f79f1ae9a3d799a7408bc1f786c4309a16ed39e41627bf3d133d9ad9b6a")

    def test_roster_row_points_at_new_implementation(self):
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]
        hits = [r for r in rows if r["id"] == SID]
        self.assertEqual(len(hits), 1)
        r = hits[0]
        self.assertEqual(r["module"], "adapters3.fwd_alpaca_enj_iu_body")
        self.assertEqual(r["session"], "24h")
        self.assertEqual(r["cadence_s"], 300)
        self.assertTrue(r["own_book_view"])
        self.assertIn("IU-BODY-ORDER-LOGIC-20261116",
                      r["params"]["parked_reason"])
        self.assertIn("ENJ-PAPER-20261116", r["params"]["parked_reason"])
        self.assertEqual(r["slice"]["capital_usd"], 10000.0)
        import importlib
        mod = importlib.import_module(r["module"])
        self.assertEqual(tuple(mod.INPUTS), tuple(r["inputs"]))

    def test_in_enj_paper_class(self):
        from desk3.dispatcher import ENJ_PAPER_SLEEVES, _enj_paper_class
        self.assertIn(SID, ENJ_PAPER_SLEEVES)
        self.assertTrue(_enj_paper_class(SID, "ENJ/USD"))

    def test_fidelity_result_published_and_clean(self):
        res = json.load(open(os.path.join(
            ROOT, "desk3", "iu_body_fidelity_result.json")))
        self.assertEqual(res["verdict"], "MATCH")
        self.assertEqual(res["total_divergences"], 0)
        self.assertGreaterEqual(res["total_steps_compared"], 400)
        self.assertEqual(res["archive_source_sha256"],
                         "e64c995dd451ac0fd0a32f8a1bcc22624a76362c"
                         "58d607ee9edecc2d99722e6b")


class TestFeatures(unittest.TestCase):
    def test_baseline_inclusive21_div20(self):
        from desk3.iu_body import source_features
        bars = [{"open": 100.0, "high": 100.4, "low": 99.6,
                 "close": 100.1, "volume": 1.0}] * 20
        bars = bars + [{"open": 100.0, "high": 103.2, "low": 99.9,
                        "close": 103.0, "volume": 1.0}]
        f = source_features(bars)
        self.assertAlmostEqual(f["body_baseline"], (20 * 0.1 + 3.0) / 20)
        self.assertTrue(f["long_signal"])
        self.assertFalse(f["short_signal"])

    def test_warmup_no_baseline(self):
        from desk3.iu_body import source_features
        bars = [{"open": 100.0, "high": 110.0, "low": 99.0,
                 "close": 109.0, "volume": 1.0}] * 20
        f = source_features(bars)
        self.assertIsNone(f["body_baseline"])
        self.assertFalse(f["long_signal"])


class TestEvaluate(unittest.TestCase):
    def setUp(self):
        from adapters3.fwd_alpaca_enj_iu_body import evaluate
        self.evaluate = evaluate

    def test_entry_on_body_impulse(self):
        out = self.evaluate(view(entry_bars(), bid=102.9, ask=103.1), {})
        self.assertEqual(len(out), 1, out)
        it = out[0]
        self.assertEqual(it["kind"], "entry")
        self.assertEqual(it["symbol"], "ENJ/USD")
        self.assertEqual(it["side"], "buy")
        self.assertEqual(it["position_intent"], "buy_to_open")
        self.assertEqual(it["qty"], 96)  # int(10000 / 103.1), slice-sized
        self.assertAlmostEqual(it["price_hint"], 103.1)
        self.assertIn("source_body_impulse", it["reason"])

    def test_warmup_no_entry(self):
        bars = quiet(19) + [(100.0, 103.2, 99.9, 103.0)]
        self.assertEqual(self.evaluate(
            view(bars, bid=102.9, ask=103.1), {}), [])

    def test_short_signal_no_entry_long_only(self):
        bars = quiet(26) + [(103.0, 103.2, 99.8, 100.0)]
        self.assertEqual(self.evaluate(
            view(bars, bid=99.9, ask=100.1), {}), [])

    def test_stale_bar_no_entry(self):
        out = self.evaluate(view(entry_bars(), bid=102.9, ask=103.1,
                                 lag_s=301.0), {})
        self.assertEqual(out, [])

    def test_no_reentry_while_held(self):
        out = self.evaluate(held_view([], bid=102.9), {})
        self.assertEqual(out, [])

    def test_held_bid_above_stop_no_exit(self):
        stop = archive_stop()
        self.assertIsNotNone(stop)
        out = self.evaluate(held_view(HELD, bid=stop + 0.05), {})
        self.assertEqual(out, [])

    def test_bar_low_pierce_without_quote_trigger_no_exit(self):
        stop = archive_stop()
        bars = HELD + [(104.5, 105.0, stop - 0.5, 104.8)]
        out = self.evaluate(held_view(bars, bid=stop + 0.05), {})
        self.assertEqual(out, [], "bar-low exit is the sibling's divergence")

    def test_opposite_body_no_exit(self):
        stop = archive_stop()
        bars = HELD + [(104.5, 104.9, 100.0, 100.2)]  # huge bearish body
        out = self.evaluate(held_view(bars, bid=stop + 0.05), {})
        self.assertEqual(out, [], "opposite-body exit does not exist in source")

    def test_quote_trigger_exit(self):
        stop = archive_stop()
        out = self.evaluate(held_view(HELD, bid=stop - 0.01), {})
        self.assertEqual(len(out), 1, out)
        it = out[0]
        self.assertEqual(it["kind"], "exit")
        self.assertEqual(it["side"], "sell")
        self.assertEqual(it["position_intent"], "sell_to_close")
        self.assertEqual(it["qty"], 96)
        self.assertIn("observed_quote_stop_trigger", it["reason"])

    def test_stale_quote_no_exit(self):
        stop = archive_stop()
        out = self.evaluate(held_view(HELD, bid=stop - 0.01,
                                      quote_age_s=11.0), {})
        self.assertEqual(out, [])

    def test_stop_ratchet_never_loosens(self):
        from desk3.iu_body import resample_1min_to_5min, reconstruct_stop
        fill_ep = BASE.timestamp() + 300 * 27 + 3
        bars = resample_1min_to_5min(expand_1min(entry_bars() + HELD))
        s1, _ = reconstruct_stop(bars[:29], 103.1, fill_ep, "long")
        s2, _ = reconstruct_stop(bars[:30], 103.1, fill_ep, "long")
        s3, _ = reconstruct_stop(bars[:31], 103.1, fill_ep, "long")
        self.assertIsNotNone(s1)
        self.assertGreaterEqual(s2, s1)
        self.assertGreaterEqual(s3, s2)


class TestResample(unittest.TestCase):
    def test_complete_buckets_only(self):
        from desk3.iu_body import resample_1min_to_5min
        rows = expand_1min(quiet(3))
        rows = rows[:-2]  # trailing partial bucket (3 of 5 minutes)
        out = resample_1min_to_5min(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["open"], 100.0)
        self.assertEqual(out[0]["close"], 100.1)


class TestWiring(unittest.TestCase):
    def test_entry_intent_paper_fills_at_dispatcher(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        from adapters3.fwd_alpaca_enj_iu_body import evaluate

        class LiveBookFake(FakeBroker):
            live_book = True

        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = Dispatcher(tmp, broker,
                       slices={SID: {"capital_usd": 10000,
                                     "cash_usd": 10000}},
                       price_lookup=lambda s: None)
        out = evaluate(view(entry_bars(), bid=102.9, ask=103.1), {})
        self.assertEqual(len(out), 1)
        r = d.process_intent(out[0], SID)
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["venue"], "kraken_paper")
        self.assertEqual(broker.submit_count, 0)
        path = os.path.join(tmp, "state", "dispatcher.jsonl")
        rows = [json.loads(l) for l in open(path)]
        fills = [x for x in rows if x.get("event") == "fill"]
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["venue"], "kraken_paper")
        self.assertEqual(fills[0]["sleeve"], SID)


class TestArchiveFidelity(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(ARCHIVE),
                         "estate archive not present on this box; the "
                         "published fidelity result file is the evidence")
    def test_drive_matches_archive_reducer(self):
        out = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "desk3", "iu_body_fidelity_check.py"),
             "--output", os.path.join(tempfile.mkdtemp(), "r.json")],
            capture_output=True, text=True, timeout=600)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn('"divergences": 0', out.stdout)


if __name__ == "__main__":
    unittest.main()
