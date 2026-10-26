# TCFT index-flow swap

A 99% QQQ book that swaps up to 20% into stocks facing a registered index-rebalance flow gap; with no events registered it holds QQQ.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | TCFT, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities and QQQ |
| **Timeframe** | 1d (to the event's endpoint) |
| **Universe** | QQQ and registered index-event stocks |
| **Style** | Index-event flow (registered inputs) |
| **Status** | blocked |

## Entry

- Core: QQQ 99%, bought once at the live quotes.
- Inputs: a hand-kept registry file of index events (the original target row, owner-lot scenarios, price, 60-session dollar ADV, the endpoint session, bounds and support counts).
- Admission at 18:30 ET of session D: a valid original index target; positive lower bounds on the timed debt and the time-cut gap; price × the gap's lower bound / ADV ≥ 0.1 with its width ≤ half its upper bound; at least 300 event clusters, 60 securities, 30 calibration clusters and 5 years; a funded net lower bound ≥ 20 bp and a positive paired base increment.
- Breakers: no new admissions after a 10% drawdown or a 2% drop against QQQ.
- Execution: on D+1 09:45-10:00 ET sell QQQ worth min(4% of NAV, 0.25% of the 60-session dollar ADV, the 20% budget left); on D+2 09:45-10:00 buy the stock with a limit 3 bp over the ask, good for 15 minutes.

## Exit

- First of: 15:50 ET of the endpoint session, the bid 5% under the entry, or a registered correction or vanished gap; sold at the market, and the QQQ restored at the next 09:45 window.

## Sizing

- $1,000,000 book; each stock leg is the QQQ notional it displaced, in fractional shares.

## Data

- The registry file and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/tcft.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/tcft/`
