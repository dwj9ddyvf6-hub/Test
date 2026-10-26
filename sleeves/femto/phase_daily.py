"""Phase Daily — lean-desk port.

EXTRACTED from the old desk's phase_daily.py + phase_signals.py
(Milkman Daily Bilbo Boxes). phase_compression_daily and
detect_episodes are ported verbatim in behavior — pandas/numpy
re-expressed in pure Python (ewm adjust=False recursions, rolling
sample stdev ddof=1); plumbing is core-owned. See ports/phase_daily.md.

Strategy (phase_signals docstring):
  Box: high/low of the FIRST 5 compression (grey) days (fewer if the
  squeeze ends early). Knowable at the close of the 5th grey day, or at
  the close of the first non-grey day when compression ends early.
  K5: resting buy-stop at box high, working 20 trading days after the
  box locks, gated each day on prior close > daily EMA21. Box-low
  touch first -> no trade. Initial stop = box low.
  Trail: each day the stop ratchets up to yesterday's daily EMA50
  (never down). Exit when price falls through the trail.
Risk 0.25%/trade; per-position notional cap 25% of equity; max 10
positions (phase_daily.py constants, verbatim).

The NC intraday nowcast arm does NOT port as a signal here — named
misfit (ports/phase_daily.md): it needs 5-min provisional bars and
crosses episode state intraday; it belongs to a core intraday product.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty",
                   "trail": float} | None, "episode_key": str|None}}
  "earnings": {SYM: "YYYY-MM-DD"|None} — earnings flatten is a core
              Risk/Gate duty desk-wide; not re-implemented here.
  "universe": optional override (default: bars keys; the old sleeve
              read desk/phase_universe.txt)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

BOX_DAYS = 5
K5_WINDOW_BARS = 20
RISK_FRACTION = 0.0025
MAX_POSITIONS = 10
NOTIONAL_CAP = 0.25

CONFIG = SleeveConfig(
    sleeve_id="phase_daily", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "episode_key": "str|None"},
    risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def _ewm(values, alpha):
    out = []
    v = None
    for x in values:
        v = x if v is None else v + alpha * (x - v)
        out.append(v)
    return out


def ema(values, n):
    """pandas ewm(span=n, adjust=False)."""
    return _ewm(values, 2.0 / (n + 1.0))


def rma(values, n):
    """pandas ewm(alpha=1/n, adjust=False)."""
    return _ewm(values, 1.0 / n)


def atr_series(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(float(b["h"]) - float(b["l"]))
        else:
            pc = float(bars[i - 1]["c"])
            trs.append(max(float(b["h"]) - float(b["l"]),
                           abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    return rma(trs, n)


def _rolling_std(values, window=21):
    """pandas rolling(21, min_periods=1).std(ddof=1): NaN for <2 points."""
    out = []
    for i in range(len(values)):
        w = values[max(0, i - window + 1):i + 1]
        if len(w) < 2:
            out.append(float("nan"))
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
        out.append(math.sqrt(var))
    return out


def phase_compression_daily(bars):
    """Verbatim port of phase_signals.phase_compression_daily:
    grey (1) when the 21-period Bollinger band sits inside the 2xATR14
    Keltner band, except when the band gap is not shrinking and we are
    already inside the 1.854xATR expansion zone."""
    n = len(bars)
    if n == 0:
        return []
    price = [float(b["c"]) for b in bars]
    a14 = atr_series(bars, 14)
    pivot = ema(price, 21)
    sd = _rolling_std(price, 21)
    grey = [0] * n
    comp = []
    inexp = []
    for i in range(n):
        above = price[i] >= pivot[i]
        bb_up, bb_dn = pivot[i] + 2.0 * sd[i], pivot[i] - 2.0 * sd[i]
        kc_up, kc_dn = pivot[i] + 2.0 * a14[i], pivot[i] - 2.0 * a14[i]
        ex_up, ex_dn = pivot[i] + 1.854 * a14[i], pivot[i] - 1.854 * a14[i]
        comp.append((bb_up - kc_up) if above else (kc_dn - bb_dn))
        inexp.append((bb_up - ex_up) if above else (ex_dn - bb_dn))
    for i in range(1, n):
        widening = comp[i - 1] <= comp[i]
        if widening and inexp[i] > 0:
            grey[i] = 0
        elif comp[i] <= 0:
            grey[i] = 1
    return grey


def detect_episodes(bars):
    """Verbatim port of phase_signals.detect_episodes (dates from bars)."""
    grey = phase_compression_daily(bars)
    dates = _dates(bars)
    h = [float(b["h"]) for b in bars]
    lo = [float(b["l"]) for b in bars]
    n = len(bars)
    episodes = []
    i = 0
    while i < n:
        if grey[i] != 1:
            i += 1
            continue
        start = i
        ep_hi, ep_lo = h[i], lo[i]
        n_grey = 1
        box = None
        j = i + 1
        while j < n and grey[j] == 1:
            ep_hi = max(ep_hi, h[j])
            ep_lo = min(ep_lo, lo[j])
            n_grey += 1
            if n_grey == BOX_DAYS:
                box = (ep_hi, ep_lo, j)
            j += 1
        ended = j < n
        if box is None:
            box = (ep_hi, ep_lo, j if ended else None)
        episodes.append({
            "start_idx": start, "end_idx": j - 1, "ended": ended,
            "n_grey": n_grey, "ep_hi": float(ep_hi), "ep_lo": float(ep_lo),
            "box_hi": float(box[0]), "box_lo": float(box[1]),
            "box_locked_idx": box[2],
            "start_date": dates[start], "end_date": dates[j - 1]})
        i = j if j > start else start + 1
    return episodes


def k5_trigger(bars, ep):
    """(femto port, kept for its tests) K5 evaluation after the box locks: (bar_idx, stop_px) of the first bar
    within K5_WINDOW_BARS after lock whose high reaches box_hi, gated on the PRIOR close > EMA21, provided no
    earlier bar touched box_lo first. None = no live trigger on the last bar."""
    lock = ep["box_locked_idx"]
    if lock is None:
        return None
    closes = [float(b["c"]) for b in bars]
    e21 = ema(closes, 21)
    last = len(bars) - 1
    for i in range(lock + 1, min(last + 1, lock + 1 + K5_WINDOW_BARS)):
        if float(bars[i]["l"]) <= ep["box_lo"]:
            return None  # box-low touch first -> no trade
        if float(bars[i]["h"]) >= ep["box_hi"] and closes[i - 1] > e21[i - 1]:
            return (i, ep["box_lo"]) if i == last else None
    return None


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from datetime import date, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

ET = ZoneInfo("America/New_York")
SCR3_DAYS = 3
MIN_BARS = 80                 # old daily_pass: len(bars) < 80 -> skip the name
NC_CACHE_BARS = 130           # old intraday pass read the daily pass's bars cache (the last 130 daily bars)
NC_MIN_BARS = 60              # old maybe_nc_fire: len(bars) < 60 -> no nowcast
_EP_MEMO = {}


def size_qty(equity, entry_ref, stop_ref):
    """old size_qty verbatim: 0.25% risk on entry->stop, capped at 25% notional; 0 allowed (no 1-share floor)."""
    risk_dist = entry_ref - stop_ref
    if risk_dist <= 0:
        return 0
    qty = int((equity * RISK_FRACTION) // risk_dist)
    return min(qty, int((equity * NOTIONAL_CAP) // entry_ref))


def k5_state(bars, ep, traded=False):
    """old manage_k5_daily on completed bars, in its order: traded -> window -> box-low touch -> box-high breach
    -> gate. Returns (status, reason); status 'arm' = place today's resting DAY buy-stop at box_hi, 'watch' =
    alive but the EMA21 gate is closed, 'dead', or 'none' (no locked box). Every death is monotonic in the
    bars, so recomputing each pass equals the old persisted status."""
    lock = ep.get("box_locked_idx")
    if lock is None:
        return "none", "no_box"
    if traded:
        return "dead", "traded"
    last = len(bars) - 1
    if last - lock > K5_WINDOW_BARS - 1:
        return "dead", "window_expired"
    start = lock if ep.get("n_grey", BOX_DAYS) < BOX_DAYS else lock + 1   # old boxlow_touched / _bh_start
    if any(float(b["l"]) <= ep["box_lo"] for b in bars[start:]):
        return "dead", "boxlow_touch"
    if any(float(b["h"]) >= ep["box_hi"] for b in bars[start:]):
        return "dead", "boxhi_breach"
    closes = [float(b["c"]) for b in bars]
    if closes[-1] > ema(closes, 21)[-1]:
        return "arm", "gate_open"
    return "watch", "gate_closed"


def nowcast_grey(completed, provisional):
    """phase_signals.nowcast_grey: today's compression flag with the forming bar appended.
    Returns (grey_now, [grey(n-3), grey(n-2), grey(n-1), grey_now])."""
    g = phase_compression_daily(list(completed) + [dict(provisional)])
    return g[-1] == 1, [int(v) for v in g[-4:]]


def _episodes(sym, bars):
    key = (sym, len(bars), float(bars[-1]["t"]), float(bars[-1]["c"]))
    if key not in _EP_MEMO:
        if len(_EP_MEMO) > 512:
            _EP_MEMO.clear()
        _EP_MEMO[key] = detect_episodes(bars)
    return _EP_MEMO[key]


def _next_td(d, holidays=()):
    n = d + timedelta(days=1)
    while n.weekday() >= 5 or n.isoformat() in holidays:
        n += timedelta(days=1)
    return n


def _close_t(context):
    """today's session close: the desk calendar's (early closes) via extra['session_close'], else 16:00 ET."""
    sc = (context.extra or {}).get("session_close")
    if sc:
        return float(sc)
    return datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                      microsecond=0).timestamp()


def _close_minus(context, minutes):
    return _close_t(context) - minutes * 60


def _phase(context):
    """pre (before 09:30 ET: the old 08:46 daily pass), rth (the old 5-min intraday pass), close (the last five
    minutes: the old >= 15:55 flatten / re-entry passes, on the real close), post."""
    now = float(context.now)
    t = datetime.fromtimestamp(now, tz=ET)
    if (t.hour, t.minute) < (9, 30):
        return "pre"
    close = _close_t(context)
    if now >= close:
        return "post"
    return "close" if now >= close - 300 else "rth"


def _key_episode(key):
    """'SYM:session:path:EPISODE_START' -> (path, episode start) for this sleeve's entry keys."""
    parts = str(key or "").split(":")
    return (parts[2], parts[3]) if len(parts) >= 4 else (None, None)


