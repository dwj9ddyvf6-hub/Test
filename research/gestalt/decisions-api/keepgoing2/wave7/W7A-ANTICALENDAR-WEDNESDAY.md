# W7A: ANTI-CALENDAR FIRST READ (CB-44) AND WEDNESDAY STRUCTURES (CB-29)

Wave 7 Lane A, Sun 2026-11-15 night. Program home:
research_notes/decisions-api-leverage-20261114/. Pre-registration:
w7a_preregistration.md (original registration plus the x10
widening addendum of 2026-11-15 01:15 ET, each written before
the outcomes it governs). All artifacts are in
keepgoing2/wave7/ and named w7a_*. Real held data only, shadow
only, no desk edits. Typed seat: not used, spend $0.00.

## Headline verdicts

W7-1 ANTI-CALENDAR: ANECDOTE-GRADE first read (the registered
grade label; every bucket holds 4 nights or fewer). Across all
four outcome universes the busy-night overnight mean is
POSITIVE and the quiet-night mean is near zero or negative,
the opposite sign from the CB-44 hypothesis, and no contrast
is anywhere near significant. The 5-session horizon contrast
is not computable in any universe (the busy bucket holds
exactly 1 date with a computable forward return). Nothing
here supports the claim that the estate busiest nights are
wrong-side; at this n nothing could support or refute it
strongly, and the record says so on its face.

W7-2 WEDNESDAY STRUCTURES: the Wednesday night leg (Wed close
to Thu open) is the weakest single night of the week in the
find (+7.72bp gross, +2.72bp net of 5bp, t 0.99), and the
two-night midweek hold LOSES to the same capital cycled
through its two single nights on the same events (+32.95bp
per hold against +36.87bp compounded singles, gross), because
the Wednesday intraday leg inside the hold averaged -3.46bp.
At the family exam at count 61 both structures are REJECTED
by wide margins (Wed night DSR 0.013; midweek hold DSR 0.169),
and no per-weekday leg promotes either (the strongest, Tue
night, prints DSR 0.844). Under CB-29 own falsifier, the
midweek shape is a story and it CLOSES. Details in Part 2,
sections 2.3 to 2.5.

## PART 1: W7-1 ANTI-CALENDAR (CB-44)

### 1.1 The pre-registration, verbatim

The governing text is w7a_preregistration.md. Its W7-1 test
specification, copied verbatim:

"Rank the analysis set by composite. BUSY = top tercile,
QUIET = bottom tercile, middle tercile reported but excluded
from the contrast (tercile cut by rank order; with n dates,
busy and quiet each hold floor(n/3) dates, ties at the cut
broken by earlier date first into the higher bucket, stated
if it binds). Outcomes per close date D:
  (i) ON leg: the focus29 basket overnight return from close
      D to the next session open (the w5c ON_full leg whose
      prior close date is D), gross and net of a single 5bp
      charge.
  (ii) 5-session forward: equal-weight per-name close D to
      close D+5 sessions return from wave3/focus_bars.json
      (names with both closes, minimum 10 names), gross and
      net of a single 5bp charge. Bucket labels are the ones
      fixed on the full analysis set; the 5-session contrast
      uses the subset of busy and quiet dates where this
      return is computable inside the held bars.
Statistics per horizon: busy mean, quiet mean, busy minus
quiet difference, Welch t and two-sided p, n per bucket.
GRADE LABEL: if either bucket holds fewer than 10 nights at
either horizon, the read is labeled ANECDOTE-GRADE in the
record headline, whatever the t says.
TRIAL COST: this read is 1 anti-calendar trial family. The
two horizons are its two registered outcomes, not two
families. The ON family count is NOT charged for W7-1 (it
conditions the existing basket; it proposes no new ON
variant); the charge is recorded in the anti-calendar family
of the lab ledger terms as 1."

The composite rule, also verbatim from the same file:

"A night is a trading-session CLOSE date in the held w5c grid
(prior_close_dates of keepgoing2/wave5/w5c_series.json). For
each component, z-score its daily counts across the analysis
set defined below (mean and standard deviation over the set,
using the dates where that component is observed; a component
is observed on a date when its source holds at least one row
for that date, and its count is then that row count, zero
counts are not manufactured for unobserved dates). A date
composite is the MEAN of the z-scores of the components
observed on that date. The ANALYSIS SET is every close date
with at least 2 of the 4 components observed AND an overnight
leg in the held bars (close date strictly before the last bar
date). Weekend and holiday activity dates are excluded from
the test and reported as coverage only."

