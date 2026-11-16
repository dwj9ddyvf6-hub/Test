# DISAGREEMENT INDEX, RUN 1 (Sat 2026-11-14)

Invention 7 (INVENTION-BRAINSTORM.md), the share-side sibling of
Chorus Dispersion. Per symbol-day, every sleeve's net opening
direction from labeled entry fills; D = 1 - |L - S| / (L + S) over
sleeve counts. Graded forward on daily bars at +1 and +5 sessions.
Tool: tools/disagreement_index.py. Numbers:
runs/disagreement_index_v1.json.

## Population

269 symbol-days carried entries; 68 had two or more sleeves
opening; 25 had sleeves on both sides. Forward windows exist for
50 symbol-days (+1) and 41 (+5). The window's entries are
overwhelmingly long (6,524 buy_to_open versus 184 sell_to_open
fills), so majority-signed returns inherit the tape's beta; the
absolute-move channel is the cleaner read at this sample size.

## Headline results

1. **Disagreement predicts SMALLER moves, not bigger ones.**
   Spearman(D, |forward return|) = -0.23 at +1 session and -0.19
   at +5. Bucket means for |fwd1|: unanimous days 7.37% (n=26),
   mild disagreement 6.09% (n=15), split days 2.26% (n=9). The
   naive story (dispersed opinion = impending volatility) is
   backwards in this fleet's first measurement: when the fleet
   agrees, the name moves; when the fleet splits, the name drifts.
2. **Unanimity continues; split majorities are wrong fast, right
   slow.** Majority-signed fwd1: unanimous +1.05%, mild -1.17%,
   split -2.38%. At +5 sessions all three buckets are positive
   (+8.57%, +12.94%, +5.33%), dominated by the window's rising
   tape and the long bias; no continuation claim is made from the
   signed numbers at this n.
3. **What this is and is not.** n=9 in the split bucket at +1 is
   an anecdote with a sign, not a verdict. But the index is not
   flat: a monotone bucket pattern across both horizons on the
   absolute channel is more structure than the falsifier's "no
   forward relationship beyond chance" describes. The falsifier
   is NOT triggered; the invention is also NOT confirmed. It is
   measured, with a direction nobody in the estate predicted,
   which is what measurement is for.

## Forward registration

The index accrues nightly from the intent journal starting
Mon 2026-11-16 (research-lane writer, no desk edit), graded by
the harvester at +1/+5/+10 sessions with beta-stripped signed
returns (symbol return minus SPY same-window) once the accrual
passes 200 multi-sleeve symbol-days. Kill condition, restated
from the registration: no forward relationship on any channel
beyond chance at that sample. The inverse-volatility direction,
if it holds, makes D a position-sizing input for unanimity days
(the fleet agreeing is the high-variance state), which is the
opposite trade from the one the brainstorm imagined; the tape
decides.
