"""qullamaggie_paper: the reconstruction engine's own backtest() (desk/vendor/aurelia_qulla/desk.py, the
strategy's definition) vs the restored sleeve's decision functions driven session by session through the same
fill model — the open (queued trail exits, the open-loss lock, the opening budget snapshot), the session's stops
(the engine's _first_intraday_exit: what the engine stop executes), the entries (the sleeve's scan on each
name's 1-minute tape rebuilt by the carrier's _minutes law from print-only bars), the close (the 1/3 scale,
the residual stop to breakeven) and the after-close trail.

Per case: QQQ (up-trending with a risk-off dip) + the 20 names over 260 sessions, several built into leader
breakouts (a 40-110% impulse into a tight 10-session base) whose breakout session's tape crosses the pivot
(the next minute opening above or back under the trigger), the sessions after them drifting up or rolling
over; 1-minute tapes (09:30-11:29, silent minutes dropped from the print-only bars) for every name over the
last 45 sessions. The fill model is the backtest's (entry x (1 + 10bp), exits x (1 - 10bp), 1bp fees each
side). Compared: every trade leg (session, symbol, reason, quantity, entry, exit) and the final cash."""
import math
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from . import femto_module, trading_dates, write_receipt

F = femto_module("qullamaggie_paper")
E = F.engine
ET = ZoneInfo("America/New_York")
N_CASES = 8
TAPE_MIN = 120


def _row(d, o, h, l, c, v):
    return {"date": d, "o": round(o, 4), "h": round(max(o, h, c), 4), "l": round(min(o, l, c), 4), "c": round(c, 4),
            "v": float(int(v))}


def _walk(rnd, days, px, drift, vol, vmin=4e5, vmax=4e6):
    out = []
    for d in days:
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(1.0, px * (1 + rnd.gauss(drift, vol)))
        out.append(_row(d, o, max(o, c) * (1 + abs(rnd.gauss(0, vol / 2))), min(o, c) * (1 - abs(rnd.gauss(0, vol / 2))),
                        c, rnd.uniform(vmin, vmax)))
        px = c
    return out


def _built(rnd, days, brk):
    """flat/drifting into a 53-session impulse, a 10-session base ending the session before `brk`, then the
    breakout session and an aftermath that drifts up or rolls over."""
    px = rnd.uniform(20, 200)
    pre = _walk(rnd, days[:brk - 63], px, 0.0003, 0.015)
    px = pre[-1]["c"]
    gain = rnd.uniform(0.4, 1.1)
    step = (1 + gain) ** (1 / 53) - 1
    imp = []
    for d in days[brk - 63:brk - 10]:
        o = px * (1 + rnd.gauss(0, 0.004))
        c = px * (1 + step + rnd.gauss(0, 0.01))
        imp.append(_row(d, o, max(o, c) * 1.006, min(o, c) * 0.994, c, rnd.uniform(1e6, 6e6)))
        px = c
    top = px
    g = rnd.choice((0.003, 0.002, 0.0015))
    base = []
    for i, d in enumerate(days[brk - 10:brk]):
        tight = 1.0 if i < 5 else 0.6
        c = top * (1 + g * (i + 1)) * (1 + rnd.gauss(0, 0.004 * tight))
        o = c * (1 + rnd.gauss(0, 0.003 * tight))
        base.append(_row(d, o, max(o, c) * (1 + 0.004 * tight), min(o, c) * (1 - 0.004 * tight), c, rnd.uniform(1e6, 6e6)))
    drift = rnd.choice((0.012, 0.006, -0.006, -0.012))
    after = _walk(rnd, days[brk:], base[-1]["c"], drift, 0.018, 1e6, 6e6)
    if rnd.random() < 0.45 and len(after) > 5:                # an overnight gap down a few sessions in (the lock)
        g = rnd.randint(2, 4)
        f = rnd.uniform(0.86, 0.92)
        r = after[g]
        after[g] = _row(r["date"], after[g - 1]["c"] * f, after[g - 1]["c"] * f * 1.01, after[g - 1]["c"] * f * 0.98,
                        after[g - 1]["c"] * f * 1.003, r["v"])
        for j in range(g + 1, len(after)):
            r = after[j]
            after[j] = _row(r["date"], r["o"] * f, r["h"] * f, r["l"] * f, r["c"] * f, r["v"])
    return pre + imp + base + after


