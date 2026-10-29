"""Desk AI tools over the odds block (desk/terminal/odds.py): setup_odds, analog_odds, level_odds. They read the
numbers the nightly odds job already computed (the edition's per-row `odds` block, the host's state/terminal/odds.json
type table). They compute nothing and type no constant: under MIN_N resolved cases, or with no block, the answer is
no_data with the exact reason. A row dated after the snapshot's market session is a future fact and is refused."""
from desk.terminal import odds as oddsmod

from . import tool
from .ctx_rows import row_of, sym_of, dated_after


def _block(args, ctx):
    sym = sym_of(args)
    where, row = row_of(sym, ctx)
    if row is None:
        return sym, None, {"status": "no_data", "reason": f"{sym} is not on the board, the watch list or the roster"}
    late = dated_after(row, ctx)
    if late:
        return sym, None, {"status": "no_data", "reason": late}
    b = row.get("odds")
    if not isinstance(b, dict) or not b:
        return sym, None, {"status": "no_data", "reason": f"no odds block for {sym} in this edition (the card has no "
                                                         "setup type or geometry, or the odds job has not run)"}
    return sym, b, None


@tool("analog_odds")
def analog_odds(args, ctx):
    sym, b, err = _block(args, ctx)
    if err:
        return err
    a = b.get("analog")
    if not isinstance(a, dict) or a.get("rate") is None:
        return {"status": "no_data", "reason": "no analog line: too few past states near this one"}
    n = a.get("n")
    if not isinstance(n, int) or n < oddsmod.MIN_N:
        return {"status": "no_data", "reason": f"analog n={n} is under {oddsmod.MIN_N} past states"}
    return {"result": {"symbol": sym, "type": b.get("type"), "regime": b.get("regime"),
                       **{k: a.get(k) for k in ("n", "rate", "base", "lift", "sentence")}},
            "sources": ["edition:odds." + sym], "as_of": ctx["edition"].get("market", {}).get("as_of")}


@tool("level_odds")
def level_odds(args, ctx):
    sym, b, err = _block(args, ctx)
    if err:
        return err
    lv = b.get("levels")
    if not lv:
        return {"status": "no_data", "reason": "the odds block carries no level odds for this card"}
    if b.get("pending"):
        return {"status": "no_data", "reason": f"n={b.get('n')} under {oddsmod.MIN_N} cases: validation pending"}
    return {"result": {"symbol": sym, "n": b.get("n"), "levels": lv, "depth": b.get("depth")},
            "sources": ["edition:odds." + sym]}


@tool("setup_odds")
def setup_odds(args, ctx):
    """a card's odds (ticker) or the type table (type + regime) from the host's odds.json"""
    ed = ctx["edition"]
    if args.get("ticker") or args.get("symbol"):
        sym, b, err = _block(args, ctx)
        if err:
            return err
        if b.get("pending") or b.get("rate") is None:
            return {"status": "no_data", "reason": f"n={b.get('n')} under {oddsmod.MIN_N} resolved cases: "
                                                   "validation pending"}
        keep = ("type", "regime", "n", "hits", "rate", "lo", "hi", "base", "lift", "mean_r", "days", "t1_atr",
                "out_atr", "t2_given_t1", "window", "last5", "method", "sentence")
        return {"result": dict({k: b.get(k) for k in keep if k in b}, symbol=sym),
                "sources": ["edition:odds." + sym]}
    typ = str(args.get("type") or "")
    regime = str(args.get("regime") or ((ed.get("market") or {}).get("badge") or {}).get("word") or "")
    if typ not in oddsmod.TYPES:
        raise ValueError(f"type must be one of {', '.join(oddsmod.TYPES)}")
    if regime not in oddsmod.REGIMES:
        return {"status": "no_data", "reason": f"no market regime read (asked '{regime}')"}
    doc, where = ctx["source"]._local("state", "terminal", "odds.json")
    if not doc:
        return {"status": "no_data", "reason": "no odds.json on this machine (the type table is host-only)"}
    cell = ((doc.get("types") or {}).get(typ) or {}).get("by_regime", {}).get(regime)
    if not cell or cell.get("rate") is None or cell.get("pending") or (cell.get("n") or 0) < oddsmod.MIN_N:
        return {"status": "no_data", "reason": f"{typ} in {regime}: n={(cell or {}).get('n')} under "
                                               f"{oddsmod.MIN_N} resolved cases"}
    return {"result": dict(cell, type=typ, regime=regime, label=oddsmod.LABEL[typ]), "sources": [where],
            "as_of": doc.get("as_of")}
