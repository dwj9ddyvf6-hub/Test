# Shipyard Research Terminal Worker

This directory is the source for the current read-only Site Worker. `scripts/build_worker.py` embeds the reviewed files in `dist/` and writes `dist/server/index.js`. It packages only the allowlisted browser assets; it does not bundle the legacy `operations.js` or `reports.js` handlers.

## Request surface

| Route | Behavior |
| --- | --- |
| `GET /api/status` | Reports demo/read-only mode and the data routes enabled. It never reads account, position, or order endpoints. |
| `GET /api/terminal/context` | Reads the public `chartslector.json` snapshot plus public Treasury, Federal Reserve, and Cboe observations. It returns the source `as_of` date. The Chartlector JSON is an upstream static GitHub Pages artifact; this Worker does not refresh or generate it. |
| `GET /api/alpaca/bars?symbol=SPY&days=90` | Reads one symbol of split-adjusted daily IEX bars and the current IEX session calendar with server-only credentials. It is not a consolidated SIP feed, quote stream, or account connection. |
| `GET /api/research/morgue/readiness` | Returns the commit-pinned manifest, section presence, and metadata only. It returns no snapshot values; freshness and decision, performance, and order gates remain closed. |
| `POST /mcp` | Exposes three read-only tools: market context, Alpaca daily bars, and Morgue readiness. Production authentication is enforced at the Site boundary. |

The Alpaca route validates symbols, limits requested windows, bounds response size, applies a provider timeout, and caches responses in Worker-isolate memory for 30 seconds. Its 20-per-minute IP counter is also isolate-local and best-effort; it is not a global quota or durable abuse-control boundary. Do not describe it as a strict public rate limit. A stronger shared limit requires a configured platform binding or durable coordinator.

The provider may return a bar dated today before the close-based research features consider that session complete. Each Alpaca bars response also includes the current IEX session from Alpaca's market calendar. The browser excludes today's bar until 15 minutes after that session's core close and excludes a same-day bar when IEX reports no session. Calendar responses are cached for six hours. If the lookup is unavailable, the browser uses the published NYSE schedule through 2028, then a conservative 16:15 ET weekday cutoff; the UI marks this as a calendar fallback.

The Market Overview and Alpaca chart pages request bars every five minutes while visible. Market Context requests a refresh every fifteen minutes while open. These are daily bars, not a streaming quote feed. CSVs and browser research files are not uploaded to Site storage.

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
