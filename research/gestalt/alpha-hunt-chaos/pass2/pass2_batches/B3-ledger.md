# B3 LEDGER: CONVERSION PASS 2, BATCH B3 (19 WATCH objects, register[86] to register[107] as listed)

Worked Sun 2026-11-15 night under the owner order of 21:03 ET. Method per object: numbers first, routes tried before tonight, then the nine routes in the mandated order (1 desk-shares, 2 book-options, 3 basket, 4 pair, 5 variation, 6 timeframe shift, 7 proxy-data, 8 conditioner, 9 fade), each with its result. No desk tree, grader config, book or Conversion Register was edited; every arming below is a proposed row in B3-rows.jsonl. Statuses: SHADOW-ARMED only where the wiring is a pure grader-config addition in the CONV-25 to CONV-38 arm form or an existing book instrument; SPEC-READY where complete arming is specified but needs a wiring act.

## P2-B3-01: 1-night-old lot closures precede rises (register[86])
Numbers: 91 rows aged exactly 1 night, 69 priceable at post5: post1 +1,063.0bp (n 85), post5 +3,320.7bp (clustered t 0.41 on 5 clusters), post10 +2,064.7bp (n 64), cut share 0.971; 63 of 91 rows are one sleeve (L1), 64 of 91 exit on 2026-10-29/30.
Routes before tonight: The VEIN3 dig itself and its registered forward check (exit log keyed by lot age, next 20 non-saty closures). No conversion form existed.
- Route 1 (desk-shares): Not runnable as a standalone: the object is a property of exits, not an entry signal; there is no entry to take in shares.
- Route 2 (book-options): Not runnable: no options expression of a post-exit drift on other sleeves' exits exists on book instruments.
- Route 3 (basket): Not applicable as a basket entry; the pooled basket of all 1-night closures is the saty-contaminated read the record warns against (63 of 91 one sleeve).
- Route 4 (pair): Not applicable: no second leg is claimed.
- Route 5 (variation): A loosened age band (lots aged 1 to 2 nights) was considered and not authored: it would grade a different population than the registered falsifier names, and the exact-age forward check costs nothing to run first.
- Route 6 (timeframe shift): Horizons already span post1, post5, post10 in the record; post5 is the registered decisive horizon, kept.
- Route 7 (proxy-data): Proxy: the pooled in-sample read is the proxy and it fails as evidence (clustered t 0.41, 5 clusters, 2 exit dates carrying 64 of 91 rows); named here so it is never quoted as the grade.
- Route 8 (conditioner): CONVERTED: shadow hold overlay on forward exits closing 1-night-old lots, graded on exit_why_grader.py, split saty vs non-saty, falsifier mean post5 at or below 0 over the next 20 priceable non-saty closures.
- Route 9 (fade): Fade (exit earlier or double down on exit) contradicts the claim's direction and has no independent support; not runnable as a form.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing. Row P2-B3-01.
Sole remainder: The forward accrual: 20 priceable non-saty 1-night closures from Mon 2026-11-16.

## P2-B3-02: Anti-Calendar, CB-44 (register[88])
Numbers: Busy minus quiet, n 4 against 4: focus29 +123.72bp (t 0.40, p 0.707), SPY +51.14bp (t 1.29, p 0.265), QQQ +57.26bp (t 0.63, p 0.551), panel +52.22bp (t 0.51, p 0.629); 13 overlap close dates.
Routes before tonight: The Wave 7 first read and its pre-registered re-read at about 26 close dates. Carried open as an anecdote-grade read, not killed.
- Route 1 (desk-shares): Not runnable: the object makes no entry claim; its sign runs opposite the hypothesis, so a shares form built on the hypothesis would trade the wrong way on n 4 against 4.
- Route 2 (book-options): Not runnable: no options form of a calendar-state observation exists, and CONV-01's options route is closed on two chain sources in any case.
- Route 3 (basket): The basket it describes (Focus 29 overnight) already exists as CONV-01; a second basket adds nothing.
- Route 4 (pair): Busy vs quiet is already the pair contrast; it is graded as the split in route 8.
- Route 5 (variation): No variation authored: loosening the busy definition would multiply an n 4 against 4 anecdote into a family of anecdotes.
- Route 6 (timeframe shift): The horizon is one night by construction; no shift applies.
- Route 7 (proxy-data): Proxy: the in-sample split is the proxy and it cannot decide (every t below 1.3); the forward tag accrual is the non-proxy route.
- Route 8 (conditioner): CONVERTED: busy/quiet estate-calendar tag on the on_falsifier_tracker.py accrual, read as a split at about 26 close dates, never a gate (the sign forbids gating on the hypothesis).
- Route 9 (fade): Fade would mean gating against busy nights, the opposite error on the same n; rejected with the gate.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing. Row P2-B3-02.
Sole remainder: Accrual from 8 to about 26 close dates.

