# ASTRA SIX-CONSTRUCTIONS PACKAGE: INGESTION AND THE CONSTRUCTION 1 AUDIT

Date: Sun 2026-11-15 (America/New_York). Program home: ~/workspace/research_notes/astra-six-constructions-20261115/. Typed Decisions API spend: $0.00. No desk, book, or trading state was touched.

## SCOPE

Surface: the six-constructions package Astra saved to GitHub, mirrored and audited on this estate; the C1 cell of Six Constructions Run 2. Constraints: source repositories read-only; code read in full before any of it ran; the audit grades the artifact's fidelity (his code, his archived inputs, his numbers), never the strategy's merit; no em dashes in deliverables. Outcome: a cell-by-cell verdict on the claimed delayed-hedge table, observed test and reproduction counts, a cross-repository identity verdict, and a reconciliation of the package's specifications against Run 2's runfiles. Proof: the final artifacts in this program home (STEP1-MIRROR-VERIFY.md, STEP2-CODE-READ.md, STEP3-4-AUDIT.md, STEP5-RECONCILIATION.md) and the reproduced outputs under six_constructions_2026-11-15/runs/historical/. Edges: the parent event list is inherited by the prototype and is consumed as given (finding F1); the estate's library versions differ from the package's pins (finding F4, cured in pass by the pinned venv).

## HEADLINE VERDICT

C1 AUDIT: REPRODUCED. Astra's code, run on Astra's archived inputs through the package's own portable route, produces Astra's claimed table exactly: 18 of 18 claimed cells match at 3 decimals, event counts 44 / 59 / 37 confirmed at both horizons, 27,513 of 27,513 recorded values matched (byte-identical outputs in the pinned environment), and the package's test suite passes 30 of 30 in both environments tested. The C5 supplied-state examples reproduce exactly. The two repository copies of the package are content-identical, 88 of 88 files.

## STEP 1, MIRROR AND VERIFY: GREEN

Source: dwj9ddyvf6-hub/cos2-estate, branch research/six-constructions-20261115, head c2cba0d433823c56cdb3b9680f69c58365a35ab2. All 88 files fetched byte-exact (9,455,986 bytes): the package MANIFEST.json lists 86 payload files, and all 86 match on size and sha256 with 0 mismatches and 0 missing; the 88 total is those 86 plus MANIFEST.json itself plus the sibling readback file. Astra's claim of 88 of 88 verified is confirmed under that accounting. Computed git blob shas matched the tree for 88 of 88.

Data archive: 4 of 4 parts match data_archive/manifest.json; the reassembled market-data.tar.gz (7,386,975 bytes, sha256 3b7c7f70b68cad0ed3cd41e27e3c0178f71230be4943fa080802bb3d24563713) matches the manifest; unpacked 799 files (7,638,507 bytes; binance/ 634 files, perp_history/ 165 files), all 799 internal manifest entries matched.

Cross-repository check: the mirrored copy in dwj9ddyvf6-hub/master-desk at head 3bc102f26abc0bda30da0e547c4c25e626f09514 was compared file by file: 88 compared, 88 identical, 0 divergent, 0 missing on either side. One named path divergence, no content divergence: the master-desk copy lives under research/six-constructions/2026-11-15/, not research/brainstorm/six_constructions_2026-11-15/. The brief's "same subtree paths" phrasing is refuted literally; the content identity holds by relative path.

## STEP 2, CODE READ: GREEN, WITH FINDINGS F1 TO F4

original/two_clocks.py and original/conditional_contracts.py were read in full before anything ran (STEP2-CODE-READ.md). Neither file contains network, credential, or order behavior. The prototype's mechanics match the report's description: lagged 180-bar beta (rolling covariance over variance of close/open returns, shifted one bar); the highlighted policy adds the beta-sized BTC perpetual hedge at the next open after two consecutive completed positive BTC bars, sized off the entry price and never rebalanced; endpoints at 6 and 18 bars with terminal prices at the last held bar's close; 10bp per one-way turnover on both legs including hedge entry and exit; archived 8-hour funding with the less favorable before/after cash-flow convention at quantity changes, and strict exclusion of any event whose funding clock is incomplete.

