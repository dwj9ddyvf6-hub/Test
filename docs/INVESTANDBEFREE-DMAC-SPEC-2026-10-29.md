# INVESTANDBEFREE-DMAC — FROZEN SLEEVE SPEC (2026-10-29)

Sleeve id: `investandbefree_dmac`. Source: clean-room extraction at
`~/workspace/opt/rea-teardowns/investandbefree/SPEC.md` (public material
only; no paid course material was opened), frozen by owner order
2026-10-29. This doc freezes the desk implementation of that spec.
An extraction is not a backtest: edge is UNPROVEN and the live paper
record is the test.

Provenance labels follow the source SPEC: **extracted** (stated in
public material), **inferred** (deduced from examples), **recreated**
(public record silent; a default frozen here so the rule set is
executable and falsifiable), **deviation** (desk v1 differs from the
source SPEC, named explicitly).

## Instruments and variant

- Underlyings: SPY and QQQ only. **recreated** narrowing for the desk
  forward test (source SPEC: a liquid underlying).
- Variant: the LONG-TERM variant only; entry timeframe daily; context
  stack 4H / daily / weekly. **extracted** (stack), confidence High.
- Long premium only: bullish buys calls, bearish buys puts. No
  spreads, no short premium, no Greeks-based selection. **extracted**,
  confidence High.

## Indicators

- Two MACDs on closes, on every timeframe in the stack:
  MACD-W uses Wilder smoothing for every EMA component (fast, slow,
  and the signal line); MACD-E uses standard exponential smoothing
  for every component. **extracted** for the pair's existence.
- Periods 12 / 26 / 9 for both MACDs. **recreated**, confidence Low
  (sealed in the course; platform defaults frozen).
- Closed bars only; a forming bar is never evaluated. **recreated**
  guard, confidence Medium.

## Timeframes

- Daily bars and weekly bars as served by the desk warm product.
- 4H bars are aggregated in the pure core from 1H bars: RTH bars only
  (bar start 09:30 to 16:00 ET), grouped by ET session date, chunked
  in consecutive groups of 4 hourly bars anchored at the session's
  first RTH bar; a bucket is emitted only when it holds exactly 4
  consecutive hourly bars. **recreated** operational form of the
  **extracted** 4H stack member.

## Alignment and dominance

- Alignment on a timeframe: bullish (+1) when BOTH MACD lines are
  above their own signal lines; bearish (-1) when BOTH are below;
  anything else (including equality or insufficient history) is no
  alignment. **extracted** as concept, **recreated** in this exact
  form.
- Dominance: the slowest timeframe (weekly, then daily, then 4H)
  whose two MACDs agree in one direction is the dominant timeframe.
  **extracted** concept, **recreated** operational form.
- A trade requires the dominant direction to equal the DAILY
  direction. Disagreement means no trade. **recreated** operational
  form of the source gate.

## Trigger (last CLOSED daily bar; either)

- (a) Crossover: MACD-E crosses its signal line in the aligned
  direction on that bar. **extracted**, confidence High.
- (b) Curl: after a pullback against the aligned direction (at least
  one counter-direction step in the MACD line over the prior two
  steps), MACD-W or MACD-E changes line direction back into the
  aligned direction on that bar, while daily alignment holds.
  **extracted** concept, **recreated** exact step form.
- The source SPEC's ladder fallback (staged re-entries at later
  curls) is NOT implemented in v1. **deviation**: v1 takes the
  primary trigger only; one open position per underlying, two total.

## Entry construction

- Strike: nearest-to-the-money (smallest |strike - spot|; ties take
  the lower strike). **recreated**, confidence Low.
- Expiry: the nearest listed expiry at least 30 calendar days out.
  **recreated**, confidence Low.
- Quote gate: (ask - bid) / mid <= 0.10, mid = (ask + bid) / 2, or no
  trade; an unquotable contract (ask <= 0 or bid <= 0) fails the
  gate. **recreated** (the 10% figure is the source SPEC's recreated
  gate value).

## Sizing

- Premium budget USD 2,000 per position (the vendor's worked-example
  low end). **extracted** examples, **recreated** as the desk rule.
- Hard cap: total premium at entry <= 25% of the sleeve slice
  (USD 2,500 on the frozen slice). **recreated** desk rule.
- qty = floor(budget / (ask x 100)), further capped so total premium
  stays within the hard cap; if one contract alone exceeds the hard
  cap, no trade.

## Exits (first trigger wins, in this order)

1. Premium stop: position premium (quote mid) at or below 50% of
   entry premium, full exit. **recreated**, confidence Low.
2. Dominant-timeframe alignment break: the current dominant
   direction exists and differs from the position direction, full
   exit. **recreated** operational form.
3. Partial at premium >= +100% over entry: sell
   ceil(qty x entry / current) contracts, enough to recover the full
   original premium, always leaving at least 1 runner contract; if
   qty is 1 the partial is a full exit. Fires once per position.
   **extracted**, confidence Medium-High (threshold and construction);
   the contract-count formula is **recreated**.
4. Runner exit: MACD-E crosses against the position on the daily
   timeframe, or the position reaches 5 DTE, whichever first.
   **extracted** (cross concept), **recreated** (5-DTE form; the
   source's overbought/oversold runner exit is not implemented, named
   here as a **deviation**). The runner ignores 4H flips while daily
   alignment holds (daily-layer hold). **extracted**, confidence
   Medium-High.

## No-trade gate

- Timeframe disagreement (dominant direction != daily direction):
  no trade. **recreated**, labeled ours in the source SPEC.
- Quote spread over the gate: no trade. **recreated**, labeled ours.
- DEVIATION, explicit: the vendor's event-calendar gate items are
  NOT implemented in v1. The source SPEC's recreated daily-variant
  calendar item (no new entry on CPI / FOMC / underlying earnings
  days) is not wired: index ETFs have no earnings, and no macro
  calendar producer is wired for this sleeve. Entries therefore do
  not check any event calendar in v1.

## Config (frozen)

- slice capital_usd 10000 / cash_usd 10000, cadence_s 3600, session
  rth, flat_by_close false, parked=false (live paper from install).
- One open position per underlying, two total.

## Provenance summary

Extracted: the double-MACD pair (Wilder + exponential), the
long-term timeframe stack, alignment/dominance as concepts, the
crossover and curl triggers, long-premium-only construction, the
+100% partial-into-runner management, the daily-layer hold, the
USD 2,000 worked-example budget figure.
Recreated defaults frozen here: periods 12/26/9, ATM strike, the
30-calendar-day expiry bound, the 50% premium stop, the budget/cap
sizing rule, the 10% spread gate, the exact alignment/dominance/
curl step forms, the 5-DTE runner bound.
Deviations: no ladder fallback; no overbought/oversold runner exit;
no event-calendar gate (named above).
Edge: UNPROVEN. No backtest is claimed; the live paper record is
the test.
