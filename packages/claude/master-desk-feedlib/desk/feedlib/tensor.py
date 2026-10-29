"""The Tensor engine — FolioTend production v698, executed, never reimplemented — and the flagship's feed.

The engine files are vendored byte-identical (desk/vendor/old_desk_research/tensor_exact/, from the old desk's
engine/tensor_exact/) and every file's sha256 is checked against the old desk's pins (engine/tensor_exact.py
PINNED_HASHES — verified there against the GitHub production snapshot) before node runs; any drift refuses to
run. run() is the old exact_swing_signal(): one node process per (symbol, series), the canonical 160-bar display
window, `swing_lookback` = also evaluate the swing point-in-time on that many bars before the last closed one.

feed(): every pass the flagship asks for its basket + held names: the canonical 1H series (desk.feedlib.canonical),
the engine over each (swing lookback 4 — the last 5 closed bars, the old EXACT_SWING_LOOKBACK; the same run
carries the trailing-5 diagnostics the bearish exit reads), and, for a name whose newest confirmed swing is
fresh and not yet acted on, the 1D / 1W confirmation (the exact consensus-buy on Yahoo daily / weekly bars,
the old fetch_confirmation). Returns the last BARS_KEEP canonical bars per name with the engine output."""
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "old_desk_research",
                      "tensor_exact")
RUNNER = os.path.join(VENDOR, "run_tensor.mjs")
ENGINE_VERSION = "v698"
DISPLAY_BARS = 160
SWING_LOOKBACK = 4
MIN_BARS = 60
TF_BARS = 100
BARS_KEEP = 400
PINNED = {
    "lib/anna-replica.mjs": "40bdae8b7da5a27f0e40c55e6aca3140d7b3701ff0e48c00bd7b7963b19508f3",
    "lib/tensor-enrichment-signals.mjs": "43e1bcab50698985840696266c70c1ab4cbc96f4be9c20d1852306fb79904ce1",
    "lib/tensor-swing-signals.mjs": "1e2192108081890f260ca4596f90fe8ca156cd1d3a1027073f02d570022008e5",
    "lib/anna-epochs.mjs": "486df48d798ed7f79cecd1623ab1a06040a0785c9dda4a098accad20d20c83c7",
    "lib/tensor-date-format.mjs": "9ffb2411cdebf5a5079bbebf5d27457c6ceeb21190f0548eb4edf566cc1d2abc",
    "app/lib/tensor-context.mjs": "bfd8ca00007ddc33570dc3d4471ab072a66cf40e8df7a1a7c97dac41a3ed4c7c",
    "lib/tensor-chart-window.mjs": "45fb46ed5c46692aadc77c3beb7f82869255e3e489dc669ec91d28d1cb1bffc2",
    "lib/tensor-swing-response-registry.mjs": "bb6b5d703700f6b1a2356b0b8e3e4bafedb7066d08fe14f0573091cad7cab5a5",
    "lib/tensor-swing-transition.mjs": "081013f7ed927b0a95d91e2a9be89ec5819ab013e501ef2f2481c4ca24584e8e",
    "lib/tensor-swing-notification.mjs": "e6cc65d220f6a67852565a052e478116a8400f9e352def1052d498fedb9a8708",
    "run_tensor.mjs": "f6507d3c0c30345c4887b836cf59642be99da9631c7c4ae83c3c5af23e80ab84",
}
_VERIFIED = {}


class TensorError(RuntimeError):
    pass


def verify():
    """raise unless every engine file matches its pin (re-checked whenever a file's mtime changes)."""
    for rel, want in PINNED.items():
        p = os.path.join(VENDOR, rel)
        try:
            st = os.stat(p)
        except OSError:
            raise TensorError(f"tensor engine file missing: {rel}")
        key = (st.st_mtime_ns, st.st_size)
        if _VERIFIED.get(rel) == key:
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got != want:
            raise TensorError(f"tensor engine file drifted: {rel} ({got[:12]} != {want[:12]}); refusing to run")
        _VERIFIED[rel] = key


