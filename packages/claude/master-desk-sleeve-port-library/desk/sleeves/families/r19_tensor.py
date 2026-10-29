"""R19 tensor books (22) — the frozen R17/R18 weekly Tensor ownership experiments: G4 (Author buy-green, deep
drawdown, native close <= 10, 60-day return >= 0, weekly vol20 >= .09), C1 (Author buy-cyan, close <= 5, 60-day
return >= 31%, vol20 >= .07) in all / cool / hot volatility cuts and cash / delay / reserve capital modes, the
10-slot G4 pair, BETA_M2_52W (v625 M2 qualifiers, bottom-third 52-week dollar-volume cohort, beta > 1.2) and
G4_RED_TIMEOUT; each ticket held to the last session of the 52nd calendar week, sold 5 minutes before its close.

The vendored, hash-pinned source decides end to end: backend/r19_tensor.py (the manifest's reviewed pin, audit
b8665a6 deployment/2026-10-11/scripts/deploy/audit-r19_tensor.py, blob 53fbcc3a — byte-identical to the
corrected-incomplete backend/r19_tensor.py) with its archived Author v615 / v625 engines run under Node
(strategies/r19/tensor, hash-verified by the module itself) over the snapshot the R19 cycle built, built here by
the vendored acquisition layer (desk.feedlib.r19_source): r19_data.Collector.collect (XNYS calendar, the full
Alpaca asset census, corporate actions, raw SIP daily bars with the 20-name rotating enrollment of the 1,838-name
frozen cohort), r19_tensor.qualify_snapshot (native identity, split transforms, exact weekly/daily prefixes,
engine prefix challenge, the census), then the latest IEX quotes. The configs are the source register() with the
deployed module name (backend.r19_tensor): their sha256 equal the inventory's config_sha256 for all 22. Each book
runs the source's per-book cycle (desk.feedlib.r19_book): r19_cli.bounded_snapshot (r19_tensor.trading_view) cuts
its view, evaluate decides, the R19 ledger's execution rules (desk.feedlib.r19_ledger: price-tiered fees 30 / 15 /
10 bps, QQQ 10; whole shares at the ask / bid; settled-cash cap; T+1 settlement) size each fill on the desk book.

Removed (runtime-wide, not these books' rules): the R19 ledger's 30 bps spread execution gate and the
NAV-withheld coupling it fed, its storage-pressure entry pause, the operator enable switch. Every book rule
stays (>= 99% census and feature coverage, slots, tickets, issuer dedupe, entry windows, 52-week exits, reserve).

Named divergences:
  * acquisition worker: the R19 worker cycled continuously; here a background thread runs the same collect /
    qualify cycle (back to back while enrollment or a new epoch is pending, every 2 minutes once settled) and the
    engine pass reads its latest snapshot with freshly refreshed quotes (held and pending names first);
  * pass clock: the books are evaluated every minute in the first and last six minutes of each session — every
    tensor rule acts only there (entries open..open+5, scheduled exits from close-5, reserve trades at the open);
    the worker keeps the snapshot current around the clock, started (or restarted) by a session's premarket
    passes (07:00-09:25 ET), which decide nothing, so its census is enrolled before the open; the priority-exit
    service and the receipt journal are not kept;
  * family scope: the snapshot is collected for the 22 tensor configs alone (the R19 cycle collected every R19
    family at once and shared one <= 200-name quote request); held names are prioritised as the source's owned
    names were;
  * book quantities as integers: the ledger handed evaluate its TEXT column's strings, and the frozen evaluator's
    (unused) slot count `p['quantity']>0` — and the reserve test `pos['QQQ']['quantity']>0` — then raise TypeError
    whenever a non-QQQ name is held: every later evaluation of the book failed (r19_cli recorded a book_error),
    so no 52-week exit and no further entry could follow its first fill. The book view carries the same whole
    units as integers (the evaluator's int() reads are unchanged; tested against the source's behaviour);
  * acknowledgement, settlement calendar past 2026, acquisition seams: as for r19_timing (desk.feedlib.r19_book /
    r19_ledger / r19_source)."""
import os
import threading
import time
from datetime import datetime, timezone

from ...contract import Intent, SleeveConfig
from ...feedlib import r19_source as RS
from ...feedlib.r19_book import R19Book
from . import r19_timing

SOURCE = {"repo": "codex-complete-archive", "ref": "audit/ausar-semantic-repairs-2026-10-12",
          "commit": "b8665a6daf8b2b07a4f51f2bf963bcb6310b005e",
          "path": "deployment/2026-10-11/scripts/deploy/audit-r19_tensor.py",
          "blob": "53fbcc3a8d6482cf13bfa95a61972971493c2bd4"}
