"""EDGAR buyback scan — the earnings_buyback sleeve's producer: the old desk's edgar_buyback_scraper.py (8-K stock
repurchase announcements of >= 5% of the shares; Quantpedia #0271, Amini & Singal) on the desk's fetch conventions.

  ticker_to_cik ....... the CIK cache, else SEC company_tickers.json: the first row whose ticker matches, its
                        cik_str zero-padded to 10 digits (cached)
  get_recent_filings .. data.sec.gov submissions: the first `count` filings of the form (exactly "8-K") among the
                        newest count x 3; a failed fetch is a scan error (filings_fetch_failed), an unreadable
                        document no filings
  fetch_filing_text ... the filing's primary document, www.sec.gov/Archives/edgar/data/<cik>/<accession>/<doc>
  parse_buyback ....... verbatim: the first buyback keyword pattern found in the lower-cased text; the first
                        percentage within 1-50 in the 500 characters either side of that match; the first dollar
                        amount >= $10M anywhere; a buyback qualifies at >= 5% (no dollar fallback)
  check_ticker ........ the ticker's 8-Ks filed on or after now - days_back (the naive UTC clock: the old VM's local
                        clock was UTC), each parsed; a qualifying one carries its accession
  scan_mode ........... every ticker in order (one ticker's failure is a scan error, never a dead scan) -> the scan
                        file buyback_scan_YYYYMMDD_HHMM.json {scan_date, days_back, tickers_scanned, results, count,
                        errors, tickers_failed}
  load_latest ......... the newest scan file by mtime, with that mtime — the sleeve's feed (feed:buyback_scan); the
                        8-day staleness rule is the sleeve's own

The desk job `edgar_buyback` (desk/jobs.py) runs scan_mode weekdays from 07:35 ET over the old scan universe (the
basket and the phase universe, sorted; femto_specs.EDGAR_UNIVERSE) with days_back 30 (old cron
desk-edgar-buyback-scan). Files live under <root>/cache/edgar_buyback/.

Named divergences (plumbing only; every decision function is the old's): requests go through the desk's
data/http.get (its per-host pacing, which already spaces www.sec.gov and data.sec.gov 0.15 s apart, and its retries
with backoff on 429 / 5xx / transport errors; the old made one attempt and read any failure as an empty document),
with this module's own 0.15 s spacing across the SEC hosts (the old slept 0.15 s before every request); no gzip
negotiation (identity encoding); the text decoded as the old's errors="ignore" (the desk decodes invalid UTF-8 as
U+FFFD, removed again here — a document that itself carries U+FFFD loses it); the User-Agent is $SEC_USER_AGENT or
"MasterDesk-PaperResearch/1.0" (the old header carried a personal email address: not carried); no static research
ticker->CIK map (the old read desk/hidden_state/mcap_edgar/ticker_cik.json first because www.sec.gov was WAF-blocked
from its network) and company_tickers.json is downloaded once per scan (the old re-downloaded it for every uncached
ticker; a failed download is retried at the next ticker, as the old's); files are written atomically; the newest
scan is the last by mtime with ties broken by name (the old: by directory order); a scan file that is not a JSON
object is no scan (the old's pass failed on it)."""
import glob
import json
import os
import re
import tempfile
import time
from datetime import datetime, timedelta, timezone

from ..data.http import get
from ..util import read_json, write_json_atomic

DEFAULT_USER_AGENT = "MasterDesk-PaperResearch/1.0"
RATE_LIMIT_DELAY = 0.15          # the old: SEC allows 10 requests/second
DAYS_BACK = 30                   # the old cron: --days-back 30
SCAN_GLOB = "buyback_scan_*.json"

# Buyback keywords (case-insensitive) — verbatim
BUYBACK_PATTERNS = [
    r'stock repurchase (program|plan|authori[sz]ation)',
    r'share repurchase (program|plan|authori[sz]ation)',
    r'repurchase (of|up to) ',
    r'buyback (program|plan|authori[sz]ation)',
    r'authori[sz]ed (a|the) (stock|share) repurchase',
    r'board (authori[sz]ed|approved) (a|the) repurchase',
]

PCT_PATTERN = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
DOLLAR_PATTERN = r'\$([\d,\.]+)\s*(million|billion|M|B)?'


def out_dir(root):
    """<root>/cache/edgar_buyback — the CIK cache and the scan files."""
    return os.path.join(root, "cache", "edgar_buyback")


def user_agent():
    """SEC fair access wants an identifying User-Agent: $SEC_USER_AGENT, else the desk's (no email address)."""
    return os.environ.get("SEC_USER_AGENT") or DEFAULT_USER_AGENT


_LAST = [0.0]


def _pace(sleep=time.sleep, clock=time.monotonic):
    """the old RATE_LIMIT_DELAY: at least 0.15 s between two SEC requests, whichever host."""
    wait = _LAST[0] + RATE_LIMIT_DELAY - clock()
    if wait > 0:
        sleep(wait)
    _LAST[0] = clock()