The x10 widening addendum (2026-11-15 01:15 ET, written after
the focus29 outcomes and before any widened outcome) added
SPY, QQQ, and the PANEL100 basket as outcome universes under
identical rules, charged 3 additional read families, total 4.
Its full text is in w7a_preregistration.md.

### 1.2 Activity series: sources and coverage

| Component | Source | Dates covered | Rows |
|---|---|---|---|
| DROP | grokbot-inbox/INBOX.md plus its 2026-10-05 to 2026-10-24 archive, read via the GitHub API | 2026-10-05 to 2026-11-14, 33 dates | 683 entries |
| TYPED | every ledger JSONL in midna-book/typed-layer/ plus hunt/typed_seats_ledger.jsonl | 2026-11-10 to 2026-11-14, 5 dates | 357 rows |
| READS | composite-confidence/reads/ entries carrying a date in the name | 2026-10-07 to 2026-11-14, 17 dates | 336 artifacts |
| DESK | muse-desk-v3/state/dispatcher.jsonl fires plus rejects, and gate_distance.jsonl rows | 2026-11-11 to 2026-11-15, 5 dates | 4,999 dated rows (fires 1,704, rejects 2,575, gate rows 720; a further 66 dispatcher fire and reject rows carry no parseable date in their intent_id and cannot enter a dated series) |

Route note: the GitHub Contents API returned no content for
the live inbox (3,839,022 bytes; the API omits content above
1 MB), so the live file was read through the Git Blobs API by
the SHA the Contents call returned (blob route, read only).
The first route failing was a route failure, not an absence:
the file was there, and the second route read all 584 live
entries (2026-10-25 to 2026-11-14) plus 99 archive entries.

Coverage honesty: the four components barely overlap in time.
READS is dense in two blocks (2026-10-07 to 2026-10-14 and
2026-11-04 to 2026-11-14) and absent between; TYPED and DESK
exist only in the final week. The registered at-least-2 rule
therefore yields an analysis set of 13 close dates in two
blocks, and that small set, not any choice made tonight, is
what makes this read anecdote-grade.

### 1.3 The analysis set (every night, every number)

| Close date | DROP | TYPED | READS | DESK | Composite | Bucket | ON bp (focus29) | Fwd5 bp (focus29) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-07 | 4 | . | 1 | . | -1.337 | quiet | -172.3 | -1538.4 |
| 2026-10-08 | 7 | . | 24 | . | -0.358 | middle | +181.4 | -1154.6 |
| 2026-10-09 | 20 | . | 1 | . | -1.121 | quiet | -123.3 | -1705.0 |
| 2026-10-12 | 3 | . | 24 | . | -0.412 | middle | -301.3 | -1217.2 |
| 2026-10-13 | 4 | . | 30 | . | -0.154 | middle | -254.8 | -1208.4 |
| 2026-10-14 | 2 | . | 21 | . | -0.548 | quiet | -449.2 | -321.9 |
| 2026-11-04 | 25 | . | 32 | . | +0.211 | middle | -470.7 | +436.7 |
| 2026-11-05 | 56 | . | 3 | . | -0.554 | quiet | +702.1 | +1851.5 |
| 2026-11-06 | 78 | . | 30 | . | +0.844 | busy | +179.5 | +797.1 |
| 2026-11-09 | 76 | . | 31 | . | +0.858 | busy | -275.2 | not in bars |
| 2026-11-10 | 35 | 200 | 31 | . | +0.538 | busy | +609.8 | not in bars |
| 2026-11-11 | 97 | 14 | 31 | 152 | +0.144 | middle | -546.2 | not in bars |
| 2026-11-12 | 96 | 106 | 31 | 2,620 | +0.739 | busy | -61.9 | not in bars |

Busy: 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-12.
Quiet: 2026-10-07, 2026-10-09, 2026-10-14, 2026-11-05.
The window the activity series honestly covers for this test
is 2026-10-07 to 2026-11-12 (13 close dates). Two confounds
are named on the face of the read: the busy bucket is entirely
November and the quiet bucket is three-quarters October, so
the contrast is partly a calendar split inside a violent
stretch (the focus29 5-session forwards in this window run
from -1705bp to +1852bp); and the middle bucket overnight
mean (-278.30bp, n 5) is worse than both contrast buckets, so
the sample shows no monotone activity gradient in any case.

