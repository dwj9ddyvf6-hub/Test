# OPT_TAIL_STATE: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "OPT_TAIL_STATE", type other, family tail_state. Algorithm grade PARTIAL, unresolved true. Accounting sources: femto land-wt config params. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "OPT_TAIL_STATE" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: femto land-wt config params; alias record sources: ausar_deployed, femto_land_wt
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: none found in any GitHub repo searched (see Provenance); no code is claimed for this canonical id.
- No code for this canonical id was located in any of the four repos searched; searched locations were the full recursive trees of Test, Silicon, quant-research-backup and Midna, by canonical id, alias and distinguishing tokens. This package is graded INCOMPLETE-CODE and nothing was vendored.

## What this strategy is

No strategy description recorded in consulted sources. Type: other; family: tail_state. Universe: not recorded in consulted sources. Asset class: not recorded. Timeframe: not recorded. Creator / source: not recorded. Style evidence in the accounting: Classification 2026-10-30: other (config evidence): Accounting records no entry or exit rule and an empty symbol list for OPT_TAIL_STATE; the name alone does not establish a readable mechanism

## Full algorithm

Not in the record. The accounting records no entry rule, no exit rule and no sizing for OPT_TAIL_STATE, and its classification evidence states the name alone does not establish a readable mechanism. Its recorded parameters hold only an empty symbol list. No algorithm is invented here: the mechanism, universe, timeframe and parameters of this strategy are not in the record.

A similarly named implementation, sleeves/free_opt_tail.py in Test (with its own package docs/FREE_OPT_TAIL-RECREATE.md), exists in this repo, but no evidence on file identifies it as this canonical id's code, so it is NOT claimed as this strategy's code and nothing from it is restated as this strategy's algorithm.

## Files in this repo

- This package: docs/OPT_TAIL_STATE-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): none found in any GitHub repo searched (see Provenance); no code is claimed for this canonical id

## Configuration

Not in the record, beyond the accounting records: symbols [] and status mode=unfunded_monitor, running=False (ausar_deployed); present in roster (femto land-wt).

## Data inputs

Not in the record.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

Behaviour spec: none can be stated from the record. This package is INCOMPLETE-CODE: no code for this canonical id was located in dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup or dwj9ddyvf6-hub/Midna (trees and filename/token searches named in Provenance). It would be settled by the sleeve module docstring or a catalog description for OPT_TAIL_STATE, per the accounting's unresolved note.

## Cure B addendum (2026-10-31, algorithm audit)

Entry rule text carried into this repo from its only source, which is outside Test: the live desk source's contract record FREE_OPT_TAIL_V1 in alpaca-swing-desk/desk/aurelia_free_options.py contracts(), a record that explicitly preserves this canonical id ('preserves': 'OPT_TAIL_STATE', shape 'long_put', legs_required 1, execution 'broker_single'). Quoted verbatim from that record, as recorded in findings-b1-entry of the 2026-10-31 algorithm audit: entry: 'Buy one put when the underlying day return is at or below -3 percent. This source shape is one contract.' The same record gives the exit 'Five sessions or a 50 percent premium loss.' No further entry parameters are stated in that source, in femto-lean/config/options_rules.json (which records only monitor_only=true, an empty symbol list and the input blocker 'separate_frozen_left_tail_and_both_tail_predictors_and_own_IV_increment_required'), or in this package's original record. The ALL-SLEEVES accounting entry for this sleeve was filled with this entry text by cure A; the exit phrase above is quoted here as part of that same external record, and was not graded as a standalone exit rule by the audit (see the NOT FOUND statement below).

NOT FOUND statement (precise, per cure A gaps in docs/ALL-SLEEVES.json): exit NOT FOUND, sizing NOT FOUND, filters NOT FOUND for this canonical id. Searched sources: this RECREATE doc and the Test tree (ALGORITHM docs and name-matched code/card paths), the recursive trees of dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna, the local desks and records (alpaca-swing-desk, muse-desk-v2, femto-lean, research_notes, memory) as recorded in findings b1/b2/b3/b5 of the 2026-10-31 algorithm audit, plus this package's own recorded GitHub searches quoted in Provenance. Entry is the only field sourced from outside Test (the contract record above); nothing else was found anywhere searched, and nothing is invented here.
