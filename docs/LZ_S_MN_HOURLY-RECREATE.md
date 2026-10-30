# lz_s_mn_hourly: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Hourly (Midna port)", type "forecast and ML models", family "1h", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 30, "limit_band_pct": 3.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: disaster stop 15% / time exit 60 bars", "hold_from": "plan", "hold_unit_kind": "1h", "stop_pct": 15.0, "max_bars": 60, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test: `strategies/midna/mn-hourly-playbook.md`; rule lines in `docs/verify/midna.md` (Hourly Tensor playbook section). The card records that the v3 wrapper `sleeves/lazarus/s_mn_hourly.py` calls a laz_sleeves._common module that is not in this repo; the complete book logic is the master-desk port `sleeves/midna/hourly.py`, which is in Test and is the code this package rests on.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

The hourly lane of the Midna Hourly Tensor book: it buys first-of-setup 1H consensus-buy (gap20) fires of the swing basket under the frozen playbook 1.0.0, with the 1h-basket plan of no plan stop beyond the recorded 15% disaster stop and a 60-bar time exit. Its 1d sibling is `lz_s_mn_hourly_1d`.

## Full algorithm

From `sleeves/midna/hourly.py` and the accounting record above, in evaluation order:

1. Fires: read the hourly watch inbox. For the 1h lane a fire must be a gap20, first-of-setup 1H consensus buy. A fire is decided once (seen set): skipped when its setup episode (sym:lane:unit:fireBar) already traded, when its unit or tags match a killed rule, when it is not tradeable or not from Yahoo bars, when a 1H fire is not the first of its gap20 episode, or when dv20 (mean of the last 20 close x volume) is unknown or below $1,000,000.
2. Entry window: the next bar's open plus 30 minutes (MAX_DELAY_MIN 1h = 30; the accounting entry policy records the same 30 minutes, limit band 3.0%, limit buffer 1.0%, order capped_limit_day, policy midna_block).
3. Ranking and capacity: best rank first (meta decile x 1,000,000 + score, then symbol). Lane cap for 1h is 5 open positions (book-wide 20 slots). Entries only in regular hours; a held name is skipped; a full lane waits for the next pass inside the window (capacityWait).
4. Price gate: a fresh quote (at most 15 minutes old, at most 1 minute ahead) whose last is within the 1h limit band of 3% over the fire close; otherwise the fire waits inside its window.
5. Sizing: slot = min($5,000, 1% of dv20); cash below 90% of the slot skips; qty = floor(min(slot, cash) / paper price) (ask to the cent, else last plus the research cost). Book: $100,000, 20 slots of $5,000.
6. Plan: the 1h-basket plan is no stop / time exit 60 bars in the playbook; the accounting record for this id records the plan as disaster stop 15% / time exit 60 bars (stop_pct 15.0, max_bars 60, hold unit 1h). Both lines are recorded here exactly as found; the 60-bar time exit is common to both.
7. Exit (regular hours, fresh quote, exits before entries): the plan stop when one applies (last <= entry x (1 - stop%)) or the time exit at the close of the 60th hourly bar from the entry bar, sold at the bid (else last minus the research cost).

v3 wrapper (`sleeves/lazarus/s_mn_hourly.py`, in Test): SLEEVE_ID s_mn_hourly, inputs bars_1hour / positions / midna_signals, evaluate delegates to mn_hourly_evaluate with stop=True and slots=12; its laz_sleeves._common dependency is not in this repo (per the card), which is why this package rests on the complete hourly.py port above.

## Files in this repo

- This doc: `docs/LZ_S_MN_HOURLY-RECREATE.md`
- Code (already in Test): `sleeves/midna/hourly.py` (the complete book: entry_window, plan_for_new_entry, time_exit_at, step), `sleeves/midna/lanes.py`, `sleeves/midna/common.py`
- Code (already in Test, v3 wrapper): `sleeves/lazarus/s_mn_hourly.py` (its laz_sleeves._common dependency is NOT in Test, per the card)
- Strategy card: `strategies/midna/mn-hourly-playbook.md`
- Rule lines: `docs/verify/midna.md` (Hourly Tensor playbook section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: the Midna swing basket carried by the hourly watch inbox.
- Timeframe / lane: 1h. Book: $100,000; 20 slots; lane caps 1h 5 / 1d 5 / 1w 10.
- Entry window: next bar's open + 30 min. Limit band: 3% (1h). Minimum dv20: $1,000,000.
- Plan: time exit 60 bars; stop 15.0% per the accounting record (the playbook's 1h-basket plan line records no stop; see the algorithm section).
- v3 wrapper parameters: stop=True, slots=12.
- State: seen set, setup episodes, capacityWait list, open positions with plan and timeExitAt.

## Data inputs

The hourly watch's inbox (Tensor-watch port) for fires; completed daily bars for dv20; live quotes (freshness at most 15 minutes) for entry and exit pricing.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_hourly` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/midna/hourly.py`; confirm LANE_CAPS['1h'] = 5, MAX_DELAY_MIN['1h'] = 30, LIMIT_BAND['1h'] = 0.03 and the 1h-basket plan (60 bars) in `plan_for_new_entry`. Feed the book only lane '1h' fires, serve the watch inbox, daily bars and fresh quotes, and run passes inside each entry window during regular hours.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A 1H fire that is not gap20 and first-of-setup, matches a killed rule, or has dv20 below $1,000,000 produces no entry.
- An entry is attempted only in regular hours, inside the next bar's open + 30 minute window, and within 3% of the fire close.
- A sixth concurrent 1h position is not opened (lane cap 5); a held name is not re-bought.
- Slot size equals min($5,000, 1% of dv20); cash below 90% of the slot skips the entry.
- A held 1h-basket position exits no later than the close of the 60th hourly bar from its entry bar.