UTC = timezone.utc
FEED = "r19_tensor_snapshot"
SCHEDULE = "open+0:open+6,close-6:close+0,premarket"     # premarket: acquisition only (R19Book.warming_only)
BUSY_S, QUIET_S = 5.0, 120.0
# what the per-book view (r19_tensor.trading_view) and the quote refresh read; the rest of a cycle's snapshot
# (full daily histories, weekly / daily prefixes) stays inside the worker
KEEP = ("asof", "now", "environment", "pause_entries", "storage", "calendar", "calendar_sessions",
        "acquisition_errors", "tensor_census", "tensor_source_bindings", "tensor_analysis", "asset_identity",
        "r19_tensor_qualification", "provider_receipts", "quotes", "corporate_actions", "corporate_action_coverage",
        "r19_tensor_quote_symbols", "assets", "etf", "enrollment_progress", "tensor_G4_events",
        "tensor_G4_exit_events", "market_open")
INTEREST = {}            # sleeve_id -> names this book holds or has pending (quoted first, prioritised)


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=UTC).isoformat()


def configs():
    """the source registry's 22 books, with the deployed module identity (their receipt digests)."""
    m = RS.vendored()
    return [dict(c, module="backend.r19_tensor") for c in m["r19_tensor"].register()]


def interest():
    return sorted({s for v in INTEREST.values() for s in v.get("held", [])} |
                  {s for v in INTEREST.values() for s in v.get("pending", [])})


def interest_books():
    """the books' owned names as the source's collect saw them (priority histories and action coverage)."""
    held = sorted({s for v in INTEREST.values() for s in v.get("held", [])})
    return [{"config": {"currency": "USD"}, "positions": {s: {"metadata": {}} for s in held},
             "action_symbols": sorted({s for v in INTEREST.values() for s in v.get("actions", [])})}]


def refresh(collector, snapshot, owned):
    """the cycle's per-book quote refresh: owned names first, then the qualified candidates."""
    owned = sorted(set(owned))
    symbols = set(snapshot.get("r19_tensor_quote_symbols", [])) | set(snapshot.get("r19_intraday_quote_symbols", [])) | {"QQQ"}
    selected = owned + sorted(symbols - set(owned))
    try:
        collector.refresh_quotes(snapshot, selected[:max(200, len(owned))])
    except Exception as exc:
        snapshot.setdefault("acquisition_errors", []).append(f"equity_quotes:{type(exc).__name__}:{exc}")
    return snapshot


def build_snapshot(collector, cfgs, directory, books=()):
    """the R19 cycle's snapshot for the tensor books (r19_cli._cycle, tensor phases)."""
    m = RS.vendored()
    iso_now = m["r19_core"].iso
    try:
        snapshot = collector.collect(cfgs, list(books))
    except Exception as exc:
        snapshot = {"asof": iso_now(), "now": iso_now(), "environment": "paper", "quotes": {}, "histories": {},
                    "calendar": {}, "acquisition_errors": [f"common_collection:{type(exc).__name__}:{exc}"]}
        try:
            cal, sessions, last, native = collector._calendar(datetime.fromisoformat(snapshot["asof"]))
            snapshot.update(calendar=cal, calendar_sessions=sessions, market_open=cal["is_open"])
            asset = collector.cached(m["r19_data"].ASSET_CACHE_KEY) or collector.cached("alpaca:all_us_equity_assets:v2")
            if asset:
                snapshot["assets"] = asset["value"]
        except Exception as calendar_exc:
            snapshot["acquisition_errors"].append(f"calendar:{type(calendar_exc).__name__}")
    try:
        snapshot = m["r19_intraday_data"].enrich_intraday(collector, snapshot, cfgs, list(books))
    except Exception as exc:
        snapshot.setdefault("acquisition_errors", []).append(f"intraday:{type(exc).__name__}:{exc}")
    try:
        snapshot = m["r19_tensor"].qualify_snapshot(snapshot, list(books), cache_directory=directory)
    except Exception as exc:
        snapshot.setdefault("acquisition_errors", []).append(f"tensor_qualification:{type(exc).__name__}:{exc}")
    refresh(collector, snapshot, {s for b in books for s in b.get("positions", {})})
    snapshot["asof"] = snapshot["now"] = iso_now()
    return snapshot


def publishable(snapshot):
    out = {k: snapshot[k] for k in KEEP if k in snapshot}
    out["histories"] = {s: rows[-10:] for s, rows in (snapshot.get("histories") or {}).items()}   # trading_view
    return out


class Worker:
    """the R19 worker's acquisition cycle on a background thread (collect -> qualify -> quotes)."""

    def __init__(self, directory, client, clock, start=True):
        m = RS.vendored()
        self.directory, self.clock = directory, clock
        self.collector = m["r19_data"].Collector(directory, getter=RS.alpaca_getter(client, clock))
        self.latest, self.error, self.cycles, self.last_cycle_s = None, None, 0, None
        self.thread = threading.Thread(target=self.loop, name="r19-tensor-acquisition", daemon=True)
        if start:
            self.thread.start()

    def cycle(self):
        t0 = time.time()
        snap = build_snapshot(self.collector, configs(), self.directory, books=interest_books())
        q = snap.get("r19_tensor_qualification") or {}
        settled = bool(q.get("exact_input_cache_reused")) and not (snap.get("enrollment_progress") or {}).get(
            "remaining_names")
        self.latest, self.error, self.last_cycle_s = publishable(snap), None, round(time.time() - t0, 1)
        self.cycles += 1
        return settled

    def loop(self):
        while True:
            settled = False
            try:
                settled = self.cycle()
            except Exception as exc:                       # the cycle's own failures are recorded, never fatal
                self.error = f"{type(exc).__name__}: {str(exc)[:200]}"
            time.sleep(QUIET_S if settled else BUSY_S)

    def status(self):
        return {"cycles": self.cycles, "error": self.error, "last_cycle_s": self.last_cycle_s}


