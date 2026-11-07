"""Regression blocker for TOOLS-CHAIN-PIN-ORDER-20261107.

Failure of record (tools runs of Thu 2026-11-05 and Fri
2026-11-06, both FAILED on this leg): refresh_morning_map.py
failed exit 1 because its chained Gamma Ladder re-run read
the Expiry Pin Watch page one session behind the session the
Morning Map had just published (pin snapshot day 2026-11-04
vs session 2026-11-05 on Thursday; 2026-11-05 vs 2026-11-06
on Friday), and the ladder refused to publish a mixed state.

Root cause: refresh_morning_map chains refresh_gammaladder
at the end of every republication (MAP-LADDER-CHAIN-20261031),
and the ladder reads expiry-pin-watch/data.json. In the
tools chain the producers group ran refresh_morning_map
BEFORE refresh_pinwatch, so the chained ladder always read
the pin page as the PREVIOUS evening left it: guaranteed
one session stale on every run, however healthy the chain
snapshot store was (the morgue collector stores the current
session's SPY/QQQ/IWM snapshots by about 16:00 ET, hours
before this 19:00 chain).

Cure pinned here: the chain produces the pin snapshot for
the current session, by the lane that owns it, before the
Morning Map leg that consumes it: refresh_pinwatch.py runs
ahead of refresh_morning_map.py in the flattened chain
order, and the Gamma Ladder's own slot stays after both.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refresh_tools  # noqa: E402


def _flat_order():
    order = ["advance_price_panel.py"]
    for _group, scripts in refresh_tools.GROUPS:
        order.extend(scripts)
    order.append("tape_family_run.py")
    return order


def test_pinwatch_runs_before_morning_map():
    order = _flat_order()
    assert order.index("refresh_pinwatch.py") < order.index(
        "refresh_morning_map.py"), (
        "the Pin Watch refresh must land before the Morning "
        "Map leg whose chained Gamma Ladder reads the pin page")


def test_gamma_ladder_slot_stays_after_both():
    order = _flat_order()
    assert order.index("refresh_gammaladder.py") > order.index(
        "refresh_pinwatch.py")
    assert order.index("refresh_gammaladder.py") > order.index(
        "refresh_morning_map.py")
