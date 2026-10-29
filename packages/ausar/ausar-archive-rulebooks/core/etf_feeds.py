"""RR3 item 1 (2026-10-15): free_etf producer — Wave-pattern feeds
for the one sleeve the wiring waves never served.

The sleeve (sleeves/free_etf.py, port of the old desk's
aurelia_free_etf.py) consumes, via context.extra:
  "etf_books":    [book dicts {id, fixed_weights?|symbols, policy}]
  "etf_receipt":  {"histories": {sym: [{session, close}...]},
                   "source_receipts_verified": bool, "feed": "sip",
                   "adjustment": "all", "signal_session": iso}
  "quotes":       {sym: {"t", "received_at", "bp", "ap"}} (IEX)
  "held_rows":    {row_id: qty} — per-BOOK holdings keyed
                   FREE_ETF_<book>_<symbol>, reconstructed from the
                   dispatch records (held_rows_from_records below;
                   AUDIT-20261018-CURE13: the sleeve's old fallback to
                   the dispatch slice_state per symbol conflated every
                   book's ownership with the sleeve-aggregate qty, so
                   this key is now supplied whenever its source is
                   wired, and omitted — never served as {} — when the
                   source is unreadable)
  "spent_usd":    session buys so far (day-cap accounting)
  "broker_qqq_qty" / "attributed_others": QQQ grant math inputs

Sourceable inputs, served here through the core data doors:
  * receipt histories — Alpaca SIP daily bars, adjustment=all (the
    sleeve contract's own signal definition), prior completed
    sessions only (rows on/after the current session are dropped:
    the signal is the COMPLETED receipt). Verified flag is set only
    when a history actually came back for every book symbol.
  * quotes — Alpaca IEX latest quotes (the sleeve's execution quote
    is IEX by its own contract, never spliced into the SIP history);
    received_at is stamped here, at fetch time.
  * spent_usd / broker_qqq_qty / attributed_others — ledger, broker
    and slices truth, supplied by the run_live assembly closures.

RULEBOOK RECOVERED (EA2a, 2026-10-15, User's 10:44 order): the
source rulebook is strategies/r19/etf_rules.json (schema
aster-r19-etf-rules-v1, 26 sleeves) in the Ausar archive payload
on GitHub (dwj9ddyvf6-hub/Agentic-Trading-Desk branch
aurelia-paper-desk, ausar-archive/.../desk-source/strategies/r19/
etf_rules.json, sha256 f7073e90…), ported verbatim to
config/aurelia_free_etf_rules.json — the namespaced filename the
old Femto _books() expected, with the same top-level "sleeves"
list. run_live's fetch_books reads that config path. The selection
backend (backend.r19_etf.select) is ported verbatim into the
sleeve's targets_for. Books carrying a secondary_provider (the six
INTERVAL_* books, secondary=YAHOO) still fail closed when no YAHOO
secondary scores are supplied: the source's YAHOO adj_close parquet
cache exists nowhere in the searched corpus (ledger in the EA2a
audit note).

The sleeve is inert BY ITS OWN DESIGN after 2026-10-19 (the
fixed-weight initial schedule, origin 2026-10-13, ends; selection
backend fenced). This wiring makes its evaluations real inputs —
it does not change when or whether it trades.

INTERVAL SECONDARY SCORES (D2, audit round 3, X-4): the six
INTERVAL_* books carry secondary_provider="YAHOO" and fail closed
without extra["etf_secondary_scores"]. Round 2 recorded the
source's parquet cache as absent and stopped there — a failed
lookup, not an absent definition: the defining computation is the
old desk's aurelia_free_etf._yahoo_scores, and it is produced here.
Per symbol, the Yahoo daily adj_close series is aligned to the SIP
receipt sessions of the book's FIRST symbol (QQQ for all six
books): sessions = the receipt's last 252 sessions, and EVERY one
must exist in the Yahoo series with adj_close > 0, else the whole
product is absent (fail closed, never partial). The score formula
is the sleeve's own: ln(closes[-1] / closes[-127]) over the aligned
closes. The product is cached per session in-process and on disk
(state/live/etf_secondary_scores.json, session-keyed — a stale
session is never served, the M2 qualifiers pattern). Yahoo is used
for daily adj_close PRICE data only, under the round-3 brief's
explicit permission; no Yahoo volume is read anywhere.
"""
import json
import math
import os
import pathlib
import re
import tempfile
from datetime import datetime, timezone

SLEEVE_ID = "free_etf"

_ROW_RE = re.compile(r"row=(FREE_ETF_[A-Za-z0-9_]+)")


