# AIRT auction impulse

Buys a stock after a registered opening-auction impulse routes to continuation or recovery with calibrated expectancy, holding up to 30 minutes; with no episodes registered it holds cash.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | AIRT, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities |
| **Timeframe** | Intraday (≤ 30 minutes) |
| **Universe** | Registered morning episodes |
| **Style** | Opening-auction microstructure (registered inputs) |
| **Status** | waiting |

## Entry

- Inputs: a hand-kept registry file of each session's morning episodes (the 09:35 opening displacement, volume and auction ratios, two probe paths with flow and impact, spreads, VWAPs, ADV, the last minute's dollars, the 1-minute sigma, matured label records).
- Route: a volume ratio ≥ 2, an auction ratio ≥ 1.25, a displacement ≥ max(20 bp, 1.5 × its scale), and a second-probe spread ≤ 8 bp and ≤ 70% of the first; continuation (an up move holding ≥ 80% through both probes with buying flow, building impact and the mid above both VWAPs) or recovery (a down move with selling then neutral flow, rebounding impact and the mid above the first VWAP).
- Admission: at least 200 earlier events over 60 dates in its cell, and mean - 1.645 SE > 2 × the round trip + 10 bp.
- Order: by 09:50 ET, one attempt per name and session, a limit at the ask + 2 bp for 90 seconds.

## Exit

- First of: 15:45 ET, the bid at entry × (1 - d) or at entry × (1 + 2d), the recovery's residual back to zero, 30 minutes after the first fill, with d = max(10 bp, half the displacement, 2 × the 1-minute sigma); sold at the market.

## Sizing

- $1,000,000 book: shares = min(0.1% of equity / d, 10% of equity, 0.1% of ADV, 2% of the last minute's dollars) / price, within 4 names, 40% gross, 25% a sector and 10% a name; no entry after a 0.5% session loss or a 5% drawdown.

## Data

- The registry file and live quotes (SPY for the recovery residual).

## Code

- **Master desk**: `sleeves/quant_research/airt.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/airt/`
