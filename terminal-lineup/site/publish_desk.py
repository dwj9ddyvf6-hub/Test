#!/usr/bin/env python3
"""Publish the desk terminal surface inside the tools site root.

The desk page lives on the desk side (muse-desk-v3/terminal/: its
index.html plus the terminal_feed.json it fetches). The tools site is
served from this folder, so the shared navigation's Desk tab (last,
by the 2026-10-31 ruling) can only link truthfully to a copy served
from the same root. This producer makes that copy: both files are
copied byte for byte into site/desk/, and the copy is verified by
hash before this prints success. The desk side stays the source;
this folder is a publish copy, refreshed by refresh_hub.py.

Usage: python3 publish_desk.py
Exit 0 when both files are in place and hash-verified.
"""
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "muse-desk-v3" / "terminal"
FILES = ("index.html", "terminal_feed.json")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish():
    dest = HERE / "desk"
    dest.mkdir(exist_ok=True)
    copied = []
    for name in FILES:
        src = SOURCE / name
        if not src.exists():
            print(f"FAIL: desk source missing: {src}")
            return 1
        out = dest / name
        shutil.copyfile(src, out)
        if _sha(src) != _sha(out):
            print(f"FAIL: desk copy does not match source: {name}")
            return 1
        copied.append(name)
    print(f"desk published: site/desk/ ({', '.join(copied)}), "
          "hash-verified against muse-desk-v3/terminal/")
    return 0


if __name__ == "__main__":
    sys.exit(publish())
