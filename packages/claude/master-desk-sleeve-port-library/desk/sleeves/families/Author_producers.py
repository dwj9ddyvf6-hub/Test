"""Author research producers: the research box's own programs (quant-research-backup ref main, commit ce5ccbcd,
Author-research/), the ones that wrote the files the Lazarus lanes read (desk/sleeves/families/lazarus.py INPUT_FILES /
LAB_DIR), run here as background desk jobs on the research-relative layout under <root>/inputs/lazarus.

Vendored byte-exact under desk/vendor/Author_research/<research-relative path> (desk/vendor/MANIFEST.json pins every blob;
tests/test_vendor.py re-hashes them): the producers' code (Python, the node production engine, shell runners) and the small
frozen configs they read. Large inputs and producer state (the hash-chained tracker ledger, the events history parquets, the
lab panel) are pinned in desk/vendor/Author_research/INPUTS.json and placed by tools/fetch_Author_inputs.py.

Materialisation (one deterministic, recorded text substitution per code file; the vendored bytes never change):
  * every vendored code file is written to <root>/cache/Author/run/<path> with these literal replacements, in this order:
        "/workspace/Author-research" -> <root>/inputs/lazarus      (the research root: data, outputs and the code's own paths)
        "/workspace/gh-deepdive"     -> <root>/inputs/gh-deepdive   (the box's gh-deepdive volume: the research DB's genome sources)
        "/workspace/backup"          -> <root>/inputs/lazarus/REBUILD/box/backup_tooling  (the box's backup tooling, archived there)
        "/home/box/scratch"          -> <root>/cache/Author/scratch (the box scratch: engine store, Yahoo payloads, caches, locks)
        "/workspace"                 -> <root>/inputs              (the rest of the box's research volume: the free-disk checks of
                                                                   the alt-data / options producers, /workspace/registry ...)
    and hard-linked (copied across filesystems) to <root>/inputs/lazarus/<path>, so the research root holds code and data side by
    side exactly as on the box: paths derived from __file__ (SH = dirname(__file__), sleeve_feed's H, node's process.cwd()) resolve
    to the same tree as the hard-coded ones. A vendored data file is copied to <root>/inputs/lazarus/<path> when absent or when
    its bytes drifted from the pin. <root>/cache/Author/run/MATERIALIZED.json records every file (blob, substitutions, sha256 out).
  * env vars the sources already read are set to the same mapped paths (SHADOW_SCRATCH; TZ=America/New_York as the box).
  * Python: the research venv <root>/inputs/lazarus/.venv, built by the vendored shadow/ensure_venv.sh (the box's own auto-heal:
    python3 -m venv + pip install -r requirements.txt, the box's pinned freeze) before every job; node: the host's Node 22.

Jobs (the research box's scheduler since 2026-10-14 = the Lazarus loop's jobs table, lazarus-desk config/lazarus.json @a3319569,
blob 5a0a4fed, vendored as desk/vendor/lazarus/lazarus.json): a slot HH:MM runs once on a trading day while
now - slot < 3 h (lazarus/main.py _job_due) -> desk schedule `weekday:12345&et:HH:MM-<HH:MM + 2:59>` (cadence 20 h) plus a
trading-day check inside the job (a market holiday weekday exits at once); a job with several slots -> one 24-minute window per
slot with a 25-minute cadence (one run per slot; Lazarus keyed each slot); friday_cmd replaces cmd on Fridays; timeout_s is the
subprocess timeout. Lazarus' internal jobs (publish, state_backup) and the terminal export are monitor-only machinery and do
not run here.

Named divergences:
  1. paths: the substitution and hard-link layout above (the box ran the same files in place under /workspace/Author-research).
  2. sync producers: Lazarus ran tracker_watch synchronously right before each pass of its slot; here it is a background job and
     the lanes read its output at their first pass after it finishes (every desk pass reads the files fresh).
  3. Lazarus' fear-window timeout cap on tracker_watch (sync_cap, part of the removed fear_day gate) is not applied.
  4. ledger continuation: the tracker continues the backed-up ledger (98,995 records, seq 1..98,995, head b478279cdb85b039, last
     record 2026-10-14 18:30 ET): append() chains from the last record's hash, and run() skips every key already logged as a fire,
     so fires the box logged are never re-logged and later ones are logged on the first run here with their true detection time
     (late_detection marks them). Records the box wrote after that snapshot are not in this chain.
  5. the close tracker's subprocess timeout is 4 h here (TIMEOUT_MIN_S), the box's 2 h a floor: on this 4-core host its
     four pandas workers share the cores with the loop and the other producers at job priority, and its 2026-10-16 run
     (the first with a cold hourly engine store) was killed at 2 h before logging the session's fires, which the next
     run would have logged late.
  6. the options producer's one-time backfills (OPTIONS_IVSKEW/jobs/nightly.sh: job A's liquid and small/micro panels, job B's
     DoltHub pull) end with a DONE marker in the box scratch, which neither the backup nor the record carries; the box's own
     status.json (a pinned input, also in the record) records each as done, and their consolidated outputs are pinned inputs.
     A marker the scratch lacks is restored from that record (restore_backfill_markers), so a new host does not repeat
     them: about 56,000 Alpaca requests on the desk's own keys from 19:00 ET (the box's runs: 39,398 and 16,532) and
     1,842 DoltHub queries. (Job A's consolidate moves files from the scratch in cache/ into the research root in
     inputs/ with os.replace: one rename that needs the service's whole checkout as one mount, deploy/systemd.)
  7. the options snapshot collector's universe (job C, snapshot_collector.py universe()) is job A's frozen panel file
     WORK/A_<panel>/universe.csv, in the same box scratch; without it the collector falls back to probe_out/
     universe_optionable_2026-11-20.csv, which is neither pinned nor in the record, and stops with FileNotFoundError
     (the host's every run from 2026-10-19 to 10-26: status.json snapshot_collector "error", nightly.log "collector
     rc=12"). A panel file the scratch lacks is rebuilt from job A's pinned consolidated output
     (data/alpaca_rebuild/<panel>/universe_<panel>.csv when present, else the names of daily_<panel>.parquet, 699 of 700
     liquid and 1,259 of 1,262 small/micro names: the ones with no option bars carry no chain), n_contracts 50: the
     collector's own default, which only sizes its open-interest batches (ensure_collector_universe).
  8. nightly.sh exits 0 when the collector failed (it only logs "collector rc=12"), so the desk job read ok while no
     snapshot was written. A collector run of this job that ends in "error" or "stopped_disk_floor" in status.json
     fails the desk job with its last error and the free disk it measured (collector_outcome): a skip is never silent.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime

from ... import calendar as cal
from ...util import ET
from . import Author_altdata as A

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor")
GR = os.path.join(VENDOR, "Author_research")
PREFIX = "Author_research/"
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "ce5ccbcd3634f79358eb096b6e43271989bb27d0",
          "dir": "Author-research/"}
RESEARCH_ROOT = "/workspace/Author-research"
BOX_GH = "/workspace/gh-deepdive"
BOX_BACKUP = "/workspace/backup"
BOX_SCRATCH = "/home/box/scratch"
BOX_VOLUME = "/workspace"           # last: every longer /workspace path above is already mapped
CODE_EXT = (".py", ".mjs", ".js", ".cjs", ".sh")
LINKS = {"DESK_INTEGRATION/lab_live/run/data/tensor": "CORPUS_AUDIT/outside_lab_orig/data/tensor",
         "DESK_INTEGRATION/lab_live/run/data/backtest": "CORPUS_AUDIT/outside_lab_orig/data/backtest"}
SLOT_WINDOW_MIN = 179          # Lazarus: a slot still runs while now - slot < 3 h
MULTI_WINDOW_MIN = 24
MULTI_CADENCE_S = 25 * 60


def _read_json(p, default=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def manifest():
    """{research-relative path: MANIFEST row} of every vendored Author_research file."""
    m = _read_json(os.path.join(VENDOR, "MANIFEST.json"), {}) or {}
    return {k[len(PREFIX):]: v for k, v in m.items() if k.startswith(PREFIX)}


def is_code(rel):
    return rel.endswith(CODE_EXT)


class Paths:
    def __init__(self, root, cfg=None):
        cfg = cfg or {}
        self.root = root
        self.inputs = cfg.get("lazarus_inputs_dir") or os.path.join(root, "inputs", "lazarus")
        self.cache = os.path.join(root, "cache", "Author")
        self.run = os.path.join(self.cache, "run")
        self.scratch = os.path.join(self.cache, "scratch")
        self.logs = os.path.join(self.cache, "log")

    def subs(self):
        return [(RESEARCH_ROOT, self.inputs), (BOX_GH, os.path.join(os.path.dirname(self.inputs), "gh-deepdive")),
                (BOX_BACKUP, os.path.join(self.inputs, "REBUILD", "box", "backup_tooling")), (BOX_SCRATCH, self.scratch),
                (BOX_VOLUME, os.path.dirname(self.inputs))]

    def map(self, s):
        for a, b in self.subs():
            s = s.replace(a, b)
        return s


def substitute(data, subs):
    """the recorded text substitution of one code file: (bytes out, {literal: replacements})."""
    n = {}
    for a, b in subs:
        k = data.count(a.encode())
        if k:
            n[a] = k
            data = data.replace(a.encode(), b.encode())
    return data, n


def _sha256(b):
    return hashlib.sha256(b).hexdigest()


def _link(src, dst):
    if os.path.lexists(dst):
        try:
            if os.path.samefile(src, dst):
                return
        except OSError:
            pass
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def materialize(paths, files=None):
    """write the runnable copy (code substituted -> cache/Author/run, hard-linked into the research root) and place the vendored
    data files under inputs; -> the MATERIALIZED record (also written to cache/Author/run/MATERIALIZED.json)."""
    files = files if files is not None else manifest()
    subs = paths.subs()
    rec = {"source": SOURCE, "substitutions": [list(x) for x in subs], "files": {}}
    for rel, row in sorted(files.items()):
        src = os.path.join(GR, rel)
        with open(src, "rb") as f:
            data = f.read()
        dst_in = os.path.join(paths.inputs, rel)
        os.makedirs(os.path.dirname(dst_in), exist_ok=True)
        if is_code(rel):
            out, n = substitute(data, subs)
            dst = os.path.join(paths.run, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            cur = None
            if os.path.exists(dst):
                with open(dst, "rb") as f:
                    cur = f.read()
            if cur != out:
                tmp = dst + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(out)
                os.chmod(tmp, 0o755 if rel.endswith(".sh") else 0o644)
                os.replace(tmp, dst)
            _link(dst, dst_in)
            rec["files"][rel] = {"blob": row.get("blob_sha"), "kind": "code", "substitutions": n, "sha256": _sha256(out)}
        else:
            cur = None
            if os.path.exists(dst_in):
                with open(dst_in, "rb") as f:
                    cur = f.read()
            if cur != data:
                tmp = dst_in + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dst_in)
            rec["files"][rel] = {"blob": row.get("blob_sha"), "kind": "data", "sha256": _sha256(data),
                                 "restored": cur is not None and cur != data}
    rec["links"] = {}
    for rel, target in sorted(LINKS.items()):                 # the box's lab_live run tree linked the outside lab's data dirs
        ln, tg = os.path.join(paths.inputs, rel), os.path.join(paths.inputs, target)
        os.makedirs(os.path.dirname(ln), exist_ok=True)
        os.makedirs(tg, exist_ok=True)
        if os.path.islink(ln) and os.readlink(ln) != tg:
            os.remove(ln)
        if not os.path.lexists(ln):
            os.symlink(tg, ln)
        rec["links"][rel] = target
    os.makedirs(paths.run, exist_ok=True)
    os.makedirs(paths.scratch, exist_ok=True)
    tmp = os.path.join(paths.run, "MATERIALIZED.json.tmp")
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(paths.run, "MATERIALIZED.json"))
    return rec


# ------------------------------------------------------------------------------------------------- pinned inputs
def pinned_inputs():
    return (_read_json(os.path.join(GR, "INPUTS.json"), {}) or {}).get("files", {})


def missing_inputs(paths, producer):
    """(required, optional): the pinned inputs (tools/fetch_Author_inputs.py) a producer reads that are absent under the
    research root. A missing required input stops the job (e.g. the tracker never starts a new ledger); a missing optional one
    is reported and the producer runs on its own fallback (its add-on logs the failure, exactly as on the box)."""
    req, opt = [], []
    for rel, p in sorted(pinned_inputs().items()):
        if producer in (p.get("used_by") or []) and not os.path.exists(os.path.join(paths.inputs, rel)):
            (req if p.get("required") else opt).append(rel)
    return req, opt


# --------------------------------------------------------------------------------------------------------- jobs
def lazarus_jobs():
    """the producer rows of the Lazarus jobs table (desk/vendor/lazarus/lazarus.json; internal / monitor-only jobs dropped)."""
    J = (_read_json(os.path.join(VENDOR, "lazarus", "lazarus.json"), {}) or {}).get("jobs", {})
    return {k: v for k, v in J.items() if isinstance(v, dict) and v.get("cmd") and not v.get("internal")
            and k in PRODUCER_OF and k not in OFF}


# producers this desk does not run, with the reason; the code stays vendored and tested. altdata_nightly is retired: its SEC
# plug-ins sent a personal email as the User-Agent contact, finra_flow and options_bundle read sources not cleared for this desk
# (off since 2026-10-19), and its one bash chain spent a run asleep on another job's marker until the 4 h limit. One job per
# source replaces it (Author_altdata.py), each source on its own switch in config/altdata.json; a source switched off is listed
# here under its producer, so the lanes that need it are recorded BLOCKED with the missing piece (lazarus.inputs_off).
OFF = {"altdata_nightly": "retired 2026-10-26: replaced by one job per source (Author_altdata.py, config/altdata.json); its SEC "
                          "plug-ins sent a personal email as the User-Agent contact, its FINRA and SqueezeMetrics sources are not "
                          "cleared, and its 2026-10-19 run slept on another job's marker until the 4 h limit"}
ALT_PRODUCERS = {"altdata_wiki": "wikimedia", "altdata_finra": "finra", "altdata_sec": "sec", "altdata_options": "squeezemetrics"}
OFF.update({p: A.off_reason(src) for p, src in ALT_PRODUCERS.items() if A.off_reason(src)})


# Lazarus job -> the producer whose pinned inputs it needs (and whose outputs it writes); chartslector_export (the public
# terminal's chartslector.json) is publish machinery and is not run
PRODUCER_OF = {"tracker_close": "tracker", "tracker_watch": "tracker", "lab_live_daily": "lab_live", "lab_live_feed": "desk_feed",
               "sleeve_feed_am": "sleeve_feed", "sleeve_feed_pm": "sleeve_feed", "altdata_nightly": "altdata",
               "options_snapshot": "options",
               # the per-source alt-data producers (Author_altdata.py); altdata_options is SqueezeMetrics' (barred: never run)
               "altdata_wiki": "altdata_wiki", "altdata_finra": "altdata_finra", "altdata_sec": "altdata_sec",
               "altdata_wswing": "altdata_wswing", "altdata_options": "altdata_options"}
OUTPUTS = {"tracker": ["shadow/log/ledger.jsonl", "shadow/live/latest_fires_v3.json", "shadow/live/fires_log_v3.csv"],
           "lab_live": ["DESK_INTEGRATION/lab_live/out/latest/" + f for f in (
               "1D-cyan-full.json", "1D-cyan-covered.json", "1D-green-full.json", "1W-cyan-full.json", "1W-cyan-covered.json",
               "1W-swing-covered.json", "1W-green-full.json", "1W-green-covered.json", "1W-swing-full.json")]
           + ["shadow/live/desk_extra_fires_v1.json"],
           "desk_feed": ["shadow/live/desk_extra_fires_v1.json"],
           "sleeve_feed": ["shadow/paper_sleeve/live/sleeve_fires_v1.json", "shadow/paper_sleeve/live/cl_fires_v1.json"],
           "altdata": ["ALTDATA_LIVE/heartbeat.json"],
           "altdata_wiki": ["WIKI_LIVE/out/wiki_features_latest.parquet", "WIKI_LIVE/out/wiki_features_history.parquet"],
           "altdata_finra": ["ALTDATA_LIVE/out/finra_ats_events.parquet", "ALTDATA_LIVE/out/finra_svr_history.parquet"],
           "altdata_sec": ["ALTDATA_LIVE/out/insider2_latest.parquet", "ALTDATA_LIVE/out/insider2_history.parquet"],
           "altdata_wswing": ["DESK_INTEGRATION/w_swing_live/out/w_swing_fires_latest.json"],
           "altdata_options": ["ALTDATA_LIVE/out/options_market_latest.parquet"],
           "options": ["OPTIONS_IVSKEW/jobs/status.json"]}


def _hhmm_plus(hhmm, minutes):
    h, m = map(int, hhmm.split(":"))
    t = min(h * 60 + m + minutes, 23 * 60 + 59)
    return f"{t // 60:02d}:{t % 60:02d}"


def schedule_of(job):
    """Lazarus slots -> (desk schedule, cadence_s): see the module docstring."""
    slots = job["slots"]
    if len(slots) == 1:
        return f"weekday:12345&et:{slots[0]}-{_hhmm_plus(slots[0], SLOT_WINDOW_MIN)}", 20 * 3600
    return ",".join(f"weekday:12345&et:{s}-{_hhmm_plus(s, MULTI_WINDOW_MIN)}" for s in slots), MULTI_CADENCE_S


def command_of(job, paths, now_et):
    cmd = job.get("friday_cmd") if job.get("friday_cmd") and now_et.weekday() == 4 else job["cmd"]
    return [paths.map(c) for c in cmd], paths.map(job["cwd"])


THREAD_CAPS = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_MAX_THREADS": "1",
               "MALLOC_ARENA_MAX": "2"}   # resource caps for the shared host (the producers' own process pools stay as written)
# the vendored add-ons' own offline switches, set for every job and not overridable: shadow/addons_sc.py's data.sec.gov
# reads and shadow/addons_w2.py's SEC reads send a personal email as the User-Agent contact, and addons_w2's api.nasdaq.com
# reads a browser User-Agent; the owner's rules forbid both. Offline, each falls back to its frozen snapshot or cache.
OFFLINE_ENV = {"SC_NO_NET": "1", "W2_OFFLINE": "1"}


def research_python():
    """the interpreter the research venv is built with (ensure_venv.sh runs `python3 -m venv`): python3.13 where the
    host has it. The source box ran 3.13.5, Ubuntu 24.04's python3 is 3.12, and PYTHON_CPU_COUNT needs 3.13."""
    return os.environ.get("Author_RESEARCH_PYTHON") or shutil.which("python3.13")


