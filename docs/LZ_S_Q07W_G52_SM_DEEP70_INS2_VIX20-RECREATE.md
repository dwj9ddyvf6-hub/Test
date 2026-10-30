# lz_s_q07w_g52_sm_deep70_ins2_vix20: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Q07 w_green H52 small deep70+insider2+stress_vix20 (test)", type trend following, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. The sizing gap is closed by the in-repo records below (SPECS budget and the config entry).
- In-repo records: the v3 wrapper `sleeves/s_q07w_g52_sm_deep70_ins2_vix20.py` (identical copy at `adapters3/s_q07w_g52_sm_deep70_ins2_vix20.py`, integration copy at `integration/s_q07w_g52_sm_deep70_ins2_vix20_adapter.py`), its spec row in `desk3/lazarus_q07.py` SPECS, its entry in `packages/grokbot/rl64/lz_engine/config/sleeves.json`, the derived algorithm doc `docs/S_Q07W_G52_SM_DEEP70_INS2_VIX20-ALGORITHM.md`, and the md2 host `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve id = "lz_" + config id, the source of this canonical id's lz_ prefix).
- Research evidence recorded on the config entry:
  - "DESK_INTEGRATION/EDGE_INVENTORY.csv Q07-w_green-H52-small-deep70+insider2+stress_vix20 (UNPROVEN (PROMISING: CI > 0, fails family BH); ADD paper-test ($1k))"
  - "CORPUS_AUDIT/out/Q07_confluence_cells.csv deep70+insider2+stress_vix20 w_green H52 small red band: n 46, names 45, edge +109.6 [23.9, 222.8], q_fam 0.253, UNPROVEN (PROMISING: CI > 0, fails family BH)"
  - Config status text: "ready (unarmed: desk staged)".
- Code search record: Searched for code: Test tree at batch start (sleeves/, adapters3/, integration/, desk3/, packages/, docs/) and the contents of packages/grokbot/rl64/lz_engine/config/sleeves.json and packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json; Silicon tree (research/, desk trees), quant-research-backup tree and Midna tree were also grepped for the canonical id and the unprefixed id: no code file for this cell was found in those repos.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W Green signal in the small cap band, restricted to fires carrying the deep70 + insider2 + stress_vix20 confluence tags, bought only on a QQQ-down day, held 52 weeks. In v3 it is a thin wrapper over the shared fire-consumer engine `desk3/lazarus_q07.py`.

## Full algorithm

From `desk3/lazarus_q07.py` (SPECS row: family="green", band="small", horizon_w=52, filters=("deep70", "ins2", "vix20"), slots=1, budget=1000.0, parked=False) and its evaluate_sleeve, in evaluation order:

1. Exits first (parked lanes would still manage exits; this lane is not parked): for each held position with qty > 0 and entry price > 0, if the last close <= entry x (1 - 0.15) emit a full sell (reason "q07 exit: stop_15pct"); else if the holding age in calendar days >= 52 x 7 emit a full sell (reason "q07 exit: horizon_52w").
2. Entries: open slots = 1 - distinct held symbols; if none, stop. A QQQ-down day is required: extra["qqq_red"] if a bool, else market["qqq_red"] if a bool, else the last QQQ close below its prior close.
3. Candidate fires come from view["fires"]; a fire is skipped if it has no symbol, its sleeve_id/sleeve (when carried) differs from `s_q07w_g52_sm_deep70_ins2_vix20`, its family does not normalise to green (green/w_green/g accepted), its band/cap_band does not normalise to small (sm/small accepted), or its symbol is held.
4. Signal age (sessions since signal_date/fired_at/fire_date/date, counted on QQQ bar dates when available, else calendar days x 5/7) must be present and <= 5 sessions (WINDOW_SESSIONS = 5).
5. Freshest-first (ENH-Q07FRESH-20261024, switch extra.q07_enh[sid].fresh_first, default ON; OFF restores producer list order): with 2 or more candidates the slot is allocated freshest-signal-first.
6. Filters, all must pass and fail closed on no evidence (passes_filters): deep70 = an explicit deep70 tag, else drawdown_from_high >= 0.30, else price <= 70% of a high_52w tag, else price <= 70% of the maximum close in bars; ins2 = insider_buys >= 2 when carried, else a true ins2 tag; vix20 = a vix tag >= 20.0, else the last close of VIX or ^VIX bars >= 20.0.
7. Execution price (ENH-Q07EXEC-20261024, switch default ON; OFF restores the fire price): filters, sizing and stop are revalidated at the latest bar close.
8. Sizing: qty = int((budget / slots) // price) = int(1000.0 // price); qty < 1 emits nothing. The entry intent is a day market buy (buy_to_open) with stop_price = round(price x 0.85, 4).
- Entry policy (config): policy fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true (both the stock and QQQ must be red on the entry day).
- The config entry's order policy (fear_day, capped limit day, 5.0% band, 1.0% buffer, no-chase 1.02, both stock and QQQ red) is the md2/Lazarus-side execution record for the same cell; the v3 engine above emits market intents. Both records are in this repo; which one a recreation follows depends on the host (md2 Lazarus host vs the v3 desk cycle), and this package does not merge them.
- Corpus tag definitions recorded in the config entry's research lines (CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly): tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; cap bands are PIT SEC bands. stress_vix20 is the VIX >= 20 stress gate (the vix20 reading used by both v3 Q07 engines in this repo); ins2 / insider2 = insider_buys >= 2 (the reading used by both v3 Q07 engines in this repo).

## Files in this repo

- This package: `docs/LZ_S_Q07W_G52_SM_DEEP70_INS2_VIX20-RECREATE.md`
- Wrapper (already in Test; nothing vendored): `sleeves/s_q07w_g52_sm_deep70_ins2_vix20.py`, `adapters3/s_q07w_g52_sm_deep70_ins2_vix20.py`, `integration/s_q07w_g52_sm_deep70_ins2_vix20_adapter.py`
- Shared engine: `desk3/lazarus_q07.py` (SPECS row for `s_q07w_g52_sm_deep70_ins2_vix20`, evaluate_sleeve, passes_filters)
- Derived algorithm doc: `docs/S_Q07W_G52_SM_DEEP70_INS2_VIX20-ALGORITHM.md`
- Config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_g52_sm_deep70_ins2_vix20`); md2 host: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`

## Configuration

- Canonical id `lz_s_q07w_g52_sm_deep70_ins2_vix20` = "lz_" + `s_q07w_g52_sm_deep70_ins2_vix20`. Kind 1w. Family green, cap band small, horizon 52 weeks, filters deep70 + ins2 + vix20.
- Sizing: SPECS budget 1000.0 over 1 slot; config entry sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Account TEST (paper), enabled true, state live.
- Inputs declared by the engine: fires, bars, positions; producers sleeve_feed_composer (fires, freshness SLA 604800s), bars (3600s), broker_readback (3600s).

## Data inputs

- Fires from the sleeve_feed composer (tracker ledger + alt-data tags), file `shadow/paper_sleeve/live/sleeve_fires_v1.json` on the md2 side; the v3 engine consumes the snapshot "fires" key (no fresh fires = fail closed, emit nothing).
- Daily bars for the symbol, QQQ and VIX/^VIX; broker positions with entry price and opened date.

## Install and run

1. Clone this repository (Test).
2. Import the wrapper: `sleeves/s_q07w_g52_sm_deep70_ins2_vix20.py` exposes evaluate(view, ctx) delegating to desk3.lazarus_q07.evaluate_sleeve with SPECS["s_q07w_g52_sm_deep70_ins2_vix20"].
3. Supply a view with fires, bars (symbol, QQQ, VIX) and positions, and a ctx with session and now.
4. Run once per desk cycle; exits are emitted before entries, and at most one $1,000 entry is emitted per cycle.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A held position at or below 85% of its entry price produces a full stop exit before any entry is considered; a position held 364 or more calendar days produces the horizon exit.
- No QQQ-down day, or no fire within 5 sessions, produces no entry.
- A fire with insider_buys 1, a vix value of 19.9, or a price above 70% of its trailing high fails its filter and produces no entry; a fire with no insider or VIX evidence at all also fails (fail closed).
- A passing fire at price $40 produces exactly one entry of 25 shares with stop_price 34.0.
