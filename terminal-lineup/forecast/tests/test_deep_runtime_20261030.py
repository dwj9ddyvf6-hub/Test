"""Regression blocker for the DEEP panel runtime remainder
(R-01/R-02, 2026-10-30): the cured StreamedPanel still held the
whole 1 GB panel text resident (measured 2,005 MB peak RSS and
107 s init per engine per run in RESEARCH-DEEP-RUNTIME.md), so
either engine died whenever the box balloon squeezed
MemAvailable below that, Engine 3's reference depth math cost
2.1 to 6.3 s per long name (a multi-day two-era pass), and
Engine 15's lengths pass parsed every symbol just to count rows.

Cure: one shared reader (site/deep_panel_reader.py) serving both
engines from a binary derived store or an mmap of the panel JSON
with a persisted offset sidecar (the JSON stays the source of
record; both caches are fingerprint-keyed and rebuildable), a
one-time checkpointed converter (site/build_deep_binary.py), an
incremental bit-identical depth_percentiles_fast in Engine 3,
and index-served lengths in Engine 15.

Fail direction: pre-cure there is no deep_panel_reader module,
no depth_percentiles_fast, and neither refresher references the
shared reader, so this file fails at import and at the source
assertions.
"""
import json
import math
import os
import random
import subprocess
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "site"))
sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))

import refresh_ownnormdepth as e3  # noqa: E402
import refresh_selfanalogue as e15  # noqa: E402
from deep_panel_reader import DeepPanelReader  # noqa: E402
import build_deep_binary  # noqa: E402


def _weekdays(start_iso, count):
    d = date.fromisoformat(start_iso)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _walk_rows(days, seed, start_price=100.0):
    rng = random.Random(seed)
    rows = []
    price = start_price
    for i, d in enumerate(days):
        drift = 0.0004 + 0.004 * math.sin(i / 40.0)
        close = price * math.exp(drift + rng.gauss(0.0, 0.011))
        open_ = price * (1.0 + rng.gauss(0.0, 0.002))
        high = max(open_, close) * (1.0 + abs(rng.gauss(0.0, 0.004)))
        low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, 0.004)))
        vol = 1000000 * (1.0 + 0.3 * math.sin(i / 25.0)
                         + abs(rng.gauss(0.0, 0.1)))
        rows.append([d, round(open_, 4), round(high, 4),
                     round(low, 4), round(close, 4), int(vol)])
        price = close
    return rows


