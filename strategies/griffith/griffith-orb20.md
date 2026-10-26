# 20-minute opening range breakout

Buys the first 5-minute close above the 09:30-09:50 range on a name whose opening volume is at least twice its usual, stopped at the range low and flat at 15:55.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 parallel strategy lab (ORB20_RVOL_1_0_0) |
| **Asset** | US equities |
| **Timeframe** | 5m |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | Opening-range breakout |
| **Status** | waiting |

## Entry

- Qualify, after 09:51 ET: the four completed 5-minute bars of 09:30-09:50, with that window's volume ≥ 2 × the median of the same window over the prior 20 complete sessions.
- Entry: the first completed 5-minute bar after the range closing above its high, while the ask is above the range low; a marketable limit good for 10 minutes, once per name a day.

## Exit

- Stop at the range low; flat from 15:55 ET.

## Sizing

- A fixed slot of $100,000 / 550 (about $182) per name.

## Data

- 5-minute bars of the universe (Alpaca; Yahoo without keys), about 22 sessions.

## Code

- **Master desk**: `sleeves/griffith/griffith_intraday.py`, `sleeves/griffith/feedlib/griffith.py`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)
