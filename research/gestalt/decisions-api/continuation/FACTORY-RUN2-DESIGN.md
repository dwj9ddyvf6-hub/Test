# FACTORY RUN 2 DESIGN: grading the Run 1 crosses against the D-16 paired corpus

Written: Sat 2026-11-14, Continuation program, workstream C6.
Program home: ~/workspace/research_notes/decisions-api-leverage-20261114/
Status: DESIGN, ready to execute on Mon 2026-11-16 data. This
file builds nothing, registers nothing new, and grades nothing
by itself. It orders the run so that on Monday every step names
its input by path, runs in sequence, and stops honestly at any
missing input instead of substituting one.

SCOPE line. Surface: this continuation folder and the Run 1
factory record, read only, plus new Run 2 artifacts written
inside this continuation folder only. Constraints: no desk tree
edits, no sleeve changes, no Tensor code, paper and shadow only,
the three crosses Run 1 skipped by construction stay skipped.
Outcome: the 377 Run 1 registrations graded in a stated order
against the D-16 paired corpus first and against forward shadow
accrual second, with paired record conditioners added as grading
splits, an accrual wiring that starts on Monday data, and a run
falsifier that can retire the factory method itself. Proof: the
artifacts named in section 7, each read back after writing.
Edges: the D-16 corpus is being built in a parallel lane at the
path named in section 1; this design treats it as a named input
with a verification gate (Step 0), never as an assumption.

## 1. Inputs, every one named with its path

Run 1 factory record (both read in full or sampled by base and
conditioner for this design):

1. Index: ~/workspace/research_notes/decisions-api-leverage-20261114/x10/FACTORY-INDEX.md
   (377 registrations; base counts CAL-TWIN 14, CHN 24, CORP 24,
   DECAY 14, DSG 16, EXE 21, FIT 24, INS 32, NSM-ABS 48,
   NSM-BRK 72, NSM-SMA 64, TSR 24; conditioner counts CAL-FORCED
   46, CHN-CONF 48, CHN-DENY 45, DSG-SPLIT 48, FIT-HI 46, FIT-LO
   48, NONE 48, REGIME-BREAK 48; three crosses skipped by
   construction with reasons printed in the index).
2. Registry: ~/workspace/research_notes/decisions-api-leverage-20261114/x10/factory_registry.jsonl
   (377 rows; fields per row: id, base, conditioner, universe,
   horizon_sessions, name, mechanism_counterparty, provenance,
   data_contract, falsifier, status. Every falsifier is
   instantiated in the same form: forward shadow, deduped one
   observation per (name, date); after N graded events at the
   row horizon, if the conditioned cohort mean excess versus SPY
   is not positive and does not beat the unconditioned base
   cohort by at least 0.3 percentage points, the crossing is
   recorded flat and the registration closes. Event counts by
   horizon across the registry: 200 at plus 1 session, 120 at
   plus 3, 100 at plus 5 and plus 6, 80 at plus 10 and plus 12,
   60 at plus 20 and plus 42, 40 at plus 30 and plus 60.)
3. Standing fusion falsifier source:
   ~/workspace/research_notes/decisions-api-leverage-20261114/x10/FUSIONS.md
   (final section: if after two quarters of forward accrual no
   registered fusion cohort beats both of its parents on its own
   falsifier terms, the fusion method is recorded as adding
   correlation, not information, and the crossing grid is retired
   in favor of parent signal depth. Section 6 below is this
   falsifier restated for the factory, not a replacement.)

The new grading corpus:

4. D-16 paired corpus (parallel lane build, input to this run):
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/d16_paired_corpus.jsonl
   Schema, fixed by the building lane and verified at Step 0:
   sleeve, symbol, date, entry, stop, target, reward_risk,
   n_records_in_cell, executed, outcome (one of target_first,
   stop_first, open_at_horizon, or null while unresolved),
   r_multiple, sessions_to_outcome. Provenance of the underlying
   records, from the data census
   (~/workspace/research_notes/decisions-api-leverage-20261114/x10/DATA-CENSUS.md,
   section 2c): the per sleeve journals at
   ~/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl, whose
   last_evaluation events carry paired_records with entry, stop,
   and target. The corpus is the cross sleeve extraction of
   those paired records, deduplicated and graded forward. At
   design time (Sat 2026-11-14 evening) this file does not yet
   exist on disk; it is the one input whose landing Step 0 must
   prove. If it has not landed by the Monday run, the run is
   BLOCKED on that named artifact and reports exactly that. No
   substitute corpus is built inside Run 2.

