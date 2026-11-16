# Wave 3 Lane C: corporate actions, ETF premium reach, Cremers-Weinbaum audit, dispersion reach

SCOPE: Lane C of Keep Going 2 Wave 3, Sat 2026-11-14 night. Surface: C1 corporate-action event studies on the Alpaca corporate-actions route and the 100-symbol local universe; C2 ETF premium and discount reach verdict; C3 point-in-time audit of the estate chain archive for the Cremers-Weinbaum IV spread; C4 dispersion reach from the same census. Constraints: desk tree read-only, Alpaca only through the estate credential route, no credential values in any artifact, writes only inside this wave3 folder. Outcome: each territory closes as a graded find through tools/admission_exam.py exam(), a graded non-find with numbers, or an untestable or unreachable verdict with the exact missing input named. Proof: lane_c_probe.json (exact probe answers), lane_c_events_raw.json (full event pull), lane_c_raw_bars.json (raw bars), lane_c_results.json (every statistic below), lane_c_census.json (archive audit tables). Edges: local bars end 2026-11-06; the corporate-actions route serves ex-dates only, no announcement dates, so every event study here is ex-date based.

## Verdict summary

| Territory | Verdict | Decisive numbers |
|---|---|---|
| C1a forward-split drift | Graded non-find, exam not run by gate | 19 events, below the 30-event gate; excess vs SPY negative at +5, +21, +63 |
| C1b reverse-split | Untestable at this universe | 2 records served, 1 verifies on raw bars (GE), 1 does not (HON) |
| C1c dividend capture | Graded non-find, exam REJECT | 2,894 events measured; V1 DSR 0.066, V2 DSR 0.884, SPA p 0.497 and 0.499, PBO 0.089 |
| Spinoffs | Census only, untestable as a holder strategy | 10 events, parent-only returns, spun-off value not in the parent series |
| Unit splits | Census only | 0 events in the universe, 511 market-wide |
| C2 ETF premium and discount | Unreachable tonight | No NAV or iNAV product served or held; exact missing product named below |
| C3 Cremers-Weinbaum | Not reachable tonight, accrual path dated | 0 sessions with 5 or more single-name matched call/put IV pairs |
| C4 dispersion | Reach fails, 0 qualifying sessions | Index chains exist on 11 sessions; single-name IV chains exist on 0 |

No candidate in this lane clears the find bar. Nothing below is dressed as a find.

## Literature first

Post-split drift and its decay. The classic result (Ikenberry, Rankine and Stice 1996; Desai and Jain 1997) is positive one-year drift after split announcements, about +7 percent buy-and-hold abnormal in Desai and Jain. Later work narrows it hard: Boehme and Danielsen (2007) find the positive returns live between announcement and effective date and do not persist after the split itself; Gharghori and Nguyen, on 1975 to 2011 data, find the roughly +5 percent per year drift concentrated in 1975 to 1999, with no drift from 2000 to 2011 and none in large and mid caps. A 1,968-split replication over 2000 to 2025 (Ceta Research, FMP data) finds post-split drift gone in aggregate: one-year CAR +0.58 percent, t 0.72; only standard 2-for-1 splits keep a significant +2.58 percent at one year (t 2.45), and the apparent extreme-ratio negative leg was mostly fund share splits and encoding errors. Planning read for this lane: in a 2019 to 2026 large-cap universe, the honest prior is zero to slightly negative drift, and fund share splits must be separated from common-stock splits before any aggregate is quoted. Both cuts are reported below.

Reverse splits. Desai and Jain (1997): reverse-split announcements are followed by minus 10.76 percent at one year and minus 33.90 percent at three years (76 events, 1976 to 1991). Kim, Klein and Rosenfeld (2008), 1,612 events over 1962 to 2001: significant negative abnormal returns for three years after the ex-split month, poor operating performance alongside, and a warning that the names are hard to short, so the drift is not cleanly harvestable. Zaremba and coauthors, 5,000-plus reverse splits across 24 developed markets, 1990 to 2016: subsequent underperformance in every region, microcaps excepted. Planning read: expect underperformance; a long-only avoidance framing or a short series are both legitimate, but only if the universe actually serves events.

