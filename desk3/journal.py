"""Append-only per-sleeve journals. Single O_APPEND writes; batched flush
on the hot path (v2 append semantics, batching added per V3-SCOPE §7.5)."""
from __future__ import annotations
import json, os

MAX_JOURNAL_BYTES = int(os.environ.get("MUSE_JOURNAL_MAX_BYTES", "5000000"))


def journal_generations(path):
    """Every generation of a journal, oldest first: path.N for the
    largest N present down to path.1, then path itself. The reader
    contract for every consumer of these journals (JOURNAL-READER-
    20261030 established it for two generations; JOURNAL-ROTATION-
    LEDGER-20261108 extends it to all of them, because rotation no
    longer destroys any)."""
    import re
    out = []
    d = os.path.dirname(os.path.abspath(path))
    base = os.path.basename(path)
    try:
        names = os.listdir(d)
    except OSError:
        names = []
    gens = []
    for name in names:
        m = re.fullmatch(re.escape(base) + r"\.(\d+)", name)
        if m:
            gens.append(int(m.group(1)))
    for n in sorted(gens, reverse=True):
        out.append(path + "." + str(n))
    if os.path.exists(path):
        out.append(path)
    return out


def _rotate_if_needed(path):
    # JOURNAL-ROTATION-LEDGER-20261108: rotation used to be
    # os.replace(path, path + ".1"), which DESTROYS the previous
    # rotated generation on every second rotation. The reader
    # contract spans the rotated generations, so the 2026-11-08
    # rotation silently deleted the 2026-10-26..2026-11-02
    # dispatcher generation from every derivation: reconcile's
    # expected positions/spend forgot that generation's fills in
    # one cycle (unexplained cash 5,122.82 -> 40,835.40 and phantom
    # net-short position discrepancies desk-wide). Rotation now
    # SHIFTS generations up (path.N -> path.N+1, path -> path.1)
    # and never deletes; retention is an owner ruling, not a
    # side effect of a size cap.
    try:
        if os.path.exists(path) and os.path.getsize(path) >= MAX_JOURNAL_BYTES:
            import re
            d = os.path.dirname(os.path.abspath(path))
            base = os.path.basename(path)
            gens = []
            for name in os.listdir(d):
                m = re.fullmatch(re.escape(base) + r"\.(\d+)", name)
                if m:
                    gens.append(int(m.group(1)))
            for n in sorted(gens, reverse=True):
                os.replace(path + "." + str(n), path + "." + str(n + 1))
            os.replace(path, path + ".1")
    except OSError:
        pass


def append_line(path, record: dict):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    _rotate_if_needed(path)
    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode())
    finally:
        os.close(fd)


def read_lines(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


class BatchedJournal:
    """Buffers records per path; flushes a whole batch in one open/write.
    Append-only: flush only ever appends complete lines."""

    def __init__(self, batch_size=32):
        self.batch_size = batch_size
        self._buf = {}

    def append(self, path, record):
        self._buf.setdefault(path, []).append(record)
        if len(self._buf[path]) >= self.batch_size:
            self._flush_path(path)

    def _flush_path(self, path):
        rows = self._buf.pop(path, [])
        if not rows:
            return
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        _rotate_if_needed(path)
        payload = "".join(
            json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n" for r in rows)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, payload.encode())
        finally:
            os.close(fd)

    def flush(self):
        for path in list(self._buf):
            self._flush_path(path)
