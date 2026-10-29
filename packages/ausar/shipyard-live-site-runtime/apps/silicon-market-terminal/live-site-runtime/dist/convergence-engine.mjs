// Generated from the 2026-10-27 active-family ledger and reviewed survivor specifications.
export const SURVIVOR_CATALOG = [
  {
    "id": "S01",
    "name": "Evidence-Gated Market Snapshot",
    "thesis": "Join one market-context capture and one completed daily-bar series into a timestamped, hash-linked research record.",
    "route": [
      "enginehub"
    ],
    "routeLabel": "Research engine suite",
    "source": "Published Chartlector context JSON and Alpaca IEX daily bars; one symbol per run.",
    "path": "Open Research engine suite → Run integrated research snapshot; GET /api/terminal/context and GET /api/alpaca/bars?symbol=SPY&days=90.",
    "mvp": "Existing one-click snapshot; validates bar dates, computes seven features, records inputs/method hashes and exports local evidence JSON.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "The freshness, completed-session selection, indicator math and evidence capture share one run receipt.",
    "ascension": "Turns disconnected scores, scanners and dashboards into a source-aware research transaction.",
    "stripped": "Generative trade calls, proprietary vendor weights and broker-order controls.",
    "ops": "combine + ascend + distill",
    "confidence_score": 98,
    "confidence_rank": 1,
    "confidence_basis": "Engineering confidence 98/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S02",
    "name": "Macro, Breadth & Rotation Context",
    "thesis": "Read macro regime, volatility, breadth and themes with each source's own observation date.",
    "route": [
      "context"
    ],
    "routeLabel": "Market context",
    "source": "Chartlector published JSON plus U.S. Treasury, Federal Reserve H.10 and Cboe index histories.",
    "path": "Market context route → GET /api/terminal/context; visible as-of and received timestamps.",
    "mvp": "Existing bounded public-feed adapter; stale/future/unknown context stays visibly labeled.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Combines cross-asset narrative with breadth/volatility without treating multiple vendor views of one input as independent evidence.",
    "ascension": "A single context plane with explicit source clocks and freshness state.",
    "stripped": "Unpublished regime weights, paid feeds and return claims.",
    "ops": "combine + concentrate + cross-pollinate",
    "confidence_score": 76,
    "confidence_rank": 14,
    "confidence_basis": "Engineering confidence 76/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S03",
    "name": "Daily Price, Trend & Volatility State",
    "thesis": "Compute a transparent completed-bar state from OHLCV instead of opaque indicator bundles.",
    "route": [
      "alpaca",
      "enginehub"
    ],
    "routeLabel": "Alpaca charts / Research engine suite",
    "source": "Alpaca split-adjusted IEX daily bars.",
    "path": "Alpaca charts → select a ticker/history → refresh; the same completed-bar selector feeds Engine Suite.",
    "mvp": "Existing daily-return, SMA20/50, RSI14, ATR14 and trend-state calculations with partial-session exclusion.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Freshness and session completeness travel beside the feature values.",
    "ascension": "Recasts indicator signals as reproducible bar-state features.",
    "stripped": "Invite-only scripts, hidden thresholds and inferred predictive claims.",
    "ops": "distill + concentrate + cross-pollinate",
    "confidence_score": 96,
    "confidence_rank": 2,
    "confidence_basis": "Engineering confidence 96/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S04",
    "name": "Cross-Section Candidate Filter",
    "thesis": "Apply an explicit, inspectable filter contract to a dated user-provided snapshot.",
    "route": [
      "finviz"
    ],
    "routeLabel": "Filter contract lab",
    "source": "User-provided authorized CSV snapshot; no third-party feed is fetched.",
    "path": "Filter contract lab → upload snapshot CSV → apply filter clauses and sort.",
    "mvp": "Existing contract parser supports documented aliases, conjunction semantics and deterministic ordering; missing values remain missing.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "The filter logic is separated from vendor coverage and applied to the user's actual snapshot.",
    "ascension": "One source-neutral query plan can be reused across different approved snapshots.",
    "stripped": "Live proprietary screener feeds and vendor-specific hidden pattern detectors.",
    "ops": "distill + combine",
    "confidence_score": 85,
    "confidence_rank": 9,
    "confidence_basis": "Engineering confidence 85/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S05",
    "name": "Catalyst & Event Timeline",
    "thesis": "Turn dated, user-supplied catalyst and alternative-data observations into a source-clocked chronological research queue.",
    "route": [
      "convergence"
    ],
    "routeLabel": "Convergence engine",
    "source": "User-provided public or licensed event CSV with ObservedAt and optional PublicAt, ReceivedAt and EventType.",
    "path": "Convergence engine → upload an event CSV → review rows ordered by observed time with publication and receipt clocks kept separate.",
    "mvp": "The new local CSV intake preserves event labels and three clocks; the page sorts accepted events chronologically and exports accepted evidence JSON.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Event chronology is kept separate from publication delay and local receipt delay.",
    "ascension": "Moves event feeds from vendor-specific alert boxes into a cross-source research timeline.",
    "stripped": "Automated scraping, private feeds, guessed entity joins and causal claims.",
    "ops": "combine + transplant + ascend",
    "confidence_score": 60,
    "confidence_rank": 20,
    "confidence_basis": "Engineering confidence 60/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S06",
    "name": "Point-in-Time Factor Matrix",
    "thesis": "Rank a dated cross-section using named factors, explicit weights and no silent imputation.",
    "route": [
      "stockrover"
    ],
    "routeLabel": "Factor profile lab",
    "source": "User-provided date-stamped fundamentals CSV.",
    "path": "Factor profile lab → choose CSV → review source date, coverage and factor audit.",
    "mvp": "Existing 22-input candidate uses explicit equal weighting and sector-relative options; incomplete factors remain unavailable.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Every row shows the exact inputs and ranking construction rather than a vendor score alone.",
    "ascension": "Produces an inspectable, cohort-comparable factor table that can flow into the portfolio lab.",
    "stripped": "Vendor weights, DCF claims, forward return claims and inaccessible feed entitlements.",
    "ops": "distill + combine + concentrate",
    "confidence_score": 83,
    "confidence_rank": 10,
    "confidence_basis": "Engineering confidence 83/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S07",
    "name": "Sector Portfolio Builder",
    "thesis": "Construct and compare dated candidate portfolios from user-supplied snapshots with visible exposure and outcome limits.",
    "route": [
      "portfolio"
    ],
    "routeLabel": "Sector portfolio lab",
    "source": "User-provided cross-section/holdings CSV.",
    "path": "Sector portfolio lab → upload the dated CSV → inspect inclusion rules, snapshots and local scorecards.",
    "mvp": "Existing local candidate handles dated input and exports analysis; no brokerage sync or orders.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Portfolio membership is tied to a timestamped input and auditable exclusions.",
    "ascension": "Connects factor ranks to portfolio-level concentration and rebalance review.",
    "stripped": "Broker account state, vendor model portfolios and automatic rebalancing.",
    "ops": "combine + concentrate",
    "confidence_score": 81,
    "confidence_rank": 11,
    "confidence_basis": "Engineering confidence 81/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S08",
    "name": "Expected-Move & Session Map",
    "thesis": "Turn a prior close and a named volatility reference into fixed, interpretable levels.",
    "route": [
      "azrael"
    ],
    "routeLabel": "15.87 Rule map",
    "source": "Completed prior-session close plus published Cboe VIX reference or user-entered value.",
    "path": "15.87 Rule map → enter/confirm prior close and VIX → recalculate level bands.",
    "mvp": "Existing public formula and session map; missing/stale inputs remain flagged.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Volatility levels are explicit inputs with clock and session boundaries, not hidden zones.",
    "ascension": "Unifies expected move and timed risk boundaries in a reviewable session object.",
    "stripped": "Proprietary dealer levels, live option-chain assumptions and guaranteed intraday behavior.",
    "ops": "distill + transplant",
    "confidence_score": 68,
    "confidence_rank": 18,
    "confidence_basis": "Engineering confidence 68/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S09",
    "name": "Options Activity Normalizer",
    "thesis": "Calculate a scoped activity profile from complete, source-labeled user exports.",
    "route": [
      "bullflow"
    ],
    "routeLabel": "Activity profile lab",
    "source": "User-provided licensed options-print CSV.",
    "path": "Activity profile lab → upload print history → set ticker, Eastern as-of date/time → recalculate.",
    "mvp": "Existing parser rejects duplicate IDs, preserves side provenance and suppresses ratios on incomplete sessions.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Observed prints, estimated side and unknown intent remain separate.",
    "ascension": "A provenance-aware intake layer for flow records rather than a vendor-wide tape clone.",
    "stripped": "Live vendor tape, proprietary SigScore and assumed opening/closing intent.",
    "ops": "distill + combine + transplant",
    "confidence_score": 86,
    "confidence_rank": 8,
    "confidence_basis": "Engineering confidence 86/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S10",
    "name": "Static Dealer-Exposure Map",
    "thesis": "Calculate a stated-sign open-interest exposure snapshot with assumptions beside the output.",
    "route": [
      "staticgex"
    ],
    "routeLabel": "Static GEX lab",
    "source": "User-provided option-chain CSV with date, spot, strike, type, open interest, IV and DTE.",
    "path": "Static GEX lab → upload chain CSV → set rate/dividend/multiplier/grid → recalculate.",
    "mvp": "Existing Black–Scholes gamma, call-positive/put-negative convention and zero-cross grid.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Each exposure value can be reconstructed from input rows and stated assumptions.",
    "ascension": "Moves dealer-positioning summaries into a scenario model with inspectable conventions.",
    "stripped": "Observed dealer inventory, proprietary live positioning and predictive direction.",
    "ops": "distill + combine",
    "confidence_score": 88,
    "confidence_rank": 7,
    "confidence_basis": "Engineering confidence 88/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S11",
    "name": "Multi-Leg Payoff & Greeks Lab",
    "thesis": "Evaluate entered option legs across expiry and theoretical price scenarios with model names visible.",
    "route": [
      "optionlab"
    ],
    "routeLabel": "Option strategy lab",
    "source": "User-entered contract legs, spot, IV, rates and exercise style.",
    "path": "Option strategy lab → enter leg rows → select European Black–Scholes or American CRR → calculate.",
    "mvp": "Existing independent payoff/Greek/sensitivity calculator; no chain feed required.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Payoff, model mark and sensitivities are distinct outputs with explicit inputs.",
    "ascension": "Combines builder, optimizer and risk-preview concepts into one transparent local scenario surface.",
    "stripped": "Vendor probability/optimizer rankings and proprietary option-chain data.",
    "ops": "combine + distill + ascend",
    "confidence_score": 91,
    "confidence_rank": 5,
    "confidence_basis": "Engineering confidence 91/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S12",
    "name": "Cost-Aware Strategy Replay",
    "thesis": "Replay one explicit long-or-flat rule against user-provided bars with a date split and turnover costs.",
    "route": [
      "strategy"
    ],
    "routeLabel": "Strategy lab",
    "source": "User-provided OHLCV CSV; optional Alpaca daily bars may be exported by the user.",
    "path": "Strategy lab → upload bars CSV → select fast/slow windows, costs and split → run/export.",
    "mvp": "Existing close-only SMA replay, one-full-bar execution delay, costs on entries/exits and out-of-sample summary.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Historical outcome and data coverage travel together; delayed signals reduce same-bar leakage.",
    "ascension": "Turns signal families into comparable, reproducible study protocols.",
    "stripped": "Vendor backtest engine, live orders and unsupported performance claims.",
    "ops": "combine + distill + transplant",
    "confidence_score": 89,
    "confidence_rank": 6,
    "confidence_basis": "Engineering confidence 89/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S13",
    "name": "Paper-Only Risk & Action Gate",
    "thesis": "Keep research and paper outcomes separate from broker permissions, account state and live orders.",
    "route": [
      "enginehub",
      "evidence"
    ],
    "routeLabel": "Research engine suite / Evidence graph",
    "source": "Evidence bundle fields, source freshness, coverage, PIT availability and user-defined research constraints.",
    "path": "Run a research snapshot → inspect eligibility blockers; API status exposes no account/order endpoints.",
    "mvp": "Existing eligibility is closed when PIT/source rights/freshness are unknown; the Site exposes no order route.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Safety is computed as a first-class output, not a disclaimer below a signal.",
    "ascension": "Applies one explicit gate across signal, replay, flow and portfolio work.",
    "stripped": "Broker automation, account access, order placement and unverified live risk logic.",
    "ops": "combine + ascend",
    "confidence_score": 78,
    "confidence_rank": 13,
    "confidence_basis": "Engineering confidence 78/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S14",
    "name": "Daily-Bar Alert Evaluator",
    "thesis": "Evaluate local price-threshold rules after a completed Alpaca bar refresh.",
    "route": [
      "alerts"
    ],
    "routeLabel": "Alert rules",
    "source": "Alpaca IEX daily bars plus user-defined browser-local rules.",
    "path": "Create a daily-move rule → open Alpaca charts/refresh → review its informational match.",
    "mvp": "Existing browser-local evaluator; no server scheduler, email, push or options feed.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "An alert is tied to the bar refresh and threshold used to evaluate it.",
    "ascension": "Combines watchlist and rule logic without pretending to provide a continuous feed.",
    "stripped": "Push delivery, hosted cron, premium options events and trade execution.",
    "ops": "combine + distill",
    "confidence_score": 74,
    "confidence_rank": 15,
    "confidence_basis": "Engineering confidence 74/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S15",
    "name": "Local Watchlist Workspace",
    "thesis": "Organize symbols and research notes locally without treating demo quote tiles as live market data.",
    "route": [
      "watchlists"
    ],
    "routeLabel": "Watchlists",
    "source": "User-entered tickers and browser-local storage.",
    "path": "Watchlists → add/remove symbols; use Alpaca charts for any price-dependent review.",
    "mvp": "Existing local list persistence; synthetic quote fixtures remain explicitly labeled and are not evidence.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "A low-friction research queue tied to separate validated price reads.",
    "ascension": "Keeps capture/workflow state distinct from source-of-truth market observations.",
    "stripped": "Cloud sync, brokerage positions and synthetic quote inference.",
    "ops": "combine + distill",
    "confidence_score": 72,
    "confidence_rank": 16,
    "confidence_basis": "Engineering confidence 72/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S16",
    "name": "AI & Model Explainability Workbench",
    "thesis": "Expose candidate scoring paths with their actual input semantics and unavailable categories visible.",
    "route": [
      "confluence"
    ],
    "routeLabel": "Confluence lab",
    "source": "Analyst-entered values and versioned public-client metadata/effective-path candidates.",
    "path": "Confluence lab → choose ticker and scoring view → enter values → review coverage and gates.",
    "mvp": "Existing separate 55-field metadata and 17-leaf effective-path candidates; external context remains no-data.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "The explanation states which path is calculated and refuses to invent missing framework inputs.",
    "ascension": "Elevates AI/rating explanations into deterministic, inspectable candidate models.",
    "stripped": "Authenticated production weights, model confidence and prediction/performance claims.",
    "ops": "distill + cross-pollinate",
    "confidence_score": 70,
    "confidence_rank": 17,
    "confidence_basis": "Engineering confidence 70/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S17",
    "name": "Read-Only Market Data Gateway",
    "thesis": "Expose bounded market-context and daily-bar reads through simple HTTP and read-only MCP contracts.",
    "route": [
      "api"
    ],
    "routeLabel": "Data source settings",
    "source": "Alpaca IEX bars and the existing public macro-context adapter.",
    "path": "Read GET /api/alpaca/bars and GET /api/terminal/context or invoke the declared read-only MCP tools.",
    "mvp": "Existing Worker endpoints with bounded provider bodies, validation, secret redaction and no account/order methods.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "A small, explicit adapter contract feeds the UI without coupling each engine to provider SDKs.",
    "ascension": "Provides one controlled read boundary for browser workflows and agents.",
    "stripped": "Yahoo scraping, broker account APIs and order endpoints.",
    "ops": "combine + distill",
    "confidence_score": 95,
    "confidence_rank": 3,
    "confidence_basis": "Engineering confidence 95/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S18",
    "name": "Vendor Capability & Identity Registry",
    "thesis": "Resolve each target's observable product family, lane, evidence status and exact report path.",
    "route": [
      "coverage"
    ],
    "routeLabel": "Vendor coverage",
    "source": "Silicon's generated 86-family ledger and active REA report links.",
    "path": "Vendor coverage → filter by name/lane/status → open target evidence.",
    "mvp": "Existing searchable 86-row source registry; pass counts remain distinct from unique families.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "Identity ambiguity and bounded review remain explicit data rather than being collapsed into a vendor count.",
    "ascension": "Makes the research corpus navigable and traceable from the product.",
    "stripped": "Assumed 92-name reconciliation and full-replica claims.",
    "ops": "distill + transplant",
    "confidence_score": 80,
    "confidence_rank": 12,
    "confidence_basis": "Engineering confidence 80/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S19",
    "name": "Normalized Evidence Envelope",
    "thesis": "Validate and export source-neutral market observations without changing their original values or clocks.",
    "route": [
      "convergence"
    ],
    "routeLabel": "Convergence engine",
    "source": "A local CSV with ObservedAt, Entity, Source, Metric and Value; optional clocks and method fields stay explicit.",
    "path": "Convergence engine → upload CSV → inspect accepted/rejected rows and download accepted records as JSON.",
    "mvp": "The new parser validates required columns, timestamps, row limits and optional source URLs; raw input stays in tab memory.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "A single evidence contract lets otherwise incompatible datasets coexist without pretending their metrics mean the same thing.",
    "ascension": "Turns vendor-specific data boxes into reusable, typed, source-labeled evidence records.",
    "stripped": "Automatic semantic mapping, imputation, private data and inferred provenance.",
    "ops": "combine + distill + ascend",
    "confidence_score": 62,
    "confidence_rank": 19,
    "confidence_basis": "Engineering confidence 62/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  },
  {
    "id": "S20",
    "name": "Evidence, Provenance & Eligibility Graph",
    "thesis": "Trace observations through source clocks, normalized facts, versioned features and decision-use gates.",
    "route": [
      "evidence"
    ],
    "routeLabel": "Evidence graph",
    "source": "Research registry, snapshot hashes, data availability and freshness metadata.",
    "path": "Evidence graph → inspect four clocks, vendor dependencies and eligibility blockers.",
    "mvp": "Existing graph reports provenance, unresolved PIT access and decision eligibility; eligible count stays zero when gates are unknown.",
    "status": "OPERATIONAL WITH SCOPE",
    "novelty": "The graph records dependency overlap so correlated vendor displays do not become duplicate confirmation.",
    "ascension": "Elevates source lineage and eligibility above individual indicator dashboards.",
    "stripped": "Unsupported point-in-time claims, source-right assumptions and alpha claims.",
    "ops": "combine + ascend + distill",
    "confidence_score": 92,
    "confidence_rank": 4,
    "confidence_basis": "Engineering confidence 92/100 based on visible local implementation, runnable path, source contract and testability; not an estimate of trading performance."
  }
];
export const FAMILY_CROSSWALK = [
  {
    "slug": "ainvest",
    "name": "AInvest — AIME, Magic Signal, and Option Pilot",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/ainvest.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md",
    "kernel": "AIME/AIME+ is presented as an AI research terminal/assistant with chat, research agents, market desk, screening, portfolio analytics, alerts and AI-generated commentary. Its terms describe informational market data, simulations, portfolio analytics and…",
    "survivor_id": "S01",
    "survivor_name": "Evidence-Gated Market Snapshot",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "alertsify",
    "name": "Alertsify",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/alertsify.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/alertsify.md",
    "kernel": "A second same-brand-looking surface, alertsify.app, currently describes a very similar copy-trading and broker-integration product and has a ©2026 Alertsify, Inc. footer. The alertsify.com Terms identify Alertsify LLC in §1, while their footer also says…",
    "survivor_id": "S14",
    "survivor_name": "Daily-Bar Alert Evaluator",
    "operations": "combine + distill"
  },
  {
    "slug": "algoalpha",
    "name": "AlgoAlpha",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/algoalpha.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/algoalpha.md",
    "kernel": "AlgoAlpha has three visible product families: TradingView indicators and screeners; algorithmic crypto signals delivered through Discord; and Echo automation that executes supported signals on connected exchanges. Its current homepage lists Indicators from…",
    "survivor_id": "S14",
    "survivor_name": "Daily-Bar Alert Evaluator",
    "operations": "combine + distill"
  },
  {
    "slug": "algobars",
    "name": "AlgoBars",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/algobars.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/algobars.md",
    "kernel": "AlgoBars is a multi-surface retail trading terminal and a broker/prop-firm white-label platform. The retail product combines charting, indicators, watchlists, alerts, AI market scan/analysis, strategy construction, backtesting, replay, paper trading,…",
    "survivor_id": "S01",
    "survivor_name": "Evidence-Gated Market Snapshot",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "algopoint-qalpha",
    "name": "AlgoPoint / Qalpha",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/algopoint-qalpha.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/algopoint-qalpha.md",
    "kernel": "The page names Hidden Markov regimes, VWMA/VWAP Z-score anomalies, Holt-Winters velocity, linear regression, and Center of Gravity among “11+” models. The Heatmap is described as fusing Holt-Winters, LR and CoG into colored market-regime bars, with…",
    "survivor_id": "S20",
    "survivor_name": "Evidence, Provenance & Eligibility Graph",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "altindex",
    "name": "AltIndex",
    "lane": "equity",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/altindex.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/altindex.md",
    "kernel": "AltIndex combines alternative-data research, daily 0–100 AI Scores, ranked stock lists, stock alerts, a screener, AI chat, portfolio insights, public results, and an API/MCP product. Its public score page describes the score as a mid-term (six months or…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "apex-quant-ai",
    "name": "Apex Quant AI",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/apex-quant-ai.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/apex-quant-ai.md",
    "kernel": "The listing describes an automated XAUUSD-only EA for MetaTrader 5, recommended on an H1 chart, with ECN/RAW spread conditions and a VPS recommended for continuous operation. The user installs the product, configures the EA inputs, and enables MetaTrader…",
    "survivor_id": "S13",
    "survivor_name": "Paper-Only Risk & Action Gate",
    "operations": "combine + ascend"
  },
  {
    "slug": "arkham-intelligence",
    "name": "Arkham Intelligence",
    "lane": "onchain",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/arkham-intelligence.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/arkham-intelligence.md",
    "kernel": "Search and profile pages for addresses, entities, tokens and pools. Portfolio/balance, historical performance, transaction, counterparties, volume, flow and borrowing/loan views. Dashboards for portfolios, exchange flows, whale activity and sector trends;…",
    "survivor_id": "S15",
    "survivor_name": "Local Watchlist Workspace",
    "operations": "combine + distill"
  },
  {
    "slug": "azrael-options",
    "name": "The 15.87 Rule (Azraël Options)",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/azrael-options.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/azrael-options.md",
    "kernel": "Azraël Options offers a free weekday premarket brief and The Vault, a paid morning desk. The current public page describes at most one live idea per day for SPX or XSP, with the level map posted at 8:30, the written plan at 8:35, a possible entry between…",
    "survivor_id": "S02",
    "survivor_name": "Macro, Breadth & Rotation Context",
    "operations": "combine + concentrate + cross-pollinate"
  },
  {
    "slug": "blackboxstocks",
    "name": "BlackBoxStocks",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/blackboxstocks.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/blackboxstocks.md",
    "kernel": "BlackBoxStocks combines stock and options scanners, algorithm-based alerts, options flow, dark-pool prints/profile, proprietary chart studies, news, watchlists, education, team trading rooms, community chat, and a mobile app. The product separates stock…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "bullflow",
    "name": "Bullflow",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/bullflow.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/bullflow.md",
    "kernel": "| Plan | Publicly stated price | Main published scope | |---|---|---| | Basic | $39 month to month in the FAQ; $33 per month billed annually ($396/year) | Real-time options flow, Gamma/Net GEX levels, mobile and desktop alerts, AI trade alerts, historical…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "bybit-apk-grid-dca",
    "name": "Bybit APK (Grid / DCA / AI Strategy)",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/bybit-apk-grid-dca.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/bybit-apk-grid-dca.md",
    "kernel": "The FAQ says up to 50 Spot Grid and DCA bots can run simultaneously. A bot can modify its per-coin amount, investment frequency, and optional maximum investment; its selected coins and Flexible Savings setting cannot be changed after creation. Flexible…",
    "survivor_id": "S13",
    "survivor_name": "Paper-Only Risk & Action Gate",
    "operations": "combine + ascend"
  },
  {
    "slug": "capitalise-ai",
    "name": "Capitalise.ai",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/capitalise-ai.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/capitalise-ai.md",
    "kernel": "The public glossary describes a constrained trading-language model rather than unrestricted natural-language control. Conditions may reference price, time, percentage changes, supported technical indicators, positions and strategy events. IF/WHEN frame…",
    "survivor_id": "S12",
    "survivor_name": "Cost-Aware Strategy Replay",
    "operations": "combine + distill + transplant"
  },
  {
    "slug": "chaikin-power-gauge",
    "name": "Chaikin Power Gauge",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/chaikin-power-gauge.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/chaikin-power-gauge.md",
    "kernel": "The member platform separates a main publication/workspace from an Analytics workspace. Common elements across subscriptions are a newsletter and portfolio, Power Gauge rating/report and basic chart. The public feature matrix differentiates a basic Power…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "chartprime",
    "name": "ChartPrime",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/chartprime.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/chartprime.md",
    "kernel": "ChartPrime is a TradingView-first indicator suite with companion community, education, screener, and promoted automated-trading products. The public page groups the core indicators into Market Dynamics (structure, liquidity, and reaction zones), Market…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "cheddar-flow",
    "name": "Cheddar Flow",
    "lane": "options",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/cheddar-flow.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/cheddar-flow.md",
    "kernel": "Ask/above ask is treated as aggressive buying; bid/below bid as aggressive selling; mid-market is separately identified. A sweep is fragmented execution routed across multiple exchanges; a split is fragmented execution on a single exchange. A block is…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "citrini-citrindex",
    "name": "Citrini Research / The Citrindex",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/citrini-citrindex.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/citrini-citrindex.md",
    "kernel": "Citrini Research is a thematic-equity and global-macro research publisher. Its public “About” page describes a top-down workflow that starts with macroeconomics and cross-asset themes, identifies long-lived narratives/megatrends, then constructs baskets of…",
    "survivor_id": "S02",
    "survivor_name": "Macro, Breadth & Rotation Context",
    "operations": "combine + concentrate + cross-pollinate"
  },
  {
    "slug": "coincodecap-signals",
    "name": "CoinCodeCap Signals",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/coincodecap-signals.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/coincodecap-signals.md",
    "kernel": "CoinCodeCap Signals is a founder-led Telegram subscription that sells discretionary trade setups rather than a market-data terminal. The published scope spans crypto spot and futures plus NFT, gold and forex channels. The paid signal payload is designed…",
    "survivor_id": "S05",
    "survivor_name": "Catalyst & Event Timeline",
    "operations": "combine + transplant + ascend"
  },
  {
    "slug": "composer",
    "name": "Composer by SoFi",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/composer.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/composer.md",
    "kernel": "Composer is a US brokerage and no-code automated-investing platform. Its rule-based strategy objects are called Symphonies. Users create or remix a Symphony as a visual rule graph, backtest it, save/share it, allocate capital to it, and let the service…",
    "survivor_id": "S12",
    "survivor_name": "Cost-Aware Strategy Replay",
    "operations": "combine + distill + transplant"
  },
  {
    "slug": "correction-scope-ai-v1",
    "name": "CorrectionScope AI v1",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/correction-scope-ai-v1.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/correction-scope-ai-v1.md",
    "kernel": "This is an indicator, not an Expert Advisor that sends orders. The Pine version draws on the price chart and defines TradingView alert conditions. The MQL5 version plots a probability line in a separate indicator window and creates chart objects. Neither…",
    "survivor_id": "S17",
    "survivor_name": "Read-Only Market Data Gateway",
    "operations": "combine + distill"
  },
  {
    "slug": "danelfin",
    "name": "Danelfin",
    "lane": "equity",
    "status": "complete",
    "passes": 3,
    "report_path": "research/rea_teardowns/targets/danelfin.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/danelfin.md",
    "kernel": "Danelfin covers US-listed stocks, US-listed ETFs, and stocks on major European exchanges. The documented user flow is to choose a market and asset class; discover candidates through rankings, search, screeners, sectors, industries, themes, Trade Ideas, or…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "deepseek-news-grid-scalper-v2",
    "name": "DeepSeek News Grid Scalper V2",
    "lane": "automation",
    "status": "bounded-complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/deepseek-news-grid-scalper-v2.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/deepseek-news-grid-scalper-v2.md",
    "kernel": "The earlier Midna report's strategy summary broadly matches this tagged source, but several claims need correction or narrower wording: the source URL is now pinned to the canonical repository and tag; the default DeepSeek placeholder attempts a connection…",
    "survivor_id": "S08",
    "survivor_name": "Expected-Move & Session Map",
    "operations": "distill + transplant"
  },
  {
    "slug": "edgeful",
    "name": "Edgeful",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/edgeful.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/edgeful.md",
    "kernel": "Edgeful is a historical probability-research platform for futures, stocks, ETFs, forex and crypto. The product combines 150+ reports, a What’s In Play (WIP) dashboard, screener, Edgeful AI, TradingView/NinjaTrader indicator libraries, community, a REST…",
    "survivor_id": "S02",
    "survivor_name": "Macro, Breadth & Rotation Context",
    "operations": "combine + concentrate + cross-pollinate"
  },
  {
    "slug": "eztrades-manipulationx",
    "name": "EzTrades to EzAlgo / ManipulationX",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/eztrades-manipulationx.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/eztrades-manipulationx.md",
    "kernel": "Use the morning NQ futures scenarios to establish levels and a directional plan. On a TradingView chart, ManipulationX scans for inverse fair-value gaps after liquidity sweeps. The indicator rates reversal or continuation setups and filters them with…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "finviz-screener",
    "name": "Finviz Screener",
    "lane": "equity",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/finviz-screener.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/finviz-screener.md",
    "kernel": "In October 2026, Finviz split the former combined screener into separate Stock Screener and ETF Screener products. The vendor says existing saved presets were migrated by type: stock presets to the stock tool, fund presets to ETF, mixed presets duplicated…",
    "survivor_id": "S04",
    "survivor_name": "Cross-Section Candidate Filter",
    "operations": "distill + combine"
  },
  {
    "slug": "flashalpha",
    "name": "FlashAlpha",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/flashalpha.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/flashalpha.md",
    "kernel": "The methodology states that the service computes BSM Greeks from market snapshots, fits per-expiry implied-volatility surfaces, then aggregates sensitivities into dollarized exposure and derived levels. The published GEX convention is gamma × OI × 100 ×…",
    "survivor_id": "S19",
    "survivor_name": "Normalized Evidence Envelope",
    "operations": "combine + distill + ascend"
  },
  {
    "slug": "flowalgo",
    "name": "FlowAlgo",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/flowalgo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/flowalgo.md",
    "kernel": "FlowAlgo markets a browser-based market-wide alert feed for equity-option activity and large equity prints. Its public taxonomy includes intermarket sweep orders, option blocks, equity blocks/dark-pool prints, on-demand history, institutional price levels,…",
    "survivor_id": "S14",
    "survivor_name": "Daily-Bar Alert Evaluator",
    "operations": "combine + distill"
  },
  {
    "slug": "foliotend-tensor",
    "name": "FolioTend / Tensor",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/foliotend-tensor.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/foliotend-tensor.md",
    "kernel": "| Surface | Publicly established | What remains unavailable | |---|---|---| | FolioTend web app | The creator directs users to foliotend.com. The app is described as a place to search tickers, maintain a watchlist, use a dashboard, and open Tensor charts.…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "gainzalgo",
    "name": "GainzAlgo",
    "lane": "charting",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/gainzalgo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/gainzalgo.md",
    "kernel": "| Product | Public choices and features | Displayed price on capture | |---|---|---:| | GainzAlgo | Standard or Pro; BUY/SELL signals, all-market/all-timeframe positioning, TradingView and community Discord access | $49.95 lifetime, crossed-out $66.95 | |…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "gammaedge",
    "name": "GammaEdge",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/gammaedge.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/gammaedge.md",
    "kernel": "The public app page shows Net GEX by strike and expiration, strike-level tables with net delta, net GEX and call/put/open interest, and visual summaries of Delta, Gamma, Charm and Vanna. It claims real-time spot and options-structure data, flexible…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "gexradar",
    "name": "GEXRadar",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/gexradar.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/gexradar.md",
    "kernel": "GEXRadar sells a dealer-positioning dashboard around options GEX, unusual flow and historical replay. Public feature claims include 3,500+ tickers, 2-second live refresh, 12 years of historical data beginning in 2013, a full Greeks suite, OI-based GEX,…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "guardian-ftmo-swing-free",
    "name": "Guardian FTMO Swing Free",
    "lane": "automation",
    "status": "bounded-complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/guardian-ftmo-swing-free.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/guardian-ftmo-swing-free.md",
    "kernel": "The exact target is realbacktesting Guardian FTMO Swing Free, cTrader Store product 4616, listed as a free cBot. The current listing shows version 4.1 (October 2026), 29 sales, 2.39K free installs, 30.48M traded volume, 12.32K pips won, no reviews, and…",
    "survivor_id": "S08",
    "survivor_name": "Expected-Move & Session Map",
    "operations": "distill + transplant"
  },
  {
    "slug": "insiderfinance",
    "name": "InsiderFinance",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/insiderfinance.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/insiderfinance.md",
    "kernel": "The home page presents a free options-flow stream with its 15 newest records delayed by 30 minutes; paid dashboard plans advertise real-time flow. The 2025 sample newsletter shows a broad flow-event schema: timestamp, ticker, expiration, call/put, spot,…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "intellectia-ai",
    "name": "Intellectia AI",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/intellectia-ai.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/intellectia-ai.md",
    "kernel": "Intellectia is a market-research assistant spanning stocks, ETFs, Hong Kong equities, major forex pairs and crypto. The public site lists stock review, technical analysis, price scenarios, options strategy, AI Stock Picker, SwingMax, day-trading signals,…",
    "survivor_id": "S16",
    "survivor_name": "AI & Model Explainability Workbench",
    "operations": "distill + cross-pollinate"
  },
  {
    "slug": "kavout",
    "name": "Kavout",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/kavout.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/kavout.md",
    "kernel": "Separately, Kavout operates SignalDB, a developer/data-feed catalog for factor signals and K Score. SignalDB describes 12 datasets: nine factor signals plus three K Score variants. Its subscription and API entitlement are separate from Kavout Pro; a Pro…",
    "survivor_id": "S16",
    "survivor_name": "AI & Model Explainability Workbench",
    "operations": "distill + cross-pollinate"
  },
  {
    "slug": "kobeissi-letter",
    "name": "The Kobeissi Letter",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/kobeissi-letter.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/kobeissi-letter.md",
    "kernel": "The Kobeissi Letter is a subscription research publication, not a brokerage or trade-execution platform. Its weekly Sunday letter presents fundamental and technical views on the S&P 500, WTI crude oil, natural gas, gold, Treasury/bonds and options, with…",
    "survivor_id": "S02",
    "survivor_name": "Macro, Breadth & Rotation Context",
    "operations": "combine + concentrate + cross-pollinate"
  },
  {
    "slug": "kucoin-app-4.43.0",
    "name": "KuCoin Android App 4.43.0",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/kucoin-app-4.43.0.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/kucoin-app-4.43.0.md",
    "kernel": "The official spot guide describes opening Trade, searching a pair, selecting an order type, and submitting buy/sell orders. The Trading Bot FAQ says bots run in the cloud without the app staying open, supports up to 60 bots per account, and cannot…",
    "survivor_id": "S13",
    "survivor_name": "Paper-Only Risk & Action Gate",
    "operations": "combine + ascend"
  },
  {
    "slug": "leadr-labs-original",
    "name": "Leadr (Leadr Labs)",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/leadr-labs-original.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/leadr-labs-original.md",
    "kernel": "Leadr is a U.S.-equity research and trade-planning SPA, not a broker or automated execution service. Its current public description stages the workflow as (1) eligibility/qualification, (2) eight-category confluence, (3) an observable price trigger, and…",
    "survivor_id": "S17",
    "survivor_name": "Read-Only Market Data Gateway",
    "operations": "combine + distill"
  },
  {
    "slug": "levelfields",
    "name": "LevelFields AI",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/levelfields.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/levelfields.md",
    "kernel": "Level 1 is described as do-it-yourself access to scenarios, data, trends and customizable alerts. Level 2 adds analyst-selected trade ideas or AI alerts flagged by staff, trade positioning, longer history, more customized alerts, one-to-one training and…",
    "survivor_id": "S05",
    "survivor_name": "Catalyst & Event Timeline",
    "operations": "combine + transplant + ascend"
  },
  {
    "slug": "luxalgo",
    "name": "LuxAlgo",
    "lane": "charting",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/luxalgo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/luxalgo.md",
    "kernel": "Unknown: Proprietary S&O/PAC/Oscillator formulas and model weights; exact provider contracts and data normalization; CME and venue licensing details; production feed latency; all current plan/feature enforcement internals; Quant model/provider, prompts and…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "m-algo-eurusd-m1-core",
    "name": "M-Algo EURUSD M1 Core",
    "lane": "automation",
    "status": "bounded-complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/m-algo-eurusd-m1-core.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/m-algo-eurusd-m1-core.md",
    "kernel": "The optional account protection measures the decline in account equity from the highest point since the cBot started; zero disables it. At the selected threshold, the cBot attempts to close all positions on the account, including manual trades and other…",
    "survivor_id": "S08",
    "survivor_name": "Expected-Move & Session Map",
    "operations": "distill + transplant"
  },
  {
    "slug": "market-chameleon",
    "name": "Market Chameleon",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/market-chameleon.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/market-chameleon.md",
    "kernel": "Market Chameleon is a browser-based research and analytics site built around stock/options screeners, volatility analysis, earnings/dividend data, event studies, trade reports, downloadable datasets, and portfolio/watchlist tools. Its overview groups the…",
    "survivor_id": "S04",
    "survivor_name": "Cross-Section Candidate Filter",
    "operations": "distill + combine"
  },
  {
    "slug": "market-cipher",
    "name": "Market Cipher",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/market-cipher.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/market-cipher.md",
    "kernel": "Market Cipher is a subscription bundle of four protected TradingView indicators plus a risk calculator and Discord access. The public setup flow is: create a TradingView account; register at Market Cipher and save the TradingView username; purchase a plan;…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "menthorq",
    "name": "MenthorQ",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/menthorq.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/menthorq.md",
    "kernel": "MenthorQ packages quantitative market levels, options positioning and volatility models, a dashboard/screener, education/community, and integrations that plot its outputs inside third-party charting/trading tools. The public plans describe a free…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "nansen",
    "name": "Nansen",
    "lane": "onchain",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/nansen.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/nansen.md",
    "kernel": "Nansen is a multi-chain on-chain analytics and intelligence product. Its core distinction is the labeling layer: it joins blockchain activity to addresses, named entities and cohorts such as Smart Money, whales, exchanges and fresh wallets. Product…",
    "survivor_id": "S15",
    "survivor_name": "Local Watchlist Workspace",
    "operations": "combine + distill"
  },
  {
    "slug": "option-alpha",
    "name": "Option Alpha",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/option-alpha.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/option-alpha.md",
    "kernel": "Option Alpha is a cloud-based options research, paper-trading and brokerage automation platform. Its basic object is a bot: a capital/allocation and position-limit container populated with reusable automations. An automation is an ordered decision/action…",
    "survivor_id": "S12",
    "survivor_name": "Cost-Aware Strategy Replay",
    "operations": "combine + distill + transplant"
  },
  {
    "slug": "optionality-sinux",
    "name": "Optionality / Sinux Signals",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/optionality-sinux.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/optionality-sinux.md",
    "kernel": "| Desk | Publicly described workflow | |---|---| | Options | 0DTE-to-weekly contract calls with exact strike/expiry, entry ranges, trims/exits and defined-risk strategies | | Day trading | Pre-market levels/bias, opening-range and momentum calls,…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "options-cartel",
    "name": "The Options Cartel — Custom Flow Bot (audit only)",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/options-cartel.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/options-cartel.md",
    "kernel": "The paid “Full Access” listing advertises real-time entry/exit alerts for swing and options strategies, daily live trading sessions, access to Sean's active positions, strategy training and market education. Its Whop listing shows $125/month plus three…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "options-trading-toolbox",
    "name": "Options Trading Toolbox (OTT)",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/options-trading-toolbox.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/options-trading-toolbox.md",
    "kernel": "The product combines discovery (underlying/options/strategy screens and trade ideas), position evaluation (P&L visualizer, GEX, max pain, put/call ratio), institutional activity views (dark-pool/blocks/unusual volume and insider activity), and historical…",
    "survivor_id": "S11",
    "survivor_name": "Multi-Leg Payoff & Greeks Lab",
    "operations": "combine + distill + ascend"
  },
  {
    "slug": "optionscout",
    "name": "OptionScout",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/optionscout.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/optionscout.md",
    "kernel": "The GEX calculation is public: per contract, OI × gamma × 100 × spot² × 1%; calls count positive and puts negative. Values sum by strike and then across the chain. Call/put walls are the largest positive/most negative net-GEX strikes. Gamma flip is the…",
    "survivor_id": "S11",
    "survivor_name": "Multi-Leg Payoff & Greeks Lab",
    "operations": "combine + distill + ascend"
  },
  {
    "slug": "optionstrat",
    "name": "OptionStrat",
    "lane": "options",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/optionstrat.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/optionstrat.md",
    "kernel": "Sentiment: bullish, bearish, very bullish, very bearish, neutral, or directional. “Very” is described relative to the implied move; directional means a large move either way; neutral means expected to remain near the current price. Trade shape: single,…",
    "survivor_id": "S11",
    "survivor_name": "Multi-Leg Payoff & Greeks Lab",
    "operations": "combine + distill + ascend"
  },
  {
    "slug": "profit-builders",
    "name": "Profit Builders",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/profit-builders.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/profit-builders.md",
    "kernel": "The .io product combines a live flow table, contract-level context and flow labels with a separate GEX view. The scanner supports custom presets, direction/flow type/signal-quality/side filters, a “curated” toggle, ask/bid/mid execution context, total…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "prospero-ai",
    "name": "Prospero.ai",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/prospero-ai.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/prospero-ai.md",
    "kernel": "Prospero’s core public description is a free mobile investing-intelligence app rather than a broker. Its support page says users search a ticker/company for 10 proprietary predictions—five short-term and five long-term—then browse four pick lists…",
    "survivor_id": "S16",
    "survivor_name": "AI & Model Explainability Workbench",
    "operations": "distill + cross-pollinate"
  },
  {
    "slug": "quant-data",
    "name": "Quant Data",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/quant-data.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quant-data.md",
    "kernel": "Options flow: The website and API docs distinguish consolidated blocks, splits, and sweeps from unconsolidated individual option prints. Consolidated rows expose contract, premium, size/volume/open interest, prices, Greeks, trade-side code, sentiment,…",
    "survivor_id": "S19",
    "survivor_name": "Normalized Evidence Envelope",
    "operations": "combine + distill + ascend"
  },
  {
    "slug": "quantcharts",
    "name": "QuantCharts",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/quantcharts.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quantcharts.md",
    "kernel": "The strongest exact-name match is quantcharts.com, which presently redirects to Vela by LuxAlgo at vela.luxalgo.com/chart. Its rendered public workspace has a watchlist, charting, trading journal summaries and Quant assistant panels. The Silicon report for…",
    "survivor_id": "S20",
    "survivor_name": "Evidence, Provenance & Eligibility Graph",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "quantix",
    "name": "QuantiX Finance",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/quantix.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quantix.md",
    "kernel": "The public “How QuantiX IQ Works” article describes chat sessions as threads. Each message starts a run; stage cards stream agent decisions and metrics; past runs reload; users can stop work at a safe checkpoint. A relevance check routes non-strategy chat…",
    "survivor_id": "S12",
    "survivor_name": "Cost-Aware Strategy Replay",
    "operations": "combine + distill + transplant"
  },
  {
    "slug": "quantum-algo",
    "name": "Quantum Algo (Zeno)",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/quantum-algo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quantum-algo.md",
    "kernel": "Zeno is presented as four detection products: Institutional Gravity Zone (general markets, tuned to 2H), Zeno Gold (XAU/USD, 15m), Zeno Stocks (Nasdaq/S&P/large U.S. stocks and ETFs, 1H+), and Zeno Oscillator (momentum confirmation across…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "saty-ecosystem",
    "name": "Saty Ecosystem (Satyland)",
    "lane": "charting",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/saty-ecosystem.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/saty-ecosystem.md",
    "kernel": "| Component | First-party distribution and constraints | TradingView listing snapshot (2026-10-26) | |---|---|---| | ATR Levels | Satyland links Thinkorswim and TradingView. The Thinkorswim page includes a scan study and two sample scans; Scalp mode is…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "scalpflip-ea-v1.9",
    "name": "SCALPFLIP EA v1.9",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/scalpflip-ea-v1.9.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/scalpflip-ea-v1.9.md",
    "kernel": "Reversal mode trades against the preceding candle: bullish close buys, bearish close sells. Trend mode follows that candle. Smart mode computes direction points from trend and RSI. The MA trend or RSI extreme contributes two points; high tick volume adds…",
    "survivor_id": "S08",
    "survivor_name": "Expected-Move & Session Map",
    "operations": "distill + transplant"
  },
  {
    "slug": "schwar-capital",
    "name": "Schwar Capital Research",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/schwar-capital.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/schwar-capital.md",
    "kernel": "Schwar Capital Research is an author-led investing newsletter and equity-research publication hosted on Substack, rather than a standalone trading terminal. Its public menu exposes Home, Notes, Idea Archive, Portfolio, SCRai Index, Philosophy, Disclaimer…",
    "survivor_id": "S02",
    "survivor_name": "Macro, Breadth & Rotation Context",
    "operations": "combine + concentrate + cross-pollinate"
  },
  {
    "slug": "simply-wall-st",
    "name": "Simply Wall St",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/simply-wall-st.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/simply-wall-st.md",
    "kernel": "The primary research flow is ticker/search or screener → company report and Snowflake → inspect the underlying valuation, future/past performance, health and dividend analyses → compare, save, or track. Portfolio functions accept holdings or transactions…",
    "survivor_id": "S07",
    "survivor_name": "Sector Portfolio Builder",
    "operations": "combine + concentrate"
  },
  {
    "slug": "skylit",
    "name": "Skylit (Heatseeker)",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/skylit.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/skylit.md",
    "kernel": "Heatseeker uses strikes as rows and expirations as columns, with a starred “King” node plus Gatekeeper/Pika/Barney and other classifications. Its controls include GEX or VEX, live node velocity, multi-index Trinity boards, alert-on-approach/tap, node-size…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "spotgamma",
    "name": "SpotGamma",
    "lane": "options",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/spotgamma.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/spotgamma.md",
    "kernel": "Founder’s Note and key levels: pre-market and follow-up commentary, expected ranges, and levels for major indices. The editorial workflow adds a human interpretation layer to the model outputs. Equity Hub: per-symbol options positioning, gamma profile,…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "squeezemetrics",
    "name": "SqueezeMetrics (sqzme)",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/squeezemetrics.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/squeezemetrics.md",
    "kernel": "sqzme is a market-structure research and data product from SqueezeMetrics. The public S&P 500 DIX/GEX chart is a different series from the ticker-level chart's similarly named measurements. Its core subscription combines ticker history, chart/research…",
    "survivor_id": "S10",
    "survivor_name": "Static Dealer-Exposure Map",
    "operations": "distill + combine"
  },
  {
    "slug": "stock-moe",
    "name": "Stock Moe Earner / Earner Plus",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/stock-moe.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/stock-moe.md",
    "kernel": "Earner Plus adds access to Moe's invite-only TradingView “Bread Recipe” indicator, an extra Wednesday livestream, and an exclusive Discord support channel. The vendor describes Bread Recipe as a backtested reversal tool for potential entries/exits and…",
    "survivor_id": "S05",
    "survivor_name": "Catalyst & Event Timeline",
    "operations": "combine + transplant + ascend"
  },
  {
    "slug": "stock-rover",
    "name": "Stock Rover",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/stock-rover.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/stock-rover.md",
    "kernel": "The main discovery loop is: select or adapt a built-in screen, filter a North American equity/ETF universe with financial, operating and price metrics, optionally weight criteria, rank results, then save/export or score a watchlist/portfolio against that…",
    "survivor_id": "S07",
    "survivor_name": "Sector Portfolio Builder",
    "operations": "combine + concentrate"
  },
  {
    "slug": "summit-iq",
    "name": "Summit IQ",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/summit-iq.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/summit-iq.md",
    "kernel": "Summit IQ presents itself as application-only crypto trading infrastructure for high-capital operators. The six advertised modules are an AI signal engine, whale-wallet tracker, meme-coin opportunity scanner, execution dashboard, caller-reputation scoring,…",
    "survivor_id": "S15",
    "survivor_name": "Local Watchlist Workspace",
    "operations": "combine + distill"
  },
  {
    "slug": "tapeboard",
    "name": "Tapeboard",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tapeboard.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tapeboard.md",
    "kernel": "Tapeboard is documented as a keyboard-centered, dark market terminal for retail users. It groups surfaces under Markets (dashboard, scanner, charts, heatmap), Trade (simulator, journal), Research (ticker research, options, filings, insider data, news),…",
    "survivor_id": "S18",
    "survivor_name": "Vendor Capability & Identity Registry",
    "operations": "distill + transplant"
  },
  {
    "slug": "ticker-nerd",
    "name": "Ticker Nerd",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/ticker-nerd.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ticker-nerd.md",
    "kernel": "Free Ticker Nerd Rank: daily 0–100 comparative scores for about 4,600 US-listed stocks, with individual factor scores and public stock pages. The score describes a stock’s relative evidence; the product explicitly says it is not a buy/sell timing signal or…",
    "survivor_id": "S04",
    "survivor_name": "Cross-Section Candidate Filter",
    "operations": "distill + combine"
  },
  {
    "slug": "tickeron",
    "name": "Tickeron",
    "lane": "events",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/tickeron.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tickeron.md",
    "kernel": "AI Robots/Agents for stocks, ETFs, crypto and other markets, with signal-only, virtual/paper and brokerage-agent variants. AI Real Time Patterns (RTP) for intraday pattern/entry/exit ideas. AI Pattern Search Engine for end-of-day historical pattern search,…",
    "survivor_id": "S04",
    "survivor_name": "Cross-Section Candidate Filter",
    "operations": "distill + combine"
  },
  {
    "slug": "tipranks",
    "name": "TipRanks",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tipranks.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tipranks.md",
    "kernel": "The Smart Score is a 1–10 cross-sectional stock rating with 1–3 Underperform, 4–7 Neutral, and 8–10 Outperform. The public glossary identifies eight factors: analyst ratings, insider transactions, blogger opinions, individual-investor sentiment, hedge-fund…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "tjr-indicators",
    "name": "TJR Trades Indicators",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tjr-indicators.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tjr-indicators.md",
    "kernel": "The indicators are chart overlays for TradingView that automate parts of a price-action workflow: structure breaks, fair-value gaps and inversions, order blocks/breaker blocks, liquidity, SMT comparisons, session/market levels, higher-timeframe bias, and…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "trade-echo",
    "name": "Trade Echo (OptionFlow)",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/trade-echo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/trade-echo.md",
    "kernel": "Trade Echo is now a broad market-intelligence and trading workspace; OptionFlow is its options-tape module, not a separate company identified by the index. The current public product groups include options flow and Discovery, DealerEdge GEX/VEX, dark-pool…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "trade-ideas",
    "name": "Trade Ideas / Holly AI",
    "lane": "events",
    "status": "complete",
    "passes": 3,
    "report_path": "research/rea_teardowns/targets/trade-ideas.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/trade-ideas.md",
    "kernel": "The legacy OddsMaker guide says entry events come from configured alerts, with user-selected direction, move threshold, entry windows, exit time, profit target, stop, trailing stop, and market/location. The older guide describes fixed, short historical…",
    "survivor_id": "S04",
    "survivor_name": "Cross-Section Candidate Filter",
    "operations": "distill + combine"
  },
  {
    "slug": "tradealgo",
    "name": "TradeAlgo / TradeGPT",
    "lane": "events",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tradealgo.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tradealgo.md",
    "kernel": "Terminal is advertised at $2,995 for a 12-month subscription with no monthly option. No add-ons or additional tiers are described on that page. It includes all listed data modules, dxFeed data, mobile access, Telegram alerts and both daily live analyst…",
    "survivor_id": "S05",
    "survivor_name": "Catalyst & Event Timeline",
    "operations": "combine + transplant + ascend"
  },
  {
    "slug": "tradingkit",
    "name": "TradingKit",
    "lane": "automation",
    "status": "bounded-complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tradingkit.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tradingkit.md",
    "kernel": "“TradingKit” is not a unique public product identity. The SaaS privacy and support pages name StrategyFactory.ai as provider; the TradingKit.net About page describes its MT4/MT5 software and education hub and links to product-specific MQL5 listings. The…",
    "survivor_id": "S20",
    "survivor_name": "Evidence, Provenance & Eligibility Graph",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "tradingview-desktop",
    "name": "TradingView Desktop 3.4.1 + web bundle",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tradingview-desktop.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tradingview-desktop.md",
    "kernel": "The privileged top-level BrowserWindow loads the local app/window/index.html shell. Its options enable Node integration and disable context isolation and sandboxing. Network tabs are BrowserViews. For non-local content the options disable Node integration…",
    "survivor_id": "S18",
    "survivor_name": "Vendor Capability & Identity Registry",
    "operations": "distill + transplant"
  },
  {
    "slug": "tradytics",
    "name": "Tradytics",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/tradytics.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/tradytics.md",
    "kernel": "The US Apple App Store listing shows in-app purchases of $49.99 monthly and $449.99 yearly, while the website advertises $69/month. This is an unresolved platform/offer discrepancy; neither listing proves the final checkout price. The site says mobile apps…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "trendspider",
    "name": "TrendSpider",
    "lane": "charting",
    "status": "complete",
    "passes": 2,
    "report_path": "research/rea_teardowns/targets/trendspider.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/trendspider.md",
    "kernel": "Open a symbol chart and apply automated analysis/indicators or build conditions in the shared visual scripting editor. Configure a strategy with a single test timeframe, chart source/type, extended-hours setting, direction, costs, and a selected historical…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "unusual-whales-original",
    "name": "Unusual Whales",
    "lane": "options",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/unusual-whales-original.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/unusual-whales-original.md",
    "kernel": "Unusual Whales is a multi-product options and market-data platform. The current homepage navigation exposes Dashboard, Options Flow, Tickers, Market, Periscope GEX, Charting, Predictions, Workspace, Tools and Data Access/API. The public pitch spans options…",
    "survivor_id": "S09",
    "survivor_name": "Options Activity Normalizer",
    "operations": "distill + combine + transplant"
  },
  {
    "slug": "vectorvest",
    "name": "VectorVest",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/vectorvest.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/vectorvest.md",
    "kernel": "VectorVest is a stock-ranking, market-timing and portfolio-workflow system, now spread across VectorVest 7, Market Launchpad, Stock Advisory mobile app, and add-ons including RealTime Derby, Options Launchpad, RoboTrader and ProfitLocker Pro. The current…",
    "survivor_id": "S07",
    "survivor_name": "Sector Portfolio Builder",
    "operations": "combine + concentrate"
  },
  {
    "slug": "vip-indicators",
    "name": "VIP Indicators",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/vip-indicators.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/vip-indicators.md",
    "kernel": "Public pages describe a bundle of TradingView indicators for FX, stocks, crypto, indices/commodities and multiple timeframes. The named indicators are VIP Market Scanner (direction, entries/stops/targets), Cloud Band Signals (buy/sell signals), Market…",
    "survivor_id": "S20",
    "survivor_name": "Evidence, Provenance & Eligibility Graph",
    "operations": "combine + ascend + distill"
  },
  {
    "slug": "wundertrading",
    "name": "WunderTrading",
    "lane": "automation",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/wundertrading.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/wundertrading.md",
    "kernel": "WunderTrading is a cloud crypto-trading automation and multi-exchange account-management platform. Public product categories include Signal/TradingView automation, DCA, grid, multi-pair grid, market-neutral, paper/demo trading, a manual trading terminal,…",
    "survivor_id": "S13",
    "survivor_name": "Paper-Only Risk & Action Gate",
    "operations": "combine + ascend"
  },
  {
    "slug": "zeiierman",
    "name": "Zeiierman Trading",
    "lane": "charting",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/zeiierman.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/zeiierman.md",
    "kernel": "Zeiierman markets an 80+ tool TradingView ecosystem: proprietary indicators, strategies, two automated strategy bots, toolkits, a Discord community, tutorials/mentorship, and signal services. The public catalog names groups for buy/sell, top/bottom,…",
    "survivor_id": "S03",
    "survivor_name": "Daily Price, Trend & Volatility State",
    "operations": "distill + concentrate + cross-pollinate"
  },
  {
    "slug": "zen-ratings",
    "name": "Zen Ratings (WallStreetZen)",
    "lane": "equity",
    "status": "complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/zen-ratings.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/zen-ratings.md",
    "kernel": "The public Zen Ratings page says an overall rating and seven component grades are available on quote pages for more than 4,600 stocks. The grades are intended as a first-pass ranking, after which users can inspect the components. Premium adds the full…",
    "survivor_id": "S06",
    "survivor_name": "Point-in-Time Factor Matrix",
    "operations": "distill + combine + concentrate"
  },
  {
    "slug": "zerith-macd-martingale-grid-v2.20",
    "name": "Zerith MACD Martingale Grid v2.20",
    "lane": "automation",
    "status": "bounded-complete",
    "passes": 1,
    "report_path": "research/rea_teardowns/targets/zerith-macd-martingale-grid-v2.20.md",
    "report_url": "https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/zerith-macd-martingale-grid-v2.20.md",
    "kernel": "There is no stop loss or take profit attached to individual positions: both are passed as zero when opening trades. Default exits use basket management: trailing starts at 10 account-currency units and follows the peak by a 3-unit callback; disabling the…",
    "survivor_id": "S08",
    "survivor_name": "Expected-Move & Session Map",
    "operations": "distill + transplant"
  }
];

export const MAX_EVIDENCE_CSV_BYTES = 10 * 1024 * 1024;
export const MAX_EVIDENCE_CSV_ROWS = 50000;
const REQUIRED = ["ObservedAt", "Entity", "Source", "Metric", "Value"];
const OPTIONAL = ["PublicAt", "ReceivedAt", "Unit", "Method", "Confidence", "EventType", "SourceURL"];
const FIELDS = [...REQUIRED, ...OPTIONAL];
const normalizeHeader = (value) => String(value ?? "").replace(/^\uFEFF/, "").trim().toLowerCase().replace(/[\s_-]+/g, "");
const HEADER_LOOKUP = new Map(FIELDS.map((field) => [normalizeHeader(field), field]));

function parseRows(input) {
  const text = String(input ?? "");
  if (new TextEncoder().encode(text).byteLength > MAX_EVIDENCE_CSV_BYTES) throw new RangeError("CSV exceeds the 10 MiB local import limit.");
  const rows = [];
  let row = [], field = "", quoted = false, afterQuote = false, line = 1, rowLine = 1;
  const pushField = () => { row.push(field); field = ""; afterQuote = false; };
  const pushRow = () => { pushField(); rows.push({ line: rowLine, values: row }); row = []; rowLine = line + 1; if (rows.length > MAX_EVIDENCE_CSV_ROWS + 1) throw new RangeError("CSV exceeds the 50,000-row local import limit."); };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') { quoted = false; afterQuote = true; }
      else { field += ch; if (ch === "\n") line += 1; else if (ch === "\r" && text[i + 1] !== "\n") line += 1; }
      continue;
    }
    if (afterQuote) {
      if (ch === ",") { pushField(); continue; }
      if (ch === "\r" || ch === "\n") { if (ch === "\r" && text[i + 1] === "\n") i += 1; line += 1; pushRow(); rowLine = line; continue; }
      if (ch === " " || ch === "\t") continue;
      throw new SyntaxError(`Unexpected character after a quoted field on line ${line}.`);
    }
    if (ch === '"') { if (field.length) throw new SyntaxError(`Quote inside an unquoted field on line ${line}.`); quoted = true; continue; }
    if (ch === ",") { pushField(); continue; }
    if (ch === "\r" || ch === "\n") { if (ch === "\r" && text[i + 1] === "\n") i += 1; line += 1; pushRow(); rowLine = line; continue; }
    field += ch;
  }
  if (quoted) throw new SyntaxError("CSV ends inside a quoted field.");
  if (field.length || row.length || afterQuote) pushRow();
  return rows;
}

