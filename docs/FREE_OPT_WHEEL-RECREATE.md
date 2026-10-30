# free_opt_wheel: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-wheel.md in this repo: Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean.

## What this sleeve is
This sleeve runs a cash-secured SPY put wheel: it sells one put only when served cash covers assignment, and after assignment (a core ledger state transition) it sells covered calls against the assigned shares. In v3 it is a thin adapter (desk3/sleeves/free_opt_wheel.py) over the strategy in desk3/strategies/free_opt_wheel.py, with an added adapter-level zero-life-put filter.

## Full algorithm
Shared quote law (all three free_opt strategies, desk3/strategies/<id>.py): a quote is fresh only when its source stamp and receipt stamp are both present, neither is more than 2 s in the future, source age <= 90 s, receipt age <= 30 s, receipt is not earlier than source, and ask >= bid > 0. Exits are evaluated before entries in signal(). Entries are deduped per session: if any served sleeve_state record has last_exit_date == this session, or a held position whose entry_date is this session, no new entry that session. The virtual ledger account is "free_options" with BUDGET_USD = 100,000 (the shared free-options pool); the roster slice is $10,000. SleeveConfig in the strategy: cadence_s=300, universe=(), state_schema={"position": "dict|None"}, risk_pct=None. Each strategy also has an ENH switch in context.extra["<id>_enhance"]["enabled"], default ON; OFF restores the pre-change rule exactly, and the pre-change rule is recorded as a shadow paired record on last_evaluation and never emits intents. After the strategy returns, the v3 adapter applies its own ENH2 filter (extra["<id>_enh2"]["enabled"], default ON) named per sleeve below; exits are never filtered by ENH2.
This sleeve's rules (desk3/strategies/free_opt_wheel.py, class FreeOptWheel), evaluated in this order:
(1) Exits first (_exit_intents): for each held position, parse its OCC expiry; only at/past expiry does an exit fire (the designed exit is expiry; assignment itself is the broker's settlement, not an order). A short position buys to close at the quote ask, a long sells to close at the bid, from extra["quotes"]; the two-sided quote gate does not apply at/past expiry.
(2) If already entered this session, return exits only.
(3) Covered-call step (_covered_call_intent): find the wheel shares record in extra["sleeve_state"] (a position with wheel="assigned" and qty > 0, written by the core derivation when a put is assigned; its entry_px is the cost basis, strike minus premium kept). If such a record exists and no open short call on the same underlying exists in the served state, and extra["call_quote"] is fresh under the shared quote law, is a call (OCC type character "C") on that underlying, with strike > 0 and bid (bp) > 0, then contracts = int(shares // 100); if contracts < 1, no call. ENH gate (default ON): refuse the call when the shares record's basis cannot be read or the call strike is below that basis. Emit one enter intent: the call OCC, qty_hint=contracts, price_hint = round(bid, 2), reason naming sell_to_open, the strike, the underlying and the reserved shares. The existing card describes the producer's selection (not in this strategy file): the nearest 7-14 DTE expiry, |delta| nearest 0.30, then strike nearest spot, for both the put and the later call, 1 contract.
(4) If a wheel shares record is open (whether or not a call was emitted), return exits (plus any call): no new put is sold while the cycle is in its shares leg.
(5) Cash-secured put entry: require a fresh extra["quote"]; read strike, extra["cash"] and the quote bid (bp). Require strike finite and > 0, cash finite and cash >= strike x 100, and bid finite and > 0. Require the quote symbol to parse as an OCC symbol whose type character is "P" (parsed at its fixed position, not a substring search). Emit one enter intent: qty_hint=1, price_hint = round(bid, 2), reason naming sell_to_open 1 cash-secured put, the strike and the cash.
Adapter ENH2 filter (desk3/enh2_edge16.py filter_wheel_zero_life_put): refuse sell_to_open put entries whose OCC expiry is unparseable or on/before the session date (from view["now"]); covered-call entries and exits are untouched.

## Files in this repo
- Sleeve module (desk desk3/sleeves/free_opt_wheel.py): `desk3/sleeves/free_opt_wheel.py`.
- Strategy (desk desk3/strategies/free_opt_wheel.py): `sleeves/free_opt_wheel.py`.
- Shared bridge: `engines/desk3/bridge.py` (desk desk3/bridge.py: ViewCtx, build_extra, old_context, to_v2_intents).
- ENH2 adapter filters: `engines/desk3/enh2_edge16.py` (desk desk3/enh2_edge16.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from desk3.contract / core.sleeve).
- Existing per-sleeve card: see the Provenance line's source doc path in docs/ALL-SLEEVES.md / the strategies/ tree.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: 24h.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: options.

## Data inputs
- The adapter's evaluate(view, ctx) ignores the bars argument for the strategy call (`_signal({}, {}, old_context(c, extra))`); all strategy inputs arrive in context.extra built from view["extra"], view["kraken_inputs"], view["options_chain"] and view["bars"].
- context.extra keys consumed by the strategy are named per sleeve in the Full algorithm section (quote / quotes, package, events, cash, call_quote, sleeve_state, session_dates). Freshness is judged inside the strategy from the quote source and receipt stamps (source <= 90 s, receipt <= 30 s, future tolerance 2 s); stale, missing, crossed or malformed quotes fail closed.
- Positions / held records arrive as extra["sleeve_state"]: {symbol: {"position": {qty, entry_date, entry_px, ...}, "last_exit_date": ...}}.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `free_opt_wheel` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the shared quote law, and that cash exactly equal to strike x 100 enters while cash one cent below does not.
- Check the OCC type test: a call symbol (type character "C") supplied as the put quote produces no put entry, even though the underlying letters contain "P".
- Check the cycle order: with an assigned shares record open, no new put is sold; with 250 reserved shares and no open call, exactly 2 covered-call contracts are offered at the call bid.
- Check the ENH covered-call gate: a call strike below the shares record's entry_px basis, or an unreadable basis, produces no call with the switch ON.
- Check the adapter ENH2 filter refuses a sell_to_open put expiring on the session date and passes one expiring after it.
- Check exits fire only at/past OCC expiry, buying to close a short at the ask without requiring a two-sided quote.
