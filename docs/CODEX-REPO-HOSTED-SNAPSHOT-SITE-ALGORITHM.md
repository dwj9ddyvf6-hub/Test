# Codex repo hosted snapshot site

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Codex branch main (repo root).

A public, read-only paper terminal hosted from the Codex repo via GitHub Pages (.github/workflows/pages.yml deploys dist/ on pushes). The static page (dist/index.html, app.js, styles.css) polls its published snapshot dist/data/desk-snapshot.json every 30 seconds and labels it with observation time and age, showing market context, open paper positions, and currency-separated book equity and P/L with stable Paper book NN aliases in place of internal book IDs. tools/refresh-desk-snapshot.py is the exporter: it reads only loopback desk endpoints, refuses to update unless the configured release README confirms the desk identity, selects numeric and accounting fields from the read-only paper projection, never copies raw IDs or account names, groups money by currency, and writes the public artifact atomically. The page makes no live-trading or profitability claim, and stale snapshots are marked stale rather than presented as live.

## Files in this package

- `packages/ausar/codex-repo-hosted-snapshot-site/.gitignore`
- `packages/ausar/codex-repo-hosted-snapshot-site/README.md`
- `packages/ausar/codex-repo-hosted-snapshot-site/.github/workflows/pages.yml`
- `packages/ausar/codex-repo-hosted-snapshot-site/.openai/hosting.json`
- `packages/ausar/codex-repo-hosted-snapshot-site/dist/app.js`
- `packages/ausar/codex-repo-hosted-snapshot-site/dist/favicon.svg`
- `packages/ausar/codex-repo-hosted-snapshot-site/dist/index.html`
- `packages/ausar/codex-repo-hosted-snapshot-site/dist/styles.css`
- `packages/ausar/codex-repo-hosted-snapshot-site/dist/data/desk-snapshot.json`
- `packages/ausar/codex-repo-hosted-snapshot-site/tools/refresh-desk-snapshot.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