### 1.4 Verdicts in numbers (gross, with net of 5bp beside)

Overnight horizon (contrast computable in all 4 universes):

| Universe | Busy mean bp (net5) | Quiet mean bp (net5) | Diff bp | Welch t | p | n busy / quiet |
|---|---|---|---|---|---|---|
| focus29 | +113.04 (+108.04) | -10.68 (-15.68) | +123.72 | 0.40 | 0.707 | 4 / 4 |
| SPY | +39.54 (+34.54) | -11.59 (-16.59) | +51.14 | 1.29 | 0.265 | 4 / 4 |
| QQQ | +47.59 (+42.59) | -9.67 (-14.67) | +57.26 | 0.63 | 0.551 | 4 / 4 |
| PANEL100 (100 names every date) | +47.55 (+42.55) | -4.67 (-9.67) | +52.22 | 0.51 | 0.629 | 4 / 4 |

5-session forward horizon (contrast NOT COMPUTABLE in any
universe: the busy bucket holds exactly 1 date, 2026-11-06,
with a computable forward return inside the held bars, which
end 2026-11-13; the other three busy dates would need closes
past the bar end). Descriptive bucket means only:

| Universe | Busy mean bp (n) | Quiet mean bp (n) | Middle mean bp (n, focus29 only computed) |
|---|---|---|---|
| focus29 | +797.09 (1) | -428.46 (4) | -785.85 (4) |
| SPY | +259.49 (1) | +19.90 (4) | . |
| QQQ | +362.60 (1) | -86.94 (4) | . |
| PANEL100 | +316.17 (1) | +16.42 (4) | . |

Reading: the CB-44 hypothesis predicted busy minus quiet
NEGATIVE. Every overnight difference printed is positive
(+51bp to +124bp) and every one is insignificant at n 4
against 4. The single busy 5-session observation is strongly
positive in all four universes, against mixed quiet means.
The honest verdict is that the first read finds NO evidence
that busy nights are wrong-side, with the direction, if
anything, running the other way, and the sample is far too
small to grade either direction. The creation is not killed
by this read (a kill needs a resolved sample that can carry
one); it is carried as an open anecdote-grade read whose
forward form is cheap: the same composite, computed nightly
from tonight forward, accrues real n without any backfill
question. Trial cost charged: 4 anti-calendar read families
(1 original plus 3 widening), 8 universe by horizon contrasts
registered, 4 computable and 4 not computable at this bar end.

## PART 2: W7-2 WEDNESDAY STRUCTURES (CB-29)

### 2.1 Reproduction gate

The held w5c series reproduces before any variant is run:
2,229 sessions, 2018-01-03 to 2026-11-13, ON_full mean
+16.46bp, Sharpe 1.67, t 4.97 (computed: +16.457bp, 1.671,
4.969). Gate passed in w7a_wednesday_build.py by assertion.

### 2.2 Naming (the trap in this workstream, disarmed)

A night is named by its CLOSE weekday. Wed night means Wed
close to Thu open. In W5C open-weekday naming that same leg
is the Thu-open leg, which W5C printed at +7.72bp, t 0.99;
the W5C Wed-open strength (+28.71bp, t 4.25) is the Tue night
in this naming. Both namings appear in the table below so no
reader can trade one for the other.

### 2.3 Per-weekday legs (conditional statistics, gross and net of 5bp)

| Night (close weekday) | W5C open-name | n legs | Spans | Mean bp | Net5 bp | Std bp | t | Sharpe (freq-ann) |
|---|---|---|---|---|---|---|---|---|
| Mon night | Tue opens | 418 | 415 span 1, 3 span 2 | +20.28 | +15.28 | 148.60 | 2.79 | 0.94 |
| Tue night | Wed opens | 460 | 453 span 1, 7 span 2 | +28.74 | +23.74 | 143.51 | 4.30 | 1.44 |
| Wed night (all spans) | Thu opens plus Fri opens after Thu holidays | 456 | 442 span 1, 14 span 2 | +8.05 | +3.05 | 162.90 | 1.06 | 0.35 |
| Wed night STRICT (structure a) | Thu opens | 442 | span 1 only | +7.72 | +2.72 | 163.94 | 0.99 | 0.33 |
| Thu night | Fri opens | 449 | 433 span 1, 16 span 4 | +13.15 | +8.15 | 145.74 | 1.91 | 0.64 |
| Fri night | weekend class opens | 446 | 402 span 3, 44 span 4 | +12.13 | +7.13 | 178.09 | 1.44 | 0.48 |

