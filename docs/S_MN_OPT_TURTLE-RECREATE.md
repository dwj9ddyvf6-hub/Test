# s_mn_opt_turtle: Recreation package

Provenance: Source row in strategies/midna/mn-opt-turtle.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset equity options, timeframe 1d, universe Midna's listed surface set, style breakout (options)). The card's Code section states the Midna v3 form in sleeves/s_mn_opt_turtle.py and notes its laz8_opt helper is not in this repo.

## What this sleeve is
This sleeve expresses the Turtle breakout rule in listed options: on a 20- or 55-day closing breakout it buys one at-the-money-ish call with a $1,000 premium budget, and closes it on the Turtle exits (a close below the prior 10-day low, or a close at or below the entry-day close minus 2 x ATR14). One position only. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_opt_turtle.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_opt_turtle.py): BUDGET = 1000.0. CONFIG: sleeve_id s_mn_opt_turtle, cadence_s 300. Option selection (desk sleeves/laz8_opt.py, NOT in this repo per the audit; its rules are stated here from the desk source): calls/puts with 21 to 75 DTE, a two-sided quote with bid > 0 and spread at most 30 percent of mid, candidates ranked by absolute strike distance to spot then absolute DTE distance to 45; contracts_for(budget, ask) = int(budget // (ask x 100)).
Breakout test (_breakout): the symbol needs at least 56 bars; breakout is last close > max of the closes 21 bars back through the bar before last (the prior 20 closes), OR last close > max of the closes 56 bars back through the bar before last (the prior 55 closes).

Evaluation, in code order:
1. Exits first: for each held OCC position, recover its underlying and take its bars; with fewer than 15 bars the position is skipped. closes = the daily closes. If last close < min of the closes 11 bars back through the bar before last (the prior 10 closes), the exit reason is 10day_low. Else, using ATR14 from sleeves/laz8_common atr (mean of the last 14 true ranges) and the entry_date's position in bar_dates, if entry_date is present and last close <= entry-day close - 2 x ATR14, the exit reason is 2atr_stop. On either, emit a full-qty sell_to_close exit, reason turtle_exit with the reason and OCC symbol.
2. If any exit was emitted or anything is held, return (one position).
3. Entries: visit symbols in sorted order; the first symbol passing _breakout is considered: apply the cross-stale gate; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. Pick a call with pick_option at its last close (the laz8_opt selection above); if no call qualifies, continue to the next breaking-out symbol.
4. Contracts: n = contracts_for(1000.0, ask) = int(1000.0 // (ask x 100)); n at or below 0 continues to the next symbol. Emit one buy_to_open entry on the OCC symbol, qty_hint = n, price_hint = the underlying's last close, reason naming the underlying, OCC symbol and ask, then stop.

Position management: one call position at a time; exits are only the two Turtle exits above.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_opt_turtle.py): `sleeves/s_mn_opt_turtle.py`.
- Adapter (desk adapters/s_mn_opt_turtle.py): `adapters/s_mn_opt_turtle.py`; also present as `integration/s_mn_opt_turtle_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Option selection helper (desk sleeves/laz8_opt.py): no repo copy is present (per the audit's missing-shared list); its selection rules are stated in the Full algorithm section.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-opt-turtle.md`.

## Configuration
- Universe: every symbol carried in view bars (Midna's listed surface set upstream). Asset: equity options (long calls). Timeframe: 1d.
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; $1,000 premium budget in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, o, h, l, c}, at least 56 bars for an entry candidate and at least 15 for an exit check. Producer named bars, freshness SLA 900 seconds.
- options: view["options"] {chains, quotes} as described for the laz8 options sleeves, merged by the adapter into context.extra. Producer named options, freshness SLA 900 seconds.
- positions: view["positions"] broker rows (held OCC symbols, with entry_date via opened_at), converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_opt_turtle.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_opt_turtle.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_opt_turtle` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_opt_turtle).
3. Wire the producers so every snapshot carries: daily bars for the candidate universe, the options chains and quotes, and this sleeve's positions. The module also needs sleeves/laz8_opt.py placed in the fresh desk (no repo copy; take it from the desk source tree).
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the breakout: a close equal to (not above) the prior 20- and 55-day maxima produces no entry; a close above either can, and a symbol with 55 bars is never a candidate.
- Check the exits: a held call exits when its underlying closes below the prior 10 closes' minimum, or at or below entry-day close minus 2 x ATR14; a close exactly at the 10-day minimum does not trigger the first exit.
- Check selection order: breaking-out symbols are tried in sorted order, an unpickable or unaffordable call moves to the next symbol, and contracts equal int(1000 // (ask x 100)).
- Check the single position and staleness: any held position suppresses entries, and a breaking-out name whose last bar lags the universe by more than 4 days is skipped.
