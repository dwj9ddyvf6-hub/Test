# WAVE 5 LANE D: DESIGNS, SPEC, AND ACCRUAL

Sat 2026-11-14 late night, under the DON'T-STOP order. Lane D
deliverable summary for Wave 5 cells 3, 6, and 7. Every claim
below points at an artifact in keepgoing2/wave5/. Rails held:
no desk tree edits (dispatcher source read only), no edits to
any wave4 file, design documents claim no results, no personal
identifiers, no em dashes.

## W5-3 CW daily formation, pre-registered

Artifact: W5D-CW-FORMATION-DESIGN.md, dated and signed
2026-11-14, before the first live formation exists (first
possible formation Mon 2026-11-16).

- Construction mirrored from the Wave 4 proof (v4_proof.py,
  V4-V7-RECORD.md): CW spread = mean over matched pairs (same
  strike and expiry, both sides with modelled IV, band 0.75 to
  1.25 moneyness, expiries within 120 days) of (call IV minus
  put IV); minimum 20 matched pairs per name per session,
  justified from the dry cross-section (29 of 31 symbols at 67
  or more pairs; only FLNC 8 and EOSE 17 below the floor).
- Formation: daily cross-section over the 29 Focus names (SPY
  and QQQ are controls and benchmarks, never ranked), ranking
  by CW descending with symbol tie-break, long the top tercile
  (k = 10 at the full pool), short the bottom tercile, equal
  weight per name, each name held as a synthetic forward
  through its traded pair (earliest expiry at least 7 days out,
  strike closest to spot). A formation is valid only with at
  least 24 rankable names; every exclusion is named with its
  reason in grading.
- Horizon and cohorts: primary horizon 5 sessions; cohorts form
  daily and overlap, five live at one fifth of capital each.
- Friction: every option leg crosses its spread at both ends,
  priced from quote_bid and quote_ask in the panel IV ledger
  (the snapshot rows carry IV but the quotes live in
  iv_ledger_modelled.jsonl; the design's data contract says so
  explicitly). Unpriceable at entry excludes the name that day;
  unpriceable at exit triggers a named hold-extension rule,
  never a modelled mark.
- Exam and count: tools/admission_exam.py exam() on the
  forward-only variant matrix, trial count 24, listed in the
  design as 3 formation quantiles (quintile, tercile, quartile)
  times 4 horizons (1, 5, 10, 21 sessions) times 2 signs;
  primary column is tercile, 5 sessions, as-signed;
  is_new_family = True; SPA against SPY and QQQ.
- Minimum lawful grade: 130 accrued panel sessions (125
  cohorts fully exited, 26 non-overlapping 5-session blocks,
  matching the estate's registered 26-formation CW minimum;
  130th weekday is Fri 2027-05-14, holidays aside, count
  governs). Integrity read only at 26 formations.
- Falsifier: at that grade the primary series is demoted on
  any of DSR below 0.95, PBO at or above 0.2, SPA p at or above
  0.05 against either benchmark, absolute t at or below 3, or
  mean net daily return at or below zero; PBO above 0.5 kills
  the family. Data contract names the snapshot, IV ledger, and
  manifest fields relied on, the Mon 2026-11-16 accrual start,
  the exclusion of the 2026-11-14 dry capture from all counts,
  and the missing-day rules (no backfill, no forward fill,
  named gap flags).

## W5-6 D-01 reject payload spec

Artifact: W5D-REJECT-PAYLOAD-SPEC.md. Spec only, no desk edit.

- Seam, verified against the live source tonight (read only):
  desk3/dispatcher.py _reject(self, intent, sleeve_id, reason)
  builds the intent_rejected row and appends it to the journal;
  the stamp goes there, from the intent dict, before the
  append. The one inline construction site
  (insufficient_options_bp_csp) gets the identical stamp via a
  single named helper, _reject_stamp(intent), which every
  future intent_rejected writer must merge.
- Fields on every row, keys never omitted: event, intent_id,
  ts_utc (new explicit timestamp, the V3 cure), sleeve, reason
  (the reject class, field name unchanged), symbol, side, kind,
  qty, reference_price, reference_price_source (precedence:
  intent_price_hint, intent_limit_price, intent_stop_price,
  dispatcher_quote_mid_at_reject, else "unavailable"),
  missing_fields, missing_reason, stamp_version 1, plus the
  existing class extras retained unchanged. A genuinely
  unavailable field is an explicit null listed in
  missing_fields with a plain-language missing_reason, never a
  silent omission. Forward-only: no backfill claimed, legacy
  rows untouched, graders filter on stamp_version.
