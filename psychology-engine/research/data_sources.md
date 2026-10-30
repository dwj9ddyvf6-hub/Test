# Psychology Engine — source acquisition and interpretation map

**As of 30 October 2026.** This is a source-feasibility map, not a trading signal, legal opinion, deployed collector or claim of prediction accuracy. Source facts are linked to primary documentation. Bias/inference boundaries and proposed features are analyst assessments and must be tested.

## What can be built first

1. **Wikimedia attention:** successful unauthenticated JSON sample; CC0 analytics data; daily bins loaded after closure. Production needs genuine contact-bearing User-Agent and a loading watermark (404 is not necessarily zero).
2. **Federal Reserve official RSS:** successful read. Suitable for event discovery and policy-language deltas, not social consensus.
3. **FRBSF economic-news tone:** successful public CSV. Daily observations are published **weekly**. Latest retrieved observation was October 25; do not relabel as an October 30 live pulse.
4. **Cboe VIX public historical CSV:** successful retrieval, daily—not live. Resolve intended non-display/derived-product and redistribution rights before turning a research download into a product feed.
5. **Kalshi and Polymarket:** unauthenticated catalog reads succeeded. Select economically relevant contracts and fetch timestamped executable books before building expectations features. The catalog samples alone do not prove macro coverage or live price freshness.
6. **SEC EDGAR, CFTC, NY Fed, EC/ECB, SPF:** strong documented public candidates, not tested collectors here. SEC requires genuine identifying contact and aggregate rate control. CFTC release-calendar versioning is essential.

No account was created, license purchased, message sent to a provider, wallet connected or order submitted. No denial was bypassed.

## Important traps caught in current documentation

