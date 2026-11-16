# Wave 3 Lane B1: Morgue Point-in-Time Short Interest as a Tested Signal

Verdict: NON-FIND, graded. Family verdict from the admission exam: KILL (PBO 0.778). Even on a lookahead-contaminated formation grain, the signal runs backwards against the literature direction in this universe and window. Numbers below; machine record in lane_b_b1.json.

## Census

- File: ~/workspace/morgue/output/short_interest_pit.jsonl (822 rows, exactly as the Alpha Hunt record stated). Location note: targeted finds in terminal-lineup and goals returned only short-VOLUME files, a different dataset the morgue code itself warns never to substitute. The PIT short-interest file lives in the morgue tree.
- Columns: symbol, settlement_date, si_shares, float_shares, float_basis, split_flag, publication_date, source.
- Universe: 34 symbols (ACHC, ALRM, AMPH, APA, ASO, CART, CBRL, CHRD, CROX, EGBN, EXEL, FTDR, FTRE, GO, HAS, HSTM, IPAR, KDP, MAT, NWE, PCRX, PGNY, PTEN, QLYS, TENB, TRUP, UFCS, URBN, VCEL, VIR, VRNS, VTRS, WAY, XNCR).
- Span and cadence: 25 settlement dates, 2025-10-15 to 2026-10-15, twice monthly (mid-month and month-end, the FINRA schedule). First two dates carry 20 symbols, the remaining 23 carry all 34.
- Rank field (exact): si_pct_float = si_shares / float_shares x 100, float basis EDGAR shares outstanding (declared in file). Range 0.79 to 34.91 percent, median 8.21 percent. All 822 rows split_flag false. Source on every row: Nasdaq short-interest table (FINRA SI republished).
- Point-in-time warning, decisive: only 3 publication dates exist in the file (2026-10-26: 29 rows, 2026-10-30: 471 rows, 2026-11-08: 322 rows). The history was backfilled into the store on those dates. Settlement-date formation is therefore not tradeable point-in-time; it is reported below as a descriptive association check only, and the publication-grain test is reported separately.

## Prices

The task-named sources cannot price this universe: 0 of 34 SI symbols are in the B2K folder, and only XNCR is in warm_bars.json. Forward returns use the morgue board bars (~/workspace/morgue/data_cache/board_bt_bars.json, 1,833 symbols, 414 sessions each for all 34 names plus SPY and QQQ, 2025-03-25 to 2026-11-13). Cross-check: board SPY closes equal the B2K split-adjusted SPY closes exactly (abs diff 0.0) on 2026-10-01, 2026-10-15, and 2026-11-06.

## Literature (2 searches, 2026-11-14)

- Cohen, Diether and Malloy (2007, Journal of Finance): shifts in shorting DEMAND predict returns; an increase in shorting demand leads to negative abnormal returns of 2.98 percent in the following month, stronger where public information flow is low. Akbas, Boehmer, Erturk and Sorescu: high short interest predicts negative abnormal returns, evidence favoring the informed-shorts (information) hypothesis over pure overvaluation. Boehmer, Jones and Zhang (2008) and Asquith, Pathak and Ritter (2005) point the same way: high SI, lower subsequent returns, concentrated on the short side and in smaller, less covered names.
- The caution: Asquith, Pathak and Ritter found value-weighted high-SI portfolios did not underperform, and a 2025 to 2026 study of the top 2,000 US equities 2007 to 2024 (Vernimmen-hosted MIF paper) finds the long-short gross alpha does not survive transaction and borrow costs at significance; quintile and long-only exclusion variants are the implementable residue. FINRA's May 2026 proposal to move to weekly SI reporting was withdrawn on 2026-08-05, so the twice-monthly cadence with publication lag remains the live constraint. In short: the published effect is real but small, cost-fragile, and fee/crowding-sensitive at the margin, exactly the earlier dives' caution.

## Event study, settlement grain (descriptive, lookahead-flagged)

23 formations (settlement dates with all 34 symbols), quintiles by si_pct_float, forward excess return vs SPY:

| Horizon | Q1 low SI | Q2 | Q3 | Q4 | Q5 high SI | Q1 minus Q5 | n per quintile |
|---|---|---|---|---|---|---|---|
| +10 sessions | +1.507% | +0.540% | +1.207% | +2.721% | +2.971% | -1.464% | 138 to 161 |
| +21 sessions | +2.599% | +0.184% | +2.358% | +4.776% | +6.149% | -3.551% | 138 to 161 |

The gradient runs the WRONG way for the literature hypothesis: the highest-SI quintile had the highest forward excess in this universe and window (a squeeze-prone mid-cap set in a rising tape is the obvious reading, stated as a reading, not a tested cause).

Avoidance test (a): mean forward return per formation, universe including vs excluding the top SI quintile: +10 sessions, including +2.183%, excluding +1.879% (excl minus incl -0.304%); +21 sessions, including +4.208%, excluding +3.452% (-0.757%). Avoiding high-SI names would have COST return here, not saved it.

## Event study, publication grain (point-in-time honest)

Formations at the 3 publication dates using the latest admitted reading per symbol (20, 20, and 34 symbols; third formation lands 2026-11-09). Only 2 formations have a full +10-session forward window inside the bars (counts 8 per quintile, 40 obs): Q1 -4.882%, Q2 -5.765%, Q3 -3.327%, Q4 -2.824%, Q5 -3.060% excess vs SPY; Q1 minus Q5 -1.822%. Avoidance at +10: including -4.889%, excluding -5.117% (excl minus incl -0.228%). No +21 window exists for any PIT formation (bars end 2026-11-13). This grain is far too small to grade a signal on; it agrees in sign with the settlement grain and nothing stronger is claimed.

## Admission exam (daily series, settlement grain)

Series: T = 267 sessions, 2025-11-17 to 2026-11-13 (first usable formation 2025-11-14). Columns: (1) long Q1 low SI minus short Q5 high SI, equal weight, reformed each settlement date; (2) avoidance excess, long universe-minus-Q5 minus full universe. trial_count 2, is_new_family true, benchmarks SPY and QQQ daily returns over the same sessions.

Full exam output:

- DSR: [0.044, 0.027] (bar 0.95)
- Annualized Sharpe: [-1.730, -1.944]
- t of mean: [-1.723, -1.936] (new-family bar |t| > 3)
- CPCV PBO: 0.778 (bar < 0.2; kill bar > 0.5)
- SPA p-values: SPY 0.503, QQQ 0.488 (bar < 0.05 against both)
- n_eff 1.0 (the two columns cluster as one trial), verdicts: KILL (family PBO > 0.5) for both columns, family verdict KILL.

Validity caveat printed with the exam in the JSON: formation uses settlement dates on a backfilled file, so a PROMOTE would not have been an honest find. A KILL on a series that had lookahead help is the stronger direction of evidence: even flattered, it does not clear any leg of the bar.

## Grade

B1 is a graded NON-FIND. The morgue SI file works as a veto input (its current use) but as a tested long-short or avoidance signal on its own universe it is negative-Sharpe, wrong-signed against its own literature in this window, and KILLed by the exam. No sleeve, no promotion, no dressing.

STATUS: PARTIAL for the territory as tasked (exam run and printed, event studies at both grains printed; the PIT grain is named as too small to grade on, +21 PIT windows do not exist in the bars). Evidence pointer: lane_b_b1.json in this folder, recounted from the artifacts named inside it.
