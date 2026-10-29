"""The analysis engine's two nightly jobs (desk/jobs.py), in the bulk lane, never on a pass's critical path.

analysis_inputs (weekday evenings, 16:40-19:25 ET, after the close's daily bars are final):
  - weekly, the listing filter's metadata: Alpaca's asset list (/v2/assets, us_equity, active then inactive) and
    Nasdaq Trader's symbol directory, turned into cache/analysis/listing.json by desk/analysis/listing.py;
  - nightly, each listed name's last N_BARS daily bars from Alpaca's SIP feed in both adjustments the spec reads:
    adjustment=all (every return-based quantity) and adjustment=raw (the price floors and dv20). The window is fetched
    whole every night, so its adjusted prices share one basis (an incrementally merged adjusted series can splice
    two bases around a small dividend). It is written to the hub's bar cache under two sources of its own, ADJ and
    RAW, which no other reader uses: no sleeve's series is touched.
analysis_screen (weekday evenings from 19:35 ET, before the lab at 19:45): the last completed session's screen from
  the cache only (the hub's cache_only path), written once to state/analysis/screen/<session>.json.gz, and
  state/analysis/summary.json. A session whose bars are not complete yet (READY_SHARE), or with no listing yet, is
  "not ready": a failed run, which the jobs' retry rules try again. A rerun once the file exists is a no-op.
The universe (2-19c): the genome, every sleeve's declared names and the held names, in Alpaca's notation, filtered by
the spec's listing rule."""
import os
import time

from .. import calendar as cal
from .. import code_identity
from ..data.hub import alpaca_stock_symbol
from ..util import iso
from . import FB2_START, SCREEN_VERSION, frozen, listing as L, screen as SC, store
from .bars import features, session_of

ADJ, RAW = "analysis_adj", "analysis_raw"   # the hub cache's sources this engine owns: Alpaca adjustment=all / raw
N_BARS = 140             # sessions in a window: momentum's 127 bars, the eligibility rule's 60, the segment rule's reach
CHUNK = 200              # names per Alpaca request (AlpacaData's own batch)
READY_SHARE = 0.95       # complete: this share of the listed names holding the previous session's bar hold d's
DEADLINE_S = 150.0       # past it the screen stops, writes nothing and says so (the job's 3-minute bound)
LISTING_MAX_AGE_S = 6 * 86400
MIN_ASSETS, MIN_ETF_FLAGS = 5000, 1000      # a smaller answer is a truncated read, never written over a good listing
SYMDIR = ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
          "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt")


def last_complete(now):
    from ..lab import last_complete as lab_last
    return lab_last(now).isoformat()


def universe(engine, now):
    """(names, {name: [origins]}, notes): the genome, every sleeve's declared names (its universe now and its
    declared bars' symbols) and the held equity names, plain US tickers in Alpaca's notation; a sleeve whose universe
    raises is noted, never fatal"""
    from ..lab import roster
    from ..lab.record import PLAIN
    origins, notes = {}, []

    def add(sym, origin):
        s = str(sym or "").strip().upper()
        s = alpaca_stock_symbol(s) if PLAIN.match(s) else None
        if s:
            origins.setdefault(s, set()).add(origin)
    for s in roster():
        add(s, "genome")
    for sid, sl in sorted((getattr(engine, "sleeves", None) or {}).items()):
        try:
            u = sl.universe_now(now) if hasattr(sl, "universe_now") else sl.CONFIG.universe
            for s in u or ():
                add(s, "declared")
            for spec in ((sl.CONFIG.needs or {}).get("bars") or ()):
                for s in spec.get("symbols") or ():
                    add(s, "declared")
        except Exception as e:                       # noqa: BLE001 - one sleeve's universe never stops the screen
            notes.append(f"{sid}: {type(e).__name__}: {str(e)[:120]}")
    books = getattr(getattr(engine, "books", None), "books", None) or {}
    for b in books.values():
        for inst, p in (getattr(b, "positions", None) or {}).items():
            try:
                held = inst.startswith("EQ:") and float((p or {}).get("qty") or 0) != 0
            except (TypeError, ValueError):
                held = False
            if held:
                add(inst[3:], "held")
    names = sorted(origins)
    return names, {s: sorted(origins[s]) for s in names}, notes


def read_listing(root):
    try:
        doc = store.read_listing(root)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) and isinstance(doc.get("symbols"), dict) else None


