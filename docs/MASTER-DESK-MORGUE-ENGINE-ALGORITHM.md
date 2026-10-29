# master-desk-morgue-engine

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/morgue/.

The master desk's morgue engine: the cycle that collects and boards dead or dormant strategy material, with board and board-card rendering, board features, edition handling, fetch/flow modules, and instrument loaders (including 13F institution data). It runs the morgue cycle (fetch, flow, board) and publishes board cards summarizing each boarded item's state, keeping retired material inspectable instead of deleted.

## Files in this package

- `packages/claude/master-desk-morgue-engine/desk/morgue/__init__.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/board.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/board_card.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/board_features.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/bs.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/cycle.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/edition.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/ext2.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/fetch.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/flow.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/flow_card.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/inst_13f.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/inst_bundle.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/inst_edgar.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/inst_short.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/lanes/__init__.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/lanes/chain_archive.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/lanes/finra_shortvol.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/lanes/sec_facts.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/ledger.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/map_dix.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/map_gex.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/opt_ext.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/routes.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/scorecards.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/sectors.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/squeeze.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/studies.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/studies_card.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/studies_feed.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/tape.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/tape_card.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/vendor_check.py`
- `packages/claude/master-desk-morgue-engine/desk/morgue/wall_study.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
