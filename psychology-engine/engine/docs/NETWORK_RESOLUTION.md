# Network diagnosis and narrow resolution

The actual selected executor's v1 policy is restricted and its current runtime status reports **enforced**. It contains exact host-only egress rules for package-management destinations. None of the four configured source hosts is included. There are no wildcard hosts, HTTP-method qualifiers or scheme qualifiers in that actual policy. Thus the initial collector preflight was a correct restriction, not a false negative caused by a wildcard parser.

The parser now validates version/mode, HTTPS/default port, GET-only operation and the documented exact-host rule shape. Unknown policy versions or qualifiers, wildcard rules and absent policy files fail closed; it does not guess their semantics. These conservative unsupported-rule cases are distinct from this executor's known absent-host grants. Tests cover hostname case, suffix tricks, nondefault ports, HTTP, missing files and unsupported method/scheme/wildcard shapes.

Narrow requested access for the configured collectors is HTTPS, GET, default port 443:

| Host | Request path |
|---|---|
| www.federalreserve.gov | /feeds/press_all.xml |
| www.frbsf.org | /wp-content/uploads/news-sentiment-chart-2.csv |
| wikimedia.org | /api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Stock_market/daily/{start}/{end} |
| cdn.cboe.com | /api/global/us_indices/daily_prices/VIX_History.csv (configured legacy endpoint; see canonical review below) |

The managed workflow exposes host permissions; GET/path scoping above expresses the application's narrower need, not a claim that the environment editor supports those extra fields. The supported resolution is the managed Cloud Environment configuration workflow with user review: add only approved exact source domains, then verify observed policy state is enforced before a bounded read. No configuration-write tool is exposed in this executor. Editing the local snapshot cannot grant access. Neither alternative hosts nor web/browser tools may be used to route engine ingestion around this restriction.

Documentation-only review of the [official Cboe history page](https://www.cboe.com/tradable-products/vix/vix-historical-data) on 2026-10-30 confirms that its current-history link points to **cdn-api.cboe.com**, while some older-history links point to cdn.cboe.com. The CSV link was not followed. The exact new endpoint path and deployment rights still require review. No endpoint was silently changed and neither host was granted. If the canonical endpoint is adopted, version the configuration and request only its exact reviewed host; do not automatically authorize both domains or a wildcard.

HTTP access and data rights are separate. Cboe history must remain behind the usage/retention gate, and fetched history is not included in public artifacts. FRBSF attribution/private-gain restrictions remain in source policy; raw newspaper articles are not included. Wikimedia Analytics CC0 permits the supplied small observed example, with identifying User-Agent and serial-request requirements for future collection.

An existing, checksum-verified Wikimedia receipt captured earlier by the parent research thread was imported without networking. This demonstrates real-data parsing, provenance and analysis while preserving the unresolved outbound permission gate. It does not establish a working outbound collector.
