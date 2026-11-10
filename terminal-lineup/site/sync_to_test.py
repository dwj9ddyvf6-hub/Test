#!/usr/bin/env python3
"""Hourly sync: local terminal lineup -> public Test repo (gated route only).

Mirrors the included-file set of the original one-time save: site/**,
forecast/** (minus the live ledger), specs/**, oracle/**, records/**,
root Markdown files and root workflow scripts, under the repo prefix
terminal-lineup/. Excluded: the deep_store and psychology-engine trees,
caches, log files, lane state, runtime artifacts, and any file over
5 MB, except data.json, whose cap is 50 MB (R3 cure, 2026-11-02: the
5 MB cap silently unpublished eight pages whose subject IS their
data.json; the pages fetch that file by name, so a data.json under
the data cap publishes whole, never trimmed). Deletions are left alone.

For each included file the local git blob SHA is compared with the repo
blob SHA from a fresh recursive tree fetch; matches are skipped. Changed
authored text files (.py/.md/.js) redact first-name matches in memory
using the existing private PII gate pattern (neutral owner wording,
capitalization preserved at sentence and string starts); local files are
never modified. Other private fields, including surnames and email
addresses, remain subject to the fail-closed gate and cause a file to be
skipped if still present. The three cure-phase unfixable files (functional EDGAR
declaration strings and functional fixture data) are never sanitized or
uploaded. Any candidate that still matches a gate pattern after
sanitization (third-party data, functional strings) is skipped and
logged, never falsified. Uploads go through the PII-gated contents
helper only. After the content sync, INDEX.json and INDEX.md are
regenerated with the repo generator logic against the new tree and
uploaded when changed; a gate refusal on either is logged, not worked
around. One proof line is appended to the sync log per run.

Desk privacy gate (DESK-PRIVACY-20261103): the desk producer feed is
an internal-state payload. terminal_feed.json is refused by name
anywhere in the tree; any JSON under a desk/ directory is key-scanned
and refused fail-closed when it carries private account fields
(balances, buying power, equity, positions, money assigned, starting
capital); the desk page is refused while it reads the internal feed.
The .published-trees local snapshot tree is excluded from the sync
set entirely: it is a local publish artifact, not site content, and
its archived desk copies carried the same private fields. On
2026-11-03 the ungated sync re-published the raw desk payload over a
sanitized public copy; the blocker is
test_sync_desk_privacy_gate_20261103.py beside this script.

Usage: python3 sync_to_test.py [--dry-run]
Exit codes: 0 clean (gate-blocked skips are a logged, expected state),
2 truncated tree, 3 hard API error (including 403/429 rate stops),
4 zero-byte guard refusal (nothing published, file named),
5 stood down: another invocation already holds the single-flight
lock, so this one published nothing (cure SYNC-SINGLE-FLIGHT-
20261108: overlapping invocations raced each other on base blob
shas and the loser died on a 409; exactly one sync runs at a
time now, and the stand-down is named, never a hard API error).
The scoped route below waits for the lock instead of standing
down (cure SYNC-SCOPED-WAIT-20261109, see publish_scoped).
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import importlib.util
import json
import os
import re
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

GH_DIR = os.path.expanduser("~/workspace/.scratch-femto-mirror")
sys.path.insert(0, GH_DIR)
import ghapi  # noqa: E402
import pii_gate  # noqa: E402

ROOT = Path(os.path.expanduser("~/workspace/terminal-lineup"))
REPO_API = "/repos/dwj9ddyvf6-hub/Test"
REPO_PATH = "dwj9ddyvf6-hub/Test"
PREFIX = "terminal-lineup/"
SYNC_LOG = Path(os.path.expanduser(
    "~/workspace/research_notes/test-repo-index-20261031/SYNC-LOG.md"))
FIVE_MB = 5 * 1024 * 1024
DATA_JSON_CAP = 50 * 1024 * 1024  # R3 cure: see header docstring
AUTHORED_EXTS = {".py", ".md", ".js"}
UNFIXABLE = {
    "site/build_xbrl_route.py",
    "site/form4_footnotes.py",
    "forecast/tests/test_insider_record_20261030.py",
}

# Identifying patterns live only in the existing private gate dependency.
_FIRST_NAME_RX = dict(pii_gate.PATTERNS)["first_name"]


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _cap_needed(text: str, start: int) -> bool:
    if start == 0:
        return True
    if text[start - 1] == "\n":
        return True
    if text[start - 1] == '"':
        return True
    prev = text[:start].rstrip()
    return prev.endswith(".") or prev.endswith(":")


def sanitize(text: str) -> str:
    """Redact first names via the private gate; remaining PII fails closed."""
    def rep_name(m):
        replacement = "The owner" if _cap_needed(m.string, m.start()) \
            else "the owner"
        return replacement + ("'s" if m.group().lower().endswith("'s") else "")

    return _FIRST_NAME_RX.sub(rep_name, text)


def gate_hits(text: str) -> list:
    return [name for name, rx in pii_gate.PATTERNS if rx.search(text)]


def zero_byte_violations(changed: list, repo_sizes: dict) -> list:
    """Zero-byte publish guard (HUB-BLANK-20261102 cure).

    changed is [(rel, candidate_bytes)]; repo_sizes maps repo path
    -> current blob size. Returns one named violation per candidate
    that must never be published: (a) any zero-byte .html page file
    outright, and (b) any zero-byte file whose repo version is
    non-empty (a shrink-to-zero of published content). On
    2026-11-02 a writer killed mid-write truncated the hub to
    0 bytes and the unguarded sync published the empty file."""
    violations = []
    for rel, cand in changed:
        if len(cand) != 0:
            continue
        if rel.lower().endswith(".html"):
            violations.append(
                f"{rel}: zero-byte .html page refused outright")
        elif repo_sizes.get(PREFIX + rel, 0) > 0:
            violations.append(
                f"{rel}: zero-byte candidate would shrink the "
                f"non-empty repo version "
                f"({repo_sizes[PREFIX + rel]} bytes) to zero")
    return violations


def included_files() -> list:
    """The original save's included set, rebuilt from the local tree."""
    included = []

    def walk(base: Path):
        for p in sorted(base.rglob("*")):
            if p.is_dir():
                continue
            rel = str(p.relative_to(ROOT))
            size = p.stat().st_size
            parts = set(p.relative_to(ROOT).parts)
            if "__pycache__" in parts or ".pytest_cache" in parts:
                continue
            if ".published-trees" in parts:
                continue  # local publish snapshots, never site content
            if p.suffix == ".log":
                continue
            if p.name.endswith(".atomic-tmp"):
                continue  # refresh_hub atomic-write temp, never publish
            if p.name == "lane_state.json":
                continue
            if p.name in (".live-server.pid", "live-server.log",
                          "suite_out.txt", ".sync_to_test.lock"):
                continue
            if rel == "forecast/ledger.jsonl":
                continue
            if p.name == "data.json" and size > DATA_JSON_CAP:
                continue
            if p.name != "data.json" and size > FIVE_MB:
                continue
            included.append(rel)

    for d in ("site", "forecast", "specs", "oracle", "records"):
        walk(ROOT / d)
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and (p.suffix == ".md"
                            or (p.name.startswith("workflow")
                                and p.suffix == ".js")):
            included.append(p.name)
    return included


