"""Desk AI tools over the market strip (desk/terminal/strip.py) and the per-name options block: expected_move, gex,
regime, day_type, options_read, structure_trade. They read the blocks the terminal job built from the session's
gather; a block that job marked no_data passes through with its reason. No option premium is ever invented: the
structures are the strip's own, priced from the chain's quotes (buy at the ask, sell at the bid) and only when the
gather captured them."""
from . import tool
from .ctx_rows import row_of, sym_of, dated_after

FUNDS = ("SPY", "QQQ")


def _strip(ctx):
    s = ctx["edition"].get("strip")
    return s if isinstance(s, dict) and not s.get("error") else None


def _blk(ctx, key, label):
    s = _strip(ctx)
    if s is None:
        return None, {"status": "no_data", "reason": "the edition carries no market strip"}
    b = s.get(key)
    if not isinstance(b, dict):
        return None, {"status": "no_data", "reason": f"the strip has no {label}"}
    if b.get("status") == "no_data":
        return None, {"status": "no_data", "reason": b.get("reason") or f"no {label}"}
    return b, None


def _out(b, ctx, label):
    st = b.get("status", "ok")
    res = {"result": b, "sources": ["edition:strip." + label], "as_of": b.get("as_of")}
    if st == "stale":
        res.update(status="stale", reason=f"{label} is from {b.get('as_of')}, not this session")
    return res


@tool("expected_move")
def expected_move(args, ctx):
    if args.get("ticker") or args.get("symbol"):
        sym = sym_of(args)
        where, row = row_of(sym, ctx)
        o = (row or {}).get("options")
        if row is None or not isinstance(o, dict) or o.get("status") != "ok" or o.get("em_pct") is None:
            return {"status": "no_data", "reason": ((o or {}).get("reason") if isinstance(o, dict) else None)
                    or f"no IV30 read for {sym} this session"}
        return {"result": {"symbol": sym, "em_pct": o["em_pct"], "iv30": o.get("iv30"), "as_of": o.get("as_of"),
                           "method": "IV30 / sqrt(252): one-day move"}, "sources": ["edition:options." + sym]}
    b, err = _blk(ctx, "move", "expected move")
    return err or _out(b, ctx, "move")


@tool("gex")
def gex(args, ctx):
    f = str(args.get("ticker") or args.get("fund") or "SPY").upper()
    if f not in FUNDS:
        return {"status": "no_data", "reason": f"gamma is read for {', '.join(FUNDS)} only, not {f}"}
    g, err = _blk(ctx, "gex", "gamma read")
    if err:
        return err
    return _out(g[f], ctx, "gex." + f) if isinstance(g.get(f), dict) and g[f].get("status") != "no_data" else {
        "status": "no_data", "reason": (g.get(f) or {}).get("reason") or f"no gamma read for {f}"}


@tool("regime")
def regime(args, ctx):
    ed = ctx["edition"]
    mk = ed.get("market") or {}
    badge = mk.get("badge") or {}
    if not badge.get("word"):
        return {"status": "no_data", "reason": "the edition carries no market regime"}
    s = _strip(ctx) or {}
    fear = s.get("fear") if isinstance((s or {}).get("fear"), dict) and s["fear"].get("status") != "no_data" else None
    return {"result": {"word": badge.get("word"), "line": badge.get("line"), "as_of": mk.get("as_of"),
                       "volatility": (fear or {}).get("word"), "vix_premium": (fear or {}).get("premium"),
                       "fear_day": (fear or {}).get("fear_day")}, "sources": ["edition:market", "edition:strip.fear"]}


@tool("day_type")
def day_type(args, ctx):
    b, err = _blk(ctx, "day", "day type")
    return err or _out(b, ctx, "day")


def _opts(args, ctx):
    sym = sym_of(args)
    where, row = row_of(sym, ctx)
    if row is None:
        return sym, None, {"status": "no_data", "reason": f"{sym} is not on the board, the watch list or the roster"}
    late = dated_after(row, ctx)
    if late:
        return sym, None, {"status": "no_data", "reason": late}
    o = row.get("options")
    if not isinstance(o, dict):
        return sym, None, {"status": "no_data", "reason": f"no options read for {sym} (not a listed long, or the "
                                                          "chain was not gathered)"}
    if o.get("status") == "no_data":
        return sym, None, {"status": "no_data", "reason": o.get("reason") or f"no options read for {sym}"}
    return sym, o, None


@tool("options_read")
def options_read(args, ctx):
    sym, o, err = _opts(args, ctx)
    if err:
        return err
    keep = ("iv30", "iv_rank", "iv_sessions", "iv_rv", "pc_volume", "pc_oi", "pc_oi_change", "spread_pct", "em_pct",
            "t1_beyond_2em", "expiry", "as_of", "method")
    res = {"result": dict({k: o.get(k) for k in keep}, symbol=sym), "sources": ["edition:options." + sym],
           "as_of": o.get("as_of")}
    if o.get("iv_rank") is None:
        res["result"]["iv_rank_reason"] = f"IV rank needs a year of stored IV30; {o.get('iv_sessions')} sessions held"
    return res


@tool("structure_trade")
def structure_trade(args, ctx):
    view = str(args.get("view") or "bullish").lower()
    if view not in ("bullish", "long"):
        return {"status": "no_data", "reason": f"the desk trades long ideas only; no structure for a {view} view"}
    sym, o, err = _opts(args, ctx)
    if err:
        return err
    ex = o.get("express") or []
    if not ex:
        return {"status": "no_data", "reason": o.get("express_reason") or "no usable call quotes"}
    return {"result": {"symbol": sym, "view": "bullish", "expiry": o.get("expiry"), "structures": ex,
                       "per": "per share; x100 a contract; priced from the chain's own quotes, indicative not signed"},
            "sources": ["edition:options." + sym], "as_of": o.get("as_of")}
