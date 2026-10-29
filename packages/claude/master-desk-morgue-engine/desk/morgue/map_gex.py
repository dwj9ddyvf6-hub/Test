"""THE MAP, gamma: the dealer gamma exposure of SPY, QQQ and IWM by SpotGamma's published construction.

Per-contract dollar GEX per 1% move = gamma x signed open interest x 100 x spot^2 x 0.01, calls +, puts -. The sign is the
vendor's published convention about dealer inventory (dealers long the calls, short the puts): a modelling assumption,
not an observation, and every card says so.

Data (Alpaca, through the desk's client and its pacing): /v2/options/contracts for open interest, with an EXPLICIT
730-day expiry window (the endpoint's default window is about one week: found live 2026-10-26, five expiries), and the
indicative snapshots of the chain for gamma and IV. A contract's gamma is the snapshot's, else Black-Scholes on its IV
(dividend yield per fund); a contract with neither is dropped and counted (contracts_used of chain_total).

Reuse, not duplication: the contract parsing is desk/terminal/optnews (oi_of, rows_of), the per-contract GEX formula is
desk/terminal/strip.contract_gex (one definition of the convention), the OCC parser is desk/data/options.

The walls are the strip's definition and Muse's alike (checked against the code, which the teardown had read the other
way round): the strike with the most call gamma, the strike with the most put gamma. The strip prices every contract's
gamma from its IV; this Map takes Alpaca's gamma first. Both are shown as they are; neither is renamed the other."""
import math
from datetime import date, datetime, timedelta, timezone

from ..data.options import occ_parse
from ..terminal import optnews as on
from ..terminal import strip
from . import bs

DIV_YIELD = {"SPY": 0.013, "QQQ": 0.005, "IWM": 0.014}
WINDOW_DAYS = 730
GRID_LO, GRID_HI, GRID_STEP = 0.80, 1.20, 0.0025
MAX_CONTRACT_PAGES = 30                    # 10,000 a page: SPY's 730-day chain is about 13,000
MAX_SNAP_PAGES = 120                       # 1,000 a page
LABEL = ("modelled, convention-signed (calls positive, puts negative), prior-close open interest: an assumption about "
         "dealer inventory, not an observation")
METHOD = ("SpotGamma's published convention; Alpaca greeks, else Black-Scholes on the contract's implied volatility; "
          "open interest from the prior close; the flip re-prices the contracts that carry an implied volatility")
SOURCE = "Alpaca option contracts and indicative snapshots"
DELAY = "prior-close open interest; snapshot greeks as of the run"


def contract_gex(g, oi, spot, is_call):
    """dollar gamma per 1% move of one contract (strip.contract_gex is the single definition)"""
    return strip.contract_gex(g, oi, spot, "call" if is_call else "put")


def chain_of(contracts, underlying, keep_empty=False):
    """Alpaca's contracts -> [{"symbol","strike","expiry","is_call","oi"}] for the underlying's own standard contracts
    with open interest (an adjusted contract delivers something else: another root), plus the latest open-interest date.
    keep_empty: also the contracts with no open interest yet (a strike listed this week trades today and has none): the
    Tape reads them with oi 0, the Map has no gamma to weigh them by"""
    out, oi_day = [], None
    for occ, c in on.oi_of(contracts).items():
        if c.get("underlying") != underlying or c.get("root") != underlying.replace(".", ""):
            continue
        if c.get("strike") is None or (not keep_empty and (not c.get("oi") or c["oi"] <= 0)):
            continue
        try:
            _root, exp, cp, _k = occ_parse(occ)
            date.fromisoformat(exp)
        except (ValueError, IndexError, TypeError, AttributeError):
            continue
        out.append({"symbol": occ, "strike": float(c["strike"]), "expiry": exp, "is_call": cp == "call",
                    "oi": float(c.get("oi") or 0.0)})
        if isinstance(c.get("date"), str) and (oi_day is None or c["date"] > oi_day):
            oi_day = c["date"]
    return out, oi_day


