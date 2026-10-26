# VXX call tail hedge

When VIX is complacent (under 16, or in the bottom quarter of its last 30 closes), buys one VXX call about 20% out of the money ~90 days out, and sells it on a doubling, a VIX spike over 30 or 21 days to expiry.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | ETP options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | VXX |
| **Style** | Tail hedge |
| **Status** | waiting |

## Entry

- Complacent: VIX < 16 or below the 25th percentile of its last 30 closes (35+ closes needed).
- The call: per expiry 60-110 days out the strike nearest 1.20 × spot; the expiry nearest 90 days first; two-sided within 20% of mid; a limit at the ask; one hedge at a time.

## Exit

- Value 2× the debit, VIX > 30, or ≤ 21 days to expiry; sold at the mid.

## Sizing

- Premium ≤ 1% of the book.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Yahoo ^VIX daily closes (130), the desk's 60-110 DTE VXX call chain and quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/vix_hedge.py`
- **Midna v3**: `sleeves/vix_hedge.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)
