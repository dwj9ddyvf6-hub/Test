# Shipyard live-data operational audit

**Checked:** 2026-10-29 UTC
**Production Site:** Shipyard Research Terminal, owner-only; current version 454, source commit `e25d1ecf0864561afefd40a05f55fb2331aeb1bd`, deployed successfully at `2026-10-29T03:51:19Z`.
**Current production publication:** version 452, source commit `4ad9bf71d174db1134e138e15c70a47f119ea192`; deployment succeeded at `2026-10-29T03:06:37Z`.
**Latest market-data endpoint observation:** version 450 at `2026-10-29T02:26:32Z`; this is the last captured provider-data response, not a new version-452 quote observation.
**Result:** live IEX stock data remains connected; option scans now use Alpaca indicative snapshots with clear estimate labeling. Open-session option quote delivery is not yet verified. Background scanning is not installed.

## What production proved

- The owner browser showed **“SIP access not enabled”** before the fallback. That is a real provider entitlement result, not a credential-presence inference.
- After version 450 deployed, a fresh owner-page load showed **“IEX connected · waiting for quotes.”** The Worker had authenticated to Alpaca's `v2/iex` stream and received a quote-subscription acknowledgment. The regular market was closed, so no current quote message was expected or observed.
- Version 452 is the active production deployment. A fresh owner-page load confirmed the content-addressed app and imported modules; this fixes stale browser-cache reuse. The latest check was after hours, so it did not produce an in-session quote.
- At `2026-10-29T02:26:32Z`, `GET /api/alpaca/bars?symbol=SPY&days=20` returned 14 split-adjusted Alpaca IEX daily bars; the latest completed bar was dated Oct. 28 with a `$772.28` close. That is a real exchange observation, not consolidated SIP.
- The production Trade Brain returned `market_closed` after hours, with zero setups. It correctly does not fabricate a setup or use stale quote snapshots. Its closed-session response skips stock quote and option-feed requests, so this check does not prove OPRA access.
- The Site is custom owner-only: the owner is the sole allowed viewer, with no groups or external visitors. `/api/status` reports credentials present and read-only routes; it does not prove provider entitlements. Account, position, balance, and order access remain off.

## Live-data path now installed

| Path | Source and cadence | Production limit |
| --- | --- | --- |
| Stock quote stream | Alpaca SIP when entitled; on SIP authorization/entitlement denial, the Worker authenticates to Alpaca IEX and forwards validated quotes. Up to five watchlist symbols; runs while Trade Brain is visible. | IEX is one exchange. The current production proof confirms IEX authentication and subscription, but not an in-session quote timestamp. |
| Trade Brain stock scan | SIP latest quote, with IEX REST fallback on HTTP 403; completed IEX daily bars; Alpaca IEX session calendar; rules-based trend, RSI, and ATR calculations. Runs once per minute while visible for up to five symbols. | Quotes must be fresh (90 seconds); stale data, wide spreads, bad session evidence, or insufficient history yield no stock setup. The scan creates no order. |
| Option scan | Alpaca option-contract metadata plus `feed=indicative` snapshots, open interest, Greeks, liquidity, and quote timestamp checks. | Quote freshness is limited to 90 seconds. Quotes are modified and trades are delayed 15 minutes; the UI labels values as estimates and requires a current broker quote before an order decision. Open-session quote delivery remains unverified. |
| Charts and market overview | Split-adjusted Alpaca IEX completed daily bars, refreshed every five minutes while visible. | Single-exchange history, not consolidated volume or quotes. |
| Market context | Published Chartlector artifact; U.S. Treasury, Federal Reserve, and Cboe observations with source dates. Context refreshes while open. | Chartlector was dated Oct. 22 and visibly stale on Oct. 29. Cboe/Treasury observations were dated Oct. 28; the Fed broad-dollar observation was dated Oct. 23. This Worker does not generate or refresh Chartlector. |
| Yahoo | Link-out only. | No Yahoo API, scraping, or automated data ingestion is configured. |

No sample quote or demo trade is used by Trade Brain. The Worker serves an explicit asset allowlist and does not import the isolated fixture scripts. Deterministic smoke tests use mocked provider responses; those responses are not production market data. Manual strategy labs accept user-entered assumptions or local CSVs and do not feed Trade Brain.

## Internet research and implementation decisions

