"""The lab's files under state/lab/ (nothing else is ever written by it).

  outcomes/<session>.jsonl.gz  one line per signal, placebo draw and exit / target intent of that session, written
                               ONCE, when its outcomes are final: the bytes go to a temporary file which is then
                               hard-linked to the name, and a link refuses an existing name, so a session's file is
                               never rewritten, and a later run reads it instead of recomputing. The bytes are
                               deterministic (sorted lines, gzip mtime 0).
  summary.json                 the analysis, replaced whole at every run
Temporary names start with .tmp (tools/state_sync.py never records them)."""
import gzip
import io
import json
import os

from ..util import write_json_atomic


def lab_dir(root):
    return os.path.join(root, "state", "lab")


def outcome_path(out_dir, session):
    return os.path.join(out_dir, "outcomes", f"{session}.jsonl.gz")


def written(out_dir):
    """the sessions whose outcome file exists"""
    d = os.path.join(out_dir, "outcomes")
    if not os.path.isdir(d):
        return set()
    return {f[:-len(".jsonl.gz")] for f in os.listdir(d) if f.endswith(".jsonl.gz") and not f.startswith(".tmp")}


def _bytes(rows):
    lines = sorted(json.dumps(r, sort_keys=True, separators=(",", ":"), default=str) for r in rows)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as g:
        g.write(("\n".join(lines) + ("\n" if lines else "")).encode())
    return buf.getvalue()


def write_once(out_dir, session, rows):
    """publish a session's outcome file -> True, or False when it already exists (it is left exactly as it is)"""
    path = outcome_path(out_dir, session)
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), f".tmp_{session}.{os.getpid()}")
    with open(tmp, "wb") as f:
        f.write(_bytes(rows))
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(tmp, path)                           # atomic, and never over an existing file
        return True
    except FileExistsError:
        return False
    finally:
        os.unlink(tmp)


def read(out_dir, session):
    with gzip.open(outcome_path(out_dir, session), "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_summary(out_dir, summary):
    return write_json_atomic(os.path.join(out_dir, "summary.json"), summary, indent=1)
