# MILKMAN-0DTE-SLEEVE-BUILD — Milkman 0DTE SPX install report

Date: 2026-10-27. Program: EXECUTE-SCOPE-2026-10-27 item 4.
Source: Femto-lean branch `milkman-0dte` (Claude's master-desk commit
8c64cd5c), fetched under the program manifest, group `d_milkman`.

## Scope (InfinityBlade)

- **Surface:** vendored package `desk3/milkman_0dte/` (authored sleeve
  byte-exact, parity doc byte-exact, adapted `spx_probe.py`,
  `PROVENANCE.md`); native strategy `sleeves/milkman_0dte.py`;
  plumbing pair `adapters/milkman_0dte.py` +
  `adapters3/milkman_0dte.py`; one config row in
  `config/sleeves.json` (`mk_zerodte_spx`, roster 313 → 314, pins
  updated at the source); tests
  `tests/test_milkman_0dte_20261027_blockers.py`; proof
  `proof/install/mk_zerodte_spx.json`; BUGLOG entry
  MILKMAN-0DTE-INSTALL-20261027.
- **Constraints:** no existing sleeve's logic, sizing, stop, or
  threshold touched; Tensor files untouched; saty_sol pin untouched;
  Best Setups still disconnected and disabled; paper only.
- **Outcome:** the authored rules installed and wired the v3 way, in
  the task's named fallback state: **UNFED + PARKED**, with both
  reasons proven and named (below), rather than a faked feed.
- **Proof:** vendored sha256 == manifest (checked at landing and
  pinned in the blocker tests); 22 blocker tests pass with fail
  direction proven in both directions; full v3 gate GREEN.
- **Edges:** engine-side cash settlement of an expired SPXW contract
  is Femto-lean engine behavior with no v3 counterpart; the authored
  hard exit (flat 15 minutes before the close) is the operative
  protection in the native port, and a held-past-expiry contract is
  dropped from sleeve state on the next session's first pass, logged
  "expired", as authored (PROVENANCE, deferred list).

## What was built

The authored sleeve (DEC-02 on Claude's desk; the -$10,000 daily stop
is Milkman's own figure from his 2026-10-21 answers): SPX 0DTE, long
premium only, $2,500 premium per trade, at most 4 open, |delta|
nearest 0.40 among fresh (≤180 s) two-sided quotes ≤20% wide, bought
at the ask, sold at the bid, daily stop flattening + blocking
re-entry, no entry in the last 30 minutes, hard flat 15 minutes
before the close, ESMON/OPX4 excluded, inert with the named reason
"SPX 0DTE chain not available" until the probe proves the chain,
never a SPY fallback, never a model price. The native port's
`pick_contract` / `contracts_for` are logic-identical to the vendored
pure functions; the pass logic mirrors the vendored `signal()`.

## Feed state (proven 2026-10-27, desk's own credential route)

`desk3.producers` reads, expiration = today, read-only: SPX lists
**504** contracts expiring today (all root SPXW; the SPXW underlying
lists 0; XSP 556 and SPY 298 as controls). Snapshots answer two-sided
quotes (252 of 504 two-sided after the close; fresh = 0 after hours,
as expected). **with_delta = 0 on every snapshot**: feed=indicative
carries no greeks on this tier and feed=opra answers 403
(FEED-WIRE-20261025). The chain exists; the authored contract pick
cannot run on it, because it refuses delta-less rows by design.

## Why PARKED + UNFED (both named, both open)

1. **MILKMAN-INTRADAY-PORT (open):** entry signals are lane trades
   from Femto-lean `desk/sleeves/milkman/intraday.py`, the Milkman
   intraday study. It was not part of the vendored source set and has
   no v3 counterpart. The adapter's `lane_signals` seam stays empty;
   no detection was invented to fill it.
2. **SPX-GREEKS-ROUTE (open):** a greeks-bearing SPX feed (OPRA tier
   or a proven vendor route). The adapted probe's `with_delta` count
   is the standing proof instrument; the sleeve stays inert until a
   complete probe record says the chain is available AND rows carry
   delta.

The declared input `milkman_0dte_chain` has no producer, so the
registry marks the sleeve UNFED by name; the config row and the
strategy CONFIG both carry parked: true.

## Tests

`tests/test_milkman_0dte_20261027_blockers.py` — 22 tests, all
passing, gate-wired by the gate's `test_*_blockers.py` discover
pattern (which also satisfies the blocker ratchet for the four new
production modules by stem). Coverage: vendored hash pins; provenance
names the gaps; authored constants; contract pick (nearest 0.40,
spread/stale/expiry/no-delta rejections); premium sizing; inert
behavior (no record, unavailable record, never SPY); the entry path
through the named seam on a delta-carrying fixture chain; the tier
chain (no delta) naming its skip; the daily stop at exactly
-$10,000 (and not at -$9,999) flattening and blocking re-entry; the
hard exit; the signal exit at the quoted bid; the adapted probe
(evaluate counts incl. with_delta = 0, availability round-trip and
staleness, outside-RTH job records "not run"); the roster row
(314, parked, UNFED input, authored params).

**Fail-first proof:** pre-install tree fails at collection
(FileNotFoundError). Mutating `TARGET_DELTA` 0.40 → 0.55 fails 3
tests; mutating `DAILY_STOP` -10000 → -5000 fails 2 tests; both
restored byte-identical and the suite is green again.

## Gate

GREEN: `run_regression_blockers.sh` — **Ran 1277 tests, OK, exit 0**
(1255 pre-install + 22 new). Roster pins 313 → 314 updated at the
source in `tests/test_deploy_blockers.py` and
`tests/test_harden_batch1_blockers.py`, as the trullas install did
for 311 → 312. The desk's ConfigWatcher picks the new row up on the
next cycle (no restart, per OPERATIONS); the sleeve is parked, so
activation changes nothing executable until both open items close.
