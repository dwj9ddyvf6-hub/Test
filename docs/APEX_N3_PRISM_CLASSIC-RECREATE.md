# apex-n3-prism-classic: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX N3 / N4: PRISM multi-asset trend", type volatility, family apex, style "Multi-asset trend x volatility", universe "QQQ, TQQQ, IEF, GLD, USO, UUP, SMH, BTC/USD, BIL", asset class US ETFs and Bitcoin, timeframe "1d", creator "APEX research desk (Cursor2), inventions N3 and N4". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-n3-prism-classic` (`docs/CATALOG.json`): card `strategies/apex/apex-n3-prism-classic.md`.
- Aliases: `apex_n3_prism_classic`, `apex_n4_prism_paradigm`.

## What this strategy is

Trend x volatility targets on a basket of assets, scaled together to 35% portfolio volatility: N3 Classic (Nasdaq-100, Treasuries, gold, oil, dollar) and N4 Paradigm (Nasdaq-100, semiconductors, gold, Bitcoin). This canonical entry covers both books; the variants table on the card records N3 PRISM Classic (Nasdaq-100, Treasuries, gold, oil, dollar) and N4 PRISM Paradigm (Nasdaq-100, semiconductors, gold, Bitcoin).

## Full algorithm

From `strategies/apex/apex-n3-prism-classic.md`, in evaluation order:

1. Per asset: unit = trend score x min(cap, 20% / HAR volatility), once it has 380 days of history.
2. The units are averaged over the assets available, then x min(3, 35% / the forecast volatility of that average); caps Nasdaq 4, Treasuries 5, gold 3, oil 2, dollar 4, semiconductors 3, Bitcoin 1; gross <= 6.
3. Each asset's held weight moves only on a change of 0.20 or more, a session after the decision.
4. Assets: N3 the Nasdaq-100, 7-10-year Treasuries (IEF), gold (GLD), oil (USO), the dollar (UUP); N4 the Nasdaq-100, semiconductors (SOX, held as SMH), gold (GLD), Bitcoin.
5. Exit: no stop; weights follow the targets; a trend score of 0 takes an asset to 0.
6. Sizing: Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit. N4's Bitcoin trades on Alpaca crypto in the last 10 minutes of the equity session. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This doc: `docs/APEX_N3_PRISM_CLASSIC-RECREATE.md`
- Strategy card: `strategies/apex/apex-n3-prism-classic.md`
- Code (already in Test): sleeves/apex/apex.py, sleeves/apex/feedlib/apex_rules.py, sleeves/apex/feedlib/apex.py, sleeves/apex/vendor/apex/inventions.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, IEF, GLD, USO, UUP, SMH, BTC/USD, BIL. Timeframe: 1d. Asset class: US ETFs and Bitcoin.
- Book: $100,000. Per-asset caps and the 35% portfolio-volatility scaling are in algorithm steps 1-2.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), IEF, GLD, USO, UUP and ^TNX (N3); ^SOX, SMH, GLD and BTC-USD (N4); recomputed after each close. N3's Treasuries: IEF's total return; before IEF, a duration model on the 10-year yield (^TNX). N4's semiconductors: ^SOX + 1% a year until SMH's history starts, then SMH's total return.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-n3-prism-classic.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- An asset with fewer than 380 days of history gets no unit.
- No per-asset weight exceeds its recorded cap, and gross exposure is at most 6.
- No weight change smaller than 0.20 is traded, and changes take effect a session after the decision.
- A trend score of 0 takes that asset to 0.
