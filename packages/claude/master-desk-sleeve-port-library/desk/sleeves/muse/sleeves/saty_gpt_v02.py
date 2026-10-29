"""saty_gpt_v02 — Sol's Saty Research System v0.2.0 as a desk
sleeve (2026-10-23), ported per PORT-SPEC.md in the
saty-gpt-v02 workflow work dir. Source: Silicon commit
3be42c82f70fba0dc6cfb589f4e55471e0d65d4c,
research/saty_mahajan/engine/, package VERSION 0.2.0.

THE PORT IN ONE PARAGRAPH. The strategy is Sol's code, ported
faithfully into core/saty_gpt_v02/ (reference, models,
structure/FeatureBook, strategies/StrategyEngine with his
single-candidate router and all ten families, data Calendar +
resampling + daily references). This file is a thin
desk-contract wrapper in the saty_sol / saty_magnum /
saty_gpt_v03 idiom: it contains NO strategy math of its own.
His brokers/store/service/SQLite layer does not exist here —
the desk dispatcher, the Ink filing door and virtual slices
own execution and accounting. His RiskConfig math survives as
sleeve-internal sizing/lot law against the virtual slice
(core/saty_gpt_v02/risk_lots.py). Expression is SPY SHARES,
long or short, per the pinned config main_10m_1h.json
(expression="equity"); options are OFF. VIX and options flow
stay ABSENT — his acceptance marks both unimplemented and this
port invents neither. 1D/1W streams are not required by the
pinned config; daily bars serve only to build the day
Reference.

WARMUP. 1000 actual completed bars per required clock (10m
and 1H), no per-clock override. Until both clocks reach 1000
for SPY the sleeve stamps blocked_warmup with per-clock
counts and emits no entries. Exits are NEVER trapped behind
warmup (or any other entry block): position management runs
first in every pass.

DETERMINISM. The StrategyEngine's own checkpoint is the
durable strategy state: it rides the journal in
ctx.extra["gpt_v02_journal"] (served back from the ledger by
tools/run_live.py's _v02_session_data via the producer, the
saty_sol / saty_gpt_v03 pattern) and is restored with
load_state at pass start — a checkpoint whose version or
config fingerprint does not match this build is rejected,
never migrated. The FeatureBook is rebuilt each pass by
replaying the door-supplied completed-bar history in
availability order, and its checkpoint checksum is stamped
per pass (the full dump/load round-trip is proven by the
ported structure tests). The sleeve writes no files.
Position truth is the broker/slice position record; the
journal is session/lot/checkpoint bookkeeping only.

SESSION LAW (his data.py Calendar defaults, not the v03
wrapper's): entry cutoff = close - 20m, flat_at = close - 10m.

FORWARD TESTING ONLY. No performance claim anywhere: Sol's
own scope label for the package is mechanical correctness,
not performance, and this port claims nothing more.
"""
import hashlib
import json
from dataclasses import replace as _dataclass_replace
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core.saty_gpt_v02 import midna_enhancements as _enh
from core.saty_gpt_v02 import midna_enhancements2 as _enh2
from core.saty_gpt_v02 import risk_lots
from core.saty_gpt_v02 import (normalize_daily_bars,
                               normalize_intraday_bars)
from core.saty_gpt_v02.data import (Calendar, build_daily_references,
                                    resample_intraday)
from core.saty_gpt_v02.reference import Session
from core.saty_gpt_v02.strategies import (SETUPS, StrategyConfig,
                                          StrategyEngine)
from core.saty_gpt_v02.structure import FeatureBook, StructureConfig

ET = ZoneInfo("America/New_York")
SYM = "SPY"
PROVIDER_FEED = "sip"     # the desk SIP door (volume law)
REPLAY_BARS = 120         # bounded replay when no checkpoint
WARMUP_BARS = 1000        # pinned: structure + strategy warmup
MAX_QUOTE_AGE_S = 5.0     # pinned: desk + risk quote age
EARLY_CLOSES = _SHARED_EARLY_CLOSES

CONFIG = SleeveConfig(
    sleeve_id="saty_gpt_v02",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
)

