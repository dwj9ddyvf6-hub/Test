# OPT_WHEEL_LIFECYCLE - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "OPT_WHEEL_LIFECYCLE", type options income, family wheel, algorithm grade PARTIAL, and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". Accounting gaps: "entry/signal rule not recorded in any consulted source" and "exit rule not recorded in any consulted source". Accounting algorithm sources: "femto land-wt config params", with parameters only `{"OPT_WHEEL_LIFECYCLE": {"symbols": []}}`. Alias status history: ausar_deployed "mode=unfunded_monitor running=False"; femto_land_wt "present in roster". Universe, asset class, timeframe and creator are "not recorded in consulted sources" / "not recorded" in the accounting.
- Classification evidence recorded on the accounting entry (2026-10-30): "femto-lean/core/options_feeds.py preserves mapping free_opt_wheel to OPT_WHEEL_LIFECYCLE, and desk3/strategies/free_opt_wheel.py sells a cash secured put then a covered call on assigned shares". That mapping was verified in this pass in Test at `packages/ausar/ausar-archive-rulebooks/core/options_feeds.py`: `_PRESERVES = {"free_opt_wheel": "OPT_WHEEL_LIFECYCLE", ...}` (the other four free_opt books map to their own OPT_ ids). The same file records the recovered rulebook verdict for this book: input_blocker "American_assignment_and_physical_share_ownership_cycle_adapter_required", originally monitor_only with initial_capital=0, and the desk activation note (ruling 2026-10-16) presenting the five free_opt parent books as active at the FREE_OPTIONS package pool of $100,000.
- Strategy card in Test: `strategies/femto/femto-free-opt-wheel.md` ("SPY 30-delta wheel"): "Sells a cash-secured 30-delta weekly SPY put; if assigned, sells 30-delta covered calls against the shares." Family Femto-lean; source Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean; asset ETF options; timeframe 1d (5-minute passes); universe SPY; style options income.
- Existing roster recreation package in Test for the same underlying sleeve under its sleeve id: `docs/FREE_OPT_WHEEL-RECREATE.md` (canonical roster id femto-free-opt-wheel). This package is the separate accounting-canonical package for OPT_WHEEL_LIFECYCLE; it does not rename or replace that doc.
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `sleeves/free_opt_wheel.py`, `desk3/sleeves/free_opt_wheel.py`, `config/sleeves.json`, `strategies/femto/femto-free-opt-wheel.md`, `docs/FREE_OPT_WHEEL-RECREATE.md` and `packages/ausar/ausar-archive-rulebooks/core/options_feeds.py`: the strategy, adapter, config row, card and mapping were all found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: no wheel sleeve path; the only wheel-named path is an unrelated jquery.mousewheel.js asset); dwj9ddyvf6-hub/quant-research-backup (recursive tree plus content reads: `femto-lean/sleeves/free_opt_wheel.py` is an earlier entry-only port, 4,167 bytes in the tree listing, and `femto-lean/ports/free_opt_wheel.md` is its port report; Test already holds the fuller lifecycle version of the same sleeve, so nothing was vendored from there); dwj9ddyvf6-hub/Midna (recursive tree: no wheel path). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

The options-income wheel lifecycle whose sleeve implementation is `free_opt_wheel`: sell one cash-secured put on SPY, and if the put is assigned, hold the resulting shares and sell covered calls against them until they are called away, then restart the cycle. It is a single-position sequential cycle (put, assignment, shares, covered call, called away, restart), not a parallel multi-leg book. The accounting name OPT_WHEEL_LIFECYCLE is the preserved rulebook-book name for this sleeve; the sleeve id in code and config is `free_opt_wheel`.

## Full algorithm

Everything below is from the code in Test (`sleeves/free_opt_wheel.py`, class FreeOptWheel, extracted from aurelia_free_options.py contracts()/evaluate()); where the accounting graded PARTIAL, the accounting's own recorded gaps are named at the end of this section. Evaluation order in `signal(bars, slice_state, context)`:

1. Shared quote freshness law (`fresh_quote` / `quote_block`): a quote is fresh only when its source stamp and receipt stamp are both present, neither is more than 2 seconds in the future (FUTURE_TOLERANCE_SECONDS = 2), source age <= 90 seconds (SOURCE_MAX_SECONDS = 90), receipt age <= 30 seconds (RECEIPT_MAX_SECONDS = 30), receipt is not earlier than source, and ask >= bid > 0. Stale, missing, crossed or malformed quotes fail closed.
2. Exits first (`_exit_intents`): for each held position in `context.extra["sleeve_state"]`, parse the OCC expiry from the symbol; an exit fires only on or after the expiry session (the designed exit is expiry; assignment itself is the broker's settlement, not an order). A short position buys to close at the snapshot quote ask from `context.extra["quotes"]`, a long position sells to close at the bid. At or past expiry the two-sided quote gate does not apply (the AUDIT3-C bypass recorded in the code).
3. Per-session entry dedupe: if any served record has `last_exit_date` equal to this session, or a held position whose `entry_date` is this session, no new entry is emitted this session (exits still return).
4. Covered-call step (`_covered_call_intent`): find the wheel shares record in `sleeve_state` (a position with `wheel="assigned"` and qty > 0, written by the core derivation in core/slice_sync.py when a put is assigned; its `entry_px` is the cost basis, strike minus the premium kept). If no open short call on the same underlying exists in the served state and `context.extra["call_quote"]` is fresh under step 1, parses as an OCC call (type character "C") on that underlying, and has strike > 0 and bid > 0, then contracts = int(shares // 100); if contracts < 1, no call. Enhancement gate (ENH, switch `context.extra["free_opt_wheel_enhance"]["enabled"]`, default ON; OFF restores the pre-change rule exactly, and the pre-change rule is recorded as a shadow paired record on `last_evaluation["paired"]` and never emits): refuse the call when the shares record's basis cannot be read, or when the call strike is below that basis. Otherwise emit one enter intent: the call OCC symbol, qty_hint = contracts, price_hint = round(bid, 2), reason naming sell_to_open, the strike, the covered underlying and the reserved shares.
5. Shares-leg block: while a wheel shares record is open (whether or not a call was emitted in step 4), return exits (plus any call) only; no new put is sold while the cycle is in its shares leg.
6. Cash-secured put entry: require a fresh `context.extra["quote"]`; read its strike, `context.extra["cash"]` and the quote bid. Require the strike finite and > 0, cash finite and cash >= strike x 100, and the bid finite and > 0. Require the quote symbol to parse as an OCC symbol whose type character at its fixed position is "P" (not a substring search). Emit one enter intent: qty_hint = 1, price_hint = round(bid, 2), reason naming sell_to_open 1 cash-secured put, the strike and the cash. The intent contract has no sell-to-open side; the entry carries its position intent in its reason for the core options path (named misfit M1 in the port report).
7. Producer contract selection (the part outside the sleeve file): the strategy card records the producer's selection as the nearest 7-14 DTE expiry, |delta| nearest 0.30, then strike nearest spot, for both the put and the later call, 1 contract. The archived producer in `packages/ausar/ausar-archive-rulebooks/core/options_feeds.py` supplies the wheel, when cash covers the selected strike's assignment, a put quote selected as the nearest expiry strictly after the session at the listed strike nearest the SIP spot on SPY (TAIL_UNDERLYING = "SPY"), and, while assigned shares have no covering call, a call quote selected the same way. Where these two selection records differ, both are recorded here; the sleeve itself consumes whichever quote it is served and applies steps 1-6 unchanged.
8. Adapter filter in the v3 desk (`desk3/sleeves/free_opt_wheel.py` calling `desk3/enh2_edge16.py` filter_wheel_zero_life_put, ENH2 switch default ON): refuse sell_to_open put entries whose OCC expiry is unparseable or on/before the session date; covered-call entries and exits are untouched.
9. Gaps, per the accounting: the accounting itself recorded no entry/signal rule and no exit rule (grade PARTIAL); steps 1-8 above are supplied by the code evidence, not by the accounting. The accounting's universe, asset class, timeframe and creator are not in the record, and its parameter block records no symbols (`symbols: []`); the SPY universe and the selection values in step 7 come from the strategy card and the producer code, not from the accounting.

## Files in this repo

- This package: `docs/OPT_WHEEL_LIFECYCLE-RECREATE.md`
- Strategy (already in Test): `sleeves/free_opt_wheel.py` (the desk3/strategies/free_opt_wheel.py strategy in desk layout; class FreeOptWheel, module-level `signal`).
- v3 adapter (already in Test): `desk3/sleeves/free_opt_wheel.py`; same adapter also at `integration/free_opt_wheel_adapter.py`.
- Producer / mapping (already in Test): `packages/ausar/ausar-archive-rulebooks/core/options_feeds.py` (`_PRESERVES` mapping free_opt_wheel to OPT_WHEEL_LIFECYCLE, the recovered rulebook verdict, and the wheel quote / call_quote supply).
- Other copies of the same sleeve in Test (already present, not used as the primary source): `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_wheel.py` and `packages/claude/master-desk-sleeve-port-library/desk/sleeves/femto/free_opt_wheel.py`.
- Strategy card: `strategies/femto/femto-free-opt-wheel.md`.
- Roster recreation package for the sleeve id: `docs/FREE_OPT_WHEEL-RECREATE.md`.
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED entry for OPT_WHEEL_LIFECYCLE.
- Earlier entry-only port outside Test (read only, not vendored; Test holds the fuller version): quant-research-backup `femto-lean/sleeves/free_opt_wheel.py` and `femto-lean/ports/free_opt_wheel.md`.

## Configuration

- Roster/config row for `free_opt_wheel` in Test `config/sleeves.json` (verbatim values): module `desk3.sleeves.free_opt_wheel`, strategy_module `desk3.strategies.free_opt_wheel`, cadence_s 300, parked false, slice capital_usd 10000.0 and cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, session "24h", timeout_s null, params {} (empty; all parameters live in the strategy code), inputs ["options"].
- Strategy constants in `sleeves/free_opt_wheel.py`: ACCOUNT = "free_options"; BUDGET_USD = 100,000.0 (the shared FREE_OPTIONS pool; the roster slice above is $10,000); SOURCE_MAX_SECONDS = 90; RECEIPT_MAX_SECONDS = 30; FUTURE_TOLERANCE_SECONDS = 2. SleeveConfig: sleeve_id "free_opt_wheel", cadence_s 300, universe (), state_schema {"position": "dict|None"}, risk_pct None.
- Switches: ENH `context.extra["free_opt_wheel_enhance"]["enabled"]` default ON (covered-call basis gate); ENH2 adapter filter default ON (zero-life put refusal).
- Accounting parameter block for OPT_WHEEL_LIFECYCLE itself: `{"symbols": []}`; any further accounting-level configuration is not in the record.

## Data inputs

- `context.extra["quote"]`: the served put quote, with symbol (OCC), strike, bid (`bp`), ask (`ap`), source stamp (`t` or `source_at`) and `received_at`.
- `context.extra["cash"]`: the book's cash available for the cash-secured test (cash = the book's cash less the strike value of its short puts, per the strategy card).
- `context.extra["call_quote"]`: the served call quote for the covered-call step, with symbol, strike, bid, ask and stamps.
- `context.extra["quotes"]`: snapshot quotes for held contracts, used by the expiry exit.
- `context.extra["sleeve_state"]`: served position records {symbol: {"position": {qty, entry_date, entry_px, wheel, ...}, "last_exit_date": ...}}, including the core-written assigned-shares record.
- SPY options chain and SIP spot (producer side, for contract selection); the sleeve's bars argument is ignored by the adapter (the strategy is called with empty bars).

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the UNRESOLVED accounting entry for OPT_WHEEL_LIFECYCLE in `docs/ALL-SLEEVES.json`, and the roster package `docs/FREE_OPT_WHEEL-RECREATE.md`.
3. Confirm the config row for `free_opt_wheel` in `config/sleeves.json` matches the Configuration section, and that `sleeves/free_opt_wheel.py` and `desk3/sleeves/free_opt_wheel.py` are present at those paths.
4. Wire the producer so each evaluation snapshot carries the Data inputs above: a fresh put quote and cash when the cycle is flat, a fresh call quote while assigned shares are uncovered, snapshot quotes for held contracts, and the served sleeve_state records (including the core derivation's assigned-shares record after an assignment).
5. Evaluate through the adapter: call `evaluate(view, ctx)` in `desk3/sleeves/free_opt_wheel.py`; it builds the old context from the snapshot and calls the strategy `signal(...)`, then applies the ENH2 zero-life put filter.
6. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo; the roster package notes the desk's port blocker tests pin the vendored strategy files by sha256):

- Quote law: a quote with source age 91 seconds, receipt age 31 seconds, a stamp more than 2 seconds in the future, receipt earlier than source, or ask < bid or bid <= 0 produces no entry.
- Cash test: cash exactly equal to strike x 100 enters; cash one cent below does not.
- OCC type test: a call symbol (type character "C") supplied as the put quote produces no put entry, even though the underlying letters contain "P".
- Cycle order: with an assigned shares record open, no new put is sold; with 250 reserved shares and no open covering call, exactly 2 covered-call contracts are offered at the call bid.
- ENH gate: with the switch ON, a call strike below the shares record's entry_px basis, or an unreadable basis, produces no call; with the switch OFF, the pre-change rule applies.
- ENH2 filter: a sell_to_open put expiring on or before the session date is refused; one expiring after it passes.
- Exits: an exit fires only on or after the held contract's OCC expiry, buying to close a short at the ask without requiring a two-sided quote.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
