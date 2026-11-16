"""HARDEN batch-2 blockers (2026-10-24) — G4 producers for the eight
named families: funding, quotes, tensor, tensor_fires,
tensor_daily20, options, options_chain, options_quotes.

Pre-cure state (HARDEN-AUDIT §2 G4): run_live registered ONLY bars +
positions producers, so every sleeve declaring these inputs was
UNFED by name. Cure: desk3/producers.py (shared source) wired in
run_live.build_desk via register_all, plus the aster_b2/aster_b4
options-shape normalization (live producer emits the runtime-cache
dict shape; those two engines iterated the fixture list shape only).

Fail direction: on the pre-cure tree desk3.producers does not exist
(ImportError in every test below) and build_desk's registry has no
producer for any of the eight keys; the b2/b4 dict-shape E2E raises
AttributeError on the un-normalized engines.
"""
import importlib, json, math, os, shutil, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 26, 13, 37, tzinfo=timezone.utc)  # Mon 09:37 ET
BATCH2_KEYS = ("funding", "quotes", "tensor", "tensor_fires",
               "tensor_daily20", "options", "options_chain",
               "options_quotes")


def ctx_of(sid):
    return {"sleeve_id": sid, "cycle_id": "fx",
            "state_dir": tempfile.mkdtemp()}


# ---------------------------------------------------------------- funding
class TestFundingProducer(unittest.TestCase):
    def test_rates_shape_and_fail_closed(self):
        # R1 RULING 2026-10-25: the funding source is Coinalyze now
        # (Binance premiumIndex = HTTP 451 from this box); the shape
        # law is unchanged — {SYM: float} plus the source stamp.
        from desk3.producers import CoinalyzeFunding
        p = CoinalyzeFunding(fetcher=lambda syms: {s: -0.0004 for s in syms})
        out = p({"now": NOW})
        self.assertEqual(set(out), {"funding", "funding_source"})
        self.assertEqual(out["funding_source"], "coinalyze")
        self.assertEqual(out["funding"]["ADAUSDT"], -0.0004)
        self.assertIsInstance(out["funding"]["ENJUSDT"], float)

        def boom(syms):
            raise RuntimeError("coinalyze down")
        self.assertEqual(CoinalyzeFunding(fetcher=boom)({"now": NOW}), {})
        self.assertEqual(CoinalyzeFunding(fetcher=lambda s: {})({"now": NOW}), {})

    def test_funding_e2e_entry_exit_flat(self):
        # aster_crypto NFS fixed96: entry on breakout + funding<0,
        # exit at the 96h deadline, flat afterwards.
        from desk3.producers import CoinalyzeFunding
        sid = "aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash"
        mod = importlib.import_module(f"adapters3.{sid}")
        bars = []
        for i in range(25):
            t = NOW - timedelta(hours=4 * (25 - i))
            c = 1.10 if i == 24 else 1.0
            bars.append({"t": t.isoformat(), "o": 1.0, "h": 1.05,
                         "l": 0.95, "c": c, "v": 100000.0})
        fund = CoinalyzeFunding(fetcher=lambda s: {"ADAUSDT": -0.01})({"now": NOW})
        view = {"now": NOW.isoformat(), "bars": {"ADAUSDT|4Hour": bars},
                "positions": [], "slice": {"capital_usd": 10000.0,
                                           "cash_usd": 10000.0},
                "params": {}, "extra": {}, **fund}
        out = mod.evaluate(view, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "enter")
        # manage: held 20h, no exit yet
        pos = [{"symbol": "ADAUSDT", "qty": 5000.0, "avg_price": 1.0,
                "opened_at": (NOW - timedelta(hours=20)).isoformat(),
                "breakout_level": 1.05}]
        view["positions"] = pos
        self.assertEqual(mod.evaluate(view, ctx_of(sid)), [])
        # exit at deadline (100h held)
        pos[0]["opened_at"] = (NOW - timedelta(hours=100)).isoformat()
        out = mod.evaluate(view, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        # flat: no position, last bar no longer a fresh breakout close
        view["positions"] = []
        view["bars"] = {"ADAUSDT|4Hour": bars[:-1] + [
            {**bars[-1], "t": (NOW + timedelta(hours=4)).isoformat(),
             "c": 1.0}]}
        self.assertEqual(mod.evaluate(view, ctx_of(sid)), [])


# ---------------------------------------------------------------- quotes
class TestQuotesProducer(unittest.TestCase):
    RAW = {"SPY": {"bp": 117.98, "ap": 118.02, "bs": 100, "as": 100,
                   "t": "2026-10-26T13:37:00Z"},
           "QQQ": {"bp": 0, "ap": 200.0, "bs": 1, "as": 1,
                   "t": "2026-10-26T13:37:00Z"}}

    def test_shape_two_sided_only_and_fail_closed(self):
        from desk3.producers import StockQuotes
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "config"))
        with open(os.path.join(tmp, "config", "universes.json"), "w") as fh:
            json.dump({}, fh)
        p = StockQuotes(tmp, {}, fetcher=lambda syms, env: dict(self.RAW))
        out = p({"now": NOW})
        q = out["quotes"]["SPY"]
        # FEED-WIRE-20261025 re-pin: was "sip" — feed=sip 403s on this
        # account tier; the producer now requests feed=delayed_sip and
        # stamps the truth. Sleeves pinning "sip" refuse it by name.
        self.assertEqual((q["feed"], q["bid"], q["ask"]), ("delayed_sip", 117.98, 118.02))
        self.assertEqual(q["market_at"], q["at"])
        self.assertIn("received_at", q)
        self.assertNotIn("QQQ", out["quotes"])  # one-sided dropped

        def boom(syms, env):
            raise RuntimeError("sip down")
        p2 = StockQuotes(tmp, {}, fetcher=boom)
        self.assertEqual(p2({"now": NOW}), {})


