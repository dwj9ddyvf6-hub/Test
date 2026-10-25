"""saty_gpt_v03 — Sol's Saty Adaptive Opportunity Engine v0.3.0
as a desk sleeve (2026-10-23), ported per PORT-SPEC.md in the
saty-gpt-v03 workflow work dir. Source: Silicon main
f171e2e92093, research/saty_mahajan/, package VERSION 0.3.0.

THE PORT IN ONE PARAGRAPH. The strategy is Sol's code, ported
faithfully into core/saty_gpt_v03/ (reference, models,
structure/FeatureBook, strategies/StrategyEngine with all ten
families advancing independently, routing/OpportunityRouter,
awareness/AwarenessBook, data Calendar + daily references).
This file is a thin desk-contract wrapper in the saty_sol /
saty_magnum idiom: it contains NO strategy math of its own. His
brokers/store/service/SQLite layer does not exist here — the
desk dispatcher, the Ink filing door and virtual slices own
execution and accounting. His RiskConfig math survives as
sleeve-internal sizing/lot law against the virtual slice
(core/saty_gpt_v03/risk_lots.py). Expression is SPY SHARES,
long or short, per the pinned config main_10m_1h.json
(expression="equity"); options are OFF. The scheduled-event
calendar is ABSENT (the desk has no compatible caller-supplied
point-in-time calendar, and SPY has no earnings): awareness
event_state is stamped event_unknown_coverage every pass, which
under the pinned require_event_calendar_coverage=false does
not block; no event is ever invented. VIX is not consumed
(vix=None permanently). 1D/1W streams are not required by the
pinned config; daily bars serve only to build the day
Reference.

WARMUP. 1000 actual completed bars per required clock (10m
and 1H), no per-clock override. Until both clocks reach 1000
for SPY the sleeve stamps blocked_warmup with per-clock
counts and emits no entries. Exits are NEVER trapped behind
warmup (or any other entry block): position management runs
first in every pass.

DETERMINISM. Process-per-pass reconstruction (PORT-SPEC
section 7.3, first branch): FeatureBook / StrategyEngine /
AwarenessBook state is rebuilt each pass by replaying the
door-supplied completed-bar history in availability order.
Durable episode/lot/session state rides the journal in
ctx.extra["gpt_v03_journal"] (PORT-SPEC section 7.3 key),
served back from the ledger by tools/run_live.py's
_v03_session_data via the producer (the saty_sol
fetch_sol_session pattern) and written back on
self.last_evaluation for the dispatcher's filing door — the
sleeve writes no files.
A journal whose version/config fingerprint does not match
0.3.0 + the pinned config is rejected (fresh state), never
migrated. Position truth is the broker/slice position record;
the journal is episode/lot bookkeeping only.

FORWARD TESTING ONLY. No performance claim anywhere: Sol's own
scope label for the package is mechanical correctness, not
performance, and this port claims nothing more.
"""
import hashlib
import json
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core.saty_gpt_v03 import risk_lots
from core.saty_gpt_v03.awareness import AwarenessBook, AwarenessConfig
from core.saty_gpt_v03.data import Calendar, build_daily_references
from core.saty_gpt_v03.models import Observation, Quote
from core.saty_gpt_v03.reference import Bar, Session
from core.saty_gpt_v03.strategies import SETUPS, StrategyConfig, StrategyEngine
from core.saty_gpt_v03.structure import FeatureBook, StructureConfig

ET = ZoneInfo("America/New_York")
SYM = "SPY"
AWARENESS_UNIVERSE = ("SPY", "QQQ", "IWM")
PROVIDER = "sip"          # the desk SIP door's lineage label
REPLAY_BARS = 120         # bounded replay window (spec 7.3)
WARMUP_BARS = 1000        # pinned: structure + strategy warmup
MAX_QUOTE_AGE_S = 5.0     # pinned: desk + risk quote age
EARLY_CLOSES = _SHARED_EARLY_CLOSES

CONFIG = SleeveConfig(
    sleeve_id="saty_gpt_v03",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
)

