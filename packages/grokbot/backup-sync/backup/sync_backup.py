#!/usr/bin/env python3
"""
sync_backup.py - incremental backup of Trader's research folders to the PRIVATE
GitHub repo dwj9ddyvf6-hub/quant-research-backup.

Roots backed up (relative to /workspace):
    Trader-research/   gainzalgo-study/   milkman-study/   registry/   gh-deepdive/   reports/   Trader-desk/   scripts_tmp/   x-profile/
    (+ small /home/box/scratch/shadow logs -> box-scratch/)

Always excluded:
    __pycache__/, node_modules/, .venv/ (recreate from backup/env/*-requirements.txt),
    nested .git/ directories (third-party clone working trees ARE included),
    images whose sha256 is in gainzalgo-study/miner/store/purged_sha256.txt,
    .env / key / credential files, and any file matching a secret pattern,
    rebuildable caches matching SKIP_FILE_RE (swing_basket/nextpass/paths_*.npy;
    swing_basket/ideas_batch1/{cache,feat,base}_*.parquet).

Files larger than SPLIT_BYTES (45 MiB) are split into <path>.part000, .part001, ...
in the repo; backup/parts_manifest.json records the parts and the sha256 of the
whole file. Reassemble with:   python3 backup/sync_backup.py reassemble <repo-dir>
(or manually:  cat FILE.part* > FILE  and check sha256sum).

Commands:
    scan                 hash everything -> backup/manifest.json, print new/changed/deleted
                         versus backup/uploaded.json (what is already in the repo)
    stage  REPO_DIR      stage new/changed files (splitting big ones)
    push   REPO_DIR      stage + git commit/push in batches (<= BATCH_BYTES per push);
                         BACKUP_DIRECT_WORKTREE=1 stages source blobs directly (no duplicate clone tree)
                         and update backup/uploaded.json after each successful push
    batches [MAX_BYTES]  list pending small UTF-8 text files grouped into connector-sized
                         batches (for MCP push_files uploads when no git auth exists)
    mark  PATH...        record PATHs as uploaded (after a connector upload)
    reassemble REPO_DIR  join all .partNNN files in a clone back into originals + verify
    pack [--force] [--dry-run] [--allow-shrink]
                         compress Trader-research/real_engine/out into
                         real_engine/out_archive/out_<1d|1h|1wk|misc>.tar.zst (zstd -15 --long=31),
                         verify every member's sha256, write out_<group>.sha256 + index.json.
                         Only groups whose files changed are rebuilt. The raw out/ is never
                         uploaded (excluded from scan) and never deleted.

Typical rerun (needs git auth on the box, e.g. `gh auth login` then `gh auth setup-git`):
    git clone https://github.com/dwj9ddyvf6-hub/quant-research-backup.git /workspace/qrb
    python3 /workspace/backup/sync_backup.py push /workspace/qrb
"""
import hashlib, json, os, re, shutil, subprocess, sys, time