# ---------------------------------------------------------------- options
OCC1 = "SPY261113C00118000"   # SPY 2026-11-13 call 118
OCC2 = "SPY261113C00123000"   # SPY 2026-11-13 call 123


def fake_contracts(und, env, ref):
    if und != "SPY":
        return []
    return [{"symbol": OCC1, "expiration_date": "2026-11-13",
             "strike_price": "118.0"},
            {"symbol": OCC2, "expiration_date": "2026-11-13",
             "strike_price": "123.0"},
            {"symbol": "SPY261113C00500000", "expiration_date": "2026-11-13",
             "strike_price": "500.0"}]  # outside the +/-25% band at spot 118


def fake_snapshots(occs, env):
    rows = {OCC1: {"latestQuote": {"bp": 2.90, "ap": 3.00, "bs": 10,
                                   "as": 10, "t": "2026-10-26T13:37:00Z"},
                   "greeks": {"delta": 0.55}},
            OCC2: {"latestQuote": {"bp": 1.10, "ap": 1.20, "bs": 10,
                                   "as": 10, "t": "2026-10-26T13:37:00Z"},
                   "greeks": {"delta": 0.30}}}
    return {o: rows[o] for o in occs if o in rows}


class TestOptionsProducer(unittest.TestCase):
    def _producer(self, tmp):
        from desk3.producers import AlpacaOptions
        return AlpacaOptions(
            tmp, {}, contracts_fetcher=fake_contracts,
            snapshots_fetcher=fake_snapshots,
            quotes_fetcher=lambda syms, env: {
                "SPY": {"bp": 117.98, "ap": 118.02}})

    def test_three_shapes_from_one_fetch(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        out = self._producer(tmp)({"now": NOW})
        self.assertEqual(set(out), {"options", "options_chain",
                                    "options_quotes"})
        # runtime-cache shape for the ported base sleeves
        payload = out["options"]["SPY"]
        self.assertIn(OCC1, payload["quotes"])
        self.assertEqual(payload["chains"]["SPY"][0]["delta"], 0.55)
        # aster_batch3 chain shape: greeks stamps + delta present,
        # out-of-band strike excluded
        chain = out["options_chain"]["SPY"]
        self.assertEqual([r["symbol"] for r in chain], [OCC1, OCC2])
        self.assertIn("greeks_market_at", chain[0])
        self.assertIn("greeks_received_at", chain[0])
        # aster_batch3 quotes shape: feed stamps.
        # FEED-WIRE-20261025 re-pin: was "opra" — feed=opra 403s on
        # this account tier; the producer now requests
        # feed=indicative and stamps the truth (the old stamp claimed
        # a feed that never served the quote).
        q = out["options_quotes"][OCC1]
        self.assertEqual((q["feed"], q["bid"], q["ask"]), ("indicative", 2.90, 3.00))

    def test_fail_closed(self):
        from desk3.producers import AlpacaOptions
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)

        def boom(und, env, ref):
            raise RuntimeError("contracts down")
        p = AlpacaOptions(tmp, {}, contracts_fetcher=boom,
                          snapshots_fetcher=fake_snapshots,
                          quotes_fetcher=lambda s, e: {})
        self.assertEqual(p({"now": NOW}), {})
        p2 = AlpacaOptions(tmp, {}, contracts_fetcher=fake_contracts,
                           snapshots_fetcher=lambda occs, env: {},
                           quotes_fetcher=lambda s, e: {})
        self.assertEqual(p2({"now": NOW}), {})  # nothing quotable

    def test_b2_b4_engines_accept_producer_dict_shape(self):
        # The live "options" value is a dict; aster_b2/b4 fixture shape
        # was a list. Both engines must select from the dict shape.
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        out = self._producer(tmp)({"now": NOW})
        from desk3 import aster_b2, aster_b4
        rows = aster_b2._contracts({"options": out["options"]})
        self.assertEqual({r["symbol"] for r in rows}, {OCC1, OCC2})
        rows4 = aster_b4._contracts({"options": out["options"]})
        self.assertEqual({r["symbol"] for r in rows4}, {OCC1, OCC2})
        self.assertEqual(aster_b2._contracts({"options": rows}), rows)

    def test_options_e2e_entry_exit_flat_batch3(self):
        # aster_rec_rsi2_vertical_fixed_a driven on producer-shaped
        # options_chain/options_quotes/quotes.
        # FEED-WIRE-20261025 re-pin: this E2E originally asserted
        # entry -> fixed exit -> flat. The producer now stamps
        # options_quotes with the TRUE feed ("indicative" — opra
        # 403s on this tier), and aster_batch3 package pricing pins
        # feed "opra" by name (_fresh raises requires_opra), so on
        # producer output the sleeve now refuses by name and emits
        # NOTHING. That refusal is the sleeve's own gate doing its
        # job on the data this tier serves — named, not tuned away.
        # Entry/exit mechanics on opra-stamped fixtures remain
        # covered by tests/test_aster_batch3_blockers.py.
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        out = self._producer(tmp)({"now": NOW})
        import tests.test_aster_batch3_blockers as b3
        sid = "aster_rec_rsi2_vertical_fixed_a"
        mod = importlib.import_module(f"adapters3.{sid}")
        v = b3.entry_view_for(sid)
        v["options_chain"] = out["options_chain"]
        v["options_quotes"] = out["options_quotes"]
        v["quotes"] = {"SPY": {"symbol": "SPY", "feed": "sip",
                               "bid": 117.98, "ask": 118.02,
                               "bid_size": 100, "ask_size": 100,
                               "market_at": v["now"],
                               "received_at": v["now"]}}
        entries = mod.evaluate(v, ctx_of(sid))
        # FEED-WIRE-20261025: requires_opra refusal — no entry is
        # emitted on indicative-stamped producer quotes.
        self.assertEqual(entries, [])


