"""Run a source repository's own JavaScript / TypeScript under Node 22 for parity — the original code, unmodified.

stage(): copy the exact files a harness needs into a fresh scratch tree, each verified as the pinned git blob
(sha1 of "blob <len>\\0" + bytes) — from the source checkout named by an environment variable (default: the clone
under /home/user), else from a blob directory ($PARITY_BLOBS, default /home/user/blobs, files named by sha).
TypeScript is transpiled per file to CommonJS with the installed `typescript` compiler (types erased only; the
emitted JavaScript is the source's own statements), so extension-less relative imports resolve as they did under
the source's bundler; stubs are plain modules a harness names explicitly (I/O only, never decision code).
run(): node <driver> with a JSON payload on stdin; the driver prints one JSON document.
(The env-rooted staging the sable / Author harnesses use; tools/parity/node_src.py is the repo-keyed variant other
harnesses use. Every node process runs with a bounded heap.)"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

TS_LIB = "/opt/node22/lib/node_modules/typescript"
NODE_HEAP = "--max-old-space-size=1024"


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def _read_pinned(root, rel, sha):
    p = os.path.join(root, rel)
    if os.path.exists(p):
        b = open(p, "rb").read()
        if blob_sha(b) == sha:
            return b
    alt = os.path.join(os.environ.get("PARITY_BLOBS", "/home/user/blobs"), sha)
    if os.path.exists(alt):
        b = open(alt, "rb").read()
        if blob_sha(b) == sha:
            return b
    raise SystemExit(f"{rel}: no copy hashing to the pinned blob {sha[:12]} (checked {root} and $PARITY_BLOBS)")


def stage(env, default_root, files, stubs=None):
    """files: {relpath: blob_sha}. stubs: {relpath: text} written as is. Returns the scratch tree."""
    root = os.environ.get(env) or default_root
    dst = tempfile.mkdtemp(prefix="parity_node_")
    for rel, sha in files.items():
        b = _read_pinned(root, rel, sha)
        p = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(b)
    for rel, text in (stubs or {}).items():
        p = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
    return dst


def transpile_ts(tree, rels):
    """TypeScript -> CommonJS next to each file (x.ts -> x.js), types erased by the TypeScript compiler."""
    script = r"""
const ts = require(process.argv[2]);
const fs = require("fs");
for (const f of JSON.parse(process.argv[3])) {
  const src = fs.readFileSync(f, "utf8");
  const out = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
    esModuleInterop: true, jsx: ts.JsxEmit.React }, fileName: f });
  fs.writeFileSync(f.replace(/\.tsx?$/, ".js"), out.outputText);
}
"""
    p = os.path.join(tree, "__transpile.cjs")
    with open(p, "w") as f:
        f.write(script)
    files = [os.path.join(tree, r) for r in rels]
    r = subprocess.run(["node", NODE_HEAP, p, TS_LIB, json.dumps(files)], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError("transpile failed: " + r.stderr[-2000:])


def run(tree, driver, payload, name="__driver.mjs", timeout=3600):
    p = os.path.join(tree, name)
    with open(p, "w") as f:
        f.write(driver)
    r = subprocess.run(["node", NODE_HEAP, p], input=json.dumps(payload), capture_output=True, text=True, timeout=timeout,
                       cwd=tree, env=dict(os.environ, TZ="UTC"))
    if r.returncode != 0:
        raise RuntimeError("node harness failed: " + r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def cleanup(tree):
    shutil.rmtree(tree, ignore_errors=True)


def same(a, b, path="", out=None, limit=20):
    """exact structural equality of two JSON values (numbers compared as doubles; a key absent on one side equals
    null on the other — JSON cannot carry JavaScript's undefined)."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            same(a.get(k), b.get(k), f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, f"len {len(a)} != {len(b)}"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                same(x, y, f"{path}[{i}]", out, limit)
    elif isinstance(a, bool) or isinstance(b, bool):
        if a is not b:
            out.append((path, a, b))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if float(a) != float(b):
            out.append((path, a, b))
    elif a != b:
        out.append((path, a, b))
    return out
