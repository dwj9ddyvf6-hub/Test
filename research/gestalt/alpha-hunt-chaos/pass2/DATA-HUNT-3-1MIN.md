# DATA HUNT 3: 1-MINUTE CACHE WIDENING

Owner order Sun 2026-11-15 18:26 ET, Tier A standard. Executed Sun 2026-11-15 evening ET.
Home: ~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/
Tooling: dh3_tools.py (probe, widen, verify, svs30 phases). Widen log: dh3_widen_log.json. SVS30 counts: dh3_svs30_counts.json.

## POTENTIAL EDGE FOUND (measurability class)

The widened coverage changes the measurability of two named reads, which is the potential edge this hunt was ordered to look for:

1. The overnight falsifier tracker's SVS30 field (final-30-RTH-minute tick-rule signed volume share, on_falsifier_tracker.py svs30_fields) was capped at 2 of 5 carry names because only NVDA and AMD had 1Min cache files among SNDK, CRWV, RKLB, NVDA, AMD. It is now computable for 5 of 5 carry names, on all 17 of 17 KG-10 span sessions each, and on all 53 of 53 widened-window sessions each. The three previously unmeasurable carry names (SNDK, CRWV, RKLB) now carry a full SVS30 series over both spans, so the KG-10 closing-imbalance conditioning on the carry basket can be run as registered instead of on a 2-name stub.
2. The same field is now computable across the Focus-30: 29 of 30 names have 1Min coverage (SIVE named-excepted), 28 of 29 with all 17 KG-10 sessions computable, ALAB at 15 of 17.

No alpha is measured by this hunt. What is found is an armed read: a registered conditioning variable that could not be computed on 3 of 5 carry names yesterday can be computed on 5 of 5 today, at full session depth. Whether SVS30 conditioning separates the overnight edge is the next test, not a result claimed here. Recommended method-ledger autopsy entry: coverage unlocks are edge-shaped; a field capped by missing cache is a route failure, and the cure was at the data layer, not in the read.

## COVERAGE VERDICT