## P2-B3-03: Anti-Focus residue (AA119) (register[89])
Numbers: +4.31bp at t 2.58, a quarter of the Focus premium, among the unwatched (non-Focus) panel names.
Routes before tonight: Surfaced in the reexamination tail below the revised table cut; no forward check was named before tonight. This batch supplies the missing check.
- Route 1 (desk-shares): Single-name desk-shares: rejected on power; a quarter-size premium spread over many names is not a single-name claim, and no single residue name carries a t of its own in the record.
- Route 2 (book-options): Book-options: closed by the same arithmetic as CONV-01's options test (one night of drift against option spread and theta), at quarter size the case is worse; not re-run, the analogy and its numbers are in CONV-01's row.
- Route 3 (basket): CONVERTED: equal-weight overnight shadow basket of all non-Focus panel names, membership rule anti-join with Focus 29 (a name entering Focus leaves the same night), graded on the print basis to the CONV-01 session-60 freeze, falsifier mean net of 5bp at or below 0.
- Route 4 (pair): Pair vs the Focus basket is the discipline read and it prints inside the same accrual (residue vs Focus at each read); it is a comparison, not a traded pair, because both legs are long overnight.
- Route 5 (variation): No variation: the basket as specified is already the loosest honest form of the claim.
- Route 6 (timeframe shift): One night is the claim's horizon; the intraday leg of the complex measured worthless in the C01 exam (Sharpe 0.01) and is not revived here.
- Route 7 (proxy-data): Proxy: bar-basis in-sample +4.31bp is the proxy read; the print-basis forward accrual is the deciding route, per the CONV-05 companion method.
- Route 8 (conditioner): As a conditioner it would gate C01 on attention, which is the story it exists to discipline; rejected as a gate, kept as a basket.
- Route 9 (fade): Fade (short the residue overnight) contradicts the measured sign (+4.31bp long); not runnable.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing (on_falsifier_tracker.py companion basket). Row P2-B3-03.
Sole remainder: 60 counted forward sessions on the print basis; the residue basket's auction cost is unmeasured and the 5bp standard is the planning figure.

## P2-B3-04: aster_etf_drift1_c098 (single-fill lead) (register[90])
Numbers: Newly INDICATIVE, n 1: excess +72.0 / +177.1 / +98.8bp at fwd1 / fwd3 / fwd5; fwd5 raw -54.7bp.
Routes before tonight: The UNBLOCK-1 reprice that printed the single fill. No check was named.
- Route 1 (desk-shares): CONVERTED: FWD_GRADE arm on the sleeve's own live stream (sleeves.json id aster_etf_drift1_c098, verified on the roster tonight), grade_n 10, decisive fwd5, falsifier non-positive fwd5 excess retires the lead.
- Route 2 (book-options): Book-options: the underlying is an ETF sleeve stream with one fill; no options form was priced and none is needed to grade the shares claim, which is prior in the mandated order and sufficient.
- Route 3 (basket): Basket: pooling it with its sibling aster_etf_drift1_m150 would grade a different stream; the lead names the c098 variant specifically, so it grades alone.
- Route 4 (pair): Pair: no pair claim exists in the record.
- Route 5 (variation): Variation: none authored; a single fill does not support designing a loosened form.
- Route 6 (timeframe shift): Horizons 1, 3, 5, 10 all print in the arm; decisive fwd5 as the record's own profile dictates, with the raw-vs-excess sign conflict on the face.
- Route 7 (proxy-data): Proxy: the PF or research-store series is the historical basis only under the grader registry's note; the arm grades live fills, the non-proxy route.
- Route 8 (conditioner): Conditioner: nothing to condition; it is an entry stream, graded directly in route 1.
- Route 9 (fade): Fade: inversion of a one-fill stream is not a form; the grader prints inversion profiles in replay machinery, not as an armed fade.
Final state: CONVERTED, SHADOW-ARMED, wire grader-config-addition. Row P2-B3-04.
Sole remainder: 10 resolved forward entries from Mon 2026-11-16.

## P2-B3-05: aster_saty_research exits precede large rises (register[91])
Numbers: 35 exit fills priceable at every horizon, realized mean -119.9bp, post1 excess +634.9bp (clustered t 1.36), post5 +2,818.9bp (t 4.06), post10 +2,303.8bp (t 17.04), 34 of 35 exits followed by a 5-session rise (cut share 0.971), on only 3 exit dates.
Routes before tonight: The VEIN3 dig and its registered forward exit-timing log (next 20 priceable exits, dual falsifier on mean and cut share).
- Route 1 (desk-shares): The sleeve already trades on the desk (roster id aster_saty_research, verified tonight); a new shares sleeve duplicating it is a second source of truth and was not created.
- Route 2 (book-options): Book-options: buying calls on each exited name is an expression of the same claim at option spreads; not priced tonight, and the shares-basis shadow grade is prior and decides whether any expression is worth pricing.
- Route 3 (basket): Basket: pooling its exits with all sleeves' exits is register[86]'s object, graded separately there; this row keeps the sleeve-specific claim the record registers.
- Route 4 (pair): Pair: no second leg is claimed.
- Route 5 (variation): Variation: a loosened exit-delay form (hold 10 sessions) already prints as the post10 split of the same overlay; no separate variation id is needed for a horizon split.
- Route 6 (timeframe shift): Horizons post1, post5, post10 all carried; post5 decisive per the registered falsifier.
- Route 7 (proxy-data): Proxy: the 3-exit-date in-sample read is the proxy and its concentration is the limiting number; the forward exit stream is the deciding route.
- Route 8 (conditioner): CONVERTED: shadow hold overlay on the sleeve's forward exits via exit_why_grader.py, grade count 20 priceable exits, falsifier mean post5 at or below 0 or cut share at or below 0.50.
- Route 9 (fade): Fade (exit even earlier) is the sleeve's own live behaviour being graded, not a new form.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing. Row P2-B3-05.
Sole remainder: 20 priceable forward exits, with the distinct exit-date count printed beside the grade (the in-sample flaw was 35 exits on 3 dates).

