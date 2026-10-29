# Ausar Public Paper Terminal

A public, read-only terminal for Ausar. Its mobile dashboard uses charcoal and gunmetal surfaces, layered greys, and restrained gold trim from the supplied armor reference, with distinct semantic colors for gains and losses. It shows market context, open paper positions, currency-separated book equity and P&L, and book-level performance when the local desk reports a supported value.

## Data boundary

`dist/data/desk-snapshot.json` is public. It contains paper positions and account-level paper performance because the desk owner explicitly requested that information be public. It replaces every internal book ID and account label with stable `Paper book NN` aliases. It omits broker account identifiers, broker account names, user names, credentials, order intents, and free-form AI output. The page is read-only and makes no live-trading or profitability claim.

The page checks its published snapshot every 30 seconds and labels it with its observation time and age. TradingView's ticker, QQQ chart, and US event calendar update independently while the page is open; exchange delays and data coverage vary. The repository's GitHub Actions workflow deploys `dist/` on pushes once Pages is enabled for the repository. The private Ausar runtime is not reachable from GitHub's hosted runners, and this repository does not have a persistent publisher attached to the desk host. That means the page auto-refreshes the published data, but the desk snapshot advances only after a fresh snapshot is published; old desk data is marked stale instead of presented as live.

## Refreshing the snapshot

The exporter reads only loopback endpoints and refuses to update unless the configured release README confirms that Ausar is the current name of the former Aster desk. It selects numeric/accounting fields from the read-only paper projection, never copies raw IDs or account names, groups money by currency, and writes the public artifact atomically.

```sh
python3 tools/refresh-desk-snapshot.py
```

That command refreshes the local artifact only. Commit and push the new `dist/data/desk-snapshot.json` to `main` to publish it. A true unattended public desk feed requires an authenticated outbound publisher from the Ausar host or a separately provisioned narrow write endpoint; the full desk API must not be exposed to the internet.

QQQ and SPY comparisons appear only when an account has aligned, distribution-aware benchmark observations. Missing returns, risk ratios, quote freshness, or trade counts remain blank/unknown rather than being replaced with zero. Native crypto spot and listed ETF data remain separate instruments and currencies.
