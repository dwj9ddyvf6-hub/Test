"""Aster batch 1 engine — 10 sleeves (ASTER-BUILD-MAP.md batch 1).

Faithful ports from the staged Ausar/Aster archive
(~/workspace/.scratch-ausar-archive/handoff-20261024/source, read-only):
- aster_rsi2_1d / aster_squeeze_1d: backend/trader_signals.py frozen
  rules trader_rsi2_public_v1 / trader_squeeze20_public_v1 (indicator
  math ported function-for-function: Wilder RSI via RMA seed, EMA seed
  = first-period mean, BB population stdev, LazyBear momentum =
  linreg endpoint of delta). Sizing per backend/trader_runtime.py:
  cap = min(0.10*equity, 0.01*DV20, cash); risk sleeves also cap at
  floor(0.005*equity / stop_distance). RSI2 has NO initial stop.
- aster_tensor_h1_recovery / aster_tensor_w1_recovery:
  backend/tensor_strategy.py StateRepairPolicy (R11): 4-bar panel,
  repair = balance[-1]-balance[0] >= 2, >=2 of 7 vote channels
  increasing across adjacent transitions, total_votes == 7 at both
  ends, close >= 5, DV20 >= $1M, ATR > 0, excluded {SPY,QQQ,B,GOLD},
  cooldown 20 native bars, exit at entry bar + 20, sizing
  floor(min(.1*eq,.01*DV20,cash)/(price*1.001)), rank by
  repair + .01*balance + .001*clip(OBV_slope5/volume,-10,10), sym asc.
  Consumes canonical Tensor products at the sleeve layer via
  view["tensor"] (Tensor ENGINE untouched); no tensor key in the
  snapshot => the registry marks the sleeve UNFED, never fake-fed.
- aster_abs_enj_4h / aster_abs_link_4h: strategies/absorption/
  signals.py advance() ported with Decimal EMA (spans 20/50,
  current-inclusive), rules-v1.json: 300-bar warmup, entry on the
  confirmation bar only, sizing = full available slice cash incl.
  10bp fee, exit at confirmation completion + 16h (never resets).
- aster_native_btc_eth_sma200 / aster_native_eth_sma200:
  backend/prospective_native.py + prospective_native_math.py:
  gate = completed daily close strictly above inclusive SMA200;
  fee-funded rebalance() bisection ported; sells before buys.
- aster_open_gamma_a / aster_open_gamma_b: backend/r19_options.py
  opening_gamma family: causal R5 + completed opening 5-min break
  (return < 0, break below first-5min low), entry window
  09:35 <= ET < 09:45, _opening_event_clocks causality, long puts,
  DTE/delta per options_rules.json books (A: DTE 0-2, B: DTE 7-14,
  delta 0.50-0.65), premium caps (A 2.5%, B 1.5% of spot), risk
  fractions (A 2.0%, B 0.5% of the $10k slice), exit flat 10:00 ET
  on the entry day (or later if missed; expiry obligation earlier).

v3 intent shape: plain dicts for the desk3 dispatcher. Positions are
snapshot rows {symbol, qty, avg_price, opened_at?, bars_held?/
sessions_held?, entry_bar_index?, legs?, entry_session?, ...};
holding counts prefer explicit position fields, then bars after
opened_at, then the sleeve's own state file (ctx state_dir).
"""
from __future__ import annotations
import json, math, os
from datetime import datetime, timezone, timedelta
from decimal import Decimal, localcontext
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UNIVERSE15 = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV",
              "XLI", "XLP", "XLU", "XLB", "XLY", "SMH", "SOXX")
TENSOR_EXCLUDED = frozenset({"SPY", "QQQ", "B", "GOLD"})
VOTE_NAMES = ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave")