def parse_buyback(filing_text: str, ticker: str, filing_date: str) -> dict | None:
    """
    Parse filing text for buyback announcement.
    Returns dict if qualifying buyback found, None otherwise.
    (verbatim: the old edgar_buyback_scraper.parse_buyback)
    """
    text_lower = filing_text.lower()

    # Check for buyback keywords
    found = False
    kw_match = None
    for pattern in BUYBACK_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            found = True
            kw_match = m
            break

    if not found:
        return None

    # Extract percentage — ONLY from text near the buyback mention.
    # Find the buyback keyword position, then search within ±500 chars
    # for a percentage. This prevents false association with unrelated
    # percentages elsewhere in the filing (e.g., "revenue grew 12%").
    pct = None
    try:
        # 3x-daily bugcheck 2026-10-10 (MINOR): the old code re-searched
        # m.group(0) AS A REGEX -- metacharacters in the matched text
        # (notably the trailing $ in the board-approved pattern, which
        # becomes an end-anchor) could fail or land the context window
        # elsewhere. Use the match offsets directly.
        if kw_match:
            start = max(0, kw_match.start() - 500)
            end = min(len(filing_text), kw_match.end() + 500)
            context = filing_text[start:end]
            pct_matches = re.findall(PCT_PATTERN, context, re.IGNORECASE)
            for p in pct_matches:
                try:
                    val = float(p)
                    if 1 <= val <= 50:
                        pct = val
                        break
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass

    # Extract dollar amount
    dollar_amt = None
    dollar_matches = re.findall(DOLLAR_PATTERN, filing_text)
    for amt_str, unit in dollar_matches:
        try:
            amt = float(amt_str.replace(',', ''))
            unit_lower = (unit or '').lower()
            if 'billion' in unit_lower or unit_lower == 'b':
                amt *= 1e9
            elif 'million' in unit_lower or unit_lower == 'm':
                amt *= 1e6
            if amt >= 10_000_000:  # $10M+ is meaningful
                dollar_amt = amt
                break
        except Exception:   # the old bare except: float() of a malformed amount ("." / "1.2.3") raises ValueError
            pass

    # Check threshold: ≥5% of outstanding shares (per Amini & Singal).
    # The $100M dollar fallback was REMOVED — it deviated from the research
    # criterion. A $100M buyback on a $50B company is 0.2%, not qualifying.
    # Only percentage-based announcements within context qualify.
    meets_pct = pct is not None and pct >= 5.0

    if meets_pct:
        return {
            'ticker': ticker.upper(),
            'filing_date': filing_date,
            'buyback_pct': pct,
            'dollar_amount': dollar_amt,
            'dollar_formatted': f"${dollar_amt/1e9:.1f}B" if dollar_amt and dollar_amt >= 1e9 else f"${dollar_amt/1e6:.0f}M" if dollar_amt else None,
            'meets_threshold': True,
            'matched_text': (kw_match.group(0) if kw_match else None),
        }

    return None


