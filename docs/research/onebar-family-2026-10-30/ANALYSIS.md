# One Bar Family: Analysis

Date: 2026-10-30. Commissioned by the owner, 2026-10-30.
Source: a screenshot the owner supplied of a post by Breakout Trading Academy, a verified X account whose handle is shown truncated as @onl... in the screenshot. The full handle is not visible in the source and is not invented here.
Edge status: UNPROVEN. The live paper record on this desk is the test. No backtest is claimed by this analysis or by the install.

## SCOPE (InfinityBlade)

Surface: three new paper sleeves (bta_onebar_qqq, bta_onebar_basket, bta_onebar_rth), their adapter pairs, three config rows, 30-minute bar producer keys and warm fetches, gate wired blocker tests, proof files, a BUGLOG entry, and this analysis.
Constraints: paper only. The Tensor engine is not touched. saty_sol is not touched. No existing sleeve changes behaviour. Commits are by explicit paths only, because the desk working tree carries other lanes' uncommitted work.
Outcome: three FED, parked false sleeves on $10,000 slices implementing the rules below, proven by the full gate from the final state.
Proof: golden, causality, cap, session and wiring blocker tests, fail first proven, plus a full gate run on the committed tree.
Edges: the desk dispatcher fills intents at the next available price after a signal evaluation, so the live entry price can differ from the modelled intrabar stop fill. The one bar holding period is preserved in live form: enter on one 30-minute bar, exit at the open of the following bar. See the translation notes.

## The mechanism in plain terms

The system is a 50-bar Donchian breakout on 30-minute bars with a one-bar time exit.

A Donchian channel is simply the highest high and the lowest low of the last N bars. Here N is 50, so the channel looks back 25 hours of 30-minute bars. A buy stop rests at the top of the channel and a sell stop rests at the bottom. If price trades up through the highest high of the last 50 bars, the buy stop fills and the sleeve is long. If price trades down through the lowest low, the sell stop fills and the sleeve is short. There is no filter, no indicator and no discretion: one condition.

The exit is time, not price. The position is held for the remainder of the entry bar only and closed at the open of the next bar. The author's stated reasoning is that a break of a 50-bar extreme shows real momentum, and holding for one bar captures the initial burst without overstaying. A fixed money stop ($1,000 per trade in the original) caps the loss if the burst fails inside that one bar.

Portability is part of the claim: the author says the identical rules, with zero changes, were profitable on E-mini NASDAQ, S&P 500, MidCap 400 and Dow Jones instruments. The basket sleeve in this family tests exactly that claim on this desk, one independent book per index ETF.

## Claim audit

| Claim in the post | Stated in source | Checkable from the post | Verdict |
| --- | --- | --- | --- |
| Market and timeframe: E-mini NASDAQ (NQ), 30-minute bars, 24-hour session | Yes | The rules text states it; no data is supplied | Accepted as the rule set to implement, not as evidence of profit |
| Direction: long and short | Yes | Rules text | Implemented both directions |
| Long entry: buy stop at the highest high of the last 50 bars | Yes | Rules text | Implemented as stated |
| Short entry: sell stop at the lowest low of the last 50 bars | Yes | Rules text | Implemented as stated |
| Exit: close on the next bar at market open | Yes | Rules text | Implemented: fill during bar T, exit at the open of bar T+1 |
| Stop loss: $1,000 per trade | Yes | Rules text states the amount; contract count is not stated | Translated to a percentage stop, arithmetic below |
| Max entries per day: 2 | Yes | Rules text | Implemented per symbol per day |
| Profitable on NQ, then on S&P 500, MidCap 400 and Dow Jones with zero changes | Claimed | No: no trades, dates, data or code are supplied | UNVERIFIED. Not checkable from the post |
| Equity curve rising to about $210,000 in the screenshot | Shown as an image | No: no axis dates, starting capital, contract count or drawdown figures can be verified from the screenshot | UNVERIFIED. The curve proves nothing on its own |
| Costs, slippage and commissions were included | Not stated | No | UNKNOWN. The post is silent, so no cost treatment can be credited to it |
| Test period and sample size | Not stated | No | UNKNOWN. Not stated in the post |
| The behaviour is real because it worked across four related markets with no re-optimization | Claimed as an inference | No: the four markets are highly correlated index products, and the underlying results are not supplied | UNVERIFIED inference. The desk forward paper record is the judge, per house practice |

Nothing in the post can be independently verified beyond the rule text itself. That is stated plainly: the rules are implementable, the profitability is not proven, and this install does not claim it.

## Translation decisions, with arithmetic

### (a) NQ futures to QQQ ETF on Alpaca paper

The desk trades ETFs on Alpaca paper, not E-mini futures. QQQ is the NASDAQ-100 ETF, the cash market counterpart of NQ. The base sleeve trades QQQ shares, long and short, on 30-minute bars. The basket sleeve trades SPY (S&P 500), QQQ (NASDAQ-100), MDY (MidCap 400) and DIA (Dow Jones Industrial Average), matching the four markets named in the post, each as its exchange traded fund.

Short sales of ETF shares on the paper account replace short futures positions. Position intent is declared exactly on every intent (buy_to_open, sell_to_open, sell_to_close, buy_to_close), per desk law.

### (b) The $1,000 stop

One NQ point is worth $20 per contract. The stop in points is:

$1,000 / $20 per point = 50 NQ points.

As a percentage of entry price, the stop depends on the index level:

50 / 20,000 = 0.0025 = 0.25 percent at an index level of 20,000.
50 / 25,000 = 0.0020 = 0.20 percent at an index level of 25,000.
50 / 30,000 = 0.00167 = 0.167 percent at an index level of 30,000.

The desk freezes the translation at the 25,000 reference level, the round level nearest the NASDAQ-100 trading range when this family was commissioned:

STOP_PCT = 0.0020, that is 0.20 percent of entry price.
Long stop = entry price x (1 - 0.0020). Short stop = entry price x (1 + 0.0020).

Worked example at a QQQ entry of $625.00 (QQQ trades at roughly one fortieth of the index, so an index near 25,000 corresponds to QQQ near $625):
Stop distance = $625.00 x 0.0020 = $1.25 per share. Long stop = $623.75.

The $10,000 slice cap is the binding sizing constraint, and it is what scales the futures risk down to desk size. One NQ contract at an index of 25,000 controls 25,000 x $20 = $500,000 of notional, and its $1,000 stop is 0.20 percent of that notional. The desk sleeve sizes to the slice as its notional cap:

qty = floor($10,000 / entry price). At $625.00, qty = 16 shares, notional = $10,000.
Modelled stop risk at that size = 16 x $1.25 = $20.00, which is 0.20 percent of the $10,000 slice, the same fraction the original risks on one contract's notional.

So the percentage is preserved exactly, the dollar risk scales with the slice, and no leverage is used. Gap risk remains: a stop is an exit rule, not a guaranteed fill price, and a bar that gaps through the stop can lose more than the modelled $20. The desk dispatcher executes the stop from the sleeve's ExitRule data.

The frozen STOP_PCT does not float with the index level. If the index level moves far from 25,000, the point equivalent of the stop drifts from 50 points in proportion. That drift is accepted and named here rather than hidden, because a floating translation would be a re-optimization the source does not describe.

### (c) The 24-hour session

NQ futures trade nearly 24 hours. Alpaca ETF bars do not. The desk warm product for these ETFs is cash session centred SIP data: the bars the desk actually has are the bars that exist for QQQ, SPY, MDY and DIA in the desk's `SYM|30Min` warm product, which is built from Alpaca SIP trades and is centred on the US cash session, including such extended hours bars as that product carries. There are no overnight futures bars in it, and the sleeve does not invent any.

Consequences, stated exactly:
Base and basket sleeves evaluate every completed 30-minute bar present in that warm product, in timestamp order, whatever session segment it belongs to. The 50-bar channel is built from the prior 50 completed bars in that same product, so the lookback spans roughly two to four cash sessions depending on how many extended hours bars the product carries, not 25 clock hours of futures trading.
The RTH variant restricts everything to regular session bars only: bar start times from 09:30 ET to before 16:00 ET. Channel, entries and exits use only those bars.
The one-bar exit at the next bar open means the next bar in the product the sleeve consumes. For the RTH variant, a position still open late in the session is closed at market at 15:55 ET instead of being held past the close (see the RTH rules in the deliverable).

This is a real translation difference from the futures original, and it is part of what the forward paper record will judge.

### (d) Max 2 entries per day

Two entries per day, counted per symbol, by the entry bar's ET calendar date. The basket sleeve therefore allows up to two entries per symbol per day, eight across its four symbols, each in its own independent book. An entry that is stopped out or that exits at the next bar open still counts. After the second entry on a symbol for a date, no further entries on that symbol that date, however strong the trigger.

### (e) The one-bar exit

Fill during bar T, exit at the open of bar T+1.

If the buy stop fills during bar T at the channel high (or at bar T's open, when the bar gaps open above the channel), the position is held for the rest of bar T only. The exit intent carries the open price of bar T+1 as its reference and closes the whole position. There is no target and no trailing rule. The only earlier exit is the protective stop.

Desk execution note: the pure core models the intrabar stop fill. In the live desk cycle, the sleeve evaluates completed bars and the dispatcher fills an entry intent at the next available price, so a live fill will generally occur near the open of bar T+1 and the corresponding live exit near the open of bar T+2. The one bar holding period is preserved; the entry price is not the modelled stop price. This lag is a property of the desk's signal and dispatch convention, shared with the other intraday installs, and it is named here so the paper record is read honestly.

Two further named choices where the source is silent or OHLC data is ambiguous:
Both stops trigger in one bar: if a single bar's range spans both the channel high and the channel low, OHLC data cannot say which stop was touched first. The sleeve takes no entry on such a bar. Guessing an order would invent information the bars do not carry.
No re-entry in the same bar after an exit: an exit bar never also becomes an entry bar for that symbol.

## The three sleeves

bta_onebar_qqq: the base translation. QQQ, 30-minute bars, all bars in the desk warm product.
bta_onebar_basket: the portability claim, tested directly. SPY, QQQ, MDY and DIA, identical rules and parameters on each symbol, independent state, independent daily caps, one position per symbol at a time.
bta_onebar_rth: the regular session variant. QQQ, channel and entries from RTH bars only, entries only during RTH, and any position open at 15:55 ET exits at market rather than holding past the close.

Full algorithms are in the deliverable, `~/workspace/your_files/onebar-family-2026-10-30.md`, and in the sleeve module docstrings, which are the frozen source of truth for the code.

## Prior work adopted

An earlier run of this build was stopped a few minutes in. Checked at the start of this run: the research notes directory for this family did not exist, and the desk repo contained no bta or onebar files in git status or in a tree search. There was no partial work to adopt. The desk working tree does carry unrelated uncommitted work from other lanes; it was left untouched, and this family's commits are by explicit paths only.
