# STEPS 3 AND 4: ASTRA SIX-CONSTRUCTIONS VERIFICATION RUN AND C1 AUDIT

Date: 2026-11-15. Auditor: Midna subagent, Steps 3 and 4 only.
Working tree: six_constructions_2026-11-15/ inside this mirror home, byte-exact mirror of dwj9ddyvf6-hub/cos2-estate branch research/six-constructions-20261115 at c2cba0d43382 (Step 1 verified 88 of 88 files).
Typed spend: $0.00. All runs sequential, one process at a time.
No file under original/ was modified. Proof: sha256 of original/conditional_contracts.py and original/conditional_payoff_examples.json rechecked OK after the C5 run, and the final reproduced outputs were compared against original/ read-only throughout.

## AUDIT VERDICT: REPRODUCED

Every claimed C1 cell matches the archived and the reproduced values within rounding at 3 decimals (18 of 18 cells). In the pinned environment the portable replay regenerates original/results.json and original/event_paths.json byte for byte. Named deviations and findings are listed in the Findings section; none touches a claimed table cell.

## Environments used

| Environment | Python | numpy | pandas | requests | Used for |
|---|---|---|---|---|---|
| Installed (system) | 3.12.3 | 1.26.4 | 2.1.4 | n/a | First pass: all tests, examples, restore, historical replay, comparison |
| Pinned venv at ~/workspace/research_notes/astra-six-constructions-20261115/venv/ | 3.12.3 | 2.5.4 | 3.1.1 | 2.34.2 | Second pass after the installed pass showed last-bit float noise: tests and historical replay rerun |
| Astra research environment (his record, verification/local_verification.json) | 3.12.14 | 2.5.4 | 3.1.1 | 2.34.2 | Reference only, not run here |

The package pins Python 3.12.14; this box has Python 3.12.3 in both environments. The venv matches the pinned library versions exactly. The final numbers reported for reproduction come from the pinned venv, where output is byte-identical to the archived originals. The installed environment produced the same numbers at every reported precision; its only difference is floating point noise at or below 2.85e-12 absolute, detailed in Step 3C.

## STEP 3A: Calculation identity, diff of run_historical.py against original/two_clocks.py

Full unified diff: 5 hunks, 134 lines in the original, 136 lines in the portable file. Every difference classified:

| # | Difference | Classification |
|---|---|---|
| 1 | Module docstring second line rewritten ("No writes into source repositories..." becomes "Portable path adapter. Writes only runs/historical inside this standalone bundle...") | Path/write-location only (documentation) |
| 2 | SOURCE changed from the hardcoded origin path /workspace/edge-audit/repos/master-desk to ROOT/vendor, with ROOT defined as the bundle directory; sys.path insert adjusted to match | Path only. Note: the imported code now comes from vendor/ copies rather than the origin tree; the diff itself cannot prove vendor equivalence, but the byte-identical reproduction in Step 3C is the behavioral proof that the vendored modules compute identically on this corpus |
| 3 | run() output directory changed from the script's own directory to ROOT/runs/historical, with a mkdir added | Write-location only |
| 4 | design dict field source_root changed from str(SOURCE) to the literal string "vendor (bundled source snapshot)" | Descriptive string only. It lands in runs/historical/design.json, which is not one of the two compared outputs (results.json, event_paths.json) |
| 5 | Data paths rewired: binance archives from ROOT/data/binance, perp data from ROOT/data/perp_history, event list from ROOT/inputs/parent_events.json instead of the origin CL-03226-detail.json path | Path only, with content identity proven: sha256 of inputs/parent_events.json is 8f556419fe1baa8766e25e51fc0a855c2c974bb928dfbc15de920d8cef172599, exactly equal to the source_events_sha256 recorded inside original/results.json |

No calculation-relevant difference found. POLICIES, hedge_fractions, hedge_pnl, the event loop, beta computation, exclusion logic, bootstrap summarization calls, and both output writers are byte-identical between the two files. The build guide claim ("changes paths from the frozen prototype and leaves calculations intact") is verified for the two files diffed.

