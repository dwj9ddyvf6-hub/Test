"""raschke_pf3 — Linda Raschke's PF3 momentum method as
designed into an autonomous algorithm by Grok at User's
request (2026-10-23), built 2026-10-23 per SPEC.md (workflow
pf3-raschke-20261023). Lineage, recorded verbatim: method =
Linda Raschke's PF3; algorithm design by Grok at User's
request (2026-10-23); transcribed from User's screenshot of
that date.

GROK'S DESIGN (verbatim): "PF3 autonomous algo (ES 5-min):
Calc: ROC2 = C - C[2]; Fast = SMA(C,3) - SMA(C,10); Slow =
SMA(Fast,16). Long if all slopes up (ROC2>ROC2[1],
Fast>Fast[1], Slow>Slow[1]) Short if all down. Enter next
bar open. Stop 0.75 ATR(14). Target 1.5 ATR or exit after
6-10 bars / slope reverse. 1 trade per cluster. Risk 0.5%
equity. Trend filter optional (ADX>20)."

THE TRANSLATION (GP-1, stated plainly). Grok's design is
written for ES 5-minute futures. This desk has no futures:
the paper API exposes no futures asset class (verified
2026-10-21 for the po10_qqq build), so the sleeve expresses
PF3 as SPY SHARES, long and short, on completed 5-minute
SIP bars through the shared data door — the po10_qqq
precedent (NQ method -> QQQ shares). No options. Every
result this sleeve produces is a SPY result, never an ES
result.

DESK PINS (GROK-PIN register, SPEC.md sections 2-12; every
number Grok did not pin is a named desk decision, never
attributed to Raschke or Grok): signal math exact with
strict inequalities (a zero slope is not aligned, GP-2);
warmup 26 completed RTH 5m bars, 28 with the trend filter
ON, fail-closed as blocked_warmup (GP-3); entry anchor =
signal-bar close, stop/target frozen at signal time off
that anchor (GP-4); stop/target are in-signal completed-
bar-close evaluations, never broker resting stops — this
sleeve is NOT in protection QUALIFYING (GP-5); slope-
reverse exit = first completed bar after the entry bar
where any slope is no longer aligned with the position
(GP-6); time exit at 10 bars max hold, the upper bound of
Grok's 6-10 (GP-7); flat at close - 5 minutes, entry
cutoff at close - 10 minutes, early closes from
core/early_close.py (GP-8); RTH-only bar basis, continuous
across sessions, premarket bars never enter the math
(GP-9); one entry attempt per cluster, consumed on
emission (GP-10); opposite clusters may follow immediately
(GP-11); sizing qty = floor(0.005 x slice equity /
(0.75 x ATR)), zero qty is a journal-named no-trade (GP-12);
trend filter switch gpf3_trend_filter default OFF, ON
requires Wilder ADX(14) > 20 at the signal bar (GP-13);
exit precedence flat > stop > target > slope-reverse >
time (GP-14); durable bookkeeping rides the ledger journal
gpf3_journal, position truth stays the broker/slice record
(GP-15); market intents only, price_hint is reference only
(GP-16); no backfill of a missed cluster (GP-17); a carried
overnight position is exited on the session's first pass
(GP-18); short entries stand down when the desk declares
SPY not shortable (GP-19).

DESK SHAPE. CONFIG + signal() in the saty_magnum /
saty_gpt_v02 idiom: a pure function of (bars, fills,
journal, ctx), deterministically reconstructed on every
60-second pass. Position management runs FIRST in every
pass and is never trapped behind warmup, the trend filter,
or any entry block. Every decision is stamped onto
self.last_evaluation, which the dispatcher merges into the
evaluation ledger row. The sleeve writes no files.

FORWARD TESTING ONLY. This sleeve claims no edge and no
backtest result anywhere (desk law). Grok's phrase
"high-probability" is Grok's summary language, recorded in
the spec, and is not a claim of this desk.
"""
import hashlib
import json
import math
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import session_close_dt
from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYM = "SPY"

CONFIG = SleeveConfig(
    sleeve_id="raschke_pf3",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
    risk_pct=0.005,
)