WS = "/workspace"
# 2026-10-17 10:00 ET (RS-1017-10): handoff/ (the Chief of Staff handoff doc agents read first) was never a backup root
ROOTS = ["Trader-research", "gainzalgo-study", "milkman-study", "registry", "gh-deepdive", "reports",
         "Trader-desk", "scripts_tmp", "x-profile", "notify", "x_video", "cloud-agent-transcripts",
         "scratch", "_restore", "_pre_restore_keep",
         "plan_stage/updown_card", "lazarus/out", "handoff"]   # 2026-10-17 (RS-1017-0): the staged Best Setups (code, site, out/ card state) and Lazarus out/ were lost in the 10-16 23:25 ET re-provision; live bestsetups/out is under Trader-research   # added 2026-10-05 nightly: scratch = Daily Cyan responder study (dc_resp); _restore = restore tooling/log; _pre_restore_keep = box copies kept before a restore overwrote them. midna-clone (Midna's own repo) and qrc-clone/qrb-clone (our repo clones) are re-clonable, not mirrored.
           # audit 4 (M5): desk + /tmp scripts; x-profile = X assets; notify = desk/intel cursors; x_video = PredictionAlgos transcripts/analysis (2026-10-02 nightly; large media split .partNNN). steelrend_ref is re-clonable (pins in clones.txt), not mirrored. cloud-agent-transcripts = Cursor cloud/outside-lab agent transcripts (added 2026-10-04 nightly; files with tokens are skipped by SECRET_RE). agent-tools (tool-output dumps), tmp (scratch incl. Midna read-only copy) are deliberately not mirrored.
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")
UPLOADED = os.path.join(HERE, "uploaded.json")
PURGED = os.path.join(WS, "gainzalgo-study/miner/store/purged_sha256.txt")
SPLIT_BYTES = 45 * 1024 * 1024
BATCH_BYTES = 1_500_000_000             # <= 1.5 GB per push (GitHub rejects pushes > 2 GB)
RUNTIME_RE = re.compile(r"\.(pid|lock|sock)$")  # BK-1019-1: runtime PID/lock/socket files are never backed up
PRE_LEFTOVER_RE = re.compile(r"^(?!.*/history/).*\.pre(\d+|updown)$")  # BK-1019-2: *.preNNNN/*.preupdown edit leftovers in live folders are not backed up (archived copies under */history/ are)
SKIP_DIRS = {"__pycache__", "node_modules", ".venv", "venv", ".conda", ".git", ".mypy_cache", ".pytest_cache"}
def _skipd(x): return x in SKIP_DIRS or x.startswith(".venv-")   # 2026-10-19 (nightly audit d): every .venv-* env too (recreate from backup/env/*-requirements.txt)
# Raw engine output (~32 GB CSV) is NOT stored file-by-file: `pack` compresses it into
# PACK_DST/*.tar.zst (+ per-file sha256 lists) and only those archives are synced.
PACK_SRC = "Trader-research/real_engine/out"
PACK_DST = "Trader-research/real_engine/out_archive"
PACK_TMP = os.path.join(HERE, "pack_tmp")
ZSTD_ARGS = ["zstd", "-q", "-15", "--long=31", "-T0"]      # restore needs: zstd -d --long=31
SKIP_REL = {PACK_SRC,
            "Trader-desk/secrets",   # audit 4: never back up the desk env file (only .env.example lives there today)
            # gh-deepdive/clones and /branches are re-clonable copies of Trader's own GitHub repos
            # (pins in gh-deepdive/CLONES.txt; re-create with gh-deepdive/tools/clone_all.sh)
            "gh-deepdive/clones", "gh-deepdive/branches",
            # swing-definition audit 2026-10-01: v686 tarballs come from Trader's TR repo
            # (releases/v686/); per-bar v686 outputs and the W3/SAME pipeline copies are
            # rebuildable (v686_check/run_v686_swing.mjs, swing_audit/run_variants.sh)
            "gh-deepdive/v686", "gh-deepdive/v686_check/out",
            "gh-deepdive/swing_audit/nextpass_W3", "gh-deepdive/swing_audit/nextpass_SAME",
            # genome study 2026-10-01: v619 signal-events (OPS LFS, recover-lfs.py) + ATD Phase 7 DB copy (Trader's repo)
            "gh-deepdive/genome/data",
            # weekly-edge expansion 2026-10-01: Alpaca bars of inactive names + engine replays (re-fetch: calib/expand/code/fetch_inactive.py,
            # mk_payloads.py, fetch_control.py, then real_engine/run_engine_live.mjs 1wk); the asset list and symbol list ARE backed up
            "gh-deepdive/genome/calib/expand/data/bars_1d", "gh-deepdive/genome/calib/expand/data/bars_1w", "gh-deepdive/genome/calib/expand/data/yahoo_1wk",
            "gh-deepdive/genome/calib/expand/data/engine_1wk", "gh-deepdive/genome/calib/expand/data/ctrl_yahoo_1wk", "gh-deepdive/genome/calib/expand/data/ctrl_engine_1wk",
            # altdata 2026-10-01: re-downloadable HF mirror reductions + rebuildable study cache (Trader-research/altdata/README.md);
            # the built tables altdata/data ARE backed up
            "Trader-research/altdata/raw_hf", "Trader-research/altdata/cache", "Trader-research/altdata/raw_sec",
            # whale_v2: re-fetchable SEC index / FINRA / Alpaca caches (fetch_sec_box.py, fetch_finra.py, fetch_blocks.py); built tables in altdata/data ARE backed up
            "Trader-research/altdata/raw_secbox", "Trader-research/altdata/raw_finra", "Trader-research/altdata/raw_blocks",
            # audit 4 (2026-10-01): pooled OHLCV caches rebuilt by their build_pool_cache.py and deleted at study end (bigwinners/code, outside_ideas/batch3_x_tradingview/code)
            "Trader-research/bigwinners/cache", "Trader-research/outside_ideas/batch3_x_tradingview/cache",
            # autopilot 2026-10-01: re-downloadable House PTR PDFs / EDGAR 13F XML caches + rebuildable fire cache (autopilot/README.md); parsed tables in autopilot/data ARE backed up
            "Trader-research/autopilot/data/raw/house_ptr", "Trader-research/autopilot/data/raw/sec13f", "Trader-research/autopilot/cache",
            # STANDALONE_ALL 2026-10-02: panel.npz (1.6 GB) rebuilt in ~25 s by STANDALONE_ALL/code/sa_common.panel(); code/out/REPORT ARE backed up
            "Trader-research/STANDALONE_ALL/cache", "Trader-research/SIGNAL_DEF_SWEEP/cache", "Trader-research/KILL_RECHECK/cache",
            # 2026-10-06 (CoS executor, ChartsLector backup): panel_d.npz (376 MB) rebuilt by CHARTSLECTOR/lib; terminal_export/cache = public Yahoo/CBOE
            # fetch cache rebuilt by export_terminal.py; cos/chartslector/img = 3,659 X post images (1.2 GB), listed in scratch/cos/chartslector/IMG_MANIFEST.tsv
            "Trader-research/CHARTSLECTOR/cache", "Trader-research/CHARTSLECTOR/terminal_export/cache", "scratch/cos/chartslector/img",
            # 2026-10-19 (nightly audit d): scratch/midna_src = 4.5 GB copy of Midna's own repo (re-clonable; pinned in lazarus/vendor/midna/PIN_*.json);
            # scratch/l100/qrb = a sparse working clone of THIS backup repo (backing it up into itself duplicated 0.5 GB). Both made the light sync time out.
            "scratch/midna_src", "scratch/l100/qrb"}
