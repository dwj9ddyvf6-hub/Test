# lz_s_mn_opt_turtle: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Midna Opt Turtle (Midna port)", type options directional, family 1d. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. The accounting records the entry policy and exit rule quoted below; the running Test code supplies the selection, budget and exit mechanics.
- No Test catalog entry in the accounting (test_entries empty); alias source md2_catalog, status installed.
- Accounting wrapper records: entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; data: sleeve_midna (entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Running code in Test (verified at batch start): the sleeve module named in the Files section, with its adapter.

## What this strategy is

Options form of the Turtle breakout rule, shadow, $1,000, one position (catalog rule in the code header: Options, 1D, Shadow, entry 'Turtle breakout traded with listed options', exit 'Turtle exit', $1,000; underlying Turtle rule: 20- or 55-day high breakouts, 2-ATR stop or 10-day low).

## Full algorithm

From `sleeves/s_mn_opt_turtle.py` `signal()`:

1. Exit first: for each held option position, look at its underlying's bars (at least 15 bars required). Exit sell_to_close, reason turtle_exit, when either: the last close is below the prior 10-day low (min of closes[-11:-1]) (exit_why 10day_low), or the last close is at or below the entry-day close minus 2 x ATR14, where the entry day is found by entry_date in the bar dates (exit_why 2atr_stop). If any position is held and no exit fires, return with no new entry.
2. Entry (only when flat): scan symbols in sorted order; a symbol breaks out when it has at least 56 bars and its last close exceeds the prior 20-day high (max closes[-21:-1]) or the prior 55-day high (max closes[-56:-1]).
3. For the first breaking-out, non-stale symbol: buy an ATM-ish call, 21-75 DTE by pick_option, sized BUDGET $1,000 of premium via contracts_for(BUDGET, ask), buy_to_open; then stop scanning (one position).
Accounting exit record: {"rule": "Midna plan: opt turtle (shadow)", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time"}.

## Files in this repo

- This package: `docs/LZ_S_MN_OPT_TURTLE-RECREATE.md`
- Strategy code (already in Test): `sleeves/s_mn_opt_turtle.py`
- Adapter (already in Test): `adapters/s_mn_opt_turtle.py`, `integration/s_mn_opt_turtle_adapter.py`
- Dependencies named by the code's imports: `sleeves/laz8_common.py` and `sleeves/laz8_opt.py` (contracts_for, pick_option, underlying_of). Note: files by those exact paths were not found in the Test tree listing taken at batch start and their fetches returned empty; the recreation must supply / locate those modules from the desk engine. This is recorded as a dependency gap, not filled by reconstruction.

## Configuration

- Sleeve id `s_mn_opt_turtle`; cadence_s=300, state_schema {"position": "dict|None"}. BUDGET $1,000, slots 1. Breakout windows 20 and 55 sessions, exit windows 10-day low and 2 x ATR14. Timeframe 1d, shadow per the catalog header.

## Data inputs

Daily bars for the underlyings in the sleeve's universe (closes, timestamps; lookbacks as in the Full algorithm). Option chain data for pick_option / contracts_for selection (ATM-ish, 21-75 DTE per the code header). Accounting data record as in Provenance.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine dependencies for the files listed above (Python, numpy and pandas where those modules require them).
3. Import / register the sleeve or strategy module named in the Files section with the sleeve id and parameters recorded in the Full algorithm and Configuration sections.
4. Serve the data inputs named below and the sleeve's book / position state.
5. Run the desk engine on the cadence recorded in the Configuration section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- When flat, a symbol closing above its prior 20-day or 55-day high (with at least 56 bars) produces exactly one buy_to_open call intent, $1,000 premium budget, and symbols are considered in sorted order.
- A held call exits when the underlying closes below its prior 10-day low or at/below entry close minus 2 x ATR14, and not on other closes.
- While a position is held, no new entry is emitted.
