"""GATE-DISTANCE-20261114 (H-TRIAGE-1): fail-open gate-distance recorder.

For each evaluated sleeve, record how close the binding gate came:
the gate's measured value, its threshold, and the distance in the
gate's own units. Probes are pure functions over the cycle's
snapshot view; they read no desk state and write none. The cycle
calls record_cycle() at the eval-result journal seam inside a
fail-open guard: any exception in the recorder is swallowed and
counted on the roll as gate_distance_errors; a recorder failure
can never fail a cycle, delay dispatch, or alter an intent.
Instrumentation only, the same contract class as the DSK-7 stage
timings.

Record schema (one JSON object per probe, appended to
state/gate_distance.jsonl):
  {asof, sleeve, symbol, gate, measured, threshold, distance,
   unit, passed, probe, note}

A sleeve whose view lacks its series carries measured=None with
the reason named in note, never a fabricated 0.

NSM forward shadow: an absorption evaluation whose latest-bar
volume-shock ratio lands in [1.5, 2.0) is additionally written
with probe="nsm_band", so the negative-space shadow cohort
accrues from the same JSONL without a second instrument.

Falsifier (H-TRIAGE-1, verbatim): with gate-distance logging
live for 5 sessions, the insufficient_evidence share of a triage
re-run must fall below 25%, or the packs' missing field is
something else and gets named.
"""
import json
import os
import sys
from decimal import Decimal

_DESK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _common():
    """The aster sleeves' shared gate math, imported the same way
    the research prototype imports it (read-only use)."""
    p = os.path.join(_DESK_ROOT, "aster_sleeves")
    if p not in sys.path:
        sys.path.insert(0, p)
    import _common as _c
    return _c


def _bars(view, key):
    return (view.get("bars") or {}).get(key) or []


def _rec(out, asof, sleeve, symbol, gate, measured, threshold, unit,
         probe, note="", passed=None):
    if measured is None or threshold is None:
        out.append(dict(asof=asof, sleeve=sleeve, symbol=symbol,
                        gate=gate, measured=None, threshold=threshold,
                        distance=None, unit=unit, passed=None,
                        probe=probe,
                        note=note or "unmeasurable_from_view"))
        return
    dist = measured - threshold
    if passed is None:
        if gate.endswith("_min"):
            passed = measured >= threshold
        elif gate.endswith("_max"):
            passed = measured <= threshold
        else:
            passed = dist >= 0
    out.append(dict(asof=asof, sleeve=sleeve, symbol=symbol, gate=gate,
                    measured=measured, threshold=threshold,
                    distance=dist, unit=unit, passed=bool(passed),
                    probe=probe, note=note))


# ---- probe families (each takes (out, asof, sleeve, view)) ----

def _probe_sma200(out, asof, sleeve, view):
    key, sym = {
        "aster_native_eth_sma200": ("ETH/USD|1Day", "ETH/USD"),
        "aster_native_btc_eth_sma200": ("BTC/USD|1Day", "BTC/USD"),
    }[sleeve]
    b = _bars(view, key)
    if len(b) >= 200:
        closes = [float(x["c"]) for x in b]
        sma = sum(closes[-200:]) / 200
        margin = closes[-1] / sma - 1.0
        _rec(out, asof, sleeve, sym, "close_over_sma200", margin, 0.0,
             "frac", "sma200",
             f"close {closes[-1]} vs SMA200 {sma:.2f}, {len(closes)} bars",
             passed=bool(margin > 0))
    else:
        _rec(out, asof, sleeve, sym, "close_over_sma200", None, 0.0,
             "frac", "sma200", f"only {len(b)} bars in view")


def _latest_rate(view, sym):
    rows = (view.get("funding") or {}).get(sym)
    if rows is None:
        return None
    if isinstance(rows, (int, float)):
        return float(rows)
    if isinstance(rows, dict):
        for k in ("rate", "funding_rate", "value", "last"):
            if k in rows and isinstance(rows[k], (int, float)):
                return float(rows[k])
        rows = rows.get("records") or rows.get("rates") \
            or rows.get("history") or []
    if not rows:
        return None
    last = rows[-1]
    if isinstance(last, (int, float)):
        return float(last)
    for k in ("rate", "funding_rate", "value"):
        if k in last:
            return float(last[k])
    return None


_FUNDING = {
    "aster_link_nfs_norm_vol": ("LINKUSDT", 0.00015, "funding_max"),
    "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash":
        ("ADAUSDT", 0.0002, "funding_max"),
    "aster_squeeze_ada_fullcash": ("ADAUSDT", 0.0002, "funding_max"),
    "aster_abs_neg_ada_fullcash": ("ADAUSDT", 0.0, "funding_max"),
    "aster_abs_nonneg_ada_fullcash": ("ADAUSDT", 0.0, "funding_min"),
}


def _probe_funding(out, asof, sleeve, view):
    sym, thr, gate = _FUNDING[sleeve]
    r = _latest_rate(view, sym)
    _rec(out, asof, sleeve, sym, gate, r, thr, "rate", "funding",
         "latest settled funding rate in view")


_ABSORPTION = {
    "aster_abs_base_ada_fullcash": ("PF_ADAUSD|4Hour", "ADA/USD"),
    "aster_abs_base_ada_vol1pct": ("PF_ADAUSD|4Hour", "ADA/USD"),
    "aster_abs_link_4h": ("PF_LINKUSD|4Hour", "LINK/USD"),
}


