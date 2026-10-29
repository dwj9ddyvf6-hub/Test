"""Inputs: daily bars as compact arrays, the bad-print guard, and the loaders the replay and the fear-day runs read.

A name's bars are a dict of numpy arrays {d (ISO session strings), t, o, h, l, c, v} (the cache's JSON bars carry t,
o, h, l, c, v). Sources, by config path (never committed):
  * a directory of the split-adjusted daily cache's JSON (cache/bars/alpaca_split/1d, the picker replay's input);
  * the cache tarball itself (cache/bars.tar.xz), streamed member by member, so nothing is extracted to disk;
  * DEEP's bars.parquet (sid, d, o, h, l, c, v, c_raw) and etf_all.parquet (SPY).

guard() is the bad-print guard: a bar is unusable when a price is missing, not positive, or its high is under its
low, or when its close jumps more than 3x (or under 1/3) from the last usable close without its volume reaching 3x
the median of the 20 bars before it (the avoid build's rule, xcheck/avoid/build.py). It is point in time: bar t's
verdict reads bars 0..t only. Unusable bars are masked, never repaired or imputed, and counted."""
import json
import os
import tarfile
from datetime import datetime, timezone

import numpy as np

JUMP = 3.0
VOL_SPIKE = 3.0
VOL_MED_N = 20


def arrays(bars):
    """JSON bars (dicts with t, o, h, l, c, v) -> compact arrays; dates are UTC sessions as the odds engine reads them"""
    n = len(bars)
    out = {k: np.empty(n, float) for k in ("t", "o", "h", "l", "c", "v")}
    for i, b in enumerate(bars):
        for k in ("t", "o", "h", "l", "c"):
            try:
                out[k][i] = float(b[k])
            except (KeyError, TypeError, ValueError):
                out[k][i] = np.nan
        try:
            out["v"][i] = float(b.get("v") or 0)
        except (TypeError, ValueError):
            out["v"][i] = np.nan
    out["d"] = np.array([datetime.fromtimestamp(t, timezone.utc).date().isoformat() if np.isfinite(t) else ""
                         for t in out["t"]])
    return out


def to_bars(a, idx=None):
    """arrays -> the JSON bar dicts desk/picker and desk/terminal read (only the rows in idx, when given)"""
    rows = range(len(a["c"])) if idx is None else idx
    return [{"t": float(a["t"][i]), "o": float(a["o"][i]), "h": float(a["h"][i]), "l": float(a["l"][i]),
             "c": float(a["c"][i]), "v": float(a["v"][i])} for i in rows]


def guard(a):
    """-> boolean mask (True = usable) by the bad-print rule above; point in time"""
    o, h, l, c, v = (np.asarray(a[k], float) for k in ("o", "h", "l", "c", "v"))
    n = len(c)
    ok = np.isfinite(o) & np.isfinite(h) & np.isfinite(l) & np.isfinite(c) & (o > 0) & (h > 0) & (l > 0) & (c > 0)
    ok &= h >= l
    vv = np.where(np.isfinite(v), v, np.nan)
    last = np.nan
    for i in range(n):
        if not ok[i]:
            continue
        if np.isfinite(last):
            r = c[i] / last
            if r > JUMP or r < 1.0 / JUMP:
                w = vv[max(0, i - VOL_MED_N):i]
                w = w[np.isfinite(w)]
                med = float(np.median(w)) if len(w) == VOL_MED_N else np.nan
                if not (np.isfinite(vv[i]) and np.isfinite(med) and vv[i] > VOL_SPIKE * med):
                    ok[i] = False
                    continue
        last = c[i]
    return ok


def masked(a, ok):
    """the usable bars only (a forecaster computes on these and scatters back; unusable bars give NaN)"""
    return {k: (np.asarray(v)[ok] if hasattr(v, "__len__") and len(v) == len(ok) else v) for k, v in a.items()}


# ---------------------------------------------------------------- the daily cache (picker replay's input)
def _sym(name):
    return os.path.basename(name)[:-5]


def iter_cache(path, sub="bars/alpaca_split/1d/"):
    """(sym, JSON bars) for every name in a directory of <SYM>.json or in the cache tarball; files starting with "_"
    (the coverage file) are skipped, as tools/picker_replay.py does. Sorted by symbol for a directory; tar order for a
    tarball (the caller sorts)"""
    if os.path.isdir(path):
        for f in sorted(os.listdir(path)):
            if f.endswith(".json") and not f.startswith("_"):
                with open(os.path.join(path, f)) as fh:
                    b = json.load(fh)
                yield f[:-5], (b if isinstance(b, list) else (b.get("bars") or []))
        return
    with tarfile.open(path, "r|*") as tf:
        for m in tf:
            if not (m.isfile() and m.name.startswith(sub) and m.name.endswith(".json")):
                continue
            if os.path.basename(m.name).startswith("_"):
                continue
            b = json.loads(tf.extractfile(m).read())
            yield _sym(m.name), (b if isinstance(b, list) else (b.get("bars") or []))


def load_cache(path):
    """{sym: arrays} sorted by symbol"""
    out = {s: arrays(b) for s, b in iter_cache(path)}
    return {s: out[s] for s in sorted(out)}


# ---------------------------------------------------------------- DEEP (bars.parquet + etf_all.parquet)
def load_deep(data_dir, columns=("sid", "d", "o", "h", "l", "c", "v", "c_raw")):
    import pandas as pd
    b = pd.read_parquet(os.path.join(data_dir, "bars.parquet"), columns=list(columns))
    b["d"] = pd.to_datetime(b["d"])
    e = pd.read_parquet(os.path.join(data_dir, "etf_all.parquet"))
    s = e[e["s"] == "SPY"].copy()
    s["d"] = pd.to_datetime(s["d"])
    spy = s.sort_values("d").set_index("d")["c"].astype(float)
    return b, spy
