# V3: The D-01 Reject Counterfactual

Wave 4, workstream V3 only. Sat 2026-11-14 night.
Census snapshot read completed 2026-11-15T03:22:10Z (Sat 2026-11-14 22:22 ET). The live dispatcher file grows; the counts below are that snapshot, and a second full run reproduced them exactly.

## Verdict first

NULL at the level that matters. No graded reject class is proven to systematically reject winners, and the gate is not proven to earn its keep either, once repeated rejects of the same intent are collapsed into independent events.

Row-level grading of reconcile_halt (the only class with a symbol) splits in opposite directions: blocked entries leaned protective and blocked exits leaned costly. But 5,331 graded rows at the 1-session horizon collapse to 126 distinct sleeve, symbol, session clusters, because a persistent halt re-rejects the same intents every cycle. At cluster level the pooled effect is +0.92% at 1 session (t 1.67) and -0.04% at 3 sessions (t -0.05). At 5 sessions only 30 rows in 14 clusters are resolvable inside the window and the result is null. The row-level t statistics of 10 to 29 are repetition inflation, not evidence.

The corpus-level finding is the durable deliverable: the reject book is not a gradeable labeled corpus. Only 7,023 of 29,360 reject rows (23.9%) carry a symbol at all. Only reconcile_halt can be graded directionally, and even it carries no side, kind, quantity, or reference price, so direction had to be reconstructed from the fill ledger under a long convention. 76.1% of the reject book is ungradeable by construction, including all 760 insufficient_slice_bp rows. The cure is a dispatcher payload change, named in section 4, not landed here (read-only rail on the desk tree).

## 1. Census

Source: ~/workspace/muse-desk-v3/state/dispatcher.jsonl plus rotations .1 to .4, read only. Total dispatcher rows 66,041. intent_rejected rows 29,360 (44.5%). Parsed table: v3_rejects.jsonl (29,360 rows, one per reject, every count below recountable from it). Script: v3_grade.py. Results: v3_results.json. Bars cache: v3_bars.json.

| reason | n | sleeves | date span (UTC, from intent_id) |
|---|---|---|---|
| exit_already_resting_at_broker | 11,931 | 58 | 2026-11-02 to 2026-11-13 |
| exit_satisfied_no_broker_position | 9,173 | 59 | 2026-11-02 to 2026-11-13 |
| reconcile_halt | 7,023 | 25 | 2026-11-02 to 2026-11-14 |
| insufficient_slice_bp | 760 | 17 | 2026-11-02 to 2026-11-15 |
| exit_satisfied_no_sleeve_position | 432 | 9 | 2026-11-12 to 2026-11-13 |
| bad_qty | 23 | 4 | no parseable timestamp (legacy intent_id format) |
| bad_kind | 11 | 6 | 2026-11-02 to 2026-11-13 |
| exit_blocked_opposite_side_resting | 7 | 5 | 2026-11-13 to 2026-11-15 |

My recount matches the recon counts class for class exactly.

Payload shape: 22,337 reject rows carry exactly four fields (event, intent_id, reason, sleeve). The 7,023 reconcile_halt rows additionally carry symbol, cash_halt, and discrepancies. 259 rows (228 exit_satisfied_no_broker_position, 23 bad_qty, 8 exit_already_resting_at_broker) carry a legacy intent_id format (for example aster_etf_exsmh1_m150-2026-10-1436-1-ABCL-sell) with no embedded timestamp; their date is absent from the record and named absent here, not reconstructed.

Reconcile_halt concentration: tensor_swing alone is 4,172 of 7,023 rows. By UTC date, 6,483 of 7,023 rows (92.3%) fall on 2026-11-07 to 2026-11-10. This is one multi-day halt episode re-firing, not 7,023 independent decisions.

## 2. Grading reconcile_halt

Method. Fill ledger: ~/workspace/muse-desk-v3/state/fill_ledger/fills-000001.jsonl and fills-000002.jsonl, 8,928 fills, timestamps 2026-10-27 to 2026-11-13. Classification: net signed quantity for (sleeve, symbol) from fills strictly before the intent timestamp (intent_id embeds YYYYMMDDTHHMMSS, treated as UTC; matched fill batches land roughly 10 to 15 minutes after their intent timestamps, consistent with UTC). Nonzero net means the sleeve held the symbol, so the blocked intent is exit-like; zero net means entry-like. Side is not persisted on reject rows, so scoring follows the task definition under the long convention: entry-like score = forward return; exit-like score = minus forward return. Positive score means the rejection cost the sleeve. The convention is validated by the ledger itself: of 3,285 exit-like plain-equity rows, 3,280 held a positive (long) net and only 5 a negative net.

