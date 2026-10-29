#!/usr/bin/env python3
"""Verify a backup receipt and restore into a NEW path; never overwrite a desk."""
import argparse
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path


def restore(backup, destination, receipt=None):
    backup, destination = Path(backup).resolve(), Path(destination).resolve()
    receipt_path = Path(receipt).resolve() if receipt else backup.with_suffix(".json")
    metadata = json.loads(receipt_path.read_text())
    if destination.exists() or any(Path(str(destination) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("Restoration requires a new database path; existing desk state is preserved")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".restore-" + uuid.uuid4().hex + ".tmp")
    try:
        # Copy and hash the SAME bytes. Opening the original with SQLite would
        # also replay an unreceipted -wal file, and a second source read could
        # observe a different database after the identity check.
        hasher, copied_bytes = hashlib.sha256(), 0
        with backup.open("rb") as source, temporary.open("xb") as restored:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                restored.write(block)
                hasher.update(block)
                copied_bytes += len(block)
            restored.flush()
            os.fsync(restored.fileno())
        digest = hasher.hexdigest()
        if metadata.get("sha256") != digest or metadata.get("bytes") != copied_bytes or metadata.get("integrity") != "ok":
            raise ValueError("Backup identity does not match its integrity receipt")
        with sqlite3.connect(temporary.as_uri() + "?mode=ro&immutable=1", uri=True) as restored:
            if restored.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Restored database failed integrity validation")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        # A hard link publishes atomically and refuses a concurrently created
        # destination. No existing file is ever replaced or deleted.
        # Sidecars can also appear while verification is in progress. Refuse
        # them immediately before the exclusive publication of the main file.
        if any(Path(str(destination) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise ValueError("Restoration requires a new database path; existing desk state is preserved")
        os.link(temporary, destination)
        directory = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return {"restored_database": str(destination), "source_sha256": digest, "integrity": "ok", "existing_state_overwritten": False, "next_action": "Stop the desk, select this new ASTER_DB_PATH, then restart and inspect journal/broker reconciliation before supplying new instructions"}
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()
    print(json.dumps(restore(args.backup, args.destination, args.receipt), indent=2))
