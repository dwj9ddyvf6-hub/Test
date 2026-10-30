# aster_core_rsi2_long: Recreation Package

## Provenance

Provenance: Ausar R17/R18 options research (core_reserve family) (Source row in `strategies/ausar/opt-qqq95-rsi2.md`).

## What this sleeve is

This sleeve holds a 95% QQQ equity core and spends the reserve on short-dated call options after an RSI(2) dip, using the long structure (book OPT_QQQ95_RSI2_LONG). It is a thin wrapper in `adapters3/aster_core_rsi2_long.py` that delegates to the shared engine `desk3/aster_b2.py`. The QQQ core leg, once bought, has no exit rule in the source engine and is never exited by this sleeve.

## Full algorithm

Evaluation order in `desk3/aster_b2.py` evaluate(), as applied to SPECS['aster_core_rsi2_long'] = book OPT_QQQ95_RSI2_LONG, family 'core_reserve', signal 'RSI2', structure 'long', risk 0.005, dte (14, 21), delta (0.5, 0.6), hold 5 sessions, max_debit_width 0.45, max_premium_spot 0.015, exit_rule 'touch', core True:

1. Exits first, for held positions that carry option legs. In order: (a) pre-expiry guard: exit if the first leg expiry is 1 day or less from the current session; (b) planned session exit: exit if sessions held is at or above 5 (sessions held is taken from the position, or counted from daily bars after the entry date); (c) touch exit (exit_rule 'touch'): exit if the underlying last daily close is at or above entry_spot x 1.02. An exit is a full sell_to_close package reversing the legs. A position with no legs (the QQQ equity core) is skipped: there is no exit rule for it.
2. If any exit was emitted, return it. If any held position carries legs, emit nothing else: one options package per book.
3. Entry window: entries only inside 09:35-09:40 as read from the evaluation timestamp (a date-only timestamp passes the window check in the code).
4. Core leg first: if no QQQ equity position (symbol QQQ with no legs) is held, buy the core once and return only that intent: quantity = int(10000 x 0.95 / (spot x 1.0015)), where spot is the last QQQ daily close; market, day, buy_to_open. No options entry is evaluated on that call.
5. RSI2 signal: for symbols in the order IWM, QQQ, SPY: require at least 200 daily bars; compute SMA200 as the mean of the last 200 closes and RSI(2) with the engine's smoothing (initial gain/loss averaged over the first 2 changes, then each step gain = (prior gain + current gain) / 2, likewise loss; RSI = 100 - 100 / (1 + gain/loss)). Qualify only if the last close is above SMA200 and RSI(2) is below 10. The first qualifying symbol is attempted; if its contract entry fails, no intent is emitted.
6. Contract selection (right 'call'): contracts for that underlying with DTE between 14 and 21 inclusive and absolute delta between 0.5 and 0.6 inclusive. The long leg minimises (expiry, |delta - 0.55|, |strike - spot|, symbol). Long structure: a single long call leg with ratio 1; there is no wing leg.
7. Debit and gates: Long premium check: reject if debit / spot is above 0.015 (the code tests (debit x 100) / (spot x 100) against max_premium_spot 0.015), where debit is the long leg ask. Reject a debit at or below 0. Core spread gate (enhancement, on by default): refuse if the long leg ask minus bid is above 25% of its ask.
8. Sizing: risk budget = 0.005 x $10,000 slice = $50. Per-contract cash cost = debit per share x 100 + $0.65 per contract per leg (fee per contract). Quantity = floor(risk budget / per-contract cost), capped by the displayed size (ask_size for a long leg, bid_size for a short leg, minimum across legs); quantity below 1 emits nothing.
9. Entry intent: buy_to_open package, day, with legs, entry_spot, exit_rule 'touch' and hold_sessions 5. Mid-limit enhancement (on by default): if every leg has a usable mid (bid above 0 and ask at or above bid) and the package mid is above 0, the order becomes a limit order at round(package mid, 2) instead of a market order.

## Files in this repo

- Sleeve module / adapter (same wrapper content in the repo):
- `adapters3/aster_core_rsi2_long.py`
- `sleeves/aster_core_rsi2_long.py`
- `integration/aster_core_rsi2_long_adapter.py`
- Shared engine: `desk3/aster_b2.py` (desk path `desk3/aster_b2.py`)
- Config: `config/sleeves.json` and `engines/config/sleeves.json` (row id `aster_core_rsi2_long`)
- Existing family doc: see the Provenance source doc path named in the audit record for this sleeve.

## Configuration

- Universe: QQQ equity core; options underlyings IWM, QQQ, SPY. Timeframe: daily bars, 09:35-09:40 entry window.
- Module: `adapters3.aster_core_rsi2_long`; cadence_s 300; session 'rth'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}.
- Inputs declared in config: bars, options, positions. Parked: false.
- Book parameters: OPT_QQQ95_RSI2_LONG, structure long, risk 0.005, DTE 14-21, delta 0.5-0.6, hold 5, max_debit_width 0.45, max_premium_spot 0.015, exit_rule touch, core True.

## Data inputs

Declared inputs: bars, options, positions (engine INPUTS_COMMON). Producers named in the engine: bars (freshness_sla_s 900), options_chain (900, outputs options), broker_readback (900, outputs positions). The engine header states inputs not produced by v3 producers (options chain, earnings_events) leave the sleeves unfed in the registry, never fake-fed; this sleeve does not use earnings_events (its adapter selects the non-PEAD producer set).

## Install and run

1. Place the files listed in 'Files in this repo' at their repo paths in a fresh desk tree, keeping `desk3/`, `adapters3/`, `sleeves/` and `integration/` side by side so the wrapper imports resolve exactly as in the repo.
2. Register the config row for `aster_core_rsi2_long` from `config/sleeves.json` (also vendored as `engines/config/sleeves.json`) with the exact values in the Configuration section; do not change cadence, slice or parked state.
3. Wire the producers named in 'Data inputs' so the declared inputs are present in the evaluation `view` at the stated freshness; a missing input must leave the sleeve unfed, never fake-fed.
4. Specific entry point: `from adapters3.aster_core_rsi2_long import evaluate; intents = evaluate(view, ctx)`, where `view` carries daily `bars`, the `options` contract list or per-underlying chain dict, and `positions`.
5. First evaluation: call the wrapper entry point `evaluate(view, ctx)` for this sleeve (see the specific call in the preceding step), confirm no intent is emitted outside the stated window / gates, then let the desk dispatcher call it on its cadence and route returned intents to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- With no QQQ core held and the entry window open, the only intent is the QQQ core buy at int(9500 / (spot x 1.0015)) shares; the core is never exited on any later evaluation.
- With the core held, a symbol with at least 200 bars, close above SMA200 and RSI(2) below 10 produces one long package only when a contract passes DTE 14-21, delta 0.5-0.6, the debit gate and the spread gate; quantity equals floor(50 / per-contract cost) capped by displayed size.
- A held package exits on the first of: expiry 1 day or less away, 5 sessions held, or underlying close at or above entry_spot x 1.02.
- Outside 09:35-09:40, or with RSI(2) at or above 10, or close at or below SMA200, no entry is emitted.
- The wrapper delegates to the named shared engine with the exact sleeve id, and no rule, threshold or sizing value differs from the values stated above.
- A missing or stale declared input emits no entry intent.
