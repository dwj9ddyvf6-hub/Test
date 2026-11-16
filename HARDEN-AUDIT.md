# HARDEN-AUDIT — muse-desk-v3 full audit + logic census (2026-10-24)

Verdict: **PARTIAL** — census complete (311/311, coverage ledger in
HARDEN-CENSUS.md); gate re-run on this tree in this phase:
**674/674 GREEN (74.3s)**. No new G2/G3/G5/G6/G8/G9/G10 sleeve-logic
gap was proven. The open items are dominated by ONE structural class
(G4 unproduced inputs, 250 sleeves) plus named singles below. No
GREEN is claimed for any row whose proof is a fixture while its live
proof is still Monday's (A9).

## 1. Census summary (HARDEN-CENSUS.md, one row per sleeve)

- Searched: all 311 ids in config/sleeves.json (71 v2 + 85 Lazarus +
  155 Aster; 288 active / 23 parked). Excluded: none. Unavailable:
  Aster archive source for 30 TSV-spec sleeves (B6/B10/B13, fidelity
  PARTIAL) and aster_saty_research's source (absent). Pagination: n/a.
- Method per sleeve: entry + exit fixture drives in gate-wired
  blockers; Aster runtime-trace census (CURE3-1: entry_missing=0,
  exit_missing=6 = the blocker-asserted ETF buy-hold never-exit
  exemption family, by design, NOT a gap); base-156 harness 133/133;
  v2 LOGIC-GAP-REPORT dispositions carried for the base roster.
- Cross-check that closes: live FED-able sleeves = 18 base (bars-only,
  health.json) + 20 Aster (inputs ⊆ {bars, positions}) = 38 =
  roster-day evaluated-ok count. UNFED = 311 − 38 − 23 parked = 250 =
  roster-day UNFED count. Two independent routes, same numbers.
- Sizing/accounting: every row carries a positive slice; dispatcher
  enforces per-slice intent-time buying power; models.validate_intent
  rejects qty<=0, non-whole qty on non-fractional symbols, missing/
  non-positive limit price, non-positive stop (desk3/models.py:23-44)
  — no dispatcher-reject-by-construction found in fixture drives, and
  malformed intents are rejectable-by-validation, never by accident.
- State: per-sleeve append-only journals + dispatcher idempotency
  (seen intent ids + broker client-order-id dedup) — restart-safe.

## 2. Gap rows by class (G1–G10)

| class | count | items |
|---|---|---|
| G1 never-fires | 1 (+1 dual) | raschke_rre: `_EVENT_GATES=(False,False)` trap-pinned (sleeves/raschke_rre.py:141), no producer/config can alter it — construction trace, carried from v2 RULING #13. Cure needs an owner ruling naming a point-in-time event-calendar feed; NOT cured in-pass (hard rail: strategy definition). aster_saty_research dual-classed G1/G4 (shell only, source absent). |
| G2 dead/missing exit | 0 proven | All fixture-driven sleeves fire a designed exit; 6 ETF buy-hold are blocker-asserted exemptions. |
| G3 wrong-quantity/shape feed | 0 new | v2 cures carried; no new instance proven. |
| G4 unproduced input | 250 sleeves | Non-bars producers unwired: funding (46 Aster), quotes (37+), tensor/tensor_fires/tensor_daily20 (26+), options/options_chain (30+), lazarus_fires (16 base), kraken family, earnings/earnings_events, session_fills, timing_signals, xsp_state, bars_secondary, saty_setups, vix/bars_1day lanes. Every one is UNFED BY NAME in health/registry — visible starvation, not hidden abstention — but the producers do not exist yet: OPEN, cure = wire producers per input family (later harden phase / desk-ops). |
| G5 state plumbing | 2 platform items | (i) state/runner.json still reports roster=156 (live read this phase: cycle 69, pid 26973) while config is 311 — stale field, H19. (ii) state/health.json covers only the base 156 ids; the 155 Aster sleeves have no per-sleeve live health row (roster-day aggregate only). Both OPEN, cure at the runner/registry source. |
| G6 translation drops | 0 new | — |
| G7 provider-blocked | 0 new | Lazarus/Aster fire lanes fail closed (the desk-research unreachable from this box) — counted inside G4, never fake-fed. |
| G8 fail-open guard | 0 new | Guards read fail-closed in drives. |
| G9 exit incoherent w/ thesis | 0 proven | No fixture-proven instance; unproven suspicions are not recorded as gaps. |
| G10 profit exit missing | 0 proven | Every non-exempt sleeve's exit drive fires its designed exit (target/mean-reversion/scheduled/risk as designed per source). |

