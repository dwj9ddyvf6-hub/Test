# Semantic audit and bug-fix pass

**Scope:** all 30 forecast engines, their catalog inputs, scorer transforms, Edge cards, and frozen primary outcome contracts. This is a semantic/static audit of the research implementation; it is not a predictive-performance study.

## Cross-engine checks

- Parsed every scorer and confirmed each formula reads exactly the inputs declared by its `EngineSpec`; no undeclared, missing, or silently unused feature remains.
- Reconciled all 30 Edge-card target definitions to the matching frozen primary label. Secondary ideas such as first-passage barriers, handoff timing, dispersion change, event decomposition, and post-effective reversal remain research diagnostics and cannot silently replace the registered outcome.
- Ran every scorer with a schema-valid neutral feature set and confirmed finite forecast values, model scores, and drivers.
- Added explicit value domains: `ratio` is `[0, 1]`, `signed_ratio` is `[-1, 1]`, and regression `beta` is signed/unbounded. Invalid domains cause forecast abstention. Direct scorer calls also reject non-numeric, boolean, and non-finite features.
- Hardened runtime input handling: malformed feature objects and boolean/coercible-string observations abstain safely rather than crashing or silently becoming numeric values.
- Kept abstention manifests strict-JSON-safe when a rejected feature contains NaN or infinity.
- Bound ledger records to the registered target identity (target, units, horizon, forecast unit, and score semantics); outcome rights attestations now require an actual boolean. Sensitivity ranges cannot leave the registered hard input domain.
- Kept forecast collision panels separate across target-contract hashes and exact frozen windows; non-directional risk/continuous scores are no longer labeled directionally stable by the boundary map.
- Made numerical scorer failures produce explicit abstentions, and fixed the boundary-map invalid-symbol path so malformed requests return the intended abstention report.
- Made ledger snapshots point-in-time with respect to actual event insertion as well as claimed issue/availability/ingestion times. The read path now rejects malformed forecast envelopes and legacy outcomes without explicit rights, complete horizons, matching units/roles, finite numeric values, and valid source hashes.
- Preserved auditable abstention attempts with future requested cutoffs while rejecting future-cutoff emitted forecasts; the ledger also rejects calibrated-probability claims in this release, whose outputs remain uncalibrated.
- Revalidated outcome timing and provenance in target-provenance reports while keeping historical frozen contract versions separate from the current window allowlist; numeric diagnostics reject booleans and coercible non-numeric values.
- Bumped the implementation identifier to `0.9.2-hypothesis`; the model fingerprint binds the updated scoring and validation code.
- The follow-up integrity pass made malformed timestamp types produce controlled validation errors, made invalid forecast cutoffs explicit abstentions, made the source-refresh labels prove horizon completion from their timestamps, bound the refresh-history fingerprint to the selected labels and timing, and made malformed ledger JSON report as a failed integrity sequence.
- The reporting-layer pass now requires literal `true` for calibration attestations, keeps abstention-summary means finite for extreme but valid observations, and rejects malformed status or identity fields instead of crashing or silently grouping them under coerced text.
- The additional audit normalized horizon-overlap cutoffs to UTC before cross-symbol grouping (so equivalent timezone spellings count as one instant) and made both outcome reports reject non-string source IDs.
- Label audit gates now reject zero-length legacy target windows, and tail-threshold units are trimmed consistently with duplicate normalized units rejected.
- A persistence audit found that legacy outcomes could attach a target window after forecast time or change a previously frozen label transform. Forecast writes now validate optional legacy bindings, final-outcome writes require exact matches, and ledger readback plus all three outcome audits reject mismatches while retaining valid frozen legacy windows.
- A numerical-evaluation pass reproduced QLIKE cancellation: a finite variance miss of roughly `1e-10` returned a zero loss. QLIKE now uses a near-unity `log1p` path and the stable `expm1(x) - x` loss form, while retaining overflow rejection for unrepresentable losses. Risk-ranking AUC now uses sorted tie groups with exact half-credit accounting, reducing the prior positive-by-negative pair scan from quadratic to `O(n log n)`; an exhaustive tied-score comparison matched the pairwise reference in 329,364 cases. Calibration reliability bins now allocate only for populated bins and reject counts beyond binary64's exact-integer indexing range, so a large caller-supplied count cannot trigger dense allocation or silently degrade bin indexing. Standard `int(p * bins)` boundary behavior is preserved.
- A model-identity audit reproduced acceptance of a fabricated model fingerprint by `append_forecast`. Contract-bound writes now require the fingerprint computed from the registered implementation and its matching engine version; malformed model identities are rejected during readback. Target-unbound historical records without model fingerprints remain appendable as legacy records.
- A follow-up identity/diagnostics audit found two readback/reporting gaps: a contract-bound payload could lose its model fingerprint and still count as valid, and duplicate engine records could cast extra votes in cross-cluster orientation entropy even while median aggregation was suppressed. Readback now rejects bound records missing model identity, and entropy is suppressed whenever an engine ID is duplicated within a panel.
- A source-refresh label audit found that negative labels were incorrectly required to wait for a later-than-horizon refresh even after their no-refresh horizon had matured. Negative labels now mature at the horizon end; positive labels still require the refresh event to precede label availability. Observation IDs are also deduplicated after the same whitespace normalization used in the history fingerprint, preventing one ID from entering twice under padded spellings.
- A panel-identity audit found that equivalent frozen target windows written with different UTC offsets were split into separate collision panels. Window bounds are now validated as complete, positive intervals and normalized to UTC before panel grouping; malformed target-window identities are rejected.
- A provenance-accounting audit reproduced negative summary counts when a malformed target-contract hash still accrued valid-looking window/transform subtotals. Bound-window, transform, and context subtotals now accrue only for syntactically valid contract fingerprints; regression coverage confirms derived counts stay non-negative.
- A deeper provenance pass found literal sentinel strings could impersonate missing contracts/windows, malformed contract hashes could pass the two label-report gates, and padded frozen identities could be counted as valid after trimming. Grouping now represents absence separately, the label reports require SHA-256 contract hashes, and provenance preserves exact frozen values while checking current target identity/status. Scenario-only attempts no longer inflate missing label-binding totals.
- The next ingestion/ledger/diagnostics pass found the collision map still encoded missing target identity with display sentinels, so a literal matching value could merge panels; grouping now keeps `None` distinct and sorts optional fields safely. The map also rejects malformed direction values before category aggregation. CLI JSON readers now reject duplicate object keys and non-standard NaN/Infinity constants. Ledger writes verify the existing hash chain inside the write transaction and fail closed instead of extending a corrupted chain.
- A numerical edge-case pass reproduced `OverflowError` while averaging three maximum finite values, despite the mathematical mean remaining representable. Paired-loss and abstention summary means now use scaled summation. The source-refresh fingerprint also no longer incorporates a first-refresh timestamp later than its evaluation cutoff, so future events cannot change the historical report identity.
- A final input-coercion pass reproduced an uncaught `OverflowError` when caller-supplied stress-range endpoints were arbitrary-precision integers outside binary64. Boundary-map range parsing now translates conversion overflow into its ordinary finite-range `ValueError`, with a regression covering both extreme endpoints.

