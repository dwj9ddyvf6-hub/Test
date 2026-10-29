#!/usr/bin/env python3
"""Read-only health probe suitable for an independently hosted scheduler.

Exit status 1 means an operator should inspect the desk. This script sends no
messages and cannot restart or trade; run it off the desk's host for detection
of complete host loss.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone


def probe(url, maximum_age=180):
    if isinstance(maximum_age, bool) or not isinstance(maximum_age, (int, float)) or not 1 <= maximum_age <= 86400:
        raise ValueError("maximum_age must be between 1 and 86400 seconds")
    with urllib.request.urlopen(url.rstrip("/") + "/api/health", timeout=10) as response:
        state = json.load(response)
    return inspect_state(state, maximum_age)


def inspect_state(state, maximum_age=180):
    runtime = state.get("autonomy", state.get("runtime", {}))
    status = runtime.get("runtime", runtime)
    heartbeat = status.get("heartbeat_at") or status.get("last_tick_at")
    problems = []
    if not heartbeat:
        problems.append("No autonomous heartbeat recorded")
    else:
        try:
            stamp = datetime.fromisoformat(heartbeat.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("Heartbeat must include a timezone")
            age = (datetime.now(timezone.utc) - stamp).total_seconds()
            if age < -5 or age > maximum_age:
                problems.append("Autonomous heartbeat is outside the allowed age")
        except (ValueError, TypeError, AttributeError):
            problems.append("Autonomous heartbeat is invalid")
    if status.get("running") and status.get("worker_alive") is not True:
        problems.append("Autonomous worker is not alive")
    if status.get("worker_stale") or status.get("progress_stale"):
        problems.append("Autonomous worker or active job is stalled")
    if status.get("healthy") is not True:
        problems.append("Autonomous runtime reports degraded health")
    if status.get("last_error"):
        problems.append("Latest autonomous pass reported an error")
    if "database" in state and state["database"].get("status") != "ok":
        problems.append("Desk database reports an error")
    if "journal_integrity" in state and state["journal_integrity"].get("status") != "ok":
        problems.append("Desk journal integrity check is not healthy")
    worker = state.get("worker")
    if worker and (worker.get("alive") is not True or worker.get("error")):
        problems.append("Task worker is not healthy")
    return {"healthy": not problems, "problems": problems, "heartbeat_at": heartbeat}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8787")
    parser.add_argument("--maximum-age", type=int, default=180)
    args = parser.parse_args()
    try:
        receipt = probe(args.url, args.maximum_age)
    except Exception:
        receipt = {"healthy": False, "problems": ["Desk endpoint unavailable"]}
    print(json.dumps(receipt, indent=2))
    raise SystemExit(0 if receipt["healthy"] else 1)