# ---------------------------------------------------------------- tensor
def write_bundle(root, doc):
    d = os.path.join(root, "cache", "tensor")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "bundle.json"), "w") as fh:
        json.dump(doc, fh)


class TestTensorBundleProducer(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_serves_three_keys_and_fail_closed(self):
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        for key in ("tensor", "tensor_fires", "tensor_daily20"):
            self.assertEqual(TensorBundleFile(tmp, key)({"now": NOW}), {})
        write_bundle(tmp, {"generated_at": NOW.isoformat(),
                           "fires": [{"symbol": "ABC"}],
                           "tensor_daily20": {"ADSK": [{"symbol": "ADSK"}]},
                           "sleeves": {}})
        self.assertEqual(
            TensorBundleFile(tmp, "tensor_fires")({"now": NOW}),
            {"tensor_fires": [{"symbol": "ABC"}]})
        self.assertIn("tensor",
                      TensorBundleFile(tmp, "tensor")({"now": NOW}))
        self.assertEqual(
            TensorBundleFile(tmp, "tensor_daily20")({"now": NOW}),
            {"tensor_daily20": {"ADSK": [{"symbol": "ADSK"}]}})
        # stale bundle: fail closed
        write_bundle(tmp, {"generated_at": (NOW - timedelta(days=3)).isoformat(),
                           "fires": [{"symbol": "ABC"}]})
        self.assertEqual(TensorBundleFile(tmp, "tensor_fires")({"now": NOW}), {})

    def test_tensor_e2e_entry_exit_flat(self):
        # aster_tensor_g4_cash_all_25 (batch14 engine, "tensor" key):
        # entry on a buy-green fire, week-52 deadline exit, flat.
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        fire = {"symbol": "ABC", "signal": "buy-green", "price": 8.0,
                "depth60": 80.0, "ret60": 5.0, "vol20": 0.12,
                "adv_usd": 3_000_000, "atr_ratio": 0.5,
                "date": "2026-10-22"}
        write_bundle(tmp, {"generated_at": NOW.isoformat(),
                           "fires": [fire]})
        prod = TensorBundleFile(tmp, "tensor")({"now": NOW})
        # batch14 _fires accepts a list or {"fires": [...]} dict
        view = {"now": NOW.isoformat(),
                "tensor": prod["tensor"].get("fires"),
                "bars": {}, "positions": []}
        sid = "aster_tensor_g4_cash_all_25"
        mod = importlib.import_module(f"adapters3.{sid}")
        out = mod.evaluate(view, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        pos = [{"symbol": "ABC", "qty": 50, "avg_price": 8.0,
                "sessions_held": 260}]
        view["positions"] = pos
        out = mod.evaluate(view, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        view["positions"] = []
        view["tensor"] = []
        self.assertEqual(mod.evaluate(view, ctx_of(sid)), [])

    def test_tensor_fires_e2e_entry_exit_flat(self):
        # aster_r19_tensor_g4_hot_delay_25 (batch15 engine,
        # "tensor_fires" key): delayed entry, 52-week exit, flat.
        import tests.test_aster_batch15_blockers as b15
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        f = b15.fire(end=b15.SIG_END)
        write_bundle(tmp, {"generated_at": NOW.isoformat(),
                           "tensor_fires": [f]})
        prod = TensorBundleFile(tmp, "tensor_fires")({"now": NOW})
        self.assertEqual(prod["tensor_fires"], [f])
        sid = b15.G4_DELAY
        sd = tempfile.mkdtemp()
        v = b15.g4_view(b15.at(b15.SESSIONS[25]), prod["tensor_fires"])
        self.assertEqual(b15.drive(sid, v, sd), [])  # pending (delay)
        entry_day = b15.date.fromisoformat(b15.FOLLOW[1])
        out = b15.drive(sid, b15.g4_view(b15.at(entry_day),
                                         prod["tensor_fires"]), sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        # 52-week scheduled exit (fixture geometry from batch15 test)
        entry = b15.date(2025, 2, 18)
        monday = entry - timedelta(days=entry.weekday())
        week = monday + timedelta(weeks=51)
        rows = [d for d in b15.SESSIONS
                if week <= d < week + timedelta(days=7)]
        pos = [{"symbol": "AAA", "qty": 79, "avg_price": 5.0,
                "opened_at": b15.at(entry).isoformat(),
                "issuer_id": "iss-AAA"}]
        out = b15.drive(sid, b15.g4_view(b15.at(rows[-1]), [],
                                         positions=pos), sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        out = b15.drive(sid, b15.g4_view(b15.at(rows[-1]), [],
                                         positions=[]), sd)
        self.assertEqual(out, [])

    def test_tensor_daily20_e2e_entry_exit_flat(self):
        # aster_tensor_d20_pv: entry on frozen-model selection,
        # hold-20-bars exit, flat on no rows.
        import tests.test_aster_batch16_blockers as b16
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        rows = {"ADSK": b16.d20_rows()}
        write_bundle(tmp, {"generated_at": NOW.isoformat(),
                           "tensor_daily20": rows})
        prod = TensorBundleFile(tmp, "tensor_daily20")({"now": NOW})
        sid = b16.D20P
        mod = importlib.import_module(f"adapters3.{sid}")
        v = b16.d20_view(rowsmap=prod["tensor_daily20"])
        out = mod.evaluate(v, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        pos = [{"symbol": "ADSK", "qty": 10, "avg_price": 100.0,
                "bars_held": 20}]
        v2 = b16.d20_view(rowsmap=prod["tensor_daily20"], positions=pos)
        out = mod.evaluate(v2, ctx_of(sid))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        v3 = b16.d20_view(rowsmap={})
        self.assertEqual(mod.evaluate(v3, ctx_of(sid)), [])


# ---------------------------------------------------------------- wiring
class TestRunLiveWiring(unittest.TestCase):
    def test_build_desk_registers_all_batch2_producers(self):
        from desk3.run_live import build_desk
        desk, rows = build_desk(ROOT, dispatch=False,
                                env={"ALPACA_KEY_ID": "x",
                                     "ALPACA_SECRET_KEY": "y"})
        try:
            produced = set()
            for spec in desk.registry.producers.values():
                produced.update(spec["outputs"])
            for key in BATCH2_KEYS:
                self.assertIn(key, produced)
        finally:
            desk.close()

    def test_registry_census_no_batch2_missing_when_produced(self):
        # With every batch-2 producer returning its keys, NO sleeve in
        # config may report a batch-2 key missing (other still-open
        # families like earnings_events may remain — not this batch).
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        from desk3.producers import register_all
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        desk = Desk(tmp, broker=FakeBroker(), sleeve_path=tmp)
        register_all(desk, tmp, env={})
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        for row in cfg["sleeves"]:
            desk.add_sleeve(row["id"], row["module"],
                            row.get("inputs", []), row.get("cadence_s", 300),
                            float(row["slice"]["capital_usd"]),
                            parked=bool(row.get("parked", False)))
        ts = NOW.timestamp()
        for name, fn in desk.producers.items():
            desk.registry.mark_produced_keys(
                name, set(desk.registry.producers[name]["outputs"]), ts=ts)
        states = desk.registry.fed_states(now=ts)
        bad = {sid: [k for k in st["missing"] if k in BATCH2_KEYS]
               for sid, st in states.items()}
        bad = {sid: ks for sid, ks in bad.items() if ks}
        self.assertEqual(bad, {})


if __name__ == "__main__":
    unittest.main()
