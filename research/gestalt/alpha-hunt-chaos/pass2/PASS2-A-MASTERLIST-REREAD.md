# PASS 2, LANE A: MASTER LIST RE-READ AT FULL ITEM GRANULARITY

Coverage: 26,723 of 26,723 rows of REEXAMINATION-SUPPLEMENT-ROWS.jsonl were read individually and given their own Pass 2 disposition from their own fields (mechanical pre-pass over every row; register PASS2-A-REGISTER.jsonl carries exactly one output row per input row, same order, recounted at build). Of the 26,723 rows, 313 were individually seated on the Decisions API (plausibility + adversarial null), 10 of 10 blocks were connection-seated, and 24 objects carried a full seven-lens panel; seats never set any tier.

## POTENTIAL EDGE FOUND IN PASS 2

Every entry below names the row or cluster, the lead as it reads at full item granularity, and the cheapest forward check that would arm it. Seat values are lens output printed beside the record, never the basis of a tier.

### SW-11861 + SW-11900 + SW-11937 (one object: the oversold complex at fwd5)
RSI=OS alone reads +521.37bp mean excess (t 3.09, n 32, 4 nights); with MACD=BEAR- it reads +527.49bp (t 3.165); with RS10=WEAK +532.65bp (t 3.007). Three rows, one phenomenon, the largest per-row excesses among the 9 leads. Seat plaus 0.55/0.36/0.32 against nulls 0.78/0.77/0.79: the seat prices the few-nights risk honestly and the record still carries the size. Cheapest forward check: the step-13 gestalt axis-tag accrual already wired from Mon 2026-11-16 persists RSI/MACD/RS10 states per resolved outcome at zero new build; first night-clustered read at 20 accrued nights.

### SW-12047 (RSI=HIGH x POS10=MID, fwd5)
The single largest |t| among all 24,517 sweep rows: t 10.012 on +144.04bp mean excess, n 34 over only 3 nights. Either a variance artefact of 3 nights or the sharpest cell in the sweep; the row's own fields cannot decide, which is exactly what makes it a lead and not a verdict. Cheapest forward check: same axis-tag accrual; this cell's tag combination (RSI state x POS10 state at fwd5) is persisted by the existing schema, first read at 20 nights.

### SW-14931 + SW-14884 (MACD=BEAR- x VOLR=CLIMAX triples)
Graded rows with t 3.917 and 3.906, mean excess +1,396.74bp and +1,367.48bp, hit rates 0.923 and 0.909, on 3 nights each. They sit inside the 819 graded rows (of 4,279) whose mean excess is at least +100bp while the separator test reads false: the excess is large, the night count is the whole question. Cheapest forward check: night-clustered regrade from accrued axis tags at 20 nights, separator rule re-run unchanged.

### Cluster: 819 large-mean graded rows (mean excess >= +100bp, separator false)
At class granularity Pass 1 read these as graded nulls. At item granularity 819 of them carry triple-digit mean excesses inseparable only because independent nights are 3 to 8. The untested live angle is not the cells; it is the grading basis: pooled by night-cluster instead of by observation, the top of this cluster is the sweep's largest unexplored mass. Cheapest forward check: one regrade script over the accrued tag ledger at 20 nights; no new data collection.

### SW-10475 (VOLR=DRY x RNG10=WIDE x ATRPCT=EXT, negative)
The strongest negative low-n cell: t -10.412, mean excess -309.23bp, n 7 over 4 nights, promoted to WATCH by its own fields. Potential edge on the avoidance side: a registered condition set under which the book's selections reliably underperform is a veto-grade input and a short-side conditioner. Cheapest forward check: axis-tag accrual carries all three axes; first read at 20 nights, graded as an avoidance cell, not a signal.

