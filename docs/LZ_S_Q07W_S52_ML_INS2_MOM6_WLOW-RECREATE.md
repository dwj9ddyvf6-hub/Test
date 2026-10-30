# lz_s_q07w_s52_ml_ins2_mom6_wlow: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_swing H52 midlarge insider2+mom6+wiki_low (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". The sizing gap is closed twice over in this repo: by the rl64 config entry and by the v3 wrapper's own call parameters cited below.
- Config record in this repo: the cell's own entry (id `s_q07w_s52_ml_ins2_mom6_wlow`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, broker_account TEST_MWJW, kind 1w, enabled true, state live), also present in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and in the vendored lazarus-desk config `sleeves/lazarus/vendor/lazarus/sleeves.json`. The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id, which is where this canonical id's lz_ prefix comes from; DISASTER_STOP 15.0 in that host).
- Code in this repo (the v3-native implementation, which is the truth for how the lane runs on the v3 desk): sleeve module `laz_sleeves/s_q07w_s52_ml_ins2_mom6_wlow.py` (copy at `sleeves/lazarus/s_q07w_s52_ml_ins2_mom6_wlow.py`), delegating to `q07_evaluate` in the shared batch-7 engine `engines/laz_sleeves/_common.py` with the lane's own parameters: band "midlarge", horizon_weeks 52, filters ('ins2', 'mom6', 'wlow'), slots 1, slot_usd 1000.0. The module docstring records: "Catalog rule (SS4.1 family rule + lane row): Tensor 1W Swing signal, midlarge band, filters ('ins2', 'mom6', 'wlow'); buy only on a QQQ-down day within 5 sessions of the signal; exit 15% stop or 52-week horizon. Source status Disabled -> parked in v3 config (evaluates, dispatcher skips entries while parked). Fires arrive via the desk Tensor bundle producer (ledger substitution LAZ-B7)." Module INPUTS = (bars_1day, positions, tensor_fires, alt_data, vix). Roster row in `config/sleeves.json` (and `engines/config/sleeves.json`): module laz_sleeves.s_q07w_s52_ml_ins2_mom6_wlow, cadence_s 86400, session rth, slice capital/cash $1,000, bp_buffer_frac 0.02, flat_by_close false, inputs [bars_1day, positions, tensor_fires, alt_data, vix], parked true.
- This id has no SPECS entry in `desk3/lazarus_q07.py` and no spec in `desk3/q07_engine.py`; those are sibling Q07 engines and are not this lane's code.
- Research evidence recorded on the rl64 config entry:
  - "DESK_INTEGRATION/EDGE_INVENTORY.csv Q07-w_swing-H52-midlarge-insider2+mom6+wiki_low (UNPROVEN (PROMISING: CI > 0, latest year against); ADD paper-test ($1k))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv insider2+mom6+wiki_low w_swing H52 midlarge red band: n 118, names 43, edge +10.8 [3.1, 16.4], q_fam 0.0736, UNPROVEN (PROMISING: CI > 0, latest year against)"
  - "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"
  - Flag: "staged off: staged-off: input missing"
  - Flag: "turned ON at cutover 2026-10-14 (was off)"
  - Flag: "md2 2026-10-24: enabled; the missing w_swing_fires_latest input is restored by the w_swing_heal job"
  - Status text on the entry: "md2 2026-10-24: ON (input = Research Lab w_swing feed, now present + healed; research CONFIRMED cells)".
- Code search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b33_Test_tree.txt, b33_Silicon_tree.txt, b33_quant-research-backup_tree.txt, b33_Midna_tree.txt in the run workspace; the quant-research-backup tree carries GitHub's own truncation note) and searched by filename for the canonical id, the unprefixed config id and the q07/lazarus tokens; the contents of the three lz_engine config copies in Test (rl64, q07-1w-swing-lz, and the vendored lazarus-desk config at sleeves/lazarus/vendor/lazarus/sleeves.json), desk3/lazarus_q07.py SPECS, desk3/q07_engine.py and the Test roster config/sleeves.json were read directly. No q07 or lazarus path exists in the Silicon, quant-research-backup or Midna trees.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (Swing) signal in the midlarge cap band, restricted to fires carrying the insider2 + mom6 + wiki_low tags. On the original Lazarus/md2 record it is a live fear-day fire-consumer (config below); on the v3 desk it is a v3-native batch-7 lane over `engines/laz_sleeves/_common.py`, parked in the roster (the module evaluates; the dispatcher skips its entries while parked). Sizing is one slot of $1,000 either way. Its corpus evidence is the weakest of this batch: the config's own research rows grade the cell UNPROVEN (PROMISING).

