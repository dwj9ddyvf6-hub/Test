# master/: what lives here

The mirrored Master Terminal edition: the combined terminal's Master half as published web assets (content-hashed JS and CSS) plus its live data files (deskview.json, edition.json, market.json, pulse.json, sleeves.json, positions.json, charts.json, panels.json, publish-manifest.json). Reached from the repository front door, index.html.

Files here: 75 including this entry doc (count at the index commit named in INDEX.md).

All 74 data and asset files sit at the top of this folder; this entry doc makes 75. The human entry point is the repository front door, index.html at the root. The data files (deskview.json, edition.json, market.json, pulse.json, sleeves.json, positions.json, charts.json, panels.json, publish-manifest.json) are the ones a reader usually wants; the hashed JS and CSS files are the published app assets and rotate per edition.

## Where its index lives

- Every file in this area is listed, with size and blob sha, in the root INDEX.json (search it by the path prefix `master/`).
- The prose map is the root INDEX.md; the mandatory first read is the root START-HERE.md; routing by topic is the root ROADMAP.md.
