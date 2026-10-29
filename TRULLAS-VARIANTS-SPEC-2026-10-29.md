# TRULLÁS VARIANT FAMILY — SPEC v1.0 (FROZEN)

**Commissioned by:** the desk owner, 2026-10-29 ("build multiple variants of the Trullas divergence algorithm, varying the manual and discretionary parts to sample the space his eye moves through").
**Date frozen:** 2026-10-29. **Status: FROZEN when written. No joint value changes after any variant sees a bar. Any change after freeze is a new spec version, a new roster id, and a new forward record; it is never a retune of a live variant.**
**Primary spec:** `TRULLAS-SPEC-2026-10-25.md` v1.0 FROZEN (same directory). **Primary sleeve:** roster id `trullas_divergence`, live paper since 2026-10-26, QQQ 1-minute SIP bars.
**Feasibility basis:** inspect phase 2026-10-29, recorded in `~/workspace/muse-desk-v3/TRULLAS-VARIANTS-BUILD.md`. All ten named joints were found implementable cleanly on the desk's real producer inputs. Dropped joints: **none** (see §5).

---

## 1. What this family is

Ten paper sleeves, each a copy of the primary's machinery with **exactly one** named discretionary joint changed, and nothing else. The family samples the space the originator's eye moves through, in the open, so no variant can be cherry-picked afterward: every variant runs on its own record, on the same days, under the same judging rule (§4).

## 2. Hard rails (apply to every variant)

- **Primary untouched in behavior.** The primary sleeve `trullas_divergence` keeps its frozen behavior. A shared-code refactor is permitted only under the inspect phase's proof duty: the primary's decisions on the fixed golden bar fixture must be byte-identical in outcome before and after (golden entry / stop / TP1 / TP2 / qty, causality and truncation tests unchanged, all primary blockers green), and that proof must be stated plainly in the build record. If the proof cannot be produced, variants ship as subclasses overriding only the named seam, and no unproven refactor lands.
- **No backtest.** the desk owner cancelled the Trullas backtest and ruled the live paper record is the test. No variant is backtested, and no backtest result may be cited for or against any variant. Each variant proves itself forward on its own live paper record only.
- **Paper only.** No strategy, sizing, or risk change to the primary or to any other sleeve. Each variant is its own roster sleeve with its own slice, its own state directory, and its own record.
- **One joint per variant.** A variant that differs from the primary in anything beyond its single named joint in §3 is not this variant; it is a defect to be cured at the source, not a design choice.
- **Cannot fire means cannot fire.** A variant whose joint makes it fire rarely or never is reported as "cannot fire" on its record. It is never silently widened, loosened, or retuned to make it fire.

## 3. Common inheritance (every variant, verbatim from the primary spec)

Except for the single joint named in its row in §4, each variant inherits the frozen primary spec (§§2–9 of `TRULLAS-SPEC-2026-10-25.md`) verbatim, including:

- Instrument QQQ, Alpaca SIP feed, regular trading hours only (09:30–16:00 ET); divergences acted on only 09:30–11:00 ET; both extremes of a pair on the same trading day; hard flat 12:00 ET; maximum 5 entries per day, earliest five taken.
- Pivot machinery: consecutive confirmed same-kind pivots; separation at least 10 bars and at most 120 bars; a pivot is usable only after its confirmation bars have closed (anti-repaint clause); indicator readings taken at the extreme bars; decision at the second pivot's confirmation bar.
- Indicators: MACD(12, 26, 9) read on the MACD line; RSI(14); regular divergence definitions exactly as primary §5, except where a variant's joint explicitly adds or conditions a case (§4).
- Fibonacci geometry: swing A = lowest low (bearish) / highest high (bullish) between the two extremes, B = second extreme; entry at the 23.6% level less / plus one tick ($0.01) on the first triggering bar after confirmation; entry expiry 30 bars or on a trade beyond B + / − one tick; stop one tick beyond the extreme; TP1 at 38.2%; orders evaluated stop-before-targets within a bar.
- Sizing: 1 unit = 0.25% of the sleeve's own slice equity of risk to the stop; units = divergence count (1–3) except where a joint (§4, v08 / v10) explicitly states otherwise; notional cap 25% of slice equity per trade; daily loss stop at −0.75% of slice equity; no re-entry on the same divergence pair.
- Exits: at TP1, exit 50% and move the remainder's stop to the entry price; remainder exits at TP2, the moved stop, or the 12:00 ET hard flat, whichever comes first. No pyramiding except v08, whose joint is pyramiding.
- Costs and reporting basis follow the desk's live paper machinery; results are reported per-trade in R and as percent return of the variant's own slice, per §4 of this spec. The primary spec's backtest window, control arm, and §11 verdict bar do **not** apply to any variant: they belonged to the cancelled backtest study, and §4 below is the only judging rule for this family.

