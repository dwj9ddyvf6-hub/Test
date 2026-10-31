#!/usr/bin/env python3
"""Build the navigation index for this repository: INDEX.json and INDEX.md.

The index is written for a reader (human or LLM) arriving cold. INDEX.json
lists every blob at one pinned commit; INDEX.md is the prose map of the
same inventory. Both files are generated from a single GitHub git-trees
fetch, so their counts always agree with each other and with the tree.

Usage:
    python3 tools/build_repo_index.py
    GITHUB_TOKEN=<token> python3 tools/build_repo_index.py --branch main
    python3 tools/build_repo_index.py --tree-json snapshot.json --out-dir .

Options:
    --owner, --repo   Repository coordinates (defaults below).
    --branch          Branch whose HEAD commit is indexed (default: the
                      repository default branch, resolved through the API).
    --tree-json PATH  Read a saved snapshot instead of calling the API.
                      Snapshot shape: {"head": <commit sha>,
                      "generated_at": <iso timestamp>, "tree": [<tree
                      entries as returned by the git trees API>]}.
    --out-dir PATH    Where INDEX.json and INDEX.md are written
                      (default: current directory).

Determinism: entries are sorted by path, JSON keys are sorted, and
generated_at is the indexed commit's own timestamp, so regenerating the
index for the same commit produces byte-identical output.

Self entries: INDEX.md, INDEX.json and this script cannot carry their own
blob hash inside themselves, so they are listed with sha and size_bytes
set to null and "self": true. Every other entry carries the exact git
blob sha and size reported by the trees API for the indexed commit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter

DEFAULT_OWNER = "dwj9ddyvf6-hub"
DEFAULT_REPO = "Test"
API_BASE = "https://api.github.com"
SCHEMA_VERSION = 1
SELF_PATHS = ("INDEX.json", "INDEX.md", "tools/build_repo_index.py")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp"}
ARCHIVE_EXTS = {".zip", ".gz", ".tgz", ".tar", ".xz", ".7z"}
DOC_EXTS = {".md", ".txt", ".pdf", ".docx", ".rst", ".adoc"}
CODE_EXTS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".ps1",
    ".html", ".css", ".pine", ".sql", ".r", ".jl", ".go", ".rs", ".java",
    ".c", ".h", ".cpp",
}
DATA_EXTS = {".json", ".csv", ".tsv", ".xml", ".log", ".ndjson"}
CONFIG_NAMES = {".gitignore", ".dockerignore", ".gitattributes"}
CONFIG_EXTS = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".example",
               ".webmanifest", ".tsbuildinfo"}

AREA_DESCRIPTIONS = {
    "(root)": "Repository root: the README catalog front page, this index, "
              "the agent rules file, and the build notes for the newest "
              "sleeve families.",
    "adapters": "Standalone desk adapters for recently built sleeves "
                "(one-bar, Trullas variants, Teddy ORB, PRZM and others), "
                "one file per sleeve.",
    "adapters3": "The Aster adapter set: one adapter module per Aster "
                 "sleeve variant, mirroring the sleeves they wire in.",
    "agentic-trade-desk": "The operational kit for running an agentic "
                          "trade desk: a runnable skeleton, docs and "
                          "templates. Paper trading only.",
    "aster_sleeves": "Aster sleeve entry points (thin wrappers over the "
                     "shared engine commons).",
    "config": "Desk configuration. config/sleeves.json is the live roster "
              "config mirrored into this repository.",
    "desk3": "The desk3 sleeve collection and its portfolio branches.",
    "docs": "Documentation at scale: the strategy catalog data, the "
            "current-desk and all-strategies accountings, one algorithm "
            "and recreation document per strategy, verification notes, "
            "and the research collections under docs/research/.",
    "engines": "Shared engine code: desk3 bridges and enhancements, "
               "sleeve commons, the roster config copy and a transport "
               "kernel.",
    "indicator": "A single indicator package.",
    "integration": "Integration adapters that wire each sleeve into the "
                   "desk runner, plus the wiring guide.",
    "laz_sleeves": "Lazarus sleeve entry points (thin wrappers over the "
                   "shared engine commons).",
    "packages": "Whole packages contributed by the desk's builders, "
                "grouped by author. See the packages entry point in "
                "INDEX.md for the per-author breakdown.",
    "pine": "Pine Script sources.",
    "proof": "Install proof records: one JSON receipt per installed "
             "sleeve under proof/install/.",
    "psychology-engine": "The standalone market-psychology engine "
                         "package: engine code, audits, research and "
                         "reports. One of the two psychology engines in "
                         "this repository.",
    "research": "Standalone research works. Home of the technical "
                "analysis study and practice archive (Markdown, PDF, "
                "DOCX and ZIP forms of the same work).",
    "sleeves": "Sleeve source code grouped by family, plus standalone "
               "sleeve modules at the top of the folder.",
    "strategies": "Strategy cards: one card per catalogued strategy, "
                  "grouped by family folder. The family folders are "
                  "enumerated in docs/CATALOG.json and in INDEX.json; "
                  "they are not repeated in this prose map.",
    "terminal-lineup": "The public terminal lineup: the tool site under "
                       "site/, the forecast engines under forecast/, "
                       "build records, design documents, the oracle and "
                       "the workflow scripts that built the tools.",
    "tests": "Repository-level regression blocker tests.",
    "tools": "Repository tooling. Home of build_repo_index.py, the "
             "generator that produces INDEX.json and INDEX.md.",
}


def extension_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    if name.startswith(".") and name.count(".") == 1:
        return name.lower()
    return "." + name.rsplit(".", 1)[-1].lower()


def kind_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1].lower()
    ext = extension_of(path)
    parts = path.lower().split("/")
    if "tests" in parts or "test" in parts or name.startswith("test_") \
            or name.startswith("test-") or "_test." in name \
            or name.endswith("_tests.py"):
        return "test"
    if ext in IMAGE_EXTS or ext == ".svg":
        return "image"
    if ext in ARCHIVE_EXTS:
        return "archive"
    if name in CONFIG_NAMES or ext in CONFIG_EXTS:
        return "config"
    if ext in DOC_EXTS:
        return "document"
    if ext in CODE_EXTS:
        return "code"
    if ext in DATA_EXTS:
        return "data"
    return "other"


def area_of(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "(root)"


def directory_of(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def build_entries(tree_entries):
    blobs = [e for e in tree_entries if e.get("type") == "blob"]
    by_path = {e["path"]: e for e in blobs}
    entries = []
    for path in sorted(by_path):
        e = by_path[path]
        if path in SELF_PATHS:
            entries.append({
                "path": path, "size_bytes": None, "sha": None,
                "extension": extension_of(path),
                "top_level_area": area_of(path),
                "directory": directory_of(path),
                "kind": kind_of(path), "self": True,
            })
        else:
            entries.append({
                "path": path, "size_bytes": e.get("size"),
                "sha": e.get("sha"),
                "extension": extension_of(path),
                "top_level_area": area_of(path),
                "directory": directory_of(path),
                "kind": kind_of(path),
            })
    for path in SELF_PATHS:
        if path not in by_path:
            entries.append({
                "path": path, "size_bytes": None, "sha": None,
                "extension": extension_of(path),
                "top_level_area": area_of(path),
                "directory": directory_of(path),
                "kind": kind_of(path), "self": True,
            })
    entries.sort(key=lambda x: x["path"])
    return entries


def build_index(tree_entries, head_sha, generated_at, owner, repo):
    entries = build_entries(tree_entries)
    per_area = Counter(e["top_level_area"] for e in entries)
    per_area_bytes = Counter()
    for e in entries:
        if e["size_bytes"]:
            per_area_bytes[e["top_level_area"]] += e["size_bytes"]
    total_bytes = sum(e["size_bytes"] or 0 for e in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": f"{owner}/{repo}",
        "generated_at": generated_at,
        "indexed_commit": head_sha,
        "totals": {"files": len(entries), "bytes": total_bytes},
        "per_area_counts": dict(sorted(per_area.items())),
        "per_area_bytes": dict(sorted(per_area_bytes.items())),
        "files": entries,
    }


def sub_counts(entries, prefix, depth):
    counts = Counter()
    for e in entries:
        path = e["path"]
        if path.startswith(prefix):
            rest = path[len(prefix):].split("/")
            key = "/".join(rest[:depth]) if len(rest) > 1 else "(files)"
            counts[key] += 1
    return counts


def render_markdown(index):
    entries = index["files"]
    total = index["totals"]["files"]
    total_bytes = index["totals"]["bytes"]
    per_area = index["per_area_counts"]
    per_area_bytes = index["per_area_bytes"]
    lines = []
    add = lines.append
    add("# Repository index")
    add("")
    add("Start here. This file is the map of the whole repository for a "
        "reader (human or LLM) arriving cold. Its machine-readable twin "
        "is [INDEX.json](INDEX.json), generated from the same inventory "
        "by [tools/build_repo_index.py](tools/build_repo_index.py).")
    add("")
    add(f"Total files indexed: {total}")
    add("")
    add(f"Indexed commit: `{index['indexed_commit']}`. "
        f"Generated at: {index['generated_at']}. "
        f"Total size of indexed files (self entries excluded, their "
        f"sizes are null): {total_bytes} bytes.")
    add("")
    add("## What this repository is")
    add("")
    add("A public library of trading strategies and the desk software "
        "around them: strategy cards, sleeve source code, recreation "
        "notes that let anyone rebuild a strategy from its recorded "
        "rules, the public terminal tool lineup, forecast and psychology "
        "engines, research works, and the guides that teach an agent or "
        "a person how to build a desk like this. Paper trading only.")
    add("")
    add("## Reading order")
    add("")
    add("1. This file, INDEX.md: the map.")
    add("2. [INDEX.json](INDEX.json): every file, when you need the "
        "exact path, size or blob sha of anything.")
    add("3. [README.md](README.md): the strategy catalog front page.")
    add("4. [docs/CATALOG.json](docs/CATALOG.json): the catalog data, "
        "one card per strategy with variants folded in; the cards "
        "themselves live under strategies/.")
    add("5. [docs/ALL-SLEEVES.md](docs/ALL-SLEEVES.md): the full "
        "accounting of every distinct strategy across all desks, with "
        "its machine-readable twin docs/ALL-SLEEVES.json.")
    add("6. [docs/SLEEVES.md](docs/SLEEVES.md): the current desk roster, "
        "one row per installed sleeve, mirrored from "
        "config/sleeves.json.")
    add("7. The research collections under docs/research/ and "
        "research/ (see entry points below).")
    add("8. [terminal-lineup/THE-70-TOOLS.md]"
        "(terminal-lineup/THE-70-TOOLS.md): the public terminal lineup "
        "and its tools, then the site and forecast code beneath it.")
    add("")
    add("## Map of every top-level area")
    add("")
    add("| Area | Files | Bytes | What it is |")
    add("| --- | ---: | ---: | --- |")
    for area in sorted(per_area):
        desc = AREA_DESCRIPTIONS.get(
            area, "Files grouped under this top-level area; see "
                  "INDEX.json for the full listing.")
        add(f"| {area} | {per_area[area]} | "
            f"{per_area_bytes.get(area, 0)} | {desc} |")
    add("")
    add("## Entry points into every major collection")
    add("")
    add("### Strategies catalog")
    add("")
    add("- [docs/CATALOG.json](docs/CATALOG.json): catalog data for the "
        "strategies, one card per strategy.")
    add("- strategies/: the card files themselves, one folder per "
        "family. Family folder names and counts are in INDEX.json.")
    add("- [docs/ALL-SLEEVES.md](docs/ALL-SLEEVES.md) and "
        "docs/ALL-SLEEVES.json: every distinct strategy across all "
        "desks, deduplicated, arranged by type.")
    add("- docs/: one algorithm document and one recreation document "
        "per strategy sit directly under docs/ alongside the catalog "
        "files; their exact names are in INDEX.json.")
    add("")
    add("### Sleeves")
    add("")
    add("- sleeves/: sleeve source code, grouped by family folder with "
        "standalone modules at the top.")
    add("- [config/sleeves.json](config/sleeves.json): the roster "
        "config the current-desk view mirrors.")
    add("- [docs/SLEEVES.md](docs/SLEEVES.md) and docs/SLEEVES.json: "
        "the installed roster, one row per sleeve with its code file.")
    add("- aster_sleeves/ and laz_sleeves/: thin sleeve entry points "
        "over the shared commons in engines/.")
    add("- desk3/ and engines/desk3/: the desk3 collection and its "
        "engine bridges.")
    add("")
    add("### Packages by author")
    add("")
    for author in sorted(sub_counts(entries, "packages/", 1)):
        if author == "(files)":
            continue
        pkg_counts = sub_counts(entries, f"packages/{author}/", 1)
        pkg_list = ", ".join(
            f"{name} ({count})" for name, count in
            sorted(pkg_counts.items()) if name != "(files)")
        add(f"- packages/{author}/ "
            f"({sub_counts(entries, 'packages/', 1)[author]} files): "
            f"{pkg_list}.")
    add("")
    add("### Docs and research")
    add("")
    add("- docs/: catalog, accountings, per-strategy algorithm and "
        "recreation documents, guides and verification notes.")
    add("- docs/verify/: verification notes.")
    add("- docs/research/: the collected research works, including the "
        "two below.")
    add("- Psychology engine, first of two: "
        "[psychology-engine/](psychology-engine/README.md), the "
        "standalone package with engine/, audit/, research/ and "
        "report/ sections.")
    add("- Psychology engine, second of two: "
        "docs/research/psychology-engine-2026-10-30/, the research "
        "build with its own engine under "
        "docs/research/psychology-engine-2026-10-30/engine/ and the "
        "study papers beside it.")
    add("- Technical analysis, first of two: "
        "docs/research/technical-analysis-mastery-20261030/, the "
        "mastery work with census/ and sections/ folders and the "
        "combined texts at its top.")
    add("- Technical analysis, second of two: "
        "research/technical-analysis-study-2026-10-30/, the study and "
        "practice archive in Markdown, PDF, DOCX and ZIP forms.")
    add("- docs/research/onebar-family-2026-10-30/: the one-bar family "
        "analysis.")
    add("")
    add("### Terminal lineup")
    add("")
    site_n = sum(1 for e in entries
                 if e["path"].startswith("terminal-lineup/site/"))
    fc_n = sum(1 for e in entries
               if e["path"].startswith("terminal-lineup/forecast/"))
    wf_n = sum(1 for e in entries
               if e["path"].startswith("terminal-lineup/workflow-"))
    add(f"- [terminal-lineup/THE-70-TOOLS.md]"
        f"(terminal-lineup/THE-70-TOOLS.md): the lineup manifest.")
    add(f"- terminal-lineup/site/ ({site_n} files): the public tool "
        f"site; each tool has its own folder with its page and data, "
        f"and the refresh scripts sit at the top of site/.")
    add(f"- terminal-lineup/forecast/ ({fc_n} files): the forecast "
        f"engines, their registry, grading and ledger code, and their "
        f"tests. See also terminal-lineup/FORECAST-ENGINES-30.md.")
    add(f"- terminal-lineup/ root: design documents, bug logs, build "
        f"progress files and {wf_n} workflow scripts that built the "
        f"tools.")
    add("- terminal-lineup/oracle/: the oracle provenance record. "
        "terminal-lineup/records/: build and search records. "
        "terminal-lineup/specs/: specifications.")
    add("")
    add("### Integration, proof and engines")
    add("")
    add("- integration/: one adapter per sleeve wiring it into the "
        "desk runner, plus integration/Femto-lean_Wiring.md.")
    add("- adapters/ and adapters3/: standalone and Aster adapter "
        "sets.")
    add("- proof/install/: one JSON install-proof receipt per "
        "installed sleeve.")
    add("- engines/: shared engine code (desk3 bridges, sleeve "
        "commons, roster config copy, transport kernel).")
    add("- tests/: repository-level regression blocker tests.")
    add("- agentic-trade-desk/: the operational kit and runnable "
        "skeleton; start at agentic-trade-desk/README.md.")
    add("")
    add("## Coverage statement")
    add("")
    add(f"Every file present at the indexed commit "
        f"(`{index['indexed_commit']}`) is listed in INDEX.json: "
        f"{total} entries in total, covering every blob in the tree "
        f"at that commit. The three index files themselves "
        f"(INDEX.md, INDEX.json, tools/build_repo_index.py) are the "
        f"only entries whose sha and size are null; they are marked "
        f"\"self\": true because a file cannot contain its own hash. "
        f"All other entries carry the exact git blob sha and size "
        f"from the tree. Nothing at the indexed commit is omitted, "
        f"and no path is listed that was not in the tree, apart from "
        f"the self entries for the two index files created by the "
        f"generation itself.")
    add("")
    add("## How to regenerate")
    add("")
    add("Run the generator from a checkout or any folder:")
    add("")
    add("    python3 tools/build_repo_index.py --out-dir .")
    add("")
    add("It resolves the default branch, fetches that branch's HEAD "
        "commit and its full recursive tree from the GitHub API "
        "(set GITHUB_TOKEN to authenticate), and rewrites INDEX.json "
        "and INDEX.md deterministically: same commit in, byte-"
        "identical files out. A saved tree snapshot can be indexed "
        "offline with --tree-json. Uploads to this repository go "
        "through the repository's gated contents route only, never "
        "raw git pushes from an index run.")
    add("")
    return "\n".join(lines)


def fetch_json(url, token):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "build-repo-index/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owner", default=DEFAULT_OWNER)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--branch", default=None)
    ap.add_argument("--tree-json", default=None)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args(argv)

    if args.tree_json:
        with open(args.tree_json, encoding="utf-8") as fh:
            snap = json.load(fh)
        tree_entries = snap["tree"]
        head_sha = snap["head"]
        generated_at = snap["generated_at"]
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get(
            "GH_TOKEN")
        branch = args.branch
        if branch is None:
            repo_info = fetch_json(
                f"{API_BASE}/repos/{args.owner}/{args.repo}", token)
            branch = repo_info["default_branch"]
        commit = fetch_json(
            f"{API_BASE}/repos/{args.owner}/{args.repo}"
            f"/commits/{branch}", token)
        head_sha = commit["sha"]
        generated_at = commit["commit"]["committer"]["date"]
        tree = fetch_json(
            f"{API_BASE}/repos/{args.owner}/{args.repo}"
            f"/git/trees/{head_sha}?recursive=1", token)
        if tree.get("truncated"):
            print("ERROR: tree response truncated; refusing to emit "
                  "a partial index", file=sys.stderr)
            return 2
        tree_entries = tree["tree"]

    index = build_index(tree_entries, head_sha, generated_at,
                        args.owner, args.repo)
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "INDEX.json")
    md_path = os.path.join(args.out_dir, "INDEX.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(index))
    print(f"indexed {index['totals']['files']} files at {head_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
