"""midna_hourly_playbook — Midna's Hourly Tensor book under the frozen playbook 1.0.0 (src/lib/equity/rules.ts @
cursor/lector-desk-f184 fd0e0a07, blob 352c91fc: evaluatePass's exits and considerEntries, entryWindow, timeExitAt,
planForNewEntry, killedMatch; fires.ts parseInboxFire, blob fd0e2a75; desk.ts runDeskPass's inputs, blob 01c4ee98),
ported line for line, on the hourly watch's inbox (desk/feedlib/midna_watch.py, the tensor-watch.mjs port).

  account   $100,000; 20 slots of $5,000; lane caps 1h 5 / 1d 5 / 1w 10
  fires     the inbox: a gap20, first-of-setup 1H consensus-buy fire of the swing basket (unit 1h-basket, max 60
            bars); a fire is decided once (seen): skipped when its setup episode (sym:lane:unit:fireBar) already
            traded, when its unit / tags match a killed rule (KILLED), when it is not tradeable or not from Yahoo
            bars, when a 1H fire is not the first of its gap20 episode, when its entry deadline passed (stale), when
            dv20 (the mean of the last 20 close x volume) is unknown or below $1,000,000
  entry     inside the window [the next bar's open, + 30 min] (1H; 1D / 1W: the next session's 09:30, + 65 min),
            best rank first (meta decile x 1e6 + score, then symbol): a 1H entry only in regular hours; a name already
            held is skipped; a full lane (or 20 open) waits for the next pass inside the window (capacityWait);
            a fresh quote (<= 15 min, <= 1 min ahead) whose last is within the lane's limit band over the fire close
            (1H 3%, 1D / 1W 5%) — else it waits; slot = min($5,000, 1% of dv20); cash below 90% of the slot skips
            ("insufficient cash"); qty = floor(min(slot, cash) / paper price) (the ask to the cent, else last + the
            research cost)
  plan      1h-basket: no stop / time exit 60 bars; otherwise the calibrated stop / max bars (default 40, 1W 52)
  exit      regular hours, a fresh quote: the plan's stop (last <= entry x (1 - stop%)) or the time exit
            (timeExitAt: the close of the 60th hourly bar from the entry bar; 1D the close of the max_bars-th session;
            1W the last session of the max_bars-th week) at the bid (else last - the research cost)

Removed (cutover doctrine): state.halted ("entries halted" — the desk kill switch).

Named divergences: fills are engine children at the source's paper price (the source booked them at once); a
working entry counts as held and a working exit as gone (common.virtual_book); the inbox / watch-stamp / tracker
file hand-offs are the watch job's cache read in-pass (the Midna checkout's tracker file latest_fires_v3.json was the
frozen research snapshot of 2026-10-02 — every fire in it past its entry deadline — so the book trades the watch's
1H fires); dv20 is computed from the desk's completed daily bars (the source's Yahoo 6-month chart could include the
forming session's partial bar), once per ET day per name as the source cached it; the inherited book (positions
adopted at the playbook's birth, plan source "inherited") and the operator flatten request are not carried — the
book starts flat; the narrative records (lines, lessons, beliefs, Saturday review) are not kept. The calendar is
common.py's."""
import math
from datetime import datetime

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

SOURCE = {"repo": "midna", "ref": "cursor/lector-desk-f184", "commit": "fd0e0a07caaf658b0c349517115e1d5491e9d79e",
          "path": "src/lib/equity/rules.ts", "blob": "352c91fcf451e3e9ad833af6f91c2d38b844f12a",
          "fires": {"path": "src/lib/equity/fires.ts", "blob": "fd0e2a75e9fc"},
          "desk": {"path": "src/lib/equity/desk.ts", "blob": "01c4ee9879ff"},
          "producer": {"path": "scripts/tensor-watch.mjs", "blob": "c3777a913452223d86b5c9013f4addcae04e8081"}}
ACCOUNT_USD = 100_000.0
SLOTS = 20
SLOT_USD = 5_000.0
MIN_SLOT_FRACTION = 0.9
MIN_DV20 = 1_000_000.0
LANE_CAPS = {"1h": 5, "1d": 5, "1w": 10}
MAX_DELAY_MIN = {"1h": 30, "1d": 65, "1w": 65}
LIMIT_BAND = {"1h": 0.03, "1d": 0.05, "1w": 0.05}
KILLED_IDS = ["bl-1", "academic-volume-shock", "f-book-51.8", "red-day-policy", "moonshot-in-slots",
              "style-cap-switch", "alt-exit", "drawdown-halt", "mtf-stack", "loser-veto", "single-name-short",
              "sector-rollover", "midna-20d", "felipe-ls", "rsi-obv", "raschke", "textbook-long", "autopilot",
              "crypto-lane", "sentiment", "static-tza"]
