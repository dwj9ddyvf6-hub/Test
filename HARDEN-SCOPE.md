# HARDEN-SCOPE — muse-desk-v3 Harden + Enhance program scope contract

Date: 2026-10-24 (Sat, America/New_York). Phase: RE-READ + RESEARCH.
Status of this document: the contract for all later phases of this
program. Verdict for this phase: **PARTIAL by design** — scope,
digest, and research are proven below; every acceptance row is
UNVERIFIED until its phase proves it on the final tree. No row is
GREEN in this document.

Canonical sources re-read IN FULL for this phase (not summaries):
- InfinityBlade doctrine repo `~/workspace/research/infinityblade-doctrine`:
  README.md, AGENTS.md, INSTALL.md, `skills/infinityblade/SKILL.md`,
  and all five references (field-manual.md, lessons-from-the-field.md,
  review-mode.md, examples.md, eval-cases.md). The canonical SKILL
  controls where any digest below differs.
- Edge skill `~/workspace/.scratch-edge-repo`: root Unified Master
  Prompt v3.0 (`Trading_Edge_Unified_Master_Prompt.txt`),
  `v3/skill/SKILL.md` (incl. §2a), all v3 references (foundations,
  mechanisms, validation, sources, frontier-sources, edge-protocol,
  adaptive-control, adaptive-learning, adaptive-sources,
  desk-runtime), and `v3/skill/scripts/edge_mechanics.py`
  (finite_value_of_information / seller_reservation_premium /
  finite_payoff_check — supplied-model checkers only; they estimate
  no probabilities, validate no semantics, authorize no orders).
- Desk state of record at scope time: HEAD `3286653`; roster
  **311 genuine sleeves** (71 v2 + 85 Lazarus + 155 Aster;
  288 active / 23 parked; config/sleeves.json census this phase);
  gate last proven 674 tests GREEN (ASTER-ADOPT-REPORT, final tree
  of that program — re-proven in this program's first audit phase,
  not inherited as proof here); runner evaluate-only, roster field
  in state/runner.json still says 156 (a known stale-state item the
  audit must disposition, row H19).

---

## 1. SCOPE contract

- **Surface (what changes):** inside `~/workspace/muse-desk-v3` ONLY:
  (a) a full bug/logic audit of every sleeve and every desk process,
  with cures at the source for missing/incoherent entries and exits,
  impossible gates, and dead code paths; (b) one Edge-skill pass over
  every sleeve — improve and enhance only; (c) always-on hardening of
  the runtime (pool, snapshot, producers, dispatcher, scheduler,
  journals, reconcile, terminal, runner/watchdog); (d) leanness and
  efficiency work measured on the complete cycle path; (e) the
  research adopts in HARDEN-RESEARCH.md, each landing only as a
  named audit/harden item with its own blocker.
