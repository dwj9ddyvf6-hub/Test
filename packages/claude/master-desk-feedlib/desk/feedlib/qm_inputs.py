"""Qullamaggie pass-3 inputs from free public sources (desk/sleeves/families/qullamaggie.py).

The research desk (qullamaggie-research-pass3, desk_fixed.py) reads a licensed point-in-time corpus: verified
catalyst events with a public timestamp, a universe file with sector / market cap / borrow flags. None of that is
licensed here, so each input is computed from the best free public source (each one a named divergence of the
family):

  events ..... SEC EDGAR current reports, forms 8-K and 6-K (amendments excluded), from the EDGAR "latest filings"
               Atom feed (www.sec.gov/cgi-bin/browse-edgar?action=getcurrent), newest first, paged by 100 until the
               filings already held; the filing's acceptance time is its public timestamp. A filing belongs to the
               first session whose close is after its acceptance; event_minute = whole minutes from that session's
               09:30 ET (negative before the open); news_verified = True (an SEC-accepted disclosure); event_type =
               the form and its items. Refreshed at most every 60 s, kept 5 days.
  tickers .... CIK -> tickers from SEC company_tickers.json (cached 31 days).
  sector ..... the SEC EDGAR industry office of the filer (data.sec.gov submissions "ownerOrg", its number
               dropped; else "sicDescription"), cached 31 days per CIK.
  shares ..... the latest-filed dei:EntityCommonStockSharesOutstanding (else us-gaap:CommonStockSharesOutstanding)
               from data.sec.gov companyfacts, cached 7 days per CIK (market cap = shares x the last close).
  listing .... the Nasdaq Trader symbol directory (nasdaqlisted.txt + otherlisted.txt): the ETF flag, cached 1 day.

Requests go through the desk's data/http.get (per-host pacing, retries) with the SEC fair-access User-Agent of
desk/feedlib/edgar_buyback.user_agent(). Every reader fails soft: a failed fetch keeps what the cache holds."""
import math
import os
import re
import time
from datetime import datetime
from html import unescape

from .. import calendar as cal
from ..data.http import get
from ..util import read_json, write_json_atomic
from .edgar_buyback import user_agent

FORMS = ("8-K", "6-K")
CURRENT_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
LISTING_URLS = ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
                "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt")
EVENTS_REFRESH_S = 60
EVENTS_KEEP_S = 5 * 86400
MAX_PAGES = 8
TICKERS_TTL_S = 31 * 86400
PROFILE_TTL_S = 31 * 86400
FACTS_TTL_S = 7 * 86400
LISTING_TTL_S = 86400
MAX_LOOKUPS = 25                 # new SEC per-company reads per call (the rest wait for the next pass)


def cache_dir(root):
    d = os.path.join(root, "qullamaggie")
    os.makedirs(d, exist_ok=True)
    return d


_DOCS = {}


def _load(path, default=None):
    """read_json memoised on the file's mtime (the per-pass feeds read these caches every minute)."""
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return default
    hit = _DOCS.get(path)
    if hit and hit[0] == mt:
        return hit[1]
    doc = read_json(path, default)
    _DOCS[path] = (mt, doc)
    return doc


def _save(path, doc):
    try:
        write_json_atomic(path, doc)
        _DOCS[path] = (os.path.getmtime(path), doc)
    except OSError:
        pass


def _sec(fetch, url, params=None, as_text=False):
    return fetch(url, params, as_text=as_text, headers={"User-Agent": user_agent()})


# -- events ----------------------------------------------------------------------------------------------------------
_ENTRY = re.compile(r"<entry>(.*?)</entry>", re.S)
_TITLE = re.compile(r"^\s*(\S+)\s+-\s+(.*?)\s+\((\d{10})\)\s+\(([^)]*)\)\s*$")
_ITEM = re.compile(r"Item\s+(\d+\.\d+):\s*([^\n<]+)")


def _tag(text, name):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (name, name), text, re.S)
    return m.group(1).strip() if m else ""


