# INVESTANDBEFREE-DMAC VARIANTS — BUILD REPORT (2026-10-29)

Four variants of `investandbefree_dmac` built and installed per
INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29.md (FROZEN),
following the Trullas variant family pattern of 2026-10-29.
Edge UNPROVEN for every variant; no backtest claimed; each
variant's live paper record is its test, no variant is judged
on fewer than 30 of its own trades, and the yardstick is
percent gain versus SPY and QQQ over the same window.

## SCOPE (InfinityBlade)

- Surface: parameterized base core, four thin variant sleeves
  with adapter pairs, four config rows, one producer key, the
  variants spec doc, one gate-wired blocker file, four install
  proofs, BUGLOG entry, this report, roster pins 329 to 333.
- Constraints: fenced dirty files untouched (named below); the
  Tensor engine and saty_sol untouched; the base sleeve's
  frozen rules unchanged, proven on its golden fixtures; each
  variant differs in exactly one axis.
- Outcome: roster 333 with each variant exactly once,
  parked=false, paper_only, live paper from install.
- Proof: pre/post base golden runs, fail-first mutations, full
  gate run on the final tree (below).
- Edges: intraday feeding depends on the warm SPY/QQQ 5Min
  product (present, 60 days) and the options producer, both
  shared with the base.

## What was built

- `sleeves/investandbefree_dmac.py` — the base core gained a
  frozen `DmacParams` bundle (defaults are the frozen base
  values field for field), a generic stack evaluator, a generic
  clock-anchored intraday aggregator from closed 5-minute bars,
  and parameterized contract selection and management. See the
  identity proof below: the base core file's hash CHANGED.
- `sleeves/investandbefree_dmac_intraday.py` — V1: stack
  15m/30m/4H from 5Min bars, 30m entry, dominance 4H > 30m >
  15m requiring dominant == 30m direction, expiry >= 5 days,
  flat_by_close at 15:55 ET in the sleeve as well as in config,
  cadence 300.
- `sleeves/investandbefree_dmac_dailyonly.py` — V2: 4H layer
  removed (weekly + daily only).
- `sleeves/investandbefree_dmac_deep.py` — V3: strike at least
  2% ITM (calls highest strike <= 0.98 x spot; puts lowest
  strike >= 1.02 x spot), expiry >= 45 days.
- `sleeves/investandbefree_dmac_premacd.py` — V4: premium-MACD
  exits. Entries base-identical; the held contract's mid is
  accrued once per cycle into the sleeve state; after 40
  samples a premium MACD-E (12/26/9) cross against replaces
  both the dominant-break and runner-cross exits; before 40
  samples the base exits apply; stop/partial/5-DTE unchanged;
  the series resets on a new contract.
- Adapter pairs under `adapters/` and `adapters3/` per variant
  (the base adapter pair itself is byte-identical to the base
  install). V2's adapter does not request 1Hour bars; V1's
  adapter fetches SPY/QQQ 5Min bars; V4's adapter carries the
  accrued premium samples from the persisted plan into the
  position state.
- `desk3/producers_g4.py` — one producer key added:
  `bars:SPY:5Min` (the warm product already serves SPY 5Min;
  `bars:QQQ:5Min` was already registered). No warm window
  widening was needed: the on-disk warm product holds SPY 5Min
  8145 rows and QQQ 5Min 8154 rows (60 calendar days), which
  aggregates to roughly 1500 15-minute, 770 30-minute and 60
  4H bars per symbol, far beyond the 34-bar MACD warmup.
- `INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29.md` — frozen
  family spec with provenance labels and the premacd deviation
  reasoning.
- `tests/test_investandbefree_dmac_variants_blockers.py` — 22
  blocker tests, gate-wired by the discover pattern.
- `proof/install/<variant>.json` for all four variants, in the
  base install proof format.

## Every file touched

