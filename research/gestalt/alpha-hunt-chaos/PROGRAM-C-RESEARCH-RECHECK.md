# PROGRAM C: RESEARCH ARCHIVE RECHECK

Owner program, Sun 2026-11-15: the full research archive rechecked item by item for potential edge and alpha, through the Decisions API as a lens, nothing arbitrary, nothing assumed. Tiers are computed from each study's own printed record; the typed seats are a lens and a disagreement flag, never the tier. Every number below is computed from the register and the recorded seat runs by the build script; no number is typed by hand.

## Coverage

| Row | Count | Detail |
|---|---|---|
| Research directories located on disk | 202 | Live count of `~/workspace/research_notes/` this session |
| Enumeration of record (Consensus Lens Phase 0 MANIFEST) | 200 | MANIFEST froze Sat 2026-11-14 23:48 ET |
| Difference | +2 | Exactly the two directories created after the freeze, both in the Sun window: `abyss-dive-five-20261115`, `alpha-hunt-chaos-20261115`. No unexplained difference |
| Fri-Sun window directories | 18 | Dated 20261113 / 20261114 / 20261115 |
| Window directories excluded | 8 | Already itemized by the reexamination or program homes: options-wave3-20261114, options-wave4-20261114, x-strategies-20261114, x-strategies-20261114-2, decisions-api-leverage-20261114, abyss-dive-five-20261115, alpha-hunt-chaos-20261115, consensus-lens-examination-20261114 |
| Window standalone studies included | 10 | Covered by the reexamination only as enumeration, never itemized; named in the register by `window_included` |
| Non-window directories | 184 | 202 located minus 18 window |
| Corpus read, itemized | 194 | 184 non-window + 10 window-included; one register row per study |
| Units with no report text | 3 | desk-board-sample-20261110 (only the declined board.html sample), terminal-fresh-graphs-20261031 (empty directory), test-all-sleeves-20261029 (only upload_progress.json). All three read as NUMBERLESS with the absence printed |

## Method

- Extraction was mechanical: each directory's report or principal deliverables were digested to verbatim headline, evidence, verdict, trial and falsifier lines; the five-field reads (claim, evidence as printed, trial-count honesty, mechanism, falsifier state) were authored from that digest against the tier rules, and any field the record does not carry is printed as absent (NUMBERLESS, TRIAL-COUNT-UNSTATED) rather than filled in.
- Tier rules. LIVE CANDIDATE: an edge claim with printed numbers, a named mechanism, and a falsifier registered, armed, or already running forward, not resolved against. WATCH: an edge claim with some evidence but a missing falsifier, missing trial honesty, thin evidence, or external-only evidence. MACHINERY: no market-edge claim (infrastructure, method, audit, cure, or intelligence work). RESOLVED-AGAINST: the study's own falsifier or its own resolved sample spoke against it. UNGRADABLE-BLOCKED: an edge claim whose deciding data or test was never supplied or persisted.
- Seats (bank `program-c-research-recheck` v1.0, gpt-6-luna): 11 questions per study at full width: a mechanism-plausibility predicate, an adversarial most-likely-null predicate, a choice (null category for edge studies, primary function for machinery), an evidence-quality score, and seven lens predicates (hedge fund manager, professional swing trader, game theorist, gambler, prediction markets analyst, data analyst, quant). Full probability vectors are recorded in the runs file; the deliverable prints argmax and lens means.
- Utilization: packs were first attempted at 36 studies (396 questions); the organization's TPM (2,000,000/min) is shared with parallel program lanes and sat at 98%+ utilization, so the large packs 429'd and the run was resized to 12-study packs (132 questions, about 26K tokens requested), which fit the observed headroom; every pack then landed, four of them only after backoff retries of 60 to 420 seconds. A 429 was backed off and resumed throughout, never treated as a stop; the only local limit is the harness's 5,000 requests/day circuit breaker. The connections pass was likewise resized from one 76,529-token pack to 18-pair packs. Full vectors, pack hashes, usage and cost per call are in the runs files.
- Connections: candidate pairs were generated mechanically from shared rare terms across claims, evidence and mechanisms (130 pairs) plus 30 hand-seeded pairs from the authoring pass (23 of them new, 7 already found mechanically), 153 pairs total over 133 units, each seated with a corroboration and a contradiction predicate; 12 theme clusters were seated with a survival choice each.

## Tier census

| Tier | Count |
|---|---|
| LIVE CANDIDATE | 0 |
| WATCH | 19 |
| MACHINERY | 171 |
| RESOLVED-AGAINST | 3 |
| UNGRADABLE-BLOCKED | 1 |
| Total | 194 |

The limiting number, stated plainly: of the 23 units in the archive that carry a market-edge claim at all, **zero** grade LIVE CANDIDATE under the tier rules. 3 resolved against on their own falsifiers, 1 is blocked on data never supplied, and 19 sit at WATCH, every one of them missing at least one of: a run falsifier, a stated trial count, or a forward record. The archive's proven content is machinery: 171 of 194 units. Potential edge in this archive lives in the WATCH list below and in the connections, not in any finished claim.

### WATCH list (all 19, by seat lens mean)

