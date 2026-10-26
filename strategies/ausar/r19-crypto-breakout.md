# R19 crypto breakout and negative-funding squeeze

Buys a completed 4-hour close above the prior 20-bar high on Binance spot. The squeeze books also need a negative perpetual funding rate.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 crypto research, run as the R19 native-spot books |
| **Asset** | Crypto spot |
| **Timeframe** | 4h |
| **Universe** | ADAUSDT, ENJUSDT, LINKUSDT |
| **Style** | Breakout |
| **Status** | 2 live · 22 waiting · 12 blocked |

## Entry

- Signal: a completed UTC 4h close above the highest high of the prior 20 bars.
- Squeeze books also need the latest known funding settlement to be negative: settled in or before the signal bar, received before the decision, at most 12 h before the bar's close.
- Buys 4 h after the signal bar closes, inside a 5-minute window, on a fresh quote: spread ≤ 100 bps and last trade ≤ 60 s old.
- Long only, one position per book, and only signals after the book's activation.

## Exit

- fixed16 / fixed96: sells 16 h or 96 h after the entry time.
- Structural exits on a completed bar after entry. normalization: funding ≥ 0. normalization_failure: funding ≥ 0 and the close is below the prior 3 bars' lowest low. lost_breakout: the close is below the breakout level. Each sells from the next bar, with the 96 h deadline as the backstop.
- No stop.

## Sizing

- fullcash: all book cash at the ask, net of the 10 bps fee.
- volume1pct: capped at 1% of the volume of the 4h bar that completes at entry.
- Floored to the venue lot; the buy fills slice by slice through the displayed depth.

## Data

- Binance spot 4h klines (340), depth and last trade; Binance USD-M funding history. US hosts get HTTP 451 there, so the master desk relays the rate from CoinGecko.

## Variants

| Parameter | Values |
|---|---|
| Coin | ADAUSDT · ENJUSDT · LINKUSDT |
| Funding filter | none (`breakout_base`) · funding < 0 (`negative_funding_squeeze`) |
| Exit | `fixed16` (both) · `fixed96`, `normalization`, `normalization_failure`, `lost_breakout` (squeeze) |
| Sizing | `fullcash` · `volume1pct` |

Rows: 36 on the master desk, 36 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_crypto.py`, `desk3/aster_batch7.py`, `desk3/aster_batch8.py`, `desk3/aster_b11_crypto.py`, `desk3/aster_b12_crypto.py`, `desk3/aster_batch13.py`, `integration/aster_*_adapter.py`. The ADA files under `sleeves/aster/` call `aster_sleeves._common`, which is not in this repo
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_crypto.py`, `desk/sleeves/families/r19_crypto.py`. The vendored Ausar original
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)

## Notes

- Midna v3 buys at the signal bar's close when it evaluates, not 4 h later. Its deadlines count from the fill, and `volume1pct` reads the bar before the signal bar.