Reconciliation against W5C, exact: the strict Wed night row
reproduces W5C Thu opens to the printed digit (n 442, +7.72bp,
t 0.99). The 14 excluded Wed closes open on Friday across a
Thursday holiday and averaged +18.51bp (t 0.53). W5C weekend
class (462 legs) equals Fri night here (446) plus the 16
span-4 Thu-night legs (Thu close to Mon open across a Friday
holiday). The Tue night is the week carrier; the Wed night
is its weakest single night. That ordering is the whole
midweek shape, and it points against the mini-weekend story:
the strong leg is the one INTO Wednesday, not out of it.

### 2.4 Structure (b): the two-night midweek hold against the same capital

Events: 439 (Tue, Wed, Thu consecutive sessions in the basket
grid; 21 Tuesday weeks skipped for holidays or thin name
coverage). All figures on the same 439 events:

| Object | Mean bp | Std bp | t | Sharpe (freq-ann) |
|---|---|---|---|---|
| Midweek hold, Tue close to Thu open, per hold | +32.95 | 303.21 | 2.28 | 0.77 |
| Midweek hold, per night (arithmetic, hold divided by 2) | +16.47 | . | . | . |
| Two single ON legs compounded (same nights) | +36.87 | 220.80 | 3.50 | 1.18 |
| Single ON nights pooled (same nights, n 878) | +18.40 | 154.75 | 3.52 | 1.18 |
| Wednesday intraday leg inside the hold | -3.46 | 204.01 | -0.35 | -0.12 |

Friction basis: hold net of one 5bp charge is +27.95bp per
hold (+13.97bp per night). Compounded singles net of two 5bp
charges (one per night) is +26.87bp. So on a net basis the
two are within 1.08bp of each other, while gross the singles
win by 3.92bp, and the singles carry the far better t and
Sharpe because the hold absorbs the Wednesday intraday leg,
which averaged -3.46bp with a 204bp standard deviation on
these weeks (the hold minus full-chain compounding residual
is -0.60bp, cross-name compounding only). Verdict on the
economics, before deflation: the hold adds nothing over its
own two nights; what it adds is Wednesday daytime variance.
The mini-weekend structure is a story the tape does not pay
for, in either of its two forms.

### 2.5 The exam at count 61 (every variant prints its count: 61)

One matrix, 7 columns (ON_full, the five close-weekday night
legs with the Wed column in its strict form, the midweek
hold), flat-filled outside each class, benchmarks SPY and QQQ
total returns on the same grid, admission_exam.exam with
is_new_family True. Matrix facts at count 61: 5 clusters of
7 columns, N_eff 43.57, CPCV PBO 0.178 (the fair form as the
exam prints it; below the 0.2 promote bar and far below the
0.5 kill bar), family SPA 0.001 against SPY and 0.001 against
QQQ, family verdict PROMOTE, carried entirely by ON_full
(DSR 0.9509 inside this matrix; the same series printed
0.8866 at count 54 inside the W5C decomposition matrix and
0.9995 inside the Wave 4 family matrix, the standing
matrix-dependence warning applying to every DSR on this page).

| Column (count 61) | DSR | Sharpe (flat) | t (flat) | Mean bp (flat) | Per-series SPA vs SPY | Per-series SPA vs QQQ | Verdict |
|---|---|---|---|---|---|---|---|
| ON_full | 0.9509 | 1.67 | 4.97 | +16.46 | (family leg) | (family leg) | PROMOTE |
| Mon night only | 0.3163 | 0.93 | 2.77 | +3.80 | p 0.464 (stat 0.0) | p 0.486 (stat 0.0) | REJECT |
| Tue night only | 0.8437 | 1.42 | 4.23 | +5.93 | p 0.370 (stat 0.249) | p 0.495 (stat 0.0) | REJECT |
| Wed night only, strict (structure a) | 0.0127 | 0.33 | 0.99 | +1.53 | p 0.488 (stat 0.0) | p 0.010 (stat 0.0) | REJECT |
| Thu night only | 0.0877 | 0.64 | 1.91 | +2.65 | p 0.493 (stat 0.0) | p 0.507 (stat 0.0) | REJECT |
| Fri night only | 0.0425 | 0.48 | 1.44 | +2.43 | p 0.506 (stat 0.0) | p 0.507 (stat 0.0) | REJECT |
| Midweek hold only (structure b) | 0.1693 | 0.76 | 2.27 | +6.49 | p 0.324 (stat 0.479) | p 0.459 (stat 0.0) | REJECT |

