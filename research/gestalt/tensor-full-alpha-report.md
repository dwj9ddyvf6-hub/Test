# Tensor Full Alpha Report — Complete Edge Inventory

**Prepared:** 2026-09-30 · **For:** the owner + Grokbot cross-track review · **From:** the Midna/Olympus research track
**Purpose:** Every edge found, stated plainly with exact definitions and numbers. Alpha only.

---

## Program context

- **Corpus:** 61,664 Family-C hourly Swing events (2026-05-13 → 2026-09-23): **15,024 winners** (+5% MFE by hour-bar 20, 51bp cost treatment), 45,562 near-winners.
- **Engine:** Tensor v625, byte-exact, read-only. Family C = the hourly swing lane.
- **Program:** PROJECT OLYMPUS — 9 completed workstreams. **54 hypotheses pre-registered** through the WS-9 validation harness (`olympus/validation/state/prereg_log.jsonl`, timestamps 2026-10-01T01:31–01:42Z); validation runs on post-2026-10-01 data. 10-candidate battery encoded in `validation/candidates.py`.
- **Universe baseline winner rate:** 24.80%.

---

## 1. Signal edges

### 1.1 P5-ROOM — room to upper band (the load-bearing gate)
- **Predicate:** `{"factor": "room to upper band"}` — engine-native factor; room := confirmation-bar close < bbUpper × 0.985 (`lib/tensor-swing-signals.mjs:59`).
- **39.0% winner rate, lift 1.57, z+31.1, n=8,898.**
- Gate ablation (WS-1): the only engine gate with steep winner decay *and* selectivity — requiring it keeps 23.11% of winners (3,472/15,024) at 39.02% kept-set touch.

### 1.2 P5-EARN — earnings proximity
- **Predicate:** `{"earnings_within_td": 5}` — event within ±5 trading days of confirmed earnings (public calendar).
- **±5TD: 39.7%, lift 1.60, z+29.4, n=7,275.**
- **Post-earnings (0..+5TD): 48.1%, lift 1.94, z+34.7, n=4,134.**
- Pre-earnings (−5..−1TD): 28.7%, lift 1.16, z+5.0, n=3,141.

### 1.3 P5-TRIPLE-A — room ∧ earnings ∧ no-squeeze
- **Predicate:** `{"all": [{"factor": "room to upper band"}, {"earnings_within_td": 5}, {"factor_not": "squeeze_on"}]}`.
- **54.8%, lift 2.21, z+27.2, n=1,541** — best-powered conjunction in the program. WS-2: **+2.44% cost-netted capture/signal**.

### 1.4 P5-TRIPLE-B — score≥8 ∧ earnings ∧ room
- **Predicate:** `{"all": [{"score_min": 8}, {"earnings_within_td": 5}, {"factor": "room to upper band"}]}`.
- **55.9%, lift 2.25, z+14.2, n=392.** WS-2: +2.41%/signal.

### 1.5 High-confidence ∧ earnings ∧ room
- **61.2%, lift 2.47, z+11.4, n=183** (n noted).

### 1.6 P4-TALLY-B — score≥7 + room TRADE gate
- **Predicate:** `{"all": [{"score_min": 7}, {"factor": "room to upper band"}]}` — TRADE iff score ≥ 7 AND room (score 8+ without room → WATCH; score 6 → SKIP).
- **40.19% touch, lift 1.62, 21.31% winner retention (3,201 winners).**
- Phase-4: 7,965 signals (13.1%), winner rate 0.402, expected capture/signal 0.259% vs 0.074% current (**~3.5×**), ~3× signal flow.
- The misallocation it fixes: score-7-with-room (wr 0.403, n=5,891) sits in WATCH today while score-8-without-room (wr 0.232, n=573) gets TRADED.

