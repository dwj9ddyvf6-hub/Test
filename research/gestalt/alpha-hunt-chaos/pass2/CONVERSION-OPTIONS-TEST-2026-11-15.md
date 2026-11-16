# Conversion Program: Fresh Options Expression Test for the Overnight Focus Edge

Date of test: Sunday 2026-11-15, evening ET (fetches 2026-11-16 00:40 to 00:47 UTC, which is 2026-11-15 19:40 to 19:47 ET).
Data basis, stated on the face of this test: today is a Sunday, so every chain, quote and Greek below carries Friday 2026-11-13 close data. No Monday data exists yet. Entry is modelled at the Friday close and exit at the Monday open.
Register object: C01, the overnight Focus names edge, exam passed. Basket gross overnight mean plus 16.46 bp over 2,229 sessions. Per name overnight move proxies used for capture, in bp of spot per night: SNDK plus 28.71, CRWV plus 18.37, RKLB plus 10.48, NVDA plus 7.52, AMD plus 6.11. True auction cost of the stock form is about 5.8 bp, for scale only. This is a fresh test on current chains, not a citation of the Wave 4 test. The Wave 4 rejection and register row ON_focus29 stand as prior history only.

## Headline verdict

No options expression on any of the five carry names clears its cost stack tonight. Not on the weekend hold (Friday close to Monday open, 3 calendar days of theta), and not on a generic single weeknight (1 calendar day of theta). All 15 primary expressions FAIL, and all 4 priceable 0.25 delta spread variants FAIL.

Best expression by net bp, weekend costing: AMD long 557.5 call / short 560 call, expiry 2026-11-16. Capture 0.10 bp, spread cost 7.18 bp, theta cost 5.26 bp, total cost 12.44 bp, net minus 12.34 bp, break-even overnight move 791.2 bp against an expected AMD overnight move of 6.11 bp. It misses by 12.34 bp, and it is a near zero expression: its delta difference is only 0.016, so it captures almost nothing. The best expression that carries meaningful capture (at least 3 bp) on weekend costing is the SNDK 0.25 delta call spread below, net minus 40.91 bp (capture 6.39 bp, cost 47.30 bp, break-even 212.4 bp against an expected 28.71 bp).

Best expression by net bp, weeknight costing: the same AMD 557.5 / 560 spread, net minus 8.83 bp (capture 0.10 bp, cost 8.93 bp, break-even 568.1 bp). It still misses by 8.83 bp.

## Routes used, and routes that failed (exact errors preserved)

1. Nested chain structure, working route. GET /option-chains/<SYM>/nested on api.tastyworks.com, User-Agent midna-desk/1.0, token minted per run from the read scope key file through the canonical loader tt_mint.py, values never printed. Fetches: SNDK 2026-11-16T00:40:05Z, CRWV 00:40:07Z, RKLB 00:40:08Z, NVDA 00:40:10Z, AMD 00:40:11Z, all HTTP 200. Finding: this payload carries strikes, OCC symbols, streamer symbols and expiries only. It carries no bid, no ask, no implied volatility and no Greeks, and no underlying price. Anyone expecting Greeks inside the nested payload will not find them there.
2. REST market data, failed route. GET /market-data and GET /market-data/by-type (tested with equity and with equity-option parameters, singular and plural forms) returned HTTP 403 with body: status 403, error Forbidden, path /market-data/by-type, timestamps 2026-11-16T00:41:19Z to 00:42:41Z. That scope was stopped after the 403s, not retried in a loop. Account and chain endpoints on the same token returned 200, so this is an endpoint scope refusal, not a dead token.
3. DXLink quote feed, working route for prices and Greeks. GET /api-quote-tokens returned 200 at 2026-11-16T00:42:32Z, level demo, dxlink-url wss://tasty-demo-dxlink-md-ws.dxfeed.com/delayed, expires 2026-11-17T00:42:32Z. Quote, Greeks, Trade and Summary events were collected over DXLink at 00:43Z (735 subscriptions, first window) and 00:46Z (69 subscriptions, extended SNDK and AMD strikes). Theta method per name: the feed Greeks theta is present for every priced leg, so feed theta is the primary method for all five names. No name needed the Black-Scholes theta fallback as its primary method. A Black-Scholes repricing sensitivity for E1 is printed per name as a cross-check, and it changes no verdict.
4. Validation of the DXLink set. Two independent cross-checks say this quote set is Friday's real closing set, despite the demo level label on the token. First, the feed equity quotes match the desk 1Min cache extended hours last prints (Friday 2026-11-14T00:59Z bar, 19:59 ET) to the cent or near it: SNDK quote 865.55 / 866.00 against last print 865.23; CRWV 51.71 / 51.76 against 51.75; RKLB 59.85 / 59.96 against 59.87; NVDA 161.00 / 161.05 against 161.01; AMD 521.24 / 521.25 against 521.20. Second, feed Greeks implied volatilities match the TastyTrade REST market-metrics per expiry implied volatilities (REST, updated Friday 2026-11-13 20:48 to 20:55 UTC) within a few points everywhere: see the IV cross-check table below.
5. Market metrics, working route. GET /market-metrics?symbols=SNDK,CRWV,RKLB,NVDA,AMD returned 200 at 2026-11-16T00:45:06Z and is used only as the IV cross-check, never as a price source.

