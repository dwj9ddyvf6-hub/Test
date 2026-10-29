# Grok support and resistance (SPY)

Trades SPY 1-minute bars against a static map of horizontal support and resistance bands built from the prior 10 completed sessions: fades with a rejection wick, and breakouts on a decisive close.

| | |
|---|---|
| **Family** | Muse |
| **Source** | X post by @thiccteddy, algo by Grok, installed by owner order 2026-10-28 |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Support and resistance fade and breakout |
| **Status** | Midna's desk only |

## Entry

- Zones: fractal swing pivots (5 bars each side) plus volume-at-price nodes (0.10 bins at or above the 90th percentile), clustered into 0.40 to 0.80 point bands; top 6 bands kept; the map is fixed for the session.
- Fade: price enters a band from outside, prints a rejection wick beyond the far edge of at least 50% of the bar range, and closes back inside the band or beyond its near edge, on volume above 1.5x the trailing 20-bar average.
- Breakout: a bar closes beyond the far edge by at least 0.10 with body at least 60% of range, volume above the prior bar and at least 1.2x the trailing 20-bar average.
- At most 3 entries a day; none at or after 11:30 ET.

## Exit

- Stop beyond the band far edge by 0.10; target the nearest band edge in the trade direction or 2R, whichever is closer.
- A close back through the band within 3 bars after the fill exits (reclaim invalidation); hard flat at 13:00 ET.

## Sizing

- 0.25% of slice equity at risk per trade, 25% notional cap; whole shares.

## Data

- SPY 1-minute SIP bars; zones from the prior 10 completed regular sessions only.

## Code

- **Midna v3**: `sleeves/grok_sr_spy.py`, `adapters3/grok_sr_spy.py`

## Notes

- Edge unproven by design: the live paper record is the test; no backtest is claimed.
- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json row grok_sr_spy, added 2026-10-29 to close the catalog diff of that date.
