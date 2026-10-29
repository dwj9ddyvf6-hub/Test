# Corpus audit and snapshot identity

**Audit snapshot:** Silicon `origin/main` at `aad9d2148752a6862ce7a6c44685311aa7310947` (2026-10-28). The forecast package is being added on top of this snapshot.

## Silicon inventory and denominator

| Scope | Tracked paths | Interpretation |
|---|---:|---|
| Entire Silicon repository | 20,324 | Git tree count at the snapshot above. |
| `research/rea-teardowns/` (hyphenated legacy/source tree) | 6,663 | Includes indexes, synthesis, vendor/source artifacts, vault, and linked research. |
| `research/rea_teardowns/` (underscore active registry) | 10,421 | Includes the active index, scope ledgers, artifacts, and target reports. |
| Two REA trees combined | 17,084 | 84.1% of this repository snapshot. |
| Active vendor/target reports in registry | 86 | Target-family denominator recorded by the current index. |
| Requested analysis passes | 100 | 95 full-scope complete, five bounded complete in the latest reconciled scope ledger; this describes research coverage, not independent validation. |
| Large vault source streams | 39 | Current source-structure index reports 37 parsed streams and two partial trailing fragments; combined original stream size is about 4.19 GB. |

The older user-supplied “6,315 files” count does not match this newer Git snapshot. It likely reflects a different date/scope; this audit uses Git tree counts and preserves the distinct directory names rather than silently merging their denominators. The second tree has the index/target registry; the first contains earlier evidence and newer synthesis. The 39 large raw streams were not re-read byte-by-byte for this feature. Their hashes, part layout, and parser state are recorded in the existing corpus manifests.

An explicit term search over Markdown and CSV files in both REA trees found 327 files containing `reverse.engineer`, `reverse engineering`, `teardown`, or `REA`. Core cross-vendor indexes and all 86 active report headings were used to trace this implementation. This does not claim every byte in raw JSON, binary app capture, every vendor source archive, or each 4.19 GB vault stream was semantically re-reviewed in this pass. Use the existing vault and artifact manifests to select a specific source for deeper follow-up.

## Femto-lean branch refs verified live

Each listed ref was live on GitHub at the time of this audit. The desk-state branch was not read as trading state; branch inventories and curated research summaries were used, and secret-bearing state was excluded.

| Branch | Commit | Use in this package |
|---|---|---|
| `master-desk` | `53096b3a3151b1705e5b437411597138d91a4495` | Read the applicable branch instructions and curated research inventory; no desk code/sleeve/order state changed. |
| `desk-state` | `ede793aef6f26b6717ea2a6f889eca68b2a06f82` | Live tip advanced two commits; compare metadata shows state/cache/ledger/sleeve snapshots only. State payloads, credentials, and secret-bearing records were not imported. |
| `research/2026-10-20-eyes` | `bf8dce8e6b2333400277986765025525ea910c4b` | Reviewed findings and validation summaries for price/visual, matched-control, and avoid/risk evidence. |
| `research/gestalt-trading-engine-2026-10-26` | `a0bc4720a3a68cdc925f725019317daa8cad19e2` | Reviewed curated forecast/strategy findings and their out-of-sample/cost limitations. |
| `research-archive` | `60f5e01a20d2d6617b34fdc3ec62b0ebc20e31de` | Used inventories/gap notes; raw session transcripts were excluded. |
| `research-data` | `58244bf2e020b1ed4b269b0c4f30638be456deb2` | Used curated Edge/validation audits and data-source cross-check summaries. |

The remote tree inventories at the verified refs were: `master-desk` 2,434 paths (295 under `docs/research/`); `desk-state` 1,244 paths (771 under `state/`); `research/2026-10-20-eyes` 43,894 paths; `research/gestalt-trading-engine-2026-10-26` 764 paths; `research-archive` 2,375 paths; and `research-data` 5,892 paths. The research branches contain many CSV/JSON artifacts. Findings here are based on branch reports, inventories, and verification summaries described above; it would be inaccurate to imply that every row of every experimental artifact was manually inspected in this feature pass. Most promising retrospective rows remain candidates until independent data and forward paper evidence pass the stated gates.

## Separate TheStrat public teardown

The separate private repo `dwj9ddyvf6-hub/thestrat-ai-public-teardown` was verified at main commit `8fb531d03c03879b0e9c297b80a216f5bfdadf02`; its public research tag was `3e0cb192cda3a5e88d6bea48edaeda4b65959727`. The 439-entry public archive bundle is 86,583,336 bytes with SHA-256 `d44aac4a858fcae234f7dccbaf8689652650252eb4159e38739d2ff6f49aa866`. The locally extracted public-surface report includes the eight public PDFs (46.6 MB / 173 pages), 136 sitemap routes, 849 WordPress route definitions, and 16 published MCP/OpenAPI tools. Public pages supply candidate rule definitions, but no complete fills, historical predictor series, backtest, or demonstrated alpha. Passworded and sign-in-only surfaces remain out of scope.

The public gap rules include continuation and failed-gap reversal, with unresolved daily-open versus kicking-bar-open triggers. Higher-timeframe setup creation and lower-timeframe confirmation are suitable event-study definitions only after they are frozen without outcome inspection. See `alpha-hypotheses.md`, `public-pdf-rule-extract.md`, and `public-deeper-pass.md` in the captured teardown archive described in `TRACEABILITY.md`.

## Scope guard

