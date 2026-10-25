"""Aster batch 15 — G4 Tensor green value/recovery (3) + timing (7).

Faithful sleeve-layer ports of the staged archive:
  source/backend/r19_tensor.py  (G4 passes/features thresholds, entry
    sessions, red_timeout wait, QQQ reserve, 52-week scheduled exit)
  source/backend/r19_timing.py  (hourly confirmed swing, EMA cloud
    reclaim, causal overnight) + strategies/r19/tensor/RULES.json books.

Tensor ENGINE untouched: G4 consumes Tensor weekly analysis as
`tensor_fires` (markers + feature fields computed by the desk Tensor
bundle); hourly consumes the v625 swing report as `timing_signals`.
No v3 producer emits `timing_signals` yet, so the hourly sleeves land
visibly UNFED rather than fake-fed. Cloud/overnight compute their
signals from bars at the sleeve layer exactly as the archive's
unprepared fallback path does.

Sizing is book-relative on the $10,000 slice (source books $100k):
G4 ticket $4,000 -> $400, slots 25; timing notional/risk fractions
apply to the slice. Paper only.
"""
from __future__ import annotations

import json
import math
import os
import statistics
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SLICE = 10000.0

UNIVERSE42 = ["AAOI", "AEHR", "AG", "ALAB", "ANF", "ARM", "ARQQ", "ASPI",
              "AXTI", "CLS", "CORZ", "CRDO", "CRML", "CVNA", "FCEL", "FFIV",
              "HIVE", "HUT", "IREN", "KEEL", "LASR", "LITE", "MU", "NBIS",
              "OKLO", "OUST", "POET", "SATL", "SHAZ", "SIVEF", "SKYQ",
              "SNDK", "SOXL", "TE", "TEM", "TSEM", "TTMI", "USAR", "VELO",
              "VRT", "WDC", "WYFI"]

G4_INPUTS = ("tensor_fires", "bars", "positions")
TIMING_INPUTS = ("bars", "positions", "quotes")
HOURLY_INPUTS = ("bars", "positions", "quotes", "timing_signals")

SPECS = {
    "aster_r19_tensor_g4_hot_delay_25": dict(
        family="G4", mode="delay", volatility="hot", slots=25,
        ticket=400.0, inputs=G4_INPUTS, cadence_s=86400),
    "aster_r19_tensor_g4_hot_reserve_25": dict(
        family="G4", mode="reserve", volatility="hot", slots=25,
        ticket=400.0, inputs=G4_INPUTS, cadence_s=86400),
    "aster_r19_tensor_g4_red_timeout_25": dict(
        family="G4", mode="red_timeout", volatility="all", slots=25,
        ticket=400.0, inputs=G4_INPUTS, cadence_s=86400),
    "aster_r19_timing_cloud_aggressive": dict(
        kind="cloud", risk=0.005, notional=0.2, fee_bps=5, slots=8,
        inputs=TIMING_INPUTS, cadence_s=300),
    "aster_r19_timing_cloud_base": dict(
        kind="cloud", risk=0.0025, notional=0.1, fee_bps=5, slots=8,
        inputs=TIMING_INPUTS, cadence_s=300),
    "aster_r19_timing_hour_floor0_delay0": dict(
        kind="hourly", floor=0, delay=0, risk=0.0025, notional=0.1,
        fee_bps=5, slots=8, inputs=HOURLY_INPUTS, cadence_s=300),
    "aster_r19_timing_hour_floor0_delay1": dict(
        kind="hourly", floor=0, delay=1, risk=0.0025, notional=0.1,
        fee_bps=5, slots=8, inputs=HOURLY_INPUTS, cadence_s=300),
    "aster_r19_timing_hour_floor1_delay0": dict(
        kind="hourly", floor=1, delay=0, risk=0.0025, notional=0.1,
        fee_bps=5, slots=8, inputs=HOURLY_INPUTS, cadence_s=300),
    "aster_r19_timing_hour_floor1_delay1": dict(
        kind="hourly", floor=1, delay=1, risk=0.0025, notional=0.1,
        fee_bps=5, slots=8, inputs=HOURLY_INPUTS, cadence_s=300),
    "aster_r19_timing_overnight_25bp": dict(
        kind="overnight", risk=0.0025, notional=0.1, fee_bps=25, slots=8,
        inputs=TIMING_INPUTS, cadence_s=300),
}
# floor0_delay1 spec written plainly (avoid cleverness drift):
SPECS["aster_r19_timing_hour_floor0_delay1"]["floor"] = 0

