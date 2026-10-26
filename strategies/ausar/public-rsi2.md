# RSI(2) pullback

Buys an extreme 2-period RSI dip in an uptrend (close above the 200-bar average) and sells when price closes back above the 5-bar average.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Larry Connors' RSI(2), via trader.dev, StockCharts and Tomazetti's Pine script; the old swing desk via Femto-lean |
| **Asset** | US ETFs · US equities · crypto (ADA) |
| **Timeframe** | 1d · 1h |
| **Universe** | 15 liquid ETFs · 41-name old-desk basket · ADA |
| **Style** | Mean reversion |
| **Status** | 4 waiting |

## Entry

- ETFs: Wilder RSI(2) ≤ 5, close > SMA200 and close < SMA5 on the completed day; lowest RSI(2) first; the next open within 300 s; at most 10 names.
- Basket: RSI(2) < 10 and close > SMA200; checked hourly at :03; at most 8 positions.
- ADA 1h: RSI(2) < 10, close > SMA200 and the 4-bar average of RSI(2) < 30; a target is good for 300 s after its bar completes.

## Exit

- Close > SMA5 everywhere. ETFs: or 10 holding bars, no stop. ADA: the source's 10% stop is off.
- Basket: also RSI(2) > 70, +5%, -8% or 5 sessions, and an 8% stop from the fill.

## Sizing

- ETFs: floor(min(10% of equity, 1% of 20-day dollar volume, cash) / (ask × 1.001)).
- Basket: 0.25% of a $100,000 book on the 8% stop, whole shares.
- ADA: the Binance book uses 100% of cash incl. 10 bps, lot-floored; the Alpaca forward up to 10% of $100,000.

## Data

- Yahoo daily bars (ETFs); split-adjusted daily bars (basket); Binance 1h klines and Alpaca crypto bars (ADA).

## Variants

| Variant | Rows | Bars | RSI(2) entry | Extra exits |
|---|---|---|---|---|
| Public ETF recipe | `ausar_public_rsi2`; Midna v3 `aster_rsi2_1d` | daily | ≤ 5, close < SMA5 | 10 bars |
| Old desk basket (Femto-lean) | `femto_rsi_meanrev`; Midna v3 `rsi_meanrev` | daily | < 10 | RSI > 70, +5%, -8%, 5 sessions |
| Tomazetti ADA (Binance) | `ausar_public_tomazetti_rsi2_spot100`; Midna v3 `aster_pub_rsi2_ada` | hourly | < 10, RSI(2) 4-bar mean < 30 | none |
| Tomazetti ADA (Alpaca forward) | `femto_fwd_alpaca_ada_rsi2`; Midna v3 `fwd_alpaca_ada_rsi2` | hourly | as above | none |

Rows: 4 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch1.py`, `sleeves/rsi_meanrev.py`, `sleeves/fwd_alpaca_ada_rsi2.py`, `sleeves/aster/aster_pub_rsi2_ada.py`. `fwd_alpaca_ada_rsi2` takes the signal as an input; the aster file's engine is not in this repo
- **Master desk** (not in this repo): `desk/vendor/ausar/trader_signals.py`, `desk/sleeves/families/ausar_public.py`, `desk/sleeves/femto/rsi_meanrev.py`
- **Master desk (ADA)**: `sleeves/ausar/ausar_spot_recipes.py`, `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py`, `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py`

## Notes

- Midna v3's `rsi_meanrev` adds an Edge-IMPROVE change (2026-10-24, on by default): it drops the SMA5 exit and manages to +5%, RSI(2) > 70, -8% or 5 days.
