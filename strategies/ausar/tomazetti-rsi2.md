# Tomazetti RSI(2) crypto (1h)

Buys ADA on an hourly RSI(2) dip above the 200-bar average and sells when price closes back above the 5-bar average.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Tomazetti RSI2 (TradingView Pine), adapted by Ausar |
| **Asset** | Crypto spot |
| **Timeframe** | 1h |
| **Universe** | ADAUSDT (Binance); ADA/USD (Alpaca forward) |
| **Style** | Mean reversion |
| **Status** | 2 waiting |

## Entry

- RSI(2) < 10, close > SMA200, SMA4 of RSI(2) < 30; long only.
- A target is good for 300 s after its bar completes.

## Exit

- Close > SMA5. The source's 10% stop is off.

## Sizing

- Binance book: 100% of cash incl. 10 bps, lot-floored. Alpaca forward: up to 10% of $100,000.

## Data

- Binance 1h klines and book ticker; Alpaca crypto bars for the forward.

## Variants

| Row | Venue | Size |
|---|---|---|
| ausar_public_tomazetti_rsi2_spot100 | Binance ADAUSDT | 100% cash |
| femto_fwd_alpaca_ada_rsi2 | Alpaca ADA/USD | ≤ 10% of $100,000 |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/ausar/ausar_spot_recipes.py`, `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py`, `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py`
- **Midna v3**: `sleeves/fwd_alpaca_ada_rsi2.py`, `sleeves/aster/aster_pub_rsi2_ada.py`. `fwd_alpaca_ada_rsi2` takes the signal as an input; the aster file's engine is not in this repo
