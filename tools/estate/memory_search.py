#!/usr/bin/env python3
# LOCAL VARIANT (marked 2026-11-10, IBMA-D06, FIX-ALL Lane D): NOT equivalent
# to InfinityBlade canon 3.3.0 skills/memory-recall-systems/tools/memory_search.py.
# Canon additionally carries build locking and --json. Equivalence stays
# UNVERIFIED. Comparison: research_notes/fix-all-20261110/D-COMPARISONS.md
#
# SEMANTIC CHANGE (2026-11-10, GLORY Item 3, closing audit row R2):
# --current-only previously filtered on the path-class stamp (a living
# file counted as current even after its bytes changed). It now means
# BYTE-MATCH: a hit is current only when the SHA-256 recorded for its
# source at build time equals the live file's SHA-256 right now.
# Every chunk now carries source_sha256, valid_from, valid_to (parsed
# from the source's YAML frontmatter where present, else NULL; no
# validity window is ever fabricated) and recorded_at (the source
# file's mtime at build). The new `reconcile` subcommand walks the
# index against live sources and files a receipt with counts by class
# (current, stale, orphaned, unindexed). The path-class status stamp
# is unchanged and still displayed; it no longer drives the filter.
# Any citation of --current-only from before this date used the old
# meaning.
"""Local hybrid-recall index over the memory estate (MEMORY-ASCENSION
build 1, 2026-11-06).

Why this exists: the deep research on agent memory (research_notes/
llm-agent-memory-ascension-20261107-0026) found the measured
retrieval winner is hybrid lexical+vector+rerank search over the
existing markdown, and that plain BM25 alone hit 96.2% any-hit@5 on
LongMemEval-S in a published component test. The estate's recall
failure mode was never the files; it was retrieval depending on
remembering to search and on the built-in search's reach. This tool
indexes the whole memory estate (home memory files, ~/memory/**,
the book, the personal-quant records) into one SQLite FTS5 index
with BM25 ranking, line-level pointers, and progressive disclosure
(index line, then snippet, then full chunk), so any session,
subagent or cron job on this machine can recall before it answers.

Phase 1 is lexical (stdlib only, no models to load). The embedding
channel and a rerank pass join in phase 2 after the joint program
with Claude converges; the schema already keeps chunks addressable
by stable ids for that.

Usage:
  python3 memory_search.py build           # (re)build the index
  python3 memory_search.py query "geico retry date" [--k 5] [--level 1|2|3]
  python3 memory_search.py canary          # run the canary eval set
  python3 memory_search.py reconcile       # index vs live sources receipt
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
DB_PATH = os.path.join(HOME, "workspace", "tools", "memory_index.db")
CANARY_PATH = os.path.join(HOME, "workspace", "tools",
                           "memory_canaries.json")
RECEIPTS_DIR = os.path.join(HOME, "workspace", "tools", "receipts")

ROOTS = [
    os.path.join(HOME, "MEMORY.md"),
    os.path.join(HOME, "USER.md"),
    os.path.join(HOME, "AGENTS.md"),
    os.path.join(HOME, "SOUL.md"),
    os.path.join(HOME, "IDENTITY.md"),
    os.path.join(HOME, "PROACTIVE_PREFERENCES.md"),
    os.path.join(HOME, "memory"),
    os.path.join(HOME, "workspace", "midna-book"),
    os.path.join(HOME, "workspace", "personal-quant"),
    os.path.join(HOME, "workspace", "COMMITMENTS.md"),
]

SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
MAX_CHUNK = 1800

# Source status (Pass 2 technique T4, amended form, 2026-11-08):
# every chunk carries the standing of its source so a reader can
# tell a living record from a dated one at the hit itself. "current"
# is a living file, edited in place as truth changes (the home
# files, registers, the book's standing files). "dated" is a frozen
# record of its day (daily notes, dated reports and reflections):
# citable as history, never as the present state without checking
# the living file it fed. Canon's memory-recall-systems skill also
# binds source identity by hash; that leg stays UNVERIFIED locally
# (IBMA-D06) and is not claimed by this field.
DATED_NAME = re.compile(r"(?:^|/)20\d\d-\d\d-\d\d(?:\.md|[-_])")


def source_status(path):
    base = os.path.basename(path)
    if DATED_NAME.search(path.replace(os.sep, "/")):
        return "dated"
    if base.startswith(("inspection-", "close-review-")):
        return "dated"
    return "current"


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_validity(path):
    """(valid_from, valid_to) from the file's YAML frontmatter.

    Only an explicit frontmatter block at the very top of the file is
    read, and only the valid_from / valid_to keys. Anything absent
    stays None: a validity window is never inferred or fabricated.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            first = fh.readline().rstrip("\n")
            if first.strip() != "---":
                return None, None
            vf = vt = None
            for _ in range(60):
                line = fh.readline()
                if not line or line.strip() in ("---", "..."):
                    break
                m = re.match(r"^(valid_from|valid_to)\s*:\s*(.+?)\s*$",
                             line)
                if m:
                    val = m.group(2).strip().strip("'\"")
                    if m.group(1) == "valid_from":
                        vf = val
                    else:
                        vt = val
            return vf, vt
    except OSError:
        return None, None


