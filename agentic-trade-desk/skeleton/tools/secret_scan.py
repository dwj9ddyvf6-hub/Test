#!/usr/bin/env python3
"""Minimal secret scanner: run before every commit/push. Exit 1 on any hit. Prints file:line and the RULE, never the value."""
import os, re, subprocess, sys

RULES = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_api_key_assign": re.compile(r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{20,}['\"]"),
    "bearer_token": re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._\-]{20,}"),
    "long_hex_secret": re.compile(r"\b[0-9a-f]{40,}\b"),
    "gh_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "email_address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}
ALLOW_EXT = {".md", ".py", ".js", ".sh", ".json", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".env.example"}


def tracked_files():
    try:
        out = subprocess.check_output(["git", "ls-files"], text=True)
        return [f for f in out.splitlines() if os.path.splitext(f)[1] in ALLOW_EXT]
    except Exception:
        return [os.path.join(d, f) for d, _, fs in os.walk(".") for f in fs]


def main():
    hits = 0
    for f in tracked_files():
        try:
            for i, line in enumerate(open(f, errors="ignore"), 1):
                for name, rx in RULES.items():
                    if rx.search(line):
                        print(f"{f}:{i}: {name}")
                        hits += 1
        except OSError:
            pass
    print(f"{hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
