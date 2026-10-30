# R19_TENSOR_G4_RED_TIMEOUT_25: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor green value / recovery · dip-or-five-session wait, all volatility, 25 positions", type forecast and ML models, family G4. Algorithm grade FULL in the accounting, sources ausar_map params/variant and md2 catalog entry/exit/strategy text. Recorded parameters for this book: {"family": "G4", "capital_mode": "red_timeout", "volatility": "all", "slots": 25, "ticket": 4000, "fee_bps": 10}. Alias `ausar_pb148` (ausar_map row: alias 'Paper book' row listing the r19 link R19_TENSOR_G4_RED_TIMEOUT_25; alias status in the accounting: md2_ausar_map present in roster, ausar_deployed mode=independent_local_paper running=False; the alias itself replaced in md2_catalog). No Test catalog entry for the R19 id itself (test_entries empty); the family card and the v3 rows are in Test (below).
- Family card in Test: `strategies/ausar/r19-tensor-g4.md` ("R19 weekly Tensor G4 green ownership": buys cheap, deeply drawn-down stocks on a weekly Tensor buy-green print and holds each for 52 weeks; universe frozen 1,838-name research cohort; US equities; timeframe 1w; variants axes volatility all/cool/hot, capital mode cash/delay/reserve/red_timeout, slots 25/10). The Source row of that card names an archived v615 engine; a codename token in that row is omitted here under the repo PII rule.
- Original-book code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_tensor.py`. Its header states the 22 R19 tensor books (G4 and C1 in all/cool/hot volatility cuts and cash/delay/reserve capital modes, the 10-slot G4 pair, and G4_RED_TIMEOUT) run the vendored, hash-pinned source `backend/r19_tensor.py` register() configs end to end, each book held to the last session of the 52nd calendar week, sold 5 minutes before its close, with the R19 ledger execution rules (price-tiered fees 30 / 15 / 10 bps, QQQ 10; whole shares at the ask/bid; settled-cash cap; T+1 settlement). Its SleeveConfig for a book carries family, volatility, capital_mode, slots and ticket from the register() config.
- v3 implementation in Test: sleeve wrapper `sleeves/aster_r19_tensor_g4_red_timeout_25.py` (also `adapters3/aster_r19_tensor_g4_red_timeout_25.py` and `integration/aster_r19_tensor_g4_red_timeout_25_adapter.py`) delegating to the shared engine `desk3/aster_batch15.py`, documented in Test at `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b23_Test_tree.txt in the run workspace) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, adapters3/, integration/, desk3/, packages/, strategies/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for these ids (no aster_tensor, aster_r19 or r19_tensor filename in any of those three trees).

## What this strategy is

A Tensor green value / recovery book: dip-or-five-session wait (red_timeout), all volatility, 25 positions. It buys cheap, deeply drawn-down US stocks on a weekly Tensor buy-green print and holds each position for 52 weeks. This canonical id is the original R19 book (ticket $4,000 on a $100,000 book); the v3 sleeve `aster_r19_tensor_g4_red_timeout_25` in Test is the same book on a $10,000 v3 slice (ticket $400).

## Full algorithm

Original book, in evaluation order (accounting record plus the family card in Test):