## Spot references (Friday 2026-11-13)

Primary spot, per the task rule (chain payload carries no underlying price, so the desk 1Day cache is the fallback): SNDK 885.01, CRWV 53.13, NVDA 163.865, AMD 557.425. RKLB has no 1Day file in the cache, so its spot is the 1Min regular session close bar at 2026-11-13T20:00Z, 61.53, corroborated by the feed Trade print 61.505. All bp conversions in this test use the primary spot, and the at the money strike is the listed strike nearest the primary spot, one rule for all names.

| Name | Primary spot used | Source | Feed equity quote mid (extended hours last) | 1Min regular close (20:00Z bar) | Note |
|---|---|---|---|---|---|
| SNDK | 885.01 | 1Day cache | 865.775 | 875.16 | Names fell after hours Friday; feed Greeks price off the later reference, which makes the test conservative, not generous |
| CRWV | 53.13 | 1Day cache | 51.735 | 53.135 | 1Day and 1Min regular close agree |
| RKLB | 61.53 | 1Min cache (no 1Day file) | 59.905 | 61.53 | Gap named: no RKLB 1Day cache file exists |
| NVDA | 163.865 | 1Day cache | 161.025 | 162.76 | 1Day close sits about 1.1 above the 1Min regular close bar |
| AMD | 557.425 | 1Day cache | 521.245 | 533.24 | Defect flagged: the AMD 1Day bar (close 557.425, volume 4,041,723) disagrees with its own 1Min regular close (533.24) by 24.19. The 557.5 strike is at the money only under the 1Day figure; under every other reference it is out of the money, which is why its feed delta is 0.138. AMD verdicts fail under either reference, see the sensitivity note in the AMD section |

## IV cross-check: feed Greeks IV at the money vs TastyTrade market-metrics expiry IV

| Name | Expiry | Feed ATM call IV | Market-metrics expiry IV |
|---|---|---|---|
| SNDK | 2026-11-20 | 1.122 | 1.059 |
| SNDK | 2026-11-27 | 0.980 | 0.939 |
| CRWV | 2026-11-20 | 1.142 | 1.156 |
| CRWV | 2026-11-27 | 1.021 | 1.036 |
| RKLB | 2026-11-20 | 0.852 | 0.870 |
| RKLB | 2026-11-27 | 0.787 | 0.768 |
| NVDA | 2026-11-16 | 0.514 | 0.543 |
| NVDA | 2026-11-18 | 0.983 | 0.977 |
| AMD | 2026-11-16 | 0.683 | 0.641 |
| AMD | 2026-11-18 | 0.833 | 0.796 |

## Costing rules, applied identically to every expression

