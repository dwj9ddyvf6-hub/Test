# BEST-SETUPS-PRESERVATION — vendored Best Setups, byte-identical

Source: femto-lean @ 2febc462aca8fc6170c82a623cd69450d4c496c9 (V3-SCOPE §4).
Vendored 2026-10-24 into `best_setups/` (layout preserved: core/, tools/).
The vendored files are NEVER modified — any byte drift fails the gate.

## Manifest (sha256, verified at vendor time and by blocker)

| File | sha256 |
|---|---|
| core/setups_curator.py | a6a98dbe0bedb12d89d726f4182a3f685b13e861b3dc70c1dc20dab4e327e06c |
| core/setup_card.py | 174541c28ea00ae4d91d50fb87626b3bd4794ed491b2216b9544aecf91863ba4 |
| core/setup_brief.py | 1796be7c60a8250ad46eb29b95b5d4b6aa486ca38d70b31a03ef761cd77fff53 |
| core/setup_call.py | 99b178105c0e5216d877f31618b28f57308a8ce4e6300cf2bb476911cc5dcc68 |
| core/setups_publish.py | fde1c81ac9ac624977b8a0c6caea2b060af1f121528fe7681892e16a150c4e4c |
| tools/build_setups.py | 9e7c7313dcb6d64eb4e9c20cd6112b0376f82e2ac5efb9e6e3142f12c9616f54 |
| tools/build_briefs.py | e1eeb07e8c7898aa87e28ac47ba771a6adc98d2be6c8989875504b37a02f9868 |
| tools/build_market_charts.py | 786d725fced920a8468d362408bdcdd1018c0d3257ed0ca8eaf5b08ce07eb264 |

All 8 match the §4 pins (full hashes re-derived from the original tree
at vendor time, not copied from the scope doc's truncated pins).

## Integration (exactly as the current desk)

Current desk: `tools/run_live.publish_feed` -> `core.setups_publish.
enrich_snapshot` / `merge_setups_into_snapshot` extends the
desk-terminal snapshot. v3: `desk3/best_setups_lane.py`
`enrich_terminal_snapshot(snapshot, setups_doc, briefs_doc)` delegates
to the vendored merge (subprocess rooted at best_setups/ — the
vendored package is also named `core` and collides with v3's own core
package; isolation only, no code change). Same inputs in, same
snapshot keys out: setups, entered_setups, setups_completed,
considered, market_context, scoring_method, lector_top, lector_as_of,
setups_as_of, notes, departures, pullback_*.

## Golden proof (behavioral identity)

Corpus: the ORIGINAL system's recorded outputs — femto-lean
`state/live/setups_latest.json` (sha256 094ac7ff…b67d) and
`state/live/setup_briefs.json` (10545ba0…ab95), copied to
`best_setups/golden/inputs/`. Driver `best_setups/golden/run_golden.py`
exercises, on those recorded inputs: setup_call.compose_call over all
11 briefs (plan/desk_read/levels/elliott from the recorded briefs),
curator geometry/underlying/ATR/ran_past_entry/market_context over
the recorded levels + spark closes, scoring_method_table/FAMILIES,
and the full setups_publish merge into a terminal snapshot.
Golden output produced by the ORIGINAL tree:
`best_setups/golden/golden_output.json` sha256
0081d53af389e645a2c91ff2244464584cbd2bee6ea1d964ed8b772e3982bac1.
Vendored copy on the same inputs: BYTE-IDENTICAL (cmp clean).

Coverage ledger: proven — setup_call, setups_curator (pure paths),
setups_publish merge. Hash-only — setup_card, setup_brief,
tools/build_*: their full rendering/generation paths need femto-lean
core deps outside the §4 vendor list (arbiter/branches/census/…,
gateway, the desk SIP door); byte-identity is their preservation
proof, and no v3 code path modifies them. Live surface (CURE2-4, 2026-10-24): every cycle merges the latest
setups doc (state/setups_latest.json when present, else these golden
inputs — the last published setups of record) through the vendored
merge into BOTH live terminal surfaces (state/terminal_feed.json and
state/terminal.json), labelled setups_source; blocker
TestLiveTerminalSetups proves the keys on a live cycle. Full
end-to-end GENERATION against v3 state (a curator run) remains
A8's open half, named OPEN.

## Blockers (gate-wired)

tests/test_best_setups_blockers.py (5 tests): hash pins over all 8
files + no-extra-files, golden-diff (subprocess vs stored golden),
lane integration keys == golden merged output. Fail direction proven:
a one-byte tamper of a /tmp copy changes its sha256 off-pin (hash
blocker) — the vendored tree itself was never touched.
