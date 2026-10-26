# SATY day system (SPY 0DTE)

Buys same-day SPY calls or puts at Saty ATR levels: the ±38.2% Golden Gate touch, a breakout after an open inside the trigger box, or a range-day fade.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Milkman Trades' SATY day system (Golden Gate, Bilbo, Trigger Box), on Saty Mahajan's indicators |
| **Asset** | SPY options (0DTE) |
| **Timeframe** | 1m · 3m · 10m · 1h |
| **Universe** | SPY (QQQ confirms) |
| **Style** | Intraday ATR levels |
| **Status** | waiting |

## Entry

- Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); levels at ±23.6, 38.2, 50, 61.8, 78.6 and 100% of the unit.
- Golden Gate: the first 1-minute touch of ±38.2% (or a fresh quote beyond it), taken within 30 minutes.
- Gates: the last completed 1-hour Phase Oscillator past -61.8 blocks a long (past +61.8 a short) and past +61.8 tags a long Bilbo; the 10-minute Pivot Ribbon Pro fully against (EMA 8 < 21 and 13 < 48) or in chop blocks, except on a gap through the level at the open; QQQ must confirm (its last 10-minute close beyond its own 23.6%, or its 38.2% touched today).
- Trigger Box: on a day opening within ±23.6%, the first completed 3-minute close beyond a trigger, within 30 minutes and until 90 minutes before the close; the same ribbon and chop vetoes.
- Range scalp: once a completed hour shows the day's range ≤ 70% of the unit with its close inside the box (until an hourly range over 90% or a 10-minute close beyond ±61.8%), buys calls on a touch of -38.2% and puts on +38.2%.
- Contract: today's SPY expiry, strike nearest the spot with a two-sided quote, spread ≤ 5% of mid, ≤ 60 s old; a limit at the mid; no same-day expiry is no trade.
- Entries from 09:30 to an hour before the close, one position at a time, none once the day is down $10,000.

## Exit

- Golden Gate: a 10-minute close back through the 23.6% trigger exits; half at 50%; all at 61.8% unless Bilbo-tagged or the 10-minute ribbon is fully aligned, then half stays on, is halved again at 78.6% and goes at 100%.
- Trigger Box: a 3-minute close back through the trigger exits; half at 50%; all at 100% unless the ribbon is fully aligned, then half rides.
- Range scalp: out at the opposite 38.2% level, or on a 10-minute close beyond the 61.8% level past the entry.
- Exits are limits at the option's mid; flat from 5 minutes before the close (the bid from 3 minutes, market from 2); a position from an earlier session is sold at once.

## Sizing

- 4% of the $10,000 slice in premium (half for a long Golden Gate from 12:00), whole contracts, at least 1.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY and QQQ 5-minute bars (about 22,000) and 1-minute bars (1,200), IEX quotes, today's SPY option chain and quotes, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/saty_day.py`. The strategy file is Midna v3's `sleeves/saty_day.py`
- **Midna v3**: `sleeves/saty_day.py`, `integration/saty_day_adapter.py`
- **Rule lines**: [docs/verify/muse.md](../../docs/verify/muse.md)

## Notes

- The $10,000 daily stop is the source's figure, unscaled: the whole slice.
- Breaks of the 1-hour EMA 21 and the 10-minute EMA 48 are logged, never traded.
- The master desk also expires every entry at 15:55 ET.
