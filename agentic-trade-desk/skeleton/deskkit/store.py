"""State file with cross-process locking, atomic writes and *merge-back of foreign additions*.

Failure story: a backup/failover process adopted lots into the book while the main loop was
mid-pass. The main loop then saved its (older) in-memory copy and overwrote the adoption.
Fixes (all three are needed):
  1. every read-modify-write happens under ONE exclusive file lock;
  2. saves are atomic (write temp, fsync, rename);
  3. save() re-reads the file under the lock and merges back anything *added by another
     writer* (items whose `source` is in FOREIGN_SOURCES) that the in-memory copy lacks.
     Merge is ADD-ONLY: it never deletes and never edits an existing item.
"""
from __future__ import annotations
import contextlib
import fcntl
import json
import os
import tempfile

FOREIGN_SOURCES = {"failover", "import"}


class StateStore:
    def __init__(self, path: str):
        self.path = path
        self.lock_path = path + ".lock"

    @contextlib.contextmanager
    def locked(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.lock_path, "a+") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)

    def load(self) -> dict:
        try:
            with open(self.path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"lots": {}, "seen": []}

    def _atomic_write(self, state: dict):
        d = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".state.")
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def save(self, state: dict):
        """Save under the lock, merging add-only foreign lots from disk first."""
        with self.locked():
            self._save_locked(state)

    def _save_locked(self, state: dict):
        disk = self.load()
        for lot_id, lot in disk.get("lots", {}).items():
            if lot.get("source") in FOREIGN_SOURCES and lot_id not in state.get("lots", {}):
                state.setdefault("lots", {})[lot_id] = lot
        seen = set(state.get("seen", [])) | set(disk.get("seen", []))
        state["seen"] = sorted(seen)
        self._atomic_write(state)

    def update(self, fn):
        """Read-modify-write atomically: fn(state) mutates a FRESH load made under the lock."""
        with self.locked():
            st = self.load()
            fn(st)
            self._save_locked(st)
            return st