Conditioner and grading stores the registry data contracts name
(all under ~/workspace/research_notes/decisions-api-leverage-20261114/hunt/
unless a full path is given):

5. fit_proxy_v1.json (FIT-HI, FIT-LO, and the FIT base; computed
   Q4 2026 to date, Focus 30; a record outside its dated coverage
   is NOT EVALUATED on FIT, never passed by default).
6. forced_events_calendar.json (CAL-FORCED; dated windows from
   2026-11-14 forward, with the forced family registrations
   behind it).
7. chain_screen_v1.json plus the desk IV ledger at
   ~/workspace/muse-desk-v3/state/iv_ledger.json (CHN base,
   CHN-CONF, CHN-DENY; at Run 1 the ledger holds one session of
   own history and cross sectional ranks carry the grade until
   own history percentiles reach the 60 observation minimum in
   the CHAIN-ANOMALY-DAILY registration).
8. disagreement_index_v2.json plus capture accrual (DSG base,
   DSG-SPLIT; Run 1 state: 68 symbol-days, 25 both sides days,
   50 with forward 1 session outcomes, 41 with forward 5).
9. decay_atlas_forward_seed.json plus accrual (DECAY base).
10. read_corpus_tranche1.jsonl plus calibration_table_v1.json
    (CORP base; tranche 1 is 29 reads plus 1 gap record over the
    Focus 30, asof 2026-11-13).
11. clv_twins_v2.json plus the fill ledger at
    ~/workspace/muse-desk-v3/state/fill_ledger/ (manifest.json,
    8,928 fills; EXE base).
12. nsm_fleet_v2.json plus the gate distance store at
    ~/workspace/muse-desk-v3/state/gate_distance.jsonl (NSM
    bases; the gate distance store is a single day snapshot of
    101 records at census time, which is why section 2 grades
    NSM against the corpus and not against gate distance history:
    that history does not exist at depth).
13. Truth serum seed record:
    ~/workspace/research_notes/decisions-api-leverage-20261114/runs/truth_serum_v1.json
    (TSR base; scoring at capture starts Mon 2026-11-16, so no
    capture exists for any corpus date; see the deferral in
    section 2).
14. Forward bars for grading forward only rows and for the SPY
    benchmark leg of every registry falsifier: Alpaca SIP daily
    bars through the estate bars route used by the H3 opponent
    lane (split adjusted, end clamped), and PF bar replays for
    the ADA and LINK universes, exactly as the registry data
    contracts state. No other bar source is used in this run.
15. Harvester machinery (the grading cadence Run 2 plugs into):
    ~/workspace/research_notes/decisions-api-leverage-20261114/tools/resolution_pipeline.py
    and
    ~/workspace/research_notes/decisions-api-leverage-20261114/tools/harvester_dashboard.py,
    with the family registry state at
    ~/workspace/research_notes/decisions-api-leverage-20261114/wave2/harvester_dashboard_v1.json
    (17 families, 783 claim resolutions at the wave 2 count) and
    the method record at
    ~/workspace/research_notes/decisions-api-leverage-20261114/wave2/W2-2-RESOLUTION-MACHINE.md.
    Cadence of record: cron resolution-harvester-nightly,
    weekdays 21:46 ET, first run Mon 2026-11-16.

Named missing inputs carried from Run 1, still missing, and
therefore deferrals in this run rather than silent gaps: the
EDGAR Form 4 corpus behind every INS row (Wave 2 workstream
W2-4 build; until it lands, INS rows are registrations against
a named missing input, per the factory index itself), and chain
own history at the 60 observation minimum behind CHN own history
percentiles (accrues from the Mon 2026-11-16 capture).

