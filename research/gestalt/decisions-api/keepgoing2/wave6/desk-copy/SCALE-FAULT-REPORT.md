# SCALE-FAULT-REPORT — muse-desk-v3 scale, fault, restart, lifecycle proofs

Date: 2026-10-24. Machine: 2 vCPU, 7.7 GiB RAM, box under load during
measurement (figures are representative of THIS box, not a quiet-box
best case). Verdict for this phase: **PARTIAL** — every row below is
proven as stated; the named open items stay OPEN. Synthetic capacity
proof is labelled SYNTHETIC throughout and is never production-load
evidence (doctrine). Harness: workflow work dir `scale_fault_proof.py`
+ `fault_proof.py`; raw results in `results_roster.json`,
`results_cap400.json`, `results_cap800.json`, `results_faults.json`
(workflow run ea57f2cc, work/).

## 0. Platform cures landed in this phase (fail-first, gate-wired)

- **SCALE-1a — synthetic sleeves could dispatch.** `Desk.add_sleeve`
  now takes `synthetic=True`; synthetic sleeves evaluate (capacity
  load) but their intents are counted as `intents_suppressed` and
  NEVER reach the dispatcher.
- **SCALE-1b — broker-down intents crashed the dispatch path.** The
  dispatcher now queues the intent (`broker_unavailable` journal row,
  status `queued`, zero fills) and `retry_pending()` re-processes it
  after recovery; fills come only from broker read-back, and the
  `_seen` index + client-order-id make a second fill impossible.
- Blockers: `tests/test_scale_fault_blockers.py` (2 tests) — FAILED
  (2 errors) on the pre-cure tree, GREEN after; gate-wired via the
  discover pattern in `run_regression_blockers.sh`. BUGLOG SCALE-1.

## 1. FULL-ROSTER RUN — simulated session day (acceptance A6 input)

Warm snapshot: harness-built single immutable snapshot (30 symbols ×
7 timeframes × 50 bars + positions/quotes/options/kraken/tensor/fires
keys for every declared producer input in `config/sleeves.json`).
Simulated day = 3 full-roster cycles (14:35Z open, 17:00Z mid,
19:55Z close, asof Fri 2026-10-23) through `Desk.run_cycle`
(producers → snapshot → fed gate → worker pool → one dispatcher).

| Cycle | Wall | ok | error | UNFED | wedged | dispatched |
|---|---|---|---|---|---|---|
| 14:35Z | 7.85 s | 131 | 2 | 0 | 0 | 3 |
| 17:00Z | 9.20 s | 131 | 2 | 0 | 0 | 3 |
| 19:55Z | 10.70 s | 131 | 2 | 0 | 0 | 3 |
| **Day total** | **27.75 s** | | | | **0** | |

Roster accounting (every one of the 156 named): 133 evaluated +
23 parked (source-off set, named in the harness output:
s_1wg_small, s_1wsw_stress, s_moonshot + 20 Q07 swing lanes) = 156.
Zero UNFED: the harness warm produced every declared input key, so
the fed gate passed all 133; UNFED behaviour itself is proven by the
registry blockers and fault (b)/(c) paths.

