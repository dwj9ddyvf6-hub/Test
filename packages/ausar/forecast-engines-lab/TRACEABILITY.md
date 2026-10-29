# Corpus-to-engine traceability

This is a synthesis crosswalk, not a claim that any vendor validated an engine. The source reports describe public products, workflows, and disclosed methods; many contain vendor claims, bounded-scope findings, or unverified methodology. The 86-report filename/hash inventory is in `rea_target_inventory.csv` so later review can tie decisions to the exact reports without copying vendor source or data.

## Silicon convergence crosswalk

| Engines | Existing kernels that informed the interface | Research extension |
|---|---|---|
| FE01–FE03 | S03 Daily Price/Trend/Vol; S04 Cross-Section Candidate Filter; S14 Daily-Bar Alert Evaluator | Estimate forward outcomes, with regime filters and acceptance/failure labels; Saty/TheStrat setups remain test candidates. |
| FE04, FE17–FE18, FE25–FE27 | S05 Catalyst/Event Timeline; S08 Expected-Move/Session Map | Forecast event magnitude, conditional drift, or event flow with point-in-time schedules and explicit trigger ambiguity. |
| FE05–FE06 | S02 Macro/Breadth/Rotation; S06 Factor Matrix; S07 Sector Portfolio | Forecast participation and leadership diffusion, not just display current breadth or rank names. |
| FE07, FE10 | S02, S03, S20 Evidence/Provenance Graph | Estimate whether relationships/regimes persist; require rolling stability and preserve source dependence. |
| FE08–FE09, FE14 | S03, S08, S11 Multi-Leg Greeks | Forecast realized variance / tail state separately; risk-neutral values remain distinct from physical outcomes. |
| FE11–FE13 | S09 Options Activity Normalizer; S17 Read-Only Gateway; S19 Evidence Envelope | Forecast auction/flow pressure only with entitled, timestamp-aligned event data. |
| FE15–FE16 | S09 Options Activity; S10 Static Dealer-Exposure Map; S20 provenance | Make dealer sign and trade intent explicit latent assumptions; model these as conditional scenarios. |
| FE19–FE24 | S05, S06, S18 Vendor Registry, S19, S20 | Forecast revisions, XBRL/filing changes, insider/crowding outcomes with publication vintages, parser quality, and staleness. |
| FE28–FE29 | S02 Macro/Breadth/Rotation; S19 evidence envelope | Preserve macro release vintages and commodity report publication schedules. |
| FE30 | S17, S19, S20 | Keep venue, chain-label, liquidity, and data-rights provenance separate; quantify squeeze risk instead of equating a social/on-chain score to direction. |

S12 Cost-Aware Replay and S13 Paper-Only Risk/Action Gate remain separate. This package does not attempt to replicate their replay or action controls.

## Fourth-pass provenance and robustness layer

| Artifact | Contribution across FE01–FE30 |
|---|---|
| fingerprint.py and Forecast.model_fingerprint | Binds each output to the engine spec, validation/scoring and Edge-card code, and Python runtime. |
| FeatureObservation.transform_id/transform_hash | Adds feature-builder lineage; inferred/reproduced values without it abstain. |
| boundary_map.py | Measures caller-defined one-feature flip distance, pairwise score interactions, and joint corner disagreements without assigning scenario probabilities. |
| diagnostics.py | Reports shared transform implementations separately from source-hash/source-ID/declared-group collisions; transform-only overlap does not merge evidence clusters. |
| FOURTH_PASS_AUDIT.md | Records the fresh repo-head check, revised desk-state ref, source findings, and specific FE01–FE30 stress dimensions. |
| abstention_audit.py and ForecastLedger | Labels the target after an abstention in a separate audit role and measures coverage-conditioned outcome tails; it never recasts an abstention as forecast skill. |
| FIFTH_PASS_AUDIT.md | Documents the selective-coverage blind spot, source rationale, label roles, and the new auditable workflow. |
| horizon_overlap.py | Builds actual labeled target intervals, measures within-symbol overlap clusters, and surfaces same-cutoff cross-symbol cohorts without claiming an effective sample size. |
| SIXTH_PASS_AUDIT.md | Documents horizon-overlap dependence as an unmeasured source of pseudo-replication and maps the new diagnostic to forecast evaluation. |
| target_contract.py and target_provenance.py | Give each engine one primary estimand, allowed window IDs, and a separate target hash; report exact-window and label-transform lineage. |
| SEVENTH_PASS_AUDIT.md | Documents mixed-estimand and wrong-maturity label risks, exact endpoint enforcement, FE15's scenario-only classification, and the legacy label boundary. |
| label_context.py | Canonicalizes six instance-level target measurement conventions and fingerprints them separately from target definition and label-transform code. |
| target_provenance.py, abstention_audit.py, horizon_overlap.py, diagnostics.py | Partition label review and forecast comparison by frozen measurement context so unlike series, benchmarks, calendars, vintages, or adjustment bases are not silently pooled. |
| EIGHTH_PASS_AUDIT.md | Documents target-measurement convention drift, its source basis, the label-context protocol, and its caller-attestation limits. |

