# Wave 3 Lane A: EDGAR Event Studies (Sat 2026-11-14 night)

STATUS: PARTIAL (bounded portion proven, rest named). No candidate clears the find bar. All numbers below recount from `lane_a_results.json` in this folder. No em dashes used. Paper and research only.

## Method (applies to A1 and A2)

- EDGAR route that answers: `https://efts.sec.gov/LATEST/search-index?q="phrase"&forms=8-K&dateRange=custom&startdt=2022-01-01&enddt=2026-11-06&from=N`, paginated at 100 hits per page, descriptive non-personal User-Agent, dates re-filtered client side.
- Routes that failed, recorded not hidden: `https://efts.sec.gov/LATEST/search` returned `Missing Authentication Token`; `https://www.sec.gov/cgi-srv/efts_search` returned a rate threshold page; `https://www.sec.gov/files/company_tickers.json` returned HTTP 403 from this host under two User-Agents. Fallback used: ticker parsed from the efts hit `display_names` field (the parenthesized ticker before the CIK tag), CIK carried from the hit itself. This is a route failure, not evidence the file does not exist.
- Universe: 100 symbol files in `biotech2k-rotation-tests-20261109/data/`, 98 non-benchmark symbols after removing SPY and QQQ. Window: filings 2022-01-01 to 2026-11-06. Dedupe: repeat announcements per firm within 12 months dropped (first kept).
- Event study: entry at the OPEN of the first session strictly after the filing date; forward return to the close at +5, +21, +63 sessions; excess return is the stock return minus the SPY return over the identical window (SPY entered at its open on the same entry date).
- Strategy series construction, exact: on each SPY trading day in the window (1217 days), the equal-weight mean daily close-to-close return of all events currently inside their holding window (21 or 63 sessions from entry), 0.0 (cash) on days with no active event. Benchmarks: SPY and QQQ daily close-to-close returns on the same calendar.
- Exam: `tools/admission_exam.py exam()`, trial matrix = the 4 constructed series (buyback hold63, buyback hold21, raises hold63, raises hold21), trial_count = 4, is_new_family = True. Family verdict REJECT.

## A1. Buyback announcements

Literature, 5 lines:
1. Ikenberry, Lakonishok and Vermaelen (1995): 1,239 open market repurchase announcements, 1980 to 1990, average abnormal four year buy and hold return 12.1 percent, 45.3 percent for value stocks, no drift for glamour stocks.
2. Peyer and Vermaelen (2009) confirm on 1991 to 2001 data, with the effect concentrated in small cap high book-to-market announcers and roughly zero for mega cap glamour names; beaten down pre-announcement price action predicts better than size or book-to-market alone.
3. Manconi, Peyer and Vermaelen (2019) find the anomaly internationally, stronger in less efficient markets and smaller firms.
4. Breaking point one: the anomaly lives in small and mid caps. This estate's bounded universe is 98 mega and large caps, exactly where the literature says the effect has decayed to roughly 0 to 2 percent over four years.
5. Breaking point two: announcements are not executions (Fried and Wang critique; programs with under 20 percent first year execution underperform), and a modern 430 company sample (2025 to 2026 announcements) shows mean excess of +1.51 percent at 5 sessions and +2.00 percent at 63 sessions but a negative median at 63 sessions, with the trimmed mean falling to +0.66 percent.

Cohort: 36 raw universe events across 10 phrases, 30 after the 12 month dedupe. Exactly at the 30 event floor, so the test ran but power is thin and that is stated, not hidden.

Event study (excess vs SPY, entry next session open):
- +5: n 30, mean +0.98 percent, median +1.14 percent, t 1.27, 60.0 percent positive.
- +21: n 30, mean +1.23 percent, median +0.58 percent, t 0.92, 56.7 percent positive.
- +63: n 30, mean +1.96 percent, median +0.59 percent, t 0.82, 50.0 percent positive.

Direction matches the literature's small positive drift; no horizon is significant, and the +63 median near zero matches the modern decay evidence for large caps.

Exam, A1_buyback_hold63: Sharpe (ann) 1.071, DSR 0.985, t 2.35, n 1217 days. Fails on PBO 0.400 (bar under 0.2), SPA p 0.300 vs SPY and 0.378 vs QQQ (bar under 0.05 both), and |t| 2.35 (bar over 3, new family). The Sharpe is flattered by long cash stretches in a sparse event portfolio; SPA against both benchmarks is the honest leg and it does not reject.
Exam, A1_buyback_hold21: Sharpe (ann) 0.570, DSR 0.841, t 1.25. Fails DSR, PBO, SPA, and the t hurdle.

