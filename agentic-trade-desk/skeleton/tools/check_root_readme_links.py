#!/usr/bin/env python3
"""Check the exact root README guide block and its four local targets.

Usage: python3 check_root_readme_links.py [README.md]
The canonical block is docs/README_FIXED_SECTION.md beside the selected README.
This checks the source-library front page; check_onboarding.py checks the separate
standalone desk skeleton without depending on its parent repository.
"""
from pathlib import Path
import re
import sys

START = "<!-- BEGIN FIXED SECTION: agent guides."
END = "<!-- END FIXED SECTION -->"
TARGETS = (
    "docs/THREE-GUIDES-RECONCILIATION.md",
    "docs/AGENTIC-TRADE-DESK-GUIDE.md",
    "agentic-trade-desk/README.md",
    "docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md",
)


def extract_block(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Expected exactly one guide-block start and end marker")
    start, end = text.index(START), text.index(END)
    if end <= start:
        raise ValueError("Guide-block markers are out of order")
    return text[start:end + len(END)]


def check(readme):
    root = readme.resolve().parent
    try:
        text = readme.read_text(encoding="utf-8")
        source = (root / "docs/README_FIXED_SECTION.md").read_text(encoding="utf-8")
        actual, expected = extract_block(text), extract_block(source)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    errors = []
    if actual != expected:
        errors.append("README guide block differs from docs/README_FIXED_SECTION.md")
    links = set(re.findall(r"\]\(([^)]+)\)", actual))
    for target in TARGETS:
        if target not in links:
            errors.append("Missing guide link in fixed block: " + target)
        if not (root / target).is_file():
            errors.append("Guide target does not exist: " + target)
    return errors


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("Usage: check_root_readme_links.py [README.md]", file=sys.stderr)
        return 2
    errors = check(Path(args[0] if args else "README.md"))
    print("OK: exact guide block and all four targets" if not errors else "FAIL: " + "; ".join(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
