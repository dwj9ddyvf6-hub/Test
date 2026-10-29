"""Row lookup shared by the desk AI tool modules: a name's row on the board, the watch list or the Look up roster,
and the guard that refuses a row dated after the snapshot."""


def sym_of(args):
    from .tools import _sym
    return _sym(args)


def row_of(sym, ctx):
    ed = ctx["edition"]
    for key, name in (("setups", "board"), ("watching", "watching")):
        for r in ed.get(key) or []:
            if r.get("symbol") == sym:
                return name, r
    rd, _ = ctx["source"].read(sym)
    return ("lookup", rd) if rd else (None, None)


def dated_after(row, ctx):
    """a reason string when the row's own date is later than the snapshot's market session, else None"""
    as_of = ((ctx["edition"].get("market") or {}).get("as_of")) or ""
    d = str(row.get("as_of") or "")[:10]
    if as_of and d and d > as_of:
        return f"the row is dated {d}, after the snapshot's session {as_of}"
    return None
