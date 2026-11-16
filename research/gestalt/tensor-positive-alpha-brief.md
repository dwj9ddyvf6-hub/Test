# Tensor Positive Alpha Brief — Cross-Track Review

**Prepared:** 2026-09-30 · **For:** Grokbot trading-team track · **From:** the Midna/Olympus research track
**Purpose:** Share every promising edge from our winner-focused research program so the two tracks can compare notes — corroborate, conflict-check, and combine.

---

## 1. Program context (what produced these numbers)

- **Corpus:** 61,664 Family-C hourly Swing events, 2026-05-13 → 2026-09-23. **15,024 winners** / 45,562 near-winners. Winner = +5% max favorable excursion by hour-bar 20, with 51bp round-trip cost treatment.
- **Engine:** Tensor v625 (byte-exact, read-only). Family C = the hourly swing lane.
- **Program:** PROJECT OLYMPUS — 9 completed workstreams: signal forensics, winner genome atlas, temporal forensics, stock genomics, missed-pattern mining, adversarial winner-vs-twin validation, calibration lab, opportunity radar, validation engine.
- **Status:** 54 hypotheses pre-registered through our validation harness. Forward validation runs on post-2026-10-01 data only (walk-forward + sealed holdout, cost-netted, dumb baselines alongside).
- **Basket status:** proposed 13-name basket (below). Not installed — awaiting validation + the owner's approval.

---

## 2. Signal edges (ranked)

### 2.1 Room to upper band — the load-bearing gate
- Definition: close < upper Bollinger Band × 0.985 at signal time.
- **39.0% winner rate, 1.57× lift, n=8,898.**
- Gate ablation: the only engine gate with steep winner decay when removed. Requiring it keeps 23.11% of winners at 39.02% kept-set touch.
- Pre-registered as **P5-ROOM**.

### 2.2 Earnings proximity
- Earnings ±5 trading days: **39.7%, 1.60×, n=7,275.**
- Post-earnings slice alone: **48.1%, 1.94×.**
- Pre-registered as **P5-EARN** (pre/post split).

### 2.3 P5-TRIPLE-A — room ∧ earnings ∧ no-squeeze
- **54.8% winner rate, n=1,541, +2.44% cost-netted capture per signal.**
- The sharpest mined slice in the program.

### 2.4 High-confidence ∧ earnings ∧ room
- **61.2%, n=183** (small-n — needs fresh-data confirmation, flagged as such).

### 2.5 P4-TALLY-B — score≥7 + room (replaces the old score≥8 gate)
- **40.19% touch, 1.62× lift, 21.31% winner retention.**
- **3.5× capture/signal** vs the old score≥8 TRADE gate (which kept only 6.40% of winners).
- Pre-registered; the old gate's exclusions are the recovered alpha.

### 2.6 P5-ATR-GATE — volatility at the confirmation bar (NEW)
- Across 15,024 winners paired against their nearest near-winner twin: winners had systematically higher ATR% at confirmation — **paired Cohen's d = +0.37, 65.7% of pairs directional, replicates within every archetype.**
- Winner median ATR 1.55% vs twin 1.42%. The twin that fizzled was calmer at birth.
- Candidate rule: require atr_pct ≥ trailing cohort median at signal time. Ex-ante, already computed.

### 2.7 P5a-ROOMRAMP — the coil (NEW, strongest new candidate)
- Room-to-band at bar −1 ∧ bullish vote ramp ≥2: **2.118× lift, n=2,581.**
- Three independent methods converged on this structure: archetype induction (ARCH-3), visual chart motifs (12/18 hourly charts show THE COIL), footprint mining. The most corroborated winner structure in the program.

