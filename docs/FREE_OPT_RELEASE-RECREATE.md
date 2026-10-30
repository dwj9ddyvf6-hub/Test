# free_opt_release: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-release.md in this repo: Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean.

## What this sleeve is
This sleeve buys a 2-leg SPY straddle (one call and one put) only on a session with a verified public release event, and exits the session after the event or at expiry. In v3 it is a thin adapter (desk3/sleeves/free_opt_release.py) over the strategy in desk3/strategies/free_opt_release.py, with an added adapter-level expiry-coherence filter.

## Full algorithm
Shared quote law (all three free_opt strategies, desk3/strategies/<id>.py): a quote is fresh only when its source stamp and receipt stamp are both present, neither is more than 2 s in the future, source age <= 90 s, receipt age <= 30 s, receipt is not earlier than source, and ask >= bid > 0. Exits are evaluated before entries in signal(). Entries are deduped per session: if any served sleeve_state record has last_exit_date == this session, or a held position whose entry_date is this session, no new entry that session. The virtual ledger account is "free_options" with BUDGET_USD = 100,000 (the shared free-options pool); the roster slice is $10,000. SleeveConfig in the strategy: cadence_s=300, universe=(), state_schema={"position": "dict|None"}, risk_pct=None. Each strategy also has an ENH switch in context.extra["<id>_enhance"]["enabled"], default ON; OFF restores the pre-change rule exactly, and the pre-change rule is recorded as a shadow paired record on last_evaluation and never emits intents. After the strategy returns, the v3 adapter applies its own ENH2 filter (extra["<id>_enh2"]["enabled"], default ON) named per sleeve below; exits are never filtered by ENH2.
This sleeve's rules (desk3/strategies/free_opt_release.py, class FreeOptRelease):
Entry, in code order: (1) compute exits first (below). (2) If already entered this session, return exits only. (3) Require a fresh indicative quote in extra["quote"] under the shared quote law. (4) Require a verified event for this session: some record in extra["events"] with session == context.session and verified true (the existing card names the event sources the producer loads: CPI and the Employment Situation from FRED's release calendar and the FOMC statement from the Fed's calendar, for today's session). (5) Require the producer-supplied package in extra["package"]["legs"] to have exactly 2 legs whose rights are exactly {call, put}, every leg has a symbol, and every leg has a finite ask > 0 (ask or ap field). (6) ENH integrity gate (default ON): refuse when the legs' source stamps are more than 30 s apart (SKEW_MAX_SECONDS), when a leg source stamp is missing/malformed for a multi-leg package, or when any leg's source stamp is older than 90 s or more than 2 s in the future. (7) Emit one enter intent per leg: qty_hint=1, price_hint = round(leg ask, 2), reason naming FREE_OPT_RELEASE_V1, the leg right, buy_to_open and the event session. The existing card describes the producer's package selection (not performed in this strategy file): an ATM SPY straddle on the nearest expiry after the session that follows the event, within 45 days, 1 straddle, max loss / risk cap = the natural debit, sent only while the market is open.
Adapter ENH2 filter (desk3/enh2_edge16.py filter_package_expiry_coherence): refuse the whole entry package when its legs' OCC expiries differ or any expiry is unparseable.
Exits (_exit_intents): group held positions by entry_date. For each group, sessions held = the count of extra["session_dates"] strictly after entry_date. Exit is due when sessions held >= 1, or when the session is on/after the earliest leg OCC expiry. Before expiry, every leg must have a two-sided quote in extra["quotes"] (ask > 0, bid >= 0, ask >= bid) or the group does not exit; at/past expiry that quote gate is bypassed. Each leg exits at its full held qty: a long leg sells to close at the bid, a short leg buys to close at the ask, reason session_after_event or expiry.

## Files in this repo
- Sleeve module (desk desk3/sleeves/free_opt_release.py): `desk3/sleeves/free_opt_release.py`.
- Strategy (desk desk3/strategies/free_opt_release.py): `sleeves/free_opt_release.py`.
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
2. Register the roster row for `free_opt_release` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the shared quote law: a quote 91 s old at source, 31 s old at receipt, more than 2 s in the future, crossed, or with bid <= 0 each produce no entry.
- Check entry requires a verified event dated this session, exactly 2 package legs with rights {call, put}, and a positive finite ask on each leg; any failure produces no entry.
- Check the ENH integrity gate: legs whose source stamps differ by more than 30 s, or a leg stamp older than 90 s, produce no entry with the switch ON and an entry with extra["free_opt_release_enhance"]["enabled"]=false.
- Check the adapter ENH2 filter: a package whose two legs expire on different dates produces no entry intents, while exits pass unfiltered.
- Check dedupe: a served record with entry_date or last_exit_date equal to this session blocks a new entry.
- Check exits: with session_dates one session after entry_date the whole package exits together; before expiry a missing or one-sided leg quote blocks the exit, and at/past expiry the exit fires without that gate.
