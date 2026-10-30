# lz_s_mn_turtle: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Turtle (Midna port)", type "breakout", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: turtle ATR stop / exit10", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test: `strategies/midna/mn-turtle.md` (Turtle System 1); rule lines in `docs/verify/midna.md` (Turtle System 1 section). Note: `sleeves/s_mn_opt_turtle.py` in Test is the listed-options expression of this same Turtle rule and is a different canonical id; this package is the equity book.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

Turtle System 1 on US equities: it buys 20-day (or 55-day) closing breakouts with Turtle unit sizing and pyramiding, and exits on a 2N stop or a close under the prior 10-day low. Style: breakout; timeframe 1d; universe: the Midna swing basket (card).

## Full algorithm

From the card and `docs/verify/midna.md`, read from `sleeves/midna/board.py` and `sleeves/midna/vendor/midna/board_signals.py`, in evaluation order:

1. Entry signal: a close above the prior 20-day high, or above the prior 55-day high, new today. At most 4 names, alphabetical.
2. Skip rule: a 20-day breakout right after a winning exit is skipped once; the 55-day breakout is taken.
3. Pyramiding: add a unit at each +0.5N move over the last add, up to 4 units per name. N = ATR(20).
4. Sizing: one unit = min(floor(1% of equity / N), floor(cash / price)).
5. Exit, stop: entry - 2N, raised with adds, acting on any regular-hours print.
6. Exit, signal: a close under the prior 10-day low. The accounting record for this id agrees in shorthand: "turtle ATR stop / exit10", stop_pct 99.0 (the stop is ATR-based, not a fixed percent), max_bars 0 (no time exit).
7. The card records that the master-desk port drops the source desk's desk-wide red-day buy gate and desk halt; those are not part of this book.

## Files in this repo

- This doc: `docs/LZ_S_MN_TURTLE-RECREATE.md`
- Code (already in Test): `sleeves/midna/board.py` (midna_turtle_s1 book: enter_turtle, the Turtle stop and 10-day exit paths), `sleeves/midna/vendor/midna/board_signals.py` (breakout signals), `sleeves/midna/common.py`
- Strategy card: `strategies/midna/mn-turtle.md`
- Rule lines: `docs/verify/midna.md` (Turtle System 1 section)
- Related but different id: `sleeves/s_mn_opt_turtle.py` (the options expression)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: the Midna swing basket (card wording; the basket list itself is not in the record: not in the record).
- Timeframe: 1d. Breakout windows: 20 and 55 sessions. Exit channel: 10 sessions. N = ATR(20).
- Unit: 1% of equity / N, capped by cash. At most 4 names; at most 4 units per name; add step 0.5N.
- State per name (from board.py's header): the peak print, the units held and the skip flags live in the sleeve's state.

## Data inputs

Completed daily bars of the swing basket (card Data section).

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_turtle` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/midna/board.py`; find the turtle book (IDS 'turtle' = midna_turtle_s1) and `enter_turtle`; confirm the 20/55-day breakout, the 0.5N adds to 4 units, the 2N stop and the 10-day exit match Configuration. Serve completed daily bars of the basket and run the book's regular-hours passes (stops act on any regular-hours print).
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A close that does not exceed the prior 20-day and prior 55-day highs produces no entry.
- A 20-day breakout immediately after a winning exit is skipped exactly once; a 55-day breakout in the same situation is taken.
- Adds happen only at +0.5N steps over the last add and never past 4 units.
- A regular-hours print at or below entry - 2N (as raised by adds) exits the name.
- A close under the prior 10-day low exits the name even when the stop was not touched.
- No more than 4 names are held at once, taken alphabetically.
