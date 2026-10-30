# killed-short-candidates: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Six short candidates", type mean reversion, family killed, style evidence "Fade / short (research forward test)", universe "41-name old-desk basket", US equities, timeframe "30m · 1d", creator "The old Alpaca swing desk's killed research studies, forward-tested on the master desk". Test catalog entry `killed-short-candidates`, status live (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/killed/killed-short-candidates.md`. The card does record all six candidate rules, their exits and sizing (quoted below), and the running code in this repo. The accounting gaps are gaps of the accounting pass, not of this repo's record.
- Card note: the master desk trades the short side; the old desk's long-only rail is dropped.

## What this strategy is

Six fade tests run as one forward-test book on a 41-name basket: shorting strong late-day runs, extended closes, strong-close streaks and gaps at the high, plus one long arm that buys bearish RSI divergences on 30-minute bars.

## Full algorithm

From the strategy card, in evaluation order (each candidate is an independent arm):

- C1: the return since 14:00 (live price over the 13:30 bar's close) is in the name's top fifth of the last 252 days (at least 63 days of history): short market-on-close; cover at the next close (a) or the next open (b).
- C2: the return since 15:00 is in its top fifth: short market-on-close, cover at the next close.
- C3: the close is in the top 5% of its 20-day range and above the 20-day mean + 1.5 ATR(14): short market-on-close; cover at the close 3 sessions later (a), or at the first touch of the 20-day mean (b).
- C4: two closes in a row in the top 20% of their day's range: short at the next open, cover at the close of the session after.
- C5: a gap up of at least 2% opening within 2% of the 252-day high: short at the open; cover at the end of the first 30 minutes, or earlier at the prior close (a).
- C6: bearish regular RSI divergences, STRONG or SUPERSTRONG, on 30-minute bars, one per name per day: buy at the next pass, sell after 4, 8 or 16 bars.
- Order mechanics: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. Touch exits trade at the market when the live price reaches the level.
- Sizing: $1,000 per tranche (fractional shares long; shorts in whole shares, at least 1).

## Files in this repo

- This package: `docs/KILLED_SHORT_CANDIDATES-RECREATE.md`
- Strategy card: `strategies/killed/killed-short-candidates.md`
- Running code (already in Test; nothing vendored for this package), per the card: `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`
- Rule lines referenced by the card: `docs/verify/killed.md`

## Configuration

- Universe: 41-name old-desk basket. Asset: US equities. Timeframes: 30m and 1d as specified per arm.
- $1,000 per tranche; fractional shares long, whole shares (at least 1) short.
- Status: live, as a research forward test.

## Data inputs

Regular-session 30-minute bars (3,400), split-adjusted daily bars (260), live quotes (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The candidates run inside the killed sleeve package: `sleeves/killed/killed_studies.py` with `sleeves/killed/intraday.py` and `sleeves/killed/common.py`; the C6 divergence study uses `sleeves/femto/vendor/old_desk_research/rsiobv.py`.
3. Feed the 30-minute and daily bars and live quotes described in Data inputs for the 41-name basket.
4. Run the sleeve's session passes (first-pass opens, market-on-close closes sent 30-11 minutes before the close).
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A name whose since-14:00 return is below the top fifth of its last 252 days produces no C1 short; at or above the threshold it shorts market-on-close and covers at the next close (arm a) or next open (arm b).
- C3 requires both the top-5%-of-20-day-range close and the close above mean + 1.5 ATR(14); missing either produces no short.
- C5 requires both the gap of at least 2% and the open within 2% of the 252-day high.
- C6 fires at most once per name per day, only on STRONG or SUPERSTRONG bearish regular RSI divergences on 30-minute bars, and sells after 4, 8 or 16 bars as configured per arm.
- Every tranche is $1,000; shorts are whole shares of at least 1.
