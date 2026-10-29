"""The desk AI's tools over the desk's existing modules. Each returns {result, status?, reason?, sources?, as_of?};
desk.ai.run wraps it in the contract. Prices are the page's own prices (desk/terminal/prices.py: the plan's % from
its close, rounded to the safe side of each line's role), so the AI quotes exactly what the terminal shows.
"""
import math

from desk.terminal import prices

from . import tool, gates, worksheet

SLIPPAGE = 0.0025     # stressed stop: the stop fill assumed 0.25% worse than the line (study I, HyperGrok sizing)


def _sym(args):
    s = str(args.get("ticker") or args.get("symbol") or "").strip().upper()
    if not s or not s.replace(".", "").replace("-", "").isalnum() or len(s) > 10:
        raise ValueError("ticker required (letters, digits, '.' or '-')")
    return s


def price_map(close, plan):
    """the plan's lines in dollars as the page shows them; None when the plan has no close or no stop/target"""
    if not isinstance(close, (int, float)) or not plan or plan.get("out") is None or plan.get("t1") is None:
        return None
    out = {"close": close}
    for k in ("zone_lo", "zone_hi", "trigger", "out", "t1", "t2"):
        v = plan.get(k)
        if v is not None:
            out[{"out": "stop"}.get(k, k)] = prices.px(close, v, prices.ROLE[k])
    for k in ("by", "window", "mode", "sessions", "r", "risk_atr", "why_zone", "why_out", "why_t1"):
        if plan.get(k) is not None:
            out[k] = plan[k]
    return out


def _find(ed, sym):
    for s in ed.get("setups") or []:
        if s.get("symbol") == sym:
            return "board", s
    for w in ed.get("watching") or []:
        if w.get("symbol") == sym:
            return "watching", w
    return None, None


def _plan_of(where, row):
    if where == "watching":
        return {k: row.get(k) for k in ("zone_lo", "zone_hi", "trigger", "out", "t1", "mode", "by")}
    return row.get("plan") or {}


def _card(where, row, ed):
    plan = _plan_of(where, row)
    conv = row.get("conviction")
    return {"symbol": row.get("symbol"), "on": where, "action": row.get("action"),
            "conviction": conv.get("word") if isinstance(conv, dict) else conv,
            "take": (row.get("gut") or {}).get("word") if isinstance(row.get("gut"), dict) else row.get("gut"),
            "form": row.get("form"), "gist": row.get("gist"), "status": row.get("status"),
            "as_of": row.get("as_of") or (ed.get("market") or {}).get("as_of"),
            "now_pct": row.get("now_pct"), "fear": row.get("fear"),
            "price_map": price_map(row.get("close"), plan),
            "invalidation": (f"a daily close below the stop ({plan.get('why_out')})" if plan.get("why_out")
                             else "a daily close below the stop") if plan.get("out") is not None else None,
            "line": (plan.get("sentence") if isinstance(plan, dict) else None) or row.get("line")}


@tool("snapshot")
def snapshot(args, ctx):
    ed = ctx["edition"]
    mk = ed.get("market") or {}
    return {"timeless": False, "result": {
        "snapshot_id": ctx["snapshot_id"], "edition": ed.get("edition"), "seq": ed.get("seq"),
        "generated_at": ed.get("generated_at"), "session": (ed.get("session") or {}).get("label"),
        "market_as_of": mk.get("as_of"), "regime": (mk.get("badge") or {}).get("word"),
        "regime_line": (mk.get("badge") or {}).get("line"), "fear": (ed.get("fear") or {}).get("text"),
        "board": [s.get("symbol") for s in ed.get("setups") or []],
        "watching": [w.get("symbol") for w in ed.get("watching") or []],
        "lookup_names": (ed.get("lookup") or {}).get("count")}}


@tool("market")
def market(args, ctx):
    mk = ctx["edition"].get("market") or {}
    if not mk.get("as_of"):
        return {"status": "no_data", "reason": "the edition carries no market read"}
    return {"result": {k: mk.get(k) for k in ("as_of", "sentence", "badge", "chips", "sectors", "calendar")}}


@tool("fear")
def fear(args, ctx):
    ed = ctx["edition"]
    rows = [{"symbol": s.get("symbol"), "fear": s.get("fear")} for s in ed.get("setups") or []]
    return {"result": {"banner": ed.get("fear"), "board": rows,
                       "rule": "a fear day: SPY or QQQ closes red; a setup's fear state is came / waiting / none "
                               "(desk/terminal/fear.py)"}}


@tool("read")
def read(args, ctx):
    sym = _sym(args)
    ed = ctx["edition"]
    where, row = _find(ed, sym)
    if row is not None:
        return {"result": _card(where, row, ed)}
    rd, src = ctx["source"].read(sym)
    if rd is None:
        return {"status": "no_data", "reason": f"{sym} is not on the board, the watch list or the Look up roster"}
    c = _card("lookup", rd, ed)
    return {"result": c, "sources": [src], "as_of": rd.get("as_of")}


