"""qr_spectral_echo_drift -- Spectral Echo Drift, SED (quant-research-critical@0be4c575
research/2026-10-10-spectral-echo-drift: engine.py, vendored byte-exact under desk/vendor/quant_research/sed/, with its
README.md and research_note.md). The source is a research package: no economic run, its inputs absent.

The rule (engine.build_features + engine.event_backtest, model "core"). Over each symbol's regular-session book,
every 12th valid update's near-touch weighted depth imbalance is averaged per minute beside the minute's mid open /
high / low / close. Per minute: return_1m and return_3m over contiguous minutes, atr_20 (true range of the mid, 20
rows), the Katz fractal dimension of the last 32 mid closes, the latest confirmed fractal low, and over the last 128
contiguous minutes the multi-taper coherence of imbalance and returns at the three strongest 2-20-minute peaks, the
band's spectral entropy and the lead (0-5 bars) of returns over imbalance changes. signal_core = coherence > 0.82,
lag 2-5 with correlation >= 0.10, entropy falling twice, imbalance > 0, return_3m > 0. Replay: one long position at
a time; per minute only the strongest-coherence candidate, signals known before 15:50; entry at the first book update
250 ms after the minute (refused when it is more than 1 s late); stop = max(fractal low - 0.1 ATR,
mid - (1 + 0.75 (D - 1)) ATR); size = min(0.4% NAV / (ask - stop), 10% NAV / ask, 5% of the displayed ask depth);
exits: the bid touching the stop, coherence < 0.65, 30 minutes, 15:55; no entry once the day's loss reaches 1.2% of
the day's starting NAV.

Model "core": the research note's own rule when X arrival times are unavailable ("run the market-only ablation and
mark the combined strategy untested"). The social model's point-in-time X post stream is a paid feed; the free
public substitute (Stocktwits' symbol stream, 30 messages a request at 200 requests an hour) cannot observe arrivals
per minute for the universe, so attention_z (the social gate) is not computed.

Removed gates (desk posture, README "Desk posture"): the Tensor 10m/1H timing confirmation and the independent risk
approval between the candidate and the paper order.

Named divergences:
  1. the book: IEX's top of book from Alpaca's quote stream (/v2/stocks/quotes, feed=iex: every update, read through
     one second before each desk pass) -- the note's venue-specific option (i) -- instead of a top-10 market-by-price
     feed (paid). Levels 1-9 are absent: the imbalance is the touch term of weighted_imbalance (a constant rescaling
     of it: sign, coherence and lead correlations unchanged) and the depth cap is 5% of the displayed IEX ask size
     (SIZE_UNIT shares per reported size unit: 1, the stream's sizes read as shares -- the cap can only be too tight
     if they are round lots, never too loose);
  2. the stream has no sequence numbers: updates are ordered as it returns them (time order), and the
     duplicate-sequence check has nothing to check;
  3. universe: 20 liquid Nasdaq names fixed at port time (the note's "liquid Nasdaq names" stratum; no point-in-time
     member list in the source); the small/micro-cap stratum is not run (IEX quotes too sparse for 128 contiguous
     minutes);
  4. timing: a minute's candidate is acted on at the first desk pass (every 30 s) after the tape covers its entry
     update, not 250 ms after the minute: the entry is an IOC limit at the replay's fill price (the ask of that
     update; the replay's order, at most 5% of the displayed size, fills there), so a market that moved away refuses
     the entry like the replay's incomplete fill; a candidate first seen more than 3 minutes late (a tape outage, a
     restart) is logged, not traded. In sim a crossing order pays IEX's mid + max(5 bp, the name's NBBO half-spread)
     (desk/venues/sim.py equity_touch), and a limit fills at its own price wherever the estimated real NBBO ask (the
     measured half-spread, or IEX's own quote when unmeasured) is at or below it: in a tight book the IOC at the
     replay's ask fills at that ask, as the replay's order did; a paper order meets the broker's own book;
  5. exits are decided on the tape (every trigger known through the tape's end, so the earliest is exact) and routed
     at that pass as market orders at the desk's quote; a stalled tape cannot hold a position more than a minute
     past its clock exit (30 minutes / 15:55);
  6. NAV is the sleeve's desk equity (the desk's fee model), not the replay's 2.5 bp a side ledger; the daily-loss
     brake reads its change since the session's first candidate;
  7. history: the features carry the previous taped session (the replay carries every session of its input file);
     the first session the sleeve tapes starts its rolling ATR and fractal lows there.

The tape's reads (not a rule): every read of the stream spans at most two minutes, narrowed after a read that
overruns the stream's 50 pages of 10,000 quotes and widened back as reads stay small; the new quotes are read first,
then a reloaded tape's last 40 minutes of raw updates newest first, and the previous session's tape (minute records
only) to its close, from 09:45 ET (not in the open's heavy passes), all inside one 8-second budget a pass; the feed
is prefilled beside the pass's other reads. Until
2026-10-26 a reloaded tape refilled its 40 minutes in one read before anything new: more than 50 pages for 20 names,
so the tape never moved and the sleeve decided nothing (10-19..10-23).

Parity: tools/parity/qr_sed.py -> docs/receipts/parity/qr_sed.json (the source's feature builder and core replay vs
the tape, the features and this sleeve driven pass by pass, on randomized top-of-book streams)."""
import json
import math
import os
import time
from datetime import datetime, time as dtime, timezone

