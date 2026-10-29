"""Earnings calendar — {SYMBOL: "YYYY-MM-DD" | None}, the old desk's earnings.json shape (desk/earnings.py):
a date = next (expected or estimated) report; None = confirmed no earnings (ETF); ABSENT = unknown.

Producer: Nasdaq's public analyst earnings-date endpoint, one symbol per request, sent with the desk's own
User-Agent (HEADERS: no browser string, no email, the owner's rule against impersonation), refreshed per symbol at
most once a day (the old desk refreshed weekly, Sunday) and cached on disk. ETFs are
recognised by Nasdaq's ETF quote page. `fresh(symbols)` mirrors the old 8-day staleness rule."""
import json
import os
import re
import time
from datetime import datetime

from ..data.http import get
from .edgar_buyback import DEFAULT_USER_AGENT

# The desk's Nasdaq request headers, which every desk caller of api.nasdaq.com sends: its own name, never a browser's
# string or an Origin / Referer claiming nasdaq.com, never an email (the owner's rule). Nasdaq answered them with
# HTTP 200 on 2026-10-26 (earnings-date, ETF info, earnings calendar, watchlist, historical). A refusal leaves each
# symbol its last good row with the error noted (refresh below): the browser string is not to come back.
HEADERS = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json, text/plain, */*"}
KNOWN_ETFS = {"QQQ", "SPY", "IWM", "DIA", "SOXL", "TQQQ", "SQQQ", "GLD", "BIL", "VXX", "UVXY", "SMH", "XLK", "XLF",
              "XLE", "XLV", "TLT", "IEF", "SHY", "QLD", "SSO", "UPRO", "SPXL", "TECL", "USD", "ROM", "XSP"}
REFRESH_S = 86400
STALE_DAYS = 8


def _parse(doc):
    d = (doc or {}).get("data") or {}
    txt = d.get("reportText") or ""
    m = re.search(r"on\s+(\d{2})/(\d{2})/(\d{4})", txt)
    if m:
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    ann = d.get("announcement") or ""
    m = re.search(r":\s*([A-Z][a-z]{2} \d{1,2}, \d{4})", ann)
    if m:
        return datetime.strptime(m.group(1), "%b %d, %Y").date().isoformat()
    return None


class Earnings:
    def __init__(self, path, clock=time.time, fetch=get, max_per_call=30):
        self.path = path
        self.clock = clock
        self.fetch = fetch
        self.max_per_call = max_per_call
        self.rows = {}
        if os.path.exists(path):
            try:
                self.rows = json.load(open(path))
            except ValueError:
                self.rows = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.rows, f, sort_keys=True)
        os.replace(tmp, self.path)

    def _lookup(self, sym):
        now = self.clock()
        if sym.upper() in KNOWN_ETFS:
            return {"date": None, "status": "etf", "at": now}
        doc = self.fetch(f"https://api.nasdaq.com/api/analyst/{sym}/earnings-date", timeout=20, tries=2, headers=HEADERS)
        date = _parse(doc)
        if date:
            return {"date": date, "status": "dated", "at": now}
        code = (((doc or {}).get("status") or {}).get("rCode"))
        if code == 400:
            q = self.fetch(f"https://api.nasdaq.com/api/quote/{sym}/info", {"assetclass": "etf"}, timeout=20, tries=2,
                           headers=HEADERS)
            if ((q or {}).get("data") or {}).get("symbol"):
                return {"date": None, "status": "etf", "at": now}
        return {"date": None, "status": "unknown", "at": now}

    def refresh(self, symbols):
        now = self.clock()
        due = [s for s in symbols if now - float((self.rows.get(s) or {}).get("at") or 0) >= REFRESH_S]
        changed = False
        for s in due[: self.max_per_call]:
            try:
                self.rows[s] = self._lookup(s)
            except Exception as e:                     # keep the last good row; note the failure
                r = dict(self.rows.get(s) or {})
                r["error"] = f"{type(e).__name__}: {str(e)[:120]}"
                r.setdefault("status", "unknown")
                r.setdefault("at", 0)
                self.rows[s] = r
            changed = True
        if changed:
            self._save()

    def calendar(self, symbols):
        """{sym: date|None} for symbols with a known status (dated or ETF); unknown symbols are absent."""
        self.refresh(symbols)
        out = {}
        for s in symbols:
            r = self.rows.get(s) or {}
            if r.get("status") == "dated":
                out[s] = r["date"]
            elif r.get("status") == "etf":
                out[s] = None
        return out

    def fresh(self, symbols):
        now = self.clock()
        return bool(symbols) and all(now - float((self.rows.get(s) or {}).get("at") or 0) <= STALE_DAYS * 86400
                                     for s in symbols)
