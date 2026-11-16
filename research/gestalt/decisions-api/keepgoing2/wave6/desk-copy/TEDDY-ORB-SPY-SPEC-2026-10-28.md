# TEDDY-ORB-SPY — FROZEN SLEEVE SPEC (2026-10-28)

Provenance: X post by @ThiccTeddy (status 2115172431316856919, posted
2026-10-27) captioned "This is my most profitable day trading strategy:" with
a 2:54 narrated video. The video content was verified from the logged-out
post page by a read-only browser pass on 2026-10-28: an opening-range
breakout strategy with volume, presented on a 5-minute chart. The desk owner
ordered this sleeve built as the companion to grok_sr_spy (Grok's separate
redesign of the same idea): "Build the opening-range version too"
(2026-10-28). Sleeve id: `teddy_orb_spy`.

## The strategy as presented in the video

- Draw the opening range: the high and the low of the opening period, drawn
  as horizontal zones across the 5-minute chart, with a volume pane below.
- Good example: price breaks the opening range on comparatively HIGH volume,
  pulls back on LOWER volume, then continues in the breakout direction.
- Failed example: price breaks down on LOW volume, the pullback comes back
  into the range on HIGHER volume, and price action turns choppy.
- Stated rule, paraphrased: look for high volume on the break of the opening
  range and lower volume on the pullback after it.

## Frozen implementation (precision choices named where the video is terse)

Instrument: SPY shares, long and short, paper desk. (The video states no
legible symbol; SPY is chosen because the desk's SPY intraday data path is
proven and the companion sleeve trades SPY.)
Data: 5-minute bars. Volume law: intraday volume uses Alpaca SIP only. If
the desk serves no native SPY 5Min key, the core aggregates the proven
SPY 1Min SIP bars into 5-minute bars deterministically (scout decides and
names the route).

### Opening range
- The first 30 minutes of RTH: the six 5-min bars 09:30-10:00 ET.
  OR high = their highest high; OR low = their lowest low. (30 minutes is
  the named choice; the video does not state the opening period length.)
- The range is fixed at 10:00 ET and never repaints.

### Breakout qualification (direction only, no entry yet)
- A 5-min bar closes above OR high (long side) or below OR low (short side).
- Volume condition (the strategy's core rule): the breakout bar's volume is
  at least 1.5x the mean volume of the six opening-range bars. A close
  through the range without that volume does NOT qualify (the failed
  example's low-volume break).
- The breakout must occur by 12:00 ET or the day is done.

### Pullback and entry (the tradeable sequence)
- After a qualified breakout, wait for a pullback of 1 to 6 bars (5 to 30
  minutes) that retraces toward the broken range edge WITHOUT any bar
  closing back inside the opening range.
- Lower-volume condition: every pullback bar's volume is below the breakout
  bar's volume, and the pullback's mean volume is below the breakout bar's
  volume (lower volume on the pullback, per the rule).
- Entry trigger: the first bar after the pullback that closes beyond the
  pullback's extreme in the breakout direction (above the pullback high for
  longs, below the pullback low for shorts), with that bar's volume greater
  than the last pullback bar's volume (volume returning for continuation).
- Signal on that bar's close; intent fills at the next bar open (desk
  convention).
- If no entry triggers within the 6-bar pullback window plus 6 further bars
  of drift outside the range, the setup expires.

### Invalidation
Any 5-min close back inside the opening range at any point after the
breakout, before or after entry, kills the setup or exits the trade at the
next bar open. (The failed example: the higher-volume return into the range
is exactly the churn this rule refuses.)

### Stop and target
- Stop: just beyond the broken range edge, inside the range: for longs,
  OR high minus 0.10; for shorts, OR low plus 0.10. This sits inside the
  invalidation rule as the hard broker-side stop.
- Target: the measured move, the opening-range height projected from the
  broken edge, or 2R from entry, whichever is closer.

### Bookkeeping rules (implementation choices, anti-churn)
- One open position at a time.
- One qualified breakout per direction per day: an invalidated or completed
  direction is dead for the session; the opposite direction may still
  qualify once.
- No entries after 12:30 ET. Hard flat at 14:00 ET.

### Desk install shape (mirrors trullas_divergence and grok_sr_spy)
- sleeves/teddy_orb_spy.py: pure causal signal core.
- adapters3/teddy_orb_spy.py plus the v2 adapter per the desk contract the
  scout establishes.
- Config row in config/sleeves.json: module adapters3.teddy_orb_spy,
  cadence_s 60, parked=false, slice capital_usd 10000, session rth, inputs
  per scout with the real SPY bar keys.
- Serialization with the grok_sr_spy install: this sleeve lands AFTER
  grok_sr_spy. The roster goes 315 (post-grok) to 316; roster pin tests are
  re-read at edit time and moved from their then-current value, never
  assumed.
- tests/test_teddy_orb_spy_blockers.py, gate-wired by discovery: golden
  fixtures with independently computed expectations (OR construction, a
  qualifying high-volume breakout, a low-volume break that must NOT
  qualify, the pullback-continuation entry sequence, a close back inside
  the range invalidating, stop/target values), plus causality tests.
- proof/install/teddy_orb_spy.json; build report TEDDY-ORB-SPY-BUILD.md.
- Edge status: UNPROVEN. The live paper record is the test; no backtest is
  claimed or implied by this install.