import numpy as np

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from .r10 import ET

SID = "qr_spectral_echo_drift"
LANE = "research/2026-10-10-spectral-echo-drift/"
SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT, "path": LANE + "engine.py",
          "blob_sha": "95d5f34ff2eb64087e0c12ff0a16f6e8cb52b565", "line_start": 1, "line_end": 695,
          "readme": LANE + "README.md", "research_note": LANE + "research_note.md"}
UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX", "PLTR", "MU", "COST",
            "INTC", "QCOM", "AMAT", "ADBE", "CSCO", "PEP", "LRCX")
NS = 1_000_000_000
MIN_NS = 60 * NS
WINDOW_NS = 120 * NS              # one stream read covers at most two minutes
MIN_WINDOW_NS = NS                # a read narrowed to one second that still overruns is an error
BUDGET_S = 8.0                    # catch-up reads per pass
LAG_NS = NS                       # the stream is read through one second before the pass
RAW_KEEP_NS = 40 * MIN_NS         # raw updates kept for entry updates and stop touches (the hold is 30 minutes)
LATE_NS = 180 * NS
STALL_NS = 60 * NS
CUTOFF, EOD = dtime(15, 50), dtime(15, 55)
BULK_FROM = dtime(9, 45)          # the previous session's catch-up (bulk) waits out the open's heavy passes
TAPE_DIR = "qr_sed"
MAX_PAGES = 50
PAGE = 10_000                     # quotes a stream page holds (the request's limit)
SIZE_UNIT = 1                     # shares per unit of the stream's bid / ask sizes


def E():
    from ...vendor.quant_research.sed import engine
    return engine


_CFG = []


def config():
    if not _CFG:
        _CFG.append(E().Config())
    return _CFG[0]


# ------------------------------------------------------------------------------------------------------ the tape
_MIN = {}


