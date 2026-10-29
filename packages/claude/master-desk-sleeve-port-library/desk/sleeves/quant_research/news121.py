"""qr_newsconditioned121leadership -- News-conditioned 12-1 leadership (quant-research-critical@0be4c575
research/2026-10-08-agentic-top-five/branches/news.md, a design specification without code: its rules are implemented
here as written; "Proposed desk implementation").

Monthly snapshot (family job `qr_news121`, after the close of each month's final regular session; the pool is frozen
for the following month):
  universe  S&P 500 members that day; >= 253 completed daily observations (d-252 observable), last close >= $10,
            trailing 20-session average dollar volume >= $25M;
  M_i       TR[d-21] / TR[d-252] - 1 on total-return closes; the pool = positive momentum in the universe's top 20%;
            R_i = the momentum percentile in the universe (permanent-ID tie break);
  S_i       .65 R_i + .35 (1 + C_i N_i) / 2, ranked by S, then R, then the ID; the top 50 are candidates and a holding
            ranked below 75 at the next refresh exits.
Entries: a candidate is bought when the desk's Tensor verdict passes -- 1H timing: the engine's newest confirmed swing
on the canonical 1H series judged TRADE by the flagship's decision law (desk/sleeves/femto/tensor_swing.decide: fresh,
<= 3 bars / 6 hours old, confidence at the trade cutoff, not extended, invalidation not breached), supplying the entry
level, the invalidation and the expiry; 1D structure: the daily structural screen not BROKEN -- and the ask is at most
entry x 1.03 (the no-chase cap, which is also the limit). Whole-share day limit orders, cancelled at the verdict's
expiry or the session's end. Size: 0.5% of NAV at risk to the invalidation per entry; at most 8 names, 10% of NAV per
name, 30% per sector, 2% of NAV total stop-risk. Exits: the invalidation (an engine-held stop), a refresh rank below
75 or loss of eligibility (at the market).

Removed gates: the shared allocator's competing-strategy claims are not modelled: this sleeve's book carries its own
ceilings (the spec's research ceilings above), as every desk sleeve does.

Named divergences:
  1. no news extractor: the spec's LLM extraction / evidence critic needs a model snapshot and article vintages the
     desk does not hold; every name is NO_SEMANTIC_EDGE (C = N = 0), so S = .65 R + .175 ranks by R -- the spec's own
     primary control arm ("identical R-only ranking under the same Tensor decisions"); the N <= -0.5 thesis exit never
     fires;
  2. membership: the current S&P 500 constituent list (datasets/s-and-p-500-companies, refreshed at each snapshot) in
     place of dated point-in-time membership records -- point in time going forward, not for history;
  3. total return: Alpaca's all-adjusted daily closes (the hub's `equity` bars: split + dividend adjusted) as TR;
  4. the 10m refinement is not used (the spec makes it optional; it can only refine a 1H approval);
  5. sectors: the desk's sector table (vendor/old_desk_research/risk.py); an unmapped name is its own sector."""
import json
import math
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C

SID = "qr_newsconditioned121leadership"
ET = ZoneInfo("America/New_York")
SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT,
          "path": "research/2026-10-08-agentic-top-five/branches/news.md",
          "blob_sha": "e06be765da3a978392929d9af085a2aed9e1112a"}
SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
CACHE, MEMBERS = "qr_news121.json", "qr_sp500.json"
UA = "Mozilla/5.0 (compatible; master-desk paper research)"
TOP_FRACTION, TOP_N, EXIT_RANK = 0.20, 50, 75
MIN_OBS, MIN_CLOSE, MIN_DV20 = 253, 10.0, 25e6
CAP_MULT, MAX_NAMES, MAX_NAME, MAX_SECTOR = 1.03, 8, 0.10, 0.30
RISK_ENTRY, RISK_TOTAL = 0.005, 0.02
EXPIRY_S = 6 * 3600