_WORKERS = {}
_LAST = {}
SYNC = [bool(os.environ.get("DESK_R19_SYNC"))]       # tests / parity: run the cycle inside the pass


def tensor_snapshot(feeds, sleeve, now, arg):
    """FEED r19_tensor_snapshot — the latest qualified cycle snapshot with this pass's quotes."""
    hub = feeds.hub
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    if client is None:
        return {"blocked": "R19_IEX_SOURCE_UNAVAILABLE: no Alpaca market-data client (credentials) on this desk"}
    m = RS.bind_clock(feeds.clock)
    directory = r19_timing.source_dir()
    col = RS.collector(directory, client, feeds.clock)
    _LAST["collector"] = col
    if SYNC[0]:
        return publishable(build_snapshot(col, configs(), directory, books=interest_books()))
    key = (directory, id(client))
    if key not in _WORKERS:
        _WORKERS[key] = Worker(directory, client, feeds.clock)
    w = _WORKERS[key]
    base = w.latest
    note = getattr(hub, "_note", None)
    if note is not None:                       # the pass record's data health: how far the acquisition cycle has got
        prog = (base or {}).get("enrollment_progress") or {}
        left = prog.get("remaining_names")
        st = w.status()
        note(FEED, {"ok": base is not None and not left, "at": feeds.clock(), "cycles": st["cycles"],
                    "last_cycle_s": st["last_cycle_s"], "worker_error": st["error"],
                    "raw_names_cached": prog.get("raw_names_cached"), "remaining_names": left,
                    "why": "no cycle has finished yet" if base is None else (f"remaining_names {left}" if left else "")})
    if base is None:
        return {"warming": "R19 tensor acquisition warming", "worker": w.status()}
    snap = dict(base)
    snap["quotes"] = dict(base.get("quotes") or {})
    snap["provider_receipts"] = dict(base.get("provider_receipts") or {})
    snap["acquisition_errors"] = list(base.get("acquisition_errors") or [])
    held = sorted({s for v in INTEREST.values() for s in v.get("held", [])})
    refresh(col, snap, held + [s for s in interest() if s not in held])
    snap["asof"] = snap["now"] = m["r19_core"].iso()
    return snap


FEEDS = {FEED: tensor_snapshot}


class R19Tensor(R19Book):
    FEED = FEED
    MODULE = "r19_tensor"
    INT_QUANTITY = True           # named divergence: the frozen evaluator compares quantities with integers

    def __init__(self, cfg):
        self.rule = cfg
        self.CONFIG = SleeveConfig(
            sleeve_id=cfg["id"].lower(), family="r19_tensor", cadence_s=60, universe=tuple(cfg["symbols"]),
            capital=float(cfg["initial_capital"]), schedule=SCHEDULE, venue_pref="alpaca", needs={"feeds": [FEED]},
            params={"family": cfg["family"], "volatility": cfg["volatility"], "capital_mode": cfg["capital_mode"],
                    "slots": cfg["slots"], "ticket": cfg["ticket"], "source_engine": cfg["source_engine"]},
            source=dict(SOURCE, config_id=cfg["id"]), state_schema=dict(R19Book.STATE_SCHEMA))

    def top_up(self, snap, symbols):
        """the cycle refreshed a book's quotes whenever one of its owned names had none (r19_cli)."""
        missing = sorted(s for s in symbols if s not in (snap.get("quotes") or {}))
        col = _LAST.get("collector")
        if missing and col is not None:
            try:
                col.refresh_quotes(snap, missing)
            except Exception as exc:
                snap.setdefault("acquisition_errors", []).append(f"owned_quotes:{type(exc).__name__}:{exc}")

    def signal(self, view):
        if self.warming_only(view):                   # the worker was started / fed by this pass's view
            return []
        snap = view.extra.get(self.FEED)
        if snap and snap.get("warming"):
            self._st = dict(view.state or {}) or None
            return [Intent("signal", "QQQ", reason="R19 tensor acquisition warming", meta={"worker": snap.get("worker")},
                           signal_key="warming")]
        out = super().signal(view)
        st = getattr(self, "_st", None) or {}
        held = sorted(p.split(":", 1)[1] for p in view.positions if p.startswith("EQ:"))
        pending = sorted({c.get("symbol") for c in ((st.get("evaluator") or {}).get("pending") or {}).values()
                          if isinstance(c, dict) and c.get("symbol")})
        INTEREST[self.CONFIG.sleeve_id] = {"held": held, "pending": pending, "actions": list(st.get("action_symbols", []))}
        return out


def sleeves():
    return [R19Tensor(c) for c in configs()]
