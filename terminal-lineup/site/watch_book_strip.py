#!/usr/bin/env python3
"""Book strip change watcher (BOOK-STRIP-20261104).

Run by the midna-book-strip-watch cron every 5 minutes. Hashes the
book's two records of truth (~/workspace/midna-book/ledger.json and
JOURNAL.md). When neither has changed since the last successful
republication, it prints NO-CHANGE and does nothing else: cheap and
silent. When either has changed, it re-runs the strip generator and
the established publish route (sync_to_test.py), appends one line to
the republication log in the program home, and only then records
the new hashes, so a failed publish is retried on the next cycle
instead of being forgotten.

A lock file in the program home keeps two cycles from publishing at
once; a lock younger than 25 minutes is respected, an older one is
treated as abandoned (a killed run) and taken over.

The publish route is the sync's SCOPED mode (cure
BOOK-STRIP-SCOPED-PUBLISH-20261109): the watcher names exactly the
files its generator can rewrite (the strip data file, the hub page
and the live-state and asset files the hub injection touches), and
the scoped publisher waits for the sync single-flight lock instead
of standing down, so a book change no longer queues behind a
whole-tree publish or reports the stand-down as a failure. Before
this cure the watcher drove the full sync and its cycles failed on
publish exit 3 (409 races, 2026-11-05/06) and exit 5 (single-flight
stand-downs, 2026-11-09), each reported as a publish failure.

Usage: python3 watch_book_strip.py
Exit 0 on no-change, on a respected lock, and on a successful
republication; exit 1 when the republication itself failed.
Test hooks: BOOK_STRIP_BOOK_DIR, BOOK_STRIP_HOME (state and log
directory) and BOOK_STRIP_SYNC_CMD (the publish command, split on
spaces) redirect the watcher at copies and a stand-in publisher.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
HERE = Path(__file__).resolve().parent
BOOK_DIR = Path(os.environ.get(
    "BOOK_STRIP_BOOK_DIR",
    os.path.expanduser("~/workspace/midna-book")))
HOME = Path(os.environ.get(
    "BOOK_STRIP_HOME",
    os.path.expanduser(
        "~/workspace/research_notes/midna-book-strip-20261104")))
STATE = HOME / "watcher-state.json"
LOG = HOME / "republish-log.md"
LOCK = HOME / "watcher.lock"
# The generator's full write set (refresh_book_strip.py: the strip
# data file, plus the hub page and its live-state, asset-manifest
# and chips files when the hub injection rewrites them). The scoped
# publisher uploads only these that actually changed.
SCOPED_FILES = ("site/book-strip/data.json", "site/index.html",
                "site/serve_live_state.json",
                "site/asset-manifest.json", "site/hub_chips.json")
SYNC_CMD = os.environ.get(
    "BOOK_STRIP_SYNC_CMD",
    "%s %s --only %s" % (sys.executable, HERE / "sync_to_test.py",
                         " ".join(SCOPED_FILES))).split()
GEN_CMD = [sys.executable, str(HERE / "refresh_book_strip.py")]
LOCK_STALE_SECONDS = 25 * 60


def file_hash(path: Path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def book_hashes():
    return {
        "ledger.json": file_hash(BOOK_DIR / "ledger.json"),
        "JOURNAL.md": file_hash(BOOK_DIR / "JOURNAL.md"),
    }


def read_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def stamp() -> str:
    now = datetime.now(ET)
    hour = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    return "%04d-%02d-%02d %d:%02d %s ET" % (
        now.year, now.month, now.day, hour, now.minute, ampm)


def log_line(text: str) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write("- %s · %s\n" % (stamp(), text))


def acquire_lock() -> bool:
    HOME.mkdir(parents=True, exist_ok=True)
    try:
        age = datetime.now().timestamp() - LOCK.stat().st_mtime
        if age < LOCK_STALE_SECONDS:
            return False
    except OSError:
        pass
    try:
        LOCK.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as exc:
        # BOOK-STRIP-LOCK-EPERM-20261108: a transient permission
        # wall on the lock write (Errno 1, 2026-11-08 09:48 ET
        # cycle) must not kill the cycle. The lock is only a
        # concurrency guard; skipping this cycle loses nothing,
        # because hashes are recorded only after a successful
        # publish, so the next cycle retries the same change.
        # Degrade to the respected-lock outcome and leave the
        # failure in the republication log when it is writable.
        try:
            log_line("LOCK-UNAVAILABLE: lock write failed (%s); "
                     "cycle skipped, will retry next cycle" % exc)
        except OSError:
            pass
        return False
    return True


def release_lock() -> None:
    try:
        LOCK.unlink()
    except OSError:
        pass


def run(cmd, timeout):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout, cwd=str(HERE))
        lines = (out.stdout or "").strip().splitlines()
        tail = ""
        for line in reversed(lines):
            if line.startswith("- ") or line.startswith("census:") \
                    or line.startswith("scoped census:"):
                tail = line
                break
        if not tail and lines:
            tail = lines[-1]
        return out.returncode, tail
    except Exception as exc:
        return 99, "watcher could not run %s: %s" % (
            cmd[1] if len(cmd) > 1 else cmd[0], exc)


def main() -> int:
    if not acquire_lock():
        print("LOCKED: a previous watcher cycle is still publishing")
        return 0
    try:
        current = book_hashes()
        previous = read_state().get("hashes") or {}
        changed = [name for name, h in current.items()
                   if h != previous.get(name)]
        if not changed:
            print("NO-CHANGE ledger=%s journal=%s" % (
                (current["ledger.json"] or "")[:8],
                (current["JOURNAL.md"] or "")[:8]))
            return 0
        gen_rc, gen_tail = run(GEN_CMD, 600)
        if gen_rc != 0:
            log_line("FAILED on %s: generator exit %d (%s); will "
                     "retry next cycle" % (", ".join(changed),
                                           gen_rc, gen_tail))
            print("FAILED: generator exit %d" % gen_rc)
            return 1
        # 2700s: the scoped publisher may wait up to 1500s for the
        # single-flight lock behind a running full sync, then needs
        # its own publish time; the watcher must outwait both.
        sync_rc, sync_tail = run(SYNC_CMD, 2700)
        if sync_rc != 0:
            log_line("FAILED on %s: publish exit %d (%s); will "
                     "retry next cycle" % (", ".join(changed),
                                           sync_rc, sync_tail))
            print("FAILED: publish exit %d" % sync_rc)
            return 1
        HOME.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_name(STATE.name + ".tmp")
        tmp.write_text(json.dumps(
            {"hashes": current, "published_at": stamp()},
            indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, STATE)
        log_line("republished on change to %s · %s" % (
            ", ".join(changed), sync_tail))
        print("REPUBLISHED on change to %s" % ", ".join(changed))
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
