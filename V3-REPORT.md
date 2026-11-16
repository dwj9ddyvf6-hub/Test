# V3-REPORT — muse-desk-v3 final report (2026-10-24)

## Verdict: PARTIAL

**Open rows at the top, by name — nothing below overrides this list:**

1. **A9 — live paper fill read-back: OPEN.** No supervised regular-trading-hours
   (RTH) dispatch session has run yet (this build finished on a Saturday).
   The root cause that made a fill impossible is cured (real SIP warm bars,
   per-key fed marking, dispatch-mode positions read-back — see Cure round 3),
   and evaluate-only cycles on warm bars emit real intents that fill against
   the test broker (5/cycle, 0 errors). The remaining proof is the first
   paper fill read back from the Alpaca paper broker in the supervised
   session on **Mon 2026-10-26 RTH**, with `--dispatch` re-enabled for that
   session only. The runner is deliberately evaluate-only over the weekend.
2. **Final verify `passed=false`.** The last independent verify phase did
   not return a pass, so under InfinityBlade (no GREEN without outcome-level
   evidence from the final system, and no GREEN while any acceptance row is
   open) the program cannot be called GREEN — even though the evidence
   re-run independently on the final pre-report tree is strong: regression
   suite **337/337 GREEN** on tree `621406de`, **337/337 GREEN** in the
   mirror-restored clone, capacity-400 spot re-run **400 ok in 6.02s**, and
   fault/restart re-run **5/5 PASS**. A9 alone also blocks GREEN.
3. **115 sleeves UNFED by name** (of 156: 18 FED, 115 UNFED, 23 parked).
   Their declared non-bars inputs — options, kraken, tensor, fires, quotes,
   earnings, and others — have no producer yet. Each is named, with its
   missing inputs, in `state/health.json` and in the terminal roll every
   cycle. They are excluded and named, never silently abstaining.
4. **Lazarus real-fire ingest unexercised.** The `the desk-research` tree is
   unreachable from this box (probed, V3-SCOPE §3.4). All Lazarus lanes are
   fire-consumers that fail closed until a real pushed fire snapshot arrives
   through the ingest contract. Fixture-fire proof is complete; live-fire
   proof is not claimed.
5. **Named fidelity risks that stay open:** `s_rules_1d` / `s_rules_1w`
   (the 43 frozen rules are not enumerated in any source in hand — pure
   fire-consumer freeze); `s_1wsw_stress` ("no live source yet" upstream,
   parked); `s_q07w_s78_ml_deep70_wcov` (a possible 6-slot / $6,563
   exception in the catalog was not adopted — standard 1 slot / $1,000 used,
   risk recorded in FIDELITY-LEDGER LAZ-B5); `s_mn_moonshot` and
   `s_mn_kronos` (upstream pick/model unreachable — UNVERIFIED against real
   upstream fires); the 6 waiting-list placeholders, the 2 Q07 index rows,
   and `legacy_exit` (excluded from the roster by design — they re-enter
   only on an owner/research-lane spec).
6. **`saty_gpt_v02` hardware floor.** Its single-core re-derivation is now
   the entire pool wall (see Efficiency). The next repair (cross-cycle
   memoisation of its resampled series) would change strategy-layer
   inputs and needs its own owner ruling — named, not done silently.
7. **Carried external blocks:** ENJ/USD is unlisted at Alpaca (ENJ sleeves
   fail closed, no substitute); no DigitalOcean component was found in the
   searched corpus (recorded as not-found, never invented).

Everything else in the acceptance matrix below is proven on the final tree.

---

## What was built — in plain language

A brand-new, self-contained paper-trading desk in `~/workspace/muse-desk-v3`
(its own git repo, standard-library-only posture). It replaces the shape
that failed in v2 — one slow subprocess per strategy, every strategy
re-reading the same market data on its own — with:

- **One shared snapshot per cycle.** Producers gather market data once
  (bars, quotes, options, Kraken, Tensor bundle, earnings, account) and
  freeze it into a single immutable, content-hashed snapshot. Every
  strategy in that cycle sees exactly the same data; a corrupted snapshot
  fails the cycle closed before any order.
