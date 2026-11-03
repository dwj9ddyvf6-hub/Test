#!/usr/bin/env python3
"""Daily DEEP-panel advance lane (cure G3 scheduling, 2026-10-30).

Root cause of the remaining freeze: morgue/data_cache/deep_bars.json
was built once by the cure-E backfill (ending 2026-10-28) and no lane
ever advanced it, so Engines 3 and 15 would silently age on a frozen
panel while the board panel (advance_price_panel.py) moved on. This
lane is the DEEP panel's own advance: it appends every completed
session after each symbol's last stored date, from Alpaca SIP daily
bars (the board lane's fetch_bars, reused verbatim, never forked).

The panel is about 1 GB of single-line JSON, so this lane never
loads it whole (the whole-panel load is what OOM-killed the DEEP
engines). It works from byte offsets, in the same form as
deep_panel_reader._build_sidecar: mmap header scan for each
symbol's array span, the last date parsed from the array tail, and
a streaming rewrite that copies the original bytes and inserts the
new rows just before each touched symbol's closing bracket. The
rewrite lands on a temp file, is re-scanned for integrity (symbol
count, per-symbol counts and last dates match the fetched appends
exactly), and only then replaces the panel atomically. Any failure
leaves the original panel untouched.

Usage: python3 advance_deep_panel.py [--through YYYY-MM-DD]
Default through: the freshest completed session (see
completed_session.py; terminal audit cure, 2026-10-31).
"""
import json
import mmap
import os
import re
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/deep_bars.json")

_HEADER_RE = re.compile(rb'"([^"]+)": \[')
_TAIL_DATE_RE = re.compile(rb'\["(\d{4}-\d{2}-\d{2})", [^\]]*\]\]$')


def scan_panel(mm):
    """{symbol: (start, length, count, last_date)} from an mmap of
    the panel, without parsing any symbol's full history."""
    out = {}
    for m in _HEADER_RE.finditer(mm):
        sym = m.group(1).decode("utf-8")
        start = m.end() - 1
        if mm[start + 1:start + 2] == b"]":
            out[sym] = (start, 2, 0, None)
            continue
        idx = mm.find(b"]]", start)
        if idx < 0:
            raise ValueError(f"panel array terminator not found for {sym}")
        length = idx + 2 - start
        count = mm[start:idx + 2].count(b"], [") + 1
        tail = mm[max(start, idx - 120):idx + 2].decode("utf-8", "replace")
        dm = re.search(r'\["(\d{4}-\d{2}-\d{2})", [^\]]*\]\]$', tail)
        out[sym] = (start, length, count, dm.group(1) if dm else None)
    return out


def plan_insertions(scan, fetched):
    """{byte_position: bytes} plus (appended, missing) reports.

    A fetched row is appended only when its date is strictly after
    the symbol's own last stored date; rows are emitted in the
    panel's own JSON row form."""
    insertions = {}
    appended = {}
    missing = []
    for sym, (start, length, count, last) in scan.items():
        rows = fetched.get(sym, {})
        new_dates = sorted(d for d in rows if last is None or d > last)
        if not new_dates:
            missing.append(sym)
            continue
        body = ", ".join(json.dumps(rows[d]) for d in new_dates)
        if count:
            insertions[start + length - 1] = (", " + body).encode()
        else:
            insertions[start + 1] = body.encode()
        appended[sym] = new_dates
    return insertions, appended, missing


def rewrite_with_insertions(src_path, tmp_path, insertions):
    """Stream src to tmp, inserting bytes at the sorted absolute
    positions. Positions fall between copied ranges, never inside
    a chunk boundary problem: ranges are copied explicitly."""
    positions = sorted(insertions)
    with open(src_path, "rb") as src, open(tmp_path, "wb") as dst:
        cursor = 0
        for pos in positions:
            _copy_range(src, dst, cursor, pos)
            dst.write(insertions[pos])
            cursor = pos
        src.seek(cursor)
        while True:
            chunk = src.read(8 * 1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)


def _copy_range(src, dst, start, end):
    src.seek(start)
    remaining = end - start
    while remaining > 0:
        chunk = src.read(min(8 * 1024 * 1024, remaining))
        if not chunk:
            raise IOError("short read while copying panel")
        dst.write(chunk)
        remaining -= len(chunk)


def verify_advanced(tmp_path, scan_before, appended):
    """Re-scan the rewritten panel; every symbol's count and last
    date must match the planned appends exactly. Returns problems."""
    problems = []
    with open(tmp_path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            after = scan_panel(mm)
        finally:
            mm.close()
    if set(after) != set(scan_before):
        return ["symbol set changed during advance"]
    for sym, new_dates in appended.items():
        _s, _l, count, last = after[sym]
        if count != scan_before[sym][2] + len(new_dates):
            problems.append(f"{sym}: count {count} != expected")
        if last != new_dates[-1]:
            problems.append(f"{sym}: last date {last} != {new_dates[-1]}")
        if len(problems) > 5:
            break
    return problems


def advance_panel_file(panel_path, fetched, through):
    """Advance one panel file with already-fetched bars.
    Returns (exit_code, message)."""
    with open(panel_path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            scan = scan_panel(mm)
        finally:
            mm.close()
    lasts = [v[3] for v in scan.values() if v[3]]
    panel_last = max(lasts) if lasts else None
    if panel_last is not None and panel_last >= through:
        return 0, f"deep panel already at {panel_last}; nothing to advance"
    insertions, appended, missing = plan_insertions(scan, fetched)
    if not appended:
        return 1, (f"FAIL: no new bars fetched through {through}; "
                   f"deep panel left at {panel_last}")
    tmp = panel_path + ".tmp"
    rewrite_with_insertions(panel_path, tmp, insertions)
    problems = verify_advanced(tmp, scan, appended)
    if problems:
        os.unlink(tmp)
        return 1, ("FAIL: advanced deep panel fails integrity gate: "
                   + "; ".join(problems[:5]) + "; nothing written")
    os.replace(tmp, panel_path)
    new_last = max(d[-1] for d in appended.values())
    total_new = sum(len(v) for v in appended.values())
    return 0, (f"deep panel advanced {panel_last} -> {new_last}: "
               f"{total_new} new bars across {len(appended)} symbols; "
               f"{len(missing)} symbols with no new bars"
               + (f" ({', '.join(missing[:20])})" if missing else ""))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    through = None
    if "--through" in argv:
        through = argv[argv.index("--through") + 1]
    if through is None:
        sys.path.insert(0, HERE)
        from completed_session import freshest_completed_session
        through = freshest_completed_session()
    with open(PANEL_PATH, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            scan = scan_panel(mm)
        finally:
            mm.close()
    lasts = [v[3] for v in scan.values() if v[3]]
    panel_last = max(lasts) if lasts else None
    if panel_last is not None and panel_last >= through:
        print(f"deep panel already at {panel_last}; nothing to advance")
        return 0
    sys.path.insert(0, HERE)
    from advance_price_panel import fetch_bars
    start = (date.fromisoformat(panel_last) + timedelta(days=1)).isoformat()
    end = (date.fromisoformat(through) + timedelta(days=1)).isoformat()
    fetched = fetch_bars(sorted(scan), start, end)
    code, msg = advance_panel_file(PANEL_PATH, fetched, through)
    print(msg, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
