"""THE BOARD, daily card: the confluence8 aggregation over the genome roster (preopen, completed sessions only).

Ported from Silicon's board_card.py with these changes, each tested:
  - bars come from the desk's split-adjusted daily cache (hub.bars("equity_split", "1d", ..., cache_only=True), kept
    fresh by the genome job), not a second 580-day SIP download of 1,838 names;
  - the forming session is never read (a bar dated today is dropped until its close plus the cache's 20 minutes);
  - sectors come from SEC SIC codes mapped to the 11 sector funds (sectors.py: the desk has no GICS file; the sector
    and industry leaves are marked as built on SIC), not from a GICS file on another machine;
  - the institutional leaves arrive from the bundle the morgue_inst job wrote (state/morgue/inst_bundle.json), each with
    its own source / as-of / delay; no network inside the scoring loop;
  - the summary's `generated_at` was the START date of the fetch in Silicon (a labelling defect): here it is the time of
    the build;
  - liquidity is capacity, not a filter: every name that scores is on the board, dollar volume is shown beside it. The
    vendor's Qualify gate (ADV above 500,000 shares and $5M among its inputs) stays as the `qualified` cohort label and
    is not applied to what is listed.
The pure functions take bars and context; run() in cycle.py does the I/O."""
import math
import statistics

from .. import calendar as cal
from . import board, board_features as bf

SECTOR_ETF = {"Information Technology": "XLK", "Health Care": "XLV", "Financials": "XLF",
              "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE", "Materials": "XLB",
              "Industrials": "XLI", "Real Estate": "XLRE", "Communication Services": "XLC", "Utilities": "XLU"}
BENCH = ("SPY", "QQQ", "IWM") + tuple(sorted(set(SECTOR_ETF.values())))
BARS = 420                      # sessions read per name: EMA200, the 12-1 momentum (253) and the weekly stage (40 weeks)
TOP = 50
SOURCE = "Desk daily bars (split-adjusted) and the Morgue institutional bundle"
DELAY = "completed sessions only; refreshed before the open"
LABELS = [
    "category weights and the gate: Leadr's confluence8 configuration, as shipped",
    "the 0-100 transform of each leaf: the desk's own, from the vendor's published measure of it",
    "sector and industry leaves are built on SEC SIC codes mapped to the 11 sector funds; a name without a SIC has none",
    "liquidity is shown as capacity, not used as a filter; the gate's Qualify step is a cohort label",
    "dealer positioning and dark pool have no free route and stay no-data; a category scores from the leaves it has "
    "and shows how many",
]


def to_bars(raw, today, now):
    """the hub's daily bars [{"t","o","h","l","c","v"}] -> the board's bars [{"d": date, ...}], ascending, completed
    sessions only: a bar dated today is kept only once the session's close plus 20 minutes has passed"""
    out = []
    for b in raw or []:
        try:
            d = cal._as_date(float(b["t"]))
            o, h, lo, c, v = (float(b[k]) for k in ("o", "h", "l", "c", "v"))
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(x) for x in (o, h, lo, c, v)) or c <= 0 or h < lo:
            continue
        if d >= today and now < cal.session_close(d) + 20 * 60:
            continue
        if out and d <= out[-1]["d"]:
            continue                                        # one bar a session, ascending
        out.append({"d": d, "o": o, "h": h, "l": lo, "c": c, "v": v})
    return out


def aligned(bench_by_date, bars):
    """the benchmark's closes on the name's dates (carried forward over a gap); [] when under 95% of the dates match"""
    out, last, hits = [], None, 0
    for b in bars:
        val = bench_by_date.get(b["d"])
        if val is not None:
            last, hits = val, hits + 1
        out.append(last if last is not None else float("nan"))
    if hits < 0.95 * len(bars):
        return []
    return out


def _peer_rank(sym, g, industries, blends):
    group = industries.get(g.get("sub_industry"), [])
    if len(group) < 5:
        group = industries.get(g.get("sector"), [])
    return board.pct_rank({m: blends[m] for m in group if m in blends}, sym)


