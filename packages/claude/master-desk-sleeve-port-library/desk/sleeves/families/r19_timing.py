"""R19 timing books (8) — Ausar R17 hourly geometry / 10-minute cloud and R18 causal overnight local-paper rules.

The vendored, hash-pinned source decides end to end: backend/r19_timing.py (blob 09a7ce30; evaluate, the hourly
v625-engine swing signal, the EMA5/12 cloud, the 13:00-15:00 overnight percentile) over its own snapshot — built
each pass by the vendored acquisition layer exactly as the R19 cycle built it (desk.feedlib.r19_source):
r19_data.Collector.collect (XNYS calendar, Alpaca asset census, corporate actions, raw SIP daily bars),
r19_intraday_data.enrich_intraday (IEX regular-session 30/10-minute bars, 09:30-anchored hours, observed split
transforms, issuer identity), r19_timing.prepare_snapshot, then the latest IEX quotes. The configs are the
source's register() with the deployed module name (backend.r19_timing): their digests equal the inventory
receipt's config_sha256 for all eight books. Each book then runs the source's per-book cycle
(desk.feedlib.r19_book): the vendored r19_cli.bounded_snapshot cuts its decision view, evaluate decides on the
ledger's book view, and the R19 ledger's execution obligations (backend/r19_core.py Ledger.process / _execute,
desk.feedlib.r19_ledger) size each fill on the desk's book:

  * owed exits first (observed bid at the stop, at the target, the scheduled exit, the 20-native-bar deadline),
    cancelled signals withdraw their working remainder, then entries — as evaluate orders them;
  * an absolute target per signal: each pass the fill is min(target - owned, displayed size net of what this book
    already took from that displayed quote), at the ask (buy) / bid (sell), whole shares, a buy capped by settled
    cash at price x (1 + fee) and the book's gross capacity, the remainder retried on later quotes until the
    signal's 5-minute window (entries) or the exit completes; a buy needs the instrument's action census and an
    active, tradable asset; a held name trades only under the contract it was bought as;
  * sale proceeds mature T+1 on the DTCC calendar and are released at the first XNYS opening on or after
    maturity (the vendored settlement_terms): evaluate and the buy cap see settled cash only, as the ledger's
    book did; fees are the config's fee_bps (5, or 25 for OVERNIGHT_25BP) per side.

Removed (runtime-wide, not these books' rules): the R19 ledger's 30 bps spread execution gate and the
NAV-withheld coupling it fed (a held name without a qualifying mark refused every buy), its storage-pressure
entry pause and the operator enable switch. No entry gate of the books themselves is removed.

Named divergences:
  * pass clock: the R19 worker cycled continuously; these books are evaluated on every engine pass in the regular
    session (evaluate returns regular_session_closed otherwise); one snapshot and one quote refresh per pass serve
    all eight books (the worker refreshed quotes per book when more than a second had passed); the priority-exit
    service (owned exits from retained features every 20 s during slow acquisitions) is subsumed by every pass
    evaluating the whole book on a fresh snapshot; the receipt journal is not kept (the desk ledger records);
    a session's premarket passes (07:00-09:25 ET) only acquire (the snapshot built, nothing decided or written:
    R19Book.warming_only), so the open's first pass builds on warm caches; no premarket snapshot serves the open;
  * family scope: the snapshot is collected for the eight timing configs alone (the R19 cycle collected every R19
    family at once and shared one <= 200-name quote request among them); held names do not jump the 6-symbol
    intraday warm-up queue (all 42 names are cached after the first passes);
  * snapshot reuse: once fully warmed, the collected snapshot is reused until the next native 10/30-minute
    boundary or session change (its only intraday inputs change there); quotes and asof are refreshed every pass,
    so the collector's cached reference inputs (asset census, corporate actions) are re-read at those boundaries
    instead of every cycle;
  * acknowledgement: the decided fill quantity is sent to the desk's venue as a marketable order at the observed
    quote instead of the ledger's local fill at that quote; a child the venue leaves unfilled (it lapses after
    120 s) returns its units to the order — decided again on a later quote within the signal's window — and to the
    sale's settlement claim; the book position opens at the venue fill time and price, while the position metadata
    the evaluators read is the ledger's (the first fill's intent metadata, contract, asset class, fill clock);
  * settlement calendar past 2026: the frozen DTCC table covers 2022-2026 and the source refused every later sale;
    beyond it the table's own rule (NYSE rule holidays + Columbus / Veterans Day; it reproduces 2022-2026
    exactly) dates the maturity (desk.feedlib.r19_ledger.settlement_terms);
  * acquisition: the R19 collector's authenticated GETs go through the desk's Alpaca client (receipts hash the
    parsed body); exchange_calendars' XNYS is the desk's NYSE rules plus the exchange's ad-hoc closures and
    special closes (identical on every call over 2000-2040: tools/parity/r19_calendar.py); the vendored modules'
    wall-clock reads (datetime.now) are bound to the desk clock (the same instant live)."""
