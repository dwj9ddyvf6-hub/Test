# lz_s_mn_opt_reversal: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Midna Opt Reversal (Midna port)", type options directional, family 1d. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. The accounting records the entry policy and exit rule quoted below; the running Test code supplies the selection, budget and exit mechanics.
- No Test catalog entry in the accounting (test_entries empty); alias source md2_catalog, status installed.
- Accounting wrapper records: entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; data: sleeve_midna (entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Running code in Test (verified at batch start): the sleeve module named in the Files section, with its adapter.

## What this strategy is

Options form of the reversal rule (last month's worst large caps), shadow, $1,000 (catalog rule in the code header: Options, 1D, Shadow, entry 'Reversal traded with listed options', exit 'Rotation exit', $1,000; catalog slots=1 for the options form, the equity form runs 3).

## Full algorithm

From `sleeves/s_mn_opt_reversal.py` `signal()`:

1. Exit first: for each held option position, if sessions_held (sessions since its entry_date on the underlying's bars) >= HOLD 21, exit sell_to_close at the held quantity, reason rotation_21_sessions. If any position is held and no exit fires, return with no new entry.
2. Entry (only when flat): score every symbol in the bars mapping with at least LOOKBACK+1 = 22 bars by its 21-session return closes[-1] / closes[-22] - 1; take the single worst performer (scored list sorted ascending, first element).
3. If that symbol is stale-refused, return. Otherwise buy an ATM-ish call on it, 21-75 DTE by pick_option, sized BUDGET $1,000 of premium via contracts_for(BUDGET, ask), buy_to_open. If no pick or zero contracts, no entry.
Accounting exit record: {"rule": "Midna plan: opt reversal (shadow)", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time"}.

## Files in this repo

- This package: `docs/LZ_S_MN_OPT_REVERSAL-RECREATE.md`
- Strategy code (already in Test): `sleeves/s_mn_opt_reversal.py`
- Adapter (already in Test): `adapters/s_mn_opt_reversal.py`, `integration/s_mn_opt_reversal_adapter.py`
- Dependencies named by the code's imports: `sleeves/laz8_common.py` and `sleeves/laz8_opt.py` (contracts_for, pick_option, underlying_of). Note: files by those exact paths were not found in the Test tree listing taken at batch start and their fetches returned empty; the recreation must supply / locate those modules from the desk engine. This is recorded as a dependency gap, not filled by reconstruction.

## Configuration

- Sleeve id `s_mn_opt_reversal`; cadence_s=300, state_schema {"position": "dict|None"}. BUDGET $1,000, LOOKBACK 21, HOLD 21, slots 1. Timeframe 1d, shadow per the catalog header.

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

- When flat, the call bought is on the worst 21-session performer among symbols with at least 22 bars, and on no other symbol.
- A held call exits sell_to_close once 21 sessions have been held, and not before.
- While a position is held, no new entry is emitted.