def refresh_listing(root, hub, now, spec, getter=None):
    """the listing from Alpaca's asset list and Nasdaq Trader's directory, written to cache/analysis/listing.json"""
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    if client is None or not hasattr(client, "assets"):
        raise RuntimeError("no Alpaca client for /v2/assets (no credentials)")
    assets, n = [], {}
    for status in ("active", "inactive"):
        got = client.assets("us_equity", status)
        if not isinstance(got, list):
            raise RuntimeError(f"/v2/assets {status}: no list")
        assets += got
        n[status] = len(got)
    if getter is None:
        from ..data.http import get

        def getter(url):
            return get(url, as_text=True)
    texts = [getter(u) for u in SYMDIR]
    if not all(isinstance(t, str) and t for t in texts):
        raise RuntimeError("the Nasdaq Trader symbol directory did not answer")
    doc = L.build(assets, texts[0], texts[1], spec)
    if len(assets) < MIN_ASSETS or doc["counts"]["etf_flags"] < MIN_ETF_FLAGS:
        raise RuntimeError("a truncated listing (%d assets, %d ETF flags): kept the previous one"
                           % (len(assets), doc["counts"]["etf_flags"]))
    from ..util import sha256_bytes
    doc.update(asof=now, at=iso(now), sources={"alpaca_assets": n, "nasdaqlisted_sha256": sha256_bytes(
        texts[0].encode()), "otherlisted_sha256": sha256_bytes(texts[1].encode())})
    store.write_listing(root, doc)
    return doc


def _trim(bars, keys):
    return [{k: b.get(k) for k in keys} for b in bars]


def refresh_bars(hub, names, now):
    """each name's last N_BARS daily bars in both adjustments, fetched whole and written over its ADJ / RAW series ->
    {source: {asked, served, errors}}; a failed request leaves its names' series as they were"""
    alpaca = getattr(hub, "alpaca", None)
    if alpaca is None:
        raise RuntimeError("no Alpaca market data (no credentials)")
    d = cal._as_date(last_complete(now))
    start = cal.session_open(cal.prev_trading_day(d, N_BARS + 5)) - 12 * 3600   # Alpaca stamps 00:00 ET
    out = {}
    for src, adj, keys in ((ADJ, "all", ("t", "o", "h", "l", "c")), (RAW, "raw", ("t", "c", "v"))):
        st = out[src] = {"asked": len(names), "served": 0, "errors": []}
        for i in range(0, len(names), CHUNK):
            chunk = names[i:i + CHUNK]
            try:
                got = alpaca.stock_bars(chunk, "1d", start, now, adjustment=adj)
            except Exception as e:                   # noqa: BLE001 - the other chunks still refresh
                st["errors"].append(f"{chunk[0]}..: {type(e).__name__}: {str(e)[:120]}")
                continue
            for s in chunk:
                bl = got.get(s) or []
                if bl:
                    hub.cache.replace(src, "1d", s, _trim(bl[-(N_BARS + 5):], keys))
                    st["served"] += 1
    return out


