"""Intent shape rules — v2 semantics carried over (DESIGN §4c of v2)."""
from __future__ import annotations
import re

OCC_RE = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
COINBASE_PRODUCT_RE = re.compile(r"^[A-Z0-9]{2,10}-(USD|USDC|USDT)$")
BARE_CRYPTO_USD_RE = re.compile(
    r"^(BTC|ETH|SOL|ADA|LINK|DOGE|XRP|LTC|AVAX|DOT|ENJ|UNI|AAVE|MATIC|ATOM|NEAR)(USD|USDT)$")


class IntentError(ValueError):
    pass


def is_fractional_symbol(sym: str) -> bool:
    s = str(sym or "")
    return "/" in s or bool(COINBASE_PRODUCT_RE.match(s)) or bool(BARE_CRYPTO_USD_RE.match(s))


def validate_intent(intent):
    if not isinstance(intent, dict):
        raise IntentError("intent_not_dict")
    for k in ("intent_id", "kind", "symbol", "side", "qty"):
        if k not in intent:
            raise IntentError(f"missing_{k}")
    if intent["kind"] not in ("entry", "exit"):
        raise IntentError("bad_kind")
    if intent["side"] not in ("buy", "sell"):
        raise IntentError("bad_side")
    qty = intent["qty"]
    if isinstance(qty, bool) or not isinstance(qty, (int, float)) or qty <= 0:
        raise IntentError("bad_qty")
    if float(qty) != int(qty) and not is_fractional_symbol(intent.get("symbol")):
        # WS4-FRACTIONAL-20261114 (owner ruling 2026-11-14, "It needs
        # to buy stuff of any price"): fractional quantities are
        # lawful for equities — the same dollar budget expressed
        # fractionally instead of rounding to zero whole shares
        # (OBS-1 reconciliation: no forced floor; the budget still
        # decides). Two named exceptions keep their refusal:
        # options contracts are whole BY THE INSTRUMENT (the door
        # serves no fractional contracts), and an equity fractional
        # quantity cannot ride a LIMIT order (the fractional door
        # is market-only) — that class fails closed here by name
        # rather than at the broker. A non-fractionable equity
        # still fails at the broker itself, journaled by name.
        sym = str(intent.get("symbol") or "")
        if OCC_RE.match(sym):
            raise IntentError("qty_not_whole")
        if intent.get("time_in_force", "day") in ("cls", "opg"):
            # OVERNIGHT-AUCTION-20261116 (B0-2, spec section 6.3):
            # a fractional quantity cannot ride an auction tif —
            # the broker's fractional door is day-tif only — so the
            # class fails closed here by name, not at the broker.
            raise IntentError("fractional_qty_auction_order")
        if intent.get("order_type", "market") == "limit":
            raise IntentError("fractional_qty_limit_order")
    otype = intent.get("order_type", "market")
    if otype not in ("market", "limit"):
        raise IntentError("bad_order_type")
    if otype == "limit":
        lp = intent.get("limit_price")
        if lp is None or float(lp) <= 0:
            raise IntentError("limit_price_required_positive")
    sp = intent.get("stop_price")
    if sp is not None and float(sp) <= 0:
        raise IntentError("stop_price_positive")
    tif = intent.get("time_in_force", "day")
    if tif in ("cls", "opg"):
        # OVERNIGHT-AUCTION-20261116 (B0-1, spec section 7): the
        # auction tifs are admitted for EQUITY market intents
        # only, fail-closed by name on every other shape. Options
        # keep (day, gtc) exactly as before; crypto pairs carry
        # their own wire rules; a limit-on-close/open shape is
        # not part of the auction form and stays refused.
        sym = str(intent.get("symbol") or "")
        if OCC_RE.match(sym):
            raise IntentError("auction_tif_on_options")
        from .broker_dialect import is_crypto_symbol
        if "/" in sym or is_crypto_symbol(sym):
            raise IntentError("auction_tif_on_crypto")
        if otype != "market":
            raise IntentError("auction_tif_requires_market")
    elif tif not in ("day", "gtc"):
        raise IntentError("bad_tif")
    return True


def client_order_id_untruncated(sleeve_id: str, intent_id: str) -> str:
    """Idempotency key construction, v3-namespaced (V3-SCOPE §7.4),
    BEFORE the broker's 127-char cap: the length the dispatcher's
    truncation warning judges.

    COID-DEDUPE-20261031 (owner ruling 2026-10-31, option B minimal
    form): every bridge and sleeve mints intent_id as
    "{sleeve_id}-...", so the original f"v3-{sleeve_id}-{intent_id}"
    carried the sleeve segment twice, and the longest constructed
    ids reached Alpaca's 127-char truncation cap exactly on the
    tail (timestamp + counter) where uniqueness between two
    intents from one sleeve lives (census 2026-10-31: 2,833
    distinct ids, 2 at the cap, zero collisions). When the intent
    id already opens with the sleeve segment, that segment IS the
    namespacing segment and is not repeated: the id is
    "v3-{intent_id}". An intent id that does not open with the
    sleeve segment keeps the explicit one:
    "v3-{sleeve_id}-{intent_id}". Either way the sleeve appears
    exactly once and the map stays injective over (sleeve_id,
    intent_id) for every intent the desk mints. Historical ids are
    untouched: they sit in the journal and at the broker as
    written, broker read-back and the pending store key on the
    stored string, and the dispatcher's _seen dedup keys on
    intent_id, so no consumer re-derives an old id."""
    sid = str(sleeve_id or "")
    iid = str(intent_id or "")
    if sid and iid.startswith(sid + "-"):
        return f"v3-{iid}"
    return f"v3-{sid}-{iid}"


def client_order_id(sleeve_id: str, intent_id: str) -> str:
    """The wire form: the constructed id under the broker's cap."""
    return client_order_id_untruncated(sleeve_id, intent_id)[:127]
