# Qullamaggie breakout

Buys a top-2% momentum leader when it breaks out of a tight, rising 10-session base after the opening range, with the stop at the day's low before the trigger.

| | |
|---|---|
| **Family** | Qullamaggie |
| **Source** | Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; three desk implementations |
| **Asset** | US equities |
| **Timeframe** | 1d setup · 5m / 1m trigger |
| **Universe** | 1,838-name genome · 20 mega-caps |
| **Style** | Breakout |
| **Status** | 1 live · 2 waiting |

## Entry

- Leader: the best of its 21-, 63- and 126-session return percentiles is ≥ 98% of the universe.
- Setup: the 63-session high ≥ 30% above the close 64 sessions back; 10-session base range ≤ 28% of the close; the late half no wider than the early half; base lows sloping up; ≥ 70% of base closes within 3% of the 10- or 20-day SMA; both SMAs rising over 3 sessions; 20-day dollar volume ≥ $5M.
- Trigger: after the 5-minute opening range, price reaches max(opening-range high, base high); the stop is the lowest low before the trigger bar, and a stop wider than 1 ATR(20) skips the trade.
- Femto: enters at the next bar's open within 30 minutes of the trigger, never below the trigger.
- Aurelia paper and pass-3: longs only while QQQ is risk-on (10-day SMA above the 20-day, both rising).

## Exit

- Hard stop at the entry stop.
- After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven.
- After 3 sessions, a close below the 10-day SMA (the 20-day when the close is more than 1.5 ATR above the 10-day) exits at the next open.
- Femto: the same scale and trail, decided on the last completed daily close.

## Sizing

- 0.35% of the session's opening equity on the stressed loss per share: stop distance + the 95th-percentile adverse overnight gap (126 sessions) + round-trip friction; capped at 20% of equity per name, 100% gross, 25% per sector, 4% total open risk, 1% of 20-day dollar volume, 15 positions; a $100,000 book.
- Femto: the same stressed-loss sizing with 0.35% risk, 20% per name, 1% of 20-day share volume, 10 positions, 3 bps friction a side.

## Data

- Split-adjusted daily bars of the genome (cached); today's 5-minute bars (Femto) or 1-minute tapes (paper, pass-3); QQQ daily bars.

## Variants

| Variant | Rows | Universe | Trigger bars | Market filter | Positions |
|---|---|---|---|---|---|
| Pass-3 research desk | `qm_leader_breakout_pass3` | genome | 1-minute | QQQ risk-on | 15 |
| Femto-lean's own | `femto_qullamaggie`; Midna v3 `qullamaggie` | genome | 5-minute | none | 10 |
| Aurelia paper engine | `femto_qullamaggie_paper`; Midna v3 `qullamaggie_paper` | 20 mega-caps | 1-minute | QQQ risk-on; the book down 1.5% at the open sells all | 15 |

Rows: 3 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk (pass-3 research desk)**: `sleeves/qullamaggie/qullamaggie.py`, `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`. One setup per sleeve; the EDGAR catalyst and metadata producer (`desk/feedlib/qm_inputs.py`) is not in this repo
- **Master desk (Femto-lean)**: `sleeves/femto/qullamaggie.py`
- **Master desk (Aurelia paper engine)**: `sleeves/femto/qullamaggie_paper.py`, `sleeves/femto/vendor/aurelia_qulla/desk.py`
- **Midna v3**: `sleeves/qullamaggie.py`, `sleeves/qullamaggie_paper.py`. Wrappers only; the strategy files are not in this repo
- **Rule lines**: [docs/verify/qullamaggie.md](../../docs/verify/qullamaggie.md)
