# W6B. ON_FIT_LO14 SCOPING (Wave 6, Lane B, 2026-11-15)

SCOPE: decide, on the record, whether ON_fit_lo14 is scoped for a point-in-time rebuild or closed as untestable as stamped, grounded in what FIT-PROXY-v1 actually is. Paper and shadow only. No rebuild is executed in this lane; this is the scoping decision and its full data contract. No em dashes in this record.

## DECISION (verbatim-ready)

Decision: (a) a point-in-time FIT rebuild plan, scoped in full below. ON_fit_lo14 as stamped is untestable and its family exam numbers (Sharpe 1.92, DSR 0.99997 at the combined count 45) are not lawful evidence, because its membership is one Q4-2026 cross-section applied to the full 2018 to 2026 history. The member is not closed, because the conditioning variable is FIT-PROXY-v1, a price and volume proxy whose every input exists point-in-time on this box, so a lawful rebuild is a deterministic recomputation, not a data acquisition. What is rebuilt is the PROXY, labeled FIT-PROXY at every step. The true Coval-Stafford FIT is a different object, blocked on fund holdings and fund flow data that is not on this box, and it is not what this plan builds.

Typed seat (w6b_fit_typed_seat.json, advisory only): rebuild_plan at probability 1.0 against close_untestable at 0.0, and 0.99 probability that the rebuild can be executed entirely from data already held on this box. Spend: 1 request, $0.000103. The seat gates nothing; the decision above is taken on the facts below.

## 1. WHAT THE PROXY ACTUALLY IS (grounding)

Source records: hunt/H3-OPPONENT-ENGINE-1.md section 1, hunt/fit_proxy_v1.json, computed by hunt/work/compute_fit_proxy.py.

FIT-PROXY-v1, per its own definition record:

- Universe: the Focus names. Window as computed: Q4 2026 quarter to date, sessions 2026-10-01 through 2026-11-13 (32 sessions scored). Benchmark leg: SPY.
- Excess return: the name's daily return minus SPY's daily return, in percent, on split-adjusted SIP daily bars.
- Volume ratio: the session's volume divided by the mean volume of the prior 20 sessions.
- Sigma: the standard deviation of the name's own daily returns over the prior 60 sessions; a day is scored only with at least 20 prior returns on record.
- Pressure day: all three gates hold at once: volume ratio at least 1.5, absolute excess return at least 2.0 percent, and absolute excess return at least 1.0 times sigma.
- Contribution: absolute excess return in percent, times (volume ratio minus 1). FIT-PROXY-SELL is the sum of contributions over gated down days; the ranking the family exam used is ranking_by_fit_proxy_sell.
- The three gate constants (1.5, 2.0 percent, 1.0 sigma) are round numbers fixed in writing before the run, not tuned and not swept. Any change is a new version, not an edit.
- The family exam (keepgoing2/wave4/v2_family_exam.py) took the top 15 names of that single ranking as fit_hi and the other 14 Focus names as fit_lo, then applied both fixed lists to every session of the 2,229-session grid. Its own header carries the caveat: these columns test whether the names now under proxy pressure are the names that historically carried the premium; they are not a point-in-time conditioned strategy and are never cited as one.

Inputs a rebuild needs, per session, and whether they exist point-in-time on this box:

| Input | Needed for | On this box, point-in-time |
|---|---|---|
| Split-adjusted daily open, high, low, close, volume for each of the 29 Focus names | Daily returns, volume ratio, sigma, gated-day contributions | Yes. keepgoing2/wave3/focus_bars.json holds all 29 names plus SPY and QQQ: 56,454 bar rows in total, 54,224 for the 29 names plus SPY. Most names run 2018-01-02 to 2026-11-13 (2,230 bars); later listings start at their listing dates (for example CRWV 411 bars from 2025-03-28, SNDK 441 from 2025-02-13, ALAB 667 from 2024-03-20). Volume is carried in every row (field v). |
| Split-adjusted SPY daily bars | The benchmark leg of every excess return | Yes. Same file, 2,230 bars, 2018-01-02 to 2026-11-13. |
| Per-fund flows, lagged fund holdings, holder heterogeneity | The TRUE Coval-Stafford FIT only | No, and not needed for this plan. Named in fit_proxy_v1.json as inputs_missing_for_true_fit, with the supplying sources named there (SEC EDGAR N-PORT, Form 13F, derived flow series). That build is the separate H3 open row OR-1, due 2026-12-12 for construction. This plan does not depend on it and does not borrow its name. |

One provenance fact the rebuild inherits: the proxy's first pass ran on raw bars and fabricated a SOXX sell score from a split-scale discontinuity; the cured computation uses adjustment split throughout, and the rebuild uses the same split-adjusted source (focus_bars.json is the exam's own split-adjusted SIP pull).

## 2. THE REBUILD PLAN AND ITS DATA CONTRACT

Name: FIT-PROXY-PIT-v1. It is a new version, registered here, not an edit of FIT-PROXY-v1.

Per-session inputs (the full contract; nothing else enters):

1. For each Focus name and each session t on the family grid: the split-adjusted daily close and volume at t and at every prior session, from focus_bars.json (extended forward by the same SIP split-adjusted route when the series is extended; the extension route is the one the shadow accruals already use daily).
2. SPY's split-adjusted daily close at t and at every prior session, same source.
3. Derived per name per session, from prior data only: trailing 20-session mean volume (sessions strictly before t), trailing 60-session standard deviation of daily returns (returns strictly before t, at least 20 required or the day is unscored for that name), the session's own daily return and excess return versus SPY (final at t's close).

