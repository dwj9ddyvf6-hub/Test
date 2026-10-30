# s_q07w_g52_ml_cheap5: Recreation Package
Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_g52_ml_cheap5", type trend following, family unrecorded, no description recorded. Algorithm grade FULL in the accounting, sourced solely from the lz_engine config (entry/exit/sizing quoted in the Full algorithm and Configuration sections). No Test catalog entry in the accounting (test_entries empty). Alias record: `s_q07w_g52_ml_cheap5` itself, source md2_lz_engine, status live. The accounting flags this strategy UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description".
- The lz_engine config row for this id IS in Test, at `packages/grokbot/rl64/lz_engine/config/sleeves.json` (row id `s_q07w_g52_ml_cheap5`, label "Q07 w_green H52 midlarge cheap5 (test)", account TEST, kind 1w, enabled true, state live, status_text "ready (md2 RL64 2026-10-24, Trader t181u)"). Its entry, exit and sizing blocks are quoted verbatim in the Full algorithm section, and its research rows are quoted in Provenance below.
- INCOMPLETE-CODE: no code that runs this lane was found in any GitHub repo searched. Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b26_*_tree.txt in the run workspace) and searched by filename for this id; no sleeve, adapter or engine file named for this id exists in any of the four trees. In Test specifically: there is no `sleeves/s_q07w_g52_ml_cheap5.py`, `adapters3/s_q07w_g52_ml_cheap5.py`, `integration/s_q07w_g52_ml_cheap5_adapter.py` or `laz_sleeves/s_q07w_g52_ml_cheap5.py`; the id has no SPECS entry in `desk3/lazarus_q07.py`; and `desk3/q07_engine.py` (a different Q07 engine in Test, for the Lazarus batch-6 lanes) carries no spec for this id and does not implement the tierA filter token at all, so it is not claimed as this lane's code. The engine that consumed the rl64 lz_engine config on the original desk is not in any searched repo. Nothing was vendored.

Research rows recorded on the config row in Test:

- `DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_green-H52-midlarge-cheap5 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))`
- `CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5 w_green H52 midlarge red band: n 33, names 21, edge +23.2 [9.0, 37.2], q_fam 0.00897, CONFIRMED; px pool 10.362 UNPROVEN (positive n.s., below realisti`
- `CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)`

## What this strategy is

A Research Lab Q07 weekly (1W) Tensor confluence cell: the green family, midlarge cap band, 52-week horizon, with the fire filters cheap5 (label: "Q07 w_green H52 midlarge cheap5 (test)"). It consumes sleeve-feed fires and, per its config, buys one $1,000 slot on a fear day under a capped limit order, exiting on the fire plan's 15% disaster stop or at the 52-week time exit. The config's own flag row records: "Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)".

## Full algorithm

Everything the record holds, from the config row in Test (`packages/grokbot/rl64/lz_engine/config/sleeves.json`). Where the record does not define a term, that is stated rather than filled in.

Filter definitions recorded on the config row's research rows (from `CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly`, as quoted there):

- cheap5 = px_fire < 5 (fire price below $5)

Entry (config `entry` block, verbatim values):

- policy: "fear_day"
- max_delay_minutes: 65
- limit_band_pct: 5.0
- limit_buffer_pct: 1.0
- window_sessions: 5 (the fire must be acted on within 5 sessions)
- no_chase_mult: 1.02
- stock_red: true
- qqq_red: true
- order: "capped_limit_day"

The mechanics behind the fear_day policy name, the limit band/buffer and the no-chase multiplier are not in the record; only the parameter values above are. The research rows record the cell's entry side as "entry red (Q07 'red')" and the params row records "K 20" (the K parameter's role is not in the record).

Exit (config `exit` block, verbatim):

- rule: "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))"
- hold_from: "fill"
- hold_unit_kind: "1w"
- stop_pct: null; max_bars: null; rest: null; plan_overrides: []
- The research params row records the time exit precisely as: exit at the close of the last NYSE session on or before D + 364 calendar days, where D is the fire date.

Sizing (config `sizing` block, verbatim values):