@tool("levels")
def levels(args, ctx):
    r = read(args, ctx)
    if r.get("status") == "no_data":
        return r
    c = r["result"]
    if not c.get("price_map"):
        return {"status": "no_data", "reason": "No trade — data gap: the read carries no complete price map"}
    return dict(r, result={"symbol": c["symbol"], "as_of": c["as_of"], "price_map": c["price_map"],
                           "invalidation": c["invalidation"]})


@tool("scan")
def scan(args, ctx):
    """lanes: best (the board), watching (Next 20), fear_pullback (board + watching rows on a pullback/level plan whose
    fear state is not 'none'), all (board + watching). Every scan carries its receipt."""
    lane = str(args.get("lane") or "best")
    ed = ctx["edition"]
    rows = [("board", s) for s in ed.get("setups") or []]
    if lane in ("watching", "all", "fear_pullback"):
        rows += [("watching", w) for w in ed.get("watching") or []]
    if lane == "watching":
        rows = [r for r in rows if r[0] == "watching"]
    if lane not in ("best", "watching", "all", "fear_pullback"):
        raise ValueError("lane must be best, watching, all or fear_pullback")
    cards, unavailable = [], []
    for where, row in rows:
        c = _card(where, row, ed)
        if lane == "fear_pullback":
            f = row.get("fear") or {}
            mode = (_plan_of(where, row) or {}).get("mode")
            if not (mode in ("level", "reaction") and (where == "watching" or f.get("state") in ("came", "waiting"))):
                continue
        (cards if c["price_map"] else unavailable).append(c)
    sheet = {r["symbol"]: r for r in worksheet.build(ed)["rows"]}    # the regime gate: Buy, Watch or No trade today
    for c in cards:
        w = sheet.get(c["symbol"])
        if w:
            c["today"] = {"verdict": w["verdict"], "size": w["size"], "reason": w["reason"]}
    actionable = [c for c in cards if (c.get("today") or {}).get("verdict") == "Buy"]
    receipt = {"at": ed.get("generated_at"), "lane": lane, "universe": (ed.get("lookup") or {}).get("count"),
               "regime": ((ed.get("market") or {}).get("badge") or {}).get("word"), "scanned": len(rows), "actionable": len(actionable), "watch": len(cards) - len(actionable),
               "unavailable": len(unavailable), "method": "desk read + board gate, edition " + str(ed.get("seq")),
               "nothing_qualifies": not cards}
    return {"result": {"receipt": receipt, "rows": cards,
                       "unavailable": [c["symbol"] for c in unavailable]}}


@tool("explain_setup")
def explain_setup(args, ctx):
    """the read's own evidence, signed: what speaks for (standouts, material), what against, and the lenses.
    Evidence weights, not probabilities (odds come from setup_odds once it lands)."""
    sym = _sym(args)
    where, row = _find(ctx["edition"], sym)
    if row is None:
        row, _ = ctx["source"].read(sym)
        where = "lookup"
    if row is None:
        return {"status": "no_data", "reason": f"no read for {sym}"}
    pro = [{"sign": "+", "head": x.get("head"), "text": x.get("text")}
           for x in (row.get("material") or []) + (row.get("standouts") or [])]
    con = [{"sign": "-", "head": x.get("head"), "text": x.get("text")} for x in row.get("against") or []]
    lens = row.get("lens") or {}
    return {"result": {"symbol": sym, "on": where, "evidence": row.get("evidence"), "for": pro, "against": con,
                       "considered": row.get("considered") or [],
                       "lenses": {k: lens.get(k) for k in ("stage", "word", "n", "red", "c8") if k in lens},
                       "note": "evidence for and against, not probabilities"}}


@tool("record")
def record(args, ctx):
    ed = ctx["edition"]
    sc = ed.get("scorecard") or {}
    kind = args.get("type") or args.get("form")
    as_of = (ed.get("market") or {}).get("as_of") or ""
    calls = [c for c in ed.get("calls") or [] if str(c.get("opened") or "")[:10] <= as_of]   # never a later call
    if kind:
        calls = [c for c in calls if c.get("form") == kind or c.get("kind") == kind]
    closed = [c for c in calls if c.get("outcome_r") is not None]
    out = {"scorecard": sc, "type": kind, "calls": len(calls), "closed": len(closed),
           "hits": sum(1 for c in closed if (c.get("outcome_r") or 0) > 0),
           "mean_r": round(sum(c["outcome_r"] for c in closed) / len(closed), 2) if closed else None,
           "rule": "losers stay in the record; under 30 closed calls the record is too few to judge"}
    out["judgeable"] = (sc.get("closed") or 0) >= 30 if not kind else len(closed) >= 30
    return {"result": out}


