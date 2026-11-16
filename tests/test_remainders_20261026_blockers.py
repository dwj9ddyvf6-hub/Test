"""Blockers: LIVE-REMAINDERS-20261026 — the four post-POS-SHAPE
remainders from the first live dispatch session (2026-10-26).

1. OPT-SHAPE-20261026 (qqq_put_ladder): the live options producer
   serves options[QQQ]["quotes"] as an OCC-keyed MAP; the batch-5
   consumer iterates it as a LIST of quote records -> its string keys
   crashed quote.get ('str' object has no attribute 'get'). Cure:
   desk3/port_b5/_ctx.py options_chain serves the canonical list.
2. BAR-T-SHAPE-20261026 (s_mn_opt_turtle): WarmBars serves bar "t"
   as an ISO string; the laz8 contract is epoch float, and
   laz8_common.bar_dates float()s it -> ValueError on
   '2025-06-13T04:00:00Z'. Cure: adapters/laz8_common normalizes
   string timestamps to epoch at the adapter boundary.
3. WORKER-EOF-20261026 (aster_r19 ..._normalization_{fullcash,
   volume1pct}): desk3/aster_crypto returns contract.Intent objects;
   desk3/worker.py json.dumps'd them OUTSIDE its guard, the worker
   process died mid-result, and the pool reported bare 'worker_eof'.
   Cure: the worker normalizes Intent objects to intent dicts and
   keeps serialization inside the guard.
4. BROKER-BURST-20261026 (dispatcher): ~80% of submits failed
   transiently (interleaved with successes from the cycle's first
   intent), the exception was swallowed unjournaled, retry_pending
   was never called by any caller, and the Dispatcher is rebuilt per
   cycle — every queued intent was LOST (806 broker_unavailable
   intents, zero terminal states). Cure: bounded in-call retry
   (3 attempts, 0.25s/0.75s backoff, transient classes only, same
   client_order_id) + the error journaled on broker_unavailable.

Fail direction (proven 2026-10-26, see BUGLOG_2026-10-26.md):
reverting each cure restores its original failure class.
"""
import hashlib, importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
NOW = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)


def _ctx(sid):
    return {"sleeve_id": sid, "state_dir": tempfile.mkdtemp(),
            "cycle_id": "cyc-test"}


class TestOptShapeQqqPutLadder(unittest.TestCase):
    def _live_options_payload(self):
        from desk3.producers import build_options_payload
        contracts = [{"symbol": "QQQ261205P00450000",
                      "expiration_date": "2026-12-05",
                      "strike_price": 450.0}]
        snaps = {"QQQ261205P00450000": {
            "latestQuote": {"bp": 2.0, "ap": 2.1, "bs": 1, "as": 1,
                            "t": "2026-10-26T15:00:00Z"},
            "greeks": {"delta": -0.06}}}
        return build_options_payload(
            ["QQQ"], {}, NOW,
            contracts_fetcher=lambda u, e, r: contracts,
            snapshots_fetcher=lambda s, e: snaps,
            spot_hint={"QQQ": 500.0})

    def test_producer_quotes_map_reaches_sleeve_as_list(self):
        payload = self._live_options_payload()
        # the producer shape that broke the sleeve, pinned as input:
        self.assertIsInstance(payload["options"]["QQQ"]["quotes"], dict)
        bars = {"QQQ|1Day": [
            {"t": (NOW - timedelta(days=i)).isoformat(), "o": 500,
             "h": 501, "l": 499, "c": 500, "v": 1000}
            for i in range(10)]}
        view = {"now": NOW.isoformat(), "bars": bars,
                "options": payload["options"], "positions": [],
                "params": {"posture": "normal"},
                "slice": {"capital_usd": 1000000.0, "cash_usd": 1000000.0}}
        mod = importlib.import_module("desk3.port_b5.qqq_put_ladder")
        out = mod.evaluate(view, _ctx("qqq_put_ladder"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "QQQ261205P00450000")
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 3)

    def test_fixture_list_shape_still_works(self):
        # the shape every fixture serves must keep working unchanged
        from desk3.port_b5._ctx import SnapshotSleeveContext
        view = {"now": NOW.isoformat(),
                "options": {"QQQ": {"quotes": [{"symbol": "X"}]}}}
        ctx = SnapshotSleeveContext("qqq_put_ladder", view, _ctx("qqq_put_ladder"))
        self.assertEqual(ctx.options_chain("QQQ")["quotes"],
                         [{"symbol": "X"}])