# Rebuildable caches (regenerate instead of backing up): the next-pass price-path arrays
# (python Trader-research/swing_basket/nextpass/paths.py rebuilds them from real_engine/out).
SKIP_FILE_RE = re.compile(r"^Trader-research/swing_basket/nextpass/paths_[^/]*\.npy$"
                          r"|^Trader-research/swing_basket/ideas_batch1/(cache|base)_[^/]*\.parquet$"   # feat_*.parquet backed up since 2026-10-01 23:10 ET (feat_1h is a db fires_1h source; H014)
                          
                          # 2026-10-01 23:10 ET: calib/expand/out/x_*.parquet|npy are NO LONGER skipped. x_1h.parquet is a required source of db fires_1h; it was lost
                          # in the 19:25 ET rollback and, being excluded, was neither restored nor seen by the deletion guards (repairs H014). ~136 MB, split as needed.
                          r"|^Trader-research/db/tables/.*\.parquet(\.tmp)?$|^Trader-research/db/research\.duckdb(\.wal)?$"   # research DB data: rebuild with .venv/bin/python db/refresh.py --force --rebuild-ledgers (db/README.md); code/views.sql/state ARE backed up
                          r"|^Trader-research/hd_(avenues2|lanes_explore)/cache/.*\.(parquet|npz|npy)(\.part\d+|\.tmp)?$"   # audit 5 (2026-10-01): study caches rebuilt by their own code (hd_avenues2/hdl_rebuild, hd_lanes_explore/code 01-04); 650 MB went to the repo at 16:35 and ~1 GB was being rewritten for the 18:02 run; results/out/code ARE backed up
                          # 2026-10-05 21:40 ET (Research Lab, SMALLMICRO cache rebuild): SMALLMICRO_RERUN/cache is backed up ONLY for the inputs CANDLES /
                          # CORPUS_AUDIT read or that cannot be re-fetched identically: panel.npz (PIT band / spread panel, ~267 MB, split .partNNN), mcap_daily.parquet
                          # (PIT SEC market cap), and the small SEC snapshots (sec_shares_extra, cikmap, company_tickers_exchange.json). Everything else there
                          # (Alpaca alp_1d_* re-fetch, fires_tagged / rf_* / pool_* / tiers_noliq rebuilt by code/rebuild_cache.sh) stays skipped. Other trees unchanged.
                          r"|^Trader-research/SMALLMICRO_RERUN/cache/(?!(panel\.npz|mcap_daily\.parquet|sec_shares_extra\.parquet|cikmap\.parquet|company_tickers_exchange\.json)$).*$"
                          # same date: ext/cache only keeps xf_h_swing.parquet (+ its CANONICAL_ONLY marker, 3.6 MB; CANDLES s07_overlay hourly input); rest of ext/cache skipped
                          r"|^Trader-research/SMALLMICRO_RERUN/ext/cache/(?!xf_h_swing\.(parquet|CANONICAL_ONLY)$).*$"
                          r"|^Trader-research/real_engine/store_v1/.*\.parquet(\.tmp)?$")   # engine bar store: rebuild with python Trader-research/real_engine/build_store.py (from out/, restorable from real_engine/out_archive); its _index.json/index.json ARE backed up   # rebuildable caches (ideas_batch1: build_cache.py / features.py / common.base); results, code, models and frozen files are still backed up
ROOT_DOCS = ("CATALOG.md", "FINDINGS.md")   # copied from /workspace/registry to the repo root when present
SECRET_NAME = re.compile(r"(^\.env($|\.)|\.pem$|\.key$|^id_rsa|^id_ed25519|credentials)", re.I)
SECRET_RE = re.compile(rb"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{32,}|"
                       rb"AKIA[0-9A-Z]{16}|xox[bpa]-[0-9A-Za-z-]{10,}|"
                       rb"(?:APCA_API_SECRET_KEY|ALPACA_[A-Z_]*SECRET[A-Z_]*)[\"']?\s*[=:]\s*[\"']?[A-Za-z0-9/+]{30,}|"   # Alpaca secret assignments (audit 2026-10-01; a bare PK/AK key-id pattern was dropped: it is not a credential and false-matched compressed archives; exact secret values are caught by ENV_SECRETS)
                       rb"BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|Bearer [A-Za-z0-9._-]{30,})")
# literal values of secret-looking env vars of the syncing process (e.g. a bare 44-char Alpaca secret the regex cannot recognise) (audit 2026-10-01)
ENV_SECRETS = [v.encode() for k, v in os.environ.items() if re.search(r"SECRET|TOKEN|PASSW|API_KEY|KEY_ID", k, re.I) and len(v) >= 16]
TEXT_EXT = {".py", ".mjs", ".js", ".sh", ".pine", ".md", ".txt", ".csv", ".json", ".html",
            ".log", ".toml", ".cfg", ".yml", ".yaml", ".out", ".err", ".done"}


def _additive_push(repo):
    """2026-10-12 Trader absolute rule: the pushed commit may only ADD or MODIFY files. Any deletion vs its parent -> undo the commit, refuse to push."""
    import safety
    d = subprocess.run(["git", "-C", repo, "diff-tree", "-r", "--no-renames", "--no-commit-id", "--name-only", "--diff-filter=D", "-z", "HEAD"],
                       capture_output=True, check=True).stdout.decode().split("\0")
    d = [x for x in d if x]
    if d:
        git(repo, "reset", "-q", "--soft", "HEAD~1"); safety.log(f"BACKUP GUARD (sync): commit would delete {len(d)} files {d[:5]}; not pushing (additive-only)"); raise safety.Guard(7)
    git(repo, "push", "-q", "origin", "HEAD")      # plain fast-forward push; never --force

def load(p, default):
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=0, sort_keys=True)
    os.replace(tmp, p)


# Small run logs of the shadow engine, which lives outside /workspace. Stored in the repo under
# box-scratch/shadow/... The engine outputs there (and /home/box/scratch/cf) are reproducible
# and are NOT backed up. The logs are skipped if they total more than SCRATCH_LOG_MAX.
SCRATCH = "/home/box/scratch"
SCRATCH_PREFIX = "box-scratch/"
SCRATCH_LOG_DIRS = ["shadow"]
SCRATCH_LOG_RE = re.compile(r"\.(log|out|err)$")
SCRATCH_LOG_MAX = 50 * 1024 * 1024
REPO_ROOTS = ROOTS + [SCRATCH_PREFIX.rstrip("/")]
# Disk Saver mode: the qrb clone is an administrative Git dir only.  Git stages
# source files by content from /workspace; no duplicate working-tree copy is made.
DIRECT_WORKTREE = os.environ.get("BACKUP_DIRECT_WORKTREE", "0") == "1"
DIRECT_PARTS = {}  # part path -> (blob oid, byte size), used for >1.5GB split pushes


def src(rel):
    """box path for a repo-relative path"""
    if rel.startswith(SCRATCH_PREFIX):
        return os.path.join(SCRATCH, rel[len(SCRATCH_PREFIX):])
    return os.path.join(WS, rel)


