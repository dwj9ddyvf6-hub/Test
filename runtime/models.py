from __future__ import annotations
import re
from dataclasses import dataclass, asdict

@dataclass
class Bar:
    t: str; o: float; h: float; l: float; c: float; v: float = 0.0
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(t=str(d["t"]), o=float(d["o"]), h=float(d["h"]), l=float(d["l"]), c=float(d["c"]), v=float(d.get("v",0.0)))

class IntentError(ValueError): pass

OCC_RE = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
def is_option_symbol(sym: str) -> bool: return bool(OCC_RE.match(sym or ""))
# D4 extension (2026-10-24, wire-coinbase): Coinbase Exchange products are
# hyphenated BASE-USD (e.g. "BTC-USD") and settle fractionally by venue
# design, exactly like the "/" crypto pairs D4 already allows. The allowance
# is narrow: only a crypto base quoted in USD/USDC/USDT via a hyphen — an
# equity hyphen ticker (BRK-B, BF-B) does not match and stays whole-unit.
COINBASE_PRODUCT_RE = re.compile(r"^[A-Z0-9]{2,10}-(USD|USDC|USDT)$")
# GAP-CURE: bare concatenated crypto-vs-USD symbols (Alpaca crypto
# convention, e.g. SOLUSD/ADAUSD/LINKUSD) settle fractionally by venue
# design exactly like the "/" pairs above. Narrow base allowlist so no
# equity ticker can match.
BARE_CRYPTO_USD_RE = re.compile(r"^(BTC|ETH|SOL|ADA|LINK|DOGE|XRP|LTC|AVAX|DOT|ENJ|UNI|AAVE|MATIC|ATOM|NEAR)USD$")
def is_fractional_symbol(sym: str) -> bool:
    s = str(sym or "")
    return "/" in s or bool(COINBASE_PRODUCT_RE.match(s)) or bool(BARE_CRYPTO_USD_RE.match(s))

def validate_intent(intent, held_symbols=None):
    """DESIGN §4c shape rules. Raises IntentError on violation."""
    if not isinstance(intent, dict): raise IntentError("intent_not_dict")
    for k in ("intent_id","kind","symbol","side","qty"):
        if k not in intent: raise IntentError(f"missing_{k}")
    if intent["kind"] not in ("entry","exit"): raise IntentError("bad_kind")
    if intent["side"] not in ("buy","sell"): raise IntentError("bad_side")
    qty = intent["qty"]
    if isinstance(qty, bool) or not isinstance(qty,(int,float)) or qty <= 0: raise IntentError("bad_qty")
    # D4 ruling (platform, not strategy): crypto pair symbols ("LINK/USD")
    # trade fractionally by venue design and core Intent.qty expressly
    # carries fractional quantities; equities/options stay whole-unit.
    # Extended 2026-10-24 to Coinbase hyphen products ("BTC-USD") — see
    # is_fractional_symbol above.
    if float(qty) != int(qty) and not is_fractional_symbol(intent.get("symbol")):
        raise IntentError("qty_not_whole")
    otype = intent.get("order_type","market")
    if otype not in ("market","limit"): raise IntentError("bad_order_type")
    if otype == "limit":
        lp = intent.get("limit_price")
        if lp is None or float(lp) <= 0: raise IntentError("limit_price_required_positive")
    sp = intent.get("stop_price")
    if sp is not None and float(sp) <= 0: raise IntentError("stop_price_positive")
    if is_option_symbol(intent["symbol"]):
        if int(qty) != qty: raise IntentError("option_qty_whole")
        if intent["kind"]=="entry" and "position_intent" not in intent and False: pass
    if intent["kind"]=="exit" and held_symbols is not None and intent["symbol"] not in held_symbols:
        raise IntentError("exit_not_held")
    if intent.get("time_in_force","day") not in ("day","gtc"): raise IntentError("bad_tif")
    return True

def client_order_id(sleeve_id: str, intent_id: str) -> str:
    return f"v2-{sleeve_id}-{intent_id}"[:127]