## STEP 3B: Tests

Astra claim: 30 tests passed (verification/full_suite.log and local_verification.json).

Our counts, installed environment:

| Component | Run | Passed | Failed | Skipped |
|---|---|---|---|---|
| Full suite, python -m unittest discover -s tests -v | 30 | 30 | 0 | 0 |
| tests/test_reference.py alone | 24 | 24 | 0 | 0 |
| tests/test_historical_kernel.py alone | 6 | 6 | 0 | 0 |
| reference.py as main (synthetic C1 to C6 dump) | exit 0 | output equals examples/expected.json exactly (parsed JSON equality) | n/a | n/a |
| run_request.py against examples/C1.json to C6.json, each compared to examples/Cn.expected.json | 6 | 6 exact JSON matches | 0 | 0 |
| original/test_two_clocks.py in the portable layout | 0 run | n/a | 1 import error | n/a |

Our counts, pinned venv: full suite rerun, 30 run, 30 passed, 0 failed.

original/test_two_clocks.py cannot run as shipped on this estate, for a recorded reason: it imports two_clocks, whose module level code inserts the hardcoded origin path /workspace/edge-audit/repos/master-desk/tools/unlock into sys.path and imports chaos_lab, which does not exist at that path here. Observed error verbatim in summary: ModuleNotFoundError: No module named 'chaos_lab' (raised on import of two_clocks in a scratch copy under /tmp). This is the known hardcoded-path limitation the portable route exists to bypass, not a test failure. The file's six tests are identical to tests/test_historical_kernel.py except the single import line (from two_clocks import versus from run_historical import), verified by direct diff, and those six tests pass against run_historical.py. No file under original/ was executed in place or modified.

## STEP 3C: Historical reproduction

Data restore: ran tools/restore_data.py as directed. It reassembled the archive from data_archive parts, hash checked every file, and wrote data/ inside the bundle. Output: restored_and_hash_checked 799. The Step 1 unpacked copy under data_archive/unpacked/ was not used by the tool and was not needed; no adaptation was required.

Replay: ran run_historical.py in both environments. Console output identical between environments and identical to Astra's verification/historical_replay.log at printed precision.

Comparison: ran tools/verify_reproduction.py (status MATCH in both environments) plus an independent leaf-by-leaf comparator written for this audit, counting exact equality, strict absolute tolerance, and the package criterion (math.isclose with abs_tol 1e-12 and rel_tol 1e-12, which is what verify_reproduction.py asserts).

| Measure | Installed env | Pinned venv |
|---|---|---|
| Leaf values compared (results.json 2,593 plus event_paths.json 24,920) | 27,513 | 27,513 |
| Matched under the package criterion (abs and rel 1e-12) | 27,513 | 27,513 |
| Mismatched beyond the package criterion | 0 | 0 |
| Matched within strict absolute 1e-12 | 27,482 | 27,513 |
| Matched exactly | 11,360 | 27,513 |
| results.json sha256 | b4860c5138990fb3d6493264845f416ccacc143dcd100bb357452415701dda6b | 01aaee72bac0beada9f94d546be2ec69b60b36cba16b54aaa73b444a1a75dd27 |
| event_paths.json sha256 | 42507c4b84e647aaa8247484c22740d1871c14deeca1d771460da5c159df3a27 | b9f6ddca2d1f191bbcdc5c1bcd02aa328606fdda17279493e569a7aa16c6dcde |

In the pinned venv both reproduced files are byte-identical to the archived originals (cmp clean) and their hashes equal Astra's recorded reproduced_output_sha256 values in verification/local_verification.json exactly. Astra's claim of 27,513 recorded values matched is confirmed, and strengthened: at pinned versions the match is exact, not merely within tolerance.