def parse_current(text):
    """the Atom feed's entries -> [{form, company, cik, role, accepted (epoch s), accession, items}]."""
    out = []
    for e in _ENTRY.findall(text or ""):
        m = _TITLE.match(unescape(_tag(e, "title")))
        acc = re.search(r"accession-number=([0-9-]+)", e)
        upd = _tag(e, "updated")
        if not m or not acc or not upd:
            continue
        try:
            accepted = datetime.fromisoformat(upd).timestamp()
        except ValueError:
            continue
        form, company, cik, role = m.groups()
        items = ["%s %s" % (a, b.strip()) for a, b in _ITEM.findall(unescape(_tag(e, "summary")))]
        out.append({"form": form, "company": company, "cik": cik, "role": role, "accepted": accepted,
                    "accession": acc.group(1), "items": items})
    return out


def session_of(ts):
    """the first session whose close is after `ts` (a filing after the close belongs to the next session)."""
    d = cal._as_date(ts)
    if cal.is_trading_day(d) and ts < cal.session_close(d):
        return d.isoformat()
    return cal.next_trading_day(d).isoformat()


def event_minute(ts, session):
    """whole minutes from the session's 09:30 ET (the source's minute_from_open clock; negative before the open)."""
    return int(math.floor((float(ts) - cal.session_open(session)) / 60.0))


class CurrentReports:
    """the EDGAR latest-filings tape of 8-K / 6-K current reports, cached in <dir>/edgar_current.json."""

    def __init__(self, path, fetch=get):
        self.path = path
        self.fetch = fetch
        self.doc = read_json(path, None) or {"at": 0, "filings": {}}
        for r in self.doc.get("filings", {}).values():
            r.setdefault("session", session_of(r["accepted"]))

    def refresh(self, now):
        if now - float(self.doc.get("at") or 0) < EVENTS_REFRESH_S:
            return False
        have = self.doc.setdefault("filings", {})
        got_any = False
        for form in FORMS:
            for page in range(MAX_PAGES):
                try:
                    text = _sec(self.fetch, CURRENT_URL, {"action": "getcurrent", "type": form, "company": "",
                                                          "dateb": "", "owner": "include", "start": page * 100,
                                                          "count": 100, "output": "atom"}, as_text=True)
                except Exception:
                    break
                rows = parse_current(text)
                if not rows:
                    break
                got_any = True
                new = 0
                for r in rows:
                    if r["form"] != form or r["role"] != "Filer":
                        continue
                    if r["accession"] not in have:
                        r["session"] = session_of(r["accepted"])
                        have[r["accession"]] = r
                        new += 1
                oldest = min(r["accepted"] for r in rows)
                if new == 0 or oldest < now - EVENTS_KEEP_S:
                    break
        for k in [k for k, r in have.items() if float(r["accepted"]) < now - EVENTS_KEEP_S]:
            have.pop(k)
        if got_any:
            self.doc["at"] = now
            _save(self.path, self.doc)
        return got_any

    def events(self, session, tickers_by_cik, universe=None):
        """the session's events in the source's frame layout, oldest first."""
        out = []
        for r in sorted(self.doc.get("filings", {}).values(), key=lambda r: (r["accepted"], r["accession"])):
            if r.get("session") != session:
                continue
            for t in tickers_by_cik.get(r["cik"], ()):
                if universe is not None and t not in universe:
                    continue
                out.append({"date": session, "symbol": t, "event_type": " ".join([r["form"]] + r["items"])[:200],
                            "news_verified": True, "event_minute": event_minute(r["accepted"], session),
                            "accession": r["accession"], "accepted": r["accepted"]})
        return out


# -- tickers, sector, shares ---------------------------------------------------------------------------------------
def norm(sym):
    return str(sym or "").upper().strip().replace("-", ".").replace("/", ".")


def tickers_by_cik(d, now, fetch=get):
    """{CIK10: [TICKER, ...]} from company_tickers.json (tickers in the desk's dotted class form)."""
    path = os.path.join(d, "tickers.json")
    doc = _load(path, None)
    if doc and now - float(doc.get("at") or 0) < TICKERS_TTL_S:
        return doc["map"]
    try:
        raw = _sec(fetch, TICKERS_URL)
        m = {}
        for r in (raw or {}).values():
            m.setdefault("%010d" % int(r["cik_str"]), []).append(norm(r["ticker"]))
        if m:
            _save(path, {"at": now, "map": m})
            return m
    except Exception:
        pass
    return (doc or {}).get("map") or {}


