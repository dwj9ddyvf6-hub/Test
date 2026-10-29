"""Desk AI tools over the Forecast Factory (desk/forecast/operator.py; FACTORY.md §11, BSF-11): forecast_route,
forecast_book, forecast_record, forecast_decay, forecast_publish. Each answers in the contract, reads what the factory
job wrote (state/forecast/) or, for a route, computes it from the promoted book and a context the caller passes in;
the AI types no number. Every answer is a proposal: nothing here places an order or touches a sleeve, the OMS or a book.
desk.forecast is imported inside the functions, so the loops never load the factory through the AI package."""
import os

from . import tool


def _root(ctx):
    return ctx["source"].root


def _book(ctx):
    from desk.forecast import promoted as PM
    from desk.forecast import operator as OP
    try:
        b = PM.load()
    except Exception as e:                                    # noqa: BLE001  (FrozenError, unreadable file)
        return None, f"the promoted book is not available: {e}"
    return PM.with_overlay(b, OP.overlay(_root(ctx))), None


@tool("forecast_route")
def forecast_route(args, ctx):
    """a name's routed proposal (BUY/WAIT/AVOID, HOLD/TRIM/SELL, or ABSTAIN) with the cell id, n, base rate, lift,
    cost and gates. Reads today's routes the factory job wrote; with a full `today` in args it routes that instead"""
    from desk.forecast import operator as OP, router as RT
    sym = str(args.get("symbol") or args.get("ticker") or args.get("sym") or "").upper()
    if isinstance(args.get("today"), dict):
        book, err = _book(ctx)
        if book is None:
            return {"status": "no_data", "reason": err}
        return {"result": RT.route(args["today"], book), "sources": ["forecast:promoted-book"], "timeless": True}
    day = OP.read_day(_root(ctx))
    if not day:
        return {"status": "no_data", "reason": "the forecast job has not run: no routes on this machine"}
    for r in day.get("routes", []):
        if r.get("sym") == sym:
            return {"result": r, "sources": ["forecast:routes"], "as_of": day.get("as_of")}
    return {"status": "no_data", "reason": f"{sym or 'no symbol'} was not routed in the latest day ({day.get('as_of')})"}


@tool("forecast_book")
def forecast_book(args, ctx):
    """the day's allocation by breadth: bets, effective breadth, risk budgets, the gain over the best single bet"""
    from desk.forecast import operator as OP
    day = OP.read_day(_root(ctx))
    if not day or not day.get("allocation"):
        return {"status": "no_data", "reason": "the forecast job has not run: no allocation on this machine"}
    return {"result": {"as_of": day.get("as_of"), "counts": day.get("counts"), "allocation": day["allocation"],
                       "propose_only": True}, "sources": ["forecast:routes"], "as_of": day.get("as_of")}


@tool("forecast_record")
def forecast_record(args, ctx):
    """the public scored record: every logged proposal, losers and abstentions included, graded at 1/5/21 sessions
    against seeded random entries on the same name; optional symbol filter"""
    from desk.forecast import operator as OP
    root = _root(ctx)
    if not os.path.isdir(OP.rdir(root)):
        return {"status": "no_data", "reason": "nothing is logged yet: the record starts with the first logged day"}
    sc = OP.scorecard(root)
    sym = str(args.get("symbol") or "").upper()
    if sym:
        sc = dict(sc, rows=[r for r in sc["rows"] if r["sym"] == sym])
    return {"result": sc, "sources": ["forecast:record"], "timeless": True}


@tool("forecast_decay")
def forecast_decay(args, ctx):
    """each promoted cell with enough forward dates through the decay state machine; demotions are status rows"""
    from desk.forecast import operator as OP
    book, err = _book(ctx)
    if book is None:
        return {"status": "no_data", "reason": err}
    root = _root(ctx)
    if not os.path.isdir(OP.rdir(root)):
        return {"status": "no_data", "reason": "no forward record yet: nothing can decay before it is graded"}
    out = OP.decay(root, book, as_of=(ctx["edition"].get("market") or {}).get("as_of"))
    return {"result": {"cells": out["cells"], "would_demote": out["status_rows"]}, "timeless": True,
            "sources": ["forecast:record"]}
