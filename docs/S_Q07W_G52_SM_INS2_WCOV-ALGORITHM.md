From the desk spec SLEEVE-CATALOG-CONSOLIDATED-2026-10-23.md.

# s_q07w_g52_sm_ins2_wcov: Algorithm

Lazarus Q07 weekly lane (Research Lab Q07 study, Alt-Data Confluence family), packaged into Test on 2026-10-29 in the audit cure. The catalog lane row and section 4.1 family rule were adapted here, and every parameter below was verified against the sleeve code (the sleeve module in sleeves/, its shared engine, and its desk config row) on 2026-10-29. Where the code and a docstring differ, the code governs and the difference is noted.

## What it trades

US stocks, long only, on the Tensor 1W (weekly) signal of the green family in the sm cap band. The sleeve is a fire-consumer: it does not generate its own signal; it consumes producer fires and applies its named alt-data filters.

## Parameters (from the sleeve code)

- Sleeve id: s_q07w_g52_sm_ins2_wcov
- Family: green
- Cap band: sm
- Horizon: 52 weeks
- Filters: ins2, wcov
- Slots: 1
- Budget: $1,000.00 total in the engine spec (per-slot budget is budget divided by slots where the engine defines budget that way). Desk config slice capital: $1,000.00.
- Parked (engine SPEC / source status): False. Desk config parked: False.
- Session: rth; cadence: 300 seconds; flat_by_close: False.
- Config inputs: sleeve_fires, bars_1day, vix, positions.

## Entry rules

See the shared-engine section below for the exact entry gate, sizing and exit mechanics implemented by the engine this sleeve delegates to. The family rule common to all Q07 lanes is: take the Tensor 1W signal of the named family in the named cap band, apply the named alt-data filters, buy only on a QQQ-down day within 5 sessions of the signal, and exit on a 15% stop or at the time horizon in the lane name (52 or 78 weeks).

## Filters for this lane

- ins2: insider buying evidence of at least 2. lazarus_q07 reading: insider_buys tag at least 2, or ins2 tag true. q07_engine and _common readings: insider_buys at least 2.
- wcov: Wikipedia coverage present. lazarus_q07 reading: wiki_cov tag true, or wiki_views greater than 0, or wiki_coverage tag true, or wiki_attention in (covered, high, spike); no evidence fails closed. q07_engine reading: wiki_views_30d greater than 0.

## Shared engine

Shared engine: desk3.q07_engine.evaluate_q07, with the per-lane SPEC dict embedded in the sleeve module itself. Inputs (module INPUTS and config row): sleeve_fires, bars_1day, vix, positions. The fire source is the sleeve_feed composer (tracker ledger plus alt-data tags) publishing sleeve_fires; in the desk snapshot the fires arrive under the sleeve_fires producer key, one fire row per sleeve. Entry gate: no position currently held (1 slot), at least 2 QQQ daily bars with the last QQQ close below the prior close (QQQ-down day), a fire whose sleeve matches this sleeve id, cap band matching the SPEC band (a stated mcap_usd must fall in the band range: mi is [0, $300M), sm is [$300M, $2B), ml is [$2B, infinity)), signal age between 0 and 5 sessions counted on QQQ bar dates, non-stale symbol bars (the stale-bars enhancement refuses entries whose last symbol bar is more than 5 sessions old, default ON), and every named filter passing. Sizing: 1 slot at $1,000 (SLOT_USD in the engine; the config slice is also $1,000); whole shares from the slot at the last close. Exit rules are evaluated first: sell when the last close is at or below avg_price times (1 - 0.15) (STOP_PCT 0.15), or when the position age in weeks reaches horizon_wk. Parked status comes from the config row, not the embedded SPEC: where the config row is parked, the desk dispatcher skips entries while the sleeve still evaluates.

## Data inputs

Config row inputs: sleeve_fires, bars_1day, vix, positions. Daily bars are used for the QQQ-down gate, filter computations that need prices, stop checks and holding-age counts, as described in the shared-engine section.

## Package

- Core: sleeves/s_q07w_g52_sm_ins2_wcov.py in this repo (the desk sleeve module).
- Adapter: integration/s_q07w_g52_sm_ins2_wcov_adapter.py in this repo (the desk adapters3 module; for this lane the adapters3 module is the sleeve module, and that adapter file was already present in this repo before this package).
- No dedicated blocker/test file and no proof/install file exist locally for this lane, so none is included.
