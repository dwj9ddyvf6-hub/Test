# Edge paper hands (10 lineages)

Ten equal sub-books, one per trading lineage, buy a watchlist stock on a clean completed-hour Tensor BUY and sell on a clean SELL, inside Sable's swing bracket and each lineage's rule.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | The Sable / Autopilot desk's Edge paper hands (scout-hands), with its ten lineage doctrines |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | AAPL, MSFT, NVDA, AMZN, JPM, XOM (SPY, QQQ, IWM, SMH as context) |
| **Style** | Signal following |
| **Status** | waiting |

## Entry

- Each completed regular-session hour, 2-11 minutes after it closes, the watchlist and held names are read.
- Buy: the hour's Tensor state is VECTOR_BUY with exactly one buy-green or buy-gold marker, for a name the sub-book does not hold.
- Gates: under 6 positions, cash for a share, the regular session, price ≤ 1.85 ATR above the 64-hour support, RSI ≤ 72, no ETF, not parked, the sub-book not parked by a 2% day loss.
- Lineage rules that act here: PTJ sizes down when its sub-book is red on the day; Druckenmiller, once holding a name, buys another only on a gold read; Minervini sells a holding at or under cost when the hour prints no buy.

## Exit

- A clean Tensor SELL (VECTOR_SELL with exactly one sell-red or sell-magenta) sells the holding.
- Bracket on each hour's close: stop at entry - 1.6 ATR, target at entry + 2.8 ATR (the hour's ATR, at least 1.5% of entry); market orders.

## Sizing

- Each sub-book is a tenth of the $100,000 book: shares = min(0.5% of equity / 1.6 ATR, 15% of equity / price, 98% of cash / price), 0.25% and 8% when sized down.

## Data

- The canonical hourly series (1 year) of the watchlist and held names, read by the v698 Tensor engine; quotes built from the same hours.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research_hands.mjs`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/autopilot/scout-hands.mjs`, `desk/vendor/foliotend_research/autopilot/lineage.mjs`

## Notes

- The Edge brief (headlines, filings, the scan) is empty here, so the lineage rules that need it never fire.
- Qullamaggie's 3% risk is recorded but not used in sizing.
- The source's break-even step at +1.6 ATR is reset by the stop floor on every pass, so it never fires.
- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
