# TRULLAS-VARIANTS-BUILD — variant family build checkpoint

Commission (the desk owner, 2026-10-29): build multiple variants of the Trullas
divergence algorithm, varying the manual/discretionary joints to sample
the space his eye moves through. Frozen primary spec:
`~/workspace/goals/ai-top50-pattern-study/files/TRULLAS-SPEC-2026-10-25.md`
(v1.0 FROZEN, read in full at inspect). Primary sleeve:
`sleeves/trullas_divergence.py` + `adapters/trullas_divergence.py` +
`adapters3/trullas_divergence.py`, live paper since 2026-10-26 (install
report `TRULLAS-SLEEVE-BUILD.md`, proof `proof/install/trullas_divergence.json`).

Hard rails for every phase: primary behavior must not change (byte-identical
preferred; a shared-code refactor only if truly necessary, with primary
outputs proven identical before/after on a fixed bar fixture, stated
plainly). NO BACKTEST for any variant (the desk owner cancelled the Trullas
backtest; the live paper record is the test). Paper only. Each variant is
its own roster sleeve, own $10,000 slice, own state, own record. Each
variant differs from the primary in exactly ONE named joint.

---

## PHASE inspect — DONE 2026-10-29

### SCOPE

- Surface inspected: frozen spec; primary strategy, both adapters, its
  blocker tests (`tests/test_trullas_blockers.py`, 12 tests), install
  proof, config row, producer registry, warm-bars product, roster pins.
- Changed in this phase: this checkpoint file only.
- Proof inputs: primary file sha256 today equals install proof exactly
  (strategy 2c8691e7…, adapter da8ebf00…, adapters3 94debe96…,
  blockers 0c37e8bf…) — the primary is untouched since install.
  Live state file `state/trullas_divergence/trullas_state.json` shows
  session 2026-10-29, day counters fresh — the primary is live today.

### How the primary is parameterized today: it is not

- Every strategy parameter is a module-level constant in
  `sleeves/trullas_divergence.py`: SYMBOL="QQQ", PIVOT_K=5,
  MIN/MAX_SEPARATION=10/120, MACD(12,26,9) read on the MACD line,
  RSI_LENGTH=14, TICK=0.01, ENTRY_LEVEL=0.236, TP1_LEVEL=0.382,
  TP2_LEVEL=0.618, ENTRY_EXPIRY_BARS=30, entry window 09:30–11:00 ET,
  FLAT_TIME=12:00, MAX_ENTRIES_PER_DAY=5, DAILY_LOSS_STOP_PCT=0.0075,
  UNIT_RISK_PCT=0.0025, NOTIONAL_CAP_PCT=0.25.
- `CONFIG = SleeveConfig(sleeve_id="trullas_divergence", cadence_s=60,
  universe=("QQQ",), risk_pct=0.0025, parked=False)` is hard-coded in
  the strategy module.
- The config row's `params` is `{}` and is NOT a strategy channel: the
  adapter honors only `params["equity"]` and
  `params["extra"]["trullas_state"]` overrides. The sleeve reads nothing
  from config except, via the adapter, slice equity
  (`ctx.slice.capital_usd`) and its persisted `trullas_state`.
- Function signatures: `find_pivots(bars, k=PIVOT_K)` is the ONLY
  already-parameterized joint (the caller in `detect_setups` never
  passes k). `detect_setups(bars)` takes no options at all;
  `signal(bars, slice_state, ctx)` and `_manage(...)` read the globals
  and the persisted plan (entry/stop/tp1/tp2/direction/tp1_done/
  qty_initial/session).
- Verdict: NONE of the ten joints can be varied by configuration today.
  Zero config-only variants exist. Every variant needs code; the design
  question is only whether that code forks the logic (bad) or threads
  one parameter through the shared machinery (below).

### Recommended architecture for the build phase (one source of truth)

