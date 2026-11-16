"""RUNNER-DEATH-CLASS-20261116 blocker.

Live defect, Sunday 2026-11-15: the watchdog journaled 16 runner
restarts, every one as the same unexplained reason pid_dead.
Counted afterward from the rows' own boot_id fields, 13 restarts
carried a boot_id different from the previous restart row: the
runner had died WITH the host at the platform's roughly hourly
boot cadence, and the incoming watchdog's recovery relaunch was
recorded as an unexplained runner death. The other 3 were
same-boot deaths by SIGTERM (exit_signal 15) during the night's
landing activity. One undifferentiated count made a platform
cadence look like a dying runner and hid the real deaths inside
it.

Cure: every restart row now carries death_class and prev_boot_id,
derived at journal time from the journal's own boot evidence:
host_boot_recovery when the boot changed since the last journaled
boot evidence, same_boot_death when it did not, and
unclassified_no_prior_boot when no prior evidence exists. The
relaunch behavior itself is unchanged.

Fail direction: on the pre-cure tree restart rows carry no
death_class at all, so every assertion on it fails.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3 import watchdog  # noqa: E402

NOW = datetime(2026, 11, 16, 15, 0, tzinfo=timezone.utc)


def _root(prior_boot=None):
    root = tempfile.mkdtemp()
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "runner.json"), "w") as fh:
        json.dump({"pid": 999999, "cycle": 7, "mode": "dispatch",
                   "ts": "2026-11-16T14:00:00+00:00"}, fh)
    if prior_boot is not None:
        with open(os.path.join(state, "watchdog.jsonl"), "w") as fh:
            fh.write(json.dumps(
                {"event": "restart", "ts": "2026-11-16T13:00:00+00:00",
                 "reason": "pid_dead", "old_pid": 111, "new_pid": 999999,
                 "boot_id": prior_boot}) + "\n")
    return root


def _restart_row(root):
    rows = [json.loads(l) for l in
            open(os.path.join(root, "state", "watchdog.jsonl"))]
    return [r for r in rows if r.get("event") == "restart"][-1]


class TestDeathClass(unittest.TestCase):
    def _check(self, root, boot):
        orig = watchdog._boot_id
        watchdog._boot_id = lambda: boot
        try:
            return watchdog.check_once(
                root=root, launcher=lambda r, m: 4242, now=NOW,
                live_pids=set())
        finally:
            watchdog._boot_id = orig

    def test_boot_change_is_host_boot_recovery(self):
        root = _root(prior_boot="boot-A")
        out = self._check(root, "boot-B")
        self.assertEqual(out["status"], "restarted")
        row = _restart_row(root)
        self.assertEqual(row["death_class"], "host_boot_recovery")
        self.assertEqual(row["prev_boot_id"], "boot-A")
        self.assertEqual(row["boot_id"], "boot-B")
        self.assertEqual(out["death_class"], "host_boot_recovery")

    def test_same_boot_is_same_boot_death(self):
        root = _root(prior_boot="boot-A")
        out = self._check(root, "boot-A")
        row = _restart_row(root)
        self.assertEqual(row["death_class"], "same_boot_death")
        self.assertEqual(row["prev_boot_id"], "boot-A")

    def test_no_prior_boot_evidence_is_named_unclassified(self):
        root = _root(prior_boot=None)
        out = self._check(root, "boot-B")
        row = _restart_row(root)
        self.assertEqual(row["death_class"],
                         "unclassified_no_prior_boot")
        self.assertIsNone(row["prev_boot_id"])

    def test_death_class_helper_directly(self):
        root = _root(prior_boot="boot-A")
        state = os.path.join(root, "state")
        self.assertEqual(watchdog._death_class(state, "boot-B"),
                         ("host_boot_recovery", "boot-A"))
        self.assertEqual(watchdog._death_class(state, "boot-A"),
                         ("same_boot_death", "boot-A"))


if __name__ == "__main__":
    unittest.main()