Created: INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29.md,
sleeves/investandbefree_dmac_intraday.py,
sleeves/investandbefree_dmac_dailyonly.py,
sleeves/investandbefree_dmac_deep.py,
sleeves/investandbefree_dmac_premacd.py,
adapters/investandbefree_dmac_intraday.py,
adapters/investandbefree_dmac_dailyonly.py,
adapters/investandbefree_dmac_deep.py,
adapters/investandbefree_dmac_premacd.py,
adapters3/investandbefree_dmac_intraday.py,
adapters3/investandbefree_dmac_dailyonly.py,
adapters3/investandbefree_dmac_deep.py,
adapters3/investandbefree_dmac_premacd.py,
tests/test_investandbefree_dmac_variants_blockers.py,
proof/install/investandbefree_dmac_intraday.json,
proof/install/investandbefree_dmac_dailyonly.json,
proof/install/investandbefree_dmac_deep.json,
proof/install/investandbefree_dmac_premacd.json, this report.
Modified: sleeves/investandbefree_dmac.py (parameterization
only, see identity proof), config/sleeves.json (four appended
rows; roster 329 -> 333), desk3/producers_g4.py (one producer
key), BUGLOG_2026-10-29.md (install entry appended), and the
roster-count pins 329 -> 333 in
tests/test_deploy_blockers.py,
tests/test_harden_batch1_blockers.py,
tests/test_milkman_0dte_20261027_blockers.py,
tests/test_teddy_orb_spy_blockers.py,
tests/test_grok_sr_spy_blockers.py,
tests/test_trullas_variants_blockers.py,
tests/test_investandbefree_dmac_blockers.py, and
tests/test_przm_recreation_blockers.py (the concurrent PRZM
lane's untracked file; only its roster-count assertion
changed, and it is left untracked as found).
No fenced file was touched, staged, reverted, or committed:
the pre-existing dirty set (BUGLOG_2026-10-27.md,
STAGE-C-PROGRESS.md, adapters/laz8_common.py,
desk3/aster_batch1.py, desk3/dispatcher.py, desk3/netfetch.py,
tests/test_aster_batch1_blockers.py,
tests/test_edge_batch5_blockers.py, the untracked przm_*
sleeves/adapters and broker-422 test files) is as found,
apart from the single named pin line above.

## Identity proof (base sleeve)

- Pre-refactor: base blockers 28/28 OK; base core sha256
  9f6268daec6520e67ffa95da4d971b6c6ad76ee41362a4afd1ab31ee635daf9f.
- Post-refactor: base blockers 28/28 OK with identical
  decisions; the family blocker file re-proves the golden
  entry directly (crossover fixture: occ
  SPY261128C00239000, strike 239.00, expiry 2026-11-28,
  qty 4 = floor(2000/500), trigger=crossover, byte-identical
  reason string).
- PLAINLY: the base core file's hash changed, to
  2909dc8a208b3b84ecf1c4b4ce01d705b93cc5fc5bdd68dc2017d04949d18086,
  due to the parameterization refactor alone. The base adapter
  pair did NOT change: adapters/investandbefree_dmac.py
  6c39ed5f7750b3cca838fa1865394410bcbe847328452ca7af2243a6345b0061
  and adapters3/investandbefree_dmac.py
  5aee4407cc0ed21e22a325645feb250ea1773c30a7f6ef4bce8f107979732d04,
  both byte-identical to the base install proof.

## Feeding proof (per variant)

- All four: blocker TestAdapterDrives drives each variant's
  real adapters3.evaluate path on a full snapshot view.
  intraday: exactly one entry, SPY261028C00140000 qty 4 (the
  5-day expiry), with dominant=h4 and trigger=crossover proven
  at the core on the same fixture. dailyonly: exactly one
  entry SPY261128C00239000 qty 4. deep: exactly one entry
  SPY261213C00234000 (2% ITM strike at the 45-day expiry)
  qty 4. premacd: exactly one entry SPY261128C00239000 qty 4,
  with dmac_state.json round-tripping premium_samples=[] and
  premium_occ set.
- Intraday raw feeding: the desk warm product on disk at build
  time holds SPY|5Min 8145 rows and QQQ|5Min 8154 rows (60
  calendar days), pinned by a blocker test (>= 3000 rows per
  symbol); the producer key bars:SPY:5Min was added at this
  install so the registry marks the slice produced.

## Gate result

