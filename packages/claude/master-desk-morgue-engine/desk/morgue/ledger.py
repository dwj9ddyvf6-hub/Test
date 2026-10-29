"""The Ledger: append-only, as-was signal log (the Morgue Engine's spine).

Every value the engine shows is written here BEFORE it is shown, with the hash of its inputs; restatement is a new row,
never an edit. Rows are one JSON object a line in state/morgue/ledger.jsonl (recorded by tools/state_sync with the rest
of state/). A reader that wants to show a card asks `logged(root, hash)` first (edition.py)."""
import fcntl
import hashlib
import json
import os
import time
from datetime import datetime, timezone

from . import state_path

LEDGER = "ledger.jsonl"


def inputs_hash(payload):
    """sha256 of the payload's sorted JSON, first 16 hex digits (Silicon's rule, kept so old hashes still match)"""
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def path(root):
    return state_path(root, LEDGER)


def append(root, row, now=None):
    """one row appended -> the row as written (ts_utc first). Never rewrites the file."""
    ts = datetime.fromtimestamp(time.time() if now is None else float(now), tz=timezone.utc).isoformat()
    row = {"ts_utc": ts, **row}
    p = path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)                 # two jobs never interleave a line (a board summary is over 4 KB)
        try:
            fh.write(json.dumps(row, default=str) + "\n")
            fh.flush()
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return row


_CACHE = {}


def read(root):
    """every row, oldest first; a line that does not parse is skipped (a killed writer's half line), not fatal. The parse is
    kept for this process while the file's size and time do not change (one edition build reads the ledger several times)."""
    p = path(root)
    try:
        st = os.stat(p)
    except OSError:
        return []
    key = (st.st_mtime_ns, st.st_size)
    hit = _CACHE.get(p)
    if hit and hit[0] == key:
        return list(hit[1])
    out = []
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    _CACHE[p] = (key, out)
    return list(out)


def hashes(root):
    """the set of inputs hashes the ledger holds"""
    return {r.get("inputs_hash") for r in read(root) if r.get("inputs_hash")}


def logged(root, h, held=None):
    """True when the ledger holds a row with this inputs hash (held: a precomputed hashes() set)"""
    return bool(h) and h in (held if held is not None else hashes(root))