def market_context(feats, universe, spy):
    """the market leaves, one set for all names (Silicon's _market_context)"""
    c = [b["c"] for b in spy["bars"]]
    e20, e50, e200 = (board.ema_series(c, n) for n in (20, 50, 200))
    above = sum(1 for e in (e20, e50, e200) if e and c[-1] > e[-1])
    rets = [(c[i] / c[i - 1] - 1) * 100 for i in range(len(c) - 20, len(c))]
    rv = statistics.pstdev(rets) * (252 ** 0.5)
    regime = above / 3 * 60 + (20 if e50 and e50[-1] > e50[-6] else 0) + board.lin(rv, 35, 15) * 0.2
    names = [feats[s] for s in universe if s in feats]
    adv_share = (sum(1 for f in names if f["close"] > f["prev_close"]) / len(names) * 100) if names else None
    ema_share = (sum(1 for f in names if f["ema50"] and f["close"] > f["ema50"]) / len(names) * 100) if names else None
    breadth = (statistics.mean([x for x in (adv_share, ema_share) if x is not None]) if adv_share is not None else None)
    v = [b["v"] for b in spy["bars"]]
    up = [v[i] for i in range(len(c) - 20, len(c)) if c[i] > c[i - 1]]
    dn = [v[i] for i in range(len(c) - 20, len(c)) if c[i] < c[i - 1]]
    accdist = (board.lin(statistics.mean(up) / statistics.mean(dn), 0.6, 1.8) if up and dn else None)
    bo = bo_held = 0
    for s in universe:
        f = feats.get(s)
        if not f or len(f["bars"]) < 25:
            continue
        cs, hs = [b["c"] for b in f["bars"]], [b["h"] for b in f["bars"]]
        if cs[-4] > max(hs[-24:-4]):
            bo += 1
            if cs[-1] > max(hs[-24:-4]):
                bo_held += 1
    follow = (bo_held / bo * 100) if bo else None
    growth = [feats[e]["blend"] for e in ("XLK", "XLY", "XLC") if e in feats and feats[e]["blend"] is not None]
    defens = [feats[e]["blend"] for e in ("XLP", "XLU", "XLV") if e in feats and feats[e]["blend"] is not None]
    risk = (board.lin(statistics.mean(growth) - statistics.mean(defens), -3, 3) if growth and defens else None)
    etfs = [feats[e] for e in SECTOR_ETF.values() if e in feats]
    outperform = sum(1 for f in etfs if (f["blend"] or -99) > (spy["blend"] or 0))
    rotation = (outperform / len(etfs) * 60 + sum(1 for f in etfs if (f["r5"] or 0) > 0) / len(etfs) * 40) if etfs else None
    agree = sum(1 for e in ("SPY", "QQQ", "IWM") if e in feats and feats[e]["ema50"] and feats[e]["close"] > feats[e]["ema50"])
    return {"marketRegime": max(0.0, min(100.0, regime)), "marketBreadth": breadth, "indexAccDist": accdist,
            "breakoutFollowThrough": follow, "riskAppetite": risk, "sectorRotation": rotation,
            "macroEventRisk": None,                      # no calendar feed is wired into the board (declared)
            "indexConfirmation": agree / 3 * 100}


