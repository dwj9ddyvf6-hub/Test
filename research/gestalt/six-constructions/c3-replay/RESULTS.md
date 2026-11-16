# C3 REPLAY RESULTS: REPAIR, THEN ROTATE

Workstream W3, Six Constructions, run Sun 2026-11-15 under the
pre-registration in ../C3-RUNFILE.md. Typed spend: $0.00. Research
artifacts only; nothing here touches the desk, the book, or any
trading state, and the module desk/research/bilbo-options/
iv_snapshot.py was never imported.

SCOPE: Surface, the C3 cell replay on the deep panel only.
Constraints, the frozen definitions of runfile sections 1 to 7, the
five same capital policies, the 5 basis point primary cost with the
registered 0 and 15 basis point sensitivities, and the registered
early termination exclusion sensitivity. Outcome, one observable
answer: whether rotating at repair adds incremental terminal wealth
after costs beyond holding, beyond cash at repair, beyond owning
the basket from entry, and beyond a fixed time switch. Proof, the
per policy paths and per event increments in results.json and
events_detail.json, read back after the run, plus the internal
formula check in section 5 below. Edges, the two named data limits
in section 7, printed on the face of this document.

Timing convention (Step 5 reconciliation amendment A7): all
observations are session closes. The repair fraction rho is
observed at a session close; every transfer executes at the close
of the next trading session. This is a close to close log return
accounting frame, not an intraday execution claim. Policy D forms
its basket at the entry close (the close of the entry session,
S plus 1) and buys at the next session close, per runfile sections
3 and 4 read together. Amendment A5 is recorded with no change: the
runfile stands as one registered instance of the package design
family (252 session beta window, 5 session shock window, damage at
least 0.10 log points, 126 session common endpoint, basket from
bars alive at the decision date). Amendment A6 is carried at full
strength in section 7 below.

## 1. Data, as recounted before use

Deep panel, ~/workspace/morgue/data_cache/deep_bars.json, recounted
in its current on disk state by streaming conversion into
panel_store/ (build_panel.py): 15,815 symbols, 22,497,888 rows,
2015-01-02 to 2026-11-13, SPY present. The recount is consistent
with the runfile inventory (15,815 names, 22,346,713 rows to
2026-10-28) plus the daily advance the inventory predicted. Spot
checks match the inventory exactly: XLNX and AABA present; BBBY,
TWTR, SIVB, FRC, and ATVI absent. Every bar in the panel falls on a
SPY calendar session (0 bars off calendar), so the SPY session
calendar (2,985 sessions) is the replay clock. Returns are split
adjusted price returns only, no dividend adjustment, for stock,
basket, and SPY alike, as registered.

## 2. Event funnel and admission

Candidate scan over all symbols (rolling 252 session OLS beta
ending the session before each 5 session shock window, damage d at
least 0.10, close at signal at least $5, mean daily dollar volume
over 63 sessions at least $5,000,000, valid bars at every session
of the beta and shock windows, valid entry bar):

| Stage | Count |
|---|---|
| Signal positions evaluated | 33,844,212 |
| With full 258 session contiguity | 17,332,036 |
| Pass damage at least 0.10 | 787,829 |
| Pass price floor | 527,344 |
| Pass dollar volume floor | 240,677 |
| Pass entry bar and beta (candidate events) | 240,660 |
| Suppressed, same name endpoint still open | 2,030 |
| Skipped, 10 positions already open | 238,420 |
| Admitted events | 210 |

Admission is chronological under the registered cap of 10
concurrent positions at $100,000 each on $1,000,000 initial
capital. The cap binds hard: the admitted stream is the first
arriving events in each window, which is a property of the
registered design, and it means the replay tests the first come
stream, not a random sample of the 240,660 candidates. One tail
property is named: the last admitted signal is at session 2802
(endpoint 2026-08-27); the 10 slots then stay occupied past
session 2924, while no candidate signal can exist after session
2857 (its endpoint must lie inside the panel), so the 10,746 late
candidates could never be admitted. Mean concurrent positions
9.98, maximum 10. Replay span: first entry 2016-01-12, last
endpoint 2026-08-27.

Of the 210 admitted events: 115 repaired (rho reached 1 before the
endpoint) and all 115 transferred; 0 repaired at the endpoint with
no transfer span; 95 never repaired, for which policies B and C
equal policy A by construction. No admitted original asset
terminated early (0 of 210 had no bar at its endpoint). Basket
members terminated early 298 times across all formations and were
liquidated at their last close with the per side cost charged, as
registered. Basket formation never came close to failing: the
smallest eligible universe at any formation was 647 names against
a basket size of 20. Four basket member weights (of 10,700 member
slots across 535 formations) found no execution bar before the
endpoint and stayed as cash; zero member executions needed a
gap bar.