**Slice and cadence (every variant):** own roster row in `config/sleeves.json`; slice **$10,000** (`capital_usd: 10000.0, cash_usd: 10000.0`); cadence **60 seconds**; `parked: false`; `session: "rth"`; `flat_by_close: false` with `flatten_time_et: null` (the sleeve owns its 12:00 ET flat; no second flatten path); own state under `state/<roster_id>/`; own install proof under `proof/install/<roster_id>.json`; own regression blockers wired into `desk/run_regression_blockers.sh`.

## 4. The ten variants (spec order)

### trullas_v01 — S1: 5-minute bars
- **Joint:** bar timeframe (primary spec §10, S1).
- **Primary value:** QQQ **1-minute** SIP bars; all bar-count rules (pivot k = 5, separation 10–120 bars, entry expiry 30 bars) counted in 1-minute bars.
- **Variant value:** QQQ **5-minute** native SIP bars (already served by the desk's warm bars product; the variant adapter requests the 5-minute series and the registry gains the `bars:QQQ:5Min` key, mirroring the primary install's 1-minute key). All bar-count rules stay at their frozen numbers, now counted in 5-minute bar units, per S1 "all else equal". Clock rules unchanged (09:30–11:00 ET entries, 12:00 ET flat). Cadence stays 60 s: the variant evaluates each cycle against the latest closed 5-minute bar, and exit checks stay per-cycle.
- **Everything else:** inherited verbatim (§3).

### trullas_v02 — S2: pivot width 3
- **Joint:** pivot width k (primary spec §10, S2).
- **Primary value:** k = **5** (an extreme must be strictly the highest / lowest of the 5 bars before and the 5 bars after it; confirmation lag 5 bars).
- **Variant value:** k = **3** (confirmation lag 3 bars).
- **Everything else:** inherited verbatim (§3), including separation and expiry counts in bars.

### trullas_v03 — S3: pivot width 8
- **Joint:** pivot width k (primary spec §10, S3).
- **Primary value:** k = **5**.
- **Variant value:** k = **8** (confirmation lag 8 bars).
- **Everything else:** inherited verbatim (§3), including separation and expiry counts in bars.

### trullas_v04 — S4: TP2 at 66.7 percent
- **Joint:** second target level (primary spec §10, S4).
- **Primary value:** TP2 at the **61.8%** retracement level (level(0.618)).
- **Variant value:** TP2 at the **66.7%** retracement level (level(0.667), the "second third" reading).
- **Everything else:** inherited verbatim (§3). TP1 (38.2%), the TP1 half-exit, and the breakeven move are unchanged; only the remainder's target moves.

