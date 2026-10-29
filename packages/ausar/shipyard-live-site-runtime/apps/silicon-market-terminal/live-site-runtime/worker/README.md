# Shipyard Research Terminal Worker

This directory is the source for the current read-only Site Worker. `scripts/build_worker.py` embeds the reviewed files in `dist/` and writes `dist/server/index.js`. It packages only the allowlisted browser assets; it does not bundle the legacy `operations.js` or `reports.js` handlers.

## Request surface

| Route | Behavior |
| --- | --- |
| `GET /api/status` | Reports whether server-only Alpaca market-data credentials are configured and the read routes enabled. Configuration is not proof of feed entitlement. It never reads account, position, or order endpoints. |
| `GET /api/terminal/context` | Reads the public `chartslector.json` snapshot plus public Treasury, Federal Reserve, and Cboe observations. It returns the source `as_of` date. The Chartlector JSON is an upstream static GitHub Pages artifact; this Worker does not refresh or generate it. |
| `GET /api/alpaca/bars?symbol=SPY&days=90` | Reads one symbol of split-adjusted daily IEX bars and the current IEX session calendar with server-only credentials. It is not a consolidated SIP feed, quote stream, or account connection. |
| `GET /api/alpaca/brain/scan?symbol=SPY` | Read-only setup scan. Requires a verified open session, a fresh SIP quote or IEX fallback, completed IEX daily history, active standard option metadata, Alpaca indicative quotes no more than 90 seconds old, current-enough open interest, and Alpaca-calculated Black-Scholes Greeks. Returns long stock for aligned bullish conditions and a clearly labeled indicative call/put candidate when its contract passes every gate. Option quotes are modified and trades are delayed 15 minutes; option prices are not executable quotes. No order is submitted. |
| `GET /api/alpaca/stream` with a WebSocket upgrade | Opens a server-authenticated Alpaca SIP stream and falls back to live IEX only when SIP access is denied. It accepts one to five validated browser-watchlist symbols. Only validated quotes and normalized connection status are forwarded; API credentials are never sent to the browser. The connection runs only while the browser is connected. |
| `GET /api/research/morgue/readiness` | Returns the commit-pinned manifest, section presence, and metadata only. It returns no snapshot values; freshness and decision, performance, and order gates remain closed. |
| `POST /mcp` | Exposes four read-only tools: market context, Alpaca daily bars, Trade Brain scan, and Morgue readiness. Production authentication is enforced at the Site boundary. |

The Alpaca route validates symbols, limits requested windows, bounds response size, applies a provider timeout, and caches responses in Worker-isolate memory for 30 seconds. Its 20-per-minute IP counter is also isolate-local and best-effort; it is not a global quota or durable abuse-control boundary. Do not describe it as a strict public rate limit. A stronger shared limit requires a configured platform binding or durable coordinator.

The provider may return a bar dated today before the close-based research features consider that session complete. Each Alpaca bars response also includes the current IEX session from Alpaca's market calendar. The browser excludes today's bar until 15 minutes after that session's core close and excludes a same-day bar when IEX reports no session. Calendar responses are cached for six hours. If the lookup is unavailable, the browser uses the published NYSE schedule through 2028, then a conservative 16:15 ET weekday cutoff; the UI marks this as a calendar fallback.

The Market Overview and Alpaca chart pages request bars every five minutes while visible. Market Context requests a refresh every fifteen minutes while open. Trade Brain streams SIP stock quotes, falling back to IEX when SIP access is denied, and separately scans up to five watchlist symbols sequentially once per minute. Each scan requests SIP quotes, with an IEX fallback on HTTP 403, plus an Alpaca indicative option snapshot; options are not streamed. IEX is one exchange, while SIP is consolidated across U.S. exchanges. The Site has no background scheduler, so the quote stream and scans stop when the page is closed. CSVs and browser research files are not uploaded to Site storage.

Trade Brain uses only live provider responses and calculations from those responses. It never reads local CSV studies or the retired flow, GEX, dark-pool, screener, news, or disclosure fixtures. A failed IEX request, stale quote, or unverified session calendar blocks a stock idea. An unavailable indicative feed, incomplete option pagination, an option quote older than 90 seconds, adjusted contracts, or missing contract metadata blocks an option candidate; the delayed trade timestamp is provenance only and is not a freshness gate. Alpaca calculates the displayed option Greeks and implied volatility with a Black-Scholes model; these are derived analytics. Modified indicative prices and risk sizing are references, not executable quotes. A risk cap entered by the user stays in browser storage and is used only to calculate a maximum whole-share or whole-contract quantity. Broker account, position, and order routes are not called.

The live scan is rules-based. It is not a trained language model, account-aware portfolio manager, or proven trading strategy. It suggests long common stock only for the bullish trend gate and long calls or puts only when the corresponding fresh indicative contract passes every stated filter. Option candidates require a current broker quote before any order decision. It does not short stock, write options, submit orders, or run after the browser page closes.

## Retired and uninstalled surfaces

`/api/ausar/*`, `/api/terminal/history`, and `/operations.html` return `410 Gone`. Other unsupported paths return `404`. The current Worker does not read the preserved D1/R2 tables; those bindings and historical tables are retained for compatibility and are not part of the live terminal request path. Do not restore the old paper-desk publisher or expose database rows through the public UI.

Saved watchlists and alert definitions remain in browser storage. Alerts are checked after a browser-side bar refresh; there is no hosted alert scheduler, push-delivery worker, or Cron Trigger in this Site. The Python research packages linked from the UI are source-linked and are not executed by this JavaScript Worker.

Yahoo Finance remains a link-out. This Worker does not scrape it or automate collection from it.

## Build and local route smoke

Run from this directory:

```powershell
python scripts/build_worker.py
node scripts/worker-smoke.mjs
```

The smoke check uses the built Worker with fake provider responses and no external requests. It covers the static entry point and icon alias, all 28 registered views, read-only status, invalid/unconfigured Alpaca states, normalized IEX bars, isolate caching, a 1 MiB streaming response bound, malformed/provider-error handling and secret redaction, metadata-only Morgue readiness, the three read-only MCP tools, and retired-route boundaries.
