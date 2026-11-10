#!/usr/bin/env python3
"""Version stamps for completed DEEP panel days (GLORY item 7b,
canon D11 semantics applied to the DEEP panel).

The DEEP panel (morgue/data_cache/deep_bars.json) is one JSON object
of per-symbol daily bars. The advance lane
(advance_deep_panel.py) already treats history as append-only: it
inserts only rows dated strictly after each symbol's last stored
date, verifies the rewrite, and replaces the panel atomically. What
was missing is the D11 stamp: a record that a completed day, once
written, is immutable, with the observed version and the means to
prove no completed row has changed since.

This module writes and verifies those stamps. A stamp for a
completed date D records, per symbol, the count and last date of
rows dated <= D and a SHA-256 over the canonical form of exactly
those rows, plus the panel fingerprint at stamp time. Rows dated
after D are forming records for this stamp: excluded, never
stamped, free to arrive via the advance lane. Verification
recomputes the same per-symbol digests from the current panel:
any changed, added, or removed completed row names its symbol.
Legitimate advances (new rows after D) do not disturb a stamp,
because the digest covers only rows dated <= D.

Stamps live beside the derived store:
terminal-lineup/deep_store/day_stamps/<date>.json

Usage:
  python3 deep_day_stamps.py stamp  [--panel PATH] --through DATE
  python3 deep_day_stamps.py verify --stamp FILE [--panel PATH]

This tool is read-only against the panel. It is not wired into the
refresh runner; adoption into the daily lane is a terminal-lane
decision (see the GLORY registry lane report).
"""
import hashlib
import json
import mmap
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from advance_deep_panel import scan_panel  # noqa: E402  (never forked)
from deep_panel_reader import panel_fingerprint  # noqa: E402

PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/deep_bars.json")
STAMP_DIR = os.path.join(
    os.path.dirname(HERE), "deep_store", "day_stamps")


def completed_digests(panel_path: str, through: str) -> dict:
    """{symbol: {rows_through, last_through, sha256}} over rows
    dated <= through, read per symbol from the mmap'd panel spans
    the shared scanner locates. Only the symbols' own spans are
    parsed; the panel object as a whole is never loaded."""
    out = {}
    with open(panel_path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            scan = scan_panel(mm)
            for sym, (start, length, _count, _last) in scan.items():
                if length <= 2:
                    rows = []
                else:
                    rows = json.loads(
                        mm[start:start + length].decode("utf-8"))
                done = [r for r in rows if r[0] <= through]
                digest = hashlib.sha256(
                    json.dumps(done, separators=(",", ":"),
                               sort_keys=False).encode()).hexdigest()
                out[sym] = {
                    "rows_through": len(done),
                    "last_through": done[-1][0] if done else None,
                    "sha256": digest,
                }
        finally:
            mm.close()
    return out


def aggregate(symbols: dict) -> str:
    h = hashlib.sha256()
    for sym in sorted(symbols):
        s = symbols[sym]
        h.update(f"{sym}|{s['rows_through']}|{s['last_through']}|"
                 f"{s['sha256']}\n".encode())
    return h.hexdigest()


def stamp(panel_path: str, through: str, stamp_dir: str) -> dict:
    symbols = completed_digests(panel_path, through)
    record = {
        "kind": "deep_completed_day_stamp",
        "date": through,
        "panel_path": panel_path,
        "panel_fingerprint_at_stamp": panel_fingerprint(panel_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "semantics": "D11: rows dated <= date are completed and "
                     "immutable under this stamp; rows after date "
                     "are forming and excluded",
        "symbols": symbols,
        "aggregate_sha256": aggregate(symbols),
    }
    os.makedirs(stamp_dir, exist_ok=True)
    path = os.path.join(stamp_dir, f"{through}.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)
    record["_stamp_path"] = path
    return record


def verify(stamp_path: str, panel_path: str) -> tuple[bool, list[str]]:
    with open(stamp_path, "r", encoding="utf-8") as fh:
        record = json.load(fh)
    now = completed_digests(panel_path, record["date"])
    problems = []
    stamped = record["symbols"]
    for sym in sorted(set(stamped) | set(now)):
        if sym not in now:
            problems.append(f"{sym}: symbol missing from panel")
        elif sym not in stamped:
            problems.append(f"{sym}: symbol not in stamp")
        elif stamped[sym] != now[sym]:
            problems.append(
                f"{sym}: completed rows changed "
                f"(stamped {stamped[sym]['rows_through']} rows / "
                f"{stamped[sym]['sha256'][:12]}..., now "
                f"{now[sym]['rows_through']} rows / "
                f"{now[sym]['sha256'][:12]}...)")
        if len(problems) >= 20:
            break
    if aggregate(now) != record["aggregate_sha256"] and not problems:
        problems.append("aggregate digest differs")
    return not problems, problems


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    panel = opt("--panel", PANEL_PATH)
    if cmd == "stamp":
        through = opt("--through")
        if not through:
            print("stamp requires --through DATE", file=sys.stderr)
            return 2
        rec = stamp(panel, through, opt("--stamp-dir", STAMP_DIR))
        print(f"stamped {rec['date']}: {len(rec['symbols'])} symbols, "
              f"aggregate {rec['aggregate_sha256'][:16]}..., "
              f"panel fingerprint {rec['panel_fingerprint_at_stamp']}, "
              f"file {rec['_stamp_path']}")
        return 0
    if cmd == "verify":
        stamp_path = opt("--stamp")
        if not stamp_path:
            print("verify requires --stamp FILE", file=sys.stderr)
            return 2
        ok, problems = verify(stamp_path, panel)
        if ok:
            print(f"verify OK: completed rows through the stamp date "
                  f"are unchanged in {panel}")
            return 0
        print("verify FAILED: completed-day immutability broken:")
        for p in problems:
            print(f" - {p}")
        return 1
    print(f"unknown command {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
