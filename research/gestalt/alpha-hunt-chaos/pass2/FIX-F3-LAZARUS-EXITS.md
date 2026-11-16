# FIX-F3 — LAZARUS EXIT CALIBRATION (Sleeve Fix Program, Lane F3)

Evidence applied: KG-7-EXIT-VARIATIONS.md / KG-7-REGISTER.jsonl (paired
per-trade replay deltas vs each sleeve's registered base, Unblock-2
Book.path machinery on stored daily closes, 6bp exit cost).
Repo: ~/workspace/muse-desk-v3, base HEAD 87a3956, fix commit **2574393**.
Single registered source for all four sleeves: `desk3/lazarus.py` SPECS
(every adapters3 module for these sleeves delegates to it; no second
copy of these parameters exists in the tree).

## CHOICES (widen-vs-drop decided per sleeve by the larger KG-7 paired gain)

- **1w → WIDEN_STOP_X2** (+1423.0bp) over DROP_STOP (+1212.8bp)
- **1wa → DROP_STOP** (+1029.1bp) over WIDEN_STOP_X2 (+1021.0bp)
- **s_1wlab → DROP_STOP** (+676.4bp) over WIDEN_STOP_X2 (+654.1bp)
- **s_rules_1w → EXTEND_HORIZON_X2** (+497.7bp, n=58, t=2.28)

## PER-SLEEVE REGISTER

### 1w — stop widened x2
- Change: `desk3/lazarus.py` SPECS["1w"], `stop_pct` **0.15 → 0.30** (horizon_sessions 252 unchanged, target None unchanged).
- KG-7 replay delta: **+1423.0bp** paired (n=28, t=1.37); base 1725.0bp → 3148.0bp.
- Forward falsifier: over its next 20 resolved fires, 1w under the widened stop must not underperform its registered base profile (stop 0.15, h=252) graded on the same paired replay machinery; underperformance ⇒ rollback.
- Rollback: in SPECS["1w"] set `stop_pct=0.30` back to `stop_pct=0.15`.

### 1wa — stop dropped
- Change: `desk3/lazarus.py` SPECS["1wa"], `stop_pct` **0.15 → None** (horizon_sessions 252 unchanged).
- KG-7 replay delta: **+1029.1bp** paired (n=34, t=1.13); base 1256.3bp → 2285.5bp.
- Forward falsifier: over its next 20 resolved fires, 1wa with no stop must not underperform its registered base profile (stop 0.15, h=252) on the same paired replay machinery; underperformance ⇒ rollback.
- Rollback: in SPECS["1wa"] set `stop_pct=None` back to `stop_pct=0.15`.

### s_1wlab — stop dropped
- Change: `desk3/lazarus.py` SPECS["s_1wlab"], `stop_pct` **0.15 → None** (horizon_sessions 126 unchanged).
- KG-7 replay delta: **+676.4bp** paired (n=80, t=1.91); base 587.6bp → 1263.9bp.
- Forward falsifier: over its next 20 resolved fires, s_1wlab with no stop must not underperform its registered base profile (stop 0.15, h=126) on the same paired replay machinery; underperformance ⇒ rollback.
- Rollback: in SPECS["s_1wlab"] set `stop_pct=None` back to `stop_pct=0.15`.

### s_rules_1w — horizon extended x2
- Change: `desk3/lazarus.py` SPECS["s_rules_1w"], `horizon_sessions` **27 → 54** (stop_pct stays 0.15 — KG-7 printed DROP_STOP −79.8bp and WIDEN_STOP_X2 −86.1bp for this sleeve, so its stop was NOT loosened; horizon_from_fire / horizon_plus_one unchanged).
- KG-7 replay delta: **+497.7bp** paired (n=58, t=2.28); base 365.2bp → 862.9bp.
- Forward falsifier: over its next 20 resolved fires, s_rules_1w at h=54 must not underperform its registered base profile (stop 0.15, h=27) on the same paired replay machinery; underperformance ⇒ rollback.
- Rollback: in SPECS["s_rules_1w"] set `horizon_sessions=54` back to `horizon_sessions=27`.

## PROTECTED — NOT TOUCHED (verified at registered values on arrival and after the fix)