- **Constraints (what stays untouched):**
  - v2 (`~/workspace/muse-desk-v2`) and all femto-lean / old-desk
    trees are READ-ONLY reference. Nothing outside muse-desk-v3 is
    edited by this program.
  - Paper only. The paper door keeps refusing `ALPACA_ENV=live` and
    any non-paper base URL; no real-money endpoint string may enter
    the tree.
  - Tensor ENGINE untouched everywhere. Tensor sleeves are worked
    only at the sleeve layer (inputs, gates, exits, sizing posture
    inside their existing caps).
  - Best Setups vendored tree (`best_setups/`) byte-identical,
    always: source, behavior, outputs, charts. Its 8 sha256 pins
    (BEST-SETUPS-PRESERVATION.md) and its golden-output identity are
    protected invariants, re-verified after the LAST change.
  - `saty_sol` byte-pin preserved (sha256-exact posture carried from
    v2; any audit finding against it is a ruling item, not an edit).
  - No sleeve is killed, parked, unparked, or critiqued for removal
    in this program. Parked stays parked; active stays active.
  - Strategy constants change ONLY where (i) the audit proves a
    logical gap — missing exit, incoherent entry/exit pair,
    impossible gate, unreachable branch — or (ii) the Edge pass
    proves a binding leak with its pre-registered experiment. Each
    such change is recorded per-sleeve (sleeve, constant, old, new,
    evidence) in the phase report and BUGLOG.
  - Verified paths are preserved: one immutable snapshot per cycle,
    one dispatcher / one writer, fills only from broker read-back,
    UNFED-by-name, scheduler restart-no-refire, per-sleeve journals.
    No second source of truth is created to work around the first.
  - Enhancement switches: every applied enhancement ships behind a
    switch whose OFF position restores the pre-change decision rule
    exactly (the v2 Edge program's proven pattern), so the control is
    always runnable against the treatment.
- **Outcome (observable success):** on the final tree — every one of
  the 311 sleeves has a completed audit row and a completed Edge row
  (enhanced, or VERIFY-ONLY with evidence, or a named owner-ruling
  item); zero proven logical gaps remain open without a cure or a
  ruling; the full gate is GREEN after the last change; the desk
  runs always-on through a full simulated roster day and is Monday
  ready (row H23), with the live RTH paper fill read-back (carried
  A9) still named as Monday's proof, never pre-claimed.
- **Proof:** the finite acceptance matrix in §3, row by row, on the
  final artifact, after the last material change. Each cure and each
  enhancement ships (1) a gate-wired regression blocker in
  `tests/test_*_blockers.py` whose fail direction is proven (fails
  on the old code, passes on the new), and (2) a dated BUGLOG entry
  (severity, file, what broke / what leaked, the fix). The gate is
  `run_regression_blockers.sh`; an unwired test is not a blocker.
- **Edges:** Alpaca paper door (orders, SIP bars, options v1beta1);
  Kraken public REST (data only); Yahoo ^VIX price-only (the one
  sanctioned use; Yahoo hourly volume is disqualified desk-wide —
  Alpaca SIP only for volume); Tensor bundle producer; Lazarus /
  Aster fire-ingest contracts (the desk-research unreachable from this
  box — fire lanes fail closed, never fake-fed); GitHub Silicon
  mirror branches `muse-desk-v3` / `muse-desk-v3-state` (the sole
  off-VM store); the terminal/feed surface.

## 2. Operative rules digest (index — canon controls on any drift)

### 2.1 InfinityBlade (canonical SKILL + references)
- Governing rule: **no GREEN without outcome-level evidence from
  the final system state.** States: GREEN / PARTIAL / BLOCKED /
  UNVERIFIED. Never translate "looks correct" or "command exited 0"
  into GREEN.
- SCOPE first (Surface / Constraints / Outcome / Proof / Edges);
  whole-product work becomes a finite acceptance matrix; no GREEN
  while any row is FAIL / BLOCKED / UNVERIFIED; never shrink the
  task to optimize the report.
- Minimum Sufficient Change at the demonstrated source: no change >
  reuse verified path > native capability > repair at source > new
  machinery last. Never strip validation, safety, observability, or
  recovery to shrink a change.
- Seven truth gates: investigate before declaring impossibility;
  prove absence separately from redirection; contradictory evidence
  is a stop signal (reproduce the named route/state, do not defend
  the hypothesis); never generalize from adjacent proof (a unit test
  does not prove the integration); no completion language while rows
  are open; final evidence follows the last change; do not shrink
  the task.
- Route failure ≠ task impossibility: classify the failure
  (implementation / hypothesis / transport / provider / dependency /
  permission / external / missing choice), preserve the exact error,
  revise the hypothesis, try the highest-confidence safe route.
- Anti-spiral: same class of action failing twice without a revised
  hypothesis = stop and reset (known facts / unproven assumptions /
  last evidence / first failed boundary / smallest discriminating
  check / protected state). Every action must reduce uncertainty.
- Efficiency Breakthrough: measure the COMPLETE path, attribute
  stages, rank by contribution, repair the DOMINANT structural
  constraint, re-measure the same complete path. Never buy speed by
  weakening source identity, freshness, authorization, or
  completeness. Bound workers/batches/retries/fan-out to the next
  boundary's capacity; one authoritative writer; single-flight
  coalescing of same-identity in-flight work; label synthetic
  capacity proof separately from authenticated production load.
- Verification layers: static → focused tests → regression
  invariants → integration/runtime → end-to-end at the boundary
  named in SCOPE; at consequential transitions check Visible /
  Durable / Enforced. Any post-test material change invalidates the
  green to the extent it could affect the proof.
- Review order: scope → authority → causality → sufficiency →
  preservation → efficiency → verification → artifact integrity →
  reporting.
- Batch/manifest discipline: bind every item to an explicit source
  identity + idempotency key; reconcile first; preserve non-targets;
  stop the batch at the first mismatch. Comprehensive claims carry
  a coverage ledger: searched / excluded / unavailable / pagination.
- Provenance: pin authoritative inputs by version/identity/hash;
  "latest" is not provenance; local presence is not remote
  durability (verify destination independently, restore-test before
  deleting a source).

### 2.2 Desk law layered on top (owner's standing orders)
- FIX = cured at the source + proven on the final state.
  Containment, fences, workarounds, watch-and-wait are NOT
  resolutions; an uncured problem stays OPEN and named at the top
  of every report until cured or ruled on. A fence may exist while
  the cure is built; every catch by the fence is an open defect
  against whatever produced it.
- Every fix: BUGLOG entry + gate-wired regression blocker with the
  fail direction proven, in the same pass. Blockers in EVERYTHING —
  production modules, automations, and state/data invariants alike.
- Prior handbacks are claims, not proof: verify against the
  repo/tree (sha cat-file, file existence, final state) before
  repeating any delegated result.
- Verify a detached process by its EFFECTS (pid file it wrote
  itself, result files, log growth, remote state) — never by a
  `pgrep -f` pattern the checking command itself matches.
- Checkpoint to HARDEN-PROGRESS.md at every phase boundary, in
  commit-sized steps; workflow agent calls carry the maximum
  timeout; a stopped run's briefs adopt committed trees by path.

### 2.3 Edge skill v3 (the enhancement method)
- Governing question: what scarce information, access, service, or
  risk-bearing capacity do we supply; who values it; why does its
  price leave a surplus; and what stops competition, costs, or
  bad-state losses from consuming it? An indicator, a win rate, a
  story, or a backtest is not an answer.
- **Enhancement law (owner): an enhancement must change trade
  decisions** — which trades are taken, refused, sized, timed, or
  exited — across execution, timing, risk, responsiveness /
  reaction, adaptability, or perception. Logging, stamps, caps
  reporting, and bookkeeping NEVER count as an enhancement.
- Per sleeve, the Edge pass produces an EDGE CONTRACT / decision
  record: payer-or-belief-wedge (transfer), the price-aware
  comparator at a stated time/size/cost, mechanism class
  (information / risk-service / access-constraint / unresolved
  empirical pattern — overlaps named, never double-counted), a
  calculation connecting the leak to net payoff, and a falsifiable
  experiment with a rival explanation and a rejection rule.
- IMPROVE discipline: attribute the baseline's value loss across
  forecasting → selection → entry → exit → execution → sizing →
  portfolio interaction; repair the BINDING leak first; prefer a
  simplification or cost reduction over more machinery; do not
  default to more indicators, more polling, or more trades. Test
  one conceptual change at a time against the frozen baseline
  (control pair: switch OFF = baseline decisions, ON = treatment),
  on the same inputs, with trade-by-trade decision diffs as the
  primary evidence.
- Information claims are conditional on the market: compare a
  price-aware baseline (Z) with the same model augmented by the
  signal (S); posterior odds = prior odds × CONDITIONAL likelihood
  ratio; correlated summaries of one source are one experiment.
  Risk-warehousing claims price the warehouse for THIS portfolio
  (reservation value, bad state, funding/margin path), not "can
  tolerate volatility." `edge_mechanics.py` checks supplied finite
  models only.
- Validation honesty: chronological splits, no leakage, costs and
  fill realism (a displayed price is not a fill; P(fill|state) and
  adverse selection on fills are modeled where the claim needs
  them), evidence stages HYPOTHESIS → RETROSPECTIVE → OUT-OF-SAMPLE
  → FORWARD SIMULATION → LIMITED LIVE. A sleeve whose honest
  verdict is "no further binding leak found" is **VERIFY-ONLY with
  evidence** (the attribution + the experiments run), never a
  forced change and never a critique.
- Adaptive/runtime discipline (desk-runtime / adaptive-control):
  auditable path versioned data → features → candidate → risk
  check → order intent → execution/reconciliation → attribution;
  persist inputs, versions, prices, order ids, fills, costs, and
  REJECTED opportunities; reconcile before restart; hard execution
  deadlines stay independent of any slow review; degrade affected
  capabilities only — uncertain positions never justify blind
  flattening.

## 3. Acceptance matrix — THIS program (all rows UNVERIFIED at scope)

Proof standard for every row: evidence from the final tree after
the last change affecting that row; gate = run_regression_blockers.sh
unless the row names a stronger boundary.

### A. Audit completeness
| Row | Claim | Proof required |
|---|---|---|
| H1 | Every sleeve audited: census ledger covers 311/311 roster ids from config/sleeves.json, each bound to its adapter, engine/source file, config row, and declared inputs; searched/excluded/unavailable recorded | Machine census diff: ledger ids == config ids, 0 missing, 0 extra; coverage ledger in the audit report |
| H2 | Every desk process audited: pool, worker, snapshot, registry/producers (incl. warm), dispatcher, broker door, scheduler, journals, reconcile, terminal, setups lane, research lane, runner + every cron/scheduled job that touches v3 | Process inventory in the audit report, each with a disposition row; no process present in the tree or schedule and absent from the inventory |
| H3 | Audit method is per-sleeve evidence, not sampling: for each sleeve, entry paths, exit paths, gates, sizing, session/flatten rules, and state handling were each read and dispositioned | Per-sleeve audit rows in the audit report; a sleeve with any sub-item unexamined is UNVERIFIED, not passed |

### B. Zero logical gaps
| Row | Claim | Proof required |
|---|---|---|
| H4 | Every position a sleeve can open has at least one reachable designed exit (or a recorded by-design never-exit exemption, e.g. buy-hold, asserted in its blocker) | Fixture drive per sleeve: entry fires, then its designed exit fires on the exit fixture; exemption list named and blocker-asserted |
| H5 | No impossible or incoherent gate remains: no gate that can never pass, never fail, contradicts its exit, or reads an input the sleeve never receives | Gate-by-gate audit disposition + fixture proof for each cured gate (refusal fixtures AND pass fixtures); cured constants recorded per-sleeve per §1 |
| H6 | No dead/unreachable strategy branch and no silent abstention: every branch either reachable by a fixture or removed at the source; every non-trade outcome carries a named reason (UNFED, gate, session, halt-by-design) | Branch census in the audit report; fixture or removal proof per branch; terminal/journal reason read-back on a full-roster cycle |
| H7 | Every cure landed at the source with a gate-wired blocker (fail direction proven) + BUGLOG entry in the same pass | Gate GREEN listing each new blocker; BUGLOG cross-check: every cure id ↔ one blocker file ↔ one log entry |

### C. Edge pass coverage
| Row | Claim | Proof required |
|---|---|---|
| H8 | Every active sleeve has a completed Edge row: ENHANCED (decision-changing, switch-gated) or VERIFY-ONLY (binding-leak attribution + experiments run, no leak found) or a named owner-ruling item; parked sleeves get an audit row and an Edge disposition by name | Edge ledger covers 311/311; counts by disposition sum to the roster; no sleeve absent, none double-counted |
| H9 | Every ENHANCED sleeve demonstrably changes trade decisions: control (switch OFF) vs treatment (ON) on identical fixture inputs produce a trade-by-trade decision diff in at least one of execution / timing / risk / responsiveness / adaptability / perception | Paired fixture diff artifact per enhanced sleeve, replayed on the final tree; a sleeve whose diff is empty is reclassified VERIFY-ONLY |
| H10 | No enhancement weakens a protected invariant: slice/BP checks, flat-by-close rules, 0DTE no-overnight, warmup gates, and halt-by-design rules behave identically except where the enhancement's own record names the change | Regression blockers for the invariants re-run GREEN on the final tree; enhancement records name any intentional decision change |
| H11 | Strategy constants changed only under §1's two proofs (logical gap, or Edge binding leak with experiment), each recorded per-sleeve | Constants-change register in the Edge/audit reports reconciled against `git diff` of sleeve/config files; any unregistered constant change = row FAIL |

### D. Prior-failure-class checklist (each class: present / cured / absent — with evidence)
| Row | Failure class (origin) | Proof required |
|---|---|---|
| H12 | Silent sleeve / silent abstention (v2: sleeves evaluating ~13×/day, UNFED invisible) | Full-roster cycle read-back: every active sleeve evaluated, dispatched, UNFED-by-name, or halted-by-design-by-name; 0 unaccounted |
| H13 | Wedged pass stalls the desk (old desk: 21 watchdog kills, 10 filed ticks in a day) | Fault fixtures on final tree: infinite-loop + crashing sleeve fixtures leave the cycle complete with the other sleeves ok; wedged verdict journaled |
| H14 | Malformed intent emission (Tensor-sleeve price=0.0/stop=0.0 class: 168 dispatcher rejects in a session) | Malformed-intent census on fixture + simulated-day runs = 0 emitted; dispatcher reject fixtures prove any malformed intent is refused, journaled, and counted as a defect against its producer |
| H15 | Fill claimed from submit ACK / duplicate order on retry or restart (dispatcher semantics) | Blockers: fill only from broker read-back; duplicate intent id and restart-replay fixtures submit exactly once (client order id `v3-<sleeve>-<intent_id>`) |
| H16 | Warmup / partial-history emission + corrupt or mixed snapshot observed mid-cycle | Blockers: warmup-gated sleeves refuse on partial history; snapshot hash re-verify fails the cycle closed; all sleeves in a cycle share one snapshot hash (read-back) |
| H17 | Unprotected open position (old desk: 12 of 85 positions unprotected) | Simulated-day read-back: every journal-derived open position carries its designed protection/exit state or a named by-design exemption; reconcile discrepancy fixtures halt entries for the affected sleeve only, exits still pass |
| H18 | Stale state presented as current (premarket-mislabeled closes; stale terminal; runner roster field still says 156 at scope time) | Freshness proof: terminal feed + runner heartbeat carry generated_at/cycle_id and match the live roster/cycle on read-back; the 156-field defect cured at the source or dispositioned as a named open item — never silently left |

### E. Leanness + efficiency metrics
| Row | Claim | Proof required |
|---|---|---|
| H19 | Leanness measured, not asserted: dead code, duplicate engines, and unused config/producer keys inventoried; removals are minimum-sufficient and each is proven absence-separately (source, imports, config, live route) | Leanness report with before/after counts (files, lines, engines per family, config keys) and the removal proof per item; gate GREEN after removals |
| H20 | Efficiency Breakthrough protocol executed on the complete cycle path: stage attribution (warm → snapshot → fed gate → pool evaluation → dispatch → journals/terminal) on the full 311 roster, dominant constraint repaired at the source, SAME path re-measured | Before/after table on identical conditions (same roster, same snapshot corpus); baseline anchors: A12 path 85.26s v2 → 34.61s v3 (71 sleeves, real cache), roster-day 25.78s (311, warm snapshot harness) — new measurements state their corpus and never mix corpora; synthetic load labelled SYNTHETIC |

### F. Always-on readiness
| Row | Claim | Proof required |
|---|---|---|
| H21 | Runner survives restart without duplicate orders, re-fired bars, or lost journals; recovery is the documented relaunch only | Restart drill on the final tree: kill + relaunch mid-sequence; scheduler cursors, dispatcher seen-index, and journals read back continuous; 0 duplicate client order ids |
| H22 | Supervision follows the research adopts (HARDEN-RESEARCH R-ADOPT-1/2): bounded worker restart intensity with a degraded mode, and a watchdog petted only after verified work with effects-based verification | Blockers: restart-storm fixture trips the cap and names the degraded state; watchdog/heartbeat read-back shows last VERIFIED cycle, grace = 2–3× cycle interval; no external dead-man service is provisioned (owner retired it 2026-10-23 — internal supervision only) |
| H23 | Producer/broker failure degrades by bulkhead, not by desk: one failing producer marks only its dependent sleeves UNFED; broker-down queues intents and recovers without a second fill | Fault fixtures on final tree per boundary (bars, options, kraken, tensor, fires, broker): affected set == declared dependents; broker-down → queued → retry fixture ends with exactly one fill |

### G. Best Setups identity + preservation
| Row | Claim | Proof required |
|---|---|---|
| H24 | Best Setups vendored tree byte-identical after the last change of the program, and behaviorally identical on the golden corpus | sha256 re-derivation of all 8 pins == BEST-SETUPS-PRESERVATION.md; golden run byte-identical (cmp clean); blocker GREEN on final tree |
| H25 | All other protected invariants intact on the final tree: saty_sol byte-pin; Tensor engine untouched (no diff in any engine path); paper-only scan (no live endpoint string); v2 and femto-lean trees untouched (HEADs/diffs read back) | Pin/hash read-backs + tree scans in the final report; v2 HEAD still `3593668…` and femto-lean unmodified |

### H. Monday readiness
| Row | Claim | Proof required |
|---|---|---|
| H26 | Full gate GREEN on the final tree after the last change, and the desk completes a full simulated roster day (≥3 cycles, real warm snapshot) with every sleeve accounted (H12) and 0 wedged | Gate output + roster-day artifact on the final commit; counts reconcile to 311 |
| H27 | Monday operating posture is explicit and honest: v3 is the operating desk; runner mode for Monday (supervised RTH `--dispatch`) is the documented OPERATIONS.md procedure; the ONLY remaining live proof is named, not pre-claimed | Final report names carried **A9 — live RTH paper fill read-back (Mon 2026-10-26)** as OPEN until a fill is read back from the Alpaca paper broker; weekend posture stays evaluate-only; legacy 85 old-desk positions remain untouched and unattributed (reconcile baseline) |
| H28 | Save/restore proven for the hardened tree: Silicon mirror read-back == local HEAD and a fresh-clone gate run GREEN there | Mirror summary + clone gate output recorded in the final report (route failure on the mirror is reported as such, never as desk failure) |

**Row count: 28 (H1–H28).** Program status is PARTIAL while any
row is open, per doctrine. Rows may be proven in phases; the
program verdict is computed only from the final tree.

## 4. Phase shape (for HARDEN-PROGRESS.md)

1. RE-READ + RESEARCH (this phase) — scope + research, commit.
2. AUDIT — H1–H7, H12–H19 evidence gathered per sleeve/process;
   cures land in-pass where bounded, each with blocker + BUGLOG.
3. EDGE PASS — H8–H11 per sleeve (enhance or verify-only).
4. HARDEN + LEAN — H20–H23, H19 removals, research adopts landed.
5. FINAL VERIFY — H24–H28 on the final tree, independent re-run;
   mirror + report. Open rows named at the top of the report.

## 5. Coverage ledger for this scope phase

- Searched/read in full: doctrine repo (README, AGENTS, INSTALL,
  SKILL, 5 references); Edge v3 skill (SKILL, edge-protocol,
  foundations, mechanisms, validation, adaptive-control,
  adaptive-learning, desk-runtime — full; sources/frontier-sources/
  adaptive-sources skimmed as source registers); edge_mechanics.py
  in full; root master prompt v3.0 (head + structure; it restates
  the v3 skill, which was read in full); v3 desk state of record
  (V3-SCOPE, V3-REPORT, EFFICIENCY, SCALE-FAULT, DEPLOY,
  ASTER-ADOPT reports, PROGRESS, OPERATIONS, DOCTRINE, BUGLOG ids,
  config census, gate script).
- Excluded by task definition: Edge v1/v2 skill bodies (v3 governs;
  v2's ENHANCE-PLAN read as desk history, not as method); femto-lean
  internals beyond preservation facts.
- Unavailable: the desk-research tree (probed in the v3 build; fire
  lanes remain fail-closed) — recorded, not treated as absence.
