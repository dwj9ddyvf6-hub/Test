"""Best Setups lane (v3 integration, NOT vendored code).

Integrates the vendored Best Setups exactly as the current desk does:
tools/run_live.publish_feed -> core.setups_publish
merge_setups_into_snapshot extends the desk-terminal snapshot with the
curator's setups. The vendored package is also named `core`, which
collides with v3's own core package, so the merge runs in a subprocess
rooted at best_setups/ (isolation the current desk's fail-soft publish
path also relies on). The vendored tree is never modified.
"""
import json, subprocess, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent / "best_setups"

TERMINAL_KEYS = ("setups", "entered_setups", "setups_completed",
                 "considered", "market_context", "scoring_method",
                 "lector_top", "lector_as_of", "setups_as_of", "notes",
                 "departures", "pullback_as_of", "pullback_counts",
                 "pullback_near", "pullback_top")

_DRIVER = (
    "import sys, json\n"
    "sys.path[:] = [p for p in sys.path if p not in ('', '.')]\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from core import setups_publish\n"
    "snap, sd, bd = (json.loads(x) for x in sys.stdin.read().split('\\n', 2))\n"
    "out = setups_publish.merge_setups_into_snapshot(snap, sd, bd)\n"
    "sys.stdout.write(json.dumps(out, sort_keys=True, default=str))\n"
)


def enrich_terminal_snapshot(snapshot, setups_doc, briefs_doc=None):
    """Same inputs in, same outputs consumed as the current desk."""
    payload = "\n".join(json.dumps(x, default=str) for x in
                        (snapshot, setups_doc, briefs_doc))
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(_ROOT)],
                       input=payload, capture_output=True, text=True, cwd=str(_ROOT))
    if r.returncode != 0:
        raise RuntimeError(f"best_setups lane failed: {r.stderr[:400]}")
    return json.loads(r.stdout)