Full gate: `run_regression_blockers.sh` exit code 0 on the
final tree; unittest discover reported "Ran 1428 tests, OK"
(the pre-install tree ran 1406; +22 new family blockers =
1428, matching exactly). The family blocker file alone:
22/22 OK; base plus family combined: 50/50 OK. Fail-first:
the deep call threshold mutation 0.98 -> 0.90 failed 3 deep
tests, and the premacd warmup mutation 40 -> 4 failed the
warmup-fallback test; both were restored byte-identical
(sha256 verified) and re-proven.

## Deviations

- V1 intraday parameters labeled recreated in the variants
  spec: the 15/30 stack operational form aggregated from
  5-minute bars (the desk serves no native 15Min/30Min bars
  for SPY), the 5-day expiry bound, the 15:55 flat time.
- V2 is a desk deviation run as a controlled variant: the
  extracted 4H stack member removed to isolate it.
- V3 strike and expiry rules labeled recreated.
- V4 premacd: entries stay underlying-based (deviation, with
  reasoning in the variants spec: no honest pre-entry premium
  series exists across strike rolls); warmup deviation: base
  exits apply before 40 accrued samples.

## Paper-trade readiness (independent verification, 2026-10-29)

Verifier: independent phase, not the builder. Verdict:
**NOT READY — two blocking findings (F1, F2 below).** Everything
else on the verification checklist passed; the failures are
named with their evidence and cures, neither cure applied by
this phase (its scope is verification plus this appendix).

### What passed

- Roster and fences: 333 rows; base plus the four variants each
  exactly once, parked=false, slice 10000/10000, session rth,
  cadence 300 intraday / 3600 others, flat_by_close true only
  for intraday (15:55). Commits c7a5329 + 76d8ba7 touch only
  the scoped family files plus the named roster-pin lines; the
  remaining dirty set is exactly the pre-existing fenced set.
- Gate, re-run by the verifier: `run_regression_blockers.sh`
  rc=0 on the final tree; an independent unittest discover
  reported "Ran 1428 tests, OK" (1406 pre-install + 22 family,
  exact). Base + family blocker files: 50/50.
- Base identity: the verifier re-ran the golden crossover
  fixture through the installed adapters3 path: entry
  SPY261128C00239000, strike 239.00, expiry 2026-11-28, qty 4,
  trigger=crossover — identical to the pre-refactor golden.
  Base core sha256 is 2909dc8a… (changed by the parameterization
  refactor alone, as stated in the BUGLOG and above); the base
  adapter pair is byte-identical to the base install
  (6c39ed5f… / 5aee4407…).
- Single-axis fidelity, measured from the effective PARAMS of
  each variant against PRIMARY_PARAMS: intraday differs only
  in stack_order (h4/m30/m15), entry_tf m30, min_dte 5,
  flat_by_close true (its one axis: stack + session shape, per
  the frozen spec); dailyonly only in stack_order
  (weekly/daily); deep only in min_dte 45 + strike_mode
  deep_itm_2pct (its one axis: contract construction); premacd
  only in premium_macd true (warmup stays the base-default 40).
  No second-axis difference exists in any variant.
- Fail-first, re-proven by the verifier on a site the build
  did not use: intraday min_dte 5 -> 30 failed exactly 3
  intraday tests (axis pin, 30m entry, adapter drive); the
  file was restored byte-identical (sha256 0364f352… before
  and after) and base + family re-passed 50/50.
- Live cycle: the running desk (dispatch mode) rebuilt to
  roster 333 and completed its first 333 cycle at
  2026-10-29T17:04:55Z (status ok, 41 intents dispatched
  desk-wide). Base, dailyonly, deep and premacd all evaluated
  FED / status ok with adapter_eval state "scanning". No
  reconcile_halt event exists in any sleeve journal, and no
  desk-wide halt condition was found in the cycle state; the
  capital epoch is present. Orders do reach the paper
  dispatcher desk-wide.
