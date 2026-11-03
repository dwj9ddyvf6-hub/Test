#!/usr/bin/env python3
"""Build grok-index.json: the finder index (SPEC C18) over our real
pages, from each page's own title and explanation line. Also computes
C15 is_new by diffing the slug set against the previous generation of
this file: on the first generation no badges are emitted (honest).
Run from anywhere; writes beside itself. Presentation only."""
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent
OUT = SITE / "grok-index.json"

GROUPS = [
    ("forecast", "Forecast Engines"),
    ("market", "Market Tools"),
    ("record", "The Record"),
    ("tool", "Tools"),
]


def group_of(slug: str, data: dict) -> str:
    tool = str(data.get("tool") or "")
    if "forecast" in tool:
        return "Forecast Engines"
    if slug in ("record", "horizon-grades", "calibration-league", "receipts"):
        return "The Record"
    return "Tools"


def main() -> int:
    prev = set()
    if OUT.exists():
        try:
            prev = {e["href"] for e in json.loads(OUT.read_text())}
        except Exception:
            prev = set()
    entries = []
    for page in sorted(SITE.glob("*/index.html")):
        slug = page.parent.name
        html = page.read_text(errors="ignore")
        m = re.search(r"<title>([^<]+)</title>", html)
        name = (m.group(1).split(":")[0].strip() if m else slug)
        desc = ""
        dj = page.parent / "data.json"
        if dj.exists():
            try:
                data = json.loads(dj.read_text())
                exp = data.get("explanation") or {}
                desc = (exp.get("summary") or "")[:140]
                grp = group_of(slug, data)
            except Exception:
                grp = "Tools"
        else:
            grp = "Tools"
        href = f"{slug}/"
        entries.append({
            "name": name, "desc": desc, "group": grp, "href": href,
            "is_new": bool(prev) and href not in prev,
        })
    OUT.write_text(json.dumps(entries, indent=1))
    print(f"grok-index: {len(entries)} pages, "
          f"{sum(1 for e in entries if e['is_new'])} new vs prior generation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
