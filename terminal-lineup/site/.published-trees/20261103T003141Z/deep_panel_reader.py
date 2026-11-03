#!/usr/bin/env python3
"""Shared reader for the DEEP panel (Engines 3 and 15).

SOURCE OF TRUTH: the panel JSON file (deep_bars.json) is the one
source of record. Everything this module reads besides that file
is a DERIVED CACHE rebuilt from it and validated against it:

- a persisted offset sidecar (symbol -> byte offset, byte length,
  row count), keyed by the panel fingerprint (basename, size,
  mtime_ns), built by one mmap scan and reused afterwards;
- an optional binary symbol-major store (float64 OHLC, float64
  volume, int32 date ordinals, plus a JSON index), built by
  build_deep_binary.py from the panel JSON and accepted only
  while its recorded fingerprint matches the panel on disk.

Neither cache is ever a second source of truth: delete both and
this reader still serves every row from the JSON alone, at mmap
cost, and build_deep_binary.py rebuilds the store from the JSON
at any time.

WHY: the previous per-engine StreamedPanel kept the whole 1 GB
panel text resident (measured 2,005 MB peak RSS, 107 s init per
engine per run), which the OOM killer decides whenever this box's
balloon squeezes MemAvailable below that (measured 1,309 MB
during the 2026-10-30 research session). This reader memory-maps
the file instead: the OS pages in only the symbols actually read,
init is the sidecar load, and the strategy choice is made from
the measured MemAvailable at startup and logged (the self-tuning
reader, research option N2): whole-load is considered only when
the panel is under 25 percent of available RAM (never true on
this box, and the log says so), otherwise mmap always.
"""

import json
import mmap
import os
import re
import sys
import time
from datetime import date

STORE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deep_store")

_HEADER_RE = re.compile(rb'"([^"]+)": \[')


def panel_fingerprint(path):
    st = os.stat(path)
    return f"{os.path.basename(path)}:{st.st_size}:{st.st_mtime_ns}"


def _safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def mem_available_mb():
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return None


class DeepPanelReader:
    """Per-symbol view over the DEEP panel with the StreamedPanel
    interface (contains, len, iter, keys, getitem, items), plus
    lengths() served from the index with no parsing."""

    def __init__(self, panel_path, store_root=None, log=True):
        t0 = time.monotonic()
        self.panel_path = panel_path
        self.store_root = store_root or STORE_ROOT
        self.fingerprint = panel_fingerprint(panel_path)
        self.mem_available_mb = mem_available_mb()
        self._index = None       # sym -> (start, count), binary mode
        self._offsets = None     # sym -> (offset, length, count), json
        self._mm = None
        self._ohlc = self._vol = self._ord = None
        if self._try_binary():
            self._mode = "binary_memmap"
        else:
            self._open_json_mmap()
            self._mode = "json_mmap_sidecar"
        self.init_seconds = time.monotonic() - t0
        panel_bytes = os.path.getsize(panel_path)
        self.strategy = {
            "mode": self._mode,
            "mem_available_mb": self.mem_available_mb,
            "panel_bytes": panel_bytes,
            "whole_load_considered": bool(
                self.mem_available_mb
                and panel_bytes
                < 0.25 * self.mem_available_mb * 1024 * 1024),
            "init_seconds": round(self.init_seconds, 3),
            "fingerprint": self.fingerprint,
        }
        if log:
            print(f"DeepPanelReader: {self.strategy}", file=sys.stderr)

    # ---- binary derived store ----
    def _try_binary(self):
        try:
            import numpy as np
        except ImportError:
            return False
        d = os.path.join(self.store_root, _safe(self.fingerprint))
        meta_p = os.path.join(d, "meta.json")
        if not os.path.exists(meta_p):
            return False
        try:
            with open(meta_p, encoding="utf-8") as fh:
                meta = json.load(fh)
            if meta.get("fingerprint") != self.fingerprint:
                return False
            with open(os.path.join(d, "index.json"),
                      encoding="utf-8") as fh:
                raw = json.load(fh)
            self._index = {s: (int(v[0]), int(v[1]))
                           for s, v in raw.items()}
            total = int(meta["rows_total"])
            self._ohlc = np.memmap(os.path.join(d, "ohlc.bin"),
                                   dtype="<f8", mode="r",
                                   shape=(total, 4))
            self._vol = np.memmap(os.path.join(d, "vol.bin"),
                                  dtype="<f8", mode="r", shape=(total,))
            self._ord = np.memmap(os.path.join(d, "ord.bin"),
                                  dtype="<i4", mode="r", shape=(total,))
            self._lengths = {s: c for s, (_st, c) in self._index.items()}
            return True
        except (OSError, ValueError, KeyError):
            self._index = None
            return False

    # ---- JSON mmap + persisted sidecar ----
    def _sidecar_path(self):
        return os.path.join(
            self.store_root,
            f"sidecar_{_safe(self.fingerprint)}.json")

    def _open_json_mmap(self):
        fh = open(self.panel_path, "rb")
        self._mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        fh.close()
        side = self._sidecar_path()
        data = None
        if os.path.exists(side):
            try:
                with open(side, encoding="utf-8") as sf:
                    data = json.load(sf)
                if data.get("fingerprint") != self.fingerprint:
                    data = None
            except (OSError, ValueError):
                data = None
        if data is None:
            data = self._build_sidecar()
        self._offsets = {s: (int(v[0]), int(v[1]), int(v[2]))
                         for s, v in data["symbols"].items()}
        self._lengths = {s: v[2] for s, v in self._offsets.items()}

    def _build_sidecar(self):
        symbols = {}
        mm = self._mm
        for m in _HEADER_RE.finditer(mm):
            sym = m.group(1).decode("utf-8")
            start = m.end() - 1
            if mm[start + 1:start + 2] == b"]":      # empty array
                symbols[sym] = [start, 2, 0]
                continue
            idx = mm.find(b"]]", start)
            if idx < 0:
                raise ValueError("panel array terminator not found")
            length = idx + 2 - start
            count = mm[start:idx + 2].count(b"], [") + 1
            symbols[sym] = [start, length, count]
        data = {"fingerprint": self.fingerprint, "symbols": symbols}
        os.makedirs(self.store_root, exist_ok=True)
        tmp = self._sidecar_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as sf:
            json.dump(data, sf)
        os.replace(tmp, self._sidecar_path())
        return data

    # ---- StreamedPanel-compatible interface ----
    def _src(self):
        return self._index if self._index is not None else self._offsets

    def __contains__(self, sym):
        return sym in self._src()

    def __len__(self):
        return len(self._src())

    def __iter__(self):
        return iter(self._src())

    def keys(self):
        return self._src().keys()

    def lengths(self):
        return dict(self._lengths)

    def __getitem__(self, sym):
        if self._index is not None:
            start, count = self._index[sym]
            ohlc = self._ohlc[start:start + count]
            vol = self._vol[start:start + count]
            ordd = self._ord[start:start + count]
            rows = []
            for i in range(count):
                v = float(vol[i])
                rows.append([
                    date.fromordinal(int(ordd[i])).isoformat(),
                    float(ohlc[i, 0]), float(ohlc[i, 1]),
                    float(ohlc[i, 2]), float(ohlc[i, 3]),
                    int(v) if v == int(v) else v])
            return rows
        off, length, _c = self._offsets[sym]
        return json.loads(self._mm[off:off + length].decode("utf-8"))

    def items(self):
        for sym in self:
            yield sym, self[sym]