def _traded(sym, st, closed):
    """episodes this sleeve traded on sym (old ep['traded'], set on the entry fill): the private stamp, the held
    position's episode, and every closed trade whose entry key names an episode."""
    out = set()
    if st.get("traded_episode"):
        out.add(st["traded_episode"])
    pos = st.get("position") or {}
    if pos.get("episode_start"):
        out.add(pos["episode_start"])
    for t in closed or ():
        if t.get("symbol") == sym:
            path, ep = _key_episode(t.get("signal_key"))
            if path in ("k5", "nc", "reentry") and ep:
                out.add(ep)
    return out


def stop_levels(bars, slice_state, context):
    """pre-market trail ratchet (old manage_position_daily): new stop = max(stop, yesterday's daily EMA50); the
    engine holds it as the position's stop. Published only when strictly higher and still below the prior
    close (at or above it the sleeve exits at the open instead: trail breach)."""
    if _phase(context) != "pre":
        return {}
    state = (context.extra or {}).get("sleeve_state") or {}
    out = {}
    for sym, st in state.items():
        pos = (st or {}).get("position")
        bl = bars.get(sym) or []
        if not pos or len(bl) < MIN_BARS or pos.get("exit_submitted"):
            continue
        closes = [float(b["c"]) for b in bl]
        stop = float(pos.get("stop_px") or 0.0)
        new = max(stop, ema(closes, 50)[-1])
        if new > stop + 1e-9 and new < closes[-1]:
            out[sym] = round(new, 2)
    return out


