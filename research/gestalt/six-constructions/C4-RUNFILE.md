# C4 Runfile: Spend the Volatility Forecast on Execution

Program: Six Constructions, Run 2, Cell C4
Date registered: 2026-11-15 (America/New_York)
Status at registration: PRE-REGISTERED ONLY. No experiment run tonight.
Verdict for tonight: PARTIAL, bounded to pre-registration plus data inventory. The execution study itself is UNVERIFIED and has produced no result.
Typed spend: $0.00
PII gate: This file contains no personal names, emails, addresses, phone numbers, account numbers, or credentials. Trading identifiers named here are instrument symbols, sleeve ids, and file paths only.
House rule compliance: Nothing in this cell imports or uses desk/research/bilbo-options/iv_snapshot.py. That file was not opened, imported, or executed.
Compute tonight: Light only. File listings, line counts, key listings, and small head samples. No backtest, no replay, no simulation run.

## 1. Scope

SCOPE: Surface is the intent level execution decision for positions that are already independently justified. Constraints are that the volatility or movement forecast is never the reason the position exists, no intent is manufactured to create study data, and historical archive material is not upgraded into execution evidence it cannot support. Outcome is a prospective, falsifiable comparison of two routers on identical intents, graded on implementation shortfall across all intents. Proof, when a later run is authorized, will be the final graded artifact from that run, with simulated fills labeled as simulations in every output. Edges are mandate type (completion required versus abstention permitted), queue position, latency, and adverse selection conditional on filling.

## 2. Construction and claim

Construction C4, "Spend the volatility forecast on execution":

A movement forecast that fails as an option purchase, because option prices already charge for the movement, might still improve execution of an independently justified position. The decision it could improve is how to work an order that the desk or the book already wants: cross the spread now, rest a limit order, stage the quantity, wait, or abstain where the mandate permits.

Two cautions are part of the construction, not afterthoughts:

1. High forecast volatility must not automatically mean post a limit order. Waiting can be the expensive choice when the price is moving away, and a passive order can fill precisely because the other side is informed. A fill is not evidence of a good price.
2. The model therefore needs both a fill probability and a value conditional on filling. Any router that scores only fill rate, only spread saved on filled orders, or only average fill price is grading the wrong object and is excluded by this registration.

Evidence status at registration: No execution experiment has been run. The archive's failed long straddle expressions are motivation for looking at execution instead of option purchase, and are not evidence for this claim.

## 3. Accounting identity, fixed before any result

For a buy intent of Q shares, with decision benchmark price P0 at intent time, fills qj at prices Pj for j in 1..n, deadline reference price PT, and total fees F:

IS = sum over j of qj x (Pj minus P0) plus (Q minus sum over j of qj) x (PT minus P0) plus F

where IS is implementation shortfall in currency for that intent. Positive IS is a cost for a buy.

Rules that follow from the identity and are binding on any later grading:

a. The unfilled term charges missed participation. An intent with no fill is not dropped and is not graded zero; it is charged (Q) x (PT minus P0) plus any fees actually incurred.
b. Partial fills are graded on both terms. Filled quantity carries its own prices; unfilled quantity carries the deadline reference.
c. P0 is the decision benchmark recorded at intent time (Section 5), fixed before any routing decision is scored. It is never replaced by the first fill price, the arrival price of a later stage, or a post hoc mid.
d. PT is the reference price at the intent deadline, recorded by the same quote source as P0 where a quote source exists, otherwise by the named bar source, with the source recorded per intent.
e. If the mandate requires completion, the reference for the unfilled term becomes attainable completion prices: the price at which the residual quantity could actually have been completed at or after the deadline under the recorded quote or bar source, not a hypothetical mid. The completion rule used must be named per intent before grading.
f. For a sell intent the identity is mirrored so that positive is still cost: each fill term is qj x (P0 minus Pj) and the unfilled term is (Q minus sum qj) x (P0 minus PT), plus fees. This mirror is registered here, before any result, and is not a post hoc adjustment.
g. Fees are included where the source records them. Where a simulated or paper route charges no fees, the fee term is recorded as zero and that fact is printed in the output, not silently assumed away.
h. Per intent IS is also reported normalized, in basis points of intended notional Q x P0, so intents of different sizes can be pooled without hiding the currency total. Both forms are reported; neither replaces the other.

