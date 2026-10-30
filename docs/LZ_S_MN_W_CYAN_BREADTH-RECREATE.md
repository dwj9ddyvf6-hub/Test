# lz_s_mn_w_cyan_breadth: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W cyan breadth (Midna port)", type market timing and rotation, family 1d. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. Sources: md2 catalog entry / exit / strategy text. Alias `lz_s_mn_w_cyan_breadth`, status installed (md2_catalog). No Test catalog entry (test_entries empty).
- The accounting's recorded entry config: {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; recorded exit: Midna plan, no stop / time exit 126 sessions, hold from fill, hold unit kind 1d, stop_pct 99.0, max_bars 126, rest "time", no plan overrides; recorded data note: sleeve_midna (Midna entire-branch signal files + Yahoo), fires at `shadow/paper_sleeve/live/midna/midna_fires_v1.json`.
- The sizing gap is filled from the code in Test: the shared engine spec and the config row below both record a $1,000 budget / slice (see Configuration).
- Per-sleeve algorithm doc in Test: `docs/S_MN_W_CYAN_BREADTH-ALGORITHM.md`, derived from the sleeve code on 2026-10-29.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start and searched by filename for the canonical id, its alias and its distinguishing tokens, across sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, laz_sleeves/, config/ and docs/; the Silicon, quant-research-backup and Midna trees in this run's workspace were searched the same way. The code is already in Test (see Files); no distinct code for this sleeve was found in Silicon, quant-research-backup or Midna.

## What this strategy is

A long-only equity Midna fire-consumer sleeve (weekly cyan family): it consumes upstream Midna fires for sleeve id `s_mn_w_cyan_breadth`, applies a market-breadth gate of at least 0.50, holds at most one $1,000 position, and exits only on a 126-session time exit. Signal generation stays upstream in the fire producer; this sleeve is the consumer and position manager. Fail-closed if fires are absent or stale.

## Full algorithm

From `docs/S_MN_W_CYAN_BREADTH-ALGORITHM.md` and the engine spec in `desk3/lazarus_midna.py` (SPECS["s_mn_w_cyan_breadth"] = family="cyan", tf="1W", hold_sessions=126, stop=None, gate="breadth", budget=1000.0), in evaluation order:

1. Exits are evaluated first. If any exit intent is emitted, or any non-zero-qty position is already held, no entry is emitted (max 1 slot).
2. Fires are read from view["midna_fires"], view["fires"], extra["midna_fires"] / ["fires"], or the tensor / tensor_bundle value (a list, a dict with a fires / midna_fires list, or a sleeves dict of fire lists). Fire shape: sleeve_id, symbol, family, timeframe, date, price.
3. A fire is skipped if its sleeve_id differs from `s_mn_w_cyan_breadth`, its family / kind / signal does not contain the spec family "cyan", its timeframe does not match 1W (1W accepts 1W / W / WEEKLY / WEEK), it has no symbol, or its date is after the session or more than 10 days before it.
4. Cross-stale gate (ENH20-MN-XSTALE-20261024, switch default ON; OFF via extra["s_mn_w_cyan_breadth_enh20"]["xstale_gate"]=False): refuse a symbol whose last bar lags the latest bar date across the snapshot bars by more than 4 days.
5. Price: the fresh last bar close when the ENH19 reprice switch is on (default) and a fresh close exists; otherwise the fire price. A price at or below zero is skipped.
6. Gate "breadth": breadth must be at least 0.50, read from extra breadth_pct, else market_breadth_pct, else extra["breadth"]["pct"]; a missing breadth value is skipped (fail-closed).
7. Sizing: qty = int(1000.0 // price); qty < 1 emits nothing. Orders are market, day, buy_to_open.
8. Exit: no price stop (stop=None). Time exit: a position held for at least 126 sessions is sold in full. Exits are market, day, sell_to_close, in full. Age is read from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against the symbol bars.

## Files in this repo

- This package: `docs/LZ_S_MN_W_CYAN_BREADTH-RECREATE.md`
- Algorithm doc: `docs/S_MN_W_CYAN_BREADTH-ALGORITHM.md`
- Code (already in Test): `sleeves/s_mn_w_cyan_breadth.py` (thin wrapper, SLEEVE_ID="s_mn_w_cyan_breadth"), `adapters3/s_mn_w_cyan_breadth.py`, `integration/s_mn_w_cyan_breadth_adapter.py`, shared engine `desk3/lazarus_midna.py`
- Config: `config/sleeves.json` row id `s_mn_w_cyan_breadth`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Config row in `config/sleeves.json`: module adapters3.s_mn_w_cyan_breadth, cadence_s 300, session rth, slice capital_usd 1000.0 / cash_usd 1000.0, bp_buffer_frac 0.02, flat_by_close false, inputs [tensor, bars, positions], parked false.
- Engine spec: family="cyan", tf="1W", hold_sessions=126, stop=None, gate="breadth", budget=1000.0, at most 1 open position.
- The accounting's entry-policy values (midna_block, 65-minute max delay, 5.0% limit band, 1.0% buffer, capped_limit_day) are recorded in Provenance; the algorithm doc's market-order description comes from the engine code. Both are recorded as found; they are not reconciled here.

## Data inputs

- Declared inputs: tensor, bars, positions. Producers named in the engine: tensor_bundle (86400s freshness, outputs tensor), bars (900s), broker_readback (900s, positions).
- Fires: the midna_fires file named in Provenance, consumed via the desk Tensor bundle producer channel using the validated fire schema.

## Install and run

1. Clone the Test repo.
2. Read `docs/S_MN_W_CYAN_BREADTH-ALGORITHM.md` and this package.
3. Use the code files listed in Files as the runnable logic: `sleeves/s_mn_w_cyan_breadth.py` exposes evaluate(view, ctx), which delegates to `desk3/lazarus_midna.py` evaluate(SLEEVE_ID, view, ctx).
4. Provide the data inputs listed above (tensor bundle with midna fires, bars, positions, and a breadth value in the view extra).
5. Run on the recorded cadence (300s, RTH session) and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry is emitted while a position is held or an exit intent was emitted in the same evaluation.
- A fire with breadth below 0.50, or with no breadth value, produces no entry.
- A fire older than 10 days, dated after the session, with the wrong sleeve_id / family / timeframe, or cross-stale by more than 4 days, produces no entry.
- Entry quantity is exactly int(1000.0 // price) and nothing is emitted when that is below 1.
- The only exit is the 126-session time exit, in full; there is no price stop.
