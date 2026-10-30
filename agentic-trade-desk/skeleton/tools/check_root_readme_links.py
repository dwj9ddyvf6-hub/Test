#!/usr/bin/env python3
"""Fail (exit 1) if a README lacks the two agent-guide links and the fixed-section markers.
Usage: python3 check_root_readme_links.py [README.md]"""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "README.md"
t = open(p, encoding="utf-8").read()
need = ["agentic-trade-desk/README.md", "docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md",
        "BEGIN FIXED SECTION", "END FIXED SECTION"]
missing = [n for n in need if n not in t]
print("OK" if not missing else f"MISSING: {missing}")
sys.exit(1 if missing else 0)
