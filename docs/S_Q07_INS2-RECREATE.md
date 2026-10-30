# s_q07_ins2: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_q07_ins2`, canonical name "s_q07_ins2", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_q07_ins2" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_q07_ins2`, label "Q07 insider2 confluence cells (index)", kind 1w, enabled False, state dead. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Q07 insider2 confluence cells (index). This is an INDEX / placeholder lane, not a directly trading sleeve: enabled false, state dead, budget 0, 0 slots. Its status text in the config row is: INDEX (1.0.3): the cells trade as s_q07w_*ins2* lanes. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description).

## Full algorithm

Host family rule (catalog section 4.1, as coded in `desk3/lazarus_q07.py` and `desk3/q07_engine.py`): take the Tensor 1W signal of the named family in the named cap band, apply the named alt-data filters (a filter with no evidence fails closed), buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the time horizon in the cell name. Tag readings in the record: tierA = tier_noliq A / dv20 >= $100k; deep70 = depth60 >= 70 (in the q07_engine reading: close at or below 70% of the trailing 252-session high); mom6 = ret126 >= pre-2020 q67 (in the q07_engine reading: positive 126-session return); cheap5 = px_fire < 5; ins2 = insider_buys >= 2.
Index wrapper (config row for this id):
1. Source: producer `sleeve_feed composer (tracker ledger + alt-data tags)`, file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, lane `s_q07_ins2`.
2. Entry wrapper: policy `fear_day`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order `capped_limit_day`.
3. Exit wrapper: rule "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = per cell lane)", hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, rest null, plan_overrides [].
4. Sizing row: budget_usd 0, max_slots 0, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Because budget and slots are 0, this index lane itself takes no position; the trading cells are the s_q07w_*ins2* lanes (ins2 = insider_buys >= 2; research lines cite the Form 4 insider plugin output and its parity record).
5. Research lines in the row: Q07 insider2 cells -> one lane per cell (s_q07w_*ins2*) in 1.0.3, with the tag definitions above.

## Files in this repo

- This doc: `docs/S_Q07_INS2-RECREATE.md`
- Host code (already in Test): `desk3/lazarus_q07.py` (shared Q07 fire-consumer engine for the s_q07w_* cell lanes) and `desk3/q07_engine.py` (the consolidated Q07 engine: filter readings, QQQ-down gate, 15% stop, horizon exit).
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

Full lz_engine config row for `s_q07_ins2` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_q07_ins2",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1w",
  "label": "Q07 insider2 confluence cells (index)",
  "enabled": false,
  "state": "dead",
  "status_text": "INDEX (1.0.3): the cells trade as s_q07w_*ins2* lanes",
  "source": {
    "producer": "sleeve_feed composer (tracker ledger + alt-data tags)",
    "file": "shadow/paper_sleeve/live/sleeve_fires_v1.json",
    "lane": "s_q07_ins2"
  },
  "entry": {
    "policy": "fear_day",
    "max_delay_minutes": 65,
    "limit_band_pct": 5.0,
    "limit_buffer_pct": 1.0,
    "window_sessions": 5,
    "no_chase_mult": 1.02,
    "stock_red": true,
    "qqq_red": true,
    "order": "capped_limit_day"
  },
  "exit": {
    "rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = per cell lane)",
    "hold_from": "fill",
    "hold_unit_kind": "1w",
    "stop_pct": null,
    "max_bars": null,
    "rest": null,
    "plan_overrides": []
  },
  "sizing": {
    "budget_usd": 0,
    "max_slots": 0,
    "position_usd": 1000,
    "position_usd_by_class": {},
    "one_share_max_usd": null,
    "cap_pct_of_dv20": 1.0,
    "min_slot_fraction": 0.9,
    "global_slot_usd": 1000,
    "min_dv20_usd": 100000
  },
  "research": [
    "DESK_INTEGRATION/EDGE_INVENTORY.md Q07 insider2 cells -> one lane per cell (s_q07w_*ins2*) in 1.0.3",
    "DESK_INTEGRATION/TAG_DEFS_FOR_DESK_OPS.md (Research Lab 20:55 ET) + CORPUS_AUDIT/code/ctx_feats.py: tierA, deep70 = depth60 >= 70, mom6 = ret126 >= pre-2020 q67, cheap5 = px_fire < 5, stress_vix20 = V",
    "ALTDATA_LIVE/out/insider2_{latest,history}.parquet (plugins/form4_insider.py, nightly 18:47 ET); parity out/PARITY_form4_2026-10-05.md: insider2 100% on 2,922 ticker-dates, ins_buyers180 99.97% (Resea"
  ],
  "flags": [
    "placeholder/index: INDEX (1.0.3): the cells trade as s_q07w_*ins2* lanes"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_q07_ins2` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_q07_ins2` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- This index lane emits no position of its own: enabled is false, budget is 0 and max_slots is 0 in its config row.
- A fire without insider evidence (insider_buys >= 2) does not pass the ins2 filter in any cell lane (fail closed).
- Cell-lane entries occur only on a QQQ-down day within 5 sessions of the signal, and exits follow the 15% stop / per-cell horizon plan.
