# PRZM Recreation — Build Report (2026-10-29)

Installs PRZM-RECREATION-SPEC-2026-10-29 (FROZEN) in muse-desk-v3.
Source teardown: ~/workspace/opt/rea-teardowns/przm/TEARDOWN.md
(PARTIAL; public record only; relay equivalence unverifiable).
Paper only. No backtest claimed by either sleeve.

## What was built

| Sleeve | Core | Adapter pair | Config |
|---|---|---|---|
| przm_zero | sleeves/przm_zero.py | adapters/przm_zero.py + adapters3/przm_zero.py | roster row, $10,000 slice, cadence 60, session rth, PARKED |
| przm_fade_edges | sleeves/przm_fade_edges.py | adapters/przm_fade_edges.py + adapters3/przm_fade_edges.py | roster row, $10,000 slice, cadence 60, session rth, PARKED |

Roster 326 -> 328. Roster pins moved 326 -> 328 in
tests/test_deploy_blockers.py, test_harden_batch1_blockers.py,
test_grok_sr_spy_blockers.py, test_teddy_orb_spy_blockers.py,
test_milkman_0dte_20261027_blockers.py,
test_trullas_variants_blockers.py. Names kept exactly as tasked
(przm_zero, przm_fade_edges); no roster-convention rename needed.
Inputs reuse existing producers only (bars:SPY:1Min warm SIP product,
options / options_chain); no second source of truth was forked for
bars, chains, or levels. State is each sleeve's own file beside its
journal (przm_state.json / przm_fade_state.json).

## przm_zero (extracted engine, parked on a named missing input)

Complete fallback engine per spec: noise weights 0 / 0.15 / 0.2 /
0.5 with sweep x1.35, opening x1.25, closing x0.7; chasing x0.55 and
contrarian x1.25 at |m5| > 0.8; five-driver equalizer
(F = 0.3 SES + 0.4 30M + 0.22 10M + 0.08 5M, STDY persistence, PX
tanh) with pin x0.85 + magnet pull / run x1.15 / phase damping;
hysteresis entry 25, flip 35, drop <8 plus 600,000 ms; 09:45-15:45
window (recreated hard gate); sign-only 30-minute grading counting
right AND wrong. Paired-leg cancellation DROPPED, stated in the
docstring, not approximated (spec decision).
PARKED, params.parked_reason = WAITING_NO_PRINT_TAPE: no desk
producer serves a signed same-day SPY options print tape (bull /
sweep / opening flags), so the sleeve ledgers PX only and trades
nothing. Unpark = a proven tape route, not a rebuild.

## przm_fade_edges (extracted regime test, recreated gamma)

Regime (extracted): pin = spot > gamma flip; Fade Edges fades
session edges to the magnet in a pin and stands aside in a run.
Gamma (recreated, frozen in the spec): GEX = OI x gamma x 100 x
spot, calls positive / puts negative; magnet = strike of max |net
GEX|; flip = cumulative sign-change strike. Edges, $2,000 notional,
magnet target, 0.15% invalidation, regime-flip exit, 15:45 flat:
recreated mechanics, graded as such in the docstring.
PARKED, params.parked_reason = WAITING_NO_GAMMA_LEVELS: the desk
options_chain producer serves delta-only rows (feed=indicative
carries no greeks and no open interest; FEED-WIRE-20261025 in
desk3/producers.py), so gamma levels cannot be computed from any
route that exists today. The spec prohibits a substitute regime
test, so none was invented.

## Proof

- tests/test_przm_recreation_blockers.py: 17 tests, gate-wired by
  the discover pattern. Hand-worked equalizer score; chasing ratio
  0.55 (about half) and contrarian 1.25; a held call does NOT flip
  on a small driver change (opposing 20 and 34 hold, 40 flips); a
  call drops ONLY on a real fade (score*dir <8 AND >=600,000 ms;
  599,999 ms holds); grading counts right=1 AND wrong=1 with a
  pending third; gamma magnet/flip hand-worked; Fade Edges fades
  in a pin fixture (short at the high, target = magnet) and stands
  aside in a run fixture; regime flip exits an open fade; both
  WAITING states emit no intents; adapter drives round-trip state;
  config rows parked with named reasons and INPUTS matching.
  Result this session: 17/17 OK.
- Full suite: one complete discover run over the final tree this
  session returned "Ran 1378 tests in 183.704s / OK" (log captured
  during the build; 1346 at the teddy install + trullas variants +
  17 przm = 1378).
- PARTIAL on gate mechanics, stated plainly: repeated
  run_regression_blockers.sh attempts in the same window were
  contended by sibling lanes running suites in this tree
  concurrently (shared fixed .gate_tmp dir, process-scan tests
  seeing stranger runners), and this box's stacked /tmp tmpfs
  mounts intermittently return EPERM to tempfile's O_NOFOLLOW
  probe and to git's loose-object writes. Those are environment
  failures, observed on unrelated test files too, not logic
  failures in this install.

## Commit state (BLOCKED, named)

All new files are in the working tree and verified there. Local
commits could NOT be landed in this session: git object writes to
muse-desk-v3/.git fail with "unable to write loose object file:
Operation not permitted" (reproduced with git add, git commit,
git hash-object -w, an alternate object directory, and plain
Python file creation inside .git/objects), while the same
operations succeed in scratch repos. Today's sibling installs
(trullas variants) are likewise uncommitted in this tree, which
points at a repo/environment-level write blockage, not at this
install. Config rows and the 326->328 roster-pin edits are also
working-tree-only for the same reason, and because those hunks
interleave with the uncommitted trullas-variant install. Nothing
was pushed (per task instruction for this phase).

Unblock: restore .git object writes for this repo, then commit
(sleeves/adapters/adapters3/tests file set, then config + pins,
then this report and the BUGLOG_2026-10-29.md entry, which is
appended in the working tree).

## Open items

1. Signed print tape route (przm_zero unpark): one verified live
   session from an Alpaca v1beta1 options trades route or another
   licensed tape, fields inspected.
2. Gamma/OI chain route (przm_fade_edges unpark, and przm_zero's
   pin/run score terms): chain rows carrying gamma + open interest.
3. Relay equivalence of every extracted fallback number remains
   unverifiable from public material (teardown claim 12).
