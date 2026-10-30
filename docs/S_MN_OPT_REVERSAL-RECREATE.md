# s_mn_opt_reversal: Recreation package

Provenance: Source row in strategies/midna/mn-opt-reversal.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset equity options, timeframe 1d (monthly), universe 40 large caps, style mean reversion (options)). The card's Code section states the Midna v3 form in sleeves/s_mn_opt_reversal.py.

## What this sleeve is
This sleeve expresses the s_mn_reversal rule in listed options: it buys one at-the-money-ish call on the single worst prior-21-session large cap in the snapshot universe, with a $1,000 premium budget, and closes it at the 21-session rotation. One position only. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_opt_reversal.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_opt_reversal.py): BUDGET = 1000.0, LOOKBACK = 21, HOLD = 21. CONFIG: sleeve_id s_mn_opt_reversal, cadence_s 300. Option selection (desk sleeves/laz8_opt.py, NOT in this repo per the audit; its rules are stated here from the desk source): calls/puts with 21 to 75 DTE, a two-sided quote with bid > 0 and spread at most 30 percent of mid, candidates ranked by absolute strike distance to spot then absolute DTE distance to 45; contracts_for(budget, ask) = int(budget // (ask x 100)).
Evaluation, in code order:
1. Exits first: for each held OCC position, recover its underlying from the OCC prefix and take that underlying's bars; if sessions held (bars strictly after entry_date) >= 21, emit a full-qty sell_to_close exit, reason rotation_21_sessions with the OCC symbol.
2. If any exit was emitted or anything is held, return (one position).
3. Ranking: for every symbol in bars with at least 22 bars, return21 = last close / close 21 bars earlier - 1. Sort ascending (return, then symbol order from the sorted scan); the worst performer is the first. No scored symbol means no entry.
4. Apply the cross-stale gate to the worst name; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. Pick a call on it with pick_option at its last close (the laz8_opt selection above). No pick means no entry.
5. Contracts: n = contracts_for(1000.0, ask) = int(1000.0 // (ask x 100)); n at or below 0 means no entry. Emit one buy_to_open entry on the OCC symbol, qty_hint = n, price_hint = the underlying's last close (the spot, not the ask), reason naming the underlying, OCC symbol and ask.

Position management: one call position at a time; the only exit is the 21-session rotation.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_opt_reversal.py): `sleeves/s_mn_opt_reversal.py`.
- Adapter (desk adapters/s_mn_opt_reversal.py): `adapters/s_mn_opt_reversal.py`; also present as `integration/s_mn_opt_reversal_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Option selection helper (desk sleeves/laz8_opt.py): no repo copy is present (per the audit's missing-shared list); its selection rules are stated in the Full algorithm section.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-opt-reversal.md`.

## Configuration
- Universe: every symbol carried in view bars (producer-defined large-cap set; the catalog names no tickers). Asset: equity options (long calls). Timeframe: 1d.
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; $1,000 premium budget in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c}, at least 22 bars per candidate. Producer named bars, freshness SLA 900 seconds.
- options: view["options"] {chains, quotes} as described for the laz8 options sleeves, merged by the adapter into context.extra. Producer named options, freshness SLA 900 seconds.
- positions: view["positions"] broker rows (held OCC symbols), converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_opt_reversal.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_opt_reversal.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_opt_reversal` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_opt_reversal).
3. Wire the producers so every snapshot carries: daily bars for the candidate universe, the options chains and quotes, and this sleeve's positions. The module also needs sleeves/laz8_opt.py placed in the fresh desk (no repo copy; take it from the desk source tree).
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the ranking: the entered underlying is the lowest prior-21-session return among symbols with at least 22 bars; a symbol with 21 bars is not scored.
- Check the exit: a held call whose underlying shows 21 sessions after entry_date exits in full; at 20 sessions it is held and no new call opens.
- Check option selection and sizing: only 21-to-75 DTE calls with bid > 0 and spread at most 30 percent of mid are picked, the strike nearest spot wins, contracts equal int(1000 // (ask x 100)), and no qualifying call means no entry.
- Check staleness: a worst name whose last bar lags the universe by more than 4 days produces no entry.
