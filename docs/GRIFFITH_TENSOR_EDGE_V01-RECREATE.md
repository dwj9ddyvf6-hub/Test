# griffith-tensor-edge-v01: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor edge v0.1 (G1 / G2 / C1)", type "forecast and ML models", family "griffith", style evidence "Tensor signal breakout", universe "Tensor research roster: 1,838 US names", asset class "US equities", timeframe "1d · 1w", creator/source "Griffith Tensor edge research (griffith-tensor-edge/0.1.0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-tensor-edge-v01` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_edge_strategy_spec.json` (version griffith-tensor-edge/0.1.0, completedBarOnly true, shadow/research authority flags all false in the spec).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A breakout book (spec griffith-tensor-edge/0.1.0) over the 1,838-name Tensor roster. It buys a break of the signal bar's high after a qualifying daily green ignition (G1), weekly green emergence (G2) or weekly cyan re-acceleration (C1), stopped at the signal bar's low and held until the frame's next sell.

## Full algorithm

From the card `strategies/griffith/griffith-tensor-edge-v01.md` and the frozen spec `tensor_edge_strategy_spec.json`, in evaluation order:

1. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
2. G1 (daily buy-green): above a rising EMA 200; a 20/60-bar range ratio <= 0.75; a 20-bar breakout; under 15% over EMA 21; and an up-volume share >= 50% or a rising OBV or A/D line. Spec archetype RISING_TREND_ORGANIZED_BASE_EXPANSION with required ABOVE_RISING_EMA200, BASE_COMPRESSION, EXPANSION_TRIGGER, CONSTRUCTIVE_PARTICIPATION.
3. G2 (weekly buy-green): a long base (range ratio <= 0.75 or >= 30% under the 52-week high); the 13-week return above SPY's (or the 13-week relative strength above the 26-week); 4-week volume >= the 20-week; under 15% over EMA 21.
4. C1 (weekly buy-cyan): 13- and 26-week returns above SPY's; a 13-week return of 25-60%; RSI 55-72; an up-volume share >= 55%; the 4-week range <= 75% of the 13-week; none when exhausted (RSI >= 75, a 13-week return >= 100%, or an extension warning). Spec research centres: return13 [0.25, 0.60], rsi14 [55, 72], upVolumeShare13 centre [0.55, 0.70].
5. Entry execution: a buy-stop at the signal bar's high, resting through the next bar (session or week).
6. Exit, stop: the bid at or under the signal bar's low, at the market. Exit, signal: the next session's open after the frame's completed sell-red / sell-magenta.
7. Sizing: One slot per event: the $100,000 book / (1,838 names x 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees (card).

## Files in this repo

- This doc: `docs/GRIFFITH_TENSOR_EDGE_V01-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-tensor-edge-v01.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_edge_strategy_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster, 1,838 US names. Timeframes: 1d and 1w. Book: $100,000.
- Arms: G1, G2, C1 as above; the spec also records an X1 cyan-exhaustion exclusion/management research item, which the card does not trade as an entry arm.
- Slot: about $27 per event (see algorithm step 7). Costs: the desk's own fees (card).
- State: per-event signal bar high/low (stop and trigger), frame, and arm.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-tensor-edge-v01` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_edge_strategy_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A signal that is not new on the bar just completed, or a roster run under half coverage, produces no entry.
- The buy-stop rests only through the next bar; an unfilled stop after that bar does not enter later.
- A G1 candidate failing any one of its five conditions (including the participation alternative) does not qualify.
- A C1 candidate with RSI >= 75 or a 13-week return >= 100% is excluded as exhausted.
- Exit occurs at the signal bar's low on a bid at or under it, or at the next open after the frame's sell-red/sell-magenta, whichever comes first.
- Each event takes one about-$27 slot, split equally among its sub-lots.
