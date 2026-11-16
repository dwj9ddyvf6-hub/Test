# PURGE-REPORT — muse-desk-v3 leanness purge (2026-10-24)

Scope: pure performance. Nothing superfluous, nothing arbitrary —
every removal carries its no-consumer proof; every candidate that
failed the proof is recorded as EXAMINED / KEPT with the reason.
Removing a regression blocker or a test is forbidden and none were
touched. Best Setups vendored tree, saty_sol pin, Tensor engine:
untouched.

## 1. Before / after (identical measurement path)

Repo / runtime sizes:

| Measure | BEFORE | AFTER |
|---|---|---|
| Working tree (excl .git) | 1.4 GB | 93 MB |
| Tracked source | 16 MB / 1004 files / ~107k py LOC (unchanged — see §3) | same |
| state/snapshots | 197 files / 1.3 GB, +1 file per cycle forever | **3 files / 19 MB, bounded by retention** |
| Roster / modules / producers | 311 sleeves (23 parked) / 670 py files / 27 producers | identical |

Full-roster cycle (311 sleeves, evaluate-only FakeBroker, env={}
fail-closed producers, COLD earnings caches, same harness
`measure_cycle.py`, per-stage producer attribution):

| Stage | BEFORE | AFTER |
|---|---|---|
| Cycle wall | ~438.7 s | **114.4 s** |
| Producer stage total | 434.8 s | **111.6 s** |
| — earnings | 234.2 s | 48.4 s |
| — earnings_events | 179.5 s | 33.1 s |
| — other 25 producers | 21.1 s | 30.1 s (network variance; bars_secondary 0.1→14.3 s) |
| Evaluation + dispatch | remainder (~4 s; 286 UNFED / 23 PARKED / 2 FED) | remainder (~3 s; states **identical** 286/23/2, status ok) |

## 2. Removals / cures (each with its proof)

### PURGE-1 — snapshot store: unbounded growth cured at the source
- FINDING: `desk3/cycle.py` saved one content-hashed snapshot per
  cycle into `state/snapshots/`; NOTHING ever removed one (grep:
  no prune/retention anywhere). 197 files / 1.3 GB accumulated in
  the desk's first day, ~15 MB more per cycle, forever.
