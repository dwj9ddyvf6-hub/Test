From the desk spec SLEEVE-CATALOG-CONSOLIDATED-2026-10-23.md.

# s_q07w_g52_sm_deep70_wcov: Algorithm

Lazarus Q07 weekly lane (Research Lab Q07 study, Alt-Data Confluence family), packaged into Test on 2026-10-29 in the audit cure. The catalog lane row and section 4.1 family rule were adapted here, and every parameter below was verified against the sleeve code (the sleeve module in sleeves/, its shared engine, and its desk config row) on 2026-10-29. Where the code and a docstring differ, the code governs and the difference is noted.

## What it trades

US stocks, long only, on the Tensor 1W (weekly) signal of the green family in the small cap band. The sleeve is a fire-consumer: it does not generate its own signal; it consumes producer fires and applies its named alt-data filters.

## Parameters (from the sleeve code)

- Sleeve id: s_q07w_g52_sm_deep70_wcov
- Family: green
- Cap band: small
- Horizon: 52 weeks
- Filters: deep70, wcov
- Slots: 1
- Budget: $1,000.00 total in the engine spec (per-slot budget is budget divided by slots where the engine defines budget that way). Desk config slice capital: $1,000.00.
- Parked (engine SPEC / source status): False. Desk config parked: False.
- Session: rth; cadence: 86400 seconds; flat_by_close: False.
- Config inputs: fires, bars, positions.

## Entry rules

See the shared-engine section below for the exact entry gate, sizing and exit mechanics implemented by the engine this sleeve delegates to. The family rule common to all Q07 lanes is: take the Tensor 1W signal of the named family in the named cap band, apply the named alt-data filters, buy only on a QQQ-down day within 5 sessions of the signal, and exit on a 15% stop or at the time horizon in the lane name (52 or 78 weeks).

## Filters for this lane

- deep70: explicit deep70 tag true; else drawdown_from_high tag at least 0.30; else price at or below 70% of the high_52w tag; else (lazarus_q07 engine) price at or below 70% of the maximum close in the available bars. In the q07_engine variant: close at or below 70% of the trailing 252-session high, with at least 20 bars required.
- wcov: Wikipedia coverage present. lazarus_q07 reading: wiki_cov tag true, or wiki_views greater than 0, or wiki_coverage tag true, or wiki_attention in (covered, high, spike); no evidence fails closed. q07_engine reading: wiki_views_30d greater than 0.

## Shared engine

Shared engine: desk3.lazarus_q07.evaluate_sleeve, with the per-lane row in that module's SPECS table. Inputs (module INPUTS and config row): fires, bars, positions. Producers: sleeve_feed_composer (fires, freshness SLA 604800s), bars (3600s), broker_readback (positions, 3600s). Entry gate: a fire for this sleeve's family and band, the symbol not already held, signal age at most 5 sessions (WINDOW_SESSIONS), QQQ down on the day (an explicit qqq_red flag in view extra/market overrides the QQQ close comparison), and every named filter passing with positive evidence; a filter with no evidence fails closed, and an unknown filter fails closed. Filters are revalidated at the latest bar price by default (the exec_price enhancement switch; OFF restores the fire-price rule), and candidates are ordered freshest-signal-first by default (the fresh_first enhancement switch). Sizing: whole shares, qty = floor((budget / slots) / price), budget and slots from the SPECS row below. Orders are market, day, buy_to_open. Exit rules are evaluated first and are never gated by parked status: sell the full held quantity when the last price is at or below entry times (1 - 0.15) (the 15% stop, STOP_FRAC), or when the holding age in calendar days reaches horizon_w times 7 (the time horizon). Parked rows: when the SPECS parked flag is true, entries are refused and only exits are managed (the module comment calls this CSV off).

## Data inputs

Config row inputs: fires, bars, positions. Daily bars are used for the QQQ-down gate, filter computations that need prices, stop checks and holding-age counts, as described in the shared-engine section.

## Package

- Core: sleeves/s_q07w_g52_sm_deep70_wcov.py in this repo (the desk sleeve module).
- Adapter: integration/s_q07w_g52_sm_deep70_wcov_adapter.py in this repo (the desk adapters3 module; for this lane the adapters3 module is the sleeve module, and that adapter file was already present in this repo before this package).
- No dedicated blocker/test file and no proof/install file exist locally for this lane, so none is included.
