# Psychology Engine evidence report

As of: 2026-10-28T12:00:00+00:00
Entity: US_MARKET; horizon: 1d

Research advisory only. Tensor retains entry timing authority. Predictive validation is not established.

| Dimension | Measures | Declared source families |
|---|---|---|
| sentiment | {"balance": 0.15} | 2 |
| attention | UNKNOWN | 0 |
| uncertainty | UNKNOWN | 0 |
| disagreement | UNKNOWN | 0 |
| positioning | UNKNOWN | 0 |
| stress | {"VIX_index_points": 23.4} | 1 |
| narrative_change | UNKNOWN | 0 |

Included observations: 3; excluded: 2.
Decision: review_evidence. No order interface is implemented.

VIX measures option-implied risk, not surveyed beliefs. Fed text measures institutional language, not investor consensus. Family counts are provenance counts, not statistical independence guarantees.

## Evidence

- risk_proxy / vix / revision 1: stress=23.4 VIX_index_points; published 2026-10-28T12:00:00+00:00; first seen 2026-10-28T12:00:00+00:00.
- survey_a / week1 / revision 1: sentiment=0.5 balance; published 2026-10-28T12:00:00+00:00; first seen 2026-10-28T12:00:00+00:00.
- survey_b / survey2 / revision 1: sentiment=-0.2 balance; published 2026-10-28T12:00:00+00:00; first seen 2026-10-28T12:00:00+00:00.
- Excluded search (36c8a7066bfc41c7ead95b41b4b2832f077cf857e153b30fd0e98d096ecf9506): unknown_value.
- Excluded old_survey (ef910468c383232f489c0300a18cd877b402d7046e629e5d9bcd9f20dabcda47): stale.

