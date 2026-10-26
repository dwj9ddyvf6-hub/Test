# Qullamaggie episodic pivot

Buys a quiet stock that gaps up 10%+ on a verified catalyst with heavy early volume, when it takes out the opening-range high from minute 20.

| | |
|---|---|
| **Family** | Qullamaggie |
| **Source** | Kristjan Kullamägi (Qullamaggie), "How to master a setup: episodic pivots"; the pass-3 research desk |
| **Asset** | US equities |
| **Timeframe** | 1d setup · 1m trigger |
| **Universe** | 1,838-name genome |
| **Style** | Catalyst breakout |
| **Status** | waiting |

## Entry

- Pool: 20-day dollar volume ≥ $5M and a 126-session return ≤ 30%, while QQQ is risk-on.
- Open: gap ≥ 10% over the last close and first-20-minute volume ≥ 0.5× the 20-day average.
- Catalyst: a verified 8-K / 6-K public before the trigger minute.
- Trigger: from minute 20, price crosses the opening-range high; stop = the low before the trigger bar, within 1 ATR.

## Exit

- Hard stop at the entry stop.
- After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven.
- After 3 sessions, a close below the 10-day SMA (the 20-day when the close is more than 1.5 ATR above the 10-day) exits at the next open.

## Sizing

- 0.35% of the session's opening equity on the stressed loss per share: stop distance + the 95th-percentile adverse overnight gap (126 sessions) + round-trip friction; capped at 20% of equity per name, 100% gross, 25% per sector, 4% total open risk, 1% of 20-day dollar volume, 15 positions; a $100,000 book.

## Data

- Genome daily bars, 1-minute tapes, SEC EDGAR current reports (acceptance time).

## Code

- **Master desk (pass-3 research desk)**: `sleeves/qullamaggie/qullamaggie.py`, `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`. One setup per sleeve; the EDGAR catalyst and metadata producer (`desk/feedlib/qm_inputs.py`) is not in this repo
- **Rule lines**: [docs/verify/qullamaggie.md](../../docs/verify/qullamaggie.md)
