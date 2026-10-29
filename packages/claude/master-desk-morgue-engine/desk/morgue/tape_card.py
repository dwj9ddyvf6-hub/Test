"""THE TAPE: today's option prints of SPY, QQQ and IWM scored print by print, aggregated per underlying (postclose card).

The scorers are tape.py (Heat Score with the Unusual / Top Position / Golden Sweep tags, the 1.005x side reclassification,
the Algo Score tallies on the buys-only intake AND on all prints, so the intake bias is measured). This module is the
aggregation and the reads.

Declared approximations, carried on the card as labels:
- the side is signed against the LATEST quote of the contract (Alpaca serves no historical NBBO for options: the quotes
  history endpoint answers 404), so a quick-moving contract's early prints can be mis-signed; `signed_share` says how
  many prints a two-sided quote could sign at all, and mid and unknown prints stay neutral;
- the Heat baselines are point-in-time expanding means over the contract's own earlier prints that day; avg_oi is the
  underlying's chain-mean open interest;
- the page cap: a batch of contracts stops at PAGE_CAP pages; `batches_capped` counts them.

Every contract is processed on its own, in time order: the baselines, the running volume and the opening-or-closing
heuristic are per contract, so reading the prints grouped by contract gives the same scores as one global sort and holds
one contract's prints in memory at a time."""
import math
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..terminal import optnews as on
from . import bs, flow, no_data, stamp, tape
from .map_gex import chain_of

SOURCE = "Alpaca option trades and quotes"
DELAY = "the session's prints to the run; the side is signed against the latest quote"
MAX_DTE = 45
BATCH = 200
PAGE_CAP = 10
PAGE_LIMIT = 10_000
MAX_REQUESTS = 600                         # a run's trade requests, all underlyings: polite and bounded
ALERTS = 25
LABELS = [
    "side: signed against the latest quote (the options feed has no quote history); mid and unknown prints stay neutral",
    "heat baselines: point-in-time expanding means over the contract's own earlier prints that day; avg_oi is the chain mean",
    "algo ratio tallies are scaled x10 (the desk's choice); the buys-only variant is the vendor's intake, both are shown",
    "multi-leg prints count in the totals and not in the net premium; cancelled prints are excluded entirely",
    "opening or closing: asserted only where the day's numbers force it (volume above open interest; a bid-side print "
    "offset by earlier ask-side volume); otherwise unclear",
]


