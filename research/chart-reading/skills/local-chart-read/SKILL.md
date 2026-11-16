---
name: chart-read
description: On-demand chart reading that runs deterministic Pass A geometry, renders multi-timeframe charts, and delivers a perceptual Pass B read with scenarios, triggers, and invalidation whenever the user names a ticker; skip for automated signal runners, which have their own engines.
version: 1.0.0
---

# Chart Read — On-Demand Protocol

## Why this skill exists

The default: Reading a chart by impression and calling the impression analysis.
The cost: Timeframes treated as independent witnesses double-counted one move as three confirmations, and the call inherited confidence it never earned.
The replacement: Geometry first, perception second, abstention allowed: a read that cannot name its invalidation has not been made.

Source of truth: your own synthesis document (set CHART_READ_SYNTHESIS to its path; the protocol below is the executable form of its geometry and epistemic-contract parts).



Source of truth: `~/workspace/research/composite-confidence/GRAND_SYNTHESIS_2026-10-07.md`.
This skill is the executable form of Parts II + III + the epistemic contract.

## When to use

The owner names a ticker and wants a read ("read NVDA", "what's PLTR doing",
"chart check on AMD"). Not for Femto sleeve signals — those have their own
runners. This is discretionary chart reading, on demand, at a whim.

## Procedure

### 1. Pass A — geometry (no model, no narration)
```bash
cd ~/workspace/skills/chart-read && python3 bin/pass_a.py --symbol SYM
```
Returns JSON: weekly regime (MA10/40, pivots), daily structure (confirmed
5-bar pivots, EMA20/50/200, ATR14, volume vs 20d, close location unit+signed,
ATR-cut level tests on recent swings — kind-aware: a bar below a prior high
can never be a "rejected-low-test" — gaps, ATR50, level clusters (2.5:
ATR-scaled pivot zones with touches vs independent episodes), declared
round-number grid), momentum layer per thesis A.1
contracts (RSI14 Wilder, MACD 12/26/9, StochRSI 14/3/3, CCI20, ADX14/DMI, CMF20,
MFI14, ATR50,
OBV slope, session VWAP, pivot-paired RSI divergence, EMA stack,
Fib retracement zones of the last swing — labeled policy levels, not
forecasts; pivots carry both extreme time and availability time (2.5:
a pivot is learned at confirmation)), pattern primitives (inside/outside bar, streaks,
pivot sequence HH-HL/LH-LL), 1H rhythm (MA20/50), 10m refinement (MA20/50,
session VWAP, close vs VWAP in ATR). Indicator conventions are embedded in
the JSON's `conventions` block. Save the JSON to
`~/workspace/research/composite-confidence/reads/<SYM>_<date>_passa.json`.

Parity tests: `python3 bin/test_pass_a.py` — 18 checks, all green as of
2026-10-08. Re-run after any edit to pass_a.py.

### 2. Render the four charts
```bash
cd ~/workspace/research/composite-confidence/calibration
python3 render_asof.py --symbol SYM --outdir \
  ~/workspace/research/composite-confidence/reads/<SYM>_<date>/
```
Renders weekly, daily, 1H, and 10m PNGs ending now.

### 3. Look — perceptual protocol (Part II of the synthesis)
Max resolution, whole → parts. Axis/frame inventory. Legend/series registry.
Transcribe key values before interpreting. Context before pattern names.
Describe-then-decide with pixel re-verification. Comparative check vs the
archetype vocabulary. Counter-deception sweep. **View the actual PNGs**
(`muse.read` injects images) — never narrate from Pass A numbers alone.

**Reconciliation** (thesis 4.3): if the image and Pass A disagree on a
material fact (image shows price above EMA20, Pass A says below), that
disagreement is a diagnostic object — stop. Check bar completeness /
provisional status, adjustment basis, and axis scale. Do not narrate
through it or resolve it by eyeball majority.

**Timeframes are not independent witnesses** (thesis 2.8): 10m/1H/1D share
the same underlying transactions. Agreement across frames is not
confirmation — ask what the lower frame adds that the daily doesn't
already show.

**Abstention is not a call** (thesis 4.10): ABSTAIN is an evidence status,
distinct from substantive bearishness. "No view" is never silently
converted into a bear call, and insufficient evidence is never dressed
up as AVOID.

### 4. Pass B — the read (model narrates Pass A objects only)
Deliver in this order:
1. **Reference class** — one line: what setup family this resembles, or
   "not established here."
2. **Structure** — regime (W), stage (D), rhythm (1H). Every level named
   with its anchor; distances in ATR.
3. **The tell** — volume verdict. Falsifies or caps conviction.
4. **The two questions, separately** — "still going up?" vs "safe to buy
   here?" Never merge them.
