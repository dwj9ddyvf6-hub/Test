#!/usr/bin/env python3
"""Freshness lint for the operational registers. ADOPT A3, Obsidian sweep 2026-11-02.

Report-only, stdlib only. Behaviour over STATE.md and CONTEXT-SNAPSHOT.md
(actual register locations: ~/workspace/midna-book/memory/STATE.md and
~/workspace/midna-book/CONTEXT-SNAPSHOT.md):
- FRESH-1 (error): a present-tense quantitative claim about a volatile noun
  (counts, balances, statuses, roster sizes) outside a dated container and
  without a proof timestamp.
- FRESH-2 (warning): a stamp older than its window (STATE.md program rows,
  7 days; snapshot age, 36 hours). Each aged stamp must be answered in the
  register as re-observe, convert, or retire.
- FRESH-3 (error): a pointer or proof path that does not resolve.
- Due claims: lines carrying `asserts-current-behavior: true` with
  `verified: YYYY-MM-DD`; due means never verified or older than 90 days.
  The due list is computed from those fields; no stale flag is stored.
Writes nothing.
"""
import re, sys
from datetime import date, datetime, timedelta
from pathlib import Path

VOLATILE = re.compile(r'\b(count|counts|balance|balances|status|roster|positions?|'
                      r'equity|cash|sleeves?|programs?|files|rows|entries|defects?)\b', re.I)
NUMBER = re.compile(r'(\$\s?\d|\b\d[\d,]*(?:\.\d+)?\b)')
DATE_RE = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
PATH_RE = re.compile(r'(~/[\w./+-]+|/[\w./+-]+\.(?:md|json|py|sh|txt)|[\w.-]+/[\w./+-]+\.(?:md|json|py|sh|txt))')
STATE_WINDOW_DAYS = 7
SNAPSHOT_WINDOW_HOURS = 36
DUE_DAYS = 90


def parse_date(s):
    try:
        return date(int(s[0]), int(s[1]), int(s[2]))
    except Exception:
        return None


def lint_file(path: Path, reference: date, kind: str) -> dict:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    findings = {"FRESH-1": [], "FRESH-2": [], "FRESH-3": [], "due": []}
    in_dated_container = False
    for i, line in enumerate(lines, 1):
        if line.startswith("#"):
            m = DATE_RE.search(line)
            in_dated_container = bool(m)
        # FRESH-1
        if NUMBER.search(line) and VOLATILE.search(line):
            has_stamp = bool(DATE_RE.search(line)) or "as of" in line.lower() \
                or "proof" in line.lower()
            if not has_stamp and not in_dated_container:
                findings["FRESH-1"].append(
                    f"{path}:{i}: unstamped quantitative claim: {line.strip()[:100]}")
        # FRESH-3: proof pointers
        if "proof" in line.lower() or line.strip().startswith("- Proof"):
            for m in PATH_RE.finditer(line):
                raw = m.group(1)
                cand = Path(raw).expanduser()
                if not cand.is_absolute():
                    # Relative proof pointers resolve against the register's
                    # own folder, its parent, the workspace root, and the
                    # desk repo (the registers cite all four bases).
                    bases = [Path(path).parent, Path(path).parent.parent,
                             Path.home() / "workspace",
                             Path.home() / "workspace" / "muse-desk-v3",
                             Path.home() / "workspace" / "midna-book"]
                    cand = next((b / raw for b in bases if (b / raw).exists()),
                                bases[0] / raw)
                if not cand.exists():
                    findings["FRESH-3"].append(
                        f"{path}:{i}: proof pointer does not resolve: {raw}")
        # Due claims (claim-class fields)
        if "asserts-current-behavior:" in line:
            if "asserts-current-behavior: true" in line:
                vm = re.search(r'verified:\s*(\d{4}-\d{2}-\d{2})', line)
                if not vm:
                    findings["due"].append(
                        f"{path}:{i}: DUE (never verified): {line.strip()[:100]}")
                else:
                    vd = parse_date(vm.group(1).split("-"))
                    if vd and (reference - vd).days > DUE_DAYS:
                        findings["due"].append(
                            f"{path}:{i}: DUE (verified {vm.group(1)}, "
                            f"{(reference - vd).days} days ago): {line.strip()[:100]}")
    # FRESH-2 stamps
    if kind == "state":
        for i, line in enumerate(lines, 1):
            m = re.search(r'Last verified:\s*(\d{4})-(\d{2})-(\d{2})', line)
            if m:
                vd = parse_date((m.group(1), m.group(2), m.group(3)))
                if vd and (reference - vd).days > STATE_WINDOW_DAYS:
                    findings["FRESH-2"].append(
                        f"{path}:{i}: stamp aged {(reference - vd).days} days "
                        f"(window {STATE_WINDOW_DAYS}): answer re-observe, convert, or retire")
    if kind == "snapshot":
        m = re.search(r'Snapshot:\s*(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}))?', text)
        if m:
            sd = parse_date((m.group(1), m.group(2), m.group(3)))
            if sd:
                age_days = (reference - sd).days
                if age_days * 24 > SNAPSHOT_WINDOW_HOURS:
                    findings["FRESH-2"].append(
                        f"{path}:1: snapshot stamp {sd.isoformat()} aged about "
                        f"{age_days} days (window {SNAPSHOT_WINDOW_HOURS} hours): "
                        f"answer re-observe, convert, or retire")
        else:
            findings["FRESH-2"].append(f"{path}:1: no Snapshot stamp found")
    return findings


def lint(paths_with_kinds, reference=None) -> dict:
    reference = reference or date.today()
    merged = {"FRESH-1": [], "FRESH-2": [], "FRESH-3": [], "due": []}
    for path, kind in paths_with_kinds:
        f = lint_file(Path(path), reference, kind)
        for k in merged:
            merged[k].extend(f[k])
    return merged


def format_report(findings: dict) -> str:
    out = []
    for code in ("FRESH-1", "FRESH-2", "FRESH-3"):
        level = "warning" if code == "FRESH-2" else "error"
        out.append(f"== {code} ({level}) ==")
        out.extend(findings[code] or ["(none)"])
    out.append("== Due claims (asserts-current-behavior, computed) ==")
    out.extend(findings["due"] or ["(none)"])
    out.append(f"counts: FRESH-1={len(findings['FRESH-1'])} FRESH-2={len(findings['FRESH-2'])} "
               f"FRESH-3={len(findings['FRESH-3'])} due={len(findings['due'])}")
    return "\n".join(out)


def main(argv) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    ref = None
    for a in argv[1:]:
        if a.startswith("--reference-date="):
            ref = parse_date(a.split("=", 1)[1].split("-"))
    if not args:
        print(__doc__)
        print("usage: freshness_lint.py <STATE.md> [CONTEXT-SNAPSHOT.md] [--reference-date=YYYY-MM-DD]")
        return 2
    pairs = []
    for a in args:
        kind = "snapshot" if "CONTEXT-SNAPSHOT" in a else "state"
        pairs.append((a, kind))
    print(format_report(lint(pairs, reference=ref)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