## 4. Intent source: independently generated intents only

Eligible intents are intents generated by the desk's or the book's own trading logic, for their own reasons, before and independently of this study. The study attaches to that order flow; it does not create it, resize it, retime it, or select which sleeves may fire.

### 4.1 Verified estate artifacts that record intents, submissions, and fills

Each path below was verified to exist tonight, 2026-11-15, by listing and by reading keys or counts from the file itself. Field descriptions are at metadata level only.

A. Desk dispatcher journal, muse-desk-v3 (primary intent and order event source)
Path: ~/workspace/muse-desk-v3/state/dispatcher.jsonl
Rotations, all verified present: dispatcher.jsonl.1, dispatcher.jsonl.2, dispatcher.jsonl.3, dispatcher.jsonl.4 in the same directory.
Sizes and counts tonight: current file 3,805,976 bytes and 12,782 lines. Rotation line counts: .1 has 23,715 lines, .2 has 7,408 lines, .3 has 21,462 lines, .4 has 2,245 lines. Total across the five generations: 67,612 lines.
Event types in the current file, counted tonight: intent_rejected 2,575; virtual_book_dual_read 2,445; broker_unavailable 1,489; fill 1,125; intent_duplicate 1,037; exit_reconciled_to_broker_book 1,005; drained_terminal 761; order_submitted 674; exit_storm_suppressed 542; broker_rejected_terminal 384; symbol_normalized 356; virtual_book_enforced 328; drained 49; drained_deferred 10; pending_drain_deferred 1; crypto_fee_in_kind 1.
Union of fields across the current file: action, attempts, broker_code, broker_message, broker_order_id, broker_position, broker_position_qty, broker_qty, cash_halt, client_order_id, derived_qty, discrepancies, error, error_body, event, from_position_intent, from_qty, from_side, from_symbol, http_status, imported, intent_id, journal_gross_qty, kind, limit_price, order_type, position_intent, price, qty, reason, ref_price, resting_close_qty, result, session, side, sleeve, suppressed_reason, symbol, time_in_force, to_position_intent, to_qty, to_side, to_symbol, ts.
Coverage in the current file: 53 distinct symbols and 71 distinct sleeves.
Fill rows carry: broker_order_id, client_order_id, event, imported, intent_id, position_intent, price, qty, side, sleeve, symbol, ts.
Order submission rows sampled tonight are sparse: the sampled order_submitted rows carry only client_order_id, event, intent_id, sleeve, and symbol, with no price, quantity, side, or timestamp on those rows. Other event rows carry more: for example broker_unavailable rows carry qty, side, order_type, limit_price, and time_in_force.
Timestamp limitation, stated plainly: only 1,126 rows in the current file carry a ts field, with ts values from 2026-11-12T14:30:00Z to 2026-11-15T08:24:13Z. Most rows have no ts field at all. A further 11,637 rows carry a timestamp embedded in intent_id, with embedded dates from 2026-11-11 to 2026-11-15 in the current file. Embedded intent timestamps are sleeve decision times as encoded by the sleeve, not verified submission or fill times, and must not be relabeled as either.

B. Durable fill ledger, muse-desk-v3 (derived from the dispatcher generations)
Path: ~/workspace/muse-desk-v3/state/fill_ledger/
Contents verified: fills-000001.jsonl with 5,000 rows, fills-000002.jsonl with 3,930 rows, and manifest.json.
Manifest states: format fill-ledger/1, total_fills 8,930, duplicates_dropped 0, built_from the five dispatcher generations listed in item A, with a sha256 recorded per segment.
Row fields match the dispatcher fill rows listed in item A. This is the cleanest fill source in the estate, and it is a derived ledger: its provenance is the dispatcher journal, so it inherits the dispatcher's timestamp and quote limitations.

C. Reconcile history, muse-desk-v3
Path: ~/workspace/muse-desk-v3/state/reconcile_history.jsonl
Size tonight: 1,300,619 bytes.
Fields: cycle_id, fill_sweep, generated_at, report. The fill_sweep object carries checked counts, errors, and fee adjustment fields. The report object carries broker order holds and cash check fields. Sampled generated_at values begin 2026-11-13T23:09:17Z. This source corroborates fills and fees at cycle level; it is not an intent source and carries no quotes.