def fetch_head_and_tree():
    _, repo = ghapi.api("GET", REPO_API)
    branch = repo.get("default_branch", "main")
    _, head = ghapi.api("GET", f"{REPO_API}/commits/{branch}")
    sha = head["sha"]
    generated_at = head["commit"]["committer"]["date"]
    _, tree = ghapi.api(
        "GET", f"{REPO_API}/git/trees/{sha}?recursive=1")
    if tree.get("truncated"):
        raise SystemExit(2)
    blobs = {e["path"]: e for e in tree["tree"] if e["type"] == "blob"}
    return sha, generated_at, tree["tree"], blobs


TRANSPORT_ERRORS = (urllib.error.URLError,
                    http.client.HTTPException,
                    ConnectionError, TimeoutError, ssl.SSLError)


def _put_once(repo_path: str, payload: dict):
    """One PUT attempt through the gated helper, with a single
    transport retry (cure SYNC-PUT-TRANSPORT-20261109).

    ghapi.api converts HTTPError responses into ApiError but a
    transport failure (an SSLEOFError inside a URLError, a
    dropped connection, a reset) raises raw: no HTTP response
    ever existed, so there is no status to honor, and the
    PUT's outcome is unknown (it may have landed). On
    2026-11-09 the 19:12 ET sync died with exit 1 mid-publish
    on one such drop: files already landed, no index
    regeneration, no sync-log line, while the mirror wrote to
    the same repo through the same helper minutes later. The
    retry re-issues the PUT once, unchanged in content and
    base sha; ghapi fetches a fresh credential surrogate per
    call, so the retry rides a fresh connection. A second
    transport error raises, unchanged, so a genuinely dead
    route still fails loud. ApiError is never caught here, so
    every response-bearing outcome (401, 409, 422, 403)
    reaches put_file's own branches untouched: a 403 rate
    stop is never retried by this wrapper."""
    try:
        return ghapi.api(
            "PUT", f"{REPO_API}/contents/"
                   + urllib.parse.quote(repo_path), payload)
    except TRANSPORT_ERRORS as te:
        print(f"put_file {repo_path}: transport error "
              f"({type(te).__name__}: {te}); retrying the PUT "
              "once", flush=True)
        time.sleep(2)
        return ghapi.api(
            "PUT", f"{REPO_API}/contents/"
                   + urllib.parse.quote(repo_path), payload)


