"""Options-chain warmer (WIRING-SOURCE-MAP §1, verdict: provider).

Ports the femto-lean master's core/options_feeds.py selection windows
(git 15f3368) onto the v2 Alpaca door, writing the exact payload shapes
the v2 consumers read via BarCache.write_options / SleeveContext.options_chain:

  QQQ puts 0..52 DTE   -> {"quotes": [{symbol, expiration, strike, delta, bid, ask}]}
  SPY parity (DESIGNED-ORDER-LOGIC §4): calls AND puts, nearest two
    expiries >= 7 DTE, strikes within +/-5% of the SPY spot (newest SPY
    close in the bar cache) -> {"quotes": [{symbol, expiration, strike,
    right ("call"/"put"), bid, ask}]} under cache key "SPY"
  VXX calls +50..+120  -> {"chains": {"VXX": [{symbol, strike, expiration}]},
  XSP puts -7..+7 DTE     "quotes": {OCC: {bid, ask}}}

Warm-time only; sleeves never touch the network (DESIGN §4b). Fail-closed
per section, exactly as the master producer: a failed contracts fetch
yields no chain, a snapshot without a two-sided quote yields no quote,
and a section failure never blocks the bar warm — it is recorded in the
returned summary instead.

VIX closes: Alpaca has no VIX. The one sanctioned Yahoo use (price only,
no volume — the master's yahoo_vix_series) warms cache/bars/VIX/1Day.jsonl
so adapters/vix_hedge.py's VIX 1Day lookup resolves.
"""
from __future__ import annotations
import json, math, os, re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .cache import BarCache
from .models import Bar

ET = ZoneInfo("America/New_York")
_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")

LADDER_UNDERLYING = "QQQ"
LADDER_DTE_MAX = 52            # master LADDER_DTE_MAX (sleeve DTE_HI)
PARITY_UNDERLYING = "SPY"      # DESIGNED-ORDER-LOGIC §4 box-spread parity
PARITY_MIN_DTE = 7             # expiries >= 7 DTE only
PARITY_WINDOW_DTE = 62         # contract fetch window (nearest two expiries chosen inside)
PARITY_EXPIRIES = 2            # nearest two expiries >= PARITY_MIN_DTE
PARITY_BAND_FRAC = 0.05        # strikes within +/-5% of the SPY spot
WINDOWS = (("VXX", "call", 50, 120),   # vix_hedge: sleeve filters to 60-110
           ("XSP", "put", -7, 7))      # spx_premium: sleeve filters to its week


def parse_occ(symbol):
    m = _OCC.match(str(symbol or ""))
    if not m:
        return None
    yy, mm, dd = int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:6])
    return {"root": m.group(1), "expiration": date(2000 + yy, mm, dd).isoformat(),
            "cp": m.group(3), "strike": int(m.group(4)) / 1000.0}