def scratch_logs():
    found = []
    for top in SCRATCH_LOG_DIRS:
        for d, dirs, files in os.walk(os.path.join(SCRATCH, top)):
            dirs[:] = sorted(x for x in dirs if not _skipd(x))
            for fn in sorted(files):
                full = os.path.join(d, fn)
                if SCRATCH_LOG_RE.search(fn) and os.path.isfile(full) and not os.path.islink(full):
                    found.append((SCRATCH_PREFIX + os.path.relpath(full, SCRATCH), full))
    tot = sum(os.path.getsize(f) for _, f in found)
    if tot > SCRATCH_LOG_MAX:
        print(f"NOTE: scratch shadow logs total {tot/1e6:.0f} MB > 50 MB; skipped")
        return []
    return found


def walk():
    yield from scratch_logs()
    for root in ROOTS:
        for d, dirs, files in os.walk(os.path.join(WS, root)):
            dirs[:] = sorted(x for x in dirs if not _skipd(x) and
                             os.path.relpath(os.path.join(d, x), WS) not in SKIP_REL)
            for fn in sorted(files):
                full = os.path.join(d, fn)
                if os.path.islink(full) or not os.path.isfile(full):
                    continue
                if SKIP_FILE_RE.match(os.path.relpath(full, WS)) or RUNTIME_RE.search(full) or PRE_LEFTOVER_RE.match(os.path.relpath(full, WS)):
                    continue
                yield os.path.relpath(full, WS), full


def sha256(full):
    h = hashlib.sha256()
    secret = False
    tail = b""
    with open(full, "rb") as f:
        while True:
            b = f.read(8 << 20)
            if not b:
                break
            h.update(b)
            if not secret and (SECRET_RE.search(tail + b) or any(v in tail + b for v in ENV_SECRETS)):
                secret = True
            tail = b[-200:]
    return h.hexdigest(), secret


def scan(quiet=False):
    old = load(MANIFEST, {"files": {}})["files"]
    purged = set()
    if os.path.exists(PURGED):
        purged = {l.split()[0] for l in open(PURGED) if l.strip()}
    files, skipped = {}, {}
    for rel, full in walk():
        st = os.stat(full)
        o = old.get(rel)
        if o and o["size"] == st.st_size and o["mtime"] == int(st.st_mtime):
            files[rel] = o                      # unchanged; reuse hash
            continue
        if SECRET_NAME.search(os.path.basename(rel)):
            skipped[rel] = "secret-like filename"
            continue
        digest, secret = sha256(full)
        if secret:
            skipped[rel] = "secret pattern in content"
            continue
        if digest in purged:
            skipped[rel] = "purged image (purged_sha256.txt)"
            continue
        files[rel] = {"size": st.st_size, "mtime": int(st.st_mtime), "sha256": digest}
    for rel in list(files):
        if files[rel]["sha256"] in purged:
            skipped[rel] = "purged image (purged_sha256.txt)"
            del files[rel]
    save(MANIFEST, {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "files": files,
                    "skipped": skipped})
    up = load(UPLOADED, {})
    new = [r for r in files if r not in up]
    changed = [r for r in files if r in up and up[r] != files[r]["sha256"]]
    deleted = [r for r in up if r not in files and not r.startswith(("README", ".git", "backup/"))]
    if not quiet:
        tot = sum(v["size"] for v in files.values())
        pend = sum(files[r]["size"] for r in new + changed)
        print(f"files={len(files)} total={tot/1e9:.2f}GB uploaded={len(up)} "
              f"new={len(new)} changed={len(changed)} deleted={len(deleted)} (= once-uploaded files no longer on the box; they stay in the repo, sync never removes them) "
              f"pending={pend/1e9:.2f}GB skipped={len(skipped)}")
        for r, why in sorted(skipped.items()):
            print("  SKIP", r, "-", why)
    return files, new + changed


def _writable(path):
    """audit 5 (2026-10-01): frozen specs are chmod 444 and copy2 keeps that mode on the mirror copy, so a later re-copy over it
    (or a .partNNN rewrite) would raise PermissionError and abort the push. Give the owner write permission on an existing destination first."""
    try:
        if os.path.lexists(path) and not os.access(path, os.W_OK): os.chmod(path, os.stat(path).st_mode | 0o200)
    except OSError: pass


def _copy2(srcf, dst):
    _writable(dst); return shutil.copy2(srcf, dst)


class SourceChanged(RuntimeError): pass   # 2026-10-03: source edited between scan and stage (live logs / LOCK files); push() defers that file
def _git_blob(repo, srcf):
    """Hash a source file into the object store without creating a work-tree copy."""
    before = sha256(srcf)[0]
    p = subprocess.run(["git", "-C", repo, "hash-object", "-w", srcf],
                       text=True, capture_output=True, check=True)
    after = sha256(srcf)[0]
    if after != before:
        raise SourceChanged(f"source changed while staging {srcf}; sync aborted before commit")
    return p.stdout.strip()


def _direct_index(repo, rel, oid, srcf=None):
    mode = "100644"
    if srcf and os.access(srcf, os.X_OK): mode = "100755"
    subprocess.run(["git", "-C", repo, "update-index", "--add", "--cacheinfo", f"{mode},{oid},{rel}"], check=True)


def _direct_stage(repo, rel, srcf, expected=None):
    if expected and sha256(srcf)[0] != expected:
        raise SourceChanged(f"source changed after scan: {rel}; sync aborted before commit")
    oid = _git_blob(repo, srcf)
    _direct_index(repo, rel, oid, srcf)
    return oid


