# Aster feature implementation verification

This is the **pre-audit release baseline**. Its file hashes and line citations describe the original implementation. See [the full repair audit](FULL_AUDIT_REPORT.md) and [current code manifest](AUDIT_CODE_MANIFEST.json) for repaired source and fresh validation.

Mapped all **30 canonical requirements and 211 atomic contracts** from Femto/Midna, Cursor and GrokBot. Baseline SHA256 `83b67d0767b98dd7da6d7b288be18ad7507c73486121714e6f1e14effa77af2c`; the original matrix was left unchanged.

Aster remains equity-only, with no installed strategies, seeded trades or profitability claim. Counts refer to overlapping source contracts, not independent capabilities or successful studies.

| Atomic status | Count |
|---|---:|
| implemented | 72 |
| configuration-required | 42 |
| extension | 96 |
| not-applicable-strategies | 1 |

The report cites exact pre-audit implementation/test symbols, line ranges and file hashes. Implemented foundations include independent books, write-ahead intent identity, cumulative partial fills, confirmed cancellation, signed accounting, durable schedules, observation provenance, bounded read-only model tools, local inbox and evidence/rollback records.

## Canonical coverage

| ID | Requirement | Status |
|---|---|---|
| U01 | Desk, account and agent identities | implemented |
| U02 | Independent books and authority | implemented |
| U03 | Unattended execution and host recovery | configuration-required |
| U04 | Child supervision and heartbeats | extension |
| U05 | Session clock and operational cadences | implemented |
| U06 | Durable attempts and success receipts | implemented |
| U07 | Critical-window end-state verification | extension |
| U08 | Single-writer atomic persistence and recovery | extension |
| U09 | Ordered immutable ledger and observer cursors | implemented |
| U10 | External paper broker and account readiness | configuration-required |
| U11 | Market-data providers, freshness and provenance | extension |
| U12 | Paper-fill and transaction-cost provenance | implemented |
| U13 | Intent-before-submit and ambiguous-order recovery | implemented |
| U14 | Cumulative partial fills and cancellation | extension |
| U15 | Reconcile, mismatch controls and adoption | implemented |
| U16 | Existing-order lifecycle and protection | extension |
| U17 | Risk policy versions and reservations | implemented |
| U18 | Entry pause, activation, resume and rollback | extension |
| U19 | Account/P&L baselines and attribution | extension |
| U20 | Performance, risk and position observations | extension |
| U21 | Health/readiness and operator diagnostics | implemented |
| U22 | Readonly public projections and reliable UI polls | implemented |
| U23 | Notification cursors and optional delivery | configuration-required |
| U24 | Structured journals, nightly review and lessons | extension |
| U25 | Research/agent tool execution with context separation | configuration-required |
| U26 | Evidence-backed research revisions and rollback | extension |
| U27 | Queryable evidence and rebuildable analytics | extension |
| U28 | Three-peer inbox and message lifecycle | extension |
| U29 | Backup/channel preservation | extension |
| U30 | Isolated staging/simulation and operator tools | extension |

## Verification limits

Independent isolated backend validation: **194 tests passed**; source hashes matched the captured suite snapshot. Full receipts and hashes are in the JSON. Fixture tests do not prove a live broker/model connection, external publication, host power-loss recovery, completed studies or investment edge. Credentials, host service/backup installation and opt-in notifications remain configuration-dependent.

Full generic protection repair, option/multileg runtime, staged activation, remote peer synchronization/threading, statistical promotion and arbitrary plugin/replay execution remain explicit extensions. Benchmark reports currently fix QQQ and SPY; Alpaca fees and full broker cashflow history remain unobserved. Empty strategy execution is intentional; unsupported generic infrastructure is not disguised as a strategy exclusion.

Named frontend implementation bodies were inspected. Browser/build verification is owned by the root agent and is not silently attributed to this reviewer. See the JSON for exact pre-audit code/test citations, preserved historical source pins and per-contract boundaries.

[Full implementation map](FEATURE_IMPLEMENTATION_VERIFICATION.json)
