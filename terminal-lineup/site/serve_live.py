#!/usr/bin/env python3
"""Always-on live server for the terminal site (owner ruling
2026-10-31: serve it live, no static push cycle).

Serves this folder directly, so a refresh is just the data file
changing underneath; the desk copy rides beneath the same root at
desk/. Data files and pages are served no-store / no-cache so the
browser live layer's clock always reads the file's true stamp.

Usage: python3 serve_live.py [port]     (default 8766, bind 0.0.0.0)
Writes its own pid to .live-server.pid next to this file. Start it
detached so it survives session restarts:

    setsid nohup python3 serve_live.py 8766 > live-server.log 2>&1 &
"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PID_FILE = HERE / ".live-server.pid"


class LiveHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?")[0]
        if path.endswith(".json"):
            self.send_header("Cache-Control", "no-store")
        elif path.endswith((".html", "/")) or "." not in path.rsplit("/", 1)[-1]:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):  # keep the log one-line-per-hit
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    PID_FILE.write_text(str(__import__("os").getpid()), encoding="utf-8")
    handler = partial(LiveHandler, directory=str(HERE))
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"live server serving {HERE} on 0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
