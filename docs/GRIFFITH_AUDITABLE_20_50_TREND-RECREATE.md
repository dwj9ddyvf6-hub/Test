# griffith-auditable-20-50-trend - Recreation Package

## Provenance

- Canonical ID: `griffith-auditable-20-50-trend`
- Canonical name: Auditable 20/50 trend (SPY)
- Aliases: griffith_auditable_20_50_trend
- Type: trend following ; Family: griffith ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Auditable 20/50 trend (SPY)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Auditable 20/50 trend (SPY)" (also docs/ALL-SLEEVES.md); Test catalog entry 'griffith-auditable-20-50-trend' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Existing Test doc: `strategies/griffith/griffith-auditable-20-50-trend.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: [] ; exit: [] ; filters: [] ; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']

## What this strategy is

Auditable 20/50 trend (SPY). Universe in accounting: SPY. Asset class in accounting: US ETF (SPY). Timeframe in accounting: 5m. Creator in accounting: Griffith / Ledge desk app, the auditable TrendAgent.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

# Auditable 20/50 trend (SPY)

Trades SPY on its 5-minute 20/50 average cross: $100 in when the 20 is above the 50, out when it drops below.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk app, the auditable TrendAgent |
| **Asset** | US ETF (SPY) |
| **Timeframe** | 5m |
| **Universe** | SPY |
| **Style** | Moving-average trend |
| **Status** | waiting |

## Entry

- Every 15 minutes on SPY's last 50 completed 5-minute bars, only on a new newest bar and never while an order works: buy when flat and SMA 20 > SMA 50 × 1.001.
- Order: round($100 / price, 6) shares as a DAY limit at the price × 1.001.

## Exit

- Sold when SMA 20 < SMA 50 while long, a DAY limit at the price × 0.999.

## Sizing

- $100 a trade.

## Data

- SPY's IEX 5-minute bars, the last 51.

## Code

- **Master desk**: `sleeves/griffith/griffith_intraday.py`; not in this repo: `desk/vendor/griffith/config.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)


Accounting gaps (not in the record): entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/GRIFFITH_AUDITABLE_20_50_TREND-RECREATE.md`
- Algorithm doc / strategy card: `strategies/griffith/griffith-auditable-20-50-trend.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/griffith/griffith_intraday.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Universe SPY, asset US ETF (SPY), timeframe 5m, status waiting in the card. Sizing $100 a trade. Code note in card: master desk file sleeves/griffith/griffith_intraday.py; a vendor config file named in the card is not in this repo: not in the record in Test, so a recreation uses the card and code parameters only.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `strategies/griffith/griffith-auditable-20-50-trend.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
