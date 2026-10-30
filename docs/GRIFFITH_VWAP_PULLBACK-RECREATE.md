# griffith-vwap-pullback: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "VWAP pullback (legacy setup)", type mean reversion, family griffith, style evidence "Intraday VWAP pullback", universe "SPY, QQQ, IWM, the SCOPE radar's top 100, held names", US equities, timeframe "1m (15-minute cycle)", creator "Griffith / Ledge desk agentic runtime, SetupAgents vwap_pullback". Test catalog entry `griffith-vwap-pullback`, status live (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/griffith/griffith-vwap-pullback.md`. The card does record entry, exit and sizing in full (quoted below), and names the running code in this repo. The accounting gaps are gaps of the accounting pass, not of this repo's record.

## What this strategy is

A legacy intraday setup: every 15 minutes it scans a radar universe, scores and headline-ranks candidates, and buys $100 of a name pulling back to VWAP in a short uptrend, with a 1.5% stop and a 3% target.

## Full algorithm

From the strategy card, in evaluation order:

1. Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread at most 0.6%; score = 0.8 x |gap| + |intraday move| + min(relative volume, 5) + log10(dollar volume) / 3.
2. Headline stage: the 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars.
3. Setup, when not a breakout: EMA 9 > EMA 20 and price within 0.4% of VWAP with RSI(14) < 68 (+2 points).
4. BUY gate: scan + headline + setup points at least 5, price not over EMA 20 + 2.5 x max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%.
5. Order: $100 (round(100 / price, 6) shares) as a DAY limit at price x 1.001; at most 30 positions, never a held or working name.
6. Exit: stop 1.5% under the entry, target 3% over it.
7. Sizing: $100 a trade.

## Files in this repo

- This package: `docs/GRIFFITH_VWAP_PULLBACK-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-vwap-pullback.md`
- Running code (already in Test; nothing vendored for this package), per the card: `sleeves/griffith/griffith_intraday.py`
- Named on the card as not in this repo: `desk/vendor/griffith/config.json` (the source desk's config; the card's parameters above are the recorded configuration).
- Rule lines referenced by the card: `docs/verify/griffith.md`

## Configuration

- Universe: SPY, QQQ, IWM, SCOPE radar top 100, held names. Timeframe 1m bars, 15-minute scan cycle.
- $100 per trade, DAY limit at price x 1.001, at most 30 positions, no held or working name re-bought.
- Stop -1.5%, target +3% from entry. Price band $5-1,000; spread cap 0.6% (on Yahoo quotes without keys the spread filter passes, per the card).

## Data inputs

Alpaca IEX snapshots, news and 1-minute bars (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs in `sleeves/griffith/griffith_intraday.py` (the SetupAgents vwap_pullback setup). Supply the desk config values recorded in Configuration (the source `config.json` itself is not in this repo, per the card).
3. Feed Alpaca IEX snapshots, news and 1-minute bars for the scan universe; run the 15-minute cycle.
4. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A candidate outside $5-1,000 or with spread over 0.6% is excluded before scoring; the scan score matches the recorded formula.
- Only the top 15 scanned names receive headline scores and only the top 8 are judged on bars.
- A judged name with EMA 9 at or below EMA 20, price more than 0.4% from VWAP, or RSI(14) at least 68 earns no setup points; a total under 5 points, a price over the EMA20 + 2.5 x max(ATR, 0.2% of price) cap, or an index average day under -0.6% blocks the buy.
- A buy is exactly round(100 / price, 6) shares as a DAY limit at price x 1.001; the 31st concurrent position and any held/working name are refused.
- The position exits at -1.5% (stop) or +3% (target) from entry.
