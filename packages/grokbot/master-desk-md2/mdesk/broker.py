"""Brokers. Default ShadowBroker: fills are simulated at the last observed mark and labelled 'shadow'.
AlpacaReadOnly: account/positions/orders read-back for reconciliation (GET only).
AlpacaPaperBroker: real PAPER orders, md2-* client ids only - DISABLED unless MD2_ORDER_MODE=paper AND an account
listed in MD2_PAPER_ACCOUNTS (Trader's OK required before enabling on the accounts Lazarus shares). Never live."""
import os, json, time, urllib.request, urllib.parse, urllib.error
from . import secrets, netguard
PAPER = "https://paper-api.alpaca.markets"

class BrokerError(Exception): pass

class ShadowBroker:
    mode = "shadow"
    def __init__(self, fail_rate=0.0, rng=None): self.fail_rate, self.rng, self.calls = fail_rate, rng, 0
    def submit(self, cid, symbol, side, qty, mark, fee_bps=0.0):
        self.calls += 1
        if self.rng is not None and self.rng.random() < self.fail_rate: raise BrokerError("injected broker error")
        if not mark or mark <= 0: return dict(status="rejected", reason="no mark")
        return dict(status="filled", price=float(mark), qty=float(qty), fee=abs(float(qty) * float(mark)) * fee_bps / 1e4, cid=cid)
    def lookup(self, cid): return None   # shadow has no remote state: a pending shadow order is re-submitted deterministically

class AlpacaReadOnly:
    def __init__(self, account="TEST_MWJW"): self.account = account; self.calls = 0
    def _get(self, path):
        self.calls += 1
        rq = urllib.request.Request(PAPER + path, headers={**secrets.headers(self.account), "User-Agent": "md2"})
        return json.loads(netguard.urlopen_read(rq, timeout=20, total=35))
    def account_info(self): return self._get("/v2/account")
    def positions(self): return self._get("/v2/positions")
    def orders(self, status="open", limit=500): return self._get(f"/v2/orders?status={status}&limit={limit}&direction=desc")
    def order_by_cid(self, cid):
        try: return self._get("/v2/orders:by_client_order_id?" + urllib.parse.urlencode(dict(client_order_id=cid)))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            raise

class AlpacaPaperBroker(AlpacaReadOnly):
    mode = "paper"
    def __init__(self, account):
        allowed = {a.strip() for a in os.environ.get("MD2_PAPER_ACCOUNTS", "").split(",") if a.strip()}
        if os.environ.get("MD2_ORDER_MODE") != "paper" or account not in allowed:
            raise BrokerError("paper orders disabled (set MD2_ORDER_MODE=paper and MD2_PAPER_ACCOUNTS; needs Trader's OK on shared accounts)")
        super().__init__(account)
    def lookup(self, cid):
        """E14: read-back by client id, normalized (status + unsigned filled qty + avg price); None = never landed."""
        try: o = self.order_by_cid(cid)
        except Exception as e: raise BrokerError(f"lookup {type(e).__name__}")
        return normalize(o, cid) if o else None
    def submit(self, cid, symbol, side, qty, mark, fee_bps=0.0, limit=None):
        assert cid.startswith("md2-"), "md2 only submits md2-* client order ids"
        q = abs(float(qty)); q = int(q) if q == int(q) else round(q, 9)   # E13: side carries the sign; Alpaca rejects negative qty
        body = dict(symbol=symbol, side=side, qty=str(q), type="limit" if limit else "market", time_in_force="day", client_order_id=cid)
        if limit: body["limit_price"] = tick(limit, side)
        data = json.dumps(body).encode(); hdr = {**secrets.headers(self.account), "Content-Type": "application/json"}
        for i in range(3):   # E17 (L-39): 429/5xx retried with short backoff in-pass (same cid -> never a double order)
            self.calls += 1
            try: o = json.loads(urllib.request.urlopen(urllib.request.Request(PAPER + "/v2/orders", data=data, method="POST", headers=hdr), timeout=10).read()); break
            except urllib.error.HTTPError as e:
                eb = e.read()
                if e.code == 422 and b"client_order_id" in eb: o = self.order_by_cid(cid); break   # duplicate cid = already submitted
                if e.code in (429, 500, 502, 503, 504) and i < 2: time.sleep(0.5 * (i + 1)); continue
                if e.code in (403, 422): return dict(status="rejected", reason=f"HTTP {e.code}", cid=cid)   # refusal -> void -> new attempt id
                raise BrokerError(f"HTTP {e.code}")
            except (urllib.error.URLError, TimeoutError) as e:   # may have landed (L-52): stays pending; recover() looks it up by cid
                raise BrokerError(f"transport {type(e).__name__}")
        return normalize(o, cid)

def tick(px, side):
    """E17 (L-28/L-39): Alpaca tick (>= $1: 2 dp, < $1: 4 dp), rounded away from crossing (buy down, sell up)."""
    import math
    d = 100 if px >= 1 else 10000
    v = math.floor(px * d + 1e-9) / d if side == "buy" else math.ceil(px * d - 1e-9) / d
    return f"{v:.2f}" if d == 100 else f"{v:.4f}"

def normalize(o, cid):
    st = (o or {}).get("status") or "unknown"
    fa = float(o.get("filled_qty") or 0); px = float(o.get("filled_avg_price") or 0) or None
    if st == "filled": return dict(status="filled", filled_abs=fa, price=px, fee=0.0, cid=cid)
    if st in ("canceled", "expired", "rejected"):
        return dict(status=st, filled_abs=fa, price=px, fee=0.0, cid=cid, reason=st) if fa else dict(status=st, reason=st, cid=cid)
    return dict(status=st, cid=cid)   # working: new/accepted/partially_filled/done_for_day/...