Fidelity (not a logic class): 30 TSV-spec Aster sleeves (B6/B10/B13)
remain PARTIAL-fidelity until diffed against r19_* archive sources.

## 3. Platform findings

- Processes/supervision: ONE detached runner (pid 26973 verified via
  /proc cmdline this phase, evaluate-only, cycle 69 ok, log
  advancing). No cron/scheduled job touches v3 (OPERATIONS.md model);
  state/scheduler.json absent — scheduler state lives in the runner,
  named here so nobody hunts for the file.
- Producers: bars producer REAL (desk3/warm.py SIP warm, per-key fed
  marking, CURE3-1); all other producer families absent = §2 G4.
- Dispatcher/journal: single writer, idempotent, fills only from
  broker read-back; dispatcher.jsonl consistent (evaluate-only fills
  vs FakeBroker observed in CURE3).
- Terminal: terminal_feed.json fresh (generated_at advancing with
  cycle_id) BUT its strategy roll still reflects the base 156
  (ASTER-ADOPT §5.5) — OPEN with G5(ii).
- Backup: Silicon branches muse-desk-v3 + muse-desk-v3-state,
  restorability route registered; restore drill GREEN in DEPLOY
  (restored tree 328/328 at drill time). Mirror of the Aster-adoption
  head read back equal (c4f4ee6/3286653 chain). This phase's commits
  require a fresh mirror pass — named OPEN for the phase tail.
- Security: paper-only enforced in the door (paper-api host pinned,
  ALPACA_ENV=live refused); secrets scan of repo (py/json/md) this
  phase: no credential-shaped strings found; credentials live only
  in the door process via the vault surrogate route. saty_sol
  byte-pin VERIFIED this phase: sha256 36e306c6…bdc == charter pin.
  Best Setups: gate GREEN includes its pin blockers (tree untouched).

## 4. Prior-failure-class checklist

| class | v3 defense | verdict |
|---|---|---|
| Wedged evaluation passes | Isolated worker pool + per-sleeve timeouts; scale-fault blockers; roster-day 0 wedged ×3 cycles | DEFENDED (fixture/roster-day evidence) |
| Sleeves starved of inputs | UNFED-by-name registry/health, excluded from dispatch, never fake-fed | Defense WORKS; underlying gap OPEN (G4, 250) |
| Zero-price/stop intents | validate_intent positive-price/stop/qty rules + dispatcher reject journaling | DEFENDED |
| Unprotected open positions | Reconcile (A15) halts entries per affected sleeve; exits pass; sleeve-layer stops fixture-proven | DEFENDED in fixture; live proof rides A9 (Monday) |
| Session/date mislabeling | Snapshots carry generated_at + cycle_id; warm bars are dated SIP bars; setups regime from real dated bars | DEFENDED (no mislabeled surface found) |
| Alert flapping (external watchers) | No external watcher provisioned for v3; retired dead-man not re-created | DEFENDED by absence |
| Gate/runtime walls | Gate owns its TMPDIR (CURE3-3); gate 674 in 74.3s this phase; roster cycle ~8.6s | DEFENDED |
| Workspace save returning empty desk | Registered restorability route + restore drill GREEN from mirror | DEFENDED (drill evidence) |
| Liveness checks matching themselves | OPERATIONS verifies by pid file + /proc + effects (runner.json advancing); re-performed this phase | DEFENDED |
| Delegated reports accepted unverified | This audit re-ran the gate and re-read live state itself; prior handbacks treated as claims | DEFENDED (procedural, applied) |
| Positions adopted without proof | Session-start reconcile baseline records the pre-v3 legacy book explicitly, never attributed to a sleeve | DEFENDED |

## 5. OPEN items (carried, named)

1. G4 producers for 250 UNFED sleeves (per input family, §2).
2. G1 raschke_rre event-gate ruling (owner names the event feed).
3. aster_saty_research source absent (needs v030 source).
4. TSV-spec fidelity diff for 30 Aster sleeves (B6/B10/B13).
5. G5: runner.json roster field 156→311; health.json + terminal roll
   extended to all 311.
6. A9 live RTH paper fill read-back — Monday 2026-10-26's proof.
7. Mirror pass for this phase's commits (tail item).
