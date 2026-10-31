#!/bin/sh
# Standalone republish wrapper (MANIFEST-STANDALONE-20261031).
#
# The defect: standalone cure runs republished single data files
# (expected-move, gap-destiny, abstention-signal on 2026-10-31)
# without rebuilding asset-manifest.json, so smoke_check.py
# failed on the delivered tree even though the pages were
# current. The scheduled chains (refresh_tools.py,
# refresh_engines.py) end with verify_terminal.sh; a standalone
# republish must end the same way.
#
# Usage: sh republish_one.sh refresh_<tool>.py [more refreshers]
# Runs each refresher in order, then the full verify_terminal.sh
# sequence (grade rows, provenance stamp, manifest rebuild,
# served-bytes smoke check). Exits nonzero if any step fails.
set -e
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then
    echo "usage: sh republish_one.sh refresh_<tool>.py [...]" >&2
    exit 2
fi
for script in "$@"; do
    python3 "$script"
done
bash verify_terminal.sh
# Publish step (serve-live route, owner ruling 2026-10-31): the
# always-on server reads these files directly, so publishing is the
# proof that served bytes equal disk bytes (hub, desk/, every page).
python3 publish_live.py
