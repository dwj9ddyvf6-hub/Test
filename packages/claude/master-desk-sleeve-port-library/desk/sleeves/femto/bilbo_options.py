"""Bilbo Box Options — lean-desk port (Wave B).

master-desk: the old desk's bilbo_options.py restored on the engine, on its own signal engine: bilbo_options_signals.py
(Milkman's Bilbo Box v2 with his live flags minutes=60, session='eth', break_rule='close', min_grey=1,
first_bar_only=True, stdev_ddof=1) is vendored byte-identical (desk/vendor/old_desk_research/bilbo_options_signals.py)
— its pandas EMA / Wilder / rolling-stdev arithmetic IS the grey flag and the daily ATR / EMA21, so it is reused, not
retyped. Long calls on a compression breakout, exits keyed to the stock.

  history .. the universe's SIP 5-minute bars, extended hours, split-adjusted, from 60 calendar days before the scan
             (fewer than 100: the name is not scanned); hourly = the on-the-hour 60-minute resample of 04:00-19:55 ET,
             daily = the 09:30-15:55 bars per date.
  grey ..... Saty Phase compression: the 21-period Bollinger band (EMA21 pivot, sample stdev) inside the 2 x ATR14
             Keltner band, except when the gap is not shrinking and price is inside the 1.854 x ATR expansion zone.
  box ...... high / low of the first 5 grey hours of a run (fewer if it ends sooner), frozen after the 5th; a run lives
             10 calendar days; the prior completed RTH day's ATR14 (dATR) rides with it.
  entry .... the hourly scan (the first pass at or after :22 of an hour 10-15 ET, weekdays): every episode whose FIRST
             hour out of compression CLOSED above the box high (one shot: a failed first hour ends the run), not yet
             decided, closed >= 20 minutes before the scan (the SIP lag), newer than the previous scan less 2 hours
             (the first scan: 24 hours); then, in the old order: that close at 10:00-15:00 ET Mon-Fri and spot strictly
             above the daily EMA21 at the prior completed RTH close (both final: a failed episode is spent); calls
             expiring 21-37 days after the entry date, the nearest expiry, the strike nearest spot + 0.75 x dATR (a tie:
             the lower); the contract two-sided with (ask - bid) / mid <= 5%; floor(4% of equity / (mid x 100))
             contracts, never under 1 (flagged oversize); at most 5 calls held or in flight; never a contract already
             held or in flight; buy to open at the mid, working 60 minutes; a partial fill keeps its contracts and
             withdraws the rest at the next pass. The decided episode is spent.
  exits .... (every pass, never gated) on the stock's completed 5-minute regular-session (09:30-15:55) closes since the
             entry hour's close, first trigger wins: <= 5 days to the contract's expiry (the backstop rail, on the last
             bar's date; a position without box levels keeps only this rail); the 10th trading day after the entry
             date; a close below the box low; once the high has run +1.25 x dATR, a close at or below entry + 25% of
             the peak gain. Sell to close at the mid, only on a two-sided quote; a working exit follows the fresh mid.

Gone under the cutover doctrine: the risk gate (kill switch, daily-loss halt), the drawdown brake (block / halve), the
context gate, the Decision #75 red-day gate and chart gate (pre_buy staging and its release replay, which re-checked
those gates and the Decision #8 earnings blackout), the 150% desk cap and its exposure ledger, and the shared-account
broker check (a contract any sleeve held at the broker blocked the entry and was adopted as a box-unknown position).
Named divergences: a pass every 5 minutes of the session, one anchored at :22 of each hour 10-15, runs the exit sweep
and (on that pass) the entry scan (the old ran two crons, the sweep every 5 minutes 09:30-16:05 ET and the scan hourly
at :22; its 16:00 / 16:05 sweeps could only queue an order for the next open — here the session's last bars are acted
on at the next session's first pass); the exit series is consolidated real-time 5-minute regular-session bars (Yahoo)
where the old read IEX's real-time 5-minute bars, one venue's prints; gate 3 reads the contract's quote once, from the
chain snapshot (the old averaged up to three indicative snapshots two seconds apart); a working exit is re-priced at
the fresh mid on every pass until it fills (the old cancel-replaced it on its next three sweeps, then left it for
manual review); a contract already held or in flight is never bought again (the old checked the broker's filled
positions only, so a second episode resolving to a contract whose entry was still working bought it again and
overwrote the first record); the book is current, so a position whose exit has filled frees its slot at once (the
old's scan counted it until its next exit sweep reconciled the fill); the engine owns submission and its retries (the
old marked the episode only once the broker accepted the order and re-ran a refused submit at its next scan); the
desk's bar cache keeps 5,000 bars a series (~26 extended sessions of 5-minute bars), so until it keeps the old's 60
calendar days the daily ATR14 / EMA21 seed later (decide() trims anything longer to the old window).

Inputs via context.extra:
  "universe"      the 20 names, in the old universe file's order (default UNIVERSE)
  "bars_5m"       {SYM: SIP 5-minute bars, extended hours, ascending, epoch t = bar start} — on the scan's pass
  "bars_rth"      {SYM: 5-minute regular-session bars of the held calls' underlyings} — the exit series
  "chains"        {SYM: call rows {"symbol","strike","expiration","type","bid","ask"}} (fetched on demand)
  "option_quotes" {OCC: {"bid","ask"}} — the held calls
  "orders"        the sleeve's live order children [{"inst","action","side","vqty","filled_v","signal_key"}]
  "session_close" epoch of the session's close (a working exit's deadline)
  "meta"          {"last_entry_scan": epoch, "seen_episodes": ["SYM|start_ts", ...]}
  "sleeve_state"  {OCC: {"position": {"qty","occ", + the entry's position_meta}}, SYM: {"pending_entry": ...}}
Bars (arg): unused (the sleeve's series are 5-minute bars in context.extra)."""
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from ...vendor.old_desk_research import bilbo_options_signals as bos
from .compat import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

