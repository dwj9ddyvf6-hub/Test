# Psychology Engine research package

A runnable Python 3.10+ research reference implementation. It compiles timestamped evidence into an explainable multidimensional state, stores revisions in SQLite, and emits an advisory record. **It has no order interface. Tensor remains entry timing authority.** No deployed system, credential, schedule or existing trading logic is modified.

## Reproduce without installing dependencies

From this directory:

```bash
python -m unittest discover -s tests -v
python -m psychology_engine --db demo.sqlite import fixtures/observations.json --trusted-historical
python -m psychology_engine --db demo.sqlite snapshot --as-of 2026-10-28T12:00:00Z --markdown
python -m psychology_engine evaluate fixtures/evaluation_synthetic.json
python -m psychology_engine --db public.sqlite monitor --source fed_press --cycles 1
```

The first four commands are offline. The last checks deployment policy and attempts a source read only if allowed, logs an error if blocked, and exits. It does not activate a scheduler. After a versioned source-usage review sets `persistent_use_authorized: true`, finite foreground monitoring supports `--cycles 5 --interval 3600 --source-config reviewed.json`. Maximum 100 cycles; intervals 60–3600 seconds; individual HTTP timeout 15 seconds; two retries by default (three attempts), at most three retries through the Python interface; responses limited to 8 MB. DNS and operating-system behavior can still extend wall-clock timeout. Do not run overlapping collectors against the same database; single-writer deployment is the supported model.

Additional implemented sources are `cboe_vix`, `frbsf_news`, and `wikimedia_attention`. Wikimedia observations belong to `TOPIC:Stock_market`, not `US_MARKET`. Public endpoints and usage terms must be reviewed for your intended deployment. Their availability is not a redistribution license.

## What is implemented

- Immutable, transactional SQLite observations with source, family, item, revision, event time, publication time, first-seen time, ingestion time, entity, horizon, dimension, units, access status, URL, freshness threshold and configuration version.
- JSON and CSV imports. Standard import stamps first-seen at ingestion; explicit `--trusted-historical` accepts supplied first-seen only for independently audited historical vintages. Backfilled archives alone do not prove historical availability.
- As-of snapshots require event, publication and first-seen timestamps at or before the cutoff. Later revisions do not rewrite earlier state. Changed payload under an existing revision fails rather than silently overwriting data.
- Per-observation freshness (from event time); stale and unavailable data are excluded, never filled with zero. Provenance and exclusion reasons remain inspectable. Stored access status describes the observation at ingestion, not a current license grant.
- Exact normalized-text syndication deduplication; same source-family numeric-event deduplication; family-balanced means within compatible units. This does not detect paraphrases or prove statistical independence.
- Seven dimensions: sentiment, attention, uncertainty, disagreement, positioning, stress, narrative change. Only observed inputs appear. Baseline text scoring derives sentiment and uncertainty; FRBSF contributes news tone; Wikimedia contributes topic attention; VIX contributes a stress proxy. Disagreement and temporal attention/stress/divergence detectors operate when prerequisites are met; remaining dimensions accept explicitly measured imports; their absence is visible.
- Small transparent English lexicon with three-token negation, model identity and match count through the scorer API. No sentiment tokens means unknown. Optional financial NLP providers implement the `NLPProvider` protocol; no external model is downloaded or claimed to run.
- Expanding-window ridge evaluation against zero, historical mean and price-only baselines, train-only scaling, explicit label availability, non-overlapping train and test periods, complete-case common samples, flat-gap open/close costs, contiguous-period turnover and final liquidation cost. The evaluator consumes an audited feature table; it does not manufacture historical features from present-day archives.
- Immutable snapshot records, JSON evidence/advisory export, Markdown report, ingestion outcome logs, a versioned hypothesis registry, bounded foreground collection.

## Interpretation

Measures are kept separate by units. A source-family mean is descriptive and is **not** a calibrated probability, latent-psychology estimate or trading signal. Source volume, source dependence, horizon, selection and measurement quality matter. A VIX reading is option-implied risk with pricing and risk-premium components; it is not a direct survey of investor fear. Federal Reserve language is institutional communication, not representative crowd opinion.