## P2-B3-06: bta_onebar_qqq (Program B near-candidate) (register[92])
Numbers: 2 own closes, expectancy -$150.25 per close, win rate 0.0; one close short of the 3-close LIVE CANDIDATE bar.
Routes before tonight: Program B's recheck named the third close as the decision. CONV-13 converted the sibling bta_onebar_rth as an own-record grade; the QQQ sleeve had no row.
- Route 1 (desk-shares): CONVERTED: FWD_GRADE arm on the sleeve's own close stream (roster id bta_onebar_qqq, verified tonight, beside bta_onebar_rth and bta_onebar_basket), interim candidacy read at close 3, full grade at 10 closes, decisive fwd5.
- Route 2 (book-options): Book-options: a one-bar QQQ sleeve's options form is a different object (0DTE expression pricing is its own program); not the claim registered here.
- Route 3 (basket): Basket: bta_onebar_basket exists on the roster as its own sleeve; pooling the QQQ sleeve into it would erase the per-sleeve candidacy question Program B posed.
- Route 4 (pair): Pair vs bta_onebar_rth prints as context (the siblings' records side by side) but CONV-13 already owns the RTH grade; no pair trade is specified.
- Route 5 (variation): Variation: none; loosening a 2-close negative record manufactures hope, not a form.
- Route 6 (timeframe shift): Timeframe: the sleeve is one-bar by definition; shifting the bar redefines the sleeve, which is a desk-lane act, not a conversion.
- Route 7 (proxy-data): Proxy: none needed; the sleeve's own closes are the data and they accrue live.
- Route 8 (conditioner): Conditioner: nothing to condition; it is a standalone sleeve graded on its own record, the CONV-13 pattern.
- Route 9 (fade): Fade: inverting a sleeve with expectancy -$150.25 on n 2 is the classic small-n trap; the inversion gets its evidence only if the forward grade confirms the negative expectancy at n 10, at which point a fade registration can be written with a real base rate. Named as the conditional next step, not armed tonight.
Final state: CONVERTED, SHADOW-ARMED, wire grader-config-addition. Row P2-B3-06. The negative record is on the face of the row; conversion here means the candidacy question is graded, not that an edge is claimed.
Sole remainder: Forward closes: 1 to the candidacy bar, 10 to the full grade.

## P2-B3-07: C03 Session-segment shape (midday leg) (register[93])
Numbers: Lane 3 (21 large caps x 14 sessions): overnight +15.6bp, open drive +11.7bp, midday -28.9bp at 43% win rate, close hour -7.8bp, full intraday -24.8bp. Lane 9: midday pooled -33.69bp, pooled t -3.73, night-clustered t -1.53; Focus-6 midday -81.63bp pooled, session t -1.82, 13 sessions. Held-tape (KG-4): OPEN_DRIVE mean +18.4bp win 0.682 (n 1,546, 52 clusters), MIDDAY mean -34.2bp win 0.257 (n 1,613, 54 clusters), CLOSE_HOUR -2.3bp win 0.485, OVERNIGHT -16.8bp win 0.579 on that tape's basis; seat lens mean 0.756.
Routes before tonight: Lane 3's shape read, Lane 9's widening, KG-4's phase decomposition, and the folded check (Lane 3's H-D segment grading plus a held-session segment log); the panel re-run at about 20 study nights and the A6 placebo sleeves were registered as the check. No direct falsifier of its own existed.
- Route 1 (desk-shares): Long shares over the full intraday session: priced by the record itself, full intraday -24.8bp; the long form of the whole session fails on the object's own numbers.
- Route 2 (book-options): Book-options: not run fresh; set aside by the CONV-01 options arithmetic (short-dated expressions against a 29 to 34bp segment move pay the spread and theta stack that closed the overnight options route on 38 of 38 costings). Recorded as an analogy with its source, not as a fresh price.
- Route 3 (basket): Basket: the claim is over the estate basket by construction (21 large caps, then the Focus panel); the converted form trades the basket, inside route 5.
- Route 4 (pair): Pair (long open drive vs short midday) doubles the cost stack and the open-drive leg is already owned by the held-tape sleeves; the midday leg alone is the unowned claim, so the pair was set aside.
- Route 5 (variation): CONVERTED with route 6: new shadow sleeve b3_midday_fade_var, short the Focus 29 basket over the midday segment only, own id, own falsifier, parents untouched; segment boundaries copied from KG-4 at wiring time.
- Route 6 (timeframe shift): CONVERTED jointly with route 5: the timeframe shift is the conversion (from a whole-session shape to a segment-only short).
- Route 7 (proxy-data): Proxy: pooled t -3.73 is the proxy-grade read; the night-clustered t -1.53 is why no stronger form was armed, and the forward 20-night panel is the deciding route.
- Route 8 (conditioner): Conditioner (gate intraday sleeves by segment) would edit how armed sleeves trade intraday; the rails forbid changing existing sleeve logic, and a gate is a logic change wearing a conditioner label. Rejected on the rails, named here.
- Route 9 (fade): The converted form IS the fade of the midday segment; a further fade of the fade is the long form priced and failed in route 1.
Final state: CONVERTED, SPEC-READY, wire desk-arming-specified (new shadow sleeve; not a grader arm and not an existing instrument, so it does not claim SHADOW-ARMED). Row P2-B3-07.
Sole remainder: 20 forward study nights plus the A6 placebo run, early December 2026 per the registered check.