### 1.7 P4-EXT-VETO — extension veto on the TRADE path
- **Predicate:** on the score≥8 TRADE path, veto when `"room to upper band" ∉ sig["factors"]` (confirmation bar extended into the envelope).
- **Vetoed wr 0.232 vs kept wr 0.399**; 21.6% fire rate; **133 winners lost vs 440 near-winners saved (3.3:1)**. WS-1: kept 39.9% vs vetoed 23.2% touch.
- Note: TALLY-B and EXT-VETO are the same gate expressed two ways — they are not stacked; the harness validates the combined form.

### 1.8 P5-ATR-GATE — volatility at the confirmation bar
- **Predicate:** require `atr_pct` ≥ trailing cohort median at signal time (confirmation-bar audit ATR, ex-ante).
- 15,024 winners paired against nearest near-winner twins: **paired Cohen's d = +0.37, 65.7% of pairs directional, BH q ≈ 0.** Winner median ATR 1.55% vs twin 1.42% (means 1.77% vs 1.63%).
- Replicates in every archetype: A (high-conviction triple) d=+0.41 (2.15% vs 1.88%); B (earnings) d=+0.40 (1.68% vs 1.46%); C1 (gap-driven) d=+0.35 (1.69% vs 1.56%); C2 (earned) d=+0.37 (1.53% vs 1.40%).

### 1.9 P5a-ROOMRAMP — the coil (strongest new candidate)
- **Predicate:** room-to-band at bar −1 ∧ bullish-vote ramp ≥2 over trailing 20 bars.
- **17.18% vs 8.11%, lift 2.118, n=2,581.**
- Three independent methods converged on this structure (see §4).

### 1.10 P5a-SQMRAMP — momentum-loaded ramp
- **Predicate:** squeezeMomentum₋₁ ≥ 0.7 ∧ vote ramp ≥2.
- 42.65% vs 34.55%, lift 1.234, n=6,408.

### 1.11 P5a-NOSTOCH — trend core without stoch
- **Predicate:** aroon ∧ di ∧ obv ∧ squeeze ∧ wave bullish, stoch NOT bullish at anchor.
- 25.03% vs 22.46%, lift 1.114, n=3,760.

