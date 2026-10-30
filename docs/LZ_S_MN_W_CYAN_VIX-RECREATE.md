# lz_s_mn_w_cyan_vix: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W cyan mid-VIX (Midna port)", type volatility, family 1d. Algorithm grade PARTIAL in the accounting, with the recorded gap: sizing not recorded in any consulted source. Alias `lz_s_mn_w_cyan_vix` (md2_catalog status: installed).
- Accounting entry record: {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}. Accounting exit record: {"rule": "Midna plan: no stop / time exit 252 sessions", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 252, "rest": "time", "plan_overrides": []}. Accounting data note: sleeve_midna (Midna entire-branch signal files + Yahoo), fire file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- The sizing the accounting lacked, and the running rules, are held in the code in this repo (named in Files) and in the code-derived Test doc `docs/S_MN_W_CYAN_VIX-ALGORITHM.md`; nothing beyond the record and that code is claimed. The Test sleeve id drops the accounting's `lz_` prefix: `s_mn_w_cyan_vix`.

## What this strategy is

A long-only equity Midna fire-consumer: it consumes weekly (1W) Cyan Tensor fires for names whose VIX sits in the mid band (12 to 25 inclusive), one position at a time, $1,000 a position, no price stop, and a 252-session time exit. Signal generation stays upstream in the fire producer; the sleeve fails closed if fires are absent or stale.

## Full algorithm

From `docs/S_MN_W_CYAN_VIX-ALGORITHM.md`, derived from the code: wrapper `sleeves/s_mn_w_cyan_vix.py` delegates to `desk3/lazarus_midna.py` evaluate(SLEEVE_ID, view, ctx). Engine SPEC for this sleeve: family="cyan", tf="1W", hold_sessions=252, stop=None, gate="vix_mid", budget=1000.0. Inputs: tensor, bars, positions; at most 1 open position.

Evaluation order:

1. Exits first: a held position held for at least 252 sessions is sold in full (market, day, sell_to_close). Age is read from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against the symbol bars. There is no price stop (stop=None). If any exit intent is emitted, or any non-zero-qty position is already held, no entry is emitted (max 1 slot).
2. Fires are read from view["midna_fires"], view["fires"], extra["midna_fires"] / ["fires"], or the tensor / tensor_bundle value (a list, a dict with a fires/midna_fires list, or a sleeves dict of fire lists). Fire shape consumed: sleeve_id, symbol, family, timeframe, date and price.
3. A fire is skipped if its sleeve_id differs, its family/kind/signal does not contain the spec family ("cyan"), its timeframe/tf does not match 1W (accepts 1W/W/WEEKLY/WEEK), it has no symbol, or its date/fire_date/ts is after the session or more than 10 days before it.
4. Cross-stale gate (ENH20-MN-XSTALE-20261024, switch default ON; OFF via extra["s_mn_w_cyan_vix_enh20"]["xstale_gate"]=False): refuse a symbol whose last bar lags the latest bar date across the snapshot bars by more than 4 days.
5. Gate "vix_mid": VIX must be between 12.0 and 25.0 inclusive, read from extra vix_close, else extra vix, else the last close of VIX or ^VIX bars; a missing VIX value is skipped (no entry).
6. Price: the fresh last bar close when the ENH19 reprice switch is on (default) and a fresh close exists; otherwise the fire price. A price at or below zero is skipped.
7. Sizing: qty = int(1000.0 // price); qty < 1 emits nothing. Entry orders are market, day, buy_to_open.

## Files in this repo

- This doc: `docs/LZ_S_MN_W_CYAN_VIX-RECREATE.md`
- Sleeve code (already in Test): `sleeves/s_mn_w_cyan_vix.py`, with copies at `adapters3/s_mn_w_cyan_vix.py` and `integration/s_mn_w_cyan_vix_adapter.py`.
- Shared engine that runs the logic: `desk3/lazarus_midna.py` (SPEC row for s_mn_w_cyan_vix).
- Code-derived algorithm doc: `docs/S_MN_W_CYAN_VIX-ALGORITHM.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `s_mn_w_cyan_vix`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.
- Code search: Silicon, quant-research-backup and Midna trees were searched for this sleeve id; the running code was found in Test only (the Midna repo tree holds the upstream branch material, not this v3 sleeve).

## Configuration

- Test sleeve id: `s_mn_w_cyan_vix`; roster module `adapters3.s_mn_w_cyan_vix`; cadence 300 seconds; session rth.
- Slice capital and cash $1,000; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; parked false.
- Inputs declared in config: tensor, bars, positions. Budget $1,000, slots 1, hold 252 sessions, VIX gate 12-25 inclusive.

## Data inputs

- Midna fires (the tensor_bundle producer, freshness 86400 s, outputs tensor) in the fire shape above.
- Bars (producer freshness 900 s) and positions (broker_readback, 900 s); a VIX value via extra vix_close / vix or VIX / ^VIX bars.

## Install and run

1. Clone the Test repo.
2. Place `desk3/lazarus_midna.py` under `desk3/` and the wrapper as `sleeves/s_mn_w_cyan_vix.py` (or the `adapters3/` copy), keeping the repo layout so imports resolve.
3. Register the roster row for `s_mn_w_cyan_vix` from `config/sleeves.json` with the Configuration values above.
4. Wire the view: fires under one of the keys in step 2 of the algorithm, bars, positions, and a VIX value; absent or stale fires mean no entry, never a fabricated fire.
5. Call the wrapper's `evaluate(view, ctx)` every 300 seconds in RTH; exits are evaluated before entries.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- No entry when VIX is below 12, above 25, or missing; no entry on a fire older than 10 days, from the future, with the wrong family or timeframe, or for a symbol whose bars lag the snapshot by more than 4 days (gate on).
- A held position blocks any new entry and exits only on the 252-session time rule, in full; there is no price stop.
- Entry quantity equals int(1000 // price) at the repriced fresh close (switch on) or the fire price; a result below 1 emits nothing.
