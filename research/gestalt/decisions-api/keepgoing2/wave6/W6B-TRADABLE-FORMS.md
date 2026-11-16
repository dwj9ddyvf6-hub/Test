# W6B. BASKET8 AND SEMIS12 TRADABLE FORMS, FCEL ON PRINTS (Wave 6, Lane B, 2026-11-15)

SCOPE: the two remaining clearing baskets of the overnight family (ON_basket8, ON_semis12) given the full Wave 5 energy8 treatment, and FCEL's single-name form priced forward off auction prints only. Membership extracted from keepgoing2/wave4/v2_family_exam.py, never from memory. Both new accruals are built to the Wave 6 amended field standard from birth. Paper and shadow only. No desk tree edits, no wave4 or wave5 file edits (Lane A's amendment targets were not touched), no production ledger written tonight. Every number below recounts from the artifact named beside it. No em dashes in this record.

## VERDICTS IN ONE BREATH

ON_basket8: auction-only, like every clearing basket in this family. Net at crossing -20.87bp with a 2-name carry subset (SNDK, MU); net at auction +23.12bp with all 8 names auction-positive, indicative only. Accrual wired on the amended standard and its cron armed and read back.
ON_semis12: auction-only, the least damaged at crossing of the three sub-baskets. Net at crossing -10.42bp with a 4-name carry subset (NVDA, AMD, MU, SNDK); net at auction +16.36bp with all 12 names auction-positive, indicative only. Accrual wired on the amended standard and its cron armed and read back.
FCEL single name: NO standalone forward accrual, decided in numbers in section 4. The print route is proven reliable (21 of 21 cross prints captured), but the single-name leg's variance makes a 60-session verdict a coin flip by construction, and its tradable sign flips with the cost estimator. FCEL keeps accruing inside the focus29 and energy8 basket accruals.
ON_fit_lo14: decided in the companion record (keepgoing2/wave6/W6B-FIT-LO14-SCOPING.md): option (a), a point-in-time FIT-PROXY rebuild plan with its full data contract, exam at trial count 46. The decision text there is verbatim-ready and is not repeated here.

## 1. ON_BASKET8 TRADABLE FORM (w6b_basket8_friction.json)

Membership (from v2_family_exam.py, the BASKET list): SMH, SOXX, SNDK, MU, CRDO, ALAB, AAOI, AXTI.

Count position, restated from the family exam with no new selection and no smaller family invented: ON_basket8 is 1 of 42 variants in the overnight family matrix at the combined trial count 45. At that count: DSR 0.97870, Sharpe 1.22, t 3.62, mean +0.135% per night (+13.50bp on its basket series), formed on 2,229 of 2,229 family sessions, verdict PROMOTE inside a family graded PROMOTE (PBO 0.000, SPA 0.000 vs SPY and 0.001 vs QQQ). Wave 3's older record had this member clearing at DSR 0.99577 at count 6 as the weaker sibling; the family exam at 45 governs now, and at 45 it is the weakest of the clearing baskets.

Friction: every name is covered by the held Wave 4 crawl, so every value is labeled held_crawl_wave4 in the artifact; no fresh SIP measurement was needed or made. The compute script (w6b_friction.py) recomputes from wave4/v1_friction_raw.json with the Wave 4 formulas and asserts its medians match wave4/v1_friction.json to 1e-9 for every name. Sessions: the same 10, 2026-11-02 to 2026-11-13. Gross is the mean of per-name full-history overnight means (the friction-net basis); the family exam basket-series mean (+13.50bp) is recorded beside it in the artifact and never mixed into the nets.

