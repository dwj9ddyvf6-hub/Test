#!/usr/bin/env python3
"""Commit-boundary secret guard (A-15). The third guard boundary, beside
capture-time redaction (redact.py) and send-time caps (sendcheck.py).

Scans content about to be committed for secret material. Outcomes are
named and distinct:
  ALLOW          (exit 0) no secret patterns found
  POLICY_BLOCK   (exit 1) secret material found, or a disabling flag was
                 attempted: the agent itself may not pass --disable or
                 --no-verify; those flags are refused by design. The only
                 bypass is an owner-created override file
                 (~/workspace/tools/.commit_guard_owner_override) whose
                 contents name the scope; this tool never creates it.
  INFRA_FAILURE  (exit 2) the guard could not run (unreadable input,
                 missing path): distinct from a policy block, never
                 reported as a secret finding and never as an allow.

Usage:
  commit_guard.py selftest
  commit_guard.py check <file...> | check --stdin
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDE_FILE = os.path.join(HERE, ".commit_guard_owner_override")

PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("generic-secret-assignment", re.compile(
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{16,}['\"]")),
]

class InfraFailure(Exception):
    pass

def scan_text(text, label="<text>"):
    hits = []
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            line = text[:m.start()].count("\n") + 1
            hits.append({"kind": name, "where": label, "line": line})
    return hits

def check_files(paths):
    all_hits = []
    for p in paths:
        if not os.path.isfile(p):
            raise InfraFailure(f"cannot read {p!r}: not a file")
        try:
            with open(p, encoding="utf-8", errors="strict") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise InfraFailure(f"cannot read {p!r}: {e}")
        all_hits += scan_text(text, label=p)
    return all_hits

def owner_override_active():
    return os.path.isfile(OVERRIDE_FILE)

def selftest():
    import tempfile
    assert scan_text('api_key = "ABCDEFGHIJKLMNOP1234"'), "secret assignment must hit"
    assert scan_text("-----BEGIN PRIVATE KEY-----"), "key block must hit"
    assert scan_text("ordinary prose about keys and tokens in general terms") == []
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "good.txt")
        open(good, "w").write("nothing sensitive here\n")
        assert check_files([good]) == []
        try:
            check_files([os.path.join(td, "missing.txt")])
            raise SystemExit("missing file must be INFRA_FAILURE")
        except InfraFailure:
            pass
    print("SELFTEST PASS commit_guard: secret patterns blocked, clean content allowed, unreadable input is INFRA_FAILURE not a block")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if any(a in ("--disable", "--no-verify", "--skip") for a in args):
        print("POLICY_BLOCK: disabling flags may not be passed by the agent; "
              "bypass requires the owner-created override file only")
        raise SystemExit(1)
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "check":
        rest = args[1:]
        try:
            if rest == ["--stdin"]:
                hits = scan_text(sys.stdin.read(), label="<stdin>")
            else:
                hits = check_files(rest)
        except InfraFailure as e:
            print(f"INFRA_FAILURE: {e}")
            raise SystemExit(2)
        if hits:
            if owner_override_active():
                print(f"ALLOW (owner override file present): {len(hits)} hit(s) waived by owner scope")
                raise SystemExit(0)
            for h in hits:
                print(f"POLICY_BLOCK: {h['kind']} in {h['where']} line {h['line']}")
            raise SystemExit(1)
        print("ALLOW: no secret patterns found")
        raise SystemExit(0)
    print(__doc__)
    raise SystemExit(2)
