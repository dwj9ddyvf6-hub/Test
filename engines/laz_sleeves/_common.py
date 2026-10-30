"""Shared engine for Lazarus batch-7 sleeves (v3-native).

Snapshot view keys consumed (declared per sleeve in desk3/laz_batch7):
  bars          {"SYM|1Day"|"SYM|1Hour": [{t,o,h,l,c,v} ascending]}
  positions     [{symbol, qty, avg_price, opened_at, sleeve_id}]
  tensor_fires  {SYM: {"family": "swing"|"cyan"|"green", "date": ISO}}
                -- the desk's Tensor bundle producer output; substitutes
                for the unreachable external-research sleeve_fires_v1.json
                composer file (FIDELITY-LEDGER LAZ-B7).
  alt_data      {SYM: {insider_buys, wiki, gamma_low, ats_z, mcap_band}}
  midna_signals {SYM: {"signal": bool}} -- desk Tensor-bundle hourly
                signal product, Midna-rules lane (ledger substitution).
  hedge_signal  bool (QQQ hedge signal from the Midna signal product)
  vix           float (^VIX close, Yahoo price-only sanctioned route)
Intents are v3 dicts; sizing is whole shares from the lane's $ slot.
A sleeve never emits for another sleeve's positions.
"""
from __future__ import annotations
from datetime import date, datetime, timezone


def _session(view):
    now = str(view.get("now") or "")[:10]
    try:
        return date.fromisoformat(now)
    except ValueError:
        return None


def _bars(view, sym, tf):
    return (view.get("bars") or {}).get(f"{sym}|{tf}") or []


def _positions(view, sid):
    out = []
    for p in view.get("positions") or []:
        if p.get("sleeve_id") not in (None, sid):
            continue
        if float(p.get("qty") or 0) != 0:
            out.append(p)
    return out


def _sessions_held(bars, opened):
    """Trading sessions strictly after the open date present in bars."""
    if not opened:
        return 0
    od = str(opened)[:10]
    return sum(1 for b in bars if str(b.get("t"))[:10] > od)


def _bars_held(bars, opened_at):
    if not opened_at:
        return 0
    oa = str(opened_at)
    return sum(1 for b in bars if str(b.get("t")) > oa)


def _intent(sid, kind, sym, qty, price, reason, sess):
    side = "buy" if kind == "entry" else "sell"
    return {"intent_id": f"{sid}-{sym}-{sess.isoformat()}-{kind}",
            "kind": kind, "symbol": sym, "side": side, "qty": int(qty),
            "order_type": "market", "time_in_force": "day",
            "price_hint": float(price), "reason": reason}


EXP_ID_19 = "ENH19-LAZB7-20261024"
EXP_ID_20 = "ENH20-LAZB7-XSTALE-20261024"
EXP_ID_24 = "ENH24-LAZB7-Q07STALE-20261024"


def _enh24_on(view, sid, key):
    cfg = ((view.get("extra") or {}).get(f"{sid}_enh24") or {})
    return cfg.get(key, True) is not False


def _enh20_on(view, sid, key):
    cfg = ((view.get("extra") or {}).get(f"{sid}_enh20") or {})
    return cfg.get(key, True) is not False


def _bar_last_dt(b):
    if not b:
        return None
    t = b[-1].get("t")
    try:
        if isinstance(t, (int, float)):
            return datetime.fromtimestamp(float(t), tz=timezone.utc)
        return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except (TypeError, ValueError, OSError):
        return None


def _enh19_on(view, sid, key):
    cfg = ((view.get("extra") or {}).get(f"{sid}_enh19") or {})
    return cfg.get(key, True) is not False


def _journal19(view, rec):
    j = (view.get("extra") or {}).get("enh19_journal")
    if isinstance(j, list):
        j.append(rec)


def _bar_stale(view, sid, bars, sess, max_age_days=4):
    """True when the last decision bar is provably stale for `sess`
    (calendar age > max_age_days; Mon-after-Fri = 3d, Tue after a Mon
    holiday = 4d, both pass). Unparseable stamps never gate."""
    if not bars:
        return False
    try:
        bd = date.fromisoformat(str(bars[-1].get("t"))[:10])
    except (TypeError, ValueError):
        return False
    return (sess - bd).days > max_age_days


