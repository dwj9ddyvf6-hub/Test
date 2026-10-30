> Historical audit record. The public copy generalizes private connected-tool provenance in the source registry; its current checksums and test results are in [PUBLIC_VALIDATION.md](../PUBLIC_VALIDATION.md). Engine code is unchanged.

# Psychology Engine independent implementation audit

Audit date: 2026-10-30 UTC. Final candidate reviewed: `implementation_v031/psychology-engine-research` (engine 0.3.1, database schema 3), following independent findings on v0.1 and v0.3. This is a local code/fixture audit, not a market-performance study. No live source endpoint was called, no network-policy workaround was attempted, and no implementation file was changed by this auditor.

## Current result

**Final v0.3.1 candidate passes the bounded independent engineering audit.** All **58 shipped tests pass**, the **same five independent regression tests pass unchanged**, and **all package checksums match**. Offline import, snapshot, contract-envelope, Markdown report, pattern detection, proxy forecasting and return-evaluation smoke checks pass, including strict finite JSON serialization of their fixture outputs. The five v0.3 defects below have been corrected and retested. No remaining critical blocker was identified in the reviewed paths. This is not a certification of production readiness or predictive value.

The original v0.1 package had 23 passing tests. All original source files, documentation, fixtures, and saved outputs were inspected or parsed and checked. The v0.3 audit focused on changed implementation modules, new tests, contract schema, source parsers, and temporal/forecast logic. The v0.1 reported dedup-units, null identifiers, entity identity, late old revision, empty feed success, mixed-entity evaluation, and gap-cost defects are addressed in v0.3; the separate aggregate-overflow defect was subsequently corrected in v0.3.1.

## Resolved findings from the v0.3 audit

The following reproductions document the pre-fix behavior. All five now pass their independent regression tests on v0.3.1. Fix review confirms: A01 stable per-item hashes plus separate acquisition ledger; A02 post-intersection usability checks; A03 origin times read directly from the immutable observations ledger; A04 process identity and explicit incomparable-boundary records; A05 overflow-resistant scaled means and finite-result checks. The monitor operational issue below is also corrected.

### A01 — High — An ordinary RSS feed update fails the entire collection transaction

**Locations:** `psychology_engine/adapters.py:121–127, 139–144`; `psychology_engine/core.py:164–169`.

Each parsed item receives `raw_content_hash` of the entire RSS response. The item revision depends on its own title, publication time and config. Adding an unrelated item changes the response hash attached to all unchanged items without changing those items' revisions. Ingestion compares that hash as semantic provenance and raises a revision collision, rolling back the new item too.

**Reproduction:** a mocked one-item feed collects successfully with two observations; the same feed plus one new item returns `status=failed,error_type=ValueError`, and the database stays at two rows. No HTTP is involved.

**Minimal correction:** use a stable per-item raw/canonical content hash for immutable item provenance; retain response/retrieval hashes separately in a fetch/run ledger. Do not suppress genuine changed-item collisions. Regression: unchanged old items plus a new item must collect successfully and leave four rows.

### A02 — High — A fresh unaligned tail can make stale, widely separated observations trigger divergence

**Locations:** `psychology_engine/patterns.py:69–77`, especially 74–76.

`usable` validates each full series before timestamp intersection. The latest three aligned observations may be much older and have much wider gaps than each series' fresh tail. The aligned sample is not checked again.

**Reproduction:** sentiment and prices align on October 1, 5 and 9. Both have fresh October 20–22 tails, but those tails have different timestamps. At October 22 the detector emits `watch` based on October 1/5/9: the last aligned observation is 13 days old and gaps are 96 hours, although the limits are a 96-hour source TTL and 72-hour gaps.

**Minimal correction:** after intersection, validate both selected aligned triplets, including minimum size, unique ascending event times, maximum gaps, and endpoint freshness. Otherwise abstain.

### A03 — High — Later revisions erase historical forecast origins and alter the scorecard's sample

**Locations:** `psychology_engine/patterns.py:8–22, 99–118`, especially 101.

The forecast's origin timestamps are derived from `history(as_of)`, which first collapses every item to its latest available revision. Original availability times of superseded observations disappear. This is not a complete reconstruction of the immutable vintage ledger and allows future revisions to change which past forecasts are evaluated.

