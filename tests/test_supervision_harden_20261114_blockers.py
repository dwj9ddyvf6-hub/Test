"""SUPERVISION-HARDEN-20261114 blockers (Lane 5, runner supervision).

Context: the runner died and was watchdog-relaunched 10x Friday
2026-11-13 plus 3x overnight; every death traces to a VM/cell
restart (watchdog.jsonl boot_ids differ per restart). The chosen
route is hardening the existing supervision (route 2): systemd
already supervises the watchdog (enabled, WantedBy=
multi-user.target) and the watchdog relaunches the runner ~30 s
after each boot (five journaled proofs Sat 2026-11-14). A second
supervisor for the runner itself (route 1) would fight the
watchdog's relaunch and cannot express its mode-flip, launch-hold
or restart-intensity semantics. The gaps in route 2 were: the
watchdog unit had no watchdog keep-alive (a wedged loop looked
alive forever) and no start limit (a crash-loop respawned
silently forever).

Cure: desk3.watchdog sends sd_notify READY=1 / WATCHDOG=1 after
each completed check pass (no-op off systemd); the unit becomes
Type=notify with WatchdogSec=120 and a start limit.

Fail direction: pre-cure, _sd_notify does not exist and the unit
carries none of the three settings; these tests fail.
"""
import os
import socket
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestSdNotify(unittest.TestCase):
    def test_notify_is_noop_without_socket_env(self):
        from desk3 import watchdog
        old = os.environ.pop("NOTIFY_SOCKET", None)
        try:
            watchdog._sd_notify("WATCHDOG=1")  # must not raise
        finally:
            if old is not None:
                os.environ["NOTIFY_SOCKET"] = old

    def test_notify_delivers_datagram(self):
        from desk3 import watchdog
        path = os.path.join(tempfile.mkdtemp(), "notify.sock")
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        srv.bind(path)
        srv.settimeout(5)
        old = os.environ.get("NOTIFY_SOCKET")
        os.environ["NOTIFY_SOCKET"] = path
        try:
            watchdog._sd_notify("WATCHDOG=1")
            data, _ = srv.recvfrom(1024)
        finally:
            if old is None:
                os.environ.pop("NOTIFY_SOCKET", None)
            else:
                os.environ["NOTIFY_SOCKET"] = old
            srv.close()
        self.assertEqual(data, b"WATCHDOG=1")

    def test_loop_pings_after_completed_pass(self):
        src = open(os.path.join(ROOT, "desk3", "watchdog.py")).read()
        loop = src[src.index("# --loop"):]
        self.assertIn('_sd_notify("READY=1")', loop)
        self.assertIn('_sd_notify("WATCHDOG=1")', loop)
        # the ping follows check_once in the loop body
        self.assertLess(loop.index("check_once(ROOT)"),
                        loop.index('_sd_notify("WATCHDOG=1")'))


class TestUnitFile(unittest.TestCase):
    def test_unit_carries_hardening(self):
        unit = open(os.path.join(
            ROOT, "desk3", "systemd",
            "muse-desk-v3-watchdog.service")).read()
        self.assertIn("Type=notify", unit)
        self.assertIn("WatchdogSec=120", unit)
        self.assertIn("StartLimitBurst=10", unit)
        self.assertIn("StartLimitIntervalSec=600", unit)
        # preserved semantics: one supervisor for the runner, the
        # watchdog; the runner is never cgroup-killed by this unit
        self.assertIn("KillMode=process", unit)
        self.assertIn("WantedBy=multi-user.target", unit)
        self.assertIn("desk3.watchdog --loop", unit)


if __name__ == "__main__":
    unittest.main()