- **A persistent worker pool.** Long-lived workers (one per CPU, 2 here)
  evaluate strategies in parallel with a hard per-strategy timeout. A
  wedged or crashed strategy is marked, its worker is killed and respawned,
  and the cycle completes anyway. Cost-aware scheduling (EFF-1) puts the
  slowest known strategies first so nothing stacks behind them.
- **A producer registry that refuses to stay silent.** Every strategy
  declares the inputs it needs. If an input was not produced or is stale,
  the strategy is **UNFED** — excluded from dispatch and named in the
  terminal and its journal, never quietly doing nothing.
- **One dispatcher to one paper door.** A single writer checks each
  strategy's slice of buying power at intent time, stamps every order
  `v3-<sleeve>-<intent_id>`, and counts a fill **only** when it is read
  back from the broker — never from a submit acknowledgement. Duplicate
  intents cannot resubmit. The door enforces the Alpaca **paper** URL and
  refuses `ALPACA_ENV=live` at startup; a gate-wired scan proves no
  real-money endpoint string exists in the tree.
- **Per-sleeve journals and reconcile.** Append-only journals per sleeve
  plus one dispatcher journal; no global ledger re-read on the hot path.
  Every dispatch cycle reconciles journal-derived positions/cash against
  broker read-back; a named discrepancy halts new entries for the affected
  sleeve only (exits still pass; a cash discrepancy halts entries desk-wide).
- **A scheduler that survives restarts.** Next-fire times and consumed-bar
  cursors are persisted, so a restart never re-fires a consumed bar and
  never duplicates an order.
- **A plain-language terminal.** Each cycle writes `state/terminal_feed.json`
  (and the static page in `terminal/`) with, per strategy: Ready / Waiting
  for data / Paused / Needs attention, money assigned, open positions, last
  action, and a session summary — with `generated_at` and `cycle_id` so
  freshness is provable by read-back.
- **A shadow research lane.** New ideas live in `candidates/`, get a frozen
  market view and can only emit signals stamped `can_be_ordered=False`.
  Reaching for an order path raises an error and is journaled. Promotion
  requires a registry flip **plus** a separate manual roster edit and commit.
- **Real warm bars (Cure round 3).** `desk3/warm.py` fetches Alpaca SIP
  1Day + 1Hour bars, paginated, for the 155-symbol union (155/155 landed;
  SPY 345 daily + 352 hourly bars in the proof run), cached in
  `state/warm_bars.json`. Fed marking is per-key: only keys a producer
  actually returned count as produced.

The Tensor **engine** was never touched anywhere — v3 only consumes its
bundle/fires, exactly as v2 did. muse-desk-v2 and all femto-lean trees were
read-only reference throughout.

## The roster — 156 genuine sleeves

Counted in `config/sleeves.json` on the final tree: **156 rows, 133 active,
23 parked** (parked = source-off set, named in config and in every cycle roll).

| Family | Count | Notes |
|---|---|---|
| Ported from muse-desk-v2 | 71 | IDs exact vs v2 @ `3593668`; slices/cadences/sessions carried verbatim (incl. morning_dip $20k, po10_qqq $100k) |
| Lazarus — Q07 lanes | 49 | Cyan/Green/Swing; source-off Swing lanes parked |
| Lazarus — Midna `s_mn_*` (genuinely new) | 18 | Includes the 5 batch-9 Tensor lanes and options expressions |
| Lazarus — direct Tensor / desk / lab / inventory books | 16 | 1h, 1d, 1w, 1dc, 1wa, s_1dg, s_1dgp5, s_1wlab, s_1wsw, s_1wc_micro, s_1wc_ml, s_rules_1d, s_rules_1w, s_1wg_small (parked), s_moonshot (parked), s_1wsw_stress (parked) |
| Lazarus — ChartsLector | 2 | s_cl_qm_small, s_cl_vmr_qqq |
| **Total genuine** | **156** | 71 + 85 (Lazarus: 49 + 18 + 16 + 2 = 85) |

The binding derivation is
V3-SCOPE §3.2: 100 CSV rows − 1 `legacy_exit` stub − 2 Q07 index rows
− 6 waiting-list placeholders − 6 duplicate-strategy counterparts
= **85 genuinely new**, + 71 v2 = **156**. No inflated, empty, or duplicate
sleeves are in the roster (acceptance A3); the 6 duplicates exist only as
lineage aliases in the ledger.