def _probe_absorption(out, asof, sleeve, view):
    key, sym = _ABSORPTION[sleeve]
    b = _bars(view, key)
    if len(b) < 300:
        _rec(out, asof, sleeve, sym, "vol_shock_mult", None, 2.0,
             "x vol-EMA", "absorption", f"only {len(b)} bars in view")
        return
    vol_ema = price_ema = None
    last_ratio = None
    for x in b:
        v, c = Decimal(str(x["v"])), Decimal(str(x["c"]))
        vol_ema = v if vol_ema is None else \
            (Decimal(2) * v + Decimal(19) * vol_ema) / Decimal(21)
        price_ema = c if price_ema is None else \
            (Decimal(2) * c + Decimal(49) * price_ema) / Decimal(51)
        last_ratio = float(v / vol_ema) if vol_ema else None
    flags = _common()._absorption_flags(b, Decimal(2))
    confirmed, count = flags[len(b) - 2]
    note = (f"latest bar v/volEMA {last_ratio:.3f}; signal-bar "
            f"confirmed={confirmed}, count={count} "
            f"(warmup needs >=300)")
    _rec(out, asof, sleeve, sym, "vol_shock_mult", last_ratio, 2.0,
         "x vol-EMA", "absorption", note, passed=bool(confirmed))
    if last_ratio is not None and 1.5 <= last_ratio < 2.0:
        # NSM forward shadow cohort, same instrument (see docstring).
        _rec(out, asof, sleeve, sym, "vol_shock_mult", last_ratio, 2.0,
             "x vol-EMA", "nsm_band", note, passed=bool(confirmed))


def _probe_breakout(out, asof, sleeve, view):
    b = _bars(view, "PF_ADAUSD|4Hour")
    if len(b) > 22:
        sig = b[-2]
        boundary = max(float(r["h"]) for r in b[-22:-2])
        margin = float(sig["c"]) / boundary - 1.0
        _rec(out, asof, sleeve, "ADA/USD", "close_over_20bar_high",
             margin, 0.0, "frac", "breakout",
             f"signal close {sig['c']} vs boundary {boundary}",
             passed=bool(margin > 0))
    else:
        _rec(out, asof, sleeve, "ADA/USD", "close_over_20bar_high",
             None, 0.0, "frac", "breakout",
             f"only {len(b)} bars in view")


_RSI2_SLEEVES = (
    "aster_rec_rsi2_long_touch_a", "aster_rec_rsi2_long_touch_b",
    "aster_rec_rsi2_long_fixed_a", "aster_rec_rsi2_long_fixed_b",
    "aster_rec_rsi2_vertical_touch_a", "aster_rec_rsi2_vertical_touch_b",
    "aster_rec_rsi2_vertical_fixed_a", "aster_rec_rsi2_vertical_fixed_b")


def _probe_rsi2(out, asof, sleeve, view):
    qqq = _bars(view, "QQQ|1Day")
    closes = [float(x["c"]) for x in qqq]
    if len(closes) < 200:
        _rec(out, asof, sleeve, "QQQ",
             "rsi2_below_10_and_close_over_sma200", None, 10.0,
             "RSI points", "rsi2",
             f"only {len(closes)} QQQ daily bars in view")
        return
    r = _common()._rsi(closes, 2)
    if isinstance(r, (list, tuple)):
        r = r[-1] if r else None
    sma = sum(closes[-200:]) / 200
    _rec(out, asof, sleeve, "QQQ",
         "rsi2_below_10_and_close_over_sma200",
         (float(r) if r is not None else None), 10.0, "RSI points",
         "rsi2",
         f"RSI2 {r}; close {closes[-1]} vs SMA200 {sma:.2f} "
         f"({'above' if closes[-1] > sma else 'below'})",
         passed=bool(r is not None and r < 10 and closes[-1] > sma))


_PROBES = {}
for _s in ("aster_native_eth_sma200", "aster_native_btc_eth_sma200"):
    _PROBES[_s] = _probe_sma200
for _s in _FUNDING:
    _PROBES[_s] = _probe_funding
for _s in _ABSORPTION:
    _PROBES[_s] = _probe_absorption
for _s in ("aster_breakout_ada_fullcash", "aster_breakout_ada_vol1pct"):
    _PROBES[_s] = _probe_breakout
for _s in _RSI2_SLEEVES:
    _PROBES[_s] = _probe_rsi2

PROBED_SLEEVES = tuple(sorted(_PROBES))


def record(asof, sleeve, view):
    """Gate-distance records for one sleeve over the snapshot view.
    Sleeves without a probe return an empty list (unprobed is a
    named state in the coverage record, not a silent one)."""
    fn = _PROBES.get(sleeve)
    if fn is None:
        return []
    out = []
    fn(out, asof, sleeve, view)
    return out


def record_cycle(state_dir, asof, sleeves, view, probes=None):
    """Fail-open cycle entry point. Appends records for every
    probed sleeve in `sleeves` to state/gate_distance.jsonl and
    returns (records_written, error_count). A probe that raises
    is counted and skipped; this function itself may raise only
    on the file append, which the cycle's guard also swallows.
    `probes` overrides the probe map (the fail-open test seam)."""
    probes = _PROBES if probes is None else probes
    records, errors = [], 0
    for sleeve in sleeves:
        fn = probes.get(sleeve)
        if fn is None:
            continue
        try:
            out = []
            fn(out, asof, sleeve, view)
            records.extend(out)
        except Exception:  # noqa: BLE001 - counted, never raised
            errors += 1
    if records:
        path = os.path.join(state_dir, "gate_distance.jsonl")
        with open(path, "a") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
    return len(records), errors
