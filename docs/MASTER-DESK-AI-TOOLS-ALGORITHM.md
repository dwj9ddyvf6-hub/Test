# master-desk-ai-tools

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/ai/.

The master desk's AI tool layer: a tool registry and worksheet for the desk's AI assistants, with context tools, forecast tools, odds tools, strip tools, source handling, evaluation helpers (evalh.py), and gates that bound what the tools may do. It is the callable surface the desk's AI workflows use to read desk context and produce worksheet output under the same gating discipline as the rest of the desk.

## Files in this package

- `packages/claude/master-desk-ai-tools/desk/ai/__init__.py`
- `packages/claude/master-desk-ai-tools/desk/ai/__main__.py`
- `packages/claude/master-desk-ai-tools/desk/ai/context_tools.py`
- `packages/claude/master-desk-ai-tools/desk/ai/ctx_rows.py`
- `packages/claude/master-desk-ai-tools/desk/ai/evalh.py`
- `packages/claude/master-desk-ai-tools/desk/ai/forecast_tools.py`
- `packages/claude/master-desk-ai-tools/desk/ai/gates.py`
- `packages/claude/master-desk-ai-tools/desk/ai/odds_tools.py`
- `packages/claude/master-desk-ai-tools/desk/ai/source.py`
- `packages/claude/master-desk-ai-tools/desk/ai/strip_tools.py`
- `packages/claude/master-desk-ai-tools/desk/ai/tools.py`
- `packages/claude/master-desk-ai-tools/desk/ai/worksheet.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
