# TRULLÁS DIVERGENCE — REPLICATION SPEC v1.0 (FROZEN)

**Commissioned by:** the desk owner, 2026-10-25 ("Yes please" to the spec-first offer).
**Author:** Midna. **Date frozen:** 2026-10-25. **Status: FROZEN before any data is touched.**
**Companion research:** `~/workspace/research_notes/trullas-triple-divergence-specs-20261025-0745/report.md` (pass 1) and `~/workspace/research_notes/trullas-exhaustive-pass-20261025-1515/report.md` (pass 2). Every rule below is tagged **[PRIMARY]** (Trullás stated it, sourced), **[SECONDARY]** (someone else's reconstruction), or **[DEFAULT]** (my frozen choice where the record is silent). No rule changes after the backtest starts; any change is a new spec version and a new, separate test.

---

## 0. What this test is, and what it is not

David Trullás Vila has won six consecutive Quarterly Futures Day Trading titles at the World Cup Trading Championships (official, verified 2026-10-25), including Q2 2026 at +2,222.6%. His method, by his own repeated statement, is **manual and discretionary**: he picks price extremes by eye and by volume signature, and he states on camera that the complete strategy is taught only live to his academy students.

This spec therefore tests **the mechanical skeleton of the method exactly as far as the public record defines it**, with the undefined joints frozen as labeled defaults. A PASS means the skeleton, with no human eye in it, carries an edge on the test instrument. A FAIL means the edge lives in the discretionary residue (extreme selection, judgement, execution feel) that the public record does not contain. Both outcomes are answers. Neither outcome says anything about Trullás himself, who trades with the residue included.

## 1. The claim under test

> On Nasdaq intraday bars, a regular divergence between two price extremes — confirmed across MACD (required), RSI, and volume — followed by a Fibonacci-anchored entry at the 23.6% retracement of the divergence swing, a stop one tick beyond the extreme, and exits at the 38.2% and 61.8% levels, produces positive expectancy net of realistic costs, and produces **more** expectancy than the identical machinery run without the divergence condition.

The second clause is the real test. Shorting pivot highs with a Fib ruler may make or lose money on its own; the claim being examined is that **the divergence is what pays**.

## 2. Instrument and data

- **Primary instrument:** QQQ, 1-minute bars, Alpaca SIP feed, regular trading hours only (09:30–16:00 ET). **[DEFAULT]** — Trullás's championship account trades the Nasdaq future exclusively **[PRIMARY]**; the desk has no futures feed, so QQQ 1-minute bars are the frozen stand-in. The NQ≠QQQ gap is a named limitation (§12), not a footnote.
- **Window:** 2024-01-02 through 2026-10-23, every trading day, no exclusions. **[DEFAULT]** Frozen now, before any fetch. Roughly 2.8 years, ~700 sessions.
- **Secondary instrument:** SPY, same rules, same window. Reported separately; **cannot upgrade the verdict** (he does not trade the S&P for titles **[PRIMARY]**).
- **Data hygiene:** bars with zero volume or crossed quotes dropped; days with fewer than 300 RTH bars excluded and counted; corporate-action adjustment as delivered by SIP intraday (none expected intraday). Any data gap is reported, never silently interpolated.
- Indicators are computed on the continuous concatenated RTH series (overnight gaps simply absent). **[DEFAULT]**

## 3. Session and clock rules

- Signal window: divergences may only be *acted on* between **09:30 and 11:00 ET**. **[DEFAULT]** anchored to **[PRIMARY]** facts: he works the US open, is normally done by ~16:00 Spanish time (≈10:00 ET), and occasionally works to ~10:20 ET.
- Both extremes of a traded divergence pair must occur **on the same trading day**. **[DEFAULT]** (His daily/1-hour context screens are acknowledged as his real filter; per §12 they are context he reads, not a rule the record lets us freeze, and they are excluded rather than improvised.)
- No entries on news prints is his rule **[PRIMARY]** and is **not** implemented: no frozen news calendar exists in the record, and inventing one would be an unlabeled default. Named here as a known deviation.
- **Hard flat: 12:00 ET.** Any open position is exited at market at 12:00 ET. No overnight holds, ever. **[DEFAULT]** from the day-trading frame **[PRIMARY]**.
- Maximum **5 entries per day**; if more signals qualify, the earliest five are taken. **[DEFAULT]** from his documented days (5 trades in 17 minutes, then done **[PRIMARY]**).

## 4. Pivot machinery — the frozen stand-in for his eye

This section is the spec's biggest honest compromise. Trullás chooses extremes **discretionarily, keyed to volume signature** **[PRIMARY]**, and states no pivot rule. The following machinery is therefore **[DEFAULT]** throughout, chosen once, here, and never tuned after results are seen.

- **Pivot high:** a bar whose high is strictly the highest of the 5 bars before and the 5 bars after it (k = 5). **Pivot low:** mirror. A pivot is *confirmed* only when its 5 right-side bars have closed; no signal may use a pivot before its confirmation bar. (This is the anti-repaint clause: the classic failure of divergence studies is pivots that only exist in hindsight.)
- **Pairing:** a divergence pair is two consecutive confirmed pivots of the same kind (two highs or two lows).
- **Separation:** the two extremes must be at least **10 bars** apart and at most **120 bars** apart.
- **Indicator readings** are taken at the extreme bars themselves (MACD line value, RSI value, bar volume at each pivot bar). The *decision* is made at the second pivot's confirmation bar; execution follows §6. Causality is audited bar-by-bar in verification: every quantity used must be knowable at the decision bar.

## 5. Divergence definitions

- **MACD:** MACD(12, 26, 9), read on the **MACD line**. Settings **[SECONDARY]** (universal defaults; Trullás states no settings anywhere in the public record — Gap 1, still open). Line (not histogram) **[DEFAULT]** from **[PRIMARY]** evidence: his book's MACD chapter is organised around the two lines and their crosses, and his named "fallo de MACD" pattern is a line phenomenon.
- **Regular bearish divergence:** second pivot high **higher** than the first, with the MACD line **lower** at the second high than at the first. **Regular bullish divergence:** mirror at lows (lower price low, higher MACD low).
- **RSI divergence:** RSI(14) **[PRIMARY period, from his book's entry chapters]** lower at the second high (bearish) / higher at the second low (bullish), read at the extreme bars. No threshold condition in the primary arm; his "RSI out of overbought" sizing nuance was never pinned down (Gap 3) and appears only as sensitivity S6.
- **Volume divergence:** bar volume at the second extreme **lower** than at the first extreme. **[PRIMARY]** structure ("a new extreme must print higher volume than the prior extreme, or it is divergence"); single-bar reading **[DEFAULT]**.
- **MACD is required.** No MACD divergence, no trade, regardless of RSI and volume. **[PRIMARY]** ("If MACD doesn't give me the image I want to see, I don't trade.")
- **Divergence count** = number of {MACD, RSI, volume} divergences present, 1 to 3. Drives size (§7), exactly his "one more contract per divergence" rule **[PRIMARY]**, mapped to risk units.
- **Hidden divergences are excluded from the primary arm** (continuation patterns; the championship pattern and the originating claim centre on regular divergence). Included as sensitivity S5 only.
- **"Fallo de MACD"** (fast line fails to cross the signal line at successive extremes **[PRIMARY]**) is excluded from the primary arm: it is a distinct named pattern and formalising its "fails to cross" window would require two more invented parameters. Sensitivity S7 only.

## 6. Fibonacci geometry, entry, stop, targets

For a **bearish** setup (bullish is the exact mirror):

- **Swing:** A = the lowest low between the two pivot highs; B = the second pivot high. **[DEFAULT]** — this anchor recipe is the **[SECONDARY]** reconstruction (Grok), geometrically consistent with his stated construction (extreme-to-extreme projection, "the maximum/minimum between the extremes" for the hidden case **[PRIMARY]**) but never confirmed by him (Gap 5, still open).
- Levels measured as retracements downward from B toward A: level(p) = B − p × (B − A).
- **Entry trigger:** after the second pivot confirms, the first bar that trades **at or below level(0.236) minus $0.01** fills a short at that bar's price at the trigger tick (bar low if the bar's range crosses the trigger, else bar close). Entry level ≈ 23.6% **[PRIMARY]** ("usually around 23–25%"), 1 tick on the break **[PRIMARY]**; tick = $0.01 on QQQ **[DEFAULT]**.
- **Entry expiry:** if the trigger has not fired within **30 bars** of confirmation, or price first trades above B + $0.01 (the extreme breaks), the setup is void. **[DEFAULT]**
- **Stop:** B + $0.01 — one tick beyond the extreme **[PRIMARY]**.
- **TP1:** level(0.382) **[PRIMARY]**. **TP2:** level(0.618) **[PRIMARY]** (his "second third"; the 66.7% reading is sensitivity S4).
- Orders are evaluated on bar ranges in strict sequence within each bar: stop before targets when a bar spans both (pessimistic ordering) **[DEFAULT]**.

## 7. Sizing and risk

- **Unit risk:** 1 unit = **0.25% of current equity** of risk to the stop. Position size in shares = (units × 0.25% × equity) ÷ (stop distance in $). **[DEFAULT]** mapping of his per-divergence contract ladder **[PRIMARY]**.
- Position size is capped at 25% of equity in notional per trade; if the cap binds, it is recorded (it should bind rarely on 1-minute swings).
- **Daily loss stop:** after cumulative realised day P&L reaches **−0.75% of equity** (three full units — his "bullets" rule: the day's assumable loss pre-split into a minimum of 2–3, maximum 5 bullets **[PRIMARY]**), no new entries that day. **[DEFAULT]** mapping.
- Equity starts at $1,000,000 for reporting **[DEFAULT, house convention]**; results are also reported per-trade in R (multiples of initial risk) so the sizing convention cannot manufacture the verdict.

## 8. Trade management and exits

- At **TP1: exit 50%** of the position and move the stop on the remainder to the **entry price** (true breakeven before costs). **[DEFAULT]** — his observed splits are situational (80/20 documented **[PRIMARY]**; 4-of-5 off early with staggered runners **[PRIMARY]**) and his breakeven stop sits at entry + 1.5 NQ points to cover commission and slippage **[PRIMARY]**; on QQQ that offset is ~$0.04 and inside the cost model, so entry-exact is the frozen simplification, named as such.
- Remainder exits at **TP2**, at the moved stop, or at the 12:00 ET hard flat, whichever comes first.
- No re-entry on the same divergence pair. No pyramiding in the primary arm (his "en ráfaga" adding **[PRIMARY]** is discretionary in trigger and is sensitivity S8, not primary).

## 9. Costs

- **Primary: 7 bps round-trip** on traded notional, charged pro-rata per exit leg. **Stress: 14 bps.** **[DEFAULT, house convention from the Washout/Gate specs.]**
- QQQ 1-minute spreads are typically a penny; the bps charge stands in for spread + slippage + fees combined and is deliberately not generous to the strategy.

## 10. Arms

1. **PRIMARY** — QQQ 1-minute, regular divergences, §§3–9 exactly. This arm alone decides the verdict.
2. **CONTROL** — identical machinery, identical pivot pairs, identical Fib entries, stops, targets, session and caps — with the **divergence condition removed**: every consecutive same-kind pivot pair that meets the geometry trades, size fixed at 1 unit. The control isolates what the divergence condition itself contributes.
3. **SECONDARY** — SPY 1-minute, primary rules. Reported; cannot upgrade the verdict.
4. **SENSITIVITIES (report-only, never upgrade, all run and published whatever they show):**
   - S1: 5-minute bars, all else equal.
   - S2: pivot k = 3. S3: pivot k = 8.
   - S4: TP2 at the 66.7% level.
   - S5: hidden divergences included (same counting and geometry, continuation direction).
   - S6: RSI divergence counted only when RSI at the second extreme is leaving an extreme zone (>70 falling bearish / <30 rising bullish).
   - S7: "fallo de MACD" admitted as a qualifying MACD divergence (fast line fails to cross the signal line in the trade direction within the 5 bars following the second extreme, price extreme still intact).
   - S8: pyramiding on strength — one add of 1 unit when price first moves 0.5R in favour, stop on the whole position to entry at the add.

## 11. Pre-registered verdict bar

The verdict is computed mechanically from the PRIMARY arm:

- **(a) Mass:** at least **150 completed trades**. Fewer → verdict is **INSUFFICIENT DATA**, not a pass and not a fail.
- **(b) Edge:** mean expectancy per trade **> 0 net at 7 bps**, and **profit factor ≥ 1.20**.
- **(c) The divergence pays:** primary expectancy per trade **strictly greater** than CONTROL expectancy per trade.
- **(d) Survivable:** maximum drawdown of the daily-marked equity curve **≤ 12%** under the frozen sizing.
- **(e) Cost-robust:** expectancy per trade **> 0 at 14 bps**.

**PASS** requires all of (a)–(e). **Any failure is a FAIL**, with this pre-committed conclusion, printed verbatim in the report:

> "The mechanical skeleton of the Trullás divergence method, as far as the public record defines it, does not reproduce an edge on QQQ 1-minute bars. What remains of the method is the discretionary residue (extreme selection and judgement) that the record does not contain and an algorithm cannot borrow."

On PASS, the pre-committed conclusion is:

> "The mechanical skeleton carries an edge on QQQ 1-minute bars under frozen rules. This licenses a paper-sleeve design discussion and nothing more; it does not establish that the skeleton is what wins the championships."

**No-retest clause:** pivot width, separation, levels, sizing, and the session window are frozen by this spec. A disappointing result may not be answered by adjusting them inside this study. Any adjusted version is a new spec, a new version number, and a new pre-registration — and the report must say so.

## 12. What this test cannot prove (read before citing it)

- **NQ ≠ QQQ.** Futures and the ETF track closely, not identically; intraday microstructure differs. A FAIL does not touch his futures results; a PASS does not certify them.
- **His clock is finer.** He executes off 5-second and 30-second views; the desk's finest bar is 1 minute. Entries and stops here are coarser than his.
- **The eye is the method's core.** §4 is a stand-in. If the skeleton fails, the most likely single cause is this substitution, and the report must rank it first among explanations rather than declaring "divergence doesn't work" — our own AI-50 study already showed daily-bar divergence is anti-predictive, and this study exists precisely because the intraday claim is a different claim.
- **Tournament ≠ portfolio.** His sizing serves a quarterly percentage contest with a $2,500 minimum restart **[PRIMARY facts]**; the frozen portfolio sizing here is ours.
- **Survivorship of the claim itself:** we are testing a champion's published method because he won. The control arm (§10.2) is the guard: it asks whether the divergence, not the Fib machinery around it, is the active ingredient.

## 13. Reporting requirements

The backtest report must contain, at minimum:

1. The verdict as its **first line**, computed by §11 mechanically, with the (a)–(e) table filled.
2. Full trade ledger (every primary-arm trade: date, direction, extremes, divergence count, entry/stop/TP prices, exit reason, R and $ P&L at both cost levels).
3. Expectancy broken down by **divergence count (1 / 2 / 3)** — his sizing ladder claims more divergences means a better trade; the data must be allowed to agree or disagree in the open.
4. Expectancy by **year** and by **direction** (long vs short).
5. The CONTROL arm's full headline metrics beside the primary's.
6. Every sensitivity S1–S8 with headline metrics, published whatever it shows.
7. Data-quality accounting: sessions used, sessions excluded and why, bars dropped.
8. **Independent verification before delivery** (house law): a fresh-code recompute of headline metrics from the trade ledger, a bar-by-bar hand audit of a random 14-trade sample, and a causality audit proving no quantity was used before its confirmation bar. A verifier-found bug means repair at the source and a full re-run, as with the Washout study.