# Pinned configs (PORT-SPEC section 2, configs/main_10m_1h.json
# transcribed exactly; the config-file enabled order — which is
# also SETUPS order — governs compression-variant precedence).
_STRUCTURE_CFG = StructureConfig(
    required_timeframes=("10m", "1H"),
    max_ages={"10m": timedelta(seconds=1200),
              "1H": timedelta(seconds=7200)},
    warmup_bars=WARMUP_BARS, warmup_by_timeframe={},
    ribbon_version="pro", pivot_left=2, pivot_right=2,
    zone_tolerance_atr=0.1, range_lookback=12, max_history=2048,
    max_pivots=256, max_streams=128, max_calendar_entries=4096,
    require_session=True, require_same_provider=True)
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
_FINGERPRINT = hashlib.sha256(json.dumps({
    "version": "0.2.0",
    "structure": str(sorted(vars(_STRUCTURE_CFG).items())),
    "strategy": _STRATEGY_CFG.fingerprint,
    "risk": str(sorted(vars(risk_lots.RISK).items())),
}, sort_keys=True, default=str).encode()).hexdigest()[:28]


def session_close_dt(session_iso):
    d = date.fromisoformat(session_iso)
    t = EARLY_CLOSES.get(session_iso, dtime(16, 0))
    return datetime.combine(d, t, tzinfo=ET)


def _session_obj(d):
    """His Calendar.from_alpaca defaults: entry delay 0m,
    entry cutoff = close - 20m, flat = close - 10m."""
    iso = d.isoformat()
    close = session_close_dt(iso)
    open_ = datetime.combine(d, dtime(9, 30), tzinfo=ET)
    return Session(session_id=iso, open=open_, entry_start=open_,
                   entry_cutoff=close - timedelta(minutes=20),
                   flat_at=close - timedelta(minutes=10),
                   close=close)


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


