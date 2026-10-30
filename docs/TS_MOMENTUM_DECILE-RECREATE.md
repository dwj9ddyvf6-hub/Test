# ts_momentum_decile: Recreation package

Provenance: The old Alpaca swing desk, via Femto-lean (Source row in strategies/femto/femto-ts-momentum-decile.md in this repo).

## What this sleeve is
This sleeve holds the top decile of liquid genome names by 252-trading-day return, equal-weighted, rebalanced monthly: eligibility, bankruptcy-artifact hygiene and a 25 percent sector cap decide the book, and the rebalance itself is the only risk management (no stops, no take profit). Sources: desk sleeves/ts_momentum_decile.py (MIN_BARS=253, MEDIAN_DV_DAYS=63, MEDIAN_DV_MIN=1000000, DECILE=0.10, EQUITY_UTIL=0.95, NEW_ENTRIES_PAUSED=False, SECTOR_CAP=0.25, plus the module's SECTOR_MAP; CONFIG cadence_s=300) and desk3/enhance26.py (ts_momentum_decile stale_bar_gate).

## Full algorithm
Evaluation in desk sleeves/ts_momentum_decile.py TsMomentumDecile.signal(bars, slice_state, context); this function emits the rebalance diff whenever called: rebalance gating (first trading day of the month, once per month) is the Scheduler's, not the sleeve's.
1. Ranking (rank_decile): for each symbol, drop the forming bar first (a last bar dated on or after the session date is excluded, the point-in-time law). A symbol is eligible only if at least 253 bars remain, its trailing-63-day MEDIAN dollar volume (median_dv over the last 63 bars) is at least $1,000,000, and it has no bankruptcy-artifact signature (has_artifact_signature over the last 504 bars: a monthly return above +500 percent preceded by at least 3 months each with |return| below 5 percent, monthly returns measured from the PREVIOUS month's final close). Score = last close / close 253 bars back in the trimmed series (closes[-1] / closes[-253]) - 1; a non-positive base close or non-finite last close excludes the symbol.
2. Decile: sort eligible names by score descending; take the top ceil(10 percent) (at least 1 when any are eligible).
3. Sector cap by count (apply_sector_cap): using the module's SECTOR_MAP (unknown sector = OTHER, uncapped), iteratively trim the lowest-ranked names of any known sector holding more than 25 percent of the kept count, until no known sector is over the cap.
4. Rebalance sells first: every held name (extra[sleeve_state]) not in the capped decile is sold in full at its last close, reason naming ts_momentum_decile rebalance: dropped from top decile. Held names still in the decile are left untouched (no resizing sells or buys in this function).
5. Entries (NEW_ENTRIES_PAUSED is False; entries also require equity > 0): per-name notional = equity x 0.95 / (number of decile names); for each decile name not already held, with a positive last close, qty = int(per_name // price); qty below 1 emits nothing (no forced 1-share floor). Entry price_hint = round(last close, 2); reason naming the rebalance, the 252d momentum and the equal-weight amount.
6. ENH sector cap by value (default ON; OFF via extra[ts_momentum_decile_improve][sector_cap_value_pass]=False restores the count-cap-only rule): after sizing, re-enforce the 25 percent cap on the SIZED entry set by value, dropping the lowest-ranked names of any known sector over 25 percent of total sized notional until it is at or below the cap; dropped slots stay unspent.
7. Adapter-layer gate (desk3/enhance26.py, ENH-B26-20261024, default ON; switch extra[ts_momentum_decile_improve2][stale_bar_gate]): refuse an entry whose symbol's newest 1Day bar is more than STALE_BAR_DAYS=7.0 days old at the evaluation clock. Rebalance sells are never filtered. There are no stops and no take profit anywhere in this sleeve.

## Files in this repo
- Sleeve module: sleeves/ts_momentum_decile.py (strategy logic and CONFIG).
- v3 adapter: adapters3/ts_momentum_decile.py (SLEEVE_ID=ts_momentum_decile; evaluate(view, ctx) rebuilds the v2 SleeveContext via adapters3/_snapshot_ctx.SnapshotSleeveContext, delegates to adapters/ts_momentum_decile.py, then applies desk3/enhance26.filter_entries; the _snapshot_ctx glue itself is not in this repo at its canonical path, as the audit record notes).
- v2 adapter mirror: integration/ts_momentum_decile_adapter.py in this repo (the adapters/ts_momentum_decile.py evaluate it mirrors).
- Shared engine file: engines/desk3/enhance26.py (desk desk3/enhance26.py: ENH-B26-20261024 adapter-layer gates, default ON per sleeve).
- Existing strategy doc: strategies/femto/femto-ts-momentum-decile.md.
- Config: engines/config/sleeves.json (row id=ts_momentum_decile), also at config/sleeves.json.

## Configuration
Module adapters3.ts_momentum_decile; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars]; parked false. Universe: the genome names present in the bars snapshot (the existing doc names the 1,838-name genome); timeframe daily bars, monthly rebalance gated by the Scheduler. Source: muse-desk-v3/config/sleeves.json row id=ts_momentum_decile. Note the existing doc's $100,000-book and 75bp cost figures are master-desk / study context; the v3 sizing rule in the Full algorithm section and the roster slice above govern this recreation.

## Data inputs
Inputs are bars: daily bar dicts {t,o,h,l,c,v} ascending per genome symbol (at least 253 closed bars per ranked name, 504 for the artifact scan), plus sleeve_state via context.extra {SYM: {position {entry_px, entry_date, qty}}}. The existing doc's Data section names split-adjusted daily bars of the genome (400, cached) and desk quotes on the master desk. A symbol whose bars end before the session has its forming bar dropped before ranking, exactly as the algorithm states.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `ts_momentum_decile` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/ts_momentum_decile.py, whose evaluate(view, ctx) delegates to adapters/ts_momentum_decile.py, which runs sleeves/ts_momentum_decile.py signal(bars, slice_state, context), after which desk3/enhance26.filter_entries is applied.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with 100 eligible names: the decile holds exactly the top 10 by 252-session return, each new entry sized int((equity x 0.95 / 10) // price), and any known sector over 25 percent of the kept count has its lowest-ranked names trimmed before sizing.
- Fixture with a held name absent from the new decile: exactly one full rebalance sell for it; a held name still in the decile receives no intent.
- Fixture with a name carrying a month above +500 percent preceded by 3 months each under 5 percent in absolute value, or with median 63-day dollar volume below $1,000,000, or with fewer than 253 bars after the forming bar is dropped: that name is not ranked.
- Fixture whose newest bar for an entry symbol is more than 7 days old at the evaluation clock: that entry is refused by the adapter gate, while a rebalance sell for a held name in the same fixture still passes.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