def snaps_of(underlying, snapshots):
    """Alpaca's snapshots {OCC: snapshot} -> {OCC: {"gamma","iv"}} (optnews.rows_of: the name's own root only)"""
    return {r["symbol"]: {"gamma": r["gamma"], "iv": r["iv"]} for r in on.rows_of(underlying, snapshots)}


def volumes_of(underlying, snapshots):
    """Alpaca's snapshots {OCC: snapshot} -> {OCC: the daily bar's volume} for the own root (the flow-GEX weight; the bar is
    the latest session's, so before the open it is yesterday's)"""
    return {r["symbol"]: r["volume"] for r in on.rows_of(underlying, snapshots) if r.get("volume") is not None}


def t_years(expiry, now):
    """years to the 16:00 ET (21:00 UTC) expiry, never under one day (an expiring contract still carries gamma)"""
    exp = datetime.combine(date.fromisoformat(expiry), datetime.min.time(), tzinfo=timezone.utc).replace(hour=21)
    return max((exp - now).total_seconds() / 86400.0, 1.0) / 365.0


def gex_profile(chain, snaps, spot, underlying, now, weight="oi", volumes=None):
    """Aggregate the static GEX suite for one underlying at the spot -> the numbers (no labels, no I/O).
    weight "oi" is the Map's static form; weight "volume" (Tradytics' intraday flow-GEX, REA A66/A47) weighs each contract
    by its daily volume from `volumes` {OCC: volume} instead of its open interest, a contract with no volume dropped."""
    div = DIV_YIELD.get(underlying, 0.0)
    by_strike, by_expiry, call_by, put_by = {}, {}, {}, {}
    net, used = 0.0, []
    for c in chain:
        sn = snaps.get(c["symbol"]) or {}
        g, iv = sn.get("gamma"), sn.get("iv")
        t = t_years(c["expiry"], now)
        if g is None and iv and 0 < iv <= on.MAX_IV:
            g = bs.gamma(spot, c["strike"], t, iv, bs.RATE, div)
        if g is None or not math.isfinite(g):
            continue
        w = c["oi"] if weight == "oi" else (volumes or {}).get(c["symbol"])
        if w is None or not math.isfinite(w):
            continue
        val = contract_gex(float(g), w, spot, c["is_call"])
        net += val
        by_strike[c["strike"]] = by_strike.get(c["strike"], 0.0) + val
        by_expiry[c["expiry"]] = by_expiry.get(c["expiry"], 0.0) + val
        tgt = call_by if c["is_call"] else put_by
        tgt[c["strike"]] = tgt.get(c["strike"], 0.0) + abs(val)
        used.append({**c, "oi": w, "gamma": float(g), "iv": iv, "t": t})
    call_wall = max(call_by, key=call_by.get) if call_by else None
    put_wall = max(put_by, key=put_by.get) if put_by else None
    flip = zero_gamma(used, spot, div)
    return {"underlying": underlying, "spot": spot, "net_gex": net, "call_wall": call_wall, "put_wall": put_wall,
            "zero_gamma": flip, "by_strike": by_strike, "by_expiry": by_expiry, "call_by_strike": call_by,
            "put_by_strike": put_by, "contracts_used": len(used), "chain_total": len(chain)}


