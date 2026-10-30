# s_mn_opt_pairs: Recreation package

Provenance: Source row in strategies/midna/mn-opt-distance-pair.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset equity options, timeframe 1d, universe 40 large caps, style pairs (options)). The card's Code section states the Midna v3 form in sleeves/s_mn_opt_pairs.py.

## What this sleeve is
This sleeve expresses the s_mn_pairs distance-pair signal in listed options: when a declared pair's 60-session log-spread is at least 2 standard deviations wide, it buys a call on the cheap leg and a put on the rich leg, $500 of premium per leg, and closes both when the spread reverts. At most one pair package is open. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_opt_pairs.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_opt_pairs.py): PER_LEG = 500.0. It imports PAIRS, ENTRY_Z, EXIT_Z and spread_z from sleeves/s_mn_pairs.py: PAIRS = (("KO", "PEP"), ("XOM", "CVX"), ("JPM", "BAC")), LOOKBACK = 60, ENTRY_Z = 2.0, EXIT_Z = 0.25. CONFIG: sleeve_id s_mn_opt_pairs, cadence_s 300. Option selection (desk sleeves/laz8_opt.py, NOT in this repo per the audit; its rules are stated here from the desk source): calls/puts with 21 to 75 DTE, a two-sided quote with bid > 0 and spread at most 30 percent of mid, candidates ranked by absolute strike distance to spot then absolute DTE distance to 45; contracts_for(budget, ask) = int(budget // (ask x 100)).
Spread (spread_z from s_mn_pairs): both legs need at least 60 bars and matching bar timestamps over the last 60 sessions of the second leg, else the spread is None; spread = log(close of first leg) - log(close of second leg) per session; z = (last spread - mean) / population standard deviation over those 60 spreads; a zero standard deviation gives z = 0.0 at the mean, else +/-99.0.

Evaluation, in code order:
1. Held underlyings are recovered from held OCC symbols by their 1-to-6-letter prefix. If both legs of a declared pair are held, that pair is the active pair: if its z is computable and |z| <= 0.25, emit a sell_to_close exit for both held OCC positions in full, reason spread_reverted with the z. Whether or not it exits, an active pair ends the evaluation (no new package).
2. If anything else is held, return nothing. If no pair is active and nothing is held, visit PAIRS in declared order: skip a pair whose z is None or |z| < 2.0; apply the cross-stale gate to both legs; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated.
3. Leg choice: z > 0 means the first leg is rich and the second cheap; z < 0 reverses them. Pick a put on the rich leg and a call on the cheap leg with pick_option at each leg's last close (the laz8_opt selection above). If either pick fails, move to the next pair.
4. Contracts: n_put = contracts_for(500.0, put ask), n_call = contracts_for(500.0, call ask); if either is at or below 0, move to the next pair. Emit two buy_to_open entries, call first then put, reasons naming the underlying, OCC symbol and z, then stop (one package only).

Position management: one pair package at a time; the only exit is |z| <= 0.25 on the active pair; there is no expiry or price exit in this module beyond what the desk does with the contracts themselves.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_opt_pairs.py): `sleeves/s_mn_opt_pairs.py`.
- Adapter (desk adapters/s_mn_opt_pairs.py): `adapters/s_mn_opt_pairs.py`; also present as `integration/s_mn_opt_pairs_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Pair rule source imported by the module (desk sleeves/s_mn_pairs.py): `sleeves/s_mn_pairs.py`.
- Option selection helper (desk sleeves/laz8_opt.py): no repo copy is present (per the audit's missing-shared list); its selection rules are stated in the Full algorithm section.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-opt-distance-pair.md`.

## Configuration
- Universe: the declared pairs KO/PEP, XOM/CVX, JPM/BAC, traded as listed options on those underlyings. Asset: equity options. Timeframe: 1d.
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; $500 premium budget per leg in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c} for the six pair underlyings, at least 60 sessions. Producer named bars, freshness SLA 900 seconds.
- options: view["options"] {chains, quotes}: chains {underlying: [{symbol, strike, expiration, type}]} and quotes {OCC: {bid, ask}}, merged by the adapter into context.extra. Producer named options, freshness SLA 900 seconds.
- positions: view["positions"] broker rows (held OCC symbols), converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_opt_pairs.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_opt_pairs.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_opt_pairs` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_opt_pairs).
3. Wire the producers so every snapshot carries: daily bars for the pair underlyings, the options chains and quotes, and this sleeve's positions. The module also needs sleeves/s_mn_pairs.py and sleeves/laz8_opt.py placed in the fresh desk (laz8_opt has no repo copy; take it from the desk source tree).
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the spread: a pair with fewer than 60 matched sessions produces no entry; |z| of 1.99 produces no entry and 2.00 can.
- Check leg direction: a positive z buys a put on the first leg and a call on the second; a negative z reverses the underlyings assigned to put and call.
- Check option selection and sizing: only 21-to-75 DTE contracts with bid > 0 and spread at most 30 percent of mid are picked, the strike nearest spot wins, and contracts equal int(500 // (ask x 100)) per leg.
- Check the exit and single package: a held pair at |z| <= 0.25 exits both OCC positions in full, a held pair above that emits nothing, and no second package opens while one is held.
