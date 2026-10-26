# Bilbo Box calls

When an hourly squeeze box (Saty Phase compression) closes out above its high, buys a call about 0.75 ATR out of the money, 21-37 days out.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Milkman (milkmantrades.com) Bilbo Box v2 with Saty's Phase Oscillator; the old swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1h (5-minute exits) |
| **Universe** | 20 large caps |
| **Style** | Volatility breakout (options) |
| **Status** | live |

## Entry

- Box: hourly bars with extended hours in Saty Phase compression (Bollinger inside Keltner); its high and low widen over the first 5 grey bars; live for 10 days.
- Trigger: the first hourly bar out of compression closes above the box high, closing 10:00-15:00 ET on a weekday, with spot above the daily 21 EMA.
- Contract: the nearest expiry 21-37 days out, the strike nearest spot + 0.75 × the prior day's ATR(14); spread ≤ 5% of mid; a limit at the mid, cancelled after 60 minutes; at most 5 open.
- Scans hourly at :22 (10:22-15:22 ET) on bars closed ≥ 20 minutes.

## Exit

- On 5-minute regular-hours bars: a close under the box low; or, once the stock has run 1.25 ATR, a close at or below entry + 25% of the peak gain; or 10 trading days after entry.
- Sold at ≤ 5 days to expiry regardless; exits are limits at the mid, re-priced each pass.

## Sizing

- 4% of the book in premium a trade, at least 1 contract.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Yahoo 5-minute bars (60 days), the desk's call chains (0-60 DTE) and option quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/bilbo_options.py`, `desk/vendor/old_desk_research/bilbo_options_signals.py`
- **Midna v3**: `sleeves/bilbo_options.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): expiries 15-21 days out.