def compute(bars, universe, sectors, tape_pos, inst_bundle):
    """the board over `universe` -> (rows, insufficient_symbols, market, as_of).
    bars: {symbol: [board bars]} including the benchmarks; sectors: {symbol: {"sector","sub_industry"}};
    tape_pos: {symbol: optionsPositioning score}; inst_bundle: {symbol: {leaf: {"score",...}}}.
    A row carries everything the cards need; the caller trims it."""
    feats = {}
    for sym in set(universe) | set(BENCH):
        f = bf.features(bars.get(sym, []))
        if f:
            feats[sym] = f
    if "SPY" not in feats:
        raise ValueError("SPY has too few completed sessions: the board cannot be read")
    spy = feats["SPY"]
    spy_by_date = {b["d"]: b["c"] for b in spy["bars"]}
    blends = {s: f["blend"] for s, f in feats.items() if f["blend"] is not None}
    industries, sector_names = {}, {}
    for sym in universe:
        g = sectors.get(sym)
        if not g or sym not in feats:
            continue
        if g.get("sub_industry"):
            industries.setdefault(g["sub_industry"], []).append(sym)
        sector_names.setdefault(g["sector"], []).append(sym)
    ind_median = {}
    for ind, members in industries.items():
        vals = [blends[m] for m in members if m in blends]
        if len(members) >= 5 and vals:
            ind_median[ind] = statistics.median(vals)
    etf_blend = {g: feats[e]["blend"] for g, e in SECTOR_ETF.items() if e in feats and feats[e]["blend"] is not None}
    rank_now = {g: board.pct_rank(etf_blend, g) for g in etf_blend}
    old = {}
    for g, e in SECTOR_ETF.items():
        if e in feats:
            v = board.blend_ret([b["c"] for b in feats[e]["bars"][:-20]])
            if v is not None:
                old[g] = v
    rank_old = {g: board.pct_rank(old, g) for g in old}
    sector_ctx = {}
    for g, e in SECTOR_ETF.items():
        f = feats.get(e)
        if not f:
            continue
        closes = [b["c"] for b in f["bars"]]
        e50 = board.ema_series(closes, 50)
        streak = 0
        for i in range(len(closes) - 1, 0, -1):
            if e50 and not math.isnan(e50[i]) and closes[i] > e50[i]:
                streak += 1
            else:
                break
        rot = None
        if rank_now.get(g) is not None and rank_old.get(g) is not None:
            dv = statistics.median([b["c"] * b["v"] for b in f["bars"][-5:]]) / statistics.median(
                [b["c"] * b["v"] for b in f["bars"][-20:]]) - 1
            rot = board.lin(rank_now[g] - rank_old[g], -40, 40) * 0.7 + board.lin(dv * 100, -20, 20) * 0.3
        sector_ctx[g] = {"strength": rank_now.get(g), "rotation": rot, "crowding": 100 - board.lin(streak, 0, 40)}
    for g, members in sector_names.items():
        above = [m for m in members if feats[m]["ema50"] and feats[m]["close"] > feats[m]["ema50"]
                 and (feats[m]["r20"] or 0) > 0]
        sector_ctx.setdefault(g, {})["confirmation"] = len(above) / len(members) * 100 if members else None
    market = market_context(feats, universe, spy)
    rows, insufficient = [], []
    for sym in universe:
        f = feats.get(sym)
        if not f:
            insufficient.append(sym)
            continue
        g = sectors.get(sym) or {}
        gname = g.get("sector")
        etf = SECTOR_ETF.get(gname) if gname else None
        bundle = inst_bundle.get(sym) or {}
        ctx = {"spy_c": aligned(spy_by_date, f["bars"]), "spy_blend": spy["blend"], "qqq_blend": feats["QQQ"]["blend"]
               if "QQQ" in feats else None,
               "sector_blend": feats[etf]["blend"] if etf in feats else None,
               "peer_rank": _peer_rank(sym, g, industries, blends) if g else None,
               "sector_strength_pct": sector_ctx.get(gname, {}).get("strength"),
               "industry_strength_pct": (board.pct_rank(ind_median, g["sub_industry"])
                                         if g.get("sub_industry") in ind_median else None),
               "sector_rotation_score": sector_ctx.get(gname, {}).get("rotation"),
               "sector_peer_rank": (board.pct_rank({m: blends[m] for m in sector_names.get(gname, []) if m in blends},
                                                   sym) if gname else None),
               "sector_peer_confirmation": sector_ctx.get(gname, {}).get("confirmation"),
               "sector_crowding_score": sector_ctx.get(gname, {}).get("crowding"),
               "tape_positioning": tape_pos.get(sym),
               "inst_leaves": {k: (v or {}).get("score") for k, v in bundle.items() if isinstance(v, dict)},
               "market": market}
        leaves = bf.score_name(f, ctx)
        agg = board.aggregate(leaves)
        if agg["score"] is None:
            insufficient.append(sym)
            continue
        qualified, qfails = board.qualify(f)
        gate_ok, gate_fails = board.vendor_gate(qualified, agg)
        rows.append({"symbol": sym, "sector": gname, "close": f["close"], "score": agg["score"],
                     "confirming": agg["confirming"], "dc": agg["dc"], "qualified": gate_ok, "gate_fails": gate_fails,
                     "qualify_fails": qfails, "capacity_usd": f["dollar_adv"], "stage": f["stage"],
                     "atr_pct": f["atr_pct"], "support": f["support"], "resistance": f["resistance"],
                     "ribbon": bf.ribbon_state(f), "triggers": bf.detect_triggers(f), "ladder": bf.saty_ladder(f),
                     "categories": {k: {"score": v["score"], "state": v["state"]} for k, v in agg["categories"].items()},
                     "leaves": leaves, "inst_bundle": bundle})
    rows.sort(key=lambda r: -r["score"])
    return rows, insufficient, market, spy["bars"][-1]["d"].isoformat()