| Name | Gross/night | Crossing RT (median) | Net at crossing | Auction RT (median, signed) | Net at auction |
|---|---|---|---|---|---|
| SMH | +10.71bp | 20.81bp | -10.10bp | -8.38bp | +19.09bp |
| SOXX | +9.26bp | 9.28bp | -0.02bp | +3.37bp | +5.89bp |
| SNDK | +44.10bp | 15.39bp | +28.71bp | +2.24bp | +41.86bp |
| MU | +14.48bp | 11.88bp | +2.59bp | +1.57bp | +12.90bp |
| CRDO | +18.84bp | 78.67bp | -59.83bp | +3.59bp | +15.25bp |
| ALAB | +24.54bp | 88.44bp | -63.89bp | -21.84bp | +46.38bp |
| AAOI | +14.62bp | 47.66bp | -33.04bp | -7.20bp | +21.81bp |
| AXTI | +17.00bp | 48.37bp | -31.38bp | -4.76bp | +21.76bp |
| **Basket, equal weight** | **+19.19bp** | **mean 40.06bp, median name 34.24bp** | **-20.87bp** | **basket cost -3.93bp** | **+23.12bp** |

CARRY subset at crossing (names net positive at crossing): SNDK (+28.71bp, class CARRY) and MU (+2.59bp, class MARGINAL). Two of eight. The other six are friction-dead at crossing, ALAB worst at -63.89bp. A crossing implementation of the full basket loses 20.87bp a night against a 19.19bp gross; even the carry pair alone is a different, thinner trade than the member the exam cleared, and it is reported as a subset, not a substitute basket.

Auction-positive set: all 8 names, indicative only under the standing mid-reference caveat. Per-name auction medians on the wide names (ALAB -21.84bp signed, AAOI -7.20bp) are prints landing inside very wide spreads; only the basket-level auction figure (cost -3.93bp, net +23.12bp) is cited as a cost. Note the basket auction cost is negative on these 10 sessions, meaning prints landed better than the bracketing mids on average; that is a 10-session measurement, not a promise, and the forward accrual grades the basket session by session regardless.

## 2. ON_SEMIS12 TRADABLE FORM (w6b_semis12_friction.json)

Membership (from v2_family_exam.py, the SECTORS dict): SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC.

Count position, restated the same way: ON_semis12 is 1 of 42 variants at the combined count 45. At that count: DSR 0.98717, Sharpe 1.30, t 3.85, mean +0.132% per night (+13.23bp on its basket series), formed on 2,229 of 2,229 sessions, verdict PROMOTE in the same family. No new selection, no smaller family.

Friction: same held crawl, same assertion to 1e-9, every value labeled held_crawl_wave4, same 10 sessions.

| Name | Gross/night | Crossing RT (median) | Net at crossing | Auction RT (median, signed) | Net at auction |
|---|---|---|---|---|---|
| SMH | +10.71bp | 20.81bp | -10.10bp | -8.38bp | +19.09bp |
| SOXX | +9.26bp | 9.28bp | -0.02bp | +3.37bp | +5.89bp |
| NVDA | +15.51bp | 7.99bp | +7.52bp | +0.01bp | +15.50bp |
| AVGO | +13.42bp | 21.86bp | -8.44bp | +4.32bp | +9.10bp |
| AMD | +17.79bp | 11.68bp | +6.11bp | -1.90bp | +19.68bp |
| MRVL | +16.75bp | 27.06bp | -10.31bp | -3.12bp | +19.87bp |
| ARM | +14.60bp | 41.24bp | -26.65bp | +7.66bp | +6.94bp |
| TSM | +15.66bp | 39.98bp | -24.31bp | -7.06bp | +22.72bp |
| AMAT | +8.51bp | 56.34bp | -47.82bp | +0.77bp | +7.75bp |
| MU | +14.48bp | 11.88bp | +2.59bp | +1.57bp | +12.90bp |
| SNDK | +44.10bp | 15.39bp | +28.71bp | +2.24bp | +41.86bp |
| WDC | +8.58bp | 50.88bp | -42.30bp | -6.48bp | +15.06bp |
| **Basket, equal weight** | **+15.78bp** | **mean 26.20bp, median name 21.34bp** | **-10.42bp** | **basket cost -0.58bp** | **+16.36bp** |

CARRY subset at crossing: NVDA (+7.52bp, CARRY), AMD (+6.11bp, CARRY), SNDK (+28.71bp, CARRY), and MU (+2.59bp, MARGINAL). Four of twelve, the richest crossing subset of any sub-basket in the family (energy8 had zero, basket8 has two). It still does not rescue a crossing implementation of the member: the full basket nets -10.42bp at crossing, and the subset is a subset, not the member.

