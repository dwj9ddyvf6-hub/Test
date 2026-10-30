# The One-Bar Family: bta_onebar_qqq, bta_onebar_basket, bta_onebar_rth

Date: 2026-10-30. Provenance: Breakout Trading Academy X post, 2026-10-30.
Source: a post by Breakout Trading Academy (verified X account, handle shown truncated as @onl... in the screenshot supplied; the full handle is not visible and is not invented here).
Edge status: UNPROVEN. No backtest was run or is claimed. The desk's forward paper record is the judge, per house practice.
Full analysis: docs/research/onebar-family-2026-10-30/ANALYSIS.md in this repo. Desk build report: BTA-ONEBAR-BUILD.md in this repo.

## Summary

The post describes a deliberately minimal system: rest a buy stop at the highest high of the last 50 bars and a sell stop at the lowest low, on 30-minute bars. Whichever stop fills, hold for one bar only and close at the next bar's open. One money stop ($1,000 per trade on E-mini NASDAQ futures), at most two entries a day, long and short, no filters and no other rules. The author claims it was profitable on NASDAQ, then on the S&P 500, MidCap 400 and Dow Jones with zero changes.

In desk terms the entry is a 50-bar Donchian breakout: the channel is the highest high and lowest low of the prior 50 bars, and a trade through either edge is treated as real momentum whose first burst is worth one bar and no more.

This family installs that system three ways on Alpaca paper, each on its own $10,000 slice, parked false: the base translation on QQQ, a basket sleeve that runs the identical rules independently on the four index ETFs named by the portability claim, and a regular-session-only variant on QQQ.

## Claim audit

| Claim in the post | Stated in source | Checkable from the post | Verdict |
| --- | --- | --- | --- |
| Market and timeframe: E-mini NASDAQ (NQ), 30-minute bars, 24-hour session | Yes | Rules text only; no data supplied | Accepted as the rule set to implement, not as evidence of profit |
| Direction: long and short | Yes | Rules text | Implemented both directions |
| Long entry: buy stop at the highest high of the last 50 bars | Yes | Rules text | Implemented as stated |
| Short entry: sell stop at the lowest low of the last 50 bars | Yes | Rules text | Implemented as stated |
| Exit: close on the next bar at market open | Yes | Rules text | Implemented: fill during bar T, exit at the open of bar T+1 |
| Stop loss: $1,000 per trade | Yes | Amount stated; contract count not stated | Translated to a percentage stop (table below) |
| Max entries per day: 2 | Yes | Rules text | Implemented per symbol per day |
| Profitable on all four markets with zero changes | Claimed | No trades, dates, data or code supplied | UNVERIFIED. Not checkable from the post |
| Equity curve rising to about $210,000 | Shown as an image | No dates, starting capital, contract count or drawdown can be verified from the screenshot | UNVERIFIED. The curve proves nothing on its own |
| Costs, slippage, commissions included | Not stated | No | UNKNOWN. The post is silent |
| Test period and sample size | Not stated | No | UNKNOWN. Not stated in the post |
| Cross-market success with no re-optimization proves the behaviour is real | Claimed as an inference | The four markets are highly correlated index products and the underlying results are not supplied | UNVERIFIED inference. The forward paper record decides |

Plainly: the rules are implementable, the profitability is not verifiable from the post, and nothing in this install treats it as proven.

## Translation table

| Original (futures) | Desk translation | Arithmetic and notes |
| --- | --- | --- |
| E-mini NASDAQ (NQ) | QQQ shares on Alpaca paper | Base and RTH sleeves. QQQ is the NASDAQ-100 ETF, the cash counterpart of NQ |
| S&P 500, MidCap 400, Dow Jones instruments | SPY, MDY, DIA shares | Basket sleeve, with QQQ as its NASDAQ leg |
| 30-minute bars, 24-hour futures session | 30-minute bars from the desk warm product (Alpaca SIP) | That product is cash session centred. It carries no overnight futures bars and none are invented. The channel is built from the prior 50 completed bars in that product. The RTH variant uses only bars starting 09:30 to before 16:00 ET |
| $1,000 stop per trade | Stop 0.20 percent from entry | 1 NQ point = $20, so $1,000 / $20 = 50 points. 50 / 25,000 (frozen reference index level) = 0.0020 = 0.20 percent. Long stop = entry x 0.998; short stop = entry x 1.002. At a $625.00 QQQ entry the stop distance is $1.25 per share |
| One contract (about $500,000 notional at an index of 25,000) | qty = floor($10,000 / entry price) | The $10,000 slice is the notional cap and the binding sizing constraint. At $625.00, qty = 16 shares, notional $10,000, modelled stop risk 16 x $1.25 = $20.00, which is 0.20 percent of the slice, the same fraction the original risks on one contract's notional. No leverage |
| Max 2 entries per day | Max 2 entries per day per symbol | Counted by the entry bar's ET date. The basket can therefore take up to 8 entries a day, 2 per symbol |
| Exit at next bar open | Exit intent at the open of the bar after the entry bar | Fill during bar T, exit at the open of bar T+1. Desk note: the live dispatcher fills intents at the next available price after a bar completes, so live entries generally land near the following open and exits near the open after that; the one bar holding period is preserved |

Named choices where the source is silent or the bars are ambiguous: if a single bar spans both channel extremes, no entry is taken, because OHLC data cannot say which stop touched first. A position that exits never re-enters in the same bar. A stop is an exit rule, not a guaranteed fill: a gap through the stop can lose more than the modelled amount.