def inputs(engine, now, getter=None, clock=time.monotonic):
    """the analysis_inputs job"""
    t0 = clock()
    root, hub = engine.root, engine.hub
    try:
        spec, _ = frozen.load_spec()
    except frozen.SpecError as e:
        return {"ok": False, "error": str(e)}
    names, _, notes = universe(engine, now)
    info = {"ok": False, "names": len(names), "notes": notes[:10]}
    lst = read_listing(root)
    if lst is None or now - float(lst.get("asof") or 0) >= LISTING_MAX_AGE_S:
        try:
            lst = refresh_listing(root, hub, now, spec, getter)
            info["listing"] = dict(lst["counts"], refreshed=True, at=lst["at"])
        except Exception as e:                       # noqa: BLE001 - a stale listing still serves
            info["listing_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    if lst is not None and "listing" not in info:
        info["listing"] = dict(lst.get("counts") or {}, refreshed=False, at=lst.get("at"))
    want = [s for s in names if lst is None or L.check(lst, s) is None]
    info["wanted"] = len(want)
    try:
        info["bars"] = refresh_bars(hub, want, now)
    except Exception as e:                           # noqa: BLE001 - recorded: the screen will find it not ready
        info["bars_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    bars = info.get("bars") or {}
    info["ok"] = lst is not None and bool(bars) and not any(v["errors"] for v in bars.values())
    info["runtime_s"] = round(clock() - t0, 2)
    return info


def run(engine, now):
    """the analysis_screen job"""
    try:
        spec, sha = frozen.load_spec()
        frozen.check_scorer()
    except frozen.SpecError as e:
        return {"ok": False, "status": "error", "error": str(e)}
    names, origins, notes = universe(engine, now)
    return build(engine.root, engine.hub, now, names, spec, sha, listing=read_listing(engine.root),
                 origins=origins, notes=notes)


def _summary(root, doc):
    store.write_summary(root, doc)
    return doc


def build(root, hub, now, names, spec, spec_sha, session=None, listing=None, origins=None, notes=None,
          deadline_s=DEADLINE_S, clock=time.monotonic):
    """the screen of `session` (default: the last completed one) over `names`, from the hub's cache only"""
    t0 = clock()
    d = session or last_complete(now)
    if os.path.exists(store.screen_path(root, d)):
        return {"ok": True, "status": "exists", "session": d}
    base = {"v": SCREEN_VERSION, "session": d, "at": iso(now), "spec_version": spec.get("version"),
            "spec_sha256": spec_sha}
    if listing is None:
        _summary(root, dict(base, status="not_ready", why="no listing yet (analysis_inputs writes it)",
                            runtime_s=round(clock() - t0, 2)))
        return {"ok": False, "status": "not_ready", "session": d, "why": "no listing"}
    prev = cal.prev_trading_day(d).isoformat()
    entries, gaps, ready = [], {"no_adjusted_bars": 0, "no_raw_bars": 0}, {"with_previous": 0, "with_session": 0}
    for k, sym in enumerate(names):
        if clock() - t0 > deadline_s:
            _summary(root, dict(base, status="deadline", why=f"stopped after {k} of {len(names)} names",
                                runtime_s=round(clock() - t0, 2)))
            return {"ok": False, "status": "deadline", "session": d, "names_read": k}
        why = L.check(listing, sym)
        if why:
            entries.append((sym, None, why))
            continue
        adj = hub.bars(ADJ, "1d", [sym], N_BARS + 10, cache_only=True).get(sym) or []
        raw = hub.bars(RAW, "1d", [sym], N_BARS + 10, cache_only=True).get(sym) or []
        if not adj or not raw:
            gaps["no_adjusted_bars" if not adj else "no_raw_bars"] += 1
            entries.append((sym, None, "no_cached_bars"))
            continue
        both = {session_of(b) for b in adj} & {session_of(b) for b in raw}
        if prev in both:
            ready["with_previous"] += 1
            ready["with_session"] += d in both
        f, why = features(adj, raw, d)
        entries.append((sym, f, why))
    share = ready["with_session"] / ready["with_previous"] if ready["with_previous"] else 0.0
    ready.update(share=round(share, 4), need=READY_SHARE, previous=prev)
    if share < READY_SHARE:
        _summary(root, dict(base, status="not_ready", why="the session's bars are not complete", ready=ready,
                            gaps=gaps, runtime_s=round(clock() - t0, 2)))
        return {"ok": False, "status": "not_ready", "session": d, "ready": ready}
    rows = SC.screen(entries, d, spec, spec_sha)
    cnt = SC.counts(rows)
    by_origin = {}
    for o in (origins or {}).values():
        for x in o:
            by_origin[x] = by_origin.get(x, 0) + 1
    code = code_identity()
    doc = dict(base, scorer_sha256=frozen.SCORER_SHA256, code=code, fb2=d >= FB2_START, counts=cnt, gaps=gaps,
               listing={k: listing.get(k) for k in ("at", "counts", "sources")}, fields=SC.FIELDS, rows=rows)
    doc.pop("at")                                     # the file is a function of its inputs; the run's time is below
    if not store.write_once(root, d, doc):
        return {"ok": True, "status": "exists", "session": d}
    took = round(clock() - t0, 2)
    _summary(root, dict(base, status="written", runtime_s=took, code=code, fb2=d >= FB2_START, ready=ready,
                        gaps=gaps, origins=by_origin, notes=(notes or [])[:10], **cnt))
    return {"ok": True, "status": "written", "session": d, "names": len(rows), "scored": cnt["coverage"]["scored"],
            "tiers": {t: v["n"] for t, v in cnt["tiers"].items()}, "runtime_s": took}
