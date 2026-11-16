# W2-2: THE RESOLUTION MACHINE (Alpha Hunt Wave 2, Sat 2026-11-14)

SCOPE: Surface, the decisions program home only (tools/ additions, wave2/ records); no desk tree edits, and iv_snapshot.py was never imported. Constraints, the withdrawn v1 aggregates stay withdrawn until reproduced from per-close rows in this record, NETTED treatment exactly as v1 defined it, synthetic data only inside wave2/synthetic_scratch/ and never mixed into a real ledger. Outcome, attribution ledger v1.1 with per-close rows, a scaled harvester registry with a graded-count dashboard, and an end to end synthetic proof of the Monday pipeline. Proof, the artifacts named at each section, recomputed and read back after writing. Edges, the harvester cron's first run is Mon 2026-11-16 21:46 ET (verified below); tape for Monday's resolutions does not exist yet, which is exactly what the synthetic proof stands in for.

Summary (no verdict is smoothed anywhere in this record): the withdrawn expectancy and win rate aggregates are reproduced exactly from per-close rows for all three sleeves that have any, and their deduped twins are identical to the raw figures because each sleeve's closes collapse to a single (symbol, date) cell. One v1 claim fails reproduction from per-close rows: excess vs SPY, named in section 1. The estate graded count, the number the Alpha Hunt falsifier watches, stands at 783 claim resolutions across 17 registered families, with 447 pending legs and the next resolutions landing Mon 2026-11-16. The Monday pipeline grades 10,000 synthetic claims in 0.083 seconds of compute, so Monday's real resolutions grade in hours with orders of magnitude to spare; the binding constraint on Monday is tape arrival, not throughput.

## 1. Attribution ledger v1.1

Tool: tools/build_attribution_v11.py. Artifact: wave2/attribution_ledger_v1_1.json (339 sleeves, 13 per-close rows). Sources, all read-only: the Lens T seeded rows (which preserve close events even though the v1 ledger artifact did not), ranking_rows.json (capital and the QQQ leg), attribution_ledger_v1.json (the claims under test), and the desk warm daily bars (the QQQ close-to-close leg; their 2026-11-13 SPY 754.37 and QQQ 679.89 closes match FORECAST-LOG.md exactly). The fill ledger behind the seeded rows verifies at 8,928 fills (entry CLV ledger v1 verification block: ok, total 8,928, no problems).

### Schema

Per-close row (one per own close, 13 rows): close_id, sleeve, symbol, open_ts, close_ts, open_date, close_date, qty, realized_usd, hold_days, win, loss, flat, r_multiple (null, with r_note: no stop or risk amount is preserved in the Lens T close event, so R is not computable for any of the 13 rows and is never invented), flags (verbatim), netted (boolean parsed from flags), allocated_capital_usd, benchmark_qqq_pnl_usd_approx, excess_vs_qqq_close2close_usd_approx (close-to-close daily bar approximation, labeled approx on the row).

Per-sleeve row (339): sleeve, klass, flags, allocated_capital_usd (new in v1.1), sessions, fills, own_closes, expectancy_usd, win_rate, realized_usd, twin_expectancy_usd, twin_win_rate, dedupe_cells, excess_vs_spy_as_recorded_v1, excess_vs_qqq_as_recorded_ranking (new in v1.1), ranking_realized_usd.

Allocated capital: ranking carries a real per-sleeve capital column (250 sleeves at 10,000; 64 at 1,000; the rest vary from 1,194 to 125,000; fleet total 2,967,192). The Level 4 design's uniform-capital proxy is retired by this column. All three sleeves with closes sit at 10,000.

QQQ excess leg, two forms, both labeled: (a) the ranking construction, carried verbatim as excess_vs_qqq_as_recorded_ranking, built exactly like the SPY leg (sleeve total return percent including unrealized marks, minus benchmark percent over the sleeve window); (b) a per-close close-to-close leg in the per-close rows. Form (a) carries the v1 SPY leg's own unit defect: it is a percentage-point figure that equals dollars only at 10,000 allocated capital. v1 printed the SPY version of it as dollars; v1.1 carries both legs labeled rather than hiding the defect.

### Reproduced vs v1

| Sleeve | v1 expectancy | Reproduced | v1 win rate | Reproduced | v1 realized | Reproduced | v1 avg hold | Reproduced | Twin expectancy | Cells |
|---|---|---|---|---|---|---|---|---|---|---|
| aster_trader_donchian55 | 686.17 | 686.17 MATCH | 1.0 | 1.0 MATCH | 5,489.35 | 5,489.35 MATCH | 2.12 | 2.12 MATCH | 686.17 | 1 |
| bta_onebar_rth | 220.45 | 220.45 MATCH | 1.0 | 1.0 MATCH | 661.36 | 661.36 MATCH | 1.0 | 1.0 MATCH | 220.45 | 1 |
| bta_onebar_qqq | -150.25 | -150.25 MATCH | 0.0 | 0.0 MATCH | -300.49 | -300.49 MATCH | 1.0 | 1.0 MATCH | -150.25 | 1 |

