# OPT_QQQ95_RSI2_VERTICAL: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Core exposure plus option reserve - RSI2, vertical, 0.5% risk", type options directional, family core_reserve. Algorithm grade FULL in the accounting. Aliases: `OPT_QQQ95_RSI2_VERTICAL` (md2_ausar_map "present in roster"; ausar_deployed "mode=independent_local_paper running=False"; femto land-wt "present in roster"), `ausar_pb21` (md2_catalog "replaced", ausar_map "present in roster"; merge tier A: the ausar_map row for ausar_pb21 lists the r19 link OPT_QQQ95_RSI2_VERTICAL), and `ausar_r19_OPT_QQQ95_RSI2_VERTICAL` (md2_catalog "blocked"; merge tier C on the identical normalised form and core_reserve family overlap).
- Accounting parameters for this book: structure vertical, universe / symbols IWM, QQQ, SPY, DTE [14, 21], delta [0.5, 0.6], hold_sessions 5, risk_fraction 0.005, max_premium_spot 0.015.
- Accounting entry text: requires close above the 200-day simple moving average; RSI2 version: two-period RSI below 10 (the VWAP20 text in the same record belongs to the sibling VWAP20 books, not this RSI2 book). It combines a configured core allocation with a separate premium reserve for recovery option opportunities; core and premium budgets are not interchangeable. Accounting exit text (truncated in the accounting at 200 characters): close the option package when a fresh underlying bid is at least 2% above the saved entry spot price during market hours, or five minutes before the fifth market session closes, counting the entry day as session one; earlier expiry or assignment-risk obligations take precedence (completion as held in the code in this repo, named in Files).
- Test family docs: `strategies/ausar/opt-qqq95-rsi2.md` (this book's card: 95% QQQ core, 5% reserve) and `strategies/ausar/opt-recovery.md` (the recovery family spec).
- Code search: the running code was found in Test (paths in Files). Silicon, quant-research-backup and Midna trees were searched for this book id and the core_rsi2 sleeves; no matching file was found there.

## What this strategy is

A book that holds a 95% QQQ equity core and spends the reserve on short-dated call options after an RSI(2) dip, using the vertical structure (book OPT_QQQ95_RSI2_VERTICAL). In Test it runs as the thin wrapper `aster_core_rsi2_vertical` delegating to the shared engine `desk3/aster_b2.py`. The QQQ core leg, once bought, has no exit rule in the source engine and is never exited by this sleeve.

## Full algorithm

Evaluation order in `desk3/aster_b2.py` evaluate(), as applied to SPECS['aster_core_rsi2_vertical'] = book OPT_QQQ95_RSI2_VERTICAL, family 'core_reserve', signal 'RSI2', structure 'vertical', risk 0.005, dte (14, 21), delta (0.5, 0.6), hold 5 sessions, max_debit_width 0.45, max_premium_spot 0.015, exit_rule 'touch', core True:

1. Exits first, for held positions that carry option legs. In order: (a) pre-expiry guard: exit if the first leg expiry is 1 day or less from the current session; (b) planned session exit: exit if sessions held is at or above 5 (sessions held is taken from the position, or counted from daily bars after the entry date); (c) touch exit (exit_rule 'touch'): exit if the underlying last daily close is at or above entry_spot x 1.02. An exit is a full sell_to_close package reversing the legs. A position with no legs (the QQQ equity core) is skipped: there is no exit rule for it.
2. If any exit was emitted, return it. If any held position carries legs, emit nothing else: one options package per book.
3. Entry window: entries only inside 09:35-09:40 as read from the evaluation timestamp (a date-only timestamp passes the window check in the code).
4. Core leg first: if no QQQ equity position (symbol QQQ with no legs) is held, buy the core once and return only that intent: quantity = int(10000 x 0.95 / (spot x 1.0015)), where spot is the last QQQ daily close; market, day, buy_to_open. No options entry is evaluated on that call.
5. RSI2 signal: for symbols in the order IWM, QQQ, SPY: require at least 200 daily bars; compute SMA200 as the mean of the last 200 closes and RSI(2) with the engine's smoothing (initial gain/loss averaged over the first 2 changes, then each step gain = (prior gain + current gain) / 2, likewise loss; RSI = 100 - 100 / (1 + gain/loss)). Qualify only if the last close is above SMA200 and RSI(2) is below 10. The first qualifying symbol is attempted; if its contract entry fails, no intent is emitted.
6. Contract selection (right 'call'): contracts for that underlying with DTE between 14 and 21 inclusive and absolute delta between 0.5 and 0.6 inclusive. The long leg minimises (expiry, |delta - 0.55|, |strike - spot|, symbol). Vertical structure: after the long leg is selected, the wing is the same-expiry, same-right contract beyond the long strike whose strike is nearest spot x 1.02 (for calls), with ratio -1. Debit gate: debit per share = long ask minus wing bid; reject if debit / width is above 0.45, where width is the absolute strike difference; reject a debit at or below 0. Core spread gate (enhancement, on by default): refuse if the long leg ask minus bid is above 25% of its ask.
7. Sizing: risk budget = 0.005 x $10,000 slice = $50. Per-contract cash cost = debit per share x 100 + $0.65 per contract per leg (fee per contract). Quantity = floor(risk budget / per-contract cost), capped by the displayed size (ask_size for a long leg, bid_size for a short leg, minimum across legs); quantity below 1 emits nothing.
8. Entry intent: buy_to_open package, day, with legs, entry_spot, exit_rule 'touch' and hold_sessions 5. Mid-limit enhancement (on by default): if every leg has a usable mid (bid above 0 and ask at or above bid) and the package mid is above 0, the order becomes a limit order at round(package mid, 2) instead of a market order.

## Files in this repo

- This doc: `docs/OPT_QQQ95_RSI2_VERTICAL-RECREATE.md`
- Sleeve code (already in Test): `sleeves/aster/aster_core_rsi2_vertical.py`, with copies at `adapters3/aster_core_rsi2_vertical.py` and `integration/aster_core_rsi2_vertical_adapter.py`.
- Shared engine that runs the logic: `desk3/aster_b2.py` (SPECS row for aster_core_rsi2_vertical).
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_core_rsi2_vertical`.
- Family docs: `strategies/ausar/opt-qqq95-rsi2.md`, `strategies/ausar/opt-recovery.md`; rule lines `docs/verify/ausar.md`.
- An earlier recreation package for the same Test sleeve exists at `docs/ASTER_CORE_RSI2_VERTICAL-RECREATE.md`; this package is the one for the canonical book id OPT_QQQ95_RSI2_VERTICAL.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.

## Configuration

- Test sleeve id: `aster_core_rsi2_vertical`; roster module `adapters3.aster_core_rsi2_vertical`; cadence 300 seconds; session rth.
- Universe: QQQ equity core; options underlyings IWM, QQQ, SPY. Timeframe: daily bars, 09:35-09:40 entry window.
- Slice capital and cash $10,000; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; parked false.
- Inputs declared in config: bars, options, positions. Book parameters as in the Full algorithm heading.

## Data inputs

- SIP daily bars (at least 200 sessions per underlying), OPRA option quotes and greeks (family docs).
- Declared producers (engine): bars (freshness 900 s), options_chain (900 s, outputs options), broker_readback (900 s, outputs positions). Inputs not produced leave the sleeve unfed in the registry, never fake-fed.

## Install and run

1. Clone the Test repo.
2. Place `desk3/aster_b2.py` under `desk3/` and the wrapper as `sleeves/aster/aster_core_rsi2_vertical.py` (or the `adapters3/` copy), keeping the repo layout so imports resolve.
3. Register the roster row for `aster_core_rsi2_vertical` from `config/sleeves.json` with the Configuration values above.
4. Wire the view: daily `bars`, the `options` contract list or per-underlying chain dict, and `positions`, at the stated freshness.
5. Call `evaluate(view, ctx)` from the wrapper every 300 seconds in RTH; the first call with no core held buys only the core, later calls evaluate exits before entries in the order above.
6. Verify against the Verification checklist before any live use. Paper only.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- With no QQQ core held and the entry window open, the only intent is the QQQ core buy at int(9500 / (spot x 1.0015)) shares; the core is never exited on any later evaluation.
- With the core held, a symbol with at least 200 bars, close above SMA200 and RSI(2) below 10 produces one vertical package only when a contract passes DTE 14-21, delta 0.5-0.6, the debit gate and the spread gate; quantity equals floor(50 / per-contract cost) capped by displayed size.
- A held package exits on the first of: expiry 1 day or less away, 5 sessions held, or underlying close at or above entry_spot x 1.02.
- Outside 09:35-09:40, or with RSI(2) at or above 10, or close at or below SMA200, no entry is emitted; a missing or stale declared input emits no entry intent.