def put_file(repo_path: str, data: bytes, message: str,
             existing_sha: str | None) -> str:
    # Avoid GitHub's account-default email when publishing public commits.
    identity = {
        "name": "Repository Maintainer",
        "email": "316344525+dwj9ddyvf6-hub@users.noreply.github.com",
    }
    payload = {"message": message,
               "content": base64.b64encode(data).decode(),
               "author": dict(identity),
               "committer": dict(identity)}
    if existing_sha:
        payload["sha"] = existing_sha
    try:
        _, resp = _put_once(repo_path, payload)
    except ghapi.ApiError as e:
        if e.status == 401:
            # A sporadic edge/credential flake (cure
            # SYNC-PUT-AUTH-20261108): the estate transport
            # diagnosis (2026-10-28) already classed transient
            # HTTP 401s on this egress path as a sporadic
            # edge/credential flake, retried by design in the
            # older pusher. On 2026-11-08 two consecutive sync
            # runs died mid-publish on a single 401 each, on
            # different files (ai-chart-read/data.json, then
            # pattern-draw/data.json), while single authenticated
            # calls and the mirror's writes to this same repo,
            # through this same credential helper, succeeded
            # minutes apart. The credential is not dead; one
            # request in a long run draws the flake and the
            # unretried error killed the whole run. The cure
            # retries the PUT once, unchanged in content and
            # base sha; ghapi fetches a fresh credential
            # surrogate per call, so the retry carries a freshly
            # fetched credential. A second 401 raises, unchanged,
            # so a genuinely dead credential still fails loud.
            time.sleep(2)
            _, resp = _put_once(repo_path, payload)
            return resp.get("content", {}).get("sha")
        # A sha conflict means the file moved on the remote after
        # this run's tree snapshot was taken (cure
        # SYNC-PUT-SHA-20261108): another writer landed on the
        # repo mid-run (on 2026-11-08 the history-rewrite publish
        # moved every blob while a sync was uploading, and the
        # run died on decay-watch/data.json). GitHub answers a
        # stale base sha with 409, and a missing one with 422;
        # the old retry handled only the 422 form, so the 409
        # killed the whole run mid-publish, after dozens of files
        # had already landed, with no index regeneration and no
        # log line. The cure re-reads the file's CURRENT sha and
        # retries once with that base; the content written is
        # still exactly this run's candidate bytes, and the
        # caller's returned-sha check plus the run's final
        # read-back proof still verify the remote ends with
        # those bytes. A second conflict raises, unchanged.
        # (The 409 body names the two blob hashes but never the
        # word "sha"; the 422 body does, so the word test stays
        # on the 422 form only.)
        if e.status == 409 or (e.status == 422 and "sha" in e.body):
            try:
                _, cur = ghapi.api(
                    "GET", f"{REPO_API}/contents/"
                           + urllib.parse.quote(repo_path))
                payload["sha"] = cur["sha"]
            except ghapi.ApiError as ge:
                if ge.status != 404:
                    raise
                payload.pop("sha", None)
            _, resp = _put_once(repo_path, payload)
        else:
            raise
    return resp.get("content", {}).get("sha")


