# Milkman filters on Tensor lanes

Takes Galath's Tensor lane fires through the Milkman study's add-on rules: four lanes, each with one filter or boost.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study's add-on rules, on Galath research lab's Tensor lanes |
| **Asset** | US equities |
| **Timeframe** | 1w · 1d |
| **Universe** | 1,822 US stocks (the store_v1 survivors) |
| **Style** | Tensor signal + filters |
| **Status** | live |

## Entry

- Lanes: weekly Cyan and Green (a closed weekly bar with the marker, bar ≥ 60); daily Green (bar ≥ 250); daily Swing (a green bar within 3 bars of its setup square).
- Weekly Cyan unless EMA13 crossed above EMA48 in the last 10 days; weekly Green unless the fire day closed exactly 3 lower closes.
- Daily Green unless the Phase Oscillator is ≥ 61.8; daily Swing at double size after a compression release up in the last 5 days.
- 20-day dollar volume ≥ $100,000.
- Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.

## Exit

- Held 78 weeks (weekly lanes), 60 sessions (daily Green) or 40 (daily Swing), then sold market-on-close.

## Sizing

- $1,000 a fire ($2,000 for a boosted Swing); a $5,000,000 book.

## Data

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes).

## Code

- **Master desk**: `sleeves/milkman/galath.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`

## Notes

- The Tensor engine these lanes run (desk/vendor/galath_engine/) is not published in this repo.
