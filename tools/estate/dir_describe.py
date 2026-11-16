#!/usr/bin/env python3
"""Every directory self-describes at two compression levels (T-69).

Convention: a directory carries DIRECTORY.md with exactly two levels:
  Abstract: one sentence (a single sentence, at most 200 characters)
  Overview: a short paragraph naming what lives here and how it is used
Read order is abstract, then overview, then full content, generalizing
the root-index discipline to every directory, across the library and
the memory store alike. This tool checks the convention and audits a
tree; generate writes a skeleton with explicit TODO markers only, it
never fabricates a description of contents it has not read.

Usage:
  dir_describe.py selftest
  dir_describe.py check <dir>
  dir_describe.py audit <root>   (one line per directory, missing named)
  dir_describe.py generate <dir> (skeleton with TODO markers)
"""
import os, re, sys

FILENAME = "DIRECTORY.md"
SKELETON = """# Directory description (TODO: replace the TODO lines with real text)

Abstract: TODO one sentence, at most 200 characters, naming what this directory is.

Overview: TODO a short paragraph naming what lives here, how it is used,
and what a reader should open first. This skeleton is UNVERIFIED until
the TODO lines are replaced from actually reading the directory.
"""

def check_dir(path):
    p = os.path.join(path, FILENAME)
    if not os.path.isfile(p):
        return [f"missing {FILENAME}"]
    text = open(p, encoding="utf-8").read()
    errs = []
    m = re.search(r"^Abstract:\s*(.+)$", text, re.M)
    if not m:
        errs.append("missing Abstract line")
    else:
        abstract = m.group(1).strip()
        if "TODO" in abstract:
            errs.append("abstract is still a TODO skeleton (UNVERIFIED)")
        if len(abstract) > 200:
            errs.append(f"abstract over 200 chars ({len(abstract)})")
        if len([s for s in re.split(r"[.!?]+", abstract) if s.strip()]) > 1:
            errs.append("abstract must be exactly one sentence")
    m2 = re.search(r"^Overview:\s*(.+)$", text, re.M | re.S)
    if not m2 or len(m2.group(1).strip()) < 40:
        errs.append("missing or too-short Overview (needs a real paragraph)")
    elif "TODO" in m2.group(1):
        errs.append("overview is still a TODO skeleton (UNVERIFIED)")
    return errs

def audit(root):
    rows = []
    for dirpath, dirnames, _files in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        errs = check_dir(dirpath)
        rows.append({"dir": dirpath, "ok": not errs, "errors": errs})
    return rows

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        assert check_dir(td) == [f"missing {FILENAME}"]
        with open(os.path.join(td, FILENAME), "w") as f:
            f.write(SKELETON)
        errs = check_dir(td)
        assert any("TODO" in e for e in errs), errs  # skeleton is named unverified, never ok
        with open(os.path.join(td, FILENAME), "w") as f:
            f.write("Abstract: Tools that gate and prove local automation work.\n\n"
                    "Overview: This directory holds the mechanical gates, their selftests, "
                    "and the shared helpers the gates compose. Open tools_gate.py first "
                    "for the composed run, then the individual gate named by the task.\n")
        assert check_dir(td) == [], check_dir(td)
        rows = audit(td)
        assert rows and rows[0]["ok"], rows
        print("SELFTEST PASS dir_describe: missing named, TODO skeleton flagged UNVERIFIED, real two-level description passes, audit reports per directory")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "check" and len(args) == 2:
        errs = check_dir(args[1])
        print("OK" if not errs else "\n".join(errs))
        raise SystemExit(1 if errs else 0)
    if args and args[0] == "audit" and len(args) == 2:
        rows = audit(args[1])
        for r in rows:
            print(("OK  " if r["ok"] else "MISS") + f" {r['dir']}" + ("" if r["ok"] else f" :: {'; '.join(r['errors'])}"))
        raise SystemExit(1 if any(not r["ok"] for r in rows) else 0)
    if args and args[0] == "generate" and len(args) == 2:
        dest = os.path.join(args[1], FILENAME)
        if os.path.exists(dest):
            print(f"refusing to overwrite existing {dest}")
            raise SystemExit(1)
        open(dest, "w").write(SKELETON)
        print(f"wrote skeleton {dest} (UNVERIFIED until TODO lines are replaced)")
        raise SystemExit(0)
    print(__doc__)
    raise SystemExit(2)