# Pinned config fingerprints (PORT-SPEC section 6): a journal is
# adopted only when every fingerprint matches this build.
_STRUCTURE_CFG = StructureConfig(
    required_timeframes=("10m", "1H"),
    max_ages={"10m": timedelta(seconds=1200),
              "1H": timedelta(seconds=7200)},
    warmup_bars=WARMUP_BARS, warmup_by_timeframe={},
    ribbon_version="pro", pivot_left=2, pivot_right=2,
    zone_tolerance_atr=0.1, range_lookback=12, max_history=2048,
    max_pivots=256, max_streams=128, max_calendar_entries=4096,
    require_session=True, require_same_provider=True,
    carry_previous_session_timeframes=("1H",))
_STRATEGY_CFG = StrategyConfig(
    enabled=tuple(SETUPS), warmup_bars=WARMUP_BARS,
    minimum_trend_bars=3, transition_memory_bars=12,
    setup_expiry_bars=6, minimum_compression_bars=3,
    maximum_compression_bars=30, compression_stop="boundary",
    tolerance_atr=0.1, stop_buffer_atr=0.1, max_chase_atr=0.4,
    minimum_net_reward_risk=1.5, estimated_round_trip_cost=0.02,
    minimum_phase_divergence=5.0, minimum_price_divergence_atr=0.05,
    maximum_pivot_separation_bars=50, maximum_pivot_age_bars=50,
    phase_exit_threshold=61.8, countertrend_risk_multiplier=0.5,
    context_timeframe="1H", require_context_alignment=False,
    max_context_age_seconds=86400.0, max_data_lag_seconds=300.0)
_AWARENESS_CFG = AwarenessConfig(
    execution_timeframe="10m", max_quote_age_seconds=MAX_QUOTE_AGE_S)
_FINGERPRINT = hashlib.sha256(json.dumps({
    "version": "0.3.0",
    "structure": str(sorted(vars(_STRUCTURE_CFG).items())),
    "strategy": _STRATEGY_CFG.fingerprint,
    "risk": str(sorted(vars(risk_lots.RISK).items())),
    "awareness": _AWARENESS_CFG.fingerprint,
}, sort_keys=True, default=str).encode()).hexdigest()[:28]


def session_close_dt(session_iso):
    d = date.fromisoformat(session_iso)
    t = EARLY_CLOSES.get(session_iso, dtime(16, 0))
    return datetime.combine(d, t, tzinfo=ET)


def _session_obj(d):
    iso = d.isoformat()
    close = session_close_dt(iso)
    return Session(session_id=iso,
                   open=datetime.combine(d, dtime(9, 30), tzinfo=ET),
                   entry_start=datetime.combine(d, dtime(9, 30),
                                                  tzinfo=ET),
                   entry_cutoff=close - timedelta(minutes=30),
                   flat_at=close, close=close)


