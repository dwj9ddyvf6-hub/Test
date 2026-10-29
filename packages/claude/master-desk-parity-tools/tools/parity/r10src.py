"""Source loader for the quant_research R10 / R8 harnesses: the archive's own files, read from a blobs directory
(R10_BLOBS, one file per git blob sha, fetched with `gh api .../git/blobs/<sha>`), checked against their pinned blob
sha, copied into a fresh temporary directory on disk and imported from there under private module names. The
temporary directory is removed on every exit."""
import contextlib
import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile

R10_BLOBS = os.environ.get("R10_BLOBS", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/"
                                        "quant/blobs_qr")
COMMIT = "d170596b4d3f24712da933683ceb6d9ee95d6937"
REPO = "quant-research-backup"


def blob(sha):
    b = open(os.path.join(R10_BLOBS, sha), "rb").read()
    got = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
    if got != sha:
        raise RuntimeError(f"blob {sha} does not match its bytes ({got})")
    return b


def _term(signum, frame):
    raise SystemExit(128 + signum)                      # SIGTERM unwinds through the finally blocks


@contextlib.contextmanager
def source_tree(files, prefix="qr_r10_src_"):
    """files: {relative path: blob sha}. Yields (tmp, load) where load(rel, name) imports one file."""
    import signal
    import threading
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, _term)
    tmp = tempfile.mkdtemp(prefix=prefix)
    loaded = []
    try:
        for rel, sha in files.items():
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(blob(sha))
        sys.path.insert(0, tmp)

        def load(rel, name):
            spec = importlib.util.spec_from_file_location(name, os.path.join(tmp, rel))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            loaded.append(name)
            spec.loader.exec_module(mod)
            return mod
        yield tmp, load
    finally:
        if tmp in sys.path:
            sys.path.remove(tmp)
        for name in list(sys.modules):
            f = getattr(sys.modules[name], "__file__", None) or ""
            if name in loaded or f.startswith(tmp):
                sys.modules.pop(name, None)
        shutil.rmtree(tmp, ignore_errors=True)
