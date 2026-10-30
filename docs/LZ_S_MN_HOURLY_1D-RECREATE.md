# lz_s_mn_hourly_1d: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Hourly 1D (Midna port)", type "forecast and ML models", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: calibrated plan / time exit 40 sessions", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 15.0, "max_bars": 40, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
The shared book that runs every lane is `sleeves/midna/hourly.py` (the Hourly Tensor playbook port, frozen playbook 1.0.0); its card is `strategies/midna/mn-hourly-playbook.md` and its rule lines are in `docs/verify/midna.md` (Hourly Tensor playbook section).
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

The 1-day lane of the Midna Hourly Tensor book: it buys first-of-setup Tensor consensus-buy fires dated to the daily (1d) lane, under the frozen playbook 1.0.0, with a calibrated stop (15% in the accounting record for this id) and a 40-session time exit. This id is the 1d variant of the same book whose 1h lane is `lz_s_mn_hourly`.

## Full algorithm

From `sleeves/midna/hourly.py` (header and `step` / `plan_for_new_entry` / `entry_window` / `time_exit_at`) and the accounting record above, in evaluation order:

1. Fires: read the hourly watch inbox fires. A fire is decided once (seen set): skipped when its setup episode (sym:lane:unit:fireBar) already traded, when its unit or tags match a killed rule, when it is not tradeable or not from Yahoo bars, when dv20 (mean of the last 20 close x volume, volume > 0) is unknown or below $1,000,000. Only fires with lane "1d" belong to this sleeve.
2. Entry window: the next session's 09:30 ET plus 65 minutes (MAX_DELAY_MIN 1d = 65; the accounting entry policy records the same 65 minutes, limit band 5.0%, limit buffer 1.0%, order capped_limit_day, policy midna_block, stock_red false, qqq_red false).
3. Ranking and capacity: best rank first (meta decile x 1,000,000 + score, then symbol). Lane cap for 1d is 5 open positions (book-wide 20 slots). A name already held is skipped; a full lane waits for the next pass inside the window (capacityWait).
4. Price gate: a fresh quote (at most 15 minutes old, at most 1 minute ahead) whose last is within the 1d limit band of 5% over the fire close; otherwise the fire waits inside its window.
5. Sizing: slot = min($5,000, 1% of dv20); cash below 90% of the slot skips the entry; qty = floor(min(slot, cash) / paper price), the paper price being the ask to the cent, else last plus the research cost. Book: $100,000, 20 slots of $5,000.
6. Plan on entry: the calibrated plan from the fire (calibratedStopPct / calibratedMaxBars); where the fire carries none, the defaults are stop as calibrated and maxBars 40 for the 1d lane. The accounting record for this id fixes stop_pct 15.0 and max_bars 40.
7. Exit (regular hours, fresh quote, exits evaluated before entries): the plan stop (last <= entry x (1 - stop%)) sells at the bid (else last minus the research cost); otherwise the time exit at the close of the 40th session from the entry bar (timeExitAt for lane 1d).

## Files in this repo

- This doc: `docs/LZ_S_MN_HOURLY_1D-RECREATE.md`
- Code (already in Test): `sleeves/midna/hourly.py` (lane constants LANE_CAPS, MAX_DELAY_MIN, LIMIT_BAND; `plan_for_new_entry`, `entry_window`, `time_exit_at`, `step`), `sleeves/midna/lanes.py`, `sleeves/midna/common.py`
- Strategy card: `strategies/midna/mn-hourly-playbook.md`
- Rule lines: `docs/verify/midna.md` (Hourly Tensor playbook section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: the Midna swing basket carried by the hourly watch inbox (the accounting records no explicit universe list: not in the record beyond the fire source).
- Timeframe / lane: 1d. Book: $100,000; 20 slots; lane caps 1h 5 / 1d 5 / 1w 10.
- Entry window: next session 09:30 ET + 65 min. Limit band: 5% (1d). Minimum dv20: $1,000,000.
- Plan: stop 15.0%, max 40 sessions (accounting record for this id); calibrated values on the fire override where present.
- State: the book's seen set, setup episodes, capacityWait list, open positions with their plan and timeExitAt.

## Data inputs

The hourly watch's inbox (Tensor-watch port) for fires; completed daily bars for dv20; live quotes (freshness at most 15 minutes) for entry and exit pricing (card and code Data sections).

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_hourly_1d` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/midna/hourly.py`; confirm LANE_CAPS['1d'] = 5, MAX_DELAY_MIN['1d'] = 65 and LIMIT_BAND['1d'] = 0.05, and that `plan_for_new_entry` defaults the 1d lane to 40 bars. Feed the book only fires with lane '1d', serve the watch inbox, daily bars and fresh quotes, and run a pass inside each entry window.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A 1d fire with dv20 below $1,000,000, a killed-rule unit, or an already-traded episode produces no entry.
- An entry is attempted only inside the next session's 09:30 ET + 65 minute window and only within 5% of the fire close.
- A sixth concurrent 1d position is not opened (lane cap 5); a held name is not re-bought.
- Slot size equals min($5,000, 1% of dv20); cash below 90% of the slot skips the entry.
- A held name exits at the plan stop (15% in the accounting record) or at the close of the 40th session, whichever comes first.
