"""DataHub: every (source, symbol, timeframe) is fetched/parsed ONCE per pass and fanned out to all consumers.
Missing data is a first-class value (Missing(reason)) — never an empty list that a rule could read as 'no signal'."""
import os, json, time, urllib.request, numpy as np

ENGINE = os.environ.get("MD2_ENGINE_BARS", "/home/box/scratch/shadow/engine")
CACHE = os.environ.get("MD2_CACHE", "/workspace/desk2/state/cache")
COLS = ("timestamp", "open", "high", "low", "close", "volume")

class Missing:
    """Absence of evidence. Rules must treat it as 'cannot evaluate' (no entry, exits fall back to time/stop), not as a negative signal."""
    __slots__ = ("reason",)
    def __init__(self, reason): self.reason = reason
    def __bool__(self): return False
    def __repr__(self): return f"Missing({self.reason})"

class Bars:
    """Columnar OHLCV (numpy). t = epoch seconds of bar open, closed bars only."""
    __slots__ = ("t", "o", "h", "l", "c", "v", "extra")
    def __init__(self, t, o, h, l, c, v, extra=None):
        self.t, self.o, self.h, self.l, self.c, self.v = (np.asarray(x, dtype=float) for x in (t, o, h, l, c, v)); self.extra = extra or {}
    def __len__(self): return len(self.c)
    def tail(self, n): return Bars(self.t[-n:], self.o[-n:], self.h[-n:], self.l[-n:], self.c[-n:], self.v[-n:], {k: v[-n:] for k, v in self.extra.items()})

def _http_json(url, timeout=20, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "md2", **(headers or {})})
    from . import netguard
    return json.loads(netguard.urlopen_read(req, timeout=timeout, total=timeout + 15))

