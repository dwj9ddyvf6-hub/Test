# przm_fade_edges: Recreation package

Provenance: PRZM (przm.space) public record: Flight Manual V201 and the public client fallback engine, recreated per PRZM-RECREATION-SPEC-2026-10-29 (Source row in strategies/muse/muse-przm-fade-edges.md in this repo; the spec's Source line is: Source: TEARDOWN.md (PARTIAL) in this directory; evidence manifest evidence/meta/capture_manifest.sha256 (6,788 entries). Public material only.)

## What this sleeve is
This is a parked, paper-only SPY recreation of the PRZM Zero Fade Edges state: in a pin regime it fades the session high or low toward the gamma magnet, and in a run it stands aside. Because the desk chain producer serves delta-only rows with no gamma or open interest, gamma levels cannot be computed and it currently trades nothing.

## Full algorithm
The strategy logic is in sleeves/przm_fade_edges.py and delegates to no desk3 engine. Constants: SYMBOL SPY, EDGE_TOL_FRAC 0.0005, INVALID_FRAC 0.0015, NOTIONAL_PER_FADE $2,000, MAX_OPEN_FADES 2 (module constant), edges first fadeable at 10:00 ET, entries 09:45 to 15:15 ET, flat at 15:45 ET.
Waiting state first: today's SPY 1-minute RTH bars are built; if there are none, state no_bars_today. Gamma levels are computed from ctx.extra przm_chain; if gamma_levels() returns None, last_evaluation is WAITING_NO_GAMMA_LEVELS with regime None and the sleeve returns no intents.
Gamma (recreated, in gamma_levels): for each chain row with a readable strike, gamma, open interest (open_interest or oi) > 0 and right in call/put/c/p, per-strike net GEX += sign * OI * gamma * 100 * spot, with sign +1 for calls and -1 for puts; rows missing any of those fields are skipped, and if no usable row exists the result is None. Magnet = strike with the largest absolute net GEX. Flip = first strike, scanning strikes ascending, at which the cumulative net GEX changes sign; if there is no sign change the result is None.
Regime (extracted test, regime_for): pin when spot > flip, run otherwise; no substitute test is used.
Management of an open fade (a plan exists and quantity is open), exit in this order of tests with the first matching reason winning: regime == run (do not fight it); time at or after 15:45; magnet reached (short: latest close <= magnet; long: latest close >= magnet); invalidation (short: latest close > edge * 1.0015; long: latest close < edge * 0.9985). Any match emits one full exit Intent at spot and clears the plan. A plan with no fill yet reports awaiting_fill.
Entries, only when regime is pin: gates in order are entry time in 09:45 to 15:15 ET, time at or after 10:00 ET (edges_not_printable_before_1000), and equity > 0. Session high = maximum high and low = minimum low of today's bars. Short fade when spot >= hi * (1 - 0.0005), hi > magnet and the high edge was not already faded today; long fade when spot <= lo * (1 + 0.0005), lo < magnet and the low edge was not already faded. An edge already past the magnet is spent: no trade. Otherwise state pin_no_edge_touch. On an entry: qty = max(1, int(2000 // spot)), stop = round(edge * 1.0015, 4) for a short / round(edge * 0.9985, 4) for a long, target = magnet, exit_rules stop and target, side sell / sell_to_open or buy / buy_to_open, the faded edge is recorded in faded_edges (one fade per edge per session) and a plan {direction, edge, magnet, flip, entry=spot, session} is stored in przm_fade_state.

## Files in this repo
- Sleeve module (all strategy logic): sleeves/przm_fade_edges.py. Adapter (plumbing): adapters/przm_fade_edges.py in this repo. V3 entry point: adapters3/przm_fade_edges.py (SLEEVE_ID=przm_fade_edges).
- Shared engine files: none; audit records engine_files_needed as empty and the module delegates to no desk3 engine. It imports the generic framework core.sleeve at sleeves/muse/core/sleeve.py (also at packages/claude/master-desk-sleeve-port-library/desk/sleeves/muse/core/sleeve.py). Note, from the audit: adapters3/przm_fade_edges.py imports adapters3/_snapshot_ctx.py and adapters/przm_fade_edges.py imports adapters/_bridge.py, neither of which is in this repo, so a fresh desk must supply those two plumbing files from the desk source.
- Existing docs: docs/PRZM-RECREATION-SPEC-2026-10-29.md, docs/PRZM-RECREATION-BUILD.md and strategies/muse/muse-przm-fade-edges.md.
- Config: engines/config/sleeves.json (row id=przm_fade_edges), also at config/sleeves.json.
- Tests in this repo: tests/test_przm_recreation_blockers.py.

## Configuration
Module adapters3.przm_fade_edges; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {parked_reason: WAITING_NO_GAMMA_LEVELS: desk options_chain producer serves delta-only rows (feed=indicative, no greeks, no open interest), so gamma magnet/flip cannot be computed; PRZM-RECREATION-SPEC-2026-10-29 waiting state. Unpark when chain rows carry gamma+OI.}; inputs [bars, bars_1min, bars:SPY:1Min, options, options_chain, positions, quotes, session_fills]; parked true. Universe: SPY only; timeframe 1-minute bars. Source: muse-desk-v3/config/sleeves.json row id=przm_fade_edges.

## Data inputs
Inputs are bars / bars_1min / bars:SPY:1Min (SPY 1-minute bars for today, RTH, with o/h/l/c), options and options_chain, positions, quotes and session_fills. The strategy consumes bars[SPY], ctx.now, ctx.session, ctx.equity, the held SPY quantity in slice_state, ctx.extra przm_fade_state (faded_edges, plan, regime_log round-tripped by the adapter) and ctx.extra przm_chain (chain rows with strike, gamma, open interest / oi and right / type). Chain rows lacking gamma or open interest produce the WAITING_NO_GAMMA_LEVELS state above, by design.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (sleeves/muse/core/sleeve.py is core/sleeve.py on a fresh desk; sleeves/trullas_divergence.py and sleeves/investandbefree_dmac.py are the same paths on a fresh desk).
2. Register the config row for `przm_fade_edges` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/przm_fade_edges.py, whose evaluate(view, ctx) builds a SnapshotSleeveContext and delegates to adapters/przm_fade_edges.py, which runs sleeves/przm_fade_edges.py signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep the sleeve parked exactly as in that row; the waiting behaviour in the Full algorithm section is the expected behaviour until its named input route is proven.

## Verification
- Run tests/test_przm_recreation_blockers.py in this repo: hand-worked gamma magnet / flip, a pin fade fixture, a run stand-aside fixture, a regime-flip exit and the WAITING state must all pass.
- Fixture with chain rows lacking gamma or open interest: no intent and last_evaluation state WAITING_NO_GAMMA_LEVELS.
- Fixture in a pin (spot above the flip) at or after 10:00 ET with spot within 0.05% of the session high and that high above the magnet, and the high not yet faded: exactly one short enter Intent, qty max(1, int(2000 // spot)), stop round(edge * 1.0015, 4), target the magnet; the mirrored low fixture gives the long.
- Fixture in a run regime, before 10:00 ET, outside 09:45 to 15:15 ET, or at an edge already past the magnet: no entry.
- Fixture with an open fade: a close at or through the magnet, a close 0.15% beyond the faded edge, a regime flip to run, or 15:45 ET each emit exactly one full exit with the matching reason; the same edge is not faded twice in one session.
- The config row used by the recreation matches engines/config/sleeves.json for przm_fade_edges (module, cadence, session, slice, parked true with the named reason, and inputs).
