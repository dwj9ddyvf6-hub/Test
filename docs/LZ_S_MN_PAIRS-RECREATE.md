# lz_s_mn_pairs: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Midna Pairs (Midna port)", type pairs and statistical arbitrage, family 1d. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. The accounting records the entry policy and exit rule quoted in the Full algorithm; the running Test code below supplies the pair list, thresholds and sizing.
- No Test catalog entry in the accounting (test_entries empty); alias record source md2_catalog, status installed.
- Running code in Test (verified at batch start by tree listing and file read): `sleeves/s_mn_pairs.py`, adapter `adapters/s_mn_pairs.py` (also `integration/s_mn_pairs_adapter.py`).

## What this strategy is

Distance pairs traded as a Midna port: for declared same-sector liquid large-cap pairs, the 60-session log-spread z-score mean-reversion rule from the code header (Gatev distance method reading).

## Full algorithm

Evaluation order, from `sleeves/s_mn_pairs.py` `signal()`:

1. Compute `spread_z` for each declared pair: spread = log(close A) - log(close B) over the trailing 60 sessions aligned by timestamp; z = (last spread - mean) / population standard deviation. If either leg has fewer than 60 bars, or a timestamp is missing, z is None and the pair is skipped. If the standard deviation is 0, z is 0 when the last spread equals the mean, otherwise +99 / -99 by direction.
2. Exit first: if both legs of a pair are held and |z| <= EXIT_Z 0.25, exit both legs at their held quantities (buy_to_close for a short leg, sell_to_close for a long leg), reason spread_reverted.
3. Count open pairs; if open pairs >= MAX_PAIRS 3, return with no new entries.
4. Entry: for each pair with neither leg held, in PAIRS order, if |z| >= ENTRY_Z 2.0 and neither leg is refused as stale (xstale_refused, ENH20), open: z > 0 means A is rich, so short A and long B; z < 0 reverses the legs. Each leg is sized PER_LEG $500 (a $1,000 pair), quantity = qty_for($500, last close).
5. Declared PAIRS, in order: (KO, PEP), (XOM, CVX), (JPM, BAC). The code header records that the catalog named no pairs and these desk pairs are recorded in the fidelity ledger as a desk-chosen universe; do not present them as catalog pairs.

Accounting wrapper records (md2 catalog, distinct from the running signal above): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: pairs z-score mean-revert exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}. In the running code there is no price stop beyond the z exit; stop_pct 99.0 in the plan record is effectively no stop.

## Files in this repo

- This package: `docs/LZ_S_MN_PAIRS-RECREATE.md`
- Strategy code (already in Test): `sleeves/s_mn_pairs.py`
- Adapter (already in Test): `adapters/s_mn_pairs.py`, `integration/s_mn_pairs_adapter.py` (DEFAULT_EQUITY 3000.0, inputs bars and positions)
- Dependencies named by the code's imports: `sleeves/laz8_common.py` (Intent, SleeveConfig, held_positions, qty_for, xstale_refused). Note: a file by that exact path was not found in the Test tree listing taken at batch start and its fetch returned empty; the recreation must supply / locate that module from the desk engine before the sleeve module can import. This is recorded as a dependency gap, not filled by reconstruction.

## Configuration

- Sleeve id in running code: `s_mn_pairs` (canonical accounting id `lz_s_mn_pairs`). Cadence: SleeveConfig cadence_s=300. State schema: {"position": "dict|None"}.
- LOOKBACK 60, ENTRY_Z 2.0, EXIT_Z 0.25, PER_LEG $500, MAX_PAIRS 3; adapter DEFAULT_EQUITY $3,000 (3 slots x $1,000, matching the code header: 3 slots, $3,000).
- Universe: the three declared pairs above; timeframe 1d in the catalog reading.

## Data inputs

Daily bars for KO, PEP, XOM, CVX, JPM, BAC (closes and timestamps, at least 60 sessions per leg). Accounting filter record: data sleeve_midna (entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json. Adapter inputs: bars, positions.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine dependencies for the files listed above (Python, numpy and pandas where those modules require them).
3. Import / register the sleeve or strategy module named in the Files section with the sleeve id and parameters recorded in the Full algorithm and Configuration sections.
4. Serve the data inputs named below and the sleeve's book / position state.
5. Run the desk engine on the cadence recorded in the Configuration section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- With a pair's 60-session log-spread at |z| >= 2.0 and neither leg held, exactly two entry intents are produced: long the cheap leg and short the rich leg, $500 per leg.
- With both legs held and |z| <= 0.25, both legs exit; with |z| > 0.25 a held pair does not exit.
- A fourth pair never opens (MAX_PAIRS 3); a pair with fewer than 60 aligned bars produces no intent.
- A stale leg (xstale_refused) blocks that pair's entry.
