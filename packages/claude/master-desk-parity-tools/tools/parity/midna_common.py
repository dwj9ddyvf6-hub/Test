"""Midna TypeScript parity helpers. The ORIGINAL sources are read from the read-only Midna clones at their pinned
commits (every file is re-hashed as a git blob against the pin before use), compiled with tsc (--noCheck, CommonJS)
into a scratch directory and driven by a small JS harness under Node over JSON cases. The Python port runs the same
cases in this process; the harness module compares.

Trees (environment overrides):
  MIDNA_PAPER   cursor/paper-desk-f184 @ 68315288   default /home/user/br/midna@cursor_paper-desk-f184
  MIDNA_LECTOR  cursor/lector-desk-f184 @ fd0e0a07  default /home/user/br/midna@cursor_lector-desk-f184
  MIDNA_ENTIRE  entire @ 43f08f96                   default /home/user/midna (its working tree matches 43f08f96 on
                every pinned path; the pin check proves it per file)
  MIDNA_MAIN    main @ 7969b522                     default /home/user/br/midna@main"""
import atexit
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

TREES = {"paper": ("MIDNA_PAPER", "/home/user/br/midna@cursor_paper-desk-f184", "68315288cb7af1340ee1a44cf446c6a9bb3e65fa"),
         "lector": ("MIDNA_LECTOR", "/home/user/br/midna@cursor_lector-desk-f184", "fd0e0a07caaf658b0c349517115e1d5491e9d79e"),
         "entire": ("MIDNA_ENTIRE", "/home/user/midna", "43f08f96fce33ee67521002e09f8bc7534cfe264"),
         "main": ("MIDNA_MAIN", "/home/user/br/midna@main", "7969b5229c46403a92290d16da23228e59e7b064")}

# "<tree>:<path>" -> blob sha at the tree's pinned commit (resolved from each clone's object store, or from the
# GitHub tree of the pinned commit, when the record was written)
PIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "midna_pins.json")


def tree_root(tree):
    env, default, _ = TREES[tree]
    return os.environ.get(env) or default


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def pins():
    return json.load(open(PIN_FILE))


_VENDOR_BLOBS = {}


def vendored_blob(sha):
    """a vendored file (desk/vendor) or a MIDNA_BLOBS file with this blob sha — the same bytes as the pinned source,
    for a pinned path the clone did not check out."""
    if not _VENDOR_BLOBS:
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desk", "vendor")
        for d, _, files in os.walk(root):
            for f in files:
                p = os.path.join(d, f)
                _VENDOR_BLOBS.setdefault(blob_sha(open(p, "rb").read()), p)
    extra = os.environ.get("MIDNA_BLOBS")
    if extra and os.path.exists(os.path.join(extra, sha)):
        return os.path.join(extra, sha)
    return _VENDOR_BLOBS.get(sha)


def check_pin(tree, rel):
    want = pins().get(f"{tree}:{rel}")
    if want is None:
        raise SystemExit(f"no pin for {tree}:{rel} (tools/parity/midna_pins.json)")
    p = os.path.join(tree_root(tree), rel)
    if not os.path.exists(p):
        p = vendored_blob(want) or p
    got = blob_sha(open(p, "rb").read())
    if got != want:
        raise SystemExit(f"{tree}:{rel} is {got[:12]}, pinned {want[:12]} — the source tree is not at the pin")
    return p


_BUILDS = {}


def build(tree, files):
    """compile `files` (paths relative to the tree; imports must be pinned too) -> scratch dir with out/<path>.js."""
    key = (tree, tuple(sorted(files)))
    if key in _BUILDS and os.path.isdir(_BUILDS[key]):
        return _BUILDS[key]
    work = tempfile.mkdtemp(prefix=f"midna_{tree}_")
    atexit.register(shutil.rmtree, work, True)          # the compiled build lives for this process only
    for rel in files:
        src = check_pin(tree, rel)
        dst = os.path.join(work, "src", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    ts = [os.path.join(work, "src", f) for f in files if f.endswith(".ts")]
    r = subprocess.run(["tsc", "--module", "node16", "--moduleResolution", "node16", "--target", "es2022", "--outDir", os.path.join(work, "out"),
                        "--rootDir", os.path.join(work, "src"), "--skipLibCheck", "--noCheck", "--noResolve",
                        "--esModuleInterop"] + ts, capture_output=True, text=True, timeout=300)
    if r.returncode != 0 and not os.path.isdir(os.path.join(work, "out")):
        raise RuntimeError("tsc failed: " + (r.stdout + r.stderr)[-3000:])
    for rel in files:                                   # plain .mjs / .js sources ride along unchanged
        if not rel.endswith(".ts"):
            dst = os.path.join(work, "out", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(work, "src", rel), dst)
    _BUILDS[key] = work
    return work


LEAN_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_MAX_THREADS": "1",
            "MALLOC_ARENA_MAX": "2", "UV_THREADPOOL_SIZE": "1"}


