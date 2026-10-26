# IU big-body bar crypto (5m)

Buys ENJ on a 5-minute bar whose body is over four times the average body, then trails a 2 × ATR stop.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | IU Big Body Bar (TradingView Pine), adapted by Ausar |
| **Asset** | Crypto spot |
| **Timeframe** | 5m |
| **Universe** | ENJUSDT (Binance) |
| **Style** | Momentum impulse |
| **Status** | 2 live |

## Entry

- Bar body > 4 × the 20-bar average body (21 bars, inclusive) and the bar closes up.

## Exit

- Trailing stop: entry - 2 × ATR14, then raised to close - 2 × ATR14, hit by the observed bid.

## Sizing

- 100% of book cash incl. 10 bps, lot-floored.

## Data

- Binance 5m klines and book ticker.

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b4.py`
- **Master desk**: `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py`, `sleeves/ausar/ausar_spot_recipes.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)

## Notes

- The Alpaca forward (`femto_fwd_alpaca_enj_iu_body`) never trades: Alpaca does not list ENJ/USD.
