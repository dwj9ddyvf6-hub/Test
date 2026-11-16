# W5-7a MK-02 DESIGN PLUS HONEST IN-SAMPLE READ

Dated 2026-11-14. Wave 5 Lane D. The design half is
pre-registered before its first forward session exists. The
in-sample half reports only what the held artifacts support, at
the sample sizes they actually carry, and labels itself
anecdote-grade. No claim beyond what n supports is made
anywhere in this document.

## 1. The question

Does final-minutes tape imbalance condition the overnight leg?
Concretely: on nights when a name's closing tape leans heavily
buy-side (or sell-side), is that name's overnight return, close
to next open, different from its unconditional overnight
return, and can a cross-sectional sort on the imbalance earn
anything after the overnight family's own friction convention?

Context that motivates and bounds the question: the overnight
family (Wave 4 V2) PROMOTED as one family at a combined trial
count of 45, and the tape-imbalance conditioned variant was
deliberately left out of that exam matrix because the proxy's
computed history was one day on the Focus names plus a
20-session SPY and QQQ probe. MK-02 is that excluded variant,
given a forward design instead of an exam it cannot yet sit.

## 2. The proxy, exactly as built

TAPE-IMBALANCE-PROXY-v1 (keepgoing2/k3_probe.py, extended by
keepgoing2/wave4/v7_mk01_probe.py). For one symbol and one
session: SIP prints from 15:50 to 16:00 ET, fully paginated;
each print is sided by the tick rule with direction carried
across the whole window (the Wave 4 extension; the K3 original
restarted tick state inside the 2-minute leg); imbalance =
(buy volume minus sell volume) / (buy volume plus sell volume),
computed for the final 10 minutes (primary) and the final 2
minutes (secondary). It is labeled PROXY in every artifact:
official closing-auction imbalance is a proprietary exchange
product (NYSE OpenBook, Nasdaq NOII) that no estate route
serves, as recorded in keepgoing2/K2-K5-RECORDS.md. Nothing in
this design calls the proxy an auction imbalance.

## 3. Forward design

- Computation: daily, beside CLOSE-IMB-01, whose shadow already
  consumes this proxy under its label from Mon 2026-11-16. The
  proxy is computed for the 29 Focus names (the V2 family
  basket: SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU,
  SNDK, WDC, AAOI, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR,
  RKLB, FLNC, EOSE, FCEL, BE, OKLO, VST, CEG, XLE) and for SPY
  and QQQ as controls, which are computed but never enter the
  cross-section.
- Name validity, per session: a name enters that session's
  cross-section only if its 15:50 to 16:00 window holds at
  least 100 prints. Below that, its imbalance is a handful of
  prints wearing a ratio's clothing; the name is excluded that
  session and named in the accrual record. A session's
  cross-section is valid only with at least 24 valid names.
- Buckets: within each valid session, names are sorted by
  final-10m imbalance and split into terciles. The primary
  conditioned series, MK02-XS, holds that night, equal weight:
  long the top tercile's overnight legs, short the bottom
  tercile's overnight legs, entry at the session close, exit at
  the next session open, equity auction form (the only form the
  Wave 4 V1 friction study found tradeable for the overnight
  leg). Gross and net are both recorded; net subtracts the
  overnight family's registered 5 basis points, the same
  convention as the ON_focus29 falsifier.
- Secondary series, registered as trials and never the headline:
  MK02-GATE, the ON_focus29 basket held overnight only on
  sessions whose basket mean final-10m imbalance is positive,
  cash otherwise; and the final-2m versions of both series.
- What is recorded daily: per name, prints in window, final-10m
  and final-2m imbalance, tercile assignment, that night's
  overnight return once the next open prints, and the two
  series' daily returns, gross and net. A missing next open
  leaves the row open, never filled from a later print.

## 4. The exam and the count it will face

MK-02 grades as a member of the ON family, because that is the
family it conditions, and it inherits the family's accounting:
the Wave 4 family exam ran at a combined trial count of 45.
MK-02's considered variants are: bucket split (tercile,
quintile, median) 3, times window (final-10m, final-2m) 2,
times form (cross-sectional long-short, day-gated basket) 2,
equals 12 new trials. At its grade the family trial count is
45 + 12 = 57, and tools/admission_exam.py exam() is called on
MK-02's forward-only matrix (the 12 variant series over its
accrued sessions) with trial_count = 57, benchmarks SPY and
QQQ, is_new_family = True for its own verdict, which is the
conservative reading: the family is established, this member
is new, and the absolute t above 3 hurdle applies to it.
Promotion bars are the exam's own: DSR at least 0.95, CPCV PBO
below 0.2, SPA p below 0.05 against both benchmarks.