class PhaseDaily(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old phase_daily runtime as one pure pass per desk pass.
          pre    K5: a resting DAY buy-stop at box_hi per armed episode (sized box_hi -> box_lo, stop = box_lo).
                 Held: trail breach (yesterday's EMA50 >= the prior close) and scr3 (prior close back below the
                 entry reference within 3 sessions) exit at the open; the earnings flatten is scheduled for the
                 last five minutes when the report is today or the next trading day.
          rth    box-low touch while a K5 stop rests -> withdraw it (episode dead). NC: market buy when
                 yesterday was grey, today's forming bar nowcasts not-grey, its high crosses the running episode
                 high, the prior close > EMA21, on episodes K5 cannot trade (no locked box, or K5 dead).
          close  NC as above; earnings re-entry the session after the report if price > the trail.
        Desk-wide gates the old runner layered on (risk gate, context gate, Decision #75, 150% desk cap) are
        out of scope by the cutover doctrine; the sleeve's own earnings policy is kept."""
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        earnings = extra.get("earnings") or {}
        earnings_fresh = bool(extra.get("earnings_fresh"))
        holidays = set(extra.get("nyse_holidays") or ())
        closed = extra.get("closed_trades") or ()
        forming = extra.get("forming") or {}
        marks = extra.get("marks") or {}
        equity = float(context.equity or 0.0)
        phase = _phase(context)
        today = date.fromisoformat(context.session)
        ntd = _next_td(today, holidays).isoformat()
        intents = []
        open_n = sum(1 for s, st in state.items() if (st or {}).get("position") or (st or {}).get("pending_entry"))
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < MIN_BARS:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            closes = [float(b["c"]) for b in bl]
            prior = closes[-1]
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0 or pos.get("exit_submitted") or phase != "pre":
                    continue
                stop = float(pos.get("stop_px") or 0.0)
                new_stop = max(stop, ema(closes, 50)[-1])
                why = None
                if new_stop >= prior and stop < prior:
                    why = "trail_breach: stop %.2f >= prior close %.2f" % (new_stop, prior)
                elif SCR3_DAYS and pos.get("ref_hi") and pos.get("entry_date"):
                    ed0 = str(pos["entry_date"])[:10]
                    dates = _dates(bl)
                    held = (len(bl) - 1) - dates.index(ed0) if ed0 in dates \
                        else (today - date.fromisoformat(ed0)).days
                    if 1 <= held <= SCR3_DAYS and prior < float(pos["ref_hi"]):
                        why = "scr3: close %.2f back below %.2f (%d sessions held)" % (prior, float(pos["ref_hi"]), held)
                if why:
                    intents.append(Intent("exit", sym, qty_hint=qty, price_hint=round(prior, 2),
                                          signal_key="%s:%s:exit" % (sym, context.session), reason="phase " + why))
                    continue
                ed = earnings.get(sym)
                if ed and ed in (today.isoformat(), ntd) and st.get("flatten_for") != ed:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, reason="phase earnings flatten (report %s)" % ed,
                        order={"not_before": _close_minus(context, 5), "not_after": _close_minus(context, 0) + 86400 * 4},
                        signal_key="%s:%s:flatten" % (sym, context.session),
                        state={"flatten_for": ed, "reentry": {
                            "qty": qty, "stop": round(new_stop, 2), "earnings_date": ed,
                            "path": pos.get("path") or "k5", "ref_hi": pos.get("ref_hi"),
                            "episode_start": pos.get("episode_start")}}))
                continue
            # earnings re-entry due? (old earnings_reentry_pass: the >= 15:55 pass of the session after the report,
            # price above the trail recomputed on the bars cache, heat cap counting working entries)
            pr = st.get("reentry")
            re_go = None
            if pr and phase == "close":
                rd = _next_td(date.fromisoformat(pr["earnings_date"]), holidays)
                mark = marks.get(sym)
                trail_now = max(float(pr["stop"]), ema(closes[-NC_CACHE_BARS:], 50)[-1])
                if today == rd and open_n < MAX_POSITIONS and mark and mark > trail_now:
                    re_go = (mark, trail_now)
            pend = st.get("pending_entry") or {}
            killed = None
            if pend:
                path, ep_start = _key_episode(pend.get("key"))
                fb = forming.get(sym)
                withdrawn = False
                if path == "k5" and phase in ("rth", "close") and fb:  # old boxlow_kill_check (intraday)
                    ep = next((e for e in reversed(_episodes(sym, bl)) if e["start_date"] == ep_start), None)
                    if ep and float(fb["l"]) <= ep["box_lo"]:
                        intents.append(Intent("cancel", sym, signal_key=pend.get("key"),
                                              reason="phase K5 box-low %.2f touched intraday (low %.2f): stop withdrawn"
                                                     % (ep["box_lo"], float(fb["l"])),
                                              state={"k5_killed": ep_start}))
                        killed, withdrawn = ep_start, True
                if path == "k5" and re_go and not withdrawn:
                    # the old re-entry pass ignored a K5 stop resting on a newer episode (the symbol could be booked
                    # twice while its state held one position); the re-entry takes the symbol's one position
                    intents.append(Intent("cancel", sym, signal_key=pend.get("key"),
                                          reason="phase earnings re-entry supersedes the resting K5 stop"))
                    withdrawn = True
                if not withdrawn:
                    continue                              # an entry is working (old: position/pending/resting)
                open_n -= 1
            if re_go:
                mark, trail_now = re_go
                intents.append(Intent(
                    "enter", sym, qty_hint=int(pr["qty"]), price_hint=round(mark, 2), stop=round(trail_now, 2),
                    exit_rules=(ExitRule("stop", round(trail_now, 2)),),
                    order={"not_after": _close_minus(context, 0)},
                    signal_key="%s:%s:reentry:%s" % (sym, context.session, pr.get("episode_start") or ""),
                    position_meta={"path": pr.get("path") or "k5", "ref_hi": pr.get("ref_hi"),
                                   "episode_start": pr.get("episode_start"), "reentered": True},
                    state={"reentry": None},
                    reason="phase earnings re-entry: %.2f above the trail %.2f (report %s)"
                           % (mark, trail_now, pr["earnings_date"])))
                open_n += 1
                continue
            if equity <= 0 or not earnings_fresh:
                continue
            eps = _episodes(sym, bl)
            if not eps:
                continue
            ep = eps[-1]
            traded = ep["start_date"] in _traded(sym, st, closed)
            status, _why = k5_state(bl, ep, traded)
            if phase == "pre":
                if status != "arm" or open_n >= MAX_POSITIONS:
                    continue
                qty = size_qty(equity, ep["box_hi"], ep["box_lo"])
                if qty < 1:
                    continue
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(ep["box_hi"], 2), stop=round(ep["box_lo"], 2),
                    exit_rules=(ExitRule("stop", round(ep["box_lo"], 2)),),
                    order={"stop_price": round(ep["box_hi"], 2), "not_after": _close_minus(context, 0)},
                    signal_key="%s:%s:k5:%s" % (sym, context.session, ep["start_date"]),
                    position_meta={"path": "k5", "ref_hi": round(ep["box_hi"], 2), "episode_start": ep["start_date"]},
                    reason="phase K5 resting buy-stop %.2f (box %.2f/%.2f, episode %s, %s)"
                           % (ep["box_hi"], ep["box_hi"], ep["box_lo"], ep["start_date"], _why)))
                open_n += 1
                continue
            if phase not in ("rth", "close") or traded:
                continue
            # NC: the old maybe_nc_fire on the old bars cache (the last 130 completed daily bars)
            k5_alive = status in ("arm", "watch") and ep["start_date"] not in (st.get("k5_killed"), killed)
            if ep["box_locked_idx"] is not None and k5_alive:
                continue                                  # K5 keeps priority on a live box
            nb = bl[-NC_CACHE_BARS:]
            fb = forming.get(sym)
            if len(nb) < NC_MIN_BARS or not fb or phase_compression_daily(nb)[-1] != 1:
                continue
            prov = {"o": float(fb["o"]), "h": float(fb["h"]), "l": float(fb["l"]), "c": float(fb["c"])}
            grey_now, gctx = nowcast_grey(nb, prov)
            if grey_now:
                continue
            nd = _dates(nb)
            if ep["start_date"] not in nd:
                continue
            s_pos = nd.index(ep["start_date"])
            run_hi = max(float(b["h"]) for b in nb[s_pos:])
            run_lo = min(float(b["l"]) for b in nb[s_pos:])
            nclose = [float(b["c"]) for b in nb]
            if not prov["h"] > run_hi or not nclose[-1] > ema(nclose, 21)[-1]:
                continue
            ed = earnings.get(sym)
            if not ed or ed in (today.isoformat(), ntd):
                continue                                  # M1: no confirmed date -> no NC entry; report imminent
            if open_n >= MAX_POSITIONS:
                continue
            qty = size_qty(equity, prov["c"], run_lo)
            if qty < 1 or prov["c"] - run_lo <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(prov["c"], 2), stop=round(run_lo, 2),
                exit_rules=(ExitRule("stop", round(run_lo, 2)),),
                order={"not_after": _close_minus(context, 0)},
                signal_key="%s:%s:nc:%s" % (sym, context.session, ep["start_date"]),
                position_meta={"path": "nc", "ref_hi": round(run_hi, 2), "episode_start": ep["start_date"]},
                reason="phase NC nowcast breakout %.2f > episode high %.2f (flags %s, episode %s)"
                       % (prov["h"], run_hi, gctx, ep["start_date"])))
            open_n += 1
        return intents


