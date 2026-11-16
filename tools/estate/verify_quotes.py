#!/usr/bin/env python3
"""Verbatim quote-proof gate for contradiction work. ADOPT A4, Obsidian sweep 2026-11-02.

Input is a list of (path, line, quote) triples naming sides of an alleged
contradiction. Each quote must be at least 12 characters and match the cited
line character-for-character. Prints pass or fail per quote with file and
line. Report-only: writes nothing. Stdlib only.
"""
import json, sys
from pathlib import Path

MIN_QUOTE = 12


def verify_one(path, line, quote) -> dict:
    if not isinstance(quote, str) or len(quote) < MIN_QUOTE:
        return {"path": str(path), "line": line, "ok": False,
                "reason": f"quote refused: shorter than {MIN_QUOTE} characters"}
    p = Path(path)
    if not p.is_file():
        return {"path": str(path), "line": line, "ok": False, "reason": "file not found"}
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if not isinstance(line, int) or line < 1 or line > len(lines):
        return {"path": str(path), "line": line, "ok": False,
                "reason": f"line out of range (file has {len(lines)} lines)"}
    actual = lines[line - 1]
    if quote == actual or quote in actual:
        # Exact line match, or the quote is the full cited segment of the line.
        if quote == actual:
            return {"path": str(path), "line": line, "ok": True, "reason": "exact line match"}
        return {"path": str(path), "line": line, "ok": True,
                "reason": "quote matches cited line character-for-character"}
    return {"path": str(path), "line": line, "ok": False,
            "reason": "quote does not match cited line"}


def verify_triples(triples) -> list:
    out = []
    for t in triples:
        if isinstance(t, dict):
            out.append(verify_one(t.get("path"), t.get("line"), t.get("quote")))
        else:
            path, line, quote = t
            out.append(verify_one(path, line, quote))
    return out


def main(argv) -> int:
    if len(argv) == 2:
        triples = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    elif len(argv) == 4:
        triples = [{"path": argv[1], "line": int(argv[2]), "quote": argv[3]}]
    else:
        print(__doc__); print("usage: verify_quotes.py <triples.json> | <path> <line> <quote>")
        return 2
    results = verify_triples(triples)
    all_ok = True
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            all_ok = False
        print(f"{status} {r['path']}:{r['line']} ({r['reason']})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
