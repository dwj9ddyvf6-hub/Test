#!/usr/bin/env python3
"""scope_audit.py: deterministic scope-creep audit, diff versus intent.

Implements round-3 adoption item 1 of discipline 8 (mechanised completion
claims) from the InfinityBlade agent-enhancement reference: a standard
library only, no network, read-only check that compares a finished git
diff against the brief's one-line stated intent and emits a keep / split /
justify report.

Flags:
  - unrelated paths: changed paths no reasonable reading of the intent
    covers, judged by path tokens against intent tokens and an optional
    allowed-paths list
  - new dependencies: dependency names added in manifest files, and any
    change to a lockfile
  - public API renames: a public definition removed while a differently
    named public definition is added in the same file
  - config or CI edits
  - oversized hunks: a single hunk larger than the threshold
  - formatting-only files: files whose diff vanishes when whitespace is
    ignored
  - subsystem spread: changes spanning more top-level areas than the
    threshold (informational flag, still counts toward the exit code)

Exit codes: 0 clean, 1 flags exist, 2 usage error.

Usage:
  scope_audit.py REPO BASE_REF HEAD_REF --intent "one line intent"
                 [--allow PATH_PREFIX ...] [--max-hunk-lines N]
                 [--max-areas N] [--format text|json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "fix", "fixes", "add", "adds", "update", "updates", "change", "changes",
    "when", "so", "that", "this", "it", "is", "are", "be", "by", "from",
    "into", "per", "via",
}

MANIFESTS = {
    "package.json", "requirements.txt", "pipfile", "pyproject.toml",
    "setup.py", "setup.cfg", "cargo.toml", "go.mod", "gemfile",
    "composer.json", "pom.xml", "build.gradle", "build.gradle.kts",
}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "pipfile.lock",
    "poetry.lock", "cargo.lock", "go.sum", "gemfile.lock", "composer.lock",
}
CI_MARKERS = (".github/workflows/", ".circleci/", ".gitlab/", ".buildkite/")
CONFIG_BASENAMES = {
    ".gitlab-ci.yml", ".travis.yml", "dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "makefile", ".pre-commit-config.yaml",
    "jenkinsfile", "azure-pipelines.yml",
}
CONFIG_SUFFIXES = (".ini", ".cfg", ".conf")
CONFIG_NAME_HINTS = ("config", "settings", ".rc")

DEF_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
    re.compile(r"^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*pub\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)"),
]

DEP_LINE_PATTERNS = [
    # "name": "version" in JSON-ish manifests
    re.compile(r'"([@A-Za-z0-9_.\-/]+)"\s*:\s*"[^"]*"'),
    # name==version, name>=version, name~=version in requirements style
    re.compile(r"^([A-Za-z0-9_.\-]+)\s*(?:==|>=|<=|~=|!=|>)"),
    # name = "version" in TOML-ish manifests
    re.compile(r"^([A-Za-z0-9_.\-]+)\s*=\s*[\"']"),
]


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise UsageError(f"git {' '.join(args[:2])} failed: {proc.stderr.strip()}")
    return proc.stdout


class UsageError(Exception):
    pass


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in re.split(r"[^A-Za-z0-9]+", text):
        if not raw:
            continue
        # split camelCase and letter/digit boundaries
        parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+", raw)
        for part in parts or [raw]:
            tok = part.lower()
            if len(tok) >= 3 and tok not in STOPWORDS:
                tokens.add(tok)
            elif len(tok) >= 2 and tok.isdigit():
                tokens.add(tok)
    return tokens


def path_tokens(path: str) -> set[str]:
    return tokenize(path.replace("/", " ").replace(".", " "))


def tokens_match(a: str, b: str) -> bool:
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 4 and long_.startswith(short)


def any_match(path_toks: set[str], intent_toks: set[str]) -> bool:
    return any(tokens_match(p, i) for p in path_toks for i in intent_toks)


def is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == a or path.startswith(a.rstrip("/") + "/") for a in allowed)


def basename(path: str) -> str:
    return path.rsplit("/", 1)[-1].lower()


def is_config_or_ci(path: str) -> bool:
    low = path.lower()
    base = basename(path)
    if any(m in low for m in CI_MARKERS):
        return True
    if base in CONFIG_BASENAMES:
        return True
    if base.startswith(".") and base.endswith("rc"):
        return True
    if "tsconfig" in base or "eslint" in base or "prettier" in base:
        return True
    if base.endswith(CONFIG_SUFFIXES) and "config" in low:
        return True
    if any(h in base for h in CONFIG_NAME_HINTS) and base not in MANIFESTS:
        return True
    return False


def parse_patch(patch: str) -> dict[str, dict]:
    """Split a unified diff into per-file added/removed lines and hunks."""
    files: dict[str, dict] = {}
    current: str | None = None
    hunk_size = 0

    def flush_hunk() -> None:
        nonlocal hunk_size
        if current is not None and hunk_size:
            files[current]["hunks"].append(hunk_size)
        hunk_size = 0

    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            flush_hunk()
            current = line[6:]
            files.setdefault(current, {"added": [], "removed": [], "hunks": []})
        elif line.startswith("@@ "):
            flush_hunk()
            m = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
            if m and current is not None:
                removed = int(m.group(1) or 1)
                added = int(m.group(2) or 1)
                hunk_size = removed + added
        elif current is not None:
            if line.startswith("+") and not line.startswith("+++"):
                files[current]["added"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                files[current]["removed"].append(line[1:])
    flush_hunk()
    return files


def public_defs(lines: list[str]) -> set[str]:
    names: set[str] = set()
    for line in lines:
        for pat in DEF_PATTERNS:
            m = pat.match(line)
            if m and not m.group(1).startswith("_"):
                names.add(m.group(1))
    return names


def dep_names(lines: list[str]) -> set[str]:
    names: set[str] = set()
    for line in lines:
        stripped = line.strip().lstrip("-").strip()
        if not stripped or stripped.startswith("#"):
            continue
        for pat in DEP_LINE_PATTERNS:
            m = pat.search(stripped)
            if m:
                names.add(m.group(1).lower())
                break
    return names


def audit(repo: str, base: str, head: str, intent: str,
          allowed: list[str], max_hunk: int, max_areas: int) -> dict:
    for ref in (base, head):
        git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    name_status = git(repo, "diff", "--name-status", "-M", base, head)
    changed: list[tuple[str, str]] = []
    for line in name_status.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        status = parts[0][0]
        path = parts[-1]
        changed.append((status, path))

    patch = git(repo, "diff", "-M", base, head, "--")
    per_file = parse_patch(patch)
    ws_patch = git(repo, "diff", "-w", "--numstat", base, head, "--")
    ws_changed: set[str] = set()
    for line in ws_patch.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            ws_changed.add(parts[-1])

    intent_toks = tokenize(intent)
    findings: list[dict] = []

    def flag(path: str, category: str, verdict: str, detail: str) -> None:
        findings.append({"path": path, "category": category,
                         "verdict": verdict, "detail": detail})

    areas: set[str] = set()
    for status, path in changed:
        areas.add(path.split("/", 1)[0] if "/" in path else "(root)")
        info = per_file.get(path, {"added": [], "removed": [], "hunks": []})
        base_name = basename(path)

        if not is_allowed(path, allowed) and not any_match(path_tokens(path), intent_toks):
            flag(path, "unrelated-path", "split",
                 "no path token matches the stated intent and the path is "
                 "not on the allowed list")

        if base_name in LOCKFILES:
            flag(path, "new-dependency", "justify",
                 "lockfile changed; dependency set may have moved")
        elif base_name in MANIFESTS:
            new_deps = dep_names(info["added"]) - dep_names(info["removed"])
            if new_deps:
                flag(path, "new-dependency", "justify",
                     "new dependencies: " + ", ".join(sorted(new_deps)))

        removed_defs = public_defs(info["removed"])
        added_defs = public_defs(info["added"])
        renamed_from = removed_defs - added_defs
        renamed_to = added_defs - removed_defs
        if renamed_from and renamed_to:
            flag(path, "public-api-rename", "justify",
                 "public definitions removed (%s) while new ones were "
                 "added (%s); possible rename" % (
                     ", ".join(sorted(renamed_from)),
                     ", ".join(sorted(renamed_to))))

        if is_config_or_ci(path):
            flag(path, "config-or-ci", "justify", "config or CI file edited")

        for size in info["hunks"]:
            if size > max_hunk:
                flag(path, "oversized-hunk", "justify",
                     f"hunk of {size} changed lines exceeds the "
                     f"{max_hunk} line threshold")

        touched = info["added"] or info["removed"]
        if status == "M" and touched and path not in ws_changed:
            flag(path, "formatting-only", "split",
                 "diff disappears when whitespace is ignored")

    if len(areas) > max_areas:
        flag("(whole diff)", "subsystem-spread", "justify",
             f"change spans {len(areas)} top-level areas "
             f"({', '.join(sorted(areas))}), over the {max_areas} threshold")

    flagged_paths = {f["path"] for f in findings}
    keep = [p for _, p in changed if p not in flagged_paths]
    return {
        "repo": repo, "base": base, "head": head, "intent": intent,
        "changed_files": [p for _, p in changed],
        "keep": keep,
        "findings": findings,
        "clean": not findings,
    }


def render_text(report: dict) -> str:
    out: list[str] = []
    out.append("Scope audit: diff versus intent")
    out.append(f"Repo:   {report['repo']}")
    out.append(f"Range:  {report['base']}..{report['head']}")
    out.append(f"Intent: {report['intent']}")
    out.append(f"Changed files: {len(report['changed_files'])}")
    out.append("")
    out.append("KEEP (no flags):")
    if report["keep"]:
        out.extend(f"  keep     {p}" for p in report["keep"])
    else:
        out.append("  (none)")
    out.append("")
    for verdict, title in (("split", "SPLIT (does not belong in this change)"),
                           ("justify", "JUSTIFY (needs a stated reason)")):
        rows = [f for f in report["findings"] if f["verdict"] == verdict]
        out.append(f"{title}:")
        if rows:
            for f in rows:
                out.append(f"  {verdict:<8} {f['path']} [{f['category']}] {f['detail']}")
        else:
            out.append("  (none)")
        out.append("")
    verdict = "CLEAN" if report["clean"] else "FLAGS PRESENT"
    out.append(f"Verdict: {verdict} ({len(report['findings'])} flag(s))")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scope_audit",
        description="Deterministic scope-creep audit: diff versus intent.")
    parser.add_argument("repo", help="path to the git repository")
    parser.add_argument("base", help="base ref")
    parser.add_argument("head", help="head ref")
    parser.add_argument("--intent", required=True,
                        help="one-line stated intent for the change")
    parser.add_argument("--allow", action="append", default=[],
                        help="allowed path or path prefix (repeatable)")
    parser.add_argument("--max-hunk-lines", type=int, default=300)
    parser.add_argument("--max-areas", type=int, default=4)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        git(args.repo, "rev-parse", "--is-inside-work-tree")
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        report = audit(args.repo, args.base, args.head, args.intent,
                       args.allow, args.max_hunk_lines, args.max_areas)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
