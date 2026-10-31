#!/usr/bin/env python3
"""Shared verdict vocabulary for the Replication Wire and every
consumer that reads it (VERDICT-VOCAB-20261031).

One source of truth: the Wire's producer
(refresh_replicationwire.py) emits exactly these verdicts, and
every consumer (Router, Survivors Wire, Graveyard) accepts
exactly these verdicts, each in its own bucket, in these plain
words. A verdict is never folded into another bucket: in
particular "untestable" (added to the Wire on 2026-10-30 for
claims whose deciding record does not exist on hand) is not
"partly" and not "not_yet".

Before this module, each consumer carried its own verdict set;
when the Wire learned "untestable", both the Router and the
Survivors Wire failed closed on every refresh. The contract
blocker in forecast/tests/test_tools_b_cures_20261031.py fails
when the Wire emits a verdict this vocabulary does not carry,
or when a consumer stops importing it.
"""

VERDICT_WORDS = {
    "held": "Held up",
    "partly": "Partly held up",
    "did_not": "Did not hold up",
    "not_yet": "Not yet tested",
    "untestable": "Cannot be tested on the records on hand",
}

VERDICTS = tuple(VERDICT_WORDS)


def empty_counts():
    """A zero count bucket for every verdict, plus the total."""
    counts = {"total": 0}
    for verdict in VERDICTS:
        counts[verdict] = 0
    return counts
