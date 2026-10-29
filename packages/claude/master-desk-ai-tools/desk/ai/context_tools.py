"""Desk AI tools over the card's context block (desk/terminal/context.py) and the record line (record.py):
event_study, catalyst, record_line. They return what the terminal already computed for the row, with its own
no_data reasons passed through; nothing is recomputed from bars here, so no bar after the snapshot can enter."""
from . import tool
from .ctx_rows import row_of, sym_of, dated_after


def _ctx_block(args, ctx):
    sym = sym_of(args)
    where, row = row_of(sym, ctx)
    if row is None:
        return sym, None, None, {"status": "no_data", "reason": f"{sym} is not on the board, the watch list or the roster"}
    late = dated_after(row, ctx)
    if late:
        return sym, row, None, {"status": "no_data", "reason": late}
    c = row.get("context")
    if not isinstance(c, dict):
        return sym, row, None, {"status": "no_data", "reason": f"no context block for {sym} in this edition"}
    return sym, row, c, None


def _pass(blk, what, sym):
    if not isinstance(blk, dict):
        return {"status": "no_data", "reason": f"no {what} for {sym}"}
    if blk.get("status") in ("no_data", "nodata"):
        return {"status": "no_data", "reason": blk.get("reason") or f"no {what} for {sym}"}
    return {"result": dict(blk, symbol=sym), "sources": ["edition:context." + sym]}


@tool("event_study")
def event_study(args, ctx):
    sym, row, c, err = _ctx_block(args, ctx)
    if err:
        return err
    return _pass(((c.get("catalyst") or {}).get("event")), "event study", sym)


@tool("catalyst")
def catalyst(args, ctx):
    sym, row, c, err = _ctx_block(args, ctx)
    if err:
        return err
    return _pass(c.get("catalyst"), "catalyst read", sym)


@tool("record_line")
def record_line(args, ctx):
    sym = sym_of(args)
    where, row = row_of(sym, ctx)
    rl = (row or {}).get("record_line")
    if not isinstance(rl, dict):
        return {"status": "no_data", "reason": f"no record line for {sym} (no call of its type is logged)"}
    return {"result": dict(rl, symbol=sym), "sources": ["edition:record_line." + sym]}
