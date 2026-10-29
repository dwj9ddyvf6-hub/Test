# InvestAndBeFree double MACD (SPY and QQQ options)

Long-premium options sleeve driven by a double MACD pair (Wilder and exponential) aligned across a 4H, daily and weekly stack: entries when the stack aligns and the dominant timeframe agrees, with a partial at +100% into a runner.

| | |
|---|---|
| **Family** | Muse |
| **Source** | InvestAndBeFree method, clean-room extraction from public material only (INVESTANDBEFREE-DMAC-SPEC-2026-10-29) |
| **Asset** | SPY and QQQ options (long premium) |
| **Timeframe** | 4H, daily, weekly stack |
| **Universe** | SPY, QQQ |
| **Style** | Multi-timeframe MACD alignment |
| **Status** | Midna's desk only |

## Entry

- Two MACDs (12/26/9) on closes on every timeframe in the stack: MACD-W with Wilder smoothing, MACD-E with standard exponential smoothing. Closed bars only.
- Alignment: both MACDs on the same side of their signal lines across the stack; dominance runs slowest to fastest, and the dominant direction must agree before entry.
- Long premium only: bullish buys calls, bearish buys puts. No spreads, no short premium.

## Exit

- Partial at +100% into a runner; runner exits on a daily MACD-E cross against or at 5 DTE.
- Premium stop 50%; spread gate 10% (recreated defaults, frozen in the desk spec).

## Sizing

- $2,000 budget per trade with a 25% slice cap (recreated default).

## Data

- Daily and weekly bars from the desk warm product; 4H aggregated in the core from closed 1-hour bars; options chain for contract selection.

## Variants

| Row | Difference from the base |
|---|---|
| investandbefree_dmac_intraday | Intraday stack 15m, 30m, 4H built from 5-minute bars; dominance 4H over 30m over 15m with the dominant equal to the 30m direction; expiry at least 5 days; flat by 15:55 ET |
| investandbefree_dmac_dailyonly | 4H layer removed: weekly and daily only |
| investandbefree_dmac_deep | Strike at least 2% in the money; expiry at least 45 days |
| investandbefree_dmac_premacd | Premium MACD exits: after 40 accrued premium samples, a premium MACD-E (12/26/9) cross against replaces the base exits |

## Code

- **Midna v3**: `sleeves/investandbefree_dmac.py`, `sleeves/investandbefree_dmac_intraday.py`, `sleeves/investandbefree_dmac_dailyonly.py`, `sleeves/investandbefree_dmac_deep.py`, `sleeves/investandbefree_dmac_premacd.py`

## Notes

- Edge unproven: an extraction is not a backtest; the live paper record is the test.
- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json rows investandbefree_dmac and its four variants, added 2026-10-29 to close the catalog diff of that date.