F1 (auditability scope, disclosed in the report itself): the residual-score event selection is not implemented in two_clocks.py; the code consumes the preserved CL-03226 parent event list and applies only its negative-BTC signal-bar filter. The audit therefore verifies policy P and L conditional on the preserved list. The packaged route consumes inputs/parent_events.json as given: 288 events in, 145 skipped by the sign filter, 143 attempted, 3 events excluded for incomplete market or funding clocks (6 event/horizon rows, exactly the exclusions the report describes), 140 events included.
F2 (forward protocol difference, not an artifact defect): our C1-RUNFILE.md exits forward events at the endpoint bar open; the prototype exits at the last held bar's close. Recorded so the two are never conflated.
F3 (consistency confirmed): the code's own design record carries the same disclosures as the report (12 policies, 4 inverse policies added after viewing initial results, inherited events, no untouched holdout). No undisclosed deviation was found.
F4 (environment): this estate runs numpy 1.26.4 and pandas 2.1.4; the package pins numpy 2.5.4 and pandas 3.1.1. This gap caused the one deviation class observed in Step 3 and was cured by rerunning in a pinned venv.

## STEP 3, ASTRA'S OWN VERIFICATION, OUR OBSERVED COUNTS

Calculation identity: run_historical.py differs from original/two_clocks.py in 5 hunks, all path or write-location only; zero calculation-relevant differences. The rewired event path is content-identical to the original run's input: the sha256 of inputs/parent_events.json equals the source_events_sha256 recorded in original/results.json.

Tests: 30 run, 30 passed, 0 failed, 0 skipped, in BOTH the installed environment and the pinned venv (tests/test_reference.py 24, tests/test_historical_kernel.py 6). The reference.py synthetic examples match examples/expected.json exactly, and all six per-construction examples match their expected files exactly through the directed runner. Astra's claim of 30 tests passed is confirmed. One component cannot run in the portable layout: original/test_two_clocks.py fails on import because the original file hardcodes the origin machine's source path. Its 6 tests are identical to test_historical_kernel.py except the import line (verified by diff), and those pass; the failure is a property of the archival original, already superseded by the portable route, and is recorded here rather than silently skipped.

Historical reproduction: 27,513 leaf values compared (results.json 2,593; event_paths.json 24,920). Matched under the package's 1e-12 criterion: 27,513 of 27,513 in both environments; 0 mismatches beyond tolerance in either. Matched exactly: 11,360 in the installed environment; 27,513 of 27,513 in the pinned venv, where both reproduced files are byte-identical to the archived originals and their sha256 values equal the reproduced hashes Astra recorded (01aaee72... and b9f6ddca...). Astra's claim of 27,513 recorded values matched is confirmed, and at pinned versions the match is exact, not merely within tolerance. The one installed-environment deviation, named and sized: 31 leaves, all break_even_round_trip_bps in results.json, drifted 1.002e-12 to 2.842e-12 absolute (relative at most 1.558e-13) beyond strict absolute 1e-12 while still passing the package criterion; the pinned rerun eliminated it entirely, confirming library versions as the cause.

One mirror artifact, not a package defect: tools/verify_bundle.py reports 800 unlisted files in this mirror because Step 1's unpacked archive tree and the combined tarball are not payload-manifest entries. All 86 payload files are present and hash-correct, and data integrity is separately proven by the restore tooling's hash check over all 799 restored files.

## STEP 4, THE C1 AUDIT PROPER: REPRODUCED

Period mapping (from CUTS in the packaged code): development_2019_2022 is the claimed 2020 to 2022 partition (included events actually span 2020-01-16 to 2022-12-17, so the label is accurate); audit_2023_2024 is 2023 to 2024; replay_2025_onward is 2025 to Oct 2026. Event counts observed: 44 / 59 / 37 at the 72-hour horizon and the same 44 / 59 / 37 at 24 hours, matching the claim.

72-hour means, percent of initial asset notional (claimed = archived = reproduced, all cells):

| Partition | Events | Immediate | Delayed | No hedge | Half hedge |
|---|---|---|---|---|---|
| 2020 to 2022 | 44 | 2.032 | 2.169 | 3.845 | 2.938 |
| 2023 to 2024 | 59 | 1.266 | 2.362 | 2.153 | 1.710 |
| 2025 to Oct 2026 | 37 | 1.888 | 3.539 | 4.442 | 3.165 |

24-hour means (claimed = archived = reproduced): delayed 3.587 / 1.922 / 2.595; immediate 3.169 / 0.735 / 0.977, same partitions in the same order. The 24-hour rows reuse the parent event list whose spacing was chosen for 72-hour holds, exactly as the report discloses.