### SW-06463 (DAY=UP x POS10=MID, overnight)
The strongest overnight-horizon lead: +42.88bp, t 3.256, n 40 over 7 of the panel's 8 nights, the widest night support of any lead. Seat plaus 0.36, null 0.70. Cheapest forward check: overnight cells accrue through the same tag ledger and the falsifier tracker's session rows from Mon 2026-11-16; first read at 20 nights.

### SW-00323 (VOLR=NORM x DAY=FLAT, overnight)
+53.40bp, t 3.038, n 35 over 6 nights, interaction +57.02bp: a two-axis interaction whose interaction term exceeds its own mean, the shape a genuine interaction (not two main effects) takes. Cheapest forward check: axis-tag accrual, interaction graded explicitly at 20 nights.

### SW-17946 + SW-17941 + SW-17942 (panel axes A08 volume state, A03 RSI, A04 MACD)
Of the 41 panel-graded axis rows, these three carry the seat's highest plausibility (0.50, 0.49, 0.49) with the panel's lowest nulls (0.56, 0.63, 0.57; panel plaus mean 0.299). The forecast panel already orders confidence correctly (Lane 7); these are the axes the panel's own grading most supports as live inputs. Cheapest forward check: the forecast-log axis extraction already exists (385 retrospective rows); grade A08/A03/A04 state x outcome on the forward forecast ledger from Mon 2026-11-16.

### BD-042 (aster_etf_qqq_monthly_c098) x Campaign 1 connection
The only sleeve whose children Campaign 1 could score at all is live-firing on the board, seat plaus 0.51, the board's joint highest (with BD-050 aster_etf_spy_monthly_m150, 0.51). Both scored children read at or below zero (C1-0147 INVERT_SIGNAL -1.61bp/day t -0.008; C1-0307 BOLT_RANDOM_VARIABLE -83.49bp/day t -2.929, DSR 0.0 both): the parent's monthly premium-selling mechanism is the live object, its mutations are not. The sleeve is also one of the 15 sleeve-wave wires (index verticals/collars/VRP gate state). Cheapest forward check: none to build; resolved closes under the virtual book give the first per-trade grades, and the G18 underwriting gate logs from Mon 2026-11-16 alongside it.

### Cluster: 154 NEARMISS_FLIP rows (Campaign 1 stage-1 class near_miss_feed_has_no_symbol_side_price)
Pass 1 read these as funnel fails. At item granularity they are 154 registered candidates whose only blocker was the pre-cure rejection feed carrying no symbol/side/price, and that feed was cured on 2026-11-15 (desk commit 87a3956, fields verified on a fixture read-back). The near-miss portfolio is the estate's named private-data object (773 true entry near-misses in the rejection history). Cheapest forward check: Campaign 2's NEARMISS_FLIP arm on post-cure intent records; the first graded near-miss shadow portfolio is already the INTENT-LOG-FIELDS row's own completing proof event across Monday's session onward.

### SW-17932 + SW-17931 (anti-Midna forward cohort x its control)
SW-17931, the founding control, grades MACHINERY in Pass 2 (its separation is the apparatus measuring itself; Lane 9 decomposed its return into universe beta plus a selection term of exactly zero). Its forward twin SW-17932, the cohort frozen at the 2026-11-13 close (29 names, 28 short bias), sits UNGRADABLE-BLOCKED on one missing field: the cohort's own forward resolutions. The connection is the candidate: if the frozen cohort's forward path separates from the sign-matched universe term the way the founding measurement did not, the inversion object is real; if not, the control has closed it. Cheapest forward check: one grading read of the frozen cohort once 20 forward nights have accrued from the freeze (early Dec 2026); the cohort needs no maintenance, it is frozen.

### SW-17791 (forecast corpus, slot=midday)
Hit rate 0.9016 on n 61, excess +15.57pp, q 0.1881, the forecast corpus's strongest slot object, in open tension with Lane 9's widened segment read, which killed the midday segment effect on cluster-robust grading. Both records stand; they are different objects (a forecast-slot conditional vs an unconditional segment mean), and the disagreement is preserved here rather than resolved by preference. Cheapest forward check: the forecast ledger accrues nightly; grade slot=midday calls specifically at the next 30 resolved calls.

