# Tenth Pass — Collision Diagnostic Semantics

## Defect isolated

The ninth pass correctly changed heuristic risk engines to `RISK_RANK_ONLY`, but the collision-map status still returned `direction_only_forecast_units_differ` whenever forecast and outcome units differed. For a risk-rank panel, that status claimed directional information the record deliberately does not emit. The same branch could label an all-abstention or non-directional panel as direction-only.

## Precision change

- Cluster summaries are now named `cluster_score_orientation_categories` and `cross_cluster_score_orientation_entropy`.
- Categories distinguish `positive_score`, `negative_score`, and `neutral_score` from `unknown` and `mixed`.
- `score_orientation_available` states whether any cluster has a meaningful signed orientation.
- Unit-mismatched panels now report `risk_rank_only_units_differ`, `score_orientation_only_units_differ`, or `no_score_orientation_units_differ` according to the actual output semantics. They never imply that ranks or abstentions carry directional information.
- Collision-map output schema advances to `1.3`; direction semantics remain part of the comparison key, and old `UP`/`DOWN`/risk labels remain recognized as legacy score orientations.

Magnitude medians remain restricted to matching forecast and target units, with duplicate engine records suppressing aggregation. Entropy remains descriptive score-sign agreement, not forecast accuracy. This pass changes diagnostic naming and status classification only; it does not alter any model score, target, label, or trading behavior.
