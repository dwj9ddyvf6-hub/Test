# Band-touch RSI divergence

A symbol-agnostic chart indicator and adaptive v2.2, multi-symbol paper-desk sleeve for confirmed Bollinger Band touches with regular RSI divergence.

The raw BB/RSI trigger stays frozen for parity. Sleeve v2.2 adds causal local trend/band-walk and volatility context, bounded risk scaling, per-symbol abstention reasons, refreshed-bar requirements, persistent stop/target exits, and close-order deduplication. The Pine indicator runs on supported chart symbols/timeframes; the desk sleeve defaults to 12 liquid US-listed ETFs and uses completed 1-hour regular-session bars.

## Files

- `indicator/BB_RSI_Divergence_Algorithm.md` — signal contract and strategy assumptions.
- `pine/BB_RSI_Divergence_Indicator.pine` — TradingView Pine Script v6 source.
- `sleeves/bb_rsi_divergence.py` — Femto-lean `BaseSleeve` implementation.
- `docs/BB_RSI_Divergence_Research.md` — research record and multi-asset replay.
- `integration/Femto-lean_Wiring.md` — required hourly-bars, quote, and fill-feed wiring.

The sleeve is paper-enabled (`parked=False`). This repository does not contain the Femto-lean core or broker order-lifecycle adapter. Runtime wiring is staged in the [Femto-lean paper-only branch](https://github.com/dwj9ddyvf6-hub/Femto-lean/tree/bb-rsi-live-readiness-20261024); the draft PR has not been merged or deployed, and no paper orders have been sent. The runtime enforces paper-only transport. See the wiring guide for the paper-run checklist and the separate real-money release gates.

## Evidence

The one-year exploratory replay found too few qualifying trades to establish an edge. A 12-ETF v2 opportunity-coverage scan found five candidates across 268 sessions; it did not model fills or P&L. The context/risk overlay remains a research hypothesis. The research note records the data window, assumptions, controls, sources, and next decisive experiment.