- **1d**: stop_pct 0.15, target_pct 0.20, partial_pct 0.30, horizon_sessions 40. KG-7 DROP_STOP printed −213.3bp (n=56, t=−2.2): the stop pairs with the +20% partial target; load-bearing pair.
- **1dc**: stop_pct None, horizon_sessions 21. KG-7 EXTEND_HORIZON_X2 printed −604.3bp (n=280, t=−4.06): the 21-session horizon is load-bearing.
- Neither was changed on arrival; neither was changed by this lane. Their values are asserted by the F3 blocker (protected-value tests pass on both the pre-cure and cured trees).
- No other sleeve's KG-7 variation was applied. Tensor engine/pins and the saty_sol pin untouched; no signal logic, sizing, invalidation, or heat change anywhere — exit-profile parameters only, each bound to its own KG-7 row.

## CONFIRMATION REPLAY (run by this lane on the FINAL tree)

Machinery: KG-7's own (Unblock-2 `Book.path`, stored daily closes, 6bp
exit cost), streams = the sleeves' KG-7 base streams
(pass2/work/runs/{1w,1wa,s_1wlab,s_rules_1w}.json), OLD = pre-cure
registered base, NEW = parameters read live from the cured
`desk3/lazarus.py` SPECS. Script: /tmp/f3_replay.py.

| Sleeve | Final-tree params | Base mean | New mean | My paired delta | KG-7 printed | Match |
|---|---|---|---|---|---|---|
| 1w | stop=0.30, h=252 | 1725.0bp | 3148.0bp | **+1423.0bp (n=28, t=1.37)** | +1423.0bp (n=28) | exact |
| 1wa | stop=None, h=252 | 1256.3bp | 2285.5bp | **+1029.1bp (n=34, t=1.13)** | +1029.1bp (n=34) | exact |
| s_1wlab | stop=None, h=126 | 587.6bp | 1263.9bp | **+676.4bp (n=80, t=1.91)** | +676.4bp (n=80) | exact |
| s_rules_1w | stop=0.15, h=54 | 365.2bp | 862.9bp | **+497.7bp (n=58, t=2.28)** | +497.7bp (n=58) | exact |

Every delta, n, t, and both means reproduce KG-7 to the printed 0.1bp.

## BUG LAW

- BUGLOG: entry **F3-LAZARUS-EXITS-20261115** in the repo's
  BUGLOG_2026-11-15.md (the repo keeps BUGLOGs at its root — there is
  no `desk/` directory in muse-desk-v3; the lane brief's
  `desk/BUGLOG_2026-11-15.md` path resolves to this file by repo
  convention). One entry covering the calibration set, each sleeve named.
- Regression blocker: **tests/test_lazarus_exit_calibration_f3_20261115_blockers.py**
  (9 tests: 4 changed registered values, 2 protected profiles, 3
  behavioral — 1w holds through −16% and stops at −35%; 1wa/s_1wlab
  hold through −50%; 1d still stops at −16%).
- Fail direction: proven on the preserved pre-cure copy
  /tmp/lazarus_precure_F3.py — all 4 changed-value assertions FAIL
  there (1w stop 0.30: FAIL; 1wa stop None: FAIL; s_1wlab stop None:
  FAIL; s_rules_1w h=54: FAIL), protected assertions PASS on both
  copies; all 9 tests PASS on the cured tree.
- Pre-existing blocker updated in the same commit:
  tests/test_lazarus_batch1_blockers.py `test_stop15` asserted the old
  profile for 1w/1wa/s_1wlab; it FAILED on the cured tree before the
  update (first failure at 1w — the behavioral fail-direction proof),
  and now asserts the F3 profile (1w/1wa/s_1wlab out of the stop15
  list; 1wa/s_1wlab in the no-stop hold-through list).
- Full gate on the final tree: `run_regression_blockers.sh` —
  **Ran 2263 tests, OK**.
- Commit: **2574393** (4 files: desk3/lazarus.py, the new F3 blocker,
  the batch-1 blocker update, BUGLOG_2026-11-15.md).
- Worktree note: unstaged modifications in other files
  (desk3/laz_batch7.py, desk3/lazarus_q07.py, desk3/q07_engine.py,
  desk3/sleeves/iron_condor.py, laz_sleeves/*) appeared during this
  session from sibling lanes; this lane neither made nor staged them,
  and they are not in commit 2574393.

STATUS: GREEN — all four KG-7-ordered exit calibrations applied at the single registered source (desk3/lazarus.py SPECS) and proven on the final artifact: confirmation replay reproduces KG-7 exactly on all four sleeves, blocker fail/pass directions proven, full gate 2263 tests OK, commit 2574393. Evidence pointer: this file's confirmation-replay table and per-sleeve register; repo commit 2574393; BUGLOG entry F3-LAZARUS-EXITS-20261115.
