#!/usr/bin/env python3
"""Publish step for the serve-live route (owner ruling 2026-10-31).

There is no static push: the always-on server (serve_live.py) reads
the site files directly, so "publishing" is proving that what the
server serves is byte-for-byte what is on disk. This step:

1. makes sure the live server answers on its port (starting it
   detached when it is down), then
2. hash-compares the served bytes against disk for the hub, the
   desk copy beneath it, and every hub page's data.json.

Exit 0 only when every compared file matches. Wired into
republish_one.sh after verify_terminal.sh, so a standalone
republish ends proven-live, not just proven-written.

Usage: python3 publish_live.py [port]
"""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
BASE = f"http://127.0.0.1:{PORT}"


def fetch(path: str) -> bytes:
    req = urllib.request.Request(BASE + "/" + path,
                                 headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def server_up() -> bool:
    try:
        fetch("index.html")
        return True
    except Exception:
        return False


def start_server() -> bool:
    log = open(HERE / "live-server.log", "ab")
    subprocess.Popen(
        [sys.executable, str(HERE / "serve_live.py"), str(PORT)],
        cwd=str(HERE), stdout=log, stderr=log,
        stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        if server_up():
            return True
        time.sleep(0.2)
    return False


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if not server_up() and not start_server():
        print(f"FAIL: live server does not answer on port {PORT}")
        return 1
    targets = ["index.html", "desk/index.html", "desk/terminal_feed.json"]
    slugs = sorted(p.parent.name for p in HERE.glob("*/data.json"))
    targets += [f"{slug}/data.json" for slug in slugs]
    targets += [f"{slug}/index.html" for slug in slugs
                if (HERE / slug / "index.html").exists()]
    bad = []
    for rel in targets:
        disk = HERE / rel
        if not disk.exists():
            bad.append(f"{rel}: missing on disk")
            continue
        try:
            served = fetch(rel)
        except Exception as exc:
            bad.append(f"{rel}: fetch failed ({exc})")
            continue
        if sha(served) != sha(disk.read_bytes()):
            bad.append(f"{rel}: served bytes differ from disk")
    if bad:
        print(f"FAIL: publish proof failed for {len(bad)} of "
              f"{len(targets)} files:")
        for line in bad[:20]:
            print("  " + line)
        return 1
    print(f"publish proof: {len(targets)} files served byte-identical "
          f"to disk at {BASE}/ (hub, desk/, every page data + shell)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
