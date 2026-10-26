# Donchian 20/10 breakout

Buys a close above the prior 20 bars' highs and exits on a close below the prior 10 bars' lows or a 2-ATR trailing stop.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities · crypto (SOL) |
| **Timeframe** | 1d · 15m |
| **Universe** | 41-name old-desk basket · SOL/USD |
| **Style** | Trend breakout |
| **Status** | 1 live · 1 waiting |

## Entry

- A close above the highest high of the prior 20 bars, with volume > 0.
- Equities: checked daily at 10:32 ET, at most 8 positions. SOL: every closed 15-minute bar, one position.

## Exit

- A close below the lowest low of the prior 10 bars, or the low touching a trail that ratchets to close - 2 × ATR(14) and never loosens.
- Equities also: a 20-session time stop and a 25% disaster stop.

## Sizing

- Equities: 0.25% of the book on the 25% disaster-stop distance (1% notional); the sleeve at most 25% of the book.
- SOL: 0.25% of the book on 2 × ATR, at most 25% notional; at least $10 when that still fits both caps.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (160); Kraken public 15-minute SOL bars (120), traded as SOL/USD.

## Variants

| Variant | Rows | Bars | Universe | Extra exits | Positions |
|---|---|---|---|---|---|
| Equities | `femto_donchian`; Midna v3 `donchian` | daily | 41-name basket | 20-session time stop, 25% disaster stop | 8 |
| Crypto | `femto_donchian_crypto`; Midna v3 `donchian_crypto` | 15-minute | SOL/USD | none | 1 |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/donchian.py`, `desk/sleeves/femto/donchian_crypto.py`
- **Midna v3**: `sleeves/donchian.py`
- **Midna v3 (SOL)**: `sleeves/donchian_crypto.py`

## Notes

- Midna v3 adds Edge-IMPROVE changes (2026-10-24, on by default): the equity time stop fires only when the position is not in profit; the SOL entry is refused when the close is more than 2 ATR over the breakout level.