UNIVERSE = ("NVDA", "NFLX", "AMD", "GOOGL", "AAPL", "AMZN", "MSFT", "AVGO", "TSLA", "PLTR", "INTC", "MU", "JPM",
            "UBER", "BAC", "DIS", "META", "SMCI", "HOOD", "COIN")    # desk/bilbo_options_universe.txt, file order
MAX_POSITIONS = 5
SIP_DELAY_MIN = 20                 # only hourly bars closed >= 20 min before the scan are evaluated
HISTORY_DAYS = 60                  # 5-minute history per scan, calendar days
HISTORY_LIMIT = 10000              # the old fetch's bar limit (its newest 10,000)
MIN_HISTORY_BARS = 100
STALE_OVERLAP_H = 2                # episodes newer than the previous scan less 2 hours
FIRST_SCAN_LOOKBACK_H = 24
ENTRY_PENDING_TIMEOUT_MIN = 60     # an unfilled entry is cancelled after 60 minutes
SCAN_MINUTE, SCAN_HOURS = 22, (10, 15)
SEEN_PRUNE_AT, SEEN_KEEP_DAYS = 5000, 120
EXIT_WINDOW_S = 23400              # a working exit's life when the session close is not known

CONFIG = SleeveConfig(
    sleeve_id="bilbo_options", cadence_s=300, universe=UNIVERSE,
    state_schema={"position": "dict|None"}, risk_pct=bos.PREMIUM_FRACTION)

# the old engine's pure helpers, as the old runner called them
target_strike = bos.target_strike
select_expiry = bos.select_expiry
spread_gate_ok = bos.spread_gate_ok
size_contracts = bos.size_contracts
occ_expiry_date = bos.occ_expiry_date


