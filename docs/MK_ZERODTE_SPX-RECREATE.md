# mk_zerodte_spx: Recreation package

Provenance: Milkman Trades' 0DTE SPX method, from his 2026-10-21 answers and the authored Femto-lean sleeve (milkman-0dte branch), installed 2026-10-27 (Source row in strategies/milkman/mk-zerodte-spx.md in this repo).

## What this sleeve is
This sleeve buys SPX same-day-expiry premium in the direction of authored intraday lanes, picking the contract nearest 0.40 delta from fresh two-sided quotes, with a $2,500 premium budget per trade and a -$10,000 daily stop. It is parked and inert at install by design: the SPX 0DTE chain with greeks is not proven on this desk and the authored lane-signal study is not ported, so it never falls back to SPY options or a model price. Sources: desk sleeves/milkman_0dte.py, adapters3/milkman_0dte.py and desk3/milkman_0dte/.

## Full algorithm
Strategy (desk sleeves/milkman_0dte.py, Milkman0DTESleeve.signal(), the v3-native expression of the authored sleeve vendored byte-exact at desk3/milkman_0dte/milkman_0dte.py), in this order. Constants: CAPITAL=1,000,000.0 (the authored book figure carried in the module; the desk slice is $10,000, see Configuration); DAILY_STOP=-10,000.0; PREMIUM_PER_TRADE=2,500.0; MAX_OPEN=4; TARGET_DELTA=0.40; MAX_SPREAD=0.20; QUOTE_MAX_AGE_S=180.0; NO_ENTRY_S=1800 (no entry in the last 30 minutes); HARD_EXIT_S=900 (hard flat 15 minutes before the 16:00 ET close); EXCLUDED=("ESMON", "OPX4"); ROOTS=("SPXW", "SPX"); INERT reason string "SPX 0DTE chain not available".
1. Session handling first: on a new session, positions still open from a prior session are dropped and logged expired (settled at the official SPX close), and the day state resets. Outside weekday RTH (09:30 to before 16:00 ET) the evaluation returns nothing.
2. Daily stop and hard flat before any entry logic: when ctx.extra book_pnl reaches -10,000 or below, the book is marked stopped, every held SPX-root contract is sold at its quoted bid (sell_to_close), and entries are blocked for the rest of the session. The same full flattening at the quoted bid happens inside the last 15 minutes before the close.
3. Lane exits next: for each key in ctx.extra lane_exits whose contract is held, sell it at the quoted bid, mark the key done, and log the signal exit.
4. Inert gate: unless ctx.extra spx_probe records available True for SPX, no entry is emitted, the evaluation state is inert, and the abstention names the reason "SPX 0DTE chain not available" plus the probe's why. Inside the last 30 minutes before the close, no entry is emitted either.
5. Lane entries: a lane signal {key, side} in ctx.extra lane_signals is skipped when its key is an excluded lane (ESMON or OPX4), the key is already open or seen, or 4 positions are already open. Long premium only: side above 0 buys a call, side below 0 buys a put.
6. Contract choice (pick_contract): among today's-expiry contracts of that type with root SPXW or SPX, keep only rows with a two-sided quote (bid above 0, ask at or above bid), quote age at most 180 seconds, spread (ask - bid) / ask at most 0.20, and a delta present (rows without a delta are never chosen from); pick the row whose absolute delta is nearest 0.40, symbol ascending on ties. No qualifying row means no entry, with the reason logged. No model price anywhere.
7. Sizing (contracts_for): whole contracts for the $2,500 premium at the quoted ask (ask times 100 per contract); one contract is allowed when a single contract costs up to 1.5 budgets (3,750); otherwise 0 and no entry. Entries are limit orders at the quoted ask, buy_to_open, reason naming the lane key, contract, quantity and ask and bid.

## Files in this repo
- Strategy: sleeves/milkman_0dte.py (Milkman0DTESleeve, pick_contract, contracts_for).
- Vendored authored source in the desk tree: desk3/milkman_0dte/milkman_0dte.py (byte-exact authored sleeve) with desk3/milkman_0dte/PROVENANCE.md and the probe desk3/milkman_0dte/spx_probe.py; in this repo the authored family copy is at packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/milkman_0dte.py and the strategy copy at sleeves/milkman_0dte.py.
- Plumbing adapter in this repo: adapters/milkman_0dte.py is the desk adapter path named by the entrypoint (the repo tree carries adapters3/milkman_0dte.py); v3 worker entrypoint: adapters3/milkman_0dte.py (SLEEVE_ID=mk_zerodte_spx, module adapters3.milkman_0dte).
- Shared contract: sleeves/muse/core/sleeve.py (BaseSleeve, Intent, SleeveConfig).
- Shared v3 plumbing: adapters3/_snapshot_ctx.py (SnapshotSleeveContext) is used by the desk entrypoint and is NOT in this repo tree (audit missing shared file); take it from the desk source tree.
- Existing docs in this repo: strategies/milkman/mk-zerodte-spx.md and docs/MK_ZERODTE_SPX-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=mk_zerodte_spx), also at config/sleeves.json.

## Configuration
Module adapters3.milkman_0dte; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; timeout_s null; inputs [bars, positions, milkman_0dte_chain]; parked true. Params in the roster row: daily_stop -10000.0, premium_per_trade 2500.0, max_open 4, target_delta 0.4, excluded_setups [ESMON, OPX4], and an inert_reason naming both blockers (the authored intraday study not ported, so no lane signals; and no delta or greeks on this account tier). Universe: SPX 0DTE options only (roots SPXW or SPX); timeframe intraday. Source: muse-desk-v3/config/sleeves.json row id=mk_zerodte_spx.

## Data inputs
Inputs are bars, positions and milkman_0dte_chain. The milkman_0dte_chain input (today's SPX 0DTE chain rows with symbol, root, expiration, type, strike, bid, ask, delta and quote time, greeks included) has NO producer on this desk: the options producer serves SPY, QQQ, IWM and XSP via feed=indicative, which carries no greeks, and SPX is not in its underlying set; declaring the key by name keeps the sleeve visibly UNFED, never fake-fed. The adapter also builds ctx.extra channels: milkman_state, spx_probe (from the probe record), chain_rows, quotes for held contracts, lane_signals (left empty because the authored intraday study is not ported), lane_exits and book_pnl. Until the probe records available True, the sleeve is inert.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `mk_zerodte_spx` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the v3 worker module adapters3/milkman_0dte.py, whose evaluate(view, ctx) rebuilds the snapshot context and delegates to adapters/milkman_0dte.py, which runs sleeves/milkman_0dte.py signal(). Because the roster row is parked, the recreation must reproduce the inert state exactly: no entries while the probe is unavailable.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- No per-sleeve test file for this sleeve exists in this repo; use this behaviour checklist instead.
- Fixture with no spx_probe record (or available not True): no entry, evaluation state inert, and the named reason contains "SPX 0DTE chain not available".
- Fixture with the probe available, a fresh lane signal, and a chain whose qualifying contract has absolute delta nearest 0.40 among fresh (at most 180 s), two-sided, at most 20 percent wide quotes with a delta present: exactly one buy_to_open limit entry at the quoted ask, contracts_for(ask) contracts, at most 4 open.
- Fixture with book_pnl at or below -10,000, or inside the last 15 minutes before the close, with a held SPX-root contract: full sell_to_close exits at the quoted bid and no entries. Fixture with an ESMON or OPX4 lane key: no entry for that lane.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
