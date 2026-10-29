import sqlite3
import hashlib
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.lab import Lab
from backend.store import Store
from scripts.backup import backup
from scripts.restore import restore
from scripts.monitor import inspect_state, probe


class BackupTests(unittest.TestCase):
    def test_restore_uses_only_receipted_bytes_even_with_live_backup_wal(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.sqlite"
            with sqlite3.connect(source) as con:
                con.execute("PRAGMA journal_mode=WAL")
                con.execute("CREATE TABLE facts(value TEXT)")
                con.execute("INSERT INTO facts VALUES('receipted')")
            receipt = backup(source, Path(tmp) / "copies")
            saved = Path(receipt["database"])
            with sqlite3.connect(saved) as writer:
                writer.execute("INSERT INTO facts VALUES('not in receipt')")
                writer.commit()
                self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), receipt["sha256"])
                self.assertTrue(Path(str(saved) + "-wal").exists())
                destination = Path(tmp) / "restored.sqlite"
                restore(saved, destination)
                with sqlite3.connect(destination) as con:
                    self.assertEqual([r[0] for r in con.execute("SELECT value FROM facts")], ["receipted"])

    def test_restore_refuses_sidecars_created_during_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.sqlite"
            Store(source)
            receipt = backup(source, Path(tmp) / "copies")
            destination = Path(tmp) / "restored.sqlite"
            original_connect = sqlite3.connect
            def racing_connect(*args, **kwargs):
                Path(str(destination) + "-wal").write_bytes(b"concurrent desk state")
                return original_connect(*args, **kwargs)
            with patch("scripts.restore.sqlite3.connect", side_effect=racing_connect):
                with self.assertRaises(ValueError):
                    restore(receipt["database"], destination)
            self.assertFalse(destination.exists())
            self.assertEqual(Path(str(destination) + "-wal").read_bytes(), b"concurrent desk state")
            self.assertEqual(list(Path(tmp).glob("*.restore-*.tmp")), [])

    def test_sqlite_backup_keeps_wal_data_and_is_additive(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "desk.sqlite"
            directory = Path(tmp) / "copies"
            lab = Lab(Store(source))
            lab.message({"sender": "operator", "recipient": "all", "topic": "First", "body": "Preserve this evidence"})
            first = backup(source, directory)
            lab.message({"sender": "operator", "recipient": "all", "topic": "Second", "body": "New evidence"})
            second = backup(source, directory)
            self.assertNotEqual(first["database"], second["database"])
            self.assertTrue(Path(first["database"]).exists())
            with sqlite3.connect(first["database"]) as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM lab_messages").fetchone()[0], 1)
                self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            with sqlite3.connect(second["database"]) as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM lab_messages").fetchone()[0], 2)
            self.assertEqual(lab.snapshot()["inbox_total"], 2)

    def test_receipted_restore_preserves_evidence_and_refuses_existing_or_modified_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "desk.sqlite"
            lab = Lab(Store(source))
            lab.message({"sender": "operator", "recipient": "all", "topic": "Evidence", "body": "Preserve original evidence"})
            receipt = backup(source, Path(tmp) / "copies")
            destination = Path(tmp) / "restored.sqlite"
            result = restore(receipt["database"], destination)
            self.assertFalse(result["existing_state_overwritten"])
            self.assertEqual(Lab(Store(destination)).snapshot()["inbox"][0]["body"], "Preserve original evidence")
            self.assertEqual(Store(destination).verify_ledger()["status"], "ok")
            lab.message({"sender": "operator", "recipient": "all", "topic": "Later", "body": "Newer original state"})
            with self.assertRaises(ValueError):
                restore(receipt["database"], source)
            self.assertEqual(lab.snapshot()["inbox_total"], 2)
            with open(receipt["database"], "ab") as handle:
                handle.write(b"modified")
            with self.assertRaises(ValueError):
                restore(receipt["database"], Path(tmp) / "bad.sqlite")
            self.assertFalse((Path(tmp) / "bad.sqlite").exists())


class MonitorTests(unittest.TestCase):
    def state(self, **values):
        return {"runtime": {"heartbeat_at": datetime.now(timezone.utc).isoformat(),
                            "running": True, "worker_alive": True, "healthy": True, **values}}

    def test_fresh_heartbeat_cannot_hide_runtime_gate_or_stall(self):
        self.assertTrue(inspect_state(self.state())["healthy"])
        for values in ({"healthy": False}, {"worker_alive": False}, {"progress_stale": True},
                       {"worker_stale": True}, {"last_error": "provider timeout"}):
            with self.subTest(values=values):
                self.assertFalse(inspect_state(self.state(**values))["healthy"])

    def test_paused_healthy_runtime_is_available_but_bad_timestamps_fail(self):
        self.assertTrue(inspect_state(self.state(running=False, worker_alive=False))["healthy"])
        for stamp in (None, "bad", "2026-10-08T00:00:00", 123,
                      (datetime.now(timezone.utc) - timedelta(seconds=181)).isoformat(),
                      (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()):
            with self.subTest(stamp=stamp):
                self.assertFalse(inspect_state(self.state(heartbeat_at=stamp))["healthy"])

    def test_invalid_monitor_age_is_rejected_before_any_http_request(self):
        with patch("scripts.monitor.urllib.request.urlopen") as transport:
            for age in (0, -1, True, float("nan"), float("inf"), "180"):
                with self.subTest(age=age), self.assertRaises(ValueError):
                    probe("http://unused", age)
            transport.assert_not_called()

    def test_health_endpoint_database_and_task_worker_failures_are_detected(self):
        healthy = {"autonomy": self.state()["runtime"], "database": {"status": "ok"},
                   "journal_integrity": {"status": "ok"}, "worker": {"alive": True, "error": None}}
        self.assertTrue(inspect_state(healthy)["healthy"])
        for key, value in (("database", {"status": "error"}),
                           ("journal_integrity", {"status": "mismatch"}),
                           ("worker", {"alive": False}), ("worker", {"alive": True, "error": "crashed"})):
            with self.subTest(key=key):
                self.assertFalse(inspect_state({**healthy, key: value})["healthy"])


class LauncherTests(unittest.TestCase):
    def test_launcher_reinstalls_frontend_when_dependency_lock_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "run.sh").write_bytes((Path(__file__).resolve().parents[1] / "run.sh").read_bytes())
            (root / ".venv/bin").mkdir(parents=True)
            (root / "frontend/node_modules").mkdir(parents=True)
            (root / "tools").mkdir()
            (root / "requirements-lock.txt").write_text("# isolated launcher fixture\n")
            (root / ".venv/.aster-requirements").write_text(hashlib.sha256((root / "requirements-lock.txt").read_bytes()).hexdigest() + "\n")
            lock = root / "frontend/package-lock.json"
            lock.write_text('{"fixture":1}\n')
            (root / "frontend/node_modules/.aster-package-lock").write_text("old dependency identity\n")
            npm = root / "tools/npm"
            npm.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$ASTER_LAUNCHER_QA_LOG"\n')
            npm.chmod(0o755)
            python = root / ".venv/bin/python"
            python.write_text("#!/bin/sh\nexit 0\n")
            python.chmod(0o755)
            log = root / "commands.log"
            env = {**os.environ, "PATH": str(root / "tools") + os.pathsep + os.environ.get("PATH", ""), "ASTER_LAUNCHER_QA_LOG": str(log)}
            def launch():
                subprocess.run(["bash", str(root / "run.sh")], env=env, check=True, capture_output=True, timeout=10)
            launch()
            self.assertEqual(log.read_text().splitlines(), ["ci --no-audit --no-fund", "run build"])
            launch()
            self.assertEqual(log.read_text().splitlines().count("ci --no-audit --no-fund"), 1)
            lock.write_text('{"fixture":2}\n')
            launch()
            self.assertEqual(log.read_text().splitlines().count("ci --no-audit --no-fund"), 2)
            self.assertEqual((root / "frontend/node_modules/.aster-package-lock").read_text().strip(), hashlib.sha256(lock.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