- Grading unlock, quantified from the Wave 4 census: today
  7,023 of 29,360 rows gradeable (23.9 percent, reconcile_halt
  only, side reconstructed from the fill ledger). On stamped
  rows, reconcile_halt plus insufficient_slice_bp are
  gradeable by class immediately from the row alone: 7,783
  rows, 26.5 percent at snapshot proportions, and every future
  reject class is gradeable from its first stamped row. The
  cluster caveat is carried into the spec's grading section:
  aggregation at (sleeve, symbol, session) cluster level is
  mandatory (Wave 4: 5,331 graded rows collapsed to 126
  clusters; row-level t is repetition inflation), with
  intent_id dedupe inside clusters.

## W5-7a MK-02 design plus honest in-sample read

Artifact: W5D-MK02-DESIGN.md.

- Question: does final-minutes tape imbalance condition the
  overnight leg. Forward design: TAPE-IMBALANCE-PROXY-v1
  computed daily on the 29 Focus names beside CLOSE-IMB-01
  from Mon 2026-11-16 (SPY and QQQ as controls), names needing
  at least 100 prints in the 15:50 to 16:00 window and sessions
  needing at least 24 valid names; primary series MK02-XS is
  the nightly equal-weight long top-tercile / short
  bottom-tercile overnight sort on final-10m imbalance, gross
  and net of the family's registered 5 basis points both
  recorded.
- Exam and count: graded as a member of the ON family with 12
  new trials (3 bucket splits x 2 windows x 2 forms), family
  trial count 45 + 12 = 57, exam() on its forward-only matrix,
  is_new_family = True for its own verdict. First lawful grade
  at 120 accrued valid sessions (120th weekday Fri 2027-04-30,
  count governs); integrity reads at 20 and 60 sessions grade
  nothing. Its falsifier demotes MK-02 alone and does not
  reopen ON_focus29.
- In-sample read (i), anecdote-grade, from
  keepgoing2/wave4/v7_mk01_probe.json: final-10m imbalance vs
  next overnight return, SPY r minus 0.053 (n 19), QQQ r minus
  0.033 (n 19); final-2m, SPY r minus 0.099, QQQ r minus 0.079;
  pooled across both symbols (38 symbol-nights sharing 19
  days, not independent), final-10m r minus 0.037 (t minus
  0.22), final-2m r minus 0.080 (t minus 0.48). Against the
  closing move inside its own window the same proxy reads
  r 0.448 (SPY) and 0.295 (QQQ). Read: contemporaneous only,
  nothing visible overnight at this size, and n 19 settles
  nothing in either direction.
- In-sample read (ii), NOT COMPUTABLE from the held artifacts,
  named exactly in the design: keepgoing2/
  k3_tape_imbalance_proxy.json carries per-symbol values for
  SPY and QQQ only and no Focus-name values, so no 29-name
  cross-section for 2026-11-13 exists in the artifact; and
  that night's overnight leg had not printed when the
  artifacts were written (the Wave 4 probe records next_open
  null for 2026-11-13, resolving Mon 2026-11-16). No crawl was
  run tonight, per the task; the forward accrual supersedes
  the missing day from Mon 2026-11-16.

## W5-7b Guidance-cuts forward accrual

Artifacts: w5d_guidance_cuts_accrual.py (the accrual script),
guidance_cuts_shadow.jsonl (the ledger), and
w5d_guidance_run_2026-11-14.log (tonight's run record).

- The script runs the Wave 4 parser route (imported, never
  edited) over 8-K filings after the Wave 4 census date
  2026-11-06: efts discovery over the parser's anchors, Archives
  fetch under the declared User-Agent, denominated-range
  parsing with verbatim snippets, chaining seeded with all 419
  Wave 4 statements, dedupe by the parser's 12-month per
  (ticker, metric) rule seeded with the Wave 4 deduped cohort
  of 35 events, cuts only appended. Event rows carry
  filing_date, event_date, symbol, accession, metric, period,
  pct_change, mid values, verbatim snippet and prev snippet,
  excess_5 and excess_21 null until matured (a maturation pass
  uses the Wave 4 study's exact entry and excess construction
  when a bar store covers the window; the current store ends
  2026-11-06, so forward rows stay null until a fresher store
  is wired), and status. Reruns are idempotent by event key.
- The ledger's first line is the genesis row, dated
  2026-11-14, zero events, grading rule on its face: grade at
  30 events; event-level +5 and +21 excess vs SPY; forward
  shadow ledger only; never a trade.
- Tonight's run, reported exactly: the route worked (efts
  answered all 7 anchors for the 2026-11-07 to 2026-11-14
  window; all-market totals 40, 4, 76, 32, 0, 0, 21) and zero
  of the fetched hits fell inside the parser's universe, so
  candidate docs 0, statements 0, appended cut events 0. That
  is a genuine zero for this 8-day window, not a route failure;
  the run log is the receipt. The ledger tonight therefore
  holds the genesis row only.
