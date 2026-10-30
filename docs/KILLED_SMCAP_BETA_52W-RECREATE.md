# killed-smcap-beta-52w - Recreation Package

## Provenance

- Canonical ID: `killed-smcap-beta-52w`
- Canonical name: Small-cap high-beta beaten-down (52 weeks)
- Aliases: killed_smcap_beta_52w
- Type: trend following ; Family: killed ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Small-cap high-beta beaten-down (52 weeks)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Small-cap high-beta beaten-down (52 weeks)" (also docs/ALL-SLEEVES.md); Test catalog entry 'killed-smcap-beta-52w' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Existing Test doc: `strategies/killed/killed-smcap-beta-52w.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: [] ; exit: [] ; filters: [] ; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']

## What this strategy is

Small-cap high-beta beaten-down (52 weeks). Universe in accounting: The weekly M2 qualifier list. Asset class in accounting: US equities. Timeframe in accounting: 1w. Creator in accounting: The old Alpaca swing desk's killed research studies, forward-tested on the master desk.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

# Small-cap high-beta beaten-down (52 weeks)

Each week, buys the qualifiers that are beaten down, small by dollar volume and 'high beta', and holds them 52 weeks.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | The weekly M2 qualifier list |
| **Style** | Deep value (research forward test) |
| **Status** | waiting |

## Entry

- BEAT: the weekly close ≤ 80% of the 52-week high, or a 13-week return ≤ -20%.
- SMALL: the bottom third of the week's qualifiers by 52-week mean weekly dollar volume.
- HIBETA: the 52-week weekly beta > 1.2 (≥ 40 weeks).
- All three: bought at the next session's open.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Sold market-on-close on the Friday 52 weeks later (the session before, on a holiday).

## Sizing

- $10,000 per name (fractional shares).

## Data

- The desk's weekly M2 qualifier file and merged weekly bars, SPY weekly.

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/smcap.py`, `sleeves/killed/common.py`, `sleeves/killed/feedlib/killed_data.py`, `sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)

## Notes

- The beta is computed as the study computed it: the slope of SPY's weekly returns on the stock's, so volatile names score low.


Accounting gaps (not in the record): entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/KILLED_SMCAP_BETA_52W-RECREATE.md`
- Algorithm doc / strategy card: `strategies/killed/killed-smcap-beta-52w.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/killed/killed_studies.py` (in Test)
- `sleeves/killed/smcap.py` (in Test)
- `sleeves/killed/common.py` (in Test)
- `sleeves/killed/feedlib/killed_data.py` (in Test)
- `sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Universe the weekly M2 qualifier list, asset US equities, timeframe 1w, status waiting in the card. Sizing $10,000 per name (fractional shares).

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `strategies/killed/killed-smcap-beta-52w.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