def _qty_for(slot_usd, price):
    if not price or price <= 0:
        return 0
    return int(slot_usd // price)


def _qqq_down(view):
    q = _bars(view, "QQQ", "1Day")
    return len(q) >= 2 and float(q[-1]["c"]) < float(q[-2]["c"])


def _mom6(closes):
    if len(closes) < 127:
        return None
    base = float(closes[-127])
    return (float(closes[-1]) / base - 1.0) if base > 0 else None


# ---------------------------------------------------------------- Q07
def q07_evaluate(view, ctx, sid, *, band, horizon_weeks, filters,
                 slots=1, slot_usd=1000.0):
    """Q07 family rule (catalog SS4.1): Tensor 1W Swing fire in the cap
    band + named alt-data filters; buy only on a QQQ-down day within 5
    sessions of the signal; exit on a 15% stop or at the horizon."""
    sess = _session(view)
    if sess is None:
        return []
    out, held = [], _positions(view, sid)
    horizon_sessions = horizon_weeks * 5
    held_syms = set()
    for p in held:
        sym = p["symbol"]
        held_syms.add(sym)
        bars = _bars(view, sym, "1Day")
        if not bars:
            continue
        last = float(bars[-1]["c"])
        entry = float(p.get("avg_price") or 0)
        if entry > 0 and last <= entry * 0.85:
            out.append(_intent(sid, "exit", sym, abs(float(p["qty"])), last,
                               "q07_stop15", sess))
        elif _sessions_held(bars, p.get("opened_at")) >= horizon_sessions:
            out.append(_intent(sid, "exit", sym, abs(float(p["qty"])), last,
                               "q07_time_horizon", sess))
    if len(held) >= slots or not _qqq_down(view):
        return out
    fires = view.get("tensor_fires") or {}
    alt = view.get("alt_data") or {}
    for sym in sorted(fires):
        if sym in held_syms:
            continue
        fire = fires[sym] or {}
        if fire.get("family") != "swing":
            continue
        try:
            age = (sess - date.fromisoformat(str(fire.get("date")))).days
        except (TypeError, ValueError):
            continue
        if age < 0 or age > 7:  # within 5 sessions of the signal
            continue
        tags = alt.get(sym) or {}
        if tags.get("mcap_band") != band:
            continue
        bars = _bars(view, sym, "1Day")
        if not bars:
            continue
        closes = [float(b["c"]) for b in bars]
        last = closes[-1]
        ok = True
        for f in filters:
            if f == "ins2":
                ok &= int(tags.get("insider_buys") or 0) >= 2
            elif f == "glow":
                ok &= tags.get("gamma_low") is True
            elif f == "wlow":
                ok &= tags.get("wiki") == "low"
            elif f == "ats_z1":
                ok &= float(tags.get("ats_z") or 0) >= 1.0
            elif f == "cheap5":
                ok &= last < 5.0
            elif f == "mom6":
                m = _mom6(closes)
                ok &= m is not None and m > 0
            elif f == "deep70":
                highs = [float(b["h"]) for b in bars[-252:]]
                ok &= bool(highs) and last <= 0.30 * max(highs)
            elif f == "vix20":
                vix = view.get("vix")
                ok &= vix is not None and float(vix) >= 20.0
        if not ok:
            continue
        # ENH24 binding leak: entries were priced/sized off the
        # symbol's last daily bar with no check of that bar's age --
        # a halted/delisted name whose feed died weeks earlier still
        # entered at the ancient close (filters deep70/mom6/cheap5
        # computed on the same dead print). ON (default): refuse the
        # entry when the last bar is >4 calendar days before the
        # session (_bar_stale; Mon-after-Fri = 3d, Tue after a Mon
        # holiday = 4d, both pass); paired shadow journal record.
        # Exits are never gated. OFF (extra {sid}_enh24.stale_gate
        # =False): pre-change rule exactly.
        if _bar_stale(view, sid, bars, sess):
            if _enh24_on(view, sid, "stale_gate"):
                _j = (view.get("extra") or {}).get("enh24_journal")
                if isinstance(_j, list):
                    try:
                        _bd = date.fromisoformat(str(bars[-1].get("t"))[:10])
                        _age = (sess - _bd).days
                    except (TypeError, ValueError):
                        _age = None
                    _j.append({"exp_id": EXP_ID_24, "sleeve": sid,
                               "symbol": sym,
                               "enhanced": "refuse_stale_bar_entry",
                               "shadow_faithful": "enter",
                               "bar_date": str(bars[-1].get("t"))[:10],
                               "age_days": _age})
                continue
        qty = _qty_for(slot_usd, last)
        if qty <= 0:
            continue
        out.append(_intent(sid, "entry", sym, qty, last,
                           "q07_" + "_".join(filters), sess))
        # ENH-Q07SLOT-20261024: pre-change the break test used the FIXED
        # held count, so with 0 held and slots=2 it never fired and the
        # sleeve entered EVERY passing fire (measured 3 entries against
        # a 2-slot / $2,000 book). ON (default): count entries already
        # emitted this pass (mirrors the ENH19 mn_hourly cure). OFF:
        # pre-change test exactly. Switch extra[f"{sid}_enh23"].slot_guard.
        _sg = ((view.get("extra") or {}).get(f"{sid}_enh23") or {})
        if _sg.get("slot_guard", True) is not False:
            _jr = (view.get("extra") or {}).get("enh23_journal")
            if isinstance(_jr, list):
                _jr.append({"exp_id": "ENH-Q07SLOT-20261024", "sleeve": sid,
                            "symbol": sym, "control_enter": True,
                            "treatment_enter":
                                len(held) + sum(1 for i in out
                                                if i["kind"] == "entry") <= slots})
            if len(held) + sum(1 for i in out if i["kind"] == "entry") >= slots:
                break
        elif len(held) + 1 >= slots:
            break
    return out


# ------------------------------------------------------------- Midna
def mn_hourly_evaluate(view, ctx, sid, *, stop, slots, slot_usd=1000.0,
                         time_bars=60):
    """Midna hourly Tensor-signal book: enter on the desk Tensor-bundle
    hourly signal; exit at the 15% stop (unless the no-stop variant)
    or after `time_bars` hourly bars."""
    sess = _session(view)
    if sess is None:
        return []
    out, held = [], _positions(view, sid)
    held_syms = set()
    for p in held:
        sym = p["symbol"]
        held_syms.add(sym)
        bars = _bars(view, sym, "1Hour")
        if not bars:
            continue
        last = float(bars[-1]["c"])
        entry = float(p.get("avg_price") or 0)
        if stop and entry > 0 and last <= entry * 0.85:
            out.append(_intent(sid, "exit", sym, abs(float(p["qty"])), last,
                               "mn_stop15", sess))
        elif _bars_held(bars, p.get("opened_at")) > time_bars:
            out.append(_intent(sid, "exit", sym, abs(float(p["qty"])), last,
                               "mn_time_bars", sess))
    if len(held) >= slots:
        return out
    signals = view.get("midna_signals") or {}
    # ENH20 binding leak (second look; ENH19 cured the slot count):
    # the hourly signal has no timestamp, so the sleeve priced/sized
    # entries off a symbol's last hourly bar even when that symbol's
    # feed stopped hours before the rest of the snapshot. ON
    # (default): refuse entry when the symbol's last 1Hour bar lags
    # the universe's latest by >4h; paired shadow journal record.
    # OFF (extra {sid}_enh20.xstale_gate=False): pre-change exactly.
    _lasts = {}
    for _s in signals:
        _dt = _bar_last_dt(_bars(view, _s, "1Hour"))
        if _dt is not None:
            _lasts[_s] = _dt
    _univ_last = max(_lasts.values()) if _lasts else None
    for sym in sorted(signals):
        if sym in held_syms or not (signals[sym] or {}).get("signal"):
            continue
        bars = _bars(view, sym, "1Hour")
        if not bars:
            continue
        if (_univ_last is not None and sym in _lasts
                and _enh20_on(view, sid, "xstale_gate")
                and (_univ_last - _lasts[sym]).total_seconds() > 4 * 3600):
            _j = (view.get("extra") or {}).get("enh20_journal")
            if isinstance(_j, list):
                _j.append({"exp_id": EXP_ID_20, "sleeve": sid,
                           "symbol": sym,
                           "enhanced": "refuse_xstale_entry",
                           "shadow_faithful": "enter",
                           "lag_hours": round((_univ_last - _lasts[sym]).total_seconds() / 3600.0, 2)})
            continue
        last = float(bars[-1]["c"])
        qty = _qty_for(slot_usd, last)
        if qty <= 0:
            continue
        out.append(_intent(sid, "entry", sym, qty, last, "mn_hourly_signal",
                           sess))
        # ENH19 slot-count cure: pre-change the break test used the
        # FIXED held count, so with <slots held it never fired and the
        # sleeve emitted one entry per signalled symbol (measured 15
        # entries into 12 slots = $15k against a $12k book). ON
        # (default): count entries already emitted this pass.
        if _enh19_on(view, sid, "slot_guard"):
            if len(held) + sum(1 for i in out if i["kind"] == "entry") >= slots:
                break
        elif len(held) + 1 >= slots:
            break
    return out