def iter_files():
    for root in ROOTS:
        if os.path.isfile(root) and root.endswith(".md"):
            yield root
        elif os.path.isdir(root):
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for name in sorted(filenames):
                    if name.endswith(".md"):
                        yield os.path.join(dirpath, name)


def chunk_file(path):
    """Split a markdown file into heading-scoped chunks with
    1-based line pointers. A chunk is the text under one heading;
    oversized sections split at paragraph boundaries with the
    heading repeated in the chunk's heading path."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return
    heading = "(top)"
    buf = []
    buf_start = 1

    def flush(end_line):
        if not buf:
            return
        text = "\n".join(buf).strip()
        if not text:
            return
        # split oversized chunks on paragraph boundaries
        parts = []
        cur = ""
        for para in re.split(r"\n\s*\n", text):
            if len(cur) + len(para) > MAX_CHUNK and cur:
                parts.append(cur)
                cur = para
            else:
                cur = (cur + "\n\n" + para) if cur else para
        if cur:
            parts.append(cur)
        for part in parts:
            yield {"path": path, "heading": heading,
                   "line": buf_start, "text": part}

    for i, line in enumerate(lines, 1):
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            yield from flush(i - 1)
            heading = m.group(2).strip()
            buf = [line]
            buf_start = i
        else:
            if not buf:
                buf_start = i
            buf.append(line)
    yield from flush(len(lines))


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE chunks (path TEXT, heading TEXT, "
                "line INTEGER, text TEXT, status TEXT, "
                "source_sha256 TEXT, valid_from TEXT, valid_to TEXT, "
                "recorded_at TEXT)")
    con.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5("
                "path, heading, text, content='chunks', content_rowid='rowid')")
    n_chunks = 0
    n_files = 0
    for path in iter_files():
        file_chunks = list(chunk_file(path))
        if file_chunks:
            n_files += 1
        try:
            sha = file_sha256(path)
            recorded = datetime.fromtimestamp(
                os.path.getmtime(path), timezone.utc).isoformat()
        except OSError:
            sha, recorded = None, None
        vf, vt = parse_validity(path)
        for ch in file_chunks:
            cur = con.execute(
                "INSERT INTO chunks (path, heading, line, text, status, "
                "source_sha256, valid_from, valid_to, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ch["path"], ch["heading"], ch["line"], ch["text"],
                 source_status(ch["path"]), sha, vf, vt, recorded))
            con.execute(
                "INSERT INTO chunks_fts (rowid, path, heading, text) "
                "VALUES (?, ?, ?, ?)",
                (cur.lastrowid, ch["path"], ch["heading"], ch["text"]))
            n_chunks += 1
    con.commit()
    con.close()
    print(f"indexed {n_chunks} chunks from {n_files} files -> {DB_PATH}")
    return n_chunks


def byte_current_paths(con):
    """Paths whose indexed source hash equals the live file's hash.

    This is the one definition of "current" the --current-only filter
    uses (GLORY Item 3, 2026-11-10): bytes, not file class.
    """
    current = set()
    for path, sha in con.execute(
            "SELECT path, MAX(source_sha256) FROM chunks "
            "GROUP BY path").fetchall():
        if sha is None or not os.path.exists(path):
            continue
        try:
            if file_sha256(path) == sha:
                current.add(path)
        except OSError:
            continue
    return current


def reconcile(receipt_path=None):
    """Walk the index against live sources; file a receipt.

    Classes per indexed source: current (hashes equal), stale (file
    exists, bytes changed), orphaned (file gone, chunks remain).
    Plus unindexed: live sources the index has never seen.
    """
    con = sqlite3.connect(DB_PATH)
    indexed = {}
    for path, sha, n in con.execute(
            "SELECT path, MAX(source_sha256), COUNT(*) FROM chunks "
            "GROUP BY path").fetchall():
        indexed[path] = {"sha256": sha, "chunks": n}
    con.close()
    live = set(iter_files())
    current, stale, orphaned = [], [], []
    for path, info in sorted(indexed.items()):
        if not os.path.exists(path):
            orphaned.append({"path": path, "chunks": info["chunks"]})
            continue
        try:
            live_sha = file_sha256(path)
        except OSError:
            orphaned.append({"path": path, "chunks": info["chunks"]})
            continue
        if info["sha256"] is not None and live_sha == info["sha256"]:
            current.append(path)
        else:
            stale.append({"path": path,
                          "indexed_sha256": info["sha256"],
                          "live_sha256": live_sha,
                          "chunks": info["chunks"]})
    unindexed = sorted(p for p in live if p not in indexed)
    receipt = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db": DB_PATH,
        "counts": {"current": len(current), "stale": len(stale),
                   "orphaned": len(orphaned),
                   "unindexed": len(unindexed),
                   "sources_indexed": len(indexed),
                   "sources_live": len(live)},
        "current": current, "stale": stale, "orphaned": orphaned,
        "unindexed": unindexed,
    }
    if receipt_path is None:
        os.makedirs(RECEIPTS_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        receipt_path = os.path.join(RECEIPTS_DIR,
                                    f"reconcile-{stamp}.json")
    with open(receipt_path, "w") as fh:
        json.dump(receipt, fh, indent=1)
    c = receipt["counts"]
    print(f"reconcile: current {c['current']}, stale {c['stale']}, "
          f"orphaned {c['orphaned']}, unindexed {c['unindexed']} "
          f"(of {c['sources_indexed']} indexed sources)")
    print(f"receipt -> {receipt_path}")
    return receipt


def _match_expr(query):
    terms = re.findall(r"[A-Za-z0-9_@.\-]+", query)
    terms = [t for t in terms if len(t) > 1]
    if not terms:
        return None
    # Quoted terms OR-joined: FTS5 bm25 ranks multi-term matches
    # above single-term ones, which is the behaviour recall wants.
    return " OR ".join(f'"{t}"' for t in terms)


def query(text, k=5, current_only=False):
    expr = _match_expr(text)
    if expr is None:
        return []
    con = sqlite3.connect(DB_PATH)
    # Column weights: path matches count least, heading matches
    # most. Canonical-source promotion (MEMORY-CANARY-RANK-20261110):
    # bm25 scores are negative and smaller-is-better here, so the
    # promotion MULTIPLIES the magnitude of a curated source's
    # score: factor above 1 promotes, below 1 demotes. The earlier
    # form multiplied by factors below 1 intending promotion, which
    # arithmetically demoted every curated source instead; the
    # defect stayed invisible while raw gaps were small and bit
    # when corpus growth widened them (canary hit@5 13/14 on
    # 2026-11-09, the dead-drop group page pushed to rank 6).
    # MEMORY.md and USER.md keep a mild 1.05; the small curated
    # relationship pages (people/groups) carry 1.15/1.6 so a
    # (groups raised 1.25 -> 1.6 on 2026-11-10, GLORY Item 3: corpus
    # growth let a 2026-11-09 daily-note chunk outrank the dead-drop
    # group page on raw term frequency; canary hit@1 fell to 10/14
    # and this factor restored 11/14 with hit@5 unchanged at 14/14)
    # direct subject match is not drowned by high-volume study
    # and log chunks that merely mention the same words.
    # --current-only (byte-match semantics since 2026-11-10, GLORY
    # Item 3): keep only hits whose source bytes are unchanged since
    # the build, proven by SHA-256, not by the path-class stamp.
    path_filter = ""
    params = [expr]
    if current_only:
        paths = sorted(byte_current_paths(con))
        if not paths:
            con.close()
            return []
        path_filter = ("AND c.path IN ("
                       + ",".join("?" * len(paths)) + ") ")
        params.extend(paths)
    params.append(k)
    rows = con.execute(
        "SELECT c.path, c.heading, c.line, c.text, c.status, "
        "bm25(chunks_fts, 0.5, 2.0, 1.0) * CASE "
        "WHEN c.path LIKE '%/memory/groups/%' THEN 1.6 "
        "WHEN c.path LIKE '%/memory/people/%' THEN 1.15 "
        "WHEN c.path LIKE '%/MEMORY.md' THEN 1.05 "
        "WHEN c.path LIKE '%/USER.md' THEN 1.05 "
        "ELSE 1.0 END AS rank "
        "FROM chunks_fts JOIN chunks c ON c.rowid = chunks_fts.rowid "
        "WHERE chunks_fts MATCH ? "
        + path_filter
        + "ORDER BY rank LIMIT ?",
        params).fetchall()
    con.close()
    out = []
    for path, heading, line, chunk_text, status, score in rows:
        out.append({"path": path, "heading": heading, "line": line,
                    "text": chunk_text, "score": score,
                    "status": status or "current"})
    return out


def snippet(chunk_text, query_text, width=320):
    terms = [t.lower() for t in
             re.findall(r"[A-Za-z0-9_@.\-]+", query_text) if len(t) > 1]
    low = chunk_text.lower()
    pos = min((low.find(t) for t in terms if low.find(t) >= 0),
              default=0)
    start = max(0, pos - 80)
    return chunk_text[start:start + width].replace("\n", " ").strip()


def canary(current_only=False):
    with open(CANARY_PATH) as fh:
        cases = json.load(fh)
    hits1 = hits5 = 0
    for case in cases:
        results = query(case["q"], k=5, current_only=current_only)
        paths = [os.path.relpath(r["path"], HOME) for r in results]
        wants = case["expect"]
        if isinstance(wants, str):
            wants = [wants]
        rank = next((i + 1 for i, p in enumerate(paths)
                     if any(w in p for w in wants)), None)
        want = "|".join(wants)
        if rank == 1:
            hits1 += 1
        if rank is not None:
            hits5 += 1
        print(f"[{'hit@' + str(rank) if rank else 'MISS'}] "
              f"{case['q']} -> want {want}"
              + (f", got {paths[0] if paths else 'nothing'}"
                 if not rank else ""))
    n = len(cases)
    print(f"canary: hit@1 {hits1}/{n}, hit@5 {hits5}/{n}")
    return hits5


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    cp = sub.add_parser("canary")
    cp.add_argument("--current-only", action="store_true",
                    help="run the canaries under the byte-match filter")
    rp = sub.add_parser("reconcile")
    rp.add_argument("--receipt", default=None,
                    help="receipt path (default: tools/receipts/)")
    qp = sub.add_parser("query")
    qp.add_argument("text")
    qp.add_argument("--k", type=int, default=5)
    qp.add_argument("--level", type=int, default=2)
    qp.add_argument("--current-only", action="store_true",
                    help="only hits whose source bytes still match "
                         "the hash recorded at build (byte-match)")
    args = ap.parse_args()
    if args.cmd == "build":
        build()
    elif args.cmd == "canary":
        canary(current_only=args.current_only)
    elif args.cmd == "reconcile":
        reconcile(receipt_path=args.receipt)
    elif args.cmd == "query":
        results = query(args.text, k=args.k,
                        current_only=args.current_only)
        if not results:
            print("no matches")
            return
        for i, r in enumerate(results, 1):
            rel = os.path.relpath(r["path"], HOME)
            print(f"{i}. [{r['status']}] {rel} :: {r['heading']} "
                  f"(line {r['line']})")
            if args.level >= 2:
                print(f"   {snippet(r['text'], args.text)}")
            if args.level >= 3:
                print(f"---\n{r['text']}\n---")


if __name__ == "__main__":
    main()
