#!/usr/bin/env python3
"""Content-addressed asset manifest + served-bytes smoke check.

House fact this fits: every page in this tree is a single
self-contained HTML file (inline CSS and JS, no external assets) and
fetches its own data.json with cache:"no-store". There are no shared
JS/CSS files to rename, so content addressing lands as a manifest:
``asset-manifest.json`` at the site root maps every served file
(the hub, every tool page, every data.json) to its sha256 and byte
count, and each entry's content hash is its address.

Modes:
  --write-manifest   rebuild asset-manifest.json from the tree.
  (default)          verify the tree against the manifest; then, if
                     --serve is given, serve the tree on a local port
                     and verify the bytes a reader would actually be
                     served match the manifest for every entry.
  --published-root P also verify a published copy of this tree at P
                     byte-for-byte against the manifest. (Checked
                     2026-10-29: no published copy of THIS terminal
                     exists in the workspace; the desk-terminal feed
                     under the Femto desk is a different terminal.
                     The leg exists for the day a copy is published.)

Exit code is nonzero and every mismatch is named on any failure:
the check fails loudly, never approximately.

Wiring: stamp_provenance.py is not the publish path; the manifest is
rebuilt and the check run by verify_terminal.sh, the terminal's
post-refresh verification step, and both can be run standalone.
"""

import hashlib
import http.server
import json
import os
import sys
import threading
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(HERE, "asset-manifest.json")
MANIFEST_VERSION = 1


def served_files(root=HERE):
    """Every file a reader can be served: hub + tool pages + data."""
    out = []
    hub = os.path.join(root, "index.html")
    if os.path.exists(hub):
        out.append("index.html")
    for name in sorted(os.listdir(root)):
        sub = os.path.join(root, name)
        if not os.path.isdir(sub):
            continue
        for fname in ("index.html", "data.json"):
            if os.path.exists(os.path.join(sub, fname)):
                out.append(f"{name}/{fname}")
    return sorted(out)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root=HERE):
    files = {}
    for rel in served_files(root):
        p = os.path.join(root, rel)
        files[rel] = {"sha256": digest(p), "bytes": os.path.getsize(p)}
    return {"manifest_version": MANIFEST_VERSION, "files": files}


def write_manifest(root=HERE):
    manifest = build_manifest(root)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def verify_tree(root, manifest):
    problems = []
    listed = set(manifest["files"])
    actual = set(served_files(root))
    for rel in sorted(listed - actual):
        problems.append(f"MISSING {rel}")
    for rel in sorted(actual - listed):
        problems.append(f"UNLISTED {rel} (not in manifest)")
    for rel in sorted(listed & actual):
        p = os.path.join(root, rel)
        want = manifest["files"][rel]
        if os.path.getsize(p) != want["bytes"] or digest(p) != want["sha256"]:
            problems.append(f"MISMATCH {rel}")
    return problems


def verify_served(manifest, port=0):
    """Serve HERE on a throwaway local port and compare the bytes a
    reader receives against the manifest."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = lambda *a, **kw: Quiet(*a, directory=HERE, **kw)  # noqa: E731
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    problems = []
    try:
        for rel, want in sorted(manifest["files"].items()):
            with urllib.request.urlopen(f"{base}/{rel}") as resp:
                body = resp.read()
            if (len(body) != want["bytes"]
                    or hashlib.sha256(body).hexdigest() != want["sha256"]):
                problems.append(f"SERVED MISMATCH {rel}")
    finally:
        server.shutdown()
    return problems


def main(argv):
    if "--write-manifest" in argv:
        manifest = write_manifest()
        print(f"manifest written: {len(manifest['files'])} files")
        return 0
    if not os.path.exists(MANIFEST_PATH):
        print("FAIL: asset-manifest.json missing; run --write-manifest")
        return 1
    manifest = load_manifest()
    problems = verify_tree(HERE, manifest)
    if "--serve" in argv:
        problems += verify_served(manifest)
    if "--published-root" in argv:
        root = argv[argv.index("--published-root") + 1]
        if not os.path.isdir(root):
            problems.append(f"PUBLISHED ROOT MISSING {root}")
        else:
            problems += [f"published: {p}" for p in verify_tree(root, manifest)]
    if problems:
        print(f"SMOKE FAIL ({len(problems)} problems)")
        for p in problems:
            print(" ", p)
        return 1
    print(f"SMOKE PASS: {len(manifest['files'])} files match the manifest"
          + ("; served bytes verified" if "--serve" in argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
