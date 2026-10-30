# Strategy catalog

Every trading strategy across our desks, one card each: what it trades, its rules as the code runs them, and where the code lives.

Monitors and research recorders are not listed.

<!-- BEGIN FIXED SECTION: agent guides. The README generator should emit this block verbatim (source text: docs/README_FIXED_SECTION.md). Checked by agentic-trade-desk/skeleton/tools/check_root_readme_links.py -->
> **New: [How to build an agentic trade desk](agentic-trade-desk/README.md)** — a full guide, written for LLM agents, covering architecture, setup, order safety, reconciliation, reliability, research validation, multi-agent coordination, 130 catalogued pitfalls, checklists and generic reference code. Paper trading only; not financial advice. See also the shorter [build guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md).
> **Guides for LLM agents:** [Agentic Trade Desk Build Guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md) (architecture and phases) · [`agentic-trade-desk/`](agentic-trade-desk/README.md) (operational kit: invariants, 130 pitfalls, tested skeleton code).
<!-- END FIXED SECTION -->

## Layout

| Folder | What |
|---|---|
| `strategies/<family>/` | one card per strategy |
| `sleeves/` | the code: Midna's sleeves, and copies of the master desk's under `sleeves/<family>/` (each listed in `docs/VERIFY.md`) |
| `desk3/`, `integration/` | Midna's v3 desk files and adapters |
| `pine/`, `indicator/` | the BB/RSI divergence indicator |
| `docs/CATALOG.json` | every strategy with its variants and row ids |
| `docs/SLEEVES.md` | every sleeve on the desk (333), one row each, with its code file in this repo |
| `docs/SLEEVES.json` | the same every-sleeve index in machine-readable form |
| `docs/ALL-SLEEVES.md` | the curated accounting: every strategy ever built across all desks, deduplicated, arranged by type, with its algorithm and variants |
| `docs/ALL-SLEEVES.json` | the same curated accounting in machine-readable form |
| `docs/VERIFY.md` | the code lines each card rule was read from (one page a family in `docs/verify/`), and where each copied file came from |

The master desk runs these sleeves on the Femto-lean framework (branch master-desk). Not in this repo: the framework itself (trading engine, order handling, data hub) and the Tensor indicator engine.

## Strategies

| Family | Cards | Assets | Bars | Live | Waiting | Blocked | Off |
|---|---:|---|---|---:|---:|---:|---:|
| [Ausar](strategies/ausar/) | 24 | Stocks, ETFs, Options, Crypto | 5m to 1mo | 48 | 97 | 21 |  |
| [Lazarus](strategies/lazarus/) | 19 | Stocks, ETFs | 1h to 1w | 17 | 7 | 54 |  |
| [Femto-lean](strategies/femto/) | 45 (1 Midna only) | Stocks, ETFs, Options, Crypto | 3m to 1mo | 24 | 32 | 4 |  |
| [Midna](strategies/midna/) | 17 | Stocks, ETFs, Options, Crypto | 1h to 1mo | 13 | 11 |  |  |
| [Muse](strategies/muse/) | 17 (7 Midna only) | Stocks, ETFs, Options | 1m to 1w |  | 11 |  |  |
| [APEX](strategies/apex/) | 33 | ETFs, Options, Crypto | 1d to 1mo | 38 |  |  |  |
| [Galath / GrokBot](strategies/galath/) | 10 | Stocks, ETFs | 5m to 1d | 3 | 7 |  |  |
| [Griffith](strategies/griffith/) | 23 | Stocks, ETFs | 1m to 1mo | 15 | 6 | 3 |  |
| [Milkman](strategies/milkman/) | 34 (1 Midna only) | Stocks, ETFs, Options, Futures | 1m to 1mo | 18 | 20 |  | 1 |
| [Quant research](strategies/quant_research/) | 18 | Stocks, ETFs | 1m to 1mo | 7 | 6 | 5 |  |
| [Tensor research](strategies/tensor_research/) | 13 | Stocks | 1h to 1w | 8 | 6 |  |  |
| [Killed studies](strategies/killed/) | 10 | Stocks, ETFs | 5m to 1w | 10 | 1 |  |  |
| [Qullamaggie](strategies/qullamaggie/) | 3 | Stocks | 1m to 1d | 1 | 4 |  |  |
| [Sable](strategies/sable/) | 2 | Stocks | 5m to 1d | 2 |  |  |  |
| [SPAN](strategies/span/) | 1 | Prediction markets | trade prints |  | 1 |  |  |
| **All** | **269** | | | **204** | **209** | **87** | **1** |

Status counts are master-desk rows; one card can hold several rows (its variants).

<details><summary><b>Ausar</b> · 24</summary>

