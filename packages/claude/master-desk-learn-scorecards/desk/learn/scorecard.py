"""The old desk's graduation bar (desk/LIVE_GRADUATION_CRITERIA.md), measured per sleeve on its forward
record. Graduation is a PROPOSAL for User — there is no auto-graduation path, and a negative-expectancy
sleeve is flagged for review, never silently benched.

  1 expectancy   >= 30 closed trades, expectancy > 0 after costs, on the closed trades and on the record with its
                 open positions marked (closed P&L + the open marks, per closed or open trade: MAC-03)
  2 sharpe       annualized daily Sharpe >= 1.0 (>= 20 trading days of equity)
  3 drawdown     max drawdown < 30%
  4 beats_spy    return > SPY buy-and-hold over the same window
  5 regimes      profitable in both halves of its record (a walk-forward proxy for trend/chop), the later half
                 carrying the open positions' marks
  6-8            one-parameter plateau, economic reason, real-world tradability: judged by people
  paper_30d      >= 30 days of paper record"""
from datetime import date


def _halves_ok(book, unrealized=0.0):
    """the closed record's two halves both profitable; the later one carries the open positions' marks (their outcome
    is the record's most recent, still unresolved)."""
    trades = sorted(book.get("trades") or [], key=lambda t: float(t.get("closed_at") or 0))
    if len(trades) < 20:
        return None
    h = len(trades) // 2
    a = sum(float(t.get("pnl") or 0) for t in trades[:h])
    b = sum(float(t.get("pnl") or 0) for t in trades[h:]) + float(unrealized or 0.0)
    return a > 0 and b > 0


def score(stats, book, spy_return_pct=None):
    """MAC-03 (Edge audit 2026-10-25): expectancy and regimes judged closed trades only, so a rule that closes only its
    winners passed while its open book lost (mk_connorsdouble7: 78 closing fills all winners, +$38,017, beside 590
    open positions at -$34,176). Both now also need the record with the open positions marked; open marks never pass
    a record its closed trades fail."""
    rows = {}
    n = stats.get("trades") or 0
    exp = stats.get("expectancy_usd")
    n_open = int(stats.get("open_positions") or 0)
    unreal = float(stats.get("unrealized") or 0.0)
    closed = sum(float(t.get("pnl") or 0.0) for t in book.get("trades") or [])
    marked = (closed + unreal) / (n + n_open) if n + n_open else None
    rows["expectancy"] = "PENDING" if n < 30 else (
        "PASS" if exp is not None and exp > 0 and marked is not None and marked > 0 else "FAIL")
    sh = stats.get("sharpe")
    td = stats.get("trading_days", stats.get("days")) or 0              # its market's sessions (attribution.market)
    rows["sharpe"] = "PENDING" if td < 20 or sh is None else ("PASS" if sh >= 1.0 else "FAIL")
    rows["drawdown"] = "PASS" if (stats.get("max_drawdown_pct") or 0) < 30 else "FAIL"
    if spy_return_pct is None or not stats.get("days"):
        rows["beats_spy"] = "PENDING"
    else:
        rows["beats_spy"] = "PASS" if stats["return_pct"] > spy_return_pct else "FAIL"
    hv = _halves_ok(book, unreal)
    rows["regimes"] = "PENDING" if hv is None else ("PASS" if hv else "FAIL")
    rows["paper_30d"] = "PASS" if (stats.get("days") or 0) >= 30 else "PENDING"
    for k in ("plateau", "economic_reason", "tradable"):
        rows[k] = "JUDGED"
    measurable = [rows[k] for k in ("expectancy", "sharpe", "drawdown", "beats_spy", "regimes", "paper_30d")]
    if all(v == "PASS" for v in measurable):
        verdict = "PROPOSE"                     # clears every measurable criterion: a proposal for User
    elif n >= 30 and ((exp is not None and exp < 0) or (marked is not None and marked < 0)):
        verdict = "REVIEW"                      # negative expectancy over >= 30 trades: User's decision
    elif "FAIL" in measurable:
        verdict = "BELOW_BAR"
    else:
        verdict = "ACCUMULATING"
    return {"criteria": rows, "verdict": verdict,
            "expectancy": {"closed_usd": exp, "with_open_usd": round(marked, 2) if marked is not None else None,
                           "open_positions": n_open, "unrealized": round(unreal, 2)}}


def spy_return(spy_bars, first_day, last_day):
    """SPY buy-and-hold % between two ISO dates from daily bars {"t", "c"} (t = 04:00 UTC of the date)."""
    from datetime import datetime, timezone
    if not spy_bars or not first_day or not last_day:
        return None
    rows = [(datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat(), float(b["c"]))
            for b in spy_bars]
    a = [c for d, c in rows if d <= first_day]
    b = [c for d, c in rows if d <= last_day]
    if not a or not b or a[-1] <= 0:
        return None
    return 100.0 * (b[-1] / a[-1] - 1.0)