- Cron arming spec for the parent (proposed, NOT armed by this
  lane): id guidance-cuts-accrual-daily; schedule daily at
  about 19:46 ET, timezone America/New_York; command
  python3 ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave5/w5d_guidance_cuts_accrual.py
  with defaults (window from the census date forward, idempotent
  and deduped, so a daily rerun is safe); the job body must
  report appended count and total ledger events, name any route
  failure (fetch_fail above 0 or a non-empty route_log) as an
  open defect, and never report a grade before the ledger
  reaches 30 events.

## Typed seat

One judgment seated via ~/workspace/midna-book/typed-layer/
decisions_harness.py (runner w5d_seat_cw.py, full record
w5d_typed_seat_cw.json): whether the CW daily-formation design
as written is falsifiable at its stated minimum accrual of 130
sessions. The seat's answer, reported on its face: predicate
probability 0.23, meaning the seat leans against the statement
as phrased (its phrasing bundled three claims: the exam can
return a demoting verdict, the sample is large enough for the
lines to bind, and no open design decision remains). Advisory
only; the seat governs nothing and the pre-registration stands
as written. This lane's note, labeled as ours and not the
seat's: the demotion lines are fail-closed (a weak sample
demotes rather than promotes, because promotion requires
clearing every bar), so falsifiability in the strict sense
holds by construction; the seat's dissent is most charitably
read as pricing statistical power at 129 daily rows under
overlapping cohorts, which is exactly why 130 sessions is a
floor for a first grade and not a promise of a promotion.
Spend: 1 request, 710 input tokens, cost $0.000071 (harness
accounting, model gpt-6-luna). Lane total typed spend tonight:
1 request, $0.000071.

## Summary for the wave report (one paragraph)

Wave 5 Lane D pre-registered the CW daily formation (tercile
long-short synthetic forwards on the Cremers-Weinbaum spread,
5-session overlapping cohorts, spread-crossing friction from
the panel IV ledger, exam at trial count 24, first lawful grade
at 130 accrued sessions with demotion lines at DSR 0.95, PBO
0.2, SPA 0.05, and t 3), wrote the D-01 reject payload spec to
the dispatcher _reject seam (stamping symbol, side, kind, qty,
and a source-named reference price on every reject row unlocks
reconcile_halt plus insufficient_slice_bp, 7,783 of 29,360
snapshot rows or 26.5 percent, gradeable by class from the row
alone, with cluster-level grading mandatory), designed MK-02
as the ON family's imbalance-conditioned member (12 new trials,
family count 57, first grade at 120 forward sessions) with an
honest anecdote-grade in-sample read (SPY and QQQ imbalance vs
overnight r between minus 0.03 and minus 0.10 at n 19, pooled
r minus 0.037, and the 2026-11-13 basket cross-section named
not computable from the held K3 artifact, which carries SPY
and QQQ values only), and stood up the guidance-cuts forward
shadow ledger (genesis row dated 2026-11-14, grade at 30
events, never a trade) with its accrual script run tonight
over the post-census window (route healthy, zero universe
filings in the window, zero events appended) and a cron arming
spec left for the parent; one typed seat was seated on the CW
design's falsifiability and dissented at probability 0.23 for
$0.000071, reported on its face as advisory.

STATUS: PARTIAL in the estate sense only where named: all four
workstreams are delivered as artifacts; the open rows are (1)
the guidance-cuts cron is proposed, not armed (parent to arm);
(2) the guidance ledger holds zero events after a genuine zero
window, accrual begins with the next universe cut filing; (3)
every design's first grade is a future dated event (CW at 130
sessions, MK-02 at 120 sessions, guidance at 30 events), by
pre-registration, not by delay. EVIDENCE POINTER:
keepgoing2/wave5/W5D-CW-FORMATION-DESIGN.md,
W5D-REJECT-PAYLOAD-SPEC.md, W5D-MK02-DESIGN.md,
w5d_guidance_cuts_accrual.py, guidance_cuts_shadow.jsonl,
w5d_guidance_run_2026-11-14.log, w5d_typed_seat_cw.json, and
this file, all under keepgoing2/wave5/.
