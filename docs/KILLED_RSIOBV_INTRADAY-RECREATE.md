# killed-rsiobv-intraday: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "RSI x OBV intraday (5-minute)", type divergence reversal, family killed, style "Divergence (research forward test)", universe "MU, ARM, SNDK, WDC, CLS, ANF, CVNA, FFIV", asset class US equities, timeframe 5m, creator "The old Alpaca swing desk's killed RSI x OBV 5-minute bucket (an @PredictionAlgos method), forward-tested". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `killed-rsiobv-intraday` (`docs/CATALOG.json`): status live (1), card `strategies/killed/killed-rsiobv-intraday.md`, master-desk row `killed_rsiobv_intraday`.
- Alias: `killed_rsiobv_intraday`.

## What this strategy is

Buys a strong bullish RSI divergence on 5-minute bars of 8 names and holds it 2, 4 or 8 hours. It is a forward test that re-checks the original kill, per `sleeves/killed/killed_studies.py` (row `killed_rsiobv_intraday`: "BuR RSI STRONG/SUPERSTRONG 5m divergences, 8 names, 2h/4h/8h forwards").

## Full algorithm

From `strategies/killed/killed-rsiobv-intraday.md` and the code in Files, in evaluation order:

1. Divergence definition: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73).
2. Entry signal: bullish regular RSI divergences, STRONG or SUPERSTRONG, on the last 600 5-minute bars; one per name per 24 h; bought at the next regular-session pass.
3. Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close (per the card's order note).
4. Exit: three tranches sell after 24, 48 and 96 bars past the signal bar (2, 4 and 8 hours on 5-minute bars).

## Files in this repo

- This doc: `docs/KILLED_RSIOBV_INTRADAY-RECREATE.md`
- Strategy card: `strategies/killed/killed-rsiobv-intraday.md`
- Code (already in Test): `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`; parity copies under `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/`
- Rule lines: `docs/verify/killed.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. Related original research was found in the Midna tree (an RSI_OBV_DIVERGENCE research tree); it is research background, not the sleeve code, and was not vendored because the sleeve code is already in Test. No killed sleeve code was found in Silicon or quant-research-backup.

## Configuration

- Universe: MU, ARM, SNDK, WDC, CLS, ANF, CVNA, FFIV. Timeframe: 5m. Asset class: US equities.
- Book: $100,000. Sizing: $100,000 / 24 per tranche (fractional shares).
- Rate limit: one signal per name per 24 h.

## Data inputs

- 5-minute bars (600), per the card.

## Install and run

1. Clone the Test repo.
2. Read `strategies/killed/killed-rsiobv-intraday.md` and `docs/verify/killed.md`.
3. Open `sleeves/killed/killed_studies.py` (row `killed_rsiobv_intraday`), `sleeves/killed/intraday.py`, `sleeves/killed/common.py` and `sleeves/femto/vendor/old_desk_research/rsiobv.py`.
4. Provide the last 600 5-minute bars for the 8 names.
5. Run in the regular session: scan for STRONG / SUPERSTRONG bullish regular divergences, buy at the next pass, and sell the three tranches after 24, 48 and 96 bars. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- A bullish divergence that is neither STRONG (RSI under 32) nor SUPERSTRONG (under 27) produces no entry, and bearish divergences produce no entry in this sleeve.
- At most one entry per name per 24 h, bought only at the next regular-session pass.
- The three tranches exit after exactly 24, 48 and 96 bars past the signal bar, each sized $100,000 / 24 in fractional shares.