def run_js(work, script, payload, timeout=1800, heap_mb=1024):
    """run `script` (CommonJS, cwd = the build's out dir; PAYLOAD read from stdin) and parse its last stdout line."""
    path = os.path.join(work, "out", "harness.cjs")
    with open(path, "w") as f:
        f.write("const PAYLOAD = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" + script)
    r = subprocess.run(["node", f"--max-old-space-size={int(heap_mb)}", path], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=timeout, cwd=os.path.join(work, "out"),
                       env=dict(os.environ, TZ="UTC", **LEAN_ENV))
    if r.returncode != 0:
        raise RuntimeError("node harness failed: " + r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def canon(x):
    """numbers as floats (JSON from Node prints 100000 for 100000.0), everything else as is — exact comparison."""
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    return x


def same(a, b):
    return json.dumps(canon(a), sort_keys=True) == json.dumps(canon(b), sort_keys=True)


# -- deterministic random inputs shared by the Midna harnesses --------------------------------------------------
def sessions_ending(as_of, n):
    """the n trading sessions ending at as_of (desk calendar), oldest first."""
    from desk.sleeves.midna import common as M
    out, d = [], as_of
    while len(out) < n:
        if M.is_trading_day(d):
            out.append(d)
        d = M.add_days(d, -1)
    return out[::-1]


def gen_series(rnd, n, start_px=None, vol=None, hole=0.02, zero_vol=0.03):
    """a context-feed Point path: {close, adj, high, low, open, volume}; holes are zero points (a missing session)."""
    px = start_px or rnd.choice([rnd.uniform(1.5, 8), rnd.uniform(5, 40), rnd.uniform(20, 400)])
    vol = vol or rnd.uniform(0.008, 0.06)
    drift = rnd.gauss(0.0004, 0.0012)
    adjf = rnd.uniform(0.85, 1.0)
    out = []
    for _ in range(n):
        r = rnd.gauss(drift, vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.05, 0.25) if rnd.random() < 0.01 else 0.0)
        o = px * (1 + rnd.gauss(0, vol / 2))
        px = max(0.3, px * (1 + r))
        h = max(o, px) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, px) * (1 - abs(rnd.gauss(0, vol / 2)))
        adjf = min(1.0, adjf * (1 + abs(rnd.gauss(0, 0.0002))))
        if rnd.random() < hole:
            out.append({"close": 0.0, "adj": 0.0, "high": 0.0, "volume": 0.0, "low": None, "open": None})
            continue
        v = 0.0 if rnd.random() < zero_vol else float(int(rnd.lognormvariate(13.0, 1.4)))
        out.append({"close": round(px, 4), "adj": round(px * adjf, 6), "high": round(h, 4), "low": round(lo, 4),
                    "open": round(o, 4), "volume": v})
    return out


def js_point(p):
    """a Point as context.ts sees it (a missing open / low is undefined)."""
    d = {"close": p["close"], "adj": p["adj"], "high": p["high"], "volume": p["volume"]}
    if p.get("open") is not None:
        d["open"] = p["open"]
    if p.get("low") is not None:
        d["low"] = p["low"]
    return d


def js_panel(panel):
    return dict(panel, series={s: [js_point(p) for p in pts] for s, pts in panel["series"].items()})


def desk_closes(years=(2023, 2024, 2025, 2027, 2028)):
    """the desk calendar's weekday full closes and early closes in `years` (outside the 2026 table the Midna sources
    carry). common.is_trading_day reads the desk calendar — a named divergence; a harness whose inputs span other
    years adds these days to the source's own HOLIDAYS / EARLY_CLOSE sets (calendar_js) so the comparison measures the
    rest of the logic exactly. Within 2026 the two tables are equal (tests/test_midna.py)."""
    from datetime import date, timedelta
    from desk.sleeves.midna import common as M
    full, early = [], []
    for y in years:
        d = date(y, 1, 1)
        while d.year == y:
            ymd = d.isoformat()
            if d.weekday() < 5:
                if not M.is_trading_day(ymd):
                    full.append(ymd)
                elif M.session_close_minutes(ymd) != 16 * 60:
                    early.append(ymd)
            d += timedelta(days=1)
    return full, early


def calendar_js(module="./src/lib/equity/rules.js"):
    """JS lines extending the source calendar (rules.ts HOLIDAYS / EARLY_CLOSE) with the desk's closes outside 2026."""
    full, early = desk_closes()
    return ("{ const __r = require(%s); for (const d of %s) __r.HOLIDAYS.add(d); for (const d of %s) __r.EARLY_CLOSE.add(d) }\n"
            % (json.dumps(module), json.dumps(full), json.dumps(early)))
