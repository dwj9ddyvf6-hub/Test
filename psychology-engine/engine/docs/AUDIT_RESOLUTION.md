# Independent audit resolutions — v0.3.1

| Finding | Change | Regression |
|---|---|---|
| Unchanged RSS items collided when the feed grew | Separate acquisition-envelope table/hash; canonical per-item content hash and revision | Two sequential feed responses store four rows, two duplicates, two acquisition hashes |
| Fresh unaligned tails hid a stale aligned divergence subset | Revalidate freshness and gaps on both aligned subsets | Stale 13-day-old aligned triplet with 96h gaps abstains |
| Revised history erased forecast origins | Query immutable eligible acquisition timestamps before collapsing revisions; replay each vintage | Ten-day fixture retains all five original first-vintage scores after full revision |
| New configuration/population/model targets scored old forecasts | Process identity includes configuration, population, measurement model and entity mapping; discard/record incomparable boundaries | All three boundary variants produce no crossed score |
| Finite large inputs overflowed means | Scale-normalized two-stage means and finite detector/forecast metrics | Two custom-unit 1e308 values aggregate to finite 1e308; strict JSON serialization succeeds |
| Failed monitoring exited successfully | Per-cycle outcomes and summary; exit 1 failure, 3 partial, 0 success | Offline CLI tests verify all statuses and outcomes |

Earlier audit regressions cover unit/entity identity, malformed feeds, typed identifiers, semantic ranges, closed bars, late old revisions, explicit extraction availability, mixed-entity evaluation, gap-period costs and duplicate-source inflation. Tests are engineering verification, not a validation of financial predictions. No audit or regression test accesses a live endpoint.
