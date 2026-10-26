# R4 blowoff (daily / hourly)

Buys a rising-edge RSI + OBV blowoff (both in the top tenth of their 144-bar range) and holds 20 bars.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's R4 blowoff sleeves, via Femto-lean; detector after an @PredictionAlgos video |
| **Asset** | US equities |
| **Timeframe** | 1d · 1h |
| **Universe** | 1,838-name research genome (daily) · 41-name old-desk basket (hourly) |
| **Style** | Exhaustion (forward test) |
| **Status** | 1 live · 1 waiting |

## Entry

- Signal: Wilder RSI(14) and OBV both ≥ their trailing 144-bar min + 90% of the range; the first bar of each run.
- Daily: the edge on the latest closed bar, ≥ 252 bars, ≥ 20 sessions after the name's last signal, only while SPY's 60-session return is ≤ 0; ranked from 16:30 ET, bought from 10:30 ET the next session.
- Hourly: an edge in the last 5 closed regular-hours bars, ≥ 160 bars, ≥ 20 bars after the last signal; scans at :10, buys at :40, 10:00-15:59 ET.

## Exit

- Daily: sold once 19 bars have closed after entry (the 20th session); backstop 28 days. No stop.
- Hourly: sold 20 hourly bars after the bar that follows the signal; backstop 4 days. No stop.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Daily split-adjusted bars (600, cached) with the genome job's last-close blowoff rows; regular-hours hourly bars (400); desk quotes.

## Code

- **Master desk**: `sleeves/femto/blowoff_d.py`, `sleeves/femto/blowoff_1h.py`, `sleeves/femto/sleeve_core.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`, `sleeves/femto/vendor/old_desk_research/run_r4_blowoff_standalone.py`, `sleeves/femto/feedlib/blowoff.py`

## Notes

- The old desk switched both off on 2026-10-08 (they buy exhaustion tops); the master desk runs them as a forward test.
- The RSI x OBV detector reconstructs the method shown in an @PredictionAlgos video.
