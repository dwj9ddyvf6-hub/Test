# femto-blowoff - Recreation Package

Grade: PARTIAL (accounting) - code present in Test; see Files and Verification

## Provenance

- Canonical ID: `femto-blowoff`
- Canonical name: R4 blowoff (daily / hourly)
- Aliases: femto_blowoff_1h, femto_blowoff_d
- Type: other; Family: femto; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "R4 blowoff (daily / hourly)" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "R4 blowoff (daily / hourly)" (also docs/ALL-SLEEVES.md); Test catalog entry 'femto-blowoff' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of strategies/femto/femto-blowoff.md, sleeves/femto/blowoff_1h.py, sleeves/femto/blowoff_d.py, sleeves/femto/feedlib/blowoff.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for this canonical id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record: entry: []; exit: []; filters: []; parameters: {}; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']. Where the accounting graded PARTIAL, the algorithm below is taken from the code and the strategy card in Test, which are the truth where they go beyond the accounting.

## What this strategy is

R4 blowoff (daily / hourly). Universe: 1,838-name research genome (daily) · 41-name old-desk basket (hourly); Asset: US equities; Timeframe: 1d · 1h.

Strategy card in Test (verbatim body):

Buys a rising-edge RSI + OBV blowoff (both in the top tenth of their 144-bar range) and holds 20 bars.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's R4 blowoff sleeves, via Femto-lean; detector after an @PredictionAlgos video |
| **Asset** | US equities |
| **Timeframe** | 1d · 1h |
| **Universe** | 1,838-name research genome (daily) · 41-name old-desk basket (hourly) |
| **Style** | Exhaustion (forward test) |
| **Status** | 1 live · 1 waiting |

## Entry

- Signal: Wilder RSI(14) and OBV both ≥ their trailing 144-bar min + 90% of the range; the first bar of each run.
- Daily: the edge on the latest closed bar, ≥ 252 bars, ≥ 20 sessions after the name's last signal, only while SPY's 60-session return is ≤ 0; ranked from 16:30 ET, bought from 10:30 ET the next session.
- Hourly: an edge in the last 5 closed regular-hours bars, ≥ 160 bars, ≥ 20 bars after the last signal; scans at :10, buys at :40, 10:00-15:59 ET.

## Exit

- Daily: sold once 19 bars have closed after entry (the 20th session); backstop 28 days. No stop.
- Hourly: sold 20 hourly bars after the bar that follows the signal; backstop 4 days. No stop.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Daily split-adjusted bars (600, cached) with the genome job's last-close blowoff rows; regular-hours hourly bars (400); desk quotes.

## Code