## Full algorithm

The v3 engine (`engines/laz_sleeves/_common.py` `q07_evaluate`, called with this lane's parameters), in evaluation order:

1. Session is read from the view's "now"; no parseable session date => no intents.
2. Exits first, over this sleeve's own positions only (positions carrying another sleeve_id are never touched): if the symbol's last daily close is at or below avg_price x 0.85, emit a full exit ("q07_stop15"); else if the sessions held (daily bars strictly after the opened date) reach horizon_weeks x 5 = 260 sessions, emit a full exit ("q07_time_horizon").
3. Entries stop here when the held count reaches slots (1) or QQQ is not down (last QQQ 1Day close below the previous close).
4. Candidate fires come from the view's "tensor_fires" map (symbol -> {family, date}; the desk Tensor bundle producer output, substituting for the unreachable composer file, LAZ-B7): the fire's family must equal "swing"; its calendar age must be 0..7 days (the code's reading of "within 5 sessions of the signal"); the symbol must not be held; the symbol's alt_data mcap_band must equal "midlarge".
5. Filters (all must pass, from the symbol's alt_data tags and daily bars): ins2 = insider_buys >= 2; mom6 = the 126-session return (last close vs the close 127 bars back) is computable and > 0; wlow = the alt_data wiki field equals "low".
6. Staleness gate (ENH24-LAZB7-Q07STALE-20261024, default ON): an entry is refused when the symbol's last daily bar is more than 4 calendar days before the session (a paired shadow journal record is written when the journal is wired); exits are never gated.
7. Sizing and entry intent: qty = int(slot_usd // last close) = int(1000 // last); qty <= 0 emits nothing. The entry intent is market, day, with price_hint at the last close and reason "q07_ins2_mom6_wlow". The ENH-Q07SLOT-20261024 slot guard (default ON) counts entries already emitted this pass against the slot cap.

The original-lane record (rl64 config entry, verbatim values):

- Entry policy: policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day.
- Entry gate mechanics, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day): buy only when QQQ < prior close AND the stock <= its prior close AND the stock <= 1.02 x fire close (the config's no_chase_mult), decided inside the afternoon window (close-40 .. close-10 minutes) of a session in the red window D+1..D+5 after the fire session (cal.red_window with window_sessions 5); nothing by D+5 -> skip (never a green-day buy); every unknown price -> wait, never a false trigger. The capped limit (gate.capped_limit): limit = live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap.
- Exit: rule "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))"; hold_from "fill"; hold_unit_kind "1w"; stop_pct null; max_bars null; rest null; plan_overrides []. The EDGE_INVENTORY row records this cell as "UNPROVEN (PROMISING: CI > 0, latest year against); ADD paper-test ($1k)" (no K 20 params row for this cell). Config flags record it was turned ON at the 2026-10-14 cutover and enabled on md2 on 2026-10-24 with the missing w_swing_fires_latest input restored by the w_swing_heal job.
- Sizing (config `sizing` block, verbatim values): budget_usd 1000; max_slots 1; position_usd 1000; position_usd_by_class {}; one_share_max_usd null; cap_pct_of_dv20 1.0; min_slot_fraction 0.9; global_slot_usd 1000; min_dv20_usd 100000. The vendored gate.size applies them: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, the one-share rule (inactive here: one_share_max_usd is null), and the lane dollar budget shrink to the remaining budget when that is at least min_slot_fraction of the position.
- Corpus tag definitions recorded on the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. Readings used by the v3 Q07 engines in this repo where the corpus lines do not define a token: wcov (wiki_cov) = wiki_cov tag true, or wiki_views > 0 (desk3/lazarus_q07.py); wlow (wiki_low) = wiki_low tag true (desk3/lazarus_q07.py), read as wiki == "low" in engines/laz_sleeves/_common.py and as 0 <= wiki_views_30d < 1000 in desk3/q07_engine.py; ins2 (insider2) = insider_buys >= 2 (both v3 engines). Cap-band dollar reading recorded in desk3/q07_engine.py: mi = market cap below $300,000,000; sm = $300,000,000 to $2,000,000,000; ml = $2,000,000,000 and above.

## Files in this repo

- This package: `docs/LZ_S_Q07W_S52_ML_INS2_MOM6_WLOW-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Sleeve code (already in Test): `laz_sleeves/s_q07w_s52_ml_ins2_mom6_wlow.py`, with a copy at `sleeves/lazarus/s_q07w_s52_ml_ins2_mom6_wlow.py`
- Shared engine that runs the logic: `engines/laz_sleeves/_common.py` (`q07_evaluate`)
- Config entries: `packages/grokbot/rl64/lz_engine/config/sleeves.json`, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, `sleeves/lazarus/vendor/lazarus/sleeves.json` (entry id `s_q07w_s52_ml_ins2_mom6_wlow` in each)
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `s_q07w_s52_ml_ins2_mom6_wlow` (parked true)
- md2 host for the config form of the lane: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Family algorithm doc for the stage-2 LZ enable: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Canonical id `lz_s_q07w_s52_ml_ins2_mom6_wlow` = "lz_" + config id `s_q07w_s52_ml_ins2_mom6_wlow`. Kind 1w. Family swing (w_swing). Cap band midlarge. Horizon 52 weeks. Filters ins2 + mom6 + wlow.
- v3 roster: cadence_s 86400, session rth, slice $1,000, bp_buffer_frac 0.02, flat_by_close false, inputs [bars_1day, positions, tensor_fires, alt_data, vix], parked true (dispatcher skips entries; the module still evaluates and its exits are produced by evaluation).
- Original-lane config: entry/exit/sizing blocks as quoted in the Full algorithm section; account TEST (paper), enabled true, state live.

## Data inputs

- v3 engine snapshot keys: bars (daily bars keyed "SYM|1Day", including QQQ), positions (with sleeve_id, qty, avg_price, opened_at), tensor_fires (symbol -> family/date, from the desk Tensor bundle producer), alt_data (symbol -> insider_buys, wiki, mcap_band, and the other batch-7 tags), and vix (declared in the module INPUTS; this lane's three filters do not read it).
- Original lane: the composer fire file `shadow/paper_sleeve/live/sleeve_fires_v1.json` (lane `s_q07w_s52_ml_ins2_mom6_wlow`; the w_swing fires input per the config flags) plus daily bars for the entry-day red checks.

## Install and run

1. Clone the Test repo.
2. Place `engines/laz_sleeves/_common.py` under `engines/laz_sleeves/` and the lane module as `laz_sleeves/s_q07w_s52_ml_ins2_mom6_wlow.py`.
3. Register the roster row for `s_q07w_s52_ml_ins2_mom6_wlow` from `config/sleeves.json` (cadence 86400, session rth, $1,000 slice, inputs bars_1day/positions/tensor_fires/alt_data/vix, parked true).
4. Wire the view with daily `bars`, `positions`, `tensor_fires`, `alt_data` and `vix`.
5. Call the module's `evaluate(view, ctx)` on each pass; exits are evaluated before entries. Unparking is a roster/config decision (the roster parked flag), not a code change.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this cell was found in the fresh Test tree. Behaviour checklist, from the engine code and the config record:

- The lane never emits an intent for a position carrying another sleeve_id, and emits nothing at all when the view carries no parseable session date.
- A held position exits in full when the last daily close is at or below avg_price x 0.85, or when the sessions held reach 260; exits are evaluated before entries and are never blocked by the staleness gate.
- No entry is emitted when QQQ's last daily close is not below its previous close, when the single slot is occupied, or while the roster parks the lane.
- A fire is refused when its family is not "swing", its calendar age is outside 0..7 days, its alt_data mcap_band is not "midlarge", or any filter fails (insider_buys < 2, 126-session return not computable or <= 0, wiki not "low"); an entry is also refused when the symbol's last daily bar is more than 4 calendar days stale (ENH24, default ON).
- The entry quantity is int(1000 // last close) whole shares.
- The original-lane record prescribes a live fear_day capped-limit entry (limit = live ref x 1.01, capped by fire close x 1.05 and the 1.02x no-chase cap); the v3 desk parks this lane and its engine enters at market under a QQQ-down gate. That divergence is recorded here, not reconciled: the code is the truth for the v3 desk, the config for the original lane.