- NO-CONSUMER PROOF for old snapshots: the only readers of a
  snapshot file are (a) cycle.py's integrity re-read of the
  just-saved path in the same cycle and (b) that cycle's workers,
  which open the exact `snapshot_path` handed to them in the task
  (desk3/worker.py:20). No code path opens a prior cycle's file
  (git grep "snapshots" over all py: only save/load of the current
  path + tests' own tmp dirs).
- CURE (minimum sufficient, at the writer): `desk3/snapshot.py`
  `save_snapshot` now prunes the directory to the newest
  `SNAPSHOT_KEEP = 3` files on every save (fail-soft). Backlog
  purged with the same function: 197 → 3 files, 1.3 GB → 31 MB
  (19 MB after the AFTER-measure cycle).
- BLOCKER: `tests/test_purge_snapshot_retention_blockers.py`
  (2 tests; FAIL pre-cure — "6 != 3" and cycle test — PASS after;
  auto-wired: the gate discovers `test_*_blockers.py`).

### PURGE-2 — earnings producers: sequential day-walk was 95% of the cycle
- FINDING (Efficiency-Breakthrough attribution, §1): on a cold-cache
  cycle, `earnings` + `earnings_events` cost 413.7 s of the 434.8 s
  producer stage. Both walk the SAME Nasdaq calendar endpoint one
  HTTP fetch per day (30 s timeout), forward ~72 weekdays /
  backward ~64, strictly sequentially, on every cache miss (20 h
  TTL caches, separate files).
- CURE (structural, output-identical): day fetches go through a
  bounded parallel map (`_fetch_days`, 8 workers) in
  `desk3/producers3.py`; the forward scan prefetches one chunk
  ahead and consumes in the original order, stopping at the exact
  day the sequential walk stopped (evidence counts consumed days
  only); the history walk aggregates in original day order.
  Payloads, evidence, reports and days_failed are byte-identical —
  only the wall changed: earnings pair 413.7 s → 81.5 s.
- BLOCKER: `tests/test_purge_earnings_fetch_blockers.py`
  (identity assertions pass on BOTH sides = preservation guard;
  concurrency assertions FAIL pre-cure — max in flight 1 — PASS
  after). Existing suite `test_harden_cure_batch3_blockers` 18/18
  GREEN after the cure.

## 3. Examined and KEPT — with the no-consumer proof that FAILED

A whole-corpus dead-module scan (dotted name + import + computed
import patterns over all 1004 tracked files) flagged 48 modules
with zero textual references. Every one was individually re-proved;
**zero modules were removable**:

| Candidate set | Verdict | Proof of life |
|---|---|---|
| adapters/ x17 (donchian_crypto, earnings_buyback, ema_vwap(+_options), fear_premium, free_etf, free_kraken_ada_basis/breakdown/crowded, momentum_rotation, morning_dip, phase_daily, phoenix, po10_qqq, qqq_put_ladder, qullamaggie_paper, raschke_pf3) — superseded in config by adapters3./port_b5. modules | **LIVE — kept** | Loaded at runtime by computed import: `adapters3/_snapshot_ctx.py:138 evaluate_ported()` and `desk3/port_b5/_ctx.py:153 run()` do `importlib.import_module(f"adapters.{sleeve_id}")`. The adapters3/port_b5 modules are thin enhance/filter wrappers AROUND these. Deleting them would have amputated 17 live sleeves. |
| adapters/_v2bridge.py (32 LOC shim) | kept | Documented compatibility shim (AUDIT-CURE-2): re-exports adapters/_bridge under historical names, "imported both as adapters._v2bridge and as top-level _v2bridge" — a preserved verified path; 32 LOC is not worth breaking it. |
| desk3/vendor/sleeves/* x10 | **LIVE — kept** | `desk3/port4_context.py:49` loads `desk3.vendor.sleeves.{sleeve_id}` by f-string. |
| sleeves/s_mn_* x8 | **LIVE — kept** | `adapters/laz8_common.py:45` loads `sleeves.{sleeve_id}` by f-string. |
| desk_sleeves/* x7 (raschke_rre, rsi_meanrev, …) | **LIVE — kept** | Config rows name them as bare top-level modules (`"module": "raschke_rre"`), resolved via the pool's sleeve_path. |
| desk3/terminal.py | **LIVE — kept** | Relative import `from .terminal import …` in desk3/cycle.py (the scan's blind spot — recorded as a scan-method lesson). |
| desk3/port_b5/_enh2.py, runtime/models.py, core/saty_gpt_v03/routing.py, candidates/example_momentum_shadow.py | kept | Relative import (`from ._enh2 import run_enh2` x10); named in port blocker-test file manifests; internal to the byte-pinned saty package; live via candidates/registry.json + desk3/research.py. |
| desk3/qulla_scan.py, desk3/buyback_scan.py | kept | Entry-point producer tooling: they WRITE the cache files (cache/qulla/proposals.json, cache/scan/buyback.json) the qulla/buyback_scan producers serve. Not imported ≠ dead. |
| Producers (27 registered) | none removed | Static census: every produced key is consumed — by config `inputs`, registry fed-gate, or direct `view.get(...)` reads (e.g. `calendar` is read by aster engines from the view). Zero produced keys with zero consumers. |
| Duplicate files desk3/contract.py == core/sleeve.py == desk3/vendor/core/sleeve.py (11.5 KB x3) | kept | Same bytes under three package names, each with live importers in its own boundary (desk3 strategies, core saty packages, port4 vendor isolation). Collapsing means rewriting imports across pinned/ported code — risk >> 23 KB saved. Not minimum-sufficient. |
| Config row keys beyond build_desk's reads (bp_buffer_frac, flat_by_close, flatten_time_et, params, session, …) | kept | The row schema is the roster contract written by every batch generator (desk3/aster_*, port registries) and carried from the v2 lineage; not provably unread by every ctx surface. No removal without a full-schema consumer proof. |
| cache/ (20 MB, untracked) | kept | Live producer cache (bars/options/kraken/qulla/scan channels are read by producers each cycle). Runtime data, not source waste. |
| .gate_tmp2/ (28 MB, untracked) | NOT touched | Scratch of sibling lanes in flight during this purge (their gate tmpdirs). Owned by those lanes; the gate's own `.gate_tmp` self-cleans via trap. |

Process/job inventory: no desk process was running during the
purge (ps: no run_live/cycle process); no v3 cron entries exist
(crontab grep: none) — no redundant processes or duplicated
scheduling to remove.

## 4. Gate

Purge blockers: 4/4 GREEN. Affected suite (batch3 producers):
18/18 GREEN. Full gate: 1045 tests, 3 failures — all three are the
pre-existing sibling-lane failures documented in HARDEN-PROGRESS
(batch 26 entry) BEFORE this purge, and none of the three suites
imports a purge-touched file (verified by grep):
`test_harden_batch4_blockers::test_xsp_e2e_entry_then_settle`,
`test_harden_edge_batch18_blockers::test_s_1dgp5_stale_bar_refused_fresh_enters`,
`test_lazarus_batch5_blockers::test_filter_specifics_other_lanes`.
Status: PARTIAL by the no-green-while-any-row-open rule — the two
purge cures are proven on the final tree; the 3 named failures are
other lanes' open items, untouched here.
