# Qullamaggie parabolic short

Shorts a name after 3+ up days and a parabolic 3-session run when the opening-range low breaks under VWAP, and covers at its 10/20-day average.

| | |
|---|---|
| **Family** | Qullamaggie |
| **Source** | Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; the pass-3 research desk |
| **Asset** | US equities |
| **Timeframe** | 1d setup · 1m trigger |
| **Universe** | 1,838-name genome |
| **Style** | Parabolic short |
| **Status** | waiting |

## Entry

- Setup: ≥ 3 consecutive up closes and a 3-session run ≥ 50% (≥ 300% at a market cap ≤ $300M); borrowable; $5M dollar volume.
- Trigger: a bar's low reaches the opening-range low and closes under the session VWAP; short at the next bar's open, stop = the high before the fill.

## Exit

- Hard stop at that high.
- Covers at max(10-day, 20-day SMA) of the completed closes.
- After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven.
- After 3 sessions, a close above the 10-day SMA exits.

## Sizing

- Half the long risk: 0.175% of opening equity on the stressed loss per share; the same caps.

## Data

- Genome daily bars, 1-minute tapes, EDGAR share counts for the market cap.

## Code

- **Master desk (pass-3 research desk)**: `sleeves/qullamaggie/qullamaggie.py`, `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`. One setup per sleeve; the EDGAR catalyst and metadata producer (`desk/feedlib/qm_inputs.py`) is not in this repo
