#!/usr/bin/env python3
"""Run a command with a MONOTONIC time limit (immune to VM pause / wall-clock jumps).

    mono_timeout.py 21600 -- python3 nightly_job.py

Exit codes: the child's code, or 124 on timeout (same convention as GNU timeout).
Sends TERM, waits 15 s, then KILL, and kills the whole process group.
"""
import os, signal, subprocess, sys, time

def main():
    limit = float(sys.argv[1]); cmd = sys.argv[sys.argv.index("--") + 1:]
    p = subprocess.Popen(cmd, start_new_session=True)
    end = time.monotonic() + limit
    while True:
        rc = p.poll()
        if rc is not None:
            return rc
        if time.monotonic() > end:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(15)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
            return 124
        time.sleep(1)

if __name__ == "__main__":
    sys.exit(main())
