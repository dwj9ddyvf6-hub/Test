# Milkman 0DTE SPX: provenance (2026-10-27)

Source: Femto-lean repo, branch `milkman-0dte`, fetched via the
program manifest at
`~/workspace/peer-execute-20261027/sources/MANIFEST.json` (group
`d_milkman`). Installed under EXECUTE-SCOPE-2026-10-27 item 4 (the owner's
order 2026-10-27 19:07 ET), following the trullas_divergence install
pattern in this repo. The sleeve's own origin is Claude's master-desk
commit 8c64cd5c (2026-10-27, citing his DEC-02); the $10,000 daily
stop is Milkman's own figure (his answer to the owner, 2026-10-21). Paper
only, like every sleeve on this desk.

## Landed byte-exact (sha256 equals the manifest)

- `milkman_0dte.py` 202841b379c96120b6e859a4a576d76fde8b4b24f7653b57a56ce7d04be106ee
  (the authored sleeve: SPX 0DTE, $2,500 premium per trade, max 4
  open, |delta| nearest 0.40, max spread 20%, quote age 180 s,
  -$10,000 daily stop, no entry in the last 30 minutes, hard flat 15
  minutes before the close, ESMON and OPX4 excluded, inert with the
  named reason "SPX 0DTE chain not available" until the probe records
  the chain, never a SPY fallback, never a model price)
- `2026-10-27-milkman-0dte-parity.md` 47ef6e9a6a9c69f998dbf74ce4563e138ae2ed67b953390801d0145e6e81fa27

The vendored sleeve is a provenance artifact. It imports Femto-lean's
desk.contract / desk.calendar / desk.data and the Milkman intraday
study; none of those exist in muse-desk-v3, and nothing in the live
desk imports this file (the blocker test pins it as record, and the
live expression of the rules is the native port below).

## Landed with adaptation (marked PORT-ADAPT in-file)

- `spx_probe.py` (source sha256
  2aa56969b48ce4f146f55736f77e3ff20d220efb318912eae0177d4b683e83ce):
  same record schema, constants and verdict rules; reads re-expressed
  through desk3.producers (the desk's verified Alpaca path) and
  desk3.run_live.credential_env; one honest addition, a `with_delta`
  count per attempt (see gap 2 below).

## The v3-native landing (trullas pattern)

- `sleeves/milkman_0dte.py`: the authored decision rules on the
  core/sleeve.py contract: pick_contract and contracts_for are
  logic-identical ports of the vendored pure functions; the pass logic
  (inert abstention, signal exits, daily stop flatten + no re-entry,
  no-entry window, hard exit, expiry drop) mirrors the vendored
  signal() against v3's Context channels (extra: milkman_state,
  spx_probe, chain_rows, quotes, lane_signals, lane_exits, book_pnl).
- `adapters/milkman_0dte.py` + `adapters3/milkman_0dte.py`: plumbing
  only, following adapters/trullas_divergence.py.
- `config/sleeves.json`: one row, id `mk_zerodte_spx`, cadence 60 s,
  RTH, $10,000 slice (desk norm for installs), parked: true, declared
  input `milkman_0dte_chain` — a key no producer produces, so the
  sleeve lands UNFED by name in the registry, never fake-fed.

## Why PARKED + UNFED (the named reasons, both proven 2026-10-27)

1. **The signal study is not in the vendored set.** Entry signals are
   lane trades from Femto-lean `desk/sleeves/milkman/intraday.py`
   (the Milkman intraday study over a SPY 1-minute panel). That
   module was not among the fetched sources and has no v3
   counterpart, so no authored signal can reach the sleeve. The
   native sleeve's entry path runs only off the named `lane_signals`
   seam, which the adapter leaves empty; inventing detections would
   be authoring a new strategy, which this install does not do.
   OPEN: port desk/sleeves/milkman/intraday.py + its SPY panel feed,
   with its own parity harness, before any un-park.
2. **No delta on this account tier.** Live probe through the desk's
   own credential route, 2026-10-27 (desk3.producers,
   expiration = today, max_dte = 0): SPX lists 504 contracts expiring
   today (root SPXW; the SPXW underlying lists 0; XSP 556 and SPY 298
   as controls). Snapshots answer two-sided quotes, but
   feed=indicative carries NO greeks and feed=opra answers 403 on
   this tier (FEED-WIRE-20261025, re-proven by the alt-data phase the
   same day). The authored pick refuses rows without a delta
   ("no delta"), so even a proven chain cannot produce an authored
   contract choice here. OPEN: a greeks-bearing SPX feed route
   (OPRA tier or a proven vendor route), proven by the adapted
   probe's `with_delta` count, before any un-park.

The chain itself is NOT the blocker: contracts and quotes are
reachable on this tier, and the adapted probe in this package is the
standing evidence path (`python3 -m desk3.milkman_0dte.spx_probe`,
in-session, once per session, writes state/probes/spx_0dte.json).

## Deferred (OPEN, by name)

- Milkman intraday study port (gap 1), including its parity harness.
- Greeks-bearing SPX chain route (gap 2).
- Engine-side cash settlement narration for expired SPXW contracts:
  the vendored sleeve relies on Femto-lean's engine settlement; v3's
  dispatcher closes expiring index positions through its own exit
  paths. The native sleeve's hard exit (15 minutes before the close,
  as authored) is the operative protection here; a held-past-expiry
  contract is dropped from sleeve state on the next session's first
  pass and logged "expired", as authored.
