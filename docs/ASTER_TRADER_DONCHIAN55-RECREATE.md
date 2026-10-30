# aster_trader_donchian55: Recreation package

Provenance: trader.dev public strategy; StockCharts price channels (Source row in strategies/ausar/public-donchian55.md in this repo).

## What this sleeve is
This is a daily Donchian 55/20 trend-following sleeve over a fixed 15-ETF universe: it buys a close above the prior 55-day high while above the 200-day SMA, with an initial 2xATR14 stop, and exits on a close below the prior 20-day low or below the 200-day SMA, the recorded stop, or 126 holding bars. It is a thin wrapper: adapters3/aster_trader_donchian55.py delegates to desk3/aster_batch16.py evaluate with kind=donchian. Sources: desk adapters3/aster_trader_donchian55.py, desk3/aster_batch16.py (SPECS entry, DONCHIAN_INPUTS, PRODUCERS, SLICE=10000.0), and docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md in this repo.

## Full algorithm
Spec and constants (desk3/aster_batch16.py): kind=donchian, inputs=(bars, positions), cadence_s=86400, session=rth, slice $10,000. Universe: SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX. Minimum bars 252; entry channel 55; exit channel 20; SMA 200; maximum hold 126 bars; slots 10; notional fraction 0.10 of equity; dollar-volume fraction 0.01 of the 20-day average dollar volume; risk fraction 0.005 of equity; stop = 2.0 x ATR14 (Wilder RMA).
1. Exits first; if any exit is emitted the evaluation returns with no entry.
2. Exit rules per held position, in the engine's evaluation order as documented in this repo's ALGORITHM doc: (a) initial stop: the last close at or below the position's recorded stop_price (the entry 2xATR14 stop, read from the position or its meta) sells the position in full; (b) timeout: a position held at least 126 completed holding bars is sold in full, reason 126_completed_holding_bars; (c) signal exits (with at least 252 bars): a last close below the prior 20-day low and/or below the 200-day SMA sells the position in full, with the triggered conditions named in the reason. Exits are market, day, sell_to_close intents, in full.
3. Entry candidates: a symbol needs at least 252 daily bars, a positive ATR14 and a positive 20-day average dollar volume.
4. Entry condition: the last close is above the prior 55-day high (the maximum high of the 55 bars before the last bar) AND the last close is above the 200-day SMA.
5. Ranking: candidates rank by (close - prior55_high) / ATR14 descending, symbol ascending on ties; at most 10 slots.
6. Sizing: cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash); shares = int(cap // price), then capped by the risk size int((equity x 0.005) // (2.0 x ATR14)); fewer than 1 share emits nothing.
7. Entry intent: market, day, buy_to_open, with stop_price = round(price - 2.0 x ATR14, 4) recorded on the intent.

## Files in this repo
- v3 adapter: adapters3/aster_trader_donchian55.py (SLEEVE_ID=aster_trader_donchian55; evaluate delegates to desk3/aster_batch16.evaluate with DONCHIAN_INPUTS and PRODUCERS imported from that engine).
- Adapter mirror: integration/aster_trader_donchian55_adapter.py in this repo.
- Shared engine file: desk3/aster_batch16.py (SPECS entry for this sleeve, the donchian evaluate path, producers). The audit record also lists desk3/aster_batch15.py among this sleeve's engine files (the batch-15 engine the batch-16 programme shares its timing and helper layer with); both are in this repo at those paths.
- Existing docs: strategies/ausar/public-donchian55.md and docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=aster_trader_donchian55), also at config/sleeves.json.

## Configuration
Module adapters3.aster_trader_donchian55; cadence_s 86400; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, positions]; parked false. Universe: the fixed 15-ETF list above; timeframe daily bars. Source: muse-desk-v3/config/sleeves.json row id=aster_trader_donchian55.

## Data inputs
Inputs are bars and positions. Producers named in desk3/aster_batch16.py PRODUCERS: bars (freshness_sla_s 900) and broker_readback (freshness_sla_s 900, outputs positions). Bars are daily bars per ETF (at least 252 for any candidate or signal exit, with high, low, close and volume for ATR14 and the 20-day average dollar volume). The existing doc's Data section names Yahoo daily bars on the master desk.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `aster_trader_donchian55` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/aster_trader_donchian55.py, whose evaluate(view, ctx) calls desk3/aster_batch16.evaluate(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with an ETF carrying 252+ daily bars whose last close is above both the prior 55-day high and the 200-day SMA: exactly one market buy_to_open entry for the top-ranked such ETF, shares = min(int(min(equity x 0.10, dollar_volume20 x 0.01, cash) // price), int((equity x 0.005) // (2.0 x ATR14))), stop_price round(price - 2.0 x ATR14, 4).
- Fixture with the last close above the 55-day high but at or below the 200-day SMA: no entry.
- Fixture with a held position whose last close is at or below its recorded stop_price: a full sell_to_close exit and no entry in the same call; a position held 126 completed bars exits with reason 126_completed_holding_bars.
- Fixture with a held position whose last close is below the prior 20-day low: a full signal exit naming that condition.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