## P2-B3-08: C04 Ledger vs Surface (register[94])
Numbers: Design sample 34,822 graded predictions; widest ledger-minus-surface spreads ACHC +14.69, ADEA +11.81, AAOI +10.79 points; sealed held-out slice 9,491 rows.
Routes before tonight: The census and reexamination reads; the one-shot held-out grade on Thu 2026-11-19 under the Lens (T1 to T8) was registered and is still ahead.
- Route 1 (desk-shares): Desk-shares: considered and recorded as the losing route in the row; the claim is that the options surface is wrong, and a shares trade tests the ledger's absolute accuracy instead. Kept as the named fallback if the grade passes on direction but options cannot be priced inside the stress budget.
- Route 2 (book-options): CONVERTED, gated: book options on the widest forward spread names, direction by the sign of ledger minus surface, Amendment 16 stress-loss sizing, arming only after a passing 2026-11-19 held-out grade; first 10 resolved expressions at or below 0 net retire the traded form.
- Route 3 (basket): Basket: a basket of all wide-spread names dilutes the claim, which lives in the widest spreads; the row takes the widest names per cycle instead.
- Route 4 (pair): Pair (long ledger-favoured vs short surface-favoured names) is a shares pair and inherits route 1's objection; not specified.
- Route 5 (variation): Variation: none; loosening the spread threshold before the held-out grade would spend the sealed slice's honesty.
- Route 6 (timeframe shift): Timeframe: the forecast horizon is part of the ledger's own record; the expression takes the nearest listed expiry at or beyond it, as specified in the row.
- Route 7 (proxy-data): Proxy: the design sample is the proxy and it is exactly what the sealed slice exists to overrule; no proxy grade is quoted.
- Route 8 (conditioner): Conditioner (gate book entries by ledger-minus-surface) is a real second use and is named as the fallback if the traded form's costing fails: the same grade, applied as an entry conditioner on existing book sleeves, would be a separate row written after 2026-11-19, not a silent substitution.
- Route 9 (fade): Fade (trade with the surface against the ledger) is the null hypothesis of the grade, not a form; if the grade shows the surface right, the object retires, it does not flip.
Final state: CONVERTED, SPEC-READY, wire book-arming-specified. Row P2-B3-08.
Sole remainder: The dated grade itself: sealed held-out slice, 9,491 rows, Thu 2026-11-19.

## P2-B3-09: C09 Oversold bounce complex (register[95])
Numbers: RSI=OS fwd5 +521bp, t 3.09, on 4 nights; pair RSI=OS x MACD=BEAR- +527bp; BH q 0.69 and 0.715; reexamination q 0.69 to 0.715 on 8 independent nights (4 at the fwd5 horizon).
Routes before tonight: The census panel read; the record's own state says WIRED, with the registered washed-out form CAND-WASH-01 as the accrual vehicle, and the K2 family arbitration (one family, shared falsifier) named in the register. CAND-WASH-01 is not a desk sleeve id (verified against sleeves.json tonight); it is a registered research form, so this row's wiring is a desk-arming act, not a grader addition.
- Route 1 (desk-shares): Single-name shares: rejected on deflation; the claim is a panel state and a single name inherits q 0.69 at worse power.
- Route 2 (book-options): Book-options: the book already carries C11, the Triple-RSI dip overlay (CONV-16, SHADOW-ARMED), which is this family's options expression; a second options form from the same nights would double-count the family, which the K2 arbitration exists to prevent.
- Route 3 (basket): CONVERTED: the washed-out panel basket in the CAND-WASH-01 form, long the in-state Focus panel names at the close, hold 5 sessions, equal weight, paper shadow, graded once as the K2 family at 20 accrued nights.
- Route 4 (pair): Pair: no pair claim; the RSI=OS x MACD=BEAR- cell prints as a split of the same accrual, not a pair trade.
- Route 5 (variation): Variation: the four parameterisations (C09 panel, CAND-WASH-01, C11, D3) are the variations, and the family grade replaces authoring a fifth.
- Route 6 (timeframe shift): Timeframe: fwd5 is the claim's horizon in every read; kept.
- Route 7 (proxy-data): Proxy: in-sample q 0.69 to 0.715 is the proxy verdict (indistinguishable from the best of thousands of nulls); the forward panel re-run is the deciding route.
- Route 8 (conditioner): Conditioner: as a gate on other sleeves it would spend the same nights four ways; the family basket is the honest single use.
- Route 9 (fade): Fade (short oversold states) contradicts the measured sign at fwd5; not runnable.
Final state: CONVERTED, SPEC-READY, wire desk-arming-specified. Row P2-B3-09.
Sole remainder: Accrual from 4 eligible fwd5 nights to 20 accrued nights, graded once as the K2 family.

## P2-B3-10: C1 buy panic, hedge reassurance (register[96])
Numbers: Claimed only, unverified: delayed hedge beat immediate in all three partitions at 72h, all incremental bootstrap intervals include zero, 12 inherited policies; claimed 72h delayed means 2.169 / 2.362 / 3.539 percent.
Routes before tonight: Both audit and rebuild routes blocked in the six-constructions program; unblockers named in the record (Astra prototype artifacts, or BTC spot 4h bars plus BTC perpetual 4h bars plus BTC perpetual funding prints). The registered check is fresh-data grading after 20 qualifying pooled events at 72h, or 6 months after the first live asset feed, whichever later.
- Route 1 (desk-shares): Not runnable: no desk shares surface expresses a BTC hedge-timing construction, and the book is options only.
- Route 2 (book-options): Not runnable: no BTC options chain is reachable through any book instrument on this box.
- Route 3 (basket): Not applicable: a two-asset timing rule has no basket form.
- Route 4 (pair): Not runnable: the pair's second leg runs under 12 inherited policies whose definitions are not in held records; the policies are part of the missing artifact.
- Route 5 (variation): Designed and rejected: a spot-only delayed-hedge variation deletes the funding leg, half the mechanism; a variation must keep the parent's signal, so this would be an invention, not a variation.
- Route 6 (timeframe shift): The claim is stated at 72h in all three partitions; shifting grades a different claim.
- Route 7 (proxy-data): Strongest lawful proxy (Kraken spot BTC tape) can decide the price-path half only; it cannot decide funding carry, so a proxy verdict would grade a different object. Printed as the reason the proxy route does not convert this object.
- Route 8 (conditioner): Not runnable: no armed panic-hedge sleeve exists for this to gate.
- Route 9 (fade): The fade (immediate hedging) is one arm inside the claim itself, with intervals also including zero; not an independent form.
Final state: EXHAUSTED. STUBBORN: claimed-only object whose decisive inputs (BTC perpetual bars and funding prints, or the Astra artifacts) do not exist on this box, and whose own intervals include zero, so no honest form can be armed and none can be killed.
Sole remainder: BTC perpetual 4h bars plus BTC perpetual funding prints (with BTC spot 4h bars), or Astra's prototype artifacts landing: the record's own named unblockers.