Also reproduced exactly: total realized across the estate's own closes 5,850.22 (the Level 4 provisional subtotal), the class counts (NOT FIRED 223, PARKED 54, LOW SAMPLE 62), sleeves with any own closes 3 of 339, sleeves at or above the 3-close bar 2, and CLEAN VERDICT-GRADE SLEEVES 0 (both bar-meeting sleeves carry NETTED, exactly as v1 treated them; their aggregates print flagged, never clean).

Disposition of the withdrawal: H2 run 2 withdrew expectancy and win rate for dedupe-certified use because v1 preserved no per-close rows. v1.1 preserves them, the recomputation matches v1 to the cent and to the fourth decimal, and the deduped twins (one observation per (sleeve, symbol, close date) cell, cell value the cell mean, twin the mean over cells, the entry CLV ledger v1 rule) equal the raw figures because every close of each sleeve shares one cell (donchian55: 8 CORZ closes all closing 2026-10-30; bta_onebar_rth: 3 QQQ closes all closing 2026-11-05; bta_onebar_qqq: 2 QQQ closes all closing 2026-11-04). The withdrawal is lifted on this evidence. The NETTED caveat is not lifted: it is a bookkeeping fact about shared exits, not a dedupe question.

### Claims that failed reproduction, named, not smoothed

1. Excess vs SPY (all three sleeves; headline instance donchian55 +11,923.30): NOT reproducible from per-close rows. The v1 figure is built on ranking total P and L including unrealized marks (donchian55 unrealized 1,186,271.19 on the shared book), a different population from own closes. It stands in v1.1 only as an as-recorded field with its construction named. Any future excess claim must be built from the per-close legs v1.1 now preserves (the QQQ close-to-close leg is the template; a SPY leg in the same form is a one-line extension and is rowed, not silently absent: owner, attribution lane, at the next nightly recompute).
2. Ranking realized for donchian55 (5,987.73) does not match own-close realized (5,489.35); difference 498.38. Ranking realized is the shared-book figure. v1 used the own-close figure, which the per-close rows prove correct for attribution; the ranking column is the one that must not be quoted as sleeve attribution.
3. R multiples: not reproduced and not computable from anything the estate preserved for these closes (no stop, no risk amount, no entry price in the close event). The v1 ledger printed no R; v1.1 prints the null with its reason on every row.

## 2. Harvester scaled: family registry and graded-count dashboard

Tool: tools/harvester_dashboard.py. Artifact: wave2/harvester_dashboard_v1.json. Every count is computed from its source artifact at run time. Counting rules: a family's unit is its own ledger's unit; the calibration table is a view over the canary, twin, pattern and journal families and is excluded to prevent double counting; execution-alpha markouts duplicate the CLV fill population and are excluded; CLV fill marks sit in their own subtotal, never inside the claim total. Families found beyond the brief's list: bank v2 upside_first legs, pattern continuation legs, canary panels, conveyor candidates, the sealed holdout, trail grader rows, visual card rows, and the entry CLV fill marks.

| Family | Posed | Resolved | Pending | Resolver | Next resolution |
|---|---|---|---|---|---|
| Forecast twin predicates | 37 | 37 | 0 | resolve_forecast_twin.py, SIP closes | complete; falsifier binds at 300 (37 of 300) |
| Bank v2 typed panels | 206 | 206 | 106 upside_first legs | graded at write; upside_first on SIP closes in 10 sessions | through 2026-11-30 |
| Selfaudit right_first | 5 | 0 | 5 | resolve_selfaudit.py, SIP closes | inside horizon; none overdue |
| Pattern panel | 35 | 35 form | 70 continuation legs | form at write; continuation on SIP closes (autopsy pack join still owed) | 2026-11-18 to 2026-11-30 |
| Canary panels | 24 | 24 | 0 | graded against the study's own words | complete |
| Book FORECAST-LOG calls | 362 | 362 | 0 tallied | graded in-file at each close review, SIP closes | nightly |
| Gestalt corpus tranche 1 | 87 | 0 | 87 | SIP printed sessions; levels on the record | 2026-11-16, 2026-11-20, through 2026-11-30 |
| Disagreement Index | 68 symbol-days | 50 at +1 (41 at +5) | accrual to 200 | warm bars forward returns | 2026-11-16 accrual |
| Calibration hypotheses | 7 | 0 | 7 | live forward fills, standard falsifier clock | time-locked; first clocks from 2026-12-10 |
| Ghost Book plus expression shadow | 48 | 0 | 48 | tape at expiry and own exit rules | 2026-11-27 (20 ghost), 2026-12-18 (1 ghost); 27 shadow legs carry no expiry field |
| Truth Serum fires | 21 | 21 | 0 (contrast ungradable: 0 passes) | verdict at write; forward contrast on tape, 100+ fires | nightly capture from 2026-11-16 |
| Book graded trades | 4 | 4 | 0 | own card and L-07 lines at close | nightly re-grade |
| Attribution own closes (v1.1) | 13 | 13 | 0 | own-lot FIFO over the 8,928-fill ledger | nightly recompute |
| Conveyor candidates | 23 | 23 | 0 | DSR, PBO, SPA vs SPY and QQQ at write | as the conveyor runs |
| Sealed holdout v1 | 60 | 0 | 60 | monthly re-test only, sealed by design | monthly; v2 accrual to 300 is a build row |
| Trail grader rows | 40 | 0 | 40 | records comparison plus sampled audit re-reads | no date on record |
| Visual card rows | 8 | 8 stage | 24 legs | stage at write; other legs on tape and re-read | no date on record |

