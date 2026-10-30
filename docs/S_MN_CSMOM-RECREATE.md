# s_mn_csmom: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.
INCOMPLETE-CODE: no code for this strategy was located in any searched GitHub repo; the searched locations are listed in Provenance / Files in this repo. This package does not claim a faithful recreation.

## Provenance

- Canonical id: `s_mn_csmom`; canonical name: s_mn_csmom; aliases: s_mn_csmom.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type momentum, family unrecorded, algorithm grade FULL; accounting gaps: none recorded. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_csmom" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path for these ids, only the femto-lean forward ports noted where relevant); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path).
- Code found: not found in any searched GitHub repo (Test, Silicon, quant-research-backup, Midna). Nothing was vendored for this package.

## What this strategy is

A cross-sectional momentum ('csmom') book in the s_mn family, recorded live in the lz_engine record (md2_lz_engine, status live). The accounting's classification evidence: 'Midna plan rank exit with a minus 40 percent circuit, a cross sectional momentum ranking book (csmom)'. Accounting algorithm grade FULL, but that grade covers only the lz_engine entry-execution / exit / sizing config reproduced below; the ranking rule that selects names is not in the record and no code was located in any searched repo, so this package is graded INCOMPLETE-CODE. No strategy description is recorded.

## Full algorithm

Everything the record holds, verbatim in substance from the accounting's lz_engine config:
- Entry / execution config: {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}. Read plainly: entries execute as capped limit day orders under the midna_block policy, maximum delay 65 minutes, limit band 5.0 percent, limit buffer 1.0 percent; stock_red and qqq_red blocks off; window_sessions and no_chase_mult null.
- The signal behind the entries (the cross-sectional momentum ranking: lookback, universe, rank construction, rebalance rule) is not in the record.
- Exit config: {"rule": "Midna plan: rank exit / circuit -40%", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 63, "rest": "time", "plan_overrides": []}. Read plainly: positions exit per the Midna plan's rank-exit rule with a -40 percent circuit, holds in 1d units from the plan, nominal stop_pct 99.0, maximum hold 63 bars, rest 'time', no plan overrides.
- Sizing config: {"budget_usd": 9000, "max_slots": 9, "position_usd": 1000, "position_usd_by_class": {}, "one_share_max_usd": null, "cap_pct_of_dv20": 1.0, "min_slot_fraction": 0.9, "global_slot_usd": 1000, "min_dv20_usd": 100000}.
- Filters: none recorded. Parameters: none recorded beyond the config above.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- This package: `docs/S_MN_CSMOM-RECREATE.md`
- Code: NONE FOUND for this canonical id. Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path for these ids, only the femto-lean forward ports noted where relevant); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). The only csmom hit in any searched tree is the separate canonical id's package `docs/LZ_S_MN_CSMOM-RECREATE.md` in Test (canonical lz_s_mn_csmom, a different accounting entry whose record comes from the md2 catalog and which was itself graded INCOMPLETE-CODE); the s_mn sleeves present in Test (for example `adapters/s_mn_faber.py`, `adapters/s_mn_macd.py`, `adapters/s_mn_pairs.py`, `adapters/s_mn_reversal.py`, `adapters/s_mn_vwap.py`) are different strategies and must not be substituted. Nothing was vendored for this package.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "s_mn_csmom" (UNRESOLVED; algorithm grade FULL from the lz_engine config alone).

## Configuration

- lz_engine config exactly as in the Full algorithm (budget_usd 9000, max_slots 9, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000; exit max_bars 63 in 1d units).
- Universe, asset class, timeframe, creator: not recorded in consulted sources.

## Data inputs

not in the record for this entry (the entry policy name 'midna_block' and the exit rule's 'Midna plan' wording are the only data-adjacent facts recorded).

## Install and run

This package cannot be installed as a faithful recreation: no code for this strategy is on file in any searched GitHub repo, and (per the Full algorithm section) key rules are not in the record.
1. Recovery would require the sleeve module or catalog description for this exact canonical id to appear in one of the searched repos.
2. Sibling or similarly named strategies in Test are different strategies; running one of them does not recreate this strategy and must not be reported as doing so.

## Verification

- No tests exist in Test for this strategy and the entry signal cannot be verified: there is no code and no recorded ranking rule.
- Behavior spec from the recorded config, for use if the code is recovered: entries are capped limit day orders under midna_block (max delay 65 minutes, band 5.0 percent, buffer 1.0 percent); exits follow the Midna plan rank exit with a -40 percent circuit and a 63-bar maximum hold; sizing is 9 slots of 1000 USD on a 9000 USD budget.
- Any recreation that invents a momentum lookback, universe or ranking rule fails this package's standard by construction.
- Recovery condition: the sleeve module docstring or a catalog description for this exact id (per the accounting's unresolved note).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
