"""Delivery time revalidation for cached decision cards and for the
snapshot's quote maps (DEEP-PASS 3.1 item 1, adopted as is from the
new-head Trade Brain delivery revalidation, Section 2.3 point 9).

The failure this closes: a cache with a 30 second (or, on this desk,
up to an hour long) life can serve a decision computed against a
quote that died seconds after computation. The cure is applied at
DELIVERY, not at computation: whatever is about to be handed to a
consumer is rechecked against the live clock first.

revalidate_card(card, now, session_open, cache, cache_key) carries
the full card semantics for a scan or decision card shaped
{status, quote: {market_at}, setups: [...], options: {status,
setup: {quote_at}}}:

- session closed since computation: the delivered card is rewritten
  to market_closed with every setup stripped.
- the underlying quote aged past 90 seconds at delivery, is future
  dated beyond 5 seconds, or carries no readable stamp (freshness
  unprovable fails closed): the delivery is stale, setups are
  stripped, and the cache entry is DELETED when a cache and key are
  supplied, forcing recomputation instead of a re-serve.
- an option setup whose own quote died is dropped individually: the
  options block is downgraded to stale and the scan status is
  recomputed from what survives (an equity setup still standing
  keeps the card's status; nothing standing makes the card stale).

revalidate_quote_map(data, now) applies the age half of the same
rule at the desk's producer to snapshot delivery seam (wired in
Desk.run_cycle): each quote in the snapshot's quotes and
options_quotes maps is judged on the freshest honest stamp it
carries, received_at first (the moment the quote entered this
desk's serving layer; the live producers stamp it, and the desk's
stock feed is delayed_sip by account tier, so market_at is the
quote's own delayed timestamp by design, FEED-WIRE-20261025), else
the quote's own market stamp (market_at, at, t) for producers that
stamp only the quote itself. A quote whose stamp is more than 90
seconds before delivery, future dated beyond 5 seconds, or missing
entirely (freshness unprovable fails closed) is dropped from the
delivered map and named in the returned report; the session half
is not applied at this seam because the desk snapshot is an
intraday and after hours data vehicle whose consumers gate their
own windows, whereas a decision card is an action surface and
gets both halves through revalidate_card.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone

QUOTE_MAX_AGE_S = 90.0
QUOTE_MAX_FUTURE_S = 5.0


def parse_ts(value):
    """ISO timestamp -> aware datetime, or None when unreadable."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def quote_age_s(stamp, now):
    """Seconds from the stamp to now (negative when future dated),
    or None when the stamp is unreadable."""
    dt = parse_ts(stamp)
    if dt is None:
        return None
    return (now - dt).total_seconds()


def _is_stale(age):
    return (age is None or age > QUOTE_MAX_AGE_S
            or age < -QUOTE_MAX_FUTURE_S)


def _underlying_stamp(card):
    if card.get("quote_at") is not None:
        return card.get("quote_at")
    quote = card.get("quote")
    if isinstance(quote, dict):
        for key in ("market_at", "t", "at"):
            if quote.get(key) is not None:
                return quote.get(key)
    return None


def _option_setup_slot(card):
    """(container, key) locating the option setup dict, or None."""
    options = card.get("options")
    if isinstance(options, dict) and isinstance(options.get("setup"), dict):
        return options, "setup"
    if isinstance(card.get("option_setup"), dict):
        return card, "option_setup"
    return None


def _option_stamp(setup):
    for key in ("quote_at", "quote_market_at", "market_at"):
        if setup.get(key) is not None:
            return setup.get(key)
    quote = setup.get("quote")
    if isinstance(quote, dict):
        for key in ("market_at", "t", "at"):
            if quote.get(key) is not None:
                return quote.get(key)
    return None


def _strip_option_setup(card, options_status):
    slot = _option_setup_slot(card)
    if slot is not None:
        container, key = slot
        container[key] = None
    options = card.get("options")
    if isinstance(options, dict):
        options["status"] = options_status


def revalidate_card(card, now, session_open, cache=None, cache_key=None):
    """Recheck a cached decision card against the live clock at
    delivery. Returns (delivered_card, verdict) with verdict one of
    fresh, market_closed, stale, option_setup_dropped. The input
    card is never mutated; the delivered card is a copy."""
    delivered = copy.deepcopy(card)
    if not session_open:
        delivered["status"] = "market_closed"
        delivered["setups"] = []
        _strip_option_setup(delivered, "market_closed")
        return delivered, "market_closed"
    if _is_stale(quote_age_s(_underlying_stamp(delivered), now)):
        delivered["status"] = "stale"
        delivered["setups"] = []
        _strip_option_setup(delivered, "stale")
        if cache is not None and cache_key is not None:
            cache.pop(cache_key, None)  # force recomputation
        return delivered, "stale"
    slot = _option_setup_slot(delivered)
    if slot is not None:
        container, key = slot
        if _is_stale(quote_age_s(_option_stamp(container[key]), now)):
            _strip_option_setup(delivered, "stale")
            if not delivered.get("setups"):
                delivered["status"] = "stale"
            return delivered, "option_setup_dropped"
    return delivered, "fresh"


def revalidate_quote_map(data, now):
    """Delivery revalidation for one producer output dict at the
    snapshot seam. Returns (delivered_data, report) where report is
    {map_key: {symbol: reason}} naming every dropped quote; the
    input dict is not mutated."""
    out = dict(data)
    report = {}
    for key in ("quotes", "options_quotes"):
        mapping = out.get(key)
        if not isinstance(mapping, dict):
            continue
        kept, dropped = {}, {}
        for sym, quote in mapping.items():
            stamp = None
            if isinstance(quote, dict):
                for stamp_key in ("received_at", "market_at", "at", "t"):
                    if quote.get(stamp_key) is not None:
                        stamp = quote.get(stamp_key)
                        break
            age = quote_age_s(stamp, now)
            if age is None:
                dropped[sym] = "quote_stamp_missing_or_unreadable"
            elif age > QUOTE_MAX_AGE_S:
                dropped[sym] = "stale"
            elif age < -QUOTE_MAX_FUTURE_S:
                dropped[sym] = "future_dated"
            else:
                kept[sym] = quote
        if dropped:
            out[key] = kept
            report[key] = dropped
    return out, report
