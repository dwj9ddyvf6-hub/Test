"""Scheduler (V3-SCOPE §7.7): cadence classes on one loop, restart-safe.
State (next-fire per sleeve + consumed-bar cursors) lives on disk; a
restart resumes from it and never re-fires a consumed bar (v2 cursor
semantics, persisted — v2 kept them in memory only). Overlap = skip:
a sleeve still marked running from a previous life is not double-fired;
its next fire is its cadence boundary."""
from __future__ import annotations
import json, os
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def cadence_class(cadence_s):
    if cadence_s <= 60:
        return "fast"
    if cadence_s <= 300:
        return "standard"
    if cadence_s <= 3600:
        return "slow"
    return "daily"


def in_session(entry, now):
    if entry.get("session") == "24h":
        return True
    et = now.astimezone(ET)
    t = et.timetz().replace(tzinfo=None)
    return dtime(9, 30) <= t < dtime(16, 0) and et.weekday() < 5


class Scheduler:
    def __init__(self, root, entries, session_check=in_session,
                 timings_sink=None):
        self.root = os.path.abspath(root)
        self.entries = entries
        self.session_check = session_check
        # Stage timings (GLORY item 2b): optional sink for one
        # stage_timings record per tick. None (the default, and what
        # every existing caller passes) means no record and no file
        # I/O; a path string appends JSONL; a callable receives the
        # record dict. Additive instrumentation only: the tick's
        # decisions and return value are unchanged.
        self.timings_sink = timings_sink
        self.state_path = os.path.join(self.root, "state", "scheduler.json")
        self.state = {"next_fire": {}, "cursors": {}}
        if os.path.exists(self.state_path):
            try:
                self.state = json.load(open(self.state_path))
            except Exception:
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        tmp = self.state_path + ".tmp"
        json.dump(self.state, open(tmp, "w"), sort_keys=True)
        os.replace(tmp, self.state_path)

    def mark_consumed(self, sleeve_id, bar_ts):
        self.state["cursors"][sleeve_id] = float(bar_ts)
        self._save()

    def _emit_timings(self, record):
        sink = self.timings_sink
        if sink is None:
            return
        try:
            if callable(sink):
                sink(record)
            else:
                with open(sink, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, sort_keys=True) + "\n")
        except Exception:
            pass  # instrumentation must never break a tick

    def tick(self, now=None):
        import time as _time
        _t0 = _time.monotonic()
        _stage_start = _t0
        now = now or datetime.now(ET)
        if now.tzinfo is None:
            now = now.replace(tzinfo=ET)
        now_ts = now.timestamp()
        fired = []
        for entry in self.entries:
            sid = entry["id"]
            if entry.get("parked"):
                continue
            if not self.session_check(entry, now):
                continue
            cad = float(entry["cadence_s"])
            cycle_key = int(now_ts // cad)
            cursor = self.state["cursors"].get(sid)
            if cursor is not None and int(float(cursor) // cad) >= cycle_key:
                continue  # bar for this cycle already consumed
            nxt = self.state["next_fire"].get(sid)
            if nxt is not None and now_ts < float(nxt):
                continue
            self.state["next_fire"][sid] = now_ts + cad
            fired.append(sid)
        _scan_end = _time.monotonic()
        if fired:
            self._save()
        _end = _time.monotonic()
        if self.timings_sink is not None:
            self._emit_timings({
                "run_id": f"tick-{int(now_ts)}",
                "runner": "desk3/scheduler.py:tick",
                "started_at": None,
                "finished_at": None,
                "total_s": round(_end - _t0, 6),
                "exit_code": 0,
                "stages": [
                    {"stage": "tick_scan", "start": None, "end": None,
                     "duration_s": round(_scan_end - _stage_start, 6),
                     "outcome": f"ok fired={len(fired)}"},
                    {"stage": "state_save", "start": None, "end": None,
                     "duration_s": round(_end - _scan_end, 6),
                     "outcome": "ok" if fired else "skipped_no_fire"},
                ],
                "unattributed_s": round(
                    (_end - _t0) - ((_scan_end - _stage_start)
                                    + (_end - _scan_end)), 6),
                "source": "monotonic_timer+sink",
            })
        return fired
