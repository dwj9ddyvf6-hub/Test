#!/usr/bin/env python3
"""Published-tree retention and flip-back (HEALTH-R1-D19-20261031).

Before this module the published site had no rollback: the live
server serves the tree on disk, so a bad publish overwrote the
only copy of the previous tree. This module retains the previous
published tree (the files the server actually serves: the root
assets plus every page's index.html and data.json) under
site/.published-trees/<utc-stamp>/, keeping the newest KEEP
snapshots, and can flip the served tree back to a retained one.

publish_live.py snapshots the tree on every publish run when its
content differs from the newest retained snapshot, so a retained
previous tree always exists before a new publish is proven.
Flip-back is a named, drilled step:

    python3 retain_tree.py --flip-back <stamp>

Usage: python3 retain_tree.py [--snapshot] [--flip-back STAMP]
"""
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RETAIN_DIR = os.path.join(HERE, ".published-trees")
KEEP = 2


def published_files(site_dir):
    """The served surface: root files plus per-page index/data."""
    out = []
    for name in sorted(os.listdir(site_dir)):
        path = os.path.join(site_dir, name)
        if os.path.isfile(path):
            out.append(name)
        elif os.path.isdir(path) and name not in (
                ".published-trees", "__pycache__"):
            for sub in ("index.html", "data.json"):
                if os.path.isfile(os.path.join(path, sub)):
                    out.append(os.path.join(name, sub))
    return out


def tree_digest(site_dir, files=None):
    files = files if files is not None else published_files(site_dir)
    h = hashlib.sha256()
    for rel in files:
        with open(os.path.join(site_dir, rel), "rb") as fh:
            h.update(rel.encode())
            h.update(fh.read())
    return h.hexdigest()


def snapshot(site_dir=HERE, keep=KEEP):
    """Retain the current published tree if it differs from the
    newest retained snapshot. Returns (stamp, created)."""
    os.makedirs(RETAIN_DIR, exist_ok=True)
    files = published_files(site_dir)
    digest = tree_digest(site_dir, files)
    stamps = sorted(os.listdir(RETAIN_DIR))
    for stamp in stamps:
        meta = os.path.join(RETAIN_DIR, stamp, "RETENTION.json")
        if os.path.isfile(meta):
            with open(meta, encoding="utf-8") as fh:
                if json.load(fh).get("digest") == digest:
                    return stamp, False
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(RETAIN_DIR, stamp)
    if os.path.exists(dest):
        return stamp, False
    for rel in files:
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(site_dir, rel), target)
    with open(os.path.join(dest, "RETENTION.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"stamp": stamp, "digest": digest,
                   "files": len(files)}, fh, indent=1)
        fh.write("\n")
    stamps = sorted(os.listdir(RETAIN_DIR))
    for old in stamps[:-keep] if keep else []:
        shutil.rmtree(os.path.join(RETAIN_DIR, old),
                      ignore_errors=True)
    return stamp, True


def flip_back(stamp, site_dir=HERE):
    """Restore the retained tree named by stamp over the served
    tree. Returns the number of files restored."""
    src = os.path.join(RETAIN_DIR, stamp)
    if not os.path.isdir(src):
        raise RuntimeError(f"no retained tree named {stamp}")
    restored = 0
    for root, _dirs, names in os.walk(src):
        for name in names:
            if name == "RETENTION.json":
                continue
            rel = os.path.relpath(os.path.join(root, name), src)
            target = os.path.join(site_dir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(os.path.join(root, name), target)
            restored += 1
    return restored


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--flip-back" in argv:
        stamp = argv[argv.index("--flip-back") + 1]
        n = flip_back(stamp)
        print(f"retain_tree: flipped back to {stamp} "
              f"({n} files restored)")
        return 0
    stamp, created = snapshot()
    print(f"retain_tree: snapshot {stamp} "
          f"({'created' if created else 'already retained'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
