# s_mn_gbm_1d_cyan: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_mn_gbm_1d_cyan`, canonical name "s_mn_gbm_1d_cyan", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_gbm_1d_cyan" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_mn_gbm_1d_cyan`, label "Midna Daily cyan trees (Midna port)", kind 1d, enabled True, state live. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Midna Daily cyan trees port: a daily (1d) lane that takes fresh daily Tensor Cyan fires scored by a frozen gradient-boosted model in its top tier and holds each name 21 sessions with no price stop. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description); the same label and config appear under the related `lz_s_mn_gbm_1d_cyan` alias in a separate accounting entry, whose classification evidence (from muse-desk-v3 sleeves/daily_cyan_gbm.py) is: entries require an external frozen GBM model score at or above the 90th percentile cut, price and dv20 filters, exit at the 21st session close.

## Full algorithm

1. Signal production (external to the lane): the sleeve_midna producer writes fires to `shadow/paper_sleeve/live/midna/midna_fires_v1.json`; the underlying selection in `sleeves/daily_cyan_gbm.py` is: candidates are daily cyan fires carrying a frozen GBM score; non-finite or non-numeric scores are skipped; the cut is the session's own 90th percentile of scores (enhancement on, default) or the absolute control cut 0.00208 (enhancement off); the signal-day close must be at least $5 and dv20 (mean 20-session dollar volume) at least $1,000,000; ranking is best score first, capacity at most 10 positions counting the book.
2. Lane entry wrapper (config row for this id): policy `midna_block`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions null, no_chase_mult null, stock_red false, qqq_red false, order `capped_limit_day`.
3. Lane exit wrapper (config row): rule "Midna plan: no stop / time exit 21 sessions", hold_from fill, hold_unit_kind 1d, stop_pct 99.0 (no price stop; the number is the record's no-stop marker), max_bars 21, rest time, plan_overrides [].
4. Sizing (config row): budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Flags in the row: runs side by side with Main 1dc as a separate experiment; L-146 scaled x0.611: $2,000 -> $1,000 / 1 slot.
5. Start state: start FLAT; upstream positions are reference only (config status_text).

## Files in this repo

- This doc: `docs/S_MN_GBM_1D_CYAN-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id; the related `lz_` form of this lane is a separate strategy entry in the accounting.
- Signal code (already in Test): `sleeves/daily_cyan_gbm.py` (selection law: frozen GBM score cut, price and dv20 filters, 21-session exit; see Full algorithm), `sleeves/midna/forward.py` and `sleeves/midna/forward_scan.py` (forward-lab book named in the config research line: FORWARD_SPECS id=gbm-1d-cyan, ruleId=V4-GBM-1D-CYAN-ALL, FORWARD_NAV=20000, FORWARD_SLOTS=6).
- Related recreation doc (already in Test): `docs/DAILY_CYAN_GBM-RECREATE.md`.

## Configuration

Full lz_engine config row for `s_mn_gbm_1d_cyan` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_mn_gbm_1d_cyan",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1d",
  "label": "Midna Daily cyan trees (Midna port)",
  "enabled": true,
  "state": "live",
  "status_text": "ready (Midna port; start FLAT; Midna positions are reference only)",
  "source": {
    "producer": "sleeve_midna (Midna entire-branch signal files + Yahoo)",
    "file": "shadow/paper_sleeve/live/midna/midna_fires_v1.json",
    "lane": "s_mn_gbm_1d_cyan"
  },
  "entry": {
    "policy": "midna_block",
    "max_delay_minutes": 65,
    "limit_band_pct": 5.0,
    "limit_buffer_pct": 1.0,
    "window_sessions": null,
    "no_chase_mult": null,
    "stock_red": false,
    "qqq_red": false,
    "order": "capped_limit_day"
  },
  "exit": {
    "rule": "Midna plan: no stop / time exit 21 sessions",
    "hold_from": "fill",
    "hold_unit_kind": "1d",
    "stop_pct": 99.0,
    "max_bars": 21,
    "rest": "time",
    "plan_overrides": []
  },
  "sizing": {
    "budget_usd": 1000,
    "max_slots": 1,
    "position_usd": 1000,
    "position_usd_by_class": {},
    "one_share_max_usd": null,
    "cap_pct_of_dv20": 1.0,
    "min_slot_fraction": 0.9,
    "global_slot_usd": 1000,
    "min_dv20_usd": 100000
  },
  "research": [
    "Midna forward.ts FORWARD_SPECS id=gbm-1d-cyan ruleId=V4-GBM-1D-CYAN-ALL FORWARD_NAV=20000 FORWARD_SLOTS=6",
    "InfinityBlade: faithful Midna rules; start FLAT; no fake feeds/fills",
    "live/midna/reference_positions.json (comparison only)"
  ],
  "flags": [
    "runs side by side with Main 1dc: separate experiment (Trader GO 2026-10-14)",
    "L-146 scaled x0.611: $2,000 -> $1,000 / 1 slots"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_mn_gbm_1d_cyan` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_mn_gbm_1d_cyan` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- A candidate with a non-finite score, a score below the session cut, a close under $5, or dv20 under $1,000,000 (selection code) produces no entry.
- The lane never holds more than 1 slot of $1,000 under its config sizing, and never enters outside the capped_limit_day wrapper with max delay 65 minutes.
- A held name exits at 21 sessions from fill and is not stopped out on price before that.