### trullas_v05 — S5: hidden divergences included
- **Joint:** divergence types admitted (primary spec §10, S5).
- **Primary value:** **regular divergences only**; hidden (continuation) divergences excluded.
- **Variant value:** hidden divergences are **included in addition to** regular divergences (union, never a replacement). Frozen reading of "hidden", from the primary spec's §10 wording: at pivot highs, a **lower** second high with a **higher** MACD line reading at the second high; at pivot lows, the mirror (a **higher** second low with a **lower** MACD line reading). RSI and volume divergence counting mirrors the regular case (RSI / volume lower at the second high, higher at the second low, read at the extreme bars). Same pivot pairing, same Fib swing geometry (the between-extremes extreme anchor the primary already uses is the hidden-case anchor), same direction mapping (pivot-high setups trade short, pivot-low setups trade long), same MACD-required gate applied to the hidden MACD condition.
- **Everything else:** inherited verbatim (§3). Plan and management shape are identical to the primary.

### trullas_v06 — S6: RSI counted only when leaving an extreme zone
- **Joint:** when an RSI divergence counts toward the divergence count (primary spec §10, S6).
- **Primary value:** an RSI divergence counts whenever RSI is lower at the second high / higher at the second low, with **no zone condition**.
- **Variant value:** an RSI divergence counts **only** when RSI at the second extreme is leaving an extreme zone: bearish, RSI at the second extreme **> 70 and falling** versus the first extreme; bullish, RSI at the second extreme **< 30 and rising** versus the first extreme. Outside that condition the RSI divergence is simply not counted.
- **Everything else:** inherited verbatim (§3). Named explicitly: RSI never gates a trade in the primary (MACD alone gates), so this joint changes the divergence count, and therefore unit size only; it never changes whether a trade fires.

### trullas_v07 — S7: fallo de MACD admitted
- **Joint:** qualifying MACD patterns (primary spec §10, S7).
- **Primary value:** only a regular MACD line divergence qualifies as the required MACD divergence; "fallo de MACD" is excluded.
- **Variant value:** "fallo de MACD" is **admitted in addition to** regular MACD divergence (union) as a qualifying MACD divergence. Frozen reading, from the primary spec's §10 S7 wording and the 2026-10-25 exhaustive research pass: the MACD **signal line** (EMA(9) of the MACD line, the one additional series this variant computes) is used, and a fallo qualifies when, **within the 5 bars following the second extreme**, the MACD fast line **fails to cross the signal line in the trade direction** (bearish: fails to cross up through the signal line; bullish: fails to cross down through it) **and the price extreme stays intact** (no trade beyond the second extreme plus / minus one tick in that window). Timing is causal by construction: the decision bar is the pivot confirmation bar, exactly second-extreme + k(5) bars, so the full 5-bar fallo window is knowable at decision time; nothing after the decision bar is used.
- **Everything else:** inherited verbatim (§3), including the MACD-required gate (now satisfiable by regular divergence or by fallo).

