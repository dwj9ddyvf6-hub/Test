# qm-parabolic-short: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "Qullamaggie parabolic short", type mean reversion, family qullamaggie. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Qullamaggie parabolic short" (also docs/ALL-SLEEVES.md); Test catalog entry 'qm-parabolic-short' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/qullamaggie/qullamaggie.py (setup qm_parabolic_short) + sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py.

## What this strategy is

Qullamaggie parabolic short Type: mean reversion; family: qullamaggie. Universe: 1,838-name genome. Asset class: US equities. Timeframe: 1d setup · 1m trigger. Creator / source: Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; the pass-3 research desk. Style evidence in the accounting: Parabolic short | Classification 2026-10-30: mean reversion (config evidence): Test catalog entry in accounting.json: style Parabolic short, 1d setup with 1m trigger on the genome roster; shorting an extended parabolic move is a reversal fade and no fuller rule text exists in consulted sources

## Full algorithm

Code truth (sleeves/qullamaggie/qullamaggie.py): sleeves() returns QullaSetup for qm_leader_breakout_pass3, qm_episodic_pivot and qm_parabolic_short; the parabolic setup is one setup per sleeve. short_candidates / short_ok use the config keys parabolic_up_days_min, parabolic_small_cap_runup_pct, parabolic_large_cap_runup_pct and parabolic_small_cap_threshold: at least the minimum consecutive up days and the 3-session run at or above the large-cap threshold, or at or above the small-cap threshold when market cap is at or below the small-cap threshold; a name with no market cap has no parabolic short (the source's metadata default). ma_target is max(10-day, 20-day SMA) of the completed closes before the session (None with fewer than 20). The module header records the same thresholds as the card: 3+ up closes, a 3-session run >= 50% (>= 300% at market cap <= $300M). The EDGAR catalyst and metadata producer (desk/feedlib/qm_inputs.py) is named on the card as not in this repo.

Strategy card record, in full:

Shorts a name after 3+ up days and a parabolic 3-session run when the opening-range low breaks under VWAP, and covers at its 10/20-day average.

| | |
|---|---|
| **Family** | Qullamaggie |
| **Source** | Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; the pass-3 research desk |
| **Asset** | US equities |
| **Timeframe** | 1d setup · 1m trigger |
| **Universe** | 1,838-name genome |
| **Style** | Parabolic short |
| **Status** | waiting |

## Entry

- Setup: ≥ 3 consecutive up closes and a 3-session run ≥ 50% (≥ 300% at a market cap ≤ $300M); borrowable; $5M dollar volume.
- Trigger: a bar's low reaches the opening-range low and closes under the session VWAP; short at the next bar's open, stop = the high before the fill.

## Exit

- Hard stop at that high.
- Covers at max(10-day, 20-day SMA) of the completed closes.
- After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven.
- After 3 sessions, a close above the 10-day SMA exits.

## Sizing

- Half the long risk: 0.175% of opening equity on the stressed loss per share; the same caps.

## Data

- Genome daily bars, 1-minute tapes, EDGAR share counts for the market cap.

## Code

- **Master desk (pass-3 research desk)**: `sleeves/qullamaggie/qullamaggie.py`, `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`. One setup per sleeve; the EDGAR catalyst and metadata producer (`desk/feedlib/qm_inputs.py`) is not in this repo
- **Rule lines**: [docs/verify/qullamaggie.md](../../docs/verify/qullamaggie.md)

## Files in this repo

- This package: docs/QM_PARABOLIC_SHORT-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/qullamaggie/qullamaggie.py (setup qm_parabolic_short) + sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Universe 1,838-name genome; timeframe 1d setup with 1m trigger; status waiting in the Test catalog. Sizing per the card: half the long risk, 0.175% of opening equity on the stressed loss per share, with the same caps as the family's long setups (the exact cap values are in the family code, not restated here beyond the card). Accounting grade PARTIAL with gaps entry/exit/sizing not recorded in its consulted sources; filled here from the card and code in this repo.

## Data inputs

Genome daily bars, 1-minute tapes, EDGAR share counts for the market cap (card).

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- No short without at least 3 consecutive up closes, the 3-session run threshold for its market-cap band (50%, or 300% at market cap <= $300M), borrowable status and $5M dollar volume; a name with no market cap is never a parabolic short.
- Trigger only when a bar's low reaches the opening-range low and closes under the session VWAP; the short is at the next bar's open with the stop at the high before the fill.
- Cover at max(10-day, 20-day SMA); hard stop at that high; after the third session held in profit, sell a third at the close and move the stop to breakeven; after 3 sessions a close above the 10-day SMA exits.
- Risk per trade is 0.175% of opening equity on the stressed loss per share.