def zero_gamma(used, spot, div, lo=GRID_LO, hi=GRID_HI, step=GRID_STEP):
    """the spot where the re-priced chain's net gamma crosses zero, the crossing nearest the spot: every contract with
    an IV is re-priced with Black-Scholes on a grid of 0.80-1.20 x spot in 0.25% steps (its own IV held fixed), the
    crossing found by linear interpolation. None when the grid has no sign change (flip_reason says so on the card)."""
    priced = [(c["strike"], c["t"], c["iv"], c["oi"], c["is_call"]) for c in used if c.get("iv")]
    if not priced:
        return None

    def total(s):
        tot = 0.0
        for k, t, iv, oi, is_call in priced:
            tot += contract_gex(bs.gamma(s, k, t, iv, bs.RATE, div), oi, s, is_call)
        return tot
    n = int(round((hi - lo) / step))
    grid = []
    for i in range(n + 1):
        s = spot * (lo + i * step)
        grid.append((s, total(s)))
    best = None
    for (s0, v0), (s1, v1) in zip(grid, grid[1:]):
        if v0 == 0.0:
            cand = s0
        elif v0 * v1 < 0:
            cand = s0 + (s1 - s0) * abs(v0) / (abs(v0) + abs(v1))
        else:
            continue
        if best is None or abs(cand - spot) < abs(best - spot):
            best = cand
    return best


def _r(x, k=4):
    return None if x is None else round(x, k)


def card_of(prof, as_of, oi_day, spot_source, expiries, now):
    """the Map card (the contract's morgue.map.cards.*) from the profile; the by-strike profile of the sidecar is
    sidecar_of's. A profile with no contract is no_data with the reason."""
    from . import stamp
    spot = prof["spot"]
    if not prof["contracts_used"]:
        return stamp("no_data", as_of, SOURCE, DELAY, f"none of {prof['chain_total']} contracts carried a gamma or an "
                     "implied volatility", spot=_r(spot, 2), spot_source=spot_source, contracts_used=0,
                     chain_total=prof["chain_total"])
    net, flip = prof["net_gex"], prof["zero_gamma"]
    top = sorted(prof["by_strike"].items(), key=lambda kv: -abs(kv[1]))[:8]
    exp = sorted(prof["by_expiry"].items(), key=lambda kv: -abs(kv[1]))[:8]
    cw, pw = prof["call_wall"], prof["put_wall"]
    card = stamp("ok", as_of, SOURCE, DELAY, spot=_r(spot, 2), spot_source=spot_source, net_gex_b=_r(net / 1e9, 3),
                 regime="Dampening" if net > 0 else "Amplifying", call_wall=cw, put_wall=pw,
                 flip=_r(flip, 2), flip_distance_pct=(None if flip is None else _r((flip - spot) / spot * 100.0, 2)),
                 call_wall_pct=(None if cw is None else _r((cw / spot - 1) * 100.0, 2)),
                 put_wall_pct=(None if pw is None else _r((pw / spot - 1) * 100.0, 2)),
                 contracts_used=prof["contracts_used"], chain_total=prof["chain_total"],
                 coverage_pct=_r(prof["contracts_used"] / max(prof["chain_total"], 1) * 100.0, 1), oi_date=oi_day,
                 expiries=expiries,
                 top_strikes=[{"strike": k, "gex_b": _r(v / 1e9, 3)} for k, v in top],
                 by_expiry=[{"expiry": k, "gex_b": _r(v / 1e9, 3)} for k, v in exp], method=METHOD)
    if flip is None:
        card["flip_reason"] = "no zero crossing within 20% of the price"
    return card


def sidecar_of(prof, band=0.12):
    """the by-strike and by-expiry profile for morgue-map.json: strikes within 12% of the spot (GEX tiles and charts)"""
    spot = prof["spot"]
    strikes = []
    for k in sorted(prof["by_strike"]):
        if abs(k / spot - 1) > band:
            continue
        c, p = prof["call_by_strike"].get(k, 0.0), -prof["put_by_strike"].get(k, 0.0)
        strikes.append({"strike": k, "call_gex_b": _r(c / 1e9, 4), "put_gex_b": _r(p / 1e9, 4),
                        "net_gex_b": _r(prof["by_strike"][k] / 1e9, 4)})
    return {"spot": _r(spot, 2), "strikes": strikes,
            "expiries": [{"expiry": k, "gex_b": _r(v / 1e9, 4)} for k, v in sorted(prof["by_expiry"].items())]}


