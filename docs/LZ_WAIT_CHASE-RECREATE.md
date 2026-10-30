# lz-wait-chase - Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "CHASE weekly lane", type momentum, family lazarus, algorithm grade PARTIAL (entry/exit/sizing gaps in the accounting), universe Liquid cross-section (dv20 >= $1M, close >= $5, operating companies), asset US equities, timeframe 1w, creator Research Lab frozen spec, wired on the master desk; alias lz_wait_chase (test_catalog, status blocked).
- Existing Test strategy card: `strategies/lazarus/lz-wait-chase.md` (full text used below).
- Code found in Test already: `sleeves/lazarus/lazarus.py` (the Lazarus runtime port, including the WAIT lanes) and `sleeves/lazarus/vendor/lazarus/` (signals.py, gate.py, cal.py, data.py, sleeves.json). The related s_wait_chase package `docs/S_WAIT_CHASE-RECREATE.md` documents the same CHASE rule in the runtime port in detail.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

CHASE weekly lane: buys weekly Cyan fires in the top tenth of 126-day momentum that sit within 5% of their 63-day high, and holds 52 weeks.

## Full algorithm

From the strategy card and the s_wait_chase runtime record in Test, in evaluation order:

1. Signal: a tracker 1W Cyan fire whose 126-day momentum (mom126 = close[t]/close[t-126] - 1) ranks >= 0.90 against the liquid cross-section (bar present, dv20 >= $1M, close >= $5, operating companies; the producer's LQ definition in the s_wait_chase record also records dv20 >= $0.5M as a UC pre-filter) and whose drawdown from the 63-day high is above -5% (close / max close over last 63 sessions, minimum 40 periods, - 1 > -0.05).
2. Entry: buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. The runtime port's capped-limit mechanics are recorded in docs/S_WAIT_CHASE-RECREATE.md: max_delay_minutes 65, limit_buffer_pct 1.0, limit_band_pct 5.0.
3. Exit: plan: no stop, time exit 52 weeks (W52 from the 1W fire week). Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% would sell on the live price (this lane records no stop); exits are DAY limits at the live price - 1%.
4. Sizing: $1,000 a position; K = 20. Fixed dollars per position, capped by a share of 20-day dollar volume (cap_pct_of_dv20 1.0), whole shares, inside the lane's budget and slot count; names under the dollar-volume floor (min_dv20_usd 100000 in the s_wait_chase config row) are skipped.

## Files in this repo

- This package: `docs/LZ_WAIT_CHASE-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- Strategy card: `strategies/lazarus/lz-wait-chase.md`; related package: `docs/S_WAIT_CHASE-RECREATE.md`; rule lines: `docs/verify/lazarus.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

Timeframe 1w; hold 52 weeks; $1,000 per position; K = 20; momentum rank >= 0.90; 63-day-high drawdown > -5%; entry DAY limit live price + 1% capped at fire close plus the lane band (limit_band_pct 5.0, limit_buffer_pct 1.0 in the runtime config record); exit DAY limit live price - 1%; no stop. Source config row for the underlying s_wait_chase lane is in `sleeves/lazarus/vendor/lazarus/sleeves.json` (see docs/S_WAIT_CHASE-RECREATE.md for the verbatim row).

## Data inputs

Tracker ledger; the tracker engine's daily store for the cross-section; wait fires in `shadow/paper_sleeve/live/wait_fires_v1.json` in the runtime port.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read `strategies/lazarus/lz-wait-chase.md`, this package, and `docs/S_WAIT_CHASE-RECREATE.md`.
3. Confirm `sleeves/lazarus/lazarus.py` and the vendor package are at their Test paths.
4. Produce/ingest the tracker 1W Cyan fires and the cross-section daily store.
5. Run the Lazarus pass for this lane and verify against the Verification section.

## Verification

- A fire with mom126 rank < 0.90 or 63-day-high drawdown <= -5% produces no entry.
- A qualifying fire produces one $1,000 entry, DAY limit at live price + 1% subject to the cap, one position per symbol.
- A held position exits only at the 52-week time exit (DAY limit at live price - 1%); no stop exit fires.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
