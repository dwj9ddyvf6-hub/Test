# DEPLOY-REPORT — muse-desk-v3 (2026-10-24)

Verdict: PARTIAL — deployed and running on paper; the mirror and the
restore drill are GREEN; a live fill is still unproven (named below).

## Mirror (GREEN)
- Silicon branch `muse-desk-v3` created via the SHA-preserving Git-Data
  mirror (`.scratch-femto-mirror/mirror_v3_branch.py`, adapted from the
  v2 tool). Pass 1: 56 blobs uploaded / 420 present, 112 trees, 24
  commits, ref created. Read-back: remote ref == local HEAD at mirror
  time (f9de8cf), summary in `mirror_v3_summary.json`.
- Two tool defects cured en route: bootstrap PUT 422 on the non-empty
  Silicon repo (skip when repo non-empty) and a hung pass — ghapi's
  urlopen has no timeout; the v3 tool sets a 60s default socket
  timeout so stalls become retryable errors.
- Restorability route was already registered in
  `~/workspace/backup/restorability_check.py` GITLINK_ROUTES
  (workspace/muse-desk-v3 → Silicon branch muse-desk-v3); its pin
  tests pass (4/4).

## Restore drill (GREEN)
- Reconstructed the desk FROM the mirror (Git Data API: recursive
  tree at the remote head, 439/439 blobs) into /tmp/v3-drill, laid out
  as in the workspace (muse-desk-v2 as the read-only sibling the
  oracle tests resolve). Full suite there: 321/321 GREEN.
- First drill attempt failed honestly (24 errors): the batch-4 oracle
  tests resolve v2 as a sibling path — a drill-layout defect, cured
  by the layout above, not a restore defect. Content diff vs local at
  the mirrored head: identical except the then-uncommitted DEPLOY-2
  changes (landed and re-mirrored in the final refresh).

## Deploy (paper, live)
- Cures landed first (BUGLOG DEPLOY-1/2, blockers fail-first proven,
  gate 322 GREEN): a live runner (desk3/run_live.py) and PaperDoor
  credential injection via v2's route (skill key file + Secure Vault
  surrogate; paper account read-back verified ACTIVE).
- Evaluate-only first (FakeBroker): cycles advancing, terminal feed
  fresh, journals appending; first cycle exposed 13 FED errors
  (snapshot_missing_now) → cured at the source (DEPLOY-2), live
  re-proof FED 18 ok / 0 errors.
- Then dispatch enabled under the v3- client-order-id namespace:
  runner pid 15538, mode=dispatch, 60s cycles, state/runner.json
  advancing (cycle 29+ at report time), every cycle status ok.
- Supervised window result: dispatched 0 — Saturday, producers
  currently supply positions + an empty bars map, so 115 sleeves are
  UNFED by name, 23 parked, 18 FED evaluate and emit no intents.
  Zero orders is the honest outcome of that feed state, not a stall:
  cycles, feed, and journals all advance. Reconciliation: dispatcher
  journal empty (no intents), broker read-back of the account taken
  at door verification.
- OPEN by name: A9 live fill read-back still requires real bars (warm
  pipelines) in market hours. v2 is untouched and intact; v3 is the
  operating desk from this point — v2's Monday smoke jobs should be
  stood down by the parent (collision rule).

## Operations
See OPERATIONS.md (run/stop/recover/state/save).

## Cure round 2 addendum (2026-10-24, verifier PARTIAL rows)
Final head 3e41e28 (docs closeout after this addendum re-mirrored).
- A15 CURED: desk3/reconcile.py — journal-derived vs broker read-back
  per cycle in the live runner (session-start baseline records the
  pre-v3 legacy book; live baseline recorded 2026-10-24). Planted
  discrepancy (+5 QQQ) detected, named, halts entries for the affected
  sleeve only (exit + other sleeve fill). Blockers fail-first GREEN.
- A5 sub-item CURED: port4_context list-contract normalization +
  s_cl_vmr_qqq vix fail-closed. Verifier harness re-run: 133/133 ok,
  0 errors (was 131 ok / 2 err).
