# Public-copy validation — v0.4.1

Date: 30 October 2026 UTC. Scope: the files in this public package, not a deployed service.

## Executed checks

| Check | Result |
|---|---|
| Shipped offline unit/regression suite | 70 passed |
| Independent earlier-behavior regressions | 5 passed |
| Independent operational regressions | 6 passed |
| Pattern registry 1.0.1 | 16 cards; original approved bytes preserved |
| Public source registry | 50 candidates; identical public copies in research and engine companion docs |
| Report | 38-page PDF; PDF/DOCX bytes preserved from reviewed final report |
| Public-copy integrity | SHA-256 manifests regenerated after documented privacy edits |

Test logs are in `audit/public-*.txt`. The historical audit reports and their older logs are retained to show the findings and resolutions; claims that an original registry matched its original hash describe that candidate, not the redacted public copy.

## Privacy and distribution review

Reviewed nested filenames, source/docs/tests/fixtures, JSON payloads, report text, PDF metadata and links, DOCX XML/relationships/metadata, and figure metadata. The report has no PDF attachments, personal author metadata, tracked changes, comments, embedded documents or non-HTTP(S) external relationships. Figure PNGs contain no EXIF.

Changes in the public copy are limited to publication documentation, removal/generalization of private connected-tool provenance in the Alpaca source-catalog entry, removal of source-response bodies from research diagnostic receipts, removal of unrelated publication-transport prose, relative-path normalization in audit prose/test instructions, and associated checksum metadata. Executable Python source and shipped tests are unchanged. Independent regression test logic is unchanged; only a reproduction-command docstring is normalized.

Runtime databases, caches, private account/portfolio state, credentials, personal contacts, internal absolute workspace paths, private connector diagnostics, licensed source payloads and publication-helper scripts are excluded. The sole real-data payload is the specifically labeled two-observation Wikimedia Analytics CC0 example. Source documents and primary citations are linked, not redistributed as a third-party article corpus.

## Limits of the evidence

The tests establish only the bounded behaviors they exercise. They do not prove complete correctness, security certification, historical data authenticity, source permission, live ingestion, continuous availability, forecasting skill or profitability. No network setting, account credential, service, timer, trading integration or order was changed by these public-copy checks.