def _door_rows(rows):
    """Desk bar tuples -> the row shape his data.py normalizers
    consume ({t iso, o/h/l/c/v})."""
    return [{"t": datetime.fromtimestamp(r[0], tz=ET).isoformat(),
             "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]}
            for r in rows]


def _fresh_journal():
    return {"fingerprint": _FINGERPRINT, "version": "0.2.0",
            "session": None, "e0": None, "entries_taken": 0,
            "entry_pending": None, "episodes": [], "lots": [],
            "sizing_rejections": [], "admission_rejections": [],
            "enh2_refusals": [], "enh2_room": None,
            "enh2_lanes": {},
            "decisions_tail": [],
            "seen_signal_ids": [], "engine_state": None,
            "fed_until": None, "session_carry_block": False,
            "book_checkpoint_session": None}


def _journal(extra, slice_state):
    """The durable journal from the filing door, adopted only
    when its fingerprint matches this build (fresh state
    otherwise — mismatched state is never migrated)."""
    raw = None
    if isinstance(extra.get("gpt_v02_journal"), dict):
        raw = extra["gpt_v02_journal"]
    elif isinstance(slice_state, dict) \
            and isinstance(slice_state.get("gpt_v02_journal"), dict):
        raw = slice_state["gpt_v02_journal"]
    if raw and raw.get("fingerprint") == _FINGERPRINT \
            and raw.get("version") == "0.2.0":
        j = _fresh_journal()
        j.update({k: raw[k] for k in j if k in raw})
        return j, False
    return _fresh_journal(), bool(raw)


class SatyGptV02(BaseSleeve):
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
        """(bid, ask, bid_size, ask_size) from the fresh-quote
        door when two-sided and <= 5s old (pinned quote age);
        sizes are 0 when the door carries none (unknown, never
        invented). None when no usable quote."""
        q = (extra.get("latest_quote") or {}).get(SYM)
        if not isinstance(q, dict) or not q.get("t"):
            return None
        try:
            t_epoch = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00")).timestamp()
            bp, ap = float(q["bp"]), float(q["ap"])
            bs = int(q.get("bs") or 0)
            asz = int(q.get("as") or 0)
        except (KeyError, TypeError, ValueError):
            return None
        if now_epoch - t_epoch > MAX_QUOTE_AGE_S or bp <= 0 or ap < bp:
            return None
        return bp, ap, bs, asz

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
    # exit management — runs FIRST, never trapped (spec 6.5)
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
                      reason=f"saty_gpt_v02 exit: {rule}",
                      signal_date=ctx.session, **kw)

    def _manage(self, pos, journal, extra, ctx, now_dt, stamp,
                bars10, current_session):
        """His exit law (portfolio.py exit_intents mapped to
        desk Intents, PORT-SPEC 6.5): high-water / runner trail,
        fee-aware breakeven after a profitable partial,
        structural stop, target scales (stage goals cumulative,
        filled quantities tracked per stage), force-close at
        flat_at. Evaluated on completed bars + the fresh quote.
        Returns a list of exit intents (possibly empty)."""
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
        # high-water underlying (runner trail input)
        if since:
            fav = max(b[2] for b in since) if d > 0 \
                else min(b[3] for b in since)
            lot["favorable"] = fav if lot.get("favorable") is None \
                else (max(lot["favorable"], fav) if d > 0
                      else min(lot["favorable"], fav))
        # was any partial fill profitable? (fill truth: exit
        # fills priced favorably against the lot entry)
        fills = self._fills(extra) or []
        partial_profitable = any(
            f["position_intent"] in ("sell_to_close", "buy_to_close")
            and d * (f["price"] - entry_px) > 0 for f in fills)
        # per-stage filled quantities from the position delta:
        # stages complete in order, so attribute scaled shares
        # to the earliest incomplete stage first.
        filled_map = {str(k): float(v) for k, v in
                      (lot.get("target_filled") or {}).items()}
        attributed = sum(filled_map.values())
        if scaled > attributed:
            stage_cursor = int(lot.get("target_index") or 0) + 1
            left = scaled - attributed
            while left > 0 and stage_cursor <= len(targets):
                goal = risk_lots.stage_goal(
                    int(initial), int(initial), stage_cursor)
                room = goal - filled_map.get(str(stage_cursor), 0.0)
                take = min(left, max(room, 0.0))
                if take <= 0:
                    break
                filled_map[str(stage_cursor)] = \
                    filled_map.get(str(stage_cursor), 0.0) + take
                left -= take
                stage_cursor += 1
            lot["target_filled"] = filled_map
        completed = int(lot.get("target_index") or 0)
        for s_no in range(1, len(targets) + 1):
            goal = risk_lots.stage_goal(int(initial), int(initial), s_no)
            if filled_map.get(str(s_no), 0.0) >= goal and goal > 0:
                completed = max(completed, s_no)
        lot["target_index"] = completed
        # breakeven after a profitable partial, then the runner
        # trail after a completed stage — tighten-only, always.
        new_stop = stop
        if scaled > 0 and partial_profitable:
            new_stop = risk_lots.tightened(
                new_stop,
                risk_lots.breakeven_stop(entry_px, d), d)
        if completed > 0 and atr > 0 and lot.get("favorable") is not None:
            new_stop = risk_lots.trailed_stop(
                new_stop, d, lot["favorable"], atr)
        if new_stop != stop:
            lot["stop"] = new_stop
            lot.setdefault("stop_history", []).append(
                {"stop": new_stop, "at": ctx.session})
            stop = new_stop
        # current underlying price: quote mid when fresh, else
        # the last completed close (never a stale-price exit —
        # a stop seen only on a stale quote does not fire).
        price_now = None
        if quote is not None:
            price_now = (quote[0] + quote[1]) / 2.0
        elif bars10:
            price_now = bars10[-1][4]
        # force-close at flat_at (close - 10m, his session law)
        if current_session is not None \
                and now_dt >= current_session.flat_at:
            stamp["decision"] = "force_close"
            return [self._exit_intent(qty_signed, "force_close",
                                      quote, ctx)]
        # structural stop: price at/through the stop
        if price_now is not None and d * (price_now - stop) <= 0:
            stamp["decision"] = "stop_exit"
            if quote is None:
                return [self._exit_intent(
                    qty_signed, "stop_exit_blocked_no_quote",
                    None, ctx)]
            return [self._exit_intent(qty_signed, "stop_exit",
                                      quote, ctx)]
        # target scales in path order
        stage = completed + 1
        if stage <= len(targets):
            tgt = targets[stage - 1]
            touched = (price_now is not None
                       and d * (price_now - tgt) >= 0) or any(
                           (b[2] >= tgt if d > 0 else b[3] <= tgt)
                           for b in since)
            if touched:
                due = risk_lots.scale_quantity(
                    int(initial), stage,
                    filled_for_stage=int(
                        filled_map.get(str(stage), 0.0)),
                    remaining_qty=int(remaining))
                if due >= 1:
                    stamp["decision"] = f"target_scale_{stage}"
                    if quote is None:
                        stamp["exit_pending_no_quote"] = \
                            f"target_scale_{stage}"
                        return []
                    return [self._exit_intent(
                        d * int(due), f"target_scale_{stage}",
                        quote, ctx)]
        return []

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "saty_gpt_v02", "session": ctx.session,
                 "state": "armed", "warmup": {"10m": 0, "1H": 0},
                 "frames": {}, "reference": None,
                 "candidate": None, "routes": [],
                 "session_pnl_r": None, "entries_taken": 0,
                 "open_lots": 0, "decision": None,
                 "stood_down": None, "flat_at": None,
                 "checkpoint_restored": False,
                 "book_checkpoint": None}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        extra = ctx.extra or {}
        journal, rejected = _journal(extra, slice_state)
        stamp["gpt_v02_journal"] = journal
        if rejected:
            stamp["journal_rejected"] = "fingerprint_mismatch"
        # MIDNA-ENH-2: bound the journal's unbounded lists at
        # adoption (open/intent records are never dropped).
        if _enh.enh_enabled(extra, "bound_journal"):
            _enh.bound_journal(journal)
        # session reset (spec 6.6): session fields reset for a
        # new session ONLY when flat — no open lots, no pending
        # entry, no position. Otherwise the state carries and
        # entries stay blocked under the named reason.
        if journal["session"] != ctx.session:
            has_lots = any(x.get("state") == "open"
                           for x in journal["lots"])
            pos_pre = self._position(extra, slice_state)
            if not has_lots and not journal.get("entry_pending") \
                    and pos_pre is None:
                journal["session"] = ctx.session
                journal["e0"] = float(ctx.equity or 0.0) or None
                journal["entries_taken"] = 0
                journal["entry_pending"] = None
                journal["session_carry_block"] = False
            elif journal["session"] is not None:
                journal["session_carry_block"] = True
                stamp["session_reset_blocked"] = \
                    "open_lot_or_pending_entry"
            else:
                journal["session"] = ctx.session
                journal["session_carry_block"] = has_lots
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
                        "target_filled": {}, "target_index": 0,
                        "signal_id": _ep.get("signal_id")})
                    _ep["state"] = "filled"
                    journal["entry_pending"] = None
            if _pos0 is None:
                for _lot in journal["lots"]:
                    if _lot.get("state") == "open":
                        _lot["state"] = "closed"

        # raw frames from the producer bundle: the long 5m SIP
        # history is the one door input; 10m and 1H are built
        # from it with his data.py rules (complete buckets only).
        raw5 = _shape((extra.get("bars_5m_long") or {}).get(SYM)) \
            if isinstance(extra.get("bars_5m_long"), dict) else []
        raw10d = _shape((extra.get("bars_10m") or {}).get(SYM)) \
            if isinstance(extra.get("bars_10m"), dict) else []
        base_rows = raw5 if raw5 else raw10d
        stamp["frames"] = {"5m_long": len(raw5), "10m": len(raw10d)}

        daily_raw = []
        if isinstance(bars, dict):
            daily_raw = _shape(bars.get(SYM))
        if not daily_raw and isinstance(extra.get("bars_daily"), dict):
            daily_raw = _shape(extra["bars_daily"].get(SYM))
        # sessions from every date present (intraday + daily)
        # + today: the daily Reference's prior sessions must
        # be registered in the calendar or no Reference can
        # ever validate.
        days = sorted({datetime.fromtimestamp(b[0], tz=ET).date()
                       for b in base_rows}
                      | {datetime.fromtimestamp(b[0], tz=ET).date()
                         for b in daily_raw}
                      | {session_d})
        sessions = [_session_obj(d) for d in days
                    if is_trading_day(d)]
        current_session = next(
            (s for s in sessions if s.session_id == ctx.session), None)
        if current_session is not None:
            stamp["flat_at"] = current_session.flat_at.isoformat()

        # build the execution clock ONCE (his data.py rules);
        # the main build below reuses these observations — a
        # second normalize/resample over ~14k door rows would
        # double the pass cost for nothing.
        bars10 = []
        obs10_pre = []
        calendar_pre = Calendar(sessions) if sessions else None
        if base_rows and calendar_pre is not None:
            step = base_rows[1][0] - base_rows[0][0] \
                if len(base_rows) > 1 else 300.0
            minutes = {300.0: 5, 600.0: 10}.get(step)
            if minutes is not None:
                try:
                    obs_base = normalize_intraday_bars(
                        SYM, _door_rows(base_rows),
                        f"{minutes}m", calendar_pre,
                        feed=PROVIDER_FEED)
                    obs10_pre = resample_intraday(
                        obs_base, "10m", calendar_pre) \
                        if minutes == 5 else obs_base
                    obs10_pre = [o for o in obs10_pre
                                 if o.available_at <= now_dt]
                    bars10 = [(o.bar.start.timestamp(), o.bar.open,
                               o.bar.high, o.bar.low, o.bar.close,
                               o.bar.volume) for o in obs10_pre]
                except ValueError:
                    bars10 = []
                    obs10_pre = []
        stamp["warmup"] = {"10m": len(bars10), "1H": 0}

        # 1. exits first — always, in every state (spec 6.5)
        pos = self._position(extra, slice_state)
        if pos is not None:
            exits = self._manage(pos, journal, extra, ctx, now_dt,
                                 stamp, bars10, current_session)
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
        if not base_rows or not sessions:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no 5m history (C-1)"
            return []
        if current_session is None:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: session unregistered (C-4)"
            return []
        if not daily_raw:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no daily bars (C-3)"
            return []

        calendar = calendar_pre
        # the 1H context clock + the daily Reference, built
        # from the reused 10m observations with his rules
        try:
            obs10 = obs10_pre
            obs1h = resample_intraday(obs10, "1H", calendar)
            daily_obs = normalize_daily_bars(
                SYM, _door_rows(daily_raw), calendar,
                feed=PROVIDER_FEED)
            refs_list = [ref for (sym, ref) in
                         build_daily_references(daily_obs, calendar)
                         if sym == SYM]
        except ValueError:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: bar build rejected (C-1)"
            return []
        obs1h = [o for o in obs1h if o.available_at <= now_dt]
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

        # rebuild the FeatureBook deterministically
        book = FeatureBook(_STRUCTURE_CFG)
        for s in sessions:
            book.register_session(s)
        for ref in refs_list:
            book.register_reference_period(
                SYM, "day", ref.valid_from, ref.valid_until,
                ref.period_end, known_at=ref.available_at)
        counts = {"10m": 0, "1H": 0}
        obs_all = sorted([*obs10, *obs1h],
                          key=lambda o: o.available_at)
        for o in obs_all:
            try:
                frame = book.update(o)
                counts[o.timeframe] = frame.count
            except ValueError:
                stamp["state"] = "blocked_data"
                stamp["decision"] = \
                    "blocked_data: observation rejected (C-1/C-10)"
                return []
        stamp["warmup"] = {"10m": counts["10m"], "1H": counts["1H"]}
        # the book's own checkpoint mechanism, proven once per
        # session (the journal carries the marker; the full
        # dump/load round-trip over ~2000 retained records is
        # too heavy to repeat every 60s pass, and the ported
        # structure tests prove it as a release gate)
        if journal.get("book_checkpoint_session") == ctx.session:
            stamp["book_checkpoint"] = "session_cached"
        else:
            try:
                payload = book.dump_state()
                FeatureBook(_STRUCTURE_CFG).load_state(payload)
                stamp["book_checkpoint"] = payload.get("checksum")
                journal["book_checkpoint_session"] = ctx.session
            except Exception:
                stamp["book_checkpoint"] = None
                stamp["book_checkpoint_failed"] = True

        # final context at the final completed bar's end (the
        # decision time — never wall-clock now, the v03 R3 law)
        final_end = obs10[-1].bar.end if obs10 else None
        if final_end is None:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no 10m bars (C-1)"
            return []
        # the decision time for a bar is when it became
        # available (bar end + finalization), not the bar end
        # itself: his context session/reference guards require
        # bar.end <= as_of <= close, and his engine requires
        # available_at <= as_of with lag <= 300s.
        final_as_of = obs10[-1].available_at
        # MIDNA-ENH-3: causal context stamp (stance-0, never a
        # veto): session phase + close vs day anchor in ATRs.
        if _enh.enh_enabled(extra, "context_stamps"):
            stamp["enh_context"] = _enh.context_stamp(
                now_dt, current_session, reference.close,
                reference.atr, obs10[-1].bar.close)
        try:
            context = book.context(SYM, "10m", final_as_of, reference,
                                   session=current_session)
        except ValueError:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no execution frame (C-1)"
            return []
        blockers = list(context.blockers or ())
        warm = counts["10m"] >= WARMUP_BARS and \
            counts["1H"] >= WARMUP_BARS
        if not warm or any(b.startswith("WARMUP") for b in blockers):
            stamp["state"] = "blocked_warmup"
            stamp["decision"] = \
                f"blocked_warmup: 10m={counts['10m']} 1H={counts['1H']}"
            # MIDNA-ENH-4: the block names its own cure distance.
            if _enh.enh_enabled(extra, "warmup_transparency"):
                stamp["enh_warmup"] = _enh.warmup_report(
                    counts, WARMUP_BARS)
            return []
        if blockers:
            stamp["state"] = "blocked_context" \
                if any("REFERENCE" in b for b in blockers) \
                else "blocked_data"
            stamp["decision"] = "blocked: " + ",".join(blockers)
            return []
        if journal.get("session_carry_block"):
            stamp["state"] = "blocked_session_carry"
            stamp["decision"] = \
                "blocked: session reset refused (open lot/pending)"
            return []

        # strategy evaluation: restore his engine checkpoint
        # from the journal when present (the durable strategy
        # state), else replay the bounded window; feed only
        # contexts newer than the checkpoint's fed_until, plus
        # the final context (his engine dedupes an exact repeat).
        engine = StrategyEngine(_STRATEGY_CFG)
        restored = False
        if isinstance(journal.get("engine_state"), dict):
            try:
                engine.load_state(journal["engine_state"])
                restored = True
            except (ValueError, KeyError, TypeError):
                stamp["engine_checkpoint_rejected"] = \
                    "version_or_config_mismatch"
        stamp["checkpoint_restored"] = restored
        fed_until = None
        if restored and journal.get("fed_until"):
            try:
                fed_until = datetime.fromisoformat(journal["fed_until"])
            except ValueError:
                fed_until = None
        sess_by_id = {s.session_id: s for s in sessions}
        ends = [o.bar.end for o in obs10]
        avail_by_end = {o.bar.end: o.available_at for o in obs10}
        if restored:
            feed_ends = [t for t in ends
                         if fed_until is None or t > fed_until]
            if ends and (not feed_ends or feed_ends[-1] != ends[-1]):
                feed_ends.append(ends[-1])
        else:
            feed_ends = ends[-REPLAY_BARS:]
        # MIDNA-ENH2 candidate generation: nine family lanes
        # (his StrategyEngine over the SAME causal contexts,
        # one family per lane; the compression pair shares a
        # lane in his config order) exist only while the
        # set-level deltas (arbitration / opposite sanity) are
        # ON. Their checkpoints ride the journal like his.
        lanes = {}
        lane_signals = []
        if _enh2.lanes_on(extra):
            saved_lanes = journal.get("enh2_lanes") or {}
            for group in _enh2.LANE_GROUPS:
                key = "+".join(group)
                lane = StrategyEngine(_dataclass_replace(
                    _STRATEGY_CFG, enabled=tuple(group)))
                lane_restored = False
                if isinstance(saved_lanes.get(key), dict):
                    try:
                        lane.load_state(saved_lanes[key])
                        lane_restored = True
                    except (ValueError, KeyError, TypeError):
                        lane_restored = False
                lanes[key] = (
                    lane, set(feed_ends) if lane_restored
                    else set(ends[-REPLAY_BARS:]))
        signals = []
        final_ctx = None
        decisions_before = len(engine.decisions)
        for t_end in feed_ends:
            ref_t = next((r for r in refs_list
                          if r.valid_from <= t_end < r.valid_until),
                         None)
            sess_t = sess_by_id.get(t_end.date().isoformat())
            if ref_t is None or sess_t is None:
                continue
            try:
                ctx_t = book.context(
                    SYM, "10m", avail_by_end[t_end], ref_t,
                    session=sess_t)
            except ValueError:
                continue
            got = engine.update(ctx_t)
            for lane, lane_feed in lanes.values():
                if t_end in lane_feed:
                    lane_got = lane.update(ctx_t)
                    if t_end == ends[-1]:
                        lane_signals.extend(lane_got)
            if t_end == ends[-1]:
                signals = got
                final_ctx = ctx_t
        if lanes:
            filed_lanes = {}
            for key, (lane, _feed) in lanes.items():
                try:
                    payload = lane.dump_state()
                    if len(payload.get("decisions") or []) > 128:
                        payload["decisions"] = \
                            payload["decisions"][-128:]
                    filed_lanes[key] = payload
                except Exception:
                    filed_lanes[key] = (journal.get("enh2_lanes")
                                        or {}).get(key)
            journal["enh2_lanes"] = filed_lanes
        new_decisions = engine.decisions[decisions_before:]
        journal["decisions_tail"] = (
            (journal.get("decisions_tail") or [])[-64:]
            + new_decisions)[-64:]
        routes = [d.get("route") for d in new_decisions
                  if d.get("event") == "ROUTE"]
        stamp["routes"] = routes[-3:]
        arm = engine._state.get("arm")
        stamp["candidate"] = arm.get("setup") if arm else None
        # file the engine checkpoint for the next pass (the
        # decisions tail is capped in the FILED copy only; the
        # live engine's own list is untouched)
        try:
            state_payload = engine.dump_state()
            if len(state_payload.get("decisions") or []) > 512:
                state_payload["decisions"] = \
                    state_payload["decisions"][-512:]
            journal["engine_state"] = state_payload
            journal["fed_until"] = ends[-1].isoformat() if ends else None
        except Exception:
            stamp["engine_checkpoint_failed"] = True

        # session accounting from fill truth
        fills = self._fills(extra)
        realized, open_lots, fill_entries = (0.0, [], 0) \
            if fills is None else self._realized(fills)
        # his _equity basis: realized slice equity (initial +
        # realized net P&L, no unrealized mark). The desk slice
        # equity already reflects realized P&L; the per-entry
        # basis is min(current, session-start) inside the math.
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
        # MIDNA-ENH2 decision pipeline: arbitrate among his
        # surviving candidates (faithful + lane), add the
        # behavioral refusals, THEN his faithful admission and
        # sizing run unchanged on the selected signal. All
        # switches OFF (or no candidates) = the pre-ENH2 path.
        sig = signals[0] if signals else None
        if _enh2.any_enh2_on(extra) and (signals or lane_signals):
            by_id = {}
            cands = []
            if signals:
                c0 = _enh2.candidate_from_signal(signals[0],
                                                 faithful=True)
                cands.append(c0)
                by_id[c0["signal_id"]] = signals[0]
            seen_keys = {(c["setup"], c["direction"])
                         for c in cands}
            for ls in lane_signals:
                key = (ls.setup, int(ls.direction))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                cx = _enh2.candidate_from_signal(ls)
                cands.append(cx)
                by_id[cx["signal_id"]] = ls
            q0 = self._quote(extra, ctx.now)
            quote2 = (q0[0], q0[1]) if q0 is not None else None
            ctx2 = {"stack": 0, "phase": None,
                    "anchor_distance_atr": None}
            if final_ctx is not None:
                frame1h = (final_ctx.frames or {}).get("1H")
                if frame1h is not None:
                    try:
                        ctx2["stack"] = StrategyEngine._stack(
                            frame1h.features.ema)
                        ctx2["phase"] = frame1h.features.phase
                    except (KeyError, TypeError):
                        pass
                dist = (stamp.get("enh_context") or {}).get(
                    "anchor_distance_atr")
                if dist is None and reference.atr:
                    dist = round(
                        (obs10[-1].bar.close - reference.close)
                        / reference.atr, 4)
                ctx2["anchor_distance_atr"] = dist
            room_j = journal.get("enh2_room")
            best_net_r = room_j.get("best_net_r") if isinstance(
                room_j, dict) and room_j.get("session") == ctx.session \
                else None
            verdict = _enh2.decide(
                cands, extra, quote=quote2, context=ctx2,
                session_pnl_r=session_pnl_r, best_net_r=best_net_r,
                decision_bar_end=ends[-1].isoformat()
                if ends else None,
                decision_time=final_as_of,
                flat_at=current_session.flat_at
                if current_session is not None else None)
            stamp["enh2"] = {
                "candidates": [c["setup"] for c in cands],
                "selected": verdict["selected"]["setup"]
                if verdict["selected"] else None,
                "refusals": verdict["refusals"],
                "strong_context": verdict["strong_context"]}
            if quote2 is not None:
                stamp["enh2"]["spread"] = round(
                    quote2[1] - quote2[0], 4)
            if verdict["refusals"]:
                journal["enh2_refusals"] = (
                    (journal.get("enh2_refusals") or [])
                    + [{"session": ctx.session, **r}
                       for r in verdict["refusals"]])[-32:]
            if verdict["survivors_net_r"]:
                new_best = max(verdict["survivors_net_r"])
                if best_net_r is not None:
                    new_best = max(new_best, best_net_r)
                journal["enh2_room"] = {
                    "session": ctx.session, "best_net_r": new_best}
            if verdict["selected"] is not None:
                sig = by_id[verdict["selected"]["signal_id"]]
            elif verdict["refusals"]:
                sig = None
                stamp["stood_down"] = verdict["refusals"][-1]["reason"]
                stamp["decision"] = \
                    "enh2_refused: " + verdict["refusals"][-1]["reason"]
                return []
            else:
                sig = None
        if sig is None:
            stamp["decision"] = "no_signal"
            # MIDNA-ENH-1: a silent pass is enumerated, never
            # implied — per-event and per-setup refusal census.
            if _enh.enh_enabled(extra, "silence_audit"):
                stamp["enh_silence_audit"] = _enh.silence_audit(
                    new_decisions, stamp["candidate"], "no_signal")
            return []
        if sig.signal_id in (journal.get("seen_signal_ids") or []):
            stamp["stood_down"] = "duplicate_signal_id"
            stamp["decision"] = "duplicate_signal_suppressed"
            if _enh.enh_enabled(extra, "silence_audit"):
                stamp["enh_silence_audit"] = _enh.silence_audit(
                    new_decisions, sig.setup, "duplicate_signal_id")
            return []
        stamp["candidate"] = sig.setup
        d = 1 if sig.direction > 0 else -1
        # shortable declaration (spec 6.1): SPY shares are
        # registered shortable in this wrapper's instrument
        # record; absent a desk declaration to the contrary in
        # ctx.market, short signals stand down, never coerced.
        if d < 0 and not (ctx.market or {}).get("spy_shortable", True):
            stamp["stood_down"] = "not_shortable"
            return []
        quote = self._quote(extra, ctx.now)
        if quote is None:
            stamp["stood_down"] = "entry_window_closed: no fresh quote"
            return []
        exec_px = quote[1] if d > 0 else quote[0]
        depth = quote[3] if d > 0 else quote[2]
        ok_adm, why = risk_lots.admission_recheck(
            d, sig.reference_entry, sig.stop, sig.targets, exec_px,
            sig.atr)
        if not ok_adm:
            stamp["stood_down"] = why
            # MIDNA-ENH-5b: admission refusals are journal-named
            # (parity with sizing refusals; faithful code left
            # them stamp-only, lost on the next pass).
            if _enh.enh_enabled(extra, "exec_audit"):
                journal.setdefault("admission_rejections", [])
                journal["admission_rejections"].append({
                    "session": ctx.session, "setup": sig.setup,
                    "reason": why, "entry": exec_px})
                if _enh.enh_enabled(extra, "silence_audit"):
                    stamp["enh_silence_audit"] = _enh.silence_audit(
                        new_decisions, sig.setup, why)
            return []
        qty, why_qty = risk_lots.compute_qty(
            float(ctx.equity or 0.0), journal["e0"] or ctx.equity or 0.0,
            exec_px, sig.stop,
            risk_multiplier=sig.risk_multiplier,
            open_risk_r=0.0, open_notional=0.0,
            entries_taken=entries_taken,
            session_pnl_r=session_pnl_r or 0.0,
            depth=depth if depth > 0 else None)
        if qty < 1:
            journal["sizing_rejections"].append({
                "session": ctx.session, "setup": sig.setup,
                "reason": why_qty, "entry": exec_px,
                "stop": sig.stop})
            stamp["stood_down"] = why_qty
            stamp["decision"] = "sizing_zero_recorded"
            if _enh.enh_enabled(extra, "silence_audit"):
                stamp["enh_silence_audit"] = _enh.silence_audit(
                    new_decisions, sig.setup, why_qty)
            return []
        journal["entry_pending"] = {
            "signal_id": sig.signal_id, "setup": sig.setup,
            "direction": d, "session": ctx.session}
        journal["entries_taken"] = entries_taken + 1
        journal["seen_signal_ids"] = (
            (journal.get("seen_signal_ids") or [])
            + [sig.signal_id])[-256:]
        journal["episodes"].append({
            "signal_id": sig.signal_id, "setup": sig.setup,
            "direction": d, "entry_ref": sig.reference_entry,
            "stop": sig.stop, "targets": list(sig.targets),
            "atr": sig.atr, "state": "intent",
            "session": ctx.session})
        stamp["decision"] = f"enter {sig.setup}"
        # MIDNA-ENH-5a: the executable terms, stamped for audit.
        if _enh.enh_enabled(extra, "exec_audit"):
            stamp["enh_exec"] = _enh.exec_audit(
                d, exec_px, sig.reference_entry, sig.atr, quote)
        return [Intent(
            "enter", SYM, qty=int(qty),
            limit_price=round(exec_px, 2),
            price_hint=round(sig.reference_entry, 2),
            stop=round(sig.stop, 2),
            target=round(sig.targets[0], 2) if sig.targets else None,
            side="buy" if d > 0 else "sell",
            position_intent="buy_to_open" if d > 0 else "sell_to_open",
            reason=(f"saty_gpt_v02/main_10m_1h {sig.setup} "
                    f"{'long' if d > 0 else 'short'} "
                    f"signal_id={sig.signal_id}: "
                    f"qty={qty} ref={sig.reference_entry:.2f} "
                    f"stop={sig.stop:.2f}"),
            signal_date=ctx.session)]


def signal(bars, slice_state, ctx):
    return SatyGptV02().signal(bars, slice_state, ctx)