- **NAAIM:** public values have a **three-month delay**; current data requires partner/member access. Commercial integration requires express permission. [NAAIM](https://naaim.org/programs/naaim-exposure-index/)
- **Google Trends:** official API is still limited alpha; do not label an unofficial scraper an available official connector. [Google](https://developers.google.com/search/apis/trends)
- **Stocktwits:** new developer registrations are closed; Enterprise data access is negotiated. [Developer page](https://api.stocktwits.com/developers)
- **YouTube:** a working comment endpoint is not permission to manufacture/retain sentiment scores. Current analytics approval and derived-metrics policies matter. [Policy guide](https://developers.google.com/youtube/terms/developer-policies-guide), [derived metrics](https://developers.google.com/youtube/terms/derived-metrics-policy)
- **CFTC:** October 27 announcement plans twice-weekly COT by year-end; today’s schedule remains Tuesday observation/Friday publication unless an actual transition is verified. [Announcement](https://www.cftc.gov/PressRoom/PressReleases/9316-26)
- **Baker-Wurgler:** current series has five proxies, revised 2026 orthogonalization and is intended as a low-frequency **level**, not a first-difference pulse. [Authors’ repository](https://github.com/BWInvestorSentimentIndex/BakerandWurglerInvestorSentimentIndex)
- **FRBSF:** daily data labels with weekly release frequency. **FINRA short volume ≠ short interest**. **Tradier real-time quotes ≠ real-time hourly Greeks**. These are measurement distinctions, not cosmetic caveats.

## FRED scope: unresolved for a persistent engine, not a blanket ban on inference

The current full terms include the phrase “development or training of any software program or system or machine learning” in API restrictions. Separately, API and MCP provisions restrict caching/archiving and incorporating content in databases. Yet the same terms explicitly describe an MCP connector for AI host platforms and discuss generated outputs. Therefore: do not equate model training, on-demand inference, personal reading and systematic archival ingestion. This engine’s persistent storage and development use needs specific clarification/permission; a universal claim that all AI-assisted FRED reads are forbidden is unsupported. Source copyrights remain independent. Use original-agency data when its own access/reuse conditions permit it—not as a route around a provider-specific access denial. [Current full terms, API and MCP sections](https://fred.stlouisfed.org/legal/terms/)

## Required observation record and point-in-time discipline

`source_id, entity_id, observation_start/end, source_published_at, vendor_received_at, first_seen_at, retrieved_at, updated_at, release_id, raw_hash, revision_of, units, denominator, coverage, query_scope, source/license_version, model_version, quality_flags`.

Keep original observation, source publication, first usable receipt and later revision separate. Unknown time must stay unknown or be a bounded interval. Historical period labels do not establish historical availability. Archive only where rights permit; otherwise preserve compliant identifiers/receipts or seek rights before storing raw content. Do not silently replace a failed source with scraped data or another provider.

## Normalization and fusion contract

- Preserve raw units before normalization. Use a lagged expanding/rolling median-MAD or percentile fitted **only to observations available then**; include sample count and minimum-history guard. Never use full-sample min/max or z-scores in backtests.
- Text/attention: deduplicate syndicated articles and near-identical posts; normalize by monitored source volume, cap author/outlet concentration; separate attention, tone, disagreement, novelty and uncertainty. One viral story is not many independent observations.
- Price-derived inputs (VIX, skew, breadth, funding, prediction prices) belong in a **market-pricing/behavior** group. Do not count them as independent confirmation of survey beliefs or use them to claim psychological causation.
- Compute expected update time and age using release calendars. Missing, delayed, revised, denied and true neutral are different states. Do not impute missing sources as neutral. Do not forward-fill daily relevance into an intraday trigger.
- Build separate slow surveys, text/news, attention, positions/flows, options/risk prices, liquidity and explicit-expectations panels. Any combined score must show coverage and freshness, not a precise-looking unsupported “fear” probability.
- A trade feature requires incremental out-of-sample improvement over price/volatility/market-event baselines, execution costs, multiple-testing controls and realistic source availability. Collection success alone establishes no edge.

## Source matrix

The JSON registry contains the same fields in machine-readable form. “Public documented” means documentation supports access, not that a collector was exercised. Prices below are source-advertised where stated, not purchased entitlements.

### 1. AAII Investor Sentiment Survey — `aaii`
- **Family:** survey
- **Original observation:** Registered-member bullish/neutral/bearish six-month stock-market outlook.
- **Publication / availability:** Survey Thu 00:01 to Wed 23:59 ET; publish Thu morning. Week-ending label is NOT publication timestamp.
- **Units / horizon:** percent; percentage-point bull-minus-bear / weeks to months
- **Access / cost:** public_current_members_history; Current web results free; complete history advertised to members; no official unrestricted API verified.
- **Rights:** Page says individual use; membership is not redistribution permission. Confirm machine-use/commercial rights before persistent product ingestion.
- **Coverage bias:** Self-selected AAII members, not representative of all households or invested dollars.
- **Manipulation / distortion:** Medium: response selection, media salience; one vote/member does not remove demographic bias.
- **Can infer:** Stated retail outlook distribution.
- **Cannot infer:** Actual positions, causal contrarian alpha, or next-session direction.
- **Feature concept:** bull-minus-bear level; neutral share; own-series expanding percentile, with respondent count when available.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Weekly survey since July 1987; full history member access.
- **Primary sources:** [source 1](https://www.aaii.com/sentimentsurvey), [source 2](https://www.aaii.com/sentimentsurvey/sent_results)

### 2. NAAIM Exposure Index — `naaim`
- **Family:** survey_positioning
- **Original observation:** Member managers report US equity exposure at Wednesday market close; -200% to +200% permitted.
- **Publication / availability:** Weekly Wednesday observation; public display THREE MONTHS delayed; current weekly subscription/member channel.
- **Units / horizon:** percent net equity exposure / weeks to months
- **Access / cost:** public_delayed_current_paid; Partner subscription or member login for current/history; current dollar tariff not verified.
- **Rights:** Express permission required for commercial use; public viewing is not permission to integrate.
- **Coverage bias:** Small active-manager membership sample; composite firm exposure masks strategies; not AUM representative unless methodology establishes it.
- **Manipulation / distortion:** Low direct manipulation; medium sample/response bias.
- **Can infer:** Reported exposure and dispersion in sampled managers.
- **Cannot infer:** All institutional sentiment or holdings now from the delayed page.
- **Feature concept:** Mean/median exposure and interquartile spread; changes only after actual publication.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** More than 20 years advertised; current/full history subscription.
- **Primary sources:** [source 1](https://naaim.org/programs/naaim-exposure-index/)

### 3. University of Michigan Surveys of Consumers — `umich`
- **Family:** macro_confidence
- **Original observation:** Household economic conditions, expectations and inflation beliefs.
- **Publication / availability:** Monthly preliminary and final releases; use official release calendar. Public detailed data site updates after embargo ending FOUR WEEKS after final release.
- **Units / horizon:** index; percent inflation expectations / months
- **Access / cost:** public_delayed_detail_current_licensed; Headline releases readable; timely detailed redistribution/subscription terms need review.
- **Rights:** University-owned survey; public access does not grant unrestricted redistribution.
- **Coverage bias:** Household survey, sample and mode changes; political/news response effects.
- **Manipulation / distortion:** Low direct manipulation; nonresponse and framing risk.
- **Can infer:** Consumer outlook and inflation expectation distribution.
- **Cannot infer:** Investor positioning, live intraday psychology; final data available at preliminary time.
- **Feature concept:** Preliminary and final series separate; surprise only vs timestamped lawful consensus; expectation dispersion.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://data.sca.isr.umich.edu/faq.php), [source 2](https://data.sca.isr.umich.edu/fetchdoc.php?docid=79628)

### 4. Conference Board US Consumer Confidence — `conference_board`
- **Family:** macro_confidence
- **Original observation:** Consumer current situation and six-month expectations from online panel.
- **Publication / availability:** Monthly 10:00 ET last Tuesday, subject to release calendar; preliminary cutoff before publication.
- **Units / horizon:** index; response percent; percentage-point labor differential / months
- **Access / cost:** public_release_paid_dataset; Public summary; premium dataset/subscription for granular history.
- **Rights:** Proprietary index and data; subscription and redistribution rights must be checked.
- **Coverage bias:** Online survey household population; expectations not executed expenditure.
- **Manipulation / distortion:** Low direct manipulation; medium composition and political framing.
- **Can infer:** Confidence, jobs-plentiful minus hard-to-get, expectation changes.
- **Cannot infer:** Stock-market fear, actual hiring, or reliable equity return prediction.
- **Feature concept:** Within-series level/innovation; labor differential; expectations-current gap.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.conference-board.org/topics/consumer-confidence/), [source 2](https://www.conference-board.org/north-america/press/economy-strategy-finance/consumer-dynamics)

### 5. NY Fed Survey of Consumer Expectations — `nyfed_sce`
- **Family:** macro_confidence
- **Original observation:** Rotating household panel expectations for inflation, jobs, income, spending, credit.
- **Publication / availability:** Monthly release per CMD calendar; microdata availability differs from aggregate release.
- **Units / horizon:** percent probability/rate; dollars as applicable / months to years
- **Access / cost:** public_documented_not_tested; Public aggregate downloads; no account necessary for published files.
- **Rights:** Use NY Fed terms and attribution; microdata-specific requirements; do not infer named individuals.
- **Coverage bias:** Household panel coverage and attrition; median beliefs differ from market-price weights.
- **Manipulation / distortion:** Low; response noise and survey anchoring.
- **Can infer:** Household expectation levels/disagreement by predefined group.
- **Cannot infer:** Actual outcome probabilities without calibration or investors marginal beliefs.
- **Feature concept:** Median 1y/3y/5y inflation, dispersion, unemployment/job-loss expectations, rolling percentile.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.newyorkfed.org/microeconomics/databank.html), [source 2](https://www.newyorkfed.org/microeconomics/sce/sce-faq), [source 3](https://www.newyorkfed.org/microeconomics/calendar.html)

### 6. ECB Consumer Expectations Survey — `ecb_ces`
- **Family:** macro_confidence
- **Original observation:** Monthly euro-area household online survey.
- **Publication / availability:** Fieldwork typically first Thursday through Tuesday before next round; monthly aggregate publication, not interview-time availability.
- **Units / horizon:** percent; probabilities / months to years
- **Access / cost:** public_documented_not_tested; Public aggregate and microdata downloads.
- **Rights:** ECB attribution and dataset conditions; no raw personal identification.
- **Coverage bias:** Country coverage expanded from six to eleven; panel/methodology changes require flags.
- **Manipulation / distortion:** Low direct manipulation.
- **Can infer:** Euro-area consumer inflation/income/labor expectations.
- **Cannot infer:** Global investors or tradeable market probabilities.
- **Feature concept:** Country-neutralized expectation innovation and cross-country dispersion.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.ecb.europa.eu/stats/ecb_surveys/consumer_exp_survey/html/index.en.html), [source 2](https://www.ecb.europa.eu/stats/ecb_surveys/consumer_exp_survey/shared/pdf/ecb.CES_microdata_guide.en.pdf)

### 7. European Commission Business and Consumer Surveys — `ec_bcs`
- **Family:** macro_confidence
- **Original observation:** Harmonized sector and consumer judgments, expectations and uncertainty.
- **Publication / availability:** Monthly release calendar; flash consumer and final releases distinct; fieldwork generally first 2-3 weeks.
- **Units / horizon:** net balance; standardized indicator / months
- **Access / cost:** public_documented_not_tested; Public ZIP/XLSX, new browser/API in testing transition.
- **Rights:** EU reuse conditions and attribution; validate dataset metadata.
- **Coverage bias:** National partner samples, sector weights, country composition.
- **Manipulation / distortion:** Low; survey framing and response composition.
- **Can infer:** Sector/country confidence and breadth of expected deterioration.
- **Cannot infer:** Cash flows, equity direction or physical probability from standardized index.
- **Feature concept:** Sector net-balance percentile; confidence breadth and dispersion across countries.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys_en), [source 2](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/time-series_en), [source 3](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/methodology-business-and-consumer-surveys/methodological-concepts_en)

### 8. Philadelphia Fed Survey of Professional Forecasters — `spf`
- **Family:** expectations
- **Original observation:** Professional macro point forecasts and probability distributions.
- **Publication / availability:** Quarterly: questionnaire around first GDP estimate; deadline ~10 days later; publication ~3 days after deadline; historical deadline/publication dates provided.
- **Units / horizon:** rates; percent probabilities; cross-sectional dispersion / quarters to years
- **Access / cost:** public_documented_not_tested; Public Excel releases/history.
- **Rights:** Attribute Philadelphia Fed; verify any source-specific conditions for redistribution.
- **Coverage bias:** Professional forecasters, not position-weighted investors; uneven variables/horizons.
- **Manipulation / distortion:** Low; herding and strategic forecasts possible.
- **Can infer:** Forecast consensus, disagreement and stated recession probability.
- **Cannot infer:** Disagreement equals individual uncertainty; current market expectations between releases.
- **Feature concept:** Anxious Index; dispersion separately from mean; horizon-aligned revision.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Quarterly survey begins 1968; Philadelphia Fed administration begins 1990.
- **Primary sources:** [source 1](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters), [source 2](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/spf-faqs), [source 3](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/dispersion-forecasts)

### 9. NFIB Small Business Economic Trends — `nfib`
- **Family:** macro_confidence
- **Original observation:** Small-business survey optimism, uncertainty, hiring, sales and credit plans.
- **Publication / availability:** Monthly PDF/release; observation month precedes release; exact historical time requires calendar/archive.
- **Units / horizon:** index (1986=100); net response percent / months
- **Access / cost:** public_reports_no_api_verified; Free reports; no supported API verified.
- **Rights:** Copyrighted report; persistent extraction/redistribution rights not confirmed.
- **Coverage bias:** NFIB small-business membership rather than all firms; sector/political composition.
- **Manipulation / distortion:** Low direct manipulation; medium selection/framing.
- **Can infer:** Sampled small-business confidence and plans.
- **Cannot infer:** Large-cap management sentiment or realized hiring.
- **Feature concept:** Soft versus hard-component divergence, uncertainty and hiring plans; seasonal-adjustment vintage.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.nfib.com/wp-content/uploads/2026/04/NFIB-SBET-Report-March-2026.pdf)

### 10. Federal Reserve SLOOS — `sloos`
- **Family:** macro_credit
- **Original observation:** Loan-officer reports of lending standards, terms and demand.
- **Publication / availability:** Usually quarterly near FOMC schedule; respondent period and release differ; exceptional extra surveys. DDP build-package retirement announced for week of Nov 9, 2026.
- **Units / horizon:** net percent tightening/stronger demand / quarters
- **Access / cost:** public_documented_not_tested; Public HTML/PDF/chart data; monitor direct-feed migration.
- **Rights:** Federal Reserve terms/attribution; direct release rather than assumed FRED archive permission.
- **Coverage bias:** Up to 80 large domestic banks and 24 foreign branches/agencies; not all lenders.
- **Manipulation / distortion:** Low; self-reporting and thresholds.
- **Can infer:** Credit supply/demand conditions and lenders risk tolerance.
- **Cannot infer:** Borrower emotional state or short-run asset price prediction.
- **Feature concept:** Net tightening and demand separately, bank-size split, point-in-time first-release change.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.federalreserve.gov/data/sloos.htm), [source 2](https://www.federalreserve.gov/feeds/sloos.html)

### 11. Baker-Wurgler Investor Sentiment Index — `baker_wurgler`
- **Family:** research_composite
- **Original observation:** Five market-based proxies; current version drops NYSE turnover.
- **Publication / availability:** Monthly low-frequency period-end levels; actual repo release/commit time determines availability. Not a real-time feed.
- **Units / horizon:** standardized principal-component level / months to years
- **Access / cost:** public_research_versioned; Public workbook and SAS/Stata code; input databases can require licenses.
- **Rights:** Repository public but broad commercial license not verified; underlying CRSP/Compustat/Morningstar rights separate.
- **Coverage bias:** Composite shares IPO/issuance/valuation inputs with markets; full-sample processing/revisions.
- **Manipulation / distortion:** Low direct manipulation; model/look-ahead risks high.
- **Can infer:** Slow speculative environment proxy under published methodology.
- **Cannot infer:** Day-to-day pulse or first-difference sentiment changes (authors explicitly warn against that).
- **Feature concept:** Versioned level/percentile only; freeze vintage and transformations.
- **Revisions:** 2026 SENT_ORTH preprocessing changed to detrending; data subject to improvement/revision; archive commit+workbook hash.
- **Historical coverage:** Public workbook historical levels; latest known methodology version March 2026; period end is not publication time.
- **Primary sources:** [source 1](https://github.com/BWInvestorSentimentIndex/BakerandWurglerInvestorSentimentIndex)

### 12. Federal Reserve official RSS / policy language — `fed_rss`
- **Family:** official_text
- **Original observation:** Official press releases, monetary policy statements, speeches and testimony.
- **Publication / availability:** Event publication/RSS pubDate; capture first_seen and updated times; statement, transcript and minutes are different events.
- **Units / horizon:** document; sentence-level scored text / minutes to weeks
- **Access / cost:** tested_public_readonly; No API key; published RSS.
- **Rights:** Federal Reserve site terms; retain provenance and avoid third-party copyrighted attachments without permission.
- **Coverage bias:** Policy makers selected language and prepared remarks, not population sentiment.
- **Manipulation / distortion:** Low forgery on official host; high strategic-communication/endogeneity.
- **Can infer:** Policy-language changes, topic emphasis and uncertainty.
- **Cannot infer:** Private FOMC beliefs or automatic hawkish-to-bearish equity mapping.
- **Feature concept:** Document-type matched novelty, hedging/uncertainty, hawkishness with cited sentence evidence.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Endpoint/tool:** `https://www.federalreserve.gov/feeds/press_all.xml`
- **Exact probe receipt:** `receipts/fed_rss.json`
- **Primary sources:** [source 1](https://www.federalreserve.gov/feeds/feeds.htm)

### 13. SEC EDGAR filings and issuer earnings exhibits — `sec_filings`
- **Family:** official_text
- **Original observation:** As-filed 10-K/10-Q/8-K/6-K text, risk factors, MD&A, earnings releases.
- **Publication / availability:** Separate report period, filing acceptance, website availability (~1-3 minutes typical), our first_seen. API updates throughout day; amendments distinct.
- **Units / horizon:** document; token proportion; topic novelty / event to quarters
- **Access / cost:** public_documented_identity_required; No key; declared User-Agent with genuine contact; max 10 requests/sec across machines.
- **Rights:** Comply fair access; issuer-authored material may have third-party copyright; no raw corpus redistribution assumption.
- **Coverage bias:** US registrants; boilerplate and legal incentives; filing lag.
- **Manipulation / distortion:** Low host tampering; managerial disclosure incentives/obfuscation.
- **Can infer:** Changes in disclosed risks, forward guidance, constraints and uncertainty.
- **Cannot infer:** Management mental state or all earnings Q&A; 8-K is not transcript.
- **Feature concept:** Section-matched year-over-year text novelty; uncertainty and guidance change; separate boilerplate.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Recent submissions JSON plus older referenced submission files and EDGAR archives; historical availability metadata must be preserved.
- **Endpoint/tool:** `https://data.sec.gov/submissions/CIK##########.json`
- **Primary sources:** [source 1](https://www.sec.gov/about/developer-resources), [source 2](https://www.sec.gov/about/webmaster-frequently-asked-questions), [source 3](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

### 14. Issuer investor-relations earnings calls/transcripts — `issuer_ir`
- **Family:** earnings_text
- **Original observation:** Issuer releases, prepared remarks, Q&A audio/transcripts when issuer publishes them.
- **Publication / availability:** Call time, webcast upload, transcript publish and correction times distinct; no universal API or fixed latency.
- **Units / horizon:** document/audio; text features / event to quarters
- **Access / cost:** issuer_specific_rights_review; Some public; others only audio or licensed transcript vendors.
- **Rights:** Check each issuer/provider automation and transcript rights; do not use unauthenticated transcript scrapers or assume YouTube caption extraction.
- **Coverage bias:** Voluntary disclosure; management/analyst selection; missing Q&A and transcription errors.
- **Manipulation / distortion:** High strategic language; low direct source falsification on official host.
- **Can infer:** Public management confidence/uncertainty and analyst challenge intensity.
- **Cannot infer:** Private beliefs, deception certainty or causal language alpha.
- **Feature concept:** Prepared-versus-Q&A uncertainty gap; evasive/non-answer rate with human validation.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4), [source 2](https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast)

### 15. GDELT DOC 2.0 — `gdelt_doc`
- **Family:** news
- **Original observation:** Indexed news article metadata/search, source coverage and tone summaries.
- **Publication / availability:** Publication claims differ from GDELT seen time; 15-minute aggregation available; endpoint service has no verified SLA.
- **Units / horizon:** articles; share of monitored coverage; tone / hours to weeks
- **Access / cost:** documented_public_probe_503; Free no-key API; BigQuery compute can cost money.
- **Rights:** GDELT database advertised open; linked article text/images remain publishers rights.
- **Coverage bias:** Monitored outlets/languages and syndication; denominator drift, keyword ambiguity.
- **Manipulation / distortion:** High source manipulation/PR amplification; model tone error.
- **Can infer:** Coverage attention, narrative prevalence and source diversity.
- **Cannot infer:** Population belief or independent evidence count from duplicate stories.
- **Feature concept:** Topic article share, de-duplicated source count, source-adjusted tone novelty.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Endpoint/tool:** `https://api.gdeltproject.org/api/v2/doc/doc`
- **Exact probe receipt:** `receipts/gdelt.json`
- **Primary sources:** [source 1](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/), [source 2](https://gdeltproject.org/data.html)

### 16. GDELT GKG / event raw files — `gdelt_gkg`
- **Family:** news
- **Original observation:** Machine annotations of themes, organizations, emotions and news events.
- **Publication / availability:** GDELT 2.0 files every 15 minutes; event occurrence, source article time and batch seen time differ.
- **Units / horizon:** theme/entity counts; tone; events / hours to months
- **Access / cost:** public_documented_not_tested; Raw files free; storage/compute sizable; BigQuery billing possible.
- **Rights:** Open annotations do not license third-party fulltext.
- **Coverage bias:** Extraction/translation errors, duplicate news and changing source mix.
- **Manipulation / distortion:** High propaganda/syndication exposure.
- **Can infer:** Narrative diffusion and geographically distributed attention.
- **Cannot infer:** Every detected event is new or factual; precise tradeable timestamp from event date.
- **Feature concept:** Entity/topic coverage shares with outlet-cluster dedup and publication-age decay.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://gdeltproject.org/data.html), [source 2](https://gdeltproject.org/)

### 17. San Francisco Fed Daily News Sentiment Index — `frbsf_news`
- **Family:** news_composite
- **Original observation:** Economic news tone from 24 US newspapers via Factiva, composition-adjusted trailing weighted average.
- **Publication / availability:** DAILY observations but WEEKLY publication. Page updated Oct 26; probe latest row Oct 25. Historical row date is not when row was available.
- **Units / horizon:** sentiment index level / weeks to months
- **Access / cost:** tested_public_readonly; Public CSV/Excel; no key.
- **Rights:** Credited reproduction allowed except distribution for private gain under site policy; raw Factiva articles not licensed by index download.
- **Coverage bias:** US economic newspaper sample; smoothing and publisher composition.
- **Manipulation / distortion:** Medium editorial bias, low direct index manipulation.
- **Can infer:** Slow US economic-news narrative tone.
- **Cannot infer:** Intraday pulse, full market consensus or raw article availability.
- **Feature concept:** Level and first-release innovation; weekly as-of age flag; no fabricated intraday updates.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Daily index since 1980; recent CSV is an 18-month window, full Excel linked.
- **Endpoint/tool:** `https://www.frbsf.org/wp-content/uploads/news-sentiment-chart-2.csv`
- **Exact probe receipt:** `receipts/frbsf_news.json`
- **Primary sources:** [source 1](https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/), [source 2](https://www.frbsf.org/site-policies/)

### 18. Alpaca News API (candidate) — `alpaca_news`
- **Family:** news
- **Original observation:** Provider articles with headline, source, created_at, updated_at, symbols and original URL.
- **Publication / availability:** Creation/update clocks are not a guarantee of receipt latency or a real-time news entitlement.
- **Access:** Applicable API credentials, feed subscription, retention and redistribution permissions must be verified.
- **Inference boundary:** Candidate only. Operational news collection has not been established for this public reference package.
- **Feature concept:** Deduplicated entity tone and novelty; correction-aware article versions.
- **Primary documentation:** https://docs.alpaca.markets/us/docs/historical-news-data
- **Public receipt:** No connector-specific diagnostic receipt is distributed.

### 19. Reddit public discussions — `reddit`
- **Family:** social
- **Original observation:** Posts/comments/votes for approved communities and queries.
- **Publication / availability:** created_utc, edited time and first receipt distinct; votes/edits/deletions revise; search rankings mutable.
- **Units / horizon:** posts/authors/engagement; classified sentiment / hours to weeks
- **Access / cost:** credential_approval_required; API registration required; commercial purpose needs approval/agreement; no account or key created.
- **Rights:** Use only approved scope; retention/deletion, attribution and model-training restrictions; do not bypass with scraping.
- **Coverage bias:** Selected subreddits/users, bots, moderation, sarcasm; not representative retail.
- **Manipulation / distortion:** High brigading, bots, coordinated pumps and vote manipulation.
- **Can infer:** Expressed narrative/attention of observed community.
- **Cannot infer:** Positions, true beliefs, unique human counts or market-wide psychology.
- **Feature concept:** Unique-thread topic share; capped author contribution; novelty and disagreement; no personal profiles.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://redditinc.com/policies/data-api-terms), [source 2](https://redditinc.com/news/building-on-our-partnership-with-cision)

### 20. X public posts — `x`
- **Family:** social
- **Original observation:** Approved search/stream posts and engagement metadata.
- **Publication / availability:** Post creation, edit and vendor receipt clocks; stream vs REST entitlement distinct.
- **Units / horizon:** post/entity counts; engagement; sentiment / minutes to weeks
- **Access / cost:** paid_credential_required; Current docs use pay-per-usage credits; verify console unit rates and cap before purchase.
- **Rights:** Developer license, display and deletion rules; no unrestricted raw redistribution or scraping fallback.
- **Coverage bias:** Query/access-tier selection, deleted/private posts, bots and influential accounts.
- **Manipulation / distortion:** Very high coordinated amplification, impersonation and engagement gaming.
- **Can infer:** Observed public attention and narrative dispersion.
- **Cannot infer:** Representative opinion or truth of claims.
- **Feature concept:** Bot/duplicate-resistant source-weighted topic volume, novelty, sentiment/disagreement.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://docs.x.com/x-api/getting-started/pricing), [source 2](https://docs.x.com/x-api/fundamentals/rate-limits)

### 21. Stocktwits — `stocktwits`
- **Family:** social
- **Original observation:** Cashtag messages and self-labeled bullish/bearish stance.
- **Publication / availability:** Message creation and receipt; historical/aggregate updates depend on licensed feed.
- **Units / horizon:** messages; stance percent; watchers / hours to weeks
- **Access / cost:** new_developer_registration_closed; Developer page not accepting new registrations; Enterprise offers personalized API; quote required.
- **Rights:** No legacy unauthenticated endpoint assumed usable; enterprise data/retention rights required.
- **Coverage bias:** Speculative ticker-focused audience; cashtag ambiguity and self-label selection.
- **Manipulation / distortion:** High ticker promotion/bot clustering.
- **Can infer:** Platform-specific expressed stance and attention.
- **Cannot infer:** Whole-market sentiment, investor holdings, or all messages via a historical public API.
- **Feature concept:** Bull-bear share conditional on explicit labels; cashtag velocity, author concentration.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://api.stocktwits.com/developers), [source 2](https://help.stocktwits.com/c/faqs/faqs/is-stocktwits-free)

### 22. YouTube comments and attention — `youtube`
- **Family:** social
- **Original observation:** Public video/comment metadata through Data API; not automatic unrestricted captions.
- **Publication / availability:** publishedAt/updatedAt/receipt; likes/views revise. Quotas per API project; commentThreads may omit replies.
- **Units / horizon:** comments/views/likes; approved derived metrics / days to weeks
- **Access / cost:** credential_and_analytics_approval_required; API project/key needed; current docs commentThreads.list=1 unit, 10k daily units for general endpoints; search separate quota.
- **Rights:** 2026 derived metrics/sentiment requires approved audited analytics use case; raw text refresh/delete <=30 days; approved derived metrics may be retained <=36 months.
- **Coverage bias:** Channel selection, moderation, recommendation algorithms and disabled comments.
- **Manipulation / distortion:** High bots/promotion; fan community concentration.
- **Can infer:** Approved channel-level attention and expressed discussion.
- **Cannot infer:** Public comments can be freely warehoused or sentiment-scored merely because API reads work.
- **Feature concept:** Only after approval: topic/stance distribution with capped channels, no individual profiling.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://developers.google.com/youtube/data/reference/rest/v3/commentThreads/list), [source 2](https://developers.google.com/youtube/data/determine_quota_cost), [source 3](https://developers.google.com/youtube/terms/developer-policies-guide), [source 4](https://developers.google.com/youtube/terms/derived-metrics-policy)

### 23. Google Trends — `google_trends`
- **Family:** attention
- **Original observation:** Sample of anonymized aggregated searches by term/topic, geography and time.
- **Publication / availability:** UI values normalized within selected request; API alpha rolling five years, regular aggregation; no universal live access proved.
- **Units / horizon:** UI 0-100 relative index; alpha consistently scaled data / days to months
- **Access / cost:** official_api_limited_alpha; Manual UI/download possible; official API application/approval required; no approval sought.
- **Rights:** Google terms; do not deploy unofficial pytrends scraping as an official connector or evade denials.
- **Coverage bias:** Search users not investors; sampling, query meaning, geography and denominator.
- **Manipulation / distortion:** Medium event-driven media amplification and query gaming.
- **Can infer:** Relative information-seeking attention.
- **Cannot infer:** Bullish/bearish sentiment from search volume alone or absolute search count from 0-100.
- **Feature concept:** Anchored topic basket; same query scope; first-seen-vintage attention percentile.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Official alpha promises rolling last five years; UI coverage/granularity differs.
- **Primary sources:** [source 1](https://developers.google.com/search/apis/trends), [source 2](https://developers.google.com/search/docs/monitor-debug/trends-start)

### 24. Wikimedia pageviews — `wikimedia`
- **Family:** attention
- **Original observation:** Per-article page requests with project/access/agent filters; user filter excludes identified automation.
- **Publication / availability:** Daily bin closes UTC; usually loaded in hours, sometimes >=24h. 404 may mean zero OR not loaded.
- **Units / horizon:** pageviews/day / days to weeks
- **Access / cost:** tested_public_readonly; Free no-key API; real contact-bearing User-Agent needed for production; sequential bounded requests.
- **Rights:** Analytics data CC0 1.0; honor API rate/stability policy.
- **Coverage bias:** Wikipedia readers not investors; page naming/redirects/language selection; user-agent bot classification imperfect.
- **Manipulation / distortion:** Medium artificial traffic; major nonfinancial events confound.
- **Can infer:** Attention to predefined concepts/entities.
- **Cannot infer:** Direction or fear from raw pageviews; missing=zero before watermark validated.
- **Feature concept:** log1p views minus rolling day-of-week baseline, article/project share, anti-spike checks.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Pageview API series begins July 1, 2015; exact article coverage varies.
- **Endpoint/tool:** `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/user/{article}/daily/{start}/{end}`
- **Exact probe receipt:** `receipts/wikimedia.json`
- **Primary sources:** [source 1](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html), [source 2](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/troubleshooting.html), [source 3](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html)

### 25. Cboe VIX daily history — `cboe_vix`
- **Family:** options_risk_price
- **Original observation:** Option-price-derived expected 30-day SPX volatility index; daily historical OHLC.
- **Publication / availability:** Market index time vs EOD file publication/receipt separate; updated daily, exact EOD upload SLA not verified.
- **Units / horizon:** annualized volatility percent / days to months
- **Access / cost:** tested_public_history_rights_review; Public CSV download; live index feed separate entitlement.
- **Rights:** Public download not broad derived-product/non-display/redistribution license; confirm intended automated/commercial use with Cboe policies.
- **Coverage bias:** SPX option prices reflect hedging demand, risk premia and liquidity, not pure beliefs.
- **Manipulation / distortion:** Low direct but microstructure/settlement distortions possible.
- **Can infer:** Market price of near-term variance exposure.
- **Cannot infer:** Physical crash probability, emotion score or expected direction.
- **Feature concept:** log VIX level/change, expanding percentile, IV-minus-matched-realized vol with both clocks.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Official daily index history from 1990; methodology and historical variant distinctions apply.
- **Endpoint/tool:** `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`
- **Exact probe receipt:** `receipts/cboe_vix.json`
- **Primary sources:** [source 1](https://www.cboe.com/tradable-products/vix/vix-historical-data), [source 2](https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf), [source 3](https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf)

### 26. Cboe VVIX / VIX9D / cross-asset volatility — `cboe_vol_family`
- **Family:** options_risk_price
- **Original observation:** Vol-of-vol, short-horizon implied vol and selected asset-specific implied volatility indices.
- **Publication / availability:** Daily public histories; horizons differ; intraday licensed separately.
- **Units / horizon:** annualized vol/index points / days to months
- **Access / cost:** public_history_not_tested; Public linked histories; licensed intraday feeds.
- **Rights:** Cboe data policies; verify non-display/derived-index/redistribution scope.
- **Coverage bias:** Underlying-option liquidity, maturity and different computation universes.
- **Manipulation / distortion:** Medium market microstructure; low direct data manipulation.
- **Can infer:** Term/event concentration of option insurance prices.
- **Cannot infer:** Independent psychology votes when sharing same options; guaranteed stress forecast.
- **Feature concept:** VIX9D/VIX ratio, VVIX conditional percentile, cross-asset volatility dispersion.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.cboe.com/tradable-products/vix/vix-historical-data), [source 2](https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf)

### 27. Cboe SKEW / left-tail implied risk — `cboe_skew`
- **Family:** options_risk_price
- **Original observation:** SPX option-price distribution asymmetry/tail pricing; methodology-specific indices.
- **Publication / availability:** Daily/intraday per licensed index; public-history endpoint not validated here.
- **Units / horizon:** index points; risk-neutral moment measure / weeks to months
- **Access / cost:** methodology_verified_feed_unverified; Licensed feed or official permitted history; exact quote needed.
- **Rights:** Cboe index/derived-data policies.
- **Coverage bias:** Far-OTM spreads, risk premia, maturity interpolation and option demand.
- **Manipulation / distortion:** Medium liquidity/quote sensitivity.
- **Can infer:** Relative price of downside-tail exposure.
- **Cannot infer:** Physical crash probability or universally bearish signal at high SKEW.
- **Feature concept:** Skew conditional on ATM vol; 25delta risk reversal from coherent surface; no physical-probability relabel.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://cdn.cboe.com/resources/education/research_publications/gladius-research-volatility-strategy-effects-on-us-implied-volatility-surface.pdf), [source 2](https://cdn.cboe.com/api/global/us_indices/governance/Cboe_SnP_500_Left_Tail_Volatility_Index_Methodology.pdf)

### 28. Cboe option volume / put-call ratios — `cboe_putcall`
- **Family:** options_activity
- **Original observation:** Calls/puts contract volume by published market category; intraday cumulative snapshots.
- **Publication / availability:** Page says all times Central; share/notional values delayed >=20 minutes; final daily values distinct from partial day.
- **Units / horizon:** contracts; put/call ratio / days to weeks
- **Access / cost:** public_delayed_statistics; Official page/CSV; older 2019-stopping archives not a current feed.
- **Rights:** Site terms apply; cite Cboe; do not scrape delayed quote tables (explicit prohibition).
- **Coverage bias:** Exchange/category coverage, index hedges, closing/opening and multi-leg trades mixed.
- **Manipulation / distortion:** Medium volume distortions from roll/expiry/0DTE/hedging.
- **Can infer:** Option activity balance within stated universe.
- **Cannot infer:** Net directional buying, opening demand or dealer gamma sign.
- **Feature concept:** Log put/call by category, same-time-of-day baseline, expiry/0DTE mix control where available.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.cboe.com/us/options/market_statistics/market/), [source 2](https://www.cboe.com/us/options/market_statistics/historical_data/)

### 29. OCC series and open interest — `occ_oi`
- **Family:** options_positions
- **Original observation:** Cleared options series and outstanding contracts.
- **Publication / availability:** Post-clearing daily OI; distinguish prior-day OI from today quote/volume; exact file schedule must be verified.
- **Units / horizon:** contracts by strike/expiry / days to weeks
- **Access / cost:** public_page_feed_not_verified; Official series search public; bulk feed/license depends product.
- **Rights:** OCC terms; raw bulk redistribution not inferred from page access.
- **Coverage bias:** Cleared listed options only; net exposure/opener identity not given.
- **Manipulation / distortion:** Low direct; corporate-action symbology and stale OI risks.
- **Can infer:** Where outstanding contracts concentrate.
- **Cannot infer:** Who is long/short, dealer inventory, net gamma or directional conviction.
- **Feature concept:** OI concentration, expiry profile and OI change aligned to clearing date.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.theocc.com/market-data/market-data-reports/series-and-trading-data/series-search)

### 30. Tradier option chains / ORATS Greeks — `tradier_chain`
- **Family:** options_surface
- **Original observation:** Standard chain quotes/volume/OI and ORATS-derived Greeks/IV.
- **Publication / availability:** Production quotes real-time for entitled accounts; sandbox delayed 15min; Greeks update hourly starting ~10:15. Quote and Greek clocks must stay separate.
- **Units / horizon:** USD; contracts; delta/gamma; IV decimal/percent as schema specifies / minutes to months
- **Access / cost:** existing_connector_possible_not_tested_here; Brokerage token/account; real-time for account holders; no credentials created.
- **Rights:** Brokerage/OPRA/ORATS and redistribution terms; public/distributed apps require partner status.
- **Coverage bias:** Chain exclusions, zero/crossed quotes and stale Greek estimates; no expired-option history at provider.
- **Manipulation / distortion:** Medium stale quotes; model assumptions.
- **Can infer:** Observed implied vol surface and insurance prices after quote-quality filtering.
- **Cannot infer:** Live Greeks from hourly data, risk-neutral equals physical probabilities, dealer positioning from OI alone.
- **Feature concept:** Constant-maturity ATM IV, 25delta skew, term slope; require quote/Greek-age thresholds and fit residuals.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://docs.tradier.com/docs/market-data), [source 2](https://docs.tradier.com/market-data/get-options-chains), [source 3](https://docs.tradier.com/)

### 31. CFTC Commitments of Traders — `cftc`
- **Family:** positioning
- **Original observation:** Reportable futures and delta-equivalent options positions by trader business category; TFF for financials, disaggregated for commodities.
- **Publication / availability:** Currently Tuesday close -> usually Friday 15:30 ET, holidays differ. Oct27 announcement plans Mon->Wed and Wed->Fri by end2026; NOT assumed active yet.
- **Units / horizon:** contracts; percent open interest / weeks to months
- **Access / cost:** public_api_documented_not_tested; Public Reporting Environment API works without tokens within reasonable use; no account needed.
- **Rights:** Government data; attribution, fair use of API; classifications aggregated for confidentiality.
- **Coverage bias:** Reporting thresholds; classifications by business purpose, not each trade motive; partial hedges outside market.
- **Manipulation / distortion:** Low direct; reclassification and reporting errors.
- **Can infer:** Group positioning/crowding and changes after publication.
- **Cannot infer:** All leveraged money is speculating; Tuesday holdings known Tuesday; direction of future prices.
- **Feature concept:** (long-short)/OI by category, expanding percentile, gross/spread positions and OI separately.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Legacy history from 1986; TFF/disaggregated from June 2006; public report type matters.
- **Primary sources:** [source 1](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm), [source 2](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm), [source 3](https://www.cftc.gov/PressRoom/PressReleases/9316-26), [source 4](https://publicreporting.cftc.gov/stories/s/r4w3-av2u)

### 32. ICI mutual fund flows and ETF net issuance — `ici`
- **Family:** fund_flows
- **Original observation:** Estimated weekly fund cash flows; ETF issuance is a different component; money-market asset stocks separate.
- **Publication / availability:** Weekly release lags reference week; e.g. Oct28 release for Oct21 week. Monthly actuals differ from weekly estimates.
- **Units / horizon:** USD millions; percent prior assets / weeks to months
- **Access / cost:** public_reports_rights_review; Public tables/summary files; detailed database subscription may apply.
- **Rights:** ICI requests permission to use/reproduce material; confirm automation and redistribution.
- **Coverage bias:** Survey asset coverage high but wrapper migration, CIT conversion, in-kind activity and price effects confound.
- **Manipulation / distortion:** Low direct; large structural one-offs important.
- **Can infer:** Net allocation/flow pressure in covered vehicles.
- **Cannot infer:** All withdrawals equal bearish selling; money-market asset rise equals new fear.
- **Feature concept:** Flows/prior AUM, equity/bond split, adjusted one-off flag, ETF and mutual fund separate.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.ici.org/research/stats/flows), [source 2](https://www.ici.org/research/statistics/mutual-funds/weekly-estimated-longterm-mutual-fund-flows)

### 33. EPFR fund flows — `epfr`
- **Family:** fund_flows
- **Original observation:** Fund-manager sourced flows, AUM, NAV and allocation datasets.
- **Publication / availability:** Product documentation lists daily/weekly T+1 and monthly T+16; verify purchased delivery SLA.
- **Units / horizon:** USD; percent flows; AUM / days to months
- **Access / cost:** paid_license_required; Negotiated API/data subscription; no price verified.
- **Rights:** Contract determines retention, derived outputs and redistribution.
- **Coverage bias:** Reporting fund subset, domicile/currency/retail-institutional composition.
- **Manipulation / distortion:** Low direct; flow estimates and reclassifications.
- **Can infer:** Covered investor-channel allocations.
- **Cannot infer:** Whole market flows or underlying trade direction without holdings.
- **Feature concept:** Flow/AUM surprise, geography/asset-class breadth, investor-type divergence.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://epfr.com/wp-content/uploads/2023/09/EFPR-Product-Overview.pdf)

### 34. FINRA daily short-sale volume — `finra_short_volume`
- **Family:** short_activity
- **Original observation:** Daily off-exchange short-marked trading volume in reported disseminated trades.
- **Publication / availability:** Daily trade-date aggregate posted after regular hours; no precise current SLA established here.
- **Units / horizon:** shares; short-volume/total reported volume / days to weeks
- **Access / cost:** public_files_api_documented; Daily files public; API access/quota requirements must be checked.
- **Rights:** FINRA data terms; do not imply consolidated all-venue coverage.
- **Coverage bias:** Off-exchange only; excludes undisclosed trades; market-making and same-day cover.
- **Manipulation / distortion:** Low reporting manipulation; very high interpretation misuse.
- **Can infer:** Short-marked activity fraction within covered tape.
- **Cannot infer:** Short interest, accumulating net shorts, naked shorts or bearish conviction.
- **Feature concept:** Short-marked share ratio by facility with own denominator and volume context.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://syndication.finra.org/content/short-interest-what-it-what-it-not), [source 2](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume), [source 3](https://www.finra.org/sites/default/files/DailyShortSaleVolumeFileLayout.pdf)

### 35. FINRA/exchange short interest — `short_interest`
- **Family:** short_positions
- **Original observation:** Snapshot of outstanding short positions reported twice monthly.
- **Publication / availability:** Settlement date, broker report date and public dissemination date distinct; use exchange-specific calendar.
- **Units / horizon:** shares; percent float; days-to-cover / weeks to months
- **Access / cost:** partial_public_full_universe_licensed; FINRA OTC public; listed shares via listing exchange/provider, often licensed.
- **Rights:** Provider licenses and point-in-time float data required; no bulk scraping fallback.
- **Coverage bias:** Two snapshots/month; derivatives and synthetic shorts absent; float estimates vary.
- **Manipulation / distortion:** Low direct; reporting corrections and corporate actions.
- **Can infer:** Reported short crowding as of old settlement date.
- **Cannot infer:** Daily net short flow, current borrow availability or squeeze inevitability.
- **Feature concept:** Short interest/point-in-time float, days-to-cover on matching ADV window, publication lag.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://syndication.finra.org/content/short-interest-what-it-what-it-not)

### 36. IBKR securities lending availability/fees — `ibkr_borrow`
- **Family:** borrow_constraint
- **Original observation:** Broker-specific lendable shares, lenders and indicative borrow rates.
- **Publication / availability:** Availability is snapshot/indicative, can change before borrow; actual locate and realized fee separate.
- **Units / horizon:** shares; annualized borrow percent / intraday to weeks
- **Access / cost:** account_credentials_required; Client Portal/API entitlement; no account accessed or created.
- **Rights:** Broker agreement; no redistribution or guaranteed inventory assumed.
- **Coverage bias:** IBKR inventory/lender network only; differs from market-wide borrow.
- **Manipulation / distortion:** Medium inventory withdrawal/concentration.
- **Can infer:** Specific broker borrow tightness and short implementation cost.
- **Cannot infer:** Market-wide short demand or a binding locate from indicative availability.
- **Feature concept:** Fee percentile/change, availability/ADV and persistence with broker identity.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.interactivebrokers.com/en/trading/short-securities-availability.php)

### 37. SEC Form 13F holdings — `sec_13f`
- **Family:** institutional_holdings
- **Original observation:** Quarter-end reportable long securities holdings of qualifying managers.
- **Publication / availability:** Due within 45 days after quarter end with holiday adjustment; actual filing acceptance is availability.
- **Units / horizon:** shares; market value / quarters
- **Access / cost:** public_documented_not_tested; EDGAR no key, declared contact/rate limits.
- **Rights:** SEC fair access; public filings; source/issuer rights and CUSIP redistribution conditions separate.
- **Coverage bias:** No complete shorts/cash/derivative hedge book; confidential treatment, manager duplication.
- **Manipulation / distortion:** Low direct; window dressing and amendments.
- **Can infer:** Disclosed long ownership concentration and delayed shifts.
- **Cannot infer:** Current portfolio, net bullishness, new trade date or unhedged conviction.
- **Feature concept:** Ownership concentration, newly disclosed positions, overlap; PIT holdings and amendment handling.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f)

### 38. SEC Form N-PORT public portfolio datasets — `sec_nport`
- **Family:** fund_holdings
- **Original observation:** Publicly disseminated registered-fund holdings and risk exposures.
- **Publication / availability:** Dataset posted quarterly; monthly report period does not imply monthly public availability. Use accession-specific publication; phase-in/rule changes need calendar versioning.
- **Units / horizon:** holdings value; exposures; assets / months to quarters
- **Access / cost:** public_documented_not_tested; Large quarterly ZIPs public; targeted filings preferable for bounded collection.
- **Rights:** Public-data fair access; as-filed disclaimer; no confidential holdings inferred.
- **Coverage bias:** Registered funds only, exclusions; funds have asynchronous fiscal quarters.
- **Manipulation / distortion:** Low direct; filing errors, amendments and aggregation risk.
- **Can infer:** Disclosed crowded holdings and fund exposure.
- **Cannot infer:** Today portfolio or complete monthly public history solely from report labels.
- **Feature concept:** Holdings overlap, exposure concentration, liquidity buckets with publication lag.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Published bulk data begins October 2019; public release restrictions and quarterly bundles.
- **Primary sources:** [source 1](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets), [source 2](https://www.sec.gov/files/nport_readme.pdf)

### 39. Alpaca bars/quotes for explicit-universe breadth — `alpaca_breadth`
- **Family:** market_behavior
- **Original observation:** Observed prices, volume and quotes from selected entitled feed.
- **Publication / availability:** Completed bar close + provider receipt; latest SIP needs entitlement, historical SIP >=15min may be available; IEX is venue subset.
- **Units / horizon:** USD; shares; breadth percent; bps spread / minutes to months
- **Access / cost:** connected_feed_entitlement_dependent; Existing tools available; confirm per-call actual feed; do not label IEX consolidated.
- **Rights:** Alpaca/exchange subscription and derived/redistribution terms.
- **Coverage bias:** Fixed watchlist vs market; survivorship, venue sampling and corporate actions.
- **Manipulation / distortion:** Medium prints/quote noise; high selection error.
- **Can infer:** Participation, dispersion, liquidity and trend behavior.
- **Cannot infer:** Psychological causes, all-market order flow from IEX volume or direction from gross volume.
- **Feature concept:** Advancer fraction; % above MA; cross-sectional dispersion; up/down volume labeled feed and denominator.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://docs.alpaca.markets/us/docs/market-data-faq), [source 2](https://docs.alpaca.markets/us/v1.1/docs/historical-stock-data-1)

### 40. Nasdaq symbol directories — `nasdaq_universe`
- **Family:** reference
- **Original observation:** Current listed symbol universe, security type/test issue, metadata.
- **Publication / availability:** Files update through day; final row creation time; current file is not historical constituent universe.
- **Units / horizon:** security identifiers and flags / daily reference
- **Access / cost:** public_documented_not_tested; Public symbol directories, no login.
- **Rights:** Nasdaq-listed events data page says unrestricted; Fund Network has distinct internal noncommercial terms; do not generalize.
- **Coverage bias:** Current listing survival; security class ambiguity; ETFs/preferreds/test issues.
- **Manipulation / distortion:** Low; identifier changes are major operational risk.
- **Can infer:** Breadth denominator and tradable/reference universe at receipt.
- **Cannot infer:** Historical unbiased universe from today list.
- **Feature concept:** Versioned common-equity cohort, coverage fraction, additions/deletions flags.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs), [source 2](https://nasdaqtrader.com/trader.aspx?id=symbollookup)

### 41. Exchange depth, order flow and auction imbalance — `exchange_depth`
- **Family:** microstructure
- **Original observation:** Entitled book updates, trades, auction imbalance and venue messages.
- **Publication / availability:** Exchange event and sequence clocks, vendor receipt and decision timestamps required; gap detection mandatory.
- **Units / horizon:** shares/contracts; bps; depth; signed flow / milliseconds to hours
- **Access / cost:** licensed_credentials_required; Exchange/vendor subscription, professional/non-display fees and infrastructure; no feed tested.
- **Rights:** Display entitlement is not non-display/algorithmic or redistribution permission; no scraping book viewers.
- **Coverage bias:** Venue fragmentation, hidden liquidity, cancellations and queue priority.
- **Manipulation / distortion:** High spoofing/cancellation/informed-order adverse selection.
- **Can infer:** Observable supply-demand imbalance and liquidity fragility.
- **Cannot infer:** Trader intent, sentiment, full market book or fills at displayed size.
- **Feature concept:** Depth-normalized order imbalance, spread/depth percentile, trade-sign uncertainty and impact.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.cboe.com/data/market-statistics), [source 2](https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf)

### 42. Kalshi public market data — `kalshi`
- **Family:** prediction_expectations
- **Original observation:** Event contracts, market metadata, bid books, trades and outcomes.
- **Publication / availability:** Public REST unauthenticated; quote/trade timestamp vs retrieval separate; WebSocket requires authentication.
- **Units / horizon:** USD per $1 payout; fixed-point quantities / contract-specific
- **Access / cost:** tested_public_readonly; No-key public REST proved; account/trading never used.
- **Rights:** API terms/reuse review before republishing; market access does not authorize trading or geographic circumvention.
- **Coverage bias:** Self-selected capital-weighted traders; contract wording, fees, liquidity and limits.
- **Manipulation / distortion:** High in thin markets; strategic displayed quotes.
- **Can infer:** Price-implied expectations for exact settlement contract after liquidity checks.
- **Cannot infer:** True probability, independent survey, or macro relevance from arbitrary catalog market.
- **Feature concept:** Bid/ask interval, logit repricing, spread/depth, matching-horizon event distribution.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Endpoint/tool:** `https://external-api.kalshi.com/trade-api/v2/markets`
- **Exact probe receipt:** `receipts/kalshi.json`
- **Primary sources:** [source 1](https://docs.kalshi.com/getting_started/quick_start_market_data)

### 43. Polymarket Gamma / CLOB public market data — `polymarket`
- **Family:** prediction_expectations
- **Original observation:** Event metadata through Gamma; executable book/price and history through CLOB.
- **Publication / availability:** Gamma updatedAt not executable-quote clock; CLOB book timestamp/receipt separate; cache age observed in probe.
- **Units / horizon:** USD/stablecoin per $1 payout; shares / contract-specific
- **Access / cost:** tested_gamma_public_clob_not_tested; No-key Gamma read proved; no wallet/account used.
- **Rights:** Terms, geographic rules and reuse rights; read-only research never authorizes trades or geo bypass.
- **Coverage bias:** Crypto venue participants, collateral/counterparty and resolution risks.
- **Manipulation / distortion:** High thin-market/wash-volume/strategic quote risk.
- **Can infer:** Contract-specific price expectations and disagreement with matched contracts.
- **Cannot infer:** Gamma outcomePrices guaranteed executable or unconstrained physical probability.
- **Feature concept:** CLOB bid/ask logit change; cross-venue comparison only identical settlement definitions.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Endpoint/tool:** `https://gamma-api.polymarket.com/markets`
- **Exact probe receipt:** `receipts/polymarket.json`
- **Primary sources:** [source 1](https://docs.polymarket.com/api-reference/predictions/overview), [source 2](https://docs.polymarket.com/api-reference/markets/list-markets)

### 44. CME FedWatch — `cme_fedwatch`
- **Family:** rates_expectations
- **Original observation:** Fed-funds-futures-implied rate outcome probabilities under CME assumptions.
- **Publication / availability:** Public UI/history; EOD API and intraday 60-second update products separate.
- **Units / horizon:** percent model-implied probabilities / FOMC meetings to months
- **Access / cost:** public_ui_paid_api; EOD API advertised $25/month; intraday price separate; no subscription made.
- **Rights:** CME license and attribution; API purchase required for supported machine integration.
- **Coverage bias:** Futures risk premia, meeting/date assumptions, 25bp discretization and EFFR mapping.
- **Manipulation / distortion:** Low direct; microstructure/liquidity effects.
- **Can infer:** Market pricing of policy-rate scenarios under methodology.
- **Cannot infer:** True odds, central-bank intent or independent nonprice sentiment.
- **Feature concept:** Expected target change, entropy, repricing vs prior close; same meeting and contract.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html), [source 2](https://www.cmegroup.com/articles/2023/understanding-the-cme-group-fedwatch-tool-methodology.html)

### 45. US Treasury nominal/real yield curve — `treasury`
- **Family:** macro_prices
- **Original observation:** Daily par nominal and TIPS real yield curves.
- **Publication / availability:** Daily source observation vs posting time separate; XML offers monthly/yearly retrieval; sample timed out.
- **Units / horizon:** percent yield; bps spread / days to years
- **Access / cost:** documented_public_probe_timeout; Public XML no key.
- **Rights:** Government data; Treasury attribution; no guarantee of tradeable yields.
- **Coverage bias:** Interpolated par curves, TIPS liquidity and inflation risk premiums.
- **Manipulation / distortion:** Low direct; model interpolation and market-liquidity effects.
- **Can infer:** Rates term structure and rough inflation compensation.
- **Cannot infer:** Breakeven equals expected inflation or public confidence.
- **Feature concept:** Matched-tenor nominal-real difference, real-rate change, curve slope; model/term premium caveat.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Endpoint/tool:** `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml`
- **Exact probe receipt:** `receipts/treasury.json`
- **Primary sources:** [source 1](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)

### 46. Chicago Fed NFCI / ANFCI — `nfci`
- **Family:** financial_conditions
- **Original observation:** Composite of 105 indicators spanning risk, credit and leverage.
- **Publication / availability:** Weekly Wed 08:30 ET for previous Friday, shifted Thursday after qualifying holiday.
- **Units / horizon:** standardized index / weeks to quarters
- **Access / cost:** public_documented_not_tested; Public downloads.
- **Rights:** Chicago Fed attribution/terms; underlying licensed components do not become freely redistributable.
- **Coverage bias:** Mixed frequency, model-imputed missing inputs; correlated with price features.
- **Manipulation / distortion:** Low direct; high model/revision risk.
- **Can infer:** Broad financial-condition tightness.
- **Cannot infer:** Pure sentiment, all observations contemporaneous, revised history was known then.
- **Feature concept:** As-released level and category contribution; vintage change separated from current innovation.
- **Revisions:** Full history can revise each release with new data/weights; archived vintages mandatory.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.chicagofed.org/research/data/nfci/current-data), [source 2](https://www.chicagofed.org/publications/chicago-fed-insights/2024/nfci-future-economic-growth)

### 47. OFR Financial Stress Index — `ofr_fsi`
- **Family:** financial_conditions
- **Original observation:** Daily stress composite from 33 market variables across credit, valuation, funding, safe assets and volatility.
- **Publication / availability:** Calculated after trading day; publication data current TWO BUSINESS DAYS prior.
- **Units / horizon:** standardized index and contributions / days to months
- **Access / cost:** public_documented_not_tested; Public index downloads; underlying vendor data rights separate.
- **Rights:** OFR terms/attribution; not entitlement to redistribute constituent vendor data.
- **Coverage bias:** Price-based composite, region/indicator selection; high overlap with VIX/spreads.
- **Manipulation / distortion:** Low direct; revisions/model weights.
- **Can infer:** Systemic market stress and category contributions.
- **Cannot infer:** Direct emotion measure or current intraday state from T+2 data.
- **Feature concept:** Lag-aware stress percentile; category breadth; use first-release vintage.
- **Revisions:** Official page records 2026 feed corrections; retain revision history and versions.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://www.financialresearch.gov/financial-stress-index/)

### 48. NY Fed reference rates and operations API — `nyfed_rates`
- **Family:** funding_liquidity
- **Original observation:** SOFR/EFFR and collateral/funding operations published by NY Fed.
- **Publication / availability:** Rate effective date differs from next-day publication; revisions and per-series release rules required.
- **Units / horizon:** percent rates; USD billions; percentiles / days to months
- **Access / cost:** public_api_documented_not_tested; Public JSON/XML/CSV/XLS API; no credential established as necessary.
- **Rights:** Reference-rate disclaimers, conditions and attribution apply; source-specific rights review.
- **Coverage bias:** Covered funding markets and administrator methodology; not all liquidity.
- **Manipulation / distortion:** Low direct; quarter-end funding/technical effects.
- **Can infer:** Funding pressure and distribution of observed transaction rates.
- **Cannot infer:** Investor fear or mechanically bullish effect of liquidity operations.
- **Feature concept:** SOFR-EFFR spread and percentile width; operations relative to seasonal baseline.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://markets.newyorkfed.org/static/docs/markets-api.html)

### 49. FRED / ALFRED — `fred_alfred`
- **Family:** macro_aggregator
- **Original observation:** Agency/vendor series and vintage data through API/MCP.
- **Publication / availability:** Observation date, release/vintage date and receipt distinct; ALFRED supports initial/revised data but dates do not establish intraday time.
- **Units / horizon:** series-specific / days to years
- **Access / cost:** credential_and_archive_scope_review; API key required; MCP account required; no key/account created.
- **Rights:** Current full terms restrict development/training use and separately API/MCP storing/caching/archiving. MCP explicitly supports AI host platforms, so blanket inference prohibition is not established. Clarify intended persistent engine use; source copyrights separate.
- **Coverage bias:** Aggregation lag and source-dependent revisions; alternative direct agency sources preferred where lawful.
- **Manipulation / distortion:** Low direct; high licensing/revision leakage risk.
- **Can infer:** Macro conditions and vintage comparisons within authorized use.
- **Cannot infer:** Free download means unrestricted archive/AI training/redistribution permission.
- **Feature concept:** Only permission-cleared PIT series; no default persistent archive connector.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://fred.stlouisfed.org/legal/terms/), [source 2](https://fred.stlouisfed.org/docs/api/terms_of_use.html), [source 3](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html), [source 4](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)

### 50. Loughran-McDonald financial lexicon — `lm_lexicon`
- **Family:** research_resource
- **Original observation:** Finance-specific positive/negative/uncertainty/constraining categories.
- **Publication / availability:** Dictionary version/year matters; annual additions/removals; March2026 version spans 1993-2025.
- **Units / horizon:** token flags and counts / document research
- **Access / cost:** commercial_license_required; Free academic research; contact authors for commercial license.
- **Rights:** Do not assume generic open-source/commercial permission or raw earnings-call data rights.
- **Coverage bias:** Financial filings/calls vocabulary; negation, context and irony still require model validation.
- **Manipulation / distortion:** Low; lexicon/model drift and context failure.
- **Can infer:** Reproducible finance-language features when licensed.
- **Cannot infer:** Validated tradable alpha or private managerial confidence.
- **Feature concept:** Category tokens/section tokens; version frozen inside training fold; sentence-level evidence audit.
- **Revisions:** Corrections possible; retain immutable retrieved vintages and source version.
- **Historical coverage:** Exact history depth not verified in this pass; inspect licensed/public file or endpoint before backtesting. Current access does not imply complete point-in-time history.
- **Primary sources:** [source 1](https://sraf.nd.edu/loughranmcdonald-master-dictionary/), [source 2](https://sraf.nd.edu/)

## Probe and blocker ledger

The `receipts/` directory contains one bounded request receipt per tested source: URL/tool, attempt/receipt time, status, content type, byte count and body hash where obtained. This public copy retains transport metadata and hashes only; response bodies and prefixes/suffixes are omitted. The recorded hash identifies the original response, not the redacted JSON receipt. Source server HTTP Date is transport metadata, not a market observation timestamp. The included HTTP receipts describe unauthenticated public-endpoint probes. Connector-specific diagnostics are not included.

| Target / action | Result | Completed | Pending / safe next step |
|---|---|---|---|
| Wikimedia two-day article JSON | HTTP 200 | Counts 498 and 578 for Oct27/28; attention only | Configure real production contact, closed-bin watermark and limited topic set |
| Cboe VIX official history CSV | HTTP 200 | CSV receipt/hash | Rights scope and daily as-of parsing; no delayed-quote scraper |
| Fed press RSS | HTTP 200 | RSS receipt/hash | Parser, dedup and release-time checks |
| FRBSF recent CSV | HTTP 200 | Latest row Oct25; receipt/hash | Weekly update calendar, vintage snapshots if permitted |
| Kalshi markets catalog limit=1 | HTTP 200 | Public metadata transport | Returned sports-combination market; no macro-relevance/executable-price claim |
| Polymarket Gamma limit=1 | HTTP 200 | Metadata transport | Returned political event; Gamma cache Date older than receipt; CLOB not tested |
| GDELT DOC inflation sample | HTTP 503 | Exact failed request recorded | Service unavailable; bounded retry/backoff later if authorized; no denial bypass |
| Treasury monthly XML | Timeout | Exact failed request recorded | Availability inconclusive; timeout is not an access denial |
| SEC sample | Not attempted | Official documentation reviewed | Genuine User-Agent contact needed; do not fabricate identity |
| Reddit/X/Stocktwits/YouTube/Trends alpha | Not attempted | Access/terms research | Existing appropriate credentials, approved use and rights would be required; no accounts created |
| FRED persistent ingestion | Policy scope unresolved | Current API/MCP/storage terms reviewed | Obtain exact-use permission/clarification; no blanket inference prohibition asserted |

This research record grants no authorization for purchases, registrations, provider contact, data redistribution or trading. Public endpoint feasibility tests establish only the bounded outcomes recorded above.
