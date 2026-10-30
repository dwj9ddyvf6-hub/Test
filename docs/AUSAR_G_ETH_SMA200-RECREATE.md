# ausar_g_ETH_SMA200: Recreation Package

Package grade: INCOMPLETE-CODE. The algorithm text on file is reproduced below, but the genuine code that runs this book was not located in any searched GitHub repo, so this package does not claim a faithful recreation.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Daily SMA200 spot allocation", type trend following, family native_trend. Sole alias: `ausar_g_ETH_SMA200`, recorded installed, source md2_catalog. Algorithm grade PARTIAL; recorded gap: "sizing not recorded in any consulted source".
- This id was created by the genuine-hosting pass recorded in Test at `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py`: md2 book `ausar_pb7` was retired (status replaced) and hosted by the posted genuine code, desk `prospective_native`, book `ETH_SMA200`, origin `quant-research-backup@1692d555 backend/prospective_native.py`, with the note "rules match the TSV entry/exit text".
- CONFLICT IN THE RECORD, stated plainly: the accounting entry text for this id reads "Target weights: Bitcoin 50%, Ether 50%", while its genuine book name (ETH_SMA200), the Test card `strategies/ausar/coinbase-sma200.md` ("Weights: ETH_SMA200 0/1"), and the v3 engine spec all describe this book as ETH only. The accounting text is reproduced verbatim in the algorithm section and flagged, not silently corrected.

## What this strategy is

The genuine (original-code) hosting of the daily SMA200 spot allocation book named ETH_SMA200: an asset is held while its completed daily close is above its 200-day simple moving average. It is the same strategy family as the `ETH_SMA200` package in this repo, but a distinct canonical record because it ran the posted original code rather than the md2 reimplementation or the v3 port.

## Full algorithm

Everything the record holds (accounting, verbatim in substance):

- Entry: "An asset qualifies when its completed daily close is above its 200-day simple moving average. Target weights: Bitcoin 50%, Ether 50%." (See the conflict note in Provenance: the weight line conflicts with the book name and every other record for this book.)
- Exit: "Reduce an asset when its completed daily close falls below its 200-day average; sell reductions before buying increases."
- Sizing: not in the record.
- Cadence, rebalance timing, fee treatment, warmup behavior: not in the record for this genuine-hosted book.

## Files in this repo

- This package: `docs/AUSAR_G_ETH_SMA200-RECREATE.md`
- Strategy card covering this book family: `strategies/ausar/coinbase-sma200.md`
- Hosting map that created this canonical id: `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py` (records the genuine book id, its desk `prospective_native`, and its origin `quant-research-backup@1692d555 backend/prospective_native.py`)
- NOT in this repo: the genuine strategy code itself. `backend/prospective_native.py` was not found in the current tree of dwj9ddyvf6-hub/quant-research-backup, nor in dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, or dwj9ddyvf6-hub/Midna (trees searched at package build time for prospective_native / native / sma200 paths). Test does contain a port of that same source for the sibling v3 sleeves (`desk3/aster_batch1.py` kind "native", wrappers `sleeves/aster_native_btc_eth_sma200.py` and `sleeves/aster_native_eth_sma200.py`), but that port belongs to the sibling canonical ids and is not presented here as this strategy's original code.

## Configuration

- Universe, asset class, timeframe: "not recorded in consulted sources" in the accounting. The hosting map records only: genuine desk `prospective_native`, data "posted Ausar runtime inputs", status installed, local paper ledger `state/ausar_orig` (a path on the md2 desk, not in any searched repo).
- Sizing: not in the record (accounting gap).

## Data inputs

Per the accounting filter text: "data: posted Ausar runtime inputs".

## Install and run

This package cannot be installed as a faithful recreation, because the genuine code is not present in any searched GitHub repo:

1. Obtain `backend/prospective_native.py` (and its math module) from quant-research-backup at commit 1692d555, the origin recorded in the hosting map; it is absent from that repo's current tree.
2. Until that code is recovered, the closest runnable relative in this repo is the sibling port `desk3/aster_batch1.py` (kind "native") used by the `BTC_ETH_SMA200` / `ETH_SMA200` packages; running it recreates the sibling v3 sleeves, not this genuine-hosted book, and must not be reported as this strategy running.

## Verification

No tests for this genuine-hosted book exist in Test. Behavior checklist from the recorded algorithm (for use once the genuine code is recovered):

- A completed daily close above the asset's SMA200 qualifies the asset at its recorded target weight.
- A completed daily close below the SMA200 reduces the asset.
- Behavior on insufficient history, fees, and order mechanics: not in the record; to be read from the recovered code, not assumed.
