# griffith-gap-continuation - Recreation Package

Grade: PARTIAL (accounting) - code present in Test; see Files and Verification

## Provenance

- Canonical ID: `griffith-gap-continuation`
- Canonical name: Gap continuation (legacy setup)
- Aliases: griffith_gap_continuation
- Type: momentum; Family: griffith; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Gap continuation (legacy setup)" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Gap continuation (legacy setup)" (also docs/ALL-SLEEVES.md); Test catalog entry 'griffith-gap-continuation' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of strategies/griffith/griffith-gap-continuation.md and sleeves/griffith/griffith_intraday.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for this canonical id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record: entry: []; exit: []; filters: []; parameters: {}; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']. Where the accounting graded PARTIAL, the algorithm below is taken from the code and the strategy card in Test, which are the truth where they go beyond the accounting.

## What this strategy is

Gap continuation (legacy setup). Universe: SPY, QQQ, IWM, the SCOPE radar's top 100, held names; Asset: US equities; Timeframe: 1m (15-minute cycle).

Strategy card in Test (verbatim body):

Buys $100 of a scanned name holding a 2% gap above VWAP in a short uptrend, with a 1.5% stop and a 3% target.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk agentic runtime, SetupAgents gap_continuation |
| **Asset** | US equities |
| **Timeframe** | 1m (15-minute cycle) |
| **Universe** | SPY, QQQ, IWM, the SCOPE radar's top 100, held names |
| **Style** | Gap continuation |
| **Status** | live |

## Entry

- Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread ≤ 0.6%; score = 0.8 × |gap| + |intraday move| + min(relative volume, 5) + log10(dollar volume) / 3.
- The 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars.
- Setup, when neither a breakout nor a VWAP pullback: a gap ≥ 2%, price above VWAP and EMA 9 > EMA 20 (+2 points).
- BUY: scan + headline + setup points ≥ 5, price not over EMA 20 + 2.5 × max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%.
- Order: $100 (round(100 / price, 6) shares) as a DAY limit at the price × 1.001; at most 30 positions, never a held or working name.

## Exit

- Stop 1.5% under the entry, target 3% over it.

## Sizing

- $100 a trade.

## Data

- Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes).

## Code

- **Master desk**: `sleeves/griffith/griffith_intraday.py`; not in this repo: `desk/vendor/griffith/config.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)

## Full algorithm

Evaluation order in sleeves/griffith/griffith_intraday.py (legacy_cycle / SetupAgents; SETUP map names this sleeve gap_continuation; one agentic cycle every 15 minutes):
1. Broad scan: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names. Keep price $5-1,000 and spread <= 0.6% (on Yahoo quotes without keys the spread filter passes). Scan score = 0.8 x |gap| + |intraday move| + min(relative volume, 5) + log10(dollar volume) / 3.
2. Headline funnel: the 15 best by scan score get a headline score (positive words minus negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars.
3. Setup selection (decide()): momentum_breakout first, else vwap_pullback, else gap_continuation. Gap continuation applies when neither of the first two does: gap >= 2%, price above VWAP, and EMA 9 > EMA 20 (+2 points).
4. BUY gate: scan + headline + setup points >= 5; price not over EMA 20 + 2.5 x max(ATR, 0.2% of price) (anti-chase); and the SPY / QQQ / IWM average day not under -0.6%.
5. Order: $100 notional, round(100 / price, 6) shares, DAY limit at price x 1.001; at most 30 positions; never a held or working name.
Exit: stop 1.5% under entry, target 3% over entry (bracket). No other exit is recorded for this setup in the code path or the strategy card.
Note from the strategy card: `desk/vendor/griffith/config.json` is named as not in this repo; the setup parameters above are the values carried in the ported code and the card.

## Files in this repo

- Strategy card: `strategies/griffith/griffith-gap-continuation.md` (in Test)
- Sleeve: `sleeves/griffith/griffith_intraday.py` (in Test; SetupAgents legacy cycle)
- Feeds: `sleeves/griffith/feedlib/griffith.py`, `sleeves/griffith/feedlib/griffith_intraday.py` (in Test)
- Vendor lab source also in Test: `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py`

## Configuration

- Setup id: gap_continuation (sleeve id griffith_gap_continuation). Cycle: 15 minutes. Universe: SPY, QQQ, IWM, SCOPE radar top 100, held names.
- Own parameters: gap >= 2%, total score >= 5, anti-chase cap EMA20 + 2.5 x max(ATR, 0.2% of price), regime floor -0.6% average index day, price band $5-1,000, spread <= 0.6%, $100 a trade, limit price x 1.001, DAY, max 30 positions, stop -1.5%, target +3%.
- Source config file desk/vendor/griffith/config.json: not in the record (not present in Test).

## Data inputs

Alpaca IEX snapshots, news headlines, and 1-minute bars (last 200 completed bars for judged names); Yahoo quotes fallback without keys.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the configuration in the Configuration section against the code constants and, where one exists, the config/sleeves.json row.
3. Wire the data inputs named in Data inputs so the sleeve receives them at evaluation time in the form the code expects.
4. Register / enable the sleeve in the host desk exactly as its code entry point expects (see the strategy card Code section).
5. Run one evaluation on fixture data and confirm the emitted behaviour matches the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this canonical strategy is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Setup check: a fixture with gap >= 2%, price above VWAP, EMA9 > EMA20, and neither breakout nor VWAP-pullback setup selected, is classified gap_continuation.
- Gate check: total points < 5, price above the anti-chase cap, or index average day under -0.6% each produce no buy.
- Order check: quantity equals round(100 / price, 6), limit equals price x 1.001, DAY; a held or working name is never re-bought; the 30-position cap holds.
- Bracket check: stop = entry x 0.985, target = entry x 1.03.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
