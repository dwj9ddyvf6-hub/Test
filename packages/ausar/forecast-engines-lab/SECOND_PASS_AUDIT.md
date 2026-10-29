# Second-pass corpus and engine audit

**Audit date:** 2026-10-29

**Silicon snapshot:** `origin/main` `aad9d2148752a6862ce7a6c44685311aa7310947`

**Purpose:** revisit under-indexed evidence, source timing, validation claims, and the 30 forecast hypotheses. This is a research audit; it does not authorize trades or claim positive expectancy.

## What this pass checked

- Reconciled the Git tree against `CORPUS_FILE_INDEX.csv`, the family traceability CSV, the unified requirement index and its separate source registers, the active-family ledger, the 39-stream vault index, and the mirror triage.
- Verified every one of the 86 active target-report SHA-256 values in `rea_target_inventory.csv` against its report file in this snapshot. All 86 matched. Headings were inventoried across all reports; technical evidence sections were revisited in depth for Saty, TheStrat, Trade Ideas, Option Alpha, QuantiX, AlgoAlpha, TrendSpider, Cheddar Flow, Unusual Whales, and Tapeboard.
- Re-read the design and scorer code with emphasis on source cadence, point-in-time availability, source dependence, and what the output actually means.
- Queried the prior Ausar/sleeve research context and the archived recovery result for the missing original R21 database and ETF manifest.

This pass did not semantically adjudicate every paragraph of all 86 reports, every generated locator, all 4.19 GB of recovered source streams, or the payload of the 224 mirrored repository bundles. Those are explicit corpus limits, not completed review claims.

## Reconciliation findings

| Surface | Second-pass result | Interpretation |
|---|---|---|
| Current Git tree vs corpus file index | 20,324 Git paths; 19,735 index rows. 628 Git paths are absent from the index; 39 index rows point to local-only vault paths outside this tree. The index labels 19,290 paths present in checkout and 406 as sparse omissions. | The 628 need scope triage before treating the index as exhaustive. The largest buckets include 414 `research/rea-teardowns/thestrat` paths and generated/build or other scoped paths. A path-count difference does not mean every missing path is vendor evidence. |
| Other repository count statement | `FULL-GAP-RECONCILIATION-2026-10-28.md` reports 20,208 non-inventory paths plus its inventory file (20,209 total), tied in its text to a `c1942f0b` baseline. | The checked `origin/main` tree is a different snapshot (`aad9d…`) with 20,324 leaves. Rerun the index generator against one named commit before comparing these counts as if they were the same snapshot. |
| Requirement map | 557 rows; all are `NOT_REVIEWED_BY_GENERATOR`. Categories are 402 shared-surface, 79 shared-surface without an order path, 63 candidates, and 13 not implemented. | These are generated locators and heuristic topics, not 557 semantically validated requirements. |
| Unified requirement records | Checked-in CSV has 23 rows. The source registers contain 9 candidate records, 14 scoped records, and a separate OptionStrat JSON register with 8 requirements. The builder asserts 31 total rows. | The 31-record prose is supported by the three input registers, but the checked-in CSV is stale and omits the eight OptionStrat rows. No generator was run against the source tree in this feature branch. |
| Active-family progress | The 2026-10-27 CSV says 80 complete and 6 in progress. The 2026-10-28 reconciliation says 81 complete, 5 bounded-complete and zero in progress, across 100 pass rows/86 families. | Keep both source dates visible; the ledger was not refreshed to the later reconciliation state. |
| Manual triage overrides | 445 rows: only 3 carry `semantically_reviewed=true`; 39 are active-family crosswalk metadata only; 403 mirror repositories are excluded by name-level scope triage and have no upstream license clearance recorded. | The override table does not close the 557-row semantic extraction gap or establish mirror-content irrelevance. |
| Recovered vault streams | 39 streams / 4,185,551,561 bytes; 37 complete JSON structures and two valid prefixes with trailing fragments separately hashed. | Structural parsing and hash integrity are recorded. Content meaning, rights, source identity and implementation mapping remain unadjudicated. |
| Mirrored repositories | 224 bundles, 4,019,267,109 bytes; name-only family screen found zero canonical matches. | Aliases and relevant payload content remain unreviewed; do not use these bundles as a cleared training corpus. |

## Vendor evidence that changes how the engines should be designed

