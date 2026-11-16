# Constants Provenance Ledger — 2026-11-16 (CONSTANTS-PROVENANCE-20261116)

Scope (claims verified against final artifacts, not repeated): morning census
instance-rows E1 191 + E2 18 + E3 112 + E4 163 = 484. saty_sol's 8 (inside
E3's 112) are EXCLUDED (pinned file) → 476 in-scope instance-rows.
E1's 191 = bp_buffer_frac 164 instances + FEE_PER_CONTRACT 20 instances +
hold/deadline 96 on 7 sleeves. E4's 163 = bp_buffer_frac again (same single
distinct constant). Distinct constants in scope: 1 (bp_buffer) + 1 (FEE) +
7 sleeve rows (96h) + 4 (aster_batch3 _BOOKS rows counted per sleeve pair) +
18 (E2) + 104 (E3 excl. saty_sol) = 135 distinct rows below (instance
counts noted per row).

Marking convention matched: the estate's existing form — a trailing inline
`#` comment (or a block comment directly above a constant block) naming the
source / spec / ruling, e.g. `# MAG-B3`, `# desk precedent: ...`,
`# source ...`. Every mark added by this lane carries the id
CONSTANTS-PROVENANCE-20261116 plus a resolvable pointer. NO value changed
anywhere in this lane (diff verified comment-only).

Dispositions: MARKED (provenance found, mark landed at source) /
ALREADY-MARKED (census claim stale: a provenance mark already exists on the
final tree; no edit) / OPEN (routes printed) / DERIVED-CANDIDATE (route 4
reached; candidate in the coordinator report only, no code change).

## Tranche 1 — desk-wide

| constant | value | location | route | source pointer | disposition |
|---|---|---|---|---|---|
| bp_buffer_frac | 0.02 | config/sleeves.json (381 rows at census; 387-row roster now), desk3/dispatcher.py defaults (4 sites: ll. 598, 1316, 1747/1811/1902/2193 pattern), every batch registry (port_batch2/6, aster_*, laz_*) | 1 PARTIAL: entered with CORE commit 638b70c34e589e95a8a2c8ba23a708f0085d45a1 (2026-10-24); BUGLOG_2026-10-25 D-GATE-PO10-SIZING uses "the 2% bp buffer" as a given; PURGE-REPORT: row schema "carried from the v2 lineage". No derivation, source study, or test naming 0.02 found in any BUGLOG/FIDELITY/doc read. 2: v2 lineage asserted, no v2 value record read. 3: no canonical 2% buying-power buffer standard exists (broker margin is instrument-level; a flat slice buffer is a desk safety choice). 4: candidate in report. | git 638b70c; BUGLOG_2026-10-25 | OPEN (327 of 476 instance-rows: E1 164 + E4 163; one distinct constant) |
| FEE_PER_CONTRACT | 0.65 | desk3/aster_b2.py:36 (definition; imported by desk3/aster_b4.py; 20 options sleeves across the b2/b4 books) | 1 FOUND + 3 CHECKED | FIDELITY-LEDGER batch-2 row: "option fee $0.65/contract/leg — source reads snapshot option_fees.per_contract_per_fill, which no v3 producer supplies yet"; aster_b2 header states the same; FIDELITY batch-3 row: fixtures supply $0.65, fee-less snapshot falls back to fee_bps=15. Route 3 (Alpaca Brokerage Fee Schedule, rev. 2026-10-12): Alpaca charges $0 commission on retail equity options; actual per-contract per-side pass-through = ORF $0.015 + OCC $0.025 + CAT $0.0003 = $0.0403 (sell adds TAF $0.00329 + SEC). $0.65 is the legacy industry-standard commission (Fidelity/Schwab/E*TRADE/IBKR fixed). FINDING: the desk models ~16x the real paper fee per contract per side (~$0.65 vs ~$0.0403 buy / ~$0.0436 sell; index options at Alpaca are $0.50/contract + exchange fees). Value NOT changed in this lane. | FIDELITY-LEDGER ll. 217, 301-302, 458; files.alpaca.markets BrokFeeSched | MARKED (1 definition site) |

