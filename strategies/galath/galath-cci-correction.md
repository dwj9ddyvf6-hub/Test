# CCI correction pullback

Buys a stock in a long uptrend after CCI(27) dipped under -100, when CCI turns back up; 2-ATR stop, 3R target, 3-ATR trail.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | GrokBot, from an X post's Lowest(CCI(27), 18) < -100 filter |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 1,838-name genome |
| **Style** | Trend pullback |
| **Status** | waiting |

## Entry

- Close ≥ $5 and 20-day average dollar volume ≥ $20M; close above the 200-day SMA and the 50-day above the 200-day.
- Regime: SPY above its 200-day SMA and VIX under 30.
- Correction: the lowest CCI(27) of the last 18 sessions < -100.
- Trigger: CCI crosses back above -100, or the close tops the prior high while CCI rises and is still below 0.
- Decided pre-market (from 07:00 ET) on the completed session; bought 09:30-09:35 ET with marketable orders, lowest CCI first, up to 10 positions.

## Exit

- Stop 2 × ATR(14) under the fill, target the fill + 3R (6 ATR), engine-held.
- Trail: the highest close since entry - 3 ATR, ratcheting up only.
- A close below the 200-day SMA sells at the next open.
- Time stop: 20 sessions counting the entry session.

## Sizing

- 0.5% of equity / (entry - stop), at most 15% of equity, whole shares; skipped when cash is short; a $100,000 book.

## Data

- Genome split-adjusted daily bars (260 sessions, cached), SPY, VIX daily, opening quotes.

## Code

- **Master desk**: `sleeves/galath/grokbot.py`, `sleeves/galath/vendor/cci_correction/cci_correction.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)
