#!/usr/bin/env python3
"""Watchdog for the always-on live server (cure D-R1-23, 2026-10-31).

The serve-live cure (LIVENESS-20261031) gave the terminal an
always-on server, but nothing owned its liveness after a runtime
or machine restart: on 2026-10-31 the pid file named a dead PID
for hours while the served terminal answered nothing, and no lane
failed on it. This watchdog is the supervised lane the audit
required. It proves the server by its effects, never by the pid
file or a process scan:

1. GET the hub page and one real page's data file; both must
   answer HTTP 200.
2. If either does not, start serve_live.py detached (the same
   start publish_live.py performs) and prove again.
3. Stamp the outcome to serve_live_state.json on every run, so a
   dead server is a named, dated state, not a silent absence.

Wired two ways: lane_run.py invokes it at the head of every lane
(intraday every 5 minutes in market hours, hourly otherwise), and
the terminal-live-server-watchdog cron runs it every 15 minutes
on its own, so the bound on an unnoticed outage is one watchdog
interval.

Usage: python3 watch_serve_live.py [port]   (default 8766)
Exit 0 only when the hub and the data file both answer 200.
"""
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
BASE = f"http://127.0.0.1:{PORT}"
STATE = HERE / "serve_live_state.json"
PROBES = ("index.html", "morning-map/data.json")


def probe(path: str):
    try:
        req = urllib.request.Request(BASE + "/" + path,
                                     headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read(64)
            return resp.status
    except Exception:
        return None


def start_server() -> None:
    log = open(HERE / "live-server.log", "ab")
    subprocess.Popen(
        [sys.executable, str(HERE / "serve_live.py"), str(PORT)],
        cwd=str(HERE), stdout=log, stderr=log,
        stdin=subprocess.DEVNULL, start_new_session=True)


def check():
    return {path: probe(path) for path in PROBES}


def main() -> int:
    results = check()
    restarted = False
    if any(status != 200 for status in results.values()):
        start_server()
        restarted = True
        for _ in range(50):
            results = check()
            if all(status == 200 for status in results.values()):
                break
            time.sleep(0.2)
    up = all(status == 200 for status in results.values())
    pid = None
    pid_file = HERE / ".live-server.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            pid = None
    state = {
        "checked_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "port": PORT,
        "up": up,
        "restarted": restarted,
        "probes": results,
        "server_pid": pid,
    }
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(f"live server {'UP' if up else 'DOWN'} on port {PORT}: "
          f"{results}" + (" (restarted)" if restarted else ""))
    return 0 if up else 1


if __name__ == "__main__":
    sys.exit(main())
