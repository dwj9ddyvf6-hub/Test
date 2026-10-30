# lz_s_q07w_s52_ml_deep70_wlow: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_swing H52 midlarge deep70+wiki_low (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". The sizing gap is closed twice over in this repo: by the rl64 config entry and by the v3 engine spec cited below.
- Config record in this repo: the cell's own entry (id `s_q07w_s52_ml_deep70_wlow`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, broker_account TEST_MWJW, kind 1w, enabled true, state live), also present in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and in the vendored lazarus-desk config `sleeves/lazarus/vendor/lazarus/sleeves.json`. The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id, which is where this canonical id's lz_ prefix comes from; DISASTER_STOP 15.0 in that host).
- Code in this repo (the v3 implementation, which is the truth for how the lane runs on the v3 desk): sleeve wrapper `sleeves/s_q07w_s52_ml_deep70_wlow.py` (copies at `adapters3/s_q07w_s52_ml_deep70_wlow.py` and `integration/s_q07w_s52_ml_deep70_wlow_adapter.py`), delegating to the shared fire-consumer engine `desk3/lazarus_q07.py`, whose SPECS entry for this id is: family "swing", band "midlarge", horizon_w 52, filters ("deep70", "wlow"), slots 1, budget 1000.0, parked True. The wrapper docstring records "Q07 Swing H52 midlarge deep70+wiki_low (CSV off)" and exposes PARAMS from the spec. Roster row in `config/sleeves.json` (and `engines/config/sleeves.json`): module adapters3.s_q07w_s52_ml_deep70_wlow, cadence_s 3600, session rth, slice capital/cash $1,000, bp_buffer_frac 0.02, flat_by_close false, inputs [fires, bars, positions], parked true, with the engine's producer list (sleeve_feed_composer 604800s, bars 3600s, broker_readback 3600s).
- Research evidence recorded on the rl64 config entry:
  - "DESK_INTEGRATION/EDGE_INVENTORY.csv Q07-w_swing-H52-midlarge-deep70+wiki_low (CONFIRMED; ADD paper-test ($1k) -> core candidate)"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv deep70+wiki_low w_swing H52 midlarge red band: n 209, names 49, edge +18.2 [10.1, 26.5], q_fam 0.0023, CONFIRMED"
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  - Flag: "staged off: staged-off: input missing"
  - Flag: "turned ON at cutover 2026-10-14 (was off)"
  - Flag: "md2 2026-10-24: enabled; the missing w_swing_fires_latest input is restored by the w_swing_heal job"
  - Status text on the entry: "md2 2026-10-24: ON (input = Research Lab w_swing feed, now present + healed; research CONFIRMED cells)".
- Code search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b33_Test_tree.txt, b33_Silicon_tree.txt, b33_quant-research-backup_tree.txt, b33_Midna_tree.txt in the run workspace; the quant-research-backup tree carries GitHub's own truncation note) and searched by filename for the canonical id, the unprefixed config id and the q07/lazarus tokens; the contents of the three lz_engine config copies in Test (rl64, q07-1w-swing-lz, and the vendored lazarus-desk config at sleeves/lazarus/vendor/lazarus/sleeves.json), desk3/lazarus_q07.py SPECS, desk3/q07_engine.py and the Test roster config/sleeves.json were read directly. No q07 or lazarus path exists in the Silicon, quant-research-backup or Midna trees.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (Swing) signal in the midlarge cap band, restricted to fires carrying the deep70 + wiki_low tags. On the original Lazarus/md2 record it is a live fear-day fire-consumer (config below); on the v3 desk the lane is parked (CSV off): the engine still evaluates and manages exits for held positions, but entries are refused while parked. Sizing is one slot of $1,000 either way.

## Full algorithm