| ID | Directory | Claim (short) | Lens mean | Plaus | Null |
| C131 | soxl-pmhigh-sleeve-and-variants-20261103 | SOXL premarket-high breakout: the replication reproduces exactly and shows a real modest edge; four pre-regist | 0.49 | 0.61 | 0.37 |
| C182 | trendspider-sso-opus-test-20261103 | SSO Opus 5.5 Swing 15m: replication on our own data of the vendor strategy as frozen | 0.47 | 0.62 | 0.43 |
| C100 | modern-options-trading-deep-dive-20261113-0046 | Modern options deep dive: earnings implied moves are systematically overpriced in aggregate (28,898 reports: p | 0.38 | 0.46 | 0.47 |
| C181 | trendspider-sso-opus-improve-20261103 | SSO Opus 5.5 Swing 15m improvement study: diagnostics split the baseline's profit engine from its bleed, and p | 0.34 | 0.53 | 0.64 |
| C180 | trendspider-soxl-pmhigh-test-20261103 | SOXL premarket-high breakout, hold to close: replication on our own data (the primary replication behind C131) | 0.34 | 0.48 | 0.51 |
| C179 | trendspider-bottom-catcher-teardown-20261111 | TrendSpider Bottom Catcher teardown program (Phase 0 REA reread): the vendor scanner's criteria extracted, wit | 0.33 | 0.23 | 0.78 |
| C009 | alpha-hunt-x10-dive-20261114 | Widest-breadth dive: closing/opening auction imbalance predictability is the highest-priority TEST; herding me | 0.31 | 0.53 | 0.68 |
| C007 | alpha-hunt-dive-four-20261114 | Six unentered territories scouted with falsifiers written first; narrow conditional intraday forms earn TEST,  | 0.31 | 0.60 | 0.61 |
| C021 | candlestick-pattern-evidence-20261008-0245 | Candlestick evidence review: engulfing patterns show significant profitability in FX majors and ML-screened 2- | 0.25 | 0.54 | 0.67 |
| C099 | milkman-trading-methodologies-20260926-2235 | Milkman methodology investigation: his systems are fully specified enough to code (Bilbo Box v2: Saty compress | 0.22 | 0.53 | 0.75 |
| C107 | options-frontier-scan-20261113-0101 | Options frontier scan (late 2026): textbook dispersion has become a capacity and crowding trade (JPM dispersio | 0.21 | 0.39 | 0.75 |
| C057 | ema-trend-system-evidence-20261008-0229 | Evidence base for three discretionary frameworks: EMA trend rules have modest academic support at longer EMAs, | 0.20 | 0.41 | 0.75 |
| C122 | saty-indicator-stack-20261021-2152 | Research report on the Saty indicator stack (Volume Stack, Pivot Ribbon, Phase Oscillator, ATR Levels) and its | 0.19 | 0.49 | 0.77 |
| C008 | alpha-hunt-dive-three-20261114 | Earnings-event primary sources are vendor artifacts, not evidence; the gated long calendar earns a twin-sleeve | 0.18 | 0.49 | 0.74 |
| C074 | ict-smc-liquidity-setup-evidence-20261008-0237 | ICT/SMC setup evidence base: liquidity sweeps are a real mechanism with an overstated narrative, FVG and SMT l | 0.16 | 0.37 | 0.79 |
| C086 | llm-chart-reading-github-20261007-2243 | LLM chart-reading evidence: vision models answer chart QA well (FinChart-Bench 76.6-84.3% for frontier models) | 0.15 | 0.26 | 0.80 |
| C056 | elliott-wave-phd-deep-dive-20261016-1907 | Elliott Wave PhD dive: the canon's three rules make any specified count falsifiable via invalidation prices, b | 0.14 | 0.34 | 0.79 |
| C025 | codex-forecast-variations-20261029 | Ausar's 30 forecast engines each carry a declared edge hypothesis card (mechanism, payer, price-aware baseline | 0.12 | 0.50 | 0.78 |
| C034 | decisions-trial-20261110 | Decisions API pilot: 100 live typed calls over the 2026-11-09 chart study's 100 entries; the disagreement stru | 0.11 | 0.27 | 0.73 |

### RESOLVED-AGAINST (3)

- **C018 biotech2k-rotation-tests-20261109**: Biotech2k sector rotation, swept over 197 cells in 6 families on 2017-2026 data, fails its own falsifier at the registered cell and the surviving cells are plateau/spike-classified, not promoted Falsifier record: RUN: registered cell failed its pre-registered bar (ratio 1.397 vs SPY 8.077); grid verdicts printed per cell (SURV/FAIL/UNTE)
- **C032 decisions-brainstorm-20261112**: Wave 1 typed-layer receipts: the rule-taxonomy sweep's falsifier TRIGGERED (typed judge agrees with the desk's own rule classes only 22.4% against a registered 80% bar), while other legs (exit census, forecast twin, visual second read) graded or carried forward Falsifier record: RUN: TRIGGERED on the first graded tranche for the taxonomy leg; the sweep claim is withdrawn on its own falsifier
- **C112 quantjourney-adoption-20261031**: EDGE spread estimator adoption study: REJECTED under kill criteria fixed before results; on a 14-name panel over 129 trading days the estimator's spreads diverge from real quoted spreads by orders of magnitude (SPY +2,325%) Falsifier record: RUN: the pre-registered kill criteria fired; verdict REJECTED is the falsifier's output

### UNGRADABLE-BLOCKED (1)

- **C105 onebar-family-2026-10-30**: One Bar family claim audit: the vendor's headline claims (profitable on NQ then three more indices with zero changes; equity curve to ~$210,000) are UNVERIFIED and uncheckable from the post (no trades, dates, data or code supplied), and the rules were still translated into three FED parked-false sleeves on $10,000 slices with the translation arithmetic done openly Blocker: None runnable: the claim carries no data to falsify against, which is the audit's finding

## Itemized per-study reads

Seat line key: PLAUS = mechanism-plausibility probability (machinery variant for M units); NULL = probability the most-likely-null is essentially correct; CAT = argmax of the null-category choice (E) or primary-function choice (M), with its probability; SCORE = argmax evidence-quality level, with its probability; LENS = mean of the seven lens predicates with min and max.

### C001 adoption-implementation-20261103 : MACHINERY (kind M)
- Claim: 55 extracted adoption items (30 ADOPT-WORTH + 25 homegrown) landed or staged across tools, skills, jobs and memory surfaces
- Evidence: Item ledger with per-item status: A-10 PARTIAL (selftest PASS, remainder named), A-12 PARTIAL, T-317 GREEN; cluster counts printed (skills 5/7/12)
- Trial honesty: UNSTATED (no sibling count applies; item census 55 is the denominator)
- Mechanism: ABSENT (process ledger, no edge mechanism claimed)
- Falsifier: None stated
- Seats: PLAUS 0.26 | NULL 0.61 | CAT bookkeeping (0.89) | SCORE assertion-only (0.78) | LENS mean 0.31 [0.22..0.50]

### C002 agent-troubleshooting-gaps-20261103-0400 : MACHINERY (kind M)
- Claim: AI agents fail mainly at hunk-level precision, reproduction and patch scope, and passing tests are a weak oracle for patch correctness
- Evidence: SWE-bench: agents localize the right file in 72-81% of failures; 29.6% of plausible Verified patches behaviourally incorrect; strengthened suites reject 19.78% of 'solved' patches; ungrounded reflection leaves 42.6% of failing programs unchanged
- Trial honesty: UNSTATED
- Mechanism: Named: reflection helps only when anchored to an external signal (test execution)
- Falsifier: None stated
- Seats: PLAUS 0.71 | NULL 0.28 | CAT measurement (0.62) | SCORE thin-or-external (0.65) | LENS mean 0.37 [0.35..0.39]

### C003 agentic-trade-desk-guide-20261029 : MACHINERY (kind M)
- Claim: An agentic trade desk works only with a single intent pipeline and dispatcher as the one broker door, with reconciliation gates before dispatch
- Evidence: NUMBERLESS as performance evidence (architecture doctrine with audit tests: broker submit/replace/cancel callable from exactly one module)
- Trial honesty: UNSTATED
- Mechanism: Named: single-writer discipline prevents unreconciled state
- Falsifier: None stated (audit tests specified, results not in this report)
- Seats: PLAUS 0.46 | NULL 0.71 | CAT safety (0.97) | SCORE assertion-only (1.00) | LENS mean 0.50 [0.49..0.50]

### C004 ai-basket-20261111 : MACHINERY (kind M)
- Claim: Wikipedia attention and the ChartsLector ranker can be refreshed nightly as conditioners for the 9-name AI basket (conditioner only, never a stance)
- Evidence: Per-name attention printed: MU 2,111 views, +29.8% trend; SNDK +17.3%; SOXX -24.8%; ranker refreshed 55 rows, zero fetch failures; pulse/breadth legs proven-stale at 2026-10-14 (named)
- Trial honesty: UNSTATED
- Mechanism: ABSENT by design (conditioner, no edge claimed)
- Falsifier: None stated
- Seats: PLAUS 0.19 | NULL 0.80 | CAT data (0.59) | SCORE thin-or-external (0.68) | LENS mean 0.17 [0.15..0.20]

### C005 ai-basket-20261112 : MACHINERY (kind M)
- Claim: Same conditioner program, 2026-11-12 edition: attention and ranker refreshed; basket sentiment swung 57.5 to 38.4 (fearful) with MU called constructive at 65.0
- Evidence: MU 1,903 views +36.4% trend; SNDK +24.4%; SOXX -19.5%; ranker 55 rows zero failures; stale legs named again
- Trial honesty: UNSTATED
- Mechanism: ABSENT by design (conditioner)
- Falsifier: None stated
- Seats: PLAUS 0.09 | NULL 0.78 | CAT data (0.51) | SCORE thin-or-external (0.81) | LENS mean 0.16 [0.15..0.17]

### C006 ai-basket-20261113 : MACHINERY (kind M, window-included)
- Claim: SIVE is measurable on its home exchange evidence: Nasdaq Stockholm close SEK 14.30 on 2026-11-13, -10.28% at the day low on 8.13M shares
- Evidence: Exchange record printed: close 14.30, range 14.13-15.68, volume 8,127,029; MU social evidence (Wikipedia 2,961 views, +36.4%)
- Trial honesty: UNSTATED
- Mechanism: ABSENT (evidence pack for an unmeasurable-on-book-routes name)
- Falsifier: None stated
- Seats: PLAUS 0.12 | NULL 0.82 | CAT data (0.70) | SCORE thin-or-external (0.94) | LENS mean 0.16 [0.13..0.19]

### C007 alpha-hunt-dive-four-20261114 : WATCH (kind E, window-included)
- Claim: Six unentered territories scouted with falsifiers written first; narrow conditional intraday forms earn TEST, buyback blackouts are real as calendar and weak as trade
- Evidence: Buyback: ~60% of programs keep buying through blackouts under pre-set plans; best index studies find no return difference blackout vs open; intraday friction accounted at 1-5bp index round trip; HLZ frame: 316 published factors, hurdle t>=3.0
- Trial honesty: STATED (multiple-testing frame declared: 316-factor catalogue, Bonferroni-equivalent ~3.7)
- Mechanism: Named per territory (forced flow, hedging flows, seasonality)
- Falsifier: Stated per territory (post-2020 data, real costs, shifted-signal control), not run
- Seats: PLAUS 0.60 | NULL 0.61 | CAT multiple-testing (0.74) | SCORE thin-or-external (0.53) | LENS mean 0.31 [0.27..0.33]

### C008 alpha-hunt-dive-three-20261114 : WATCH (kind E, window-included)
- Claim: Earnings-event primary sources are vendor artifacts, not evidence; the gated long calendar earns a twin-sleeve TEST and capacity ceilings must gate every anomaly's grade
- Evidence: 9,622-event straddle result traced to a vendor post; gated calendar traced to a YouTube video; index add/delete close dislocation 9-30bp; closing-auction reversal ~3bp gross, regime fragile; capacity ceiling: most anomalies worth under $1,000/day
- Trial honesty: UNSTATED (event count 9,622 is the vendor's, not an estate trial count)
- Mechanism: Named (capacity constraints, forced index flow, closing price pressure)
- Falsifier: Forward-test form stated (dollar profit at 1% and 5% of ADV participation caps), not run
- Seats: PLAUS 0.49 | NULL 0.74 | CAT data-artifact (0.47) | SCORE thin-or-external (0.99) | LENS mean 0.18 [0.16..0.20]

### C009 alpha-hunt-x10-dive-20261114 : WATCH (kind E, window-included)
- Claim: Widest-breadth dive: closing/opening auction imbalance predictability is the highest-priority TEST; herding measures earn TEST as a filter only; lunar refused, odd-lot flow TEST, vanna/charm refused as signals
- Evidence: Auction leg graded confidence B- (two independent sources support predictability of the auction move from displayed imbalance; no source proves net profitability at sub-$1M scale); herding C+ as filter
- Trial honesty: UNSTATED
- Mechanism: Named per territory (auction price discovery, herding cascades, crowding unwinds)
- Falsifier: Pre-registration forms stated (decile rule and cost assumption before first session; HERD-STATE-01 promotion needs 2 quarters of paper), not run
- Seats: PLAUS 0.53 | NULL 0.68 | CAT none-real (0.43) | SCORE thin-or-external (0.92) | LENS mean 0.31 [0.28..0.34]

### C010 ascension-research-deep-dive-two-20261114-2130 : MACHINERY (kind M, window-included)
- Claim: The sleeve fleet should be run as a strategy population: capped births, pre-registered kill rules, senescence planning on published decay rates, allocation computable from a table
- Evidence: Harvey-Liu-Zhu hurdle t>3.0; Hou-Xue-Zhang: 452 anomalies re-run under one method; N_eff formula over eigenvalues; dashboard of falsifiable population-health metrics specified
- Trial honesty: STATED (452-anomaly replication census and 316-factor catalogue carried as the trial frame)
- Mechanism: Named (winner-picking, cross-subsidisation drift, correlation externality)
- Falsifier: Population-health dashboard specified as falsifiable; not yet run at this report's date
- Seats: PLAUS 0.89 | NULL 0.50 | CAT bookkeeping (0.58) | SCORE large-insample (1.00) | LENS mean 0.54 [0.50..0.60]

### C011 audit3-execution-20261016 : MACHINERY (kind M)
- Claim: Execution engineering defect taxonomy: FIFO evaluation order is a defect whenever any member has a hard deadline; no pass-duration budget means no deadline claim; the real deadline is the broker cutoff, not the close
- Evidence: NUMBERLESS as performance evidence (defect classes A/B/D with per-class checks; price=0.0/stop=0.0 emission class named from this desk's own history)
- Trial honesty: UNSTATED
- Mechanism: Named per defect class (deadline arithmetic, state drift, grouping drift)
- Falsifier: Phase-2 falsifiable checks specified per finding; outcomes live in the desk lane, not this report
- Seats: PLAUS 0.80 | NULL 0.51 | CAT safety (0.96) | SCORE assertion-only (0.99) | LENS mean 0.48 [0.43..0.52]

### C012 audit3-meanrev-20261016 : MACHINERY (kind M)
- Claim: Canonical Connors RSI(2) specified exactly (200-day filter, Wilder vs Cutler RSI is critical, signal-close vs next-open entry changes the system), and most desk deviations are defect classes
- Evidence: Published system parameters printed (scale-in 10/20/30/40% on successive lower closes, exit RSI(2)>70, no stops in the published system); RSI(2)-family next-open vs signal-close aggregate differences reported from sources
- Trial honesty: STATED in source terms (published tests' universes named); estate trial count UNSTATED
- Mechanism: Named: short-term oversold bounces in uptrend names
- Falsifier: None run here (specification audit; verdicts belong to the sleeve lane)
- Seats: PLAUS 0.52 | NULL 0.47 | CAT measurement (0.52) | SCORE thin-or-external (0.87) | LENS mean 0.45 [0.39..0.49]

### C013 audit3-momentum-20261016 : MACHINERY (kind M)
- Claim: Momentum/breakout sleeve defect taxonomy: forming-bar look-ahead, signal-at-close vs next-bar execution, warm-up divergence and unadjusted prices are the highest-yield audit areas
- Evidence: Unadjusted 2:1 split reads as a fake -50% crash; ADX(14) first true value delayed by Wilder smoothing; Turtle sizing 2N stop with 1N ~ 1% equity; template turnover ~30-35% monthly, 0.5-1% annual cost drag at ~100% turnover
- Trial honesty: UNSTATED
- Mechanism: Named per defect class
- Falsifier: Falsifiable core checks listed for Phase 2 code review; not run in this report
- Seats: PLAUS 0.78 | NULL 0.62 | CAT safety (0.60) | SCORE assertion-only (0.87) | LENS mean 0.40 [0.36..0.46]

### C014 audit3-options-20261016 : MACHINERY (kind M)
- Claim: Options exit conventions audited: '50% profit' has three denominators and only one is doctrine; there is no broker-side stop on an Alpaca spread, so every spread stop is a desk-side construct
- Evidence: Alpaca order classes simple only for options; stop/stop_limit single-leg only (platform documentation); 50%/21-DTE shown structure-specific, not a platform law
- Trial honesty: UNSTATED
- Mechanism: Named per finding (denominator drift, roll risk increase, settlement mechanics)
- Falsifier: None stated (findings are platform facts and code-audit checks)
- Seats: PLAUS 0.27 | NULL 0.52 | CAT safety (0.89) | SCORE assertion-only (0.72) | LENS mean 0.36 [0.29..0.42]

### C015 audit3-synthesis-20261016 : MACHINERY (kind M)
- Claim: Gestalt synthesis must not add correlated signals as independent votes; fixed simple weights are the benchmark to beat and context voices belong in a meta-labeling shape, never in the score
- Evidence: Breakeven win-rate arithmetic printed (p > 1/(1+b)); deflated-Sharpe trial-family accounting required (configurations counted, Sharpe deflated); PNAS aggregation evidence cited
- Trial honesty: STATED (trial-family counting and deflation required as method; the audit's own family size not enumerated)
- Mechanism: Named (shared-information distortion in aggregation, double counting)
- Falsifier: Frozen-record requirement stated (an unfrozen synthesis is unfalsifiable); no estate falsifier run in this report
- Seats: PLAUS 0.87 | NULL 0.44 | CAT safety (0.49) | SCORE assertion-only (0.86) | LENS mean 0.46 [0.37..0.53]

### C016 audit3-voldef-20261016 : MACHINERY (kind M)
- Claim: Volatility/defensive construction rules: long VXX decays by construction, hedge sizing must be by crisis payoff not premium spent, parked cash is not buying power until sold and accounted, SGOV dominates BIL/SHV for true bill exposure
- Evidence: SGOV fee 0.09%, duration 0.10yr; SHV duration ~0.33yr (~4x SGOV); bill yields ~3.6-3.7% 30-day SEC; Antonacci GEM 2022: AGG fell ~13% as 'safe haven'
- Trial honesty: UNSTATED
- Mechanism: Named (contango decay, crisis beta, settlement lag)
- Falsifier: None stated (construction rules with inspect-and-recompute checks)
- Seats: PLAUS 0.30 | NULL 0.67 | CAT safety (0.85) | SCORE thin-or-external (0.72) | LENS mean 0.33 [0.29..0.39]

### C017 best-setups-fix-best-practices-20261016-1736 : MACHINERY (kind M)
- Claim: Best Setups board redesign: setups carry measurable pre-declared states (extended = >5% above buy zone), every card is born with an expiry, and sub-1 R:R must print its breakeven win rate
- Evidence: IBD conventions (buy zone ends +5%, cut at 7-8%, profits 20-25%); 0.35R first target implies 74.1% breakeven win rate before costs (1/(1+R)); default card time-box 5 trading days, 10 maximum
- Trial honesty: UNSTATED
- Mechanism: Named (disclosure discipline, spliced-fact prevention by structure)
- Falsifier: None stated
- Seats: PLAUS 0.87 | NULL 0.58 | CAT safety (0.49) | SCORE assertion-only (0.88) | LENS mean 0.50 [0.45..0.55]

### C018 biotech2k-rotation-tests-20261109 : RESOLVED-AGAINST (kind E)
- Claim: Biotech2k sector rotation, swept over 197 cells in 6 families on 2017-2026 data, fails its own falsifier at the registered cell and the surviving cells are plateau/spike-classified, not promoted
- Evidence: Benchmarks same window: SPY +272.97% (return/maxDD 8.077), QQQ +459.40% (13.125); registered cell W252/gate-both/top-3 RS ratio 1.397, +54.65%, FAILS the SPY 8.077 bar; options cells MODELED (Black-Scholes, IV proxy 1.15x realized); 'do not sell strength' lever nearly triples OPT-B2K-1 ratio 1.08 to 3.12
- Trial honesty: STATED (197 cells enumerated by family: 56+36+42+36+9+18; plateau-vs-spike rule frozen before reading)
- Mechanism: Named (relative-strength sector rotation; rank-1 exit removes the strongest name too early)
- Falsifier: RUN: registered cell failed its pre-registered bar (ratio 1.397 vs SPY 8.077); grid verdicts printed per cell (SURV/FAIL/UNTE)
- Seats: PLAUS 0.54 | NULL 0.78 | CAT multiple-testing (0.63) | SCORE resolved-forward (0.73) | LENS mean 0.14 [0.11..0.18]

### C019 blocked-feeds-fixes-research-20261021-0140 : MACHINERY (kind M)
- Claim: Blocked data feeds have lawful self-serve routes: Alpaca OPRA historical trades/quotes, FINRA short interest at $0 via the API Console, Databento for ES history
- Evidence: Endpoint-level facts printed (feed=opra routes, historical trades accessible older than 15 min on all feeds; FINRA Rule 4560 twice-monthly cadence; vendor price table Oct 2026)
- Trial honesty: UNSTATED
- Mechanism: Named (entitlement routes, not market mechanism)
- Falsifier: None stated
- Seats: PLAUS 0.60 | NULL 0.63 | CAT data (0.84) | SCORE thin-or-external (0.63) | LENS mean 0.16 [0.12..0.20]

### C020 book-strip-cure-20261109 : MACHINERY (kind M)
- Claim: Book-strip publish collisions are a GitHub concurrency-semantics problem; candidate cures graded ADOPT/AMEND/REJECT each with a falsifier
- Evidence: Contents API optimistic concurrency via sha (409 on mismatch); REST points budget 900/min, mutative ~180 req/min ceiling; tree chunking at <=1,000 entries per field cure
- Trial honesty: UNSTATED
- Mechanism: Named (optimistic concurrency, fast-forward-only ref updates)
- Falsifier: Stated per candidate (e.g. 14-day instrumented trial of offset+jitter with zero collisions would prove a rejection wrong); trial outcome not in this report
- Seats: PLAUS 0.71 | NULL 0.47 | CAT safety (0.96) | SCORE assertion-only (0.89) | LENS mean 0.12 [0.09..0.16]

### C021 candlestick-pattern-evidence-20261008-0245 : WATCH (kind E)
- Claim: Candlestick evidence review: engulfing patterns show significant profitability in FX majors and ML-screened 2-day patterns in China, but the general candlestick canon is contradicted as often as supported
- Evidence: Engulfing across 24 FX pairs 2000-2018 significant, esp. 7 majors (European Journal of Finance 2020); Lin/Liu 2021: filtered 2-day patterns 36.73% avg annual return, Sharpe 0.81, IR 2.37 after costs (external samples)
- Trial honesty: UNSTATED (external studies' trial frames not enumerated)
- Mechanism: Mixed: named sources both ways; confluence-not-alone hypothesis examined
- Falsifier: None run on estate data (literature review); the estate's own pattern ledger is the deciding instrument
- Seats: PLAUS 0.54 | NULL 0.67 | CAT multiple-testing (0.48) | SCORE thin-or-external (1.00) | LENS mean 0.25 [0.23..0.27]

### C022 chart-reading-mastery-and-annotation-cra-20261015-2352 : MACHINERY (kind M)
- Claim: Classical chart patterns carry published base rates (Bulkowski) strong enough to encode as reading rules, and annotation craft is itself a measurable discipline
- Evidence: Bulkowski table with sample counts: cup-with-handle 913 samples, 5% failure, +54% avg rise; Eve&Eve double bottom 952, 12% failure; head-and-shoulders top >2,800, 19% failure; symmetrical-triangle breakouts ~74% of the way to apex, upward 60%
- Trial honesty: STATED in source terms (per-pattern sample counts printed, 759 to >2,800); estate trial count UNSTATED
- Mechanism: Named (pattern completion statistics, Wyckoff cause/effect)
- Falsifier: None run on estate data; time-box retirement rules specified for patterns that drift into the apex
- Seats: PLAUS 0.23 | NULL 0.66 | CAT measurement (0.79) | SCORE thin-or-external (0.83) | LENS mean 0.32 [0.29..0.34]

### C023 cloudflare-login-options-20261108-0358 : MACHINERY (kind M)
- Claim: Cloudflare dashboard sign-in failure after Google SSO has ranked, sourced causes and a lawful recovery path (email/password via reset)
- Evidence: Official-docs-backed answers on Q1/Q2/Q4/Q5 (high confidence stated); Q3 error string undocumented, ranking is inference from Community threads (named as such)
- Trial honesty: UNSTATED
- Mechanism: Named (social-linkage unlinking on email change)
- Falsifier: None stated
- Seats: PLAUS 0.09 | NULL 0.57 | CAT safety (0.47) | SCORE thin-or-external (0.96) | LENS mean 0.05 [0.05..0.06]

### C024 cloudflare-optimal-estate-20261109-0432 : MACHINERY (kind M)
- Claim: Cloudflare can carry this estate's off-host infrastructure (Tunnel + Access, Queues, cron staleness checks) inside free-tier limits if token scopes and Zero Trust onboarding are done in the right order
- Evidence: Queues free tier 10,000 operations/day, 24h retention; cloudflared unit Restart=on-failure/RestartSec=5s; SPF single-record and 10-lookup rules; failure modes enumerated (scoped token cannot create tunnels)
- Trial honesty: UNSTATED
- Mechanism: Named per component
- Falsifier: None stated
- Seats: PLAUS 0.30 | NULL 0.54 | CAT data (0.51) | SCORE assertion-only (0.88) | LENS mean 0.16 [0.13..0.18]

### C025 codex-forecast-variations-20261029 : WATCH (kind E)
- Claim: Ausar's 30 forecast engines each carry a declared edge hypothesis card (mechanism, payer, price-aware baseline), and Midna's 30-engine set has no plain trend-persistence engine by design
- Evidence: Engine-by-engine map FE01-FE30 against Midna's E-set: FE01 multi-horizon trend persistence (5-20 sessions, no counterpart), FE02 regime-gated residual reversion, FE18 PEAD after controls, FE19 consensus revision diffusion (no counterpart); evaluation machinery lists Brier/log-loss/QLIKE/AUC and Benjamini-Hochberg control
- Trial honesty: UNSTATED (30 engines enumerated; no resolved grades in this report)
- Mechanism: Named per engine on its edge card (hypothesized payer declared)
- Falsifier: None run in this report (analysis of his package; grades live in his ledger)
- Seats: PLAUS 0.50 | NULL 0.78 | CAT none-real (0.48) | SCORE assertion-only (0.99) | LENS mean 0.12 [0.10..0.20]

### C026 codex-shipyard-live-terminal-20261029 : MACHINERY (kind M)
- Claim: The Codex shipyard live-terminal branch is a real, attended-only live terminal (versions 452-454 verified against production) whose save is a partial backup missing the source half
- Evidence: Branch read end to end via GitHub API; no cron/scheduled handler/Durable Object, so streams stop when the page closes (its own README and audit state this)
- Trial honesty: UNSTATED
- Mechanism: ABSENT (inspection report)
- Falsifier: None stated
- Seats: PLAUS 0.05 | NULL 0.50 | CAT presentation (0.42) | SCORE assertion-only (0.98) | LENS mean 0.12 [0.09..0.14]

### C027 codex-terminal-deep-pass-20261029 : MACHINERY (kind M)
- Claim: Deep-pass inventory of the Codex terminal: FE01-FE30 engines, forecast machinery, Trade Brain and Alpaca machinery catalogued with parameters as coded and failure behaviour per mechanism
- Evidence: Coverage ledger printed (repos and shas enumerated, exclusions named: workspace-backup 209 entries sweep-only); mechanism tables M05 abstention audit, M12 source clock with inputs and state per row
- Trial honesty: UNSTATED
- Mechanism: Named per mechanism row (what it computes or enforces)
- Falsifier: None stated
- Seats: PLAUS 0.65 | NULL 0.50 | CAT measurement (0.62) | SCORE assertion-only (0.98) | LENS mean 0.39 [0.23..0.50]

### C028 compute-memory-money-20261110 : MACHINERY (kind M)
- Claim: GLORY program build record, containing the estate's fullest typed-layer corpus grade: on 100 items the Decisions stage leg beat the always-none baseline by +13 rows while the verdict leg showed no demonstrated skill (+0)
- Evidence: Stage 60/100 vs always-'none' 47/100 = +13 rows (grew from +9 at n=24); verdict 55/100 vs always-WATCH 55/100 = +0; forecast refresh runner and desk scheduler fixture-proven GREEN; live desk cycle BLOCKED by design at this pass
- Trial honesty: STATED (n=100 corpus with named baselines; stage and verdict legs separated)
- Mechanism: Named (typed classification as a disagreement flag and staging aid, not a verdict source)
- Falsifier: Eight-week falsifier registered for the program (register it reads named as not run tonight)
- Seats: PLAUS 0.82 | NULL 0.07 | CAT measurement (0.74) | SCORE large-insample (0.97) | LENS mean 0.39 [0.31..0.44]

### C029 compute-memory-money-ascension-20261110-2203 : MACHINERY (kind M)
- Claim: Deep research synthesis: verifier-filtered self-improvement compounds while unfiltered self-training collapses, and most published anomalies fail honest replication, so the estate's edge must be breadth x low correlation x combination x cost internalisation
- Evidence: Hou-Xue-Zhang: 452 anomalies, 65% fail t>=1.96, ~82% fail the multiple-testing hurdle; McLean-Pontiff: 97 predictors 26% lower OOS, 58% lower post-publication; FinMem return falls ~72% across the training cutoff; LongMemEval Zep 71.2 vs full-context 60.2
- Trial honesty: STATED (452-anomaly and 97-predictor censuses carried as the frame)
- Mechanism: Named (verifier filtering, temporal contamination, publication arbitrage)
- Falsifier: None stated (synthesis); its checklist is the falsifiable residue
- Seats: PLAUS 0.23 | NULL 0.52 | CAT measurement (0.60) | SCORE large-insample (0.87) | LENS mean 0.27 [0.23..0.33]

### C030 decision-standard-20261104 : MACHINERY (kind M)
- Claim: Program record of the Decision Analysis Standard build (2026-11-04): deliverable computed and cross-referenced into the book's chart study
- Evidence: NUMBERLESS in this record (the computed standard lives in midna-book/DECISION-STANDARD.md; this file is the program's provenance and verification record)
- Trial honesty: UNSTATED
- Mechanism: ABSENT (program record)
- Falsifier: None stated
- Seats: PLAUS 0.10 | NULL 0.53 | CAT measurement (0.31) | SCORE assertion-only (1.00) | LENS mean 0.33 [0.15..0.47]

### C031 decisions-api-incorporation-study-20261110-1857 : MACHINERY (kind M)
- Claim: Science review for incorporating LLM probabilities as forecasts: silicon-crowd Brier is statistically indistinguishable from human crowds, acquiescence bias is real and mitigated by asking predicates in both polarities, and mined Sharpe ratios need ~50% haircuts with DSR>0.95 as the significance convention
- Evidence: Schoenegger 2024: 12-LLM ensemble Brier 0.20 vs human crowd 0.19, p=0.850, n=31 questions; Whelan 2026: 143 post-cutoff questions, base rate 36.4%; Harvey-Liu haircut ~50%; Bailey-Lopez de Prado DSR>0.95
- Trial honesty: STATED (143-question and 31-question benchmarks enumerated with base rates)
- Mechanism: Named (acquiescence bias, alpha decay by exploitation, calibration structure)
- Falsifier: None run in this report (the estate pilot it builds on is decisions-trial-20261110)
- Seats: PLAUS 0.71 | NULL 0.52 | CAT measurement (0.91) | SCORE thin-or-external (0.88) | LENS mean 0.39 [0.34..0.46]

### C032 decisions-brainstorm-20261112 : RESOLVED-AGAINST (kind E)
- Claim: Wave 1 typed-layer receipts: the rule-taxonomy sweep's falsifier TRIGGERED (typed judge agrees with the desk's own rule classes only 22.4% against a registered 80% bar), while other legs (exit census, forecast twin, visual second read) graded or carried forward
- Evidence: Agreement 436/1,943 = 22.4% vs 80% bar and below the degenerate always-SOURCED baseline 69.8%; per class ARBITRARY 93.5%, SOURCED 5.1%, ILLOGICAL 3.0%; program spend $0.099146; exit-census typed leg perfect-arm proof 38/38 on its graded denominator
- Trial honesty: STATED (1,943 graded rule instances; falsifier bar pre-registered at 80%)
- Mechanism: Named (the judge calls nearly everything ARBITRARY; class semantics diverge between desk ledger and typed seat)
- Falsifier: RUN: TRIGGERED on the first graded tranche for the taxonomy leg; the sweep claim is withdrawn on its own falsifier
- Seats: PLAUS 0.09 | NULL 0.86 | CAT none-real (0.40) | SCORE resolved-forward (0.79) | LENS mean 0.07 [0.05..0.10]

### C033 decisions-incorporation-20261110 : MACHINERY (kind M)
- Claim: The full-incorporation study: the typed layer's demonstrated excess lives in classification (stage), not verdicts; every incorporation program is built with a falsifier and a proof event, and simple averages beat fitted optimal weights out of sample
- Evidence: Pilot graded 57/100 exact on stage with 42 of 43 misses leaning exactly one class; 9.2 GB daily bar store 2016 onward as the resolution tape; the 197-cell biotech sweep cited as the qualifier-space enumeration model
- Trial honesty: STATED (100-item pilot corpus; running trial count of every posed family required by its own architecture)
- Mechanism: Named (classification excess vs verdict parity; reliability loss eating fitted-weight gains)
- Falsifier: Stated per program with proof dates; runs belong to the later wave receipts
- Seats: PLAUS 0.84 | NULL 0.21 | CAT measurement (0.90) | SCORE large-insample (0.77) | LENS mean 0.36 [0.30..0.39]

### C034 decisions-trial-20261110 : WATCH (kind E)
- Claim: Decisions API pilot: 100 live typed calls over the 2026-11-09 chart study's 100 entries; the disagreement structure between seat and book is the finding, with stage classification the leg that later proved excess
- Evidence: Thin report (3,130 chars digested): 100 entries, verdict choice among CARRY/CARD/ACTIVE-WATCH/WATCH/PASS graded against the book's own stated verdicts; full grading deferred to Friday B5 in its own text
- Trial honesty: STATED (100 posed items, corpus declared)
- Mechanism: Named (seat as second reader; disagreement as signal)
- Falsifier: Not run inside the pilot; the full-corpus grade landed in the GLORY lane (stage +13, verdict +0 at n=100)
- Seats: PLAUS 0.27 | NULL 0.73 | CAT none-real (0.43) | SCORE thin-or-external (0.73) | LENS mean 0.11 [0.08..0.14]

### C035 deep-dive-repair-20261030 : MACHINERY (kind M)
- Claim: Broker order validation and reconciliation design research: Alpaca 422s are deterministic payload verdicts whose message string is the diagnostic of record, and acceptance is not a terminal state
- Evidence: Async rejection delivered on the trade-events stream, not the POST response; idempotency via client_order_id carried across retries; saty_sol pin re-verified in-pass (sha256 36e306c...bdc)
- Trial honesty: UNSTATED
- Mechanism: Named per defect (discarded error bodies, restart without fill import, id truncation)
- Falsifier: None stated (design research ending in falsifiable Phase-2 checks)
- Seats: PLAUS 0.63 | NULL 0.53 | CAT safety (0.97) | SCORE assertion-only (0.90) | LENS mean 0.35 [0.29..0.45]

### C036 deep-panel-acquisition-20261029 : MACHINERY (kind M)
- Claim: DEEP forecast panel acquisition: the engines require 750-813 sessions per name; the held panel (1,833 names at <=403 sessions) could never fire them, and the landed panel (1,773 names at >=813 sessions, SPY 2,973) clears the floor, with the engines still dark for runtime reasons, not data
- Evidence: Per-name floors from code (MIN_SESSIONS 750; first possible forecast 813); landed panel counted name by name; engine exits record 137 (killed) in engine3.exit and engine15.exit
- Trial honesty: UNSTATED
- Mechanism: Named (session-floor starvation; batch failure on one invalid symbol, cured)
- Falsifier: None stated (acquisition investigation with gaps stated exactly)
- Seats: PLAUS 0.49 | NULL 0.50 | CAT data (0.91) | SCORE assertion-only (0.83) | LENS mean 0.24 [0.19..0.30]

### C037 deepinfer-teardown-20261101 : MACHINERY (kind M)
- Claim: DeepInfer inference-path teardown: every claim about the engine's scheduling, sampling and MoE routing verified or refuted at file:line in the pinned tree
- Evidence: Verdict table per claim (CONFIRMED on code/artefact presence); step discipline (a step is prompt or decode, never mixed) traced to scheduler source lines
- Trial honesty: UNSTATED
- Mechanism: Named per component (zero-overhead scheduling, EPLB routing, DeepGEMM mega-kernel)
- Falsifier: None stated (teardown verdicts are the resolution)
- Seats: PLAUS 0.13 | NULL 0.50 | CAT intelligence (0.73) | SCORE assertion-only (0.85) | LENS mean 0.14 [0.12..0.19]

### C038 delegated-rulings-execution-20261031 : MACHINERY (kind M)
- Claim: Delegated rulings execution record: Week Ahead macro calendar v2 GREEN; Tensor daily20 pipeline carried PARTIAL with one BLOCKED row, later finalized and proven in the serve addendum
- Evidence: Process-level proof states printed (dispatcher pid and watchdog status at cycle reads); verdicts follow the no-green-without-final-state rule in its own text
- Trial honesty: UNSTATED
- Mechanism: ABSENT (execution record)
- Falsifier: None stated
- Seats: PLAUS 0.15 | NULL 0.51 | CAT safety (0.62) | SCORE assertion-only (0.98) | LENS mean 0.16 [0.13..0.20]

### C039 desk-board-sample-20261110 : MACHINERY (kind M)
- Claim: No study claim: the directory holds only board.html (30,831 bytes), the desk-board sample widget artifact
- Evidence: NUMBERLESS (no report file exists in the directory; single HTML artifact)
- Trial honesty: UNSTATED
- Mechanism: ABSENT
- Falsifier: None (no claim to falsify)
- Seats: PLAUS 0.04 | NULL 0.60 | CAT presentation (0.93) | SCORE assertion-only (0.97) | LENS mean 0.01 [0.00..0.03]

### C040 desk-defect-fixes-research-20261016-1439 : MACHINERY (kind M)
- Claim: Four desk production defects researched to fixes: local buying-power pre-check with size-down-or-queue disposition, options-hours gating, live-state test hangs, silent scheduled-job death
- Evidence: Alpaca BP computation basis per session documented; the stale-BP failure mode quantified by shape (24 positions' orders validating against one pass-level figure); Freqtrade protections pattern named as the reusable pause shape
- Trial honesty: UNSTATED
- Mechanism: Named per defect (reserved BP omitted, exits blocked by entry breakers)
- Falsifier: None stated
- Seats: PLAUS 0.37 | NULL 0.52 | CAT safety (0.91) | SCORE assertion-only (0.74) | LENS mean 0.28 [0.22..0.36]

### C041 desk-defect-optimal-fixes-20261023-0446 : MACHINERY (kind M)
- Claim: Optimal-fix research for wedged worker passes, a 633 MB append-only JSONL ledger, and diverged git mirrors: one propagated deadline object, soft-deadline terminal records, API-only mirror convergence
- Evidence: Concrete budgets printed (PASS_BUDGET 600, GRACE 15; DB statement_timeout 8s, lock acquire 2s); heartbeat failure modes enumerated both directions (work-thread heartbeat hides wedges, timer-thread heartbeat proves only the interpreter)
- Trial honesty: UNSTATED
- Mechanism: Named per defect
- Falsifier: None stated
- Seats: PLAUS 0.69 | NULL 0.50 | CAT safety (0.79) | SCORE assertion-only (0.95) | LENS mean 0.21 [0.20..0.24]

### C042 desk-efficiency-enhancements-20261019-20261019-1543 : MACHINERY (kind M)
- Claim: Desk efficiency research: the append-only market-facts store (~540 MB, ~140 files, 76% of desk state) is the leanness problem; snapshot publication and producer-liveness patterns drawn from mature open-source systems
- Evidence: State census printed (540 MB / ~140 files / 76%); SQLite retention semantics (DELETE frees pages, VACUUM reclaims); Freqtrade reconciliation cost O(open trades); Alpaca paper fill semantics verified live (NBBO fills, random 10% partials, no impact model)
- Trial honesty: UNSTATED
- Mechanism: Named per pattern (dirty-flagging, content hashing, per-producer freshness registry)
- Falsifier: None stated
- Seats: PLAUS 0.72 | NULL 0.55 | CAT data (0.39) | SCORE assertion-only (0.50) | LENS mean 0.26 [0.21..0.31]

### C043 desk-execution-hardening-research-20261018-2320 : MACHINERY (kind M)
- Claim: Desk execution-hardening research: every intent must reach a terminal accounted state and no open position may lack a working exit, on a ~60-sleeve shared Alpaca paper account
- Evidence: Alpaca facts printed (GET /v2/orders defaults status=open limit=50 max 500; options_buying_power separate with level gates); SIP vs IEX scale example (AAPL 2023-09-29: IEX 12,630 trades vs SIP 535,136)
- Trial honesty: UNSTATED
- Mechanism: Named (recurring reconciliation notices vanished exits; rejection classification retryable vs never)
- Falsifier: None stated (properties specified as inspectable invariants)
- Seats: PLAUS 0.62 | NULL 0.47 | CAT safety (0.94) | SCORE assertion-only (0.70) | LENS mean 0.26 [0.21..0.30]

### C044 desk-hardening-research-20261104-0538 : MACHINERY (kind M)
- Claim: Hardening research at 337 sleeves on one shared account: liveness and progress heartbeats are different instruments and must be separate threads, and GTC does not rescue market orders
- Evidence: Heartbeat design table printed (liveness sidecar 10-30s atomic rename; progress heartbeat at phase boundaries with cycle fields); Alpaca GTC limit-only fact for options market orders
- Trial honesty: UNSTATED
- Mechanism: Named (fork+exec spawn safety, per-task timeout and worker recycling)
- Falsifier: None stated
- Seats: PLAUS 0.28 | NULL 0.51 | CAT safety (0.94) | SCORE assertion-only (0.92) | LENS mean 0.26 [0.20..0.38]

### C045 desk-machinery-clean-20261104 : MACHINERY (kind M)
- Claim: Machinery clean pass on muse-desk-v3: runner instability root-caused and cure live-proven, SPY put exit pile-up dispositioned by broker truth, the -$176.85 reconcile gap composed exactly
- Evidence: End states printed for the 16 night-inspection items; zero PF_ wire rows on 2026-11-04 dispatcher rows sampled after the cure; reconcile figure composed to the cent in its own section
- Trial honesty: UNSTATED
- Mechanism: Named (dispatch pre-flight fence is containment, not the cure, in its own words)
- Falsifier: None stated (cure record with live proof states)
- Seats: PLAUS 0.51 | NULL 0.20 | CAT safety (0.95) | SCORE assertion-only (0.88) | LENS mean 0.27 [0.23..0.32]

### C046 desk-readiness-20261104 : MACHINERY (kind M)
- Claim: Desk readiness landing-pass patch specs: scripted config edits, CSP preflight, drain hold and pending hygiene, fill-sweep batching, daily20 pool isolation
- Evidence: Spec-level record (order queries paged at limit=500, closed-status paging to 4 pages); six free_kraken rows parked with reasons asserted in tests
- Trial honesty: UNSTATED
- Mechanism: Named per patch (staleness of the public copy, drain hygiene)
- Falsifier: None stated (patch specs; proof lives in the gate and BUGLOG of the landing pass)
- Seats: PLAUS 0.36 | NULL 0.55 | CAT safety (0.79) | SCORE assertion-only (0.99) | LENS mean 0.36 [0.22..0.48]

### C047 desk-readiness-20261112 : MACHINERY (kind M)
- Claim: Enter/exit coherence census of all 339 sleeves: entry proven for 63, invalidations dead on 20, closes landing beyond own lots on 44, and the roster's closed-trade record is far thinner than its firing record
- Evidence: Census counts printed: Entry PROVEN 63 (62 with live fills + 1 fixture-proven); Invalidation DEAD 20; health roll FED 230 / UNFED 55 / PARKED 54; board 2026-11-12 pre-open: LIVE-FIRING 62, ARMED-PROVEN 99, DEFECT 60, UNFED 63, PARKED 54; tensor_swing 3,638 attributed fills with zero own-lot closes; donchian55's 8 closes are lots of one CORZ fill
- Trial honesty: STATED (339-row census is the denominator; prior 192 figure reconciled in its own section)
- Mechanism: Named (netting through the shared book leaves closes beyond own lots; lot artifacts inflate close counts)
- Falsifier: Calibration list carries per-item forward falsifiers (e.g. batch15 six-session wait graded on the next 20 waited candidates); census itself is the measurement, not a claim under test
- Seats: PLAUS 0.86 | NULL 0.16 | CAT bookkeeping (0.41) | SCORE large-insample (0.91) | LENS mean 0.27 [0.21..0.31]

### C048 desk-sleeve-surface-20261031 : MACHINERY (kind M)
- Claim: Desk sleeve surface map: the owner-visible page's per-sleeve fields joined config x health with id sets matching exactly (336 = 336), and the fields that are null across the roster named as never-print
- Evidence: Roster 336 at this pass; UNFED 72 with missing-input names listed (lazarus_fires, opening_events, timing_signals, tensor_daily20 x2); parked=true x48 matching health PARKED 48
- Trial honesty: UNSTATED
- Mechanism: Named (refresh path derives from the same roll the desk persists, so the surface cannot drift)
- Falsifier: None stated (locate-only phase)
- Seats: PLAUS 0.28 | NULL 0.57 | CAT presentation (0.75) | SCORE assertion-only (0.83) | LENS mean 0.23 [0.21..0.31]

### C049 doctrine-application-20261031 : MACHINERY (kind M)
- Claim: Memory compaction receipts: decision-2 execution log of deleted units per dated memory file, kept as the audit trail of what was removed
- Evidence: NUMBERLESS (per-file deletion receipts, e.g. 10 units from 2026-10-06.md, each with its source line)
- Trial honesty: UNSTATED
- Mechanism: ABSENT (receipts log)
- Falsifier: None stated
- Seats: PLAUS 0.34 | NULL 0.71 | CAT bookkeeping (1.00) | SCORE assertion-only (0.99) | LENS mean 0.18 [0.16..0.20]

### C050 doctrine-ascension-20261102 : MACHINERY (kind M)
- Claim: Cold audit of the published InfinityBlade doctrine package: verdict PARTIAL; the core skill grades strong, the surrounding package does not yet meet the same standard, and the index's completeness promise is falsified by two skills depending on unshipped machinery
- Evidence: 63 staged files searched on final bytes for gate patterns and secret-shaped strings; dimension grades printed (Execution 8, Insight 8, Persuasive force 6); target pinned at HEAD 97eb1fee, doctrine 3.0.0
- Trial honesty: UNSTATED
- Mechanism: Named (enforcement mechanisms verify words present, not words true, in the package's own print)
- Falsifier: The completeness-promise failure is itself a falsified universal claim, recorded in the audit
- Seats: PLAUS 0.77 | NULL 0.52 | CAT safety (0.62) | SCORE assertion-only (0.84) | LENS mean 0.28 [0.23..0.34]

### C051 doctrine-full-read-20261102 : MACHINERY (kind M)
- Claim: Full-read record of the doctrine repo at the 3.1.0 landing: changelog and canon read file by file as the reread source for the estate's doctrine pin
- Evidence: Version history 2.5.0 through 3.1.0 with per-version cure notes (ignition heads on every library skill, worked false-GREEN autopsies added, cold-read protocol scheduled)
- Trial honesty: UNSTATED
- Mechanism: Named (the doctrine exists to make the report answer to the artifact)
- Falsifier: None stated (read record)
- Seats: PLAUS 0.74 | NULL 0.55 | CAT safety (0.51) | SCORE assertion-only (0.99) | LENS mean 0.34 [0.27..0.44]

### C052 doctrine-harvest-landing-20261102 : MACHINERY (kind M)
- Claim: Landing survey: the total harvest maps into the doctrine repo as Round 6 (2.9.0 to 2.10.0), with mechanisms already in force landing as coverage notes only and candidate rows staying candidates until their own tests pass
- Evidence: Mapping table printed (harvest sections to doctrine locations by standing); A-18 worker-slot cap stays a candidate because the scheduler test does not exist yet; README 12,851 bytes with CI prompt-parity check
- Trial honesty: UNSTATED
- Mechanism: Named (dated-note folding into existing disciplines; avoid-list for recorded-not-adopted)
- Falsifier: None stated
- Seats: PLAUS 0.74 | NULL 0.45 | CAT safety (0.35) | SCORE assertion-only (0.99) | LENS mean 0.33 [0.28..0.39]

### C053 doctrine-reread-desk-terminal-audit-20261103 : MACHINERY (kind M)
- Claim: Doctrine reread applied to desk and terminal: terminal header collision (F1) confirmed on Midna's own renders, and the cycle-7 reconcile event is the desk audit's real finding, with two dead hypotheses killed by evidence and recorded
- Evidence: Reconcile tolerance parameters printed (0.1% of expected cash, floor CASH_TOLUSD); fill capture shown sweep-driven; two hypotheses recorded as killed by evidence so they are not re-run
- Trial honesty: UNSTATED
- Mechanism: Named per finding (injected-nav stacking, sweep-driven fill capture vs durable ledger absence)
- Falsifier: Two hypotheses falsified inside the record (named in its own verdict lines)
- Seats: PLAUS 0.81 | NULL 0.27 | CAT safety (0.69) | SCORE assertion-only (0.89) | LENS mean 0.42 [0.37..0.48]

### C054 dsh-superagent-teardown-20261101 : MACHINERY (kind M)
- Claim: DSH superagent execution-core teardown: admission, fan-out, eval and ticket creation traced end to end, each mechanism claim graded CONFIRMED or UNVERIFIABLE at file:line in the pinned tree
- Evidence: Pinned tree sha 6337fc82; D5 direct-accept gate re-run confirmed in source; B1 core principle graded UNVERIFIABLE (a value statement, not a mechanism) in its own table
- Trial honesty: UNSTATED
- Mechanism: Named per component
- Falsifier: None stated (teardown verdicts are the resolution)
- Seats: PLAUS 0.67 | NULL 0.33 | CAT intelligence (0.47) | SCORE assertion-only (0.87) | LENS mean 0.46 [0.42..0.49]

### C055 efficiency-addendum-20261103 : MACHINERY (kind M)
- Claim: Efficiency addendum harvest: 11 BUGLOG files and 14 research folders mined for transferable mechanisms, landing as one doctrine skill carrying only insights genuinely absent from the current repo
- Evidence: Coverage ledger printed (corpora enumerated, exclusions named with their existing homes); verification run on the final artifact after the last edit
- Trial honesty: UNSTATED
- Mechanism: Named per harvested mechanism
- Falsifier: None stated
- Seats: PLAUS 0.75 | NULL 0.50 | CAT intelligence (0.47) | SCORE assertion-only (0.97) | LENS mean 0.38 [0.33..0.46]

### C056 elliott-wave-phd-deep-dive-20261016-1907 : WATCH (kind E)
- Claim: Elliott Wave PhD dive: the canon's three rules make any specified count falsifiable via invalidation prices, but the tradable evidence base grades weak (a 93.94% accuracy claim grades C- for no causal timestamping, costs, or naive benchmark; a retail forecast channel audits at ~31% wins)
- Evidence: Evidence table with per-source grades: Akbarzadeh & Soleimani 2023 SOM Forex 93.94% claimed, graded C-; Coinspot channel audit ~31% win rate over 6 months with losing ideas often unclosed; Investopedia synthesis: experienced analysts routinely disagree on counts in real time
- Trial honesty: UNSTATED (per-source samples named where the sources state them)
- Mechanism: Named by the theory (socionomic herding produces self-similar mood waves); anchor-choice bias named against it
- Falsifier: Stated in form (a specified count dies publicly on breach of its invalidation prices); no estate count has been run under it in this report
- Seats: PLAUS 0.34 | NULL 0.79 | CAT multiple-testing (0.30) | SCORE thin-or-external (1.00) | LENS mean 0.14 [0.12..0.16]

### C057 ema-trend-system-evidence-20261008-0229 : WATCH (kind E)
- Claim: Evidence base for three discretionary frameworks: EMA trend rules have modest academic support at longer EMAs, the three-confirmation framework's volume leg works best as a veto, and the Wyckoff '90% win rate' vendor claim is an accounting artifact (breakeven-after-TP1 plus scratches counted as wins)
- Evidence: Nazario et al. 2017 EMA rules on NASDAQ 1985-2015 (longer EMAs 50+ captured medium-term trends); the report's own verdict: the exit plan (partial at 1:2, breakeven stops, EMA trails) has no validated edge in any cited source; vendor GOLD claim based on the indicator's internal statistics
- Trial honesty: STATED as method requirement (expectancy, profit factor, DSR with trial-count disclosure demanded); the frameworks' own trial counts UNSTATED
- Mechanism: Named (capitulation volume spike + reversal is economically coherent and backtestable as a standalone)
- Falsifier: None run on estate data; regime-labelled self-scoring prescribed as the conversion to falsifiable form
- Seats: PLAUS 0.41 | NULL 0.75 | CAT none-real (0.37) | SCORE thin-or-external (0.83) | LENS mean 0.20 [0.19..0.22]

### C058 enhancement-build-20261103 : MACHINERY (kind M)
- Claim: Enhancement build record (revised scope: the doctrine repo package itself): disciplines shipped in package and proven, verdict PARTIAL with open rows named
- Evidence: Fail-first proof and final-tree evidence sections; per-discipline ship-status rows
- Trial honesty: UNSTATED
- Mechanism: ABSENT (build record)
- Falsifier: None stated
- Seats: PLAUS 0.18 | NULL 0.50 | CAT safety (0.79) | SCORE assertion-only (1.00) | LENS mean 0.29 [0.18..0.45]

### C059 enhancement-round5-20261102 : MACHINERY (kind M)
- Claim: Round 5 enhancement synthesis: exactly two mechanisms are large enough to be new disciplines (the near-miss ledger; content-bound expiring approvals), one formula completes Discipline 1, and the long tail is graded ADOPT / ADOPT-AS-TOOL / REJECT-WITH-REASON item by item
- Evidence: Per-item Value/Evidence/Cost grades printed; local violation found by the pass itself (local-stock-analysis SKILL.md at 22,381 bytes vs the 20,000-byte compaction-cut gate)
- Trial honesty: UNSTATED
- Mechanism: Named per candidate (near-miss records as diagnostics-only, neither rejections nor silence)
- Falsifier: None stated (adoption grading; rejected items carry reasons)
- Seats: PLAUS 0.73 | NULL 0.49 | CAT safety (0.60) | SCORE assertion-only (0.99) | LENS mean 0.44 [0.40..0.50]

### C060 enhancement-total-extraction-20261102 : MACHINERY (kind M)
- Claim: Homegrown extraction: the master inventory of the estate's own hard-won techniques, mined read-only from doctrine, fixes, delegation and memory practice, each with sources and standing
- Evidence: NUMBERLESS (inventory entries with source pointers and CODIFIED standing marks)
- Trial honesty: UNSTATED
- Mechanism: Named per entry
- Falsifier: None stated
- Seats: PLAUS 0.48 | NULL 0.51 | CAT intelligence (0.59) | SCORE assertion-only (0.97) | LENS mean 0.32 [0.26..0.40]

### C061 estate-completeness-20261110 : MACHINERY (kind M)
- Claim: Estate completeness synthesis: verdict PARTIAL; the automation surface is 222 cron jobs (94 enabled, 128 disabled) with stopped-without-authority rows hunted by name, and the desk surface reads 338 sleeves on a healthy runner
- Evidence: Cron census counted (222 jobs); absent-by-record items exactly 3 (full seal cron, external dead-man, X-posting cron, each with its ruling); runner state at 2026-11-11T00:35Z cycle 19, last_status ok, roster 338
- Trial honesty: UNSTATED
- Mechanism: Named (regime replacement routes backup through the light-save; stopped jobs classified by ruling, not by age)
- Falsifier: None stated (audit synthesis; open rows carry owners and dates)
- Seats: PLAUS 0.75 | NULL 0.53 | CAT bookkeeping (0.58) | SCORE assertion-only (0.72) | LENS mean 0.32 [0.29..0.36]

### C062 estate-dossier-20261103 : MACHINERY (kind M)
- Claim: Estate dossier for the Claude covenant: the strategy estate counts 654 sleeves/algorithms (650 FULL, 4 PARTIAL, 18/18 drills) and the book at census time is wired GREEN but execution-UNVERIFIED with zero fills
- Evidence: Census table with method named per row (107 terminal module dirs, 23 custom-skill folders); dead-drop proof marker count = 1; book's first proof event named (Fri 2026-11-06)
- Trial honesty: UNSTATED
- Mechanism: Named (dated markers, anti-laziness mechanisms, weekly cross-audit)
- Falsifier: None stated (dossier and covenant record)
- Seats: PLAUS 0.57 | NULL 0.50 | CAT bookkeeping (0.50) | SCORE assertion-only (0.47) | LENS mean 0.39 [0.29..0.46]

### C063 exit-execution-mechanics-20261019-20261019-1224 : MACHINERY (kind M)
- Claim: Exit execution mechanics research: Alpaca bracket legs stay inactive until the entry is completely filled, so partial fills carry zero bracket protection, and a resting broker order is the only exit that survives the process dying
- Evidence: Bracket behaviour verified from Alpaca documentation in the report; Freqtrade re-creation loop as the reference implementation; missed-run policy per job type (protection sweeps catch up once coalesced, entry signals expire)
- Trial honesty: UNSTATED
- Mechanism: Named (protection persistence architectures, watchdog ping wired into the work loop)
- Falsifier: None stated
- Seats: PLAUS 0.82 | NULL 0.25 | CAT safety (0.99) | SCORE thin-or-external (0.89) | LENS mean 0.35 [0.32..0.39]

### C064 failing-refresh-legs-fix-research-20261107-1655 : MACHINERY (kind M)
- Claim: Failing refresh legs diagnosed arithmetically: Class A's gap is 6,606 rows (9.40% missing, too large for boundary errors, the size of a missing slice), and Class B's 94 is exactly two-thirds of 141, flagged as a clue, not proof
- Evidence: Class A: live 70,275 vs page 63,669 (page = 90.60% of live); Class B: 141 vs 94 graded, rose 65 vs 50, missing-slice rose rate 31.9% vs retained 53.2%; guard redesign (compare two oracle calls, not an oracle vs a stored string)
- Trial honesty: UNSTATED
- Mechanism: Named per class (two builders one series, claim pinned to a moving counter)
- Falsifier: None stated (diagnosis and permanent-fix research)
- Seats: PLAUS 0.80 | NULL 0.57 | CAT data (0.57) | SCORE assertion-only (0.37) | LENS mean 0.40 [0.34..0.48]

### C065 fix-all-20261110 : MACHINERY (kind M)
- Claim: Fix-all program report: every row cured or named with proof, including the BTC divergence cause proven to the digit (destroyed journal span netted +0.384754672 = the gap) and the Coffin S1 question answered against its bar (drop-best ratio 3.35 under SPY's 8.077)
- Evidence: Reconcile residual -$5,489.15 cause found and booked, halt released; MO journal correction verified against ledger.json (realised -$838.48); Coffin S1 bootstrap median +370.24% with 41.12% of draws below SPY's total
- Trial honesty: UNSTATED
- Mechanism: Named per row (journal rotation destroying a span; wave-boundary-only ledger records hiding a stall)
- Falsifier: The embedded Coffin S1 falsifier was RUN inside this program: drop-best 3.35 fails the 8.077 bar as a standalone claim
- Seats: PLAUS 0.86 | NULL 0.21 | CAT safety (0.92) | SCORE assertion-only (0.74) | LENS mean 0.43 [0.39..0.49]

### C066 frontier-trading-research-deep-dive-20261114-2036 : MACHINERY (kind M, window-included)
- Claim: Frontier fleet-grading dive: the fleet admission exam is DSR>=0.95 / PBO<0.2 / t>3 with meta-labeling as a filter on existing rules, combination ordered equal-weight then HRP then stacking, and of the free alt-data, insider cluster buys survive scrutiny (~10-day horizon) while Wikipedia attention is a volatility signal, not direction
- Evidence: Meta-labeling form specified (secondary classifier on entry-known features, trade only above a calibrated probability); plateau rule for thresholds (expectancy positive and flat across t* +/- 0.10); the grading machinery carries its own forward falsification (strict-admission cohort must beat loose-admission cohort)
- Trial honesty: STATED (admission-exam trial accounting is the subject; DSR honesty depends on audited trial count, named as the limit)
- Mechanism: Named (triple-barrier labelling, purged/embargoed splits, fractional Kelly on sleeves)
- Falsifier: Stated for the machinery itself (cohort-vs-cohort forward test; calibration buckets must track forward); not yet run at this report's date
- Seats: PLAUS 0.91 | NULL 0.50 | CAT measurement (0.98) | SCORE assertion-only (0.62) | LENS mean 0.45 [0.37..0.48]

### C067 gestalt-100-20261110 : MACHINERY (kind M)
- Claim: The Wikipedia conditioner freeze root-caused and cured at the source: the desk fetcher only mirrors an upstream parquet that had not been re-run since 2026-10-14, and SIVE's listed chain is summarized from the exchange CSV (22 sessions of Nasdaq bars)
- Evidence: Frozen asof 2026-10-14 (sha a6f8fef66f97) vs cured output dated 2026-11-09; per-name attention (SMH +6.3%, SOXX -29.4%, SNDK +13.9%); four no-article names proven absent, named
- Trial honesty: UNSTATED
- Mechanism: Named (mirror never re-run; no error, no dead endpoint, no hard-coded date)
- Falsifier: None stated (cure record, GREEN on its named scope)
- Seats: PLAUS 0.25 | NULL 0.17 | CAT data (0.95) | SCORE thin-or-external (0.71) | LENS mean 0.29 [0.23..0.34]

### C068 github-api-transport-failures-and-bulk-u-20261028-0551 : MACHINERY (kind M)
- Claim: GitHub API transport failures and bulk-upload routes researched for the estate's save pipeline
- Evidence: REST endpoints capped at 900 points/min (GET/HEAD/OPTIONS = 1 point, every blob/tree/commit creation POST = 5 points), so a single endpoint's blob creation ceiling is 180/min; a tree entry may inline `content` so GitHub writes the blob inside one create-tree call instead of N blob calls; documented GitHub incident windows run 2-7% API errors/timeouts on bad nights, which a thousands-call job turns into certain failure
- Trial honesty: UNSTATED
- Mechanism: ABSENT in the extracted digest
- Falsifier: None stated
- Seats: PLAUS 0.20 | NULL 0.50 | CAT safety (0.69) | SCORE thin-or-external (0.74) | LENS mean 0.15 [0.10..0.21]

### C069 github-save-pipeline-best-practices-20261023-0449 : MACHINERY (kind M)
- Claim: GitHub automation reliability for the backup pipeline: fine-grained PAT scope boundaries, Git Data bulk-push limits, race-safe ref updates, and commit-SHA equality as the verification standard
- Evidence: PAT primary limit 5,000/hr; secondary 100 concurrent; Contents-only token fails repo-creation permission checks (mechanism explained); annotated-tag SHA comparison false-fails (named trap)
- Trial honesty: UNSTATED
- Mechanism: Named (permission check precedes endpoint logic; SHA equality implies tree equality)
- Falsifier: None stated
- Seats: PLAUS 0.32 | NULL 0.52 | CAT safety (0.99) | SCORE assertion-only (0.61) | LENS mean 0.22 [0.18..0.26]

### C070 grand-reconciliation-20261112 : MACHINERY (kind M)
- Claim: Grand reconciliation WS3 delta: the doctrine tip shows NO MOVEMENT (byte-identical), the Efficiency Breakthrough audit's HAVE/HAVE-NOT rows are spot-verified in live artifacts, and carry-forward rows from the 3.4.0 obligations ledger are enumerated
- Evidence: Tip-delta verdict NO MOVEMENT on byte comparison; EB-28 (no unified terminal-decision latch) carried as a delta row into the desk dispatcher; execution schedule read in full (34 rows); mandate audits R1/R2 as carry-forward sources
- Trial honesty: UNSTATED
- Mechanism: Named (spot-verification in a live artifact is what HAVE means)
- Falsifier: None stated (reconciliation record)
- Seats: PLAUS 0.65 | NULL 0.58 | CAT bookkeeping (0.58) | SCORE assertion-only (0.80) | LENS mean 0.38 [0.33..0.49]

### C071 grokbot-ui-replication-20261102 : MACHINERY (kind M)
- Claim: GrokBot UI replication audit, graded by rendered eye against spec: NOT GREEN, 2 PASS / 146 FAIL of 148 surfaces; the replication is a shell with cross-cutting failures carried as open rows
- Evidence: 148 surfaces graded from fresh renders or public read-backs; numeric discrepancies printed (hero 48.7% vs chart last value 49.3 on the above-200 share)
- Trial honesty: STATED (148-surface census is the denominator)
- Mechanism: Named per failure (enhancer copies a hero only where a card already has one; hub excluded from the enhancer's selector)
- Falsifier: The audit is itself the falsification pass over the build's claims; the build's completeness claim fails on its own spec
- Seats: PLAUS 0.19 | NULL 0.27 | CAT presentation (0.81) | SCORE large-insample (0.99) | LENS mean 0.14 [0.11..0.17]

### C072 gstack-gbrain-audit-20261110 : MACHINERY (kind M)
- Claim: GStack and GBrain audited against the estate's skill system: GStack's anatomy wins on uniformity, GBrain's memory design compared mechanism by mechanism, and adoption candidates are tabled with gear, falsifier and a Friday B5 grading hook each
- Evidence: Revisions pinned (GStack 1.99.0.0, GBrain 0.60.656.0); estate side counted (custom-skills 127 files; memory_search.py 465 lines BM25 over SQLite FTS5); Wilson 95% intervals used in its claims check
- Trial honesty: UNSTATED
- Mechanism: Named per candidate
- Falsifier: Stated per candidate (kill rules in its own table); outcomes land at B5, outside this report
- Seats: PLAUS 0.43 | NULL 0.51 | CAT bookkeeping (0.43) | SCORE assertion-only (0.44) | LENS mean 0.42 [0.33..0.47]

### C073 how-saas-and-online-tools-are-created-20261028-0457 : MACHINERY (kind M)
- Claim: How SaaS products and online tools are created end to end: successful products are not built feature-first, the scale gate is a flattening retention curve plus Ellis >=40% in the target segment, and open-mindedness that works is procedural (consider-the-opposite, premortems, scorekeeping)
- Evidence: Dropbox video MVP waitlist 5,000 to 75,000 overnight; Superhuman PMF engine 22% to 58% on the disappointed-segment metric; auth boilerplate 40-60h+ done properly
- Trial honesty: UNSTATED (framework criticisms kept attached in its own text: Ellis 40% is self-reported sentiment)
- Mechanism: Named per practice
- Falsifier: None stated
- Seats: PLAUS 0.50 | NULL 0.56 | CAT measurement (0.67) | SCORE thin-or-external (0.95) | LENS mean 0.28 [0.20..0.36]

### C074 ict-smc-liquidity-setup-evidence-20261008-0237 : WATCH (kind E)
- Claim: ICT/SMC setup evidence base: liquidity sweeps are a real mechanism with an overstated narrative, FVG and SMT legs are weak, the large-cap overnight-reversal edge has already decayed, intraday momentum has decayed ~58%+ post-publication, and specialization builds skill but does not manufacture edge
- Evidence: Brock et al. breakeven costs fell 0.54% (1926-43) to 0.22% (1976-91), at or below actual trading costs; McLean-Pontiff decay figures; the report's own standard: 100+ logged trades with no edge means the setup has none
- Trial honesty: UNSTATED (external studies' frames not enumerated)
- Mechanism: Named (stop clustering at round numbers, order-flow cascades) and named against (zones-not-lines plus role reversal as an unfalsifiable alibi structure)
- Falsifier: None run on estate data; the 100+ logged-trades standard is the stated deciding test
- Seats: PLAUS 0.37 | NULL 0.79 | CAT crowded-decayed (0.76) | SCORE thin-or-external (1.00) | LENS mean 0.16 [0.14..0.19]

### C075 infinityblade-3.1-application-20261102 : MACHINERY (kind M)
- Claim: InfinityBlade 3.1.0 full read and application ledger: every canon piece mapped to where it lands in the estate with proof, open rows named and carried
- Evidence: 10 tools landed in ~/workspace/tools named; all 19 library SKILL.md files plus core and seven references in the read set; local divergences carried as named rows
- Trial honesty: UNSTATED
- Mechanism: Named (a discipline counts only where a mechanism runs in a live path)
- Falsifier: None stated (application ledger)
- Seats: PLAUS 0.73 | NULL 0.52 | CAT safety (0.30) | SCORE assertion-only (0.89) | LENS mean 0.40 [0.28..0.47]

### C076 infinityblade-build-20261103 : MACHINERY (kind M)
- Claim: InfinityBlade build acceptance criteria: mechanisms, not paper; a discipline counts as built only when a real mechanism runs inside the repo
- Evidence: Thin record (3,954 chars): 34 disciplines mined for the efficiency addendum; check_prompt passes on the landed package
- Trial honesty: UNSTATED
- Mechanism: Named (mechanisms over paper as the acceptance rule)
- Falsifier: None stated
- Seats: PLAUS 0.36 | NULL 0.69 | CAT safety (0.58) | SCORE thin-or-external (0.62) | LENS mean 0.22 [0.20..0.26]

### C077 infinityblade-maximal-application-20261108 : MACHINERY (kind M)
- Claim: Maximal-application research lanes: context-engineering and memory techniques graded ADOPT with falsifiers attached (bullet-lesson counters audited at 4 weeks, >25% stale = theatre; delta-only check-in falsified or proven in the 2026-11-09 trading week)
- Evidence: ACE playbook (arXiv:2510.04618) and MemGPT/Letta lineage as sources; lane-4 census 222 rows; per-technique verdicts with reasons tied to the estate's named failure (long sessions degrading, restated lists crowding out judgment)
- Trial honesty: UNSTATED
- Mechanism: Named per technique (Generator/Reflector/Curator delta bullets, tiered memory with decay score, verification economics)
- Falsifier: Stated with dates and thresholds for the adopted parts; outcomes are not in this report
- Seats: PLAUS 0.78 | NULL 0.50 | CAT bookkeeping (0.72) | SCORE thin-or-external (0.78) | LENS mean 0.39 [0.37..0.42]

### C078 infinityblade-repo-fix-20261110 : MACHINERY (kind M)
- Claim: Doctrine repo audit and cure at the live tip: internal consistency, shipped-tools-vs-docs, and eval set all GREEN in repo scope, with eval case 21's paired-rerun falsifier carried open
- Evidence: Coverage ledger and per-section verdicts printed; eval set composition stated (cases 21, 31, 32, 33 in the rerun arm, two fresh trials per arm per case, 16 trials)
- Trial honesty: STATED (16-trial rerun composition enumerated)
- Mechanism: Named (A4: a fix commit names the routes it rejected)
- Falsifier: Claude's case-21 falsifier stated (still fails in the paired rerun = trigger); not resolved inside this report
- Seats: PLAUS 0.83 | NULL 0.50 | CAT safety (0.93) | SCORE large-insample (0.64) | LENS mean 0.40 [0.32..0.48]

### C079 infinityblade-total-application-20261110 : MACHINERY (kind M)
- Claim: TOTAL APPLICATION Wave 0: the 3.4.0 canon reread with a SHA manifest and a 202-row obligations ledger; 8 drift defects found and 46 defect IDs carried in the synthesis ledger
- Evidence: Pin and manifest facts printed; local clone proven stale (3.1.0 plus drift) against the pinned fetch; efficiency-breakthroughs SKILL verified present with all 34 disciplines
- Trial honesty: UNSTATED
- Mechanism: Named per drift defect
- Falsifier: Amendment triggers recorded as met or not in the ledger (A3's falsifier trigger met on the adopting host's arm, not executed in adoption)
- Seats: PLAUS 0.75 | NULL 0.59 | CAT bookkeeping (0.50) | SCORE assertion-only (0.93) | LENS mean 0.34 [0.27..0.41]

### C080 inspora-exploitation-20261110 : MACHINERY (kind M)
- Claim: Inspora exploitation study: a server-rendered curated design archive (keyset-cursor feed, human-flagged Featured view) whose borrowable mechanics and design language are extracted, with credit-is-not-permission as the legal rail
- Evidence: Feed mechanics from the teardown (16 posts per page, createdAt descending); market table with fee ranges (designer ~3.5-4%, client ~2-5%); ~54% of 2025 developer-tool sites ship dark-first
- Trial honesty: UNSTATED
- Mechanism: Named (keyset (createdAt, id) cursor, server-rendered first page, client id-dedupe)
- Falsifier: None stated
- Seats: PLAUS 0.22 | NULL 0.60 | CAT intelligence (0.72) | SCORE thin-or-external (0.98) | LENS mean 0.17 [0.12..0.21]

### C081 inspora-teardown-20261110 : MACHINERY (kind M)
- Claim: REA teardown of inspora.design: mechanics, stack, endpoints, operator and monetization established from payloads and code; grade PARTIAL with three rows open for named reasons
- Evidence: Next.js on Vercel from response headers; at least 32 posts across two captured pages, createdAt 2026-10-03 to 2026-11-09, cadence ~3/day in ingest batches
- Trial honesty: UNSTATED
- Mechanism: Named (human-gated ingestion plus a manually flagged Featured view)
- Falsifier: None stated (teardown grade is the resolution)
- Seats: PLAUS 0.29 | NULL 0.57 | CAT intelligence (0.82) | SCORE thin-or-external (0.91) | LENS mean 0.19 [0.16..0.21]

### C082 known-good-snapshot-20261031 : MACHINERY (kind M)
- Claim: Known-good snapshot record: the desk's Week 1 of the $1M epoch certified at +7.74% vs SPY -1.25% and QQQ -3.05% over the same window, book flat at the close, with the archive's limits stated (no live state, 45 dirty paths excluded, off-box push still owed)
- Evidence: Certified close figures printed with benchmarks; archive self-contained outside the repo; honesty note states the tag is not Friday's exact intraday runtime tree
- Trial honesty: UNSTATED (one week, one epoch; no trial frame claimed)
- Mechanism: ABSENT (snapshot record)
- Falsifier: None stated
- Seats: PLAUS 0.08 | NULL 0.70 | CAT bookkeeping (0.83) | SCORE thin-or-external (0.52) | LENS mean 0.15 [0.11..0.19]

### C083 launch-readiness-20261111 : MACHINERY (kind M)
- Claim: Launch-readiness living record: cure waves landed and gate-proven on the final tree, with the poll-heal rate measured (2,197 of 3,936 polls, 55.8%) and absent-mechanisms rows closed-proven by name
- Evidence: Heal rate 55.8% against a 57% threshold model in its own text; 11 broker_rejected_terminal counted in the current dispatcher generation; connectors 79-82 of 87 with zero references in the audited surface
- Trial honesty: UNSTATED
- Mechanism: Named per cure (writes misrouted to the default branch as one absence cause)
- Falsifier: Design questions decided with falsifiable revalidation triggers (named in the record)
- Seats: PLAUS 0.80 | NULL 0.50 | CAT safety (0.97) | SCORE thin-or-external (0.50) | LENS mean 0.43 [0.40..0.49]

### C084 leadrlabs-full-footprint-20261026-0308 : MACHINERY (kind M)
- Claim: LeadrLabs full public footprint: a trading-education vendor whose published qualification filter (500K+ average daily shares, $5MM+ dollar volume, ATR >= 2% of price, Stage 1/2 structure, 0-45 DTE options focus) is the extractable content; ratings 4.9 across 109 on its funnel page
- Evidence: Footprint enumerated (origins, posts, videos, interviews, pricing: Core $49 / Pro $99 monthly); founder account 37K followers in latest crawls with impersonator accounts named
- Trial honesty: UNSTATED (vendor's own numbers are marketing surface, graded as such)
- Mechanism: ABSENT (footprint research)
- Falsifier: None stated
- Seats: PLAUS 0.06 | NULL 0.59 | CAT intelligence (0.92) | SCORE thin-or-external (1.00) | LENS mean 0.08 [0.07..0.10]

### C085 llm-agent-memory-ascension-20261107-0026 : MACHINERY (kind M)
- Claim: LLM agent memory state of the art: file-store plus coding-agent evidence gathering beats plain RAG on long-trajectory memory (72.5% vs 48.5%), while on action-guiding memory all methods score low and RAG is at least as good as dedicated systems (recall is not use)
- Evidence: LongMemEval-V2: plain RAG 48.5%, tuned RAG 57.8%, file-store + coding agent 72.5%, off-the-shelf coding agent 69.3%; MemoryArena success 0.09-0.20 across methods; MemoryOS heat-score promotion formula; MIRIX claims +35% over RAG on ScreenshotVQA
- Trial honesty: UNSTATED (benchmark sizes named per source: LongMemEval 500 questions)
- Mechanism: Named (write-manage-read loop, heat-score promotion/eviction, governed shared store)
- Falsifier: None stated (survey with a benchmark warning as its first section)
- Seats: PLAUS 0.73 | NULL 0.20 | CAT bookkeeping (0.73) | SCORE thin-or-external (0.87) | LENS mean 0.32 [0.28..0.35]

### C086 llm-chart-reading-github-20261007-2243 : WATCH (kind E)
- Claim: LLM chart-reading evidence: vision models answer chart QA well (FinChart-Bench 76.6-84.3% for frontier models) but read candlestick direction at ~53% at best against a 50.87% numeric baseline, and an independent audit finds direction calls 51.4-57.1% with confidence intervals including 50% and pattern-name accuracy 1/215
- Evidence: FinChart-Bench 1,200 charts / 7,016 QA (GPT-4o 76.6%, GPT-4.1 80.9%, o3 83.9%, Sonnet 4 84.3%); 193,524-chart VLM study best 53.48%; roman-rr audit 215 calls, pattern naming 1/215
- Trial honesty: STATED (benchmark sizes printed: 1,200 charts, 193,524 charts, 215 audited calls)
- Mechanism: Named (vision for geometry, deterministic rules for numbers; falsification gate forcing a stated invalidation price)
- Falsifier: None run here; the estate's own visual second read is graded in the Wave 1 program (decisions-brainstorm-20261112)
- Seats: PLAUS 0.26 | NULL 0.80 | CAT none-real (0.77) | SCORE large-insample (0.95) | LENS mean 0.15 [0.13..0.20]

### C087 llm-consensus-alpha-circumvention-20261115-0410 : MACHINERY (kind M, window-included)
- Claim: The consensus-objection framework (Morillo): LLM outputs converge to consensus by mechanism, reasoning quality does not convert to returns (r = 0.07, p = 0.29 across 210 debate runs), and the supported design is peers who vote and are scored independently, never debate-to-consensus
- Evidence: Stanford multi-agent trading-debate study figures printed (210 runs, r = 0.07, p = 0.29); circumvention playbook ranked with the generate-and-test arithmetic done in the report
- Trial honesty: STATED in source terms (210 runs enumerated)
- Mechanism: Named (convergence mechanisms at token, training and aggregation levels; novelty search / quality-diversity as the counter-design)
- Falsifier: The framework carries the Consensus Lens program's own pre-registered failure verdict (2027-05 checkpoint), outside this report
- Seats: PLAUS 0.63 | NULL 0.35 | CAT measurement (0.59) | SCORE large-insample (0.70) | LENS mean 0.27 [0.23..0.32]

### C088 llm-enhancement-extraction-20261031 : MACHINERY (kind M)
- Claim: LLM enhancement extraction catalog: trait-by-trait mechanisms from public repos, each with source, quality evidence and an adoption verdict; independent verification PASS on 2026-10-31 with two wording errors corrected and no shortlist claim downgraded
- Evidence: Verification record in-directory (VERIFY.md); verdict vocabulary ADOPT-CODE / ADOPT-IDEA / ALREADY-HAVE / REFERENCE / SKIP applied per entry
- Trial honesty: UNSTATED
- Mechanism: Named per entry
- Falsifier: None stated (verification pass is the check)
- Seats: PLAUS 0.33 | NULL 0.54 | CAT intelligence (0.78) | SCORE assertion-only (0.95) | LENS mean 0.31 [0.21..0.49]

### C089 llm-visual-acuity-enhancement-20261008-0254 : MACHINERY (kind M)
- Claim: VLM visual-acuity protocol for chart reading: most failed reasoning steps are visual grounding errors (58%+), axis misreads are 24% of step failures, over 80% of first errors occur in steps 0-1, and an extract-then-verify pipeline gains +9-22%
- Evidence: chart-prm step analysis percentages printed per failure mode (grounding 58%+, axes 24.0%, color/series 19.5%, labels 15.2%); inverted axes fooled 10/10 VLMs in the deception study; step-N error implies ~83% failure at step N+1
- Trial honesty: UNSTATED (benchmark internals not enumerated)
- Mechanism: Named (front-loaded verification on inventory and transcription; transcribe-then-cross-check; abstention as a skill)
- Falsifier: None stated (protocol synthesis)
- Seats: PLAUS 0.83 | NULL 0.52 | CAT safety (0.68) | SCORE thin-or-external (0.94) | LENS mean 0.36 [0.33..0.38]

### C090 loop-beats-posting-20261104 : MACHINERY (kind M)
- Claim: Loop beats posting record (2026-11-04): all three beats posted to the dead drop and read-back verified, GREEN; the NWE earnings gap re-checked externally and stays MISSING, named
- Evidence: Read-back evidence per post in the record; study-file correction line appended at entry 81 of the 2026-11-04 chart study
- Trial honesty: UNSTATED
- Mechanism: ABSENT (posting record)
- Falsifier: None stated
- Seats: PLAUS 0.06 | NULL 0.79 | CAT bookkeeping (0.44) | SCORE assertion-only (0.99) | LENS mean 0.07 [0.06..0.08]

### C091 loose-ends-sweep-20261103 : MACHINERY (kind M)
- Claim: Loose-ends sweep of 2026-10-30 to 2026-11-03: every open row across the estate counted, cures landed with proof in-pass, verdict PARTIAL with the five heaviest open rows and the owner's exact ruling questions named
- Evidence: Counts section and full ledger in-directory; carried populations named (set-in-stone 150 PARTIAL commitments, adoption 8 PARTIAL remainders, dossier open rows)
- Trial honesty: UNSTATED
- Mechanism: Named per row
- Falsifier: None stated (sweep record)
- Seats: PLAUS 0.75 | NULL 0.50 | CAT bookkeeping (0.83) | SCORE assertion-only (0.90) | LENS mean 0.29 [0.22..0.37]

### C092 market-data-pipeline-rate-limit-fixes-20261013-1813 : MACHINERY (kind M)
- Claim: Market-data pipeline rate-limit build spec: chunk the nightly top-up (1,838 symbols in ~10 chunks of 200), never present IEX as consolidated, never mix Yahoo and Alpaca rows without a source column, and compute IV Rank on the IV series' own 52-week range
- Evidence: Request arithmetic printed (1,838 single-symbol calls vs ~2-10 chunked); the desk's own overlap measurement: Yahoo daily OHLC within 0.48% worst case of Alpaca SIP over the overlap; Alpaca limit semantics verified live (default 1,000, max 10,000, counts points across all symbols)
- Trial honesty: UNSTATED
- Mechanism: Named per anti-pattern (cache stampede at expiry, forming-bar repaint, error cached as no-data deleting symbols)
- Falsifier: None stated (build spec)
- Seats: PLAUS 0.82 | NULL 0.56 | CAT data (0.77) | SCORE thin-or-external (0.85) | LENS mean 0.42 [0.37..0.48]

### C093 master-traders-deep-dive-20261029-0229 : MACHINERY (kind M)
- Claim: Master-trader curriculum: one lineage (Livermore, Darvas, O'Neil, Ryan, Zanger, Minervini, Qullamaggie) with exact operating rules, CAN SLIM quantified (EPS acceleration +25%+, ROE 17%+, hard cut at 7-8% below cost, profits taken at 20-25%)
- Evidence: Rules stated numerically per trader (bases >= ~7 weeks, buy point = pivot on volume, Darvas box buy-stop above the box and ratcheting sell-stop below each new box); the report frames itself as a curriculum, not a ranking, and supplies no estate backtest
- Trial honesty: UNSTATED
- Mechanism: Named (buy strength in leading groups, RS 80-90+, cut losses mechanically)
- Falsifier: None run in this report; the lineage's rules were later coded into the master-trader playbook and sleeves by other programs
- Seats: PLAUS 0.16 | NULL 0.65 | CAT measurement (0.59) | SCORE assertion-only (0.92) | LENS mean 0.29 [0.24..0.37]

### C094 memory-ascension-doctrine-landing-20261106 : MACHINERY (kind M)
- Claim: Memory-recall doctrine landing record: the canon copy and its changelog landed locally as the memory program's source, with the 3.1.1 cure pass (alpaca_lib NameError definitions, stop-hook status-form mismatch) recorded
- Evidence: Changelog entries with the defects named at file level (undefined _BASES/_DATA_BASE in the shipped 3.1.0 alpaca-paper skill; hook exempting only the em-dash status form while docs teach the comma form)
- Trial honesty: UNSTATED
- Mechanism: Named per cure
- Falsifier: None stated (landing record)
- Seats: PLAUS 0.43 | NULL 0.66 | CAT bookkeeping (0.65) | SCORE assertion-only (0.93) | LENS mean 0.23 [0.19..0.31]

### C095 memory-enhancement-audit-20261108 : MACHINERY (kind M)
- Claim: Memory enhancement audit: the BM25 recall index is IMPLEMENTED-PROVEN (90,976,256-byte index, nightly rebuild), the canary baseline is hit@1 11/14 and hit@5 14/14 with any hit@5 drop defined as a recall defect, and the local tool's full semantic equivalence with canon stays recorded UNVERIFIED
- Evidence: Canary run in-session against 14 cases; living/dated census 2,615 current vs 17,644 dated chunks; memory_write fail-closed path proven on 6 logged attempts (blocked writes named)
- Trial honesty: STATED (14-case canary is the denominator, baseline set 2026-11-06)
- Mechanism: Named (progressive disclosure levels, canonical-source boost, living-vs-dated labeling weaker than canon's byte-identity flag, named as such)
- Falsifier: Stated and armed (canary below baseline = defect); the audit itself ran it and it held at baseline
- Seats: PLAUS 0.92 | NULL 0.25 | CAT bookkeeping (0.42) | SCORE thin-or-external (0.94) | LENS mean 0.38 [0.35..0.40]

### C096 midna-book-strip-20261104 : MACHINERY (kind M)
- Claim: Midna's Book strip on the terminal front page: built and trigger-proven, verdict PARTIAL by its own gate because the dated live proof event was still to come; first published figures show the book +0.00% vs SPY -0.18% and QQQ -0.75% since 2026-10-30
- Evidence: Strip figures traced to index closes through 2026-11-03; position-fields cure appended the same evening (BOOK-STRIP-POSITION-FIELDS-20261104)
- Trial honesty: UNSTATED
- Mechanism: Named (watcher-driven strip refresh)
- Falsifier: None stated (the dated live proof event is the check)
- Seats: PLAUS 0.15 | NULL 0.62 | CAT presentation (0.77) | SCORE assertion-only (0.56) | LENS mean 0.31 [0.26..0.33]

### C097 midna-claude-loop-20261103 : MACHINERY (kind M)
- Claim: Midna/Claude recursive self-improvement loop program: the two-agent loop is designed so successful artifacts carry claim, evidence, falsifier and ask as mandatory fields, and the loop's convergence claim is itself falsifiable by design
- Evidence: Research coverage ledger in-directory; dead-drop proof with the marker mechanics explained (the bare marker string occurs twice by construction); no published two-agent trading protocol existed to copy, stated in the report
- Trial honesty: STATED in design terms (loop iterations as trials); no graded outcome in this report
- Mechanism: Named (append-only shared memory, mandatory falsifier fields, B0/B1 beat structure)
- Falsifier: Stated as a design property (the derivation is the design's own claim and its falsifier); run state lives in the beats, not this report
- Seats: PLAUS 0.78 | NULL 0.73 | CAT bookkeeping (0.49) | SCORE assertion-only (0.99) | LENS mean 0.40 [0.34..0.48]

### C098 midna-trader-formation-20261029 : MACHINERY (kind M)
- Claim: Trader formation doctrine: no thesis without a reference class, an EV sentence before entry, and samples judged instead of trades (30+ trades minimum for an expectancy worth the name, 100-200 for a clear picture)
- Evidence: NUMBERLESS as measurement (a cognition curriculum: base-rate questions per setup and regime, the three-question sort for new information, sterile-cockpit execution windows)
- Trial honesty: UNSTATED
- Mechanism: Named (reference-class forecasting against personal base rates; state regulation of the estimator-executor)
- Falsifier: None stated (formation standard; its instruments are the trade card's forced fields)
- Seats: PLAUS 0.81 | NULL 0.74 | CAT measurement (0.98) | SCORE assertion-only (1.00) | LENS mean 0.37 [0.33..0.45]

### C099 milkman-trading-methodologies-20260926-2235 : WATCH (kind E)
- Claim: Milkman methodology investigation: his systems are fully specified enough to code (Bilbo Box v2: Saty compression box, hourly close out of compression above box high 10:00-15:00 ET, ~28 DTE call ~1 strike OTM, exits keyed to the stock never the premium), with evidence graded per methodology in Part 2
- Evidence: Complete rule sets extracted for the A-class systems (box = high/low of first 5 compression candles, frozen; 3-5% of account premium; 75% give-back exit after +1.0 dATR); intraday SPY/SPX conditional-odds setups classed semi-discretionary
- Trial honesty: UNSTATED (his published statistics are the vendor's; estate replication lives in the Bilbo sleeve lane)
- Mechanism: Named (compression-expansion after volatility contraction)
- Falsifier: None run in this report (investigation and specification; the desk's own Bilbo work is the test bed)
- Seats: PLAUS 0.53 | NULL 0.75 | CAT none-real (0.63) | SCORE assertion-only (0.65) | LENS mean 0.22 [0.20..0.25]

### C100 modern-options-trading-deep-dive-20261113-0046 : WATCH (kind E, window-included)
- Claim: Modern options deep dive: earnings implied moves are systematically overpriced in aggregate (28,898 reports: priced +/-9.18%, closed +/-6.32%, only 25.2% closed beyond implied), long ATM earnings straddles are a structural loser (-18.5%/trade, 22% win rate over 9,622 S&P 500 events, worst quintile -44.5% at 0.3% win rate), and dealer flip levels measure volatility state, not direction
- Evidence: EarningsWatcher 28,898 US reports Jan 2023-Sep 2026 (overpricing 2.86pp; AI-complex exception 411 reports); IVolatility 9,622 events 2021-2026 with real bid/ask round-trips, IV crush +15.6pp average; FlashAlpha 70 events flagged in-text as a tiny single source
- Trial honesty: STATED (28,898 and 9,622 event censuses printed with windows; the 70-event source flagged as tiny by the report itself)
- Mechanism: Named (event premium overpricing, IV crush, dealer gamma state)
- Falsifier: None run on estate data in this report; the estate's F5 high-EAV straddle-selling shadow arm (from Tue 2026-11-17) is its forward form
- Seats: PLAUS 0.46 | NULL 0.47 | CAT none-real (0.55) | SCORE large-insample (0.96) | LENS mean 0.38 [0.31..0.43]

### C101 multi-writer-git-commit-architecture-20261013-2159 : MACHINERY (kind M)
- Claim: Multi-writer git commit architecture research: worktree-per-writer plus a single daemon owning main via CAS ref updates, with jj colocated as an ergonomics accelerator, not a substitute for the queue
- Evidence: Pattern-level evidence (bors/Zuul/GitHub queue survey for the one-machine case; hook path-resolution traps in linked worktrees; one ADR's 10-20 minute suites removed from the local hook because they trained --no-verify behaviour)
- Trial honesty: UNSTATED
- Mechanism: Named (CAS update-ref fails if base moved; queue never blocks behind a bad entry)
- Falsifier: None stated
- Seats: PLAUS 0.24 | NULL 0.66 | CAT safety (0.96) | SCORE assertion-only (0.80) | LENS mean 0.23 [0.18..0.38]

### C102 name-removal-20261101 : MACHINERY (kind M)
- Claim: Name-removal program final report: GREEN on every reachable surface, proven by fresh rescan with counts preserved exactly (775 commits post = 775 pre; distinct commit-tree set 701 = 701)
- Evidence: Proof table with before/after counts; false positives verified and left untouched (two scholars sharing a first name, named in the report); honest residuals stated, not hidden
- Trial honesty: UNSTATED
- Mechanism: Named (filter-repo blob-content replacement across all refs)
- Falsifier: The fresh rescan is the falsification pass; it passed on reachable surfaces with residuals named
- Seats: PLAUS 0.16 | NULL 0.63 | CAT safety (0.57) | SCORE assertion-only (0.95) | LENS mean 0.08 [0.06..0.11]

### C103 night-lane-cures-20261104 : MACHINERY (kind M)
- Claim: Night-lane cures for the daily full audit's failed lanes: six items dispositioned with verdicts, a new OPRA 403 blocker named on the tape card, and one refresh proofgate killed at exit 137 recorded as a kill, not a pass
- Evidence: Per-item verdicts at a glance; FNQC dark-print figures (dix 0.491, date 2026-11-04) with card and feed agreeing after the cure
- Trial honesty: UNSTATED
- Mechanism: Named per item
- Falsifier: None stated (cure record)
- Seats: PLAUS 0.20 | NULL 0.70 | CAT safety (0.93) | SCORE assertion-only (0.98) | LENS mean 0.23 [0.19..0.26]

### C104 obsidian-second-brain-sweep-20261102 : MACHINERY (kind M)
- Claim: Obsidian second-brain sweep synthesis: seven repos classified against what the estate already runs, 6 packages ADOPT with spec and proof each, 18 rows ALREADY-HAVE with the existing machinery named, the rest SKIP with reasons; PARTIAL by construction
- Evidence: Counts section (6 ADOPT / 18 ALREADY-HAVE / named SKIPs, e.g. per-operation Git checkpoints SKIP because the seal system already versions the workspace with proven restores)
- Trial honesty: UNSTATED
- Mechanism: Named per row (reimplementation in our own files, never importing, as the adoption rule)
- Falsifier: None stated (classification synthesis)
- Seats: PLAUS 0.24 | NULL 0.63 | CAT bookkeeping (0.48) | SCORE assertion-only (0.99) | LENS mean 0.23 [0.20..0.25]

### C105 onebar-family-2026-10-30 : UNGRADABLE-BLOCKED (kind E)
- Claim: One Bar family claim audit: the vendor's headline claims (profitable on NQ then three more indices with zero changes; equity curve to ~$210,000) are UNVERIFIED and uncheckable from the post (no trades, dates, data or code supplied), and the rules were still translated into three FED parked-false sleeves on $10,000 slices with the translation arithmetic done openly
- Evidence: Claim-by-claim audit table (each claim graded UNVERIFIED with the missing evidence named); translation arithmetic printed ($1,000 stop = 50 NQ points at $20/point; STOP_PCT 0.0020); exit is time, not price (remainder of the entry bar)
- Trial honesty: UNSTATED (the vendor states none; the audit's point is exactly that absence)
- Mechanism: Named by the author (a break of a 50-bar extreme shows real momentum; one-bar hold preserves it)
- Falsifier: None runnable: the claim carries no data to falsify against, which is the audit's finding
- Seats: PLAUS 0.30 | NULL 0.85 | CAT none-real (0.52) | SCORE assertion-only (0.88) | LENS mean 0.05 [0.05..0.05]

### C106 openai-wiring-20261110 : MACHINERY (kind M)
- Claim: OpenAI wiring census (Surface 6): every classification-shaped task in the estate enumerated (~230 cron jobs scanned, 31 candidate bodies read), each wire graded, with SKIP where the classification is broker-read and a typed seat would add nothing
- Evidence: Summary counts and per-wire verdict table; one surface's grades printed (agreement at the 0.5 threshold 41/46 = 89.1%); privacy pack-contents rule stated once for all surfaces
- Trial honesty: STATED (census denominators printed per surface)
- Mechanism: Named (typed seats only where judgment, not measurement, is the input)
- Falsifier: One MO falsifier note carried in the record (no MO close above 78.03 through Tue 2026-11-10; the falsifier week grades Friday)
- Seats: PLAUS 0.73 | NULL 0.57 | CAT measurement (0.50) | SCORE large-insample (0.81) | LENS mean 0.35 [0.32..0.41]

### C107 options-frontier-scan-20261113-0101 : WATCH (kind E, window-included)
- Claim: Options frontier scan (late 2026): textbook dispersion has become a capacity and crowding trade (JPM dispersion index -4.9% in March 2026, worst month since 2011; 3-month implied correlation fell to ~7% by July 2026, near the lowest on record vs a ~33% decade average), so the tradeable frontier is timing the correlation regime and basket curation
- Evidence: Cboe/Hedgeweek correlation figures with dates; 0DTE at 62.4% of SPX volume in 2025 (Cboe via practitioner content, graded promoter-layer in the report); a GEX forward-returns falsification study carried in its own table
- Trial honesty: UNSTATED
- Mechanism: Named (correlation regime timing; QVR's wind-down as the contrarian-side proof)
- Falsifier: None run on estate data (scan and survey); the referenced GEX falsification study is external
- Seats: PLAUS 0.39 | NULL 0.75 | CAT regime-fluke (0.61) | SCORE thin-or-external (0.99) | LENS mean 0.21 [0.19..0.23]

### C108 paid-trading-tools-landscape-20261021-1155 : MACHINERY (kind M)
- Claim: Paid retail trading tools landscape: what is worth reimplementing in-house is the documented mechanics (GEX arithmetic, ATR trailing logic), not the marketed signals; vendor price and claim table with conflicts printed (GainzAlgo $49.95 description vs $99.95 Open-Graph price)
- Evidence: Price census (LuxAlgo $67.99/mo, Trade Ideas $127/$254, FlowAlgo $149/mo, Cheddar Flow $85/$99); GEX formula printed with the identification caveat (public OI does not identify the holder; call-positive/put-negative is a convention, not an observation)
- Trial honesty: UNSTATED
- Mechanism: Named per tool (UT Bot ATR trailing stop by QuantNomad, non-repaint on close)
- Falsifier: None stated
- Seats: PLAUS 0.25 | NULL 0.64 | CAT intelligence (0.96) | SCORE thin-or-external (0.75) | LENS mean 0.33 [0.30..0.35]

### C109 psychology-engine-2026-10-30 : MACHINERY (kind M)
- Claim: Psychology and sentiment study for the Psychology Engine: the behavioral canon graded mechanism by mechanism, with Robust reserved for effects found in multiple independent samples with a mechanism that predicts where the effect strengthens, and that moderation actually observed
- Evidence: Grading standard printed in the report (Robust / mixed / folklore classes); citation-honesty note (findings known through replications are cited as such)
- Trial honesty: UNSTATED
- Mechanism: Named per effect (prospect theory in positioning, overconfidence and trading frequency, disposition effect, herding cascades)
- Falsifier: None stated (study for an engine; grades are the deliverable)
- Seats: PLAUS 0.50 | NULL 0.53 | CAT measurement (0.94) | SCORE assertion-only (0.88) | LENS mean 0.36 [0.31..0.45]

### C110 public-pii-sweep-20261101 : MACHINERY (kind M)
- Claim: Public GitHub PII sweep final report (2026-11-01 re-scan): grade PARTIAL in its own words; verified exposure at HEAD remains (79 grouped rows) and history-only exposure remains (82 grouped rows), with account-level surfaces proven clean (5 profile fields zero hits, 0 public gists, 7 repo descriptions read fresh with zero hits)
- Evidence: Coverage ledger proven by scanner counts; false-positive class separated (41 grouped rows verified in context); waived-by-ruling class separated (6 rows, never cured, by ruling)
- Trial honesty: UNSTATED
- Mechanism: Named (contents-only edits cannot cure rows that automation would overwrite; each blocking reason stated per row)
- Falsifier: None stated (sweep report; the rescan is the check)
- Seats: PLAUS 0.81 | NULL 0.43 | CAT data (0.59) | SCORE assertion-only (0.53) | LENS mean 0.21 [0.18..0.27]

### C111 public-pii-sweep-20261107 : MACHINERY (kind M)
- Claim: Second PII sweep (2026-11-07): what was found was cured and the heal was verified from a fresh clone (main read back at the exact published sha), overall verdict PARTIAL with one heal killed by a host restart at 3,701 items and recorded as such
- Evidence: Heal and fresh-clone verification section with timestamps (2026-11-10 16:20-17:25 ET); per-item verdicts table; disposable-domain blocklist line identified as a false positive in spam-filter code
- Trial honesty: UNSTATED
- Mechanism: Named (hourly sync builds on the healed ref; ref history taken from the API with full shas only)
- Falsifier: None stated
- Seats: PLAUS 0.83 | NULL 0.19 | CAT safety (0.57) | SCORE assertion-only (0.70) | LENS mean 0.19 [0.16..0.23]

### C112 quantjourney-adoption-20261031 : RESOLVED-AGAINST (kind E)
- Claim: EDGE spread estimator adoption study: REJECTED under kill criteria fixed before results; on a 14-name panel over 129 trading days the estimator's spreads diverge from real quoted spreads by orders of magnitude (SPY +2,325%)
- Evidence: Panel printed (14 US equities in three liquidity tiers, Alpaca SIP daily bars 2026-04-29 to 2026-10-31, 129 trading days per name, one estimate per name); both known biases (quoted vs effective) stated and shown unable to rescue the result; one narrow near-miss noted (tick-dominated SNDL landed near the measured spread)
- Trial honesty: STATED (14 names x 129 days; kill criteria fixed before any run, quoted in the report)
- Mechanism: Named (GMM moment conditions on high/low/close; the failure is that daily range is not spread in liquid names)
- Falsifier: RUN: the pre-registered kill criteria fired; verdict REJECTED is the falsifier's output
- Seats: PLAUS 0.05 | NULL 0.96 | CAT data-artifact (0.50) | SCORE resolved-forward (0.69) | LENS mean 0.02 [0.01..0.04]

### C113 quantjourney-rea-20261031 : MACHINERY (kind M)
- Claim: QuantJourney gateway extraction: the vendor's public API surface fully inventoried (597 operations, all POST, all BearerAuth) with conventions, auth model and rate limits assembled from spec, security page, SDK metadata and client code
- Evidence: Complete endpoint inventory with per-operation parameters; non-spec public surface probed without a credential and recorded
- Trial honesty: UNSTATED
- Mechanism: Named per route family
- Falsifier: None stated (extraction record)
- Seats: PLAUS 0.17 | NULL 0.59 | CAT intelligence (0.87) | SCORE assertion-only (0.62) | LENS mean 0.18 [0.17..0.20]

### C114 quants-mechanisms-activation-20261031 : MACHINERY (kind M)
- Claim: Quants mechanisms activation progress: weight-lag activation implemented and proven, then REVERTED per the no-impairment rail (state OPEN); rebalance-policy enforcement PARTIAL (declared dimensions enforced, absent-value dimensions declared-only by name); evidence-packet live adoption GREEN on the final artifacts
- Evidence: Per-mechanism outcome lines with proof forms (updated blocker fails on pre-activation code; runner state read at cycle 12 dispatch); the revert is recorded as the rail working, not as a failure hidden
- Trial honesty: UNSTATED
- Mechanism: Named per mechanism
- Falsifier: None stated (program progress record)
- Seats: PLAUS 0.75 | NULL 0.29 | CAT safety (0.79) | SCORE assertion-only (0.85) | LENS mean 0.35 [0.31..0.39]

### C115 quants-mechanisms-steal-20261031 : MACHINERY (kind M)
- Claim: Quants mechanisms steal progress: six mechanisms implemented in passes (weight-lag, next-bar fills with cost objects, honest walk-forward labelling, evidence-packet dashboards, win-rate accounting basis, rebalance-policy object), each audited PARTIAL with its live/backtest scope stated
- Evidence: Audit states printed per mechanism (weight-lag PARTIAL/LIVE; next-bar fills PARTIAL/BACKTEST; labelling PARTIAL/BACKTEST); the po10 header now states its accounting basis beside the 59% win rate / PF 1.86 figure, and any WR/PF without a basis field fails its own rule
- Trial honesty: STATED in mechanism terms (trials/deflation_trials and split fields carried in the forecast package)
- Mechanism: Named per mechanism (Corwin-Schultz half-spread x2.3 + 2bp auction + square-root impact as the cost object)
- Falsifier: None stated (implementation passes with failing-first blockers as the proof form)
- Seats: PLAUS 0.90 | NULL 0.26 | CAT measurement (0.67) | SCORE thin-or-external (0.49) | LENS mean 0.51 [0.42..0.58]

### C116 rea-applications-20261110 : MACHINERY (kind M)
- Claim: REA applications brief: reverse-engineering audits are the estate's pre-adoption claims filter (TraderDev teardown extracted 29,394 unique strategies from a ~376,000-row catalog and proved the marketplace KPIs recompute exactly from the platform's own served trade lists)
- Evidence: Named examples with counts (29,394 of ~376,000; Biotech2k pattern: one X post became three registered candidates, six falsifier tests and CAND-ROT-04 graded against SPY/QQQ); the protocol rule stated (the research protocol, never the teardown, decides whether a primitive earns a sleeve)
- Trial honesty: UNSTATED
- Mechanism: Named (signal path from shipped code, repaint and future-leak verdicts with proving lines quoted)
- Falsifier: None stated (brief); falsifiers attach at candidate registration downstream
- Seats: PLAUS 0.90 | NULL 0.44 | CAT intelligence (0.99) | SCORE thin-or-external (0.66) | LENS mean 0.53 [0.47..0.58]

### C117 rea-target-list-expansion-20261026-0440 : MACHINERY (kind M)
- Claim: REA target-list expansion: a census of retail trading-tool vendors worth tearing down, with market-size and track-record caveats
- Evidence: Whop trading-indicators niche: 4,831 products, ~$1.77M estimated monthly revenue; Trade Ideas publishes no Holly win rate (its records measure signal-to-high profit potential, not realized profits); Quantum Algo's 75% / 160-signal ledger = 43 public calls + 117 vendor-recorded premium signals
- Trial honesty: Target list enumerated (40+ entries)
- Mechanism: Teardown target intelligence; the caveats are themselves claim-audit instruments
- Falsifier: Not applicable (census)
- Seats: PLAUS 0.83 | NULL 0.61 | CAT intelligence (1.00) | SCORE thin-or-external (0.95) | LENS mean 0.31 [0.22..0.39]

### C118 realtime-midna-avatar-options-20260929-0136 : MACHINERY (kind M)
- Claim: Landscape of real-time conversational AI avatar platforms (HeyGen, D-ID, Anam, Hedra, Tavus, Synthesia) with pricing and latency
- Evidence: LiveAvatar Essential $99 / 1,100 credits; first frame <300ms; D-ID Pro $16; streaming-minute metering identified as the cost driver (Build tier 32 streaming minutes)
- Trial honesty: Six platforms compared
- Mechanism: Product selection research (not a market-edge claim)
- Falsifier: Not applicable
- Seats: PLAUS 0.05 | NULL 0.68 | CAT intelligence (0.70) | SCORE thin-or-external (0.89) | LENS mean 0.08 [0.06..0.12]

### C119 reconcile-defects-abc-20261104 : MACHINERY (kind M)
- Claim: Cure report for reconcile defects A/B/C (signed halt/materiality comparisons, D1-CFEE double-count, missing reconcile history)
- Evidence: cash_halt_materiality_usd 984.34 (0.1% of expected cash) printed; all three defects marked CURED with blockers and gate
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Reconcile correctness machinery
- Falsifier: Gate and first post-cure cycle named as the check
- Seats: PLAUS 0.70 | NULL 0.48 | CAT safety (0.99) | SCORE assertion-only (0.95) | LENS mean 0.34 [0.22..0.43]

### C120 remainders-fix-20261030 : MACHINERY (kind M)
- Claim: Remainder census 2026-10-30: every PARTIAL and open item classified with an owner
- Evidence: Classes: CODE_GAP 14, NEVER_STARTED 6, STOPPED 2, SOURCE_LIMIT 17, RULING 1; State Analogue accrual 1 of 126 sessions (writer cured, 125 sessions of accrual remaining); board panel 403 sessions vs the 813 floor
- Trial honesty: Full remainder population enumerated
- Mechanism: Program bookkeeping machinery
- Falsifier: Not applicable (census)
- Seats: PLAUS 0.54 | NULL 0.60 | CAT bookkeeping (0.96) | SCORE assertion-only (0.85) | LENS mean 0.22 [0.19..0.28]

### C121 saty-code-acquisition-rea-20261021-2223 : MACHINERY (kind M)
- Claim: Saty Phase Oscillator and Pivot Ribbon Pro source acquired and transcribed from the live TradingView publications
- Evidence: Phase Oscillator 132 lines Pine v5; Pivot Ribbon Pro 204 lines; parameters printed: ATR(14), stdev(21), EMA(21) pivot, compression at pivot ± 2.0 ATR, expansion ± 1.854 ATR
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Source acquisition enabling exact replication; the stack's edge is graded in the Saty sleeves, not here
- Falsifier: Not applicable (transcription verified against live source)
- Seats: PLAUS 0.75 | NULL 0.86 | CAT data (0.53) | SCORE assertion-only (0.94) | LENS mean 0.20 [0.18..0.24]

### C122 saty-indicator-stack-20261021-2152 : WATCH (kind E)
- Claim: Research report on the Saty indicator stack (Volume Stack, Pivot Ribbon, Phase Oscillator, ATR Levels) and its doctrine, including the call-trigger confirmation statistics
- Evidence: Vendor-doctrine numbers as printed: first 3-minute close above the call trigger reaches the +38.2% target 73.8% overall, 97.1% when no 3m close falls back below the trigger, median 18 minutes; ATR Levels fib ladder 0.236 to 3.000 anchored to the previous HTF close (gap limitation printed: an overnight gap can open beyond the trigger)
- Trial honesty: TRIAL-COUNT-UNSTATED (doctrine source gives no sample size for the trigger statistics)
- Mechanism: ATR-level trigger plus 3-minute-close confirmation as a location-and-confirmation rule
- Falsifier: Not run in this report; the desk's Saty sleeves carry the forward record
- Seats: PLAUS 0.49 | NULL 0.77 | CAT none-real (0.50) | SCORE thin-or-external (1.00) | LENS mean 0.19 [0.15..0.20]

### C123 set-in-stone-20261031 : MACHINERY (kind M)
- Claim: Set in Stone Ledger 2026-10-31: the estate's commitments assembled and independently verified
- Evidence: Counts by state printed after dedup and verification adjustments; PARTIAL: 150 rows
- Trial honesty: Full ledger population
- Mechanism: Commitment bookkeeping machinery
- Falsifier: Independent verification pass is the check
- Seats: PLAUS 0.37 | NULL 0.51 | CAT bookkeeping (0.96) | SCORE assertion-only (1.00) | LENS mean 0.22 [0.17..0.30]

### C124 setups-product-redesign-20261016-2005 : MACHINERY (kind M)
- Claim: Product research on presenting one trade idea: institutional idea tickets, signal-card anatomy, calibrated likelihood language, progressive disclosure
- Evidence: IPCC calibrated-language anchors printed (likely >66%, very likely >90%, about as likely as not 33-66%); design decision: the card carries exactly the 80% case
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Presentation machinery for trade cards
- Falsifier: Not applicable (design research)
- Seats: PLAUS 0.10 | NULL 0.75 | CAT presentation (0.99) | SCORE assertion-only (0.99) | LENS mean 0.18 [0.15..0.21]

### C125 site-visual-polish-20261030 : MACHINERY (kind M)
- Claim: Terminal auto-update audit 2026-10-30: per-page producer, schedule and freshness census with a defect list
- Evidence: Per-page table with last stamps (several pages one to two sessions stale at audit); defects named: D3 source-clock producer unscheduled and unmapped; D8 concurrent writes during proof runs invalidate the proof
- Trial honesty: Full terminal page population
- Mechanism: Freshness and provenance machinery
- Falsifier: Smoke and refresh proof read as the check
- Seats: PLAUS 0.93 | NULL 0.34 | CAT safety (0.90) | SCORE assertion-only (0.89) | LENS mean 0.31 [0.26..0.40]

### C126 skool-daviddtech-teardown-20261109 : MACHINERY (kind M)
- Claim: REA teardown of the DaviddTech Skool community: the public funnel and offer stack extracted; verdict PARTIAL behind the paywall
- Evidence: Affiliate commission 40%; full server-rendered payload captured; PARTIAL driven by the paywall and a REA browser-capture limitation, both named
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Competitor and claim-audit machinery
- Falsifier: Not applicable (teardown)
- Seats: PLAUS 0.19 | NULL 0.51 | CAT intelligence (1.00) | SCORE assertion-only (0.80) | LENS mean 0.10 [0.08..0.12]

### C127 sleeve-activation-calibration-20261111 : MACHINERY (kind M)
- Claim: Operation Firing Line readiness verdict for Thu 2026-11-12 pre-open: the full sleeve board classified with every defect named
- Evidence: Counts recomputed from the board: FIXTURE-PROVEN 1, ARMED-PROVEN 100, DEFECT-CURED 25, DEFECT 35, UNFED 62, PARKED 54 (superseded by the 2026-11-14 board: 65 live-firing of 339)
- Trial honesty: Full 339-sleeve population
- Mechanism: Readiness machinery
- Falsifier: Counts recomputed at destination
- Seats: PLAUS 0.85 | NULL 0.47 | CAT safety (0.90) | SCORE assertion-only (0.96) | LENS mean 0.41 [0.35..0.49]

### C128 sleeve-census-20261029 : MACHINERY (kind M)
- Claim: Sleeve census 2026-10-29: cross-source union of every sleeve definition, reconciled against the parent's 1,562 count
- Evidence: muse-desk-v3 config 333 sleeves at census date; reconciliation PARTIAL-EXACT with the difference named; deliverable verdict GREEN on key-set proof
- Trial honesty: Full union population
- Mechanism: Population bookkeeping machinery (the denominator every later census inherits)
- Falsifier: Key-set proof at destination
- Seats: PLAUS 0.95 | NULL 0.35 | CAT bookkeeping (0.98) | SCORE assertion-only (0.94) | LENS mean 0.36 [0.29..0.43]

### C129 sleeve-firing-2026-11-11 : MACHINERY (kind M)
- Claim: Sleeve-Firing Program 2026-11-11: non-firing sleeves classified by cause (desk plumbing, external data, owner ruling, standing defect, reconcile halt) with cures landed
- Evidence: Classes: (a) 8 desk-plumbing, (b) 61 waiting + 3 parked external, (c) 45 parked by ruling or design, (d) 6 parked for defect, (e) 6 halted by reconcile (confirmed, untouched)
- Trial honesty: Full non-firing population
- Mechanism: Activation machinery
- Falsifier: Not applicable (program report)
- Seats: PLAUS 0.87 | NULL 0.52 | CAT safety (0.94) | SCORE assertion-only (0.91) | LENS mean 0.40 [0.32..0.45]

### C130 sleeve-options-suitability-20261113 : MACHINERY (kind M, window-included)
- Claim: Sleeve-to-options suitability inspection: which desk sleeves serve as signal sources for options strategies, ranked by five suitability tests
- Evidence: Roster reconciled at 339; Tier 1 = 24 sleeves, Tier 2 = 115 usable with adaptation; board counts printed (LIVE-FIRING 65, FIXTURE-PROVEN 1, ARMED-PROVEN 132, DEFECT 23, UNFED 61, PARKED 57, with the 54-vs-57 parked discrepancy carried openly); top picks carry fill counts (aster_tensor_d20_tensor 672 fills; aster_etf_spy_monthly_c098 45 fills)
- Trial honesty: Full 339-sleeve population tested
- Mechanism: Signal-routing machinery: horizon fit, underlying liquidity, volatility character route sleeve fires to options structures; no new edge claim is made
- Falsifier: Not applicable (suitability ranking); the underlying sleeves' edges are graded on their own records
- Seats: PLAUS 0.94 | NULL 0.36 | CAT measurement (0.39) | SCORE large-insample (0.71) | LENS mean 0.44 [0.39..0.48]

### C131 soxl-pmhigh-sleeve-and-variants-20261103 : WATCH (kind E)
- Claim: SOXL premarket-high breakout: the replication reproduces exactly and shows a real modest edge; four pre-registered improvement variants all fail to beat the baseline
- Evidence: Replication at 5bp/side: 1,116 trades, average +0.263%, PF 1.291, total +775.78%, max DD -57.77% (2,724 sessions); development screen baseline 662 trades, average +0.090%; best variant V3 +263.93%, PF 1.178, DD improved to -44.84% and still lost to baseline
- Trial honesty: Four variants pre-registered in VARIANTS.md before testing; split and evaluation protocol frozen, identical to the SSO gauntlet
- Mechanism: Premarket-high breakout on a 3x levered semiconductor ETF, flat by close, no stop or target as specified
- Falsifier: Variant gauntlet run: all four variants failed their improvement test; the baseline's forward falsifier is the installed sleeve's live paper record
- Seats: PLAUS 0.61 | NULL 0.37 | CAT none-real (0.56) | SCORE large-insample (0.95) | LENS mean 0.49 [0.45..0.56]

### C132 strategyfactory-teardown-20261109 : MACHINERY (kind M)
- Claim: REA teardown of StrategyFactory.ai: its three public proof surfaces are presentation layer, not data
- Evidence: Bot library is a hardcoded array (for example 'Breakout Hunter' BTC/USDT 1D +203.4%, DD -18.2%, 67 trades, as a literal in the page code); 'Live Bot Activity' is a count-up animation to fixed constants; the funnel's 'live performance' is a seeded in-browser emulation replicated exactly
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Fraud-evidence machinery (same operator as C126)
- Falsifier: Seeded emulation replicated exactly is the proof standard
- Seats: PLAUS 0.05 | NULL 0.65 | CAT intelligence (0.74) | SCORE assertion-only (0.86) | LENS mean 0.06 [0.05..0.08]

### C133 ta-canon-gap-audit-20261020-2156 : MACHINERY (kind M)
- Claim: Canon gap audit: the desk's TA inventory against the complete technical-analysis canon; the gaps are structural patterns, not more oscillators
- Evidence: 38+ gap items rated; HIGH: high-tight flag (rise >=100% in <=8 weeks, flag <=25% for 3-5 weeks), O'Neil flat base (>=5 weeks, <=15% deep after >=30% advance); most oscillator candidates rated LOW as near-duplicates
- Trial honesty: Full canon enumerated against the inventory
- Mechanism: Coverage machinery for the chart-reading program
- Falsifier: Not applicable (gap census)
- Seats: PLAUS 0.84 | NULL 0.60 | CAT data (0.48) | SCORE assertion-only (0.95) | LENS mean 0.37 [0.32..0.41]

### C134 ta-github-sweep-20261007 : MACHINERY (kind M)
- Claim: TA and visual chart-inspection sweep of the estate's GitHub repos, centred on the Steelrend renderer: how four public chart analysts actually read charts, reverse-engineered into 180 rules
- Evidence: 279 chart images studied; renderer constants printed: touchATR 0.65, maxLineBreach 0.18, breakoutVolume 1.25 (breakout needs >=1.25x 20-bar mean volume); honesty section names what is not known (ticker and pivot selection, line-fitting objective)
- Trial honesty: 22 repos swept
- Mechanism: Chart-reading machinery; its constants are inputs to the gestalt arbitrary-constant census
- Falsifier: Not applicable (reverse engineering)
- Seats: PLAUS 0.86 | NULL 0.55 | CAT measurement (0.37) | SCORE thin-or-external (0.56) | LENS mean 0.34 [0.30..0.37]

### C135 ta-synthesis-20261007 : MACHINERY (kind M)
- Claim: TA Mastery synthesis: the three passes woven into one playbook, with the sobering VLM evaluations carried honestly
- Evidence: FinChart-Bench: frontier models 76-84% on chart QA, reasoning QA ~60%; best VLM candlestick direction ~53% vs XGBoost numeric baseline ~51%; setup-vs-noise discriminators printed (>=2 touches trendline, >=3 shelf, breakout needs a close plus retest)
- Trial honesty: Three source passes integrated
- Mechanism: Synthesis machinery; its falsification gate (state invalidation before any call) is the ancestor of the book's card discipline
- Falsifier: Falsification gate specified as a rule, graded in the forecast corpus
- Seats: PLAUS 0.88 | NULL 0.38 | CAT measurement (0.46) | SCORE thin-or-external (0.85) | LENS mean 0.38 [0.33..0.44]

### C136 target-stop-derivation-methods-20261016-1901 : MACHINERY (kind M)
- Claim: Target and stop derivation methods review: eight families ranked by evidence; volatility-scaled distances are best supported, Elliott projections unfalsifiable
- Evidence: Bulkowski perfect-trade samples: head-and-shoulders bottom target hit 71% (n=3,197, +45% average), H&S top 51% (n>2,800), complex H&S top 47% (n>650); Bulkowski correction printed (target = breakout +/- height x the pattern's historical hit percentage); no peer-reviewed validation of the 1x-height convention against alternatives found; Park & Irwin review of 95 TA studies (56 positive, 20 negative, 19 mixed) noted snooping corrections missing
- Trial honesty: Eight method families reviewed with sample sizes printed
- Mechanism: Method evidence base: supplies the target and stop standards the expression resolver grades against
- Falsifier: Not applicable (evidence review)
- Seats: PLAUS 0.93 | NULL 0.55 | CAT measurement (0.85) | SCORE thin-or-external (0.93) | LENS mean 0.39 [0.33..0.47]

### C137 technical-analysis-mastery-20261007-2229 : MACHINERY (kind M)
- Claim: TA Mastery reference: the master-level toolkit with honest per-family verdicts (Fibonacci, patterns, Elliott, support/resistance, trend, candlesticks)
- Evidence: Verdicts printed: Elliott Wave 'no rigorous evidence, unfalsifiable as commonly practiced'; support/resistance and multi-timeframe discipline are process tools, not predictions; the self-fulfilling order-clustering mechanism named as why levels appear to work
- Trial honesty: TRIAL-COUNT-UNSTATED (reference work)
- Mechanism: Reference machinery for the chart-reading program
- Falsifier: Not applicable (reference)
- Seats: PLAUS 0.26 | NULL 0.69 | CAT measurement (0.58) | SCORE assertion-only (0.94) | LENS mean 0.31 [0.27..0.36]

### C138 technical-analysis-mastery-20261030 : MACHINERY (kind M)
- Claim: TA Mastery census of assets: the coverage ledger of every corpus and playbook the mastery program rests on
- Evidence: Corpora and playbooks 243; census files enumerated with line and character counts (external-canon 286 lines, external-x 332 lines, and five more); local.md flags XCHART-STUDY.md as PARTIAL in its own text
- Trial honesty: Full asset population
- Mechanism: Coverage bookkeeping machinery
- Falsifier: On-disk counts verified for headline corpora
- Seats: PLAUS 0.15 | NULL 0.56 | CAT bookkeeping (0.98) | SCORE assertion-only (1.00) | LENS mean 0.17 [0.14..0.20]

### C139 tensor-daily20-pipeline-20261031 : MACHINERY (kind M)
- Claim: tensor_daily20 producer pipeline build report: the pipeline is correct, but the Phase 1 sample gate failed because the tapes cannot be rebuilt from today's vendor data
- Evidence: Verdict PARTIAL / BLOCKED, SAMPLE-PROOF-FAIL at the designed gate; anchors printed (AMD: 2,513 bars, first 1474896600, last 1790256600, input and native sha256 recorded); no desk file modified, nothing published
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Producer machinery for the two D20 Tensor sleeves
- Falsifier: The sample-proof gate ran and failed, exactly as designed to catch this
- Seats: PLAUS 0.13 | NULL 0.55 | CAT data (0.90) | SCORE assertion-only (0.89) | LENS mean 0.15 [0.12..0.18]

### C140 terminal-amazing-20261102 : MACHINERY (kind M)
- Claim: Amazing-recon: live terminal gap census 2026-11-02, verdict NOT READY with gaps named
- Evidence: 103 engines-and-tools pages censused live; C15 verdict DEFECT (mechanism fires, identity match wrong both ways); GAP-3: 51 families sum to 336 sleeves; attractions figures cross-checked (SPY -1.73%, QQQ -4.37%, desk +6.89%)
- Trial honesty: Full live page population
- Mechanism: Terminal quality machinery
- Falsifier: Live HTTP and rendered-stamp checks are the test
- Seats: PLAUS 0.15 | NULL 0.38 | CAT safety (0.37) | SCORE assertion-only (0.54) | LENS mean 0.27 [0.19..0.31]

### C141 terminal-chart-cures-20261031 : MACHINERY (kind M)
- Claim: Terminal chart cures 2026-10-31: per-page chart defects cured file by file; verdict PARTIAL
- Evidence: charts_ia 8 files green including the 3 named pages (agent-debate, echo-board, second-opinion each GREEN on independent verification); two monolithic runs were OOM-killed (exit 137) in this environment, which is why the pass ran file by file
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Terminal quality machinery
- Falsifier: Independent verification section re-ran the pages
- Seats: PLAUS 0.22 | NULL 0.55 | CAT safety (0.58) | SCORE assertion-only (0.88) | LENS mean 0.26 [0.23..0.30]

### C142 terminal-deficit-cures-20261104 : MACHINERY (kind M)
- Claim: Terminal deficit cures 2026-11-04: seven named deficits cured, each with a gate-wired blocker in the terminal BUGLOG
- Evidence: Items: ECHO-BOARD, expected-move filing gap, proofgate memory (after a caught false proof), suite triage with two rows carried open by name, morning-map upstream, proof-gate hardening, earnings-drift bounded retry
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Terminal quality machinery; the caught false proof is recorded as an incident, not hidden
- Falsifier: Fail-first tests per item (the zero-publish test fails pre-cure)
- Seats: PLAUS 0.75 | NULL 0.50 | CAT safety (0.97) | SCORE assertion-only (0.95) | LENS mean 0.41 [0.35..0.47]

### C143 terminal-earnings-explanation-20261031 : MACHINERY (kind M)
- Claim: Earnings-calendar explanation cure 2026-10-31: the one failing explanation surface fixed at its root cause
- Evidence: Fail-first established twice: the explanation test expected 100 summaries and failed only on earnings-calendar; after the cure the surface uses the same mechanism as the healthy pages
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Terminal quality machinery
- Falsifier: Fail-first then pass on the cured tree
- Seats: PLAUS 0.27 | NULL 0.34 | CAT safety (0.79) | SCORE assertion-only (0.96) | LENS mean 0.36 [0.23..0.46]

### C144 terminal-fixall-20261110 : MACHINERY (kind M)
- Claim: Terminal Fix-All program 2026-11-10: five workstreams GREEN, forecast engines PARTIAL with the completion proof in flight
- Evidence: Dark prints rebuilt: combined 42.9%, 499 of 503 stocks, 782 per-stock sessions; State Analogue at 8 of 126 sessions, reported as an accrual state; second-opinion refresh exit 0 on session 2026-11-10
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Terminal quality machinery
- Falsifier: Per-workstream proofs on the final tree
- Seats: PLAUS 0.16 | NULL 0.51 | CAT safety (0.66) | SCORE assertion-only (0.85) | LENS mean 0.35 [0.31..0.41]

### C145 terminal-foliotend-style-20261031 : MACHINERY (kind M)
- Claim: Terminal FolioTend style adoption, audit phase: orphan pages, hub cards and band derivations audited before any site edit
- Evidence: Status PARTIAL (audit complete, no site file edited in this phase); corrected figure printed: 2,238 graded study forecasts under the page's own definition over a 404-session span (2025-03-25 to 2026-10-30)
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Presentation machinery
- Falsifier: Not applicable (audit phase)
- Seats: PLAUS 0.13 | NULL 0.69 | CAT presentation (0.98) | SCORE assertion-only (0.55) | LENS mean 0.22 [0.18..0.29]

### C146 terminal-fresh-graphs-20261031 : MACHINERY (kind M)
- Claim: NUMBERLESS: the directory is empty; no report, no files, no claim on record
- Evidence: NUMBERLESS (0 characters extracted; the directory contains no files)
- Trial honesty: TRIAL-COUNT-UNSTATED (no artifact exists)
- Mechanism: Absent: an empty directory carried in the archive
- Falsifier: Not applicable: nothing was ever filed
- Seats: PLAUS 0.00 | NULL 0.96 | CAT bookkeeping (0.39) | SCORE assertion-only (0.82) | LENS mean 0.00 [0.00..0.00]

### C147 terminal-full-census-20261104 : MACHINERY (kind M)
- Claim: Terminal Full Census 2026-11-04: every engine, tool and page checked for liveness, access and display; verdict PARTIAL
- Evidence: Expected-move STALE: filed-map record ends 2026-10-30, missing sessions 2026-11-02 and 2026-11-03 named on the page's face, extrapolates nothing by design; refresh_proofgate OOM-killed (exit -9) after 2,983s, its third kill at that step, carried as a reliability row
- Trial honesty: Full terminal population
- Mechanism: Freshness and access machinery
- Falsifier: Census retaken on the settled tree against the expected session
- Seats: PLAUS 0.26 | NULL 0.34 | CAT safety (0.57) | SCORE assertion-only (0.73) | LENS mean 0.33 [0.31..0.36]

### C148 terminal-health-loop-20261031 : MACHINERY (kind M)
- Claim: Terminal Health Loop inventory: the estate of forecast engines and market tools enumerated for the health loop
- Evidence: Forecast engines 30; market tools THE-70 (70); counting and verification method stated up front
- Trial honesty: Full engine and tool population
- Mechanism: Health-monitoring machinery
- Falsifier: Not applicable (inventory)
- Seats: PLAUS 0.33 | NULL 0.52 | CAT bookkeeping (0.68) | SCORE assertion-only (0.79) | LENS mean 0.47 [0.40..0.50]

### C149 terminal-lineup-save-20261031 : MACHINERY (kind M)
- Claim: Terminal lineup save to the public Test repo: census and README PASS; program verdict PARTIAL solely because 65 files were blocked by the PII gate
- Evidence: 65 included files absent from the repo because the gate blocked them during the save (never worked around, contents not edited); the only write route was the PII-gated contents helper
- Trial honesty: Full included-file population
- Mechanism: Save and share machinery; the gate-blocked remainder is named, not silently dropped
- Falsifier: Proof from the final repo state (read-back)
- Seats: PLAUS 0.63 | NULL 0.22 | CAT safety (0.80) | SCORE assertion-only (0.95) | LENS mean 0.31 [0.21..0.42]

### C150 terminal-mastery-20261029 : MACHINERY (kind M)
- Claim: The Terminal Operator's Playbook: how an expert trader actually trades with this terminal, organised by the nine questions in fixed order
- Evidence: Decision rules printed as conditionals (a macro event inside a candidate's horizon changes its size class or kills it; a Dial reading with fewer than four counting checks is no reading); stand-down conditions specified
- Trial honesty: TRIAL-COUNT-UNSTATED (playbook)
- Mechanism: Operating machinery: the ancestor of the book's session routines
- Falsifier: Stand-down and kill conditions are stated as rules; their grading lives in the forecast corpus
- Seats: PLAUS 0.78 | NULL 0.35 | CAT safety (0.52) | SCORE assertion-only (1.00) | LENS mean 0.47 [0.44..0.51]

### C151 terminal-missing-pieces-20261103-0345 : MACHINERY (kind M)
- Claim: Best-in-class terminal missing-pieces study: no major page type is missing; the gaps are five desk-level consolidations and the shell
- Evidence: Inventory over the terminal's 100+ pages; gaps specified: benchmark-relative performance, exposure vs small caps, position heatmaps, strategy scorecards with a closed trades log (per family: trades, win rate, total P&L, avg R, expectancy), regime and breadth gauges, plus honest per-card freshness with coverage denominators
- Trial honesty: GitHub project inventory plus the full local page population
- Mechanism: Design machinery; its scorecard and coverage-denominator specs are the ancestors of the book's grading surfaces
- Falsifier: Not applicable (gap study)
- Seats: PLAUS 0.94 | NULL 0.19 | CAT presentation (0.48) | SCORE assertion-only (0.96) | LENS mean 0.59 [0.51..0.65]

### C152 terminal-open-rows-execution-20261104 : MACHINERY (kind M)
- Claim: Terminal Open-Rows Execution 2026-11-04: the SUPN ledger void executed GREEN; the Q4 measurement pass measured PARTIAL by construction
- Evidence: SUPN void executed through the ledger correction mechanism; NEW-badge residue named (26 figure-free partial cards on 23 pages)
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Ledger-correction machinery (the same mechanism class the expression resolver's void handling uses)
- Falsifier: Per-item verdicts with evidence pointers
- Seats: PLAUS 0.70 | NULL 0.50 | CAT safety (0.61) | SCORE assertion-only (0.98) | LENS mean 0.43 [0.39..0.49]

### C153 terminal-public-ready-20261104 : MACHINERY (kind M)
- Claim: Terminal public-ready pass 2026-11-04: morning map and flow family cured; the final freshness sweep re-run on the final tree found 0 STALE
- Evidence: Flow family at session 2026-11-03 across flow-board, unusual-volume, golden-sweep-wire, dark-prints; short-volume freshest day 2026-11-03 with 753 days on record; verdict PARTIAL bounded with open rows named
- Trial honesty: Full page population swept
- Mechanism: Terminal quality machinery
- Falsifier: Freshness sweep re-run on the final tree
- Seats: PLAUS 0.68 | NULL 0.52 | CAT safety (0.67) | SCORE assertion-only (0.79) | LENS mean 0.51 [0.50..0.54]

### C154 terminal-reliability-deep-dive-20261031-2356 : MACHINERY (kind M)
- Claim: Terminal Reliability Deep Dive: engineering doctrine for data-heavy personal terminals (idempotent pipelines, watermark discipline, denominator integrity)
- Evidence: Rules printed: advance a watermark only after a verified load; every ledger entry must reach a terminal grade or an explicit void, because the denominator is the integrity; retention and heartbeat requirements specified
- Trial honesty: Five research areas surveyed
- Mechanism: Reliability machinery; its denominator-integrity rule is the direct ancestor of the shadow resolver's resolve-everything design
- Falsifier: Not applicable (doctrine study)
- Seats: PLAUS 0.96 | NULL 0.22 | CAT safety (0.91) | SCORE assertion-only (0.98) | LENS mean 0.68 [0.59..0.73]

### C155 terminal-repo-links-20261104 : MACHINERY (kind M)
- Claim: Terminal repo links 2026-11-04: repository links placed on every shell surface and verified live
- Evidence: STATUS GREEN, proven on the final published artifact; surfaces not covered named by name
- Trial honesty: All shell surfaces
- Mechanism: Presentation machinery
- Falsifier: Live verification after the build completed
- Seats: PLAUS 0.10 | NULL 0.60 | CAT presentation (0.97) | SCORE assertion-only (0.98) | LENS mean 0.14 [0.11..0.17]

### C156 terminal-state-the-information-20261031 : MACHINERY (kind M)
- Claim: Census of stated information: every hub page's subject visual checked against its own record; overall verdict GREEN
- Evidence: Per-page table (subject visual, internal visual, the record fields that should be plotted); the generic lead and record-section code re-implemented line for line and run over every page's real data.json
- Trial honesty: Full hub page population
- Mechanism: Honesty machinery: a page must show its subject, not its plumbing
- Falsifier: Independent verifier re-ran the tests
- Seats: PLAUS 0.86 | NULL 0.33 | CAT safety (0.41) | SCORE assertion-only (0.45) | LENS mean 0.44 [0.39..0.49]

### C157 terminal-total-audit-20261031 : MACHINERY (kind M)
- Claim: Terminal total audit Round 1 cures: the Friday forecast refresh failure (15 engines) and tools refresh failure (6 refreshers) root-caused and cured at source
- Evidence: Scheduler status masking partial failures as succeeded cured at the job-body source; vol-clock source string recomputed from the panel actually read (1,833 names, at most 404 trading days each, 2025-03-25 to 2026-10-30); scheduled proof pending by calendar, named
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Terminal reliability machinery
- Falsifier: Refresh exit 0 with corrected readings printed; the full scheduled proof was calendar-pending at writing
- Seats: PLAUS 0.77 | NULL 0.30 | CAT safety (0.95) | SCORE assertion-only (0.95) | LENS mean 0.35 [0.27..0.40]

### C158 terminal-total-fix-loop-20261104 : MACHINERY (kind M)
- Claim: Terminal Total-Fix Loop program record (living): the fix loop's iteration log against the owner's acceptance contract
- Evidence: Dark-prints row A1-04 closed: repo blob byte-identical to the local file carrying session 2026-11-04 throughout (combined reading from 500 of 503 stocks, per-stock 778 sessions); a suite assertion failure preserved verbatim ('16.7%' == '16.2%')
- Trial honesty: TRIAL-COUNT-UNSTATED (living record)
- Mechanism: Program bookkeeping machinery
- Falsifier: Per-row closure on destination-side proof
- Seats: PLAUS 0.24 | NULL 0.74 | CAT bookkeeping (0.79) | SCORE assertion-only (0.98) | LENS mean 0.27 [0.24..0.33]

### C159 terminal-total-hookup-20261029 : MACHINERY (kind M)
- Claim: Terminal Total Hookup Ledger: the DEEP price panel built out to full coverage and every feed hooked up with per-lane verdicts
- Evidence: Final DEEP panel GREEN: 15,815 names, 22,346,713 rows, 9,782 names at or above 813 sessions (coded floor had 0 qualifying names before the program); inactive expansion merged 369 of 369 batches (2,240 names, 1,922,958 rows); base panel 1,833 names, 4,731,575 rows; Echo lane publication: WATCH 228, NO TRADE 982, TRAP 595, SETUP 28, 0 errors
- Trial honesty: Full universe enumerated
- Mechanism: Data-coverage machinery: the panel depth every later bar-based study silently depends on
- Falsifier: Counts taken from the panel file and its coverage record
- Seats: PLAUS 0.96 | NULL 0.04 | CAT data (0.99) | SCORE large-insample (0.87) | LENS mean 0.64 [0.58..0.68]

### C160 terminal-ui-implementation-20261031 : MACHINERY (kind M)
- Claim: Terminal UI audit graded against the research spec and the owner's three absolutes: 50 rules graded, violations named
- Evidence: Rules graded 50: 18 PASS, 14 PARTIAL, 18 VIOLATION; worst freshness defect: premium-meter (intraday cadence) at session 2026-10-26, four sessions old; skew-lens as_of 2026-10-14, twelve sessions old, drawn as Live; A2 NO DISCLAIMERS passes with 0 hits
- Trial honesty: Full rule set and page population
- Mechanism: Presentation honesty machinery
- Falsifier: Rule-by-rule grading against the spec
- Seats: PLAUS 0.82 | NULL 0.31 | CAT presentation (0.71) | SCORE large-insample (0.67) | LENS mean 0.36 [0.32..0.49]

### C161 terminal-visual-expression-20261031 : MACHINERY (kind M)
- Claim: Terminal No-Blank-States audit (INFO-MAP): every page classified INFORMATIVE, THIN or BLANK against its own data
- Evidence: Census: INFORMATIVE 52 / THIN 49 / BLANK 1 of 102 pages
- Trial honesty: Full 102-page population
- Mechanism: Presentation machinery
- Falsifier: Per-page map against each page's data.json keys
- Seats: PLAUS 0.33 | NULL 0.71 | CAT presentation (0.94) | SCORE large-insample (0.62) | LENS mean 0.24 [0.19..0.28]

### C162 terminal-visual-live-20261030 : MACHINERY (kind M)
- Claim: Visual Study: a unified pattern catalog of 34 chart and display patterns for the terminal, each with exemplars and failure modes
- Evidence: 34 patterns across seven families; study corpora enumerated (study-trading 11 patterns from nine named products); failure modes printed per pattern (a shifting denominator quietly changes a completeness percent)
- Trial honesty: Multiple product corpora surveyed
- Mechanism: Presentation machinery
- Falsifier: Not applicable (design study)
- Seats: PLAUS 0.19 | NULL 0.70 | CAT presentation (0.84) | SCORE thin-or-external (0.80) | LENS mean 0.28 [0.22..0.33]

### C163 test-all-sleeves-20261029 : MACHINERY (kind M)
- Claim: NUMBERLESS: no report text exists in this directory; the only artifact is an upload progress file
- Evidence: NUMBERLESS (0 characters extracted; the directory carries upload_progress.json only)
- Trial honesty: TRIAL-COUNT-UNSTATED (no report exists)
- Mechanism: Absent: a test-run artifact directory
- Falsifier: Not applicable: no claim was filed
- Seats: PLAUS 0.00 | NULL REFUSED | CAT bookkeeping (0.44) | SCORE assertion-only (0.80) | LENS mean 0.00 [0.00..0.00]

### C164 test-gate-ratchet-architecture-20261019-2018 : MACHINERY (kind M)
- Claim: Five-mission research report: test-gate ratchet architecture, order gateway, charts, positions and ops design for a ~2,700-test desk on a shared 2-core box
- Evidence: Designs printed with numbers: quarantine escape valve capped (gate goes red on the quarantine ledger itself above ~2% flake); retention tiers (raw per-test rows 1 year, JUnit/coverage XML 90 days, logs 30 days); no silent rerun-to-green; validate at write at one choke point with a non-nullable contract field
- Trial honesty: Five missions surveyed against real implementations
- Mechanism: Gate machinery: the ratchet design the desk's regression-blocker law implements
- Falsifier: Not applicable (architecture research)
- Seats: PLAUS 0.93 | NULL 0.56 | CAT safety (0.86) | SCORE assertion-only (0.93) | LENS mean 0.50 [0.42..0.59]

### C165 test-repo-alert-note-20261029 : MACHINERY (kind M)
- Claim: Note on running this desk as your own alert system and replicating the vendor stack (options flow, dark pool, GEX, expected move, insider trackers)
- Evidence: Vendor price bands printed: options flow typically $30 to $100 a month or folded into platforms; insider and cluster-buy trackers $25 to $100 a month
- Trial honesty: TRIAL-COUNT-UNSTATED (not applicable)
- Mechanism: Alerting and vendor-replication machinery
- Falsifier: Not applicable (design note)
- Seats: PLAUS 0.20 | NULL 0.73 | CAT safety (0.27) | SCORE thin-or-external (0.94) | LENS mean 0.18 [0.13..0.20]

### C166 test-repo-audit-20261107 : MACHINERY (kind M)
- Claim: Test Repo full audit 2026-11-07: change audit, consistency census, integrity sweep, privacy scan and divergence risk over the public repo clone
- Evidence: Clone 1.3 GB, 60,170 packed objects; docs/ALL-SLEEVES.json: 654 strategies, algorithm_full 650, algorithm_partial 4 (consistent); denominators reconciled in print: CATALOG 269 cards vs ALL-SLEEVES 654 groups vs roster 336; privacy verdict for the tree at HEAD: clean, no true PII hit
- Trial honesty: Full clone population
- Mechanism: Repository integrity machinery
- Falsifier: Five audit lanes with an evidence directory of 55 raw outputs
- Seats: PLAUS 0.54 | NULL 0.67 | CAT safety (0.62) | SCORE large-insample (0.94) | LENS mean 0.29 [0.25..0.34]

### C167 test-repo-catalog-diff-20261029 : MACHINERY (kind M)
- Claim: Test repo catalog diff: the live desk roster reconciled against docs/CATALOG.json
- Evidence: Present 312, excluded by design 1, genuinely missing 20 (each also checked against the sleeves tree for a same-named file)
- Trial honesty: Full roster enumerated
- Mechanism: Population bookkeeping machinery
- Falsifier: Close phase specified per missing entry
- Seats: PLAUS 0.55 | NULL 0.50 | CAT bookkeeping (0.73) | SCORE large-insample (0.44) | LENS mean 0.26 [0.20..0.31]

### C168 test-repo-discoverability-20261102 : MACHINERY (kind M)
- Claim: Test Repo discoverability probes: independent cold reads test whether the repo's own navigation reaches the right file
- Evidence: PROBE score 28 of 30 NAV-OK (93.3%) against a pass threshold of 27, two partial misses named exactly; PROBE2 repeats the test independently; INDEX.json 2,119,837 bytes landed through the gated contents route; diagnosis: the failure mode is comprehension and routing, not inventory
- Trial honesty: 30 navigation questions per probe
- Mechanism: Navigation machinery
- Falsifier: The probe is itself a falsification test with a pre-set threshold
- Seats: PLAUS 0.86 | NULL 0.25 | CAT presentation (0.94) | SCORE large-insample (0.86) | LENS mean 0.41 [0.30..0.54]

### C169 test-repo-index-20261031 : MACHINERY (kind M)
- Claim: Test repo index build: the INDEX.json and INDEX.md navigation layer for the public repo
- Evidence: NUMBERLESS in the extracted digest (the index is a data artifact, not a prose report; its size and route are proven in C168: INDEX.json 2,119,837 bytes through the gated contents route)
- Trial honesty: TRIAL-COUNT-UNSTATED (data artifact)
- Mechanism: Navigation machinery
- Falsifier: Discoverability probes C168 are its acceptance test
- Seats: PLAUS 0.78 | NULL 0.80 | CAT presentation (0.99) | SCORE assertion-only (0.97) | LENS mean 0.22 [0.17..0.31]

### C170 test-sleeve-algorithm-audit-20261031 : MACHINERY (kind M)
- Claim: Test sleeve algorithm audit and cure 2026-10-31: every canonical strategy's entry, exit, sizing, filters and parameters recovered or named missing
- Evidence: Baseline: 651 canonical strategies, FULL 224 / PARTIAL 427; per-field empty at baseline: entry 208, exit 260, sizing 460, filters 303, parameters 555; after Cure A: FULL 636 / PARTIAL 15; status PARTIAL with acceptance rows still open, GREEN not claimed
- Trial honesty: Full 651-strategy population
- Mechanism: Specification-recovery machinery: the denominator honesty the Trial Register inherits
- Falsifier: Recreation drills (DRILLS.md) and the coverage ledger are the checks
- Seats: PLAUS 0.94 | NULL 0.20 | CAT data (0.54) | SCORE assertion-only (0.79) | LENS mean 0.65 [0.57..0.71]

### C171 three-guide-reconciliation-20261029 : MACHINERY (kind M)
- Claim: Three Guides, One Desk: a three-way reconciliation of the estate's operating guides (FG, KIT, CMP), claim by claim in both directions
- Evidence: Shared invariants extracted (append-only ledger, reconcile before dispatch, saves proven by read-back and restore over an enumerated set); each guide's unique additions named; divergences carried forward by name (D1 halt and kill-switch semantics)
- Trial honesty: Three full guides reconciled
- Mechanism: Doctrine bookkeeping machinery
- Falsifier: Bidirectional presence and absence checks per claim
- Seats: PLAUS 0.69 | NULL 0.61 | CAT bookkeeping (0.87) | SCORE assertion-only (0.94) | LENS mean 0.45 [0.40..0.50]

### C172 todd-granly-postcard-chalfont-20261029-0047 : MACHINERY (kind M)
- Claim: Investigation of the 'Todd Granly' traveling-storyteller postcard received in Chalfont, PA: no real sender exists behind it
- Evidence: No person named Todd Granly (or Granlye/Granlee) appears in any people-search, social, news, court or performer listing found; the printed address is a working McDonald's (4272 County Line Rd, Chalfont, verified live 2026-10-28); the phone number has zero online footprint and its block is a VoIP wholesale carrier prefix
- Trial honesty: TRIAL-COUNT-UNSTATED (investigation)
- Mechanism: Investigation machinery (not a market study)
- Falsifier: Multi-source negative search is the test; the near-match 'Todd Granley' is a different, retired person
- Seats: PLAUS 0.08 | NULL REFUSED | CAT intelligence (0.88) | SCORE thin-or-external (0.94) | LENS mean 0.06 [0.05..0.07]

### C173 trade-plan-distillation-patterns-20261016-1344 : MACHINERY (kind M)
- Claim: Trade-plan distillation patterns: how the best alert products reduce deep analysis to one actionable plan
- Evidence: Pattern printed across products: three numbers in fixed order (entry zone, stop, targets T1/T2); position size expressed as risk, never shares (worked examples use max 0.5-1% account risk); the trust layer is three short lines: why in one sentence, what kills it, and a base rate ('similar setups did X, n = ...') or an explicit absence
- Trial honesty: Product pattern catalog surveyed
- Mechanism: Card-design machinery: the direct ancestor of the book's card format and its base-rate line
- Falsifier: Stop and invalidation kept as separate fields precisely so the falsifier survives distillation (a design rule, graded wherever cards are graded)
- Seats: PLAUS 0.95 | NULL 0.33 | CAT presentation (0.80) | SCORE assertion-only (0.59) | LENS mean 0.59 [0.51..0.65]

### C174 trader-ascension-20261112 : MACHINERY (kind M)
- Claim: Trader Ascension Pass 1: how the best operators run firms, pods and themselves, distilled into transfer notes for this book
- Evidence: Principles printed with their numbers treated honestly (pod drawdown de-risking at 5 and 7.5: 'the value is not the exact numbers, the value is pre-commitment and automaticity'); C1: count every trial and deflate every Sharpe by the search that produced it; reading rule: do not build step N machinery until the falsifier for the upgrade that owns step N is written
- Trial honesty: Practitioner and firm literature surveyed by section
- Mechanism: Operating-doctrine machinery
- Falsifier: The pass is doctrine extraction; its rules are graded wherever the book's routines run
- Seats: PLAUS 0.81 | NULL 0.61 | CAT safety (0.54) | SCORE assertion-only (0.70) | LENS mean 0.49 [0.45..0.52]

### C175 traderdev-teardown-20261109 : MACHINERY (kind M)
- Claim: REA teardown of the TraderDev strategy marketplace: its headline numbers are percent-of-equity compounding artifacts, and its full result schema is extractable
- Evidence: Worked example printed: 100% percent-of-equity compounding over multi-year windows turns a +55% win-rate BNB strategy into a printed +19,978.73%; 'the arithmetic is honest; the sizing assumption is the' trick; result summary schema 60 fields recovered; API census verified live 2026-11-09; grade PARTIAL with open rows named
- Trial honesty: Full public catalog extracted
- Mechanism: Claim-audit machinery for external strategy marketplaces
- Falsifier: KPI recomputation from the extracted trade rows is the check
- Seats: PLAUS 0.81 | NULL 0.57 | CAT intelligence (0.56) | SCORE thin-or-external (0.79) | LENS mean 0.50 [0.41..0.61]

### C176 trading-desk-reliability-research-20261102-0521 : MACHINERY (kind M)
- Claim: Trading Desk Reliability Research: the minimum stack for a desk that is 100% operational for a trading week
- Evidence: Prescriptions printed: a single pre-open READY gate that fails closed (hash-chained ready.json; sleeves refuse to run without a fresh valid verdict); exhaustive sleeve registry set-equality diff, count = 336 at writing (the Knight Capital lesson: failure on 1 of 8 servers); order state-machine with reject-rate tripwires and a drilled kill switch
- Trial honesty: Four research domains surveyed
- Mechanism: Reliability machinery: the ancestor of the morning inspection's READY / NOT READY verdict
- Falsifier: Not applicable (reliability research)
- Seats: PLAUS 0.95 | NULL 0.36 | CAT safety (0.99) | SCORE assertion-only (0.98) | LENS mean 0.59 [0.54..0.66]

### C177 trading-mandate-audit-2026-11-11 : MACHINERY (kind M)
- Claim: Trading Mandate Audit: the owner's trading statements 2026-10-11 through 2026-11-11 extracted and graded against destination-side evidence
- Evidence: 113 statements graded: Grade 1 (in force and followed) 50, Grade 2 (lost) 3, Grade 3 (superseded) 5, Grade 4 (partial) 55; lost words (grades 2 and 4) 58; extraction PARTIAL by construction (clean pages cover 2026-10-11 00:21 ET through 2026-10-25 ~13:12 ET, 21 flagged pages as gaps)
- Trial honesty: Full statement population in the covered window
- Mechanism: Mandate bookkeeping machinery: the direct ancestor of the nightly mandate audit
- Falsifier: Grades rest on destination-side evidence pointers per statement
- Seats: PLAUS 0.93 | NULL 0.59 | CAT bookkeeping (0.99) | SCORE assertion-only (0.46) | LENS mean 0.55 [0.50..0.61]

### C178 trading-strategy-calibration-best-practi-20260929-1605 : MACHINERY (kind M)
- Claim: Best practices for calibrating systematic strategies: walk-forward design, plateau robustness, trial counting and bracket calibration
- Evidence: Prescriptions printed with numbers: in-sample 4-6x the out-of-sample window; degradation >30% under +/-20% parameter perturbation marks a curve-fit; require t ~ 3.0 rather than 2.0 under broad search, with the Deflated Sharpe Ratio; stops ~2-3x ATR as a starting point refined by MAE/MFE (stop just beyond the 90-95th percentile of winning-trade MAE); the limit printed too: DSR/PBO/RC/SPA correct selection bias only, never lookahead, omitted trials, cost-model or survivorship errors
- Trial honesty: Practitioner literature surveyed by question
- Mechanism: Calibration machinery: the methods canon the admission exam and the mutation campaign apply
- Falsifier: Not applicable (methods canon)
- Seats: PLAUS 0.94 | NULL 0.59 | CAT measurement (0.84) | SCORE thin-or-external (0.69) | LENS mean 0.57 [0.51..0.68]

### C179 trendspider-bottom-catcher-teardown-20261111 : WATCH (kind E)
- Claim: TrendSpider Bottom Catcher teardown program (Phase 0 REA reread): the vendor scanner's criteria extracted, with a falsifiable claim stated for its catch events
- Evidence: 358 of 1,014 indicators (35%) serve their complete JavaScript source through the public API (3,314,305 characters, median 4,210); no performance claims exist on any of the three listings (no win rate, profit factor, return or trade count asserted, so no vendor arithmetic to recompute); REA tooling pinned at 6.8.0 with a PARTIAL version-match verdict
- Trial honesty: Full 1,014-indicator catalog census
- Mechanism: Bottom-catcher scanner: threshold cross within 3 candles with a -25% floor, monthly timeframe default
- Falsifier: Stated in the report: on a point-in-time S&P 500 universe at the monthly timeframe (the scanner's default), catch events passing the shipped criteria (threshold cross within 3 candles, % > -25) are to be followed per the claim; no run of it is filed in this unit
- Seats: PLAUS 0.23 | NULL 0.78 | CAT none-real (0.68) | SCORE large-insample (0.48) | LENS mean 0.33 [0.12..0.46]

### C180 trendspider-soxl-pmhigh-test-20261103 : WATCH (kind E)
- Claim: SOXL premarket-high breakout, hold to close: replication on our own data (the primary replication behind C131)
- Evidence: 138,643 bars, 2016-01-04 to 2026-11-02: zero-cost +2573.41%, CAGR 35.45%, max DD -49.48%, 1,116 trades, win rate 56.27%, average +0.363%; 15:45-exit sensitivity +1875.68%, average +0.331%; cost case (5bp per side) +775.78%, average +0.263%, PF 1.29, max DD -57.77%; known-answer harness test (T-103) passed before any real-data verdict
- Trial honesty: One frozen specification replicated; its four improvement variants are counted in C131
- Mechanism: Premarket-high breakout on SOXL, hold to close, no stop, no target, no overnight holds
- Falsifier: Pre-stated falsification uses the cost case; the installed sleeve's forward paper record is the live falsifier
- Seats: PLAUS 0.48 | NULL 0.51 | CAT regime-fluke (0.52) | SCORE large-insample (1.00) | LENS mean 0.34 [0.30..0.37]

### C181 trendspider-sso-opus-improve-20261103 : WATCH (kind E)
- Claim: SSO Opus 5.5 Swing 15m improvement study: diagnostics split the baseline's profit engine from its bleed, and pre-registered variants were screened on development then judged once on validation
- Evidence: Setup B earns 3x Setup A per trade (average +1.197%, PF 2.41, n=63) versus A (average +0.399%, PF 1.51, n=202); 17 TAKE_PROFIT trades produce 72.1% of all gross profit; the TIME_25 exit class is the bleed (166 trades, average -0.79%, PF 0.06); variants include trailing stop widened 7% to 10% and time-exit changes, judged on the 2022-2026 validation window at 5bp
- Trial honesty: Variants pre-registered in VARIANTS.md; development 2016-2021, validation 2022-2026
- Mechanism: Two-setup 15-minute swing system on SSO with trailing stop and time exits; the improvement claim rests on exit-class surgery
- Falsifier: Development/validation split with a single validation judgment, per the frozen protocol
- Seats: PLAUS 0.53 | NULL 0.64 | CAT multiple-testing (0.84) | SCORE large-insample (0.57) | LENS mean 0.34 [0.33..0.37]

### C182 trendspider-sso-opus-test-20261103 : WATCH (kind E)
- Claim: SSO Opus 5.5 Swing 15m: replication on our own data of the vendor strategy as frozen
- Evidence: 2,725 trading days, 2016-01-04 to 2026-11-02: zero-cost +285.02%, CAGR 13.26%, max DD -27.30%, 265 trades, win rate 36.98%, average +0.588%, PF 1.76; cost case (5bp per side) +176.95%, average +0.436%, PF 1.53, max DD -31.55%; setup mix 202 A trades, 63 B trades; known-answer harness test passed first
- Trial honesty: One frozen specification; improvement variants counted in C181
- Mechanism: 15-minute swing entries on a 2x levered S&P ETF with a -3.5% stop, 7% trailing stop and time exits
- Falsifier: Pre-stated falsification on the cost case; forward record is the live falsifier
- Seats: PLAUS 0.62 | NULL 0.43 | CAT none-real (0.71) | SCORE large-insample (0.95) | LENS mean 0.47 [0.42..0.52]

### C183 triad-protocol-20261112 : MACHINERY (kind M)
- Claim: Triad Protocol adoption map: the three-node operating protocol mapped element by element against what already runs here
- Evidence: Gaps named honestly (cross-prompt partially present, cognitive coverage compensated silently before the protocol); every cycle post must carry observations pooled, one cross-prompt per peer, positions with falsifiers and the coverage line
- Trial honesty: TRIAL-COUNT-UNSTATED (protocol document)
- Mechanism: Collaboration machinery
- Falsifier: Standing checks listed in the map
- Seats: PLAUS 0.71 | NULL 0.72 | CAT presentation (0.51) | SCORE assertion-only (0.99) | LENS mean 0.30 [0.22..0.41]

### C184 trullas-exhaustive-pass-20261025-1414 : MACHINERY (kind M)
- Claim: David Trullás exhaustive completion pass (first): his MACD triple-divergence method mined gap by gap against 13 named questions
- Evidence: Rules recovered as printed (MACD fast crosses above 0 to buy; divergences can chain across up to four consecutive extremes with decreasing volume; Fib levels 23/48/50/61/100 with the 48 flagged as a likely typo for 38.2); gaps 1-13 each verdicted
- Trial honesty: 13 gaps enumerated
- Mechanism: Extraction machinery for a discretionary futures method
- Falsifier: Not applicable (source mining)
- Seats: PLAUS 0.40 | NULL 0.53 | CAT intelligence (0.98) | SCORE assertion-only (0.72) | LENS mean 0.25 [0.21..0.26]

### C185 trullas-exhaustive-pass-20261025-1515 : MACHINERY (kind M)
- Claim: David Trullás exhaustive completion pass (second): the championship record resolved and the remaining spec gaps narrowed
- Evidence: Q2 2026: he won, 1st place, 2,222.6% (official, Final), a fifth consecutive title; Q3 2026 also 1st at 1,350.8% (Final Pending Audit), a sixth; the un-located X claim ('five consecutive championships', '2,200% 90-day return') matches the official Q2 result almost exactly; still open by name: MACD periods never stated anywhere mined, RSI thresholds, the exact Fib anchor recipe, a fixed TP1/TP2 split, risk % per trade
- Trial honesty: Gap list carried from C184, each closed or named open
- Mechanism: Extraction machinery; the method itself stays unbuildable as specified because its core parameters were never published, which is this unit's operative finding
- Falsifier: Official World Cup standings are the deciding source; one interview remained unmined (transcript service returned HTTP 429), named
- Seats: PLAUS 0.19 | NULL 0.51 | CAT intelligence (0.97) | SCORE assertion-only (0.50) | LENS mean 0.20 [0.16..0.26]

### C186 trullas-triple-divergence-specs-20261025-0644 : MACHINERY (kind M)
- Claim: David Trullás MACD triple-divergence exact published specifications (first specs pass)
- Evidence: Championship framing printed (four-time champion at writing, 1321% quarterly return in the Rankia description); beginner rule recovered: enter at the 23.6 Fib, take profit at 38.2 ('from 23 to 38'); secondary-reconstruction claims flagged for verification rather than adopted
- Trial honesty: TRIAL-COUNT-UNSTATED (spec sheet)
- Mechanism: Extraction machinery
- Falsifier: Not applicable (spec extraction)
- Seats: PLAUS 0.11 | NULL 0.74 | CAT intelligence (0.99) | SCORE assertion-only (0.65) | LENS mean 0.20 [0.17..0.21]

### C187 trullas-triple-divergence-specs-20261025-0745 : MACHINERY (kind M)
- Claim: David Trullás strategy reconstruction, source-cited: what is primary, what is partial, and what the secondary reconstruction asserts without support
- Evidence: Official standings printed (2025 Q1 2nd at 291.00%, Q2 1st at 712.10%, futures day-trading division only); TP1 at 38.2% is PRIMARY; several secondary claims (exact short-side Fib anchor, '30-second to 5-minute' timeframes, 'avoid the open', breakeven stops, daily limits) are NOT stated in the primary sources and are marked as such
- Trial honesty: TRIAL-COUNT-UNSTATED (reconstruction)
- Mechanism: Extraction machinery with a primary/secondary/unverified marking discipline
- Falsifier: Primary-source citation standard applied per claim
- Seats: PLAUS 0.57 | NULL 0.71 | CAT intelligence (0.97) | SCORE assertion-only (0.65) | LENS mean 0.29 [0.25..0.35]

### C188 week-readiness-20261102 : MACHINERY (kind M)
- Claim: Week Readiness cure round 2 after AUDIT1: Qulla producer cured, gate completed solo, one more real defect found and cured; the $0.45 reconcile discrepancy still open
- Evidence: Overnight health roll printed: 218 of 336 sleeves FED, 70 UNFED, 48 PARKED; dispatcher state 15,047 rows; ENJ door-rule defect: pre-cure failures, 4 passed post-cure, neighbor suites green; D1 $0.45 discrepancy carried STILL OPEN, evidence advanced, not cured, not fenced
- Trial honesty: TRIAL-COUNT-UNSTATED (cure report)
- Mechanism: Readiness machinery
- Falsifier: Completed solo gate on the final tree is the check
- Seats: PLAUS 0.44 | NULL 0.27 | CAT safety (0.95) | SCORE assertion-only (0.73) | LENS mean 0.29 [0.24..0.36]

### C189 week-readiness-round2-20261102 : MACHINERY (kind M)
- Claim: Week-Readiness Round 2 research: site building, pipelines, visualization and QA for data terminals (research only, nothing implemented, nothing GREEN by its own statement)
- Evidence: Additions over round 1 printed: in-band freshness signalling (GitHub Pages gives no cache headers), deterministic byte-identical builds, visual regression testing with a determinism checklist, freeze-the-data / freeze-the-code separation; the 2026-10-31 false green (mechanism proven, visual never tested) named as the failure this prevents
- Trial honesty: Four domains surveyed
- Mechanism: Quality machinery
- Falsifier: Not applicable (research)
- Seats: PLAUS 0.84 | NULL 0.69 | CAT safety (0.79) | SCORE assertion-only (0.98) | LENS mean 0.28 [0.22..0.37]

### C190 week-recap-deaddrop-20261031 : MACHINERY (kind M)
- Claim: Week Recap 2026-10-25 to 2026-10-31: the desk week, all sleeves and the terminal, with open defects by name
- Evidence: Desk +7.74% since the $1M paper epoch (2026-10-26) vs SPY -1.25% and QQQ -3.05%; Friday alone +13.60% from Thursday's proven close of $948,382.12 vs SPY -1.77% and QQQ -3.47%; the EDGE spread estimator REJECTED here too (14-name panel, 129 daily SIP bars, median signed error +2,237%, about 23x overstatement, against a pre-fixed 50% bound; C112 prints the same rejection at +2,325%)
- Trial honesty: Full week population
- Mechanism: Program bookkeeping machinery
- Falsifier: Counts tied to the known-good snapshot (regression gate 1,550 tests OK, Tensor pins all MATCH)
- Seats: PLAUS 0.19 | NULL 0.58 | CAT bookkeeping (0.97) | SCORE large-insample (0.47) | LENS mean 0.23 [0.20..0.24]

### C191 week-recap-for-claude-20261101 : MACHINERY (kind M)
- Claim: Week recap to Claude, 2026-10-26 to 2026-11-01: the meticulous cross-node record of the desk, terminal, book, research and saves
- Evidence: Seal seq 33 closed PROVEN 2026-10-31 (workspace HEAD 86fe2f8f, remote main ddf428d8, 43,054 paths compared, zero missing, zero SHA diffs); restore drills passed 43,001 of 43,001 blobs; honest caveat printed: per-sleeve P&L credit stays unreliable until the virtual-book divergence cure lands
- Trial honesty: Full week population
- Mechanism: Cross-node memory machinery
- Falsifier: Destination-side proofs cited per section
- Seats: PLAUS 0.57 | NULL 0.52 | CAT bookkeeping (0.98) | SCORE assertion-only (0.54) | LENS mean 0.23 [0.18..0.32]

### C192 weight-lag-landing-20261031 : MACHINERY (kind M)
- Claim: Weight-Lag Landing program: the weight-lag fixture updates and re-application landed, full gate and live adoption GREEN on the final system state
- Evidence: Live adoption proven by the runner executing the landed tree in dispatch mode (runner pid and cycle/heartbeat recorded); blocker tests test_weight_lag_20261031_blockers.py green on the final tree; 20 fixtures could not be updated without weakening intent and were handled by the named STOP rule
- Trial honesty: TRIAL-COUNT-UNSTATED (program record)
- Mechanism: Desk machinery (fixture and weighting cure)
- Falsifier: Gate plus live-runner proof on the final state
- Seats: PLAUS 0.33 | NULL 0.50 | CAT safety (0.95) | SCORE assertion-only (0.71) | LENS mean 0.44 [0.34..0.50]

### C193 what-graphs-and-terminals-are-20261031-2116 : MACHINERY (kind M)
- Claim: What graphs are, what terminals are, how humans parse numbers: the perceptual-science foundation for the terminal's display rules
- Evidence: Cleveland & McGill encoding ranking carried; misleading-form evidence printed (Yang et al.: 83.5% of participants showed the truncated-axis effect and instruction did not remove it); honesty note printed: no large trial reporting a dual-axis misreading rate was found, 'anyone quoting one is inventing it'
- Trial honesty: Literature surveyed by part
- Mechanism: Presentation machinery
- Falsifier: Not applicable (science survey)
- Seats: PLAUS 0.89 | NULL 0.20 | CAT presentation (0.71) | SCORE thin-or-external (0.98) | LENS mean 0.48 [0.41..0.49]

### C194 winning-sleeves-20261031 : MACHINERY (kind M)
- Claim: Winning sleeves of the week: FIFO attribution of the week's fills and full algorithm extraction for the top 10 winners
- Evidence: 1,974 fills in the epoch, 1,948 through Friday close; residual -$472.40 (0.61% of the move) unattributed in the journal and named, not smoothed (the journal records fills only, never fee activities); top 10 by week % are all FIFO winners, each extracted from desk source; verdict PARTIAL by construction
- Trial honesty: Full fill population of the epoch
- Mechanism: Attribution machinery
- Falsifier: Attribution reconciled against the fill record with the residual printed
- Seats: PLAUS 0.12 | NULL 0.49 | CAT bookkeeping (0.47) | SCORE large-insample (0.74) | LENS mean 0.48 [0.41..0.50]

## Connections

### Cluster survival choices (typed seat, argmax with probability)

| Cluster | Members | Seat pick | P |
| vendor-claim-audits | C117, C126, C132, C175, C179, C086 | C175 (traderdev-teardown-20261109) | 0.71 |
| vlm-chart-reading | C086, C089, C134, C135, C032, C034 | C089 (llm-visual-acuity-enhancement-20261008-0254) | 0.29 |
| deflation-and-trials | C007, C010, C029, C031, C066, C178, C174 | C178 (trading-strategy-calibration-best-practi-20260929-1605) | 0.95 |
| earnings-events | C008, C100, C056, C057 | C100 (modern-options-trading-deep-dive-20261113-0046) | 0.87 |
| saty-stack | C121, C122, C130 | C121 (saty-code-acquisition-rea-20261021-2223) | 0.73 |
| replication-gauntlets | C131, C180, C181, C182, C099 | C131 (soxl-pmhigh-sleeve-and-variants-20261103) | 0.52 |
| population-denominators | C047, C128, C166, C167, C170, C127 | C166 (test-repo-audit-20261107) | 0.47 |
| save-and-transport | C068, C069, C149, C191 | C069 (github-save-pipeline-best-practices-20261023-0449) | 0.93 |
| freshness-and-census | C125, C140, C147, C153, C160, C161 | C125 (site-visual-polish-20261030) | 0.47 |
| card-discipline | C124, C150, C173, C136 | C173 (trade-plan-distillation-patterns-20261016-1344) | 0.51 |
| trullas-extraction | C184, C185, C186, C187 | C187 (trullas-triple-divergence-specs-20261025-0745) | 0.97 |
| attention-signals | C066, C004, C005, C067 | C067 (gestalt-100-20261110) | 0.84 |

### Strongest corroborations (seat CORROB >= 0.70): 23 pairs

| Pair | Units | CORROB | CONTRA | Deciding check |
| PAIR002 | C086 x C135 | 0.95 | 0.05 | Run one shared candlestick set through both protocols: direction accuracy near 53% in both confirms the ceiling is a property of the reader class, not of either sample. |
| PAIR010 | C131 x C180 | 0.95 | 0.05 | Already decided by the record: both units report the same frozen replication. The forward check is the installed sleeve's live paper record against the printed cost-case numbers. |
| PAIR033 | C020 x C068 | 0.95 | 0.01 | Recompute the shared quantity (rest, ceiling, points, github) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR070 | C036 x C159 | 0.95 | 0.03 | Recompute the shared quantity (floor, panel, deep, names) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR090 | C036 x C120 | 0.93 | 0.00 | Recompute the shared quantity (floor, panel, cured, code) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR029 | C028 x C033 | 0.90 | 0.09 | Recompute the shared quantity (demonstrated, stage, classification, typed) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR061 | C116 x C175 | 0.88 | 0.05 | Recompute the shared quantity (marketplace, traderdev, teardown) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR081 | C015 x C178 | 0.84 | 0.06 | Recompute the shared quantity (deflated, counting, sharpe) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR019 | C033 x C034 | 0.83 | 0.10 | Recompute the shared quantity (pilot, excess, stage, classification) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR048 | C041 x C044 | 0.83 | 0.05 | Recompute the shared quantity (timeout, worker, heartbeat) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR016 | C004 x C067 | 0.79 | 0.09 | Recompute the shared quantity (sndk, soxx, per-name, conditioner) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR017 | C112 x C190 | 0.77 | 0.02 | Recompute the estimator's signed error on the 14-name, 129-day panel from the SIP sample: the two printed figures (+2,325% and +2,237%) must reconcile to one named statistic (mean vs median), or one is a transcription error. The rejection itself is not in dispute. |
| PAIR001 | C004 x C005 | 0.76 | 0.02 | Recompute the shared quantity (refreshed, ranker, views, sndk) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR050 | C174 x C178 | 0.75 | 0.05 | Count one sleeve family's registered trials both ways (pod doctrine vs calibration canon); the counts must agree or every DSR computed from them differs by construction. |
| PAIR057 | C066 x C178 | 0.75 | 0.05 | Recompute the shared quantity (exam, plateau, admission) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR015 | C181 x C182 | 0.73 | 0.04 | Already decided by the record: the improvement study's diagnostics and the replication's headline table describe the same frozen system. The forward check is the sleeve's live record against the validation-window statistics. |
| PAIR022 | C028 x C034 | 0.73 | 0.09 | Recompute the shared quantity (disagreement, decisions, stage, classification) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR024 | C127 x C130 | 0.73 | 0.10 | Recompute the shared quantity (live-firing, armed-proven, fixture-proven, unfed) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR036 | C015 x C033 | 0.73 | 0.06 | Recompute the shared quantity (weights, simple, cited, beat) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR058 | C186 x C187 | 0.73 | 0.05 | Recompute the shared quantity (trull, david, claims, extraction) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR072 | C055 x C076 | 0.73 | 0.05 | Recompute the shared quantity (addendum, efficiency, mined, mechanisms) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR006 | C080 x C081 | 0.72 | 0.05 | Recompute the shared quantity (inspora, view, featured, createdat) from both primary sources on one denominator; corroboration stands only if it agrees in sign and rough magnitude in both records. |
| PAIR138 | C086 x C089 | 0.72 | 0.05 | Cross-run each evaluation's item set under the other's protocol; agreement of the two ceilings (about 53% vs a about 51% numeric baseline) is the corroboration test. |

### Strongest contradictions (seat CONTRA >= 0.50): 0 pairs

| Pair | Units | CONTRA | CORROB | Deciding check |
No pair reached the 0.50 contradiction threshold. The highest CONTRA in the bank is 0.19 (PAIR008, C047 x C127), and the bank's contradiction signal is weak throughout: on the printed records, the archive's studies disagree with each other far less than they corroborate or ignore each other. One pair carries a recorded refusal instead of a CORROB probability: PAIR038 (C028 x C032), refused by the endpoint and recorded as a refusal, never coerced.

### Full pair table (all 153, sorted by strongest seat signal)

| Pair | Units | Source | CORROB | CONTRA | Deciding check |
| PAIR002 | C086 x C135 | mechanical+seeded | 0.95 | 0.05 | Run one shared candlestick set through both protocols: direction accuracy near 53% in both confirms the ceiling is a property of the reader class, not of either sample. |
| PAIR010 | C131 x C180 | mechanical+seeded | 0.95 | 0.05 | Already decided by the record: both units report the same frozen replication. The forward check is the installed sleeve's live paper record against the printed cost-case numbers. |
| PAIR033 | C020 x C068 | mechanical | 0.95 | 0.01 | Recompute the shared quantity (rest, ceiling, points, github) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR070 | C036 x C159 | mechanical | 0.95 | 0.03 | Recompute the shared quantity (floor, panel, deep, names) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR090 | C036 x C120 | mechanical | 0.93 | 0.00 | Recompute the shared quantity (floor, panel, cured, code) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR029 | C028 x C033 | mechanical | 0.90 | 0.09 | Recompute the shared quantity (demonstrated, stage, classification, typed) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR061 | C116 x C175 | mechanical | 0.88 | 0.05 | Recompute the shared quantity (marketplace, traderdev, teardown) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR081 | C015 x C178 | mechanical | 0.84 | 0.06 | Recompute the shared quantity (deflated, counting, sharpe) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR019 | C033 x C034 | mechanical | 0.83 | 0.10 | Recompute the shared quantity (pilot, excess, stage, classification) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR048 | C041 x C044 | mechanical | 0.83 | 0.05 | Recompute the shared quantity (timeout, worker, heartbeat) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR016 | C004 x C067 | mechanical | 0.79 | 0.09 | Recompute the shared quantity (sndk, soxx, per-name, conditioner) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR017 | C112 x C190 | mechanical+seeded | 0.77 | 0.02 | Recompute the estimator's signed error on the 14-name, 129-day panel from the SIP sample: the two printed figures (+2,325% and +2,237%) must reconcile to one named statistic (mean vs median), or one is a transcription error. The rejection itself is not in dispute. |
| PAIR001 | C004 x C005 | mechanical | 0.76 | 0.02 | Recompute the shared quantity (refreshed, ranker, views, sndk) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR050 | C174 x C178 | mechanical+seeded | 0.75 | 0.05 | Count one sleeve family's registered trials both ways (pod doctrine vs calibration canon); the counts must agree or every DSR computed from them differs by construction. |
| PAIR057 | C066 x C178 | mechanical | 0.75 | 0.05 | Recompute the shared quantity (exam, plateau, admission) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR015 | C181 x C182 | mechanical+seeded | 0.73 | 0.04 | Already decided by the record: the improvement study's diagnostics and the replication's headline table describe the same frozen system. The forward check is the sleeve's live record against the validation-window statistics. |
| PAIR022 | C028 x C034 | mechanical | 0.73 | 0.09 | Recompute the shared quantity (disagreement, decisions, stage, classification) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR024 | C127 x C130 | mechanical | 0.73 | 0.10 | Recompute the shared quantity (live-firing, armed-proven, fixture-proven, unfed) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR036 | C015 x C033 | mechanical | 0.73 | 0.06 | Recompute the shared quantity (weights, simple, cited, beat) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR058 | C186 x C187 | mechanical | 0.73 | 0.05 | Recompute the shared quantity (trull, david, claims, extraction) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR072 | C055 x C076 | mechanical | 0.73 | 0.05 | Recompute the shared quantity (addendum, efficiency, mined, mechanisms) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR006 | C080 x C081 | mechanical | 0.72 | 0.05 | Recompute the shared quantity (inspora, view, featured, createdat) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR138 | C086 x C089 | seeded | 0.72 | 0.05 | Cross-run each evaluation's item set under the other's protocol; agreement of the two ceilings (about 53% vs a about 51% numeric baseline) is the corroboration test. |
| PAIR083 | C018 x C116 | mechanical | 0.63 | 0.03 | Recompute the shared quantity (biotech2k, registered, falsifier) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR046 | C184 x C187 | mechanical | 0.62 | 0.06 | Recompute the shared quantity (futures, trull, david, extraction) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR130 | C015 x C066 | mechanical | 0.61 | 0.05 | Recompute the shared quantity (meta-labeling, beat, must) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR008 | C047 x C127 | mechanical | 0.58 | 0.19 | Recompute the shared quantity (firing, live-firing, armed-proven, pre-open) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR075 | C003 x C043 | mechanical | 0.56 | 0.05 | Recompute the shared quantity (gates, intent, reconciliation) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR023 | C010 x C029 | mechanical | 0.55 | 0.00 | Recompute the shared quantity (hou-xue-zhang, hurdle, anomalies, correlation) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR030 | C166 x C167 | mechanical | 0.52 | 0.05 | Recompute the shared quantity (docs, reconciled, catalog, roster) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR129 | C068 x C069 | mechanical | 0.49 | 0.01 | Recompute the shared quantity (endpoint, pipeline, github, tree) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR005 | C114 x C115 | mechanical | 0.48 | 0.12 | Recompute the shared quantity (quants, evidence-packet, rebalance-policy, weight-lag) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR032 | C150 x C173 | mechanical+seeded | 0.46 | 0.03 | Same field-by-field card audit as C173 x C124, against the playbook's decision routines. |
| PAIR071 | C014 x C063 | mechanical | 0.46 | 0.05 | Recompute the shared quantity (documentation, mechanics, order, alpaca) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR139 | C007 x C010 | seeded | 0.46 | 0.05 | Verify both deflations count trials the same way (nominal trials at generation, not post-hoc survivors); if either counted differently, the two DSRs are not comparable and one must be recomputed. |
| PAIR026 | C043 x C044 | mechanical | 0.45 | 0.04 | Recompute the shared quantity (separate, orders, account, shared) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR107 | C036 x C144 | mechanical | 0.45 | 0.06 | Recompute the shared quantity (dark, engines, forecast, sessions) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR069 | C051 x C094 | mechanical | 0.44 | 0.05 | Recompute the shared quantity (changelog, landing, canon, skill) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR088 | C018 x C178 | mechanical | 0.44 | 0.05 | Recompute the shared quantity (plateau, ratio, window) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR073 | C146 x C163 | mechanical | 0.43 | 0.00 | Recompute the shared quantity (characters, directory, numberless, extracted) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR037 | C052 x C055 | mechanical | 0.42 | 0.05 | Recompute the shared quantity (harvest, existing, landing, mechanisms) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR064 | C120 x C144 | mechanical | 0.42 | 0.05 | Recompute the shared quantity (analogue, accrual, sessions) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR007 | C047 x C130 | mechanical | 0.41 | 0.09 | Recompute the shared quantity (live-firing, armed-proven, fixture-proven, unfed) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR039 | C144 x C158 | mechanical | 0.39 | 0.05 | Recompute the shared quantity (combined, per-stock, session, sessions) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR153 | C117 x C175 | seeded | 0.37 | 0.03 | Recompute the public part of one C117-listed vendor ledger (the 43 public signals of the 160) with C175's method; the 117 premium signals are unverifiable by construction, which is itself the verdict. |
| PAIR152 | C175 x C132 | seeded | 0.36 | 0.05 | Apply C175's recomputation method to C132's surfaces: hardcoded constants fail recomputation from trade rows by construction, which is the shared finding. |
| PAIR137 | C089 x C135 | seeded | 0.35 | 0.04 | Same shared-set check as C086 x C135, against this unit's protocol and baseline. |
| PAIR150 | C173 x C124 | seeded | 0.35 | 0.05 | Score the current card format against both pattern sets field by field; a missing base-rate line or a merged stop/invalidation field is the deciding gap. |
| PAIR021 | C121 x C122 | mechanical+seeded | 0.33 | 0.07 | Recompute the trigger statistics from the transcribed source (C121) on desk data: if the 73.8% / 97.1% rates do not reproduce, C122's doctrine numbers are vendor claims, not measurements. |
| PAIR077 | C048 x C188 | mechanical | 0.33 | 0.03 | Recompute the shared quantity (health, roll, unfed, parked) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR140 | C007 x C066 | seeded | 0.33 | 0.05 | Apply C007's deflation standard to C066's surviving insider-cluster signal at its true sibling count; survival at a high deflated Sharpe keeps it a candidate, failure retires it. |
| PAIR013 | C185 x C186 | mechanical | 0.32 | 0.08 | Recompute the shared quantity (championship, macd, trull, david) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR027 | C047 x C048 | mechanical | 0.32 | 0.08 | Recompute the shared quantity (health, roll, unfed, tensor) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR014 | C184 x C186 | mechanical | 0.31 | 0.09 | Recompute the shared quantity (triple-divergence, macd, recovered, trull) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR018 | C022 x C136 | mechanical | 0.31 | 0.05 | Recompute the shared quantity (bulkowski, head-and-shoulders, bottom, samples) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR085 | C036 x C157 | mechanical | 0.30 | 0.00 | Recompute the shared quantity (engines, panel, names, forecast) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR009 | C114 x C192 | mechanical | 0.29 | 0.06 | Recompute the shared quantity (updated, weight-lag, blocker, runner) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR011 | C168 x C169 | mechanical | 0.29 | 0.05 | Recompute the shared quantity (navigation, gated, contents, route) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR052 | C075 x C079 | mechanical | 0.29 | 0.05 | Recompute the shared quantity (application, local, canon, skill) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR079 | C039 x C163 | mechanical | 0.29 | 0.00 | Recompute the shared quantity (directory, exists, artifact, numberless) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR091 | C050 x C052 | mechanical | 0.29 | 0.05 | Recompute the shared quantity (force, bytes, does, mechanisms) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR035 | C005 x C067 | mechanical | 0.28 | 0.05 | Recompute the shared quantity (sndk, soxx, conditioner, attention) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR051 | C017 x C173 | mechanical | 0.28 | 0.05 | Recompute the shared quantity (zone, setups, card, best) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR020 | C185 x C187 | mechanical | 0.27 | 0.03 | Recompute the shared quantity (anchor, official, trull, david) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR063 | C029 x C074 | mechanical | 0.27 | 0.05 | Recompute the shared quantity (mclean-pontiff, post-publication, edge) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR067 | C052 x C059 | mechanical | 0.27 | 0.07 | Recompute the shared quantity (disciplines, candidate, bytes, round) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR068 | C031 x C178 | mechanical | 0.27 | 0.05 | Recompute the shared quantity (calibration, bias, sharpe) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR103 | C171 x C191 | mechanical | 0.27 | 0.04 | Recompute the shared quantity (saves, restore) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR125 | C025 x C027 | mechanical | 0.27 | 0.05 | Recompute the shared quantity (fe01-fe30, engines, forecast) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR062 | C057 x C074 | mechanical | 0.26 | 0.05 | Recompute the shared quantity (reversal, breakeven, plus, edge) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR111 | C120 x C129 | mechanical | 0.26 | 0.05 | Recompute the shared quantity (ruling, owner, classified, classes) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR142 | C008 x C100 | seeded | 0.26 | 0.05 | Price this unit's event-window claims against C100's 28,898-report base rates (priced about +/-9.18% vs closed about +/-6.32%, 25.2% beyond implied): claims inside the base-rate envelope are not edge. |
| PAIR004 | C184 x C185 | mechanical | 0.25 | 0.06 | Recompute the shared quantity (consecutive, exhaustive, macd, completion) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR031 | C154 x C173 | mechanical | 0.25 | 0.01 | Recompute the shared quantity (explicit, direct, ancestor, deep) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR074 | C141 x C142 | mechanical | 0.24 | 0.02 | Recompute the shared quantity (echo-board, cures, quality, cured) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR087 | C056 x C109 | mechanical | 0.24 | 0.05 | Recompute the shared quantity (theory, herding, canon) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR141 | C029 x C031 | seeded | 0.24 | 0.05 | Same trial-accounting check as C007 x C010: one counting convention, both DSRs recomputed, then compared. |
| PAIR043 | C098 x C173 | mechanical | 0.23 | 0.04 | Recompute the shared quantity (sentence, base-rate, base, entry) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR078 | C116 x C179 | mechanical | 0.23 | 0.05 | Recompute the shared quantity (recompute, claims, teardown, extracted) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR135 | C032 x C015 | seeded | 0.23 | 0.05 | Recompute the taxonomy agreement rate excluding the synthesis rows C015 flags as double-counted; if agreement stays near 22.4%, the falsifier stands as triggered on the cleaned denominator too. |
| PAIR116 | C075 x C076 | mechanical | 0.22 | 0.05 | Recompute the shared quantity (infinityblade, runs, landed, discipline) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR042 | C048 x C130 | mechanical | 0.21 | 0.07 | Recompute the shared quantity (fires, unfed, tensor, roster) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR076 | C047 x C188 | mechanical | 0.20 | 0.03 | Recompute the shared quantity (health, roll, unfed, parked) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR086 | C024 x C046 | mechanical | 0.20 | 0.01 | Recompute the shared quantity (staleness, free, order) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR092 | C062 x C191 | mechanical | 0.19 | 0.05 | Recompute the shared quantity (drills, claude, zero) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR146 | C128 x C166 | seeded | 0.19 | 0.05 | Reconcile the denominators by date and definition (roster snapshot vs accounting groups) in a single dated key-set diff; the counts differ by construction, and the diff must show exactly where. |
| PAIR055 | C131 x C182 | mechanical | 0.18 | 0.05 | Recompute the shared quantity (levered, side, replication, average) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR056 | C007 x C009 | mechanical | 0.18 | 0.05 | Recompute the shared quantity (territory, earn, flow) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR089 | C022 x C057 | mechanical | 0.18 | 0.06 | Recompute the shared quantity (wyckoff, statistics, base) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR106 | C099 x C122 | mechanical | 0.18 | 0.05 | Recompute the shared quantity (call, saty, above, close) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR096 | C038 x C139 | mechanical | 0.17 | 0.05 | Recompute the shared quantity (daily20, tensor, pipeline, blocked) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR098 | C100 x C107 | mechanical | 0.17 | 0.05 | Recompute the shared quantity (implied, worst, average) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR099 | C061 x C120 | mechanical | 0.17 | 0.05 | Recompute the shared quantity (stopped, ruling, classified) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR147 | C128 x C170 | seeded | 0.17 | 0.05 | Same dated key-set diff as C128 x C166, against the 651 canonical strategies of the algorithm audit. |
| PAIR060 | C103 x C111 | mechanical | 0.16 | 0.02 | Recompute the shared quantity (killed, per-item, items, recorded) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR114 | C086 x C134 | mechanical | 0.16 | 0.04 | Recompute the shared quantity (chart-reading, charts, chart, read) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR118 | C098 x C181 | mechanical | 0.16 | 0.05 | Recompute the shared quantity (judged, setup, class) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR124 | C008 x C009 | mechanical | 0.16 | 0.05 | Recompute the shared quantity (closing, flow, sources) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR131 | C126 x C132 | seeded | 0.16 | 0.04 | Operator identity is printed in both teardowns. The deciding check is whether any StrategyFactory claim survives the claim-audit standard the Skool teardown applied to the same operator's funnel. |
| PAIR049 | C108 x C117 | mechanical | 0.15 | 0.03 | Recompute the shared quantity (retail, ideas, worth, signals) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR059 | C041 x C171 | mechanical | 0.15 | 0.03 | Recompute the shared quantity (directions, append-only, both, enumerated) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR084 | C059 x C079 | mechanical | 0.15 | 0.02 | Recompute the shared quantity (disciplines, synthesis, local, found) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR047 | C103 x C142 | mechanical | 0.14 | 0.05 | Recompute the shared quantity (proofgate, blocker, cures, items) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR066 | C015 x C057 | mechanical | 0.14 | 0.05 | Recompute the shared quantity (accounting, cited, breakeven, counted) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR127 | C050 x C076 | mechanical | 0.14 | 0.05 | Recompute the shared quantity (infinityblade, package, mechanisms) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR025 | C006 x C067 | mechanical | 0.13 | 0.05 | Recompute the shared quantity (sive, exchange, nasdaq, wikipedia) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR034 | C016 x C043 | mechanical | 0.13 | 0.00 | Recompute the shared quantity (power, buying, accounted, must) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR041 | C088 x C104 | mechanical | 0.13 | 0.01 | Recompute the shared quantity (already-have, skip, repos, adoption) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR054 | C007 x C008 | mechanical | 0.13 | 0.05 | Recompute the shared quantity (forced, calendar, flow, index) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR100 | C001 x C050 | mechanical | 0.13 | 0.05 | Recompute the shared quantity (skills, staged) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR112 | C008 x C107 | mechanical | 0.13 | 0.03 | Recompute the shared quantity (capacity, regime, index) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR003 | C180 x C182 | mechanical | 0.12 | 0.01 | Recompute the shared quantity (harness, cagr, zero-cost, known-answer) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR028 | C037 x C054 | mechanical | 0.12 | 0.02 | Recompute the shared quantity (component, traced, confirmed, pinned) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR038 | C028 x C032 | mechanical | REFUSED | 0.12 | Recompute the shared quantity (typed-layer, typed, while, forecast) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR108 | C027 x C134 | mechanical | 0.12 | 0.01 | Recompute the shared quantity (inputs, repos, what) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR119 | C050 x C168 | mechanical | 0.12 | 0.02 | Recompute the shared quantity (cold, bytes, index) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR120 | C024 x C069 | mechanical | 0.12 | 0.00 | Recompute the shared quantity (token, checks, limits) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR040 | C062 x C097 | mechanical | 0.11 | 0.03 | Recompute the shared quantity (dead-drop, marker, claude) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR053 | C057 x C122 | mechanical | 0.11 | 0.05 | Recompute the shared quantity (indicator, statistics, volume, plus) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR044 | C021 x C136 | mechanical | 0.10 | 0.02 | Recompute the shared quantity (supported, review, mixed, samples) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR093 | C083 x C095 | mechanical | 0.10 | 0.00 | Recompute the shared quantity (living, current, writes) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR104 | C021 x C056 | mechanical | 0.10 | 0.05 | Recompute the shared quantity (often, costs, canon) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR148 | C159 x C180 | seeded | 0.10 | 0.03 | Re-run the replication on the post-expansion panel only: headline statistics inside the original bands confirm the panel build did not manufacture the result. |
| PAIR105 | C093 x C122 | mechanical | 0.09 | 0.03 | Recompute the shared quantity (pivot, below, above, volume) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR145 | C136 x C154 | seeded | 0.09 | 0.00 | Both are design inputs to the expression resolver. The deciding check is the resolver's first 100 resolved expressions graded under C136's base rates with C154's denominator rule enforced. |
| PAIR144 | C087 x C028 | seeded | 0.08 | 0.05 | Already corroborated in the record: the estate's own corpus grade (verdict excess +0) is the local instance of r = 0.07. The forward check is the typed seats' Brier record plotted against their reasoning-quality scores. |
| PAIR045 | C032 x C106 | mechanical | 0.07 | 0.05 | Recompute the shared quantity (agreement, seat, typed, read) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR134 | C066 x C067 | seeded | 0.07 | 0.05 | Same check as C066 x C004, on this unit's name set: direction-vs-magnitude split of forward returns after attention spikes. |
| PAIR149 | C159 x C182 | seeded | 0.07 | 0.00 | Same post-expansion-panel re-run as C159 x C180, for this replication. |
| PAIR151 | C179 x C086 | seeded | 0.07 | 0.02 | Apply one standard to both: C179's vendor offered no numbers at all, C086's offered numbers failed measurement. The check is whether either claim class survives a registered forward test on this estate. |
| PAIR094 | C040 x C068 | mechanical | 0.06 | 0.00 | Recompute the shared quantity (researched, documented, entry) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR101 | C040 x C109 | mechanical | 0.06 | 0.00 | Recompute the shared quantity (disposition, reserved) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR115 | C009 x C109 | mechanical | 0.06 | 0.00 | Recompute the shared quantity (herding, cascades, independent) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR012 | C131 x C181 | mechanical | 0.05 | 0.01 | Recompute the shared quantity (improvement, development, variants, pre-registered) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR080 | C069 x C110 | mechanical | 0.05 | 0.00 | Recompute the shared quantity (contents-only, automation, github) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR082 | C018 x C032 | mechanical | 0.05 | 0.00 | Recompute the shared quantity (nearly, registered, falsifier) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR095 | C068 x C098 | mechanical | 0.05 | 0.00 | Recompute the shared quantity (instead, windows, entry) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR097 | C086 x C141 | mechanical | 0.05 | 0.00 | Recompute the shared quantity (charts, including, independent, chart) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR102 | C041 x C067 | mechanical | 0.05 | 0.00 | Recompute the shared quantity (mirrors, mirror) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR113 | C130 x C188 | mechanical | 0.05 | 0.05 | Recompute the shared quantity (discrepancy, unfed, parked) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR117 | C104 x C134 | mechanical | 0.05 | 0.01 | Recompute the shared quantity (repos, section, sweep, what) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR126 | C099 x C179 | mechanical | 0.05 | 0.01 | Recompute the shared quantity (candles, complete, extracted) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR132 | C066 x C004 | seeded | 0.05 | 0.02 | Split forward returns on the conditioner names by attention direction vs attention magnitude: if attention predicts volatility but not sign, C066's reading governs and the conditioner must be re-based as a volatility conditioner. |
| PAIR133 | C066 x C005 | seeded | 0.05 | 0.00 | Same check as C066 x C004, on this unit's name set: direction-vs-magnitude split of forward returns after attention spikes. |
| PAIR136 | C032 x C047 | seeded | 0.05 | 0.02 | Apply the taxonomy's rule-agreement test to the census's sleeve rules: agreement far below the registered 80% bar confirms the estate's rule logic is not self-consistent across its own ledgers. |
| PAIR143 | C100 x C122 | seeded | 0.05 | 0.04 | Compare event-window behavior across the two doctrines on one shared earnings sample; agreement on the overshoot rate corroborates both, disagreement localizes the artifact. |
| PAIR109 | C034 x C159 | mechanical | 0.04 | 0.00 | Recompute the shared quantity (watch, later, verdicts) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR123 | C068 x C105 | mechanical | 0.04 | 0.00 | Recompute the shared quantity (points, point, post, entry) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR122 | C099 x C113 | mechanical | 0.02 | 0.00 | Recompute the shared quantity (fully, complete, code) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR065 | C136 x C152 | mechanical | 0.01 | 0.00 | Recompute the shared quantity (expression, resolver, correction) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR128 | C036 x C067 | mechanical | 0.01 | 0.00 | Recompute the shared quantity (per-name, names, cured, sessions) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR110 | C044 x C112 | mechanical | 0.00 | 0.00 | Recompute the shared quantity (rescue, orders, alpaca) from both primary sources on one denominator and compare sign and magnitude. |
| PAIR121 | C069 x C187 | mechanical | 0.00 | 0.00 | Recompute the shared quantity (secondary, primary, limits) from both primary sources on one denominator and compare sign and magnitude. |

## Spend (Decisions API, this leg only)

| Bank | Requests landed | Questions | Answers | Input tokens | Cost USD |
|---|---|---|---|---|---|
| program-c-research-recheck | 17 | 2134 | 2134 | 423,347 | 0.042634 |
| program-c-connections | 11 | 318 | 318 | 98,947 | 0.010877 |
| Total, Leg C | 28 | 2452 | 2452 | 522,294 | 0.053511 |

Day ledger after this leg (all lanes, from `request_budget.json`): 148 requests, 2,221,026 input tokens, $0.227079. The 5,000/day circuit breaker was never approached.
Refusals: three answers across both banks came back as endpoint refusals and are recorded as refusals under the harness audit rule, never coerced or re-asked: C163_NULL and C172_NULL (seat bank, adversarial-null predicates) and PAIR038_CORROB (connections bank). They print as REFUSED wherever they appear. Seat bank returns: 2,134 of 2,134 questions (2,132 probabilities/vectors + 2 refusals). Connections bank returns: 318 of 318 (317 + 1 refusal). No call failed after the backoff ladders; failed-call count is zero in both banks.
Utilization choices, restated: all three question types used (predicate, choice, score); seven-lens panels at full width on all 194 studies (no sampling); connections as their own bank at full width (153 pairs x 2 predicates + 12 cluster choices); pack size resized from 396 to 132 questions under measured TPM contention, with backoff-and-resume on every 429; full probability vectors recorded in the runs files, of which this deliverable prints argmax, means, and the pair vectors in full.

## Status

STATUS: PARTIAL, bounded by two named remainders. (1) The connections table's deciding checks for the 123 purely mechanical pairs are recomputation checks on the shared quantity, not yet executed recomputations; the 30 seeded pairs carry authored checks, three of them already decided by the record itself. (2) No LIVE CANDIDATE was found in the archive under the tier rules; that is a finding about the archive, printed with its limiting number in the tier census, not a gap in the read. Everything else in the brief is closed: coverage reconciled (202 located vs 200 MANIFEST, difference named), 194 of 194 corpus units itemized with five-field reads, 2,134 of 2,134 seat questions returned (3 refusals across both banks recorded as refusals and named in the spend section), connections seated at full width (318 of 318 returned).

Evidence pointers: register `~/workspace/research_notes/alpha-hunt-chaos-20261115/PROGRAM-C-REGISTER.jsonl` (194 rows, seat summaries merged); seat runs `program-c-work/seat_runs.json` (17 calls, pack hashes, usage, full vectors); connections runs `program-c-work/connections_runs.json` with `program-c-work/connections_candidates.json` (pair provenance); extraction digest `program-c-work/digest.txt` (2,633 lines) over `program-c-work/digests.json`; authored reads `program-c-work/batch1.json` to `batch8.json` with the C068 evidence override applied at merge (`program-c-work/merge_register.py`).