- **Master desk**: `sleeves/femto/blowoff_d.py`, `sleeves/femto/blowoff_1h.py`, `sleeves/femto/sleeve_core.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`, `sleeves/femto/vendor/old_desk_research/run_r4_blowoff_standalone.py`, `sleeves/femto/feedlib/blowoff.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- The old desk switched both off on 2026-10-08 (they buy exhaustion tops); the master desk runs them as a forward test.
- The RSI x OBV detector reconstructs the method shown in an @PredictionAlgos video.

## Full algorithm

Detector (sleeves/femto/feedlib/blowoff.py, vendored byte-identical from the old desk research code): Wilder RSI(14) and OBV each at or above trailing-144-bar min + 90% of range; rising edge only (first bar of each run). Daily form uses rsiobv.scan_exhaustion (rsi_period=14, range_lookback=144); hourly form uses blowoff_indices_vec on closes and volumes.

Daily sleeve (sleeves/femto/blowoff_d.py; HOLD_BARS=20, DEOVERLAP_BARS=20, MIN_BARS=252, COST_BPS_SIDE=0.001, RANK 16:30 ET, FILL 10:30 ET, cadence_s=1800):
1. Rank phase (at/after 16:30 ET, once per session): read the genome job's last-close blowoff rows (context.extra blowoff_events). Regime gate: SPY trailing-60-session return <= 0 (spy_down_regime needs >= 61 SPY bars); if SPY is not down, no signals.
2. A name signals when its event row date equals today and its signal date is set, it is not SPY, it has >= 252 bars, and the session gap since its last signal is >= 20 (de-overlap).
3. Sells staged: a held name whose entry_date is followed by >= 19 closed bars (HOLD_BARS-1) is sold (the 20th session). Exit backstop date = rank date + 28 days. No disaster stop.
4. Buys staged in sorted order, skipping held names, capped so buys + surviving pending buys + book <= sleeve_core MAX_POSITIONS (10 per the strategy card). Pending state carries buys, sells, exit_dates, last_signal.
5. Fill phase (10:30 ET to 16:00 ET): core.fill_intents / core.fill apply the sleeve_core fill law (strategy card: budget = 30% of the book less held and working notional, split over staged buys; whole shares at a fresh mid plus cost, at least 1; cost modeled 10 bps a side; $100,000 book per sleeve).

Hourly sleeve (sleeves/femto/blowoff_1h.py; HOLD_BARS=20, DEOVERLAP_BARS=20, MIN_BARS=160, COST_BPS_SIDE=0.001, FORMING_S=65*60, cadence_s=600):
1. Phase gate: weekdays only, 10:00-15:59 ET; minutes < 30 are scan, otherwise fill. Bars are closed only when bar time + 65 minutes <= now.
2. Scan: for each basket name with >= 160 closed regular-hours bars, rising edges in the last 5 closed bars, excluding the recorded signal bar and any edge < 20 bars after the recorded anchor, become signals.
3. Sells staged: a held name is sold once >= 20 hourly bars have closed after its entry bar (entry bar = the bar after the signal bar). Exit backstop = today + 4 days. No disaster stop.
4. Buys staged skipping held names under the same MAX_POSITIONS cap; fill phase at :40 applies the same sleeve_core fill law at 10 bps a side.
Both sleeves were switched off in the old desk on 2026-10-08 (they buy exhaustion tops) and run in the master desk as a forward test with the law unchanged.

## Files in this repo

- Strategy card: `strategies/femto/femto-blowoff.md` (in Test)
- Daily sleeve: `sleeves/femto/blowoff_d.py` (in Test)
- Hourly sleeve: `sleeves/femto/blowoff_1h.py` (in Test)
- Detector loader: `sleeves/femto/feedlib/blowoff.py` (in Test)
- Fill law: `sleeves/femto/sleeve_core.py` (in Test)
- Vendored detector: `sleeves/femto/vendor/old_desk_research/rsiobv.py` and `sleeves/femto/vendor/old_desk_research/run_r4_blowoff_standalone.py` (in Test)
- Parity mirrors in Test: `packages/claude/master-desk-parity-tools/tools/parity/blowoff_1h.py`, `packages/claude/master-desk-parity-tools/tools/parity/blowoff_d.py`, `packages/claude/master-desk-feedlib/desk/feedlib/blowoff.py`

## Configuration

- No config/sleeves.json v3 roster row for the femto master-desk sleeves was found in the fetched config; the sleeves carry their own CONFIG: blowoff_d SleeveConfig(sleeve_id="blowoff_d", cadence_s=1800), blowoff_1h SleeveConfig(sleeve_id="blowoff_1h", cadence_s=600); universe empty in CONFIG (supplied at runtime), risk_pct None.
- Own parameters: RSI period 14, range lookback 144, threshold 90% of range, HOLD_BARS 20, DEOVERLAP_BARS 20, MIN_BARS 252 (daily) / 160 (hourly), cost 10 bps a side (0.001), SPY 60-session regime gate (daily only).
- Book: $100,000 per sleeve (strategy card).

## Data inputs

Daily: split-adjusted daily bars (600, cached) for the 1,838-name research genome, plus the genome job's last-close blowoff rows (cache/blowoff_events.json via feedlib load/run, rows only when the file date equals the session). Hourly: regular-hours 1h bars (400) for the 41-name old-desk basket via context.extra bars_1h. Both: desk quotes and sleeve_state via context.extra; SPY daily bars for the daily regime gate.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the configuration in the Configuration section against the code constants and, where one exists, the config/sleeves.json row.
3. Wire the data inputs named in Data inputs so the sleeve receives them at evaluation time in the form the code expects.
4. Register / enable the sleeve in the host desk exactly as its code entry point expects (see the strategy card Code section).
5. Run one evaluation on fixture data and confirm the emitted behaviour matches the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this canonical strategy is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Detector check: on a fixture series, an index is a signal only when RSI(14) and OBV are both >= min + 0.9 x range over 144 bars and the previous bar is not also in that state (rising edge).
- Daily regime check: with SPY 60-session return > 0, rank stages no buys; with it <= 0 and a same-day event row, the name is staged.
- De-overlap check: a second signal < 20 sessions (daily) or < 20 bars (hourly) after the recorded signal is ignored.
- Hold check: daily exits stage at 19 bars closed after entry; hourly exits stage at 20 bars after the entry bar; no stop intent exists in either sleeve.
- Fill check: staged buys respect the 10-position cap and whole-share sizing under the sleeve_core fill law at 10 bps a side.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
