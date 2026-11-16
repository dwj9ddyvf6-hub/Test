"""One immutable, content-hashed market-data snapshot per cycle (V3-SCOPE §7.2).
Workers receive read-only views of this single snapshot; a cycle never
observes a half-written warm, and a corrupted snapshot fails closed."""
from __future__ import annotations
import hashlib, json, os
from types import MappingProxyType


class SnapshotCorrupt(Exception):
    pass


def _freeze(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return tuple(_freeze(v) for v in obj)
    return obj


def _canonical(data) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      default=str).encode()


class Snapshot:
    def __init__(self, data, asof, snap_hash=None):
        self._data = data
        self.asof = asof
        self.hash = snap_hash or hashlib.sha256(_canonical(data)).hexdigest()
        self._frozen = None

    @property
    def data(self):
        """Deep-frozen read-only view."""
        if self._frozen is None:
            self._frozen = _freeze(self._data)
        return self._frozen

    @property
    def plain(self):
        return self._data

    def verify(self) -> bool:
        return hashlib.sha256(_canonical(self._data)).hexdigest() == self.hash


def build_snapshot(data: dict, asof: str) -> Snapshot:
    return Snapshot(dict(data), asof)


# PURGE-1 retention: nothing reads a snapshot after its own cycle
# (cycle.py re-reads the just-saved path for integrity; that cycle's
# workers open it by exact path). Pre-cure the store grew one file per
# cycle forever — 196 files / 1.3 GB in the desk's first day. Keep the
# newest few for forensics/rollback; prune on every save, fail-soft.
SNAPSHOT_KEEP = 3


def prune_snapshots(directory: str, keep: int = SNAPSHOT_KEEP) -> int:
    """Remove all but the newest `keep` snapshot files; return count."""
    try:
        names = [n for n in os.listdir(directory) if n.endswith(".json")]
    except OSError:
        return 0
    if len(names) <= keep:
        return 0
    paths = sorted((os.path.join(directory, n) for n in names),
                   key=lambda p: os.path.getmtime(p))
    removed = 0
    for p in paths[:-keep] if keep else paths:
        try:
            os.remove(p)
            removed += 1
        except OSError:
            pass
    return removed


def save_snapshot(snap: Snapshot, directory: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, snap.hash + ".json")
    if not os.path.exists(path):
        doc = {"hash": snap.hash, "asof": snap.asof, "data": snap.plain}
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(doc, fh, sort_keys=True)
        os.replace(tmp, path)
    prune_snapshots(directory)
    return path


def load_snapshot(path: str) -> Snapshot:
    with open(path) as fh:
        doc = json.load(fh)
    snap = Snapshot(doc["data"], doc.get("asof"), snap_hash=doc["hash"])
    if not snap.verify():
        raise SnapshotCorrupt(f"snapshot hash mismatch: {path}")
    return snap