The engine never predicts an individual's private thoughts. Research forecasts concern aggregate observable outcomes and distributions. None of the fixture results establishes market predictive skill. See [research design](docs/RESEARCH_DESIGN.md), [source capabilities](docs/SOURCE_CAPABILITIES.md) and [hypotheses](docs/research_companion/pattern_registry.json).

## Deliverables and maturity

`examples/fixture-report.md` and `fixture-snapshot.json` are explicitly synthetic evidence examples. `synthetic-evaluation.json` tests evaluation plumbing on generated observations; it is not a market backtest. `test-results.txt` records engineering tests. `live-probe.json` records this environment's source probe outcome.

This is a tested research foundation, not a completed production forecasting service. Remaining work: authorized live feeds, historical vintage audits, financial-language validation, learned measurement models, topic/stance providers, source coverage monitoring alerts, robust out-of-sample significance analysis, operational deployment and approved integration. No claimed profitable strategy, calibrated market forecast, real-money trading or persistent monitoring is included.

## Temporal detectors and proxy forecasts

```bash
python -m psychology_engine --db temporal.sqlite import fixtures/temporal_observations.json --trusted-historical
python -m psychology_engine --db temporal.sqlite patterns --as-of 2026-10-19T12:00:00Z
python -m psychology_engine --db temporal.sqlite forecast --as-of 2026-10-19T12:00:00Z --source article --dimension attention --units article_daily_user_pageviews
```

These generated fixtures exercise attention acceleration, VIX stress persistence, opposing source signs and aligned sentiment/price divergence. Every result includes evidence IDs, prerequisites and either context/watch or abstention. Thresholds are transparent research settings, not validated trading rules. A single source family produces an advisory diversity abstention; declared family names do not prove independence.

The forecast command predicts the next observed proxy value using persistence and recent mean first differences. It outputs target, units, as-of and next-observation horizon. Its walk-forward scores reconstruct actual available vintages; single-vintage historical archives produce no historical score. No calibrated probability or market-return forecast is claimed by that command.

Optional monitor configuration: `--source-config path.json`. Supply a JSON object keyed by an implemented source name, each with an explicit `config_version` and overridden public HTTPS endpoint/freshness settings. Config changes never bypass the deployment network policy. Credentials, URL passwords and query strings are rejected. Wikimedia currently supports only the explicitly validated Stock_market / en.wikipedia / all-access / user population.

Database schema v3 distinguishes source/item/revision/dimension/entity/horizon/units. Legacy v0.1/v0.2 databases are rejected with an explicit export/reimport instruction instead of being silently rewritten. Archived fixtures can be imported into a new database.

## Availability and contract output (v0.4.1)

Historical imports now require provenance objects containing provider_received_at, locally_received_at and extracted_at. These fixture clocks are supplied only for generated data; never fabricate them for downloaded archives. available_at is the maximum of publication, first-seen, receipts, extraction and any used market-bar availability. Normal import stamps actual local ingestion/extraction time. Snapshot and pattern histories require available_at <= information cutoff.

Use `snapshot --contract` for the contract-shaped descriptive envelope. It distinguishes historical information cutoff from actual output computation/availability and reports replay-only status. Unsupported latent estimates, calibrated probabilities, population coverage and author diagnostics remain empty/null. The original design contract is preserved in `docs/research_companion/engine_contract.json`; a contract-shaped output is not proof that every research requirement is implemented.

Price-return imports require explicit market-context provenance, including instrument, venue, calendar version, bar end, true bar_closed, price-adjustment policy, provider feed, availability, age and context version. Positioning imports require reported_net_exposure, published_short_interest or reported_futures_position measurement_kind; daily short-sale volume and unsigned open interest cannot be passed as positioning by naming alone. Import metadata is an operator attestation, not independent provider authentication.

Population-specific measures are retained. A combined measure is null when populations differ or population identity is unknown. Source health reports only actual logged checks known by the cutoff; absence of a recorded outage is not proof of coverage.

