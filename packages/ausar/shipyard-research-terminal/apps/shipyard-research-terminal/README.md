# Shipyard Research Terminal

Public, read-only research workspace built on the existing Shipyard Sites project.

See the [2026-10-28 installation audit](./INSTALLATION-AUDIT-2026-10-28.md) for the verified live release, included browser modules, runtime boundaries, and remaining integration gaps.

## Included UI

- Market context and Chartlector macro views.
- Alpaca IEX daily bars, charting, and locally calculated SMA20/SMA50, RSI14, and ATR14. The overview and chart lab refresh every five minutes while open.
- A Research Engine Suite control room that refreshes Chartlector context and one Alpaca symbol together, reports bar-derived indicators, and routes into the browser-ready tools.
- A browser-memory evidence adapter for the integrated Alpaca snapshot. It validates canonical bar observations, hashes the normalized capture and versioned indicator methods, records feature lineage and eligibility blockers, and offers a local JSON download. It does not upload or persist the bundle on the Site.
- A read-only Morgue snapshot intake at `/api/research/morgue/readiness` and in the engine control room. It embeds a metadata-only manifest pinned to a source commit and SHA-256, then reports timestamp and section presence only; it returns no snapshot values and keeps freshness, source-rights, point-in-time, decision, performance, and order gates closed. Refreshing this manifest requires a source update and Site release. The endpoint is also available as the read-only `shipyard_morgue_readiness` Site MCP tool.
- Close-based Alpaca charts, returns, indicators, alert checks, and evidence features exclude a daily bar dated today in New York until 16:15 ET. This conservative rule does not model exchange holidays or early closes; the unfiltered provider bar stays visible and is labeled in the source table.
- Chartlector freshness is shown in the engine hub. Context older than three calendar days is labeled stale rather than ready.
- Research tools from the Silicon Market Terminal source: vendor coverage/evidence index, chart workspace, confluence and GEX candidates, screeners, options-payoff and activity labs, strategy replay, local CSV workflows, watchlists, and browser-local alerts.
- Source and run-guide links for the Saty, Raschke, Morgue, and ChartsLector Python research packages. They are not executed by this JavaScript Worker; the page states that runtime boundary rather than showing false connected status.
- Sample-only views remain labeled synthetic. Local uploads, saved layouts, watchlists, and alert rules stay in the visitor's browser.

## Refresh and storage

- Overview and Alpaca chart pages poll daily bars every five minutes while visible. Market context polls every fifteen minutes while its page is open.
- A daily bar dated today is shown as partial and excluded from close metrics until 16:15 New York time on weekdays.
- CSVs, watchlists, alerts, layouts, and evidence exports stay in the browser. The Site does not upload visitor files to server storage.

## Public-site data boundary

- `GET /api/alpaca/bars` reads one symbol of split-adjusted daily bars from Alpaca's IEX feed. It uses the server-only runtime secrets `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY`.
- `GET /api/terminal/context` reads the existing public Chartlector feed with Treasury, Federal Reserve, and Cboe context.
- `POST /mcp` exposes read-only market-context and daily-bars tools.
- No Alpaca account, order, balance, or holding data is requested or returned. There is no order-submission path.
- The integrated snapshot uses only public context and daily bars. It reports descriptive measurements and does not generate calibrated probabilities or trade instructions.
- Alpaca feature lineage is explicitly blocked from decision eligibility while entitlement and historical point-in-time availability remain unverified. Chartlector is included only as a source pointer in the evidence export; its values are not copied into that bundle.
- Yahoo Finance is linked out to; the Site does not scrape or automate collection from Yahoo.
- Old desk snapshots, portfolio history, reports, and operations APIs are retired. Static deployment assets are allowlisted; old snapshot JSON and generated Worker files are not served as browser assets.

## Corpus status shown in the UI

The current REA scoreboard (2026-10-28) records 100 requested passes: 95 complete, 5 bounded-review complete, 0 in progress, and 0 queued across 86 report families. The historical 92-name roster is not present in the active index, so that denominator remains unreconciled. The legacy teardown index separately lists OpenMarket, VolSignals, and TheStrat as three post-index additions outside the active scope; they are not counted or assumed to fill the missing roster. The suite has shared prototypes and eight partial candidates; it does not claim full vendor replicas or trading alpha.

The UI links to the dated [scoreboard](https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/SCOREBOARD.md), [denominator reconciliation](https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/synthesis/SCOPE-AND-DENOMINATOR-RECONCILIATION-2026-10-27.md), and [86-family registry](https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/apps/silicon-market-terminal/vendor-coverage.json).

## Build

Run `python3 scripts/build_worker.py`. The build emits `dist/server/index.js`, embeds only reviewed public assets, and does not require a bundler.
