"""Inputs of the Griffith legacy intraday agent (agentic_runtime: broad_scan / ResearchEngine / SetupAgents) and of
the auditable trend agent (app.TrendAgent), served the way the source fetched them:

  snapshots   Alpaca /v2/stocks/snapshots, feed=iex (dailyBar, prevDailyBar, minuteBar, latestQuote, latestTrade);
  news        Alpaca /v1beta1/news (symbols, limit, sort desc, no content) — the headlines the ResearchEngine scores;
  bars        Alpaca /v2/stocks/bars, feed=iex, adjustment=raw, sort=desc, limit N over the last `days` days (the
              source's app.Alpaca.bars), returned ascending.
With no Alpaca credentials the best free public substitutes are served and labelled (named divergences of the
sleeves): Yahoo quote / daily bars for the snapshot fields (no bid/ask: the spread is unknown), Yahoo Finance RSS
headlines for news, Yahoo intraday bars (extended session) for the bars."""
import time
import xml.etree.ElementTree as ET_XML
from datetime import datetime, timezone

from ..data.http import get
from ..util import parse_ts

DATA = "https://data.alpaca.markets"


def _iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def client(hub):
    a = getattr(hub, "alpaca", None)
    return getattr(a, "c", None) if a is not None else None


def snapshots(hub, symbols):
    """{SYM: Alpaca-shaped snapshot}; source label in the second value."""
    c = client(hub)
    if c is not None:
        out = {}
        syms = list(dict.fromkeys(symbols))
        for i in range(0, len(syms), 100):
            r = c.stock_snapshots(syms[i:i + 100], feed="iex") or {}
            out.update(r.get("snapshots", r))
        return out, "alpaca_iex"
    out = {}
    for s in dict.fromkeys(symbols):
        try:
            q = hub.yahoo.quote(s) or {}
            daily = hub.bars("yahoo", "1d", [s], 3).get(s) or []
        except Exception:
            continue
        prev = daily[-1] if daily else {}
        if not q.get("last"):
            continue
        t = _iso(q.get("t") or time.time())
        out[s] = {"dailyBar": {"o": q.get("day_open"), "h": q.get("day_high"), "l": q.get("day_low"),
                               "c": q.get("last"), "v": q.get("day_volume") or 0, "t": t},
                  "prevDailyBar": {"c": q.get("prev_close") or prev.get("c"), "v": prev.get("v") or 0},
                  "latestTrade": {"p": q.get("last"), "t": t}, "latestQuote": {}}
    return out, "yahoo"


def news(hub, symbols, limit=50):
    c = client(hub)
    if c is not None:
        r = c._get("/v1beta1/news", {"symbols": ",".join(symbols), "limit": limit, "sort": "desc",
                                     "include_content": "false", "exclude_contentless": "true"}, host=DATA) or {}
        return r.get("news", []), "alpaca"
    rows = []
    for s in symbols:
        try:
            xml = get("https://feeds.finance.yahoo.com/rss/2.0/headline", {"s": s, "region": "US", "lang": "en-US"},
                      as_text=True)
            for item in ET_XML.fromstring(xml).iter("item"):
                rows.append({"headline": (item.findtext("title") or "").strip(), "symbols": [s],
                             "created_at": item.findtext("pubDate")})
        except Exception:
            continue
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return rows[:limit], "yahoo_rss"


def bars_desc(hub, symbol, timeframe, limit, days, now=None):
    """the latest `limit` bars (ascending) of the last `days` days, as app.Alpaca.bars returned them."""
    now = now or time.time()
    c = client(hub)
    if c is not None:
        r = c._get("/v2/stocks/bars", {"symbols": symbol, "timeframe": timeframe, "limit": limit, "feed": "iex",
                                       "sort": "desc", "start": _iso(now - days * 86400), "adjustment": "raw"},
                   host=DATA) or {}
        rows = [{"t": parse_ts(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"],
                 "vw": b.get("vw")} for b in (r.get("bars") or {}).get(symbol, [])]
        return sorted(rows, key=lambda b: b["t"])[-limit:], "alpaca_iex"
    iv = {"1Min": "1m", "5Min": "5m", "15Min": "15m"}[timeframe]
    got = hub.bars("yahoo_ext", iv, [symbol], limit).get(symbol) or []
    return got[-limit:], "yahoo"
