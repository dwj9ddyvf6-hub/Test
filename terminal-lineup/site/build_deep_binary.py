#!/usr/bin/env python3
"""Build the binary derived store for the DEEP panel.

The panel JSON (deep_bars.json) is the source of record. This
converter reads it once through DeepPanelReader's mmap sidecar
mode (never whole-loaded), writes a symbol-major float64 store
under terminal-lineup/deep_store/<fingerprint>/, and verifies the
store against the JSON before publishing it: total row and
symbol counts must match the panel exactly, and every symbol's
binary slice is compared row for row against the JSON rows for a
deterministic sample plus a full count and value-sum pass over
all symbols. The store is published (meta.json written) only
after verification passes; readers ignore a store with no meta
or a stale fingerprint, so a half-built store is never served.

Checkpointed: progress.json records each finished symbol as it
is appended; a killed run resumes by skipping finished symbols
(the .tmp data files are reopened in append order). A changed
panel fingerprints differently and starts a fresh store.
"""

import json
import os
import sys
import time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from deep_panel_reader import (DeepPanelReader, STORE_ROOT,  # noqa: E402
                               _safe, panel_fingerprint)

PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/deep_bars.json")


def build(panel_path=PANEL_PATH, store_root=None, sample_every=97):
    store_root = store_root or STORE_ROOT
    fp = panel_fingerprint(panel_path)
    final_dir = os.path.join(store_root, _safe(fp))
    meta_p = os.path.join(final_dir, "meta.json")
    if os.path.exists(meta_p):
        with open(meta_p, encoding="utf-8") as fh:
            if json.load(fh).get("fingerprint") == fp:
                print(f"store already built and current: {final_dir}")
                return final_dir
    work_dir = final_dir + ".building"
    os.makedirs(work_dir, exist_ok=True)
    prog_p = os.path.join(work_dir, "progress.json")
    done, rows_total = [], 0
    if os.path.exists(prog_p):
        with open(prog_p, encoding="utf-8") as fh:
            prog = json.load(fh)
        if prog.get("fingerprint") == fp:
            done = prog["done"]
            rows_total = int(prog["rows_total"])
    reader = DeepPanelReader(panel_path, store_root=store_root)
    assert reader._mode == "json_mmap_sidecar", reader._mode
    lengths = reader.lengths()
    symbols = [s for s in reader.keys()]
    index = {}
    pos = rows_total
    t0 = time.monotonic()
    # Resume safety (2026-10-30, remainders fix): a build killed
    # mid-symbol leaves that symbol's partial rows in the data
    # files past the checkpointed rows_total. Appending after
    # them shifts every later symbol's offsets and the finished
    # store fails its own verification (proven on the 15,815-name
    # panel: exactly 243,640 stray rows in all three files, close
    # sum mismatch at AMGN). Truncate each file back to the
    # checkpointed byte length before appending, so resumed data
    # always lands at the offset the index records.
    for fname, itemsize in (("ohlc.bin", 32), ("vol.bin", 8),
                            ("ord.bin", 4)):
        fpath = os.path.join(work_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r+b") as fh:
                fh.truncate(rows_total * itemsize)
    ohlc_f = open(os.path.join(work_dir, "ohlc.bin"), "ab")
    vol_f = open(os.path.join(work_dir, "vol.bin"), "ab")
    ord_f = open(os.path.join(work_dir, "ord.bin"), "ab")
    try:
        # rebuild index for already-done symbols from lengths
        p = 0
        for s in symbols:
            if s in done:
                index[s] = [p, lengths[s]]
                p += lengths[s]
        for sym in symbols:
            if sym in done:
                continue
            rows = reader[sym]
            if len(rows) != lengths[sym]:
                raise ValueError(f"row count mismatch for {sym}")
            ohlc = np.array([[r[1], r[2], r[3], r[4]] for r in rows],
                            dtype="<f8")
            vol = np.array([r[5] for r in rows], dtype="<f8")
            ordd = np.array([date.fromisoformat(r[0]).toordinal()
                             for r in rows], dtype="<i4")
            ohlc.tofile(ohlc_f)
            vol.tofile(vol_f)
            ordd.tofile(ord_f)
            index[sym] = [pos, len(rows)]
            pos += len(rows)
            done.append(sym)
            if len(done) % 250 == 0 or len(done) == len(symbols):
                for f in (ohlc_f, vol_f, ord_f):
                    f.flush()
                with open(prog_p, "w", encoding="utf-8") as fh:
                    json.dump({"fingerprint": fp, "done": done,
                               "rows_total": pos}, fh)
                print(f"progress {len(done)}/{len(symbols)} symbols, "
                      f"{pos} rows, {time.monotonic() - t0:.0f}s",
                      flush=True)
    finally:
        for f in (ohlc_f, vol_f, ord_f):
            f.close()
    rows_total = pos
    # ---- verification against the JSON source of record ----
    total_counted = sum(lengths.values())
    if rows_total != total_counted:
        raise ValueError(
            f"store rows {rows_total} != panel rows {total_counted}")
    if len(index) != len(symbols):
        raise ValueError("index symbol count mismatch")
    ohlc = np.memmap(os.path.join(work_dir, "ohlc.bin"), dtype="<f8",
                     mode="r", shape=(rows_total, 4))
    vol = np.memmap(os.path.join(work_dir, "vol.bin"), dtype="<f8",
                    mode="r", shape=(rows_total,))
    ordd = np.memmap(os.path.join(work_dir, "ord.bin"), dtype="<i4",
                     mode="r", shape=(rows_total,))
    # full pass: per-symbol close-sum check against JSON rows
    for i, sym in enumerate(symbols):
        st, ct = index[sym]
        rows = reader[sym]
        json_close_sum = float(np.sum([r[4] for r in rows]))
        bin_close_sum = float(np.sum(ohlc[st:st + ct, 3]))
        if abs(json_close_sum - bin_close_sum) > 1e-6 * max(1.0, abs(json_close_sum)):
            raise ValueError(f"close sum mismatch for {sym}")
        if i % sample_every == 0 or ct != lengths[sym]:
            # exact row-for-row comparison on the sample
            for j, r in enumerate(rows):
                brow = ohlc[st + j]
                if (date.fromordinal(int(ordd[st + j])).isoformat() != r[0]
                        or float(brow[0]) != float(r[1])
                        or float(brow[1]) != float(r[2])
                        or float(brow[2]) != float(r[3])
                        or float(brow[3]) != float(r[4])
                        or float(vol[st + j]) != float(r[5])):
                    raise ValueError(f"exact row mismatch {sym} row {j}")
    del ohlc, vol, ordd
    with open(os.path.join(work_dir, "index.json"), "w",
              encoding="utf-8") as fh:
        json.dump(index, fh)
    with open(os.path.join(work_dir, "meta.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"fingerprint": fp, "rows_total": rows_total,
                   "symbols": len(index),
                   "source_panel": panel_path,
                   "kind": "derived cache of the panel JSON, "
                           "rebuilt by build_deep_binary.py"}, fh)
    if os.path.exists(final_dir):
        raise ValueError(f"final dir appeared during build: {final_dir}")
    os.replace(work_dir, final_dir)
    print(f"BUILT {final_dir}: {len(index)} symbols, {rows_total} rows, "
          f"verified against panel JSON in {time.monotonic() - t0:.0f}s")
    return final_dir


if __name__ == "__main__":
    build()
