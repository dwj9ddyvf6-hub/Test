# CARM recovery memory

A 90% QQQ core plus short intraday trades on registered shock-recovery order-book episodes; with none registered it holds QQQ.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | CARM, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities and QQQ |
| **Timeframe** | Intraday (≤ 30 minutes) |
| **Universe** | QQQ and registered episode stocks |
| **Style** | Order-book microstructure (registered inputs) |
| **Status** | blocked |

## Entry

- Core: QQQ 90%, re-set at the month's first pass while no episode is open.
- Inputs: a hand-kept registry file of episodes (bid and ask order-lifecycle summaries or events, anchors, fitted lower and upper estimates, support counts).
- Admission, 10:02-14:40 ET, one look per episode: at least 500 training episodes over 100 dates and 60 calibration dates; a defined bid-minus-ask commitment; an incremental lower bound > 5 bp and gross lower - QQQ upper > 2 × cost (≥ 15 bp) + overhead + 10 bp; the registered CPDW edge > 5 bp; a spread ≤ 4 bp; none within 30 minutes of the name's last exit or after a 1% daily loss.
- Order: a limit at the ask + $0.01 for 10 seconds, min(5% of equity, the 10% sleeve's room); at most 2 positions.

## Exit

- First of: the bid 40 bp under or 60 bp over the entry, 30 minutes after the fill, 10 minutes before the close, or a 1% daily account loss; sold at the market.

## Sizing

- $1,000,000 book; fractional shares.

## Data

- The registry file and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/carm.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/carm/`
