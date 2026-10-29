# PRZM Recreation Specs — FROZEN 2026-10-29

Source: `TEARDOWN.md` (PARTIAL) in this directory; evidence manifest
`evidence/meta/capture_manifest.sha256` (6,788 entries). Public material only.
Paper only. No backtest claim is made for either strategy; each proves itself
forward on live paper records or dies by its kill criterion.

Provenance grades, used on every rule: **extracted** = in the public record,
quoted in the teardown. **inferred** = deduced from observable public behavior,
reasoning in the teardown. **recreated** = our frozen default where the record
is silent. Relay equivalence is unverifiable (teardown claim 12): every numeric
rule below is extracted from the public client fallback `localRead()` in
`demo_zero.html`, and only inferred for the live relay.

Global freeze rules (both strategies):

- F1. No parameter in this document changes after the first live session.
  A change voids the record, restarts the count at zero, and requires a new
  spec version. (**recreated** governance rule, per task instruction.)
- F2. Paper slice: $10,000 per strategy, separate ledgers. (**recreated**,
  per task instruction.)
- F3. Every call is ledgered at the moment it is made (time ET, state, SPY
  price, score, all five drivers, regime) before any grading exists, and
  graded at +30 minutes with right and wrong both counted. No call is
  deleted, including stand-aside and Fade Edges states that resolve.
  (**extracted** grading ethic: manual "Every call graded in the open";
  **recreated** ledger-before-grading mechanics.)
- F4. If a required input is unavailable at decision time, the strategy emits
  its waiting state (below), never an estimated call. A waiting day is
  recorded as a waiting day, not a flat day. (**recreated**.)

---

## Strategy 1: PRZM Zero Recreation (SPY same-day lean)

### Claim and kill criterion

- Falsifiable claim: over live paper sessions, directional calls (long or
  short) graded sign-only at +30 minutes are right more than 55% of the time,
  and the Fade Edges / stand-aside states are not hiding directional losses
  (audited by grading the score's sign at every state change as a shadow
  record, reported separately, never traded). (**recreated** thresholds.)
- Kill criterion: after 100 graded directional calls, right-rate is at or
  below 52%, OR after 40 sessions fewer than 30 produced a gradable call
  because inputs were in the waiting state. Either kills the sleeve; the
  ledger is published internally either way. (**recreated**.)

### Inputs and data routes (what we actually have today)

| Input | Route today | Status |
|---|---|---|
| SPY spot and 1-minute candles, incl. the 30-minute reference price and 5-candle move at each print | Alpaca market data `GET /v2/stocks/SPY/bars`, timeframe 1Min, `feed=sip` for history (lags ~15-18 min) and `feed=iex` for real-time RTH; explicit `start` param and `next_page_token` pagination required (desk-proven quirks, AGENTS.md 2026-09-27/28) | Available |
| Today's SPY options contracts (same-day expiry list, strikes, type) | Alpaca `GET /v2/options/contracts?underlying_symbols=SPY&status=active&type=<call|put>&expiration_date_gte=<today>&expiration_date_lte=<today>`; filter tradable client-side, no `sort` param (desk-proven) | Available |
| Options quotes for trade-direction classification | Alpaca `GET /v1beta1/options/quotes/latest?symbols=...&feed=indicative` (desk-proven path) | Available |
| Options snapshots (OI, IV, greeks per contract) | Alpaca `GET /v1beta1/options/snapshots?symbols=...` (desk-proven path) | Available, snapshot cadence only |
| Signed same-day options print tape: every print with size, price, timestamp, and a directional bull/bear flag, sweep flag, opening/closing flag, paired-leg identity | No desk route proven today. Alpaca options trades exist under v1beta1 in principle, but no desk code path, credential scope check, or live sample was verified in this teardown, and PRZM's own `bull`, sweep, opening, and paired-leg flags are vendor-derived fields whose construction is not in the public record | **NOT YET AVAILABLE** — see waiting state |
| Gamma magnet, gamma flip, call/put walls (server-supplied levels in PRZM) | Not an Alpaca field. Computable in principle from snapshot OI + greeks, but no desk implementation exists or was verified today | **NOT YET AVAILABLE** — see waiting state and Strategy 2 |
| IV per print for Black-Scholes delta | Snapshot IV when present; fallback IV 0.16 (**extracted**: fallback defaults IV to 0.16 when out of range) | Available with extracted fallback |