## Tranche 2 — hold/deadline 96 (7 sleeves, E1)

| constant | value | location | route | source pointer | disposition |
|---|---|---|---|---|---|
| hold_h / deadline_h | 96 | desk3/aster_crypto.py, desk3/aster_batch7.py, desk3/aster_b12_crypto.py, desk3/aster_batch13.py (SPECS rows for the 7 crypto sleeves: NFS fixed96 + structural policies) | 2 FOUND (1 confirms) | Archive source/backend/r19_crypto.py:285 `exit_due_at = due + timedelta(hours=16 if fixed16 else 96)` read directly in ~/workspace/.scratch-ausar-archive/handoff-20261024; FIDELITY-LEDGER HARDEN batch-1 diff (2026-10-24): "96h deadline for all non-fixed16 policies source-confirmed"; FIDELITY: "source code, not an assumption" (the census's "ASSUMPTION" label is superseded by that diff) | MARKED (header comment in all 4 engine files) |

## Tranche 3 — E3 aster_batch3 _BOOKS (4 counted values × 2 sleeves)

| constant | value | location | route | source pointer | disposition |
|---|---|---|---|---|---|
| hold_sessions | 5 | desk3/aster_batch3.py _BOOKS (all RSI2/VWAP20 books) | 1/2 | Header: FAITHFUL PORT of archive source/backend/r19_options.py, books in source/strategies/r19/options_rules.json, TSV rows 26-35 | MARKED (block comment above _BOOKS) |
| debit caps (max_debit_width / max_premium_spot) | 0.6/0.45, 0.025/0.015 (LEAPS 0.5) | same | 1/2 | same | MARKED (same block) |

## Tranche 4 — E3 sleeves (104 counted values excl. saty_sol's 8)

| sleeve/file | constants | route | source pointer | disposition |
|---|---|---|---|---|
| sleeves/bb_rsi_divergence.py (15) | PIVOT_LEFT 3, PIVOT_RIGHT 3, RSI_ALIGN_RADIUS 1, MIN_PIVOT_GAP 5, MAX_PIVOT_GAP 60, MIN_RSI_DIVERGENCE 2.0, MIN_PRICE_EXTENSION_PCT 0.0, STOP_ATR_BUFFER 0.5, MIN_REWARD_RISK 1.2, MAX_HOLD_BARS 24, RISK_PCT 0.0025, MAX_NOTIONAL_PCT 0.05, MAX_SPREAD_BPS 15.0, QUOTE_MAX_AGE_S 60.0, BAR_MAX_AGE_S 600 | 2 | Header: ported faithfully from Test package v2.2 (dwj9ddyvf6-hub/Test @ 39a200a4), "byte-for-byte in the frozen constants"; X2 values restated in header EXPANSION. BAR_MAX_AGE_S provenance marked only — CR-4 vote unchanged, still open. | MARKED (block comment) |
| sleeves/beatendown.py (6) | CUT_LAM 0.17647058823529413, MAX_POSITIONS 10, HOLD_DAYS 91, SLEEVE_CAP 0.30, COST_BPS_SIDE 0.00255, BEAT_LO52_CUT 0.80 | 1 | Header Selection law restates 91d/30%/10/25.5bp/0.80 verbatim; CUT_LAM carried verbatim in the frozen port, Q_LAM feature arrives via context.extra qualifiers, no in-module consumer (grep-proven). Route 2 for CUT_LAM attempted (ghapi code search incomplete_results, guessed Femto-lean paths absent) — origin rests on the in-file verbatim-port statement. | MARKED (inline ×6) |
| sleeves/confluence.py (6) | CUT_LAM, MAX_POSITIONS 10, HOLD_DAYS 91, SLEEVE_CAP 0.30, COST_BPS_SIDE 0.00255, SELECT_MIN_COUNT 2 | 1 | Header restates all (incl. ">= SELECT_MIN_COUNT (2)") | MARKED (inline ×6) |
| sleeves/milkman_0dte.py (5) | TARGET_DELTA 0.40, MAX_SPREAD 0.20, QUOTE_MAX_AGE_S 180.0, NO_ENTRY_S 1800 (30*60), HARD_EXIT_S 900 (15*60) | 1/2 | Header "Rules as authored" restates all five; desk3/milkman_0dte/PROVENANCE.md:17; vendored source byte-exact (sha256 in header) | MARKED (inline ×5) |
| sleeves/przm_fade_edges.py (4) | EDGE_TOL_FRAC 0.0005, INVALID_FRAC 0.0015, NOTIONAL_PER_FADE 2000.0, MAX_OPEN_FADES 2 | 1 | Docstring Frozen mechanics restates all four (0.05% / 0.15% / $2,000 / max two), labeled recreated under PRZM-RECREATION-SPEC-2026-10-29 (FROZEN) — provenance is the spec recreation, honestly not an extracted original | MARKED (inline ×4) |
| sleeves/przm_zero.py (9) | ENTRY_SCORE 25, FLIP_SCORE 35, DROP_SCORE 8, MIN_HOLD_MS 600000, GRADE_AFTER_MS 1800000, NOTIONAL_PER_CALL 1000.0, CHASING_MULT 0.55, CONTRARIAN_MULT 1.25, CHASING_M5_MIN 0.8 | 1 | PRZM-RECREATION-BUILD.md ll. 29-34 + sleeve docstring ($1,000 notional); GRADE_AFTER_MS derived: 30-min grading = 30*60*1000 | MARKED (inline ×9) |
| sleeves/qullamaggie.py (19) | RISK_FRACTION 0.0035, MAX_NAME_NOTIONAL_PCT 0.20, MAX_ADV_PARTICIPATION 0.01, MAX_POSITIONS 10, LEADER_PCT 0.98, IMPULSE_MIN 0.30, BASE_WINDOW 10, BASE_WIDTH_MAX 0.28, TIGHTENING_MAX 1.0, MA_SUPPORT_MIN 0.70, MA_TOL 0.97, OR_MINUTES 5, MAX_STOP_ATR 1.0, ADV_MIN 5000000, SCALE_DAYS 3, TRAIL_HELD_MIN 3, EXTENSION_ATR 1.5, GAP_QUANTILE 0.95, SLIP_BPS 2.0 | 1 | Header restates every value in prose and records "every constant below cites its source in the old file and is copied exactly" (converged spec S1-S4) | MARKED (block comment) |
| sleeves/qullamaggie_paper.py (1) | BUDGET_USD 100000.0 | 1 | Header VIRTUAL BOOK MAPPING: aurelia_common.BUDGETS; cumulative accept check vs $100,000 in docstring. The $10k-slice authority tension (FULL-AUDIT OPEN row 12) is NOT cured by this mark and stays open. | MARKED (inline, tension named on the mark) |
| sleeves/saty_day.py (8) | SPREAD_GATE 0.05, QUOTE_STALE_S 60.0, BUDGET_PCT 0.04, DAILY_STOP_USD 10000.0, ENTRY_FRESH_S 1800.0, STATION_FRESH_S 600.0, RANGE_LOW_PCT 70.0, RANGE_HIGH_PCT 90.0 | 1 | Census claim STALE on the final tree: every one already carries an inline mark (# desk options convention (bilbo), # D-3, # D-14 (his 3-5% range, worked 4%), # one scan cycle, # two exit sweeps, # port range gauge SPEC 5.1). DAILY_STOP_USD itself was superseded today by DAILY_STOP_FRACTION = 0.01 # Saty family standard (SATY-DAY-STOP-20261116). | ALREADY-MARKED ×8 (no edit) |
| sleeves/saty_magnum.py (12) | SNAP_M3 -100.0, SNAP_M10 -100.0, SNAP_H1 -80.0, QUOTE_STALE_S 60.0, RISK_PCT 0.005, NOTIONAL_CAP 0.25, SESSION_STOP_PCT 0.01, FRESH_S 1800.0, RETEST_WINDOW_S 3600.0, CHOP_CROSSINGS 3, CHOP_BARS 12, OPEN_WAIT_MIN 10 | 1 | 10 already marked (# MAG-B3/# MAG-B4, # desk IEX quote convention, SNAP_M3 # Arm C legs (R26)); SNAP_M10/SNAP_H1 are the same R26 Arm C trio (single joint condition, code ll. 751-753) | ALREADY-MARKED ×10; MARKED ×2 (SNAP_M10, SNAP_H1) |
| sleeves/saty_sol_0dte.py (8) | MAX_ADVERSE_ATR 0.03, SPREAD_GATE 0.05, PREMIUM_FRACTION 0.005, DAILY_LOSS_FRACTION 0.01, QUOTE_STALE_S 60.0, ENTRY_FRESH_S 120.0, MIN_MINUTES_TO_CLOSE 90, LIQ_MINUTES_BEFORE_CLOSE 10 | 1 | Census claim STALE: all 8 already carry inline marks (# his section 9, # paper value, # desk mapping of his freshness budgets, etc.) | ALREADY-MARKED ×8 (no edit) |
| sleeves/tensor_red_dip.py (6) | FEAR_QQQ_PCT -1.5, RISK_FRACTION 0.0025, STOP_LOSS_PCT 0.08, STRENGTH_TARGET_PCT 0.03, HOLD_DAYS 3, MAX_POSITIONS 5 | 1 | Header Strategy paragraph restates all six; verbatim port from old desk tensor_red_dip_sleeve.py | MARKED (block comment) |
| sleeves/tensor_swing.py (1) | EXIT_TIME_STOP_BARS 20 | 1 | Already marked: "# old desk EXIT_TIME_STOP_BARS: the study's edge horizon" + M-TS1 cure note | ALREADY-MARKED (no edit) |

## Tranche 5 — E2 (18)

| constant | value | location | route | source pointer | disposition |
|---|---|---|---|---|---|
| selected_weight / qqq_add_weight | 0.25 / 0.75 | sleeves/free_etf.py (CORE25 book branch) | 1/derived | Policy name CORE25 = 25% selected; QQQ 0.75 = 1 − 0.25 complement | MARKED (inline) |
| ma_lookback_bars | 252 | sleeves/free_etf.py score_map | 3/derived | 252 sessions = one trading year, the standard annual lookback; code states "252 are required" | MARKED (inline) |
| vol_window_bars | 127 | sleeves/free_etf.py vol_normalized_score | derived | Already derived in the function's own docstring: 126-session log return needs the last 127 closes (126 returns + 1) | ALREADY-DERIVED in docstring (no edit; counted resolved) |
| crowded_percentile (ada) | 0.75 | sleeves/free_kraken_ada_crowded.py:173 | 1 | Header: "funding above zero and the 90-day 75th percentile" | MARKED (inline) |
| crowded_percentile (link) | 0.75 | desk3/strategies/free_kraken_link_crowded.py:177 | 1 | Same header rule | MARKED (inline) |
| stop (s_mn_hourly_1w) | 0.15 | desk3/lazarus_midna.py SPECS | 1 | Lazarus catalog 15% stop (header cites catalog 4.2 sketches; cf. Q07 SS4.1 "15% stop" family rule) | MARKED (inline) |
| band_low / band_high | 10.0 / 20.0 | desk3/lazarus_midna.py gate "band" | 1 PARTIAL: header cites "catalog 4.2 rule sketches" but no record read states the $10–$20 band. 2: catalog unreachable (the desk-research, V3-SCOPE 3.4). 3: no canonical form (a desk price band). 4: candidate in report. | — | OPEN |
| breadth_min | 0.50 | desk3/lazarus_midna.py gate "breadth" | same 4 routes; candidate: majority breadth (>50% advancing) | — | OPEN |
| vix_low / vix_high | 12.0 / 25.0 | desk3/lazarus_midna.py gate "vix_mid" | same 4 routes; candidate: mid-VIX regime band | — | OPEN |
| smh_calm_window / smh_calm_max_move | 21 / 0.05 | desk3/lazarus_midna.py gate "smh_calm" | same 4 routes; candidates: 21 sessions ≈ one trading month; 5% calm-move bound | — | OPEN |
| MAX_FIRE_AGE_DAYS (kronos) | 7 | sleeves/s_mn_kronos.py | 1: header catalog §4.2 restates holds/budget, not the age bound. 2: upstream fire producer unreachable. 3: n/a. 4: candidate in report (one-week freshness for a 1D fire). | — | OPEN |
| MAX_FIRE_AGE_DAYS (moonshot) | 7 | sleeves/s_mn_moonshot.py | same | — | OPEN |
| fire_age_days | 10 | desk3/lazarus_midna.py:176 (literal `age_d > 10`) | same 4 routes; candidate in report. NOTE: engines disagree (7 vs 10 days for the same fire-freshness concept) — named inconsistency for the coordinator. | — | OPEN |
| MAX_SPREAD_FRAC (laz8_opt) | 0.30 | sleeves/laz8_opt.py:14 | 1: docstring restates "spread <= 30% of mid" (a restatement, not a source); aster_batch3.py:170 cites laz8_opt as "desk precedent" — a circular precedent chain, not a source. 2/3: no external source found. 4: candidate in report. | — | OPEN |

## Excluded

| constant set | disposition |
|---|---|
| saty_sol's 8 unmarked (E3) | EXCLUDED per task: pinned file sleeves/saty_sol.py, sha256 36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc verified unchanged, not in this lane's diff. (Observation only: the file's constants in fact carry inline marks of the same form as saty_sol_0dte's.) |

## Counts

- In-scope instance-rows: 476 of 484 census rows (8 saty_sol excluded).
- Resolved: 138 of 476 instance-rows (FEE 20 + 96h 7 + E3 104 + E2 7).
- OPEN: 338 of 476 instance-rows = bp_buffer 327 instances (1 distinct constant) + E2 11 distinct constants.
- Unreached: 0 — every tranche row above was examined; E4 contributes no distinct constant beyond bp_buffer.
- Derived candidates (route 4, report only, no value changed): bp_buffer_frac 0.02; band 10/20; breadth 0.50; vix 12/25; smh 21/0.05; MAX_FIRE_AGE_DAYS 7; fire_age 10; laz8 MAX_SPREAD_FRAC 0.30.

## Addendum — CONSTANTS-DERIVATIONS-20261116 closure (added 2026-11-16, full sleeve audit Lane B Job 5)

The Counts section above is the pre-derivations snapshot and is
superseded on this point: the route-4 derivations it listed as
candidates were landed in-file by CONSTANTS-DERIVATIONS-20261116
(DERIVED marks at desk3/dispatcher.py:546-556 for bp_buffer_frac
0.02; desk3/lazarus_midna.py for the band/breadth/vix/smh/fire-age
set; sleeves/s_mn_kronos.py:24 and sleeves/s_mn_moonshot.py:21
for MAX_FIRE_AGE_DAYS 7; sleeves/laz8_opt.py:14 for
MAX_SPREAD_FRAC 0.30), and the eight port byte-pinned files carry
their provenance in this ledger's rows after commit ad95ab1
removed their in-file marks to restore the byte pins. Counted
result (BUGLOG_2026-11-16, CONSTANTS-DERIVATIONS-20261116):
476 of 476 in-scope instance-rows carry provenance, OPEN 0; no
numeric literal changed. Pinned by
tests/test_constants_provenance_20261116_blockers.py (6 passed,
re-verified on the final tree by the full sleeve audit).
Named remainder: the fire-age 7 vs 10 inconsistency is marked on
all three sites and deliberately NOT harmonized; harmonization
is a behavior change and an owner design ruling.
