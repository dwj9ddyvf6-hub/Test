#!/bin/sh
# muse-desk-v3 regression gate: every blocker test file must pass.
# CURE3-3: TMPDIR is redirected to a disk-backed dir inside the repo
# and removed on exit. Blocker tests create thousands of mkdtemp dirs;
# on the default 512MB /tmp tmpfs they leaked until ENOSPC made the
# gate environment-fragile (verifier round 3). The gate now owns its
# temp space, so a green gate is a property of the tree, not of /tmp.
# GATE-MASK-20261026: the previous form piped unittest through
# `| tail -5`; POSIX sh has no pipefail, so the pipeline's exit status
# was tail's (always 0) and the gate could NEVER return failure.
# unittest now writes to a log inside GATE_TMP; its own exit code is
# captured and re-raised as this script's exit code. The tail is still
# printed for humans. Proof both directions is in BUGLOG_2026-10-26.md
# (GATE-MASK-20261026) and tests/test_gate_mask_20261026_blockers.py.
# GATE-EVIDENCE-DESTRUCTION + GATE-CONCURRENCY (2026-11-11): the
# scratch dir used to be the FIXED path $PWD/.gate_tmp, rm -rf'd at
# start and by the EXIT trap -- two concurrent gate runs collided on
# it, and the trap deleted unittest.log with it, so a failing gate
# destroyed its own evidence (the LAND-SHEN-20261110 first-run
# failure, Ran 1,859 failures=2 errors=1, lost its log this way).
# Cure: the scratch dir is now per-run unique (mktemp -d under the
# already-ignored .gate_tmp/ parent; the trap removes only that
# per-run dir), and on EVERY run, pass or fail, the full unittest
# log is copied to a durable receipt in state/gate_receipts/ (state/
# is the ignored runtime dir, never committed) plus a one-line JSON
# proof row appended to state/gate_receipts/receipts.jsonl. The
# receipt lives OUTSIDE GATE_TMP and is never removed by the trap.
# Proof: BUGLOG_2026-11-11.md and
# tests/test_gate_receipts_20261111_blockers.py.
set -e
cd "$(dirname "$0")"
GATE_PARENT="$PWD/.gate_tmp"
mkdir -p "$GATE_PARENT"
GATE_TMP="$(mktemp -d "$GATE_PARENT/run.XXXXXX")"
trap 'rm -rf "$GATE_TMP"' EXIT INT TERM
RECEIPTS_DIR="$PWD/state/gate_receipts"
mkdir -p "$RECEIPTS_DIR"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
RECEIPT_LOG="$RECEIPTS_DIR/unittest-$RUN_ID.log"
RECEIPTS_LEDGER="$RECEIPTS_DIR/receipts.jsonl"
GATE_LOG="$GATE_TMP/unittest.log"
gate_start="$(date +%s)"
rc=0
TMPDIR="$GATE_TMP" TEMP="$GATE_TMP" TMP="$GATE_TMP" \
python3 -m unittest discover -s tests -p "test_*_blockers.py" -v \
    > "$GATE_LOG" 2>&1 || rc=$?
gate_end="$(date +%s)"
gate_wall=$((gate_end - gate_start))
# Receipts: written on every run, pass or fail, BEFORE the tail/exit
# below; failures here warn but never mask unittest's exit code.
if ! cp "$GATE_LOG" "$RECEIPT_LOG"; then
    printf 'gate: WARNING: receipt log copy failed: %s\n' "$RECEIPT_LOG" >&2
fi
ran_line="$(grep '^Ran ' "$GATE_LOG" 2>/dev/null | tail -1 || true)"
ran_esc="$(printf '%s' "$ran_line" | sed 's/\\/\\\\/g; s/"/\\"/g')"
tree_hash="$(git rev-parse HEAD 2>/dev/null || printf 'unknown')"
run_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if ! printf '{"run_id":"%s","timestamp_utc":"%s","tree_hash":"%s","wall_seconds":%s,"ran_line":"%s","exit_code":%s,"log":"state/gate_receipts/unittest-%s.log"}\n' \
    "$RUN_ID" "$run_ts" "$tree_hash" "$gate_wall" "$ran_esc" "$rc" "$RUN_ID" \
    >> "$RECEIPTS_LEDGER"; then
    printf 'gate: WARNING: receipt ledger append failed: %s\n' "$RECEIPTS_LEDGER" >&2
fi
tail -5 "$GATE_LOG"
exit "$rc"