`research/morgue-engine/` was inspected read-only and was not included in the sparse feature checkout. No file under that fenced lane, `apps/silicon-market-terminal/`, Ausar Desk, Femto's master desk, or Femto state was edited. The new package is intentionally not wired into any of them.

## Second-pass update — 2026-10-29

The second pass verified all 86 target-report hashes against this snapshot and revisited data cadence, chronology and validation evidence. It also found index disagreements that were not visible in the first feature audit: the current tree has 20,324 paths while `CORPUS_FILE_INDEX.csv` has 19,735 rows (628 tree paths absent and 39 manifest-only local vault references); the generated family locator CSV has 557 rows all marked `NOT_REVIEWED_BY_GENERATOR`; and the checked-in unified CSV has 23 rows although its three source registers and builder define 31 (9 candidate + 14 scoped + 8 OptionStrat). The active-family ledger's 80-complete/6-in-progress counts also differ from the later 2026-10-28 reconciliation's 81 complete/5 bounded-complete. These are preserved as source-state discrepancies, not silently repaired in the upstream research trees.

The complete evidence and code changes are documented in [SECOND_PASS_AUDIT.md](SECOND_PASS_AUDIT.md). This package adds measurement/publication/ingestion-clock visibility, declared source-family concentration diagnostics, and cadence-aware ages for slow data families. It still has no calibrated model-error gate, licensed point-in-time outcome panel, production data connector, or trade execution path.

## Third-pass update — 2026-10-29

The third pass returned to failure modes shared across the seven original repositories, Vibe-Trading, Edge, Silicon's REA, Femto research, the supplied Ausar sleeves, Saty, and the public TheStrat extraction. The central cross-source correction is that multi-agent agreement is not independent evidence when agents or vendors reuse the same feed. See [THIRD_PASS_AUDIT.md](THIRD_PASS_AUDIT.md) for the source-by-source design transfer and the full FE01–FE30 mechanism map.

The 30 hypotheses now have typed Edge cards with local source-reference validation. `forecast_collision_map` identifies comparable forecast records that share exact hashes, source IDs, or declared groups; it flags duplicate engine records and abstains from a descriptive median where duplicates exist. `estimate_source_refresh` uses only matured and rights-approved history to describe source refresh cadence by age-to-horizon band. Both diagnostics are non-decision outputs and preserve the existing point-in-time feature gate. The third pass does not modify the upstream REA indexes, Femto branches, desk state, or trading surfaces.

## Fourth-pass update — 2026-10-29

The live desk-state ref advanced to ede793aef6f26b6717ea2a6f889eca68b2a06f82; compare metadata shows changes in state/cache/ledger and sleeve snapshot files, with no research-document additions. Silicon main and the earlier feature commit were unchanged at the live ref check. The fourth-pass implementation binds source, transformation, and model identity separately, adds caller-bounded score boundary analysis for every FE01–FE30, and distinguishes shared transformation code from shared raw-source collision edges. See FOURTH_PASS_AUDIT.md for the source-by-source findings and empirical next steps.

## Fifth-pass update — 2026-10-29

The evaluation-ledger audit found that abstained attempts could not receive final target labels, preventing measurement of selection bias in forecast coverage. The ledger now supports a separate `abstention_audit` outcome role, enforces one final outcome per forecast ID, verifies chain integrity before cutoff joins, and reports outcomes for answered vs abstained attempts without mixing them into forecast-skill scores. See FIFTH_PASS_AUDIT.md and the selective-prediction sources in SOURCES.md.

## Sixth-pass update — 2026-10-29

The fifth pass closed the abstention-outcome gap, but it still left the experimental unit ambiguous: repeated forecasts for the same symbol can label overlapping pieces of the same future path. This pass adds `horizon-overlap`, which reconstructs actual target intervals from forecast cutoffs and final outcome observation times, measures within-symbol interval reuse, and flags exact-cutoff cross-symbol cohorts. It reports a maximum non-overlapping interval set as geometry for experiment design, not as a statistically effective sample size. Diebold–Mariano and Hansen–Hodrick provide the classical inference motivation; conditional loss inference and empirical dependence remain future work. See [SIXTH_PASS_AUDIT.md](SIXTH_PASS_AUDIT.md).

## Seventh-pass update — 2026-10-29

The full target-card re-read found that a “horizon-complete” attestation alone did not prove the label reached the forecast's intended endpoint. The catalog also used several broad/multi-outcome definitions, including one scenario-only sensitivity that was not an unconditional return forecast. The forecast record now carries a target-contract fingerprint plus an optional pre-frozen allowed window ID/start/end and label-transform hash. Current outcome writes must match those values exactly, and audits partition distinct target/window/transform definitions. Old events remain visible as legacy-unbound. FE15 is scenario-only; FE25's target is now a future issuer residual return conditional on executed pace, not a claimed causal buyback contribution. Details and verification scope are in [SEVENTH_PASS_AUDIT.md](SEVENTH_PASS_AUDIT.md).

## Eighth-pass update — 2026-10-29

The label/window/code contract still allowed one target name and transform to hide different instance conventions (series, adjusted/raw basis, calendar, benchmark, data vintage, corporate actions). A canonical six-field label context is now fingerprinted on each bound forecast, repeated by its outcome, and validated in ledger reads. Provenance and pooling diagnostics partition on that context. CRSP return methodology, ALFRED vintage retrieval, and Nasdaq session calendars motivated the fields; they do not prescribe the local hash protocol. See [EIGHTH_PASS_AUDIT.md](EIGHTH_PASS_AUDIT.md).
