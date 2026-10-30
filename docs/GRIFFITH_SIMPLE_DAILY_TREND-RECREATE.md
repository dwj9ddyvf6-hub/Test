# griffith-simple-daily-trend - Recreation Package

## Provenance

- Canonical ID: `griffith-simple-daily-trend`
- Canonical name: Simple daily trend cohorts
- Aliases: griffith_simple_daily_trend
- Type: trend following ; Family: griffith ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Simple daily trend cohorts" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Simple daily trend cohorts" (also docs/ALL-SLEEVES.md); Test catalog entry 'griffith-simple-daily-trend' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Existing Test doc: `strategies/griffith/griffith-simple-daily-trend.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: [] ; exit: [] ; filters: [] ; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']

## What this strategy is

Simple daily trend cohorts. Universe in accounting: SCOPE universe: 550 US names. Asset class in accounting: US equities. Timeframe in accounting: 1d (20-session cohorts). Creator in accounting: Griffith R4 strategy tournament (SIMPLE_TREND_1_0_0).

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

# Simple daily trend cohorts

Each session, every SCOPE name closing above its 200-day average with the 50-day above the 200-day opens a 20-session cohort in a fixed slot.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 strategy tournament (SIMPLE_TREND_1_0_0) |
| **Asset** | US equities |
| **Timeframe** | 1d (20-session cohorts) |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | Trend |
| **Status** | blocked |

## Entry

- Observation: each session, every name with close > SMA 200 and SMA 50 > SMA 200 on its last completed bar (253 bars needed).
- Entry: at the session's first pass with a live quote, a fixed slot of $100,000 / 550 (about $182) as a marketable limit good for an hour; one cohort per name, none while it is held or working.

## Exit

- Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1).

## Sizing

- A fixed $182 slot per cohort.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/strategy_tournament.py`, `sleeves/griffith/feedlib/griffith.py`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)


Accounting gaps (not in the record): entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/GRIFFITH_SIMPLE_DAILY_TREND-RECREATE.md`
- Algorithm doc / strategy card: `strategies/griffith/griffith-simple-daily-trend.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/griffith/griffith_factor.py` (in Test)
- `sleeves/griffith/vendor/griffith/strategy_tournament.py` (in Test)
- `sleeves/griffith/feedlib/griffith.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Universe SCOPE universe: 550 US names, asset US equities, timeframe 1d (20-session cohorts), status blocked in the card. Sizing fixed slot $100,000 / 550 (about $182) per cohort.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `strategies/griffith/griffith-simple-daily-trend.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