1. Signal and gates: a candidate must satisfy all of: canonical buy-green event (weekly Tensor buy-green primary marker); price at most $10; depth60 at least 70; nonnegative ret60 (60-session return >= 0); vol20 at least 0.09; average dollar volume (dv20) at least $2,000,000. Volatility split: none; the fire's atr_ratio is not gated.
2. Coverage and ranking (family card): needs at least 99% census and feature coverage; ranks by 20-day dollar volume; one position per issuer.
3. Capital-mode timing (red_timeout): red_timeout waits up to 5 sessions for a QQQ red day with the stock at or below 1.02 x signal close (family card); on the first red session, or at the 5th scanned session (timeout), entry is set to the next session (v3 record).
4. Sizing: ticket = $4,000 (= $100,000 / 25 slots in the family card's sizing rule), whole shares; fees 30 / 15 / 10 bps by price in the R19 ledger reading (the accounting parameter row records fee_bps 10 for this book). Entries stop once 25 positions are held.
5. Exit: Exit five minutes before the final market session closes in the 52nd calendar week, counting the originally scheduled entry week as week one. Holidays and early closes follow the exchange calendar. There is no price stop or profit target.

v3 implementation in Test (desk3/aster_batch15.py; see `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md` for the per-sleeve record):

This sleeve's SPECS entry (desk3/aster_batch15.py): family="G4", mode="red_timeout", volatility="all", slots=25, ticket=400.0, inputs=("tensor_fires", "bars", "positions"), cadence_s=86400. Slice constant SLICE=10000.0. Its full per-sleeve record is already in Test at `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`, including the red-timeout trigger scan: a pending candidate waits through its first 5 wait sessions; on the first session where QQQ closes below its prior close AND the stock closes at or below 1.02 x signal close (the red trigger), or at the 5th scanned session (the timeout), entry_date is set to the next session. That record is part of this package by reference.

## Files in this repo

- This package: `docs/R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family card: `strategies/ausar/r19-tensor-g4.md`
- Original-book code (already in Test): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_tensor.py`
- v3 sleeve (already in Test): `sleeves/aster_r19_tensor_g4_red_timeout_25.py`, `adapters3/aster_r19_tensor_g4_red_timeout_25.py`, `integration/aster_r19_tensor_g4_red_timeout_25_adapter.py`; shared engine `desk3/aster_batch15.py`; per-sleeve record `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Family G4; capital_mode red_timeout; volatility all; slots 25; original ticket $4,000; fee_bps 10 (accounting parameter row; R19 ledger price-tiered fees 30/15/10 bps per the code header).
- Universe: frozen 1,838-name research cohort (family card); asset class US equities; timeframe 1w (weekly Tensor fires).
- v3 slice: $10,000 book, ticket $400, slots 25 (engine SPECS in `desk3/aster_batch15.py`).
- Cadence and state beyond the above: the v3 batch15 sleeves record cadence_s=86400 and a state file (see the batch15 packages in Test); for batch14 sleeves the engine producers are tensor_bundle (86400s), bars (900s), broker_readback (900s). Anything further is not in the record.

## Data inputs

- Completed daily/weekly bars and canonical Tensor v698 features (accounting data note); raw SIP daily bars built into weekly bars for the original engine (family card).
- v3: declared inputs tensor, bars, positions (batch14) or tensor_fires, bars, positions (batch15), per `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`.

## Install and run

1. Clone the Test repo.
2. For the original book: take `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_tensor.py` with its feedlib dependencies in the same package (`desk/feedlib/r19_source`, `r19_book`, `r19_ledger` in the master-desk packages in Test); select the register() config whose id is `R19_TENSOR_G4_RED_TIMEOUT_25` (family G4, capital_mode red_timeout, volatility all, slots 25, ticket 4000).
3. For the v3 desk form: place `desk3/aster_batch15.py` at its desk path and the wrapper at `sleeves/aster_r19_tensor_g4_red_timeout_25.py` with SLEEVE_ID = "aster_r19_tensor_g4_red_timeout_25", and wire the producers named in Data inputs so each evaluation carries tensor fires, bars and positions.
4. First evaluation: call evaluate(view, ctx) on the wrapper. Confirm a snapshot with no qualifying buy-green fire returns no entry intents (fail-closed), then run the Verification checklist.

## Verification

No per-sleeve test file for this R19 id was found in Test. Behaviour checklist from the recorded algorithm:

- Every gate in step 1 is individually necessary: buy-green marker, price $10, depth60 70, ret60 0, vol20 0.09, dv20 $2,000,000, and the volatility test for this book (all).
- The capital-mode timing rule for mode red_timeout holds exactly as stated; no entry occurs outside it.
- Sizing is whole shares from the $4,000 ticket (original book) / $400 ticket (v3 slice), and entries stop at 25 positions, one per issuer.
- The only exit is the 52-week exit: five minutes before the close of the last session of the 52nd calendar week (original book) / the v3 260-session or scheduled 52-week equivalent in `docs/ASTER_R19_TENSOR_G4_RED_TIMEOUT_25-RECREATE.md`; there is no stop and no profit target.
