"""The R4 blowoff detector: Wilder RSI(14) and OBV each at or above their trailing-144-bar min + 90% of the
range, rising edge only — the old desk's research code, vendored byte-identical
(desk/vendor/old_desk_research/rsiobv.py: scan_exhaustion for the daily sleeve; run_r4_blowoff_standalone.py:
blowoff_indices_vec for the 1H sleeve, its vectorized mirror) and loaded the way the old sleeves loaded it.
The genome job writes every name's last-close daily row to cache/blowoff_events.json."""
import importlib.util
import os
import sys
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "old_desk_research")
_MODS = {}


def _load(name, filename):
    if name not in _MODS:
        if VENDOR not in sys.path:
            sys.path.insert(0, VENDOR)               # the research modules import rsiobv from their directory
        spec = importlib.util.spec_from_file_location(name, os.path.join(VENDOR, filename))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODS[name] = mod
    return _MODS[name]


def rsiobv():
    return _load("rsiobv", "rsiobv.py")


def r4():
    return _load("r4_blowoff", "run_r4_blowoff_standalone.py")


def bar_date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


def latest_daily_signal(bars):
    """old blowoff_d latest_signal_date: a rising-edge BLOWOFF on the latest bar (signal at bar n-1, not at
    n-2), >= 160 bars; returns the bar's date or None."""
    if len(bars or ()) < 160:
        return None
    dicts = [{"t": bar_date(b) + "T04:00:00Z", "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
              "c": float(b["c"]), "v": float(b.get("v") or 0)} for b in bars]
    try:
        sigs = rsiobv().scan_exhaustion(dicts, rsi_period=14, range_lookback=144)
    except Exception:
        return None
    idx = {s["index"] for s in sigs if s.get("type") == "BLOWOFF"}
    n = len(dicts)
    if (n - 1) in idx and (n - 2) not in idx:
        return dicts[-1]["t"][:10]
    return None


def rising_edges(closes, vols):
    return r4().blowoff_indices_vec(closes, vols)


def run(hub, symbols, path, now, n=600, chunk=200):
    out = {}
    for i in range(0, len(symbols), chunk):
        got = hub.bars("equity_split", "1d", symbols[i:i + chunk], n, cache_only=True)
        for s, bl in got.items():
            if len(bl) >= 252:
                out[s] = [bar_date(bl[-1]), latest_daily_signal(bl)]
    dates = sorted({r[0] for r in out.values()})
    doc = {"at": now, "date": dates[-1] if dates else None, "rows": out}
    write_json_atomic(path, doc)
    return doc


def load(path, session):
    doc = read_json(path, {}) or {}
    return doc.get("rows") if doc.get("date") == session else None
