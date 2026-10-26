# Buyback before earnings (call spreads)

Buys a call debit spread 8-15 days before earnings on a stock that announced a buyback of 5%+ of its shares 15-30 days before the report, and holds through the event.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Quantpedia #0271 (Amini & Singal, buybacks before earnings); the old swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | 73 basket and phase names |
| **Style** | Event drift (options) |
| **Status** | waiting |

## Entry

- Signal: an 8-K repurchase announcement of ≥ 5% of the shares, filed 15-30 days before the earnings date; the weekday EDGAR scan no older than 8 days.
- Entry 8-15 days before earnings on a fresh calendar; stock ≥ $10; at most 4 positions, 2 per sector.
- Structure: a call debit spread in the nearest 30-45 DTE expiry (long = highest strike ≤ spot, short = the first strike ≥ long × 1.10, debit 30-45% of the width, long-leg spread ≤ 10%); else a call ≥ 2% out of the money (spread ≤ 15%); both must expire after earnings.

## Exit

- 15 trading days after earnings, +50% or -50% on the debit, or 5 days to expiry.

## Sizing

- 0.5% of the book in debit a trade.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The EDGAR buyback scan (8-K text), the earnings calendar, 30-45 DTE call chains and quotes, sector map.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/earnings_buyback.py`, `desk/feedlib/edgar_buyback.py`
- **Midna v3**: `sleeves/earnings_buyback.py`

## Notes

- SEC requests stay off until the owner sets a contact, so the scan has no fresh input until then.
- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the expiry must be at least 26 days after earnings.