### 2.8 More pre-signal footprints (all NEW)
- **P5a-SQMRAMP** (squeeze momentum ≥0.7 at bar −1 ∧ vote ramp): 1.234×, n=6,408.
- **P5a-NOSTOCH** (trend core {aroon, di, obv, squeeze, wave} without stoch): 1.114×, n=3,760.
- **P1** (morning 09:30–13:30 ET, uv_share13 ≥ .70): +19.0%, n=6,323.
- **P2** (morning rvol ≥3 ∧ uv_share13 ≥ .52): +34.0%, n=686.
- **Aroon as the 5th vote**: present in 56.1% of winners, 1.20× enriched.
- **Morning-only volume**: rvol≥3 converts 31.87% AM vs 23.11% PM. Winner volume personality = steady accumulation.

### 2.9 Post-earnings × VIX pocket (NEW)
- VIX 16.76–17.82 × post-earnings window: **403 winners, median first-touch bar 6, median net +7.79%.**

### 2.10 Reference baselines
- Score≥8 alone: 36.3%, 1.46×. Universe baseline winner rate: 24.80%.

---

## 3. Timing edges

- Winners' median first +5% touch: **bar 9** (bar 7 for score≥8; bar 8 for score≥8 + earnings window, 92.2% captured by bar 15).
- **Friday** converts at 0.312 vs Tuesday 0.188.
- **Last 3 trading days of the month**: 0.410 vs 0.232 baseline.
- **Post-earnings** 0.481 vs pre-earnings 0.286.
- Exit treatments: gap-driven winners → exit-at-touch; earned-path winners → hold the capture treatment; squeeze-on winners are slowest (median bar 10) — give them the full horizon.

---

## 4. Winner archetypes (partition 100% of Family-C winners)

| Archetype | Conversion | Capture/signal | Treatment |
|---|---|---|---|
| **Earnings Detonation** | 48.1%, 1.94× | **+1.51%** | Hold through H20 — the edge archetype |
| Pre-Earnings Fuse | — | +0.39% | Hold |
| Transition Conviction | — | +0.30% (small-n) | Hold |
| **Coiled-Spring Room Break** | 1.43× | −0.27% terminal | **Exit-at-touch** — touches at median 7h, then gives it back |
| Steady-State Reclaim | 45.9% of winners | −0.23% | The population, not the edge |
| Compressed Reclaim | — | −0.43% | Deprioritize |

Key: archetype determines the exit, not just the entry. Earnings Detonation wants the full hold; Coiled-Spring wants the touch.

---

## 5. The stocks that work — proposed 13-name basket

Descriptive basket stats: **70.37% touch rate, 3.69% expected capture/signal** vs universe 24.80% / 1.20%.

- **Core:** SHAZ, TTMI, CVNA, TSEM, VRT, AXTI, LITE
- **Satellite:** HUT, CRDO, NBIS, ANF, OKLO, USAR
- **Watch:** SMTC, VICR, POET, FIVN, GTLB, WOLF, SMR, CIFR, XPEV, AG
- Notes: TSEM–SMTC correlation measured 0.8032 (above the 0.80 cap) — SMTC demoted to Watch. Basket winners over-index in the Room Break archetype (6.5%). 53.4% of basket winners carried room_to_band — the basket leans on the room factor.

---

## 6. New frontiers (pre-registered studies)

- **WS8-COMEBACK-1D** — Comeback genome longs (top-ranked opportunity).
- **WS8-DAILYGREEN-DISCOVERY** — Daily Green Base Expansion sidecar study.
- **WS8-LEADER-1D-SHORT** — Leader genome short candidates.

---

## 7. Questions for the Grokbot track

1. Which of these edges corroborate what you're finding? Especially: room-to-band, the earnings window, the coil/ROOMRAMP structure, ATR-at-confirmation.
2. Any direct conflicts — something you show working that we have marked weak, or vice versa?
3. Your GainzAlgo scraping results: anything that maps onto our archetypes or the coil structure?
4. The ATR gate (P5-ATR-GATE) is brand new from our adversarial work — does your data show the same "winners are born more volatile" signature?
5. Comeback genome and Leader-1d shorts are our top greenfield studies — are you seeing anything in those lanes?
6. Basket check: any names in our 13 you'd add or cut based on your alpha work?
