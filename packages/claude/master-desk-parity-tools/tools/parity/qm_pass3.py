"""qm_pass3: the qullamaggie pass-3 sleeves (desk/sleeves/families/qullamaggie.py) vs the source desk itself —
desk_fixed.py (midna @7969b522 workspace/qualla_desk/pass3/, vendored byte-exact and hash-pinned by
tests/test_vendor.py), run on frames built here directly from the synthetic arrays, never through the sleeves'
converters.

Markets: per seed 150 completed sessions of a QQQ trend (mostly risk-on, sometimes falling), 52 noise names, two
planted leaders (an impulse of 35-90% into a tight 10-session base), two quiet names that gap 4-22% on a random
session with a random catalyst (an 8-K / 6-K at minute -900..+80, verified or not, heavy or light first 20
minutes), two parabolic names (three up sessions of +30-90%, or +200-350% for a sub-$300M cap; EDGAR-style share
counts), each planted name with a 60-minute tape on the last 8 sessions (random drift / volatility / opening gap).

  scan    one pass of a sleeve at a random completed minute of a random session: the screen on the genome-style
          bars, the watch (breakout prefilter / EP pool x events x opening gap and volume / parabolic candidates x
          market cap), the minute tapes, the trigger check and the sleeve's _scan, with a random opening equity and
          random occupied budget rows -> the proposals (every Proposal field), against AgenticResearchDesk.scan on
          the source frames with every planted name's tape through the same minute. Proves the converters, the
          watch prefilters (lossless) and the reduced daily frame of the EP / short scans exact.
  replay  a sleeve's whole run over the 8 sessions on the source's information set (the hindsight the source's
          backtest had: the day's stops before its scan, the close as the scale price, fills at the source's
          prices + slippage, the parabolic target on the day's post-entry bars) with every decision taken by the
          sleeve's own methods (_open_pass, _entries -> _scan, _scale, _scale_book, _after_close / trail_exit,
          ma_target, occupied_row) -> the trades, against the source's backtest() with setup_precedence = [the
          setup] and the removed desk_eod_loss_lock disabled (max_daily_loss_pct = inf). Compared exactly (date,
          symbol, setup, side, quantity, entry, exit, P&L, reason) up to the first session where the live rule of
          divergence 5 applies (an entry stopped out in its own session keeps counting toward that session's later
          triggers: the sleeve decides each trigger when it prints); such sessions are counted, not compared.

    python3 -m tools.parity.run qm_pass3"""
import math
import random
from dataclasses import asdict
from types import SimpleNamespace

import numpy as np
import pandas as pd

from desk import calendar as cal
from desk.sleeves.families import qullamaggie as Q
from desk.util import et_date
from desk.vendor.qullamaggie_pass3 import desk_fixed as E

from . import write_receipt

END = "2026-09-30"
N_DAYS = 150
N_INTRA = 8
TAPE_MIN = 60
N_NOISE = 52
SEEDS_SCAN = 15
SEEDS_REPLAY = 30
SID = {v: k for k, v in Q.SETUP_OF.items()}
SECTORS = ["Technology", "Life Sciences", "Energy & Transportation", "Finance", "Manufacturing"]


def _days():
    d, out = cal._as_date(END), [END]
    while len(out) < N_DAYS + N_INTRA:
        d = cal.prev_trading_day(d)
        out.append(d.isoformat())
    return out[::-1]


def _t(day):
    """Alpaca's daily stamp: 04:00 UTC of the session date."""
    from datetime import datetime, timezone
    d = cal._as_date(day)
    return datetime(d.year, d.month, d.day, 4, tzinfo=timezone.utc).timestamp()


def _bar(day, o, h, lo, c, v):
    return {"t": _t(day), "o": float(o), "h": float(h), "l": float(lo), "c": float(c), "v": float(v)}


def _walk_bars(days, closes, rng, rp=0.02, vol=1e6):
    out, prev = [], closes[0]
    for d, c in zip(days, closes):
        o = round(prev * (1 + rng.normal(0, 0.004)), 2)
        c = round(c, 2)
        h = round(max(o, c) * (1 + abs(rng.normal(0, rp / 2))), 2)
        lo = round(min(o, c) * (1 - abs(rng.normal(0, rp / 2))), 2)
        out.append(_bar(d, o, h, lo, c, vol))
        prev = c
    return out


