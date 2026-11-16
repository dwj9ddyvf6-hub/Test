"""PF-PAIRED-RV-20261116 blockers (MAKE-IT-WORK Decision C; owner
ruling 2026-11-16 12:46 ET: "Make it work").

Defect: the four short-side PF spot variations
(free_kraken_ada_breakdown_varspot, free_kraken_link_breakdown_varspot,
free_kraken_ada_crowded_varspot, free_kraken_link_crowded_varspot)
computed their parent signals unchanged on the served ADA/USD and
LINK/USD spot 4h tapes, but the side is short and Alpaca serves no
crypto spot shorting, so an entry_ready decision recorded a named
no-trade (spot_decision status named_no_trade_short_side) and the
sleeves never traded.

Cure: the paired relative-value expression the escalation record
named as the standing alternative. On entry_ready the sleeve goes
LONG BTC/USD spot (Alpaca-listed, the desk's existing route),
sized by its own slice (fractional qty = slice cash net of the
per-side fee over the BTC price; the dispatcher's normal slice
check still gates the intent), at the same due time, held for the
parent's 16h hold clock, then exits the full held BTC quantity.
Grading is on the spread: BTC return minus the signal asset's
return over the same window, net of the desk's crypto fee
convention -- 10bp per side on the traded BTC leg
(desk3/aster_crypto.py FEE=0.001; desk3/t474u_crypto.py
FEE_1X_CRYPTO=0.001; aster_sleeves/_common.py FEE =
Decimal("0.001"), "10 bps each side (crypto_rules.json)").
A stale/missing BTC tape or an empty slice fails closed with a
named abstention; no signal = flat, zero intents. The signal
computations are not edited (the parent-decision equality pin
below), and the pure-short form stays in the registry records as
the named future-venue form.

Fail direction: on the pre-cure tree (c7aea75) spot_decision maps
entry_ready to named_no_trade_short_side, signal() never emits an
intent, spread_grade / paired_qty do not exist, the registry
carries no Decision C amendment and warm serves no BTC/USD 4Hour
fetch, so the behavior/registry/warm tests fail; the parent-file
sha pins pass on both trees by design.
"""
import hashlib
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 11, 16, 16, 0, tzinfo=timezone.utc)
FOUR = ["free_kraken_ada_breakdown_varspot",
        "free_kraken_link_breakdown_varspot",
        "free_kraken_ada_crowded_varspot",
        "free_kraken_link_crowded_varspot"]
STRAT = {"free_kraken_ada_breakdown_varspot":
         ("sleeves.free_kraken_ada_breakdown_varspot",
          "sleeves.free_kraken_ada_breakdown", "ADA/USD", 1.0, False),
         "free_kraken_link_breakdown_varspot":
         ("desk3.strategies.free_kraken_link_breakdown_varspot",
          "desk3.strategies.free_kraken_link_breakdown", "LINK/USD",
          9.0, False),
         "free_kraken_ada_crowded_varspot":
         ("sleeves.free_kraken_ada_crowded_varspot",
          "sleeves.free_kraken_ada_crowded", "ADA/USD", 1.0, True),
         "free_kraken_link_crowded_varspot":
         ("desk3.strategies.free_kraken_link_crowded_varspot",
          "desk3.strategies.free_kraken_link_crowded", "LINK/USD",
          9.0, True)}
