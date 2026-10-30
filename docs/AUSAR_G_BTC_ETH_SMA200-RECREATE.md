# Daily SMA200 spot allocation (ausar_g_BTC_ETH_SMA200): recreation package

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): canonical name 'Daily SMA200 spot allocation', type trend following, family native_trend, algorithm grade PARTIAL, unresolved false. Test strategy card: strategies/ausar/coinbase-sma200.md. Accounting gap recorded for every SMA200 variant in this batch: sizing not recorded in any consulted source; the Test card and the Test engine below do record weights and sizing rules, and this package uses those Test sources and names the conflict where the accounting entry text differs. This canonical entry carries only the alias ausar_g_BTC_ETH_SMA200. Its accounting entry text records: 'An asset qualifies when its completed daily close is above its 200-day simple moving average. Target weights: Ether 100 percent.' Data recorded in the accounting: posted Ausar runtime inputs.

## What this strategy is

A daily crypto spot SMA200 trend allocation as recorded above. No strategy card, catalog entry, or code file carrying this exact canonical id was located in Test; see the Files section for the search record. This package is graded INCOMPLETE-CODE.

## Full algorithm

What the record holds, in evaluation order:

1. Gate (accounting entry text): an asset qualifies when its completed daily close is above its 200-day simple moving average.
2. Target weights (accounting entry text): Ether 100 percent.
3. Exit (accounting exit text): reduce an asset when its completed daily close falls below its 200-day average; for the 50 / 50 form the accounting also records: sell reductions before buying increases.
4. Everything else is not in the record for this canonical id: rebalance time, fees, lot rules, account size, and execution venue details are not in the record. Do not fill them from the related BTC_ETH_SMA200 or ETH_SMA200 books; those are separate canonical entries in the accounting.

## Files in this repo

- This doc: docs/AUSAR_G_BTC_ETH_SMA200-RECREATE.md
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'Daily SMA200 spot allocation', alias ausar_g_BTC_ETH_SMA200
- CODE NOT FOUND: no file carrying this canonical id, and no code file implementing this exact book, was located. Searched: Test recursive tree (sleeves/, strategies/, packages/, desk3/, adapters3/, integration/); Silicon recursive tree (research/ and desk trees); Midna recursive tree; quant-research-backup recursive tree (truncated by GitHub) plus its femto-lean subtree searched separately. Related family code exists in Test for the separate BTC_ETH_SMA200 and ETH_SMA200 books (desk3/aster_batch1.py, sleeves/aster_native_btc_eth_sma200.py, sleeves/aster_native_eth_sma200.py, packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/coinbase_sma200.py); it does not name this canonical id and is not claimed here as this strategy's code.
- No code was vendored for this package, because no code for this canonical id was found.

## Configuration

- SMA period: 200 (accounting). Target weights: as recorded in the Full algorithm section.
- Universe, timeframe beyond 'daily', cadence, sizing, session, and state: not in the record for this canonical id (accounting gap: sizing not recorded in any consulted source).

## Data inputs

- Accounting filter text: data: posted Ausar runtime inputs. No further data specification is in the record for this canonical id.

## Install and run

This package is INCOMPLETE-CODE: there is no code to install for this canonical id in the Test repo. Steps 1 to 3 of a recreation would be: 1. Read this package and the ALL-SLEEVES entry. 2. Stop: do not substitute the code of the separate BTC_ETH_SMA200 or ETH_SMA200 books and present it as this strategy. 3. A faithful install requires the original code or runtime record for this id, which is not in any searched GitHub repo.

## Verification

Behavior checklist from the recorded algorithm (a recreation cannot be proven against code, because no code was located):
1. An asset whose completed daily close is above its 200-day average qualifies for its recorded target weight.
2. An asset whose completed daily close falls below its 200-day average is reduced.
3. Any implementation claiming to be this strategy must be checked against the original code if it is ever located; until then this package stays INCOMPLETE-CODE.
