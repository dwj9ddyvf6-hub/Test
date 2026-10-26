# Liquid 126-session momentum

Holds the top tenth of liquid names by 126-session return, re-ranked every 63 sessions, in equal dollars.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Midna's swing basket |
| **Style** | Momentum |
| **Status** | live |

## Entry

- Liquid: close ≥ $5 and 20-session mean dollar volume ≥ $1M (SOXL excluded); rank by adjusted 126-session return; take the top floor(10%), at least 1, when 10+ names are liquid.
- Re-stages the rank every 63 panel sessions; reviews from 10:00 ET on a fresh panel.

## Exit

- A name leaves at the next review it is not in.

## Sizing

- Equal dollars = equity / names; shares = floor(dollars / (price × (1 + cost))), cost 5-50 bps by price; sells first.

## Data

- Midna's daily panel (Yahoo adjusted closes).

## Code

- **Master desk**: `sleeves/midna/context.py`, `sleeves/midna/common.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