- Capture, in bp of spot: effective delta times the per name overnight bp above. The basket figure (times 16.46 bp) is printed for E1 as a second column.
- Spread cost, round trip, in bp of spot: half-spread paid on entry plus half-spread paid on exit equals the full quoted width per leg, summed over legs, divided by spot. Width is the absolute ask minus bid where a quote is crossed (defects listed below).
- Theta cost: net signed feed theta per day times 3 for the weekend case, times 1 for the weeknight case. A negative net theta is a cost; a positive net theta (calendars on SNDK, CRWV and RKLB) is printed as a negative cost, that is, a gain, and it still does not save those calendars because their spread widths are larger.
- Verdict: SURVIVES only if capture exceeds total cost. Break-even overnight move, in bp: total cost divided by effective delta. Compare it with the expected per name move in the spot table of the brief (28.71, 18.37, 10.48, 7.52, 6.11 bp). The break-evens below run from 118 bp to 3,398 bp, that is, from about 7 times to about 470 times the expected move.
- Expressions: E1 is the long at the money call on the nearest expiry. E2 is the long at the money call, short call one strike step up, on the nearest expiry; where a short leg at about 0.25 delta exists in the feed, that variant is priced as E2b as well. E3 is a same strike call calendar, short the nearest expiry at the money call, long the next expiry at the money call, priced only because a second expiry with a quotable spread exists for all five names.

## Data defects carried on the face of this test

- Crossed quotes in the Sunday snapshot (bid above ask), widths taken as absolute values and mids as averages: NVDA 2026-11-16 C165 (1.98 / 1.80), C167.5 (1.12 / 1.00), C170 (0.67 / 0.60); AMD 2026-11-16 C560 (2.90 / 2.80); SNDK 2026-11-20 C900 (42.50 / 42.00, in the ladder, not used in any expression). No verdict depends on a crossed width: zeroing every crossed width in the best expression (AMD E2) would cut its cost by at most 1.8 bp against a miss of 12.34 bp weekend and 8.83 bp weeknight.
- SNDK 2026-11-27 quotes are wide (ATM width 6.10 on a 62.95 mid). That width is real in the snapshot and is charged in full to the SNDK calendar.
- NVDA 2026-11-18 ATM call quote is locked (5.95 / 5.95, width 0.00) in the snapshot. It is charged as printed. Giving it a normal width would only worsen the NVDA calendar, which already fails on theta.
- Feed Greeks theoretical prices sit below quoted mids at the money for the Nov 20 and Nov 27 names (for example SNDK C885 theoretical 44.35 against mid 49.75). Costs in this test are charged on quoted widths, and capture on feed deltas, so the gap does not flatter any expression.


## SNDK (spot used 885.01, expected overnight move 28.71 bp, basket 16.46 bp)

At the money options, nearest and next expiry:

| Expiry | Kind | Strike | Bid | Ask | Mid | IV | Delta | Theta per day |
|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | Call | 885 | 49.30 | 50.20 | 49.75 | 1.122 | 0.473 | -3.866 |
| 2026-11-20 | Put | 885 | 49.80 | 50.00 | 49.90 | 0.940 | -0.543 | -3.227 |
| 2026-11-27 | Call | 885 | 59.90 | 66.00 | 62.95 | 0.980 | 0.491 | -2.390 |
| 2026-11-27 | Put | 885 | 58.30 | 64.30 | 61.30 | 0.850 | -0.521 | -2.070 |

Expressions, nearest expiry 2026-11-20 unless stated:

| Expression | Legs | Effective delta | Capture bp (per name) | Capture bp (basket, E1 only) | Spread cost bp | Theta cost bp | Total cost bp | Net bp | Break-even move bp | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 weekend | Long C885 | 0.473 | 13.57 | 7.78 | 10.17 | 131.03 | 141.20 | -127.63 | 298.7 | FAILS |
| E1 weeknight | Long C885 | 0.473 | 13.57 | 7.78 | 10.17 | 43.68 | 53.85 | -40.28 | 113.9 | FAILS |
| E2 weekend | Long C885, short C890 (one step) | 0.015 | 0.44 | n/a | 16.95 | 1.20 | 18.15 | -17.71 | 1194.7 | FAILS |
| E2 weeknight | Long C885, short C890 | 0.015 | 0.44 | n/a | 16.95 | 0.40 | 17.35 | -16.91 | 1142.1 | FAILS |
| E2b weekend | Long C885, short C965 (delta 0.250 exactly) | 0.223 | 6.39 | n/a | 15.82 | 31.48 | 47.30 | -40.91 | 212.4 | FAILS |
| E2b weeknight | Long C885, short C965 | 0.223 | 6.39 | n/a | 15.82 | 10.49 | 26.31 | -19.92 | 118.2 | FAILS |
| E3 weekend | Short C885 2026-11-20, long C885 2026-11-27 | 0.018 | 0.53 | n/a | 79.10 | -50.03 (gain) | 29.06 | -28.54 | 1582.4 | FAILS |
| E3 weeknight | Same calendar | 0.018 | 0.53 | n/a | 79.10 | -16.68 (gain) | 62.42 | -61.89 | 3398.4 | FAILS |