INSIDER_WIRE_DATA = "site/insider-wire/data.json"


def _insider_wire_first_names_are_third_party(text: str) -> bool:
    """True only when every first_name occurrence in the insider-wire
    data sits inside a multiword proper name (a capitalised name token
    adjacent within the same quoted string), i.e. a third-party
    insider's full name on a public SEC filing, never a standalone
    reference. Any other shape fails closed."""
    for m in _FIRST_NAME_RX.finditer(text):
        lo = text.rfind('"', 0, m.start())
        hi = text.find('"', m.end())
        if lo < 0 or hi < 0:
            return False
        value = text[lo + 1:hi]
        tokens = [t for t in re.split(r"[^A-Za-z.'-]+", value) if t]
        if len(tokens) < 2:
            return False
        if not any(t[0].isupper() and not _FIRST_NAME_RX.search(t)
                   for t in tokens):
            return False
    return True


# Desk privacy gate (DESK-PRIVACY-20261103): see the header docstring.
# Scope: terminal_feed.json by name anywhere, plus any file under a
# desk/ directory. Fail closed: unparseable desk JSON is refused.
DESK_PRIVATE_KEYS = {
    "account", "account_positions", "buying_power", "cash", "equity",
    "last_equity", "portfolio_value", "money_assigned",
    "money_assigned_total", "starting_capital", "positions_cost",
    "open_positions", "account_present", "positions",
}


