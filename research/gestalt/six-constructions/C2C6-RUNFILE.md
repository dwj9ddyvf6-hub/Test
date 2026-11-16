# C2/C6 Runfile: One Cell, One Liability Object, Two Holdings Contexts

Program: Six Constructions, Run 2
Cell: C2/C6 (a single cell, charged as one trial stream, with two holdings contexts)
Filed: Sun 2026-11-15, before any result, before the first production chain capture
Typed spend: $0.00
Experiment run tonight: none. This file is a pre-registration only.

## SCOPE

Surface: this runfile and the chain history inventory recorded in section 8. Nothing else changes.
Constraints: no experiment is run tonight; light compute only; the estate file desk/research/bilbo-options/iv_snapshot.py is never imported (it has no main guard and importing it re-runs a snapshot); no personal identifiers appear in this file; option-implied probabilities are never used as physical probabilities anywhere in this study.
Outcome: the band-liability study for constructions C2 and C6 is registered in full before data exists, so no later choice of universe, strike family, expiry family, estimator, comparator, or cost rule can be fitted to results.
Proof: this file, read back after writing, plus the inventory evidence in section 8 (paths, file counts, and date ranges taken from the estate itself tonight).
Edges: the chain source is the estate chain panel, whose production store does not exist yet. Its first production capture is Mon 2026-11-16. Every read date in this file is bounded by that fact.

## 1. The shared liability object

Both contexts sell the same call spread on the same terms:

- Sell one call at strike K1, buy one call at strike K2, K2 above K1, same expiry, same underlying, standard deliverable only.
- Liability at expiry, per share: L = min(max(ST minus K1, 0), K2 minus K1), where ST is the underlying settlement price at expiry.
- Executable credit, per share: c = bid of the K1 call minus ask of the K2 call, taken from executable quotes at the decision capture (section 4). Mid prices are never used as the credit.
- The claim under test, identical in both contexts: c exceeds E[L | I] plus all costs, where I is the information set archived at decision time and E[L | I] is a physical conditional expectation (section 5). Nothing risk-neutral enters the claim.

Because the liability object is one object, C2 and C6 are one cell. Their credits, liabilities, and outcomes are never counted as two independent streams and never presented as diversification of each other (section 9).

## 2. The two contexts

### C2: Sell the middle of the rebound (holdings context: long stock)

- Position: hold a recovery stock bought at S0. At the prespecified recovery stage (section 3), sell the call spread above and keep the stock.
- Terminal P and L per share, at expiry, before costs: ST minus S0 plus c minus max(ST minus K1, 0) plus max(ST minus K2, 0).
- The spread caps the stock above K2, keeps the stock return up to K1, and collects c against the band between K1 and K2. The liability being priced is exactly L above.

### C6: Price the squeeze tail (holdings context: no stock)

- Position: no stock. For a bearish-flagged name, sell the same call spread.
- Terminal P and L per share, at expiry, before costs: c minus L.
- The question is whether the market credit overpays for the physical right tail of a bearish-flagged name, where a squeeze is the loss case and the loss is capped at (K2 minus K1) minus c.

## 3. Decision point and recovery stage

- Decision timestamp: the close capture of the decision session. No intraday decision points.
- C2 recovery stage: the stage transition recorded by the flag source itself, under the flag definition in force at flag time (section 6). The archived flag governs. No stage definition may be re-derived, loosened, or re-timed after chain data arrives.
- C6 decision point: the first close capture on or after the session on which the bearish flag is archived.
- One decision per flag event. A name with no executable spread at its decision point is not re-shopped on later sessions under the same flag; it enters the missing-options cohort (section 7).

## 4. Chain source and executable credit