Stamping rule (what makes every session's membership lawful): two registered forms, one primary, and the primary is fixed now so the count below is honest.

- PRIMARY, quarterly completed-quarter form (the source study's own trade timing: liquidity is provided after the pressure quarter, per H3 section 4). For each calendar quarter Q, compute each name's FIT-PROXY-SELL score over the completed prior quarter Q minus 1, using only sessions inside Q minus 1 and lookbacks that reach before them. Membership for every overnight leg inside Q is the resulting fixed split: the 14 Focus names with the lowest prior-quarter sell scores form ON_fit_lo14_pit for that quarter, the other 15 form the hi half. Membership for a leg is therefore known in full at the prior quarter's close, before the leg begins, with zero lookahead. A name with too few bars to score in Q minus 1 (new listing) is placed by the stated tie rule: unscored names rank as highest pressure (excluded from the lo half) until they have a fully scored quarter, so a new listing can never enter the lo half on missing data.
- ALTERNATIVE, daily quarter-to-date form (not in the primary count): membership at session t from scores accumulated over the current quarter's sessions up to and including t, applied to the leg beginning at t's close. Lawful, but it churns membership daily and thins to near-empty windows at each quarter start. If this form is ever computed and graded, it is a second new trial and the count is incremented before grading, never after.

Series construction after membership: identical to the family exam's universe() construction (mean overnight leg over member names present that session, minimum 5 names, flat 0.0 below the floor, coverage recorded), so the rebuilt column is comparable to every other family column cell for cell.

Compute cost, estimated from the actual series sizes: the gate evaluation is one pass over the held bars, 54,224 name-days for the 29 names plus SPY returns, with rolling 20-session volume means and rolling 60-session return standard deviations precomputed in the same pass; the quarterly aggregation covers the 35 membership quarters, Q2 2018 through Q4 2026, times 29 names (Q1 2018 has no completed prior quarter in the held bars, so the rebuilt column is flat over Q1 2018 under the matrix convention, the same treatment the exam gives any unformed session). A naive upper bound that re-scans a full 64-session window per name-day is 29 times 2,229 times 64, about 4.14 million day evaluations. Either way this is a single Python job of seconds to a few minutes on this box, smaller than the family exam run it feeds. No crawl, no API window, and no filing wait is involved.

The exam the rebuilt member faces: the estate admission exam (tools/admission_exam.py, the same instrument and settings as v2_family_exam.py), on the full family matrix with the rebuilt column replacing the as-stamped fit_lo column's claim but not its count history. Trial count: 46, stated once here: the family's combined 45 plus 1 for the primary rebuilt variant. The daily alternative, if ever run, makes 47 and is counted before it is graded. Hurdles, unchanged from the family exam: DSR at least 0.95 at count 46, SPA below 0.05 against both SPY and QQQ, absolute t above 3, family PBO read on the same matrix. Falsifier on failure: any hurdle missed closes the rebuilt member as a find; the as-stamped column stays in the record as a labeled lookahead artifact, never cited as evidence either way. If the rebuilt member clears, its tradable form is then a friction exercise on held measurements, and its context is already computable from wave4/v1_friction.json: the 14 lo names carry an equal-weight gross of +19.21bp per night (mean of per-name full-history means), a crossing round trip mean of +51.24bp (net at crossing -32.03bp, carry subset at crossing MU and RKLB only), and a basket auction cost of +2.68bp (mean of per-name medians; net at auction +16.53bp on the mean-of-per-name basis). That context is printed here so the exam is not run blind to friction; it is not a tradable-form verdict, and no accrual is wired for fit_lo14 in this lane.

## 3. WHY NOT CLOSURE

Closure as untestable would be the right verdict for the true FIT (its inputs are absent) and for any member whose proxy needed data this box cannot stamp point-in-time. Neither holds here. The proxy is arithmetic on daily bars and volume; the bars are held, split-adjusted, full-history, and already the exam's own source. The only defect is the single-cross-section stamping, and the cure is recomputation under the stamping rule above. Refusing the rebuild would discard the family's strongest printed member (Sharpe 1.92) over a defect that costs minutes to cure, while citing its numbers anyway would be worse. The plan threads both: numbers void as stamped, member alive as a scoped rebuild at count 46.

## OPEN ROWS NAMED BY THIS SCOPING

- FIT-PIT-BUILD: execute FIT-PROXY-PIT-v1 (primary quarterly form) and run the admission exam at count 46. Owner: a future Wave 6 or 7 lane; this lane scopes it and does not run it, per its tasking. No date was set by the tasking; the parent sets it.
- OR-1 (pre-existing, H3): true Coval-Stafford FIT from EDGAR N-PORT and 13F plus a derived flow series, due 2026-12-12 for construction. Unchanged by this decision; the proxy rebuild neither waits for it nor substitutes for it.

STATUS: GREEN as a scoping decision (the decision, its grounding in the proxy's actual construction, the full data contract, the stamping rule, the compute estimate from actual series sizes, and the exam at a stated count are all on this record; the typed seat is printed beside the decision). EVIDENCE POINTER: keepgoing2/wave6/W6B-FIT-LO14-SCOPING.md, keepgoing2/wave6/w6b_fit_typed_seat.json, hunt/fit_proxy_v1.json, keepgoing2/wave4/v2_family_exam.py.
