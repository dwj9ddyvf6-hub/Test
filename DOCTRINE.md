# DOCTRINE.md — InfinityBlade, operative summary for muse-desk-v3

Canonical source (controls where this summary differs):
`~/workspace/research/infinityblade-doctrine/` — README.md, AGENTS.md,
`skills/infinityblade/SKILL.md`, and references field-manual.md,
lessons-from-the-field.md, review-mode.md, examples.md, eval-cases.md.
Read in full at scope phase, 2026-10-24. This file is an index, not a
substitute; re-read the canonical skill at any program-level phase
boundary and whenever a failure class repeats.

## Governing rule
**No green status without evidence from the final system state.**

## Every task
- **SCOPE first** — Surface (what changes), Constraints (what stays
  untouched), Outcome (observable success), Proof (what evidence
  demonstrates it), Edges (boundaries/dependencies). For whole-product
  work, SCOPE becomes a **finite acceptance matrix**; every row is
  PASS / FAIL / BLOCKED / UNVERIFIED; no GREEN while any row is open;
  never shrink the task to optimize the report.
- **Minimum sufficient change** at the demonstrated source. Prefer no
  change, then reuse of a verified path, then native capability, then
  repair at source; new machinery only when the existing system cannot
  satisfy the outcome. Never strip validation, safety, observability,
  or recovery to shrink a change.
- **Preserve verified paths** — one authoritative source of truth;
  never create a second to work around the first; preserve unrelated
  state in a dirty tree.
- **Outcome before activity** — success is an observable result, not a
  list of actions.

## On failure
- **Route failure ≠ task impossibility.** A failed route proves that
  route failed. Classify the failure (implementation / hypothesis /
  transport / provider / dependency / permission / external / missing
  choice), preserve the exact error, revise the hypothesis, try the
  highest-confidence safe alternative. Stop only at a genuine
  authority boundary or exhausted reasonable routes.
- **Anti-spiral** — every action must reduce uncertainty. Same class
  of action failing twice without a revised hypothesis = stop and
  reassess (known facts / unproven assumptions / last evidence / first
  failed boundary / smallest discriminating check / protected state).
- **Contradictory evidence is a stop signal** — do not defend the
  hypothesis; reproduce the exact named route/state; look for a second
  implementation, stale cache, wrong version, environment mismatch.
- **Never generalize from adjacent proof** — a unit test does not prove
  the integration; one account/interval/device does not prove another;
  a redirect does not prove deletion; prove absence separately.

## Efficiency Breakthrough (field-manual)
When a process is slow/flaky/repeating: (1) measure the complete path
under representative conditions, (2) attribute delay/failure to
stages, (3) rank by contribution, (4) repair the DOMINANT structural
constraint, (5) re-run the same complete measurement. Never improve
timing by weakening source identity, freshness, authorization, or
completeness checks. Label synthetic capacity proof separately from
authenticated production load. Bound workers/batches/retries/fan-out
to the capacity of the next boundary; one authoritative writer when
workers calculate from shared state; deduplicate in-flight work by
full identity; persist complete identity-verified evidence before
claiming a cold-start boundary complete.

## Verification & reporting
- Verify in layers: static → focused tests → regression invariants →
  integration → end-to-end at the boundary named in SCOPE. Final
  evidence must follow the LAST change, on the exact delivered
  artifact/environment. Any post-test change invalidates the green to
  the extent it could affect the proof (**final-artifact integrity**).
- Report exactly one state: **GREEN** (proven on final artifact) /
  **PARTIAL** (bounded portion proven, rest named) / **BLOCKED**
  (needs authority/access/input) / **UNVERIFIED** (changed, unproven).
  Report facts, not confidence; include receipts (action, artifact,
  expected vs observed, invariants checked).
- Review order (review-mode): scope → authority → causality →
  sufficiency → preservation → efficiency → verification → artifact
  integrity → reporting.

## Desk law layered on top (owner's standing orders)
- **Fix = cured at source + proven on final state.** Containment,
  fences, workarounds are not resolutions; an uncured problem stays
  OPEN and named at the top of every report.
- **Every fix ships a regression blocker** (test that FAILS on old
  code, PASSES on new — fail direction proven) wired into the gate,
  **plus a BUGLOG entry** (severity, file, what broke, the fix).
- **Coverage ledger for comprehensive claims:** searched / excluded /
  unavailable / pagination — never claim "everything" beyond the
  recorded corpus.
- **Manifest discipline for batch work:** bind each item to an
  explicit source identity + idempotency key; reconcile first;
  preserve non-targets; stop the batch at the first mismatch.
- **Provenance:** pin authoritative inputs by version/identity/hash.
  A familiar name or "latest" label is not provenance. Local presence
  is not remote durability — verify the destination independently and
  restore-test before deleting any source.
- Checkpoint progress to PROGRESS.md at every phase boundary, in
  commit-sized steps, so a stopped run is adoptable by a fresh launch.