def session_start_iso(day):
    """the regular session's open as a Zulu time (13:30 in summer, 14:30 in winter), from the desk's calendar"""
    return datetime.fromtimestamp(cal.session_open(day), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def score_contract(prints, c, spot, quote, hi52, lo52, avg_oi, today, agg, alerts, hist=None, sink=None):
    """score one contract's prints (ascending by time) into the aggregate `agg`; alert candidates go to `alerts`.
    c: {"symbol","strike","expiry","is_call","oi"}; quote: {"bid","ask"}; returns the contract's (volume, prints).
    sink: a list that receives each scored print as flow.signed_print's dict (the flow reads' input)."""
    n = prem_sum = size_sum = 0
    day_vol = ask_vol = bid_vol = 0.0
    dte = (date.fromisoformat(c["expiry"]) - today).days
    otm = (max(0.0, (c["strike"] - spot) / spot * 100.0) if c["is_call"]
           else max(0.0, (spot - c["strike"]) / spot * 100.0))
    for r in prints:
        cond = r.get("c")
        if tape.is_cancel(cond):
            agg["cancelled_excluded"] += 1
            continue
        try:
            price, size = float(r["p"]), int(r["s"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (price > 0 and size > 0 and math.isfinite(price)):
            continue
        premium = price * size * 100.0
        if sink is not None:
            sp = flow.signed_print(r, c, spot, quote, today)
            if sp is not None:
                sink.append(sp)
        day_vol += size
        base = {"avg_premium": (prem_sum / n) if n else None, "avg_size": (size_sum / n) if n else None,
                "avg_oi": avg_oi}
        p = {"premium": premium, "dte": dte, "sweep": tape.is_sweep(cond), "size": size, "otm_pct": otm,
             "oi": c["oi"]}
        heat, _ = tape.heat_score(p, base)
        tg = tape.tags(p)
        side = tape.classify_side(price, quote.get("bid"), quote.get("ask"))
        sign = tape.directional_sign(side, c["is_call"])
        algo, _ = tape.algo_score(p, {"day_volume": day_vol, "oi": c["oi"], "spot": spot, "hi52": hi52, "lo52": lo52})
        oc = tape.open_close(size, day_vol, c["oi"], ask_vol, bid_vol, side)
        agg["prints"] += 1
        agg["total_premium"] += premium
        agg["heat_sum"] += heat
        agg["algo_all_sum"] += algo
        agg["algo_all_n"] += 1
        if side != "unknown":
            agg["signed"] += 1
        if tape.buys_only_intake(side):
            agg["algo_buys_only_sum"] += algo
            agg["algo_buys_only_n"] += 1
        if oc == "likely_opening":
            agg["opening"] += 1
        elif oc == "likely_closing":
            agg["closing"] += 1
        if tape.is_multileg(cond):
            agg["multileg_prints"] += 1
        else:
            agg["net_premium"] += sign * premium
            agg["call_net_premium" if c["is_call"] else "put_net_premium"] += sign * premium
        if tg["golden_sweep"]:
            agg["golden_sweeps"] += 1
        if heat >= tape.HIGH_HEAT:
            agg["high_heat"] += 1
        if tg["golden_sweep"] or heat >= tape.HIGH_HEAT:
            alerts.append({"ts": str(r.get("t") or ""), "contract": c["symbol"], "kind": "call" if c["is_call"] else "put",
                           "strike": c["strike"], "expiry": c["expiry"], "dte": dte, "size": size, "price": round(price, 4),
                           "premium_usd": round(premium, 2), "heat": round(heat, 2), "algo": round(algo, 2),
                           "side": side, "sentiment": tape.sentiment(side, c["is_call"]), "sweep": p["sweep"],
                           "golden_sweep": tg["golden_sweep"], "unusual": tg["unusual"],
                           "top_position": tg["top_position"], "opening": oc,
                           "size_oi": (round(size / c["oi"], 3) if c["oi"] else None)})
        if side in tape.ASK_SIDES:
            ask_vol += size
        elif side in tape.BID_SIDES:
            bid_vol += size
        n += 1
        prem_sum += premium
        size_sum += size
    return day_vol, n


def new_agg():
    return {"prints": 0, "signed": 0, "cancelled_excluded": 0, "multileg_prints": 0, "total_premium": 0.0,
            "net_premium": 0.0, "call_net_premium": 0.0, "put_net_premium": 0.0, "golden_sweeps": 0, "high_heat": 0,
            "heat_sum": 0.0, "algo_buys_only_sum": 0.0, "algo_buys_only_n": 0, "algo_all_sum": 0.0, "algo_all_n": 0,
            "opening": 0, "closing": 0}


def card_of(underlying, spot, agg, alerts, as_of, contracts_in_scope, capped, hi52, lo52):
    """the contract's morgue.tape.cards.* object from the aggregate"""
    if not agg["prints"]:
        return no_data("no scoreable print in the window", as_of, SOURCE, DELAY, spot=round(spot, 2),
                       contracts_in_scope=contracts_in_scope, batches_capped=capped)
    alerts = sorted(alerts, key=lambda a: -a["premium_usd"])[:ALERTS]
    n = agg["prints"]
    return stamp(
        "ok", as_of, SOURCE, DELAY, spot=round(spot, 2), prints=n, signed_share=round(agg["signed"] / n, 3),
        cancelled_excluded=agg["cancelled_excluded"], multileg_prints=agg["multileg_prints"],
        total_premium_usd=round(agg["total_premium"], 2), net_premium_usd=round(agg["net_premium"], 2),
        call_net_premium_usd=round(agg["call_net_premium"], 2), put_net_premium_usd=round(agg["put_net_premium"], 2),
        golden_sweeps=agg["golden_sweeps"], high_heat=agg["high_heat"], mean_heat=round(agg["heat_sum"] / n, 2),
        mean_algo_all=(round(agg["algo_all_sum"] / agg["algo_all_n"], 2) if agg["algo_all_n"] else None),
        mean_algo_buys_only=(round(agg["algo_buys_only_sum"] / agg["algo_buys_only_n"], 2)
                             if agg["algo_buys_only_n"] else None),
        opening_prints=agg["opening"], closing_prints=agg["closing"], contracts_in_scope=contracts_in_scope,
        batches_capped=capped, week52_hi=(None if hi52 is None else round(hi52, 2)),
        week52_lo=(None if lo52 is None else round(lo52, 2)), week52_context=tape.week52_context(spot, hi52, lo52),
        alerts=alerts)


# ---- the reads --------------------------------------------------------------------------------------------------------

def read_chain(client, underlying, today, go=None):
    """(chain, quotes, whole): the underlying's contracts to MAX_DTE days with open interest, and each contract's latest
    quote from the chain snapshots"""
    from ..venues.alpaca import DATA
    lte = (today + timedelta(days=MAX_DTE)).isoformat()
    contracts, c_whole = client.paged("/v2/options/contracts", {
        "underlying_symbols": underlying, "status": "active", "expiration_date_gte": today.isoformat(),
        "expiration_date_lte": lte, "limit": 10000}, "option_contracts", go=go, max_pages=30)
    snaps, s_whole = client.paged("/v1beta1/options/snapshots/" + underlying, {
        "feed": "indicative", "expiration_date_gte": today.isoformat(), "expiration_date_lte": lte, "limit": 1000},
        "snapshots", host=DATA, go=go, max_pages=60)
    chain, _ = chain_of(contracts or [], underlying, keep_empty=True)
    quotes = {r["symbol"]: {"bid": r["bid"], "ask": r["ask"], "iv": r["iv"]} for r in on.rows_of(underlying, snaps or {})}
    return chain, quotes, bool(c_whole and s_whole)


def read_trades(client, symbols, start_iso, go=None, budget=None):
    """{OCC: [prints ascending]} and the number of capped batches. `budget` is a one-item list holding the requests
    still allowed; reading stops when it is spent (the batches left are counted as capped)."""
    from ..venues.alpaca import DATA
    out, capped = {}, 0
    for i in range(0, len(symbols), BATCH):
        batch = symbols[i:i + BATCH]
        if budget is not None and budget[0] <= 0:
            capped += 1
            continue
        pages = 0
        token = None
        while True:
            if go is not None and not go():
                capped += 1
                break
            r = client._get("/v1beta1/options/trades", {"symbols": ",".join(batch), "start": start_iso,
                                                          "limit": PAGE_LIMIT, "sort": "asc", "page_token": token},
                            host=DATA) or {}
            pages += 1
            if budget is not None:
                budget[0] -= 1
            for occ, rows in (r.get("trades") or {}).items():
                out.setdefault(occ, []).extend(rows or [])
            token = r.get("next_page_token")
            if not token:
                break
            if pages >= PAGE_CAP or (budget is not None and budget[0] <= 0):
                capped += 1
                break
    return out, capped


def build_card(client, underlying, today, now, spot, hi52, lo52, go=None, budget=None):
    """one underlying's tape card -> (card, info); never raises (a failure is the card's no_data reason)"""
    as_of = today.isoformat()
    try:
        chain, quotes, whole = read_chain(client, underlying, today, go)
        if not chain:
            return no_data("no contract in the window" if whole else "the contracts read was cut short",
                           as_of, SOURCE, DELAY, spot=round(spot, 2)), {}
        by_sym = {c["symbol"]: c for c in chain}
        trades, capped = read_trades(client, [c["symbol"] for c in chain], session_start_iso(today), go, budget)
        with_oi = [c["oi"] for c in chain if c["oi"] > 0]
        avg_oi = (sum(with_oi) / len(with_oi)) if with_oi else None
        agg, alerts, sink = new_agg(), [], []
        for occ, rows in trades.items():
            c = by_sym.get(occ)
            if c is None or not rows:
                continue
            rows.sort(key=lambda r: str(r.get("t") or ""))
            score_contract(rows, c, spot, quotes.get(occ) or {}, hi52, lo52, avg_oi, today, agg, alerts, sink=sink)
        card = card_of(underlying, spot, agg, alerts, as_of, len(chain), capped, hi52, lo52)
        return card, {"capped": capped, "prints": agg["prints"], "spot": spot, "signed": sink, "deltas": deltas_of(chain, quotes, spot, now, underlying)}
    except Exception as e:                                          # noqa: BLE001
        return no_data(f"{type(e).__name__}: {str(e)[:120]}", as_of, SOURCE, DELAY), {}


def deltas_of(chain, quotes, spot, now, underlying):
    """{OCC: delta} from each contract's implied volatility (Black-Scholes, the Map's rate and dividend yield); a contract with
    no usable IV has none, and HIRO counts the prints it drops"""
    from .map_gex import DIV_YIELD, t_years
    div = DIV_YIELD.get(underlying, 0.0)
    when = datetime.fromtimestamp(float(now), tz=timezone.utc)
    out = {}
    for c in chain:
        iv = (quotes.get(c["symbol"]) or {}).get("iv")
        if iv and 0 < iv <= on.MAX_IV:
            out[c["symbol"]] = bs.delta(spot, c["strike"], t_years(c["expiry"], when), iv, c["is_call"], bs.RATE, div)
    return out


def range52(bars):
    """(high, low) over the last 252 completed sessions of daily bars, or (None, None)"""
    b = [x for x in (bars or [])[-252:] if x.get("h") and x.get("l")]
    return (max(x["h"] for x in b), min(x["l"] for x in b)) if len(b) >= 60 else (None, None)