class DataHub:
    def __init__(self, engine=ENGINE, cache=CACHE, http=_http_json, keep=420):
        self.engine, self.cache, self.http, self.keep = engine, cache, http, keep
        self._memo = {}; self.stats = dict(file_parses=0, npy_loads=0, http_calls=0, memo_hits=0, missing=0)
        os.makedirs(cache, exist_ok=True)
    def new_pass(self):
        """network evidence is re-fetched every pass; canonical-file bars persist until their file's mtime changes."""
        self._memo = {k: v for k, v in self._memo.items() if k[0] == "eq"}
    def _m(self, key, fn):
        if key in self._memo: self.stats["memo_hits"] += 1; return self._memo[key]
        v = fn(); self._memo[key] = v
        if isinstance(v, Missing): self.stats["missing"] += 1
        return v
    # ---- canonical equity bars (Tensor v698 engine output, Yahoo source) ----
    def equity(self, sym, iv="1d", extra_cols=()):
        try: mt = os.stat(f"{self.engine}/{iv}/{sym}.csv").st_mtime_ns
        except OSError: mt = time.strftime("%F")   # fallback source (Alpaca daily) refreshes per day
        return self._m(("eq", sym, iv, tuple(extra_cols), mt), lambda: self._equity(sym, iv, tuple(extra_cols)))
    def _equity(self, sym, iv, extra_cols):
        src = f"{self.engine}/{iv}/{sym}.csv"
        if not os.path.exists(src):
            return self._alpaca_daily(sym) if iv == "1d" and sym.isalpha() else Missing(f"no canonical {iv} bars for {sym}")
        mt = os.path.getmtime(src); tag = f"{iv}_{sym}_{int(mt)}_{'-'.join(extra_cols)}"
        npz = f"{self.cache}/{iv}/{sym}.npz"
        if os.path.exists(npz):
            try:
                z = np.load(npz, allow_pickle=False)
                if str(z["tag"]) == tag:
                    self.stats["npy_loads"] += 1
                    return Bars(*(z[k] for k in "tohlcv"), {k: z["x_" + k] for k in extra_cols})
            except Exception: pass
        import pandas as pd
        self.stats["file_parses"] += 1
        df = pd.read_csv(src, usecols=list(COLS) + ["barFinality"] + list(extra_cols))
        df = df[df.barFinality == "closed"].tail(self.keep)
        if not len(df): return Missing(f"{sym} {iv}: zero closed bars")
        b = Bars(df.timestamp, df.open, df.high, df.low, df.close, df.volume,
                 {k: pd.to_numeric(df[k], errors="coerce").to_numpy(float) for k in extra_cols})
        os.makedirs(os.path.dirname(npz), exist_ok=True); tmp = npz + ".tmp.npz"
        np.savez(tmp, tag=tag, t=b.t, o=b.o, h=b.h, l=b.l, c=b.c, v=b.v, **{"x_" + k: v for k, v in b.extra.items()}); os.replace(tmp, npz)
        return b
    def universe(self, iv="1d"):
        d = f"{self.engine}/{iv}"
        return sorted(f[:-4] for f in os.listdir(d) if f.endswith(".csv")) if os.path.isdir(d) else []
    # ---- crypto: OKX public 4H spot candles + perpetual funding; Coinbase daily ----
    def okx_4h(self, inst):
        return self._m(("okx4h", inst), lambda: self._okx(inst))
    def _okx(self, inst, n=3):
        rows = []; after = ""
        try:
            for _ in range(n):   # 3 x 100 = 300 bars warm-up (spec: >=300 indicator bars)
                self.stats["http_calls"] += 1
                r = self.http(f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=4H&limit=100{after}")
                d = r.get("data") or []
                if not d: break
                rows += d; after = f"&after={d[-1][0]}"
        except Exception as e: return Missing(f"okx {inst}: {type(e).__name__}")
        rows = [x for x in rows if x[8] == "1"]   # confirm flag: completed bars only
        if len(rows) < 50: return Missing(f"okx {inst}: only {len(rows)} completed 4H bars")
        rows.sort(key=lambda x: int(x[0]))
        a = np.array([[int(x[0]) / 1000, *map(float, x[1:6])] for x in rows])
        return Bars(a[:, 0], a[:, 1], a[:, 2], a[:, 3], a[:, 4], a[:, 5])
    def funding(self, inst):
        """latest OBSERVED funding rate for a USDT perpetual (Missing if not observed)."""
        def f():
            try:
                self.stats["http_calls"] += 1
                d = self.http(f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&limit=1").get("data") or []
                return float(d[0]["fundingRate"]) if d else Missing(f"no funding observation {inst}")
            except Exception as e: return Missing(f"funding {inst}: {type(e).__name__}")
        return self._m(("fund", inst), f)
    def coinbase_1d(self, prod):
        def f():
            try:
                self.stats["http_calls"] += 1
                d = self.http(f"https://api.exchange.coinbase.com/products/{prod}/candles?granularity=86400")
            except Exception as e: return Missing(f"coinbase {prod}: {type(e).__name__}")
            d = sorted(d)[:-1]   # drop the in-progress UTC day
            if len(d) < 201: return Missing(f"coinbase {prod}: {len(d)} bars < 201")
            a = np.array(d, dtype=float)   # [time, low, high, open, close, volume]
            return Bars(a[:, 0], a[:, 3], a[:, 2], a[:, 1], a[:, 4], a[:, 5])
        return self._m(("cb", prod), f)

    def _alpaca_daily(self, sym):
        """fallback for symbols outside the canonical engine universe (e.g. QLD): Alpaca 1Day bars, cached per day."""
        day = time.strftime("%F"); p = f"{self.cache}/alpaca1d/{sym}_{day}.npz"
        if os.path.exists(p):
            z = np.load(p); self.stats["npy_loads"] += 1; return Bars(*(z[k] for k in "tohlcv"))
        try:
            from . import warm
            self.stats["http_calls"] += 1; rows = warm.alpaca_multi([sym], "1Day", 700).get(sym) or []
        except Exception as e: return Missing(f"alpaca 1Day {sym}: {type(e).__name__}")
        if len(rows) < 50: return Missing(f"alpaca 1Day {sym}: {len(rows)} bars")
        from datetime import datetime
        t = [datetime.fromisoformat(r.t.replace("Z", "+00:00")).timestamp() for r in rows]
        b = Bars(t, [r.o for r in rows], [r.h for r in rows], [r.l for r in rows], [r.c for r in rows], [r.v for r in rows])
        os.makedirs(os.path.dirname(p), exist_ok=True); np.savez(p, t=b.t, o=b.o, h=b.h, l=b.l, c=b.c, v=b.v); return b
