"""Aligned tick scheduler: passes run a few seconds after each bar boundary; late wakes catch up ONCE.

* A pass never starts 'every 300 s from an arbitrary start' (drift moves it out of critical windows).
* After a pause the next boundary runs one catch-up pass, not every missed slot.
* A due pass runs BEFORE same-tick side jobs (publish, backup).
* `guaranteed_pass_needed`: inside a critical window, if no pass ran in the last N seconds, run one now.
"""
from __future__ import annotations
import math


def next_boundary(now_epoch: float, period_s: int = 300, offset_s: int = 20) -> float:
    """Epoch of the next boundary strictly after now: k*period + offset."""
    k = math.floor((now_epoch - offset_s) / period_s) + 1
    return k * period_s + offset_s


def due_slot(last_run_epoch: float, now_epoch: float, period_s: int = 300, offset_s: int = 20) -> bool:
    """True if at least one boundary passed since the last run (catch-up collapses to one)."""
    return next_boundary(last_run_epoch, period_s, offset_s) <= now_epoch


def guaranteed_pass_needed(in_critical_window: bool, last_pass_epoch: float, now_epoch: float,
                           max_gap_s: float = 480) -> bool:
    return in_critical_window and (now_epoch - last_pass_epoch) > max_gap_s


def order_tick(jobs: list[str]) -> list[str]:
    """Due pass first, then side jobs (stable order)."""
    return sorted(jobs, key=lambda j: 0 if j == "pass" else 1)