def _f(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _contract_row(c):
    """Raw Alpaca contract dict -> {symbol, strike, expiration} (None if unusable)."""
    occ = c.get("symbol")
    parsed = parse_occ(occ)
    if parsed is None:
        return None
    strike = _f(c.get("strike")) if c.get("strike") is not None else _f(c.get("strike_price"))
    exp = c.get("expiration") or c.get("expiration_date") or parsed["expiration"]
    return {"symbol": occ, "strike": strike if strike is not None else parsed["strike"],
            "expiration": str(exp)[:10]}


def _snapshot_row(snap):
    """Snapshot in any door shape -> {bid, ask, delta} (fields may be None).

    Accepts the master's normalized {bid, ask, delta} and the raw
    v1beta1 body entry {latestQuote: {bp, ap}, greeks: {delta}}.
    """
    if not isinstance(snap, dict):
        return {}
    if "latestQuote" in snap or "latest_quote" in snap:
        q = snap.get("latestQuote") or snap.get("latest_quote") or {}
        g = snap.get("greeks") or {}
        return {"bid": _f(q.get("bp")), "ask": _f(q.get("ap")), "delta": _f(g.get("delta"))}
    return {"bid": _f(snap.get("bid")), "ask": _f(snap.get("ask")), "delta": _f(snap.get("delta")),
            "iv": _f(snap.get("impliedVolatility")) or _f((snap.get("greeks") or {}).get("iv"))}


def _snapshots(door, symbols):
    """{OCC: {bid, ask, delta}} — batched at 100 (v1beta1 convention);
    any batch failure drops only that batch (master _snapshots)."""
    out = {}
    if door is None or not symbols:
        return out
    for i in range(0, len(symbols), 100):
        batch = symbols[i:i + 100]
        try:
            resp = door.option_snapshots(batch) or {}
        except Exception:
            continue
        snaps = resp.get("snapshots") if isinstance(resp, dict) else None
        if not isinstance(snaps, dict):
            snaps = resp if isinstance(resp, dict) else {}
        for occ, snap in snaps.items():
            row = _snapshot_row(snap)
            if row:
                out[occ] = row
    return out


def _contracts(door, underlying, kind, ref, lo, hi):
    gte = (ref + timedelta(days=lo)).isoformat()
    lte = (ref + timedelta(days=hi)).isoformat()
    try:
        rows = door.option_contracts(underlying, type=kind, expiry_gte=gte, expiry_lte=lte) or []
    except Exception:
        return []
    out = []
    for c in rows:
        if isinstance(c, dict):
            row = _contract_row(c)
            if row is not None:
                out.append(row)
    return out


def build_ladder_quotes(door, ref):
    """QQQ put quotes 0..52 DTE — the ladder consumer shape (master _ladder_quotes)."""
    chain = _contracts(door, LADDER_UNDERLYING, "put", ref, 0, LADDER_DTE_MAX)
    snaps = _snapshots(door, sorted({c["symbol"] for c in chain}))
    quotes = []
    for row in sorted(chain, key=lambda r: r["symbol"]):
        snap = snaps.get(row["symbol"]) or {}
        if snap.get("bid") is None or snap.get("ask") is None:
            continue  # unquotable: the sleeve fails closed on it
        quotes.append({**row, "bid": snap["bid"], "ask": snap["ask"], "delta": snap.get("delta")})
    return quotes


def _spy_spot(cache):
    """Newest SPY close from the local bar cache (1Day, then 1Hour).

    The parity window is struck around the spot the desk already
    cached at bar-warm time; no spot -> no parity window (fail closed).
    """
    for tf in ("1Day", "1Hour"):
        bars = cache.read_bars(PARITY_UNDERLYING, tf, 1)
        if bars:
            spot = _f(bars[-1].c)
            if spot is not None and spot > 0:
                return spot
    return None


def build_parity_quotes(door, ref, spot, held=()):
    """SPY box-parity quotes (DESIGNED-ORDER-LOGIC §4): calls AND puts
    for the nearest two expiries >= 7 DTE, strikes within +/-5% of
    `spot`. Two-sided snapshots only (fail closed per contract). Held
    SPY OCCs outside the window are appended in the same list shape so
    an open box can always be priced for exit."""
    chain = []
    for kind in ("call", "put"):
        for row in _contracts(door, PARITY_UNDERLYING, kind, ref,
                              PARITY_MIN_DTE, PARITY_WINDOW_DTE):
            chain.append({**row, "right": kind})
    expiries = sorted({r["expiration"] for r in chain
                       if r["expiration"] >= (ref + timedelta(days=PARITY_MIN_DTE)).isoformat()})
    keep_exp = set(expiries[:PARITY_EXPIRIES])
    lo, hi = spot * (1 - PARITY_BAND_FRAC), spot * (1 + PARITY_BAND_FRAC)
    selected = [r for r in chain if r["expiration"] in keep_exp
                and r["strike"] is not None and lo <= r["strike"] <= hi]
    snaps = _snapshots(door, sorted({r["symbol"] for r in selected}))
    quotes, have = [], set()
    for row in sorted(selected, key=lambda r: r["symbol"]):
        snap = snaps.get(row["symbol"]) or {}
        if snap.get("bid") is None or snap.get("ask") is None:
            continue  # unquotable: the sleeve fails closed on it
        quotes.append({"symbol": row["symbol"], "expiration": row["expiration"],
                       "strike": row["strike"], "right": row["right"],
                       "bid": snap["bid"], "ask": snap["ask"]})
        have.add(row["symbol"])
    held_spy = [o for o in (held or [])
                if (parse_occ(o) or {}).get("root") == PARITY_UNDERLYING and o not in have]
    if held_spy:
        hsnaps = _snapshots(door, held_spy)
        for occ in held_spy:
            snap, parsed = hsnaps.get(occ) or {}, parse_occ(occ)
            if snap.get("bid") is not None and snap.get("ask") is not None and parsed:
                quotes.append({"symbol": occ, "expiration": parsed["expiration"],
                               "strike": parsed["strike"],
                               "right": "call" if parsed["cp"] == "C" else "put",
                               "bid": snap["bid"], "ask": snap["ask"]})
    return quotes


def build_simple_chains_quotes(door, sym, kind, lo, hi, ref):
    """(chain, quotes) for one underlying+kind+DTE window (master _simple_chains_quotes)."""
    chain = _contracts(door, sym, kind, ref, lo, hi)
    snaps = _snapshots(door, sorted({c["symbol"] for c in chain}))
    quotes = {}
    for occ, snap in snaps.items():
        if snap.get("bid") is not None and snap.get("ask") is not None:
            quotes[occ] = {"bid": snap["bid"], "ask": snap["ask"]}
    return chain, quotes


def fetch_vix_series():
    """Yahoo ^VIX daily closes [(date_iso, close)] — price only, the one
    sanctioned Yahoo use (master yahoo_vix_series). Failure -> []."""
    import urllib.request
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5y&interval=1d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as fh:
            doc = json.loads(fh.read())
        res = doc["chart"]["result"][0]
        out = []
        for ts_, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
            if c:
                out.append((datetime.fromtimestamp(ts_, tz=ET).date().isoformat(), float(c)))
        return out
    except Exception:
        return []


def traded_dates_from_bars(bars):
    """Sorted ET session dates present in SPY 1Hour bars — the spx_premium
    sleeve's own traded_dates definition (W-1 cure, shared by the adapter)."""
    out = set()
    for b in bars or []:
        t = b.t if hasattr(b, "t") else (b.get("t") if isinstance(b, dict) else None)
        if t is None:
            continue
        try:
            if isinstance(t, (int, float)):
                d = datetime.fromtimestamp(float(t), tz=timezone.utc).astimezone(ET).date()
            else:
                dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                d = dt.astimezone(ET).date()
            out.add(d.isoformat())
        except Exception:
            continue
    return sorted(out)


def held_occs_from_state(root):
    """OCC symbols with open positions in any sleeve journal under root/state."""
    occs = set()
    state = os.path.join(os.path.abspath(root), "state")
    if not os.path.isdir(state):
        return []
    from .journal import positions_from_journal
    from .models import is_option_symbol
    for name in sorted(os.listdir(state)):
        jp = os.path.join(state, name, "journal.jsonl")
        if os.path.exists(jp):
            try:
                for p in positions_from_journal(jp):
                    if is_option_symbol(p.get("symbol") or ""):
                        occs.add(p["symbol"])
            except Exception:
                continue
    return sorted(occs)


def warm_options(root, door=None, session=None, held_occs=None, vix_fetch=None):
    """Populate cache/options/{QQQ,SPY,VXX,XSP}/chain.json + VIX 1Day bars.

    Returns a summary dict of counts (never raises per section)."""
    root = os.path.abspath(root)
    cache = BarCache(os.path.join(root, "cache"))
    if door is None:
        from .alpaca_door import AlpacaDoor
        door = AlpacaDoor()
    try:
        ref = date.fromisoformat(session) if session else datetime.now(ET).date()
    except ValueError:
        ref = datetime.now(ET).date()
    if held_occs is None:
        held_occs = held_occs_from_state(root)
    summary = {}

    # QQQ ladder quotes (+ held QQQ OCCs appended in the same list shape)
    try:
        quotes = build_ladder_quotes(door, ref)
        have = {q["symbol"] for q in quotes}
        held_qqq = [o for o in held_occs if (parse_occ(o) or {}).get("root") == "QQQ" and o not in have]
        if held_qqq:
            snaps = _snapshots(door, held_qqq)
            for occ in held_qqq:
                snap = snaps.get(occ) or {}
                parsed = parse_occ(occ)
                if snap.get("bid") is not None and snap.get("ask") is not None and parsed:
                    quotes.append({"symbol": occ, "expiration": parsed["expiration"],
                                     "strike": parsed["strike"], "bid": snap["bid"],
                                     "ask": snap["ask"], "delta": snap.get("delta")})
        cache.write_options("QQQ", {"quotes": quotes})
        summary["QQQ"] = {"quotes": len(quotes)}
    except Exception as e:
        summary["QQQ"] = {"error": f"{type(e).__name__}: {e}"}

    # SPY parity window (DESIGNED-ORDER-LOGIC §4): box-spread chain for
    # free_opt_parity. Fail-closed: no cached SPY spot -> no window.
    try:
        spot = _spy_spot(cache)
        if spot is None:
            raise ValueError("no SPY spot in bar cache")
        quotes = build_parity_quotes(door, ref, spot, held=held_occs)
        cache.write_options("SPY", {"quotes": quotes})
        summary["SPY"] = {"quotes": len(quotes), "spot": spot}
    except Exception as e:
        summary["SPY"] = {"error": f"{type(e).__name__}: {e}"}

    # VXX / XSP simple chains+quotes (+ held OCC quotes merged for exit marks)
    for sym, kind, lo, hi in WINDOWS:
        try:
            chain, quotes = build_simple_chains_quotes(door, sym, kind, lo, hi, ref)
            held = [o for o in held_occs if (parse_occ(o) or {}).get("root") == sym and o not in quotes]
            if held:
                for occ, snap in _snapshots(door, held).items():
                    if snap.get("bid") is not None and snap.get("ask") is not None:
                        quotes[occ] = {"bid": snap["bid"], "ask": snap["ask"]}
            cache.write_options(sym, {"chains": {sym: chain}, "quotes": quotes})
            summary[sym] = {"chain": len(chain), "quotes": len(quotes)}
        except Exception as e:
            summary[sym] = {"error": f"{type(e).__name__}: {e}"}

    # Held OCCs under any other root: quotes-only payload so exits can mark.
    other = {}
    for occ in held_occs:
        r = (parse_occ(occ) or {}).get("root")
        if r and r not in ("QQQ", "VXX", "XSP", "SPY"):
            other.setdefault(r, []).append(occ)
    for r, occs in other.items():
        try:
            quotes = {}
            for occ, snap in _snapshots(door, occs).items():
                if snap.get("bid") is not None and snap.get("ask") is not None:
                    quotes[occ] = {"bid": snap["bid"], "ask": snap["ask"]}
            existing = cache.read_options(r) or {}
            existing["quotes"] = {**(existing.get("quotes") or {}), **quotes}
            cache.write_options(r, existing)
            summary[r] = {"held_quotes": len(quotes)}
        except Exception as e:
            summary[r] = {"error": f"{type(e).__name__}: {e}"}

    # GAP-CURE generic windows: bilbo 20-name universe, iron_condor
    # 13-name watchlist, capitulation_options basket_41 — chains+quotes
    # in the {chains, quotes} shape their adapters/sleeves read, plus a
    # per-underlying IV observation ledger (one obs per session, the
    # sleeve's documented "stored IV observations").
    try:
        from sleeves.bilbo_options import UNIVERSE as _BILBO
        from sleeves.iron_condor import WATCHLIST as _IRON
        import json as _json
        _uni = json.load(open(os.path.join(root, "config", "universes.json")))
        _generic = sorted(set(_BILBO) | set(_IRON) | set(_uni.get("basket_41") or []))
    except Exception:
        _generic = []
    for sym in _generic:
        try:
            chain_all, quotes_all = [], {}
            for kind in ("call", "put"):
                ch, qu = build_simple_chains_quotes(door, sym, kind, 0, 62, ref)
                chain_all.extend(ch); quotes_all.update(qu)
            existing = cache.read_options(sym) or {}
            merged_q = dict(existing.get("quotes") or {}) if isinstance(existing.get("quotes"), dict) else {}
            merged_q.update(quotes_all)
            cache.write_options(sym, {"chains": {sym: chain_all}, "quotes": merged_q})
            summary[sym] = {"chain": len(chain_all), "quotes": len(quotes_all)}
            # IV ledger: near-ATM call snapshot iv for this session.
            spot = None
            bb = cache.read_bars(sym, "1Day", 1)
            if bb: spot = _f(bb[-1].c)
            iv_obs = None
            if spot:
                cand = [r for r in chain_all if r.get("strike")]
                if cand:
                    near = min(cand, key=lambda r: abs(r["strike"] - spot))
                    iv_obs = (quotes_all.get(near["symbol"]) or {})
                    # quotes_all has no iv; use snapshot iv via _snapshots
                    snap_iv = _snapshots(door, [near["symbol"]]).get(near["symbol"]) or {}
                    iv_obs = snap_iv.get("iv")
            if iv_obs:
                prev = cache.read_iv(sym) or {}
                hist = [h for h in (prev.get("history") or []) if h.get("date") != ref.isoformat()]
                hist.append({"date": ref.isoformat(), "iv": float(iv_obs)})
                cache.write_iv(sym, {"current": float(iv_obs), "history": hist[-260:]})
        except Exception as e:
            summary[sym] = {"error": f"{type(e).__name__}: {e}"}

    # VIX daily closes (sanctioned Yahoo price-only exception)
    try:
        series = (vix_fetch or fetch_vix_series)() or []
        bars = [Bar(t=f"{d}T04:00:00Z", o=c, h=c, l=c, c=c, v=0) for d, c in series]
        summary["VIX/1Day"] = cache.write_bars("VIX", "1Day", bars)
    except Exception as e:
        summary["VIX/1Day"] = {"error": f"{type(e).__name__}: {e}"}
    return summary