Notes: E1 premium mid 49.75; the round trip spread of 0.90 is 1.81 percent of premium and 10.17 bp of spot. E2 one step net premium mid 2.35, net theta -0.035 per day. E2b short leg C965: bid 20.00, ask 20.50, mid 20.25, IV 1.066, delta 0.250, theta -2.937; net premium mid 29.50, net theta -0.929 per day. This leg sits above the first collected window and was fetched in the second DXLink run at 00:46Z; without that run the closest collected leg was C935 at delta 0.326. E3 net debit mid 13.20, net theta plus 1.476 per day: the calendar earns theta and still loses, because the Nov 27 leg width of 6.10 dominates. Black-Scholes sensitivity for E1 weekend, repricing at feed spot 865.775 and feed IV 1.122 from 7 calendar days to 4: decay 13.03 per share, 147.28 bp of spot, net minus 143.87 bp. FAILS under both theta methods.

## CRWV (spot used 53.13, expected overnight move 18.37 bp, basket 16.46 bp)

At the money options, nearest and next expiry:

| Expiry | Kind | Strike | Bid | Ask | Mid | IV | Delta | Theta per day |
|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | Call | 53 | 3.25 | 3.40 | 3.325 | 1.142 | 0.470 | -0.235 |
| 2026-11-20 | Put | 53 | 3.10 | 3.25 | 3.175 | 1.131 | -0.531 | -0.233 |
| 2026-11-27 | Call | 53 | 4.00 | 4.25 | 4.125 | 1.021 | 0.491 | -0.149 |
| 2026-11-27 | Put | 53 | 3.90 | 4.15 | 4.025 | 0.975 | -0.513 | -0.142 |

Expressions, nearest expiry 2026-11-20 unless stated:

| Expression | Legs | Effective delta | Capture bp (per name) | Capture bp (basket, E1 only) | Spread cost bp | Theta cost bp | Total cost bp | Net bp | Break-even move bp | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 weekend | Long C53 | 0.470 | 8.64 | 7.74 | 28.23 | 132.77 | 161.00 | -152.36 | 342.4 | FAILS |
| E1 weeknight | Long C53 | 0.470 | 8.64 | 7.74 | 28.23 | 44.26 | 72.49 | -63.85 | 154.2 | FAILS |
| E2 weekend | Long C53, short C54 (one step) | 0.047 | 0.87 | n/a | 56.47 | 2.17 | 58.63 | -57.77 | 1238.8 | FAILS |
| E2 weeknight | Long C53, short C54 | 0.047 | 0.87 | n/a | 56.47 | 0.72 | 57.19 | -56.32 | 1208.2 | FAILS |
| E2b weekend | Long C53, short C58 (delta 0.254) | 0.216 | 3.97 | n/a | 50.82 | 26.92 | 77.74 | -73.77 | 360.1 | FAILS |
| E2b weeknight | Long C53, short C58 | 0.216 | 3.97 | n/a | 50.82 | 8.97 | 59.79 | -55.83 | 277.0 | FAILS |
| E3 weekend | Short C53 2026-11-20, long C53 2026-11-27 | 0.021 | 0.39 | n/a | 75.29 | -48.67 (gain) | 26.61 | -26.23 | 1257.4 | FAILS |
| E3 weeknight | Same calendar | 0.021 | 0.39 | n/a | 75.29 | -16.22 (gain) | 59.06 | -58.67 | 2790.5 | FAILS |

