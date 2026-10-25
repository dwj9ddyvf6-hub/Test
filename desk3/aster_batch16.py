"""Aster batch 16 — overnight 5bp, Trader Donchian55, Tensor daily20 x2,
saty_research shell (ASTER-BUILD-MAP batch 16, TSV 156-160).

Faithful sleeve-layer ports from the staged archive:
  source/backend/r19_timing.py + strategies/r19/tensor/RULES.json
    (R19_TIMING_OVERNIGHT_5BP — the archive book differs from batch 15's
    25BP book ONLY in fee_bps; the timing machinery is batch 15's single
    implementation, reused, not re-derived)
  source/backend/trader_signals.py (TRADER_DONCHIAN55 frozen rules doc)
    + trader_runtime.py sizing/exit obligations
  source/backend/tensor_daily_models.py (frozen D20_PV / D20_TENSOR
    tree ensembles; model artifacts vendored as DATA under
    desk3/aster_d20_assets/ and hash-verified at load — no refit,
    Tensor ENGINE untouched)
  saty_research: SOURCE ABSENT (map S4) — TSV-as-spec meta-ranker shell
    only; the 10 setup families are NOT invented. Candidates arrive via
    the `saty_setups` snapshot key; no v3 producer emits it, so the
    sleeve lands visibly UNFED/monitor-only.

Sizing is book-relative on the $10,000 slice (source books $100k).
Paper only.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SLICE = 10000.0

OVERNIGHT_ID = "aster_r19_timing_overnight_5bp"
DONCHIAN_ID = "aster_trader_donchian55"
D20_TENSOR_ID = "aster_tensor_d20_tensor"
D20_PV_ID = "aster_tensor_d20_pv"
SATY_ID = "aster_saty_research"

TIMING_INPUTS = ("bars", "positions", "quotes")
DONCHIAN_INPUTS = ("bars", "positions")
D20_INPUTS = ("tensor_daily20", "bars", "positions")
SATY_INPUTS = ("saty_setups", "quotes", "bars", "positions")

PRODUCERS = (
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
    {"name": "quotes", "outputs": ("quotes",), "freshness_sla_s": 60},
    {"name": "broker_readback", "outputs": ("positions",),
     "freshness_sla_s": 900},
    {"name": "tensor_daily20_bundle", "outputs": ("tensor_daily20",),
     "freshness_sla_s": 93600},
    {"name": "saty_setup_families", "outputs": ("saty_setups",),
     "freshness_sla_s": 60},
)
# NOTE: run_live registers only bars + broker_readback today. quotes /
# tensor_daily20 / saty_setups have no live producer yet, so those
# sleeves are visibly UNFED in the registry, never fake-fed.

SPECS = {
    OVERNIGHT_ID: dict(kind="overnight", inputs=TIMING_INPUTS, cadence_s=300),
    DONCHIAN_ID: dict(kind="donchian", inputs=DONCHIAN_INPUTS, cadence_s=86400),
    D20_TENSOR_ID: dict(kind="d20", model="price_volume_plus_tensor",
                        inputs=D20_INPUTS, cadence_s=86400),
    D20_PV_ID: dict(kind="d20", model="price_volume",
                    inputs=D20_INPUTS, cadence_s=86400),
    SATY_ID: dict(kind="saty", inputs=SATY_INPUTS, cadence_s=600),
}


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


def _positions(view):
    return [p for p in (view.get("positions") or [])
            if float(p.get("qty") or 0) != 0]


def _bars_held(p, view, sym, tf="1Day"):
    for k in ("bars_held", "sessions_held", "held_bars"):
        if p.get(k) is not None:
            return int(p[k])
    opened = str(p.get("opened_at") or "")[:10]
    if not opened:
        return 0
    return sum(1 for b in _bars(view, sym, tf)
               if str(b.get("t"))[:10] > opened)


def _intent(sid, stamp, n, kind, sym, qty, reason, price=None,
            side=None, stop_price=None):
    if side is None:
        side = "buy" if kind == "entry" else "sell"
    return {"intent_id": f"{sid}-{stamp}-{n}", "kind": kind,
            "symbol": sym, "side": side, "qty": qty,
            "order_type": "market", "limit_price": None,
            "stop_price": stop_price, "reason": reason,
            "time_in_force": "day",
            "position_intent": ("buy_to_open" if side == "buy" else "sell_to_open")
            if kind == "entry" else "sell_to_close",
            "price_hint": float(price) if price else None}


# ---------------------------------------------------------------- overnight
def _eval_overnight(sid, view, ctx):
    """R19_TIMING_OVERNIGHT_5BP: batch 15's r19_timing machinery with the
    5bp book (archive RULES.json: identical to the 25bp book except
    fee_bps 5 vs 25 — verified in the intake census)."""
    from desk3 import aster_batch15 as b15
    spec = dict(b15.SPECS["aster_r19_timing_overnight_25bp"], fee_bps=5)
    return b15._eval_timing(sid, spec, view, ctx)


# ---------------------------------------------------------------- donchian55
DON_UNIVERSE = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV",
                "XLI", "XLP", "XLU", "XLB", "XLY", "SMH", "SOXX")
DON_MIN_BARS = 252
DON_ENTRY_CH, DON_EXIT_CH, DON_SMA = 55, 20, 200
DON_MAX_HOLD, DON_SLOTS = 126, 10
DON_NOTIONAL_FRAC, DON_DV_FRAC = 0.10, 0.01
DON_RISK_FRAC, DON_STOP_ATR = 0.005, 2.0


def _sma(values, period):
    out = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = math.fsum(values[i + 1 - period:i + 1]) / period
    return out


def _rma(values, period):
    out = [None] * len(values)
    if len(values) < period:
        return out
    out[period - 1] = math.fsum(values[:period]) / period
    for i in range(period, len(values)):
        out[i] = out[i - 1] + (values[i] - out[i - 1]) / period
    return out


def _don_features(bars):
    """Archive trader_signals._features (DONCHIAN arm), last bar only."""
    closes = [float(b["c"]) for b in bars]
    trs = [max(float(b["h"]) - float(b["l"]),
               abs(float(b["h"]) - float(bars[i - 1]["c"])),
               abs(float(b["l"]) - float(bars[i - 1]["c"]))) if i
           else float(b["h"]) - float(b["l"]) for i, b in enumerate(bars)]
    atr = _rma(trs, 14)[-1]
    dv = math.fsum(float(b["c"]) * float(b.get("v") or 0)
                   for b in bars[-20:]) / 20
    sma200 = _sma(closes, DON_SMA)[-1]
    prior55 = max(float(b["h"]) for b in bars[-1 - DON_ENTRY_CH:-1])
    prior20lo = min(float(b["l"]) for b in bars[-1 - DON_EXIT_CH:-1])
    return {"close": closes[-1], "atr14": atr, "dollar_volume20": dv,
            "sma200": sma200, "prior55_high": prior55, "prior20_low": prior20lo}


def _eval_donchian(sid, view, ctx):
    now = _now(view, ctx)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    cash = float(((view.get("slice") or {}).get("cash_usd")) or SLICE)
    equity = float(((view.get("slice") or {}).get("capital_usd")) or SLICE)
    out, n = [], 0
    held = {}
    for p in positions:
        held[p["symbol"]] = p
        cash -= abs(float(p["qty"])) * float(p.get("avg_price") or 0)

    # ---- exits (archive obligations: close-signal exits from the frozen
    # features; initial 2ATR stop + 126-bar timeout from position state)
    for sym, p in held.items():
        qty = abs(float(p["qty"]))
        bars = _bars(view, sym, "1Day")
        last = float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
        reason = None
        stop = p.get("stop_price", (p.get("meta") or {}).get("stop_price"))
        if stop is not None and last <= float(stop):
            reason = f"{sid} exit: observed_quote_initial_2atr_stop stop={float(stop):.2f} last={last:.2f}"
        elif _bars_held(p, view, sym) >= DON_MAX_HOLD:
            reason = f"{sid} exit: 126_completed_holding_bars"
        elif len(bars) >= DON_MIN_BARS:
            f = _don_features(bars)
            rs = []
            if f["close"] < f["prior20_low"]:
                rs.append("close_below_prior20_low")
            if f["close"] < f["sma200"]:
                rs.append("close_below_sma200")
            if rs:
                reason = f"{sid} exit: {';'.join(rs)}"
        if reason:
            n += 1
            out.append(_intent(sid, stamp, n, "exit", sym, qty, reason, last))
    if out:
        return out

    # ---- entries: ranked by (close-prior55)/atr desc, symbol asc
    cands = []
    for sym in DON_UNIVERSE:
        if sym in held:
            continue
        bars = _bars(view, sym, "1Day")
        if len(bars) < DON_MIN_BARS:
            continue
        try:
            f = _don_features(bars)
        except Exception:
            continue
        if not f["atr14"] or f["atr14"] <= 0 or f["dollar_volume20"] <= 0:
            continue
        if f["close"] > f["prior55_high"] and f["close"] > f["sma200"]:
            cands.append((-(f["close"] - f["prior55_high"]) / f["atr14"], sym, f))
    cands.sort(key=lambda x: (x[0], x[1]))
    slots = DON_SLOTS - len(held)
    for _, sym, f in cands:
        if slots <= 0:
            break
        price = f["close"]
        cap = min(equity * DON_NOTIONAL_FRAC, f["dollar_volume20"] * DON_DV_FRAC, cash)
        shares = int(cap // price) if cap > 0 else 0
        risk_shares = int((equity * DON_RISK_FRAC) // (DON_STOP_ATR * f["atr14"]))
        shares = min(shares, risk_shares)
        if shares < 1:
            continue
        n += 1
        stop = price - DON_STOP_ATR * f["atr14"]
        out.append(_intent(
            sid, stamp, n, "entry", sym, shares,
            f"{sid} entry: close > max(previous_55_high) and close > sma200 "
            f"close={price:.2f} prior55={f['prior55_high']:.2f} atr14={f['atr14']:.4f}",
            price, stop_price=round(stop, 4)))
        cash -= shares * price
        slots -= 1
    return out


# --- ENH (Edge batch 26, 2026-10-24) --------------------------------
# ENH-B26-D20FRESH: _d20_decision validates a candidate series'
# internal consistency (ordinal, origin, phase, readiness) but
# never compares its last row to the desk's current bars — a
# stalled tensor_daily20 producer leaves the sleeve entering
# 20-bar holds at a days-old close, sized off that close. Cure
# (entry candidates only; the 20-bar exit is never gated): when
# the symbol's own 1Day bars are present, refuse selection when
# the last row predates the last bar by more than
# D20_ROW_MAX_AGE_DAYS (the longest legitimate gap is a Friday
# row read on a Tuesday after a Monday holiday = 4 days). No
# bars = no evidence = pass (archive behavior).
# ENH-B26-SATYEXEC: _eval_saty sizes qty off the PLANNED entry's
# risk-per-share while the intent fills at the current quote mid;
# a chased price widens the real risk-per-share and the position
# silently exceeds its 1R budget. Cure: size off the executable
# price the intent actually carries, |price - invalidation|.
# Switches: extra["enh_<sid>"] or extra["aster_b16_enh"]
# {"fresh_row_gate" | "exec_risk_sizing": bool}, default ON; OFF
# restores the pre-change rule exactly. Paired records ride the
# aster_enh_exp_journal (batch-15 idiom) + intent["enhance_exp"].
EXP_ID_B26_D20 = "ENH-B26-D20FRESH-20261024"
EXP_ID_B26_SATY = "ENH-B26-SATYEXEC-20261024"
D20_ROW_MAX_AGE_DAYS = 4


def _enh_on_b16(view, sid, field):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b16_enh")
    if isinstance(ov, dict) and field in ov:
        return bool(ov[field])
    return True


def _paired_b16(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)


def _d20_row_age_days(view, sym, rows):
    """(age_days, row_date, ref_date) of the last decision row vs
    the symbol's newest 1Day bar; None when either side is absent
    or unparseable (no evidence -> the gate passes)."""
    if not rows:
        return None
    bars = _bars(view, sym, "1Day")
    if not bars:
        return None
    ref = _parse_ts(bars[-1].get("t"))
    try:
        row_dt = datetime.fromtimestamp(float(rows[-1].get("timestamp")),
                                        tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
    if ref is None:
        return None
    return ((ref.date() - row_dt.date()).days,
            row_dt.date().isoformat(), ref.date().isoformat())


# ---------------------------------------------------------------- tensor D20
D20_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "aster_d20_assets")
D20_MANIFEST_SHA256 = "9be2845edd541c0a48ef33063cab165689e25bdbbd7e7a6df94e30e66506d757"
D20_SOURCE_SHA256 = {
    "price_volume": "36216e1b8f0000066cf51356b70a7a54a885e154ee417a42d360ab921d634965",
    "price_volume_plus_tensor": "e7776b115b908380dc3df85210302736d306d38538568e91e26cf3f6e0c4b300",
}
PV_COLUMNS = ("return20", "return60", "atr_pct", "rvol",
              "log_dollar_volume20", "close_ema21_distance_atr")
VOTE_COLUMNS = tuple("vote_" + x for x in
                     ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave"))
TENSOR_COLUMNS = VOTE_COLUMNS + (
    "balance_delta3", "ribbon_inversion_count", "ribbon_repair3",
    "ribbon_width", "ribbon_slope", "normalized_obv_slope5", "squeeze_on",
    "normalized_squeeze_momentum", "squeeze_length", "first_squeeze_release",
    "squeeze_release_age", "ut_state", "ut_state_age", "mcdx_position",
    "mcdx_position_delta3", "normalized_macd_histogram",
    "normalized_sign_entropy20", "entropy_delta3", "efficiency10",
    "efficiency_delta3", "prior_sell_avwap_distance_atr", "overhead60_atr")
ALL_COLUMNS = PV_COLUMNS + TENSOR_COLUMNS
REQUIRED_NATIVE_COLUMNS = frozenset((
    "symbol", "bar_index", "timestamp", "completed_at", "usable_at",
    "source_origin_timestamp", "native_status", "open", "close", "volume",
    "atr14", "return20", "return60", "rvol", "dollar_volume20", "ema21",
    "bullish_votes", "bearish_votes", "ribbon_inversion_count",
    "ribbon_width", "ribbon_slope", "obv_slope5", "squeeze_on",
    "squeeze_momentum", "squeeze_length", "ut_regime", "mcdx_position",
    "mcdx_position_delta3", "macd_histogram", "efficiency10",
    "normalized_sign_entropy20", "prior_sell_avwap",
    "prior_sell_completed_at", "overhead60_atr")) | frozenset(VOTE_COLUMNS)
D20_EXCLUDED = frozenset(("QQQ", "SPY", "B", "GOLD"))
D20_HOLD_BARS, D20_SLOTS = 20, 10
D20_CAP_EQUITY, D20_CAP_DV = 0.10, 0.01

_D20_CACHE = {}


class D20IntegrityError(ValueError):
    pass


def _d20_phase(symbol):
    return int(hashlib.sha256(symbol.encode("utf-8")).hexdigest(), 16) % 20


def _load_d20_models(asset_dir=None):
    """Archive load path: verify the frozen manifest + every asset hash,
    the model contract, and the canonical anchors — fail closed."""
    asset_dir = asset_dir or D20_ASSET_DIR
    if asset_dir in _D20_CACHE:
        return _D20_CACHE[asset_dir]
    manifest_bytes = open(os.path.join(asset_dir, "MANIFEST.json"), "rb").read()
    if hashlib.sha256(manifest_bytes).hexdigest() != D20_MANIFEST_SHA256:
        raise D20IntegrityError("frozen model manifest identity differs")
    manifest = json.loads(manifest_bytes)
    if manifest.get("new_fits") != 0 or manifest.get("new_calibrations") != 0:
        raise D20IntegrityError("model asset provenance authorizes unexpected fits")
    bodies = {}
    for item in manifest["files"]:
        name = item["path"]
        if os.path.basename(name) != name or name in bodies:
            raise D20IntegrityError("invalid numerical model asset path")
        path = os.path.join(asset_dir, name)
        if not os.path.exists(path):
            continue  # joblib/oracle files are not consumed at the sleeve layer
        body = open(path, "rb").read()
        if len(body) != item["bytes"] or hashlib.sha256(body).hexdigest() != item["sha256"]:
            raise D20IntegrityError("frozen numerical asset identity differs: " + name)
        bodies[name] = body
    models = {}
    for name in ("price_volume", "price_volume_plus_tensor"):
        p = json.loads(bodies[name + ".json"])
        expected = PV_COLUMNS if name == "price_volume" else ALL_COLUMNS
        if (p.get("schema") != "tensor-daily20-frozen-numerical-model/1"
                or p.get("new_fits") != 0
                or p["source_sha256"] != D20_SOURCE_SHA256[name]
                or tuple(p["columns"]) != expected or p["frame"] != "1d"
                or p["hold_bars"] != 20 or len(p["trees"]) != 100
                or len(p["medians"]) != len(expected)):
            raise D20IntegrityError("frozen numerical model contract differs")
        trees = tuple(tuple((float(nd["value"]), int(nd["feature"]),
                             float(nd["threshold"]), int(nd["left"]),
                             int(nd["right"]), bool(nd["leaf"]),
                             bool(nd["missing_left"])) for nd in tree)
                      for tree in p["trees"])
        models[name] = {"name": name, "columns": expected,
                        "medians": tuple(float(x) for x in p["medians"]),
                        "threshold": float(p["threshold"]),
                        "baseline": float(p["baseline"]), "trees": trees,
                        "source_sha256": p["source_sha256"]}
    anchors_raw = json.loads(bodies["DAILY_SOURCE_ANCHORS.json"])
    anchors = {s: {"first_timestamp": int(v["first_timestamp"]),
                   "last_timestamp": int(v["last_timestamp"]),
                   "original_rows": int(v["original_rows"]),
                   "phase": int(v["phase"])}
               for s, v in anchors_raw["symbols"].items()}
    if len(anchors) != 1817 or any(a["phase"] != _d20_phase(s)
                                    for s, a in anchors.items()):
        raise D20IntegrityError("canonical daily source anchors differ")
    bundle = {"models": models, "anchors": anchors}
    _D20_CACHE[asset_dir] = bundle
    return bundle


def verify_d20_assets():
    bundle = _load_d20_models()
    return {"status": "PASS", "manifest_sha256": D20_MANIFEST_SHA256,
            "new_fits": 0, "new_calibrations": 0,
            "canonical_symbols": len(bundle["anchors"]),
            "model_source_sha256": {n: m["source_sha256"]
                                    for n, m in bundle["models"].items()}}


def _num(value):
    if value is None or isinstance(value, bool):
        return float(value) if isinstance(value, bool) else None
    try:
        v = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return v if math.isfinite(v) else None


def _d20_predict(model, features):
    """Frozen ensemble: baseline + one leaf per tree; medians impute."""
    vector = tuple(v if (v := _num(features.get(c))) is not None else med
                   for c, med in zip(model["columns"], model["medians"]))
    pred = model["baseline"]
    for tree in model["trees"]:
        j = 0
        while not tree[j][5]:
            node = tree[j]
            j = node[3] if vector[node[1]] <= node[2] else node[4]
        pred += tree[j][0]
    return pred


def _ratio(a, b):
    return _num(a / b) if a is not None and b is not None and b != 0 else None


def _diff(a, b):
    return _num(a - b) if a is not None and b is not None else None


def _d20_feature_frame(rows):
    """Archive feature_frame: the C01 35-column past-only transform."""
    converted = [{k: _num(row.get(k)) for k in REQUIRED_NATIVE_COLUMNS
                  if k not in {"symbol", "native_status", "ut_regime"}}
                 for row in rows]
    result, seen_on, off_age, last_ut, ut_age = [], False, None, None, 0
    for i, (row, v) in enumerate(zip(rows, converted)):
        if not REQUIRED_NATIVE_COLUMNS.issubset(row):
            raise ValueError("required native feature columns are absent")
        close, atr = v["close"], (v["atr14"] or None)
        if v["atr14"] == 0:
            atr = None
        lag = converted[i - 3] if i >= 3 else {}
        balance = _diff(v["bullish_votes"], v["bearish_votes"])
        old_balance = _diff(lag.get("bullish_votes"), lag.get("bearish_votes"))
        vols = [p["volume"] for p in converted[max(0, i - 19):i + 1]]
        mean_vol = (math.fsum(vols) / 20 if len(vols) == 20
                    and all(x is not None for x in vols) else None)
        dollar = v["dollar_volume20"]
        log_dollar = math.log1p(dollar) if dollar is not None and dollar > -1 else None
        on = v["squeeze_on"]
        if on == 1:
            release_age, seen_on, off_age = 0.0, True, 0
        elif on == 0 and seen_on and off_age is not None:
            off_age += 1
            release_age = float(off_age)
        else:
            off_age, release_age = None, None
        regime = str(row["ut_regime"] or "").lower()
        direction = 1 if regime == "bullish" else -1 if regime == "bearish" else None
        if direction is None:
            last_ut, ut_age = None, 0
            enc_ut, enc_age = None, None
        else:
            ut_age = ut_age + 1 if last_ut == direction else 0
            last_ut = direction
            enc_ut, enc_age = float(direction), float(ut_age)
        first_release = float(on == 0 and i >= 3 and all(
            p["squeeze_on"] == 1 for p in converted[i - 3:i]))
        f = {"return20": v["return20"], "return60": v["return60"],
             "atr_pct": _ratio(atr, close), "rvol": v["rvol"],
             "log_dollar_volume20": log_dollar,
             "close_ema21_distance_atr": _ratio(_diff(close, v["ema21"]), atr),
             "balance_delta3": _diff(balance, old_balance),
             "ribbon_inversion_count": v["ribbon_inversion_count"],
             "ribbon_repair3": _diff(lag.get("ribbon_inversion_count"),
                                     v["ribbon_inversion_count"]),
             "ribbon_width": v["ribbon_width"], "ribbon_slope": v["ribbon_slope"],
             "normalized_obv_slope5": _ratio(v["obv_slope5"], mean_vol),
             "squeeze_on": on,
             "normalized_squeeze_momentum": _ratio(v["squeeze_momentum"], atr),
             "squeeze_length": v["squeeze_length"],
             "first_squeeze_release": first_release,
             "squeeze_release_age": release_age, "ut_state": enc_ut,
             "ut_state_age": enc_age, "mcdx_position": v["mcdx_position"],
             "mcdx_position_delta3": v["mcdx_position_delta3"],
             "normalized_macd_histogram": _ratio(v["macd_histogram"], atr),
             "normalized_sign_entropy20": v["normalized_sign_entropy20"],
             "entropy_delta3": _diff(v["normalized_sign_entropy20"],
                                     lag.get("normalized_sign_entropy20")),
             "efficiency10": v["efficiency10"],
             "efficiency_delta3": _diff(v["efficiency10"], lag.get("efficiency10")),
             "prior_sell_avwap_distance_atr": _ratio(
                 _diff(close, v["prior_sell_avwap"]), atr),
             "overhead60_atr": v["overhead60_atr"]}
        for col in VOTE_COLUMNS:
            f[col] = (v[col] if v[col] is not None else 0.0) \
                if row["native_status"] == "ready" else None
        anchor_c, complete = v["prior_sell_completed_at"], v["completed_at"]
        if anchor_c is not None and (complete is None or anchor_c >= complete):
            raise ValueError("sell anchor must belong to an earlier completed bar")
        result.append({c: f[c] for c in ALL_COLUMNS})
    return result


def _d20_decision(bundle, model_name, symbol, rows):
    """Archive evaluate_daily20 for ONE sleeve: eligibility gates in the
    archive's order, then the frozen threshold. ({selected, score, reason})"""
    model = bundle["models"][model_name]
    anchor = bundle["anchors"].get(symbol)
    if anchor is None:
        return {"selected": False, "score": None, "reason": "no_anchor"}
    if not rows:
        return {"selected": False, "score": None, "reason": "empty_history"}
    for i, row in enumerate(rows):
        if not REQUIRED_NATIVE_COLUMNS.issubset(row):
            return {"selected": False, "score": None, "reason": "missing_native_columns"}
        if row["symbol"] != symbol or int(row["bar_index"]) != i:
            return {"selected": False, "score": None, "reason": "ordinal_mismatch"}
        if int(row["source_origin_timestamp"]) != anchor["first_timestamp"] \
                or (i == 0 and int(row["timestamp"]) != anchor["first_timestamp"]):
            return {"selected": False, "score": None, "reason": "origin_mismatch"}
    i = len(rows) - 1
    row = rows[-1]
    close, dollar, atr = _num(row["close"]), _num(row["dollar_volume20"]), _num(row["atr14"])
    if symbol in D20_EXCLUDED:
        reason = "excluded_symbol"
    elif i < 233:
        reason = "warmup"
    elif row["native_status"] != "ready":
        reason = "native_not_ready"
    elif close is None or close < 5:
        reason = "price_below_5"
    elif dollar is None or dollar < 1e6:
        reason = "liquidity_below_1m"
    elif atr is None or atr <= 0:
        reason = "invalid_atr"
    elif i % 20 != anchor["phase"]:
        reason = "phase_not_selected"
    else:
        reason = "eligible"
    if reason != "eligible":
        return {"selected": False, "score": None, "reason": reason}
    feats = _d20_feature_frame(rows)[-1]
    score = _d20_predict(model, feats)
    if not math.isfinite(score):
        return {"selected": False, "score": None, "reason": "nonfinite_score"}
    return {"selected": score >= model["threshold"], "score": score,
            "reason": "selected" if score >= model["threshold"]
            else "below_frozen_threshold",
            "close": close, "dollar_volume20": dollar}


