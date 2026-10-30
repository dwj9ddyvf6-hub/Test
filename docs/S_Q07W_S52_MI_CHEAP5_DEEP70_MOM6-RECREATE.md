# s_q07w_s52_mi_cheap5_deep70_mom6 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_s52_mi_cheap5_deep70_mom6", type trend following, algorithm grade FULL from the lz_engine config (entry/exit/sizing), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Status history: live (md2_lz_engine). Classification evidence on the accounting entry: "Classification 2026-10-30: other (config evidence): lz_engine config in accounting shows only a fear_day capped-limit execution policy and a weekly time exit; the cell signal comes from upstream sleeve_feed Tensor and alt-data fires whose rule is not recorded for this cell, and its factor tags (cheap, deep, momentum, wiki, insider) mix mechanisms Repair 2026-10-30 per CLASSIFY-VERIFY D6"
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_q07w_s52_mi_cheap5_deep70_mom6`, label "Q07 w_swing H52 micro cheap5+deep70+mom6 (test)", kind 1w, enabled True, state live, account TEST, broker_account TEST_MWJW. Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)". Flags: ["md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"]
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H52-micro-cheap5+deep70+mom6 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+deep70+mom6 w_swing H52 micro red band: n 1177, names 337, edge +58.9 [40.9, 79.1], q_fam 7.76e-07, CONFIRMED; px pool 5.8836 UNPROVEN (positive n.s., "
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `packages/grokbot/rl64/lz_engine/config/sleeves.json` where this id's row was found, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, `config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`, all searched by content: this id is NOT present in those three files; plus `desk3/lazarus_q07.py` and `desk3/q07_engine.py` searched by content: no SPECS / evaluate entry for this exact id in either); dwj9ddyvf6-hub/Silicon (recursive tree; no path for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path for this id); dwj9ddyvf6-hub/Midna (recursive tree; no path for this id). No standalone sleeve module, adapter or integration file named for this exact id exists in any searched repo. Because no executable spec for this id exists in the desk3 Q07 engines, this package is graded INCOMPLETE-CODE.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (Swing) signal in the micro cap band, restricted to fires carrying the cheap5 + deep70 + mom6 confluence tags, bought only on a fear (red) day, held 52 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires. Accounting description: "No strategy description recorded in consulted sources." (no strategy description recorded in consulted sources). Grade note: the accounting grades the algorithm FULL from the config, but the executable-code bar (R2) is not met for this exact id, hence INCOMPLETE-CODE here.

## Full algorithm

Evaluation order, from the config entry and the recorded family rule:

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)") when a Tensor 1W w_swing (Swing) signal in the micro cap band carries all of this cell's tags: cheap5 + deep70 + mom6.
2. Entry policy (config, verbatim values): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
3. Entry window: the buy must occur within 5 sessions of the signal and at most 65 minutes after the fear-day trigger; the capped limit day order may not chase above 1.02x (no_chase_mult) and is capped by the 5.0% limit band with a 1.0% buffer.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130), or the time exit at hold = 52 weeks (calendar weeks after the fire week, desk weekly time exit; the price-family params record the exit as the close of the last NYSE session <= D + 364 calendar days). hold_from = fill, hold_unit_kind = 1w, stop_pct null in the config entry (the 15% stop lives in the fire's plan text), max_bars null, no plan overrides.
6. Tag definitions: Corpus tag definitions recorded on every config entry (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. The v3 Q07 engines in this repo (`desk3/q07_engine.py`, `desk3/lazarus_q07.py`) read the same tokens as: cheap5 = last close < $5, deep70 = close at or below 70% of the trailing 252-session high, mom6 = positive 6-month momentum over 126 sessions; where the corpus definition and the v3 reading differ, the corpus definition recorded on this cell's config entry is this cell's record. Host family rule (catalog section 4.1, as coded for sibling cells in `desk3/lazarus_q07.py`): take the Tensor 1W signal of the named family in the named cap band, apply the named alt-data filters (a filter with no evidence fails closed), buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the time horizon in the cell name. That host code contains SPECS for sibling w_swing / swing cells (for example wcov and ins2 variants) but NO spec for this exact id.
7. Sizing (config, verbatim values): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.
8. Gap: no executable spec for this id in `desk3/lazarus_q07.py` SPECS or `desk3/q07_engine.py`, and no standalone sleeve module in any searched repo: not in the record (code). Do not run this cell from the desk3 engines as if it were registered there. The exact intraday mechanics of the fear_day trigger inside the original Lazarus engine are also not in the record beyond the entry-policy fields above.

## Files in this repo

- This package: `docs/S_Q07W_S52_MI_CHEAP5_DEEP70_MOM6-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id. This row is NOT present in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, `config/sleeves.json` or `sleeves/lazarus/vendor/lazarus/sleeves.json` (searched by content).
- Host family code (already in Test, but with no spec for this id): `desk3/lazarus_q07.py` (SPECS table has no entry for this id) and `desk3/q07_engine.py` (its cap-band table defines the bands, but its evaluate path has no entry for this id).
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`; installer: `packages/grokbot/rl64/tools/install_rl64.py`.
- Family algorithm doc: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

Full lz_engine config row for `s_q07w_s52_mi_cheap5_deep70_mom6` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
 "id": "s_q07w_s52_mi_cheap5_deep70_mom6",
 "account": "TEST",
 "broker_account": "TEST_MWJW",
 "kind": "1w",
 "label": "Q07 w_swing H52 micro cheap5+deep70+mom6 (test)",
 "enabled": true,
 "state": "live",
 "status_text": "ready (md2 RL64 2026-10-24, Trader t181u)",
 "source": {
  "producer": "sleeve_feed composer (tracker ledger + alt-data tags)",
  "file": "shadow/paper_sleeve/live/sleeve_fires_v1.json",
  "lane": "s_q07w_s52_mi_cheap5_deep70_mom6"
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
  "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H52-micro-cheap5+deep70+mom6 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))",
  "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+deep70+mom6 w_swing H52 micro red band: n 1177, names 337, edge +58.9 [40.9, 79.1], q_fam 7.76e-07, CONFIRMED; px pool 5.8836 UNPROVEN (positive n.s., ",
  "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
 ],
 "flags": [
  "md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"
 ]
}
```