- [AI volume spike crypto (4h)](strategies/ausar/ai-volume.md) · Crypto spot · 4h
- [Coinbase SMA200 crypto trend](strategies/ausar/coinbase-sma200.md) · Crypto spot · 1d
- [Crypto confirmed absorption (4h)](strategies/ausar/crypto-absorption.md) · Crypto spot · 4h
- [Daily20 tree-model forecasts](strategies/ausar/daily20.md) · US equities · 1d
- [Earnings-drift (PEAD) put options](strategies/ausar/opt-pead.md) · Equity options · 1d
- [Index-ETF recovery options (RSI2 / VWAP20)](strategies/ausar/opt-recovery.md) · ETF options · 1d
- [IU big-body bar crypto (5m)](strategies/ausar/iu-body.md) · Crypto spot · 5m
- [Opening gamma puts](strategies/ausar/opt-opening-gamma.md) · Equity options · 5m
- [Public BB/KC squeeze (daily)](strategies/ausar/public-squeeze20.md) · US ETFs · 1d
- [Public Donchian 55 trend (daily)](strategies/ausar/public-donchian55.md) · US ETFs · 1d
- [QQQ 95% core with RSI2 options](strategies/ausar/opt-qqq95-rsi2.md) · ETF + ETF options · 1d
- [R17 ETF ladder rules](strategies/ausar/r17-etf-ladder.md) · US ETFs · 1d, monthly
- [R19 10-minute EMA cloud reclaim](strategies/ausar/r19-timing-cloud.md) · US equities · 10m (1h bias)
- [R19 causal overnight hold](strategies/ausar/r19-timing-overnight.md) · US equities · 30m
- [R19 crypto breakout and negative-funding squeeze](strategies/ausar/r19-crypto-breakout.md) · Crypto spot · 4h
- [R19 ETF books: momentum leader rotation](strategies/ausar/r19-etf.md) · US ETFs · 1d, monthly rebalance
- [R19 hourly confirmed swing](strategies/ausar/r19-timing-hourly.md) · US equities · 1h
- [R19 weekly Tensor beta M2 52-week cohort](strategies/ausar/r19-tensor-beta-m2.md) · US equities · 1w
- [R19 weekly Tensor C1 cyan ownership](strategies/ausar/r19-tensor-c1.md) · US equities · 1w
- [R19 weekly Tensor G4 green ownership](strategies/ausar/r19-tensor-g4.md) · US equities · 1w
- [RSI(2) pullback](strategies/ausar/public-rsi2.md) · US ETFs · US equities · crypto (ADA) · 1d · 1h
- [Tensor LEAPS calls](strategies/ausar/opt-tensor-leaps.md) · Equity options · 1w
- [Tensor state repair (hourly / weekly)](strategies/ausar/tensor-state-repair.md) · US equities · 1h · 1w
- [XSP weekly put credit spread](strategies/ausar/opt-xsp-pcs.md) · Index options · 1w

</details>

<details><summary><b>Lazarus</b> · 19</summary>

- [ChartsLector breakout leaders (small caps)](strategies/lazarus/cl-qm-small.md) · US equities · 1d
- [ChartsLector market-fear rebound (QQQ)](strategies/lazarus/cl-vmr-qqq.md) · US ETF · 1d
- [CHASE weekly lane](strategies/lazarus/lz-wait-chase.md) · US equities · 1w
- [Daily Cyan desk feed](strategies/lazarus/lz-daily-cyan.md) · US equities · 1d
- [Daily Green under $5](strategies/lazarus/lz-daily-green-under5.md) · US equities · 1d
- [FLOW short volume / FTD / dark pool](strategies/lazarus/lz-wait-flow.md) · US equities · 1d
- [Intraweek early entry](strategies/lazarus/lz-wait-intraweek.md) · US equities · 1w (daily entry)
- [Lab 1D Green trees](strategies/lazarus/lz-lab-1d-green-trees.md) · US equities · 1d
- [Lab 1W Cyan books](strategies/lazarus/lz-lab-1w-cyan-books.md) · US equities · 1w
- [Lab 1W Swing covered](strategies/lazarus/lz-lab-1w-swing.md) · US equities · 1w
- [Lab rule books (1D / 1W)](strategies/lazarus/lz-lab-rules.md) · US equities · 1d · 1w
- [Moonshot weekly lane](strategies/lazarus/lz-moonshot.md) · US equities · 1w
- [OLX R1/R2 books](strategies/lazarus/lz-wait-olx.md) · US equities · 1d
- [Q07 Tensor alt-data confluence cells](strategies/lazarus/lz-q07.md) · US equities · 1w
- [Q14 under-$5 weekly book](strategies/lazarus/lz-wait-q14.md) · US equities · 1w
- [R2 Daily Cyan extended](strategies/lazarus/lz-wait-r2-dcyan.md) · US equities · 1d
- [Tensor tracker lanes (1H / 1D / 1W)](strategies/lazarus/lz-tracker.md) · US equities · 1h · 1d · 1w
- [Weekly Cyan tier A](strategies/lazarus/lz-weekly-cyan-tier-a.md) · US equities · 1w
- [Weekly Green tier A small](strategies/lazarus/lz-weekly-green-small.md) · US equities · 1w

</details>

<details><summary><b>Femto-lean</b> · 45</summary>