First lawful grade: 120 accrued valid sessions. Reasoning: the
overnight horizon resolves one session after each formation,
so at 120 sessions the first 119 conditioned nights are fully
resolved; and 120 daily observations is the smallest sample
this lane will put in front of the exam's CPCV and SPA legs
for a conditioned subseries whose per-night name count is a
third of the basket on each side. Counting weekdays from Mon
2026-11-16, the 120th session falls on Fri 2027-04-30, holidays
aside; the session count governs. Integrity reads at 20 and 60
sessions check accrual mechanics only (valid sessions, names
per session, no silent gaps) and grade nothing, mirroring the
ON shadow's discipline of grading nothing before its own
registered reads. MK-02's falsifier is its exam row at that
grade: failure on any promotion bar demotes MK-02 alone. It
does not reopen ON_focus29, whose own 60-session forward
falsifier governs it, and ON_focus29's result, in either
direction, does not grade MK-02.

## 5. In-sample read (i): SPY and QQQ, 20 sessions, anecdote-grade

Source: keepgoing2/wave4/v7_mk01_probe.json, sessions
2026-10-19 to 2026-11-13, 1,166,344 SPY prints and 870,383 QQQ
prints. Overnight legs resolve for 19 of 20 sessions per symbol
(the 2026-11-13 leg resolves Mon 2026-11-16 and is null in the
artifact). Correlations below are the artifact's own grades,
plus a pooled line computed by this lane from the artifact's
rows tonight.

| series | n | Pearson r vs next overnight return |
|---|---|---|
| SPY final-10m imbalance | 19 | minus 0.053 |
| SPY final-2m imbalance | 19 | minus 0.099 |
| QQQ final-10m imbalance | 19 | minus 0.033 |
| QQQ final-2m imbalance | 19 | minus 0.079 |
| Pooled, both symbols, final-10m | 38 | minus 0.037 (t minus 0.22) |
| Pooled, both symbols, final-2m | 38 | minus 0.080 (t minus 0.48) |

Sign-bucket means, pooled, computed from the same rows: nights
with positive final-10m imbalance averaged an overnight return
of plus 0.063 percent (18 symbol-nights) against minus 0.109
percent on negative-imbalance nights (20 symbol-nights); for
final-2m, plus 0.090 percent (18) against minus 0.134 percent
(20). The pooled rows share 19 calendar days across two index
symbols and are not 38 independent observations.

For contrast, the same proxy against the closing move inside
its own measurement window: SPY final-10m r 0.448 (sign
agreement 14 of 20), QQQ r 0.295 (14 of 20). The proxy co-moves
with the move it is measured inside and shows no visible
relation to the overnight leg at this size.

Label, stated plainly: anecdote-grade. n of 19 per symbol
cannot distinguish a small real effect from zero, the pooled
line double-counts calendar days, and no exam was run or is
implied. The honest summary is: at the only size in hand, the
overnight relation reads as nothing, and the forward design of
section 3 exists because nothing at n 19 settles the question
in either direction.

## 6. In-sample read (ii): the single-day basket cross-section, NOT COMPUTABLE from the held artifacts

The task for this lane asked for the 2026-11-13 cross-section,
29 names, imbalance versus that night's overnight legs, labeled
n 1 day. It cannot be computed from the held artifacts, and the
gap is named exactly instead of crawling tonight:

- keepgoing2/k3_tape_imbalance_proxy.json, the K3 proxy artifact
  for 2026-11-13, carries per-symbol values for SPY and QQQ
  only (SIP and IEX legs for each). It carries no Focus-name
  values at all, so no 29-name cross-section exists in the
  artifact to read. The two control values on file for that
  day, SIP final-10m: SPY plus 0.2585, QQQ plus 0.0279, are two
  index points, not a basket cross-section, and this lane does
  not present them as one.
- The overnight leg for 2026-11-13 had not printed when the
  artifacts were written: the Wave 4 probe records next_open
  and overnight as null for 2026-11-13 on both symbols, because
  the next open is Mon 2026-11-16. So even the two control
  points have no overnight leg in the held record.

What would cure it, named for the record: a per-name proxy
computation over the Focus names for 2026-11-13 (the K3 route
exists; it was run for two symbols), joined to the
2026-11-16 opens. That is a new crawl, out of tonight's scope
by the task's own instruction, and the forward accrual of
section 3 supersedes it from Mon 2026-11-16 in any case: one
in-sample day, even computed, would be an anecdote with 29
correlated points sharing a single night, and it would change
no decision the forward design makes.

## 7. Rails held in this document

The proxy is called a proxy throughout. No admission claim is
made for MK-02. The in-sample reads are labeled at their true
sizes, the uncomputable read is named uncomputable with its
exact missing fields, and the only path to a verdict is the
forward accrual and exam registered above.

Written 2026-11-14, Wave 5 Lane D.
