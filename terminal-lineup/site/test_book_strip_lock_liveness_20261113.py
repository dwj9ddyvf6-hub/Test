#!/usr/bin/env python3
"""Regression blocker for the book strip watcher lock liveness
defect (STRIP-LOCK-LIVENESS-20261113, hunt item PR-4).

Failure class: on 2026-11-13 the 08:08 ET watcher cycle was
terminated by SIGTERM about 13 seconds in (the 13:08Z VM restart),
leaving watcher.lock with holder PID 14758 recorded. Lock validity
was judged by age alone (25 minutes), never by whether the recorded
holder still existed, so the 08:33 ET cycle exited 0 with "LOCKED:
a previous watcher cycle is still publishing" and stood down
without verifying NO-CHANGE or REPUBLISHED; the lane recovered only
when the lock aged out, and the published strip lagged the book for
the whole window.

The cure: acquire_lock() also checks holder liveness. A young lock
whose recorded PID provably does not exist is reclaimed at once; a
young lock with a live holder, or with content that cannot be read
as a PID, is still respected; the 25-minute age takeover is
unchanged.

This blocker proves: (1) a fresh lock naming a dead PID is
reclaimed immediately and rewritten with the acquirer's PID;
(2) a fresh lock naming a live PID is respected and left untouched;
(3) a fresh lock with unparseable content is respected (death is
never guessed); (4) a stale lock is still taken over by age.
Pre-cure, check (1) fails: acquire_lock() returns False for the
dead holder's fresh lock. Run standalone:
python3 test_book_strip_lock_liveness_20261113.py [watcher_path]
(exit 0 = pass). The optional watcher_path runs the same checks
against another copy (the preserved pre-cure copy proves the fail
direction).
"""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SITE = Path(__file__).resolve().parent


def load_watcher(home: Path, book: Path, watcher_path: Path):
    os.environ["BOOK_STRIP_HOME"] = str(home)
    os.environ["BOOK_STRIP_BOOK_DIR"] = str(book)
    loader = importlib.machinery.SourceFileLoader(
        "watch_book_strip_liveness_test", str(watcher_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dead_pid() -> int:
    proc = subprocess.Popen(["sleep", "60"])
    pid = proc.pid
    proc.kill()
    proc.wait()
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return pid
    raise RuntimeError("could not obtain a provably dead pid")


def main() -> int:
    watcher_path = (Path(sys.argv[1]) if len(sys.argv) > 1
                    else SITE / "watch_book_strip.py")
    fails = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        home = root / "home"
        book = root / "book"
        home.mkdir()
        book.mkdir()
        (book / "ledger.json").write_text("{}", encoding="utf-8")
        (book / "JOURNAL.md").write_text("# j\n", encoding="utf-8")
        watch = load_watcher(home, book, watcher_path)

        gone = dead_pid()
        sleeper = subprocess.Popen(["sleep", "60"])
        try:
            # (1) The defect itself: a FRESH lock whose recorded
            # holder is dead must be reclaimed at once.
            watch.LOCK.write_text(str(gone), encoding="utf-8")
            try:
                if not watch.acquire_lock():
                    fails.append(
                        "fresh lock with dead holder pid %d was "
                        "respected instead of reclaimed" % gone)
                elif watch.LOCK.read_text(
                        encoding="utf-8") != str(os.getpid()):
                    fails.append(
                        "reclaimed lock not rewritten with the "
                        "acquirer's pid")
                watch.release_lock()
            except OSError as exc:
                fails.append("dead-holder check raised %r" % exc)

            # (2) A fresh lock with a LIVE holder is respected and
            # left untouched.
            watch.LOCK.write_text(str(sleeper.pid), encoding="utf-8")
            try:
                if watch.acquire_lock():
                    fails.append(
                        "fresh lock with live holder pid %d was "
                        "broken" % sleeper.pid)
                elif watch.LOCK.read_text(
                        encoding="utf-8") != str(sleeper.pid):
                    fails.append("live holder's lock was overwritten")
            except OSError as exc:
                fails.append("live-holder check raised %r" % exc)

            # (3) Unparseable content is never read as death.
            watch.LOCK.write_text("not-a-pid", encoding="utf-8")
            try:
                if watch.acquire_lock():
                    fails.append(
                        "fresh lock with unparseable content was "
                        "reclaimed on a guess")
            except OSError as exc:
                fails.append("unparseable check raised %r" % exc)

            # (4) The age takeover still works.
            old = time.time() - (watch.LOCK_STALE_SECONDS + 60)
            os.utime(watch.LOCK, (old, old))
            try:
                if not watch.acquire_lock():
                    fails.append("stale lock not taken over by age")
                watch.release_lock()
            except OSError as exc:
                fails.append("stale takeover raised %r" % exc)
        finally:
            sleeper.kill()
            sleeper.wait()

    for f in fails:
        print("FAIL: " + f)
    print("book strip lock liveness tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