- **Signals are not a common data type.** Saty's public ATR Levels code gives explicit prior-period close/ATR levels and EMA ordering, but no measured predictive edge. TheStrat public gap rules still contain an unresolved daily-open versus kicking-bar-open trigger. Both should be represented as frozen event definitions before they enter a study, not as prevalidated signals.
- **Backtest claims are product-specific and bounded.** Trade Ideas' public OddsMaker material contains different historical-window descriptions and a one-minute/non-tick limitation. Option Alpha describes minute option history for short-dated tests and warns that live execution cannot be reproduced fully. QuantiX publishes numerical IQ gates, but the underlying split/leakage/repeated-search policy is not fully specified. TrendSpider warns about overfit. These designs support recording baselines, test windows, version, costs and failed attempts; they do not establish vendor alpha.
- **Automation surfaces are not execution guarantees.** Tapeboard describes simulated fills; its Broker Link is a local, user-clicked ticker handoff, not broker order routing. Option Alpha and AlgoAlpha describe separate backtest, alert and execution layers. The forecast lab therefore continues to emit no order or trade state.
- **Options/flow products need provenance and uncertainty.** Cheddar Flow's October 2026 feed-capacity and speed statements lack a reproducible latency distribution, complete coverage measure, and public event-dedup/quote-clock specification. Unusual Whales documents authenticated APIs and inconsistent public MCP tool counts across pages; an anonymous catalog is not live market data. Neither option volume nor open interest identifies dealer direction. Multiple vendors can derive scores from the same tape, so vendor agreement cannot be counted as independent evidence without lineage.
- **Public macro and positioning data are clocks, not timeless features.** EDGAR submissions/XBRL have filing availability timestamps; ALFRED preserves macro vintages; COT uses a measured-as-of date distinct from release time; FINRA short interest is a twice-monthly position snapshot and is not daily short-sale volume. On 2026-10-27, CFTC announced a planned semiweekly COT rollout by year-end. The engine must use the schedule actually effective on each date, not switch on a future schedule from the announcement.

## Changes made to the forecast package

1. **Cadence-aware freshness limits.** Quarterly XBRL/disclosure, 13F, reported buybacks, monthly-or-slower alternative panels, macro composites and weekly COT/inventory fields no longer inherit the generic two-day cap. Publication timestamps and `as_of` validation remain mandatory. The COT cap allows the weekly measurement/release cycle and holiday delays while still rejecting observations older than fourteen days; inventory remains capped at eight days.
2. **Three-clock feature trace.** Each accepted feature now records age since observation, age since publication, and publication lag. This makes a stale measurement distinguishable from a fresh but late-published value.
3. **Declared lineage concentration.** Each forecast reports a Herfindahl concentration and effective count across caller-declared source groups. This surfaces apparent multi-feature breadth that collapses to one declared source family. It does not estimate correlations or assert true independence.

The 30 forecast formulas remain research hypotheses with hand-set coefficients. No model-error meta-forecast was fitted: the archived Ausar recovery search reported the exact R21 SQLite source and standalone ETF corporate-action manifest as not found, and the current package has no licensed, timestamp-complete outcome panel. Building a “forecastability probability” without that panel would manufacture confidence. The next empirical step is to reconcile the source indexes, freeze target/horizon definitions, and collect rights-cleared point-in-time outcomes before fitting calibration or abstention gates.

## Archived Ausar and sleeve context

The 100 sleeve descriptions supplied in this conversation are strategy specifications, not results. The prior Edge-repo methodology calls for a frozen incumbent, one deliberate change at a time, matched baselines, temporal holdouts, cost and regime checks, and retention of failed variants. Prior Femto research summaries also report no Grade-A independent replication; many candidates were better interpreted as avoid/veto signals than positive alpha. The archival exact-source search reported no exact R21 database and no authenticated standalone ETF corporate-action manifest. I therefore used those materials to strengthen evidence and data controls, not to rank sleeves by unavailable P&L.

## Next-pass queue

1. Regenerate or reconcile `CORPUS_FILE_INDEX.csv` and `UNIFIED-REQUIREMENT-INDEX-2026-10-27.csv` on one pinned tree; preserve the 39 local-only vault references separately.
2. Turn the 557 locator rows into source-reviewed requirements in bounded batches; keep unknown, partial, rights-limited and not-implemented states explicit.
3. Semantically review the 37 complete vault JSON payloads and the two preserved fragments only after source/rights scope is confirmed; inspect mirror payloads only with a source and license basis.
4. Build a point-in-time outcome panel and one-change-at-a-time evaluation protocol before selecting or calibrating engines. Keep abstentions, source lineage, data vintages and all attempted variants in the ledger.
