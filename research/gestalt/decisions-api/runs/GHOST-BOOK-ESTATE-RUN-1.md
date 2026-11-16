# GHOST BOOK ESTATE-WIDE, RUN 1 (Sat 2026-11-14)

Program: Execute Both Brainstorms (W5; Decisions item 6; Unlock
Lever 5). The 2026-11-12 first run priced 21 Tensor fires by hand.
This run consolidates every priced or drafted options expression on
the estate into one viability map: runs/ghost_estate_map_v1.json.

## Map, first edition
- Ghost Book ledger: 21 fires priced (session 2026-11-12 bundle).
  Viable (R to target >= 1.0): 11. Not viable: 10, of which 4 sat at
  R = -1.0 on the first run's record (no defined expression at that
  expiry pays even when the fire is right).
- Expression shadow ledger: 27 drafted expressions (book cards'
  options shadows), status drafted, awaiting outcome grading on
  their own exit rules; viability is graded at resolution, not at
  drafting, so they are counted as the forward population.
- Population by symbol (48 rows): CRDO 4, AXTI 3, EXPD 3, CEG 3,
  ALAB 2, MU 2, RKLB 2, PLTR 2, TSM 2, SMH 2, and 23 symbols at 1.
- Resolution state: 0 of 48 resolved. Ghost expiry is 2026-11-27;
  the harvester (W1) owns resolution from that date.

## The archive gap this run found (named, with its fix)
The Tensor bundle archive keeps only each day's FINAL generation,
and the final generation decays to zero fires as the memo rolls
(bundle-2026-11-13 and bundle-2026-11-14 both archive 0 fires). The
2026-11-12 ghost run was possible only because its builder caught
the first served generation. Estate-wide daily ghost pricing is
therefore impossible from the archive as kept. Fix, registered as
this workstream's next build (dated Mon 2026-11-16, research lane,
no desk-tree edit): a first-generation bundle capture copied at the
session's first serve, feeding the nightly ghost run; the desk is
never edited for it (the capture reads the served file).
Cadence registered: ghost-book-estate-nightly (weekdays), which
prices the day's captured first-generation fires via the book's
expression selector and appends to the map.
STATUS: GREEN for run 1 as scoped (map consolidated on the final
artifacts; the live-population gap is named with its dated fix, not
worked around). EVIDENCE: runs/ghost_estate_map_v1.json;
midna-book/ghost-book-ledger.jsonl; midna-book/GHOST-BOOK.md.