Per-stage attribution (instrumented single cycle, wall 7.49 s):
warm producers 0.00 s (harness data pre-built; snapshot serialize is
inside the cycle), dispatch 3 intents (negligible, matches the v2
baseline's non-bottleneck finding), **evaluation = the remainder
(~100% of cycle wall)** — the dominant stage is sleeve evaluation on
the 2-worker pool, exactly the structural constraint v3 was built
against (v2 baseline: 85.26 s sequential for 71 sleeves; v3: ~9 s
per cycle for 133).

OPEN (named, not hidden) — 2 sleeves error deterministically on the
harness snapshot shape; the evaluation completes, the error is
recorded in the terminal roll, no wedge, no phantom intent:
- `fwd_alpaca_ada_rsi2` — `AttributeError: 'list' object has no
  attribute 'get'` (expects a dict-shaped producer value where the
  harness warm supplied the generic list for its bespoke input key).
- `s_cl_vmr_qqq` — `TypeError: float() argument must be ... not
  'dict'` (expects its ChartsLector/Tensor input in a shape the
  generic warm does not reproduce).
Both are harness-fidelity gaps to close when their real producers
are wired; they do not block the scale invariants (0 wedged).

## 2. CAPACITY 400 — SYNTHETIC padding (acceptance A6)

133 genuine sleeves + 267 TEST-ONLY harness sleeves
(`synthetic=True`, one shared trivial module, each emitting one
intent per cycle to prove suppression) = 400 slots, one cycle:
**wall 8.43 s**, states ok 398 / error 2 (the §1 pair), wedged 0,
synthetic intents suppressed 267, broker submits 3 (genuine sleeves
only), **synthetic dispatched 0**. Peak RSS: parent 140 MB,
children 140 MB.

## 3. CAPACITY 800 (2×) — SYNTHETIC padding (acceptance A7)

133 genuine + 667 synthetic = 800 slots, one cycle: **wall 9.67 s**,
states ok 798 / error 2, wedged 0, timeouts 0, synthetic intents
suppressed 667, broker submits 3, **synthetic dispatched 0**.
Peak RSS: parent 141 MB, children 141 MB (maxrss, loaded box).

Queue-wait vs execution split (pool-level, 800 synthetic slots,
pool size 2): wall 0.64 s, summed execution 1.03 s (1.3 ms/slot),
estimated queue wait 0.12 s — at synthetic load the queue is not the
constraint; in the full 800-slot cycle the wall is dominated by the
genuine sleeves' evaluation (§1 stage attribution), and the
synthetic tail adds ~1–2 s over the genuine-only cycle.

Design target check: 400 slots complete a full cycle in 8.43 s —
inside the fastest 60 s cadence with wide margin on this box class.

## 4. FAULTS (acceptance A13/A14)

| # | Fault | Verdict | Evidence |
|---|---|---|---|
| a | Worker killed mid-cycle (`os._exit(3)` sleeve) | **PASS** | Cycle status ok; crashed sleeve verdict `wedged/worker_eof`; good sleeve ok in the same cycle AND ok next cycle (worker respawned) |
| b | Corrupt one snapshot file | **PASS** | Direct load raises `SnapshotCorrupt`; desk-level injected corruption → cycle status `failed_closed_snapshot_corrupt`, dispatched 0, broker submits 0, no phantom intents |
| c | Broker door down during dispatch | **PASS** | Intent status `queued`, phantom fills while down 0; after recovery `retry_pending()` → filled exactly once (broker submits 1, fill rows 1, position qty 1.0) — fill from read-back only |
| d | Whole desk killed mid-session, restart | **PASS** | New Desk/Dispatcher over the same state root: replayed intent → `duplicate`, broker submits unchanged (1 → 1), **zero duplicate orders**; scheduler cursor persisted on disk — restarted scheduler re-fires nothing for the consumed bar |

## 5. ORDER LIFECYCLE (acceptance input to A9/A15)

FakeBroker (fills only from read-back), entry → fill → manage →
exit → flat, all read back from the dispatcher slice + journal:

| Family | Entry | Manage | Exit | Flat |
|---|---|---|---|---|
| Equities (SPY ×10) | filled | qty 10.0 held | filled | yes |
| Options multi-leg (4 OCC legs, iron-condor shape) | 4× filled | legs held | 4× filled | yes |
| Crypto fractional (BTC/USD 0.01) | filled | qty 0.01 held | filled | yes |
| Kraken-style pair (ADA/USD ×100) | filled | held | filled | yes |

Real Alpaca PAPER door, **evaluate-only mode** (no order submitted):
door constructed on `https://paper-api.alpaca.markets`; live base
URL refused at construction (PASS); probe intent validates and its
idempotency id derives as `v3-probe-probe1`; orders submitted to
the real door: **0**; credentials present in this shell: no — so a
live paper fill/read-back round-trip remains **UNVERIFIED** here
and belongs to the live-smoke phase (A9), not claimed from this run.

## Coverage ledger

- Proven on the final tree: roster day (3 cycles), cap 400, cap 800,
  faults a–d, FakeBroker lifecycle (4 families), paper-door
  construction/refusal proofs, SCALE-1 blockers.
- OPEN by name: `fwd_alpaca_ada_rsi2` + `s_cl_vmr_qqq` harness-shape
  errors (§1); real paper-door fill read-back (evaluate-only here).
- Not in scope of this phase: live RTH autonomy (A9), backups (A16),
  GitHub save of the final tree (A18) — later phases.