import os
import re
from datetime import datetime, timezone

from ...contract import SleeveConfig
from ...feedlib import r19_source as RS
from ...feedlib.r19_book import R19Book

SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/r19_timing.py",
          "blob": "09a7ce30a24693ffd0daaa295b3411127d6865f4"}
UTC = timezone.utc


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=UTC).isoformat()


def configs():
    """the source registry's eight books, with the deployed module identity (their receipt digests)."""
    m = RS.vendored()
    return [dict(c, module="backend.r19_timing") for c in m["r19_timing"].register()]


def source_dir():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.environ.get("DESK_R19_SOURCE_DIR") or os.path.join(root, "cache", "r19_source")


def build_snapshot(collector, cfgs, books=(), clock_iso=None):
    """the R19 cycle's snapshot for the timing books (r19_cli._cycle, timing phases only)."""
    m = RS.vendored()
    iso_now = clock_iso or m["r19_core"].iso
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
        snapshot = m["r19_timing"].prepare_snapshot(snapshot)
    except Exception as exc:
        snapshot.setdefault("acquisition_errors", []).append(f"timing_preparation:{type(exc).__name__}:{exc}")
    owned = sorted({s for b in books for s in b.get("positions", {})})
    symbols = set(snapshot.get("r19_intraday_quote_symbols", [])) | {s for c in cfgs for s in c.get("symbols", [])}
    selected = owned + sorted(symbols - set(owned))
    try:
        collector.refresh_quotes(snapshot, selected[:max(200, len(owned))])
    except Exception as exc:
        snapshot.setdefault("acquisition_errors", []).append(f"equity_quotes:{type(exc).__name__}:{exc}")
    snapshot["asof"] = snapshot["now"] = iso_now()
    return snapshot


_MEMO = {}


def boundary_key(snapshot, now):
    """the snapshot's intraday inputs change only when a native 10/30-minute boundary completes (or a session
    turns); a fully warmed snapshot is reused until then, its quotes refreshed every pass."""
    m = RS.vendored()
    try:
        cal = m["r19_tensor"].sessions(snapshot)
        at = m["r19_core"].stamp(now)
        live = any(m["r19_core"].stamp(x["open"]) <= at < m["r19_core"].stamp(x["close"]) for x in cal)
        return (snapshot.get("calendar", {}).get("session"), live,      # a premarket snapshot never serves the open
                m["r19_intraday_data"]._last_complete_boundary(cal, 10, at),
                m["r19_intraday_data"]._last_complete_boundary(cal, 30, at))
    except Exception:
        return None


# The vendored collector files a cash dividend whose terms it cannot verify (a foreign or non-USD payer such as AG) under
# acquisition_errors, but it keeps the symbol in the verified set (r19_data: financial_pending only, never `pending`):
# prices, splits and the name's qualification are unchanged. Left in the count it kept every snapshot from reuse (35 notes
# on the record, 488 rebuilds of about 21 s each). The vendored bytes stay as they are; the desk reads past this one note.
_DIVIDEND_TERMS_NOTE = re.compile(r"^action_normalization:[^:,]+:native_dividend_rate_or_currency_unverified$")


def blocking_errors(snapshot):
    """the acquisition errors that make a build incomplete (the dividend-terms note does not)"""
    return [e for e in (snapshot.get("acquisition_errors") or []) if not _DIVIDEND_TERMS_NOTE.match(str(e))]