**Reproduction:** ten daily observations yield five walk-forward predictions. Add a later revision for each item, all received on day 11. The walk-forward count becomes zero, although the original observations and forecasts were genuinely available on earlier days and still exist in SQLite.

**Minimal correction:** enumerate all eligible immutable revision availability events directly from the ledger, filtered to source/entity/horizon/dimension/units and the evaluation cutoff; reconstruct observations at each event. Preserve issued forecast identity/config and score its first compatible observed target. Add a test that subsequent revisions do not remove or rewrite already matured historical forecast scores.

### A04 — Medium — Forecast score crosses a configuration boundary without disclosure

**Locations:** `psychology_engine/patterns.py:85–87, 106–114`.

Series construction separates config versions, but pending predictions contain no config identity, and the target selected from a later configuration is scored against the earlier configuration's forecast. This silently bridges a possible measurement/model change.

**Reproduction:** five v1 observations followed by five v2 observations produce one historical score: the forecast issued from v1 on day 5 is compared with the v2 observation on day 6. Neither version has a compatible sixth observation, so under version-boundary abstention there should be zero scored targets.

**Minimal correction:** carry source/units/config/population identity with every issued forecast and target; abstain at incompatible boundaries unless an explicitly versioned comparability map permits the comparison. Arbitrary different source config strings should not automatically invalidate a cross-source comparison when measurement semantics are truly compatible; identity should represent the relevant measurement/model semantics.

### A05 — Medium — Finite imported values can produce Infinity in a valid-looking snapshot

**Locations:** `psychology_engine/core.py:120–126, 217`; related arithmetic in `psychology_engine/patterns.py` should also be guarded.

Input validation rejects nonfinite values but not overflow of intermediate sums. Two accepted `VIX_index_points` observations of `1e308` from distinct families produce `population_measures.value=Infinity` and `measures.VIX_index_points=Infinity`. Python's default JSON encoder emits the nonstandard token `Infinity`.

**Minimal correction:** use overflow-resistant means and validate all derived quantities as finite; reject implausible source-specific ranges where justified, or explicitly abstain with an arithmetic/data-quality reason. Serialize public JSON with `allow_nan=False` as a final invariant. The financial-return evaluator's bounds do not cover snapshot or pattern arithmetic.

## Test artifacts and reproduction

Run from the candidate checkout:

```bash
python -m unittest discover -s tests -v
PYTHONPATH=. python -m unittest discover \
  -s ../audit \
  -p test_independent_regressions.py -v
```

- `baseline-tests.txt`: v0.1 shipped tests, 23/23 pass.
- `v03-shipped-tests.txt`: v0.3 shipped tests, 50/50 pass (one unclosed-test-file ResourceWarning).
- `test_independent_regressions.py`: five executable desired-behavior regression tests; no live endpoints.
- `v03-independent-tests.txt`: five confirmed failures on v0.3.
- `v031-shipped-tests.txt`: 58/58 shipped tests pass on v0.3.1.
- `v031-independent-tests.txt`: 5/5 unchanged independent tests pass on v0.3.1.
- `v031-checksums.txt`: every final package checksum matches.
- `probe_v03.py`, `v03-probes.txt`: small diagnostic reproduction and actual outputs.

The v0.3 independent failures were application defects, not tooling/environment errors; they are now fixed and the unchanged assertions pass. The tests are outside the implementation so the implementation owner can fix code without concurrent edits.

## Capability and research-contract assessment

The implementation is a **bounded research scaffold**, not the full design contract. This distinction is appropriately stated in the README and `docs/CONTRACT_IMPLEMENTATION.md`.

