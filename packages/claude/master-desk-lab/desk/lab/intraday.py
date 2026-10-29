"""The roster's intraday bars the lab reads besides the hub's cache: the canonical 1H store (EQ-06).

The hub's equity_split 1h cache holds the basket names only (about 41 on the host), so before EQ-06 most 1h rows
(v615, census, genome 1h, lz_1h, ausar_h1state) found no hourly bars for their session and were priced at the next
session's open without saying so (lab vs_nbo +66.96 bps for v615 against +8.7 bps measured on the next 1H bar). The
roster's hours are cached, though: the tensor_research_1h job keeps every roster name's canonical series.

  <cache>/canonical/1h_alpaca/<SYM>.json   desk/feedlib/canonical_alpaca.py (the host, with Alpaca keys): SIP 30-minute
                                           bars ("halves") on the open-anchored grid, a Yahoo seed ("hours") before
                                           its cut; the hours served are exactly AlpacaCanonical.bars'
  <cache>/canonical/1h/<SYM>.json          desk/feedlib/canonical.py (no keys): the Yahoo canonical 60m series

canonical(root, sym, until) -> {"1h": hours, "30m": half hours, "src"} or None. Point in time: only bars the store
could have served at `until` (the Alpaca store's hours and half hours ended DELAY_S before it; the Yahoo series' hours
ended by it). Read-only and cache-only: a file is read, never fetched, refreshed or written."""
import json
import os

from .. import calendar as cal
from ..feedlib.canonical import completed, session_opens
from ..feedlib.canonical_alpaca import DELAY_S

_DAYS = {}                   # day number -> (canonical opens, close) of the ET day, None when it is no trading day


def _day(t):
    """the canonical opens and the close of the ET day whose window holds t (from 06:00 UTC: no US equity bar prints
    in that hour in either season; the date read at the window's 12:00 UTC), asked once per day"""
    k = int((float(t) - 21600.0) // 86400.0)
    if k not in _DAYS:
        d = cal._as_date(k * 86400.0 + 43200.0)
        opens = session_opens(d)
        _DAYS[k] = (opens, cal.session_close(d)) if opens else None
    return _DAYS[k]


def aggregate(halves):
    """desk/feedlib/canonical_alpaca.py aggregate()'s hours, the calendar asked once per day instead of once per half
    hour (the lab reads a year of half hours for ~1,000 names a night): each regular-session half hour joins the latest
    canonical open at or before it (09:30 ... 15:30; on an early close the 13:00 stub); open of the first, high / low
    over all, close of the last, volumes summed. tests/test_lab_eq06.py pins it to AlpacaCanonical.bars"""
    hours = {}
    for b in sorted(halves, key=lambda x: x["t"]):
        day = _day(b["t"])
        if day is None:
            continue
        opens, close = day
        t = b["t"]
        if not (opens[0] <= t < close):
            continue
        k = max(o for o in opens if o <= t)
        h = hours.get(k)
        if h is None:
            hours[k] = {"t": int(k), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
        else:
            h["h"], h["l"], h["c"], h["v"] = max(h["h"], b["h"]), min(h["l"], b["l"]), b["c"], h["v"] + b["v"]
    return [hours[k] for k in sorted(hours)]


def _file(d, sym):
    return os.path.join(d, sym.upper().replace("/", "_").replace(".", "_").replace("^", "") + ".json")


def _doc(path):
    try:
        with open(path) as f:
            doc = json.load(f)
        return doc if isinstance(doc, dict) else None
    except (OSError, ValueError):
        return None


def canonical(root, sym, until, since=None):
    """the symbol's canonical hours (and the Alpaca store's half hours) at `until`, or None when neither store holds
    any; since: drop the bars starting before it (the lab needs its open sessions and a warm-up, not the store's year)"""
    if not root:
        return None
    doc = _doc(_file(os.path.join(root, "canonical", "1h_alpaca"), sym))
    if doc and (doc.get("hours") or doc.get("halves")):
        hours, halves = doc.get("hours") or [], doc.get("halves") or []
        if since is not None:
            hours = [b for b in hours if float(b["t"]) >= since]
            halves = [b for b in halves if float(b["t"]) >= since]
        out = aggregate(halves)                     # AlpacaCanonical.bars: the seed's hours, then the halves' hours
        if hours:
            cut = doc.get("cut") or hours[-1]["t"] + 1
            out = hours + [h for h in out if h["t"] >= cut]
        cut_t = float(until) - DELAY_S
        return {"1h": completed(out, cut_t), "30m": [b for b in halves if float(b["t"]) + 1800 <= cut_t],
                "src": "canonical_alpaca"}
    doc = _doc(_file(os.path.join(root, "canonical", "1h"), sym))
    if doc and doc.get("bars"):
        bars = doc["bars"] if since is None else [b for b in doc["bars"] if float(b["t"]) >= since]
        return {"1h": completed(bars, float(until)), "30m": [], "src": "canonical_yahoo"}
    return None