## P2-B3-11: C12 Forecast midday slot (register[98])
Numbers: 90.2% hit, n 61 (55 of 61), excess +15.57pp, z 2.79, BH q 0.188 over a 128-cell family; no mechanism claimed.
Routes before tonight: The census entry held it at WATCH on q 0.188 and re-grading correlation; the folded check (20-grading-day re-grade with as-written and final-revision grades side by side) was registered.
- Route 1 (desk-shares): Not runnable: a hit-rate cell on forecast calls is not an entry signal; no shares form exists without inventing a mechanism the record explicitly does not claim.
- Route 2 (book-options): Not runnable for the same reason: no options expression of a slot-level hit rate exists.
- Route 3 (basket): Basket: no basket is named by the cell.
- Route 4 (pair): Pair: no pair is named.
- Route 5 (variation): Variation: loosening the slot window would multiply cells inside a 128-cell family whose q is already 0.188; rejected as family inflation.
- Route 6 (timeframe shift): The slot IS a timeframe object; its forward re-grade is the timeframe test, carried in route 8.
- Route 7 (proxy-data): Proxy: the final-revision grade is the contaminated proxy (re-grading correlation); the as-written grade printed beside it is the control, built into the decisive test.
- Route 8 (conditioner): CONVERTED: confidence-ordering conditioner on the book's forecast calls (tag only, no sizing), decisive test the registered 20-grading-day re-grade with as-written and final-revision grades side by side; falsifier forward excess at or below 0, or the as-written grade erasing the excess.
- Route 9 (fade): Fade (distrust midday calls) is a sizing act on an unseparated cell (q 0.188); the conditioner must earn separation before any fade or boost is lawful.
Final state: CONVERTED, SPEC-READY, wire book-arming-specified (tagging wiring in the book grading entry). Row P2-B3-11.
Sole remainder: 20 forward grading days of tagged calls.

## P2-B3-12: D-10 ATS weekly z surface, recovered series (register[100])
Numbers: Recomputed z matches stamped z to 4 decimals for all 8 fires symbols, z_matches_stamp true 8 of 8, 28 to 30 usable weeks per symbol. No edge was graded on this surface in Wave 4.
Routes before tonight: The Wave 4 recovery itself (artifact v6_ats_series.json, source label finra-ats-weekly-z26-reconstruction). No forward check was named.
- Route 1 (desk-shares): The surface's natural shares hosts already trade: the four s_q07w ATS sleeves are on the roster (verified tonight). A new shares sleeve built on the z surface alone would invent the directional claim Wave 4 did not grade.
- Route 2 (book-options): Book-options: no options claim exists for a weekly dark-pool z state; not priced, and route 8 grades the surface's predictive content first and cheaper.
- Route 3 (basket): Basket: the 8 fires symbols as a z-ranked basket was designed and set aside (see route 4).
- Route 4 (pair): Pair (long high-z vs short low-z fires symbols, weekly): designed in full and recorded as the losing route; it manufactures a direction from a data-recovery artifact. It becomes writable only if the route 8 conditioner split separates, at which point it is a new registration with a real base rate.
- Route 5 (variation): Variation: none; there is no parent trade form to vary.
- Route 6 (timeframe shift): Timeframe: weekly is the series' own cadence (FINRA ATS weekly); kept, with fwd5 as the grading horizon inside the week-ahead window.
- Route 7 (proxy-data): Proxy: the stamped z was itself the proxy under audit; the recomputation to 4 decimals on 8 of 8 is the provenance proof, and the forward split is the deciding route for any trading content.
- Route 8 (conditioner): CONVERTED: FWD_GRADE arm on the four live ATS sleeves with the weekly ATS z tercile as the recorded conditioner split, grade_n 20 pooled resolved entries, decisive fwd5, falsifier top-minus-bottom tercile spread at or below 0.
- Route 9 (fade): Fade: no sign exists to fade; the surface has never carried a directional grade.
Final state: CONVERTED, SHADOW-ARMED, wire grader-config-addition. Row P2-B3-12.
Sole remainder: 20 resolved forward parent entries with a joined z week, plus the weekly FINRA ATS refresh that extends the recovered series.

## P2-B3-13: Early Globex segment conditioner (register[101])
Numbers: ES split +192.41bp (up segment nights +45.63bp, n 21, t 0.741; down nights -146.77bp, n 18, t -1.878); NQ split +110.41bp; 39 of 48 window nights covered.
Routes before tonight: NEW-DATA-BUILDS registered the nightly accrual read at 60 forward nights, on the same accrual as futures drift, and stated the segment cannot gate cash entry.
- Route 1 (desk-shares): Not runnable: the segment is a futures-session state, and the desk has no futures surface (the CONV-60 verdict); a shares trade on the tag alone would be a gate, which the record forbids at this strength.
- Route 2 (book-options): Book-options: CONV-60 priced the index options form of the overnight drift family and it returned negative at the touch on held quotes (-6.13bp long call, -2.48bp spread on the capture window); a conditioner-strength signal does not revive it.
- Route 3 (basket): Basket: the basket it conditions (Focus overnight) exists as CONV-01; no second basket.
- Route 4 (pair): Pair: ES vs NQ segment disagreement is a sub-split of an n 39 read with no separating cell; not a pair.
- Route 5 (variation): Variation: widening the segment window (16:00 to 20:00 ET) was not authored; the registered window is 16:00 to 18:00 ET and changing it forks the accrual the record already started.
- Route 6 (timeframe shift): The read point is fixed at 60 forward nights by the record; kept.
- Route 7 (proxy-data): Proxy: the in-sample split is the proxy (t 0.741 and -1.878, no cell separates); the forward tag accrual is the deciding route.
- Route 8 (conditioner): CONVERTED as a tag only: Globex segment sign joined to the on_falsifier_tracker.py accrual, split printed beside the CONV-01 verdict, falsifier at 60 forward nights (split at or below 0, or absolute night-clustered t below 2). Never a gate under this row.
- Route 9 (fade): Fade: trading against down-segment nights is the gate in reverse; forbidden by the same record sentence.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing. Row P2-B3-13.
Sole remainder: 60 forward nights of accrual (in-sample coverage was 39 of 48 window nights).