- Real-data drives: the verifier drove all five adapters3
  entrypoints on that cycle's actual producer-built snapshot
  (hash 0df4385f…, asof 2026-10-29T17:04:55Z, the exact worker
  view and ctx shape). All five evaluated without error,
  state "scanning", zero intents — explained by the census on
  the same snapshot, not by missing data: SPY/QQQ daily family
  had 345 closed daily bars, 71 closed weekly, daily -1 with
  dominant=daily (-1) for both symbols and NO crossover or
  curl trigger on the last closed daily bar; intraday had
  8,145 / 8,154 closed 5Min rows aggregating to 1,102 m15,
  551 m30 and 42 complete 4H bars per symbol, all three
  timeframes -1, dominant=h4 (-1) agreeing with m30, and NO
  trigger on the last closed 30-minute bar. Intent shape is
  proven dispatcher-ready by the fixture adapter drives
  (kind=entry, symbol=OCC, side=buy, qty 4, order_type=limit
  at the ask, position_intent=buy_to_open, time_in_force=day).

### F1 (BLOCKING, all five sleeves): live-path entries size to zero

Every family adapter (the base's and all four variants')
derives sizing equity solely from `ctx.slice`
(`equity = float((ctx.slice or {}).get("capital_usd") or …)`).
The live worker view is the snapshot data dict, and the
snapshot carries NO `slice` key (verified on the 17:04 cycle
snapshot: no `slice` key and zero occurrences of
`capital_usd` in the file); no producer emits one, and the
worker/pool injects none. So in the real cycle equity is 0,
`qty_for_position` returns 0, and any entry signal is blocked
as `sizing_zero_or_cap`. Proof at the boundary: the verifier
drove the base adapters3 path on the golden crossover fixture
with the view in the exact live shape (the `slice` key the
blocker fixtures hand-supply deleted) — result: zero intents
with last_evaluation blocked SPY=`sizing_zero_or_cap`, where
the same fixture with a slice emits the qty-4 entry above.
The gate-wired blocker drives all supply `slice` by hand, so
the gate is green while the live path cannot size an entry.
Exits are unaffected (the manage path does not use equity).
This same derivation predates the variants in the base
adapter (byte-identical to the base install) and follows the
desk-wide SnapshotSleeveContext adapter pattern, but for this
family it is curable inside family files. Cure (not applied
here): give each family adapter a sizing-equity fallback to
its own $10,000 slice when `ctx.slice` is absent (the aster
adapters' `or 10000.0` convention), and add a gate-wired
blocker that drives adapters3 on a slice-less, live-shaped
view and requires the qty-4 entry. Until that lands, NO
family sleeve (base included) can enter a paper trade on the
live path, however clean its signals are.

### F2 (BLOCKING for intraday live feeding): UNFED in the live cycle

In the first 333 cycle, investandbefree_dmac_intraday was
UNFED, missing `bars:SPY:5Min` (its journal records the unfed
event; health carries the same state). The family code is
proven correct from a fresh process: BarsProjection with the
committed `_BARS_TF_KEYS` emits the `bars:SPY:5Min` marker
from the on-disk warm product (SPY 8,145 rows) at a
cycle-time `now`. Cause: the live runner process (pid 969,
started 2026-10-29T15:59Z) predates the producers_g4.py edit
(16:59Z) that added the key; the ConfigWatcher desk rebuild
re-imports the module from the running process's cache, so
the producer registry in the live process still lacks the
key. Cure (desk operations, outside family files, not
applied here): restart the runner process, then confirm
intraday shows FED in health.json on the next cycle. The
verifier's own adapters3 drive above proves the intraday
sleeve evaluates real 5Min data correctly once fed.

### Named data condition (not a family defect)

The live warm product on disk holds only 360 SPY/QQQ 1Hour
rows, aggregating to 22 complete 4H bars — below the 34-bar
MACD warmup — so the daily family's 4H alignment reads None
on live warm data (dominance still resolves to daily, which
is aligned -1, so evaluation is meaningful). This is the
same warm state the base install recorded; the widened
hourly window lands at the next warm fetch.


## Repair: F1 slice fallback cured; F2 carried OPEN (2026-10-29)

Repair phase for the independent verification above (verdict
NOT READY, findings F1 + F2). Scope: family files only; no
golden expectation changed; no fenced file touched.

### F1 — CURED at the source, proven at the live boundary

- Cure: all five family adapters
  (`adapters/investandbefree_dmac.py` plus the four variant
  adapters) gained `SLICE_FALLBACK_USD = 10000.0`. Sizing
  equity is now `capital_usd` or `cash_usd` or
  `SLICE_FALLBACK_USD` — the aster adapters' `or 10000.0`
  convention named by the verifier. A supplied slice still
  governs when present; the `params["equity"]` override is
  unchanged; exits never used equity and are untouched.
- Boundary proof (the verifier's own failing drive, re-run):
  the golden crossover fixture driven through
  `adapters3.investandbefree_dmac` in the exact live view
  shape (the `slice` key deleted) emitted ZERO intents on the
  pre-cure code and now emits exactly the golden entry:
  SPY261128C00239000, strike 239.00, expiry 2026-11-28,
  qty 4, limit at ask 5.00, buy_to_open, with a reason string
  byte-identical to the with-slice drive.
- Blockers (gate-wired, 6 new): base file TestSliceLessLiveView
  (slice-less drive emits the qty-4 entry; a supplied 4000
  slice still governs at qty 2) and one slice-less adapter
  drive per variant in the variants file (dailyonly
  SPY261128C00239000 qty 4; deep SPY261213C00234000 qty 4;
  premacd SPY261128C00239000 qty 4; intraday
  SPY261028C00140000 qty 4). Fail-first: all 5 slice-less
  tests FAILED on the pre-cure adapters (zero intents each)
  and pass after the cure; the mutation
  SLICE_FALLBACK_USD 10000 -> 4000 in the base adapter failed
  exactly the base slice-less test and was restored
  byte-identical (sha256 3c83bb4e… before and after).
- Hashes, stated plainly: the cure changes all five
  `adapters/` files — base 6c39ed5f… -> 3c83bb4e…, dailyonly
  4296c565… -> 21d09135…, deep 79b018a8… -> 48d889d9…,
  intraday e4cf2e0a… -> 30048cf0…, premacd 128a4c47… ->
  9ac17abe…. So the base adapter is NO LONGER byte-identical
  to the base install (that identity held through the
  parameterization refactor and ends with this cure, which is
  the base adapter's first functional change). The base core
  `sleeves/investandbefree_dmac.py` is untouched
  (2909dc8a…) and every `adapters3/` entrypoint is
  byte-identical, including the base's (5aee4407…). The
  base's frozen rules did not change: base blockers re-prove
  the golden entry identically, with and without a slice.
- Install proofs refreshed for all five sleeves (adapter and
  blocker-file hashes, repair records, gate counts):
  proof/install/investandbefree_dmac.json and the four variant
  proofs. In the same refresh, the base proof's recorded core
  hash — stale at 9f6268da… since the variants parameterization
  refactor — was aligned to the current core (2909dc8a…, as the
  variant proofs already record); the core itself was not
  touched by this repair. BUGLOG_2026-10-29.md entry
  INVESTANDBEFREE-DMAC-SLICE-FALLBACK-20261029.

### F2 — OPEN (desk operations; family side re-proven)

The intraday UNFED state is NOT cured by this repair and is
not claimed cured. The family code was re-proven correct in
this phase from a fresh process: BarsProjection with the
committed `_BARS_TF_KEYS` emits the `bars:SPY:5Min` marker
(SPY 8,159 warm rows) at 2026-10-29T17:24Z. The live runner
(pid 969, started 2026-10-29T15:59Z, before the 16:59Z
producers_g4 edit) still serves its cached pre-edit registry,
and health.json (cycle 2026-10-29T17:04:55Z) still shows
investandbefree_dmac_intraday UNFED missing bars:SPY:5Min.
Cure, outside this repair's family-file scope: restart the
runner process, then confirm intraday shows FED in
health.json on the next cycle. Until that FED observation
exists, F2 stays OPEN by name on every report.

### Gate after the repair

Full gate: `run_regression_blockers.sh` exit code 0 on the
final tree; unittest discover reported "Ran 1434 tests, OK"
(1428 at the variants verification + 6 new F1 blockers,
matching exactly). Base + family blocker files: 56/56 OK
(base 30/30, variants 26/26). Roster unchanged at 333; the
four variant axes and every other verification result above
are unaffected by the cure (single-site sizing-equity change
in the adapters only).

### Repair verdict

F1 CURED with boundary proof on the final tree. F2 OPEN,
named above with its exact unblock step (runner restart +
FED confirmation), which is a desk-operations action outside
this repair's family-file scope. Family readiness is
therefore PARTIAL until F2's FED observation lands; no family
file change remains outstanding for either finding.

## Re-verification after repair (2026-10-29, independent)

Verifier: independent re-verification phase, not the repairer.
Verdict: **PARTIAL. F1 CURED and re-proven; F2 still OPEN and
blocking only investandbefree_dmac_intraday live feeding.**
No other failure found.

- Roster and fences: 333 rows; base plus four variants each
  exactly once, parked=false, paper_only, slice 10000/10000,
  session rth, cadence 300 intraday / 3600 others,
  flat_by_close true only for intraday (15:55). Repair commits
  dfbe3af + 8e1b646 touch only the five family adapters, the
  two family blocker files, the five install proofs, the
  BUGLOG and this report. Remaining dirty set is exactly the
  pre-existing fenced set (plus the Oct 28 wtest_24155 file).
- Base identity: core sha256 2909dc8a... unchanged by the
  repair; adapters3 base 5aee4407... byte-identical; base
  adapter is now 3c83bb4e... (its F1 cure change, plainly
  stated in the repair section and BUGLOG; it is no longer
  byte-identical to the original base install). All five
  install proofs' recorded hashes match the files on disk.
  Golden crossover re-proven identically (blockers below).
- Gate, re-run by this verifier: run_regression_blockers.sh
  rc=0 on the final tree; independent unittest discover
  reported "Ran 1434 tests, OK" (1428 + 6 F1 blockers, exact).
  Base plus family blocker files: 56/56 (base 30/30,
  variants 26/26).
- F1 boundary, re-proven: all five adapters carry
  SLICE_FALLBACK_USD = 10000.0; the slice-less live-shaped
  adapter drives pass for all five sleeves (base, dailyonly
  and premacd SPY261128C00239000 qty 4; deep
  SPY261213C00234000 qty 4; intraday SPY261028C00140000
  qty 4), and a supplied slice still governs sizing.
- Fail-first, re-proven on a site neither prior phase used:
  SLICE_FALLBACK_USD 10000 -> 4000 in the dailyonly adapter
  failed exactly its slice-less drive (qty 2 vs expected 4);
  restored byte-identical (sha256 21d09135... before and
  after) and base plus family re-passed 56/56.
- Single-axis fidelity, measured from each variant class
  PARAMS against PRIMARY_PARAMS: intraday differs only in
  stack_order (h4/m30/m15), entry_tf m30, min_dte 5,
  flat_by_close true (its one axis per the frozen spec);
  dailyonly only in stack_order (weekly/daily); deep only
  in min_dte 45 plus strike_mode deep_itm_2pct (its one
  axis: contract construction); premacd only in
  premium_macd true (warmup stays 40). No second-axis
  difference in any variant.
- Live cycle and F2: journals show cycle 1 (17:04:55Z) and
  cycle 2 (17:13:54Z) with base, dailyonly, deep and premacd
  FED / status ok / adapter_eval scanning, zero intents (no
  trigger on the last closed bars, as censused in the first
  verification), no reconcile_halt in any family journal,
  capital epoch present. Intraday was UNFED missing
  bars:SPY:5Min in BOTH cycles, and health.json still shows
  that state. The live runner (pid 969, started 15:59Z)
  still predates the 16:59Z producers_g4 edit and has NOT
  been restarted. Family code re-proven correct from a
  fresh process in this phase: BarsProjection with the
  committed _BARS_TF_KEYS emits bars:SPY:5Min and
  bars:QQQ:5Min from the warm product (SPY 5Min 8159 rows).
  Cure remains desk operations only: restart the runner,
  then confirm intraday FED in health.json on the next
  cycle. Until that FED observation exists, F2 stays OPEN
  by name and the family readiness stays PARTIAL: four
  sleeves plus the base are paper-trade ready on the live
  path; intraday is ready in code and fixture drives but
  cannot evaluate live until the runner restart.
- Named data condition unchanged: warm SPY/QQQ 1Hour holds
  362 rows (about 22 complete 4H bars, below the 34-bar
  MACD warmup), so the daily family's live 4H alignment
  reads None and dominance resolves to daily; not a family
  defect, as recorded at the base install.
