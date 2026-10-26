# Phase compression breakout (daily)

Trades the break out of a daily squeeze (Bollinger inside Keltner): a buy-stop over the 5-day box, or a nowcast breakout, trailed by the 50-day EMA.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Milkman Trades' Daily Bilbo Boxes, via the old Alpaca swing desk and Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 48-name phase universe |
| **Style** | Volatility breakout |
| **Status** | live |

## Entry

- Squeeze (grey): the 21-period, 2-sd Bollinger band inside the 2 × ATR(14) Keltner band around EMA(21), unless the gap is widening inside the 1.854 × ATR zone.
- K5: once 5 grey days lock a box, a DAY buy-stop rests at the box high before each open while the prior close is above EMA(21), for 20 bars, until the box low or high is touched.
- NC: on episodes K5 cannot trade, buys when yesterday was grey, today's forming bar nowcasts not grey, its high crosses the episode high and the prior close is above EMA(21), with a confirmed earnings date not today or tomorrow.
- One trade per episode; ≥ 80 bars; new entries need a fresh earnings calendar.

## Exit

- Stop at the box low (K5) or the episode low (NC), ratcheted up to the prior day's EMA(50) before each open; sold at the open when that trail reaches the prior close.
- Sold at the open if the prior close is back below the entry reference within 3 sessions.
- Flattens in the last 5 minutes before an earnings report today or next session; re-enters the session after the report when price is above the trail.

## Sizing

- 0.25% of the book risked from entry to stop, capped at 25% notional; at most 10 positions.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (500), the forming daily bar, earnings dates.

## Code

- **Master desk**: `sleeves/femto/phase_daily.py`
- **Midna v3**: `sleeves/phase_daily.py`. A wrapper only; the strategy file is not in this repo

## Notes

- K5 is Milkman's Daily Bilbo Box; the Milkman study trades that box alone, both ways, as [Daily Bilbo Box](../milkman/mk-dailybilbobox.md).