## 2. Which crosses grade FIRST against the corpus, and why

The ordering principle: the corpus grades first the signal bases
whose fires resemble paired records, because a paired record is
itself a graded fire (an entry with its stop, its target, and
its resolution). A base whose natural unit is already
(sleeve, symbol, date, entry, stop, target) can be matched to
corpus records without a translation layer, and every
translation layer is a place for a silent error. Bases that need
an external store dated on or before the record date grade
second, under a coverage guard. Bases whose conditioner did not
exist on the record date do not grade against the corpus at all;
grading them there would be lookahead fabrication, and this
design refuses it by name.

### Wave R2-1: corpus native grading, Monday night, no new tape needed

Grades in this order, each base first at conditioner NONE to fix
its unconditioned cohort, because every registry falsifier is
written as conditioned versus unconditioned and no conditioned
grade means anything before its base exists:

1. NSM bases (184 of 377 rows: NSM-BRK 72 at horizons 3, 12, 42
   over ADA, LINK, and SPOT-UNIVERSE; NSM-SMA 64 at horizons 5,
   20 over BTC, ETH, QQQ, SPY; NSM-ABS 48 at horizons 3, 6, 12
   over ADA and LINK). Why first: largest block in the registry,
   and the near miss idea is the corpus shape stated in words.
   A sleeve evaluation that almost fired and a sleeve evaluation
   that fired with a paired record differ only in which side of
   a gate the measurement fell, and the corpus preserves both
   populations with the same geometry (entry, stop, target,
   reward_risk). The band question (does the band just below the
   gate behave differently from the fire) becomes a corpus query:
   records are grouped by sleeve family and by distance implied
   in their geometry, and graded on outcome and r_multiple at
   the row horizons. Inside the family, NSM-BRK grades before
   NSM-ABS and NSM-SMA, because it is the one NSM family with a
   directional prior on record: the H2 measurement run found
   fires beating near misses at the traded horizons in the
   breakout family (plus 1.296 percent versus minus 1.513
   percent) while the absorption and SMA families read
   indistinguishable to slightly inverted, so BRK has a claim to
   confirm or kill and the other two have a null to measure
   honestly. Falsifier counts are the registry counts for each
   row horizon (120, 80, 60, 100, 40 per section 1).
2. CORP buckets (24 rows, FOCUS30, horizons 1, 5, 20). Why
   second: the corpus grades the corpus. The CORP base claim is
   that rate graded gestalt pattern buckets (the tranche 1
   example on record is downtrend_reversal at 25 of 25) are pre
   registered pattern claims; the D-16 corpus is an independent
   labeled population of the same estate reads and fires, with
   resolutions attached. Matching is by symbol, date proximity,
   and pattern bucket where the corpus record sleeve maps to a
   bucket family, and the grade is the bucket rate recomputed on
   paired outcomes (target_first share and mean r_multiple)
   against the tranche 1 calibration table rates. No external
   conditioner store is needed, so nothing in this grade can be
   blocked by coverage.
3. DSG disagreement (16 rows, FLEET, horizons 1, 5). Why third:
   disagreement is a property of a (symbol, date) cell, and the
   corpus is the first estate store that enumerates those cells
   completely, with n_records_in_cell carried on every record.
   The Run 1 index holds 68 symbol-days and is missing forward
   outcomes on 18 of them at plus 1 and 27 at plus 5; the corpus
   supersedes it as the counting source for split days (two or
   more sleeves, or sleeves on both sides where direction is
   carried, on the same symbol and date), and every split cell
   arrives with its paired outcomes already resolved or
   censored as open_at_horizon. The registered question (the
   split itself predicts smaller or larger forward moves;
   Run 1 Spearman of disagreement versus absolute forward return
   was minus 0.226 at plus 1 and minus 0.190 at plus 5) is
   re-graded on corpus outcomes at both horizons in one pass.
