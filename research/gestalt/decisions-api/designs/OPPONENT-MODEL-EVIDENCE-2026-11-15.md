# OPPONENT MODEL EVIDENCE ANNEX (feeds the Level 9 design and Trade the Forced)

Status: EVIDENCE ANNEX, dated 2026-11-15, prepared Sat
2026-11-14 for the Sunday program. Source of record: Deep Dive
Two (ascension-research-deep-dive-two-20261114-2130/report.md)
section 6, folded in by name. This annex grades opponent-model
instruments on evidence. It builds nothing and changes no
strategy; it tells the Level 9 design which instruments it may
use, which it must refuse, and on what terms.

## 1. Forced flow (Coval and Stafford): the strongest evidence in the dive

Finding: funds with extreme outflows cut existing positions
pro-rata, creating price pressure in commonly held stocks;
investors trading against constrained funds earn highly
significant returns, and the reversal plays out over subsequent
quarters. In the lowest investor-heterogeneity quintile, long
fire-sales and short fire-purchases earned 6.95 percent
risk-adjusted over the next year. Heterogeneity is a measurable
conditioner: a diverse holder base absorbs shocks, a concentrated
one transmits them.

Implementation registered for the Level 9 design (quarterly,
from public data): compute the FIT measure per stock,
pressure = sum over funds of (flow_f x weight_{f,stock}), from
public fund flow plus lagged holdings data. Long extreme
forced-sale names AFTER the pressure quarter, sized by
heterogeneity and ADV; exit on reversal completion or after 2
quarters, whichever comes first. Slow, capacity-small, and
exactly why it can persist. This is also orphan candidate O-02
in runs/ORPHAN-SCAN-1.md; the two registrations are one trade
seen from two levels, and the conveyor must not double-count it.

## 2. VPIN: REJECTED by name

Andersen and Bondarenko (2014, 2015) showed that with accurate
trade classification VPIN behaves oppositely to its marketed
claim: bulk-volume VPIN's apparent volatility prediction is
classification error correlated with volume and volatility, and
controlling for trading intensity and realised vol it has NO
incremental predictive power. VPIN thresholds (0.5, 0.7) in
vendor and course material are marketing. Ruling for this
estate: VPIN is not an entry conditioner, not a risk gauge, and
not a dashboard metric. If it is ever computed, it enters only
as the control arm of the section 6 forward test below: it must
beat the realised-vol-plus-intensity control out of sample or
be dropped permanently.

## 3. Borrow fees: a filter and a veto, not a short book

Evidence: simultaneous rising fee and rising loan quantity
predict negative next-month returns (Cohen, Diether and Malloy
2007); fee portfolios beat 102 anomalies in the cited window.
But the 2026 marginal-fee draft shows new borrowers pay the
marginal, not average, fee: valuing shorts at the marginal fee
cuts value-weighted strategy returns by about a third and
eliminates equal-weighted returns. And JFQA 2026: holders of
high-fee names (fee at or above 25 percent, 1,200 plus episodes,
2005 to 2023) lost about 20 percent per episode on average. The
long side is where the evidence sits.
Rulings: (a) borrow fee plus utilisation is a LONG-EXCLUSION and
underweight filter: do not own high-and-rising-fee names;
(b) it is a SHORT VETO: never short into a rising fee plus a
rising loan balance; (c) direct shorts on fee signals are not
an estate strategy under this evidence.

## 4. GEX: regime variable only

What has academic backing: the SIGN regime. Net long gamma
dampens intraday volatility; net short gamma amplifies it and
predicts intraday momentum character (Ni, Pearson, Poteshman
and White; Barbon and Buraschi; Baltussen et al., all reached
via secondary sources in the dive and flagged as such). The
regime predicts path character, NOT direction. What is
untestable as marketed: precise flip, call wall and put wall
levels, because standard GEX assumes the dealer sign convention
(customers long puts, short calls); open interest origin is not
observed in the public file, so the level is a model output
conditional on an unverified assumption and can invert.
Ruling: compute GEX both ways (convention sign, and signed by
trade aggressor where a feed exists); act ONLY when both
computations agree on regime. In long-gamma regime, favour
intraday mean-reversion sizing; in short-gamma, cut
mean-reversion size and widen stops. Log the regime daily and
score it under the forward test.

## 5. OFI: execution use only

Cont, Kukanov and Stoikov 2014: order-flow imbalance explains
about 65 percent of CONTEMPORANEOUS mid-price changes over 10
second to 1 minute windows; lagged predictability is weak.
Ruling: OFI is an execution instrument (trade patiently when OFI
is with you, urgently or not at all when against) and an
adverse-selection avoidance aid. It is not a holding-period
alpha and no sleeve may cite it as one.

## 6. Falsifiable forward test (Deep Dive Two section 6, carried in substance)

Pre-register four conditioners for 6 months on existing
strategies (no new strategies): (a) the Coval and Stafford
forced-flow flag; (b) the borrow-fee exclusion filter; (c)
GEX-regime sizing, both-signs-agree only; (d) VPIN as a control
that must beat vol controls. Predictions, as registered in the
dive: (b) improves long-book excess return by reducing losers
(the effect sits in the left tail, not the mean winner); (a)
adds return only on a quarterly horizon, not weekly; (c)
predicts next-day realised vol divided by implied and the
intraday reversal rate, but NOT next-day return sign (accuracy
about 50 percent); (d) adds nothing over vol controls. Any
conditioner failing its prediction is removed. Opponent modeling
that cannot pass this test is narrative, not information.

Ascension Level 9 falsifier, carried from ASCENSION-BRAINSTORM.md
for the design this annex feeds, verbatim: "Falsifier: cards
with a named, evidence-backed opponent model do not outperform
cards without one on forward grading within a quarter."

STATUS: GREEN for the annex as scoped. EVIDENCE: Deep Dive Two
section 6 and its cited primaries as flagged there (several GEX
primaries reached via secondary summaries; re-verify from
primaries before sizing capital on them, per the dive's own
open-questions section).
