# lz_s_mn_moonshot: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Moonshot (Midna port)", type "other", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: no stop / time exit 78 weeks", "hold_from": "plan", "hold_unit_kind": "1w", "stop_pct": 99.0, "max_bars": 78, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Rule lines in Test: `docs/verify/lazarus.md` (Moonshot weekly lane section) and the WeeklyCyanMoonshot book in `sleeves/midna/shadow.py`. The pick itself is generated upstream (Midna entire-branch signal files); the v3 lane is a fire-consumer by design, as its own file header records.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A lottery / deep-reset weekly lane: it takes an upstream moonshot pick at a 1% weight, holds it with no stop, and exits only at 78 weeks. The master-desk form of the same idea is the WeeklyCyanMoonshot book, which filters weekly cyan fires by cheapness and 60-week depth.

## Full algorithm

A. v3 fire-consumer (`sleeves/s_mn_moonshot.py`), in evaluation order:
1. Exits first: a held name exits when sessions held reach 390 (HOLD_SESSIONS = 390, i.e. 78 weeks x 5; the accounting record agrees: no stop, stop_pct 99.0, time exit 78 weeks, max_bars 78 in 1w units). No price stop at any point.
2. If anything is held, no entry: one slot.
3. Entry: only on a fresh fire naming sleeve_id s_mn_moonshot, aged 0 to 7 days (MAX_FIRE_AGE_DAYS = 7); the newest such fire wins. Absent, stale or malformed fires fail closed. A name whose feed is cross-stale is refused (ENH20 gate).
4. Sizing: $1,000 (BUDGET = 1000.0), recorded in the file header as the 1%-weight pick on the test book. Cadence 300 seconds.

B. Master-desk book (`sleeves/midna/shadow.py`, WeeklyCyanMoonshot / moonshot_step):
1. Entry fire: a weekly buy-cyan fire with close at most $14.94 and 60-week depth at least 70.35, at most 10 days old, not seen before, with fewer than 10 open in the tracker form (the book's own MOONSHOT_SLOTS cap governs its slots); one position per symbol; buys at a fresh regular-hours quote.
2. Sizing: floor(min(cash, $1,000) / price) per the verify record ($1,000 a position).
3. Exit: at the first regular-hours print after its 78th week (timeExitAt = the close of the last session of week 78); no stop.

## Files in this repo

- This doc: `docs/LZ_S_MN_MOONSHOT-RECREATE.md`
- Code (already in Test): `sleeves/s_mn_moonshot.py` (imports `sleeves/laz8_common.py`, present in Test at `engines/sleeves/laz8_common.py`)
- Code (already in Test, master book): `sleeves/midna/shadow.py` (WeeklyCyanMoonshot, moonshot_step)
- Rule lines: `docs/verify/lazarus.md` (Moonshot weekly lane section)
- NOT in Test: the upstream pick generator (Midna entire-branch signal files feeding midna_fires_v1.json, unreachable from the desk by the file header's own record); the desk-side management above is complete in Test.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: not recorded in the accounting for this id (not in the record); entries come only from fires.
- Timeframe: 1w plan (v3 hold counted in sessions: 390). Sizing: $1,000 per position, 1 slot (v3).
- Master book filters: close <= $14.94, 60-week depth >= 70.35, fire at most 10 days old.
- Cadence: 300 s (v3). State: the held position with its entry date; the master book also keeps a seen set.

## Data inputs

Fires: shadow/paper_sleeve/live/midna/midna_fires_v1.json per the accounting filter line (v3, via context.extra); the hourly watch's weekly moonshot fires (master book). Daily bars for sessions-held counting and pricing.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_moonshot` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/s_mn_moonshot.py`; confirm BUDGET = 1000.0, HOLD_SESSIONS = 390 and MAX_FIRE_AGE_DAYS = 7. Serve daily bars and fires carrying sleeve_id, symbol and date, and call `signal` per pass. For the master form, open `sleeves/midna/shadow.py` (moonshot_step) and serve weekly cyan fires with close and depth60 fields.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- No fire, a fire older than 7 days, or a malformed fire produces no v3 entry.
- A held v3 position is never stopped out on price, at any drawdown.
- The v3 exit fires exactly when sessions held reach 390.
- A second v3 entry never opens while a position is held.
- In the master book, a fire with close above $14.94 or depth60 below 70.35 is marked rejected and never entered.