4. DECAY timing (14 rows, FLEET, horizons 1, 5). Why fourth, and
   why it grades at all in the corpus wave: sessions_to_outcome
   is a decay measurement carried on every resolved record. The
   Run 1 decay atlas was a forward seed with no accrual behind
   it; the corpus gives, per sleeve family, the empirical
   distribution of sessions to target versus sessions to stop,
   which is the peak horizon and zero crossing question the
   DECAY base asks, answered from resolutions instead of from
   another quarter of waiting. DECAY grades last in this wave
   because its rows are fewest and its answer feeds the other
   families horizon choices, so it is computed once, carefully,
   after the three larger grades have fixed their cohorts.

### Wave R2-2: coverage guarded grading, same run, after R2-1

5. EXE execution markouts (21 rows, FLEET, horizons 1, 5, 10),
   graded where the corpus executed flag and the fill ledger
   join agree on (sleeve, symbol, date). The corpus separates
   executed records from evaluated records, which is the control
   and treatment structure section 3 uses; EXE is graded in this
   wave because its store (clv_twins_v2.json plus the fill
   ledger) is complete for the desk window, unlike the stores
   below.
6. FIT base and the FIT-HI, FIT-LO, and CAL-FORCED crosses on
   the R2-1 bases, graded only for corpus records whose dates
   fall inside the dated coverage of fit_proxy_v1.json (Q4 2026
   to date) or inside a dated forced_events_calendar.json
   window. A record outside coverage prints NOT EVALUATED for
   that conditioner. No proxy is recomputed backward inside
   Run 2; a historical FIT build is a separate lane with its own
   provenance, and borrowing its name for a backfill is the
   borrowed identity error the H3 record refuses.
7. CHN base and CHN-CONF, CHN-DENY crosses, graded only in the
   cross sectional rank form Run 1 used, and only for record
   dates the chain screen or IV ledger actually covers (one
   session at Run 1). In practice this wave grades almost no
   historical CHN rows, and the design says so in advance: CHN
   is a forward accrual family in Run 2 (section 4), and its
   corpus grade is limited to a coverage census (how many corpus
   records fall on covered dates) printed in the report, so the
   absence is a counted fact, not a quiet skip.
8. REGIME-BREAK crosses on the R2-1 bases, graded wherever the
   record date index state (index below its 200 day line) is
   computable from the section 1 bar source. This conditioner
   is bar derived and dated, so it carries no coverage excuse;
   it grades across the full corpus span.

### Deferred, with the reason on the row, not graded in Run 2 first pass

- INS (32 rows): deferred whole. Input missing (EDGAR Form 4
  corpus, W2-4). First grade becomes possible the run after
  that corpus lands and passes its own Step 0 style check.
- TSR (24 rows): forward only. Truth serum scoring at capture
  starts Mon 2026-11-16; no capture exists for corpus dates, and
  reconstructing one from later chains would grade the past with
  information stamped in the future. TSR rows accrue shadows
  from Monday (section 4) and grade only on forward records.
- CAL-TWIN (14 rows): not a paired outcome claim. Its registry
  form is a calibration weight on other families fires (the
  fusion form is FX-07 in FUSIONS.md: calibration weighted shadow
  selection versus unweighted over two quarters). The forecast
  record behind it is thin on record (37 forward resolved calls,
  twin Brier 0.2197 against climatology 0.1695, trailing by
  0.0503, falsifier binding at 300). CAL-TWIN therefore grades
  on the forward shadow selection record over the two quarter
  clock in section 6, never on corpus outcomes, and Run 2
  carries its state as a named open row in every weekly print.
- Long horizon rows whose corpus records are still
  open_at_horizon (notably FIT at plus 60 and NSM-BRK at plus
  42): the open records are censored, counted as pending, and
  never scored as failures or as zeros. A row grades when its
  resolved count reaches the registry count for its horizon, or
  reports its resolved and pending counts side by side until it
  does.

## 3. What the corpus changes about the conditioner set