# -- Grok's numbers (verbatim from the design) ----------------
STOP_MULT = 0.75               # stop 0.75 ATR(14)
TARGET_MULT = 1.5              # target 1.5 ATR
MAX_HOLD_BARS = 10             # GP-7: upper bound of his 6-10
RISK_PCT = 0.005               # risk 0.5% equity
ADX_THRESHOLD = 20.0           # trend filter: ADX > 20

# -- desk pins (GROK-PIN register) -----------------------------
WARMUP_BARS = 26               # GP-3 (trend filter OFF)
WARMUP_BARS_FILTER = 28        # GP-3 (trend filter ON)
FLAT_BEFORE_CLOSE_MIN = 5      # GP-8
CUTOFF_BEFORE_CLOSE_MIN = 10   # GP-8
BAR_SECONDS = 300              # 5-minute bars

_FINGERPRINT = hashlib.sha256(json.dumps({
    "sleeve": "raschke_pf3", "version": "1.0",
    "stop_mult": STOP_MULT, "target_mult": TARGET_MULT,
    "max_hold": MAX_HOLD_BARS, "risk_pct": RISK_PCT,
    "warmup": WARMUP_BARS, "warmup_filter": WARMUP_BARS_FILTER,
    "flat_min": FLAT_BEFORE_CLOSE_MIN,
    "cutoff_min": CUTOFF_BEFORE_CLOSE_MIN,
}, sort_keys=True).encode()).hexdigest()[:28]


def _fresh_journal():
    return {"fingerprint": _FINGERPRINT, "version": "1.0",
            "consumed_clusters": [], "lot": None,
            "sizing_rejections": []}


def _journal(extra, slice_state):
    """The durable journal from the filing door, adopted only
    when its fingerprint and version match this build (fresh
    state otherwise — mismatched state is never migrated,
    GP-15 / the v02 law). Returns (journal, rejected_flag,
    door_present)."""
    raw = None
    if isinstance(extra.get("gpf3_journal"), dict):
        raw = extra["gpf3_journal"]
    elif isinstance(slice_state, dict) \
            and isinstance(slice_state.get("gpf3_journal"), dict):
        raw = slice_state["gpf3_journal"]
    if raw and raw.get("fingerprint") == _FINGERPRINT \
            and raw.get("version") == "1.0":
        j = _fresh_journal()
        j.update({k: raw[k] for k in j if k in raw})
        return j, False, True
    return _fresh_journal(), bool(raw), raw is not None


