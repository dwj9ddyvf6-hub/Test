# Terminal chart cures — PROGRESS (2026-10-31)

## SCOPE (written before editing, per InfinityBlade)

- Surface (what changes):
  - `site/refresh_agentdebate.py`, `site/refresh_echoboard.py`,
    `site/refresh_second_opinion.py`: each generator adds ONE new
    top-level `counts` dict, derived in-code from the exact record
    values it already assembles (no new source, no new numbers).
    This is the sibling pattern used by flow-tape and state-analogue:
    `record_surface.build_record_surface` turns a top-level `counts`
    dict into `record_surface.live_accrual.counts`, and
    `page_charts.js` draws it as SVG `countBars` both as the page
    lead (`genericLead` -> `countRows`) and in the record section
    (`recordSection`, `#recordChart`).
  - The three pages' `data.json`, regenerated through the normal
    lane path: bare refreshers first (they strip
    `record_surface`/`explanation`), then the lane close
    `enrich_all.py` (record_surface first, explanation second),
    which restores both enrichments.
  - Regression blockers added to
    `forecast/tests/test_charts_ia_20261031.py`: one test per page.
  - This PROGRESS.md only, in the program home.

- Constraints (what stays untouched):
  - No existing data value changes: `counts` values are copies/sums
    of values already in each page's own record (verified by the
    blockers recomputing them from the record itself).
  - Collapsed explanation summary lines unchanged (they come from
    each page's own job line in index.html); explanation bodies gain
    only the producer's own live-counts sentence, exactly as on
    healthy sibling pages.
  - No index.html, page_charts.js, visual.js, record_surface.py or
    explanation.py edits. No other page touched.
  - Charts draw ONLY values present in each page's own record.

- Outcome (observable success): each of agent-debate, echo-board and
  second-opinion renders a drawn SVG count-bars chart as its lead
  and a `#recordChart` "The record" section, with bar values equal
  to its data.json counts, and keeps all existing content.

- Proof: new blockers fail on the pre-cure data (no `counts`, no
  live_accrual counts) and pass after; a node render of the real
  `page_charts.js` record/lead logic (jsdom-free harness driving
  VisualKit + page_charts functions is not exported, so proof is:
  blockers assert data + generator source + record_surface accrual,
  plus a headless render check if available); full terminal-lineup
  test suite run and recorded below.

- Edges: zero counts (QQQ rising 0, six-families 0) are kept in
  `counts` for honesty; the chart renderer itself skips non-positive
  rows, as it does on every sibling page. Banned-word gates in the
  generators scan the whole assembled blob, so count keys use only
  plain reader words.

## Series charted (all from each page's own record)

- agent-debate (`counts`, from `funds[].count_rising/count_falling`):
  spy_readings_pointing_to_rising, spy_readings_pointing_to_falling,
  qqq_readings_pointing_to_rising, qqq_readings_pointing_to_falling,
  iwm_readings_pointing_to_rising, iwm_readings_pointing_to_falling.
  Current values: SPY 1/5, QQQ 0/6, IWM 1/5.
- echo-board (`counts`, from its `coverage` distribution):
  names_covered_by_six_families, names_covered_by_five_families,
  names_covered_by_four_families, names_covered_by_three_families,
  names_covered_by_two_families, names_covered_by_one_family,
  names_covered_by_no_family. Current: 0, 23, 22, 4, 53, 1731, 5.
- second-opinion (`counts`, from its `coverage` distribution):
  same seven coverage keys as echo-board, from its own coverage
  block. Current: 0, 23, 22, 4, 53, 1731, 5.

Chart kind for all three: SVG horizontal count bars (VisualKit
countBars), lead chart plus record-section chart, same as flow-tape
and state-analogue.

## Status log

- SCOPE written, generators and enrichment wiring read
  (record_surface.py, explanation.py, enrich_all.py, lane_run.py,
  page_charts.js, visual.js countBars).
- Generators cured: each of the three refreshers now emits the
  top-level `counts` block described above, derived in-code from
  its own assembled record.
- Blockers added to forecast/tests/test_charts_ia_20261031.py:
  test_agent_debate_record_chart_from_own_counts,
  test_echo_board_record_chart_from_own_counts,
  test_second_opinion_record_chart_from_own_counts. FAIL-FIRST
  proven: all 3 failed on the pre-cure data.json files; all pass
  on the final tree (file total 8 passed).
- Regeneration through the normal lane path: bare refreshers
  (second-opinion, then echo-board, then agent-debate), then
  tape_family_run.py (the tape lane producer; restores agent-debate's
  tape_freshness stamp, state "current", tape session 2026-10-30,
  all 9 consumers current), then the lane close enrich_all.py
  (100 pages enriched, no failures), which restored record_surface
  and explanation on every page. Collapsed explanation summaries
  unchanged; bodies gained only the producer's live-counts sentence.
  One intermediate failure (test_automations_cures agent-debate
  tape parity, KeyError tape_freshness after the bare refresh) was
  cured by this lane step and now passes.
- Rendered proof on the FINAL tree (Playwright over HTTP, local
  server): each of the three pages renders #chartLead with 1 SVG
  (agent-debate 5 rects; echo-board 7; second-opinion 7) and
  #recordChart with 1 SVG (5, 6 and 6 rects respectively; zero
  counts are skipped by the renderer as on all sibling pages),
  bar labels/values matching data.json counts (6/5/5/1 for
  agent-debate; 1731/53/23/22 for echo-board and second-opinion),
  and the explanation details block present and closed.
- Full terminal-lineup suite (forecast/tests, 72 files, run
  file-by-file after two monolithic runs were killed in this
  memory-tight environment): 661 passed, 21 failed, 57 of 72 files
  fully green. Relevant files all green: charts_ia (8, incl. the 3
  new blockers), explanation (5), record_surface (3), liveness (6),
  automations_cures (17). The 21 failures sit in 13 files in areas
  this cure does not touch (hub count pins expecting 100 vs the
  current 102, per-name collector bound 103 vs 60, psychology
  "percentile None" HTML, gap-fill date pin 2026-10-29 vs current
  2026-10-30, shared CSS token pins, desk emdash, corrected-band
  guard, chain collector, engine19/20 and proving-ground record
  checks, MCP provenance for market-mood, second-opinion prints
  count 102 vs a stale 52 pin that already read 102 in the pre-cure
  file) and are recorded as PRE-EXISTING, not cured here and not
  caused here. Two deep-panel files
  (test_deep_panel_20261029.py, test_deep_panel_expansion_20261029.py)
  were OOM-killed (exit 137) repeatedly in this environment and are
  UNVERIFIED here; they exercise the deep bar panel, untouched by
  this cure.

## Verdict: PARTIAL

The three named defects are cured and proven on the final rendered
tree (GREEN for the three pages, per the render and blocker proof
above). The overall suite is PARTIAL only because of the named
pre-existing failures and the two OOM-unverified deep-panel files,
none of which this program's scope covers.
