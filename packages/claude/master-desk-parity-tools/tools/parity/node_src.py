"""Run TypeScript / JavaScript SOURCE code under Node for parity with its Python port.

stage(repo, files) copies each pinned source file (relative path -> git blob sha) from the local clone (or from
the blob store when the clone's working tree holds another version) into a scratch tree, refusing any file whose
bytes do not hash to its pin. build() transpiles the .ts files one by one with TypeScript's transpileModule
(syntax only: no type checking, no edits to the logic; `.ts` import specifiers rewritten to `.js`, CommonJS
output) and copies .mjs / .js / .json unchanged. run() executes a small driver next to the built sources: it
reads the case corpus as JSON on stdin and prints one JSON document — the source's own outputs.

    SRC_<REPO>=/path/to/clone   overrides a clone location (REPO upper-cased, '-' -> '_')
    SRC_BLOBS=/path/to/blobs    the blob store (one file per git blob sha)"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

REPOS = {"chatgpt": "/home/user/chatgpt", "Author-desk": "/home/user/Author-desk",
         "Author-desk-backup": "/home/user/Author-desk-backup",
         "foliotend-tensor-release": "/home/user/foliotend-tensor-release",
         "foliotend-chart-renderer": "/home/user/foliotend-chart-renderer", "midna": "/home/user/midna"}


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def repo_root(repo):
    return os.environ.get("SRC_" + repo.upper().replace("-", "_"), REPOS[repo])


def source_bytes(repo, rel, sha):
    p = os.path.join(repo_root(repo), rel)
    if os.path.isfile(p):
        b = open(p, "rb").read()
        if blob_sha(b) == sha:
            return b
    q = os.path.join(os.environ.get("SRC_BLOBS", "/home/user/blobs"), sha)
    if os.path.isfile(q):
        b = open(q, "rb").read()
        if blob_sha(b) == sha:
            return b
    raise SystemExit(f"source {repo}:{rel} at blob {sha} is not available (clone or blob store)")


def stage(repo, files, root=None, extra=None):
    """files: {relpath: blob_sha} -> a scratch directory holding exactly those bytes. extra: {relpath: text} —
    harness-only shims (e.g. a stub for an import the decision code never calls), listed in the receipt."""
    root = root or tempfile.mkdtemp(prefix="parity_src_")
    for rel, sha in files.items():
        out = os.path.join(root, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(source_bytes(repo, rel, sha))
    for rel, text in (extra or {}).items():
        out = os.path.join(root, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            f.write(text)
    return root


_TRANSPILE = r"""
const ts = require(process.env.TS_PATH);
const fs = require('fs'), path = require('path');
const [src, out] = process.argv.slice(2);
function walk(d) { return fs.readdirSync(d, {withFileTypes: true}).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]); }
for (const f of walk(src)) {
  const rel = path.relative(src, f);
  const dest = path.join(out, rel.replace(/\.tsx?$/, '.js'));
  fs.mkdirSync(path.dirname(dest), {recursive: true});
  if (/\.tsx?$/.test(f)) {
    const r = ts.transpileModule(fs.readFileSync(f, 'utf8'), {fileName: f, compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, rewriteRelativeImportExtensions: true,
      esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX}});
    fs.writeFileSync(dest, r.outputText);
  } else fs.copyFileSync(f, dest);
}
fs.writeFileSync(path.join(out, 'package.json'), JSON.stringify({type: 'commonjs'}));
"""


# every harness node process runs with a bounded heap (the machine is shared)
NODE_HEAP = "--max-old-space-size=1024"


def _ts_path():
    g = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    return os.path.join(g, "typescript")


def build(src_root, out=None):
    out = out or tempfile.mkdtemp(prefix="parity_build_")
    tool = os.path.join(out, "_transpile.cjs")
    with open(tool, "w") as f:
        f.write(_TRANSPILE)
    r = subprocess.run(["node", NODE_HEAP, tool, src_root, out], capture_output=True, text=True,
                       env=dict(os.environ, TS_PATH=_ts_path()))
    if r.returncode != 0:
        raise RuntimeError("transpile failed: " + r.stderr[-3000:])
    os.remove(tool)
    return out


def run(build_root, driver, payload, timeout=1800, name="driver.cjs"):
    """write `driver` (CommonJS, or ESM when name ends in .mjs) into build_root and run it with payload on stdin."""
    p = os.path.join(build_root, name)
    with open(p, "w") as f:
        f.write(driver)
    r = subprocess.run(["node", NODE_HEAP, p], input=json.dumps(payload), capture_output=True, text=True,
                       timeout=timeout, cwd=build_root, env=dict(os.environ, TZ="UTC"))
    if r.returncode != 0:
        raise RuntimeError("node driver failed (exit %s): %s" % (r.returncode, r.stderr[-4000:]))
    return json.loads(r.stdout.strip().splitlines()[-1])


def cleanup(*dirs):
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)


DRIVER_IO = r"""
const fs = require('fs');
const PAYLOAD = JSON.parse(fs.readFileSync(0, 'utf8'));
function nn(v) {            // JSON cannot carry NaN / Infinity: tag them so both sides compare exactly
  if (typeof v === 'number') return Number.isFinite(v) ? (Object.is(v, -0) ? 0 : v) : {__num: String(v)};
  if (Array.isArray(v)) return v.map(nn);
  if (v && typeof v === 'object') { const o = {}; for (const k of Object.keys(v)) { if (v[k] !== undefined) o[k] = nn(v[k]); } return o; }
  return v;
}
function emit(x) { process.stdout.write(JSON.stringify(nn(x)) + '\n'); }
"""


def nn(v):
    """the Python side of DRIVER_IO's nn(): NaN / Infinity tagged, -0 -> 0, tuples -> lists, None-valued keys kept."""
    import math
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        f = float(v)
        if not math.isfinite(f):
            return {"__num": "NaN" if f != f else ("Infinity" if f > 0 else "-Infinity")}
        if f == 0:
            return 0
        return int(f) if f.is_integer() and abs(f) < 2 ** 53 else f
    if isinstance(v, (list, tuple)):
        return [nn(x) for x in v]
    if isinstance(v, dict):
        return {k: nn(x) for k, x in v.items()}
    raise TypeError(type(v))


def canon(v):
    """a JSON round trip of nn(v) — what Node's emit() output parses to (ints and floats unified)."""
    def fix(x):
        if isinstance(x, float) and x.is_integer() and abs(x) < 2 ** 53:
            return int(x)
        if isinstance(x, list):
            return [fix(y) for y in x]
        if isinstance(x, dict):
            return {k: fix(y) for k, y in x.items()}
        return x
    return fix(json.loads(json.dumps(nn(v))))
