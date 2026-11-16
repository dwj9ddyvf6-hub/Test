from __future__ import annotations
import json, os
from datetime import datetime, timezone
from .models import Bar
from .journal import append_line

class BarCache:
    """Local bar cache: cache/bars/<SYMBOL>/<tf>.jsonl, deduped by timestamp (DESIGN §3b)."""
    def __init__(self, root):
        self.root=root; self.bars_dir=os.path.join(root,"bars"); self.meta_path=os.path.join(root,"meta.json")
    def _path(self, symbol, tf): return os.path.join(self.bars_dir, symbol, f"{tf}.jsonl")
    def write_bars(self, symbol, tf, bars):
        path=self._path(symbol,tf); existing=set()
        if os.path.exists(path):
            with open(path) as fh:
                for line in fh:
                    try: existing.add(json.loads(line)["t"])
                    except Exception: pass
        added=0
        for b in sorted(bars, key=lambda x: x.t):
            d=b.to_dict() if isinstance(b,Bar) else b
            if d["t"] in existing: continue
            append_line(path, d); existing.add(d["t"]); added+=1
        if bars: self._update_meta(symbol, tf)
        return added
    def _update_meta(self, symbol, tf):
        meta={}
        if os.path.exists(self.meta_path):
            try: meta=json.load(open(self.meta_path))
            except Exception: meta={}
        bars=self.read_bars(symbol,tf,1)
        meta.setdefault(symbol,{})[tf]={"newest": bars[-1].t if bars else None, "warm": bool(bars)}
        tmp=self.meta_path+".tmp"; json.dump(meta, open(tmp,"w"), indent=1, sort_keys=True); os.replace(tmp,self.meta_path)
    def read_bars(self, symbol, tf, n):
        path=self._path(symbol,tf)
        if not os.path.exists(path): return []
        rows=[]
        with open(path) as fh:
            for line in fh:
                try: rows.append(Bar.from_dict(json.loads(line)))
                except Exception: pass
        rows.sort(key=lambda b:b.t); return rows[-n:] if n else rows
    def cache_age_s(self, symbol, tf, now=None):
        bars=self.read_bars(symbol,tf,1)
        if not bars: return None
        now=now or datetime.now(timezone.utc)
        try: bt=datetime.fromisoformat(bars[-1].t.replace("Z","+00:00"))
        except Exception: return None
        if bt.tzinfo is None: bt=bt.replace(tzinfo=timezone.utc)
        return max(0.0,(now-bt).total_seconds())
    def write_account(self, payload):
        """Persisted door account read-back (cache/account.json), written
        by runtime/cache_warm at warm/session start from
        door.get_account() — the ACCOUNT equity spx_premium's gate
        reads via SleeveContext.account_equity()."""
        path=os.path.join(self.root,"account.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_account(self):
        path=os.path.join(self.root,"account.json")
        if not os.path.exists(path): return None
        try: return json.load(open(path))
        except Exception: return None
    def write_quotes(self, payload):
        """Persisted latest SIP stock quotes (cache/quotes/latest.json),
        written by runtime/quotes_warm at warm time only; consumed by
        adapters/bb_rsi_divergence.py via read_quotes."""
        path=os.path.join(self.root,"quotes","latest.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_quotes(self):
        path=os.path.join(self.root,"quotes","latest.json")
        if not os.path.exists(path): return {}
        try: return json.load(open(path))
        except Exception: return {}
    def write_options(self, underlying, payload):
        path=os.path.join(self.root,"options",underlying,"chain.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def write_qulla(self, payload):
        """Persisted per-session qulla proposals + evaluation evidence
        (cache/qulla/proposals.json), written by runtime/qulla_warm."""
        path=os.path.join(self.root,"qulla","proposals.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_qulla(self):
        path=os.path.join(self.root,"qulla","proposals.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
    def read_options(self, underlying):
        path=os.path.join(self.root,"options",underlying,"chain.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
    def write_kraken(self, payload):
        """Persisted Kraken producer inputs (cache/kraken/inputs.json),
        written by runtime/kraken_warm at warm time only."""
        path=os.path.join(self.root,"kraken","inputs.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_kraken(self):
        path=os.path.join(self.root,"kraken","inputs.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
    def write_earnings(self, payload):
        """Persisted earnings calendar (cache/earnings/calendar.json),
        written by runtime/earnings_warm at warm time only (R-2)."""
        path=os.path.join(self.root,"earnings","calendar.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def write_buyback_scan(self, payload):
        path=os.path.join(self.root,"scan","buyback.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_buyback_scan(self):
        path=os.path.join(self.root,"scan","buyback.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
    def write_iv(self, underlying, payload):
        path=os.path.join(self.root,"options",underlying,"iv.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_iv(self, underlying):
        path=os.path.join(self.root,"options",underlying,"iv.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
    def read_earnings(self):
        path=os.path.join(self.root,"earnings","calendar.json")
        if not os.path.exists(path): return None
        try: return json.load(open(path))
        except Exception: return None
    def write_tensor_bundle(self, payload):
        path=os.path.join(self.root,"tensor","bundle.json"); os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"; json.dump(payload,open(tmp,"w")); os.replace(tmp,path)
    def read_tensor_bundle(self):
        path=os.path.join(self.root,"tensor","bundle.json")
        if not os.path.exists(path): return None
        return json.load(open(path))
