# Tensor breadth timing (IWM)

Holds IWM when few stocks show strong weekly Tensor votes (breadth at or below its train-period median), else cash.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Galath research lab, TENSOR_CREATIVE breadth study, on Galath's Tensor engine |
| **Asset** | US ETF |
| **Timeframe** | 1w |
| **Universe** | IWM |
| **Style** | Breadth timing |
| **Status** | live |

## Entry

- Breadth: the share of the 1,822 names whose closed weekly Tensor bar has ≥ 5 bullish votes (weeks with ≥ 500 names).
- In when the latest week's breadth is at or below the median of the weeks to 2023-09-29 (at least 20 of them).
- Decided once the week's scan is in; trades the next session at the market.

## Exit

- To cash when breadth is above the median.

## Sizing

- The whole $100,000 book in IWM, or none.

## Data

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes).

## Code

- **Master desk**: `sleeves/milkman/galath.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`

## Notes

- The Tensor engine these lanes run (desk/vendor/galath_engine/) is not published in this repo.