Auction-positive set: all 12 names, indicative only under the same mid-reference caveat; only the basket-level figure (cost -0.58bp, net +16.36bp) is cited as a cost.

Cross-basket read, for the wave report: the three sub-baskets now treated (energy8 in Wave 5, basket8 and semis12 here) are all auction-only. Their crossing damage ranks semis12 (-10.42bp) least, basket8 (-20.87bp) next, energy8 (-49.24bp) worst, and their basket auction nets rank basket8 (+23.12bp) first, energy8 (+18.13bp) second, semis12 (+16.36bp) third, on grosses of +19.19, +21.12, and +15.78bp respectively. None of that re-ranks the family exam, which grades the gross series; it ranks only how each member could be traded.

## 3. ACCRUALS FOR BOTH, AMENDED STANDARD, ARMED

Scripts: keepgoing2/wave6/w6b_basket8_accrual.py and keepgoing2/wave6/w6b_semis12_accrual.py. Ledgers (production, not yet created, by design): keepgoing2/wave6/on_basket8_shadow.jsonl and keepgoing2/wave6/on_semis12_shadow.jsonl. Anchor 2026-11-13; 60 forward sessions from Mon 2026-11-16; demotion if the mean net of 5bp over the first 60 recorded sessions is not positive.

Amended field standard, as built (each item is in the code and the docstrings, which agree with the computations):

