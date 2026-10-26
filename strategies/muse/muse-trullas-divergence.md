# Trullas divergence (QQQ 1-minute)

Trades QQQ on 1-minute MACD divergences between two same-day swing pivots, entering on a 23.6% retrace and scaling out at 38.2% and 61.8%.

| | |
|---|---|
| **Family** | Muse |
| **Source** | David Trullas Vila's divergence method, from Midna's frozen spec |
| **Asset** | QQQ shares, long and short |
| **Timeframe** | 1m |
| **Universe** | QQQ |
| **Style** | Divergence reversal |
| **Status** | Midna's desk only |

## Entry

- Pivots: a bar strictly highest (or lowest) over 5 bars each side, usable once those 5 bars have closed; regular-session bars with volume.
- Setup: two consecutive same-kind pivots of one day, 10-120 bars apart, with price diverging from the MACD(12, 26, 9) line (required); RSI(14) divergence and lower volume on the second extreme add to the count (1-3).
- Trigger (bearish): A = the lowest low between the highs, B = the second high; entry when price trades through B - 0.236 × (B - A) - 1 tick; bullish mirrored; the day's newest untraded setup is the one pending.
- Cancelled after 30 bars or by a trade more than a tick beyond B; entries 09:30-11:00 ET, at most 5 a day, none after a -0.75% day.

## Exit

- Stop one tick beyond B, checked before the targets on the same bar.
- TP1 at 38.2%: half off and the stop to the entry; TP2 at 61.8%: the rest.
- Flat at 12:00 ET.

## Sizing

- Divergence count × 0.25% of the slice at risk to the stop, capped at 25% of the slice in notional; whole shares.

## Data

- QQQ 1-minute bars.

## Code

- **Midna v3**: `sleeves/trullas_divergence.py`, `integration/trullas_divergence_adapter.py`, `integration/trullas_divergence_worker.py`

## Notes

- The frozen spec is `docs/TRULLAS-SPEC-2026-10-25.md`; this is its primary arm.
- Not on the master desk: its pinned source commit could not be read.
