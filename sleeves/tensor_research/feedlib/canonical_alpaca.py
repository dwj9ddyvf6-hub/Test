"""The research roster's canonical 1H series from Alpaca — the tensor_research hourly job's input when the desk holds
Alpaca keys, so the 1,838-name roster costs about ten batched requests an hour instead of 1,838 Yahoo requests (the
Yahoo canonical feed refetched every name's full year after each completed hour, the desk's heaviest Yahoo load).

Bars: SIP 30-minute bars (split-adjusted, the canonical feed's adjustment) aggregated onto the canonical grid of
desk/feedlib/canonical.py: regular-session hours opening 09:30 ... 15:30 ET (the 15:30 bar is the closing half-hour
stub; on an early close each half hour joins the latest canonical open at or before it), open of the first half
hour, high / low over both, close of the last, volumes summed. Completed bars only, and on the free plan an hour is
read 16 minutes after it ends (SIP data younger than 15 minutes is not served).

Named divergences from the Yahoo canonical feed (tensor_swing keeps that feed and its own cache, canonical/1h/):
the consolidated SIP tape and its volumes in place of Yahoo's hourly prints; incremental (a stored hour is not
re-read, Yahoo's between-fetch revisions are not mirrored); the 16-minute availability delay. The series lives in
canonical/1h_alpaca/, never in the Yahoo canonical cache.

Cold years: Alpaca pages a symbol's history in pieces of about three weeks whatever the batch (measured 2026-10-16:
one symbol's year of half hours = 20 requests, two symbols = 45), so a cold roster is ~20 requests a name. A name
new to this store therefore starts from the Yahoo canonical cache's hours when that cache holds them (the feed this
store reproduces; only sessions before the cache's fetch day: Yahoo revises the current day's hourly volumes, e.g.
AAPL 10:30 69.7M vs SIP 5.4M), and Alpaca fills from that day on. Each run refreshes the stored series first (cheap,
batched) and spends at most its budget on cold years, ten names a request; the index is written after every batch,
so an interrupted run resumes where it stopped. A split is caught on the overlap half hour each refresh re-reads (its
close moved by more than SPLIT_TOL): the stored series is re-based by that ratio, as the split adjustment would."""
import json
import os
import time
from datetime import datetime, timedelta, timezone

from .. import calendar as cal
from ..util import write_json_atomic
from .canonical import BAR_S, completed, session_opens

DELAY_S = 16 * 60
BATCH = 100                                   # symbols per request for a refresh (short spans share pages)
COLD_BATCH = 10                               # symbols per request for a cold year (pages are per symbol anyway)
SHORT_SPAN_S = 7 * 86400                      # a refresh; longer spans are cold loads, run within the budget
YEAR_S = 366 * 86400
SPLIT_TOL = 0.02                              # the overlap half hour's close moved more than this: a split re-based it


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def latest_available_open(now):
    """the newest canonical hour Alpaca's free SIP serves by now (it ended at least DELAY_S ago)."""
    from .canonical import latest_completed_open
    return latest_completed_open(now - DELAY_S)


