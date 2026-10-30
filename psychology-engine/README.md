# Psychology Engine — research and reference implementation

**Version 0.4.1 · 30 October 2026 · research/advisory only**

A point-in-time evidence engine and a 38-page research report for studying observable market beliefs, attention, uncertainty and constraints. This is **not mind reading, a validated trading strategy, or an activated live service**. It has no order interface and does not alter the incumbent timing or risk authority.

## Start here

- **Research report:** [PDF](report/psychology_engine_research.pdf) · [Word](report/psychology_engine_research.docx) · [Markdown](report/manuscript.md)
- **Runnable source:** [engine README](engine/README.md) · [Python package](engine/psychology_engine/) · [tests](engine/tests/)
- **Research:** [behavioral foundations](research/behavioral_foundations.md), [50-source catalog](research/data_sources.md), [forecast design](research/forecast_design.md), [16 research patterns](research/pattern_registry.json)
- **Fixes and remaining gates:** [blocker resolutions](research/BLOCKER_RESOLUTIONS.md), [v0.4.1 corrections](engine/docs/RELEASE_0.4.1.md), [independent operational audit](audit/AUDIT_V04_OPERATIONS.md), [network activation guide](research/NETWORK_ACTIVATION_GUIDE.md)
- **Verification:** [public-copy validation](PUBLIC_VALIDATION.md) · [SHA-256 checksums](CHECKSUMS.sha256)

The report is the research/design baseline. The current code and release/audit notes govern implementation status where later fixes extend that baseline. A proposed pattern, catalog entry or report diagram is not an implemented capability.

## Run offline

Python 3.10+; the reference engine uses the standard library. From this directory:

```bash
cd engine
python -m unittest discover -s tests -v
PYTHONPATH=. python -m unittest discover -s ../audit -p 'test_*regressions.py' -v
PYTHONPATH=. python -m unittest discover -s ../audit -p test_operations_independent.py -v
python -m psychology_engine --db demo.sqlite import fixtures/observations.json --trusted-historical
python -m psychology_engine --db demo.sqlite snapshot --as-of 2026-10-28T12:00:00Z --markdown
python -m psychology_engine evaluate fixtures/evaluation_synthetic.json
```

The exact public copy passed **70 shipped tests + 5 independent regressions + 6 independent operational tests**. These are engineering checks, not evidence of profitable forecasts. Generated fixtures are synthetic. Historical import clocks must be independently supported for real data; never invent them.

## What works

- Immutable SQLite evidence/revision storage, availability-clock gates, compatible-unit aggregation and explicit missing/stale states.
- Four implemented source adapters: Federal Reserve press RSS, FRBSF news-sentiment index, Wikimedia attention, and Cboe VIX. Their existence does not imply permission or verified live collection.
- Four descriptive temporal detectors, next-observation proxy baselines, synthetic evaluation plumbing and evidence-linked advisory output.
- Hash-checked offline receipt import; read-only health; exclusive private-permission backups; inactive deployment templates and scheduled-use gates.
- Documented fixes for feed-update idempotence, aligned-sample freshness, vintage preservation, configuration boundaries, numeric overflow, monitor exit codes, latest-revision health, receipt chronology and backup confidentiality.

## What remains unestablished

**Outbound collection remains restricted in the audited engine environment.** No service/timer was activated. Network permission, source-specific usage rights, a real Wikimedia project-contact identifier and operational acceptance checks remain separate gates. Cboe endpoint/rights review remains open. Do not bypass infrastructure restrictions or treat public access as permission to retain or redistribute data.

The 50-source catalog and 16 pattern specifications are research candidates, not 50 live feeds or 16 implemented strategies. Learned financial-language extraction, broad population coverage, calibrated belief/return probabilities, prospective out-of-sample validation and economic value after costs are not established.

Two real Wikimedia CC0 pageview counts are included solely as a small, attributed offline receipt-import example. They are attention, not sentiment; they are insufficient for temporal detection or forecasting. Importing that earlier capture is not a live source poll.

## Public-package boundary

Only reviewed code, documentation, generated fixtures, audit records and the explicitly labeled CC0 example are included. No runtime SQLite database, credential, personal contact, account/portfolio state, private connector receipt or licensed article/market-data corpus is distributed. Research HTTP receipts retain transport metadata and hashes, not response payloads. Private connected-tool provenance in one source-catalog entry is generalized; the public checksums reflect that change.

This directory is an additive, standalone research package. It does not install schedules, alter existing strategies or authorize trading. Publication itself grants no separate software license or third-party data rights.
