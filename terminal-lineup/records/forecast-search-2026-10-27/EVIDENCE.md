# Evidence registry (graded)

This is the desk's graded evidence base. The Forecast Factory uses it as the source of its forecaster registry: each
row's ID is stable, and a forecaster cites the IDs it rests on (`evidence: [T1, S1, A2]`).

- **Read the grades before making a claim.** Nothing here becomes a desk rule without the gates in
  [OWNER_RULINGS.md](../OWNER_RULINGS.md) (RES-04, RES-13, BSF-08).
- **Stable IDs.** Rows are never renumbered or deleted. A regrade edits the Grade cell and says why; a new finding
  gets the next free ID in its family. Families: T timing, S selection, A avoid, V size/volatility, E exit,
  X execution, D data and method facts, AD findings added from the helper reports of 2026-10-27.
- **Update it in the same commit** as the study that changes a grade.

**Provenance.** Built 2026-10-27 from the session's engine/EVIDENCE.md and its addendum (the S_aa, S_ab and S_ac
helper reports), merged into one table and deduplicated. Nothing was re-run. Every number is copied from the cited
line. Status: PARTIAL.
- The source evidence base read the master research inventory and R7 gaps in full, the xcheck findings and creative
  results in full, and scanned R4 (other repos) for verdict lines.
- `xcheck/new10` had no RESULTS.md when this was built; its rows (S4–S8) were graded from the raw run log only. **Update 2026-10-27 night:** the file now exists (AD-70).
- `xcheck/reset2` had no results when this was built. **Update 2026-10-27 night:** results exist (AD-72); the sec.gov 403 was a rate limit, and the insider run is still to be repeated.
- Source keys point into the session's research files, which are not in this repository: `MRI Lnnn` the master
  research inventory; `R7` gaps; `R4` other repos; `XF` xcheck findings; `XC` xcheck creative; `N10` the new10 log.

**Terms.** R: one unit of initial risk. IC: daily cross-sectional Spearman correlation. Disc/Hold: discovery and
holdout periods. DEEP: the CNN study on 6,330–6,385 names, delisted included, 2016–26. Roster: the 1,832-name
survivors-only universe. small3: the small, micro and nano tiers pooled.

**Grades.** **A** held out of sample or forward and replicated in a second study or dataset. **B** held once out of
sample. **C** in-sample only, noisy, or a single period. **V** volatility only (size of the move, not direction).
**X** refuted. **P** forward test pending. Borderline claims get the lower grade.

---

## 1. Graded claims

### TIMING (when to enter; market state)

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| T1 | Fear days (SPY ≤ −1%), risk-off days and VIX spikes lift **every** long entry. The lift is market timing, not chart shape | Pullbacks +0.13R vs +0.035R (n 85k). Risk-off +0.12R. Random entries get the same lift. VIX-spike pullback +0.24R vs random +0.16R. Any uptrend name on a fear day +0.29 to +0.36R, about equal to random. Random deep-reset day on a fear day +0.18R (n 10,163) vs +0.07R on any day | Three replays on different universes (85k, 296k and 19k cases). No formal disc/hold split of the lift itself. The pullback base is about 0 since 2022 | **B** (P: the Lab fear-day arm, about mid-Nov) | Forced selling and liquidity demand get paid a premium; the market rebounds after high-volatility down days | XF L3; MRI L307, L309, L312, L1947–1951 |
| T2 | In drawdowns, yesterday's losers beat yesterday's winners (short-horizon reversal in stress) | Last-day return IC −0.058 / −0.028 in the deepest SPY-drawdown tercile. The only 3 of 8,816 pairs that survive. Short-term reversal is stronger in stress (393 confirmed vs a null of 17). 1-week peer-gap reversal IC +0.017 (t 4.4) | Discovery 2017–21, confirmed 2022–26 (roster). Replicated in the CB round and in 3C | **A** | Liquidity provision: the price pressure from forced sellers reverts | MRI L1076, L205, L202, L1829–1833 |
| T3 | Implied volatility priced well above realized (a high VRP) precedes better index months | "HOLDS". VRP top decile DIA +489 bp per 60 days (t 5.2) | Pre-registered rule, both eras | **B** | Investors pay a fear premium; when the premium is high, the risk is already priced | MRI L199, L1829 |
| T4 | Long setups need a healthy tape: leader setups pay only with SPY above a rising 200-day | Pooled leader setups +0.1–0.2%/20d in up markets vs −1.2/−1.3% otherwise, a gap of 1.3–1.5 pts in both eras. Gated-out sessions −0.121R. Leader setups lose when SPY is >10% below its high (diff +1.81%, p 0.005) | Both eras (roster) | **B** | Momentum continuation needs risk appetite | MRI L1124–1130, L1273+, L206 |
| T5 | Breakouts in weak markets lose | −0.194R (t −1.9, borderline) | One test | **C** (as an avoid) | False breakouts fail without broad buying | MRI L179, L1257 |
| T6 | Credit and stress indices (STLFSI, HY/IG OAS) are positive for the next month of SPY | STLFSI ρ +0.188 (t 2.9). HY OAS +0.494, 2023+ only | Short sample. FRED is limited to plain statistics by the owner's ruling | **C** | High spreads mean a high risk premium | MRI L1353–1359 |
| T7 | Market extremes (breadth washout, VIX > 30, SPY −20%) are followed by strong SPY | +5.2% (8 episodes), +5.2% (13), +7.6% (5) | Too few episodes | **C** | Capitulation | MRI L1086–1093 |
| T8 | A QQQ bear flip hedged with 30% TZA improves a long book | OOS +5.7 pp CAGR, Sharpe +0.16. FAZ 5d: train t 2.7 over 29 episodes, **3 OOS episodes** | OOS has 3 episodes | **C** | Times the short state rather than picking shorts | R4 L6215–6217, L14453 |
| T9 | Legend's Buy Day overnight leg on SPY | Replicated on an SPY proxy and in 1993–2007, which the author never tested (t 3.6) | Out of sample in time and instrument | **B** (index only) | Overnight risk premium | R4 L6000 |
| T10 | Calendar effects (turn of month, holidays, Fed days) and Fibonacci levels | "RULED OUT". The turn-of-month SPY +0.49%/5d is descriptive only | — | **X** (turn of month: C) | — | MRI L199, L1096 |
| T11 | Breadth or internals predict index direction | "No internal calls SPY or IWM". Breadth led SPY at no horizon | — | **X** for direction; **V** for volatility (see S4) | — | MRI L1787, L251, L631 |
| T12 | Red-day / no-chase entry | Red-day policy t 1.65 → 0.16 after 2022. "Red open does NOT beat": tier A −0.88 OOS | Decays in later data | **X** | — | R7 L412; R4 L10123 |