def ciks_by_ticker(m):
    """the inverted map: {TICKER: CIK10}."""
    return {t: c for c, ts in (m or {}).items() for t in ts}


def profile(d, cik, now, fetch=get, budget=None):
    """{"sector": industry office | sic description | None, "sic": code} for a CIK (cached)."""
    path = os.path.join(d, "profiles.json")
    doc = dict(_load(path, None) or {})
    hit = doc.get(cik)
    if hit and now - float(hit.get("at") or 0) < PROFILE_TTL_S:
        return hit
    if budget is not None and budget[0] <= 0:
        return hit
    if budget is not None:
        budget[0] -= 1
    try:
        raw = _sec(fetch, SUBMISSIONS_URL.format(cik=cik)) or {}
    except Exception:
        return hit
    office = re.sub(r"^\s*\d+\s*", "", str(raw.get("ownerOrg") or "")).strip()
    rec = {"sector": office or (str(raw.get("sicDescription") or "").strip() or None), "sic": raw.get("sic"),
           "at": now}
    doc[cik] = rec
    _save(path, doc)
    return rec


def shares_from_facts(facts):
    """(shares, end, filed) from the latest-filed cover-page share count; None when the filer reports none."""
    f = (facts or {}).get("facts") or {}
    for ns, tag in (("dei", "EntityCommonStockSharesOutstanding"), ("us-gaap", "CommonStockSharesOutstanding")):
        units = (((f.get(ns) or {}).get(tag) or {}).get("units") or {}).get("shares") or []
        best = None
        for u in units:
            try:
                v, end, filed = float(u["val"]), str(u.get("end") or ""), str(u.get("filed") or "")
            except (KeyError, TypeError, ValueError):
                continue
            if v > 0 and (best is None or (filed, end) > (best[2], best[1])):
                best = (v, end, filed)
        if best:
            return best
    return None


def shares(d, cik, now, fetch=get, budget=None):
    """{"shares", "end", "filed"} (or {"shares": None}) for a CIK (cached; only the extracted values are kept)."""
    path = os.path.join(d, "shares.json")
    doc = dict(_load(path, None) or {})
    hit = doc.get(cik)
    if hit and now - float(hit.get("at") or 0) < FACTS_TTL_S:
        return hit
    if budget is not None and budget[0] <= 0:
        return hit
    if budget is not None:
        budget[0] -= 1
    try:
        raw = _sec(fetch, FACTS_URL.format(cik=cik))
    except Exception:
        return hit
    got = shares_from_facts(raw)
    rec = {"shares": got[0], "end": got[1], "filed": got[2], "at": now} if got else {"shares": None, "at": now}
    doc[cik] = rec
    _save(path, doc)
    return rec


# -- listing ---------------------------------------------------------------------------------------------------------
def parse_listing(nasdaq_text, other_text):
    """{SYMBOL: is_etf} from the two symbol-directory files (header row, '|' separated, a trailer row)."""
    out = {}
    for text, sym_cols in ((nasdaq_text, ("Symbol",)), (other_text, ("ACT Symbol", "CQS Symbol"))):
        lines = [l for l in (text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            continue
        head = lines[0].split("|")
        if "ETF" not in head:
            continue
        ie = head.index("ETF")
        idx = [head.index(c) for c in sym_cols if c in head]
        for l in lines[1:]:
            cols = l.split("|")
            if len(cols) <= ie or l.startswith("File Creation Time"):
                continue
            for i in idx:
                if i < len(cols) and cols[i].strip():
                    out[norm(cols[i])] = cols[ie].strip().upper() == "Y"
    return out


def listing(d, now, fetch=get):
    path = os.path.join(d, "listing.json")
    doc = _load(path, None)
    if doc and now - float(doc.get("at") or 0) < LISTING_TTL_S:
        return doc["etf"]
    try:
        texts = [fetch(u, None, as_text=True) for u in LISTING_URLS]
        m = parse_listing(*texts)
        if m:
            etf = sorted(s for s, e in m.items() if e)
            _save(path, {"at": now, "etf": etf, "n": len(m)})
            return etf
    except Exception:
        pass
    return (doc or {}).get("etf")