Waiting state (honest, frozen): until a signed print tape route is proven by
a live sample (one full session captured, fields inspected, direction
classification spot-checked against quotes), Zero Recreation runs in
**WAITING: NO PRINT TAPE** state: it computes and ledgers the PX driver and
SPY candles only, emits no lean, makes no paper trade, and grades nothing.
This is a named input gap, not a strategy failure; the 40-session kill clock
in the kill criterion counts waiting days so the gap cannot hide forever.
(**recreated** state design; the gap itself is established from the route
table above.)

Direction classification once a tape exists (**recreated**, record silent on
how PRZM derives `bull`): a print at or above the ask is buyer-initiated, at
or below the bid is seller-initiated, inside the spread is unclassified and
gets weight 0 (matching the extracted mid-print rule in effect). Call prints
buyer-initiated or put prints seller-initiated are bullish-signed; the mirror
pair is bearish-signed. Sweep, opening, and paired-leg flags are dropped, not
approximated, until the tape carries them natively (teardown recreated
decision rule).

### Print weighting (all extracted from the fallback unless noted)

Signed value per print: `v = bull * |delta| * size * 100 * spot * w`, delta
from Black-Scholes `ncdf(d1)`. Weight `w`:

- `w = 0`: mid print or no directional flag.
- `w = 0.15`: `|delta| < 0.1`, or price < 0.12 with `|delta| < 0.2` (lottery wings).
- `w = 0.2`: put bought at ask with `|delta| < 0.25` and OTM > 0.6 (insurance).
- `w = 0.5`: `|delta| > 0.85` (deep in the money).
- Otherwise `w = 1`. Multipliers: sweep x1.35, opening x1.25, closing x0.7 —
  applied only if the tape natively carries those flags (see above).
- Paired-leg cancellation (opposite print, near-equal size within
  max(2, 12% of size), within 2,500 ms: remove the earlier contribution,
  move both premiums to aside): **dropped** in this recreation because our
  tape cannot identify pairs; dropping it is stated here, not silent.
  (**recreated** decision, per teardown.) Consequence named: paired spreads
  will count directionally in our record where PRZM sets them aside; if the
  kill criterion fires, this is a named suspect, not a tuning excuse.

### Chasing discount and contrarian premium (extracted)

For each print, `m5` = SPY's move over the 5 candles ending at the print, in
volatility units. If `|m5| > 0.8`: `w *= 0.55` when the print agrees with the
move (chasing; manual "counts about half"), `w *= 1.25` when it leans against
the move (contrarian premium; manual "counts more").

### The five-driver equalizer (extracted)

Prints bucketed in 5-minute buckets of signed net vs absolute flow. Each
driver is a net/abs share in [-1, +1], displayed x100:

| Driver | Definition |
|---|---|
| SES | Signed share of all filtered flow since the open |
| 30M | Signed share over the last 30 minutes |
| 10M | Signed share over the last 10 minutes |
| STDY | Fraction of the last 4 non-empty buckets whose net sign agrees with blended flow F, displayed as a percent |
| PX | `tanh((spot - c30) / c30 / (v1 * sqrt(30)) / 1.5)`, the 30-minute price move in volatility units, squashed |

Blend: `F = 0.3*SES + 0.4*30M + 0.22*10M + 0.08*5M` (the 5-minute share is in
the blend but is not a displayed driver). Score:

```
x = F * (0.7 + 0.3 * STDY)
x *= price agrees ? 1 + 0.15*|PX| : 1 - 0.25*|PX|
if pin:  x *= 0.85; x += 0.18 * clamp((magnet - spot) / max(0.05, expected move))
if run:  x *= 1.15
if before 10:00 ET: x *= 0.75
if from 15:45 ET:    x *= 0.6
score = round(clamp(x, -1, 1) * 100)
```

Pin/run terms apply only when the gamma levels exist (Strategy 2 input);
until then both multipliers and the magnet pull are omitted and the omission
is ledgered with each call. (**recreated** degradation rule.)

