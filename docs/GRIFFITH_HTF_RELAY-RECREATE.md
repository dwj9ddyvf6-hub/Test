# griffith-htf-relay: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor HTF relay (T1-T7)", type "forecast and ML models", family "griffith", style evidence "Tensor signal relay", universe "Tensor research roster: 1,838 US names", asset class "US equities", timeframe "1d · 1w", creator/source "Griffith Tensor HTF research (TENSOR_HTF_RELAY_1_0_0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-htf-relay` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_htf_strategy_spec.json` (version TENSOR_HTF_RELAY_1_0_0_SHADOW, preregistered research only in the spec, core exit list DAILY_SELL_RED / DAILY_SELL_MAGENTA / WEEKLY_SELL_RED / WEEKLY_SELL_MAGENTA, daily horizons [1, 3, 5, 10, 20, 60] and weekly horizons [1, 2, 4, 8, 12] recorded for measurement).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A forward-test relay book (spec TENSOR_HTF_RELAY_1_0_0) over the 1,838-name roster. Arms T1-T7 buy fresh daily and weekly Tensor buys (daily greens, inside a weekly bull episode or not, and weekly greens and cyans); each position holds until the first completed daily or weekly sell.

## Full algorithm

From the card `strategies/griffith/griffith-htf-relay.md` and the relay spec, in evaluation order:

1. Arms (each arm is a sub-lot): T1 a daily buy-green; T4 a daily buy-green inside an active weekly bull episode (the latest fresh weekly green or cyan with no weekly sell since); T5 a T4 with consensus-buy or lifecycle P active; T6 a daily bounce buy inside a weekly bull episode; T7 the first daily green of each weekly episode; T2 a weekly buy-green; T3 a weekly buy-cyan. The spec lists the same arms as T1_DAILY_GREEN, T2_WEEKLY_GREEN, T3_WEEKLY_CYAN, T4_DAILY_GREEN_IN_WEEKLY_BULL_EPISODE, T5_T4_PLUS_CONSENSUS_BUY_OR_LIFECYCLE_P, T6_GREEN_STAR_IN_WEEKLY_BULL_EPISODE, T7_WEEKLY_BUY_THEN_DAILY_GREEN_LATENCY (plus a T8 matched no-signal control, which is not a traded arm).
2. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
3. Exit: the next session's open after the first completed daily or weekly sell-red / sell-magenta after the entry bar, at the market.
4. Sizing: One slot per event: the $100,000 book / (1,838 names x 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees (card).

## Files in this repo

- This doc: `docs/GRIFFITH_HTF_RELAY-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-htf-relay.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_strategy_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster, 1,838 US names. Timeframes: 1d and 1w. Book: $100,000.
- Arms T1-T7 as listed (T8 is a control, not traded). Slot: about $27 per event. Costs: the desk's own fees.
- State: per-sub-lot arm, entry bar, and the weekly bull-episode state per name.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-htf-relay` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_htf_strategy_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A daily green outside a weekly bull episode qualifies only for T1, not for T4/T5/T6/T7.
- T7 fires only on the first daily green of each weekly episode.
- The first completed daily or weekly sell-red/sell-magenta after the entry bar exits the sub-lot at the next session's open; no fixed-horizon exit applies.
- Only a signal new on the bar just completed enters, at the next session's open, within that session only.
- Each event takes one about-$27 slot, split equally among its sub-lots (arms).
