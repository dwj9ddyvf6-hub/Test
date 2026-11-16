from __future__ import annotations
from .journal import append_line

class SleeveContext:
    """DESIGN §4b ctx: local cache only, own positions/slice only, no broker/network."""
    def __init__(self, sleeve_id, now, cache, positions, slice_view, params, journal_path, account_equity=None):
        self.sleeve_id=sleeve_id; self.now=now; self._cache=cache
        self.positions=positions; self.slice=slice_view; self.params=params; self._journal=journal_path
        self._account_equity_override=account_equity
    def account_equity(self):
        """ACCOUNT equity for gate-semantic consumers (spx_premium's
        $37k gate): the door's account read-back cached at warm
        (BarCache cache/account.json). Fixture overrides win, in order:
        constructor arg, params["account_equity"],
        params["extra"]["account_equity"]. None when no read-back is
        cached — gates fail closed. Never a hardcoded number, and
        never the slice (self.slice stays the sizing basis)."""
        if self._account_equity_override is not None:
            try: return float(self._account_equity_override)
            except (TypeError, ValueError): return None
        params=self.params or {}
        for v in (params.get("account_equity"),
                  (params.get("extra") or {}).get("account_equity")
                  if isinstance(params.get("extra"), dict) else None):
            if v is not None:
                try: return float(v)
                except (TypeError, ValueError): return None
        read=getattr(self._cache, "read_account", None)
        if read is not None:
            try: acct=read()
            except Exception: acct=None
            if isinstance(acct, dict) and acct.get("equity") is not None:
                try: return float(acct["equity"])
                except (TypeError, ValueError): return None
        return None
    def bars(self, symbol, tf, n): return self._cache.read_bars(symbol, tf, n)
    def cache_age_s(self, symbol, tf): return self._cache.cache_age_s(symbol, tf, now=self.now)
    def options_chain(self, underlying): return self._cache.read_options(underlying)
    def tensor_bundle(self): return self._cache.read_tensor_bundle()
    def qulla_proposals(self): return self._cache.read_qulla()
    def kraken_inputs(self): return self._cache.read_kraken()
    def earnings_calendar(self): return self._cache.read_earnings()
    def iv_history(self, underlying):
        fn=getattr(self._cache,"read_iv",None)
        try: return (fn(underlying) or {}) if callable(fn) else {}
        except Exception: return {}
    def buyback_scan(self):
        fn=getattr(self._cache,"read_buyback_scan",None)
        try: return (fn() or {}) if callable(fn) else {}
        except Exception: return {}
    def latest_quotes(self):
        fn=getattr(self._cache,"read_quotes",None)
        try: return (fn() or {}) if callable(fn) else {}
        except Exception: return {}
    def session_fills(self):
        """Today's (ET session) fill rows from this sleeve's own journal
        — broker read-back truth recorded by the dispatcher (fill recs
        carry ts + position_intent). Shape: [{position_intent, qty,
        price, symbol, side, ts}]. [] when no fills today; sleeves that
        fail closed on None keep failing closed when the journal is
        unreadable (exception -> None)."""
        from .journal import tail_lines
        from zoneinfo import ZoneInfo
        try: recs=tail_lines(self._journal, 100000)
        except Exception: return None
        today=self.now.astimezone(ZoneInfo("America/New_York")).date().isoformat()
        out=[]
        for r in recs:
            if r.get("event")!="fill": continue
            ts=str(r.get("ts") or "")
            if ts[:10]!=today: continue
            out.append({"position_intent":r.get("position_intent"),"qty":r.get("qty"),
                        "price":r.get("price"),"symbol":r.get("symbol"),
                        "side":r.get("side"),"ts":r.get("ts")})
        return out
    def log(self, event, **fields): append_line(self._journal, {"event":event, "sleeve":self.sleeve_id, "ts":self.now.isoformat(), **fields})
