# AI volume spike crypto (4h)

Buys LINK on a 4-hour bar with volume over twice its average that closes up and above its 50-bar EMA; exits after 5 bars.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | AI Volume Strategy (TradingView Pine), adapted by Ausar |
| **Asset** | Crypto spot |
| **Timeframe** | 4h |
| **Universe** | LINKUSDT (Binance); LINK/USD (Alpaca forward) |
| **Style** | Volume breakout |
| **Status** | 2 waiting |

## Entry

- Volume > 2 × EMA20(volume), close > EMA50 and close > open.

## Exit

- Flat on the 5th bar of the position (the source counter), or on an opposite spike.

## Sizing

- Binance: 100% of cash incl. 10 bps. Alpaca forward: up to 10% of $100,000.

## Data

- Binance 4h klines; Alpaca crypto bars.

## Variants

| Row | Venue |
|---|---|
| ausar_public_ai_volume_spot100 | Binance LINKUSDT |
| femto_fwd_alpaca_link_ai_volume | Alpaca LINK/USD |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b4.py`, `sleeves/fwd_alpaca_link_ai_volume.py`
- **Master desk**: `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py`, `sleeves/ausar/ausar_spot_recipes.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
