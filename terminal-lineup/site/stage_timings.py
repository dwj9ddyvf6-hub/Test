#!/usr/bin/env python3
"""Stage-timing records for the forecast refresh runner.

The runner (refresh_engines.py) already prints one duration line per
stage ("done <stage> in <N>s exit <X>") into its proof log. This
module turns those prints, plus the run's total wall time measured
by the runner's main(), into one structured record per run:

    {run_id, runner, started_at, finished_at, total_s, exit_code,
     stages: [{stage, duration_s, outcome}], unattributed_s,
     source: "runner_prints+main_timer"}

Stage start/end timestamps are not recoverable from the prints and
are recorded as null rather than fabricated; durations come from
the runner's own prints (integer seconds, as printed). The
unattributed remainder (total minus the sum of printed stage
durations) covers the untimed stages (Record, enrich, smoke,
publish) and print rounding, so stages + unattributed == total by
construction and any large unattributed share is itself visible.
Because the prints carry integer seconds, the remainder can be
small-negative (bounded by half a second per printed stage) when
rounded stage prints sum above the true total; that is the
rounding term made visible, not an error.

Appending a record must never fail a refresh: callers wrap the
append in try/except.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

_DONE_RE = re.compile(
    r"^done (?P<stage>.+?) in (?P<secs>\d+(?:\.\d+)?)s "
    r"exit (?P<exit>-?\d+)", re.M)
_OUTCOME_ONLY = (
    ("record-surface enrich", re.compile(
        r"^record-surface enrich exit (?P<exit>-?\d+)", re.M)),
    ("publish-live", re.compile(
        r"^publish-live proof exit (?P<exit>-?\d+)", re.M)),
)


def parse_stages(proof_text: str) -> list[dict]:
    stages = []
    for m in _DONE_RE.finditer(proof_text):
        stages.append({
            "stage": m.group("stage"),
            "start": None,
            "end": None,
            "duration_s": float(m.group("secs")),
            "outcome": "ok" if m.group("exit") == "0"
                       else f"exit {m.group('exit')}",
        })
    for name, rx in _OUTCOME_ONLY:
        m = rx.search(proof_text)
        if m:
            stages.append({
                "stage": name,
                "start": None,
                "end": None,
                "duration_s": None,
                "outcome": "ok" if m.group("exit") == "0"
                           else f"exit {m.group('exit')}",
            })
    return stages


def build_record(proof_text: str, total_s: float, exit_code: int,
                 started_at: str | None = None,
                 run_id: str | None = None) -> dict:
    stages = parse_stages(proof_text)
    timed = sum(s["duration_s"] for s in stages
                if s["duration_s"] is not None)
    return {
        "run_id": run_id or ("refresh-"
                             + datetime.now(timezone.utc).strftime(
                                 "%Y%m%dT%H%M%SZ")),
        "runner": "refresh_engines.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "total_s": round(float(total_s), 3),
        "exit_code": exit_code,
        "stages": stages,
        "unattributed_s": round(float(total_s) - timed, 3),
        "source": "runner_prints+main_timer",
    }


def append_record(record: dict, path: Path) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
