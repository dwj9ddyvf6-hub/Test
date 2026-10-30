# killed-pairs-distance-coint: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Distance pairs", type pairs and statistical arbitrage, family killed, universe NYSE, NASDAQ and AMEX listings, asset US equities, timeframe 1d, creator "The old Alpaca swing desk's killed distance pairs study (Gatev SSD) and its news-filtered V1, forward-tested". Algorithm grade PARTIAL in the accounting's consulted sources; the full rule is in the Test card and running Test code below.
- Test catalog entry `killed-pairs-distance-coint`, status counts {'live': 2}; aliases killed_pairs_distance_coint and killed_pairs_news_filtered, merged Tier A on the evidence that the catalog entry groups both rows.

## What this strategy is

Trades the 20 closest stock pairs of a 12-month formation: both legs at a 2 sigma spread, out at 0.5 sigma, stop at 4 sigma; the V1 variant opens at 2.5 sigma only without news and holds at most 10 sessions (card summary). Both rows are forward-tested killed studies, not a live alpha claim.

## Full algorithm

From the card and `sleeves/killed/pairs.py` (step_distance, step_v1, PairsDistance, PairsNewsFiltered):

Formation (each half-year window; Jan-Jun from the prior calendar year, Jul-Dec from Jul-Jun):
1. Universe: NYSE / NASDAQ / AMEX listings with bars on at least 240/252 of the 12 formation months' sessions, median dollar volume at least $1M, median price at least $5, and every day present after bad-tick cleaning.
2. Select the 20 pairs with the smallest sum of squared distances (SSD) of normalized prices. The 20 best Engle-Granger ADF pairs are formed and recorded, not traded.

Daily decision (once a day in the market-on-close window, 30-11 minutes before the close in the card; code schedule close-60:close-11, cadence 300):
3. z = the normalized spread less its formation mean, over its formation sigma, on the live prices.
4. Base book (step_distance, entry 2.0, exit 0.5, stop 4.0): flat and z > 2 opens short A / long B; z < -2 opens long A / short B. Long-spread state closes when |z| < 0.5 (converge) or z < -4 (adverse stop); short-spread state closes when |z| < 0.5 or z > 4. Pairs may reopen.
5. V1 news-filtered (step_v1, entry 2.5, exit 0.5, time stop 10 sessions): entry only when neither leg has a news item, an earnings date or an ex-dividend date from 5 sessions back to today (code: clean flag from the killed_pairs_news feed). Exit at |z| < 0.5 or after 10 sessions; the time stop replaces the 4 sigma stop.
6. Every pair closes on the trading window's last session (force close). Base book birth / new window: state is replayed from the vendored trade_pair over the window to date and an open replay position is opened at once; V1 starts flat.

Sizing: $5,000 per pair, $2,500 a leg (code: PAIR_CAPITAL = CAPITAL / N_PAIRS = $100,000 / 20 = $5,000; $1/$1 self-financing, each leg half the pair capital); whole shares on the short leg. Entries and exits are market-on-close.

## Files in this repo

- This package: `docs/KILLED_PAIRS_DISTANCE_COINT-RECREATE.md`
- Strategy card: `strategies/killed/killed-pairs-distance-coint.md`
- Running code (already in Test): `sleeves/killed/pairs.py`, `sleeves/killed/killed_studies.py` (registers PairsDistance and PairsNewsFiltered and their feeds / jobs), `sleeves/killed/common.py` (CAPITAL 100000.0), `sleeves/killed/feedlib/killed_data.py` (formation and news jobs; path as named in the card / code imports)
- Vendored study code in Test: `sleeves/killed/vendor/midna_research/pairs_backtest_dev.py`
- Parity tool in Test: `packages/claude/master-desk-parity-tools/tools/parity/killed_pairs.py`
- Rule lines: `docs/verify/killed.md`

## Configuration

- Sleeve ids: `killed_pairs_distance_coint` (base) and `killed_pairs_news_filtered` (V1). N_PAIRS 20, entry_z 2.0 / 2.5, exit_z 0.5, stop_z 4.0 (base only), time_stop 10 sessions (V1 only), news window 5 sessions (V1 only), pair_capital $5,000.
- Schedule close-60:close-11, cadence 300, WHOLE_SHORT true. Formation: 12 months, half-year windows.
- Named divergences recorded in the code: universe from NASDAQ Trader directories instead of Alpaca /v2/assets; today's z read on the live price in the auction window; adjusted series is the hub's; borrow drag is the venue's; the long-only rail of the old desk is dropped (removed_gates).

## Data inputs

Daily adjusted closes (420 bars) of the legs; NASDAQ Trader symbol directories. Formation feed killed_pairs and, for V1, killed_pairs_news: Alpaca news (or Yahoo RSS headlines without keys) and Nasdaq earnings and dividend calendars, per the card.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine dependencies for the files listed above (Python, numpy and pandas where those modules require them).
3. Import / register the sleeve or strategy module named in the Files section with the sleeve id and parameters recorded in the Full algorithm and Configuration sections.
4. Serve the data inputs named below and the sleeve's book / position state.
5. Run the desk engine on the cadence recorded in the Configuration section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file was named in the card. Behavior checklist (from step_distance / step_v1 in `sleeves/killed/pairs.py`):

- Flat with z = +2.1 opens the short-spread state; z = -2.1 opens the long-spread state; |z| <= 2.0 opens nothing in the base book.
- A held base position closes at |z| < 0.5 and at the adverse 4 sigma stop; a held V1 position closes at |z| < 0.5 or at 10 sessions, and V1 never opens at |z| between 2.0 and 2.5 or when the news gate is dirty.
- On the window's last session every open pair force-closes and no new entry opens.
- Parity: `packages/claude/master-desk-parity-tools/tools/parity/killed_pairs.py` replays the vendored study functions; the recreation's state transitions must match it.