def _shape(raw):
    """Desk bars ({t epoch, o/h/l/c/v}) -> sorted tuples
    (start_epoch, o, h, l, c, v). Unparseable rows are
    dropped, never guessed. Duplicate starts: the later row
    is dropped, the first kept (SPEC section 5); the drop is
    reported so the pass can stamp it. Returns (rows, dup)."""
    out = []
    for b in raw or []:
        try:
            out.append((float(b["t"]), float(b["o"]), float(b["h"]),
                        float(b["l"]), float(b["c"]),
                        float(b.get("v") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda x: x[0])
    rows, dup, seen = [], False, set()
    for r in out:
        if r[0] in seen:
            dup = True
            continue
        seen.add(r[0])
        rows.append(r)
    return rows, dup


def _rth_series(raw, now_epoch):
    """The continuous RTH completed-bar series (GP-9): a bar
    belongs iff its start falls in [09:30, session close) ET
    on a trading day (close from core/early_close.py) and its
    close time is <= now. Premarket / extended-hours bars
    never enter the math. Returns (rows, duplicate_dropped)."""
    rows, dup = _shape(raw)
    out = []
    for r in rows:
        t = r[0]
        if t + BAR_SECONDS > now_epoch:
            continue  # forming bar: never arms/triggers/exits
        start_dt = datetime.fromtimestamp(t, tz=ET)
        d = start_dt.date()
        if not is_trading_day(d):
            continue
        open_dt = datetime.combine(d, dtime(9, 30), tzinfo=ET)
        if not (open_dt <= start_dt < session_close_dt(d.isoformat())):
            continue
        out.append(r)
    return out, dup


def _sma(values, n):
    """SMA over a list that may hold None (undefined) values:
    defined at i when the full window values[i-n+1..i] is
    defined. Returns a same-length list with None gaps."""
    out = [None] * len(values)
    run = 0.0
    for i, v in enumerate(values):
        if v is None:
            run = 0.0
            continue
        run += v
        if i >= n and values[i - n] is not None:
            run -= values[i - n]
        if i >= n - 1 and all(x is not None
                              for x in values[i - n + 1:i + 1]):
            out[i] = run / n
    return out


def indicators(closes, highs, lows):
    """PF3 series + Wilder ATR(14) + Wilder ADX(14) over the
    completed-bar series (SPEC section 4 / GP-2 / GP-13).
    Pure function; every list is same-length, None where
    undefined. Slopes are first differences; alignment is
    +1 (all slopes > 0), -1 (all < 0), 0 (defined but not
    aligned — a zero slope is not aligned), None (undefined)."""
    n = len(closes)
    roc2 = [None] * n
    for i in range(2, n):
        roc2[i] = closes[i] - closes[i - 2]
    sma3 = _sma(closes, 3)
    sma10 = _sma(closes, 10)
    fast = [None] * n
    for i in range(n):
        if sma3[i] is not None and sma10[i] is not None:
            fast[i] = sma3[i] - sma10[i]
    slow = _sma(fast, 16)

    def _slope(series):
        out = [None] * n
        for i in range(1, n):
            if series[i] is not None and series[i - 1] is not None:
                out[i] = series[i] - series[i - 1]
        return out

    sroc, sfast, sslow = _slope(roc2), _slope(fast), _slope(slow)
    alignment = [None] * n
    for i in range(n):
        s = (sroc[i], sfast[i], sslow[i])
        if any(x is None for x in s):
            continue
        if all(x > 0 for x in s):
            alignment[i] = 1
        elif all(x < 0 for x in s):
            alignment[i] = -1
        else:
            alignment[i] = 0
    # Wilder ATR(14)
    tr = [None] * n
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]))
    atr = [None] * n
    if n > 14:
        atr[14] = sum(tr[1:15]) / 14.0
        for i in range(15, n):
            atr[i] = (atr[i - 1] * 13.0 + tr[i]) / 14.0
    # Wilder ADX(14): smoothed TR/+DM/-DM seeded as 14-period
    # sums at bar 15 (index 14); DX there; ADX seeded as the
    # mean of DX over bars 15..28 (indices 14..27) at index 27.
    adx = [None] * n
    if n > 14:
        pdm = [0.0] * n
        mdm = [0.0] * n
        for i in range(1, n):
            up = highs[i] - highs[i - 1]
            down = lows[i - 1] - lows[i]
            pdm[i] = up if (up > down and up > 0) else 0.0
            mdm[i] = down if (down > up and down > 0) else 0.0
        dx = [None] * n
        s_tr = sum(tr[1:15])
        s_p = sum(pdm[1:15])
        s_m = sum(mdm[1:15])
        for i in range(14, n):
            if i > 14:
                s_tr = s_tr - s_tr / 14.0 + tr[i]
                s_p = s_p - s_p / 14.0 + pdm[i]
                s_m = s_m - s_m / 14.0 + mdm[i]
            if s_tr > 0:
                pdi = 100.0 * s_p / s_tr
                mdi = 100.0 * s_m / s_tr
            else:
                pdi = mdi = 0.0
            denom = pdi + mdi
            dx[i] = (100.0 * abs(pdi - mdi) / denom) if denom > 0 else 0.0
        if n > 27:
            adx[27] = sum(dx[14:28]) / 14.0
            for i in range(28, n):
                adx[i] = (adx[i - 1] * 13.0 + dx[i]) / 14.0
    return {"roc2": roc2, "fast": fast, "slow": slow,
            "sroc": sroc, "sfast": sfast, "sslow": sslow,
            "alignment": alignment, "atr": atr, "adx": adx}


def clusters_of(alignment, starts):
    """Maximal runs of consecutive bars aligned in one
    direction (GP-10). Returns [{direction, first, last,
    cluster_id}]; cluster_id pins the first bar's session,
    its start epoch, and the signed direction."""
    out = []
    i, n = 0, len(alignment)
    while i < n:
        d = alignment[i]
        if d in (1, -1):
            j = i
            while j + 1 < n and alignment[j + 1] == d:
                j += 1
            sess = datetime.fromtimestamp(starts[i], tz=ET) \
                .date().isoformat()
            out.append({
                "direction": d, "first": i, "last": j,
                "cluster_id": f"{sess}:{int(starts[i])}:{d:+d}"})
            i = j + 1
        else:
            i += 1
    return out