# ------------------------------------------------------------ frames
def frame(bars):
    """5-minute bar dicts (epoch t = bar start) -> the old fetch_5min frame: o/h/l/c floats on a tz-aware ET bar-START
    index, sorted. None when there are no bars."""
    if not bars:
        return None
    df = pd.DataFrame([{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in bars])
    df.index = pd.to_datetime([float(b["t"]) for b in bars], unit="s", utc=True).tz_convert(ET)
    return df[["o", "h", "l", "c"]].astype(float).sort_index()


def history(bars, now):
    """the old scan's fetch: the bars from 60 calendar days before the scan (its RFC3339 start, whole seconds), the
    newest 10,000."""
    start = math.floor(float(now) - HISTORY_DAYS * 86400)
    return [b for b in bars or [] if float(b["t"]) >= start][-HISTORY_LIMIT:]


def exit_frame(bars, now):
    """the old exit sweep's series: completed bars only (the forming bar dropped), then the 09:30-15:55 ET session."""
    df = frame([b for b in bars or [] if float(b["t"]) + 300 <= float(now)])
    if df is None or not len(df):
        return None
    df = df.between_time("09:30", "15:55")
    return df if len(df) else None


def phase_compression(bars):
    """the grey flags (0/1) of bar dicts — the vendored Saty Phase compression."""
    df = frame(bars)
    return [] if df is None else [int(g) for g in bos.phase_compression(df)]


def _iso(t):
    return datetime.fromtimestamp(float(t), tz=timezone.utc).astimezone(ET).isoformat()


def _epoch(iso):
    return pd.Timestamp(iso).timestamp()


def evaluate_exit(bars5, pos):
    """the old evaluate_exits on bar dicts: (trigger bar ISO, reason) for the first trigger, else None. pos carries
    occ, entry_ts (ISO; or entry_t epoch), entry_spot, box_lo, datr14_prior, entry_date (or box_metadata_unknown)."""
    df = frame(bars5)
    if df is None:
        return None
    p = dict(pos)
    if p.get("entry_ts") is None and p.get("entry_t") is not None:
        p["entry_ts"] = _iso(p["entry_t"])
    return bos.evaluate_exits(df, p)


def exit_record(pos, occ):
    """the old evaluate_exits record from the held position's entry meta; box levels are never fabricated: a position
    without them keeps only the expiry rail (the old's box_metadata_unknown)."""
    keys = ("entry_ts", "entry_spot", "box_lo", "datr14_prior", "signal_date")
    if any(pos.get(k) is None for k in keys):
        return {"occ": occ, "box_metadata_unknown": True}
    return {"occ": occ, "entry_ts": pos["entry_ts"], "entry_spot": float(pos["entry_spot"]),
            "box_lo": float(pos["box_lo"]), "datr14_prior": float(pos["datr14_prior"]),
            "entry_date": str(pos["signal_date"])[:10]}


def exit_due(bars, pos, occ, now):
    """(trigger bar ISO, reason) | None on the completed regular-session 5-minute bars."""
    df = exit_frame(bars, now)
    if df is None:
        return None
    return bos.evaluate_exits(df, exit_record(pos, occ))


def exit_mid(q):
    """the old exit's quote read: bid and ask both > 0 -> the mid, else None (no two-sided quote, no order)."""
    q = q or {}
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if bid <= 0 or ask <= 0:
        return None
    return (bid + ask) / 2.0


def quote_gate(bid, ask):
    """gate 3 on the contract's quote: two-sided (bid > 0, ask > 0, ask >= bid) and (ask - bid) / mid <= 5% ->
    (ok, mid). The old averaged up to three indicative snapshots; one snapshot is its exact special case."""
    try:
        b, a = float(bid), float(ask)
    except (TypeError, ValueError):
        return False, None
    if not (b > 0 and a > 0 and a >= b):
        return False, None
    return bool(bos.spread_gate_ok(b, a)), (b + a) / 2.0


def underlying(occ, pos=None):
    return (pos or {}).get("underlying") or str(occ)[:-15]


# ------------------------------------------------------------ the scan
def entry_due(now, meta):
    """the hourly entry scan: the first pass at or after :22 of an hour 10-15 ET on a weekday (the old cron, 10:22-15:22)."""
    t = datetime.fromtimestamp(float(now), tz=timezone.utc).astimezone(ET)
    if t.weekday() >= 5 or not (SCAN_HOURS[0] <= t.hour <= SCAN_HOURS[1]) or t.minute < SCAN_MINUTE:
        return False
    mark = t.replace(minute=SCAN_MINUTE, second=0, microsecond=0).timestamp()
    last = (meta or {}).get("last_entry_scan")
    return last is None or float(last) < mark


def episode_key(sym, ep):
    return "%s|%s" % (sym, ep["start_ts"])


def prune_seen(seen, now):
    """the old _prune_seen_episodes: past 5,000 keys, keep those whose episode started within 120 days (behaviour-
    neutral: nothing that old is detectable in the 60-day history)."""
    if len(seen) <= SEEN_PRUNE_AT:
        return list(seen)
    cutoff = float(now) - SEEN_KEEP_DAYS * 86400
    kept = []
    for k in seen:
        try:
            ts = pd.Timestamp(str(k).rsplit("|", 1)[1])
            if ts.tzinfo is None:
                ts = ts.tz_localize(timezone.utc)
            if ts.timestamp() >= cutoff:
                kept.append(k)
        except (ValueError, IndexError):
            kept.append(k)
    return kept


def contract_for(ep, rows):
    """the old contract selection: calls expiring 21-37 days after the entry date (its chain query), the nearest such
    expiry, the strike nearest spot + 0.75 x dATR, the first matching contract -> (row, expiry, strike) | None."""
    d = pd.Timestamp(ep["entry_ts"]).date()
    lo = (d + timedelta(days=bos.MIN_DTE)).isoformat()
    hi = (d + timedelta(days=bos.MAX_DTE)).isoformat()
    calls = [r for r in rows if (r.get("type") or "call") == "call" and r.get("expiration")
             and lo <= str(r["expiration"])[:10] <= hi]
    expiry = bos.select_expiry([str(r["expiration"])[:10] for r in calls], ep["entry_ts"])
    if not expiry:
        return None
    strikes = [r["strike"] for r in calls if str(r["expiration"])[:10] == expiry]
    try:
        strike = bos.target_strike(ep["spot"], ep["datr14_prior"], strikes)
        row = next(r for r in calls if str(r["expiration"])[:10] == expiry and float(r["strike"]) == float(strike))
    except (ValueError, StopIteration):
        return None
    return row, expiry, float(strike)


def scan(context, extra, meta, occupied, blocked=None, trace=None):
    """the old run_entry decision path on one pass -> (entry intents, meta update). occupied: the contracts held or in
    flight (the slot count); blocked: those never bought again (default: occupied)."""
    now = float(context.now)
    equity = float(context.equity or 0.0)
    cutoff = now - SIP_DELAY_MIN * 60
    last = meta.get("last_entry_scan")
    fresh_after = float(last) - STALE_OVERLAP_H * 3600 if last is not None else now - FIRST_SCAN_LOOKBACK_H * 3600
    seen = list(meta.get("seen_episodes") or [])
    seen_set = set(seen)
    sip = extra.get("bars_5m") or {}
    chains = extra.get("chains") or {}
    occupied = set(occupied)
    blocked = set(occupied if blocked is None else blocked)
    tr = trace if trace is not None else {}

    def note(what):
        tr[what] = tr.get(what, 0) + 1

    intents = []
    for sym in extra.get("universe") or CONFIG.universe:
        bars5 = history(sip.get(sym), now)
        if len(bars5) < MIN_HISTORY_BARS:
            note("no_history")
            continue
        df5 = frame(bars5)
        episodes = bos.detect_episodes(df5)
        daily = bos.daily_rth(df5)
        for ep in episodes:
            if not ep["broke"]:
                note("not_broke")
                continue
            key = episode_key(sym, ep)
            if key in seen_set:
                note("seen")
                continue
            et = _epoch(ep["entry_ts"])
            if et > cutoff:
                note("sip_delay")
                continue
            if et <= fresh_after:
                note("stale_episode")
                continue
            if not bos.time_gate_ok(ep["entry_ts"]):
                note("time_gate")
                seen.append(key)
                seen_set.add(key)
                continue
            if not bos.ema21_gate_ok(ep["spot"], daily, ep["entry_ts"]):
                note("ema21_gate")
                seen.append(key)
                seen_set.add(key)
                continue
            rows = chains.get(sym)
            if rows is None:
                note("chain_unavailable")
                continue
            got = contract_for(ep, rows)
            if got is None:
                note("no_contract")
                continue
            row, expiry, strike = got
            occ = row["symbol"]
            ok, mid = quote_gate(row.get("bid"), row.get("ask"))
            if not ok:
                note("spread_gate")
                continue
            qty = bos.size_contracts(equity, mid * 100)
            if len(occupied) >= MAX_POSITIONS:
                note("max_positions")
                continue
            if occ in blocked:
                note("held_or_in_flight")
                continue
            limit = round(mid, 2)
            premium = qty * mid * 100
            oversize = premium > bos.PREMIUM_FRACTION * equity
            note("entered")
            intents.append(Intent(
                "enter", occ, qty_hint=qty, asset="option", price_hint=limit,
                legs=({"symbol": occ, "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},),
                order={"type": "limit", "limit_price": limit, "window_s": ENTRY_PENDING_TIMEOUT_MIN * 60},
                signal_key=key,
                position_meta={"episode": key, "underlying": sym, "entry_ts": ep["entry_ts"],
                               "entry_spot": float(ep["spot"]), "box_hi": float(ep["box_hi"]),
                               "box_lo": float(ep["box_lo"]), "datr14_prior": float(ep["datr14_prior"]),
                               "n_grey": int(ep["n_grey"]), "signal_date": pd.Timestamp(ep["entry_ts"]).date().isoformat(),
                               "expiry": expiry, "strike": strike, "mid": round(mid, 4), "oversize": bool(oversize)},
                reason="bilbo_options long_call: %s strike %g expiry %s mid %.2f x%d%s; box %.2f-%.2f (%d grey from %s) "
                       "closed out above at %s, spot %.2f, dATR14 %.2f, target spot+0.75xdATR"
                       % (occ, strike, expiry, mid, qty, " oversize" if oversize else "", ep["box_lo"], ep["box_hi"],
                          ep["n_grey"], ep["start_ts"], ep["entry_ts"], ep["spot"], ep["datr14_prior"])))
            seen.append(key)
            seen_set.add(key)
            occupied.add(occ)
            blocked.add(occ)
    return intents, {"last_entry_scan": now, "seen_episodes": prune_seen(seen, now)}


# ------------------------------------------------------------ the pass
def exit_key(occ, session, limit):
    return "%s|exit|%s|%.2f" % (occ, session, limit)


def book(extra):
    """(held calls {OCC: position}, live entry children {OCC: [order]}, live exit children {OCC: [order]})."""
    held = {}
    for st in (extra.get("sleeve_state") or {}).values():
        pos = (st or {}).get("position")
        if pos and pos.get("occ") and float(pos.get("qty") or 0) > 0:
            held[pos["occ"]] = pos
    entering, exiting = {}, {}
    for o in extra.get("orders") or []:
        inst = str(o.get("inst") or "")
        if not inst.startswith("OPT:"):
            continue
        if o.get("action") == "enter":
            entering.setdefault(inst[4:], []).append(o)
        elif o.get("action") in ("exit", "target"):
            exiting.setdefault(inst[4:], []).append(o)
    return held, entering, exiting


def decide(bars, context):
    """(intents, meta update | None): the exit sweep on every pass, then (on the scan's pass) the entry scan."""
    extra = context.extra or {}
    meta = extra.get("meta") or {}
    oq = extra.get("option_quotes") or {}
    rth = extra.get("bars_rth") or {}
    now = float(context.now)
    session = context.session
    close = extra.get("session_close")
    held, entering, exiting = book(extra)
    intents = []
    for occ, orders in entering.items():           # a partial fill keeps its contracts, the rest is withdrawn
        for o in orders:
            if 0 < float(o.get("filled_v") or 0) < float(o.get("vqty") or 0) - 1e-9:
                intents.append(Intent("cancel", occ, asset="option", signal_key=o.get("signal_key") or None,
                                      reason="bilbo_options entry partial fill %g of %g: remainder withdrawn"
                                             % (float(o["filled_v"]), float(o["vqty"]))))
    for occ, pos in held.items():
        qty = int(float(pos.get("qty") or 0))
        if qty <= 0:
            continue
        mid = exit_mid(oq.get(occ))
        hit = exit_due(rth.get(underlying(occ, pos)), pos, occ, now)
        if occ in exiting:                          # a working exit follows the fresh mid
            if mid is None:
                continue
            limit = round(mid, 2)
            key = exit_key(occ, session, limit)
            if key in {o.get("signal_key") for o in exiting[occ]}:
                continue
            for o in exiting[occ]:
                intents.append(Intent("cancel", occ, asset="option", signal_key=o.get("signal_key") or None,
                                      reason="bilbo_options exit re-priced to the mid %.2f" % limit))
            why = hit[1] if hit else "reprice"
        else:
            if hit is None or mid is None:
                continue
            limit = round(mid, 2)
            key = exit_key(occ, session, limit)
            why = hit[1]
        order = {"type": "limit", "limit_price": limit}
        order.update({"not_after": float(close)} if close else {"window_s": EXIT_WINDOW_S})
        intents.append(Intent(
            "exit", occ, qty_hint=qty, price_hint=limit, order=order, signal_key=key,
            reason="bilbo_options exit: %s occ=%s mid=%.2f trigger=%s" % (why, occ, limit, hit[0] if hit else None)))
    upd = None
    if entry_due(now, meta):
        occupied = set(held) | set(entering)
        new, upd = scan(context, extra, meta, occupied)
        intents += new
    return intents, upd


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_bo_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:            # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_bo_pass"] = memo
    return memo[1]


class BilboOptions(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)[0])


def signal(bars, slice_state, context):
    return BilboOptions().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    _intents, upd = _pass(bars, context)
    if upd:
        meta.update(upd)
    return meta