def _tape(rnd, d, o_day, n, cross=None):
    """print-only 1-minute bars for one session (a silent minute is absent); `cross` = (minute, trigger, next
    open factor, pre-trigger floor) forces a breakout crossing."""
    start = datetime.fromisoformat(d).replace(hour=9, minute=30, tzinfo=ET)
    px, rows = o_day, []
    for k in range(n):
        o = px * (1 + rnd.gauss(0, 0.0006))
        c = px * (1 + rnd.gauss(0.0001, 0.0015))
        h, l = max(o, c) * (1 + abs(rnd.gauss(0, 0.0008))), min(o, c) * (1 - abs(rnd.gauss(0, 0.0008)))
        if cross:
            km, trig, nxt, floor = cross
            if k < km:
                h, o, c = min(h, trig * 0.999), min(o, trig * 0.998), min(c, trig * 0.998)
                l = max(min(l, o, c), floor)
                o, c = max(o, l), max(c, l)
            elif k == km:
                h = max(h, trig * 1.002)
            elif k == km + 1:
                o = trig * nxt
                c = o * (1 + rnd.gauss(0, 0.001))
                h, l = max(o, c) * 1.0008, min(o, c) * 0.9992
        rows.append((k, o, max(o, h, c), min(o, l, c), c, rnd.uniform(2e3, 4e4)))
        px = c
    out = []
    for k, o, h, l, c, v in rows:
        if 0 < k < n - 1 and rnd.random() < 0.01:
            continue                                          # a silent minute (no print)
        out.append({"t": (start + timedelta(minutes=k)).timestamp(), "o": round(o, 4), "h": round(h, 4),
                    "l": round(l, 4), "c": round(c, 4), "v": float(int(v))})
    return out


def _case(rnd, k):
    days = trading_dates("2025-08-04", 260)
    win = days[-45:]
    qqq = _walk(rnd, days[:-45], 400.0, 0.0012, 0.008)
    dip_at = rnd.randint(8, 30)
    for i, d in enumerate(win):
        drift = -0.012 if dip_at <= i < dip_at + 6 else 0.002
        qqq += _walk(rnd, [d], qqq[-1]["c"], drift, 0.006)
    daily = {"QQQ": qqq}
    names = list(F.UNIVERSE)
    built = rnd.sample(names, rnd.randint(4, 7))
    brk = {}
    for s in names:
        if s in built:
            b = len(days) - 45 + rnd.randint(2, 38)
            brk[s] = days[b]
            daily[s] = _built(rnd, days, b)
        else:
            daily[s] = _walk(rnd, days, rnd.uniform(20, 300), rnd.uniform(-0.0005, 0.0012), rnd.uniform(0.01, 0.02))
    tapes = {}
    for s in names:
        rows = {r["date"]: r for r in daily[s]}
        prev = {d: daily[s][i - 1]["c"] for i, d in enumerate(days) if i}
        for d in win:
            cross = None
            if brk.get(s) == d:
                bi = days.index(d)
                pivot = max(r["h"] for r in daily[s][bi - 10:bi])
                km = rnd.randint(8, 70)
                floor = pivot * (1 - rnd.choice((0.004, 0.008, 0.03)))
                cross = (km, pivot * 1.0005, rnd.choice((1.002, 1.004, 0.995)), floor)
                o_day = pivot * (1 - rnd.uniform(0.001, 0.004))
            else:
                o_day = rows[d]["o"]
            bars = _tape(rnd, d, o_day, TAPE_MIN, cross)
            tapes.setdefault(s, {})[d] = bars
            if cross:                                         # the session's daily bar carries its tape
                lo = min(b["l"] for b in bars)
                hi = max(b["h"] for b in bars)
                r = rows[d]
                r.update(o=bars[0]["o"], h=max(hi, r["h"], r["c"]), l=min(lo, r["l"], r["c"]))
    return {"days": days, "win": win, "daily": daily, "tapes": tapes, "built": built, "brk": brk}


