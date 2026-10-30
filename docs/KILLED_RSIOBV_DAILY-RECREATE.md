# killed-rsiobv-daily: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "RSI x OBV daily studies", type divergence reversal, family killed, style "Divergence (research forward test)", universe "19 names (MU, WDC, ANF, CLS, FFIV, AAOI, AXTI, SOXL, AEHR, FCEL, TTMI, SIMO, VICR, AG, SILJ, SPY, QQQ, NVDA, AAPL)", asset class US equities, timeframe 1d, creator "The old Alpaca swing desk's killed RSI x OBV studies (the scanner reconstructs an @PredictionAlgos video), forward-tested". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `killed-rsiobv-daily` (`docs/CATALOG.json`): status live (1), card `strategies/killed/killed-rsiobv-daily.md`, master-desk row `killed_rsiobv_daily`.
- Alias: `killed_rsiobv_daily`. Note on the card: the master desk trades the short side; the old desk's long-only rail is dropped.

## What this strategy is

Trades every arm of three RSI / OBV divergence studies on 19 names' daily bars, each held 5, 10 or 20 sessions. It is a forward test that re-checks the original kill, per `sleeves/killed/killed_studies.py`.

## Full algorithm

From `strategies/killed/killed-rsiobv-daily.md`, `sleeves/killed/killed_studies.py` (row `killed_rsiobv_daily`: "RSIxOBV studies A/B/C on 19 names") and `sleeves/femto/vendor/old_desk_research/rsiobv.py`, in evaluation order:

1. Divergence definition: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73).
2. Study A: four buckets per direction (all RSI; RSI and OBV agreeing over the same swings; strong regular RSI; RSI and OBV both in the top / bottom tenth of their 144-bar range), one signal per 20 bars; entry the next open, holds 5 / 10 / 20 sessions.
3. Study B: regular RSI divergences confirmed by a trendline break (a close, a wick, or two closes) within 5 bars; entry the next open, holds 5 / 10 / 20.
4. Study C: a strict 20-day closing high, alone or with RSI (8, 13 or 21) at or below 30; long, out at the close 21 sessions after the signal.
5. Bullish arms buy, bearish arms sell short.
6. Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.
7. Exit: each tranche sells or covers market-on-close at its hold.

## Files in this repo

- This doc: `docs/KILLED_RSIOBV_DAILY-RECREATE.md`
- Strategy card: `strategies/killed/killed-rsiobv-daily.md`
- Code (already in Test): `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`; parity copies under `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/` and `packages/claude/master-desk-parity-tools/tools/parity/killed_rsiobv.py`
- Rule lines: `docs/verify/killed.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. Related original research was found in the Midna tree (an RSI_OBV_DIVERGENCE research tree with divergence code and reports); it is research background, not the sleeve code, and was not vendored because the sleeve code is already in Test. No killed sleeve code was found in Silicon or quant-research-backup.

## Configuration

- Universe: the 19 names in Provenance. Timeframe: 1d. Asset class: US equities.
- Book: $100,000. Sizing: $100,000 / 150 per tranche (fractional shares long; shorts in whole shares, at least 1).
- State / cadence: not in the record beyond the session first-pass and market-on-close timing above.

## Data inputs

- Closed daily bars (520), per the card.

## Install and run

1. Clone the Test repo.
2. Read `strategies/killed/killed-rsiobv-daily.md` and `docs/verify/killed.md`.
3. Open `sleeves/killed/killed_studies.py` (row `killed_rsiobv_daily`), `sleeves/killed/daily.py`, `sleeves/killed/common.py` and `sleeves/femto/vendor/old_desk_research/rsiobv.py`.
4. Provide 520 closed daily bars for the 19 names.
5. Run daily: scan for the Study A / B / C signals, enter at the next open, and exit each tranche market-on-close at its hold. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- A pivot pair under 5 or over 60 bars apart produces no divergence; STRONG requires RSI under 32 / over 68 and SUPERSTRONG under 27 / over 73.
- Study A emits at most one signal per 20 bars per bucket; Study B requires a trendline break within 5 bars; Study C requires a strict 20-day closing high.
- Entries are at the next open only; exits are market-on-close at exactly 5, 10 or 20 sessions (21 sessions after the signal for Study C).
- Each tranche is $100,000 / 150, fractional long and whole-share short (minimum 1).