Dividend capture and the ex-date drop ratio. Frictionless theory says the price falls by exactly the dividend on the ex-date (drop ratio 1.0), leaving capture with nothing. The empirical literature (Elton and Gruber 1970 onward) usually measures a raw ratio below 1, and the most recent large replication (5,106 events, 80 S and P 500 names, 2010 to 2025) shows why measurement basis decides the answer: raw close-to-open ratio 0.812 (95 percent CI 0.762 to 0.861), but ex-dates had positive average market returns, and the correctly signed market adjustment brings the ratio back to approximately 1.0. Karpoff and Walkling (1988): after commission deregulation, any capture profit concentrates in high-yield names. Planning read: report the raw ratio and the market-adjusted ratio side by side, report the distribution and not just the mean, and judge capture net of a stated cost, not gross.

Cremers-Weinbaum. Cremers and Weinbaum (2010, Journal of Financial and Quantitative Analysis): the spread is the implied volatility of calls minus the implied volatility of puts at the same strike and the same expiry on the same firm, a deviation from put-call parity; stocks with relatively expensive calls beat stocks with relatively expensive puts by about 50 basis points per week in their sample, with predictability decaying over the sample. Dive four graded it the one canonical vol signal still significant in every regime of the 2015 to 2026, 12.36 million firm-day re-estimation. Note the definition, because it decides the audit: the CW input per firm is a matched call/put IV pair, not a pair of tenors. The task text for this lane described the gate as near-term ATM IV and longer-dated IV on single names; that is a term-structure pair, not the CW spread. The C3 audit below checks both readings against the archive, and the verdict is the same either way, for the reason stated there.

## C1 probe: what the corporate-actions route actually serves

Route tested exactly as briefed, through the estate credential route only (desk3.run_live credential_env plus desk3.netfetch). Full answers in lane_c_probe.json.

