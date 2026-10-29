"""Per-sleeve forward record, read from the virtual books (state/books.json) — the books are built only from
fills, so this is the forward test's own evidence. Pure functions over the book documents."""
import math
import os
import statistics
from datetime import datetime, timezone

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic

US_SESSION = ("EQ", "OPT")     # instruments that trade only in the NYSE session; every other kind trades every day
PERIODS = {"us": 252, "always": 365}


def market(book):
    """'us' when every instrument the book holds or traded trades only in the NYSE session (a book that never traded
    too), else 'always': a book whose value can move on any calendar day"""
    insts = set(book.get("positions") or {}) | {t.get("inst") for t in book.get("trades") or () if t.get("inst")}
    return "us" if all(str(i).split(":")[0] in US_SESSION for i in insts) else "always"


def _daily_curve(curve, sessions=False):
    """last equity per ET date from [[ts, equity], ...]; sessions: NYSE trading days only (a US book is marked on
    weekends and holidays too, at the value it closed with: those days were flat returns that diluted its Sharpe by
    about sqrt(5/7) and counted toward its "trading days")."""
    out = {}
    for ts, eq in curve or ():
        d = datetime.fromtimestamp(float(ts), tz=ET).date()
        if sessions and not cal.is_trading_day(d):
            continue
        out[d.isoformat()] = float(eq)
    return sorted(out.items())


def max_drawdown(values):
    peak, mdd = None, 0.0
    for v in values:
        peak = v if peak is None else max(peak, v)
        if peak and peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


def sleeve_stats(book, capital=None):
    """book: one sleeve's book document."""
    cap = float(book.get("capital") or capital or 100_000.0)
    trades = list(book.get("trades") or [])
    marks = book.get("marks") or {}
    mv = 0.0
    unreal = 0.0
    gross = 0.0
    for inst, p in (book.get("positions") or {}).items():
        m = 100.0 if inst.startswith("OPT:") else 1.0
        px = float(marks.get(inst, p.get("avg") or 0.0))
        q = float(p.get("qty") or 0.0)
        mv += q * px * m
        gross += abs(q) * px * m
        unreal += (px - float(p.get("avg") or 0.0)) * q * m
    equity = float(book.get("cash", cap)) + mv
    pnls = [float(t.get("pnl") or 0.0) for t in trades]
    rets = [float(t["ret"]) for t in trades if t.get("ret") is not None]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    holds = [(float(t["closed_at"]) - float(t["opened_at"])) / 86400.0 for t in trades
             if t.get("closed_at") and t.get("opened_at")]
    by_reason = {}
    for t in trades:
        r = str(t.get("reason") or "exit").split(":")[0].split(" ")[0][:40] or "exit"
        e = by_reason.setdefault(r, {"n": 0, "pnl": 0.0})
        e["n"] += 1
        e["pnl"] = round(e["pnl"] + float(t.get("pnl") or 0.0), 2)
    daily = _daily_curve(book.get("curve"))              # every date with a mark: the paper record's days
    mkt = market(book)
    points = _daily_curve(book.get("curve"), sessions=True) if mkt == "us" else daily   # its market's trading days
    vals = [v for _, v in points]
    drets = [vals[i] / vals[i - 1] - 1.0 for i in range(1, len(vals)) if vals[i - 1] > 0]
    sharpe = None
    moments = {"ret_n": len(drets), "ret_mean": None, "ret_sd": None, "ret_skew": None, "ret_kurt": None}
    if len(drets) >= 10:
        sd = statistics.pstdev(drets)
        if sd > 0:
            mu = statistics.mean(drets)
            sharpe = mu / sd * math.sqrt(PERIODS[mkt])
            moments.update(ret_mean=mu, ret_sd=sd,
                           ret_skew=sum((x - mu) ** 3 for x in drets) / len(drets) / sd ** 3,
                           ret_kurt=sum((x - mu) ** 4 for x in drets) / len(drets) / sd ** 4)   # raw (normal = 3)
    return {
        "capital": round(cap, 2), "equity": round(equity, 2), "return_pct": round(100.0 * (equity / cap - 1.0), 4),
        "realized": round(float(book.get("realized") or 0.0), 2), "unrealized": round(unreal, 2),
        "fees": round(float(book.get("fees") or 0.0), 2), "gross": round(gross, 2),
        "exposure_pct": round(100.0 * gross / equity, 2) if equity > 0 else None,
        "open_positions": len(book.get("positions") or {}), "fills": int(book.get("n_fills") or 0),
        "trades": len(trades), "win_rate": round(len(wins) / len(pnls), 4) if pnls else None,
        "avg_win": round(statistics.mean(wins), 2) if wins else None,
        "avg_loss": round(statistics.mean(losses), 2) if losses else None,
        "profit_factor": round(sum(wins) / -sum(losses), 4) if losses and sum(losses) < 0 else None,
        "expectancy_ret": round(statistics.mean(rets), 6) if rets else None,
        "expectancy_usd": round(statistics.mean(pnls), 2) if pnls else None,
        "avg_hold_days": round(statistics.mean(holds), 2) if holds else None,
        "max_drawdown_pct": round(100.0 * max_drawdown(vals), 4) if vals else 0.0,
        "sharpe": round(sharpe, 3) if sharpe is not None else None, "days": len(daily),
        "trading_days": len(points), "market": mkt,
        "first_day": daily[0][0] if daily else None, "last_day": daily[-1][0] if daily else None,
        "exits_by_reason": by_reason,
        "last_trade_at": max((float(t.get("closed_at") or 0) for t in trades), default=None),
        **moments,
    }


def report(root, now=None):
    """the attribution report for the desk at root; written to state/report.json."""
    books = read_json(os.path.join(root, "state", "books.json"), {}) or {}
    sleeves = {sid: sleeve_stats(b) for sid, b in sorted(books.items())}
    tot = {"capital": 0.0, "equity": 0.0, "realized": 0.0, "unrealized": 0.0, "fees": 0.0, "trades": 0,
           "open_positions": 0}
    for s in sleeves.values():
        for k in tot:
            tot[k] += s.get(k) or 0
    tot = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in tot.items()}
    tot["return_pct"] = round(100.0 * (tot["equity"] / tot["capital"] - 1.0), 4) if tot["capital"] else None
    ranked = sorted(((sid, s["return_pct"]) for sid, s in sleeves.items() if s["fills"]), key=lambda kv: -kv[1])
    out = {"generated_at": datetime.fromtimestamp(now or datetime.now(timezone.utc).timestamp(), tz=timezone.utc)
           .isoformat(timespec="seconds"), "desk": tot, "sleeves": sleeves,
           "leaders": ranked[:10], "laggards": ranked[-10:][::-1]}
    write_json_atomic(os.path.join(root, "state", "report.json"), out)
    return out
