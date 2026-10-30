# lz_s_q07w_g78_mi_cheap5_deep70_vix20: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_green H78 micro cheap5+deep70+stress_vix20 (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". The sizing gap is closed by the rl64 config entry cited below, which is in this repo.
- Executable record in this repo: the cell's own entry (id `s_q07w_g78_mi_cheap5_deep70_vix20`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (164 entries; account TEST, kind 1w, enabled true, state live), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24: the Research Lab Q07 price-family cells installed as paper sleeves, 1 slot x $1k each, fires emitted by the composer via the generic sleeve_q07.cell_hits path). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id, which is where this canonical id's lz_ prefix comes from; DISASTER_STOP 15.0 in that host).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_green-H78-micro-cheap5+deep70+stress_vix20 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 546 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+deep70+stress_vix20 w_green H78 micro red band: n 96, names 86, edge +110.0 [77.4, 151.7], q_fam 3.77e-06, CONFIRMED; px pool 10.417 UNPROVEN (positive...)" (truncated in the source entry)
  - Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)".
- Code search record: Searched for code: Test tree at batch start (sleeves/, adapters3/, integration/, desk3/, packages/, docs/) and the contents of packages/grokbot/rl64/lz_engine/config/sleeves.json and packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json; Silicon tree (research/, desk trees), quant-research-backup tree and Midna tree were also grepped for the canonical id and the unprefixed id: no code file for this cell was found in those repos.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_green (Green) signal in the micro cap band, restricted to fires carrying the cheap5 + deep70 + stress_vix20 confluence tags, bought only on a fear (red) day, held 78 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires.

## Full algorithm

Evaluation order, from the config entry and the recorded family rule:

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_green (Green) signal in the micro cap band carries all of this cell's tags: cheap5 + deep70 + stress_vix20.
- Entry policy (config): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x (no_chase_mult) and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130; the md2 Lazarus host holds DISASTER_STOP = 15.0), or the time exit at hold = 78 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 546 calendar days). hold_from = fill, hold_unit_kind = 1w, no plan overrides.
6. Gaps in the record, marked not filled: the accounting graded this algorithm PARTIAL (sizing gap, closed by the config entry above); the exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are not in the record beyond the entry-policy fields above.
- Corpus tag definitions recorded in the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. stress_vix20 is the VIX >= 20 stress gate (the vix20 reading used by both v3 Q07 engines in this repo); ins2 / insider2 = insider_buys >= 2 (the reading used by both v3 Q07 engines in this repo).

## Files in this repo

- This package: `docs/LZ_S_Q07W_G78_MI_CHEAP5_DEEP70_VIX20-RECREATE.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_g78_mi_cheap5_deep70_vix20`)
- Installer that created these RL64 rows: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- The same section 4.1 family rule implemented as v3 engines (sibling cells): `desk3/lazarus_q07.py` and `desk3/q07_engine.py`
- Family algorithm doc for the stage-2 LZ enable: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`

## Configuration

- Canonical id `lz_s_q07w_g78_mi_cheap5_deep70_vix20` = "lz_" + config id `s_q07w_g78_mi_cheap5_deep70_vix20`. Kind 1w (weekly). Family green. Cap band micro. Horizon 78 weeks. Filters: cheap5 + deep70 + stress_vix20.
- Sizing (rl64 config entry): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper). enabled true, state live.
- Cadence/state: weekly signal cadence (kind 1w); state is the single open slot and its fill (hold is counted from the fill).

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_g78_mi_cheap5_deep70_vix20`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, VIX, insider buys, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the broker-held 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test).
2. Take the entry id `s_q07w_g78_mi_cheap5_deep70_vix20` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`, LazarusSleeve), which reads the lz_engine config and the composer fires; `packages/grokbot/rl64/tools/install_rl64.py` documents how these rows were installed originally.
4. Feed the composer fire file (lane `s_q07w_g78_mi_cheap5_deep70_vix20`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 78-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in Test. Behavior checklist, from the algorithm section:

- A fire missing any of this cell's tags (cheap5 + deep70 + stress_vix20) produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 78-week time exit (close of the last NYSE session <= D + 546 calendar days).