def _shape(raw):
    """Desk bars ({t epoch, o/h/l/c/v}) -> sorted tuples
    (start_epoch, o, h, l, c, v). Unparseable rows dropped."""
    out = []
    for b in raw or []:
        try:
            out.append((float(b["t"]), float(b["o"]), float(b["h"]),
                        float(b["l"]), float(b["c"]),
                        float(b.get("v") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda x: x[0])
    return out


def _finer_step(rows):
    for a, b in zip(rows, rows[1:]):
        if b[0] > a[0]:
            return b[0] - a[0]
    return None


def _complete_buckets(rows, minutes):
    """Aggregate desk rows (any finer step) into complete
    `minutes` buckets across all sessions present."""
    step_s = minutes * 60
    finer = _finer_step(rows)
    if finer is None or step_s % int(finer) != 0:
        return []
    need = int(step_s // finer)
    by_day = {}
    for r in rows:
        d = datetime.fromtimestamp(r[0], tz=ET).date()
        by_day.setdefault(d, []).append(r)
    out = []
    for d in sorted(by_day):
        open_epoch = datetime.combine(
            d, dtime(9, 30), tzinfo=ET).timestamp()
        buckets = {}
        for r in by_day[d]:
            idx = int((r[0] - open_epoch) // step_s)
            if idx >= 0:
                buckets.setdefault(idx, []).append(r)
        for idx in sorted(buckets):
            rs = buckets[idx]
            if len(rs) < need:
                continue  # incomplete bucket: dropped (spec law)
            out.append((open_epoch + idx * step_s, rs[0][1],
                        max(x[2] for x in rs), min(x[3] for x in rs),
                        rs[-1][4], sum(x[5] for x in rs)))
    out.sort(key=lambda x: x[0])
    return out


def _obs(symbol, timeframe, start_epoch, o, h, l, c, v, minutes):
    start = datetime.fromtimestamp(start_epoch, tz=ET)
    end = start + timedelta(minutes=minutes)
    bar = Bar(start, end, o, h, l, c, v)
    return Observation(symbol, timeframe, bar, end, PROVIDER, "US",
                       "regular", "raw", "0")


def _fresh_journal():
    return {"fingerprint": _FINGERPRINT, "version": "0.3.0",
            "session": None, "e0": None, "entries_taken": 0,
            "entry_pending": None, "episodes": [], "lots": [],
            "sizing_rejections": [], "decisions_tail": []}


def _journal(extra, slice_state):
    """The durable journal from the filing door, adopted only
    when its fingerprint matches this build (fresh state
    otherwise — v0.2 or mismatched state is never migrated)."""
    raw = None
    if isinstance(extra.get("gpt_v03_journal"), dict):
        raw = extra["gpt_v03_journal"]
    elif isinstance(slice_state, dict) \
            and isinstance(slice_state.get("gpt_v03_journal"), dict):
        raw = slice_state["gpt_v03_journal"]
    if raw and raw.get("fingerprint") == _FINGERPRINT \
            and raw.get("version") == "0.3.0":
        j = _fresh_journal()
        j.update({k: raw[k] for k in j if k in raw})
        return j, False
    return _fresh_journal(), bool(raw)


class SatyGptV03(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # inputs
    # ------------------------------------------------------------
    def _position(self, extra, slice_state):
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if not isinstance(pos, dict) and isinstance(slice_state, dict):
            pos = slice_state.get("position")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            return pos
        return None

    def _quote(self, extra, now_epoch):
        """(bid, ask) from the fresh-quote door when two-sided
        and <= 5s old (pinned quote age); else None."""
        q = (extra.get("latest_quote") or {}).get(SYM)
        if not isinstance(q, dict) or not q.get("t"):
            return None
        try:
            t_epoch = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00")).timestamp()
            bp, ap = float(q["bp"]), float(q["ap"])
        except (KeyError, TypeError, ValueError):
            return None
        if now_epoch - t_epoch > MAX_QUOTE_AGE_S or bp <= 0 or ap < bp:
            return None
        return bp, ap

    def _fills(self, extra):
        fills = extra.get("session_fills")
        if fills is None:
            return None
        out = []
        for f in fills:
            try:
                out.append({
                    "position_intent": f.get("position_intent"),
                    "qty": abs(float(f.get("qty") or 0)),
                    "price": float(f.get("price") or 0)})
            except (TypeError, ValueError):
                continue
        return out

    def _realized(self, fills):
        """FIFO reconstruction from session fills (fill truth):
        (realized_pnl_dollars, open_lots, entries_taken). Each
        open fill is a lot; closes realize against the oldest
        open lot first."""
        realized, lots, entries = 0.0, [], 0
        for f in fills or []:
            pi, q, px = f["position_intent"], f["qty"], f["price"]
            if pi in ("buy_to_open", "sell_to_open"):
                entries += 1
                lots.append({"direction": 1 if pi == "buy_to_open"
                             else -1, "qty": q, "price": px})
            elif pi in ("buy_to_close", "sell_to_close"):
                left = q
                while left > 0 and lots:
                    lot = lots[0]
                    take = min(left, lot["qty"])
                    # a sell closes a long lot: (px-entry)*take;
                    # a buy closes a short lot: (entry-px)*take.
                    if pi == "sell_to_close":
                        realized += (px - lot["price"]) * take
                    else:
                        realized += (lot["price"] - px) * take
                    lot["qty"] -= take
                    left -= take
                    if lot["qty"] <= 0:
                        lots.pop(0)
        return realized, lots, entries

    # ------------------------------------------------------------
    # exit management — runs FIRST, never trapped (spec 7.6)
    # ------------------------------------------------------------
    def _exit_intent(self, qty_signed, rule, quote, ctx):
        d = 1 if qty_signed > 0 else -1
        q = abs(int(qty_signed))
        kw = {}
        if quote is not None:
            limit = quote[0] if d > 0 else quote[1]
            kw["limit_price"] = round(limit, 2)
            kw["price_hint"] = round(limit, 2)
        side = "sell" if d > 0 else "buy"
        pi = "sell_to_close" if d > 0 else "buy_to_close"
        return Intent("exit", SYM, qty=q, side=side,
                      position_intent=pi,
                      reason=f"saty_gpt_v03 exit: {rule}",
                      signal_date=ctx.session, **kw)

    def _manage(self, pos, journal, extra, ctx, now_dt, stamp,
                bars10):
        """Structural stop, target scales, breakeven migration
        and the 1-ATR runner trail for the journal's open lot,
        evaluated on completed bars + the fresh quote. Returns
        a list of exit intents (possibly empty)."""
        qty_signed = float(pos.get("qty") or 0)
        d = 1 if qty_signed > 0 else -1
        remaining = abs(qty_signed)
        quote = self._quote(extra, ctx.now)
        lot = next((x for x in journal["lots"]
                    if x.get("state") == "open"), None)
        stamp["position"] = {"qty": qty_signed, "direction": d,
                             "entry_px": pos.get("entry_px"),
                             "lot": bool(lot)}
        if lot is None:
            stamp["ownership_mismatch"] = True
            stamp["decision"] = "exit_unmanaged_no_lot_record"
            return []
        entry_px = float(lot["entry_px"])
        stop = float(lot["stop"])
        atr = float(lot.get("atr") or 0)
        targets = [float(t) for t in lot.get("targets") or []]
        initial = float(lot.get("initial_qty") or remaining)
        scaled = float(lot.get("scaled_qty") or 0)
        if initial > remaining:
            scaled = max(scaled, initial - remaining)
            lot["scaled_qty"] = scaled
        fill_t = float(pos.get("fill_t") or pos.get("entry_t")
                       or lot.get("fill_t") or 0)
        since = [b for b in bars10
                 if fill_t and b[0] + 600 > fill_t] if fill_t else bars10
        # favorable extreme since entry (runner trail input)
        if since:
            fav = max(b[2] for b in since) if d > 0 \
                else min(b[3] for b in since)
            lot["favorable"] = fav if lot.get("favorable") is None \
                else (max(lot["favorable"], fav) if d > 0
                      else min(lot["favorable"], fav))
        # breakeven migration after a profitable partial, then
        # the runner trail — stops never loosen (risk_lots law)
        if scaled > 0:
            be = risk_lots.breakeven_stop(entry_px, d)
            stop = max(stop, be) if d > 0 else min(stop, be)
            if atr > 0 and lot.get("favorable") is not None:
                stop = risk_lots.trailed_stop(
                    stop, d, lot["favorable"], atr)
            if stop != float(lot["stop"]):
                lot["stop"] = stop
                lot.setdefault("stop_history", []).append(
                    {"stop": stop, "at": ctx.session})
        # structural stop: a completed 10m close beyond the stop
        if bars10:
            last_close = bars10[-1][4]
            if (d > 0 and last_close < stop) or \
                    (d < 0 and last_close > stop):
                stamp["decision"] = "stop_exit"
                if quote is None:
                    return [self._exit_intent(
                        qty_signed, "stop_exit_blocked_no_quote",
                        None, ctx)]
                return [self._exit_intent(qty_signed, "stop_exit",
                                          quote, ctx)]
        # target scales in path order (stage 1 = 50%, later 25%)
        for stage, tgt in enumerate(targets, start=1):
            due_total = sum(
                risk_lots.scale_quantity(int(initial), s)
                for s in range(1, stage + 1))
            if scaled >= due_total:
                continue
            touched = any(
                (b[2] >= tgt if d > 0 else b[3] <= tgt)
                for b in since)
            if not touched:
                break
            due = min(due_total - scaled, remaining)
            if due < 1:
                break
            stamp["decision"] = f"target_scale_{stage}"
            if quote is None:
                stamp["exit_pending_no_quote"] = \
                    f"target_scale_{stage}"
                return []
            return [self._exit_intent(
                d * int(due), f"target_scale_{stage}", quote, ctx)]
        return []

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "saty_gpt_v03", "session": ctx.session,
                 "state": "armed", "warmup": {"10m": 0, "1H": 0},
                 "carried_timeframes": {}, "frames": {},
                 "reference": None, "families": {},
                 "router": None, "awareness": None,
                 "session_pnl_r": None, "entries_taken": 0,
                 "open_lots": 0, "decision": None,
                 "stood_down": None,
                 "event_state": "event_unknown_coverage",
                 "event_unknown_coverage": True}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        extra = ctx.extra or {}
        journal, rejected = _journal(extra, slice_state)
        stamp["gpt_v03_journal"] = journal
        if rejected:
            stamp["journal_rejected"] = "fingerprint_mismatch"
        if journal["session"] != ctx.session:
            # new session: session fields reset only when flat
            # (spec section 4 reset law); lots/episodes persist
            # until their fills close them.
            has_lots = any(x.get("state") == "open"
                           for x in journal["lots"])
            if not has_lots:
                journal["session"] = ctx.session
                journal["e0"] = float(ctx.equity or 0.0) or None
                journal["entries_taken"] = 0
                journal["entry_pending"] = None
        if journal["e0"] is None:
            journal["e0"] = float(ctx.equity or 0.0) or None

        # fill-truth lot sync (before exit management): a broker
        # position with a matching journal episode and an open
        # fill lot becomes a managed journal lot; a vanished
        # position closes its journal lots.
        _fills0 = self._fills(extra)
        if _fills0 is not None:
            _real0, _lots0, _ent0 = self._realized(_fills0)
            _pos0 = self._position(extra, slice_state)
            if _pos0 is not None and _lots0 and not any(
                    x.get("state") == "open" for x in journal["lots"]):
                _ep = next((e for e in reversed(journal["episodes"])
                            if e.get("state") in ("intent", "filled")),
                           None)
                if _ep is not None:
                    _fl = _lots0[-1]
                    journal["lots"].append({
                        "state": "open", "direction": _ep["direction"],
                        "entry_px": _fl["price"],
                        "initial_qty": _fl["qty"],
                        "stop": _ep["stop"],
                        "targets": list(_ep["targets"]),
                        "atr": _ep.get("atr"),
                        "scaled_qty": 0.0, "favorable": None,
                        "signal_id": _ep.get("signal_id")})
                    _ep["state"] = "filled"
                    journal["entry_pending"] = None
            if _pos0 is None:
                for _lot in journal["lots"]:
                    if _lot.get("state") == "open":
                        _lot["state"] = "closed"

        # raw frames from the producer bundle
        raw10 = _shape((extra.get("bars_10m") or {}).get(SYM)) \
            if isinstance(extra.get("bars_10m"), dict) else []
        raw5 = _shape((extra.get("bars_5m_long") or {}).get(SYM)) \
            if isinstance(extra.get("bars_5m_long"), dict) else []
        if raw10:
            bars10 = [(r[0], r[1], r[2], r[3], r[4], r[5])
                      for r in raw10]
        elif raw5:
            bars10 = _complete_buckets(raw5, 10)
        else:
            bars10 = []
        bars10 = [b for b in bars10 if b[0] + 600 <= ctx.now]
        raw1h = _shape((extra.get("bars_1h") or {}).get(SYM)) \
            if isinstance(extra.get("bars_1h"), dict) else []
        if raw1h:
            bars1h = [(r[0], r[1], r[2], r[3], r[4], r[5])
                      for r in raw1h]
        elif bars10:
            bars1h = _complete_buckets(
                [(b[0], b[1], b[2], b[3], b[4], b[5]) for b in bars10],
                60)
        else:
            bars1h = []
        bars1h = [b for b in bars1h if b[0] + 3600 <= ctx.now]
        stamp["warmup"] = {"10m": len(bars10), "1H": len(bars1h)}
        stamp["frames"] = {
            "10m": {"count": len(bars10)},
            "1H": {"count": len(bars1h)}}

        # 1. exits first — always, in every state (spec 7.6)
        pos = self._position(extra, slice_state)
        if pos is not None:
            exits = self._manage(pos, journal, extra, ctx, now_dt,
                                 stamp, bars10)
            if exits:
                return exits
            stamp["open_lots"] = sum(
                1 for x in journal["lots"]
                if x.get("state") == "open")

        # 2. calendar
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        # 3. data doors
        if not bars10:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no 10m bars (C-1)"
            return []
        daily_raw = []
        if isinstance(bars, dict):
            daily_raw = _shape(bars.get(SYM))
        if not daily_raw and isinstance(extra.get("bars_daily"), dict):
            daily_raw = _shape(extra["bars_daily"].get(SYM))
        if not daily_raw:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no daily bars (C-3)"
            return []

        # sessions from every date present + today
        days = sorted({datetime.fromtimestamp(b[0], tz=ET).date()
                       for b in bars10}
                      | {datetime.fromtimestamp(b[0], tz=ET).date()
                         for b in daily_raw} | {session_d})
        sessions = [_session_obj(d) for d in days
                    if is_trading_day(d)]
        if not any(s.session_id == ctx.session for s in sessions):
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: session unregistered (C-4)"
            return []
        calendar = Calendar(sessions)
        current_session = next(
            s for s in sessions if s.session_id == ctx.session)

        # daily reference for this session (C-3)
        daily_obs = []
        sess_by_date = {s.session_id: s for s in sessions}
        for r in daily_raw:
            d_iso = datetime.fromtimestamp(r[0], tz=ET).date().isoformat()
            s = sess_by_date.get(d_iso)
            if s is None:
                continue
            daily_obs.append(Observation(
                SYM, "1D",
                Bar(s.open, s.close, r[1], r[2], r[3], r[4], r[5]),
                s.close + timedelta(minutes=1), PROVIDER, "US",
                "regular", "raw", "0"))
        try:
            refs_list = [ref for (sym, ref) in
                         build_daily_references(daily_obs, calendar)
                         if sym == SYM]
        except Exception:
            refs_list = []
        reference = None
        for ref in refs_list:
            if ref.valid_from <= now_dt < ref.valid_until:
                reference = ref
        if reference is None:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no valid day reference (C-3)"
            return []
        stamp["reference"] = {
            "anchor": reference.close, "atr": reference.atr,
            "period_id": reference.period_id}

        # rebuild the books deterministically (spec 7.3)
        book = FeatureBook(_STRUCTURE_CFG)
        for s in sessions:
            book.register_session(s)
        for ref in refs_list:
            book.register_reference_period(
                SYM, "day", ref.valid_from, ref.valid_until,
                ref.period_end, known_at=ref.available_at)
        aware = AwarenessBook(_AWARENESS_CFG)
        for s in sessions:
            aware.register_session(s)
        obs_all = []
        for b in bars10:
            obs_all.append(_obs(SYM, "10m", *b, 10))
        for b in bars1h:
            obs_all.append(_obs(SYM, "1H", *b, 60))
        # awareness cross-section (C-6): synchronized 10m batches
        for sym in AWARENESS_UNIVERSE[1:]:
            raw_x = _shape((extra.get("bars_10m") or {}).get(sym)) \
                if isinstance(extra.get("bars_10m"), dict) else []
            if not raw_x and isinstance(extra.get("bars_5m_long"), dict):
                raw_x5 = _shape(extra["bars_5m_long"].get(sym))
                raw_x = _complete_buckets(raw_x5, 10) if raw_x5 else []
            for b in raw_x:
                if b[0] + 600 <= ctx.now:
                    obs_all.append(_obs(sym, "10m", *b, 10))
        obs_all.sort(key=lambda o: o.available_at)
        counts = {"10m": 0, "1H": 0}
        for o in obs_all:
            if o.symbol == SYM:
                try:
                    frame = book.update(o)
                    counts[o.timeframe] = frame.count
                except ValueError:
                    stamp["state"] = "blocked_data"
                    stamp["decision"] = \
                        "blocked_data: observation rejected (C-1/C-10)"
                    return []
            aware.update(o)
        stamp["warmup"] = {"10m": counts["10m"], "1H": counts["1H"]}
        quote = self._quote(extra, ctx.now)
        if quote is not None:
            # the quote carries its OWN door timestamps (never
            # wall-clock now): an awareness snapshot stamped at
            # the final bar's decision time can only honestly
            # contain a quote that existed by then.
            q_at = now_dt
            q_raw = (extra.get("latest_quote") or {}).get(SYM)
            if isinstance(q_raw, dict) and q_raw.get("t"):
                try:
                    q_at = datetime.fromisoformat(
                        str(q_raw["t"]).replace(
                            "Z", "+00:00")).astimezone(ET)
                except ValueError:
                    q_at = now_dt
            aware.update_quote(Quote(
                SYM, quote[0], quote[1], 0, 0, q_at, q_at))
        # R3 chronology cure (VERIFY-CURE-20261023): the snapshot
        # fed to engine.update for the final replay context must
        # be stamped at that context's decision time — the final
        # completed bar's end (== final ctx.as_of) — not at
        # wall-clock now. routing.py requires latest_bar_end <=
        # latest_available_at <= snapshot.as_of <= ctx.as_of; a
        # now-stamped snapshot is > ctx.as_of, so the router
        # labeled it future_snapshot_ignored and the bounded
        # awareness tie-break never applied.
        decision_as_of = datetime.fromtimestamp(
            bars10[-1][0] + 600, tz=ET) if bars10 else now_dt
        snapshot = None
        try:
            snapshot = aware.snapshot(SYM, decision_as_of,
                                      benchmark=SYM)
            stamp["awareness"] = snapshot.to_dict()
        except Exception:
            stamp["awareness"] = None

        try:
            context = book.context(SYM, "10m", now_dt, reference,
                                   session=current_session)
        except ValueError:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no execution frame (C-1)"
            return []
        stamp["carried_timeframes"] = \
            (context.metadata or {}).get("carried_timeframes") or {}
        blockers = list(context.blockers or ())
        warm = counts["10m"] >= WARMUP_BARS and \
            counts["1H"] >= WARMUP_BARS
        if not warm or any(b.startswith("WARMUP") for b in blockers):
            stamp["state"] = "blocked_warmup"
            stamp["decision"] = \
                f"blocked_warmup: 10m={counts['10m']} 1H={counts['1H']}"
            return []
        if blockers:
            stamp["state"] = "blocked_context" \
                if any("REFERENCE" in b for b in blockers) \
                else "blocked_data"
            stamp["decision"] = "blocked: " + ",".join(blockers)
            return []

        # strategy evaluation (all ten families, independently):
        # deterministic replay — the engine sees the contexts of
        # the most recent REPLAY_BARS execution bars in order
        # (bounded so a pass stays cheap on 2 cores); only the
        # final context's ranked signals are actionable.
        engine = StrategyEngine(_STRATEGY_CFG)
        signals = []
        sess_by_id = {s.session_id: s for s in sessions}
        replay_ends = [datetime.fromtimestamp(b[0] + 600, tz=ET)
                       for b in bars10[-REPLAY_BARS:]]
        for t_end in replay_ends:
            ref_t = next((r for r in refs_list
                          if r.valid_from <= t_end < r.valid_until),
                         None)
            sess_t = sess_by_id.get(t_end.date().isoformat())
            if ref_t is None or sess_t is None:
                continue
            try:
                ctx_t = book.context(SYM, "10m", t_end, ref_t,
                                     session=sess_t)
            except ValueError:
                continue
            got = engine.update(
                ctx_t, awareness=snapshot
                if t_end == replay_ends[-1] else None)
            if t_end == replay_ends[-1]:
                signals = got
        decisions = engine.drain_decisions()
        if decisions:
            journal["decisions_tail"] = (
                journal.get("decisions_tail") or [])[-64:] + decisions
            if any(d.get("event") == "AUDIT_GAP" for d in decisions):
                stamp["audit_gap"] = True
        lanes = (engine.last_cycle or {}).get("lanes") or {}
        stamp["families"] = {
            name: (lanes.get(name) or {}).get("state", "WAIT")
            for name in SETUPS}
        stamp["router"] = {
            "ranked": [s.signal_id for s in signals],
            "candidate_count": (engine.last_cycle or {}).get(
                "candidate_count")}

        # session accounting from fill truth
        fills = self._fills(extra)
        realized, open_lots, fill_entries = (0.0, [], 0) \
            if fills is None else self._realized(fills)
        r_unit = risk_lots.session_r(journal["e0"] or ctx.equity or 0.0)
        session_pnl_r = (realized / r_unit) if r_unit > 0 else None
        stamp["session_pnl_r"] = session_pnl_r
        entries_taken = max(journal["entries_taken"], fill_entries)
        stamp["entries_taken"] = entries_taken
        stamp["open_lots"] = len(open_lots)

        if pos is not None:
            stamp["state"] = "family_busy"
            stamp["stood_down"] = "family_busy"
            return []
        if journal.get("entry_pending"):
            stamp["stood_down"] = "entry_pending"
            return []
        if not signals:
            stamp["decision"] = "no_signal"
            return []
        sig = signals[0]
        stamp["families"][sig.setup] = "SIGNAL"
        d = 1 if sig.direction > 0 else -1
        # shortable declaration (spec section 5): the desk record
        # for SPY shares declares shortable via ctx market door;
        # absent a declaration, short signals stand down, never
        # coerced long.
        if d < 0 and not (ctx.market or {}).get("spy_shortable", True):
            stamp["stood_down"] = "not_shortable"
            return []
        if quote is None:
            stamp["stood_down"] = "entry_window_closed: no fresh quote"
            return []
        exec_px = quote[1] if d > 0 else quote[0]
        ok_adm, why = risk_lots.admission_recheck(
            d, sig.reference_entry, sig.stop, sig.targets, exec_px,
            sig.atr)
        if not ok_adm:
            stamp["stood_down"] = why
            return []
        open_risk_r = 0.0
        qty, why_qty = risk_lots.compute_qty(
            float(ctx.equity or 0.0), journal["e0"] or ctx.equity or 0.0,
            exec_px, sig.stop,
            risk_multiplier=sig.risk_multiplier,
            open_risk_r=open_risk_r, open_notional=0.0,
            entries_taken=entries_taken,
            session_pnl_r=session_pnl_r or 0.0)
        if qty < 1:
            journal["sizing_rejections"].append({
                "session": ctx.session, "setup": sig.setup,
                "reason": why_qty, "entry": exec_px,
                "stop": sig.stop})
            stamp["stood_down"] = why_qty
            stamp["decision"] = "sizing_zero_recorded"
            return []
        journal["entry_pending"] = {
            "signal_id": sig.signal_id, "setup": sig.setup,
            "direction": d, "session": ctx.session}
        journal["entries_taken"] = entries_taken + 1
        journal["episodes"].append({
            "signal_id": sig.signal_id, "setup": sig.setup,
            "direction": d, "entry_ref": sig.reference_entry,
            "stop": sig.stop, "targets": list(sig.targets),
            "atr": sig.atr, "state": "intent",
            "session": ctx.session})
        stamp["decision"] = f"enter {sig.setup}"
        return [Intent(
            "enter", SYM, qty=int(qty),
            # section 7.2 intent shape (VERIFY-CURE-20261023):
            # limit_price is the admission-checked executable-side
            # price (ask for buys, bid for sells, rounded as
            # saty_sol rounds its limit), and the reason carries
            # the signal_id + the profile stamp.
            limit_price=round(exec_px, 2),
            price_hint=round(sig.reference_entry, 2),
            stop=round(sig.stop, 2),
            target=round(sig.targets[0], 2) if sig.targets else None,
            side="buy" if d > 0 else "sell",
            position_intent="buy_to_open" if d > 0 else "sell_to_open",
            reason=(f"saty_gpt_v03/main_10m_1h {sig.setup} "
                    f"{'long' if d > 0 else 'short'} "
                    f"signal_id={sig.signal_id}: "
                    f"qty={qty} ref={sig.reference_entry:.2f} "
                    f"stop={sig.stop:.2f}"),
            signal_date=ctx.session)]


def signal(bars, slice_state, ctx):
    return SatyGptV03().signal(bars, slice_state, ctx)
