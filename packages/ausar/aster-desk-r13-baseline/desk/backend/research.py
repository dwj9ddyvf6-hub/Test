"""Bounded research collection with stored source receipts and catalogue lookup.

Headlines, filings and bars are observations, never trade recommendations. The
collector has no order, funding, policy or strategy-writing capability.
"""
import hashlib
import json
import os
import sqlite3
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from .store import DeskError, now, symbol
from .http_transport import bounded_http
from .research_workflows import ResearchWorkflows, workflow_router


class Research:
    MAX_BYTES = 2_000_000

    def __init__(self, store, providers=None, transport=None):
        self.store, self.providers, self.transport = store, providers, transport
        self.index_path = os.environ.get("ASTER_RESEARCH_INDEX", "")
        self.sec_user_agent = os.environ.get("ASTER_SEC_USER_AGENT", "")
        self.interval = max(900, int(os.environ.get("ASTER_RESEARCH_INTERVAL_SECONDS", "3600")))
        with store.connect() as con:
            con.executescript("""
              CREATE TABLE IF NOT EXISTS research_receipts(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,kind TEXT NOT NULL,source TEXT NOT NULL,source_time TEXT,fetched_at TEXT NOT NULL,payload TEXT NOT NULL,sha256 TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS research_collection(key TEXT PRIMARY KEY,last_attempt TEXT,last_success TEXT,last_error TEXT,next_due REAL NOT NULL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS research_cache(key TEXT PRIMARY KEY,payload TEXT NOT NULL,updated_at TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS research_receipt_symbol ON research_receipts(symbol,fetched_at);
            """)
        self.workflows = ResearchWorkflows(self)

    def _fetch(self, url, headers=None):
        if self.transport:
            return self.transport(url, headers or {})
        status, body = bounded_http("GET", url, headers={"User-Agent": "AsterDesk/1.0", **(headers or {})}, timeout_seconds=8, maximum_bytes=self.MAX_BYTES, follow_redirects=True)
        if not 200 <= status < 300:
            raise RuntimeError("Research source returned an unsuccessful HTTP status")
        return body

    def _record(self, sym, kind, source, payload, source_time=None):
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        sha = hashlib.sha256(encoded.encode()).hexdigest()
        rid = hashlib.sha256((sym + kind + source + sha).encode()).hexdigest()
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO research_receipts VALUES(?,?,?,?,?,?,?,?)", (rid, sym, kind, source, source_time, now(), encoded, sha))
        return {"id": rid, "kind": kind, "symbol": sym, "sha256": sha}

    def headlines(self, sym):
        sym = symbol(sym)
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?" + urllib.parse.urlencode({"s": sym, "region": "US", "lang": "en-US"})
        root = ET.fromstring(self._fetch(url))
        if root.tag not in {"rss", "feed", "{http://www.w3.org/2005/Atom}feed"}:
            raise RuntimeError("Research feed did not return an RSS or Atom document")
        receipts = []
        atom = root.tag != "rss"
        prefix = "{http://www.w3.org/2005/Atom}" if root.tag.startswith("{") else ""
        nodes = root.findall(".//" + prefix + "entry") if atom else root.findall(".//item")
        for node in nodes[:30]:
            title = node.findtext(prefix + "title", "").strip()
            if atom:
                links = node.findall(prefix + "link")
                selected = next((item for item in links if item.get("rel", "alternate") == "alternate" and item.get("href")), None)
                link = selected.get("href", "").strip() if selected is not None else ""
                date = node.findtext(prefix + "published") or node.findtext(prefix + "updated", "")
                summary = node.findtext(prefix + "summary") or node.findtext(prefix + "content", "")
            else:
                link = node.findtext("link", "").strip()
                date, summary = node.findtext("pubDate", ""), node.findtext("description", "")
            if not title or not link:
                continue
            try:
                parsed = datetime.fromisoformat(date.replace("Z", "+00:00")) if atom and date else parsedate_to_datetime(date) if date else None
                source_time = parsed.astimezone(timezone.utc).isoformat() if parsed and parsed.tzinfo else None
            except (ValueError, TypeError):
                source_time = None
            receipts.append(self._record(sym, "headline", url, {"title": title, "url": link, "summary": summary[:12000], "publisher_date": date, "source": "Yahoo Finance RSS aggregation", "scope": "Headline evidence; not a verified corporate filing or trading signal"}, source_time))
        return receipts

    def filings(self, sym):
        if not self.sec_user_agent:
            return {"status": "unconfigured", "detail": "Set ASTER_SEC_USER_AGENT to identify SEC requests"}
        sym = symbol(sym)
        with self.store.connect() as con:
            cached = con.execute("SELECT * FROM research_cache WHERE key='sec-tickers'").fetchone()
        if cached and time.time() - datetime.fromisoformat(cached["updated_at"]).timestamp() < 86400:
            mapping = json.loads(cached["payload"])
        else:
            mapping = json.loads(self._fetch("https://www.sec.gov/files/company_tickers.json", {"User-Agent": self.sec_user_agent}))
            with self.store.transaction() as con:
                con.execute("INSERT OR REPLACE INTO research_cache VALUES('sec-tickers',?,?)", (json.dumps(mapping), now()))
        match = next((r for r in mapping.values() if r.get("ticker", "").upper().replace("-", ".") == sym.replace("-", ".")), None)
        if not match:
            return {"status": "not_found", "symbol": sym, "detail": "No SEC issuer mapping; fund/index symbols may have no company submission record"}
        cik = str(match["cik_str"]).zfill(10)
        url = "https://data.sec.gov/submissions/CIK" + cik + ".json"
        submissions = json.loads(self._fetch(url, {"User-Agent": self.sec_user_agent}))
        recent = submissions.get("filings", {}).get("recent", {})
        rows = []
        for i, accession in enumerate(recent.get("accessionNumber", [])[:25]):
            record = {key: recent.get(key, [])[i] if i < len(recent.get(key, [])) else None for key in ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "form", "primaryDocument")}
            record["issuer"] = submissions.get("name")
            record["url"] = "https://www.sec.gov/Archives/edgar/data/" + str(int(cik)) + "/" + accession.replace("-", "") + "/" + (record["primaryDocument"] or "")
            rows.append(self._record(sym, "filing", url, record, record["acceptanceDateTime"]))
        return {"status": "collected", "receipts": rows, "cik": cik}

    def collect(self, symbols=None, force=False):
        if symbols is None:
            with self.store.connect() as con:
                symbols = [r[0] for r in con.execute("SELECT symbol FROM watchlist ORDER BY symbol")]
        symbols = list(dict.fromkeys(symbol(s) for s in symbols))[:2]
        results = []
        for sym in symbols:
            key = "research:" + sym
            with self.store.connect() as con:
                row = con.execute("SELECT * FROM research_collection WHERE key=?", (key,)).fetchone()
            if row and not force and row["next_due"] > time.time():
                continue
            with self.store.transaction() as con:
                con.execute("INSERT INTO research_collection(key,last_attempt,next_due) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET last_attempt=excluded.last_attempt,next_due=excluded.next_due", (key, now(), time.time() + self.interval))
            result = {"symbol": sym, "sources": {}, "errors": []}
            for name, collector in (("headlines", self.headlines), ("filings", self.filings)):
                try:
                    result["sources"][name] = collector(sym)
                except Exception:
                    # URLs/headers and provider responses may contain private data; only
                    # a bounded source label reaches status, never transport internals.
                    result["errors"].append(name + " collection failed; will retry")
            success = bool(result["sources"].get("headlines")) or result["sources"].get("filings", {}).get("status") == "collected"
            with self.store.transaction() as con:
                con.execute("UPDATE research_collection SET last_success=CASE WHEN ? THEN ? ELSE last_success END,last_error=?,next_due=? WHERE key=?", (success, now(), "; ".join(result["errors"]) or None, time.time() + (self.interval if success else 900), key))
                self.store.event(con, "research_collection", "data_steward", "Collected research observations for " + sym if success else "Research collection incomplete for " + sym, {"symbol": sym, "successful": success, "sources": list(result["sources"]), "errors": result["errors"]})
            results.append(result)
        return {"results": results, "strategy_count": 0, "trade_decisions": 0}

    def operate(self):
        # Rotate through due symbols; a failed first ticker cannot starve the rest.
        with self.store.connect() as con:
            symbols = [r[0] for r in con.execute("SELECT w.symbol FROM watchlist w LEFT JOIN research_collection r ON r.key='research:'||w.symbol WHERE r.next_due IS NULL OR r.next_due<=? ORDER BY COALESCE(r.next_due,0),w.symbol LIMIT 2", (time.time(),))]
        return {**self.collect(symbols), "workflow": self.workflows.operate()}

    def search(self, query, limit=25):
        if not self.index_path:
            return {"configured": False, "results": [], "detail": "Set ASTER_RESEARCH_INDEX to the saved repository catalogue SQLite file"}
        path = Path(self.index_path)
        if not path.is_file():
            raise DeskError("Configured research index is unavailable", 503)
        tokens = [token for token in query.strip().split() if token][:8]
        if not tokens:
            return {"configured": True, "results": []}
        uri = path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=3) as con:
            con.row_factory = sqlite3.Row
            clauses, params = [], []
            for token in tokens:
                # Literal LIKE metacharacters are escaped; query is not executable SQL.
                literal = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                clauses.append("(f.path LIKE ? ESCAPE '\\' OR f.title LIKE ? ESCAPE '\\' OR f.catalogue_terms LIKE ? ESCAPE '\\')")
                params += ["%" + literal + "%"] * 3
            sql = "SELECT f.id,f.repo,f.path,f.blob_sha,f.kind,f.title,f.local_source FROM files f WHERE " + " AND ".join(clauses) + " ORDER BY f.on_default DESC,f.repo,f.path LIMIT ?"
            rows = [dict(r) for r in con.execute(sql, params + [min(50, max(1, limit))])]
            for row in rows:
                row["refs"] = [dict(r) for r in con.execute("SELECT ref_type,ref,commit_sha FROM locations WHERE file_id=? LIMIT 5", (row["id"],))]
        return {"configured": True, "results": rows, "scope": "Read-only catalogue path and provenance search; no trading decisions"}

    def snapshot(self):
        with self.store.connect() as con:
            receipts = []
            for row in con.execute("SELECT * FROM research_receipts ORDER BY fetched_at DESC LIMIT 150"):
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                receipts.append(item)
            return {**self.workflows.snapshot(), "receipts": receipts, "receipt_count": con.execute("SELECT COUNT(*) FROM research_receipts").fetchone()[0], "collections": [dict(r) for r in con.execute("SELECT * FROM research_collection ORDER BY key")], "sources": {"headlines": "Yahoo Finance RSS", "filings": {"provider": "SEC EDGAR", "configured": bool(self.sec_user_agent)}, "repository_library": {"configured": bool(self.index_path), "available": bool(self.index_path and Path(self.index_path).is_file())}}, "trade_decisions": 0}

    def export(self):
        with self.store.connect() as con:
            return {name: [dict(r) for r in con.execute("SELECT * FROM " + name)] for name in ("research_receipts", "research_collection", "research_workflows", "research_runs", "research_nodes", "research_node_receipts")}


def research_router(research):
    router = APIRouter(prefix="/api/research")
    router.include_router(workflow_router(research.workflows), prefix="")

    @router.get("")
    def snapshot():
        return research.snapshot()

    @router.get("/library")
    def search(q: str = "", limit: int = 25):
        if len(q) > 500:
            raise DeskError("Library query is too long", 422)
        return research.search(q, limit)

    class Collection(BaseModel):
        model_config = ConfigDict(extra="forbid")
        symbols: list[str] = Field(max_length=2)

    @router.post("/collect")
    def collect(body: Collection):
        return research.collect(body.symbols, force=True)

    return router
