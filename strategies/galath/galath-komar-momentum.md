# Komar momentum breakout

Buys a liquid, trending leader on a stop order at its 20-day high the session after a tight or large-base setup, and sells under the 21-day EMA.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Julian Komar's momentum method, the Galath / GrokBot desk's public-proxy screen |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs) |
| **Style** | Momentum breakout |
| **Status** | waiting |

## Entry

- Screen after the close (≥ 80 sessions): close > $5, 50-day dollar volume ≥ $20M, 20-day ADR ≥ 4%, ≥ 70% above the 52-week low, close above the 65-day EMA, the 8-day EMA above the 21-day.
- Setup within 18% of the 52-week high: tight breakout (10-day range ≤ 55% of the 40-day, 5-day volume ≤ 80% of the 50-day, within 6% of the 20-day high) or large base (10-day range ≤ 70% of the 40-day, within 10%); ready when within 2% of the 20-day high after fewer than 3 straight up days.
- Market: Nasdaq Composite proxy B from the prior session (8-day EMA over the 21-day with both rising over 5 sessions = green; under with both falling = red); red blocks entries; green with strong reads is tier A, the rest tier B; both trade.
- Entry: the next session, a day buy-stop at the 20-day high; skipped when open risk would pass 5% of equity.

## Exit

- Stop at the 10-day low, engine-held.
- A close under the 21-day EMA sells at the next session.
- After 10 sessions, a close at or under the entry sells at the next session.
- A close back under the 20-day-high pivot sells half at the next session, once.

## Sizing

- 0.5% of equity at risk to the 10-day low, capped at 35% of equity; whole shares.

## Data

- Split-adjusted daily bars (504 sessions), Nasdaq Composite daily bars, live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/komar.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)
