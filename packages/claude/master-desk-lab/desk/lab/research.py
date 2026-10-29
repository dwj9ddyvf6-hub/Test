"""The research block every lab signal row carries (eyes/DEEP/LAB_RESEARCH_FLAGS_SPEC.md, "Each lab signal row carries
`research`"; of that spec's flags only the analysis engine is built):

  research.engine          the screen row of the entry's symbol (desk/analysis) from the last session completed
                           before its decision: a desk entry during session d+1 carries screen d (2-19c). A session is
                           complete SETTLE_S after its close, as the lab counts it (desk/lab/__init__.py last_complete)
  research.engine_session  that session
  research.engine_reason   None, or why there is no row: a short entry (FB2 screens long entries), no screen file for
                           the session, the symbol not in it
A row is taken as the screen wrote it, scored or not (an unscored row says why). Nothing is computed here: P needs its
session's whole cross-section (OW is a same-session rank), so no stand-alone P is ever made. Read-only: the screen
files are read, never written. desk.analysis is imported only when a screen is read: desk/engine.py imports
desk/lab/quotes.py, so nothing this package loads at import may pull the engine into the loop's process."""
from ..data.hub import alpaca_stock_symbol


class Screens:
    """each session's screen rows by symbol, read once per run"""

    def __init__(self, root):
        self.root, self._rows = root, {}

    def rows(self, session):
        """{symbol: row}, None when the session has no screen file, or a string naming why it cannot be read"""
        if session not in self._rows:
            from ..analysis import store as screens_store
            try:
                doc = screens_store.read(self.root, session)
                self._rows[session] = {r["sym"]: r for r in doc.get("rows") or ()}
            except FileNotFoundError:
                self._rows[session] = None
            except (OSError, ValueError, EOFError, KeyError, TypeError, AttributeError) as e:
                self._rows[session] = f"unreadable ({type(e).__name__})"
        return self._rows[session]


def screen_session(t):
    """the last session completed before a decision at t"""
    from . import last_complete
    return last_complete(t).isoformat()


def engine(row, screens):
    if row.get("side") != "long":
        return {"engine": None, "engine_session": None, "engine_reason": "a short entry: FB2 screens long entries"}
    d = screen_session(row["decided_at"])
    rows = screens.rows(d)
    if rows is None:
        return {"engine": None, "engine_session": d, "engine_reason": f"no screen for {d}"}
    if isinstance(rows, str):
        return {"engine": None, "engine_session": d, "engine_reason": f"the {d} screen is {rows}"}
    sym = row["symbol"]
    r = rows.get(sym) or rows.get(alpaca_stock_symbol(sym) or sym)
    if r is None:
        return {"engine": None, "engine_session": d, "engine_reason": f"{sym} is not in the {d} screen"}
    return {"engine": r, "engine_session": d, "engine_reason": None}