Alpaca documents Basic as live IEX equities with indicative options, while Algo Trader Plus provides all-exchange equities and OPRA options. Alpaca's stock stream uses `v2/iex` or `v2/sip`, and a feed outside an account's entitlement is rejected during authentication. The latest stock-quote endpoint also accepts an explicit `feed=iex` selection. This supports the new fallback while preserving the actual source label. See [Alpaca Market Data plans](https://docs.alpaca.markets/us/docs/about-market-data-api), [real-time stock stream](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data), [latest quote reference](https://docs.alpaca.markets/us/reference/stocklatestquotesingle-1), and [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).

Version 453 required OPRA and gated indicative option ideas. Version 454 changed the interim path to Alpaca `feed=indicative`: only a fresh quote is considered, and all quote-derived prices and sizing remain estimates rather than executable quotes. The 15-minute delayed trade timestamp is provenance, not a freshness gate. See [Alpaca options data](https://docs.alpaca.markets/us/docs/real-time-option-data) and the [options data-path memo](OPTIONS-DATA-ACCESS-2026-10-28.md).

Cloudflare supports WebSockets in Workers and recommends Durable Objects for durable, coordinated long-lived streams. Cloudflare Cron Triggers require both a `scheduled()` handler and a configured trigger. This Site has no Durable Object binding, scheduled handler, Worker Cron Trigger, or Site automation. Its stream and polling stop when the owner closes the page. See [Worker WebSocket clients](https://developers.cloudflare.com/workers/examples/websockets/), [Durable Object WebSocket guidance](https://developers.cloudflare.com/durable-objects/best-practices/websockets/), and [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/).

The production check exposed an asset-cache issue: the bootstrap loaded `app.js` without a content version, so an already-open browser could retain the prior bundle after deployment. Version 451 added a hash to the application URL and bootstrap URL. A deeper pass found that the bootstrap's four imported modules and the vendor-coverage fetch were still unversioned. The current build content-addresses those modules and data, along with the stylesheet and favicon. The smoke suite compares every versioned URL with the exact served asset bytes. The complete dependency-cache repair is included in version 452.

## Ausar and GitHub

- Ausar remains a separate service. The refresh script expects `/workspace/ausar-r24b-release-2026-10-10` and loopback producers. Its historical publisher calls `/api/ausar/publish`; Shipyard retires `/api/ausar/*` with HTTP 410. The remote Ausar host is not accessible from this workspace, so its current runtime health cannot be confirmed. Ausar data is not a Shipyard source.
- Silicon PR #1, `Add live Shipyard Site runtime snapshot`, is the repository path for the current terminal. It was open before this live-feed pass and will be updated with the fallback, cache-versioning repair, source, tests, and audit. The Silicon repository has no open issues recorded in the connected GitHub search.
- Quant research backup PRs #1–3 are unmerged Ausar hardening against an older pinned revision; they do not verify current runtime health. Femto-lean PR #1 is a separate paper-execution path and remains outside Shipyard. The Agentic work has no deployed Site integration. None of those repos supplies a live Shipyard market feed.

## Remaining proof required for broader claims

1. During the next regular session, observe a real IEX quote with its provider timestamp and receipt timestamp on the owner page. The after-hours subscription acknowledgment is not a quote test.
2. During an open session, run a scan for a liquid symbol. Confirm live IEX stock quote selection, the displayed quote age, and the matching source label. With insufficient history, stale data, or a wide spread, the result must stay empty.
3. During an open session, verify that Alpaca returns a fresh indicative option quote and confirm the UI shows its source, quote age, and estimate status. Do not describe it as OPRA NBBO or executable liquidity. After Tradier access is ready, verify its licensed quote product and timestamps before switching.
4. If scans must continue while the browser is closed, move collection to a deployed scheduled Worker or Durable Object-backed service with an actual trigger and authenticated storage/API. The current Sites deployment has no such configuration.
5. Refresh the upstream Chartlector artifact and verify its as-of date. Continue to show it as stale until the publisher supplies a newer observation.

The terminal is therefore **live for IEX stock data while open**, with SIP and IEX source labeling and fail-closed setup rules. It is not yet a 24/7 background scanner, an OPRA-verified options terminal, or a complete live replacement for the disconnected research pages.

## Current option-feed update — version 454

The current production path is Alpaca indicative options snapshots, explicitly requested by the Worker. Indicative quotes are modified and associated option trades may be delayed 15 minutes. The UI labels option-derived values as estimates and requires a current broker quote before any order decision. This is a live provider path when the account returns data, but the latest check was after hours, so in-session delivery remains unverified.

The supplied Massive documentation describes real-time options quote WebSockets for eligible plans. The connected Massive integration returned `NOT_ENTITLED` for an options snapshot request; WebSocket entitlement has not been separately verified and Massive is not configured in this Site. Tradier remains the next provider to evaluate after account/API access is available.
