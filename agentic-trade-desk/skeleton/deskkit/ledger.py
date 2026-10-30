"""Append-only, hash-chained event ledger (SQLite).

* UPDATE and DELETE are blocked by triggers: history is never edited. Corrections are new
  `note` events that point at the event they correct.
* Each row stores sha256(prev_hash + payload) so truncation or edits are detectable.
* State (positions, cash) is a pure *fold* over the events, so it can always be replayed
  and compared with the live in-memory book.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from typing import Iterable, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  prev TEXT NOT NULL,
  hash TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
"""


class Ledger:
    def __init__(self, path: str):
        self.path = path
        # journal_mode: use WAL on a local disk. On network/FUSE mounts use DELETE (see pitfalls: WAL on FUSE).
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.executescript(SCHEMA)
        row = self.db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        self._last = row[0] if row else "genesis"

    def append(self, kind: str, payload: dict, ts: float | None = None) -> int:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256((self._last + kind + body).encode()).hexdigest()
        cur = self.db.execute(
            "INSERT INTO events(ts,kind,payload,prev,hash) VALUES(?,?,?,?,?)",
            (ts if ts is not None else time.time(), kind, body, self._last, h))
        self._last = h
        return cur.lastrowid

    def events(self, kinds: Iterable[str] | None = None) -> Iterator[dict]:
        q = "SELECT seq,ts,kind,payload FROM events ORDER BY seq"
        for seq, ts, kind, payload in self.db.execute(q):
            if kinds is None or kind in kinds:
                yield {"seq": seq, "ts": ts, "kind": kind, **json.loads(payload)}

    def has(self, kind: str, **match) -> bool:
        """True if an event of `kind` exists whose payload contains all `match` items."""
        for ev in self.events([kind]):
            if all(ev.get(k) == v for k, v in match.items()):
                return True
        return False

    def verify_chain(self) -> bool:
        prev = "genesis"
        for _seq, _ts, kind, payload, p, h in self.db.execute(
                "SELECT seq,ts,kind,payload,prev,hash FROM events ORDER BY seq"):
            if p != prev or hashlib.sha256((prev + kind + payload).encode()).hexdigest() != h:
                return False
            prev = h
        return True

    def positions(self) -> dict:
        """Replay fills into {(sleeve,symbol): qty}. Pure fold: same events -> same book."""
        book: dict[tuple, float] = {}
        for ev in self.events(["fill"]):
            k = (ev["sleeve"], ev["symbol"])
            book[k] = round(book.get(k, 0.0) + (ev["qty"] if ev["side"] == "buy" else -ev["qty"]), 8)
            if book[k] == 0:
                del book[k]
        return book