Symbols. 57 distinct symbols. Excluded from directional grading: 1,006 OCC option code rows (SPY put codes) and 572 crypto pair rows (BTC/USD), total 1,578 excluded. Graded pool: 5,445 plain equity rows across 50 symbols. All 50 symbols returned bars (19 sessions each, zero no-bar symbols).

Bars. Split-adjusted SIP daily bars, 2026-10-20 to 2026-11-13, fetched through the estate route (desk3.run_live credential_env plus desk3.netfetch fetch_json, data.alpaca.markets /v2/stocks/bars, feed sip, adjustment split), the same route as keepgoing2/wave3/w3_fetch_focus_bars.py. Route note: an explicit end parameter of 2026-11-14 draws HTTP 403 "subscription does not permit querying recent SIP data" (reproduced on SPY alone); omitting end, as wave 3 does, succeeds, and the window end is enforced in scoring. Cross-check: closes for ARM, CRDO, SPY, QQQ, and AXTI match wave 3 focus_bars.json exactly on all 19 common sessions.

Session definition. Session 0 is the first bar date on or after the intent's America/New_York calendar date. Horizon h return is close[session 0 + h] / close[session 0] minus 1, close to close. Events whose forward window runs past 2026-11-13 are unresolvable at that horizon and counted, never extrapolated.

Classification result: entry-like 2,160 rows; exit-like 3,285 rows.

### Row-level results (n, mean, median, t; scores in return units)

| horizon | pool | n | mean | median | t |
|---|---|---|---|---|---|
| 1 session | all | 5,331 | +1.29% | +0.44% | 10.50 |
| 1 session | entry-like | 2,160 | -1.32% | -2.33% | -9.07 |
| 1 session | exit-like | 3,171 | +3.06% | +2.55% | 17.64 |
| 3 sessions | all | 5,230 | +1.00% | +0.95% | 6.71 |
| 3 sessions | entry-like | 2,156 | -4.54% | -5.27% | -20.56 |
| 3 sessions | exit-like | 3,074 | +4.89% | +4.35% | 28.94 |
| 5 sessions | all | 30 | +5.27% | +0.08% | 2.18 |
| 5 sessions | entry-like | 19 | -0.03% | +0.08% | -0.50 |
| 5 sessions | exit-like | 11 | +14.42% | +24.78% | 2.51 |

Unresolvable: at 1 session, 114 of 5,445 (60 forward window past 2026-11-13, 54 with no session on or after the intent inside the window, the 2026-11-14 UTC tail). At 3 sessions, 215. At 5 sessions, 5,415 of 5,445: the graded mass sits in sessions 2026-11-06 to 2026-11-10, whose 5-session windows close after 2026-11-13. The 5-session row is therefore a 30-row residue (14 clusters) and carries no verdict weight.

### Cluster-level results (the honest denominator)

Rows within a (sleeve, symbol, session) cluster are the same blocked intent re-rejected across cycles of one halt, sharing one forward return. Averaging within clusters first:

| horizon | pool | clusters | mean | median | t |
|---|---|---|---|---|---|
| 1 session | all | 126 | +0.92% | +0.62% | 1.67 |
| 1 session | entry-like | 43 | +0.30% | +0.30% | 0.34 |
| 1 session | exit-like | 87 | +1.25% | +0.91% | 1.82 |
| 3 sessions | all | 96 | -0.04% | -0.59% | -0.05 |
| 3 sessions | entry-like | 39 | -3.02% | -2.54% | -1.92 |
| 3 sessions | exit-like | 60 | +2.04% | -0.59% | 1.89 |
| 5 sessions | all | 14 | -1.08% | +0.08% | -0.36 |

Reading. At cluster level nothing clears a plain significance bar. The two 3-session leans (blocked entries protective at -3.02%, blocked exits costly at +2.04%, both t near 1.9) point the same way and deserve one honest sentence: during the halt window the halted names fell hard (per-symbol 3-session scores include VELO -30.2%, CRML -14.0%, HIVE -8.8%, HUT -7.2% against TEM +10.5%, SATL +13.1%, CLS +11.0%), so an indiscriminate block in a falling tape mechanically protects entries and strands exits. reconcile_halt by construction does not select intents; it blocks everything while the books disagree. The leans are a property of when the halt fired, not evidence of per-intent judgment in either direction. Concentration warning: SKYQ alone contributes 247 rows at a +29.8% mean 1-session score, a handful of clusters of one collapsing name, and it visibly moves the row-level exit-like mean while barely moving the cluster mean.

