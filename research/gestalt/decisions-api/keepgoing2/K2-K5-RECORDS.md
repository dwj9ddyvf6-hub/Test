# K2, K3, K4, K5 RECORDS (KEEP GOING 2, 2026-11-14 night)

## K2 / M-07: EVENT-BLOCKED CPCV. Instrument built; validation PARTIAL, both sides printed.

Instrument: keepgoing2/k2_event_blocked_cpcv.py. Seasons are
indivisible blocks; splits are combinations of k=2 whole blocks
(45 splits at 10 blocks, mirroring the charter CPCV's 45); an
embargo drops the blocks immediately adjacent to a test block
from training; rank, omega, lambda and PBO math are the estate
CPCV's own conventions, unchanged. Results:
keepgoing2/k2_results.json and k2_sweep.json.

Synthetic truth tests, judged on an 8-seed sweep
(k2_sweep.py), because single seeds are anecdotes:
- T1, planted seasonal effect (a variant carrying a real effect
  in every season): blocked PBO below 0.2 in 8 of 8 seeds,
  median 0.038. The instrument does not refuse real seasonal
  effects. This side is PROVEN.
- T2, nested-window artifact (shared stream, one strong season,
  nested hold windows, the FX-01 family's own shape): blocked
  PBO median 0.386, above the naive day-group figure in only 3
  of 8 seeds, above 0.5 in only 3 of 8. At event-matrix scale
  (12 blocks of 10 days, 6 variants) the blocked instrument is
  NOT proven to discriminate the artifact better than the naive
  CPCV. This side is NOT PROVEN, and the record says so instead
  of claiming the cure. The first single-seed construction also
  failed its acceptance (blocked 0.273) and was replaced by the
  canonical shared-stream construction plus the sweep; both
  failures are in the record.

FX-01 methods check (method behavior only; no promotion
decision changes; the season grades in January): the FX-01
trial matrix rebuilt from the x10 run's own builder and data
(150 active hold rows, 10 seasons, 2016 to 2025). Blocked PBO
0.778, against naive CPCV on the same rows 0.911 and the
recorded full-matrix exam PBO 0.933. Reading, stated as method
behavior: whole-season holdout moves FX-01's PBO leg DOWN by
about 0.15 (its variants rank more consistently when seasons
cannot leak), and 0.778 still sits far above the 0.2 promote
line and the 0.5 kill line. Blocking neither rescues nor
condemns the family; it removes the unfairness objection to
the number, and the number remains a fail on that leg. The
fairness question now has an instrument; the instrument's own
artifact-discrimination power at this scale is the open row,
and any future seasonal family with more seasons (the estate
accrues one per year) strengthens it mechanically.

## K3 / D-09: CLOSING-AUCTION FEED ROUTE. Proxy built, first day computed; the real product named absent.

What the estate can source, probed tonight on its own Alpaca
route: final-minutes prints, in full. What it cannot: official
auction imbalance (NYSE OpenBook, Nasdaq NOII) is a proprietary
exchange product that Alpaca does not resell; no endpoint on
the estate's routes serves it. That is the named blocker for
CLOSE-IMB-01 in its registered form, with the route answers
recorded in the probe script's outputs.

Built instead, labeled on its face: TAPE-IMBALANCE-PROXY-v1
(keepgoing2/k3_probe.py; output
keepgoing2/k3_tape_imbalance_proxy.json). Buy versus sell volume
in the final 10 and final 2 minutes, side by the tick rule
against the previous print. First computed day, Fri 2026-11-13,
SIP feed (the proxy of record):
- SPY: 46,903 prints in the window; imbalance +0.259 at 10
  minutes, +0.430 at 2 minutes (buy-heavy into the close).
- QQQ: 38,438 prints; +0.028 at 10 minutes, +0.074 at 2 minutes.
The IEX subsets (2,145 and 1,101 prints) agree in sign and
differ in magnitude, and are labeled a thin cross-check, not
the proxy. The proxy measures final-minutes tape pressure; it
is not auction imbalance, and CLOSE-IMB-01's shadow can consume
it under that label from Mon 2026-11-16 while the real feed
remains a purchase-class unblocker.

## K4: CLV COVERAGE BUILD. Coverage lifted; the remainder named by instrument.

Build: keepgoing2/k4_fetch.py fetched daily bars for the 15
equity symbols behind the ungraded fills through the desk's own
warm route (desk3.warm._fetch: SIP, adjustment raw, the route
that built warm_bars.json), 53 sessions each, 2026-09-01 to
2026-11-13, zero session drops; LINK/USD daily came through the
same module's crypto route (76 rows). Extended map:
keepgoing2/warm_bars_extended.json. Ledger rebuilt by the
estate's own entry_clv logic pointed at the extended map:
keepgoing2/entry_clv_ledger_v2.json. Grader re-run:
keepgoing2/CLV-GRADE-02.md and clv_grade_v2.json (the grader's
internal rebuild check passes on v2: per-sleeve cells rebuilt
from v2 rows match v2's published aggregates, max deviation
4.99e-07; its twins comparisons now measure the v1 to v2 delta
and are reported as such, not as mismatches).

The lift, recounted from the two ledgers:
- Ungraded for no_warm_daily_series: 1,667 to 1,016 fills.
- Graded entry fills: T0 5,041 to 5,692 (+651); T1 5,024 to
  5,675 (+651). Entry coverage at T0: 75.1 to 84.9 percent of
  6,708 entries.
- aster_tensor_d20_pv graded 173 of 420 to 420 of 420;
  aster_tensor_d20_tensor 282 of 684 to 684 of 684; the s_mn_macd
  MDY row graded.
- Deduped cells: T0 396 to 429; T1 384 to 417.
- Estate deduped CLV: T0 -0.006497 to -0.006060; T1 -0.013927
  to -0.010613. The sign does not change at either horizon; the
  newly graded population is less negative at T1 than the v1
  population was.
- Sleeve coverage stays 42 of 339, stated plainly: the lifted
  fills belong to sleeves already in the table. The other 297
  sleeves have no entry fills in the ledger population and
  cannot gain CLV rows from any bar build.
- Classifications unchanged (LUCKY 0, GOOD 0, UNPROFITABLE 1,
  SAMPLE_TOO_SMALL 2): the binding gap was never bars; it is
  that only 3 sleeves hold realized P&L, all below threshold.

The remainder, named by instrument: all 1,016 still-ungraded
fills are OCC option contracts (16 distinct SPY and QQQ put
contracts; investandbefree_dmac family 1,015 rows,
qqq_put_ladder 1). No estate bar source serves an option
contract's daily close (the warm route serves equities and
crypto; the desk's options products are intraday snapshots).
The inherited CLV definition grades a fill against its own
symbol's daily close; grading an option fill against the
underlying's close would be a different definition, and it was
refused rather than substituted. Unblocker, named: a contract
daily-bar source (Alpaca options bars exist as a product; the
estate's routes do not currently fetch them), or a definition
amendment at a B5, either of which is a decision above this
lane.

## K5: FACTORY RUN 2, STEP 0 CENSUS. Gate executed; Run 2 cleared in reduced form, the reduction priced.

Executed tonight (keepgoing2/k5_step0.py) instead of Monday
morning, so Monday starts from a known state:
- Registry verified: 377 rows; base counts and conditioner
  counts match FACTORY-INDEX.md exactly; all 11 registry fields
  present per row.
- D-16 corpus validated: 244 rows, the design's 12 required
  fields present on every row (plus unresolvable_reason),
  outcome enum clean; 1 sleeve; executed share 48.4 percent;
  resolved 41.4 percent; both arms (executed and planned cells)
  present inside tensor_swing.
- Corpus v2 (K1) validated: 120 rows, schema and enum clean;
  11 sleeves; executed share 7.5 percent; resolved 19.2
  percent; both arms present in 5 of 11 trullas sleeves.
  Combined corpora: 364 cells, 124 resolved.
- The design's Step 0 question, answered from counts: a
  planned (non-executed) population DOES exist in the corpora
  (126 of 244 D-16 cells, 111 of 120 v2 cells), so the
  executed-versus-evaluated control arm is real where the
  corpora reach. But NO NSM-family sleeve appears in either
  corpus (the count is zero, printed by the census): the NSM
  sleeves journal in shapes that carry no priced geometry
  (K1's key census is the proof).

Verdict: Step 0 PASSES its verification gate (registry exact,
corpora schema-valid), so Run 2 is not blocked. It is CLEARED
for Monday in accrual and reduced-corpus form: Steps 1 and 2
(tools proven on synthetic records, bands frozen), the EXE wave
of Step 4 (the corpora's executed flags join the fill ledger
directly), the paired-split machinery (RR bands, stop-distance,
cell density, exec arms) on the cohorts the corpora actually
contain, Step 6 accrual arming, and Step 7's first print. It is
NOT cleared as designed for Wave R2-1's NSM, CORP, DSG and
DECAY corpus-native grading at registry counts: those cohorts
do not exist in the corpus, and grading them there would be
fabrication. The corpus-stage falsifier can run Monday night
only on combined-corpus splits with at least 30 resolved
records (the 124 resolved cells support the large splits, not
per-base cohorts). The unblocker is named and dated to the
Fri 2026-11-20 B5 as a desk-lane decision: a paired-record
stamp on the NSM sleeves' evaluations at the source, or a
design amendment scoping Run 2's first grade to the corpora
that exist. Neither is this program's to land tonight.