Installed environment deviations, named and sized: 31 leaf values in results.json exceeded strict absolute 1e-12 while passing the package relative criterion. All 31 are break_even_round_trip_bps fields (large magnitude derived values, roughly 7.5 to 490 in absolute value). Largest: results.json/rows/19/periods/audit_2023_2024/net/break_even_round_trip_bps, archived -114.87265487126614, installed -114.87265487126898, absolute difference 2.842e-12, relative 2.474e-14. The remaining 30 range from 1.002e-12 to 2.728e-12 absolute, relative at most 1.558e-13. In event_paths.json all 24,920 leaves were within strict absolute 1e-12 (maximum difference 7.472e-14, at beta fields). Cause: library version differences (numpy 1.26.4 and pandas 2.1.4 versus pinned 2.5.4 and 3.1.1) changing floating point summation order. The deviation vanished completely in the pinned venv, which confirms the cause. No claimed table value is affected: every table mean agreed to all printed digits in both environments.

Excluded rows: the reproduced results.json lists 6 excluded event/horizon rows, identical to the archived original: 3 distinct events times 2 horizons, each with reason "incomplete market or funding clock": ADAUSDT at t 1576526400 (h 6 and h 18), ETHUSDT at t 1576526400 (h 6 and h 18), XRPUSDT at t 1574654400 (h 6 and h 18).

Event list provenance: the packaged route consumes inputs/parent_events.json as given. It does not regenerate the parent event list. Observed flow: 288 events in the file; 145 skipped by the code's own filter (BTC signal bar return not negative, the continue before the horizon loop); 143 attempted; 3 excluded for incomplete market or funding clock; 140 included, giving 280 event_paths rows (140 per horizon). This confirms Step 2 finding F1: the audit verifies policy P&L conditional on the preserved event list; the upstream residual-score selector that produced the list is not in this package's executable route.

## STEP 4: C1 audit proper, cell by cell

Period mapping, from vendor/edge_attribution.py CUTS (epoch seconds, UTC). A sample counts when lo is at or below the event time and the event end (t plus h bars of 4 hours) is at or below hi.

| Claimed partition | Code CUTS name | Window (UTC) | Observed event rows per horizon |
|---|---|---|---|
| 2020-2022, 44 events | development_2019_2022 | lo 0 (1970-01-01) to hi 1672531200 (2023-01-01) | 44 at h 6 and 44 at h 18 |
| 2023-2024, 59 events | audit_2023_2024 | 1672531200 (2023-01-01) to 1735689600 (2025-01-01) | 59 at h 6 and 59 at h 18 |
| 2025 to Oct 2026, 37 events | replay_2025_onward | 1735689600 (2025-01-01) to 1793491200 (2026-11-01) | 37 at h 6 and 37 at h 18 |

Naming note: the code name says 2019_2022, but the included event rows in that partition actually span 2020-01-16 to 2022-12-17 (observed from event_paths.json), so the report's 2020-2022 label is accurate for the included sample. Counts are event rows (timestamp, symbol pairs); distinct timestamps per partition are 31, 27, and 26 because symbols share timestamps. Event counts observed in reproduced results equal the archived counts in every cell (n columns below are identical in both files).

Values are means in percent of initial asset notional, computed as net.mean_gross times 100 from results.json. Archived and reproduced agree to all six decimals shown in every cell (they are byte-identical files in the pinned venv). Verdict per cell: MATCH means the archived value rounded to 3 decimals equals the claimed value.

### 72-hour horizon (h 18)