# ---- the reads --------------------------------------------------------------------------------------------------------

def read_chain(client, underlying, today, go=None):
    """(contracts, contracts_whole, snapshots, snapshots_whole) of the underlying's 730-day chain through the desk's
    Alpaca client (paged, paced, its three tries): the contracts on the trading host, the snapshots on the data host"""
    lte = (today + timedelta(days=WINDOW_DAYS)).isoformat()
    contracts, c_whole = client.paged("/v2/options/contracts", {
        "underlying_symbols": underlying, "status": "active", "expiration_date_gte": today.isoformat(),
        "expiration_date_lte": lte, "limit": 10000}, "option_contracts", go=go, max_pages=MAX_CONTRACT_PAGES)
    from ..venues.alpaca import DATA
    snaps, s_whole = client.paged("/v1beta1/options/snapshots/" + underlying, {
        "feed": "indicative", "expiration_date_gte": today.isoformat(), "expiration_date_lte": lte, "limit": 1000},
        "snapshots", host=DATA, go=go, max_pages=MAX_SNAP_PAGES)
    return contracts or [], bool(c_whole), snaps or {}, bool(s_whole)


def read_spot(client, underlying, close=None):
    """(price, source): the last trade (SIP first, IEX when the plan refuses SIP: Muse found sip 403s on recent data),
    else the cached prior close; (None, reason) when none"""
    for feed in ("sip", "iex"):
        try:
            got = client.stock_trades_latest([underlying], feed=feed) or {}
        except Exception:                                           # noqa: BLE001  (the next feed or the close serves)
            continue
        p = (got.get(underlying) or {}).get("p")
        try:
            p = float(p)
        except (TypeError, ValueError):
            p = None
        if p and p > 0 and math.isfinite(p):
            return p, f"last trade ({feed.upper()})"
    if close and close > 0:
        return float(close), "prior close (cache)"
    return None, "no trade and no cached close"


def build_card(client, underlying, today, now, close=None, go=None):
    """one underlying's card and sidecar profile from the live reads -> (card, sidecar or None, extra)
    Never raises: a refusal or an empty chain is the card's no_data reason."""
    from . import no_data
    as_of = today.isoformat()
    try:
        spot, spot_src = read_spot(client, underlying, close)
        if spot is None:
            return no_data(spot_src, as_of, SOURCE, DELAY), None, {}
        contracts, c_whole, snaps, s_whole = read_chain(client, underlying, today, go)
        if not (c_whole and s_whole):
            # half a chain misplaces the walls and the flip: it is no card (the gate closes at the open's window, 09:25 ET)
            return no_data("the chain read was cut short (the open's window or the page cap): a partial chain would "
                           "misplace the walls and the flip", as_of, SOURCE, DELAY, spot=_r(spot, 2),
                           spot_source=spot_src), None, {}
        chain, oi_day = chain_of(contracts, underlying)
        if not chain:
            return no_data("no contract with open interest", as_of, SOURCE, DELAY, spot=_r(spot, 2),
                           spot_source=spot_src), None, {}
        when = datetime.fromtimestamp(float(now), tz=timezone.utc)
        sn = snaps_of(underlying, snaps)
        prof = gex_profile(chain, sn, spot, underlying, when)
        card = card_of(prof, as_of, oi_day, spot_src, len({c["expiry"] for c in chain}), now)
        # the chain itself, for the extended reads (opt_ext, flow_card): the same rows the card was built from
        return card, (sidecar_of(prof) if card["status"] == "ok" else None), {
            "profile_net": prof["net_gex"], "chain": chain, "snaps": sn, "volumes": volumes_of(underlying, snaps),
            "spot": spot, "oi_date": oi_day, "profile": prof}
    except Exception as e:                                          # noqa: BLE001  (one fund's failure is its card's)
        return no_data(f"{type(e).__name__}: {str(e)[:120]}", as_of, SOURCE, DELAY), None, {}