### Make / hold / drop hysteresis (extracted)

- Make: from neutral, score >= +25 makes LONG, score <= -25 makes SHORT,
  otherwise STAND ASIDE. (Manual: "It takes a clear read to make a call.")
- Flip: opposing score x -direction >= 35 flips directly to the other side.
  The flip bar (35) exceeds the entry bar (25): asymmetric hysteresis.
- Drop: to neutral only when score x direction < 8 AND at least 600,000 ms
  (10 minutes) have elapsed since the call was made. (Manual: "a real fade
  to drop one"; a call holds at least 10 minutes.)
- Every state change ledgers `{time, lean, SPY price}`.

### Window (extracted manual, extracted code damping)

Calls matter from 09:45 to 15:45 ET. The fallback has no hard 09:45 gate; it
damps x0.75 before 10:00 and x0.6 from 15:45. Recreation: no new call is made
before 09:45 or after 15:45 (**recreated** hard gate from the manual's
instruction "Zero starts to matter after 9:45"), the extracted phase damping
applies inside the window's edges as written above, and any open call is
force-closed and graded at 15:45 regardless of the drop rule (**recreated**:
PRZM grades open calls in its log per the screenshot, but no forced-close
rule is in the public record).

### Execution on the paper slice (recreated; PRZM itself is a lean, not an order)

Manual usage rule (**extracted**): "Trade with the call at the level it
names. When it says stand aside, stand aside." Recreation mechanics
(**recreated**): on LONG or SHORT, buy the same-day SPY contract in the call
direction nearest the named level (nearest listed level in that direction,
else session high/low or expected-move distance, per the extracted plan-tile
default) for a fixed $1,000 notional per call (echoing the demo Zero Fund's
"$1,000 each", teardown claim 15, unverifiable as a live record); exit on
flip, drop, or 15:45. Stand aside and Fade Edges states hold no Zero position.
Total exposure is capped by the $10,000 slice; a call that cannot be filled
inside the slice is ledgered as skipped, not resized.

### Grading (extracted method, recreated ledger)

Each directional call is graded at the first SPY 1-minute price at or after
call time + 1,800,000 ms: RIGHT if the sign of (price then minus price at
call) matches the call direction, WRONG otherwise, zero move grades WRONG.
Sign-only, no magnitude floor, no cost: stated plainly because it inflates
"right" versus any economic measure (teardown claim 8). The running record
reports calls made, graded, right, wrong, and right-rate, plus the separate
paper P&L on the $10,000 slice; the two are never merged into one number.

---

## Strategy 2: Fade Edges Recreation (pin-regime mean reversion)

### What the record supports, and what it does not

**Extracted**: Fade Edges is the neutral-in-a-pin call state, not a fourth
directional call (word = long / short / fade edges if neutral in pin /
stand aside otherwise). Manual: "In a pin, fade the edges to the magnet. In a
run, don't fight it." Pin damps the Zero score x0.85 and pulls it toward the
magnet; run amplifies x1.15. Regime in the fallback is `pin = spot > gammaFlip`
with server-supplied gamma levels.

**Not in the record**: any numeric definition of a session "edge", any entry
distance, stop, or target beyond "to the magnet", and the gamma levels
computation itself. Those are recreated below and graded as such. If the
gamma input cannot be built from our snapshot route, this strategy cannot be
recreated and stays in its waiting state; the magnet is its core and will not
be replaced by a VWAP or prior-day level under this spec's name.

### Claim and kill criterion

- Falsifiable claim: on live paper, in pin-regime sessions, SPY touches of a
  session edge that are faded toward the magnet reach the magnet before the
  invalidation level in more than 50% of trades, net positive on the $10,000
  slice after Alpaca paper fills as executed. (**recreated**.)
- Kill criterion: after 30 closed fade trades, magnet-first rate is at or
  below 45%, OR the slice is down 10% ($1,000), OR 40 sessions pass with
  fewer than 10 pin-regime trade days because the gamma input is unavailable.
  Any one kills it. (**recreated**.)

### Inputs and routes

| Input | Route today | Status |
|---|---|---|
| SPY 1-minute candles, session high/low, spot | Alpaca `/v2/stocks/SPY/bars` 1Min, `feed=iex` RTH real-time, `feed=sip` history (as Strategy 1) | Available |
| Same-day SPY options contracts + snapshots with open interest and greeks | Alpaca `/v2/options/contracts` + `/v1beta1/options/snapshots` (as Strategy 1) | Available as snapshots; intraday OI is prior-close OI in practice (**inferred** from how OI is published; named, not assumed fresh) |
| Gamma magnet and gamma flip | **Recreated computation** (below) from snapshot OI and greeks; no desk implementation exists today | **NOT YET AVAILABLE** until built and sample-verified; waiting state until then |

Gamma computation (**recreated**, record silent): per snapshot pull (frozen
cadence: 09:40 ET, then every 30 minutes), for each same-day SPY strike,
gamma exposure = OI x gamma x 100 x spot, signed positive for calls and
negative for puts (dealer-long-gamma convention). Magnet = strike with the
largest absolute net gamma exposure. Flip = strike where cumulative net gamma
exposure, summed from the lowest strike up, changes sign. The last pull of
the day is the level set for the rest of the session; levels never update
inside a trade.

### Pin and run tests (extracted test, recreated fallback named)

- Primary test (**extracted**): pin when spot > gamma flip; run when spot <=
  gamma flip, exactly as the fallback codes it.
- No secondary or substitute regime test is defined. If gamma levels are
  unavailable, there is no regime, no fade, and the state is
  **WAITING: NO GAMMA LEVELS**. Inventing a volatility or range based pin
  test under this spec is prohibited by F1/F4. (**recreated** prohibition.)

### Edges, entry, target, invalidation (recreated; manual direction extracted)

- Session edges (**recreated**): the running session high and session low of
  SPY 1-minute bars, first printable at 10:00 ET (before that the "edges" are
  the opening range and are not faded; **recreated** guard).
- Entry (**recreated** mechanics on the extracted rule "fade the edges to
  the magnet"): in a pin, when SPY trades within 0.05% of the session high
  and that high is above the magnet, sell short SPY (paper) toward the
  magnet; mirror at the session low below the magnet, buy long. If an edge
  is on the far side of the magnet already (edge crossed the magnet), no
  trade: the fade thesis is spent.
- Size (**recreated**): fixed $2,000 notional per fade, one fade per edge per
  session, max two open fades, inside the $10,000 slice.
- Target (**extracted** destination, **recreated** execution): the magnet
  level; exit in full on a 1-minute close at or through the magnet.
- Invalidation (**recreated**): a 1-minute close 0.15% beyond the faded edge
  exits in full at market. A regime flip to run while a fade is open also
  exits in full at the next minute's open (manual, **extracted**: "In a run,
  don't fight it").
- Window (**recreated**, aligned to Strategy 1): entries 09:45 to 15:15 ET;
  all fades closed by 15:45 ET at market if neither target nor invalidation
  hit, and graded as closed at that price.

### Grading (recreated)

Every fade ledgers entry time, edge, magnet, flip, regime, and price before
the outcome exists. Outcome classes: MAGNET FIRST, INVALIDATION FIRST,
REGIME EXIT, or TIME EXIT, with paper P&L. The headline measure is the
magnet-first rate in the claim above; P&L is reported beside it, never
instead of it. Stand-aside (run) days ledger the regime series so a later
audit can confirm fades were actually withheld in runs.

---

## Open items carried honestly

1. Signed options print tape: no proven desk route; Strategy 1 waits.
   Unblock: one verified live session capture from an Alpaca v1beta1 options
   trades route, or another licensed tape, with fields inspected.
2. Gamma levels: no desk implementation; Strategy 2 waits, and Strategy 1
   runs without its pin/run score terms (ledgered omission) once its tape
   exists.
3. Relay equivalence of every extracted fallback number: unverifiable from
   public material (teardown claim 12). These specs recreate the fallback,
   and say so.
4. All PRZM performance figures (88%, 7 of 8): unverifiable, not used
   anywhere in these specs as a target or expectation.