## Constraints carried forward from the research

1. **Prediction and trade edge are different.** A forecast can be directionally useful but too small or costly to monetize. This package emits no expected net return or order.
2. **Vendor scores are not comparable.** Similar names and charts do not imply identical definitions, coverage, or calibration. No feature is accepted merely because several vendors display it.
3. **Options data have limits.** OI does not reveal dealer-side sign; option flow does not guarantee opening intent; public/delayed data are not exchange depth or a full OPRA tape.
4. **Alternative data have selection and rights risk.** Coverage quality, source eligibility, panel drift, and label confidence are explicit prerequisites.
5. **Historical results need multiple-testing control.** Femto's internal search summaries contain many tested cells, holdout failures, cost failures, and avoid/veto candidates; no universal positive alpha was established.
6. **Interpretive strategies have rule ambiguity.** Saty/TheStrat source materials can inspire causal and event definitions, but incomplete trigger rules and selected examples are not a trade log.

## Vendor and source inventory

`rea_target_inventory.csv` indexes the exact 86 active target-report files in the Silicon snapshot used to build this package, with SHA-256 digests. It is an audit manifest, not an assertion that all 86 products contain forecasting algorithms or that all raw vendor captures were manually re-read in this implementation pass. Vendor-specific use is bounded by each linked report's scope and source-rights notes.

## Second-pass vendor findings

The detailed source/index reconciliation is in [SECOND_PASS_AUDIT.md](SECOND_PASS_AUDIT.md). The follow-on design pass and per-engine Edge contracts are in [THIRD_PASS_AUDIT.md](THIRD_PASS_AUDIT.md). Selected findings that change the forecast contract:

| Evidence family | Source observations | Design consequence |
|---|---|---|
| Chart/setup rules | `saty-ecosystem.md` contains explicit prior-close/prior-ATR levels and EMA-state rules; TheStrat gap material still has a daily-open vs kicking-bar-open ambiguity. | Freeze rule, event clock, and source version before an event study. A displayed level is not evidence of positive expectancy. |
| Backtest/ranking products | Trade Ideas, Option Alpha, QuantiX, AlgoAlpha, and TrendSpider publish different test windows, bar resolutions, gates, and simulation limits. | Preserve vendor/version/data window/costs and all tried variants. A vendor's gates or backtest does not validate this lab's formulas. |
| Options/flow | Cheddar Flow and Unusual Whales describe changing feed/API surfaces, but do not establish a complete quote clock, deduplication, licensing, or dealer-side-position truth in the public evidence reviewed. | Retain source age and lineage. Repeated vendor scores on shared prints are not independent confirmations; open interest is not dealer direction. |
| Automation/paper workflow | Tapeboard's documented fills are simulated and its local Broker Link is a user-clicked ticker handoff; other products separate alerts, backtests, and execution. | Forecast records remain separate from orders, fills, and position state. |
| Filing/positioning sources | SEC filing/XBRL, macro vintages, COT snapshots, and twice-monthly short-interest reports have distinct observation and availability clocks. CFTC announced a planned COT cadence change for year-end 2026. | Record measurement, publication, and ingestion times separately; apply the schedule effective on each date. |

