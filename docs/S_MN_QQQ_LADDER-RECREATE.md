# s_mn_qqq_ladder: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_mn_qqq_ladder`, canonical name "s_mn_qqq_ladder", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_qqq_ladder" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_mn_qqq_ladder`, label "Midna QQQ Ladder (Midna port)", kind 1d, enabled True, state shadow. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Midna QQQ Ladder port: a cash-secured short-put ladder on QQQ, shadow-tracked on this stocks-only desk (no broker orders). It sells one new band put layer a week, three contracts a layer, on its own $1,000,000 book, and manages each layer by challenge state. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description); the same label and config appear under the related `lz_s_mn_qqq_ladder` alias in a separate accounting entry, which records only a ladder mark-to-market (shadow) plan, with no ladder construction rule; the construction rules below are from `sleeves/midna/ladder.py` in Test.

## Full algorithm

From the header and constants of `sleeves/midna/ladder.py`, in evaluation order. Session: regular hours from 10:00 ET. Sales are booked at the bid, buy-backs at the ask, per contract x 100.
1. Severe challenge (checked first): spot at or below the strike, or ask at least 3x the sale credit, or live put delta at least 0.35: the put is bought back; this needs today's fresh chain and the cash for it.
2. Short datedness: anything with 7 days or fewer left is bought back.
3. Roll up: 8 to 21 DTE, not rolled before, not challenged: QQQ above the sale's spot, the put's ask at most half its credit: buy it back and sell the band put above it in the same expiration (band = delta 0.05 to 0.08, nearest 0.065, lower strike on a tie) whose bid is at least that ask, when the cash still secures it.
4. Roll down: 8 to 21 DTE, challenged (ask at least 2x credit, delta at least 0.20, or QQQ at or below strike) but not severe: buy back and sell the band put below the strike in the later expiration nearest 45 days (38 to 52) whose bid is at least half the old credit, when the cash still secures it.
5. New layer, once per ISO week: QQQ not down on the day and VIX not up on the day; no open put challenged; today's fresh chain (at most 20 minutes old) whose spot is within 2% of QQQ's quote; the expiration nearest 45 days (38 to 52, a tie takes the later) not already held; sell the band put (delta 0.05 to 0.08, nearest 0.065); the cash after the credit, less the strikes already secured, must secure 3 x strike x 100. Quantity: 3 contracts a layer.
6. Lane wrapper (config row for this id): entry policy `midna_none` (no buy-block; shadow book), max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order `capped_limit_day`; exit rule "Midna plan: ladder mark-to-market (shadow)", hold_from plan, hold_unit_kind 1d, stop_pct 99.0, max_bars 0. Sizing row: budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_dv20_usd 100000. Research line in the row: LADDER_NAV=1e6 LADDER_QTY=3 (the ladder book's own $1,000,000 book, distinct from the lane's $1,000 shadow sizing row).

## Files in this repo

- This doc: `docs/S_MN_QQQ_LADDER-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id; the related `lz_` form of this lane is a separate strategy entry in the accounting.
- Signal code (already in Test): `sleeves/midna/ladder.py` (the QQQ ladder book; its header names its source as the QQQ ladder module of the upstream desk, ported line for line).
- Producer named in the code (already in Test): `packages/claude/master-desk-feedlib/desk/feedlib/midna_options.py` (listed QQQ chain, option marks).
- Related recreation doc (already in Test): `docs/LZ_S_MN_QQQ_LADDER-RECREATE.md` (the `lz_` form of this lane, same label and config).

## Configuration

Full lz_engine config row for `s_mn_qqq_ladder` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_mn_qqq_ladder",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1d",
  "label": "Midna QQQ Ladder (Midna port)",
  "enabled": true,
  "state": "shadow",
  "status_text": "shadow-tracked (no broker orders): QQQ options ladder; Test desk is stocks-only \u2014 paper-tracked from option-marks/ladder",
  "source": {
    "producer": "sleeve_midna (Midna entire-branch signal files + Yahoo)",
    "file": "shadow/paper_sleeve/live/midna/midna_fires_v1.json",
    "lane": "s_mn_qqq_ladder"
  },
  "entry": {
    "policy": "midna_none",
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
    "rule": "Midna plan: ladder mark-to-market (shadow)",
    "hold_from": "plan",
    "hold_unit_kind": "1d",
    "stop_pct": 99.0,
    "max_bars": 0,
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
    "Midna qqq-ladder.ts LADDER_NAV=1e6 LADDER_QTY=3",
    "InfinityBlade: faithful Midna rules; start FLAT; no fake feeds/fills",
    "live/midna/reference_positions.json (comparison only)"
  ],
  "flags": [
    "options/ladder book: stays shadow on the stocks-only desk (Trader GO 2026-10-14: stocks only)",
    "Midna lane with NO buy-block (qqq-ladder: shadow options book)"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_mn_qqq_ladder` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_mn_qqq_ladder` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- No new layer is sold in a week that already has one, on a QQQ-down day, on a VIX-up day, or while any open put is challenged.
- A put with spot at or below strike, ask at least 3x credit, or delta at least 0.35 is bought back before any roll is considered.
- Every open put with 7 or fewer days left is bought back.
- On this desk the lane stays shadow: no broker order is emitted for this id.
