# Independent verification — terminal chart cures (2026-10-31)

Method: site served over HTTP (port 8766 was not running; served
`terminal-lineup/site` on scratch port 8791), each page loaded in
Chromium (Playwright) at 1280x900 viewport. Record-section DOM
(`#recordChart`) inspected for SVG/rect counts and plotted values;
values compared against the page's own `data.json` `counts` (which
equal `record_surface.live_accrual.counts`). Explanation checked as
the page's `<details>` block: present and `open == false`.
Screenshots: `verify_agent-debate.png`, `verify_echo-board.png`,
`verify_second-opinion.png` in this program home (viewport
1280x900, readable; agent-debate shot shows the lead count-bars
chart with values 6/5/5/1/1 and the collapsed explanation line).

## agent-debate — GREEN

- `#recordChart`: 1 SVG, 5 rects. Plotted values in order:
  QQQ falling 6, IWM falling 5, SPY falling 5, IWM rising 1,
  SPY rising 1.
- data.json counts: SPY rising 1 / falling 5, QQQ rising 0 /
  falling 6, IWM rising 1 / falling 5. All positive counts match
  exactly; the zero count (QQQ rising 0) is skipped by the
  renderer, as on sibling pages. No mismatch.
- Lead `#chartLead`: 1 SVG, 5 rects, same values.
- Explanation `<details>` present, closed. Session 2026-10-30.

## echo-board — GREEN

- `#recordChart`: 1 SVG, 6 rects. Plotted values: one family
  1731, two families 53, five families 23, four families 22,
  no family 5, three families 4.
- data.json counts: six 0, five 23, four 22, three 4, two 53,
  one 1731, none 5. All positive counts match exactly; the zero
  count (six families 0) is skipped by the renderer. No mismatch.
- Lead `#chartLead`: 1 SVG, 7 rects (adds "Names on record 1838").
- Explanation `<details>` present, closed.

## second-opinion — GREEN

- `#recordChart`: 1 SVG, 6 rects. Plotted values identical in
  kind to echo-board: 1731, 53, 23, 22, 5, 4.
- data.json counts: six 0, five 23, four 22, three 4, two 53,
  one 1731, none 5, recomputed from its own names. All positive
  counts match exactly; zero count skipped by the renderer.
  No mismatch.
- Lead `#chartLead`: 1 SVG, 7 rects.
- Explanation `<details>` present, closed.

## Test suite re-run (verifier, this pass)

- `test_charts_ia_20261031.py`: 8 passed, including the three new
  blockers (agent-debate, echo-board, second-opinion record
  charts from own counts).
- `test_explanation_20261031.py` run together with the above:
  12 passed, 1 failed. The one failure is
  `test_every_hub_page_has_a_unique_substantive_explanation`
  failing on **earnings-calendar** ("no explanation block") — a
  page outside this cure's three-page scope; the three cured
  pages each carry their explanation block (proven over HTTP
  above). This differs from the cure report's "explanation 5
  passed" line and is named here as an out-of-scope open item,
  not a defect in the three cured pages.

## Overall verdict

All three named defects are cured and independently proven on
the final rendered tree over HTTP: **GREEN** for agent-debate,
echo-board and second-opinion. One out-of-scope suite failure
(earnings-calendar explanation block) is named above.
