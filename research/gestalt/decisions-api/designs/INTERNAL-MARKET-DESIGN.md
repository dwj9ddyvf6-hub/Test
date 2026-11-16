# DESIGN: THE INTERNAL MARKET (Invention 1)

Status: DESIGN ONLY, Sat 2026-11-14. No build today. Registration:
midna-book/strategy-candidates/2026-11-14-invention-internal-market.md.

## Mechanism

Stop asking which sleeve is good; make the fleet price itself.
Every fire becomes a contract. When a sleeve fires, it stakes
virtual capital on its own fire at odds implied by its own stated
geometry: the fire's target and stop define a breakeven win
probability p_self = stop_dist / (stop_dist + target_dist). A
market maker (an automated market maker over a virtual book, LMSR
or a simple continuous double auction against a house book)
quotes a market probability p_mkt per fire, seeded from the
fleet's base rates for that sleeve family and phenotype, updated
as peer sleeves take positions for or against the fire with their
own signal strength. At resolution (target, stop, or the fire's
horizon), contracts settle in R. Sleeves accumulate a market P&L
distinct from their trading P&L: a sleeve can be a mediocre
trader and a superb pricer, and the estate currently cannot tell
the difference.

The allocable quantity the market produces: each sleeve's
**pricing gap** = realized frequency minus its average self-priced
probability, and its market Brier score. Capital allocation reads
the gap: sleeves whose fires beat their own odds earn flow;
sleeves systematically overconfident in their own geometry get
their geometry audited, not their feelings hurt.

Extremizing, from the research report (section 1.4/1.6): raw
fleet-average probabilities are systematically under-confident
(Good Judgment Project: aggregation in log-odds space with an
extremizing coefficient a > 1 was the single largest accuracy
lever, ~35% of gains). The market's aggregate price therefore
applies logit extremizing with a fitted on calibration data only.
Kalshi's full-history calibration record (Brier 0.08-0.09 at
3 months out improving to ~0.02 at close) is the template for what
the market's own reliability diagram must look like before its
prices are allowed to steer anything.

## Data contracts (against the attribution ledger)

Reads, nightly, from runs/attribution_ledger_v1.json (recomputed
inside resolution-harvester-nightly): per sleeve: own_closes,
wins, losses, win_rate, expectancy_usd, realized_usd,
excess_vs_spy_usd, avg_hold_days, sessions, fills, flags, klass.
Consumed as: family base rates for market-maker seeding (win_rate
by sleeve family where own_closes >= 30 pooled), settlement truth
(realized outcomes per fire join the ledger's per-sleeve closes),
and the honesty flags (a NETTED sleeve's market contracts settle
as UNGRADED until the fleet flip cleans its attribution).
Writes: its own append-only market ledger in the research lane
(fire, p_self, p_mkt, positions, settlement, market P&L per
sleeve). Never writes to the desk, the fill ledger, or the
attribution ledger.

## Build order

1. Contract writer: fires (Ghost Book capture from Mon 2026-11-16
   plus the intent journal) become contracts with p_self from
   fire geometry; no market yet, just the contract population.
2. Static pricer: p_mkt = family base rate, extremized; Brier and
   log score per sleeve and per family, graded by the harvester.
   This stage alone already computes the pricing gap.
3. LMSR market maker with peer positioning: sleeves stake on
   fires (their own and others') proportional to their signal
   confidence fields where present; virtual capital only.
4. Allocation read: a shadow allocator compares market-priced
   allocation versus equal-weight on forward R, in shadow, for a
   full quarter before any live allocation reads it.

## Dive-Two Fold-In (added Sat 2026-11-14, Deep Dive Two section 2)

This section folds Deep Dive Two section 2 into this design by
name. Where it conflicts with the mechanism above, the fold-in
governs the SEQUENCE: the scored poll comes first, the market
only if the poll proves insufficient.

1. Start with scored polls, not a market. The production-proven
   stack is: question discipline first (unambiguous resolution
   criterion, source and date fixed before forecasts); strictly
   proper scoring (log score for the AI team, because it forces
   tail honesty; Brier for human-readable reporting); then
   aggregation.
2. Aggregation recipe: weighted average (weights from recent,
   domain-matched Brier plus update frequency), then extremize
   on a logit scale, with the overlap caveat stated in the dive
   in terms: the extremizing factor tends to 1 as information
   overlap tends to 1. Everyone reading the same note is the
   failure case; estimate overlap before extremizing, and do
   not extremize a consensus that shares one source.
3. Herding cure: independent first forecasts are LOCKED before
   any aggregate is seen (Delphi round 1), then deliberation.
   This amends the peer-positioning stage above: no sleeve or
   node sees the fleet aggregate before its first price is
   sealed.
4. If a market is ever built: LMSR, with the worst-case operator
   loss b x ln(n) budgeted in advance as the explicit price of
   information. Set b from what one resolved question's
   information is worth; if that b makes prices too jumpy to
   use, there are not enough participants for a market and the
   design returns to polls. The LMSR stage in the build order
   above inherits this budget rule.
5. Optimism bias is measured, not assumed away. Cowgill and
   Zitzewitz on Google's markets: optimism coefficient about
   minus 0.103 overall and about minus 0.239 on own-project
   deadlines (about minus 0.039 on demand questions). This
   design therefore includes: per-question-type de-biasing
   estimated on resolved history, and a ban or flag on
   position-taking by project owners on their own questions.
   For this estate, a sleeve's owner-equivalent (its authoring
   lane) is flagged on contracts about that sleeve.
6. Decision rights are decided IN ADVANCE: which decisions the
   internal price may override is written here before any price
   exists. Corporate markets (Google, Lilly, Ford) died
   organisationally, not empirically: a live price contradicting
   a decided plan became a politics problem. Ruling for this
   design: in its first two quarters the internal price may
   override NOTHING; it is an evidence instrument whose stage-4
   shadow comparison (below) earns or fails to earn decision
   rights. The rights, if earned, are granted by a written
   amendment naming the decision class, never by drift.
7. Bayesian Truth Serum is EXPERIMENT-ONLY, never an allocation
   input (Lehmann 2025 review: evidence for verification-free
   mechanisms is sparse and weak, and uninformative equilibria
   exist). BTS may be run as a side experiment on unresolvable
   questions; its outputs steer no capital.

Dive-Two section 2 falsifiable test, carried: run 50
pre-registered internal questions in parallel by (a) simple
median, (b) weighted plus extremized poll, (c) LMSR market.
Prediction: (b) beats (a) on Brier by at least 10 percent; (c)
does not beat (b) with under 10 regular participants, and shows
a positive optimism bias on own-strategy questions that (b) with
locked first forecasts does not. If (c) beats (b) at this scale,
publish the b, the participation, and the subsidy spent per unit
of Brier improvement.

## Falsifier

Restated from the registration: market-priced allocation fails to
beat equal-weight allocation on forward R over a quarter, in the
stage-4 shadow run, and the invention dies. Interim kill: if the
stage-2 static pricer's fleet Brier is no better than the raw
base-rate constant after 300 settled contracts, the pricing-gap
premise itself is empty and stages 3-4 are never built.
