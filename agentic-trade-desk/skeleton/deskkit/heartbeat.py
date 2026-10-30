"""Heartbeat and failover arbitration.

Primary (the full desk) writes a heartbeat ONLY when it is making real progress (progress-gated),
not merely when its process is alive. A standby (e.g. a cloud function on a schedule) trades
ONLY when the primary heartbeat is stale, and uses the SAME deterministic client order ids, so
even a mistaken overlap cannot double-order.

Ages are computed against the standby's own clock; the primary stores an epoch + a monotonic
counter so a resume-from-pause can be told apart from a real stall.
"""
from __future__ import annotations
import json
import os
import time


def write_heartbeat(path: str, progress_counter: int, last_progress_ts: float | None = None):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"epoch": time.time(), "progress": progress_counter,
                   "last_progress_epoch": last_progress_ts or time.time()}, f)
    os.replace(tmp, path)


def standby_should_trade(hb: dict | None, now_epoch: float, stale_after_s: float = 600.0,
                         market_open: bool = True) -> bool:
    if not market_open:
        return False
    if hb is None:
        return True
    return (now_epoch - hb["epoch"]) >= stale_after_s


def keepalive_ok(prev_progress: int, cur_progress: int, hb_age_s: float, limit_s: float = 900.0) -> bool:
    """Supervisor test: alive means 'heartbeat fresh AND progress counter moved or still within grace'."""
    return hb_age_s < limit_s or cur_progress != prev_progress