Run 1 crossed its bases with eight conditioners (NONE, FIT-HI,
FIT-LO, CAL-FORCED, CHN-CONF, CHN-DENY, DSG-SPLIT, REGIME-BREAK),
every one of which needs an external store. The corpus makes a
second conditioner class possible: conditioners derived from
the paired record itself, knowable at entry time, computable
for every record with no new data purchase and no coverage gaps.
Run 2 does not mint new registrations from them. They are
applied as grading splits on the existing 377 rows, every split
counted in the run trial count, and only a split that survives
its grade may be proposed as a Run 3 registered cross at a
Friday B5. That discipline keeps the factory honest about how
many things it has tried.

The paired record conditioners, with bands frozen in Step 2 of
section 5 before any grade is computed:

- RR bands, from reward_risk on the record: RR-HI at
  reward_risk at or above 2.0, RR-MID from 1.0 to below 2.0,
  RR-LO below 1.0. The 1.0 line is not invented for this run:
  it is the viability line the estate already uses on paired
  fires (the ghost book estate graded 11 of 21 fires viable at
  entry at R to target at or above 1.0). Question the split
  asks: does the conditioned edge live only in viable geometry,
  or does the base signal carry the low R records too.
- STOP-DIST bands, from stop distance percent, computed as the
  absolute value of (entry minus stop) divided by entry, times
  100, so long and short records are comparable: STOP-NEAR at or
  below 2 percent, STOP-MID above 2 and at or below 5 percent,
  STOP-FAR above 5 percent. Question: whether a base edge is a
  tight stop artifact (many small losses, few target hits at
  high R) or survives wide stops, which separates timing claims
  from geometry claims.
- CELL-DENSE versus CELL-SPARSE, from n_records_in_cell on the
  record: DENSE at 3 or more records in the (symbol, date) cell,
  SPARSE at exactly 1, with 2 as the reference middle. This is
  the corpus native form of the disagreement question, asked
  from the long side: lone fires versus crowded agreement,
  graded on the same outcomes DSG uses, so the two readings
  cross check each other.
- EXEC arms, from the executed flag: executed records are the
  treatment arm (the fleet actually took the fire) and evaluated
  but not executed records on the same (sleeve family, symbol,
  date) are the control arm, where the journals carry both.
  Where a family journal carries only executed records, the arm
  prints ABSENT for that family and no control is fabricated.
  Step 0 prints the executed share and the both arms share of
  the corpus, so the size of this conditioner is a counted fact
  before it is used. Question: whether the fleet selection of
  which fires to take adds or subtracts outcome value over the
  fires themselves, which is the cheapest execution alpha test
  the estate has ever been able to run.

Two hygiene rules bind every paired conditioner. First, entry
time knowability: reward_risk, stop distance, cell density, and
executed status are all facts at entry or at the entry decision,
so they may condition cohorts. Outcome, r_multiple, and
sessions_to_outcome are resolution time facts: they are grading
axes only and may never select a cohort, with the single named
exception of the DECAY base, whose claim is about resolution
timing itself and which therefore grades on sessions_to_outcome
by construction, selecting nothing with it. Second, dedupe: the
registry rule (one observation per (name, date)) is applied
inside every split, using n_records_in_cell as the cell weight
record, so a dense cell never counts as many independent
observations in any cohort mean. Cohort grades report both the
registry axis (mean excess versus SPY at the row horizon, from
the section 1 bar source) and the corpus axis (target_first
share and mean r_multiple), side by side. The row own registry
falsifier, written on the SPY axis, remains the binding verdict;
the corpus axis can demote a row early (section 6) but cannot
promote one on its own. No goalpost moves in either direction.

## 4. Accrual wiring for the top families shadows, from Monday data

Top families for accrual, in the section 2 order: NSM-BRK,
NSM-SMA, NSM-ABS, CORP, DSG, DECAY, plus EXE, and plus the
forward only families TSR and CHN, whose shadows are the only
record they will ever grade on. Every other Run 1 row accrues
under its NONE base cohort accounting only (its fires are
counted inside the base cohorts), so no registration is silently
dropped and no shadow store grows by 377 rows a day.

Daily wiring, each trading session from Mon 2026-11-16:

1. Capture (sources, all read only to Run 2): the desk runner
   appends the session evaluations to
   ~/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl; the
   D-16 building lane extends
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/d16_paired_corpus.jsonl
   with the session paired records in the section 1 schema; the
   chain capture extends chain_screen_v1.json accrual and the IV
   ledger at ~/workspace/muse-desk-v3/state/iv_ledger.json; the
   disagreement capture extends the disagreement ledger behind
   disagreement_index_v2.json; truth serum scoring runs at
   capture for the first time. Run 2 consumes these stores; it
   writes none of them.
2. Shadow writer (nightly, before the harvester pass): the Run 2
   tool built at Step 1,
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_shadow.py,
   reads the day new corpus records and the day conditioner
   store states, matches each record to every top family row
   whose base and conditioner it satisfies, dedupes to one
   observation per (factory row, name, date), and appends one
   shadow row per match to
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_shadow.jsonl.
   Shadow row fields: factory_id, base, conditioner, universe,
   horizon_sessions, sleeve, symbol, date, entry, stop, target,
   reward_risk, stop_distance_pct, n_records_in_cell, executed,
   run1_conditioner_value, paired splits (rr_band, stop_band,
   cell_band, exec_arm), state (OPEN on write). Paired
   conditioner values for every graded record, corpus and
   forward alike, are also written once to
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_conditioners.jsonl,
   so any later re-grade recomputes from a frozen conditioner
   record instead of re-deriving history.
3. Resolution (nightly, inside the same tool run, after the
   shadow write): an OPEN shadow row resolves when its corpus
   record carries an outcome (target_first or stop_first, with
   r_multiple and sessions_to_outcome copied from the corpus
   record, never recomputed), or, for forward only rows with no
   corpus record (TSR and CHN forward shadows), when its horizon
   closes on the section 1 bar source and its excess versus SPY
   over the identical window is computed. Resolved rows are
   appended as resolution records to the same shadow file
   (append only; no row is edited in place), carrying outcome,
   r_multiple where the corpus supplies it, excess_vs_spy where
   bars supply it, and sessions_to_outcome.
4. Harvester grading (the harvester grades it, Run 2 does not
   grade itself): cron resolution-harvester-nightly (weekdays
   21:46 ET, first run Mon 2026-11-16) runs
   tools/resolution_pipeline.py with the Run 2 grader built at
   Step 1,
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_grade.py,
   registered as the resolver for a new harvester family,
   FACTORY-RUN2, the 18th family in the registry behind
   wave2/harvester_dashboard_v1.json. Family unit: the shadow
   row. The grader recomputes, from the shadow file alone, per
   factory row: graded count against the registry count for its
   horizon, conditioned cohort mean excess versus SPY, the
   unconditioned NONE cohort for the same base, universe, and
   horizon, the 0.3 percentage point beat test, and the corpus
   axis twins (target_first share, mean r_multiple, and the
   section 3 split grades). Output, rewritten nightly:
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_grades.json,
   and the harvester dashboard gains the family posed, resolved,
   and pending counts in its normal form. A row whose graded
   count reaches its registry count is graded FLAT or SURVIVES
   on its own falsifier wording in that night grades file; the
   wording is recorded flat and the registration closes, or it
   survives to the section 6 clock. No intermediate verdict
   language is used.
5. Human print (weekly): each Friday B5, the week factory
   section of
   ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/FACTORY-RUN2-REPORT.md
   is appended from factory_run2_grades.json: rows graded, rows
   closed flat, splits that separated, coverage counts (NOT
   EVALUATED and ABSENT counts by conditioner), and the section
   6 clock state. The report is a view over the grades file; if
   the two ever disagree, the grades file governs and the report
   is corrected, never the reverse.

Stores written by Run 2, complete list: factory_run2_shadow.jsonl
(append only), factory_run2_conditioners.jsonl (append only),
factory_run2_grades.json (nightly rewrite), FACTORY-RUN2-REPORT.md
(weekly append), plus the two tools in section 5 and their
synthetic proof artifacts. Run 2 writes nowhere else. In
particular it writes nothing in the desk tree, nothing in the
x10 folder, and nothing in any registration file.

