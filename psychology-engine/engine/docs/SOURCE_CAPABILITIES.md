# Versioned source capabilities — 2026-10-30

Configuration changes require recording a new version; source access and publication cadence are not permanent facts.

| Source | Implemented access | Actual construct | Availability and caveat |
|---|---|---|---|
| Federal Reserve press RSS | Public RSS parser and bounded reader | Institutional language | Event-driven. Feed publication time preserved; first-seen is actual collection. Lexicon headlines are weak sentiment evidence. https://www.federalreserve.gov/feeds/press_all.xml |
| Cboe VIX history | Public CSV parser and bounded reader | Option-implied risk | Daily close. Historical dates lack verified release timestamps in this adapter; publication is conservatively set to first retrieval. Subsequent changes produce new revisions. https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv |
| Explicit user data | JSON/CSV import | Declared dimension and units | User must have access rights and verify vintage timestamps. No private mailbox, profile or credential harvesting. |
| SF Fed Daily News Sentiment | Public CSV adapter | News sentiment index | Research thread reported successful public CSV read; daily observations with weekly publication. https://www.frbsf.org/wp-content/uploads/news-sentiment-chart-2.csv |
| Wikimedia pageviews | Public JSON adapter | Attention, not opinion direction | Research thread reported successful API read. Article choice, bot exclusions, date windows and revisions matter. https://wikimedia.org/api/rest_v1/ |
| CFTC COT | Import only | Reported trader positioning | Research thread reports Friday publication of Tuesday positions; announced future semiweekly reporting is not assumed active. https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm |
| NAAIM exposure | Import only; access restricted for current data | Manager equity exposure | Research thread reports public index delayed three months; current data require membership/permission. https://www.naaim.org/programs/naaim-exposure-index/ |
| Google Trends | No automated adapter | Relative search attention | Official API limited alpha; no universal-access assumption. https://developers.google.com/search/apis/trends |
| Stocktwits | No adapter | Self-selected investor expression | Developer registration closed; enterprise access negotiated per research findings. https://api.stocktwits.com/developers |
| YouTube | No adapter | Creator/audience expression | Derived sentiment may require approved analytics use; do not infer approval from public viewing. https://developers.google.com/youtube/terms/developer-policies |
| Prediction markets | No adapter | Contract-specific risk-neutral/microstructure-influenced prices | Contract rules, liquidity, fees, participant selection and resolution must be audited; arbitrary contracts are not a sentiment index. |

The research thread supplied source observations and access notes, not a grant of credentials or permission for blocked destinations. In this implementation environment, Fed, Cboe, FRBSF and Wikimedia hosts are absent from the network allowlist. The actual CLI probe returned `PermissionError` at preflight, made no source HTTP request and did not bypass the policy. Separate research-thread successful GETs do not count as an engine live-ingestion validation. No raw public-source dataset is redistributed in this archive.

FRBSF date values describe daily observations, not verified publication dates. The adapter stamps publication conservatively at collection because weekly release times and historical vintages are not present in the chart CSV. Wikimedia counts describe a completed UTC day; event_time is day end and publication/first-seen are collection time. API publication/revision timing is not inferred from the pageview date. Both adapters retain revised values and configuration versions. Missing FRBSF values remain unknown.