| Requested capability | Present in candidate | Material remaining boundary |
|---|---|---|
| Gather | Four public-source parsers/readers, user JSON/CSV imports; bounded request/retry/read limits | No end-to-end live ingestion was established in the engineering environment. Public access does not establish redistribution rights. RSS rolling-update defect A01 is fixed; local mock continuity passes. |
| Measure | Tiny transparent headline lexicon, FRBSF tone proxy, pageview attention, VIX risk proxy, typed imports | Not calibrated claim/entity/speaker extraction; no trained financial NLP provider, representative-population belief estimate, or comprehensive emotional/positioning inference. |
| Track | Immutable SQLite observations and snapshots, revision clocks, source health, availability gating, freshness, declared-population separation | No stable-author panels, origin/exposure lineage, learned dependence, comprehensive coverage denominator, semantic drift monitor, or externally verified historical vintages. |
| Find patterns | Four deterministic descriptive detectors with evidence and abstention | These are not an executable implementation of all 16 research cards. Attention's recent-three/prior-three ratio is a level-growth comparison, not a formal second-difference acceleration measure. Narrative concentration explicitly abstains. The stale-alignment defect A02 is fixed. |
| Forecast | Next-observation persistence/drift point estimates and a small historical ridge evaluator | No calibrated distribution, latent belief-state forecast, validated market forecast, matched Tensor opportunity study, or predictive-skill evidence. The identified vintage/version score-integrity defects A03/A04 are fixed. |
| Inform trades | Evidence/advisory outputs; no order interface, unchanged Tensor authority | No automatic entries, vetoes, sizing, exits, portfolio/risk authority, or approved deployed integration. This separation should remain. |

The supplied `engine_contract.json` is explicitly DESIGN_ONLY/HYPOTHESIS. Its 12 dimensions, claim fields, population/author lineage, forecasting distributions, calibration, block/cluster uncertainty, nested validation, trial ledger, and matched after-cost Tensor comparison exceed this implementation. Null or empty output fields are honest unsupported-state disclosures, not proof those scientific functions exist. A contract-shaped output passes shape checks but does not establish semantic completeness.

The companion `pattern_registry.json` contains 16 research cards with unvalidated test status; the implementation originally contains five provisional hypothesis descriptions plus four simple detectors. Merely bundling the research registry cannot make those research cards executable. The final v0.3.1 package contains both complete research registries: 16 pattern cards and 50 sources. The source registry bytes match the current research original exactly; the pattern registry matches its recorded transferred SHA-256 but the current research master has since changed, so latest-master byte identity is not claimed. SHA-256 values are recorded in the integration manifest/capabilities output. All 16 cards are explicitly marked research_candidate_not_implemented_as_specified with test_result NOT_RUN, separate from the four implemented descriptive detectors.

## Chronology, security and operational observations

- Snapshot gates event, publication, first-seen and maximum receipt/extraction/bar-availability times. Ordinary import does not backdate historical availability; historical mode requires supplied clocks but trusts the operator's attestations.
- Latest revision now orders publication before receipt, resolving the reproduced late-old-revision downgrade. Source/item/revision identity now includes entity, horizon and units. Exact text dedup now includes units/entity/horizon.
- Return evaluation uses explicit label availability, train-only standardization, common complete-case samples, and nonoverlapping training/test holding windows. Gap costs now match the flat-between-holdings assumption. These properties do not address event dependence, survivorship, model-selection uncertainty, capacity, borrow/funding, or prospective validation.
- SQL values are parameterized. Source text is used as data in lexicon/parsers and is not evaluated as executable code or LLM instructions. The public reader disables redirects and avoids persisting remote exception messages. No order/execution interface is present.
- The v0.3 monitor success-exit defect is fixed in v0.3.1: summary/status and exit codes are 0 for all-success, 1 for all-failed, and 3 for partial success. Shipped mocked CLI tests cover all three. Repeated source collection additionally requires an explicit versioned operator source-policy authorization setting; no scheduler was activated.
- JSON/CSV source imports and raw source families remain trusted operator inputs; self-declared families are not proof of independence. The code labels the family count accordingly.
- Local code and fixtures were accessible. Live source validation was intentionally not attempted because the originating environment denied the hosts; it remains unverified, not silently passed. No denied-path read, external source request, credential access or policy bypass occurred during this audit.

## Final acceptance boundary

The exact v0.3.1 candidate passed the shipped suite, unchanged independent regressions, offline workflow smoke checks, strict finite fixture-output JSON checks, checksum checks, and registry count/hash comparisons (source registry also byte-identical to current research master; pattern-master updates require packaging reconciliation). Only documentation-only clarification may occur after this run; any executable change requires affected tests to be rerun. Preserve the maturity statement: engineering checks pass, while predictive validation, prospective collection, implementation of the 16 research cards, and live integration remain unestablished. No external endpoint validation or financial-performance inference was performed.