def parse_ns(s):
    """RFC 3339 UTC (Alpaca: up to nanoseconds, 'Z') -> integer epoch nanoseconds."""
    base = _MIN.get(s[:16])
    if base is None:
        if len(_MIN) > 20_000:
            _MIN.clear()
        base = _MIN[s[:16]] = int(datetime.strptime(s[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
                                  .timestamp()) * NS
    rest = s[19:].rstrip("Z")
    frac = int(rest[1:10].ljust(9, "0")) if rest.startswith(".") else 0
    return base + int(s[17:19]) * NS + frac


def iso_ns(ns):
    return datetime.fromtimestamp(ns // NS, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + f".{ns % NS:09d}Z"


def et_ns(day, hh, mm):
    return int(round(datetime.combine(cal._as_date(day), dtime(hh, mm), ET).timestamp())) * NS


def valid_row(q, lo, hi):
    """engine._clean_book on one top-of-book update: the regular session (09:30 <= ET < 16:00), positive prices, an
    uncrossed and unlocked touch, non-negative sizes -> (t_ns, bid, bid size, ask, ask size) or None."""
    try:
        t = q["t"] if isinstance(q["t"], int) else parse_ns(q["t"])
        bp, bs, ap, az = float(q["bp"]), float(q["bs"]), float(q["ap"]), float(q["as"])
    except (KeyError, TypeError, ValueError):
        return None
    if not lo <= t < hi or not all(math.isfinite(v) for v in (bp, bs, ap, az)):
        return None
    if bp <= 0 or ap <= 0 or ap <= bp or bs < 0 or az < 0:
        return None
    return t, bp, bs, ap, az


def touch_imbalance(bid_size, ask_size):
    """engine.weighted_imbalance on a book whose levels 1-9 are empty (the IEX touch only)."""
    b = np.zeros((1, 10))
    a = np.zeros((1, 10))
    b[0, 0], a[0, 0] = bid_size, ask_size
    return float(E().weighted_imbalance(b, a)[0])


class Tape:
    """one session's IEX top-of-book tape: the valid updates folded into the source's minute records (mid open /
    high / low / close, update count, and the mean -- pandas' compensated group mean -- of every 12th valid update's
    imbalance, counted per symbol and session), plus the recent raw updates."""

    def __init__(self, session):
        self.session = cal._as_date(session).isoformat()
        self.lo, self.hi = et_ns(self.session, 9, 30), et_ns(self.session, 16, 0)
        self.through = self.lo            # read through this instant (exclusive)
        self.count = {}                   # valid updates per symbol so far
        self.partial = {}                 # the forming minute per symbol
        self.minutes = {}                 # closed minute records per symbol, in time order
        self.raw = {}                     # symbol -> list of (t int64 array, values (k, 4): bid, bid size, ask, ask size)
        self.raw_from = self.lo           # raw updates are complete from here (a reloaded tape refills them)
        self.win = WINDOW_NS              # the span of the next stream read of new quotes (narrowed after an overrun)
        self.rwin = WINDOW_NS             # ... and of the raw refill's next read (its own: a refill never narrows the new)
        self.refill_failed = False        # a refill that overran at one second: the raw updates stay from raw_from
        self.dirty = False

    # -- folding
    def ingest(self, sym, rows, aggregate=True, front=False):
        if rows:
            chunk = (np.array([r[0] for r in rows], dtype=np.int64), np.array([r[1:] for r in rows], dtype=float))
            chunks = self.raw.setdefault(sym, [])
            chunks.insert(0, chunk) if front else chunks.append(chunk)
        if not aggregate:
            return
        k = self.count.get(sym, 0)
        p = self.partial.get(sym)
        for t, bp, bs, ap, az in rows:
            m = t - t % MIN_NS
            if p is not None and p["m"] != m:
                self._close(sym, p)
                p = None
            mid = (bp + ap) / 2.0
            if p is None:
                p = self.partial[sym] = {"m": m, "o": mid, "h": mid, "l": mid, "c": mid, "n": 0, "s": 0.0, "k": 0.0,
                                         "ns": 0, "bc": bp, "ac": ap}
            else:
                p["h"] = max(p["h"], mid)
                p["l"] = min(p["l"], mid)
                p["c"] = mid
            p["bc"], p["ac"] = bp, ap
            p["n"] += 1
            if k % 12 == 0:                                       # every 12th valid update of the session
                y = touch_imbalance(bs, az) - p["k"]
                tt = p["s"] + y
                p["k"] = tt - p["s"] - y
                if p["k"] != p["k"]:
                    p["k"] = 0.0
                p["s"] = tt
                p["ns"] += 1
            k += 1
        self.count[sym] = k

    def _close(self, sym, p):
        self.minutes.setdefault(sym, []).append(
            {"m": p["m"], "o": p["o"], "h": p["h"], "l": p["l"], "c": p["c"], "n": p["n"], "ns": p["ns"],
             "imb": p["s"] / p["ns"] if p["ns"] else None, "bc": p["bc"], "ac": p["ac"]})
        self.partial.pop(sym, None)

    def close_through(self, t):
        for sym, p in list(self.partial.items()):
            if p["m"] + MIN_NS <= t:
                self._close(sym, p)

    # -- reading the stream
    def advance(self, read, symbols, now_ns, budget_s=BUDGET_S, raw=True):
        """read(symbols, start_ns, end_ns) -> {symbol: [quote dicts]} for [start, end); folds every complete window.
        Every read spans at most self.win (two minutes; halved after a read that overruns the stream's pages, doubled
        back while reads stay under a quarter of them), so no read is larger than the stream serves. The new quotes
        come first; then (raw) the recent raw updates a reloaded tape lacks, newest first, each window prepended as
        it arrives (raw_from: complete from there); both stop at the budget and go on at the next call."""
        end = min(now_ns - LAG_NS, self.hi)
        t0 = time.monotonic()
        while self.through < end and time.monotonic() - t0 < budget_s:
            stop = min(end, self.through + self.win)
            got = self._read(read, symbols, self.through, stop, "win")
            if got is None:
                continue                                          # narrowed: the same start, a shorter window
            for s in symbols:
                self.ingest(s, self._rows(got.get(s)))
            self.through = stop
            self.close_through(stop)
            self.dirty = True
        self.prune()
        a = max(self.lo, self.through - RAW_KEEP_NS)
        while raw and not self.refill_failed and self.raw_from > a and time.monotonic() - t0 < budget_s:
            start = max(a, self.raw_from - self.rwin)             # a reloaded tape: refill the recent raw updates
            try:
                got = self._read(read, symbols, start, self.raw_from, "rwin")
            except Overrun:
                self.refill_failed = True                         # entries before raw_from log no_raw_updates
                raise
            if got is None:
                continue
            for s in symbols:
                self.ingest(s, self._rows(got.get(s)), aggregate=False, front=True)
            self.raw_from = start
        return self

    def _read(self, read, symbols, a, b, which):
        """one read of [a, b); None after an overrun (the window `which` is halved; one second that overruns is an
        error). A read that filled under a quarter of the pages widens the window back (to two minutes at most)."""
        try:
            got = read(list(symbols), a, b)
        except Overrun:
            if b - a <= MIN_WINDOW_NS:
                raise
            setattr(self, which, max(MIN_WINDOW_NS, (b - a) // 2))
            return None
        if sum(len(v or ()) for v in got.values()) * 4 <= PAGE * MAX_PAGES and b - a >= getattr(self, which):
            setattr(self, which, min(WINDOW_NS, getattr(self, which) * 2))
        return got

    def _rows(self, quotes):
        rows = [v for v in (valid_row(q, self.lo, self.hi) for q in quotes or []) if v]
        rows.sort(key=lambda r: r[0])                              # stable: stream order within a timestamp
        return rows

    def prune(self):
        """raw updates older than RAW_KEEP_NS before the tape's end are dropped (raw_from moves with them)."""
        cut = self.through - RAW_KEEP_NS
        if cut <= self.raw_from:
            return
        for s, chunks in self.raw.items():
            while chunks and (not len(chunks[0][0]) or chunks[0][0][-1] < cut):
                chunks.pop(0)
            if chunks and chunks[0][0][0] < cut:
                t, v = chunks[0]
                i = int(np.searchsorted(t, cut, side="left"))
                chunks[0] = (t[i:], v[i:])
        self.raw_from = cut

    def raw_rows(self, sym):
        """(t, values) of the kept raw updates of `sym` (complete from self.raw_from)."""
        ch = self.raw.get(sym) or []
        if not ch:
            return np.zeros(0, dtype=np.int64), np.zeros((0, 4))
        if len(ch) > 1:
            ch[:] = [(np.concatenate([c[0] for c in ch]), np.concatenate([c[1] for c in ch]))]
        return ch[0]

    def records(self, sym):
        return list(self.minutes.get(sym) or [])

    # -- persistence (a restart resumes the folding; the raw updates are re-read)
    def save(self, root):
        if not root or not self.dirty:
            return
        d = os.path.join(root, "cache", TAPE_DIR)
        os.makedirs(d, exist_ok=True)
        doc = {"session": self.session, "through": self.through, "count": self.count, "partial": self.partial,
               "minutes": self.minutes}
        tmp = os.path.join(d, self.session + ".json.tmp")
        with open(tmp, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        os.replace(tmp, os.path.join(d, self.session + ".json"))
        self.dirty = False
        keep = sorted(n for n in os.listdir(d) if n.endswith(".json"))[-5:]
        for n in os.listdir(d):
            if n.endswith(".json") and n not in keep:
                try:
                    os.remove(os.path.join(d, n))
                except OSError:
                    pass

    @classmethod
    def load(cls, root, session):
        t = cls(session)
        try:
            doc = json.load(open(os.path.join(root, "cache", TAPE_DIR, t.session + ".json")))
        except (OSError, ValueError, TypeError):
            return None
        t.through, t.count = int(doc["through"]), {k: int(v) for k, v in doc["count"].items()}
        t.partial, t.minutes = doc.get("partial") or {}, doc.get("minutes") or {}
        t.raw_from = t.through
        return t


# --------------------------------------------------------------------------------------------------- the features
def features(recs, cache=None, since=None):
    """engine.build_features' per-symbol block, the columns the core model reads, over minute records in time order
    (minutes without a sampled update are dropped, as the source's inner merge drops them). The rolling, shifted and
    forward-filled columns run over every record given (the source: every row of its input); the fractal dimension
    and the spectral statistics are computed for rows from `since` on (None: all), memoised in `cache` by minute."""
    import pandas as pd
    K = E()
    cfg = config()
    rows = [r for r in recs if r["ns"] > 0]
    if not rows:
        return []
    cache = {} if cache is None else cache
    m = np.array([r["m"] for r in rows], dtype=np.int64)
    g = pd.DataFrame({"mid_high": [r["h"] for r in rows], "mid_low": [r["l"] for r in rows],
                      "mid_close": [r["c"] for r in rows], "imbalance": [r["imb"] for r in rows]})
    minute_delta = pd.Series(m).diff().div(MIN_NS)
    contiguous = minute_delta.eq(1)
    g["return_1m"] = np.log(g["mid_close"] / g["mid_close"].shift(1)).where(contiguous)
    contiguous_3m = minute_delta.eq(1) & minute_delta.shift(1).eq(1) & minute_delta.shift(2).eq(1)
    g["return_3m"] = np.log(g["mid_close"] / g["mid_close"].shift(3)).where(contiguous_3m)
    prev = g["mid_close"].shift(1)
    true_range = pd.concat([g["mid_high"] - g["mid_low"], (g["mid_high"] - prev).abs(), (g["mid_low"] - prev).abs()],
                           axis=1).max(axis=1)
    g["atr_20"] = true_range.rolling(20, min_periods=20).mean()
    low = g["mid_low"]
    pivot = low.where((low < low.shift(1)) & (low < low.shift(2)) & (low < low.shift(-1)) & (low < low.shift(-2)))
    g["fractal_low"] = pivot.shift(2).ffill()
    n = len(g)
    first = 0 if since is None else int(np.searchsorted(m, since, side="left"))
    cont = contiguous.to_numpy()
    closes = g["mid_close"].to_numpy()
    imb = g["imbalance"].to_numpy(dtype=float)
    r1 = g["return_1m"].to_numpy()
    fd = np.full(n, np.nan)
    stats = [None] * n
    w = cfg.window_minutes
    for i in range(first, n):
        key = int(m[i])
        hit = cache.get(key)
        if hit is not None and hit[0] == (int(m[i - 31]) if i >= 31 else None) and hit[1] == (
                int(m[i - w + 1]) if i >= w - 1 else None):
            fd[i], stats[i] = hit[2], hit[3]
            continue
        if i >= 31 and cont[i - 30:i + 1].all():
            fd[i] = K._katz_dimension(closes[i - 31:i + 1])
        if i >= w - 1:
            s0 = i - w + 1
            if np.all(np.diff(m[s0:i + 1]) == MIN_NS) and not np.isnan(r1[s0:i + 1]).any():
                st = K._spectral_stats(imb[s0:i + 1], r1[s0:i + 1], cfg)
                stats[i] = {k: st[k] for k in ("coherence", "entropy", "lag_bars", "lag_corr")}
        cache[key] = (int(m[i - 31]) if i >= 31 else None, int(m[i - w + 1]) if i >= w - 1 else None, fd[i],
                      stats[i])
    nan = float("nan")
    coh = np.array([s["coherence"] if s else nan for s in stats], dtype=float)
    ent = pd.Series([s["entropy"] if s else nan for s in stats], dtype=float)
    lag = np.array([s["lag_bars"] if s else nan for s in stats], dtype=float)
    lcor = np.array([s["lag_corr"] if s else nan for s in stats], dtype=float)
    falling = ((ent < ent.shift(1)) & (ent.shift(1) < ent.shift(2))).fillna(False).to_numpy()
    sig = ((coh > cfg.coherence_enter) & (lag >= cfg.min_lag) & (lag <= cfg.max_lag) & (lcor >= cfg.min_lag_corr)
           & falling & (imb > 0) & (g["return_3m"].to_numpy() > 0))
    out = []
    atr, flow, ret3 = g["atr_20"].to_numpy(), g["fractal_low"].to_numpy(), g["return_3m"].to_numpy()
    for i in range(first, n):
        out.append({"minute": int(m[i]), "known_at": int(m[i]) + MIN_NS, "mid_close": float(closes[i]),
                    "imbalance": float(imb[i]), "return_1m": float(r1[i]), "return_3m": float(ret3[i]),
                    "atr_20": float(atr[i]), "fractal_dim": float(fd[i]), "fractal_low": float(flow[i]),
                    "coherence": float(coh[i]), "entropy": float(ent.iloc[i]), "lag_bars": float(lag[i]),
                    "lag_corr": float(lcor[i]), "entropy_falling": bool(falling[i]), "signal_core": bool(sig[i])})
    return out


# -------------------------------------------------------------------------------------------- the replay's choices
def et_clock(ns):
    return datetime.fromtimestamp(ns / NS, tz=ET)


def best(rows):
    """event_backtest's one candidate per minute: the highest coherence, then (every core row's attention_z is 0)
    the symbol."""
    return sorted(rows, key=lambda r: (-r["coherence"], r["symbol"]))[0]


def first_at_or_after(t, due, start=0):
    return max(int(np.searchsorted(t, due, side="left")), start)


def entry_plan(sig, t, v, nav):
    """event_backtest's entry for the candidate `sig` against the symbol's session updates (t, v): (plan, None) or
    (None, reason). The displayed depth is the touch: the size is capped at 5% of it, so the replay's book walk
    fills the whole order at the ask."""
    cfg = config()
    due = sig["known_at"] + cfg.latency_ms * 1_000_000
    i = first_at_or_after(t, due)
    if i >= len(t):
        return None, "no_entry_update"
    if (int(t[i]) - due) / 1e9 * 1000 > cfg.max_book_staleness_ms:
        return None, "stale_book"
    bid, _, ask, ask_size = (float(x) for x in v[i])
    mid = (bid + ask) / 2.0
    stop = E()._stop_price(sig, mid, cfg)
    if not np.isfinite(stop) or stop >= mid:
        return None, "no_stop"
    risk_budget = nav * cfg.risk_fraction
    risk_shares = math.floor(risk_budget / max(ask - stop, cfg.tick_size))
    notional_shares = math.floor(nav * cfg.max_notional_fraction / ask)
    depth_shares = math.floor(max(0, int(ask_size)) * SIZE_UNIT * cfg.max_book_participation)
    requested = min(risk_shares, notional_shares, depth_shares)
    if requested <= 0:
        return None, "size"
    vwap = (requested * ask) / requested
    if vwap - stop <= 0:
        return None, "risk"
    capped = math.floor(risk_budget / (vwap - stop))
    if capped < requested:
        requested = capped
        if requested <= 0:
            return None, "risk"
        vwap = (requested * ask) / requested
    return {"i": i, "t": int(t[i]), "mid": mid, "ask": ask, "vwap": vwap, "stop": float(stop), "shares": int(requested),
            "risk_budget": risk_budget}, None


def clock_exits(signal_t):
    cfg = config()
    eod = int(round(datetime.combine(et_clock(signal_t).date(), EOD, ET).timestamp())) * NS
    return [(signal_t + cfg.max_hold_minutes * MIN_NS, "time_stop"), (eod, "session_close")]


def after_entry(t, pos):
    """the index of the first update after the replay's entry update (a refilled tape may start after it)."""
    k = first_at_or_after(t, pos["entry_due"])
    return k + 1 if k < len(t) and int(t[k]) == pos["entry_t"] else k


def exit_trigger(pos, frows, t, v, horizon):
    """event_backtest's earliest exit for an open position -- the first later minute with coherence < 0.65, the time
    stop, 15:55 and the first update after the entry update with the bid at or below the stop -- among the triggers
    at or before `horizon` (ns): (t_ns, reason) or None."""
    cfg = config()
    cands = []
    for r in frows:
        if r["known_at"] > pos["signal_t"] and r["coherence"] < cfg.coherence_exit:
            cands.append((r["known_at"], "coherence_collapse"))
            break
    cands += clock_exits(pos["signal_t"])
    trig = [min(cands, key=lambda c: c[0])]
    k = after_entry(t, pos)
    hits = np.flatnonzero(v[k:, 0] <= pos["stop"]) if k < len(t) else []
    if len(hits):
        trig.append((int(t[k + hits[0]]), "fractal_vol_stop"))
    when, why = min(trig, key=lambda c: c[0])
    return (when, why) if when <= horizon else None


def exit_update(t, pos, when):
    """the replay's exit update: the first after the entry update at or after the trigger + 250 ms (its time is the
    replay's busy_until); None while the tape has not reached it."""
    j = first_at_or_after(t, when + config().latency_ms * 1_000_000, start=after_entry(t, pos))
    return j if j < len(t) else None


# ----------------------------------------------------------------------------------------------------- the feed
_TAPES = {}
_PREV = {}
# reads that ran out of pages, by the request's identity (symbols, start, end): a window of the past only gains quotes,
# so the same read fails the same way, and it is refused at once instead of being paged again. A reloaded tape refills
# 40 minutes of raw updates in one read (Tape.load), and 20 names' IEX quotes overrun 50 pages of 10,000 there and in
# the open's catch-up windows; every pass then paged the same read again, 17-95 s each (17,508 s in the record, 44.9 s
# and 17.1 s of the 2026-10-22 and 10-23 opening passes), while the tape and the decisions stayed where they were.
_OVERRUN = {}


class Overrun(RuntimeError):
    """a read whose quotes fill more than MAX_PAGES pages (Tape.advance narrows its window and reads again)"""


def fetch(hub, symbols, start_ns, end_ns):
    """Alpaca's IEX quote stream for [start, end): {symbol: [quote dicts in stream order]} (every page)."""
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    if client is None or not hasattr(client, "_get"):
        raise RuntimeError("Alpaca market data unavailable (the IEX quote stream needs the desk's data client)")
    key = (tuple(symbols), int(start_ns), int(end_ns))
    if key in _OVERRUN:
        raise Overrun("IEX quote stream: page limit reached")
    from ...venues.alpaca import DATA
    out, token = {}, None
    for _ in range(MAX_PAGES):
        r = client._get("/v2/stocks/quotes", {"symbols": ",".join(symbols), "start": iso_ns(start_ns),
                                              "end": iso_ns(end_ns - 1), "feed": "iex", "limit": PAGE,
                                              "sort": "asc", "page_token": token}, host=DATA) or {}
        for s, rows in (r.get("quotes") or {}).items():
            out.setdefault(s, []).extend(rows)
        token = r.get("next_page_token")
        if not token:
            return out
    if len(_OVERRUN) >= 256:
        _OVERRUN.clear()
    _OVERRUN[key] = time.time()
    raise Overrun("IEX quote stream: page limit reached")


def tape_for(root, session):
    key = (root, session)
    tape = _TAPES.get(key)
    if tape is None:
        tape = (Tape.load(root, session) if root else None) or Tape(session)
        _TAPES.clear()
        _TAPES[key] = tape
    return tape


def previous_records(root, session, read=None, symbols=(), budget_s=BUDGET_S):
    """the previous taped session's minute records (the features' carry); a tape the last pass left short of 16:00
    is read to the close first, inside the pass's remaining budget (its raw updates are not refilled: positions
    never carry overnight, and only the minute records are read)."""
    key = (root, session)
    if key not in _PREV:
        prev = cal.prev_trading_day(session).isoformat()
        t = Tape.load(root, prev) if root else None
        if t is not None and t.through < t.hi and read is not None:
            t.advance(read, symbols, t.hi + LAG_NS, budget_s=budget_s, raw=False)
            t.save(root)
        if t is not None and t.through < t.hi:
            return t.minutes                                     # retried at the next pass
        _PREV.clear()
        _PREV[key] = (t.minutes if t else {})
    return _PREV[key]


def feed_tape(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    day = cal._as_date(now).isoformat()
    if not C.is_session(day):
        return None
    tape = tape_for(root, day)
    syms = list(getattr(getattr(s, "CONFIG", None), "universe", None) or UNIVERSE)

    def read(sy, a, b):
        return fetch(f.hub, sy, a, b)
    err, prev = None, {}
    t0 = time.monotonic()
    try:
        tape.advance(read, syms, int(now * NS))
        bulk = datetime.fromtimestamp(now, tz=ET).time() >= BULK_FROM     # before 09:45 ET only today's new quotes
        prev = previous_records(root, day, read, syms,
                                budget_s=max(0.0, BUDGET_S - (time.monotonic() - t0)) if bulk else 0.0)
    except Exception as e:                    # the tape keeps what it read; the sleeve still manages its exits
        err = f"{type(e).__name__}: {str(e)[:160]}"
    finally:
        tape.save(root)
    return {"tape": tape, "prev": prev, "error": err}


# ---------------------------------------------------------------------------------------------------- the sleeve
class SED(Sleeve):
    def __init__(self):
        self.engine = None
        self._cache = {}
        cfg = config()
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=30, universe=UNIVERSE, capital=float(cfg.starting_nav),
            schedule="rth", needs={"feeds": ["qr_sed_tape"], "quotes": {"source": "equity"}},
            params={"model": "core", "book": "IEX top of book (Alpaca quote stream)", "coherence_enter":
                    cfg.coherence_enter, "coherence_exit": cfg.coherence_exit, "lag": [cfg.min_lag, cfg.max_lag],
                    "risk_fraction": cfg.risk_fraction, "max_notional_fraction": cfg.max_notional_fraction,
                    "max_book_participation": cfg.max_book_participation, "max_hold_minutes": cfg.max_hold_minutes,
                    "max_daily_loss_fraction": cfg.max_daily_loss_fraction, "latency_ms": cfg.latency_ms},
            source=SOURCE, state_schema={"session": "str", "seen": "int|None", "pos": "dict|None",
                                         "closing": "list", "busy_until": "int|None", "day": "str",
                                         "day_nav": "float", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book):
        return list(self.CONFIG.universe)

    def _features(self, tape, prev):
        out = {}
        for sym in self.CONFIG.universe:
            recs = list(prev.get(sym) or []) + tape.records(sym)
            cache = self._cache.setdefault((tape.session, sym), {})
            out[sym] = features(recs, cache, since=tape.lo)
        for k in [k for k in self._cache if k[0] != tape.session]:
            self._cache.pop(k)
        return out

    def _log(self, st, **rec):
        st["log"] = (st["log"] + [rec])[-200:]

    def signal(self, view):
        cfg = config()
        st = dict(view.state or {})
        st["log"] = list(st.get("log") or [])
        st["closing"] = [dict(c) for c in st.get("closing") or []]
        self._st = st
        now, day = float(view.now), view.session
        if not cal.is_rth(now):
            return []
        now_ns = int(now * NS)
        doc = (view.extra or {}).get("qr_sed_tape") or {}
        tape = doc.get("tape")
        if doc.get("error"):
            self._log(st, at=now, decision="tape_error", error=doc["error"])
        if st.get("session") != day:
            st.update(session=day, seen=None, busy_until=None)
        if tape is not None and st.get("seen") is None:
            st["seen"] = max(tape.lo, tape.through - tape.through % MIN_NS)      # from now on: no replay of the past
        feats = self._features(tape, doc.get("prev") or {}) if tape is not None else {}
        empty = (np.zeros(0, dtype=np.int64), np.zeros((0, 4)))
        held = C.held(view)
        pending = {p.get("signal_key") for p in (view.extra or {}).get("pending_orders") or []}
        nav = C.nav(view)
        out = []
        # the active trade
        pos = st.get("pos")
        if pos and pos.get("session") != day:                   # never carried: the replay flattens each session
            pos.update(status="exiting", why="session_close", trigger=None)
        if pos and pos["status"] == "entering":
            if held.get(pos["sym"], 0.0) > 1e-9:
                pos["status"] = "open"
            elif pos["key"] not in pending and now > pos["since"]:
                self._log(st, at=now, sym=pos["sym"], known_at=pos["signal_t"], decision="entry_unfilled")
                pos = st["pos"] = None
        if pos and pos["status"] == "open":
            if held.get(pos["sym"], 0.0) <= 1e-9:
                self._log(st, at=now, sym=pos["sym"], known_at=pos["signal_t"], decision="position_gone")
                pos = st["pos"] = None
            else:
                t, v = tape.raw_rows(pos["sym"]) if tape is not None else empty
                trig = exit_trigger(pos, feats.get(pos["sym"]) or [], t, v, tape.through) if tape is not None \
                    else None
                if trig is None:                                 # a stalled tape: the clock exits still bind
                    late = [c for c in clock_exits(pos["signal_t"]) if c[0] + STALL_NS <= now_ns]
                    trig = min(late, key=lambda c: c[0]) if late else None
                if trig:
                    pos.update(status="exiting", why=trig[1], trigger=trig[0])
        if pos and pos["status"] == "exiting":
            st["closing"].append(pos)
            pos = st["pos"] = None
        # closing trades: the replay's busy_until (its exit update), the exit until flat
        for c in list(st["closing"]):
            if c.get("busy_until") is None and c.get("trigger") is not None and tape is not None:
                t, _ = tape.raw_rows(c["sym"])
                j = exit_update(t, c, c["trigger"])
                if j is not None:
                    c["busy_until"] = int(t[j])
            if held.get(c["sym"], 0.0) <= 1e-9:
                st["closing"].remove(c)
                st["busy_until"] = max(int(st.get("busy_until") or 0), int(c.get("busy_until") or now_ns))
                self._log(st, at=now, sym=c["sym"], known_at=c["signal_t"], decision="exit", why=c.get("why"))
            else:
                out.append(Intent("exit", c["sym"], signal_key=c["key"] + ":exit", reason=f"{SID} {c.get('why')}",
                                  order=OrderSpec(type="market", window_s=300)))
        if tape is None:
            return out
        # candidates, minute by minute, as the replay meets them
        horizon = tape.through
        lat = cfg.latency_ms * 1_000_000
        stale = cfg.max_book_staleness_ms * 1_000_000
        by_minute = {}
        for sym, rows in feats.items():
            for r in rows:
                if st["seen"] < r["known_at"] <= horizon:
                    by_minute.setdefault(r["known_at"], []).append(dict(r, symbol=sym))
        for ka in sorted(by_minute):
            cands = [r for r in by_minute[ka] if r["signal_core"] and et_clock(ka).time() < CUTOFF]
            if not cands:
                st["seen"] = ka
                continue
            if ka + lat + stale > horizon:
                break                                            # its entry update cannot be judged yet
            sig = best(cands)
            sym = sig["symbol"]
            rec = {"at": now, "sym": sym, "known_at": ka, "coherence": sig["coherence"]}
            if st.get("pos") is not None or any(c.get("busy_until") is None or ka + lat < c["busy_until"]
                                                for c in st["closing"]) or ka + lat < int(st.get("busy_until") or 0):
                st["seen"] = ka
                if st.get("day") != day:
                    st.update(day=day, day_nav=nav)
                self._log(st, decision="busy", **rec)
                continue
            if st["closing"]:
                break                                            # the replay's book is flat: size on it next pass
            st["seen"] = ka
            if st.get("day") != day:
                st.update(day=day, day_nav=nav)
            if nav - float(st["day_nav"]) <= -cfg.max_daily_loss_fraction * float(st["day_nav"]):
                self._log(st, decision="daily_loss", **rec)
                continue
            if ka < now_ns - LATE_NS:
                self._log(st, decision="late", **rec)
                continue
            if ka + lat < tape.raw_from:
                self._log(st, decision="no_raw_updates", **rec)
                continue
            t, v = tape.raw_rows(sym)
            plan, why = entry_plan(sig, t, v, nav)
            if plan is None:
                self._log(st, decision=why, **rec)
                continue
            cap = round(plan["ask"], 4)
            key = f"sed:{day}:{sym}:{ka}"
            st["pos"] = {"sym": sym, "session": day, "status": "entering", "since": now, "signal_t": ka, "key": key,
                         "entry_due": ka + lat, "entry_t": plan["t"], "stop": plan["stop"], "shares": plan["shares"],
                         "ask": plan["ask"]}
            self._log(st, decision="enter", shares=plan["shares"], stop=plan["stop"], ask=plan["ask"], **rec)
            out.append(Intent("enter", sym, side="long", qty=float(plan["shares"]), price_hint=plan["ask"],
                              signal_key=key, reason=f"{SID} coherence {sig['coherence']:.3f} "
                              f"lag {int(sig['lag_bars'])} stop {plan['stop']:.4f}",
                              order=OrderSpec(type="limit", limit_price=cap, cap_price=cap, tif="ioc", window_s=60)))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [SED()]
