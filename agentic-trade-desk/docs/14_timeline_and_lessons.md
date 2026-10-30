# 14 — How the desks evolved (anonymized timeline and lessons)

This is the story behind the rules. Dates are relative. It shows *order of discovery*, which is also a sensible order of defence.

## Phase 1 — Many scripts, one idea per desk
Several desks existed side by side: a research-heavy desk with a public page, a desk run by a partner agent with its own strategies, a code-agent's strategy-free "framework" desk, and a lab of studies. Each had its own scheduler, ledger and conventions. **Lessons:** identity drift (similar names meaning different things), duplicated work, and the need for a **catalog** with stable ids; a published "N sleeves" number that nobody could reproduce.

## Phase 2 — Consolidate onto one engine
A single new engine replaced the older desk in one night. The old schedulers were shut down — and a supervisor restarted them two minutes later (P-17). Within days of the cutover, a first wave of bugs (≈ 25 in a few hours) appeared: bad quote fallbacks, a delayed index feed making a rule unknowable (P-34), rounding above caps (P-29), a liquidity rule copied from a template (P-33/`04` §4.6), an **inverted ported rule** (P-58). Rule: *"the first week after any cutover is an audit week"* — run readiness drills before every open.

## Phase 3 — Execution hardening
Order lifecycle bugs dominated: slot accounting (P-42, P-43), refusals and retries (P-03, P-04), partial fills (P-31), timeouts mistaken for refusals (P-02), final-state sets (P-30), read-back cadence, sub-penny prices (P-28). The **fake-broker lifecycle test** was born here and caught the rest. A "one decision per session" idea turned out to be too blunt.

## Phase 4 — Robustness against the platform
The host machine was paused when idle (P-12), rolled back (P-09), and its keys/venv/cache disappeared. Defences: resume-aware supervisor, persistent store, boot hook, boot sentinel, off-box backup after fills, restore drills, venv freeze. A **cloud failover** was designed (P-19, P-20, P-21) after "box suspended during a decision window" cost real entries.

## Phase 5 — Risk exits that survive the machine sleeping
A standing per-trade disaster stop was added to lots that had none (P-37), broker-side GTC stops placed, the failover's stop interactions solved, and the "no kill switches" principle formalized: *per-trade stops yes, desk-wide halts no*.

## Phase 6 — Scale: hundreds of sleeves
Partner and library strategies were vendored byte-for-byte and hosted in-process; a speed shim passed a 284/284 identity test; an 800-sleeve load test showed first pass seconds, steady pass sub-second, tens of MB; **exit audits** found sleeves whose exits could never fire (P-40); a restart-re-entry bug in a vendored library was fixed *around* it in the host (P-01). The inventory was reconciled: configs ≠ catalog rows ≠ running sleeves (P-49).

## Phase 7 — Second-order operations
Concurrent writers (failover vs main loop) exposed the lock/merge race (P-05); a stuck desk (P-08) led to hard deadlines everywhere; lane caps that had been cut to fit a smaller capacity were restored once evidence showed valid signals were being blocked, while the capacity gap was made *visible* instead of silently enforced (P-44, P-48); the weekly agent usage limit took scheduled wake-ups down (P-18); the supervisor gained wall-vs-monotonic detection.

## Phase 8 — Documentation as a deliverable
Every fix got a log row, a guard, and a runbook line; mirrors were made non-destructive (P-10); an engineering doctrine (scope, minimum change, anti-spiral, proof before green) was adopted by every agent. This guide is the generalization.

## The ten sentences to remember
1. Derive ids from data, persist them before sending, and a restart is harmless.
2. A timeout is unknown, not refused.
3. Lock, replace atomically, merge foreign additions add-only.
4. Every network call, pass and job has a deadline; use monotonic time.
5. Alert, don't halt; unknown means wait, not guess.
6. One order path; tests can't reach it.
7. Exits first, and every exit must be able to fire.
8. The book is a fold of an append-only ledger and equals the broker every pass.
9. The machine will vanish; back up off-box and practise restoring.
10. Green is an evidence state.
