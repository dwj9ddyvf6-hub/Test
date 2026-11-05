"""Regression blocker for EXCEEDANCE-NOTE-VOID-20261104.

The Exceedance page's same-session republication note promised
that every earlier-run row "stays on the record and will be
graded". That stopped being true when the SUPN triple of
2026-11-03 was voided on the ledger (Q1 gap-destiny precedent:
the name's missing 2026-11-02 bar was filled, the publication
was voided and reissued, and voided rows are never graded).
The note's generation now names any voided subjects and says
they will not be graded; with no voids the original wording
stands.

Fail direction on the pre-cure code: refresh_exceedance has no
superseded_block builder and the note is an unconditional
literal, so these tests fail at import/attribute on the old
file and pass on the cured one.
"""
import importlib.util
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_exceedance", os.path.join(SITE, "refresh_exceedance.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ORIGINAL_NOTE = (
    "Forecast rows published by an earlier run of this same "
    "session stay on the record and will be graded; they are "
    "not part of the live set above. Subjects lists the names "
    "that qualified in an earlier run only; parallel subjects "
    "are names whose declared outcomes moved between runs, so "
    "both publications stand on the record.")


def test_no_voids_keeps_original_note():
    block = mod.superseded_block([], ["SUPN"], [])
    assert block["note"] == ORIGINAL_NOTE
    assert block["voided_subjects"] == []
    assert block["parallel_subjects"] == ["SUPN"]


def test_voided_subject_is_named_and_not_promised_grading():
    block = mod.superseded_block([], ["SUPN"], ["SUPN"])
    note = block["note"]
    assert "SUPN" in note
    assert "will not be graded" in note
    assert "voided on the record" in note
    assert "and will be graded; they are not part" not in note
    assert block["voided_subjects"] == ["SUPN"]


# Appended 2026-11-04 night (terminal total-fix loop, AUDIT-1 row
# A1-06 completion): the all-empty case. On the 2026-11-04 session
# there was no same-session republication at all (subjects,
# parallel and voided all empty), yet the block still printed the
# republication narrative and its blanket "will be graded"
# promise. The block must say plainly that the session has a
# single publication when that is the fact.
def test_no_republication_states_single_publication():
    block = mod.superseded_block([], [], [])
    note = block["note"]
    assert "will be graded" not in note
    assert "single publication" in note
    assert block["subjects"] == []
    assert block["parallel_subjects"] == []
    assert block["voided_subjects"] == []