## 3. The table: five policies, primary cost 5 bp per side

Terminal wealth on $1,000,000 initial capital, complete capital
paths, identical event stream for every policy:

| Policy | Terminal wealth | Total return | Turnover (x capital) | Mean deployed | Realized beta to SPY | Largest single name weight | Top 5 event profit share |
|---|---|---|---|---|---|---|---|
| A, hold original | $2,926,496 | +192.6% | 21.0 | $1,040,098 | 0.65 | 0.410 | 0.800 |
| B, cash at repair | $1,343,450 | +34.3% | 34.7 | $999,637 | 0.48 | 0.125 | 0.913 |
| C, rotate at repair | $2,265,609 | +126.6% | 48.4 | $1,010,413 | 0.68 | 0.123 | 0.416 |
| D, basket from entry | $2,456,202 | +145.6% | 21.0 | $1,008,937 | 0.73 | 0.134 | 0.301 |
| E, fixed time switch | $2,412,677 | +141.3% | 63.5 | $1,013,297 | 0.69 | 0.164 | 0.408 |

Capital occupation (time integral of deployed capital) in dollar
sessions: A 2,779,142,963; B 2,671,029,042; C 2,699,822,564;
D 2,695,879,368; E 2,707,530,020. Benchmark context only, as
registered: $1,000,000 held in SPY over the same calendar span,
no costs, ends at $4,013,603, above every policy. Realized betas
are description only and adjust nothing.

Portfolio differences at the primary cost, the registered primary
and secondary comparisons:

| Comparison | Difference |
|---|---|
| C minus A (primary) | minus $660,886 |
| C minus B | plus $922,159 |
| C minus D | minus $190,593 |
| C minus E | minus $147,067 |

Registered cost sensitivities, terminal wealth:

| Cost per side | A | B | C | D | E |
|---|---|---|---|---|---|
| 0 bp | $2,937,965 | $1,360,978 | $2,291,580 | $2,467,887 | $2,446,598 |
| 5 bp | $2,926,496 | $1,343,450 | $2,265,609 | $2,456,202 | $2,412,677 |
| 15 bp | $2,903,558 | $1,308,414 | $2,213,734 | $2,432,833 | $2,344,937 |

The ordering is identical at all three costs: A first, then D,
then E, then C, then B. The registered early termination exclusion
sensitivity was run at the primary cost and excluded 0 events,
because no admitted original asset terminated early; its terminal
wealth figures are therefore identical to the primary row, and the
sensitivity is vacuous for originals on this stream (it is not
vacuous inside the baskets, where 298 member liquidations were
charged in every policy that held them).

## 4. The registered estimand: incremental terminal wealth of rotating

Per event incremental terminal wealth of C versus A, computed on
complete paths, equals the registered formula V_tau times
(R_B minus R_A) minus K (section 5 check). Distribution at the
primary cost:

All 210 admitted events (the 95 unrepaired events contribute
exactly 0, because C equals A for them):

| n | Mean | Median | SD | P25 | P75 | Min | Max | Share positive |
|---|---|---|---|---|---|---|---|---|
| 210 | minus $3,147 | $0 | $68,186 | minus $802 | $8,794 | minus $841,435 | $113,504 | 0.295 |

The 115 repaired events with a transfer:

| n | Mean | Median | SD | P25 | P75 | Min | Max | Share positive |
|---|---|---|---|---|---|---|---|---|
| 115 | minus $5,747 | $4,776 | $92,243 | minus $23,785 | $33,605 | minus $841,435 | $113,504 | 0.539 |

Block bootstrap of the per event mean by entry quarter (21
quarters, 2,000 resamples, seed 20261115): 95 percent interval
minus $11,264 to plus $4,465, which includes zero. The single
worst event dominates the left tail: AGL (signal 2026-02-18,
entry 2026-02-19, repaired 2026-02-26), where holding ended at
$1,018,977 on the $100,000 allocation (the damaged name rose
about tenfold after repair) while rotating ended at $177,542,
an increment of minus $841,435. Policy A's profit concentration
is extreme (top 5 events contribute 0.800 of its total profit);
the rotation's diversification is real (0.416) but it pays for it
by surrendering exactly those post repair continuation gains.

## 5. Internal consistency check