D. Broker pending log, muse-desk-v3
Path: ~/workspace/muse-desk-v3/state/broker_pending.jsonl
Verified present and empty tonight: 0 bytes. It records nothing at present and cannot support any grading until it accumulates rows.

E. Per sleeve journals, muse-desk-v3
Pattern: ~/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl
Count verified tonight: 339 journal files match this pattern. Field sets vary by sleeve; the sampled first journal carries cycle_id, event, snapshot_hash, status, and ts. These journals are supporting context for why an intent existed. They are not a uniform intent schema and are not a substitute for the dispatcher record.

F. Midna book ledger (the book's own fills; simulated fills, see the label rule in Section 7)
Path: ~/workspace/midna-book/ledger.json
Contents verified: a book object with fills, positions, equity_history, exception_ledger, pods, and rules. Fills count tonight: 14. Positions count tonight: 7.
Fill fields: symbol, side, qty, decision_id, decision_ts, bar_ts, bar_open, feed, timeframe, fill_price, priced_at, slippage_bp.
Fill rule, from ~/workspace/midna-book/fill_engine.py, verified by reading its header tonight: the fill price is the open of the next 5 minute SIP bar at or after the decision timestamp, adjusted 5 basis points against the trade, capped at the pricing bar's traded range, with a capped fill flagged. These are therefore simulated fills by construction, priced from bars, not broker executions. Every use of this source in C4 output must say so.

G. Ghost book ledger (priced option expressions, not fills)
Path: ~/workspace/midna-book/ghost-book-ledger.jsonl
Rows tonight: 21.
Fields include: symbol, date, structure, strikes, expiry, direction, debit, breakeven, max_loss, priced, expression_viable, fire (with entry, stop, target), chain_fetched_at, chain_ts, bundle_generated_at, selector_rows, selector_verdict, resolved, resolution_date, realized_pnl, realized_r.
Use in C4: motivation and expression context only. A priced expression with a chain timestamp is not an execution, and realized fields are null on the sampled rows.

H. Expression shadow ledger
Path: ~/workspace/midna-book/expression-shadow-ledger.jsonl
Size tonight: 10,697 bytes.
Fields include: symbol, date, session, source, expression, debit_mid, width, max_loss, exit_rules, baseline, status. Sampled source notes name indicative mids and a verified chain structure with empty quotes after hours. Use in C4: context only, not execution evidence.

I. Legacy swing desk records (checked, and found thin)
Path: ~/workspace/alpaca-swing-desk/desk/hidden_state/fills_tca.jsonl exists and is empty: 0 bytes, 0 lines.
Path: ~/workspace/alpaca-swing-desk/desk/outcomes/outcomes.jsonl has 9 lines, sampled dates 2026-10-12 to 2026-10-13, with signal, decision, and outcome fields, not an execution log.
Neither legacy source can support C4 grading.

### 4.2 Eligibility rules, registered

1. An intent enters the study population at the moment the desk or book logic emits it, whether or not it is later rejected, duplicated, suppressed, submitted, partially filled, or filled. Rejected and duplicate intents are recorded and classified, and the classification rule is fixed here: intent_rejected and intent_duplicate rows are population records for counting and for router counterfactuals only where a genuine routing choice existed; where no routing choice existed (for example a duplicate of an intent already working), the row is excluded from the IS pool and the exclusion is counted and printed.
2. No intent is excluded because its outcome was bad, its sleeve later lost money, or its fill history is inconvenient. Exclusions are only for the pre named mechanical reasons in rule 1, plus a missing decision benchmark P0, and every exclusion is counted with its reason.
3. Entry and exit intents are both eligible and are stratified, never pooled silently. Position intent (open versus close) is a required stratum.
4. Crypto and perpetual symbols present in the dispatcher (for example symbols carrying a slash or a PF prefix) are a separate stratum from US equities and options underlyings, because their quote, fee, and session structure differs. They are not pooled with equity intents in the primary grade.

## 5. What is recorded at intent time (prospective capture schema)

The historical record in Section 4 does not contain most of these fields joined to an intent (see Section 9 for the gap statement). This schema is therefore a prospective capture requirement: from the first shadow run onward, each intent gets one record, written at intent time, before any outcome is known, containing:

a. Intent identity: intent_id, sleeve or book decision_id, cycle_id where available, and the intent timestamp with its clock source named.
b. Instrument: symbol in the source's own form, plus the normalized symbol where symbol_normalized applies, asset class, and for options the contract symbol, strike, expiry, and right where the intent is an option intent.
c. Side and quantity: side, position_intent, intended quantity Q in shares or contracts, and the quantity unit.
d. Deadline: the intent deadline or time in force, the session, and whether the mandate requires completion or permits abstention. Where the source gives no explicit deadline, the deadline rule applied is recorded by name (for example end of session) and flagged as imputed, never presented as source data.
e. Reason: the sleeve's stated reason, signal, or fire object, in the compact form the source provides, sufficient for a later reader to confirm the intent was independently justified without this study.
f. Market at intent time: bid, ask, mid, spread in currency and in basis points of mid, bid size and ask size where the source provides them, and depth where available, each with its capture timestamp and source named. If a field is unavailable, it is recorded as unavailable. It is never backfilled from a later quote, a bar, or a chain snapshot.
g. The volatility forecast: the numeric movement or volatility forecast value that C4 proposes to spend, its horizon, its units, the model or artifact that produced it, and its generation timestamp. A confidence word is not a numeric forecast and does not satisfy this field.
h. Any directional forecast attached to the intent, recorded separately from the movement forecast, so the study can tell whether any benefit came from direction rather than from movement magnitude.
i. Recent order flow: a compact, pre defined summary over a stated lookback ending at intent time (for example own desk submissions and fills in the symbol, and any recorded flow proxy the source actually holds), with the lookback and source named. If no flow source exists for that intent, the field is recorded as unavailable.
j. Router state: which router graded the intent (baseline or augmented, Section 6), the action chosen, the limit price and distance where applicable, stage sizes and times where applicable, and the decision timestamp, so latency from intent to decision to submission can be computed where submission timestamps exist.
k. Outcome fields, appended later and never edited into the intent time fields: submissions, acknowledgements where available, fills with price, quantity, and timestamp, fees, the deadline reference PT and its source, and the markout prices in Section 7.

Storage rule: the capture record is append only. Corrections are new rows that name the row they correct.

## 6. Policies compared

Two routers grade the same intents. Nothing else differs between the arms.

### 6.1 Baseline router (price aware, no movement forecast)

Inputs allowed: quoted spread, displayed depth where available, ordinary volatility (a realized or bar based volatility measure computed from data available at intent time, named per run), time of day, instrument, side, quantity relative to displayed size, and the thesis fields the desk already attaches (sleeve, position intent, deadline, mandate type). The baseline is deliberately competent: it is the ordinary spread and volatility router named in the falsifier, implemented honestly, not a straw man that always crosses or always rests.

### 6.2 Augmented router (baseline plus the movement forecast)

Identical to the baseline in every input, rule, and feasible action, plus one added input: the numeric volatility or movement forecast from Section 5 item g, with its horizon matched to the intent deadline. The augmented router may use the forecast only to choose among the feasible execution actions for an intent that already exists. It may not create, cancel for thesis reasons, resize for thesis reasons, or retime the intent itself. Any such influence, if ever proposed, is a different study and needs its own registration.

### 6.3 Feasible actions, enumerated for both routers

1. Cross: take displayed liquidity immediately at or through the touch, up to the intended quantity, accepting the spread as the price of immediacy.
2. Rest: post a passive limit order at a stated limit distance from the touch or mid, where the distance is stated in ticks and in basis points, with a stated resting duration not exceeding the deadline, and a stated rule for what happens at expiry of the resting period (cross the residual, rest again, or stop, as the mandate permits).
3. Stage: split Q into two or more tranches under a stated schedule (sizes and trigger or time spacing fixed by the router rule before the intent is graded), each tranche itself crossed or rested under the same action rules.
4. Wait: defer the first submission by a stated interval within the deadline, then act under the router's rule with the market as it then stands. The wait interval and the post wait rule are part of the router, fixed before grading.
5. Abstain: take no position on this intent. Feasible only where the mandate permits abstention. Where completion is required, abstain is not in the action set, and any router output of abstain on a completion intent is a router error, counted as such, with the intent then graded under the completion reference of Section 3 rule e.

Both routers must output exactly one action (or one staged schedule) per intent, with all parameters that Section 5 item j requires. A router that declines to grade an intent is recorded as a router failure for that intent, not as a missing observation.

### 6.4 Comparison design

Replay and paper shadow first (Section 8). In shadow, both routers grade every intent; the desk's actual execution proceeds untouched, and the routers' actions are counterfactual records. Where both routers choose the same action on an intent, that intent contributes no contrast and is counted as a tie by construction, reported separately, so the effective contrast sample is visible and is never inflated by identical decisions.

## 7. Grading

Primary grade: implementation shortfall under Section 3, computed across ALL intents in the IS pool, including no fills and partial fills, reported as the distribution and the total for each router, and as the paired per intent difference (baseline IS minus augmented IS, so positive means the augmented router cost less) with the count of intents, the count of contrast intents, and a plain statement of the share of the total difference contributed by the largest five intents.

Secondary grades, all registered in advance:

a. Fill conditioned markouts. For each fill, the signed price movement from fill price to the reference price at fixed horizons after the fill (registered horizons: 1 minute, 5 minutes, 30 minutes, and the deadline), signed so that a buy fill followed by a price fall is adverse. Reported as the distribution over fills for each router, separately for crossed and rested fills. This is the adverse selection check: a router whose rested fills systematically show adverse markouts is buying fills with information leakage, and that fact is reported on the face of the grade, not netted away inside IS.
b. Fill probability and completion: fill rate, partial fill rate, no fill rate, mean filled fraction, and time to first fill and to completion, per router, per stratum.
c. Value conditional on filling: mean and median IS on filled quantity only, reported beside, never instead of, the all intents IS. The gap between the two is itself a reported quantity, because it measures how much of any apparent benefit is survivorship over fills.
d. Inventory and downside consequences: for staged, waited, and abstained actions, the position actually held during the working period versus the intended position, the price exposure missed or carried as a result (using PT and the markout references), and the worst per intent shortfall in each arm. Where an exit intent is worked slowly, the residual position's exposure over the working period is reported the same way.
e. Stratification: every grade above is reported by side, by position intent, by asset class stratum, by mandate type, and by forecast level band (the forecast value split into bands fixed before the run, with band edges printed). A pooled benefit that reverses in the completion mandated stratum is reported as reversed there, not averaged away.

Queue position treatment, stated in advance: the estate holds no queue data (Section 9), so no historical claim about queue position can be made. In any simulation, a rested order is assumed to join the queue behind the displayed size at its price at placement time, and it fills only after that quantity plus subsequent prints at that price have traded, under the simulator's stated rule. Sensitivity to queue assumption is mandatory: every simulated grade is run under at least a front of queue optimistic bound and a back of queue conservative bound beside the central assumption, and all three are printed. A benefit that exists only at the front of queue bound is reported as exactly that.

Latency treatment, stated in advance: in shadow and simulation, decision and submission are delayed by a stated latency drawn from the observed intent to submission gaps where those exist in the prospective capture, and by a fixed stress latency named in the run output. Prices are read at the delayed time, not at intent time. A grade computed with zero latency is labeled zero latency and cannot be the headline grade.

Simulated fill labeling: simulated fills are labeled as simulations in every output, table, chart, and summary sentence that uses them. The Midna book fills in Section 4 item F are simulated fills under that book's bar based rule and carry the same label. Paper shadow counterfactual fills are simulations. Only dispatcher and fill ledger rows sourced from the broker record are actual fills, and outputs must keep the two classes in separate columns or separate tables, never summed into one fill count.

Statistics, minimal and pre committed: paired per intent differences are the unit of analysis. Report the mean and median paired difference, the share of contrast intents where the augmented router was cheaper, and an interval estimate from a paired bootstrap over intents with the seed recorded. No significance claim is made from a sample whose contrast intent count is under 30; such a run is reported as a pilot with its count printed. Multiple strata are descriptive unless a stratum was named primary in advance; the primary population is all IS pool intents, and the primary stratum check is mandate type.

## 8. Run sequence and authorization boundaries

Stage 1, replay: permitted only as a coarse, bar based simulation where quotes do not exist, and labeled as such, with the explicit caveat that bar based replay cannot estimate fill probability, queue position, or adverse selection, and therefore cannot confirm or falsify C4. Replay on the sampled NBBO archive in Section 9 item Q2 is permitted as a methods check on those sampled days only, for symbols and days that archive actually covers, and its results do not transfer to desk intents, whose window it does not overlap.
Stage 2, paper shadow: the first stage that can produce C4 evidence. Requires the prospective capture of Section 5 to be running, both routers grading every intent, and the desk's real execution untouched. This runfile is the pre-registration for that stage; the capture build itself is separate work, not authorized or performed tonight.
Stage 3, randomized routing: NOT authorized by this runfile. Any later experiment that actually routes real or paper orders by random assignment between the routers needs its own authorization, and under this registration it would additionally require: assignment probabilities fixed and logged per intent before the outcome, the randomization seed or device recorded, the assignment log append only, and grading still across all assigned intents including router failures. Absent that separate authorization, no routing of any order is changed by this study.

Tonight's work stops at this registration plus the inventory in Section 9. No stage was run tonight.

## 9. Data inventory, as verified tonight 2026-11-15

Granularity key: trade or bar means OHLCV bars only; quote means bid and ask records; depth means size beyond the top of book or a book; aggregate means summary statistics with no underlying records.

Q1. Desk equity quote cache (inert)
Path: ~/workspace/muse-desk-v3/cache/quotes/latest.json
Verified content: an empty JSON object, 2 bytes. Granularity: none. There is no equity NBBO archive inside muse-desk-v3. The directory exists; the archive does not.

Q2. Sampled NBBO archive, quantjourney adoption study (the only true quote archive found)
Path: ~/workspace/research_notes/quantjourney-adoption-20261031/edge/quotes_raw.json
Size: 9,326,239 bytes.
Granularity: quote, tick level NBBO. Record fields: ap (ask price), as (ask size), ax (ask exchange), bp (bid price), bs (bid size), bx (bid exchange), c (conditions), t (timestamp, nanosecond precision in sampled records), z (tape).
Instruments, 14: SPY, QQQ, AAPL, NVDA, MSFT, SOXL, AXTI, CORZ, FFIV, ANF, SNDL, TLRY, CLOV, BYND.
Date coverage: 14 sampled dates per symbol, 2026-05-06, 2026-05-20, 2026-06-03, 2026-06-17, 2026-07-01, 2026-07-15, 2026-07-29, 2026-08-12, 2026-08-26, 2026-09-09, 2026-09-23, 2026-10-07, 2026-10-21, 2026-10-28.
Volume per symbol across those dates, counted tonight: 5,600 quote records for each of SPY, QQQ, AAPL, NVDA, MSFT, SOXL, AXTI, and CORZ; 4,710 for FFIV; 4,763 for ANF; 2,351 for SNDL; 4,980 for TLRY; 4,413 for CLOV; 3,635 for BYND. Sampled records show a per symbol per day cap: the file records n_seen_pages_capped 400 and truncated true, and 5,600 equals 14 dates times 400. Treat every symbol day as a capped sample of quotes, not a complete quote stream.
Limitations, plainly: sampled days only, capped per day, no November 2026 dates, and therefore zero overlap with the dispatcher intent window of 2026-11-11 to 2026-11-15. It cannot be joined to a single desk intent. No depth beyond top of book sizes as and bs.

Q3. Live quote session quality record, terminal lineup (aggregates only)
Path: ~/workspace/terminal-lineup/site/corrected-band/live_quote_record.json
Size: 69,574 bytes.
Content: a record titled "FE12 live quote session quality readings", freshest session 2026-11-13.
Sessions, 10, each with one captured_at_utc timestamp: 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-12, 2026-11-13, each captured near 20:31 UTC, with 49 names per session except 48 on the last two sessions.
Per name fields: depth_drop_share, events, median_depth, median_spread_share. Granularity: aggregate. There are no bid or ask prices, no per quote timestamps, and no size records in this file. It can describe typical spread and depth conditions per session; it cannot price or fill any individual intent.

Q4. Options chain snapshots, muse-desk-v3
Pattern: ~/workspace/muse-desk-v3/cache/options/<symbol>/chain.json
Count verified: 65 symbol files.
Fields in sampled files: symbol (contract), strike, expiration, bid, ask, and on some files delta and right. Granularity: quote, single snapshot per symbol, overwritten in place. Sampled file modification times are 2026-11-02. The files carry no internal fetch timestamp, no underlying price, no quote size, and no history. They are the last snapshot only, and the sampled QQQ chain even carries an expiration of 2026-11-02, confirming staleness for November intent use. Usable in C4 only as evidence of what a chain snapshot looks like, not as intent time quotes.

Q5. Bars, muse-desk-v3 (the estate's main price history)
Path: ~/workspace/muse-desk-v3/cache/bars/<symbol>/<timeframe>.jsonl
Counts verified: 151 symbol directories, 176 files, comprising 126 files of 1Day, 21 files of 1Min, 27 files of 1Hour, and 2 files of 4Hour.
Fields, complete: t, o, h, l, c, v. Granularity: trade or bar. No bid, no ask, no size at price, no depth.
Examples verified tonight: SPY 1Day has 53 rows from 2026-09-01T04:00:00Z to 2026-11-13T05:00:00Z. NVDA 1Min has 13,889 rows from 2026-10-20T21:41:00Z to 2026-11-13T14:32:00Z. SPY has 1Hour and 1Day only, no 1Min file; QQQ has 1Day and 1Min.
Related snapshots: ~/workspace/muse-desk-v3/state/warm_bars.json at 40,891,200 bytes and ~/workspace/muse-desk-v3/state/bars_secondary.json at 1,001,072 bytes, each a fetched_at timestamp plus a bars object, same bar granularity.

Q6. Terminal snapshots
Paths: ~/workspace/muse-desk-v3/state/terminal_feed.json (188,509 bytes) and ~/workspace/muse-desk-v3/state/terminal.json (30,500 bytes), with a second copy of the feed under ~/workspace/muse-desk-v3/terminal/.
Fields include generated_at, cycle_id, setups, sleeves or sleeve_groups, account and account_positions on the feed, and a summary. Granularity: snapshot, overwritten each cycle. These record what the terminal displayed, not a quote history, and earlier cycles are not retained in these files.

Q7. Tensor bundle and ghost capture (signal context, with chain timestamps inside)
Paths: ~/workspace/muse-desk-v3/cache/tensor/bundle.json, with dated archives bundle-2026-11-11.json through bundle-2026-11-15.json in ~/workspace/muse-desk-v3/cache/tensor/archive/, and copies served to the book at ~/workspace/midna-book/ghost-capture/2026-11-14/first-serve.json and ~/workspace/midna-book/ghost-capture/2026-11-15/first-serve.json, logged in ~/workspace/midna-book/ghost-capture/capture_log.jsonl (300 lines).
Content: session, generated_at, sleeves, fires, tensor universe, analysis, and census, plus per symbol analysis objects. This is where many desk intents originate, and its generated_at is a genuine intent adjacent timestamp. It carries no NBBO for the underlying at fire time.

Q8. Volatility and forecast artifacts (the forecast to be spent)
Paths verified: the forecast package at ~/workspace/muse-desk-v3/desk3/forecast/ (modules include registry, ensemble, contexts, capacity, costs, data, evidence, freeze, gates, laws, score, sleeve_ensemble, xs); ~/workspace/muse-desk-v3/state/iv_ledger.json, which holds one IV value per session for 13 symbols with the sampled session 2026-11-13 (symbols include AEHR, ARM, ARQQ, AXTI, CORZ, DGXX, HIVE, IREN, NBIS); ~/workspace/midna-book/FORECAST-LOG.md, dated forecast calls from 2026-11-03 onward in confidence words; and the forecast twin records under ~/workspace/midna-book/typed-layer/ including forecast_twin_ledger.jsonl.
Gap within this item: no artifact found in tonight's search records a numeric movement or volatility forecast joined to an intent_id at intent time. The IV ledger is per symbol per session, not per intent. The forecast log is words, not numbers. The join that Section 5 item g requires does not exist yet and must be built prospectively.

O1 to O4. Order event and fill data: items A to E of Section 4.1 are the order event inventory and are not repeated here. Summary: intents, submissions, rejections, duplicates, suppressions, and fills exist in quantity for 2026-11-11 to 2026-11-15 in the current dispatcher generation, with older generations in the rotations and 8,930 deduped fills in the durable fill ledger. Submission rows are sparse, most rows lack a ts field, and no row in any sampled order source carries a contemporaneous bid, ask, or depth.

### 9.1 The gaps, stated plainly, and what they decide

Gap 1, no contemporaneous quotes for desk intents. The estate holds fills and submissions with no contemporaneous quotes joined to them. For the November intent window there is no NBBO archive at all in the estate: the desk quote cache is an empty object, the only true NBBO archive stops at 2026-10-28 on sampled capped days, and the chain snapshots are a single stale snapshot per symbol. P0 and PT therefore cannot be reconstructed honestly for historical intents, except coarsely from bars.
Gap 2, no depth. No level 2, order book, or depth time series exists anywhere in the searched estate. The only depth numbers are per session medians in item Q3. Displayed size at intent time is unrecoverable historically.
Gap 3, no queue or latency record. Nothing records queue position, acknowledgement times, or submission latency for historical orders. Most dispatcher rows do not even carry a timestamp.
Gap 4, no intent time forecast join. See item Q8. The treatment variable of this study was never recorded against the intents it would have treated.
Gap 5, bar only price history for most symbols. One minute bars exist for only 21 symbol files; the rest are hourly or daily. Even a coarse replay is minute resolution at best, and only for a minority of symbols.

Decision that follows from the gaps: execution quality replay of historical desk intents is NOT possible from the estate as it stands. A bar based pass over historical intents would be a labeled coarse simulation that cannot estimate fill probability, cannot condition on the quote at intent time, cannot model queue or latency, and cannot measure fill conditioned markouts at the registered horizons. It will not be run as evidence and will not be described as a replay of executions. C4 evidence can only come from Stage 2 paper shadow with the prospective capture of Section 5 running, or from a Stage 1 methods check confined to the sampled NBBO days of item Q2 with no transfer claim to desk flow. This is a route finding, not a finding against the construction: the construction is untested, not falsified.

## 10. Falsifier

The claim weakens, in the words of the construction as handed to this cell, if the benefit disappears when missed fills, fill conditioned markouts, realistic queue position, and latency are included, or if an ordinary spread and volatility router performs equally.

Operational form, registered: C4 is falsified for the studied population if, in a Stage 2 shadow grade conducted under Section 7, any one of the following holds.
1. The mean paired per intent IS difference (baseline minus augmented) is zero or negative across all IS pool intents, or its interval estimate includes zero while the point estimate is smaller than the run's own fee and latency stress adjustments.
2. The augmented router's advantage on filled quantity is offset, in whole or in part large enough to erase the all intents advantage, by adverse fill conditioned markouts on its rested fills at the 5 minute or 30 minute horizon.
3. The advantage is present only under the front of queue bound or only at zero latency, and disappears under the central queue assumption or the stress latency.
4. The baseline router of Section 6.1, given the same intents and the same action set, matches the augmented router within the interval estimate, which is the "performs equally" branch of the falsifier stated as a test.

A null or falsifying result is a result. It will be reported with the same completeness as a positive one, including the contrast intent count, and it demotes the movement forecast back to a non execution input for this population until a new registration says otherwise.

## 11. Trial ledger

Trial counting rule for this program: each pre-registered study design charged to a construction counts as one trial in that construction's ledger, whether or not a run follows, because the design space was searched to produce it.
C4 ledger after tonight: 1 trial.
Entry 1, 2026-11-15: this runfile. Intent level execution comparison, baseline spread and volatility router versus the same router augmented with a numeric movement forecast, graded on all intents implementation shortfall with fill conditioned markouts, queue and latency sensitivity, replay barred as evidence by the data gaps in Section 9.1, paper shadow as the first evidentiary stage. No run performed, no result claimed.
Any later amendment, added stratum, added action, changed horizon, or changed band edge is a new ledger entry, numbered in order, written before the run it affects.

## 12. What was not done tonight

No replay was run. No simulation was run. No router was coded. No order, paper or otherwise, was routed, modified, or shadowed. No capture schema was built into the desk or the book. No file outside this program home was modified. The failed long straddle archive was not re graded and is cited as motivation only.

## 13. Status line

STATUS: PARTIAL. Evidence pointer: this file, C4-RUNFILE.md in ~/workspace/research_notes/six-constructions-20261115/, containing the pre-registration (Sections 2 to 8, 10, 11) and the verified data inventory with gaps and the replay decision (Sections 4.1 and 9), all checks performed tonight as described in the header. Open rows, named: the prospective intent time capture of Section 5 does not exist yet; no evidentiary run of any stage has been performed; Stage 3 randomized routing is unauthorized. The construction itself is UNVERIFIED.