def aggregate(halves):
    """SIP 30-minute bars (ascending dicts with t/o/h/l/c/v) -> canonical hours."""
    by_day = {}
    for b in halves:
        by_day.setdefault(cal._as_date(b["t"]), []).append(b)
    out = []
    for day in sorted(by_day):
        opens = [t for t in session_opens(day)]
        if not opens:
            continue
        close = cal.session_close(day)
        hours = {}
        for b in sorted(by_day[day], key=lambda x: x["t"]):
            if not (opens[0] <= b["t"] < close):
                continue
            k = max(t for t in opens if t <= b["t"])
            h = hours.get(k)
            if h is None:
                hours[k] = {"t": int(k), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
            else:
                h["h"], h["l"], h["c"], h["v"] = max(h["h"], b["h"]), min(h["l"], b["l"]), b["c"], h["v"] + b["v"]
        out += [hours[k] for k in sorted(hours)]
    return out


def _rebase(bars, r):
    """prices x r, volumes / r: the split adjustment applied to a stored series."""
    return [dict(b, o=b["o"] * r, h=b["h"] * r, l=b["l"] * r, c=b["c"] * r, v=(b.get("v") or 0) / r) for b in bars]


class AlpacaCanonical:
    """bars(sym, now) / status like canonical.Canonical; prefetch(symbols, now) first fills every symbol's series
    with batched requests (Canonical fetches one symbol at a time). Memory stays one batch: a symbol's half hours
    are written and dropped, an index keeps each series' last half hour, bars() reads one file."""

    def __init__(self, root, client):
        self.dir = os.path.join(root, "canonical", "1h_alpaca")
        self.yahoo_dir = os.path.join(root, "canonical", "1h")
        self.client = client
        self.status = {}
        self.deferred = 0
        self._index = None

    def _path(self, sym):
        return os.path.join(self.dir, sym.upper().replace("/", "_").replace(".", "_").replace("^", "") + ".json")

    def _doc(self, sym, d=None):
        try:
            with open(os.path.join(d or self.dir, os.path.basename(self._path(sym)))) as f:
                doc = json.load(f)
            return doc if isinstance(doc, dict) else {}
        except (OSError, ValueError):
            return {}

    def _read(self, sym):
        return self._doc(sym).get("halves") or []

    def index(self):
        if self._index is None:
            try:
                with open(os.path.join(self.dir, "_index.json")) as f:
                    self._index = json.load(f) or {}
            except (OSError, ValueError):
                self._index = {}
        return self._index

    def _recover(self, sym, end):
        """a name missing from the index: the series an interrupted run already wrote, else a seed from the Yahoo
        canonical cache's hours before its fetch day. Returns the index value (fetch from the next second) or None."""
        doc = self._doc(sym)
        if doc.get("halves"):
            return float(doc["halves"][-1]["t"])
        if doc.get("hours") and doc.get("cut"):
            return float(doc["cut"]) - 1
        y = self._doc(sym, self.yahoo_dir)
        bars, at = y.get("bars") or [], y.get("fetched_at")
        if not bars or not at:
            return None
        opens = session_opens(cal._as_date(float(at)))
        cut = int(opens[0]) if opens else int(float(at))
        hours = [b for b in bars if end - YEAR_S <= int(b["t"]) < cut]
        if not hours:
            return None
        os.makedirs(self.dir, exist_ok=True)
        write_json_atomic(self._path(sym), {"hours": hours, "cut": cut, "halves": [], "fetched_at": None,
                                            "seed": {"src": "yahoo canonical/1h", "fetched_at": at}})
        self.status[sym] = "seed"
        return float(cut) - 1

    def prefetch(self, symbols, now, budget_s=None):
        """one incremental fill for the roster: the stored series first (from each one's last stored half hour,
        which is re-read as the split check), grouped by start hour so a batch shares one request window; then the
        cold years (new names without a seed, a year back) while budget_s lasts (None: all). Returns the number of
        batches fetched; self.deferred counts the cold names left for the next run."""
        end = now - DELAY_S
        t0 = time.monotonic()
        idx = self.index()
        groups = {}
        for s in dict.fromkeys(x.upper() for x in symbols):
            if s not in idx:
                got = self._recover(s, end)
                if got is not None:
                    idx[s] = got
            start = float(idx[s]) if s in idx else end - YEAR_S
            if start + 3600 <= end:
                groups.setdefault(int(start // 3600), []).append(s)
        n, self.deferred = 0, 0
        for _, syms in sorted(groups.items(), reverse=True):                 # freshest first
            start = min(float(idx[s]) if s in idx else end - YEAR_S for s in syms)
            cold = end - start > SHORT_SPAN_S
            size = COLD_BATCH if cold else BATCH
            for i in range(0, len(syms), size):
                chunk = syms[i:i + size]
                if cold and budget_s is not None and time.monotonic() - t0 > budget_s:
                    self.deferred += len(chunk)
                    for s in chunk:
                        self.status[s] = "deferred"
                    continue
                try:
                    got = self.client.stock_bars(chunk, "30Min", start=_iso(start), end=_iso(end), feed="sip",
                                                 adjustment="split")
                except Exception as e:
                    for s in chunk:
                        self.status[s] = "error: %s" % str(e)[:120]
                    continue
                n += 1
                os.makedirs(self.dir, exist_ok=True)
                for s in chunk:
                    new = [{"t": _epoch(b["t"]), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                            "c": float(b["c"]), "v": float(b.get("v") or 0)} for b in got.pop(s, None) or []]
                    new = [b for b in new if b["t"] + 1800 <= end]
                    doc = self._doc(s) if s in idx else {}
                    old, hours = doc.get("halves") or [], doc.get("hours") or []
                    last = old[-1]["t"] if old else float("-inf")
                    seen = next((b for b in new if b["t"] == last), None)
                    split = seen is not None and old[-1]["c"] > 0 and abs(seen["c"] / old[-1]["c"] - 1) > SPLIT_TOL
                    if split:
                        r = seen["c"] / old[-1]["c"]
                        old, hours = _rebase(old, r), _rebase(hours, r)
                        doc["rebased"] = (doc.get("rebased") or []) + [[int(last), round(r, 8), now]]
                    add = [b for b in new if b["t"] > last]
                    if not add and not split:
                        self.status[s] = "cache" if s in idx else "empty"
                        continue
                    merged = [b for b in old + add if b["t"] >= end - YEAR_S]
                    hours = [h for h in hours if h["t"] >= end - YEAR_S]
                    if not merged and not hours:
                        self.status[s] = "empty"
                        continue
                    doc.update(halves=merged, hours=hours, fetched_at=now)
                    write_json_atomic(self._path(s), doc)
                    idx[s] = merged[-1]["t"] if merged else idx.get(s, end)
                    self.status[s] = "fetch"
                del got
                write_json_atomic(os.path.join(self.dir, "_index.json"), idx)   # an interrupted run resumes here
        return n

    def bars(self, sym, now):
        sym = sym.upper()
        doc = self._doc(sym)
        hours, halves = doc.get("hours") or [], doc.get("halves") or []
        if not hours and not halves:
            self.status.setdefault(sym, "empty")
            return []
        out = aggregate(halves)
        if hours:
            cut = doc.get("cut") or hours[-1]["t"] + 1
            out = hours + [h for h in out if h["t"] >= cut]
        return completed(out, now - DELAY_S)