On the 74 repaired events with no early termination anywhere in
the event (original survives to the endpoint, basket fully
traded, no early member liquidation), the registered estimand
formula V_tau times (R_B minus R_A) minus K, with K the transfer
costs grown in the destination leg, reproduces the independently
computed complete path difference C minus A with maximum absolute
difference $0.00000000004. The formula and the path accounting are
the same object, as registered.

## 6. Falsifier verdict, in the runfile's own terms

Runfile section 7: C3 is reported as falsified if any of three
conditions holds at the primary cost.

1. Policy C does not exceed policy A in terminal wealth:
   $2,265,609 versus $2,926,496. CONDITION HOLDS. There is no
   incremental post repair relative value after costs; the
   increment is minus $660,886 at portfolio level and minus
   $3,147 per event on average.
2. Policy D terminal wealth is at least policy C terminal
   wealth: $2,456,202 versus $2,265,609. CONDITION HOLDS. Owning
   the leadership basket from entry beats waiting for repair.
3. Policy E terminal wealth is at least policy C terminal
   wealth: $2,412,677 versus $2,265,609. CONDITION HOLDS. A fixed
   elapsed time switch also beats the repair timed switch.

VERDICT: FALSIFIED, on all three conditions. The switching
mechanism has not earned its complexity. One positive component
is named so it is not lost: rotating beat cash at repair by
$922,159 (C minus B), so the leadership basket was a better home
for recovered capital than cash; but holding the original asset
beat both, and the repair observation itself carried no timing
information beyond the passage of time (E) or no waiting at all
(D). Per the registration, this is reported as a basket effect
and a time effect, not as evidence for repair timed rotation.
No parameter was changed after results were seen.

## 7. Caveats on the face

Delisting coverage gap. The panel's universe was built from
Alpaca asset snapshots dated 2026-10-30; the inactive leg obtained
bars for only 2,240 of 18,419 inactive names, and names absent
from the Alpaca asset list entirely (BBBY, TWTR, SIVB, FRC, ATVI
confirmed absent on recount) are missing with no held source to
supply them. Direction of bias, stated honestly: the event
universe is survivor tilted at its edges. Damaged names that went
on to delist at or near zero are under represented among admitted
originals, which plausibly flatters policy A (holding a loser to
zero is the outcome rotation and cash exist to avoid) and so
plausibly biases the C minus A comparison against rotation. The
same gap flatters the basket legs (C, D, E), whose members are
drawn from names alive at the decision date in a panel assembled
in 2026. The net direction on the falsifier is therefore not
signed by this caveat alone; what can be said is that the missing
loser class is exactly the class where repair timed exit would
be expected to help most, and it is largely absent here.

No point in time constituents. The estate holds no historical
index or basket membership table. The leadership basket is
therefore the runfile's rule based basket computed from dated
bars alone, never index membership. Direction of bias: a name
must have bars alive at the decision date inside a panel whose
symbol list was assembled from 2026 snapshots, so the basket is
survivor tilted and its measured returns are plausibly biased
upward relative to a true point in time universe. This tilt
favors C, D, and E equally in kind; it does not explain C losing
to D and E, which share the same basket construction.

Further named limits. The concurrency cap admits a first come
stream (section 2), so the estimand is the effect on that stream,
not on all 240,660 candidates. Returns are split adjusted price
returns with no dividends anywhere, as registered, so no total
return claim is made. Cash earns zero, as registered. Executions
are next close accounting conventions, not intraday fills.

## 8. Trial ledger and files

Trials charged to C3: 1 prior (the registration) plus 4 in this
run: the primary replay at 5 bp, the 0 bp sensitivity, the 15 bp
sensitivity, and the early termination exclusion sensitivity.
C3 total: 5 trials. Typed spend: $0.00.

Files in this folder: build_panel.py and panel_store/ (the
recounted binary panel), c3_replay.py (scan and admission),
c3_account.py (baskets, accounting, statistics), candidates.json,
admitted_events.json, skipped_events.json (238,420 skipped
candidates with dates and names, plus the suppressed count),
events_detail.json (per event terminals and flags), results.json
(every number in this document), and the run logs.

STATUS: GREEN for the replay deliverable (the registered replay
ran in full and its numbers are read back from the final
artifacts above; the C3 construction itself is FALSIFIED per
section 6, which is the replay's finding, not a shortfall of the
replay). EVIDENCE POINTER: results.json and events_detail.json in
this folder, with the falsifier arithmetic in section 6 of this
document and the formula check in section 5.