- Docstring labels agree with computations: the crossing leg is labeled and computed as the MEAN of the per-name median quoted round trips (basket8 +40.063bp, semis12 +26.199bp, read at runtime from this lane's friction artifacts), and the auction leg as the basket-level signed cost, basket gross mean minus basket net-auction mean (basket8 -3.925bp, semis12 -0.583bp). No median-of-medians label anywhere.
- "symbols" list recorded per session beside the name count.
- Multi-day legs marked: "multiday_names" and "multiday_spans" (calendar days), judged against the union session calendar of the basket built from the fetched bars.
- Sub-minimum sessions written as marker rows {"skipped": true, "reason": "insufficient_names", "names_present": n, plus basket, date and symbols} and excluded from session counting and every mean.
- Verdict computed on the first 60 non-skipped sessions and frozen (the state prints verdict_basis_sessions 60 and verdict_frozen true once reached; later sessions never recompute it).
- Friction reads guarded against missing keys: any missing per-name or basket key yields a null leg, never a KeyError.
- Minimum-names rule, stated: three quarters (0.75) of membership, the energy8 adaptation logic (Wave 5 used 6 of 8). Here: at least 6 of 8 names for basket8, at least 9 of 12 for semis12.
- No earnings flag fields: those are Lane A's wiring on the two existing accruals only, per tasking; these two can gain the flag later by the same amendment route if the parent rules it.

Scratch dry runs (anchor shifted to 2026-11-12 via W6B_ANCHOR and W6B_LEDGER overrides, scratch ledgers in wave6):

- Basket8: one row for Fri 2026-11-13, {"basket": "ON_basket8", "date": "2026-11-13", "names": 8, "symbols": [all 8], "gross_bp": -128.246, "net5_bp": -133.246, "crossing_cost_bp": 40.063, "net_crossing_bp": -168.309, "auction_cost_bp": -3.925, "net_auction_bp": -124.32, "multiday_names": [], "multiday_spans": {}}; second run appended 0. (w6b_scratch_basket8.jsonl)
- Semis12: one row for Fri 2026-11-13, {"basket": "ON_semis12", "date": "2026-11-13", "names": 12, "symbols": [all 12], "gross_bp": -124.216, "net5_bp": -129.216, "crossing_cost_bp": 26.199, "net_crossing_bp": -150.414, "auction_cost_bp": -0.583, "net_auction_bp": -123.633, "multiday_names": [], "multiday_spans": {}}; second run appended 0. (w6b_scratch_semis12.jsonl)

Both rows are wiring proofs on a historical session (a hard down night for the complex; focus29's own dry-run row that night was -61.92bp gross), not forward sessions, and they grade nothing. Production ledgers verified absent after the dry runs.

Crons, armed and read back (cron view and cron status both read after arming):

- on-basket8-shadow-accrual: enabled, weekly Mon to Fri 09:46 America/New_York, next run Mon 2026-11-16 09:46:00 EST.
- on-semis12-shadow-accrual: enabled, weekly Mon to Fri 09:46 America/New_York, next run Mon 2026-11-16 09:46:00 EST.

One honesty note on the arming: both cron.add calls returned a tool timeout ("timed out waiting for tool-extension path sync") rather than a success receipt. The jobs are nevertheless armed: each was verified afterward by cron view (full body, schedule and enabled state read back exactly as submitted) and by cron status (enabled, next run stamp above, no runs yet). The timeout was in the tool's reporting path, not in the arming; the read-backs are the evidence.

## 4. FCEL SINGLE-NAME FORM, PRICED ON PRINTS ONLY (w6b_fcel_print_capture.json)

Method: the Wave 5 print route (w5a_carry_capture.py). FCEL is Nasdaq listed; the official opening cross print is the first exchange-Q trade carrying condition 'O' in the first seconds after the 09:30 ET open, and the official closing cross print is the first exchange-Q trade carrying condition '6' around the 16:00 ET close. Capture windows are computed per date in America/New_York and converted to UTC. That conversion matters and caught a defect in this lane's first run: the prior session, Fri 2026-10-30, is on daylight time, so its closing cross sits at 20:00:00Z, and a fixed EST window returned zero rows for it, silently dropping the first leg (9 legs instead of 10). The window code was fixed to be timezone-aware and the capture rerun; the EST sessions' prints are identical across both runs, and the rerun is the artifact of record.

Capture completeness: 21 of 21 prints. All 10 sessions (2026-11-02 to 2026-11-13) yielded exactly one opening cross and one closing cross, plus the 2026-10-30 closing cross at 11.22 (341,419 shares) that anchors the first leg.

Print-based per-session series (overnight leg: opening cross print over previous closing cross print; auction cost on prints: cross prints versus the held crawl's bracketing quote mids, the Wave 4 method's own mids):

| Session | Prev close cross | Open cross | Leg (bp) | Close cross | Auction cost on prints (bp) |
|---|---|---|---|---|---|
| 2026-11-02 | 11.22 (10-30) | 11.40 | +160.43 | 10.50 | +48.85 |
| 2026-11-03 | 10.50 | 10.79 | +276.19 | 11.21 | +96.12 |
| 2026-11-04 | 11.21 | 11.21 | 0.00 | 10.54 | -44.07 |
| 2026-11-05 | 10.54 | 10.00 | -512.33 | 8.93 | -20.04 |
| 2026-11-06 | 8.93 | 9.50 | +638.30 | 9.955 | -42.28 |
| 2026-11-09 | 9.955 | 10.16 | +205.93 | 10.82 | +49.22 |
| 2026-11-10 | 10.82 | 10.33 | -452.87 | 10.28 | +81.72 |
| 2026-11-11 | 10.28 | 11.05 | +749.03 | 10.95 | -22.66 |
| 2026-11-12 | 10.95 | 10.20 | -684.93 | 10.25 | +43.92 |
| 2026-11-13 | 10.25 | 10.15 | -97.56 | 9.68 | +74.29 |

Series summary on prints (10 legs): mean +28.22bp, median +80.21bp, standard deviation 477.40bp, range -684.93 to +749.03bp, positive in 5 of 10, t 0.19. Ten sessions of a name this volatile carry no grade; this is a measurement window, not an exam, and it is not read as one.

Auction cost distribution on prints (10 sessions): median +46.39bp, mean +26.51bp, standard deviation 53.53bp, range -44.07 to +96.12bp, positive (a cost) in 6 of 10.

Labeled comparison line, bar-based figures, not used anywhere above: Wave 5's bar-form auction cost median for FCEL was +28.66bp (range -63.43 to +93.87). The true-print median is higher (+46.39bp) and no tighter. Bar versus cross agreement in this capture: bar close matched the closing cross print in 10 of 10 sessions; bar open matched the opening cross print in only 7 of 10, which is exactly why this section is priced on prints.

Family context: ON_1n_FCEL in the family exam printed mean +42.03bp per night (bar-form, full history), Sharpe 1.42, t 4.22, DSR 0.99946 at count 45, PROMOTE. That gross is the number a single-name tradable form would have to survive against.

DECISION: no standalone FCEL forward accrual on prints is wired, and no cron is armed for it. Reasons, in numbers:

1. The sign of the tradable form flips with the cost estimator. Against the full-history gross of +42.03bp, the print auction cost leaves -4.36bp at its median (+46.39bp) and +15.52bp at its mean (+26.51bp). A form whose existence depends on which average of a 10-session cost sample you pick has no measured tradable form yet.
2. The 60-session family standard cannot resolve it. The print leg's per-session standard deviation is 477.40bp, so the standard error of a 60-session mean is about 61.6bp, larger than the entire +42.03bp historical gross. Reaching a standard error of half the gross (21bp) would take about 516 sessions, roughly two years. A 60-session FCEL verdict would be noise wearing a verdict's clothes.
3. The blocker is variance, not measurement. The print route captured 21 of 21 cross prints uniquely; if the estate ever registers a single-name FCEL accrual at an honest horizon (500 plus sessions, with its power stated on its face), the wiring is a day of work on the amended standard with prints as the gross source. Until then FCEL's forward measurement continues every session inside the focus29 and energy8 basket accruals, where its leg is diversified and the baskets' own auction costs measured +2.99bp and -0.63bp at basket level.

Typed seat (w6b_fcel_typed_seat.json, advisory only): no_accrual at probability 1.0 against wire_accrual at 0.0, and 0.50 probability that a 60-session verdict would correctly reflect the sign of FCEL's true long-run tradable mean, a coin flip, matching the power arithmetic above. Spend: 1 request, $0.000097.

## 5. TYPED SPEND AND ARTIFACTS

Typed-layer spend, this lane: 2 requests, $0.000200 total (fit scoping $0.000103, FCEL $0.000097). All seats advisory; both agreed with the decisions taken on the numbers, and neither gated anything.

Artifacts (all under keepgoing2/wave6/):

- W6B-TRADABLE-FORMS.md (this record)
- W6B-FIT-LO14-SCOPING.md (the fit_lo14 decision and data contract)
- w6b_friction.py, w6b_basket8_friction.json, w6b_semis12_friction.json
- w6b_basket8_accrual.py, w6b_semis12_accrual.py
- w6b_scratch_basket8.jsonl, w6b_scratch_semis12.jsonl (dry-run wiring proofs, 1 row each)
- w6b_fcel_print_capture.py, w6b_fcel_print_capture.json
- w6b_typed_seats.py, w6b_fit_typed_seat.json, w6b_fcel_typed_seat.json
- Production ledgers (not yet created, by design): on_basket8_shadow.jsonl, on_semis12_shadow.jsonl

## OPEN ROWS

- FIT-PIT-BUILD (from the scoping record): execute the FIT-PROXY-PIT-v1 primary quarterly form and grade it at count 46. Owner and date are the parent's to set.
- FCEL-LONG-HORIZON (new, named by section 4): a standalone FCEL print accrual is reconsidered only as a 500 plus session registration with its power stated; no action until someone registers it.
- The two new accruals' first production rows land Mon 2026-11-16 under their armed crons; a missing row Monday morning is an open defect against the cron, to be caught by the morning inspection.

STATUS: GREEN as a study and wiring record (both tradable forms proven on their friction artifacts, both accruals proven on scratch dry runs and armed with read-back stamps, the fit_lo14 decision filed with its contract, and the FCEL no-accrual decision proven in numbers on the print capture; the only unproven surface is Monday's first production rows, named above). EVIDENCE POINTER: keepgoing2/wave6/w6b_basket8_friction.json, keepgoing2/wave6/w6b_semis12_friction.json, keepgoing2/wave6/w6b_scratch_basket8.jsonl, keepgoing2/wave6/w6b_scratch_semis12.jsonl, keepgoing2/wave6/w6b_fcel_print_capture.json, keepgoing2/wave6/W6B-FIT-LO14-SCOPING.md.