- A8 live surface CURED: every live cycle merges the latest setups doc
  through the vendored merge into terminal_feed.json AND
  terminal.json (keys verified live after restart, runner pid 23574,
  and in the restored tree). OPEN by name: end-to-end setups
  GENERATION from v3 state (curator run) — not claimed.
- A1 evidence CURED: isolated-tree end-to-end blocker (tree copied to
  a directory with no v2/femto sibling; cycle GREEN there; gate-wired).
- A16 CURED at final head: source restored from Silicon branch
  muse-desk-v3 @ 3e41e28 (blob reconstruction) AND state restored from
  Silicon branch muse-desk-v3-state @ f4332ec (manifest read back
  from GitHub; 228/228 state files sha256-verified, 0 mismatches;
  dispatcher.jsonl absent because zero intents have ever dispatched).
  Restored-tree gate 328/328 GREEN. First drill attempt died ENOSPC
  (/tmp tmpfs filled by the A1 blocker's leaked tree copies) — cured
  at the source (blocker cleanup + drill off tmpfs), BUGLOG CURE2-5.
- Gate note: one intermediate gate run failed (55 errors) while a
  full roster harness ran concurrently in another process; sequential
  re-runs on identical code GREEN before and after (328/328 x3).
- A9 stays OPEN by name: no RTH session has run (Saturday); live
  producers still supply empty bars (115 UNFED named); first
  supervised market-hours window with real bars remains the proof.
  Verdict stays PARTIAL on A9 alone.

## Cure round 3 addendum (2026-10-24, verifier PARTIAL rows)
- A8 CURED (as written): end-to-end setups GENERATION from v3 state
  now exists (desk3/setups_generate.py, CURE3-2) and ran live
  2026-10-24: v3 journals translated to a curator state dir (0 ledger
  rows — the desk has never dispatched a paper order), the original
  generator produced state/setups_latest.json (0 setups, market
  regime Downtrend from real SPY/QQQ SIP bars), and the live cycle
  merges it with setups_source=state/setups_latest.json (verified in
  state/terminal_feed.json after restart). Vendored pins unchanged.
- A9 root cause CURED, fill still OPEN by name: the empty-bars
  producer is replaced by a real SIP warm (CURE3-1: 155/155 symbols,
  465 snapshot keys, SPY 345 daily + 352 hourly bars, paginated
  fetch), fed-marking is per-key (a failed producer leaves sleeves
  UNFED, never FED-on-empty), dispatch-mode positions read back from
  the account, and reconcile no longer poisons evaluate-only mode
  (CURE3-4, found in-pass). Live proof on the cured runner
  (evaluate-only, pid 26973): FED sleeves emit real intents on warm
  bars and fill against the test broker (s_mn_vwap / s_mn_macd /
  s_mn_reversal fills in state/dispatcher.jsonl, dispatched 5/cycle,
  0 errors). The runner is deliberately EVALUATE-ONLY over the
  weekend — no paper orders from stale Friday bars. A9's live paper
  fill requires the supervised RTH dispatch session (Mon 2026-10-26);
  it stays OPEN by name until that read-back exists. Verdict stays
  PARTIAL on A9 alone.
- A6 text CURED: the row now states the proven composition (133
  genuine evaluated + 267 synthetic; 23 parked named, not evaluated).
- A19 fragility CURED (CURE3-3): the gate owns its temp space
  (TMPDIR -> repo .gate_tmp, trap-cleaned; the isolated-tree copy
  excludes it). Gate on the final tree in the DEFAULT environment:
  337/337 GREEN; /tmp stayed at 11% throughout.
- FED/UNFED roll is unchanged in count (115 UNFED / 23 PARKED /
  18 FED) — the 115 lack non-bars producers (options/kraken/fires/
  tensor/quotes), named per-sleeve in state/health.json; bars-only
  sleeves were the 18 FED before and are now FED on real data.
