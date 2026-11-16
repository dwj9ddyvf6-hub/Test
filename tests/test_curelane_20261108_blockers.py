"""CURE-LANE-20261108 blockers: the five cure rows of the
2026-11-08 desk cure lane (night inspection 2026-11-08 follow-up).

1. JOURNAL-ROTATION-LEDGER-20261108: journal rotation overwrote
   the previous rotated generation (os.replace onto .1), so the
   second rotation after 2026-11-02 destroyed the epoch's first
   journal generation (2026-10-26..11-02) at 2026-11-08T13:35Z.
   Every derivation reading the journal (reconcile truth, the
   fill sweep's submission index, the dispatcher's duplicate
   index, the session fills census) silently lost that span:
   reconcile unexplained cash jumped 5,122.82 -> 40,835.40 in
   one cycle with no broker event. Cure: rotation shifts
   generations up and never deletes; every reader enumerates
   all generations through journal.journal_generations.

2. ORDER-HOLD-CASH-20261108: reconcile compared journal
   expected cash against the broker's raw `cash`, which excludes
   funds encumbered by open orders while `equity` counts them.
   The desk's own stuck pending_new BTC buy (submitted
   2026-11-07T13:22:25Z, 5,087.72 hold) stepped broker cash down
   by exactly the hold in the first reconcile after submission
   and manufactured the desk-wide cash halt. Cure: the cycle
   derives the hold from the broker's own account identity
   (equity - cash - position_market_value) and reconcile
   compares expected cash against cash + holds, naming the hold
   on the report and the cash row. No threshold changed.

3. POSITION-DIALECT-READBACK-20261108: aster_batch1._positions
   keyed the snapshot's positions by their raw symbol; the
   snapshot serves the broker's BARE form (BTCUSD) while the
   native engine looks up the dashed internal form and the
   slash broker form, so held qty read 0 every cycle and
   aster_native_btc_eth_sma200 re-bought its full ~$5,000 BTC
   target every evaluation (41 filled buys on 2026-11-07, one
   per cycle, identical qty 0.065804301 twice as the daily-close
   price input repeated). Cure: keys normalized through the one
   canonical translator, desk3.broker_dialect.

4. QULLA-SESSION-RULE-20261108: QullaFileProducer and
   QullaScanWarmer demanded the qulla file's session equal
   today's CALENDAR date; the scan stamps the most recent
   trading day (its decision-date rule), so every weekend and
   holiday the producer named stale_qulla_session (sleeve
   UNFED) and the warmer relaunched the full engine scan every
   retry window for a file that was already current. Cure: one
   shared expected-session rule in producers_g4.

5. PID-DEAD-BOOT-CLASS-20261108: watchdog restart rows carried
   no host boot identity, so a runner killed by a HOST REBOOT
   (2026-11-08: full OS boots at ~2h cadence, journal "Journal
   started" at each, watchdog service and runner both new at
   the same minute) was indistinguishable from a lone runner
   death. Cure: restart and wedged_terminated rows carry the
   host boot_id.

Fail direction on the pre-cure tree: journal_generations,
_expected_qulla_session and _boot_id do not exist (ImportError /
AttributeError); reconcile() rejects the broker_order_holds_usd
kwarg (TypeError); _positions keys stay in the bare dialect and
the native evaluator re-emits the full target with the position
already at target.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")


# ------------------------------------------------------------ rotation
class TestJournalRotationPreservesGenerations(unittest.TestCase):
    def test_rotation_shifts_and_readers_see_every_row(self):
        from desk3 import journal
        from desk3.reconcile import journal_rows
        root = tempfile.mkdtemp(prefix="rot_")
        state = os.path.join(root, "state")
        os.makedirs(state)
        path = os.path.join(state, "dispatcher.jsonl")
        markers = []
        old_max = journal.MAX_JOURNAL_BYTES
        journal.MAX_JOURNAL_BYTES = 400
        try:
            for i in range(60):
                row = {"event": "order_submitted", "n": i,
                       "client_order_id": f"coid-{i}",
                       "pad": "x" * 40}
                markers.append(i)
                journal.append_line(path, row)
        finally:
            journal.MAX_JOURNAL_BYTES = old_max
        gens = journal.journal_generations(path)
        # more than the pre-cure two files survive
        self.assertGreaterEqual(len(gens), 3)
        # oldest first: the first generation opens with row 0
        with open(gens[0]) as fh:
            first = json.loads(fh.readline())
        self.assertEqual(first["n"], 0)
        # the reconcile reader sees every row exactly once
        seen = [r["n"] for r in journal_rows(path)
                if r.get("event") == "order_submitted"]
        self.assertEqual(sorted(seen), markers)

    def test_generations_order_and_gaps(self):
        from desk3.journal import journal_generations
        root = tempfile.mkdtemp(prefix="gen_")
        p = os.path.join(root, "dispatcher.jsonl")
        open(p, "w").close()
        open(p + ".1", "w").close()
        open(p + ".3", "w").close()  # a gap: .2 missing
        self.assertEqual(journal_generations(p), [p + ".3", p + ".1", p])
        self.assertEqual(journal_generations(p + ".missing"), [])


# ------------------------------------------------------------ order hold
CAP = 100000.0


def _cash_state():
    root = tempfile.mkdtemp(prefix="hold_")
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "capital_epoch.json"), "w") as fh:
        json.dump({"epoch_start_utc": "2026-10-26T20:14:30+00:00"}, fh)
    open(os.path.join(state, "dispatcher.jsonl"), "w").close()
    from desk3.reconcile import reconcile
    rep = reconcile(state, {}, broker_cash=CAP,
                    slice_capital={"s1": CAP}, record_baseline=True)
    assert rep["status"] == "BASELINE_RECORDED", rep
    # one fill: buy 10 AAPL @ 10 -> expected cash CAP-100,
    # expected position AAPL 10.
    with open(os.path.join(state, "dispatcher.jsonl"), "a") as fh:
        fh.write(json.dumps(
            {"event": "fill", "sleeve": "s1", "symbol": "AAPL",
             "side": "buy", "qty": 10, "price": 10.0,
             "ts": "2026-11-08T00:00:00+00:00"}) + "\n")
    return state


class TestReconcileOrderHold(unittest.TestCase):
    POS = {"AAPL": 10.0}

    def _rep(self, state, broker_cash, holds="ABSENT"):
        from desk3.reconcile import reconcile
        kw = {} if holds == "ABSENT" else {"broker_order_holds_usd": holds}
        return reconcile(state, self.POS, broker_cash=broker_cash,
                         slice_capital={"s1": CAP}, broker_fees_usd=0.0,
                         **kw)

    def test_raw_cash_gap_halts_without_holds(self):
        # The 2026-11-07 shape: broker cash sits exactly the
        # open-order hold below expectation, no holds supplied.
        rep = self._rep(_cash_state(), CAP - 100 - 5000)
        self.assertTrue(rep["cash_halt"])
        self.assertEqual(rep["unexplained_cash_usd"], 5000.0)

    def test_holds_named_and_compared(self):
        rep = self._rep(_cash_state(), CAP - 100 - 5000, holds=5000.0)
        self.assertFalse(rep["cash_halt"])
        # no cash discrepancy row -> the headline stays None
        # (the desk's clean-run convention), not a forgiven zero
        self.assertIsNone(rep["unexplained_cash_usd"])
        self.assertEqual(rep["broker_order_holds_usd"], 5000.0)
        self.assertEqual(rep["discrepancies"], [])

    def test_overstated_holds_still_halt(self):
        # An overstated hold manufactures a gap in the other
        # direction and must not pass silently (unexplained is
        # reported as a magnitude; the halt is magnitude-aware).
        rep = self._rep(_cash_state(), CAP - 100 - 5000, holds=6500.0)
        self.assertTrue(rep["cash_halt"])
        self.assertEqual(rep["unexplained_cash_usd"], 1500.0)

    def test_negative_holds_clamped_to_zero(self):
        rep = self._rep(_cash_state(), CAP - 100 - 5000, holds=-50.0)
        self.assertEqual(rep["broker_order_holds_usd"], 0.0)
        self.assertTrue(rep["cash_halt"])


# ------------------------------------------------------------ dialect
def _ctx():
    return {"state_dir": tempfile.mkdtemp(prefix="aster_"),
            "now": datetime(2026, 10, 23, 14, 0, tzinfo=timezone.utc)}


def _ev(sid, view):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, _ctx())


def _daily(closes, sym):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return {f"{sym}|1Day": [
        {"t": (base + timedelta(days=i)).isoformat(), "o": c,
         "h": c * 1.001, "l": c * 0.999, "c": c, "v": 100000}
        for i, c in enumerate(closes)]}


class TestNativePositionsDialect(unittest.TestCase):
    def _bars(self):
        up = [100 + 0.5 * i for i in range(210)]     # last 204.5
        down = [300 - 0.5 * i for i in range(210)]
        out = {}
        out.update(_daily(up, "BTC-USD"))
        out.update(_daily(down, "ETH-USD"))
        return out

    def test_positions_keys_normalized_to_broker_form(self):
        from desk3.aster_batch1 import _positions
        out = _positions({"positions": [
            {"symbol": "BTCUSD", "qty": 0.5, "avg_price": 100.0},
            {"symbol": "AAPL", "qty": 3, "avg_price": 10.0}]})
        self.assertIn("BTC/USD", out)
        self.assertNotIn("BTCUSD", out)
        self.assertIn("AAPL", out)  # equities pass through

    def test_internal_dialect_keys_untouched(self):
        # The absorption family's books are keyed in the USDT
        # internal form and the rsi2/pair books in the dashed
        # form; rows already carrying an internal form keep it
        # (the gate's absorption blockers pin this contract).
        from desk3.aster_batch1 import _positions
        out = _positions({"positions": [
            {"symbol": "ENJUSDT", "qty": 5, "avg_price": 1.0},
            {"symbol": "ETH-USD", "qty": 2, "avg_price": 100.0}]})
        self.assertIn("ENJUSDT", out)
        self.assertIn("ETH-USD", out)
        self.assertNotIn("ENJ/USD", out)

    def test_held_at_target_emits_nothing(self):
        # Broker BARE form. The engine targets 50% of the book it
        # can see (static slice cash + holdings): held 10000 of
        # BTC against 10000 cash is exactly the pair weight, so
        # the delta is zero. Pre-cure the lookup missed the bare
        # form and the full target was re-bought every cycle.
        qty = 10000.0 / 204.5
        pos = [{"symbol": "BTCUSD", "qty": qty, "avg_price": 204.5}]
        out = _ev("aster_native_btc_eth_sma200",
                  {"now": "2026-10-23T14:00:00+00:00",
                   "bars": self._bars(), "positions": pos,
                   "slice": {"capital_usd": 10000.0,
                             "cash_usd": 10000.0}})
        self.assertEqual(out, [])

    def test_held_position_shrinks_the_buy_to_the_delta(self):
        # Held 2495 (broker bare form): the pair target is 50% of
        # (10000 cash + 2495 held) = 6247.50, so the buy is the
        # 3752.50 delta less the 0.1% fee reserve = 3748.75, NOT
        # the empty-book 4990 the pre-cure code emitted with the
        # position already on the book (the repeater's shape).
        qty = 2495.0 / 204.5
        pos = [{"symbol": "BTCUSD", "qty": qty, "avg_price": 204.5}]
        out = _ev("aster_native_btc_eth_sma200",
                  {"now": "2026-10-23T14:00:00+00:00",
                   "bars": self._bars(), "positions": pos,
                   "slice": {"capital_usd": 10000.0,
                             "cash_usd": 10000.0}})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "BTC/USD")
        self.assertAlmostEqual(out[0]["qty"] * 204.5, 3748.75, delta=30.0)
        self.assertLess(out[0]["qty"] * 204.5, 4990.0)


# ------------------------------------------------------------ qulla
class TestQullaSessionRule(unittest.TestCase):
    def test_expected_session_walks_back_to_trading_day(self):
        from desk3.producers_g4 import _expected_qulla_session
        # Sunday 2026-11-08 -> Friday 2026-11-06 (the scan's stamp)
        self.assertEqual(_expected_qulla_session(date(2026, 11, 8)),
                         "2026-11-06")
        # Saturday -> Friday; Monday -> itself
        self.assertEqual(_expected_qulla_session(date(2026, 11, 7)),
                         "2026-11-06")
        self.assertEqual(_expected_qulla_session(date(2026, 11, 9)),
                         "2026-11-09")

    def _root_with_file(self, session):
        root = tempfile.mkdtemp(prefix="qulla_")
        d = os.path.join(root, "cache", "qulla")
        os.makedirs(d)
        with open(os.path.join(d, "proposals.json"), "w") as fh:
            json.dump({"session": session, "proposals": []}, fh)
        return root

    def test_producer_serves_friday_file_on_sunday(self):
        from desk3.producers_g4 import QullaFileProducer
        p = QullaFileProducer(self._root_with_file("2026-11-06"))
        now = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)
        out = p({"now": now})
        self.assertIn("qulla", out)
        self.assertIsNone(p.last_error)

    def test_producer_still_rejects_wrong_session(self):
        from desk3.producers_g4 import QullaFileProducer
        p = QullaFileProducer(self._root_with_file("2026-11-05"))
        now = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(p({"now": now}), {})
        self.assertEqual(p.last_error, "stale_qulla_session")

    def test_producer_rejects_friday_file_on_monday(self):
        from desk3.producers_g4 import QullaFileProducer
        p = QullaFileProducer(self._root_with_file("2026-11-06"))
        now = datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(p({"now": now}), {})
        self.assertEqual(p.last_error, "stale_qulla_session")

    def test_warmer_launches_nothing_for_current_weekend_file(self):
        from desk3.producers_g4 import QullaScanWarmer
        root = self._root_with_file("2026-11-06")
        w = QullaScanWarmer(root)
        now = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(w({"now": now}), {})
        self.assertIsNone(w.last_error)
        # no scan was stamped or launched
        self.assertFalse(os.path.exists(
            os.path.join(root, "cache", "qulla", "scan_attempt.json")))


# ------------------------------------------------------------ boot id
class TestWatchdogBootId(unittest.TestCase):
    def test_boot_id_reads_proc_and_caches(self):
        from desk3 import watchdog
        try:
            want = open("/proc/sys/kernel/random/boot_id").read().strip()
        except OSError:
            self.skipTest("no /proc boot_id on this host")
        if not want:
            self.skipTest("empty boot_id")
        self.assertEqual(watchdog._boot_id(), want)
        self.assertEqual(watchdog._boot_id(), want)  # cached, stable

    def test_restart_rows_carry_boot_id(self):
        # Source-assertion (desk law's named fallback): the full
        # maintain() harness needs a live pid table; the row
        # construction sites are the contract.
        src = open(os.path.join(ROOT, "desk3", "watchdog.py")).read()
        self.assertIn('"mode": want, "boot_id": _boot_id()', src)
        self.assertGreaterEqual(src.count('"boot_id": _boot_id()'), 3)


if __name__ == "__main__":
    unittest.main()