One minimal shared-code refactor of `sleeves/trullas_divergence.py`,
explicitly the exception the hard rail allows, with its proof duty:

1. Add a parameter bundle (frozen dataclass or plain dict) carrying
   exactly the joint fields: `pivot_k`, `tp2_level`, `include_hidden`,
   `rsi_zone_only`, `fallo_admitted`, `pyramid`, `vol_window`,
   `require_all_three` (timeframe is adapter-side, not strategy-side).
   Defaults = the frozen primary values, field for field.
2. Thread it through `detect_setups(bars, params=PRIMARY)` and the
   sleeve class as a class attribute (`PARAMS = PRIMARY`); `signal` and
   `_manage` read `self.PARAMS`. The primary class keeps defaults.
3. PROOF DUTY (before any variant lands): the existing golden blocker
   drive must produce byte-identical decisions pre/post refactor —
   golden entry 109.2908 / stop 111.01 / TP1 108.2496 / TP2 106.5504 /
   qty 22, causality and truncation tests unchanged, all 12 primary
   blockers green, and the primary's sha change + identity proof stated
   plainly in this file and the BUGLOG entry. If that proof cannot be
   produced, stop and ship variants as subclasses that override only
   `detect_setups` seams instead — do not ship an unproven refactor.
4. Each variant sleeve is then a thin module (~30 lines): subclass of
   `TrullasDivergenceSleeve` with one PARAMS field changed, its own
   `SleeveConfig(sleeve_id="trullas_vNN", cadence_s=60, …)`, and the
   same module-level `signal(...)` wrapper shape as the primary
   (exposing `last_evaluation` / `trullas_state`).
5. Each variant adapter pair is the primary adapter pair with only
   SLEEVE_ID, the strategy import, and (v01 only) the bars timeframe /
   INPUTS changed. State isolation is automatic: the adapter derives
   its state path from the sleeve's own journal dir
   (`state/<sleeve_id>/trullas_state.json`); the `trullas_state` extra
   key name can stay identical because the file is per-sleeve.
6. Rejected alternatives, recorded: (a) ten full copies of the strategy
   — forks the logic ten ways, drift guaranteed, violates minimum
   sufficient change; (b) variant modules monkeypatching primary module
   globals — the worker process is shared machinery, a mutated global
   is a cross-sleeve contamination risk and invisible in review.

### Producer reality (what each variant actually consumes)

- Primary route: adapter `bars_old(ctx, "QQQ", "1Min", 4000)` reads
  `view["bars"]["QQQ|1Min"]` from the warm SIP product
  (`desk3/warm.py` WarmBars, `INTRADAY_FETCHES` includes
  ("QQQ","1Min",10) days); registry FED keys are the adapters3 INPUTS
  `['bars','bars_1min','bars:QQQ:1Min','positions','quotes',
  'session_fills']`; `bars:QQQ:1Min` was added to
  `desk3/producers_g4._BARS_TF_KEYS` at the primary install.
