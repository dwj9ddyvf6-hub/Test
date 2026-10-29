# Trullas Replay Algorithm

Created by GrokBot.

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/master-desk, main, tools/trullas_replay.py).

## What it is
A signals-only replay sanity check for the t_trullas base sleeve and its ten variants (t_trullas_v01 through v10). It produces no fills, no P&L and no backtest.

## Method (from the code's own docstring and body)
- Feeds the last at most 5 sessions of Yahoo 1-minute bars to each sleeve's scan() at every md2 pass time (a 5-minute grid plus 20 seconds) inside that sleeve's entry window.
- Counts distinct signals and abstentions per sleeve. Counts only.
- Optional --json PATH writes the counts as JSON.

## Files in this package
- packages/grokbot/trullas-replay/tools/trullas_replay.py
- docs/TRULLAS-REPLAY-ALGORITHM.md (this file)
