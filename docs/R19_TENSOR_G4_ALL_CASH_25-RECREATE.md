# R19_TENSOR_G4_ALL_CASH_25: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor green value / recovery · cash funded, all volatility, 25 positions", type "forecast and ML models", family "G4". Algorithm grade FULL (sources: ausar_map params/variant; md2 catalog entry/exit/strategy text). Universe, asset class, timeframe and creator are not recorded in the consulted sources for this entry.
- Accounting parameters for this variant: family G4, capital_mode cash, volatility all, slots 25, ticket 4000 (source book), fee_bps 10.
- Aliases: `R19_TENSOR_G4_ALL_CASH_25`, `ausar_pb138`.
- Code search (this package): fresh trees of Test, Silicon, quant-research-backup and Midna were searched at batch start for the canonical id, its alias and the Tensor family terms. No code for this id was found in Silicon, quant-research-backup or Midna; the code below is already in Test (the v3 wrapper/engine port and the master-desk R19 Tensor family port).

## What this strategy is

A long-only equity book in the R19 Tensor G4 family. It consumes canonical Tensor v698 buy fires through the desk's Tensor bundle fire channel (signal generation is the Tensor bundle's; this book implements the fire gating, sizing and exit rules) and holds each position to a 52nd-calendar-week deadline. This variant is distinguished by: capital mode cash, volatility cut all, 25 positions.

## Full algorithm

From the ALL-SLEEVES accounting entry and the code in Test (`desk3/aster_batch14.py` SPECS row for `aster_tensor_g4_cash_all_25` and its evaluate logic), in evaluation order:

1. Exits are evaluated first; if any exit is emitted, no entry is evaluated in the same pass.
2. Entry gates: a Tensor bundle fire with 'buy-green' in its primary markers (or 'green' in its signal); fire price <= 10; depth60 >= 70; ret60 >= 0; vol20 >= 0.09; average dollar volume >= $2,000,000.
3. Volatility: "all"; no atr_ratio split is applied.
4. Capital mode cash: entries may act on a fire in the current session, funded from sleeve cash; no extra-session delay.
5. Execution-price revalidation (enhancement, on by default in the v3 engine): when a current bar is available, the family price cap (<= 10) is revalidated against the latest close; a current close above the cap refuses the entry, and sizing uses the latest close; the fire-price decision is kept as the paired shadow control record.
6. Sizing: at most one entry per evaluation pass, into a symbol not already held, while fewer than 25 distinct symbols are held. qty = floor(ticket / entry price); qty < 1 emits nothing. Source book ticket $4,000; the v3 port in Test scales it to $400 on its $10,000 slice (engine ticket constant). Orders are market, day, buy_to_open in the v3 port.
7. Exit (accounting, source-exact): exit five minutes before the final market session closes in the 52nd calendar week, counting the originally scheduled entry week as week one; holidays and early closes follow the exchange calendar. There is no price stop or profit target. The v3 port models this deadline as HOLD_SESSIONS = 260 sessions held and sells the full position ("week52_deadline").

## Files in this repo

- This doc: `docs/R19_TENSOR_G4_ALL_CASH_25-RECREATE.md`
- Algorithm doc derived from the code in Test: `docs/ASTER_TENSOR_G4_CASH_ALL_25-ALGORITHM.md`
- Code (already in Test): `sleeves/aster_tensor_g4_cash_all_25.py`, `adapters3/aster_tensor_g4_cash_all_25.py`, `integration/aster_tensor_g4_cash_all_25_adapter.py` (thin wrappers: evaluate delegates to the shared engine), shared engine `desk3/aster_batch14.py` (SPECS row for `aster_tensor_g4_cash_all_25`), and the master-desk R19 Tensor family port `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_tensor.py` (the 22-book R19 Tensor registry, its configs and divergences).
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Family: G4. Capital mode: cash. Volatility cut: all. Slots: 25 distinct symbols.
- Ticket: $4,000 on the source book (accounting fee_bps 10); v3 port ticket $400 on a $10,000 slice.
- Hold: 52nd calendar week deadline (v3 model: 260 sessions).
- Universe, timeframe and cadence: not in the record in the accounting entry; the v3 engine declares inputs tensor / bars / positions and no cadence or session row for the Tensor rows.

## Data inputs

- Completed daily/weekly bars and canonical Tensor v698 features (accounting).
- v3 declared inputs (INPUTS_TENSOR / engine INPUTS): tensor, bars, positions. Producers named in the engine: tensor_bundle (86400s freshness, outputs tensor), bars (900s), broker_readback (900s, positions). With no tensor key in the snapshot the registry marks the sleeve UNFED, never fake-fed.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `R19_TENSOR_G4_ALL_CASH_25` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/aster_tensor_g4_cash_all_25.py` and the SPECS row for `aster_tensor_g4_cash_all_25` in `desk3/aster_batch14.py`; confirm family, capital_mode, volatility, slots and ticket match Configuration above.
4. Provide the data inputs listed above (a Tensor bundle fire feed, bars and a positions readback).
5. Call the wrapper's `evaluate(view, ctx)` per pass; exits are produced before entries by construction.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A fire failing any entry gate in step 2 (including the price cap) produces no entry.
- The volatility rule in step 3 is applied exactly: no atr_ratio gate is applied; a fire with no atr_ratio still enters if the other gates pass.
- A same-session fire may enter (cash mode).
- qty equals floor(ticket / entry price), at most one entry per pass, and entries stop at 25 distinct held symbols.
- A position held 260 sessions (v3 model) is sold in full with reason week52_deadline, and no entry is emitted in a pass that emits an exit.
- No price stop or profit target ever emits an exit.