PARENT_FILE_SHA256 = {
    "sleeves/free_kraken_ada_breakdown.py":
    "a244bf67fa547e4424347e8990fe3ec2b3fea38b8a00b59d9dc1604a31126c4f",
    # Pin re-struck at the MAKE-IT-WORK final merge (2026-11-16):
    # TOTAL-AUDIT-PIN-REBASE-20261116 (5)+(6) removed the
    # CONSTANTS-PROVENANCE in-file marks from this file on main,
    # restoring its original bytes; Decision C never touched it.
    "sleeves/free_kraken_ada_crowded.py":
    "85b5ebea605d7182cab6ec8b55425a749e2464b6f82ce2387373f4e284b2f777",
    "adapters/free_kraken_ada_breakdown.py":
    "f64a45d7e7bac91253f189fecb0d6b1967d5566fa8333b5260470366a92d5b23",
    "adapters/free_kraken_ada_crowded.py":
    "348a266a399b7cebcaecd947348ecdb2dc3148ca6fdc0eb08a9e32e573e71538",
    "adapters3/free_kraken_ada_breakdown.py":
    "774eb2ccf27a76e378e6dd07d543a9367f47f8a8f85ee8d7e8ca5b97fe037c0e",
    "adapters3/free_kraken_ada_crowded.py":
    "110693333739b7a798b5664479e52082a066d22a1d54bddd183356163347a7b8",
    "desk3/strategies/free_kraken_link_breakdown.py":
    "be427ed66b7b8534f015d5f2e1e3673c4a820771cd6da80d1fbd84ccb4facef9",
    # Pin re-struck at the MAKE-IT-WORK final merge (2026-11-16):
    # same TOTAL-AUDIT-PIN-REBASE-20261116 (5)+(6) restoration as
    # the ADA crowded parent above; Decision C never touched it.
    "desk3/strategies/free_kraken_link_crowded.py":
    "c9b22591486a66c0ee2ea09ce22d95bc9450f08a06ba2d23f9a12c2ab09cbf1f",
    "desk3/sleeves/free_kraken_link_breakdown.py":
    "41c2f24f96f95e75ed6b453cda4edb3d411068074852830a54278706b99e279d",
    "desk3/sleeves/free_kraken_link_crowded.py":
    "709b83aa0c378080b7dec7ed42a4d3b7d8e22eb990ccd2f137fd9b3110148d23"}


def _ctx(extra, now=NOW, equity=10000.0):
    from desk3.contract import Context
    return Context(now=now.timestamp(), session="2026-11-16",
                   equity=equity, extra=extra)


def _sig_bars(price, signal_close=0.9, n=30, now=NOW):
    """Spot bars whose newest due signal bar closes below the
    prior 20 lows (all 0.99 x price): a textbook parent breakdown.
    The signal bar opens 12h before `now`; its entry due time is
    4h before `now`."""
    bars = []
    t0 = now - timedelta(hours=4 * (n + 2))
    for i in range(n):
        close = price if i < n - 1 else signal_close * price
        bars.append({"t": (t0 + timedelta(hours=4 * i)).timestamp(),
                     "o": price, "h": price * 1.01, "l": price * 0.99,
                     "c": close, "v": 10.0})
    return bars


def _btc_bars(price, newest_open, n=6):
    bars = []
    for i in range(n):
        t = newest_open - timedelta(hours=4 * (n - 1 - i))
        bars.append({"t": t.timestamp(), "o": price, "h": price,
                     "l": price, "c": price, "v": 10.0})
    return bars


def _funding(now=NOW, latest=0.001):
    out = []
    for i in range(40):
        ts = now - timedelta(hours=40 - i)
        out.append({"timestamp": ts.isoformat(),
                    "fundingRate": latest if i == 39 else 0.0001})
    return out


def _close_at(bars, when):
    """Close of the last bar completed at or before `when`."""
    best = None
    for b in bars:
        if b["t"] + 4 * 3600 <= when.timestamp():
            if best is None or b["t"] > best["t"]:
                best = b
    return best["c"] if best else None


