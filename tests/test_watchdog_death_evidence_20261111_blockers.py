"""DSK-9 DEATH-EVIDENCE blockers (NO-PARTIALS DRIVE 2026-11-11):
watchdog restart and wedged_terminated rows carried no signal,
exit code, or memory figure, so in-boot deaths were
indistinguishable except by cross-boot inference from boot ids.

Cure: default_launcher retains the Popen handle
(note_launched_child); death rows reap a retained child and carry
exit_code / exit_signal / child_peak_rss_kb (_death_evidence);
adopted (non-child) runners cannot be waited, so the watchdog
samples /proc VmHWM each pass into state/watchdog_mem.json and the
death row carries last_vmhwm_kb instead. Both evidence forms are
named as what they are.

Fail direction on the pre-cure tree: watchdog has no
_death_evidence / note_launched_child at all (ImportError).
"""
import os, signal, subprocess, sys, time, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3 import watchdog


class TestDeathEvidence(unittest.TestCase):

    def tearDown(self):
        watchdog._CHILDREN.clear()

    def test_normal_exit_carries_exit_code(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", "import sys; sys.exit(3)"])
        proc.wait(timeout=10)
        watchdog.note_launched_child(proc.pid, proc)
        ev = watchdog._death_evidence(proc.pid)
        self.assertEqual(ev.get("exit_code"), 3, ev)
        self.assertNotIn("exit_signal", ev)
        self.assertGreater(ev.get("child_peak_rss_kb", 0), 0, ev)

    def test_signal_death_carries_the_signal(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"])
        watchdog.note_launched_child(proc.pid, proc)
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=10)
        ev = watchdog._death_evidence(proc.pid)
        self.assertEqual(ev.get("exit_signal"), 9, ev)
        self.assertNotIn("exit_code", ev)

    def test_adopted_pid_has_no_wait_evidence(self):
        # A pid this process never launched: no handle, no fields;
        # the VmHWM sample is its only memory evidence (below).
        self.assertEqual(watchdog._death_evidence(999999), {})

    def test_vmhwm_reader_reads_a_live_process(self):
        kb = watchdog._pid_vmhwm_kb(os.getpid())
        self.assertIsNotNone(kb)
        self.assertGreater(kb, 0)


if __name__ == "__main__":
    unittest.main()
