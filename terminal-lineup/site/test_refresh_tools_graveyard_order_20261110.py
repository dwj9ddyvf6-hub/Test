"""Regression blocker for GRAVEYARD-WIRE-ORDER-20261110.

Failure of record: refresh_tools.py ran refresh_survivorswire.py
BEFORE refresh_graveyard.py in the assemblies group. The
Graveyard restates the Replication Wire and stamps the wire
grading_run_at it read; Survivors Wire refuses when that stamp
is not the Wire's current one. The Wire is re-graded earlier in
the evening, so the checker ran against the Graveyard's previous
restatement (2026-11-10: Graveyard carried the 15:07 grading
against the Wire's 21:58 re-grade) and failed with "the
Graveyard's grading time is not the Wire's", even though running
the Graveyard first made the pair agree exactly.

Cure pinned here: in refresh_tools' group order, the Graveyard
(the producer of the restatement) precedes Survivors Wire (its
checker). Pre-cure order fails this assertion.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refresh_tools  # noqa: E402


def _flat_order():
    out = []
    for _group, scripts in refresh_tools.GROUPS:
        out.extend(scripts)
    return out


def test_graveyard_precedes_survivorswire():
    order = _flat_order()
    assert order.index("refresh_graveyard.py") < \
        order.index("refresh_survivorswire.py")
