"""Host for muse-desk-v2 sleeves (Silicon@muse-desk-v2, vendored unmodified at vendor/silicon, manifest-pinned).
Each sleeve's own adapter.evaluate(ctx) runs IN-PROCESS (muse ran one python subprocess per sleeve per tick) against a
shared, memoised bar cache (muse re-read and re-parsed every jsonl file per sleeve per call)."""
import os, sys, json, time, importlib.util, traceback
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor", "silicon"); ET = ZoneInfo("America/New_York")
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from runtime.cache import BarCache          # noqa: E402  (vendored, unmodified)
from runtime.context import SleeveContext   # noqa: E402
from runtime.models import validate_intent  # noqa: E402

def _install_epoch_shim():
    """Efficiency (t183u B): memoize the vendored bridge's ISO->epoch parse WITHOUT editing vendor/silicon (pinned, byte-identical).
    epoch(ts, naive, on_error) is a pure function of (str(ts), naive, on_error) in a fixed-TZ process; misses call the ORIGINAL
    function, so values and exceptions are identical (lru_cache never caches exceptions). The module-level partials that bound the
    original are rebuilt against the memoized one before any adapter imports them. MD2_EPOCH_SHIM=0 disables (used by the A/B proof)."""
    if os.environ.get("MD2_EPOCH_SHIM", "1") == "0": return 0
    import functools
    from adapters import _bridge as B
    if getattr(B, "_md2_shim", False): return 0
    orig = B.epoch
    @functools.lru_cache(maxsize=1 << 19)
    def _c(ts, naive, on_error): return orig(ts, naive=naive, on_error=on_error)
    def epoch(ts, *, naive="utc", on_error="raise"): return _c(str(ts), naive, on_error)
    swap = {id(orig): epoch}; B.epoch = epoch; changed = True
    while changed:   # rebuild partials whose func/keywords reference a swapped object (dependency order, until stable)
        changed = False
        for k, v in list(vars(B).items()):
            if isinstance(v, functools.partial) and id(v) not in swap.values():
                kw = {kk: swap.get(id(vv), vv) for kk, vv in v.keywords.items()}; fn = swap.get(id(v.func), v.func)
                if fn is not v.func or kw != v.keywords:
                    nv = functools.partial(fn, *v.args, **kw); swap[id(v)] = nv; setattr(B, k, nv); changed = True
    B._md2_shim = True; B._md2_epoch_cache = _c; return len(swap)

class MemoCache(BarCache):
    """Same on-disk format/semantics as muse's BarCache; each (sym, tf) file is parsed once per pass, then served
    from memory to every sleeve. Records every request so warm can fetch exactly what consumers ask for."""
    def __init__(self, root):
        super().__init__(root); self._mem = {}; self.requests = set(); self.requests_seen = set(); self.parses = 0
    def sig(self, k):
        try: st = os.stat(self._path(*k)); return (st.st_size, st.st_mtime_ns)
        except OSError: return None
    def new_pass(self): pass   # entries stay valid until their file changes (keyed by size+mtime below)
    def read_bars(self, symbol, tf, n):
        self.requests.add((symbol, tf)); self.requests_seen.add((symbol, tf)); k = (symbol, tf); p = self._path(symbol, tf)
        try: st = os.stat(p); sig = (st.st_size, st.st_mtime_ns)
        except OSError: sig = None
        hit = self._mem.get(k)
        if hit is None or hit[0] != sig:
            self.parses += 1; hit = self._mem[k] = (sig, super().read_bars(symbol, tf, 0))
        rows = hit[1]; return rows[-n:] if n else list(rows)

SHIM = _install_epoch_shim()

