"""Canonical broker symbol dialect (FILL-CAPTURE / DOOR-PREFLIGHT
cure, 2026-10-30; research RESEARCH-R1 B6 items 422-2 and 422-3).

ONE translator for the door defence and for the aster_crypto
emission family (ADAUSDT, ENJUSDT), so no second source of truth
can drift there. aster_batch1 keeps its own narrower emission
function for the dashed form only (BTC-USD to BTC/USD): its
USDT-named families are pinned by their blockers to emit the
archive symbol (test_aster_batch1_blockers asserts LINKUSDT at
emission), and those symbols are translated HERE at the door,
which is the single place every intent passes. The broker dialect
is BASE/USD for crypto pairs; desk-internal and foreign dialects
(Coinbase BASE-USD, Binance BASEUSDT, bare BASEUSD) are not Alpaca
assets and 422 at the broker as asset-not-found (bodies captured
live 2026-10-27 and 2026-10-29).

Equities, OCC option symbols and already-broker-dialect symbols pass
through untouched.
"""
from __future__ import annotations

CRYPTO_BASES = ("BTC", "ETH", "SOL", "ADA", "LINK", "DOGE", "XRP",
                "LTC", "AVAX", "DOT", "ENJ", "UNI", "AAVE", "MATIC",
                "ATOM", "NEAR")


def normalize_broker_symbol(sym):
    """Translate a desk/foreign-dialect symbol to the broker dialect.

    - "BTC/USD" (already broker dialect) passes through.
    - "BTC-USD" (Coinbase style, any base) becomes "BTC/USD"
      (the aster_batch1 precedent, BROKER-422-ASTER-CRYPTO-20261027:
      a dashed USD pair is a crypto pair in this desk's models, see
      desk3/models.COINBASE_PRODUCT_RE).
    - "ADAUSDT" / "ADAUSD" for a known crypto base become "ADA/USD"
      (the blocked-exit door precedent, BLOCKED-EXIT-20261029).
    - Everything else passes through untouched.
    """
    if not isinstance(sym, str) or "/" in sym:
        return sym
    if sym.endswith("-USD") and len(sym) > 4:
        return sym[:-4] + "/USD"
    for suf in ("USDT", "USD"):
        if sym.endswith(suf) and sym[:-len(suf)] in CRYPTO_BASES:
            return sym[:-len(suf)] + "/USD"
    return sym


def is_crypto_symbol(sym):
    """True when the (normalized) symbol is a BASE/USD crypto pair
    with a known base. Crypto carries its own wire rules: TIF must
    be gtc or ioc (day 422s, captured live 2026-10-27)."""
    if not isinstance(sym, str) or "/" not in sym:
        return False
    base, _, quote = sym.partition("/")
    return quote == "USD" and base in CRYPTO_BASES


def broker_time_in_force(sym, tif):
    """The TIF the broker accepts for this symbol: crypto rejects
    "day" outright, so a day intent on a crypto pair rides as gtc
    (the session-less equivalent); every other combination passes
    through untouched."""
    if is_crypto_symbol(sym) and (tif or "day") == "day":
        return "gtc"
    return tif