class TestPairedExpressionFixture(unittest.TestCase):
    """Per variation: signal fires -> exactly one paired BTC entry
    (slice-sized) at the due time -> 16h window elapses -> exit
    intent selling the full held BTC quantity -> spread grade on
    the fixture tapes equals the hand-computed spread.

    Fixture moves: BTC/USD 100.00 -> 110.00 (+10.00%); signal asset
    entry price -> -20.00% over the same window (ADA 1.00 -> 0.80;
    LINK 9.00 -> 7.20 in price terms, graded via the normalized
    10.00 -> 8.00 pair below so all four share one arithmetic).
    Hand-computed spread: gross = 0.10 - (-0.20) = 0.30; fees =
    2 x 0.001 (10bp per side, traded BTC leg round trip) = 0.002;
    net = 0.298.
    """

    def _drive(self, vid):
        smod_name, pmod_name, symbol, price, crowded = STRAT[vid]
        smod = importlib.import_module(smod_name)
        pmod = importlib.import_module(pmod_name)
        sig = _sig_bars(price)
        btc_entry = _btc_bars(100.0, NOW - timedelta(hours=4))
        bars = {symbol: sig, "BTC/USD": btc_entry}
        extra = {"funding_rates": _funding()} if crowded else {}
        # --- signal integrity: parent decision fields unchanged ---
        rows = pmod.normalize(sig)
        if crowded:
            parent_dec = pmod.crowded_decision(
                rows, _funding(), NOW, instrument=symbol,
                freshness_gate=True)
            dec = smod.spot_decision(rows, _funding(), NOW)
        else:
            parent_dec = pmod.breakdown_decision(
                rows, NOW, instrument=symbol)
            dec = smod.spot_decision(rows, NOW)
        self.assertEqual(parent_dec["status"], "entry_ready", vid)
        self.assertEqual(dec["status"], "paired_rv_entry_ready", vid)
        for k in ("signal_event_id", "entry_due_at", "prior_20_low",
                  "signal_open_at", "signal_close_at", "signal_close"):
            self.assertEqual(dec[k], parent_dec[k], (vid, k))
        entry_due = datetime.fromisoformat(dec["entry_due_at"])
        # --- entry: exactly one paired BTC buy, slice-sized ---
        intents = smod.signal(bars, {}, _ctx(dict(extra)))
        self.assertEqual(len(intents), 1, (vid, intents))
        it = intents[0]
        self.assertEqual((it.kind, it.symbol), ("enter", "BTC/USD"), vid)
        self.assertEqual(it.side, "buy", vid)
        self.assertEqual(it.position_intent, "buy_to_open", vid)
        # qty = slice cash 10000 x (1 - 0.001 fee) / BTC price 100
        self.assertAlmostEqual(it.qty, 99.9, places=9, msg=vid)
        self.assertAlmostEqual(it.price_hint, 100.0, places=9, msg=vid)
        # --- mid-hold: position open, clock not elapsed -> flat ---
        exit_due = entry_due + timedelta(hours=16)
        state = {"BTC/USD": {"qty": 99.9,
                             "entry_due_at": entry_due.isoformat()}}
        mid_extra = dict(extra)
        mid_extra["sleeve_state"] = state
        self.assertEqual(
            smod.signal(bars, {}, _ctx(mid_extra, now=NOW)), [], vid)
        # --- exit: window elapsed -> sell the full held quantity ---
        btc_exit = _btc_bars(110.0, exit_due - timedelta(hours=4))
        exit_bars = {symbol: sig, "BTC/USD": btc_exit}
        exit_extra = dict(extra)
        exit_extra["sleeve_state"] = state
        intents = smod.signal(exit_bars, {}, _ctx(exit_extra,
                                                  now=exit_due))
        self.assertEqual(len(intents), 1, (vid, intents))
        xt = intents[0]
        self.assertEqual((xt.kind, xt.symbol), ("exit", "BTC/USD"), vid)
        self.assertEqual(xt.side, "sell", vid)
        self.assertEqual(xt.position_intent, "sell_to_close", vid)
        self.assertAlmostEqual(xt.qty, 99.9, places=9, msg=vid)
        self.assertAlmostEqual(xt.price_hint, 110.0, places=9, msg=vid)
        # --- spread grade on the fixture tapes ---
        g_btc = [_btc_bars(100.0, entry_due - timedelta(hours=4))[-1],
                 _btc_bars(110.0, exit_due - timedelta(hours=4))[-1]]
        g_sig = [{"t": (entry_due - timedelta(hours=8)).timestamp(),
                  "c": 10.0},
                 {"t": (exit_due - timedelta(hours=8)).timestamp(),
                  "c": 8.0}]
        grade = smod.spread_grade(
            _close_at(g_btc, entry_due), _close_at(g_btc, exit_due),
            _close_at(g_sig, entry_due), _close_at(g_sig, exit_due))
        self.assertAlmostEqual(grade["btc_return"], 0.10, places=9,
                               msg=vid)
        self.assertAlmostEqual(grade["signal_return"], -0.20, places=9,
                               msg=vid)
        self.assertAlmostEqual(grade["gross_spread"], 0.30, places=9,
                               msg=vid)
        self.assertAlmostEqual(grade["round_trip_fees"], 0.002,
                               places=9, msg=vid)
        self.assertAlmostEqual(grade["net_spread"], 0.298, places=9,
                               msg=vid)

    def test_ada_breakdown_varspot(self):
        self._drive("free_kraken_ada_breakdown_varspot")

    def test_link_breakdown_varspot(self):
        self._drive("free_kraken_link_breakdown_varspot")

    def test_ada_crowded_varspot(self):
        self._drive("free_kraken_ada_crowded_varspot")

    def test_link_crowded_varspot(self):
        self._drive("free_kraken_link_crowded_varspot")


