"""Regression blockers for the 2026-10-30 remainders fix stream 3.

Fail directions, each proven against the pre-cure state:
- R-06: neither Engine 19 nor Engine 20 page carried a proof gate
  block, and neither refresher mentioned the gate. The shared
  builder (site/proof_gate_block.py) must embed a block whose
  counts recount from proof-gate/data.json and from the Engine 19
  forward rows in the forecast ledger, and must refuse a tampered
  gate. On the pre-cure tree the module does not exist and both
  data files lack the key, so every test below fails.
- R-10: refresh_gapfill.py, refresh_openingrange.py and
  refresh_fearday.py refused every coherent cycle by demanding
  the feed's board session date equal the study card's run date
  (all three exited 1 live on 2026-10-30 with exactly that
  refusal). The cure is the earnings-drift pattern: exact figure
  agreement plus generation order. Source assertions pin the
  removal and the replacement; final-data tests read the
  republished pages.
"""
import importlib.util
import json
import os
import sys

LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
SITE = os.path.join(LINEUP, "site")
LEDGER = os.path.join(LINEUP, "forecast", "ledger.jsonl")
sys.path.insert(0, SITE)


def _src(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def _data(slug):
    with open(os.path.join(SITE, slug, "data.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _gate():
    return _data("proof-gate")


# ---- RC-06 follow-on: Engine 12's league pin binds to its page ----
# refresh_calibrationleague refused every run once Engine 12's
# abstention rows began ledgering: its pin demanded the ledger
# count be a multiple of 3 (whole companies x 3 figures) with a
# floor of 24, but the ledger also carries the page's 9
# not-recorded rows beside its 34 taken rows (43 total). The cure
# binds Engine 12 to its own page like every other entrant: the
# ledger count must equal the page's taken plus not-recorded
# counts. These assertions fail on the pinned code.

def test_calibrationleague_engine12_binds_to_its_own_page():
    src = _src("refresh_calibrationleague.py")
    assert 'live_counts["engine_12"] % 3' not in src
    assert '"engine_12", "engine_15"' in src
    assert 'd["live"]["distribution_forecasts_recorded"]' in src
    assert 'd["live"]["not_recorded_rows"]' in src


def test_engine20_page_carries_recounting_proof_gate_block():
    gate = _gate()
    block = _data("calibration-league")["proof_gate"]
    assert block["source_as_of"] == gate["as_of"]
    assert block["names_scanned"] == gate["counts"]["names_scanned"]
    assert block["forward_records_created"] == \
        gate["forward_ledger"]["created"]
    assert block["ledger_rows_recounted"] == \
        block["forward_records_created"]
    assert block["ledger_rows_total"] == \
        gate["forward_ledger"]["ledger_rows"]
    assert block["ledger_duplicate_rows"] == 19


# ---- RC-27: refresh_analogue carries the cured date pattern ----
# The re-census carried analogue as a latent date equality risk
# with no evidenced cure. Inspection on 2026-10-30 shows the
# cured pattern already in the code (generation order, never an
# equality demand between the card's run date and the feed's
# board session); what was missing is the blocker. These source
# assertions fail on the pre-cure equality pattern and pass on
# the code as found, so the class cannot return silently.

def test_analogue_uses_generation_order_not_date_equality():
    src = _src("refresh_analogue.py")
    assert "feed_gen < card_gen" in src
    assert "does not postdate the studies card" in src
    # No equality demand between the two different date kinds.
    assert 'feed.get("as_of") == as_of' not in src
    assert 'feed.get("as_of_session") == as_of' not in src
    assert "never equality of those two different date kinds" in src


# ---- R-06: the shared proof gate block ----

def test_both_refreshers_use_the_shared_builder():
    for name in ("refresh_inregimeoracle.py",
                 "refresh_calibrationleague.py"):
        src = _src(name)
        assert "build_proof_gate_block" in src, name
        assert "proof_gate_block" in src, name


def test_engine19_page_carries_recounting_proof_gate_block():
    gate = _gate()
    block = _data("in-regime-oracle")["proof_gate"]
    assert block["source_as_of"] == gate["as_of"]
    assert block["names_scanned"] == gate["counts"]["names_scanned"]
    assert block["by_state"] == gate["counts"]["by_state"]
    assert block["forward_records_created"] == \
        gate["forward_ledger"]["created"]
    assert block["ledger_rows_recounted"] == \
        block["forward_records_created"]
    assert sum(block["by_state"].values()) == block["names_scanned"]
    assert "provisional" in block["words"]


def test_builder_recounts_and_refuses_tamper(tmp_path):
    from proof_gate_block import (ProofGateError,
                                  build_proof_gate_block)
    block = build_proof_gate_block(SITE, "engine_20", "2026-10-29",
                                   LEDGER)
    # The tie is per distinct name against the gate's cumulative
    # created count (RC-05 cure, 2026-10-30): the first partial
    # scan's 19 superseded rows stay on the append only ledger
    # and are named, not counted twice and not hidden.
    gate = _gate()
    assert block["ledger_rows_recounted"] == \
        block["forward_records_created"] == \
        gate["forward_ledger"]["created"]
    assert block["ledger_rows_total"] == \
        gate["forward_ledger"]["ledger_rows"]
    assert block["ledger_duplicate_rows"] == \
        block["ledger_rows_total"] - block["ledger_rows_recounted"]
    if block["ledger_duplicate_rows"]:
        assert "superseded" in block["words"]
    # A gate that does not name the engine is refused.
    try:
        build_proof_gate_block(SITE, "engine_99", "2026-10-29",
                               LEDGER)
    except ProofGateError:
        pass
    else:
        raise AssertionError("unnamed engine was not refused")
    # A gate from the future is refused.
    try:
        build_proof_gate_block(SITE, "engine_20", "2026-10-27",
                               LEDGER)
    except ProofGateError:
        pass
    else:
        raise AssertionError("future gate was not refused")
    # A tampered gate count is refused (recount disagreement).
    fake = tmp_path / "site"
    (fake / "proof-gate").mkdir(parents=True)
    gate = _gate()
    gate["forward_ledger"] = dict(gate["forward_ledger"],
                                  created=gate["forward_ledger"]
                                  ["created"] + 1)
    with open(fake / "proof-gate" / "data.json", "w",
              encoding="utf-8") as fh:
        json.dump(gate, fh)
    try:
        build_proof_gate_block(str(fake), "engine_20", "2026-10-29",
                               LEDGER)
    except ProofGateError:
        pass
    else:
        raise AssertionError("tampered gate was not refused")


# ---- R-10: date-kind equality refusals removed ----

def test_date_equality_refusal_gone_generation_order_present():
    for name in ("refresh_gapfill.py", "refresh_openingrange.py",
                 "refresh_fearday.py"):
        src = _src(name)
        assert "the published summary is dated" not in src, name
        assert "generation time must not precede" in src, name


def test_r10_pages_republished_on_the_cured_refreshers():
    # All three exited 1 before the cure and 0 after it, on the
    # same live sources; the republished pages carry the study
    # card's own date, not the board session the feed carries.
    assert _data("gap-fill")["as_of"] == "2026-10-29"
    assert _data("opening-range")["as_of"] == "2026-10-29"
    # Fear Day carries the card's generation stamp, not an as_of.
    assert _data("fear-day")["published_at_utc"] == \
        "2026-10-29T20:51:16.967158+00:00"