def run(symbol, bars, interval="1h", swing_lookback=0, display_bars=DISPLAY_BARS, timeout=120):
    """the exact engine over [{t (epoch s), o, h, l, c, v}] oldest -> newest; the runner's JSON or TensorError."""
    verify()
    payload = {"symbol": symbol.upper(), "interval": interval, "timezone": "America/New_York", "latestBarOpen": False,
               "displayBars": int(display_bars), "swingLookback": int(swing_lookback),
               "bars": [{"t": int(b["t"]), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                         "c": float(b["c"]), "v": float(b.get("v") or 0)} for b in bars]}
    try:
        p = subprocess.run(["node", RUNNER], input=json.dumps(payload), capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError as e:
        raise TensorError("node is not available") from e
    except subprocess.TimeoutExpired as e:
        raise TensorError(f"tensor runner timed out after {timeout}s") from e
    try:
        res = json.loads((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError) as e:
        raise TensorError(f"tensor runner produced no JSON (exit {p.returncode}): {(p.stderr or '')[:300]}") from e
    if not isinstance(res, dict):
        raise TensorError(f"tensor runner produced non-dict JSON: {type(res).__name__}")
    if not res.get("ok"):
        raise TensorError(f"tensor runner error: {res.get('error')}")
    return res


def consensus_buy(symbol, bars, interval):
    """the exact consensus-buy (green arrow) on the last closed daily / weekly bar: (is_buy, info)."""
    res = run(symbol, bars, interval=interval)
    diag = res.get("diagnostics") or []
    if not isinstance(diag, list):
        raise TensorError(f"tensor diagnostics malformed for {symbol}")
    last = diag[-1] if diag else None
    if last is None:
        return False, None
    if not isinstance(last, dict):
        raise TensorError(f"tensor diagnostic malformed for {symbol}")
    ids = last.get("enrichmentIds") or []
    if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
        raise TensorError(f"tensor enrichmentIds malformed for {symbol}")
    if last.get("timestamp") is None:
        raise TensorError(f"tensor diagnostic missing timestamp for {symbol}")
    return "consensus-buy" in ids, {"t": last["timestamp"], "bull_votes": last.get("bullishVotes"),
                                    "bear_votes": last.get("bearishVotes"), "enrichment_ids": ids}


def scan(series, swing_lookback=SWING_LOOKBACK, workers=8):
    """{SYM: bars} -> {SYM: (True, result) | (False, error)} — independent node processes in parallel."""
    items = list(series.items())
    if not items:
        return {}

    def one(item):
        sym, bars = item
        try:
            return sym, (True, run(sym, bars, swing_lookback=swing_lookback))
        except Exception as e:
            return sym, (False, f"{type(e).__name__}: {str(e)[:200]}")

    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as ex:
        return dict(ex.map(one, items))


def _strip_tf(bars, now, interval):
    """the old strip_forming_bar_tf for 1D / 1W canonical bars (session date = (t + 4h) in ET)."""
    from datetime import datetime, time as dtime, timedelta
    from ..util import ET
    now_et = datetime.fromtimestamp(now, tz=ET)
    today = now_et.date()

    def sess(b):
        return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=ET).date()

    if interval == "1d":
        return [b for b in bars if sess(b) < today or (sess(b) == today and now_et.time() >= dtime(16, 5))]
    monday = today - timedelta(days=today.weekday())
    week_open = not (today.weekday() < 4 or (today.weekday() == 4 and now_et.time() < dtime(16, 5)))
    out = []
    for b in bars:
        m = sess(b) - timedelta(days=sess(b).weekday())
        if m > monday or (m == monday and not week_open):
            continue
        out.append(b)
    return out


def confirmation(hub, sym, now):
    """the old fetch_confirmation: {"daily_green", "weekly_buy", "daily_bar_t", "weekly_bar_t", "note"}; a leg's
    failure leaves it False with a note (never raises)."""
    out = {"daily_green": False, "weekly_buy": False, "daily_bar_t": None, "weekly_bar_t": None, "note": None}
    notes = []
    for key, tkey, label, interval, iv in (("daily_green", "daily_bar_t", "daily", "1d", "1d"),
                                            ("weekly_buy", "weekly_bar_t", "weekly", "1wk", "1w")):
        try:
            tb = (hub.bars("yahoo", iv, [sym], TF_BARS + 2).get(sym) or [])[-TF_BARS:]
            tb = _strip_tf(tb, now, interval)
            if len(tb) < MIN_BARS:
                notes.append("%s: only %d completed bars (need %d)" % (label, len(tb), MIN_BARS))
                continue
            is_buy, info = consensus_buy(sym, tb, interval)
            out[key] = is_buy
            if info:
                out[tkey] = int(info["t"])
        except Exception as e:
            notes.append("%s: %s" % (label, str(e)[:120]))
    if notes:
        out["note"] = "; ".join(notes)
    return out


def feed(feeds, sleeve, now, arg=None):
    """the flagship's pass input: {"series": {SYM: last BARS_KEEP canonical bars}, "engine": {SYM: result},
    "errors": {SYM: reason}, "confirm": {SYM: confirmation}, "status": {SYM: cache|fetch|stale_cache|...},
    "newest": the newest bar open a session could have completed by now (the desk calendar)}."""
    from .canonical import Canonical, latest_completed_open
    root = os.path.dirname(feeds.hub.cache.root)
    can = Canonical(root)
    syms = list(dict.fromkeys(list(sleeve.universe_now(now)) if hasattr(sleeve, "universe_now")
                              else list(sleeve.CONFIG.universe)))
    series, errors = {}, {}
    for s in syms:
        bl = can.bars(s, now)
        if len(bl) >= MIN_BARS:
            series[s] = bl
        else:
            errors[s] = "only %d completed canonical bars (need %d): %s" % (len(bl), MIN_BARS, can.status.get(s))
    res = scan(series)
    engine = {}
    for s, (ok, r) in res.items():
        if ok:
            engine[s] = {k: r.get(k) for k in ("swings", "diagnostics", "lastClosedTimestamp", "engineVersion",
                                              "swingVersion")}
        else:
            errors[s] = r
    meta = {}
    if getattr(sleeve, "engine", None) is not None:
        meta = (sleeve.engine.store.sleeve_get(sleeve.CONFIG.sleeve_id) or {}).get("meta") or {}
    acted = meta.get("acted") or {}
    confirm = {}
    for s, e in engine.items():
        swings = [ev for ev in (e.get("swings") or []) if (ev.get("swing") or {}).get("confirmed")]
        if swings and str(acted.get(s)) != str(swings[-1].get("timestamp")):
            confirm[s] = confirmation(feeds.hub, s, now)
    return {"asof": now, "series": {s: bl[-BARS_KEEP:] for s, bl in series.items()}, "engine": engine,
            "errors": errors, "confirm": confirm, "status": dict(can.status), "engine_version": ENGINE_VERSION,
            "newest": latest_completed_open(now)}