def action_problems(snapshot):
    """'SYM:reasons' of every corporate action the collector could not qualify, with whether it blocks the name's price basis"""
    out = []
    for p in (snapshot.get("corporate_action_coverage") or {}).get("normalization_errors") or []:
        out.append(f"{p.get('symbol')}:{','.join(p.get('reasons') or [])}" + (" (blocks the name)" if p.get("price_basis_coverage_blocked") else ""))
    return out


def warmed(snapshot):
    q = snapshot.get("r19_intraday_qualification") or {}
    pending = any(v.get("pending_uncached") for v in (q.get("progress") or {}).values())
    remaining = (snapshot.get("enrollment_progress") or {}).get("remaining_names")
    return bool(q) and not pending and not remaining and not blocking_errors(snapshot)


def unwarmed(snapshot):
    """what keeps a built snapshot from reuse (warmed's conditions), '' when nothing: on 2026-10-19 every pass rebuilt
    it (about 21 s of each pass, all session) and the record could not say why"""
    q = snapshot.get("r19_intraday_qualification") or {}
    out = [] if q else ["no intraday qualification"]
    pending = {k: v.get("pending_uncached") for k, v in (q.get("progress") or {}).items() if v.get("pending_uncached")}
    if pending:
        out.append("pending_uncached " + " ".join(f"{k}m:{v}" for k, v in sorted(pending.items())))
    remaining = (snapshot.get("enrollment_progress") or {}).get("remaining_names")
    if remaining:
        out.append(f"remaining_names {remaining}")
    errs = blocking_errors(snapshot)
    if errs:
        out.append(f"acquisition_errors {len(errs)}: " + "; ".join(str(e)[:80] for e in errs[:2]))
    return "; ".join(out)


def timing_snapshot(feeds, sleeve, now, arg):
    """FEED r19_timing_snapshot — one source snapshot per pass for the eight books."""
    import copy
    hub = feeds.hub
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    if client is None:
        return {"blocked": "R19_IEX_SOURCE_UNAVAILABLE: no Alpaca market-data client (credentials) on this desk"}
    m = RS.bind_clock(feeds.clock)
    col = RS.collector(source_dir(), client, feeds.clock)
    memo = _MEMO.get(id(col))
    if memo and memo["key"] is not None and memo["key"] == boundary_key(memo["snapshot"], m["r19_core"].iso()):
        snapshot = copy.deepcopy(memo["snapshot"])
        symbols = set(snapshot.get("r19_intraday_quote_symbols", [])) | {s for c in configs() for s in c["symbols"]}
        try:
            col.refresh_quotes(snapshot, sorted(symbols)[:200])
        except Exception as exc:
            snapshot.setdefault("acquisition_errors", []).append(f"equity_quotes:{type(exc).__name__}:{exc}")
        snapshot["asof"] = snapshot["now"] = m["r19_core"].iso()
        return snapshot
    snapshot = build_snapshot(col, configs())
    if warmed(snapshot):
        _MEMO[id(col)] = {"key": boundary_key(snapshot, snapshot["asof"]), "snapshot": copy.deepcopy(snapshot)}
    else:
        _MEMO.pop(id(col), None)
    note = getattr(hub, "_note", None)
    if note is not None:                       # the pass record's data health: why a build was not kept for reuse
        note("r19_timing_snapshot", {"ok": warmed(snapshot), "at": feeds.clock(), "why": unwarmed(snapshot)[:200],
                                               "actions": action_problems(snapshot)[:12]})
    return snapshot


FEEDS = {"r19_timing_snapshot": timing_snapshot}


class R19Timing(R19Book):
    FEED = "r19_timing_snapshot"
    MODULE = "r19_timing"

    def __init__(self, cfg):
        self.rule = cfg
        self.CONFIG = SleeveConfig(
            sleeve_id=cfg["id"].lower(), family="r19_timing", cadence_s=30, universe=tuple(cfg["symbols"]),
            capital=float(cfg["initial_capital"]), schedule="rth,premarket", venue_pref="alpaca",
            needs={"feeds": ["r19_timing_snapshot"]},
            params={"cost_bps": cfg["fee_bps"], "kind": cfg["kind"], "slots": cfg["slots"], "risk": cfg["risk"],
                    "notional": cfg["notional"]},
            source=dict(SOURCE, config_id=cfg["id"]),
            state_schema=dict(R19Book.STATE_SCHEMA))


def sleeves():
    return [R19Timing(c) for c in configs()]
