# free_opt_tail: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-tail.md in this repo: Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean.

## What this sleeve is
This sleeve buys one SPY put after a down day of 3% or more, as a tail hedge, and exits after five sessions, at a 50% premium loss, or at expiry. In v3 it is a thin adapter (desk3/sleeves/free_opt_tail.py) over the strategy in desk3/strategies/free_opt_tail.py, with an added adapter-level minimum-days-to-expiry filter.

## Full algorithm
Shared quote law (all three free_opt strategies, desk3/strategies/<id>.py): a quote is fresh only when its source stamp and receipt stamp are both present, neither is more than 2 s in the future, source age <= 90 s, receipt age <= 30 s, receipt is not earlier than source, and ask >= bid > 0. Exits are evaluated before entries in signal(). Entries are deduped per session: if any served sleeve_state record has last_exit_date == this session, or a held position whose entry_date is this session, no new entry that session. The virtual ledger account is "free_options" with BUDGET_USD = 100,000 (the shared free-options pool); the roster slice is $10,000. SleeveConfig in the strategy: cadence_s=300, universe=(), state_schema={"position": "dict|None"}, risk_pct=None. Each strategy also has an ENH switch in context.extra["<id>_enhance"]["enabled"], default ON; OFF restores the pre-change rule exactly, and the pre-change rule is recorded as a shadow paired record on last_evaluation and never emits intents. After the strategy returns, the v3 adapter applies its own ENH2 filter (extra["<id>_enh2"]["enabled"], default ON) named per sleeve below; exits are never filtered by ENH2.
This sleeve's rules (desk3/strategies/free_opt_tail.py, class FreeOptTail):
Entry, in code order: (1) compute exits first. (2) If already entered this session, return exits only. (3) Require a fresh indicative quote in extra["quote"] under the shared quote law. (4) Require extra["underlying_return"] present, finite, and <= -0.03 (a NaN return does not pass). (5) Require the quote symbol to contain the letter "P", a finite ask (ap) > 0. (6) ENH zero-life gate (default ON): parse the OCC expiry from the quote symbol; refuse when the expiry is unparseable or expiry <= this session (the adapter separately refuses < 5 days, below). (7) Emit one enter intent: the quote symbol, qty_hint=1, price_hint = round(ask, 2), exit_rules=(ExitRule("time_bars", 5),), reason naming the return, the free_options account and the $100,000 pool budget. The existing card describes the producer's contract selection (not performed in this strategy file): the put with |delta| 0.50-0.65, 21-35 DTE, expiring 7+ days past the 5-session exit, nearest expiry then delta nearest 0.575, 1 contract at the ask, once per session.
Adapter ENH2 filter (desk3/enh2_edge16.py filter_min_days_to_expiry with min_days=5, using view["now"]'s date as the session): refuse entry intents whose OCC expiry is unparseable or less than 5 days after the session date.
Exits (_exit_intents), per held contract in symbol order: require a two-sided quote in extra["quotes"] unless the session is on/after the contract's OCC expiry. Exit is due, in this precedence, when sessions held (extra["session_dates"] strictly after entry_date) >= 5 (five_sessions), else when the quote bid <= 0.5 x the position's entry_px (premium_loss_50pct), else when the session is on/after expiry (expiry). A long position sells to close at the bid, a short buys to close at the ask, at the full held qty.

## Files in this repo
- Sleeve module (desk desk3/sleeves/free_opt_tail.py): `desk3/sleeves/free_opt_tail.py`.
- Strategy (desk desk3/strategies/free_opt_tail.py): `sleeves/free_opt_tail.py`.
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
2. Register the roster row for `free_opt_tail` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the shared quote law and the return gate: underlying_return of -0.029, a missing return, and a NaN return each produce no entry; -0.03 exactly enters.
- Check the quote symbol must contain "P" and have a finite ask > 0.
- Check the ENH gate: a put expiring on or before the session produces no entry with the switch ON and an entry with it OFF; check the adapter ENH2 filter separately refuses an entry expiring 4 days after the session and passes one expiring 5 or more days after.
- Check dedupe per session as in the shared law.
- Check exit precedence: 5 sessions held beats the 50% premium-loss rule, which beats expiry; before expiry a one-sided quote blocks the exit, at/past expiry it does not.
