# Capability matrix — v0.4.1

| Capability | Implemented algorithm | Prerequisites and abstention |
|---|---|---|
| Policy language | Small English lexicon, three-token negation | Fed RSS title; directional match absent -> unknown |
| News tone | FRBSF index import through CSV adapter | Required date and named sentiment column; acquisition timestamp does not establish historical publication |
| Topic attention | Wikimedia daily user pageview counts | Fixed validated article/population; completed UTC day; no direction inference |
| Option-implied risk | Cboe VIX close adapter | Required CSV fields; no survey-of-beliefs interpretation |
| Attention acceleration | Last three vs prior three mean; watch at +50% | Six ordered values, freshest within source TTL, adjacent gaps <=72h, positive denominator |
| Stress persistence | Three consecutive observed VIX closes >=25 | Three observations, <=72h gaps, fresh latest value |
| Source disagreement | Opposing signs, common units, distinct source families | At least two nonduplicated sources within 48h and own TTL; declared families are not proven independent |
| Sentiment-price divergence | Three aligned event timestamps; sentiment change vs summed price return | Explicit decimal_return imports and sentiment series; no fabricated prices |
| Narrative concentration | Not implemented | Complete topic shares, taxonomy version and denominator required; explicit abstention |
| Proxy forecast | Persistence and mean last four first differences | Five ordered values with fresh endpoint; next-observation target, not a probability |
| Proxy walk-forward scoring | Reconstruct available vintages at observation times, score first later observed target | Multiple knowledge vintages; backfilled single-vintage archive -> no score |
| Return evaluation | Fixed ridge, price-only and sentiment-added models, zero/mean baselines | Explicit label availability, one entity/horizon, nonoverlapping windows, audited features, gap-aware costs |
| Latent state model / calibrated probabilities | Research candidate | Not estimated or production-validated |
| Individual mind reading / trade execution | Not implemented | Outside system purpose; Tensor owns entry timing |

The complete 16-card registry and 50-source registry are integrated under research_companion with verified original checksums. Four descriptive detectors are implemented; the 16 richer research hypotheses remain unvalidated candidates, not 16 implemented trading algorithms. See PATTERN_CAPABILITIES.md for the per-card distinction.

Operational additions: strict managed-policy preflight, read-only health, verified online backup, bounded scheduled permission gate, inactive source-specific service/timer templates, and checksum-verified offline receipt import are implemented. No daemon has been activated, no outbound collector has been validated in this environment, and templates do not confer source rights or a production SLA.