## Engine-by-engine disposition

| ID | Engine | Audit result |
|---|---|---|
| FE01 | Multi-horizon trend persistence | Return target aligned; horizon components and path-quality multiplier consume only declared inputs. |
| FE02 | Regime-gated residual reversion | Residual sign and mean-reversion gate aligned; Hurst and trend gates are range-checked. |
| FE03 | Breakout acceptance and survival | Frozen outcome is underlying return; acceptance/failure labels remain distinct secondary events. |
| FE04 | Overnight gap decomposition | Frozen outcome uses the declared open reference; acceptance now switches between continuation and gap fade, with a neutral score at ambiguous 50% acceptance. Fair-gap inputs remain as-of constrained. |
| FE05 | Breadth participation impulse | Frozen outcome is benchmark-relative index return; breadth sign and bounded breadth delta are explicit. |
| FE06 | Sector leadership diffusion | Frozen outcome is benchmark-relative sector return; handoff is not mixed into the primary label. |
| FE07 | Cross-asset lead-lag graph | One selected lag endpoint is the primary outcome; regression beta is correctly signed and unbounded. |
| FE08 | HAR-style realized-volatility forecast | Variance output and target units agree; fixed an extreme-value bug so the log-ratio uses the same clipped values as the emitted variance. |
| FE09 | Jump and overnight-tail hazard | Risk rank maps to the absolute-return barrier event; cause-specific/downside labels stay separate. |
| FE10 | Volatility and correlation regime transition | Risk rank maps to one binary transition outcome; transition direction is not conflated. |
| FE11 | Closing-auction imbalance pressure | Close-to-next-open outcome aligned; positive imbalance and rebalance flow convention is documented as net buying. |
| FE12 | Liquidity fragility / halt hazard | Risk rank maps to persistent depth/spread impairment at the selected endpoint. |
| FE13 | Order-flow-imbalance adverse selection | Added a bounded depth-replenishment ratio and attenuation; renamed the markout feature to `historical_post_fill_drift_z` and require it to be available before `as_of`. |
| FE14 | Options-implied downside tail state | Risk rank maps to a physical left-tail event; risk-neutral surface values remain inputs, not physical probabilities. |
| FE15 | Dealer-gamma scenario map | Scenario-only label remains non-labelable; corrected the hedge-flow sign for positive assumed dealer gamma and documented the scenario convention. |
| FE16 | Options-flow response with intent uncertainty | Replaced ambiguous call/put volume imbalance with signed customer delta-equivalent aggressor flow plus separate aggressor-side confidence; low confidence shrinks direction toward zero. |
| FE17 | Earnings absolute-move forecast | Edge card now matches the frozen absolute-return outcome; implied-move residual remains a separate diagnostic. |
| FE18 | Post-earnings drift after controls | Sector-residual return from the executable post-release open is the sole primary outcome. |
| FE19 | Consensus revision diffusion | Issuer residual return is primary; dispersion change is not mixed into that label. |
| FE20 | Alternative-data nowcast with panel-drift control | Frozen next-period fundamental-surprise z-score aligned; stability, coverage, and drift only weight the estimate. |
| FE21 | XBRL cash-conversion inflection | Frozen-accession-to-next-comparable-filing change aligned; filing vintage and comparability guards retained. |
| FE22 | Filing and guidance semantic delta | Next comparable filing is the primary endpoint; event-level alternatives are no longer presented as equivalent labels. |
| FE23 | Insider activity adjusted for plan status | Filing-availability return aligned; renamed the liquidity feature to `issuer_illiquidity_z` so its dampening sign is unambiguous. |
| FE24 | 13F crowding-unwind hazard | Fixed staleness semantics: older filings now discount crowding evidence instead of mechanically increasing unwind risk. The binary unwind event excludes illiquidity. |
| FE25 | Executed buyback support | Executed pace and issuer residual return aligned; renamed liquidity input to `liquidity_anomaly_z` because either-direction deviation attenuates the score. |
| FE26 | Index rebalance and basket flow pressure | Effective-date constituent relative return is primary; post-effective reversal is separate. A passed effective date now emits zero pressure instead of maximum time weight. |
| FE27 | Macro surprise reaction function by vintage | Fixed 30-minute post-release return is primary; cycle reaction is bounded to `[-1, 1]` and its sign convention is explicit. |
| FE28 | Yield-curve and credit regime transition | Binary stress transition is primary; curve and credit feature signs are documented. |
| FE29 | Commodity positioning, inventory, and supply shock | Commodity excess return is primary; COT crowding, inventory, roll-yield, and supply-shock orientations are explicit. |
| FE30 | Crypto liquidity/crowding squeeze risk | Venue-specific liquidation/depth squeeze is the binary risk target; output is a rank, not direction or calibrated probability. |

## Regression evidence

Focused regressions live in `tests/test_semantics.py` and `tests/test_integrity.py`. They cover the 30-way input/target audit, all 30 end-to-end forecast and ledger writes, repaired FE04/FE08/FE13/FE15/FE16/FE24/FE26/FE27 semantics, malformed/non-finite input handling, target-binding and model-identity integrity, bound and frozen-legacy label round trips, point-in-time event cutoffs, malformed-label rejection, malformed ledger payloads, source-refresh horizon maturity and cutoff-stable fingerprints, metric-attestation validation, overflow-safe summaries, timezone-equivalent cutoff grouping, source-ID type checks, window/transform binding, sentinel-safe report grouping, scenario-only accounting, diagnostic range/window behavior, strict CLI JSON ingestion, and refusal to extend a broken ledger chain.

Command:

```powershell
python -m unittest discover -s research/forecast_engines/tests -v
```

Result: **72 tests passed.**
