"""Memory-bounded monolith-to-segments migration (EC-B16 fixture path).

The D09 precondition for the segmented-ledger migration: a
memory-bounded migration path demonstrated on a fixture before any
re-attempt against the live monolith (femto-lean
state/ledger_sidecar.jsonl, 888 MB, whole-loadable only at real risk
on this box). This module is that path, demonstrated by its blocker
tests on a fixture and deliberately format-agnostic: sidecar rows are
hash-chained state snapshots, so the migration treats lines as opaque
bytes and never parses a whole state into memory.

Method: stream the source line by line (constant memory per line),
write fixed-row-count segment files, and build a manifest carrying
per-segment sha256 plus a whole-source sha256 computed in the same
single pass. Verification re-streams the segments and proves:
segment hashes match, row counts match, and the concatenation of the
segments is byte-identical to the source (same whole hash, same byte
count) -- i.e. segmentation loses and reorders nothing, which is the
entire safety question a migration has to answer before cutover.

Cutover is NOT landed by this increment and the live path is still
the monolith; the register row stays open at the top of inspection
reports until the desk lane lands the cutover under the night
inspection's resume/verify ownership (fixture proof graded at the
Fri 2026-11-13 night inspection).
"""

import hashlib
import json
import os


def segment_file(src_path, out_dir, rows_per_segment=10000):
    """Segment src_path into out_dir; returns the manifest dict.

    Streams: at any moment only one line and the running hashes are in
    memory, regardless of source size.
    """
    os.makedirs(out_dir, exist_ok=True)
    segments = []
    total_rows = 0
    total_bytes = 0
    whole = hashlib.sha256()
    seg_index = 0
    seg_rows = 0
    seg_bytes = 0
    seg_hash = hashlib.sha256()
    seg_file = None
    seg_name = None

    def _close_segment():
        nonlocal seg_file
        if seg_file is not None:
            seg_file.close()
            segments.append(
                {
                    "name": seg_name,
                    "rows": seg_rows,
                    "bytes": seg_bytes,
                    "sha256": seg_hash.hexdigest(),
                }
            )
            seg_file = None

    with open(src_path, "rb") as src:
        for raw in src:
            if seg_file is None or seg_rows >= rows_per_segment:
                _close_segment()
                seg_index += 1
                seg_rows = 0
                seg_bytes = 0
                seg_hash = hashlib.sha256()
                seg_name = "segment-%06d.jsonl" % seg_index
                seg_file = open(os.path.join(out_dir, seg_name), "wb")
            seg_file.write(raw)
            seg_hash.update(raw)
            whole.update(raw)
            seg_rows += 1
            seg_bytes += len(raw)
            total_rows += 1
            total_bytes += len(raw)
    _close_segment()

    keep = {seg["name"] for seg in segments}
    for name in os.listdir(out_dir):
        if (
            name.startswith("segment-")
            and name.endswith(".jsonl")
            and name not in keep
        ):
            os.remove(os.path.join(out_dir, name))

    manifest = {
        "format": "ledger-segments/1",
        "source": os.path.basename(src_path),
        "total_rows": total_rows,
        "total_bytes": total_bytes,
        "source_sha256": whole.hexdigest(),
        "rows_per_segment": rows_per_segment,
        "segments": segments,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def verify_segments(out_dir):
    """Re-stream the segments under out_dir against the manifest.

    Returns {"ok": bool, "total_rows": int, "problems": [str]}; the
    decisive check is that the segments' concatenation hashes to the
    manifest's source_sha256 (byte-identical round trip).
    """
    problems = []
    with open(os.path.join(out_dir, "manifest.json"), "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    whole = hashlib.sha256()
    total_rows = 0
    total_bytes = 0
    for seg in manifest.get("segments", []):
        digest = hashlib.sha256()
        rows = 0
        nbytes = 0
        with open(os.path.join(out_dir, seg["name"]), "rb") as fh:
            for raw in fh:
                digest.update(raw)
                whole.update(raw)
                rows += 1
                nbytes += len(raw)
        if rows != seg["rows"] or nbytes != seg["bytes"]:
            problems.append("%s: rows/bytes mismatch" % seg["name"])
        if digest.hexdigest() != seg["sha256"]:
            problems.append("%s: sha256 mismatch" % seg["name"])
        total_rows += rows
        total_bytes += nbytes
    if total_rows != manifest.get("total_rows"):
        problems.append("total rows mismatch")
    if total_bytes != manifest.get("total_bytes"):
        problems.append("total bytes mismatch")
    if whole.hexdigest() != manifest.get("source_sha256"):
        problems.append("concatenation sha256 != source sha256")
    return {"ok": not problems, "total_rows": total_rows, "problems": problems}
