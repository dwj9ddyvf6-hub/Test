#!/usr/bin/env python3
"""Consistent, additive SQLite backups. This script never deletes any state."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError("Desk database does not exist")
    destination.mkdir(parents=True, exist_ok=True)
    required = max(10_000_000, source.stat().st_size * 2)
    if shutil.disk_usage(destination).free < required:
        raise ValueError("Backup deferred: insufficient disk space; source state remains untouched")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = destination / ("aster-" + stamp + "-" + uuid.uuid4().hex[:8] + ".sqlite")
    temporary = target.with_suffix(".sqlite.tmp")
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as original, sqlite3.connect(temporary) as copy:
            original.backup(copy)
            if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup failed integrity validation")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        temporary.rename(target)
        directory = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        receipt = {"database": str(target), "sha256": digest.hexdigest(), "bytes": target.stat().st_size, "created_at": datetime.now(timezone.utc).isoformat(), "integrity": "ok", "additive": True}
        with target.with_suffix(".json").open("x") as handle:
            json.dump(receipt, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return receipt
    finally:
        # Only our incomplete temporary copy is disposable; source/older copies
        # and the ledger/inbox/research tables are never cleanup candidates.
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=os.environ.get("ASTER_DB_PATH", "data/aster.sqlite"))
    parser.add_argument("--destination", default="backups")
    args = parser.parse_args()
    print(json.dumps(backup(args.database, args.destination), indent=2))
