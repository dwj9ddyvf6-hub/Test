"""Append-only event ledger (SQLite WAL). The ONLY writer of desk state.
Every state change is an event; sleeve/position state is a pure fold over events, so a restart
(or kill -9) recovers by replaying the ledger. Idempotency: each order carries a deterministic
client_order_id; inserting an already-known (cid, event) pair is a no-op."""
import sqlite3, json, time, hashlib, os, threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, sleeve TEXT NOT NULL,
  kind TEXT NOT NULL, symbol TEXT, cid TEXT, body TEXT NOT NULL, UNIQUE(cid, kind));
CREATE INDEX IF NOT EXISTS ev_sleeve ON events(sleeve);
CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
"""

def cid(sleeve, symbol, signal_key, leg="EN", n=0):
    """Deterministic, namespaced client_order_id: same signal -> same id across restarts (broker dedupes)."""
    h = hashlib.sha1(f"{sleeve}|{symbol}|{signal_key}|{leg}|{n}".encode()).hexdigest()[:20]
    return f"md2-{leg}-{h}"   # 'md2-' prefix: never collides with Lazarus ids (Lazarus uses its own scheme)

class Ledger:
    def __init__(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path; self.db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL"); self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(SCHEMA); self.lock = threading.Lock(); self.writes = 0
    def append(self, sleeve, kind, symbol=None, cid=None, ts=None, **body):
        with self.lock:
            cur = self.db.execute("INSERT OR IGNORE INTO events(ts,sleeve,kind,symbol,cid,body) VALUES(?,?,?,?,?,?)",
                                  (ts or time.time(), sleeve, kind, symbol, cid, json.dumps(body, sort_keys=True, default=str)))
            self.writes += cur.rowcount; return cur.rowcount == 1
    def append_many(self, rows):
        """one transaction for a whole pass (Efficiency: 1 fsync per pass, not per event)."""
        with self.lock:
            self.db.execute("BEGIN")
            n = 0
            for r in rows:
                n += self.db.execute("INSERT OR IGNORE INTO events(ts,sleeve,kind,symbol,cid,body) VALUES(?,?,?,?,?,?)",
                                     (r.get("ts") or time.time(), r["sleeve"], r["kind"], r.get("symbol"), r.get("cid"),
                                      json.dumps(r.get("body", {}), sort_keys=True, default=str))).rowcount
            self.db.execute("COMMIT"); self.writes += n; return n
    def events(self, sleeve=None, since=0):
        q = "SELECT seq,ts,sleeve,kind,symbol,cid,body FROM events WHERE seq>?" + (" AND sleeve=?" if sleeve else "") + " ORDER BY seq"
        for s, ts, sl, k, sym, c, b in self.db.execute(q, (since, sleeve) if sleeve else (since,)):
            yield dict(seq=s, ts=ts, sleeve=sl, kind=k, symbol=sym, cid=c, **json.loads(b))
    def count(self): return self.db.execute("SELECT count(*) FROM events").fetchone()[0]
    def has(self, cid, kind): return self.db.execute("SELECT 1 FROM events WHERE cid=? AND kind=?", (cid, kind)).fetchone() is not None