Notes: E1 premium mid 3.325; the round trip spread of 0.15 is 4.51 percent of premium and 28.23 bp of spot. On a 53 dollar stock, a 15 cent width is 28 bp before any theta, which alone is one and a half times the whole expected overnight move. E2 one step net premium mid 0.50, net theta -0.004 per day. E2b net premium mid 1.91, net theta -0.048 per day. E3 net debit mid 0.80, net theta plus 0.086 per day. Black-Scholes sensitivity for E1 weekend, feed spot 51.735, feed IV 1.142, 7 days to 4: decay 0.79 per share, 149.02 bp, net minus 168.61 bp. FAILS under both theta methods.

## RKLB (spot used 61.53, expected overnight move 10.48 bp, basket 16.46 bp)

At the money options, nearest and next expiry. At the money strike by the stated rule (nearest listed strike to spot 61.53) is 62. The neighbouring calls straddle true at the money in delta terms: C60 delta 0.521, C61 delta 0.465, C62 delta 0.409, all on 2026-11-20.

| Expiry | Kind | Strike | Bid | Ask | Mid | IV | Delta | Theta per day |
|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | Call | 62 | 2.47 | 2.65 | 2.56 | 0.852 | 0.409 | -0.198 |
| 2026-11-20 | Put | 62 | 2.98 | 3.20 | 3.09 | 0.849 | -0.591 | -0.198 |
| 2026-11-27 | Call | 62 | 3.20 | 3.60 | 3.40 | 0.787 | 0.443 | -0.132 |
| 2026-11-27 | Put | 62 | 3.65 | 4.10 | 3.875 | 0.765 | -0.561 | -0.128 |

Expressions, nearest expiry 2026-11-20 unless stated:

| Expression | Legs | Effective delta | Capture bp (per name) | Capture bp (basket, E1 only) | Spread cost bp | Theta cost bp | Total cost bp | Net bp | Break-even move bp | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 weekend | Long C62 | 0.409 | 4.29 | 6.73 | 29.25 | 96.74 | 126.00 | -121.71 | 308.1 | FAILS |
| E1 weeknight | Long C62 | 0.409 | 4.29 | 6.73 | 29.25 | 32.25 | 61.50 | -57.22 | 150.4 | FAILS |
| E2 weekend | Long C62, short C63 (one step) | 0.054 | 0.57 | n/a | 52.01 | 4.95 | 56.95 | -56.39 | 1052.7 | FAILS |
| E2 weeknight | Long C62, short C63 | 0.054 | 0.57 | n/a | 52.01 | 1.65 | 53.66 | -53.09 | 991.7 | FAILS |
| E2b weekend | Long C62, short C65 (delta 0.255) | 0.154 | 1.62 | n/a | 48.76 | 19.39 | 68.15 | -66.53 | 441.3 | FAILS |
| E2b weeknight | Long C62, short C65 | 0.154 | 1.62 | n/a | 48.76 | 6.46 | 55.22 | -53.60 | 357.6 | FAILS |
| E3 weekend | Short C62 2026-11-20, long C62 2026-11-27 | 0.034 | 0.35 | n/a | 94.26 | -32.60 (gain) | 61.66 | -61.31 | 1828.2 | FAILS |
| E3 weeknight | Same calendar | 0.034 | 0.35 | n/a | 94.26 | -10.87 (gain) | 83.40 | -83.04 | 2472.5 | FAILS |

Notes: E1 premium mid 2.56; the round trip spread of 0.18 is 7.03 percent of premium and 29.25 bp of spot. E2 one step net premium mid 0.43, net theta -0.010 per day. E2b net premium mid 1.16, net theta -0.040 per day. E3 net debit mid 0.84, net theta plus 0.067 per day. Using C60 or C61 as the long leg instead of C62 raises capture (delta 0.521 gives 5.46 bp) and leaves theta and width of the same size, so no strike choice in this neighbourhood changes the verdict. Black-Scholes sensitivity for E1 weekend, feed spot 59.905, feed IV 0.852, 7 days to 4: decay 0.66 per share, 107.37 bp, net minus 132.34 bp. FAILS under both theta methods.