- 5-minute reality (v01): the warm product ALREADY fetches and serves
  native QQQ 5Min SIP bars — `INTRADAY_FETCHES` includes
  ("QQQ","5Min",60) days, the install proof recorded QQQ|5Min = 8,058
  rows, and the live cache read at inspect (fetched
  2026-10-29T11:46Z) holds QQQ|5Min = 8,101 rows spanning
  2026-08-31 → 2026-10-29, fresh. No warm.py change is needed.
  The one missing piece is the registry key: `_BARS_TF_KEYS` has
  bars:QQQ:1Day / 15Min / 1Min but NO `bars:QQQ:5Min` (the generic
  `bars_5min` timeframe key does exist via the bars_intraday
  BarsProjection). Clean route, mirroring the primary install exactly:
  add `bars:QQQ:5Min` to `_BARS_TF_KEYS`, v01 adapter requests
  `bars_old(ctx,"QQQ","5Min",4000)`, v01 INPUTS =
  `['bars','bars_5min','bars:QQQ:5Min','positions','quotes',
  'session_fills']`. (Teddy's aggregate-1Min-to-5Min route is the
  fallback, not the choice: native bars exist here, SPY's did not.)
  Bar-count parity note: 4,000 5Min bars ≈ 51 RTH sessions of context
  (vs ~10 for 1Min) — indicator warmup is more than sufficient; all
  count-based rules (separation 10–120, expiry 30, pivot k) stay at
  their frozen numbers in 5-minute bar units, per spec S1 "all else
  equal". Clock rules (09:30–11:00 entries, 12:00 flat) unchanged.

### Roster, slice, and cadence conventions (from the live config)

- Config: `config/sleeves.json`, currently 316 rows. Row shape copied
  from trullas_divergence / grok_sr_spy / teddy_orb_spy (the two most
  recent $10k installs): `id`, `module: "adapters3.<id>"`,
  `cadence_s: 60`, `parked: false`, `slice: {capital_usd: 10000.0,
  cash_usd: 10000.0}`, `bp_buffer_frac: 0.02`, `flat_by_close: false`,
  `flatten_time_et: null` (the sleeve owns its 12:00 flat; no second
  flatten path), `session: "rth"`, `timeout_s: null`, `params: {}`,
  `inputs` exactly equal to the adapters3 module's INPUTS (a blocker
  asserts this equality for the primary; the variant blockers must too).
- Cadence: 60 s for all ten variants, including v01 (it evaluates each
  cycle against the latest closed 5Min bar, exactly as the primary
  evaluates against the latest 1Min bar; exit checks stay per-cycle).
- Activation: per-cycle ConfigWatcher reload in `desk3/run_live.py` —
  no service restart for a roster add (per TRULLAS-SLEEVE-BUILD.md).
- Roster pins that MUST move 316 → 326 when all ten land (assert
  `len(rows)==316` today): `tests/test_deploy_blockers.py`,
  `tests/test_harden_batch1_blockers.py`,
  `tests/test_grok_sr_spy_blockers.py`,
  `tests/test_milkman_0dte_20261027_blockers.py`,
  `tests/test_teddy_orb_spy_blockers.py`. The ratchet blocker
  (`tests/test_blocker_ratchet_20261026_blockers.py`) recomputes
  coverage mechanically — new modules without gate-wired blockers = RED.