class TestControls(unittest.TestCase):
    def _check(self, vid):
        smod_name, pmod_name, symbol, price, crowded = STRAT[vid]
        smod = importlib.import_module(smod_name)
        btc = _btc_bars(100.0, NOW - timedelta(hours=4))

        def base_extra():
            return {"funding_rates": _funding()} if crowded else {}
        # No signal (flat tape) -> zero intents, no abstention.
        flat = [dict(b, c=price) for b in _sig_bars(price)]
        extra = base_extra()
        self.assertEqual(
            smod.signal({symbol: flat, "BTC/USD": btc}, {},
                        _ctx(extra)), [], vid)
        self.assertNotIn("paired_rv_abstentions", extra, vid)
        # Signal fires + anchor tape stale (newest bar opened 12h
        # before now, beyond the two-bar freshness discipline) ->
        # named abstention, zero intents.
        stale = _btc_bars(100.0, NOW - timedelta(hours=12))
        extra = base_extra()
        self.assertEqual(
            smod.signal({symbol: _sig_bars(price), "BTC/USD": stale},
                        {}, _ctx(extra)), [], vid)
        abst = extra.get("paired_rv_abstentions") or []
        self.assertEqual(len(abst), 1, vid)
        self.assertEqual(abst[0]["status"],
                         "named_abstention_anchor_stale", vid)
        # Signal fires + anchor tape missing entirely -> same.
        extra = base_extra()
        self.assertEqual(
            smod.signal({symbol: _sig_bars(price)}, {}, _ctx(extra)),
            [], vid)
        abst = extra.get("paired_rv_abstentions") or []
        self.assertEqual(len(abst), 1, vid)
        self.assertEqual(abst[0]["status"],
                         "named_abstention_anchor_stale", vid)

    def test_all_four_controls(self):
        for vid in FOUR:
            self._check(vid)


class TestDispatcherSliceSeam(unittest.TestCase):
    def test_entry_fills_inside_slice_and_refuses_outside_it(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher

        class LiveBookFake(FakeBroker):
            live_book = True

        intent = {"intent_id": "rv1", "kind": "entry",
                  "symbol": "BTC/USD", "side": "buy", "qty": 99.9,
                  "order_type": "market", "time_in_force": "gtc",
                  "price_hint": 100.0,
                  "position_intent": "buy_to_open"}
        broker = LiveBookFake(prices={"BTC/USD": 100.0})
        d = Dispatcher(tempfile.mkdtemp(), broker,
                       slices={FOUR[0]: {"capital_usd": 10000,
                                         "cash_usd": 10000}},
                       price_lookup=lambda s: 100.0)
        r = d.process_intent(dict(intent), FOUR[0])
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)
        broker2 = LiveBookFake(prices={"BTC/USD": 100.0})
        d2 = Dispatcher(tempfile.mkdtemp(), broker2,
                        slices={FOUR[0]: {"capital_usd": 10000,
                                          "cash_usd": 5000}},
                        price_lookup=lambda s: 100.0)
        r2 = d2.process_intent(dict(intent, intent_id="rv2"), FOUR[0])
        self.assertEqual(r2["status"], "rejected", r2)
        self.assertEqual(r2["reason"], "insufficient_slice_bp", r2)
        self.assertEqual(broker2.submit_count, 0)


