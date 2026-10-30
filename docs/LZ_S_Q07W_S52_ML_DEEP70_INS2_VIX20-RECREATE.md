# lz_s_q07w_s52_ml_deep70_ins2_vix20: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_swing H52 midlarge deep70+insider2+stress_vix20 (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The sizing gap is closed by the in-repo records below (the engine's SLOT_USD and the config entry).
- In-repo records: the v3 wrapper `sleeves/s_q07w_s52_ml_deep70_ins2_vix20.py` (identical copy at `adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py`, integration copy at `integration/s_q07w_s52_ml_deep70_ins2_vix20_adapter.py`) carrying its SPEC inline, the shared engine `desk3/q07_engine.py`, its entry in `packages/grokbot/rl64/lz_engine/config/sleeves.json`, the derived algorithm doc `docs/S_Q07W_S52_ML_DEEP70_INS2_VIX20-ALGORITHM.md`, and the md2 host `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve id = "lz_" + config id). The wrapper header records: batch 6, authored for v3, no v2 source exists; catalog section 4.1 family rule.
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/EDGE_INVENTORY.csv Q07-w_swing-H52-midlarge-deep70+insider2+stress_vix20 (CONFIRMED; ADD paper-test ($1k) -> core candidate)"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv deep70+insider2+stress_vix20 w_swing H52 midlarge red band: n 185, names 64, edge +29.7 [11.2, 39.6], q_fam 0.00271, CONFIRMED"
  - Config status text: "md2 2026-10-24: ON (input = Research Lab w_swing feed, now present + healed; research CONFIRMED cells)".
- Code search record: Searched for code: Test tree at batch start (sleeves/, adapters3/, integration/, desk3/, packages/, docs/) and the contents of packages/grokbot/rl64/lz_engine/config/sleeves.json and packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json; Silicon tree (research/, desk trees), quant-research-backup tree and Midna tree were also grepped for the canonical id and the unprefixed id: no code file for this cell was found in those repos.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W Swing signal in the midlarge cap band, restricted to fires carrying the deep70 + insider2 + stress_vix20 confluence tags, bought only on a QQQ-down day, held 52 weeks. In v3 it is a thin wrapper over the shared engine `desk3/q07_engine.py`.

## Full algorithm

From the wrapper's inline SPEC (family="swing", band="ml", horizon_wk=52, filters=("deep70", "ins2", "vix20")) and `desk3/q07_engine.py` evaluate_q07, in evaluation order (constants SLOT_USD = 1000.0, STOP_PCT = 0.15, MAX_SIGNAL_AGE_SESSIONS = 5; CAP_BANDS_USD ml = $2,000,000,000 and above):

1. Exits first: for each held position (qty > 0), if the last close <= avg_price x 0.85 emit a full sell_to_close (reason q07_stop15); else if the position age in weeks ((today - opened_at).days / 7) >= 52 emit a full sell_to_close (reason q07_horizon_exit).
2. Entries are blocked entirely while any position is held (the 1 slot is occupied).
3. A QQQ-down day is required: at least 2 QQQ daily bars and the last QQQ close below the prior close.
4. Fires are read from view extra["sleeve_fires"] (params extra may also supply keys). A fire is skipped if its sleeve field differs from `s_q07w_s52_ml_deep70_ins2_vix20`, it has no symbol, its symbol is held, its cap_band (when carried) differs from "ml", its mcap_usd (when carried) falls outside the ml range, it has no signal_date, its signal age (QQQ sessions in (signal_date, today]) is under 0 or over 5, or it has no daily bars.
5. Freshest-first (ENH-Q07FRESH-20261024, switch default ON; OFF restores producer list order): eligible fires are ordered by signal age, freshest first. Stale bars (ENH25-Q07-STALEBARS-20261024, switch default ON): a fire whose symbol's last bar is more than 5 sessions before today is refused.
6. Filters, all must pass and fail closed (engine readings): deep70 = at least 20 daily bars and last close <= 70% of the maximum high over the trailing 252 sessions; ins2 = the fire's insider_buys >= 2 (missing counts as 0 and fails); vix20 = the snapshot vix value >= 20.0 (missing fails).
7. Sizing: qty = int(1000.0 // price); qty < 1 emits nothing. The entry Intent is a buy (buy_to_open) with stop = round(price x 0.85, 4) and exit rules stop at that price plus time_bars = 52 x 5 = 260. Only one entry is emitted (break after the first passing fire).
- Entry policy (config): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
- The config entry's order policy (fear_day, capped limit day, 5.0% band, 1.0% buffer, no-chase 1.02, both stock and QQQ red) is the md2/Lazarus-side execution record for the same cell; the v3 engine above emits Intents for the desk cycle. Both records are in this repo; this package does not merge them.
- Corpus tag definitions recorded in the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. stress_vix20 is the VIX >= 20 stress gate (the vix20 reading used by both v3 Q07 engines in this repo); ins2 / insider2 = insider_buys >= 2 (the reading used by both v3 Q07 engines in this repo).

## Files in this repo

- This package: `docs/LZ_S_Q07W_S52_ML_DEEP70_INS2_VIX20-RECREATE.md`
- Wrapper (already in Test; nothing vendored): `sleeves/s_q07w_s52_ml_deep70_ins2_vix20.py`, `adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py`, `integration/s_q07w_s52_ml_deep70_ins2_vix20_adapter.py`
- Shared engine: `desk3/q07_engine.py` (evaluate_q07)
- Derived algorithm doc: `docs/S_Q07W_S52_ML_DEEP70_INS2_VIX20-ALGORITHM.md`
- Config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_s52_ml_deep70_ins2_vix20`); md2 host: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`

## Configuration

- Canonical id `lz_s_q07w_s52_ml_deep70_ins2_vix20` = "lz_" + `s_q07w_s52_ml_deep70_ins2_vix20`. Kind 1w. Family swing, cap band ml ($2B and above in the engine), horizon 52 weeks, filters deep70 + ins2 + vix20.
- Sizing: engine SLOT_USD 1000.0, 1 slot; config entry sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper), enabled true, state live.
- Declared wrapper inputs: sleeve_fires, bars_1day, vix, positions.

## Data inputs

- Sleeve fires via the sleeve_feed composer (tracker ledger + alt-data tags), producer key "sleeve_fires" in the cycle snapshot view extra (fire rows carry sleeve, symbol, signal_date, cap_band, insider_buys, wiki_views_30d); file form `shadow/paper_sleeve/live/sleeve_fires_v1.json`.
- Daily bars (symbol and QQQ), the snapshot VIX value, and broker positions with avg_price and opened_at.

## Install and run

1. Clone this repository (Test).
2. Import the wrapper: `sleeves/s_q07w_s52_ml_deep70_ins2_vix20.py` exposes evaluate(view, ctx) delegating to desk3.q07_engine.evaluate_q07 with its inline SPEC.
3. Supply a view with extra.sleeve_fires, extra.vix, bars keyed "<symbol>|1day", and positions.
4. Run once per desk cycle; exits are emitted before entries, and at most one $1,000 entry is emitted per cycle.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A held position at or below 85% of its average price produces a full q07_stop15 exit; at 52 weeks of age it produces q07_horizon_exit; while any position is held, no entry is emitted.
- On a QQQ up day, or with the snapshot vix at 19.9, or with a fire whose insider_buys is 1, no entry is emitted.
- A passing fire at price $40 in the ml band produces exactly one buy_to_open entry of 25 shares with stop 34.0 and a 260-bar time exit rule.
