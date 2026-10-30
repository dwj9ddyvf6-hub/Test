import os, sqlite3, tempfile, threading, time, unittest, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from deskkit.ids import signal_key, client_order_id
from deskkit.ledger import Ledger
from deskkit.fsm import Position, IllegalTransition
from deskkit.store import StateStore
from deskkit.broker import ShadowBroker, tick_round, Order, SendUnknown, Refused
from deskkit.caps import Lane, budget_vs_capacity
from deskkit.heartbeat import standby_should_trade, keepalive_ok
from deskkit.reconcile import reconcile, orphans
from deskkit.alerts import Alerts
from deskkit.desk import Desk
from deskkit.clock import JumpDetector
from deskkit.netguard import PassDeadline
from deskkit.gates import market_condition_gate, window_gate, price_cap_gate, run_gates, ALLOW
from deskkit.quotes import reference_price
from deskkit.datahub import DataHub, Missing
from deskkit.reservation import ShareReservations, StandDown, pinned_stop, settle_date, LatestWins
from datetime import date
from deskkit.scheduler import next_boundary, due_slot, guaranteed_pass_needed, order_tick


class T(unittest.TestCase):
    def tmp(self):
        return tempfile.mkdtemp()

    def test_ids_are_restart_stable_and_short(self):
        k1 = signal_key("s1", "spy", "2026-01-02T15:55", "entry", "buy")
        k2 = signal_key("s1", "SPY", "2026-01-02T15:55", "entry", "buy")
        self.assertEqual(k1, k2)
        c = client_order_id("dsk", k1)
        self.assertEqual(c, client_order_id("dsk", k2))
        self.assertLessEqual(len(c), 48)
        self.assertNotEqual(c, client_order_id("dsk", k1, attempt=1))

    def test_ledger_append_only_and_chain(self):
        L = Ledger(os.path.join(self.tmp(), "l.sqlite"))
        L.append("fill", {"sleeve": "a", "symbol": "X", "side": "buy", "qty": 5})
        with self.assertRaises(sqlite3.DatabaseError):
            L.db.execute("UPDATE events SET kind='x'")
        with self.assertRaises(sqlite3.DatabaseError):
            L.db.execute("DELETE FROM events")
        self.assertTrue(L.verify_chain())
        self.assertEqual(L.positions(), {("a", "X"): 5})

    def test_fsm_illegal(self):
        p = Position("s", "X")
        with self.assertRaises(IllegalTransition):
            p.to("exiting")
        p.to("pending"); p.to("open"); p.to("exiting"); p.to("flat")

    def test_store_merge_keeps_foreign_lot_added_during_pass(self):
        S = StateStore(os.path.join(self.tmp(), "state.json"))
        S.save({"lots": {"a": {"source": "primary"}}, "seen": []})
        mine = S.load()                                      # main loop starts a pass with an in-memory copy
        S.update(lambda st: st["lots"].update({"b": {"source": "failover"}}))   # standby adopts a lot meanwhile
        S.save(mine)                                         # main loop saves its OLD copy
        self.assertIn("b", S.load()["lots"])                 # adopted lot survived

    def test_store_concurrent_updates_do_not_lose_writes(self):
        S = StateStore(os.path.join(self.tmp(), "state.json"))
        def work(i):
            for j in range(20):
                S.update(lambda st: st["lots"].update({f"{i}-{j}": {"source": "primary"}}))
        ths = [threading.Thread(target=work, args=(i,)) for i in range(4)]
        [t.start() for t in ths]; [t.join() for t in ths]
        # flock is per open-file-description, threads each open their own handle -> excluded
        self.assertEqual(len(S.load()["lots"]), 80)

    def test_tick_round_never_crosses_cap(self):
        self.assertEqual(tick_round(62.4766, "buy", cap=62.475), 62.47)
        self.assertEqual(tick_round(0.123456, "buy"), 0.1234)
        self.assertEqual(tick_round(10.011, "sell"), 10.02)

    def test_caps_queued_hold_slots_and_release(self):
        l = Lane("a", 2, 2000, open_positions=1)
        l.take()
        self.assertFalse(l.can_take())
        l.release()
        self.assertTrue(l.can_take())
        r = budget_vs_capacity([Lane("a", 1, 150_000), Lane("b", 1, 120_000)], 180_000)
        self.assertTrue(r["alert"])

    def test_heartbeat_failover(self):
        now = 10_000.0
        self.assertFalse(standby_should_trade({"epoch": now - 60}, now))
        self.assertTrue(standby_should_trade({"epoch": now - 700}, now))
        self.assertFalse(standby_should_trade({"epoch": now - 700}, now, market_open=False))
        self.assertTrue(keepalive_ok(5, 6, 5000))             # old heartbeat but progress moved
        self.assertFalse(keepalive_ok(5, 5, 5000))

    def test_reconcile_tolerates_pending(self):
        self.assertEqual(reconcile({"X": 10}, {"X": 15}, pending_buy={"X": 5}), [])
        self.assertEqual(len(reconcile({"X": 10}, {"X": 16}, pending_buy={"X": 5})), 1)
        o = [{"client_order_id": "dsk-1"}, {"client_order_id": "manual-2"}]
        self.assertEqual(orphans(o, set(), ("dsk-",)), [o[0]])

    def test_jump_detector_quiet(self):
        self.assertEqual(JumpDetector().check(), 0.0)

    def test_pass_deadline(self):
        self.assertTrue(PassDeadline(-1).expired())

    def _desk(self, marks, sleeves, lanes):
        L = Ledger(os.path.join(self.tmp(), "l.sqlite"))
        return Desk(L, ShadowBroker(marks), Alerts(L), sleeves, lanes, marks.get), L

    class S:
        name = "s1"
        def __init__(self, entries=(), exits=()): self._e, self._x = list(entries), list(exits)
        def entries(self): return self._e
        def exits(self): return self._x

    def test_restart_does_not_reenter(self):
        it = dict(sleeve="s1", symbol="X", bar_ts="2026-01-02T15:55", kind="entry", side="buy", qty=3)
        d, L = self._desk({"X": 10.0}, [self.S([it])], {"s1": Lane("s1", 5, 5000)})
        d.run_pass()
        # "restart": brand-new Desk object, same ledger, same signal bar
        d2 = Desk(L, ShadowBroker({"X": 10.0}), Alerts(L), [self.S([it])], {"s1": Lane("s1", 5, 5000)}, {"X": 10.0}.get)
        s = d2.run_pass()
        self.assertEqual(s["orders"], 0)
        self.assertEqual(L.positions(), {("s1", "X"): 3})

    def test_one_bad_sleeve_does_not_abort_pass(self):
        class Bad:
            name = "bad"
            def entries(self): raise ValueError("torn input")
            def exits(self): return []
        it = dict(sleeve="s1", symbol="X", bar_ts="b1", kind="entry", side="buy", qty=1)
        d, L = self._desk({"X": 10.0}, [Bad(), self.S([it])], {"s1": Lane("s1", 5, 5000)})
        s = d.run_pass()
        self.assertEqual((s["errors"], s["orders"]), (1, 1))

    def test_lane_cap_blocks(self):
        its = [dict(sleeve="s1", symbol=f"X{i}", bar_ts="b", kind="entry", side="buy", qty=1) for i in range(3)]
        d, L = self._desk({f"X{i}": 1.0 for i in range(3)}, [self.S(its)], {"s1": Lane("s1", 2, 100)})
        s = d.run_pass()
        self.assertEqual((s["orders"], s["skipped"]), (2, 1))

    def test_exit_without_mark_waits(self):
        it = dict(sleeve="s1", symbol="X", bar_ts="b", kind="exit", side="sell", qty=1)
        d, L = self._desk({}, [self.S(exits=[it])], {"s1": Lane("s1", 2, 100)})
        s = d.run_pass()
        self.assertEqual(s["orders"], 0)
        self.assertTrue(d.alerts.items)


    def test_gates_unknown_waits_even_on_last_day(self):
        self.assertEqual(market_condition_gate(None, -1.0, True).verdict, "wait")
        self.assertEqual(market_condition_gate(-0.5, -1.0, False), ALLOW)
        self.assertEqual(market_condition_gate(0.5, -1.0, True).verdict, "skip")
        self.assertEqual(market_condition_gate(0.5, -1.0, False).verdict, "wait")
        self.assertEqual(window_gate(False, True).verdict, "skip")
        self.assertEqual(price_cap_gate(100, 102.5).verdict, "wait")
        self.assertEqual(run_gates([lambda: ALLOW, lambda: window_gate(False, False)]).why, "not_in_window")

    def test_reference_price_chain_tags_fallbacks(self):
        now = 1000.0
        self.assertEqual(reference_price((10.0, now - 60), None, lambda: None, now), (10.0, "last"))
        self.assertEqual(reference_price((10.0, now - 9000), (9.9, 10.1, now - 30), lambda: None, now), (10.0, "mid"))
        self.assertEqual(reference_price((10.0, now - 9000), (9.0, 11.0, now - 30), lambda: 10.5, now), (10.5, "secondary"))
        self.assertEqual(reference_price(None, None, lambda: None, now), (None, "none"))

    def test_datahub_missing_stale_and_replace(self):
        calls = {"v": 1}
        def loader(sym, tf):
            if sym == "BAD":
                raise RuntimeError("provider down")
            return calls["v"], ["2026-03-02", "2026-03-03"]
        h = DataHub(loader)
        self.assertIsInstance(h.bars("BAD", "1d", "2026-03-04"), Missing)
        self.assertEqual(h.bars("X", "1d", "2026-03-04")[-1], "2026-03-03")
        self.assertEqual(h.bars("X", "1d", "2026-04-04").reason, "stale")
        calls["v"] = 2
        h.bars("X", "1d", "2026-03-04")
        self.assertEqual(len(h._cache), 1)          # BAD never cached; X replaced, not accumulated
        self.assertEqual(h._cache[("X", "1d")][0], 2)

    def test_scheduler_alignment_and_catchup(self):
        b = next_boundary(1000.0)
        self.assertEqual(b % 300, 20)
        self.assertTrue(b > 1000.0)
        self.assertTrue(due_slot(0, 10_000))         # long pause: due once
        self.assertFalse(due_slot(9_990, 10_000))
        self.assertTrue(guaranteed_pass_needed(True, 0, 600))
        self.assertFalse(guaranteed_pass_needed(False, 0, 600))
        self.assertEqual(order_tick(["publish", "pass", "backup"])[0], "pass")

    def test_reservation_standdown_unknown_and_release(self):
        r = ShareReservations()
        r.set_position("A", "X", 100)
        r.reserve("op1", "A", "X", 100, "operator")
        with self.assertRaises(StandDown):
            r.reserve("s1", "A", "X", 10, "sleeve")           # operator holds every share
        r.mark("op1", "UNKNOWN")                                # timeout: reservation persists
        self.assertEqual(r.available("A", "X"), 0)
        r.mark("op1", "REFUSED")                                # reconciled: released
        r.reserve("s1", "A", "X", 10, "sleeve")
        self.assertEqual(r.available("A", "X"), 90)

    def test_pinned_stop_uses_actual_fill(self):
        self.assertEqual(pinned_stop(110.0, 0.10), 99.0)

    def test_settlement_calendar_fails_closed_and_skips_holiday(self):
        cal = {2026: {date(2026, 10, 12)}}
        # Fri 2026-10-09 sale, T+1 -> Mon 12th is a settlement holiday -> Tue 13th
        self.assertEqual(settle_date(date(2026, 10, 9), cal, 1), date(2026, 10, 13))
        with self.assertRaises(KeyError):
            settle_date(date(2026, 12, 31), cal, 1)             # rolls into 2027, no data

    def test_latest_wins_ignores_stale(self):
        lw = LatestWins()
        self.assertTrue(lw.offer(2, "good"))
        self.assertFalse(lw.offer(1, "error"))
        self.assertEqual(lw.value, "good")


if __name__ == "__main__":
    unittest.main()