def cpu_cap(meminfo="/proc/meminfo"):
    """the producers' parallel width by memory: the close tracker starts one `node --max-old-space-size=2500` engine
    per CPU (shadow/tracker.py engine()) plus a pool as wide, so about 3 GB a worker with 3 GB left over:
    floor((RAM GiB, rounded up - 3) / 3), between 1 and the CPU count. 12 GB -> 3, 16 GB -> 4, 24 GB -> 7, then
    capped at the CPUs. Each name's output is its own engine's, whatever the width, so the width changes memory and
    time only."""
    try:
        with open(meminfo) as f:
            kb = int(next(line.split()[1] for line in f if line.startswith("MemTotal:")))
    except (OSError, StopIteration, ValueError, IndexError):
        return None
    return max(1, min(os.cpu_count() or 1, int((-(-kb // 1048576) - 3) // 3)))


def env_of(paths, extra=None):
    env = dict(os.environ)
    env.update(THREAD_CAPS)
    if "SEC_USER_AGENT" in env:                    # the vendored producers read it raw: a value failing the guard is replaced
        from ...feedlib import edgar_buyback
        env["SEC_USER_AGENT"] = edgar_buyback.user_agent()
    env.update(TZ="America/New_York", SHADOW_SCRATCH=os.path.join(paths.scratch, "shadow"))
    py = research_python()
    if py:                                         # `python3` resolves to it for the producers (the venv's build)
        shim = os.path.join(paths.scratch, "bin")
        link = os.path.join(shim, "python3")
        if os.path.realpath(link) != os.path.realpath(py):
            os.makedirs(shim, exist_ok=True)
            if os.path.lexists(link):
                os.remove(link)
            os.symlink(py, link)
        env["PATH"] = shim + os.pathsep + env.get("PATH", "")
    cap = os.environ.get("Author_CPU_COUNT") or cpu_cap()
    if cap:
        env.setdefault("PYTHON_CPU_COUNT", str(cap))
    env.update(extra or {})
    env.update(OFFLINE_ENV)
    return env


def ensure_venv(paths, runner=subprocess.run):
    """the vendored shadow/ensure_venv.sh: the research venv <inputs>/.venv from the box's pinned requirements (no-op when it
    imports pandas, pyarrow and numpy)."""
    sh = os.path.join(paths.inputs, "shadow", "ensure_venv.sh")
    r = runner(["bash", sh], cwd=paths.inputs, env=env_of(paths), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"research venv not usable (ensure_venv.sh rc {r.returncode}): {(r.stdout or '')[-200:]}")
    return os.path.join(paths.inputs, ".venv", "bin", "python")


GH_FIRES_1W = ("genome/calib/out/frame_1w.parquet", "genome/out/fires_1w.parquet")


def ensure_research_db(paths, runner=subprocess.run):
    """db/research.duckdb (views over the research parquets, db/views.sql) and db/tables/fires_1w: neither is in the backup, so
    the box's own db/refresh.py rebuilds them: `--only fires_1w` once its gh-deepdive sources are placed, else `--views` (the
    views over whatever sources are present). -> what ran."""
    py = os.path.join(paths.inputs, ".venv", "bin", "python")
    gh = os.path.join(os.path.dirname(paths.inputs), "gh-deepdive")
    have_src = all(os.path.exists(os.path.join(gh, f)) for f in GH_FIRES_1W)
    built = os.path.exists(os.path.join(paths.inputs, "db", "tables", "fires_1w", "data.parquet"))
    arg = "--only" if have_src and not built else "--views"
    cmd = [py, os.path.join(paths.inputs, "db", "refresh.py")] + (["--only", "fires_1w"] if arg == "--only" else ["--views"])
    r = runner(cmd, cwd=paths.inputs, env=env_of(paths), capture_output=True, text=True, timeout=1800)
    return {"cmd": " ".join(cmd[2:]), "rc": r.returncode, "fires_1w": built or (arg == "--only" and r.returncode == 0)}


COLLECTOR_PANELS = ("liquid", "smallmicro")
_UNIVERSE_PY = r"""
import os, sys, pandas as pd
data, work = sys.argv[1], sys.argv[2]
for panel in sys.argv[3:]:
    out = os.path.join(work, "A_" + panel, "universe.csv")
    if os.path.exists(out):
        continue
    csv = os.path.join(data, "alpaca_rebuild", panel, "universe_%s.csv" % panel)
    pq = os.path.join(data, "alpaca_rebuild", panel, "daily_%s.parquet" % panel)
    if os.path.exists(csv):
        U = pd.read_csv(csv)
    elif os.path.exists(pq):
        U = pd.DataFrame({"sym": sorted(pd.read_parquet(pq, columns=["sym"]).sym.astype(str).unique())})
    else:
        continue
    if "n_contracts" not in U.columns:
        U["n_contracts"] = 50
    os.makedirs(os.path.dirname(out), exist_ok=True)
    U[["sym", "n_contracts"]].to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    print(panel, len(U))
"""


def ensure_collector_universe(paths, runner=subprocess.run, py=None):
    """divergence 7: the collector's panel universes WORK/A_<panel>/universe.csv, rebuilt where the scratch lacks them from
    job A's pinned consolidated output (by the research venv: the parquet needs its pyarrow) -> {panel: names} written."""
    work = os.path.join(paths.scratch, "options_ivskew")
    todo = [pn for pn in COLLECTOR_PANELS if not os.path.exists(os.path.join(work, f"A_{pn}", "universe.csv"))]
    if not todo:
        return {}
    py = py or os.path.join(paths.inputs, ".venv", "bin", "python")
    data = os.path.join(paths.inputs, "OPTIONS_IVSKEW", "data")
    r = runner([py, "-c", _UNIVERSE_PY, data, work] + todo, cwd=paths.inputs, env=env_of(paths), capture_output=True,
               text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"options: collector universe not rebuilt (rc {r.returncode}): {(r.stdout or '')[-200:]}")
    return {ln.split()[0]: int(ln.split()[1]) for ln in (r.stdout or "").splitlines() if len(ln.split()) == 2}


COLLECTOR_FAILED = ("error", "stopped_disk_floor")


def _et_ts(s):
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ET).timestamp()
    except ValueError:
        return None


def collector_outcome(paths, since):
    """divergence 8: the snapshot collector's own outcome of a run that started at `since` (status.json) -> the row's
    summary, or RuntimeError when that run ended in error or on the disk floor (nightly.sh still exits 0 on an error)."""
    S = _read_json(os.path.join(paths.inputs, "OPTIONS_IVSKEW", "jobs", "status.json"), {}) or {}
    row = (S.get("jobs") or {}).get("snapshot_collector") or {}
    t = _et_ts(row.get("finished") or row.get("last_heartbeat") or "")
    if t is None or t < since - 60:
        return {"ran": False}
    out = {"ran": True, "state": row.get("state"), "date": row.get("date"), "free_disk_gb": S.get("free_disk_gb"),
           "disk_floor_gb": S.get("disk_floor_gb")}
    if row.get("state") in COLLECTOR_FAILED:
        raise RuntimeError(f"options snapshot collector {row.get('state')} (free disk {S.get('free_disk_gb')} GiB, floor "
                           f"{S.get('disk_floor_gb')} GiB): {str(row.get('last_error'))[:240]}")
    return out


SETUP = {"tracker": [ensure_research_db], "options": [ensure_collector_universe]}

# divergence 6: OPTIONS_IVSKEW/jobs/status.json job -> its DONE marker's directory under the scratch's options_ivskew/
BACKFILL_DONE = {"alpaca_rebuild": "A_liquid", "alpaca_smallmicro_addon": "A_smallmicro", "dolthub_pull": "B"}


def restore_backfill_markers(paths):
    """divergence 6: each one-time backfill the box's status.json records as done gets its DONE marker (the box's
    finish time) where the scratch lacks it -> the markers restored. A backfill running or unfinished there is left
    to run."""
    st = (_read_json(os.path.join(paths.inputs, "OPTIONS_IVSKEW", "jobs", "status.json"), {}) or {}).get("jobs") or {}
    out = []
    for job, sub in sorted(BACKFILL_DONE.items()):
        row = st.get(job) or {}
        marker = os.path.join(paths.scratch, "options_ivskew", sub, "DONE")
        if row.get("state") == "done" and row.get("finished") and not os.path.exists(marker):
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w") as f:
                f.write(str(row["finished"]))
            out.append(sub)
    return out


def _out_state(paths, producer):
    st = {}
    for rel in OUTPUTS.get(producer, []):
        p = os.path.join(paths.inputs, rel)
        if os.path.exists(p):
            s = os.stat(p)
            st[rel] = {"bytes": s.st_size, "mtime": round(s.st_mtime, 1)}
        else:
            st[rel] = None
    return st


TIMEOUT_MIN_S = {"tracker_close": 4 * 3600}        # divergence 5


def run_job(name, root, now, cfg=None, runner=subprocess.run, venv=True, extra_env=None):
    """one Lazarus producer job, as the box ran it, on this desk's research root -> small info dict (raises on failure)."""
    job = lazarus_jobs()[name]
    producer = PRODUCER_OF[name]
    now_et = datetime.fromtimestamp(now, tz=ET)
    if not cal.is_trading_day(now_et.date()):
        return {"skipped": "not a trading day (Lazarus runs research jobs on trading days only)"}
    paths = Paths(root, cfg)
    mat = materialize(paths)
    req, opt = missing_inputs(paths, producer)
    if req:
        raise RuntimeError(f"{producer}: {len(req)} required pinned inputs missing under {paths.inputs} "
                           f"(python3 -m tools.fetch_Author_inputs): {', '.join(req)}")
    setup = {}
    if producer == "options":
        setup["backfill_markers_restored"] = restore_backfill_markers(paths)
    if venv:
        ensure_venv(paths, runner)
        for step in SETUP.get(producer, []):
            setup[step.__name__] = step(paths, runner)
    cmd, cwd = command_of(job, paths, now_et)
    os.makedirs(paths.logs, exist_ok=True)
    before = _out_state(paths, producer)
    t0 = time.time()
    with open(os.path.join(paths.logs, f"{name}.log"), "a") as lf:
        lf.write(f"\n== {now_et.isoformat()} {name}\n")
        lf.flush()
        try:
            rc = runner(cmd, cwd=cwd, env=env_of(paths, extra_env), stdout=lf, stderr=subprocess.STDOUT,
                        timeout=max(job["timeout_s"], TIMEOUT_MIN_S.get(name, 0))).returncode
        except subprocess.TimeoutExpired:
            rc = 124
    info = {"rc": rc, "secs": round(time.time() - t0), "cmd": " ".join(cmd)[-200:], "materialized": len(mat["files"]),
            "setup": setup, "missing_optional_inputs": len(opt), "missing_optional_sample": opt[:8],
            "outputs": _out_state(paths, producer)}
    info["changed"] = sorted(k for k, v in info["outputs"].items() if v != before.get(k))
    if rc != 0:
        raise RuntimeError(f"{name} rc {rc} (log cache/Author/log/{name}.log): {json.dumps(info)[:200]}")
    if producer == "options":
        info["collector"] = collector_outcome(paths, t0)
    return info


def _job(name):
    def run(engine):
        return run_job(name, engine.root, engine.clock(), getattr(engine, "cfg", None))
    run.__name__ = f"Author_{name}"
    return run


def jobs_table():
    out = {}
    for name, job in lazarus_jobs().items():
        sched, cadence = schedule_of(job)
        out[f"Author_{name}"] = (sched, cadence, _job(name))
    out.update(A.JOBS)                     # the per-source alt-data jobs that replace altdata_nightly
    return out


JOBS = jobs_table()


def sleeves():
    return []