### SELECTION (which names, once timing is removed)

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| S1 | **F3**: in uptrend (UP) names on fear days, a pullback deeper than the stock's own norm ranks higher | IC +0.026 (t 4.3) disc, +0.031 (t 4.3) hold at 20d. 60d 2023+ IC +0.062 (t 9.8). 2023+ quintile spread +0.81 pts/20d | Same sign in 2016–22 and 2023+ | **B** | An oversold amount relative to the name's own volatility reverts | XF L11; MRI L1952 |
| S2 | RESET names (≥35% off the high, near the low): laggards win on a 10-day RS vs SPY (F7); fear-day RS (F5) | F7 IC −0.041 in both periods (t −5.5 / −4.9). F5 −0.033 / −0.021. Spread about +1.1 to +3.0 pts/20d | Both periods | **B** (consistent with T2) | Reversal | XF L12 |
| S3 | RESET: high recent down volume (capitulation) is better | F6 IC +0.040 / +0.020, spreads +0.95 / +1.28 pts. new10 N6, volume-confirmed capitulation: IC +0.016 (t 4.2) disc / +0.015 (t 3.9) hold on all days; ≈0 on fear days | Both periods, two definitions | **B** | Seller exhaustion | XF L13; N10 L1011–1014 |
| S4 | new10 N1 "innocent bystander" in UP on fear days | IC +0.026 (t 4.8) disc / +0.028 (t 4.6) hold. All days: hold +0.001 | Fear days only; both periods | **B** (raw log only; no RESULTS.md) | Indiscriminate selling hits names that did nothing wrong | N10 L967–970 |
| S5 | new10 N7 "gap-down absorbed" in UP | Fear days +0.018 (t 4.2) / +0.017 (t 3.1). All days +0.008 / +0.006 | Both periods | **B** (raw log) | Absorbed supply | N10 L1019–1022 |
| S6 | new10 N9 composite, RESET (signs fixed on discovery) | Fear days IC +0.053 (t 7.3) / +0.028 (t 3.9). Trade diff RESET: disc t 2.0, hold t 6.1 | Holdout confirmed | **B** | Combines S2/S3 | N10 L1076–1079, L1094–1095 |
| S7 | new10 N9 composite, UP | Fear days +0.041 (t 6.4) / +0.010 (t 1.5). Trade diff: disc t 5.8, hold t 1.6 | Fades in the holdout | **C** | — | N10 L1092–1093 |
| S8 | new10 N8 trend age (UP) | Fear days −0.014 (t −2.2) disc vs +0.039 (t 6.4) hold: **the sign flips** | Sign flips | **C** (unstable) | — | N10 L1027–1030 |
| S9 | Fear personality: prefer UP names that historically beat SPY after −1% days | Disc IC 0.008 (t 0.8), hold 0.050 (t 5.8) | Holdout only | **C** (P: score forward) | Possibly a regime change | XC L15, L24–29 |
| S10 | Cross-sectional momentum, liquid: 126d return, top 10%, held 63d | Excess +15.4% (2023–24 holdout, Sharpe 1.06) and +20.8% (fresh, Sharpe 0.77). DEEP C3 smooth momentum +1.45 / +1.88 (q 0.005). Liquid momentum +2.0% / +2.8% (3D) | Holdout and fresh, several repos | **B** (downgraded for conflicts C3) | Underreaction; risk premium | R4 L8811, L8773; MRI L1725, L203 |
| S11 | Residual and vol-scaled momentum | Resid mom: holdout +2.76% (q 0.016), fresh +0.81. Vol-scaled mom: holdout +1.01% (q 0.047), fresh +0.63. Desk corr 0.75 | Holdout and fresh, one repo | **B** | As S10 | R4 L14561–14562 |
| S12 | Index membership: S&P 500 members beat, S&P 600 members lag | +0.37 / +0.39% (t 2.8 / 3.3). −0.74 / −0.78% (t −3.7 / −4.9) | Both eras; roster (survivors) | **B** | Size and flow effects | MRI L1243 |
| S13 | NVI above its 1-year average (EMA255) | +0.8 (t 6.2) in every tier | DEEP-2 confirmed (both eras) | **B** | Smart-money accumulation on quiet days | MRI L258, L1800 |
| S14 | R1: last week's bottom 20% with low FINRA short volume, when breadth is in its bottom third | Small caps +2.9% / +2.7% over 60d (t 3.5 / 2.6). Liquid +2.4% / +1.3% (t 2.4 / 3.2). 9 of 9 years | Both eras, two tiers | **B** (data-blocked; see D7) | Reversal without informed short sellers | MRI L201, L1832 |
| S15 | gap_share conditional on fear | Top VIX third IC +0.069 (t 4.8) / +0.074 (t 3.4) | Both eras | **B** | Gap moves revert more in panic | MRI L204, L1835 |
| S16 | Strong close × IWM above its 50-day, small caps, 10 sessions | +0.015 (t 4.9) / +0.021 (t 4.1) | Both eras | **B** (small caps only) | Continuation in a supportive tape | MRI L205 |
| S17 | A pullback plan, when filled, beats other plan forms | +0.231R (t 4.3) / +0.134R (t 2.5). Only about ⅓ fill. Live: real-support plans +0.54R (n 88) | Both eras (roster) | **B** (live: P) | Buying at a level improves R:R | MRI L1257, L306 |
| S18 | Textbook uptrend pullback to the 20/50-day as a signal | +0.05R vs random same names +0.08R. A first tag of the 20d lags by 0.23 pts (t −2.18, n 55,574) | Two repos | **X** | — | XF L2; R4 L8454 |
| S19 | Stacking reversal confirmations in deep resets | 3+ signs −0.02R, 4+ signs −0.15R, vs random +0.07R | — | **X** | Late, rare entries | MRI L312, L1951 |
| S20 | Named setups standalone (VCP, HTF, EP, flags, breakouts, Minervini, Bulkowski, pocket pivot, NR7) | "No edge". Naive breakout OOS excess +0.03 [−0.90, 1.01], n 47,037. Breakouts −1.12 / −0.81% | Many studies | **X** (VCP with SPY up: C) | — | MRI L217, L251, L1124, L1361–1376; R4 L6893 |
| S21 | Mined rules, analogs, rubber band, close location, beta overshoot | Factory: 0 of 9,861 pass BH. Analog IC +0.0046. Every close-location \|IC\| < 0.02 | — | **X** | — | XC L16–19; XF L15; MRI L1094 |
| S22 | LLM chart eyes, Elliott/Fibonacci, chart-pattern frequency, Echo's calls | Eye partial IC +0.003 [−0.046, +0.052]. Wave setups 1.07× the shuffle. Fibonacci mass 0.99–1.04×. Echo's calls median −4.8% vs SPY | — | **X** | — | MRI L231, L779, L1095, L1104 |
| S23 | Raw Tensor markers; the board/read's ranking | 1D cyan −0.3% (t −2.4). Board +0.012R vs random −0.021R, no ranking separates. 0 of 46 insights hold | — | **X** | — | R4 L9090; MRI L1158–1166 |
| S24 | 1W Cyan tier A (cheap-stock lane) | OOS +51.2 mean, but median +1.4: tail-driven. Q05 not distinguishable from random sub-$5 names | — | **C** | Cheap-stock location | R4 L14346; R7 L222 |
| S25 | OBV-vs-A/D split, micro/nano | IC +0.072 (t 5.0) micro, +0.099 (t 7.6) nano. Spreads unchecked | "OPEN candidate" | **C** (the registered OBV-high/A-D-low variant went the wrong way: X, see AD-12) | — | MRI L198, L1681 |
| S26 | Trend efficiency, residual-momentum z, small-cap ensemble, fixed equal weights | er_63 +0.0115 (t 2.4). Ensemble IC +0.035 (survivors). Equal weights IC +0.0091 (t 2.52) | Not both eras, or survivors only | **C** | — | MRI L1332–1351, L203 |
| S27 | Orderly staircase beats jagged (DEEP) | +0.5–0.8%/20d before costs. The red-team found "spotting losers" was volatility. Staircase + fear did not beat uptrend + fear | — | **V / C** | — | MRI L217, L223; XF L4 |