The checked-in 31-record description is assembled from three sources (9 bounded candidates, 14 scoped records, and 8 OptionStrat records), while the current unified CSV contains only 23 rows. The eight OptionStrat requirements remain in their separate JSON register. Do not treat locator coverage as semantic review: all 557 generated family-traceability rows remain marked `NOT_REVIEWED_BY_GENERATOR`.

Relevant curated synthesis in the base snapshot:

- `research/rea-teardowns/synthesis/CONVERGENCE-ENGINE-2026-10-28.md`
- `research/rea-teardowns/synthesis/SECOND-PASS-2026-10-27.md`
- `research/rea-teardowns/synthesis/GESTALT-2026-10-27.md`
- `research/rea-teardowns/synthesis/ACTIVE-FAMILY-SCOPE-LEDGER-2026-10-27.csv`
- `research/rea_teardowns/INDEX.md` and `research/rea_teardowns/targets/`
- `research/saty_mahajan/README.md`, `START_HERE.md`, and `ALGORITHM_SPEC.md`
- separate public-only TheStrat extraction: `public-deeper-pass.md`, `public-pdf-rule-extract.md`, and `alpha-hypotheses.md` in the captured teardown archive

## Multi-repository evidence carried into hypotheses

- **Femto `research/2026-10-20-eyes`:** exploratory, multi-period price/visual and risk-avoid studies; winners, losers, regimes, and matched controls were differentiated. Positive momentum/visual effects were modest and sensitive to regime/costs. Used to include avoid/tail/transition forecasts instead of assuming a buy signal.
- **Femto `research/gestalt-trading-engine-2026-10-26`:** candidate-generation and forecast analyses indicate cost, date clustering, simple baselines, and untouched OOS validation can erase an apparent improvement. Used to require paired baselines and persistent test-family accounting.
- **Femto `research-data` and `research-archive`:** Edge reviews require an edge contract, one minimal variant, paired incumbent comparison, and staged evidence. Used as a validation process only; no Edge implementation or user's desk sleeves were changed.
- **Femto `master-desk` / `desk-state`:** inspected only for research boundaries and summarized inventory. The live/paper desk and state were not modified or imported. Secret-bearing state is not part of this package.
- **TheStrat private teardown:** public rules generate event candidates (gap continuation/reversal, higher-timeframe signal creation, pivot sequence); contradictory trigger references, selected examples, missing historical series, and no established alpha remain explicit limitations. Private/password-protected surfaces were not accessed.

## Third-pass extensions

| New artifact | Traceability contribution |
|---|---|
| `edge_cards.py` | One pre-registered ledger card for each FE01–FE30, with target, incumbent baselines, payer hypothesis, information/risk transfer, adverse state, holdability/co-loss, execution net, decisive comparison, kill rule, and report references. Local source paths are checked by `validate_edge_cards`; all cards remain `HYPOTHESIS`. |
| `diagnostics.py` | Compares only identical symbol/cutoff/target/units/horizon panels; records exact-hash, source-ID, and declared-group overlap; flags duplicate engines, unknown lineage, and cross-cluster directional disagreement. Magnitude medians require forecast and target units to match. Dependency links are conservative evidence-collision warnings, not correlation estimates. |
| `source_clock.py` | Estimates source refresh frequency from matured, rights-approved historical refresh labels, using exact-source history or a same-family fallback only after a sample floor. Returns no point estimate below the floor and never relaxes the original observation/publication/ingestion timestamp gate. |
| `THIRD_PASS_AUDIT.md` | Records architectural lessons from the seven originally supplied GitHub repos plus Vibe-Trading and Edge, Silicon/Femto/desk research boundaries, Saty/TheStrat event definitions, and the distinct mechanism for every engine. |