Verdict A1: graded NON-FIND. Positive but insignificant drift in a 30 event large cap cohort; the one leg that passes (DSR on hold63) does not rescue the three that fail.

## A2. Guidance revisions from 8-K text

Miner delivered in the run script logic and embodied in `lane_a_results.json` (phrase sets, per phrase hit counts recorded in the run log summary): raises set of 9 phrases (raises full-year, raises guidance, raised its full-year, increased its full-year guidance, and kin), cuts set of 10 phrases (lowers full-year, lowered its full-year, reduced its full-year guidance, cut its full-year guidance, and kin).

Cohort counts per direction: raises 80 raw, 45 after dedupe. Cuts 1 raw, 1 after dedupe.

Raises event study (excess vs SPY, entry next session open):
- +5: n 45, mean -0.32 percent, median -0.16 percent, t -0.67.
- +21: n 43, mean -0.27 percent, median -1.16 percent, t -0.32.
- +63: n 43, mean -1.10 percent, median -3.68 percent, t -0.48.

Exam, A2_raises_hold63: Sharpe (ann) 0.410, DSR 0.715, t 0.90, SPA p 0.300 vs SPY and 0.378 vs QQQ (family legs), PBO 0.400. REJECT on every leg.
Exam, A2_raises_hold21: Sharpe (ann) 0.595, DSR 0.837, t 1.31. REJECT on every leg.

Verdict A2 raises: graded NON-FIND, and worse than null. Guidance raises in this mega cap universe are already priced by the next session open; the forward drift is negative at every horizon.

Named defect, cuts cohort: the phrase miner cannot build a cuts cohort in this universe (1 event). Large cap guidance cuts are typically phrased as "now expects", "updates outlook", or numeric range revisions inside earnings releases, which a phrase miner cannot sign reliably without parsing the numbers against the prior guide. Delivering the miner and the count instead of a forced test, per the lane instructions. Unblocker: a numeric guidance parser (extract current guide range, compare to the firm's previous 8-K guide) or a licensed guidance revisions feed. No cuts series was constructed; the single event is printed in the JSON and excluded from the trial matrix.

## A3. Closed-end fund discount mean reversion: verdict only

Literature: Lee, Shleifer and Thaler (1991) document the four part puzzle (IPO premium near 10 percent, slide to a discount over 10 percent within 120 days, discounts that move together across funds, convergence to NAV at termination), explained by noise trader sentiment with no riskless arbitrage to close the gap. Modern evidence (Patro and others) finds premium mean reversion with a bias adjusted speed near 8.6 percent per month and a half life near 7.7 months, but convergence is catalyst driven (tenders, open-ending, liquidation); nothing forces a discount to close, and discounts can widen for years.

Verdict: NOT TESTABLE on this estate tonight, and no price only test was run or dressed up as one. The strategy is defined on discount = price vs NAV, which requires point-in-time NAV history per fund. Checked: no store on this box holds CEF NAV history (filesystem search for CEF, closed end, and NAV history stores returned nothing outside library code), the local bars universe contains no CEF panel with NAV, and no free route serves historical NAV at depth (CEFConnect and fund sites serve current or short window discounts; SEC N-PORT filings carry holdings and NAV only from 2019 forward in bulk-unfriendly form). Exact unblocker: a point-in-time CEF NAV history source, either a licensed feed (Morningstar or CEFConnect historical export) or a built N-PORT/N-CSR extraction pipeline that reconstructs dated NAV per fund from SEC filings. Until one of those lands, this territory stays BLOCKED with the unblocker named, not parked silently.

## Find bar accounting

Find bar: DSR at least 0.95 at the clustered trial count, SPA p under 0.05 vs both SPY and QQQ, fair PBO under 0.2, |t| over 3 for a new family. Best candidate (A1 hold63) clears only DSR (0.985) and fails PBO (0.400), SPA (0.300 / 0.378), and t (2.35). Family verdict from the exam: REJECT. Lane A result: zero finds, two graded non-finds (A1, A2 raises), one named miner defect (A2 cuts), one blocked territory with a named unblocker (A3).