def _tape(day, start, mu, sig, base_vol, rng, heavy20=1.0):
    """a 60-minute tape (contiguous minutes) and its daily aggregate."""
    o0 = cal.session_open(day)
    rows, px = [], start
    for m in range(TAPE_MIN):
        o = round(px, 2)
        c = round(px * (1 + rng.normal(mu, sig)), 2)
        h = round(max(o, c) * (1 + abs(rng.normal(0, sig / 2))), 2)
        lo = round(min(o, c) * (1 - abs(rng.normal(0, sig / 2))), 2)
        v = float(int(base_vol / 390 * rng.uniform(0.5, 1.5) * (heavy20 if m < 20 else 1.0)))
        rows.append({"t": o0 + 60 * m, "o": o, "h": h, "l": lo, "c": c, "v": v})
        px = c
    agg = _bar(day, rows[0]["o"], max(r["h"] for r in rows), min(r["l"] for r in rows), rows[-1]["c"],
               sum(r["v"] for r in rows) * 6.5)
    return rows, agg


def market(seed):
    rnd = random.Random(seed)
    rng = np.random.default_rng(seed)
    days = _days()
    hist, intra = days[:N_DAYS], days[N_DAYS:]
    mk = {"days": days, "intra": intra, "daily": {}, "tapes": {d: {} for d in intra}, "events": [], "meta": {},
          "planted": []}
    qd = rnd.choice([0.002, 0.002, 0.0015, 0.0025, -0.0015])
    qc = list(400 * np.exp(np.cumsum(rng.normal(qd, 0.004, len(days)))))
    mk["daily"]["QQQ"] = _walk_bars(days, qc, rng, rp=0.01, vol=5e7)
    for k in range(N_NOISE):
        cl = list(40 * np.exp(np.cumsum(rng.normal(0, 0.014, len(days)))))
        mk["daily"][f"N{k:02d}"] = _walk_bars(days, cl, rng)
    for j in range(2):                                     # leaders
        s = f"L{j}"
        up = rnd.randint(45, 60)
        gain = rnd.uniform(0.35, 0.9)
        flat = N_DAYS - up - 10
        cl = list(50 * (1 + rng.normal(0, 0.004, flat)))
        cl += [50 * (1 + gain) ** ((i + 1) / up) * (1 + rng.normal(0, 0.006)) for i in range(up)]
        top = cl[-1]
        width = rnd.uniform(0.01, 0.05)
        base = []
        for i in range(10):
            span = width * (1.0 if i < 5 else rnd.uniform(0.4, 1.1))
            c = top * (1 + rnd.uniform(-span / 2, span / 2))
            base.append(c)
        bars = _walk_bars(hist[:N_DAYS - 10], cl, rng, rp=0.025)
        prev = bars[-1]["c"]
        lo0 = top * (1 - width)
        for i, (d, c) in enumerate(zip(hist[N_DAYS - 10:], base)):
            o, c = round(prev, 2), round(c, 2)
            lo = round(min(o, c, lo0 * (1 + 0.002 * i * rnd.uniform(0, 1.5))), 2)
            h = round(max(o, c) * (1 + rnd.uniform(0.002, width)), 2)
            bars.append(_bar(d, o, h, lo, c, 1e6))
            prev = c
        mk["daily"][s] = bars
        pivot = max(b["h"] for b in bars[-10:])
        mk["planted"].append((s, "leader", {"mu": rnd.uniform(0.0001, 0.0012), "sig": rnd.uniform(0.0005, 0.002),
                                            "start": pivot * (1 - rnd.uniform(0.001, 0.008))}))
        mk["meta"][s] = {"sector": rnd.choice(SECTORS)}
    for j in range(2):                                     # episodic pivots
        s = f"E{j}"
        cl = list(30 * (1 + rng.normal(0, 0.004, N_DAYS)))
        mk["daily"][s] = _walk_bars(hist, cl, rng, rp=rnd.uniform(0.02, 0.06))
        k = rnd.randrange(N_INTRA)
        ev_min = rnd.randint(-900, 30) if rnd.random() < 0.85 else rnd.randint(30, 80)
        mk["planted"].append((s, "ep", {"day": intra[k], "gap": rnd.uniform(0.06, 0.25),
                                        "heavy": rnd.uniform(8.0, 30.0), "mu": rnd.uniform(-0.0003, 0.0012),
                                        "sig": rnd.uniform(0.0006, 0.0025)}))
        mk["events"].append({"date": intra[k], "symbol": s, "event_type": rnd.choice(["8-K 2.02 Results", "6-K",
                                                                                       "8-K 8.01 Other Events"]),
                             "news_verified": rnd.random() < 0.8, "event_minute": ev_min})
        if rnd.random() < 0.3:                             # a second, later filing the same session
            mk["events"].append({"date": intra[k], "symbol": s, "event_type": "8-K 7.01 Reg FD",
                                 "news_verified": True, "event_minute": rnd.randint(ev_min, 90)})
        mk["meta"][s] = {"sector": rnd.choice(SECTORS)}
    for j in range(2):                                     # parabolic runs
        s = f"P{j}"
        k = rnd.randrange(1, N_INTRA)
        small = rnd.random() < 0.35
        run = rnd.uniform(2.0, 3.5) if small else rnd.uniform(0.3, 0.9)
        n_flat = N_DAYS + k - 3
        cl = list(20 * (1 + rng.normal(0, 0.003, n_flat)))
        cl[-1] = 19.9
        step = (1 + run) ** (1 / 3)
        cl += [19.9 * step, 19.9 * step ** 2, 19.9 * (1 + run)]
        mk["daily"][s] = _walk_bars(days[:len(cl)], cl, rng, rp=0.03)
        close = round(19.9 * (1 + run), 2)
        mcap_target = rnd.uniform(1.0e8, 2.9e8) if small else rnd.uniform(4e8, 5e9)
        mk["meta"][s] = {"sector": rnd.choice(SECTORS), "shares": float(int(mcap_target / close))}
        mk["planted"].append((s, "para", {"day": days[len(cl)], "mu": rnd.uniform(-0.0015, 0.0003),
                                          "sig": rnd.uniform(0.002, 0.006)}))
    # tapes on the intraday sessions (planted names); their daily bars are the tapes' aggregates
    for s, kind, p in mk["planted"]:
        for d in intra:
            if kind == "para" and d < p["day"]:
                continue                                  # the run's sessions keep their daily bars
            prev = [b for b in mk["daily"][s] if et_date(b["t"]) < d][-1]["c"]
            gap, heavy = rng.normal(0, 0.008), 1.0
            if kind == "ep" and d == p["day"]:
                gap, heavy = p["gap"], p["heavy"]
            if kind == "para" and d == p["day"]:
                gap = rng.normal(0.01, 0.02)
            start = prev * (1 + gap)
            if kind == "leader" and d == intra[0]:
                start = p["start"]                         # the first session opens just under the base pivot
            mu = p["mu"]
            if (kind == "leader" and d != intra[0]) or (kind == "ep" and d > p["day"]):
                mu = rng.uniform(-0.0012, 0.0012)          # the sessions after the setup: drift either way
            if kind == "ep" and d < p["day"]:
                mu = rng.uniform(-0.0004, 0.0004)          # a quiet tape until the catalyst
            rows, agg = _tape(d, start, mu, p["sig"], 1e6, rng, heavy20=heavy)
            mk["tapes"][d][s] = rows
            mk["daily"][s] = sorted([b for b in mk["daily"][s] if et_date(b["t"]) != d] + [agg], key=lambda b: b["t"])
    return mk