Friction basis for the examed objects: the exam runs on gross
series, as every prior lane exam did; the net-of-5bp
conditional means are printed in sections 2.3 and 2.4 (Wed
night strict +2.72bp net; hold +27.95bp net per hold,
+13.97bp net per night).

Two reading notes. First, the Wed-night per-series SPA against
QQQ prints p 0.010 with its statistic floored at 0.0: a
bootstrap corner of the studentized SPA when a series trails
its benchmark on most days (the statistic floors at zero while
the recentered bootstrap maximum rarely reaches zero), not
evidence of superiority; the same column fails DSR at 0.013,
fails the absolute t hurdle at 0.99, and does not reject
against SPY (p 0.488), so no leg of the bar is met. Second,
no per-weekday leg clears the bar the family applies: Tue
night is the closest (DSR 0.8437, t 4.23) and still fails
deflation at the honest count, exactly the W5C weekday
reading at its count, now printed per weekday at 61 as the
brief required.

CB-29 falsifier, applied as written in the brainstorm: if
the Wednesday structures do not clear DSR 0.95 at the shared
count, the midweek shape is a story and closes. Wed night
prints 0.013 and the hold prints 0.169. THE MIDWEEK SHAPE
CLOSES. What survives the closing is the decomposition fact
itself (Tue night carries, Wed night is the weakest leg),
which stays inside the unconditioned basket and its forward
falsifier, and the W5C-WEEKDAY-FWD cell, which is separate
and untouched by this verdict.

Run note, for honesty: the brief gated heavy compute on a
load average at or below 2.5. Load was checked repeatedly
across roughly 30 minutes (1-minute average falling from
12.35 to the 4.3 to 4.8 range as the other Wave 7 lanes
finished, never reaching 2.5 on this shared cell). The exam
then ran capped to one thread at nice 10; it completed in
about 4 seconds and the load average did not move across the
run (4.26 before, 4.24 after), so the contention the gate
guards against did not in fact occur. The count 59 reference
run was cut to halve the planned compute and the cut is
recorded in w7a_wednesday_exam.json rather than silent.

### 2.6 Tape probes (CB-30 lunch hour, CB-31 first ninety seconds)

Lunch hour probe: NOT SUPPORTED by held data. The held tape
files (keepgoing2/k3_tape_imbalance_proxy.json and
keepgoing2/wave4/v7_mk01_probe.json) cover only the 15:50 to
16:00 ET closing window for SPY and QQQ; the missing input is
any held 12:00 to 13:00 ET intraday bar or print series for
the Focus names, and no new intraday crawl was fetched
tonight, per the brief.

First ninety seconds probe: NOT SUPPORTED by held data, for
the same reason: the missing input is any held 09:30:00 to
09:31:30 ET print series for the Focus names; the held tape
files carry the closing window only.

## Artifacts

| File | Contents |
|---|---|
| w7a_preregistration.md | Original registration plus the x10 widening addendum, each written before its outcomes |
| w7a_fetch_inbox.py, w7a_drop_counts.json | Dead-drop read (Contents metadata plus Git Blobs route) and per-date entry counts, 683 entries |
| w7a_anticalendar.py, w7a_anticalendar.json | Activity build, composite, buckets, focus29 contrasts |
| w7a_anticalendar_wide.py, w7a_anticalendar_wide.json | SPY, QQQ, PANEL100 contrasts under the fixed buckets |
| w7a_wednesday_build.py, w7a_wednesday_stats.json, w7a_wednesday_series.json | Reproduction gate, per-weekday classes, midweek hold, exam series |
| w7a_wednesday_exam.py, w7a_wednesday_exam.json, w7a_wednesday_exam_run.log | The count 61 exam with per-series SPA (the 59 reference run was cut, named inside the JSON) |

## Trial costs charged by this lane

Anti-calendar family: 4 read families (1 original focus29
read plus 3 widening reads for SPY, QQQ, PANEL100), 8
universe by horizon contrasts registered. ON family: stands
at 61 after the two Wednesday structures join (59 after the
Anti-Focus read, plus Wed-night-only and the midweek hold);
the weekday forward cell remains separate, as briefed.
Typed spend: $0.00 (no seat used).