Classification limit, named: the fill ledger starts 2026-10-27 and 7,722 of its 8,928 fills are imported rows whose timestamps are import times. A position opened before the ledger start and closed by an imported sell could make an early row read entry-like when it was exit-like. The graded mass is 2026-11-07 to 2026-11-10, after the 2026-11-02 import batch settled, which bounds but does not erase this exposure. Classification here is ledger-visible position, stated as such.

## 3. The classes that cannot be graded

insufficient_slice_bp (760 rows, 17 sleeves, 2026-11-02 to 2026-11-15 UTC; top sleeves investandbefree_dmac_dailyonly, investandbefree_dmac, and investandbefree_dmac_premacd at 148 each, aster_etf_leader1_m150 at 103): directional grading is impossible from the persisted record. These rows carry no symbol, no side, no kind, and no reference price. Nothing about what was blocked can be recovered from the dispatcher log, the sleeve journals (which carry no symbol or side on intent and eval events either), or any other persisted per-intent payload, because full intent payloads are not persisted per intent. This is stated plainly as a record defect, not worked around.

Exit classes, census only, with the mechanical meaning of each:

- exit_already_resting_at_broker (11,931): bookkeeping. The exit order was already working at the broker when a duplicate exit intent arrived; rejecting the duplicate lost nothing, the exit was already in flight.
- exit_satisfied_no_broker_position (9,173): the sleeve journal believed it held a position, but the broker showed none, so there was nothing at the broker to sell and the exit intent was dropped as already satisfied on the broker side.
- exit_satisfied_no_sleeve_position (432): the sleeve's own book held no position, so the exit intent was a no-op against its own ledger and was dropped.
- exit_blocked_opposite_side_resting (7): an opposite-side order for the same symbol was already resting, and the exit was blocked rather than crossed against the sleeve's own working order.
- bad_qty (23) and bad_kind (11): malformed intent fields caught by validation before any order logic.

## 4. The payload finding and the cure

As a labeled corpus, the reject book labels 29,360 events with a reason and a sleeve, timestamps 29,101 of them through intent_id, and gives a tradable identity (symbol) to only 7,023. Side, kind, quantity, and reference price are absent from every reject row. Any future counterfactual grading of the other classes, and any cleaner grading of reconcile_halt that does not need ledger reconstruction, is blocked on the same single defect.

The cure, for the desk lane to land (not landed here; the desk tree was read only): dispatcher intent_rejected rows should stamp symbol, side, kind, and reference price on every reason class, plus an explicit event timestamp field so no consumer has to parse timestamps out of intent_id, and the legacy intent_id format should stop being emitted. Until that lands, D-01-style grading covers at most the reconcile_halt quarter of the reject book.

## 5. Verdict restated

- Does any graded class systematically reject winners? Not proven. reconcile_halt is the only gradeable class; at the independent-event (cluster) level its pooled effect is null at 3 sessions (-0.04%, t -0.05) and marginal at 1 session (+0.92%, t 1.67), and the 5-session horizon is unresolvable for 99.4% of its rows inside this window.
- Does the gate earn its keep? Not proven either. The weak 3-session cluster leans (entries protected, exits stranded, both t near 1.9) are what an indiscriminate halt produces in a falling tape; they credit the calendar, not the gate.
- The finding that stands without qualification is the payload finding in section 4: 76.1% of the reject book cannot be graded from what the desk persists, and that is fixable at one stamping site in the dispatcher.

## Artifacts

- V3-REJECT-COUNTERFACTUAL.md (this file)
- v3_rejects.jsonl: 29,360 parsed reject rows (intent_id, reason, sleeve, symbol, cash_halt, intent timestamp UTC, source file, discrepancy count)
- v3_grade.py: census, classification, fetch, and grading script, rerunnable end to end
- v3_results.json: full census detail, per-symbol grading, cluster statistics
- v3_bars.json: the fetched SIP split-adjusted daily bars for the 50 graded symbols

Rails observed: desk tree read only, no edits; no Tensor or saty contact (log records mentioning those sleeves were read as part of the assigned census, nothing was sent to or run on them); one heavy job at a time; no field fabricated, absences named as absences.