## P2-B3-14: EMA stack bear_below A06 (register[102])
Numbers: 9 of 9 hits, rate 1.0 vs base 0.6567, excess +34.33pp, z 2.169, BH q 0.4713.
Routes before tonight: PASS2-B named the mechanism (A06 mechanical on every symbol call under tags) and the check (re-grade at 20 forward bear_below rows). The Forward Grading Protocol class P1 already carries A06 in its 11-axis tag set with wired step-13 accrual.
- Route 1 (desk-shares): Not runnable: a forecast posture accuracy cell is not an entry signal.
- Route 2 (book-options): Not runnable: no options expression of a posture tag exists; sizing book entries by an unseparated tag (q 0.4713) would be authority the numbers do not carry.
- Route 3 (basket): Basket: no basket is named by the cell.
- Route 4 (pair): Pair: A06 pairs and triples grade inside protocol class P1 at their own floors (pairs about 15 nights, triples 60 to 80 nights); they are the protocol's business, not a separate conversion.
- Route 5 (variation): Variation: other posture states (the non-bear_below cells) are separate cells of the same class, graded by the same sitting; no variation id is authored for one cell.
- Route 6 (timeframe shift): Timeframe: the tag is per-call; no shift applies.
- Route 7 (proxy-data): Proxy: the 9-row in-sample read is the proxy; the protocol's forward rows are the deciding route, and the two evidence classes are never merged under the protocol's standing rule 1.
- Route 8 (conditioner): CONVERTED: the protocol class P1 arm named as this object's forward check (step-13 tag accrual, mechanical A06 on every symbol call), grade count 20 forward bear_below rows, falsifier excess at or below 0 at that count.
- Route 9 (fade): Fade (discount calls made under bear_below posture, the usual prior the record says this runs opposite to) is a sizing act on a q 0.4713 cell; rejected until the forward grade separates.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing (the Forward Grading Protocol is the named existing instrument, class P1 accrual wired). Row P2-B3-14.
Sole remainder: 20 forward bear_below rows under the step-13 accrual.

## P2-B3-15: ema_vwap (small-n lead) (register[103])
Numbers: Newly INDICATIVE, n 2, 1 date: fwd5 +1,535.4bp raw, excess +2,034.1bp.
Routes before tonight: The UNBLOCK-1 reprice printed it at its n. No check was named.
- Route 1 (desk-shares): CONVERTED: FWD_GRADE arm on the sleeve's own live stream (roster id ema_vwap, verified tonight), grade_n 10, decisive fwd5, falsifier non-positive fwd5 excess retires the lead.
- Route 2 (book-options): Book-options: a sibling sleeve ema_vwap_options exists on the roster and is a distinct object with its own record; borrowing its form or record for this lead would blend two objects. Named and not used.
- Route 3 (basket): Basket: pooling two fills into a basket grades the basket, not this sleeve; rejected.
- Route 4 (pair): Pair: no pair claim exists.
- Route 5 (variation): Variation: none authored on n 2.
- Route 6 (timeframe shift): Horizons 1, 3, 5, 10 print in the arm; fwd5 decisive as printed in the lead.
- Route 7 (proxy-data): Proxy: none needed; live fills are the data.
- Route 8 (conditioner): Conditioner: an entry stream, graded directly in route 1.
- Route 9 (fade): Fade: inverting a 2-fill, 1-date lead is not a form.
Final state: CONVERTED, SHADOW-ARMED, wire grader-config-addition. Row P2-B3-15.
Sole remainder: 10 resolved forward entries from Mon 2026-11-16.

