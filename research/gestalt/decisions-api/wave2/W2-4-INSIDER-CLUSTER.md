# W2-4 INSIDER CLUSTER SIGNAL (Alpha Hunt Wave 2)

SCOPE: Surface: a new graded family built from EDGAR Form 4 insider
purchases, in the wave2 research lane and one registration file.
Constraints: no desk tree edits, paper and shadow only, recipe from
frontier dive one applied exactly. Outcome: corpus built on this box,
clusters extracted, next open replay at 10, 30 and 60 sessions against
SPY and QQQ, fleet admission exam run, shadow registered with a named
losing counterparty and a dated falsifier. Proof: corpus files,
insider_day_purchases.csv, clusters_registered.csv, replay.csv and
results.json in this folder, all produced by the rerunnable scripts
work/build_corpus2.py and work/analyze.py. Edges: EDGAR fair access
respected throughout (declared User-Agent "MidnaResearch
admin@example.com", request spacing, every response cached locally);
the first per filing XML route ran at roughly 0.4 requests per second
through the proxy and was replaced by the SEC structured Form 345
bulk route joined to the submissions route, per Route Failure is not
Task Impossibility.

## 1. Corpus

Universe: the Focus 30 from the gestalt pre-read record (SMH, SOXX,
NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, COHR,
LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, BE, OKLO,
VST, CEG, XLE, plus SIVE named in the task brief). Four names have no
Form 4 issuer corpus and are excluded by name: SMH, SOXX and XLE are
funds (no CIK in the SEC company tickers file, no insider issuer
filings), and SIVE is a Swedish listing with no SEC CIK. The served
universe is 26 operating issuers.

Routes: (a) EDGAR submissions route per issuer (data.sec.gov
submissions JSON, recent block plus every history file back to the
window start), giving the filing census and the ACCEPTANCE timestamp
for every Form 4; (b) the SEC insider transactions data sets
(structured Form 345 bulk files, quarterly zips), giving SUBMISSION,
REPORTINGOWNER and NONDERIV_TRANS rows, joined to (a) on accession
number. Window actually achieved: submissions census 2019-04-01 to
2026-11-14; bulk transaction rows 2019q2 through 2026q3, so the last
transaction quarter ends 2026-09-30 (the 2026q4 bulk set is not yet
published; filings after 2026-09-30 are counted in the census and
carry no transaction rows yet). Prices: Yahoo Finance daily OHLC,
split adjusted, 2019-04-01 to 2026-11-13, cached per ticker in
corpus/prices/ (late listings start at their first session: ARM
2023-09-14, SNDK 2025-02-13, CRWV 2025-03-28, ALAB 2024-03-20, CRDO
2022-01-27, CEG 2022-01-19, PLTR 2020-09-30).

| Corpus count | Value |
| --- | --- |
| Form 4 filings, submissions census, 26 issuers, 2019-04-01 to 2026-11-14 | 9,206 |
| Form 4 submissions present in bulk sets (through 2026q3) | 8,949 |
| Bulk submissions carrying non-derivative transaction rows | 8,173 |
| Non-derivative transaction rows extracted | 26,489 |
| Rows with an acceptance timestamp matched from the submissions route | 26,489 of 26,489 |
| Code P and acquired rows | 488 |
| Code P filings | 396 |
| Insider day purchases after aggregating rows by issuer, acceptance date and owner | 396 |

Per issuer filing census (submissions route): NVDA 666, WDC 610,
PLTR 527, AMD 519, CRDO 514, BE 506, MU 500, CRWV 487, MRVL 476,
LITE 471, AAOI 454, COHR 404, AVGO 400, VST 372, AMAT 302, TSM 288,
EOSE 271, FCEL 268, CEG 214, ALAB 185, RKLB 184, OKLO 151, FLNC 145,
AXTI 141, SNDK 117, ARM 34.

### Recipe fields: availability, substitutes, exclusions

| Recipe field | Status |
| --- | --- |
| Transaction code P, acquired code A | Present in NONDERIV_TRANS (TRANS_CODE, TRANS_ACQUIRED_DISP_CD). Applied exactly. |
| Acceptance timestamp | Present in the submissions route (acceptanceDateTime), joined on accession. Applied exactly; transaction date is never used for timing. |
| 10b5-1 flag (aff10b5One) | Present at FILING level as AFF10B5ONE in the bulk SUBMISSION table, but only from the 2023q1 bulk set onward (the Form 4 checkbox itself dates from the SEC 2023 amendment). Encodings observed across focus issuers 2023 onward: 0 (3,244 filings), blank (3,453), 1 (1,311), false (741), true (200), so the filter is live in general. Among the 488 code P rows the values are only 0 (313), blank (165) and false (10): ZERO code P purchases in this universe were flagged, so the drop rule removed 0 rows. For 2019 to 2022 the field is UNAVAILABLE in the structured set; those rows are kept with the flag recorded as unavailable, which is a named limitation, not a fabricated value: a pre 2023 filing could in principle describe a plan trade in footnote text (FOOTNOTES.tsv is in the corpus zips but was not parsed for this pass). |
| Distinct insider identity | REPORTINGOWNER RPTOWNERCIK per filing. Applied exactly. |
| Aggregate value | TRANS_SHARES times TRANS_PRICEPERSHARE per row, summed. Present. |
| Prices for replay | Not an EDGAR field; Yahoo Finance daily bars as stated above. |

## 2. Cluster census

Recipe applied exactly: at least 2 distinct insiders, same issuer,
acceptance dates inside one 5 calendar day window, aggregate at
least $100,000, greedy non-overlapping scan in acceptance order (a
purchase consumed by a completed cluster is not reused; purchases
left in a failed window are rescanned from the next purchase).
Result: 46 clusters, 2019-06-20 to 2026-09-22, on 8 of 26 names:
VST 13, FLNC 9, TSM 9, EOSE 8, AAOI 3, MRVL 2, ALAB 1, CRDO 1. The
other 18 issuers produced code P purchases but no qualifying
cluster. Two named shapes inside the census: (a) the TSM rows from
2026-04 to 2026-09 with 25 to 28 insiders and aggregate values of
$101,956 to $104,050 are a monthly cadence of very small purchases
(about $4,000 per insider) that clear the $100,000 bar only in
aggregate; the recipe carries no per insider minimum, so they are
kept and flagged here rather than silently removed; (b) the EOSE
2020-11-12 cluster ($22,888,915) is two B. Riley entities buying at
the Eos de-SPAC close, a financing event wearing cluster clothing;
kept per recipe, named here, and it is the single largest positive
10 day outcome in the replay, so the headline means lean on it and
the medians below are the honest center.

| Ticker | Cluster complete (acceptance) | Insiders | Aggregate | Entry (next open) | 10d excess vs SPY | 30d excess vs SPY | 60d excess vs SPY |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AAOI | 2024-03-18 | 2 | $547,534 | 2024-03-19 | -1.11% | -24.33% | -27.60% |
| AAOI | 2025-08-14 | 2 | $829,113 | 2025-08-15 | +16.32% | +15.61% | +27.03% |
| AAOI | 2025-08-15 | 2 | $345,882 | 2025-08-18 | +5.79% | +10.53% | +5.49% |
| ALAB | 2024-03-22 | 2 | $540,000 | 2024-03-25 | -4.62% | +6.95% | -14.11% |
| CRDO | 2022-02-02 | 2 | $101,500 | 2022-02-03 | +14.86% | +8.90% | -7.95% |
| EOSE | 2020-11-12 | 2 | $22,887,915 | 2020-11-13 | +38.95% | +107.12% | +124.16% |
| EOSE | 2022-03-02 | 3 | $197,275 | 2022-03-03 | +3.36% | +6.66% | -45.65% |
| EOSE | 2022-03-02 | 2 | $107,876 | 2022-03-03 | +3.36% | +6.66% | -45.65% |
| EOSE | 2022-03-07 | 4 | $104,212 | 2022-03-08 | +29.78% | -13.52% | -55.90% |
| EOSE | 2022-05-13 | 2 | $198,100 | 2022-05-16 | +3.22% | +4.02% | +86.33% |
| EOSE | 2022-05-13 | 2 | $123,100 | 2022-05-16 | +3.22% | +4.02% | +86.33% |
| EOSE | 2022-11-14 | 2 | $125,014 | 2022-11-15 | -16.22% | -7.60% | +4.58% |
| EOSE | 2026-03-04 | 2 | $435,600 | 2026-03-05 | -17.85% | +3.71% | +15.47% |
| FLNC | 2021-11-02 | 2 | $308,000 | 2021-11-03 | +2.01% | -13.27% | -47.47% |
| FLNC | 2021-11-03 | 2 | $140,000 | 2021-11-04 | -1.83% | -16.48% | -45.17% |
| FLNC | 2022-02-17 | 2 | $369,500 | 2022-02-18 | -22.92% | -0.56% | -33.60% |
| FLNC | 2022-02-24 | 2 | $256,350 | 2022-02-25 | -1.70% | -7.36% | -19.19% |
| FLNC | 2024-03-04 | 2 | $149,119 | 2024-03-05 | -7.58% | +6.74% | +57.15% |
| FLNC | 2025-02-14 | 2 | $261,500 | 2025-02-18 | -19.11% | -20.14% | -10.91% |
| FLNC | 2025-02-18 | 2 | $160,156 | 2025-02-19 | -21.43% | -24.59% | -19.81% |
| FLNC | 2025-02-20 | 2 | $149,370 | 2025-02-21 | -24.44% | -31.18% | -26.32% |
| FLNC | 2026-09-22 | 2 | $125,120 | 2026-09-23 | +5.87% | -24.58% | n/a |
| MRVL | 2025-09-25 | 2 | $1,313,726 | 2025-09-26 | +8.09% | +11.43% | -1.33% |
| MRVL | 2025-09-25 | 2 | $795,906 | 2025-09-26 | +8.09% | +11.43% | -1.33% |
| TSM | 2026-03-31 | 2 | $167,040 | 2026-04-01 | +1.93% | +2.63% | +14.14% |
| TSM | 2026-04-01 | 2 | $486,210 | 2026-04-02 | +2.53% | +11.97% | +24.51% |
| TSM | 2026-04-13 | 26 | $102,604 | 2026-04-14 | +2.75% | -0.47% | +5.87% |
| TSM | 2026-05-11 | 25 | $102,918 | 2026-05-12 | +1.70% | +11.23% | +0.74% |
| TSM | 2026-06-09 | 25 | $102,385 | 2026-06-10 | +6.41% | -0.36% | -4.79% |
| TSM | 2026-07-09 | 28 | $104,050 | 2026-07-10 | -3.52% | -6.67% | +5.34% |
| TSM | 2026-07-23 | 2 | $663,490 | 2026-07-24 | -2.50% | -3.42% | -3.14% |
| TSM | 2026-08-10 | 26 | $103,001 | 2026-08-11 | -1.99% | +6.60% | -2.07% |
| TSM | 2026-09-09 | 25 | $101,956 | 2026-09-10 | +3.33% | -0.81% | n/a |
| VST | 2019-06-20 | 2 | $800,290 | 2019-06-21 | -8.47% | -8.55% | +7.56% |
| VST | 2020-03-05 | 2 | $303,580 | 2020-03-06 | -10.72% | -9.78% | +0.84% |
| VST | 2020-03-12 | 2 | $187,400 | 2020-03-13 | +3.08% | +9.41% | +19.82% |
| VST | 2020-03-24 | 2 | $358,200 | 2020-03-25 | +3.50% | +8.94% | +11.83% |
| VST | 2020-12-21 | 2 | $666,450 | 2020-12-22 | +12.63% | +13.70% | -8.52% |
| VST | 2021-03-05 | 2 | $246,840 | 2021-03-08 | -5.61% | -9.20% | -18.17% |
| VST | 2021-03-05 | 2 | $665,600 | 2021-03-08 | -5.61% | -9.20% | -18.17% |
| VST | 2021-05-11 | 2 | $406,914 | 2021-05-12 | -2.78% | +5.76% | +4.29% |
| VST | 2021-05-11 | 2 | $851,400 | 2021-05-12 | -2.78% | +5.76% | +4.29% |
| VST | 2022-06-16 | 2 | $1,208,860 | 2022-06-17 | -0.76% | +0.08% | +3.23% |
| VST | 2022-06-21 | 2 | $405,142 | 2022-06-22 | -6.72% | +1.63% | +7.80% |
| VST | 2023-03-13 | 2 | $709,700 | 2023-03-14 | -7.63% | -9.48% | -7.39% |
| VST | 2023-03-17 | 2 | $439,630 | 2023-03-20 | -9.24% | -13.08% | -12.63% |

Insider names per cluster are in clusters_registered.csv (column
insiders); the table above carries the census in compact form.

## 3. Replay

Entry at the next session's open after the cluster completes; exit
at the close of session 10, 30 or 60 counting the entry session as
session one; benchmark return measured open to close over the same
two dates. Cost assumption, stated because no estate trading
haircut is documented in the hunt records (the H1 conveyor ran
gross and said so): 10 bp round trip deducted from the stock leg
only. McLean and Pontiff planning haircuts (0.42 published, 0.74
private) are not transaction costs and are not applied here.

| Horizon | n | Mean net return | Median | Win rate | Mean excess vs SPY | t | Mean excess vs QQQ | t |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 sessions (primary) | 46 | +0.19% | +1.91% | 54.3% | minus 0.57% | minus 0.32 | minus 0.73% | minus 0.43 |
| 30 sessions | 46 | +2.97% | +4.21% | 58.7% | +0.58% | +0.20 | minus 0.40% | minus 0.14 |
| 60 sessions | 44 | +4.95% | +1.86% | 59.1% | +0.91% | +0.17 | minus 0.47% | minus 0.09 |

Reading: the modern study's cluster premium (+2.41 percent excess
at 10 days, gone by 30, negative at 60 to 90) does NOT replicate on
this universe. At the primary horizon the cluster portfolio trails
both benchmarks on average despite a positive median, because the
left tail (four FLNC clusters at minus 19 to minus 24 percent
excess in Feb 2022 and Feb 2025) outweighs the right tail. At 30
and 60 sessions the raw returns rise with the tape while the SPY
excess stays near zero and the QQQ excess stays negative, the
opposite ordering from the study's decay shape, and no horizon
reading is anywhere near significance. Full per event rows are in
replay.csv.

