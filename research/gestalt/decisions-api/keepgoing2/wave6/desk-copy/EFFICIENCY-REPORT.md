# EFFICIENCY-REPORT — muse-desk-v3 before/after (acceptance A12)

Date: 2026-10-24. Verdict for this phase: **PARTIAL** — the A12
identical re-run is proven below and one in-v3 structural repair
(EFF-1) landed with re-measurement; the governing constraint is now
a single sleeve's single-core CPU cost (hardware floor, §4). Live
paper-door latency stays with the live-smoke phase (A9), as scoped.

## 1. The measurement (same complete path, both desks)

Identical conditions, per V3-SCOPE §6/§8-A12: the 71 v2 sleeves, the
same cache content (v2's real cache, 126 symbols / 328 series /
242,641 bars, read read-only through v2's own BarCache — v2 tree
untouched), the same asof **2026-10-23T19:00:00Z**, FakeBroker
dispatch (broker round-trip excluded on BOTH sides, as in the
baseline). v3 side: snapshot built once from that cache by the
parent, sleeves evaluated on the 2-worker pool, one dispatcher.
Machine: 2 vCPU, 7.7 GiB RAM, box under load (load avg ~4) during
both measurements — figures are representative of THIS box under
load, not a quiet-box best case (v2's own audit measured
saty_gpt_v02 at 4.83 s on a quieter box; the spread is load, and it
hits both desks). Harness: workflow work dir `measure_a12.py`, raw
`results_a12.json` (run workflow-run-88e3e459).

## 2. Before / after

| Stage | v2 (BEFORE) | v3 pre-EFF-1 | v3 after EFF-1 (cycle 2, learned costs) |
|---|---|---|---|
| **Full-roster cycle wall (71 sleeves)** | **85.26 s** | **46.84 s** | **34.61 s** |
| Evaluation | 85.26 s (sequential subprocess per sleeve; wall = sum) | pool wall 38.81 s / eval sum 46.68 s | pool wall **31.76 s** / eval sum 39.55 s |
| — saty_gpt_v02 alone | 44.75 s (52% of cycle) | 33.61 s (72% of eval sum) | 31.76 s (**100% of pool wall**) |
| — next 4 sleeves | 9.38 s | 6.44 s | 2.51 s |
| — remaining 66 (median each) | ~31 s (median 0.384 s) | median 0.073 s | median 0.026 s |
| Process spawn + interpreter + imports | ~0.135 s × 71 ≈ **9.6 s per cycle** | ~0 (persistent workers; spawn once at pool creation) | ~0 |
| Cache / snapshot read | every sleeve subprocess re-reads + re-parses its own slice from disk JSON (full-cache parse 1.56 s in-process); no shared snapshot; a cycle could observe mixed cache states | ONE parent read of the cache (2.56 s) → one immutable snapshot (24.2 MB, content-hashed): build 1.04 s + save 3.83 s + verify re-read 1.77 s (standalone timings); each worker JSON-loads it once per hash (0.8 s), then reuses it across cycles | same |
| Non-pool remainder inside cycle wall (snapshot + fed gate + dispatch + journals + terminal) | inside the 85.26 s (dispatch alone 0.023 s, journal 0.067 s / 1k appends — non-bottlenecks) | ~8.0 s | ~2.85 s |
| Provider / network calls during evaluation | 0 (cache-local by design) | 0 (snapshot-local by construction; sleeve env is stripped, workers hold no credentials) | 0 |
| File reads of market data per cycle | 71 subprocess cache-slice reads | 1 cache read pass (parent, warm) + 1 snapshot file (workers, once per hash) | same |
| Dispatch (FakeBroker, local) | 0.023 s for 21 intents | inside remainder; 15 intents cycle 1 | inside remainder; 9 intents cycle 2 (fewer: cycle-1 fills are journal state, sleeves correctly stand down — behaviour, not a timing effect) |
| Memory (peak RSS) | not recorded in the scope baseline — not invented here | parent ~299 MB, largest worker ~299 MB (24.2 MB snapshot held per process) | parent ~301 MB, workers ~299 MB |
| Result quality | 70 ok / **1 error** (iron_condor float(tuple)) / 21 intents | **71 ok / 0 error** / 15 intents | 71 ok / 0 error |

**Headline: 85.26 s → 34.61 s = 2.46× on the identical complete
measurement**, with result quality strictly better (71/71 ok).