class TestBarTShapeTurtle(unittest.TestCase):
    def _iso_bars(self, closes):
        base = datetime(2025, 1, 1, 4, 0, tzinfo=timezone.utc)
        return [{"t": (base + timedelta(days=i)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),
                 "o": c, "h": c * 1.001, "l": c * 0.999, "c": c,
                 "v": 10000} for i, c in enumerate(closes)]

    def test_held_occ_exit_path_survives_iso_timestamps(self):
        # held OCC position + underlying closes collapsing through the
        # prior 10-day low: the exit path calls bar_dates() on the
        # underlying series (the exact float(ISO) crash site).
        closes = [100.0 + i * 0.1 for i in range(55)] + [90.0]
        view = {"bars": {"SPY": self._iso_bars(closes)},
                "positions": [{"symbol": "SPY250321C00100000", "qty": 1,
                               "avg_price": 2.0,
                               "opened_at": "2025-02-01T15:00:00"}],
                "options": {"chains": {}, "quotes": {}}}
        ctx = {"sleeve_id": "s_mn_opt_turtle", "session": "2025-02-26",
               "now": "2025-02-26T15:00:00", "equity": 10000.0}
        out = importlib.import_module(
            "adapters.s_mn_opt_turtle").evaluate(view, ctx)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertEqual(out[0]["symbol"], "SPY250321C00100000")

    def test_epoch_fixture_shape_unchanged(self):
        from adapters.laz8_common import _normalize_bars
        bars = {"AAA": [{"t": 1735689600.0, "c": 1.0}]}
        self.assertEqual(_normalize_bars(bars), bars)

    def test_date_only_strings_pass_through(self):
        # s_mn_faber's ENH19 stale gate parses str(t)[:10] as a date;
        # date-only strings are its native dialect and must not be
        # epoch-converted (gate regression caught in the full run).
        from adapters.laz8_common import _normalize_bars
        bars = {"SPY": [{"t": "2026-10-01", "c": 110.0}]}
        self.assertEqual(_normalize_bars(bars), bars)

    def test_bar_dates_on_iso_series(self):
        from sleeves.laz8_common import bar_dates
        from adapters.laz8_common import _normalize_bars
        rows = _normalize_bars({"SPY": self._iso_bars([100.0, 101.0])})["SPY"]
        self.assertEqual(bar_dates(rows), ["2025-01-01", "2025-01-02"])


class TestWorkerEof(unittest.TestCase):
    SID = ("aster_r19_adausdt_negative_funding_squeeze_"
           "normalization_fullcash")

    def _view(self):
        bars = [{"t": (NOW - timedelta(hours=4 * (25 - i))).isoformat(),
                 "o": 1.0, "h": 1.05, "l": 0.95, "c": 1.0, "v": 100000.0}
                for i in range(25)]
        return {"now": NOW.isoformat(), "bars": {"ADAUSDT|4Hour": bars},
                "funding": {"ADAUSDT": 0.001},
                "positions": [{"symbol": "ADAUSDT", "qty": 5000.0,
                               "avg_price": 1.0,
                               "opened_at": (NOW - timedelta(
                                   hours=2)).isoformat(),
                               "breakout_level": 1.05}],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}, "extra": {}, "session_fills": []}

    def test_intent_object_normalizes_to_dispatcher_dict(self):
        from desk3.worker import _normalize_intents
        mod = importlib.import_module(f"adapters3.{self.SID}")
        raw = mod.evaluate(self._view(), _ctx(self.SID))
        self.assertEqual(len(raw), 1)  # an Intent object pre-cure
        out = _normalize_intents(raw, self.SID, "cyc-test")
        self.assertEqual(len(out), 1)
        d = out[0]
        self.assertIsInstance(d, dict)
        json.dumps(d)  # must be JSON-serializable (the EOF crash site)
        self.assertEqual(d["kind"], "exit")
        self.assertEqual(d["symbol"], "ADA/USD")  # BLOCKED-EXIT-20261029: emitted in broker dialect
        self.assertEqual(d["side"], "sell")
        self.assertEqual(d["qty"], 5000.0)
        self.assertEqual(d["position_intent"], "sell_to_close")
        from desk3.models import validate_intent
        self.assertTrue(validate_intent(d))

    def test_pool_end_to_end_no_worker_eof(self):
        from desk3.pool import WorkerPool
        view = self._view()
        doc = {"hash": "repro-hash", "data": view}
        snap = os.path.join(tempfile.mkdtemp(), "snap.json")
        with open(snap, "w") as fh:
            json.dump(doc, fh)
        pool = WorkerPool(size=1, state_root=tempfile.mkdtemp(),
                          timeout_s=60.0)
        try:
            res = pool.run([{"sleeve_id": self.SID,
                             "module": f"adapters3.{self.SID}",
                             "snapshot_path": snap,
                             "snapshot_hash": "repro-hash",
                             "ctx": {"cycle_id": "cyc-test",
                                     "sleeve_id": self.SID,
                                     "state_dir": tempfile.mkdtemp()}}])
        finally:
            pool.close() if hasattr(pool, "close") else None
        r = res[self.SID]
        self.assertEqual(r["status"], "ok", r)
        self.assertEqual(len(r["intents"]), 1)
        self.assertEqual(r["intents"][0]["kind"], "exit")


