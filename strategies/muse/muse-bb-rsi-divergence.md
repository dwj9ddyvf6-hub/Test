# Band-touch RSI divergence

Buys a confirmed 1-hour swing low that tags the lower Bollinger Band while RSI makes a higher low, aiming for the band's midline.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Midna's desk: a TradingView indicator reconstructed from a chart screenshot, and its desk sleeve |
| **Asset** | US ETFs and large caps |
| **Timeframe** | 1h |
| **Universe** | 12 ETFs (v2.2) · 40 names (expanded) |
| **Style** | Mean reversion |
| **Status** | Midna's desk only |

## Entry

- Bars: completed regular-session 1-hour bars; a missing hour among the last 24, or a latest bar over 10 minutes old, blocks the symbol.
- Setup: a pivot low (3 bars each side) at or below the lower Bollinger Band (20, 2), lower than the previous accepted pivot low 5-60 bars back, with RSI(14) (the lowest within a bar of the pivot) more than 2 points higher; acted on at the confirming bar, 3 bars after the pivot.
- Order: a limit at the ask, rounded up to the cent, from a quote ≤ 60 s old with a spread ≤ 15 bps.
- Stop = the pivot low - 0.5 ATR(14); target = the band's midline; reward/risk ≥ 1.2; candidates ranked by risk scale, reward/risk, RSI gap, touch depth, spread.

## Exit

- A bar's low at the stop (checked first) or high at the target.
- After 24 hourly bars, or on a bearish upper-band divergence (the mirror setup).
- Exit orders carry no limit; a working exit blocks new orders.

## Sizing

- 0.25% of equity at risk × a risk scale, capped at 5% of equity in notional; whole shares.
- Risk scale = a volatility scale (1 / √(ATR% over its 60-bar median), 0.5-1) × 0.5 when walking the band against the trade (12-bar efficiency ≤ -0.55 with 2 of the last 4 closes beyond the band), at least 0.25.

## Data

- 1-hour bars, latest quotes, the session's fills and orders.

## Variants

| Version | Code | Universe | Sides | Entries | Signal closes |
|---|---|---|---|---|---|
| v2.2 | `sleeves/bb_rsi_divergence.py` | 12 ETFs: SPY, QQQ, IWM, DIA, GLD, SLV, TLT, IEF, USO, UUP, XLF, XLK | long; a bearish divergence exits | one filled entry a session | 10:00-15:00 ET |
| Expanded (Midna v3 `bb_rsi_divergence`) | `sleeves/bb_rsi_divergence_expanded.py` | 40: the 12, 8 more sector ETFs and 20 large caps | long and short (the mirror at the bid; a bullish divergence exits a short) | one per symbol a session, up to 3 open | any completed regular-session hour |

## Code

- **Midna v3**: `sleeves/bb_rsi_divergence_expanded.py`, `integration/bb_rsi_divergence_expanded_adapter.py`. The expanded file; its switch defaults on
- **Femto-lean sleeve v2.2**: `sleeves/bb_rsi_divergence.py`
- **TradingView indicator**: `pine/BB_RSI_Divergence_Indicator.pine`
- **Rule lines**: [docs/verify/muse.md](../../docs/verify/muse.md)

## Notes

- The Pine indicator plots the raw trigger and raises alerts; it does not size or send orders.

## The original README

This repo's README before the catalog, unchanged.

A symbol-agnostic chart indicator and adaptive v2.2, multi-symbol paper-desk sleeve for confirmed Bollinger Band touches with regular RSI divergence.

The raw BB/RSI trigger stays frozen for parity. Sleeve v2.2 adds causal local trend/band-walk and volatility context, bounded risk scaling, per-symbol abstention reasons, refreshed-bar requirements, persistent stop/target exits, and close-order deduplication. The Pine indicator runs on supported chart symbols/timeframes; the desk sleeve defaults to 12 liquid US-listed ETFs and uses completed 1-hour regular-session bars.

### Files

- [`indicator/BB_RSI_Divergence_Algorithm.md`](../../indicator/BB_RSI_Divergence_Algorithm.md) — signal contract and strategy assumptions.
- [`pine/BB_RSI_Divergence_Indicator.pine`](../../pine/BB_RSI_Divergence_Indicator.pine) — TradingView Pine Script v6 source.
- [`sleeves/bb_rsi_divergence.py`](../../sleeves/bb_rsi_divergence.py) — Femto-lean `BaseSleeve` implementation.
- [`docs/BB_RSI_Divergence_Research.md`](../../docs/BB_RSI_Divergence_Research.md) — research record and multi-asset replay.
- [`integration/Femto-lean_Wiring.md`](../../integration/Femto-lean_Wiring.md) — required hourly-bars, quote, and fill-feed wiring.

The sleeve is paper-enabled (`parked=False`). This repository does not contain the Femto-lean core or broker order-lifecycle adapter. Runtime wiring is staged in the [Femto-lean paper-only branch](https://github.com/dwj9ddyvf6-hub/Femto-lean/tree/bb-rsi-live-readiness-20261024); the draft PR has not been merged or deployed, and no paper orders have been sent. The runtime enforces paper-only transport. See the wiring guide for the paper-run checklist and the separate real-money release gates.

### Evidence

The one-year exploratory replay found too few qualifying trades to establish an edge. A 12-ETF v2 opportunity-coverage scan found five candidates across 268 sessions; it did not model fills or P&L. The context/risk overlay remains a research hypothesis. The research note records the data window, assumptions, controls, sources, and next decisive experiment.
