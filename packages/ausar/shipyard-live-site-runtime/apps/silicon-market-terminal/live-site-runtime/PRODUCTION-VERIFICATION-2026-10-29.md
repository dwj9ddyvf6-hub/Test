# Production verification — 2026-10-29

Checked at 2026-10-29 03:06 UTC against Shipyard Site version 452.

- Production URL: https://shipyard-mobile.j2wrgxpsj9.chatgpt.site (custom owner-only access; one owner allowlisted, no groups or external viewers).
- Published source commit: `4ad9bf71d174db1134e138e15c70a47f119ea192`.
- The owner browser loaded `app-bootstrap.mjs?v=53cac668e0f27264` and `app.js?v=98f62d11c74686e5`. CSS and favicon URLs also carry content hashes. The bootstrap imports four separately versioned modules; `research-adapters.mjs` also versions its evidence-contract dependency. The app versions its vendor catalog request. The smoke test hashes served bytes and checks every URL against its exact dependency.
- `GET /api/status` returned `mode=read_only`, `keyConfigured=true`, stock stream/bar/scan/context reads enabled, and `accountData=false`, `orderAccess=false`. This confirms secret presence and route configuration only; it does not confirm all market-data entitlements.
- `GET /api/alpaca/bars?symbol=SPY&days=20` returned 14 real Alpaca IEX split-adjusted daily bars. The latest completed bar was dated 2026-10-28: open 771.33, high 773.33, low 769.27, close 772.28, volume 1,163,105, 16,707 trades. Provider observation time was `2026-10-28T04:00:00Z`; the API response was received at `2026-10-29T03:06:40Z`.
- `GET /api/alpaca/brain/scan?symbol=SPY` returned `market_closed`, `setups=[]`, and options `not_scanned` because the regular session had ended. No stale after-hours quote was presented as live.
- The owner UI showed `IEX connected · waiting for quotes`. Alpaca had rejected SIP access before the IEX fallback was deployed. This after-hours check proves IEX stream authentication and subscription acknowledgement; it does not prove an in-session quote was received.
- OPRA access and a fresh open-session options snapshot remain unverified. The application requests OPRA and does not substitute indicative options data.
- Trade Brain scans and streams only while its page is open. There is no deployed cron trigger, scheduled handler, durable background scanner, Yahoo feed, account/position access, or order submission.
- The Worker embeds an explicit allowlist of ten production assets. Local fixture modules are excluded from that request surface. Mock provider responses exist only in the isolated smoke test; they are not live market data or Trade Brain inputs. Manual labs use user-entered scenarios or local CSV.
- The production build embedded 10 assets (597,036 bytes). The strengthened Worker smoke check passed 30 views, including exact content-hash checks for scripts, imported modules, catalog, style, and icon. All 13 Market Overview checks passed.

## Source basis

- [Alpaca market-data plans](https://docs.alpaca.markets/us/docs/about-market-data-api): Basic provides IEX equities and indicative options; consolidated equities and OPRA coverage require the appropriate entitlement.
- [Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq): IEX is one exchange; SIP consolidates US exchange quotes and trades.
- [Alpaca real-time stock stream](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data) and [latest quote API](https://docs.alpaca.markets/us/reference/stocklatestquotesingle-1): IEX/SIP feed selection and timestamped quote responses.
- [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/): background schedule requires a configured trigger and `scheduled()` handler; neither is present in this Site.

## Remaining live-session proof

1. During the next regular session, capture a real IEX quote with provider time and receipt time, then verify the scan displays the same feed and quote age.
2. Verify OPRA entitlement and a fresh option snapshot during an open session. Until then, option suggestions stay gated.
3. If scanning must continue after the browser closes, deploy and configure a scheduled Worker or Durable Object-backed collector with authenticated persistence and monitoring.
4. Refresh the upstream Chartlector artifact; its source remains a dated published snapshot, not an auto-generated feed.

## Version 453 options-data hardening

Checked at 2026-10-29 03:24 UTC against Shipyard Site version 453.

- Published source commit: `33a6b9accd2042312903954da84fd876310dc5b6`.
- The Worker now rejects an option quote older than 90 seconds before returning an option setup. This matches the browser freshness limit and prevents direct API/MCP callers from receiving a stale option quote paired with a recent trade.
- Option output identifies Greeks and implied volatility as Alpaca's Black-Scholes-derived analytics. The UI labels delta/IV as model output.
- The production Site MCP scan returned `market_closed` at `2026-10-29T03:24:40Z`; the 2026-10-28 regular session had ended. It returned no setups and marked options `not_scanned`. This verifies the deployed route's closed-session behavior; it does not verify current OPRA access.
- The focused Worker smoke passed after the change, including a regression case with a ten-minute-old OPRA quote and a ten-second-old option trade. It retained a qualifying stock idea but returned no option idea.
- Deployment succeeded as version 453 at the existing owner-only URL. The Site still has one owner allowlisted and zero external viewers.

The next in-session proof remains open: confirm Alpaca's OPRA entitlement and hosted-use approval, then compare a fresh live contract quote with Alpaca's entitled display.

## Version 454 — Alpaca indicative options update

Checked 2026-10-29 03:51 UTC against the production Site.

- Production URL: https://shipyard-mobile.j2wrgxpsj9.chatgpt.site (owner-only access retained).
- Site version 454; source commit `e25d1ecf0864561afefd40a05f55fb2331aeb1bd`; deployment `appgdep_6ae2c273dec08191a0503da1df16064b` succeeded.
- The Worker now explicitly requests Alpaca `feed=indicative` for option snapshots. An option quote must be no older than 90 seconds. Alpaca option trades may be delayed 15 minutes; the delayed trade timestamp is disclosed and does not invalidate an otherwise fresh quote.
- Option ideas are marked indicative, price and risk are estimates, and the UI requires a current broker quote before an order decision. Account, position, and order routes remain unused.
- The focused Worker smoke check passed after the update. It verifies a current indicative quote alongside a 900-second-old trade timestamp and still rejects a stale option quote. The check uses fixtures; it does not prove live-session options access.
- The production visual check was after hours and showed the market closed, so live in-session option data has not been verified.
- The supplied Massive docs describe a real-time options WebSocket for eligible plans. A request through the connected Massive integration returned `NOT_ENTITLED` for an options snapshot endpoint; the WebSocket entitlement itself has not been separately tested. Massive is not configured in the Site.
- Tradier remains the planned replacement after the user's account and API access are ready.

This v454 section supersedes the version 452/453 statements below about the options feed. The earlier entries remain as release history.
