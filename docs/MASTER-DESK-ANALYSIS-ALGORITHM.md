# master-desk-analysis

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/analysis/.

The master desk's analysis layer: bars handling, engine score reference, frozen specs (spec/engine_spec.json), job runner, listing, screen, and store modules. It runs analysis jobs against frozen engine specifications and stores their outputs, so an analysis result can be traced back to the exact spec and bar set that produced it.

## Files in this package

- `packages/claude/master-desk-analysis/desk/analysis/__init__.py`
- `packages/claude/master-desk-analysis/desk/analysis/bars.py`
- `packages/claude/master-desk-analysis/desk/analysis/engine_score_ref.py`
- `packages/claude/master-desk-analysis/desk/analysis/frozen.py`
- `packages/claude/master-desk-analysis/desk/analysis/job.py`
- `packages/claude/master-desk-analysis/desk/analysis/listing.py`
- `packages/claude/master-desk-analysis/desk/analysis/screen.py`
- `packages/claude/master-desk-analysis/desk/analysis/spec/engine_spec.json`
- `packages/claude/master-desk-analysis/desk/analysis/store.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