### Cluster: 167 signal-shaped LOW-N rows promoted to WATCH
Pass 1 carried 8,537 LOW-N rows as one below-floor class. Read row by row, 167 of them carry |t| >= 2 on at least 4 nights (top by |t|: SW-10475 t -10.412, SW-06307 t 8.537, SW-10133 t 6.586, SW-06753 t 6.397, SW-00178 and SW-01101 t 5.372 on 5 nights). The seat disagrees with the promotion in aggregate (their nulls run 0.80 to 0.86); the disagreement is printed, and the tier rests on the rows' own fields. Cheapest forward check: the axis-tag accrual grades the whole class at 20 nights with no per-row work.

Connection seat, printed whole: asked for the single strongest potential-edge object in each of the 10 blocks (S1-P, S1-F, S1-T, S1-A, S1-M, S2-CAMPAIGN1, S3-BOARD, S4-PAIRS, S4-TRIPLES, S5-PROTOTYPE), the seat chose NONE in 10 of 10 blocks. That is a lens verdict on block-level selection, preserved as found; the per-row plausibility values above (which differentiate rows the argmax would not) are the same seat's finer read, and the two are in tension by design of the questions, not by error.

## TIER CENSUS (Pass 2, from the rows' own fields)

Of 26,723 rows: LIVE CANDIDATE 0, WATCH 323, MACHINERY 270, RESOLVED-AGAINST 4316, UNGRADABLE-BLOCKED 21814.