| Partition | Policy | Claimed | Archived | Reproduced | n | Verdict |
|---|---|---|---|---|---|---|
| 2020-2022 | immediate (fixed_beta) | 2.032 | 2.031913 | 2.031913 | 44 | MATCH |
| 2020-2022 | delayed (add_two_market_up) | 2.169 | 2.168903 | 2.168903 | 44 | MATCH |
| 2020-2022 | none (unhedged) | 3.845 | 3.844681 | 3.844681 | 44 | MATCH |
| 2020-2022 | half hedge (static fraction 0.5) | 2.938 | 2.938297 | 2.938297 (static file, see note) | 44 | MATCH |
| 2023-2024 | immediate (fixed_beta) | 1.266 | 1.266257 | 1.266257 | 59 | MATCH |
| 2023-2024 | delayed (add_two_market_up) | 2.362 | 2.362037 | 2.362037 | 59 | MATCH |
| 2023-2024 | none (unhedged) | 2.153 | 2.153372 | 2.153372 | 59 | MATCH |
| 2023-2024 | half hedge (static fraction 0.5) | 1.710 | 1.709814 | 1.709814 (static file, see note) | 59 | MATCH |
| 2025 to Oct 2026 | immediate (fixed_beta) | 1.888 | 1.888380 | 1.888380 | 37 | MATCH |
| 2025 to Oct 2026 | delayed (add_two_market_up) | 3.539 | 3.539025 | 3.539025 | 37 | MATCH |
| 2025 to Oct 2026 | none (unhedged) | 4.442 | 4.441876 | 4.441876 | 37 | MATCH |
| 2025 to Oct 2026 | half hedge (static fraction 0.5) | 3.165 | 3.165128 | 3.165128 (static file, see note) | 37 | MATCH |

### 24-hour horizon (h 6)

| Partition | Policy | Claimed | Archived | Reproduced | n | Verdict |
|---|---|---|---|---|---|---|
| 2020-2022 | delayed (add_two_market_up) | 3.587 | 3.587316 | 3.587316 | 44 | MATCH |
| 2020-2022 | immediate (fixed_beta) | 3.169 | 3.168885 | 3.168885 | 44 | MATCH |
| 2023-2024 | delayed (add_two_market_up) | 1.922 | 1.922432 | 1.922432 | 59 | MATCH |
| 2023-2024 | immediate (fixed_beta) | 0.735 | 0.735369 | 0.735369 | 59 | MATCH |
| 2025 to Oct 2026 | delayed (add_two_market_up) | 2.595 | 2.595440 | 2.595440 | 37 | MATCH |
| 2025 to Oct 2026 | immediate (fixed_beta) | 0.977 | 0.977168 | 0.977168 | 37 | MATCH |

Result: 18 of 18 claimed cells MATCH. No deviation cells.

Half hedge derivation, verified: original/static_fraction_comparison.json carries 9 rows (fractions 0.25, 0.5, 0.75 for each of its period labels 2019_2022, 2023_2024, 2025_Oct2026) with n 44, 59, 37 matching the 72-hour counts. The file has no horizon field; its values are the 72-hour horizon, proven by the linearity check below. Each row states its derivation in its own derivation field: fixed fractional hedge P&L is linear in size under the linear fee and funding model, with the asset leg constant. Independent verification from results.json: static_mean(f) equals unhedged_mean plus f times (fixed_beta_mean minus unhedged_mean) for all 9 rows, with maximum absolute discrepancy 6.94e-18. The file's dynamic_minus_static field also equals the delayed policy mean (add_two_market_up) minus static_mean for all 9 rows, maximum discrepancy 6.94e-18. The half hedge column is therefore not a separate simulation; it is the exact linear interpolation halfway between the unhedged and full fixed hedge 72-hour means, and its claimed values (2.938, 1.710, 3.165) match the fraction 0.5 rows (2.938297, 1.709814, 3.165128) at 3 decimals.

For context only (not claimed, not audited as claims): the 24-hour unhedged means in the same files are 4.9015, 1.6086, and 2.5552 for the three partitions.

## STEP 4B: C5 examples

Method note: original/conditional_contracts.py run as main writes conditional_payoff_examples.json beside itself. To honor the rule against modifying original/, a byte copy was run in /tmp/c5run and its written output compared against the archived copy. The script printed "Four supplied-model checks passed; no actual arbitrage claimed." and exited 0. Its written file is byte-identical to original/conditional_payoff_examples.json (cmp clean, parsed JSON equal).