## 5. Execution order for Monday, step by step

Step 0, verify inputs before anything is built (Mon 2026-11-16,
before the session or at the latest before the nightly pass):
parse factory_registry.jsonl and confirm 377 rows and the
section 1 base and conditioner counts against FACTORY-INDEX.md;
confirm d16_paired_corpus.jsonl exists at its section 1 path,
validate every row against the 12 field schema and the outcome
enum, and print the corpus census (row count, date span, sleeve
count, resolved share by outcome, executed share, both arms
share, open_at_horizon share by horizon). If the registry
counts disagree with the index, or the corpus is missing, short,
or schema invalid, STOP: the run reports BLOCKED with the exact
artifact and discrepancy named, and no later step runs. A corpus
that fails Step 0 is the building lane defect to cure, not a
Run 2 input to work around.

Step 1, build the two Run 2 tools at their section 4 paths
(factory_run2_shadow.py, factory_run2_grade.py) and prove them
before any real row is graded, in the wave 2 synthetic
discipline: fabricated records only, inside
~/workspace/research_notes/decisions-api-leverage-20261114/continuation/synthetic_scratch/,
every file labeled SYNTHETIC in its name, no real ledger touched.
Hand checked expectations are written before the proof run
(dedupe collapses a shared (name, date) cell to one observation;
a split grade moves when its cell mean moves; a FLAT verdict
prints at exactly the registry count and not before). The tools
are accepted only when the synthetic grades match the hand
computations to the digit.

Step 2, freeze the paired conditioner bands in writing: the
section 3 bands (RR 1.0 and 2.0 lines, STOP-DIST 2 and 5 percent
lines, CELL 1 and 3 lines) are written into the header of
factory_run2_grades.json by the grader on its first run, before
any cohort is computed. Any later band change is a new run with
a new design, never an edit to this one.

Step 3, corpus grading Wave R2-1 in the section 2 order (NSM-BRK,
NSM-SMA, NSM-ABS, CORP, DSG, DECAY; NONE cohorts first inside
each base), writing factory_run2_conditioners.jsonl and the
first factory_run2_grades.json. Rows that reach their registry
counts on corpus records alone are graded in this pass; the
rest carry resolved and pending counts into accrual.

Step 4, corpus grading Wave R2-2 under its coverage guards (EXE,
then FIT and CAL-FORCED crosses inside coverage, then the CHN
coverage census, then REGIME-BREAK across the full span), same
artifacts. Every NOT EVALUATED and ABSENT count is printed in
the grades file, per conditioner, in this pass.

Step 5, paired splits: apply the four section 3 conditioners as
splits on every cohort graded in Steps 3 and 4, count every
split in the run trial count printed in the grades file header,
and record which splits separated (beat their unsplit cohort on
the corpus axis by the section 6 corpus stage bar) and which did
not. No split is registered in this step.

Step 6, arm the accrual wiring of section 4 for the Monday
session record: register the FACTORY-RUN2 family and its
resolver with the harvester configuration the W2-2 record
describes, confirm the resolution-harvester-nightly cron state
(enabled, weekdays, 21:46 ET) by read back, and run the shadow
writer once on Monday corpus extension as the first live accrual
proof, reading the appended shadow rows back before the
harvester pass.

Step 7, first print and clock start: append the first section of
FACTORY-RUN2-REPORT.md (Step 0 census, Steps 3 to 5 grades,
Step 6 accrual proof, deferred rows restated with their
unblockers), and start the section 6 falsifier clocks dated
Mon 2026-11-16. From here the run is cadence, not project:
nightly accrual and grading, Friday B5 prints, until a falsifier
or a promotion decision ends it.

## 6. The run own falsifier

Corpus stage falsifier, which can fire on Monday night: in Wave
R2-1, if no conditioned split or cross in any of the four corpus
native bases (NSM family, CORP, DSG, DECAY) beats its
unconditioned NONE cohort on the corpus axis by at least 0.10R
of mean r_multiple with at least 30 resolved records inside the
split, that base is recorded flat for conditioning purposes in
Run 2: its crosses stop accruing shadows, its NONE parent
continues, and the report names the base as a conditioning
failure, not as a signal failure. The parent signals are graded
by their own falsifiers; only the crossing claim dies here.