- Chain source for both contexts: the estate chain panel, collected by ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave4/v4_chain_panel.py (which reuses ~/workspace/terminal-lineup/site/collect_chains.py), run by cron chain-panel-close-capture, weekdays at 16:46 ET, inside the script-enforced 16:00 to 17:30 ET close window.
- Production store: ~/workspace/morgue/state/morgue/chains_panel/ with one canonical close snapshot per symbol per session at <SYM>/<YYYY-MM-DD>.json.gz, plus manifest.jsonl and iv_ledger_modelled.jsonl in the same directory.
- Panel: 31 symbols, the 29 Focus single names (SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, BE, OKLO, VST, CEG, XLE) plus SPY and QQQ as controls.
- First production capture: Mon 2026-11-16, the 16:46 ET run. As of tonight, Sun 2026-11-15, the production store directory does not exist and holds zero captures.
- Executable quotes: the snapshot rows carry OCC code, open interest, volume, and modelled IV only. Executable bid and ask live in the panel iv_ledger_modelled.jsonl rows (quote_bid, quote_ask, quote_mid per contract), which cover contracts inside the enrichment scope stated by the collector (expiries within 120 days of the snapshot day, moneyness inside the 0.75 to 1.25 band). The credit c is computed only from those quote fields: bid for the short K1 leg, ask for the long K2 leg.
- A contract outside the enrichment scope, or with a null or crossed quote, has no executable credit in this store. Any spread needing such a contract goes to the missing-options cohort. It is never priced from modelled IV and never priced from a mid.
- Modelled IV in either store is labelled MODELLED by the collector. It is an implied quantity. It may be reported as context, clearly labelled implied, and it never enters E[L | I] (section 5).
- Per-symbol manifest errors are named accrual losses, not silent skips. A symbol with a manifest error on its decision session goes to the missing-options cohort with that error as its reason code.

## 5. Liability estimator (physical, pre-registered)

- Identity: E[L | I] = integral from K1 to K2 of P(ST above k | I) dk. The liability is the area under the physical conditional right-tail curve over the strike interval. This identity, not any option price, defines the estimand.
- Estimation method class: historical conditional empirical distribution, fitted on development data only (section 6). For each development flag event, the forward return to the matching horizon is recorded; the conditional survival curve P(ST above k | I) is the empirical survival function of those forward outcomes, conditioned on the archived information set I (flag source and type, context, horizon to expiry, and the price and factor fields archived at decision time in the flag source, for example the night study factors.json fields). No field timestamped after the decision point may enter I.
- Discrete form: the integral is evaluated as a step sum over the listed strikes inside [K1, K2] on the decision chain, using the empirical survival value at each strike interval. The strike grid is the listed grid; no interpolation model is fitted.
- Pooling: the primary estimate pools flag events across names within a context, because single-name flag counts are small. Per-name estimates are reported alongside wherever the count allows, and a context with too few development events to form a survival curve is reported as ungradable yet, with its event count named, rather than graded on a curve borrowed from the other context. The two contexts keep separate conditioning: a recovery flag and a bearish flag are different information sets.
- Band: E[L | I] is reported as a band, not a point. The band is a percentile band from a cluster bootstrap over development events, clustered by underlying name, so repeated flags on one name are not treated as independent draws. The primary claim test uses the point estimate plus costs, exactly as stated in section 1. A secondary read, credit against the upper band edge plus costs, is named here in advance and reported alongside; it may not replace the primary read after results are seen.
- Hard rule: option-implied probabilities, implied volatilities, modelled IV, risk-neutral densities, and any inversion of option prices are never used as, converted into, or relabelled as the physical curve P(ST above k | I). If a number came from an option price, it is implied, and it stays labelled implied.
- Strike and expiry family selection: fixed on development data only. The family is defined by offsets from the decision spot (K1 as a moneyness offset, K2 as a width above K1, expiry as a horizon band), and the numeric offsets are locked in a dated development lock addendum to this runfile, written before the first read date in section 10 and derived only from the development archives in section 6 and their price history. Chain outcomes, credits, and liabilities from production captures may not be used to choose the offsets. Until that addendum exists, no spread in this study is specified and no read beyond coverage is lawful.

## 6. Development universes (estate sources, verified to exist tonight)

Development data means the estate's own archived calls and flags, all timestamped before the first production capture. No production chain outcome is development data.

### C2 development universe: flagged recovery names

A name enters when one of these sources records a recovery, beaten-down, capitulation, or ignition flag for it, under that source's own definition, with its archive timestamp:

