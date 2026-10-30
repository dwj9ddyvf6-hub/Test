> Historical audit record. The public copy generalizes private connected-tool provenance in the source registry; its current checksums and test results are in [PUBLIC_VALIDATION.md](../PUBLIC_VALIDATION.md). Engine code is unchanged.

# v0.4 operational extension audit

Date: 2026-10-30 UTC. Final candidate: `implementation_v041/psychology-engine-research` (v0.4.1), following findings on v0.4.0.

## Result

**Final v0.4.1 fix verification passes.** All **70 shipped tests**, the same **five independent v0.3 regressions**, and all **six unchanged independent operational tests** pass. All package checksums match. Code review confirms the three operational defects are fixed: latest eligible revision selection before health validity checks, capture-clock consistency checks before ingestion, and exclusive backup creation with mode 0600. No implementation file was edited, endpoint fetched, service activated, policy altered, or credential read during this audit.

## Resolved defects from v0.4.0

The reproductions below describe v0.4.0, not the corrected final v0.4.1. Each corresponding unchanged independent regression now passes.

### O01 — Medium — Health reports healthy after the latest revision makes evidence unknown

`psychology_engine/operations.py:27–33`, especially line 29, selects any historical non-null available observation without first selecting each item's latest eligible revision. A valid row followed by a newer null-valued revision leaves the snapshot with no evidence, but a recent successful run makes health report `healthy`, `fresh_observation_present=true`, exit 0. An unavailable latest revision has the analogous risk.

Fix: apply the same event/publication/first-seen/availability gates and revision ordering as snapshot assembly; select latest revisions first, then evaluate value/access/freshness. Do not resurrect superseded valid data for health.

### O02 — Medium — Receipt importer accepts data whose completion occurs after its claimed capture

`psychology_engine/receipts.py:23–36` parses with the capture timestamp but validates observations only against the later local import timestamp. A completed October 27 Wikimedia daily count has event time October 28 00:00, yet a receipt claiming capture at October 27 12:00 imports successfully on October 29.

Fix: reject source observations/publications that could not exist at the claimed capture, before mutating the ledger. Maintain the separate later local first-seen/extraction availability. This is a provenance-consistency defect, not a claim of early engine availability: local first-seen gating already works. The actual supplied 498/578 sample has consistent clocks and is not affected.

### O03 — Medium — Manual backups inherit a permissive umask

`psychology_engine/operations.py:44–49` exclusively creates the destination through `Path.open('xb')`, resulting in mode 0644 under umask 022. Runtime databases may contain licensed or private imported evidence and should not become group/world-readable through backup. The systemd collector's UMask=0077 does not apply to a manual backup command.

Fix: exclusive descriptor creation with mode 0600 (e.g. `os.open` with O_CREAT|O_EXCL|O_WRONLY), retaining no-overwrite and error-cleanup behavior. Do not rely on the caller's umask.

## New independent operational tests

`test_operations_independent.py`, run from the candidate checkout:

```bash
PYTHONPATH=. python -m unittest discover \
  -s ../audit \
  -p test_operations_independent.py -v
```

| Check | v0.4 result → v0.4.1 result |
|---|---|
| Health respects latest null revision | FAIL (O01) → PASS |
| Capture cannot precede daily completion | FAIL (O02) → PASS |
| Backup stays private under umask 022 | FAIL (O03) → PASS |
| Committed WAL-backed evidence/acquisitions survive backup/reopen, destination overwrite refused | PASS |
| Receipt import makes no HTTP call and cannot backdate local availability | PASS |
| Scheduled one-shot requires permission, collector never called on rejection | PASS |

Historical logs: `v04-shipped-tests.txt`, `v04-independent-tests.txt`, `v04-operations-independent.txt`, `v04-checksums.txt`.

Final logs: `v041-shipped-tests.txt`, `v041-independent-tests.txt`, `v041-operations-independent.txt`, `v041-checksums.txt`.

## Verified boundaries

- Read changed/new executable modules, tests, deployment files, documentation, example receipts and observed outputs; compared unchanged core behavior with v0.3.1.
- New health uses a read-only SQLite connection and does not create a missing database. Integrity checking and supported schema checks are present. O01 concerns semantic selection, not connection mutability.
- Backup uses SQLite's online backup API, preserves committed WAL data, checks integrity, refuses an existing destination, and cleans its own newly created destination on failure. O03 concerns filesystem confidentiality.
- Exact-host network policy interpretation is conservative for the actual documented host-only policy. Managed policy takes precedence over a standalone policy path. Unknown/missing policy, HTTP, non-default port and unsupported rule shapes are rejected. No infrastructure permission was changed and no denied fetch was retried through another route.
- Scheduled/repeated collection gates on explicit versioned operator authorization. Templates are inactive `.example` files, have no Install section, use a dedicated account, serialize collectors through `flock`, and leave all usage authorizations false. Template syntax is not deployment or a production SLA.
- Both research registries match current masters byte-for-byte: 16-card pattern schema 1.0.1, SHA-256 `2a3005066bbb41dc9f21dfe3d618180fafcab8beceabad80f56cc9a75ddd60c2`; 50-source registry SHA-256 `7deb8af84c748a79ad687676f91509c0f61e844c2fec1dba2c0c9dd97bb9e305`.
- The supplied observed receipt checksum matches its payload. Stored counts are 498/578 for completed UTC days, with engine first-seen/available-at at actual import, not earlier upstream capture. The sample's detectors and forecast abstain because two observations are insufficient. This verifies local receipt parsing, not outbound collection or predictive value.

The exact corrected v0.4.1 candidate passed all requested tests and fix verification at 2026-10-30 22:11 UTC. Both research registry files remain byte-identical to their current masters. **No remaining blocker in the requested bounded audit scope; suitable for publication as the explicitly limited research package.** This is not approval to activate a service, alter network policy, claim market predictive validity, or integrate trading execution. No audit scope expansion or external requests were made.