Interim demotion, at the first quarter checkpoint (2027-02-16):
any base family whose every conditioned cross trails its NONE
base on both axes (mean excess versus SPY and mean r_multiple)
on graded forward records is demoted to NONE only accrual for
the second quarter. Demotion is recorded in the B5 print nearest
the checkpoint with the numbers that forced it.

Standing falsifier, binding, in the fusion form: if, after two
quarters of forward accrual from Mon 2026-11-16 (final grade at
2027-05-16, reported at the nearest Friday B5), no conditioned
factory cohort has beaten its unconditioned base cohort on its
own registry falsifier terms (positive mean excess versus SPY
and at least 0.3 percentage points over the base, at the row
registered event count and horizon), the factory method itself
is recorded as adding correlation, not information. Consequence,
pre committed: the crossing grid is retired in favor of parent
signal depth, factory shadow accrual stops except for the NONE
parent cohorts, the surviving parents continue under their own
registrations and falsifiers, and no Run 3 crossing design may
be written without a new mechanism argument that answers this
result. This is the FUSIONS.md standing falsifier (no fusion
cohort beating both of its parents in two quarters retires the
fusion method) restated for the factory, where the unconditioned
base is the parent every cross must beat; the two clocks run
together and either one firing is reported in both records.

What does not falsify the method: a single family failing (that
is what per row falsifiers are for), a quarter of thin accrual
in a family whose registry count is not yet reachable (reported
as pending with counts, never graded early), or a corpus stage
failure in one base (section 6, first paragraph, demotes that
base only). The method falsifier binds on the whole grid, over
the full two quarters, on the rows own terms, exactly as the
fusion falsifier binds on the fusion family.

## 7. Artifacts this design produces when executed

- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_shadow.py (Step 1 tool)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_grade.py (Step 1 tool)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/synthetic_scratch/ (Step 1 proof set, SYNTHETIC labeled)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_conditioners.jsonl (Steps 3 to 4, then nightly)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_grades.json (Steps 3 to 4, then nightly rewrite)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/factory_run2_shadow.jsonl (Step 6, then nightly append)
- ~/workspace/research_notes/decisions-api-leverage-20261114/continuation/FACTORY-RUN2-REPORT.md (Step 7, then weekly append)

## 8. Gaps named honestly at design time

1. The D-16 corpus does not exist on disk yet (parallel lane,
   due for Monday). This design is executable the moment it
   lands and passes Step 0, and not before; that dependency is
   the design single hard blocker and it is named, dated, and
   gated rather than assumed away.
2. The executed versus not executed split of the corpus is
   uncounted at design time, because the corpus is unbuilt. If
   Step 0 finds the journals carried only executed records for
   most families, the EXEC control arm is small or absent for
   those families and section 3 prints that as a finding; the
   design does not promise a control arm the journals may not
   contain.
3. Gate distance history is one day deep (101 records), so no
   historical near miss grading exists outside the corpus
   resemblance argument of section 2. If that argument is wrong
   (if paired records turn out to be only fires, with no near
   fire population preserved), NSM grading in Wave R2-1 degrades
   to fire only cohorts and the band claim cannot be graded from
   the corpus at all. Step 0 tests this directly: it prints the
   corpus population by executed and by cell density, and the
   report must state, from those counts, whether a near miss
   population exists in the corpus before Step 3 claims one.
4. CHN own history and TSR capture both start Mon 2026-11-16, so
   two of twelve bases have no historical grade in Run 2 by
   construction. Their forward clocks are the longest in the
   run, and the weekly print carries them as accruing, with
   counts, until their registry counts are reachable.
5. INS remains blocked on the W2-4 EDGAR Form 4 corpus, whose
   landing date is owned by that lane, not by this run. Run 2
   neither builds it nor grades around it.
