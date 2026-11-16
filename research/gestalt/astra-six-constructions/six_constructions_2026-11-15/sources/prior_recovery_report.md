# Edge recovery and invention — 2026-11-15

This pass created new research machinery and new economic constructions, then tested them. Its most useful lead is a **relative crash recovery expressed as a cash altcoin position plus a BTC perpetual hedge**, conditional on a sharp negative market move. A second lead is **dispersion forecasting magnitude more consistently than direction**. A third is **changing the payoff and execution clock rather than rejecting an information signal because one expression loses money**.

These are research leads, not established deployable alpha. All historical periods were explored. Selecting an attractive combination from thousands of variants creates selection bias; the results below are event P&L, not funded portfolio returns. Every attempted configuration and the unattractive results remain saved.

**Overall status: PARTIAL against the owner's full all-repositories/all-history/live-engine objective.** The concrete invention, repair and preservation work below is delivered; exhaustive semantic inspection, missing host-only history, original equity-panel replay and live capture remain open. No profitable live system or complete day-one backup is asserted.

## What was built and executed

| Work | Executed scope | Evidence |
|---|---:|---|
| Shock/side/context/horizon invention grid | 3,456 registered configurations | master-desk `recovery/chaos_v2/` |
| Flow, path, disagreement and illogical controls | 216 configurations, including deliberate duplicates | `recovery/motifs_v2/` |
| Market sign, beta hedge and entry-delay decomposition | 27 post-search comparisons | `recovery/attribution.json` |
| Cash asset plus BTC perpetual expression | 27 post-search comparisons using actual archived perp prices and funding rates | `recovery/perp_expression.json` |
| Alternative option payoffs | 702 historical quote constructions across five symbols | `recovery/option_expressions.jsonl` |
| Prediction-market payoff arithmetic | 60 binary full-set size checks and 63 nested-threshold size checks | `recovery/prediction_financial/` |
| New economic designs | 32 detailed contracts | [inventions](https://github.com/dwj9ddyvf6-hub/cos2-estate/blob/research/edge-recovery-20261115/research/brainstorm/edge_recovery_2026-11-15/inventions.md) |
| Decisions API | 416 typed questions, two real requests, zero refusals, no mock | [review receipts](https://github.com/dwj9ddyvf6-hub/cos2-estate/blob/research/edge-recovery-20261115/research/brainstorm/edge_recovery_2026-11-15/decisions/review_summary.json) |

The counts are not independent strategies, independent statistical tests, or proven edges. Re-executing the corrected measurement version is not counted as another discovery. All 32 invention designs contain an observable input, proposed consequence, action/payoff, hypothesized payer, rival explanation and next experiment. They cover equities, microcaps, swing trading, options, crypto, ETFs, prediction markets, execution, portfolio risk and information processing.

## New empirical leads and the changes of lens that produced them

### 1. Separate an asset's shock from the market's shock, then separate market direction

The original raw-shock experiment buys a negative shock and waits. The new construction first subtracts a lagged rolling-beta market component, then distinguishes **negative market stress** from **positive market stress**. Those two states should not be lumped together merely because both have a large absolute market move.

The grid's raw crash/24h example CL-01465 has gross event means of 1.066%, 1.957%, and 1.284% in the three historical periods. The residual-shock/72h example CL-03226, conditional on a large absolute BTC move, has gross means of **1.881%, 2.587%, and 4.729%**. The latter has 130, 95, and 63 event rows. The last 63 events occupy 41 entry dates; treating them as 63 independent observations would exaggerate precision.

For the latest period, CL-03226's approximate calendar-HAC t is 3.06 and its seven-day moving-block bootstrap interval for gross event mean is [1.64%, 7.98%]. The interval is **not adjusted for selecting this example from the search**. The largest entry day's aggregate contribution is 26.5% of gross summed returns. Changing the block length to 3/14/28 days did not make this selected interval include zero, but those checks do not remove selection, universe or execution bias.

The economically revealing step was to hedge the market component. The broad absolute-stress variant becomes negative in the earliest period after a full beta hedge. The **negative-market-stress subset** retains positive average modeled P&L in all three periods. The positive-market-stress subset does not. This suggests two different mechanisms hiding under one label, not proof of one universal crash rule.

The Decisions review suggested funding/borrow evidence for this idea. That led to a further expression: a cash asset position and a BTC perpetual hedge, using downloaded perpetual prices and actual historical funding rates instead of assuming stock-like spot borrow.

| Same selected negative-market-stress events | Development period | 2023–2024 | 2025–Oct 2026 |
|---|---:|---:|---:|
| Available event rows with perp/funding data | 44 | 59 | 37 |
| Immediate next-bar entry, full beta hedge; modeled net P&L | **2.038%** | **1.269%** | **1.895%** |
| Entry delayed 12h, same original endpoint | 0.328% | -0.014% | 0.563% |

P&L is per initial dollar of the asset leg, not return on account equity or posted margin. Each leg is charged an assumed 20bp round-trip cost times its initial absolute notional. Historical funding uses trade-bar-open prices as a mark proxy; uncertain funding inclusion at the entry/exit instant uses the adverse endpoint treatment. This is not a mathematical lower bound on every real implementation cost. Margin calls, liquidation, spreads, impact, venue access and exact funding marks remain unmeasured. Twelve original events lack a complete perp/funding calendar and are explicitly listed; early-period samples therefore differ from the spot-hedge table.

**Constructive next step:** observe liquidation flow, open interest, depth recovery and actual quoted entry opportunities together. Test whether entry timing follows the disappearance of forced supply. Preserve the unhedged, partial-hedge, full-hedge and delayed variants; do not choose a live winner from this retrospective exercise.

### 2. Reverse the interpretation of a low-volume bounce

A weak-volume rebound is often dismissed as unconvincing. The alternative explanation is **supply exhaustion**: price can recover because less inventory is being offered, even without conspicuous buying volume.

MOT-080 buys a positive bar immediately after a large negative shock when volume declines. Its gross next-24h means are **0.678%, 1.189%, and 0.517%**, with 551/391/361 event rows. The latest approximate HAC t is only about 1.24. The three quantile settings are redundant for this motif and must not be counted as separate corroboration. This does not identify passive buying or forced selling: the next experiment must match market return and prior volatility and measure actual supply/flow.

A useful counterexample stays beside it: the simple aggressive-selling/rising-price mask changes direction in the latest period. Static flow disagreement alone has not supplied stable directional evidence here. A **two-step absorption/replenishment state machine** is a new preserved hypothesis, not a claim that the first weak result has been rescued.

### 3. Change the objective from direction to movement

For the dispersion-laggard motif, gross directional 24h means are **0.825%, 0.731%, and -0.053%**. The third period does not support the same long-direction story.

Absolute movement, however, is greater than its baseline in all three periods. Scaling absolute movement by prior own-asset RMS volatility times the square root of the horizon gives:

| Historical period | Motif normalized absolute movement | Baseline |
|---|---:|---:|
| 2019–2022 | 0.955 | 0.749 |
| 2023–2024 | 0.891 | 0.757 |
| 2025–Oct 2026 | 0.881 | 0.753 |

This is a volatility-information candidate. It is **not** evidence that a straddle makes money: implied volatility, skew, spread, hedging costs, different event sampling and funding must be compared over the same horizon. The invention is to keep the information and change its use: direction, magnitude, fill timing, or insurance valuation are different objectives.

### 4. Change the contract instead of generalizing from one option loss

The archive contains negative short-dated call examples, a deep-ITM example and a call-spread example. Those observations do not establish that every options expression fails. The new payoff compiler enumerates verticals, synthetics, straddles and calls partly financed by put spreads, buying at ask and selling at bid, and evaluates terminal knots plus unbounded tails.

One **historical geometry illustration**, not a current recommendation: the saved NVDA 2026-11-16 quotes price a long 165 call, short 165 put and long 157.5 put at a $1.12/share credit. Its modeled expiration loss is bounded at $6.38/share ($638 for the standard 100-share multiplier), with unlimited terminal upside. The credit is not profit. Interim assignment and margin needs are not bounded by that expiration-loss figure. Quote synchronization, executable size, fees, financing, exit marks and a horizon-matched distribution are missing.

The exact task is now reviewable: compare complete payoff and funding paths for the same underlying thesis. None of the 702 geometries has a positive modeled minimum expiration P&L after its quoted acquisition cost. This is a bounded result for one archived snapshot, not a universal options rejection.

### 5. Treat prediction-market rules as data

The first broad 100-market response contained no financial-keyword candidates. Expanding through the Crypto, Finance and Economy tags produced 272 unique records, of which 105 met the explicit financial-keyword/binary filter. Twenty markets supplied 40 orderbooks. This is transparent selection, not a market-wide survey.

A concrete semantic distinction: most captured Bitcoin year-end upside targets share a fixed start of **November 24, 2025, 14:00 ET**, while the $90,000 target uses **the creation of that market**. A headline-only monotonicity check can combine incompatible windows.

The new compiler admits only the independently read fixed-window BTC one-minute-high template with identical rule text. It modeled 21 threshold pairs. Buying lower-target YES plus higher-target NO has modeled terminal payouts [1,2,1] across below/between/above states, before acquisition cost. Depth is consumed at 1/10/100 shares; top-of-book size is not assumed unlimited.

No positive pre-fee modeled minimum was observed in the 60 same-market or 63 nested checks. Fees, non-atomic execution, collateral, oracle behavior and payment timing remain separate. Different clocks are preserved as unresolved relations, not forcibly made identical.

## Repair work and scientific accounting

Four grouped measurement defects in `tools/unlock/edge_r2.py` were demonstrated with failing-before tests and repaired on the research branch:

1. **Historical liquidity depended on the end of the cache.** Eligibility is now evaluated through the signal date, using the existing trailing-dollar-volume level; finite/current-volume requirements are explicit. Total-cache loading requires enough history to form features rather than the former 40-bar end-of-cache screen. This changes research sample construction, not live order eligibility.
2. **Three-day exhaustion returns were compared with a one-day benchmark.** Both legs now use the same three-day horizon and eligible universe.
3. **Nonfinite entry/exit prices could enter returns.** They are excluded explicitly; zero terminal equity value remains a possible valid loss.
4. **A supplied research root did not control output location.** Writes now stay under the supplied root instead of an import-frozen global output directory.

Existing numeric admission thresholds and falsifier dates were not silently relaxed. The registry currently supplies 4.26; older source commentary says 3.98. That mismatch is recorded in the gate audit. A registry of 148 hypotheses is not proof that the runner executes 148 independent studies.

A new pure exit kernel addresses three demonstrated problems in the archived R4 study design: labels crossing a train/test boundary, comparing different capital endpoints, and stop-first logic overriding a known opening gap through the target. It compares the same complete paths through a common endpoint, holds early-exit cash at zero interest, purges immature training labels and reports unordered intrabar double hits. It does not reproduce the old entire exit grid, trailing/ATR policies or a reinvested portfolio. The original full PIT panel was not recovered, so no corrected original-panel performance claim is made.

**A correction to this pass's own first run:** the rolling residual scale contains lagged 180-bar beta estimates. A 180-bar gap check was insufficient for its full nested dependency. Measurement v2 checks beta-lookback plus scale-lookback continuity. It changes 1,638 of 3,456 rows in the full historical result table. The original `chaos/` output is preserved as superseded; `chaos_v2/` is current. For CL-03226, the oldest-period mean changes from 1.264% to 1.881%; the two later-period means are unchanged. This correction also changes the early same-context comparison. It is not hidden as a new successful trial.

## What “freeze all research” means in this delivery

Seven original ref snapshots were preserved under named research/frozen branches and remotely read back equal. Their exact commit IDs are in [frozen_refs.json](https://github.com/dwj9ddyvf6-hub/cos2-estate/blob/research/edge-recovery-20261115/research/brainstorm/edge_recovery_2026-11-15/preservation/frozen_refs.json). These are ordinary branches, not protected immutable storage; the commit IDs are the precise references.

The corpus index includes **25,890 Git-tree entries**. Its coverage is **16,367 lexical searches**, **7,144 not materialized**, **2,271 indexed only**, **76 symlinks not followed**, and **32 credential-related paths excluded**. Lexical search is not semantic inspection. The targeted semantic ledger describes files and sections actually examined, while the inventory keeps gaps visible. The preserved register contains **2,797 source records**, not 2,797 unique validated strategies. Original definitions, evidence and historical labels remain in their frozen source commits.

Both retrieved nightly packet sets, November 14 and 15, were read and checked against their manifests: **20 packets, 14,671 member entries, zero hash mismatches**. The latest memory packet was inspected through its relevant extracted memory files. This does not prove that every historical conversation or every file on an inaccessible host is saved. The packet manifests themselves describe additional workspace backlog. No credential, sealed file or user-supplied API key was added to these research artifacts.

All new research code, full result tables, downloaded public raw inputs, source records, verification logs and invention records are saved in the research branches of master-desk and cos2-estate. The final save receipt is added after remote content read-back. Source archives are preserved in their original private repositories rather than copied wholesale between repositories.

## Decisions API contribution and its limits

The existing estate client was used with mock explicitly disabled and the official OpenAI endpoint. After the user supplied authentication, the initial configuration block was resolved. Two real calls returned **256 evidence-review answers and 160 constructive-transformation answers**, with no refusals. Client-reported usage cost totals **$0.01144515**; this is the client's calculation, not a billing-invoice reconciliation.

The first review did not support calling capture/costs established. It suggested funding/borrow acquisition for the relative-crash idea; that suggestion produced the new perpetual-expression data and experiment. The constructive pass proposed changing objectives/clocks for recovery ideas, payoff construction for options and magnitude, inventory for carry/ETF opportunities, and information pairs for earnings/source disagreement. The full answer distributions are retained. Their probabilities are model judgments, not market probabilities or evidence of alpha. No API answer promotes, kills, sizes or trades a sleeve.

The constructive model also returned near-unanimous “economic difference possible” answers. That optimistic pattern is not treated as validation. Its contribution is observable in experiments and specifications, not in the confidence of its wording.

## Sources and assumption discipline

[The source register](https://github.com/dwj9ddyvf6-hub/cos2-estate/blob/research/edge-recovery-20261115/research/brainstorm/edge_recovery_2026-11-15/source_register.json) distinguishes primary pages/abstracts read, official data used, inherited research, inaccessible pages and wrong citation candidates. BIS crypto carry and Brunnermeier–Pedersen liquidity spirals motivate a constrained-capital mechanism; they do not prove these event returns arise from it. OIC parity supports payoff relationships, with interest/dividend/exercise qualifications. Official Polymarket rules support the admitted state model. SEC fails-to-deliver guidance prevents confusing an outstanding settlement balance with new short sales or proof of naked shorting.

The attempted Blackwell page returned a block page despite HTTP 200. An attempted arXiv liquidation citation was actually a supernova paper, and an attempted NY Fed variance citation was a different subject. They remain in the capture record and are excluded from support. The NYSE URL attempted returned 404; auction findings here are inherited archived evidence, not sourced from that failed request.

No research can eliminate all assumptions. Here they are named and varied: seven currently surviving crypto symbols, Binance rather than original OKX data, 60/180-bar shock scales, thresholds 1.5/2/3, 4/24/72-hour horizons, trailing-beta definition, cost scenarios, historical period boundaries, calendar dependence model and entry/exit fill conventions. These are exploratory design choices and sensitivity axes, not universal economic laws. There is no automatic “no edge” verdict because a preferred threshold was not crossed.

## Verification and remaining acceptance work

The final source snapshot is hashed. A clean regular-file export excludes 76 original external symlinks and uses an isolated local compatibility path, not a live desk. Every new test module passes alone and with the affected set. The full `tests/` suite is compared with an unchanged baseline; exact results are in [verification_summary.json](https://github.com/dwj9ddyvf6-hub/cos2-estate/blob/research/edge-recovery-20261115/research/brainstorm/edge_recovery_2026-11-15/verification_summary.json). Existing host-database/feed dependencies remain failures, rather than being satisfied with fabricated live state. An initial unscoped root pytest collection aborted on a legacy module's import-time SystemExit; that log is preserved too.

| Acceptance item | State | What changes the state |
|---|---|---|
| Preserve seven named source snapshots and retrieved nightly packets | Verified within stated scope | Remote refs and packet hash receipts |
| New reproducible invention/experiment package | Delivered | Complete code, inputs, registries and results |
| Four grouped R2 measurement repairs | Tested in isolated research branch | Host review/deployment remains separate |
| Original R4 equity/PIT results recomputed | Open | Original complete panel, adjustments and delisting settlements |
| Every source file semantically understood | Open | Expand the explicit semantic ledger beyond targeted files; materialize the missing paths |
| Every day-one/host-only research item saved | Open | Reconcile and drain original host backlog; verify new packets |
| Decisions API used for this pass | Executed | Real request/response and usage receipts retained |
| Proven deployable trading alpha | Open | New prospective observations, executable costs/fills, portfolio/margin feasibility |
| Original live engines fixed/deployed and observed | Open | Authorized host environment and end-to-end execution proof |

**Handoff:** Proven: source preservation receipts, new historical calculations, payoff arithmetic, measurement fixes and bounded tests. Open: the all-history/all-sleeve semantic objective and executable forward capture. Next evidence that matters: timestamped forced-flow/depth observations and viable fills for the residual-crash expression, contemporaneous option surfaces for the magnitude signal, and the original PIT equity panel for the repaired exit comparison.
