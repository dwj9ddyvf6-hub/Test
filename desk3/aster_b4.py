"""Aster batch 4 engine — recovery VWAP20 vertical (x4), XSP put-credit
spread (x4), public_recipe spot (LINK ai_volume, ENJ iu_body).

Faithful port of the staged archive sources:
- recovery: source/backend/r19_options.py::recovery_signal (VWAP20 arm:
  200 completed sessions, close > SMA200 and close <= 0.98 * VWAP20 of
  typical price over the last 20 sessions) + options_rules.json books
  OPT_VWAP20_VERTICAL_{FIXED,TOUCH}_{A,B}; contract selection / sizing /
  exits reuse the batch-2 engine (desk3/aster_b2.py), itself a port of
  the same archive functions (_select_contracts, _entry_intent,
  _exit_intents: planned hold_sessions=5 exit, pre-expiry guard, touch
  sleeves only underlying >= entry_spot*1.02).
- xsp_pcs: r19_options.py::select_xsp_legs + _xsp + _weekly_atr14 +
  _xsp_digital, books OPT_XSP_{CALM,GRADED}_{A,B}. Entry only on the
  first session of the week, 10:00-10:05 ET; prior-week digital (from
  the mids of two adjacent same-expiry XSP puts) must be below the
  75th percentile of the last 52 weekly observations, and below the
  median for the calm structure to trade at all (source regime skip);
  short strike targets prior_close - ATR14*(1.0 calm-regime /
  1.236 graded-regime), long strike exactly 5 below the short for
  calm, prior_close - ATR14*(1.618 / 1.786) for graded. Sizing: qty =
  min(risk_budget / max_loss_per_package, cash / width, displayed
  sizes); max loss = width - credit + 2 leg fees. Exit is the source's
  ONLY exit: European cash settlement at the weekly PM expiry
  (official_PM_expiry) — no earlier price stop exists in the source.
- public_recipe spot: source/strategies/public_recipes/
  public_source_sleeves.py::source_features for 'ai_volume'
  (EMA20 volume spike x2, EMA50 trend, exit_bars=5) and 'iu_body'
  (body > 4 * source-inclusive-21-body-sum/20 baseline, ATR14 x2
  trailing stop), per the Pine sources. SPOT100 long-only adaptation
  per the TSV: the bearish counterpart is an exit, never a short
  entry; sizing is 100% of available slice cash, whole units.

Fees: $0.65/contract/leg (batch-2 recorded assumption; the source
reads snapshot option_fees.per_contract_per_fill, which no v3
producer supplies yet). Inputs not produced by v3 producers (OPRA
chain, XSP index-regime state) leave the sleeves UNFED in the
registry — never fake-fed.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
ET = ZoneInfo('America/New_York')
EXP_ID_XSP_ETWIN = 'ENH-B13-XSP-ETWIN-20261024'
def _xsp_etwin_on(view, ctx, sid):
    extra = {}
    if isinstance(ctx, dict): extra.update(ctx.get('extra') or {})
    extra.update((view or {}).get('extra') or {})
    ov = extra.get('aster_xsp_enh')
    if isinstance(ov, dict):
        per = ov.get(sid) if isinstance(ov.get(sid), dict) else ov
        if isinstance(per, dict) and 'et_window' in per: return bool(per['et_window'])
    return True

from desk3.aster_b2 import (FEE_PER_CONTRACT, SLICE, _bars, _entry,
                            _in_window, _quantile, _sess)

SPECS = {
 "aster_rec_vwap20_vert_fixed_a": dict(book="OPT_VWAP20_VERTICAL_FIXED_A", family="recovery", signal="VWAP20", structure="vertical", risk=0.02, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="fixed"),
 "aster_rec_vwap20_vert_fixed_b": dict(book="OPT_VWAP20_VERTICAL_FIXED_B", family="recovery", signal="VWAP20", structure="vertical", risk=0.005, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="fixed"),
 "aster_rec_vwap20_vert_touch_a": dict(book="OPT_VWAP20_VERTICAL_TOUCH_A", family="recovery", signal="VWAP20", structure="vertical", risk=0.02, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="touch"),
 "aster_rec_vwap20_vert_touch_b": dict(book="OPT_VWAP20_VERTICAL_TOUCH_B", family="recovery", signal="VWAP20", structure="vertical", risk=0.005, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="touch"),
 "aster_xsp_pcs_calm_a":   dict(book="OPT_XSP_CALM_A", family="xsp_pcs", structure="calm", risk=0.03),
 "aster_xsp_pcs_calm_b":   dict(book="OPT_XSP_CALM_B", family="xsp_pcs", structure="calm", risk=0.01),
 "aster_xsp_pcs_graded_a": dict(book="OPT_XSP_GRADED_A", family="xsp_pcs", structure="graded", risk=0.03),
 "aster_xsp_pcs_graded_b": dict(book="OPT_XSP_GRADED_B", family="xsp_pcs", structure="graded", risk=0.01),
}
INPUTS_COMMON = ("bars", "options", "positions")
INPUTS_XSP = ("options", "positions", "xsp_state")
PRODUCERS = ({"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
             {"name": "options_chain", "outputs": ("options",), "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900})
PRODUCERS_XSP = PRODUCERS + ({"name": "xsp_index_regime", "outputs": ("xsp_state",), "freshness_sla_s": 900},)


# ---------------------------------------------------------------- recovery
def _contracts(view):
    """G4 batch-2 producer shape: view["options"] may be the fixture
    list of contract rows OR the live producer's per-underlying dict
    {UND: {"chains": {UND: [full rows]}, "quotes": {...}}}. Normalize
    to rows (same helper as aster_b2)."""
    raw = (view or {}).get("options") or []
    if isinstance(raw, list):
        return [c for c in raw if isinstance(c, dict)]
    if isinstance(raw, dict):
        out = []
        for payload in raw.values():
            if isinstance(payload, list):
                out.extend(c for c in payload if isinstance(c, dict))
            elif isinstance(payload, dict):
                chains = payload.get("chains") or {}
                if isinstance(chains, dict):
                    for rows in chains.values():
                        if isinstance(rows, list):
                            out.extend(c for c in rows if isinstance(c, dict))
                elif isinstance(chains, list):
                    out.extend(c for c in chains if isinstance(c, dict))
        return out
    return []

def _vwap20_signal(b):
    """Source recovery_signal VWAP20 arm on the last 200 sessions."""
    if len(b) < 200:
        return False
    closes = [float(x["c"]) for x in b]
    sma = sum(closes[-200:]) / 200
    last = b[-20:]
    vol = sum(float(x["v"]) for x in last)
    if vol <= 0:
        return False
    vwap = sum(((float(x["h"]) + float(x["l"]) + float(x["c"])) / 3)
               * float(x["v"]) for x in last) / vol
    return closes[-1] > sma and closes[-1] <= vwap * .98


EXP_ID_B4 = "ENH-B11-VWAP20VERT-EXITMID-20261024"
ENH11_VERT = ("aster_rec_vwap20_vert_fixed_a", "aster_rec_vwap20_vert_fixed_b",
              "aster_rec_vwap20_vert_touch_a", "aster_rec_vwap20_vert_touch_b")


def _enh11_exit_on(view, sid):
    """ENH batch 11 switch: extra[f'enh_{sid}'] {'exit_mid_limit': bool},
    default ON; OFF restores the pre-change market exit exactly."""
    ov = ((view or {}).get("extra") or {}).get(f"enh_{sid}")
    if isinstance(ov, dict) and "exit_mid_limit" in ov:
        return bool(ov["exit_mid_limit"])
    return True


def _enh11_paired(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)


def _opt_exits(sleeve_id, spec, view, ctx, positions):
    """Source _exit_intents as translated by the batch-2 engine:
    pre-expiry guard, planned hold exit, touch (touch books only)."""
    sess = _sess(view, ctx)
    out = []
    for p in positions:
        legs = p.get("legs")
        if not legs:
            continue
        expiry = str(legs[0].get("expiry") or "")[:10]
        held = p.get("sessions_held")
        if held is None:
            sym0 = legs[0].get("underlying")
            b = _bars(view, sym0) if sym0 else []
            ed = str(p.get("opened_at") or p.get("entry_date") or "")[:10]
            held = sum(1 for x in b if str(x.get("t"))[:10] > ed) if ed else 0
        reason = None
        try:
            if expiry and (date.fromisoformat(expiry)
                            - date.fromisoformat(sess)).days <= 1:
                reason = "pre_expiry_obligation_exit"
        except Exception:
            pass
        if not reason and int(held) >= spec["hold"]:
            reason = "planned_session_exit"
        if not reason and spec.get("exit_rule") == "touch":
            sym0 = legs[0].get("underlying")
            b = _bars(view, sym0) if sym0 else []
            spot = float(b[-1]["c"]) if b else float(p.get("entry_spot") or 0)
            if p.get("entry_spot") and spot >= float(p["entry_spot"]) * 1.02:
                reason = "touch_two_percent_recovery_exit"
        if reason:
            xit = {
                "intent_id": f"{sleeve_id}-exit-{p['symbol']}", "kind": "exit",
                "symbol": p["symbol"], "side": "sell",
                "qty": int(abs(float(p["qty"]))), "order_type": "market",
                "limit_price": None, "stop_price": None,
                "reason": f"{sleeve_id} exit: {reason} held={held}",
                "time_in_force": "day", "position_intent": "sell_to_close",
                "price_hint": float(p.get("avg_price") or 0) or None,
                "legs": [{"symbol": l["symbol"],
                          "side": "sell" if l.get("ratio", 1) > 0 else "buy",
                          "position_intent": "sell_to_close" if l.get("ratio", 1) > 0 else "buy_to_close",
                          "ratio": l.get("ratio", 1)} for l in legs]}
            # ENH batch 11 (binding leak: exit spread crossing): entries
            # got the batch-10 mid-limit cure via aster_b2._entry, but
            # these exits still crossed the full spread at market and
            # carried price_hint = cost basis (avg_price), not a market
            # price. Treatment: when the chain prices both legs, exit
            # as a limit at the package mid; the market-cross price
            # (bid long / ask short) is the paired shadow control.
            if sleeve_id in ENH11_VERT and _enh11_exit_on(view, sleeve_id):
                rows = {c.get("symbol"): c for c in _contracts(view)}
                mids, cross = [], None
                try:
                    for l in legs:
                        r = rows[l["symbol"]]
                        b, a = float(r["bid"]), float(r["ask"])
                        if not (b > 0 and a >= b):
                            raise ValueError("bad_quote")
                        mids.append(((b + a) / 2, b, a, l.get("ratio", 1)))
                    mid_ps = sum(m if rt > 0 else -m for m, _, _, rt in mids)
                    cross = sum(b if rt > 0 else -a for _, b, a, rt in mids)
                except (KeyError, TypeError, ValueError):
                    mids = []
                if mids and mid_ps > 0:
                    rec = {"exp_id": EXP_ID_B4, "sleeve": sleeve_id,
                           "kind": "exit", "switch_on": True,
                           "control_price_ps": round(cross, 4),
                           "treatment_limit_ps": round(mid_ps, 4),
                           "spread_saved_ps": round(mid_ps - cross, 4)}
                    xit["order_type"] = "limit"
                    xit["limit_price"] = round(mid_ps, 2)
                    xit["price_hint"] = round(mid_ps, 4)
                    xit["enhance_exp"] = rec
                    _enh11_paired(view, rec)
            out.append(xit)
    return out


def _evaluate_recovery(sleeve_id, spec, view, ctx):
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    out = _opt_exits(sleeve_id, spec, view, ctx, positions)
    if out:
        return out
    if any(p.get("legs") for p in positions):
        return []  # one package per book (source)
    if not _in_window(view, ctx):
        return []
    sess = _sess(view, ctx)
    for sym in ("IWM", "QQQ", "SPY"):  # source universe order, first pass wins
        b = _bars(view, sym)
        if not _vwap20_signal(b):
            continue
        e = _entry(view, ctx, sleeve_id, spec, sym, "call",
                   float(b[-1]["c"]), f"{sym}:{sess}")
        if e:
            return [e]
    return []


# ------------------------------------------------------------------- xsp
def _weekly_atr14(rows):
    """Source _weekly_atr14: Wilder ATR14 over completed weekly bars;
    returns (atr, last_close). Caller guarantees >= 15 bars."""
    trs = []
    for n, x in enumerate(rows):
        h, l = float(x["h"]), float(x["l"])
        if n == 0:
            continue
        pc = float(rows[n - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:14]) / 14
    for tr in trs[14:]:
        atr = (atr * 13 + tr) / 14
    return atr, float(rows[-1]["c"])


def _evaluate_xsp(sleeve_id, spec, view, ctx):
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    sess = _sess(view, ctx)
    # Source exit: European legs settle at the PM expiry close. No
    # earlier price stop exists in the source or the TSV exit rule.
    for p in positions:
        legs = p.get("legs")
        if not legs:
            continue
        expiry = str(legs[0].get("expiry") or "")[:10]
        if expiry and sess >= expiry:
            return [{"intent_id": f"{sleeve_id}-settle-{p['symbol']}",
                     "kind": "exit", "symbol": p["symbol"], "side": "sell",
                     "qty": int(abs(float(p["qty"]))), "order_type": "market",
                     "limit_price": None, "stop_price": None,
                     "settle": True,
                     "reason": f"{sleeve_id} exit: official_PM_expiry_settle expiry={expiry}",
                     "time_in_force": "day",
                     "position_intent": "sell_to_close",
                     "price_hint": float(p.get("avg_price") or 0) or None,
                     "legs": [{"symbol": l["symbol"],
                               "side": "sell" if l.get("ratio", 1) > 0 else "buy",
                               "position_intent": "sell_to_close" if l.get("ratio", 1) > 0 else "buy_to_close",
                               "ratio": l.get("ratio", 1)} for l in legs]}]
    if any(p.get("legs") for p in positions):
        return []  # one package per book (source)
    # Entry: source select_xsp_legs gates, in source order.
    cal = view.get("calendar") or {}
    t = str((ctx or {}).get("now") or view.get("now") or "")
    # ENH batch 13 (binding leak: entry-window clock read raw): the
    # 10:00-10:05 ET window was sliced out of the raw timestamp string,
    # so a UTC-stamped live snapshot (14:00Z = 10:00 ET) NEVER opened
    # the window and a 10:00Z stamp opened it at 06:00 ET. Convert
    # tz-aware stamps to ET; naive stamps keep the source ET reading
    # (shadow control = the raw slice, recorded in the paired journal).
    try:
        if _xsp_etwin_on(view, ctx, sleeve_id):
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(ET)
            hm = (dt.hour, dt.minute)
        else:
            hm = (int(t[11:13]), int(t[14:16]))
    except Exception:
        return []
    _xj = (view.get("extra") or {}).get("edge_exp_journal")
    if isinstance(_xj, dict) and isinstance(_xj.get("records"), list):
        try: _ctrl = (int(t[11:13]), int(t[14:16]))
        except Exception: _ctrl = None
        _xj["records"].append({"exp_id": EXP_ID_XSP_ETWIN, "sleeve": sleeve_id,
            "control_window_open": bool(_ctrl and (10, 0) <= _ctrl < (10, 5)),
            "treatment_window_open": bool((10, 0) <= hm < (10, 5))})
    if not cal.get("first_session_of_week") or not ((10, 0) <= hm < (10, 5)):
        return []
    state = view.get("xsp_state") or {}
    weekly = state.get("weekly_bars") or []
    if not weekly or weekly[-1].get("week_end") != cal.get("previous_session"):
        return []
    if len(weekly) < 15:
        return []
    hist = sorted((x for x in (state.get("prior_digitals") or [])
                   if x.get("week_end", "") < sess),
                  key=lambda x: x["week_end"])
    if len({x["week_end"] for x in hist}) != len(hist) or len(hist) < 26:
        return []
    if any(not 0 < float(x["value"]) < 1 for x in hist):
        return []
    chain = {(c.get("symbol")): c for c in _contracts(view)}
    adj = state.get("adjacent_put_symbols") or []
    if len(adj) != 2 or adj[0] == adj[1] or any(s not in chain for s in adj):
        return []
    expiry = cal.get("weekly_pm_expiry")
    legs_adj = [chain[s] for s in adj]
    if any(c.get("underlying") != "XSP" or c.get("right") != "put"
           or str(c.get("expiry"))[:10] != expiry for c in legs_adj):
        return []
    legs_adj = sorted(legs_adj, key=lambda x: float(x["strike"]))
    lo, hi = float(legs_adj[0]["strike"]), float(legs_adj[1]["strike"])
    if any(c.get("underlying") == "XSP" and c.get("right") == "put"
           and str(c.get("expiry"))[:10] == expiry
           and lo < float(c["strike"]) < hi for c in chain.values()):
        return []  # strikes not adjacent
    mids = [(float(c["bid"]) + float(c["ask"])) / 2 for c in legs_adj]
    current = (mids[1] - mids[0]) / (hi - lo)
    if not 0 < current < 1:
        return []
    vals = [float(x["value"]) for x in hist[-52:]]
    median = _quantile(vals, .5)
    p75 = _quantile(vals, .75)
    if current >= p75 or (spec["structure"] == "calm" and current >= median):
        return []  # XSP_conditional_regime_skip
    atr, priorclose = _weekly_atr14(weekly)
    if atr <= 0 or priorclose <= 0:
        return []
    calm = current < median
    target_short = priorclose - atr * (1 if calm else 1.236)
    if spec["structure"] == "calm":
        target_long = target_short - 5
    else:
        target_long = priorclose - atr * (1.618 if calm else 1.786)
    puts = [c for c in chain.values() if c.get("underlying") == "XSP"
            and c.get("right") == "put" and str(c.get("expiry"))[:10] == expiry]
    if not puts:
        return []
    short = min(puts, key=lambda x: (abs(float(x["strike"]) - target_short),
                                     str(x["symbol"])))
    choices = [x for x in puts if float(x["strike"]) < float(short["strike"])
               and (spec["structure"] != "calm"
                    or float(short["strike"]) - float(x["strike"]) == 5)]
    if not choices:
        return []
    long = min(choices, key=lambda x: (abs(float(x["strike"]) - target_long),
                                       str(x["symbol"])))
    width = (float(short["strike"]) - float(long["strike"])) * 100
    credit = (float(short["bid"]) - float(long["ask"])) * 100
    if credit <= 0:
        return []
    loss = width - credit + 2 * FEE_PER_CONTRACT
    if not 0 < loss < width:
        return []
    risk = spec["risk"] * SLICE
    qty = min(int(risk // loss), int(SLICE // width),
              int(long["ask_size"]), int(short["bid_size"]))
    if qty < 1:
        return []  # XSP_package_unaffordable
    legs = [dict(long, ratio=1), dict(short, ratio=-1)]
    return [{"intent_id": f"{sleeve_id}-xsp-{sess}", "kind": "entry",
             "symbol": short["symbol"], "side": "sell", "qty": qty,
             "order_type": "market", "limit_price": None, "stop_price": None,
             "reason": (f"{sleeve_id} entry: XSP_prior_week_conditional_credit "
                        f"book={spec['book']} digital={current:.4f} "
                        f"median={median} p75={p75} credit={credit / 100:.2f} "
                        f"max_loss={loss:.2f} risk_budget={risk:.0f}"),
             "time_in_force": "day", "position_intent": "sell_to_open",
             "price_hint": None, "entry_spot": priorclose,
             "exit_rule": "settle", "expiry": expiry,
             "legs": [{"symbol": l["symbol"],
                       "side": "buy" if l["ratio"] > 0 else "sell",
                       "position_intent": "buy_to_open" if l["ratio"] > 0 else "sell_to_open",
                       "ratio": l["ratio"], "strike": float(l["strike"]),
                       "expiry": expiry, "right": "put",
                       "underlying": "XSP", "exercise_style": "european"}
                      for l in legs]}]


# ----------------------------------------------------------- public spot
def _ema(xs, n):
    out = []
    old = None
    a = 2 / (n + 1)
    for x in xs:
        old = x if old is None else a * x + (1 - a) * old
        out.append(old)
    return out


def _rma(xs, n):
    out = []
    seed = []
    old = None
    for x in xs:
        if x is None:
            out.append(None)
            continue
        if old is None:
            seed.append(x)
            if len(seed) < n:
                out.append(None)
                continue
            old = sum(seed[-n:]) / n
        else:
            old = (old * (n - 1) + x) / n
        out.append(old)
    return out


def _atr_series(bars, n):
    tr = []
    for i, b in enumerate(bars):
        if i == 0:
            tr.append(float(b["h"]) - float(b["l"]))
        else:
            pc = float(bars[i - 1]["c"])
            tr.append(max(float(b["h"]) - float(b["l"]),
                          abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    return _rma(tr, n)


def _spot_bars(view, sym):
    m = view.get("bars") or {}
    for k in (f"{sym}|4Hour", f"{sym}|4H", sym):
        if m.get(k):
            return m[k]
    return []


def _spot_position(view, sid, sym):
    for p in view.get("positions") or []:
        if p.get("sleeve_id") not in (None, sid):
            continue
        if p.get("symbol") == sym and float(p.get("qty") or 0) != 0:
            return p
    return None


def _spot_cash(view):
    sl = view.get("slice") or {}
    if isinstance(sl, dict) and "cash_usd" in sl:
        return float(sl["cash_usd"])
    return SLICE


def _spot_intent(sid, sym, kind, qty, price, reason, tag):
    return {"intent_id": f"{sid}-{sym}-{tag}", "kind": kind, "symbol": sym,
            "side": "buy" if kind == "entry" else "sell", "qty": int(qty),
            "order_type": "market", "limit_price": None, "stop_price": None,
            "reason": f"{sid} {kind}: {reason}", "time_in_force": "gtc",
            "position_intent": "buy_to_open" if kind == "entry" else "sell_to_close",
            "price_hint": float(price)}


EXP_ID_LINK = "ENH-B6-HELDBARS-20261024"


def _link_enh_on(view, ctx, sid):
    """EDGE batch 6 switch: enhance_held_bars, default ON. OFF restores
    the pre-change rule exactly (bars_held field or 0, nothing else)."""
    for src in ((ctx or {}), (view or {}).get("params") or {},
                (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            sub = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(sub, dict) and "enhance_held_bars" in sub:
                return bool(sub["enhance_held_bars"])
    return True


def _link_shadow(ctx, sid, rec):
    sd = (ctx or {}).get("state_dir") if isinstance(ctx, dict) else None
    if not sd:
        return
    try:
        import json as _j, os as _o
        _o.makedirs(sd, exist_ok=True)
        with open(_o.path.join(sd, "enhance_journal.jsonl"), "a") as fh:
            fh.write(_j.dumps({"sleeve": sid, **rec}, sort_keys=True) + "\n")
    except Exception:
        pass


def _bar_close_ts(b):
    t = b.get("t")
    try:
        if isinstance(t, (int, float)):
            return float(t) + 14400.0  # 4h bars, epoch-seconds stamps
        from datetime import datetime, timezone
        d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.timestamp() + 14400.0
    except Exception:
        return None


def _opened_ts(pos):
    raw = pos.get("opened_at") or pos.get("entry_time")
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return float(raw)
        from datetime import datetime, timezone
        d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except Exception:
        return None


def _derived_bars_held(pos, bars):
    """Bars whose close falls after the position opened — the count
    the source 5-bar time exit consumes when the journal row carries
    opened_at but no bars_held field."""
    opened = _opened_ts(pos)
    if opened is None:
        return None
    n = 0
    for b in bars:
        ct = _bar_close_ts(b)
        if ct is not None and ct > opened:
            n += 1
    return n


def evaluate_link_ai_volume(view, ctx=None, sid="aster_pub_link_ai_volume"):
    """Archive ai_volume: volume > 2*EMA20(volume) spike; long iff
    bullish candle and close > EMA50(close); bearish counterpart is an
    exit in this long-only spot adaptation (TSV); time exit after 5
    bars (source exit_bars, counted as in the archive reducer)."""
    sym = "LINKUSDT"
    bars = _spot_bars(view, sym)
    pos = _spot_position(view, sid, sym)
    if len(bars) < 50:
        return []
    closes = [float(b["c"]) for b in bars]
    vols = [float(b["v"]) for b in bars]
    b = bars[-1]
    vema = _ema(vols, 20)[-1]
    pema = _ema(closes, 50)[-1]
    spike = vols[-1] > vema * 2.0
    long_sig = spike and closes[-1] > pema and closes[-1] > float(b["o"])
    short_sig = spike and closes[-1] < pema and closes[-1] < float(b["o"])
    if pos is not None:
        held = pos.get("bars_held")
        if held is None:
            # EDGE batch 6 binding leak: the designed 5-bar time exit
            # read ONLY the bars_held field; a position row carrying
            # opened_at but no bars_held silently held forever (only a
            # bearish spike could exit it). Treatment derives the held
            # count from opened_at over the bar series; the legacy
            # held=0 reading is the paired shadow control.
            held = 0
            if _link_enh_on(view, ctx, sid):
                derived = _derived_bars_held(pos, bars)
                if derived is not None:
                    held = derived
                    if derived >= 5:
                        _link_shadow(ctx, sid, {
                            "exp_id": EXP_ID_LINK, "kind": "exit",
                            "control_exit": False, "treatment_exit": True,
                            "derived_bars_held": derived,
                            "rule": "held_bars_derivation"})
        if short_sig:
            return [_spot_intent(sid, sym, "exit", abs(float(pos["qty"])),
                                 closes[-1], "source_bearish_counterpart_exit",
                                 "exit-signal")]
        if int(held) >= 5:
            return [_spot_intent(sid, sym, "exit", abs(float(pos["qty"])),
                                 closes[-1], "source_signal_reset_counter_exit_bars5",
                                 "exit-bars")]
        return []
    if not long_sig:
        return []
    qty = int(_spot_cash(view) // closes[-1])
    if qty < 1:
        return []
    return [_spot_intent(sid, sym, "entry", qty, closes[-1],
                         "source_entry_long volume_spike trend_up bullish",
                         "entry")]


def evaluate_enj_iu_body(view, ctx=None, sid="aster_pub_enj_iu_body"):
    """Archive iu_body: |body| > 4 * (sum of last 21 bodies)/20 and
    bullish => long entry (long-only spot adaptation; the bearish
    strong-body counterpart is an exit per the TSV). Exit also on the
    source ATR14 x2 trailing stop, reconstructed deterministically
    from the bars after entry (stop starts at avg - 2*ATR, ratchets
    with close - 2*ATR, never loosens)."""
    sym = "ENJUSDT"
    bars = _spot_bars(view, sym)
    pos = _spot_position(view, sid, sym)
    if len(bars) < 21:
        return []
    bodies = [abs(float(b["c"]) - float(b["o"])) for b in bars]
    base = sum(bodies[-21:]) / 20
    b = bars[-1]
    strong = bodies[-1] > base * 4.0
    long_sig = strong and float(b["c"]) > float(b["o"])
    short_sig = strong and float(b["c"]) < float(b["o"])
    if pos is not None:
        qty = abs(float(pos["qty"]))
        if short_sig:
            return [_spot_intent(sid, sym, "exit", qty, float(b["c"]),
                                 "source_opposite_body_exit", "exit-signal")]
        held = pos.get("bars_held")
        _held_derived = False
        if held is None and _link_enh_on(view, ctx, sid):
            # ENH-B5-ENJ-HELDBARS (Edge batch 5, 2026-10-24): binding
            # leak — the ATR14 x2 trailing stop (this sleeve's ONLY
            # price stop) read bars_held, a field desk position rows
            # do not carry (they carry opened_at), so on real rows
            # the stop never evaluated and losses ran unbounded.
            # Treatment: derive bars held from opened_at against bar
            # close stamps (same derivation EDGE batch 6 proved for
            # the LINK ai_volume time exit in this file). Switch =
            # enhance_held_bars (shared helper), default ON; OFF
            # restores the field-only rule exactly. Shadow control =
            # the field-only decision (no stop), paired on the intent.
            held = _derived_bars_held(pos, bars)
            _held_derived = held is not None
        atrs = _atr_series(bars, 14)
        if held is not None and int(held) >= 1 and atrs[-2] is not None:
            entry_idx = len(bars) - 1 - int(held)
            if 0 <= entry_idx < len(bars) - 1:
                avg = float(pos.get("avg_price") or bars[entry_idx]["c"])
                stop = None
                for i in range(entry_idx, len(bars) - 1):
                    if atrs[i] is None:
                        continue
                    cand = float(bars[i]["c"]) - atrs[i] * 2.0
                    init = avg - atrs[i] * 2.0
                    stop = init if stop is None else max(stop, cand)
                if stop is not None and stop > 0 and float(b["l"]) <= stop:
                    it = _spot_intent(sid, sym, "exit", qty, float(b["c"]),
                                      f"source_atr_trailing_stop stop={stop:.4f}",
                                      "exit-atr")
                    if _held_derived:
                        it["reason"] += " enh:ENH-B5-ENJ-HELDBARS-20261024 held_derived_from_opened_at"
                        it["enhance_exp"] = {"exp_id": "ENH-B5-ENJ-HELDBARS-20261024",
                            "sleeve": sid, "control_decision": "no_stop_bars_held_absent",
                            "treatment_decision": "atr_trailing_stop_exit",
                            "bars_held_derived": int(held)}
                        _link_shadow(ctx, sid, it["enhance_exp"])
                    return [it]
        return []
    if not long_sig:
        return []
    qty = int(_spot_cash(view) // float(b["c"]))
    if qty < 1:
        return []
    return [_spot_intent(sid, sym, "entry", qty, float(b["c"]),
                         "source_body_impulse_long", "entry")]


PUB_EVALUATORS = {"aster_pub_link_ai_volume": evaluate_link_ai_volume,
                  "aster_pub_enj_iu_body": evaluate_enj_iu_body}
PUB_INPUTS = ("bars", "positions")


def evaluate(sleeve_id, view, ctx=None):
    view = view or {}
    ctx = ctx or {}
    if sleeve_id in PUB_EVALUATORS:
        return PUB_EVALUATORS[sleeve_id](view, ctx, sleeve_id)
    spec = SPECS[sleeve_id]
    if spec["family"] == "xsp_pcs":
        return _evaluate_xsp(sleeve_id, spec, view, ctx)
    return _evaluate_recovery(sleeve_id, spec, view, ctx)