REMOVED = ["state.halted: 'entries halted' (desk kill switch)"]


def ms_of(iso):
    """new Date(iso).getTime() / 1000 for the ISO stamps the fires carry (None when unparseable: NaN)."""
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _num(v, fallback):
    if isinstance(v, bool):
        return fallback
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else fallback
    if isinstance(v, str):
        try:
            x = float(v.strip()) if v.strip() else 0.0           # Number("") is 0
        except ValueError:
            return fallback
        return x if math.isfinite(x) else fallback
    return fallback


def _stamp(v):
    return v if not v or "T" in v else v.replace(" ", "T", 1)


def parse_inbox_fire(raw):
    """fires.ts parseInboxFire."""
    lane = raw.get("lane")
    if lane not in ("1h", "1d", "1w"):
        return None
    key = str(raw.get("key") or "")
    sym = str(raw.get("sym") or raw.get("symbol") or "")
    unit = str(raw.get("unit") or "")
    if not key or not sym or not unit:
        return None
    fb = raw.get("fireBar") if raw.get("fireBar") is not None else raw.get("fire_bar")
    return {"key": key, "sym": sym, "lane": lane, "unit": unit, "fireBar": _stamp(str(fb or "")),
            "fireClose": _num(raw.get("fireClose") if raw.get("fireClose") is not None else raw.get("close"), 0.0),
            "tradeable": raw.get("tradeable") is True,
            "gap20": raw["gap20"] if isinstance(raw.get("gap20"), bool) else None,
            "firstOfSetup": raw["firstOfSetup"] if isinstance(raw.get("firstOfSetup"), bool) else None,
            "barSource": str(raw.get("barSource") or raw.get("bar_source") or "yahoo:inbox"),
            "metaDecile": _num(raw.get("metaDecile"), None), "score": _num(raw.get("score"), 0.0),
            "tags": [str(t) for t in raw["tags"]] if isinstance(raw.get("tags"), list) else [],
            "calibratedStopPct": _num(raw.get("stopPct") if raw.get("stopPct") is not None else raw.get("stop_pct"),
                                      None),
            "calibratedMaxBars": _num(raw.get("maxBars") if raw.get("maxBars") is not None else raw.get("max_bars"),
                                      None)}