## Algorithm 1: bta_onebar_qqq (base)

Instrument: QQQ shares, long and short. Timeframe: 30-minute bars, completed bars only, every bar in the desk warm product for QQQ. Slice: $10,000. Cadence: 60 seconds. Parked: false. Paper only.

1. Channel. At each evaluation, take the prior 50 completed bars before the latest completed bar. Channel high = their highest high. Channel low = their lowest low. Fewer than 51 completed bars in total: no action.
2. Entries. If the latest completed bar's high is at or above the channel high, a long entry fills at the channel high, or at that bar's open if the bar opened above the channel high. If the latest bar's low is at or below the channel low, a short entry fills at the channel low, or at that bar's open if it opened below it. If the bar spans both extremes, no entry. One position at a time. An entry is counted on the entry bar's ET date; at most 2 entries per day, and entries are only taken on the current session's bars.
3. Size. qty = floor(slice equity / entry price), whole shares. If the live snapshot carries no slice, the configured $10,000 slice is used.
4. Protective stop. Long: entry x 0.998. Short: entry x 1.002. Declared as an ExitRule on the entry intent and executed by the dispatcher. No target, no trailing rule.
5. Time exit. A position entered on bar T exits in full at the open of bar T+1, at market, with the closing position intent (sell_to_close for a long, buy_to_close for a short). No re-entry in the same bar as an exit.

## Algorithm 2: bta_onebar_basket (the portability claim)

Instruments: SPY, QQQ, MDY, DIA shares, long and short. Everything else identical to Algorithm 1, applied independently to each symbol: its own 50-bar channel from its own bars, its own position (one at a time per symbol, so up to four positions at once across the basket), its own stop at 0.20 percent, its own size from the same $10,000 sleeve slice cap formula per entry, and its own counter of at most 2 entries per day per symbol. No symbol's state, cap or position affects any other symbol. Slice: $10,000 for the sleeve. Cadence: 60 seconds. Parked: false. Paper only.

## Algorithm 3: bta_onebar_rth (regular session only)

Instrument: QQQ shares, long and short. Slice: $10,000. Cadence: 60 seconds. Parked: false. Paper only. Identical to Algorithm 1 with three session restrictions:

1. RTH bars only. The channel and all entry decisions are computed only on bars whose start time is from 09:30 ET to before 16:00 ET. Premarket and after-hours bars in the warm product are ignored entirely.
2. Entries only during RTH, which follows from the bar filter: no bar outside the session can trigger an entry.
3. 15:55 ET flat. Any position still open at 15:55 ET exits at market at that time, instead of the next-bar-open exit carrying it past the close. This flat is the sleeve's own rule (config flat_by_close stays false), so there is exactly one flatten path.

## Install State

Desk commits: a7a229c (the family: cores, adapters, config rows, producer keys, warm fetches, blockers, proofs, BUGLOG) and 80fe2bc (build report and proof hash correction), in repo muse-desk-v3.
Roster: 336 sleeves (was 333). Config rows as committed, all with slice capital_usd 10000.0 and cash_usd 10000.0, cadence_s 60, session rth, flat_by_close false:
bta_onebar_qqq: module adapters3.bta_onebar_qqq, parked false, inputs bars, bars_30min, bars:QQQ:30Min, positions, quotes, session_fills.
bta_onebar_basket: module adapters3.bta_onebar_basket, parked false, inputs bars, bars_30min, bars:SPY:30Min, bars:QQQ:30Min, bars:MDY:30Min, bars:DIA:30Min, positions, quotes, session_fills.
bta_onebar_rth: module adapters3.bta_onebar_rth, parked false, inputs bars, bars_30min, bars:QQQ:30Min, positions, quotes, session_fills.
Gate: family blockers 24/24 pass (tests/test_bta_onebar_blockers.py, gate wired by the discover pattern). Full gate on the working tree: 1502 tests, 2 failures, both pre-existing and outside this family (the untracked przm lane's own roster pin still reads 333, and a dmac test that reads the live on-disk warm product, which currently carries no daily keys; both named in BUGLOG_2026-10-30.md and BTA-ONEBAR-BUILD.md). On a clean worktree of the family commit: 1426 tests, 0 failures, with 24 errors confined to one external-oracle test class whose script path does not resolve outside the main tree.
BUGLOG: BTA-ONEBAR-UNFED-20261030 in desk BUGLOG_2026-10-30.md (the missing 30-minute feed class, cured at the source in this install), plus two investigated-and-cleared notes.
FED status: producer keys and warm fetches are registered in code and proven in a fresh process (a BarsProjection drive on a fixture warm map returns all four 30Min keys). Config rows activate by per-cycle reload. Live feeding is NOT yet proven: the live runner predates the new desk3 code, so all three sleeves are UNFED-live until a desk-ops runner restart. OPEN item, named exactly: restart the desk runner (after the 16:00 ET close), then prove on the first live cycle that bars:QQQ:30Min, bars:SPY:30Min, bars:MDY:30Min and bars:DIA:30Min are produced and that bta_onebar_qqq, bta_onebar_basket and bta_onebar_rth evaluate as FED. Prior installs (dmac variants, finding F2) left the same step to desk-ops in the same way.
Prior work: an earlier stopped run of this build left nothing behind (no research notes directory, no bta or onebar files in the tree or in git status), so there was no partial work to adopt.

Save and notification proof is recorded in the local deliverable for this family.
