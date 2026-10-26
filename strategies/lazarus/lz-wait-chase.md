# CHASE weekly lane

Buys weekly Cyan fires in the top tenth of 126-day momentum that sit within 5% of their 63-day high, and holds 52 weeks.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Liquid cross-section (dv20 ≥ $1M, close ≥ $5, operating companies) |
| **Style** | Momentum |
| **Status** | blocked |

## Entry

- Signal: a tracker 1W Cyan fire whose 126-day momentum ranks ≥ 0.90 against the liquid cross-section and whose drawdown from the 63-day high is above -5%.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 52 weeks.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = 20.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger; the tracker engine's daily store for the cross-section.

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
