# Saty Magnum (SPY shares)

Trades SPY shares long or short when the daily and 10-minute Pivot Ribbons agree: a Golden Gate close and retest, a compression release, or an oscillator snap-back.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Saty Mahajan's system (ATR Levels, Pivot Ribbon Pro, Phase Oscillator, Volume Stack), from his posts |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 3m · 10m · 1h · 1d |
| **Universe** | SPY |
| **Style** | Intraday ATR levels |
| **Status** | waiting |

## Entry

- Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); levels at ±23.6, 38.2, 50, 61.8, 78.6, 100, 123.6 and 200% of the unit.
- Regime: trend up when both Pro ribbon clouds (EMA 8 ≥ 21, EMA 13 ≥ 48) are up on the daily and the 10-minute frames, trend down when all are down.
- Arm A, Golden Gate: a completed 10-minute close through ±38.2% (cancelled by a 10-minute close back through the 23.6% trigger); within 60 minutes a completed 3-minute bar reaches the zone between the gate and the 10-minute EMA 21 and closes back beyond the gate, with ≥ 55% of its volume split on the trade's side; the regime in trend that way; the 10-minute oscillator not beyond ∓100 and the 1-hour not beyond ∓61.8.
- Arm B, compression release: 2+ consecutive completed 10-minute bars in Phase Oscillator compression, then the first bar out closing beyond the coil's range with the oscillator's colour agreeing; not against both 10-minute clouds or the opposite daily trend.
- Arm C, snap-back (half size): the 3- and 10-minute oscillators below -100 and the 1-hour below -80 (mirror for shorts), the 3-minute oscillator already turning; one entry per episode.
- Schedule: from 09:40 to 30 minutes before the close; Arms A and B stand down 11:30-13:30 and once the day's range reaches 90% of the unit; caps 2 Arm A, 1 Arm B, 1 Arm C per episode, 3 entries a session, one position at a time; a -1% session stops entries; events over 30 minutes old are skipped.
- Orders: a limit at the ask (long) or bid (short) from an IEX quote ≤ 60 s old.

## Exit

- Arm A: a 10-minute close back through the 23.6% trigger exits; a third at 50%, a third at 61.8% (then a 10-minute close back through the entry exits the rest), the rest at 100% (123.6% when the next weekly-ladder level lies beyond it).
- Arm B: a 10-minute close through the coil's midpoint exits; thirds at 50% and 61.8% with the same break-even rule, half the runner at 100%, the rest at 200%.
- Arm C: out when the 10-minute oscillator is back to -23.6 (+23.6 for a short), on a 10-minute close beyond the opposite 23.6% trigger, or after 60 minutes.
- Exits are limits at the bid (long) or ask (short); flat at market 5 minutes before the close; a position from an earlier session is sold at once.

## Sizing

- Risk 0.5% of the $10,000 slice to the invalidation level (the 23.6% trigger, the coil midpoint, or the opposite trigger for Arm C at half), capped at 25% of the slice in notional; whole shares, none under 1.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY 5-minute bars (about 52,000, for the daily ribbon's warmup) and 1-minute bars (1,200), IEX quotes, ^VIX daily closes, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/saty_magnum.py`. The strategy file is Midna v3's `sleeves/saty_magnum.py`
- **Midna v3**: `sleeves/saty_magnum.py`, `integration/saty_magnum_adapter.py`

## Notes

- The VIX key level, the intraday pivot and EMA breaks against the position are recorded, never traded.
- Risk, caps, windows and the 55% vote are the desk's numbers; Saty states none.
