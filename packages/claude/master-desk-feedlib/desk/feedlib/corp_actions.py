"""Corporate actions on the desk's equity books: the split and dividend events of every held stock (Yahoo chart
events), collected by the corp_actions job into <root>/cache/corp_actions.json and applied once per position by the
engine (Engine._corp_actions). Alpaca's paper account applies neither (its staff, 2026-07-15), and a virtual book that
ignored them would mark a split stock at a multiple of its true value and miss every dividend.

    collect(yahoo, symbols, now, days=14) -> {SYM: {"splits": [{"ex", "num", "den"}], "dividends": [{"ex", "amount"}]}}
    ex = the event's ex-date (ET session date)."""
import json
import os
from datetime import datetime

from ..util import ET

LOOKBACK_DAYS = 14


def collect(yahoo, symbols, now, days=LOOKBACK_DAYS):
    out = {}
    for s in sorted(set(symbols)):
        try:
            ev = yahoo.events(s, now - days * 86400, now)
        except Exception:
            continue
        rows = {k: [dict(e, ex=datetime.fromtimestamp(e["t"], tz=ET).date().isoformat()) for e in ev.get(k) or []]
                for k in ("splits", "dividends")}
        if rows["splits"] or rows["dividends"]:
            out[s] = rows
    return out


def path(root):
    return os.path.join(root, "cache", "corp_actions.json")


def write(root, events, now):
    p = path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w") as f:
        json.dump({"at": now, "events": events}, f)
    os.replace(p + ".tmp", p)


def load(root):
    try:
        with open(path(root)) as f:
            return (json.load(f) or {}).get("events") or {}
    except (OSError, ValueError):
        return {}


PRICE_RULES = ("stop", "target", "stop_dist")


def split_meta(meta, r):
    """a position's price levels after a num:den split (r = num / den): the sleeve's stop / target and the engine's
    price-level exit rules divide by r, as do position_meta fields priced in the stock (*_px, *_price)."""
    m = dict(meta or {})
    for k in ("stop", "target"):
        if isinstance(m.get(k), (int, float)):
            m[k] = m[k] / r
    if m.get("exit_rules"):
        m["exit_rules"] = [[kind, (val / r if kind in PRICE_RULES else val)] for kind, val in m["exit_rules"]]
    pm = dict(m.get("position_meta") or {})
    for k, v in list(pm.items()):
        if isinstance(v, (int, float)) and not isinstance(v, bool) and (k.endswith("_px") or k.endswith("_price")
                                                                        or k in ("stop", "target")):
            pm[k] = v / r
    if pm:
        m["position_meta"] = pm
    return m
