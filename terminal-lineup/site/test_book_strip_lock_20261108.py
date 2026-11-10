#!/usr/bin/env python3
"""Regression blocker for the book strip watcher lock failure
(BOOK-STRIP-LOCK-EPERM-20261108).

Failure class: on 2026-11-08 the 09:48 ET watcher cycle died with
PermissionError: [Errno 1] Operation not permitted from
acquire_lock() (watch_book_strip.py, LOCK.write_text) and the cycle
was reported FAILED. Neighbouring cycles (09:43, 09:53) acquired and
released the same lock in the same directory without error, so the
EPERM was a transient permission wall on the lock write, not a
filesystem state. The defect at the source: acquire_lock() let an
OSError from the lock write escape and kill the whole cycle, instead
of degrading to the watcher's own benign outcome (skip this cycle;
the change is retried in 5 minutes because hashes are recorded only
after a successful publish).

This blocker proves: (1) a lock write that raises PermissionError
makes acquire_lock() return False and main() exit 0 with the LOCKED
line, never an exception; (2) a fresh lock is respected untouched;
(3) a stale lock is taken over; (4) a normal acquire/release cycle
works. Pre-cure, check (1) raises PermissionError out of
acquire_lock() and this file FAILs. Run standalone:
python3 test_book_strip_lock_20261108.py (exit 0 = pass).
"""
import importlib.util
import io
import os
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

SITE = Path(__file__).resolve().parent


def load_watcher(home: Path, book: Path):
    os.environ["BOOK_STRIP_HOME"] = str(home)
    os.environ["BOOK_STRIP_BOOK_DIR"] = str(book)
    spec = importlib.util.spec_from_file_location(
        "watch_book_strip_locktest", SITE / "watch_book_strip.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EpermPath(type(Path())):
    """A Path whose write_text raises the exact 2026-11-08 error."""

    def write_text(self, *args, **kwargs):  # noqa: D102
        raise PermissionError(1, "Operation not permitted")


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        home = root / "home"
        book = root / "book"
        book.mkdir()
        (book / "ledger.json").write_text("{}", encoding="utf-8")
        (book / "JOURNAL.md").write_text("# j\n", encoding="utf-8")
        watch = load_watcher(home, book)

        # (4) Normal acquire/release.
        try:
            if not watch.acquire_lock():
                fails.append("normal acquire_lock returned False")
            elif watch.LOCK.read_text(encoding="utf-8") != str(os.getpid()):
                fails.append("lock file does not carry the pid")
            watch.release_lock()
            if watch.LOCK.exists():
                fails.append("release_lock left the lock file behind")
        except OSError as exc:
            fails.append("normal acquire/release raised %r" % exc)

        # (2) A fresh lock is respected and left untouched.
        watch.LOCK.write_text("424242", encoding="utf-8")
        try:
            if watch.acquire_lock():
                fails.append("fresh lock not respected")
            elif watch.LOCK.read_text(encoding="utf-8") != "424242":
                fails.append("fresh lock was overwritten")
        except OSError as exc:
            fails.append("fresh-lock check raised %r" % exc)

        # (3) A stale lock (older than the 25 minute stale bound)
        # is taken over.
        old = time.time() - (watch.LOCK_STALE_SECONDS + 60)
        os.utime(watch.LOCK, (old, old))
        try:
            if not watch.acquire_lock():
                fails.append("stale lock not taken over")
            elif watch.LOCK.read_text(encoding="utf-8") != str(os.getpid()):
                fails.append("stale lock not rewritten with the pid")
            watch.release_lock()
        except OSError as exc:
            fails.append("stale-lock takeover raised %r" % exc)

        # (1) The defect itself: the lock write raises
        # PermissionError (Errno 1). acquire_lock must return False
        # and main must exit 0 with the LOCKED line; no exception
        # may escape either.
        real_lock = watch.LOCK
        watch.LOCK = EpermPath(str(real_lock))
        try:
            try:
                got = watch.acquire_lock()
                if got:
                    fails.append("EPERM lock write reported acquired")
            except PermissionError as exc:
                fails.append(
                    "acquire_lock let PermissionError escape: %r" % exc)
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = watch.main()
                if rc != 0:
                    fails.append("main with EPERM lock returned %d" % rc)
                elif "LOCKED" not in buf.getvalue():
                    fails.append("main with EPERM lock printed %r"
                                 % buf.getvalue())
            except PermissionError as exc:
                fails.append("main let PermissionError escape: %r" % exc)
        finally:
            watch.LOCK = real_lock

    for f in fails:
        print("FAIL: " + f)
    print("book strip lock tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