GREEN on coverage. The desk 1Min cache went from 21 symbols to 44. All 29 widened Focus names hold a 1Min.jsonl covering the full window 2026-09-01 to 2026-11-13 with every one of the 53 sessions present and zero session holes inside the window. RTH-complete sessions (at least 385 bars stamped 09:30 to 15:59 ET, the tracker's CACHE_MIN_BARS rule): 53 of 53 for 26 names; ARM 51, FLNC 51, ALAB 48, where the short sessions are genuinely thin trading days in the source data, itemized in the register, not fetch gaps. Per-name proof: DH3-COVERAGE-REGISTER.jsonl, one row per Focus name, SIVE included as a named-excepted row.

Carry-name SVS30 coverage, the headline line: before 2 of 5, after 5 of 5.

## BASIS CHECK (step 1, run before any write)

Probe 1: SNDK 1Min for 2026-11-12 (Alpaca, feed sip, adjustment raw) returned 960 rows spanning 2026-11-12T09:00:00Z to 2026-11-13T00:59:00Z, the full 04:00 to 19:59 ET bar day.

Probe 2: NVDA fetched for 2026-11-12 against the existing cache file on the 960 shared timestamps: 937 exact matches, 23 differing stamps, zero fetched-only and zero cached-only stamps. Characterization across 9 symbol-days (NVDA, AMD, MU, PLTR, AVGO, AMAT on recent and older sessions) resolved the 23:

- Older sessions are byte-identical: NVDA 2026-10-21 matched 959 of 959, AMD 2026-10-21 matched 790 of 790, zero price and zero volume differences. Same basis, proven where settlement is final.
- All differences sit in recent sessions and are volume-only except one stamp. Cached volume is always greater than or equal to fetched, by small amounts (mostly 1 to a few hundred shares) plus round-number excesses (16,500; 46,000; 100,000; exactly 250,000 on the single price-differing stamp, NVDA 2026-11-12 21:13Z, an after-hours bar whose cached high carries one extra print the current SIP response no longer includes).
- Reading: the cache was accrued before post-session exchange trade corrections settled; the fetched bars carry the corrected values. This is a settlement-timing artifact on a handful of stamps, not a basis conflict: no price scaling, no feed-level volume ratio, older sessions exact.

Verdict: basis MATCHES, proceed. The merge rule made the point doubly safe: existing rows were preserved verbatim and fetched rows were added only where the timestamp was absent, so no cached row was ever overwritten by a corrected fetched row.

## WHAT WAS DONE

- Backup first: the 6 existing Focus 1Min files (NVDA, AVGO, AMD, AMAT, MU, PLTR) copied verbatim into dh3_cache_backup/ before any write; spot hash check on NVDA matched the source file.
- Window per name: 2026-09-01 to 2026-11-13 for all 29 names. Each name's own stored 1Day span governed its session set inside the window: the 11 names with 53-session 1Day files contributed exactly those sessions; the 6 existing names' 515-session 1Day spans contain the window, so their in-window sessions were used; the 12 names with no 1Day file (SMH, SOXX, MRVL, TSM, COHR, RKLB, FLNC, EOSE, BE, VST, CEG, XLE) used the stated default window on the SNDK 53-session calendar. Window source is recorded per name in the register.
- Fetch: Alpaca bars endpoint, feed sip, adjustment raw, timeframe 1Min, paginated at limit 10000, paced, one symbol at a time. Credentials only via desk3.run_live.credential_env, never printed. Total fetched: 1,108,337 bars; total added: 1,033,782; grand total across the 29 widened files: 1,108,518 bars.
- Merge for the 6 existing files: union by timestamp, existing rows verbatim, fetched rows only where absent, file rewritten sorted by t. Conflicts on shared stamps (the settlement artifact above) counted per name: NVDA 93, AVGO 29, AMD 31, AMAT 20, MU 46, PLTR 25; total 244, all on stamps whose cached rows were kept untouched. The 23 new files have zero conflicts by construction.
- Preservation proof on the final files: all 74,736 pre-existing rows across the 6 files are present verbatim in the widened files (missing 0 per name), every widened file is sorted ascending by t with zero duplicate timestamps. The 15 non-Focus 1Min files were never written; the only files created or changed are the 29 Focus paths.

## SVS30 RECOMPUTE (step 5)

Definition replicated exactly from the tracker (svs30_fields and _cache_rth_bars): RTH bars 09:30 to 15:59 ET from the cache, session covered only at 385 or more RTH bars, SVS30 is the sum of sign(close minus previous RTH close) times volume over bar-start stamps 15:30 to 15:59 ET, divided by the window volume, rounded to 4 places.

Cross-check against the tracker's own svs30_fields on the final cache, NVDA and AMD over the 17 KG-10 sessions (2026-10-21 to 2026-11-12): 34 of 34 values identical, 0 mismatches. The replica is faithful, so the counts below are the tracker's counts.

Carry-name coverage (computable name-sessions):

| Name | KG-10 before | KG-10 after | Full window after |
|------|------|------|------|
| SNDK | 0 (no file) | 17 of 17 | 53 |
| CRWV | 0 (no file) | 17 of 17 | 53 |
| RKLB | 0 (no file) | 17 of 17 | 53 |
| NVDA | 14 of 17 | 17 of 17 | 53 |
| AMD | 14 of 17 | 17 of 17 | 53 |

Carry names with any computable KG-10 SVS30: before 2 of 5, after 5 of 5. The before figure for NVDA and AMD also rose from 14 to 17 sessions because the merge filled the old cache's missing sessions (2026-10-26, 2026-10-27, 2026-10-28).

Full 29-name table (KG-10 computable sessions of 17; full-window computable sessions of 53): every name is 17 and 53 except ARM (17, 51), FLNC (17, 51), ALAB (15, 48). SIVE: excepted. Machine-readable counts: dh3_svs30_counts.json.

## OPEN ROWS

- ALAB has 2 KG-10 sessions (2026-10-21 at 375 RTH bars, 2026-10-23 at 384) and 5 window sessions under the 385-bar completeness rule; ARM has 2 (2026-09-09, 2026-09-10) and FLNC has 2 (2026-10-07, 2026-10-09). These are thin source sessions, verified present with their true bar counts in the register; no fetch route adds bars the market did not print. Any read consuming them gets the tracker's named reason (session_incomplete_in_1min_cache), never a fabricated value.
- The 244 settlement-artifact conflicts are documented, not cured: the cached (pre-correction) rows stand as the desk's historical record by the preservation rule. If a future read needs corrected values on those stamps, that is a separate ruling, not a silent rewrite.
- SIVE remains without a US listing data route, named-excepted by the task.

## STATUS

STATUS: GREEN. Evidence pointer: DH3-COVERAGE-REGISTER.jsonl (per-name totals, sessions, completeness, holes on the final files), dh3_widen_log.json (per-name fetched, added, conflicts), dh3_svs30_counts.json plus the printed 34 of 34 tracker cross-check in dh3_tools.py svs30 output, and the verbatim-preservation check over dh3_cache_backup/ (74,736 of 74,736 rows present, 0 missing). Carry-name SVS30 coverage: before 2 of 5, after 5 of 5.
