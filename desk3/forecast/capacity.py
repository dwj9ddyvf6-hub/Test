"""Capacity per candidate (FACTORY.md §4 step 9): cap_i = PARTICIPATION x ADV$_20 x h / turnover per name, turnover
= 1 (one entry per h-session holding). A cell whose median capacity per name is under TINY_USD is `tiny` and its
weight is capped later (§7)."""
import numpy as np

PARTICIPATION = 0.01
TINY_USD = 10_000.0


def cap(dv20, h, turnover=1.0):
    return PARTICIPATION * np.asarray(dv20, float) * h / turnover


def note(median_cap):
    if median_cap is None or not np.isfinite(median_cap):
        return "capacity unknown"
    word = "tiny" if median_cap < TINY_USD else "ok"
    return f"median capacity ${median_cap:,.0f} per name per entry (1% ADV x h): {word}"
