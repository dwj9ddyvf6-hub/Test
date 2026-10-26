"""The Echo Analysis sidecar — line-by-line ports of galath-desk @652db7af src/lib/echo/{classify,gate}.ts and
scripts/echo-sidecar.mjs's feed reader (stripHtml / parseRss). JavaScript's regular expressions are ASCII-word
(\\b, \\w) with Unicode whitespace (\\s, trim); the ports spell those classes out so the reads match the source
character for character. Parity: tools/parity/galath_echo.py."""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

JS_WS = "\t\n\v\f\r                " \
        "  　﻿"
S = "[" + JS_WS + "]"
A = re.ASCII


def js_trim(s):
    return s.strip(JS_WS)


def _rx(p, flags=0):
    return re.compile(p.replace(r"\s", S), flags | A)


# == classify.ts =======================================================================================================
NOISE = {"I", "A", "THE", "AND", "FOR", "TO", "ON", "AT", "OF", "IN", "IS", "IT", "OR", "MY", "DMA", "WMA", "EMA", "ATR",
         "RSI", "MACD", "FIB", "NFA", "IMO", "CEO", "ETF", "IPO", "WAVE", "PLAN", "PRICE", "SUPPORT", "RESISTANCE",
         "TARGET", "LONG", "TERM", "HEAVY"}
TICK = _rx(r"\$([A-Z]{1,5})\b")
BARE = _rx(r"\bI bought ([A-Z]{1,5})\b", re.I)
NAMED = _rx(r"\bi bought\s+\$?([A-Z]{1,5})\b", re.I)
RECAP = _rx(r"another great week|last \d+ weeks|going into next week|every buy posted|up over \d+%|current market "
            r"thoughts")
HIST = _rx(r"\bon (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|\bthis week\b|\blast week\b|"
           r"\byesterday\b|\blast \d+ weeks\b")
REPOST = _rx(r"^rt by ", re.I)
NEVER = _rx(r"\bi never bought\b|\bdidn't buy\b|\bdid not buy\b|\bhasn't gone to plan\b")
FUTURE = _rx(r"\bi will buy\b|\bi'll buy\b|\bwhere i will buy\b|\bplan to (buy|add)\b|\bi plan to very soon\b|"
             r"\bi'll consider buying\b|\bnear a buy\b|\bbefore buying\b|\bwhere i('ll| will) add\b|"
             r"\bi plan to increase\b|\bi plan to buy")
PATIENCE = _rx(r"\bdon'?t rush\b|\bstaying patient\b")
BOUGHT = _rx(r"\bi bought\b|\bwe bought\b|\bpublicly bought\b")
STARTER = _rx(r"\bstarter position\b|\bstarter here\b")
ADDED = _rx(r"\bi added\b|\bi('ve| have) added\b")
ADDING = _rx(r"\bi('m| am) adding\b|\badding to my position\b")
HOLDING = _rx(r"\bhappy holding\b|\bi('m| am) holding\b|\bno concerns\b")
SETUP = _rx(r"\bbuying opportunity\b|\bbuy zone\b|\bi('m| am) near a buy\b")
WS_RUN = re.compile(S + "+")


def _js_lower(s):
    return s.lower()


def _tickers(text):
    out = []
    for m in TICK.finditer(text):
        if m.group(1) not in out:
            out.append(m.group(1))
    if not out:
        bare = BARE.search(text)
        if bare:
            out.append(bare.group(1).upper())
    return [s for s in out if s not in NOISE]


def _named_buys(text):
    out = []
    for m in NAMED.finditer(text):
        s = m.group(1).upper()
        if s not in NOISE and s not in out:
            out.append(s)
    return out


def _is_recap(low, symbols):
    return len(symbols) >= 6 or bool(RECAP.search(low))


def classify_echo(text):
    raw = js_trim(WS_RUN.sub(" ", str(text if text is not None else "")))
    symbols = _tickers(raw)
    low = _js_lower(raw)

    def call(kind, syms, filled, reason, paper):
        return {"kind": kind, "symbols": syms, "filled": filled, "reason": reason, "paper": paper, "telegram": False}
    if not raw or REPOST.search(raw):
        return call("SKIP", symbols, False, "repost", False)
    if _is_recap(low, symbols):
        return call("WATCH", symbols, False, "weekly wrap — not a live buy", False)
    if NEVER.search(low):
        return call("SKIP", symbols, False, "he did not buy", False)
    future = bool(FUTURE.search(low))
    patience = bool(PATIENCE.search(low))
    bought = bool(BOUGHT.search(low))
    starter = bool(STARTER.search(low))
    added = bool(ADDED.search(low))
    adding = bool(ADDING.search(low))
    holding = bool(HOLDING.search(low))
    if bought or starter:
        live = _named_buys(raw)
        names = live if live else symbols[:2]
        if HIST.search(low):
            return call("WATCH", names, False, "old fill — not today", False)
        return call("BUY", names, True, "he bought" if bought else "starter position", len(names) > 0)
    if added or adding:
        return call("ADD", symbols[:2], added, "he added" if added else "adding to a position",
                    added and len(symbols) > 0)
    if holding:
        return call("HOLD", symbols, False, "holding", False)
    if future or patience:
        return call("WATCH", symbols, False, "plan / wait — not a fill", False)
    if symbols and SETUP.search(low):
        return call("WATCH", symbols, False, "setup, not filled", False)
    if symbols:
        return call("WATCH", symbols, False, "ticker note", False)
    return call("SKIP", symbols, False, "no ticker", False)


