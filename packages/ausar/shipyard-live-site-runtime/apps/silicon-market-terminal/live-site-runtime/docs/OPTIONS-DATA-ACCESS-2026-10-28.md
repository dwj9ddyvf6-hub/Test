# Options data path

Reviewed 2026-10-28 ET.

## Current path

Until the Tradier account is ready, the terminal requests Alpaca's `feed=indicative` options snapshots. This is an explicit provider choice, not a fallback from OPRA. The options scan stays read-only and uses server-side Alpaca credentials.

Alpaca describes its indicative option feed as derived from OPRA: quotes are modified and option trades are delayed by 15 minutes. It is not OPRA NBBO and does not provide executable prices. The terminal therefore treats a recent indicative quote as a research reference, labels any resulting call or put candidate `INDICATIVE`, and requires a current broker quote before an order decision. The 15-minute-delayed trade timestamp is shown as provenance and is not used as a real-time freshness gate. [Alpaca historical options data](https://docs.alpaca.markets/us/docs/historical-option-data) · [Snapshot API](https://docs.alpaca.markets/us/v1.4.2/reference/optionsnapshots)

The Worker still enforces a 90-second maximum age for the option quote, standard contract deliverables, current-enough open interest, a bounded indicative spread, and Alpaca's Black–Scholes Greek availability. Indicative bid/ask, spread, midpoint, size, and ask-based risk sizing are estimates; none are treated as fillable liquidity or a limit instruction. No order, position, or account routes are called.

## Provider decision

| Provider | Current role | Notes |
| --- | --- | --- |
| Alpaca | Active interim options source | Existing server credentials and snapshot path; explicit `feed=indicative`; modified quotes and 15-minute-delayed trades. |
| Tradier | Planned later provider | User has applied. After account/API access is available, confirm the data product and use rights, add a server-side provider adapter, and compare returned timestamps and fields before switching. The sandbox is delayed and is not the production quote source. [Tradier market data](https://docs.tradier.com/docs/market-data) · [Streaming](https://docs.tradier.com/docs/streaming) |
| Massive | Future option-stream candidate; unavailable in the connected plan check | The supplied docs describe real-time quote WebSockets at `wss://socket.massive.com/options`, with access listed for Options Advanced and Business + Expansion plans (up to 1,000 contracts per connection). The connected Massive integration returned `NOT_ENTITLED` for an options snapshot request; WebSocket entitlement was not separately verified. No Massive adapter or credentials are configured in the terminal. [Options quote WebSocket](https://massive.com/docs/websocket/options/quotes) |
| Cboe One Options | Venue-subset possibility | Covers four Cboe options exchanges rather than national NBBO; its multicast/UDP feed does not fit this Sites Worker runtime directly. |

No source is scraped or used to evade a provider entitlement. A licensed direct-feed consolidator would require venue feeds, contract/reference data, sequence recovery, clock alignment, and applicable agreements; it is not a quick substitute for a consolidated options feed.

## Operational checks

1. The scan requests Alpaca's snapshot endpoint with `feed=indicative`.
2. A current option quote must be no more than 90 seconds old; missing, invalid, or stale quotes yield no option candidate.
3. The delayed trade time is reported for context, not described as a current trade.
4. The UI labels quote basis and estimated pricing and risk. It never calls these quotes executable or OPRA NBBO.
5. The page refreshes snapshots during scans while open. Alpaca option quotes are not streamed by this implementation; the scan stops when the page closes.
6. Tradier can replace this source after the account is ready. Provider-specific differences in authentication, fields, streaming, and permissions will be verified during that migration.

Alpaca's official pages: [market-data plans](https://docs.alpaca.markets/us/docs/about-market-data-api) · [real-time options stream](https://docs.alpaca.markets/us/docs/real-time-option-data) · [market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)
