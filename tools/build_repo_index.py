#!/usr/bin/env python3
"""Build or check the exact file inventory and prose collection map.

Online (compatible with the original command):
  python3 tools/build_repo_index.py --branch main --out-dir .
Offline, pinned local commit:
  python3 tools/build_repo_index.py --local-repo . --ref HEAD --out-dir .
Offline, staged candidate (read-only Git access; no git write-tree):
  python3 tools/build_repo_index.py --local-repo . --staged --out-dir /tmp/index
Check the saved inventory against a selected source, without rewriting files:
  python3 tools/build_repo_index.py --local-repo . --ref HEAD --check --out-dir .
Saved API snapshot (head, generated_at, tree; optional navigation_map):
  python3 tools/build_repo_index.py --tree-json snapshot.json --out-dir .

Only INDEX.json and INDEX.md are self entries. The generator is ordinary source
and is hashed. A staged tree has no commit: indexed_commit is null, while the
source records its base commit and exact computed Git tree hash. Publish a
commit-pinned inventory after committing source changes. Counts are measured;
area meanings and task routes come from docs/REPOSITORY-MAP.json when present.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse
import urllib.request

DEFAULT_OWNER = "dwj9ddyvf6-hub"
DEFAULT_REPO = "Test"
API_BASE = "https://api.github.com"
SCHEMA_VERSION = 1
SELF_PATHS = ("INDEX.json", "INDEX.md")
MAP_PATH = "docs/REPOSITORY-MAP.json"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp"}
ARCHIVE_EXTS = {".zip", ".gz", ".tgz", ".tar", ".xz", ".7z"}
DOC_EXTS = {".md", ".txt", ".pdf", ".docx", ".rst", ".adoc"}
CODE_EXTS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".ps1", ".html", ".css", ".pine", ".sql", ".r", ".jl", ".go", ".rs", ".java", ".c", ".h", ".cpp"}
DATA_EXTS = {".json", ".csv", ".tsv", ".xml", ".log", ".ndjson"}
CONFIG_NAMES = {".gitignore", ".dockerignore", ".gitattributes"}
CONFIG_EXTS = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".example", ".webmanifest", ".tsbuildinfo"}
# Compatibility fallback for historical snapshots that predate the curated map.
# New areas are still enumerated; these annotations never determine file coverage.
AREA_DESCRIPTIONS = {
    "(root)": "Repository entrypoints, complete inventories and family build records.",
    "adapters": "Standalone adapters for recorded sleeve builds.",
    "adapters3": "The Aster adapter collection, paired with its sleeve variants.",
    "agentic-trade-desk": "Paper-desk engineering guide, offline skeleton and templates.",
    "aster_sleeves": "Aster entrypoints over the shared engine commons.",
    "config": "Versioned paper-only roster configuration; a snapshot, not current-runtime proof.",
    "desk3": "Packaged desk-engine modules, sleeves and portfolio branches.",
    "docs": "Catalogs, strategy accounting, recreation contracts, verification and research.",
    "educational": "Preserved standalone educational engine packages and their boundaries.",
    "engines": "Shared-engine copies, bridges, configuration snapshot and sanitization provenance.",
    "indicator": "Indicator algorithm contracts linked to the Pine sources.",
    "integration": "Integration adapters and their recorded wiring guide.",
    "laz_sleeves": "Lazarus entrypoints over the shared engine commons.",
    "master": "Externally mirrored terminal assets and dated data; check producer clocks. Mirror updates may replace this directory wholesale.",
    "packages": "Whole contributed packages retained with source identity and version distinctions.",
    "pine": "Pine Script sources for the recorded indicator contracts.",
    "proof": "Historical install receipts; their scopes and dates bound what they demonstrate.",
    "psychology-engine": "Standalone market-psychology research and reference implementation.",
    "research": "Preserved standalone studies, documents and practice archives.",
    "sleeves": "Strategy implementation copies, grouped by family and standalone modules.",
    "strategies": "Strategy cards; the catalog is one collection within the repository.",
    "terminal-lineup": "Tool-site snapshots, forecast research, grading code and build records.",
    "tests": "Repository-level test sources; executing a test is separate from reading it.",
    "tools": "Offline navigation and inventory tools for readers and maintainers.",
}


def extension_of(path):
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    if name.startswith(".") and name.count(".") == 1:
        return name.lower()
    return "." + name.rsplit(".", 1)[-1].lower()


def kind_of(path):
    name = path.rsplit("/", 1)[-1].lower()
    ext = extension_of(path)
    parts = path.lower().split("/")
    if "tests" in parts or "test" in parts or name.startswith(("test_", "test-")) or "_test." in name or name.endswith("_tests.py"):
        return "test"
    if ext in IMAGE_EXTS or ext == ".svg": return "image"
    if name in CONFIG_NAMES or ext in CONFIG_EXTS: return "config"
    if ext in ARCHIVE_EXTS: return "archive"
    if ext in DOC_EXTS: return "document"
    if ext in CODE_EXTS: return "code"
    if ext in DATA_EXTS: return "data"
    return "other"


def area_of(path):
    return path.split("/", 1)[0] if "/" in path else "(root)"


def directory_of(path):
    return path.rsplit("/", 1)[0] if "/" in path else ""


def valid_path(path):
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or any(ord(c) < 32 for c in path):
        raise ValueError("Invalid repository-relative path")
    if any(part in ("", ".", "..", ".git") for part in path.split("/")):
        raise ValueError("Unsafe repository-relative path: " + path)
    return path


def validate_tree(tree_entries):
    if not isinstance(tree_entries, list):
        raise ValueError("tree must be a list of complete Git tree entries")
    seen = set()
    blobs = []
    for e in tree_entries:
        if not isinstance(e, dict): raise ValueError("Malformed tree entry")
        path = valid_path(e.get("path"))
        if path in seen: raise ValueError("Duplicate tree path: " + path)
        seen.add(path)
        if e.get("type") == "tree": continue
        if e.get("type") != "blob":
            raise ValueError("Unsupported non-blob entry (submodule coverage is not implicit): " + path)
        if not isinstance(e.get("sha"), str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", e["sha"]):
            raise ValueError("Invalid or missing blob hash: " + path)
        if not isinstance(e.get("size"), int) or isinstance(e["size"], bool) or e["size"] < 0:
            raise ValueError("Invalid or missing blob size: " + path)
        if e.get("mode", "100644") not in ("100644", "100755", "120000"):
            raise ValueError("Unsupported blob mode: " + path)
        blobs.append(e)
    paths = {e["path"] for e in blobs}
    for path in paths:
        if any(str(parent) in paths for parent in PurePosixPath(path).parents if str(parent) != "."):
            raise ValueError("File/directory path collision: " + path)
    return blobs


def build_entries(tree_entries):
    blobs = validate_tree(tree_entries)
    by_path = {e["path"]: e for e in blobs}
    entries = []
    for path in sorted(set(by_path) | set(SELF_PATHS)):
        e = by_path.get(path, {})
        entry = {"path": path, "size_bytes": e.get("size"), "sha": e.get("sha"), "extension": extension_of(path), "top_level_area": area_of(path), "directory": directory_of(path), "kind": kind_of(path)}
        if path in SELF_PATHS:
            entry.update(size_bytes=None, sha=None, self=True)
        entries.append(entry)
    return entries


def build_index(tree_entries, head_sha, generated_at, owner, repo, source=None):
    if head_sha is not None and (not isinstance(head_sha, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head_sha)):
        raise ValueError("Invalid indexed commit hash")
    if head_sha is None and (source or {}).get("mode") != "git-index":
        raise ValueError("Only an explicitly staged inventory may omit its commit")
    try:
        stamp = datetime.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if stamp.utcoffset() is None: raise ValueError("timezone required")
    except (AttributeError, TypeError, ValueError):
        raise ValueError("Source timestamp must be ISO8601 with a timezone") from None
    entries = build_entries(tree_entries)
    per_area = Counter(e["top_level_area"] for e in entries)
    per_area_bytes = Counter()
    for e in entries: per_area_bytes[e["top_level_area"]] += e["size_bytes"] or 0
    result = {"schema_version": SCHEMA_VERSION, "repository": f"{owner}/{repo}", "generated_at": generated_at, "indexed_commit": head_sha, "totals": {"files": len(entries), "bytes": sum(per_area_bytes.values())}, "per_area_counts": dict(sorted(per_area.items())), "per_area_bytes": dict(sorted(per_area_bytes.items())), "files": entries}
    if source: result["source"] = source
    return result


def sub_counts(entries, prefix, depth):
    counts = Counter()
    for e in entries:
        if e["path"].startswith(prefix):
            rest = e["path"][len(prefix):].split("/")
            counts["/".join(rest[:depth]) if len(rest) > 1 else "(files)"] += 1
    return counts


def _link(path, label=None):
    return f"[{label or path}]({urllib.parse.quote(path, safe='/#.-_')})"


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def validate_navigation(navigation, entries):
    if navigation is None: return
    if navigation.get("schema_version") != 1 or not isinstance(navigation.get("areas"), dict):
        raise ValueError("Navigation map requires schema_version1 and an areas object")
    paths = {e["path"] for e in entries}
    for area, row in navigation["areas"].items():
        if not isinstance(row, dict) or not isinstance(row.get("summary"), str) or not isinstance(row.get("entrypoints"), list):
            raise ValueError("Malformed navigation area: " + area)
        for entrypoint in row["entrypoints"]:
            path = urllib.parse.unquote(entrypoint.split("#", 1)[0]).rstrip("/")
            if path not in paths and not any(p.startswith(path + "/") for p in paths):
                raise ValueError("Navigation entrypoint absent from selected source: " + entrypoint)


def _collection_entries(index, navigation, prefix):
    paths = {e["path"] for e in index["files"]}
    counts = sub_counts(index["files"], prefix, 1)
    routes = (navigation or {}).get("routes", [])
    for name, count in sorted(counts.items()):
        if name == "(files)": continue
        directory = prefix + name + "/"
        candidates = []
        for route in routes:
            for item in route.get("reading_order", []):
                path = item.get("path", "").split("#", 1)[0]
                if path in paths and path.startswith(directory) and path not in candidates:
                    candidates.append(path)
        if not candidates:
            members = sorted(p for p in paths if p.startswith(directory))
            preferred = ("README.md", "REPORT.md", "report.md", "FORMATION.md", "ANALYSIS.md", "ENGINE-DESIGN.md")
            candidates = [p for n in preferred for p in members if p.rsplit("/", 1)[-1] == n]
        yield directory, count, candidates[:4]


def render_markdown(index, navigation=None):
    validate_navigation(navigation, index["files"])
    source = index.get("source", {})
    lines = ["# Repository index", "", "The complete measured file inventory and collection map. [INDEX.json](INDEX.json) is the machine-readable twin; [docs/REPOSITORY-MAP.json](docs/REPOSITORY-MAP.json) supplies curated meanings and task routes when present. No catalog or prose page substitutes for the full inventory.", "", f"Total files indexed: {index['totals']['files']}", ""]
    if index["indexed_commit"]:
        lines.append(f"Indexed commit: `{index['indexed_commit']}`. Source commit timestamp: {index['generated_at']}.")
    else:
        lines.append(f"**Staged candidate, not a published commit.** Base commit: `{source.get('base_commit') or 'unborn'}`. Timestamp inherited from that base: {index['generated_at']}.")
    if source.get("tree_sha"):
        lines.append(f"Exact source Git tree: `{source['tree_sha']}`. Inventory mode: `{source.get('mode', 'snapshot')}`.")
    lines.extend([f"Total indexed bytes: {index['totals']['bytes']} (only the two generated index outputs have null hashes and sizes).", "", "## What this repository is", "", "A public, versioned library of strategy cards, implementation copies, research studies, educational engines, terminal snapshots and paper-desk engineering guides. Its contents preserve multiple independent systems and historical states. A committed file or historical receipt does not prove a currently active service, feed, trading account, deployment or profitable strategy.", "", "## Reading order and first useful actions", "", "1. [START-HERE.md](START-HERE.md): the entry protocol and evidence boundaries.", "2. This map, then the relevant [ROADMAP.md](ROADMAP.md) topic and area entrypoint.", "3. [docs/LLM-OPERATING-GUIDE.md](docs/LLM-OPERATING-GUIDE.md): source-to-answer workflows, examples and bounded checks.", "4. Use the offline navigator to find exact paths or build a bounded reading packet. It reads repository content; it does not activate any service.", "", "```sh", 'python3 tools/repo_navigator.py search "tensor"', 'python3 tools/repo_navigator.py route "forecast engines"', "python3 tools/repo_navigator.py check", "```", "", "For manual readers, [docs/CATALOG.json](docs/CATALOG.json) catalogs strategy cards; [docs/ALL-SLEEVES.json](docs/ALL-SLEEVES.json) is the broader deduplicated accounting; [docs/SLEEVES.json](docs/SLEEVES.json) describes the committed roster. They have different denominators and purposes.", "", "## Map of every top-level area", "", "Counts and bytes below are derived from the selected Git tree, not copied from older prose. Curated descriptions do not determine coverage: newly added areas remain visible even before a route is written.", "", "| Area | Files | Bytes | Purpose and entrypoints |", "| --- | ---: | ---: | --- |"])
    areas = (navigation or {}).get("areas", {})
    paths = {e["path"] for e in index["files"]}
    for area, count in sorted(index["per_area_counts"].items()):
        row = areas.get(area, {})
        summary = row.get("summary", AREA_DESCRIPTIONS.get(area, "New or unclassified area: inspect its files and add a curated route."))
        entrypoints = row.get("entrypoints", [])
        if not entrypoints and area != "(root)":
            entrypoints = [p for p in (area + "/README.md", area + "/AREA.md") if p in paths]
        details = _cell(summary)
        if entrypoints: details += " " + " · ".join(_link(p) for p in entrypoints)
        if row.get("evidence_status"): details += " " + _cell(row["evidence_status"])
        lines.append(f"| {area} | {count} | {index['per_area_bytes'].get(area, 0)} | {details} |")
    lines.extend(["", "## Packages by contributing desk", "", "Packages are retained whole. A package's README, manifest and source version determine its scope; the most recent directory name is not authority to replace another implementation.", ""])
    for author in sorted(sub_counts(index["files"], "packages/", 1)):
        if author == "(files)": continue
        counts = sub_counts(index["files"], f"packages/{author}/", 1)
        links = [f"{_link('packages/' + author + '/' + name + '/', name)} ({count})" for name, count in sorted(counts.items()) if name != "(files)"]
        lines.append(f"- **{author}**: " + ", ".join(links) + ".")
    lines.extend(["", "## Research collections, enumerated from the tree", "", "These are independent source collections unless their own records establish a lineage. Coverage, conclusions and adoption status belong to each study's dated evidence. Listing a collection does not claim a fresh scientific validation.", ""])
    for prefix in ("docs/research/", "research/"):
        for directory, count, candidates in _collection_entries(index, navigation, prefix):
            tail = " Read: " + " · ".join(_link(p) for p in candidates) if candidates else " Open the directory, then search INDEX.json for its files."
            lines.append(f"- {_link(directory)} — {count} files." + tail)
    lines.extend(["", "## Educational and reference implementations", "", "- [psychology-engine/README.md](psychology-engine/README.md): the standalone psychology research/reference package, release notes and offline checks.", "- [docs/research/psychology-engine-2026-10-30/](docs/research/psychology-engine-2026-10-30/): the separate nine-gauge study and implementation snapshot. Do not merge their status or evidence."])
    for directory, count, candidates in _collection_entries(index, navigation, "educational/"):
        lines.append(f"- {_link(directory)} — {count} files. " + " · ".join(_link(p) for p in candidates))
    lines.extend(["", "## Terminal, implementation and evidence routes", "", "- [terminal-lineup/THE-70-TOOLS.md](terminal-lineup/THE-70-TOOLS.md) and [terminal-lineup/FORECAST-ENGINES-30.md](terminal-lineup/FORECAST-ENGINES-30.md) retain historical titles; the tree and registry determine the captured contents."])
    for prefix, meaning in [("terminal-lineup/site/", "tool pages, assets, source and dated data"), ("terminal-lineup/forecast/", "forecast implementations, registry, grading and tests"), ("terminal-lineup/records/", "historical build and source-discovery records"), ("master/", "externally mirrored terminal assets and snapshots")]:
        n = sum(e["path"].startswith(prefix) for e in index["files"])
        lines.append(f"- {_link(prefix)} — {n} files: {meaning}.")
    lines.extend(["- [docs/VERIFY.md](docs/VERIFY.md), [docs/verify/](docs/verify/) and [proof/install/](proof/install/): source attribution and historical receipts. Check the captured source, date and exact claim before relying on them.", "- [engines/SANITIZATION-NOTE.md](engines/SANITIZATION-NOTE.md): disclosed representation differences in copied source.", "- [agentic-trade-desk/README.md](agentic-trade-desk/README.md): paper-desk architecture, offline skeleton and operational guide; it does not authorize an account or order.", "- [ROADMAP.md](ROADMAP.md): the cross-directory Tensor route and other source-to-claim reading sequences.", "", "## Coverage and preservation contract", "", f"INDEX.json has {index['totals']['files']} sorted file entries. All source blobs are included with exact Git blob hashes and byte sizes. Only `INDEX.md` and `INDEX.json` are generated self entries, with null hashes/sizes; `tools/build_repo_index.py` is ordinary hashed source. When an output is absent from the selected source tree, its marked self entry anticipates the generated file and is not a claim it was already committed.", "", "A file inventory proves paths and byte identity, not semantic correctness or runtime behavior. Unsupported submodules, truncated snapshots, duplicate paths, unsafe paths and missing hashes/sizes fail explicitly rather than yielding a partial inventory described as complete. The index does not enumerate files inside archives; use their own manifests and the artifact's documented extraction procedure.", "", "## Reproduce and check", "", "```sh", "# Exact committed source; no GitHub connection required.", "python3 tools/build_repo_index.py --local-repo . --ref HEAD --out-dir .", "# Read-only comparison: catches missing/new paths, changed bytes, counts and prose drift.", "python3 tools/build_repo_index.py --local-repo . --ref HEAD --out-dir . --check", "# Pre-commit candidate; does not mutate the Git index or write Git objects.", "python3 tools/build_repo_index.py --local-repo . --staged --out-dir /tmp/test-index", "# Original API and offline-snapshot modes remain available.", "python3 tools/build_repo_index.py --branch main --out-dir /tmp/test-index-api", "python3 tools/build_repo_index.py --tree-json snapshot.json --out-dir /tmp/test-index-snapshot", "```", "", "For a published inventory, commit source changes first, generate from that pinned source commit, and then commit the two generated outputs. The later index-only commit may have a different HEAD while every non-self source hash still matches; `--check` verifies those hashes instead of requiring an impossible self-referential commit ID. An explicit `--map-file` can supply annotations for a saved snapshot. Generation never pushes, posts, activates services or changes trading state.", ""])
    return "\n".join(lines)


def fetch_json(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "build-repo-index/2.0"})
    if token: req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def _git(repo, *args, input=None):
    p = subprocess.run(["git", "-C", str(repo), *args], input=input, capture_output=True)
    if p.returncode:
        raise ValueError("Git source read failed: " + " ".join(args[:2]))
    return p.stdout


def tree_hash(entries, algorithm="sha1"):
    root = {}
    for e in validate_tree(entries):
        node = root
        parts = e["path"].split("/")
        for part in parts[:-1]: node = node.setdefault(part, {})
        node[parts[-1]] = (e.get("mode", "100644"), e["sha"])
    def digest(node):
        data = bytearray()
        for name, value in sorted(node.items(), key=lambda item: (item[0] + ("/" if isinstance(item[1], dict) else "")).encode("utf-8")):
            mode, sha = ("40000", digest(value)) if isinstance(value, dict) else value
            data.extend(mode.encode() + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(sha))
        return hashlib.new(algorithm, b"tree " + str(len(data)).encode() + b"\0" + data).hexdigest()
    return digest(root)


def local_snapshot(repo, ref="HEAD", staged=False):
    base = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", ref + "^{commit}"], capture_output=True)
    head = base.stdout.decode().strip() if base.returncode == 0 else None
    if not head and not staged: raise ValueError("Selected ref is not a commit")
    timestamp = _git(repo, "show", "-s", "--format=%cI", head).decode().strip() if head else "1970-01-01T00:00:00Z"
    entries = []
    if staged:
        rows = _git(repo, "ls-files", "--stage", "-z").split(b"\0")
        for row in rows:
            if not row: continue
            meta, path = row.split(b"\t", 1)
            mode, sha, stage = meta.decode().split()
            if stage != "0": raise ValueError("Unmerged index entry; resolve before inventory")
            entries.append({"path": path.decode("utf-8"), "type": "blob" if mode != "160000" else "commit", "mode": mode, "sha": sha})
        hashes = sorted({e["sha"] for e in entries})
        sizes = {}
        if hashes:
            raw = _git(repo, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input=("\n".join(hashes) + "\n").encode())
            for line in raw.decode().splitlines():
                sha, kind, size = line.split()
                if kind != "blob": raise ValueError("Non-blob staged object is outside inventory scope")
                sizes[sha] = int(size)
        for entry in entries: entry["size"] = sizes[entry["sha"]]
        algorithm = _git(repo, "rev-parse", "--show-object-format").decode().strip()
        tree_sha = tree_hash(entries, algorithm)
    else:
        for row in _git(repo, "ls-tree", "-r", "-l", "-z", "--full-tree", head).split(b"\0"):
            if not row: continue
            meta, path = row.split(b"\t", 1)
            mode, kind, sha, size = meta.decode().split()
            entries.append({"path": path.decode("utf-8"), "type": kind, "mode": mode, "sha": sha, "size": int(size) if size != "-" else None})
        tree_sha = _git(repo, "rev-parse", head + "^{tree}").decode().strip()
    validate_tree(entries)
    navigation = None
    match = next((e for e in entries if e["path"] == MAP_PATH), None)
    if match:
        navigation = json.loads(_git(repo, "cat-file", "blob", match["sha"]).decode("utf-8"))
    return {"head": None if staged else head, "generated_at": timestamp, "tree": entries, "navigation_map": navigation, "source": {"mode": "git-index" if staged else "git-ref", "base_commit": head, "tree_sha": tree_sha}}


def check_saved(index, navigation, out_dir):
    errors = []
    try:
        saved = json.loads((Path(out_dir) / "INDEX.json").read_text(encoding="utf-8"))
        markdown = (Path(out_dir) / "INDEX.md").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return ["Saved index cannot be read: " + type(exc).__name__]
    for field in ("schema_version", "repository", "totals", "per_area_counts", "per_area_bytes", "files"):
        if saved.get(field) != index[field]: errors.append("Stale or invalid field: " + field)
    try:
        # Validate metadata as well as the inventory. Never accept an arbitrary
        # commit label or an undated saved result merely because its paths match.
        build_index([], saved["indexed_commit"], saved["generated_at"], "", "", saved.get("source"))
        source = saved.get("source", {})
        if source:
            if source.get("mode") not in ("git-ref", "git-index", "github-api"):
                raise ValueError("Unknown saved source mode")
            if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source.get("tree_sha", "")):
                raise ValueError("Invalid saved source tree")
            if source.get("mode") != "git-index" and source.get("base_commit") != saved["indexed_commit"]:
                raise ValueError("Saved source commit disagrees with indexed commit")
    except (KeyError, TypeError, ValueError):
        errors.append("Saved provenance is malformed")
    # The source commit may legitimately precede an index-only commit. Content
    # matching above is strict; the saved provenance remains visible, not rewritten.
    try:
        if markdown != render_markdown(saved, navigation): errors.append("INDEX.md differs from the deterministic rendering")
    except (KeyError, TypeError, ValueError): errors.append("Saved index structure cannot be rendered")
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default=DEFAULT_OWNER)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--branch")
    sources = ap.add_mutually_exclusive_group()
    sources.add_argument("--tree-json")
    sources.add_argument("--local-repo")
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--map-file", help="Explicit curated map for an offline snapshot")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--check", action="store_true", help="Check saved outputs without rewriting files")
    args = ap.parse_args(argv)
    if args.staged and not args.local_repo: ap.error("--staged requires --local-repo")
    if args.staged and args.ref != "HEAD": ap.error("--staged uses the current index and its HEAD base; do not combine with another --ref")
    if args.branch and (args.local_repo or args.tree_json): ap.error("--branch applies only to the API source")
    try:
        if args.local_repo:
            snap = local_snapshot(args.local_repo, args.ref, args.staged)
        elif args.tree_json:
            snap = json.loads(Path(args.tree_json).read_text(encoding="utf-8"))
        else:
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            prefix = f"{API_BASE}/repos/{urllib.parse.quote(args.owner, safe='')}/{urllib.parse.quote(args.repo, safe='')}"
            branch = args.branch or fetch_json(prefix, token)["default_branch"]
            commit = fetch_json(prefix + "/commits/" + urllib.parse.quote(branch, safe=""), token)
            tree = fetch_json(prefix + "/git/trees/" + commit["sha"] + "?recursive=1", token)
            if tree.get("truncated"): raise ValueError("Tree response truncated; refusing partial inventory")
            navigation = None
            entry = next((e for e in tree["tree"] if e["path"] == MAP_PATH), None)
            if entry:
                blob = fetch_json(prefix + "/git/blobs/" + entry["sha"], token)
                if blob.get("encoding") != "base64": raise ValueError("Unexpected navigation-map blob encoding")
                navigation = json.loads(base64.b64decode(blob["content"]).decode("utf-8"))
            snap = {"head": commit["sha"], "generated_at": commit["commit"]["committer"]["date"], "tree": tree["tree"], "navigation_map": navigation, "source": {"mode": "github-api", "base_commit": commit["sha"], "tree_sha": tree["sha"]}}
        if snap.get("truncated"): raise ValueError("Saved snapshot is truncated; refusing partial inventory")
        navigation = json.loads(Path(args.map_file).read_text(encoding="utf-8")) if args.map_file else snap.get("navigation_map")
        index = build_index(snap["tree"], snap["head"], snap["generated_at"], args.owner, args.repo, snap.get("source"))
        validate_navigation(navigation, index["files"])
        if args.check:
            errors = check_saved(index, navigation, args.out_dir)
            if args.local_repo and not errors:
                saved = json.loads((Path(args.out_dir) / "INDEX.json").read_text(encoding="utf-8"))
                if saved["indexed_commit"] is not None:
                    recorded = local_snapshot(args.local_repo, saved["indexed_commit"])
                    recorded_index = build_index(recorded["tree"], recorded["head"], recorded["generated_at"], args.owner, args.repo, recorded["source"])
                    if recorded_index["files"] != saved["files"]:
                        errors.append("Saved commit does not contain the indexed source blobs")
                    recorded_time = datetime.datetime.fromisoformat(recorded["generated_at"].replace("Z", "+00:00"))
                    saved_time = datetime.datetime.fromisoformat(saved["generated_at"].replace("Z", "+00:00"))
                    if recorded_time != saved_time:
                        errors.append("Saved timestamp differs from its source commit")
                    if saved.get("source", {}).get("tree_sha", recorded["source"]["tree_sha"]) != recorded["source"]["tree_sha"]:
                        errors.append("Saved source tree differs from its source commit")
            print(json.dumps({"status": "FAIL" if errors else "PASS", "checked_files": index["totals"]["files"], "source_commit": index["indexed_commit"], "errors": errors}, sort_keys=True))
            return 1 if errors else 0
        markdown = render_markdown(index, navigation)
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "INDEX.json").write_text(json.dumps(index, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        (out / "INDEX.md").write_text(markdown, encoding="utf-8")
        print(json.dumps({"indexed_files": index["totals"]["files"], "indexed_commit": index["indexed_commit"], "source": index.get("source")}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
