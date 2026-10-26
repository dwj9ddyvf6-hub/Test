# Verification: Ausar

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [R19 crypto breakout and negative-funding squeeze](../../strategies/ausar/r19-crypto-breakout.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a completed UTC 4h close above the highest high of the prior 20 bars. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:120-129` |
| Entry: Squeeze books also need the latest known funding settlement to be negative: settled in or before the signal bar, received before the decision, at most 12 h before the bar's close. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:66-80`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:126-133` |
| Entry: Buys 4 h after the signal bar closes, inside a 5-minute window, on a fresh quote: spread ≤ 100 bps and last trade ≤ 60 s old. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:272-286`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:300-308`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:40-56` |
| Entry: Long only, one position per book, and only signals after the book's activation. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:166-170`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:272-282` |
| Exit: fixed16 / fixed96: sells 16 h or 96 h after the entry time. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:285`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:216-219` |
| Exit: Structural exits on a completed bar after entry. normalization: funding ≥ 0. normalization_failure: funding ≥ 0 and the close is below the prior 3 bars' lowest low. lost_breakout: the close is below the breakout level. Each sells from the next bar, with the 96 h deadline as the backstop. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:187-213`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:285` |
| Exit: No stop. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:173-221` |
| Sizing: fullcash: all book cash at the ask, net of the 10 bps fee. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:313-317`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:52` |
| Sizing: volume1pct: capped at 1% of the volume of the 4h bar that completes at entry. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:309-319` |
| Sizing: Floored to the venue lot; the buy fills slice by slice through the displayed depth. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:320-324`<br>master-desk `desk/sleeves/families/r19_crypto.py:226-262` |
| Data: Binance spot 4h klines (340), depth and last trade; Binance USD-M funding history. US hosts get HTTP 451 there, so the master desk relays the rate from CoinGecko. | master-desk `desk/sleeves/families/r19_crypto.py:79-123` |
| Midna v3: entry on the latest completed bar; volume cap from the bar before it; deadlines from the fill | `desk3/aster_crypto.py:116-119`<br>`desk3/aster_crypto.py:145-156` |
| Book grid: 3 coins × families × exit policies × 2 capacity arms | master-desk `desk/vendor/strategies/r19/crypto_rules.json:2-32`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:40-56` |

## [Crypto confirmed absorption (4h)](../../strategies/ausar/crypto-absorption.md)

| Rule | Read from |
|---|---|
| Entry: Shock bar: volume > 2 × EMA20(volume), close < open, close < EMA50(close). The EMAs include the bar and seed at the first bar. | master-desk `desk/vendor/ausar_ctx/strategies/absorption/signals.py:36-50`<br>master-desk `desk/sleeves/families/r19_crypto.py:45-60` |
| Entry: Confirmation: the next bar closes above its open and above the shock bar's (high + low) / 2, after at least 300 completed bars. | master-desk `desk/vendor/ausar_ctx/strategies/absorption/signals.py:48`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:131`<br>master-desk `desk/sleeves/families/absorption.py:277-282` |
| Entry: R19 books: optional funding filter (none, negative, non-negative) and entry 4 h after the confirmation bar closes, in a 5-minute window. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:126-135`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:272-286` |
| Entry: Original books (ENJ, LINK): buy at the ask within 300 s of the confirmation bar's close. | master-desk `desk/sleeves/families/absorption.py:277-288`<br>master-desk `desk/sleeves/families/absorption.py:385-395` |
| Exit: R19 books: sell 16 h after the entry time. | master-desk `desk/vendor/ausar_r19/r19_crypto.py:285`<br>master-desk `desk/vendor/ausar_r19/r19_crypto.py:216-219` |
| Exit: Original books: sell at the bid from 16 h after the confirmation bar's close. | master-desk `desk/sleeves/families/absorption.py:75`<br>master-desk `desk/sleeves/families/absorption.py:286-288`<br>master-desk `desk/sleeves/families/absorption.py:353-356` |
| Exit: No stop, no pyramiding. | master-desk `desk/sleeves/families/absorption.py:385-392` |
| Sizing: R19 books: `fullcash` (all cash, net of 10 bps) or `volume1pct` (≤ 1% of the entry bar's volume). | master-desk `desk/vendor/ausar_r19/r19_crypto.py:313-319` |
| Sizing: Original books: 100% of book cash including the 10 bps fee, floored to the lot, capped by the displayed ask size. | master-desk `desk/sleeves/families/absorption.py:415-423` |
| Data: Binance spot 4h klines, book ticker and last trade; funding for the filtered R19 books. | master-desk `desk/sleeves/families/r19_crypto.py:79-123`<br>master-desk `desk/sleeves/families/absorption.py:144-181` |
| Midna v3 absorption test and catch-up | `desk3/aster_crypto.py:103-109`<br>`desk3/aster_batch1.py:746-880` |

## [R19 ETF books: momentum leader rotation](../../strategies/ausar/r19-etf.md)

| Rule | Read from |
|---|---|
| Entry: Score: log(close / close 126 sessions earlier) on total-return closes. A fund needs 252 sessions of history to be eligible. | master-desk `desk/vendor/ausar_r19/r19_etf.py:135-173` |
| Entry: LEADER1 holds the top score. EXSMH1 excludes SMH. CORE25 holds 25% leader and 75% QQQ. DRIFT1 keeps the incumbent's shares when it leads again. | master-desk `desk/vendor/ausar_r19/r19_etf.py:70-77`<br>master-desk `desk/vendor/ausar_r19/r19_etf.py:295-301`<br>master-desk `desk/vendor/ausar_r19/r19_etf.py:317-318` |
| Entry: INTERVAL policies score on Alpaca and Yahoo. They take the fund whose lower score beats every other fund's upper score, else the incumbent if it can still lead, else QQQ. | master-desk `desk/vendor/ausar_r19/r19_etf.py:78-86` |
| Entry: Trades 09:35-09:40 ET on the month's first session, on the prior month's last close, retrying for up to 5 sessions. | master-desk `desk/vendor/ausar_r19/r19_etf.py:88-117`<br>master-desk `desk/vendor/strategies/r19/etf_rules.json:156-157` |
| Exit: Each month sells what left the target before it buys. Buy-and-hold books never sell. No stops. | master-desk `desk/vendor/ausar_r19/r19_etf.py:274-276`<br>master-desk `desk/vendor/ausar_r19/r19_etf.py:346-350` |
| Sizing: Target shares = floor(weight × gross × NAV / ask). Gross is 0.98 in cash (C098), 1.5 on margin with a 10%/yr debit (M150), or 1.0 (C100). | master-desk `desk/vendor/ausar_r19/r19_etf.py:318`<br>master-desk `desk/vendor/strategies/r19/etf_rules.json:144-152`<br>master-desk `desk/vendor/strategies/r19/etf_rules.json:193-197` |
| Sizing: Buys wait for settled cash and the displayed ask size; 15 bps per side. | master-desk `desk/vendor/ausar_r19/r19_etf.py:351-371`<br>master-desk `desk/vendor/strategies/r19/etf_rules.json:152` |
| Data: Daily total-return closes (Alpaca; Yahoo too for INTERVAL); IEX quotes. | master-desk `desk/vendor/ausar_r19/r19_etf.py:135-150` |
| Midna v3: last-close sizing, same-session catch-up, volatility rank | `desk3/aster_etf.py:51-75`<br>`desk3/aster_etf.py:113-157`<br>`sleeves/free_etf.py:124-152` |

## [R19 weekly Tensor G4 green ownership](../../strategies/ausar/r19-tensor-g4.md)

| Rule | Read from |
|---|---|
| Entry: Weekly buy-green primary marker, close ≤ $10, 60-week drawdown depth ≥ 70%, 60-session return ≥ 0, weekly volatility ≥ 0.09, 20-day dollar volume ≥ $2M. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:242-257` |
| Entry: cool / hot cuts: ATR20/ATR60 ≤ 1 or > 1; all takes both. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:257` |
| Entry: Buys at the open after the signal week (one session later in delay and reserve modes); red_timeout waits up to 5 sessions for a QQQ red day with the stock ≤ 1.02 × signal close. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:145-148`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:357`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:360-386` |
| Entry: Needs ≥ 99% census and feature coverage; ranks by 20-day dollar volume; one position per issuer. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:300`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:338`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:350-353` |
| Exit: Sells 5 minutes before the close of the last session of the 52nd calendar week. No stop, no target. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:150-157`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:293-297`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:359` |
| Sizing: Ticket = $100,000 / slots (25 or 10 slots), whole shares, fees 30 / 15 / 10 bps by price. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:54`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:72`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:388` |
| Sizing: reserve mode parks idle cash in QQQ weekly and sells it to fund tickets. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:396-424` |
| Data: Raw SIP daily bars built into weekly bars, the archived Galath v615 Tensor engine (Node). | master-desk `desk/vendor/ausar_r19/r19_tensor.py:73`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:242-252` |
| Midna v3: v698 fires, $400 ticket, 260-session hold | `desk3/aster_batch14.py:1-35`<br>`desk3/aster_batch14.py:84-96` |

## [R19 weekly Tensor C1 cyan ownership](../../strategies/ausar/r19-tensor-c1.md)

| Rule | Read from |
|---|---|
| Entry: Weekly buy-cyan primary marker, close ≤ $5, 60-session return ≥ 31%, weekly volatility ≥ 0.07, 20-day dollar volume ≥ $2M. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:254-257` |
| Entry: cool / hot cuts: ATR20/ATR60 ≤ 1 or > 1; all takes both. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:257` |
| Entry: Buys at the open after the signal week, one session later in delay and reserve modes. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:145-148`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:357` |
| Exit: Sells 5 minutes before the close of the 52nd calendar week. No stop, no target. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:150-157`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:293-297` |
| Sizing: Ticket = $100,000 / 25 slots, whole shares; reserve mode funds tickets from a QQQ reserve. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:72`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:388`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:396-424` |
| Data: Raw SIP daily and weekly bars; archived Galath v615 Tensor engine. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:73` |
| Midna v3 C1 rule | `desk3/aster_batch13.py:1-37` |

## [R19 weekly Tensor beta M2 52-week cohort](../../strategies/ausar/r19-tensor-beta-m2.md)

| Rule | Read from |
|---|---|
| Entry: M2 label: weekly dollar volume ≥ $10M, relative volume 0.8-2, bullish votes ≥ bearish + 2, consensus buy; then a buy-green (13-week return ≥ 0) or buy-cyan print. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:259-269` |
| Entry: Beaten down (close ≤ 80% of the 52-week high, or 13-week return ≤ -20%) and 52-week beta to SPY > 1.2. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:270-276`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:745-751` |
| Entry: Takes only the bottom third of that week's qualifiers by 52-week dollar volume. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:745-751` |
| Exit: Sells at the close of the 52nd calendar week. No stop. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:150-157`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:293-297` |
| Sizing: Ticket = $100,000 / 25 slots, whole shares. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:63`<br>master-desk `desk/vendor/ausar_r19/r19_tensor.py:388` |
| Data: 200+ weekly bars per name, SPY weekly bars, the v625 Tensor engine. | master-desk `desk/vendor/ausar_r19/r19_tensor.py:259-261` |
| Midna v3 BETA row | `desk3/aster_batch13.py:27` |

## [R19 10-minute EMA cloud reclaim](../../strategies/ausar/r19-timing-cloud.md)

| Rule | Read from |
|---|---|
| Entry: Hourly bias: EMA34 > EMA50 on each of the last 3 hourly closes. | master-desk `desk/vendor/ausar_r19/r19_timing.py:158-160` |
| Entry: A 10-minute bar dips into the EMA 5/12 cloud after a bar fully above it; within 3 bars and no deeper than 0.5 ATR below the cloud, a bar closes back above it with the EMA spread widening. | master-desk `desk/vendor/ausar_r19/r19_timing.py:161-172` |
| Entry: Enters 09:50-15:30 ET only if the target (prior session high) is at least 2× the risk. | master-desk `desk/vendor/ausar_r19/r19_timing.py:237`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:265` |
| Exit: Stop at the dip's low - 0.1 ATR; target the prior session high; time exit after 100 minutes, by 15:50 ET at the latest. | master-desk `desk/vendor/ausar_r19/r19_timing.py:172`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:204-206`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:269-272` |
| Sizing: min(10% or 20% of $100,000 notional, cash) and a 0.25% or 0.5% risk budget over the stop; 8 slots. | master-desk `desk/vendor/ausar_r19/r19_timing.py:69`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:74`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:266-267` |
| Data: IEX 10-minute and hourly regular-session bars; prior daily high. | master-desk `desk/vendor/ausar_r19/r19_timing.py:36-43` |
| Midna v3 cloud rows | `desk3/aster_batch15.py:54-59` |

## [R19 hourly confirmed swing](../../strategies/ausar/r19-timing-hourly.md)

| Rule | Read from |
|---|---|
| Entry: v625 engine swing: confirmed, score ≥ 8, no bearish conflict, stop < close < target. | master-desk `desk/vendor/ausar_r19/r19_timing.py:144-150` |
| Entry: A TRANSITION phenotype is skipped when the bar's body > 0.5 ATR or its range > 1.5 ATR. | master-desk `desk/vendor/ausar_r19/r19_timing.py:152` |
| Entry: delay1 waits one bar and drops the signal if that bar touches the stop or target. | master-desk `desk/vendor/ausar_r19/r19_timing.py:145`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:154` |
| Exit: Stop (floor1 widens it to at least 1 ATR below entry), the engine's target, or 20 hourly bars. | master-desk `desk/vendor/ausar_r19/r19_timing.py:155-156`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:204-210` |
| Sizing: min(10% of $100,000, cash) and a 0.25% risk budget over the stop; 8 slots. | master-desk `desk/vendor/ausar_r19/r19_timing.py:74`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:266-267` |
| Data: IEX hourly bars (60+), the v625 Tensor engine. | master-desk `desk/vendor/ausar_r19/r19_timing.py:26-35` |
| Midna v3 hourly rows | `desk3/aster_batch15.py:1-20`<br>`desk3/aster_batch15.py:60-71` |

## [R19 causal overnight hold](../../strategies/ausar/r19-timing-overnight.md)

| Rule | Read from |
|---|---|
| Entry: The 13:00-15:00 ET return (closes of the 12:30 and 14:30 half-hour bars) ≥ the 80th percentile of the last 252 full sessions (at least 126). | master-desk `desk/vendor/ausar_r19/r19_timing.py:175-191` |
| Entry: Buys 15:30-15:35 ET on full-length sessions. | master-desk `desk/vendor/ausar_r19/r19_timing.py:176-177`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:238` |
| Exit: Sells at the next session's open. | master-desk `desk/vendor/ausar_r19/r19_timing.py:193-194`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:206` |
| Sizing: min(10% of $100,000, cash), whole shares; 8 slots. | master-desk `desk/vendor/ausar_r19/r19_timing.py:74`<br>master-desk `desk/vendor/ausar_r19/r19_timing.py:266` |
| Data: IEX 30-minute regular-session bars. | master-desk `desk/vendor/ausar_r19/r19_timing.py:44-46` |
| Book grid | master-desk `desk/vendor/ausar_r19/r19_timing.py:64-71` |

## [Index-ETF recovery options (RSI2 / VWAP20)](../../strategies/ausar/opt-recovery.md)

| Rule | Read from |
|---|---|
| Entry: Close > SMA200 and either RSI(2) < 10 (RSI2 books) or close ≤ 0.98 × the 20-day typical-price VWAP (VWAP20 books), on the prior session. | master-desk `desk/vendor/ausar_r19/r19_options.py:389-416`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:878-886` |
| Entry: Enters 09:35-09:40 ET on the first passing symbol in IWM, QQQ, SPY order; one package at a time. | master-desk `desk/vendor/ausar_r19/r19_options.py:855-857`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:877-890` |
| Entry: Call with 14-21 days to expiry and delta 0.50-0.60; vertical books sell the strike nearest spot × 1.02. | master-desk `desk/vendor/ausar_r19/r19_options.py:471-512`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:11-55` |
| Exit: Planned exit on the 5th session counting the entry day, 5 minutes before the close; pre-expiry exit the session before expiry. | master-desk `desk/vendor/ausar_r19/r19_options.py:578-596`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:741-755` |
| Exit: touch books also exit when the underlying bid reaches entry spot × 1.02. | master-desk `desk/vendor/ausar_r19/r19_options.py:617-623` |
| Sizing: Risk = min(NAV × 2% (A) or 0.5% (B), 5% of capital minus open risk, cash) / package debit, capped by displayed size. | master-desk `desk/vendor/ausar_r19/r19_options.py:516-534` |
| Sizing: Debit caps: vertical ≤ 60% / 45% of width; long ≤ 2.5% / 1.5% of spot. | master-desk `desk/vendor/ausar_r19/r19_options.py:522-525` |
| Data: SIP daily bars (200 sessions), OPRA option quotes and greeks. | master-desk `desk/vendor/ausar_r19/r19_options.py:389-404`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:486-490` |
| Midna v3 book table | `desk3/aster_b2.py:30-39`<br>`desk3/aster_batch3.py:135-165` |

## [QQQ 95% core with RSI2 options](../../strategies/ausar/opt-qqq95-rsi2.md)

| Rule | Read from |
|---|---|
| Entry: Buys the QQQ core once: 95% of initial capital at the ask. | master-desk `desk/vendor/ausar_r19/r19_options.py:860-874` |
| Entry: Overlay: the RSI2 recovery signal (close > SMA200, RSI(2) < 10), 09:35-09:40 ET, 14-21 DTE calls of delta 0.50-0.60. | master-desk `desk/vendor/ausar_r19/r19_options.py:877-890`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:1095-1140` |
| Exit: Overlay: exit on the 5th session counting the entry day, or on a 2% touch of the underlying; the core is held. | master-desk `desk/vendor/ausar_r19/r19_options.py:578-596`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:617-623` |
| Sizing: Overlay risk 0.5% of NAV, within the 5% premium reserve. | master-desk `desk/vendor/ausar_r19/r19_options.py:530`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:1095-1140` |
| Data: SIP daily bars, OPRA quotes. | master-desk `desk/vendor/ausar_r19/r19_options.py:389-404` |
| Midna v3 rows | `desk3/aster_b2.py:34-35` |

## [Earnings-drift (PEAD) put options](../../strategies/ausar/opt-pead.md)

| Rule | Read from |
|---|---|
| Entry: Surprise = the stock's return minus SPY's from the session before to the session after the event. | master-desk `desk/vendor/ausar_r19/r19_options.py:424-454` |
| Entry: Trades when the surprise is at or below the 20th percentile of at least 200 prior events (prior four quarters), price ≥ $5, 20-day dollar volume ≥ $1M. | master-desk `desk/vendor/ausar_r19/r19_options.py:456-469` |
| Entry: Enters on event day + 3 sessions, 09:35-09:40 ET: puts with 21-35 DTE, delta 0.50-0.65; verticals sell the strike nearest spot × 0.95. | master-desk `desk/vendor/ausar_r19/r19_options.py:454`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:894-911`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:500` |
| Exit: Planned exit on the 10th session counting the entry day; pre-expiry exit the session before expiry. | master-desk `desk/vendor/ausar_r19/r19_options.py:578-596`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:766-800` |
| Sizing: Risk = min(NAV × 2% (A) or 0.5% (B), the 5% reserve, cash) / package debit. | master-desk `desk/vendor/ausar_r19/r19_options.py:516-534` |
| Data: Earnings calendar with first-publication times; SIP daily bars of the stock and SPY. | master-desk `desk/vendor/ausar_r19/r19_options.py:424-447`<br>master-desk `desk/sleeves/families/ausar_options.py:485-512` |
| Midna v3 buys puts | `desk3/aster_b2.py:326` |

## [XSP weekly put credit spread](../../strategies/ausar/opt-xsp-pcs.md)

| Rule | Read from |
|---|---|
| Entry: First session of the week, 10:00-10:05 ET. | master-desk `desk/vendor/ausar_r19/r19_options.py:671-676` |
| Entry: Regime: the current-week digital put price (from two adjacent puts) must be below the 75th percentile of the last 52 weeks; the calm books also need it below the median. | master-desk `desk/vendor/ausar_r19/r19_options.py:650-669`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:690-703` |
| Entry: Short strike near prior close - ATR14(weekly) × 1.0 (calm regime) or × 1.236; the long strike 5 points lower (calm) or at 1.618 / 1.786 ATR (graded). | master-desk `desk/vendor/ausar_r19/r19_options.py:704-720` |
| Exit: Held to the weekly PM expiry and cash-settled. | master-desk `desk/vendor/ausar_r19/r19_options.py:573-576`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:736` |
| Exit: Femto variant: no regime filter; short = prior weekly close - 1 × weekly ATR(14), long 5 points lower, this week's last expiry, credit > 0; held to settlement; a loss of 90% of the wing pauses entries 4 weeks. | master-desk `desk/sleeves/femto/spx_premium.py:39-50`<br>master-desk `desk/sleeves/femto/spx_premium.py:88-140`<br>master-desk `desk/sleeves/femto/spx_premium.py:196-253`<br>master-desk `desk/sleeves/femto/spx_premium.py:299-310` |
| Sizing: Contracts = min(NAV × 3% (A) or 1% (B) / max loss, cash / width, displayed sizes). | master-desk `desk/vendor/ausar_r19/r19_options.py:722-733` |
| Sizing: Femto variant: 1 lot, only with book equity ≥ $37,000. | master-desk `desk/sleeves/femto/spx_premium.py:42-43`<br>master-desk `desk/sleeves/femto/spx_premium.py:219` |
| Data: XSP weekly index bars, OPRA XSP put chain and quotes. | master-desk `desk/vendor/ausar_r19/r19_options.py:633-649` |
| Data: Femto variant: S&P 500 daily sessions / 10 (Yahoo), the desk's 0-7 DTE XSP put chain. | master-desk `desk/sleeves/families/femto_specs.py:617-629` |
| Midna v3 XSP rows | `desk3/aster_b4.py:63-66` |
| Credit: Milkman Trades' spec | master-desk `desk/sleeves/femto/spx_premium.py:3` |
| Midna v3 spx_premium change | `sleeves/spx_premium.py:40-50`<br>`sleeves/spx_premium.py:361-378` |

## [Opening gamma puts](../../strategies/ausar/opt-opening-gamma.md)

| Rule | Read from |
|---|---|
| Entry: Prior afternoon: the last-two-hours return ≥ the 80th percentile of its trailing 252 sessions (at least 126). | master-desk `desk/sleeves/families/ausar_options.py:389-391`<br>master-desk `desk/sleeves/families/ausar_options.py:431-449` |
| Entry: Today: the first 5-minute bar closes down and price breaks below its low; buys 09:35-09:45 ET. | master-desk `desk/vendor/ausar_r19/r19_options.py:933-937`<br>master-desk `desk/vendor/ausar_r19/r19_options.py:855-857`<br>master-desk `desk/sleeves/families/ausar_options.py:481-482` |
| Entry: Puts, delta 0.50-0.65: A 0-2 DTE, B 7-14 DTE. | master-desk `desk/vendor/strategies/r19/options_rules.json:1029-1061` |
| Exit: Sells at 10:00 ET the same day. | master-desk `desk/vendor/ausar_r19/r19_options.py:612-614` |
| Sizing: Risk 2% (A) or 0.5% (B) of NAV / debit; premium ≤ 2.5% / 1.5% of spot. | master-desk `desk/vendor/ausar_r19/r19_options.py:516-534`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:1029-1061` |
| Data: 30-minute bars for the R5 statistic; the first 5-minute bar; OPRA quotes. | master-desk `desk/sleeves/families/ausar_options.py:404-430` |
| Midna v3 gamma rule and 10:00 exit | `desk3/aster_batch1.py:1095-1118`<br>`desk3/aster_batch1.py:1188-1196` |

## [Tensor LEAPS calls](../../strategies/ausar/opt-tensor-leaps.md)

| Rule | Read from |
|---|---|
| Entry: On a qualified G4 event's entry session: calls with 540-720 DTE, delta 0.60-0.80. | master-desk `desk/vendor/ausar_r19/r19_options.py:912-929`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:1062-1094` |
| Exit: Exits at the G4 trade's saved 52-week deadline or its state exit. | master-desk `desk/vendor/ausar_r19/r19_options.py:606-613` |
| Sizing: Risk 2% (A) or 0.5% (B) of NAV / debit; premium ≤ 50% of spot. | master-desk `desk/vendor/ausar_r19/r19_options.py:516-534`<br>master-desk `desk/vendor/strategies/r19/options_rules.json:1062-1094` |
| Data: The R19 G4 event bridge; OPRA quotes. | master-desk `desk/sleeves/families/ausar_options.py:523-540` |
| Midna v3 leaps rows | `desk3/aster_batch3.py:147-152` |

## [RSI(2) pullback](../../strategies/ausar/public-rsi2.md)

| Rule | Read from |
|---|---|
| Entry: ETFs: Wilder RSI(2) ≤ 5, close > SMA200 and close < SMA5 on the completed day; lowest RSI(2) first; the next open within 300 s; at most 10 names. | master-desk `desk/vendor/ausar/trader_signals.py:26-37`<br>master-desk `desk/vendor/ausar/trader_signals.py:51-62`<br>master-desk `desk/vendor/ausar/trader_signals.py:279-287`<br>master-desk `desk/sleeves/families/ausar_public.py:86-106` |
| Entry: Basket: RSI(2) < 10 and close > SMA200; checked hourly at :03; at most 8 positions. | master-desk `desk/sleeves/femto/rsi_meanrev.py:24-34`<br>master-desk `desk/sleeves/femto/rsi_meanrev.py:141-150`<br>master-desk `desk/sleeves/families/femto_specs.py:71-81` |
| Entry: ADA 1h: RSI(2) < 10, close > SMA200 and the 4-bar average of RSI(2) < 30; a target is good for 300 s after its bar completes. | `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:18`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:87-90`<br>`sleeves/ausar/ausar_spot_recipes.py:338-349` |
| Exit: Close > SMA5 everywhere. ETFs: or 10 holding bars, no stop. ADA: the source's 10% stop is off. | master-desk `desk/vendor/ausar/trader_signals.py:55-60`<br>master-desk `desk/vendor/ausar/trader_signals.py:285`<br>master-desk `desk/sleeves/families/ausar_public.py:97`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:18`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:90`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:214-225` |
| Exit: Basket: also RSI(2) > 70, +5%, -8% or 5 sessions, and an 8% stop from the fill. | master-desk `desk/sleeves/femto/rsi_meanrev.py:26-29`<br>master-desk `desk/sleeves/femto/rsi_meanrev.py:118-137`<br>master-desk `desk/sleeves/families/femto_specs.py:79-80` |
| Sizing: ETFs: floor(min(10% of equity, 1% of 20-day dollar volume, cash) / (ask × 1.001)). | master-desk `desk/sleeves/families/ausar_public.py:95-96` |
| Sizing: Basket: 0.25% of a $100,000 book on the 8% stop, whole shares. | master-desk `desk/sleeves/femto/rsi_meanrev.py:30`<br>master-desk `desk/sleeves/femto/rsi_meanrev.py:79-85` |
| Sizing: ADA: the Binance book uses 100% of cash incl. 10 bps, lot-floored; the Alpaca forward up to 10% of $100,000. | `sleeves/ausar/ausar_spot_recipes.py:76-81`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:275-281`<br>`sleeves/fwd_alpaca_ada_rsi2.py:51-54`<br>`sleeves/fwd_alpaca_ada_rsi2.py:119` |
| Data: Yahoo daily bars (ETFs); split-adjusted daily bars (basket); Binance 1h klines and Alpaca crypto bars (ADA). | master-desk `desk/sleeves/families/ausar_public.py:38`<br>master-desk `desk/sleeves/families/femto_specs.py:75`<br>`sleeves/ausar/ausar_spot_recipes.py:104-135` |
| Midna v3 RSI2 rule | `desk3/aster_batch1.py:356-366` |
| Femto forward: gates and size, signal from context | `sleeves/fwd_alpaca_ada_rsi2.py:1-30` |
| Midna v3 rsi_meanrev change | `sleeves/rsi_meanrev.py:139-146`<br>`sleeves/rsi_meanrev.py:185-195` |

## [Public Donchian 55 trend (daily)](../../strategies/ausar/public-donchian55.md)

| Rule | Read from |
|---|---|
| Entry: Close > the prior 55-day high and > SMA200; ranked by (close - prior high) / ATR14; next open. | master-desk `desk/vendor/ausar/trader_signals.py:40-49`<br>master-desk `desk/vendor/ausar/trader_signals.py:270-278` |
| Exit: Close < the prior 20-day low or < SMA200, the 2 × ATR stop, or 126 holding bars. | master-desk `desk/vendor/ausar/trader_signals.py:48`<br>master-desk `desk/vendor/ausar/trader_signals.py:275`<br>master-desk `desk/sleeves/families/ausar_public.py:97-100` |
| Sizing: Liquidity cap as RSI2, and ≤ 0.5% of equity at risk to the 2 × ATR14 stop. | master-desk `desk/sleeves/families/ausar_public.py:95-100`<br>master-desk `desk/vendor/ausar/trader_signals.py:44` |
| Data: Yahoo daily bars. | master-desk `desk/sleeves/families/ausar_public.py:38` |

## [Public BB/KC squeeze (daily)](../../strategies/ausar/public-squeeze20.md)

| Rule | Read from |
|---|---|
| Entry: Prior bar BB(20, 2) inside KC(20, 1.5 ATR), current bar not; momentum (linear-regression endpoint) > 0 and rising; close > the prior 20-day high. | master-desk `desk/vendor/ausar/trader_signals.py:64-77`<br>master-desk `desk/vendor/ausar/trader_signals.py:241-259`<br>master-desk `desk/vendor/ausar/trader_signals.py:288-297` |
| Exit: Close < EMA20, momentum ≤ 0, the 2 × ATR stop, or 20 holding bars. | master-desk `desk/vendor/ausar/trader_signals.py:75`<br>master-desk `desk/vendor/ausar/trader_signals.py:295` |
| Sizing: Liquidity cap and 0.5% risk to the stop, as Donchian 55. | master-desk `desk/sleeves/families/ausar_public.py:95-100` |
| Data: Yahoo daily bars. | master-desk `desk/sleeves/families/ausar_public.py:38` |

## [IU big-body bar crypto (5m)](../../strategies/ausar/iu-body.md)

| Rule | Read from |
|---|---|
| Entry: Bar body > 4 × the 20-bar average body (21 bars, inclusive) and the bar closes up. | `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:17`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:80-86`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:202-205` |
| Exit: Trailing stop: entry - 2 × ATR14, then raised to close - 2 × ATR14, hit by the observed bid. | `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:206-213` |
| Sizing: 100% of book cash incl. 10 bps, lot-floored. | `sleeves/ausar/ausar_spot_recipes.py:76-81`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:275-281` |
| Data: Binance 5m klines and book ticker. | `sleeves/ausar/ausar_spot_recipes.py:104-135` |
| Femto forward is unlisted | `sleeves/fwd_alpaca_enj_iu_body.py:1-20` |

## [AI volume spike crypto (4h)](../../strategies/ausar/ai-volume.md)

| Rule | Read from |
|---|---|
| Entry: Volume > 2 × EMA20(volume), close > EMA50 and close > open. | `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:16`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:76-79` |
| Exit: Flat on the 5th bar of the position (the source counter), or on an opposite spike. | `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:192-201` |
| Sizing: Binance: 100% of cash incl. 10 bps. Alpaca forward: up to 10% of $100,000. | `sleeves/ausar/ausar_spot_recipes.py:76-81`<br>`sleeves/ausar/vendor/public_recipes/public_source_sleeves.py:275-281`<br>`sleeves/fwd_alpaca_link_ai_volume.py:55-57`<br>`sleeves/fwd_alpaca_link_ai_volume.py:123` |
| Data: Binance 4h klines; Alpaca crypto bars. | `sleeves/ausar/ausar_spot_recipes.py:104-135` |

## [Coinbase SMA200 crypto trend](../../strategies/ausar/coinbase-sma200.md)

| Rule | Read from |
|---|---|
| Entry: Gate: the latest completed UTC daily close strictly above the 200-day SMA (inclusive). | master-desk `desk/vendor/ausar_native/prospective_native_math.py:11-24`<br>master-desk `desk/vendor/ausar_native/prospective_native.py:36` |
| Entry: Rebalances 00:00-00:05 UTC to post-fee targets, once per day, with every market qualified. | master-desk `desk/sleeves/families/coinbase_sma200.py:180-219`<br>master-desk `desk/vendor/ausar_native/prospective_native.py:347-381` |
| Exit: A symbol whose gate turns off is sold in full at the bid, at any time. | master-desk `desk/sleeves/families/coinbase_sma200.py:224-227` |
| Exit: Aurelia forward: no exit on the master desk; Midna v3's copy sells it all on a close below the SMA200. | master-desk `desk/sleeves/femto/fwd_coinbase_sma200.py:133-144`<br>`sleeves/fwd_coinbase_sma200.py:145-160`<br>`sleeves/fwd_coinbase_sma200.py:219-272` |
| Sizing: Weights: ETH_SMA200 0/1, BTC_ETH_SMA200 0.5/0.5 of post-fee NAV; 0.2% fee per side; lot floors. | master-desk `desk/vendor/ausar_native/prospective_native.py:29-30`<br>master-desk `desk/vendor/ausar_native/prospective_native.py:347-381` |
| Sizing: Aurelia forward: 0.01 BTC at the ask once per UTC day (00:00-00:05) once 200 consecutive completed days exist and the quote is ≤ 30 s old; each order ≤ 10% of a $100,000 budget. | master-desk `desk/sleeves/femto/fwd_coinbase_sma200.py:38-46`<br>master-desk `desk/sleeves/femto/fwd_coinbase_sma200.py:75-106`<br>master-desk `desk/vendor/aurelia/coinbase_schedule.py:21-66` |
| Data: Coinbase daily candles (200), products and quotes. | master-desk `desk/sleeves/families/coinbase_sma200.py:83-151` |
| Midna v3 native rows | `desk3/aster_batch1.py:883-935` |
| Aurelia forward: no SMA200 test, no exit | master-desk `desk/sleeves/femto/fwd_coinbase_sma200.py:7-15` |
| Midna v3 forward: SMA200 entry and exit | `sleeves/fwd_coinbase_sma200.py:36-48` |

## [Daily20 tree-model forecasts](../../strategies/ausar/daily20.md)

| Rule | Read from |
|---|---|
| Entry: Eligible on its 20-bar phase: close ≥ $5, 20-day dollar volume ≥ $1M, ATR > 0, 234+ bars. | master-desk `desk/vendor/ausar_tensor/tensor_daily_models.py:374-405` |
| Entry: Selected when the model's forecast ≥ its frozen threshold; ranked by forecast; next open within 300 s; 10 slots. | master-desk `desk/vendor/ausar_tensor/tensor_daily_models.py:88-102`<br>master-desk `desk/vendor/ausar_tensor/tensor_daily_models.py:406-431` |
| Exit: Sells at the open 20 sessions after entry. | master-desk `desk/vendor/ausar_tensor/tensor_daily_models.py:414-417`<br>master-desk `desk/sleeves/families/ausar_daily20.py:278` |
| Sizing: floor(min(10% equity, 1% of 20-day dollar volume, cash) / (price × 1.001)). | master-desk `desk/sleeves/families/ausar_daily20.py:62`<br>master-desk `desk/sleeves/families/ausar_daily20.py:295-310` |
| Data: Yahoo daily bars; Tensor v690 engine features (Node). | master-desk `desk/sleeves/families/ausar_daily20.py:145` |

## [Tensor state repair (hourly / weekly)](../../strategies/ausar/tensor-state-repair.md)

| Rule | Read from |
|---|---|
| Entry: Full 7-vote panel now and 3 bars ago, vote balance up ≥ 2, ≥ 2 channels rising; close ≥ $5, 20-bar dollar volume ≥ $1M, ATR > 0; 20-bar cooldown. | master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:201-229`<br>master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:271-284` |
| Entry: Ranked by repair + 0.01 × balance + 0.001 × clip(OBV slope / volume); bought at the next open. | master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:285-289` |
| Exit: Sells at the open 20 native bars after entry. | master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:201`<br>master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:224-226` |
| Sizing: floor(min(10% equity, 1% of 20-bar dollar volume, settled cash) / (price × 1.001)); 10 slots. | master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:203-204`<br>master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:228-230` |
| Data: Yahoo 1h / 1wk bars; Tensor v690 vote channels. | master-desk `desk/vendor/ausar_ts/backend/tensor_strategy.py:189-200` |
| Midna v3 state-repair rule | `desk3/aster_batch1.py:1-30` |

## [R17 ETF ladder rules](../../strategies/ausar/r17-etf-ladder.md)

| Rule | Read from |
|---|---|
| Entry: Month-end decision; signals: 126- and 21-day log returns, 63-day volatility, 200-day MA, 20-day drawdown. | `sleeves/ausar/vendor/quant_r17/run_ladder.py:23-31` |
| Entry: LEADER3: top 3 by 126-day return. RELATIVE3: top 3 beating QQQ. VOLADJ3: relative strength / volatility. ACCEL3: (21-day - 126-day/6) / volatility, above the 200-day MA. REPAIR3: beating QQQ, 2-10% off the 20-day high, up 3 days, above the 200-day MA. ESCAPE1: best positive 126-day return above the 200-day MA. | `sleeves/ausar/vendor/quant_r17/run_ladder.py:32-41` |
| Entry: Unfilled slots go to QQQ (ESCAPE1 stays in cash). | `sleeves/ausar/vendor/quant_r17/run_ladder.py:42` |
| Exit: Held to the next month-end decision; sells first at the open. | `sleeves/ausar/r17_etf.py:155-202`<br>`sleeves/ausar/r17_etf.py:266-306` |
| Sizing: Equal weights × gross 0.98; each fund capped at 0.1% of its prior-day dollar volume; 15 bps per side. | `sleeves/ausar/vendor/quant_r17/run_ladder.py:76-91`<br>`sleeves/ausar/r17_etf.py:155-202`<br>`sleeves/ausar/r17_etf.py:206` |
| Data: Total-return daily closes and raw dollar volume. | `sleeves/ausar/vendor/quant_r17/run_ladder.py:11-21` |