class Scanner:
    """one scan's state: the clock, the fetch, the output directory and the scan errors (the old SCAN_ERRORS)."""

    def __init__(self, directory, clock=time.time, fetch=None, sleep=time.sleep):
        self.dir = directory
        self.clock = clock
        self.fetch = fetch                 # None: the desk's data/http.get
        self.sleep = sleep
        self.errors = []
        self.last_path = None
        self._tickers_doc = None

    # -- I/O ------------------------------------------------------------------------------------------------
    def now_naive(self):
        """the old datetime.now(): naive local time on a UTC clock."""
        return datetime.fromtimestamp(float(self.clock()), tz=timezone.utc).replace(tzinfo=None)

    def fetch_url(self, url: str, timeout: int = 30) -> str:
        """the old fetch_url: the document's text, "" on any failure (a 404, an HTTP error after the desk's retries,
        a transport failure)."""
        _pace(self.sleep)
        try:
            text = (self.fetch or get)(url, timeout=timeout, as_text=True, headers={"User-Agent": user_agent()})
        except Exception:
            return ""
        return (text or "").replace("�", "")      # the old decode(errors="ignore")

    def _cik_path(self):
        return os.path.join(self.dir, "cik_cache.json")

    def load_cik_cache(self) -> dict:
        try:
            cache = read_json(self._cik_path(), {})
        except Exception:
            return {}
        return cache if isinstance(cache, dict) else {}

    def save_cik_cache(self, cache: dict):
        write_json_atomic(self._cik_path(), cache, indent=2)

    def _company_tickers(self) -> str:
        if self._tickers_doc is None:
            data = self.fetch_url("https://www.sec.gov/files/company_tickers.json")
            if not data:
                return ""
            self._tickers_doc = data
        return self._tickers_doc

    # -- the old functions --------------------------------------------------------------------------------
    def ticker_to_cik(self, ticker: str) -> str | None:
        """
        Convert ticker to CIK using SEC's company_tickers.json.
        Returns 10-digit CIK string or None.
        """
        cache = self.load_cik_cache()
        ticker_upper = ticker.upper()

        if ticker_upper in cache:
            return cache[ticker_upper]

        data = self._company_tickers()
        if not data:
            return None

        try:
            tickers = json.loads(data)
            for key, info in tickers.items():
                if info.get('ticker', '').upper() == ticker_upper:
                    cik = str(info['cik_str']).zfill(10)
                    cache[ticker_upper] = cik
                    self.save_cik_cache(cache)
                    return cik
        except Exception:
            pass

        return None

    def get_recent_filings(self, cik: str, form: str = "8-K", count: int = 10) -> list:
        """
        Get recent filings for a CIK using the EDGAR JSON API.
        Returns list of filing dicts with accession numbers and dates.
        """
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        data = self.fetch_url(url)
        if not data:
            # 2026-10-12 institutional audit (W3): a failed fetch is not "no filings".
            self.errors.append({"cik": cik, "error": "filings_fetch_failed"})
            return []

        try:
            submissions = json.loads(data)
            filings = submissions.get('filings', {}).get('recent', {})

            forms = filings.get('form', [])
            accession = filings.get('accessionNumber', [])
            filing_dates = filings.get('filingDate', [])
            primary_docs = filings.get('primaryDocument', [])

            results = []
            for i in range(min(len(forms), count * 3)):  # Check extra to find enough 8-Ks
                if forms[i] == form:
                    results.append({
                        'form': forms[i],
                        'accession': accession[i].replace('-', ''),
                        'accession_dash': accession[i],
                        'filing_date': filing_dates[i],
                        'primary_doc': primary_docs[i],
                        'cik': cik,
                    })
                    if len(results) >= count:
                        break

            return results
        except Exception:
            return []

    def fetch_filing_text(self, cik: str, accession: str, primary_doc: str) -> str:
        """
        Fetch the full text of a filing.
        URL format: https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}
        """
        cik_trimmed = str(int(cik))
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_trimmed}/{accession}/{primary_doc}"
        return self.fetch_url(url)

    def check_ticker(self, ticker: str, days_back: int = 60) -> list:
        """
        Check a ticker for buyback announcements in recent 8-K filings.
        Returns list of qualifying buybacks.
        """
        ticker = ticker.upper()
        cik = self.ticker_to_cik(ticker)
        if not cik:
            self.errors.append({"ticker": ticker, "error": "cik_not_found"})
            return []

        filings = self.get_recent_filings(cik, "8-K", count=10)
        cutoff = self.now_naive() - timedelta(days=days_back)
        results = []

        for filing in filings:
            filing_date = datetime.strptime(filing['filing_date'], '%Y-%m-%d')
            if filing_date < cutoff:
                continue

            text = self.fetch_filing_text(cik, filing['accession'], filing['primary_doc'])
            if not text:
                continue

            parsed = parse_buyback(text, ticker, filing['filing_date'])
            if parsed:
                parsed['accession'] = filing['accession_dash']
                results.append(parsed)

        return results

    def scan_mode(self, days_back: int, tickers: list | None = None) -> list:
        """
        Scan for buybacks over the tickers, in order, and write the scan file. No tickers: no scan (the old printed
        a note and wrote nothing).
        """
        if not tickers:
            return []

        self.errors.clear()
        all_results = []
        for ticker in tickers:
            try:
                results = self.check_ticker(ticker.strip(), days_back)
            except Exception as e:  # noqa: BLE001 -- one bad ticker != dead scan
                self.errors.append({"ticker": ticker.strip(), "error": "exception: %s" % str(e)[:120]})
                results = []
            all_results.extend(results)

        now = self.now_naive()
        path = os.path.join(self.dir, f"buyback_scan_{now.strftime('%Y%m%d_%H%M')}.json")
        _write(path, {
            'scan_date': now.isoformat(),
            'days_back': days_back,
            'tickers_scanned': tickers,
            'results': all_results,
            'count': len(all_results),
            # 2026-10-12 audit (W3): fetch failures are first-class output -- an empty scan with errors is NOT
            # "no signals".
            'errors': list(self.errors),
            'tickers_failed': len(self.errors),
        })
        self.last_path = path
        return all_results


def _write(path, doc):
    """the old json.dump(indent=2), atomically (tmp + rename: a reader never sees half a scan)."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(doc, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_latest(directory):
    """the newest scan file by mtime: {"file", "mtime", "scan"} — None when there is none or it is unreadable (the
    old latest_scan: no fallback to an older file)."""
    files = sorted(glob.glob(os.path.join(directory, SCAN_GLOB)))
    if not files:
        return None
    try:
        files.sort(key=os.path.getmtime)
        path = files[-1]
        mtime = os.path.getmtime(path)
        with open(path) as f:
            scan = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(scan, dict):
        return None
    return {"file": os.path.basename(path), "mtime": mtime, "scan": scan}


def run(root, tickers, clock=time.time, days_back=DAYS_BACK, fetch=None):
    """the desk job: one scan over `tickers`; returns the run's summary."""
    sc = Scanner(out_dir(root), clock=clock, fetch=fetch)
    results = sc.scan_mode(days_back, list(tickers))
    return {"universe": len(tickers), "results": len(results), "tickers_failed": len(sc.errors),
            "file": os.path.basename(sc.last_path) if sc.last_path else None,
            "signals": [[r["ticker"], r["buyback_pct"], r["filing_date"]] for r in results]}