STRUCT_SHA = "0a2f117b1eeea9b20454d8bee612dc06f29f0d63f9382f4434af52b06fec69fb"
def _install_struct_shim():
    """Efficiency (t183u B, dominant stage): saty_gpt_v02 StructureEngine.update scanned the WHOLE stream history for a duplicate
    bar end on every new bar (O(n^2) per evaluation; 4.3 s of a 10 s market-hours muse pass). Records are appended only after
    'start >= previous end' and 'end - start = duration > 0', so ends are strictly increasing: once a record's end is below the
    new end, no earlier record can match. The method is recompiled from the vendored source with exactly that early exit; the
    file stays byte-identical, and the shim installs ONLY when the file matches the pinned sha (any upstream change disables it)."""
    if os.environ.get("MD2_STRUCT_SHIM", "1") == "0": return False
    import hashlib, inspect, textwrap
    path = f"{ROOT}/core/saty_gpt_v02/structure.py"
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != STRUCT_SHA: return False
    import core.saty_gpt_v02.structure as S
    cls = next(v for v in vars(S).values() if inspect.isclass(v) and v.__module__ == S.__name__ and "update" in vars(v) and "_streams" in inspect.getsource(v))
    src = textwrap.dedent(inspect.getsource(cls.update))
    old = "            if r.frame.bar.end == o.bar.end:\n"   # (dedented one level)
    new = "            if r.frame.bar.end < o.bar.end: break\n" + old
    if src.count(old) != 1: return False
    ns = {}; exec(compile(src.replace(old, new), path, "exec"), vars(S), ns)
    cls.update = ns["update"]; cls._md2_shim = True; return True
STRUCT = _install_struct_shim()

def _load(sid):
    p = f"{ROOT}/adapters/{sid}.py"; spec = importlib.util.spec_from_file_location(f"md2_adapter_{sid}", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class MuseSleeve:
    source = "muse-desk-v2"; owner = "md2 (port of User's muse-desk-v2)"; venue = "shadow"
    def __init__(self, entry):
        self.entry = entry; self.sid = entry["id"]; self.family = entry["module"]; self.tf = "intents"; self.params = entry.get("params", {})
        self.principal = float((entry.get("slice") or {}).get("capital_usd") or 10000); self.slots = None; self.status = "installed"; self.reason = ""
        self.cadence_s = int(entry.get("cadence_s", 300)); self.parked = bool(entry.get("parked"))
        try: self.mod = _load(self.sid)
        except Exception as e: self.mod = None; self.status, self.reason = "blocked", f"adapter import failed: {type(e).__name__}: {e}"[:200]
    def evaluate(self, cache, now, positions, cash, journal):
        """-> (list of validated v2 intent dicts, error-or-None). An exception is recorded, never propagated."""
        if self.mod is None: return [], self.reason
        ctx = SleeveContext(self.sid, now, cache, positions, dict(capital_usd=self.principal, cash_usd=cash), self.params, journal)
        try:
            out = self.mod.evaluate(ctx) or []
            held = {p["symbol"] for p in positions}; ok = []
            for it in out:
                validate_intent(it, held_symbols=held if it.get("kind") == "exit" else None); ok.append(it)
            return ok, None
        except Exception as e:
            return [], f"{type(e).__name__}: {str(e)[:160]}"
    def describe(self):
        return dict(sid=self.sid, source=self.source, owner=self.owner, family=self.family, tf=f"cadence {self.cadence_s}s", principal=self.principal,
                    status=self.status, reason=self.reason, venue=self.venue, parked=self.parked)

def load():
    cfg = json.load(open(f"{ROOT}/config/sleeves.json")); out = [MuseSleeve(e) for e in cfg["sleeves"]]
    cat = []
    for s, e in zip(out, cfg["sleeves"]):
        doc = (s.mod.__doc__ or "").strip().split("\n")[0][:200] if s.mod else ""
        cat.append(dict(sid=s.sid, source="muse-desk-v2", family=e["module"], strategy=doc, entry="sleeve-owned (sleeves/%s.py)" % s.sid, exit="sleeve-owned exit intents",
                        data="WARMUP_BARS=" + json.dumps(getattr(s.mod, "WARMUP_BARS", {}) if s.mod else {}), status=s.status, reason=s.reason, merged_into=None,
                        origin=f"Silicon@muse-desk-v2:sleeves/{s.sid}.py"))
    cat.append(dict(sid="shen_fade", source="femto-lean", family="shen_fade", strategy="Shen fade (Femto-lean only, per attachment)", entry="", exit="", data="",
                    status="blocked", reason="source not found: searched every branch tree of Femto-lean, Silicon, Test, Midna (2026-10-24) - no path matching shen_fade", merged_into=None,
                    origin="Femto-lean@backup-master-20261021 (claimed)"))
    return out, cat