def held_rows_from_records(rows):
    """Per-book held rows for free_etf, reconstructed from the
    dispatch records (the ledger rows dispatch itself wrote).

    Attribution source: every free_etf intent's reason carries its
    row id (row=FREE_ETF_<book>_<symbol>). Entry `fill` rows carry
    that reason and the signed qty booked; `exit_submitted` rows
    carry it verbatim with the exit's qty magnitude (free_etf books
    are long-only, so an exit moves its row toward zero). Rows for
    other sleeves, rows without a row id, and virtual QQQ
    attributions (never ordered, never row-held) contribute nothing.
    Zero rows are pruned. This is a DERIVED view of the ledger — the
    same derivation discipline as core.slice_sync — not a second
    book of record.

    R2 cure (2026-10-22, audit row 15(d)): a free_etf fill or
    exit_submitted row whose reason carries NO row tag cannot be
    attributed to any book. The pre-cure code silently dropped it,
    so the reconstruction understated ownership with no surface
    anywhere: the sleeve could re-enter over real shares, and the
    stranded shares had no exit route (deselected exits read
    held_rows only). Dispatch-written fills always carry the tag
    (the intent reason rides the fill row — CURE13), so an
    unattributable row is a foreign/legacy record, and the only
    honest answer is fail-closed: raise, and the producer's
    unreadable-holdings path omits the held_rows key entirely,
    which the sleeve already treats as fail-closed (CURE13)."""
    held = {}
    for row in rows or []:
        if not isinstance(row, dict) or row.get("sleeve") != SLEEVE_ID:
            continue
        m = _ROW_RE.search(str(row.get("reason") or ""))
        if not m:
            if row.get("kind") in ("fill", "exit_submitted"):
                try:
                    _q = float(row.get("signed_qty")
                               if row.get("signed_qty") is not None
                               else row.get("qty") or 0)
                except (TypeError, ValueError):
                    _q = 0.0
                if _q:
                    raise ValueError(
                        "free_etf %s row without a row= tag cannot be "
                        "attributed to a book (symbol=%s qty=%s) — "
                        "held_rows reconstruction fails closed"
                        % (row.get("kind"), row.get("symbol"), _q))
            continue
        row_id = m.group(1)
        kind = row.get("kind")
        try:
            if kind == "fill":
                q = row.get("signed_qty")
                if q is None:
                    q = float(row.get("qty") or 0) * (
                        -1.0 if row.get("side") == "sell" else 1.0)
                held[row_id] = held.get(row_id, 0.0) + float(q or 0)
            elif kind == "exit_submitted":
                q = float(row.get("qty") or 0)
                cur = held.get(row_id, 0.0)
                held[row_id] = cur - q if cur >= 0 else cur + q
        except (TypeError, ValueError):
            continue
    return {k: float(v) for k, v in held.items() if v}
_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _book_symbols(books):
    syms = []
    for book in books or []:
        for s in list(book.get("fixed_weights") or {}) + list(book.get("symbols") or []):
            if s not in syms:
                syms.append(s)
    return syms


