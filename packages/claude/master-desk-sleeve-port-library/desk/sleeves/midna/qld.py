"""midna_qld_weekly_timing — Midna's QLD timing book (src/lib/felipe/pullback.ts @ entire 43f08f96, blob da620bd7:
runQld, completedWeeks / toWeeks / cleanDays / weekStart; src/lib/lector/pine.ts ema), forward-tested on the engine.

  rule     fully invested in QLD while the prior completed QQQ week has EMA(12) above EMA(26) of the weekly closes
           (SMA-seeded EMAs over QQQ's whole adjusted daily history, as felipe/live.ts fetched it: Yahoo daily from
           1990-01-01, OHLC scaled by adjclose / close); entries and exits at the open of the week's first session
  size     the whole book: notional = cash / (1 + 0.1%) (runQld's cost)

Removed: none — runQld carries no desk gate.

Named divergences: runQld is the source's walk-forward backtest (scripts/felipe-pullback.ts ran it over the daily
history; the desk only read the trend, qldState); here its weekly decision runs forward: in each week's first
regular-hours pass (once per week) the prior weeks are complete — runQld's week i reads EMA[i - 1] — and the order
is an engine child at the live quote (the backtest booked the week's opening print and charged 0.1% per side in its
own ledger, the engine its venue schedule); the daily history is the producer feed desk/feedlib/midna_qld.py
(refreshed every 12 hours, the felipe cache's age)."""
from datetime import date, timedelta

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

SOURCE = {"repo": "midna", "ref": "entire", "commit": "43f08f96fce33ee67521002e09f8bc7534cfe264",
          "path": "src/lib/felipe/pullback.ts", "blob": "da620bd787610653ccb4b3b46ba46e828a3b6944",
          "lines": [474, 520], "ema": {"path": "src/lib/lector/pine.ts"}, "data": {"path": "src/lib/felipe/live.ts"}}
COST = 0.001
NAV = 100_000.0


def clean_days(days):
    out = {}
    for d in days:
        if not (d["close"] > 0) or not (d["high"] > 0):
            continue
        o = d["open"] if d["open"] > 0 else d["close"]
        lo = d["low"] if d["low"] > 0 else min(o, d["close"])
        out[d["date"]] = {"date": d["date"], "open": o, "high": max(d["high"], o, d["close"], lo),
                          "low": min(lo, o, d["close"]), "close": d["close"]}
    return [out[k] for k in sorted(out)]


def week_start(ymd):
    d = date.fromisoformat(ymd)
    return (d - timedelta(days=d.weekday())).isoformat()


def to_weeks(days):
    groups = {}
    for d in days:
        k = week_start(d["date"])
        g = groups.get(k)
        if g is None:
            groups[k] = dict(d)
            continue
        g["high"] = max(g["high"], d["high"])
        g["low"] = min(g["low"], d["low"])
        g["close"] = d["close"]
        g["date"] = d["date"]
    return sorted(groups.values(), key=lambda w: w["date"])


def completed_weeks(days):
    weeks = to_weeks(clean_days(days))
    if weeks and date.fromisoformat(weeks[-1]["date"]).isoweekday() % 7 != 5:
        weeks.pop()
    return weeks


def ema(values, length):
    out = [None] * len(values)
    if length < 1 or len(values) < length:
        return out
    s = 0.0
    for i in range(length):
        s += values[i]
    prev = s / length
    out[length - 1] = prev
    alpha = 2 / (length + 1)
    for i in range(length, len(values)):
        prev = values[i] * alpha + prev * (1 - alpha)
        out[i] = prev
    return out


def run_qld(qqq_days, qld_days, frm=None, to=None, cost=COST):
    """runQld, line for line -> {"curve", "trips", "open"}."""
    frm = frm or "0000-01-01"
    qqq_weeks = completed_weeks(qqq_days)
    qld_by = {week_start(w["date"]): w for w in completed_weeks(qld_days)}
    closes = [w["close"] for w in qqq_weeks]
    fast, slow = ema(closes, 12), ema(closes, 26)
    curve, trips = [], []
    cash, holding = 1.0, None
    for i in range(1, len(qqq_weeks)):
        bar = qld_by.get(week_start(qqq_weeks[i]["date"]))
        if not bar:
            continue
        if bar["date"] < frm:
            continue
        if to is not None and bar["date"] >= to:
            break
        on = fast[i - 1] is not None and slow[i - 1] is not None and fast[i - 1] > slow[i - 1]
        if on and not holding and bar["open"] > 0:
            before = cash
            notional = cash / (1 + cost)
            cash = 0.0
            holding = {"entry": bar["open"], "notional": notional, "before": before, "entryDate": bar["date"]}
        elif not on and holding:
            cash = holding["notional"] * (bar["open"] / holding["entry"]) * (1 - cost)
            trips.append({"entryDate": holding["entryDate"], "exitDate": bar["date"],
                          "ret": 0 if holding["before"] == 0 else cash / holding["before"] - 1})
            holding = None
        equity = holding["notional"] * (bar["close"] / holding["entry"]) + cash if holding else cash
        curve.append({"date": bar["date"], "equity": equity})
    return {"curve": curve, "trips": trips, "open": holding is not None}


def trend_for_week(qqq_days, monday):
    """the decision of the week starting `monday`: EMA(12) > EMA(26) on the QQQ weeks before it (runQld's i - 1).
    -> (on, last week's date, fast, slow) or None while the EMAs are warming up."""
    weeks = to_weeks(clean_days([d for d in qqq_days if d["date"] < monday]))
    closes = [w["close"] for w in weeks]
    fast, slow = ema(closes, 12), ema(closes, 26)
    if not weeks or fast[-1] is None or slow[-1] is None:
        return None
    return fast[-1] > slow[-1], weeks[-1]["date"], fast[-1], slow[-1]


class QldWeeklyTiming(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_qld_weekly_timing", family="midna", cadence_s=300, capital=NAV, universe=("QLD",),
            schedule="rth", needs={"quotes": {"source": "equity", "symbols": ["QLD"]}, "feeds": ["midna_qld_daily"]},
            params={"fast": 12, "slow": 26, "cost": COST, "removed_gates": []}, source=SOURCE,
            state_schema={"week": "str|None", "on": "bool|None"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        st = dict(view.state or {})
        self._st = st
        monday = week_start(view.session)
        if st.get("week") == monday:
            return []
        feed = view.extra.get("midna_qld_daily") or {}
        qqq = feed.get("QQQ") or []
        if not qqq or not any(d["date"] >= M.add_days(monday, -7) for d in qqq):
            return []                                       # the prior week is not in the history yet: wait
        tr = trend_for_week(qqq, monday)
        if tr is None:
            return []
        on, last_week, fast, slow = tr
        q = M.mq(view.quotes.get("QLD"))
        held = M.equity_positions(view).get("QLD")
        out = []
        why = f"QQQ week of {last_week}: EMA12 {fast:.4f} {'>' if on else '<='} EMA26 {slow:.4f}"
        if on and not held:
            if not q:
                return []                                   # no QLD print yet: the week waits for one
            out.append(Intent("enter", "QLD", notional=float(view.cash) / (1 + COST), price_hint=q["ask"] or q["last"],
                              signal_key=f"qld:{monday}:buy", reason=why, order=OrderSpec(window_s=6 * 3600)))
        elif not on and held:
            out.append(Intent("exit", "QLD", price_hint=(q or {}).get("bid") or (q or {}).get("last"),
                              signal_key=f"qld:{monday}:sell", reason=why, order=OrderSpec(window_s=6 * 3600)))
        st.update(week=monday, on=on, decided=last_week)
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