def stage_file(rel, repo, expected=None):
    srcf = src(rel)
    size = os.path.getsize(srcf)
    if DIRECT_WORKTREE:
        if size <= SPLIT_BYTES:
            _direct_stage(repo, rel, srcf, expected)
            return [rel]
        # Hash each split part directly into Git.  No temporary 45MiB files are
        # created, and a pre/post hash check prevents an in-place edit from
        # producing a mixed staged blob.
        before = sha256(srcf)[0]
        parts = []; total = 0
        with open(srcf, "rb") as f:
            i = 0
            while True:
                b = f.read(SPLIT_BYTES)
                if not b: break
                p = f"{rel}.part{i:03d}"
                oid = subprocess.run(["git", "-C", repo, "hash-object", "-w", "--stdin"], input=b,
                                     capture_output=True, check=True).stdout.decode().strip()
                DIRECT_PARTS[p] = (oid, len(b))
                parts.append(p); total += len(b); i += 1
        after = sha256(srcf)[0]
        if after != before or (expected and after != expected):
            raise RuntimeError(f"source changed while splitting {rel}; sync aborted before commit")
        if size <= BATCH_BYTES:
            for p in parts:
                oid, _ = DIRECT_PARTS[p]; _direct_index(repo, p, oid, srcf)
        return parts
    dst = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for old in os.listdir(os.path.dirname(dst)):          # drop stale parts
        if re.fullmatch(re.escape(os.path.basename(rel)) + r"\.part\d{3}", old):
            os.remove(os.path.join(os.path.dirname(dst), old))
    if size <= SPLIT_BYTES:
        _copy2(srcf, dst)
        return [rel]
    parts = []
    with open(srcf, "rb") as f:
        i = 0
        while True:
            b = f.read(SPLIT_BYTES)
            if not b: break
            p = f"{rel}.part{i:03d}"
            _writable(os.path.join(repo, p))
            with open(os.path.join(repo, p), "wb") as o: o.write(b)
            parts.append(p); i += 1
    if os.path.exists(dst): os.remove(dst)
    return parts

def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True)


def commit(repo, msg):
    """2026-10-05 22:00 ET (GrokBot): in direct-worktree mode commit with `write-tree --missing-ok` + `commit-tree` + `update-ref`.
    The clone is blob-less (~57k of ~100k blobs of origin/main are not local); `git commit` runs cache_tree_update(), which PREFETCHES every
    missing blob in the index from GitHub (GBs; a 4 GB lazy fetch was observed 21:48). The missing blobs are already on origin (they come from
    its tree), so they are neither needed for the commit nor sent by the push. Non-direct mode: plain git commit as before."""
    if not DIRECT_WORKTREE:
        git(repo, "commit", "-q", "-m", msg); return
    run = lambda *a: subprocess.run(["git", "-C", repo, *a], check=True, text=True, capture_output=True).stdout.strip()
    tree = run("write-tree", "--missing-ok"); parent = run("rev-parse", "HEAD")
    c = subprocess.run(["git", "-C", repo, "commit-tree", tree, "-p", parent, "-F", "-"], input=msg + "\n", check=True, text=True, capture_output=True).stdout.strip()
    run("update-ref", "-m", "commit: " + msg, "HEAD", c, parent)