**Fidelity ledger summary (`FIDELITY-LEDGER.md`):** one row per Lazarus
sleeve across batches 1–9. Every catalog-specified field (entry, exit, hold,
slots, budget, stop) is implemented and fixture-proven. Where a source was
thin, the reading adopted is written down in the ledger — e.g. Q07 filter
definitions (deep70 = ≥30% drawdown / ≤70% of trailing high, cheap5 = <$5,
ins2 = ≥2 insider buys, mom6 = positive 126-session return, wcov/wlow =
Wikipedia tags), the 1h exit plan, the 1d trail reading, and every
fire-source substitution for the unreachable the desk-research files.
Overall Lazarus fidelity verdict in the ledger: **PARTIAL** — faithful to
every specified field; the documented readings are not source-verified, and
the fire-consumer lanes are unverified against real upstream fires.
The 71 v2 ports are byte-identical strategy copies (sha256-pinned in their
blocker tests; saty_sol byte-identical included), with fixture intent/exit/
refusal parity against v2 oracles.

## Best Setups — preservation proof

- **Vendored byte-identical, never modified:** 8 files from femto-lean
  @ `2febc46` into `best_setups/` (5 core modules + 3 tools), sha256-pinned
  in `BEST-SETUPS-PRESERVATION.md` and by a gate-wired blocker that fails
  on any byte drift.
- **Behavioural identity (golden proof):** on the original system's recorded
  inputs, the vendored copy's output is **byte-identical** to the original
  tree's output (golden sha256 `0081d53a…bac1`; compose_call ×11 briefs,
  curator geometry, full publish merge).
- **Live in v3:** every cycle merges the latest setups doc through the
  vendored merge into both terminal surfaces, labelled `setups_source`.
  Generation from v3 state is cured (CURE3-2, `desk3/setups_generate.py`):
  a live doc was generated from v3 journals on 2026-10-24 (0 setups on an
  as-yet empty v3 ledger; market regime Downtrend from real SPY/QQQ SIP
  bars). Vendored pins re-verified by the gate after every cure round.

## Efficiency — before / after (acceptance A12, identical measurement)

Same 71 v2 sleeves, same real cache (242,641 bars, read read-only), same
as-of `2026-10-23T19:00:00Z`, FakeBroker on both sides. Full detail:
`EFFICIENCY-REPORT.md`.

| Stage | v2 (before) | v3 (after EFF-1) |
|---|---|---|
| Full-roster cycle wall (71) | **85.26s** | **34.61s (2.46×)** |
| saty_gpt_v02 alone | 44.75s (52% of cycle) | 31.76s (= 100% of pool wall) |
| Spawn + imports per cycle | ~9.6s (71 subprocesses) | ~0 (persistent workers) |
| Market-data reads per cycle | 71 per-sleeve cache re-parses | 1 parent read → 1 hashed snapshot |
| Result quality | 70 ok / 1 error (iron_condor) | 71 ok / 0 errors |

The dominant v2 constraints — sequential subprocess-per-sleeve and repeated
cache parsing — were removed structurally, not hidden. What remains is
saty_gpt_v02's own single-core cost (open item 6 above).

## Capacity, fault, and restart results

Detail: `SCALE-FAULT-REPORT.md`, plus the independent re-runs on the final
pre-report tree noted in the verdict section.

| Proof | Result |
|---|---|
| Full roster, simulated day (3 cycles) | 27.75s total; per cycle 131 ok / 2 harness-shape errors (both since cured — harness re-run 133/133 ok) / 0 UNFED / 0 wedged; 156 accounted (133 evaluated + 23 parked named) |
| Capacity 400 (A6, as corrected) | 133 genuine active + 267 SYNTHETIC = 400 slots in **8.43s**; synthetic intents suppressed 267, synthetic dispatched **0**. Spot re-run on final tree: **400 ok in 6.02s** |
| Capacity 800 (A7, SYNTHETIC) | 800 slots in **9.67s**; 0 wedged/timeouts; suppressed 667; peak RSS ~141MB. Labelled SYNTHETIC everywhere — capacity proof, never production-load evidence |
| Fault a — worker killed mid-cycle | PASS — cycle completes, sleeve marked wedged, next cycle recovers |
| Fault b — corrupt snapshot | PASS — cycle fails closed, 0 dispatched, 0 phantom intents |
| Fault c — broker door down | PASS — intent queued, 0 phantom fills; after recovery, filled exactly once from read-back |
| Fault d — desk killed mid-session, restart | PASS — 0 duplicate orders (idempotency + client-order-id), scheduler re-fires nothing |
| Fault/restart re-run (final tree) | **5/5 PASS** |
| Order lifecycle (FakeBroker) | Equities, options multi-leg, crypto fractional, Kraken-style pair: entry → fill → manage → exit → flat, all from read-back |