SPECS = {
 "aster_rsi2_1d": dict(kind="rsi2", cadence_s=300, session="rth"),
 "aster_squeeze_1d": dict(kind="squeeze", cadence_s=300, session="rth"),
 "aster_tensor_h1_recovery": dict(kind="tensor", frame="1h", tf="1Hour",
                                  cadence_s=3600, session="rth"),
 "aster_tensor_w1_recovery": dict(kind="tensor", frame="1wk", tf="1Week",
                                  cadence_s=3600, session="rth"),
 "aster_abs_enj_4h": dict(kind="absorption", symbol="ENJUSDT",
                          cadence_s=14400, session="24h"),
 "aster_abs_link_4h": dict(kind="absorption", symbol="LINKUSDT",
                           cadence_s=14400, session="24h"),
 "aster_native_btc_eth_sma200": dict(kind="native",
    weights=(("BTC-USD", 0.5), ("ETH-USD", 0.5)),
    cadence_s=86400, session="24h"),
 "aster_native_eth_sma200": dict(kind="native",
    weights=(("ETH-USD", 1.0),),
    cadence_s=86400, session="24h"),
 "aster_open_gamma_a": dict(kind="gamma", risk_fraction=0.02,
    max_premium_spot=0.025, dte=(0, 2), cadence_s=300, session="rth"),
 "aster_open_gamma_b": dict(kind="gamma", risk_fraction=0.005,
    max_premium_spot=0.015, dte=(7, 14), cadence_s=300, session="rth"),
}
INPUTS_BY_KIND = {
 "rsi2": ("bars", "positions"), "squeeze": ("bars", "positions"),
 "tensor": ("tensor", "bars", "positions"),
 "absorption": ("bars", "quotes", "positions"),
 "native": ("bars", "positions"),
 "gamma": ("opening_events", "options", "positions"),
}
PRODUCERS = (
 {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
 {"name": "tensor_bundle", "outputs": ("tensor",), "freshness_sla_s": 86400},
 {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900},
 {"name": "quotes", "outputs": ("quotes",), "freshness_sla_s": 60},
 {"name": "options_chain", "outputs": ("options",), "freshness_sla_s": 300},
 {"name": "opening_events", "outputs": ("opening_events",),
  "freshness_sla_s": 300},
)



EXP_ID_TENSOR_REC = "ENH-B13-TENSORREC-REPRICE-20261024"
def _tensor_rec_enh_on(view, ctx, sid):
    """ENH (Edge batch 13): executable-price revalidation for Tensor
    recovery entries. Default ON; OFF restores the panel-close rule."""
    extra = {}
    if isinstance(ctx, dict): extra.update(ctx.get("extra") or {})
    extra.update((view or {}).get("extra") or {})
    ov = extra.get("aster_tensor_rec_enh")
    if isinstance(ov, dict):
        per = ov.get(sid) if isinstance(ov.get(sid), dict) else ov
        if isinstance(per, dict) and "exec_reprice" in per:
            return bool(per["exec_reprice"])
    return True

def _tensor_rec_paired(view, ctx, record):
    extra = (view or {}).get("extra") or {}
    j = extra.get("edge_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)

def inputs_for(sleeve_id):
    return INPUTS_BY_KIND[SPECS[sleeve_id]["kind"]]


# ---------------------------------------------------------------- utils
def _now(view, ctx):
    raw = (view or {}).get("now") or (ctx or {}).get("now")
    if raw:
        if isinstance(raw, datetime):
            d = raw
        else:
            d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    sess = (ctx or {}).get("session")
    if sess:
        return datetime.fromisoformat(str(sess) + "T14:00:00+00:00")
    return datetime.now(timezone.utc)


def _parse_ts(raw):
    if raw is None:
        return None
    if isinstance(raw, datetime):
        d = raw
    elif isinstance(raw, (int, float)):
        d = datetime.fromtimestamp(float(raw), tz=timezone.utc)
    else:
        try:
            d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _equity(view, ctx):
    sl = (view or {}).get("slice") or (ctx or {}).get("slice") or {}
    for v in (sl.get("capital_usd"), (ctx or {}).get("equity"),
              (view or {}).get("equity")):
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 10000.0


def _cash(view, ctx):
    sl = (view or {}).get("slice") or (ctx or {}).get("slice") or {}
    if sl.get("cash_usd") is not None:
        try:
            return float(sl["cash_usd"])
        except (TypeError, ValueError):
            pass
    return _equity(view, ctx)


def _bars(view, sym, tfs):
    m = (view or {}).get("bars") or {}
    for tf in tfs:
        for k in (f"{sym}|{tf}", sym if tf is None else None):
            if k and m.get(k):
                return list(m[k])
    if m.get(sym):
        return list(m[sym])
    return []


def _bar(row):
    """Normalize archive (open/high/...) and v3 (o/h/l/c/v) bar rows."""
    g = row.get
    return {"t": g("t", g("timestamp_ms", g("timestamp"))),
            "o": float(g("o", g("open"))), "h": float(g("h", g("high"))),
            "l": float(g("l", g("low"))), "c": float(g("c", g("close"))),
            "v": float(g("v", g("volume", 0.0)))}


def _norm(rows):
    return [_bar(r) for r in rows]


def _positions(view):
    out = {}
    for p in (view or {}).get("positions") or []:
        try:
            q = float(p.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        if q != 0 and p.get("symbol"):
            out[p["symbol"]] = p
    return out


def _state(ctx, sleeve_id):
    sd = (ctx or {}).get("state_dir")
    if not sd:
        return {}, None
    path = os.path.join(sd, f"aster_b1_{sleeve_id}.json")
    try:
        return (json.load(open(path)) if os.path.exists(path) else {}), path
    except Exception:
        return {}, path


def _save_state(path, st):
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(st, fh, sort_keys=True)


def _held_bars(view, pos, sym, tfs, bar_count_now=None):
    for k in ("bars_held", "sessions_held", "held_bars"):
        if pos.get(k) is not None:
            try:
                return int(float(pos[k]))
            except (TypeError, ValueError):
                pass
    opened = _parse_ts(pos.get("opened_at") or pos.get("entry_at")
                       or pos.get("opened"))
    if opened is not None:
        rows = _bars(view, sym, tfs)
        n = 0
        for r in rows:
            t = _parse_ts(r.get("t", r.get("timestamp_ms",
                                         r.get("timestamp"))))
            if t is not None and t > opened:
                n += 1
        if rows:
            return n
    return None


def _intent(sleeve_id, stamp, n, kind, sym, side, qty, reason,
            price=None, stop=None, legs=None):
    d = {"intent_id": f"{sleeve_id}-{stamp}-{n}-{sym}",
         "kind": kind, "symbol": sym, "side": side, "qty": qty,
         "order_type": "market", "limit_price": None,
         "stop_price": stop, "reason": reason, "time_in_force": "day"}
    if price is not None:
        d["price_hint"] = float(price)
    if legs is not None:
        d["legs"] = legs
        d["position_intent"] = ("buy_to_open" if side == "buy"
                                 else "sell_to_close")
    return d


# ------------------------------------------------- trader indicator math
# Ported from archive trader_signals.py (frozen public adaptations).
def _sma(values, period):
    out = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = math.fsum(values[i + 1 - period:i + 1]) / period
    return out


def _smooth(values, period, alpha):
    out = [None] * len(values)
    if len(values) < period:
        return out
    out[period - 1] = math.fsum(values[:period]) / period
    for i in range(period, len(values)):
        out[i] = out[i - 1] + alpha * (values[i] - out[i - 1])
    return out


def _ema(values, period):
    return _smooth(values, period, 2.0 / (period + 1))


def _rma(values, period):
    return _smooth(values, period, 1.0 / period)


def _true_range(bars):
    return [max(b["h"] - b["l"],
                abs(b["h"] - bars[i - 1]["c"]),
                abs(b["l"] - bars[i - 1]["c"])) if i else b["h"] - b["l"]
            for i, b in enumerate(bars)]


def _rsi(values, period):
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gain = _rma([max(v, 0.0) for v in changes], period)
    loss = _rma([max(-v, 0.0) for v in changes], period)
    out = [None] * len(values)
    for i in range(period, len(values)):
        g, l = gain[i - 1], loss[i - 1]
        out[i] = (50.0 if g == l == 0 else 100.0 if l == 0
                  else 0.0 if g == 0 else 100.0 - 100.0 / (1.0 + g / l))
    return out


def _linreg_endpoint(values):
    period = len(values)
    cx = (period - 1) / 2.0
    cy = math.fsum(values) / period
    den = math.fsum((i - cx) ** 2 for i in range(period))
    slope = math.fsum((i - cx) * (v - cy)
                      for i, v in enumerate(values)) / den
    return cy + slope * cx


def _squeeze_series(bars):
    closes = [b["c"] for b in bars]
    n = k = m = 20
    sma = _sma(closes, n)
    center = _ema(closes, k)
    atr = _rma(_true_range(bars), k)
    squeeze = [None] * len(bars)
    delta = [None] * len(bars)
    momentum = [None] * len(bars)
    for i in range(max(n, k) - 1, len(bars)):
        mean = sma[i]
        sd = math.sqrt(math.fsum((v - mean) ** 2
                                 for v in closes[i + 1 - n:i + 1]) / n)
        upper, lower = mean + 2.0 * sd, mean - 2.0 * sd
        kc_u = center[i] + 1.5 * atr[i]
        kc_l = center[i] - 1.5 * atr[i]
        squeeze[i] = lower > kc_l and upper < kc_u
        window = bars[i + 1 - m:i + 1]
        mid = (max(b["h"] for b in window)
               + min(b["l"] for b in window)) / 2.0
        delta[i] = closes[i] - (mid + sma[i]) / 2.0
        if i >= max(n, k) - 1 + m - 1:
            momentum[i] = _linreg_endpoint(delta[i + 1 - m:i + 1])
    return {"squeeze": squeeze, "momentum": momentum,
            "kc_center": center, "kc_atr": atr}


def _trader_features(kind, bars):
    closes = [b["c"] for b in bars]
    i = len(bars) - 1
    atr = _rma(_true_range(bars), 14)[i]
    dv20 = math.fsum(b["c"] * b["v"] for b in bars[-20:]) / 20
    if not atr or atr <= 0 or dv20 <= 0:
        return None
    f = {"close": closes[i], "atr14": atr, "dollar_volume20": dv20}
    if kind == "rsi2":
        f["rsi2"] = _rsi(closes, 2)[i]
        f["sma200"] = _sma(closes, 200)[i]
        f["sma5"] = _sma(closes, 5)[i]
        if None in (f["rsi2"], f["sma200"], f["sma5"]):
            return None
        f["entry"] = (f["rsi2"] <= 5.0 and f["close"] > f["sma200"]
                      and f["close"] < f["sma5"])
        f["exit_reasons"] = (["close_above_sma5"]
                             if f["close"] > f["sma5"] else [])
        f["rank"] = (f["rsi2"], -(f["sma5"] - f["close"]) / atr)
        f["max_hold"] = 10
        f["stop_distance"] = None
    else:
        vals = _squeeze_series(bars)
        mom, prev = vals["momentum"][i], vals["momentum"][i - 1]
        if mom is None or prev is None or vals["kc_center"][i] is None:
            return None
        prior_high = max(b["h"] for b in bars[i - 20:i])
        release = (vals["squeeze"][i - 1] is True
                   and vals["squeeze"][i] is False)
        f.update({"momentum": mom, "previous_momentum": prev,
                  "kc_center": vals["kc_center"][i],
                  "prior20_high": prior_high, "squeeze_release": release})
        f["entry"] = bool(release and mom > 0 and mom > prev
                          and f["close"] > prior_high)
        reasons = []
        if f["close"] < f["kc_center"]:
            reasons.append("close_below_ema20")
        if mom <= 0:
            reasons.append("momentum_nonpositive")
        f["exit_reasons"] = reasons
        f["rank"] = (-mom / atr,)
        f["max_hold"] = 20
        f["stop_distance"] = 2.0 * atr
    return f


EXP_ID_B1 = "ENH-B11-TRADER-COMPLETEDBAR-20261024"
ENH11_TRADER = ("aster_rsi2_1d", "aster_squeeze_1d")


def _enh11_on(view, ctx, sid):
    """ENH batch 11 switch: extra[f'enh_{sid}'] or ctx['enhance'][sid]
    {'completed_bar': bool}, default ON; OFF restores the pre-change
    last-bar (forming-bar-inclusive) rule exactly."""
    for src in ((view or {}).get("extra") or {}, (ctx or {}).get("enhance") or {}):
        ov = src.get(f"enh_{sid}") or src.get(sid)
        if isinstance(ov, dict) and "completed_bar" in ov:
            return bool(ov["completed_bar"])
    return True


def _enh11_paired(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)


def _eval_trader(sleeve_id, spec, view, ctx, now):
    kind = spec["kind"]
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    state, spath = _state(ctx, sleeve_id)
    equity, cash = _equity(view, ctx), _cash(view, ctx)
    out, n = [], 0
    # ENH batch 11 (binding leak: forming-bar perception): the trader
    # rules are defined on COMPLETED daily bars, but features were
    # computed over the last bar even while it is still forming (the
    # desk evaluates every ~86s through RTH), so entries/exits fired
    # intraday on a "close" that was not a close and could vanish by
    # the bell. Treatment: drop bars dated the current ET session from
    # the feature set; the forming-bar decision is the shadow control.
    enh = sleeve_id in ENH11_TRADER and _enh11_on(view, ctx, sleeve_id)
    sess_date = now.astimezone(ET).date().isoformat() if enh else None
    feats = {}
    for sym in UNIVERSE15:
        rows = _bars(view, sym, ("1Day", "1D"))
        if len(rows) >= 252:
            try:
                f = _trader_features(kind, _norm(rows))
            except (TypeError, ValueError, KeyError):
                f = None
            if enh:
                done = [r for r in rows
                        if str(r.get("t") or "")[:10] < sess_date]
                fd = None
                if len(done) >= 252:
                    try:
                        fd = _trader_features(kind, _norm(done))
                    except (TypeError, ValueError, KeyError):
                        fd = None
                if bool((f or {}).get("entry")) != bool((fd or {}).get("entry")) \
                        or bool((f or {}).get("exit_reasons")) != bool((fd or {}).get("exit_reasons")):
                    _enh11_paired(view, {
                        "exp_id": EXP_ID_B1, "sleeve": sleeve_id,
                        "symbol": sym, "switch_on": True,
                        "control_enter": bool((f or {}).get("entry")),
                        "treatment_enter": bool((fd or {}).get("entry")),
                        "control_exit": bool((f or {}).get("exit_reasons")),
                        "treatment_exit": bool((fd or {}).get("exit_reasons"))})
                f = fd
            if f:
                feats[sym] = f
    # exits first (owned exits continue even if entries would refuse)
    for sym in sorted(positions):
        p = positions[sym]
        qty = float(p["qty"])
        if qty <= 0:
            continue
        held = _held_bars(view, p, sym, ("1Day", "1D"))
        if held is None and state.get(sym):
            rows = _bars(view, sym, ("1Day", "1D"))
            held = len(rows) - int(state[sym].get("bar_count", len(rows)))
        reason = None
        f = feats.get(sym)
        if f and f["exit_reasons"]:
            reason = ";".join(f["exit_reasons"])
        if (kind == "squeeze" and reason is None):
            stop = p.get("stop_price") or state.get(sym, {}).get(
                "stop_price")
            rows = _bars(view, sym, ("1Day", "1D"))
            if stop and rows:
                try:
                    if _norm(rows)[-1]["l"] <= float(stop):
                        reason = "observed_quote_initial_2atr_stop"
                except (TypeError, ValueError, KeyError):
                    pass
        if reason is None and held is not None:
            max_hold = (f or {}).get("max_hold",
                                     10 if kind == "rsi2" else 20)
            if held >= max_hold:
                reason = f"{max_hold}_completed_holding_bars"
        if reason:
            n += 1
            out.append(_intent(sleeve_id, stamp, n, "exit", sym, "sell",
                               int(qty), f"{sleeve_id}:{reason}",
                               price=(f or {}).get("close")))
            state.pop(sym, None)
    if out:
        _save_state(spath, state)
        return out
    # entries: ranked candidates into free slots (max 10 positions)
    free = 10 - len(positions)
    if free <= 0:
        return []
    cands = [(f["rank"] + (sym,), sym, f) for sym, f in feats.items()
             if f["entry"] and sym not in positions]
    for _, sym, f in sorted(cands, key=lambda x: x[0]):
        if len(out) >= free:
            break
        cap = min(0.10 * equity, 0.01 * f["dollar_volume20"], cash)
        shares = int(cap // f["close"]) if f["close"] > 0 else 0
        if f["stop_distance"]:
            shares = min(shares,
                         int((0.005 * equity) // f["stop_distance"]))
        if shares < 1:
            continue
        n += 1
        stop_price = (round(f["close"] - f["stop_distance"], 4)
                      if f["stop_distance"] else None)
        rows = _bars(view, sym, ("1Day", "1D"))
        state[sym] = {"bar_count": len(rows),
                      "stop_price": stop_price,
                      "entry_at": now.isoformat()}
        out.append(_intent(sleeve_id, stamp, n, "entry", sym, "buy",
                           shares,
                           f"{sleeve_id}:{'rsi2_pullback' if kind == 'rsi2' else 'squeeze_breakout'}",
                           price=f["close"], stop=stop_price))
        cash -= shares * f["close"]
    if out:
        _save_state(spath, state)
    return out


# ---------------------------------------------------------------- tensor
def _tensor_panels(view, frame):
    raw = (view or {}).get("tensor")
    panels = {}
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        grouped = {}
        for r in raw:
            if isinstance(r, dict) and r.get("symbol"):
                grouped.setdefault(r["symbol"], []).append(r)
        items = grouped.items()
    else:
        return panels
    for sym, val in items:
        rows = None
        if isinstance(val, list):
            rows = val
        elif isinstance(val, dict):
            if isinstance(val.get("features"), list):
                rows = val["features"]
            elif val.get("votes") is not None or val.get("balance") is not None:
                rows = [val]
        if rows:
            fr = None
            if isinstance(val, dict):
                fr = val.get("frame")
            if fr is None and rows and isinstance(rows[-1], dict):
                fr = rows[-1].get("frame")
            if fr is not None and str(fr).lower() not in (
                    frame, "1h" if frame == "1h" else "1wk",
                    "hourly" if frame == "1h" else "weekly"):
                continue
            panels[sym] = rows
    return panels


def _votes(row):
    v = row.get("votes")
    if isinstance(v, dict):
        return [v.get(n) for n in VOTE_NAMES]
    if isinstance(v, (list, tuple)):
        return list(v)
    return [row.get("vote_" + n) for n in VOTE_NAMES]


def _balance(row):
    if row.get("balance") is not None:
        return int(row["balance"])
    bull = row.get("bullish_votes")
    bear = row.get("bearish_votes")
    if bull is not None and bear is not None:
        return int(bull) - int(bear)
    vs = [x for x in _votes(row) if x is not None]
    return sum(1 for x in vs if x == 1) - sum(1 for x in vs if x == -1)


def _total_votes(row):
    if row.get("total_votes") is not None:
        return int(row["total_votes"])
    return sum(1 for x in _votes(row) if x is not None)


def _eval_tensor(sleeve_id, spec, view, ctx, now):
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    state, spath = _state(ctx, sleeve_id)
    equity, cash = _equity(view, ctx), _cash(view, ctx)
    panels = _tensor_panels(view, spec["frame"])
    out, n = [], 0
    # exits: entry bar + 20 native bars (late observation still exits)
    for sym in sorted(positions):
        p = positions[sym]
        qty = float(p["qty"])
        if qty <= 0:
            continue
        held = None
        rows = panels.get(sym) or []
        cur_idx = None
        if rows:
            last = rows[-1]
            cur_idx = last.get("bar_index", last.get("index"))
        if p.get("entry_bar_index") is not None and cur_idx is not None:
            held = int(cur_idx) - int(p["entry_bar_index"])
        if held is None:
            held = _held_bars(view, p, sym, (spec["tf"],))
        if held is None and state.get(sym):
            ent = state[sym].get("entry_bar_index")
            if ent is not None and cur_idx is not None:
                held = int(cur_idx) - int(ent)
            elif state[sym].get("entry_at"):
                held = _held_bars(view, {**p, "opened_at":
                                         state[sym]["entry_at"]},
                                  sym, (spec["tf"],))
        if held is not None and held >= 20:
            n += 1
            price = None
            brows = _bars(view, sym, (spec["tf"],))
            if brows:
                try:
                    price = _norm(brows)[-1]["c"]
                except (TypeError, ValueError, KeyError):
                    price = None
            out.append(_intent(sleeve_id, stamp, n, "exit", sym, "sell",
                               int(qty) if float(qty).is_integer()
                               else qty,
                               f"{sleeve_id}:hold_20_native_bars",
                               price=price))
            state.pop(sym, None)
    if out:
        _save_state(spath, state)
        return out
    free = 10 - len(positions)
    if free <= 0:
        return []
    scored = []
    for sym, rows in panels.items():
        if sym in TENSOR_EXCLUDED or sym in positions or len(rows) < 4:
            continue
        pts = rows[-4:]
        try:
            first, cur = pts[0], pts[-1]
            if _total_votes(cur) != 7 or _total_votes(first) != 7:
                continue
            status = cur.get("native_status", cur.get("status"))
            if status is not None and status != "ready":
                continue
            close = float(cur.get("close", cur.get("price")))
            atr = float(cur.get("atr14"))
            dv20 = float(cur.get("dollar_volume20"))
            vol = float(cur.get("volume", 0.0))
            slope = float(cur.get("obv_slope5", 0.0))
            if close < 5 or dv20 < 1_000_000 or atr <= 0:
                continue
            repair = _balance(cur) - _balance(first)
            increasing = 0
            for k in range(7):
                seq = [_votes(p)[k] for p in pts]
                if any(a is not None and b is not None and b > a
                       for a, b in zip(seq, seq[1:])):
                    increasing += 1
            if repair < 2 or increasing < 2:
                continue
            idx = cur.get("bar_index", cur.get("index"))
            if idx is not None and int(idx) + 1 < 234:
                continue  # warming: minimum source bars (archive)
            nxt = state.get(sym, {}).get("next_eligible_bar_index")
            extra_next = (view.get("extra") or {}).get(
                "next_eligible_bar_index")
            if isinstance(extra_next, dict):
                nxt = extra_next.get(sym, nxt)
            if (nxt is not None and idx is not None
                    and int(idx) < int(nxt)):
                continue  # cooldown (20 native bars, archive R11)
            ratio = slope / vol if vol > 0 else 0.0
            ratio = min(10.0, max(-10.0, ratio))
            score = repair + 0.01 * _balance(cur) + 0.001 * ratio
        except (TypeError, ValueError, KeyError):
            continue
        scored.append((-score, sym, close, dv20, idx))
    enh_on = _tensor_rec_enh_on(view, ctx, sleeve_id)
    for _, sym, close, dv20, idx in sorted(scored):
        if len(out) >= free:
            break
        # ENH batch 13 (binding leak: stale panel price): the Tensor
        # panel close can lag the executable bar (bundle SLA 86400s).
        # When a current bar exists, re-check the $5 floor and size off
        # ITS close; the panel-close decision is the shadow control.
        exec_close, rec = close, None
        if enh_on:
            brows = _bars(view, sym, (spec["tf"],))
            if brows:
                try: cur = float(_norm(brows)[-1]["c"])
                except (TypeError, ValueError, KeyError): cur = None
                if cur and cur > 0:
                    rec = {"exp_id": EXP_ID_TENSOR_REC, "sleeve": sleeve_id,
                           "symbol": sym, "panel_price": close,
                           "current_price": cur, "control_enter": True,
                           "control_qty": int(min(0.10 * equity, 0.01 * dv20, cash) // (close * 1.001)) if close > 0 else 0}
                    if cur < 5:
                        rec.update(treatment_enter=False, treatment_qty=0,
                                   refusal="current_price<5_floor")
                        _tensor_rec_paired(view, ctx, rec); continue
                    exec_close = cur
                    rec.update(treatment_enter=True,
                               treatment_qty=int(min(0.10 * equity, 0.01 * dv20, cash) // (cur * 1.001)))
        budget = min(0.10 * equity, 0.01 * dv20, cash)
        shares = int(budget // (exec_close * 1.001)) if exec_close > 0 else 0
        if shares < 1:
            continue
        n += 1
        state[sym] = {"entry_bar_index": idx,
                      "next_eligible_bar_index":
                          (int(idx) + 20) if idx is not None else None,
                      "entry_at": now.isoformat()}
        _it = _intent(sleeve_id, stamp, n, "entry", sym, "buy",
                      shares, f"{sleeve_id}:state_repair"
                      + (f" reprice panel={close:.2f} cur={exec_close:.2f}" if rec else ""),
                      price=exec_close)
        if rec:
            _it["enhance_exp"] = {"exp_id": EXP_ID_TENSOR_REC, "records": [rec]}
            _tensor_rec_paired(view, ctx, rec)
        out.append(_it)
        cash -= shares * exec_close * 1.001
    if out:
        _save_state(spath, state)
    return out


# ------------------------------------------------------------ absorption
EXP_ID_ABS4H = "ENH-ABS4H-CATCHUP-20261024"


def _catchup_on(view, ctx, sid):
    """ENH-ABS4H-CATCHUP-20261024 (Edge batch 1, IMPROVE): binding
    leak — the confirmation is visible only while the confirmation
    bar is the last completed bar, and the sleeve cadence (14400s)
    equals the bar period, so ONE missed/delayed evaluation (pool
    timeout, UNFED cycle, restart) destroys the designed trade
    permanently (measured on fixture: confirmation on bars[-1] ->
    entry; the same confirmation one bar older -> no entry, ever).
    Treatment (switch ON, default): a one-bar catch-up — if the
    confirmation fired on bars[-2] and the current bar still holds
    the absorption (close at/above the shock bar's midpoint), enter
    at the current close; the exit deadline stays anchored to the
    ORIGINAL confirmation close + 16h (never resets, per archive).
    The missed baseline decision is the paired shadow record on
    enhance_exp. OFF restores the pre-change rule exactly."""
    for src in ((ctx or {}).get("enhance"),
                ((view or {}).get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src, dict):
            per = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(per, dict) and "catchup_entry" in per:
                return bool(per["catchup_entry"])
    return True


def _eval_absorption(sleeve_id, spec, view, ctx, now):
    sym = spec["symbol"]
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    state, spath = _state(ctx, sleeve_id)
    rows = _bars(view, sym, ("4Hour", "4H"))
    out = []
    # exit: first evaluation at/after confirmation completion + 16h
    p = positions.get(sym)
    if p and float(p.get("qty") or 0) > 0:
        deadline = None
        for src in (p, state.get(sym) or {}):
            for k in ("exit_due_at", "deadline_at", "confirm_close_at"):
                if src.get(k):
                    t = _parse_ts(src[k])
                    if t is not None:
                        deadline = (t if k != "confirm_close_at"
                                    else t + timedelta(hours=16))
                        break
            if deadline:
                break
        if deadline is None:
            opened = _parse_ts(p.get("opened_at"))
            if opened is not None:
                deadline = opened + timedelta(hours=16)
        if deadline is not None and now >= deadline:
            price = None
            if rows:
                try:
                    price = _norm(rows)[-1]["c"]
                except (TypeError, ValueError, KeyError):
                    price = None
            q = (view.get("quotes") or {}).get(sym)
            if isinstance(q, dict) and q.get("bid"):
                price = float(q["bid"])
            out.append(_intent(sleeve_id, stamp, 1, "exit", sym, "sell",
                               float(p["qty"]),
                               f"{sleeve_id}:deadline_16h", price=price))
            state.pop(sym, None)
            _save_state(spath, state)
        return out
    if p:
        return []
    # entry: Decimal EMA advance() over completed bars (archive signals)
    if len(rows) < 300:
        return []
    try:
        bars = _norm(rows)
    except (TypeError, ValueError, KeyError):
        return []
    with localcontext() as lc:
        lc.prec = 34
        ve = pe = None
        prev_shock = False
        prev_h = prev_l = None
        confirmed = False
        confirmed_hist = []
        for b in bars:
            v, c = Decimal(str(b["v"])), Decimal(str(b["c"]))
            ve = v if ve is None else (Decimal(2) * v
                                       + Decimal(19) * ve) / Decimal(21)
            pe = c if pe is None else (Decimal(2) * c
                                       + Decimal(49) * pe) / Decimal(51)
            shock = (v > Decimal(2) * ve and c < Decimal(str(b["o"]))
                     and c < pe)
            confirmed = bool(prev_shock and c > Decimal(str(b["o"]))
                             and c > (prev_h + prev_l) / Decimal(2))
            confirmed_hist.append(confirmed)
            prev_shock = shock
            prev_h, prev_l = Decimal(str(b["h"])), Decimal(str(b["l"]))
    catchup = False
    rec = None
    if not confirmed:
        if not (_catchup_on(view, ctx, sleeve_id)
                and len(bars) >= 3 and confirmed_hist[-2]):
            return []
        shock_mid = (Decimal(str(bars[-3]["h"]))
                     + Decimal(str(bars[-3]["l"]))) / Decimal(2)
        if Decimal(str(bars[-1]["c"])) < shock_mid:
            return []  # absorption already invalidated: no catch-up
        catchup = True
        rec = {"exp_id": EXP_ID_ABS4H, "sleeve": sleeve_id,
               "control": "no_entry_confirmation_bar_missed",
               "treatment": "catchup_entry_one_bar_late",
               "confirm_bar_t": str(bars[-2]["t"]),
               "entry_bar_t": str(bars[-1]["t"])}
    price = bars[-1]["c"]
    q = (view.get("quotes") or {}).get(sym)
    if isinstance(q, dict) and q.get("ask"):
        price = float(q["ask"])
    if not price or price <= 0:
        return []
    cash = _cash(view, ctx)
    qty = cash / (price * 1.001)  # 100% cash incl. 10bp fee (rules-v1)
    if qty <= 0:
        return []
    confirm_close = _parse_ts(bars[-2]["t"] if catchup
                              else bars[-1]["t"])
    state[sym] = {"confirm_close_at":
                  confirm_close.isoformat() if confirm_close else None,
                  "exit_due_at": ((confirm_close + timedelta(hours=16)
                                   ).isoformat() if confirm_close
                                  else None),
                  "entry_at": now.isoformat()}
    _save_state(spath, state)
    ent = _intent(sleeve_id, stamp, 1, "entry", sym, "buy", qty,
                  f"{sleeve_id}:confirmed_absorption"
                  + ("_catchup" if catchup else ""), price=price)
    if rec:
        ent["enhance_exp"] = {"exp_id": EXP_ID_ABS4H, "records": [rec]}
    return [ent]


# ---------------------------------------------------------------- native
def _native_rebalance(cash, quantities, prices, weights, fee=0.002):
    """Port of archive prospective_native_math.rebalance()."""
    values = [q * p for q, p in zip(quantities, prices)]
    pre = cash + math.fsum(values)
    lo, hi = 0.0, pre
    for _ in range(70):
        nav = (lo + hi) / 2
        residual = nav + fee * math.fsum(
            abs(w * nav - v) for w, v in zip(weights, values)) - pre
        if residual > 0:
            hi = nav
        else:
            lo = nav
    post = (lo + hi) / 2
    targets = [w * post for w in weights]
    dollars = [t - v for t, v in zip(targets, values)]
    return dollars, post


# --- ENH-B5-NATIVE (Edge pass batch 5, 2026-10-24), two sleeves:
# pair book (btc_eth): binding leak = all-or-nothing warmup — one
# leg's short/stale history (e.g. an ETH feed gap) froze BOTH legs,
# so a qualified BTC trend went untraded for as long as the other
# leg's data lagged. Treatment: per-leg qualification — a leg with
# >=200 completed bars trades on its own fee-funded target; the
# unqualified leg is left untouched (never traded blind).
# single book (eth): binding leak = fee churn — the rebalance fired
# on ANY drift > $0.01, paying the 0.2% fee to adjust positions by
# pennies whenever price jittered around the target. Treatment: a
# no-trade deadband — drift adjustments within 0.5% of book value
# (2.5x the one-way fee) are refused while invested; initial entries
# and full exits are never banded. Switches: extra[f"enh_{sid}"] or
# ctx["enhance"][sid] {"per_leg_warmup"/"deadband": bool}, default
# ON; OFF restores the pre-change rule exactly. Shadow control =
# the pre-change decision, paired on served intents / journal.
EXP_ID_NATIVE_PAIR = "ENH-B5-NATIVE-PERLEG-20261024"
EXP_ID_NATIVE_BAND = "ENH-B5-NATIVE-DEADBAND-20261024"


def _native_enh_on(view, ctx, sid, key):
    for src in ((view or {}).get("extra") or {}, (ctx or {}).get("enhance") or {}):
        ov = src.get(f"enh_{sid}") or src.get(sid)
        if isinstance(ov, dict) and key in ov:
            return bool(ov[key])
    return True


def _native_single_leg(sleeve_id, stamp, sym, w, closes_sym, price,
                       held_qty, cash, exp_id):
    """Fee-funded 1-asset target for one qualified leg (the archive
    rebalance() shape reduced to a single dimension)."""
    sma200 = math.fsum(closes_sym[-200:]) / 200
    weight = w if closes_sym[-1] > sma200 else 0.0
    value = held_qty * price
    pre = cash + value
    lo, hi = 0.0, pre
    for _ in range(70):
        nav = (lo + hi) / 2
        residual = nav + 0.002 * abs(weight * nav - value) - pre
        if residual > 0:
            hi = nav
        else:
            lo = nav
    d = weight * ((lo + hi) / 2) - value
    if d < -0.01:
        qty = min(abs(d) / price, held_qty)
        if qty <= 0:
            return []
        it = _intent(sleeve_id, stamp, 1, "exit", sym, "sell", qty,
                     f"{sleeve_id}:sma200_rebalance enh:{exp_id} per_leg_warmup",
                     price=price)
        it["enhance_exp"] = {"exp_id": exp_id, "sleeve": sleeve_id,
                             "control_decision": "no_trade_pair_warmup_block",
                             "treatment_decision": "single_leg_exit"}
        return [it]
    if d > 0.01:
        it = _intent(sleeve_id, stamp, 1, "entry", sym, "buy", d / price,
                     f"{sleeve_id}:sma200_rebalance enh:{exp_id} per_leg_warmup",
                     price=price)
        it["enhance_exp"] = {"exp_id": exp_id, "sleeve": sleeve_id,
                             "control_decision": "no_trade_pair_warmup_block",
                             "treatment_decision": "single_leg_entry"}
        return [it]
    return []


def _eval_native(sleeve_id, spec, view, ctx, now):
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    sleeves_syms = [s for s, _ in spec["weights"]]
    # Held symbols outside this book's pair (single-asset book) are not
    # this sleeve's to trade; the pair book manages BTC+ETH.
    closes, prices = {}, {}
    _missing = []
    for sym in sleeves_syms:
        rows = _bars(view, sym, ("1Day", "1D"))
        if len(rows) < 200:
            _missing.append(sym)
            continue  # warmup: SMA200 undefined for this leg
        try:
            cs = [b["c"] for b in _norm(rows)]
        except (TypeError, ValueError, KeyError):
            _missing.append(sym)
            continue
        closes[sym] = cs
        prices[sym] = cs[-1]
    if _missing:
        # ENH-B5 pair treatment: trade the qualified leg alone.
        if len(sleeves_syms) == 2 and len(closes) == 1 \
                and _native_enh_on(view, ctx, sleeve_id, "per_leg_warmup"):
            sym = next(iter(closes))
            w = dict(spec["weights"])[sym]
            held = positions.get(sym)
            return _native_single_leg(
                sleeve_id, stamp, sym, w, closes[sym], prices[sym],
                float(held["qty"]) if held else 0.0, _cash(view, ctx),
                EXP_ID_NATIVE_PAIR)
        return []  # warmup: SMA200 undefined — fail closed
    weights, quantities = [], []
    for sym, w in spec["weights"]:
        sma200 = math.fsum(closes[sym][-200:]) / 200
        weights.append(w if closes[sym][-1] > sma200 else 0.0)
        held = positions.get(sym)
        quantities.append(float(held["qty"]) if held else 0.0)
    # The single-asset book still needs the pair dimension for the
    # archive rebalance() shape: pad with the other asset at weight 0
    # only when it is part of this book; single book runs 1-asset math
    # via the same fee-funded formula on its own dimension.
    if len(weights) == 2:
        dollars, _ = _native_rebalance(_cash(view, ctx), quantities,
                                        [prices[s] for s in sleeves_syms],
                                        weights)
        pairs = list(zip(sleeves_syms, dollars))
    else:
        sym = sleeves_syms[0]
        cash = _cash(view, ctx)
        value = quantities[0] * prices[sym]
        pre = cash + value
        target_value = weights[0] * pre / (1 + 0.002 * weights[0]) \
            if weights[0] > 0 else 0.0
        # fee-funded single-asset target: solve nav like rebalance()
        lo, hi = 0.0, pre
        for _ in range(70):
            nav = (lo + hi) / 2
            residual = nav + 0.002 * abs(weights[0] * nav - value) - pre
            if residual > 0:
                hi = nav
            else:
                lo = nav
        target_value = weights[0] * ((lo + hi) / 2)
        pairs = [(sym, target_value - value)]
        # ENH-B5 deadband (single book): refuse fee-churn drift trades
        # while invested — adjustments within 0.5% of book value cost
        # the 0.2% fee to capture <0.5% of exposure correction.
        if _native_enh_on(view, ctx, sleeve_id, "deadband") \
                and quantities[0] > 0 and weights[0] > 0 \
                and abs(pairs[0][1]) <= 0.005 * pre:
            _enh11_paired(view, {"exp_id": EXP_ID_NATIVE_BAND,
                "sleeve": sleeve_id, "control_decision": "dust_rebalance",
                "treatment_decision": "refuse_within_deadband",
                "drift_usd": round(pairs[0][1], 2), "book_usd": round(pre, 2)})
            return []
    out, n = [], 0
    sells = [(s, d) for s, d in pairs if d < -0.01]
    buys = [(s, d) for s, d in pairs if d > 0.01]
    for sym, d in sells:  # sales before increases (archive RULES)
        qty = min(abs(d) / prices[sym], quantities[sleeves_syms.index(sym)]
                  if sym in sleeves_syms else abs(d) / prices[sym])
        if qty <= 0:
            continue
        n += 1
        kind = ("exit" if weights[sleeves_syms.index(sym)] == 0
                else "exit")
        out.append(_intent(sleeve_id, stamp, n, kind, sym, "sell", qty,
                           f"{sleeve_id}:sma200_rebalance",
                           price=prices[sym]))
    for sym, d in buys:
        qty = d / prices[sym]
        if qty <= 0:
            continue
        n += 1
        out.append(_intent(sleeve_id, stamp, n, "entry", sym, "buy", qty,
                           f"{sleeve_id}:sma200_rebalance",
                           price=prices[sym]))
    return out


# ----------------------------------------------------------------- gamma
def _gamma_contracts(view, sym):
    raw = (view or {}).get("options")
    rows = []
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        v = raw.get(sym)
        if isinstance(v, list):
            rows = v
        elif isinstance(v, dict):
            rows = v.get("chain") or v.get("contracts") or []
        else:
            for val in raw.values():
                if isinstance(val, list):
                    rows.extend(val)
    return [r for r in rows if isinstance(r, dict)]


def _eval_gamma(sleeve_id, spec, view, ctx, now):
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    et_now = now.astimezone(ET)
    out, n = [], 0
    # exits first: flat 10:00 ET entry day; missed exit stays due;
    # expiry obligation can force an earlier exit.
    for sym in sorted(positions):
        p = positions[sym]
        qty = float(p["qty"])
        if qty <= 0:
            continue
        legs = p.get("legs") or []
        if not legs and "C" not in sym and "P" not in sym:
            continue  # not an option package row
        entry_session = (p.get("entry_session")
                         or (legs[0].get("entry_session") if legs else None)
                         or str(p.get("opened_at") or "")[:10])
        expiry = ((legs[0].get("expiry") or legs[0].get("expiration_date"))
                  if legs else None) or p.get("expiry")
        due, reason = False, None
        today = et_now.date().isoformat()
        if expiry and today >= str(expiry):
            due, reason = True, "pre_expiry_obligation_exit"
        elif entry_session:
            if today > entry_session:
                due, reason = True, "same_day_1000_exit_overdue"
            elif today == entry_session and (et_now.hour, et_now.minute) \
                    >= (10, 0):
                due, reason = True, "same_day_1000_exit"
        if p.get("sessions_held") is not None:
            try:
                if int(float(p["sessions_held"])) >= 1:
                    due, reason = True, "same_day_1000_exit_overdue"
            except (TypeError, ValueError):
                pass
        if due:
            n += 1
            out.append(_intent(sleeve_id, stamp, n, "exit", sym, "sell",
                               int(qty) if float(qty).is_integer()
                               else qty,
                               f"{sleeve_id}:{reason}", legs=legs or None))
    if out:
        return out
    # entries: 09:35 <= ET < 09:45, causal opening events only
    if not ((9, 35) <= (et_now.hour, et_now.minute) < (9, 45)):
        return []
    if (view or {}).get("market_open") is False:
        return []
    cal = (view or {}).get("calendar") or {}
    session = et_now.date().isoformat()
    if cal.get("session") and cal["session"] != session:
        return []
    events = ((view or {}).get("opening_events")
              or (view or {}).get("opening_reversal_events")
              or ((view or {}).get("extra") or {}).get(
                  "opening_reversal_events") or [])
    equity = _equity(view, ctx)
    for ev in events:
        if not isinstance(ev, dict):
            continue
        try:
            # _opening_event_clocks (archive): session identity + causal
            # clock chain + prior-afternoon R5 + 5s break-quote freshness
            if ev.get("session") != session:
                continue
            if cal.get("session") and ev.get("session") != cal["session"]:
                continue
            prev = cal.get("previous_session")
            if prev and ev.get("prior_afternoon_session") != prev:
                continue
            opened = _parse_ts(cal.get("open")) if cal.get("open") else None
            start = _parse_ts(ev.get("first_5min_start_at"))
            end = _parse_ts(ev.get("first_5min_end_at"))
            bar_rx = _parse_ts(ev.get("first_5min_received_at"))
            bm = _parse_ts(ev.get("break_market_at"))
            brx = _parse_ts(ev.get("break_received_at"))
            r5m = _parse_ts(ev.get("R5_signal_at"))
            r5r = _parse_ts(ev.get("R5_received_at"))
            clocks = [start, end, bar_rx, bm, brx, r5m, r5r]
            if any(c is None for c in clocks):
                continue
            if opened is not None and start != opened:
                continue
            if end != start + timedelta(minutes=5):
                continue
            if not (end <= bar_rx <= bm <= brx <= now):
                continue
            if prev and r5m.astimezone(ET).date().isoformat() != prev:
                continue
            if opened is not None and not (r5m <= r5r < opened):
                continue
            if (now - bm).total_seconds() > 5:
                continue
            if float(ev["first_5min_low"]) <= 0 or float(
                    ev["observed_break_price"]) <= 0:
                continue
            # signal (archive _evaluate opening_gamma branch)
            if ev.get("causal_R5_prior_afternoon") is not True:
                continue
            if ev.get("first_5min_complete") is not True:
                continue
            if not float(ev["first_5min_return"]) < 0:
                continue
            if not float(ev["observed_break_price"]) < float(
                    ev["first_5min_low"]):
                continue
            if not ev.get("source_sha256"):
                continue
        except (TypeError, ValueError, KeyError):
            continue
        sym = ev.get("symbol")
        if not sym:
            continue
        q = ((view or {}).get("quotes") or {}).get(sym) or {}
        spot = None
        if q.get("bid") and q.get("ask"):
            spot = (float(q["bid"]) + float(q["ask"])) / 2
        else:
            spot = float(ev["observed_break_price"])
        today = et_now.date()
        cands = []
        for c in _gamma_contracts(view, sym):
            if c.get("underlying", sym) != sym:
                continue
            if c.get("right") != "put":
                continue
            exp = c.get("expiry") or c.get("expiration_date")
            if not exp:
                continue
            try:
                dte = (datetime.fromisoformat(str(exp)).date()
                       - today).days
                delta = abs(float(c.get("delta")))
                ask = float(c.get("ask"))
            except (TypeError, ValueError):
                continue
            if not (spec["dte"][0] <= dte <= spec["dte"][1]):
                continue
            if not (0.50 <= delta <= 0.65):
                continue
            if ask <= 0:
                continue
            cands.append((str(exp), abs(delta - 0.575),
                          abs(float(c.get("strike", spot)) - spot),
                          c.get("symbol"), c, ask))
        if not cands:
            continue
        cands.sort(key=lambda x: (x[0], x[1], x[2], x[3] or ""))
        _, _, _, _, contract, ask = cands[0]
        debit = ask * 100.0
        if debit / (spot * 100) > spec["max_premium_spot"]:
            continue  # uncapped_premium_budget_exceeded (archive)
        per = debit * (1 + 0.0015)  # fee_bps 15 (rules book)
        risk = spec["risk_fraction"] * equity
        qty = int(risk // per) if per > 0 else 0
        ask_size = contract.get("ask_size")
        if ask_size is not None:
            qty = min(qty, int(float(ask_size)))
        if qty < 1:
            continue
        occ = contract.get("symbol")
        if not occ:
            continue
        legs = [{"symbol": occ, "underlying": sym, "right": "put",
                 "expiry": str(contract.get("expiry")
                               or contract.get("expiration_date")),
                 "strike": float(contract.get("strike", spot)),
                 "ratio": 1}]
        n += 1
        out.append(_intent(sleeve_id, stamp, n, "entry", occ, "buy", qty,
                           f"{sleeve_id}:opening_break_put",
                           price=ask, legs=legs))
        break  # one open package per cycle (archive evaluate())
    return out


_DISPATCH = {"rsi2": _eval_trader, "squeeze": _eval_trader,
             "tensor": _eval_tensor, "absorption": _eval_absorption,
             "native": _eval_native, "gamma": _eval_gamma}


def evaluate(sleeve_id, view, ctx=None):
    spec = SPECS[sleeve_id]
    view = view or {}
    ctx = ctx or {}
    now = _now(view, ctx)
    return _DISPATCH[spec["kind"]](sleeve_id, spec, view, ctx, now)
