# Research — how best-in-class products present ONE trade idea

Commissioned by the owner's 2026-10-16 19:51 ET indictment of the Setups product
("Do deep internet research. Figure it out."). Each pattern below is named,
sourced, and mapped to the design decision it forced in the redesign.
Prior in-house research this builds on:
research_notes/trade-plan-distillation-patterns-20261016-1344/report.md
(action-verb plans, WAIT as a first-class state, three numbers, two
meta-fields: time bound + conviction).

## P1 — The institutional idea ticket (alpha capture)

Source: Institutional Investor, "Six Ways Trade Ideas Are Changing
Investor Strategies" (institutionalinvestor.com). Professional trade-idea
systems (alpha capture) require the author to file a FIXED parameter set
per idea: direction (long or short — research-style "holds" are explicitly
excluded), style, **conviction**, **time horizon**, amount, **target
price**, price method, and **stop loss**. Ideas are price- and
time-stamped, and authors CLOSE ideas when they have played out, which is
what builds the author's track record.

Design decision: a setup's call is a fixed-grammar object, not prose
that happens to the author that day: direction + expectation + objective
+ horizon + conviction word + the line that ends it. A name that cannot
fill the ticket does not get a card (the "no holds" rule → our unclear
bucket). The desk already time-stamps briefs and logs departures;
Phase D wires the call to the same close-out discipline (the call is
re-stated or closed each pass, never left stale).

## P2 — Signal-card anatomy and reading order

Source: signal-service practice, e.g. Best Trading Signal, "How to Use
Forex Signals" (besttradingsignal.com): a trade idea has four parts —
instrument and side, entry, stop-loss ("exit if wrong"), take-profit —
presented in that order, with reward:risk computed from the live price;
if price has moved so reward < risk, the idea is skipped, not chased.
Practitioner cards on TradingView use the same skeleton: a one-word
Bias line first, then Entry zone / Stop (with its reason attached, e.g.
"below key support") / TP1 / TP2 / R to each.

Design decision: the card's reading order is fixed — CALL (bias +
expectation) → plan strip (zone · stop · objective · R) → why → what
ends it. The stop carries its reason in apposition, as practitioner
cards do. R is always printed next to the objective it belongs to.

## P3 — Calibrated words: likelihood is not confidence

Source: the words-of-estimative-probability tradition (Sherman Kent;
US National Intelligence Estimate practice, via Wikipedia "Words of
estimative probability" and Language Log's NIE explainer): professional
estimative writing separates TWO judgments that amateurs merge —
(a) the assessed likelihood of the outcome (a fixed word ladder:
remote < very unlikely < unlikely < even chance < likely < very likely
< almost certainly; IPCC anchors: likely >66%, very likely >90%,
about as likely as not 33–66%), and (b) confidence in the judgment,
which is a statement about the evidence (its quality, corroboration,
fragmentation). "Might/may" is reserved for "we cannot assess" — it is
never a conclusion. Tetlock's superforecasting research (via the US
Army Research Institute summary of Tetlock & Gardner): forecasters who
live at "maybe" are the LEAST accurate; good forecasters use base rates
(the outside view), commit to granular estimates, update on a cadence,
and audit their own record.

Design decision: conviction on the card is a WORD from a fixed ladder
(High conviction / Conviction / Lean / No call), and the word is always
printed WITH its evidence basis (families agreeing, decisive voices for
and against, the strategy families' record as the base rate) — the word
summarizes the basis; it never replaces it. Opposition evidence
DISCOUNTS the word deterministically instead of vetoing the call into
"mixed". "No call" is a routing decision (one-line bucket), never a
card's conclusion. The family record on the card is the Tetlock base
rate, labeled as history.

## P4 — Progressive disclosure: one surface, one expansion

Source: Nielsen Norman Group, "Progressive Disclosure" (nngroup.com,
summarized in multiple secondary digests): initially show only the few
most important options; offer the specialized set on request. NN/g names
the two ways to fail: (1) the wrong primary/secondary split — hiding
what most users need up front; (2) unclear navigation to the deeper
level. Working-memory limits (chunking, ~4 items) set the budget for
the primary surface; mobile tolerates ~2 disclosure levels.

Design decision: the card carries exactly the 80% case — the call, the
three numbers + R, the why, the invalidation, the plan chart — and ONE
expansion ("The full read") holds everything else, descriptively
labeled. Nothing a first reader needs hides behind the expansion;
nothing else competes on the card. This is also the owner's distillation
law stated in UX vocabulary (forefront + one layer down).

## P5 — Chart minimalism: the plan is the chart's only subject

Source: Tufte's data-ink principle (via NN/g, "Clutter-Free: One of the
3 Cs for Better Charts", nngroup.com, and the EU data-visualisation
guide): ink that is not the message is chartjunk; the data rectangle
should be filled by the data that matters — axes encompass the range
where the decision lives, not the range that happens to exist; direct
labels at the lines beat legends. The empirical counterweight (Bateman
et al., "Useful Junk", CHI 2010): embellishment does not hurt reading
accuracy and aids recall — which licenses bold, legible annotation of
the message itself; Kosara's "harmful junk" line governs: ink that
INTERFERES with the reading (competing systems, wrong zoom) goes.

Design decision: the hero chart is a PLAN chart — windowed to the
decision range (zone → objective), plan lines as the dominant ink,
direct price labels at each line, one governing invalidation, at most
one structural context element (the pattern the call cites). The full
annotated chart-read exhibit (averages, Fib, clusters, RSI/MACD
panels) survives unchanged — inside the expansion, where it is depth,
not competition.

## What the research changed (not decoration)

1. Without P1, the rebuild would have produced prettier prose. P1 made
   the call a TICKET: fixed fields, no-holds rule, close-out discipline.
2. Without P3, "conviction" would have stayed a score with a caveat
   sentence. P3 split it into likelihood-word + evidence-basis, and
   gave opposition a deterministic discounting role instead of a veto.
3. Without P5, the chart fix would have been "fewer lines". P5 made it
   a different chart: windowed to the decision, the full read demoted
   to the expansion intact.
4. P4's failure-mode list became the acceptance test for the page:
   right split (the four questions + call on the card) and one
   obviously-labeled door to depth.