## P2-B3-16: ENJ funding-squeeze family counter-cyclical condition (10 sleeves, no-fire) (register[104])
Numbers: 10 sleeves fired zero times; the conjunction (funding below 0 AND a 20-bar breakout close) occurred 0 times in 420 eval bars; funding negative on 74 bars, breakouts on 20, zero overlap; ENJ fell from $0.0276 to $0.0190 (KG-6, hand-recounted against both engines' entry definitions).
Routes before tonight: KG-6 cured the ENJ class's data route (Kraken public OHLC, 720 complete 4H bars, HTTP 200; funding via OKX ENJ-USDT-SWAP history after Binance 451 and Bybit 403) and graded all 22 ENJ sleeves in replay; the squeeze family's forward check was named as free (the first live occurrence is the test). CONV-27 converted the sibling ENJ breakout stream as an intent-based shadow arm, BLOCKED-ON-WIRING on the ENJ feed. The 10 parents were verified on the roster tonight: aster_enj_nfs_fixed96_vol, aster_enj_nfs_lost_full, aster_enj_nfs_lost_vol, aster_enj_nfs_norm_full, aster_enj_nfs_norm_vol, aster_enj_nfs_normfail_full, aster_enj_nfs_normfail_vol, aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash, aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct, aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash.
- Route 1 (desk-shares): CONVERTED in the intent form: fills can never exist (ENJ/USD unlisted at the broker, 42210000 asset-not-found, entries fail closed by name), so the CONV-27 intent-shadow form is the desk-shares route for this family: dispatcher intents priced at the Kraken tape close, pooled as one stream, decisive fwd5, grade_n 10.
- Route 2 (book-options): Book-options: no ENJ options chain exists on any book instrument; not runnable, and unnecessary: the intent grade decides the family first.
- Route 3 (basket): Basket: the family already IS the basket (10 sleeves, one conjunction); pooling them as one stream is done inside route 1, per the CONV-27 convention for sizing variants.
- Route 4 (pair): Pair vs the ENJ breakout stream (CONV-27) prints as context (the breakout fired 11 times while the squeeze fired 0, the counter-cyclical anatomy in one line); no pair trade is specified, because the squeeze leg has never occurred.
- Route 5 (variation): Variation: explicitly NOT authored. Loosening the conjunction (funding below 0 OR breakout, or a wider breakout window) to manufacture fires is the exact act the gutting doctrine and the non-firing-sleeve doctrine forbid as a cure: the route changes (the feed), the signal stays. If a loosened form is ever wanted, it registers as a new variation beside these parents, and tonight's row names that as a future act, not a conversion.
- Route 6 (timeframe shift): Timeframe: the 20-bar breakout on the sleeves' own 4H basis is the registered definition; kept verbatim.
- Route 7 (proxy-data): Proxy-data: the replay tape (KG-6) is the proxy evidence and it is already spent: it proved the condition never occurred, which is a fact about the tape, not a grade of the trade. The forward live tape is the deciding route.
- Route 8 (conditioner): Conditioner: the family is itself a conjunction looking for its first occurrence; conditioning another sleeve on a state that has never occurred gates on a null. Not runnable.
- Route 9 (fade): Fade: there is no fire to fade and no sign to invert; the counter-cyclical reading is an anatomy, not a short signal. Not runnable.
Final state: CONVERTED, SHADOW-ARMED (proposed grader-config addition in the CONV-27 arm form), arms the moment the ENJ feed lands. Row P2-B3-16. Dependency named exactly: ENJ-FEED-CONV27-20261115, the Kraken ENJ/USD tape plus funding prints being landed tonight by the sibling feed lane; until it lands the arm is dormant by name, not dead.
Sole remainder: The feed landing, then the first live occurrence of the conjunction (the family's first-ever test), then 10 resolved shadow entries. A 120-forward-day no-occurrence read prints ACCRUING-NO-OCCURRENCE and does not kill.

## P2-B3-17: F13 G8 (registered, ID-only) (register[105])
Numbers: NUMBERLESS in the master list and in the reexamination greps; remainder seat P 0.00 / N 0.94, panel lens vector max 0.05, min 0.03. No mechanism at this granularity.
Routes before tonight: The record's own forward check is the Round-2 rotation triage, a definition hunt. A seat surprise fire against it is on the record and does not supply a definition.
- Route 1 (desk-shares): Not runnable: no signal definition exists to express in shares.
- Route 2 (book-options): Not runnable: no underlying, direction or horizon is stated anywhere in held records.
- Route 3 (basket): Not runnable: no membership rule exists; a basket cannot be formed from an ID.
- Route 4 (pair): Not runnable: no legs are named.
- Route 5 (variation): Not runnable under the gutting rule: a variation requires the parent verbatim, and there is no parent definition to keep verbatim; authoring one would invent the object.
- Route 6 (timeframe shift): Not runnable: no timeframe is stated to shift from.
- Route 7 (proxy-data): Strongest lawful proxy is the seat and lens remainder (P 0.00 / N 0.94, lens max 0.05, min 0.03): a judgement about the object, usable to rank it in a triage queue, unable to decide any trade form. Printed as the proxy route's exact limit.
- Route 8 (conditioner): Not runnable: a conditioner needs a host sleeve and a stated conditioning variable; neither exists.
- Route 9 (fade): Not runnable: there is no sign to fade.
Final state: EXHAUSTED. STUBBORN: ID-only registration; the missing object is a definition, not a price, a feed or a grade, and no route manufactures a definition honestly.
Sole remainder: The F13 G8 signal definition (mechanism and membership rule) from its registering lane, due at the Round-2 rotation triage.

## P2-B3-18: FCEL single-name overnight standalone (register[106])
Numbers: Print legs mean +28.22bp, median +80.21bp, standard deviation 477.40bp, t 0.19, 5 of 10 positive; auction cost median +46.39bp; against full-history gross +42.03bp the sign flips by estimator; about 516 sessions needed for a standard error of half the gross.
Routes before tonight: Wave 6 cell 7 registered the standalone as a 500+ session question. CONV-06 converted the single-name clearers as a basket accrual, and tonight's routes ledger amendment (ON-FALSIFIER-SPEC.md, Amendment 2026-11-15) ruled FCEL outside the print population: no per-name print line, standing rides the basket accruals. Verified tonight: no FCEL position in Midna's book ledger (0 occurrences) and no FCEL standalone sleeve on the desk roster.
- Route 1 (desk-shares): Standalone shares: priced and failed with numbers: cost median +46.39bp against full-history gross +42.03bp is net negative at the median, the mean-based read (+28.22bp print legs) is worse, and t 0.19 on a 477.40bp standard deviation cannot grade in 60 sessions (516 needed). Not armed in any form.
- Route 2 (book-options): Book-options: closed by the CONV-01 options test family (38 of 38 costings failed on the five carry names; a one-night drift against weekend theta), and FCEL's leg variance (477.40bp) makes its options case worse, not better. Analogy with source named, not re-run.
- Route 3 (basket): CONVERTED: basket membership only, in the two already-armed baskets that already carry it: CONV-01 Focus (FCEL is a Focus 30 name) at basket weight, and the CONV-06 clearers accrual for its standing. No standalone sizing is created.
- Route 4 (pair): Pair: no partner with a stated basis exists in any held record; a pair invented to rescue a failed standalone would be a new object, not a conversion.
- Route 5 (variation): Variation: a half-weight standalone is a sizing change on a cost-negative expectancy; variation doctrine governs signal forms, not a smaller bet on a priced failure. Not authored.
- Route 6 (timeframe shift): Timeframe: the intraday leg of the overnight complex measured worthless (Sharpe 0.01) in the C01 exam; a multi-night hold is a different claim with no read in the record. Not runnable from held evidence.
- Route 7 (proxy-data): Proxy: the full-history bar gross (+42.03bp) is the proxy and the print legs overrule it (estimator sign flip); printed so the proxy number is never quoted alone.
- Route 8 (conditioner): Conditioner: FCEL as a conditioner on the basket (its median leg is +80.21bp) was considered; a conditioner needs a forward split with power, and 10 print legs give none. Its per-name legs already print inside the basket accrual, which is the honest version of this route.
- Route 9 (fade): Fade (short FCEL overnight): the median leg is +80.21bp long; fading trades against the median on a t 0.19 mean. Not runnable.
Final state: CONVERTED as a basket member, SHADOW-ARMED via the existing on_falsifier_tracker.py basket accruals (CONV-01 and CONV-06 arms, neither edited). Row P2-B3-18. STUBBORN as a standalone: cost-negative at the median and ungradeable inside 516 sessions; the standalone is not converted, not killed, and its 500+ session registration bar stands verbatim.
Sole remainder: The session-60 basket read for the membership; the standalone question reopens only as a 500+ session registration with power stated.

## P2-B3-19: Fetched 79-name universe overnight read (register[107])
Numbers: Fetched basket -1.34bp overnight (t -0.07) over 52 stored nights, no symbol at t 2 or above; SKYQ +111.92bp at win rate 0.327; ASPI +75.98bp, t 1.86; Focus names on the same 52 nights -28.12bp (halves +5.59 / -61.84).
Routes before tonight: VEIN1 registered the mechanism: desk cache accrues daily, first regrade of the fetched universe at 120 nights per name, a rerun of the VEIN1 script.
- Route 1 (desk-shares): Single-name shares for the two internal leads: rejected with numbers: SKYQ +111.92bp at win rate 0.327 is a carried-by-outliers profile, and ASPI t 1.86 is below the record's own t 2 naming bar; both accrue inside route 3 and promote only through its rule.
- Route 2 (book-options): Book-options: a null basket mean (-1.34bp) against option spreads and theta has no case; the CONV-01 options closure applies a fortiori. Not run.
- Route 3 (basket): CONVERTED: the 79-name equal-weight overnight shadow basket as the CONV-01 control basket and per-name accrual vehicle, legs recorded nightly on the per-name amendment basis, regrade at 120 nights per name by rerun of the VEIN1 script; promotion bar per name t at least 2 and mean net of 5bp positive; basket trade form retires if its 120-night mean net of 5bp is at or below 0, continuing as control.
- Route 4 (pair): Pair (fetched basket vs Focus basket) is the control comparison and prints inside the same accrual; it is not a traded pair because the same-window Focus leg is also negative (-28.12bp), so a spread trade would be long one null against another.
- Route 5 (variation): Variation: narrowing to a top-decile sub-basket on 52 nights would fit the window the record calls a window property; explicitly not authored.
- Route 6 (timeframe shift): Timeframe: one night is the claim; the halves split (+5.59 / -61.84 on Focus) shows the window, not a timeframe effect, dominates.
- Route 7 (proxy-data): Proxy: the 52-night read is the proxy verdict (a window null); the 120-night accrual is the deciding route, and the Focus same-window read is printed beside it so the null is never read as a universe property.
- Route 8 (conditioner): Conditioner: as a gate on CONV-01 (trade only when the fetched basket agrees) it would condition a proven complex (DSR 0.99994 on 2,229 sessions) on a 52-night null; rejected on sufficiency.
- Route 9 (fade): Fade (short the fetched basket overnight): mean -1.34bp at t -0.07 against auction costs is a negative-expectancy trade after any positive cost; not runnable.
Final state: CONVERTED, SHADOW-ARMED, wire book-instrument-existing (on_falsifier_tracker.py per-name accrual basis). Row P2-B3-19. Converted as control plus accrual vehicle, explicitly not as a return claim.
Sole remainder: Accrual from 52 to 120 nights per name on the daily desk cache.

## Batch totals
19 objects: 17 CONVERTED (P2-B3-01 to P2-B3-09, P2-B3-11 to P2-B3-16, P2-B3-18, P2-B3-19), 2 EXHAUSTED (P2-B3-10 C1, P2-B3-17 F13 G8), 0 ALREADY-TRADED (verified: no B3 object is a position in Midna's book ledger, and the objects that are live desk sleeves, aster_etf_drift1_c098, ema_vwap, bta_onebar_qqq, aster_saty_research and the ATS and ENJ parents, are converted as grades on their own streams, which is a conversion, not a pre-existing trade of the lead).
Converted by route (each converted row counted once, by its primary route): conditioner form 7 (P2-B3-01, P2-B3-02, P2-B3-05, P2-B3-11, P2-B3-12, P2-B3-13, P2-B3-14), basket form 4 (P2-B3-03, P2-B3-09, P2-B3-18, P2-B3-19), desk-shares FWD_GRADE on the object's own stream 4 (P2-B3-04, P2-B3-06, P2-B3-15, and P2-B3-16 in the intent-shadow form), variation plus timeframe shift 1 (P2-B3-07), book-options form 1 (P2-B3-08). Total 17.
Stubborn objects: P2-B3-10 (C1, missing decisive data set), P2-B3-17 (F13 G8, missing definition), P2-B3-18 (FCEL standalone, cost-negative at the median and 516 sessions to grade; converted only as a basket member).
STATUS: PARTIAL by the batch's own construction: 17 of 19 converted with complete rows, 2 exhausted with every route printed and one named external remainder each; every converted row's remaining proof is a dated forward accrual, a dated grade (2026-11-19), or a named feed landing (ENJ-FEED-CONV27-20261115). Evidence pointer: B3-rows.jsonl beside this file, verified by read-back count and JSON parse after writing.