def push(repo):
    # 2026-10-01 failsafes (after the 19:36 ET stale-box push of 464 removals): preflight (FREEZE / sentinels / ledger integrity /
    # staleness vs the repo manifest) before anything is pushed; mass-removal guard + soft deletes in flush(); see backup/safety.py
    sys.path.insert(0, HERE); import safety
    safety.preflight(repo, "sync")
    if DIRECT_WORKTREE:
        # 2026-10-05 (GrokBot, grokbot-inbox fix): sync.sh only moves refs/heads/main to origin/main; the INDEX kept the tree of the box's own
        # last commit, so every file another party pushed meanwhile (grokbot-inbox/INBOX.md by Midna/Cursor) was missing from the index and
        # got committed as a deletion (33824e14 19:22, 1347582f 20:53, 5652456e 21:01 ET). Re-align main to the freshly fetched origin/main
        # and load its tree into the index (read-tree: index only, the /workspace work tree is not touched) before staging anything.
        rh = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "-q", "origin/main^{commit}"], text=True, capture_output=True).stdout.strip()
        if rh: git(repo, "update-ref", "refs/heads/main", rh)
        git(repo, "read-tree", "HEAD")
    run_id = safety.next_run_id(); first = [True]
    files, pending = scan()
    up = load(UPLOADED, {})
    pm_path = os.path.join(HERE, "parts_manifest.json")
    pm = load(pm_path, {})
    batch, bsize, n = [], 0, 0
    deferred = set()
    pending.sort(key=lambda r: files[r]["size"])            # small (code/reports) first

    def flush():
        nonlocal batch, bsize, n
        if not batch:
            return
        n += 1
        save(pm_path, pm)
        if not DIRECT_WORKTREE:
            os.makedirs(os.path.join(repo, "backup"), exist_ok=True)
            for f in ("sync_backup.py", "parts_manifest.json", "sync.sh", "manifest.json", "clones.txt",
                      "PENDING.md", "safety.py", "restore.sh", "RESTORE.md", "tombstones.json", "critical_sync.py",
                      "midna_sync.py.disabled", "midna_sync.log", "critical_scheduler.sh", "ensure_critical.sh",
                      "BUG_LOG.md", "check_restore_1017.sh"):   # 2026-10-17: the bug log + restore regression were never backed up
                if os.path.exists(os.path.join(HERE, f)):
                    _copy2(os.path.join(HERE, f), os.path.join(repo, "backup", f))
            if os.path.isfile(os.path.join(HERE, "tests", "test_safety.py")):
                os.makedirs(os.path.join(repo, "backup", "tests"), exist_ok=True); _copy2(os.path.join(HERE, "tests", "test_safety.py"), os.path.join(repo, "backup", "tests", "test_safety.py"))
            if os.path.isfile(os.path.join(HERE, "tests", "test_midna_sync.py")):
                os.makedirs(os.path.join(repo, "backup", "tests"), exist_ok=True); _copy2(os.path.join(HERE, "tests", "test_midna_sync.py"), os.path.join(repo, "backup", "tests", "test_midna_sync.py"))
            if os.path.isfile(os.path.join(HERE, "tests", "test_direct_staging.py")):
                os.makedirs(os.path.join(repo, "backup", "tests"), exist_ok=True); _copy2(os.path.join(HERE, "tests", "test_direct_staging.py"), os.path.join(repo, "backup", "tests", "test_direct_staging.py"))
            if os.path.isdir(os.path.join(HERE, "env")):
                shutil.copytree(os.path.join(HERE, "env"), os.path.join(repo, "backup", "env"), dirs_exist_ok=True, copy_function=_copy2)
            if os.path.exists(os.path.join(HERE, "README.md")):
                _copy2(os.path.join(HERE, "README.md"), os.path.join(repo, "README.md"))
        root_docs = ["README.md"]
        if DIRECT_WORKTREE:
            # All normal roots already point at /workspace via core.worktree.
            # Stage only the scanned batch and explicit generated metadata; never
            # use git add -A, which would interpret historical remote-only files
            # as deletions from the source tree.
            for rel in batch:
                if rel not in DIRECT_PARTS and not (pm.get(rel, {}).get("parts")):
                    try: _direct_stage(repo, rel, src(rel), files[rel]["sha256"])
                    except SourceChanged as ex:   # 2026-10-03: a live log / LOCK rewritten by a running job between scan and stage -> defer that one
                        deferred.add(rel); print(f"  DEFER {rel}: {ex} (not staged, not marked uploaded; retried next sync)", flush=True)   # file (old blob stays), instead of aborting the whole sync
            for f in ("sync_backup.py", "parts_manifest.json", "sync.sh", "manifest.json", "clones.txt",
                      "PENDING.md", "safety.py", "restore.sh", "RESTORE.md", "tombstones.json", "critical_sync.py",
                      "midna_sync.py.disabled", "midna_sync.log", "critical_scheduler.sh", "ensure_critical.sh",
                      "BUG_LOG.md", "check_restore_1017.sh"):   # 2026-10-17: the bug log + restore regression were never backed up
                p = os.path.join(HERE, f)
                if os.path.exists(p): _direct_stage(repo, "backup/" + f, p)
            for f in ("test_safety.py", "test_midna_sync.py", "test_direct_staging.py", "test_protected_inbox.py", "test_restore_modes.py"):
                p = os.path.join(HERE, "tests", f)
                if os.path.isfile(p): _direct_stage(repo, "backup/tests/" + f, p)
            p = os.path.join(HERE, "hooks", "pre-push")      # 2026-10-05: grokbot-inbox pre-push guard (installed by sync.sh)
            if os.path.isfile(p): _direct_stage(repo, "backup/hooks/pre-push", p)
            envd = os.path.join(HERE, "env")
            if os.path.isdir(envd):
                for d, _, fs in os.walk(envd):
                    for f in fs:
                        p = os.path.join(d, f); _direct_stage(repo, "backup/env/" + os.path.relpath(p, envd), p)
            p = os.path.join(HERE, "README.md")
            if os.path.exists(p): _direct_stage(repo, "README.md", p)
            for f in ROOT_DOCS:
                p = os.path.join(WS, "registry", f)
                if os.path.exists(p): _direct_stage(repo, f, p); root_docs.append(f)
        else:
            for f in ROOT_DOCS:      # registry catalog/findings (written by registry/build_registry.py) -> repo root, like README.md
                if os.path.exists(os.path.join(WS, "registry", f)):
                    _copy2(os.path.join(WS, "registry", f), os.path.join(repo, f)); root_docs.append(f)
            git(repo, "add", "-A", "--", *[r for r in REPO_ROOTS if os.path.exists(os.path.join(repo, r))],
                "backup", *root_docs)
        first[0] = False   # 2026-10-12 Trader absolute rule: NEVER remove files from GitHub -> tombstone drops disabled (no confirmed_drops)
        staged_del = subprocess.run(["git", "-C", repo, "diff", "--cached", "--name-only", "--diff-filter=D", "-z"],
                                    capture_output=True, check=True).stdout.decode().split("\0")
        bset = set(batch)
        dels = [d for d in staged_del if d and not (re.fullmatch(r"(.*)\.part\d{3}", d) and re.fullmatch(r"(.*)\.part\d{3}", d).group(1) in bset)]
        if dels:   # 2026-10-05: removals of protected paths / files this box never uploaded (other parties' pushes) are put back, never tombstoned
            dels = safety.hold_foreign(repo, dels, owned=set(up))
        if dels:   # 2026-10-12 strictly additive: every staged removal is put back (copy-only, same as critical_sync.py)
            safety.unstage_restore(repo, dels); safety.log(f"sync: {len(dels)} removals put back (additive-only repo)")
        _r = subprocess.run(["git", "-C", repo, "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=D", "-z", "HEAD"], capture_output=True)
        _left = [d for d in _r.stdout.decode().split("\0") if d] if _r.returncode == 0 else []   # no HEAD yet (first commit) -> nothing can be deleted
        if _left: safety.log(f"BACKUP GUARD (sync): {len(_left)} deletions still staged {_left[:5]}; refusing to commit/push (additive-only)"); raise safety.Guard(7)
        safety.protected_guard(repo, "sync")                  # 2026-10-05: nothing under grokbot-inbox/ may be staged
        r = subprocess.run(["git", "-C", repo, "diff", "--cached", "--quiet"])
        if r.returncode:
            commit(repo, f"backup batch {n}: {len(batch)} files, {bsize/1e6:.0f} MB")
            if not safety.ledger_prefix_ok(repo, "HEAD"):
                git(repo, "reset", "-q", "--soft", "HEAD~1"); raise safety.Guard(5)
            bad = safety.commit_touches_protected(repo, "HEAD")
            if bad:
                git(repo, "reset", "-q", "--soft", "HEAD~1"); safety.log(f"BACKUP GUARD (sync): commit would change protected {bad[:5]}; not pushing"); raise safety.Guard(6)
            _additive_push(repo)      # plain fast-forward push; history is never rewritten (no --force anywhere)
        for rel in batch:
            if rel in deferred: continue
            up[rel] = files[rel]["sha256"]
        save(UPLOADED, up)
        print(f"pushed batch {n}: {len(batch)} files {bsize/1e6:.0f} MB", flush=True)
        batch, bsize = [], 0

    def push_parts(rel, parts):
        """a single file bigger than one batch: commit+push its parts in <= BATCH_BYTES chunks"""
        chunk, csz, k = [], 0, 0
        for i, p in enumerate(parts):
            size = DIRECT_PARTS[p][1] if DIRECT_WORKTREE else os.path.getsize(os.path.join(repo, p))
            chunk.append(p); csz += size
            if csz + SPLIT_BYTES > BATCH_BYTES or i == len(parts) - 1:
                k += 1
                if DIRECT_WORKTREE:
                    for q in chunk:
                        oid, _ = DIRECT_PARTS[q]; _direct_index(repo, q, oid)
                else:
                    git(repo, "add", "--", *chunk)
                safety.protected_guard(repo, "sync parts")
                if subprocess.run(["git", "-C", repo, "diff", "--cached", "--quiet"]).returncode:
                    commit(repo, f"backup {rel} parts chunk {k}: {len(chunk)} parts, {csz/1e6:.0f} MB")
                    bad = safety.commit_touches_protected(repo, "HEAD")
                    if bad:
                        git(repo, "reset", "-q", "--soft", "HEAD~1"); safety.log(f"BACKUP GUARD (sync parts): commit would change protected {bad[:5]}; not pushing"); raise safety.Guard(6)
                    _additive_push(repo)
                print(f"pushed {rel} chunk {k}: {len(chunk)} parts {csz/1e6:.0f} MB", flush=True)
                chunk, csz = [], 0

    for rel in pending:
        size = files[rel]["size"]
        if batch and bsize + size > BATCH_BYTES:
            flush()
        try: parts = stage_file(rel, repo, files[rel]["sha256"])
        except SourceChanged as ex:   # 2026-10-03: live file rewritten by a running job since the scan -> defer it (old blob stays in the repo), push the rest
            deferred.add(rel); print(f"  DEFER {rel}: {ex} (not staged, not marked uploaded; retried next sync)", flush=True); continue
        if size > BATCH_BYTES:
            push_parts(rel, parts)
        if len(parts) > 1:
            pm[rel] = {"sha256": files[rel]["sha256"], "size": files[rel]["size"], "parts": parts}
        else:
            pm.pop(rel, None)
        batch.append(rel)
        bsize += size if size <= BATCH_BYTES else 0
        if bsize >= BATCH_BYTES or size > BATCH_BYTES:
            flush()
    flush()