| Host and query | Status | Exact answer |
|---|---|---|
| paper-api.alpaca.markets/v1beta1/corporate-actions, types forward_split, reverse_split, cash_dividend, spinoff, unit_separation (each, 2019-01-01 to 2026-11-14, limit 5) | 404 for all five | {"message": "endpoint not found."} |
| paper-api host, no params | 404 | {"message": "endpoint not found."} |
| data.alpaca.markets/v1beta1/corporate-actions, type forward_split | 200 | corporate_actions.forward_splits, 5 records on the probe page; record fields include symbol, ex_date, record_date, payable_date, process_date, new_rate, old_rate, cusip, id |
| data host, type reverse_split | 200 | corporate_actions.reverse_splits, 5 on the probe page; fields include symbol, ex_date, new_rate, old_rate, new_symbol, new_cusip, old_cusip |
| data host, type cash_dividend | 200 | corporate_actions.cash_dividends, 5 on the probe page; fields include symbol, ex_date, record_date, payable_date, rate, special, foreign, cusip |
| data host, type spinoff (the task's literal name) | 400 | {"message":"invalid ca type: spinoff, valid types are forward_split, reverse_split, stock_dividend, spin_off, cash_merger, stock_merger, stock_and_cash_merger, unit_split, cash_dividend, redemption, name_change, worthless_removal, rights_distribution, contract_adjustment, partial_call, reorganization, capital_gains_distribution"} |
| data host, type unit_separation (the task's literal name) | 400 | Same body shape: invalid ca type: unit_separation, followed by the same valid-types list |

So the route lives on the data host only, and two of the five briefed type names are not the server's names: the server calls them spin_off and unit_split. All pulls below use the server's names, on the data host, window 2019-01-01 to 2026-11-14, fully paginated (lane_c_fetch_events.py, lane_c_events_raw.json).

Universe-filtered pull (symbols parameter set to the 100 local tickers):

| Type (server name) | Pages | Records in universe |
|---|---|---|
| forward_split | 1 | 19 |
| reverse_split | 1 | 2 |
| cash_dividend | 3 | 2,895 |
| spin_off | 1 | 10 |
| unit_split | 1 | 0 (response carried no unit_splits key) |

Market-wide context (no symbols filter, same window): forward_split 773, reverse_split 5,167, spin_off 246, unit_split 511, cash_dividend at least 201,000 (the pull hit this lane's own 200-page guard at 201,000 records and the true total is higher; the capped count is a lower bound, not a total).

Two basis facts govern everything after this point. First, the records carry ex_date, record_date, payable_date and process_date, and no announcement or declaration date: every study below is ex-date based, exactly as the brief's fallback anticipated. Second, the local bars are not merely split-adjusted: the source study's FREEZE.md and pull script show adjustment=all, split and dividend adjusted, benchmarks included. Drift returns on those bars are total returns, which is the right basis for split drift (the mechanical jump is removed and dividends stay in). The same bars cannot measure an ex-dividend price drop, because the drop is adjusted away in them by construction; C1c therefore runs on a separate raw pull (adjustment=raw, feed sip, 2018-12-01 to 2026-11-14, lane_c_raw_bars.json, 1,998 sessions per symbol). The two bases are never mixed inside one return, and every result below names its basis.

## C1a forward-split drift: graded non-find, no exam by the pre-set gate

Events (19, ex-date based, total-return excess vs SPY from the ex-date close, local adjustment=all bars):

| Symbol | Ex-date | Factor | Excess +5 | Excess +21 | Excess +63 |
|---|---|---|---|---|---|
| AAPL | 2020-08-31 | 4.0 | -7.84% | -6.20% | -11.54% |
| TSLA | 2020-08-31 | 5.0 | -29.01% | -9.86% | +9.95% |
| NEE | 2020-10-27 | 4.0 | +1.02% | -6.42% | -2.73% |
| SHW | 2021-04-01 | 3.0 | -0.50% | +6.89% | +2.67% |
| NVDA | 2021-07-20 | 4.0 | +1.34% | +0.38% | +15.30% |
| AMZN | 2022-06-06 | 20.0 | -7.99% | -1.65% | +5.75% |
| GOOGL | 2022-07-18 | 20.0 | -4.96% | -0.88% | -5.45% |
| TSLA | 2022-08-25 | 3.0 | -0.88% | +6.03% | -34.44% |
| SRE | 2023-08-22 | 2.0 | -1.94% | +2.13% | -1.60% |
| WMT | 2024-02-26 | 3.0 | -1.75% | -0.99% | +5.49% |
| NVDA | 2024-06-10 | 10.0 | +5.42% | +0.40% | -14.02% |
| AVGO | 2024-07-15 | 10.0 | -4.82% | -5.43% | +2.69% |
| NFLX | 2025-11-17 | 10.0 | -3.47% | -14.91% | -33.31% |
| XLB | 2025-12-05 | 2.0 | +2.97% | +5.55% | +14.66% |
| XLE | 2025-12-05 | 2.0 | -0.32% | -1.76% | +23.05% |
| XLK | 2025-12-05 | 2.0 | -1.41% | -0.76% | -3.57% |
| XLU | 2025-12-05 | 2.0 | -0.52% | -3.45% | +9.29% |
| XLY | 2025-12-05 | 2.0 | +1.38% | +0.31% | -3.29% |
| BKNG | 2026-04-06 | 25.0 | -3.52% | -14.69% | -10.24% |

Aggregates (full distributions in lane_c_results.json):

| Cut | Horizon | n | Mean | Median | t | Win rate |
|---|---|---|---|---|---|---|
| All events | +5 | 19 | -2.99% | -1.41% | -1.82 | 26.3% |
| All events | +21 | 19 | -2.39% | -0.99% | -1.70 | 36.8% |
| All events | +63 | 19 | -1.65% | -1.60% | -0.48 | 47.4% |
| Common stock only (excludes the five Select Sector SPDR share splits, all 2-for-1 on 2025-12-05: XLB, XLE, XLK, XLU, XLY) | +5 | 14 | -4.21% | -2.70% | -1.97 | 21.4% |
| Common stock only | +21 | 14 | -3.23% | -1.32% | -1.79 | 35.7% |
| Common stock only | +63 | 14 | -5.11% | -2.17% | -1.30 | 42.9% |

Ex-date mapping was verified independently on the raw bars: the raw close ratio across each ex-date (prior close divided by ex-date close) tracks the stated factor (AAPL 3.87 vs 4.0, NEE 3.99 vs 4.0, NVDA 2021 4.04 vs 4.0, AMZN 19.61 vs 20.0, GOOGL 20.50 vs 20.0, NVDA 2024 9.93 vs 10.0, AVGO 9.92 vs 10.0, the five SPDR splits 1.99 to 2.02 vs 2.0; largest deviations TSLA 2020 at 4.44 vs 5.0 and BKNG at 23.81 vs 25.0, both ordinary large ex-day market moves, full table in lane_c_results.json). The events are real and correctly dated.

Verdict: 19 events is below the brief's 30-event gate, so no portfolio series was constructed and no admission exam was run; running one anyway would be exam-shopping against a pre-set gate. On the event evidence itself there is no positive drift to promote: the sign is negative at every horizon in both cuts, which matches the decayed post-2000 literature and contradicts the 1990s sign in this mega-cap sample. The negative side is also not a find: it was not a pre-registered variant, and its largest |t| is 1.97, far under the new-family bar of 3. Graded non-find.

## C1b reverse splits: untestable at this universe

The route serves exactly 2 reverse-split records for the 100 names in 2019 to 2026:

| Symbol | Ex-date | Factor (new per old) | Raw-bar verification | Excess vs SPY +5 | +21 | +63 |
|---|---|---|---|---|---|---|
| GE | 2021-08-02 | 0.125 (1-for-8) | Verifies: raw ratio 0.1287 vs stated 0.125 | +2.05% | +1.59% | -0.95% |
| HON | 2026-06-29 | 0.5 (1-for-2) | Does not verify: raw ratio 1.019 vs stated 0.5 | -2.11% | +7.40% | -10.45% |

The HON record fails its own effectiveness check: no HON session in 2026 shows a raw close ratio of 1.8 or more (largest absolute 2026 moves are ratios of 1.064, 0.944, 1.057, 0.947, 0.949), so the served 1-for-2 reverse split had not taken effect in the served bars by 2026-11-06. It is a scheduled or announced action carried in the feed, not an observed event, and its row above is printed only so the discrepancy is on the record; it is not a reverse-split observation. Usable observations: 1 (GE), and GE, a strong-name reverse split executed from a position of restructuring strength, mildly outperformed at +5 and +21, the known exception class rather than the distressed class the literature's underperformance comes from. With one usable event there is nothing to average, no portfolio to build, and no exam to run. The literature's expectation (long-run underperformance) is neither confirmed nor refuted here; it is untestable in this universe, stated as such rather than forced. The short framing and the long-only avoidance framing both die on the same count.

## C1c dividend capture net of the drop: graded non-find, exam REJECT

Population: 2,895 cash-dividend records pulled; 2,894 measured; 1 excluded because its window overlaps a split ex-date (NVDA, ex-date 2024-06-11, one session after the 2024-06-10 10-for-1 split, rate 0.01); 0 unmatched to the raw calendar; 0 nonpositive rates. Composition: 2,882 regular and 12 special dividends; per-symbol counts run from 94 (O, a monthly payer) down to 5 (BA); SPY contributes 31 and QQQ 33. Basis: raw bars, entry at the close before the ex-date, dividend received in cash. Full per-stat distributions in lane_c_results.json.

The drop ratio, printed as a distribution because the mean alone lies here:

| Cut | n | Raw ratio mean | Raw ratio median | Market-adjusted ratio mean | Market-adjusted median |
|---|---|---|---|---|---|
| All measured | 2,894 | 0.320 (sd 23.06) | 0.899 | 0.587 (sd 20.86) | 1.086 |
| Entry yield at least 0.1 percent | 2,797 | 0.890 | 0.904 | 1.065 | 1.087 |
| Trimmed, absolute raw ratio at most 10 | 2,692 | 0.785 | 0.888 | 1.051 | 1.066 |

The all-sample means are destroyed by penny dividends, and the artifact names them: the ten largest absolute ratios are all NVDA, amounts of 0.01 to 0.16 dollars on prices of 108.76 to 500.81 dollars, entry yields of 0.006 to 0.035 percent, where the ratio divides an ordinary day's price move by a near-zero dividend (worst case: NVDA 2025-03-12, amount 0.01, price up 6.98 dollars on the ex-date, ratio minus 698.0). Those are not data errors; the ratio is simply noise at tiny yields, which is why the yield-floor cut is the headline. On that cut (n 2,797): raw drop ratio mean 0.890, t against 1.0 of minus 1.20 (not significant); market-adjusted mean 1.065, t against 1.0 of plus 0.89 (not significant). By entry-yield quartile, median raw ratios are 0.139 in the lowest quartile (the noise quartile), then 0.967, 0.948 and 0.990. Read plainly: prices fall by about nine-tenths of the dividend before the market move is accounted, and by an amount statistically indistinguishable from the full dividend after it, the same shape as the corrected 2010 to 2025 replication. There is no mechanical gap left for capture to eat.

Capture net (dividend minus price drop, as a return on the entry close):

| Measure | n | Mean | Median | t | Win rate |
|---|---|---|---|---|---|
| Net at ex-date close, gross | 2,894 | +3.4 bp | +6.7 bp | 0.91 | 52.0% |
| Net at ex-date close, minus 10 bp round trip | 2,894 | -6.6 bp | -3.3 bp | -1.76 | 48.9% |
| Net at +5 sessions, gross | 2,894 | +42.6 bp | +41.5 bp | 5.32 | 55.6% |
| Net at +5 sessions, excess vs SPY over the same closes | 2,894 | +10.9 bp | +4.8 bp | 1.62 | 51.0% |
| Yield-floor subset: net at ex-date close | 2,797 | +2.0 bp | +6.0 bp | 0.46 | 51.8% |
| Yield-floor subset: excess at +5 vs SPY | 2,797 | +8.0 bp | +4.0 bp | 1.19 | 50.9% |
| Highest yield quartile: net at ex-date close | 724 | -4.2 bp | +1.5 bp | -0.41 | 50.4% |

The +5 gross figure is the trap this lane was built to avoid springing: five extra sessions of market exposure in a rising sample contributes most of it, and against SPY the same window leaves +10.9 bp at t 1.62, before any cost. The overnight leg, the only leg that is actually capture, is +3.4 bp gross at t 0.91 and negative after a 10 bp round trip. High-yield names, where the older literature said any residue would live, are the worst quartile overnight, not the best.

Admission exam, run exactly as briefed (tools/admission_exam.py exam(), full output in lane_c_results.json). Matrix: two daily portfolio series on the 1,974 sessions from 2019-01-02 to 2026-11-06. V1 overnight capture: on each ex-date, the equal-weight mean capture net of that day's events, flat (0) on the 716 days with no event (active 1,258 days). V2 six-session hold: each event held from the close before its ex-date to the close at +5, dividend credited on the ex-date, equal-weight across active events each day (active 1,971 days). Benchmarks: SPY and QQQ total returns from the same local adjustment=all bars, the like-for-like comparison for a cash-plus-price strategy. trial_count 4 (every variant evaluated in this lane tonight: forward long, reverse short, capture V1, capture V2), is_new_family true.

| Leg | V1 overnight | V2 six-session |
|---|---|---|
| Annualized Sharpe | -0.158 | 0.788 |
| PSR at zero | 0.319 | 0.984 |
| DSR | 0.066 | 0.884 |
| t of mean daily return | -0.44 | 2.21 |
| Verdict | REJECT (DSR 0.066 < 0.95; SPA not rejected vs all benchmarks at 0.05; \|t\| 0.44 <= 3, new-family hurdle) | REJECT (DSR 0.884 < 0.95; SPA not rejected vs all benchmarks at 0.05; \|t\| 2.21 <= 3, new-family hurdle) |

Family level: n_eff 2.0 from 1 correlation cluster, SR0 annualized 0.347, CPCV PBO 0.089 over 45 splits (the PBO leg alone passes; it cannot promote by itself), SPA p-values 0.497 vs SPY and 0.499 vs QQQ with SPA statistics of 0.0 against both benchmarks, family verdict REJECT (not KILL: PBO 0.089 is far below the 0.5 kill bar). V2 is the closest thing in this lane to a signal and it still fails three of the four bars: deflated Sharpe 0.884 against 0.95, no SPA rejection against either benchmark, and |t| 2.21 against 3. Graded non-find, in numbers.

## Spinoffs and unit separations: census, and why no test follows

Spinoffs (server type spin_off; the briefed name spinoff returns the 400 quoted in the probe table): 10 records in the universe. Parent, spun-off child, ex-date, distribution rate (child shares per parent share): CMCSA to VSNT 2026-01-05 (0.04), CTVA to VYLR 2026-10-01 (1.0), EXC to CEG 2022-02-02 (0.33333), GE to WAB 2019-02-25 (0.005371), GE to GEHC 2023-01-04 (0.33333), GE to GEV 2024-04-02 (0.25), HON to SOLS 2025-10-30 (0.25), HON to HONA 2026-06-29 (0.5), O to ONL 2021-11-15 (0.1), T to WBD 2022-04-11 (0.24192). Parent-only total-return excess vs SPY (adjustment=all parent bars; full table in lane_c_results.json): mean +2.24 percent at +5 (t 1.29), +4.41 percent at +21 (t 1.44), +7.88 percent at +63 (t 1.67, n 9 because CTVA to VYLR has no +63 window before the bars end). Three reasons this is a census and not a test. First, parent-only return is not holder return: the holder also receives the child shares, the parent series on its own systematically understates the position, and the children (WAB, ONL, CEG, GEHC, GEV, WBD, SOLS, VSNT, VYLR, HONA) are almost entirely outside the local 100-name universe, so the holder leg cannot be priced from estate data. Second, the events cluster: GE is the parent in 3 of 10, and HON to HONA shares its 2026-06-29 ex-date with the unverified HON reverse-split record (one separation event wearing two records; its parent excess row is numerically the HON row in C1b). Third, n 10 with t under 1.7 clears nothing even before those defects. Untestable at this universe, named as such.

Unit separations (server type unit_split): 0 records in the universe against 511 market-wide in the window. Census only; there is nothing in this universe to test.

## C2 ETF premium and discount: reach verdict

The test needs, per ETF and timestamp, price against point-in-time net asset value per share (or the exchange intraday indicative value, iNAV or IIV, on the same clock). Without that second series there is no premium or discount to measure, only price changes wearing a borrowed name.

What the estate holds: the warm store (muse-desk-v3 state warm_bars.json) carries exactly two top-level keys, fetched_at and bars, and bar rows of t, o, h, l, c, v; the local research bars carry the same six fields. Neither holds NAV in any field. What the Alpaca route serves, from this lane's own probes (lane_c_probe.json, nav_probes):

| Probe | Status | Fields or body |
|---|---|---|
| data.alpaca.markets/v2/stocks/SPY/snapshot | 200 | dailyBar, latestQuote, latestTrade, minuteBar, prevDailyBar, symbol. No NAV field anywhere in the object. The dailyBar does carry vw (the day's volume-weighted average price) |
| data.alpaca.markets/v1beta1/options/snapshots/SPY, indicative | 200 | Snapshots carrying latestQuote only. No NAV |
| data.alpaca.markets/v2/stocks/SPY/bars/latest | 200 | bar plus symbol; the bar carries vw. No NAV |
| data.alpaca.markets/v2/stocks/SPY/nav | 404 | {"message":"Not Found"} |
| data.alpaca.markets/v1beta1/etfs/SPY/nav | 404 | {"message": "endpoint not found."} |
| data.alpaca.markets/v2/stocks/snapshots for SPY and QQQ with feed sip | 403 | {"message":"subscription does not permit querying recent SIP data"} (recorded for completeness; it is a feed-permission answer about snapshots, not NAV evidence either way) |

Verdict: UNREACHABLE tonight. The exact missing product is a timestamped NAV-per-share (or iNAV/IIV) time series for each ETF under test, covering the test window at the frequency the dislocation claim needs (intraday for intraday dislocations, official end-of-day NAV for close dislocations). Alpaca serves no such product on any probed route, and the estate holds none. No NAV was fabricated and no test was run under the premium and discount name.

The cheapest honest proxy, named for what it is and deliberately not run under any premium label: close versus same-day VWAP, computable tonight because Alpaca bars and snapshots already carry the vw field. Close minus VWAP, divided by VWAP, measures where the close printed inside the day's own trading range of prices: an intraday price-location and close-strength statistic, useful for execution quality. It is not a premium or a discount, because VWAP is an average of the ETF's own traded prices and contains no information about the value of the underlying basket. A second candidate, ETF close versus a constituent-basket replication close built from local bars, measures a replication residual contaminated by stale constituent closes and corporate-action timing; it is also not NAV. Either may be worth testing later under its own name; neither may be reported as premium and discount.

## C3 Cremers-Weinbaum IV spread: archive audit and verdict

Audit scope: every options-chain store the estate holds, read in place. Full tables in lane_c_census.json (lane_c_census.py). One correction to the brief's premises first, because the parent will recount: the brief, following the Unlooked Map, describes the morgue's dated chains as 6 symbols with SPY at 12 sessions from 2026-10-29. The store itself holds 3 symbols at 11 sessions. The census below governs.

Store A, the chain-snapshot-collector's store (the point-in-time archive proper): ~/workspace/morgue/state/morgue/chains/, written by terminal-lineup/site/collect_chains.py (TastyTrade nested chains for layout, enriched from Alpaca), cron every 30 minutes inside the 09:30 to 16:00 ET window.

| Fact | Census value |
|---|---|
| Symbols | SPY, QQQ, IWM. Index ETFs only. Single names: none |
| Daily canonical sessions per symbol | 11: 2026-10-29, 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-12, 2026-11-13 |
| Intraday captures kept | SPY 111, QQQ 113, IWM 109 (333 total) |
| Manifest | 398 lines, 333 status ok and 65 status error, first 2026-10-29T22:39:41Z, last 2026-11-13T20:57:32Z |
| Snapshot columns | occ, oi, volume, iv (rows are [occ, oi, volume, iv] tuples) |
| Contracts per daily snapshot | 5,024 (IWM 2026-11-13) to 13,000 (SPY 2026-11-10); expirations 30 to 35 per snapshot |
| Field provenance (the store's own labels) | Layout from TastyTrade nested chains; open interest MEASURED from Alpaca contracts, dated by oi_date; volume MEASURED from Alpaca indicative snapshot daily bars; IV MODELLED, Black-Scholes inversion of Alpaca indicative quote midpoints (flat r 0.045, fixed dividend yields of SPY 0.013, QQQ 0.005, IWM 0.014, European exercise, expiry at 21:00 UTC), enrichment limited to expiries within 120 days and the 0.75 to 1.25 moneyness band |
| Matched call/put pairs with IV on both sides, same strike and expiry | Present in depth for the 3 ETFs: 750 to 1,004 per IWM session, 1,435 to 2,523 per QQQ session, 1,637 to 2,514 per SPY session |
| Near-term and longer-dated ATM matched pairs (the brief's tenor reading) | Also present for the 3 ETFs on all 11 sessions (at least two expiries carry a matched pair at the ATM strike in every audited snapshot) |
| Modelled IV ledger beside the store (iv_ledger_modelled.jsonl) | 134,857 rows: SPY 57,855, QQQ 54,186, IWM 22,816; same 11 dates; fields include underlying, date, occ, side, strike, expiry, spot, quote bid, ask and mid, iv, iv_basis MODELLED |

Store B, the desk IV ledger (~/workspace/muse-desk-v3/state/iv_ledger.json): 13 symbols (AEHR, ARM, ARQQ, AXTI, CORZ, DGXX, HIVE, IREN, NBIS, POET, SNDK, VELO, WYFI), exactly 1 entry per symbol, every entry dated session 2026-11-13, entry fields iv and session only. One scalar IV per name: no side, no strike, no expiry, no second tenor, no call/put split. It cannot form a CW pair for any firm on any date.

Store C, the desk options cache (~/workspace/muse-desk-v3/cache/options/): 65 symbols with a chain.json each, all written in a single capture window (file modification times 2026-11-02 05:44 to 06:04 UTC). Chains carry symbol, strike and expiration listings; quotes carry bid and ask only. A token scan of the AAPL file finds zero occurrences of implied, iv, delta, gamma, theta, vega and open_interest. One day, no IV: it is a contract-listing snapshot, not an IV archive.

Store D, the book's night-study chain files (goals/midna-trading-her-own-simulated-book hidden files, tt_chains_raw.json 2026-11-12 with 7 names and tt_chains.json 2026-11-13 with 12 names): each name carries a reference price and an empty exps list. No contracts at all.

Point-in-time honesty of the one real archive: the morgue store is genuinely point-in-time (timestamped captures, manifest with hashes, errors recorded as errors, intraday captures preserved), and its IV is labelled MODELLED in the store itself, with the model and its assumptions written into every ledger row. A CW test built on it would be a test on modelled IV from indicative midpoints, which is a usable input if labelled as such; that is not the blocker. The blocker is coverage.

Verdict: a Cremers-Weinbaum exam is NOT honestly reachable tonight, under either definition of the spread. CW is a cross-sectional sort: each formation date needs matched call/put IV pairs across dozens of firms, and the test needs many formation dates. The estate's counts are: sessions with 5 or more single-name matched call/put IV pairs, 0; sessions with any single-name chain carrying IV at all, 0; firms with a CW pair on any date, 0 (the 3 names with pairs are index ETFs, and a 3-ETF sort is not the CW cross-section); formation dates available even for the ETFs, 11 daily sessions, about two weekly formations. No sort was run and no exam was manufactured.

Dated accrual path, using plumbing that already exists: extend the chain collector's enrichment leg (the Alpaca contracts plus indicative-quote leg that already produces modelled IV for SPY, QQQ and IWM) to a fixed single-name panel, the liquid optionable Focus names, storing one canonical snapshot per session per name with, at minimum, the matched call/put modelled IV at the ATM strike for the nearest expiry more than 7 days out (the CW level), the same pair one week earlier carried forward by the series itself (the CW change leg), spot, and the existing oi_date and MODELLED labelling. Cadence: every session, which the current collector already sustains at 30-minute intervals in the trading window; the canonical daily file is the test input. Minimum honest test: 30 or more names times 26 weekly formations, which, starting the next session (Mon 2026-11-16), completes in the week of Mon 2027-05-17; the preferred depth is 52 weekly formations, completing in the week of Mon 2027-11-15. Until the first of those dates, CW stays in its dive-four state: TEST-gated, untested, with this audit as the gate evidence.

## C4 dispersion with the estate chain archive: reach verdict

Implied correlation, the standard dispersion input, needs, in the same session: an index IV at a matched tenor (the morgue store has this for SPY, QQQ and IWM on 11 sessions), plus IVs at the same tenor for the index's top constituent single names, plus constituent weights. The question the brief sets is the count of sessions where an index chain and at least 5 single-name chains coexist.

From the C3 census, the count is 0 under the only reading that makes the computation possible (single-name chains carrying IV): the morgue store holds no single names on any of its 11 sessions, the desk cache holds no IV on its single day, and the desk IV ledger holds no chains. Two near-misses, named so they are not mistaken for qualifications. On 2026-11-02, the desk cache's capture day, index chains exist in the morgue store and 62-plus single-name chain listings exist in the cache on the same calendar date; but the listings carry bid and ask only, with no IV, no constituent weights and no synchronized spot, so implied correlation is not computable on that date either. On 2026-11-13, index chains coexist with 13 single-name scalar IVs in the desk ledger; scalar IVs with no strike, expiry or tenor basis, on names that are not the index's top constituents, with no weights recorded, are not a dispersion input. Qualifying sessions for an honest implied-correlation computation: 0.

Verdict: reach fails. The unblocker is the C3 accrual path plus one addition: per-session constituent weights for the chosen index recorded alongside the panel, with every panel name's IV taken at the same tenor rule as the index IV. The same dated milestones apply (first testable week of 2027-05-17 at 26 formations, preferred 2027-11-15 at 52). No dispersion number was computed, because any number produced tonight would be built from inputs the archive does not contain.

## Files and reproducibility

All inside ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave3/:

| File | Contents |
|---|---|
| lane_c_probe.py, lane_c_probe.json | Corporate-actions and NAV probes; exact statuses, bodies and first records |
| lane_c_fetch_events.py, lane_c_events_raw.json | Full paginated event pull, universe and market-wide counts |
| lane_c_fetch_raw.py, lane_c_raw_bars.json | Raw-basis daily bars for the dividend leg and split verification (17 MB) |
| lane_c_census.py, lane_c_census.json | Chain archive audit: morgue store, modelled ledger, desk IV ledger, desk options cache, warm store |
| lane_c_analysis.py, lane_c_results.json | Event studies, dividend distributions, portfolio construction, full admission exam output |
| lane_c_report.md | This report |

Methods notes for the recount: event windows are sessions on the SPY calendar, entry at the ex-date close unless stated otherwise (dividend capture enters at the close before the ex-date, as stated there); the exam's SPA legs use 1,000 stationary-bootstrap draws per benchmark at the exam's own defaults; the dividend exam's trial count of 4 counts every variant this lane evaluated, including the two event-study families that never reached an exam matrix. Open rows carried forward, named: (1) the HON 2026-06-29 reverse-split record that had not taken effect in served bars by 2026-11-06, worth one recheck against a later bar pull before anyone cites HON as a reverse-split event; (2) the C3 and C4 accrual, which needs the collector extension to be scheduled by whoever owns the collector, with first testable dates in the weeks of 2027-05-17 and 2027-11-15 as above; (3) C2 stays closed until a NAV or iNAV product is actually procured, and the close-versus-VWAP statistic, if ever tested, enters under its own name.

STATUS: Lane C complete as a set of graded non-finds and reach verdicts, zero promotions. Evidence pointers: lane_c_results.json (exam family verdict REJECT, forward aggregate excess, dividend distributions), lane_c_probe.json (route answers), lane_c_census.json (archive counts). PARTIAL in the doctrine sense only about the estate, not about this lane's work: C1b, spinoffs, C2, C3 and C4 name the exact missing inputs above, and C1a and C1c are closed with numbers.