PRODUCERS = (
    {"name": "tensor_bundle", "outputs": ("tensor_fires",),
     "freshness_sla_s": 93600},
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
    {"name": "broker_readback", "outputs": ("positions",),
     "freshness_sla_s": 900},
    {"name": "quotes", "outputs": ("quotes",), "freshness_sla_s": 60},
)


# --- EDGE BATCH 9 enhancement: execution-window grace -----------------
# Binding leak: G4 entries were executable only 09:30-09:35 ET and
# cloud/hourly timing entries only within 5 min of actionable_at, while
# their cadences are 86400s (G4) / 300s (timing) — a single delayed or
# wedged cycle silently killed the trade (G4 pending then expired
# unfilled next session). Cure (switches enhance_window_grace /
# enhance_actionable_grace, default ON): G4 window extends to 10:30 ET
# and timing actionable window to 15 min, with every pre-existing
# price guard (stop<bid<=price<target, cloud 2R) re-checked at the
# actual entry moment, so a stale signal whose geometry died still
# refuses. OFF restores the 09:35 / 5-minute rules exactly.
def _enh_on(view, ctx, key):
    sid = (ctx or {}).get("sleeve_id") if isinstance(ctx, dict) else None
    for src in ((ctx or {}) if isinstance(ctx, dict) else {},
                (view or {}).get("params") or {},
                (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            sub = src.get(sid) if sid and isinstance(src.get(sid), dict) else src
            if isinstance(sub, dict) and key in sub:
                return bool(sub[key])
    return True


def _enh_journal(ctx, sid, rec):
    sd = (ctx or {}).get("state_dir") if isinstance(ctx, dict) else None
    if not sd:
        return
    try:
        os.makedirs(sd, exist_ok=True)
        with open(os.path.join(sd, "enhance_journal.jsonl"), "a") as fh:
            fh.write(json.dumps({"sleeve": sid, **rec}, sort_keys=True) + "\n")
    except Exception:
        pass


def config_rows():
    rows = []
    for sid, spec in SPECS.items():
        rows.append({
            "id": sid, "module": f"adapters3.{sid}",
            "cadence_s": spec["cadence_s"], "session": "rth",
            "slice": {"capital_usd": SLICE, "cash_usd": SLICE},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None, "params": {},
            "inputs": list(spec["inputs"]), "parked": False,
        })
    return rows


# ---------------------------------------------------------------- helpers
def _now(view, ctx):
    raw = (view or {}).get("now") or (ctx or {}).get("now")
    if raw:
        if isinstance(raw, datetime):
            d = raw
        else:
            d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _parse_ts(raw):
    if not raw:
        return None
    try:
        d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _bars(view, sym, tf):
    m = (view or {}).get("bars") or {}
    for k in (f"{sym}|{tf}", sym):
        if m.get(k):
            return m[k]
    return []


def _bar_end(bar, minutes):
    e = _parse_ts(bar.get("end"))
    if e:
        return e
    t = _parse_ts(bar.get("t"))
    return t + timedelta(minutes=minutes) if t else None


def _quote(view, sym, side):
    q = ((view or {}).get("quotes") or {}).get(sym) or {}
    v = q.get("ask" if side == "buy" else "bid")
    try:
        return float(v) if v else None
    except Exception:
        return None


def _last_close(view, sym, tf="1Day"):
    rows = _bars(view, sym, tf)
    if rows:
        try:
            return float(rows[-1]["c"])
        except Exception:
            return None
    return None


def _sessions(view):
    dates = ((view or {}).get("extra") or {}).get("session_dates") or []
    if not dates:
        seen = set()
        for sym in ("SPY", "QQQ"):
            for r in _bars(view, sym, "1Day"):
                if r.get("t"):
                    seen.add(str(r["t"])[:10])
        dates = sorted(seen)
    return [str(d)[:10] for d in dates]


def _state_path(ctx):
    sd = (ctx or {}).get("state_dir")
    return os.path.join(sd, "aster_batch15_state.json") if sd else None


def _load_state(ctx, sid):
    p = _state_path(ctx)
    if p and os.path.exists(p):
        try:
            return (json.load(open(p)).get(sid) or {})
        except Exception:
            return {}
    return {}


def _save_state(ctx, sid, st):
    p = _state_path(ctx)
    if not p:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    allst = {}
    if os.path.exists(p):
        try:
            allst = json.load(open(p))
        except Exception:
            allst = {}
    allst[sid] = st
    with open(p, "w") as fh:
        json.dump(allst, fh, sort_keys=True)


def _intent(sid, stamp, n, kind, sym, qty, reason, price=None,
            stop=None, target=None):
    # dispatcher kind vocabulary is entry/exit (desk3/models.py)
    kind = "entry" if kind == "enter" else kind
    return {"intent_id": f"{sid}-{stamp}-{kind}-{n}", "kind": kind,
            "symbol": sym, "side": "buy" if kind == "entry" else "sell",
            "qty": qty, "order_type": "market", "limit_price": None,
            "stop_price": None, "reason": reason, "time_in_force": "day",
            "position_intent": "buy_to_open" if kind == "entry"
            else "sell_to_close",
            "price_hint": price, "stop": stop, "target": target}


# --- ENH (Edge IMPROVE batch 10, 2026-10-24): mid-price limit entry for
# aster_r19_timing_overnight_25bp ONLY (other batch-15 sleeves keep the
# pre-change execution). Binding leak: the sleeve crosses the full ask
# at 15:30 ET and the full bid at the next open on an ~18h hold whose
# entire edge is a 25bp-class overnight move — spread paid twice can
# exceed the signal's expected capture. Treatment: entry limit at the
# quoted mid. Switch: extra["enh_aster_r19_timing_overnight_25bp"] or
# extra["aster_b15_enh"] {"mid_limit": bool}, default ON; OFF restores
# the market order exactly. Shadow control = the ask the pre-change
# rule would have paid, recorded paired on the intent + journal.
EXP_ID_B15 = "ENH-ASTERB15-MIDLIMIT-20261024"

def _enh_on_b15(view, sid):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b15_enh")
    if isinstance(ov, dict) and "mid_limit" in ov:
        return bool(ov["mid_limit"])
    return True

def _paired_b15(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)

# --- ENH (Edge batch 26, 2026-10-24): mid-price limit for the
# SCHEDULED time exit of aster_r19_timing_overnight_5bp ONLY (the
# 25bp book's exit was named the next leak candidate by batch 10's
# ENH-ASTERB15-MIDLIMIT record; this batch owns the 5bp book, whose
# entire edge is a 5bp-fee overnight capture — crossing the full
# bid at the 09:30 exit pays the spread a second time on the
# thinnest book). Treatment: the scheduled exit (never stop/target
# exits, which keep immediacy) is a limit at the quoted mid; an
# unfilled limit is re-emitted at the next cycle's fresh mid by
# the same exit loop, exactly as the market exit was. Switch:
# extra["enh_aster_r19_timing_overnight_5bp"] or
# extra["aster_b26_enh"] {"exit_mid_limit": bool}, default ON;
# OFF restores the market exit exactly. Shadow control = the bid
# the pre-change market exit would have received.
EXP_ID_B26_ON = "ENH-B26-ONEXIT-20261024"

def _enh_on_exit_mid(view, sid):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b26_enh")
    if isinstance(ov, dict) and "exit_mid_limit" in ov:
        return bool(ov["exit_mid_limit"])
    return True

def _fee_bps_price(price):
    # archive r19_tensor.fee_bps(price) — G4 fill-fee schedule
    return 30 if price < 5 else 15 if price < 20 else 10


# ---------------------------------------------------------------- G4
def g4_passes(spec, f):
    """Archive r19_tensor.passes() for family G4 + the dv20 gate."""
    if not f:
        return False
    try:
        markers = f.get("markers") or f.get("primaryMarkers") or []
        return bool(
            "buy-green" in markers
            and float(f["native_close"]) <= 10
            and float(f["depth60"]) >= 70
            and float(f["ret60"]) >= 0
            and float(f["vol20"]) >= 0.09
            and float(f["dv20"]) >= 2e6
            and (spec["volatility"] == "all"
                 or (float(f["atr_ratio"]) <= 1)
                 == (spec["volatility"] == "cool")))
    except (KeyError, TypeError, ValueError):
        return False


def _exit_session_date(sessions, entry_date):
    """Last session of the week 51 weeks after the entry week
    (archive exit_session: week = entry-week Monday + 51 weeks)."""
    monday = entry_date - timedelta(days=entry_date.weekday())
    week = monday + timedelta(weeks=51)
    rows = [d for d in sessions
            if week <= date.fromisoformat(d) < week + timedelta(days=7)]
    if not rows:
        return None
    if not any(date.fromisoformat(d) >= week + timedelta(days=7)
               for d in sessions):
        return None  # calendar incomplete past target week (archive rule)
    return rows[-1]


def _eval_g4(sid, spec, view, ctx):
    now = _now(view, ctx)
    et = now.astimezone(ET)
    today = et.date().isoformat()
    sessions = _sessions(view)
    state = _load_state(ctx, sid)
    pending = state.setdefault("pending", {})
    seen = state.setdefault("seen", {})
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    pos_by_sym = {p["symbol"]: p for p in positions}
    _c = (view.get("slice") or {}).get("cash_usd")
    cash = SLICE if _c is None else float(_c)
    out = []
    n = 0
    stamp = now.strftime("%Y%m%dT%H%M%S")

    # ---- exits first: 52-week scheduled exit (the only G4 exit) ----
    for p in positions:
        sym = p["symbol"]
        if sym == "QQQ" and spec["mode"] == "reserve":
            continue  # reserve asset; sold only by the funding rule
        opened = _parse_ts(p.get("opened_at"))
        if not opened or not sessions:
            continue
        xd = _exit_session_date(sessions, opened.astimezone(ET).date())
        if xd and today >= xd:
            n += 1
            out.append(_intent(sid, stamp, n, "exit", sym,
                               abs(float(p["qty"])),
                               f"{sid} exit: 52_week_scheduled_exit",
                               _last_close(view, sym)))
    if out:
        _save_state(ctx, sid, state)
        return out

    if not sessions:
        return []  # no calendar => entries refuse (never invent sessions)

    # pending housekeeping: filled -> owned; window passed -> expired
    for key in list(pending):
        c = pending[key]
        if c["symbol"] in pos_by_sym:
            seen[key] = "owned"
            pending.pop(key)
        elif c.get("entry_date") and today > c["entry_date"]:
            seen[key] = "expired_unfilled"
            pending.pop(key)
        elif c.get("wait_expires") and today > c["wait_expires"]:
            seen[key] = "expired_unfilled"
            pending.pop(key)

    # ---- new candidates from Tensor fires ----
    fires = view.get("tensor_fires") or \
        ((view.get("extra") or {}).get("tensor_fires")) or []
    held_issuers = {p.get("issuer_id") for p in positions
                    if p["symbol"] != "QQQ"}
    occupied = sum(1 for p in positions if p["symbol"] != "QQQ")
    cands = []
    for f in fires:
        if not isinstance(f, dict):
            continue
        sym = f.get("symbol")
        if not sym or not g4_passes(spec, f):
            continue
        end = str(f.get("signal_end") or "")[:10]
        if not end:
            continue
        key = f"{sid}:{f.get('issuer_id') or sym}:{end}"
        if key in seen or key in pending:
            continue
        cands.append((key, sym, f, end))
    cands.sort(key=lambda x: (-float(x[2]["dv20"]), x[1]))
    for key, sym, f, end in cands:
        if sym in pos_by_sym or (f.get("issuer_id")
                                 and f.get("issuer_id") in held_issuers):
            seen[key] = "issuer_already_owned"
            continue
        if occupied + len(pending) >= spec["slots"]:
            seen[key] = "slot_limit"
            continue
        following = [d for d in sessions if d > end]
        if spec["mode"] in ("delay", "reserve"):
            if len(following) < 2:
                continue
            entry_date = following[1]
            base_date = following[0]
        elif spec["mode"] == "red_timeout":
            if len(following) < 6:
                continue
            entry_date = None
            base_date = following[0]
        else:
            if not following:
                continue
            entry_date = following[0]
            base_date = following[0]
        rec = {"symbol": sym, "issuer_id": f.get("issuer_id"),
               "signal_end": end, "signal_close": float(f["native_close"]),
               "entry_date": entry_date, "base_date": base_date}
        if spec["mode"] == "red_timeout":
            rec["wait_sessions"] = following[:6]
            rec["wait_expires"] = following[5]
        pending[key] = rec

    _grace = _enh_on(view, ctx, "enhance_window_grace")
    in_entry_window = et.time() >= time(9, 30) and \
        et.time() < (time(10, 30) if _grace else time(9, 35))
    _grace_entry = _grace and et.time() >= time(9, 35)

    # ---- red_timeout trigger scan ----
    if spec["mode"] == "red_timeout":
        qbars = {str(r.get("t"))[:10]: r
                 for r in _bars(view, "QQQ", "1Day")}
        qdates = sorted(qbars)
        for key, c in pending.items():
            if c.get("entry_date"):
                continue
            dbars = {str(r.get("t"))[:10]: r
                     for r in _bars(view, c["symbol"], "1Day")}
            for i, sess in enumerate(c["wait_sessions"][:5]):
                b = dbars.get(sess)
                qb = qbars.get(sess)
                if not b or not qb:
                    break
                prior = [d for d in qdates if d < sess]
                if not prior:
                    break
                red = float(qb["c"]) < float(qbars[prior[-1]]["c"]) \
                    and float(b["c"]) <= 1.02 * c["signal_close"]
                if red or i == 4:
                    nxt = [d for d in sessions if d > sess]
                    if nxt:
                        c["entry_date"] = nxt[0]
                        c["wait_trigger"] = "red" if red else "timeout"
                    break

    # ---- reserve funding sale (day before delayed entry) ----
    if spec["mode"] == "reserve":
        sale_day = [c for c in pending.values()
                    if c.get("entry_date") == _next_session(sessions, today)
                    and c.get("base_date") == today]
        qqq = pos_by_sym.get("QQQ")
        if sale_day and qqq and in_entry_window:
            price = _quote(view, "QQQ", "sell") or \
                _last_close(view, "QQQ")
            if price:
                shortage = max(0.0, len(sale_day) * spec["ticket"] - cash)
                units = min(int(float(qqq["qty"])),
                            math.ceil(shortage / (price * 0.999))
                            if shortage > 0 else 0)
                targets = state.setdefault("funding_targets", {})
                fund_key = "fund:" + ",".join(sorted(
                    k for k, c in pending.items() if c in sale_day))
                if units > 0 and fund_key not in targets:
                    targets[fund_key] = int(float(qqq["qty"])) - units
                if fund_key in targets and \
                        int(float(qqq["qty"])) > targets[fund_key]:
                    n += 1
                    out.append(_intent(
                        sid, stamp, n, "exit", "QQQ",
                        int(float(qqq["qty"])) - targets[fund_key],
                        f"{sid} exit: reserve_ticket_funding_wait_T1",
                        price))
                    _save_state(ctx, sid, state)
                    return out

    # ---- entries at the entry session open window ----
    if in_entry_window:
        for key, c in list(pending.items()):
            if c.get("entry_date") != today:
                continue
            if occupied + sum(1 for o in out if o["kind"] == "entry") \
                    >= spec["slots"]:
                break
            price = _quote(view, c["symbol"], "buy") or \
                _last_close(view, c["symbol"])
            if not price or price <= 0:
                continue
            fee = _fee_bps_price(price) / 1e4
            units = math.floor(min(spec["ticket"], cash)
                               / (price * (1 + fee)))
            if units <= 0:
                continue
            n += 1
            out.append(_intent(sid, stamp, n, "enter", c["symbol"], units,
                               f"{sid} entry: frozen_weekly_G4 mode="
                               f"{spec['mode']}", price))
            if _grace_entry:
                _enh_journal(ctx, sid, {"event": "enhance_entry",
                    "enhanced": "entry_in_grace_window",
                    "shadow": "no_entry_window_expired_0935",
                    "symbol": c["symbol"], "ts": now.isoformat()})
            cash -= units * price * (1 + fee)
            c["target_quantity"] = units

    # ---- reserve weekly idle-cash QQQ purchase ----
    if spec["mode"] == "reserve" and not pending and not out \
            and in_entry_window:
        monday = et.date() - timedelta(days=et.date().weekday())
        week = monday.isoformat()
        first = [d for d in sessions
                 if monday <= date.fromisoformat(d)
                 < monday + timedelta(days=7)]
        if first and today == first[0] \
                and state.get("reserve_week") != week:
            order = state.get("reserve_order")
            if order:
                if "QQQ" in pos_by_sym:
                    state["reserve_week"] = order["week"]
                    state.pop("reserve_order", None)
                elif today > order["week"]:
                    state["reserve_week"] = order["week"]
                    state.pop("reserve_order", None)
            if state.get("reserve_week") != week \
                    and "reserve_order" not in state:
                price = _quote(view, "QQQ", "buy") or \
                    _last_close(view, "QQQ")
                if price and cash > 0:
                    units = math.floor(cash / (price * 1.001))
                    if units > 0:
                        n += 1
                        out.append(_intent(
                            sid, stamp, n, "enter", "QQQ", units,
                            f"{sid} entry: weekly_idle_cash_reserve",
                            price))
                        state["reserve_order"] = {"week": week}
                    else:
                        state["reserve_week"] = week
    _save_state(ctx, sid, state)
    return out


def _next_session(sessions, day):
    nxt = [d for d in sessions if d > day]
    return nxt[0] if nxt else None


# ---------------------------------------------------------------- timing
def _ema(xs, n):
    out = [float(xs[0])]
    a = 2 / (n + 1)
    for x in xs[1:]:
        out.append(out[-1] + a * (float(x) - out[-1]))
    return out


def _atr14_seed(bars):
    win = bars[-14:]
    if len(win) < 14:
        raise ValueError("atr_warmup")
    a = [win[0]["h"] - win[0]["l"]] + [
        max(x["h"] - x["l"], abs(x["h"] - win[i - 1]["c"]),
            abs(x["l"] - win[i - 1]["c"]))
        for i, x in enumerate(win) if i > 0]
    if min(a) <= 0:
        raise ValueError("nonpositive_source_atr")
    return statistics.mean(a)


def _rma_atr(bars, n=14):
    tr = [max(x["h"] - x["l"],
              abs(x["h"] - (bars[i - 1]["c"] if i else x["c"])),
              abs(x["l"] - (bars[i - 1]["c"] if i else x["c"])))
          for i, x in enumerate(bars)]
    if len(tr) < n:
        raise ValueError("atr_warmup")
    a = statistics.mean(tr[:n])
    for x in tr[n:]:
        a += (x - a) / n
    return a


def hourly_signal(bars, spec, swing):
    """Archive r19_timing.hourly_signal with the v625 swing report
    supplied as an input (Tensor engine product, not recomputed)."""
    delay = spec["delay"]
    i = len(bars) - 1 - delay
    if i < 59:
        return None
    s = (swing or {}).get("swing") or {}
    if not s.get("confirmed") or s.get("usesFutureData") \
            or (s.get("score") or 0) < 8 or s.get("bearishConflict"):
        return None
    window = bars[:i + 1]
    last = window[-1]
    entry = float(last["c"])
    stop, target = s.get("invalidation"), s.get("target")
    if stop is None or target is None \
            or not (float(stop) < entry < float(target)):
        return None
    atr = _atr14_seed(window)
    if str(s.get("phenotype", "")).upper() == "TRANSITION" and (
            (entry - float(last["o"])) / atr > 0.5
            or (float(last["h"]) - float(last["l"])) / atr > 1.5):
        return None
    if any(float(x["l"]) <= float(stop) or float(x["h"]) >= float(target)
           for x in bars[i + 1:]):
        return None
    floorstop = min(float(stop), entry - spec["floor"] * atr)
    return {"signal_end": _bar_end(last, 60),
            "actionable_at": _bar_end(bars[-1], 60), "stop": floorstop,
            "target": float(target), "original_stop": float(stop),
            "deadline_bars": 20, "atr": atr}


def cloud_signal(ten, hour, prior_high):
    """Archive r19_timing.cloud_signal, verbatim logic."""
    hc = [float(x["c"]) for x in hour]
    if len(hour) < 53:
        return None
    a, b = _ema(hc, 34), _ema(hc, 50)
    if not all(a[i] > b[i] for i in range(len(a) - 3, len(a))):
        return None
    if len(ten) < 30:
        return None
    c = [float(x["c"]) for x in ten]
    e5, e12 = _ema(c, 5), _ema(c, 12)
    for start in range(max(15, len(ten) - 3), len(ten)):
        lower, upper = sorted((e5[start - 1], e12[start - 1]))
        prior = ten[start - 1]
        if float(prior["l"]) <= upper or float(ten[start]["l"]) > upper \
                or float(ten[start]["h"]) < lower:
            continue
        atr = _rma_atr(ten[:start])
        episode = ten[start:]
        if len(episode) > 3 or \
                min(float(x["l"]) for x in episode) < lower - 0.5 * atr:
            continue
        if float(ten[-1]["c"]) <= upper \
                or e5[-1] - e12[-1] <= e5[-2] - e12[-2]:
            continue
        if any(float(x["c"]) > upper
               and e5[j] - e12[j] > e5[j - 1] - e12[j - 1]
               for j, x in enumerate(ten[start:-1], start)):
            continue
        return {"signal_end": _bar_end(ten[-1], 10),
                "stop": min(float(x["l"]) for x in episode) - 0.1 * atr,
                "target": float(prior_high), "atr": atr,
                "deadline_minutes": 100}
    return None


def overnight_signal(bars, sessions, now):
    """Archive r19_timing.overnight_signal: 12:30->14:30 ET 30m return
    at/above the 80th percentile of the prior 126+ sessions."""
    et_now = now.astimezone(ET)
    day = et_now.date().isoformat()
    full = {d for d in sessions
            if date.fromisoformat(d).weekday() < 5}
    # archive gates on sessions whose close is 16:00 ET; the v3 session
    # list carries regular sessions only (documented in the ledger).
    if day not in full:
        return None
    rows = {}
    for b in bars:
        t = _parse_ts(b.get("t"))
        if not t:
            continue
        te = t.astimezone(ET)
        rows[(te.date().isoformat(), te.strftime("%H:%M"))] = b
    hist = []
    current = None
    for d in sorted(full):
        if d > day:
            break
        a, b = rows.get((d, "12:30")), rows.get((d, "14:30"))
        if not a or not b:
            continue
        r = float(b["c"]) / float(a["c"]) - 1
        if d == day:
            current = (r, b)
        else:
            hist.append(r)
    if current is None or len(hist) < 126:
        return None
    values = sorted(hist[-252:])
    k = (len(values) - 1) * 0.8
    lo, hi = math.floor(k), math.ceil(k)
    threshold = values[lo] + (values[hi] - values[lo]) * (k - lo)
    if current[0] < threshold:
        return None
    end = _bar_end(current[1], 30)
    nxt = _next_session(sessions, day)
    if not nxt:
        return None
    exit_at = datetime.combine(date.fromisoformat(nxt), time(9, 30),
                               ET)
    return {"signal_end": end,
            "actionable_at": end + timedelta(minutes=30),
            "exit_at": exit_at, "threshold": threshold,
            "return13to15": current[0], "history_count": len(values)}


def _eval_timing(sid, spec, view, ctx):
    now = _now(view, ctx)
    et = now.astimezone(ET)
    sessions = _sessions(view)
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    _c = (view.get("slice") or {}).get("cash_usd")
    cash = SLICE if _c is None else float(_c)
    out = []
    n = 0
    stamp = now.strftime("%Y%m%dT%H%M%S")
    kind = spec["kind"]

    # ---- exits first (archive: witnessed bid vs stop/target, then
    # scheduled time exit, then the 20-bar hourly deadline) ----
    for p in positions:
        sym = p["symbol"]
        meta = p.get("meta") or {}
        stop = p.get("stop", meta.get("stop"))
        target = p.get("target", meta.get("target"))
        exit_at = _parse_ts(p.get("exit_at") or meta.get("exit_at"))
        bid = _quote(view, sym, "sell")
        if bid is None:
            tf = "1Hour" if kind == "hourly" else \
                "10Min" if kind == "cloud" else "30Min"
            bid = _last_close(view, sym, tf)
        reason = None
        if stop is not None and bid is not None and bid <= float(stop):
            reason = "observed_stop_trigger"
        elif target is not None and bid is not None \
                and bid >= float(target):
            reason = "observed_target"
        elif exit_at and now >= exit_at:
            reason = "scheduled_time_exit"
        elif kind == "hourly" and meta.get("signal_end"):
            send = _parse_ts(meta["signal_end"])
            bars = _bars(view, sym, "1Hour")
            cnt = sum(1 for x in bars
                      if _bar_end(x, 60) and send
                      and _bar_end(x, 60) > send)
            if cnt >= int(meta.get("deadline_bars") or 20):
                reason = "original_20_native_bar_deadline"
        if reason:
            n += 1
            it = _intent(sid, stamp, n, "exit", sym,
                         abs(float(p["qty"])),
                         f"{sid} exit: {reason}", bid)
            if reason == "scheduled_time_exit" and kind == "overnight" \
                    and sid == "aster_r19_timing_overnight_5bp" \
                    and _enh_on_exit_mid(view, sid):
                q = ((view or {}).get("quotes") or {}).get(sym) or {}
                try:
                    qb, qa = float(q.get("bid") or 0), float(q.get("ask") or 0)
                except Exception:
                    qb = qa = 0.0
                if qa >= qb > 0:
                    mid = (qa + qb) / 2
                    rec = {"exp_id": EXP_ID_B26_ON, "sleeve": sid,
                           "kind": "exit", "switch_on": True,
                           "control_price": qb,
                           "treatment_limit": round(mid, 4),
                           "spread_saved": round(mid - qb, 4)}
                    it["order_type"] = "limit"
                    it["limit_price"] = round(mid, 2)
                    it["enhance_exp"] = rec
                    _paired_b15(view, rec)
            out.append(it)
    if out:
        return out

    # ---- entry windows (archive clocks, ET) ----
    clock = et.time()
    if kind == "cloud" and not (time(9, 50) <= clock <= time(15, 30)):
        return []
    if kind == "overnight" and not (time(15, 30) <= clock < time(15, 35)):
        return []

    held = {p["symbol"] for p in positions}
    signals = view.get("timing_signals") or {}
    for sym in UNIVERSE42:
        if sym in held:
            continue
        if len(held) + sum(1 for o in out if o["kind"] == "entry") \
                >= spec["slots"]:
            break
        sig = None
        _grace_sig = False
        if kind == "hourly":
            bars = _bars(view, sym, "1Hour")
            if len(bars) < 60 + spec["delay"]:
                continue
            sig = hourly_signal(bars, spec, signals.get(sym))
            if not sig:
                continue
            act = sig["actionable_at"]
            _win = 15 if _enh_on(view, ctx, "enhance_actionable_grace") else 5
            if not (act <= now < act + timedelta(minutes=_win)):
                continue
            _grace_sig = now >= act + timedelta(minutes=5)
        elif kind == "cloud":
            ten = _bars(view, sym, "10Min")
            hour = _bars(view, sym, "1Hour")
            if len(ten) < 30 or len(hour) < 53:
                continue
            tend = _bar_end(ten[-1], 10)
            hour = [x for x in hour
                    if _bar_end(x, 60) and _bar_end(x, 60) <= tend]
            daily = _bars(view, sym, "1Day")
            prior = [r for r in daily
                     if str(r.get("t"))[:10] < et.date().isoformat()]
            if not prior:
                continue
            sig = cloud_signal(ten, hour, float(prior[-1]["h"]))
            if not sig:
                continue
            act = sig["signal_end"]
            _win = 15 if _enh_on(view, ctx, "enhance_actionable_grace") else 5
            if not (act <= now < act + timedelta(minutes=_win)):
                continue
            _grace_sig = now >= act + timedelta(minutes=5)
        else:  # overnight
            bars = _bars(view, sym, "30Min")
            if len(bars) < 252:
                continue
            sig = overnight_signal(bars, sessions, now)
            if not sig:
                continue
            act = sig["actionable_at"]
            if not (act <= now < act + timedelta(minutes=5)):
                continue
        price = _quote(view, sym, "buy")
        if price is None:
            tf = "1Hour" if kind == "hourly" else \
                "10Min" if kind == "cloud" else "30Min"
            price = _last_close(view, sym, tf)
        if not price or price <= 0:
            continue
        stop = sig.get("stop")
        target = sig.get("target")
        if stop is not None and target is not None:
            bid = _quote(view, sym, "sell") or price
            if not (float(stop) < bid <= price < float(target)):
                continue
        if kind == "cloud" and stop is not None and target is not None \
                and (float(target) - price) < 2 * (price - float(stop)):
            continue  # archive: target_less_than_two_actual_risk
        fee = spec["fee_bps"] / 1e4
        budget = min(cash, SLICE * spec["notional"])
        qty = math.floor(budget / (price * (1 + fee)))
        if stop is not None:
            qty = min(qty, math.floor(SLICE * spec["risk"]
                                      / (price - float(stop))))
        if qty <= 0:
            continue
        meta_exit = None
        if kind == "cloud":
            forced = datetime.combine(et.date(), time(15, 50), ET)
            meta_exit = min(now + timedelta(minutes=100), forced)
            if meta_exit <= now:
                continue
        elif kind == "overnight":
            meta_exit = sig["exit_at"]
        n += 1
        it = _intent(sid, stamp, n, "enter", sym, qty,
                     f"{sid} entry: {kind}_qualified_actual_quote",
                     price, stop=float(stop) if stop is not None else None,
                     target=float(target) if target is not None else None)
        if kind == "overnight" and _enh_on_b15(view, sid):
            q = ((view.get("quotes") or {}).get(sym) or {})
            try:
                qb, qa = float(q.get("bid") or 0), float(q.get("ask") or 0)
            except Exception:
                qb = qa = 0.0
            if qa >= qb > 0:
                mid = (qa + qb) / 2
                rec = {"exp_id": EXP_ID_B15, "sleeve": sid,
                       "kind": "entry", "switch_on": True,
                       "control_price": qa,
                       "treatment_limit": round(mid, 4),
                       "spread_saved": round(qa - mid, 4)}
                it["order_type"] = "limit"
                it["limit_price"] = round(mid, 2)
                it["enhance_exp"] = rec
                _paired_b15(view, rec)
        if meta_exit:
            it["exit_at"] = meta_exit.isoformat()
        if kind == "hourly":
            it["signal_end"] = sig["signal_end"].isoformat()
            it["deadline_bars"] = sig["deadline_bars"]
        out.append(it)
        if _grace_sig:
            _enh_journal(ctx, sid, {"event": "enhance_entry",
                "enhanced": "entry_in_actionable_grace_window",
                "shadow": "no_entry_actionable_window_expired_5m",
                "symbol": sym, "ts": now.isoformat()})
        cash -= qty * price * (1 + fee)
    return out


def evaluate(sleeve_id, view, ctx=None):
    spec = SPECS[sleeve_id]
    view = view or {}
    ctx = ctx or {}
    if spec.get("family") == "G4":
        return _eval_g4(sleeve_id, spec, view, ctx)
    return _eval_timing(sleeve_id, spec, view, ctx)
