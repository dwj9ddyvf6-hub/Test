"""V-tv-2 - output audit: the desk's RSI and MACD against values read off a chart by hand.

`captures` are hand-entered rows {symbol, date, rsi, macd, signal, hist} (any may be absent); `closes` is
{symbol: [(iso date, close), ...]} ascending. The desk's value for a name-day comes from desk.terminal.read.ta over the
closes up to and including that date. A row passes when every supplied figure is within its tolerance. Under MIN_ROWS
(20) name-days the audit is no_data, with the rows that were checked still listed."""
from .stats import no_data

MIN_ROWS = 20
TOL = {"rsi": 0.5, "macd": 0.05, "signal": 0.05, "hist": 0.05}


def audit_indicators(captures, closes, tol=None):
    from ..terminal.read import ta
    tol = {**TOL, **(tol or {})}
    rows = []
    for c in captures:
        series = closes.get(c["symbol"]) or []
        xs = [float(v) for d, v in series if d <= c["date"]]
        if not xs or not any(d == c["date"] for d, _ in series):
            rows.append({"symbol": c["symbol"], "date": c["date"], "checked": False, "pass": None})
            continue
        line, sig, hist = ta.macd(xs)
        desk = {"rsi": ta.rsi(xs)[-1], "macd": line[-1], "signal": sig[-1], "hist": hist[-1]}
        diffs = {k: abs(desk[k] - float(c[k])) for k in tol if c.get(k) is not None and desk[k] is not None}
        rows.append({"symbol": c["symbol"], "date": c["date"], "checked": bool(diffs),
                     "diffs": {k: round(v, 4) for k, v in diffs.items()},
                     "pass": bool(diffs) and all(v <= tol[k] for k, v in diffs.items())})
    done = [r for r in rows if r["checked"]]
    worst = max((v for r in done for v in r["diffs"].values()), default=None)
    out = {"n": len(done), "n_pass": sum(1 for r in done if r["pass"]), "max_diff": worst, "rows": rows}
    if len(done) < MIN_ROWS:
        return no_data(f"{len(done)} name-days checked; need {MIN_ROWS}", **out)
    return {"status": "ok", **out}