- budget_usd: 1000; max_slots: 1; position_usd: 1000; position_usd_by_class: {}; one_share_max_usd: null; cap_pct_of_dv20: 1.0; min_slot_fraction: 0.9; global_slot_usd: 1000; min_dv20_usd: 100000

Signal source (config `source` block): producer "sleeve_feed composer (tracker ledger + alt-data tags)", file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, lane `s_q07w_g52_ml_cheap5`.

## Files in this repo

- This package: `docs/S_Q07W_G52_ML_CHEAP5-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json`, row `s_q07w_g52_ml_cheap5` (the second lz_engine config in Test, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, was also checked and does not contain this id)
- Related but NOT this lane's code: `desk3/q07_engine.py` and `desk3/lazarus_q07.py` (Q07 engines in Test for other lanes; neither carries this id)
- Code for this lane: none found in any searched GitHub repo (see the INCOMPLETE-CODE search record in Provenance). Nothing was vendored.

## Configuration

- As recorded on the config row: id `s_q07w_g52_ml_cheap5`; account TEST; kind 1w; label "Q07 w_green H52 midlarge cheap5 (test)"; enabled true; state live.
- Entry, exit and sizing blocks: as quoted verbatim in the Full algorithm section.
- Universe: Q07 weekly fires in the green family and the midlarge cap band passing the filters cheap5; timeframe 1w fires. Asset class and cadence beyond the config: not in the record.

## Data inputs

- The sleeve_feed composer file `shadow/paper_sleeve/live/sleeve_fires_v1.json` (tracker ledger + alt-data tags), per the config `source` block.
- The filter inputs named in the recorded definitions: fire price, 60-session depth (c_depth60), 126-session return, the no-liquidity tier tag and 20-day dollar volume, and (for vix20 lanes) the stress_vix20 input, whose source is not in the record.
- Positions and fills for the hold/stop management: the record names the fire's plan and the desk weekly time exit; no further input list is in the record.

## Install and run

1. Clone the Test repo.
2. This package is INCOMPLETE-CODE: the engine that ran this lane is not in this repo or any searched GitHub repo, so a faithful install is not possible from the record alone. Do not substitute `desk3/q07_engine.py` or `desk3/lazarus_q07.py`: neither carries this id, and the former does not implement the tierA token.
3. What can be installed exactly is the configuration: copy the row for `s_q07w_g52_ml_cheap5` from `packages/grokbot/rl64/lz_engine/config/sleeves.json` into an lz_engine-compatible desk's sleeve config unchanged.
4. Supply the sleeve_feed composer output at `shadow/paper_sleeve/live/sleeve_fires_v1.json` with this lane's fires and alt-data tags.
5. An lz_engine implementation honouring the entry/exit/sizing blocks quoted in the Full algorithm section (fear_day policy, capped_limit_day order, 5-session window, 15% disaster stop, 52-week time exit at the close of the last NYSE session on or before D + 364 days) is required before any run; that implementation is not in the record.
6. Verify any candidate implementation against the Verification checklist before any live use.

## Verification

No test file for this lane was found in the fresh Test tree. Behaviour checklist from the recorded config:

- Entries only under the fear_day policy with stock_red and qqq_red both true, within 5 sessions of the fire and 65 minutes maximum delay, as a capped_limit_day order with limit_band_pct 5.0, limit_buffer_pct 1.0 and no_chase_mult 1.02.
- A fire passes only if every named filter passes under the recorded definitions: cheap5.
- Sizing is exactly one slot of $1,000 (budget_usd 1000, max_slots 1, position_usd 1000), with cap_pct_of_dv20 1.0, min_slot_fraction 0.9 and min_dv20_usd 100000 honoured.
- Exit fires on the 15% disaster stop, or at the 52-week time exit: the close of the last NYSE session on or before D + 364 calendar days, hold counted from the fill in 1-week units.
- Open items: the fear_day mechanics, the K 20 parameter's role are not in the record, and the lane stays UNRESOLVED in the accounting until a sleeve module docstring or catalog description for this id is found.