def batches(max_bytes=200_000):
    files, pending = scan(quiet=True)
    out, cur, cs = [], [], 0
    for rel in sorted(pending):
        sz = files[rel]["size"]
        if os.path.splitext(rel)[1].lower() not in TEXT_EXT or sz > max_bytes:
            continue
        try:
            open(src(rel), encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        if cur and cs + sz > max_bytes:
            out.append(cur); cur, cs = [], 0
        cur.append(rel); cs += sz
    if cur:
        out.append(cur)
    print(json.dumps(out, indent=1))


def mark(paths):
    files = load(MANIFEST, {"files": {}})["files"]
    up = load(UPLOADED, {})
    for p in paths:
        if p in files:
            up[p] = files[p]["sha256"]
    save(UPLOADED, up)


def reassemble(repo):
    pm = load(os.path.join(repo, "backup", "parts_manifest.json"), {})
    for rel, info in pm.items():
        dst = os.path.join(repo, rel)
        h = hashlib.sha256()
        with open(dst, "wb") as o:
            for p in info["parts"]:
                with open(os.path.join(repo, p), "rb") as f:
                    b = f.read(); h.update(b); o.write(b)
        print(("OK  " if h.hexdigest() == info["sha256"] else "BAD ") + rel)


# ---------------------------------------------------------------- pack (real_engine/out)
def pack_group(name):
    """timeframe family of a top-level entry of out/ (variants of one timeframe compress
    far better together: --long=31 finds the shared OHLC/indicator columns)."""
    for tf in ("1h", "1wk", "1d"):
        if name == tf or name.startswith(f"cf_{tf}_"):
            return tf
    if name.startswith("cf_"):
        return "1d"            # cf_utoff, cf_sq14, cf_sq20 are daily runs
    return "misc"


def pack_plan():
    srcd = os.path.join(WS, PACK_SRC)
    groups, symlinks = {}, []
    for name in sorted(os.listdir(srcd)):
        full = os.path.join(srcd, name)
        if os.path.islink(full):
            symlinks.append(f"{name} -> {os.readlink(full)}")
            continue
        g = "misc" if os.path.isfile(full) else pack_group(name)
        if os.path.isfile(full):
            groups.setdefault(g, []).append(name)
            continue
        for d, dirs, files in os.walk(full):
            dirs[:] = sorted(x for x in dirs if not _skipd(x))
            for fn in sorted(files):
                f = os.path.join(d, fn)
                if not os.path.islink(f) and os.path.isfile(f):
                    groups.setdefault(g, []).append(os.path.relpath(f, srcd))
    for g in groups:      # interleave variants: same symbol of every variant side by side
        groups[g].sort(key=lambda r: (os.path.basename(r), r))
    return groups, symlinks


def archived_members(dst, g):
    """member paths (relative to out/) recorded in out_<g>.sha256 of the existing archive, or None."""
    p = os.path.join(dst, f"out_{g}.sha256")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return {l.rstrip("\n").split("  ", 1)[1].split("/", 1)[1] for l in f if "  " in l}


def pack(force=False, dry=False, allow_shrink=False):
    """(Re)build PACK_DST/out_<group>.tar.zst for groups whose files changed (size/mtime).
    Safety (2026-10-01, out/ may be dropped once real_engine/store_v1 serves the readers): if out/ is absent, or a group's
    current files do not include EVERY member of its existing archive (a partially deleted group), that group is skipped and its
    archive + sha256 list are kept untouched -- an archive is never rebuilt from partial contents. --allow-shrink overrides
    (deliberate removals only). --dry-run prints the plan and writes nothing."""
    src_parent = os.path.dirname(os.path.join(WS, PACK_SRC))       # .../real_engine
    dst = os.path.join(WS, PACK_DST)
    idx_path = os.path.join(dst, "index.json")
    idx = load(idx_path, {"archives": {}})
    srcd = os.path.join(WS, PACK_SRC)
    if not os.path.isdir(srcd):
        print(f"pack: {PACK_SRC} is absent; all {len(idx['archives'])} archives kept as they are (nothing packed)")
        return
    if not dry:
        os.makedirs(dst, exist_ok=True); os.makedirs(PACK_TMP, exist_ok=True)
    man = load(MANIFEST, {"files": {}})["files"]
    groups, symlinks = pack_plan()
    out = os.path.basename(PACK_SRC)                                  # "out"
    for g, rels in sorted(groups.items()):
        arc = f"out_{g}.tar.zst"
        have = archived_members(dst, g) if arc in idx["archives"] else None
        if have is not None and not allow_shrink:
            missing = have - set(rels)
            if missing:
                print(f"pack {arc}: SKIPPED - source incomplete ({len(missing)} of {len(have)} archived files missing, "
                      f"e.g. {sorted(missing)[:2]}); existing archive kept")
                continue
        stats = [(r, os.stat(os.path.join(WS, PACK_SRC, r))) for r in rels]
        sig = hashlib.sha256("\n".join(f"{r}\t{st.st_size}\t{int(st.st_mtime)}"
                                        for r, st in stats).encode()).hexdigest()
        old = idx["archives"].get(arc)
        if not force and old and old.get("source_signature") == sig and \
                os.path.exists(os.path.join(dst, arc)):
            print(f"pack {arc}: unchanged ({len(rels)} files)")
            continue
        if dry:
            print(f"pack {arc}: WOULD repack ({len(rels)} files; dry run, nothing written)")
            continue
        t0 = time.time()
        sums = {}
        for r, st in stats:                        # sha256 of every source file
            m = man.get(f"{PACK_SRC}/{r}")
            if m and m["size"] == st.st_size and m["mtime"] == int(st.st_mtime):
                sums[r] = m["sha256"]
            else:
                sums[r], secret = sha256(os.path.join(WS, PACK_SRC, r))
                if secret or SECRET_NAME.search(os.path.basename(r)):
                    print(f"  SKIP {PACK_SRC}/{r} - secret pattern; not packed")
                    del sums[r]
        rels = [r for r in rels if r in sums]
        stats = [(r, st) for r, st in stats if r in sums]
        lst = os.path.join(PACK_TMP, f"{g}.list")
        with open(lst, "wb") as f:
            f.write(b"\0".join(f"{out}/{r}".encode() for r in rels) + b"\0")
        tmp = os.path.join(PACK_TMP, arc)
        tar = subprocess.Popen(["tar", "-C", src_parent, "--null", "--no-recursion", "-T", lst,
                                "--format=posix", "--numeric-owner", "-cf", "-"],
                               stdout=subprocess.PIPE)
        subprocess.run(ZSTD_ARGS + ["-f", "-o", tmp], stdin=tar.stdout, check=True)
        tar.stdout.close()
        if tar.wait():
            raise SystemExit(f"tar failed for {arc}")
        # verify: decompress the archive and hash every member against the source hash
        import tarfile
        dz = subprocess.Popen(["zstd", "-dc", "--long=31", tmp], stdout=subprocess.PIPE)
        seen = {}
        with tarfile.open(fileobj=dz.stdout, mode="r|") as tf:
            for m in tf:
                if m.isfile():
                    h = hashlib.sha256(); fo = tf.extractfile(m)
                    for b in iter(lambda: fo.read(8 << 20), b""):
                        h.update(b)
                    seen[m.name[len(out) + 1:]] = h.hexdigest()
        if dz.wait() or seen != sums:
            bad = [r for r in sums if seen.get(r) != sums[r]]
            raise SystemExit(f"VERIFY FAILED {arc}: {len(bad)} mismatches, e.g. {bad[:3]}")
        with open(os.path.join(PACK_TMP, f"out_{g}.sha256"), "w") as f:
            f.writelines(f"{sums[r]}  {out}/{r}\n" for r in rels)
        asz = os.path.getsize(tmp)
        idx["archives"][arc] = {
            "group": g, "files": len(rels), "bytes": sum(st.st_size for _, st in stats),
            "archive_bytes": asz, "archive_sha256": sha256(tmp)[0], "source_signature": sig,
            "sha256_list": f"out_{g}.sha256", "verified": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "zstd": " ".join(ZSTD_ARGS[1:])}
        os.replace(tmp, os.path.join(dst, arc))
        os.replace(os.path.join(PACK_TMP, f"out_{g}.sha256"), os.path.join(dst, f"out_{g}.sha256"))
        os.remove(lst)
        idx["symlinks_not_packed"] = symlinks
        idx["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        save(idx_path, idx)
        print(f"pack {arc}: {len(rels)} files {idx['archives'][arc]['bytes']/1e9:.2f} GB -> "
              f"{asz/1e9:.3f} GB, verified, {time.time()-t0:.0f}s", flush=True)
    for arc in list(idx["archives"]):        # group vanished entirely
        if arc[4:-8] not in groups:
            print(f"pack {arc}: source group gone; archive kept")
    if dry:
        return
    idx["symlinks_not_packed"] = symlinks
    save(idx_path, idx)
    if symlinks:
        print("pack: NOT packed (symlinks out of the tree):", "; ".join(symlinks))


if __name__ == "__main__":
    a = sys.argv[1:] or ["scan"]
    {"scan": lambda: scan(),
     "stage": lambda: [stage_file(r, a[1]) for r in scan()[1]],
     "push": lambda: push(a[1]),
     "batches": lambda: batches(int(a[1]) if len(a) > 1 else 200_000),
     "mark": lambda: mark(a[1:]),
     "reassemble": lambda: reassemble(a[1]),
     "pack": lambda: pack(force="--force" in a, dry="--dry-run" in a, allow_shrink="--allow-shrink" in a)}[a[0]]()