# --------------------------------------------------------------------------------------------- the snapshot
def month_end(d):
    """the final regular session of d's month."""
    d = cal._as_date(d)
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    e = nxt - timedelta(days=1)
    while not C.is_session(e):
        e -= timedelta(days=1)
    return e.isoformat()


def snapshot(frames, members, d):
    """the spec's monthly ranking as of session d from {sym: daily frame (o h l c v, all-adjusted)}."""
    rows = []
    for s in sorted(set(members)):
        f = frames.get(s)
        if f is None or not len(f):
            continue
        f = f[f.index <= np.datetime64(d)]
        if len(f) < MIN_OBS or str(f.index[-1].date()) != d:
            continue
        c, v = f["c"].to_numpy(float), f["v"].to_numpy(float)
        if not (np.isfinite(c[-MIN_OBS:]).all() and c[-1] >= MIN_CLOSE):
            continue
        dv20 = float(np.mean(c[-20:] * v[-20:]))
        if not dv20 >= MIN_DV20:
            continue
        m = c[-22] / c[-253] - 1.0                     # TR[d-21] / TR[d-252] - 1 (index -1 is d)
        if np.isfinite(m):
            rows.append((s, float(m), dv20))
    n = len(rows)
    order = sorted(rows, key=lambda r: (r[1], r[0]))   # ascending momentum, permanent-ID tie break
    R = {s: (i + 1) / n for i, (s, _, _) in enumerate(order)}
    k = int(math.ceil(TOP_FRACTION * n))
    top = {s for s, _, _ in order[n - k:]} if n else set()
    pool = [(s, m) for s, m, _ in rows if m > 0 and s in top]
    C_, N_ = 0.0, 0.0                                   # no semantic edge (divergence 1)
    ranked = sorted(({"symbol": s, "M": m, "R": R[s], "S": .65 * R[s] + .35 * (1 + C_ * N_) / 2} for s, m in pool),
                    key=lambda r: (-r["S"], -r["R"], r["symbol"]))
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return {"asof": d, "eligible": sorted(R), "ranked": ranked, "top": [r["symbol"] for r in ranked[:TOP_N]]}


def parse_members(text):
    out = []
    for i, line in enumerate((text or "").splitlines()):
        if i == 0 or not line.strip():
            continue
        sym = line.split(",", 1)[0].strip().upper().replace(".", "-")
        if sym:
            out.append(sym)
    return sorted(set(out))


def members(root, now, fetch=None, refresh=False):
    p = os.path.join(root, "cache", MEMBERS)
    try:
        doc = json.load(open(p))
    except (OSError, ValueError):
        doc = None
    if doc and not refresh:
        return doc["symbols"]
    from ...data.http import get
    fetch = fetch or (lambda url: get(url, headers={"User-Agent": UA}, timeout=30, as_text=True))
    try:
        syms = parse_members(fetch(SP500_URL))
        if len(syms) >= 400:
            doc = {"symbols": syms, "fetched_at": now, "source": SP500_URL}
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p + ".tmp", "w") as f:
                json.dump(doc, f)
            os.replace(p + ".tmp", p)
    except Exception:
        if not doc:
            raise
    return doc["symbols"]


def run(hub, root, now, fetch=None):
    """the job `qr_news121`: the snapshot of the latest month-end session that has completed."""
    today = cal._as_date(now).isoformat()
    last = today if C.is_session(today) and now >= cal.session_close(today) + 15 * 60 else C.prev_session(today)
    d = last if month_end(last) == last else month_end((cal._as_date(last).replace(day=1) - timedelta(days=1)))
    p = os.path.join(root, "cache", CACHE)
    try:
        old = json.load(open(p))
    except (OSError, ValueError):
        old = None
    if old and old.get("asof") == d:
        return {"due": False, "asof": d}
    syms = members(root, now, fetch, refresh=True)
    frames = C.daily(hub, "equity", syms, 300)
    doc = snapshot(frames, syms, d)
    doc.update(computed_at=now, members=len(syms), served=len(frames))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w") as f:
        json.dump(doc, f)
    os.replace(p + ".tmp", p)
    return {"asof": d, "members": len(syms), "eligible": len(doc["eligible"]), "pool": len(doc["ranked"])}


