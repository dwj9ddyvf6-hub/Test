# SLEEVE FIX PROGRAM — CONSOLIDATED REPORT (Sun 2026-11-15)

Owner order (14:06 ET): "Fix them all so they fire and work, optimize them."
Governing doctrine: a non-firing sleeve is a ROUTE FAILURE (no armed-by-design
resting class); the route changes, the signal stays; radical loosening lands
only as a registered VARIATION under a new id, never as the original cured
(Owner Addenda 1 and 2, 2026-11-15 14:07/14:08 ET).

Repo: ~/workspace/muse-desk-v3. Base HEAD 87a3956 → final HEAD
13f09f80bdbe039f4b372afd3ca6065bfe335b6f. Worktree clean at consolidation.

COORDINATOR VERIFICATION (Midna, on the final tree, not lane self-report):
every commit below was read in the log and its diff/stat checked; every
blocker file confirmed present; every BUGLOG entry confirmed present in
repo-root BUGLOG_2026-11-15.md (this repo has no desk/ directory; all three
lanes that hit the brief's desk/ path filed at root per standing convention);
the variation registry was opened and counted (16); the desk gate was run by
the coordinator on the final tree after the last commit:
**run_regression_blockers.sh → Ran 2283 tests, OK, exit 0.**
Rails held throughout: Tensor engine and pins untouched, saty_sol byte-pin
untouched (F2's vendor strategy sha256 unchanged), no core signal logic
rewritten in any lane, roster untouched at 339 (variations registered, not
rostered — see F4).

Lane deliverables of record:
FIX-F1-Q07.md, FIX-F2-SHIMS.md, FIX-F3-LAZARUS-EXITS.md, FIX-F4-ROUTES.md
(same directory as this report).

---

## F1 — Q07 FAIL-CLOSED FILTERS (49 sleeves) — commit 13f09f8

Root cause (the producer DOES tag; three consumers each failed to read the
served form):
- D1 desk3/q07_engine.py: specs use band "ml", the composer stamps cap_band
  "midlarge" — every real fire refused on the band check before any filter
  ran; _filters_pass also read only flat fields, blind to fire["tags"] where
  wiki_low lives.
- D2 desk3/lazarus_q07.py: SPECS parked=True for the 4 swing-ML lanes the
  roster unparked 2026-11-14; the engine flag silently overrode the roster.
- D3 laz_sleeves/_common.py: tensor_fires indexed as a dict while the bundle
  producer serves a list (TypeError on the live shape); alt evidence read
  only from alt_data, whose producer serves mcap_band only; deep70 computed
  at 0.30×high vs the estate-wide documented 0.70.

Cure: band-vocabulary normalization + flat-then-tags evidence reads;
parked=False for exactly the 4 roster-unparked lanes; list normalization +
composer-tags fallback + deep70 restored to 0.70. No signal/sizing/stop/
horizon/heat changes. Three tests that pinned the old parked registration
were updated with the cure stamped in-file; no assertion deleted.

Proof: blocker tests/test_q07_failclosed_f1_20261115_blockers.py — 8 passed
cured; 7 failed / 1 passed on the preserved pre-cure HEAD tree (the 1 pass is
the fail-closed guard, by design). BUGLOG FIX-F1-Q07-20261115 (High).

Replay (Unblock-2 machinery, 255 sessions): BEFORE 0/49 firing, 0 entries.
AFTER-BASE (cured code, identical untagged fires) 0/49 — fail-closed proven
intact, nothing manufactured. AFTER-TAGGED probe (producer-shaped passing
alt evidence): 21/49 firing, 45 entries — midlarge 20/21 (40 entries),
micro 1/4 (5), small-band 0/24. All 14 of Unblock-2's drop-revealed sleeves
fire, plus the 4 unparked and 3 laz lanes.

Falsifier: nonzero entries over the next 20 QQQ-down sessions where the
composer addresses the 21 with passing tags. Rollback: revert 13f09f8.

## F2 — SHIM TYPE DEFECTS — commit 5dbc57c

Census: mechanical AST census (58 stamp sites) + repo-wide grep, each pair
verified against its consumer's documented contract: 48 pairs, exactly 2
mismatches, 46 checked-and-cleared (recorded as deliberately-not-bugs in the
BUGLOG, including the trap set: adapters/{beatendown,confluence,momentum}
stamp the same vix 4-tuple CORRECTLY — their strategies document and unpack
the tuple; a guard test pins this).

Cures (shim-side only):
1. iron_condor extra['vix']: 4-tuple stamp → float of last VIX close,
   matching the vendor's documented float | None contract. Was crashing
   every session from 2026-09-01 (TypeError: float() on tuple).
2. Second mismatch found by the census drive, masked by #1: chains — the
   shim passed the live producer's flat row list while build_condor expects
   {SYM: {"put": [...], "call": [...]}} (AttributeError on every gated entry
   evaluation). Cured with _chains_by_kind() in the shim.

Proof: fixture drive over 19 sessions from 2026-09-01 — before: 19/19 CRASH;
after (final tree, post-commit rerun): 19/19 OK with 4 intents (the designed
4-leg condor fan-out) every session. Blocker
tests/test_shim_type_f2_20261115_blockers.py — 6/6 pass cured; 5 fail / 1
pass (the cleared-pairs guard) on preserved pre-cure copies. BUGLOG entry
with deliberately-not-bugs section. Vendor strategy byte-pin intact.

## F3 — LAZARUS EXIT CALIBRATION — commit 2574393

Applied exactly KG-7's paired evidence, larger gain wins, all in the single
registered source desk3/lazarus.py SPECS:
- 1w: stop_pct 0.15 → 0.30 (WIDEN_STOP_X2 +1423.0bp, n=28; over DROP +1212.8)
- 1wa: stop_pct 0.15 → None (DROP_STOP +1029.1bp, n=34; over WIDEN +1021.0)
- s_1wlab: stop_pct 0.15 → None (DROP_STOP +676.4bp, n=80; over WIDEN +654.1)
- s_rules_1w: horizon_sessions 27 → 54 (EXTEND_HORIZON_X2 +497.7bp, n=58,
  t=2.28; its stop NOT loosened — DROP/WIDEN printed −79.8/−86.1bp)

Protected and verified unchanged in the diff: 1d (stop 0.15 / target 0.20 /
partial 0.30 / h=40 — its stop pairs with its partial target; DROP printed
−213.3bp) and 1dc (h=21 — extension printed −604.3bp, t=−4.06, load-bearing).

Proof: the lane's confirmation replay on the final tree, new params read
live from cured SPECS, reproduces KG-7 exactly on all four (delta, n, t,
both means, to 0.1bp). Blocker
tests/test_lazarus_exit_calibration_f3_20261115_blockers.py — 9 tests (4
changed values, 2 protected profiles, 3 behavioral); all 4 changed-value
assertions FAIL on the preserved pre-cure copy, all 9 pass cured. The
pre-existing batch-1 test_stop15 asserted the old profile and was updated in
the same commit to the F3 profile. BUGLOG F3-LAZARUS-EXITS-20261115.

Falsifier per sleeve (registered in FIX-F3-LAZARUS-EXITS.md with exact
rollback lines): the changed sleeve must not underperform its registered
base profile over its next 20 resolved fires, else rollback.

Cosmetic remainder (named, not a defect): the exit-reason label in
desk3/lazarus.py is the hardcoded string "{sleeve_id}_stop15" regardless of
stop value; 1w exits will read "1w_stop15" while triggering at −30%.
Logging only; trigger values are correct.

## F4 — NO-FIRE ROUTE-ATTACK PROGRAM — commits 20baa09, 36a78ec, e76b920

Class census of the 195 REPLAY-NO-FIRE sleeves (recounted from
UNBLOCK-2-REGISTER.jsonl; sums to 195): BARS-ONLY-SINGLES 46,
FUNDING-GATED-CRYPTO 27, OPTIONS-FEED-ABSENCE 24, Q07-SMALL 24,
TENSOR-REFUSAL 20, Q07-ML-GATED 11, MN-NO-REBALANCE 9, RSI2-NO-RECOVERY 9,
ETF-B9-ELIGIBILITY 8, TIMING-STREAM 8, KRAKEN-CURRENT-ONLY 6,
REAL-RULE-SPARSE 3. Upstream cross-cut: 49 named-stream sleeves + 146
none-recorded. The ENJ 10 overlap with the 195 is ZERO (they were
EXECUTION-IMPOSSIBLE in Unblock-2, handled separately below).
Per-sleeve remainder tables (195/195 rows) are in FIX-F4-ROUTES.md and are
the routes-tried ledger of record for the classes below.

### ENJ funding-squeeze class (10 sleeves) — CURED, 10/10 fire on own logic
Routes tried, each printed: Route 0 recount on the 4H Kraken tape reproduced
KG-6 exactly (74 funding-neg / 20 breakouts / 0 conjunction on 420 bars; a
first-script phantom conjunction was traced to an as-of boundary error and
corrected in print). Route (a) 1H tape: conjunction occurs 4×. Route (b)
alternative funding series: Binance 451, Bybit 403, Hyperliquid null, OKX
coin-margined nonexistent, Coinalyze history not archived — exhausted with
the gap named. Route (c) intrabar evaluation forms: 1× each on 4H. Route
(d), found by engine drive: the conjunction occurs 1× on the full 4H tape at
bar 192, inside KG-6's warmup window. A serving defect blocked route (a):
batch7's ENH freshness gate hardcoded 4H bar duration and refused every 1H
entry as −3h stale — cured in 20baa09 (freshness derives bar duration from
served bars; batch8 lag same cure; native 4H behavior bit-identical).
Post-cure engine entries on 1H: batch8 arms 3–4 each, r19 arms 4/3/4.
Signal definition unchanged throughout.

### Tensor serving — structural defect cured; gate values still refuse (named)
Commit 36a78ec: tensor_warm's native pass universe was memo-only; fires
outside the memo universe got no analysis record and empty feature cells,
failing every variant consumer closed. Universe is now memo UNION bundle
fire symbols. Archived fires re-served through the desk's own native pass
gain complete cells 0/42 → 42/42. BUT on the archived pair the gate VALUES
still refuse (ret60≥31 on 0/42, buy markers 0/42 — RECLAIM/TRANSITION
phenotypes vs weekly-product gates): post-cure result 0 entries for all 25
consumers, value-faithful, not a serving failure. This class stands with
routes printed in FIX-F4-ROUTES.md; the C1 phenotype got _varpx variations
(below).

### Upstream streams — verified, one cadence defect named
All producers verified running/writing where consumers read (fires drop 52,
rule_fires 624 items, midna_signals 158 fresh). lazarus_fires drop is empty
because the Tensor bundle's fires channel was engine-empty 2026-11-13..15
(21 fires on 11-11/12) — a bundle-side gap, named. timing_signals drop
exists but ages past its 1-day SLA (research-lane cadence, named, not cured
in this program). Monitor check: fwd_alpaca_enj_iu_body's designed output
DOES occur (80 monitor_status journal records) — not a route failure.
free_kraken_enj_spot: historical order-book depth route exhausted, archive
gap named (no honest source archives it; nothing fabricated).
The iron_condor vix defect in this lane's scope was already cured by F2
(5dbc57c, verified in the final tree) — not duplicated.

### Variations (Owner Addendum 2) — commit e76b920
16 variations registered in config/f4_variations_20261115.json, each with
its own id, replay counts, and forward falsifier; parents untouched
(blocker asserts parent catalog filters still match the registry):
- 14 Q07 _vargd (GATE_DROP of the alt-filters; parents are sleeves whose
  base logic produced 0 entries and whose drop runs revealed 23 entries;
  these parents sit outside the 195 as register-graded INDICATIVE).
- 2 Tensor C1 _varpx (ret60 31→0; fire-level read 2/42 vs 0/42).
Uniform falsifier: retire the variation if mean fwd5 excess vs QQQ < 0bp
over its first 20 resolved forward fires.
Variations are REGISTERED, NOT ROSTERED: sleeves.json is gate-pinned at 339
by six blocker files; rostering them is a deliberate roster-change step,
named here as owed work, not silently done.

Blockers: tests/test_f4_routes_20261115_blockers.py — 6 tests, fail
direction proven on preserved pre-cure copies (native-4H path passes pre
and post, by design). BUGLOG FIX-F4-20261115-A/B/C.

---

## FALSIFIER REGISTER (every loosening in the program)
- F1 (filter serving-form cure): nonzero entries over the next 20 QQQ-down
  sessions where the composer addresses the 21 tagged-probe sleeves with
  passing tags; rollback = revert 13f09f8.
- F3 (4 exit calibrations): per-sleeve — must not underperform the
  registered base profile over the next 20 resolved fires, else rollback
  (exact rollback lines in FIX-F3-LAZARUS-EXITS.md).
- F4 variations (16): retire if mean fwd5 excess vs QQQ < 0bp over the
  first 20 resolved forward fires.
- F2 and the F4 plumbing cures (20baa09, 36a78ec) are defect cures, not
  loosenings; they are guarded by their blocker tests in the gate.

## HONEST REMAINDER — still not firing, by class, routes in print
(Full per-sleeve rows and routes-tried ledgers: FIX-F4-ROUTES.md for the
195; FIX-F1-Q07.md for the Q07 remainder.)
- Q07-SMALL 24: band-faithful; their universe is not in the bar cache and
  the composer addresses none of them. Route class: data/universe, open.
- Q07 micro remainder + s_q07w_s78_mi_ats_z1_mom6: the only micro-banded
  cache symbols have <127 bars; mom6 uncomputable on the available tape.
- s_q07w_s78_ml_deep70_glow_ins2: gamma_low has NO producer anywhere on
  the desk — the one genuinely unfed filter left. Open: producer build.
- OPTIONS-FEED-ABSENCE 24: owed work is dated options-chain accumulation.
- FUNDING-GATED-CRYPTO 27: owed work is per-sleeve drives on the proven
  ENJ pattern (the ENJ 10 are cured; the ADA/LINK remainder is not yet
  driven sleeve by sleeve).
- ETF-B9-ELIGIBILITY 8: MIN_SESSIONS ruling / seasoning.
- KRAKEN-CURRENT-ONLY 6: aligned-history drives owed.
- TENSOR-REFUSAL 20: serving cured; gate values refuse the archived fires
  value-faithfully. Stands with routes printed; C1 carries _varpx
  variations. No further route may loosen the weekly-product gates without
  crossing from route repair into signal redesign, which the rails forbid.
- BARS-ONLY-SINGLES 46, MN-NO-REBALANCE 9, RSI2-NO-RECOVERY 9,
  TIMING-STREAM 8, REAL-RULE-SPARSE 3: routes tried and per-sleeve rows in
  FIX-F4-ROUTES.md; TIMING-STREAM additionally carries the producer-cadence
  SLA defect named above.
- free_kraken_enj_spot: historical book-depth archive gap; route exhausted
  honestly, nothing fabricated.

## STATUS
STATUS: PARTIAL — proven on the final artifact: all four defect/calibration
lanes cured at the source and committed (2574393, 5dbc57c, 13f09f8, 20baa09,
36a78ec, e76b920), the ENJ squeeze class firing 10/10 on its own logic, Q07
tagged-evidence replay firing 21/49 (was 0/49) with fail-closed intact,
iron_condor firing its designed fan-out 19/19 sessions (was 19/19 crashes),
16 variations registered with falsifiers, and the full gate green on the
final tree (Ran 2283 tests, OK, coordinator-run at HEAD 13f09f8). The
PARTIAL names the remainder above: classes whose routes are exhausted in
print with named gaps or owed work (small-band universe, gamma_low
producer, options-chain accumulation, ADA/LINK per-sleeve drives, B9
seasoning ruling, Kraken aligned-history drives, Tensor gate values), plus
the forward falsifiers, which only live sessions can settle.