Full-roster context (SCALE-FAULT-REPORT, harness warm snapshot,
30 symbols × 50 bars — a much smaller data set, not the A12
measurement): v3 runs all 133 active sleeves in 7.85–10.70 s per
cycle, 400 slots in 8.43 s, 800 SYNTHETIC slots in 9.67 s, peak RSS
~141 MB. The A12 numbers are larger because the real cache is
~100× the harness data and saty_gpt_v02 re-derives over ~1,000-bar
warmup histories — the comparison that matters is same-data,
above.

## 3. The breakthroughs (structural, in order of contribution)

1. **Subprocess-per-sleeve → persistent worker pool + one immutable
   snapshot** (the v3 architecture, §7.1–7.2 of the scope). Kills
   three baseline costs at once: the ~9.6 s/cycle spawn+import tax,
   the 71× per-sleeve cache re-parse (now one parent read + one
   hashed snapshot every sleeve in the cycle provably shares), and
   the sequential wall = sum shape (2 workers overlap; the roster's
   non-saty work, 7.8 s of CPU, now hides entirely behind the
   slowest sleeve). 85.26 s → 46.84 s before any in-phase repair.
2. **EFF-1 — cost-aware list scheduling in the pool** (this phase;
   BUGLOG EFF-1, blockers `tests/test_efficiency_blockers.py`,
   fail direction proven: collection error pre-cure, GREEN after;
   full gate GREEN 318). The v3 scale runs exposed the remaining
   in-v3 constraint: round-robin assignment (`i % size`, config
   order) stacked ~half the roster serially behind saty_gpt_v02 on
   its worker — pool wall 38.81–39.77 s vs a 33.6 s single-sleeve
   floor. Repair at the chassis only (no sleeve code, timeout, or
   isolation semantics touched): longest-known-cost first, each task
   to the least-loaded queue, costs learned per sleeve from each
   cycle's elapsed and reused the next cycle. Re-measured on the
   identical path: **pool wall 39.77 s → 31.76 s, cycle wall
   46.92 s → 34.61 s (−26%)** — and 31.76 s is exactly
   saty_gpt_v02's own elapsed: the queue behind it is gone.

## 4. What remains — the governing constraint

**saty_gpt_v02's own single-core CPU re-derivation is now the whole
pool wall (31.76 s of 31.76 s).** It resamples 5Min SIP bars into
its 10m/1H clocks and re-derives over its full warmup history
inside every evaluation. That computation lives inside the
byte-identical ported strategy; the port-fidelity boundary forbids
changing it, and it is inherently sequential on one core — the
governing constraint is the **hardware floor for that sleeve on
this box under load** (the same code measured 4.83 s on a quiet
box in v2's audit, so the floor itself is load-set). Further
repair stops paying here: the next candidate (cross-cycle
memoization of the sleeve's resampled series) would change what
the strategy computes from, i.e. a strategy-layer change requiring
its own owner ruling — named, not done silently.

Second stage, not dominant: snapshot serialization of the real
cache (~6.6 s standalone: build 1.04 + save 3.83 + verify 1.77;
~2.85 s total non-pool remainder in-cycle). It is ~8% of the cycle
and buys the integrity gate (corrupt snapshot fails the cycle
closed before any dispatch — A13, proven). Left as is.

## 5. Dispositions and coverage ledger

- **A20 (baseline defect):** iron_condor's float(tuple) error from
  the v2 baseline does **NOT** reproduce on the v3 port — 71/71 ok
  on the identical cache/asof. Cured in the port (dispatcher/D3-era
  fixes carried over); recorded here, not silently inherited.
- **Intent-count delta (21 v2 vs 15/9 v3):** different starting
  state (v2 baseline ran over the copied desk's journal state; v3
  ran from empty journals, then its own fills). Timing comparison
  is unaffected; intent parity per sleeve is A4's fixture proof,
  already landed in the port phases.
- Proven on the final tree: A12 identical re-run (2 cycles),
  EFF-1 blockers fail-first + GREEN, full regression gate GREEN
  (318 tests) after the cure.
- OPEN by name (unchanged, other phases): real paper-door fill
  read-back / broker RTT (A9 live smoke); the two harness-shape
  sleeve errors from the scale phase (`fwd_alpaca_ada_rsi2`,
  `s_cl_vmr_qqq` — both evaluate ok here on the real cache shape:
  they are among the 71 ok above; their scale-phase errors were
  harness-warm shape gaps, as that report suspected).
- SYNTHETIC labelling: the 800-slot figure remains synthetic
  capacity proof only, never production-load evidence.