- Night study archives: ~/workspace/goals/midna-trading-her-own-simulated-book/hidden_files/night-study-2026-11-04, night-study-2026-11-05, night-study-2026-11-06, night-study-2026-11-09, night-study-2026-11-10, night-study-2026-11-11, night-study-2026-11-12, and night-study-2026-11-13 (eight sessions, each holding factors.json and companion files).
- Beaten-down sleeve flag record: spec at ~/workspace/alpaca-swing-desk/desk/sleeves/beatendown/SPEC.md, ledger at ~/workspace/alpaca-swing-desk/beatendown_ledger.jsonl (5 rows tonight).
- Capitulation sleeve flag record: spec at ~/workspace/alpaca-swing-desk/desk/sleeves/capitulation/SPEC.md, ledger at ~/workspace/alpaca-swing-desk/capitulation_ledger.jsonl (97 rows tonight).
- Phoenix sleeve flag record: spec at ~/workspace/alpaca-swing-desk/desk/sleeves/phoenix/SPEC.md, pre-registration at ~/workspace/alpaca-swing-desk/desk/research/phoenix/PRE_REG_IGNITION.md.
- Resurrection research records: ~/workspace/alpaca-swing-desk/desk/research/resurrection/ (charters and pre-registrations for recovery constructions).
- Harvester records: ~/workspace/research_notes/decisions-api-leverage-20261114/runs/HARVESTER-RUN-1.md and ~/workspace/research_notes/decisions-api-leverage-20261114/wave2/harvester_dashboard_v1.json.

### C6 development universe: flagged bearish names

A name enters when one of these sources records a bearish, blowoff, or short-program flag for it, under that source's own definition, with its archive timestamp:

- Blowoff daily sleeve flag record: spec at ~/workspace/alpaca-swing-desk/desk/sleeves/blowoff_d/SPEC.md, ledger at ~/workspace/alpaca-swing-desk/blowoff_d_ledger.jsonl (43 rows tonight).
- Blowoff hourly sleeve flag record: spec at ~/workspace/alpaca-swing-desk/desk/sleeves/blowoff_1h/ (directory verified), ledger at ~/workspace/alpaca-swing-desk/blowoff_1h_ledger.jsonl (161 rows tonight).
- Short-program research records: ~/workspace/alpaca-swing-desk/desk/research/short-program/ including D23_BORROW_DATA_REQUIREMENTS.md, which governs borrow feasibility for the short comparator in section 7.
- Night study archives: the same eight night-study directories listed for C2, using their bearish flags as archived.
- Harvester records: the same two harvester paths listed for C2, using their bearish flags as archived.

### Coverage boundary

The chain panel covers only the 29 Focus names plus SPY and QQQ. A flagged name outside the panel has no chain source in this study. It stays in the development universe and in every coverage denominator, and it is reported in the missing-options cohort with reason code outside panel. The universe is never silently cut down to the panel.

## 7. Comparators, costs, and contract handling

### Identical endpoints and capital conventions (both contexts)

- Same decision timestamp, same expiry, same terminal price source for every comparator in a context: ST is the underlying daily close on the expiry date from the estate daily bars, the same bar source behind the night study factors.json files.
- Unit: one spread per 100 shares of reference stock. Results are reported per share, per unit, and per dollar of capital committed, with the same convention in every comparator.
- Capital committed: for C2, the stock purchase price S0 per share (the spread is an overlay on held stock; margin on the spread against held stock is reported as recorded by the executing venue and never assumed to be zero in the per-capital read). For C6, the spread capital is the maximum liability minus credit, (K2 minus K1) minus c, per share. For the C6 share short, capital is the margin the venue requires, recorded at decision time. For the C6 purchased put, capital is the premium paid plus costs.

### C2 comparators

1. Stock only: hold the stock from S0 to expiry, no overlay.
2. Immediate overlay: the same spread family sold at position entry instead of at the recovery stage.
3. Recovery-stage overlay: the construction itself, spread sold at the section 3 decision point.
4. Exit to cash at the decision point: stock sold at the decision session close, proceeds held as cash to expiry.

### C6 comparators

1. No trade: zero position, zero P and L, the baseline the credit must beat after costs.
2. Feasible share short: short the shares at the decision close and cover at expiry, charged the borrow rate recorded at decision time under the short-program borrow requirements, with recall handled as below. A name with no feasible borrow at decision time has no short comparator; that fact is recorded, and the name is not dropped from the other comparators.
3. Put purchased at the ask: one put per 100 shares, same expiry, strike family locked in the same development lock addendum as section 5, premium taken at the ask from the same quote source as the credit, P and L of max(put strike minus ST, 0) minus premium minus costs.

### Costs

