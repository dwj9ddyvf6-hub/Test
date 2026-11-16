"""Check final STATUS syntax and evidence-pointer presence, never its truth.

Usage: python3 tools/status_evidence_check.py [FILE]
Quoted examples and fenced code are not verdicts. The last nonempty prose
line must be a valid STATUS. Only a reply consisting entirely of the exact
GREEN no-change marker is exempt from a nonempty evidence pointer.
"""
import argparse
import re
from pathlib import Path
import sys

VERDICTS = ("GREEN", "PARTIAL", "BLOCKED", "UNVERIFIED")
SCOPE = re.compile(r"STATUS:\s*GREEN\s*(?:—|,)\s*no change made\.?", re.I)
STATUS = re.compile(r"STATUS:\s*(GREEN|PARTIAL|BLOCKED|UNVERIFIED)\b(.*)")
POINTER = re.compile(r"evidence:\s*\S|https?://[^\s/]+(?:/\S*)?|(?:[\w.-]+/)+[\w.-]+|[\w-]+\.[A-Za-z0-9]{1,12}(?:[:#]\S+)?")


def check(text):
    stripped = text.strip()
    if SCOPE.fullmatch(stripped):
        return True, "scope marker: no claim made, no pointer required"
    prose, fence = [], None
    for line in text.splitlines():
        value = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", value)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None and value and not value.startswith(">"):
            prose.append(value)
    if fence is not None:
        return False, "unterminated code fence: final verdict is ambiguous"
    if not prose or not STATUS.fullmatch(prose[-1]):
        return False, "last prose line must be STATUS: GREEN, PARTIAL, BLOCKED, or UNVERIFIED"
    tail = STATUS.fullmatch(prose[-1]).group(2)
    if not POINTER.search(tail):
        return False, "final STATUS needs a nonempty evidence pointer; no-change exemption requires the whole reply"
    return True, "final STATUS carries an evidence pointer (presence checked, truth not checked)"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    ok, message = check(text)
    print(message, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
