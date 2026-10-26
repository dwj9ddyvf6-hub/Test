# Crypto confirmed absorption (4h)

Buys the 4-hour bar that closes back above the midpoint of a high-volume down bar, then sells 16 hours later.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar crypto research: the original absorption books and the R19 funding-filter books |
| **Asset** | Crypto spot |
| **Timeframe** | 4h |
| **Universe** | ADAUSDT, ENJUSDT, LINKUSDT |
| **Style** | Mean reversion |
| **Status** | 5 live · 11 waiting · 4 blocked |

## Entry

- Shock bar: volume > 2 × EMA20(volume), close < open, close < EMA50(close). The EMAs include the bar and seed at the first bar.
- Confirmation: the next bar closes above its open and above the shock bar's (high + low) / 2, after at least 300 completed bars.
- R19 books: optional funding filter (none, negative, non-negative) and entry 4 h after the confirmation bar closes, in a 5-minute window.
- Original books (ENJ, LINK): buy at the ask within 300 s of the confirmation bar's close.

## Exit

- R19 books: sell 16 h after the entry time.
- Original books: sell at the bid from 16 h after the confirmation bar's close.
- No stop, no pyramiding.

## Sizing

- R19 books: `fullcash` (all cash, net of 10 bps) or `volume1pct` (≤ 1% of the entry bar's volume).
- Original books: 100% of book cash including the 10 bps fee, floored to the lot, capped by the displayed ask size.

## Data

- Binance spot 4h klines, book ticker and last trade; funding for the filtered R19 books.

## Variants

| Parameter | Values |
|---|---|
| Coin | ADAUSDT · ENJUSDT · LINKUSDT (R19); ENJUSDT · LINKUSDT (original) |
| Funding filter (R19) | none (`absorption_base`) · < 0 (`absorption_negative_funding`) · ≥ 0 (`absorption_nonnegative_funding`) |
| Sizing (R19) | `fullcash` · `volume1pct` |

Rows: 20 on the master desk, 20 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_crypto.py`, `desk3/aster_batch7.py`, `desk3/aster_b11_crypto.py`, `desk3/aster_batch1.py`, `integration/aster_*_adapter.py`. The ADA files under `sleeves/aster/` call `aster_sleeves._common`, which is not in this repo
- **Master desk** (not in this repo): `desk/vendor/ausar_ctx/strategies/absorption/signals.py`, `desk/sleeves/families/absorption.py`, `desk/sleeves/families/r19_crypto.py`

## Notes

- Midna v3 buys at the latest close when it evaluates. Its original books add a one-bar catch-up, on by default: when the confirmation was one bar ago and the close still holds the shock bar's midpoint, it buys late and keeps the original 16 h deadline.
