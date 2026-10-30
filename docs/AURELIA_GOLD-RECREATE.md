# aurelia_gold: Recreation package

Provenance: Source row in strategies/femto/femto-aurelia.md in this repo: Aurelia (Agentic-Trading-Desk paper desk), via Femto-lean; also APEX round 3 C1 (the AURELIA pair) (family Femto-lean, asset US ETFs (incl. 3x leveraged), timeframe 1d, universe QQQ, TQQQ, GLD, BIL, style trend x volatility targeting).

## What this sleeve is
This sleeve is the gold leg of the two-sleeve Aurelia allocation book: it holds GLD one for one against the band-resolved, gross-capped gold exposure from signal aurelia-gc-band20-v1, sizing off broker-refreshed account equity. Only GLD deltas are emitted here; the QQQ, TQQQ and BIL deltas of the same book belong to aurelia_ndx. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/aurelia_gold.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/aurelia_gold.py): SIGNAL_ID = "aurelia-gc-band20-v1", ACCOUNT = "aurelia_gold", SYMBOLS = ("QQQ", "TQQQ", "GLD", "BIL"), EXPOSURE_BAND = 0.20, GROSS_CAP = 1.80, NDX_CAP = 3.0, MIN_WEIGHT = 0.02. CONFIG: sleeve_id aurelia_gold, cadence_s 300, universe ("GLD",), risk_pct None.

Band resolution (resolve_book, verbatim in both modules): the raw signal and prior book values are sanitised (non-numeric or non-finite becomes 0.0, negatives clamp to 0.0); if the signal is 0.0 and the book is above 0.0 the book goes to 0.0 at once; otherwise the book moves to the signal only when the absolute move is at least EXPOSURE_BAND = 0.20 (within 1e-12), else it keeps the prior book value. Posture: when extra posture_cap is present, the Nasdaq book is capped at min(book, posture_cap), with an unreadable cap capping to zero (fail closed); gold is never posture-capped.
Weights (sleeve_weights): cap_exposures first clamps Nasdaq to [0, NDX_CAP = 3.0] and gold to at least 0, then, when the capital measure (Nasdaq capital used plus gold, per _capital) exceeds GROSS_CAP = 1.80, both exposures are scaled down together by bisection (40 iterations) until the cap holds. If Nasdaq is at most 1.0, weights are QQQ = ndx and TQQQ = 0; otherwise TQQQ = (ndx - 1.0) / 2 and QQQ = 1.0 - TQQQ, so capital used by Nasdaq is 1.0 while its exposure (QQQ + 3 x TQQQ) reaches ndx. GLD weight = gold. The residual cash weight (1.0 minus capital used) becomes BIL only when it is at least MIN_WEIGHT = 0.02, else BIL = 0. Weights are rounded to 6 decimals and zero weights are dropped.
Share targets: qty = int(equity x weight / last close) per symbol with a positive price and weight; zero targets are dropped. Deltas (order_deltas, band = MIN_WEIGHT = 0.02): a new name always trades; a held name trades only when its target-versus-held notional move is at least 2 percent of equity; the delta is want minus have. Buying-power fit (only when extra buying_power is present): sells are untouched, buys are scaled proportionally to 95 percent of buying power and dropped entirely when there is no room (fit_to_buying_power, buffer 0.95).

This sleeve's evaluation, in code order:
1. Fail closed on inputs: extra exposures must be a dict containing both ndx and gold, otherwise no intents. The sizing basis is context.equity (broker-refreshed account equity); equity at or below 0 or unreadable makes the sleeve inert.
2. Holdings come from extra sleeve_state ({symbol: {"qty": n}}); prices are the last bar closes for SYMBOLS, keeping only finite positive closes. No GLD price means no intents.
3. Resolve both books (the Nasdaq book is resolved too because it consumes gross capital alongside gold, and the posture cap is applied to it here exactly as in the module), compute weights, share targets and deltas, then apply the buying-power fit when extra buying_power is present.
4. Emit only the GLD order: a buy delta becomes an enter intent and a sell delta an exit intent, qty_hint = the absolute delta, price_hint = the GLD last close rounded to 2 decimals, with the reason naming the account, book_gold and the signal id (plus bp_fit=scaled95 when the buying-power fit scaled the orders).

Position management: target-following only; there is no stop, target price or time exit in this module beyond moving to the next band-resolved target.

## Files in this repo
- Sleeve module (desk sleeves/aurelia_gold.py): `sleeves/aurelia_gold.py`.
- v3 adapter (desk adapters3/aurelia_gold.py): `adapters3/aurelia_gold.py`; also present as `integration/aurelia_gold_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- No separate engine file: the full logic is in `sleeves/aurelia_gold.py` itself (audit engine_files_needed is empty for this sleeve).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-aurelia.md`.

## Configuration
- Universe: GLD for this sleeve's orders; the shared book symbols are QQQ, TQQQ, GLD, BIL (the exposures and gross cap are computed over the whole book). Asset: US ETFs. Timeframe: 1d (daily signal aurelia-gc-band20-v1).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; execution sizing is off context.equity (account equity), not the slice, per the module header (AURELIA-EXEC).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- exposures: context.extra["exposures"] {"ndx", "gold"} raw signal values, required; supplied by core.book_feeds from the aurelia-gc-band20-v1 producer (core/aurelia_signal.py), per the module header.
- book and posture_cap: context.extra["book"] prior band state and context.extra["posture_cap"] (Nasdaq only).
- sleeve_state and buying_power: context.extra["sleeve_state"] held quantities and context.extra["buying_power"] when present.
- bars: last closes for QQQ, TQQQ, GLD and BIL; positions arrive through the snapshot context the adapter rebuilds.

## Install and run
1. Place the sleeve module at sleeves/aurelia_gold.py and the adapter at adapters3/aurelia_gold.py (repo copies at the same paths). The module needs the desk BaseSleeve / SleeveConfig / Intent plumbing it imports in the fresh desk.
2. Register the roster row for `aurelia_gold` exactly as in the Configuration section in config/sleeves.json (module adapters3.aurelia_gold).
3. Wire the producers so every snapshot carries: daily bars for QQQ, TQQQ, GLD and BIL, this sleeve's positions, context.equity, and extra exposures (ndx and gold), book, sleeve_state, and buying_power when available.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check fail-closed behaviour: missing exposures, a missing gold key, equity at or below 0, or no GLD price each produce no intents.
- Check the band: a gold signal moving less than 0.20 from the prior book keeps the prior book value; a move of at least 0.20 adopts the signal; a zero signal flattens the book at once.
- Check the caps and weights: Nasdaq above 3.0 is clamped, a book over the 1.80 gross cap is scaled down proportionally, GLD weight equals the capped gold exposure, and BIL appears only when the residual cash weight is at least 0.02.
- Check emission scope and deltas: only GLD intents are emitted, a held GLD position whose target move is under 2 percent of equity emits nothing, and with buying_power present the buys are scaled to 95 percent of it.
