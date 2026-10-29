"""Monitor read caches: a monitor group whose source computation is heavy (a node process over a watch list, a
universe-wide scan) computes it in a family job — a separate process, never blocking a desk pass (desk/jobs.py) —
and writes <root>/cache/monitor/<name>.json; the group's monitors read it on every pass and record what changed.
A read older than its group's max age is not used (the monitors keep their previous states)."""
import hashlib
import json
import os

from ...util import read_json, write_json_atomic

_DOCS = {}           # path -> ((mtime_ns, size), doc): the group's monitors share one parse per job run


def path(root, name):
    return os.path.join(root, "cache", "monitor", name + ".json")


def write(root, name, at, results, **extra):
    doc = dict(extra, at=at, results=results)
    p = path(root, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    write_json_atomic(p, json.loads(json.dumps(doc, default=str)))
    return doc


def fingerprint(*parts):
    """a render request's identity: its exact JSON (sorted keys) and the context it renders under."""
    h = hashlib.sha1()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, separators=(",", ":"), default=str).encode())
        h.update(b"\0")
    return h.hexdigest()


def reusable(root, name, reqs, fps):
    """(results reused from the group's previous run, requests still to compute). The heavy renderers re-rendered
    every name on every run; a name whose request fingerprint equals the one its stored result came from is the same
    fact recomputed. Both are pure functions of a name's own request (measured 2026-10-17: the same output rendered
    alone or in any batch order, and at any `now` for unchanged bars), so that stored result is the answer."""
    prev = (read_json(path(root, name), None) or {}) if root else {}
    old_fp, old = prev.get("fp") or {}, prev.get("results") or {}
    reused, todo = {}, []
    for r in reqs:
        s = r["symbol"]
        if s in old and old_fp.get(s) == fps[s]:
            reused[s] = old[s]
        else:
            todo.append(r)
    return reused, todo


def _doc(root, name):
    if not root:
        return {}
    p = path(root, name)
    try:
        st = os.stat(p)
    except OSError:
        return {}
    key = (st.st_mtime_ns, st.st_size)
    hit = _DOCS.get(p)
    if hit and hit[0] == key:
        return hit[1]
    doc = read_json(p, None) or {}
    _DOCS[p] = (key, doc)
    return doc


def read_at(root, name):
    """the clock of the newest job run (its doc's `at`), or None when there is none."""
    at = _doc(root, name).get("at")
    return float(at) if at is not None else None


def read(root, name, now, max_age):
    """{symbol: result} of the newest job run, or {} when there is none or it is older than max_age seconds."""
    doc = _doc(root, name)
    at = doc.get("at")
    if at is None or now - float(at) > max_age or float(at) > now + 60:
        return {}
    return doc.get("results") or {}


def hub_bars(engine, needs, symbols, chunk=50):
    """{interval: {symbol: bars}} for a job: the hub's tapes for each need over `symbols` (the engine's own data
    path, the same cache the sleeves read). A need may name a `fallback` source for the names its own source did
    not serve (e.g. Alpaca's 5m bars, extended hours included, while Yahoo refuses this host) — a named divergence
    of the group that declares it; a fallback that is not configured (no credentials) is skipped."""
    out = {}
    for spec in needs:
        syms = list(spec.get("symbols") or symbols)
        got = {}
        for i in range(0, len(syms), chunk):
            got.update(engine.hub.bars(spec["source"], spec["interval"], syms[i:i + chunk], spec["n"]))
        miss = [s for s in syms if not got.get(s)]
        fb = spec.get("fallback")
        if miss and fb and not (fb == "alpaca" and getattr(engine.hub, "alpaca", None) is None):
            for i in range(0, len(miss), chunk):
                try:
                    got.update({k: v for k, v in engine.hub.bars(fb, spec["interval"], miss[i:i + chunk],
                                                                 spec["n"]).items() if v})
                except Exception:              # noqa: BLE001 — a fallback's failure leaves the names unserved
                    pass
        out.setdefault(spec["interval"], {}).update(got)
    return out
