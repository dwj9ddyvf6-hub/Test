#!/usr/bin/env python3
"""Regression harness skeleton: one command, PASS/WARN/FAIL/SKIP, SKIP never counts as PASS.

Add groups as you grow. A bug-log row that names a blocker must map to a check here (see check_bug_log_blockers).
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPS = {
    "unit": (["python3", "-m", "unittest", "discover", "-s", "tests"], "fail"),
    "example_runs": (["python3", "examples/run_example.py"], "fail"),
}


def check_bug_log_blockers(path="BUG_LOG.md", tests_dir="tests"):
    """Every `backticked` blocker named in the bug log must exist as a test function/name somewhere."""
    if not os.path.exists(path):
        return "SKIP", "no BUG_LOG.md yet"
    names = set(re.findall(r"`([A-Za-z0-9_:.\-]+)`", open(path).read()))
    corpus = "".join(open(os.path.join(d, f), errors="ignore").read()
                     for d, _, fs in os.walk(tests_dir) for f in fs if f.endswith(".py"))
    missing = sorted(n for n in names if n not in corpus)
    return ("PASS", "") if not missing else ("FAIL", f"blockers not found in tests: {missing[:5]}")


def main():
    res = {}
    for name, (cmd, sev) in GROUPS.items():
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        res[name] = ("PASS", "") if r.returncode == 0 else ("FAIL" if sev == "fail" else "WARN", r.stderr[-300:])
    res["bug_log_blockers"] = check_bug_log_blockers(os.path.join(ROOT, "BUG_LOG.md"), os.path.join(ROOT, "tests"))
    print(json.dumps(res, indent=1))
    return 1 if any(v[0] == "FAIL" for v in res.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