class TestAdapterPaths(unittest.TestCase):
    def _view(self, symbol, price, crowded):
        sig = [{"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"],
                "c": b["c"], "v": b["v"]} for b in _sig_bars(price)]
        for b in sig:
            b["t"] = datetime.fromtimestamp(b["t"],
                                            tz=timezone.utc).isoformat()
        btc = [{"t": datetime.fromtimestamp(b["t"], tz=timezone.utc)
                .isoformat(), "o": b["o"], "h": b["h"], "l": b["l"],
                "c": b["c"], "v": b["v"]}
               for b in _btc_bars(100.0, NOW - timedelta(hours=4))]
        view = {"now": NOW.isoformat(), "positions": [], "extra": {},
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "kraken_inputs": {}, "kraken": {}, "kraken.funding": {}}
        if symbol == "ADA/USD":
            view["bars"] = {"ADA/USD|240Min": sig, "BTC/USD|240Min": btc}
            if crowded:
                view["kraken.funding"] = {"PF_ADAUSD": _funding()}
        else:
            view["bars"] = {"LINK/USD|4Hour": sig, "BTC/USD|4Hour": btc}
            if crowded:
                view["kraken.funding"] = {"PF_LINKUSD": _funding()}
        return view

    def _check(self, vid, module):
        smod_name, pmod_name, symbol, price, crowded = STRAT[vid]
        mod = importlib.import_module(module)
        out = mod.evaluate(self._view(symbol, price, crowded),
                           {"sleeve_id": mod.SLEEVE_ID,
                            "state_dir": tempfile.mkdtemp()})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1, (vid, out))
        self.assertEqual(entries[0]["symbol"], "BTC/USD", vid)
        self.assertEqual(entries[0]["side"], "buy", vid)
        self.assertAlmostEqual(entries[0]["qty"], 99.9, places=9,
                               msg=vid)
        # Adapter INPUTS vs config row inputs pin (LINK desk3
        # adapters): the BTC tape rides the "bars" producer, so
        # both stay as registered.
        rows = {r["id"]: r for r in json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]}
        if hasattr(mod, "INPUTS"):
            self.assertEqual(tuple(rows[vid]["inputs"]), mod.INPUTS,
                             vid)
        self.assertIn("bars", rows[vid]["inputs"], vid)

    def test_all_four_adapters(self):
        self._check("free_kraken_ada_breakdown_varspot",
                    "adapters3.free_kraken_ada_breakdown_varspot")
        self._check("free_kraken_ada_crowded_varspot",
                    "adapters3.free_kraken_ada_crowded_varspot")
        self._check("free_kraken_link_breakdown_varspot",
                    "desk3.sleeves.free_kraken_link_breakdown_varspot")
        self._check("free_kraken_link_crowded_varspot",
                    "desk3.sleeves.free_kraken_link_crowded_varspot")


class TestRegistrationAndPins(unittest.TestCase):
    def test_registry_amendment_and_future_venue_form_retained(self):
        reg = json.load(open(os.path.join(
            ROOT, "config", "pf_spot_variations_20261116.json")))
        by_id = {v["id"]: v for v in reg["variations"]}
        self.assertEqual(len(by_id), 6)
        for vid in FOUR:
            v = by_id[vid]
            self.assertIn("PF-PAIRED-RV-20261116", v["form"], vid)
            self.assertIn("paired relative-value", v["form"].lower(),
                          vid)
            self.assertIn("future-venue form", v["form"], vid)
            # The pure-short form's own words are retained, not
            # deleted.
            self.assertIn("named no-trade", v["form"], vid)
            self.assertIn("40 registered signal events",
                          v["falsifier"], vid)
            self.assertIn("spread", v["falsifier"], vid)
            self.assertIn("killed, not loosened",
                          v["falsifier"].lower(), vid)
            self.assertIn("BTC/USD", v["grade_path"], vid)
            self.assertIn("dispatcher record", v["grade_path"], vid)
            self.assertIn("PF-PAIRED-RV-20261116", v["status"], vid)
        # The two basis variations' records stay byte-untouched in
        # substance: no Decision C amendment on them.
        for vid in ("free_kraken_ada_basis_varspot",
                    "free_kraken_link_basis_varspot"):
            self.assertNotIn("PF-PAIRED-RV-20261116",
                             by_id[vid]["form"], vid)

    def test_warm_serves_btc_4hour_on_the_same_route(self):
        from desk3 import warm
        hits = [(s, tf, d) for (s, tf, d) in warm.CRYPTO_FETCHES
                if s == "BTC/USD" and tf == "4Hour"]
        self.assertEqual(len(hits), 1)
        self.assertGreaterEqual(hits[0][2], 90)

    def test_parents_byte_untouched(self):
        for path, want in PARENT_FILE_SHA256.items():
            with open(os.path.join(ROOT, path), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(),
                                 want, path)

    def test_roster_count_unchanged(self):
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]
        self.assertEqual(len(rows), 400)
        for vid in FOUR:
            self.assertEqual(len([r for r in rows if r["id"] == vid]),
                             1, vid)


if __name__ == "__main__":
    unittest.main()