class EtfProducer:
    """fetch_books() -> [book dicts] ([] when the rulebook is absent);
    fetch_histories(symbols) -> {sym: [(session_iso, close), ...]}
    via the SIP adjustment=all door; fetch_quotes(symbols) ->
    {sym: {"t", "bp", "ap"}} via the IEX latest-quote door;
    fetch_spent(session) -> session buys USD so far;
    fetch_qqq() -> (broker_qqq_qty, attributed_others)."""

    def __init__(self, fetch_books=None, fetch_histories=None,
                 fetch_quotes=None, fetch_spent=None, fetch_qqq=None,
                 fetch_secondary=None, secondary_cache_path=None,
                 fetch_held_rows=None):
        self.fetch_books = fetch_books
        self.fetch_histories = fetch_histories
        self.fetch_quotes = fetch_quotes
        self.fetch_spent = fetch_spent
        self.fetch_qqq = fetch_qqq
        # fetch_held_rows() -> {row_id: qty} per-book holdings (the
        # run_live assembly reconstructs them from the dispatch
        # ledger via held_rows_from_records). CURE13.
        self.fetch_held_rows = fetch_held_rows
        # fetch_secondary(symbol) -> {date_iso: adj_close} (Yahoo
        # daily adj_close door; production callable in run_live).
        self.fetch_secondary = fetch_secondary
        self.secondary_cache_path = secondary_cache_path
        self._books_cache = {}    # session -> books list
        self._receipt_cache = {}  # session -> receipt dict
        self._secondary_cache = {}  # session -> scores dict | None

    def _books(self, session):
        if session not in self._books_cache:
            books = []
            if self.fetch_books is not None:
                try:
                    books = list(self.fetch_books() or [])
                except Exception:
                    books = []  # unreadable rulebook: old _books() shape
            self._books_cache[session] = books
        return self._books_cache[session]

    def _receipt(self, session, symbols):
        if session in self._receipt_cache:
            return self._receipt_cache[session]
        histories, verified = {}, False
        if symbols and self.fetch_histories is not None:
            try:
                raw = self.fetch_histories(list(symbols)) or {}
                for sym in symbols:
                    rows = [{"session": str(d)[:10], "close": float(c)}
                            for d, c in (raw.get(sym) or [])
                            if str(d)[:10] < session and c]
                    if rows:
                        histories[sym] = rows
                verified = all(sym in histories for sym in symbols)
            except Exception:
                histories, verified = {}, False
        last = None
        for rows in histories.values():
            if rows:
                last = max(last or "", rows[-1]["session"])
        receipt = {"histories": histories,
                   "source_receipts_verified": bool(verified),
                   "feed": "sip", "adjustment": "all",
                   "signal_session": last}
        self._receipt_cache[session] = receipt
        return receipt

    def _secondary(self, session, books, receipt):
        """Yahoo secondary scores for the INTERVAL_* books, per the
        old desk's _yahoo_scores (see module docstring): aligned to
        the SIP receipt sessions of the first symbol of the first
        secondary book; ANY missing/nonpositive session for ANY
        symbol -> None (the key stays absent and the books fail
        closed by name, exactly as before this product existed).
        Served only as a complete set over the secondary books'
        symbol union."""
        if session in self._secondary_cache:
            return self._secondary_cache[session]
        scores = None
        sec_books = [b for b in books or [] if b.get("secondary_provider")]
        if sec_books and self.fetch_secondary is not None:
            cache_path = self.secondary_cache_path or (
                _ROOT / "state" / "live" / "etf_secondary_scores.json")
            try:
                cached = json.loads(pathlib.Path(cache_path).read_text())
                if cached.get("session") == session \
                        and isinstance(cached.get("scores"), dict) \
                        and cached["scores"]:
                    scores = {str(k): float(v)
                              for k, v in cached["scores"].items()}
            except Exception:
                scores = None
            if scores is None:
                try:
                    symbols = []
                    for b in sec_books:
                        for s in b.get("symbols") or []:
                            if s not in symbols:
                                symbols.append(s)
                    anchor = list(sec_books[0].get("symbols") or [])
                    histories = (receipt or {}).get("histories") or {}
                    rows = histories.get(anchor[0]) if anchor else None
                    if not rows or len(rows) < 252:
                        raise ValueError("receipt anchor history short")
                    sessions = [r["session"] for r in rows[-252:]]
                    computed = {}
                    for sym in symbols:
                        series = self.fetch_secondary(sym) or {}
                        closes = [series.get(s) for s in sessions]
                        if any(c is None or float(c) <= 0 for c in closes):
                            raise ValueError(
                                f"{sym}: Yahoo series misses a SIP session")
                        computed[sym] = math.log(
                            float(closes[-1]) / float(closes[-127]))
                    scores = computed
                    try:
                        p = pathlib.Path(cache_path)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        fd, tmp = tempfile.mkstemp(
                            dir=str(p.parent), prefix=".etf-secondary-",
                            suffix=".tmp")
                        with os.fdopen(fd, "w") as fh:
                            json.dump({"session": session,
                                       "scores": scores}, fh)
                        os.replace(tmp, p)
                    except Exception:
                        pass  # disk cache is an optimization, not truth
                except Exception:
                    scores = None
        self._secondary_cache[session] = scores
        return scores

    def extra_for(self, sleeve_id, ctx):
        if sleeve_id != SLEEVE_ID:
            return {}
        books = self._books(ctx.session)
        symbols = _book_symbols(books)
        receipt = self._receipt(ctx.session, symbols)
        out = {"etf_books": books,
               "etf_receipt": receipt}
        secondary = self._secondary(ctx.session, books, receipt)
        if secondary:
            out["etf_secondary_scores"] = secondary
        quotes = {}
        if symbols and self.fetch_quotes is not None:
            try:
                raw = self.fetch_quotes(list(symbols)) or {}
                received = datetime.fromtimestamp(
                    float(ctx.now), tz=timezone.utc).isoformat()
                for sym in symbols:
                    q = raw.get(sym) or {}
                    if q.get("t") and q.get("bp") is not None and q.get("ap") is not None:
                        quotes[sym] = {"t": q["t"], "received_at": received,
                                       "bp": q["bp"], "ap": q["ap"]}
            except Exception:
                quotes = {}  # unquotable: the sleeve fails closed on it
        out["quotes"] = quotes
        if self.fetch_spent is not None:
            try:
                out["spent_usd"] = float(self.fetch_spent(ctx.session) or 0.0)
            except Exception:
                pass
        if self.fetch_qqq is not None:
            try:
                qty, others = self.fetch_qqq()
                out["broker_qqq_qty"] = float(qty or 0.0)
                out["attributed_others"] = float(others or 0.0)
            except Exception:
                pass
        if self.fetch_held_rows is not None:
            try:
                raw = self.fetch_held_rows() or {}
                out["held_rows"] = {str(k): float(v)
                                     for k, v in raw.items()
                                     if v}
            except Exception:
                # Unreadable holdings source: omit the key entirely.
                # Serving {} would lie ("nothing held") and the
                # sleeve would re-enter over real positions; with
                # the key absent the sleeve fails closed on any
                # unattributed aggregate instead (CURE13).
                pass
        return out
