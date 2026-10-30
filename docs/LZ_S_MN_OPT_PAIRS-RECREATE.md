# lz_s_mn_opt_pairs: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Midna Opt Pairs (Midna port)", type options directional, family 1d. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. The accounting records the entry policy and exit rule quoted below; the running Test code supplies the selection, budget and exit mechanics.
- No Test catalog entry in the accounting (test_entries empty); alias source md2_catalog, status installed.
- Accounting wrapper records: entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; data: sleeve_midna (entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Running code in Test (verified at batch start): the sleeve module named in the Files section, with its adapter.

## What this strategy is

Options form of the s_mn_pairs distance rule, traded with listed options, shadow, $1,000 total (catalog rule in the code header: Options, 1D, Shadow, entry 'Pairs traded with listed options', exit 'Spread reverts', $1,000).

## Full algorithm

From `sleeves/s_mn_opt_pairs.py` `signal()`:

1. Pairs, lookback, thresholds are imported from `sleeves/s_mn_pairs.py`: PAIRS (KO, PEP), (XOM, CVX), (JPM, BAC); ENTRY_Z 2.0, EXIT_Z 0.25, spread_z over 60 sessions (see the LZ_S_MN_PAIRS package for the spread_z definition).
2. Exit first: if both underlyings of a pair are held as options, compute z; if |z| <= 0.25, exit both legs sell_to_close at held quantities, reason spread_reverted. If any option position is held and no exit fires, return with no new entry.
3. Entry: for the first pair (in PAIRS order) with |z| >= 2.0 and neither leg stale-refused: the rich leg (z > 0: A rich; otherwise B rich) gets a bought put and the cheap leg a bought call, each selected ATM-ish, 21-75 DTE by pick_option (laz8_opt selection in the code header), sized PER_LEG $500 of premium budget per leg via contracts_for(PER_LEG, ask). If either pick or contract count is empty / zero, the pair is skipped.
4. Only one pair is entered per evaluation (break after the first qualifying pair). Accounting exit record: {"rule": "Midna plan: opt pairs (shadow)", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time"}.

## Files in this repo

- This package: `docs/LZ_S_MN_OPT_PAIRS-RECREATE.md`
- Strategy code (already in Test): `sleeves/s_mn_opt_pairs.py`
- Adapter (already in Test): `adapters/s_mn_opt_pairs.py`, `integration/s_mn_opt_pairs_adapter.py`
- Dependencies named by the code's imports: `sleeves/laz8_common.py` and `sleeves/laz8_opt.py` (contracts_for, pick_option, underlying_of). Note: files by those exact paths were not found in the Test tree listing taken at batch start and their fetches returned empty; the recreation must supply / locate those modules from the desk engine. This is recorded as a dependency gap, not filled by reconstruction.

## Configuration

- Sleeve id `s_mn_opt_pairs`; SleeveConfig cadence_s=300, state_schema {"position": "dict|None"}. PER_LEG $500 premium per leg ($1,000 total). One active pair at a time in practice (held positions block new entries). Timeframe 1d, shadow per the catalog header.

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

- With |z| >= 2.0 on a declared pair and no positions held, two buy_to_open intents open: a put on the rich leg and a call on the cheap leg, each about $500 of premium.
- With both legs held and |z| <= 0.25, both legs exit sell_to_close; with |z| > 0.25 they do not.
- With any option position held, no new pair entry is emitted.
