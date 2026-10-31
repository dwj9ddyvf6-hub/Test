# Evidence-Class Column — Binding Format for Any Future Aggregation

Provenance: Adopted 2026-10-28 by the owner's order, evaluation 05-EVALUATION.md section 7 item 9 and section 3 (scoped requirement rows), and 04-TARGETS-REVIEW.md cross-cutting finding 3 and open item 2.
Source: Codex's scoped requirement register, adopted ONLY with this column added. The register is adopted into our work queue in this labelled form; scoped row counts are never coverage (see ADOPTED-STANDARDS.md section 6).

## The column

Every family row in any future aggregation of scoped requirements must carry an `evidence_class` value from exactly this set, built from the target file's own status lines:

| evidence_class | Meaning |
|---|---|
| source-pinned | An exact public source artifact is pinned by blob or tag and audited against it. |
| docs-rich | Rich public documentation supports detailed semantics; no pinned source artifact and no runtime observation. |
| docs-only | Public documents or pages only, thinner than docs-rich; no artifact, no runtime. |
| boundary-only | No inspectable artifact; the work is boundary, conflict, and unknown mapping around an empty core. |
| rights-gate | Terms or EULA gate the family: the correct outcome is a hold / do-not-build row, not a recreation spec. |

Depth signals must differ by family: two families with the same scoped-row count but different evidence classes do not carry the same depth, and no aggregation may sum rows across classes as a coverage total without showing the class split.

## Ten named families classified (from the review)

| Family | evidence_class | Basis in the review (04-TARGETS-REVIEW.md) |
|---|---|---|
| Zerith MACD Martingale Grid v2.20 | source-pinned | Blob 5ad3bcbcef... exactly matches the 1,043-line local snapshot; section 1, strongest in the lane. |
| DeepSeek News Grid Scalper V2 | source-pinned | Source pinned at tag v2.0.0, EA blob c3bbb4c515...; section 2. |
| Stock Rover | docs-rich | 24 numbered, sourced recheck items; rich public docs; section 6. Status downgraded by its own deepening to a bounded public-source semantic slice. |
| Simply Wall St | docs-rich | One genuinely open public specification (CC BY-NC-SA model) mined into reusable semantics; section 5. |
| Nansen | docs-rich | Strong documentation substance, endpoint and credit detail; no runtime backing and none claimed; section 3. |
| Kobeissi Letter | docs-only | Prices and headline re-confirmed only; the 2025 PDF did not render; the +516% composite stays publisher-reported and unrecalculated; section 8. |
| AlgoBars | docs-only | Dated change-detection and conflict preservation from public pages; no script compiled or run; section 7. |
| GainzAlgo | boundary-only | No inspectable artifact at all; mechanism 100% UNKNOWN; +24 templated rows for an empty core; section 9. Named in the task and in evaluation section 7 item 9 as the boundary-only exemplar. |
| Arkham Intelligence | rights-gate | Public SaaS terms exclude bots/AI/ML and bar competing-vendor access while a hosted MCP is marketed; carried as an unresolved rights conflict; section 4. Named in the task as rights-gate. |
| SpotGamma | rights-gate | Terms restrict reverse engineering, systematic collection, automated access and competing use absent written authorization; disposition is an explicit hold, +1 scoped row; section 10. Trade Ideas is the same class (section 11, EULA, +1 row). |

## Binding rule

Any future register, scoreboard, or aggregation produced for the lineup that uses scoped requirement rows must include this column, populated from the target files' own status lines, and must report the GAP share alongside any row count (683 of 735 scoped rows in Codex's register are explicit GAPs, per evaluation section 3).