- Gate: `desk/run_regression_blockers.sh` discovers
  `tests/test_*_blockers.py` — a new
  `tests/test_trullas_variants_blockers.py` is gate-wired by naming
  alone; it must assert per variant: config row shape + INPUTS equality,
  the one-joint difference on the golden fixture (each variant's
  decisions differ from the primary's ONLY as its joint dictates, and
  match the primary's where the joint is inert), and primary identity
  post-refactor.
- BUGLOG: dated entry in `BUGLOG_2026-10-29.md` (new dated file,
  following the TRULLAS-INSTALL-20261025 / TEDDY-ORB-SPY-INSTALL-20261028
  install-entry shape), plus one install proof JSON per variant under
  `proof/install/trullas_vNN.json` mirroring the primary's proof shape.

### Per-variant feasibility verdicts (all ten)

| id | subtitle (joint) | verdict | where the joint lives / what changes |
|---|---|---|---|
| trullas_v01 | S1 — 5-minute bars | FEASIBLE, clean | Adapter-side only. Native QQQ\|5Min already in the warm product (8,101 rows live at inspect, 60-day fetch). Add `bars:QQQ:5Min` to producers_g4._BARS_TF_KEYS (one line, mirrors primary install); variant adapter fetches "5Min"; strategy math untouched (bar-unit counts frozen). |
| trullas_v02 | S2 — pivot width 3 | FEASIBLE, trivial | `find_pivots(bars, k=3)` — the only joint already a function parameter. Confirm lag becomes 3 bars; separation/expiry counts unchanged. One PARAMS field threaded into detect_setups. |
| trullas_v03 | S3 — pivot width 8 | FEASIBLE, trivial | Same seam as v02 with k=8. Confirm lag 8 bars. |
| trullas_v04 | S4 — TP2 at 66.7% | FEASIBLE, trivial | TP2_LEVEL 0.618 → 0.667 in detect_setups' level computation; plan carries tp2 so _manage, adapter plan record, and the Intent target/exit_rules follow automatically. TP1 unchanged. |
| trullas_v05 | S5 — hidden divergences included | FEASIBLE, moderate | New branch in detect_setups ONLY: hidden = inverted price/MACD conditions (bearish: lower second high + higher MACD; bullish mirrored), ADDED to regular (union, per spec "included"). Same pivot pairing, same Fib swing geometry (spec §6: the between-extremes max/min anchor is the hidden-case anchor the primary already uses), same direction mapping (highs→short, lows→long), RSI/volume counting mirrored. No management changes (plan shape identical). |
| trullas_v06 | S6 — RSI counted only when leaving an extreme zone | FEASIBLE, trivial | Count seam in detect_setups only. Frozen reading: RSI divergence counts only if RSI at the second extreme is in the extreme zone and moving out — bearish rsi_second > 70 (with rsi falling), bullish rsi_second < 30 (with rsi rising). NOTE: RSI never gates the primary (MACD alone gates); this joint changes divergence_count → unit size only, never whether a trade fires. |
| trullas_v07 | S7 — fallo de MACD admitted | FEASIBLE, moderate | Needs the one genuinely new indicator series: MACD signal line = EMA(9) of the MACD line (the primary computes only the line; `_ema` helper exists). Frozen reading per spec §10 S7: fallo qualifies as the MACD divergence when, within the 5 bars following the second extreme, the fast line fails to cross the signal line in the trade direction and the price extreme stays intact. Timing is causal for free: the decision bar is the pivot confirmation bar, exactly second-extreme + k(5) bars, so the full 5-bar fallo window is knowable at decision time. Admitted IN ADDITION TO regular MACD divergence (union). Research grounding: exhaustive pass 2026-10-25 (fast line fails to cross through the signal line at successive extremes, then hooks away). |
| trullas_v08 | S8 — pyramiding on strength | FEASIBLE, the only management-side joint | Touches signal/_manage + plan state: one add of 1 unit when price first moves 0.5R in favour (R = original entry→stop distance), whole-position stop to entry at the add. Two facts the variant spec must freeze BEFORE build: (a) add qty = 1 unit on the primary formula (0.25% slice equity ÷ original risk/share), computed at add time; (b) intrabar ordering vs TP1 — the 0.5R trigger distance (≈0.118×swing) is SHORTER than the entry→TP1 distance (0.146×swing), so on a monotonic move the add fires before TP1; freeze add-evaluation before TP1 within a bar, pessimistic stop-first still supreme. Plan gains an `added` flag; TP1 half then applies to the enlarged position. No dispatcher obstacle found: an enter intent with the sleeve's declared side/position_intent is the same shape as the initial entry. |
| trullas_v09 | volume window around the extreme | FEASIBLE, trivial | Count seam in detect_setups only: volume at each extreme read as the SUM over a window around the extreme bar instead of the single bar. Frozen reading proposed for the variant spec: centred 5-bar window [i−2, i+2] at both extremes (equal widths, so sum and mean rank identically); knowable at decision time because pivot confirmation (k=5) guarantees the right-side bars exist. Like v06, volume never gates — count/size only. Window width is the one number the variant spec must name; ±2 is the recommendation (inside the pivot window, symmetric). |
| trullas_v10 | all-three confirmation strictness | FEASIBLE, trivial | Gate seam in detect_setups only: require price divergence + MACD + RSI + volume divergences all present (divergence_count == 3) instead of MACD-required-plus-count. Every v10 trade then sizes at exactly 3 units. No other change. |

Dropped joints: NONE. All ten named joints implement cleanly on the
desk's real producer inputs; no substitutes were improvised.

### Risks / edges the build phase must carry

- The shared refactor is the single point of danger to the primary.
  Its identity proof (golden fixture, pre vs post) is a hard gate for
  the whole family, not a per-variant nicety.
- v05/v07 are interpretation-bearing: both readings above are frozen
  from the spec's own §10 wording plus the 2026-10-25 research pass;
  the variant spec must restate them verbatim so the live record is
  judged against what was actually built.
- v06/v09 change sizing only (their divergences never gate). That is
  faithful to the primary's counting design; expect subtler record
  divergence, not different trade sets, except where a count change
  alters qty.
- Slice competition is honest by construction: ten new $10,000 slices,
  parked=false, session rth, each with its own
  `state/trullas_vNN/` — no shared state, no cherry-picking surface.
- Working tree note: the repo had unrelated uncommitted changes at
  inspect (BUGLOG_2026-10-27, STAGE-C-PROGRESS, adapters/laz8_common,
  desk3/dispatcher, desk3/netfetch, two test files, untracked
  422-blocker tests). Build phases must not sweep those into variant
  commits.

### Status

- inspect: DONE (this section). Build: NOT STARTED.
- Next: build phase implements the parameterization refactor +
  identity proof first, then variants in spec order v01…v10, each
  with blockers, BUGLOG entry, install proof, roster pins 316 → 326,
  and a full gate run before any GREEN is claimed.

---

## PHASE spec — DONE 2026-10-29

- Frozen variant spec written: `~/workspace/goals/ai-top50-pattern-study/files/TRULLAS-VARIANTS-SPEC-2026-10-29.md` (v1.0 FROZEN at writing; no joint value changes after any variant sees a bar).
- Follows inspect verdicts exactly: all ten joints survive (trullas_v01 S1 5-min bars; v02 S2 k=3; v03 S3 k=8; v04 S4 TP2 0.667; v05 S5 hidden included, union; v06 S6 RSI zone-only count, sizing only; v07 S7 fallo admitted, union, 5-bar window + signal-line EMA9 reading frozen; v08 S8 pyramiding, add-qty and add-before-TP1 ordering frozen; v09 volume centred 5-bar window [i-2,i+2] sum, sizing only; v10 all-three gate, count==3). Dropped joints: NONE, recorded as such in spec §5.
- Each variant in the spec carries: roster id, single joint, primary value vs variant value, verbatim inheritance of the primary spec, $10,000 own slice, 60s cadence, own state/record.
- Forward judging rule frozen in spec §6: own live paper record only, no backtest; graded vs primary and siblings on same days, in R and in % vs SPY/QQQ over same window; no promotion/retune/kill below 30 own completed trades; cannot-fire reported as cannot-fire, never widened; family always reported together.
- Changed in this phase: the variant spec file + this checkpoint section only. No code, config, or primary file touched.
- Next: build phase (parameterization refactor + primary identity proof first, then v01..v10 in spec order).

---

## PHASE build — IN PROGRESS 2026-10-29

- Refactor landed: `sleeves/trullas_divergence.py` gained the frozen
  `TrullasParams` bundle (defaults = primary values field for field),
  threaded through `detect_setups(bars, params)` and the sleeve class
  (`PARAMS`; `_manage` reads it for the pyramid joint). New indicator
  series only where a joint needs it: MACD signal line (EMA9 of the
  MACD line) computed only when `fallo_admitted`.
- PRIMARY IDENTITY: PROVEN. Pre-refactor golden drive + setups
  captured to the workflow work dir; post-refactor both IDENTICAL
  (enter bar 79, entry 109.2908 / stop 111.01 / TP2 106.5504 / qty 22,
  TP1 108.2496 in plan); all 12 primary blockers pass unchanged.
  Primary sha changed by the refactor (plainly stated in
  BUGLOG_2026-10-29.md); its decisions did not. Inert state addition:
  plans now carry `stop_orig` + `added` (v08 bookkeeping).
- Variants v01..v10 generated as thin subclasses (one PARAMS field
  each; v01 zero fields, adapter-side 5Min joint) + adapter pairs;
  `bars:QQQ:5Min` added to producers_g4._BARS_TF_KEYS; config rows
  appended (roster 316 -> 326, each $10,000, parked=false, 60s, rth);
  roster pins moved in the 5 pin files.
- Blockers: `tests/test_trullas_variants_blockers.py` (15 tests) +
  primary 12 = 27/27 OK locally. Install proofs written for all ten.
  BUGLOG_2026-10-29.md entry TRULLAS-VARIANTS-INSTALL-20261029.
- Full gate evidence so far: the official run_regression_blockers.sh
  passed rc=0 on the completed 326-roster tree (207s). Later re-runs
  were poisoned by two recorded non-tree causes: the concurrent PRZM
  roster landing mid-run (326 -> 328) and, from ~13:45Z, an
  environment-wide exec write(2) EPERM degradation (strace-proven:
  openat succeeds, write returns EPERM for python/git/cp children;
  shell-builtin writes unaffected; the PRZM lane's own detached gate
  died of it too, /tmp/gate3.log empty). A detached finisher
  (workflow work dir, finisher.sh) now probes every 60s for a healthy
  write window, then re-runs the full gate on the settled 328 tree,
  records the count here + in the BUGLOG, and makes the local commits
  (--no-verify per the documented park/restore pattern, with its own
  fresh gate evidence in hand). No push in this phase.
- Remaining: finisher completion (gate count + 4 local commits).
- Concurrency note: a parallel PRZM install landed in the same tree
  during this build (przm_zero, przm_fade_edges; roster 326 -> 328)
  and moved the shared roster pins, including the variant test's
  total assertion, to 328. An interim gate-count run also failed
  spuriously for two recorded reasons, neither a tree defect: (1) its
  TMPDIR was placed inside the repo, so a tree-copying blocker
  recursed into its own temp dir; (2) the PRZM roster change landed
  mid-run. The official gate script had already passed rc=0 at roster
  326; a final clean run on the settled 328 tree is recorded below.
- FINAL GATE (finisher run after the 2026-10-29 exec write-block
  window cleared): run_regression_blockers.sh rc=0; unittest discover
  Ran 1378 tests, OK. Family status: GREEN on the final tree
  (roster 328 including the concurrent PRZM pair).

---

## PHASE save — 2026-10-29

- Desk commits for this family (muse-desk-v3, in order):
  556d91aead38bda16892a3c9738f66383bc7da07 (parameterize primary),
  aff45c936a0ca8799fd4846a2d7915e6d217e48d (variant sleeves/adapters/roster),
  f686f0db864277c6130299f3951161b3e68dcd9d (variant blockers),
  85d2a65b2b5671ff2f6765f1310652d8b93ed8e6 (buglog, proofs, build record).
  Desk head at build completion: 85d2a65b2b5671ff2f6765f1310652d8b93ed8e6.
  This save section is appended on top as the save-record commit.
- Public save: variant spec, variant modules + adapter pairs, the
  refactored primary strategy module the variants subclass, blocker
  tests, install proofs, and this build report saved to the public
  sleeve-package repo (dwj9ddyvf6-hub/Test), verified by read-back
  (remote blob hashes equal local hashes for the sleeve modules and
  the spec; sanitized docs compared against their sanitized sources).
- PII: the frozen primary spec (TRULLAS-SPEC-2026-10-25.md) was NOT
  re-saved in this phase: its local header carries the owner's full
  name. The variant spec and this report were saved in sanitized form
  (owner referred to as "the desk owner"), matching how the primary
  package was saved on 2026-10-25. Local originals are unchanged.
