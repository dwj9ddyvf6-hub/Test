# killed-golden-cross-spy - Recreation Package

## Provenance

- Canonical ID: `killed-golden-cross-spy`
- Canonical name: Golden cross (SPY)
- Aliases: killed_golden_cross_spy
- Type: trend following ; Family: killed ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Golden cross (SPY)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Golden cross (SPY)" (also docs/ALL-SLEEVES.md); Test catalog entry 'killed-golden-cross-spy' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Existing Test doc: `strategies/killed/killed-golden-cross-spy.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: [] ; exit: [] ; filters: [] ; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']

## What this strategy is

Golden cross (SPY). Universe in accounting: SPY. Asset class in accounting: US ETF. Timeframe in accounting: 1d. Creator in accounting: QuantifiedStrat's golden cross, a killed study of the old Alpaca swing desk, forward-tested.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

# Golden cross (SPY)

Holds SPY while its 50-day average is above the 200-day, and goes flat when it is below.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | QuantifiedStrat's golden cross, a killed study of the old Alpaca swing desk, forward-tested |
| **Asset** | US ETF |
| **Timeframe** | 1d |
| **Universe** | SPY |
| **Style** | Trend (moving-average cross) |
| **Status** | live |

## Entry

- Long when SPY's 50-day SMA is above its 200-day SMA on the last completed session (a tie keeps the state); bought at the next session's first pass.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Flat when the 50-day is below the 200-day: sold at the next pass.

## Sizing

- All of the sleeve's equity; a $100,000 book.

## Data

- SPY split-adjusted daily bars (320).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)


Accounting gaps (not in the record): entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/KILLED_GOLDEN_CROSS_SPY-RECREATE.md`
- Algorithm doc / strategy card: `strategies/killed/killed-golden-cross-spy.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/killed/killed_studies.py` (in Test)
- `sleeves/killed/daily.py` (in Test)
- `sleeves/killed/common.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Universe SPY, asset US ETF, timeframe 1d, status live in the card. Sizing all of the sleeve equity; a $100,000 book.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `strategies/killed/killed-golden-cross-spy.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
