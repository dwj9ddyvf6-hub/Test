# PO10 extreme (QQQ)

Goes long QQQ when the 10-minute Phase Oscillator closes above +100 (short below -100) in the first 90 minutes, and exits on the opposite extreme or at the close.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Milkman Trades' PO10 extreme algo (NQ, August 2026 thread), translated to QQQ shares |
| **Asset** | QQQ shares, long and short |
| **Timeframe** | 10m |
| **Universe** | QQQ |
| **Style** | Momentum |
| **Status** | waiting |

## Entry

- Signal: the first completed 10-minute bar closing between 09:30 and 11:00 ET with the Phase Oscillator above +100 (long) or below -100 (short); the oscillator runs on clock-aligned extended-hours bars (04:00-20:00).
- Acted on within 30 minutes of that close; one entry a session, no re-entry after the exit.
- A limit at the ask (long) or bid (short).

## Exit

- The first later 10-minute close beyond the opposite extreme; no stop and no target.
- Flat at 15:59 ET (a minute before an early close); the master desk expires every entry at 15:55 ET first.
- Exits are limits at the bid (long) or ask (short).

## Sizing

- Two Micro NQ equivalents: shares = round($4 × NQ / QQQ) with NQ taken as QQQ × 41, which is always 164 shares; a $100,000 slice.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- QQQ 5-minute bars (4,000) built into 10-minute bars, IEX quotes, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/sleeves/po10_qqq.py`, `sleeves/muse/muse.py`. Vendored from Midna v3
- **Midna v3**: `sleeves/po10_qqq.py`, `integration/po10_qqq_adapter.py`. A wrapper only; the strategy file is not in this repo
- **Rule lines**: [docs/verify/muse.md](../../docs/verify/muse.md)

## Notes

- Milkman's rule is on NQ futures; with no futures on the desk the signal and the position are both QQQ.