# -- source-side frames (built directly from the arrays) -------------------------------------------------------------
def src_daily(mk, upto):
    rows = [(et_date(b["t"]), s, b["o"], b["h"], b["l"], b["c"], b["v"]) for s, bl in mk["daily"].items() for b in bl
            if et_date(b["t"]) <= upto]
    return pd.DataFrame(rows, columns=Q.DAILY_COLS).sort_values(["date", "symbol"]).reset_index(drop=True)


def src_intraday(mk, days, minute_lt=None):
    rows = []
    for d in days:
        o = cal.session_open(d)
        for s, bl in mk["tapes"][d].items():
            for b in bl:
                m = int((b["t"] - o) // 60)
                if minute_lt is None or m < minute_lt:
                    rows.append((d, s, m, b["o"], b["h"], b["l"], b["c"], b["v"]))
    return pd.DataFrame(rows, columns=Q.INTRADAY_COLS)


def src_universe(mk, upto):
    out = []
    for s in mk["daily"]:
        m = mk["meta"].get(s) or {}
        last = [b["c"] for b in mk["daily"][s] if et_date(b["t"]) < upto]
        cap = float(m["shares"]) * float(last[-1]) if m.get("shares") and last else float("nan")
        out.append({"symbol": s, "sector": m.get("sector", "UNKNOWN"), "market_cap": cap, "borrowable": True})
    return pd.DataFrame(out, columns=Q.UNIVERSE_COLS)


def src_universe_pit(mk):
    """the point-in-time universe the source's _metadata reads through its asof_date column: per session, the
    market cap = shares x the last close before it."""
    out = []
    for d in mk["intra"]:
        u = src_universe(mk, d)
        u["asof_date"] = d
        out.append(u)
    return pd.concat(out, ignore_index=True)


def src_events(mk):
    return pd.DataFrame(mk["events"], columns=Q.EVENT_COLS)


def _p(props):
    return [asdict(p) for p in props]


# -- the sleeve side -----------------------------------------------------------------------------------------------------
def session_memo(mk, day):
    """the sleeves' shared session memo, built from the genome-style bars before the session."""
    Q.reset()
    bars = {s: [b for b in bl if et_date(b["t"]) < day] for s, bl in mk["daily"].items()}
    memo = dict(Q._memo_for(day, bars, [], cal.session_open(day) - 3600))
    Q.reset()
    return memo


def _sleeve(setup, mk, day, memo):
    sl = Q.QullaSetup(SID[setup], universe=tuple(mk["daily"]))
    st = {"watch": sl._screen(memo, day), "pos": {}}
    sl._refresh_watch(st, {"qm_events": [e for e in mk["events"] if e["date"] == day],
                           "qm_meta": {s: dict(m) for s, m in mk["meta"].items()}}, memo, day)
    return sl, st


def sleeve_scan(setup, mk, day, m, equity, occupied, memo):
    now = cal.session_open(day) + 60 * m + 5
    sl, st = _sleeve(setup, mk, day, memo)
    st["day"] = {"session": day, "equity": equity, "marks": {}, "decided": {}, "ep_checked": {}, "exiting": [],
                 "entries": {r["symbol"]: dict(r, qty=0.0, open=0.0) for r in occupied}}
    view = SimpleNamespace(session=day, now=now, quotes={}, positions={}, extra={"pending_orders": []},
                           cash=equity, equity=equity,
                           bars={"1m": {s: [b for b in bl if b["t"] + 60 <= now] for s, bl in mk["tapes"][day].items()}})
    got = []
    orig = sl._scan

    def wrap(*a, **k):
        r = orig(*a, **k)
        got.append(r)
        return r
    sl._scan = wrap
    intents = sl._entries(view, st, memo, {})
    props = got[0][0] if got else []
    return _p(props), intents, st


def source_scan(setup, mk, day, m, equity, occupied):
    cfg = dict(Q.CFG, setup_precedence=[setup])
    acc, audit, _ = E.AgenticResearchDesk(cfg).scan(day, src_daily(mk, day), src_intraday(mk, [day], m),
                                                    src_events(mk), src_universe(mk, day), equity, list(occupied))
    return _p(acc)


def run_scan(stats, diffs):
    rnd = random.Random(20261016)
    n = same = 0
    for seed in range(SEEDS_SCAN):
        mk = market(seed)
        for day in mk["intra"]:
            memo = session_memo(mk, day)
            for setup in ("breakout", "episodic_pivot", "parabolic_short"):
                for _ in range(2):
                    m = rnd.randint(5, TAPE_MIN)
                    equity = rnd.choice([100_000.0, rnd.uniform(20_000, 250_000)])
                    occ = [{"symbol": f"X{i}", "notional": rnd.uniform(0, 40_000), "sector": rnd.choice(SECTORS),
                            "risk": rnd.uniform(0, 2_500)} for i in range(rnd.choice([0, 0, 1, 3, 15]))]
                    ours, intents, st = sleeve_scan(setup, mk, day, m, equity, occ, memo)
                    theirs = source_scan(setup, mk, day, m, equity, occ)
                    n += 1
                    stats["proposals"][setup] += len(theirs)
                    stats["enter_intents"] += sum(1 for i in intents if i.kind == "enter")
                    if ours == theirs:
                        same += 1
                    else:
                        diffs.append({"kind": "scan", "seed": seed, "day": day, "setup": setup, "minute": m,
                                      "ours": ours[:3], "theirs": theirs[:3]})
    Q.reset()
    return n, same


# -- replay: the sleeve's decisions on the backtest's information set ------------------------------------------------
def _fill(price, side, entry, cfg):
    return E._fill_price(price, side, entry, cfg)


def replay(setup, mk):
    """the sleeve's own methods for every decision, the source's fill model and information set."""
    cfg = dict(Q.CFG, setup_precedence=[setup], max_daily_loss_pct=float("inf"))
    sl = Q.QullaSetup(SID[setup], universe=tuple(mk["daily"]))
    cash = float(cfg["initial_cash"])
    book, trades, st = {}, [], {"pos": {}}
    marks_live = {}
    flagged, curve = [], []

    def held_view():
        return {s: {"qty": p["qty"], "avg": p["entry"], "opened_at": p["opened_at"], "stop": p["stop"],
                    "pm": p["pm"], "mark": marks_live.get(s), "exiting": False} for s, p in book.items()}

    def close(s, qty, raw, date, reason):
        nonlocal cash
        p = book[s]
        side = 1 if p["qty"] > 0 else -1
        qty = min(qty, abs(p["qty"]))
        px = _fill(raw, side, False, cfg)
        exit_fees = raw * qty * float(cfg["commission_bps"]) / 10_000
        entry_fees = p["entry"] * qty * float(cfg["commission_bps"]) / 10_000
        pnl = side * (px - p["entry"]) * qty - entry_fees - exit_fees
        cash += side * qty * px
        cash -= exit_fees
        trades.append({"date": date, "symbol": s, "setup": p["pm"]["setup"], "side": side, "quantity": qty,
                       "entry": p["entry"], "exit": px, "pnl": pnl, "reason": reason})
        p["qty"] -= side * qty
        if abs(p["qty"]) < 1e-12:
            book.pop(s)

    dates = mk["intra"]
    for di, date in enumerate(dates):
        day_bars = {s: next(b for b in bl if et_date(b["t"]) == date) for s, bl in mk["daily"].items()
                    if any(et_date(b["t"]) == date for b in bl)}
        opens = {s: b["o"] for s, b in day_bars.items()}
        closes = {s: b["c"] for s, b in day_bars.items()}
        tapes = mk["tapes"][date]
        for s in book:
            marks_live[s] = opens.get(s, book[s]["entry"])
        # the session's open: the sleeve's opening snapshot and its queued trail exits (at the open)
        o0 = cal.session_open(date)
        view = SimpleNamespace(session=date, now=o0 + 20, cash=cash,
                               quotes={s: {"day_open": opens.get(s), "day_date": date} for s in book})
        memo = session_memo(mk, date)
        for it in sl._open_pass(view, st, memo, held_view()):
            if it.kind == "exit" and it.symbol in book and it.symbol in opens:
                close(it.symbol, abs(book[it.symbol]["qty"]), opens[it.symbol], date, "close_below_trailing_MA")
            elif it.kind == "adjust" and it.symbol in book and it.target is not None:
                book[it.symbol]["target"] = float(it.target)
        # the day's hard stops on the minute bars (the backtest's information set: before its scan)
        for s in list(book):
            p = book[s]
            for b in tapes.get(s, []):
                side = 1 if p["qty"] > 0 else -1
                if side == 1 and b["l"] <= p["stop"]:
                    close(s, abs(p["qty"]), min(b["o"], p["stop"]), date, "hard_stop")
                    break
                if side == -1 and b["h"] >= p["stop"]:
                    close(s, abs(p["qty"]), max(b["o"], p["stop"]), date, "hard_stop")
                    break
        # the scan on the session's whole tape (one pass after the last minute), the sleeve deciding
        st["watch"] = sl._screen(memo, date)
        sl._refresh_watch(st, {"qm_events": [e for e in mk["events"] if e["date"] == date],
                               "qm_meta": {s: dict(m) for s, m in mk["meta"].items()}}, memo, date)
        now = o0 + 60 * TAPE_MIN + 5
        ev = SimpleNamespace(session=date, now=now, quotes={}, positions={}, extra={"pending_orders": []}, cash=cash,
                             equity=cash, bars={"1m": {s: list(bl) for s, bl in tapes.items()}})
        got = []
        orig = sl._scan

        def wrap(*a, **k):
            r = orig(*a, **k)
            got.append(r)
            return r
        sl._scan = wrap
        intents = sl._entries(ev, st, memo, held_view())
        sl._scan = orig
        props = {p.symbol: p for p in (got[0][0] if got else [])}
        held_before = set(book)
        entered = {it.symbol for it in intents if it.kind == "enter"}
        blocked = set(props) - entered - held_before         # accepted by the scan, refused by the entry loop
        same_session_stops = 0
        for it in intents:
            if it.kind != "enter":
                continue
            prop = props[it.symbol]
            side = int(prop.side)
            entry = _fill(prop.entry, side, True, cfg)
            qty = int(prop.quantity)
            minute = int(prop.trigger_time.split("+")[-1])
            pm = dict(it.meta["position_meta"])
            book[it.symbol] = {"qty": side * qty, "entry": entry, "stop": prop.stop, "pm": pm, "opened_at": o0 + 60 * minute,
                               "minute": minute, "date": date, "target": it.target}
            cash -= side * qty * entry
            cash -= entry * qty * float(cfg["commission_bps"]) / 10_000
            bl = tapes.get(it.symbol, [])
            stopped = None
            for b in bl:
                m = int((b["t"] - o0) // 60)
                if m < minute:
                    continue
                if side == 1 and b["l"] <= prop.stop:
                    stopped = min(b["o"], prop.stop)
                    break
                if side == -1 and b["h"] >= prop.stop:
                    stopped = max(b["o"], prop.stop)
                    break
            if stopped is not None:
                close(it.symbol, qty, stopped, date, "same_session_hard_stop")
                same_session_stops += 1
        if same_session_stops and blocked:                  # divergence 5: the backtest's loop released them
            flagged.append(date)
        # the close: the scale (the close is the price), breakeven, the trail, the short's target
        cview = SimpleNamespace(session=date, now=cal.session_close(date) - 14 * 60, quotes={s: {"last": closes.get(s)}
                                                                                            for s in book})
        st["day"] = dict(st.get("day") or {}, session=date)
        sync_book(st, book, date)
        for it in sl._scale(cview, st, memo, held_view()):
            s = it.symbol
            if s in closes:
                close(s, int(it.qty), closes[s], date, "scale_after_strength")
        held_after = held_view()
        for s, ps in st["pos"].items():                         # the scale fill shrank the position
            sent = ps.get("scale_sent")
            if sent and s in book:
                held_after[s]["qty"] = book[s]["qty"]
        for it in sl._scale_book(st, held_after, date):
            if it.kind == "adjust" and it.symbol in book:
                p = book[it.symbol]
                p["stop"] = max(p["stop"], float(it.stop)) if p["qty"] > 0 else min(p["stop"], float(it.stop))
        aview = SimpleNamespace(session=date, now=cal.session_close(date) + 30 * 60,
                                bars={"1d": {s: [b for b in mk["daily"][s] if et_date(b["t"]) <= date] for s in book}})
        st.pop("eod", None)
        sl._after_close(aview, st, held_view())
        for s in list(book):
            p = book[s]
            if p["qty"] < 0 and s in closes:
                hist = [b["c"] for b in mk["daily"][s] if et_date(b["t"]) < date]
                tgt = Q.ma_target(hist)
                if tgt is None:
                    continue
                post = [b for b in tapes.get(s, []) if (date > p["date"]) or int((b["t"] - o0) // 60) > p["minute"]]
                if post and min(b["l"] for b in post) <= tgt:
                    close(s, abs(p["qty"]), min(opens.get(s, tgt), tgt), date, "parabolic_MA_target")
        for s in book:
            marks_live[s] = closes.get(s, book[s]["entry"])
        curve.append({"date": date, "equity": cash + sum((1 if p["qty"] > 0 else -1) * abs(p["qty"])
                                                         * closes.get(s, p["entry"]) for s, p in book.items()),
                      "open_positions": len(book)})
        if di + 1 < len(dates):
            st["pending_exits"]["session"] = dates[di + 1]
    Q.reset()
    return trades, flagged, curve


def sync_book(st, book, session):
    pos = st.setdefault("pos", {})
    for s in list(pos):
        if s not in book:
            pos.pop(s)
    for s, p in book.items():
        rec = pos.setdefault(s, {})
        if rec.get("opened_at") != p["opened_at"]:
            rec.clear()
            rec.update(opened_at=p["opened_at"], entry_session=p["date"])


def backtest(setup, mk):
    cfg = dict(Q.CFG, setup_precedence=[setup], max_daily_loss_pct=float("inf"))
    trades, curve = E.backtest(src_daily(mk, mk["intra"][-1]), src_intraday(mk, mk["intra"]), src_events(mk),
                               src_universe_pit(mk), cfg, start_date=mk["intra"][0])
    keep = ["date", "symbol", "setup", "side", "quantity", "entry", "exit", "pnl", "reason"]
    tr = [] if trades.empty else [{k: (v.item() if hasattr(v, "item") else v) for k, v in r.items() if k in keep}
                                  for r in trades.to_dict("records")]
    cv = [{"date": r["date"], "equity": float(r["equity"]), "open_positions": int(r["open_positions"])}
          for r in curve.to_dict("records")]
    return tr, cv


def _close_enough(a, b):
    if set(a) != set(b):
        return False
    for k in a:
        x, y = a[k], b[k]
        if isinstance(x, float) or isinstance(y, float):
            if not (x == y or (math.isnan(float(x)) and math.isnan(float(y)))):
                return False
        elif x != y:
            return False
    return True


def run_replay(stats, diffs):
    n = same = 0
    for seed in range(SEEDS_REPLAY):
        mk = market(1000 + seed)
        for setup in ("breakout", "episodic_pivot", "parabolic_short"):
            ours, flagged, our_curve = replay(setup, mk)
            theirs, their_curve = backtest(setup, mk)
            cut = min(flagged) if flagged else None
            o = [t for t in ours if cut is None or t["date"] < cut]
            t_ = [t for t in theirs if cut is None or t["date"] < cut]
            oc = [c for c in our_curve if cut is None or c["date"] < cut]
            tc = [c for c in their_curve if cut is None or c["date"] < cut]
            k = len(mk["intra"]) if cut is None else mk["intra"].index(cut)
            n += k
            stats["replay_trades"][setup] += len(t_)
            stats["replay_open_at_end"][setup] += (tc[-1]["open_positions"] if tc else 0)
            if cut is not None:
                stats["divergence_5_sessions"] += 1
            if len(o) == len(t_) and all(_close_enough(a, b) for a, b in zip(o, t_)) and oc == tc:
                same += k
            else:
                diffs.append({"kind": "replay", "seed": 1000 + seed, "setup": setup, "ours": o[:6], "theirs": t_[:6],
                              "curve_ours": oc[-3:], "curve_theirs": tc[-3:]})
    return n, same


def run():
    stats = {"proposals": {"breakout": 0, "episodic_pivot": 0, "parabolic_short": 0}, "enter_intents": 0,
             "replay_trades": {"breakout": 0, "episodic_pivot": 0, "parabolic_short": 0},
             "replay_open_at_end": {"breakout": 0, "episodic_pivot": 0, "parabolic_short": 0},
             "divergence_5_sessions": 0}
    diffs = []
    n1, s1 = run_scan(stats, diffs)
    n2, s2 = run_replay(stats, diffs)
    res = {"sleeve": "qm_pass3", "cases": n1 + n2, "identical": s1 + s2, "diffs": diffs[:40], "n_diffs": len(diffs),
           "stats": dict(stats, scan_cases=n1, scan_identical=s1, replay_sessions=n2, replay_identical=s2),
           "method": "the sleeves' scan path and management (desk/sleeves/families/qullamaggie.py) vs desk_fixed.py's "
                     "AgenticResearchDesk.scan / backtest() (the vendored source, blob 6df5d6cb) on frames built "
                     "directly from the synthetic arrays",
           "named_divergences": 10, "removed_gates": ["desk_eod_loss_lock (max_daily_loss_pct 1.5%)"],
           "sleeves": sorted(SID.values())}
    write_receipt("qm_pass3", res)
    return res