Pending counts include sub-legs inside rows already counted resolved (bank v2 106, pattern 70, visual card 24), so posed and pending are not additive; resolved is the clean column.

### Headline numbers

- Claim families registered: 17.
- Claims posed (family units): 1,048.
- ESTATE GRADED COUNT (claim resolutions): 783. This is the number the Alpha Hunt falsifier watches.
- Pending legs: 447.
- Fill-mark grades, separate subtotal: 10,065 (entry CLV T0 5,041 plus T1 5,024 over the verified 8,928-fill ledger).
- Combined grades including fill marks: 10,848.
- Monday 2026-11-16 movement, named in advance so the falsifier can bind: 29 next-session corpus legs resolve at the close, disagreement accrual restarts, truth serum and ghost first-generation capture start, and resolution-harvester-nightly runs its first pass at 21:46 ET (cron verified enabled, weekdays, next run Mon 2026-11-16 21:46 ET, no prior run on record).

Resolver gaps, named: the pattern continuation legs still need the autopsy pack join; the trail grader and visual card families carry no resolution date on record; the expression shadow legs carry no expiry field and resolve only on their own exit rules. None of these is counted resolved, and none is smoothed over.

## 3. Synthetic proof of the Monday pipeline

Tool: tools/resolution_pipeline.py (the same entry point Monday's real ledgers use; only the input paths change; its closes path calls the v1.1 builder's own functions, so synthetic closes grade through the identical code as the real ledger). Scratch: wave2/synthetic_scratch/, every file labeled SYNTHETIC in its name, no real ledger touched.

Fabricated set: 6 level calls on 3 fake symbols against a fabricated tape, plus 4 fabricated closes across 2 fake sleeves (one NETTED) in Lens T seeded shape. Hand-checked expectations before the run: 5 calls gradable, 1 waiting (horizon 2026-11-20 not in tape); SYN-02 Brier 0.16; mean Brier 0.1145; synth_alpha raw expectancy 46.67 with a twin of 47.5 (its two FAKEA closes share one cell, so the twin must move, proving the dedupe is live code and not a copy of the raw figure).

Result, read back from graded_SYNTHETIC.json: graded 5, waiting 1 with the reason on the row; hit rate 1.0; mean Brier 0.1145, matching the hand computation to the digit; per-close rows 4; synth_alpha expectancy 46.67, twin 47.5, twin win rate 1.0 against a raw 0.6667 (the shared cell is net positive), synth_beta expectancy -80.0; QQQ close-to-close legs computed on the fabricated tape (benchmark 20.0 on the 10-share FAKEA closes). Runtime: 0.0005 seconds internal, 0.181 seconds wall including interpreter start.

Scale run: 10,000 fabricated claims graded in 0.083 seconds internal, 0.277 seconds wall (graded_scale_SYNTHETIC.json; hit rate 0.5056 and mean Brier 0.3307 on random probabilities, as expected of noise). Full real-side recompute for scale: the v1.1 builder plus the dashboard census over every source artifact above took 3.2 seconds wall together. Conclusion: when Monday's tape prints, the 29 next-session corpus legs and every other due family grade the same evening, inside the 21:46 ET harvester pass, with throughput headroom of roughly five orders of magnitude. The pipeline is not the bottleneck; tape arrival is.

## Open rows

1. SPY per-close excess leg in the v1.1 close-to-close form (the QQQ leg is the template): attribution lane, next nightly recompute.
2. Pattern continuation resolution needs the autopsy pack join: harvester lane, before 2026-11-18 when the first continuation legs come due.
3. Trail grader (40) and visual card legs (24) carry no resolution date on record: dates to be registered by their owning lanes; until then they print pending with no date, as above.
4. Forecast twin falsifier clock: 37 of 300 resolved; the twin trails climatology by 0.0503 Brier on the only forward cohort, recorded in run 1 and not smoothed here.

STATUS: GREEN for W2-2 as scoped (v1.1 built and proven against v1 with the one failed claim named, the registry and dashboard computed from source artifacts, the Monday path proven end to end on synthetic data at scale). EVIDENCE POINTER: wave2/attribution_ledger_v1_1.json, wave2/harvester_dashboard_v1.json, wave2/synthetic_scratch/graded_SYNTHETIC.json and graded_scale_SYNTHETIC.json, built by tools/build_attribution_v11.py, tools/harvester_dashboard.py and tools/resolution_pipeline.py.
