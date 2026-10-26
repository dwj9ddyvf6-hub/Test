# Daily Cyan desk feed

Buys the live lab's Daily Cyan book picks, sized by market-cap band, for 21 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research lab (lab_live 1D Cyan books), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Lab panel names |
| **Style** | Tensor signal + model |
| **Status** | live |

## Entry

- Signal: a 1D Cyan full or covered lab book fire (rule search or boosted trees).
- Size class by PIT band: small = core, micro = core at 0.52×, mid/large = logged only; covered-only fires trade at test size.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 21 sessions from the fill.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $700 core small, $364 core micro, $230 test; 68 slots, $12,500; cap 5% of dv20, floor $100k.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's daily book outputs; Yahoo daily bars.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