The v3 engine (`desk3/lazarus_q07.py` `evaluate_sleeve` with this cell's SPECS entry), in evaluation order:

1. Exits first, and parked lanes still manage exits: for each held position with qty > 0 and entry price > 0, if the last close (or the position's current price when no bars) is at or below entry x (1 - 0.15), emit a full market sell_to_close exit ("stop_15pct"). Otherwise, if the position's opened date is at least horizon_w x 7 = 364 calendar days before the session date, emit a full market sell_to_close exit ("horizon_52w").
2. Because the spec is parked, evaluation returns after the exit scan: no entries are emitted on the v3 desk while parked.
3. If unparked, entries would proceed exactly as the shared engine prescribes: slots = 1 minus distinct held symbols; entries refused when QQQ is not down; candidate fires must match this sleeve id when they carry one, read family "swing" and band "midlarge", and not be already held; signal age in sessions must be known and <= 5; filters (all must pass, fail closed): deep70 = the fire's deep70 tag true, else drawdown_from_high >= 0.30, else price <= 0.70 x high_52w tag, else price <= 0.70 x the maximum close in the symbol's bars; wlow = the fire's wiki_low tag true or wiki_attention == "low", otherwise fail. Pricing under ENH-Q07EXEC-20261024 (default ON) revalidates filters/sizing/stop at the last bar close; qty = int(1000 // price); the entry intent is market, day, buy_to_open with stop_price = round(price x 0.85, 4).

The original-lane record (rl64 config entry, verbatim values), which was live (not parked) on the md2 record:

- Entry policy: policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day.
- Entry gate mechanics, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day): buy only when QQQ < prior close AND the stock <= its prior close AND the stock <= 1.02 x fire close (the config's no_chase_mult), decided inside the afternoon window (close-40 .. close-10 minutes) of a session in the red window D+1..D+5 after the fire session (cal.red_window with window_sessions 5); nothing by D+5 -> skip (never a green-day buy); every unknown price -> wait, never a false trigger. The capped limit (gate.capped_limit): limit = live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap.
- Exit: rule "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))"; hold_from "fill"; hold_unit_kind "1w"; stop_pct null; max_bars null; rest null; plan_overrides []. The EDGE_INVENTORY row records this cell as "CONFIRMED; ADD paper-test ($1k) -> core candidate" (no K 20 params row for this cell). Config flags record it was turned ON at the 2026-10-14 cutover and enabled on md2 on 2026-10-24 with the missing w_swing_fires_latest input restored by the w_swing_heal job.
- Sizing (config `sizing` block, verbatim values): budget_usd 1000; max_slots 1; position_usd 1000; position_usd_by_class {}; one_share_max_usd null; cap_pct_of_dv20 1.0; min_slot_fraction 0.9; global_slot_usd 1000; min_dv20_usd 100000. The vendored gate.size applies them: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, the one-share rule (inactive here: one_share_max_usd is null), and the lane dollar budget shrink to the remaining budget when that is at least min_slot_fraction of the position.
- Corpus tag definitions recorded on the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. Readings used by the v3 Q07 engines in this repo where the corpus lines do not define a token: wcov (wiki_cov) = wiki_cov tag true, or wiki_views > 0 (desk3/lazarus_q07.py); wlow (wiki_low) = wiki_low tag true (desk3/lazarus_q07.py), read as wiki == "low" in engines/laz_sleeves/_common.py and as 0 <= wiki_views_30d < 1000 in desk3/q07_engine.py; ins2 (insider2) = insider_buys >= 2 (both v3 engines). Cap-band dollar reading recorded in desk3/q07_engine.py: mi = market cap below $300,000,000; sm = $300,000,000 to $2,000,000,000; ml = $2,000,000,000 and above.

## Files in this repo

- This package: `docs/LZ_S_Q07W_S52_ML_DEEP70_WLOW-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Sleeve code (already in Test): `sleeves/s_q07w_s52_ml_deep70_wlow.py`, with copies at `adapters3/s_q07w_s52_ml_deep70_wlow.py` and `integration/s_q07w_s52_ml_deep70_wlow_adapter.py`
- Shared engine that runs the logic: `desk3/lazarus_q07.py` (SPECS entry `s_q07w_s52_ml_deep70_wlow`; INPUTS (fires, bars, positions))
- Config entries: `packages/grokbot/rl64/lz_engine/config/sleeves.json`, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, `sleeves/lazarus/vendor/lazarus/sleeves.json` (entry id `s_q07w_s52_ml_deep70_wlow` in each)
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `s_q07w_s52_ml_deep70_wlow` (parked true)
- md2 host for the config form of the lane: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Family algorithm doc for the stage-2 LZ enable: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Canonical id `lz_s_q07w_s52_ml_deep70_wlow` = "lz_" + config id `s_q07w_s52_ml_deep70_wlow`. Kind 1w. Family swing (w_swing). Cap band midlarge. Horizon 52 weeks. Filters deep70 + wlow.
- v3 roster: cadence_s 3600, session rth, slice $1,000, bp_buffer_frac 0.02, flat_by_close false, inputs [fires, bars, positions], parked true (entries refused; exits managed).
- Original-lane config: entry/exit/sizing blocks as quoted in the Full algorithm section; account TEST (paper), enabled true, state live.

## Data inputs

- v3 engine: the snapshot's "fires" key (sleeve_feed composer output; no fresh fires => fail closed, emit nothing), daily bars, and positions (broker readback).
- Fire shape the engine consumes: {symbol, family, band, signal_date, price, tags: {deep70 / drawdown_from_high / high_52w, wiki_low / wiki_attention, ...}} (tags may also be flat on the fire).
- Original lane: the composer fire file `shadow/paper_sleeve/live/sleeve_fires_v1.json` (lane `s_q07w_s52_ml_deep70_wlow`; the w_swing fires input per the config flags) plus daily bars for the entry-day red checks.

## Install and run

1. Clone the Test repo.
2. Place `desk3/lazarus_q07.py` under `desk3/` and the wrapper as `sleeves/s_q07w_s52_ml_deep70_wlow.py` (or the `adapters3/` copy).
3. Register the roster row for `s_q07w_s52_ml_deep70_wlow` from `config/sleeves.json` (cadence 3600, session rth, $1,000 slice, inputs fires/bars/positions, parked true).
4. Wire the view with composer `fires`, daily `bars`, and `positions`.
5. Call the wrapper's `evaluate(view, ctx)` on each pass; while parked it manages exits only. Unparking is a spec change (SPECS parked flag and the roster parked flag), not a config edit to make silently.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this cell was found in the fresh Test tree. Behaviour checklist, from the engine code and the config record:

- While parked, no entry intent is ever emitted, for any fire; exits are still evaluated first on every pass.
- A held position exits in full when the last close is at or below entry x 0.85, or when it has been held at least 364 calendar days.
- If unparked: a fire that reads the wrong family or band, is older than 5 sessions, or fails deep70 or wlow under the readings in the Full algorithm section produces no entry; a filter with no evidence fails closed; no entry is emitted on a day QQQ is not down or while the slot is occupied; quantity is int(1000 // execution price) and the entry intent carries stop_price = price x 0.85 (rounded to 4dp).
- The original-lane record prescribes a live fear_day capped-limit entry (limit = live ref x 1.01, capped by fire close x 1.05 and the 1.02x no-chase cap); the v3 desk parks this lane. That divergence is recorded here, not reconciled: the code is the truth for the v3 desk, the config for the original lane.