## Deployment posture

- **Operating desk:** v3. Runner live in **evaluate-only** mode over the
  weekend (pid recorded in `state/runner.json`; at last read-back cycle 15,
  mode evaluate-only, last_status ok, dispatched 5/cycle against the test
  broker, 0 errors) — no paper orders are placed from stale Friday bars.
  Dispatch is re-enabled only for the supervised Mon 2026-10-26 RTH session
  (that session is the A9 proof, open item 1).
- **Paper only:** Alpaca paper door, v2's credentials route (key file +
  Secure Vault surrogate, held only in the door process). Live env refused.
- **v2:** untouched and intact, kept as reference/rollback. Under the Monday
  collision rule, v2's Monday smoke jobs should be stood down by the parent
  now that v3 is the operating desk — that action is the parent's, not taken
  by this report.
- **Operations:** `OPERATIONS.md` (run / stop / recover / save / reconcile).

## GitHub locations

- **Source mirror:** GitHub repo `dwj9ddyvf6-hub/Silicon`, branch
  **`muse-desk-v3`** (SHA-preserving Git-Data mirror; restorability route
  registered in `~/workspace/backup/restorability_check.py`).
- **State mirror:** same repo, branch **`muse-desk-v3-state`**
  (`state_snapshot.tar.gz` + `manifest.json`, per-file sha256).
- **Pre-report tested head:** `621406de6f57648a49b5e677a279e019d57dadba`
  (suite 337/337 there, and 337/337 in the mirror-restored clone).
- **Final head:** this report is committed on top of `621406de` as a
  doc-only commit; the mirror was refreshed after that commit and read back
  — remote branch head == local HEAD at the final head printed in the
  commit/mirror summary accompanying this report. Any post-test change
  beyond this doc-only commit would invalidate that statement.

## Acceptance matrix — verdict per row (V3-SCOPE §8)

| # | Row | Verdict | Evidence (short) |
|---|---|---|---|
| A1 | Independence | PASS | Isolated-tree end-to-end blocker (tree copied with no v2/femto sibling; cycle GREEN there), gate-wired (CURE2-5) |
| A2 | Roster fidelity (156) | PASS | Config count 156 = 71 v2 IDs exact + 85 Lazarus per §3.2; parked set = source-off set (23), named |
| A3 | No inflated sleeves | PASS | None of legacy_exit / 2 Q07 index / 6 waiting-list / 6 duplicates in config; duplicates are ledger aliases only |
| A4 | Port fidelity (v2 71) | PASS | Byte-identical strategies (sha256-pinned, saty_sol included); fixture entry/exit/refusal parity vs v2 oracles in every port batch |
| A5 | Port fidelity (Lazarus 85) | PARTIAL | Ledger complete for all 85, every lane fixture-drives on recorded fires; fidelity readings documented, not source-verified; live fires unexercised (open items 4–5) |
| A6 | Capacity — design (400) | PASS | Proven composition: 133 genuine evaluated + 267 SYNTHETIC, 23 parked named not evaluated; 8.43s, spot re-run 400 ok in 6.02s, inside the 60s fastest cadence |
| A7 | Capacity — synthetic (800) | PASS (SYNTHETIC) | 800 slots in 9.67s, 0 wedged; labelled SYNTHETIC in every report |
| A8 | Best Setups identity | PASS | 8/8 sha256 pins + gate blocker; golden output byte-identical; generation from v3 state cured and run live (CURE3-2); merged into both live terminal surfaces |
| A9 | Autonomy within paper scope | **OPEN** | Warm-bars root cause cured; evaluate-only cycles dispatch intents on real bars; the RTH paper fill read-back requires the supervised Mon 2026-10-26 session — a Saturday cannot prove it |
| A10 | Paper-only enforcement | PASS | Door + Desk refuse `ALPACA_ENV=live` (blocker-proven); gate-wired scan: no real-money endpoint string in tree |
| A11 | Research-lane isolation | PASS | No code path reads the desk-research or executes research code; ingest validates schema + hash, fails closed on stale/absent/malformed (all four tested); shadow lane cannot reach an order path |
| A12 | Efficiency before/after | PASS | Identical re-run: 85.26s → 34.61s (2.46×), attribution in EFFICIENCY-REPORT.md |
| A13 | Fault proof | PASS | Worker-kill and corrupt-snapshot faults PASS; re-run 5/5 with the restart set |
| A14 | Restart proof | PASS | Kill/restart: state rebuilt, 0 duplicate orders, no lost fills, scheduler no-refire |
| A15 | Reconcile proof | PASS | desk3/reconcile.py; planted +5 QQQ detected, named, halts entries for the affected sleeve only; live baseline recorded |
| A16 | Backups + restore | PASS | Source restored from the mirror branch and state from the state branch (228/228 state files sha-verified in cure-2 drill); restored clone suite 337/337 on the final pre-report tree |
| A17 | Terminal freshness | PASS | Feed carries snapshot hash + generated_at + cycle_id; freshness proven by read-back across cycles; health roll names stale/UNFED producers and sleeves |
| A18 | GitHub save | PASS | Final tree committed and mirrored; remote head read back == local HEAD (see GitHub locations; doc-only final commit) |
| A19 | Blockers + BUGLOG | PASS | Every defect ships a gate-wired blocker with fail direction proven + a BUGLOG_2026-10-24.md entry; gate 337/337 GREEN on the final pre-report tree in the default environment (CURE3-3) |
| A20 | Baseline defect disposition | PASS | iron_condor float(tuple) baseline error does **not** reproduce on the v3 port (71/71 ok on identical cache/as-of); dispositioned in EFFICIENCY-REPORT §5, not silently inherited |

