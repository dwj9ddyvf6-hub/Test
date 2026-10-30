# s_q07w_c52_mi_deep70_mom6_tierA: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_q07w_c52_mi_deep70_mom6_tierA`, canonical name "s_q07w_c52_mi_deep70_mom6_tierA", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_q07w_c52_mi_deep70_mom6_tierA" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_q07w_c52_mi_deep70_mom6_tierA`, label "Q07 w_cyan H52 micro deep70+mom6+tierA (test)", kind 1w, enabled True, state live. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Q07 w_cyan H52 micro cell deep70+mom6+tierA (test). A weekly (1w) Q07 confluence cell: family w_cyan (cyan), horizon 52 weeks, cap band mi (micro), with the named filters deep70+mom6+tierA. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description). Its complete record in Test is the lz_engine config row quoted in Configuration; no executable spec for this id was found in the desk3 Q07 engines, so this package is graded INCOMPLETE-CODE.

## Full algorithm

Host family rule (catalog section 4.1, as coded in `desk3/lazarus_q07.py` and `desk3/q07_engine.py`): take the Tensor 1W signal of the named family in the named cap band, apply the named alt-data filters (a filter with no evidence fails closed), buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the time horizon in the cell name. Tag readings in the record: tierA = tier_noliq A / dv20 >= $100k; deep70 = depth60 >= 70 (in the q07_engine reading: close at or below 70% of the trailing 252-session high); mom6 = ret126 >= pre-2020 q67 (in the q07_engine reading: positive 126-session return); cheap5 = px_fire < 5; ins2 = insider_buys >= 2.
Cell record (config row for this id, the only record found):
1. Label and state: kind 1w, enabled true, state live, status ready (md2 RL64 2026-10-24).
2. Source: producer `sleeve_feed composer (tracker ledger + alt-data tags)`, file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, lane = this id.
3. Entry wrapper: policy `fear_day`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order `capped_limit_day`.
4. Filters for this cell: deep70+mom6+tierA. Tag readings: cheap5 = px_fire < 5; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; tierA = tier_noliq A / dv20 >= $100k (per the config research lines).
5. Exit wrapper: rule "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, rest null, plan_overrides []. Research line: exit at the close of the last NYSE session <= D + 364 calendar days; entry red (Q07 'red'); K 20.
6. Sizing row: budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.
7. Research evidence in the row: Q07 confluence cells deep70+mom6+tierA w_cyan H52 micro red band: n 48, names 32, edge +193.5 [92.0, 328.9], q_fam 0.00628, CONFIRMED; px pool 152.62 CONFIRMED (per the row's CORPUS_AUDIT citation).
8. Gap: no executable spec for this id in `desk3/lazarus_q07.py` SPECS or `desk3/q07_engine.py`, and no standalone sleeve module in any searched repo: not in the record (code). Do not run this cell from the desk3 engines as if it were registered there.

## Files in this repo

- This doc: `docs/S_Q07W_C52_MI_DEEP70_MOM6_TIERA-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id. This row is NOT present in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` or `sleeves/lazarus/vendor/lazarus/sleeves.json` (searched by content).
- Host family code (already in Test, but with no spec for this id): `desk3/lazarus_q07.py` (SPECS table has no entry for this id) and `desk3/q07_engine.py` (its CAP_BANDS_USD defines the mi band as 0 to 300,000,000 USD, but its SPECS / evaluate path has no entry for this id).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

Full lz_engine config row for `s_q07w_c52_mi_deep70_mom6_tierA` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_q07w_c52_mi_deep70_mom6_tierA",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1w",
  "label": "Q07 w_cyan H52 micro deep70+mom6+tierA (test)",
  "enabled": true,
  "state": "live",
  "status_text": "ready (md2 RL64 2026-10-24, Trader t181u)",
  "source": {
    "producer": "sleeve_feed composer (tracker ledger + alt-data tags)",
    "file": "shadow/paper_sleeve/live/sleeve_fires_v1.json",
    "lane": "s_q07w_c52_mi_deep70_mom6_tierA"
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
    "rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))",
    "hold_from": "fill",
    "hold_unit_kind": "1w",
    "stop_pct": null,
    "max_bars": null,
    "rest": null,
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
    "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_cyan-H52-micro-deep70+mom6+tierA (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))",
    "CORPUS_AUDIT/out/Q07_confluence_cells.csv deep70+mom6+tierA w_cyan H52 micro red band: n 48, names 32, edge +193.5 [92.0, 328.9], q_fam 0.00628, CONFIRMED; px pool 152.62 CONFIRMED",
    "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  ],
  "flags": [
    "md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_q07w_c52_mi_deep70_mom6_tierA` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_q07w_c52_mi_deep70_mom6_tierA` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- The config row for this id exists in `packages/grokbot/rl64/lz_engine/config/sleeves.json` with the entry, exit and sizing values in Configuration, and does not exist in the other two sleeves.json files searched.
- No SPECS entry for this id exists in `desk3/lazarus_q07.py` or `desk3/q07_engine.py` (this is the INCOMPLETE-CODE finding, not a behaviour to verify by running).
- Any future executable implementation must reproduce: fear_day entry within 5 sessions, no-chase 1.02, stock_red and qqq_red true, the named filters failing closed, the 15% disaster stop, and the 52-week time exit.
