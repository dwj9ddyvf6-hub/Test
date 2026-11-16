"""EGRESS-2 blockers: boot-persistent supervision for muse-desk-v3.

Route A (systemd USER unit) was evaluated and rejected with evidence
on this platform: systemd-logind and dbus are inactive (dead),
/run/user/<uid> does not exist, `systemctl --user` fails with
'Failed to connect to bus: No medium found', loginctl cannot reach
the bus, and the guest boots a minimal default.target — there is no
user manager to enable, and linger depends on the absent logind.

Chosen route B: a Muse-layer hook guardian. Its canonical script
lives in the repo (desk3/systemd/v3_supervision_guardian.sh) and is
installed byte-identically under ~/hooks/scripts/ (home persists
across VM replacements; /etc does not). The script is silent when
supervision is healthy; on absence it reinstalls the canonical
system unit, daemon-reloads, enables, starts, and verifies by
effects; it wakes an agent only when its own heal fails.
"""
import os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, "desk3", "systemd", "v3_supervision_guardian.sh")
README = os.path.join(ROOT, "desk3", "systemd", "README.md")
UNIT = os.path.join(ROOT, "desk3", "systemd", "muse-desk-v3-watchdog.service")
CANON_UNIT = "/home/hatch/workspace/muse-desk-v3/desk3/systemd/muse-desk-v3-watchdog.service"


class TestGuardianArtifacts(unittest.TestCase):
    def setUp(self):
        with open(GUARD) as fh:
            self.guard = fh.read()
        with open(README) as fh:
            self.readme = fh.read()
        with open(UNIT) as fh:
            self.unit = fh.read()

    def test_guardian_reinstalls_from_canonical_repo_copy(self):
        self.assertIn(CANON_UNIT, self.guard)
        self.assertIn("/etc/systemd/system/muse-desk-v3-watchdog.service", self.guard)
        self.assertIn("daemon-reload", self.guard)
        self.assertIn("systemctl enable", self.guard)
        self.assertIn("systemctl start", self.guard)

    def test_guardian_silent_when_healthy_and_wakes_only_on_failed_heal(self):
        self.assertIn('silent "v3 supervision healthy', self.guard)
        self.assertIn("wake ", self.guard)
        # dry runs never heal / never write install state
        self.assertIn("HATCH_HOOK_DRY_RUN", self.guard)

    def test_guardian_verifies_by_effects_not_self_matching_pattern(self):
        # health is proven from the watchdog's own status file +
        # health.json freshness + systemctl is-active, never pgrep -f
        self.assertIn("watchdog.json", self.guard)
        self.assertIn("health.json", self.guard)
        self.assertIn("is-active", self.guard)
        self.assertNotIn("pgrep -f", self.guard)

    def test_guardian_single_healer_flock(self):
        self.assertIn("flock", self.guard)

    def test_no_credential_values_in_guardian_or_readme(self):
        for text in (self.guard, self.readme):
            self.assertNotIn("://", text.replace("sandbox://", ""))
            for token in ("HTTP_PROXY=", "HTTPS_PROXY=", "ALL_PROXY="):
                self.assertNotIn(token, text)
        # egress config referenced by path only
        self.assertIn("/etc/environment.d/80-hatch-egress.conf", self.readme)

    def test_readme_documents_route_a_rejection_and_rebuild(self):
        for token in ("Route A", "No medium found", "systemd-logind",
                      "Route B", "v3-supervision-guardian",
                      "Simulated wipe", "EGRESS-2"):
            self.assertIn(token, self.readme)

    def test_unit_still_carries_egress1_lines(self):
        self.assertIn("EnvironmentFile=-/etc/environment.d/80-hatch-egress.conf", self.unit)
        self.assertIn("Environment=HOME=/home/hatch", self.unit)


if __name__ == "__main__":
    unittest.main()
