# R19_TENSOR_BETA_M2_52W_25: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Tensor relative-market cohort - cash funded, all volatility, 25 positions", type forecast and ML models, family BETA. Algorithm grade FULL, sources ausar_map params/variant and md2 catalog entry/exit/strategy text. Parameters recorded: family BETA, capital_mode cash, volatility all, slots 25, ticket 4000, fee_bps 10. Aliases: `R19_TENSOR_BETA_M2_52W_25`, `ausar_pb127`.
- Test implementation record: `docs/ASTER_TENSOR_BETA_CASH_ALL_25-ALGORITHM.md` (algorithm derived from the sleeve code on 2026-10-29) for the corresponding Test sleeve `aster_tensor_beta_cash_all_25`, whose SPECS match on family BETA, capital_mode cash, volatility all and slots 25; its ticket is recorded there as $400, described as the $4,000 source book ticket scaled to the $10k slice. Both values are in the record and are kept distinct here.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Trades long stock positions from Tensor bundle fires in the M2-qualified relative-market cohort, 25 slots, cash funded, exiting at the 52nd-week deadline.

## Full algorithm

Accounting algorithm (ausar_pb127) plus the Test algorithm doc, in evaluation order:

1. Data / filter: completed weekly symbol/SPY bars and canonical Tensor v698 features. Builds the canonical M2-qualified weekly cohort, compares it with SPY and selects the configured beta cohort after consolidating issuer aliases. It is a relative-market selection experiment, not a guarantee of market outperformance.
2. Exits are evaluated first; if any exit is emitted, no entry is evaluated in the same pass (Test doc).
3. Entry: one entry per evaluation pass, into a symbol not already held, while fewer than 25 distinct symbols are held. BETA entry: a Tensor bundle fire from the M2-qualified relative-market cohort ('beta' or 'm2' in the signal name, or an m2_qualified flag that is not False). Volatility 'all': no atr_ratio split. Capital mode cash: entries may act on a fire in the current session, funded from sleeve cash.
4. Fire-age enhancement (on by default, Test doc): fires older than 1 day, or future-dated, are refused as stale. Stale-fire pricing enhancement (on by default): when a current bar is available, the price cap is revalidated against the latest close and sizing uses the latest close.
5. Sizing: accounting ticket 4000 with fee_bps 10; Test implementation qty = floor($400 / entry price) (the scaled ticket), qty < 1 emits nothing.
6. Exit: five minutes before the final market session closes in the 52nd calendar week, counting the originally scheduled entry week as week one (accounting); modelled in Test as 260 sessions held, full position sold ('week52_deadline'). Holidays and early closes follow the exchange calendar. No price stop or profit target.

## Files in this repo

- This doc: `docs/R19_TENSOR_BETA_M2_52W_25-RECREATE.md`
- Test algorithm doc: `docs/ASTER_TENSOR_BETA_CASH_ALL_25-ALGORITHM.md`
- Strategy / algorithm doc in Test: see Provenance.
- Code (already in Test): `sleeves/aster_tensor_beta_cash_all_25.py` / `sleeves/aster_tensor_c1_cash_all_25.py` as applicable (thin wrapper, SLEEVE_ID set, evaluate delegates), shared engine `desk3/aster_batch13.py`, plus the same wrapper under `adapters3/` and `integration/`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; rule lines: `docs/verify/ausar.md`

## Configuration

- Family BETA, capital_mode cash, volatility all, slots 25, ticket 4000 (source book; $400 in the Test $10k slice), fee_bps 10.
- Hold: 52 calendar weeks / 260 sessions. No cadence or session row is defined for the tensor rows in desk3/aster_batch13.py itself (Test doc).

## Data inputs

- Declared inputs (INPUTS_TENSOR): tensor, bars, positions. Producers in the engine: bars (900s freshness), tensor_bundle (86400s, outputs tensor), broker_readback (900s, positions). With no tensor key in the snapshot the registry marks the sleeve UNFED, never fake-fed.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Wire the Tensor bundle, bars and broker-readback producers named in Data inputs; without a tensor key the sleeve is UNFED and must not trade.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Exits are evaluated before entries and an exit pass emits no entry.
- At most one entry per pass, never into a held symbol, never beyond 25 distinct symbols.
- A fire without 'beta'/'m2' in its name and without a non-False m2_qualified flag produces no entry; a fire older than 1 day or future-dated is refused.
- The full position is sold at the 52nd-week / 260-session deadline, with no earlier price stop or profit target.
