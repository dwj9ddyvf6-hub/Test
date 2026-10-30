# s_q07w_g52_sm_cheap5_tierA: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`; local census copy `research_notes/sleeve-census-20261029/accounting.json`): this canonical id is an UNRESOLVED singleton: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description" The same cell is also carried as the alias `lz_s_q07w_g52_sm_cheap5_tierA` of the PARTIAL strategy entry "Q07 w_green H52 small cheap5+tierA (test)" (type trend following, family 1w, algorithm sources: md2 catalog entry/exit/strategy text; the single recorded gap is "sizing not recorded in any consulted source"; the accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources"). The sizing gap is closed by the rl64 config entry cited below, which is in this repo.
- Executable record in this repo: the cell's own entry (id `s_q07w_g52_sm_cheap5_tierA`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (164 entries; account TEST, broker_account TEST_MWJW, kind 1w, enabled true, state live), installed by `packages/grokbot/rl64/tools/install_rl64.py` (md2 RL64, 2026-10-24: the Research Lab Q07 price-family cells installed as paper sleeves, 1 slot x $1k each). The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; DISASTER_STOP 15.0 in that host; its scan resolves each config row through the Lazarus signals resolver, which for a TEST-account sleeve_feed row is the generic feed_lane over the composer fires). The signal and gate functions that host relies on are vendored in this repo at `sleeves/lazarus/vendor/lazarus/signals.py` (resolve / feed_lane / valid_fire) and `sleeves/lazarus/vendor/lazarus/gate.py` (fear_day / capped_limit / size), with the session calendar at `sleeves/lazarus/vendor/lazarus/cal.py`.
- No v3-native code carries this cell: none of `sleeves/s_q07w_g52_sm_cheap5_tierA.py`, `adapters3/s_q07w_g52_sm_cheap5_tierA.py`, `integration/s_q07w_g52_sm_cheap5_tierA_adapter.py`, `laz_sleeves/s_q07w_g52_sm_cheap5_tierA.py` exists in the fresh Test tree, there is no SPECS entry for `s_q07w_g52_sm_cheap5_tierA` or `lz_s_q07w_g52_sm_cheap5_tierA` in `desk3/lazarus_q07.py`, no spec in `desk3/q07_engine.py`, no roster row for this id in `config/sleeves.json`, and the row is absent from the other lz_engine config copy read directly (`packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, 100 entries). Its executable record is the rl64 config entry plus the md2 host and vendored Lazarus functions above.
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_green-H52-small-cheap5+tierA (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+tierA w_green H52 small red band: n 30, names 24, edge +184.3 [55.7, 344.9], q_fam 0.0322, CONFIRMED; px pool 37.951 CONFIRMED"
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  - Flag: "md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"
  - Status text on the entry: "ready (md2 RL64 2026-10-24, Trader t181u)".
- Code search record: fresh recursive tree of dwj9ddyvf6-hub/Test taken at batch start (b46_test_tree.txt in the run workspace), plus the run's stored recursive trees of dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna, were searched by filename for the canonical id and the q07/lazarus tokens; no file named for this id exists in any of the four repos, and no q07 or lazarus path exists in the Silicon, quant-research-backup or Midna trees. The contents of both lz_engine config copies in Test (rl64 and q07-1w-swing-lz), `desk3/lazarus_q07.py`, `desk3/q07_engine.py` and the Test roster `config/sleeves.json` were read directly from Test at batch start.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_green (Green) signal in the small cap band, restricted to fires carrying the cheap5+tierA confluence tag(s), bought only on a fear (red) day, held 52 weeks. It is a fire-consumer: it does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires. Recorded label: "Q07 w_green H52 small cheap5+tierA (test)".

## Full algorithm

Evaluation order, from the config entry and the recorded family rule (consolidated catalog section 4.1):

1. Signal: the composer emits a fire for this lane (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, producer "sleeve_feed composer (tracker ledger + alt-data tags)", lane `s_q07w_g52_sm_cheap5_tierA`) when a Tensor 1W w_green (Green) signal in the small cap band carries all of this cell's tags: cheap5, tierA.
2. Entry policy (config `entry` block, verbatim values): {"limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "max_delay_minutes": 65, "no_chase_mult": 1.02, "order": "capped_limit_day", "policy": "fear_day", "qqq_red": true, "stock_red": true, "window_sessions": 5}.
3. Entry gate mechanics, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day): buy only when QQQ < prior close AND the stock <= its prior close AND the stock <= 1.02 x fire close (the config's no_chase_mult), decided inside the afternoon window (close-40 .. close-10 minutes) of a session in the red window D+1..D+5 after the fire session (cal.red_window with window_sessions 5); nothing by D+5 -> skip (never a green-day buy); every unknown price -> wait, never a false trigger. The capped limit (gate.capped_limit): limit = live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry (config `exit` block, verbatim): {"hold_from": "fill", "hold_unit_kind": "1w", "max_bars": null, "plan_overrides": [], "rest": null, "rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "stop_pct": null}. The md2 host's exit_reason applies the plan's own stop when one is set and otherwise the 15% DISASTER_STOP, and the time exit on the plan's bar count; the price-family params row recorded on this entry states this cell's time exit precisely (see the research lines in Provenance).
6. Sizing (config `sizing` block, verbatim values): {"budget_usd": 1000, "cap_pct_of_dv20": 1.0, "global_slot_usd": 1000, "max_slots": 1, "min_dv20_usd": 100000, "min_slot_fraction": 0.9, "one_share_max_usd": null, "position_usd": 1000, "position_usd_by_class": {}}. The vendored gate.size applies them: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, the one-share rule (inactive here: one_share_max_usd is null), and the lane dollar budget shrink to the remaining budget when that is at least min_slot_fraction of the position.
7. Census algorithm record for the `lz_s_q07w_g52_sm_cheap5_tierA` alias entry (verbatim from the accounting; entry/exit/filter text, parameters empty in the record): {
 "entry": [
  "[lz_s_q07w_g52_sm_cheap5_tierA] {\"policy\": \"fear_day\", \"max_delay_minutes\": 65, \"limit_band_pct\": 5.0, \"limit_buffer_pct\": 1.0, \"window_sessions\": 5, \"no_chase_mult\": 1.02, \"stock_red\": true, \"qqq_red\": true, \"order\": \"capped_limit_day\"}"
 ],
 "exit": [
  "[lz_s_q07w_g52_sm_cheap5_tierA] {\"rule\": \"the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))\", \"hold_from\": \"fill\", \"hold_unit_kind\": \"1w\", \"stop_pct\": null, \"max_bars\": null, \"rest\": null, \"plan_overrides\": []}"
 ],
 "sizing": [],
 "filters": [
  "[lz_s_q07w_g52_sm_cheap5_tierA] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json"
 ],
 "parameters": {},
 "variant_axes": [],
 "status": "PARTIAL",
 "gaps": [
  "sizing not recorded in any consulted source"
 ],
 "sources": [
  "md2 catalog entry/exit/strategy text"
 ]
}
8. Gaps in the record, marked not filled: the accounting graded this cell PARTIAL under its lz_ alias (sizing gap, closed by the config entry above) and UNRESOLVED under this canonical id; the params row records "K 20" (the K parameter's role is not in the record).
- Corpus tag definitions recorded on the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. Cap-band dollar reading recorded in desk3/q07_engine.py: mi = market cap below $300,000,000; sm = $300,000,000 to $2,000,000,000; ml = $2,000,000,000 and above.

## Files in this repo

- This package: `docs/S_Q07W_G52_SM_CHEAP5_TIERA-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- The cell's executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_g52_sm_cheap5_tierA`)
- Installer that created these RL64 rows: `packages/grokbot/rl64/tools/install_rl64.py`; install evidence: `packages/grokbot/rl64/evidence/rl64_install.json`
- Host engine for Lazarus config sleeves: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Vendored Lazarus signal/gate/calendar functions the host relies on: `sleeves/lazarus/vendor/lazarus/signals.py`, `sleeves/lazarus/vendor/lazarus/gate.py`, `sleeves/lazarus/vendor/lazarus/cal.py`, `sleeves/lazarus/vendor/lazarus/data.py`
- The same section 4.1 family rule implemented as v3 engines (sibling cells only; neither carries this id): `desk3/lazarus_q07.py` and `desk3/q07_engine.py`, and the shared engine `engines/laz_sleeves/_common.py`
- Family algorithm doc for the stage-2 LZ enable: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Nothing was vendored for this package: all code and config relied on was already in Test.

## Configuration

- Canonical id `s_q07w_g52_sm_cheap5_tierA` = the rl64 config id itself (the md2 host's sleeve id for a config row is "lz_" + the config id, which is the accounting's `lz_s_q07w_g52_sm_cheap5_tierA` alias). Kind 1w (weekly). Family w_green (Green). Cap band small. Horizon 52 weeks. Filters: cheap5, tierA.
- Entry, exit and sizing blocks: as quoted verbatim in the Full algorithm section. Account TEST (paper), broker_account TEST_MWJW, enabled true, state live.
- Cadence/state: weekly signal cadence (kind 1w); state is the single open slot and its fill (hold is counted from the fill).

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_g52_sm_cheap5_tierA`.
- Alt-data tags on the fires (ctx_feats tags): tier, dv20, c_depth60, ret126, px_fire, wiki coverage/attention and insider buys, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ) and for the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test).
2. Take the entry id `s_q07w_g52_sm_cheap5_tierA` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
3. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`, LazarusSleeve), which reads an lz_engine config and the composer fires; `packages/grokbot/rl64/tools/install_rl64.py` documents how these rows were installed originally. The host's own pinned lz_engine copy is not in this repo; the rl64 config above is the in-repo copy of that config format, and the Lazarus signal/gate functions are vendored under `sleeves/lazarus/vendor/lazarus/`.
4. Feed the composer fire file (lane `s_q07w_g52_sm_cheap5_tierA`) and daily bars; entries follow the fear_day policy in the Full algorithm section, exits the 15% stop / 52-week time exit.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this cell was found in the fresh Test tree. Behavior checklist, from the recorded config and the vendored gate code:

- A fire missing any of this cell's tags (cheap5, tierA) produces no entry.
- An entry is attempted only on a fear day (QQQ below its prior close, the stock at or below its prior close, and the stock at or below 1.02 x the fire close) inside the afternoon decision window of a session D+1..D+5 after the fire, as a capped limit day order: limit = live ref x 1.01, capped by fire close x 1.05 and by the 1.02x no-chase cap.
- Exactly one position of $1,000 is opened (whole shares, dv20 cap and min_dv20_usd 100000 liquidity floor honoured); a second fire while the slot is occupied produces no entry.
- A position whose price falls 15% from its fill is exited by the disaster stop; any surviving position is exited at the 52-week time exit (per the params row recorded in Provenance: close of the last NYSE session <= D + 364 calendar days).
- Open items: this canonical id is UNRESOLVED in the ALL-SLEEVES accounting (see Provenance); the K 20 parameter's role is not in the record.
