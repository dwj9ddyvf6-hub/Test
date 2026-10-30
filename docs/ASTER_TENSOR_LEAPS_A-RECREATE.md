# aster_tensor_leaps_a: Recreation package

Provenance: Ausar R17/R18 options research (Source row in strategies/ausar/opt-tensor-leaps.md in this repo).

## What this sleeve is
This sleeve expresses a qualified weekly Tensor G4 event as a single long-dated call on the event's symbol, bought on the event's own entry session. This book is A with risk fraction 0.02 of the slice. It is a thin wrapper delegating to desk3/aster_batch3.py with its own SPECS entry, and it lands visibly UNFED because no v3 producer emits OPRA chains or G4 events yet.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch3.py, book OPT_TENSOR_LEAPS_A): signal=None, structure="long", exit_rule=None, risk_fraction=0.02, max_debit_width=None, max_premium_spot=0.5, dte=(540, 720), delta=(0.6, 0.8), hold_calendar_days=365. Engine constant SLICE_USD=10000.0.

Evaluation order in desk3/aster_batch3.py::evaluate(sleeve_id, view, ctx):
1. Exits first (_exit_intents), over every held position that carries option legs, qty > 0. For each position, due and reason are decided in this order (later rules override earlier ones where the code assigns them):
   a. European legs (first leg exercise_style == "european"): due only at settlement, when the calendar session >= expiry and now >= that expiry's option close, action "settle", reason official_PM_expiry.
   b. Otherwise the planned exit: due when the session stored in position metadata exit_session is due under _session_exit_due with 5 minutes before that session's close (any time after that date also counts), reason planned_session_exit.
   c. Pre-expiry guard: the guard session is the calendar's previous session before the first leg's expiry (or metadata expiry_exit_session); if that guard session is due under _session_exit_due with 15 minutes before close, due with reason pre_expiry_obligation_exit.
   d. Assignment alert: if view extra exercise_checks / assignment_alerts for the leg underlying carries assignment_alert true, verified true, a source_sha256, and received_at <= now, due with reason assignment_risk_exit_or_lifecycle_obligation.
   e. Original G4 deadline: if metadata original_G4_exit_at is present and now >= it, due with reason original_G4_saved_deadline_exit.
   f. G4 exit events: only if not already due, a view extra tensor_G4_exit_events entry with event_id == metadata G4_event_id, qualified_native_G4 true, exit_due true, a source_sha256, and available_at <= now makes it due with reason original_G4_state_or_time_exit. (The touch rule does not apply to this book: exit_rule is None.)
   A due non-settle exit is priced from current OPRA quotes for every leg (fresh <= 10 seconds, feed "opra", leg timestamps within 2 seconds of each other, displayed depth at least the position qty on the closing side); the closing package price is bid for the long leg times 100. An unpriceable due exit emits no intent in this engine. Exit intent: market, day, sell_to_close, whole qty, legs carried, exit_action "close" or "settle". The mid-limit enhancement in this engine is scoped to the recovery family and does NOT apply to this sleeve.