def _frames(c):
    rows = [{"date": r["date"], "symbol": s, "open": r["o"], "high": r["h"], "low": r["l"], "close": r["c"],
             "volume": r["v"]} for s, rl in c["daily"].items() for r in rl]
    daily = pd.DataFrame(rows).sort_values(["date", "symbol"]).reset_index(drop=True)
    pieces = []
    for s, by in c["tapes"].items():
        for d, bars in by.items():
            x = F.tape(bars, s, d)
            if x is not None:
                pieces.append(x.drop(columns=["security_id"]))
    intraday = pd.concat(pieces, ignore_index=True).sort_values(["date", "symbol", "minute_from_open"])
    universe = F.universe_frame(sorted(c["daily"]), c["days"][0])
    return daily, intraday, universe


def _epoch(rows):
    return [{"t": datetime.fromisoformat(r["date"]).replace(hour=4, tzinfo=timezone.utc).timestamp(), "o": r["o"],
             "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]


def _replay(c, daily, intraday):
    """the sleeve's decisions through the backtest's fill model, session by session."""
    cfg = F.CFG
    cash = float(cfg["initial_cash"])
    slip, comm = float(cfg["slippage_bps"]) / 1e4, float(cfg["commission_bps"]) / 1e4
    bars_all = {s: _epoch(rl) for s, rl in c["daily"].items()}
    by_date = {s: {r["date"]: r for r in rl} for s, rl in c["daily"].items()}
    book, meta, trades = {}, {}, []
    counts = {"proposals": 0}

    def close_leg(s, qty, raw, d, reason):
        nonlocal cash
        p = book[s]
        qty = min(qty, p["qty"])
        px = E._fill_price(raw, 1, False, cfg)                 # the backtest's _close_position arithmetic
        fees_x = raw * qty * float(cfg["commission_bps"]) / 10_000
        fees_e = p["entry_px"] * qty * float(cfg["commission_bps"]) / 10_000
        trades.append({"date": d, "symbol": s, "quantity": int(qty), "entry": round(p["entry_px"], 6),
                       "exit": round(px, 6), "reason": reason, "pnl": round(1 * (px - p["entry_px"]) * qty - fees_e - fees_x, 6)})
        cash += 1 * qty * px
        cash -= fees_x
        p["qty"] -= qty
        if p["qty"] <= 0:
            del book[s]

    def state():
        return {s: {"position": {"qty": p["qty"], "entry_px": p["entry_px"], "entry_date": p["entry_date"],
                                 "stop_px": p["stop"], "stop_level": p["stop"], "scaled_third": p["scaled"] or None,
                                 "gap_buffer_pct": p["gap_pct"], "sector": p["sector"]}} for s, p in book.items()}

    prev_d = None
    for d in c["win"]:
        bars = {s: [b for b in bl if F._bar_date(b) < d] for s, bl in bars_all.items()}
        forming = {s: {"o": by_date[s][d]["o"]} for s in by_date if d in by_date[s]}
        if (meta.get("watch") or {}).get("date") != d:
            ms, watch = F.watch_list(F.daily_frame(bars), d)
            meta["watch"] = {"date": d, "symbols": watch, "market_state": ms}
        exits, op = F.open_actions(state(), meta, forming, {}, cash, d, prev_session=prev_d)
        meta["open"] = op
        for i in exits:
            close_leg(i.symbol, book[i.symbol]["qty"], forming[i.symbol]["o"], d,
                      "close_below_trailing_MA" if i.signal_key.endswith(":trail") else "desk_open_loss_lock")
        for s in list(book):                                  # the session's stops (existing positions)
            p = book[s]
            ev = E._first_intraday_exit(intraday[(intraday.symbol == s) & (intraday.date == d)], 1, p["stop"])
            if ev is not None:
                close_leg(s, p["qty"], ev[0], d, ev[1])
        tapes = {s: F.tape(c["tapes"][s][d], s, d) for s in (meta["watch"]["symbols"] or []) if d in c["tapes"][s]}
        ents, _rows = F.entries(bars, tapes, state(), meta, d, forming, {})
        counts["proposals"] += len(ents)
        for it in sorted(ents, key=lambda i: (int(i.position_meta["trigger_time"].split("+")[-1]), i.symbol)):
            entry = E._fill_price(it.position_meta["entry_ref"], 1, True, cfg)
            qty = it.qty_hint
            cash -= 1 * qty * entry
            cash -= entry * qty * float(cfg["commission_bps"]) / 10_000
            book[it.symbol] = {"qty": qty, "entry_px": entry, "entry_date": d, "stop": it.stop, "scaled": False,
                               "gap_pct": it.position_meta["gap_buffer_pct"], "sector": it.position_meta["sector"]}
            em = int(it.position_meta["trigger_time"].split("+")[-1])
            ev = E._first_intraday_exit(intraday[(intraday.symbol == it.symbol) & (intraday.date == d)], 1, it.stop,
                                        None, start_minute=em)
            if ev is not None:
                close_leg(it.symbol, qty, ev[0], d, "same_session_" + ev[1])
        closes = {s: by_date[s][d]["c"] for s in by_date if d in by_date[s]}
        quotes = {s: {"last": closes[s]} for s in book}
        for it in F.close_scale(bars, state(), quotes, d, ()):
            s = it.symbol
            close_leg(s, it.qty_hint, closes[s], d, "scale_after_strength")
            if s in book:
                book[s]["scaled"] = True
                book[s]["stop"] = max(book[s]["stop"], book[s]["entry_px"])
        bars_d = {s: [b for b in bl if F._bar_date(b) <= d] for s, bl in bars_all.items()}
        syms, complete = F.eod_trail(bars_d, state(), d, ())
        assert complete
        meta["pending_exits"] = {"session": F._next_session(d, ()), "syms": syms}
        meta["eod"] = {"date": d, "equity": F.eod_equity(bars_d, state(), cash, d)}
        prev_d = d
    return trades, cash, counts


def run():
    rnd = random.Random(61)
    n = same = 0
    diffs = []
    counts = {"trades": 0, "entries": 0, "same_session_hard_stop": 0, "hard_stop": 0, "scale_after_strength": 0,
              "close_below_trailing_MA": 0, "desk_open_loss_lock": 0, "risk_off_sessions": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": str(a)[:600], "new": str(b)[:600]})

    for ci in range(N_CASES):
        c = _case(rnd, ci)
        daily, intraday, universe = _frames(c)
        cfg = dict(F.CFG)
        events = pd.DataFrame(columns=F.EVENT_COLS)
        tr, curve = E.backtest(daily, intraday, events, universe, cfg)
        old = [] if tr.empty else [
            {"date": r["date"], "symbol": r["symbol"], "quantity": int(r["quantity"]), "entry": round(float(r["entry"]), 6),
             "exit": round(float(r["exit"]), 6), "reason": r["reason"], "pnl": round(float(r["pnl"]), 6)}
            for r in tr.to_dict("records")]
        new, cash, cnt = _replay(c, daily, intraday)
        key = lambda t: (t["date"], t["symbol"], t["reason"])
        cmp("trades", ci, sorted(old, key=key), sorted(new, key=key))
        end_cash = float(curve.cash.iloc[-1]) if not curve.empty else float(cfg["initial_cash"])
        cmp("cash", ci, round(end_cash, 4), round(cash, 4))
        counts["trades"] += len(old)
        counts["entries"] += cnt["proposals"]
        for t in old:
            counts[t["reason"]] = counts.get(t["reason"], 0) + 1
        counts["risk_off_sessions"] += int((curve.market_state != "risk_on").sum()) if not curve.empty else 0
    res = {"sleeve": "qullamaggie_paper", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("qullamaggie_paper", res)
    return res
