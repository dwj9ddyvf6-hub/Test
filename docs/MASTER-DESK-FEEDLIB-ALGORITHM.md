# master-desk-feedlib

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/feedlib/.

The master desk's data-feed library: one module per feed family supplying sleeve inputs, including Alpaca canonical bars, earnings and corporate actions, EDGAR buyback data, Binance funding/spot observation relays, Kraken data, index and market-cap data, IV backfill, leader/discovery feeds, and the per-strategy feed adapters (apex, aurelia, ausar_pead, blowoff, dcg, Author_tensor, griffith, m2, midna) that normalize vendor and broker data into the shapes the master-desk sleeves consume.

## Files in this package

- `packages/claude/master-desk-feedlib/desk/feedlib/__init__.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/apex.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/apex_book.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/apex_rules.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/aurelia.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/aurelia_options.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/ausar_pead.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/binance_funding_relay.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/binance_spot_obs.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/blowoff.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/canonical.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/canonical_alpaca.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/corp_actions.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/dcg.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/discovery.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/earnings.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/edgar_buyback.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/free_options_inputs.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/Author_tensor.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/griffith.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/griffith_earnings.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/griffith_intraday.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/iv_backfill.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/killed_data.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/kraken.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/leader.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/m2.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/mcap.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_fires.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_forward.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_forward_runner.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_hyperliquid.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_kronos.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_kronos_runner.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_options.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_panel.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_qld.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_signals.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_watch.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/midna_watch_runner.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/Author_phd.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/Author_tensor.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/midna.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/ts_resolve.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/workspace_fs.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node/workspace_fs_sync.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/node_source.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/polymarket.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/qm_inputs.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/r19_book.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/r19_ledger.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/r19_source.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/release_calendar.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/sentiment.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/tbill.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/tensor.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/tensor_features.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/tensor_research.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/tensor_research.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/tensor_research_hands.mjs`
- `packages/claude/master-desk-feedlib/desk/feedlib/ts_bridge.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/ts_source.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/ts_yahoo.py`
- `packages/claude/master-desk-feedlib/desk/feedlib/yahoo_spark.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.

## Sanitization note

This copy was sanitized at 33 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/feedlib/ is the verbatim source.
Sanitized files in this package (non-verbatim copies):
- packages/claude/master-desk-feedlib/desk/feedlib/edgar_buyback.py: 1 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/Author_tensor.py: 6 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/midna_fires.py: 3 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/midna_panel.py: 1 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/midna_watch_runner.mjs: 1 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/node/Author_phd.mjs: 5 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/node/Author_tensor.mjs: 5 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/node/workspace_fs.mjs: 3 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/node/workspace_fs_sync.mjs: 3 occurrence(s) replaced
- packages/claude/master-desk-feedlib/desk/feedlib/sentiment.py: 1 occurrence(s) replaced
- docs/MASTER-DESK-FEEDLIB-ALGORITHM.md: 4 occurrence(s) replaced
Files whose package path was renamed to pass the same gate (original filenames are in the private origin named above):
- packages/claude/master-desk-feedlib/desk/feedlib/Author_tensor.py
- packages/claude/master-desk-feedlib/desk/feedlib/node/Author_phd.mjs
- packages/claude/master-desk-feedlib/desk/feedlib/node/Author_tensor.mjs