## NVDA (spot used 163.865, expected overnight move 7.52 bp, basket 16.46 bp)

Nearest expiry is Monday 2026-11-16 itself. At the Friday close this contract had 3 calendar days of life; at the Monday open exit it has only the Monday session left. This is the purest overnight options form available tonight, and it is the one the theta stack hits hardest in proportion.

At the money options, nearest and next expiry:

| Expiry | Kind | Strike | Bid | Ask | Mid | IV | Delta | Theta per day |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | Call | 165 | 1.98 | 1.80 | 1.89 | 0.514 | 0.304 | -0.449 |
| 2026-11-16 | Put | 165 | 4.10 | 4.25 | 4.175 | 0.418 | -0.739 | -0.340 |
| 2026-11-18 | Call | 165 | 5.95 | 5.95 | 5.95 | 0.983 | 0.437 | -0.742 |
| 2026-11-18 | Put | 165 | 8.10 | 8.25 | 8.175 | 0.887 | -0.574 | -0.666 |

The C165 call quote is crossed (bid above ask), flagged in the defects section; mid and absolute width are used. Its feed delta is 0.304, not about 0.5, because the feed references the after hours spot near 161, where the 165 strike is out of the money. The put at the same strike carries delta -0.739 for the same reason.

Expressions, nearest expiry 2026-11-16 unless stated:

| Expression | Legs | Effective delta | Capture bp (per name) | Capture bp (basket, E1 only) | Spread cost bp | Theta cost bp | Total cost bp | Net bp | Break-even move bp | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 weekend | Long C165 2026-11-16 | 0.304 | 2.28 | 5.00 | 10.98 | 82.28 | 93.26 | -90.98 | 307.0 | FAILS |
| E1 weeknight | Long C165 2026-11-16 | 0.304 | 2.28 | 5.00 | 10.98 | 27.43 | 38.41 | -36.13 | 126.4 | FAILS |
| E2 weekend | Long C165, short C167.5 (one step, also the closest collected leg to 0.25 delta, at 0.193) | 0.111 | 0.83 | n/a | 18.31 | 19.29 | 37.60 | -36.77 | 339.5 | FAILS |
| E2 weeknight | Long C165, short C167.5 | 0.111 | 0.83 | n/a | 18.31 | 6.43 | 24.74 | -23.91 | 223.3 | FAILS |
| E3 weekend | Short C165 2026-11-16, long C165 2026-11-18 | 0.133 | 1.00 | n/a | 10.98 | 53.56 | 64.54 | -63.54 | 483.6 | FAILS |
| E3 weeknight | Same calendar | 0.133 | 1.00 | n/a | 10.98 | 17.85 | 28.84 | -27.83 | 216.1 | FAILS |

Notes: E1 premium mid 1.89; the round trip spread of 0.18 is 9.52 percent of premium and 10.98 bp of spot. E2 net premium mid 0.83, net theta -0.105 per day. E3 net debit mid 4.06, net theta -0.293 per day: this calendar loses on theta, the reverse of the Nov 20 names, because the Nov 18 expiry carries far higher IV (0.983 against 0.514) and therefore a larger daily theta than the expiring front leg. Black-Scholes sensitivity for E1 weekend, feed spot 161.025, feed IV 0.514, repricing from 3 calendar days to expiry morning: decay 1.41 per share, 86.01 bp, net minus 94.71 bp. Note the feed theta times 3 (82.28 bp) and the bounded Black-Scholes decay (86.01 bp) agree closely here, and both are about 40 times the capture. FAILS under both theta methods.

## AMD (spot used 557.425, expected overnight move 6.11 bp, basket 16.46 bp)

Nearest expiry is Monday 2026-11-16, as with NVDA. Spot defect, repeated here because it decides how to read this section: the 1Day cache close of 557.425 disagrees with the 1Min regular close of 533.24 and with the feed extended hours quote mid of 521.245. The feed therefore prices the 557.5 strike as out of the money (call delta 0.138, put delta -0.997). The test is run as briefed, on the 1Day spot and the 557.5 strike, with feed Greeks. Sensitivity: even granting a full at the money delta of 0.5, E1 capture would be 3.06 bp against a weekend cost of 71.05 bp, and the E2 spread verdicts, which are the best in this test, do not use the long leg delta alone and miss by 12.34 bp on a delta difference that a higher spot reference would raise only modestly, while raising theta on both legs. No AMD verdict flips under the 533.24 reference.