## 4. Fleet admission exam

Tool: tools/admission_exam.py, run as its test file demonstrates,
is_new_family True (hurdle |t| above 3). Trial family, declared:
7 columns built from the same corpus (registered 2 in 5d $100k
hold 10; 2 in 7d $100k hold 10; 3 in 5d $100k hold 10; 2 in 5d
$250k hold 10; 2 in 5d $50k hold 10; single insider $100k hold 10
as the control; registered parameters hold 20), daily equal weight
portfolio series on the SPY calendar 2019-04-01 to 2026-11-13,
cost charged on each entry day. Honest trial count 21 (7 variants
times the 3 horizon readings taken in this pass).

| Number | Value |
| --- | --- |
| Family verdict | REJECT |
| Registered variant Sharpe (annualized) | 0.208 |
| Registered variant DSR | 0.579 (bar 0.95) |
| Registered variant |t| of mean daily return | 0.57 (new family hurdle 3) |
| Effective trials N_eff | 3.0 (raw 21; the 7 columns cluster to 1 correlation cluster, scaled by the exam's stated estimator) |
| SR0, expected max Sharpe under the null | 0.137 annualized |
| CPCV PBO | 0.244 (promote bar below 0.2, kill bar above 0.5; neither met) |
| SPA p versus SPY | 0.442 (statistic 0.756) |
| SPA p versus QQQ | 0.707 (statistic 0.201) |
| Variant DSR range | 0.434 (big $250k) to 0.879 (single insider control) |
| Variant events | registered 46, wide 50, strict 26, big 29, loose 56, single control 147, hold 20 form 46 |

One uncomfortable row, stated plainly: the single insider control
outscores every cluster variant on DSR (0.879) and Sharpe (0.551),
which on this universe argues the cluster condition is not the
active ingredient. It still fails every promotion bar. No variant
promotes; the family is not killed (PBO 0.244 is below the 0.5
kill bar on a fair 7 column family).

## 5. Registration

Shadow registered at
~/workspace/midna-book/strategy-candidates/2026-11-14-insider-cluster.md
(CAND-INSIDER-CLUSTER-01): full rules, the L9 opponent line naming
the impatient outside holder and accommodating liquidity providers
selling into the insiders' window as the losing counterparty, and
a falsifier dated 2027-05-14 (kill if the forward 10 session mean
excess versus SPY is at or below zero by that date or after 20
forward clusters, or forward DSR stays below 0.50). Forward shadow
starts Mon 2026-11-16, paper only.

STATUS: PARTIAL. Evidence pointer: this folder (corpus/ with the
cached EDGAR responses and bulk zips, clusters_registered.csv with
46 rows, replay.csv with 46 rows, results.json with the exam
record). Proven: corpus, census, replay and exam on the final
artifacts, registration filed. Open by name: the 2026q4 bulk gap
(filings after 2026-09-30 counted, transactions pending the bulk
set), the pre 2023 10b5-1 field unavailability, and the forward
shadow itself, which is the only instrument that can now promote
or kill this family.
