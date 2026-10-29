# REA register-builder scripts

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch main, research/rea_teardowns/scripts/.

The Node (.mjs) builder and verifier scripts for the REA teardown corpus registers. The builders read the corpus synthesis CSV/JSON inputs and write derived registers: candidate requirement register, corpus file index, corpus gap matrix, funnel profile ledger, mirror family name triage, requirement traceability, scope ledger, scoped requirement index, unified requirement index, and vault structure index, sharing csv_utils.mjs for CSV parse/serialize. The verifiers check mirror bundle parts and oversize evidence shards. capture_public_rechecks.ps1 captures public recheck evidence from PowerShell.

## Files in this package

- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_candidate_requirement_register.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_corpus_file_index.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_corpus_gap_matrix.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_funnel_profile_ledger.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_mirror_family_name_triage.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_requirement_traceability.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_scope_ledger.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_scoped_requirement_index.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_unified_requirement_index.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/build_vault_structure_index.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/capture_public_rechecks.ps1`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/csv_utils.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/verify_mirror_bundle_parts.mjs`
- `packages/ausar/rea-register-builder-scripts/research/rea_teardowns/scripts/verify_oversize_evidence_shards.mjs`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
