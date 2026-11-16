"""Blockers: A9 Monday flip (A9-FLIP-20261025).

Before this cure the desk's mode was decided ONLY by the `--dispatch`
argv flag at runner launch and the watchdog preserved the recorded
mode forever, so Monday 2026-10-26's live RTH paper session depended
on a human remembering OPERATIONS.md's manual relaunch. The watchdog
now owns the flip via desired_mode() (dispatch from FLIP_AT =
Mon 2026-10-26 13:25 UTC = 09:25 ET) plus the first-fill broker
read-back into state/a9_first_fill.json.

Fail direction: without the watchdog cure, desired_mode / FLIP_AT /
a9_readback do not exist and every test errors/fails; the pre-flip
preservation tests pin that behavior BEFORE the boundary is exactly
the old behavior.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import watchdog  # noqa: E402

BEFORE = datetime(2026, 10, 25, 20, 0, 0, tzinfo=timezone.utc)   # Sun eve ET
AT = datetime(2026, 10, 26, 13, 25, 0, tzinfo=timezone.utc)       # Mon 09:25 ET
AFTER = datetime(2026, 10, 26, 13, 26, 0, tzinfo=timezone.utc)
OPEN = datetime(2026, 10, 26, 13, 30, 0, tzinfo=timezone.utc)      # Mon 09:30 ET


def mkroot(test, hb=None):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    state = os.path.join(root, "state")
    os.makedirs(state)
    if hb is not None:
        with open(os.path.join(state, "runner.json"), "w") as fh:
            json.dump(hb, fh)
    test.addCleanup(lambda: __import__("shutil").rmtree(root, True))
    return root, state


def hb(now, age_s=30, pid=999999, mode="evaluate-only"):
    return {"pid": pid, "cycle": 7, "mode": mode,
            "ts": (now - timedelta(seconds=age_s)).isoformat()}


class Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, root, mode):
        self.calls.append((root, mode))
        return 424242


class Killer:
    def __init__(self, ok=True):
        self.calls = []
        self.ok = ok

    def __call__(self, pid):
        self.calls.append(pid)
        return self.ok


class FakeDoor:
    def __init__(self, order=None, positions=None):
        self.order = order or {"status": "filled", "filled_qty": 2,
                               "filled_avg_price": 501.25}
        self.positions = positions or {"QQQ": 2.0}
        self.reads = []

    def get_order_by_client_id(self, coid):
        self.reads.append(coid)
        return dict(self.order)

    def get_positions(self):
        return dict(self.positions)


def journal_events(state, name="watchdog.jsonl"):
    path = os.path.join(state, name)
    if not os.path.exists(path):
        return []
    return [json.loads(x) for x in open(path).read().splitlines() if x.strip()]


class DesiredModeTests(unittest.TestCase):
    def test_flip_at_is_monday_0925_et(self):
        self.assertEqual(watchdog.FLIP_AT, AT)

    def test_boundary_drive_weekend_to_monday_open(self):
        # The predicate traced across the boundary: weekend and
        # Monday pre-09:25 ET preserve the recorded mode; 09:25 ET
        # and the 09:30 open are dispatch.
        for now in (datetime(2026, 10, 24, 16, 0, tzinfo=timezone.utc),
                    datetime(2026, 10, 25, 23, 59, tzinfo=timezone.utc),
                    datetime(2026, 10, 26, 13, 24, 59, tzinfo=timezone.utc)):
            self.assertEqual(watchdog.desired_mode(now, "evaluate-only"),
                             "evaluate-only")
            self.assertEqual(watchdog.desired_mode(now, None),
                             "evaluate-only")
            self.assertEqual(watchdog.desired_mode(now, "dispatch"),
                             "dispatch")
        for now in (AT, OPEN, datetime(2026, 10, 26, 20, 0,
                                        tzinfo=timezone.utc)):
            self.assertEqual(watchdog.desired_mode(now, "evaluate-only"),
                             "dispatch")
            self.assertEqual(watchdog.desired_mode(now, None), "dispatch")


class FlipTests(unittest.TestCase):
    def setUp(self):
        self._alive = watchdog.pid_alive_desk
        self.addCleanup(setattr, watchdog, "pid_alive_desk", self._alive)
        watchdog.pid_alive_desk = lambda pid: True

    def test_healthy_eval_runner_before_flip_is_untouched(self):
        root, state = mkroot(self, hb(BEFORE))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, killer=K, now=BEFORE,
                                  live_pids={999999})
        self.assertEqual(row["status"], "ok")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_healthy_eval_runner_after_flip_is_flipped_to_dispatch(self):
        root, state = mkroot(self, hb(AFTER))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, killer=K, now=AFTER,
                                  live_pids={999999})
        self.assertEqual(row["status"], "flipped")
        self.assertEqual(row["action"], "flip")
        self.assertEqual(K.calls, [999999])          # old runner killed first
        self.assertEqual(L.calls, [(root, "dispatch")])
        flips = [e for e in journal_events(state)
                 if e.get("event") == "mode_flip"]
        self.assertEqual(len(flips), 1)
        self.assertEqual(flips[0]["from_mode"], "evaluate-only")
        self.assertEqual(flips[0]["to_mode"], "dispatch")
        self.assertEqual(flips[0]["new_pid"], 424242)
        launched = json.load(open(os.path.join(state,
                                               "watchdog_launched.json")))
        self.assertEqual(launched["mode"], "dispatch")

    def test_healthy_dispatch_runner_after_flip_is_untouched(self):
        root, state = mkroot(self, hb(AFTER, mode="dispatch"))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, killer=K, now=AFTER,
                                  live_pids={999999})
        self.assertEqual(row["status"], "ok")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_flip_blocked_by_stranger_runner(self):
        root, state = mkroot(self, hb(AFTER))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, killer=K, now=AFTER,
                                  live_pids={999999, 555})
        self.assertEqual(row["status"], "flip_blocked_duplicate")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_flip_aborts_when_runner_cannot_be_terminated(self):
        root, state = mkroot(self, hb(AFTER))
        L, K = Launcher(), Killer(ok=False)
        row = watchdog.check_once(root, launcher=L, killer=K, now=AFTER,
                                  live_pids={999999})
        self.assertEqual(row["status"], "degraded")
        self.assertEqual(L.calls, [])  # never a duplicate beside a live runner

    def test_dead_runner_after_flip_relaunches_dispatch(self):
        root, state = mkroot(self, hb(AFTER))
        watchdog.pid_alive_desk = lambda pid: False
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=AFTER, live_pids=set())
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(L.calls, [(root, "dispatch")])

    def test_dead_runner_before_flip_relaunches_recorded_mode(self):
        root, state = mkroot(self, hb(BEFORE))
        watchdog.pid_alive_desk = lambda pid: False
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=BEFORE, live_pids=set())
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(L.calls, [(root, "evaluate-only")])


FILL_PRE = {"event": "fill", "intent_id": "i-pre", "sleeve": "saty_day",
            "client_order_id": "v3-saty_day-i-pre", "symbol": "QQQ",
            "side": "buy", "qty": 1, "price": 500.0,
            "ts": "2026-10-25T15:00:00+00:00"}
FILL_POST = {"event": "fill", "intent_id": "i-post", "sleeve": "po10_qqq",
             "client_order_id": "v3-po10_qqq-i-post", "symbol": "QQQ",
             "side": "buy", "qty": 2, "price": 501.0,
             "ts": "2026-10-26T13:31:00+00:00"}


class ReadbackTests(unittest.TestCase):
    def _root_with_fills(self, fills):
        root, state = mkroot(self)
        with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
            for f in fills:
                fh.write(json.dumps(f) + "\n")
        return root, state

    def test_no_post_flip_fill_no_proof(self):
        root, state = self._root_with_fills([FILL_PRE])
        door = FakeDoor()
        self.assertIsNone(watchdog.a9_readback(state, now=AFTER, door=door))
        self.assertFalse(os.path.exists(os.path.join(state,
                                                     "a9_first_fill.json")))
        self.assertEqual(door.reads, [])

    def test_first_post_flip_fill_read_back_from_broker(self):
        root, state = self._root_with_fills([FILL_PRE, FILL_POST])
        door = FakeDoor()
        proof = watchdog.a9_readback(state, now=AFTER, door=door)
        self.assertEqual(proof["verdict"], "FILLED_READ_BACK")
        self.assertEqual(proof["client_order_id"], "v3-po10_qqq-i-post")
        self.assertEqual(proof["broker_status"], "filled")
        self.assertEqual(proof["broker_filled_qty"], 2.0)
        self.assertEqual(proof["broker_filled_avg_price"], 501.25)
        self.assertEqual(proof["broker_position_qty"], 2.0)
        self.assertEqual(door.reads, ["v3-po10_qqq-i-post"])
        on_disk = json.load(open(os.path.join(state, "a9_first_fill.json")))
        self.assertEqual(on_disk, proof)
        ev = [e for e in journal_events(state)
              if e.get("event") == "a9_first_fill_readback"]
        self.assertEqual(len(ev), 1)
        # Exactly once: a second pass returns the stored proof and
        # does not read the broker again.
        again = watchdog.a9_readback(state, now=AFTER, door=door)
        self.assertEqual(again, proof)
        self.assertEqual(door.reads, ["v3-po10_qqq-i-post"])

    def test_ack_is_not_a_fill(self):
        root, state = self._root_with_fills([FILL_POST])
        door = FakeDoor(order={"status": "accepted", "filled_qty": 0,
                               "filled_avg_price": None},
                        positions={})
        proof = watchdog.a9_readback(state, now=AFTER, door=door)
        self.assertEqual(proof["verdict"], "SUBMITTED_NOT_FILLED")
        self.assertEqual(proof["broker_status"], "accepted")


if __name__ == "__main__":
    unittest.main()