- Canonical id `s_q07w_s52_mi_cheap5_deep70_mom6` (config id; the md2 host's sleeve id is "lz_" + this id). Kind 1w (weekly). Family w_swing (Swing). Cap band micro. Horizon 52 weeks. Tags: cheap5 + deep70 + mom6.
- Account TEST (paper), broker_account TEST_MWJW per the config entry. enabled true, state live.

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_s52_mi_cheap5_deep70_mom6`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the UNRESOLVED accounting entry for `s_q07w_s52_mi_cheap5_deep70_mom6` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_q07w_s52_mi_cheap5_deep70_mom6` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and confirm the entry, exit and sizing values match Configuration. Note the INCOMPLETE-CODE grade: there is no executable spec for this id in `desk3/lazarus_q07.py` or `desk3/q07_engine.py`, so the desk3 engines cannot run this cell as registered; the original run path was the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`) reading the lz_engine config and the composer fires.
4. If running under that host, feed the composer fire file (lane `s_q07w_s52_mi_cheap5_deep70_mom6`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 52-week time exit.
5. Verify against the Verification section before treating any recreation as faithful.

## Verification

- The config row for this id exists in `packages/grokbot/rl64/lz_engine/config/sleeves.json` with the entry, exit and sizing values in Configuration, and does not exist in the other three sleeves.json files searched.
- No SPECS entry for this id exists in `desk3/lazarus_q07.py` or `desk3/q07_engine.py` (this is the INCOMPLETE-CODE finding, not a behaviour to verify by running).
- Behaviour checklist if a spec is later written from the config record: a fire missing any of this cell's tags (cheap5 + deep70 + mom6) produces no entry; an entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the signal and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x; exactly one position of $1,000 is opened; a position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 52-week time exit (close of the last NYSE session <= D + 364 calendar days).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
