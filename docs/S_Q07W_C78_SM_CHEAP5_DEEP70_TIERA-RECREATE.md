# s_q07w_c78_sm_cheap5_deep70_tierA - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_c78_sm_cheap5_deep70_tierA", type trend following, algorithm grade FULL from the lz_engine config (entry/exit/sizing), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Status history: live (md2_lz_engine). Classification evidence on the accounting entry: "Classification 2026-10-30: forecast and ML models (code evidence): muse-desk-v3 desk3/q07_engine.py and desk3/lazarus_q07.py read: Tensor 1W signal of the named family plus alt-data filters, buy on a QQQ-down day, 15% stop or horizon exit; a model signal, not a price-only rule Repair 2026-10-30 per CLASSIFY-VERIFY D5"
- Executable record in this repo: this cell's own entry (id `s_q07w_c78_sm_cheap5_deep70_tierA`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, kind 1w, enabled true, state live, label "Q07 w_cyan H78 small cheap5+deep70+tierA (test)"), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (its sleeve id is "lz_" + the config id).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_cyan-H78-small-cheap5+deep70+tierA (CONFIRMED; K 20; exit: close of last NYSE session <= D + 546 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+deep70+tierA w_cyan H78 small red band: n 42, names 22, edge +136.3 [83.5, 196.6], q_fam 0.000162, CONFIRMED; px pool 108.37 CONFIRMED"
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  - Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)". Flags: ["md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"]
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus the file reads named here: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry for this id, `desk3/q07_engine.py`, `desk3/lazarus_q07.py`, `config/sleeves.json`); dwj9ddyvf6-hub/Silicon (recursive tree; no q07 path for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no q07 path for this id); dwj9ddyvf6-hub/Midna (recursive tree; no q07 code for this id). No standalone sleeve module for this exact id exists in Test (no `sleeves/s_q07w_c78_sm_cheap5_deep70_tierA.py`, adapter or integration file); the running code is the config-driven host plus the config entry. Code found in Test already, so nothing was vendored.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_cyan (Cyan) signal in the small cap band, restricted to fires carrying the cheap5 + deep70 + tierA confluence tags, bought only on a fear (red) day, held 78 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires. Accounting description: "No strategy description recorded in consulted sources." (no strategy description recorded in consulted sources).

## Full algorithm

Evaluation order, from the config entry and the recorded family rule:

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_cyan (Cyan) signal in the small cap band carries all of this cell's tags: cheap5 + deep70 + tierA.
2. Entry policy (config, verbatim values): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x (no_chase_mult) and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130), or the time exit at hold = 78 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 546 calendar days). hold_from = fill, hold_unit_kind = 1w, stop_pct null in the config entry (the 15% stop lives in the fire's plan text), max_bars null, no plan overrides.
6. Tag definitions: Corpus tag definitions recorded on every config entry (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. The v3 Q07 engines in this repo (`desk3/q07_engine.py`, `desk3/lazarus_q07.py`) read the same tokens as: cheap5 = last close < $5, deep70 = close at or below 70% of the trailing 252-session high, mom6 = positive 6-month momentum over 126 sessions; where the corpus definition and the v3 reading differ, the corpus definition recorded on this cell's config entry is this cell's record.
7. Sizing (config, verbatim values): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.
8. Gap in the record, marked not filled: the exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are not in the record beyond the entry-policy fields above, and the accounting's UNRESOLVED note above stands.

## Files in this repo

- This package: `docs/S_Q07W_C78_SM_CHEAP5_DEEP70_TIERA-RECREATE.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_c78_sm_cheap5_deep70_tierA`)
- Installer that created these RL64 rows: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- The same section 4.1 family rule implemented as v3 engines (sibling cells): `desk3/lazarus_q07.py` and `desk3/q07_engine.py`
- Family algorithm doc: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `s_q07w_c78_sm_cheap5_deep70_tierA` (config id; the md2 host's sleeve id is "lz_" + this id). Kind 1w (weekly). Family w_cyan (Cyan). Cap band small. Horizon 78 weeks. Tags: cheap5 + deep70 + tierA.
- Entry/exit/sizing: exactly the values in the Full algorithm section (steps 2, 5 and 7), taken verbatim from this cell's config entry in `packages/grokbot/rl64/lz_engine/config/sleeves.json`.
- Account TEST (paper), broker_account TEST_MWJW per the config entry. enabled true, state live.
- Cadence/state: weekly signal cadence (kind 1w); state is the single open slot and its fill (hold is counted from the fill).

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_c78_sm_cheap5_deep70_tierA`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Take the entry id `s_q07w_c78_sm_cheap5_deep70_tierA` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`), which reads the lz_engine config and the composer fires; `packages/grokbot/rl64/tools/install_rl64.py` documents how these rows were installed originally.
4. Feed the composer fire file (lane `s_q07w_c78_sm_cheap5_deep70_tierA`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 78-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in Test. Behaviour checklist, from the algorithm section:

- A fire missing any of this cell's tags (cheap5 + deep70 + tierA) produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 78-week time exit (close of the last NYSE session <= D + 546 calendar days).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
