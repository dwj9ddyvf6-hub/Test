# QQQ morning dip limit

Between 10:00 and 12:00 ET, after a calm 3-minute QQQ candle, rests a limit buy one ATR under its close and targets the candle's midpoint.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US ETF |
| **Timeframe** | 3m |
| **Universe** | QQQ |
| **Style** | Intraday mean reversion |
| **Status** | live |

## Entry

- 3-minute candles from 1-minute bars; a closed signal candle starting 10:00-12:00 ET, the last 16 healthy, efficiency ratio over 15 candles ≤ 0.35.
- Arms a DAY limit one tick under level = floor(close - ATR(14)); cancelled after 9 minutes; one order or position at a time.

## Exit

- Target = the signal candle's midpoint; stop = max(4 ticks, 1.5 ATR) under the limit; a 15-minute time stop; flat at 12:00 ET.

## Sizing

- Shares = 0.25% of the book / the stop distance.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Yahoo 1-minute bars with the extended session (420).

## Code

- **Master desk**: `sleeves/femto/morning_dip.py`
- **Midna v3**: `sleeves/morning_dip.py`. A wrapper only: it runs the strategy file through Midna's `_enh2` layer, neither of which is in this repo
