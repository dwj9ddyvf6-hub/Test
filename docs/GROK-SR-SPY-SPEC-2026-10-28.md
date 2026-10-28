# GROK-SR-SPY — FROZEN SLEEVE SPEC (2026-10-28)

Provenance: X post by @thiccteddy (status 2115172431316856919, 2026-10-28) asked
Grok to "Design a sophisticated trading algorithm for this"; Grok's reply is the
algo below, screenshotted and sent by the desk owner with the order: "Look at
this and make a sleeve out of it." Sleeve id: `grok_sr_spy`.

## Grok's algo, verbatim substance

Algo for SPY 1-min horizontal S/R:

- Detect multi-session zones by clustering swing pivots + high-vol nodes into
  0.4-0.8 pt bands, ranked by touches/volume.
- Entry: Approach zone, rejection (long wick + vol >1.5x avg) for fade, or
  decisive close through + expanding vol for breakout.
- Invalid if reclaim within 3 bars.
- Confirm strong continuation via sequential holds outside with rising volume.
- Stop beyond zone, target next level or 2R. Limit to first 2 hrs RTH.

## Frozen implementation (precision choices named where Grok is terse)

Instrument: SPY shares, long and short, paper desk.
Data: 1-min bars, Alpaca SIP feed (desk volume law: volume signals on
1-min bars use SIP only). RTH session only.

### Zone map (built pre-open, static for the session, no repaint)
Inputs: the prior 10 RTH sessions of SPY 1-min bars (completed sessions only).
- Swing pivots: fractal pivot highs/lows, 5 bars each side, causally confirmed.
- Volume nodes: volume-at-price in 0.10 bins across the lookback; a bin is a
  high-volume node when its volume is at or above the 90th percentile of bins.
- Clustering: single-linkage over pivot prices and node prices with max gap
  0.40 pt. Band = [cluster min, cluster max]; if width < 0.40, expand
  symmetrically to 0.40; if width > 0.80, split at the largest internal gap
  and re-apply.
- Score: pivot touch count + node volume share. Keep the top 6 bands.
- A band above the current price is resistance; below, support (by position at
  evaluation time).

### Entry window
New entries only 09:30-11:30 ET (first 2 hrs RTH). Hard flat at 13:00 ET.

### Fade setup (fade resistance = short; fade support = long)
- Price enters a band from outside.
- Rejection bar: the wick beyond the band's far edge is at least 50% of the
  bar's total range, the bar closes back inside the band or beyond its near
  edge, and bar volume > 1.5x the trailing 20-bar average volume.
- Signal on that bar's close; intent fills at the next bar open (desk
  convention: evaluate on close, fill next open).

### Breakout setup
- A bar closes beyond the band's far edge by at least 0.10 pt, with body at
  least 60% of its range, volume greater than the prior bar's volume and at
  least 1.2x the trailing 20-bar average (expanding volume).
- Signal on that bar's close; fill at next bar open.
- Continuation confirm (hold rule): subsequent closes holding outside the
  band with rising volume confirm the move; no extra entry is taken on it.

### Invalidation (both setups)
If any bar closes back through the band (a reclaim of the zone) within 3 bars
after the entry fill, exit at the next bar open. After 3 bars the reclaim rule
lapses and only stop/target/hard-flat govern.

### Stop and target
- Stop beyond the zone: fade short stop = band top + 0.10; breakout long
  stop = band bottom - 0.10; mirrored for the other two directions.
- Target: the nearest band edge in the trade direction, or 2R from entry,
  whichever is closer. If no band lies in the trade direction, target = 2R.

### Bookkeeping rules (implementation choices, anti-churn)
- One open position at a time.
- A band that produced an exit (any reason) is dead for the rest of the
  session; it cannot trigger again that day.
- Max 3 entries per session.

### Desk install shape (mirrors trullas_divergence)
- sleeves/grok_sr_spy.py: pure causal signal core.
- adapters3/grok_sr_spy.py: desk adapter.
- Config row in config/sleeves.json: module adapters3.grok_sr_spy,
  cadence_s 60, parked=false, slice capital_usd 10000, session rth,
  inputs include bars:SPY:1Min (exact producer key to be confirmed by scout;
  use the real key the desk serves, never an invented one).
- tests/test_grok_sr_spy_blockers.py wired into run_regression_blockers.sh:
  golden-fixture tests with independently computed expectations for zone
  clustering, fade trigger, breakout trigger, reclaim invalidation, and
  stop/target math; causality tests (zones use prior sessions only; signals
  use bars up to the signal bar only).
- proof/install/grok_sr_spy.json; build report GROK-SR-SPY-BUILD.md.
- Edge status: UNPROVEN. The live paper record is the test; no backtest is
  claimed or implied by this install.