# == gate.ts ===========================================================================================================
def echo_session_open(weekday, hour, minute):
    if not weekday:
        return False
    hm = hour * 60 + minute
    return 4 * 60 <= hm <= 15 * 60 + 45


def _num0(v):
    """Number(v || 0)."""
    try:
        x = float(v) if v else 0.0
    except (TypeError, ValueError):
        return float("nan")
    return x


def at_support(price, entry=None, vs21=None, ret5=None):
    px = _num0(price)
    e = _num0(entry)
    if e > 0 and px > 0 and px <= e * 1.01:
        return True
    if vs21 is not None and -0.05 <= vs21 <= 0.02:
        return True
    if ret5 is not None and ret5 <= 0:
        return True
    return False


def is_echo_chase(vs21=None, ret5=None):
    if ret5 is not None and ret5 > 0.08:
        return True
    if vs21 is not None and vs21 > 0.04:
        return True
    return False


def echo_paper_gate(weekday, hour, minute, kind, boughtToday, hasPosition, price, entry=None, vs21=None, ret5=None):
    if not weekday:
        return {"ok": False, "reason": "weekend — no Echo paper"}
    if not echo_session_open(True, hour, minute):
        return {"ok": False, "reason": "Echo paper only 4:00–15:45 ET weekdays"}
    if kind == "ADD":
        if not at_support(price, entry, vs21, ret5):
            return {"ok": False, "reason": "add is not a support retest"}
        return {"ok": True, "reason": "Echo re-add at support"}
    if boughtToday or hasPosition:
        return {"ok": False, "reason": "not his first buy today"}
    if is_echo_chase(vs21, ret5):
        return {"ok": False, "reason": "Echo chase — already ran"}
    return {"ok": True, "reason": "Echo first buy today"}


# == echo-sidecar.mjs stripHtml / parseRss =============================================================================
HANDLE = "EchoAnalysis"
FEEDS = ("https://nitter.net/EchoAnalysis/rss", "https://nitter.privacydev.net/EchoAnalysis/rss",
         "https://nitter.cz/EchoAnalysis/rss")
_CDATA = re.compile(r"<!\[CDATA\[|\]\]>")
_BR = re.compile(r"<br" + S + r"*/?>", re.I | A)
_TAG = re.compile(r"<[^>]+>")


def strip_html(html):
    s = str(html or "")
    s = _CDATA.sub(" ", s)
    s = _BR.sub("\n", s)
    s = _TAG.sub(" ", s)
    s = s.replace("&", "&").replace("<", "<").replace(">", ">")    # the source's replaces are identities
    s = WS_RUN.sub(" ", s)
    return js_trim(s)


def _first(rx, chunk):
    m = rx.search(chunk)
    return m.group(1) if m else ""


_ITEM = re.compile(r"<item>", re.I)
_TITLE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
_CREATOR = re.compile(r"<dc:creator>([\s\S]*?)</dc:creator>", re.I)
_GUID = re.compile(r"<guid[^>]*>([\s\S]*?)</guid>", re.I)
_LINK = re.compile(r"<link>([\s\S]*?)</link>", re.I)
_PUB = re.compile(r"<pubDate>([\s\S]*?)</pubDate>", re.I)
_DESC = re.compile(r"<description>([\s\S]*?)</description>", re.I)
_RT = re.compile(r"^RT by ", re.I)
_M_END = re.compile(r"#m$")


def _iso_ms(ms):
    d = datetime.fromtimestamp(ms // 1000, tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (ms % 1000)


def _parse_pub(pub):
    """new Date(pub) for an RFC-822 pubDate (the RSS format); None when unparseable."""
    try:
        d = parsedate_to_datetime(pub)
    except (TypeError, ValueError, IndexError):
        return None
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return int(round(d.timestamp() * 1000))


def parse_rss(xml, now_ms):
    items = []
    for chunk in _ITEM.split(str(xml))[1:]:
        title = strip_html(_first(_TITLE, chunk))
        if _RT.search(title):
            continue
        creator = _first(_CREATOR, chunk).replace("@", "")
        if creator and creator.lower() != HANDLE.lower():
            continue
        gid = js_trim(_first(_GUID, chunk))
        link = js_trim(_first(_LINK, chunk))
        pub = js_trim(_first(_PUB, chunk))
        desc = strip_html(_first(_DESC, chunk))
        text = desc or title
        if not gid or not text:
            continue
        at_ms = _parse_pub(pub) if pub else now_ms
        if at_ms is None:
            raise ValueError("Invalid time value")              # new Date(pub).toISOString() throws: the sweep fails
        url = _M_END.sub("", link.replace("nitter.net", "x.com", 1)) if "status" in link else \
            f"https://x.com/{HANDLE}/status/{gid}"
        items.append({"id": gid, "at": _iso_ms(at_ms), "url": url, "text": text, "title": title})
    return items