def read(root):
    try:
        return json.load(open(os.path.join(root, "cache", CACHE)))
    except (OSError, ValueError, TypeError):
        return None


def feed_snapshot(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    return read(root) if root else None


# --------------------------------------------------------------------------------------------- the verdict
def verdict(sym, feed, daily, equity, held, acted, now):
    """the desk's Tensor verdict for one candidate: (ok, detail) -- 1H TRADE by the flagship's law and the daily
    structural screen not BROKEN."""
    from ...vendor.old_desk_research import structural_screen as sscreen
    from ..femto import tensor_swing as TS
    series, engine = (feed or {}).get("series") or {}, (feed or {}).get("engine") or {}
    bars = series.get(sym) or []
    if sym not in engine or len(bars) < TS.MIN_BARS_AFTER_STRIP:
        return False, {"why": "no 1H engine output"}
    d = TS.decide(sym, bars, equity, set(), set(), acted, TS.signals_of(bars, engine[sym]), now=now)
    if d["decision"] != "TRADE":
        return False, {"why": d["decision"], "reason": d["reason"][:160]}
    sv = sscreen.screen_from_bars(sym, daily or [])
    if sv.get("verdict") in ("BROKEN", "UNKNOWN"):
        return False, {"why": "1D structure " + str(sv.get("verdict"))}
    sig = d["signal"]
    return True, {"entry": float(sig["entry"]), "stop": float(sig["stop"]), "t": int(sig["t"]),
                  "confidence": sig.get("confidence"), "phenotype": sig.get("phenotype")}


def sector(sym):
    from ...vendor.old_desk_research import risk as desk_risk
    return desk_risk.sector(sym) or sym


class News121(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=(), capital=1_000_000.0,
            schedule="rth",
            needs={"feeds": ["qr_news121", "tensor"], "quotes": {"source": "equity"},
                   "bars": [{"source": "equity_split", "interval": "1d", "n": 260, "symbols_for": True,
                             "key": "daily"}]},
            params={"pool": "positive 12-1 momentum in the S&P 500 universe's top 20%", "S": ".65R + .35(1+CN)/2",
                    "top": TOP_N, "exit_rank": EXIT_RANK, "cap": CAP_MULT, "max_names": MAX_NAMES,
                    "max_name": MAX_NAME, "max_sector": MAX_SECTOR, "risk_entry": RISK_ENTRY,
                    "risk_total": RISK_TOTAL},
            source=SOURCE, state_schema={"held": "dict", "acted": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _doc(self):
        return read(self.engine.root) if self.engine is not None else None

    def universe_now(self, now, book=None):
        """the Tensor feed's names: this month's candidates and the held book."""
        doc = self._doc() or {}
        if book is None and self.engine is not None and getattr(self.engine, "books", None) is not None:
            book = self.engine.books.books.get(SID)
        held = {i.split(":", 1)[1] for i, p in ((book.positions if book is not None else None) or {}).items()
                if i.startswith("EQ:") and abs(float(p["qty"])) > 1e-12}
        return sorted(set(doc.get("top") or ()) | held)

    def bar_symbols(self, spec, now, book):
        held = {i.split(":", 1)[1] for i, p in (book.positions or {}).items() if i.startswith("EQ:")}
        return sorted(set((self._doc() or {}).get("top") or ()) | held)

    def quote_universe(self, now, book):
        return self.bar_symbols(None, now, book)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("held", {}), ("acted", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now = float(view.now)
        if not cal.is_rth(now):
            return []
        doc = (view.extra or {}).get("qr_news121")
        if not doc:
            st["log"] = (st["log"] + [{"at": view.session, "why": "no monthly snapshot yet"}])[-50:]
            return []
        pos = C.held(view)
        for s in list(st["held"]):
            if s not in pos:
                st["held"].pop(s)                               # stopped out / exited
        out = []
        ranks = {r["symbol"]: r["rank"] for r in doc.get("ranked") or []}
        elig = set(doc.get("eligible") or ())
        for s, q in sorted(pos.items()):                        # the monthly refresh exits
            h = st["held"].get(s) or {}
            if h.get("asof") and doc["asof"] > h["asof"] and (ranks.get(s, 10 ** 9) > EXIT_RANK or s not in elig):
                out.append(Intent("exit", s, signal_key=f"news121:{doc['asof']}:{s}:refresh",
                                  reason=f"{SID} refresh {doc['asof']}: rank {ranks.get(s)} / eligible {s in elig}",
                                  order=OrderSpec(type="market", window_s=1800)))
        exiting = {i.symbol for i in out}
        nav = C.nav(view)
        risk_used = sum(float(h.get("risk") or 0) for s, h in st["held"].items() if s in pos)
        sector_w = {}
        for s, q in pos.items():
            px = ((view.quotes or {}).get(s) or {}).get("bid") or 0.0
            sector_w[sector(s)] = sector_w.get(sector(s), 0.0) + q * px / nav if nav else 0.0
        names = len(set(pos) - exiting)
        pending = {str(o.get("inst", "")).split(":", 1)[-1] for o in ((view.extra or {}).get("pending_orders") or [])}
        feed = (view.extra or {}).get("tensor") or {}
        daily = (view.extra or {}).get("bars_daily") or (view.bars or {}).get("1d") or {}
        session_end = cal.session_close(view.session) if hasattr(cal, "session_close") else now + 3600
        for s in doc.get("top") or []:
            if names >= MAX_NAMES:
                break
            if s in pos or s in pending:
                continue
            ok, det = verdict(s, feed, daily.get(s), nav, set(pos), st["acted"], now)
            if not ok:
                continue
            st["acted"][s] = det["t"]                           # one decision per swing bar
            q = (view.quotes or {}).get(s) or {}
            ask = q.get("ask")
            cap = round(det["entry"] * CAP_MULT, 2)
            if not ask or ask > cap or det["entry"] <= det["stop"]:
                st["log"] = (st["log"] + [{"at": view.session, "s": s, "why": "NO_CHASE" if ask else "no quote"}])[-50:]
                continue
            per = det["entry"] - det["stop"]
            qty = int(math.floor(min(RISK_ENTRY * nav / per, MAX_NAME * nav / cap)))
            qty = min(qty, int(math.floor(max(0.0, RISK_TOTAL * nav - risk_used) / per)))
            sec = sector(s)
            qty = min(qty, int(math.floor(max(0.0, MAX_SECTOR - sector_w.get(sec, 0.0)) * nav / cap)))
            if qty < 1:
                continue
            st["held"][s] = {"asof": doc["asof"], "stop": det["stop"], "entry": det["entry"], "risk": qty * per,
                             "bar": det["t"], "since": view.session}
            risk_used += qty * per
            sector_w[sec] = sector_w.get(sec, 0.0) + qty * cap / nav
            names += 1
            out.append(Intent("enter", s, side="long", qty=float(qty), price_hint=float(ask), stop=det["stop"],
                              exit_rules=(ExitRule("stop", det["stop"]),), signal_key=f"news121:{s}:{det['t']}",
                              reason=f"{SID} R-rank candidate, Tensor TRADE conf {det['confidence']} "
                                     f"({det['phenotype']}), entry {det['entry']:.2f} stop {det['stop']:.2f}",
                              order=OrderSpec(type="limit", limit_price=cap, cap_price=cap, tif="day",
                                              window_s=max(60.0, min(EXPIRY_S, session_end - now)))))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [News121()]