At the money options, nearest and next expiry (at the money under the briefed 1Day spot):

| Expiry | Kind | Strike | Bid | Ask | Mid | IV | Delta | Theta per day |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | Call | 557.5 | 3.35 | 3.65 | 3.50 | 0.683 | 0.138 | -1.220 |
| 2026-11-16 | Put | 557.5 | 26.00 | 27.55 | 26.775 | 0.279 | -0.997 | -0.022 |
| 2026-11-18 | Call | 557.5 | 9.15 | 9.90 | 9.525 | 0.833 | 0.257 | -1.665 |
| 2026-11-18 | Put | 557.5 | 32.30 | 34.20 | 33.25 | 0.543 | -0.852 | -0.776 |

Expressions, nearest expiry 2026-11-16 unless stated:

| Expression | Legs | Effective delta | Capture bp (per name) | Capture bp (basket, E1 only) | Spread cost bp | Theta cost bp | Total cost bp | Net bp | Break-even move bp | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 weekend | Long C557.5 2026-11-16 | 0.138 | 0.84 | 2.27 | 5.38 | 65.67 | 71.05 | -70.21 | 514.3 | FAILS |
| E1 weeknight | Long C557.5 2026-11-16 | 0.138 | 0.84 | 2.27 | 5.38 | 21.89 | 27.27 | -26.43 | 197.4 | FAILS |
| E2 weekend | Long C557.5, short C560 (one step) | 0.016 | 0.10 | n/a | 7.18 | 5.26 | 12.44 | -12.34 | 791.2 | FAILS |
| E2 weeknight | Long C557.5, short C560 | 0.016 | 0.10 | n/a | 7.18 | 1.75 | 8.93 | -8.83 | 568.1 | FAILS |
| E3 weekend | Short C557.5 2026-11-16, long C557.5 2026-11-18 | 0.118 | 0.72 | n/a | 18.84 | 23.92 | 42.75 | -42.03 | 361.2 | FAILS |
| E3 weeknight | Same calendar | 0.118 | 0.72 | n/a | 18.84 | 7.97 | 26.81 | -26.09 | 226.5 | FAILS |

Notes: E1 premium mid 3.50; the round trip spread of 0.30 is 8.57 percent of premium and 5.38 bp of spot. E2 net premium mid 0.65, net theta -0.098 per day. The short C560 quote is crossed (2.90 / 2.80); absolute width 0.10 used. E2b, the 0.25 delta variant, is NOT PRICEABLE for AMD on the nearest expiry, with this reason: in the feed reference there is no call at or above 0.25 delta at any strike, because the long leg itself carries delta 0.138 and deltas fall from there (C585 delta 0.032, C600 delta 0.017, C660 delta 0.002, all fetched in the second DXLink run). A 0.25 delta short leg exists only under the disputed 1Day spot reference, and pricing it would require model deltas, not chain deltas. That is a named gap, not a silent skip: E2 one step is priced, E2b is not, for AMD only. E3 net debit mid 6.03, net theta -0.444 per day; as with NVDA, the back expiry theta exceeds the front, so the calendar pays theta instead of earning it. Black-Scholes sensitivity for E1 weekend, feed spot 521.245, feed IV 0.683, 3 days to expiry morning: decay 2.35 per share, 42.24 bp, net minus 46.78 bp. FAILS under both theta methods, and with a smaller margin than the feed theta method, because Black-Scholes decay is bounded by the premium while theta times 3 is not.

## Aggregate

Question asked: does any options expression on any carry name clear its cost stack tonight? Answer: no.

