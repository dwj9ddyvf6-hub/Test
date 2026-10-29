"""The analysis engine's files.

  state/analysis/screen/<session>.json.gz  one session's screen, written ONCE: the bytes go to a temporary file that
                                           is then hard-linked to the name, and a link refuses an existing name, so a
                                           screen is never rewritten (desk/lab/store.py's rule). The bytes are
                                           deterministic (sorted keys and rows, gzip mtime 0).
  state/analysis/summary.json              the last run's outcome, replaced whole at every run that reaches one
  cache/analysis/listing.json              the listing filter's result, refreshed weekly by analysis_inputs
The screen's bars live in the hub's bar cache under two sources of their own (ADJ, RAW; desk/analysis/job.py), so no
other reader's series is touched. Temporary names start with .tmp (tools/state_sync.py never records them); the
record's push carries state/analysis/ like the rest of state/."""
import gzip
import io
import json
import os

from ..util import read_json, write_json_atomic


def analysis_dir(root):
    return os.path.join(root, "state", "analysis")


def screen_dir(root):
    return os.path.join(analysis_dir(root), "screen")


def screen_path(root, session):
    return os.path.join(screen_dir(root), f"{session}.json.gz")


def summary_path(root):
    return os.path.join(analysis_dir(root), "summary.json")


def listing_path(root):
    return os.path.join(root, "cache", "analysis", "listing.json")


def written(root):
    """the sessions whose screen file exists"""
    d = screen_dir(root)
    if not os.path.isdir(d):
        return set()
    return {f[:-len(".json.gz")] for f in os.listdir(d) if f.endswith(".json.gz") and not f.startswith(".tmp")}


def encode(doc):
    raw = json.dumps(doc, sort_keys=True, separators=(",", ":"), default=str).encode()
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as g:
        g.write(raw)
    return buf.getvalue()


def write_once(root, session, doc):
    """publish a session's screen -> True, or False when it already exists (it is left exactly as it is)"""
    path = screen_path(root, session)
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), f".tmp_{session}.{os.getpid()}")
    with open(tmp, "wb") as f:
        f.write(encode(doc))
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(tmp, path)                           # atomic, and never over an existing file
        return True
    except FileExistsError:
        return False
    finally:
        os.unlink(tmp)


def read(root, session):
    with gzip.open(screen_path(root, session), "rt") as f:
        return json.load(f)


def write_summary(root, summary):
    return write_json_atomic(summary_path(root), summary, indent=1)


def read_listing(root):
    return read_json(listing_path(root), None)


def write_listing(root, doc):
    os.makedirs(os.path.dirname(listing_path(root)), exist_ok=True)
    return write_json_atomic(listing_path(root), doc)
