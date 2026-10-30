# lz_s_1dg - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Lab 1D Green trees (test)", type forecast and ML models, family 1d, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. Classification evidence on the entry (2026-10-30): the Muse desk v3 fidelity ledger for s_1dg reads "a boosted tree pick on a 1D Green fire, held 21 sessions with no stop". The sizing gap is closed by the rl64 config entry cited below, which is in this repo.
- Executable record in this repo: the entry (id `s_1dg`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, broker_account TEST_MWJW, kind 1d, enabled true, state live, status "ready (unarmed: desk staged)"), installed by `packages/grokbot/rl64/tools/install_rl64.py`. The md2 host that runs Lazarus config sleeves is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id, which is where this canonical id's lz_ prefix comes from). Research lines on the config entry: "DESK_INTEGRATION/DESK_PLAN.md F1 (1D green full gbm: Sharpe 0.89, alpha +8.2%, null p 0.048) + F2 (next open, 21 sessions)" and the desk playbook lane t_1dg; flags record the lane budget raised to $28,000 / 28 slots (2026-10-15) then L-146 scaled x0.611 to $17,000 / 17 slots.
- The v3 desk implementation of the same sleeve is also in this repo: adapter `adapters3/laz_s_1dg.py` (also `sleeves/s_1dg.py` and `integration/s_1dg_adapter.py`), the shared engine `desk3/lazarus.py` SPECS entry s_1dg, its own recreation package `docs/S_1DG-RECREATE.md`, the algorithm doc `docs/S_1DG-ALGORITHM.md` and the strategy card `strategies/lazarus/lz-lab-1d-green-trees.md`.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

One Lazarus 1D Green lane: a boosted-tree (gbm) pick over upstream lab_live 1D Green fires. It is a fire-consumer: the lab_live books produce the fires (native Lazarus routing, `DESK_INTEGRATION/lab_live/out/latest/*.json` per the config source block); this lane buys a fresh fire only on a fear (red) day under the capped-limit policy, holds 21 sessions with no stop, and exits on the fire plan's time exit or a stored target in the v3 engine form.

## Full algorithm

Two recorded layers, both in this repo; the config entry is the canonical record for this lz_ id and the v3 engine is its desk implementation:

Config layer (rl64 entry s_1dg):
1. Source: lab_live books (native Lazarus routing), file `DESK_INTEGRATION/lab_live/out/latest/*.json`, lane s_1dg.
2. Entry policy: fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true.
3. Entry gate mechanics for the fear_day policy, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day / capped_limit / size): buy only when QQQ is below its prior close AND the stock is at or below its prior close AND at or below 1.02 x the fire close (the config no_chase_mult), decided inside the afternoon window (close-40 to close-10 minutes) of a session in the red window D+1..D+5 after the fire session (window_sessions 5); nothing by D+5 means skip; every unknown price means wait, never a false trigger. The capped limit is live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap. Sizing under that gate: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, and the lane dollar budget shrunk to the remaining budget when that is at least min_slot_fraction of the position.
4. Exit (config): the sleeve feed fire's plan: no stop, time exit at hold = 21 sessions, hold_from fill, hold_unit_kind 1d, no plan overrides.
5. Sizing (config, closing the accounting gap): budget_usd 17000, max_slots 17, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000, position_usd_by_class {}, one_share_max_usd null.

v3 engine layer (`desk3/lazarus.py` SPECS s_1dg, per `docs/S_1DG-RECREATE.md`): slots=17, capital=17000.0, cadence_s=300, session rth, max_age_min=2880, stop_pct=None, horizon_sessions=21, family green, tf 1D, ml_pick=True. Exits first (stored target, then the 21-session time exit; no stop), and if any exit fires no entries are evaluated that call. Entries only when open positions are fewer than slots: a fire is skipped when it is not a dict, its sleeve_id differs, its symbol is missing or held, its side is not buy/long, its fired_at is unparseable, or its age is outside 0..2880 minutes; a fire carrying ml_pick=False is skipped; family is enforced only on fires carrying a family/color field. Price: fire price, falling back to the latest bar close, with the fresh-price enhancement (ENH-LAZ-REPRICE-20261024, default ON) using the freshest completed bar close for sizing and price_hint when it differs, and the bound guard (ENH19, default ON) refusing an entry at or above the fire target_price. Sizing: per_slot = 17000/17 = 1000.0; qty = int(per_slot // execution price); below 1 emits nothing. Entry is market, day, buy, reason s_1dg_tensor_fire, stop_price None. The adapter post-filter (`desk3/enhance18.py` stale_bar_gate, default ON, sleeve switch extra["s_1dg_enh2"]) refuses entries whose symbol's newest 1Day bar is more than 7 days old; exits are never filtered.

## Files in this repo

- This package: `docs/LZ_S_1DG-RECREATE.md`
- Executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_1dg`); installer `packages/grokbot/rl64/tools/install_rl64.py`
- md2 host: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; sleeve id "lz_" + config id)
- Vendored Lazarus gate: `sleeves/lazarus/vendor/lazarus/gate.py` (fear_day / capped_limit / size)
- v3 adapter: `adapters3/laz_s_1dg.py`; also `sleeves/s_1dg.py` and `integration/s_1dg_adapter.py`
- v3 engine: `desk3/lazarus.py` (SPECS entry s_1dg); post-filter `desk3/enhance18.py`
- Sibling packages and card: `docs/S_1DG-RECREATE.md`, `docs/S_1DG-ALGORITHM.md`, `strategies/lazarus/lz-lab-1d-green-trees.md`
- Roster row: `config/sleeves.json` (row id s_1dg), also `engines/config/sleeves.json`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `lz_s_1dg` = "lz_" + config id `s_1dg`. Kind 1d, account TEST, enabled true, state live.
- Config entry and sizing: as in the Full algorithm (budget $17,000, 17 slots, $1,000 position).
- v3 roster row for s_1dg: module adapters3.laz_s_1dg, cadence_s 300, session rth, slice capital_usd 17000.0 / cash_usd 17000.0, bp_buffer_frac 0.02, flat_by_close false, params {}, inputs [lazarus_fires, bars, positions], parked false.

## Data inputs

- lab_live fire books: `DESK_INTEGRATION/lab_live/out/latest/*.json` (config layer), delivered to the v3 engine as lazarus_fires (view lazarus_fires, extra lazarus_fires, view tensor_fires, or extra fires, first list found) with sleeve_id, symbol, side, fired_at/ts, price, optional target_price, horizon, family/color and ml_pick fields.
- Daily bars per symbol (and SPY bars for the session-count fallback); positions (broker readback); sleeve state in laz_state.json under the ctx state_dir.
- Daily closes for the entry-day red checks on the stock and QQQ (config-layer fear_day gate).

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Take the entry id `s_1dg` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this lane's configuration; do not edit its entry, exit or sizing fields.
4. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`), or through the v3 adapter `adapters3/laz_s_1dg.py`, whose evaluate(view, ctx) delegates to `desk3/lazarus.py` with the s_1dg SPECS entry and then the enhance18 stale-bar filter.
5. Feed the lab_live fires and daily bars in the shapes described under Data inputs.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (the desk's port blocker tests pin the vendored strategy files by sha256; no dedicated test file for this exact canonical id was found):

- A fire aged over 2880 minutes, with side not buy/long, or carrying ml_pick=False produces no entry.
- Config layer: an entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the fire and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x the fire close.
- Exactly $1,000 per slot and at most 17 slots; a fire while all slots are occupied produces no entry.
- A held position exits at its stored target or at 21 sessions held; no price move alone exits it (stop_pct None).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
