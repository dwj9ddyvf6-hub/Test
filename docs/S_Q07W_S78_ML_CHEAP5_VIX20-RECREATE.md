# s_q07w_s78_ml_cheap5_vix20: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- UNRESOLVED note (accounting unresolved list): singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description. The plan for this canonical id likewise records unresolved true and algorithm grade FULL from the lz_engine config alone (entry/exit/sizing).
- No standalone sleeve module for this exact id was found in any searched repo; the executable record is the config entry under the generic host, as with the sibling Q07 cells.

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_swing H78 midlarge cheap5+stress_vix20 (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". The sizing gap is closed by the rl64 config entry cited below, which is in this repo.
- Executable record in this repo: the cell's own entry (id `s_q07w_s78_ml_cheap5_vix20`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (164 entries; account TEST, kind 1w, enabled true, state live), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24: the Research Lab Q07 price-family cells installed as paper sleeves, 1 slot x $1k each, fires emitted by the composer via the generic sleeve_q07.cell_hits path). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id; DISASTER_STOP 15.0 in that host).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H78-midlarge-cheap5+stress_vix20 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 546 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+stress_vix20 w_swing H78 midlarge red band: n 45, names 17, edge +79.6 [24.3, 167.6], q_fam 0.0495, CONFIRMED; px pool n/a UNPROVEN (n<10)"
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4609 entries, plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21337 entries; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47379 entries; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7855 entries; no path named for this id). Desk source /home/hatch/workspace/muse-desk-v3 was also read for the v3 engines named below.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (swing) signal in the midlarge cap band, restricted to fires carrying the cheap5 + stress_vix20 confluence tags, bought only on a fear (red) day, held 78 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires.

## Full algorithm

Evaluation order, from the config entry and the recorded family rule:
1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_swing (swing) signal in the midlarge cap band carries all of this cell's tags: cheap5 + stress_vix20.
2. Entry policy (config): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130; the md2 Lazarus host holds DISASTER_STOP = 15.0), or the time exit at hold = 78 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 546 calendar days). hold_from = fill, hold_unit_kind = 1w, no plan overrides.
6. Tag definitions recorded in the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. stress_vix20 is the VIX >= 20 stress gate (the vix20 reading used by the v3 Q07 engines in this repo).
7. Gaps: the exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are not in the record beyond the entry-policy fields above.

## Files in this repo

- This package: `docs/S_Q07W_S78_ML_CHEAP5_VIX20-RECREATE.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_s78_ml_cheap5_vix20`)
- Installer: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- The same family rule implemented as v3 engines: `desk3/lazarus_q07.py` and `desk3/q07_engine.py`, and `laz_sleeves/_common.py` q07_evaluate in `engines/laz_sleeves/_common.py`
- Family algorithm doc: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`

## Configuration

- Config id `s_q07w_s78_ml_cheap5_vix20`; kind 1w (weekly). Family w_swing (swing). Cap band midlarge. Horizon 78 weeks. Filters: cheap5 + stress_vix20.
- Sizing (rl64 config entry): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper), broker TEST_MWJW. enabled true, state live.
- Status text: "ready (md2 RL64 2026-10-24, Trader t181u)".

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_s78_ml_cheap5_vix20`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, VIX, insider buys, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test).
2. Take the entry id `s_q07w_s78_ml_cheap5_vix20` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`, LazarusSleeve), which reads the lz_engine config and the composer fires.
4. Feed the composer fire file (lane `s_q07w_s78_ml_cheap5_vix20`) and daily bars; entries follow the fear_day policy, exits the 15% stop / 78-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in Test. Behaviour checklist:
- A fire missing any of this cell's tags (cheap5 + stress_vix20) produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 78-week time exit (close of the last NYSE session <= D + 546 calendar days).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