## Audited revision and source registries

The package contains the complete, checksum-verified 16-card research pattern registry and 50-source acquisition registry in `docs/research_companion/`. Documentation does not activate or license the other 46 sources. The four implemented descriptive detectors are listed separately from those 16 unvalidated research cards. `python -m psychology_engine capabilities` returns the distinction.

The RSS collector stores acquisition-envelope hashes separately from immutable item hashes, so adding a new feed item does not rewrite unchanged evidence. Divergence detectors validate the aligned subset after joining. Proxy forecasts reconstruct origins from immutable acquisition history; revisions do not erase earlier scorecards. Config/model/population/mapping changes create explicit incomparable boundaries. Numeric aggregation uses scale-normalized means and output guards. Forecast drift respects simple nonnegative/bounded unit domains but remains uncalibrated.

Monitor stdout is newline-delimited JSON: each cycle outcome followed by a summary containing all outcomes. Exit codes are 0 for complete success, 1 for total collection failure, 3 for partial success, and 2 for CLI/configuration validation errors. No persistent service is activated. Wikimedia deployment additionally requires an operator-supplied contact-bearing User-Agent; no personal address is bundled.

The shipped initial source probe is only a local network-policy rejection receipt, not successful live ingestion. The observed-wikimedia examples separately contain two real CC0 pageview observations imported from a supplied earlier capture, with checksum verification and current local availability; no outbound request was made by that import. Source-research probe references inside the supplied registry are external research records, not files included in this package. Engineering tests and generated examples do not establish market predictive validity.

## Operations and previously captured evidence (v0.4.1)

```bash
python -m psychology_engine --db observed.sqlite import-receipt examples/observed-wikimedia-receipt.json
python -m psychology_engine --db observed.sqlite snapshot --entity TOPIC:Stock_market
python -m psychology_engine --db observed.sqlite backup observed-backup.sqlite
python -m psychology_engine --db observed.sqlite health --source wikimedia_attention
```

Receipt imports are offline. They verify payload hashes, preserve upstream capture time and stamp actual local receipt/extraction. They never backdate this engine's availability. The two supplied observed values (498 and 578 pageviews) are topic attention, not sentiment. They are insufficient for temporal detection or forecasting. Health correctly reports the outbound collector unavailable after receipt-only import; an import is not a successful source poll. The report in `examples/observed-wikimedia-report.md` records the original demonstration; a new reproduction gets its own later availability.

Read-only health checks database integrity, recent collection outcome and usable observation freshness after latest-eligible-revision selection. It returns 0 for healthy, 3 for degraded, 1 for unavailable, without creating a missing database. Online SQLite backup creates its new destination exclusively with mode 0600, refuses overwrite and checks copied integrity. The persistent store survives process restarts; do not publish runtime databases.

[Inactive deployment templates](deployment/README.md) provide per-source schedules, a single-writer lock, health checks and permission-review placeholders. Scheduled collection requires `--scheduled` and explicit versioned usage approval even for one cycle. No service or timer was installed or activated. Templates are starting points requiring an operator's paths, account and permission review, not a deployed service.

[Network diagnosis](docs/NETWORK_RESOLUTION.md) confirms a real enforced host restriction, not a parser mismatch. Managed policy always takes precedence; unknown policy schemas/rules fail closed. Outside managed execution a separate reviewed local policy is required. Local configuration cannot grant network permissions withheld by infrastructure. Public contact for Wikimedia remains an operator-supplied project URL after publication; no personal contact is embedded.

## Public distribution note

This is the privacy-reviewed public copy of v0.4.1. The Alpaca catalog entry is generalized to remove private connected-tool provenance; no adapter implementation is changed. The public registry checksum is recorded in `docs/research_companion/INTEGRATION_STATUS.json`. The aggregate package README, independent audits, full research and report are one directory above. Historical engine validation receipts describe their original candidate; current public-copy checks are in `../PUBLIC_VALIDATION.md`.