def _eval_d20(sid, spec, view, ctx):
    now = _now(view, ctx)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    cash = float(((view.get("slice") or {}).get("cash_usd")) or SLICE)
    equity = float(((view.get("slice") or {}).get("capital_usd")) or SLICE)
    out, n = [], 0
    held = {}
    for p in positions:
        held[p["symbol"]] = p
        cash -= abs(float(p["qty"])) * float(p.get("avg_price") or 0)
    # ---- the ONLY designed exit: 20 completed holding bars from the fill
    for sym, p in held.items():
        if _bars_held(p, view, sym) >= D20_HOLD_BARS:
            bars = _bars(view, sym, "1Day")
            last = float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
            n += 1
            out.append(_intent(sid, stamp, n, "exit", sym, abs(float(p["qty"])),
                               f"{sid} exit: hold_20_bars exit after twenty "
                               f"completed daily holding bars", last))
    if out:
        return out
    try:
        bundle = _load_d20_models()
    except Exception:
        return []  # frozen-asset integrity failure: fail closed, no intents
    rowsmap = view.get("tensor_daily20") or {}
    cands = []
    for sym in sorted(rowsmap):
        if sym in held:
            continue
        try:
            d = _d20_decision(bundle, spec["model"], sym, rowsmap[sym] or [])
        except Exception:
            continue
        if d["selected"]:
            if _enh_on_b16(view, sid, "fresh_row_gate"):
                age = _d20_row_age_days(view, sym, rowsmap[sym] or [])
                if age is not None:
                    stale = age[0] > D20_ROW_MAX_AGE_DAYS
                    _paired_b16(view, {
                        "exp_id": EXP_ID_B26_D20, "sleeve": sid,
                        "kind": "entry", "switch_on": True,
                        "symbol": sym, "row_date": age[1],
                        "ref_bar_date": age[2], "row_age_days": age[0],
                        "control": "enter",
                        "treatment": "refuse_stale_row" if stale else "enter"})
                    if stale:
                        continue  # ENH-B26-D20FRESH refusal
            cands.append((-d["score"], sym, d))
    cands.sort(key=lambda x: (x[0], x[1]))  # archive rank: score desc, symbol
    slots = D20_SLOTS - len(held)
    for _, sym, d in cands:
        if slots <= 0:
            break
        price = d["close"]
        cap = min(equity * D20_CAP_EQUITY, d["dollar_volume20"] * D20_CAP_DV, cash)
        shares = int(cap // price) if cap > 0 and price > 0 else 0
        if shares < 1:
            continue
        n += 1
        out.append(_intent(
            sid, stamp, n, "entry", sym, shares,
            f"{sid} entry: frozen_{spec['model']} score={d['score']:.6f} "
            f"threshold={bundle['models'][spec['model']]['threshold']:.6f} "
            f"hold=20bars", price))
        cash -= shares * price
        slots -= 1
    return out


# ---------------------------------------------------------------- saty_research
SATY_RISK_USD = 0.0025 * SLICE          # 0.25% of slice per entry ($25 = 1R)
SATY_COST_PER_SHARE = 0.02              # TSV round-trip cost estimate
SATY_MAX_ENTRIES_DAY = 3
SATY_DAILY_LOSS_R = 2.0
SATY_OPEN_RISK_R = 2.0
SATY_CORRELATED_R = 1.0                 # single-instrument book: all SPY
SATY_QUOTE_MAX_AGE_S = 5.0
SATY_ENTRY_DEADLINE = time(15, 40)      # 20 min before the 16:00 close
SATY_FINAL_EXIT = time(15, 50)          # 10 min before the close


def _saty_price(view):
    q = (view.get("quotes") or {}).get("SPY") or {}
    bid, ask = q.get("bid"), q.get("ask")
    if bid and ask:
        return (float(bid) + float(ask)) / 2
    bars = _bars(view, "SPY", "10Min")
    return float(bars[-1]["c"]) if bars else None


def _saty_net_room(c, ref_entry=None):
    entry = float(ref_entry if ref_entry is not None else c["entry"])
    inval, t1 = float(c["invalidation"]), float(c["targets"][0])
    if c["direction"] == "long":
        risk, room = entry - inval, t1 - entry - SATY_COST_PER_SHARE
    else:
        risk, room = inval - entry, entry - t1 - SATY_COST_PER_SHARE
    if risk <= 0:
        return None
    return room / risk


def _eval_saty(sid, view, ctx):
    """TSV-as-spec meta-ranker shell (map S4 fallback). The 10 setup
    families are absent from the archive; candidates arrive pre-formed
    via `saty_setups`. This shell owns ONLY: ranking (net target room /
    risk, context, chase room, age), the 0.25% risk sizing (half for
    mean-reversion), the 3/day + 2R loss + 2R open / 1R correlated
    limits, the entry/final-exit deadlines, 5s quote freshness, and the
    structural exits (invalidation, T1 scale, post-scale trail,
    final deadline)."""
    now = _now(view, ctx)
    et = now.astimezone(ET)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = _positions(view)
    out, n = [], 0
    price = _saty_price(view)

    # ---- exits first (owned exits continue even when entries are off)
    for p in positions:
        sym = p["symbol"]
        qty = float(p["qty"])
        direction = p.get("direction") or ("long" if qty > 0 else "short")
        inval = p.get("invalidation", (p.get("meta") or {}).get("invalidation"))
        targets = p.get("targets") or (p.get("meta") or {}).get("targets") or []
        entry_ref = float(p.get("avg_price") or 0)
        reason, exit_qty = None, abs(qty)
        if price is not None and inval is not None:
            if (direction == "long" and price <= float(inval)) or \
               (direction == "short" and price >= float(inval)):
                reason = "structural_invalidation"
        if reason is None and et.time() >= SATY_FINAL_EXIT:
            reason = "final_exit_deadline"
        if reason is None and price is not None and targets:
            t1 = float(targets[0])
            if not p.get("scaled"):
                if (direction == "long" and price >= t1) or \
                   (direction == "short" and price <= t1):
                    reason, exit_qty = "target1_scale", abs(qty) // 2 or abs(qty)
            elif (direction == "long" and price <= entry_ref) or \
                 (direction == "short" and price >= entry_ref):
                reason = "trail_to_breakeven_after_scale"
        if reason:
            n += 1
            out.append(_intent(sid, stamp, n, "exit", sym, exit_qty,
                               f"{sid} exit: {reason}", price,
                               side="sell" if qty > 0 else "buy"))
    if out:
        return out

    # ---- entries
    if et.time() >= SATY_ENTRY_DEADLINE:
        return []
    state = view.get("saty_state") or (view.get("extra") or {}).get("saty_state") or {}
    if int(state.get("entries_today") or 0) >= SATY_MAX_ENTRIES_DAY:
        return []
    if float(state.get("realized_r_today") or 0) <= -SATY_DAILY_LOSS_R:
        return []
    q = (view.get("quotes") or {}).get("SPY") or {}
    qat = _parse_ts(q.get("at"))
    if qat is None or (now - qat).total_seconds() > SATY_QUOTE_MAX_AGE_S \
            or (now - qat).total_seconds() < 0:
        return []  # no fresh two-sided quote: fail closed
    if price is None:
        return []
    open_risk = 0.0
    held_syms = set()
    for p in positions:
        held_syms.add(p["symbol"])
        inval = p.get("invalidation", (p.get("meta") or {}).get("invalidation"))
        if inval is not None:
            open_risk += abs(float(p["qty"])) * abs(float(p.get("avg_price") or 0) - float(inval))
    cands = []
    for c in view.get("saty_setups") or []:
        if not isinstance(c, dict) or c.get("symbol") != "SPY":
            continue
        if "SPY" in held_syms:
            continue
        try:
            room_plan = _saty_net_room(c)
            room_now = _saty_net_room(c, ref_entry=price)
        except Exception:
            continue
        if room_plan is None or room_now is None or room_now <= 0:
            continue
        key = (-room_now, -float(c.get("context") or 0), float(c.get("age_min") or 0),
               str(c.get("family") or ""))
        cands.append((key, c, room_now))
    if not cands:
        return []
    cands.sort(key=lambda x: x[0])
    best_key, best, _ = cands[0]
    for key, c, _r in cands[1:]:
        if c["direction"] != best["direction"] and abs(key[0] - best_key[0]) < 1e-9:
            return []  # conflicting equal-ranked directions wait (TSV)
    risk_usd = SATY_RISK_USD
    fam = str(best.get("family") or "").lower()
    if "mean_reversion" in fam or "meanrev" in fam or "mean-reversion" in fam:
        risk_usd = SATY_RISK_USD / 2
    planned_risk_per_share = abs(float(best["entry"]) - float(best["invalidation"]))
    # ENH-B26-SATYEXEC: size off the executable price (the intent's
    # own price), not the setup's planned entry.
    exec_risk_on = _enh_on_b16(view, sid, "exec_risk_sizing")
    risk_per_share = abs(price - float(best["invalidation"])) \
        if exec_risk_on else planned_risk_per_share
    if risk_per_share <= 0:
        return []
    if open_risk + risk_usd > min(SATY_OPEN_RISK_R, SATY_CORRELATED_R) * SATY_RISK_USD:
        return []
    qty = int(risk_usd // risk_per_share)
    if qty < 1:
        return []
    n += 1
    side = "buy" if best["direction"] == "long" else "sell"
    out.append(_intent(
        sid, stamp, n, "entry", "SPY", qty,
        f"{sid} entry: family={best.get('family')} dir={best['direction']} "
        f"net_room={_saty_net_room(best, price):.3f}R risk_usd={risk_usd:.2f} "
        f"invalidation={float(best['invalidation']):.2f} "
        f"targets={','.join(str(t) for t in best['targets'])}",
        price, side=side))
    if exec_risk_on:
        rec = {"exp_id": EXP_ID_B26_SATY, "sleeve": sid,
               "kind": "entry", "switch_on": True,
               "planned_entry": float(best["entry"]), "exec_price": price,
               "control_risk_per_share": round(planned_risk_per_share, 4),
               "treatment_risk_per_share": round(risk_per_share, 4),
               "control_qty": (int(risk_usd // planned_risk_per_share)
                               if planned_risk_per_share > 0 else 0),
               "treatment_qty": qty}
        out[-1]["enhance_exp"] = rec
        _paired_b16(view, rec)
    return out


# ---------------------------------------------------------------- dispatch
def evaluate(sleeve_id, view, ctx=None):
    view = view or {}
    ctx = ctx or {}
    spec = SPECS[sleeve_id]
    kind = spec["kind"]
    if kind == "overnight":
        return _eval_overnight(sleeve_id, view, ctx)
    if kind == "donchian":
        return _eval_donchian(sleeve_id, view, ctx)
    if kind == "d20":
        return _eval_d20(sleeve_id, spec, view, ctx)
    return _eval_saty(sleeve_id, view, ctx)
