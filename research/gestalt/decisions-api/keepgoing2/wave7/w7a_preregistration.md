# W7A PRE-REGISTRATION (written before any W7-1 outcome is computed)

Lane: Wave 7 Lane A, Sun 2026-11-15 night. Program home:
research_notes/decisions-api-leverage-20261114/. This file is the
pre-registration for W7-1 and the construction registration for
W7-2. It was written after inspecting activity-source COVERAGE
only (which dates each source holds). No activity count has been
joined to any return at the time of writing, and no W7-2 variant
return has been computed. The W5C decomposition numbers cited
below are prior lanes published record, not tonight outcomes.

## W7-1 ANTI-CALENDAR (CB-44): hypothesis

The estate busiest nights are systematically wrong-side for the
Focus complex: the focus29 basket overnight leg and its 5-session
forward return are WORSE on high-activity nights than on
low-activity nights. Two-sided test; the sign is read from the
data, the hypothesis predicts busy minus quiet is negative.

## W7-1 activity components (daily counts, ET calendar dates)

1. DROP: dead-drop entries per ET date. Source: grokbot-inbox/
   INBOX.md in dwj9ddyvf6-hub/quant-research-backup read via the
   GitHub API (live file, entries from 2026-10-25) plus its
   archive file grokbot-inbox/archive/INBOX-2026-10-05-to-
   2026-10-24.md (entries 2026-10-05 to 2026-10-24). An entry is
   a line matching the header pattern: three hash marks, a
   YYYY-MM-DD date, at line start. Only dates and counts are
   extracted; no post text enters any deliverable.
2. TYPED: typed-seat ledger rows per ET date. Sources: every
   ledger JSONL in ~/workspace/midna-book/typed-layer/ plus
   hunt/typed_seats_ledger.jsonl. Row date is its ts field
   converted from UTC to America/New_York.
3. READS: study and gestalt page artifacts per date. Source:
   entries (files or directories) in ~/workspace/research/
   composite-confidence/reads/ whose name contains a
   YYYY-MM-DD date; each entry counts once, under that date.
4. DESK: desk fires plus rejects plus gate evaluations per ET
   date. Sources: muse-desk-v3/state/dispatcher.jsonl (fires =
   event order_submitted or fill; rejects = event
   intent_rejected or broker_rejected_terminal; row date from
   the YYYYMMDD inside intent_id) and muse-desk-v3/state/
   gate_distance.jsonl (every row counts; row date from asof
   converted to America/New_York).

Known coverage at writing (dates only, no outcome contact):
DROP covers 2026-10-05 onward. READS is dense 2026-10-07 to
2026-10-14 and 2026-11-04 to 2026-11-14, absent between.
TYPED is concentrated on 2026-11-10 and 2026-11-13 to
2026-11-15. DESK covers 2026-11-11 to 2026-11-15 only, and its
gate rows fall on Sat 2026-11-14 and Sun 2026-11-15, which are
not session closes and so cannot enter the test.

## W7-1 composite rule (fixed here)

A night is a trading-session CLOSE date in the held w5c grid
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
the test and reported as coverage only.

## W7-1 test (fixed here)

Rank the analysis set by composite. BUSY = top tercile,
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
of the lab ledger terms as 1.

## W7-2 WEDNESDAY STRUCTURES (CB-29): construction registration

Family count: the ON family stands at 59 after the Anti-Focus
read (CHAOS-FOUNDRY-1-2026-11-15.md). The two structures below
join at AUGMENTED COUNT 61. The weekday forward cell
(W5C-WEEKDAY-FWD) is separate and is not charged here.
Reproduction gate, run before any variant: the held w5c
series must reproduce 2,229 sessions, mean +16.46bp, Sharpe
1.67, t 4.97 for ON_full, or the lane stops.

Night naming (fixed here, read carefully): a night is named
by its CLOSE weekday. Wed night means Wed close to Thu open,
which is the Thu-open leg in W5C open-weekday naming (W5C
printed Thu opens at +7.72bp, t 0.99, and Wed opens, meaning
Tue close to Wed open, at +28.71bp, t 4.25). Both namings are
printed in the record so no reader can confuse them.

