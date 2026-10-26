# Distance pairs

Trades the 20 closest stock pairs of a 12-month formation: both legs at a 2σ spread, out at 0.5σ, stop at 4σ; V1 opens at 2.5σ only without news and holds at most 10 sessions.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed distance pairs study (Gatev SSD) and its news-filtered V1, forward-tested |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | NYSE, NASDAQ and AMEX listings |
| **Style** | Pairs |
| **Status** | 2 live |

## Entry

- Formation, each half-year: listings with bars on ≥ 240/252 of the 12 formation months' sessions, median dollar volume ≥ $1M, median price ≥ $5 and every day present after bad-tick cleaning; the 20 pairs with the smallest sum of squared distances of normalized prices.
- z = the normalized spread less its formation mean, over its formation σ, on the live prices once a day, 30-11 minutes before the close; |z| > 2 (V1: 2.5) buys the cheap leg and shorts the rich one, market-on-close.
- V1 opens only when neither leg has a news item, an earnings date or an ex-dividend date from 5 sessions back to today.

## Exit

- |z| < 0.5 (converged), market-on-close; the base book also stops at |z| beyond 4 against the trade, V1 after 10 sessions; every pair closes on the window's last session; pairs may reopen.

## Sizing

- $5,000 per pair, $2,500 a leg; whole shares on the short leg.

## Data

- Daily adjusted closes (420) of the legs; NASDAQ Trader symbol directories.
- V1: Alpaca news (Yahoo RSS headlines without keys); Nasdaq earnings and dividend calendars.

## Variants

| Book | Entry | Exit | Row |
|---|---|---|---|
| Distance pairs | spread beyond 2σ | back inside 0.5σ, a 4σ stop, or the window's end | `killed_pairs_distance_coint` |
| V1 news-filtered | spread beyond 2.5σ, no news, earnings or ex-dividend in 5 sessions | back inside 0.5σ, 10 sessions, or the window's end | `killed_pairs_news_filtered` |

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/pairs.py`, `sleeves/killed/common.py`, `sleeves/killed/feedlib/killed_data.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)

## Notes

- The 20 best Engle-Granger ADF pairs are formed and recorded, not traded.
- The base book starts each window from its replayed state (a pair already open since the window start opens at once); V1 starts flat.
- The master desk trades the short side; the old desk's long-only rail is dropped.