@tool("preview_order")
def preview_order(args, ctx):
    """a proposal, never an order: size from the stressed stop, risk in $ and % of the stated equity, the desk's
    current exposure to the name and its sector fund, then the consistency and risk gates"""
    sym = _sym(args)
    equity = float(args.get("equity") or 0)
    if equity <= 0:
        raise ValueError("equity (the account value to size against) is required")
    lv = levels({"ticker": sym}, ctx)
    if lv.get("status") == "no_data":
        return lv
    pm = lv["result"]["price_map"]
    lim = gates.limits()
    risk_pct = min(float(args.get("risk_pct") or lim["risk_pct"]), lim["risk_pct"])
    entry = pm.get("zone_hi") or pm.get("trigger")
    stop = pm["stop"]
    stressed = stop * (1 - SLIPPAGE)
    per = entry - stressed if entry else None
    shares = math.floor(equity * risk_pct / 100 / per) if per and per > 0 else 0
    if entry:                                            # the position ceiling caps the size; it does not reject it
        shares = min(shares, math.floor(equity * lim["max_position_pct"] / 100 / entry))
    expo = exposure(sym, ctx)
    intent = {"symbol": sym, "side": "long", "entry": entry, "stop": stop, "t1": pm.get("t1"), "t2": pm.get("t2"),
              "zone_lo": pm.get("zone_lo"), "zone_hi": pm.get("zone_hi"), "last": _last(pm, lv),
              "shares": shares, "equity": equity, "risk_dollars": round(shares * per, 2) if per else None,
              "notional": round(shares * entry, 2) if entry else None, "earnings_in_hold": args.get("earnings_in_hold"),
              "open_risk_pct": float(args.get("open_risk_pct") or 0), "sector": expo.get("sector"),
              "sector_names_held": expo.get("sector_names_held", 0),
              "today": next((r["verdict"] for r in worksheet.build(ctx["edition"])["rows"] if r["symbol"] == sym),
                            "No trade")}
    cons = gates.consistency_gate(intent)
    risk = gates.risk_gate(intent, root=ctx["source"].root)
    rr = round((pm["t1"] - entry) / (entry - stop), 2) if entry and entry > stop else None
    return {"result": {"proposal": intent, "risk_pct_of_equity": round(100 * intent["risk_dollars"] / equity, 3)
                       if intent["risk_dollars"] is not None else None, "rr_to_t1": rr,
                       "stressed_stop": round(stressed, 4), "exposure": expo, "consistency": cons, "risk": risk,
                       "approval": "propose-then-approve: no order was placed; the owner approves each ticket",
                       "invalidation": lv["result"]["invalidation"]}}


def _last(pm, lv):
    return pm.get("close")


def exposure(sym, ctx):
    """the desk's books summed: the name's notional across sleeves, and how many names it holds under the same sector
    fund; host only (never published)"""
    try:
        from desk.terminal.read.indicators import sector_of
        sec = sector_of(sym)
    except Exception:                                    # noqa: BLE001  (the map file may be absent off-host)
        sec = None
    books, where = ctx["source"].books()
    if not books:
        return {"status": "no_data", "reason": "no books on this machine", "sector": sec}
    by_sym = {}
    for b in books.values():
        for k, p in ((b or {}).get("positions") or {}).items():
            s = k.split(":", 1)[-1]
            q = float(p.get("qty") or p.get("shares") or 0)
            mark = ((b or {}).get("marks") or {}).get(k) or p.get("avg") or 0
            by_sym[s] = by_sym.get(s, 0.0) + q * float(mark)
    same = 0
    if sec:
        try:
            from desk.terminal.read.indicators import sector_of as so
            same = sum(1 for s, v in by_sym.items() if v and s != sym and so(s) == sec)
        except Exception:                                # noqa: BLE001
            same = 0
    return {"status": "ok", "sector": sec, "held_notional": round(by_sym.get(sym, 0.0), 2),
            "sector_names_held": same, "source": where}


@tool("worksheet")
def worksheet_tool(args, ctx):
    return {"result": worksheet.build(ctx["edition"])}


@tool("consistency_gate")
def consistency_tool(args, ctx):
    return {"result": gates.consistency_gate(args.get("intent") or {}), "timeless": True}


@tool("risk_gate")
def risk_tool(args, ctx):
    return {"result": gates.risk_gate(args.get("intent") or {}, root=ctx["source"].root), "timeless": True}


@tool("ground")
def ground_tool(args, ctx):
    return {"result": gates.ground(args.get("text") or "", args.get("outputs") or []), "timeless": True}


def slot_call(f, args, ctx):
    """a sibling build's tool: called with (args, edition); it may return a contract-shaped dict or a bare result"""
    out = f(args, ctx["edition"])
    if isinstance(out, dict) and ("result" in out or "status" in out):
        return out
    return {"result": out}


from . import odds_tools, context_tools, strip_tools, forecast_tools   # noqa: E402,F401  (each registers its tools)
