"""Blockers: always-on supervision (H21/H22, HARDEN always-on phase).

The watchdog verifies the runner by EFFECTS (its own heartbeat file +
the pid's live cmdline), relaunches it detached when proven down,
journals every restart, and stops at a restart-intensity cap with a
named DEGRADED state (R-ADOPT-1/2). Fail direction: without
desk3/watchdog.py every test errors at import.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import watchdog  # noqa: E402

NOW = datetime(2026, 10, 25, 3, 0, 0, tzinfo=timezone.utc)


def mkroot(test, hb=None, alive=False):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    state = os.path.join(root, "state")
    os.makedirs(state)
    if hb is not None:
        with open(os.path.join(state, "runner.json"), "w") as fh:
            json.dump(hb, fh)
    test.addCleanup(lambda: __import__("shutil").rmtree(root, True))
    return root, state


def hb(age_s, pid=999999, cycle=7, mode="evaluate-only"):
    return {"pid": pid, "cycle": cycle, "mode": mode,
            "ts": (NOW - timedelta(seconds=age_s)).isoformat()}


class Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, root, mode):
        self.calls.append((root, mode))
        return 424242


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self._alive = watchdog.pid_alive_desk
        self.addCleanup(setattr, watchdog, "pid_alive_desk", self._alive)

    def test_healthy_runner_is_never_relaunched(self):
        root, state = mkroot(self, hb(30))
        watchdog.pid_alive_desk = lambda pid: True
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(L.calls, [])  # no duplicate runner, ever

    def test_dead_pid_is_relaunched_and_journaled(self):
        root, state = mkroot(self, hb(30))
        watchdog.pid_alive_desk = lambda pid: False
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(len(L.calls), 1)
        rows = [json.loads(x) for x in open(os.path.join(state, "watchdog.jsonl"))]
        self.assertEqual(rows[-1]["event"], "restart")
        self.assertEqual(rows[-1]["old_pid"], 999999)
        self.assertEqual(rows[-1]["new_pid"], 424242)

    def test_stale_heartbeat_is_relaunched_even_if_pid_alive(self):
        # SUPERSEDED by AUDIT-CURE 2026-10-25 (A-01/A-02): this test
        # encoded the defect — relaunching BESIDE a live pid created
        # duplicate runners (live: 970 + 2520 racing the same state).
        # New law: a stale-but-alive runner inside WEDGED_S is named
        # stale_but_alive and NEVER duplicated; beyond WEDGED_S it is
        # terminated (verified dead) first, then relaunched once.
        root, state = mkroot(self, hb(watchdog.GRACE_S + 120))
        watchdog.pid_alive_desk = lambda pid: True
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={999999})
        self.assertEqual(row["status"], "stale_but_alive")
        self.assertIn("heartbeat_stale", row["reason"])
        self.assertEqual(L.calls, [])

    def test_missing_heartbeat_is_relaunched(self):
        root, state = mkroot(self, None)
        L = Launcher()
        # AUDIT-CURE 2026-10-25: live_pids pinned empty — on a live box
        # the A-01 guard correctly refuses to launch beside the real
        # runner, which is not what this test exercises.
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids=set())
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(row["reason"], "no_heartbeat")

    def test_restart_cap_trips_named_degraded_mode(self):
        # R-ADOPT-1: beyond MAX_RESTARTS in the window, no respawn —
        # the failure is named DEGRADED instead of looping forever.
        root, state = mkroot(self, hb(30))
        watchdog.pid_alive_desk = lambda pid: False
        with open(os.path.join(state, "watchdog.jsonl"), "w") as fh:
            for i in range(watchdog.MAX_RESTARTS):
                fh.write(json.dumps({"event": "restart",
                                     "ts": (NOW - timedelta(seconds=60 * (i + 1))).isoformat(),
                                     "old_pid": 1, "new_pid": 2}) + "\n")
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(row["status"], "degraded")
        self.assertEqual(L.calls, [])
        status = json.load(open(os.path.join(state, "watchdog.json")))
        self.assertEqual(status["status"], "degraded")

    def test_dispatch_mode_is_preserved_on_relaunch(self):
        root, state = mkroot(self, hb(30, mode="dispatch"))
        watchdog.pid_alive_desk = lambda pid: False
        L = Launcher()
        watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(L.calls[0][1], "dispatch")

    def test_launched_runner_in_first_cycle_is_not_relaunched(self):
        # HARDEN-WD1 (live 2026-10-25): the heartbeat still names the
        # dead pid while the relaunched runner runs its first (long)
        # cycle — judging by the stale file stormed 3 runners. The
        # launched pid, alive and inside launch grace, is 'starting'.
        root, state = mkroot(self, hb(30))
        watchdog._write_launched(state, 555, "evaluate-only",
                                 NOW - timedelta(seconds=60))
        watchdog.pid_alive_desk = lambda pid: pid == 555
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(row["status"], "starting")
        self.assertEqual(L.calls, [])

    def test_launched_runner_past_launch_grace_is_relaunched(self):
        root, state = mkroot(self, hb(30))
        watchdog._write_launched(
            state, 555, "evaluate-only",
            NOW - timedelta(seconds=watchdog.LAUNCH_GRACE_S + 60))
        watchdog.pid_alive_desk = lambda pid: pid == 555
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW)
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(row["reason"], "launched_no_heartbeat")
        self.assertEqual(len(L.calls), 1)

    def test_degraded_is_journaled_once_not_per_check(self):
        root, state = mkroot(self, hb(30))
        watchdog.pid_alive_desk = lambda pid: False
        with open(os.path.join(state, "watchdog.jsonl"), "w") as fh:
            for i in range(watchdog.MAX_RESTARTS):
                fh.write(json.dumps({"event": "restart",
                                     "ts": (NOW - timedelta(seconds=60 * (i + 1))).isoformat(),
                                     "old_pid": 1, "new_pid": 2}) + "\n")
        L = Launcher()
        watchdog.check_once(root, launcher=L, now=NOW)
        watchdog.check_once(root, launcher=L,
                            now=NOW + timedelta(seconds=30))
        rows = [json.loads(x) for x in open(os.path.join(state, "watchdog.jsonl"))]
        self.assertEqual(sum(1 for r in rows if r["event"] == "degraded"), 1)

    def test_systemd_unit_keeps_watchdog_alive_across_reboots(self):
        # HARDEN-WD2: a VM reboot kills every userspace process; the
        # boot-enabled unit is the only honest cure. The canonical
        # unit lives in the repo; the installed copy derives from it.
        path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))),
            "desk3", "systemd", "muse-desk-v3-watchdog.service")
        unit = open(path).read()
        self.assertIn("ExecStart=/usr/bin/python3 -u -m desk3.watchdog --loop", unit)
        self.assertIn("Restart=always", unit)
        self.assertIn("KillMode=process", unit)  # never cgroup-kill the runner
        self.assertIn("WantedBy=multi-user.target", unit)

    def test_pid_check_reads_the_pids_own_cmdline(self):
        # Effects-based: a real non-runner pid is not 'alive', and a
        # nonsense pid is not either — no pattern self-matching.
        self.assertFalse(watchdog.pid_alive_desk(os.getpid()))
        self.assertFalse(watchdog.pid_alive_desk(99999999))
        self.assertFalse(watchdog.pid_alive_desk(None))


if __name__ == "__main__":
    unittest.main()
