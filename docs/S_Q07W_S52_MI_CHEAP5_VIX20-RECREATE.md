# s_q07w_s52_mi_cheap5_vix20: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_s52_mi_cheap5_vix20", type trend following, algorithm grade FULL from the lz_engine config (entry/exit/sizing), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Status history: live (md2_lz_engine).
- Executable record in this repo: this cell's own entry (id `s_q07w_s52_mi_cheap5_vix20`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, kind 1w, enabled true, state live, label "Q07 w_swing H52 micro cheap5+stress_vix20 (test)"), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (its sleeve id is "lz_" + the config id; the same cell therefore also appears in this repo under the lz_-prefixed recreation packages built for those canonical ids).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H52-micro-cheap5+stress_vix20 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+stress_vix20 w_swing H52 micro red band: n 1436, names 400, edge +56.6 [41.0, 71.7], q_fam 5.45e-09, CONFIRMED; px pool -26.71 UNPROVEN (negative, unde...) (truncated in the source entry)"
  - Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)".
- Code search record: Test tree at batch start (sleeves/, adapters3/, integration/, desk3/, packages/, docs/) was searched for the canonical id; the cell's config entry and host above were found in Test. Silicon tree, quant-research-backup tree and Midna tree were also searched for the canonical id: no code file for this cell was found in those repos. No standalone sleeve module for this exact id exists in Test (no `sleeves/s_q07w_s52_mi_cheap5_vix20.py`, adapter or integration file); the running code is the config-driven host plus the config entry.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (Swing) signal in the micro cap band, restricted to fires carrying the cheap5 + stress_vix20 confluence tags, bought only on a fear (red) day, held 52 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires.

## Full algorithm

Evaluation order, from the config entry and the recorded family rule:

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_swing (Swing) signal in the micro cap band carries all of this cell's tags: cheap5 + stress_vix20.
2. Entry policy (config): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x (no_chase_mult) and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130; the md2 Lazarus host holds DISASTER_STOP = 15.0), or the time exit at hold = 52 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 364 calendar days). hold_from = fill, hold_unit_kind = 1w, no plan overrides.
6. Tag definitions: Corpus tag definitions recorded on every config entry (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. stress_vix20 is the VIX >= 20 stress gate (the vix20 reading used by both v3 Q07 engines in this repo: `desk3/q07_engine.py` and `desk3/lazarus_q07.py`, where vix20 = VIX >= 20, cheap5 = last close < $5, deep70 = close at or below 70% of the trailing 252-session high, mom6 = positive 6-month momentum over 126 sessions).
7. Gap in the record, marked not filled: the exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are not in the record beyond the entry-policy fields above, and the accounting's UNRESOLVED note above stands.

## Files in this repo

- This package: `docs/S_Q07W_S52_MI_CHEAP5_VIX20-RECREATE.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_s52_mi_cheap5_vix20`)
- Installer that created these RL64 rows: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- The same section 4.1 family rule implemented as v3 engines (sibling cells): `desk3/lazarus_q07.py` and `desk3/q07_engine.py`
- Family algorithm doc: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `s_q07w_s52_mi_cheap5_vix20` (config id; the md2 host's sleeve id is "lz_" + this id). Kind 1w (weekly). Family w_swing (Swing). Cap band micro. Horizon 52 weeks. Tags: cheap5 + stress_vix20.
- Sizing (config entry): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper). enabled true, state live.
- Cadence/state: weekly signal cadence (kind 1w); state is the single open slot and its fill (hold is counted from the fill).

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_s52_mi_cheap5_vix20`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, VIX, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test).
2. Take the entry id `s_q07w_s52_mi_cheap5_vix20` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`), which reads the lz_engine config and the composer fires; `packages/grokbot/rl64/tools/install_rl64.py` documents how these rows were installed originally.
4. Feed the composer fire file (lane `s_q07w_s52_mi_cheap5_vix20`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 52-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in Test. Behaviour checklist, from the algorithm section:

- A fire missing any of this cell's tags (cheap5 + stress_vix20) produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 52-week time exit (close of the last NYSE session <= D + 364 calendar days).
