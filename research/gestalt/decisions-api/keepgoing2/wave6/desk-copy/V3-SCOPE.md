# V3-SCOPE — muse-desk-v3 scope contract, census, baseline, acceptance matrix

Scope phase completed 2026-10-24 (Sat). Status of this document: the
contract for all later phases. Verdict for the phase itself: **PARTIAL
by design** — scope/census/baseline are proven below; every acceptance
row is UNVERIFIED until its build phase proves it on the final tree.

Doctrine: read in full (README, AGENTS, SKILL, all five references of
`~/workspace/research/infinityblade-doctrine`); operative summary in
`DOCTRINE.md`.

---

## 1. SCOPE contract

- **Surface:** a brand-new desk in `~/workspace/muse-desk-v3` (own git
  repo, stdlib-only posture like v2): roster of 156 sleeves (71 ported
  from muse-desk-v2 + 85 genuinely-new Lazarus sleeves), a producer
  layer, a worker-pool evaluation engine over a single immutable
  per-cycle snapshot, one dispatcher to the Alpaca **paper** door,
  per-sleeve append-only journals, a scheduler, a terminal/feed
  surface, a research-lane fire-ingest for Lazarus lanes, and Best
  Setups vendored byte-identical as a preserved product lane.
- **Constraints (hard boundaries):**
  - v3 lives ONLY in `~/workspace/muse-desk-v3`. `muse-desk-v2` and
    all femto-lean trees are READ-ONLY reference — never edited.
  - Tensor ENGINE untouched everywhere (consumer of its bundle/fires
    only, exactly as v2).
  - Paper trading only: Alpaca paper door, same credentials route as
    v2 (ALPACA_KEY_ID env / local-alpaca-paper config + Secure Vault
    surrogate). Real-money endpoints forbidden; the door must refuse
    `ALPACA_ENV=live`.
  - Best Setups: vendor byte-identical; NEVER modify its source,
    behavior, outputs, charts, or UX (sha256 pins in §4).
  - Saty sleeves byte-faithful as in v2 (saty_sol sha256-exact posture
    carries over); every port is faithful — strategy logic changes
    only under a separate, explicit enhancement ruling, never silently
    during the port.
- **Outcome:** a desk that runs the full 156-sleeve roster
  autonomously through a live paper session — every sleeve evaluating
  on schedule against a fresh immutable snapshot, intents dispatched
  through the single paper door, fills reconciled against the broker,
  terminal fresh — designed for 400 sleeves, synthetic-proven at 800.
- **Proof:** the acceptance matrix in §6, row by row, on the final
  tree, ending in a live paper smoke read back from the broker.
- **Edges:** Alpaca paper door (orders, bars SIP, options v1beta1);
  Kraken public REST (data only); Yahoo ^VIX price-only (the one
  sanctioned use); Tensor bundle producer; the desk-research fire files
  (NOT reachable from this box — see §3.4, research-lane isolation);
  GitHub (backup/save route); the desk-terminal feed surface.

---

## 2. Census A — the 71 v2 sleeves (authoritative source)

Source: `~/workspace/muse-desk-v2/config/sleeves.json` @ v2 HEAD
`3593668` (COINBASE-APPLY). Verified mechanically 2026-10-24:

- **71 sleeves, 0 parked** (fwd_coinbase_sma200 unparked by the
  coinbase apply @ 3593668 — matches the task premise).
- Cadences: 300s ×47, 60s ×11, 3600s ×8, 900s ×2, 180s ×1, 1800s ×1,
  14400s ×1. Sessions: RTH ×55, 24h ×16.
