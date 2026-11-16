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

## Gap 1 CLOSED — the intraday study port (MILKMAN-0DTE-PORT-20261116)

The study was recovered from the GitHub Femto-lean repo, branch
`milkman-0dte` at commit 8c64cd5cc53a (the same commit the vendored
sleeve came from), via the ghapi route:

- `intraday.py` — Femto-lean `desk/sleeves/milkman/intraday.py`,
  blob d6339131541cc460b7650d468d99cd691606f6f8, 59,999 bytes,
  sha256 77034c9fc88edea81fa304e2bd7cbe13b952b739a4b8fd9accf1c873b7785362.
  Landed BYTE-EXACT as a provenance artifact (like the vendored
  sleeve above; nothing live imports it — its femto framework has
  no v3 counterpart). It is itself the port of milkman-study/v2
  `21_intraday.py` / `22_intraday2.py` (quant-research-critical@
  0be4c57569e363d052bd23564cf0664697439927), with the femto parity
  receipt at Femto-lean `docs/receipts/parity/milkman_intraday.json`
  (blob b708e9189fbcca989b74e46493fe62f74df79d3f, sha256
  ee0eed2759350cd030a2d1bb7b399da57fbcbfc87a12c81922211a47cc2c8fd6):
  1,778 cases identical, 26,854 lane trades, 0 diffs.
- `mlib.py` — the study's own library (Femto-lean
  `desk/vendor/milkman/mlib.py`, blob
  0e488ae7ad34c37197b7141afb3ba5d1483892f6, sha256
  0c6823c0c1a55ca8520f5121c8660ff46170813a67fb24a2c5e51adb16a536b9).
  Landed BYTE-EXACT and imported live by the port (its ema / atr /
  po / compression are the study's indicator definitions).
- `intraday_study.py` — the v3-native port: the vendored module's
  detection (Panel, detect21, detect10, detect_cdc, the LEMA /
  MDL / PMATH / GUPN engines, step_exit / run_exit, lane_trades,
  SETUPS / SOURCE / LATE) line-for-line, with only the dependency
  surface changed (mlib direct; a calendar shim over v3's
  canonical calendar; the femto Sleeve class / Yahoo feed_spy /
  registry dropped — full statement in its docstring). Proven by
  differential comparison against the byte-exact vendored module
  in tests/test_milkman_0dte_port_20261116_blockers.py.
- Wiring: `adapters/milkman_0dte.py` builds the Panel from the
  snapshot's SPY bars (Alpaca SIP 1Min 18 days, 1Hour 200 days,
  1Day 500 days — the warm products) and fills `lane_signals` /
  `lane_exits` applying the vendored authored sleeve's own
  eligibility rules (same_bar, missed, LATE=2, ESMON/OPX4
  excluded). `adapters3/milkman_0dte.py` declares the SPY 1-minute
  inputs. No sizing, stop, or chain-feed change.

Named lane-level limitation (the one unsourced-on-live-data
piece): the LEMA lane's threshold is the train-period (2000-2012)
body/range quantile of the daily table. The snapshot's daily
history is 500 days, so the threshold is None live and that lane
alone produces no signals — the source's own fail-closed
behaviour when the train years are absent. The rule is ported
and proven on train-era fixtures; it stays dark until a daily
source carrying 2000-2012 SPY sessions is served to the panel.
Routes tried for that history: (1) the warm bars product
(SPY|1Day, 500 days — insufficient by construction); (2)
bars_secondary (Yahoo daily, range 2y — insufficient); (3) the
estate's files (no SPY daily history back to 2000 on this desk).
No other lane is affected.

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

Historical install record. Both reasons are superseded: gap 2 by
MILKMAN-CHAIN-20261114 (the chain producer with computed delta;
the sleeve was unparked 2026-11-14) and gap 1 by
MILKMAN-0DTE-PORT-20261116 (the study port at the top of this
file). The text below stands as the install-era record.

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