2. If any exit was produced, return only exits. If any position carries legs, return no entry (one package per book).
3. Entry gates: view extra market_open must be exactly True (default True when absent), and the ET time must satisfy 09:35 <= time < 09:40.
4. G4 event scan (view extra["tensor_G4_events"], in list order; the first event that qualifies and prices is entered): refuse an event when signal_end is missing, when no installed_at is available (view extra or ctx), when signal_end < installed_at, when qualified_native_G4 is not True, when source_sha256 is missing, when entry_session != the current session, when not (signal_end <= available_at < now), or when original_G4_exit_at is missing or <= now.
5. Contract selection (_select_contracts for calls on the event symbol): spot is the midpoint of the underlying quote in view["quotes"], which must be fresh (<= 5 seconds, feed "sip") and identity-checked. Candidates are chain calls (view["options_chain"][symbol]) with 540 <= DTE <= 720 and 0.6 <= abs(delta) <= 0.8, whose greeks stamps satisfy greeks_market_at <= greeks_received_at <= now and now - greeks_market_at <= 10 seconds. Choose the minimum by (expiry, abs(abs(delta) - 0.7), abs(strike - spot), symbol). Structure is long, so there is one leg with ratio 1 and no wing.
6. LEAPS spread gate (ENH-B13-LEAPS-SPREAD-20261024, switch spread_gate under extra/ctx key aster_leaps_enh, default ON): refuse when (ask - bid) / mid > 0.30 on the long leg, using its OPRA quote (fresh <= 10 seconds as in step 1, timestamps within 2 seconds across legs). OFF restores the ask-only rule.
7. Premium cap and sizing (_entry_intent): debit per package = long leg ask * 100. Refuse if debit / (spot * 100) > 0.5. Fees come from the snapshot fee schedule (view extra option_fees or view options fees, per_contract_per_fill * number of legs); absent a schedule, the fallback fee total is debit * 0.0015 per package. Per-package cost = debit + fees. Risk budget = min(equity * 0.02, equity * 0.05 - outstanding, cash), where equity is slice capital_usd or 10000.0, cash is slice cash_usd or equity, and outstanding is the sum over held positions of metadata max_loss_per_package * qty. qty = int(risk budget // per-package cost), then capped by the long leg's ask_size; refuse if qty < 1 either way. Risk fraction 0.02 of the $10,000 slice is $200 before the other two caps.
8. Exit session stored on entry (_exit_session): the first calendar future_session >= entry session + 365 calendar days; the calendar's future_sessions must be sorted, unique, and start with the entry session, otherwise the entry raises and is skipped. Entry intent: market, day, buy_to_open, symbol "PKG:" plus a hash of book, signal id and leg symbols, price_hint = debit, legs and metadata carrying rule_id OPT_TENSOR_LEAPS_A, risk_budget, entry_spot, entry_session, exit_session, expiry_exit_session, the G4 source sha256, event id, signal_end and original_G4_exit_at.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_tensor_leaps_a.py` (also `sleeves/aster_tensor_leaps_a.py` and `integration/aster_tensor_leaps_a_adapter.py`).
- Shared engine: `desk3/aster_batch3.py` (this sleeve's SPECS entry, _select_contracts, _entry_intent, _exit_intents and evaluate).
- Contract type: desk3/contract.py, whose repo copy is at `engines/desk3/contract.py` in engines_map.json with status gate_blocked, so that copy was not vendored by the engines pass; the desk original must be supplied from desk3/contract.py to run.
- Existing family card: `strategies/ausar/opt-tensor-leaps.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: the symbol of a qualified native G4 event (R19 G4 signals, per the existing card). Asset: equity options (long calls). Timeframe: weekly G4 events; contracts at 540-720 DTE.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; risk fraction 0.02 with the caps in the Full algorithm section; bp_buffer_frac=0.02.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and the engine INPUTS tuple: bars, options_chain, quotes, positions. Producers in the engine PRODUCERS tuple: bars -> bars (freshness_sla_s 3600), options_chain -> options_chain and options_quotes (900), quotes -> quotes (60), broker_readback -> positions (900), tensor_bundle -> tensor (93600).
- tensor_G4_events: view extra["tensor_G4_events"] entries with event_id, symbol, signal_end, available_at, entry_session, qualified_native_G4, source_sha256, original_G4_exit_at and original_G4_exit_session; installed_at comes from view extra or ctx. The engine header states no v3 producer emits OPRA chains or G4 events yet, so this sleeve is UNFED, never fake-fed.
- options_chain: view["options_chain"] keyed by underlying symbol, rows with right, expiry, strike, delta, greeks_market_at and greeks_received_at; option quotes in view["options_quotes"] keyed by OCC symbol with bid, ask, bid_size, ask_size, market_at, received_at and feed.
- quotes: view["quotes"][symbol] underlying quote with bid and ask (fresh, feed sip) for spot.
- bars: view["bars"] keyed by symbol or `<symbol>|1Day` / `1d` / `1D` (declared input; the LEAPS path itself prices from quotes and the chain).
- calendar: view["calendar"] with session, future_sessions, option_close_by_date and previous_session_by_date.
- positions: view["positions"] rows with symbol, qty, legs and metadata (exit_session, expiry_exit_session, entry_spot, G4_event_id, original_G4_exit_at, max_loss_per_package).

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_tensor_leaps_a.py` with SLEEVE_ID = "aster_tensor_leaps_a" (the repo also carries `sleeves/aster_tensor_leaps_a.py` and `integration/aster_tensor_leaps_a_adapter.py` copies).
2. Register the roster row for `aster_tensor_leaps_a` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_tensor_leaps_a, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch3.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check each G4 event gate on fixtures: pre-install signal_end, qualified_native_G4 not True, missing source_sha256, entry_session other than today, available_at not strictly before now, and a missing or past original_G4_exit_at each produce no entry.
- Check the entry window is 09:35 to 09:40 ET, market_open must be exactly True, and any held legged package blocks entries.
- Check contract selection picks the minimum by (expiry, distance of abs(delta) from 0.7, distance of strike from spot, symbol) inside DTE 540-720 and delta 0.6-0.8, with greeks older than 10 seconds rejected.
- Check the premium cap at max_premium_spot=0.5 and this book's sizing with risk_fraction=0.02: qty equals int(min(equity * 0.02, equity * 0.05 - outstanding, cash) // (debit + fees)), capped by ask_size.
- Check the spread gate: (ask - bid) / mid above 0.30 refuses with the gate ON and is allowed (subject to the other gates) with it OFF.
- Check the stored exit_session is the first future session at or after entry + 365 calendar days, and the exit precedence in step 1, including the original G4 deadline and G4 exit events, and that an unpriceable due exit emits no intent.