**Coverage ledger:** proven on the final tree — roster, ports (fixture
level), capacity 400/800, faults, restart, reconcile, efficiency, Best
Setups identity + generation, restore, gate. Not proven — A9's live RTH
paper fill (open item 1) and live Lazarus fire ingest (open item 4).
Excluded by design — the 9 non-roster rows in A3. Unavailable — the
the desk-research tree and the upstream Midna/Kronos models from this box.

## Remaining open items — by name (complete list)

A9 live paper fill (Mon 2026-10-26 RTH) · final verify `passed=false`
(program stays PARTIAL until a verify passes on the final tree with A9
closed) · 115 UNFED sleeves pending non-bars producers (options, kraken,
tensor, fires, quotes, earnings — per-sleeve names in `state/health.json`)
· Lazarus live-fire ingest unexercised (the desk-research unreachable) ·
s_rules_1d / s_rules_1w 43-rule freeze · s_1wsw_stress no live source ·
s_q07w_s78_ml_deep70_wcov slot-exception risk · s_mn_moonshot / s_mn_kronos
unverified against real fires · 6 waiting-list + 2 Q07 index + legacy_exit
awaiting a spec · saty_gpt_v02 strategy-layer memoisation needs an owner
ruling · ENJ/USD unlisted at Alpaca · v2 Monday smoke stand-down is the
parent's action under the collision rule.

— End of report. Supporting reports: V3-SCOPE.md, FIDELITY-LEDGER.md,
BEST-SETUPS-PRESERVATION.md, EFFICIENCY-REPORT.md, SCALE-FAULT-REPORT.md,
DEPLOY-REPORT.md, OPERATIONS.md, BUGLOG_2026-10-24.md, PROGRESS.md.

---

## STATUS AMENDMENT — 2026-10-26 (A9-DOCS-20261026)

**A9 is CLOSED** (open item 1 above, and the A9 row of the acceptance
table). The live RTH paper fill read-back was proven on Monday
2026-10-26: `state/a9_first_fill.json`, verdict **FILLED_READ_BACK**,
recorded 2026-10-26T15:39:25Z — sleeve `aster_etf_leader1_m150`,
symbol ALAB, sell 45 @ 263.8, broker status `filled`,
client_order_id `v3-aster_etf_leader1_m150-aster_etf_leader1_m150-20261026T151808-4`.
The report above was written Sat 2026-10-24, when A9 was genuinely
OPEN, and its narrative is unchanged; this amendment records the
state change and its date.
