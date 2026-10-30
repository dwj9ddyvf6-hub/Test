# griffith-liquid-momentum-trend - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `.md`): canonical name "Liquid momentum trend cohorts", type momentum, family griffith, algorithm grade PARTIAL, gaps entry/exit/sizing not recorded in the accounting sources; universe SCOPE universe: 550 US names; asset US equities; timeframe 1d (20-session cohorts); creator Griffith R4 strategy tournament (LIQUID_MOMENTUM_TREND_1_0_0); alias griffith_liquid_momentum_trend (test_catalog, status blocked).
- Existing Test strategy card: `strategies/griffith/griffith-liquid-momentum-trend.md` (full entry/exit/sizing/data/code text quoted in substance below).
- Code found in Test already: `sleeves/griffith/griffith_factor.py` (DAILY mapping griffith_liquid_momentum_trend -> LIQUID_MOMENTUM_TREND_1_0_0, R4DailyCandidate), `sleeves/griffith/vendor/griffith/strategy_tournament.py` (evaluate_daily_candidate), `sleeves/griffith/feedlib/griffith.py`, and `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` in the vendor tree.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

Griffith daily tournament candidate LIQUID_MOMENTUM_TREND_1_0_0. Each session, every liquid SCOPE name in an uptrend with positive 12-1 momentum opens a 20-session cohort in a fixed slot. Status in the strategy card: blocked.

## Full algorithm

From the strategy card and `sleeves/griffith/griffith_factor.py` (header and R4DailyCandidate), in evaluation order:

1. Observation, each session on the last completed bar (253 bars needed): close > SMA 200 and SMA 50 > SMA 200; 12-1 momentum = close 21 sessions back / close 252 sessions back - 1 > 0 (code header: close[-22]/close[-253] - 1 > 0); 20-day average dollar volume >= $20M. The vendored evaluate_daily_candidate returns SETUP only when all hold.
2. Tape/coverage handling in griffith_factor.py is for the monthly books; the daily candidate observes each eligible name in tape order and collects SETUP names, skipping names already held or with a pending order.
3. Entry: at the session's first pass with a live quote, a fixed slot of $100,000 / 550 (about $182; code: slot = CONFIG.capital / UNIVERSE_SLOTS, UNIVERSE_SLOTS = 550, HORIZON = 20) as a marketable limit good for an hour (code: OrderSpec(window_s=3600), price_hint = live ask or last). One cohort per name, none while held or working.
4. Exit: market-on-close in the last 25 minutes of the 20th session, the entry session counting as 1 (code: when minutes_to_close <= 25 and trading days held + 1 >= 20, exit Intent with OrderSpec(type="market", tif="cls")). No stop or target is recorded for this candidate.

## Files in this repo

- This package: `docs/GRIFFITH_LIQUID_MOMENTUM_TREND-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/strategy_tournament.py`, `sleeves/griffith/feedlib/griffith.py`
- Strategy card: `strategies/griffith/griffith-liquid-momentum-trend.md`; rule lines: `docs/verify/griffith.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

Version LIQUID_MOMENTUM_TREND_1_0_0; capital basis $100,000 in the card's slot formula ($100,000 / 550, about $182 per cohort); UNIVERSE_SLOTS 550; HORIZON 20 sessions; cadence_s 300 and schedule rth in R4DailyCandidate CONFIG; params {version_id, horizon_sessions: 20, slots: 550}. Thresholds: SMA 200, SMA 50, 12-1 momentum > 0, 20-day average dollar volume >= $20M, 253 bars needed.

## Data inputs

Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys as fallback (per the strategy card). Live quotes for entry price_hint.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read `strategies/griffith/griffith-liquid-momentum-trend.md` and this package.
3. Place/confirm the code files listed under Files in this repo at their Test paths; register the R4DailyCandidate sleeve griffith_liquid_momentum_trend in sleeves/griffith/griffith_factor.py sleeves().
4. Wire the Griffith IEX daily feed and live equity quotes.
5. Run the desk cycle; the candidate's signal(view) observes SETUP names and emits the cohort entry/exit intents described above.
6. Run the Verification checks on a fixture before treating a recreation as faithful.

## Verification

- A name with close <= SMA 200, SMA 50 <= SMA 200, 12-1 momentum <= 0, or 20-day average dollar volume < $20M produces no cohort.
- A SETUP name not held and not pending, with a live quote, produces exactly one entry of about $182 notional with a 3600-second window.
- A held cohort on its 20th session in the last 25 minutes produces a market-on-close exit; before that it does not.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes (recorded in the batch results file).
