# Source-derived component coverage

This finite coverage table is derived from the pinned source catalogs, surface identifiers, and advertised MCP input schemas. It intentionally omits runtime receipts, per-install URLs, credentials, host dispatch, and response payloads. The machine-readable JSON contains the sanitized input schema, validation boundary, and safe output-class summary for each named tool; no tool is executable from this collection.

Counts: **32 engine IDs**, **31 surface IDs**, **36 MCP tool contracts**; **8** pure browser-local analytical groups extracted.

## Engine IDs

| ID | Coverage | Included artifacts |
|---|---|---|
| `tradier_options_research` | component_source_included | `worker/options-research.js`, `worker/brokers.js` |
| `trade_brain` | component_source_included | `worker/market-readers.js` |
| `stock_quote_snapshot` | component_source_included | `worker/alpaca.js` |
| `integrated_daily_research` | component_source_included | `dist/research-adapters.mjs`, `dist/evidence-contract.mjs` |
| `alpaca_daily` | component_source_included | `worker/alpaca.js`, `dist/research-adapters.mjs` |
| `chartlector_context` | component_source_included | `components/public-feed-parsers.mjs`, `research/chartslector/adapter.mjs` |
| `aperture_on_demand` | component_source_included | `worker/aperture-producer.js`, `research/live-aperture/` |
| `lector_on_demand` | component_source_included | `worker/live-engine-tools.js`, `research/live-lector/` |
| `lector` | component_source_included | `research/live-lector/` |
| `aperture` | component_source_included | `research/live-aperture/` |
| `official_scheduled_events` | component_source_included | `worker/official-events.js` |
| `alpaca_news` | component_source_included | `worker/connected-research.js` |
| `exchange_calendar_inputs` | component_source_included | `worker/exchange-calendar.js` |
| `intraday_provider_inputs` | component_source_included | `worker/intraday-reader.js` |
| `morgue` | host_bound_or_restricted_contract_only | Contract only / withheld |
| `saty` | component_source_included | `deploy/python-research-service/` |
| `raschke_rre` | component_source_included | `deploy/python-research-service/` |
| `forecast_fe01_source_policy` | component_source_included | `worker/forecast-fe01.js`, `research/forecast-features/fe01-trend-v1.mjs` |
| `forecast_fe02_source_policy` | component_source_included | `worker/forecast-fe02.js`, `research/forecast-features/fe02-residual-v1.mjs`, `research/forecast-features/fe02-residual-session-v2.mjs` |
| `forecast_fe03_source_policy` | component_source_included | `worker/forecast-fe03.js`, `research/forecast-features/fe03-breakout-v1.mjs` |
| `forecast_fe04_source_policy` | component_source_included | `worker/forecast-fe04.js`, `research/forecast-features/fe04-gap-decomposition-v1.mjs` |
| `forecast_fe05_source_policy` | component_source_included | `worker/forecast-fe05.js`, `research/forecast-features/fe05-spy-breadth-v1.mjs` |
| `forecast_fe06_source_policy` | component_source_included | `worker/forecast-fe06.js` |
| `forecast_fe07_source_policy` | component_source_included | `worker/forecast-fe07-fe10.js`, `research/forecast-features/fe07-fe10-v1.mjs` |
| `forecast_fe08_source_policy` | component_source_included | `worker/forecast-fe08.js`, `research/forecast-features/fe08-rv-v1.mjs` |
| `forecast_fe09_source_policy` | component_source_included | `worker/forecast-fe09.js`, `research/forecast-features/fe09-jump-tail-v1.mjs` |
| `forecast_fe10_source_policy` | component_source_included | `worker/forecast-fe07-fe10.js`, `research/forecast-features/fe07-fe10-v1.mjs` |
| `forecast_fe12_source_policy` | component_source_included | `worker/forecast-fe12.js`, `research/forecast-features/fe12-top-of-book-v2.mjs`, `research/forecast-features/fe12-top-of-book-v3.mjs` |
| `chartslector_archive_subset` | component_source_included | `research/chartslector/` |
| `forecast_numeric_calculators` | component_source_included | `dist/forecast-engines.mjs`, `dist/forecast-engine-catalog.mjs` |
| `browser_local_labs` | component_source_included | `components/static-gex.mjs`, `components/bullflow-activity.mjs`, `components/finviz-filter.mjs`, `components/stockrover-factors.mjs`, `components/confluence.mjs`, `components/portfolio.mjs`, `components/daily-change-alerts.mjs`, `components/strategy-sma.mjs` |
| `static_research_catalog` | host_bound_or_restricted_contract_only | Contract only / withheld |

