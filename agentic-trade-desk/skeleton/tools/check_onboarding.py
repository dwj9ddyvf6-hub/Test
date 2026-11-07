#!/usr/bin/env python3
"""Verify the documented offline scaffold in a clean temporary directory.

Copies the reviewed deskkit, tests and example into the documented top-level
layout, then uses an isolated Python process with no inherited credentials.
The child's audit hook rejects network and subprocess activity. This is a
guard for these bundled examples, not a security sandbox for untrusted code.
No broker, service, repository file or persistent state is changed.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


CHILD = r'''
import contextlib, io, json, pathlib, re, runpy, sys, unittest
root = pathlib.Path.cwd().resolve()
sys.path.insert(0, str(root))

def offline_guard(event, args):
    if event.startswith("socket.") or event in {
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "os.forkpty"
    }:
        raise RuntimeError("Offline onboarding forbids network and child processes: " + event)

sys.addaudithook(offline_guard)
import deskkit
assert pathlib.Path(deskkit.__file__).resolve().is_relative_to(root / "deskkit"), "wrong package imported"
suite = unittest.defaultTestLoader.discover("tests", top_level_dir="tests")
count = suite.countTestCases()
if count == 0:
    raise RuntimeError("No tests discovered: check the scaffold copy layout")
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
test_report = {
    "discovered": count, "run": result.testsRun,
    "failures": len(result.failures), "errors": len(result.errors),
    "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
    "unexpected_successes": len(result.unexpectedSuccesses)
}
if not result.wasSuccessful() or result.testsRun != count or result.skipped or result.expectedFailures:
    print(json.dumps({"status": "FAIL", "tests": test_report, "details": stream.getvalue()}))
    raise SystemExit(1)

output = io.StringIO()
with contextlib.redirect_stdout(output):
    runpy.run_path("examples/run_example.py", run_name="__main__")
text = output.getvalue()
rows = re.findall(r"^(\d{4}-\d{2}-\d{2}) (first process|restarted process)\s+orders=(\d+) skipped=(\d+) errors=(\d+)$", text, re.M)
restarts = [r for r in rows if r[1] == "restarted process"]
example = {
    "passes": len(rows), "simulated_restart_passes": len(restarts),
    "orders": sum(int(r[2]) for r in rows),
    "restart_orders": sum(int(r[2]) for r in restarts),
    "errors": sum(int(r[4]) for r in rows),
    "final_book_flat": "book (replayed from ledger): flat" in text.splitlines(),
    "ledger_chain_valid": "chain ok: True" in text.splitlines()
}
# Independent outcomes of this frozen toy: one entry, one exit, no restart
# duplicates, flat terminal book and a valid append-only chain.
passed = (example["passes"] == 12 and example["simulated_restart_passes"] == 6
          and example["orders"] == 2 and example["restart_orders"] == 0
          and example["errors"] == 0 and example["final_book_flat"]
          and example["ledger_chain_valid"])
print(json.dumps({"status": "PASS" if passed else "FAIL", "tests": test_report,
                  "example": example,
                  "boundary": "Frozen simulated example; no broker, real process-failover or market-performance proof."}))
raise SystemExit(0 if passed else 1)
'''


def main() -> int:
    source = Path(__file__).resolve().parents[1]
    manifest: list[dict[str, str | int]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="deskkit-onboarding-") as temporary:
            destination = Path(temporary)
            for folder in ("deskkit", "tests", "examples"):
                origin = source / folder
                for path in sorted(origin.rglob("*")):
                    if path.is_symlink():
                        raise ValueError("Onboarding source must not contain symlinks")
                    if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                        continue
                    data = path.read_bytes()
                    relative = path.relative_to(source)
                    manifest.append({"path": relative.as_posix(), "bytes": len(data),
                                     "sha256": hashlib.sha256(data).hexdigest()})
                shutil.copytree(origin, destination / folder,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for item in manifest:
                copied = (destination / str(item["path"])).read_bytes()
                if hashlib.sha256(copied).hexdigest() != item["sha256"]:
                    raise ValueError("Source changed during export: " + str(item["path"]))
            (destination / "temporary-state").mkdir()
            # Do not inherit tokens, PYTHONPATH, custom site initialization or
            # broker configuration. -I additionally isolates Python imports.
            environment = {"PATH": os.defpath, "LANG": "C.UTF-8",
                           "TMPDIR": str(destination / "temporary-state")}
            run = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD],
                                 cwd=destination, env=environment, capture_output=True,
                                 text=True, timeout=90, check=False)
            try:
                result = json.loads(run.stdout)
            except json.JSONDecodeError:
                result = {"status": "FAIL", "reason": "Child did not produce a JSON receipt",
                          "details": run.stderr or run.stdout}
            if run.returncode != 0:
                result["status"] = "FAIL"
            result["python"] = sys.version.split()[0]
            result["returncode"] = run.returncode
            result["source_manifest"] = manifest
            result["source_manifest_sha256"] = hashlib.sha256(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            result["verification_script_sha256"] = hashlib.sha256(
                Path(__file__).read_bytes()).hexdigest()
            result["isolation"] = {
                "temporary_export": True, "inherited_credentials": False,
                "network_and_child_process_audit_guard": True,
                "source_tree_modified": False
            }
            print(json.dumps(result, indent=2))
            return 0 if result.get("status") == "PASS" and run.returncode == 0 else 1
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL", "reason": type(exc).__name__,
                          "details": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