export function parseEvidenceCsv(input) {
  const parsed = parseRows(input);
  if (!parsed.length) throw new Error("CSV is empty.");
  const headerCells = parsed[0].values.map((x) => String(x).replace(/^\uFEFF/, "").trim());
  const headers = headerCells.map((x) => HEADER_LOOKUP.get(normalizeHeader(x)) || null);
  if (headers.some((x) => x === null)) throw new Error("CSV has an unrecognized column. Use the documented template headers.");
  if (new Set(headers).size !== headers.length) throw new Error("CSV contains duplicate column names.");
  const absent = REQUIRED.filter((field) => !headers.includes(field));
  if (absent.length) throw new Error(`CSV is missing required columns: ${absent.join(", ")}.`);
  const index = new Map(headers.map((field, i) => [field, i]));
  const records = [], rejected = [];
  for (const parsedRow of parsed.slice(1)) {
    const values = parsedRow.values;
    if (values.every((value) => String(value ?? "").trim() === "")) continue;
    const record = { rowNumber: parsedRow.line };
    for (const field of headers) record[field] = String(values[index.get(field)] ?? "");
    let reason = "";
    for (const required of REQUIRED) if (!record[required].trim()) { reason = `${required} is required`; break; }
    if (!reason && !Number.isFinite(Date.parse(record.ObservedAt))) reason = "ObservedAt must be a parseable date or timestamp";
    for (const clock of ["PublicAt", "ReceivedAt"]) if (!reason && record[clock]?.trim() && !Number.isFinite(Date.parse(record[clock]))) reason = `${clock} must be a parseable date or timestamp when supplied`;
    if (!reason && record.SourceURL?.trim()) { try { const url = new URL(record.SourceURL.trim()); if (!["https:", "http:"].includes(url.protocol)) reason = "SourceURL must use HTTP or HTTPS"; } catch { reason = "SourceURL must be a valid HTTP or HTTPS URL"; } }
    const oversized = FIELDS.find((field) => (record[field] ?? "").length > 8192);
    if (!reason && oversized) reason = `${oversized} exceeds the 8,192-character field limit`;
    if (values.length > headers.length && values.slice(headers.length).some((value) => String(value).trim())) reason ||= "Row contains extra values beyond the header columns";
    if (reason) rejected.push({ rowNumber: parsedRow.line, reason }); else records.push(record);
  }
  return { headers, records, rejected, acceptedCount: records.length, rejectedCount: rejected.length, totalRows: records.length + rejected.length };
}