| Check | Required | Observed | Verdict |
|---|---|---|---|
| Unknown history minimum terminal PnL is negative | below 0 | -0.9500000000000001 (min payoff 0 minus cost 0.95) | PASS |
| Verified case minimum terminal PnL is +0.05 at prices 0.40 and 0.55 | +0.05 (cost 0.95, floor payout 1.00) | 0.04999999999999993, which is 1.00 minus 0.95 up to float representation; payoffs [1, 2, 1], minimum payout 1.0 | PASS |
| State (0,1) present with unknown history | present | states [[0,0],[0,1],[1,0],[1,1]], (0,1) present | PASS |
| State (0,1) absent with verified higher target not previously hit | absent | states [[0,0],[1,0],[1,1]], (0,1) absent | PASS |

Directed package route for C5: run_request.py examples/C5.json produced output exactly equal to examples/C5.expected.json (the verified case: minimum terminal PnL 0.04999999999999993, states [[0,0],[1,0],[1,1]]). The reference.py main dump independently shows the same unknown case (-0.9500000000000001) and verified case. C5 verdict: PASS on every check.

## Findings

1. GREEN, calculation identity: the portable route changes paths and write locations only. No calculation-relevant difference between run_historical.py and original/two_clocks.py.
2. GREEN, reproduction strength: at pinned library versions the replay is byte-identical to the archived outputs, a stronger result than the documented 1e-12 tolerance. File hashes match Astra's own recorded reproduced hashes.
3. PARTIAL (environment sensitivity, cured in pass): under the installed numpy 1.26.4 and pandas 2.1.4, 31 break_even_round_trip_bps leaves in results.json drift by 1.002e-12 to 2.842e-12 absolute (relative at most 1.558e-13), and only 11,360 of 27,513 leaves are exact. The package tolerance criterion still passes with zero mismatches. The pinned venv eliminates the drift entirely. Any future rerun on unpinned versions should expect this noise class and not mistake it for a data or code change.
4. UNVERIFIED by design (scope limit, disclosed in the package): tools/verify_bundle.py cannot pass in this mirror layout. It reports missing 0 and unlisted 800: the 799 files under data_archive/unpacked/ plus the combined data_archive/market-data.tar.gz, all added by Step 1 of this audit program and not part of the payload manifest (86 payload files, all present and hash-correct, since missing is empty). This is a mirror layout artifact, not a payload defect. The bundle's own payload integrity is separately proven by restore_data.py hash checking all 799 restored data files and by the byte-identical replay.
5. BLOCKED as shipped, with a working substitute (recorded, not a defect): original/test_two_clocks.py cannot execute in the portable layout because the original module hardcodes origin machine paths. Its six tests survive verbatim (import line excepted) as tests/test_historical_kernel.py and pass.
6. Scope confirmation (Step 2 finding F1 stands): the parent event list is consumed as given (288 events in, 145 filtered by the code's BTC sign filter, 3 events excluded on data completeness, 140 events and 280 event/horizon rows out). The C1 table is verified conditional on that preserved list. The upstream event selector is not reproduced by this package and was not audited here.
7. Naming note (no numeric effect): the first partition's code name is development_2019_2022 with a window opening at epoch 0, while the report labels it 2020-2022. Included events in fact begin 2020-01-16, so the report label describes the sample correctly.

## Verdict restated

Audit verdict: REPRODUCED. Tests: 30 run, 30 passed in both environments; 6 of 6 synthetic examples exact. Reproduction: 27,513 values compared, 27,513 matched within the package 1e-12 criterion in both environments, 27,513 matched exactly in the pinned venv, 0 mismatches beyond tolerance in either environment. C1 table: 18 of 18 claimed cells match at 3 decimals, event counts 44, 59, 37 confirmed at both horizons. C5: PASS on all four checks plus the directed route.

STATUS: GREEN. Evidence pointer: this file, with observed counts and hashes from runs executed in this session (installed pass outputs preserved during the session at /tmp/runs_installed, pinned venv outputs at six_constructions_2026-11-15/runs/historical/).
