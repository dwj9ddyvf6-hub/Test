# TRUTH SERUM, GRADING PASS 1 (Sat 2026-11-14)

Invention 4 (INVENTION-BRAINSTORM.md). Every fire in the Ghost
Book estate map (21 Tensor fires, bar_date 2026-11-11, expiry
2026-11-27) scored implied-move versus target. IV inverted from
each fire's own recorded ATM call mid (Black-Scholes, r=4%, q=0),
spot = 2026-11-12 close, the session the chain was fetched.
PASS := target distance exceeds the implied move. Tool:
tools/truth_serum.py. Numbers: runs/truth_serum_v1.json.

## Headline result: zero of twenty-one pass, at every horizon

Target distances run 1.9% to 7.3%. Implied moves to expiry run
10.3% to 30.0% (IVs 51% to 148%; this universe is high-beta
names: SOXL, TTMI, HIVE, IREN, AAOI all above 100% IV). The
horizon objection was tested before it could be raised: scaling
the implied move to 3, 5, or 10 sessions instead of expiry still
passes zero fires. The market's expected fluctuation dwarfs what
these signals ask for, on any clock. The serum's literal verdict
on the estate's flagship fire population is unanimous: the
options market has already priced a move two to six times larger
than every target in the book.

## The two readings, both carried

1. **The invention's reading.** Per the brainstorm: when implied
   exceeds the target, the market has already paid for the idea
   and the share trade is late. On this reading the Tensor swing
   family trades inside the noise band the market prices, and
   its targets are set at a fraction of one sigma at every
   horizon, which is a statement about the signal family's
   geometry that no share-side grading ever surfaced.
2. **The design-flaw reading.** A share trade does not need to
   beat the straddle; it needs expectancy net of its stop. A 5%
   target with a 0.75% stop can be a fine share trade inside a
   20% implied move. On this reading the serum as registered
   grades the wrong quantity for shares and its proper home is
   exactly where the Ghost Book already uses it: the options
   expression, where the breakeven must clear the implied move
   or the expression cannot pay. Noted: serum verdicts agree
   with the Ghost Book's expression-viability verdicts on only
   10 of 21 fires, so the two surfaces are not measuring the
   same thing even there.

## Interim forward read (two sessions, named as such)

Sessions 2026-11-12 and 2026-11-13 were a sharp selloff. All 21
fires touched their stops intraday; one touched its target; mean
progress to target at the 2026-11-13 close is -2.43 (price moved
2.4 target-distances the wrong way). With an empty PASS cohort
there is no contrast to grade; this paragraph is a tape record,
not evidence for or against the filter.

## Forward registration

The falsifier (fires passing the filter do not outperform fires
failing it, forward, over 100+ fires) cannot bind on a population
with zero passes. Registered: every future Ghost Book fire is
serum-scored at capture (the nightly run from Mon 2026-11-16,
first-generation capture), both the literal score and the
target-to-implied ratio are recorded, and grading happens at
each fire's resolution under the harvester. The contrast cohort
accumulates from lower-IV universes and any family whose targets
are a larger fraction of implied. If 100 graded fires still
contain no passes, the invention's population claim itself is
the finding: this estate's signals all live inside the implied
noise band, and that fact gets reported at B5 as a fleet-level
verdict, not buried.
