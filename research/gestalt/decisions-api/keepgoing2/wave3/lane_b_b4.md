# Wave 3 Lane B4: Map Cell D-17, Forecast Engines Per-Engine Ranking

Ledger: ~/workspace/terminal-lineup/forecast/ledger.jsonl. Method: FULL-LEDGER recompute (one streaming pass, cheap) plus the tasked stratified 1,000-grade sample (proportional by engine, seed 42) as a cross-check. Both are reported; the full ledger governs. Machine record in lane_b_b4.json.

## Census, recounted

431,124 rows: 354,950 forecasts, 69,916 grades, 6,257 corrections, 1 genesis. That matches the Unlooked Map's record exactly. But grades exist for only 17 engines, not 26; 9 engines have forecasts and no grades and cannot be ranked. Grade rules: brier 55,967, survival_brier 7,340, abs_error 5,544, pinball 1,055, coverage 8, none 2.

Brier population for the ranking: grade rows with rule_id brier, a scores.brier value, and a binary_outcome: 55,947 rows across only 7 engines (engine_02, engine_05, engine_06, engine_08, engine_16, engine_28, engine_30). engine_04 is survival_brier only (mean brier@1 0.2547 over its 3,723 brier@1 rows, reported separately, not mixed in); engine_19 is abs_error only; the other graded engines carry pinball, coverage, or abs_error grades with no Brier to rank.

## Baselines

Two climatologies are printed in the JSON. PRIMARY: each engine against its own event-stream base rate, the standard climatology for that stream. SECONDARY: the pooled population base rate applied to all engines, which mixes event families and flatters engines whose events are rare. Verdicts use the primary. Stated margin: beats climatology means skill (1 minus Brier over climatology Brier) at least 0.05; materially worse means skill at most -0.05.

## Full-ledger ranking (primary baseline)

| Rank | Engine | n grades | Mean Brier | Own base rate | Own climatology Brier | Skill |
|---|---|---|---|---|---|---|
| 1 | engine_08 | 458 | 0.1285 | 0.2031 | 0.1618 | +0.2062 |
| 2 | engine_06 | 25,735 | 0.1827 | 0.2670 | 0.1957 | +0.0666 |
| 3 | engine_05 | 1,593 | 0.2122 | 0.2461 | 0.1855 | -0.1437 |
| 4 | engine_16 | 82 | 0.2429 | 0.5854 | 0.2427 | -0.0009 |
| 5 | engine_02 | 288 | 0.2519 | 0.4167 | 0.2431 | -0.0366 |
| 6 | engine_28 | 27,787 | 0.2554 | 0.5730 | 0.2447 | -0.0439 |
| 7 | engine_30 | 4 | 0.3405 | 1.0000 | 0.0000 | undefined (n 4, all outcomes 1) |

## Named verdicts

- Beats climatology by the stated margin: engine_08 (skill +0.206, n 458) and engine_06 (skill +0.067, n 25,735). engine_06 is the only high-volume engine that clears the margin.
- Materially worse than climatology: engine_05 (skill -0.144, n 1,593). Its finish-above probabilities are worse than always forecasting its own base rate.
- Neither: engine_16 (skill -0.001, effectively climatology itself), engine_02 (-0.037), engine_28 (-0.044, the largest engine by grade count, 27,787 grades, and still below its own climatology). engine_30 is unrankable at n 4.

## Sample cross-check

The stratified 1,000-grade sample (allocation: engine_28 497, engine_06 460, engine_05 28, engine_08 8, engine_02 5, engine_16 1, engine_30 1) reproduces the top of the ranking (engine_08 0.1325, engine_06 0.1753 mean Brier) but is too thin for the small engines (engine_16 and engine_30 get 1 draw each) and flips engine_28 negative on its sample draw. It is reported in the JSON as tasked; no verdict rests on it. The full-ledger recompute is the ranking of record.

Note on what this is: a measurement of forecast calibration quality per engine, not a trading signal. No admission exam applies and no find is claimed for B4. engine_08 and engine_06 beating climatology is a statement about their probability grades, full stop.

STATUS: GREEN for the ranking as scoped (full ledger recounted, sample drawn and printed, both baselines named). Evidence pointer: lane_b_b4.json in this folder.
