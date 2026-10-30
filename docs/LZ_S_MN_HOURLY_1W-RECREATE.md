# lz_s_mn_hourly_1w - Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Midna Hourly 1W (Midna port)", type other (classification evidence: lz_engine config shows only a midna_block execution policy and a 52-week time exit; the upstream Midna fire signal is not recorded), algorithm grade PARTIAL with gap: sizing not recorded in the accounting; alias lz_s_mn_hourly_1w (md2_catalog, status installed).
- Accounting record: entry {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: calibrated plan / time exit 52 weeks", "hold_from": "plan", "hold_unit_kind": "1w", "stop_pct": 15.0, "max_bars": 52, "rest": "time"}; data: sleeve_midna :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Code found in Test already for the same cell without the lz_ prefix: `sleeves/s_mn_hourly_1w.py` / `adapters3/s_mn_hourly_1w.py` (SLEEVE_ID = "s_mn_hourly_1w", delegating to desk3/lazarus_midna.py), engine `desk3/lazarus_midna.py`, and the existing package `docs/S_MN_HOURLY_1W-RECREATE.md` plus `docs/S_MN_HOURLY_1W-ALGORITHM.md`. The lz_ prefix is the md2 catalog form of the same sleeve id.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

The weekly Midna fire-consumer lane of the shared Lazarus Midna engine: it holds one fire-named position for up to 260 sessions (52 weeks), with a 15% stop, sized from a $1,000 budget, with no family or price-band gate. Signal generation stays upstream in the Midna fire producer.

## Full algorithm

From `docs/S_MN_HOURLY_1W-RECREATE.md` and desk3/lazarus_midna.py SPECS:

1. SPECS entry s_mn_hourly_1w: family=None, tf="1W", hold_sessions=260, stop=0.15, gate=None, budget=1000.0. Maximum 1 open position.
2. Exits first: for each non-zero position, price is the last bar close (keys SYM|1Day, SYM|1D, SYM, SYM|1Week, SYM|1W) or avg_price if no bars; age from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against bars. If price <= entry x (1 - 0.15), emit a full-qty market sell_to_close exit, reason stop_15pct. Else if age >= 260, emit a full-qty exit, reason time_52_weeks. Any exit returns; any held position suppresses entries.
3. Entries: fires from view midna_fires, view fires, extra midna_fires / fires, or the tensor / tensor_bundle value. Skip non-dict fires, mismatched sleeve_id, timeframe not matching 1W (1W, W, WEEKLY, WEEK accepted), missing symbol, or a date after the session or more than 10 days before it. No family filter (family=None).
4. Cross-stale gate (ENH20-MN-XSTALE-20261024, on by default; off via extra s_mn_hourly_1w_enh20 xstale_gate=False): refuse when the symbol's last bar date lags the snapshot's latest bar date by more than 4 days.
5. Price: ENH19 reprice on by default: when on and a fresh last close exists, price = that close; otherwise the fire price or the fresh close. Price <= 0 is skipped. Sizing: qty = int(1000.0 // price); qty < 1 is skipped. Emit one market, day, buy_to_open entry, price_hint = price, reason naming tensor_weekly_1W and gate=none, then stop.

## Files in this repo

- This package: `docs/LZ_S_MN_HOURLY_1W-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/s_mn_hourly_1w.py`, `adapters3/s_mn_hourly_1w.py`, `integration/s_mn_hourly_1w_adapter.py`, shared engine `desk3/lazarus_midna.py`
- Existing packages/docs: `docs/S_MN_HOURLY_1W-RECREATE.md`, `docs/S_MN_HOURLY_1W-ALGORITHM.md`, `docs/LZ_S_MN_HOURLY-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

Engine SPECS as in step 1. Existing S_MN_HOURLY_1W package records the roster row: capital_usd 1000.0, cash_usd 1000.0; cadence 300 seconds; session rth; flat_by_close false; bp_buffer_frac 0.02; params {}; parked false; roster inputs tensor, bars, positions. Accounting entry policy midna_block is in Provenance.

## Data inputs

Tensor / Midna fires (view tensor or the fire channels in step 3) with sleeve_id, symbol, family, timeframe, date and price, producer tensor_bundle (freshness SLA 86400s in the engine PRODUCERS); bars per symbol (SLA 900s); positions with symbol, qty, avg_price and age/opened fields (broker_readback, SLA 900s). Fire file in the accounting: shadow/paper_sleeve/live/midna/midna_fires_v1.json.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Place/confirm desk3/lazarus_midna.py and the adapter at their Test paths with SLEEVE_ID = "s_mn_hourly_1w".
3. Register the roster row exactly as in Configuration.
4. Wire the producers so snapshots carry the fires, bars, positions, now and session.
5. Call evaluate(view, ctx) on the adapter; it delegates to desk3.lazarus_midna.evaluate("s_mn_hourly_1w", view, ctx).
6. Run the Verification checks before treating a recreation as faithful.

## Verification

- A position at or below 85% of entry exits with stop_15pct; a position aged 260 sessions exits with time_52_weeks; at 259 sessions above the stop it is held.
- A fire for another sleeve, a 1D timeframe, a future date, or a date more than 10 days old produces no entry; any family value is accepted.
- Sizing: qty = int(1000.0 // price), exactly one entry, and any held position suppresses entries.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