- The credit is already executable (bid minus ask, section 4), so spread crossing cost is inside c and is never charged twice.
- Commissions and exchange and regulatory fees are charged per contract at the executing venue schedule in force at trade time, recorded in the lock addendum, and applied identically to the construction and to every comparator that trades options.
- Stock legs are charged their recorded execution cost: C2 exit-to-cash at the decision close, C6 short sale and cover at the recorded prices, with any stock spread or fee the venue records.
- Borrow cost for the C6 short comparator accrues for the actual days held at the rate recorded at decision time. A rate that changes mid-hold is recorded and the accrual uses the recorded path, never a single assumed rate applied silently.

### Assignment and early exercise

- The short K1 call is American style. Early assignment is a real outcome, not an error to be cleaned away.
- C2 assignment: the held stock is delivered at K1. P and L is computed on the delivery basis (stock sold at K1, long K2 call retained to expiry or closed at its recorded executable bid), and the event is flagged as an assignment outcome.
- C6 assignment: assignment creates a short stock position at K1 alongside the long K2 call. The registered handling is to close the resulting stock position at the first executable price on the session after the assignment notice, at its recorded cost, with the long call retained to expiry or closed at its recorded executable bid. The outcome is flagged as an assignment outcome and kept in the results.
- Assignment outcomes are never excluded, reclassified as non-events, or moved to a different comparator after the fact.

### Dividends and earnings

- C2: dividends paid on the held stock while held are credited to every C2 comparator that holds the stock over the ex-date, including the construction. If assignment delivers the stock before an ex-date, that dividend is not credited, which the delivery-basis P and L already reflects.
- C6: the spread itself receives no dividend. An assigned short stock position is charged any dividend paid while it is short, inside the assignment handling above. The purchased put and the share short comparators are charged and credited by the same rule: a short share position owes dividends paid while short.
- Earnings: the earnings date for each flagged name inside its holding window is recorded at decision time from the estate's archived calendars. Names with earnings inside the window are retained, flagged as earnings-window events, and reported as a named subgroup. They are never dropped after outcomes are known.

### Adjusted deliverables

- The panel accrues the standard chain only. The collector excludes adjusted chain items (non-standard deliverables whose OCC roots carry a digit suffix, observed 2026-11-14 on WDC and FCEL) and counts the exclusion on the snapshot.
- No spread in this study is priced on an adjusted contract as if it were standard. A name whose needed contracts exist only in adjusted form at decision time goes to the missing-options cohort with reason code adjusted only.

### Missing-options cohort and coverage reporting

- Every flag event that reaches a decision point is accounted for in exactly one of two places: an executable spread with a recorded credit, or the missing-options cohort with one reason code.
- Reason codes, fixed in advance: outside panel; manifest error (the error text is carried); no listed expiry in the locked family; no listed strikes spanning the locked family; quote missing or crossed for either leg; adjusted only; borrow infeasible (short comparator only, and it removes only that comparator).
- Coverage is reported for every read as: flag events, events with an executable spread, and events missing by reason code, split by context. A read that reports only the priced events is not a lawful read of this study.

## 8. Chain history inventory (tonight, Sun 2026-11-15)

Searched: the panel store, the index chain store, the dry capture store, the bilbo-options directory (listing and ledger metadata only; iv_snapshot.py was not imported), the night study chain files, the morgue IV and tape stores, and the collector code. Findings:

1. Production single-name chain panel: none yet. ~/workspace/morgue/state/morgue/chains_panel/ does not exist; zero files. First production capture is Mon 2026-11-16 at 16:46 ET under cron chain-panel-close-capture. Plain statement: no usable single-name production chain history exists yet for the C2 or C6 names.
2. Dry capture, proof of mechanism only: ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave4/dry_capture/store/ holds one labelled dry capture dated Sat 2026-11-14 (31 symbol files marked ok in its manifest, 27,405 IV ledger rows, with WDC and FCEL error lines recorded on earlier attempts the same evening). Its own snapshot note states it is a forced run outside the close window and not a session accrual record. It is excluded from development data, from efficacy data, and from any history claim. It proves the collector works; it is not chain history.
3. Index chain store: ~/workspace/morgue/state/morgue/chains/ holds SPY, QQQ, and IWM only. Canonical daily snapshots: 11 sessions per symbol, 2026-10-29 to 2026-11-13 (2026-10-29, 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-12, 2026-11-13). Intraday captures: 111 for SPY, 113 for QQQ, 109 for IWM, spanning 2026-10-29 to 2026-11-13. Beside them: manifest.jsonl (398 lines) and iv_ledger_modelled.jsonl (134,857 rows, modelled IV, index underlyings only). This store contains zero single-name sessions, so it cannot price a C2 or C6 spread. It is usable only as index control context.
4. Morgue IV summary: ~/workspace/morgue/state/morgue/iv_history.jsonl holds 33 rows of summary IV statistics (iv30, iv60, skew terms) for SPY, QQQ, and IWM, 2026-10-29 to 2026-11-13. Summary level, index only, implied only. Not a chain archive.
5. Bilbo IV snapshots: ~/workspace/alpaca-swing-desk/desk/research/bilbo-options/iv_snapshots.jsonl holds 1,198 rows dated 2026-10-02 to 2026-10-14, one target strike per symbol per date (fields: date, symbol, expiry_dte, strike, iv, underlying, target_strike, atr14). No strike grid, no bid or ask, no spread. It cannot price the liability or the credit, and its IV is implied, never physical. Inspected by listing and ledger metadata only; the snapshot script beside it was not imported.
6. Night study chain files: the only tt_chains.json found, in night-study-2026-11-13, carries reference prices with empty expiration lists for every name. The night studies are flag and factor archives (section 6), not chain archives.
7. Options print tape, ancillary: ~/workspace/morgue/state/morgue/pername_tape/ holds 12 session files, 2026-10-29 to 2026-11-13, of Alpaca options trade prints. Prints are not quotes; they cannot supply an executable credit. Not chain history for this study.
8. Short volume store, not options: ~/workspace/morgue/state/morgue/shortvol/ holds 785 dated files, 2023-09-29 to 2026-11-13, of share short volume. Relevant at most to the C6 borrow discussion, never to chain pricing.

Inventory verdict: the only chain history the estate holds tonight is index-only (SPY, QQQ, IWM, 2026-10-29 to 2026-11-13) plus one excluded dry capture. For the single names these constructions trade, there is no usable chain history yet. Accrual starts Mon 2026-11-16.

## 9. Trial ledger

- TRIAL C2C6-001, 2026-11-15: this registration. Cell C2/C6, charged as ONE trial with two holdings contexts (C2 long stock, C6 no stock). Charge: 1.
- Running trial count for the cell after tonight: 1.
- Counting rule, printed here so it cannot drift: C2 and C6 share one liability object and one estimator, so they are charged as one cell forever. Their credits and premiums are never counted as separate diversification, their results are never reported as two independent confirmations, and any grade for the cell is one grade with two context rows. Splitting this cell into two trials, or reporting one context's result as independent support for the other, is a counting violation.
- The development lock addendum (section 5) is part of this same trial and adds no new charge. Any later change to the liability definition, the estimator class, the comparator set, or this counting rule is a new trial and must be charged and dated when made.

## 10. First read date

- First production capture: Mon 2026-11-16, 16:46 ET run, storing the Mon 2026-11-16 close snapshots.
- FIRST READ DATE: Tue 2026-11-17. This is the first date on which a production capture exists, its manifest can be verified complete for Mon 2026-11-16, and a read is lawful.
- Scope of the first read: coverage and executability only. Which panel symbols stored, which manifest errors occurred, which development flag names fall inside the panel, and whether the locked strike and expiry family has executable quotes. No efficacy, liability, or credit-versus-liability read is lawful on a single capture, and no efficacy read of any kind is lawful before the development lock addendum exists and registered expiries begin to resolve.
- Any read before Tue 2026-11-17, any read of the Sat 2026-11-14 dry capture as if it were history, and any efficacy claim drawn from the index-only store are violations of this registration.

## 11. Status

STATUS: PARTIAL. Registration is complete and filed before any result (this file). The study itself is UNVERIFIED: no production captures exist yet, the development lock addendum is not yet written, and no efficacy evidence exists.
EVIDENCE POINTER: section 8 of this file (inventory counts and date ranges taken tonight) and cron chain-panel-close-capture as viewed tonight (weekly, Mon to Fri, 16:46 America/New_York, running v4_chain_panel.py into ~/workspace/morgue/state/morgue/chains_panel/).
Open rows, named: (1) development lock addendum with numeric strike, expiry, put strike, and fee parameters, due before Tue 2026-11-17; (2) first production capture, Mon 2026-11-16 16:46 ET, outside tonight's control; (3) accrual of resolved expiries before any efficacy read can exist.
