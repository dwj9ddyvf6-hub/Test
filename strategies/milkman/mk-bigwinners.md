# Big Winners weekly Tensor sleeve

Buys $1,000 of every liquid, calibrated weekly Tensor Cyan / Green fire, one per name, holds 52 weeks, inside a $50,000 budget.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Galath research lab, bigwinners study (W52S-CAL) |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | 1,822 US stocks (the store_v1 survivors) |
| **Style** | Tensor signal, many small positions |
| **Status** | 2 live |

## Entry

- Weekly fire: a closed weekly Tensor bar with a buy-cyan or buy-green marker (bar ≥ 60).
- Stream: 20-day dollar volume ≥ $1M; not avoided (price ≥ $100; Cyan within 5% of the 52-week high; XLF, XLB, XLRE; Cyan in XLU; Green within 13 weeks of the name's last fire); calibrated (Cyan: ≤ $14.94 or a 60-week depth ≥ 70.35%; Green: ≤ $13.15 with a 20-week standard deviation of weekly returns ≥ 0.08896).
- Order: the desk score (5.5, plus up to 1 for the calibration boosts when dollar volume ≥ $2M), then dollar volume; one position per name.
- Budget: open cost basis ≤ $50,000 less realised losses.
- Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.

## Exit

- At the close of the 52nd week after the fire week, market-on-close.

## Sizing

- Whole shares = floor($1,000 / the live ask); a $100,000 book.
- Paced row: a weekly token bucket (starts at 1, refills $50,000 / (52 × $1,000) a week, holds at most 3), one token an entry.

## Data

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes).

## Variants

| Row | Pace |
|---|---|
| `mk_bigwinnersmanysmallpositionssleeve` | every eligible fire |
| `mk_bigwinnerspacedtokenbucketvariant` | token bucket, ≤ 3 saved |

## Code

- **Master desk**: `sleeves/milkman/galath.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)

## Notes

- The Tensor engine these lanes run (desk/vendor/galath_engine/) is not published in this repo.
