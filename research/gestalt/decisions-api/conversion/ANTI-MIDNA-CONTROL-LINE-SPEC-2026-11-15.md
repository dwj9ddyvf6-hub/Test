# THE ANTI-MIDNA CONTROL LINE: STANDING SPEC FOR THE NIGHT STUDY

Filed Sun 2026-11-15, Conversion Engine run 1, workstream CV-4a.
Source measurement: the Chaos Foundry's first casting, C-1 THE
ANTI-MIDNA (registration
~/workspace/midna-book/strategy-candidates/2026-11-15-anti-midna.md;
results foundry/c1_results.json in this program home). This spec
makes the casting's control comparison a standing element of the
night study's own output, per the foundry's Wave 7 cell 2. No em
dashes in this document.

## Why this line exists

The foundry faded the night study's stated directional
conclusions across four cohorts and won +268.80bp per position
pooled (t 4.37, n 58). It then compared that win against the
naive control, fading everything, and the win vanished: the
control made +272.13bp on the same nights, so the study's
per-name selection excess was minus 3.33bp, i.e. nothing. The
structural finding underneath: as written, the study's
directional conclusions are one-signed per night (the TARGET
cohorts ran 43 of 43 long; the STAGE cohorts' positions ran 15
of 15 short), so following them is indistinguishable from
holding the complex with a sign. A conclusion that never
discriminates carries no per-name information, and from now on
that fact is measured every night instead of suspected once.

## The standing line, defined exactly

Every night study record carries, beside its conclusions, a
CONTROL LINE block with these fields, computed under the frozen
C-1 rules (any change to these rules is a dated amendment, never
a silent edit):

1. BIAS EXTRACTION. Per Focus name, the study's stated
   directional bias for that night, extracted by the C-1 rules:
   TARGET form: the sign of (base-case target minus last close)
   from the entry's own Working close; zero difference is no
   position. STAGE form: Pass A Stage 2 is +1, Stage 4 is -1,
   Stages 1, 3 and none are no position. Posture language is
   never a position.
2. ANTI RETURN. Per positioned name, minus bias times the
   forward overnight return (close on the study's asof date to
   the next session's open, SIP split-adjusted bars, the study's
   own basis), and the same at the 5-session horizon when the
   bars exist.
3. THE CONTROL. Per night: minus the equal-weight mean
   overnight return of the full Focus complex that night. This
   is the fade-everything line: short the whole complex,
   ignoring the study entirely.
4. THE GRADE. Per night and pooled to date: the anti book's
   mean (bp, with t and hit rate), the control (bp), and the
   SELECTION EXCESS, anti minus control. The study's own side
   is minus the anti mean on positioned names by construction
   and is printed too, so the study sees its own number and
   the number it has to beat.
5. ONE-SIGNEDNESS. The night's bias split (longs, shorts,
   no-position count) is printed on the line. A night whose
   positioned conclusions are all one sign is flagged
   ONE-SIGNED on its face: on such a night the study's
   conclusions cannot, by construction, express per-name
   selection, and any card language implying they do is wrong.

## The citation rule

A book card may not cite the night study's directional
conclusions for any night whose study record lacks the control
line. If the line is missing, the study that night is context,
not evidence, and the card must say so or not cite it. This
rule binds from the first study night after this spec files:
Mon 2026-11-16.

## First standing grade (computed 2026-11-15 from the existing record)

The four cohorts the foundry graded are the standing grade's
opening balance, recomputed from foundry/c1_results.json and
verified against the foundry report's table:

| Cohort | Positions | Bias split | Anti bp | Control bp | Excess bp |
|---|---|---|---|---|---|
| TARGET 2026-11-11 | 21 | 21 long / 0 short | +522.58 (t 5.08) | +546.17 | -23.59 |
| TARGET 2026-11-12 | 22 | 22 long / 0 short | +82.13 (t 3.09) | +61.92 | +20.21 |
| STAGE 2026-11-09 | 7 | 0 long / 7 short | -379.20 (t -5.35) | -275.22 | -103.98 |
| STAGE 2026-11-10 | 8 | 0 long / 8 short | +682.93 (t 4.82) | +609.81 | +73.12 |
| Pooled | 58 | 43 long / 15 short | +268.80 (t 4.37, hit 0.724) | +272.13 | -3.33 |

Net of the 5bp charge the pooled anti read is +263.80bp; the
excess is unchanged by the charge (both books trade the same
nights). All four nights are flagged ONE-SIGNED under the rule
above. The four nights were extreme (complex overnight means
-546, -62, +275, -610bp), which bounds the grade's reach: it
convicts the written form's structure, not yet the study's
per-name skill, which has never been measurable while the
conclusions were one-signed.

STANDING GRADE #1, printed plainly: selection excess -3.33bp
over 58 positions. The study's directional conclusions, as
written, have so far carried no per-name information beyond
the complex's own sign.

## Forward reads already dated

- The forward cohort frozen in c1_results.json (the gestalt
  ledger as of the 2026-11-13 close: 29 names, 28 short bias,
  CEG alone long, mean upside_first 0.233) reads overnight on
  Mon 2026-11-16 and at 5 sessions on Fri 2026-11-20. This
  cohort is the first one graded under this spec's standing
  line from birth.
- The TARGET cohorts' 5-session reads land Wed 2026-11-18 and
  Thu 2026-11-19.
- From Mon 2026-11-16 the line accrues nightly with the study
  itself (wired into the midna-book-night-study job the night
  this spec filed; the wiring is verified by reading the job
  body back).

## What would change the verdict

The line is a measurement, not a punishment. If the study's
conclusions begin discriminating (two-sided nights with a
positive pooled selection excess over a quarter of graded
nights), the standing grade prints that too, and the Anti-Midna
registration's own falsifier terms govern the casting's fate.
If the excess stays at or below zero while the conclusions
stay one-signed, the correct conclusion is the one the foundry
printed: the study is a posture instrument, and the book's
cards should cite it as posture, never as selection.
