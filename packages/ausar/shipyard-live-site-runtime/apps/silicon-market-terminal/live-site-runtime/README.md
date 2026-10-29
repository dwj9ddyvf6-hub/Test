# Shipyard Research Terminal

Owner-only personal research terminal built on the existing Shipyard Site.

See the [2026-10-29 live-data operational audit](./docs/LIVE-DATA-OPERATIONAL-AUDIT-2026-10-29.md) for current feed status, runtime boundaries, verification results, and the remaining live-data work. The [2026-10-28 installation audit](./INSTALLATION-AUDIT-2026-10-28.md) is historical release evidence; its public-access references are superseded.

## Live data

- Trade Brain streams actual Alpaca SIP quotes while entitled and automatically falls back to the real-time IEX exchange feed when SIP access is denied. Server-side credentials never enter the browser. The stream validates its origin and accepts up to five watchlist symbols.
- Trade Brain rechecks real stock quotes (SIP or IEX), completed IEX daily bars, session hours, and Alpaca indicative option snapshots once per minute while open. IEX is a single exchange; SIP is consolidated. Option quotes are modified and last trades are delayed 15 minutes; option prices and risk sizing are reference values, not executable quotes. Stale or missing inputs produce no setup.
- Market Overview and Alpaca chart pages load split-adjusted IEX daily bars. They refresh every five minutes while visible. Market Context refreshes every fifteen minutes while open; Chartlector is an upstream static artifact, not a feed this Worker regenerates.
- The Site has no background market scan. Closing the page stops the quote stream and Trade Brain scans.
- A configured key only confirms that secret values are present. It does not confirm SIP, IEX, or options feed access. The terminal reports each actual feed and never substitutes sample data. Tradier can replace the options provider after the brokerage account is available and its API access is configured.

## Other tools

- The Research Engine Suite displays linked research and metadata-only Morgue readiness. The Worker does not run the Python research engines or expose Morgue snapshot values.
- Watchlists, alert definitions, saved layouts, local uploads, and evidence exports stay in browser storage. Alerts check after browser-side bar refresh; no hosted alert delivery is installed.
- Manual pricing labs use the assumptions entered on their forms. CSV and research templates are local inputs, not live market data, and do not feed Trade Brain.
- Options flow, dark pool, news, disclosures, and broad-market screener feeds remain disconnected and show unavailable or empty states. Yahoo is a link-out only.

## Security and execution boundary

- The production Site is owner-only. Alpaca keys remain in server-side runtime secrets.
- No account balances, holdings, positions, or order routes are accessed. Order placement is disabled.
- `/api/ausar/*`, `/api/terminal/history`, and `/operations.html` are retired and return `410 Gone`.
- The current API exposes dated source fields and rejects invalid, stale, or unavailable data rather than manufacturing a replacement.

## Build

Run `python scripts/build_worker.py` to create `dist/server/index.js` from the reviewed Worker modules and explicit static-asset allowlist. The worker smoke suite uses mocked provider responses only in its isolated test process; those responses are not packaged into the Site.