## Surface IDs

| ID | Coverage | Included artifacts |
|---|---|---|
| `brain` | component_source_included | `worker/market-readers.js`, `worker/options-research.js` |
| `enginehub` | component_source_included | `dist/forecast-engines.mjs`, `deploy/python-research-service/` |
| `context` | component_source_included | `components/public-feed-parsers.mjs`, `research/chartslector/adapter.mjs` |
| `alpaca` | component_source_included | `worker/alpaca.js`, `dist/research-adapters.mjs` |
| `overview` | component_source_included | `dist/market-overview.mjs`, `dist/research-adapters.mjs` |
| `flow` | component_source_included | `worker/options-research.js` |
| `gex` | component_source_included | `worker/options-research.js` |
| `staticgex` | component_source_included | `components/static-gex.mjs` |
| `azrael` | host_ui_or_operational_contract_only | Contract only / app boundary |
| `optionlab` | component_source_included | `worker/options-research.js` |
| `bullflow` | component_source_included | `components/bullflow-activity.mjs` |
| `finviz` | component_source_included | `components/finviz-filter.mjs` |
| `stockrover` | component_source_included | `components/stockrover-factors.mjs` |
| `darkpool` | host_ui_or_operational_contract_only | Contract only / app boundary |
| `congress` | host_ui_or_operational_contract_only | Contract only / app boundary |
| `insiders` | component_source_included | `research/forecast-features/sec-public-adapters-v1.mjs` |
| `screener` | component_source_included | `worker/market-readers.js` |
| `calendar` | component_source_included | `worker/official-events.js`, `worker/exchange-calendar.js` |
| `news` | component_source_included | `worker/connected-research.js`, `worker/psychology.js` |
| `ticker` | component_source_included | `dist/research-adapters.mjs` |
| `confluence` | component_source_included | `components/confluence.mjs` |
| `portfolio` | component_source_included | `components/portfolio.mjs` |
| `charts` | component_source_included | `research/chartslector/adapter.mjs`, `dist/market-overview.mjs` |
| `watchlists` | host_ui_or_operational_contract_only | Contract only / app boundary |
| `alerts` | component_source_included | `components/daily-change-alerts.mjs` |
| `tools` | component_source_included | `worker/options-research.js` |
| `strategy` | component_source_included | `components/strategy-sma.mjs` |
| `coverage` | host_ui_or_operational_contract_only | Contract only / app boundary |
| `convergence` | component_source_included | `dist/convergence-evidence-csv.mjs` |
| `evidence` | component_source_included | `dist/evidence-contract.mjs` |
| `api` | host_ui_or_operational_contract_only | Contract only / app boundary |

## MCP tool IDs

The JSON file contains the sanitized advertised input schema for each tool, a validation boundary, operation class, and bounded output-contract summary. The host router and formal output schemas are omitted.

| Tool ID | Input schema | Operation | Output boundary |
|---|---|---|---|
| `shipyard_options_expirations` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_options_chain` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_python_status` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_python_run` | Included (sanitized) | write_or_capture_at_host | host output schema omitted |
| `shipyard_python_attempts` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_python_attempt` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_python_job` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_forecast_from_bars` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_forecast_macro_features` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_forecast_from_sources` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_chartslector_scan` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_forecast_catalog` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_forecast_evaluate` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_official_events` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_news_feed` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_psychology_headline_tone` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_psychology_capture` | Included (sanitized) | write_or_capture_at_host | host output schema omitted |
| `shipyard_psychology_history` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_exchange_calendar` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_preopen_status` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_capture_preopen_inputs` | Included (sanitized) | write_or_capture_at_host | host output schema omitted |
| `shipyard_preopen_inputs` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_aperture_scan` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_lector_scan` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_intraday_bars` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_market_context` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_alpaca_daily_bars` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_trade_brain_scan` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_morgue_readiness` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_research_capabilities` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_research_capability_page` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_lector_output` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_aperture_output` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_stock_quote` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_research_catalog` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
| `shipyard_research_snapshot` | Included (sanitized) | read_or_compute_at_host | host output schema omitted |