### trullas_v08 — S8: pyramiding on strength
- **Joint:** adding to a winning position (primary spec §10, S8).
- **Primary value:** **no pyramiding**; one entry per divergence pair, sized once at entry.
- **Variant value:** **one add of 1 unit** when price first moves **0.5R in favour** (R = the original entry-to-stop distance). Two sub-values frozen here, before build, because the primary spec leaves them open: (a) add quantity = 1 unit on the primary sizing formula (0.25% of the sleeve's slice equity ÷ original risk per share), computed at add time; (b) intrabar ordering: within a bar, the add is evaluated **before TP1** (the 0.5R trigger distance, ≈0.118 × swing, is shorter than the entry-to-TP1 distance, 0.146 × swing, so on a monotonic move the add fires first), while the pessimistic **stop-before-everything** ordering remains supreme. At the add, the stop on the **whole** (enlarged) position moves to the **entry price**. The plan carries an `added` flag; no second add ever. The TP1 half-exit then applies to the enlarged position, and the breakeven-after-TP1 rule applies as inherited.
- **Everything else:** inherited verbatim (§3), including the daily entry cap, the daily loss stop, and the no-re-entry rule (the add is part of the original pair's trade, not a re-entry).

### trullas_v09 — volume signature read over a window around the extreme
- **Joint:** how volume at an extreme is read for the volume divergence count (named in the 2026-10-29 conversation; the primary spec's §5 single-bar reading is the labeled **[DEFAULT]** this joint varies).
- **Primary value:** volume divergence compares the **single extreme bar's** volume at the second extreme against the single extreme bar's volume at the first extreme.
- **Variant value:** volume at each extreme is the **sum of volume over a centred 5-bar window [i−2, i+2] around the extreme bar i**, at both extremes (equal widths, so sum and mean rank identically); the divergence test itself is unchanged (second extreme's windowed volume lower at highs / higher at lows than the first extreme's). The window is knowable at decision time because pivot confirmation (k = 5) guarantees the right-side bars exist. Window width frozen at ±2 bars; it does not change after freeze.
- **Everything else:** inherited verbatim (§3). Named explicitly: volume never gates a trade in the primary, so this joint changes the divergence count, and therefore unit size only; it never changes whether a trade fires.

### trullas_v10 — confirmation strictness: all three divergences required
- **Joint:** the firing gate on divergence count (named in the 2026-10-29 conversation; varies the primary spec's §5 "MACD is required" gate).
- **Primary value:** a trade fires when the **MACD divergence is present**; RSI and volume divergences only add to the count (1–3) that sizes the trade.
- **Variant value:** a trade fires **only when all three divergences are present** (price divergence with MACD **and** RSI **and** volume divergences; divergence count == 3). Every v10 trade therefore sizes at exactly 3 units.
- **Everything else:** inherited verbatim (§3), including how each of the three divergences is defined and read.

## 5. Dropped joints

**None.** All ten named joints (S1–S8 from §10 of the frozen primary spec, plus the volume-window and all-three-confirmation joints named on 2026-10-29) were verified at inspect against the desk's real producer inputs and implement cleanly. No substitute joint was improvised for any of them. If build later finds a joint cannot be implemented as written here, that variant does not ship improvised: the failure and its reason are recorded in the build record, and the variant is reported dropped with that reason.

## 6. Forward judging rule (the only verdict machinery for this family)

- **Record:** each variant is judged on **its own live paper record only**: its fills, its per-trade R (multiples of that trade's initial risk), and its slice percent return. No backtest, no fixture, and no sibling's record substitutes for it.
- **Comparison:** each variant is graded **against the primary and against its siblings on the same days**: same-window per-trade expectancy in R, and same-window percent return **versus SPY and versus QQQ over the identical window** (the house performance yardstick). A variant is never graded on days it did not trade alongside the comparison set.
- **Minimum mass:** no variant is **promoted, retuned, or killed on fewer than 30 of its own completed trades**. Below 30 completed trades its status is exactly "insufficient record", whatever its early numbers look like. (Retuning a live variant is in any case barred by the freeze in the header; a "retune" can only ever mean a new spec version under a new roster id.)
- **Cannot fire:** a variant that produces no qualifying setups is reported as **"cannot fire"**, with its evaluation counts, and left exactly as specified. It is never silently widened.
- **No cherry-picking:** all ten records are reported together whenever any one is reported. A family report that shows only the current leader is a defective report.
- **Promotion, if any, is the desk owner's ruling**, made on the graded forward record above, never on this spec and never on a fixture.

## 7. Build obligations carried from this spec (not part of the judging rule)

Each shipped variant carries: its own roster row (§3), a named regression blocker file wired into `desk/run_regression_blockers.sh` asserting (per variant) config-row shape and INPUTS equality, the one-joint difference on the golden fixture (decisions differ from the primary's only as its joint dictates, and match the primary's where the joint is inert), and primary identity post-refactor where the refactor route is used; a dated BUGLOG entry in `BUGLOG_2026-10-29.md` following the desk's install-entry convention; one install proof JSON per variant under `proof/install/`; roster-count pins updated for the sleeves that actually land; and a full gate run before any GREEN is claimed for the family.

**END OF SPEC — FROZEN 2026-10-29.**