- Slices: per-sleeve virtual slices in config (default $10k;
  morning_dip $20k and po10_qqq $100k per the D5/D6 ruling recorded in
  v2's AUDIT-REPORT). Slices carry over unchanged.
- IDs (the port manifest — bind every v3 sleeve to exactly one row):
  aurelia_gold, aurelia_ndx, bb_rsi_divergence, beatendown,
  bilbo_options, capitulation, capitulation_options, confluence,
  daily_cyan_gbm, donchian, donchian_crypto, earnings_buyback,
  em_1587, ema_vwap, ema_vwap_options, fear_premium, free_etf,
  free_kraken_ada_basis, free_kraken_ada_breakdown,
  free_kraken_ada_crowded, free_kraken_enj_spot,
  free_kraken_link_basis, free_kraken_link_breakdown,
  free_kraken_link_crowded, free_opt_own_iv, free_opt_pair,
  free_opt_parity, free_opt_release, free_opt_tail, free_opt_wheel,
  fwd_alpaca_ada_rsi2, fwd_alpaca_enj_iu_body,
  fwd_alpaca_link_ai_volume, fwd_coinbase_sma200, gate_1h,
  iron_condor, leader_d, leader_sc, leaps_momentum, legends_ema,
  momentum, momentum_rotation, morning_dip, phase_daily, phoenix,
  po10_qqq, qqq_put_ladder, qullamaggie, qullamaggie_paper,
  raschke_pf3, raschke_rre, red_day_reversal, rsi_meanrev,
  rsi_meanrev_options, rule_1d_cyan_smallcap, rule_1d_green_tom,
  rule_1h_cyan_raw, rule_1w_cyan_mom_adx, rule_1w_swing_beta_wt,
  saty_day, saty_gpt_v02, saty_gpt_v03, saty_magnum, saty_sol,
  saty_sol_0dte, snapback, spx_premium, tensor_red_dip, tensor_swing,
  ts_momentum_decile, vix_hedge.

## 3. Census B — Lazarus reconciliation

Sources: (i) `~/workspace/user/files/lazarus_sleeves_1024.csv`
(100 rows: sleeve_id, account, name, status, producer, fire_file);
(ii) the Lazarus section (§§4–5, 7–8) of
`goals/femto-lean-desk-rebuild/files/SLEEVE-CATALOG-CONSOLIDATED-2026-10-23.md`
(99 counted sleeves; GrokBot's page as of 2026-10-23, reported not
independently verified).

### 3.1 Row reconciliation (CSV ↔ catalog)
- CSV 100 rows = catalog 99 + `legacy_exit` (hidden exit-only stub on
  MAIN, producer "none (exit-only)", no fire file; the catalog
  explicitly excludes it from the 99). All 99 catalog IDs appear in
  the CSV; no CSV ID besides legacy_exit is missing from the catalog.
- Status mapping reconciles exactly: CSV ON 68 = catalog Live 63 +
  5 Shadow lanes the CSV marks ON (s_mn_kronos + the 4 s_mn_opt_*
  ports); CSV off 32 = catalog Disabled 29 + legacy_exit + 2 Shadow
  lanes the CSV marks off (s_1wg_small, s_moonshot).
- Accounts: MAIN 6 rows (5 counted + stub), TEST 94.
- Producer classes (CSV): sleeve_feed composer (tracker ledger +
  alt-data tags) 63; sleeve_midna (Midna entire-branch signal files +
  Yahoo) 24; lab_live books 5; tracker (canonical Tensor v698 engine)
  3; desk_feed 2; cl_live (ChartsLector screens) 2; none 1.
- Fire files (CSV): `shadow/paper_sleeve/live/sleeve_fires_v1.json`
  65 rows; `shadow/paper_sleeve/live/midna/midna_fires_v1.json` 24;
  `DESK_INTEGRATION/lab_live/out/latest/*.json` 5;
  `shadow/live/latest_fires_v3.json` + ledger 3 (the direct
  Tensor-fire lanes 1h/1d/1w); `shadow/live/desk_extra_fires_v1.json`
  2; none 1.

### 3.2 Genuine-count derivation (the roster math)
Start: 100 CSV rows.
- −1 `legacy_exit` — exit-only stub, not a strategy sleeve → **99**.
- −2 Q07 index entries (`s_q07_ins2`, `s_q07_wiki`) — index rows
  only per catalog §4.1; their cells trade as the 49 separate Q07
  lanes. Counting them would inflate the roster → **97**.
- −6 waiting-list placeholders (`s_wait_flow`, `s_wait_intraweek`,
  `s_wait_r2_dcyan`, `s_wait_chase`, `s_wait_olx_books`,
  `s_wait_q14`) — catalog §4.9: 0 slots, $0, entries not set, no rule
  documented (s_wait_q14 has no documented rule at all). Not buildable
  faithfully; carried in the fidelity ledger (§3.5) as parked-pending-
  spec, NOT in the roster → **91**.
- −6 apparent-counterpart duplicates of v2 strategies (catalog §5.1,
  inferred pairings — the only rows whose strategy already trades on
  the v2 roster): `s_mn_csmom`≈momentum, `s_mn_turtle`≈donchian,
  `s_mn_qqq_ladder`≈qqq_put_ladder, `s_mn_w_cyan_adx`≈
  rule_1w_cyan_mom_adx, `s_mn_gbm_1d_cyan`≈daily_cyan_gbm family,
  `s_mn_hourly_1d`≈tensor_swing. These are lineage ports of strategies
  v3 already carries; counting them as new would inflate the roster.
  They are recorded as lineage aliases of the v2 sleeves, not new
  sleeves → **85 genuinely new**.

**Lazarus genuine new = 85. Roster total = 71 + 85 = 156.**

Composition of the 85: Q07 traded lanes 49 (Cyan/Green ON 29 +
Swing off 20 — source status preserved, off lanes land parked);
Midna ports genuinely new 18 (of the 24 s_mn_*: 9 related-only
variants + 9 with no v2 counterpart; distinct rules/universes/exits —
variants, not duplicates); lab_live books 5 (s_1dg, s_1wlab, s_1wsw,
s_rules_1d, s_rules_1w); Tensor inventory lanes 5 (s_1dgp5,
s_1wc_micro, s_1wc_ml, s_1wg_small [off], s_1wsw_stress [off, "no
live source yet"]); direct Tensor engine books 3 (1h, 1d, 1w);
desk_feed books 2 (1dc, 1wa); ChartsLector lanes 2 (s_cl_qm_small,
s_cl_vmr_qqq); Moonshot study 1 (s_moonshot [off]).
Producer split of the 85: composer-fed (Tensor tracker ledger +
alt-data) 55; Midna-signal-fed 18; lab_live native 5; desk_feed 2;
cl_live 2; direct Tensor-fire 3.

### 3.3 Tensor-fire lanes vs independent strategies
- **Direct Tensor-fire lanes (producer = canonical Tensor tracker):**
  exactly 3 — `1h`, `1d`, `1w` (MAIN). They consume
  `latest_fires_v3.json` + the tracker ledger directly.
- **Tensor-derived, composer-fed:** 55 of the 85 consume tracker
  ledger fires re-composed with alt-data tags via
  `sleeve_fires_v1.json` (all Q07 lanes, inventory lanes, moonshot).
  Tensor is their signal root, but the traded rule (alt-data
  confluence gates, tier/band filters, holds) is the lane's own.
- **Independent of Tensor:** Midna-signal lanes 18 (their own branch
  signal files; 9 of the s_mn_* family are Tensor-signal books per
  catalog §5.2 — signal lineage noted, execution rule independent),
  lab_live books 5 (native Lazarus routing; s_1dg/s_1wlab/s_1wsw are
  Tensor-signal books routed natively), ChartsLector 2.
- In ALL cases the Tensor ENGINE is a data producer only; v3 never
  modifies it (hard boundary).

### 3.4 the desk-research reachability — coverage ledger
- Searched: `~/workspace/the desk-research` (absent), filesystem scan to
  depth 4 for a `the desk-research` directory (none found),
  `~/workspace/` top level (no such tree).
- Excluded: deeper filesystem scans (bounded probe per doctrine —
  the tree is GrokBot's Research Lab tree, not a desk tree).
- **Inaccessible: the entire the desk-research tree.** Every Lazarus
  fire-file path in the CSV is relative to that tree. Consequence,
  recorded as an architecture input (§7): Lazarus lanes in v3 are
  **fire-consumers** fed through a research-lane ingest contract
  (a drop directory / pushed snapshot), never by reaching into
  the desk-research. Until fires actually arrive, Lazarus lanes are
  fail-closed (evaluate, find no fresh fires, emit nothing) — honest
  state, named in the terminal, never papered over.

### 3.5 Fidelity-ledger skeleton (thin-description Lazarus rows)
Every Lazarus row is thin in the CSV (id/name/status/producer/fire
file only); the catalog adds a one-line rule sketch for most. The
build phase must complete one ledger row per Lazarus sleeve before
its port is claimed faithful. Columns: sleeve_id | catalog rule
sketch (entry/exit/hold/slots/budget) | missing fields | fidelity
risk | resolution route (fire-file schema / GrokBot page re-read /
freeze as pure fire-consumer with position rules from catalog).
Known-thinnest groups, pre-registered:
- Q07 lanes (49): rule lives in the ID's parameter string
  (family/horizon/band/filters); entry/exit/hold pattern from catalog
  §4.1 group text, not per-lane text. Risk: per-lane exit variance.
- `s_rules_1d` / `s_rules_1w`: 43 frozen rules replicated from an
  outside-lab export — the 43 rules are NOT enumerated in either
  source. Risk: highest. Route: fire-consumer freeze (trade the
  fires; the rule set lives upstream) unless the export is obtained.
- `s_1wlab`: four books run as one sleeve. Risk: book boundaries.
- `s_mn_kronos`: Kronos model internals are upstream. Fire-consumer.
- Waiting list (6, excluded from roster): no rule exists to port;
  ledger rows stay OPEN until a spec arrives from the research lane.
- `s_1wsw_stress`: catalog says "no live source yet" — port as
  parked fire-consumer; fidelity UNVERIFIED until fires exist.

## 4. Census C — Best Setups (preservation target)

Located in the femto-lean tree (the old desk's repo; v2 does NOT
consume Best Setups at all — no reference in v2 source/config/docs;
that absence is the preservation gap v3 closes by vendoring):

- **Source (femto-lean @ 2febc46):**
  - `core/setups_curator.py` — sha256 a6a98dbe…e06c (the pure curator)
  - `core/setup_card.py` — 174541c2…ba4
  - `core/setup_brief.py` — 1796be7c…f53
  - `core/setup_call.py` — 99b17810…c68
  - `core/setups_publish.py` — fde1c81a…4c4 (publish enrichment;
    called ONLY from `tools/run_live.py:publish_feed`, fail-soft)
- **Generator:** `tools/build_setups.py` (9e7c7313…f54) — wires the
  desk's SIP door + the one sanctioned Yahoo ^VIX use into the
  curator, read-only against desk state; plus `tools/build_briefs.py`
  (e1eeb07e…986) and `tools/build_market_charts.py` (786d725f…264).
- **Outputs:** `state/live/setups_latest.json` (32 KB, refreshed
  2026-10-24 13:44 ET — still live on the old tree),
  `state/live/setup_briefs.json` (2.68 MB), `market_charts.json`,
  `setup-charts/` PNGs, `setups_published.json`,
  `setup_alerts_outbox.jsonl`.
- **Surface / consumption today:** `tools/run_live.publish_feed` →
  `setups_publish.enrich_snapshot` extends the desk-terminal feed
  snapshot; charts pushed to the Femto repo
  (`docs/desk-terminal-live/setup-charts/`) via GitHub Contents API;
  the desk-terminal page hides absent panels (graceful degradation).
- **v3 preservation contract:** vendor the five core modules + three
  tools byte-identical (sha256 verified at vendor time and by a
  gate-wired blocker thereafter), run them as their own scheduled
  lane against v3 state, feed the same snapshot keys to the v3
  terminal. No source, behavior, output, chart, or UX change — ever.
  Any future change is a separate owner ruling, not a desk change.

## 5. Census D — data pipelines inventory (what v2 actually runs)

Producers (all warm-time only; sleeves make zero network calls —
v2 DESIGN §3b/§4b, carried into v3):
- **Bars** — `runtime/cache_warm.py`: the cache warmer, only caller
  of the market-data door; Alpaca SIP bars into the local bar cache
  (cache holds 126 symbols / 378 series / 138,700 bars at scope time).
- **Quotes** — `runtime/quotes_warm.py`: latest SIP quotes (bb_rsi
  fresh-quote gate, 60s max age at evaluation).
- **Options** — `runtime/options_warm.py`: options chain ported from
  femto-lean `core/options_feeds.py` @15f3368 selection windows onto
  the Alpaca door (v1beta1), incl. Yahoo price-only route for VIX/VXX
  context per v2 WIRING-REPORT.
- **Kraken** — `runtime/kraken_warm.py`: Kraken PUBLIC REST, data
  only, no keys/orders (ADA/ENJ/LINK basis/breakdown/crowded sleeves).
  Known external block carried from v2: ENJ/USD unlisted at Alpaca
  (40410000) — ENJ sleeves fail closed; no substitute.
- **Tensor** — `runtime/tensor_warm.py`: runs the faithfully ported
  femto-lean `core/tensor_feeds.py` TensorProducer @15f3368 on the
  warmer side; engine untouched; bundle into cache for tensor_swing /
  tensor_red_dip.
- **Qullamaggie** — `runtime/qulla_warm.py`: the only place the qulla
  scan runs (vendored engine, lazy pandas/numpy, fail-closed);
  proposals into cache.
- **Earnings** — `runtime/earnings_warm.py`: earnings calendar for
  earnings-aware sleeves via `context.extra["earnings"]`.
- **Alpaca door** — `runtime/alpaca_door.py`: the ONLY network client
  for trading/market data; paper API; credentials via ALPACA_KEY_ID /
  local-alpaca-paper config + Secure Vault `hsurr:*` surrogate; the
  door refuses live env.
- **DigitalOcean:** searched v2 docs/configs and femto-lean desk
  docs for any DigitalOcean-hosted component — **none found**
  (searched: v2 *.md + config/*.json, femto-lean desk/ + README;
  excluded: femto-lean worktrees). Recorded as not-found, never
  invented. If a DO component exists, it is outside the recorded
  corpus and must be surfaced by the owner or a later census.

## 6. Baseline measurement — v2 complete evaluation path (BEFORE)

Method (Efficiency Breakthrough steps 1–3): v2 copied to
`/tmp/v2base/desk` (v2 tree untouched — read-only boundary), full
71-sleeve roster evaluated once through v2's own `runtime.runner`
(sequential subprocess per sleeve) on v2's real cache, asof
2026-10-23T19:00:00Z (Fri 15:00 ET, RTH), intents dispatched through
`Dispatcher.process_inbox` against the fake broker (paper door not
exercised in scope phase — broker round-trip cost is therefore NOT
in this table and is labeled as such). Raw output:
`BASELINE-V2-MEASURE.json` in this repo.

Machine: 2 vCPU (AMD EPYC 9D25), 7.7 GiB RAM, Python 3.12.3.
Conditions caveat: the box was memory-pressured during measurement
(free RAM ~0.7–3.5 GiB across runs); figures are representative of
THIS box under load, not a quiet-box best case. v2's own audit
measured saty_gpt_v02 at 4.83s on a quieter box — the spread itself
is evidence: per-evaluation cost is uncached and load-sensitive.

| Stage | Measured | Share of cycle |
|---|---|---|
| Full-roster evaluation wall (71 sleeves, sequential) | **85.26 s** | 100% |
| Sleeve evaluation — saty_gpt_v02 alone | 44.75 s | **52%** |
| Sleeve evaluation — next 4 (raschke_rre 2.70, saty_gpt_v03 2.53, raschke_pf3 2.32, saty_day 1.83) | 9.38 s | 11% |
| Sleeve evaluation — remaining 66 (median 0.384 s each) | ~31 s | ~37% |
| — of which process spawn + interpreter + runtime imports | ~0.135 s × 71 ≈ 9.6 s | ~11% |
| Cache load (in-process, full cache: 138,700 bars / 378 series) | 1.56 s per full read; every sleeve subprocess re-reads its own slice from disk JSON — no shared snapshot | (inside eval) |
| Journal write (append_line, 1,000 appends) | 0.067 s | negligible |
| Dispatch (21 intents, fake broker, local) | 0.023 s | negligible locally; broker RTT unmeasured |
| Result quality | 70 ok / **1 error** (iron_condor: TypeError float(tuple) on this cache/asof — observed baseline defect, recorded, NOT fixed in v2 per read-only boundary) / 21 intents | — |

### Ranked bottlenecks (dominant first)
1. **Single-sleeve CPU re-derivation — saty_gpt_v02 = 52% of the
   cycle.** It resamples 5Min SIP bars into its 10m/1H clocks and
   re-derives over ~1,000-bar warmup history inside every evaluation,
   in its own subprocess, with no shared pre-computation. Under load
   it swung 4.83s (v2 audit, quiet box) → 44.7s (this measurement).
2. **Sequential subprocess-per-sleeve architecture.** Cycle wall =
   the SUM of all sleeves; zero parallelism on a 2-vCPU box; at the
   v3 roster of 156 the same shape projects to ~3 min/cycle, and at
   the 400-sleeve design target it cannot fit the fastest cadences
   (60s sleeves exist). Roster growth is linear wall growth.
3. **Repeated per-sleeve cache parsing; no single immutable
   snapshot.** Each of 71 spawns re-reads and re-parses its bar slice
   from disk JSON (full-cache parse = 1.56s in-process), and
   spawn+imports alone cost ~9.6s/cycle (~11%). The same bars are
   parsed dozens of times per cycle, and two sleeves in one cycle
   can observe different cache states (warmers write concurrently).

Non-bottlenecks (measured, do not optimize): journal appends and
local dispatch logic are three orders of magnitude below the cycle.

## 7. Architecture decisions (v3)

1. **Worker pool, not subprocess-per-sleeve-per-cycle.** A bounded
   pool of long-lived worker processes (pool size = vCPU count,
   2 here; configurable), each worker recycled after a bounded number
   of evaluations (native-memory hygiene per field-manual §11).
   Per-sleeve hard timeout preserved (v2's isolation property: a
   wedged sleeve is marked degraded and never blocks the roster).
   Sleeve code runs identically; only the execution chassis changes.
2. **Single immutable snapshot per cycle.** Producers build one
   content-hashed snapshot (bars/quotes/options/kraken/tensor/qulla/
   earnings + account) per cycle; the hash is stamped on every
   evaluation, intent, and journal row in that cycle. Workers read
   the snapshot read-only (shared memory / read-only mapping, never
   per-sleeve re-parse of the full cache). A cycle never observes a
   half-written warm.
3. **Producer registry contract.** Every producer registers: name,
   cadence, output keys, freshness SLA, fail-closed behavior. The
   registry is the single source of truth for what data exists;
   a sleeve needing an unregistered or stale input fails closed and
   the terminal names it. Producers from census D carry over, plus:
   **lazarus_fire_ingest** (research-lane drop → validated, hashed
   fire snapshot; see decision 6) and **best_setups lane** (§4).
4. **Dispatcher.** Single authoritative writer to the paper door.
   Per-sleeve slice buying-power checked at intent time (v2 property,
   preserved); intents carry snapshot hash + sleeve id + idempotency
   key (sleeve + cycle + intent ordinal); duplicate submission is
   impossible by construction. Door refuses live env. Flatten and
   flatten_time_et semantics carried from v2 config unchanged.
5. **Journals.** Append-only per-sleeve JSONL (eval, intent, fill,
   exit, defect events) + one dispatcher journal; rotation bounded
   (v2 D8 property). No global ledger re-read on the hot path;
   state is derived per-sleeve from its own journal + broker
   reconcile.
6. **Research-lane isolation.** Lazarus lanes never execute research
   code and never read the desk-research. They consume ONLY the
   ingested fire snapshot (schema-validated: sleeve_id, symbol,
   side, fire time, source hash). Position management (entries on
   fresh fires, exits/stops/holds per the fidelity ledger) is desk
   code; signal generation stays in the research lane. A stale or
   absent fire snapshot = fail-closed, named in the terminal.
7. **Scheduler.** Thin cadence loop (v2 §3f shape): fire-and-forget,
   overlap = skip, per-sleeve due-times from config cadences, cycle
   health roll (evaluated / timed-out / errored / stale-input counts)
   written every cycle for the terminal and the inspections.
8. **Capacity shape.** Design load 400 sleeves/cycle inside the
   fastest cadence (60s) on this box class; synthetic proof at 800
   (fixture sleeves, labeled SYNTHETIC — never reported as
   production load, per doctrine).

## 8. Acceptance matrix (finite; every row must PASS for GREEN)

| # | Row | Proof required |
|---|---|---|
| A1 | Independence | v3 runs end-to-end with v2/femto-lean trees renamed away; no runtime import or path reaches outside the v3 repo except the credentials route and the fire-ingest drop |
| A2 | Roster fidelity | 156 sleeves in config (71 v2 ids exact + 85 Lazarus ids per §3.2); manifest test binds each to its source row; parked set = source-off set, named |
| A3 | No inflated sleeves | Roster contains none of: legacy_exit, the 2 Q07 index entries, the 6 waiting-list placeholders, the 6 duplicate-strategy ports (present only as lineage aliases) |
| A4 | Port fidelity (v2 71) | Every sleeve fixture-drives deterministically on recorded inputs; saty_sol byte-identical (sha256); intent/exit parity vs v2 fixture outputs on the same inputs |
| A5 | Port fidelity (Lazarus 85) | Fidelity ledger complete for all 85 (no missing-fields cell empty — a field is either specified or the sleeve is frozen as fire-consumer with that freeze recorded); each lane fixture-drives on recorded fires |
| A6 | Capacity — design | 400-sleeve roster completes a full cycle inside 60s on this box, zero wedged evaluations. Composition as proven (CURE3 correction, 2026-10-24): 133 genuine active sleeves evaluated + 267 SYNTHETIC fixture sleeves (23 parked genuine sleeves are named, not evaluated) — the earlier "156 real" phrasing overstated the genuine share |
| A7 | Capacity — synthetic | 800 fixture sleeves complete a cycle; result labeled SYNTHETIC in every report; not used as production evidence |
| A8 | Best Setups identity | Vendored files sha256-match §4 pins; a gate-wired blocker fails on any byte drift; setups outputs produced on v3 state and present in the v3 terminal snapshot with identical keys. CURE3 (2026-10-24): generation half cured — desk3/setups_generate.py translates v3 journals into a curator state dir and runs the original generator read-only; live doc generated from v3 state 2026-10-24 (see DEPLOY-REPORT cure-3 addendum) |
| A9 | Autonomy within paper scope | A full RTH session runs unattended: scheduler cycles, producers refresh, evaluations dispatch, no manual step; any human-only action is named, not silently required. CURE3 (2026-10-24): the empty-bars root cause is cured (desk3/warm.py real SIP warm + per-key fed marking); the RTH fill itself remains OPEN by name until the first supervised market-hours dispatch session (Mon 2026-10-26) — a Saturday cannot prove it |
| A10 | Paper-only enforcement | Door refuses live env (test proves refusal); no real-money endpoint string exists in the tree (gate-wired scan) |
| A11 | Research-lane isolation | No v3 code path reads the desk-research or executes research-lane code; fire ingest validates schema + hash and fails closed on stale/absent/malformed fires (tests for all four) |
| A12 | Efficiency before/after | The §6 baseline measurement re-run identically on v3 (same cache content, same asof, same roster subset): cycle wall and top-stage attribution reported side-by-side; v3 cycle < v2 cycle with the dominant constraint (per-sleeve re-derivation + serialization) structurally removed, not hidden |
| A13 | Fault proof | Kill a worker mid-cycle: cycle completes, sleeve marked degraded, next cycle recovers it; corrupt one snapshot: cycle fails closed before any dispatch |
| A14 | Restart proof | Kill the desk mid-session, restart: state rebuilt from journals + broker, no duplicate orders (idempotency keys), no lost fills |
| A15 | Reconcile proof | Broker positions/cash vs journal-derived state reconciled at session start and end; a planted discrepancy is detected, named, and halts new entries for the affected sleeve only |
| A16 | Backups + restore | Repo + state pushed to GitHub; restore into a clean directory from GitHub alone reproduces config, journals, and terminal state; restore is executed, not assumed (eval-case 12) |
| A17 | Terminal freshness | Terminal snapshot carries snapshot-hash + generated-at; a staleness test proves the surface shows its age and the health roll names stale producers/sleeves |
| A18 | GitHub save | Final tree committed and pushed; the pushed head is the tested head (final-artifact integrity: any post-test change re-runs affected proof) |
| A19 | Regression blockers + BUGLOG | Every defect found after scope ships with a gate-wired blocker (fails on old, passes on new, fail direction proven) and a BUGLOG entry; the gate runs green on the final tree |
| A20 | Baseline defect disposition | The iron_condor float(tuple) error observed in §6 is either reproduced-and-cured in the v3 port (with blocker) or carried as a named OPEN defect — never silently inherited |

## 9. Open items carried forward (named, not hidden)
- the desk-research fire files inaccessible from this box (§3.4):
  Lazarus lanes are fail-closed until the ingest route is exercised
  with a real pushed snapshot — A5/A11 proof depends on it.
- Waiting-list 6 + Q07 index 2 + legacy_exit: excluded from the
  roster by §3.2; they re-enter only on an owner/research-lane spec.
- s_1wsw_stress has "no live source yet" upstream; s_rules_* rule
  set unenumerated in any source in hand (fire-consumer freeze
  pre-registered in §3.5).
- DigitalOcean component: not found in the searched corpus (§5).
- Broker round-trip latency is unmeasured (scope phase used the fake
  broker); A9/A12 measure it against the paper door in-session.