Deviation cells: NONE. The half-hedge column is a derivation, not a simulation, and is verified as such: static_fraction_comparison.json's 0.5-fraction rows equal unhedged plus 0.5 times (fixed minus unhedged) from results.json for every row (maximum discrepancy 6.94e-18), and its dynamic-minus-static column equals delayed minus static throughout, consistent with the report's linearity note.

C5 examples: PASS on all checks. The supplied-state enumeration reproduces: unknown history gives a minimum terminal PnL of -0.95 (negative, the zero-payout state retained); the verified higher-target-not-hit case gives +0.05 on the 0.40 and 0.55 supplied prices (cost 0.95, floor 1.00); the (0,1) state is present in the first case and absent in the second; the file the code writes is byte-identical to the archived copy, and the directed C5 example matches its expected file exactly.

What this verdict does and does not say: the artifact is faithful. His code on his data produces his numbers, his tests pass, and his recorded hashes are honest. The claimed result's own standing is restated unchanged from the report and from our runfile: exploratory and adaptive (12 policies explored, 4 inverse policies added after viewing the first results, events inherited from an earlier broad search, survivor universe), every incremental bootstrap interval includes zero, the delayed hedge's fifth-percentile outcomes are worse than the immediate hedge's, and no partition is an untouched holdout. Nothing in this audit promotes the strategy. The frozen fresh-data protocol in C1-RUNFILE.md remains the forward test.

## STEP 5, RECONCILIATION WITH RUN 2: GREEN

Full text in STEP5-RECONCILIATION.md. Summary: the package's specifications and Run 2's runfiles agree on the liability identity and executable-credit convention (C2/C6), the five same-capital arms and the repair falsifier (C3), the implementation-shortfall identity and all-intents grading (C4), and the state-elimination standard with prices read last (C5). Twelve proposed amendments are recorded with their effects, none applied silently: the package's unset-parameter list becomes the checklist for the C2/C6 development lock addendum (A1); portfolio reservation pricing and interim loss-path reporting are added as secondary reads (A2, A4); quote size is carried as a named coverage limitation (A3); the C3 parameter mapping and membership limitation are recorded at package strength (A5 to A7); the C4 capture build adopts the package's order-state vocabulary and terminal-wealth secondary read (A8, A9), with the estate's fills-without-quotes inventory standing as the binding circumstance (A10); the C5 standard gains the lower-already-hit floor route and void/revision state expansion before any second pair audit (A11), and the fuller reference.py contract machinery is rowed as untested against a real pair (A12).

C1 cell status, updated: Route 1 (audit) unblocked by this landing on Sun 2026-11-15 and closed with the REPRODUCED verdict. Route 2 (reconstruction from the specification) is retired as moot, as registered for this audit. The data rows C1-DATA-01 to C1-DATA-05 remain open in their forward-protocol role only. A dated addendum recording this status has been appended to C1-RUNFILE.md; its registered text is untouched.

## OPEN ROWS

1. C1 fresh-data protocol: frozen and standing; its per-asset forward start still waits on the BTC 4h, BTC perpetual, and BTC funding rows (owner: desk feed work; no date forced by this audit).
2. C2/C6 development lock addendum: due before the first read on Tue 2026-11-17, now carrying amendment A1's checklist (owner: C2/C6 cell).
3. C5 reference machinery against a real pair: open, due when a second pair audit is registered (owner: C5 cell).
4. The six constructions' remaining cells (C3 replay, C4 prospective capture) stand exactly as Run 2 registered them; this audit changes none of their verdicts.

## SAVES

This report and the full mirror home (code, reports, manifests, reproduced outputs, and the data archive parts as fetched; the unpacked tree is reproducible from those parts by the package's own restore tooling, and the venv is reproducible from requirements-reproduction.txt, so neither is duplicated into the save) are light-saved to dwj9ddyvf6-hub/Midna under light-save/astra-six-constructions-20261115/ as a packet with a per-file manifest, read back and hash-verified. Receipts are recorded in SAVE-RECEIPTS.md in this program home and in the dead-drop post carrying marker midna-inbox:2026-11-15-astra-six-audit.

STATUS: GREEN. Evidence pointers: STEP1-MIRROR-VERIFY.md (mirror, archive, cross-repo counts), STEP2-CODE-READ.md (code findings F1 to F4), STEP3-4-AUDIT.md (observed counts and the cell table), STEP5-RECONCILIATION.md (agreements and amendments A1 to A12), six_constructions_2026-11-15/runs/historical/ (reproduced outputs).
