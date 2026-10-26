# Tensor 1H swing flagship

Buys fresh confirmed Tensor swings (confidence 8+) on canonical hourly bars of the old basket with a bracket at the engine's invalidation and target, risking 1% a trade.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | 41-name old-desk basket |
| **Style** | Tensor signal |
| **Status** | blocked |

## Entry

- Signal: the newest confirmed swing of the Tensor v698 engine on canonical 1H bars, at most 3 bars and 6 clock hours old, not acted on before.
- Trade at confidence ≥ 8 (6-7 is watch only); not extended; the latest bar's low still above the planned stop; not held; at most 10 positions, 3 per sector.
- Order: a GTC bracket limit at the signal close, take-profit at the engine's target, stop at its invalidation.

## Exit

- The bracket's stop or target; a bearish trigger on either of the last two closed bars (bearish conflict, more bear than bull votes, consensus-sell); or more than 20 closed bars held.

## Sizing

- 1% of the book risked on entry - stop, × 0.75 when a held name's 1H-return correlation ≥ 0.65 (× 0.5 at 0.80); notional ≤ 50% of the book.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The canonical Tensor feed (1H), split-adjusted daily bars (300).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/tensor_swing.py`
- **Midna v3**: `sleeves/tensor_swing.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no trade whose target is closer than its stop.