- [12-month momentum top decile (monthly)](strategies/femto/femto-ts-momentum-decile.md) · US equities · 1d (monthly)
- [20-day VWAP reversion](strategies/femto/femto-ema-vwap.md) · US equities · 1d (hourly checks)
- [20-day VWAP reversion call spreads](strategies/femto/femto-ema-vwap-options.md) · Equity options · 1d (hourly checks)
- [60-day momentum rotation](strategies/femto/femto-momentum-rotation.md) · US equities · 1d (weekly)
- [Aurelia Nasdaq + gold allocation](strategies/femto/femto-aurelia.md) · US ETFs (incl. 3× leveraged) · 1d
- [Beaten-down weekly qualifiers](strategies/femto/femto-beatendown.md) · US equities · 1w
- [Bilbo Box calls](strategies/femto/femto-bilbo-options.md) · Equity options · 1h (5-minute exits)
- [Buyback before earnings (call spreads)](strategies/femto/femto-earnings-buyback.md) · Equity options · 1d (hourly checks)
- [Capitulation reversal (hourly)](strategies/femto/femto-capitulation.md) · US equities · 1h · 1d filters
- [Capitulation reversal calls (0-7 DTE)](strategies/femto/femto-capitulation-options.md) · Equity options · 1h · 1d filters
- [Daily Cyan GBM](strategies/femto/femto-daily-cyan-gbm.md) · US equities · 1d
- [Daily Cyan small-cap rule](strategies/femto/femto-rule-1d-cyan-smallcap.md) · US equities · 1d
- [Daily Green turn-of-month rule](strategies/femto/femto-rule-1d-green-tom.md) · US equities · 1d
- [Donchian 20/10 breakout](strategies/femto/femto-donchian.md) · US equities · crypto (SOL) · 1d · 15m
- [Fear premium put spreads (red days)](strategies/femto/femto-fear-premium.md) · Equity options · 1d (hourly checks)
- [High-IV iron condor](strategies/femto/femto-iron-condor.md) · Equity options · 1d (hourly checks)
- [Hourly Cyan range-expansion rule](strategies/femto/femto-rule-1h-cyan-raw.md) · US equities · 1h
- [Kraken basis repair (ADA / LINK)](strategies/femto/femto-kraken-basis.md) · Crypto spot + perpetual · 4h
- [Kraken breakdown short (ADA / LINK)](strategies/femto/femto-kraken-breakdown.md) · Crypto perpetual · 4h
- [Kraken crowded-long failure short (ADA / LINK)](strategies/femto/femto-kraken-crowded.md) · Crypto perpetual · 4h
- [Kraken ENJ order-book imbalance (spot)](strategies/femto/femto-free-kraken-enj-spot.md) · Crypto spot · 1h checks
- [Leader-1d event](strategies/femto/femto-leader-d.md) · US equities · 1d (one variant 1h)
- [LEAPS momentum with covered calls](strategies/femto/femto-leaps-momentum.md) · Equity options · 1d (hourly checks)
- [Legend's EMA (trend-day fade)](strategies/femto/femto-legends-ema.md) · US ETFs · 15m · 1d
- [Microcap snapback (weekly)](strategies/femto/femto-snapback.md) · US equities (microcaps) · 1w · 1d
- [Morning dip limit](strategies/femto/femto-morning-dip.md) · US ETFs · 3m
- [Own-IV straddle](strategies/femto/femto-free-opt-own-iv.md) · ETF options · 1d (5-minute passes)
- [Phase compression breakout (daily)](strategies/femto/femto-phase-daily.md) · US equities · 1d
- [Phoenix breakout (red-day entry)](strategies/femto/femto-phoenix.md) · US equities and ETFs · 1d
- [QQQ weekly put ladder](strategies/femto/femto-qqq-put-ladder.md) · ETF options · 1d (weekly layers)
- [R4 blowoff (daily / hourly)](strategies/femto/femto-blowoff.md) · US equities · 1d · 1h
- [Red-day washout reversal](strategies/femto/femto-red-day-reversal.md) · US equities · 1d (hourly checks)
- [Release straddle (CPI, jobs, FOMC)](strategies/femto/femto-free-opt-release.md) · ETF options · 1d (5-minute passes)
- [RSI(2) pullback call spreads](strategies/femto/femto-rsi-meanrev-options.md) · Equity options · 1d (hourly checks)
- [Six-month momentum leaders](strategies/femto/femto-momentum.md) · US equities · 1d
- [SPY / QQQ residual option pair](strategies/femto/femto-free-opt-pair.md) · ETF options · 1d (5-minute passes)
- [SPY 30-delta wheel](strategies/femto/femto-free-opt-wheel.md) · ETF options · 1d (5-minute passes)
- [SPY put-call parity package](strategies/femto/femto-free-opt-parity.md) · ETF options · 1d (5-minute passes)
- [Tail put after a -3% day](strategies/femto/femto-free-opt-tail.md) · ETF options · 1d (5-minute passes)
- [Tensor 1H swing flagship](strategies/femto/femto-tensor-swing.md) · US equities · 1h
- [Tensor red-dip buys on fear days](strategies/femto/femto-tensor-red-dip.md) · US equities · Intraday · 1h signals
- [VXX call tail hedge](strategies/femto/femto-vix-hedge.md) · ETP options · 1d (hourly checks)
- [Weekly Cyan momentum ADX rule](strategies/femto/femto-rule-1w-cyan-mom-adx.md) · US equities · 1w
- [Weekly swing high-beta WaveTrend rule](strategies/femto/femto-rule-1w-swing-beta-wt.md) · US equities · 1w
- [Winner confluence (weekly qualifiers)](strategies/femto/femto-confluence.md) · US equities · 1w

</details>

<details><summary><b>Midna</b> · 17</summary>

- [Distance-pair shares](strategies/midna/mn-distance-pair.md) · US equities · 1d
- [EMA4 rising VWAP](strategies/midna/mn-ema4-vwap.md) · US equities · 1d
- [Faber ETF trend (10-month average)](strategies/midna/mn-faber.md) · US ETFs · 1d (monthly average)
- [Forward lab accounts (Tensor scan)](strategies/midna/mn-forward-lab.md) · US equities · 1d · 1w
- [Hourly Tensor playbook](strategies/midna/mn-hourly-playbook.md) · US equities · 1h
- [Hyperliquid momentum floor](strategies/midna/mn-hyperliquid-floor.md) · Crypto perps · intraday (10-min scan)
- [Kronos-base TopkDropout](strategies/midna/mn-kronos-topk.md) · US equities · 1d (10-session cycle)
- [Large-cap prior-month reversal](strategies/midna/mn-prior-month-reversal.md) · US equities · 1d (monthly)
- [Listed distance-pair package](strategies/midna/mn-opt-distance-pair.md) · Equity options · 1d
- [Listed reversal call spread](strategies/midna/mn-opt-reversal.md) · Equity options · 1d (monthly)
- [Listed Turtle ATM call](strategies/midna/mn-opt-turtle.md) · Equity options · 1d
- [MACD-CCI](strategies/midna/mn-macd-cci.md) · US equities · 1d
- [QLD weekly timing](strategies/midna/mn-qld-weekly-timing.md) · Leveraged ETF · 1w
- [QQQ flip5 TZA hedge](strategies/midna/mn-qqq-flip5-tza.md) · Leveraged ETF · 1d
- [TSMOM 12-1 ETF book](strategies/midna/mn-tsmom-12-1-etf.md) · US ETFs · 1d (every 21 sessions)
- [Turtle System 1](strategies/midna/mn-turtle.md) · US equities · 1d
- [Weekly 8/20/50 pullback](strategies/midna/mn-weekly-8-20-50-pullback.md) · US ETFs · 1w signal · 1d management

</details>

<details><summary><b>Muse</b> · 17</summary>

- [15.87 Rule (SPY 0DTE)](strategies/muse/muse-em-1587.md) · SPY options (0DTE) · 5m
- [Band-touch RSI divergence](strategies/muse/muse-bb-rsi-divergence.md) · US ETFs and large caps · 1h
- [Grok support and resistance (SPY)](strategies/muse/muse-grok-sr-spy.md) · SPY shares, long and short · 1m
- [InvestAndBeFree double MACD (SPY and QQQ options)](strategies/muse/muse-investandbefree-dmac.md) · SPY and QQQ options (long premium) · 4H, daily, weekly stack
- [PO10 extreme (QQQ)](strategies/muse/muse-po10-qqq.md) · QQQ shares, long and short · 10m
- [PRZM Fade Edges recreation (SPY)](strategies/muse/muse-przm-fade-edges.md) · SPY shares, long and short · 1m
- [PRZM Zero recreation (SPY)](strategies/muse/muse-przm-zero.md) · SPY shares (signal engine) · 1m
- [Raschke PF3 momentum (SPY)](strategies/muse/muse-raschke-pf3.md) · SPY shares, long and short · 5m
- [Raschke RRE adaptive desk (SPY)](strategies/muse/muse-raschke-rre.md) · SPY shares · 5m
- [SATY day system (SPY 0DTE)](strategies/muse/muse-saty-day.md) · SPY options (0DTE) · 1m · 3m · 10m · 1h
- [Saty Magnum (SPY shares)](strategies/muse/muse-saty-magnum.md) · SPY shares, long and short · 3m · 10m · 1h · 1d
- [Saty opportunity engine v0.3 (SPY shares)](strategies/muse/muse-saty-gpt-v03.md) · SPY shares, long and short · 10m · 1h
- [Saty research system v0.2 (SPY shares)](strategies/muse/muse-saty-gpt-v02.md) · SPY shares, long and short · 10m · 1h
- [Shen first-touch fade (SPY 0DTE)](strategies/muse/muse-shen-fade.md) · SPY options (0DTE) · 1m
- [Sol's Saty engine (SPY options)](strategies/muse/muse-saty-sol.md) · SPY options · 1m · 3m · 10m
- [Teddy opening range breakout (SPY)](strategies/muse/muse-teddy-orb-spy.md) · SPY shares, long and short · 5m (aggregated from 1m)
- [Trullas divergence (QQQ 1-minute)](strategies/muse/muse-trullas-divergence.md) · QQQ shares, long and short · 1m

</details>

<details><summary><b>APEX</b> · 33</summary>

- [APEX C2: Sector Kings](strategies/apex/apex-c2-sector-kings.md) · US ETFs · 1d (monthly picks)
- [APEX C3: Follow-through](strategies/apex/apex-c3-follow-through.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C4: Broken Hedge](strategies/apex/apex-c4-broken-hedge.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C5: REFLEX](strategies/apex/apex-c5-reflex.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C6: SLINGSHOT](strategies/apex/apex-c6-slingshot.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C7: COUNCIL](strategies/apex/apex-c7-council.md) · US ETFs, ETF options and Bitcoin · 1d (monthly options)
- [APEX E1: VIX term-structure gate](strategies/apex/apex-e1-vix-term-gate.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E2: Double 7 dip overlay](strategies/apex/apex-e2-double7-dip.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E3 / v1.1: defensive Treasuries](strategies/apex/apex-e3-defensive-treasuries.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E4: rolling tail puts](strategies/apex/apex-e4-rolling-tail-puts.md) · US ETFs and ETF options · 1d (monthly puts)
- [APEX E5: semiconductor tilt](strategies/apex/apex-e5-semis-rs-tilt.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E6: overnight boost](strategies/apex/apex-e6-overnight-boost.md) · US ETFs (incl. 3× leveraged) · 1d (overnight boost)
- [APEX E7: turn-of-month boost](strategies/apex/apex-e7-turn-of-month.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N1: Duration Shield](strategies/apex/apex-n1-duration-shield.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N2: Silicon Switch](strategies/apex/apex-n2-silicon-switch.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N3 / N4: PRISM multi-asset trend](strategies/apex/apex-n3-prism-classic.md) · US ETFs and Bitcoin · 1d
- [APEX N5: GESTALT analog engine](strategies/apex/apex-n5-gestalt.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N6: GESTALT × APEX](strategies/apex/apex-n6-gestalt-apex.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N7: OMNI](strategies/apex/apex-n7-omni.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O10: LEAPS + Variance Value](strategies/apex/apex-o10-leaps-vv.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O11: APEX + Variance Value](strategies/apex/apex-o11-apex-vv.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O12: hybrid LEAPS + QQQ trim](strategies/apex/apex-o12-hybrid-leaps.md) · US ETFs and ETF options · 1d
- [APEX O1: CONVEX](strategies/apex/apex-o1-convex.md) · US ETFs and ETF options · 1d
- [APEX O2: LEAPS-APEX](strategies/apex/apex-o2-leaps.md) · US ETFs and ETF options · 1d
- [APEX O3: regime put-write](strategies/apex/apex-o3-regime-putwrite.md) · US ETFs and ETF options · 1d (monthly puts)
- [APEX O4: PHOENIX](strategies/apex/apex-o4-phoenix.md) · US ETFs and ETF options · 1d
- [APEX O5: CHOP HARVEST](strategies/apex/apex-o5-chop-harvest.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O6: Variance Value](strategies/apex/apex-o6-variance-value.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O7: skew risk reversal](strategies/apex/apex-o7-skew-risk-reversal.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O8: FEAR put spread](strategies/apex/apex-o8-fear-put-spread.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O9: OMEGA](strategies/apex/apex-o9-omega.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX QQQ benchmark](strategies/apex/apex-benchmarks.md) · US ETFs · 1d
- [APEX-50F Nasdaq trend × volatility](strategies/apex/apex-trend-har-tiers.md) · US ETFs (incl. 3× leveraged) · 1d

</details>

<details><summary><b>Galath / GrokBot</b> · 10</summary>

- [Anna PhD location printer](strategies/galath/galath-anna-phd-printer.md) · US equities and ETFs · 1d
- [Anna seven-vote printer](strategies/galath/galath-anna-seven-vote-printer.md) · US equities · 1d
- [CCI correction pullback](strategies/galath/galath-cci-correction.md) · US equities · 1d
- [Echo swing](strategies/galath/galath-echo-swing.md) · US equities · Posts (3-minute sweeps) · 1d
- [Komar momentum breakout](strategies/galath/galath-komar-momentum.md) · US equities · 1d
- [Next-support plan](strategies/galath/galath-next-support-plan.md) · US equities · 1d (1-minute passes)
- [Scanner book swing](strategies/galath/galath-scanner-book-swing.md) · US equities · 1d · 5m session tape
- [Sector-first bottom](strategies/galath/galath-sector-first-bottom.md) · US equities · 1d · 5m session tape
- [Tensor 2 washout / reclaim printer](strategies/galath/galath-tensor2-washout-reclaim.md) · US equities and ETFs · 1h
- [Washout and PPC coil](strategies/galath/galath-washout-ppc-coil.md) · US equities · 1d (1-minute passes)

</details>

<details><summary><b>Griffith</b> · 23</summary>

- [20-minute opening range breakout](strategies/griffith/griffith-orb20.md) · US equities · 5m
- [52-week-high strength](strategies/griffith/griffith-52w-high-rs.md) · US equities · 1d (monthly)
- [Auditable 20/50 trend (SPY)](strategies/griffith/griffith-auditable-20-50-trend.md) · US ETF (SPY) · 5m
- [Cross-sectional momentum (12-1 / 6-1)](strategies/griffith/griffith-xs-momentum.md) · US equities · 1d (monthly)
- [ETF 12-month time-series momentum](strategies/griffith/griffith-etf-tsmom12.md) · US ETFs · 1d (monthly)
- [Gap continuation (legacy setup)](strategies/griffith/griffith-gap-continuation.md) · US equities · 1m (15-minute cycle)
- [Leaders Rest](strategies/griffith/griffith-leaders-rest.md) · US equities · 1d
- [Liquid momentum trend cohorts](strategies/griffith/griffith-liquid-momentum-trend.md) · US equities · 1d (20-session cohorts)
- [Momentum breakout (legacy setup)](strategies/griffith/griffith-momentum-breakout.md) · US equities · 1m (15-minute cycle)
- [Momentum plus earnings drift](strategies/griffith/griffith-momentum-pead.md) · US equities · 1d (20-session hold)
- [Parallax](strategies/griffith/griffith-parallax.md) · US equities · 1d
- [Positive earnings surprise drift](strategies/griffith/griffith-pead-sue.md) · US equities · 1d (20-session hold)
- [Simple daily trend cohorts](strategies/griffith/griffith-simple-daily-trend.md) · US equities · 1d (20-session cohorts)
- [Tensor edge v0.1 (G1 / G2 / C1)](strategies/griffith/griffith-tensor-edge-v01.md) · US equities · 1d · 1w
- [Tensor frozen phenotypes v4](strategies/griffith/griffith-frozen-phenotypes-v4.md) · US equities · 1d · 1w
- [Tensor HTF conditional holdout (H1-H8)](strategies/griffith/griffith-htf-conditional-h1-h8.md) · US equities · 1d · 1w
- [Tensor HTF relay (T1-T7)](strategies/griffith/griffith-htf-relay.md) · US equities · 1d · 1w
- [Tensor phenotype experiment (HIGH_BREAK_4)](strategies/griffith/griffith-tensor-phenotype-experiment.md) · US equities · 1d · 1w
- [Tensor weekly color forward shadow (FG / FC)](strategies/griffith/griffith-weekly-color-forward-shadow.md) · US equities · 1w
- [Tensor weekly cyan confirmation (CY01-CY18)](strategies/griffith/griffith-weekly-cyan-confirmation.md) · US equities · 1w
- [Tensor weekly green / cyan deep confirmation (WG / WC)](strategies/griffith/griffith-weekly-green-cyan-deep-confirmation.md) · US equities · 1w
- [Top-decile SUE drift](strategies/griffith/griffith-top-decile-sue.md) · US equities · 1d (20-session hold)
- [VWAP pullback (legacy setup)](strategies/griffith/griffith-vwap-pullback.md) · US equities · 1m (15-minute cycle)

</details>

<details><summary><b>Milkman</b> · 34</summary>

- [ATR level cascade (SPY)](strategies/milkman/mk-atrlevelcascade.md) · US ETF · 1m
- [Big down-day response](strategies/milkman/mk-bigdowndayresponse.md) · US index ETFs and futures · 1d
- [Big Winners weekly Tensor sleeve](strategies/milkman/mk-bigwinners.md) · US equities · 1w
- [Bilbo Golden Gate (SPY)](strategies/milkman/mk-bilbogoldengate.md) · US ETF · 1m · 1h Phase Oscillator
- [Call-to-put reversal (SPY)](strategies/milkman/mk-calltoputputtocallreversal.md) · US ETF · 1m
- [Connors Double 7](strategies/milkman/mk-connorsdouble7.md) · US equities, index ETFs and futures · 1d
- [Daily Bilbo Box](strategies/milkman/mk-dailybilbobox.md) · US equities, index ETFs and futures · 1d
- [Daily compression expansion](strategies/milkman/mk-dailycompressionexpansion.md) · US equities, index ETFs and futures · 1d
- [Day Golden Gate (SPY)](strategies/milkman/mk-daygoldengate.md) · US ETF · 1m (daily ATR levels)
- [Directional trigger box (SPY)](strategies/milkman/mk-directionaltriggerbox.md) · US ETF · 10m
- [EMA21 deviation reversion](strategies/milkman/mk-ema21deviationreversion.md) · US equities, index ETFs and futures · 1d
- [ES Monday clock (SPY)](strategies/milkman/mk-esmondayclockonspyproxy.md) · US ETF · 1m (06:00-16:00 ET)
- [Four-hour Phase Oscillator OpEx rollover (SPY)](strategies/milkman/mk-fourhourpoopexrollover.md) · US ETF · 4h
- [Gap fade / momentum mirror (SPY)](strategies/milkman/mk-gapfademomentummirror.md) · US ETF · 1d gap · 1m exits
- [Gap-up pre-noon continuation (SPY)](strategies/milkman/mk-gapupprenooncontinuation.md) · US ETF · 1m
- [Legend's Buy Day](strategies/milkman/mk-legendsbuyday.md) · US equities, index ETFs and futures · 1d
- [Milkman 0DTE (SPX)](strategies/milkman/mk-zerodte-spx.md) · SPX index options (0DTE) · Intraday
- [Milkman daily rules on crypto-linked stocks](strategies/milkman/mk-milkmancryptolinkedstockvariant.md) · US equities · 1d
- [Milkman filters on Tensor lanes](strategies/milkman/mk-milkmanlaneaddonfilters.md) · US equities · 1w · 1d
- [Multi-day Golden Gate (weekly ATR)](strategies/milkman/mk-multidaygoldengateweekly.md) · US equities, index ETFs and futures · 1d (weekly ATR levels)
- [O'Neil follow-through-day race](strategies/milkman/mk-oneilfollowthroughdayrace.md) · US index ETFs and futures · 1d
- [Opening range breakout (SPY)](strategies/milkman/mk-openingrangebreakout.md) · US ETF · 1m (5-minute closes)
- [Phase Oscillator zone exit](strategies/milkman/mk-phaseoscillatorzoneexit.md) · US equities, index ETFs and futures · 1d
- [Pivot Ribbon 13/48 cross](strategies/milkman/mk-pivotribbon1348cross.md) · US equities, index ETFs and futures · 1d
- [Premarket all-time-high fade (SPY)](strategies/milkman/mk-premarketathmorningfade.md) · US ETF · 1m · 10m Phase Oscillator
- [Swing Golden Gate (monthly ATR)](strategies/milkman/mk-swinggoldengatemonthly.md) · US equities, index ETFs and futures · 1d (monthly ATR levels)
- [Ten-minute compression release (SPY)](strategies/milkman/mk-tenminutecompressionrelease.md) · US ETF · 10m
- [Tensor breadth timing (IWM)](strategies/milkman/mk-creativetensorbreadthtiming.md) · US ETF · 1w
- [Tensor fires as calls](strategies/milkman/mk-creativetensoroptionexpressionproxy.md) · Equity options · 1w
- [Tensor ratio-chart signals](strategies/milkman/mk-creativetensorratiochartsignals.md) · US equities · 1w
- [Three-minute compression drift (SPY)](strategies/milkman/mk-threeminutecompressiondrift.md) · US ETF · 3m
- [Three-minute trigger confirmation (SPY)](strategies/milkman/mk-threeminutetriggerconfirmation.md) · US ETF · 3m
- [Vomy / iVomy (SPY)](strategies/milkman/mk-vomyivomy.md) · US ETF · 10m
- [Weekday open-to-close (Monday)](strategies/milkman/mk-weekdayopentocloseproxy.md) · US index ETFs and futures · 1d

</details>

<details><summary><b>Quant research</b> · 18</summary>

- [AIRT auction impulse](strategies/quant_research/qr-auctionimpulseresponsetrading.md) · US equities · Intraday (≤ 30 minutes)
- [AlphaMemo factor book](strategies/quant_research/qr-alphamemosourcepreservingfactorrecon.md) · US equities · 1d
- [AlphaQCM factor rotation](strategies/quant_research/qr-alphaqcmiqcmfactorpolicyreconstructi.md) · US equities · 1d (every 20 sessions)
- [BOLT event tilt (SPY / QQQ)](strategies/quant_research/qr-bracketedoptionlawtransport.md) · US ETFs (SPY, QQQ) · Event windows (about 10 sessions)
- [CARM recovery memory](strategies/quant_research/qr-commitmentadjustedrecoverymemory.md) · US equities and QQQ · Intraday (≤ 30 minutes)
- [CER entitlement repricing](strategies/quant_research/qr-conjunctiveentitlementrepricing.md) · US equities and ETFs · 1d (21- or 63-session hold)
- [CQR contract queue revaluation](strategies/quant_research/qr-contractqueuerevaluation.md) · US equities · 1d (up to 63 sessions)
- [CRD capital release](strategies/quant_research/qr-capitalreleasedynamics.md) · US equities · 1w decisions
- [CRG own-stock filing surprise](strategies/quant_research/qr-catalystresolutiongap.md) · US equities and ETFs · 1d (20-session hold)
- [Fast Numbers earnings surprise](strategies/quant_research/qr-fastnumbersslowwordseventreconstruct.md) · US equities (long and short) · 1d (open to close)
- [FinRL-X adaptive rotation](strategies/quant_research/qr-finrlxreleasedadaptiverotationrecons.md) · US equities and ETFs · 1w
- [News-conditioned 12-1 leadership](strategies/quant_research/qr-newsconditioned121leadership.md) · US equities · 1mo ranking · 1h timing
- [QuantaAlpha factor book](strategies/quant_research/qr-quantaalphadeterministicproposalreco.md) · US equities · 1d
- [Spectral Echo Drift](strategies/quant_research/qr-spectral-echo-drift.md) · US equities · 1m (from IEX quotes)
- [TCFT index-flow swap](strategies/quant_research/qr-timecutflowtransport.md) · US equities and QQQ · 1d (to the event's endpoint)
- [Tensor rejection memory (MID21)](strategies/quant_research/qr-tensor-rejection-memory.md) · US equities · 1d
- [TRACE residual accumulation (daily)](strategies/quant_research/qr-tensor-residual-accumulation.md) · US equities · 1d
- [UIR filing relay](strategies/quant_research/qr-unpricedinformationrelay.md) · US equities and ETFs · 1d (20-session hold)

</details>

<details><summary><b>Tensor research</b> · 13</summary>

- [Coiled Spring genome](strategies/tensor_research/tr-genome-coiled-spring.md) · US equities · 1h · 1d · 1wk
- [Comeback genome](strategies/tensor_research/tr-genome-comeback.md) · US equities · 1h · 1d · 1wk
- [Daily green base expansion](strategies/tensor_research/tr-genome-daily-green-base-expansion.md) · US equities · 1d
- [Deep Reset cross-scan](strategies/tensor_research/tr-ro-deep-reset-cross-scan.md) · US equities · 1d · 1wk
- [Edge paper hands (10 lineages)](strategies/tensor_research/tr-sable-edge-paper-hands.md) · US equities · 1h
- [Hourly Core / Burst transition](strategies/tensor_research/tr-ro-hourly-transition-core-burst.md) · US equities · 1h
- [Leader genome](strategies/tensor_research/tr-genome-leader.md) · US equities · 1h · 1d · 1wk
- [Leaders Rest v1.1 on daily buy-greens](strategies/tensor_research/tr-ro-leaders-rest-v11.md) · US equities · 1d
- [Swing Transition (1H)](strategies/tensor_research/tr-ro-swing-transition-1h-v1.md) · US equities · 1h
- [Tensor 1H Swing (v615)](strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md) · US equities · 1h
- [Weekly cyan accumulation](strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md) · US equities · 1wk
- [Weekly cyan transition](strategies/tensor_research/tr-ro-weekly-cyan-transition.md) · US equities · 1wk
- [Weekly green recovery](strategies/tensor_research/tr-ro-weekly-green-recovery.md) · US equities · 1wk

</details>

<details><summary><b>Killed studies</b> · 10</summary>

- [Distance pairs](strategies/killed/killed-pairs-distance-coint.md) · US equities · 1d
- [Earnings-day overnight scalp](strategies/killed/killed-pead-spillover-scalp.md) · US equities · 1d (overnight)
- [Golden cross (SPY)](strategies/killed/killed-golden-cross-spy.md) · US ETF · 1d
- [Intraday momentum (Gao et al.)](strategies/killed/killed-intraday-momentum-gao.md) · US ETFs · 5m
- [Naive 20-day breakout](strategies/killed/killed-naive-20d-breakout.md) · US equities · 1d
- [PEAD price surprise](strategies/killed/killed-pead-price-surprise.md) · US equities · 1d (event)
- [RSI × OBV daily studies](strategies/killed/killed-rsiobv-daily.md) · US equities · 1d
- [RSI × OBV intraday (5-minute)](strategies/killed/killed-rsiobv-intraday.md) · US equities · 5m
- [Six short candidates](strategies/killed/killed-short-candidates.md) · US equities · 30m · 1d
- [Small-cap high-beta beaten-down (52 weeks)](strategies/killed/killed-smcap-beta-52w.md) · US equities · 1w

</details>

<details><summary><b>Qullamaggie</b> · 3</summary>

- [Qullamaggie breakout](strategies/qullamaggie/qm-leader-breakout.md) · US equities · 1d setup · 5m / 1m trigger
- [Qullamaggie episodic pivot](strategies/qullamaggie/qm-episodic-pivot.md) · US equities · 1d setup · 1m trigger
- [Qullamaggie parabolic short](strategies/qullamaggie/qm-parabolic-short.md) · US equities · 1d setup · 1m trigger

</details>

<details><summary><b>Sable</b> · 2</summary>

- [Location-first repair](strategies/sable/sable-location-first.md) · US equities · 1d (5-minute passes)
- [Support scanner (5-minute)](strategies/sable/sable-support-scanner.md) · US equities · 5m

</details>

<details><summary><b>SPAN</b> · 1</summary>

- [SPAN Harvest](strategies/span/span-harvest.md) · Prediction markets · Trade prints (60 s passes)

</details>

## How to read a card

- **Header**: family, source, asset, bars, universe, style and status.
- **Entry / Exit / Sizing / Data**: the rules as the code runs them; `docs/VERIFY.md` gives the lines.
- **Variants**: rows that run the same rules on other symbols, bars, sizes or parameters.
- **Code**: each desk's implementation; paths marked *not in this repo* stay on the master desk.

## Status

| Status | Meaning |
|---|---|
| live | trading: holds a position or traded recently |
| waiting | on, waiting for its next signal or session |
| blocked | on, but an input or a defect stops it |
| off | switched off |
| Midna's desk only | not run on the master desk |

Status is the master desk's roll call of 2026-10-26.

## Credits

| Who | For |
|---|---|
| Midna | her TypeScript and Python v3 desks, and the strategies posted here |
| Femto-lean | the owner's Python desk; the master desk runs its framework |
| Desks and agents | Ausar, Lazarus, Galath / GrokBot, Griffith / Ledge, APEX (Cursor2), Aurelia (Agentic-Trading-Desk), Sable / Autopilot, SPAN, the quant research desk, the Milkman v2 study, FolioTend research, Sol (ChatGPT), Grok and Astra |
| Traders and authors | Larry Connors (RSI(2), Double 7), Kristjan Kullamägi (Qullamaggie), Milkman Trades, Saty Mahajan, Linda Raschke, Shen Lao (@shentrades), Azrael (15.87 Rule), David Trullas Vila, Echo (@EchoAnalysis), Julian Komar, ChartsLector, @PredictionAlgos, William O'Neil, Mebane Faber |
| Research and open code | Gatev (distance pairs); Gao, Han, Li and Zhou (intraday momentum); Amini and Singal (buybacks before earnings, via Quantpedia); QuantifiedStrat; trader.dev; StockCharts; LazyBear; Tomazetti; IU (TradingView); FinRL-X (AI4Finance), AlphaMemo, QuantaAlpha, AlphaQCM and Kronos; TimePortal (Polymarket tapes) |