def _json_keys(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(str(k).lower())
            _json_keys(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _json_keys(v, out)
    return out


def desk_privacy_reason(rel: str, raw: bytes):
    """Skip reason when rel/raw falls under the desk privacy gate,
    else None. Pure function of the candidate, so the blocker test
    exercises the exact code the sync runs."""
    name = Path(rel).name
    if name == "terminal_feed.json":
        return ("desk privacy gate (DESK-PRIVACY-20261103): internal "
                "producer feed is never published")
    if "desk" not in Path(rel).parts:
        return None
    if name == "index.html" and b"terminal_feed.json" in raw:
        return ("desk privacy gate (DESK-PRIVACY-20261103): the desk "
                "page reads the internal producer feed and is not "
                "published until it reads a public-safe file")
    if Path(rel).suffix.lower() != ".json":
        return None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        return ("desk privacy gate (DESK-PRIVACY-20261103): "
                "unparseable desk JSON refused (fail closed)")
    hits = sorted(_json_keys(obj, set()) & DESK_PRIVATE_KEYS)
    if hits:
        return ("desk privacy gate (DESK-PRIVACY-20261103): private "
                f"desk keys present: {hits}")
    return None


def candidate_for(rel: str, raw: bytes):
    """Return (candidate_bytes, skip_reason). Exactly one is set."""
    reason = desk_privacy_reason(rel, raw)
    if reason:
        return None, reason
    if rel in UNFIXABLE:
        return None, "unfixable-by-sanitization (cure phase ruling)"
    ext = Path(rel).suffix.lower()
    if ext in AUTHORED_EXTS:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is not None:
            cand = sanitize(text)
            hits = gate_hits(cand)
            if hits:
                return None, f"gate patterns remain after sanitization: {hits}"
            return cand.encode("utf-8"), None
    text = raw.decode("utf-8", errors="replace")
    hits = gate_hits(text)
    if hits:
        # Eighth one-file gate exception (pii_gate.FILE_EXCEPTIONS,
        # 2026-11-02): insider-wire's data.json is third-party public
        # SEC Form 4 data whose only hit is first_name, each time as
        # part of a third-party insider's full name. The waiver here
        # mirrors the gate's: this exact file, first_name only, and
        # only while every occurrence is a multiword proper name and
        # no other pattern hits. Anything else still skips.
        if (rel == INSIDER_WIRE_DATA and hits == ["first_name"]
                and _insider_wire_first_names_are_third_party(text)):
            return raw, None
        return None, f"gate patterns in non-authored file: {hits}"
    return raw, None


def load_repo_generator():
    """Fetch the repo generator and import its logic for this run."""
    _, cur = ghapi.api("GET", f"{REPO_API}/contents/tools/build_repo_index.py")
    src = base64.b64decode(cur["content"])
    tmp = Path(tempfile.mkdtemp(prefix="repo-index-gen-"))
    mod_path = tmp / "build_repo_index.py"
    mod_path.write_bytes(src)
    spec = importlib.util.spec_from_file_location("build_repo_index",
                                                  mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MAP_PATH = "docs/REPOSITORY-MAP.json"


def fetch_navigation(entries):
    """Return the curated navigation map named by a repo tree, or
    None when that tree carries no map.

    Cure SYNC-INDEX-NAVIGATION-20261110: both index regeneration
    paths below rendered INDEX.md with no navigation, while the
    repo generator's own check (tools/build_repo_index.py, run by
    the Repository integrity workflow) renders the saved INDEX.md
    against the navigation map at the indexed commit and compares
    byte for byte. The map changes area summaries, entrypoints and
    collection routes, so every sync-published INDEX.md differed
    from the deterministic rendering and the integrity workflow
    failed on every hourly run (live proof: run 42840525482, step
    8, "INDEX.md differs from the deterministic rendering", and
    the saved INDEX.md reproduced locally as exactly the
    no-navigation render). The map is fetched by blob sha from
    the same post-upload tree the index describes, so the
    published rendering is the one the checker will reproduce.
    A tree without a map keeps the old no-navigation render."""
    entry = next((e for e in entries
                  if e.get("path") == MAP_PATH), None)
    if entry is None:
        return None
    _, blob = ghapi.api("GET", f"{REPO_API}/git/blobs/{entry['sha']}")
    if blob.get("encoding") not in (None, "base64"):
        raise ValueError("Navigation map blob is not base64")
    return json.loads(base64.b64decode(
        blob.get("content") or "").decode("utf-8"))


_LOCK_FH = None


def acquire_single_flight():
    """Hold the sync's single-flight lock for this process, or
    return None when another invocation already holds it. The
    lock is an flock on a file beside this script, released by
    the OS when the holder exits, so a killed run never leaves
    a stale lock behind."""
    global _LOCK_FH
    import fcntl
    fh = open(Path(__file__).with_name(".sync_to_test.lock"), "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    _LOCK_FH = fh
    return fh


def acquire_single_flight_wait(timeout=1500):
    """Like acquire_single_flight, but waits for the lock.

    Cure SYNC-SCOPED-WAIT-20261109: the full sync stands down on
    contention (exit 5) because waiting would serialize two
    whole-tree publishes. The scoped publisher below carries a
    handful of files, so waiting is the right trade: the holder
    is a sync that is already publishing this run's delta too,
    and when it finishes the scoped census finds nothing left to
    upload. Returns the lock handle, or None when the wait times
    out (the caller then fails loud, never silently)."""
    import fcntl
    deadline = time.time() + timeout
    while True:
        fh = acquire_single_flight()
        if fh is not None:
            return fh
        if time.time() >= deadline:
            return None
        time.sleep(5)


def publish_scoped(rels) -> int:
    """Publish only the named files (paths relative to ROOT),
    under the same gates as the full sync, waiting for the
    single-flight lock instead of standing down.

    Cure SYNC-SCOPED-WAIT-20261109: the book strip watcher's
    publish is one data file (plus whatever else its generator
    rewrote, such as the hub page), but it drove the full-tree
    sync, so it collided with the hourly sync's whole publish,
    first dying on 409 sha conflicts (exit 3, 2026-11-05/06) and,
    after the single-flight cure, standing down (exit 5,
    2026-11-09 08:13 and 15:13 ET) behind runs of 5 to 20 minutes
    while the watcher reported each stand-down as a publish
    FAILURE. The scoped route uploads only the named files'
    candidates (same sanitization and gates via candidate_for,
    same zero-byte guard, same per-file sha-conflict retry inside
    put_file), then regenerates INDEX.json/INDEX.md against the
    post-upload tree exactly as the full sync does, and verifies
    by read-back. Exit codes mirror the full sync's: 0 clean
    (nothing changed is clean), 2 truncated tree, 3 hard API
    error, 4 zero-byte guard refusal, 6 the lock wait timed out.
    """
    fh = acquire_single_flight_wait()
    if fh is None:
        print("SCOPED PUBLISH: single-flight lock still held "
              "after waiting; failing loud, nothing published.",
              flush=True)
        return 6
    summary = {"uploaded": [], "skipped_unchanged": 0,
               "skipped_gate": [], "index_md": "not-run",
               "index_json": "not-run", "index_total": None,
               "head_before": None, "head_after": None,
               "scoped": list(rels)}
    try:
        head, _gen_at, _entries, blobs = fetch_head_and_tree()
        summary["head_before"] = head
        repo_shas = {p: e["sha"] for p, e in blobs.items()}
        changed = []
        for rel in rels:
            raw = (ROOT / rel).read_bytes()
            cand, reason = candidate_for(rel, raw)
            if cand is None:
                summary["skipped_gate"].append(
                    {"path": rel, "reason": reason})
                continue
            if repo_shas.get(PREFIX + rel) == blob_sha(cand):
                summary["skipped_unchanged"] += 1
                continue
            changed.append((rel, cand))
        repo_sizes = {p: e.get("size", 0) for p, e in blobs.items()}
        violations = zero_byte_violations(changed, repo_sizes)
        if violations:
            for v in violations:
                print(f"GUARD REFUSAL: {v}", flush=True)
            summary["guard_violations"] = violations
            print(json.dumps(summary, indent=1))
            return 4
        print(f"scoped census: {len(changed)} changed, "
              f"{summary['skipped_unchanged']} unchanged, "
              f"{len(summary['skipped_gate'])} gate-skipped",
              flush=True)
        uploaded_sha = {}
        for rel, cand in changed:
            repo_path = PREFIX + rel
            got = put_file(repo_path, cand,
                           f"terminal-lineup: scoped sync {rel}",
                           repo_shas.get(repo_path))
            exp = blob_sha(cand)
            if got != exp:
                print(f"UPLOAD SHA MISMATCH {repo_path}: repo "
                      f"{got} expected {exp}", flush=True)
                return 3
            uploaded_sha[repo_path] = exp
            summary["uploaded"].append(rel)
            time.sleep(0.15)
        head2, gen_at2, entries2, blobs2 = fetch_head_and_tree()
        summary["head_after"] = head2
        gen = load_repo_generator()
        index = gen.build_index(entries2, head2, gen_at2,
                                "dwj9ddyvf6-hub", "Test")
        summary["index_total"] = index["totals"]["files"]
        idx_json = (json.dumps(index, indent=1, sort_keys=True)
                    + "\n").encode("utf-8")
        idx_md = gen.render_markdown(
            index, fetch_navigation(entries2)).encode("utf-8")
        repo_shas2 = {p: e["sha"] for p, e in blobs2.items()}
        for repo_path, data, key in (
                ("INDEX.json", idx_json, "index_json"),
                ("INDEX.md", idx_md, "index_md")):
            if len(data) == 0:
                print(f"GUARD REFUSAL: {repo_path}: zero-byte "
                      f"generated index refused", flush=True)
                return 4
            if repo_shas2.get(repo_path) == blob_sha(data):
                summary[key] = "unchanged"
                continue
            try:
                got = put_file(repo_path, data,
                               f"index: regenerate {repo_path}",
                               repo_shas2.get(repo_path))
            except Exception as e:
                summary[key] = f"blocked: {type(e).__name__}: {e}"
                print(f"INDEX {repo_path} BLOCKED: {e}", flush=True)
                continue
            if got != blob_sha(data):
                print(f"INDEX SHA MISMATCH {repo_path}", flush=True)
                return 3
            uploaded_sha[repo_path] = blob_sha(data)
            summary[key] = "uploaded"
            time.sleep(0.15)
        _h3, _g3, _e3, blobs3 = fetch_head_and_tree()
        final_shas = {p: e["sha"] for p, e in blobs3.items()}
        bad = [p for p, exp in uploaded_sha.items()
               if final_shas.get(p) != exp]
        if bad:
            print(f"READ-BACK MISMATCH: {bad}", flush=True)
            return 3
        summary["read_back_verified"] = len(uploaded_sha)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        changed_names = ",".join(summary["uploaded"]) or "none"
        line = (f"- {ts} | scoped publish: "
                f"{len(summary['uploaded'])} ({changed_names}) | "
                f"gate-skipped: {len(summary['skipped_gate'])} | "
                f"unchanged: {summary['skipped_unchanged']} | "
                f"index total: {summary['index_total']} | "
                f"INDEX.md: {summary['index_md']} | INDEX.json: "
                f"{summary['index_json']} | read-back verified: "
                f"{summary['read_back_verified']} | head: "
                f"{summary['head_after']}\n")
        SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNC_LOG, "a", encoding="utf-8") as fh2:
            fh2.write(line)
        print(line, flush=True)
        print(json.dumps(summary, indent=1))
        return 0
    except ghapi.ApiError as e:
        print(f"HARD API ERROR: {e}", flush=True)
        return 3


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if "--only" in args:
        i = args.index("--only")
        rels = [r for r in args[i + 1:] if not r.startswith("--")]
        if not rels:
            print("scoped publish needs at least one file path",
                  flush=True)
            return 2
        return publish_scoped(rels)
    dry_run = "--dry-run" in args
    if not dry_run and acquire_single_flight() is None:
        print("SYNC ALREADY RUNNING: another sync_to_test.py "
              "invocation holds the single-flight lock; this "
              "invocation stands down and published nothing.",
              flush=True)
        return 5
    summary = {"uploaded": [], "skipped_unchanged": 0, "skipped_gate": [],
               "index_md": "not-run", "index_json": "not-run",
               "index_total": None, "head_before": None, "head_after": None}
    try:
        head, _gen_at, _entries, blobs = fetch_head_and_tree()
        summary["head_before"] = head
        repo_shas = {p: e["sha"] for p, e in blobs.items()}

        changed = []  # (rel, candidate_bytes)
        for rel in included_files():
            raw = (ROOT / rel).read_bytes()
            cand, reason = candidate_for(rel, raw)
            if cand is None:
                summary["skipped_gate"].append(
                    {"path": rel, "reason": reason})
                continue
            if repo_shas.get(PREFIX + rel) == blob_sha(cand):
                summary["skipped_unchanged"] += 1
                continue
            changed.append((rel, cand))

        # Zero-byte guard (HUB-BLANK-20261102): checked over the
        # whole changed set BEFORE any upload, so a refused publish
        # publishes nothing and fails loud with the file named.
        repo_sizes = {p: e.get("size", 0) for p, e in blobs.items()}
        violations = zero_byte_violations(changed, repo_sizes)
        if violations:
            for v in violations:
                print(f"GUARD REFUSAL: {v}", flush=True)
            summary["guard_violations"] = violations
            print(json.dumps(summary, indent=1))
            return 4

        print(f"census: {len(changed)} changed, "
              f"{summary['skipped_unchanged']} unchanged, "
              f"{len(summary['skipped_gate'])} gate-skipped", flush=True)
        if dry_run:
            summary["changed_paths"] = [r for r, _ in changed]
            print(json.dumps(summary, indent=1))
            return 0

        uploaded_sha = {}  # repo path -> expected blob sha
        for rel, cand in changed:
            repo_path = PREFIX + rel
            got = put_file(repo_path, cand,
                           f"terminal-lineup: sync {rel}",
                           repo_shas.get(repo_path))
            exp = blob_sha(cand)
            if got != exp:
                print(f"UPLOAD SHA MISMATCH {repo_path}: repo {got} "
                      f"expected {exp}", flush=True)
                return 3
            uploaded_sha[repo_path] = exp
            summary["uploaded"].append(rel)
            time.sleep(0.15)

        # Regenerate the index against the post-sync tree.
        head2, gen_at2, entries2, blobs2 = fetch_head_and_tree()
        summary["head_after"] = head2
        gen = load_repo_generator()
        index = gen.build_index(entries2, head2, gen_at2,
                                "dwj9ddyvf6-hub", "Test")
        summary["index_total"] = index["totals"]["files"]
        idx_json = (json.dumps(index, indent=1, sort_keys=True)
                    + "\n").encode("utf-8")
        idx_md = gen.render_markdown(
            index, fetch_navigation(entries2)).encode("utf-8")
        repo_shas2 = {p: e["sha"] for p, e in blobs2.items()}
        for repo_path, data, key in (
                ("INDEX.json", idx_json, "index_json"),
                ("INDEX.md", idx_md, "index_md")):
            if len(data) == 0:
                print(f"GUARD REFUSAL: {repo_path}: zero-byte "
                      f"generated index refused", flush=True)
                return 4
            if repo_shas2.get(repo_path) == blob_sha(data):
                summary[key] = "unchanged"
                continue
            try:
                got = put_file(repo_path, data,
                               f"index: regenerate {repo_path}",
                               repo_shas2.get(repo_path))
            except Exception as e:  # gate refusal is logged, never bypassed
                summary[key] = f"blocked: {type(e).__name__}: {e}"
                print(f"INDEX {repo_path} BLOCKED: {e}", flush=True)
                continue
            if got != blob_sha(data):
                print(f"INDEX SHA MISMATCH {repo_path}", flush=True)
                return 3
            uploaded_sha[repo_path] = blob_sha(data)
            summary[key] = "uploaded"
            time.sleep(0.15)

        # Final read-back proof: every uploaded file at its expected SHA.
        _h3, _g3, _e3, blobs3 = fetch_head_and_tree()
        final_shas = {p: e["sha"] for p, e in blobs3.items()}
        bad = [p for p, exp in uploaded_sha.items()
               if final_shas.get(p) != exp]
        if bad:
            print(f"READ-BACK MISMATCH: {bad}", flush=True)
            return 3
        summary["read_back_verified"] = len(uploaded_sha)

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        changed_names = ",".join(summary["uploaded"]) or "none"
        line = (f"- {ts} | files changed: {len(summary['uploaded'])} "
                f"({changed_names}) | gate-skipped: "
                f"{len(summary['skipped_gate'])} | unchanged: "
                f"{summary['skipped_unchanged']} | index total: "
                f"{summary['index_total']} | INDEX.md: "
                f"{summary['index_md']} | INDEX.json: "
                f"{summary['index_json']} | read-back verified: "
                f"{summary['read_back_verified']} | head: "
                f"{summary['head_after']}\n")
        SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNC_LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
        print(line, flush=True)
        print(json.dumps(summary, indent=1))
        return 0
    except ghapi.ApiError as e:
        print(f"HARD API ERROR: {e}", flush=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