def tape_positioning(tape_cards):
    """optionsPositioning for the index funds from the Tape's net premium share: board.lin(net / total, -0.5, 0.5)"""
    out = {}
    for sym, c in (tape_cards or {}).items():
        if isinstance(c, dict) and c.get("status") == "ok" and c.get("total_premium_usd"):
            out[sym] = board.lin(c["net_premium_usd"] / c["total_premium_usd"], -0.5, 0.5)
    return out


def _r(x, k=2):
    return None if x is None else round(x, k)


INST_LEAVES = ("instOwnership", "instActivity", "insiderActivity", "optionsPositioning", "dealerPositioning", "darkPool",
               "shortPositioning")


def public_row(r, now_stamp):
    """a row as the contract's morgue.board.top[] (the leaves rounded, the institutional leaves stamped)"""
    from . import stamp
    leaves = {}
    for cat, vals in r["leaves"].items():
        for k, v in vals.items():
            leaves.setdefault(cat, {})[k] = _r(v, 1)
    inst = {}
    for k in INST_LEAVES:
        if k == "optionsPositioning":
            v = r["leaves"]["institutionalPositioning"].get(k)
            inst[k] = (stamp("ok", now_stamp, "Morgue tape net premium", "the session's prints", score=_r(v, 1))
                       if v is not None else {"score": None, "status": "no_data",
                                              "reason": "index funds only; no tape card for this name",
                                              "as_of": None, "source": "Morgue tape net premium", "delay": None})
            continue
        b = (r.get("inst_bundle") or {}).get(k)
        if isinstance(b, dict) and b.get("score") is not None:
            inst[k] = {"score": _r(b["score"], 1), "status": b.get("status", "ok"), "as_of": b.get("as_of"),
                       "source": b.get("source"), "delay": b.get("delay")}
        elif isinstance(b, dict):
            inst[k] = {"score": None, "status": "no_data", "reason": b.get("reason") or "no reading",
                       "as_of": b.get("as_of"), "source": b.get("source"), "delay": b.get("delay")}
        else:
            why = {"dealerPositioning": "no free route for stock-level dealer positioning",
                   "darkPool": "no free route for stock-level dark-pool prints"}.get(k, "not read for this name")
            inst[k] = {"score": None, "status": "no_data", "reason": why, "as_of": None, "source": None, "delay": None}
    lad = r["ladder"]
    return {"symbol": r["symbol"], "sector": r["sector"], "close": _r(r["close"]), "score": _r(r["score"], 1),
            "confirming": r["confirming"], "dc": r["dc"], "qualified": r["qualified"], "gate_fails": r["gate_fails"],
            "qualify_fails": r["qualify_fails"], "capacity_usd": _r(r["capacity_usd"], 0), "stage": r["stage"],
            "atr_pct": _r(r["atr_pct"]), "support": _r(r["support"]), "resistance": _r(r["resistance"]),
            "ribbon": r["ribbon"],
            "triggers": [{"trigger": t["trigger"], "level": _r(t["level"]), "validated": bool(t["validated"])}
                         for t in r["triggers"]],
            "ladder": (None if not lad else {"anchor": lad["anchor"], "atr": lad["atr"], "trigger_up": lad["trigger_up"],
                                             "trigger_down": lad["trigger_down"]}),
            "categories": {k: {"score": _r(v["score"], 1), "state": v["state"]} for k, v in r["categories"].items()},
            "leaves": leaves, "inst": inst}


FULL_COLUMNS = ["symbol", "sector", "close", "score", "confirming", "dc", "qualified", "capacity_usd", "stage"] + \
    list(board.CONFIG) + ["instOwnership", "instActivity", "insiderActivity", "optionsPositioning", "shortPositioning"]


def full_row(r):
    """one compact array of the sidecar morgue-board.json, in FULL_COLUMNS order"""
    inst = r["leaves"]["institutionalPositioning"]
    return ([r["symbol"], r["sector"], _r(r["close"]), _r(r["score"], 1), r["confirming"], r["dc"], r["qualified"],
             _r(r["capacity_usd"], 0), r["stage"]]
            + [_r(r["categories"][c]["score"], 1) for c in board.CONFIG]
            + [_r(inst.get(k), 1) for k in ("instOwnership", "instActivity", "insiderActivity", "optionsPositioning",
                                            "shortPositioning")])