def next_symbol_state(bars, slice_state, context, intents):
    """per-symbol bookkeeping after a pass: stamp the episode a held position came from as traded (old
    open_position_from_fill: ep['traded'] = True); drop a pending earnings re-entry once it can no longer fire
    (old earnings_reentry_pass: past the re-entry day, still holding on it, or below the trail at its pass)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    holidays = set(extra.get("nyse_holidays") or ())
    marks = extra.get("marks") or {}
    today = date.fromisoformat(context.session)
    entered = {i.symbol for i in intents if i.kind == "enter"}
    out = {}
    for sym, st in state.items():
        st = st or {}
        pos = st.get("position") or {}
        upd = {}
        if pos.get("episode_start") and st.get("traded_episode") != pos["episode_start"]:
            upd["traded_episode"] = pos["episode_start"]
        pr = st.get("reentry")
        if pr and sym not in entered and not any(i.symbol == sym and i.kind == "exit" for i in intents):
            try:
                rd = _next_td(date.fromisoformat(pr["earnings_date"]), holidays)
            except (KeyError, TypeError, ValueError):
                rd = None
            bl = bars.get(sym) or []
            drop = rd is None or today > rd or (today >= rd and pos)
            if not drop and today == rd and _phase(context) == "close" and not pos and bl and marks.get(sym):
                trail_now = max(float(pr["stop"]), ema([float(b["c"]) for b in bl[-NC_CACHE_BARS:]], 50)[-1])
                drop = marks[sym] <= trail_now               # below the trail at the re-entry pass: dropped
            if drop:
                upd["reentry"] = None
        if upd:
            out[sym] = upd
    return out


def signal(bars, slice_state, context):
    return PhaseDaily().signal(bars, slice_state, context)