- Weekend costing (the actual trade, Friday close to Monday open): 19 of 19 priced expressions fail. Closest miss: AMD E2 one step, minus 12.34 bp (cost 12.44 bp, capture 0.10 bp). Next closest: SNDK E2 one step, minus 17.71 bp (cost 18.15 bp, capture 0.44 bp); CRWV E3 calendar, minus 26.23 bp (cost 26.61 bp, capture 0.39 bp, after a 48.67 bp theta gain was already credited); SNDK E2b 0.25 delta spread, minus 40.91 bp (cost 47.30 bp, capture 6.39 bp), the closest miss among expressions capturing at least 3 bp.
- Weeknight costing (a generic single night, 1 day of theta): 19 of 19 fail. Closest miss: AMD E2 one step, minus 8.83 bp. Next: SNDK E2b, minus 19.92 bp; NVDA E2, minus 23.91 bp.
- By class, weekend: E1 long calls fail by 70.21 to 152.36 bp of spot. E2 one step spreads fail by 12.34 to 57.77 bp. E2b 0.25 delta spreads fail by 36.77 to 73.77 bp. E3 calendars fail by 26.23 to 63.54 bp, including the three calendars that earn net theta.
- Why, in one line per mechanism: outright calls pay 43 to 133 bp of theta per night against 1 to 14 bp of delta capture; one step spreads cut theta to near zero but also cut capture to near zero (delta differences of 0.015 to 0.111) while keeping 7 to 56 bp of two leg spread width; 0.25 delta spreads keep real capture (4 to 6 bp on SNDK and CRWV) but keep 27 to 51 bp of spread width plus 19 to 31 bp of weekend theta; calendars on the Nov 20 names earn 33 to 50 bp of weekend theta and pay 75 to 94 bp of two expiry spread width for 0.4 to 0.5 bp of capture, and calendars on the Monday expiry names pay theta outright because the second expiry carries the higher IV.
- Count of what was priced: names priced 5 of 5 (SNDK, CRWV, RKLB, NVDA, AMD). Primary expressions priced 15 of 15 (E1, E2, E3 for each name), each costed twice, weekend and weeknight, for 30 primary costings. Variants priced: E2b 0.25 delta spreads for 4 of 5 names (SNDK, CRWV, RKLB, NVDA), 8 further costings. Total costings 38, verdicts 38 FAIL, 0 SURVIVES. The single gap: AMD E2b, not priceable, reason printed in the AMD section. At the money call and put tables are printed for both the nearest and the next expiry for all 5 names, 20 contracts in full.

## What this test does and does not settle

This is a fresh, current chain test, run 2026-11-15 evening on Friday 2026-11-13 close data, and its result agrees with the Wave 4 conclusion for a different chain snapshot: the overnight edge, which is 6 to 29 bp per name in the stock, is one to two orders of magnitude smaller than the cost of carrying listed options over the same night at these IV levels (IV 0.51 to 1.14 at the money) and these quoted widths. It does not settle expressions never priced here: no puts as the long leg (the edge is long overnight, and the at the money puts are printed for the record), no strikes beyond the collected windows except as named, no intraday Monday exit timing, and no volatility trade. Those would be different tests, not corrections to this one.

STATUS: PARTIAL. Evidence pointers: nested chain fetches, HTTP 200, 2026-11-16T00:40:05Z to 00:40:13Z for SNDK, CRWV, RKLB, NVDA, AMD, expiries used 2026-11-16 and 2026-11-18 (NVDA, AMD) and 2026-11-20 and 2026-11-27 (SNDK, CRWV, RKLB); DXLink Quote and Greeks collections 2026-11-16T00:43Z and 00:46Z under a quote token issued 00:42:32Z, level demo, delayed; REST market-metrics cross-check fetched 2026-11-16T00:45:06Z with IV timestamps 2026-11-13T20:48Z to 20:55Z; REST market data 403 Forbidden errors preserved in the routes section; spot sources and the AMD 1Day defect named in the spot section. Why PARTIAL and not GREEN: every briefed expression was priced and verdicted on current chains, but one variant (AMD E2b) is not priceable on chain deltas for the reason named, the AMD primary spot is disputed between desk sources, and three priced legs carry crossed quotes. The headline verdict (no expression survives, best weekend miss 12.34 bp, best weeknight miss 8.83 bp) is robust to all three gaps, as shown in the sensitivity notes per name.
