"""Durable append-only fill ledger: builder (DURABLE-FILL-LEDGER).

First landed increment, 2026-11-11. The defect: fills live only as
dispatcher journal events across four preserved journal generations
(38,971 rows at the 2026-11-11 night count), so there is no durable
fill record of its own. Per the estate's 2026-10-23 ledger standard,
the durable form is immutable segments plus a manifest.

This module is the BUILDER only: it streams journal generations,
extracts fill rows, dedupes them on their natural key, and writes
immutable JSONL segments plus manifest.json (per-segment row counts
and sha256, totals, duplicate count). It is not consumed by any live
cycle yet; the register row closes when a live cycle consumes the
ledger with reconcile imported_rows staying 0 against it.

Dedupe key: (intent_id, broker_order_id, ts). A fill re-journaled by a
later generation (the heal path re-imports fills) carries the same
key; re-journaled copies are dropped and counted, never silently.
Rows are written canonicalised (json.dumps, sort_keys) so a rebuild
from the same journals produces byte-identical segments and therefore
an identical manifest: the build is idempotent and its proof is a
hash comparison, not a log line.
"""

import hashlib
import json
import os


def fill_key(row):
    return (row.get("intent_id"), row.get("broker_order_id"), row.get("ts"))


def iter_fill_rows(journal_paths):
    """Stream fill rows from journal generation files, in path order.

    Malformed lines are skipped (journal generations carry a small
    number of torn tail lines); fill rows only, everything else in the
    journal is not the ledger's business.
    """
    for path in journal_paths:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("event") == "fill":
                    yield row


def build_ledger(journal_paths, out_dir, rows_per_segment=5000):
    """Build (or rebuild) the ledger under out_dir; returns the manifest.

    out_dir is created if needed. Existing segment files from a prior
    build with a higher segment count are removed so a rebuild never
    leaves stale trailing segments behind its own manifest.
    """
    os.makedirs(out_dir, exist_ok=True)
    seen = set()
    segments = []
    total = 0
    duplicates = 0
    seg_index = 0
    seg_rows = 0
    seg_hash = hashlib.sha256()
    seg_file = None

    def _open_segment():
        nonlocal seg_index, seg_rows, seg_hash, seg_file
        seg_index += 1
        seg_rows = 0
        seg_hash = hashlib.sha256()
        name = "fills-%06d.jsonl" % seg_index
        seg_file = open(os.path.join(out_dir, name), "w", encoding="utf-8")
        return name

    seg_name = None
    try:
        for row in iter_fill_rows(journal_paths):
            key = fill_key(row)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            if seg_file is None or seg_rows >= rows_per_segment:
                if seg_file is not None:
                    seg_file.close()
                    segments.append(
                        {
                            "name": seg_name,
                            "rows": seg_rows,
                            "sha256": seg_hash.hexdigest(),
                        }
                    )
                seg_name = _open_segment()
            encoded = (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
            seg_file.write(encoded.decode("utf-8"))
            seg_hash.update(encoded)
            seg_rows += 1
            total += 1
        if seg_file is not None:
            seg_file.close()
            segments.append(
                {"name": seg_name, "rows": seg_rows, "sha256": seg_hash.hexdigest()}
            )
            seg_file = None
    finally:
        if seg_file is not None:
            seg_file.close()

    # Remove stale segments from any earlier, larger build.
    keep = {seg["name"] for seg in segments}
    for name in os.listdir(out_dir):
        if name.startswith("fills-") and name.endswith(".jsonl") and name not in keep:
            os.remove(os.path.join(out_dir, name))

    manifest = {
        "format": "fill-ledger/1",
        "built_from": [os.path.basename(p) for p in journal_paths],
        "total_fills": total,
        "duplicates_dropped": duplicates,
        "segments": segments,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def verify_ledger(out_dir):
    """Re-read the ledger under out_dir against its manifest, streaming.

    Returns {"ok": bool, "total_fills": int, "problems": [str]}. Checks
    per-segment row counts and sha256, total count, and that no fill
    key repeats across the whole ledger.
    """
    problems = []
    with open(os.path.join(out_dir, "manifest.json"), "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    seen = set()
    total = 0
    for seg in manifest.get("segments", []):
        path = os.path.join(out_dir, seg["name"])
        digest = hashlib.sha256()
        rows = 0
        with open(path, "rb") as fh:
            for raw in fh:
                digest.update(raw)
                rows += 1
                try:
                    row = json.loads(raw.decode("utf-8"))
                except ValueError:
                    problems.append("%s: unparsable row" % seg["name"])
                    continue
                key = fill_key(row)
                if key in seen:
                    problems.append("%s: duplicate fill key %r" % (seg["name"], key))
                seen.add(key)
        if rows != seg["rows"]:
            problems.append(
                "%s: rows %d != manifest %d" % (seg["name"], rows, seg["rows"])
            )
        if digest.hexdigest() != seg["sha256"]:
            problems.append("%s: sha256 mismatch" % seg["name"])
        total += rows
    if total != manifest.get("total_fills"):
        problems.append(
            "total %d != manifest %d" % (total, manifest.get("total_fills"))
        )
    return {"ok": not problems, "total_fills": total, "problems": problems}