5. **Scenario tree** — 3 branches (bullish / bearish / neutral). Each:
   trigger, confirmation, target + method, invalidation, confidence
   (LOW/MED — never HIGH on a single read), what would raise it. A branch
   with no visible trigger stays EMPTY.
6. **Pre-mortem** — how this read is wrong in two weeks.
7. **Self-critique** — the strongest case against the delivered lean.

Epistemic contract: observe ≠ interpret (labeled); probabilities not
predictions; ambiguity valid; invalidation mandatory; base rates only from
a published table or "not established here"; steelman the opposite.

**Neutral measured language** (thesis 4.4): "price traded below the prior
low and closed back above it" is verifiable; "a liquidity sweep trapped
shorts" adds a mechanism OHLCV does not prove. Banned: "smart money is
preparing a move," "genuine accumulation," "distribution," "trapped"
(used of participants). A tolerance around a level is a tolerance, not a
fabricated new Fibonacci line.

**Structure first, patterns as interpretations**: the structure section
leads with location, trend/regime, volatility, participation, and
structural maturity — a named pattern is an interpretation of those
relationships, never the starting point.

**Evidence classes** (thesis §1.3): tag every substantive claim in the read
with one of [computed] (deterministic from bars — pivots, ATR distances,
indicator values), [measured] (Pass A extraction, e.g. volume ratio),
[lit-derived] (published finding — Marshall 2006, Lu/Chen/Hsu 2015, etc.),
[derived-inference] (logic built on the above, e.g. "rejection + light
volume caps continuation odds"), [validated-model] (a scored, audited
model — none exist for these reads; say so), or [judgment] (discretionary
pattern read). A read with no [computed]/[measured] anchor for a claim
doesn't make the claim.

**Paired rendering** (thesis H2, cheap version): when the whole read hinges
on one contested visual feature (a wick, a trendline touch, a shelf),
render the chart twice — with and without the feature — and check whether
the read changes. If it doesn't survive the pair, it wasn't a read, it
was a suggestion.

Save the read to `~/workspace/research/composite-confidence/reads/<SYM>_<date>.md`.

## Turning it into action

After delivering the read, offer (don't assume):

1. **Trigger watch** — for any branch with a clean trigger, set a cron
   running `bin/watch_trigger.py --symbol SYM --read-date <date>
   --bullish-above X --bearish-below Y`. It prints one line; the cron
   notifies the owner ONLY when a trigger fires, silent otherwise. Paper-only
   by nature — it watches, never orders.
2. **Paper order** — only on the owner's explicit word, via the alpaca-paper
   skill. A read is not an order. Never imply one.
3. **Log it** — reads with dated triggers are the raw material for the
   prospective log (Part IX.2 of the synthesis). Trigger watches that
   fire produce scored outcomes.

## Rules

- One read per ticker per day unless new information arrives.
- Never more than 10 reads per calendar day (Batch 3 was fatigue-risk).
- Missing volume = capped conviction, stated.
- A weekly bar does not contain five knowable daily bars — no invented
  higher timeframes.
- "Not visible = not known."

## Addendum — Echo/Max methodology layer (the owner, 2026-10-12)

Source: `~/workspace/research/chart-methodology/PLAYBOOK_echo_max_2026-10-12.md`
(134-post corpus, deep-read 2026-10-12). These conventions now bind every
Pass B read, on top of the Grand Synthesis protocol:

1. **Cycle position first.** Before indicators: name where price sits in
   its cycle (impulse leg, correction leg A/B/C, terminal pattern —
   wedge/triangle — or base). The read's lean follows from the position.
2. **Levels are zones with confluence.** Build candidate zones from the
   fib retracement of the defining impulse (0.5/0.618 shelf; 0.786/0.887
   deep shelf), then score confluence: +1 each for an MA cluster
   (50/200 DMA/WMA) inside the zone, a trendline arriving there, a prior
   pivot shelf, a round number. A lone fib is a watch level, not a zone.
3. **Trendline discipline.** At most two lines, anchored on confirmed
   major pivots spanning the whole pattern. A line price has already
   closed through is dead — never re-drawn, never re-reported as news.
4. **Divergence arms, the level fires.** RSI/MACD divergence counts only
   at pattern extremes (tops, wedge terminals, C-wave lows). It arms a
   level; the trigger is always the 50MA reclaim/loss or the zone
   reaction, named in advance with its price.
5. **Both scenarios drawn.** Primary and alternate paths both get a
   terminus price (the alternate's flush/target box included), so the
   read carries its own invalidation geometry.
6. **Verdict grammar.** Close the read with one conditional line in
   their form — "Losing $X confirms the move to the buy zone at $Y–$Z.
   Patience." — then the full Pass B apparatus (volume tell, two
   questions, pre-mortem, evidence tags) stands behind it.
## Available connectors

Use `muse.connector_search` to find the current connector docs before following
recovered instructions.