def entry_window(lane, fire_bar):
    """rules.ts entryWindow -> (start, deadline) epochs."""
    p = M.et_parts(fire_bar)
    if lane == "1h":
        nxt = p["minutes"] + 60
        if nxt < M.session_close_minutes(p["ymd"]):
            start = M.et_to_epoch(p["ymd"], nxt // 60, nxt % 60)
        else:
            start = M.et_to_epoch(M.next_trading_day(p["ymd"]), 9, 30)
        return start, start + MAX_DELAY_MIN["1h"] * 60
    start = M.et_to_epoch(M.next_trading_day(p["ymd"]), 9, 30)
    return start, start + MAX_DELAY_MIN[lane] * 60


def time_exit_at(lane, entry_start, max_bars):
    """rules.ts timeExitAt -> epoch."""
    if lane == "1h":
        left = max_bars
        ymd = M.et_parts(entry_start)["ymd"]
        for _ in range(40):
            if not M.is_trading_day(ymd):
                ymd = M.next_trading_day(M.add_days(ymd, -1))
            close = M.session_close_minutes(ymd)
            cursor = 9 * 60 + 30
            while cursor < close:
                start = M.et_to_epoch(ymd, cursor // 60, cursor % 60)
                end_min = min(cursor + 60, close)
                end = M.et_to_epoch(ymd, end_min // 60, end_min % 60)
                if start >= entry_start - 1:
                    left -= 1
                    if left == 0:
                        return end
                cursor += 60
            ymd = M.next_trading_day(ymd)
        return entry_start
    if lane == "1d":
        ymd = M.et_parts(entry_start)["ymd"]
        left = max_bars
        while left > 1:
            ymd = M.next_trading_day(ymd)
            left -= 1
        close = M.session_close_minutes(ymd)
        return M.et_to_epoch(ymd, close // 60, close % 60)
    p = M.et_parts(entry_start)
    monday = M.add_days(p["ymd"], -((p["weekday"] + 6) % 7) + (max_bars - 1) * 7)
    friday = M.add_days(monday, 4)
    while not M.is_trading_day(friday):
        friday = M.add_days(friday, -1)
    close = M.session_close_minutes(friday)
    return M.et_to_epoch(friday, close // 60, close % 60)


def killed_match(fire):
    blob = " ".join([fire["unit"]] + list(fire["tags"])).lower()
    for k in KILLED_IDS:
        if k in blob:
            return k
    return None


def plan_for_new_entry(fire):
    if fire["lane"] == "1h" and fire["unit"] == "1h-basket":
        return {"scheme": "no stop / time exit 60 bars", "stopPct": None, "maxBars": 60, "source": "playbook-1.0.0"}
    mb = fire["calibratedMaxBars"]
    stop = fire["calibratedStopPct"]
    if stop is not None:
        scheme = f"calibrated stop {M.js_num(stop)}% / {M.js_num(mb if mb is not None else 40)} bars"
    else:
        scheme = "calibrated plan"
    return {"scheme": scheme, "stopPct": stop, "maxBars": mb if mb is not None else (52 if fire["lane"] == "1w" else 40),
            "source": "calibrated"}


def stop_price(entry, plan):
    st = plan.get("stopPct")
    if st is None or not st < 99:
        return None
    return entry * (1 - st / 100)


def rank_score(fire):
    d = fire["metaDecile"] if fire["metaDecile"] is not None else 5.5
    return d * 1_000_000 + fire["score"]


def episode_id(fire):
    return f"{fire['sym']}:{fire['lane']}:{fire['unit']}:{fire['fireBar']}"


def dv20_of(bars):
    """quotes.ts fetchDv20 on daily bars: the mean of the last 20 close x volume with volume > 0 (Array.reduce)."""
    pairs = [float(b["c"]) * float(b["v"]) for b in bars if b.get("c") is not None and (b.get("v") or 0) > 0]
    tail = pairs[-20:]
    return M.js_sum(tail) / len(tail) if len(tail) >= 20 else None


def step(book, now, quotes, fires, dv20):
    """evaluatePass's exits + considerEntries on book = {"cash", "positions": [open {id, sym, lane, unit, qty,
    entryAvg, entryFill, timeExitAt, plan, ...}], "seen", "episodes", "capacityWait"} (mutated). -> orders."""
    orders = []
    phase = M.phase_at(now)
    book["cash"] = M.round2(book["cash"])
    for p in list(book["positions"]):
        q = quotes.get(p["sym"])
        if phase != "rth" or not M.quote_is_fresh(q, now):
            continue
        stop = stop_price(p["entryAvg"], p["plan"])
        through_stop = stop is not None and q["last"] <= stop
        through_time = now >= p["timeExitAt"]
        if not through_stop and not through_time:
            continue
        fill = M.paper_fill(q, "sell")
        if not fill:
            continue
        reason = f"stop {M.js_num(p['plan']['stopPct'])}% at {M.js_num(fill[0])}" if through_stop else \
            f"time exit {M.js_num(p['plan']['maxBars'])} bars"
        book["cash"] = M.round2(book["cash"] + p["qty"] * fill[0])
        book["positions"].remove(p)
        orders.append({"side": "sell", "sym": p["sym"], "qty": p["qty"], "px": fill[0], "id": p["id"],
                       "reason": reason})
    candidates = []
    for fire in fires:
        if book["seen"].get(fire["key"]):
            continue
        if book["episodes"].get(episode_id(fire)):
            book["seen"][fire["key"]] = {"action": "skip", "reason": "setup episode already traded", "at": now}
            continue
        killed = killed_match(fire)
        if killed:
            book["seen"][fire["key"]] = {"action": "skip", "reason": f"killed rule {killed}", "at": now}
            continue
        if not fire["tradeable"]:
            book["seen"][fire["key"]] = {"action": "skip", "reason": "not tradeable", "at": now}
            continue
        if not fire["barSource"].startswith("yahoo"):
            book["seen"][fire["key"]] = {"action": "skip", "reason": "non-canonical bar source", "at": now}
            continue
        fb = ms_of(fire["fireBar"])
        if fire["lane"] == "1h" and (fire["gap20"] is None or fire["firstOfSetup"] is None):
            if fb is not None and now > entry_window(fire["lane"], fb)[1]:
                book["seen"][fire["key"]] = {"action": "skip", "at": now,
                                             "reason": "stale: entry deadline passed before the setup was confirmed"}
            continue
        if fire["lane"] == "1h" and (not fire["gap20"] or not fire["firstOfSetup"]):
            book["seen"][fire["key"]] = {"action": "skip", "reason": "not the first fire of its setup episode", "at": now}
            continue
        if fb is None:                                  # new Date(NaN): every comparison false -> waits forever
            continue
        start, deadline = entry_window(fire["lane"], fb)
        if now > deadline:
            waits = book["capacityWait"].pop(fire["key"], 0)
            reason = f"stale: entry deadline passed (capacity-blocked at {waits} pass(es))" if waits else \
                "stale: entry deadline passed"
            book["seen"][fire["key"]] = {"action": "skip", "reason": reason, "at": now}
            continue
        if now < start:
            continue
        dv = dv20.get(fire["sym"])
        if dv is None:
            book["seen"][fire["key"]] = {"action": "skip", "reason": "illiquid/unknown: dv20 unavailable", "at": now}
            continue
        if dv < MIN_DV20:
            book["seen"][fire["key"]] = {"action": "skip", "at": now,
                                         "reason": f"illiquid: dv20 {M.js_round(dv)} < {int(MIN_DV20)}"}
            continue
        candidates.append((fire, start, deadline))
    candidates.sort(key=lambda c: (-rank_score(c[0]), M.locale_key(c[0]["sym"])))
    for fire, start, deadline in candidates:
        if fire["lane"] == "1h" and phase != "rth":
            continue
        lane_used = sum(1 for p in book["positions"] if p["lane"] == fire["lane"])
        if any(p["sym"] == fire["sym"] for p in book["positions"]):
            book["seen"][fire["key"]] = {"action": "skip", "reason": "symbol already held", "at": now}
            continue
        if len(book["positions"]) >= SLOTS or lane_used >= LANE_CAPS[fire["lane"]]:
            book["capacityWait"][fire["key"]] = book["capacityWait"].get(fire["key"], 0) + 1
            continue
        q = quotes.get(fire["sym"])
        if not M.quote_is_fresh(q, now):
            continue
        fill = M.paper_fill(q, "buy")
        if not fill:
            continue
        cap = fire["fireClose"] * (1 + LIMIT_BAND[fire["lane"]])
        if q["last"] > cap:
            continue
        slot_cap = min(SLOT_USD, dv20[fire["sym"]] * 0.01)
        if book["cash"] < MIN_SLOT_FRACTION * min(slot_cap, SLOT_USD):
            book["seen"][fire["key"]] = {"action": "skip", "reason": "insufficient cash", "at": now}
            continue
        budget = min(slot_cap, book["cash"])
        qty = math.floor(budget / fill[0])
        if qty < 1:
            book["seen"][fire["key"]] = {"action": "skip", "reason": "price above a whole-share slot", "at": now}
            continue
        plan = plan_for_new_entry(fire)
        pos = {"id": fire["key"], "sym": fire["sym"], "lane": fire["lane"], "unit": fire["unit"], "qty": qty,
               "entryAvg": fill[0], "entryFill": fill[1], "fireClose": fire["fireClose"], "fireBar": fire["fireBar"],
               "entryBarStart": start, "timeExitAt": time_exit_at(fire["lane"], start, plan["maxBars"]), "plan": plan}
        book["positions"].append(pos)
        book["cash"] = M.round2(book["cash"] - qty * fill[0])
        book["episodes"][episode_id(fire)] = fire["key"]
        book["capacityWait"].pop(fire["key"], None)
        book["seen"][fire["key"]] = {"action": "enter", "at": now}
        orders.append({"side": "buy", "sym": fire["sym"], "qty": qty, "px": fill[0], "pos": pos,
                       "deadline": deadline})
    return orders


class HourlyPlaybook(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_hourly_playbook", family="midna_tensor", cadence_s=300, capital=ACCOUNT_USD, universe=(),
            schedule="always",
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 130, "symbols_for": "dv20"}],
                   "quotes": {"source": "equity"}, "feeds": ["midna_watch"]},
            params={"slots": SLOTS, "slot_usd": SLOT_USD, "lane_caps": LANE_CAPS, "max_delay_min": MAX_DELAY_MIN,
                    "limit_band": LIMIT_BAND, "min_dv20": MIN_DV20, "playbook": "1.0.0", "removed_gates": REMOVED},
            source=SOURCE, state_schema={"seen": "dict", "episodes": "dict", "capacityWait": "dict", "pos": "dict",
                                         "dv20": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _fires(self, now):
        feed = self.engine.feeds.get("midna_watch", self, now) if self.engine is not None and \
            self.engine.feeds is not None else None
        return fires_of(feed)

    def _open_candidates(self, now, book=None):
        st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) if self.engine is not None else {}
        seen = (st or {}).get("seen") or {}
        return [f["sym"] for f in self._fires(now) if f["tradeable"] and not seen.get(f["key"])]

    def bar_symbols(self, need, now, book=None):
        return list(dict.fromkeys(self._open_candidates(now, book)))

    def quote_universe(self, now, book=None):
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        return list(dict.fromkeys(held + self._open_candidates(now, book)))

    def signal(self, view):
        st = dict(view.state or {})
        fires = fires_of(view.extra.get("midna_watch"))
        vb, cash = M.virtual_book(view)
        rec = dict(st.get("pos") or {})
        positions = []
        for sym, p in vb.items():
            r = rec.get(sym) or p["meta"] or {}
            if not r.get("timeExitAt"):
                continue                                 # not this book's position record (never happens)
            positions.append(dict(r, sym=sym, qty=p["qty"]))
        # dv20 once per ET day per name (desk.ts cachedDv20)
        day = M.et_ymd(view.now)
        dvc = st.get("dv20") if (st.get("dv20") or {}).get("day") == day else {"day": day, "values": {}}
        dvc = {"day": day, "values": dict(dvc.get("values") or {})}
        daily = (view.bars or {}).get("1d") or {}
        need = {f["sym"] for f in fires if f["tradeable"] and not (st.get("seen") or {}).get(f["key"])}
        for sym in need:
            if dvc["values"].get(sym) is None:
                v = dv20_of([b for b in daily.get(sym) or []])
                if v is not None:
                    dvc["values"][sym] = v
        dv20 = {s: dvc["values"].get(s) for s in need}
        quotes = {}
        for sym in need | {p["sym"] for p in positions}:
            q = M.mq(view.quotes.get(sym))
            if q:
                quotes[sym] = q
        book = {"cash": cash, "positions": positions, "seen": dict(st.get("seen") or {}),
                "episodes": dict(st.get("episodes") or {}), "capacityWait": dict(st.get("capacityWait") or {})}
        orders = step(book, view.now, quotes, fires, dv20)
        out = []
        for o in orders:
            if o["side"] == "buy":
                pm = {k: o["pos"][k] for k in ("id", "lane", "unit", "entryBarStart", "timeExitAt", "plan", "fireClose",
                                               "fireBar", "entryFill")}
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"], signal_key=o["pos"]["id"],
                                  reason=f"{o['pos']['lane']} {o['pos']['unit']} fire {o['pos']['fireBar']}: "
                                         f"{o['pos']['plan']['scheme']}",
                                  order=OrderSpec(window_s=max(300.0, o["deadline"] - view.now)),
                                  meta={"position_meta": pm}))
            else:
                out.append(Intent("exit", o["sym"], price_hint=o["px"], signal_key=o["id"] + ":exit",
                                  reason=o["reason"], order=OrderSpec(window_s=3600)))
        keep = {p["sym"]: {k: p.get(k) for k in ("id", "lane", "unit", "entryBarStart", "timeExitAt", "plan",
                                                 "fireClose", "fireBar", "entryFill", "entryAvg")}
                for p in book["positions"]}
        for p in book["positions"]:
            keep[p["sym"]]["entryAvg"] = p.get("entryAvg") or (vb.get(p["sym"]) or {}).get("avg")
        for sym in M.equity_positions(view):
            if sym not in keep and sym in rec:
                keep[sym] = rec[sym]
        seen = book["seen"]
        if len(seen) > 5000:
            for k in list(seen)[:len(seen) - 5000]:
                seen.pop(k)
        st.update(seen=seen, episodes=book["episodes"], capacityWait=book["capacityWait"], pos=keep, dv20=dvc)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def fires_of(feed):
    """the inbox fires of the watch cache (fires.ts readInbox + parseInboxFire)."""
    out = []
    for raw in (feed or {}).get("inbox") or []:
        f = parse_inbox_fire(raw)
        if f:
            out.append(f)
    return out