def compute_qty(equity, atr):
    """GP-12 sizing: (qty, refusal_reason|None).
    qty = floor(0.005 x equity / (0.75 x ATR)); a refusal is
    named, never silently floored to a share."""
    try:
        eq = float(equity)
        a = float(atr)
    except (TypeError, ValueError):
        return 0, "atr_unusable"
    if not math.isfinite(a) or a <= 0:
        return 0, "atr_unusable"
    if not math.isfinite(eq) or eq <= 0:
        return 0, "equity_unusable"
    qty = math.floor(RISK_PCT * eq / (STOP_MULT * a))
    if qty < 1:
        return 0, "qty_rounds_to_zero"
    return int(qty), None


def _filter_on(extra):
    """GP-13 switch: ctx.extra['gpf3_trend_filter'], absent
    = OFF (the faithful default)."""
    v = extra.get("gpf3_trend_filter")
    if v is True:
        return True
    if isinstance(v, str):
        return v.strip().lower() in ("on", "true", "1")
    return bool(v) if isinstance(v, (int, float)) else False


class RaschkePf3(BaseSleeve):
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

    def _exit_intent(self, qty_signed, rule, ctx):
        d = 1 if qty_signed > 0 else -1
        q = abs(float(qty_signed))
        q = int(q) if q == int(q) else q
        side = "sell" if d > 0 else "buy"
        pi = "sell_to_close" if d > 0 else "buy_to_close"
        return Intent(
            "exit", SYM, qty=q, side=side, position_intent=pi,
            reason=(f"raschke_pf3 exit: {rule} "
                    f"{'long' if d > 0 else 'short'} qty={q}"),
            signal_date=ctx.session)

    # ------------------------------------------------------------
    # position management — runs FIRST, never trapped (GP-14)
    # ------------------------------------------------------------
    def _manage(self, pos, journal, series, ind, ctx, now_dt,
                flat_dt, stamp):
        qty_signed = float(pos.get("qty") or 0)
        d = 1 if qty_signed > 0 else -1
        lot = journal.get("lot") if isinstance(
            journal.get("lot"), dict) else None
        stamp["position"] = {"qty": qty_signed, "direction": d,
                             "lot": bool(lot)}
        if lot is None:
            stamp["ownership_mismatch"] = True
        # GP-18: a position carried from a prior session is
        # exited on this pass, whatever else is true.
        held_from = str(pos.get("signal_date")
                        or pos.get("entry_date") or "")
        if not held_from and lot is not None:
            held_from = str(lot.get("session") or "")
        if held_from and held_from != ctx.session:
            stamp["carried_position"] = True
            stamp["state"] = "exited"
            stamp["decision"] = "exit_carried_flat"
            stamp["exit_rule"] = "carried_flat"
            return [self._exit_intent(qty_signed, "carried_flat", ctx)]
        # GP-8 session flat: a clock rule — fires even when
        # the bars door is absent.
        if now_dt >= flat_dt:
            stamp["state"] = "exited"
            stamp["decision"] = "exit_flat_close"
            stamp["exit_rule"] = "flat_close"
            return [self._exit_intent(qty_signed, "flat_close", ctx)]
        if lot is None:
            # Frozen levels unknown and never re-derived: the
            # position is managed on the session rules above
            # only (the saty_magnum unattributable posture).
            stamp["state"] = "holding"
            stamp["decision"] = "holding_unattributed"
            return []
        if not series:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: holding, no bars"
            return []
        last = len(series) - 1
        close = series[last][4]
        stop = float(lot["stop"])
        target = float(lot["target"])
        # bars held: entry bar is the bar after the signal bar,
        # so bars_held = last_idx - signal_idx (SPEC section 7).
        starts = [r[0] for r in series]
        bars_held = None
        sig_start = lot.get("signal_bar_start")
        if sig_start in starts:
            bars_held = last - starts.index(sig_start)
        elif lot.get("entry_bar_start") in starts:
            bars_held = last - starts.index(lot["entry_bar_start"]) + 1
        stamp["position"].update({
            "bars_held": bars_held, "stop": stop, "target": target,
            "anchor": lot.get("anchor"), "cluster_id": lot.get("cluster_id")})
        rule = None
        if d > 0:
            if close <= stop:
                rule = "stop"
            elif close >= target:
                rule = "target"
        else:
            if close >= stop:
                rule = "stop"
            elif close <= target:
                rule = "target"
        if rule is None and bars_held is not None and bars_held >= 1:
            # GP-6 slope reverse: the latest completed bar is
            # at/after the entry bar and its alignment (against
            # the position direction) is broken.
            s = (ind["sroc"][last], ind["sfast"][last],
                 ind["sslow"][last])
            if all(x is not None for x in s):
                broken = (any(x <= 0 for x in s) if d > 0
                          else any(x >= 0 for x in s))
                if broken:
                    rule = "slope_reverse"
        if rule is None and bars_held is not None \
                and bars_held >= MAX_HOLD_BARS:
            rule = "time"
        if rule is None:
            stamp["state"] = "holding"
            stamp["decision"] = "holding"
            return []
        stamp["state"] = "exited"
        stamp["decision"] = f"exit_{rule}"
        stamp["exit_rule"] = rule
        return [self._exit_intent(qty_signed, rule, ctx)]

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "raschke_pf3", "session": ctx.session,
                 "state": "idle", "decision": None,
                 "bars_completed": 0, "warmup_need": WARMUP_BARS,
                 "trend_filter": "off", "adx": None,
                 "slopes": None, "alignment": None,
                 "cluster_id": None, "position": None,
                 "stood_down": None}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        extra = ctx.extra or {}
        journal, rejected, _door = _journal(extra, slice_state)
        stamp["gpf3_journal"] = journal
        if rejected:
            stamp["journal_rejected"] = "fingerprint_mismatch"
        close_dt = session_close_dt(ctx.session)
        flat_dt = close_dt - timedelta(minutes=FLAT_BEFORE_CLOSE_MIN)
        cutoff_dt = close_dt - timedelta(
            minutes=CUTOFF_BEFORE_CLOSE_MIN)
        filter_on = _filter_on(extra)
        need = WARMUP_BARS_FILTER if filter_on else WARMUP_BARS
        stamp["trend_filter"] = "on" if filter_on else "off"
        stamp["warmup_need"] = need

        # bars: the shared long 5m SIP door, RTH completed only
        raw = None
        if isinstance(extra.get("bars_5m_long"), dict):
            raw = extra["bars_5m_long"].get(SYM)
        series, dup = _rth_series(raw, float(ctx.now)) \
            if raw is not None else ([], False)
        if dup:
            stamp["data_note"] = "duplicate_bar_dropped"
        stamp["bars_completed"] = len(series)
        ind = None
        if series:
            ind = indicators([r[4] for r in series],
                             [r[2] for r in series],
                             [r[3] for r in series])
            last = len(series) - 1
            stamp["slopes"] = {
                "roc2": ind["sroc"][last], "fast": ind["sfast"][last],
                "slow": ind["sslow"][last]}
            stamp["alignment"] = ind["alignment"][last]
            if filter_on and ind["adx"][last] is not None:
                stamp["adx"] = ind["adx"][last]
            for cl in clusters_of(ind["alignment"],
                                  [r[0] for r in series]):
                if cl["last"] == last:
                    stamp["cluster_id"] = cl["cluster_id"]

        # 1. position management first — never trapped
        pos = self._position(extra, slice_state)
        if pos is not None:
            return self._manage(pos, journal, series, ind, ctx,
                                now_dt, flat_dt, stamp)

        # 2. calendar
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            stamp["decision"] = "not_a_trading_day"
            return []

        # 3. entry proof: the journal door, or the fills
        # fallback; with neither, entries stand down (GP-15).
        fills = extra.get("session_fills")
        journal_present = isinstance(extra.get("gpf3_journal"), dict) \
            or (isinstance(slice_state, dict)
                and isinstance(slice_state.get("gpf3_journal"), dict))
        if not journal_present and fills is None:
            stamp["state"] = "blocked_data"
            stamp["decision"] = \
                "blocked_data: no journal or fills proof for entries"
            return []
        if not journal_present and fills is not None and any(
                f.get("position_intent") in
                ("buy_to_open", "sell_to_open") for f in fills):
            # fills-only mode: an entry fill this session means
            # its cluster is consumed, and fills alone cannot
            # name which cluster — no further entry is proven.
            stamp["stood_down"] = "fills_only_consumed_unknown"
            stamp["decision"] = "stood_down: fills_only_consumed_unknown"
            return []

        # 4. warmup fail-closed (GP-3)
        if raw is None:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no 5m history"
            return []
        if len(series) < need:
            stamp["state"] = "blocked_warmup"
            stamp["decision"] = \
                f"blocked_warmup: bars={len(series)} need={need}"
            return []

        # 5. entry: the latest completed bar must be a
        # cluster's first bar, of this session (GP-10/GP-17)
        last = len(series) - 1
        starts = [r[0] for r in series]
        clus = clusters_of(ind["alignment"], starts)
        cur = next((c for c in clus if c["first"] == last), None)
        if cur is None:
            stamp["decision"] = "no_signal"
            return []
        sig_start_dt = datetime.fromtimestamp(starts[last], tz=ET)
        if sig_start_dt.date().isoformat() != ctx.session:
            stamp["decision"] = "no_signal: cluster began prior session"
            return []
        cluster_id = cur["cluster_id"]
        stamp["cluster_id"] = cluster_id
        if cluster_id in (journal.get("consumed_clusters") or []):
            stamp["stood_down"] = "cluster_consumed"
            stamp["decision"] = "stood_down: cluster_consumed"
            return []
        sig_close_dt = sig_start_dt + timedelta(seconds=BAR_SECONDS)
        if sig_close_dt > cutoff_dt or now_dt >= flat_dt:
            stamp["stood_down"] = "entry_cutoff"
            stamp["decision"] = "stood_down: entry_cutoff"
            return []
        d = cur["direction"]
        if d < 0 and (ctx.market or {}).get("spy_shortable") is False:
            stamp["stood_down"] = "not_shortable"
            stamp["decision"] = "stood_down: not_shortable"
            return []
        if filter_on:
            adx = ind["adx"][last]
            stamp["adx"] = adx
            if adx is None or adx <= ADX_THRESHOLD:
                stamp["stood_down"] = "adx_filter"
                stamp["decision"] = \
                    f"stood_down: adx_filter adx={adx}"
                return []
        # 6. sizing (GP-12): zero is a journal-named no-trade
        atr = ind["atr"][last]
        qty, why = compute_qty(ctx.equity, atr)
        if qty < 1:
            journal["sizing_rejections"] = (
                journal.get("sizing_rejections") or []) + [{
                    "session": ctx.session, "cluster_id": cluster_id,
                    "reason": why, "equity": ctx.equity, "atr": atr}]
            stamp["gpf3_journal"] = journal
            stamp["decision"] = "sizing_zero_recorded"
            stamp["stood_down"] = why
            return []
        anchor = float(series[last][4])
        if d > 0:
            stop = anchor - STOP_MULT * atr
            target = anchor + TARGET_MULT * atr
            side, pi, word = "buy", "buy_to_open", "long"
        else:
            stop = anchor + STOP_MULT * atr
            target = anchor - TARGET_MULT * atr
            side, pi, word = "sell", "sell_to_open", "short"
        # consumed on emission (GP-10) + the frozen lot (GP-4)
        journal["consumed_clusters"] = (
            journal.get("consumed_clusters") or []) + [cluster_id]
        journal["lot"] = {
            "cluster_id": cluster_id, "direction": d,
            "anchor": anchor, "atr": atr, "stop": stop,
            "target": target, "signal_bar_start": starts[last],
            "entry_bar_start": starts[last] + BAR_SECONDS,
            "session": ctx.session}
        stamp["gpf3_journal"] = journal
        stamp["state"] = "entered"
        stamp["decision"] = f"enter_{word}"
        reason = (
            f"raschke_pf3 enter {word} cluster={cluster_id} "
            f"anchor={anchor:.2f} atr={atr:.2f} stop={stop:.2f} "
            f"target={target:.2f} qty={qty}")
        return [Intent(
            "enter", SYM, qty=int(qty), price_hint=anchor,
            stop=stop, target=target, side=side,
            position_intent=pi, reason=reason,
            signal_date=ctx.session)]


def signal(bars, slice_state, ctx):
    return RaschkePf3().signal(bars, slice_state, ctx)