def _panel(tmp_path, n_days=60):
    days = _weekdays("2020-01-02", n_days)
    panel = {"SPY": _walk_rows(days, 1), "BRK.B": _walk_rows(days, 2),
             "AAA": _walk_rows(days[:5], 3), "EMPTY": []}
    path = str(tmp_path / "panel.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(panel, fh)
    return path, panel


def test_reader_json_mode_matches_json_load(tmp_path):
    path, panel = _panel(tmp_path)
    store = str(tmp_path / "store")
    r = DeepPanelReader(path, store_root=store, log=False)
    assert r._mode == "json_mmap_sidecar"
    assert len(r) == len(panel)
    for sym, rows in panel.items():
        assert r[sym] == rows
    assert r.lengths() == {s: len(v) for s, v in panel.items()}
    # residency contract: no attribute holds the panel text or
    # parsed rows for the universe (that residency was the OOM)
    for attr in vars(r).values():
        assert not isinstance(attr, str) or len(attr) < 10000
        assert not (isinstance(attr, dict) and attr and all(
            isinstance(v, list) and v and isinstance(v[0], list)
            for v in attr.values()))


def test_reader_sidecar_reused_not_rebuilt(tmp_path):
    path, _panel_ = _panel(tmp_path)
    store = str(tmp_path / "store")
    r1 = DeepPanelReader(path, store_root=store, log=False)
    side = r1._sidecar_path()
    mtime = os.stat(side).st_mtime_ns
    r2 = DeepPanelReader(path, store_root=store, log=False)
    assert os.stat(side).st_mtime_ns == mtime
    assert r2.init_seconds < 1.0


def test_reader_binary_mode_after_conversion(tmp_path):
    path, panel = _panel(tmp_path)
    store = str(tmp_path / "store")
    build_deep_binary.build(panel_path=path, store_root=store,
                            sample_every=1)
    r = DeepPanelReader(path, store_root=store, log=False)
    assert r._mode == "binary_memmap"
    for sym, rows in panel.items():
        assert r[sym] == rows, sym
    assert r.lengths() == {s: len(v) for s, v in panel.items()}


def test_reader_rejects_stale_binary_store(tmp_path):
    path, panel = _panel(tmp_path)
    store = str(tmp_path / "store")
    build_deep_binary.build(panel_path=path, store_root=store,
                            sample_every=1)
    # panel changes: fingerprint moves, the stale store must be
    # ignored and the JSON (source of record) served instead
    panel["AAA"] = panel["AAA"] + [panel["AAA"][-1]]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(panel, fh)
    r = DeepPanelReader(path, store_root=store, log=False)
    assert r._mode == "json_mmap_sidecar"
    assert r["AAA"] == panel["AAA"]


def test_reader_memory_bound_on_large_fixture(tmp_path):
    # A 300-name x 400-session panel (~25 MB of JSON): a
    # whole-load reader's child peak RSS exceeds the panel size
    # several times over; the mmap reader must stay well under
    # the panel size while serving a long name exactly.
    days = _weekdays("2020-01-02", 500)
    # cheap deterministic rows (no rng): the point is panel size,
    # not realism. 1200 names x 500 sessions is about 40 MB of
    # JSON; a whole-load reader peaks at several times the panel
    # size, the mmap reader at interpreter scale.
    panel = {}
    for s in range(1200):
        base = 50.0 + (s % 40)
        panel[f"S{s:04d}"] = [
            [d, base + (i % 7) * 0.11, base + (i % 7) * 0.11 + 0.4,
             base + (i % 7) * 0.11 - 0.4, base + (i % 5) * 0.13,
             1000000 + i] for i, d in enumerate(days)]
    path = str(tmp_path / "big.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(panel, fh)
    panel_bytes = os.path.getsize(path)
    assert panel_bytes > 30 * 1024 * 1024
    # VmHWM from /proc/self/status, not ru_maxrss: rusage peak is
    # inherited across fork and not reset by exec, so a child
    # spawned from this test process would carry the parent's
    # peak as its floor and the measurement would be meaningless.
    hwm = ("[int(l.split()[1]) * 1024 for l in "
           "open('/proc/self/status') "
           "if l.startswith('VmHWM')][0]")
    site_dir = os.path.join(os.path.dirname(__file__), "..", "..", "site")
    code = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from deep_panel_reader import DeepPanelReader;"
        "r = DeepPanelReader(r'%s', store_root=r'%s', log=False);"
        "rows = r['S0001']; assert len(rows) == 500;"
        "print(%s)"
        % (site_dir, path, str(tmp_path / "store"), hwm))
    out = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    peak = int(out.stdout.strip())
    # comparative bound, measured in identical child conditions:
    # a whole json.load of the same panel must peak far higher
    # (this is the residency the cure removes), and the mmap
    # reader must come in under half of it
    load_code = (
        "import json;"
        "json.load(open(r'%s'));"
        "print(%s)" % (path, hwm))
    out2 = subprocess.run([sys.executable, "-c", load_code],
                          capture_output=True, text=True)
    assert out2.returncode == 0, out2.stderr
    load_peak = int(out2.stdout.strip())
    assert load_peak > panel_bytes * 4, (load_peak, panel_bytes)
    assert peak < load_peak / 2, (peak, load_peak)


def test_binary_build_resume_truncates_partial_symbol_tail(tmp_path):
    # A build killed mid-symbol leaves partial rows in the data
    # files past the checkpointed rows_total. Resuming must
    # truncate that tail before appending, or every later
    # symbol's offsets shift and the store fails verification
    # (the 2026-10-30 AMGN close-sum mismatch on the real panel).
    import numpy as np
    from datetime import date as _date
    path, panel = _panel(tmp_path)
    store = str(tmp_path / "store")
    fp = build_deep_binary.panel_fingerprint(path)
    work = os.path.join(
        store, build_deep_binary._safe(fp) + ".building")
    os.makedirs(work)
    # checkpoint: first two symbols (reader order) fully written
    reader = DeepPanelReader(path, store_root=store, log=False)
    order = list(reader.keys())
    done = order[:2]
    rows_total = 0
    with open(os.path.join(work, "ohlc.bin"), "wb") as fo, \
            open(os.path.join(work, "vol.bin"), "wb") as fv, \
            open(os.path.join(work, "ord.bin"), "wb") as fd:
        for sym in done:
            rows = panel[sym]
            np.array([[r[1], r[2], r[3], r[4]] for r in rows],
                     dtype="<f8").tofile(fo)
            np.array([r[5] for r in rows], dtype="<f8").tofile(fv)
            np.array([_date.fromisoformat(r[0]).toordinal()
                      for r in rows], dtype="<i4").tofile(fd)
            rows_total += len(rows)
        # the killed run's partial next symbol: 3 stray rows
        np.zeros((3, 4), dtype="<f8").tofile(fo)
        np.zeros(3, dtype="<f8").tofile(fv)
        np.zeros(3, dtype="<i4").tofile(fd)
    with open(os.path.join(work, "progress.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"fingerprint": fp, "done": done,
                   "rows_total": rows_total}, fh)
    build_deep_binary.build(panel_path=path, store_root=store,
                            sample_every=1)
    r = DeepPanelReader(path, store_root=store, log=False)
    assert r._mode == "binary_memmap"
    for sym, rows in panel.items():
        assert r[sym] == rows, sym


def test_depth_percentiles_fast_identical_to_reference():
    rng = random.Random(7)
    for hw, tw, pw, n in ((5, 10, 10, 300), (63, 750, 750, 2973),
                          (3, 4, 5, 120)):
        rows = []
        price = 50.0
        for i in range(n):
            c = price * math.exp(rng.gauss(0, 0.01))
            rows.append([f"2020-01-{(i % 28) + 1:02d}", price,
                         max(price, c) * 1.002,
                         min(price, c) * 0.998, c, 1000])
            price = c
        d0, p0 = e3.depth_percentiles(rows, pct_window=pw,
                                      high_window=hw, tr_window=tw)
        d1, p1 = e3.depth_percentiles_fast(
            rows, high_window=hw, tr_window=tw, pct_window=pw)
        assert d0 == d1
        assert p0 == p1


def test_both_refreshers_use_shared_reader():
    for mod in (e3, e15):
        src = open(mod.__file__, encoding="utf-8").read()
        assert "DeepPanelReader" in src, mod.__name__
        assert "deep_panel_reader" in src, mod.__name__
    src15 = open(e15.__file__, encoding="utf-8").read()
    assert "panel.lengths()" in src15
    src3 = open(e3.__file__, encoding="utf-8").read()
    assert "depth_percentiles_fast(rows)" in src3
