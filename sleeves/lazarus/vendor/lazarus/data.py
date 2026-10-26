"""Data: canonical Tensor v698 (imported from the pinned engine, never forked), its Yahoo canonical bars, and the signal producers' files.
verify_pins() is the first thing every pass does: any byte drift in the pinned engine = the pass halts (fail closed)."""
import os, json, hashlib, glob
import pandas as pd
from . import cal
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def _pin_rows(pin):
    return [l.split() for l in open(pin).read().splitlines() if l.strip() and not l.startswith("#")]
def verify_pins(C):
    """-> (ok, detail). (1) the 17 v698 engine files under real_engine == PIN_v698; (2) ST bundle shadow/st/st_replay.mjs and
    swing_transition/st_entry.mjs == PIN_st_v698; (3) every .mjs row of the ST pin == its PIN_v698 row; (4) the 10 pinned app/lib .ts
    sources in shadow/st/canon_v698_ts == PIN_st_v698. Mirrors shadow/st/check_st_pin.py steps 1-3 (regress also runs its step 4 rebuild)."""
    P = C["paths"]; drift = []
    V = {p: h for h, p in _pin_rows(P["pin_v698"])}
    for p, h in V.items():
        f = os.path.join(P["tensor_root"], p)
        if not os.path.exists(f) or sha(f) != h: drift.append(p)
    ST = {p: h for h, p in _pin_rows(P["pin_st_v698"])}
    for name, f in (("st_replay.mjs", f"{P['st_dir']}/st_replay.mjs"), ("st_entry.mjs", P["st_entry"])):
        if not os.path.exists(f) or sha(f) != ST.get(name): drift.append("st:" + name)
    for p, h in ST.items():
        if p.endswith(".mjs") and p not in ("st_replay.mjs", "st_entry.mjs") and V.get(p) != h: drift.append("st-vs-v698:" + p)
        if p.endswith(".ts"):
            f = f"{P['st_dir']}/canon_v698_ts/{os.path.basename(p)}"
            if not os.path.exists(f) or sha(f) != h: drift.append("st-ts:" + p)
    return (not drift), dict(v698_files=len(V), st_rows=len(ST), drift=drift)
_B = {}
def bars(C, sym, iv="1d"):
    """closed canonical bars (Tensor engine output, Yahoo source) -> DataFrame[d(session date ET), open, high, low, close, volume]."""
    k = (sym, iv)
    if k not in _B:
        p = f"{C['paths']['engine_bars']}/{iv}/{sym}.csv"; df = None
        if os.path.exists(p):
            b = pd.read_csv(p, usecols=["timestamp", "open", "high", "low", "close", "volume", "barFinality"]); b = b[b.barFinality == "closed"].copy()
            b["d"] = pd.to_datetime(b.timestamp, unit="s", utc=True).dt.tz_convert(cal.TZ).dt.normalize(); df = b.drop(columns=["barFinality"])
        _B[k] = df
    return _B[k]
def prior_close(C, sym, day):
    """close of the last completed session before `day`; a file missing the previous session -> (None, stale day): never a false red (old desk 1.6.0)."""
    b = bars(C, sym)
    if b is None: return None, None
    b = b[b.d < cal.day0(day)]
    if not len(b): return None, None
    last = b.d.iloc[-1]
    if last != cal.prev_td(day): return None, str(last.date())
    return float(b.close.iloc[-1]), str(last.date())
def dv20(C, sym, asof):
    b = bars(C, sym)
    if b is None: return None
    b = b[b.d <= cal.day0(asof)]
    return float((b.close * b.volume).tail(20).mean()) if len(b) >= 20 else None
def load_feed(path, max_age_h, now):
    """producer file -> (obj, health). Fail closed: unreadable or older than max_age_h -> obj None."""
    h = dict(path=path, ok=False)
    try:
        b = open(path, "rb").read(); o = json.loads(b); h["sha256"] = hashlib.sha256(b).hexdigest()
    except Exception as e: h["error"] = str(e)[:120]; return None, h
    g = o.get("generated") or o.get("generated_at")
    try: age = (now - cal.ts(g)).total_seconds() / 3600
    except Exception: age = None
    h.update(generated=g, age_h=None if age is None else round(age, 2))
    if age is None or age > max_age_h: h["error"] = f"stale or undated (age_h={age})"; return None, h
    h["ok"] = True; return o, h
def lab_books(C):
    out = {}
    for p in sorted(glob.glob(f"{C['paths']['lab_books']}/*.json")):
        try: out[os.path.basename(p)] = json.load(open(p))
        except Exception: pass
    return out
def tracker_log(C, oldest):
    """tradeable yahoo-canonical rows of the tracker fire log (shadow/live/fires_log_v3.csv) on/after `oldest`."""
    p = f"{C['paths']['research']}/shadow/live/fires_log_v3.csv"
    if not os.path.exists(p): return []
    f = pd.read_csv(p, dtype=str, keep_default_na=False)
    f = f[(f.time_et >= oldest) & (f.tradeable.str.lower() == "true") & f.bar_source.str.startswith("yahoo")]
    return f.to_dict("records")
