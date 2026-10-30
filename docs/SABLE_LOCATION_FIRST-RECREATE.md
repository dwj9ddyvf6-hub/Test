# sable-location-first: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Location-first repair", type mean reversion, family sable. Algorithm grade in the accounting: PARTIAL, with entry, exit and sizing "not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id `sable-location-first`, status counts {'live': 1}, card `strategies/sable/sable-location-first.md`, code `sleeves/sable/sable.py`, `sleeves/sable/location_first.py`, `sleeves/sable/runtime.py`.
- Creator per the card: Sable / Autopilot desk, Location-first Repair v2.1.0. The code header in `sleeves/sable/sable.py` records the source desk and that `location_first.py` ports the source scanner module (Location-first Repair v2.1.0) line by line.
- Running code in Test (verified present at batch start): `sleeves/sable/sable.py` (sleeve class `LocationFirstRepair`, sleeve_id `sable_location_first_repair_v210`, family `location_first`, cadence_s 300, schedule rth), `sleeves/sable/location_first.py` (the scan), `sleeves/sable/runtime.py` (the paper runtime).

## What this strategy is

Buys a washed-out stock still under its 50-day average when it sits on a support shelf with MACD lifting and RSI 28-52.

## Full algorithm

Evaluation order (card, confirmed against the code headers in `sleeves/sable/sable.py` and `sleeves/sable/location_first.py`):

Research pass (the scan, `build_location_first_scan`):
1. Funnel: every stock's 6 months of daily closes; the 48 best under-50-day reads and the 48 best leaders-rest reads (plus SPY, QQQ) are re-read on 400 days of daily OHLC with today's forming bar and the live price. ETFs are read as context and never bought.
2. Out (any one excludes): price above the 50-day EMA; RSI(14) over 52; the 50-day EMA down more than 1.5% over 10 sessions; under $3 with under $2M 20-day dollar volume; or earnings from 12 h before to 48 h ahead.
3. Shelf: the 21-day EMA within 2%, the 12-day low within 4%, or a 50 / 61.8 / 78.6% retrace of the 60-day swing within 2.5%; the best by weight, confluence and distance; price at most 3% above it.
4. Repair: RSI 28-52; the ATR-scaled MACD(12, 26, 9) histogram up in 2 of the last 3 sessions with a net lift; at least 8% under the 20-day high; today's low above the prior 11 sessions' low x 1.001; at least 20 bars with a real range.
5. Grade: S_COIL (on the 21-day, RSI 40-52, MACD up all 3 steps from below zero) at score at least 80, or A_WASHOUT at at least 68, is a SETUP; the 6 best-scoring SETUP stocks are the hands.

Paper pass (every 5 minutes in the regular session):
6. Buys each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order. One buy per name per daily bar.
7. Orders per the card: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands. (The code header records the desk-engine divergence that the pass's buys become marketable engine orders decided on the same simulated state.)
8. Sizing: min(0.5% of equity / (1.6 x ATR), 15% of equity, 98% of cash) in whole shares; a $100,000 book.
9. Exits, checked on the quote every 5 minutes: stop at fill - 1.6 x ATR, target at fill + 2.8 x ATR (daily ATR(14), at least 1.5% of the fill; both widen if ATR grows). Breakeven at +1R: once the stop is moved to the entry price it stays there (card note: the owner's decision Q44, 2026-10-26).
10. Time stop: after 15 days if the position is not in profit.
11. Not carried over (card): the desk pause and 2% daily-loss park, the Edge overlay and the Tensor SELL veto.

## Files in this repo

- This package: `docs/SABLE_LOCATION_FIRST-RECREATE.md`
- Strategy card: `strategies/sable/sable-location-first.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/sable/sable.py` (the sleeve: `LocationFirstRepair`, sleeve_id `sable_location_first_repair_v210`, cadence 300 s, rth schedule; capital from the runtime mandate's startingCapital)
  - `sleeves/sable/location_first.py` (the scan: `build_location_first_scan`, `evaluate`)
  - `sleeves/sable/runtime.py` (the paper runtime port: mandate, stop/target pass)
  - Support files in Test: `sleeves/sable/desk_scanner.py`, `sleeves/sable/feedlib/yahoo_spark.py`, `sleeves/sable/vendor/sable/catalog.mjs`, `sleeves/sable/vendor/sable/universe.ts`
- Parity tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/sable_location_first.py` drives the original modules on the same inputs.
- Rule lines: `docs/verify/sable.md`.

## Configuration

- Universe: Sable catalog: 488 stocks (68 ETFs as context, never bought). Asset class: US equities. Timeframe: 1d, with 5-minute passes.
- Book: $100,000. Max positions: 6. Cadence: 300 s in the regular session.
- State: the sleeve's scan bundle, hands, shortlist and held-position records (fill price, open time, ATR at decision) in the engine store.
- Status in the accounting/catalog: live.

## Data inputs

Yahoo spark daily closes (6 months); split-adjusted daily bars (400 days) with today's forming bar; live quotes; the Nasdaq earnings calendar.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Place the `sleeves/sable/` package on the desk engine it was written for (it imports the desk contract and the sable runtime in this repo).
3. Configure the sleeve from its CONFIG in `sleeves/sable/sable.py`: sleeve_id `sable_location_first_repair_v210`, family `location_first`, cadence 300 s, rth schedule, capital from the runtime mandate.
4. Serve the declared needs: daily split-adjusted bars (300 bars for the OHLC symbols), equity quotes, and the sable_spark and sable_earnings feeds.
5. Run the desk engine in the regular session; the scan produces the hands and the 5-minute pass trades them.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test; the parity tool named in the Files section drives the original modules on the same inputs. Behavior checklist, from the algorithm section:

- A stock above its 50-day EMA, or with RSI(14) over 52, or with earnings inside the -12 h / +48 h window, never appears as a SETUP hand.
- A name meeting the shelf and repair rules with grade S_COIL at score at least 80 (or A_WASHOUT at at least 68) is a SETUP; at most 6 hands are produced and ETFs never appear among them.
- A held position exits at fill - 1.6 x ATR (floored at 1.5% of fill) or fill + 2.8 x ATR on a 5-minute quote check, and after 15 days if not in profit.
- Position size equals min(0.5% of equity / (1.6 x ATR), 15% of equity, 98% of cash) in whole shares, and no seventh position is opened while 6 are held or working.