class TestBrokerBurst(unittest.TestCase):
    def _intent(self):
        return {"intent_id": "burst-test-1", "kind": "entry",
                "symbol": "SPY", "side": "buy", "qty": 1,
                "order_type": "market", "limit_price": None,
                "price_hint": 100.0, "time_in_force": "day"}

    def _disp(self, broker):
        from desk3.dispatcher import Dispatcher
        return Dispatcher(tempfile.mkdtemp(), broker,
                          slices={"s": {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0}},
                          price_lookup=lambda s: 100.0)

    def test_transient_429_retried_in_call_to_fill(self):
        from desk3.broker import FakeBroker
        from desk3.netfetch import FetchError

        class Flaky(FakeBroker):
            def __init__(self):
                super().__init__(prices={"SPY": 100.0})
                self.attempts = 0

            def submit_order(self, *a, **k):
                self.attempts += 1
                if self.attempts < 3:
                    raise FetchError(429, "https://paper-api.alpaca.markets/v2/orders")
                return super().submit_order(*a, **k)

        broker = Flaky()
        r = self._disp(broker).process_intent(self._intent(), "s")
        self.assertEqual(broker.attempts, 3)
        self.assertEqual(r["status"], "filled")

    def test_non_transient_422_not_retried_and_error_journaled(self):
        from desk3.broker import FakeBroker
        from desk3.netfetch import FetchError

        class Bad(FakeBroker):
            def __init__(self):
                super().__init__(prices={"SPY": 100.0})
                self.attempts = 0

            def submit_order(self, *a, **k):
                self.attempts += 1
                raise FetchError(422, "https://paper-api.alpaca.markets/v2/orders")

        broker = Bad()
        disp = self._disp(broker)
        r = disp.process_intent(self._intent(), "s")
        self.assertEqual(broker.attempts, 1)
        # READINESS-DSP1-20261112 supersession, named: the 422 is
        # still never retried and the error is still journaled
        # (every assertion below unchanged), but the verdict is
        # now consumed terminally — status "rejected", nothing
        # persisted — instead of "queued" into the pending store,
        # whose drain used to submit the identical payload again.
        self.assertEqual(r["status"], "rejected")
        rows = [json.loads(l) for l in open(disp.djournal) if l.strip()]
        bu = [x for x in rows if x["event"] == "broker_unavailable"]
        self.assertEqual(len(bu), 1)
        self.assertIn("FetchError", bu[0]["error"])
        self.assertIn("422", bu[0]["error"])

    def test_persistent_transient_bounded_attempts_then_queued(self):
        from desk3.broker import FakeBroker
        from desk3.netfetch import FetchError

        class Down(FakeBroker):
            def __init__(self):
                super().__init__(prices={"SPY": 100.0})
                self.attempts = 0

            def submit_order(self, *a, **k):
                self.attempts += 1
                raise FetchError(503, "https://paper-api.alpaca.markets/v2/orders")

        broker = Down()
        r = self._disp(broker).process_intent(self._intent(), "s")
        self.assertEqual(broker.attempts, 3)  # bounded: 3, never a loop
        self.assertEqual(r["status"], "queued")


class TestRailsUntouched(unittest.TestCase):
    def test_saty_sol_byte_identical(self):
        h = hashlib.sha256(open(os.path.join(
            ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest()
        self.assertTrue(h.startswith("36e306c6"), h)


if __name__ == "__main__":
    unittest.main()
