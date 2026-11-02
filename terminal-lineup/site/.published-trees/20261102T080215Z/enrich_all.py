#!/usr/bin/env python3
"""Run the record-surface producer over every hub page.

Wired into refresh_engines.py and refresh_tools.py before their verify
step, so regeneration preserves the record_surface block every page
carries. Pages with no data.json (greeks-sketch, payoff-sketch) are
named, never silently skipped.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import explanation  # noqa: E402
import record_surface  # noqa: E402


def hub_slugs():
    hub = (HERE / "index.html").read_text()
    return sorted(set(re.findall(r'href="([a-z0-9\-]+)/"', hub)))


def main():
    enriched, no_data, failed = [], [], []
    for slug in hub_slugs():
        path = HERE / slug / "data.json"
        if not path.exists():
            no_data.append(slug)
            continue
        try:
            record_surface.enrich_file(path)
            # Explanation runs second: its tool text reads the
            # record_surface block the first step just wrote.
            explanation.enrich_file(path)
            enriched.append(slug)
        except Exception as exc:  # name it, keep going
            failed.append(f"{slug}: {exc}")
    print(f"record-surface: enriched {len(enriched)} pages; "
          f"no data.json: {', '.join(no_data) or 'none'}; "
          f"failures: {'; '.join(failed) or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
