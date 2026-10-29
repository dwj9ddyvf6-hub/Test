# master-desk-terminal-builder

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, paths desk/terminal/ and web/terminal/.

The master desk's terminal builder: the Python builder modules (board, calls, cautions, coherence, context, dash, deskview, distill, engine, fear, funnel, gates, lector, ledger, lod, market, odds, optnews and more) that assemble the desk terminal's pages and data, plus the web/terminal/ front-end assets (viz.css, viz.js and pages) they emit. The builder reads desk state and ledger data and renders the terminal surfaces; cautions and gates modules carry the honesty and eligibility rules the pages must obey.

## Files in this package

- `packages/claude/master-desk-terminal-builder/desk/terminal/__init__.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/board.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/calls.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/cautions.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/coherence.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/context.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/dash.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/deskview.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/distill.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/engine.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/fear.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/funnel.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/gates.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/lector.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/ledger.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/lod.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/market.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/odds.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/optnews.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/pickcard.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/prices.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/publish.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/ranking.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/__init__.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/call.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/candles.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/candlesticks.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/clx.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/compose.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/core.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/diet.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/divergence.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/elliott.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/formations.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/geometry.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/indicators.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/integrity.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/lenses.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/levels.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/lines.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/momentum.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/optnews.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/patterns.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/pivots.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/plain.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/plan.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/sheet.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/structure.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/ta.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/trend.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/volatility.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/volume.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/waves.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/words.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/wyckoff.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/read/wyckoff_phase.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/reads.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/record.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/strip.py`
- `packages/claude/master-desk-terminal-builder/desk/terminal/vendor_ext.py`
- `packages/claude/master-desk-terminal-builder/web/terminal/app.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/app.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/brief.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/brief.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/context.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/context.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/desk.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/desk.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/engine.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/engine.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/favicon.svg`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/edition.closed.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/edition.empty.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/edition.first.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/edition.full.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/edition.partial.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-A.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-C.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-E.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-G.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-M.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-N.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-P.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-S.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-X.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/fixtures/reads-index.json`
- `packages/claude/master-desk-terminal-builder/web/terminal/funnel.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/funnel.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/gates.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/gates.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/heur.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/heur.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/index.html`
- `packages/claude/master-desk-terminal-builder/web/terminal/manifest.webmanifest`
- `packages/claude/master-desk-terminal-builder/web/terminal/market.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/market.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/record.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/record.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/strip.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/strip.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/vendor.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/vendor.js`
- `packages/claude/master-desk-terminal-builder/web/terminal/viz.css`
- `packages/claude/master-desk-terminal-builder/web/terminal/viz.js`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.

## Sanitization note

This copy was sanitized at 4 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/terminal/ and web/terminal/ is the verbatim source.
Sanitized files in this package (non-verbatim copies):
- packages/claude/master-desk-terminal-builder/desk/terminal/deskview.py: 2 occurrence(s) replaced
- packages/claude/master-desk-terminal-builder/desk/terminal/lector.py: 1 occurrence(s) replaced
- packages/claude/master-desk-terminal-builder/desk/terminal/read/waves.py: 1 occurrence(s) replaced