The zero is a finding about this register, printed with its scope: zero of 26,723 supplement rows carries a separating record in its own fields (the sweep's separator count was zero in Lane 7 and stays zero row by row). The estate's live candidates from the reexamination's named reads (the overnight Focus edge and its peers) are not supplement rows; where they touch this register they appear as blocked special objects (SW-17932, SW-17936) whose missing fields are named per row.

- S1-SWEEP (24517 rows): MACHINERY 2, RESOLVED-AGAINST 4279, UNGRADABLE-BLOCKED 19997, WATCH 239
- S2-CAMPAIGN1 (1200 rows): RESOLVED-AGAINST 37, UNGRADABLE-BLOCKED 1163
- S3-BOARD (339 rows): MACHINERY 268, UNGRADABLE-BLOCKED 3, WATCH 68
- S4-PAIRS (561 rows): UNGRADABLE-BLOCKED 545, WATCH 16
- S4-TRIPLES (6 rows): UNGRADABLE-BLOCKED 6
- S5-PROTOTYPE (100 rows): UNGRADABLE-BLOCKED 100

## TIER CHANGES FROM PASS 1

9,805 of 26,723 rows carry a Pass 2 change against Pass 1's class-level read; every changed row's own reason is printed in its register note (pass2_change + pass2_note). The change classes:

1. LOW-N split (8,537 rows): Pass 1 carried one below-floor class. Pass 2 promotes 167 signal-shaped rows (|t| >= 2, nights >= 4) to WATCH and grades 8,370 UNGRADABLE-BLOCKED, each with its own missing field (independent nights, with its n and nights printed).
2. Campaign stage-1 split (1,078 rows): Pass 1 carried one fail class. Pass 2 grades 1,043 as UNGRADABLE-BLOCKED data absences, split by the row's own stage1_reason (691 no parent event stream; 154 near-miss feed fields, since cured; 104 expression not priceable on stored history; 94 gate-blocked set unpriceable), and 35 byte-duplicates RESOLVED-AGAINST as non-independent objects.
3. Campaign stage-2 rows (122 rows): from funnel-fail class to UNGRADABLE-BLOCKED with the missing field named per row (parent event stream for 61; sufficient priceable scored events for 59; the 2 scored rows are RESOLVED-AGAINST on their own numbers, DSR 0.0).
4. The control rows (2 rows): SW-17931, Pass 1's one separating graded object, grades MACHINERY (a control measures the apparatus), as does SW-17967 (A29 anti-Midna sign, graded via the control line); the separation is preserved in the register fields, the disposition changes because a control is not a candidate.
5. Graded rows (4,279 rows): Pass 1 counted the GRADED class in aggregate (4,289 incl. leads and the control). Pass 2 gives each graded-no-separation row its own RESOLVED-AGAINST disposition with its statistics printed in its note; the standing caveat, independent nights at most 8, is printed in every note rather than once per class.
6. Live-firing board rows (68 rows): from operating census to WATCH; forward evidence is accruing on these sleeves and the disposition now says so. Fixture-proven and armed rows (268) grade MACHINERY.
7. UNGRADABLE-YET rows (6,522), EMPTY rows (5,105), NEVER-EXAMINED pairs and triples (551), prototype rows (100): all grade UNGRADABLE-BLOCKED in Pass 2, each row carrying its own named missing field (per-outcome persisted state, with the row's own reason text for 6,515 of the 6,522; observations for the empty cells; any examination for the pairs/triples; a scored outcome for the prototypes). Pass 1's softer labels are replaced by the blocker, named per row.

## METHOD AND SEAT ACCOUNTING

Mechanical rules were fixed before any seat result was read and are printed in full in pass2/mechanical_pass2a.py's header: GRADED status is the sweep's own grading floor (LOW-N is its below-floor class); a graded no-separation row is RESOLVED-AGAINST; leads, panel/forecast-graded, examined, and live-accruing rows are WATCH; operating apparatus is MACHINERY; every data absence is UNGRADABLE-BLOCKED with the missing field named from the row's own fields. Decisions API (gpt-6-luna, banks pass2a-plausnull and pass2a-lenses v1.0): 804 questions in 3 packs (400 + 236 + 168), 804 answers, 1 refusal(s) recorded as refusal (BD-030), cost $0.018339. Individually seated: 313 of 26,723 rows (all 9 leads, all 167 promoted LOW-N rows, both scored candidates, all 42 panel/forecast-graded rows, all 68 live-firing board rows, all 16 examined pairs, all 9 block-M special objects). The remaining 26,410 rows carry seat_scope=block with their block's connection result; no seat value was imputed to any row. One process note: the first seat run's connection questions used a malformed choice field and were rejected by the endpoint; the run was stopped, the format corrected to the proven schema, and the packs re-landed clean (checkpointed pack 1 reused, zero duplicate calls).

Disagreements preserved: the seat's adversarial nulls run 0.70 to 0.79 on the 9 leads and 0.80 to 0.86 on the promoted LOW-N class, against plausibilities of 0.31 to 0.55; the seven-lens panel on the top 24 objects gives lens means of 0.014 (the two scored candidates) to 0.313 (SW-06463), spread at most 0.23. The seat, read whole, is colder than the records' own statistics on every lead in this register. Tiers rest on the records; the seat's cold read is the standing counterweight, and both are printed.

Remainders, named: the 21,814 UNGRADABLE-BLOCKED rows grade only as their missing fields land (step-13 axis-tag accrual from Mon 2026-11-16 for the sweep classes; Campaign 2 for the campaign classes; the gamma pair's feed for BD rows; per-outcome persistence for the 6,522). No row in this lane was graded from anything but its own fields and the printed rules.

STATUS: PARTIAL — 26,723 of 26,723 rows carry an individual Pass 2 disposition proven on the final register (PASS2-A-REGISTER.jsonl recounted at build, one row per input row in order); the PARTIAL names the 21,814 rows whose potential is blocked on named missing fields and grades only as those fields accrue forward, and the seat lens's individually seated fraction of 313 of 26,723 rows (the remaining rows carry block-level seat results, printed as such).