Structures:
  (a) WED-NIGHT-ONLY: legs whose prior close is a Wednesday
      and whose open is the next session, a Thursday (span 1
      only; Wed closes followed by a Friday open across a
      Thursday holiday are excluded and counted).
  (b) MIDWEEK-HOLD: per event, Tue close to Thu open, per
      name open(Thu) over close(Tue) minus 1, basket equal
      weight, minimum 10 names, from wave3/focus_bars.json.
      Events require Tue, Wed, Thu to be consecutive sessions
      in the basket grid; other weeks are excluded and
      counted. Same-capital comparison, all on the same
      events: the hold return; the two single ON legs of the
      same nights compounded; the Wed intraday basket leg
      implied between them; per-night means (hold divided
      by 2) against the single-night mean.
Per-weekday legs: each close-weekday class (Mon, Tue, Wed,
Thu, Fri nights; all spans, span composition printed) gets
conditional statistics and an exam column.
Exam: one matrix at trial count 61 (reference run at 59 also
printed): columns ON_full, Mon-night-only, Tue-night-only,
Wed-night-only (structure a), Thu-night-only, Fri-night-only,
Midweek-hold-only; sub-series flat 0.0 outside their class,
the hold placed on its Thu open date; benchmarks SPY and QQQ
total returns on the same grid (w5c construction);
admission_exam.exam with is_new_family True. Hurdles as the
family applies them: DSR 0.95, SPA rejection against both
benchmarks at 0.05, CPCV PBO fair form as the exam prints it
(promote bar 0.2, kill bar 0.5), absolute t above 3. Every
variant also prints gross and net-of-5bp conditional means
(the hold net basis charges 5bp once per hold event, and its
per-night net divides by 2; single nights charge 5bp each).
Per-series SPA (single column against each benchmark) is run
for every exam column except ON_full, following the W5C
pattern.
Tape probes: CB-30 lunch hour and CB-31 first ninety seconds
are read against held data only (keepgoing2/
k3_tape_imbalance_proxy.json and keepgoing2/wave4/
v7_mk01_probe.json). Both files were inspected before this
registration: each covers only the 15:50 to 16:00 ET closing
window for SPY and QQQ. If no held file carries the probe
window, the probe is reported NOT SUPPORTED in one line with
the missing input named. No new intraday crawl is fetched
tonight.

## Rails

Real held data only; shadow only; no desk edits; heavy
compute only after a load-average check at or below 2.5;
typed seat optional (any use and spend reported); no em
dashes in the record.

## X10 WIDENING ADDENDUM (owner order 2026-11-15 01:15 ET,
## written before any widened outcome is computed)

The owner x10 order widens the W7-1 OUTCOME side to the
honest maximum. The activity series, the composite rule, the
analysis set, and the busy and quiet bucket labels are
UNCHANGED from the registration above (the buckets were fixed
by w7a_anticalendar.py under that registration; the widened
script reads them from w7a_anticalendar.json and recomputes
nothing on the activity side). At the time of this addendum
the only outcomes computed are the original focus29 ones.

Added outcome universes, same two registered horizons each
(overnight leg from close D to next session open; 5-session
forward close D to close D+5 sessions), same Welch contrast,
same net-of-5bp print, same anecdote-grade rule:
  (a) SPY alone, legs from wave3/focus_bars.json (the same
      bars the focus29 basket is built from).
  (b) QQQ alone, same source.
  (c) PANEL100 basket: foundry/panel100_bars.json, all 100
      names as fetched, equal-weight mean over names with
      both prints on the relevant dates, minimum 50 names
      or the date outcome is missing and counted. Session
      calendar is the SPY calendar in focus_bars.json.
TRIAL COST OF THE WIDENING: each added universe is one
additional anti-calendar read family (its two horizons ride
inside it, exactly as the original focus29 family was
charged). Added reads: 3. TOTAL anti-calendar trial cost
after widening: 4 read families, comprising 8 universe by
horizon contrasts, printed in full. The ON family count is
still not charged (no new ON variant is proposed; W7-2
carries the ON charges at 61).
W7-2 is unchanged by the widening: count 61 stands.
