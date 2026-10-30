# s_q07w_g52_ml_cheap5: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_g52_ml_cheap5" (no separate strategy description is recorded in the consulted sources), type trend following, family unrecorded; universe, asset class, timeframe and creator "not recorded in consulted sources". Algorithm grade FULL in the accounting, sourced from a single source: the lz_engine config (entry/exit/sizing) quoted in the Full algorithm. Alias status: live (md2_lz_engine). The accounting marks the entry UNRESOLVED ("singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description"); no Test catalog entry and no sleeve module for this id exists, so this package is graded unresolved_built and holds the best evidence on file: the cell's own executable config entry in Test, below.
- Executable record in this repo: the cell's own entry (id `s_q07w_g52_ml_cheap5`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (164 entries; account TEST, broker_account TEST_MWJW, kind 1w, enabled true, state live, label "Q07 w_green H52 midlarge cheap5 (test)"), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24: the Research Lab Q07 price-family cells installed as paper sleeves, 1 slot x $1k each, fires emitted by the composer via the generic sleeve_q07.cell_hits path). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id; DISASTER_STOP 15.0 in that host).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_green-H52-midlarge-cheap5 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5 w_green H52 midlarge red band: n 33, names 21, edge +23.2 [9.0, 37.2], q_fam 0.00897, CONFIRMED; px pool 10.362 UNPROVEN (positive n.s., below realisti"
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  - Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)"; flag on the entry: "md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)".
- Code search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start and searched by filename for the canonical id, its aliases and its distinguishing tokens; the contents of the Test files named in this package were read from GitHub. Every fact below names the repo and path it came from (all paths are in Test unless stated). Specifically: no sleeve, adapter or integration file named for this id exists in Test (the Test tree holds s_q07w files only for other cells); the Silicon, quant-research-backup and Midna trees contain no file named for this id and no lz_engine config at all. The second lz_engine config in Test, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, does not contain this id (it holds the cyan/small and other bands, not this midlarge green cell).

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_green (Green) signal in the midlarge cap band, restricted to fires carrying the cheap5 confluence tags, bought only on a fear (red) day, held 52 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires. The accounting lists this unprefixed id as a separate unresolved singleton even though its algorithm record is FULL from the config below.

## Full algorithm

Evaluation order, from the config entry in Test and the recorded family rule:

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_green (Green) signal in the midlarge cap band carries all of this cell's tags: cheap5. Tag definitions recorded on the config entry (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands; cap bands are PIT SEC bands. This cell's only tag is cheap5 (px_fire < 5).
2. Entry policy (config entry verbatim): {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}. Both the stock and QQQ must be red on the entry day.
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x (no_chase_mult) and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied. Sizing (config entry verbatim): {"budget_usd": 1000, "max_slots": 1, "position_usd": 1000, "position_usd_by_class": {}, "one_share_max_usd": null, "cap_pct_of_dv20": 1.0, "min_slot_fraction": 0.9, "global_slot_usd": 1000, "min_dv20_usd": 100000}.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130; the md2 Lazarus host holds DISASTER_STOP = 15.0), or the time exit at hold = 52 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 364 calendar days). Config exit fields: hold_from = fill, hold_unit_kind = 1w, stop_pct null, max_bars null, plan_overrides [].
6. Gaps in the record, marked not filled: the exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are not in the record beyond the entry-policy fields above; the accounting's own description/universe/asset-class fields for this id are not in the record (the label and config entry above are the record).

## Files in this repo

- This package: `docs/S_Q07W_G52_ML_CHEAP5-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_g52_ml_cheap5`)
- Installer that created these RL64 rows: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- The same family rule implemented as v3 engines (sibling cells): `desk3/lazarus_q07.py` and `desk3/q07_engine.py`
- Family algorithm doc for the stage-2 LZ enable: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Nothing was vendored: the config entry and host were already in Test, and no code file for this cell exists in any searched repo.

## Configuration

- Config id `s_q07w_g52_ml_cheap5`; the md2 host's sleeve id is `lz_s_q07w_g52_ml_cheap5`. Kind 1w (weekly). Family green (w_green). Cap band midlarge. Horizon 52 weeks. Filters: cheap5.
- Sizing (rl64 config entry): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper), broker_account TEST_MWJW. enabled true, state live.
- Cadence/state: weekly signal cadence (kind 1w); state is the single open slot and its fill (hold is counted from the fill).

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_g52_ml_cheap5`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, VIX, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test).
2. Take the entry id `s_q07w_g52_ml_cheap5` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`, LazarusSleeve), which reads the lz_engine config and the composer fires; `packages/grokbot/rl64/tools/install_rl64.py` documents how these rows were installed originally.
4. Feed the composer fire file (lane `s_q07w_g52_ml_cheap5`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 52-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in Test. Behavior checklist, from the algorithm section:

- A fire missing any of this cell's tags (cheap5) produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 52-week time exit (close of the last NYSE session <= D + 364 calendar days).
- Open item: the ALL-SLEEVES accounting still lists this id as an unresolved singleton; this package does not change that status.
