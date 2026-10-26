# CQR contract queue revaluation

Buys an issuer the session after a registered contract award re-optimizes its order book to a positive value gain, for up to 63 sessions; with no packets registered it holds cash.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | CQR, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities |
| **Timeframe** | 1d (up to 63 sessions) |
| **Universe** | Registered contract issuers |
| **Style** | Event-driven (registered inputs) |
| **Status** | waiting |

## Entry

- Inputs: a hand-kept registry file of contract packets (the issuer's order book before and after the award, resource capacity, settlement, market value, a forecast and its cost).
- Admission at the prior close: both books re-optimized under the same capacity give a gain / market value > 0; at least 100 matured clusters, 20 issuers, 24 months and 30 calibration clusters; the forecast above 2 × max(15 bp, the measured side cost) + 50 bp.
- Entry: the next session 09:35-10:05 ET only, whole shares, a marketable limit that expires at 10:05; weight = min(5%, the 25% sector and 15% cluster room, the 95% gross room); at most 20 issuers.

## Exit

- First of: 63 sessions, the bid 8% under the entry, or a revoked packet; sold at the market.
- A 20% drawdown from the peak NAV sells everything and pauses entries for 20 sessions.

## Sizing

- $1,000,000 book; unallocated cash stays cash.

## Data

- The registry file and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/cqr.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/cqr/`