### AVOID (vetoes; the most robust layer)

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| A1 | Crashed, volatile, illiquid small caps keep losing. A CNN/fitted veto of the worst tenth helps a long book | Money test: micro +0.53% / nano +0.66% per 20d (t 5.1 / 7.6), 4 of 4 years. Avoid edges keep 92–96% factor-neutral | Holdout 2023–26 opened once; robustness lenses | **A** in micro/nano (large caps 0) (P: FB2, MB1) | Distress, dilution, lottery demand | MRI L226, L1764, L252, L1791 |
| A2 | Loud attention days fade: a +25% day without earnings, fresh pumps | −10.6% over 20d (t −5.6), 10 of 10 years. C1 small3 −9.45 pts (t −11.2). Fresh pump −12 (t −10.6) | Both eras, several studies | **A** | Retail overreaction | MRI L206, L265, L1688 |
| A3 | Stretched far above the 50-day / extended | C5b −5.3 / −7.1. −7 to −13 (model book). Large caps weak | Both eras | **A** (small caps) | Mean reversion of froth | MRI L1722, L1688, L216 |
| A4 | Short-term strength fades in small/micro caps (close above yesterday's high, crosses above the 20d/AVWAP, overbought) | −0.74 (T02). can_ind 61 of 66 events are avoids | DEEP-2 confirmed | **B** | Short-term reversal | MRI L258, L265, L1800 |
| A5 | Jackpot trap: predictors of +50% runners don't pay | 0 of 560 cells with positive mean pay. s_win5 IC −0.108. No exit makes runners pay | Several studies | **A** (as "never buy runner scores") | Lottery premium | MRI L1757–1759, L1729, L1776 |
| A6 | Warning combos stack (one-shot holdout) | 197 of 200 small/micro warnings held. Strongest −8.4 pts plus 13 more big losers per 100. Buys: only 6 beat singles, all lose after costs | One-shot holdout, combos locked Oct 20 | **B** | — | MRI L257, L1802 |
| A7 | Chart-pattern warnings: dead-cat bounce, selling climax, V-bottom, bullish divergence at the year's low | Dead-cat −5.6 (t −11.7). Climax −6.2. Divergence −1.14 / −0.73 (t −2.6 / −2.1) | Both eras | **B** | Supply overhead | MRI L256, L1799, L1247 |
| A8 | Repeat reverse-splitters | About −16 pts vs vol-matched (strong). First-time about −4 (n.s.) | Corrected after a leak check | **B** (first-time: C) | Distress | MRI L255, L1784 |
| A9 | Buying far above the day's low; trade-count surges in small caps | lod small3 −2.1 (t −13.2). Trade-count surge is a "strong AVOID" | DEEP-2 confirmed | **B** | Chasing | MRI L1771, L1752 |
| A10 | Broken stock + bullish signal (triples) | −3.9 / −2.6% per month. Far below the high + breakout retest + 30% month: −7.2 / −5.3 | Confirmed vs a shuffle null (148 vs 2) | **B** | Bull traps in downtrends | MRI L1148–1152, L1229 |
| A11 | Heavily shorted or broken names lag in healthy, broad markets | Short-volume IC −0.053 / −0.071 (t −6 to −8). FINRA short volume alone holds 2022–26 only | Context-dependent | **B** (alone: C) (D7 data limit) | Informed shorts | MRI L1153, L1136 |
| A12 | Small-cap earnings and episodic-pivot gaps fade | EP −5.1 / −8.5 (t −9.5). Next week −0.41 / −1.05% (t −2.0 / −2.9) | Both eras | **B** | Gap overreaction | MRI L1724, L1365 |
| A13 | 1–2 sessions before earnings trail; golden cross outside SPY's uptrend | −0.43% (t −2.8, "at the edge"). −1.75% | Borderline | **C** | — | MRI L206 |
| A14 | Avoid edges are 1.6–1.75× stronger with the McClellan oscillator negative | Multiplier | Descriptive | **C** | — | MRI L251, L1787 |
| A15 | Company-specific (idiosyncratic) declines do worse | F4 IC −0.012, and −0.022 at 60d 2023+ | Both periods | **B** | Information-driven declines persist (vs liquidity-driven ones) | XF L14 |
| A16 | Shorting picked names profits after borrow | Bottom tenth −3.7% (t −2.30) but "no book clears". 50 bp borrow leaves t 0.45 | — | **X** (use avoid as a veto, never a short book) | — | R7 L425; R4 L8748 |

### SIZE-VOL

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| V1 | Volatility is forecastable, mostly from its own past (HAR) | Long-scale vol R² gain +0.127 / +0.116 (t 19 / 20). About 59% of volatility claims survive an own-vol control | Both eras, every tier | **A** (V) | Volatility clustering | MRI L203, L264, L1761, L1834 |
| V2 | Implied vol is the best realized-vol forecast but runs high | Realized/implied 0.87 liquid, 0.69 nano. Direction 0 of 12 | — | **B** (V) | Variance premium | MRI L1816 |
| V3 | VIX backwardation → bigger SPY moves | t 4.6 / 3.6. 13 of 99 cells, all volatility | Holdout t 3.6 | **B** (V) | — | MRI L280, L1815 |
| V4 | Shapes and weak internals forecast volatility, not direction | Shapes: 172 of 384 volatility cells vs 2 of 384 direction cells | Confirmed | **B** (V) | — | MRI L1781, L251 |
| V5 | Inverse-vol weighting of small-cap momentum | Trails equal weight by −0.73% / −0.97% | Both eras | **B** (against inverse-vol sizing in small caps) | Volatility is part of the small-cap payoff | MRI L203 |
| V6 | Snap-back size on fear days scales with volatility | Jagged names on fear days 2023+ +0.09R | One period | **C** | Higher beta | XF L4 |
| V7 | Per-name HMM, Kelly, regime × factor | "Ruled out" | — | **X** | — | MRI L203 |

### EXIT

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| E1 | Trailing stops, profit caps, early first-leg exits, hard % stops and scale-outs hurt | Trailing stops: 159 of 159 BH-significant results harmful. 1:6 profit cap t −6.63 (n 76,896). 5-day exit −1.17 pp (t −23.5) | Across 4+ desks. The kill-quality caveat: 85% of kills were unproven | **B** (P: Lab exit arms) | Cutting the right tail. Wald: with no drift, exits only trade holding time for R | MRI L546–552, L595; R4 L16 |
| E2 | No alternative exit beats a plain time exit in both eras | 3-ATR trail +0.172 / −0.013. Time20 +0.126 / +0.005 | Both eras | **B** | — | MRI L1259–1265 |
| E3 | Best horizon from the next open is about 60 sessions; fast edges are mostly the next-morning gap | T09. "Most edges peak at 1–5 sessions (includes the overnight move)" | Ledger theme | **B** | — | MRI L265, L252; XF L6 |
| E4 | Washout exit on a close above the 5d MA | +0.30%/trade net (n 6.5k, 63% wins) on fear days 2023+. Calm days about 0 | One period | **C** | — | XF L5 |
| E5 | Wider targets (3R+) do better | "Targets of 3R+ do better" (no number). Conflicts with AD-28 (R:R structure creates no edge) | — | **C** (contested) | Right tail | MRI L307 |

### EXECUTION

| # | Claim | Best numbers | Disc vs holdout | Grade | Mechanism | Sources |
|---|---|---|---|---|---|---|
| X1 | Latency costs: decide and fill on fresh data | 1H one bar late costs $502/trade (t 7.6). Delay worth $701/trade (t 9.97). Delay −450 to −1,183 bps in two sleeves | Two corpora | **B** | Edges decay in 1–5 sessions | MRI L559, L507; R7 L449 |
| X2 | Next-open entry is fine | ΔSharpe −0.04..0 | Adopted | **B** | — | MRI L543 |
| X3 | Fill realism: the sim touch matches the NBBO within ±4.5 bp. Crossing the real NBBO costs 2.3× the sim's charge. 30-minute adverse drift −11 bp | Measured | Measured, not a backtest | **B** (fact) | — | MRI L112, L270 |
| X4 | Pullback limits fill only about ⅓ of the time | ⅓ fill | Both eras | **B** | Selection bias of fills | MRI L1158, L179 |
| X5 | Gap/limit filters and breakout/stop entries | Rejected | Corpus | **X** | — | MRI L551 |
| X6 | EQ-01 official open print (+16.6 bps expected), LoD gate, sizing arms | Pre-registered | Forward | **P** | — | MRI L489–497 |

### DATA (method facts that limit claims)

| # | Fact | Numbers | Source |
|---|---|---|---|
| D1 | A shared "synth" null gave 21–67% false positives in cross-stock tests | — | MRI L202 |
| D2 | A full-sample same-name mean leans toward reversal by about (h/n) × move. Fix: a leave-out centred mean | — | MRI L206 |
| D3 | Roster studies (G0, the read replays) are survivors only. 86.7% of small rows are names that later turn liquid (roster look-ahead). Micro survivors' 155.8% vs IWC is survivorship | — | MRI L1062, L205; R4 L14 (EDGE_LAB) |
| D4 | Split-adjusted volume rounding leaked reverse splits (227 names). The audit says results are not driven by it | — | MRI L230, L1801 |
| D5 | Earnings dates were one session late for 4.2% of winter events (fixed). There are 123 vendor price-adjustment errors and about 0.2% duplicate tickers | — | MRI L181, L260, L350 |
| D6 | The DEEP panel has no VIX and no sector ETFs (realized vol and SPY stand in). Hourly data: one source says Dec 2025, the tensor build says 2026-03-17 at the earliest (terminal 1h: 41 names from April); treat 2026-03-17 as the safe start (AD-09). No pre-2016 data | — | XC L6; MRI L348–354 |
| D7 | FINRA terms forbid automated downloads and models (affects S14 and A11). The owner allows FINRA (10-26, restated 10-27) and has been told its terms restrict models. The compliant Query API keeps only 12 months of short volume and short interest from June 2021, so a compliant rerun cannot reach the 2018–26 study period (AD-11) | — | MRI L283, L84 |
| D8 | LLM eye results are contaminated by training memory (IC +0.230 before the cutoff vs +0.091 after) | — | MRI L215 |
| D9 | Crediting stops at the stop price fakes +0.02–0.08R | — | MRI L533 |
| D10 | Skill-less best of 550 sleeves shows SR ≈ 3.1 at 1 year. MinTRL for SR 1.0 is 2.7 years | — | R7 L23–24 |

### ADDED (findings from the helper reports, 2026-10-27; duplicates of rows above were merged, not repeated)

| # | Finding | Numbers | Grade | Relation to the rows above | Source |
|---|---|---|---|---|---|
| AD-01 | Breakout quality (closes held beyond the line, stretched-spike break) does not change the next 5–10 sessions, in both eras | 32,702 breaks | **X** | Supports S20 | S_aa N1 |
| AD-02 | Candles at key levels separate no more than a shuffled-session null (best 0.60 ATR, 2+ kinds); the prior-move window is unsettled (best 0.7 ATR, 90% range 0.3–1.8) | — | **X** (window: C) | With S20/S21 | S_aa N2, N3 |
| AD-03 | Indicator context (10-day, ChartsLector, monthly/weekly map, 6-1 momentum, RS, MFI/CMF, VWAP20) is redundant with the 50/200 stack and none holds alone | 145 of 147 redundant | **X** standalone; context only | With S21, S26 | S_aa N4 |
| AD-04 | Chart patterns fire on random walks at about the rate on real charts | 0–5.3% (self-test 0.1–5.6%) | **X** | Supports S20 | S_aa N5 |
| AD-05 | The Corwin-Schultz spread runs 11.5× quoted spreads | Spearman 0.70, n 23 | **C** (rank only; never a cost input) | Bears on X3 | S_aa N6 |
| AD-06 | Echo's % targets are measured from the planned entry, not the last price, so upside is overstated (about 860 images); the CELH target breaks his own method | — | **X** as a signal | Mechanism for S22 | S_aa N7 |
| AD-07 | Execution Lab v1 has no verdict yet ("collecting"); its null false-positive rate is 13/100 at α 0.10 | 13/100 | **P** | X6, E1 | S_aa N8 |
| AD-08 | MB traits: pick-side visual traits fail on unseen charts; every liquid trait shows nothing | 140 of 231 nothing; liquid composite +0.003 | **X** | With S22 | S_ab |
| AD-09 | Hourly history starts 2026-03-17 at the earliest; terminal 1h covers 41 names from April | — | Data fact | Corrects D6 | S_aa N9 |
| AD-10 | Bar-cache defects: the 2016-06-20 bar missing for nearly all names; Yahoo missing 2017-06-19 for most names; bad prints in WOLF (~100×), CTVA, RTX, DGXX; fake first-bar dates on 21 names; `_VIX.json` held 203 sessions twice | — | Data fact | Adds to D5 | S_aa N10; S_ab |
| AD-11 | FINRA: cdn files forbid a database and predictive models; a compliant free Query API credential exists; short interest for listed stocks only from June 2021; the API keeps 12 months of short volume | — | Data fact | S14 and A11 stay B but a compliant replication cannot reach the study period; D7 | S_aa N11 |
| AD-12 | OBV-high / A-D-low split, registered test, reversed | −0.02 to −0.07 | **X** (this variant) | Regrades S25's variant | S_ab |
| AD-13 | MB traits avoid side: MFI ≥ 75 and close ≥ 1.15× the 10-day predict losers in small tiers (fresh pump and close ≥ 1.6× 50d are already A2/A3) | −0.123 nano; −0.130 small (−8.0%); −0.092 micro; −0.062 nano; −0.056 small | **C** (out of sample in charts, not in time) | Adds to A2/A3 | S_ab |
| AD-14 | Spike memory and panic flush as buys reversed at full strength; they work as avoids | −0.147, −0.150 | **X** as buys | Consistent with A1/A2 | S_ab |
| AD-15 | MCDX profit crowd positive in nano | +0.05..+0.07 | **C** | — | S_ab |
| AD-16 | Washout in small tiers is an avoid (nano −0.046); capitulation ≈ 0 under this definition | — | **C** | S3 unchanged (other definition) | S_ab |
| AD-17 | 33 of 37 candidates fail only the rotation test (e.g. two-year wreck −0.21): the effect is in which names, not timing | — | Method fact | — | S_ab |
| AD-18 | V4 plain-chart eye: avoid skill | IC +0.12 (p 0.07); nano +0.36; bottom-10% AUC 0.61 (p 0.03) | **C** (P: FB1) | 160 charts, IC SE ≈ 0.08 | S_ab |
| AD-19 | Overlays make the eye worse, and readers echo the drawn code read | +0.03 / +0.08 vs +0.12; echo ρ +0.71; buys ~0R | **B** (method fact) | With S22 | S_ab |
| AD-20 | Twins pairwise pick is at chance on post-cutoff charts | 39/83 (47%); high confidence 10/30 | **X** | With S22 | S_ab |
| AD-21 | Eye sample size: about 620 charts per arm are needed to detect IC 0.10; published LLM chart IC is 0.04–0.09 | — | Method fact | Explains AD-18 | S_ab |
| AD-22 | Subgroup search, small3 avoid triples (down-day trade surge + top ATR% + red cloud; MAX5 + ADR + spread) | −5.3 (t −12.9); −3.1 (t −12.7); −5.9 (t −11.9) | **C** (P: holdout) | Near A9 | S_ab |
| AD-23 | Subgroup search, small3 buy triples (closes near lows, RSI(2) bottom tenth), thin names ≤ 300k sh/day | +1.6 (t 8.6); +1.8 (t 8.4) | **C** (P; costs unchecked) | Consistent with T2/S2 | S_ab |
| AD-24 | ChartsLector Calibrated-RSI ~99% countertrend; Strong Long Continuation fired 15 times | — | **C** (descriptive) | — | S_ab |
| AD-25 | Breakout hold rates: 47% hold 5 closes, 53% back inside within 4, 20% bust | — | Descriptive | S20 unchanged | S_ab |
| AD-26 | Desk read: 9 of 16 pattern keys never vote; an `_averages` crash bug on 14 reads; a "vs 20-day VWAP" sign bug on the OL fact strip | — | Method fact | Affects S23 and the OL arm | S_ab |
| AD-27 | Listing age modifies everything: under 1 year old, avoid edges are 2–3× stronger and buy edges vanish or flip | — | **C** (P if registered) | Matters for A1–A4 | S_ac 1 |
| AD-28 | R:R structure creates no edge: mean R +0.05 to +0.15 at every R:R; ranking by P × R:R works against realized R | — | **X** for P×R:R ranking | Contests E5 | S_ac 10 |
| AD-29 | Net genome count ladder in small3: ≤ −3 gives −2.3/−3.1 pts; ≥ +2 gives +1.1/+1.1 | Monotone in both eras | **C** (holdout seen) | — | S_ac 2 |
| AD-30 | Downside-only precursors (C1 gaps 1.6–1.9×, down-day trade-count surge, Gann states, weekly divergence at the low) forecast tail size | — | **C** (V-like) | For stops and puts, not direction | S_ac 3 |
| AD-31 | The genome's avoid stack adds almost nothing over 8 core measures | holdout vm_ic 0.0585 vs 0.055; bottom tenth −1.1 to −1.6%/20d; no long-short spread after costs | **C** | Supports A16 (veto, not a short book) | S_ac 4 |
| AD-32 | Weak 6-month momentum is 97% distance from the 250-day high | — | **C** (redundancy) | — | S_ac 5 |
| AD-33 | Deep reset B2/B3 (close over base, or reclaim + volume + RS) | about +0.06R over random-in-uptrend; B1 SE 0.15 | **C** | Owner's deep-reset family (BSF-07) | S_ac 7 |
| AD-34 | Read facts in B0 (levels.floor, mom.macd, levels.on) pass BH | +8 to +12 pts hit rate; R up to +0.26 | **C** (one replay, discovery) | — | S_ac 8 |
| AD-35 | Hit-rate features (RSI, distance from the 21d, 20d RS) add 10–15 pts of hit rate but no mean R | — | **X** as an R edge | Warns against hit-rate-only odds | S_ac 9 |
| AD-36 | Walk-forward picker model fails: calibration off 16–26 pts out of sample | — | **X** | Any odds tool needs per-regime recalibration | S_ac 11 |
| AD-37 | Sweep and reclaim of a swing low | +0.041 vs +0.030; edge ≈ 0 (n 110k) | **X** | Vendor "reclaim trigger" idea | S_ac 12 |
| AD-38 | Codex indicator composite: 34 of 35 models with negative predictive power | — | **X** | — | S_ac 13 |
| AD-39 | Intraday momentum replication fails | t −1.16 | **X** | — | S_ac 14 |
| AD-40 | Leadr-style conviction (LDR-1), pre-registered PIT test | one arm t 0.61, two rejected | **X** | — | S_ac 15 |
| AD-41 | Families with no direction edge: cot, ovn, peer, ftd, h1, SEC-V+ | — | **X** (direction) | cot is low-power | S_ac 16 |
| AD-42 | Read-score families: 36 cells fall to 15 after near-baseline cells are removed | — | **C** | — | S_ac 17 |
| AD-43 | CNN seed-1 holdout IC 0.11–0.18 in small/nano | — | **B** (one seed) | Source number for A1 | S_ac 18 |
| AD-44 | Option costs: half-spreads $88k on 52 fills (176 bps); LEAPS spreads up to 13% turned −$44k into −$123k | — | **B** (measured) | Options side of X3 | S_ac 19 |
| AD-45 | Crowding: about 55 sleeves long QQQ (31% of gross); 20 groups / 46 sleeves with identical fills | — | **B** (measured) | Limits independent evidence (D10); input to SLV-14 | S_ac 20 |
| AD-46 | r19_crypto −$31,542 on 136 fills; costs exceed pre-cost P&L in 26 sleeves | — | **B** (measured) | Cost dominance | S_ac 21 |
| AD-47 | Muse-derived M-ROOM and M-COIL lose in their forward record | no numbers | **C** | — | S_ac 22 |
| AD-48 | Alpaca news filter and sort act on `updated_at`, not `created_at` | — | Data fact (PIT trap) | Any news family | S_ac 23 |
| AD-49 | Incremental adjustment=all merges can mix price bases; raw bars are never cached | — | Data fact | Live features vs research | S_ac 24 |
| AD-50 | The tracker ledger falls out of the record past 95 MiB (about 10-26/27); tensor_state books are not recorded | — | Data fact | P items depend on the record | S_ac 25 |
| AD-51 | Best Setups live record: 29 calls, 7 closed, 5 won, +0.90R average | n < 30 | **P** | — | S_ac 26 |
| AD-52 | The live board showed Buy (4 High) on a Risk-off day; conviction inflation 135 High vs 5 slots | — | Ops fact | Contradicts T1/T4 gating | S_ac 27 |
| AD-53 | Vendor edge claims: Milkman gate +2.19% vs random +1.97%; QuantiX backtest > live 133/133 | — | **C** (third party, unverified) | QuantiX supports D10 | S_ac 28 |
| AD-54 | Blind / blind2 / blind3 / eyes chart rounds (about 478 charts each) are unscored here; FB1 eye pairs and MB1 machine book frozen 10-20 | — | **P** | With S22, A1 | S_aa N16; S_ab |

### ADDED 2 (xcheck and search studies, written 2026-10-27 night; files in [2026-10-27-studies/](2026-10-27-studies/INDEX.md))

Columns: claim, data, test design (discovery / holdout / embargo / multiplicity), numbers, grade, caveats, status. D is
discovery, H is holdout, EM is the expected move S·σ·√T.

| # | Claim | Data | Test design | Numbers | Grade | Caveats | Status | Source |
|---|---|---|---|---|---|---|---|---|
| AD-55 | VIX/15.87 (VIX/√252 per day, √252 scaling) is an **~81% band**, not a 1σ/68% band. √252 vs √365 differ only at h=1 | SPY and QQQ daily, 2010 to 2026-10; VIX, VXN, VIX9D, HV30, HAR, GARCH | D 2010–19, H 2020+. Coverage of S·(1±EM). Descriptive calibration; no BH; no embargo | SPY ±1 EM coverage with VIX, D/H: 81.6/80.9 at h=1, 83.2/81.7 at h=5, 85.0/82.2 at h=21. Lognormal says 68.3. QQQ VXN 78.0% at h=1. VIX9D no better. Over-cover 13 to 17 points at every horizon | **B** | Windows overlap (about 4,200 SPY starts per cell), heavy autocorrelation for h>=5. No skew (VIX stands in for every strike). Two index ETFs only | PARTIAL | bands/RESULTS §1, §4a |
| AD-56 | A realized companion band, **HAR × √(h/252) × 0.88**, holds 68%. Stop and target distances should be HAR × 0.9, not VIX | Same | k fitted on 2010–19, coverage read on 2020+ | k 0.87/0.88/0.91 gives 68.7/68.0/69.8% at h=1/5/21 (holdout). VIX needs k 0.71–0.75 (65.7–67.8%). HV30 k 0.94–0.97, GARCH 0.90. VIX stop distances about 25–30% too wide | **B** | k fitted on D, read once on H; SPY only for the k; overlapping windows. A vendor-style 1σ label on VIX/15.87 is the miscalibration, not the constant | PARTIAL | bands/RESULTS §1, §4c |
| AD-57 | `strip.p_touch` (reflection, 2N(·)) **overstates** touch probability by 13 to 30 points and saturates near 100% for bands narrower than about ±0.7 EM | Same, daily high/low | Touch = daily high/low reaches the band within h sessions | At ±1 EM the reflection model says 63.5%; realized 32–33% (VIX), about 50% (HV30, HAR, GARCH), 45–50% for HAR-scaled; at ±0.5 EM realized 77–93% | **B** | Daily extremes only; no 5-minute SPY cache existed. For h=1 the daily range is the exact session path | PARTIAL | bands/RESULTS §1, §4c |
| AD-58 | Option Alpha's HV30 driftless N(d2) POP is the best-calibrated POP; IV-based POP understates win rate by 12 to 15 points. A win rate is not an edge | SPY, short strangle and iron condor at ±1 EM strikes, credit priced on VIX | D/H pooled in the table; POP predicted vs realized | HV30 POP 82.4 → 83.0 (h=1), 85.9 (h=21); IV (VIX) 75.7 → 87.6 to 90.3; HAR 80.0 → 84.1 to 87.5. IC at h=21: 79.4 → 82.0 (HV30) | **B** (calibration only) | Counts wins, ignores loss size; no skew; no per-strike chain | PARTIAL | bands/RESULTS §2 |
| AD-59 | The variance premium vanishes on fear days: 1-day VRP **−9.4%** when VIX > VIX3M; hard-block short premium then. Calm-VIX tercile is richest (VRP 37–40% at h=1–5) | SPY, ATM straddle priced on VIX vs empirical expiry value | D 24.3% / H 19.9% overall at h=1; regime splits pooled, not split D/H | Fear day VRP −9.4% (h=1), 5.4% (h=5), 17.6% (h=21); coverage on fear days 55.5–66.7%. Below a falling 200d VRP 9.6%. Above a rising 200d 28.9% | **C** (regime splits pooled) | VRP is before costs and skew; one asset for the regime splits | PARTIAL | bands/RESULTS §3, §4b |
| AD-60 | Avoid replication (M0): jump25, deadcat, newlist, pump_nano, 1.6× the 50-day and mfi_nano keep sign and holdout t>=2. **The small-cap 20-day-loser flag flips sign** (+0.69%, t 1.9 in D). stretch, idio and surge fail the holdout | DEEP: 6,344 names, 11.23M name-days, no price or volume floor, delisted marked to last close | D 2016–22, H 2023+. Excess vs same-day same-tier mean; Newey-West by date (lag = horizon−1). PASS = same sign, H t>=2, net positive. No BH across the 10 signals | 6 of 10 PASS. pump_nano H −9.05%/20d (t −9.8), −16.6%/60d (t −16.8) | **B** (X for the loser flag) | Thresholds frozen from D (stretch 0.196, idio 1.55). No earnings-date filter on jump25. Surge uses volume (no trade counts in bars) | PARTIAL | avoid/RESULTS Method, M0 |
| AD-61 | The avoid flags work as an **entry veto** (M3) and by warning count (M4), not as anything you trade | Same | Disc basket chosen on D only (6 signals with D t<=−2). M3: pass−fail net 60d return of random entries | M3 pooled +6.9% (t 7.1) D / +10.7% (t 8.5) H; micro +3.6/+6.7; fear-day micro +4.4/+7.8; small, mid, large n.s. M4: count>=4 gives −3.36% (t −3.3) / −7.45% (t −8.2) per 20d. M6: calm-bull effect (H calm −0.98%, t −2.8); **reverses in risk-off (H +2.64%, t 2.2)** | **B** | The pooled M3 mixes tiers (fails sit in nano). Nano cannot be traded at $50k a name. The veto must be off with SPY under its 200d (the picker does this) | PARTIAL | avoid/RESULTS Verdict M3, M4, M6 |
| AD-62 | Trading the avoid flags **fails after costs**: clean-universe book (M1), avoid as exit (M2), hedged short (M5). Shorts refuted | Same | One-way cost = Corwin-Schultz half-spread + σ20·√($50k/ADV20). Borrow 50/20/5/1/0.5% nano..large | M1 net CAGR 17.2→9.4% (disc, monthly). M2 selling hurts −1.0 to −1.7% per hold. M5 gross +2.1/+2.4%/yr, net −27%/−36%/yr; 4.3% of 20d shorts rise >=50%, max single loss +3,708% | **X** (as a trade) | M2 t-stats are per hold, not date-clustered. CS spread runs about 11.5× quoted (AD-05), so costs are conservative | PARTIAL | avoid/RESULTS M1, M2, M5 |
| AD-63 | **C4 momentum dip** (fear day, 126d momentum top 30%, 5d return bottom 30%, no veto) beats liquidity-matched random picks at the trade level but **fails as a portfolio** | DEEP, vetoes frozen from D, 60-session hold from the next open, cost 2×max(CS, σ√(N/ADV)) | D 2016–22 / H 2023+; thresholds frozen from D; excess vs same-day pool; date-clustered t. Ladder: top 5 per fear day, 20 slots, $1M, 10 random seeds. PASS needs matched t>=2 and Sharpe > SPY 1.41 | Pooled excess D +1.5% (t 4.7) / H +2.85% (t 4.5). Vs liquidity-matched random H +5.9% per trade, **t 2.35** (n 555, 111 days); D +6.3% (t 5.5). Portfolio NW t 1.23 (H). Sharpe: ladder 0.85, SPY-idle 1.14, random 0.94, SPY 1.41. A combined score gives H matched t 2.77, Sharpe 0.94 / 1.19 | **B** (selection); portfolio **FAIL** | Only 111 fear days in H. Ladder sits about 70% in cash; the SPY-idle gain is beta (random 1.26). Non-fear C4 loses. Params in fearday_params.json are provisional until fitted. **P: FT-02** | PARTIAL | composite/RESULTS, RESULTS2 |
| AD-64 | C1 forced-selling top decile and C2 "clean of all vetoes" pass pooled but are **liquidity tilts**. Every single veto is negative in both periods | Same | Same | C1 H +4.9% (t 11.3) pooled, about 0 inside each tier (tiers 3–5 −0.3% to +0.1%). C2 clean H +1.7% (t 6.8); failing any veto −4.8% (t −5.9). Tier 1 clean net −6.7% after costs | **C** (C1, C2 as selectors); vetoes consistent with A | The idio veto never fired (F4 q90 is 1.0, strict >): UNVERIFIED in C1, C2 | PARTIAL | composite/RESULTS |
| AD-65 | Composite resets lose; most composite cells fail. C3 UP F3-top pullback on bull-fear days is positive in the holdout only. C5 absorb/capitulation, C7, C8 switch, D2 thin triples fail | Same | Same | C3 UP bull/fear H +2.55% (t 7.1) but D t 1.4; C3 RESET −7.4% (H). C5 H −5.6%. C8 switch H −0.01%. D2 thin triple H −6.0% (t −50) | **C** (C3 holdout only); **X** (rest) | C3 and C6 may be a 2023+ regime effect | PARTIAL | composite/RESULTS, RESULTS2 |
| AD-66 | A **SPY core with fear-day rotation into the picks** does not beat SPY. Only bear-fear rotation is positive in both periods | Same, f=2%, k=20, Fmax=100% frozen from D; 20 random seeds | D grid best active t 1.52 (none reaches 2). H opened once. Newey-West lag 60 | H active **+0.8%/yr, IR 0.25, t 0.77**; beta-matched IR 0.09, t 0.34. Picks beat random 20/20 seeds (+2.1%/yr, t 1.62) but random rotation loses to SPY (−1.4%/yr). Bear-fear tranches: D +4.6% (n 198), H +3.8% (n 43) vs random −4.1%; bull-fear H −0.7% | **C** (bear-fear cell only); rotation as specified **FAIL** | Most D edge is 2020. 43 holdout bear-fear entries. Tranche t's treat overlap as independent (ignored). **P: FT-01** | PARTIAL | composite/RESULTS3 |
| AD-67 | Idiosyncratic share (F4) top decile is a veto; a continuous penalty adds nothing | Same, fear days, rank deciles | Tier-matched excess by decile, D and H | Top decile D −3.5% (t −2.6), H −2.1% (t −2.5). λ_idio 0.5 never beat 0 on D | **B** | Decile 8 is the F4=1 tie mass. Complements A15 | PARTIAL | composite/RESULTS2 Test 4 |
| AD-68 | Prediction map: 26 failed or refuted buy signals are reliable **DOWN** predictors (11 with at least a B record); DOWN is a **veto, not a short book** | DEEP, 6,385 names, no floors, 9.70M name-days; 8 signals re-tested | D 2016–22 / H 2023+. Thresholds fixed a priori. Newey-West by date. Hedged short = −excess − cost − borrow | 7 of 8 re-tested signals negative in both periods at 20d (panic flush −0.7%, t −2.5 / −6.1%, t −11.2; spike memory −0.5% / −2.9%). P(drawdown>=20% in 20d) 1.2–2.3× peers. 16–27% of events trade +50% above the short entry. Hedged short at 5% borrow −2% to −33% per 20d, no cell positive with t>=2 in both periods | **B** (veto); short book **X** (consistent with A16) | Long puts untested (need IV). Borrow flat, not locate-aware. The A1 proxy is the one exception (positive n.s. in D) | PARTIAL | predmap/RESULTS (a); PREDICTION_MAP |
| AD-69 | NO-MOVE (short premium) edges seen under a lagging IV proxy vanish under a fair proxy; BIG-MOVE forecasts are right but **long straddles lose** | Same, BS straddle and ±1σ/±2σ condor, IV1 = 1.15×rv60, IV2 = 1.15×HAR | D / H, option cost assumed 10% of premium | Compression short straddle +18%/+22% of premium under IV1, −5% under IV2: a proxy artifact. Every BIG-MOVE long straddle negative under IV2 (−1% to −24%) | **X** (compression edge); BIG-MOVE belongs in sizing (V grade) | The loud-spike candidate (+17.7% / +20.4% under IV2) was then **KILLED on real quotes (AD-75)** | PARTIAL | predmap/RESULTS (b), (c) |
| AD-70 | new10: N1, N7 (UP), N9 RESET and N5 RESET (negative sign) pass; N2, N3, N4, N5 UP, N6, N8, N9 UP fail. **Gap 4 check:** the file has the **quintile spreads and the N10 trade table, but no BH across N1–N10** and no 2019–22 re-split | Liquid names (price>5, $vol20>5M), fear days, 20d and 60d | IC t over days; pass = same sign and \|t\|>=2 in D and H on 20d fear days. Q5−Q1 spread (point estimates, no SE) | Pass rows are S4, S5, S6 (unchanged). N5 RESET IC −0.0168 / −0.0246 (laggards win). N10 UP top quintile minus random per day: D +0.092R (t 5.8), H +0.029R (t 1.6); RESET D +0.043R (t 2.0), H +0.140R (t 6.1). An informal BH at q 0.10 over the 14 rows, from the reported t's (normal approximation, not in the file, not from raw data), keeps the same four rows | **B** (N1, N7, N9 RESET); **C** (N9 UP, N8) | N10 t's overstate independence. N1 increment over F3 untested. N9 not rebuilt from holdout-passing members. N3 holdout IC is the 2023+ rally | PARTIAL | new10/RESULTS |
| AD-71 | The owner's **deep-reset recipe fails** (52-week low at structural support plus MACD, RSI, divergence, higher-low and volume confirmations) | DEEP, 40,836 simulated trades: 21,782 setups, 19,054 random deep-reset days | Next-open entry, stop-first, 40-session time stop, cost 0.2%. 2016–22 vs 2023+ shown; no pre-registered holdout, no BH | Random deep-reset day +0.067R; setup at support **−0.027R**; 3+ confirmations −0.016R (n 1,831); 4+ **−0.150R** (n 241; 2023+ −0.177R, n 108). Only "support held" is positive alone (+0.037R). Fear and 3+ gives +0.071R but the random fear-day deep reset gives +0.179R | **X** (stack of confirmations; matches S19) | Naive standard errors, overlapping trades. **Re-aggregated from the saved trade file on 2026-10-27 night; the run printed it but wrote no RESULTS.md.** The picker keeps deep resets on a watch lane | PARTIAL | reset/RESULTS; reset.py |
| AD-72 | **reset2**, 45 deep-reset indicators by fear-day IC: pooled passes are mostly thin-tail **avoid** effects; short volume and the chart indicators show nothing | 732,460 reset rows (283,989 joined to indicators); FINRA short volume 2018-08 to 2026-10 | D 2016–22 / H 2023+, fear days, pass = same sign and \|t\|>=2 in both. Quintile splits by dollar volume. No BH across 45 | Pass on 20d and 60d: f_nvi(+), f_w200(+), f_fib(+), F6(+), f_voldie(−), f_tight(−), f_obvdiv(−), w_revsplit(−), w_lottery(−), x_dd(−), x_atrpct(−). Without a liquidity filter −F7 fails pooled (fear IC −0.006 / −0.040). Short volume: x_svr5 t +1.1/+0.5. MACD curl, support, divergence, patterns, stochastic, A/D, MFI: no pass. Deeper drawdown predicts worse returns pooled | **C** | **Insider buying is untested.** The one SEC request (company_tickers.json) got HTTP 403 "Request Rate Threshold Exceeded"; the single-name study later fetched the same file and 53,259 filing dates from sec.gov at about 3 requests/s with a Jack Tailor contact, so the 403 was a **rate limit, not a block**. The insider run has not been repeated. FINRA files for 2016-06 to 2018-07 return 403 (545 sessions), so short-volume discovery covers 2018-08 to 2022. The 35%/10% reset thresholds are provisional | PARTIAL | reset2/RESULTS |
| AD-73 | **No ETF or leveraged-ETF strategy passes** (564 pre-registered). Holding the leverage beats most timing | Yahoo adjusted bars, Cboe VIX/VIX3M/VVIX, ^IRX; 2010-01 to 2026-10; synthetic leveraged series validated (all within 0.9 pp/yr except SOXL, an index mismatch) | Manifest hashed (sha256 e04cdbb7…0816405) before any backtest. D 2010-03–2019, H 2020-01+. Jensen alpha vs a leverage-matched benchmark; circular block bootstrap (block 20, 2,000 reps); **BH q 0.10 across all 564**; deflated Sharpe N=564 | H alpha>0: 383. Same sign in D: 179. p<0.05: 13 (min 0.0085); **0 survive BH**; dsr_active>0.95: 0; best H Sharpe 1.05 vs hurdle about 1.1. Only 16 of 90 3× timing rules beat 3× buy-and-hold in H (0 of 90 in D). Closest: regime-gated overnight `overnight.1.SPY.1x` alpha_H 6.2%, p 0.008, DSR 0.44; the **ungated overnight leg has zero alpha** | **X** (as stand-alone index ETF timing at this trial count) | Does not refute T1, T3, T4, T9 as entry lifts for single-name books. `overnight.3` has a small MOC-proxy lookahead. The gate (T4), not the overnight premium (T9), carries the near-miss. **P: FT-03** | NULL (search GREEN) | etf/RESULTS |
| AD-74 | **Options on SPY/QQQ express none of the desk's edges better than stock**: 27 trials, 0 pass | Cboe PUT/BXM/PPUT/CNDR; real SPY chain 2020–22 (CC0) as ground truth; model: Black-Scholes on VIX9D/VIX/VIX3M plus a fitted smile | Validation gate fixed first (monthly corr>0.95, tracking error<3%, drift<1.5%): passed. D 2010–19 / H 2020+. BH q 0.10 on D one-sided p across 27; deflated Sharpe N=27 | 0 of 27 pass BH; best DSR 0.02. Fear-day calls lose 1–3%/yr (ATM) to stock. Put-write after spikes −3 to −5%/yr vs always-on. VRP>2 filter worst month −22.3%. Protective put does not cover Mar-20. 3× LEAPS trail UPRO. QQQ delta-hedged loud-spike straddle +1.1%/yr (t 2.1, p 0.02) in D, +0.5% (t 0.6) in H, fails BH | **X** (as alpha) | Model-priced, not chain P&L. Real half-spread about 0.5–0.7% vs 2% assumed (conclusions unchanged at 0.75%). 28/30-day expiries assumed before about 2016 | PARTIAL | options/RESULTS |
| AD-75 | The **single-name loud-spike short straddle is KILLED** on real quotes. Long straddles after spikes are not confirmed | DoltHub option_chain (391 names, 403 dates after the gate), Kaggle TSLA/NVDA/QQQ chains (CC0), SEC 8-K 2.02 dates for earnings labels | BH q 0.10 over 24 cells; holdout opened once in the same run; control = random session for the same name, >=25 sessions from any spike; fills at bid/ask; spread gate <=10% | Short after a 4σ spike, % of premium, D: earnings −58.0 (unhedged), non-earnings −30.8, vs control +13.3. H: −37.1 / −20.5 vs −17.0. **0 of 6 D cells pass BH.** Long: 7 D cells pass BH, **none confirmed in H** (p 0.26–0.70). Predmap's proxy +17.7%/+20.4% was an artifact. TSLA/NVDA n = 3 + 6 | **X** (short); long **UNVERIFIED** | n is 35–75 per cell. 2019 missing from DoltHub. Hedge deltas use a constant entry IV. About 12% of exits model-marked. Survivorship: delisted names have no prices | PARTIAL | options/single/RESULTS |
| AD-76 | **Forecast Factory P2 search on DEEP:** vetoes carry the run; fear-day buy survivors are re-found but fail costs; momentum and reversal do not survive | DEEP 6,385 names, 11.57M bars, panel 11.47M rows; DIX/GEX is a revised-history fixture (non-PIT) | Split 2023-01-01; embargo >=45 calendar days (88 for 60-session labels); walk-forward (sign agree>=70% of folds); **BH q 0.10 over 11,150 tested cells**; cell minimum 30 dates and 300 observations; holdout opened once (key 5e165e4c…); costs CS half-spread × 2.3 + 2 bp + impact | 15,135 cells, 11,150 tested, **2,986 pass BH**, **1,217 promoted-B** (45 forecaster×target pairs; 1,050 are avoid or veto flags), 590 cost-failed, 455 walk-forward-failed, 682 holdout-failed, 308 sign flips. F3 in fear\|VIX-high: D IC +0.039, H +0.061, but top-quintile long **−0.027 per opportunity net** (cost-failed). Low GEX → higher SPY realized vol promoted at 5 and 20 sessions but null on the part persistence does not give | **B** (A needs a second dataset) | 2023+ rerun not done. Holdout power for 60-session targets is low (5–8 blocks); a stricter df-aware rule, applied after opening and for information only, keeps 1,184 of 1,217. Volatility forecasters mostly rank persistence, with no incremental-over-HAR target. No sector map (no cells). **Not yet on master-desk** | PARTIAL | branch `forecast-p2` 227d2e59, `docs/research/forecast-search-2026-10-27.md` (read with git show) |

Updates to older rows (nothing renumbered): S4, S5 and S6 were graded from a raw log. `xcheck/new10/RESULTS.md` now
exists and agrees with them (AD-70). Gap 1 now has a registered test (FT-05), gap 4 is partly closed (AD-70), and gap
5 is partly closed (AD-72: the build and the IC run are done; the insider run is still open). See
[forward_tests/](forward_tests/README.md).

Merged without a new row: the VIX-spike pullback split (S_ac 6, into T1), fear personality (S_ac 29, = S9), reset2
(S_ac 30, no results), SEC 777/777 failures (S_aa N15, into the header), FRED limits (S_aa N12, = T6), options data
limits (S_aa N13: no free IV, OI or quote history; IV rank blocked until about 2027-10; V2 forward use is data-blocked),
and the S&P 500 index-change table (S_aa N14: 311 events, PIT proof passed; current membership columns are not PIT, so
S12 reruns must use event dates).

Promised but not found in the helper reports: the CNN ensemble and MB2 numbers, the L exit policies, the K lenses, the
shp/spl verifiers, the cot/vmr scores, the Addendum 2-19 validation, the OPT1 registered-test result, the new10 table
and the ldr1 numbers.

---

---

## 2. Conflicts

1. **Pullbacks: edge or not?**
   - The read replays (S17) show filled pullbacks at +0.231R / +0.134R.
   - Replay A (S18) shows a textbook pullback at +0.05R vs random +0.08R, and a fresh 20d tag lags (t −2.18).
   - **Replay A is more credible.** It uses a delisted-inclusive universe, a same-name random baseline and next-open entry. S17 is survivors only, conditions on the fill (⅓ fill, a selection effect) and has no random baseline.
   - Resolution: pullback depth matters only *relative to the stock's own norm and on fear days* (S1). The "pullback" label alone is not a signal.
2. **Fear-day buying (T1) vs the healthy-market gate (T4).**
   - These are different clocks. T1 is a 1-day panic inside a mostly healthy tape. T4 is the long regime (SPY over a rising 200d).
   - Since 2022 the pullback base is about 0 and the fear lift carries everything.
   - Both are B. The engine should require T4 for leader/momentum names and use T1 for entry timing. Their interaction has never been tested (gap G2).
3. **Momentum (S10, B) vs "momentum flips by era" (roster G0.2) and "momentum tilt doesn't pay after costs" (analysis engine).**
   - The R4 book result (holdout plus fresh, liquid, 63d hold) is more credible for a *portfolio*: it has a longer hold and lower turnover.
   - The DEEP/roster IC tests use 20d horizons and survivors.
   - Momentum stays B as a ranking tilt in liquid names. It is a tie-break only in small caps.
4. **Reversal (T2/S2) vs momentum (S10).** These are horizons, not a contradiction: reversal at 1–10 days, momentum at 3–12 months. Watch the D2 bias. Novel/new10 use a same-day cross-sectional mean within the state group (not a same-name mean), so S2 is **not** exposed to the reversal-lean flaw.
5. **Eye/CNN "spotting losers" vs the red-team result.**
   - The red-team showed about 70% of calls are explained by price features. "Spotting losers" was volatility.
   - The money-test veto (A1) survives as a *veto*, because it was measured against equal-volatility names.
   - Direction claims from the CNN shapes are V, not selection.
6. **Veto value: money test vs analysis-engine validation.**
   - The money test gives +0.53/+0.66% per 20d.
   - The fitted veto "saves little" (+0.10% small, +0.24% nano), and the count rule blocks 83–91% of small caps.
   - The fitted-veto validation is more conservative because its holdout numbers had been seen. Expect the low end. FB2 decides.
7. **Shared-baseline studies.** The 3C cross-stock results were re-run because the synth null gave 21–67% false positives (D1). Any claim that rests only on a pre-fix 3C run is downgraded. K1 and the 1-week reversal survived the re-run.
8. **Same-stock random baseline** (odds engine, replay A). It is right for "does the setup beat random timing in this name". It leans toward reversal-type conclusions when the name mean is computed over the full sample (D2). The fear-day lift was also seen against *other names on the same day* (novel/creative state-group means), so T1 holds under both baselines.
9. **FINRA short volume.** It is negative alone (A11, 2022–26 only). Low short volume is positive inside the R1 cell (S14). These are consistent. R1 is the better-specified cell (9 of 9 years), but it is data-blocked (D7).
10. **Calendar.** Patterns ruled calendar effects out. The roster found turn of month +0.49%/5d and the NDX OpEx Friday −25 bp was a candidate. The pre-registered ruling governs: X.
11. **Fear personality (S9)** and **N8 trend age (S8)**. Both are holdout-only or sign-flipping. Treat them as regime-change risk, not edge.

---

## 3. Per layer: what the engine may use

| Layer | May use (A/B) | Weak tiebreak only (C) | Banned (X) |
|---|---|---|---|
| TIMING | T2 stress reversal (A). T1 fear / risk-off / VIX-spike entry days (B). T3 high VRP (B). T4 SPY over a rising 200d gate for leader/momentum entries (B). T9 overnight leg, index only (B) | T5 breakouts in weak markets (avoid). T6 credit/stress. T7 extremes. T8 QQQ-flip hedge. Turn of month | T10 calendar and Fibonacci. T11 internals for direction. T12 red-day / red-open entries |
| SELECTION | S1 F3 relative pullback depth (UP, fear). S2 RESET laggards. S3 capitulation volume. S4 N1 and S5 N7 (UP, fear). S6 N9 RESET composite. S10/S11 liquid momentum (incl. residual and vol-scaled). S12 index membership. S13 NVI. S15 gap_share in fear. S16 strong close × IWM > 50d (small). S17 level/pullback plans (fill-conditional). S14 only if licensing is cleared | S7 N9 UP. S8 trend age. S9 fear personality. S24 cheap-stock Cyan. S25 OBV/A-D. S26 trend efficiency and ensembles | S18 textbook pullback as a signal. S19 stacking confirmations. S20 named setups. S21 mined rules, analogs, rubber band, close location, beta overshoot. S22 LLM eyes, Elliott, Fibonacci, Echo. S23 raw Tensor markers and the old board rank |
| AVOID | A1 small3 veto. A2 attention spikes. A3 stretched. A5 runner/jackpot scores. A4 short-term strength in small caps. A6 stacked warnings. A7 dead-cat, climax, divergence-at-low. A8 repeat reverse splits. A9 LoD chase and trade-count surge. A10 broken + bullish. A11 shorted/broken in healthy markets. A12 small-cap gap fades. A15 idiosyncratic declines | A13 pre-earnings and golden cross outside the uptrend. A14 McClellan multiplier | A16 short books built from avoid lists |
| SIZE-VOL | V1 HAR own-vol forecast (A). V2 implied vol, discounted. V3 VIX backwardation. V4 shapes → vol. V5: no inverse-vol in small-cap momentum. All of these size and set stops; **none sets direction** | V6 vol-scaled snap-back | V7 Kelly, per-name HMM, regime × factor |
| EXIT | E1: no trailing stops, profit caps or early first-leg exits. E2: a plain time exit. E3: about 60-session horizon from the next open | E4 5d-MA washout exit. E5 3R+ targets | Profit caps, trails, 5-day no-progress exits (unless the Lab arms reverse this) |
| EXECUTION | X1 fresh decisions. X2 next-open entry. X3 NBBO-based cost model (assume 2.3× the sim when crossing). X4 expect ⅓ fills on pullback limits | — | X5 gap/limit filters and breakout-stop entries |
| DATA | Delisted-inclusive universes; PIT bars; same-day cross-sectional baselines; leave-out means | Survivors-only roster results (downgrade one grade) | Synth-null cross-stock tests (D1); pre-cutoff LLM charts |

---

## 4. The 10 most important gaps

1. **A forward test of the fear-day lift (T1) itself.** The Lab fear-day arm ships about mid-Nov, but it needs about 20 sessions. Register a pre-specified Fear-Day Buy List now, with a random-name control on the same days. Every timing claim rests on T1 being B rather than A.
2. **T1 × T4 interaction.** Do fear-day entries pay when SPY is *below* a falling 200d (2022)? Split by regime with delisted names included. This decides whether the engine gates or only times.
3. **Net-of-cost portfolio test of the B selection stack** (F3 + N1 + N7 for UP; F7 + F6 + N9 for RESET) on fear days. Use NBBO-realistic costs (X3), a ⅓ fill model and a 60-session hold. All current numbers are ICs or per-trade R, not book Sharpe.
4. **Write up new10 properly** (a RESULTS.md, quintile spreads, BH across N1–N10, the N10 units). Re-split discovery as 2019–22 for S8/S9. N1, N7 and N9 RESET are graded from a raw log only.
5. **Finish reset2.** The build completed (114,473 rows), but insider.py failed on the SEC ticker fetch and the FINRA feed has misses. No deep-reset indicator, insider or short-volume result exists yet.
6. **Licensing and replication of R1 (S14) and the short-volume avoid (A11).** Clear the FINRA terms conflict (D7). If cleared, rerun on the delisted-inclusive panel. R1 is the strongest replicated buy cell (9 of 9 years) and it is unusable today.
7. **Veto value at desk scale.** FB2 and MB1 score after Nov 17. Pre-commit how the engine uses the veto if FB2 shows only the +0.10/+0.24% "fitted" size rather than the money-test size.
8. **Momentum in the fear-day frame.** Does S10 momentum add to or fight S1/S2 reversal within the same day? There is no joint test. It decides the ranking blend.
9. **Lab exit arms (E1).** 85% of the corpus kills were "unproven". Score the 8/15% stops, 5/10% caps and day-5 exit arms forward before the engine hard-codes "no stops". Also test vol-scaled (V1) stops vs no stop.
10. **A delisted-inclusive rerun of the survivor-roster B claims** (T2 drawdown reversal, S12 index membership, S17 pullback fills, T4 market gate). These rest on the 1,832-name survivor roster (D3). Moving them to the 6,385-name DEEP panel would upgrade them to A or downgrade them.
