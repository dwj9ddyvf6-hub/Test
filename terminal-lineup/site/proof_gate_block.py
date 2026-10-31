#!/usr/bin/env python3
"""Shared proof gate block for the pages that consume the gate.

One builder, used by both consuming refreshers (Engine 19,
refresh_inregimeoracle.py, and Engine 20,
refresh_calibrationleague.py), so the block embedded in each page
can never drift into two copies of the same figures.

The gate file (proof-gate/data.json) is the source of truth for its
own scan: its counts are copied, never recomputed from names. The
one figure this builder computes itself is the recount of the
gate's forward record in the forecast ledger: the Engine 19
forecast rows carrying the gate's forward quantity, counted per
distinct name. Publication fails closed when that recount differs
from the number of forward records the gate says are on record,
when the gate does not name the consuming engine, when the gate
file is missing, or when the gate is dated after the page that
would carry it (a gate from the future means the page is stale,
not fresh).

Count semantics (cured 2026-10-30, RC-05): the gate's
forward_ledger.created is the cumulative count of distinct names
with a forward record on the ledger, not the last run's creation
count (a rerun creates nothing and must not zero the record).
The ledger is append only and one scan can supersede another:
the first partial scan (4,641 names) wrote 19 names whose
Benjamini-Hochberg q values changed when the full 15,815 name
scan recomputed the correction, and the changed values defeated
the ledger's value hash dedupe, so those 19 names carry two rows
each. Both rows stay on the record; this block counts each name
once and names the superseded rows as ledger_duplicate_rows
instead of letting them break or inflate the count.

Every state the gate publishes is provisional, and the block says
so in plain words on the page itself.
"""

import json
import os

FORWARD_QUANTITY = "provisional_proof_state_forward_return_10s"
FORWARD_ENGINE = "engine_19"


class ProofGateError(ValueError):
    """The proof gate block cannot be built honestly."""


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def recount_forward_rows(ledger_path):
    """Recount the gate's forward record in the forecast ledger.

    Returns (distinct_names, total_rows): the record is one
    forward forecast per name, so the recount that must tie to
    the gate is the distinct name count; total_rows is returned
    so the superseded rows (see the module docstring) are named,
    never silently absorbed.
    """
    subjects = set()
    rows = 0
    with open(ledger_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("type") == "forecast" \
                    and row.get("engine_id") == FORWARD_ENGINE \
                    and row.get("quantity") == FORWARD_QUANTITY:
                rows += 1
                subjects.add(row.get("subject"))
    return len(subjects), rows


def build_proof_gate_block(site_dir, engine_id, page_as_of, ledger_path):
    """Build the proof_gate block for one consuming page.

    Raises ProofGateError on any disagreement; callers fail closed.
    """
    gate_path = os.path.join(site_dir, "proof-gate", "data.json")
    if not os.path.exists(gate_path):
        raise ProofGateError(
            f"the proof gate record is missing ({gate_path}); "
            "refusing to publish a page without its gate block.")
    gate = _load_json(gate_path)
    consuming = gate.get("consuming_engines") or []
    if engine_id not in consuming:
        raise ProofGateError(
            f"the proof gate record names consuming engines "
            f"{consuming}, not {engine_id}; refusing to embed a "
            "gate this page does not consume.")
    gate_as_of = gate.get("as_of")
    if not gate_as_of or not page_as_of or gate_as_of > page_as_of:
        raise ProofGateError(
            f"the proof gate is dated {gate_as_of} and this page "
            f"is dated {page_as_of}; refusing to publish a gate "
            "from the future on a stale page.")
    counts = gate.get("counts") or {}
    by_state = counts.get("by_state") or {}
    names_scanned = counts.get("names_scanned")
    forward = gate.get("forward_ledger") or {}
    created = forward.get("created")
    if names_scanned is None or created is None \
            or sum(by_state.values()) != names_scanned:
        raise ProofGateError(
            "the proof gate record's own counts do not hold "
            f"together (names_scanned {names_scanned}, by_state "
            f"{by_state}, forward created {created}); refusing "
            "to embed a gate whose figures disagree with "
            "themselves.")
    recounted, total_rows = recount_forward_rows(ledger_path)
    if recounted != created:
        raise ProofGateError(
            f"the proof gate says {created} forward records are "
            f"on record but the forecast ledger holds "
            f"{recounted} distinct Engine 19 names with forward "
            "rows of its quantity; refusing to publish a gate "
            "block that does not recount.")
    ledger_rows = forward.get("ledger_rows")
    if ledger_rows is not None and ledger_rows != total_rows:
        raise ProofGateError(
            f"the proof gate says {ledger_rows} forward rows are "
            f"on the ledger but the recount finds {total_rows}; "
            "refusing to publish a gate block that does not "
            "recount.")
    duplicate_rows = total_rows - recounted
    supported = by_state.get("SUPPORTED", 0)
    words = (
        "The proof gate scanned "
        f"{names_scanned} names and wrote each name's "
        "provisional state to the forward record, where it "
        "will be checked against what the name does next. "
        "Every state is provisional: "
        f"{by_state.get('MIXED', 0)} names read MIXED, "
        f"{by_state.get('OBSERVING', 0)} are still OBSERVING, "
        f"and {supported} "
        + ("name is" if supported == 1 else "names are")
        + " SUPPORTED today"
        + ("." if supported else
           ", so no name on this page is shown as proven."))
    if duplicate_rows:
        words += (
            f" {duplicate_rows} names carry an earlier superseded "
            "row from the first partial scan beside their current "
            "one; the record is append only, both rows stay on "
            "it, and every count on this page counts each name "
            "once.")
    return {
        "source_as_of": gate_as_of,
        "names_scanned": names_scanned,
        "by_state": by_state,
        "forward_records_created": created,
        "forward_duplicates": forward.get("duplicates", 0),
        "ledger_rows_recounted": recounted,
        "ledger_rows_total": total_rows,
        "ledger_duplicate_rows": duplicate_rows,
        "words": words,
    }