### 1.12 WS5-P1 — morning constructive-accumulation filter
- **Predicate:** signal 09:30–13:30 ET ∧ uv_share13 ≥ .70 (sidecar's exact up-volume-share).
- 29.12%, +19.0%, n=6,323.

### 1.13 WS5-P2 — morning directed-extension
- **Predicate:** AM ∧ rvol ≥ 3 ∧ uv_share13 ≥ .52.
- 32.80%, +34.0%, n=686.

### 1.14 Post-earnings × VIX pocket
- **Predicate:** post-earnings window ∧ VIX in [16.76, 17.82].
- **403 winners, median first-touch bar 6, median net +7.79%** — fastest-and-biggest cell in the program.

### 1.15 Aroon as the marginal 5th vote
- Present in **56.1% of winners, 1.20× enriched** — the vote that carries the 5-vote mask's signal.

### 1.16 Morning-only volume
- rvol≥3 converts **31.87% AM vs 23.11% PM**; rvol≥3 works only with up-volume (29.19% vs 25.97% without); uv_share13 monotonic across deciles (20.10% → 29.00%). Winner volume personality = steady accumulation.

### 1.17 Reference baselines
- **P5-SCORE8** (`{"score_min": 8}`): 36.3%, lift 1.46, n=2,647.
- Universe: 24.80%.

## 2. Timing edges

### 2.1 Touch-bar ladder by condition (first +5% touch)
| Condition | Median touch | Give-up-90 | Notes |
|---|---|---|---|
| All signals | 9 | 18 | mode bar 6; 68.7% of touches fall bars 4–15; bar 1 = 1.5% |
| score≥8 | 7 | 16 | ~20% less hold for ~92% capture |
| confidence=high | 8 | 15 | 90.1% by bar 15 |
| Stacked (score≥8 ∧ earn) | 8 | 15 | 92.2% by bar 15, retention 88.6% |
| squeeze_on | 10 (p25 6) | 18 | slowest condition — needs a longer stop |
| pre_earn | 8 | — | touches ~1 bar faster than post |
| post_earn | 9 | — | retention 85.5%, median net +5.46 vs pre's +4.96 |
| gap_driven touch | 9 | — | exit-at-touch: 0/2,096 have a bar-1 touch |
| earned touch | 9 | — | retention 87.7% |

### 2.2 Time stops
- Population: **bar 18** captures ~92% of all touches.
- Score≥8: **bar 16** (~92%, ~20% less hold).
- Stacked (score≥8 ∧ earn): **bar 15** (92.2%).
- Squeeze-on: keep at **bar 18** (90.9%) — do not shorten.

### 2.3 Weekday / month-end
- **Friday 0.312 vs Tuesday 0.188 (1.66×)**; Thursday 0.274 + highest median winner net **+5.25**. Thu/Fri = 52% of winners from ~44% of events.
- **Month-end (last 3 trading days): 0.410 vs 0.232** (+15pp; ex-earnings 0.362 vs 0.214).

### 2.4 Volatility & trend regime
- VIX quantile gradient: **0.154 → 0.328 (2.1×)**; median winner net 3.80 → 4.92.
- SPY 20d trend below-median: **0.290 vs 0.208 above (1.39×)**.
- Post-earnings × VIX [16.76–17.82] pocket: 403 winners, median touch bar 6, median net **+7.79%**.

### 2.5 Earnings timing split
- Post 0.481 vs pre 0.286 (1.68×); pre touches ~1 bar faster (median 8 vs 9); pre retention 0.882 vs post 0.855; post median net +5.46 vs +4.96.
- FOMC ±1 trading-day window: **0.275 conversion, median net +5.57** — best calendar cell.

### 2.6 Gap vs earned exit treatment
- 20.1% of touches are gap-driven, 79.9% earned. **Gap-driven → exit-at-touch** (0/2,096 bar-1 touches; retention 80.1% vs 87.7% earned). Gap-through opens carry a median **+0.53pp premium** over the +5% threshold; gap-driven mean fill 6.31% vs earned 4.60%.

### 2.7 Post-H20 study
- 8.29% of near-winners first touch +5% in bars 21–30 (horizon-extension study candidate).

---

## 3. Winner archetypes

| ID | Definition | Signals | Winners | Rate | Lift | $/signal | Med touch |
|---|---|---|---|---|---|---|---|
| **ARCH-1 Earnings Detonation** | earn_td ∈ [0,+5] | 4,134 | 1,988 (13.2%) | 48.1% | 1.94× | **+1.51%** | 9h |
| **ARCH-2 Pre-Earnings Fuse** | earn_td ∈ [−5,−1) | 3,141 | 900 (6.0%) | 28.7% | 1.16× | +0.39% | 8h |
| **ARCH-3 Coiled-Spring Room Break** | ¬earn ∧ room | 7,203 | 2,545 (16.9%) | 35.3% | 1.43× | −0.27% | **7h (p25 4h)** |
| **ARCH-4 Compressed Reclaim** | ¬earn ∧ ¬room ∧ squeeze | 13,956 | 2,617 (17.4%) | 18.8% | 0.76× | −0.43% | 11h |
| **ARCH-5 Transition Conviction** | ¬earn ∧ ¬room ∧ ¬squeeze ∧ score≥8 | 357 | 81 (0.5%) | 22.7% | 0.91× | +0.30% | 9h |
| **ARCH-6 Steady-State Reclaim** | everything else | 31,795 | 6,893 (45.9%) | 21.7% | 0.87× | −0.23% | 10h |

- **Earnings Detonation is the edge archetype:** 85.5% of its winners finish net>0, p95 terminal +21.7%. Exit treatment: **hold through H20**.
- **Coiled-Spring Room Break is the fast one:** winner-conditional mean net +5.72%, but 26.5% of winners MAE below −4% — violent then gone. Exit treatment: **exit-at-touch, never a runner**.
- **Super-conjunctions inside ARCH-1** (all positive): room∧earn∧¬squeeze — 1,541 signals, **54.8%, +2.44%/signal**; score≥8∧earn∧room — 392, **55.9%, +2.41%**; high-confidence∧earn — 243, **54.7%, +2.00%**; earnings alone (¬room∧¬squeeze) — 2,269, 45.8%, +1.07%.
- Basket names over-index in ARCH-3 (6.5% vs 1.6–3.7% for others).

---

## 4. The coil — three-method convergence

Three independent methods found the same structure:

1. **Archetype lens (WS-2):** ARCH-3 — no-earnings, room-to-band at confirmation, median first touch 7h, p25 4h. Basket names concentrate here (6.5%).
2. **Visual forensics (WS-1):** 12 of 18 sampled hourly winner charts share a signature — a multi-day flat base with dying volume, an ignition bar just before the confirmation bar, then a violent touch ~6 hours out.
3. **Missed-pattern mining (WS-5):** **P5a-ROOMRAMP** — room-to-band at bar −1 ∧ bullish-vote ramp ≥2 over trailing 20 bars — **lift 2.118 (n=2,581)**, the strongest novel candidate in the program.

Supporting footprints (WS-5): winners' votes ramp into the signal (median bullish-vote delta 4.0 vs 3.0 for near-winners); squeeze momentum already strong at bar −1 (0.703 vs 0.487).

## 5. The basket

**Stats:** n=648, 456 winners → **70.37% touch**, mean fill 5.243%, realistic expected capture **3.69%/signal** (naive 3.16%) vs universe 1.199% and basket v2 2.995%. All 13 names cleared the **$50M/day liquidity gate** (SHAZ thinnest at $78.2M); every condition in the table cleared **≥60% touch with n≥20**.

### 5.1 Tier Core — precision floor (8 conditions)
| Symbol | # conds | Qualifying conditions (n / wins / rate) | Avg rate | $M/d | Weight |
|---|---|---|---|---|---|
| SHAZ | 5 | score≥8 20/17/85.0, earn 49/30/61.2, room 21/15/71.4, vix 22/16/72.7, spy 21/13/61.9 | .703 | 78.2 | .058 |
| TTMI | 4 | earn 44/36/81.8, score≥8 27/19/70.4, triple 20/17/85.0, spy 49/35/71.4 | .772 | 112.0 | .085 |
| CVNA | 3 | triple 28/21/75.0, earn 58/40/69.0, vix 29/19/65.5 | .698 | 305.7 | .072 |
| TSEM | 4 | score≥8 33/32/97.0, triple 23/22/95.7, room 27/25/92.6, earn 20/16/80.0 | .913 | 141.6 | .072 |
| VRT | 4 | room 30/17/56.7, earn 22/12/54.5, vix 21/13/61.9, spy 25/14/56.0 | .573 | 63.9 | .075 |
| AXTI | 3 | room 20/14/70.0, vix 21/16/76.2, spy 21/13/61.9 | .694 | 88.4 | .059 |
| LITE | 4 | score≥8 34/21/61.8, room 25/20/80.0, triple 24/18/75.0, vix 27/16/59.3 | .690 | 158.2 | .103 |

### 5.2 Tier Satellite — conviction × 1.25 (5 conditions)
| Symbol | # conds | Qualifying conditions (n / wins / rate) | Avg rate | $M/d | Weight |
|---|---|---|---|---|---|
| HUT | 2 | earn 38/26/68.4, vix 28/22/78.6 | .735 | 402.4 | .060 |
| CRDO | 2 | earn 39/25/64.1, spy 38/28/73.7 | .689 | 388.9 | .066 |
| NBIS | 3 | earn 28/23/82.1, room 30/27/90.0, vix 24/22/91.7 | .879 | 267.1 | .088 |
| ANF | 3 | earn 24/22/91.7, room 26/23/88.5, spy 26/20/76.9 | .857 | 214.3 | .076 |
| OKLO | 3 | triple 21/15/71.4, earn 20/16/80.0, spy 31/24/77.4 | .763 | 598.1 | .073 |

### 5.3 Tier Watch — paper-watch only (1 condition, excluded from the 13)
USAR — earn 24/19/79.2, triple 20/14/70.0 (avg .746, $64.3M). Swap-in packet: n=55, 36 wins, 0.655 touch, 4.65% fill — mid-pack expectancy, IN if a name drops.

### 5.4 Concentration notes
- **room_to_band accounts for 53.4% of basket winners; top-3 names 29.6%.** No name exceeds 1.3% of any condition's winners.
- **TSEM–SMTC correlation 0.8032** (> 0.80 cap) → SMTC demoted to watch; TSEM kept (4 floor conditions at 93.5% vs SMTC's 2).
- Cluster caps: semis 5/5 AT CAP (TSEM, SMTC, AXTI, LITE, CRDO); crypto 1/2; nuclear/rare-earth 1/1 each.
- Per-name expectancy: NBIS **87.5% touch, n=48, 4.87% expcap** (anchor); ANF 8.47% mean fill, n=28, 6.05 expcap (fat-tail, n noted); AXTI 59.6% touch / 5.94% fill / 3.54% expcap; VRT 49.2% touch, gap-driven majority (53%), 12/12 pre-earnings winners.
- Weighting: expected-capture weighting wᵢ = (tᵢ·fᵢ)/Σ, equal-weight as dumb baseline. Quarterly promotion/relegation, mechanical rules (≥3 conditions at strict floors ≥60% conv, liq ≥$50M, corr ≤0.80, cluster headroom).

### 5.5 Watch list (promotion paths)
SMTC (2 floor legs + corr eviction resolution); VICR (1/2, needs room leg); POET (earnings-vix-spy cluster, room leg in progress); FIVN, GTLB, WOLF, SMR, CIFR, XPEV, AG (2-3 positive legs each, need one more floor leg).

---

## 6. New frontiers (WS-8)

### 6.1 S1 — WS8-COMEBACK-1D: Comeback genome long entries
- **Predicate (byte-exact `foliotend-market-sidecar/1.0.1`):** daily `genomes()` raw output (not the display visibility gate): ema21_reclaimed (close ≥ ema21) ∧ rsi_improving (+5/12 bars) ∧ macd_slope_positive ∧ conflict_evaporating ∧ above_low_anchor (close ≥ 52-bar low); score ≥ 3/5; genome index ≥ 12; price ≥ $5; 20d median dollar volume ≥ $10M; dedupe 1/symbol/20-bar block; entry next daily open.
- **Metric:** 20-daily-bar net excess − 51bp vs same-symbol nearby control. n floors: ≥1,000 matched pairs, ≥100 symbols, ≥20 blocks, ≥8 weeks. Pass: pair-weighted net excess > 0, one-sided p<0.05 (double-clustered SE), +5% touch lift > 1.0. Baselines: roster buy-and-hold; random symbol×week bars.
- **Sizing context:** pooled **+1.799%/20 bars** over 10,248 pairs / 1,761 symbols (1d), +1.40% (1h); symbol-level 57.9% positive, z=6.60.

### 6.2 S2 — WS8-DAILYGREEN-DISCOVERY: sidecar Daily Green Base Expansion
- **Predicate (byte-exact v1.0.1):** 1d ∧ buy-green ∈ primaryMarkers ∧ close > ema200 ∧ ema200 > ema200[−20] ∧ compression ≤ 0.75 ∧ close > max(high[−21..−1]) ∧ (close/ema21−1) < 0.15 ∧ (upVolumeShare₁₃ ≥ 0.50 OR participation-footprint); 260-bar fetch (EMA200 needs 220+); price ≥ $5, $10M vol; dedupe 1/20-bar block; next-open entry.
- **Metric:** 20/60/120-bar terminal returns net 51bp, 102bp stress mandatory, Holm across horizons. n floors: ≥200 events, ≥100 symbols, ≥20 blocks, ≥6 months, two control families (buy-green failing ≥1 gate; compression+EMA200-rising without buy-green). Pass: 20-bar net excess > 0, p<0.05 double-clustered, Holm, double-cost stress.
- **Sizing context:** the sealed H4 daily-green analog passed 8/8 gates — **+7.71% costed winsor mean, +5.99% median, 72.9% positive** (n=48).

### 6.3 S3 — WS8-LEADER-1D-SHORT: Leader genome short entries
- **Predicate (byte-exact v1.0.1):** daily `genomes()` raw output: ema21_extended (close ≥ 1.08×ema21) ∧ rsi_strong (≥60) ∧ participation_expanded (rvol ≥ 1.2) ∧ path_efficient (≥0.30) ∧ bullish_vote_majority (≥4); score ≥ 3/5; 1,838-name roster minus hard-to-borrow (missing borrow data → excluded, never assumed); dedupe 1/20-bar block; short at next daily open.
- **Exit:** 20-bar time stop OR daily close < EMA21 − 0.5×ATR(14), whichever first.
- **Metric:** short net = (open_{t+1}/close_{t+20} − 1) − 51bp − borrow(20d). Borrow: 5%/yr baseline, 15%/yr stress. n floors: ≥1,000 pairs, ≥100 symbols, ≥20 blocks, ≥8 weeks. Pass: short net excess > 0, one-sided p<0.05, survives stress directionally. Baselines: short random bars; short-every-bar.
- **Sizing context:** pooled **−8.76%/20 bars**, 1,754 pairs, 26.6% pair-positive, 20.2% symbol-positive, z=−19.3.
- All three run on **prospective data from 2026-10-01** under the WS-9 harness (append-only JSONL ledger, lane-matched signals).

### 6.4 Further greenfield opportunities (ranked backlog, condensed)
- **Earnings-calendar drift sleeve (O20):** SEDG post-earnings 10/10, XYL post-earnings 10/10, EXP — "the earnings calendar converts where the engine does not." Already queued as P5-EARN for validation.
- **Gap-impulse exit specialization (O16):** 20.1% gap-driven touches want exit-at-touch (+0.53pp gap-through premium); 79.9% earned retain.
- **sell-red / sell-magenta as exit trigger (O7):** the engine's native sell markers vs the desk's proxy trigger — never benchmarked head-to-head.
- **Weekly→1H sequencing (O17):** sidecar phenotype active anywhere in trailing 13 weeks → 24/553 episodes, +5% touch **83.3% vs 67.3%** baseline.
- **Fifth-family discovery (O18):** unclassified near-miss groups — 1wk/buy-cyan EARLY_MARKUP/RECOVERY (n=34, medT +35.4%, 71% positive), 1wk/buy-green EARLY_MARKUP/BREAKOUT_26 (n=24, medT +35.2%, 92% positive); Tier-B #1 cell above two Tier-A cells' scores.
- **Responder model as universe tilt (O26):** logistic AUC 0.798; ATR% importance 0.0388 (~4× #2); top decile pred 0.631 / actual 0.711 vs bottom 0.011/0.003.

---

## 7. Questions for Grokbot

1. **Corroboration:** do you see the same four signatures on your side — room-to-upper-band, the earnings window (especially post), the coil (room at bar −1 + vote ramp), and higher ATR at the confirmation bar? Which is strongest in your data?
2. **GainzAlgo cross-check:** the reversal-engine scrape showed engines that don't use our gates at all still find winners on the same names — do those overlap our archetypes (especially Earnings Detonation and the coil)?
3. **ATR gate:** can you replicate the winner-vs-twin ATR% difference in your data? If it holds there too, that's the most portable finding in the program.
4. **Comeback / Leader genomes:** anything in your lanes that looks like a reclaim-genome (ema21 reclaimed, improving RSI, evaporating bearish conflict) or an extension-genome (8%+ over ema21, strong RSI)? These are our two biggest new frontiers (S1/S3).
5. **The basket:** of SHAZ, TTMI, CVNA, TSEM, VRT, AXTI, LITE, HUT, CRDO, NBIS, ANF, OKLO, USAR — any you'd add or cut based on your own data?
6. **New alpha:** anything in your findings that maps onto our archetype table, or something in a lane we haven't mined?
