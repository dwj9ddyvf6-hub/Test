# qr-spectral-echo-drift: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "Spectral Echo Drift", type other, family quant_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Spectral Echo Drift" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-spectral-echo-drift' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/sed.py + sleeves/quant_research/vendor/quant_research/sed/engine.py + sleeves/quant_research/common.py.

## What this strategy is

Spectral Echo Drift Type: other; family: quant_research. Universe: 20 Nasdaq leaders. Asset class: US equities. Timeframe: 1m (from IEX quotes). Creator / source: Spectral Echo Drift, a desk research package (core model). Style evidence in the accounting: Order-book spectral | Classification 2026-10-30: other (config evidence): Test catalog entry in accounting.json records only style Order-book spectral, 1m from IEX quotes, status blocked; its code (master desk sed.py) is not in any consulted tree and no rule text exists, so no mechanism can be read

## Full algorithm

Code truth: sleeves/quant_research/sed.py carries SID qr_spectral_echo_drift, a Tape class and class SED(Sleeve) with cadence_s=30, universe the 20 names on the card and capital from its config starting NAV ($100,000 book per the card); sleeves() returns the SED sleeve. The card states this is the source's market-only core model and the social-attention gate is not computed. Accounting grade PARTIAL (its code was not in the accounting's consulted trees); the full rule is on the card and in the code in this repo.

Strategy card record, in full:

Intraday longs in 20 Nasdaq leaders when returns lead top-of-book pressure with high spectral coherence, held up to 30 minutes.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | Spectral Echo Drift, a desk research package (core model) |
| **Asset** | US equities |
| **Timeframe** | 1m (from IEX quotes) |
| **Universe** | 20 Nasdaq leaders |
| **Style** | Order-book spectral |
| **Status** | blocked |

## Entry

- Tape: IEX top-of-book updates for AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AVGO, AMD, NFLX, PLTR, MU, COST, INTC, QCOM, AMAT, ADBE, CSCO, PEP and LRCX, folded into minutes: the mid's open, high, low and close and the mean touch imbalance of every 12th update.
- Features: 1- and 3-minute mid returns over contiguous minutes, ATR(20) of the mid, the Katz fractal dimension of the last 32 closes, the latest confirmed fractal low; over the last 128 contiguous minutes, the coherence of imbalance and returns at the three strongest 2-20-minute peaks, the band's spectral entropy, and the lag (0-5 minutes) by which returns best lead imbalance changes.
- Signal: coherence > 0.82, a lag of 2-5 minutes with correlation ≥ 0.10, entropy falling two minutes running, imbalance > 0 and a positive 3-minute return, known before 15:50 ET; per minute the most coherent name.
- Gate: one position at a time; none after the day's loss reaches 1.2% of its starting NAV, or for a signal seen more than 3 minutes late.
- Order: an IOC limit at the ask of the first update at least 250 ms after the minute, refused when that update is more than 1 second late.

## Exit

- First of: the bid at or below the stop, coherence < 0.65, 30 minutes after the signal, 15:55 ET; sold at the market.

## Sizing

- $100,000 book: stop = max(the fractal low - 0.1 ATR, mid - (1 + 0.75 × (D - 1)) ATR) with D the fractal dimension; shares = min(0.4% of NAV / (ask - stop), 10% of NAV / ask, 5% of the displayed ask size).

## Data

- Alpaca's IEX quote stream for the 20 names (the session's tape plus the previous session's).

## Code

- **Master desk**: `sleeves/quant_research/sed.py`, `sleeves/quant_research/vendor/quant_research/sed/engine.py`, `sleeves/quant_research/common.py`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Notes

- This is the source's market-only core model; the social-attention gate is not computed.

## Files in this repo

- This package: docs/QR_SPECTRAL_ECHO_DRIFT-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/sed.py + sleeves/quant_research/vendor/quant_research/sed/engine.py + sleeves/quant_research/common.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Universe: the 20 Nasdaq leaders listed on the card (AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AVGO, AMD, NFLX, PLTR, MU, COST, INTC, QCOM, AMAT, ADBE, CSCO, PEP, LRCX); timeframe 1m from IEX quotes; $100,000 book; status blocked in the Test catalog. One position at a time; daily loss gate 1.2% of starting NAV.

## Data inputs

Alpaca's IEX quote stream for the 20 names (the session's tape plus the previous session's) (card).

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- No entry unless coherence > 0.82, lag 2-5 minutes with correlation >= 0.10, entropy falling two minutes running, imbalance > 0 and a positive 3-minute return, known before 15:50 ET; per minute only the most coherent name.
- No entry after the day's loss reaches 1.2% of starting NAV, for a signal seen more than 3 minutes late, or while a position is held.
- Entry is an IOC limit at the ask of the first update at least 250 ms after the minute, refused when that update is more than 1 second late.
- Exit is the first of: bid at or below the stop, coherence < 0.65, 30 minutes after the signal, 15:55 ET; sold at the market. Stop and sizing follow the card's fractal-low / ATR formula and its three caps.
